"""EDGAR submissions wrapper."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

import polars as pl

from dartlab.engines.edgar.openapi.client import DEFAULT_BASE_URL, EdgarClient

SUPPORTED_REGULAR_FORMS = ("10-K", "10-Q", "20-F", "40-F")


def getSubmissionsJson(cik: str, client: EdgarClient | None = None) -> dict[str, Any]:
    api = client or EdgarClient()
    normalized = str(cik).zfill(10)
    return api.getJson(f"{DEFAULT_BASE_URL}/submissions/CIK{normalized}.json")


def mergeSubmissionFilings(
    submissions: dict[str, Any],
    *,
    sinceYear: int = 2009,
    client: EdgarClient | None = None,
) -> dict[str, list[Any]]:
    recent = submissions.get("filings", {}).get("recent", {})
    merged = {k: list(v) for k, v in recent.items()}
    api = client or EdgarClient()

    for fileInfo in submissions.get("filings", {}).get("files", []):
        filingTo = str(fileInfo.get("filingTo") or "")
        if filingTo and filingTo[:4].isdigit() and int(filingTo[:4]) < sinceYear:
            continue
        name = str(fileInfo.get("name") or "")
        if not name:
            continue
        extra = api.getJson(f"{DEFAULT_BASE_URL}/submissions/{name}")
        for key in merged:
            if key in extra:
                merged[key].extend(extra[key])
    return merged


def _coerceDateBound(value: str | date | datetime | None, *, end: bool) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()

    text = str(value).strip()
    if not text:
        return None
    if re.fullmatch(r"\d{4}", text):
        return f"{text}-12-31" if end else f"{text}-01-01"
    if re.fullmatch(r"\d{4}-\d{2}", text):
        return f"{text}-31" if end else f"{text}-01"
    return text


def findRegularFilings(
    submissions: dict[str, Any],
    *,
    sinceYear: int = 2009,
    forms: list[str] | tuple[str, ...] | None = None,
    since: str | date | datetime | None = None,
    until: str | date | datetime | None = None,
    client: EdgarClient | None = None,
) -> list[dict[str, Any]]:
    merged = mergeSubmissionFilings(submissions, sinceYear=sinceYear, client=client)
    reportDates = merged.get("reportDate", [""] * len(merged.get("form", [])))
    acceptanceDates = merged.get("acceptanceDateTime", [""] * len(merged.get("form", [])))
    descriptions = merged.get("primaryDocDescription", [""] * len(merged.get("form", [])))
    formSet = {form.upper() for form in forms} if forms else None
    sinceBound = _coerceDateBound(since, end=False)
    untilBound = _coerceDateBound(until, end=True)
    cik = str(submissions.get("cik") or "").zfill(10)

    rows: list[dict[str, Any]] = []
    for idx, formType in enumerate(merged.get("form", [])):
        formText = str(formType or "")
        if formText not in SUPPORTED_REGULAR_FORMS:
            continue
        if formSet is not None and formText.upper() not in formSet:
            continue

        filingDate = str(merged.get("filingDate", [None])[idx] or "")
        if len(filingDate) < 4 or not filingDate[:4].isdigit():
            continue
        if int(filingDate[:4]) < sinceYear:
            continue
        if sinceBound is not None and filingDate < sinceBound:
            continue
        if untilBound is not None and filingDate > untilBound:
            continue

        accession = str(merged.get("accessionNumber", [None])[idx] or "")
        primaryDocument = str(merged.get("primaryDocument", [None])[idx] or "")
        accessionNoDash = accession.replace("-", "")
        filingDir = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accessionNoDash}"
        rows.append(
            {
                "cik": cik,
                "form": formText,
                "filing_date": filingDate,
                "report_date": reportDates[idx] or None,
                "acceptance_datetime": acceptanceDates[idx] or None,
                "accession_no": accession,
                "primary_document": primaryDocument or None,
                "primary_doc_description": descriptions[idx] or None,
                "filing_url": f"{filingDir}/{primaryDocument}" if primaryDocument else filingDir,
                "filing_index_url": f"{filingDir}/index.json",
                "year": filingDate[:4],
            }
        )

    rows.sort(key=lambda row: (row["filing_date"], row["form"], row["accession_no"]))
    return rows


def filingsFrame(
    submissions: dict[str, Any],
    *,
    ticker: str | None = None,
    title: str | None = None,
    sinceYear: int = 2009,
    forms: list[str] | tuple[str, ...] | None = None,
    since: str | date | datetime | None = None,
    until: str | date | datetime | None = None,
    client: EdgarClient | None = None,
) -> pl.DataFrame:
    rows = findRegularFilings(
        submissions,
        sinceYear=sinceYear,
        forms=forms,
        since=since,
        until=until,
        client=client,
    )
    if not rows:
        return pl.DataFrame(
            schema={
                "ticker": pl.Utf8,
                "cik": pl.Utf8,
                "title": pl.Utf8,
                "form": pl.Utf8,
                "filing_date": pl.Utf8,
                "report_date": pl.Utf8,
                "accession_no": pl.Utf8,
                "primary_document": pl.Utf8,
                "primary_doc_description": pl.Utf8,
                "filing_url": pl.Utf8,
                "filing_index_url": pl.Utf8,
                "year": pl.Utf8,
            }
        )

    df = pl.DataFrame(rows)
    return df.with_columns(
        [
            pl.lit((ticker or "")).alias("ticker"),
            pl.lit((title or "")).alias("title"),
        ]
    ).select(
        [
            "ticker",
            "cik",
            "title",
            "form",
            "filing_date",
            "report_date",
            "accession_no",
            "primary_document",
            "primary_doc_description",
            "filing_url",
            "filing_index_url",
            "year",
        ]
    )
