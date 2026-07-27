"""revenueForecast 앙상블 산술 . 기준점 확정 + 소스별 성장률 + 예측 경로.

`_revenueForecastCore.forecastRevenue` 에서 분리. 여기 있는 함수는 전부 순수
산술이라 외부 수집·모듈 전역에 손대지 않는다 (소스 수집과 결과 조립은 core 가
그대로 들고 있다). 누산 순서가 부동소수점 결과에 직결되므로 식 순서는 옮길 때도
바꾸지 않았다.

비공개 (_) 헬퍼 10 종:
- 기준점: _consensusBaseline · _resolveBaseRevenue
- 성장률 시계열: _timeseriesGrowthRates · _consensusGrowthRates · _roicTimeseriesGap
- 경로: _overrideProjection · _yearBlendedGrowth · _ensembleProjection ·
  _padProjected · _pathGrowthRates
"""

from __future__ import annotations

from dartlab.analysis.forecast._revenueForecastTypes import BacklogSignal

# ══════════════════════════════════════
# 기준점 + 소스별 성장률 시계열
# ══════════════════════════════════════


def _consensusBaseline(
    consensusItems: list[tuple[int, float, str]],
) -> tuple[dict[int, float], list[float], int, float | None]:
    """컨센서스 원자료를 원 단위로 펼쳐 estimate 와 최신 actual 로 가른다.

    컨센서스는 actual 과 estimate 가 한 list 에 섞여 오는데, 앙상블은 estimate 만
    쓰고 기준 매출은 actual 만 쓴다. 이 갈래질이 본체에 흩어져 있으면 어느 쪽이
    어디에 쓰이는지 추적이 어려워 한 자리에서 갈라 낸다.

    baseYear 는 현재 호출부에서 소비하지 않지만 산출 자체는 원본 그대로 둔다.
    """
    consensusByYear: dict[int, tuple[float, str]] = {}  # year → (revenue_원, source)
    if consensusItems:
        for fy, rev, src in consensusItems:
            if rev > 0:
                consensusByYear[fy] = (rev * 1e8, src)  # 억원 → 원

    # 컨센서스 estimate만 추출
    consensusProj: dict[int, float] = {}
    consensusRevenue: list[float] = []
    for fy, (revWon, src) in consensusByYear.items():
        if src.endswith("_consensus"):
            consensusProj[fy] = revWon
            consensusRevenue.append(revWon)

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

    return consensusProj, consensusRevenue, baseYear, lastActualRevenue


def _resolveBaseRevenue(
    lastRevenue: float | None,
    lastActualRevenue: float | None,
    ov: dict,
    lifecycle: str,
    tsResult: object,
    tsAvailable: bool,
    warnings: list[str],
) -> float | None:
    """앙상블 출발점이 될 기준 매출 확정 (컨센서스 actual > override > mid-cycle).

    기준 매출은 세 갈래에서 덮어써진다. 우선순위가 코드 순서에 숨어 있으면
    나중에 한 갈래만 추가하다 순서를 깨기 쉬워, 세 갈래를 한 함수에 모은다.
    warnings 는 호출부 list 를 그대로 받아 덮어쓴 사실을 남긴다.
    """
    # lastRevenue를 컨센서스 actual과 동기화 (더 신뢰할 수 있으므로)
    if lastActualRevenue:
        lastRevenue = lastActualRevenue

    # override: baseRevenue
    if "baseRevenue" in ov:
        lastRevenue = ov["baseRevenue"]
        warnings.append(f"baseRevenue override: {lastRevenue / 1e12:.1f}조")

    # mid-cycle 정규화 (사이클 기업 자동, override 없을 때)
    if "baseRevenue" not in ov and lifecycle in ("cyclical", "mature_cyclical"):
        historicals = [v for v in (tsResult.historical if tsAvailable and tsResult else []) if v and v > 0]
        if len(historicals) >= 3:
            midCycleRevenue = sum(historicals[-5:]) / len(historicals[-5:])
            if lastRevenue and abs(lastRevenue - midCycleRevenue) / midCycleRevenue > 0.15:
                lastRevenue = midCycleRevenue
                warnings.append(f"사이클 기업 → mid-cycle 매출 {midCycleRevenue / 1e12:.1f}조 적용")

    return lastRevenue


def _timeseriesGrowthRates(tsResult: object, tsAvailable: bool) -> list[float]:
    """시계열 projected 의 YoY 성장률 (분기 데이터라 자체 기준 비교)."""
    tsGrowthRates: list[float] = []
    if tsAvailable and tsResult.projected:
        prev = tsResult.historical[-1] if tsResult.historical and tsResult.historical[-1] else None
        for p in tsResult.projected:
            if prev and prev > 0 and p > 0:
                tsGrowthRates.append((p / prev - 1) * 100)
            else:
                tsGrowthRates.append(tsResult.growthRate)
            prev = p
    return tsGrowthRates


