"""네이버 금융 테마 분류 수집 — KR 테마 리스트 + 테마별 편입종목·사유 (로컬 개인용).

⚠ 데이터 출처 고지
    네이버 금융의 테마 *분류* 와 *편입사유* 는 네이버의 편집저작물이다. 본인 컴퓨터에서
    분석 용도로 라이브 직독해 쓰는 것은 무방하나, 수집 결과를 재배포·공개(HF 적재·서비스
    배포·제3자 공개)하면 데이터베이스제작자의 권리(저작권법 제4장)·저작권 문제가 발생할 수
    있다. dartlab 은 데이터를 호스팅·재배포하지 않고 호출 시점에 네이버에서 직접 당겨오며,
    이는 다른 네이버 출처 축(price/flow/ownership/sector/peers)과 동일한 라이브 직독 posture
    다 — 따라서 본 축의 산출물은 HF SSOT 적재 대상이 아니고 공개 터미널 제품에 배선하지 않는다.

라이브 검증(2026-06-29): 리스트 page1 40테마·lastPage 7(약 280테마), 상세(no=523 리튬)
22종목 + 편입사유 파싱 정상.
"""

from __future__ import annotations

import logging
import re

import polars as pl

from ..infra.http import GatherHttpClient

log = logging.getLogger(__name__)

_LIST_URL = "https://finance.naver.com/sise/theme.naver"
_DETAIL_URL = "https://finance.naver.com/sise/sise_group_detail.naver"
# 네이버 금융 일부 endpoint 가 referer 를 확인 — 리스트 페이지를 referer 로 명시.
_HEADERS = {"Referer": _LIST_URL}

# 파싱 정규식 — 라이브 검증된 현행 페이지 구조.
_THEME_LINK_RE = re.compile(r'<a href="/sise/sise_group_detail\.naver\?type=theme&no=(\d+)">(.*?)</a>')
_PAGE_RE = re.compile(r'<a href="/sise/theme\.naver\?page=(\d+)"')
_TR_RE = re.compile(r"<tr.*?>(.*?)</tr>", re.DOTALL)
_STOCK_RE = re.compile(r'<a href="/item/main\.naver\?code=(\d+)">(.*?)</a>')
_REASON_RE = re.compile(r'<p class="info_txt">(.*?)</p>', re.DOTALL)

_TAG_RE = re.compile(r"<[^>]+>")

# 출력 스키마 (빈 결과도 동일 컬럼 유지).
_LIST_SCHEMA: dict[str, pl.DataType] = {"themeNo": pl.Int64, "themeName": pl.Utf8, "url": pl.Utf8}
_STOCKS_SCHEMA: dict[str, pl.DataType] = {
    "themeNo": pl.Int64,
    "themeName": pl.Utf8,
    "stockCode": pl.Utf8,
    "stockName": pl.Utf8,
    "reason": pl.Utf8,
}


def _clean(text: str) -> str:
    """HTML 조각의 잔여 태그·기본 엔티티·공백을 정리한다."""
    text = _TAG_RE.sub("", text)
    text = text.replace("&amp;", "&").replace("&nbsp;", " ").replace("&gt;", ">").replace("&lt;", "<")
    return text.strip()


def _parseThemeListHtml(html: str) -> tuple[list[dict], int]:
    """테마 리스트 HTML → (테마 dict 리스트, lastPage). 네트워크 없는 순수 파싱."""
    themes = [
        {"themeNo": int(no), "themeName": _clean(name), "url": f"{_DETAIL_URL}?type=theme&no={no}"}
        for no, name in _THEME_LINK_RE.findall(html)
    ]
    pages = [int(p) for p in _PAGE_RE.findall(html)]
    return themes, (max(pages) if pages else 1)


def _parseThemeDetailHtml(html: str) -> list[dict]:
    """테마 상세 HTML → 편입종목 dict 리스트(stockCode/stockName/reason). 순수 파싱."""
    rows: list[dict] = []
    for tr in _TR_RE.findall(html):
        stock = _STOCK_RE.search(tr)
        if not stock:
            continue
        reason = _REASON_RE.search(tr)
        rows.append(
            {
                "stockCode": stock.group(1),
                "stockName": _clean(stock.group(2)),
                "reason": _clean(reason.group(1)) if reason else "",
            }
        )
    return rows


