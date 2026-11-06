"""증권사별 보드 HTML → ReportMeta 파싱 어댑터 (내부).

보드 DOM 이 제각각이라(미래에셋 표·NH ul>li·유안타 표) 범용 셀렉터 하나로는 부족 —
증권사별 어댑터로 분기한다(P0 실측 결론). 본문은 받지 않고 메타만 추출.
공개 진입점은 mixins/research.py 의 brokerageReports — 본 파서들은 내부 헬퍼.
"""

from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup

from .schema import ReportMeta

_MIRAE_VIEW = "https://securities.miraeasset.com/bbs/board/message/view.do"


def _normDate(s: str) -> str:
    """'2026.06.26'·'2026/06/26' 류 날짜를 'YYYY-MM-DD' 로 정규화 (구분자 통일·앞 10자)."""
    return re.sub(r"[./]", "-", (s or "").strip())[:10]


def _parseMiraeasset(html: str, label: str, srcUrl: str) -> list[ReportMeta]:
    """미래에셋 보드 표(작성일·제목·첨부·작성자) → ReportMeta. 링크는 view() → view.do URL.

    Args:
        html: 보드 list.do 응답 HTML (cp949 디코드 후).
        label: 카테고리 라벨 = reportType.
        srcUrl: 링크 추출 실패 시 fallback URL.

    Returns:
        list[ReportMeta] — 표 행마다 1건. 표 미발견 시 빈 리스트.

    Example::

        _parseMiraeasset(html, "기업분석", url)
    """
    soup = BeautifulSoup(html, "lxml")
    table = None
    for tb in soup.find_all("table"):
        ths = [th.get_text(strip=True) for th in tb.find_all("th")]
        if "제목" in ths and "작성일" in ths:
            table = tb
            break
    if table is None:
        return []
    out: list[ReportMeta] = []
    body = table.find("tbody") or table
    for tr in body.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 4:
            continue
        link = tds[1].find("a")
        href = link.get("href", "") if link else ""
        m = re.search(r"view\('(\d+)','(\d+)'\)", href)
        url = f"{_MIRAE_VIEW}?messageId={m.group(1)}&categoryId={m.group(2)}" if m else srcUrl
        out.append(
            ReportMeta(
                broker="miraeasset",
                brokerName="미래에셋",
                title=tds[1].get_text(" ", strip=True),
                url=url,
                pubDate=_normDate(tds[0].get_text(strip=True)),
                reportType=label,
                author=tds[3].get_text(strip=True) or None,
            )
        )
    return out


def _parseNh(html: str, label: str, srcUrl: str) -> list[ReportMeta]:
    """NH 모바일 보드 ul>li>a → ReportMeta. reportType 은 행별 p.sort 우선(없으면 라벨).

    Args:
        html: boardList 응답 HTML.
        label: 카테고리 라벨 (p.sort 부재 시 fallback reportType).
        srcUrl: 링크 부재 시 fallback URL.

    Returns:
        list[ReportMeta] — p.tit 있는 항목마다 1건.

    Example::

        _parseNh(html, "기업분석", url)
    """
    soup = BeautifulSoup(html, "lxml")
    out: list[ReportMeta] = []
    for a in soup.select("ul li a"):
        tit = a.select_one("p.tit")
        if tit is None:
            continue
        sort = a.select_one("p.sort")
        name = a.select_one("span.info_name")
        date = a.select_one("span.info_date")
        href = a.get("href", "")
        url = ("https://m.nhqv.com" + href) if href.startswith("/") else (href or srcUrl)
        out.append(
            ReportMeta(
                broker="nh",
                brokerName="NH투자",
                title=tit.get_text(" ", strip=True),
                url=url,
                pubDate=_normDate(date.get_text(strip=True) if date else ""),
                reportType=(sort.get_text(strip=True) if sort else None) or label,
                author=name.get_text(strip=True) if name else None,
            )
        )
    return out


def _parseYuanta(html: str, label: str, srcUrl: str) -> list[ReportMeta]:
    """유안타 rs_list 표(날짜·제목·파일·-·저자·조회수) → ReportMeta. 링크 href=# → srcUrl.

    Args:
        html: rs_list.cmd 응답 HTML.
        label: 카테고리 라벨 = reportType.
        srcUrl: 링크 href=# 라 카테고리 URL 을 그대로 사용.

    Returns:
        list[ReportMeta] — td 5개 이상 행마다 1건.

    Example::

        _parseYuanta(html, "투자전략", url)
    """
    soup = BeautifulSoup(html, "lxml")
    out: list[ReportMeta] = []
    body = soup.find("tbody") or soup
    for tr in body.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 5:
            continue
        author = tds[4].get_text(" ", strip=True).replace("관심 애널리스트", "").strip()
        out.append(
            ReportMeta(
                broker="yuanta",
                brokerName="유안타",
                title=tds[1].get_text(" ", strip=True),
                url=srcUrl,
                pubDate=_normDate(tds[0].get_text(strip=True)),
                reportType=label,
                author=author or None,
            )
        )
    return out


_HANYANG_HOST = "https://www.hygood.co.kr"
# Next.js 가 페이지 끝에 싣는 서버 데이터 조각. 문자열 리터럴 하나가 한 조각이다.
_NEXT_PUSH_RE = re.compile(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)')
_HANYANG_POST_RE = re.compile(r'"postUuid":"([0-9a-f-]{36})","title":"((?:[^"\\]|\\.)*)"')
_HANYANG_BASE_RE = re.compile(r'"basePath":"(/board/[^"]+)"')
_DATE_RE = re.compile(r"\d{4}[.\-/]\d{2}[.\-/]\d{2}")


