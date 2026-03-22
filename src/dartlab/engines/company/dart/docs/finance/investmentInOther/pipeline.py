"""타법인출자 현황 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.company.dart.docs.finance.investmentInOther.parser import parseInvestments
from dartlab.engines.company.dart.docs.finance.investmentInOther.types import InvestmentInOtherResult


def _buildInvestmentDf(rows: list[dict], headers: list[str] | None = None) -> pl.DataFrame | None:
    if not rows:
        return None
    maxVals = max(len(r["values"]) for r in rows)
    data: dict[str, list] = {"name": [r["name"] for r in rows]}
    for i in range(maxVals):
        colName = headers[i] if headers and i < len(headers) else f"v{i + 1}"
        if colName in data:
            colName = f"{colName}_{i + 1}"
        data[colName] = [r["values"][i] if i < len(r["values"]) else None for r in rows]
    return pl.DataFrame(data)


def investmentInOther(stockCode: str) -> InvestmentInOtherResult | None:
    """타법인출자 현황 분석."""
    try:
        df = loadData(stockCode)
    except FileNotFoundError:
        return None

    corpName = extractCorpName(df)
    years = sorted(df["year"].unique().to_list(), reverse=True)

    for year in years[:2]:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        for row in report.iter_rows(named=True):
            title = row.get("section_title", "") or ""
            if "타법인" in title and ("출자" in title or "투자" in title):
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                investments, headers = parseInvestments(content)
                if investments:
                    return InvestmentInOtherResult(
                        corpName=corpName,
                        nYears=1,
                        investments=investments,
                        investmentDf=_buildInvestmentDf(investments, headers),
                    )

                if "해당사항" in content[:500] or "없습니다" in content[:500]:
                    return InvestmentInOtherResult(corpName=corpName, nYears=1, noData=True)
    return None
