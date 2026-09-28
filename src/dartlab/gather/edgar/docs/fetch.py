"""EDGAR docs 원문 수집기.

로컬/릴리즈에 parquet가 없을 때 SEC EDGAR API와 원문 HTML에서 직접 수집한다.
저장 포맷은 EDGAR 메타를 최대한 보존하고, 비교용 필드는 함께 저장한다.
"""

from __future__ import annotations

import json
import re
import signal
import threading
import time
import warnings
from pathlib import Path
from typing import Callable

from dartlab.core.logger import getLogger

_log = getLogger(__name__)


import httpx
import polars as pl
from bs4 import BeautifulSoup, NavigableString, XMLParsedAsHTMLWarning
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

from dartlab.gather.edgar.docs._const import (  # noqa: E402,F401
    BASE_URL,
    DATA_URL,
    HEADERS,
    REQUEST_INTERVAL,
    SINCE_YEAR,
)

FILING_TIMEOUT_SECONDS = 45
BATCH_SIZE = 25


def filingTimeoutSeconds() -> int:
    """공시 fetch 타임아웃(초) — providers 소비자가 core.edgarClient seam 으로 접근."""
    return FILING_TIMEOUT_SECONDS


_ITEM_HEADER_RE = re.compile(r"Item\s+\d+[A-K]?\.\s*\S", re.IGNORECASE)
_ITEM_HEADER_EXACT_RE = re.compile(r"Item\s+\d+[A-K]?\.\s*$", re.IGNORECASE)
_IX_DECOMPOSE_RE = re.compile(r"^(ix:header|ix:hidden|ix:references|ix:resources|xbrli:|dei:|link:)")
_IX_UNWRAP_RE = re.compile(r"^ix:")
_WHITESPACE_RE = re.compile(r"\s+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
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


def _makeProgress(total: int, title: str, *, disable: bool = False):
    """alive_bar 호환 (progress, bar) 쌍을 반환하는 헬퍼."""
    from dartlab.core.logger import getConsole

    p = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        console=getConsole(),
        disable=disable,
    )
    tid = p.add_task(title, total=total)

    class _Bar:
        @property
        def title(self):
            """진행 막대 description (read-only getter — 빈 문자열).

            Returns:
                빈 str.

            Raises:
                없음.

            Example:
                >>> _, bar = _progress(...)
                >>> bar.title
                ''
            """
            return ""

        @title.setter
        def title(self, v):
            """진행 막대 description 변경.

            Args:
                v: 새 description.

            Raises:
                없음.

            Example:
                >>> bar.title = "downloading..."

            SeeAlso:
            Requires:
                - bs4
                - dartlab
                - httpx
                - polars
                - rich

            Capabilities:
            Guide:
            AIContext:
                (AI 호출 컨텍스트)

            LLM Specifications:
                AntiPatterns:
                OutputSchema:
                Prerequisites:
                Freshness:
                Dataflow:
                TargetMarkets:
            """
            p.update(tid, description=v)

        def __call__(self):
            p.advance(tid)

    return p, _Bar()


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


