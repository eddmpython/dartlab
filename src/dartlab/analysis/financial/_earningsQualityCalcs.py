"""earningsQuality 의 Beneish/Sloan/Flags/AuditFlags 핵심. 정적 함수 입력 (snake_id 키)."""

from __future__ import annotations

import math

from dartlab.analysis.financial._constants import ACCRUAL_RATIO_WARNING
from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.calc import safeDiv as _safe
from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId
from dartlab.core.utils.safe import get as _get

_getF = _getF2 = _getF3 = _getF4 = _get
_MAX_YEARS = 8

_BENEISH_MISSING_CANONICAL_INPUTS = [
    "gross_property_plant_equipment",
    "pure_depreciation_expense",
    "long_term_debt",
    "current_maturities_of_long_term_debt",
    "income_tax_payable",
    "cash_and_cash_equivalents",
]


def _beneishUnavailable() -> dict:
    """공통 공급자 계약으로 원식을 재현할 수 없다는 구조화 결과."""
    return {
        "status": "unavailable",
        "available": False,
        "mScore": None,
        "zone": "unavailable",
        "components": {},
        "interpretation": "Beneish 원식 입력의 공급자 공통 의미가 없어 판정하지 않습니다.",
        "reasonCode": "canonical_inputs_unavailable",
        "missingCanonicalInputs": list(_BENEISH_MISSING_CANONICAL_INPUTS),
        "requirements": {
            "basis": "two_audited_annual_periods_same_scope",
            "companyType": "nonfinancial",
            "asOfRequired": True,
            "canonicalFormulaOracleRequired": True,
        },
    }


# memoizedCalc 를 붙이면 안 된다. 그 래퍼는 첫 인자가 Company 인 계산기 전용이라
# `wrapper(company, *, basePeriod, overrides)` 로 서명이 바뀐다. 이 함수는 키워드 전용
# 순수 계산기라 붙는 순간 모든 호출이 TypeError 로 죽었다. 여덟 계정이 다 있는 정상
# 경로에서만 불리므로, 자료가 갖춰진 회사일수록 확실히 터졌다.
def calcBeneishMScore(
    *,
    salesT: float,
    salesT1: float,
    receivablesT: float,
    receivablesT1: float,
    cogsT: float,
    cogsT1: float,
    sgaT: float,
    sgaT1: float,
    grossPropertyT: float,
    grossPropertyT1: float,
    totalAssetsT: float,
    totalAssetsT1: float,
    netIncomeT: float,
    ocfT: float,
    leverageT: float,
    leverageT1: float,
    depreciationT: float,
    depreciationT1: float,
) -> dict:
    """Beneish M-Score 호환 슬롯의 명시적 비발행 결과.

    공식: M = -4.84 + 0.92×DSRI + 0.528×GMI + 0.404×AQI + 0.892×SGI
              + 0.115×DEPI - 0.172×SGAI + 4.679×TATA - 0.327×LVGI

    기존 키워드 서명은 호출 호환성을 위해 유지한다. 그러나 이 서명에는 원식 TATA와
    LVGI를 재현할 current maturities, income-tax payable, LTD가 없고 공급자 공통
    depreciation 의미도 보장되지 않는다. 따라서 proxy 점수나 zone을 발행하지 않는다.
    """
    return _beneishUnavailable()


def _beneishInterpretation(zone: str) -> str:
    _ = zone
    return "Beneish 원식 입력 계약이 없어 판정하지 않습니다."


