"""연결재무제표 기반 재무제표 추출 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import PERIOD_KINDS, loadData, extractCorpName
from dartlab.core.reportSelector import selectReport, parsePeriodKey
from dartlab.core.tableParser import extractAccounts
from dartlab.finance.statements.extractor import extractConsolidatedContent, splitStatements
from dartlab.finance.statements.types import StatementsResult


def statements(
    stockCode: str,
    ifrsOnly: bool = True,
    period: str = "y",
) -> StatementsResult | None:
    """연결재무제표에서 BS, IS, CF 시계열 DataFrame 추출.

    Args:
        stockCode: 종목코드 (6자리)
        ifrsOnly: True면 K-IFRS 이후(2011~)만
        period: "y" | "q" | "h"

    Returns:
        StatementsResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    kinds = PERIOD_KINDS.get(period, PERIOD_KINDS["y"])
    years = sorted(df["year"].unique().to_list(), reverse=True)

    # 기간별 각 제표 데이터 수집
    bsData: dict[str, tuple[dict, list]] = {}
    isData: dict[str, tuple[dict, list]] = {}
    cfData: dict[str, tuple[dict, list]] = {}

    for year in years:
        for kind in kinds:
            report = selectReport(df, year, reportKind=kind)
            if report is None:
                continue

            content = extractConsolidatedContent(report)
            if content is None:
                continue

            parts = splitStatements(content)

            if period == "y":
                key = year
            else:
                reportType = report["report_type"][0]
                key = parsePeriodKey(reportType)
                if key is None:
                    continue

            if ifrsOnly and int(key[:4]) < 2011:
                continue

            for stKey, stContent, target in [
                ("BS", parts.get("BS"), bsData),
                ("IS", parts.get("PNL"), isData),
                ("CF", parts.get("CF"), cfData),
            ]:
                if stContent is None:
                    continue
                accounts, order = extractAccounts(stContent)
                if accounts:
                    target[key] = (accounts, order)

    if not bsData and not isData and not cfData:
        return None

    allKeys = sorted(set(bsData) | set(isData) | set(cfData), reverse=True)

    return StatementsResult(
        corpName=corpName,
        period=period,
        nYears=len(allKeys),
        BS=_buildDf(allKeys, bsData),
        IS=_buildDf(allKeys, isData),
        CF=_buildDf(allKeys, cfData),
    )


def _buildDf(
    sortedKeys: list[str],
    data: dict[str, tuple[dict, list]],
) -> pl.DataFrame:
    """계정명 직접 매칭 방식으로 DataFrame 생성."""
    nameData: dict[str, dict[str, float | None]] = {}
    accountOrder: list[str] = []

    for key in sortedKeys:
        if key not in data:
            continue
        accounts, order = data[key]
        for name in order:
            if name not in nameData:
                nameData[name] = {}
                accountOrder.append(name)
            amts = accounts[name]
            nameData[name][key] = amts[0] if amts else None

    rows = []
    for name in accountOrder:
        row: dict[str, object] = {"계정명": name}
        for key in sortedKeys:
            row[key] = nameData[name].get(key)
        rows.append(row)

    if not rows:
        return pl.DataFrame()

    schema = {"계정명": pl.Utf8}
    for key in sortedKeys:
        schema[key] = pl.Float64
    return pl.DataFrame(rows, schema=schema)