class EdgarDocsNotApplicableError(ValueError):
    """지원 정기보고서(10-K/10-Q/20-F/40-F) filing 자체가 없는 ticker.

    폐쇄형 펀드(N-CSR), FDIC 제출 은행, unit/warrant/right 처럼 구조적으로 수집 대상이 아닌 경우다.
    수집 실패가 아니므로 batch 는 0 행 skip 으로 다룬다. 기존 ``except ValueError`` 호출자 호환을 위해
    ValueError 하위로 둔다.
    """


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
    """EDGAR 10-K/10-Q/20-F/40-F 문서를 수집하여 parquet 로 저장.

    Args:
        ticker: 종목 ticker.
        outPath: 저장 경로.
        sinceYear: 시작 연도 (기본 ``SINCE_YEAR``).
        maxFilings: 최대 filing 수. None 이면 무제한.
        filingTimeout: 단일 filing fetch 타임아웃 (초).
        showProgress: progress bar 표시 여부.
        sourceMode: ``"sec_api"`` (기본).
        strictQuality: 품질 게이트 strict 모드.

    Returns:
        저장된 parquet Path.

    Raises:
        EdgarDocsNotApplicableError: 지원 정기보고서 filing 이 없는 ticker (ValueError 하위).
        ValueError: section 추출 실패 (건너뛴 filing 수와 첫 사유 동행).

    Example:
        >>> fetchEdgarDocs("AAPL", Path("data/edgar/docs/AAPL.parquet"))
    """
    ticker = ticker.upper()
    meta = _resolveTickerMeta(ticker)
    submissions = _getSubmissions(meta["cik"])
    filings = _findFilings(submissions, sinceYear)

    if not filings:
        raise EdgarDocsNotApplicableError(f"{ticker} EDGAR docs filing 없음 (since {sinceYear})")

    from dartlab.core.messaging import emit

    if maxFilings is not None and len(filings) > maxFilings:
        filings = filings[-maxFilings:]
        emit("edgar:filing_limit", ticker=ticker, maxFilings=maxFilings)

    emit("edgar:docs_start", ticker=ticker, count=len(filings), sinceYear=sinceYear)

    rows: list[dict] = []
    panelTableRows: list[dict] = []
    filingIndex: list[dict] = []
    skippedFilings: list[str] = []
    skipReasons: list[str] = []
    if showProgress:
        _prog, _bar = _makeProgress(len(filings), f"EDGAR 원문 수집 | {ticker}")
        with _prog:
            _collectFilingRows(
                rows,
                filings,
                meta,
                ticker,
                _bar,
                filingTimeout,
                skippedFilings,
                panelTableRows=panelTableRows,
                filingIndex=filingIndex,
                skipReasons=skipReasons,
            )
    else:
        _collectFilingRows(
            rows,
            filings,
            meta,
            ticker,
            None,
            filingTimeout,
            skippedFilings,
            panelTableRows=panelTableRows,
            filingIndex=filingIndex,
            skipReasons=skipReasons,
        )

    if not rows:
        # 건너뛴 사유를 함께 남긴다. 사유 없이 "추출 실패" 만 남기면 전 ticker 가 같은 환경 결함
        # (예: worker thread 의 signal 등록 거부) 으로 실패해도 파서 문제처럼 보인다.
        detail = f" (건너뛴 filing {len(skipReasons)}/{len(filings)}, 첫 사유: {skipReasons[0]})" if skipReasons else ""
        raise ValueError(f"{ticker} EDGAR docs에서 section 추출 실패{detail}")

    # plan delegated-prancing-tower PR-E7b — 운영자 트리거 게이트.
    # DARTLAB_EDGAR_DOCS_DEPRECATED=1 환경변수 set 시 옛 docs.parquet emit 자동 skip.
    # 운영자는 PR-E7a 의 sectionsParityEdgar 가 4 주 연속 0 violations + D.1 회귀 0 +
    # viewer Playwright 0 + sync 14 일 무사고 모두 통과 확인 후 환경변수 set + 1 회 sync.
    # 그 시점부터 신 sections artifact 단독 운영. HF 의 옛 artifact 실제 삭제는 별 운영
    # 행동 (HF API curl) — 본 코드 path 외.
    import os as _os

    docsDeprecated = _os.environ.get("DARTLAB_EDGAR_DOCS_DEPRECATED", "").strip() in ("1", "true", "True")

    if not docsDeprecated:
        outPath.parent.mkdir(parents=True, exist_ok=True)
        df = pl.DataFrame(rows)
        summary = summarizeEdgarDocsFrame(df)
        if strictQuality:
            _assertEdgarDocsQuality(summary)
        df.write_parquet(outPath)
        if skippedFilings:
            emit("edgar:docs_skip", ticker=ticker, count=len(skippedFilings))
        emit("edgar:docs_save", path=str(outPath))
    else:
        emit("edgar:docs_skip_deprecated", ticker=ticker, reason="DARTLAB_EDGAR_DOCS_DEPRECATED=1")
        _log.info("docs.parquet emit skip (%s) — DARTLAB_EDGAR_DOCS_DEPRECATED gate active", ticker)

    # PR-E2 dual-write — sections artifact 도 동시 emit. emit 실패 시 옛 docs.parquet 만
    # 보존 (warning + 진행). PR-E7 안전 게이트 통과 전까지 옛 path 단독으로 fallback 가능.
    if panelTableRows:
        try:
            from dartlab.core.edgarBuild import emitIndexArtifact, emitPeriodArtifacts

            secResult = emitPeriodArtifacts(ticker, panelTableRows)
            emitIndexArtifact(ticker, filingIndex)
            emit(
                "edgar:sections_save",
                ticker=ticker,
                periodsWritten=secResult["periodsWritten"],
                totalRows=secResult["totalRows"],
            )
        except (OSError, ValueError, pl.exceptions.ComputeError) as exc:
            _log.warning("sections artifact emit 실패 (%s): %s — docs.parquet 만 유지", ticker, exc)

    return outPath


