"""naverTheme source 단위 테스트 — 순수 파싱 + collectTheme 오케스트레이션 (네트워크 없음).

라이브 페이지 구조는 fake client 로 대체. 정규식·target 분기·스키마만 검증.
unit marker — ci-fast 에서 실행.
"""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.gather.infra.http import runAsync
from dartlab.gather.sources import naverTheme

pytestmark = pytest.mark.unit


# 라이브 구조를 축약한 샘플 — 테마 링크 2개, 페이지네이션 없음(lastPage=1).
_LIST_HTML = """
<html><body>
<a href="/sise/sise_group_detail.naver?type=theme&no=523">리튬</a>
<a href="/sise/sise_group_detail.naver?type=theme&no=449">2차전지(생산)</a>
</body></html>
"""

# 상세 — 종목 2개, 둘째는 편입사유(info_txt) 없음.
_DETAIL_523 = """
<table>
<tr><td><a href="/item/main.naver?code=270520">앱튼</a></td>
    <td><p class="info_txt">리튬 사업 추진 중.</p></td></tr>
<tr><td><a href="/item/main.naver?code=290670">대보마그네틱</a></td></tr>
</table>
"""

_DETAIL_449 = """
<table>
<tr><td><a href="/item/main.naver?code=348370">엔켐</a></td>
    <td><p class="info_txt">2차전지 전해액 생산.</p></td></tr>
</table>
"""


class _FakeResp:
    """fake httpx 응답 — text 속성만."""

    def __init__(self, text: str) -> None:
        self.text = text


class _FakeClient:
    """fake GatherHttpClient — URL/파라미터로 샘플 HTML 디스패치."""

    def __init__(self, listHtml: str, detail: dict[int, str]) -> None:
        self._listHtml = listHtml
        self._detail = detail

    async def get(self, url: str, *, params=None, headers=None, **kwargs) -> _FakeResp:
        """list URL → listHtml, detail URL → detail[no]."""
        params = params or {}
        if "sise_group_detail" in url:
            return _FakeResp(self._detail.get(int(params.get("no")), ""))
        return _FakeResp(self._listHtml)


def test_parseThemeListHtml():
    """테마 링크 파싱 + lastPage 기본값 1 (페이지네이션 링크 없음)."""
    themes, lastPage = naverTheme._parseThemeListHtml(_LIST_HTML)
    assert lastPage == 1
    assert [t["themeNo"] for t in themes] == [523, 449]
    assert themes[0]["themeName"] == "리튬"
    assert themes[0]["url"].endswith("type=theme&no=523")


def test_parseThemeListHtml_pagination():
    """페이지네이션 링크가 있으면 최대값이 lastPage."""
    html = _LIST_HTML + '<a href="/sise/theme.naver?page=2">2</a><a href="/sise/theme.naver?page=7">7</a>'
    _, lastPage = naverTheme._parseThemeListHtml(html)
    assert lastPage == 7


def test_parseThemeDetailHtml():
    """편입종목 파싱 — 종목코드/종목명/편입사유, 사유 없으면 빈 문자열."""
    rows = naverTheme._parseThemeDetailHtml(_DETAIL_523)
    assert len(rows) == 2
    assert rows[0] == {"stockCode": "270520", "stockName": "앱튼", "reason": "리튬 사업 추진 중."}
    assert rows[1]["reason"] == ""


def test_collectTheme_defaultCrawlsAllCombined():
    """target 없으면 전 테마 개별 수집 → 하나의 long DataFrame 으로 결합 (기본 동작)."""
    client = _FakeClient(_LIST_HTML, {523: _DETAIL_523, 449: _DETAIL_449})
    df = runAsync(naverTheme.collectTheme(client, None, progress=False))
    assert df.columns == ["themeNo", "themeName", "stockCode", "stockName", "reason"]
    assert set(df["themeNo"].to_list()) == {523, 449}  # 전 테마 결합
    assert df.height == 3


def test_collectTheme_listKeyword():
    """target 'list' 면 테마 리스트만 (_LIST_SCHEMA)."""
    client = _FakeClient(_LIST_HTML, {})
    df = runAsync(naverTheme.collectTheme(client, "list"))
    assert df.columns == ["themeNo", "themeName", "url"]
    assert df.height == 2
    assert df["themeNo"].to_list() == [523, 449]


def test_collectTheme_byName():
    """테마명 exact 매칭 → 해당 테마 편입종목 long (themeNo/themeName 부착)."""
    client = _FakeClient(_LIST_HTML, {523: _DETAIL_523})
    df = runAsync(naverTheme.collectTheme(client, "리튬"))
    assert df.columns == ["themeNo", "themeName", "stockCode", "stockName", "reason"]
    assert df.height == 2
    assert set(df["themeNo"].to_list()) == {523}
    assert df["stockCode"].to_list() == ["270520", "290670"]


def test_collectTheme_byNumber():
    """숫자 target → themeNo 직접 매칭."""
    client = _FakeClient(_LIST_HTML, {449: _DETAIL_449})
    df = runAsync(naverTheme.collectTheme(client, "449"))
    assert df.height == 1
    assert df["stockName"].to_list() == ["엔켐"]


def test_collectTheme_all():
    """'all' → 전 테마 편입종목 concat. progress=True 로 SSOT rich 진행바 경로도 실행."""
    client = _FakeClient(_LIST_HTML, {523: _DETAIL_523, 449: _DETAIL_449})
    df = runAsync(naverTheme.collectTheme(client, "all", progress=True))
    assert set(df["themeNo"].to_list()) == {523, 449}
    assert df.height == 3


def test_themeProgress_marimoForcesTerminal():
    """마리모 stdout 모듈 감지 시 force_terminal console (라이브 ANSI). 그 외엔 SSOT getProgress."""
    import sys

    class _MarimoStream:
        pass

    _MarimoStream.__module__ = "marimo._messaging.streams"
    orig = sys.stdout
    sys.stdout = _MarimoStream()
    try:
        prog = naverTheme._themeProgress()
    finally:
        sys.stdout = orig
    assert prog.console.is_terminal is True


def test_collectTheme_noMatchEmpty():
    """매칭 0 (예: 6자리 종목코드) → 빈 DataFrame, 스키마 유지, 크래시 없음."""
    client = _FakeClient(_LIST_HTML, {})
    df = runAsync(naverTheme.collectTheme(client, "005930"))
    assert df.is_empty()
    assert df.columns == ["themeNo", "themeName", "stockCode", "stockName", "reason"]
    assert df.schema["themeNo"] == pl.Int64