def calcSloanAccruals(
    netIncome: float,
    ocf: float,
    totalAssets: float,
) -> dict:
    """Sloan Accruals (1996). 발생액 비율.

    공식: Accruals = (NI - OCF) / Total Assets
    상위 quintile (Q1, accrual 큼) → 1년 후 underperform 경향

    Returns
    -------
    dict
        accrualRatio : float
        quintile : "Q1" (highest accrual, 위험) ~ "Q5" (cleanest)
        warning : str | None

    Capabilities:
        - Sloan 1996 accrual ratio + 5-quintile 분류 + 경고 메시지
        - Q1 = highest accrual = 1 년 후 underperform 위험

    Guide:
        accrual > 10% = Q1 (high risk). < 0% = Q5 (cleanest).

    When:
        Earnings quality + AI 발생액 답변.

    How:
        (NI - OCF) / TA → quintile 분류.

    Requires:
        IS net + CF ocf + BS total assets.

    Raises:
        없음.

    Example:
        >>> calcSloanAccruals(net, ocf, ta)["quintile"]
        'Q2'

    See Also:
        - calcBeneishMScore : 8 변수
        - calcAccrualAnalysis : 시계열

    AIContext:
        "발생액 위험" 답변 시 accrualRatio + quintile 인용.
    """
    if totalAssets is None or totalAssets <= 0 or netIncome is None or ocf is None:
        return {"accrualRatio": None, "quintile": "skip", "warning": None}

    accrual_ratio = (netIncome - ocf) / totalAssets

    # Quintile 분류 (Sloan 1996 KOSPI 근사)
    if accrual_ratio > 0.10:
        quintile = "Q1"
        warning = "발생액 > 10%. Sloan 분류 최고위험 quintile (1년 후 실적 후행 가능성)"
    elif accrual_ratio > 0.05:
        quintile = "Q2"
        warning = "발생액 5~10%. 주의 (일회성 이익 의심)"
    elif accrual_ratio > 0.0:
        quintile = "Q3"
        warning = None
    elif accrual_ratio > -0.05:
        quintile = "Q4"
        warning = None
    else:
        quintile = "Q5"
        warning = None

    return {
        "accrualRatio": round(accrual_ratio, 4),
        "quintile": quintile,
        "warning": warning,
    }


def _calcEarningsQualityFlagsBase(
    *,
    salesT: float,
    salesT1: float,
    receivablesT: float,
    receivablesT1: float,
    netIncomeT: float,
    ocfT: float,
    totalAssetsT: float,
    nonOperatingIncomeT: float | None = None,
    operatingIncomeT: float | None = None,
    goodwillT: float | None = None,
    capitalCfT: float | None = None,
) -> dict:
    """5 카테고리 회계 품질 이상치 종합 (Damodaran Ch.4).

    Returns
    -------
    dict
        score : int. 0~100 (100 = clean)
        flags : list[{category, severity, evidence, damodaranRef}]
    """
    flags = []
    score = 100

    # 카테고리 1: 분식 의심. Sloan accrual 만 (Beneish 는 별도 호출)
    sloan = calcSloanAccruals(netIncomeT, ocfT, totalAssetsT)
    if sloan["quintile"] == "Q1":
        flags.append(
            {
                "category": "분식 의심",
                "severity": "high",
                "evidence": f"Sloan 발생액 {sloan['accrualRatio'] * 100:.1f}%. Q1 quintile",
                "damodaranRef": "Investment Valuation Ch.4 Earnings Quality",
            }
        )
        score -= 25
    elif sloan["quintile"] == "Q2":
        flags.append(
            {
                "category": "분식 의심",
                "severity": "medium",
                "evidence": f"Sloan 발생액 {sloan['accrualRatio'] * 100:.1f}%. Q2",
                "damodaranRef": "Sloan 1996",
            }
        )
        score -= 10

    # 카테고리 2: 일회성 거래 (영업외/영업이익 > 0.3)
    if nonOperatingIncomeT is not None and operatingIncomeT and operatingIncomeT > 0:
        ratio = abs(nonOperatingIncomeT) / abs(operatingIncomeT)
        if ratio > 0.3:
            flags.append(
                {
                    "category": "일회성 거래",
                    "severity": "medium",
                    "evidence": f"영업외/영업이익 {ratio * 100:.0f}%. 일회성 비중 큼",
                    "damodaranRef": "Damodaran Normalized Earnings Ch.22",
                }
            )
            score -= 15

    # 카테고리 3: 매출채권 급증 (DSO 전기 +20%)
    if salesT > 0 and salesT1 > 0:
        dso_t = receivablesT / salesT * 365
        dso_t1 = receivablesT1 / salesT1 * 365
        if dso_t1 > 0:
            dso_change_pct = (dso_t - dso_t1) / dso_t1 * 100
            if dso_change_pct > 20:
                flags.append(
                    {
                        "category": "매출채권 급증",
                        "severity": "high",
                        "evidence": f"DSO {dso_t1:.0f}일 → {dso_t:.0f}일 (+{dso_change_pct:.0f}%). 매출 인식 공격적 의심",
                        "damodaranRef": "Aggressive Revenue Recognition (Ch.4)",
                    }
                )
                score -= 20

    # 카테고리 4: 자본 우회 (자본거래 > 영업CF)
    if capitalCfT is not None and ocfT and abs(ocfT) > 0:
        if abs(capitalCfT) > abs(ocfT):
            flags.append(
                {
                    "category": "자본 우회",
                    "severity": "medium",
                    "evidence": f"자본거래 {capitalCfT / 1e9:.0f}B vs 영업CF {ocfT / 1e9:.0f}B. 외부 자본 의존",
                    "damodaranRef": "Off-balance financing (Ch.4)",
                }
            )
            score -= 10

    # 카테고리 5: 영업권/총자산 > 30%
    if goodwillT is not None and totalAssetsT > 0:
        gw_ratio = goodwillT / totalAssetsT * 100
        if gw_ratio > 30:
            flags.append(
                {
                    "category": "영업권 과대",
                    "severity": "high",
                    "evidence": f"영업권/총자산 {gw_ratio:.0f}%. 손상 가능성",
                    "damodaranRef": "Goodwill Impairment Risk (Ch.4)",
                }
            )
            score -= 20
        elif gw_ratio > 15:
            flags.append(
                {
                    "category": "영업권 과대",
                    "severity": "low",
                    "evidence": f"영업권/총자산 {gw_ratio:.0f}%",
                    "damodaranRef": "Goodwill watch zone",
                }
            )
            score -= 5

    score = max(0, min(100, score))

    return {
        "score": score,
        "flags": flags,
        "sloanAccrual": sloan,
    }


