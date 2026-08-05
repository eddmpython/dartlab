"""업종 횡단면 표가 프로세스 안에서 한 번만 읽히는지 지키는 회귀 테스트.

배경. 처음에는 이 표를 `BoundedCache` 에 넣었다. 그런데 그 캐시는 메모리 압력이 오르면
항목 수를 줄인다. Company 하나가 수백 MB 인 이 저장소에서는 압력이 늘 높아 표가 곧바로
쫓겨났고, 실측(2026-08-06) 결과 예열 16 초 뒤에도 다음 호출이 14 초를 다시 냈다.

그래서 원본 DataFrame 을 버리고 필요한 열만 실수로 뽑아 들고 있는 쪽으로 바꿨다.
여기서 지키는 것은 그 계약이다.
"""

from __future__ import annotations

from typing import Any

import polars as pl
import pytest

from dartlab.industry.calcs import sectorTables


@pytest.fixture(autouse=True)
def _resetModuleState() -> Any:
    """모듈 전역을 케이스마다 비운다. 앞 케이스가 채운 표가 뒤로 새면 판정이 무의미하다."""
    sectorTables._distilled = {}
    sectorTables._loadedAt = 0.0
    yield
    sectorTables._distilled = {}
    sectorTables._loadedAt = 0.0


def _fakeLoader(calls: list[str]) -> Any:
    """스캐너 호출을 세는 대역. 실제 스캔은 초 단위라 테스트에서 부를 수 없다."""

    def _load(moduleName: str, functionName: str) -> Any:
        calls.append(functionName)
        if functionName == "scanProfitability":
            return pl.DataFrame({"stockCode": ["005930", "000660"], "opMargin": [13.1, 22.0], "roe": [8.0, 15.0]})
        if functionName == "scanGrowth":
            return pl.DataFrame({"stockCode": ["005930"], "revenueCagr": [7.2]})
        if functionName == "scanLiquidity":
            return pl.DataFrame({"stockCode": ["005930"], "currentRatio": [253.9]})
        if functionName == "scanDebtMix":
            # 이 스캐너만 DataFrame 이 아니라 dict 를 준다. 두 모양을 다 받아야 한다.
            return {"005930": {"부채비율": 30.1, "총부채": 1.0}, "000660": {"부채비율": 55.0}}
        return None

    return _load


def test다섯축을모두준다(monkeypatch: pytest.MonkeyPatch) -> None:
    """수익성 셋과 건전성 둘. 건전성이 빠지면 재무 건전성 질문에 기준이 없다."""
    monkeypatch.setattr(sectorTables, "_load", _fakeLoader([]))
    tables = sectorTables.sectorMetricTables()
    assert set(tables) == {"opMargin", "roe", "revenueCagr", "currentRatio", "debtRatio"}
    assert tables["debtRatio"]["005930"] == 30.1
    assert tables["currentRatio"]["005930"] == 253.9


def test두번째호출은다시읽지않는다(monkeypatch: pytest.MonkeyPatch) -> None:
    """이게 깨져서 예열이 무의미했다. 표는 회사가 아니라 시장에 속한다."""
    calls: list[str] = []
    monkeypatch.setattr(sectorTables, "_load", _fakeLoader(calls))
    sectorTables.sectorMetricTables()
    firstRound = len(calls)
    sectorTables.sectorMetricTables()
    sectorTables.sectorMetricTables()
    assert firstRound > 0
    assert len(calls) == firstRound


def test같은스캐너를축마다다시부르지않는다(monkeypatch: pytest.MonkeyPatch) -> None:
    """영업이익률과 ROE 는 같은 스캐너에서 온다. 두 번 부르면 그만큼 그냥 손해다."""
    calls: list[str] = []
    monkeypatch.setattr(sectorTables, "_load", _fakeLoader(calls))
    sectorTables.sectorMetricTables()
    assert calls.count("scanProfitability") == 1


def test축하나가실패해도나머지는산다(monkeypatch: pytest.MonkeyPatch) -> None:
    """부채 스캔이 없는 환경에서 수익성까지 같이 죽으면 안 된다."""

    def _load(moduleName: str, functionName: str) -> Any:
        if functionName == "scanDebtMix":
            return None
        return _fakeLoader([])(moduleName, functionName)

    monkeypatch.setattr(sectorTables, "_load", _load)
    tables = sectorTables.sectorMetricTables()
    assert tables["debtRatio"] == {}
    assert tables["opMargin"]["005930"] == 13.1


def test원본표를들고있지않는다(monkeypatch: pytest.MonkeyPatch) -> None:
    """DataFrame 을 붙들면 압력 관리가 캐시를 되돌린다. 실수만 남긴다."""
    monkeypatch.setattr(sectorTables, "_load", _fakeLoader([]))
    tables = sectorTables.sectorMetricTables()
    for values in tables.values():
        assert all(isinstance(v, float) for v in values.values())
    assert not any(isinstance(v, pl.DataFrame) for v in sectorTables._distilled.values())


def test값없는회사는키가없다(monkeypatch: pytest.MonkeyPatch) -> None:
    """0 으로 채우면 부채가 없는 회사와 데이터가 없는 회사가 같아진다."""
    monkeypatch.setattr(sectorTables, "_load", _fakeLoader([]))
    tables = sectorTables.sectorMetricTables()
    assert "000660" not in tables["revenueCagr"]
    assert "000660" in tables["debtRatio"]
