"""Beneish M-Score 횡단면 호환 축.

현재 공통 KR/US scan schema는 Beneish(1999) 8변수 원식에 필요한 계정 의미를
보장하지 않는다. 다른 비율이나 결측 중립값으로 이름만 같은 점수를 만들지 않고,
재활성화 조건을 구조화해 반환한다.
"""

from __future__ import annotations

from dartlab.core.market import detectMarket

_MISSING_CANONICAL_INPUTS = [
    "gross_property_plant_equipment",
    "pure_depreciation_expense",
    "long_term_debt",
    "current_maturities_of_long_term_debt",
    "income_tax_payable",
    "cash_and_cash_equivalents",
]


def calcBeneishFactor(
    *,
    market: str = "auto",
    stockCode: str | None = None,
    **kwargs,
) -> dict:
    """Beneish 횡단면 축의 명시적 비발행 결과를 반환한다.

    축 이름과 호출 경로는 호환성을 위해 유지한다. ``scores``나 clean/red-flag
    판정은 원식 입력, 연간 공시 시점, 비금융 적용성이 공급자 공통 계약으로 확인될
    때까지 발행하지 않는다.
    """
    requested_market = market.strip().upper() if isinstance(market, str) else ""
    if requested_market == "AUTO":
        resolved_market = detectMarket(stockCode) if stockCode else "KR"
    elif requested_market in {"KR", "US"}:
        resolved_market = requested_market
    else:
        raise ValueError("market은 'auto', 'KR', 'US' 중 하나여야 합니다")

    result = {
        "status": "unavailable",
        "available": False,
        "market": resolved_market,
        "model": "Beneish M-Score (1999, 8-variable)",
        "reasonCode": "canonical_inputs_unavailable",
        "reason": (
            "공통 공급자 스키마가 Beneish 원식의 계정 의미를 보장하지 않아 "
            "점수와 clean/red-flag 판정을 발행하지 않습니다."
        ),
        "score": None,
        "flag": None,
        "scores": None,
        "flags": None,
        "topFlag": None,
        "topClean": None,
        "missingCanonicalInputs": list(_MISSING_CANONICAL_INPUTS),
        "requirements": {
            "basis": "two_audited_annual_periods_same_scope",
            "companyType": "nonfinancial",
            "asOfRequired": True,
            "canonicalFormulaOracleRequired": True,
        },
        "provenance": {
            "currentProviderContractCanonical": False,
            "pointInTime": False,
            "thresholdPublished": False,
        },
    }
    if stockCode is not None:
        result["stockCode"] = stockCode
    return result
