"""dartlab.gather.entry.handlers mirror 슬롯 + dispatch 검증 (G+ P-Q2.1).

룰 7 mirror 만족 + 12 axis handler 가 모두 dispatch table 에 등록됐는지 확인.
"""

from __future__ import annotations

import importlib

import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.entry.handlers`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.entry.handlers")


def test_all_axes_have_handler() -> None:
    """AXIS_REGISTRY 의 12 axis 모두 _AXIS_DISPATCH 에 handler 등록."""
    from dartlab.gather.entry.dispatch import AXIS_REGISTRY
    from dartlab.gather.entry.main import _AXIS_DISPATCH

    missing = set(AXIS_REGISTRY) - set(_AXIS_DISPATCH)
    extra = set(_AXIS_DISPATCH) - set(AXIS_REGISTRY)
    assert not missing, f"AXIS_REGISTRY axis 가 _AXIS_DISPATCH 에 없음: {missing}"
    assert not extra, f"_AXIS_DISPATCH 에 registry 미등록 axis: {extra}"


def test_handlers_callable() -> None:
    """현재 공개 handler 전체가 callable (가짜 g 로 호출 안 함) — 신규 axis 누락 차단."""
    from dartlab.gather.entry import handlers

    expected = [
        "handlePrice",
        "handleFlow",
        "handleFlowMany",
        "handleMacro",
        "handleNews",
        "handleSector",
        "handleInsider",
        "handleOwnership",
        "handlePeers",
        "handleKrx",
        "handleKrxIndex",
        "handleNarrative",
        "handleResearch",
        "handleCalendar",
        "handleDartDoc",
        "handleNaverTheme",
        "handleNaverIndustry",
        "handleNaverEtf",
        "handleNaverEtn",
    ]
    for name in expected:
        assert hasattr(handlers, name), f"handlers.{name} 누락"
        assert callable(getattr(handlers, name)), f"handlers.{name} 가 callable 아님"


def test_calendar_handler_raises() -> None:
    """handleCalendar 는 항상 ValueError — 폐기된 axis."""
    from dartlab.gather.entry.handlers import handleCalendar

    with pytest.raises(ValueError, match="0.10 부터 폐기"):
        handleCalendar(None, None, market="KR", start=None, end=None, marketExplicit=False)


def test_dartDoc_handler_requires_target() -> None:
    """handleDartDoc 는 target 없으면 ValueError."""
    from dartlab.gather.entry.handlers import handleDartDoc

    with pytest.raises(ValueError, match="rcept_no"):
        handleDartDoc(None, None, market="KR", start=None, end=None, marketExplicit=False)
    with pytest.raises(ValueError, match="rcept_no"):
        handleDartDoc(None, "", market="KR", start=None, end=None, marketExplicit=False)


def test_flow_handler_accepts_all_alias() -> None:
    """handleFlow 는 공개 kwargs all=True 를 Gather.flow(full=True) 로 변환한다."""
    from dartlab.gather.entry.handlers import handleFlow

    seen = {}

    class FakeGather:
        def flow(self, target, **kwargs):
            seen["target"] = target
            seen.update(kwargs)
            return "flow-result"

    result = handleFlow(
        FakeGather(),
        "005930",
        market="KR",
        start=None,
        end=None,
        marketExplicit=False,
        all=True,
        sleepSec=0.5,
        proxy="http://proxy.example:8080",
    )

    assert result == "flow-result"
    assert seen["target"] == "005930"
    assert seen["full"] is True
    assert seen["sleepSec"] == 0.5
    assert seen["proxy"] == "http://proxy.example:8080"


def test_info_handlers_preserve_complete_rows_and_provenance() -> None:
    """정보 축 변환은 source와 원본 필드를 버리지 않는다."""
    from dartlab.gather.entry.handlers import handleInsider, handleOwnership, handleSector
    from dartlab.gather.types import InsiderTrade, InstitutionOwnership, SectorInfo

    class FakeGather:
        @staticmethod
        def sector(target, *, market):
            return SectorInfo(
                sectorCode="278",
                sectorName="반도체",
                industryCode="261",
                industryName="반도체 제조업",
                market="코스피",
                source="kind+naver",
            )

        @staticmethod
        def insiderTrading(target, *, market):
            return [
                InsiderTrade(
                    date="20260701",
                    name="홍길동",
                    position="사내이사",
                    tradeType="취득",
                    changeShares=100,
                    afterShares=1_000,
                    reason="등기임원",
                    source="dart",
                )
            ]

        @staticmethod
        def ownership(target, *, market):
            return [
                InstitutionOwnership(
                    holderName="외국인 합계",
                    shares=1_000,
                    ratio=20.0,
                    value=50_000.0,
                    changeShares=10,
                    source="naver",
                )
            ]

    common = {"market": "KR", "start": None, "end": None, "marketExplicit": False}
    sector = handleSector(FakeGather(), "005930", **common)
    insider = handleInsider(FakeGather(), "005930", **common)
    ownership = handleOwnership(FakeGather(), "005930", **common)

    assert sector.row(0, named=True)["source"] == "kind+naver"
    assert insider.row(0, named=True) == {
        "date": "20260701",
        "name": "홍길동",
        "position": "사내이사",
        "tradeType": "취득",
        "changeShares": 100,
        "afterShares": 1_000,
        "reason": "등기임원",
        "source": "dart",
    }
    assert ownership.row(0, named=True) == {
        "holderName": "외국인 합계",
        "ratio": 20.0,
        "shares": 1_000,
        "value": 50_000.0,
        "changeShares": 10,
        "source": "naver",
    }


def test_naverTheme_handler_routesToThemeGroup(monkeypatch: pytest.MonkeyPatch) -> None:
    """handleNaverTheme → groups.collectGroup(groupKey='theme') + progress/maxAgeDays/refresh 전달."""
    import polars as pl

    from dartlab.gather.entry import handlers
    from dartlab.gather.sources.naver import groups

    seen: dict = {}

    async def fakeCollect(client, groupKey, target, **kwargs):
        seen["groupKey"] = groupKey
        seen["target"] = target
        seen.update(kwargs)
        return pl.DataFrame({"groupNo": [1]})

    monkeypatch.setattr(groups, "collectGroup", fakeCollect)

    class FakeGather:
        _client = object()

    df = handlers.handleNaverTheme(
        FakeGather(),
        "리튬",
        market="KR",
        start=None,
        end=None,
        marketExplicit=False,
        maxAgeDays=3,
        refresh=True,
    )
    assert df.height == 1
    assert seen["groupKey"] == "theme"
    assert seen["target"] == "리튬"
    assert seen["maxAgeDays"] == 3.0
    assert seen["refresh"] is True


def test_naverIndustry_handler_routesToIndustryGroup(monkeypatch: pytest.MonkeyPatch) -> None:
    """handleNaverIndustry → groups.collectGroup(groupKey='industry')."""
    import polars as pl

    from dartlab.gather.entry import handlers
    from dartlab.gather.sources.naver import groups

    seen: dict = {}

    async def fakeCollect(client, groupKey, target, **kwargs):
        seen["groupKey"] = groupKey
        return pl.DataFrame({"groupNo": [1]})

    monkeypatch.setattr(groups, "collectGroup", fakeCollect)

    class FakeGather:
        _client = object()

    handlers.handleNaverIndustry(FakeGather(), "list", market="KR", start=None, end=None, marketExplicit=False)
    assert seen["groupKey"] == "industry"


def test_naverProduct_handlers_routeToEtfEtn(monkeypatch: pytest.MonkeyPatch) -> None:
    """handleNaverEtf/handleNaverEtn → products.collectEtf/collectEtn (target 전달, 저장 없음)."""
    import polars as pl

    from dartlab.gather.entry import handlers
    from dartlab.gather.sources.naver import products

    seen: dict = {}

    async def fakeEtf(client, target=None):
        seen["etf"] = target
        return pl.DataFrame({"code": ["A"]})

    async def fakeEtn(client, target=None):
        seen["etn"] = target
        return pl.DataFrame({"code": ["B"]})

    monkeypatch.setattr(products, "collectEtf", fakeEtf)
    monkeypatch.setattr(products, "collectEtn", fakeEtn)

    class FakeGather:
        _client = object()

    handlers.handleNaverEtf(FakeGather(), "KODEX", market="KR", start=None, end=None, marketExplicit=False)
    handlers.handleNaverEtn(FakeGather(), None, market="KR", start=None, end=None, marketExplicit=False)
    assert seen == {"etf": "KODEX", "etn": None}


def test_gather_entry_flow_targets_parallel(monkeypatch: pytest.MonkeyPatch) -> None:
    """gather("flow", targets=[...]) 는 batch 결과에 stockCode 컬럼을 붙인다."""
    import dartlab.gather as gatherPkg
    from dartlab.gather.entry.main import GatherEntry
    from dartlab.gather.sources import flow as flowSource

    seen: list[tuple[str, dict]] = []

    class FakeGather:
        _client = object()

    async def fakeFetch(stockCode, **kwargs):
        seen.append((stockCode, kwargs))
        return [
            {
                "date": "20260611",
                "foreignNet": 1.0 if stockCode == "005930" else 2.0,
                "institutionNet": 0.0,
                "individualNet": 0.0,
                "foreignHoldingRatio": 50.0,
            }
        ]

    monkeypatch.setattr(gatherPkg, "getDefaultGather", lambda: FakeGather())
    monkeypatch.setattr(flowSource, "fetch", fakeFetch)

    df = GatherEntry()(
        "flow",
        targets=["005930", "000660"],
        start="2026-06-01",
        parallel=2,
        proxy="http://proxy.example:8080",
    )

    assert df.select("stockCode").to_series().to_list() == ["000660", "005930"]
    assert {call[0] for call in seen} == {"005930", "000660"}
    assert all(call[1]["proxy"] == "http://proxy.example:8080" for call in seen)
    assert all(call[1]["start"] == "2026-06-01" for call in seen)


def test_gather_entry_flow_targets_auto_parallel_with_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    """proxy 설정 상태에서도 targets 기본 병렬은 종목 단위로 동작한다."""
    import asyncio

    import dartlab.gather as gatherPkg
    from dartlab.gather.entry.main import GatherEntry
    from dartlab.gather.sources import flow as flowSource

    active = 0
    maxActive = 0
    seen: list[tuple[str, str | None]] = []

    class FakeGather:
        _client = object()

    async def fakeFetch(stockCode, **kwargs):
        nonlocal active, maxActive
        active += 1
        maxActive = max(maxActive, active)
        await asyncio.sleep(0.01)
        active -= 1
        seen.append((stockCode, kwargs.get("proxy")))
        return [
            {
                "date": "20260611",
                "foreignNet": 1.0,
                "institutionNet": 0.0,
                "individualNet": 0.0,
                "foreignHoldingRatio": 50.0,
            }
        ]

    monkeypatch.setattr(gatherPkg, "getDefaultGather", lambda: FakeGather())
    monkeypatch.setattr(flowSource, "fetch", fakeFetch)

    df = GatherEntry()(
        "flow",
        ["005930", "000660", "035420"],
        limit=1,
        proxy="http://proxy.example:8080",
    )

    assert df.height == 3
    assert maxActive > 1
    assert {stockCode for stockCode, _proxy in seen} == {"005930", "000660", "035420"}
    assert all(proxy == "http://proxy.example:8080" for _stockCode, proxy in seen)
