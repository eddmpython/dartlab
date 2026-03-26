"""주석 세부항목 파이프라인."""

import re

import polars as pl

from dartlab.core.dataLoader import PERIOD_KINDS, extractCorpName, loadData
from dartlab.core.notesExtractor import extractNotesContent, findNumberedSection
from dartlab.core.reportSelector import selectReport
from dartlab.core.tableParser import detectUnit, parseAmount, parseNotesTable
from dartlab.providers.dart.docs.finance.notesDetail.types import (
    NOTES_KEYWORDS,
    NotesDetailResult,
    NotesItem,
    NotesPeriod,
)


def notesDetail(
    stockCode: str,
    keyword: str,
    period: str = "y",
) -> NotesDetailResult | None:
    """주석 세부항목 테이블 추출.

    Args:
        stockCode: 종목코드 (6자리)
        keyword: 주석 키워드 (NOTES_KEYWORDS 참조, 23개 지원)
        period: "y" (연간) | "q" (분기) | "h" (반기)

    Returns:
        NotesDetailResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    keywords = NOTES_KEYWORDS.get(keyword, [keyword])
    kinds = PERIOD_KINDS.get(period, PERIOD_KINDS["y"])
    years = sorted(df["year"].unique().to_list(), reverse=True)

    allTables: dict[str, list[NotesPeriod]] = {}
    unitByYear: dict[str, float] = {}
    latestUnit = 1.0

    for year in years:
        for kind in kinds:
            report = selectReport(df, year, reportKind=kind)
            if report is None:
                continue

            contents = extractNotesContent(report)
            if not contents:
                continue

            section = None
            for kw in keywords:
                section = findNumberedSection(contents, kw)
                if section is not None:
                    break
            if section is None:
                continue

            parsed = parseNotesTable(section)
            if not parsed:
                continue

            unit = detectUnit(section)
            unitByYear[year] = unit
            if not allTables:
                latestUnit = unit

            periods = []
            for block in parsed:
                items = [NotesItem(name=it["name"], values=it["values"]) for it in block["items"]]
                periods.append(
                    NotesPeriod(
                        pattern=block["pattern"],
                        period=block["period"],
                        headers=block["headers"],
                        items=items,
                    )
                )

            if periods:
                allTables[year] = periods
            break

    if not allTables:
        return None

    tableDf = _buildTableDf(allTables, unitByYear)

    return NotesDetailResult(
        corpName=corpName,
        keyword=keyword,
        nYears=len(allTables),
        unit=latestUnit,
        tables=allTables,
        tableDf=tableDf,
    )


def _normalizeName(name: str) -> str:
    """항목명 정규화. 한글 사이 공백 제거."""
    return re.sub(r"(?<=[\uAC00-\uD7A3])\s+(?=[\uAC00-\uD7A3])", "", name.strip())


def _pickValue(values: list[str]) -> str:
    """값 리스트에서 대표값 선택. 마지막 유효 숫자를 사용."""
    for v in reversed(values):
        if v and v.strip() and v.strip() not in ("-", ""):
            return v
    return values[0] if values else ""


_CURRENT_PERIOD = re.compile(r"(당기|당기말|당반기|당분기|현재|전체)")


def _isCurrentPeriod(period: str) -> bool:
    """당기 계열 period인지 판정. 전기/전기말은 제외."""
    if re.search(r"(전기|전반기|전분기)", period):
        return False
    return bool(_CURRENT_PERIOD.search(period))


def _buildTableDf(
    allTables: dict[str, list[NotesPeriod]],
    unitByYear: dict[str, float] | None = None,
) -> pl.DataFrame | None:
    """항목별 시계열 DataFrame 생성.

    각 연도에서 당기 블록만 선택하여 연도 컬럼으로 정렬.
    전기 블록은 이전 연도 당기와 중복이므로 제외.
    단위가 다른 연도는 백만원 기준으로 정규화.
    """
    itemData: dict[str, dict[str, str]] = {}
    colOrder: list[str] = []
    colUnit: dict[str, float] = {}

    for year in sorted(allTables.keys(), reverse=True):
        periods = allTables[year]
        # 당기 블록 선택 (없으면 첫 번째 블록 사용)
        currentBlock = None
        for p in periods:
            if _isCurrentPeriod(p.period):
                currentBlock = p
                break
        if currentBlock is None:
            currentBlock = periods[0]

        colName = year
        if colName not in colOrder:
            colOrder.append(colName)
        colUnit[colName] = (unitByYear or {}).get(year, 1.0)

        for item in currentBlock.items:
            normalized = _normalizeName(item.name)
            if normalized not in itemData:
                itemData[normalized] = {}
            if item.values:
                itemData[normalized][colName] = _pickValue(item.values)

    if not itemData:
        return None

    rows = []
    for name, vals in itemData.items():
        row: dict[str, object] = {"항목": name}
        for col in colOrder:
            raw = vals.get(col, "")
            amount = parseAmount(raw)
            if amount is not None:
                unit = colUnit.get(col, 1.0)
                if unit != 1.0:
                    amount = amount * unit
            row[col] = amount
        rows.append(row)

    schema: dict[str, type] = {"항목": pl.Utf8}
    for col in colOrder:
        schema[col] = pl.Float64
    return pl.DataFrame(rows, schema=schema)
