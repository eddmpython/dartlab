"""섹터별 재무비율 벤치마크.

016_sectorBenchmark 실험(2026-03-09) 결과 기반.
2508종목 전수조사로 측정한 섹터별 중앙값/사분위수.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from dartlab.engines.analysis.sector.types import Sector


@dataclass
class SectorBenchmark:
    """섹터별 재무비율 중앙값/사분위수."""

    omMedian: float
    omQ1: float
    omQ3: float
    roeMedian: float
    roeQ1: float
    roeQ3: float
    n: int
    # Merton D2D 벤치마크 (실험 085_mertonEngine/004 결과 기반)
    d2dMedian: Optional[float] = None
    d2dQ1: Optional[float] = None
    d2dQ3: Optional[float] = None


BENCHMARKS: dict[Sector, SectorBenchmark] = {
    Sector.IT: SectorBenchmark(
        omMedian=2.7, omQ1=-4.9, omQ3=7.3,
        roeMedian=12.7, roeQ1=-17.5, roeQ3=34.0, n=466,
        d2dMedian=4.0, d2dQ1=2.4, d2dQ3=6.7,
    ),
    Sector.HEALTHCARE: SectorBenchmark(
        omMedian=2.2, omQ1=-19.0, omQ3=10.3,
        roeMedian=0.8, roeQ1=-66.0, roeQ3=27.8, n=259,
        d2dMedian=2.9, d2dQ1=1.7, d2dQ3=6.1,
    ),
    Sector.CONSUMER_DISC: SectorBenchmark(
        omMedian=3.2, omQ1=0.1, omQ3=6.7,
        roeMedian=17.6, roeQ1=-9.1, roeQ3=30.5, n=245,
        d2dMedian=4.3, d2dQ1=2.9, d2dQ3=7.0,
    ),
    Sector.FINANCIALS: SectorBenchmark(
        omMedian=6.9, omQ1=3.2, omQ3=15.6,
        roeMedian=25.2, roeQ1=6.2, roeQ3=43.8, n=63,
        # 금융업: Merton D2D 구조적 왜곡으로 벤치마크 미설정
    ),
    Sector.INDUSTRIALS: SectorBenchmark(
        omMedian=3.5, omQ1=-1.9, omQ3=7.8,
        roeMedian=18.1, roeQ1=-7.8, roeQ3=33.0, n=405,
        d2dMedian=4.1, d2dQ1=2.8, d2dQ3=6.6,
    ),
    Sector.MATERIALS: SectorBenchmark(
        omMedian=3.4, omQ1=-0.6, omQ3=7.3,
        roeMedian=15.3, roeQ1=-11.9, roeQ3=29.4, n=416,
        d2dMedian=3.4, d2dQ1=2.1, d2dQ3=5.3,
    ),
    Sector.ENERGY: SectorBenchmark(
        omMedian=2.1, omQ1=-3.6, omQ3=5.8,
        roeMedian=16.0, roeQ1=-21.2, roeQ3=30.7, n=33,
        d2dMedian=2.9, d2dQ1=1.8, d2dQ3=4.3,
    ),
    Sector.UTILITIES: SectorBenchmark(
        omMedian=2.9, omQ1=1.1, omQ3=4.6,
        roeMedian=21.9, roeQ1=11.9, roeQ3=25.6, n=12,
        d2dMedian=6.0, d2dQ1=4.0, d2dQ3=8.0,
    ),
    Sector.COMMUNICATION: SectorBenchmark(
        omMedian=1.0, omQ1=-6.1, omQ3=7.5,
        roeMedian=-0.3, roeQ1=-55.0, roeQ3=24.2, n=141,
        d2dMedian=3.4, d2dQ1=2.1, d2dQ3=6.6,
    ),
    Sector.CONSUMER_STAPLES: SectorBenchmark(
        omMedian=3.7, omQ1=1.2, omQ3=7.3,
        roeMedian=18.3, roeQ1=0.8, roeQ3=31.8, n=123,
        d2dMedian=5.1, d2dQ1=3.6, d2dQ3=8.3,
    ),
    Sector.REAL_ESTATE: SectorBenchmark(
        omMedian=2.6, omQ1=-5.5, omQ3=6.1,
        roeMedian=11.2, roeQ1=-11.0, roeQ3=30.9, n=4,
        d2dMedian=4.0, d2dQ1=2.8, d2dQ3=6.0,
    ),
}

DEFAULT_BENCHMARK = SectorBenchmark(
    omMedian=3.2,
    omQ1=-2.3,
    omQ3=7.7,
    roeMedian=14.2,
    roeQ1=-16.9,
    roeQ3=31.1,
    n=2167,
)


def getBenchmark(sector: Sector) -> SectorBenchmark:
    """섹터별 벤치마크 반환."""
    return BENCHMARKS.get(sector, DEFAULT_BENCHMARK)


def sectorAdjustment(value: Optional[float], median: float, q1: float, q3: float) -> int:
    """섹터 중앙값 대비 가점/감점 (±1).

    Q3 이상 → +1 (업종 상위)
    Q1 이하 → -1 (업종 하위)
    Q1~Q3 → 0 (업종 평균)
    """
    if value is None:
        return 0
    if value >= q3:
        return 1
    if value <= q1:
        return -1
    return 0
