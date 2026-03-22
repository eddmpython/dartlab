"""직원 현황 데이터 추출 파이프라인."""

import polars as pl

from dartlab.core.dataLoader import extractCorpName, loadData
from dartlab.core.reportSelector import extractReportYear, selectReport
from dartlab.engines.company.dart.docs.finance.employee.parser import parseEmployeeTable
from dartlab.engines.company.dart.docs.finance.employee.types import EmployeeResult


def employee(stockCode: str) -> EmployeeResult | None:
    """사업보고서에서 직원 현황 시계열 추출.

    Args:
        stockCode: 종목코드 (6자리)

    Returns:
        EmployeeResult 또는 데이터 부족 시 None
    """
    df = loadData(stockCode)
    corpName = extractCorpName(df)

    years = sorted(df["year"].unique().to_list(), reverse=True)

    yearData: dict[int, dict] = {}

    for year in years:
        report = selectReport(df, year, reportKind="annual")
        if report is None:
            continue

        empRows = report.filter(
            pl.col("section_title").str.contains("직원") | pl.col("section_title").str.contains("임원")
        )
        if empRows.height == 0:
            continue

        reportYear = extractReportYear(empRows["report_type"][0])
        if reportYear is None:
            continue

        content = empRows["section_content"][0]
        parsed = parseEmployeeTable(content)

        if not parsed.get("totalEmployees"):
            continue

        # avgSalary 있어야 신뢰할 수 있는 데이터
        if not parsed.get("avgSalary"):
            continue

        if reportYear not in yearData:
            yearData[reportYear] = parsed

    if not yearData:
        return None

    records = []
    for yr in sorted(yearData.keys()):
        d = yearData[yr]
        records.append(
            {
                "year": yr,
                "totalEmployees": d.get("totalEmployees"),
                "avgTenure": d.get("avgTenure"),
                "totalSalary": d.get("totalSalary"),
                "avgSalary": d.get("avgSalary"),
            }
        )

    ts = pl.DataFrame(records)

    return EmployeeResult(
        corpName=corpName,
        nYears=ts.height,
        timeSeries=ts,
    )
