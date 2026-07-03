"""revenueForecast 의 forecastRevenue 본체 — 4-source 앙상블."""

from __future__ import annotations

import logging

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
    """매출액 4-소스 앙상블 예측 — fundamental + segment + backlog + consensus.

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
        companyData: ``CompanyDataBundle`` — segmentRevenue/orderDf/salesDf
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
        backlog (수주 산업 — 건설/조선/방산), consensus (대형주). 4 source
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
        confidence=low 결과 단독 인용 금지 — 호출자가 시나리오 cross-check.

    LLM Specifications:
        AntiPatterns:
            - growthRates override 길이가 horizon 과 다르면 자동 truncate/
              extend — 예상치 다르면 horizon 일치 권장.
            - market="US" + stockCode KR 조합 — consensus 조회 실패.
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
    assumptions: list[str] = []

    # ── 라이프사이클 판별 ──
    lifecycle, lifecycleDetail = _classifyLifecycle(series)

    # ── Source 1: 시계열 예측 (기존 forecast.py) ──
    tsResult = forecastMetric(series, "revenue", horizon)
    tsAvailable = len(tsResult.projected) > 0

    # 과거 매출 시계열 (revenue 키 조회)
    historical = tsResult.historical

    # 최근 매출 (앙상블 기준점)
    validHist = [v for v in historical if v is not None]
    lastRevenue = validHist[-1] if validHist else None

    # ── Source 2: 컨센서스 (KR: 네이버, US+: Yahoo) ──
    consensusItems: list[tuple[int, float, str]] = []
    if stockCode:
        consensusItems = _fetchConsensusRevenue(stockCode, market)
        if not consensusItems and market != "KR":
            warnings.append(f"컨센서스 수집 실패({market}) — 시계열 기반 예측")

    # ── Source 4: ROIC 기반 내재 성장 ──
    roicGrowth, roicDetail = _fundamentalGrowth(series)
    roicGrowthRate: float | None = roicGrowth  # % 단위

    # ── Source 5: 세그먼트 Bottom-Up ──
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

    # ── Source 6: 수주잔고 선행지표 ──
    backlogSignal: BacklogSignal | None = None
    if companyData and companyData.orderDf is not None:
        backlogSignal = _computeBacklogSignal(
            companyData.orderDf,
            companyData.salesDf,
            sectorKey,
        )

    # ── 가중치 계산 ──
    _sb = companyData.structuralBreak if companyData else None
    weights = _computeWeights(tsAvailable, consensusItems, roicGrowth, structuralBreak=_sb)

    # v3 소스 가중치 할당 (시계열에서 할당)
    if segGrowthRates and "timeseries" in weights:
        segShare = min(_SEGMENT_WEIGHT, weights["timeseries"])
        weights["segments"] = segShare
        weights["timeseries"] -= segShare

    if backlogSignal and "timeseries" in weights:
        blShare = min(_BACKLOG_WEIGHT, weights["timeseries"])
        weights["backlog"] = blShare
        weights["timeseries"] -= blShare

    # 시계열 최소 보장: 과도 희석 방지 (최소 0.10)
    _TS_FLOOR = 0.10
    if "timeseries" in weights and weights["timeseries"] < _TS_FLOOR:
        deficit = _TS_FLOOR - weights["timeseries"]
        weights["timeseries"] = _TS_FLOOR
        # 부족분을 다른 v3 소스에서 비례 차감
        v3Keys = [k for k in ("segments", "backlog") if k in weights and weights[k] > 0]
        if v3Keys:
            totalV3 = sum(weights[k] for k in v3Keys)
            for k in v3Keys:
                weights[k] -= deficit * (weights[k] / totalV3)
                weights[k] = max(weights[k], 0.0)

    # 라이프사이클 기반 가중치 조정
    weights = _lifecycleWeightAdjustments(lifecycle, weights)

    # 시계열 최소 보장 재확인 (라이프사이클 조정 후)
    if "timeseries" in weights and weights["timeseries"] < _TS_FLOOR:
        deficit = _TS_FLOOR - weights["timeseries"]
        weights["timeseries"] = _TS_FLOOR
        v3Keys2 = [k for k in ("segments", "backlog") if k in weights and weights[k] > 0]
        if v3Keys2:
            totalV3_2 = sum(weights[k] for k in v3Keys2)
            if totalV3_2 > 0:
                for k in v3Keys2:
                    weights[k] -= deficit * (weights[k] / totalV3_2)
                    weights[k] = max(weights[k], 0.0)

    # ── 앙상블 ──
    projected: list[float] = []
    consensusRevenue: list[float] = []

    # 컨센서스에서 전체 매출 시계열 (actual + estimate) 구축
    consensusByYear: dict[int, tuple[float, str]] = {}  # year → (revenue_원, source)
    if consensusItems:
        for fy, rev, src in consensusItems:
            if rev > 0:
                consensusByYear[fy] = (rev * 1e8, src)  # 억원 → 원

    # 컨센서스 estimate만 추출
    consensusProj: dict[int, float] = {}
    for fy, (revWon, src) in consensusByYear.items():
        if src.endswith("_consensus"):
            consensusProj[fy] = revWon
            consensusRevenue.append(revWon)

    # ── override 적용 ──
    from dartlab.synth.overrides import validateOverrides

    _ov = validateOverrides(overrides)

    # 기준 연도: 컨센서스 actual 중 가장 최근
    baseYear = 0
    lastActualRevenue: float | None = None
    actualsSorted = sorted(
        [(fy, rev) for fy, (rev, src) in consensusByYear.items() if src.endswith("_actual")],
        key=lambda x: x[0],
    )
    if actualsSorted:
        baseYear = actualsSorted[-1][0]
        lastActualRevenue = actualsSorted[-1][1]
    if baseYear == 0:
        baseYear = 2025

    # lastRevenue를 컨센서스 actual과 동기화 (더 신뢰할 수 있으므로)
    if lastActualRevenue:
        lastRevenue = lastActualRevenue

    # override: baseRevenue
    if "baseRevenue" in _ov:
        lastRevenue = _ov["baseRevenue"]
        warnings.append(f"baseRevenue override: {lastRevenue / 1e12:.1f}조")

    # mid-cycle 정규화 (사이클 기업 자동, override 없을 때)
    if "baseRevenue" not in _ov and lifecycle in ("cyclical", "mature_cyclical"):
        historicals = [v for v in (tsResult.historical if tsAvailable and tsResult else []) if v and v > 0]
        if len(historicals) >= 3:
            midCycleRevenue = sum(historicals[-5:]) / len(historicals[-5:])
            if lastRevenue and abs(lastRevenue - midCycleRevenue) / midCycleRevenue > 0.15:
                lastRevenue = midCycleRevenue
                warnings.append(f"사이클 기업 → mid-cycle 매출 {midCycleRevenue / 1e12:.1f}조 적용")

    # 시계열 성장률: projected 간 YoY 성장률 (분기 데이터이므로 자체 기준 비교)
    tsGrowthRates: list[float] = []
    if tsAvailable and tsResult.projected:
        prev = tsResult.historical[-1] if tsResult.historical and tsResult.historical[-1] else None
        for p in tsResult.projected:
            if prev and prev > 0 and p > 0:
                tsGrowthRates.append((p / prev - 1) * 100)
            else:
                tsGrowthRates.append(tsResult.growthRate)
            prev = p

    # 컨센서스 성장률 계산
    conGrowthRates: list[float] = []
    sortedConYears = sorted(consensusProj.keys())
    for i, fy in enumerate(sortedConYears):
        if i == 0:
            # 첫 컨센서스 연도: actual 대비 성장률
            if lastRevenue and lastRevenue > 0:
                conGrowthRates.append((consensusProj[fy] / lastRevenue - 1) * 100)
            else:
                conGrowthRates.append(0.0)
        else:
            prevFy = sortedConYears[i - 1]
            prevRev = consensusProj[prevFy]
            if prevRev > 0:
                conGrowthRates.append((consensusProj[fy] / prevRev - 1) * 100)
            else:
                conGrowthRates.append(0.0)

    # ROIC 성장률: horizon 동안 일정 (내재 성장은 구조적)
    roicG = roicGrowthRate if roicGrowthRate is not None else 0.0

    # ROIC vs 시계열 괴리 감지
    roicTsGap: float | None = None
    if roicGrowthRate is not None and tsGrowthRates:
        avgTsG = sum(tsGrowthRates) / len(tsGrowthRates)
        roicTsGap = roicGrowthRate - avgTsG
        if abs(roicTsGap) > 10:
            warnings.append(
                f"ROIC 내재 성장률({roicGrowthRate:.1f}%)과 시계열 성장률({avgTsG:.1f}%) 괴리 {roicTsGap:+.1f}%p"
            )

    # override: growthRates (AI/사용자 직접 지정 → 앙상블 전체 교체)
    if "growthRates" in _ov:
        ovGrowth = _ov["growthRates"]
        projected = []
        prevR = lastRevenue or 0
        for i in range(horizon):
            g = ovGrowth[i] if i < len(ovGrowth) else (ovGrowth[-1] if ovGrowth else 3.0)
            prevR = prevR * (1 + g / 100)
            projected.append(prevR)
        warnings.append(f"growthRates override: {ovGrowth}")
        # growthRates → projected 직접 산출 후 아래 앙상블 건너뜀
        growthRates = list(ovGrowth[:horizon])
        while len(growthRates) < horizon:
            growthRates.append(growthRates[-1] if growthRates else 3.0)
    else:
        projected = []

    # 앙상블: 성장률 기반 블렌딩 (override 시 이미 projected 채워짐 → 건너뜀)
    prevRevenue = lastRevenue or 0
    if projected:
        pass  # override에서 이미 채움
    else:
        for yrOffset in range(1, horizon + 1):
            if prevRevenue <= 0:
                break

            # 시계열 성장률
            tsG = (
                tsGrowthRates[yrOffset - 1]
                if yrOffset <= len(tsGrowthRates)
                else (tsGrowthRates[-1] if tsGrowthRates else 0.0)
            )

            # 컨센서스 성장률
            conG = conGrowthRates[yrOffset - 1] if yrOffset <= len(conGrowthRates) else None

            # 가중 성장률 계산
            blendedGrowth = 0.0
            if conG is not None and "consensus" in weights:
                blendedGrowth += conG * weights.get("consensus", 0)
                blendedGrowth += tsG * weights.get("timeseries", 0)
            else:
                # 컨센서스 없는 연도 → 시계열이 컨센서스 몫도 흡수
                blendedGrowth += tsG * (weights.get("timeseries", 0) + weights.get("consensus", 0))

            blendedGrowth += roicG * weights.get("roic", 0)

            # 세그먼트 Bottom-Up 성장률
            if segGrowthRates and "segments" in weights:
                segG = (
                    segGrowthRates[yrOffset - 1]
                    if yrOffset <= len(segGrowthRates)
                    else (segGrowthRates[-1] if segGrowthRates else 0.0)
                )
                blendedGrowth += segG * weights.get("segments", 0)

            # 수주잔고 내재 성장률
            if backlogSignal and "backlog" in weights:
                # 수주잔고 신호는 horizon 동안 감쇠
                decay = max(0.5, 1.0 - (yrOffset - 1) * 0.2)
                blendedGrowth += backlogSignal.impliedRevenueGrowth * decay * weights.get("backlog", 0)

            projVal = prevRevenue * (1 + blendedGrowth / 100)
            projected.append(projVal)
            prevRevenue = projVal

    # ── 스키마 보장: projected가 horizon보다 적으면 패딩 ──
    while len(projected) < horizon:
        if projected:
            projected.append(projected[-1])
        elif lastRevenue and lastRevenue > 0:
            projected.append(lastRevenue)
        else:
            projected.append(0.0)

    # ── 성장률 계산 ──
    growthRates: list[float] = []
    for i, proj in enumerate(projected):
        if i == 0 and lastRevenue and lastRevenue > 0:
            growthRates.append((proj / lastRevenue - 1) * 100)
        elif i > 0 and projected[i - 1] > 0:
            growthRates.append((proj / projected[i - 1] - 1) * 100)
        else:
            growthRates.append(0.0)

    while len(growthRates) < horizon:
        growthRates.append(0.0)

    # ── 메서드 & 신뢰도 결정 ──
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

    # ── 예측 불가 판정 (2개 이상 조건 동시 충족 시 거부) ──
    _unfConditions: list[str] = []
    if confidence == "low" and lifecycle == "transition":
        _unfConditions.append("전환기 기업 + 낮은 신뢰도")
    if tsResult.rSquared < 0.1 and not consensusProj:
        _unfConditions.append("시계열 R²<0.1 + 컨센서스 없음")
    if _sb and _sb.get("overallStability") == "volatile" and confidence != "high":
        _unfConditions.append("다중 구조변화 + 높지 않은 신뢰도")

    _forecastable = len(_unfConditions) < 2
    _unfReason = "; ".join(_unfConditions) if not _forecastable else ""
    if not _forecastable:
        warnings.append(f"예측 불가 판정: {_unfReason}")

    # ── 스키마 보장: sourceWeights 합이 1.0 ──
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

    # ── 가정 설명 (정규화된 가중치 기준) ──
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

    # ── AI 컨텍스트 (Tier 2 브릿지) ──
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

    # 불확실성 플래그
    if lifecycle == "transition":
        aiContext["uncertainty_flags"].append("전환기 기업 — 과거 추세 신뢰도 낮음")
    if roicTsGap is not None and abs(roicTsGap) > 10:
        aiContext["uncertainty_flags"].append(f"ROIC-시계열 괴리 {roicTsGap:+.1f}%p")
    if conTsGap is not None and abs(conTsGap) > 15:
        aiContext["uncertainty_flags"].append(f"컨센서스-시계열 괴리 {conTsGap:+.1f}%p")
    if not consensusProj:
        aiContext["uncertainty_flags"].append("컨센서스 데이터 없음")

    # 구조변화 컨텍스트 (forecastCalcs.py dead code 활성화)
    if _sb:
        aiContext["structural_break"] = {
            "stability": _sb.get("overallStability", "stable"),
            "revenue_break": any(m.get("hasBreak") for m in _sb.get("metrics", []) if m.get("name") == "revenue"),
            "n_breaks": sum(1 for m in _sb.get("metrics", []) if m.get("hasBreak")),
        }
        if _sb.get("overallStability") in ("volatile", "transitioning"):
            aiContext["uncertainty_flags"].append(f"구조변화 감지 ({_sb['overallStability']}) — 과거 추세 신뢰도 제한")

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
