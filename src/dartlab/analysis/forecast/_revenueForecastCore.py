"""revenueForecast 의 forecastRevenue 본체. 4-source 앙상블."""

from __future__ import annotations

import logging

from dartlab.analysis.forecast._revenueForecastEnsemble import (
    _consensusBaseline,
    _consensusGrowthRates,
    _ensembleProjection,
    _overrideProjection,
    _padProjected,
    _pathGrowthRates,
    _resolveBaseRevenue,
    _roicTimeseriesGap,
    _timeseriesGrowthRates,
)
from dartlab.analysis.forecast._revenueForecastHelpers import (
    _classifyLifecycle,
    _computeWeights,
    _fetchConsensusRevenue,
    _fundamentalGrowth,
    _lifecycleWeightAdjustments,
)
from dartlab.analysis.forecast._revenueForecastSegments import (
    _buildScenarios,
    _computeBacklogSignal,
    _extractSegmentForecasts,
    _segmentBottomUpGrowth,
)
from dartlab.analysis.forecast._revenueForecastTypes import (
    BacklogSignal,
    CompanyDataBundle,
    RevenueForecastResult,
    SegmentForecast,
)
from dartlab.analysis.forecast.forecast import forecastMetric

log = logging.getLogger(__name__)

# ROIC 기반 성장 소스 가중치
_ROIC_WEIGHT = 0.15

# 세그먼트 가중치
_SEGMENT_WEIGHT = 0.25

# 수주잔고 선행 시그널 가중치
_BACKLOG_WEIGHT = 0.15

# 시계열 최소 보장 가중치 (v3 소스 과도 희석 방지)
_TS_FLOOR = 0.10


# ══════════════════════════════════════
# 소스 수집 (앙상블 입력 4 종)
# ══════════════════════════════════════
#
# 각 소스는 "데이터가 없으면 조용히 비어서 돌아온다" 가 계약이다. 본체가 소스마다
# None 체크를 늘어놓지 않도록, 가용성 판정을 소스 함수 안에 가둔다.


def _timeseriesSource(series: dict, horizon: int) -> tuple[object, bool, list, float | None]:
    """시계열 소스 1 회 호출 + 앙상블 기준점 파생.

    tsResult/tsAvailable/historical/lastRevenue 는 늘 함께 쓰이는 한 덩어리라
    호출과 파생을 한 자리에 묶는다.
    """
    tsResult = forecastMetric(series, "revenue", horizon)
    tsAvailable = len(tsResult.projected) > 0

    # 과거 매출 시계열 (revenue 키 조회)
    historical = tsResult.historical

    # 최근 매출 (앙상블 기준점)
    validHist = [v for v in historical if v is not None]
    lastRevenue = validHist[-1] if validHist else None

    return tsResult, tsAvailable, historical, lastRevenue


def _segmentSource(
    companyData: CompanyDataBundle | None,
    horizon: int,
    lastRevenue: float | None,
) -> tuple[list[SegmentForecast], list[float]]:
    """세그먼트 Bottom-Up 소스. 세그먼트 데이터가 없으면 (빈 list, 빈 list)."""
    segmentForecasts: list[SegmentForecast] = []
    segGrowthRates: list[float] = []
    if companyData and companyData.segmentRevenue is not None:
        segmentForecasts = _extractSegmentForecasts(
            companyData.segmentRevenue,
            horizon,
        )
        if segmentForecasts:
            segGrowthRates = _segmentBottomUpGrowth(
                segmentForecasts,
                horizon,
                lastRevenue,
            )
    return segmentForecasts, segGrowthRates


def _backlogSource(
    companyData: CompanyDataBundle | None,
    sectorKey: str | None,
) -> BacklogSignal | None:
    """수주잔고 선행지표 소스. 수주 데이터가 없으면 None."""
    if companyData and companyData.orderDf is not None:
        return _computeBacklogSignal(
            companyData.orderDf,
            companyData.salesDf,
            sectorKey,
        )
    return None