def _hanyangPosts(html: str) -> tuple[str, dict[str, list[str]]]:
    """한양 보드 페이지의 Next.js 서버 데이터에서 (보드 경로, {제목: [글 번호, ...]}) 를 읽는다.

    표의 제목 칸은 링크 없는 버튼이라 글 주소가 표에 없다. 같은 페이지의 서버 데이터에 글 번호(postUuid)가
    제목과 함께 들어 있어 주소 ``{보드 경로}/{글 번호}`` 를 만들 수 있다. 제목이 같은 글(예: 커버리지 제외
    종목)은 번호를 표와 같은 순서로 쌓아 두므로, 호출 쪽이 행마다 앞에서부터 하나씩 쓴다. 서버 데이터를
    읽지 못하면 빈 값이고 호출 쪽이 보드 주소로 대신한다.
    """
    raw = "".join(_NEXT_PUSH_RE.findall(html))
    if not raw:
        return "", {}
    try:
        flight = json.loads(f'"{raw}"')
    except ValueError:
        flight = raw.replace('\\"', '"')
    base = _HANYANG_BASE_RE.search(flight)
    titles: dict[str, list[str]] = {}
    for postId, title in _HANYANG_POST_RE.findall(flight):
        key = re.sub(r"\s+", " ", title.replace('\\"', '"')).strip()
        titles.setdefault(key, []).append(postId)
    return (base.group(1) if base else ""), titles


def _parseHanyang(html: str, label: str, srcUrl: str) -> list[ReportMeta]:
    """한양 board 표(번호·제목·등록일·첨부·조회) → ReportMeta. 링크는 {보드 경로}/{글 번호}(자기 서버).

    제목 칸은 링크 없는 버튼이다. 글 주소는 같은 페이지 서버 데이터의 글 번호로 만들고, 번호를 못 찾은 행은
    보드 주소(srcUrl)로 둔다. 제목 칸에 링크(a)가 있으면 그 주소를 쓴다.

    Args:
        html: 보드 목록 응답 HTML (/board/<보드 번호>).
        label: 카테고리 라벨 = reportType.
        srcUrl: 글 주소를 못 만들 때 쓰는 보드 URL.

    Returns:
        list[ReportMeta]. 제목과 등록일이 있는 행마다 1건. 제목에 종목코드(005930) 내장.

    Example::

        _parseHanyang(html, "기업분석", url)
    """
    soup = BeautifulSoup(html, "lxml")
    out: list[ReportMeta] = []
    table = soup.select_one("table.board-list-table") or soup
    body = table.find("tbody") or table
    basePath, postIds = _hanyangPosts(html)
    for tr in body.find_all("tr"):
        tds = tr.find_all("td")
        titleCell = next((td for td in tds if td.find(["button", "a"])), None)
        if titleCell is None:
            continue
        date = ""
        for td in tds:
            txt = td.get_text(strip=True)
            if _DATE_RE.match(txt):
                date = txt
                break
        if not date:
            continue
        link = titleCell.find("a", href=True)
        title = re.sub(r"\s+", " ", (link or titleCell.find(["button", "a"])).get_text(" ", strip=True))
        queue = postIds.get(title)
        postId = queue.pop(0) if queue else None
        if link is not None:
            href = link["href"].split(";")[0]  # jsessionid 꼬리 제거
            url = (_HANYANG_HOST + href) if href.startswith("/") else href
        elif postId and basePath:
            url = f"{_HANYANG_HOST}{basePath}/{postId}"
        else:
            url = srcUrl
        out.append(
            ReportMeta(
                broker="hanyang",
                brokerName="한양",
                title=title,
                url=url,
                pubDate=_normDate(date),
                reportType=label,
                author=None,
            )
        )
    return out


def _parseBookook(html: str, label: str, srcUrl: str) -> list[ReportMeta]:
    """부국 보드 표(번호·날짜·제목·-·저자/조회수) → ReportMeta. per-report URL 부재 → 보드 URL.

    detail 은 같은 페이지 in-page 펼침(viewDetailContent), PDF 는 POST(/file/download)라
    깨끗한 per-report GET 링크가 없어 보드 URL 로 링크아웃(유안타 동형). cp949 디코드 전제.

    Args:
        html: research_N 보드 응답 HTML(cp949 디코드 후).
        label: 카테고리 라벨 = reportType.
        srcUrl: 보드 list URL (각 행 url 로 사용).

    Returns:
        list[ReportMeta] — 날짜 있는 표 행마다 1건. 제목에 종목코드(304360) 내장.

    Example::

        _parseBookook(html, "기업분석", url)
    """
    soup = BeautifulSoup(html, "lxml")
    out: list[ReportMeta] = []
    body = soup.find("tbody") or soup
    for tr in body.find_all("tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        date = next((c for c in cells if re.match(r"\d{4}[./-]\d{2}[./-]\d{2}", c)), "")
        if not date:
            continue
        titles = [c for c in cells if c and c != date and not c.isdigit()]
        if not titles:
            continue
        title = max(titles, key=len)
        # 저자 = 숫자(번호·조회수)·날짜·제목 아닌 셀. 기업분석엔 있고(예 유대웅) 시황엔 없음(None).
        author = next((c for c in cells if c and not c.isdigit() and c not in {title, date}), None)
        out.append(
            ReportMeta(
                broker="bookook",
                brokerName="부국",
                title=title,
                url=srcUrl,
                pubDate=_normDate(date),
                reportType=label,
                author=author,
            )
        )
    return out


PARSERS = {
    "miraeasset": _parseMiraeasset,
    "nh": _parseNh,
    "yuanta": _parseYuanta,
    "hanyang": _parseHanyang,
    "bookook": _parseBookook,
}
