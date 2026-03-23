"""EDGAR docs 원문 수집기.

로컬/릴리즈에 parquet가 없을 때 SEC EDGAR API와 원문 HTML에서 직접 수집한다.
저장 포맷은 EDGAR 메타를 최대한 보존하고, 비교용 필드는 함께 저장한다.
"""

from __future__ import annotations

import json
import re
import signal
import time
import warnings
from pathlib import Path
from typing import Callable

import polars as pl
import requests
from alive_progress import alive_bar
from bs4 import BeautifulSoup, NavigableString, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

HEADERS = {"User-Agent": "DartLab eddmpython@gmail.com"}
BASE_URL = "https://www.sec.gov"
DATA_URL = "https://data.sec.gov"
SINCE_YEAR = 2009
REQUEST_INTERVAL = 0.2
FILING_TIMEOUT_SECONDS = 45
BATCH_SIZE = 25
BATCH_COOLDOWN_SECONDS = 8.0
SUPPORTED_REGULAR_FORMS = ("10-K", "10-Q", "20-F", "40-F")
SUPPORTED_ANNUAL_FORMS = ("10-K", "20-F", "40-F")
FALLBACK_FULL_DOCUMENT_FORMS = ("40-F",)
QUALITY_GATED_FORMS = ("10-K", "10-Q", "20-F")
FORTY_F_HEADINGS = {
    "NOTE TO UNITED STATES READERS - DIFFERENCES",
    "ANNUAL INFORMATION FORM",
    "AUDITED ANNUAL FINANCIAL STATEMENTS",
    "MANAGEMENT'S DISCUSSION AND ANALYSIS",
    "DISCLOSURE CONTROLS AND PROCEDURES",
    "AUDIT COMMITTEE",
    "CODE OF ETHICS",
    "PRINCIPAL ACCOUNTANT FEES AND SERVICES",
    "AUDIT COMMITTEE PRE-APPROVAL POLICIES AND PROCEDURES",
    "OFF-BALANCE SHEET ARRANGEMENTS",
    "CASH REQUIREMENTS",
    "MINE SAFETY DISCLOSURE",
    "DISCLOSURE REGARDING FOREIGN JURISDICTIONS THAT PREVENT INSPECTIONS",
    "RECOVERY OF ERRONEOUSLY AWARDED COMPENSATION",
    "NEW YORK STOCK EXCHANGE DISCLOSURE",
    "UNDERTAKINGS",
    "CONSENT TO SERVICE OF PROCESS",
    "EXHIBIT INDEX",
}

ITEM_NAMES_10K = {
    "1": "Business",
    "1A": "Risk Factors",
    "1B": "Unresolved Staff Comments",
    "1C": "Cybersecurity",
    "2": "Properties",
    "3": "Legal Proceedings",
    "4": "Mine Safety Disclosures",
    "5": "Market for Common Equity",
    "6": "Reserved",
    "7": "MD&A",
    "7A": "Market Risk Disclosures",
    "8": "Financial Statements",
    "9": "Changes in Accountants",
    "9A": "Controls and Procedures",
    "9B": "Other Information",
    "9C": "Foreign Jurisdiction Disclosures",
    "10": "Directors & Corporate Governance",
    "11": "Executive Compensation",
    "12": "Security Ownership",
    "13": "Related Transactions",
    "14": "Principal Accountant Fees",
    "15": "Exhibits & Schedules",
    "16": "Form 10-K Summary",
}

ITEM_NAMES_20F = {
    "1": "Identity of Directors & Senior Management",
    "2": "Offer Statistics and Expected Timetable",
    "3": "Key Information",
    "4": "Information on the Company",
    "4A": "Unresolved Staff Comments",
    "5": "Operating and Financial Review",
    "6": "Directors & Senior Management",
    "7": "Major Shareholders",
    "8": "Financial Information",
    "9": "The Offer and Listing",
    "10": "Additional Information",
    "11": "Quantitative and Qualitative Disclosures",
    "12": "Description of Securities",
    "13": "Defaults & Arrears",
    "14": "Material Modifications",
    "15": "Controls and Procedures",
    "16": "Reserved",
    "16A": "Audit Committee Financial Expert",
    "16B": "Code of Ethics",
    "16C": "Principal Accountant Fees",
    "16D": "Exemptions from Listing Standards",
    "16E": "Purchases of Equity Securities",
    "16F": "Change in Registrant's Certifying Accountant",
    "16G": "Corporate Governance",
    "16H": "Mine Safety Disclosure",
    "16I": "Disclosure Regarding Foreign Jurisdictions",
    "16J": "Insider Trading Policies",
    "16K": "Cybersecurity",
    "17": "Financial Statements",
    "18": "Financial Statements",
    "19": "Exhibits",
}

ITEM_NAMES_10Q = {
    "I:1": "Financial Statements",
    "I:2": "Management's Discussion and Analysis of Financial Condition and Results of Operations",
    "I:3": "Quantitative and Qualitative Disclosures About Market Risk",
    "I:4": "Controls and Procedures",
    "II:1": "Legal Proceedings",
    "II:1A": "Risk Factors",
    "II:2": "Unregistered Sales of Equity Securities and Use of Proceeds",
    "II:3": "Defaults Upon Senior Securities",
    "II:4": "Mine Safety Disclosures",
    "II:5": "Other Information",
    "II:6": "Exhibits",
}

