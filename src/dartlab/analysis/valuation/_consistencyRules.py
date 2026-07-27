"""Damodaran 정합성 7 규칙 (calcCashFlowConsistency 의 규칙별 seam).

규칙마다 "입력이 수치인지 확인 → 임계 비교 → flags 에 dict 한 장 추가 → checks 갱신"
이라는 같은 모양이 반복된다. 규칙 하나당 함수 하나로 떼어낸다. flags/checks 는 인자로
받아 제자리 변경하므로 원본의 삽입 순서가 그대로 보존된다.
"""

from __future__ import annotations

from typing import Any

from dartlab.core.utils.calc import reinvestmentIdentity

_SEV_INFO = "info"
_SEV_WARN = "warn"
_SEV_CRITICAL = "critical"

_SEV_ORDER = {_SEV_INFO: 0, _SEV_WARN: 1, _SEV_CRITICAL: 2}


def _resolveFromCompany(
    company: Any,
    basePeriod: str | None,
    currency: str | None,
    valuation: dict[str, Any] | None,
    roicPct: float | None,
    waccPct: float | None,
    effectiveTaxRatePct: float | None,
    growthRatePct: float | None,
) -> tuple:
    """company 로부터 누락 입력 자동 추출. 실패한 소스는 그대로 None 으로 남긴다.

    Parameters
    ----------
    company : Any
        Company 객체.
    basePeriod : str | None
        기준 기간.
    currency, valuation, roicPct, waccPct, effectiveTaxRatePct, growthRatePct
        호출자가 명시한 값. None 인 것만 채운다.

    Returns
    -------
    tuple
        (currency, valuation, roicPct, waccPct, effectiveTaxRatePct, growthRatePct).
    """
    if currency is None:
        currency = getattr(company, "currency", None)
    if valuation is None:
        try:
            from dartlab.analysis.valuation.dFV import calcDFV

            valuation = calcDFV(company, basePeriod=basePeriod)
        except (ImportError, AttributeError, ValueError, TypeError):
            pass
    if roicPct is None or waccPct is None:
        try:
            from dartlab.analysis.financial.investmentAnalysis import calcRoicTimeline

            r = calcRoicTimeline(company, basePeriod=basePeriod)
            if r and r.get("history"):
                latest = r["history"][0]
                if roicPct is None:
                    roicPct = latest.get("roic")
                if waccPct is None:
                    waccPct = latest.get("waccEstimate")
                if effectiveTaxRatePct is None:
                    effectiveTaxRatePct = latest.get("effectiveTaxRate")
        except (ImportError, AttributeError, ValueError, TypeError):
            pass
    if growthRatePct is None:
        try:
            from dartlab.analysis.financial.growthAnalysis import calcGrowthTrend

            g = calcGrowthTrend(company, basePeriod=basePeriod)
            if g:
                growthRatePct = (g.get("cagr") or {}).get("revenue")
        except (ImportError, AttributeError, ValueError, TypeError):
            pass
    return currency, valuation, roicPct, waccPct, effectiveTaxRatePct, growthRatePct


def _mergeValuation(
    valuation: dict[str, Any],
    roicPct: float | None,
    growthRatePct: float | None,
    terminalGrowthPct: float | None,
    terminalValueShare: float | None,
    primaryModel: str | None,
    modelsUsed: int | None,
    waccPct: float | None,
) -> tuple:
    """valuation dict 에서 누락 입력을 채운다. 명시 인자가 항상 우선.

    Parameters
    ----------
    valuation : dict
        dFV 결과 dict (truthy 보장).
    roicPct, growthRatePct, terminalGrowthPct, terminalValueShare, primaryModel, modelsUsed, waccPct
        호출자가 명시한 값. None 인 것만 채운다.

    Returns
    -------
    tuple
        (roicPct, growthRatePct, terminalGrowthPct, terminalValueShare, primaryModel, modelsUsed, waccPct).
    """
    roicPct = roicPct if roicPct is not None else valuation.get("roicPct")
    growthRatePct = growthRatePct if growthRatePct is not None else valuation.get("growthRatePct")
    terminalGrowthPct = terminalGrowthPct if terminalGrowthPct is not None else valuation.get("terminalGrowth")
    terminalValueShare = terminalValueShare if terminalValueShare is not None else valuation.get("tvShare")
    primaryModel = (
        primaryModel if primaryModel is not None else valuation.get("primary") or valuation.get("primaryModel")
    )
    modelsUsed = modelsUsed if modelsUsed is not None else len(valuation.get("allMethods") or [])
    waccPct = waccPct if waccPct is not None else valuation.get("wacc") or (valuation.get("details") or {}).get("wacc")
    return roicPct, growthRatePct, terminalGrowthPct, terminalValueShare, primaryModel, modelsUsed, waccPct