# ══════════════════════════════════════
# 소스 가중치 배분
# ══════════════════════════════════════


def _applyTimeseriesFloor(weights: dict[str, float]) -> None:
    """시계열 가중치 하한 보정 (부족분은 v3 소스에서 비례 차감).

    동일 보정이 v3 할당 직후와 라이프사이클 조정 직후 두 번 필요하다. 두 벌로
    두면 한쪽만 고치는 표류가 생기므로 한 함수로 묶는다. weights 를 제자리에서
    고친다 (호출부가 이어서 같은 dict 를 넘긴다).
    """
    if "timeseries" not in weights or weights["timeseries"] >= _TS_FLOOR:
        return

    deficit = _TS_FLOOR - weights["timeseries"]
    weights["timeseries"] = _TS_FLOOR
    v3Keys = [k for k in ("segments", "backlog") if k in weights and weights[k] > 0]
    if not v3Keys:
        return

    totalV3 = sum(weights[k] for k in v3Keys)
    if totalV3 > 0:
        for k in v3Keys:
            weights[k] -= deficit * (weights[k] / totalV3)
            weights[k] = max(weights[k], 0.0)


def _allocateSourceWeights(
    tsAvailable: bool,
    consensusItems: list[tuple[int, float, str]],
    roicGrowth: float | None,
    structuralBreak: dict | None,
    segGrowthRates: list[float],
    backlogSignal: BacklogSignal | None,
    lifecycle: str,
) -> dict[str, float]:
    """소스 가용성 + 라이프사이클로 앙상블 가중치를 확정한다.

    가중치는 "누가 얼마나 있느냐" 만 보는 순수 배분이라 예측 경로와 섞이면
    읽기 어렵다. 배분 규칙 전체(기본 배분, v3 소스 할당, 하한 보정,
    라이프사이클 조정) 를 한 경계 안에 가둔다. 키 삽입 순서가 곧 결과
    ``sources`` 순서라 순서를 바꾸지 않는다.
    """
    weights = _computeWeights(tsAvailable, consensusItems, roicGrowth, structuralBreak=structuralBreak)

    # v3 소스 가중치 할당 (시계열에서 할당)
    if segGrowthRates and "timeseries" in weights:
        segShare = min(_SEGMENT_WEIGHT, weights["timeseries"])
        weights["segments"] = segShare
        weights["timeseries"] -= segShare

    if backlogSignal and "timeseries" in weights:
        blShare = min(_BACKLOG_WEIGHT, weights["timeseries"])
        weights["backlog"] = blShare
        weights["timeseries"] -= blShare

    # 시계열 최소 보장: 과도 희석 방지
    _applyTimeseriesFloor(weights)

    # 라이프사이클 기반 가중치 조정
    weights = _lifecycleWeightAdjustments(lifecycle, weights)

    # 시계열 최소 보장 재확인 (라이프사이클 조정이 다시 깎을 수 있다)
    _applyTimeseriesFloor(weights)

    return weights


# ══════════════════════════════════════
# 판정 + 결과 조립
# ══════════════════════════════════════


def _resolveMethodConfidence(
    weights: dict[str, float],
    tsResult: object,
    tsAvailable: bool,
    consensusProj: dict[int, float],
    lifecycle: str,
    market: str,
) -> tuple[str, str]:
    """method 와 confidence 동시 판정.

    둘 다 "살아있는 소스가 몇 개인가" 라는 같은 셈에서 갈라져 나오므로 한 함수로
    묶는다. 상한 규칙(transition, 비-KR 컨센서스 부재) 도 여기서 끝낸다.
    """
    activeSources = [s for s in weights if weights[s] > 0]
    if not activeSources:
        activeSources = ["timeseries"]
    method = "ensemble" if len(activeSources) > 1 else f"{activeSources[0]}_only"

    # 신뢰도: 소스 수 + 시계열 R² + 컨센서스 유무 + 라이프사이클
    if len(activeSources) >= 3 and tsResult.rSquared > 0.5:
        confidence = "high"
    elif len(activeSources) >= 2 and (tsAvailable or consensusProj):
        confidence = "medium" if lifecycle != "transition" else "low"
    elif tsAvailable or consensusProj:
        confidence = "medium"
    else:
        confidence = "low"

    # transition → 최대 medium
    if lifecycle == "transition" and confidence == "high":
        confidence = "medium"

    # 비-KR 시장에서 컨센서스 없으면 → 최대 medium
    if market != "KR" and not consensusProj:
        if confidence == "high":
            confidence = "medium"

    return method, confidence