def detectAuditFlags(auditOpinionText: str) -> list[dict]:
    """감사보고서 텍스트에서 위험 키워드 자동 감지.

    Damodaran Ch.4 + KICPA 표준 키워드.

    Capabilities:
        - 의견거절/부적정/한정/계속기업/내부통제/재작성/특수관계자/KAM 8 키워드 매칭
        - severity (critical/high/low) 분류

    Args:
        auditOpinionText: 감사보고서 본문 텍스트.

    Returns:
        list[dict]. keyword/severity/description.

    Guide:
        critical 키워드 1개 이상 = 즉시 매도 검토. high ≥ 2 = 위험 다중 신호.

    When:
        감사보고서 안전성 + AI 회계 신뢰 답변.

    How:
        키워드 list 순회 → text 매칭 → dict 누적.

    Requires:
        auditOpinionText 문자열.

    Raises:
        없음. 빈 입력 시 빈 list.

    Example:
        >>> detectAuditFlags("...계속기업 가정에 관한 의문...")[0]["severity"]
        'high'

    See Also:
        - calcEarningsQualityFlags : 종합
        - _earningsQualityDeep.calcBeneishTimeline

    AIContext:
        "감사보고서 위험" 답변 시 keyword + severity 인용.
    """
    if not auditOpinionText:
        return []

    text = str(auditOpinionText)
    flags = []

    keyword_severity = [
        ("의견거절", "critical", "감사 의견거절. 재무제표 신뢰 붕괴"),
        ("부적정의견", "critical", "부적정의견. 회계 기준 위반"),
        ("한정의견", "high", "한정의견. 일부 항목 검증 불가"),
        ("계속기업 불확실성", "high", "계속기업 가정 의심"),
        ("계속기업 가정에 관한", "high", "계속기업 가정 의심"),
        ("내부통제 미흡", "high", "내부회계관리 미흡"),
        ("내부회계관리제도 비적정", "high", "내부회계관리 비적정"),
        ("재무제표 재작성", "high", "과거 재무제표 재작성"),
        ("특수관계자 거래", "low", "특수관계자 거래 비중 (양적 검토 필요)"),
        ("핵심감사사항", "low", "KAM 명시"),
    ]

    for kw, sev, desc in keyword_severity:
        if kw in text:
            flags.append(
                {
                    "keyword": kw,
                    "severity": sev,
                    "description": desc,
                }
            )

    return flags
