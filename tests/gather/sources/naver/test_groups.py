"""naver.groups 단위 테스트. 테마·업종 공통 collector (네트워크 없음).

네이버증권 JSON API(``m.stock.naver.com/api/stocks/<kind>[/<no>]``) 를 fake client 로 대체한다.
파싱·페이지네이션·target 분기·freshness 저장을 검증하고, config.dataDir → tmp_path 로 전수 크롤
저장을 격리한다.
"""

from __future__ import annotations

import json

import polars as pl
import pytest

from dartlab import config as cfg
from dartlab.gather.infra.http import runAsync
from dartlab.gather.sources.naver import groups

pytestmark = pytest.mark.unit


def _stock(code: str, name: str) -> dict:
    return {"stockType": "domestic", "itemCode": code, "stockName": name, "closePrice": "1,000"}


# 목록 API ``groups`` (실측 응답의 필드 부분집합).
_THEME_GROUPS = [
    {"no": 523, "name": "리튬", "totalCount": 2, "changeRate": "1.20"},
    {"no": 449, "name": "2차전지(생산)", "totalCount": 2, "changeRate": "-0.50"},
]
_INDUSTRY_GROUPS = [{"no": 283, "name": "전기제품", "totalCount": 2, "changeRate": "0.10"}]

# 편입종목 API. 테마는 themeItemInfoMap(종목코드 → 편입사유) 동행, 업종은 없음.
_THEME_DETAIL = {
    "stocks": [_stock("270520", "앱튼"), _stock("290670", "대보마그네틱")],
    "themeItemInfoMap": {"270520": "리튬 사업 추진.", "290670": " 탄산리튬. "},
}
_INDUSTRY_DETAIL = {"stocks": [_stock("348370", "엔켐"), _stock("416180", "신성에스티")]}


class _FakeResp:
    """fake httpx 응답. dict 는 그대로, 문자열은 JSON 으로 해석(빈 문자열은 JSONDecodeError)."""

    def __init__(self, payload) -> None:
        self._payload = payload

    def json(self):
        if isinstance(self._payload, str):
            return json.loads(self._payload)
        return self._payload


def _paged(payload, params: dict):
    """서버처럼 groups/stocks 목록을 page·pageSize 로 잘라 totalCount 와 함께 돌려준다."""
    if not isinstance(payload, dict):
        return payload
    key = "groups" if "groups" in payload else "stocks"
    rows = payload.get(key) or []
    page, size = int(params.get("page", 1)), int(params.get("pageSize", 20))
    return {**payload, key: rows[(page - 1) * size : page * size], "totalCount": len(rows)}


class _FakeClient:
    """fake GatherHttpClient. ``/api/stocks/<kind>`` → 목록, ``/api/stocks/<kind>/<no>`` → 편입종목."""

    def __init__(self, listByKind: dict, detailByNo: dict) -> None:
        self._listByKind = listByKind
        self._detailByNo = detailByNo
        self.calls: list[tuple[str, dict]] = []

    async def get(self, url: str, *, params=None, headers=None, **kwargs) -> _FakeResp:
        params = dict(params or {})
        self.calls.append((url, params))
        kind, _, no = url.split("/api/stocks/", 1)[1].partition("/")
        payload = self._detailByNo.get(int(no), "") if no else self._listByKind.get(kind, "")
        return _FakeResp(_paged(payload, params))


@pytest.fixture
def tmpDataDir(tmp_path, monkeypatch):
    """config.dataDir → tmp_path (전수 크롤 저장 격리)."""
    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    return tmp_path


def test_parseGroupList_dedupAndScreenUrl():
    """번호 중복·결측·빈 이름은 버리고, url 은 stock.naver.com 화면 주소."""
    raw = [*_THEME_GROUPS, {"no": 523, "name": "리튬"}, {"no": None, "name": "x"}, {"no": 7, "name": " "}]
    out = groups._parseGroupList(raw, "theme")
    assert [g["groupNo"] for g in out] == [523, 449]
    assert out[0]["groupName"] == "리튬"
    assert out[0]["url"] == "https://stock.naver.com/market/stock/kr/theme/523"