def summarizeEdgarDocsFrame(df: pl.DataFrame) -> dict[str, object]:
    """EDGAR docs DataFrame 의 품질 요약 통계.

    Args:
        df: fetchEdgarDocs 결과 DataFrame.

    Returns:
        ``rows_saved``/``filings_saved``/``forms_found``/``full_document_rows``/
        ``table_rows``/``quality_flags``/``form_metrics`` 키 dict.

    Raises:
        없음.

    Example:
        >>> summarizeEdgarDocsFrame(df)
    """
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
    pl.col("form_type").cast(pl.Utf8)

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
    """parquet 파일에서 EDGAR docs 품질 요약.

    Args:
        path: parquet 경로.

    Returns:
        ``summarizeEdgarDocsFrame`` 결과에 ``path``/``ticker`` 추가된 dict.

    Raises:
        FileNotFoundError: 경로 부재.

    Example:
        >>> summarizeEdgarDocsParquet(Path("data/edgar/docs/AAPL.parquet"))
    """
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
    panelTableRows: list[dict] | None = None,
    filingIndex: list[dict] | None = None,
    skipReasons: list[str] | None = None,
) -> None:
    """filing list 를 순회하면서 옛 rows (docs.parquet) + 신 panelTableRows (sections artifact) 동시 누적.

    plan delegated-prancing-tower PR-E2 — dual-write 강행. ``panelTableRows`` 가 None 이면
    옛 path 단독 (back-compat). non-None 이면 buildPanelTableRowsFromFiling 호출해 신
    sections artifact row 도 누적. raw HTML 은 ``html`` 변수에서 두 path 동시 활용.
    ``skipReasons`` 를 넘기면 건너뛴 filing 마다 "접수번호: 예외형: 메시지" 를 누적한다.
    """
    for filing in filings:
        if bar is not None:
            formType = filing.get("formType", "")
            filingDate = filing.get("filingDate", "")
            bar.title = f"EDGAR | {ticker} | {formType} {filingDate}"
        html: str | None = None
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
        except (httpx.HTTPError, TimeoutError, ValueError, AttributeError, KeyError, TypeError) as exc:
            skippedFilings.append(str(filing["accessionNumber"]))
            if skipReasons is not None:
                skipReasons.append(f"{filing['accessionNumber']}: {type(exc).__name__}: {exc}")
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

        # PR-E2 dual-write — sections artifact 신 path 동시 누적.
        if panelTableRows is not None and html is not None and items:
            from dartlab.core.edgarBuild import buildPanelTableRowsFromFiling

            sectionMeta = {
                "ticker": ticker,
                "cik": meta["cik"],
                "accession_no": filing["accessionNumber"],
                "filing_date": filing["filingDate"],
                "period_end": filing.get("periodEnd"),
                "form_type": filing["formType"],
                "report_type": reportType,
                "period_key": periodKey,
                "filing_url": filing["filingUrl"],
                "year": filing["year"],
            }
            try:
                secRows = buildPanelTableRowsFromFiling(
                    items=items,
                    rawHtml=html,
                    formType=filing["formType"],
                    meta=sectionMeta,
                )
                panelTableRows.extend(secRows)
                if filingIndex is not None:
                    filingIndex.append(sectionMeta)
            except (ValueError, AttributeError, OSError) as exc:
                _log.warning(
                    "sections artifact 빌드 실패 (%s %s): %s — docs.parquet 만 emit",
                    ticker,
                    filing["accessionNumber"],
                    exc,
                )

        if bar is not None:
            bar()