async def fetchThemeList(client: GatherHttpClient, *, limit: int | None = None) -> list[dict]:
    """네이버 금융 전 페이지 테마 리스트 수집.

    Capabilities: page 1 → lastPage 파싱 → 전 페이지 순회 → themeNo 중복 제거(순서 보존).
    AIContext: gather('theme') (target 없음) 의 backend — 가벼운 테마 목록.
    Guide: rate limit 은 GatherHttpClient 가 도메인별 처리 — 별도 sleep 불요.
    When: collectTheme 가 리스트/이름매핑/전체크롤을 위해 호출.
    How: client.get(_LIST_URL, page) → _parseThemeListHtml → 페이지 순회 → dedup → limit.

    Args:
        client: GatherHttpClient — 도메인별 rate limit/재시도를 자체 처리.
        limit: 반환 테마 수 상한 (None=전체).

    Returns:
        list[dict] — {themeNo:int, themeName:str, url:str}. themeNo 중복 제거(순서 보존).

    Raises:
        없음 — 호출자(collectTheme)가 빈 결과를 빈 DataFrame 으로 흡수.

    Example::

        themes = await fetchThemeList(client)  # [{'themeNo': 523, 'themeName': '리튬', ...}, ...]

    Requires:
        네트워크 (finance.naver.com 무인증). 산출물 재배포 금지(DB권/저작권).

    See Also:
        fetchThemeStocks : 단일 테마 편입종목.
        collectTheme : target 분기 오케스트레이터.
    """
    resp = await client.get(_LIST_URL, params={"page": 1}, headers=_HEADERS)
    themes, lastPage = _parseThemeListHtml(resp.text)
    for page in range(2, lastPage + 1):
        resp = await client.get(_LIST_URL, params={"page": page}, headers=_HEADERS)
        more, _ = _parseThemeListHtml(resp.text)
        themes.extend(more)

    seen: set[int] = set()
    unique: list[dict] = []
    for theme in themes:
        if theme["themeNo"] in seen:
            continue
        seen.add(theme["themeNo"])
        unique.append(theme)
    return unique if limit is None else unique[:limit]


async def fetchThemeStocks(client: GatherHttpClient, themeNo: int, *, limit: int | None = None) -> list[dict]:
    """단일 테마의 편입종목 + 편입사유 수집.

    Capabilities: 상세 페이지 fetch → tr 행 파싱 → 종목코드/종목명/편입사유.
    AIContext: collectTheme 의 테마별 편입종목 backend.
    Guide: 편입사유(info_txt) 없으면 빈 문자열.
    When: collectTheme 가 선택된 테마마다 호출.
    How: client.get(_DETAIL_URL, no) → _parseThemeDetailHtml → limit.

    Args:
        client: GatherHttpClient.
        themeNo: 테마 번호 (리스트의 themeNo).
        limit: 반환 종목 수 상한 (None=전체).

    Returns:
        list[dict] — {stockCode:str, stockName:str, reason:str}.

    Raises:
        없음.

    Example::

        rows = await fetchThemeStocks(client, 523)  # 리튬 테마 편입종목

    Requires:
        네트워크 (finance.naver.com 무인증). 산출물 재배포 금지(DB권/저작권).

    See Also:
        fetchThemeList : 테마 리스트.
        collectTheme : target 분기 오케스트레이터.
    """
    resp = await client.get(_DETAIL_URL, params={"type": "theme", "no": themeNo}, headers=_HEADERS)
    rows = _parseThemeDetailHtml(resp.text)
    return rows if limit is None else rows[:limit]


