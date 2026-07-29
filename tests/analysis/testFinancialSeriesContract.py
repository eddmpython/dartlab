"""DART와 EDGAR Company의 재무 시계열 호출 계약 회귀."""

from __future__ import annotations

import pytest

from dartlab.analysis.financial.insight.pipeline import _seriesPairsFromCompany

pytestmark = pytest.mark.unit


def testDartCompanyBuilderUsesExplicitQuarterAndYearModes() -> None:
    calls: list[str] = []

    class DartCompany:
        def _getFinanceBuild(self, mode: str):
            calls.append(mode)
            return ({"IS": {"sales": [1.0]}}, [mode])

    assert _seriesPairsFromCompany(DartCompany()) == (
        ({"IS": {"sales": [1.0]}}, ["q"]),
        ({"IS": {"sales": [1.0]}}, ["y"]),
    )
    assert calls == ["q", "y"]


def testEdgarCompanyBuilderUsesExplicitQuarterAndYearModes() -> None:
    calls: list[str] = []

    class EdgarCompany:
        def _buildFinanceSeries(self, *, freq: str):
            calls.append(freq)
            return ({"IS": {"sales": [1.0]}}, [freq])

    assert _seriesPairsFromCompany(EdgarCompany()) == (
        ({"IS": {"sales": [1.0]}}, ["Q"]),
        ({"IS": {"sales": [1.0]}}, ["Y"]),
    )
    assert calls == ["Q", "Y"]


def testFinanceBuilderErrorsRemainVisible() -> None:
    class BrokenCompany:
        def _getFinanceBuild(self, mode: str):
            raise RuntimeError(f"broken {mode}")

    with pytest.raises(RuntimeError, match="broken q"):
        _seriesPairsFromCompany(BrokenCompany())


def testFinanceBuilderInvalidContractRemainsVisible() -> None:
    class InvalidCompany:
        def _getFinanceBuild(self, mode: str):
            return mode

    with pytest.raises(TypeError, match=r"_getFinanceBuild\('q'\) must return"):
        _seriesPairsFromCompany(InvalidCompany())
