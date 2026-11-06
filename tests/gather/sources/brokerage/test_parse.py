"""brokerage.parse 단위 테스트 — 증권사별 파서 어댑터 (픽스처, 네트워크 0)."""

from __future__ import annotations

import json

import pytest

from dartlab.gather.sources.brokerage.parse import (
    _normDate,
    _parseBookook,
    _parseHanyang,
    _parseMiraeasset,
    _parseNh,
)

pytestmark = pytest.mark.unit

_MIRAE_HTML = """
<table><thead><tr><th>작성일</th><th>제목</th><th>첨부</th><th>작성자</th></tr></thead>
<tbody>
<tr><td>2026-06-25</td>
    <td><a href="javascript:view('111','1800')">삼성전자 (005930/매수) 좋다</a></td>
    <td></td><td>홍길동</td></tr>
</tbody></table>
"""

_NH_HTML = """
<ul><li><a href="/research/authCheck?type=view&rshPprNo=123">
<p class="sort">기업</p><p class="tit">[한세실업] 과도한 우려</p>
<p class="info"><span class="info_name">정지윤</span><span class="info_date">2026.06.26</span></p>
</a></li></ul>
"""

_HANYANG_BOARD = "/board/00000000-0000-0000-0000-000009000004"
_HANYANG_POST_A = "b8af9b37-feb8-42fb-8968-d56810922fdd"
_HANYANG_POST_B = "88a63537-171f-462a-99ba-200ab0838cc6"
_HANYANG_POST_C = "b552c115-5b1b-4baf-9186-7b585c631836"


def _hanyangRow(number: int, title: str, date: str) -> str:
    """2026-11 개편 뒤 한양 표 행: 제목은 링크 없는 버튼, 뒤에 등록일·첨부·조회 칸."""
    return (
        f'<tr><td>{number}</td><td class="text-left"><button type="button" class="w-full">{title}</button></td>'
        f'<td>{date}</td><td><span title="첨부파일 있음"></span></td><td>2255</td></tr>'
    )


def _hanyangPage(rows: str, posts: list[tuple[str, str]] | None = None) -> str:
    """표 + Next.js 서버 데이터 조각(글 번호·제목·보드 경로)이 든 한양 보드 페이지."""
    head = "<thead><tr><th>번호</th><th>제목</th><th>등록일</th><th>첨부</th><th>조회</th></tr></thead>"
    html = f'<table class="board-list-table">{head}<tbody>{rows}</tbody></table>'
    if posts is not None:
        flight = '1:["$","x",null,{"posts":[' + ",".join(
            f'{{"postUuid":"{uuid}","title":{json.dumps(title, ensure_ascii=False)},"viewCount":1}}'
            for uuid, title in posts
        )
        flight += f'],"basePath":"{_HANYANG_BOARD}","boardUuid":"x"}}]\n'
        html += f"<script>self.__next_f.push([1,{json.dumps(flight, ensure_ascii=False)}])</script>"
    return html


_HANYANG_HTML = _hanyangPage(
    _hanyangRow(2075, "[10/21] 펌텍코리아(251970) : 물 들어올 땐, 펌텍코리아", "2026-10-21")
    + _hanyangRow(3, "커버리지 제외 종목", "2024-03-06")
    + _hanyangRow(2, "커버리지 제외 종목", "2022-11-21"),
    [
        (_HANYANG_POST_C, "[10/21] 펌텍코리아(251970) : 물 들어올 땐, 펌텍코리아"),
        (_HANYANG_POST_A, "커버리지 제외 종목"),
        (_HANYANG_POST_B, "커버리지 제외 종목"),
    ],
)

# 부국: 기업분석(6셀: 번호·날짜·제목·-·저자·조회수) + 시황(5셀: 저자 없음·끝=조회수) 실제 양식.
_BOOKOOK_HTML = """
<table><tbody>
<tr><td>2399</td><td>2026/06/22</td>
    <td><a href="javascript:void(0);" onclick="viewDetailContent('2512')">에스바이오메딕스(304360) - Not Rated</a></td>
    <td></td><td>유대웅</td><td>79</td></tr>
<tr><td>3430</td><td>2026/06/26</td>
    <td><a href="javascript:__fileDownload('1','6328','x.pdf','re02','2026/06')">아침종합자료(06/26/금)</a></td>
    <td></td><td>10</td></tr>
</tbody></table>
"""


def test_norm_date() -> None:
    assert _normDate("2026.06.26") == "2026-06-26"
    assert _normDate("2026/06/26") == "2026-06-26"
    assert _normDate("") == ""


