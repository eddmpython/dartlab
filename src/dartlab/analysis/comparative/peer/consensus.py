"""Peer consensus 매출 예측.

peer 그룹의 매출 성장률 중앙값을 예측 앵커로 사용.
dartlab finance 엔진의 mapper(34,175 매핑)를 통해 매출 커버리지 확보.

실험 근거: 098-009 (MdAE 9.0%, 20%이내 84.7%)
"""

from __future__ import annotations

import logging
import statistics

from dartlab.analysis.comparative.peer.types import ConsensusResult, PeerResult

_log = logging.getLogger(__name__)


def _getAnnualRevenue(stockCode: str) -> dict[str, float] | None:
    """finance 엔진으로 연간 매출 시계열 추출.

    pivot.py의 mapper(34,175 매핑)를 거쳐 sales snakeId로 통합.
    Company 객체 없이 경량 접근.
    """
    from dartlab.providers.dart.finance.pivot import buildTimeseries

    result = buildTimeseries(stockCode)
    if result is None:
        return None

    series, periods = result
    salesVals = series.get("IS", {}).get("sales")
    if not salesVals:
        return None

    # period → 연도 매핑 (연간 사업보고서 = Q4 시점)
    yearRevenue: dict[str, float] = {}
    for i, period in enumerate(periods):
        if i >= len(salesVals) or salesVals[i] is None:
            continue
        # period 형식: "2024-Q4", "2024-Q3" 등
        year = period.split("-")[0]
        quarter = period.split("-")[1] if "-" in period else ""
        # 연간 매출 = Q4 누적 standalone (IS는 이미 standalone 변환됨)
        # standalone이므로 4개 분기를 합산해야 연간
        if year not in yearRevenue:
            yearRevenue[year] = 0.0
        yearRevenue[year] += salesVals[i]

    # 최소 3년 이상
    if len(yearRevenue) < 3:
        return None
    return yearRevenue


def _computeGrowthRates(revMap: dict[str, float]) -> dict[str, float]:
    """연간 매출 → YoY 성장률 (%)."""
    years = sorted(revMap.keys())
    growth = {}
    for i in range(1, len(years)):
        prev = revMap[years[i - 1]]
        curr = revMap[years[i]]
        if prev != 0:
            growth[years[i]] = ((curr - prev) / abs(prev)) * 100
    return growth


def consensus(
    peerResult: PeerResult,
    *,
    targetYear: str | None = None,
    maxOutlier: float = 200.0,
) -> ConsensusResult:
    """peer 그룹의 매출 성장률 중앙값으로 예측.

    Args:
        peerResult: discover()의 결과
        targetYear: 예측 기준 연도 (None이면 가장 최근)
        maxOutlier: 이상치 필터 기준 (절대값 %)
    """
    if not peerResult.peers:
        return ConsensusResult(
            stockCode=peerResult.stockCode,
            name=peerResult.name,
        )

    peerGrowths: dict[str, float] = {}

    for peer in peerResult.peers:
        try:
            rev = _getAnnualRevenue(peer.stockCode)
        except (RuntimeError, FileNotFoundError, OSError):
            continue
        if rev is None:
            continue
        growth = _computeGrowthRates(rev)
        if not growth:
            continue

        if targetYear and targetYear in growth:
            g = growth[targetYear]
        else:
            # 가장 최근 연도
            latestYear = max(growth.keys())
            g = growth[latestYear]

        if abs(g) <= maxOutlier:
            peerGrowths[peer.stockCode] = round(g, 2)

    if not peerGrowths:
        return ConsensusResult(
            stockCode=peerResult.stockCode,
            name=peerResult.name,
        )

    predicted = statistics.median(list(peerGrowths.values()))

    return ConsensusResult(
        stockCode=peerResult.stockCode,
        name=peerResult.name,
        predictedGrowth=round(predicted, 2),
        peerGrowths=peerGrowths,
        nPeers=len(peerGrowths),
        method="median",
    )
