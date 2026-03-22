"""insight pipeline 통합 테스트 — mock 재무 시계열로 analyze() 검증.

unit 마커: 실제 데이터 불필요.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def _make_series() -> tuple[dict, list[str], dict, list[str]]:
    """analyze()에 넘길 mock 시계열 데이터.

    Returns:
        (qSeries, qPeriods, aSeries, aYears)
    """
    # 연간 시계열 (3년) — list 형식 (extract.py가 기대하는 형태)
    aYears = ["2022", "2023", "2024"]
    aSeries: dict = {
        "IS": {
            "sales": [100e9, 110e9, 120e9],
            "operating_profit": [10e9, 12e9, 15e9],
            "net_income": [8e9, 10e9, 12e9],
            "cost_of_sales": [60e9, 65e9, 70e9],
            "sga": [20e9, 22e9, 23e9],
            "ebitda": [15e9, 18e9, 22e9],
            "interest_expense": [1e9, 1e9, 1e9],
        },
        "BS": {
            "total_assets": [200e9, 220e9, 250e9],
            "total_equity": [120e9, 135e9, 150e9],
            "total_liabilities": [80e9, 85e9, 100e9],
            "current_assets": [80e9, 90e9, 100e9],
            "current_liabilities": [40e9, 45e9, 50e9],
            "non_current_liabilities": [40e9, 40e9, 50e9],
            "inventory": [20e9, 22e9, 25e9],
            "receivables": [15e9, 18e9, 20e9],
            "payables": [10e9, 12e9, 14e9],
            "cash": [30e9, 35e9, 40e9],
            "short_term_debt": [10e9, 10e9, 12e9],
            "long_term_debt": [20e9, 20e9, 25e9],
        },
        "CF": {
            "operating_cashflow": [12e9, 15e9, 18e9],
            "investing_cashflow": [-5e9, -7e9, -8e9],
            "financing_cashflow": [-3e9, -4e9, -5e9],
            "capex": [5e9, 7e9, 8e9],
            "dividends_paid": [2e9, 3e9, 3e9],
        },
    }

    # 분기 시계열 (8분기)
    qPeriods = ["2023Q1", "2023Q2", "2023Q3", "2023Q4", "2024Q1", "2024Q2", "2024Q3", "2024Q4"]
    qSeries: dict = {
        "IS": {
            "sales": [30e9] * 8,
            "operating_profit": [3e9] * 8,
            "net_income": [2.5e9] * 8,
        },
        "BS": {
            "total_assets": [250e9] * 8,
            "total_equity": [150e9] * 8,
        },
        "CF": {
            "operating_cashflow": [4e9] * 8,
        },
    }

    return qSeries, qPeriods, aSeries, aYears


# ── analyze() 호출 ──


def test_analyze_returns_result():
    """mock 데이터로 analyze() 호출 시 AnalysisResult 반환."""
    from dartlab.engines.analysis.insight import AnalysisResult, analyze

    qSeries, qPeriods, aSeries, aYears = _make_series()
    result = analyze(
        "999999",
        corpName="테스트기업",
        qSeriesPair=(qSeries, qPeriods),
        aSeriesPair=(aSeries, aYears),
    )
    assert result is not None
    assert isinstance(result, AnalysisResult)
    assert result.corpName == "테스트기업"
    assert result.stockCode == "999999"


def test_analyze_has_7_grades():
    """7영역 등급이 모두 존재."""
    from dartlab.engines.analysis.insight import analyze

    qSeries, qPeriods, aSeries, aYears = _make_series()
    result = analyze(
        "999999",
        corpName="테스트기업",
        qSeriesPair=(qSeries, qPeriods),
        aSeriesPair=(aSeries, aYears),
    )
    assert result is not None
    grades = result.grades()
    assert len(grades) == 7
    expected_keys = {"performance", "profitability", "health", "cashflow", "governance", "risk", "opportunity"}
    assert set(grades.keys()) == expected_keys
    for grade in grades.values():
        assert grade in ("A", "B", "C", "D", "F", "N")  # N = 데이터 부족


def test_analyze_has_profile():
    """profile 문자열 존재."""
    from dartlab.engines.analysis.insight import analyze

    qSeries, qPeriods, aSeries, aYears = _make_series()
    result = analyze(
        "999999",
        corpName="테스트기업",
        qSeriesPair=(qSeries, qPeriods),
        aSeriesPair=(aSeries, aYears),
    )
    assert result is not None
    assert isinstance(result.profile, str)
    assert len(result.profile) > 0


def test_analyze_has_summary():
    """summary 텍스트 존재."""
    from dartlab.engines.analysis.insight import analyze

    qSeries, qPeriods, aSeries, aYears = _make_series()
    result = analyze(
        "999999",
        corpName="테스트기업",
        qSeriesPair=(qSeries, qPeriods),
        aSeriesPair=(aSeries, aYears),
    )
    assert result is not None
    assert isinstance(result.summary, str)
    assert "테스트기업" in result.summary


def test_analyze_anomalies_list():
    """anomalies가 리스트 타입."""
    from dartlab.engines.analysis.insight import Anomaly, analyze

    qSeries, qPeriods, aSeries, aYears = _make_series()
    result = analyze(
        "999999",
        corpName="테스트기업",
        qSeriesPair=(qSeries, qPeriods),
        aSeriesPair=(aSeries, aYears),
    )
    assert result is not None
    assert isinstance(result.anomalies, list)
    for a in result.anomalies:
        assert isinstance(a, Anomaly)


def test_analyze_repr():
    """AnalysisResult repr 정상 동작."""
    from dartlab.engines.analysis.insight import analyze

    qSeries, qPeriods, aSeries, aYears = _make_series()
    result = analyze(
        "999999",
        corpName="테스트기업",
        qSeriesPair=(qSeries, qPeriods),
        aSeriesPair=(aSeries, aYears),
    )
    assert result is not None
    r = repr(result)
    assert "테스트기업" in r


# ── 개별 grading 함수 ──


def test_grading_score_to_grade():
    """_scoreToGrade 경계값 테스트."""
    from dartlab.engines.analysis.insight.grading import _scoreToGrade

    assert _scoreToGrade(8, 10) == "A"
    assert _scoreToGrade(5, 10) == "B"
    assert _scoreToGrade(2, 10) == "C"
    assert _scoreToGrade(0, 10) == "D"
    assert _scoreToGrade(0, 0) == "D"  # maxScore=0 edge case


# ── anomaly detection ──


def test_anomaly_detection_clean_data():
    """정상 데이터에서 이상치 탐지 실행."""
    from dartlab.engines.analysis.insight.anomaly import runAnomalyDetection

    _, _, aSeries, _ = _make_series()
    anomalies = runAnomalyDetection(aSeries, isFinancial=False)
    assert isinstance(anomalies, list)


# ── types ──


def test_insight_result_dataclass():
    from dartlab.engines.analysis.insight.types import InsightResult

    ir = InsightResult(grade="A", summary="좋음", details=["상세1"], risks=[], opportunities=[])
    assert ir.grade == "A"
    assert ir.summary == "좋음"


def test_flag_dataclass():
    from dartlab.engines.analysis.insight.types import Flag

    f = Flag(level="warning", category="debt", text="부채비율 높음")
    assert f.level == "warning"


def test_anomaly_dataclass():
    from dartlab.engines.analysis.insight.types import Anomaly

    a = Anomaly(severity="danger", category="earningsQuality", text="이익 품질 의심", value=50.0)
    assert a.value == 50.0
