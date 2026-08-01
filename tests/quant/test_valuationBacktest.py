"""dFV 재무 기준 기간 라이브 canary.

과거 구현은 최신 1년 가격과 최신 WACC를 사용하면서 2024Q4 point-in-time
예측 적중률이라고 주장했다. 시장 입력 vintage와 공시 가용일이 고정되지 않은
상태에서는 재현 가능한 백테스트가 아니므로, 이 파일은 공개 결과의 재무 기간
제한과 provenance만 검증한다. 진정한 as-of 성과 게이트는 시장 snapshot 계약이
생긴 뒤 별도 동결 fixture로 복구한다.
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.requires_data]


def test_financial_base_period_live_provenance_has_no_future_annual_rows():
    """기준 연도 이후의 연간 FCF와 BS가 twoStage 입력에 포함되지 않는다."""
    import dartlab
    from dartlab.analysis.valuation.dFV import calcDFV

    result = calcDFV(dartlab.Company("003230"), basePeriod="2024")

    assert result is not None
    two_stage = result.get("twoStage") or {}
    assumptions = two_stage.get("assumptions") or {}
    assert assumptions["periodContract"] == "financialPeriod"
    assert assumptions["financialBasePeriod"] == "2024"
    assert assumptions["fcfPeriods"]
    assert all(int(period[:4]) <= 2024 for period in assumptions["fcfPeriods"])
    assert int(assumptions["balancePeriod"][:4]) <= 2024
    assert assumptions["sharesPeriod"] <= "2024-12-31"
    assert assumptions["erpAsOf"]
    assert assumptions["erpSource"]
    assert any("시장 입력 빈티지" in warning for warning in two_stage["warnings"])
