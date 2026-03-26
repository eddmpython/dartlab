"""섹터별 특화 KPI 레지스트리."""

from __future__ import annotations

import logging

from dartlab.analysis.comparative.sector.types import Sector
from dartlab.analysis.financial.research.types import SectorKpi, SectorKpis

_log = logging.getLogger(__name__)


def _extractFromRatios(ratios: object, attr: str) -> float | None:
    """RatioResult에서 속성 추출."""
    if ratios is None:
        return None
    return getattr(ratios, attr, None)


def _extractFromSeries(
    aSeries: dict, sjDiv: str, snakeId: str, denomSjDiv: str | None = None, denomSnakeId: str | None = None
) -> float | None:
    """시계열에서 최신값 또는 비율 추출."""
    vals = aSeries.get(sjDiv, {}).get(snakeId, [])
    num = None
    for v in reversed(vals):
        if v is not None:
            num = v
            break
    if num is None:
        return None
    if denomSjDiv is None:
        return num
    denomVals = aSeries.get(denomSjDiv, {}).get(denomSnakeId or "", [])
    denom = None
    for v in reversed(denomVals):
        if v is not None:
            denom = v
            break
    if denom is None or denom == 0:
        return None
    return num / denom


# ── 섹터별 KPI 정의 ──

_FINANCIALS_KPIS = [
    ("interestMargin", "순이자마진", "IS", "interest_income", "BS", "total_assets", "%"),
    ("costToIncome", "판관비율", "IS", "selling_and_admin_expense", "IS", "operating_revenue", "%"),
]

_HEALTHCARE_KPIS = [
    ("rndIntensity", "R&D/매출", "IS", "research_and_development_expense", "IS", "sales", "%"),
]

_IT_KPIS = [
    ("rndIntensity", "R&D/매출", "IS", "research_and_development_expense", "IS", "sales", "%"),
]


def _buildKpisFromDefs(
    defs: list[tuple[str, str, str, str, str | None, str | None, str]],
    aSeries: dict,
    benchmarks: dict[str, float],
) -> list[SectorKpi]:
    """KPI 정의 → SectorKpi 리스트."""
    kpis: list[SectorKpi] = []
    for name, label, numSj, numId, denomSj, denomId, unit in defs:
        value = _extractFromSeries(aSeries, numSj, numId, denomSj, denomId)
        if value is not None and unit == "%":
            value = round(value * 100, 2)
        bench = benchmarks.get(name)
        assessment = ""
        if value is not None and bench is not None:
            if value > bench * 1.1:
                assessment = "good"
            elif value < bench * 0.9:
                assessment = "bad"
            else:
                assessment = "neutral"
        kpis.append(
            SectorKpi(
                name=name,
                label=label,
                value=round(value, 2) if value is not None else None,
                benchmark=bench,
                unit=unit,
                assessment=assessment,
            )
        )
    return kpis


# ── 섹터 벤치마크 (대략적 시장 평균) ──

_BENCHMARKS: dict[str, dict[str, float]] = {
    "FINANCIALS": {"interestMargin": 1.5, "costToIncome": 50.0},
    "HEALTHCARE": {"rndIntensity": 10.0},
    "IT": {"rndIntensity": 8.0},
}

_SECTOR_DEFS: dict[str, list] = {
    "FINANCIALS": _FINANCIALS_KPIS,
    "HEALTHCARE": _HEALTHCARE_KPIS,
    "IT": _IT_KPIS,
}


def calcSectorKpis(
    sector: Sector | None,
    aSeries: dict[str, dict[str, list[float | None]]],
    ratios: object = None,
) -> SectorKpis | None:
    """섹터별 특화 KPI 계산."""
    if sector is None or sector == Sector.UNKNOWN:
        return None

    sectorKey = sector.name
    defs = _SECTOR_DEFS.get(sectorKey)
    if not defs:
        return None

    benchmarks = _BENCHMARKS.get(sectorKey, {})
    kpis = _buildKpisFromDefs(defs, aSeries, benchmarks)

    if not kpis:
        return None

    return SectorKpis(sectorName=sector.value, kpis=kpis)
