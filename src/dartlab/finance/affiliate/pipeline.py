"""관계기업/공동기업 투자 분석 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import PERIOD_KINDS, loadData, extractCorpName
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport
from dartlab.finance.affiliate.extractor import parseTableRows
from dartlab.finance.affiliate.parser import (
    extractMovements,
    extractProfiles,
    extractTransposedMovements,
    extractTransposedProfiles,
)
from dartlab.finance.affiliate.types import (
    AffiliateMovement,
    AffiliateProfile,
    AffiliatesResult,
)


_AFFILIATE_KEYWORDS = ["관계기업", "지분법", "공동기업"]


def affiliates(
    stockCode: str,
    period: str = "y",
) -> AffiliatesResult | None:
    """연결재무제표 주석에서 관계기업/공동기업 투자 데이터 추출.

    Args:
        stockCode: 종목코드 (6자리)
        period: "y" (연간) | "q" (분기) | "h" (반기)

    Returns:
        AffiliatesResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    kinds = PERIOD_KINDS.get(period, PERIOD_KINDS["y"])
    years = sorted(df["year"].unique().to_list(), reverse=True)

    allProfiles: dict[str, list[AffiliateProfile]] = {}
    allMovements: dict[str, list[AffiliateMovement]] = {}

    for year in years:
        for kind in kinds:
            report = selectReport(df, year, reportKind=kind)
            if report is None:
                continue

            contents = extractNotesContent(report)
            if not contents:
                continue

            section = None
            for kw in _AFFILIATE_KEYWORDS:
                section = findNumberedSection(contents, kw)
                if section is not None:
                    break
            if section is None:
                continue

            rows = parseTableRows(section)
            if not rows:
                continue

            # 프로필: 일반 + 횡전개, 더 많은 쪽 채택
            profiles = extractProfiles(rows)
            tProfiles = extractTransposedProfiles(rows)
            if len(tProfiles) > len(profiles):
                profiles = tProfiles

            # 변동: 일반 + 횡전개, 더 많은 쪽 채택
            movements = extractMovements(rows)
            tMovements = extractTransposedMovements(rows)
            if len(tMovements) > len(movements):
                movements = tMovements

            if profiles:
                allProfiles[year] = profiles
            if movements:
                allMovements[year] = movements
            break  # 해당 연도는 첫 번째 매칭 보고서 사용

    if not allProfiles and not allMovements:
        return None

    nYears = len(set(allProfiles.keys()) | set(allMovements.keys()))
    movementDf = _buildMovementDf(allMovements, years)

    return AffiliatesResult(
        corpName=corpName,
        nYears=nYears,
        period=period,
        profiles=allProfiles,
        movements=allMovements,
        movementDf=movementDf,
    )


def _buildMovementDf(
    allMovements: dict[str, list[AffiliateMovement]],
    sortedYears: list[str],
) -> pl.DataFrame | None:
    """기업별 변동 시계열 DataFrame 생성.

    기업명 = 행, 연도별 기초/기말/지분법손익 = 열.
    """
    companyData: dict[str, dict[str, float | None]] = {}

    for year in sortedYears:
        movs = allMovements.get(year, [])
        for mv in movs:
            if mv.name not in companyData:
                companyData[mv.name] = {}
            companyData[mv.name][f"{year}_기초"] = mv.opening
            companyData[mv.name][f"{year}_기말"] = mv.closing
            companyData[mv.name][f"{year}_지분법손익"] = mv.equityIncome

    if not companyData:
        return None

    # 연도별 열 순서
    colOrder: list[str] = []
    for year in sortedYears:
        if year in allMovements:
            colOrder.extend([f"{year}_기초", f"{year}_기말", f"{year}_지분법손익"])

    rows = []
    for name, vals in companyData.items():
        row: dict[str, object] = {"기업명": name}
        for col in colOrder:
            row[col] = vals.get(col)
        rows.append(row)

    if not rows:
        return None

    schema: dict[str, type] = {"기업명": pl.Utf8}
    for col in colOrder:
        schema[col] = pl.Float64
    return pl.DataFrame(rows, schema=schema)