ITEM_PATTERN = re.compile(
    r"(?:^|\n)\s*"
    r"(?:ITEM|Item)\s+"
    r"(\d+[A-K]?)"
    r"[\.\:\s\—\-]+"
    r"([^\n]{3,80})",
    re.MULTILINE,
)
PART_PATTERN = re.compile(r"^\s*PART\s+(II|I)\b", re.IGNORECASE | re.MULTILINE)
ITEM_LINE_PATTERN = re.compile(r"^\s*Item\s+(\d+[A-K]?)\s*[\.\:\-\u2013\u2014]?\s*(.*)$", re.IGNORECASE)
ITEM_NUMBER_TITLE_PATTERN = re.compile(r"^\s*(\d+[A-K]?)\s*[\.\:\-\u2013\u2014]\s*(.*)$", re.IGNORECASE)
ITEM_TABLE_LINE_PATTERN = re.compile(
    r"^\|\s*Item\s+(\d+[A-K]?)\s*[\.\:\-\u2013\u2014]?\s*\|\s*(.*?)\s*\|",
    re.IGNORECASE,
)
PART_TABLE_LINE_PATTERN = re.compile(
    r"^\|\s*PART\s+(II|I)\.?\s*(.*?)\|",
    re.IGNORECASE,
)


def fetchEdgarDocs(
    ticker: str,
    outPath: Path,
    *,
    sinceYear: int = SINCE_YEAR,
    maxFilings: int | None = None,
    filingTimeout: int = FILING_TIMEOUT_SECONDS,
    showProgress: bool = True,
    sourceMode: str = "sec_api",
    strictQuality: bool = False,
) -> Path:
    ticker = ticker.upper()
    meta = _resolveTickerMeta(ticker)
    submissions = _getSubmissions(meta["cik"])
    filings = _findFilings(submissions, sinceYear)

    if not filings:
        raise ValueError(f"{ticker} EDGAR docs filing 없음 (since {sinceYear})")

    from dartlab.core.guidance import emit

    if maxFilings is not None and len(filings) > maxFilings:
        filings = filings[-maxFilings:]
        emit("edgar:filing_limit", ticker=ticker, maxFilings=maxFilings)

    emit("edgar:docs_start", ticker=ticker, count=len(filings), sinceYear=sinceYear)

    rows: list[dict] = []
    skippedFilings: list[str] = []
    if showProgress:
        with alive_bar(len(filings), title="EDGAR 원문 수집") as bar:
            _collectFilingRows(rows, filings, meta, ticker, bar, filingTimeout, skippedFilings)
    else:
        _collectFilingRows(rows, filings, meta, ticker, None, filingTimeout, skippedFilings)

    if not rows:
        raise ValueError(f"{ticker} EDGAR docs에서 section 추출 실패")

    outPath.parent.mkdir(parents=True, exist_ok=True)
    df = pl.DataFrame(rows)
    summary = summarizeEdgarDocsFrame(df)
    if strictQuality:
        _assertEdgarDocsQuality(summary)
    df.write_parquet(outPath)
    if skippedFilings:
        emit("edgar:docs_skip", ticker=ticker, count=len(skippedFilings))
    emit("edgar:docs_save", path=str(outPath))
    return outPath


def summarizeEdgarDocsFrame(df: pl.DataFrame) -> dict[str, object]:
    if df.is_empty():
        return {
            "rows_saved": 0,
            "filings_saved": 0,
            "forms_found": [],
            "full_document_rows": 0,
            "table_rows": 0,
            "quality_flags": ["empty_parquet"],
            "form_metrics": [],
        }

    sectionTitle = pl.col("section_title").cast(pl.Utf8)
    sectionContent = pl.col("section_content").cast(pl.Utf8)
    formType = pl.col("form_type").cast(pl.Utf8)

    formMetricsDf = (
        df.group_by("form_type")
        .agg(
            pl.len().alias("rows_saved"),
            pl.col("accession_no").n_unique().alias("filings_saved"),
            sectionTitle.eq("Full Document").sum().alias("full_document_rows"),
            sectionContent.str.contains(r"\|").sum().alias("table_rows"),
            sectionTitle.n_unique().alias("unique_titles"),
        )
        .sort("form_type")
    )

    qualityFlags: list[str] = []
    formMetrics: list[dict[str, object]] = []
    for row in formMetricsDf.to_dicts():
        filingsSaved = int(row["filings_saved"])
        fullDocumentRows = int(row["full_document_rows"])
        fullDocumentRatio = fullDocumentRows / filingsSaved if filingsSaved else 0.0
        tableRows = int(row["table_rows"])
        rowsSaved = int(row["rows_saved"])
        tableRatio = tableRows / rowsSaved if rowsSaved else 0.0
        metric = {
            "form_type": row["form_type"],
            "rows_saved": rowsSaved,
            "filings_saved": filingsSaved,
            "full_document_rows": fullDocumentRows,
            "full_document_ratio": round(fullDocumentRatio, 6),
            "table_rows": tableRows,
            "table_ratio": round(tableRatio, 6),
            "unique_titles": int(row["unique_titles"]),
        }
        formMetrics.append(metric)
        if row["form_type"] not in FALLBACK_FULL_DOCUMENT_FORMS and fullDocumentRows > 0:
            qualityFlags.append(f"unexpected_full_document:{row['form_type']}")

    return {
        "rows_saved": df.height,
        "filings_saved": df["accession_no"].n_unique() if "accession_no" in df.columns else 0,
        "forms_found": sorted(df["form_type"].drop_nulls().unique().to_list()) if "form_type" in df.columns else [],
        "full_document_rows": int(df.filter(sectionTitle == "Full Document").height),
        "table_rows": int(df.select(sectionContent.str.contains(r"\|").sum().alias("table_rows")).item()),
        "quality_flags": qualityFlags,
        "form_metrics": formMetrics,
    }