def test_parse_miraeasset() -> None:
    rows = _parseMiraeasset(_MIRAE_HTML, "기업분석", "https://fallback")
    assert len(rows) == 1
    r = rows[0]
    assert r.broker == "miraeasset"
    assert r.pubDate == "2026-06-25"
    assert r.reportType == "기업분석"
    assert r.author == "홍길동"
    assert "messageId=111" in r.url and "categoryId=1800" in r.url


def test_parse_miraeasset_no_table() -> None:
    assert _parseMiraeasset("<html><body>없음</body></html>", "기업분석", "u") == []


def test_parse_nh() -> None:
    rows = _parseNh(_NH_HTML, "기업분석", "https://fallback")
    assert len(rows) == 1
    r = rows[0]
    assert r.broker == "nh"
    assert r.title == "[한세실업] 과도한 우려"
    assert r.reportType == "기업"  # 행별 p.sort 우선
    assert r.author == "정지윤"
    assert r.pubDate == "2026-06-26"
    assert r.url.startswith("https://m.nhqv.com/research/authCheck")


def test_parse_hanyang() -> None:
    rows = _parseHanyang(_HANYANG_HTML, "기업분석", "https://fallback")
    assert len(rows) == 3
    r = rows[0]
    assert r.broker == "hanyang"
    assert r.reportType == "기업분석"
    assert r.pubDate == "2026-10-21"
    assert "펌텍코리아(251970)" in r.title
    # 제목은 링크 없는 버튼 → 글 주소 = 보드 경로 + 서버 데이터의 글 번호 (한양 자기 서버)
    assert r.url == f"https://www.hygood.co.kr{_HANYANG_BOARD}/{_HANYANG_POST_C}"


def test_parse_hanyang_same_title_keeps_row_order() -> None:
    """제목이 같은 글(커버리지 제외 종목)은 표 순서대로 서로 다른 글 번호를 받는다."""
    rows = _parseHanyang(_HANYANG_HTML, "시황", "https://fallback")
    assert [r.pubDate for r in rows[1:]] == ["2024-03-06", "2022-11-21"]
    assert rows[1].url.endswith(_HANYANG_POST_A)
    assert rows[2].url.endswith(_HANYANG_POST_B)
    assert len({r.reportId() for r in rows}) == 3


def test_parse_hanyang_without_payload_uses_board_url() -> None:
    """서버 데이터를 못 읽어도 행은 버리지 않고 보드 주소로 남긴다(0행 장애로 번지지 않게)."""
    html = _hanyangPage(_hanyangRow(1, "[10/21] 핌스(347770) : 기술력에 비해 너무 싼 주가", "2026-10-21"))
    rows = _parseHanyang(html, "기업분석", "https://fallback")
    assert len(rows) == 1
    assert rows[0].url == "https://fallback"
    assert rows[0].pubDate == "2026-10-21"


def test_parse_hanyang_anchor_link() -> None:
    """제목 칸에 링크(a)가 다시 생기면 그 주소를 쓴다. jsessionid 꼬리는 지운다."""
    html = (
        "<table><tbody><tr><td>2052</td>"
        '<td><a href="/board/x/detail/2087;jsessionid=ABC?pageIndex=1">[06/25] 리브스메드(491000) : 추천종목</a></td>'
        "<td>2026.06.25</td><td></td><td>304</td></tr></tbody></table>"
    )
    rows = _parseHanyang(html, "기업분석", "https://fallback")
    assert len(rows) == 1
    assert rows[0].pubDate == "2026-06-25"
    assert rows[0].url == "https://www.hygood.co.kr/board/x/detail/2087"


def test_parse_hanyang_no_detail() -> None:
    assert _parseHanyang("<table><tbody><tr><td>없음</td></tr></tbody></table>", "기업분석", "u") == []


def test_parse_bookook() -> None:
    rows = _parseBookook(_BOOKOOK_HTML, "기업분석", "https://www.bookook.co.kr/research/research_5")
    assert len(rows) == 2
    r0 = rows[0]
    assert r0.broker == "bookook"
    assert r0.pubDate == "2026-06-22"
    assert "에스바이오메딕스(304360)" in r0.title
    assert r0.author == "유대웅"
    assert r0.url == "https://www.bookook.co.kr/research/research_5"  # per-report URL 부재 → 보드 URL
    # 시황 행: 마지막 셀이 조회수(숫자) → author None
    assert rows[1].author is None
    assert "아침종합자료" in rows[1].title


def test_parse_bookook_no_date() -> None:
    assert _parseBookook("<table><tbody><tr><td>헤더</td><td>제목</td></tr></tbody></table>", "기업분석", "u") == []
