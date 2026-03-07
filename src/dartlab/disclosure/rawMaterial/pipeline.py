"""원재료 및 생산설비 데이터 추출 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import loadData, extractCorpName
from dartlab.core.reportSelector import selectReport, extractReportYear
from dartlab.disclosure.rawMaterial.parser import (
    parseCapex,
    parseEquipment,
    parseRawMaterials,
)
from dartlab.disclosure.rawMaterial.types import (
    CapexItem,
    Equipment,
    RawMaterial,
    RawMaterialResult,
)


def rawMaterial(stockCode: str) -> RawMaterialResult | None:
    """사업보고서에서 원재료 및 생산설비 현황 추출.

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
    report = selectReport(df, years[0], reportKind="annual")
    if report is None:
        return None

    reportYear = extractReportYear(report["report_type"][0])

    sections = report.filter(
        pl.col("section_title").str.contains("원재료")
        | pl.col("section_title").str.contains("생산설비")
    )

    if sections.height == 0:
        return None

    rawResult = eqResult = capResult = None
    for i in range(sections.height):
        content = sections["section_content"][i]
        if rawResult is None:
            rawResult = parseRawMaterials(content)
        if eqResult is None:
            eqResult = parseEquipment(content)
        if capResult is None:
            capResult = parseCapex(content)

    if rawResult is None and eqResult is None and capResult is None:
        return None

    materials = [
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

    equipment = None
    if eqResult:
        equipment = Equipment(**{
            k: eqResult.get(k)
            for k in Equipment.__dataclass_fields__
            if k in eqResult
        })

    capexItems = [
        CapexItem(segment=r["segment"], amount=r["amount"])
        for r in (capResult or [])
    ]

    return RawMaterialResult(
        corpName=corpName,
        year=reportYear,
        materials=materials,
        equipment=equipment,
        capexItems=capexItems,
    )