def summarizeEdgarDocsParquet(path: Path) -> dict[str, object]:
    summary = summarizeEdgarDocsFrame(pl.read_parquet(path))
    summary["path"] = str(path)
    summary["ticker"] = path.stem
    return summary


def _assertEdgarDocsQuality(summary: dict[str, object]) -> None:
    qualityFlags = [str(flag) for flag in summary.get("quality_flags", [])]
    blocking = [
        flag
        for flag in qualityFlags
        if any(flag == f"unexpected_full_document:{formType}" for formType in QUALITY_GATED_FORMS)
    ]
    if blocking:
        raise ValueError(f"EDGAR docs 품질 게이트 실패: {', '.join(blocking)}")


def _collectFilingRows(
    rows: list[dict],
    filings: list[dict],
    meta: dict[str, str],
    ticker: str,
    bar,
    filingTimeout: int,
    skippedFilings: list[str],
) -> None:
    for filing in filings:
        try:
            timer = _FilingTimeout(filingTimeout)
            with timer:
                html = _downloadFilingSource(filing)
                if timer.timedOut:
                    raise TimeoutError("filing fetch timed out")
                text = _htmlToText(html)
                if filing["formType"] == "40-F":
                    items = _split40FSections(filing, text)
                else:
                    items = _splitItems(text, filing["formType"])
        except (requests.RequestException, TimeoutError, ValueError):
            skippedFilings.append(str(filing["accessionNumber"]))
            if bar is not None:
                bar()
            continue

        reportType = _reportType(filing["formType"], filing.get("periodEnd"))
        periodKey = _periodKey(filing["formType"], filing.get("periodEnd"), filing["year"])
        for order, item in enumerate(items):
            rows.append(
                {
                    "cik": meta["cik"],
                    "company_name": meta["title"],
                    "ticker": ticker,
                    "year": filing["year"],
                    "filing_date": filing["filingDate"],
                    "period_end": filing.get("periodEnd"),
                    "accession_no": filing["accessionNumber"],
                    "form_type": filing["formType"],
                    "report_type": reportType,
                    "period_key": periodKey,
                    "section_order": order,
                    "section_title": item["title"],
                    "filing_url": filing["filingUrl"],
                    "section_content": item["content"],
                }
            )
        if bar is not None:
            bar()


_HAS_SIGALRM = hasattr(signal, "SIGALRM")


class _FilingTimeout:
    """크로스 플랫폼 타임아웃 컨텍스트 매니저.

    Unix: signal.SIGALRM 사용 (메인 스레드에서만 동작).
    Windows: threading.Timer 폴백 (메인 스레드 인터럽트 불가하므로
    requests의 timeout 파라미터에 의존하되, 전체 작업 타임아웃은
    Timer로 _timedOut 플래그 설정).
    """

    def __init__(self, seconds: int):
        self.seconds = max(int(seconds), 0)
        self._previousHandler = None
        self._timer = None
        self.timedOut = False

    def __enter__(self):
        if self.seconds <= 0:
            return self
        if _HAS_SIGALRM:
            self._previousHandler = signal.getsignal(signal.SIGALRM)
            signal.signal(signal.SIGALRM, self._handle)
            signal.alarm(self.seconds)
        else:
            import threading

            self._timer = threading.Timer(self.seconds, self._markTimedOut)
            self._timer.daemon = True
            self._timer.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.seconds > 0:
            if _HAS_SIGALRM:
                signal.alarm(0)
                if self._previousHandler is not None:
                    signal.signal(signal.SIGALRM, self._previousHandler)
            elif self._timer is not None:
                self._timer.cancel()
        return False

    def _markTimedOut(self):
        self.timedOut = True

    @staticmethod
    def _handle(signum, frame):
        raise TimeoutError("filing fetch timed out")


