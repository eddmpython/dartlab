import re

import polars as pl

_RE_YEAR_MONTH = re.compile(r"\((\d{4})\.(\d{2})\)")
_RE_YEAR_ONLY = re.compile(r"\((\d{4})\.\d{2}\)")


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

    useLiteral = reportKind in {"annual", "semi"}
    reports = df.filter((pl.col("year") == year) & (pl.col("report_type").str.contains(kindFilter, literal=useLiteral)))
    if reports.height == 0:
        return None

    orig = reports.filter(~pl.col("report_type").str.contains("기재정정|첨부"))
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
    m = _RE_YEAR_MONTH.search(reportType)
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
    m = _RE_YEAR_ONLY.search(reportType)
    if m:
        return int(m.group(1))
    return None


def selectEdgarReport(df: pl.DataFrame, periodKey: str) -> pl.DataFrame | None:
    """EDGAR docs DataFrame에서 특정 period_key에 해당하는 filing 선택.

    periodKey 예시:
    - "2024"   -> annual (10-K/20-F)
    - "2024Q1" -> 10-Q
    - "2024Q2" -> 10-Q
    - "2024Q3" -> 10-Q
    """
    if "period_key" not in df.columns:
        return None

    reports = df.filter(pl.col("period_key") == periodKey)
    if reports.height == 0:
        return None

    dateCol = "filing_date" if "filing_date" in reports.columns else None
    if dateCol is None:
        return reports

    latest = reports.sort(dateCol, descending=True).head(1)
    if "accession_no" in latest.columns:
        accession = latest["accession_no"][0]
        return reports.filter(pl.col("accession_no") == accession)

    reportType = latest["report_type"][0] if "report_type" in latest.columns else None
    if reportType is not None:
        return reports.filter(pl.col("report_type") == reportType)
    return latest


def parseEdgarPeriodKey(reportType: str) -> str | None:
    """EDGAR report_type 문자열에서 period key 추출.

    Examples:
        "10-K (2024.12)" -> "2024"
        "20-F (2024.12)" -> "2024"
        "10-Q (2024.03)" -> "2024Q1"
        "10-Q (2024.06)" -> "2024Q2"
        "10-Q (2024.09)" -> "2024Q3"
    """
    match = _RE_YEAR_MONTH.search(reportType)
    if not match:
        return None

    year = match.group(1)
    month = match.group(2)

    if "10-K" in reportType or "20-F" in reportType:
        return year
    if "10-Q" not in reportType:
        return None
    if month == "03":
        return f"{year}Q1"
    if month == "06":
        return f"{year}Q2"
    if month == "09":
        return f"{year}Q3"
    return None


def extractEdgarReportYear(reportType: str) -> int | None:
    """10-K (2024.12) -> 2024"""
    match = _RE_YEAR_ONLY.search(reportType)
    if match:
        return int(match.group(1))
    return None


_REPORT_KIND_MAP = {
    "annual": "사업보고서",
    "Q1": r"분기보고서.*\d{4}\.03",
    "semi": "반기보고서",
    "Q3": r"분기보고서.*\d{4}\.09",
}