def _ruleTerminalGrowthBounded(
    terminalGrowthPct: Any,
    rfPct: float,
    flags: list[dict],
    checks: dict[str, Any],
) -> None:
    """규칙 1: 영구성장률 <= 무위험수익률 (Damodaran 강제).

    Parameters
    ----------
    terminalGrowthPct : Any
        영구성장률 (%). 수치가 아니면 검사 skip.
    rfPct : float
        무위험수익률 (%).
    flags, checks : list, dict
        누적 구조. 제자리 변경.
    """
    checks["terminalGrowthBounded"] = True
    if not isinstance(terminalGrowthPct, (int, float)):
        return
    if terminalGrowthPct > rfPct + 0.5:
        checks["terminalGrowthBounded"] = False
        flags.append(
            {
                "rule": "g_vs_rf",
                "severity": _SEV_WARN,
                "message": (
                    f"영구성장률 {terminalGrowthPct:.1f}% 가 무위험수익률 {rfPct:.1f}% 초과. "
                    "장기 GDP 초과는 불가능 가정"
                ),
                "observed": terminalGrowthPct,
                "expected": rfPct,
            }
        )


def _ruleGrowthEquation(
    growthRatePct: float | None,
    roicPct: float | None,
    reinvestmentRatePct: float | None,
    flags: list[dict],
    checks: dict[str, Any],
) -> None:
    """규칙 2: 성장 항등식 g = 재투자율 x ROIC.

    Parameters
    ----------
    growthRatePct, roicPct, reinvestmentRatePct : float | None
        성장률(%), ROIC(%), 재투자율(%).
    flags, checks : list, dict
        누적 구조. 제자리 변경.
    """
    checks["growthReinvestmentMatch"] = None
    if not (growthRatePct is not None and roicPct is not None and roicPct > 0):
        return
    identity = reinvestmentIdentity(growthRatePct, roicPct)
    implied = identity["impliedReinvestRate"] if identity else None
    if reinvestmentRatePct is not None and implied is not None:
        observed = reinvestmentRatePct / 100.0
        gap = abs(observed - implied)
        checks["growthReinvestmentMatch"] = gap < 0.10
        if gap >= 0.10:
            flags.append(
                {
                    "rule": "reinvest_identity",
                    "severity": _SEV_CRITICAL,
                    "message": (
                        f"g={growthRatePct:.1f}% 와 ROIC={roicPct:.1f}% 에서 필요 재투자율은 "
                        f"{implied * 100:.0f}% 이나 {reinvestmentRatePct:.0f}% 가정. 수학 위반"
                    ),
                    "observed": reinvestmentRatePct,
                    "expected": round(implied * 100, 1),
                }
            )
    elif implied is not None:
        checks["impliedReinvestRate"] = round(implied, 4)


def _ruleDiscountRateMatch(primaryModel: Any, waccPct: float | None, checks: dict[str, Any]) -> None:
    """규칙 3: 할인율 매칭 (FCFF 는 WACC, FCFE/DDM/RIM 은 Ke).

    실제 비교는 dFV.py 가 담당하므로 여기서는 checks 초기화만 한다.

    Parameters
    ----------
    primaryModel : Any
        주 모델명.
    waccPct : float | None
        WACC (%).
    checks : dict
        누적 구조. 제자리 변경.
    """
    checks["discountRateMatch"] = True
    if primaryModel:
        pm = str(primaryModel).lower()
        if pm in ("fcfe", "ddm", "rim") and waccPct is not None:
            # 이 모델들은 Ke 로 할인해야 하므로 WACC 가 아니라 Ke 가 제공되어야 함.
            # valuation dict 에 ke 가 별도 표기된 경우만 경고 (정보성).
            pass  # 실제 비교는 dFV.py 에서 담당. 여기서는 명시적 경고만 스킵


def _ruleTerminalValueShare(terminalValueShare: Any, flags: list[dict], checks: dict[str, Any]) -> None:
    """규칙 4: Terminal Value 비중 과다.

    Parameters
    ----------
    terminalValueShare : Any
        TV / EV (0.0~1.0).
    flags, checks : list, dict
        누적 구조. 제자리 변경.
    """
    checks["terminalValueShare"] = terminalValueShare
    if isinstance(terminalValueShare, (int, float)) and terminalValueShare > 0.75:
        flags.append(
            {
                "rule": "tv_weight",
                "severity": _SEV_WARN,
                "message": f"Terminal Value 비중 {terminalValueShare * 100:.0f}%. explicit forecast 구간 신뢰도 낮음",
                "observed": round(terminalValueShare, 3),
                "expected": 0.75,
            }
        )


