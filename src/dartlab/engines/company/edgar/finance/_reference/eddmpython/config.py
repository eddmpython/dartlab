"""
EDGAR 모듈 설정

SEC API 설정, 컬럼 매핑, 표준화 설정 등
"""

from pathlib import Path

SEC_HEADERS = {"User-Agent": "o12486vs2@gmail.com"}

EDGAR_UPDATE_TIME_UTC = {"hour": 4, "minute": 0}


def getEdgarDataDir() -> Path:
    from core.paths import DATA_DIR

    return DATA_DIR / "edgarData"


SEC_API_BASE = "https://data.sec.gov"
SEC_FILES_BASE = "https://www.sec.gov/files"
SEC_ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar"

BULK_FINANCE_URL = f"{SEC_ARCHIVES_BASE}/daily-index/xbrl/companyfacts.zip"
TICKERS_URL = f"{SEC_FILES_BASE}/company_tickers.json"
DATASET_BASE_URL = f"{SEC_FILES_BASE}/dera/data/financial-statement-data-sets"

RATE_LIMIT = 10

DATASET_TYPES = ["sub", "pre", "tag", "num"]

STATEMENT_MAPPING = {
    "BS": "Balance Sheet",
    "IS": "Income Statement",
    "CF": "Cash Flow Statement",
    "EQ": "Equity Statement",
    "CI": "Comprehensive Income",
    "UN": "Unclassified",
}

PERIOD_ORDER = {
    "Q1": 1,
    "Q2": 2,
    "Q3": 3,
    "Q4": 4,
    "FY": 5,
    "FYA": 6,
}

COLUMN_MAPPING = {
    "tag": "태그",
    "plabel": "표시명",
    "tlabel": "태그라벨",
    "val": "금액",
    "fy": "회계연도",
    "fp": "회계기간",
    "filed": "제출일",
    "form": "보고서유형",
    "stmt": "재무제표",
    "line": "순서",
    "inpth": "깊이",
}

NUMERIC_COLS = ["val", "fy", "line", "inpth"]