def downloadListedEdgarDocs(
    *,
    limit: int = 2000,
    sinceYear: int = SINCE_YEAR,
    batchSize: int = BATCH_SIZE,
    cooldownSeconds: float = BATCH_COOLDOWN_SECONDS,
    skipExisting: bool = True,
) -> pl.DataFrame:
    from dartlab import config

    docsDir = Path(config.dataDir) / "edgar" / "docs"
    docsDir.mkdir(parents=True, exist_ok=True)

    universe = buildEdgarCollectibleUniverse(limit=limit, sinceYear=sinceYear)

    tickers = universe["ticker"].to_list()
    total = len(tickers)
    from dartlab.core.guidance import emit

    emit("edgar:batch_start", total=total, sinceYear=sinceYear)

    results: list[dict] = []
    with alive_bar(total, title="EDGAR docs 배치 수집") as bar:
        for idx, ticker in enumerate(tickers, start=1):
            outPath = docsDir / f"{ticker}.parquet"
            if skipExisting and outPath.exists():
                results.append({"ticker": ticker, "status": "skipped", "reason": "exists"})
                bar()
                continue

            try:
                fetchEdgarDocs(ticker, outPath, sinceYear=sinceYear, showProgress=False)
                results.append({"ticker": ticker, "status": "downloaded", "reason": None})
            except (OSError, ValueError, requests.RequestException) as e:
                results.append({"ticker": ticker, "status": "failed", "reason": str(e)})
            finally:
                bar()

            if batchSize > 0 and idx < total and idx % batchSize == 0:
                print()
                emit("edgar:batch_progress", idx=idx, cooldown=cooldownSeconds)
                time.sleep(cooldownSeconds)

    return pl.DataFrame(results)


def buildEdgarCollectibleUniverse(
    *,
    limit: int = 2000,
    sinceYear: int = SINCE_YEAR,
    forceRefresh: bool = False,
) -> pl.DataFrame:
    return prepareEdgarCollectibleUniverse(
        limit=limit,
        sinceYear=sinceYear,
        forceRefresh=forceRefresh,
    )


def prepareEdgarCollectibleUniverse(
    *,
    limit: int = 2000,
    sinceYear: int = SINCE_YEAR,
    forceRefresh: bool = False,
    progressPath: Path | None = None,
    flushEvery: int = 25,
    heartbeat: Callable[..., None] | None = None,
) -> pl.DataFrame:
    from dartlab import config
    from dartlab.core.dataLoader import loadEdgarListedUniverse

    cachePath = Path(config.dataDir) / "edgar" / "docsCollectibleUniverse.parquet"
    cacheDf = _loadCollectibleUniverseCache(cachePath, forceRefresh=forceRefresh)

    listed = (
        loadEdgarListedUniverse()
        .filter(pl.col("is_exchange_listed"))
        .select(["ticker", "cik", "title", "exchange"])
        .sort(["ticker", "cik"])
    )
    issuerUniverse = _dedupeIssuerUniverse(listed)

    if not cacheDf.is_empty():
        issuerUniverse = issuerUniverse.join(
            cacheDf.select(["cik", "has_supported_regular_filing", "supported_regular_forms", "last_checked"]),
            on="cik",
            how="left",
        )
    else:
        issuerUniverse = issuerUniverse.with_columns(
            pl.lit(None, dtype=pl.Boolean).alias("has_supported_regular_filing"),
            pl.lit(None, dtype=pl.Utf8).alias("supported_regular_forms"),
            pl.lit(None, dtype=pl.Utf8).alias("last_checked"),
        )

    evaluationUniverse = _interleaveIssuerUniverse(issuerUniverse)
    rows = evaluationUniverse.to_dicts()
    evaluatedBatch: list[dict[str, object]] = []
    selected: list[dict[str, object]] = []
    for idx, row in enumerate(rows, start=1):
        if heartbeat is not None:
            heartbeat(
                stage="prepare_universe",
                currentTicker=str(row["ticker"]),
                currentCik=str(row["cik"]),
                candidatesReady=len(selected),
                universeChecked=idx - 1,
            )

        if row.get("has_supported_regular_filing") is None or forceRefresh:
            try:
                submissions = _getSubmissions(str(row["cik"]))
                supportedForms = _supportedRegularForms(submissions, sinceYear)
                row["supported_regular_forms"] = ",".join(supportedForms)
                row["has_supported_regular_filing"] = bool(supportedForms)
                row["last_checked"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                universeStatus = "supported" if supportedForms else "unsupported_regular_forms"
            except requests.RequestException as exc:
                row["supported_regular_forms"] = None
                row["has_supported_regular_filing"] = None
                row["last_checked"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                universeStatus = "submissions_fetch_error"
                if progressPath is not None:
                    _appendJsonl(
                        progressPath,
                        {
                            "ticker": row["ticker"],
                            "cik": row["cik"],
                            "exchange": row["exchange"],
                            "status": universeStatus,
                            "reason": str(exc),
                            "last_checked": row["last_checked"],
                        },
                    )
                continue

            if progressPath is not None:
                _appendJsonl(
                    progressPath,
                    {
                        "ticker": row["ticker"],
                        "cik": row["cik"],
                        "exchange": row["exchange"],
                        "status": universeStatus,
                        "supported_regular_forms": row["supported_regular_forms"],
                        "last_checked": row["last_checked"],
                    },
                )

        evaluatedBatch.append(row)
        if row.get("has_supported_regular_filing"):
            selected.append(row)
        if flushEvery > 0 and len(evaluatedBatch) >= flushEvery:
            cacheDf = _mergeCollectibleUniverseCache(cachePath, cacheDf, evaluatedBatch)
            evaluatedBatch = []
        if limit > 0 and len(selected) >= limit:
            break

    if evaluatedBatch:
        cacheDf = _mergeCollectibleUniverseCache(cachePath, cacheDf, evaluatedBatch)

    result = pl.DataFrame(selected)
    if limit > 0 and result.height > limit:
        result = result.head(limit)
    if result.is_empty():
        return pl.DataFrame(
            schema={
                "candidate_order": pl.Int64,
                "ticker": pl.Utf8,
                "cik": pl.Utf8,
                "title": pl.Utf8,
                "exchange": pl.Utf8,
                "supported_regular_forms": pl.Utf8,
                "last_checked": pl.Utf8,
            }
        )
    result = result.with_row_index("candidate_order", offset=1)
    return result.select(
        [
            "candidate_order",
            "ticker",
            "cik",
            "title",
            "exchange",
            "supported_regular_forms",
            "last_checked",
        ]
    )


def _emptyCollectibleUniverseCache() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "ticker": pl.Utf8,
            "cik": pl.Utf8,
            "title": pl.Utf8,
            "exchange": pl.Utf8,
            "supported_regular_forms": pl.Utf8,
            "has_supported_regular_filing": pl.Boolean,
            "last_checked": pl.Utf8,
        }
    )