_HAS_SIGALRM = hasattr(signal, "SIGALRM")


class _FilingTimeout:
    """크로스 플랫폼 타임아웃 컨텍스트 매니저.

    SIGALRM 이 있는 플랫폼의 메인 스레드: signal.SIGALRM 으로 작업을 인터럽트한다.
    그 외 (Windows, 또는 batch 수집처럼 worker thread 에서 호출될 때): threading.Timer 폴백.
    메인 스레드 밖에서는 인터럽트할 수 없으므로 httpx 의 timeout 파라미터에 의존하고, 전체 작업
    타임아웃은 Timer 가 ``timedOut`` 플래그로 알린다.
    """

    def __init__(self, seconds: int):
        self.seconds = max(int(seconds), 0)
        self._previousHandler = None
        self._timer = None
        self._useAlarm = False
        self.timedOut = False

    def __enter__(self):
        if self.seconds <= 0:
            return self
        # signal.signal 은 메인 스레드 밖에서 ValueError 를 던진다. batchCollectEdgar 는 asyncio 를
        # worker thread 에서 돌리므로 여기서 가르지 않으면 filing 마다 ValueError 가 나 전부 skip 된다.
        self._useAlarm = _HAS_SIGALRM and threading.current_thread() is threading.main_thread()
        if self._useAlarm:
            self._previousHandler = signal.getsignal(signal.SIGALRM)
            signal.signal(signal.SIGALRM, self._handle)
            signal.alarm(self.seconds)
        else:
            self._timer = threading.Timer(self.seconds, self._markTimedOut)
            self._timer.daemon = True
            self._timer.start()
        return self

    def __exit__(self, _excType, exc, tb):
        if self.seconds > 0:
            if self._useAlarm:
                signal.alarm(0)
                if self._previousHandler is not None:
                    signal.signal(signal.SIGALRM, self._previousHandler)
            elif self._timer is not None:
                self._timer.cancel()
        return False

    def _markTimedOut(self):
        self.timedOut = True

    @staticmethod
    def _handle(_signum, frame):
        raise TimeoutError("filing fetch timed out")


def downloadListedEdgarDocs(
    *,
    limit: int = 2000,
    sinceYear: int = SINCE_YEAR,
    batchSize: int = BATCH_SIZE,
    cooldownSeconds: float = BATCH_COOLDOWN_SECONDS,
    skipExisting: bool = True,
) -> pl.DataFrame:
    """EDGAR 상장 기업 universe 전체에 대해 docs parquet 배치 수집.

    Args:
        limit: 최대 ticker 수.
        sinceYear: 시작 연도.
        batchSize: 배치 cooldown 단위 (이 수 단위로 sleep).
        cooldownSeconds: 배치 간 sleep 초.
        skipExisting: 기존 parquet 존재 시 skip 여부.

    Returns:
        ``ticker/status/reason`` 컬럼 결과 DataFrame.

    Raises:
        없음 (개별 ticker 실패는 status="failed" 로 기록).

    Example:
        >>> downloadListedEdgarDocs(limit=100)
    """
    from dartlab.core.dataLoader import _getDataRoot

    docsDir = _getDataRoot() / "edgar" / "docs"
    docsDir.mkdir(parents=True, exist_ok=True)

    universe = buildEdgarCollectibleUniverse(limit=limit, sinceYear=sinceYear)

    tickers = universe["ticker"].to_list()
    total = len(tickers)
    from dartlab.core.messaging import emit

    emit("edgar:batch_start", total=total, sinceYear=sinceYear)

    results: list[dict] = []
    successCount = 0
    failCount = 0
    _prog, _bar = _makeProgress(total, "EDGAR 배치 수집")
    with _prog:
        for idx, ticker in enumerate(tickers, start=1):
            _bar.title = f"EDGAR 배치 | {ticker}"
            outPath = docsDir / f"{ticker}.parquet"
            if skipExisting and outPath.exists():
                results.append({"ticker": ticker, "status": "skipped", "reason": "exists"})
                _bar()
                continue

            try:
                fetchEdgarDocs(ticker, outPath, sinceYear=sinceYear, showProgress=False)
                results.append({"ticker": ticker, "status": "downloaded", "reason": None})
                successCount += 1
                _bar.title = f"EDGAR 배치 | ✓ {ticker}"
            except (OSError, ValueError, httpx.HTTPError) as e:
                results.append({"ticker": ticker, "status": "failed", "reason": str(e)})
                failCount += 1
                _bar.title = f"EDGAR 배치 | ✗ {ticker}"
            finally:
                _bar()

            if batchSize > 0 and idx < total and idx % batchSize == 0:
                _log.info()
                emit("edgar:batch_progress", idx=idx, cooldown=cooldownSeconds)
                time.sleep(cooldownSeconds)

    emit("edgar:batch_done", success=successCount, failed=failCount, total=total)
    return pl.DataFrame(results)


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