async def _crawlThemes(client: GatherHttpClient, selected: list[tuple[int, str]], *, progress: bool) -> list[dict]:
    """선택 테마들의 편입종목 순회 수집 — 다중 테마(>1)면 SSOT core.progress 진행바.

    진행 표시는 ``dartlab.core.progress`` (rich 기반, 환경 자동 감지) 재사용 —
    터미널/Jupyter/마리모 라이브, CI/파이프/테스트 무음. detailed 로 현재 테마명 표시.
    """
    total = len(selected)
    records: list[dict] = []
    if not (progress and total > 1):
        for no, name in selected:
            for stock in await fetchThemeStocks(client, no):
                records.append({"themeNo": no, "themeName": name, **stock})
        return records
    from dartlab.core.progress import progressBar

    with progressBar(total, desc="테마 수집", detailed=True) as bar:
        for no, name in selected:
            bar.update(item=name)
            for stock in await fetchThemeStocks(client, no):
                records.append({"themeNo": no, "themeName": name, **stock})
            bar.advance()
    return records


async def collectTheme(client: GatherHttpClient, target: str | None, *, progress: bool = True) -> pl.DataFrame:
    """테마 축 수집 오케스트레이터 — 기본은 전 테마를 개별 수집해 하나의 long DataFrame 으로.

    Capabilities:
        - target None/""/"all" : 전 테마(약 280)를 개별 수집 → 하나의 long DataFrame 으로
          결합 (themeNo/themeName/stockCode/stockName/reason). 기본 동작.
        - target "list"        : 테마 *리스트* 만 (themeNo/themeName/url) — 가벼움.
        - target 숫자          : 해당 themeNo 테마의 편입종목만.
        - target 문자열        : 테마명 exact → 없으면 contains 매칭 테마들의 편입종목.
        - 매칭 0 : 빈 DataFrame (스키마 유지, 크래시 없음).

    AIContext: gather('theme', ...) handler 의 backend — 기본은 전수 크롤 후 단일 프레임 결합.
    Guide: 기본(target 없음)이 전 테마 크롤이라 무겁다 — SSOT rich 진행바를 띄운다.
        wide(테마기준) 행렬은 ``df.pivot(values="reason", index="stockCode", on="themeName")``.
    When: handleTheme 가 runAsync 로 호출.
    How: fetchThemeList → 선택 테마 결정(기본=전체) → _crawlThemes(개별 fetchThemeStocks) → concat.

    Args:
        client: GatherHttpClient (rate limit·jitter 자체 처리 — 별도 sleep 불요).
        target: None/"all"=전체 결합(기본) · "list"=목록만 · 테마명/themeNo=해당 테마만.
        progress: 다중 테마 크롤 시 rich 진행바 (getProgress SSOT; 터미널/Jupyter/marimo, 기본 True).

    Returns:
        pl.DataFrame — target "list" 면 _LIST_SCHEMA, 그 외 _STOCKS_SCHEMA(long 결합).

    Raises:
        없음 — 빈 결과는 빈 DataFrame.

    Example::

        await collectTheme(client, None)      # 전 테마 결합 long DataFrame (기본)
        await collectTheme(client, "list")    # 테마 목록만
        await collectTheme(client, "2차전지")  # 해당 테마만 필터

    Requires:
        네트워크 (finance.naver.com 무인증). 산출물 재배포 금지(DB권/저작권).

    See Also:
        fetchThemeList / fetchThemeStocks : 본 함수가 호출하는 수집기.
        entry.handlers.handleTheme : gather('theme') dispatch caller.
    """
    themeList = await fetchThemeList(client)
    nameByNo = {t["themeNo"]: t["themeName"] for t in themeList}
    norm = "" if target is None else str(target).strip()

    if norm.lower() == "list":
        return pl.DataFrame(themeList, schema=_LIST_SCHEMA)

    if norm in ("", "all"):
        selected = [(t["themeNo"], t["themeName"]) for t in themeList]
    elif norm.isdigit() and int(norm) in nameByNo:
        no = int(norm)
        selected = [(no, nameByNo[no])]
    else:
        exact = [t for t in themeList if t["themeName"] == norm]
        matches = exact or [t for t in themeList if norm in t["themeName"]]
        selected = [(t["themeNo"], t["themeName"]) for t in matches]

    if not selected:
        log.info("gather('theme', %r): 매칭 테마 없음 — 빈 결과", target)
        return pl.DataFrame(schema=_STOCKS_SCHEMA)

    records = await _crawlThemes(client, selected, progress=progress)
    return pl.DataFrame(records, schema=_STOCKS_SCHEMA)
