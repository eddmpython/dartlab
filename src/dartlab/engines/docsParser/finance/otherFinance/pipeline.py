"""기타 재무에 관한 사항 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.docsParser.finance.otherFinance.parser import (
    parseBadDebtProvision,
    parseInventory,
)
from dartlab.engines.docsParser.finance.otherFinance.types import OtherFinanceResult


def otherFinance(stockCode: str) -> OtherFinanceResult | None:
    """기타 재무에 관한 사항 분석."""
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
            if "기타 재무" in title or ("기타" in title and "재무" in title):
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                badDebt = parseBadDebtProvision(content)
                inventory = parseInventory(content)

                if not badDebt and not inventory:
                    if "해당사항" in content[:500] or "없습니다" in content[:500] or "참조" in content[:300]:
                        return OtherFinanceResult(corpName=corpName, nYears=1, noData=True)
                    continue

                badDebtDf = None
                if badDebt:
                    badDebtDf = pl.DataFrame(badDebt)

                inventoryDf = None
                if inventory:
                    inventoryDf = pl.DataFrame(inventory)

                return OtherFinanceResult(
                    corpName=corpName,
                    nYears=1,
                    badDebt=badDebt,
                    inventory=inventory,
                    badDebtDf=badDebtDf,
                    inventoryDf=inventoryDf,
                )
    return None