def _loadCollectibleUniverseCache(cachePath: Path, *, forceRefresh: bool) -> pl.DataFrame:
    if cachePath.exists() and not forceRefresh:
        return pl.read_parquet(cachePath)
    return _emptyCollectibleUniverseCache()


def _mergeCollectibleUniverseCache(
    cachePath: Path, cacheDf: pl.DataFrame, rows: list[dict[str, object]]
) -> pl.DataFrame:
    freshDf = pl.DataFrame(rows)
    if cacheDf.is_empty():
        merged = freshDf
    else:
        remaining = cacheDf.filter(~pl.col("cik").is_in(freshDf["cik"].to_list()))
        merged = pl.concat([remaining, freshDf], how="vertical_relaxed")
    cachePath.parent.mkdir(parents=True, exist_ok=True)
    merged.write_parquet(cachePath)
    return merged


def _appendJsonl(path: Path, record: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _resolveTickerMeta(ticker: str) -> dict[str, str]:
    from dartlab.engines.company.edgar.openapi.identity import resolveIssuer

    info = resolveIssuer(str(ticker).upper())
    return {
        "ticker": info["ticker"],
        "cik": info["cik"],
        "title": info["title"],
    }


def _getSubmissions(cik: str) -> dict:
    from dartlab.engines.company.edgar.openapi.submissions import getSubmissionsJson

    return getSubmissionsJson(cik)


def _mergeFilingArrays(submissions: dict, sinceYear: int) -> dict:
    from dartlab.engines.company.edgar.openapi.submissions import mergeSubmissionFilings

    return mergeSubmissionFilings(submissions, sinceYear=sinceYear)


def _findFilings(submissions: dict, sinceYear: int) -> list[dict]:
    from dartlab.engines.company.edgar.openapi.submissions import findRegularFilings

    rows = findRegularFilings(submissions, sinceYear=sinceYear)
    converted: list[dict] = []
    for row in rows:
        converted.append(
            {
                "formType": row["form"],
                "filingDate": row["filing_date"],
                "year": row["year"],
                "periodEnd": row["report_date"],
                "accessionNumber": row["accession_no"],
                "filingUrl": row["filing_url"],
            }
        )
    return converted


def _downloadHtml(url: str, *, maxRetries: int = 3) -> str:
    """HTML 다운로드 (재시도 포함)."""
    lastErr: Exception | None = None
    for attempt in range(maxRetries):
        time.sleep(REQUEST_INTERVAL if attempt == 0 else REQUEST_INTERVAL * (2**attempt))
        try:
            resp = requests.get(url, headers=HEADERS, timeout=60)
            resp.raise_for_status()
            return resp.text
        except (requests.ConnectionError, requests.Timeout) as e:
            lastErr = e
            continue
    raise lastErr or requests.RequestException(f"failed after {maxRetries} retries: {url}")


def _submissionTextUrl(filing: dict) -> str:
    filingUrl = str(filing["filingUrl"])
    baseDir = filingUrl.rsplit("/", 1)[0]
    accession = str(filing["accessionNumber"])
    return f"{baseDir}/{accession}.txt"


def _filingDirectoryUrl(filing: dict) -> str:
    return str(filing["filingUrl"]).rsplit("/", 1)[0]


def _filingIndexJsonUrl(filing: dict) -> str:
    return f"{_filingDirectoryUrl(filing)}/index.json"


def _listFilingHtmlDocuments(filing: dict) -> list[str]:
    time.sleep(REQUEST_INTERVAL)
    resp = requests.get(_filingIndexJsonUrl(filing), headers=HEADERS, timeout=30)
    resp.raise_for_status()
    items = resp.json().get("directory", {}).get("item", [])
    names: list[str] = []
    for item in items:
        name = str(item.get("name") or "")
        lower = name.lower()
        if not lower.endswith((".htm", ".html")):
            continue
        if lower.endswith("-index.html") or lower.endswith("-index-headers.html"):
            continue
        if re.fullmatch(r"r\d+\.htm", lower):
            continue
        names.append(name)
    return names


def _classify40FDocumentName(name: str) -> str | None:
    lower = name.lower()
    if "annualinformation" in lower or "annual-information" in lower or "annualinformationfo" in lower:
        return "Annual Information Form"
    if lower.startswith("mda") or "managementdiscussion" in lower or "management-discussion" in lower:
        return "MD&A"
    if "financialstatement" in lower or "financial-statements" in lower or lower.endswith("_d2.htm"):
        return "Financial Statements"
    return None


def _isLowQualityText(text: str) -> bool:
    sample = text[:8000].strip()
    if len(sample) < 200:
        return True
    letters = sum(ch.isalpha() for ch in sample)
    spaces = sample.count(" ")
    if letters > 0 and spaces / max(len(sample), 1) < 0.02:
        return True
    return False


def _downloadFilingSource(filing: dict) -> str:
    html = _downloadHtml(str(filing["filingUrl"]))
    if html.strip():
        return html
    return _downloadHtml(_submissionTextUrl(filing))


def _split40FSections(filing: dict, primaryText: str) -> list[dict]:
    sections: list[dict] = []
    seenTitles: set[str] = set()

    try:
        for name in _listFilingHtmlDocuments(filing):
            title = _classify40FDocumentName(name)
            if title is None or title in seenTitles:
                continue
            url = f"{_filingDirectoryUrl(filing)}/{name}"
            text = _htmlToText(_downloadHtml(url))
            if _isLowQualityText(text):
                continue
            sections.append({"title": title, "content": text})
            seenTitles.add(title)
    except requests.RequestException:
        pass

    if sections:
        return sections
    headingSections = _split40FPrimaryText(primaryText)
    if headingSections:
        return headingSections
    return [{"title": "Full Document", "content": primaryText}]


def _split40FPrimaryText(text: str) -> list[dict]:
    starts: list[dict[str, int | str]] = []
    offset = 0
    seen: set[str] = set()
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        upper = stripped.upper()
        if upper in FORTY_F_HEADINGS and upper not in seen:
            starts.append({"title": stripped, "start": offset})
            seen.add(upper)
        offset += len(line)

    if len(starts) < 2:
        return []

    sections: list[dict] = []
    for idx, startInfo in enumerate(starts):
        start = int(startInfo["start"])
        end = int(starts[idx + 1]["start"]) if idx + 1 < len(starts) else len(text)
        content = text[start:end].strip()
        if not content:
            continue
        sections.append(
            {
                "title": str(startInfo["title"]).title(),
                "content": content,
            }
        )
    return sections


def _tableToMarkdown(table) -> str:
    rows = []
    for tr in table.find_all("tr"):
        cells = []
        for cell in tr.find_all(["td", "th"]):
            colspan = int(cell.get("colspan", 1))
            text = cell.get_text(" ", strip=True)
            text = re.sub(r"\s+", " ", text)
            text = text.replace("|", "｜")
            cells.append(text)
            for _ in range(colspan - 1):
                cells.append("")
        if cells and any(cell.strip() for cell in cells):
            rows.append(cells)

    if not rows:
        return ""

    maxCols = max(len(r) for r in rows)
    for row in rows:
        while len(row) < maxCols:
            row.append("")

    lines = []
    lines.append("| " + " | ".join(rows[0]) + " |")
    lines.append("| " + " | ".join(["---"] * maxCols) + " |")
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _extractItemHeaders(soup) -> None:
    itemRe = re.compile(r"Item\s+\d+[A-K]?\.\s*\S", re.IGNORECASE)
    itemExact = re.compile(r"Item\s+\d+[A-K]?\.\s*$", re.IGNORECASE)
    for tag in soup.find_all(["font", "span", "b", "strong", "p", "div"]):
        text = tag.get_text(strip=True)
        if not itemRe.match(text) and not itemExact.match(text):
            continue
        if tag.find_parent("a", href=True) or tag.find("a", href=True):
            continue
        parentTable = tag.find_parent("table")
        if not parentTable:
            continue
        if tag.name in ("p", "div") and len(text) > 120:
            continue
        headerP = soup.new_tag("p")
        headerP.string = text
        parentTable.insert_before(headerP)


def _htmlToText(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "meta", "link", "header", "footer", "nav"]):
        tag.decompose()
    for tag in soup.find_all(style=True):
        style = str(tag.get("style") or "").lower()
        if "display:none" in style or "visibility:hidden" in style:
            tag.decompose()
    for tag in soup.find_all(re.compile(r"^(ix:header|ix:hidden|ix:references|ix:resources|xbrli:|dei:|link:)")):
        tag.decompose()
    for ix_tag in soup.find_all(re.compile(r"^ix:")):
        ix_tag.unwrap()
    _extractItemHeaders(soup)
    for table in soup.find_all("table"):
        md = _tableToMarkdown(table)
        if md:
            table.replace_with(NavigableString(f"\n\n{md}\n\n"))
        else:
            table.decompose()
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all(["p", "div", "li", "h1", "h2", "h3", "h4"]):
        p.insert_after("\n")
    text = (soup.body or soup).get_text("\n")
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _splitItems(text: str, formType: str) -> list[dict]:
    if formType == "40-F":
        return [{"title": "Full Document", "content": text}]
    if formType == "10-Q":
        return _splitQuarterlyItems(text)

    itemNames = ITEM_NAMES_20F if formType == "20-F" else ITEM_NAMES_10K
    matches = list(ITEM_PATTERN.finditer(text))
    if not matches:
        tableItems = _splitTableStructuredItems(text, itemNames)
        if tableItems:
            return tableItems
        return [{"title": "Full Document", "content": text}]

    startsByItem: dict[str, dict[str, int | str]] = {}
    for match in matches:
        itemNum = match.group(1).upper()
        canonTitle = itemNames.get(itemNum, match.group(2).strip().rstrip("."))
        startsByItem[itemNum] = {
            "item_num": itemNum,
            "start": match.start(),
            "title": f"Item {itemNum}. {canonTitle}",
        }

    starts = sorted(startsByItem.values(), key=lambda row: int(row["start"]))
    items: list[dict] = []
    for idx, startInfo in enumerate(starts):
        start = int(startInfo["start"])
        end = int(starts[idx + 1]["start"]) if idx + 1 < len(starts) else len(text)
        content = text[start:end].strip()
        if not content:
            continue
        items.append(
            {
                "title": str(startInfo["title"]),
                "content": content,
            }
        )
    return items


