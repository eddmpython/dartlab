"""F2 강행 - macro/ 폴더 구조 회귀 방지.

F2.1 (이번 라운드): assets/historicalContext → corporate/, liquidity/sentiment → cycles/, _helpers → seriesFetch.
root 잔존: __init__, seriesFetch, summary, spec.
"""

from __future__ import annotations

from pathlib import Path

import pytest

MACRO = Path(__file__).resolve().parent.parent.parent / "src" / "dartlab" / "macro"

ROOT_ALLOWED: set[str] = {
    "__init__.py",
    "dataProduct.py",
    "seriesFetch.py",  # F2.1: _helpers.py → seriesFetch.py (헬퍼 generic 이름 폐지)
    "summary.py",
    "spec.py",
}

EXPECTED_LAYOUT: dict[str, set[str]] = {
    "rates": {"rates.py", "yieldCurve.py", "bondRiskPremia.py", "impliedERP.py", "riskPremiums.py"},
    "cycles": {
        "cycle.py",
        "macroCycle.py",
        "regimeSwitching.py",
        "inflection.py",
        "turningPoint.py",
        "inventoryCycle.py",
        "inventory.py",
        "liquidity.py",  # F2.1: root → cycles
        "sentiment.py",  # F2.1: root → cycles
    },
    "crisis": {
        "crisis.py",
        "fci.py",
        "growthAtRisk.py",
        "rrCrisisDB.py",
        "creditCycleDetect.py",
        "detectors.py",
        "excessBondPremium.py",
    },
    "forecast": {"forecast.py", "nowcast.py", "macroBacktest.py"},
    "corporate": {
        "corporate.py",
        "corporateAggregate.py",
        "assets.py",  # F2.1: root → corporate
        "historicalContext.py",  # F2.1: root → corporate
    },
    "trade": {"trade.py", "termsOfTrade.py"},
    "transmission": {"transmission.py"},
}


@pytest.mark.unit
def test_macro_root_allowed_only() -> None:
    """macro/ 직속 .py 는 ROOT_ALLOWED 8 개만 (평면 회귀 차단)."""
    actual = {p.name for p in MACRO.glob("*.py")}
    extra = actual - ROOT_ALLOWED
    assert not extra, f"macro/ 직속 .py 평면 회귀: {extra}"


@pytest.mark.unit
@pytest.mark.parametrize("subfolder,expected", sorted(EXPECTED_LAYOUT.items()))
def test_macro_subfolder_layout(subfolder: str, expected: set[str]) -> None:
    """각 서브폴더가 정확한 모듈을 보유 + __init__.py 존재."""
    sub = MACRO / subfolder
    assert sub.is_dir(), f"macro/{subfolder}/ 누락"
    assert (sub / "__init__.py").exists(), f"macro/{subfolder}/__init__.py 누락"
    # private split file (`_*.py`) 은 layout 검사 제외 - public API 표면만 강제.
    actual = {p.name for p in sub.glob("*.py") if not p.name.startswith("_")} - {"__init__.py"}
    assert actual == expected, f"macro/{subfolder}/ 모듈 불일치: 기대 {expected}, 실제 {actual}"


@pytest.mark.unit
def test_macro_scenarios_has_three_new() -> None:
    """scenarios/ 에 신규 3 모듈 (scenario, dalio48Match, dalioCaseMatch) 흡수 검증."""
    scenarios = MACRO / "scenarios"
    files = {p.name for p in scenarios.glob("*.py")} - {"__init__.py"}
    required = {"scenario.py", "dalio48Match.py", "dalioCaseMatch.py"}
    assert required.issubset(files), f"scenarios/ 누락: {required - files}"


@pytest.mark.unit
def test_macro_subfolder_imports() -> None:
    """7 서브폴더 모두 import 가능 (회귀 시 ImportError)."""
    from dartlab.macro.corporate import (  # noqa: F401
        assets,  # F2.1: root → corporate
        corporate,
        corporateAggregate,
        historicalContext,  # F2.1: root → corporate
    )
    from dartlab.macro.crisis import crisis, fci, growthAtRisk, rrCrisisDB  # noqa: F401
    from dartlab.macro.cycles import (  # noqa: F401
        cycle,
        inflection,
        inventory,
        inventoryCycle,
        liquidity,  # F2.1: root → cycles
        macroCycle,
        regimeSwitching,
        sentiment,  # F2.1: root → cycles
        turningPoint,
    )
    from dartlab.macro.forecast import forecast, macroBacktest, nowcast  # noqa: F401
    from dartlab.macro.rates import bondRiskPremia, impliedERP, rates, riskPremiums, yieldCurve  # noqa: F401
    from dartlab.macro.scenarios import dalio48Match, dalioCaseMatch, scenario  # noqa: F401
    from dartlab.macro.trade import termsOfTrade, trade  # noqa: F401
    from dartlab.macro.transmission import transmission  # noqa: F401
