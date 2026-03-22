"""
실험 ID: 057-017
실험명: SEC master.idx 기반 bulk 스트리밍 docs 수집

목적:
- master.idx를 읽으면서 바로 filing을 처리한다.
- manifest 파일을 따로 저장하지 않고, 대표 종목 중심으로 docs parquet를 즉시 append한다.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import polars as pl
import requests
from alive_progress import alive_bar

from dartlab import config
from dartlab.core.dataLoader import loadEdgarListedUniverse
from dartlab.engines.company.edgar.docs.fetch import (
    _FilingTimeout,
    _htmlToText,
    _periodKey,
    _reportType,
    _split40FSections,
    _splitItems,
)

HEADERS = {"User-Agent": "DartLab eddmpython@gmail.com"}
SUPPORTED_FORMS = {"10-K", "10-Q", "20-F", "40-F"}
START_YEAR = 2009
FILING_TIMEOUT_SECONDS = 45
PRIORITY_TICKERS = (
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "NFLX", "COST",
    "AVGO", "AMD", "ADBE", "CSCO", "INTC", "QCOM", "AMGN", "TXN", "INTU",
    "CMCSA", "PEP", "SBUX", "BKNG", "AMAT", "ADP", "GILD", "VRTX", "ISRG",
    "PANW", "SNPS", "CDNS", "CRWD", "SHOP", "UBER", "MU", "LRCX", "ADI",
    "PYPL", "ABNB", "MAR", "MELI",
    "JPM", "BAC", "WFC", "GS", "MS", "BRK-B", "V", "MA", "AXP",
    "XOM", "CVX", "COP", "SLB",
    "UNH", "JNJ", "LLY", "MRK", "ABBV", "PFE",
    "WMT", "HD", "LOW", "KO", "PG", "MCD", "DIS", "NKE",
    "TSM", "TM", "BABA", "AG", "O",
)


def _quarter_refs(start_year: int) -> list[tuple[int, int]]:
    now = datetime.now(UTC)
    current_quarter = ((now.month - 1) // 3) + 1
    refs: list[tuple[int, int]] = []
    for year in range(start_year, now.year + 1):
        max_quarter = current_quarter if year == now.year else 4
        for quarter in range(1, max_quarter + 1):
            refs.append((year, quarter))
    return refs


def _master_idx_url(year: int, quarter: int) -> str:
    return f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/master.idx"


def _fetch_master_idx(year: int, quarter: int) -> str:
    response = requests.get(_master_idx_url(year, quarter), headers=HEADERS, timeout=60)
    response.raise_for_status()
    return response.text


def _build_priority_ticker_map() -> dict[str, dict[str, str]]:
    df = (
        loadEdgarListedUniverse()
        .filter(pl.col("ticker").is_in(PRIORITY_TICKERS))
        .select(["cik", "ticker", "title"])
        .sort(["cik", "ticker"])
    )
    rows = df.to_dicts()
    mapping: dict[str, dict[str, str]] = {}
    for row in rows:
        cik = str(row["cik"]).zfill(10)
        ticker = str(row["ticker"]).upper()
        current = mapping.get(cik)
        if current is None or len(ticker) < len(current["ticker"]):
            mapping[cik] = {
                "ticker": ticker,
                "company_name": str(row["title"] or "").strip(),
            }
    return mapping


def _parse_master_idx(text: str, cik_map: dict[str, dict[str, str]]) -> list[dict]:
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.startswith("CIK|Company Name|Form Type|Date Filed|Filename"))
    except StopIteration:
        return []

    rows: list[dict] = []
    for line in lines[start + 2:]:
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) != 5:
            continue
        cik, company_name, form_type, filing_date, filename = parts
        cik = cik.zfill(10)
        if form_type not in SUPPORTED_FORMS or cik not in cik_map:
            continue
        meta = cik_map[cik]
        accession_no = Path(filename).name.replace(".txt", "")
        rows.append({
            "ticker": meta["ticker"],
            "cik": cik,
            "company_name": meta["company_name"] or company_name,
            "form_type": form_type,
            "filing_date": filing_date,
            "accession_no": accession_no,
            "filing_url": f"https://www.sec.gov/Archives/{filename}",
            "year": filing_date[:4],
        })
    return rows


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _existing_accessions(path: Path) -> set[str]:
    if not path.exists():
        return set()
    df = pl.read_parquet(path, columns=["accession_no"])
    return {str(value) for value in df["accession_no"].drop_nulls().to_list()}


def _append_rows(path: Path, rows: list[dict]) -> None:
    new_df = pl.DataFrame(rows)
    if path.exists():
        current_df = pl.read_parquet(path)
        merged = pl.concat([current_df, new_df], how="vertical_relaxed")
        merged = merged.unique(subset=["accession_no", "section_order", "section_title"], keep="first")
    else:
        merged = new_df
    path.parent.mkdir(parents=True, exist_ok=True)
    merged.write_parquet(path)


def _collect_rows(filing: dict) -> list[dict]:
    with _FilingTimeout(FILING_TIMEOUT_SECONDS):
        response = requests.get(filing["filing_url"], headers=HEADERS, timeout=60)
        response.raise_for_status()
        text = _htmlToText(response.text)
        if filing["form_type"] == "40-F":
            items = _split40FSections({
                "formType": filing["form_type"],
                "filingUrl": filing["filing_url"],
                "accessionNumber": filing["accession_no"],
                "year": filing["year"],
                "filingDate": filing["filing_date"],
            }, text)
        else:
            items = _splitItems(text, filing["form_type"])

    report_type = _reportType(filing["form_type"], None)
    period_key = _periodKey(filing["form_type"], None, filing["year"])
    rows: list[dict] = []
    for order, item in enumerate(items):
        rows.append({
            "cik": filing["cik"],
            "company_name": filing["company_name"],
            "ticker": filing["ticker"],
            "year": filing["year"],
            "filing_date": filing["filing_date"],
            "period_end": None,
            "accession_no": filing["accession_no"],
            "form_type": filing["form_type"],
            "report_type": report_type,
            "period_key": period_key,
            "section_order": order,
            "section_title": item["title"],
            "filing_url": filing["filing_url"],
            "section_content": item["content"],
        })
    return rows


def main() -> None:
    docs_dir = Path(config.dataDir) / "edgar" / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    progress_path = Path(__file__).parent / "output" / "streamMasterIndex.progress.jsonl"

    cik_map = _build_priority_ticker_map()
    refs = _quarter_refs(START_YEAR)
    print(f"[057-017] priority tickers={len(set(PRIORITY_TICKERS))} mapped ciks={len(cik_map)} quarters={len(refs)}")

    with alive_bar(len(refs), title="057 master.idx stream") as bar:
        for year, quarter in refs:
            filings = _parse_master_idx(_fetch_master_idx(year, quarter), cik_map)
            for filing in filings:
                out_path = docs_dir / f"{filing['ticker']}.parquet"
                if filing["accession_no"] in _existing_accessions(out_path):
                    continue
                try:
                    rows = _collect_rows(filing)
                    if not rows:
                        raise ValueError("empty rows")
                    _append_rows(out_path, rows)
                    _append_jsonl(progress_path, {
                        "ticker": filing["ticker"],
                        "accession_no": filing["accession_no"],
                        "filing_date": filing["filing_date"],
                        "form_type": filing["form_type"],
                        "status": "downloaded",
                        "rows_saved": len(rows),
                        "path": str(out_path),
                    })
                except Exception as exc:
                    _append_jsonl(progress_path, {
                        "ticker": filing["ticker"],
                        "accession_no": filing["accession_no"],
                        "filing_date": filing["filing_date"],
                        "form_type": filing["form_type"],
                        "status": "failed",
                        "reason": str(exc),
                    })
            bar()


if __name__ == "__main__":
    main()
