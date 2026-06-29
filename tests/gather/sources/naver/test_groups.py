"""naver.groups 단위 테스트 — 테마·업종 공통 collector (네트워크 없음).

sise_group 구조를 fake client 로 대체. 파싱·type 필터·target 분기·freshness 저장 검증.
config.dataDir → tmp_path 로 전수 크롤 저장 격리.
"""

from __future__ import annotations

import polars as pl
import pytest

from dartlab import config as cfg
from dartlab.gather.infra.http import runAsync
from dartlab.gather.sources.naver import groups

pytestmark = pytest.mark.unit


# sise_group?type=theme 리스트 — 테마 링크 2 (업종 링크 1 섞여도 type 필터로 걸러짐).
_THEME_LIST = """
<a href="/sise/sise_group_detail.naver?type=theme&no=523">리튬</a>
<a href="/sise/sise_group_detail.naver?type=theme&no=449">2차전지(생산)</a>
<a href="/sise/sise_group_detail.naver?type=upjong&no=283">전기제품</a>
"""
_UPJONG_LIST = '<a href="/sise/sise_group_detail.naver?type=upjong&no=283">전기제품</a>'

# 테마 상세 — 종목 2 + 편입사유.
_THEME_DETAIL = """
<table>
<tr><td><a href="/item/main.naver?code=270520">앱튼</a></td>
    <td><p class="info_txt">리튬 사업 추진.</p></td></tr>
<tr><td><a href="/item/main.naver?code=290670">대보마그네틱</a></td>
    <td><p class="info_txt">탄산리튬.</p></td></tr>
</table>
"""
# 업종 상세 — 편입사유(info_txt) 없음.
_UPJONG_DETAIL = """
<table>
<tr><td><a href="/item/main.naver?code=348370">엔켐</a></td></tr>
<tr><td><a href="/item/main.naver?code=416180">신성에스티</a></td></tr>
</table>
"""


class _FakeResp:
    """fake httpx 응답."""

    def __init__(self, text: str) -> None:
        self.text = text


class _FakeClient:
    """fake GatherHttpClient — list(type)/detail(type,no) 디스패치."""

    def __init__(self, listByType: dict[str, str], detailByNo: dict[int, str]) -> None:
        self._listByType = listByType
        self._detailByNo = detailByNo

    async def get(self, url: str, *, params=None, headers=None, **kwargs) -> _FakeResp:
        """sise_group_detail → detail[no], sise_group → list[type]."""
        params = params or {}
        if "sise_group_detail" in url:
            return _FakeResp(self._detailByNo.get(int(params.get("no")), ""))
        return _FakeResp(self._listByType.get(params.get("type"), ""))


@pytest.fixture
def tmpDataDir(tmp_path, monkeypatch):
    """config.dataDir → tmp_path (전수 크롤 저장 격리)."""
    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    return tmp_path


def test_parseGroupListHtml_typeFilter():
    """type 필터 — theme 페이지에서 upjong 링크는 제외, 중복 제거."""
    out = groups._parseGroupListHtml(_THEME_LIST, "theme")
    assert [g["groupNo"] for g in out] == [523, 449]
    assert out[0]["groupName"] == "리튬"
    assert out[0]["url"].endswith("type=theme&no=523")


def test_parseGroupDetailHtml_reasonAndNone():
    """테마 상세는 사유 매핑, 업종 상세는 빈 사유."""
    theme = groups._parseGroupDetailHtml(_THEME_DETAIL)
    assert theme[0] == {"stockCode": "270520", "stockName": "앱튼", "reason": "리튬 사업 추진."}
    upjong = groups._parseGroupDetailHtml(_UPJONG_DETAIL)
    assert [r["stockCode"] for r in upjong] == ["348370", "416180"]
    assert all(r["reason"] == "" for r in upjong)


def test_collectGroup_themeDefaultCombinedAndSaved(tmpDataDir):
    """theme 전수 → 결합 long + collectedAt 저장."""
    client = _FakeClient({"theme": _THEME_LIST}, {523: _THEME_DETAIL, 449: _THEME_DETAIL})
    df = runAsync(groups.collectGroup(client, "theme", None, progress=False))
    assert set(df["groupNo"].to_list()) == {523, 449}
    assert "collectedAt" in df.columns
    assert (tmpDataDir / "naver" / "theme" / "data.parquet").exists()


def test_collectGroup_industryDefault(tmpDataDir):
    """industry(업종) 전수 → 결합, 사유 없음."""
    client = _FakeClient({"upjong": _UPJONG_LIST}, {283: _UPJONG_DETAIL})
    df = runAsync(groups.collectGroup(client, "industry", None, progress=False))
    assert df["groupName"].unique().to_list() == ["전기제품"]
    assert df.height == 2
    assert all(r == "" for r in df["reason"].to_list())
    assert (tmpDataDir / "naver" / "industry" / "data.parquet").exists()


def test_collectGroup_list():
    """target 'list' → 그룹 목록만 (groupNo/groupName/url)."""
    client = _FakeClient({"theme": _THEME_LIST}, {})
    df = runAsync(groups.collectGroup(client, "theme", "list"))
    assert df.columns == ["groupNo", "groupName", "url"]
    assert df["groupNo"].to_list() == [523, 449]


def test_collectGroup_byName():
    """그룹명 매칭 → 해당 그룹 편입종목 (라이브)."""
    client = _FakeClient({"theme": _THEME_LIST}, {523: _THEME_DETAIL})
    df = runAsync(groups.collectGroup(client, "theme", "리튬"))
    assert set(df["groupNo"].to_list()) == {523}
    assert df["stockCode"].to_list() == ["270520", "290670"]


def test_collectGroup_freshReloadSkipsCrawl(tmpDataDir):
    """7일 내 저장본 있으면 재크롤 없이 직독, refresh=True 면 재크롤."""
    calls = {"n": 0}

    class _Counting(_FakeClient):
        async def get(self, url, *, params=None, headers=None, **kwargs):
            calls["n"] += 1
            return await super().get(url, params=params, headers=headers, **kwargs)

    client = _Counting({"theme": _THEME_LIST}, {523: _THEME_DETAIL, 449: _THEME_DETAIL})
    runAsync(groups.collectGroup(client, "theme", None, progress=False))
    first = calls["n"]
    runAsync(groups.collectGroup(client, "theme", None, progress=False))
    assert calls["n"] == first  # 직독
    runAsync(groups.collectGroup(client, "theme", None, progress=False, refresh=True))
    assert calls["n"] > first  # 재크롤


def test_collectGroup_noMatchEmpty():
    """매칭 0 → 빈 DataFrame, 스키마 유지."""
    client = _FakeClient({"theme": _THEME_LIST}, {})
    df = runAsync(groups.collectGroup(client, "theme", "005930"))
    assert df.is_empty()
    assert df.columns == ["groupNo", "groupName", "stockCode", "stockName", "reason"]
    assert df.schema["groupNo"] == pl.Int64