def test_parseGroupStocks_reasonAndNone():
    """테마는 사유 매핑(공백 정리), 업종은 빈 사유. 코드 중복은 한 번만."""
    theme = groups._parseGroupStocks(_THEME_DETAIL["stocks"], _THEME_DETAIL["themeItemInfoMap"])
    assert theme[0] == {"stockCode": "270520", "stockName": "앱튼", "reason": "리튬 사업 추진."}
    assert theme[1]["reason"] == "탄산리튬."
    industry = groups._parseGroupStocks([*_INDUSTRY_DETAIL["stocks"], _stock("348370", "엔켐")], {})
    assert [r["stockCode"] for r in industry] == ["348370", "416180"]
    assert all(r["reason"] == "" for r in industry)


def test_fetchGroupList_directAndLimit():
    """fetchGroupList: 목록 API 경로 + provenance + limit."""
    client = _FakeClient({"theme": {"groups": _THEME_GROUPS}}, {})
    rows = runAsync(groups.fetchGroupList(client, "theme"))
    assert [r["groupNo"] for r in rows] == [523, 449]
    assert {r["source"] for r in rows} == {"naver"}
    assert all(r["fetchedAt"] for r in rows)
    assert client.calls[0][0] == "https://m.stock.naver.com/api/stocks/theme"
    assert client.calls[0][1] == {"page": 1, "pageSize": groups._PAGE_SIZE}
    limited = runAsync(groups.fetchGroupList(client, "theme", limit=1))
    assert [r["groupNo"] for r in limited] == [523]


def test_fetchGroupList_paginatesUntilTotal(monkeypatch):
    """pageSize 를 넘는 목록은 totalCount 까지 페이지를 이어 받고, 404 가 나는 다음 페이지는 요청하지 않는다."""
    monkeypatch.setattr(groups, "_PAGE_SIZE", 2)
    many = [{"no": n, "name": f"그룹{n}"} for n in (1, 2, 3, 4)]
    client = _FakeClient({"industry": {"groups": many}}, {})
    rows = runAsync(groups.fetchGroupList(client, "industry"))
    assert [r["groupNo"] for r in rows] == [1, 2, 3, 4]
    assert [c[1]["page"] for c in client.calls] == [1, 2]


def test_fetchGroupStocks_directReasonAndLimit():
    """fetchGroupStocks: 단일 그룹 편입종목 + 사유 매핑 + limit."""
    client = _FakeClient({}, {523: _THEME_DETAIL})
    rows = runAsync(groups.fetchGroupStocks(client, "theme", 523))
    assert [r["stockCode"] for r in rows] == ["270520", "290670"]
    assert rows[0]["reason"] == "리튬 사업 추진."
    assert rows[0]["source"] == "naver"
    assert rows[0]["fetchedAt"]
    assert client.calls[0][0] == "https://m.stock.naver.com/api/stocks/theme/523"
    assert len(runAsync(groups.fetchGroupStocks(client, "theme", 523, limit=1))) == 1


def test_fetchGroupStocks_multiPageMergesReasons(monkeypatch):
    """100 종목 초과 그룹처럼 여러 페이지로 나뉘어도 전 종목과 사유를 모은다."""
    monkeypatch.setattr(groups, "_PAGE_SIZE", 1)
    client = _FakeClient({}, {523: _THEME_DETAIL})
    rows = runAsync(groups.fetchGroupStocks(client, "theme", 523))
    assert [r["stockCode"] for r in rows] == ["270520", "290670"]
    assert [r["reason"] for r in rows] == ["리튬 사업 추진.", "탄산리튬."]
    assert [c[1]["page"] for c in client.calls] == [1, 2]


def test_collectGroup_themeDefaultCombinedAndSaved(tmpDataDir):
    """theme 전수 → 결합 long + collectedAt 저장."""
    client = _FakeClient({"theme": {"groups": _THEME_GROUPS}}, {523: _THEME_DETAIL, 449: _THEME_DETAIL})
    df = runAsync(groups.collectGroup(client, "theme", None, progress=False))
    assert set(df["groupNo"].to_list()) == {523, 449}
    assert "collectedAt" in df.columns
    assert (tmpDataDir / "naver" / "theme" / "data.parquet").exists()