def _ruleSingleModel(modelsUsed: Any, flags: list[dict]) -> None:
    """규칙 5: 단일 방법론 의존.

    Parameters
    ----------
    modelsUsed : Any
        사용 모델 수.
    flags : list
        누적 구조. 제자리 변경.
    """
    if isinstance(modelsUsed, int) and modelsUsed <= 1:
        flags.append(
            {
                "rule": "single_model",
                "severity": _SEV_INFO,
                "message": "단일 방법론만 사용. 삼각검증 부재",
                "observed": modelsUsed,
                "expected": 2,
            }
        )


def _ruleTaxConsistency(
    effectiveTaxRatePct: Any,
    marginalTax: float,
    flags: list[dict],
    checks: dict[str, Any],
) -> None:
    """규칙 6: 유효세율 vs 한계세율 괴리.

    Parameters
    ----------
    effectiveTaxRatePct : Any
        유효세율 (%).
    marginalTax : float
        한계세율 (%).
    flags, checks : list, dict
        누적 구조. 제자리 변경.
    """
    checks["taxRateConsistency"] = True
    if not isinstance(effectiveTaxRatePct, (int, float)):
        return
    gap = abs(effectiveTaxRatePct - marginalTax)
    if gap > 5.0:
        checks["taxRateConsistency"] = False
        flags.append(
            {
                "rule": "tax_consistency",
                "severity": _SEV_INFO,
                "message": f"유효세율 {effectiveTaxRatePct:.1f}% vs 한계세율 {marginalTax:.1f}%. terminal 구간 세율 점검",
                "observed": effectiveTaxRatePct,
                "expected": marginalTax,
            }
        )


def _ruleGrowthOptimism(
    growthRatePct: Any,
    terminalGrowthPct: Any,
    rfPct: float,
    flags: list[dict],
) -> None:
    """규칙 7: 성장 가정 연쇄 과대 (Damodaran 7 Sins 1 번).

    Parameters
    ----------
    growthRatePct, terminalGrowthPct : Any
        explicit 구간 성장률과 영구성장률 (%).
    rfPct : float
        무위험수익률 (%).
    flags : list
        누적 구조. 제자리 변경.
    """
    if not (isinstance(growthRatePct, (int, float)) and isinstance(terminalGrowthPct, (int, float))):
        return
    if growthRatePct > 30 and terminalGrowthPct > rfPct:
        flags.append(
            {
                "rule": "growth_optimism",
                "severity": _SEV_WARN,
                "message": f"explicit 구간 {growthRatePct:.0f}% + terminal {terminalGrowthPct:.1f}%. 성장 가정 연쇄 과대",
                "observed": {"explicit": growthRatePct, "terminal": terminalGrowthPct},
                "expected": {"explicit": "< 30%", "terminal": f"< {rfPct:.1f}%"},
            }
        )


def _severityAndScore(flags: list[dict]) -> tuple[str, int]:
    """플래그 목록에서 최고 심각도와 100 점 감점 점수를 낸다.

    Parameters
    ----------
    flags : list[dict]
        규칙 위반 플래그.

    Returns
    -------
    tuple[str, int]
        (severity, score). critical -40, warn -15, 나머지 -5. 하한 0.
    """
    severity = _SEV_INFO
    for f in flags:
        if _SEV_ORDER[f["severity"]] > _SEV_ORDER[severity]:
            severity = f["severity"]

    score = 100
    for f in flags:
        if f["severity"] == _SEV_CRITICAL:
            score -= 40
        elif f["severity"] == _SEV_WARN:
            score -= 15
        else:
            score -= 5
    return severity, max(0, score)


__all__ = [
    "_SEV_CRITICAL",
    "_SEV_INFO",
    "_SEV_ORDER",
    "_SEV_WARN",
    "_mergeValuation",
    "_resolveFromCompany",
    "_ruleDiscountRateMatch",
    "_ruleGrowthEquation",
    "_ruleGrowthOptimism",
    "_ruleSingleModel",
    "_ruleTaxConsistency",
    "_ruleTerminalGrowthBounded",
    "_ruleTerminalValueShare",
    "_severityAndScore",
]