def iterEdgarDocs(
    ticker: str,
    outPath: Path,
    *,
    sinceYear: int = SINCE_YEAR,
    maxFilings: int | None = None,
    filingTimeout: int = FILING_TIMEOUT_SECONDS,
    showProgress: bool = True,
    sourceMode: str = "sec_api",
    strictQuality: bool = False,
):
    """``fetchEdgarDocs`` 의 iterator pair (룰 10).

    ``fetchEdgarDocs`` 가 parquet 한 번 빌드하는 것과 달리, ``iterEdgarDocs`` 는 결과 parquet
    을 row 단위로 yield. 호출자가 메모리 전체 로드 없이 streaming 가능.

    Args:
        ticker: SEC ticker.
        outPath: 결과 parquet 경로.
        sinceYear: 시작 연도.
        maxFilings: 최대 filings 수.
        filingTimeout: filing 별 timeout (초).
        showProgress: 진행 표시.
        sourceMode: 소스 모드.
        strictQuality: 품질 검증 strict.

    Yields:
        섹션 row dict.

    Raises:
        ValueError: filing 부재 또는 section 추출 실패 (``fetchEdgarDocs`` 위임).

    Example:
        >>> for row in iterEdgarDocs("AAPL", Path("apple.parquet"), maxFilings=5):
        ...     print(row.get("section_title"))
    """
    fetchEdgarDocs(
        ticker,
        outPath,
        sinceYear=sinceYear,
        maxFilings=maxFilings,
        filingTimeout=filingTimeout,
        showProgress=showProgress,
        sourceMode=sourceMode,
        strictQuality=strictQuality,
    )
    if not outPath.exists():
        return
    df = pl.read_parquet(outPath)
    yield from df.iter_rows(named=True)


# ── 재내보내기 (분리: fetchHtmlParse.py · fetchUniverse.py) ──────
from dartlab.gather.edgar.docs.fetchHtmlParse import (  # noqa: E402  re-export
    _classify40FDocumentName,
    _cleanQuarterlySectionText,
    _downloadFilingSource,
    _downloadHtml,
    _extractItemHeaders,
    _filingDirectoryUrl,
    _filingIndexJsonUrl,
    _htmlToText,
    _isLowQualityText,
    _listFilingHtmlDocuments,
    _quarterlyBodyText,
    _split40FPrimaryText,
    _split40FSections,
    _splitItems,
    _splitQuarterlyItems,
    _splitTableStructuredItems,
    _submissionTextUrl,
    _tableToMarkdown,
)
from dartlab.gather.edgar.docs.fetchUniverse import (  # noqa: E402  re-export
    _appendJsonl,
    _emptyCollectibleUniverseCache,
    _findFilings,
    _getSubmissions,
    _loadCollectibleUniverseCache,
    _mergeCollectibleUniverseCache,
    _mergeFilingArrays,
    _resolveTickerMeta,
    buildEdgarCollectibleUniverse,
    prepareEdgarCollectibleUniverse,
)