def test_collectGroup_industryDefault(tmpDataDir):
    """industry(업종) 전수 → 결합, 사유 없음."""
    client = _FakeClient({"industry": {"groups": _INDUSTRY_GROUPS}}, {283: _INDUSTRY_DETAIL})
    df = runAsync(groups.collectGroup(client, "industry", None, progress=False))
    assert df["groupName"].unique().to_list() == ["전기제품"]
    assert df.height == 2
    assert all(r == "" for r in df["reason"].to_list())
    assert (tmpDataDir / "naver" / "industry" / "data.parquet").exists()


def test_collectGroup_list():
    """target 'list' → 그룹 목록만 (groupNo/groupName/url)."""
    client = _FakeClient({"theme": {"groups": _THEME_GROUPS}}, {})
    df = runAsync(groups.collectGroup(client, "theme", "list"))
    assert df.columns == ["groupNo", "groupName", "url", "source", "fetchedAt"]
    assert df["groupNo"].to_list() == [523, 449]


def test_collectGroup_byNameAndNumber():
    """그룹명 매칭과 그룹 번호 지정 → 해당 그룹 편입종목 (라이브)."""
    client = _FakeClient({"theme": {"groups": _THEME_GROUPS}}, {523: _THEME_DETAIL, 449: _THEME_DETAIL})
    byName = runAsync(groups.collectGroup(client, "theme", "리튬"))
    assert set(byName["groupNo"].to_list()) == {523}
    assert byName["stockCode"].to_list() == ["270520", "290670"]
    byNo = runAsync(groups.collectGroup(client, "theme", "449"))
    assert set(byNo["groupName"].to_list()) == {"2차전지(생산)"}


def test_collectGroup_freshReloadSkipsCrawl(tmpDataDir):
    """7일 내 저장본 있으면 재크롤 없이 직독, refresh=True 면 재크롤."""
    client = _FakeClient({"theme": {"groups": _THEME_GROUPS}}, {523: _THEME_DETAIL, 449: _THEME_DETAIL})
    runAsync(groups.collectGroup(client, "theme", None, progress=False))
    first = len(client.calls)
    runAsync(groups.collectGroup(client, "theme", None, progress=False))
    assert len(client.calls) == first  # 직독
    runAsync(groups.collectGroup(client, "theme", None, progress=False, refresh=True))
    assert len(client.calls) > first  # 재크롤


def test_collectGroup_noMatchEmpty():
    """매칭 0 → 빈 DataFrame, 스키마 유지 (종목코드를 넣어도 그룹 번호로 오인하지 않음)."""
    client = _FakeClient({"theme": {"groups": _THEME_GROUPS}}, {})
    df = runAsync(groups.collectGroup(client, "theme", "005930"))
    assert df.is_empty()
    assert df.columns == ["groupNo", "groupName", "stockCode", "stockName", "reason", "source", "fetchedAt"]
    assert df.schema["groupNo"] == pl.Int64


def test_empty_group_provider_page_is_schema_failure():
    """목록/상세 응답 소실(빈 본문·HTML·형식 변경)을 유효한 0건으로 위장하지 않는다."""
    blank = _FakeClient({"theme": ""}, {523: ""})
    with pytest.raises(ValueError, match="목록 응답"):
        runAsync(groups.fetchGroupList(blank, "theme"))
    with pytest.raises(ValueError, match="상세 응답"):
        runAsync(groups.fetchGroupStocks(blank, "theme", 523))

    html = _FakeClient({"theme": "<!DOCTYPE html><html></html>"}, {})
    with pytest.raises(ValueError, match="목록 응답"):
        runAsync(groups.fetchGroupList(html, "theme"))

    reshaped = _FakeClient({"theme": {"items": _THEME_GROUPS}}, {523: {"stocks": []}})
    with pytest.raises(ValueError, match="목록 응답"):
        runAsync(groups.fetchGroupList(reshaped, "theme"))
    with pytest.raises(ValueError, match="상세 응답"):
        runAsync(groups.fetchGroupStocks(reshaped, "theme", 523))