def _splitTableStructuredItems(text: str, itemNames: dict[str, str]) -> list[dict]:
    startsByItem: dict[str, dict[str, int | str]] = {}
    offset = 0
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        match = ITEM_TABLE_LINE_PATTERN.match(stripped)
        if match:
            itemNum = match.group(1).upper()
            title = itemNames.get(itemNum) or re.sub(r"\s+", " ", match.group(2).strip(" |"))
            if title:
                startsByItem[itemNum] = {
                    "item_num": itemNum,
                    "start": offset,
                    "title": f"Item {itemNum}. {title}",
                }
        offset += len(line)

    starts = sorted(startsByItem.values(), key=lambda row: int(row["start"]))
    if len(starts) < 2:
        return []

    items: list[dict] = []
    for idx, startInfo in enumerate(starts):
        start = int(startInfo["start"])
        end = int(starts[idx + 1]["start"]) if idx + 1 < len(starts) else len(text)
        content = text[start:end].strip()
        if not content:
            continue
        items.append(
            {
                "title": str(startInfo["title"]),
                "content": content,
            }
        )
    return items


def _splitQuarterlyItems(text: str) -> list[dict]:
    body = _quarterlyBodyText(text)
    if not body:
        return [{"title": "Full Document", "content": text}]

    bodyLines = body.splitlines()
    startsByKey: dict[tuple[str, str], dict[str, int | str]] = {}
    currentPart: str | None = None
    offset = 0

    for idx, rawLine in enumerate(bodyLines):
        line = rawLine + "\n"
        stripped = rawLine.strip()
        if not stripped:
            offset += len(line)
            continue
        partMatch = PART_PATTERN.match(stripped)
        if partMatch:
            currentPart = partMatch.group(1).upper()
            offset += len(line)
            continue

        if stripped.upper() == "PART" and idx + 1 < len(bodyLines):
            nextLine = bodyLines[idx + 1].strip()
            nextMatch = re.match(r"^(I|II)\b", nextLine, re.IGNORECASE)
            if nextMatch:
                currentPart = nextMatch.group(1).upper()
                offset += len(line)
                continue

        partTableMatch = PART_TABLE_LINE_PATTERN.match(stripped)
        if partTableMatch:
            currentPart = partTableMatch.group(1).upper()
            offset += len(line)
            continue

        itemMatch = ITEM_LINE_PATTERN.match(stripped)
        if itemMatch and currentPart is not None:
            itemNum = itemMatch.group(1).upper()
            key = (currentPart, itemNum)
            canonicalTitle = ITEM_NAMES_10Q.get(f"{currentPart}:{itemNum}")
            if idx + 1 < len(bodyLines):
                nextTitle = bodyLines[idx + 1].strip()
                if nextTitle and not PART_PATTERN.match(nextTitle) and not ITEM_LINE_PATTERN.match(nextTitle):
                    if not itemMatch.group(2).strip():
                        canonicalTitle = canonicalTitle or nextTitle
            if canonicalTitle:
                startsByKey[key] = {
                    "part": currentPart,
                    "item_num": itemNum,
                    "start": offset,
                    "title": f"Part {currentPart} - Item {itemNum}. {canonicalTitle}",
                }
            offset += len(line)
            continue

        if stripped.upper() == "ITEM" and idx + 1 < len(bodyLines) and currentPart is not None:
            nextLine = bodyLines[idx + 1].strip()
            nextItemMatch = ITEM_NUMBER_TITLE_PATTERN.match(nextLine)
            if nextItemMatch:
                itemNum = nextItemMatch.group(1).upper()
                key = (currentPart, itemNum)
                canonicalTitle = ITEM_NAMES_10Q.get(f"{currentPart}:{itemNum}") or nextItemMatch.group(2).strip()
                if canonicalTitle:
                    startsByKey[key] = {
                        "part": currentPart,
                        "item_num": itemNum,
                        "start": offset,
                        "title": f"Part {currentPart} - Item {itemNum}. {canonicalTitle}",
                    }
                offset += len(line)
                continue

        itemTableMatch = ITEM_TABLE_LINE_PATTERN.match(stripped)
        if itemTableMatch and currentPart is not None:
            itemNum = itemTableMatch.group(1).upper()
            key = (currentPart, itemNum)
            titleText = itemTableMatch.group(2).strip()
            canonicalTitle = ITEM_NAMES_10Q.get(f"{currentPart}:{itemNum}") or titleText
            if canonicalTitle:
                startsByKey[key] = {
                    "part": currentPart,
                    "item_num": itemNum,
                    "start": offset,
                    "title": f"Part {currentPart} - Item {itemNum}. {canonicalTitle}",
                }
        offset += len(line)

    starts = sorted(startsByKey.values(), key=lambda row: int(row["start"]))
    if len(starts) < 2:
        return [{"title": "Full Document", "content": body}]

    items: list[dict] = []
    for idx, startInfo in enumerate(starts):
        start = int(startInfo["start"])
        end = int(starts[idx + 1]["start"]) if idx + 1 < len(starts) else len(body)
        content = _cleanQuarterlySectionText(body[start:end].strip())
        if not content:
            continue
        items.append(
            {
                "title": str(startInfo["title"]),
                "content": content,
            }
        )

    if len(items) < 2:
        return [{"title": "Full Document", "content": body}]
    return items


