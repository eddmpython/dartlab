"""주요 제품 및 서비스 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import selectReport
from dartlab.providers.dart.docs.finance.productService.parser import (
    detectUnit,
    parseProductService,
)
from dartlab.providers.dart.docs.finance.productService.types import ProductServiceResult


def productService(stockCode: str) -> ProductServiceResult | None:
    """주요 제품 및 서비스 분석."""
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
            if "주요 제품" in title or "주요 서비스" in title:
                content = row.get("section_content", "") or ""
                if len(content) < 50:
                    continue

                unit = detectUnit(content)
                products = parseProductService(content)

                if not products:
                    if "없습니다" in content[:500] or len(content) < 200:
                        return ProductServiceResult(
                            corpName=corpName,
                            nYears=1,
                            unit=unit,
                            noData=True,
                        )
                    continue

                productDf = pl.DataFrame(
                    {
                        "label": [p["label"] for p in products],
                        "amount": [p.get("amount") for p in products],
                        "ratio": [p.get("ratio") for p in products],
                    },
                    schema={
                        "label": pl.Utf8,
                        "amount": pl.Int64,
                        "ratio": pl.Float64,
                    },
                )

                return ProductServiceResult(
                    corpName=corpName,
                    nYears=1,
                    unit=unit,
                    products=products,
                    noData=False,
                    productDf=productDf,
                )

    return None
