"""유형자산 변동표 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport
from dartlab.providers.dart.docs.finance.tangibleAsset.parser import findMovementTables
from dartlab.providers.dart.docs.finance.tangibleAsset.types import TangibleAssetResult, TangibleMovement


def tangibleAsset(stockCode: str) -> TangibleAssetResult | None:
    """연결재무제표 주석에서 유형자산 변동표 추출.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        TangibleAssetResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    years = sorted(df["year"].unique().to_list(), reverse=True)

    allMovements: dict[str, list[TangibleMovement]] = {}
    allWarnings: list[str] = []
    overallReliability = "high"

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        contents = extractNotesContent(report)
        if not contents:
            continue

        section = findNumberedSection(contents, "유형자산")
        if section is None:
            continue

        results, parserWarnings = findMovementTables(section)
        if not results:
            continue

        movements = []
        yearWarnings = list(parserWarnings)
        yearReliability = "high"

        for parsed in results:
            hasTotal = any("합계" in c or "합 계" in c for c in parsed["categories"])
            catCount = len(parsed["categories"])

            if not hasTotal:
                yearReliability = "low"
                yearWarnings.append("합계 컬럼 없음 — 개별 열 합산값은 취득원가일 수 있음")
            if catCount < 4:
                yearWarnings.append(f"카테고리 {catCount}개 — 축약된 테이블일 수 있음")

            movements.append(
                TangibleMovement(
                    period=parsed["period"],
                    categories=parsed["categories"],
                    rows=parsed["rows"],
                    unit=parsed["unit"],
                )
            )

        if movements:
            allMovements[year] = movements
            if yearReliability == "low":
                overallReliability = "low"
            allWarnings.extend(yearWarnings)

    if not allMovements:
        return None

    warnings = list(dict.fromkeys(allWarnings))

    movementDf = _buildMovementDf(allMovements, years)

    return TangibleAssetResult(
        corpName=corpName,
        nYears=len(allMovements),
        reliability=overallReliability,
        warnings=warnings,
        movements=allMovements,
        movementDf=movementDf,
    )


def _buildMovementDf(
    allMovements: dict[str, list[TangibleMovement]],
    sortedYears: list[str],
) -> pl.DataFrame | None:
    """카테고리별 기초/기말 시계열 DataFrame 생성.

    카테고리 = 행, 연도별 기초/기말 = 열.
    당기 블록의 기초/기말만 사용.
    """
    catData: dict[str, dict[str, float | None]] = {}

    for year in sortedYears:
        movs = allMovements.get(year, [])
        dangki = [m for m in movs if m.period == "당기"]
        if not dangki:
            continue

        mv = dangki[0]
        startRow = next((r for r in mv.rows if r["label"] == "기초"), None)
        endRow = next((r for r in mv.rows if r["label"] == "기말"), None)

        for cat in mv.categories:
            if cat not in catData:
                catData[cat] = {}
            if startRow:
                catData[cat][f"{year}_기초"] = startRow["values"].get(cat)
            if endRow:
                catData[cat][f"{year}_기말"] = endRow["values"].get(cat)

    if not catData:
        return None

    colOrder: list[str] = []
    for year in sortedYears:
        if year in allMovements:
            colOrder.extend([f"{year}_기초", f"{year}_기말"])

    rows = []
    for cat, vals in catData.items():
        row: dict[str, object] = {"카테고리": cat}
        for col in colOrder:
            row[col] = vals.get(col)
        rows.append(row)

    if not rows:
        return None

    schema: dict[str, type] = {"카테고리": pl.Utf8}
    for col in colOrder:
        schema[col] = pl.Float64
    return pl.DataFrame(rows, schema=schema)
