"""원재료 및 생산설비 데이터 추출 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import extractReportYear, selectReport
from dartlab.engines.dart.docs.disclosure.rawMaterial.parser import (
    parseCapex,
    parseEquipment,
    parseRawMaterials,
)
from dartlab.engines.dart.docs.disclosure.rawMaterial.types import (
    CapexItem,
    Equipment,
    RawMaterial,
    RawMaterialResult,
    YearSnapshot,
)


def _parseYear(
    report: pl.DataFrame,
) -> tuple[
    list[dict] | None,
    dict | None,
    list[dict] | None,
]:
    """단일 연도 report에서 원재료/설비/CAPEX 파싱."""
    sections = report.filter(
        pl.col("section_title").str.contains("원재료") | pl.col("section_title").str.contains("생산설비")
    )
    if sections.height == 0:
        return None, None, None

    rawResult = eqResult = capResult = None
    for i in range(sections.height):
        content = sections["section_content"][i]
        if rawResult is None:
            rawResult = parseRawMaterials(content)
        if eqResult is None:
            eqResult = parseEquipment(content)
        if capResult is None:
            capResult = parseCapex(content)

    return rawResult, eqResult, capResult


def _buildMaterials(rawResult: list[dict] | None) -> list[RawMaterial]:
    return [
        RawMaterial(
            segment=r.get("segment"),
            item=r.get("item"),
            usage=r.get("usage"),
            amount=r.get("amount"),
            ratio=r.get("ratio"),
            supplier=r.get("supplier"),
        )
        for r in (rawResult or [])
    ]


def _buildEquipment(eqResult: dict | None) -> Equipment | None:
    if not eqResult:
        return None
    return Equipment(**{k: eqResult.get(k) for k in Equipment.__dataclass_fields__ if k in eqResult})


def _buildCapex(capResult: list[dict] | None) -> list[CapexItem]:
    return [CapexItem(segment=r["segment"], amount=r["amount"]) for r in (capResult or [])]


def rawMaterial(stockCode: str) -> RawMaterialResult | None:
    """사업보고서에서 원재료 및 생산설비 현황 추출 (다년도).

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        RawMaterialResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    years = sorted(df["year"].unique().to_list(), reverse=True)
    if not years:
        return None

    latestYear: int | None = None
    latestMaterials: list[RawMaterial] = []
    latestEquipment: Equipment | None = None
    latestCapex: list[CapexItem] = []
    yearSnapshots: dict[int, YearSnapshot] = {}

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        reportYear = extractReportYear(report["report_type"][0])
        if reportYear is None or reportYear in yearSnapshots:
            continue

        rawResult, eqResult, capResult = _parseYear(report)
        if rawResult is None and eqResult is None and capResult is None:
            continue

        materials = _buildMaterials(rawResult)
        equipment = _buildEquipment(eqResult)
        capexItems = _buildCapex(capResult)

        yearSnapshots[reportYear] = YearSnapshot(
            materials=materials,
            equipment=equipment,
            capexItems=capexItems,
        )

        if latestYear is None:
            latestYear = reportYear
            latestMaterials = materials
            latestEquipment = equipment
            latestCapex = capexItems

    if not yearSnapshots:
        return None

    return RawMaterialResult(
        corpName=corpName,
        year=latestYear,
        nYears=len(yearSnapshots),
        materials=latestMaterials,
        equipment=latestEquipment,
        capexItems=latestCapex,
        yearSnapshots=yearSnapshots,
    )