def _quarterlyBodyText(text: str) -> str:
    lines = text.splitlines()
    partStarts: list[int] = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r"^PART\s+I\b", stripped, re.IGNORECASE):
            partStarts.append(idx)
            continue
        if stripped.upper() == "PART" and idx + 1 < len(lines):
            if re.match(r"^I\b", lines[idx + 1].strip(), re.IGNORECASE):
                partStarts.append(idx)
                continue
        if PART_TABLE_LINE_PATTERN.match(stripped):
            partStarts.append(idx)
    if len(partStarts) >= 2:
        return "\n".join(lines[partStarts[1] :]).strip()
    if partStarts:
        return "\n".join(lines[partStarts[0] :]).strip()
    return text


def _cleanQuarterlySectionText(text: str) -> str:
    lines = text.splitlines()
    cleaned: list[str] = []
    headerSeen = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if not headerSeen and ITEM_LINE_PATTERN.match(stripped):
            headerSeen = True
            cleaned.append(stripped)
            continue
        if stripped.startswith("| Item ") or stripped.startswith("| PART "):
            continue
        cleaned.append(stripped)
    return "\n".join(cleaned).strip()


def _reportType(formType: str, periodEnd: str | None) -> str:
    if not periodEnd:
        return formType
    match = re.match(r"(\d{4})-(\d{2})", periodEnd)
    if not match:
        return formType
    year, month = match.groups()
    return f"{formType} ({year}.{month})"