def _forecastabilityVerdict(
    confidence: str,
    lifecycle: str,
    tsResult: object,
    consensusProj: dict[int, float],
    structuralBreak: dict | None,
) -> tuple[bool, str]:
    """예측 불가 판정 (거부 조건 2 개 이상 동시 충족 시 거부).

    조건을 list 로 모아 개수로 판정하는 구조라, 조건 추가가 판정식을 건드리지
    않도록 수집과 판정을 한 경계 안에 둔다.
    """
    unfConditions: list[str] = []
    if confidence == "low" and lifecycle == "transition":
        unfConditions.append("전환기 기업 + 낮은 신뢰도")
    if tsResult.rSquared < 0.1 and not consensusProj:
        unfConditions.append("시계열 R²<0.1 + 컨센서스 없음")
    if structuralBreak and structuralBreak.get("overallStability") == "volatile" and confidence != "high":
        unfConditions.append("다중 구조변화 + 높지 않은 신뢰도")

    forecastable = len(unfConditions) < 2
    return forecastable, "; ".join(unfConditions) if not forecastable else ""


def _normalizeSourceWeights(weights: dict[str, float]) -> dict[str, float]:
    """공개용 가중치 정규화 (합 1.0 보장 + 반올림 잔여분 보정).

    내부 배분은 하한/삭감을 거치며 합이 1.0 에서 밀린다. 결과 스키마는 합 1.0 을
    약속하므로 노출 직전 한 번만 정규화한다 (배분 로직과 분리해야 삭감 규칙이
    정규화에 오염되지 않는다).
    """
    wSum = sum(v for v in weights.values() if v > 0)
    if wSum > 0 and abs(wSum - 1.0) > 0.01:
        for k in weights:
            if weights[k] > 0:
                weights[k] = weights[k] / wSum

    finalWeights = {k: round(v, 2) for k, v in weights.items() if v > 0}
    if not finalWeights:
        finalWeights = {"timeseries": 1.0}
    # 반올림 오차 보정: 가장 큰 가중치에 잔여분 할당
    wTotal = sum(finalWeights.values())
    if abs(wTotal - 1.0) > 0.001 and finalWeights:
        maxKey = max(finalWeights, key=finalWeights.get)  # type: ignore[arg-type]
        finalWeights[maxKey] = round(finalWeights[maxKey] + (1.0 - wTotal), 2)

    return finalWeights


def _buildAssumptions(
    finalWeights: dict[str, float],
    tsResult: object,
    consensusProj: dict[int, float],
    roicGrowthRate: float | None,
    lifecycle: str,
    lifecycleDetail: dict,
) -> list[str]:
    """소스별 가정 문장 (정규화된 가중치 기준)."""
    assumptions: list[str] = []
    for src, w in finalWeights.items():
        if w > 0:
            if src == "timeseries":
                assumptions.append(f"시계열({w:.0%}): {tsResult.method}, R²={tsResult.rSquared:.2f}")
            elif src == "consensus":
                nEst = len(consensusProj)
                assumptions.append(f"컨센서스({w:.0%}): 네이버 금융 {nEst}개년 추정치")
            elif src == "roic":
                assumptions.append(f"ROIC({w:.0%}): g=ROIC×재투자율={roicGrowthRate:.1f}%")

    if lifecycle != "unknown":
        assumptions.append(
            f"라이프사이클: {lifecycle} (CAGR {lifecycleDetail.get('cagr_3y', 'N/A')}%, CV {lifecycleDetail.get('cv', 'N/A')})"
        )
    return assumptions