def _consensusGrowthRates(consensusProj: dict[int, float], lastRevenue: float | None) -> list[float]:
    """컨센서스 연도별 성장률 (첫 해만 기준 매출 대비, 이후는 직전 추정치 대비)."""
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
    return conGrowthRates


def _roicTimeseriesGap(
    roicGrowthRate: float | None,
    tsGrowthRates: list[float],
    warnings: list[str],
) -> float | None:
    """ROIC 내재 성장률과 시계열 성장률의 괴리 (%p). 10%p 초과면 경고 동반."""
    if roicGrowthRate is None or not tsGrowthRates:
        return None

    avgTsG = sum(tsGrowthRates) / len(tsGrowthRates)
    roicTsGap = roicGrowthRate - avgTsG
    if abs(roicTsGap) > 10:
        warnings.append(
            f"ROIC 내재 성장률({roicGrowthRate:.1f}%)과 시계열 성장률({avgTsG:.1f}%) 괴리 {roicTsGap:+.1f}%p"
        )
    return roicTsGap


# ══════════════════════════════════════
# 예측 경로 산출
# ══════════════════════════════════════


def _overrideProjection(ovGrowth: list[float], lastRevenue: float | None, horizon: int) -> list[float]:
    """override 성장률로 직접 복리 전개한 경로 (앙상블 자체를 대체한다)."""
    projected: list[float] = []
    prevR = lastRevenue or 0
    for i in range(horizon):
        g = ovGrowth[i] if i < len(ovGrowth) else (ovGrowth[-1] if ovGrowth else 3.0)
        prevR = prevR * (1 + g / 100)
        projected.append(prevR)
    return projected


def _yearBlendedGrowth(
    yrOffset: int,
    weights: dict[str, float],
    tsGrowthRates: list[float],
    conGrowthRates: list[float],
    roicG: float,
    segGrowthRates: list[float],
    backlogSignal: BacklogSignal | None,
) -> float:
    """해당 연차의 소스 가중 성장률 (%).

    소스가 늘 때마다 앙상블 루프가 부풀던 자리다. 연차 1 개의 가중합만 책임지게
    잘라 두면 소스 추가가 루프 구조를 건드리지 않는다. 누산 순서는 부동소수점
    결과에 직결되므로 바꾸지 않는다.
    """
    # 시계열 성장률
    tsG = (
        tsGrowthRates[yrOffset - 1] if yrOffset <= len(tsGrowthRates) else (tsGrowthRates[-1] if tsGrowthRates else 0.0)
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

    return blendedGrowth


def _ensembleProjection(
    lastRevenue: float | None,
    horizon: int,
    weights: dict[str, float],
    tsGrowthRates: list[float],
    conGrowthRates: list[float],
    roicG: float,
    segGrowthRates: list[float],
    backlogSignal: BacklogSignal | None,
) -> list[float]:
    """가중 성장률을 복리로 굴린 앙상블 경로. 기준 매출이 0 이하면 즉시 멈춘다."""
    projected: list[float] = []
    prevRevenue = lastRevenue or 0
    for yrOffset in range(1, horizon + 1):
        if prevRevenue <= 0:
            break

        blendedGrowth = _yearBlendedGrowth(
            yrOffset,
            weights,
            tsGrowthRates,
            conGrowthRates,
            roicG,
            segGrowthRates,
            backlogSignal,
        )

        projVal = prevRevenue * (1 + blendedGrowth / 100)
        projected.append(projVal)
        prevRevenue = projVal

    return projected


def _padProjected(projected: list[float], horizon: int, lastRevenue: float | None) -> list[float]:
    """스키마 보장: projected 길이를 horizon 까지 채운다 (마지막 값 → 기준 매출 → 0)."""
    while len(projected) < horizon:
        if projected:
            projected.append(projected[-1])
        elif lastRevenue and lastRevenue > 0:
            projected.append(lastRevenue)
        else:
            projected.append(0.0)
    return projected


def _pathGrowthRates(projected: list[float], lastRevenue: float | None, horizon: int) -> list[float]:
    """확정된 경로에서 YoY 성장률 재산출 (첫 해만 기준 매출 대비)."""
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
    return growthRates


__all__ = [
    "_consensusBaseline",
    "_consensusGrowthRates",
    "_ensembleProjection",
    "_overrideProjection",
    "_padProjected",
    "_pathGrowthRates",
    "_resolveBaseRevenue",
    "_roicTimeseriesGap",
    "_timeseriesGrowthRates",
    "_yearBlendedGrowth",
]
