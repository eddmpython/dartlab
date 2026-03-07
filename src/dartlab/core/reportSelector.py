import re

import polars as pl


def selectReport(df: pl.DataFrame, year: str, reportKind: str = "annual") -> pl.DataFrame | None:
    """해당 연도+기간 보고서 선택. 원본 우선, 없으면 기재정정/첨부 중 가장 나중 접수.

    Args:
        df: 전체 DataFrame
        year: 연도 문자열 (예: "2024")
        reportKind: "annual" | "Q1" | "semi" | "Q3"
    """
    kindFilter = _REPORT_KIND_MAP.get(reportKind)
    if kindFilter is None:
        return None

    reports = df.filter(
        (pl.col("year") == year)
        & (pl.col("report_type").str.contains(kindFilter))
    )
    if reports.height == 0:
        return None

    orig = reports.filter(
        ~pl.col("report_type").str.contains("기재정정|첨부")
    )
    if orig.height > 0:
        return orig

    latest = reports.sort("rcept_date", descending=True).head(1)
    latestType = latest["report_type"][0]
    return reports.filter(pl.col("report_type") == latestType)


def parsePeriodKey(reportType: str) -> str | None:
    """report_type 문자열에서 period key 추출.

    Returns:
        "2024Q1", "2024Q2", "2024Q3", "2024" 등. 파싱 불가 시 None.
    """
    m = re.search(r"\((\d{4})\.(\d{2})\)", reportType)
    if not m:
        return None

    year = m.group(1)
    month = m.group(2)

    if "분기보고서" in reportType:
        if month == "03":
            return f"{year}Q1"
        elif month == "09":
            return f"{year}Q3"
    elif "반기보고서" in reportType:
        return f"{year}Q2"
    elif "사업보고서" in reportType:
        return f"{year}Q4"
    return None


def extractReportYear(reportType: str) -> int | None:
    """사업보고서 (2024.12) → 2024"""
    m = re.search(r"\((\d{4})\.\d{2}\)", reportType)
    if m:
        return int(m.group(1))
    return None


_REPORT_KIND_MAP = {
    "annual": "사업보고서",
    "Q1": r"분기보고서.*\d{4}\.03",
    "semi": "반기보고서",
    "Q3": r"분기보고서.*\d{4}\.09",
}