def _buildAiContext(
    growthRates: list[float],
    lifecycle: str,
    lifecycleDetail: dict,
    market: str,
    finalWeights: dict[str, float],
    tsResult: object,
    roicGrowthRate: float | None,
    roicDetail: dict,
    roicTsGap: float | None,
    tsGrowthRates: list[float],
    conGrowthRates: list[float],
    sectorKey: str | None,
    assumptions: list[str],
) -> tuple[dict, float | None]:
    """AI 브릿지 컨텍스트 기본 dict + 컨센서스/시계열 괴리.

    불확실성 플래그는 호출부에 남긴다. 플래그 append 순서가 곧 소비자가 읽는
    우선순위라 순서를 한눈에 보이는 자리에 둔다. conTsGap 은 여기서만 계산되고
    플래그 판정에도 쓰여 함께 돌려준다.
    """
    conTsGap: float | None = None
    if conGrowthRates and tsGrowthRates:
        avgCon = sum(conGrowthRates) / len(conGrowthRates)
        avgTs = sum(tsGrowthRates) / len(tsGrowthRates)
        conTsGap = avgCon - avgTs

    avgGrowth = sum(growthRates) / len(growthRates) if growthRates else 0.0
    aiContext: dict = {
        "base_growth": round(avgGrowth, 2),
        "lifecycle": lifecycle,
        "lifecycle_detail": lifecycleDetail,
        "market": market,
        "sources_used": list(finalWeights.keys()),
        "ts_method": tsResult.method,
        "ts_r_squared": tsResult.rSquared,
        "roic_growth": round(roicGrowthRate, 2) if roicGrowthRate is not None else None,
        "roic_detail": roicDetail if roicDetail else None,
        "roic_ts_gap": round(roicTsGap, 2) if roicTsGap is not None else None,
        "consensus_vs_ts_gap": round(conTsGap, 2) if conTsGap is not None else None,
        "sector_key": sectorKey,
        "key_assumptions": assumptions.copy(),
        "uncertainty_flags": [],
    }
    return aiContext, conTsGap


def _structuralBreakContext(structuralBreak: dict) -> dict:
    """구조변화 요약 (안정도 + 매출 break 여부 + break 개수)."""
    return {
        "stability": structuralBreak.get("overallStability", "stable"),
        "revenue_break": any(
            m.get("hasBreak") for m in structuralBreak.get("metrics", []) if m.get("name") == "revenue"
        ),
        "n_breaks": sum(1 for m in structuralBreak.get("metrics", []) if m.get("hasBreak")),
    }


def _attachSourceContext(
    aiContext: dict,
    segmentForecasts: list[SegmentForecast],
    backlogSignal: BacklogSignal | None,
) -> None:
    """v3 소스(세그먼트/수주잔고) 요약을 컨텍스트에 덧붙인다 (있을 때만 키 추가)."""
    if segmentForecasts:
        aiContext["segment_count"] = len(segmentForecasts)
        aiContext["segments_top3"] = [
            {"name": sf.name, "share": sf.shareOfRevenue, "growth": sf.growthRates[0] if sf.growthRates else 0}
            for sf in segmentForecasts[:3]
        ]
    if backlogSignal:
        aiContext["backlog"] = {
            "br_ratio": backlogSignal.backlogRevenueRatio,
            "trend": backlogSignal.brRatioTrend,
            "implied_growth": backlogSignal.impliedRevenueGrowth,
            "applicable": backlogSignal.sectorsApplicable,
        }


