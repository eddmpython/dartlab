"""credit 통합 테스트 - MockCompany로 전체 파이프라인 검증.

evaluateCompany → metrics → scorecard → 등급 결정 전체 경로를 합성 데이터로 실행.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ── evaluateCompany 전체 파이프라인 ──


def test_evaluateCompany_returns_dict_or_none(mock_company):
    """전체 파이프라인 - dict 또는 None, crash 없음."""
    from dartlab.credit.engine import evaluateCompany

    mock_company._cache.clear()
    result = evaluateCompany(mock_company)
    assert result is None or isinstance(result, dict)


def test_evaluateCompany_grade_fields(mock_company):
    """결과가 있으면 핵심 필드 존재 확인."""
    from dartlab.credit.engine import evaluateCompany

    mock_company._cache.clear()
    result = evaluateCompany(mock_company)
    if result is not None:
        assert "grade" in result, "Missing 'grade' field"
        assert "healthScore" in result, "Missing 'healthScore' field"
        assert "pdEstimate" in result, "Missing 'pdEstimate' field"
        assert "outlook" in result, "Missing 'outlook' field"
        assert "sector" in result, "Missing 'sector' field"


def test_evaluateCompany_detail_mode(mock_company):
    """detail=True - narratives, metricsHistory 포함."""
    from dartlab.credit.engine import evaluateCompany

    mock_company._cache.clear()
    result = evaluateCompany(mock_company, detail=True)
    if result is not None:
        assert "grade" in result
        # detail mode 추가 필드
        if "narratives" in result:
            assert isinstance(result["narratives"], dict)
        if "metricsHistory" in result:
            assert isinstance(result["metricsHistory"], list)


# ── calcAllMetrics ──


def test_calcAllMetrics(mock_company):
    """지표 산출 단계 - dict 또는 None."""
    from dartlab.credit.scoring.metrics import calcAllMetrics

    mock_company._cache.clear()
    result = calcAllMetrics(mock_company)
    assert result is None or isinstance(result, dict)


def test_calcAllMetrics_history_structure(mock_company):
    """history가 있으면 list of dict."""
    from dartlab.credit.scoring.metrics import calcAllMetrics

    mock_company._cache.clear()
    result = calcAllMetrics(mock_company)
    if result is not None and "history" in result:
        assert isinstance(result["history"], list)
        if result["history"]:
            first = result["history"][0]
            assert isinstance(first, dict)
            # 기본 지표 키 확인
            expected_keys = {"period"}
            assert expected_keys.issubset(set(first.keys())), (
                f"Missing keys in history[0]: {expected_keys - set(first.keys())}"
            )


# ── 빈 데이터 안전성 ──


def test_evaluateCompany_empty(empty_mock_company):
    """빈 회사 데이터로도 crash 없음."""
    from dartlab.credit.engine import evaluateCompany

    empty_mock_company._cache.clear()
    result = evaluateCompany(empty_mock_company)
    # 빈 데이터면 None이 정상
    assert result is None or isinstance(result, dict)


def test_calcAllMetrics_empty(empty_mock_company):
    """빈 데이터 - None 반환."""
    from dartlab.credit.scoring.metrics import calcAllMetrics

    empty_mock_company._cache.clear()
    result = calcAllMetrics(empty_mock_company)
    assert result is None or isinstance(result, dict)


# ── basePeriod 전달 ──


def test_evaluateCompany_with_basePeriod(mock_company):
    """basePeriod 전달 - crash 없음."""
    from dartlab.credit.engine import evaluateCompany

    mock_company._cache.clear()
    result = evaluateCompany(mock_company, basePeriod="2023")
    assert result is None or isinstance(result, dict)


def test_evaluateCompany_applies_credit_overrides_to_scoring_input(mock_company):
    """override는 표시만 하지 않고 실제 dCR 점수 입력과 축 결과를 바꿔야 한다."""
    from dartlab.credit.engine import evaluateCompany

    mock_company._cache.clear()
    baseline = evaluateCompany(mock_company)
    stressed = evaluateCompany(
        mock_company,
        overrides={"debtRatio": 500.0, "interestCoverage": 0.5, "currentRatio": 40.0},
    )

    assert baseline is not None and stressed is not None
    assert stressed["scenarioMetrics"]["debtRatio"] == 500.0
    assert stressed["scenarioMetrics"]["ebitdaInterestCoverage"] == 0.5
    assert stressed["appliedOverrides"] == {
        "debtRatio": 500.0,
        "interestCoverage": 0.5,
        "currentRatio": 40.0,
    }
    assert stressed["currentScore"] != baseline["currentScore"]


def test_evaluateCompany_does_not_claim_unsupported_quick_ratio(mock_company):
    from dartlab.credit.engine import evaluateCompany

    mock_company._cache.clear()
    result = evaluateCompany(mock_company, overrides={"quickRatio": 80.0})

    assert result is not None
    assert result["appliedOverrides"] == {}
    assert "calibration" in result["ignoredOverrides"]["quickRatio"]


def test_missing_axis_contribution_remains_none(mock_company):
    """축 결손을 위험기여 0으로 위장하지 않는다."""
    from dartlab.credit.engine import evaluateCompany

    mock_company._cache.clear()
    result = evaluateCompany(mock_company)

    assert result is not None
    for axis in result["axes"]:
        if axis["score"] is None:
            assert axis["contribution"] is None


# ── 등급 유효성 ──


def test_grade_is_valid_format(mock_company):
    """등급 문자열이 유효한 형식인지 확인."""
    from dartlab.credit.engine import evaluateCompany

    mock_company._cache.clear()
    result = evaluateCompany(mock_company)
    if result is not None and "grade" in result:
        grade = result["grade"]
        assert isinstance(grade, str)
        assert len(grade) <= 5, f"Grade too long: {grade}"


def test_healthScore_range(mock_company):
    """healthScore가 0~100 범위인지 확인."""
    from dartlab.credit.engine import evaluateCompany

    mock_company._cache.clear()
    result = evaluateCompany(mock_company)
    if result is not None and "healthScore" in result:
        score = result["healthScore"]
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100, f"healthScore out of range: {score}"
