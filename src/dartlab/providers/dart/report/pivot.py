"""apiType별 시계열 피벗 함수."""

from __future__ import annotations

from typing import Optional

import polars as pl

from dartlab.providers.dart.report.extract import extractAnnual, extractClean
from dartlab.providers.dart.report.types import (
    AuditResult,
    DividendResult,
    EmployeeResult,
    ExecutiveResult,
    MajorHolderResult,
)


def pivotDividend(stockCode: str, *, base_df: pl.DataFrame | None = None) -> DividendResult | None:
    """배당 시계열 (Q4 사업보고서 기준, 보통주)."""
    df = extractAnnual(stockCode, "dividend", quarterNum=4, base_df=base_df)
    if df is None:
        return None

    common = df.filter(pl.col("stock_knd") == "보통주")
    if common.is_empty():
        common = df

    years = sorted(common["year"].unique().to_list())

    def _pickSeries(seName: str) -> list[Optional[float]]:
        rows = common.filter(pl.col("se").str.contains(seName))
        valMap: dict[int, Optional[float]] = {}
        for row in rows.iter_rows(named=True):
            valMap[row["year"]] = row.get("thstrm")
        return [valMap.get(y) for y in years]

    return DividendResult(
        years=years,
        dps=_pickSeries("현금배당금"),
        dividendYield=_pickSeries("현금배당수익률"),
        stockDividend=_pickSeries("주식배당"),
        stockDividendYield=_pickSeries("주식배당수익률"),
        df=common,
    )


def pivotEmployee(stockCode: str, *, base_df: pl.DataFrame | None = None) -> EmployeeResult | None:
    """직원현황 시계열 (Q2 반기보고서 기준)."""
    df = extractAnnual(stockCode, "employee", quarterNum=2, base_df=base_df)
    if df is None:
        return None

    totals = df.filter((pl.col("sexdstn").is_null()) | (pl.col("sexdstn") == "계") | (pl.col("sexdstn") == "합계"))

    if totals.is_empty():
        totals = (
            df.group_by(["year", "quarterNum"])
            .agg(
                [
                    pl.col("sm").sum().alias("sm"),
                    pl.col("fyer_salary_totamt").sum().alias("fyer_salary_totamt"),
                    pl.col("jan_salary_am").mean().alias("jan_salary_am"),
                ]
            )
            .sort("year")
        )

    years = sorted(totals["year"].unique().to_list())
    totalEmp: list[Optional[float]] = []
    avgSalary: list[Optional[float]] = []
    totalSalary: list[Optional[float]] = []

    for y in years:
        row = totals.filter(pl.col("year") == y)
        if row.is_empty():
            totalEmp.append(None)
            avgSalary.append(None)
            totalSalary.append(None)
        else:
            r = row.row(0, named=True)
            totalEmp.append(r.get("sm"))
            avgSalary.append(r.get("jan_salary_am"))
            totalSalary.append(r.get("fyer_salary_totamt"))

    return EmployeeResult(
        years=years,
        totalEmployee=totalEmp,
        avgMonthlySalary=avgSalary,
        totalAnnualSalary=totalSalary,
        df=df,
    )


def pivotMajorHolder(stockCode: str, *, base_df: pl.DataFrame | None = None) -> MajorHolderResult | None:
    """최대주주현황 시계열 (Q2 반기보고서 기준, 보통주)."""
    df = extractAnnual(stockCode, "majorHolder", quarterNum=2, base_df=base_df)
    if df is None:
        return None

    common = df.filter(pl.col("stock_knd") == "보통주")
    if common.is_empty():
        common = df

    topRows = common.filter(pl.col("nm") == "계")
    if topRows.is_empty():
        topRows = common.filter(pl.col("rm") == "계")

    if topRows.is_empty():
        topRows = (
            common.filter(pl.col("nm") != "계")
            .group_by(["year", "quarterNum"])
            .agg(pl.col("trmend_posesn_stock_qota_rt").sum())
            .sort("year")
        )

    years = sorted(topRows["year"].unique().to_list())
    ratio: list[Optional[float]] = []
    for y in years:
        row = topRows.filter(pl.col("year") == y)
        if row.is_empty():
            ratio.append(None)
        else:
            ratio.append(row.row(0, named=True).get("trmend_posesn_stock_qota_rt"))

    latestYear = years[-1] if years else None
    latestHolders: list[dict] = []
    if latestYear is not None:
        individuals = common.filter(
            (pl.col("year") == latestYear) & (pl.col("nm") != "계") & pl.col("nm").is_not_null()
        ).sort("trmend_posesn_stock_qota_rt", descending=True)

        for row in individuals.head(10).iter_rows(named=True):
            latestHolders.append(
                {
                    "name": row["nm"],
                    "relate": row.get("relate"),
                    "ratio": row.get("trmend_posesn_stock_qota_rt"),
                    "shares": row.get("trmend_posesn_stock_co"),
                }
            )

    return MajorHolderResult(
        years=years,
        totalShareRatio=ratio,
        latestHolders=latestHolders,
        df=common,
    )


def pivotExecutive(stockCode: str, *, base_df: pl.DataFrame | None = None) -> ExecutiveResult | None:
    """임원현황 (최신 분기 기준)."""
    df = extractClean(stockCode, "executive", base_df=base_df)
    if df is None:
        return None

    latestYear = df["year"].max()
    latestQ = df.filter(pl.col("year") == latestYear)["quarterNum"].max()
    latest = df.filter((pl.col("year") == latestYear) & (pl.col("quarterNum") == latestQ))

    if latest.is_empty():
        return None

    total = latest.height
    registered = latest.filter(pl.col("rgist_exctv_at") == "사내이사").height
    outside = latest.filter(pl.col("rgist_exctv_at") == "사외이사").height

    return ExecutiveResult(
        df=latest,
        totalCount=total,
        registeredCount=registered,
        outsideCount=outside,
    )


def pivotAudit(stockCode: str, *, base_df: pl.DataFrame | None = None) -> AuditResult | None:
    """감사의견 시계열 (Q4 사업보고서 기준)."""
    df = extractAnnual(stockCode, "auditOpinion", quarterNum=4, base_df=base_df)
    if df is None:
        return None

    yearly = df.unique(["year"], keep="last").sort("year")
    years = yearly["year"].to_list()
    opinions: list[Optional[str]] = []
    auditors: list[Optional[str]] = []

    for row in yearly.iter_rows(named=True):
        opinions.append(row.get("adt_opinion"))
        auditors.append(row.get("adtor"))

    return AuditResult(
        years=years,
        opinions=opinions,
        auditors=auditors,
        df=df,
    )
