"""F1 강행 - credit/ 폴더 구조 회귀 방지.

credit/ 평면 18 파일이 4 서브폴더 (scoring/models/monitoring/features) 로
정리됐다. 본 테스트는 평면 회귀 (서브폴더 우회 import) 를 차단한다.

테스트 게이트:
    1. credit/ 직속 .py = {__init__.py, engine.py} 만
    2. 4 서브폴더 모두 __init__.py 존재
    3. 16 모듈이 정확한 서브폴더에 위치
"""

from __future__ import annotations

from pathlib import Path

import pytest

CREDIT = Path(__file__).resolve().parent.parent.parent / "src" / "dartlab" / "credit"

ROOT_ALLOWED: set[str] = {
    "__init__.py",
    "dataProduct.py",
    "engine.py",
    "product.py",
    "_engineConfig.py",
    "_engineNotch.py",
    "_engineCHS.py",
    "_engineFinancial.py",
    "_enginePostAdjust.py",
    "_engineScoring.py",
}

EXPECTED_LAYOUT: dict[str, set[str]] = {
    "scoring": {
        "metrics.py",
        "gradeTable.py",
        "creditScorecard.py",
        "migration.py",
        "calcs.py",
        "_metricsArithmetic.py",
        "_metricsFetchers.py",
        "_metricsTrackB.py",
        "_calcsAdvanced.py",
    },
    "models": {"chsModel.py", "merton.py", "survival.py", "excessBondPremium.py"},
    "monitoring": {"crisisDetector.py", "creditCycle.py", "audit.py", "history.py"},
    "features": {
        "chsFeatures.py",
        "sectorThresholds.py",
        "_sectorThresholdsA.py",
        "_sectorThresholdsB.py",
        "narrative.py",
        "_narrativeTypes.py",
        "_narrativeBuilders.py",
        "_narrativeAxes.py",
        "_narrativeAxesA.py",
    },
}


@pytest.mark.unit
def test_credit_root_only_init_and_engine() -> None:
    """credit/ 직속 .py 는 __init__.py + engine.py 만 (평면 회귀 차단)."""
    actual = {p.name for p in CREDIT.glob("*.py")}
    extra = actual - ROOT_ALLOWED
    assert not extra, f"credit/ 직속 .py 평면 회귀: {extra}"


@pytest.mark.unit
@pytest.mark.parametrize("subfolder,expected", sorted(EXPECTED_LAYOUT.items()))
def test_credit_subfolder_layout(subfolder: str, expected: set[str]) -> None:
    """각 서브폴더가 정확한 모듈을 보유 + __init__.py 존재."""
    sub = CREDIT / subfolder
    assert sub.is_dir(), f"credit/{subfolder}/ 누락"
    assert (sub / "__init__.py").exists(), f"credit/{subfolder}/__init__.py 누락"
    actual = {p.name for p in sub.glob("*.py")} - {"__init__.py"}
    assert actual == expected, f"credit/{subfolder}/ 모듈 불일치: 기대 {expected}, 실제 {actual}"


@pytest.mark.unit
def test_credit_subfolder_imports() -> None:
    """4 서브폴더 모두 import 가능 (회귀 시 ImportError)."""
    from dartlab.credit import engine  # noqa: F401
    from dartlab.credit.features import chsFeatures, narrative, sectorThresholds  # noqa: F401
    from dartlab.credit.models import chsModel, excessBondPremium, merton, survival  # noqa: F401
    from dartlab.credit.monitoring import audit, creditCycle, crisisDetector, history  # noqa: F401
    from dartlab.credit.scoring import calcs, creditScorecard, gradeTable, metrics, migration  # noqa: F401
