"""EDGAR docs 원문 수집기.

로컬/릴리즈에 parquet가 없을 때 SEC EDGAR API와 원문 HTML에서 직접 수집한다.
저장 포맷은 EDGAR 메타를 최대한 보존하고, 비교용 필드는 함께 저장한다.
"""

from __future__ import annotations

import re
import time
import warnings
from pathlib import Path

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
BATCH_SIZE = 25
BATCH_COOLDOWN_SECONDS = 8.0

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
PART_PATTERN = re.compile(r"^\s*PART\s+(I|II)\b", re.IGNORECASE | re.MULTILINE)
ITEM_LINE_PATTERN = re.compile(r"^\s*Item\s+(\d+[A-K]?)\.\s*(.*)$", re.IGNORECASE)


def fetchEdgarDocs(
    ticker: str,
    outPath: Path,
    *,
    sinceYear: int = SINCE_YEAR,
    maxFilings: int | None = None,
    showProgress: bool = True,
) -> Path:
    ticker = ticker.upper()
    meta = _resolveTickerMeta(ticker)
    submissions = _getSubmissions(meta["cik"])
    filings = _findFilings(submissions, sinceYear)

    if not filings:
        raise ValueError(f"{ticker} EDGAR docs filing 없음 (since {sinceYear})")

    if maxFilings is not None and len(filings) > maxFilings:
        filings = filings[-maxFilings:]
        print(f"[dartlab] {ticker} filing 수가 많아 최근 {maxFilings}건만 수집")

    print(f"[dartlab] {ticker} EDGAR docs 원문 수집 시작 ({len(filings)} filings, since {sinceYear})")

    rows: list[dict] = []
    if showProgress:
        with alive_bar(len(filings), title="EDGAR 원문 수집") as bar:
            _collectFilingRows(rows, filings, meta, ticker, bar)
    else:
        _collectFilingRows(rows, filings, meta, ticker, None)

    if not rows:
        raise ValueError(f"{ticker} EDGAR docs에서 section 추출 실패")

    outPath.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows).write_parquet(outPath)
    print(f"[dartlab] 저장 완료: {outPath}")
    return outPath


def _collectFilingRows(
    rows: list[dict],
    filings: list[dict],
    meta: dict[str, str],
    ticker: str,
    bar,
) -> None:
    for filing in filings:
        html = _downloadHtml(filing["filingUrl"])
        text = _htmlToText(html)
        items = _splitItems(text, filing["formType"])

        reportType = _reportType(filing["formType"], filing.get("periodEnd"))
        periodKey = _periodKey(filing["formType"], filing.get("periodEnd"), filing["year"])
        for order, item in enumerate(items):
            rows.append({
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
            })
        if bar is not None:
            bar()


def downloadListedEdgarDocs(
    *,
    limit: int = 2000,
    sinceYear: int = SINCE_YEAR,
    batchSize: int = BATCH_SIZE,
    cooldownSeconds: float = BATCH_COOLDOWN_SECONDS,
    skipExisting: bool = True,
) -> pl.DataFrame:
    from dartlab import config
    from dartlab.core.dataLoader import loadEdgarListedUniverse

    docsDir = Path(config.dataDir) / "edgar" / "docs"
    docsDir.mkdir(parents=True, exist_ok=True)

    universe = (
        loadEdgarListedUniverse()
        .filter(pl.col("is_exchange_listed"))
        .select(["ticker", "cik", "title", "exchange"])
        .sort("ticker")
    )
    if limit > 0:
        universe = universe.head(limit)

    tickers = universe["ticker"].to_list()
    total = len(tickers)
    print(f"[dartlab] EDGAR docs 배치 수집 시작 ({total} tickers, since {sinceYear})")

    results: list[dict] = []
    with alive_bar(total, title="EDGAR docs 배치 수집") as bar:
        for idx, ticker in enumerate(tickers, start=1):
            outPath = docsDir / f"{ticker}.parquet"
            if skipExisting and outPath.exists():
                results.append({"ticker": ticker, "status": "skipped", "reason": "exists"})
                bar()
                continue

            try:
                fetchEdgarDocs(ticker, outPath, sinceYear=sinceYear)
                results.append({"ticker": ticker, "status": "downloaded", "reason": None})
            except (OSError, ValueError, requests.RequestException) as e:
                results.append({"ticker": ticker, "status": "failed", "reason": str(e)})
            finally:
                bar()

            if batchSize > 0 and idx < total and idx % batchSize == 0:
                print(f"\n[dartlab] {idx}건 처리 완료 → {cooldownSeconds:.1f}초 휴지")
                time.sleep(cooldownSeconds)

    return pl.DataFrame(results)