def _periodKey(formType: str, periodEnd: str | None, year: str) -> str | None:
    if periodEnd:
        match = re.match(r"(\d{4})-(\d{2})", periodEnd)
        if match:
            pYear, month = match.groups()
            if formType in SUPPORTED_ANNUAL_FORMS:
                return pYear
            if formType == "10-Q":
                if month == "03":
                    return f"{pYear}Q1"
                if month == "06":
                    return f"{pYear}Q2"
                if month == "09":
                    return f"{pYear}Q3"
    if formType in SUPPORTED_ANNUAL_FORMS:
        return str(year)
    return None


def _tickerSortKey(ticker: str) -> tuple[int, int, str]:
    hasSuffix = 1 if "-" in ticker else 0
    return hasSuffix, len(ticker), ticker


def _dedupeIssuerUniverse(df: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for cik, group in df.group_by("cik", maintain_order=True):
        records = group.sort("ticker").to_dicts()
        records.sort(key=lambda row: _tickerSortKey(str(row["ticker"])))
        rows.append(records[0])
    return pl.DataFrame(rows).sort("ticker")


def _tickerBucketKey(ticker: str) -> str:
    ticker = ticker.upper()
    if not ticker:
        return "#"
    first = ticker[0]
    if first.isalnum():
        return first
    return "#"


def _interleaveIssuerUniverse(df: pl.DataFrame) -> pl.DataFrame:
    if df.is_empty():
        return df

    buckets: dict[str, list[dict[str, object]]] = {}
    for row in df.sort("ticker").to_dicts():
        buckets.setdefault(_tickerBucketKey(str(row["ticker"])), []).append(row)

    ordered: list[dict[str, object]] = []
    bucketKeys = sorted(buckets)
    while True:
        progressed = False
        for key in bucketKeys:
            bucket = buckets[key]
            if not bucket:
                continue
            ordered.append(bucket.pop(0))
            progressed = True
        if not progressed:
            break

    return pl.DataFrame(ordered)


def _supportedRegularForms(submissions: dict, sinceYear: int) -> list[str]:
    merged = _mergeFilingArrays(submissions, sinceYear)
    forms: list[str] = []
    for i, formType in enumerate(merged["form"]):
        if formType not in SUPPORTED_REGULAR_FORMS:
            continue
        filingDate = merged["filingDate"][i]
        if int(filingDate[:4]) < sinceYear:
            continue
        if formType not in forms:
            forms.append(formType)
    return forms