def forecastRevenue(
    series: dict,
    stockCode: str | None = None,
    sectorKey: str | None = None,
    market: str = "KR",
    horizon: int = 3,
    companyData: CompanyDataBundle | None = None,
    currency: str = "KRW",
    overrides: dict | None = None,
) -> RevenueForecastResult:
    """매출액 4-소스 앙상블 예측. fundamental + segment + backlog + consensus.

    Capabilities:
        4 source 가중평균: (1) fundamentalGrowth (재무 시계열 ARIMA-like) +
        (2) segment bottom-up (사업부문별 합산) + (3) backlog signal (수주
        잔고/계약자산) + (4) consensus (외부 추정치). 각 source 가중치는
        라이프사이클 단계 + 데이터 가용성으로 동적 조정. AI/사용자 overrides
        로 baseRevenue/growthRates 강제 가능.

    Args:
        series: ``finance.timeseries`` dict (BS/IS/CF).
        stockCode: 종목코드 (consensus 조회용). None 이면 consensus 제외.
        sectorKey: WICS 업종 키. lifecycle/탄성치 룩업.
        market: ``"KR"``/``"US"``. 기본 ``"KR"``.
        horizon: 예측 기간 (년). 기본 3.
        companyData: ``CompanyDataBundle``. segmentRevenue/orderDf/salesDf
            L1 데이터 브릿지. None 이면 segment + backlog source 제외.
        currency: ``"KRW"``/``"USD"``. 출력 단위.
        overrides: AI 가정 dict. 키:
            - ``baseRevenue`` (float): 시작점 강제
            - ``growthRates`` (list[float]): horizon 길이 list
            - ``primarySource`` (str): 4 source 중 하나 강제
            - ``ai`` (dict): RevenueForecastAIOverlay (시나리오 가중)

    Returns:
        RevenueForecastResult dataclass:
            - ``projected`` (list[float]): 연도별 예측 매출
            - ``growthRates`` (list[float]): 연도별 YoY (%)
            - ``method`` (str): ``"ensemble"`` 또는 ``"{source}_only"``
            - ``confidence`` (str): high/medium/low
            - ``sourceWeights`` (dict[str, float]): 4 source 가중치
            - ``scenarios`` (dict): bull/base/bear path
            - ``segmentForecasts`` (list[SegmentForecast]): 세그먼트 상세
            - ``backlogSignal`` (BacklogSignal|None): 수주잔고 신호
            - ``forecastable`` (bool): 예측 가능 여부
            - ``warnings``/``assumptions`` (list[str])

    Raises:
        없음.

    Example:
        >>> from dartlab import Company
        >>> c = Company("005930")
        >>> r = forecastRevenue(c.panel("timeseries"), stockCode="005930",
        ...                     sectorKey="IT", horizon=3)
        >>> r.projected, r.confidence

    Guide:
        weights 결정: fundamentalGrowth (안정 사업), segment (다각화 회사),
        backlog (수주 산업. 건설/조선/방산), consensus (대형주). 4 source
        모두 사용 가능 시 confidence=high. 1 개 source 만이면 medium 이하.

    When:
        매출 단일 예측이 아닌 4 source 앙상블 + 시나리오가 필요할 때.

    How:
        fundamentalGrowth + segment + backlog + consensus 가중 평균 후
        라이프사이클 보정.

    SeeAlso:
        - ``_extractSegmentForecasts``: 세그먼트 source
        - ``_computeBacklogSignal``: backlog source
        - ``_fundamentalGrowth``: fundamental source
        - ``simulateScenario``: 매크로 시나리오 결합 (forecast 의 다음 단계)

    Requires:
        series 가 finance.timeseries 스키마. 매출 시계열 ≥ 3 년.

    AIContext:
        sourceWeights 를 리포트에 항상 노출 (어떤 source 비중이 높은지).
        confidence=low 결과 단독 인용 금지. 호출자가 시나리오 cross-check.

    LLM Specifications:
        AntiPatterns:
            - growthRates override 길이가 horizon 과 다르면 자동 truncate/
              extend. 예상치 다르면 horizon 일치 권장.
            - market="US" + stockCode KR 조합. consensus 조회 실패.
        OutputSchema:
            RevenueForecastResult (12 필드 dataclass).
        Prerequisites:
            매출 시계열 ≥ 3 년 + sectorKey 적합.
        Freshness:
            series freshness (분기). consensus = T+1 캐시.
        Dataflow:
            series → _fundamentalGrowth + _extractSegmentForecasts +
            _computeBacklogSignal + _fetchConsensusRevenue → _computeWeights
            (lifecycle 별 가중) → 가중평균 projected → _buildScenarios → 결과.
        TargetMarkets: KR (DART), US (EDGAR).
    """
    warnings: list[str] = []

    # ── 라이프사이클 판별 ──
    lifecycle, lifecycleDetail = _classifyLifecycle(series)

    # ── Source 1: 시계열 예측 (기존 forecast.py) ──
    tsResult, tsAvailable, historical, lastRevenue = _timeseriesSource(series, horizon)

    # ── Source 2: 컨센서스 (KR: 네이버, US+: Yahoo) ──
    consensusItems: list[tuple[int, float, str]] = []
    if stockCode:
        consensusItems = _fetchConsensusRevenue(stockCode, market)
        if not consensusItems and market != "KR":
            warnings.append(f"컨센서스 수집 실패({market}). 시계열 기반 예측")

    # ── Source 4: ROIC 기반 내재 성장 ──
    roicGrowth, roicDetail = _fundamentalGrowth(series)
    roicGrowthRate: float | None = roicGrowth  # % 단위

    # ── Source 5: 세그먼트 Bottom-Up ──
    segmentForecasts, segGrowthRates = _segmentSource(companyData, horizon, lastRevenue)

    # ── Source 6: 수주잔고 선행지표 ──
    backlogSignal = _backlogSource(companyData, sectorKey)

    # ── 가중치 계산 ──
    _sb = companyData.structuralBreak if companyData else None
    weights = _allocateSourceWeights(
        tsAvailable,
        consensusItems,
        roicGrowth,
        _sb,
        segGrowthRates,
        backlogSignal,
        lifecycle,
    )

    # ── 앙상블 ──
    projected: list[float] = []

    # 컨센서스 actual/estimate 분해 + 기준 연도
    consensusProj, consensusRevenue, baseYear, lastActualRevenue = _consensusBaseline(consensusItems)

    # ── override 적용 ──
    from dartlab.synth.overrides import validateOverrides

    _ov = validateOverrides(overrides)

    lastRevenue = _resolveBaseRevenue(
        lastRevenue,
        lastActualRevenue,
        _ov,
        lifecycle,
        tsResult,
        tsAvailable,
        warnings,
    )

    # 소스별 성장률 시계열
    tsGrowthRates = _timeseriesGrowthRates(tsResult, tsAvailable)
    conGrowthRates = _consensusGrowthRates(consensusProj, lastRevenue)

    # ROIC 성장률: horizon 동안 일정 (내재 성장은 구조적)
    roicG = roicGrowthRate if roicGrowthRate is not None else 0.0

    # ROIC vs 시계열 괴리 감지
    roicTsGap = _roicTimeseriesGap(roicGrowthRate, tsGrowthRates, warnings)

    # override: growthRates (AI/사용자 직접 지정 → 앙상블 전체 교체)
    if "growthRates" in _ov:
        ovGrowth = _ov["growthRates"]
        projected = _overrideProjection(ovGrowth, lastRevenue, horizon)
        warnings.append(f"growthRates override: {ovGrowth}")
        # growthRates → projected 직접 산출 후 아래 앙상블 건너뜀
        growthRates = list(ovGrowth[:horizon])
        while len(growthRates) < horizon:
            growthRates.append(growthRates[-1] if growthRates else 3.0)
    else:
        projected = []

    # 앙상블: 성장률 기반 블렌딩 (override 시 이미 projected 채워짐 → 건너뜀)
    if not projected:
        projected = _ensembleProjection(
            lastRevenue,
            horizon,
            weights,
            tsGrowthRates,
            conGrowthRates,
            roicG,
            segGrowthRates,
            backlogSignal,
        )

    # ── 스키마 보장: projected가 horizon보다 적으면 패딩 ──
    projected = _padProjected(projected, horizon, lastRevenue)

    # ── 성장률 계산 ──
    growthRates = _pathGrowthRates(projected, lastRevenue, horizon)

    # ── 메서드 & 신뢰도 결정 ──
    method, confidence = _resolveMethodConfidence(
        weights,
        tsResult,
        tsAvailable,
        consensusProj,
        lifecycle,
        market,
    )

    # ── 예측 불가 판정 (2개 이상 조건 동시 충족 시 거부) ──
    _forecastable, _unfReason = _forecastabilityVerdict(confidence, lifecycle, tsResult, consensusProj, _sb)
    if not _forecastable:
        warnings.append(f"예측 불가 판정: {_unfReason}")

    # ── 스키마 보장: sourceWeights 합이 1.0 ──
    finalWeights = _normalizeSourceWeights(weights)

    # ── 가정 설명 (정규화된 가중치 기준) ──
    assumptions = _buildAssumptions(
        finalWeights,
        tsResult,
        consensusProj,
        roicGrowthRate,
        lifecycle,
        lifecycleDetail,
    )

    # ── AI 컨텍스트 (Tier 2 브릿지) ──
    aiContext, conTsGap = _buildAiContext(
        growthRates,
        lifecycle,
        lifecycleDetail,
        market,
        finalWeights,
        tsResult,
        roicGrowthRate,
        roicDetail,
        roicTsGap,
        tsGrowthRates,
        conGrowthRates,
        sectorKey,
        assumptions,
    )

    # 불확실성 플래그
    if lifecycle == "transition":
        aiContext["uncertainty_flags"].append("전환기 기업. 과거 추세 신뢰도 낮음")
    if roicTsGap is not None and abs(roicTsGap) > 10:
        aiContext["uncertainty_flags"].append(f"ROIC-시계열 괴리 {roicTsGap:+.1f}%p")
    if conTsGap is not None and abs(conTsGap) > 15:
        aiContext["uncertainty_flags"].append(f"컨센서스-시계열 괴리 {conTsGap:+.1f}%p")
    if not consensusProj:
        aiContext["uncertainty_flags"].append("컨센서스 데이터 없음")

    # 구조변화 컨텍스트 (forecastCalcs.py dead code 활성화)
    if _sb:
        aiContext["structural_break"] = _structuralBreakContext(_sb)
        if _sb.get("overallStability") in ("volatile", "transitioning"):
            aiContext["uncertainty_flags"].append(f"구조변화 감지 ({_sb['overallStability']}). 과거 추세 신뢰도 제한")

    # ── v3: 3-시나리오 ──
    scenarios, scenarioGrs, scenarioProbs = _buildScenarios(
        projected,
        [round(g, 1) for g in growthRates],
        historical,
        lifecycle,
        lastRevenue,
        structuralBreak=_sb,
    )

    # v3: 세그먼트/수주잔고 AI 컨텍스트
    _attachSourceContext(aiContext, segmentForecasts, backlogSignal)

    # Forward test 키 생성 (저장은 opt-in)
    ftKey = None
    if stockCode:
        from dartlab.analysis.forecast.forwardTest import generateKey

        ftKey = generateKey(stockCode, horizon)

    return RevenueForecastResult(
        historical=historical,
        projected=projected,
        horizon=horizon,
        method=method,
        confidence=confidence,
        growthRates=[round(g, 1) for g in growthRates],
        sources=list(finalWeights.keys()),
        sourceWeights=finalWeights,
        consensusRevenue=consensusRevenue,
        assumptions=assumptions,
        warnings=warnings + tsResult.warnings,
        aiContext=aiContext,
        scenarios=scenarios,
        scenarioGrowthRates=scenarioGrs,
        scenarioProbabilities=scenarioProbs,
        segmentForecasts=segmentForecasts,
        backlogSignal=backlogSignal,
        forwardTestKey=ftKey,
        currency=currency,
        forecastable=_forecastable,
        unforecastableReason=_unfReason,
    )