def _resolveTickerMeta(ticker: str) -> dict[str, str]:
    from dartlab import config
    from dartlab.core.dataLoader import loadEdgarListedUniverse

    tickerPath = Path(config.dataDir) / "edgar" / "tickers.parquet"
    try:
        listedDf = loadEdgarListedUniverse()
        listedRow = listedDf.filter(pl.col("ticker") == ticker)
        if not listedRow.is_empty():
            record = listedRow.row(0, named=True)
            return {
                "ticker": ticker,
                "cik": str(record["cik"]).zfill(10),
                "title": record.get("title") or ticker,
            }
    except OSError:
        pass

    if tickerPath.exists():
        df = pl.read_parquet(tickerPath)
        row = df.filter(pl.col("ticker") == ticker)
        if row.is_empty():
            row = df.filter(pl.col("ticker") == ticker.upper())
        if not row.is_empty():
            record = row.row(0, named=True)
            return {
                "ticker": ticker,
                "cik": str(record["cik"]).zfill(10),
                "title": record.get("title") or ticker,
            }

    time.sleep(REQUEST_INTERVAL)
    resp = requests.get("https://www.sec.gov/files/company_tickers.json", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    for record in payload.values():
        if str(record.get("ticker", "")).upper() == ticker:
            return {
                "ticker": ticker,
                "cik": str(record["cik_str"]).zfill(10),
                "title": record.get("title") or ticker,
            }
    raise ValueError(f"{ticker}에 해당하는 CIK를 찾을 수 없음")


def _getSubmissions(cik: str) -> dict:
    time.sleep(REQUEST_INTERVAL)
    resp = requests.get(f"{DATA_URL}/submissions/CIK{cik}.json", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _mergeFilingArrays(submissions: dict, sinceYear: int) -> dict:
    recent = submissions["filings"]["recent"]
    merged = {k: list(v) for k, v in recent.items()}

    for fileInfo in submissions["filings"].get("files", []):
        filingTo = fileInfo.get("filingTo", "")
        if filingTo and int(filingTo[:4]) < sinceYear:
            continue
        time.sleep(REQUEST_INTERVAL)
        resp = requests.get(f"{DATA_URL}/submissions/{fileInfo['name']}", headers=HEADERS, timeout=30)
        resp.raise_for_status()
        extra = resp.json()
        for key in merged:
            if key in extra:
                merged[key].extend(extra[key])
    return merged


def _findFilings(submissions: dict, sinceYear: int) -> list[dict]:
    merged = _mergeFilingArrays(submissions, sinceYear)
    reportDates = merged.get("reportDate", [""] * len(merged["form"]))
    rows: list[dict] = []

    for i, formType in enumerate(merged["form"]):
        if formType not in ("10-K", "10-Q", "20-F"):
            continue
        filingDate = merged["filingDate"][i]
        year = int(filingDate[:4])
        if year < sinceYear:
            continue

        accession = merged["accessionNumber"][i]
        primaryDoc = merged["primaryDocument"][i]
        rows.append({
            "formType": formType,
            "filingDate": filingDate,
            "year": str(year),
            "periodEnd": reportDates[i] or None,
            "accessionNumber": accession,
            "filingUrl": (
                f"{BASE_URL}/Archives/edgar/data/{submissions['cik']}/{accession.replace('-', '')}/{primaryDoc}"
            ),
        })

    rows.sort(key=lambda row: (row["filingDate"], row["formType"]))
    return rows


def _downloadHtml(url: str) -> str:
    time.sleep(REQUEST_INTERVAL)
    resp = requests.get(url, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    return resp.text


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
    text = soup.get_text()
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _splitItems(text: str, formType: str) -> list[dict]:
    if formType == "10-Q":
        return _splitQuarterlyItems(text)

    itemNames = ITEM_NAMES_20F if formType == "20-F" else ITEM_NAMES_10K
    matches = list(ITEM_PATTERN.finditer(text))
    if not matches:
        return [{"title": "Full Document", "content": text}]

    seen = set()
    items = []
    for i, match in enumerate(matches):
        itemNum = match.group(1).upper()
        if itemNum in seen:
            continue
        seen.add(itemNum)
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        canonTitle = itemNames.get(itemNum, match.group(2).strip().rstrip("."))
        items.append({
            "title": f"Item {itemNum}. {canonTitle}",
            "content": text[start:end].strip(),
        })
    return items


def _splitQuarterlyItems(text: str) -> list[dict]:
    body = _quarterlyBodyText(text)
    if not body:
        return [{"title": "Full Document", "content": text}]

    starts: list[dict[str, int | str]] = []
    currentPart: str | None = None
    offset = 0
    seen: set[tuple[str, str]] = set()

    for line in body.splitlines(keepends=True):
        stripped = line.strip()
        if not stripped:
            offset += len(line)
            continue
        if "|" in stripped:
            offset += len(line)
            continue

        partMatch = PART_PATTERN.match(stripped)
        if partMatch:
            currentPart = partMatch.group(1).upper()
            offset += len(line)
            continue

        itemMatch = ITEM_LINE_PATTERN.match(stripped)
        if itemMatch and currentPart is not None:
            itemNum = itemMatch.group(1).upper()
            key = (currentPart, itemNum)
            canonicalTitle = ITEM_NAMES_10Q.get(f"{currentPart}:{itemNum}")
            if canonicalTitle and key not in seen:
                starts.append({
                    "part": currentPart,
                    "item_num": itemNum,
                    "start": offset,
                    "title": f"Part {currentPart} - Item {itemNum}. {canonicalTitle}",
                })
                seen.add(key)
        offset += len(line)

    if len(starts) < 2:
        return [{"title": "Full Document", "content": body}]

    items: list[dict] = []
    for idx, startInfo in enumerate(starts):
        start = int(startInfo["start"])
        end = int(starts[idx + 1]["start"]) if idx + 1 < len(starts) else len(body)
        content = _cleanQuarterlySectionText(body[start:end].strip())
        if not content:
            continue
        items.append({
            "title": str(startInfo["title"]),
            "content": content,
        })

    if len(items) < 2:
        return [{"title": "Full Document", "content": body}]
    return items


def _quarterlyBodyText(text: str) -> str:
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if "|" in stripped:
            continue
        if re.match(r"^PART\s+I\b", stripped, re.IGNORECASE):
            return "\n".join(lines[idx:]).strip()
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
            if formType in ("10-K", "20-F"):
                return pYear
            if formType == "10-Q":
                if month == "03":
                    return f"{pYear}Q1"
                if month == "06":
                    return f"{pYear}Q2"
                if month == "09":
                    return f"{pYear}Q3"
    if formType in ("10-K", "20-F"):
        return str(year)
    return None
