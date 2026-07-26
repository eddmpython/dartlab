"""EDGAR OpenAPI saver."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import polars as pl

import dartlab.config as _dartlabConfig
from dartlab.core.dataConfig import DATA_RELEASES
from dartlab.core.dataLoader import loadEdgarListedUniverse
from dartlab.core.edgarClient import (
    EDGAR_COMPANYFACTS_SCHEMA,
    EdgarClient,
    companyFactsToRows,
    getCompanyFactsJson,
    loadTickers,
)
from dartlab.core.polarsUtil import isEmptyDf
from dartlab.gather.edgar.docs.fetch import fetchEdgarDocs

EDGAR_DOCS_SCHEMA = {
    "cik": pl.Utf8,
    "company_name": pl.Utf8,
    "ticker": pl.Utf8,
    "year": pl.Utf8,
    "filing_date": pl.Utf8,
    "period_end": pl.Utf8,
    "accession_no": pl.Utf8,
    "form_type": pl.Utf8,
    "report_type": pl.Utf8,
    "period_key": pl.Utf8,
    "section_order": pl.Int64,
    "section_title": pl.Utf8,
    "filing_url": pl.Utf8,
    "section_content": pl.Utf8,
}


def _dataPath(category: str, key: str) -> Path:
    subDir = DATA_RELEASES[category]["dir"]
    dest = Path(_dartlabConfig.dataDir) / subDir / f"{key}.parquet"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


def _tempPath(dest: Path) -> Path:
    token = uuid.uuid4().hex[:8]
    return dest.with_name(f"{dest.stem}.tmp-{token}{dest.suffix}")


def _backupPath(dest: Path) -> Path:
    token = uuid.uuid4().hex[:8]
    return dest.with_name(f"{dest.stem}.bak-{token}{dest.suffix}")


def _validateSchema(df: pl.DataFrame, schema: dict[str, pl.DataType], *, label: str) -> None:
    expectedCols = list(schema.keys())
    actualCols = list(df.columns)
    if actualCols != expectedCols:
        raise ValueError(f"{label} schema mismatch: columns {actualCols} != {expectedCols}; overwrite prevented")

    for col, dtype in schema.items():
        actual = df.schema.get(col)
        if actual != dtype:
            raise ValueError(f"{label} schema mismatch: column {col} dtype {actual} != {dtype}; overwrite prevented")


def _ensureIdentityCaches(client: EdgarClient | None = None) -> None:
    try:
        loadEdgarListedUniverse(forceUpdate=False)
    except (FileNotFoundError, OSError, RuntimeError):
        pass
    loadTickers(client, refresh=False)


def _replaceWithValidation(
    tempPath: Path,
    dest: Path,
    *,
    validator,
) -> Path:
    backupPath: Path | None = None
    try:
        if dest.exists():
            backupPath = _backupPath(dest)
            os.replace(dest, backupPath)
        os.replace(tempPath, dest)
        validator(dest)
        if backupPath is not None and backupPath.exists():
            backupPath.unlink()
        return dest
    except (OSError, ValueError, RuntimeError):
        if dest.exists():
            dest.unlink()
        if backupPath is not None and backupPath.exists():
            os.replace(backupPath, dest)
        raise
    finally:
        if tempPath.exists():
            tempPath.unlink()
        if backupPath is not None and backupPath.exists():
            backupPath.unlink()


def _validateSavedDocsParquet(path: Path, ticker: str) -> None:
    from dartlab.core.edgarBuild import sections

    df = pl.read_parquet(path)
    _validateSchema(df, EDGAR_DOCS_SCHEMA, label="edgarDocs")

    sec = sections(ticker)
    if isEmptyDf(sec):
        raise ValueError("edgarDocs consumer smoke check failed: sections() returned empty; overwrite prevented")


def _validateSavedFinanceParquet(path: Path, cik: str) -> None:
    from dartlab.core.edgarBuild import buildTimeseries

    df = pl.read_parquet(path)
    _validateSchema(df, EDGAR_COMPANYFACTS_SCHEMA, label="edgarFinance")

    ts = buildTimeseries(cik, edgarDir=path.parent)
    if ts is None:
        raise ValueError(
            "edgarFinance consumer smoke check failed: buildTimeseries() returned None; overwrite prevented"
        )


def verifyOpenEdgarSaveCompatibility(ticker: str) -> dict[str, object]:
    """저장된 EDGAR 데이터가 Company 파이프라인과 호환되는지 검증.

    Args:
        ticker: 종목 ticker.

    Returns:
        ``ticker/corpName/hasTimeseries/...`` 검증 결과 dict.

    Raises:
        ValueError: ticker resolve 실패.

    Example:
        >>> verifyOpenEdgarSaveCompatibility("AAPL")

    SeeAlso:
        - ``saveFinance`` / ``saveDocs`` — 본 모듈 saver 함수.
        - ``EDGAR_COMPANYFACTS_SCHEMA`` / ``EDGAR_DOCS_SCHEMA`` — 정규화 schema.

    Requires:
        - dartlab
        - polars
        - uuid

    Capabilities:
        - SEC companyfacts / docs → parquet 저장 + dartlab Company API 호환 검증. ticker→cik 변환.

    Guide:
        - 운영자 수집 파이프라인 — 사용자 API 직접 호출 X.

    AIContext:
        internal saver — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - User-Agent 미설정 → 403.
            - 저장 경로 명시 X → 기본 dataDir.
        OutputSchema:
            - Path / pl.DataFrame — 함수별.
        Prerequisites:
            - 인터넷 + SEC API + ticker/cik.
        Freshness:
            - SEC EDGAR 실시간.
        Dataflow:
            - ticker → SEC API → 정규화 + 저장 → parquet.
        TargetMarkets:
            - US (SEC EDGAR) saver.
    """
    from dartlab.core.edgarBuild import edgarCompany

    company = edgarCompany(ticker)
    docsSections = company._docs.sections
    financeBs = company._finance.BS
    indexDf = company.index
    docTopics = []
    if indexDf is not None and "source" in indexDf.columns and "topic" in indexDf.columns:
        docTopics = (
            indexDf.filter(pl.col("source") == "docs").select("topic").to_series().to_list()
            if indexDf.height > 0
            else []
        )
    sampleDocTopic = str(docTopics[0]) if docTopics else None
    sampleDocShow = company._showImpl(sampleDocTopic) if sampleDocTopic else None
    sampleDocTrace = company.trace(sampleDocTopic) if sampleDocTopic else None
    bsTrace = company.trace("BS")
    return {
        "ticker": ticker.upper(),
        "corpName": company.corpName,
        "hasTimeseries": company.panel("IS") is not None,
        "docsSectionsShape": None if docsSections is None else docsSections.shape,
        "financeBsShape": None if financeBs is None else financeBs.shape,
        "indexShape": indexDf.shape,
        "sampleDocTopic": sampleDocTopic,
        "sampleDocShowShape": None if sampleDocShow is None else sampleDocShow.shape,
        "sampleDocTrace": sampleDocTrace,
        "bsTrace": bsTrace,
    }


def saveDocs(
    ticker: str,
    *,
    client: EdgarClient | None = None,
    sinceYear: int = 2009,
) -> Path:
    """10-K/10-Q 문서를 SEC 에서 수집하여 검증 후 parquet 로 저장.

    Args:
        ticker: 종목 ticker.
        client: EdgarClient 인스턴스.
        sinceYear: 시작 연도.

    Returns:
        저장된 parquet Path.

    Raises:
        ValueError: filing 부재 (``fetchEdgarDocs`` 위임).

    Example:
        >>> saveDocs("AAPL", sinceYear=2020)

    SeeAlso:
        - ``saveFinance`` / ``saveDocs`` — 본 모듈 saver 함수.
        - ``EDGAR_COMPANYFACTS_SCHEMA`` / ``EDGAR_DOCS_SCHEMA`` — 정규화 schema.

    Requires:
        - dartlab
        - polars
        - uuid

    Capabilities:
        - SEC companyfacts / docs → parquet 저장 + dartlab Company API 호환 검증. ticker→cik 변환.

    Guide:
        - 운영자 수집 파이프라인 — 사용자 API 직접 호출 X.

    AIContext:
        internal saver — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - User-Agent 미설정 → 403.
            - 저장 경로 명시 X → 기본 dataDir.
        OutputSchema:
            - Path / pl.DataFrame — 함수별.
        Prerequisites:
            - 인터넷 + SEC API + ticker/cik.
        Freshness:
            - SEC EDGAR 실시간.
        Dataflow:
            - ticker → SEC API → 정규화 + 저장 → parquet.
        TargetMarkets:
            - US (SEC EDGAR) saver.
    """
    normalized = str(ticker).upper().strip()
    _ensureIdentityCaches(client)
    dest = _dataPath("edgarDocs", normalized)
    tempPath = _tempPath(dest)
    fetchEdgarDocs(normalized, tempPath, sinceYear=sinceYear)
    return _replaceWithValidation(
        tempPath,
        dest,
        validator=lambda finalPath: _validateSavedDocsParquet(finalPath, normalized),
    )


def saveFinance(
    cik: str,
    *,
    client: EdgarClient | None = None,
) -> Path:
    """XBRL companyfacts 를 SEC 에서 수집하여 검증 후 parquet 로 저장.

    Args:
        cik: SEC CIK 번호.
        client: EdgarClient 인스턴스.

    Returns:
        저장된 parquet Path.

    Raises:
        EdgarApiError: SEC API 호출 실패.

    Example:
        >>> saveFinance("0000320193")

    SeeAlso:
        - ``saveFinance`` / ``saveDocs`` — 본 모듈 saver 함수.
        - ``EDGAR_COMPANYFACTS_SCHEMA`` / ``EDGAR_DOCS_SCHEMA`` — 정규화 schema.

    Requires:
        - dartlab
        - polars
        - uuid

    Capabilities:
        - SEC companyfacts / docs → parquet 저장 + dartlab Company API 호환 검증. ticker→cik 변환.

    Guide:
        - 운영자 수집 파이프라인 — 사용자 API 직접 호출 X.

    AIContext:
        internal saver — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - User-Agent 미설정 → 403.
            - 저장 경로 명시 X → 기본 dataDir.
        OutputSchema:
            - Path / pl.DataFrame — 함수별.
        Prerequisites:
            - 인터넷 + SEC API + ticker/cik.
        Freshness:
            - SEC EDGAR 실시간.
        Dataflow:
            - ticker → SEC API → 정규화 + 저장 → parquet.
        TargetMarkets:
            - US (SEC EDGAR) saver.
    """
    normalized = str(cik).zfill(10)
    _ensureIdentityCaches(client)
    payload = getCompanyFactsJson(normalized, client)
    df = companyFactsToRows(payload)
    dest = _dataPath("edgar", normalized)
    tempPath = _tempPath(dest)
    _validateSchema(df, EDGAR_COMPANYFACTS_SCHEMA, label="edgarFinance")
    df.write_parquet(tempPath)
    return _replaceWithValidation(
        tempPath,
        dest,
        validator=lambda finalPath: _validateSavedFinanceParquet(finalPath, normalized),
    )
