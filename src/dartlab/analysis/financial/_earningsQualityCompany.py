"""earningsQuality 의 회사 기반 calc — Accrual/Persistence/QualityFlags."""

from __future__ import annotations

import math

from dartlab.analysis.financial._constants import ACCRUAL_RATIO_WARNING
from dartlab.analysis.financial._earningsQualityCalcs import (
    _beneishInterpretation,
    _calcEarningsQualityFlagsBase,
    calcBeneishMScore,
    calcSloanAccruals,
    detectAuditFlags,
)
from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.calc import safeDiv as _safe
from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId
from dartlab.core.utils.safe import get as _get

_getF = _getF2 = _getF3 = _getF4 = _get
_MAX_YEARS = 8


def _calcBeneishTimeline(company, *, basePeriod: str | None = None) -> dict | None:
    """Lazy proxy — _earningsQualityDeep.calcBeneishTimeline 호출 (cycle 회피)."""
    from dartlab.analysis.financial._earningsQualityDeepBeneish import (
        calcBeneishTimeline as _f,
    )

    return _f(company, basePeriod=basePeriod)


def calcAccrualAnalysis(company, *, basePeriod: str | None = None) -> dict | None:
    """발생액(Accrual) 시계열 — 이익 중 현금이 아닌 비중.

    Returns
    -------
    dict
        history : list[dict] — 기간별 발생액 시계열
            period : str — 회계연도
            netIncome : float — 당기순이익 (원)
            ocf : float — 영업활동현금흐름 (원)
            totalAssets : float — 자산총계 (원)
            sloanAccrualRatio : float | None — Sloan 발생액비율 (배)
            accrualToRevenue : float | None — 발생액/매출액 (%)
            ocfToNi : float | None — 영업CF/순이익 (%)
        notesDetail : dict | None — 매출채권 대손충당금 주석 (있는 경우)

    Capabilities:
        - 발생액 시계열 + Sloan ratio + accrual/revenue + OCF/NI 4 지표 종합
        - notesDetail 로 매출채권 대손 보강

    Guide:
        OCF/NI < 80% 가 3 년 지속 = 이익 품질 의심.

    When:
        Earnings quality 시계열 + AI 발생액 시간 추세 답변.

    How:
        IS/CF/BS 시계열 → 발생액 + 비율 계산.

    Requires:
        IS/CF/BS 시계열.

    Raises:
        없음.

    Example:
        >>> calcAccrualAnalysis(company)["history"][-1]["ocfToNi"]
        92

    See Also:
        - calcSloanAccruals : 단일 지표
        - _earningsQualityDeep.calcRichardsonAccrual : 3 계층

    AIContext:
        "이익 품질 추세" 답변 시 ocfToNi 시계열 인용.
    """
    isResult = company.select("IS", ["당기순이익", "매출액"])
    cfResult = company.select("CF", ["영업활동현금흐름"])
    bsResult = company.select("BS", ["자산총계"])

    isParsed = toDictBySnakeId(isResult)
    cfParsed = toDictBySnakeId(cfResult)
    bsParsed = toDictBySnakeId(bsResult)
    if isParsed is None or cfParsed is None or bsParsed is None:
        return None

    isData, _ = isParsed
    cfData, cfPeriods = cfParsed
    bsData, _ = bsParsed

    niRow = isData.get("당기순이익", {})
    revRow = isData.get("매출액", {})
    ocfRow = cfData.get("영업활동현금흐름", {})
    taRow = bsData.get("자산총계", {})

    yCols = annualColsFromPeriods(cfPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if not yCols:
        return None

    history = []
    for col in yCols:
        ni = _getF(niRow, col)
        ocf = _getF(ocfRow, col)
        ta = _get(taRow, col)
        rev = _getF(revRow, col)
        accrual = ni - ocf

        history.append(
            {
                "period": col,
                "netIncome": ni,
                "ocf": ocf,
                "totalAssets": ta,
                "sloanAccrualRatio": _safe(accrual, ta) if ta > 0 else None,
                "accrualToRevenue": _safe(accrual, rev) * 100 if rev > 0 and _safe(accrual, rev) is not None else None,
                "ocfToNi": (lambda r: r if abs(r) <= 1000 else None)(_safe(ocf, ni) * 100)
                if ni != 0 and _safe(ocf, ni) is not None
                else None,
            }
        )

    if not history:
        return None

    result: dict = {"history": history}

    # notes enrichment — 매출채권 대손충당금 상세
    from dartlab.analysis.financial.companyContext import fetchNotesDetail

    notesDetail = fetchNotesDetail(company, ["receivables"])
    if notesDetail:
        result["notesDetail"] = notesDetail

    return result


# ── 이익 지속성 ──


@memoizedCalc
def calcEarningsPersistence(company, *, basePeriod: str | None = None) -> dict | None:
    """이익 지속성 — 영업이익 vs 영업외손익, 변동성.

    Returns
    -------
    dict
        history : list[dict] — 기간별 이익 구성 시계열
            period : str — 회계연도
            operatingIncome : float — 영업이익 (원)
            preTaxIncome : float — 법인세차감전순이익 (원)
            nonOperatingIncome : float — 영업외손익 (원)
            nonOpRatio : float | None — 영업외/영업이익 비율 (%)
        earningsVolatility : float | None — 영업이익 변동계수 (배)

    Capabilities:
        - 영업이익 vs 세전이익 분해 → 영업외 비중 + 변동계수 (CV)
        - 이익 안정성 측정

    Guide:
        nonOpRatio ≥ 30% = 비영업 이익 의존. CV ≥ 0.5 = 변동 큰 이익.

    When:
        Earnings persistence + AI 이익 안정성 답변.

    How:
        IS 시계열 → 영업/세전 분해 → 변동계수.

    Requires:
        IS 시계열 ≥ 3 년.

    Raises:
        없음.

    Example:
        >>> calcEarningsPersistence(company)["earningsVolatility"]
        0.18

    See Also:
        - _earningsQualityDeep.calcNonOperatingBreakdown : 정밀 비영업
        - calcAccrualAnalysis : 발생액

    AIContext:
        "이익 안정성" 답변 시 nonOpRatio + earningsVolatility 인용.
    """
    accounts = ["영업이익", "법인세차감전순이익", "세전이익"]
    isResult = company.select("IS", accounts)
    isParsed = toDictBySnakeId(isResult)
    if isParsed is None:
        return None

    isData, isPeriods = isParsed
    opRow = isData.get("영업이익", {})
    # 세전이익 fallback
    ptRow = isData.get("법인세차감전순이익", isData.get("세전이익", {}))

    yCols = annualColsFromPeriods(isPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if not yCols:
        return None

    history = []
    opValues = []
    for col in yCols:
        opIncome = _getF2(opRow, col)
        ptIncome = _getF2(ptRow, col)
        nonOp = ptIncome - opIncome

        nonOpRatio = None
        if opIncome > 0:
            nonOpRatio = abs(nonOp) / opIncome * 100

        history.append(
            {
                "period": col,
                "operatingIncome": opIncome,
                "preTaxIncome": ptIncome,
                "nonOperatingIncome": nonOp,
                "nonOpRatio": nonOpRatio,
            }
        )
        if opIncome != 0:
            opValues.append(opIncome)

    # 변동계수 (CV = std / |mean|)
    earningsVolatility = None
    if len(opValues) >= 3:
        mean = sum(opValues) / len(opValues)
        if mean != 0:
            variance = sum((v - mean) ** 2 for v in opValues) / len(opValues)
            earningsVolatility = math.sqrt(variance) / abs(mean)

    return {"history": history, "earningsVolatility": earningsVolatility} if history else None


# ── Beneish M-Score 시계열 ──


# ── 플래그 ──


@memoizedCalc
def calcEarningsQualityFlags(company, *, basePeriod: str | None = None) -> dict:
    """이익 품질 경고 신호.

    Returns
    -------
    dict
        flags : list[str] — 경고 메시지 목록 (발생액 과다, CF 부족, M-Score 초과 등)
        enrichedFlags : list[dict] — 구조화된 플래그 (정밀도/기저율/학술근거 포함)
            code : str — 플래그 코드
            message : str — 경고 메시지
            precision : float | None — 정밀도
            baseRate : str — 표본 기반
            reference : str — 학술 근거
            sectorNote : str — 업종별 주의사항

    Capabilities:
        - accrual/persistence/Beneish/audit 4 sub-calc 결과 → 종합 flag list + enrichedFlags
        - precision/baseRate/reference 메타로 정확도 명시

    Guide:
        story earnings quality flag 박스 입력. enriched ≥ 2 critical = 매도 검토.

    When:
        Story flag + AI 회계 위험 답변.

    How:
        4 sub-calc 호출 → 임계 비교 → flags + enriched 누적.

    Requires:
        IS/BS/CF + audit text.

    Raises:
        없음.

    Example:
        >>> calcEarningsQualityFlags(company)["flags"]
        ['Sloan 발생액비율 15% — 이익 현금화 부족']

    See Also:
        - calcAccrualAnalysis : 발생액
        - detectAuditFlags : 감사 키워드

    AIContext:
        "회계 위험 종합" 답변 시 flags + enrichedFlags 인용.
    """
    flags: list[str] = []
    enriched: list[dict] = []
    observedComponents: list[str] = []

    accrual = calcAccrualAnalysis(company, basePeriod=basePeriod)
    if accrual and accrual["history"]:
        observedComponents.append("accrual")
        h0 = accrual["history"][0]
        sar = h0.get("sloanAccrualRatio")
        if sar is not None and sar > ACCRUAL_RATIO_WARNING:
            flags.append(f"Sloan 발생액비율 {sar:.1%} — 이익 현금화 부족")
        ocfNi = h0.get("ocfToNi")
        if ocfNi is not None and 0 < ocfNi < 40:
            flags.append(f"영업CF/순이익 {ocfNi:.0f}% — 이익 대비 현금 부족")

    persistence = calcEarningsPersistence(company, basePeriod=basePeriod)
    if persistence:
        if persistence.get("history") or persistence.get("earningsVolatility") is not None:
            observedComponents.append("persistence")
        if persistence["history"]:
            h0 = persistence["history"][0]
            nonOpRatio = h0.get("nonOpRatio")
            nonOpIncome = h0.get("nonOperatingIncome")
            if nonOpRatio is not None and nonOpRatio > 30:
                if nonOpIncome is not None and nonOpIncome < 0:
                    suffix = " (일회성 항목 가능성)" if nonOpRatio > 100 else ""
                    flags.append(f"영업외손실 비중 {nonOpRatio:.0f}% — 영업이익을 상쇄{suffix}")
                else:
                    suffix = " (일회성 항목 가능성)" if nonOpRatio > 100 else ""
                    flags.append(f"영업외이익 비중 {nonOpRatio:.0f}% — 일회성 이익 의존{suffix}")

        cv = persistence.get("earningsVolatility")
        if cv is not None and cv > 0.5:
            flags.append(f"이익 변동계수 {cv:.2f} — 이익 변동성 높음")

    beneish = _calcBeneishTimeline(company, basePeriod=basePeriod)
    if beneish and beneish["history"]:
        observedComponents.append("beneish")
        h0 = beneish["history"][0]
        ms = h0.get("mScore")
        if ms is not None and ms > -1.78:
            msg = f"Beneish M-Score {ms:.2f} — 임계값 초과, 이익 조작 가능성"
            flags.append(msg)
            meta = beneish.get("diagnosticMeta", {})
            enriched.append(
                {
                    "code": "BENEISH_MANIPULATOR",
                    "message": msg,
                    "precision": meta.get("precision"),
                    "baseRate": meta.get("sampleBase", ""),
                    "reference": meta.get("reference", ""),
                    "sectorNote": meta.get("krNote", ""),
                }
            )

    expectedComponents = 3
    observedCount = len(set(observedComponents))
    coverageStatus = "observed" if observedCount == expectedComponents else "partial" if observedCount else "missing"
    return {
        "flags": flags,
        "enrichedFlags": enriched,
        "coverage": {
            "status": coverageStatus,
            "observed": observedCount,
            "expected": expectedComponents,
            "components": sorted(set(observedComponents)),
            "reason": (
                None
                if coverageStatus == "observed"
                else f"이익품질 하위 계산 근거 {observedCount}/{expectedComponents}개만 관측"
            ),
        },
    }


# ── Richardson 3계층 발생액 분해 ──


# ── 영업외손익 분해 ──


# ── EPS 희석 분석 ──
