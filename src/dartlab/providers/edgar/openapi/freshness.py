"""EDGAR freshness 감지 + 증분 수집 트리거.

3-Layer Freshness (DART freshness.py 패턴):
- L1: TTL 게이트 (.freshness 사이드카, 24h)
- L2: 로컬 데이터 존재 여부
- L3: SEC submissions API — accession_no 비교로 누락 감지
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import polars as pl

_FRESHNESS_TTL_HOURS = 24


@dataclass
class EdgarFreshnessResult:
    """EDGAR ticker freshness 체크 결과."""

    ticker: str
    isFresh: bool
    localLatestFiling: str | None = None
    missingCount: int = 0
    missingAccessions: list[str] = field(default_factory=list)
    source: str = "unknown"
    financeMissing: bool = False
    docsMissing: bool = False


def _edgarDataDir(category: str) -> Path:
    """EDGAR 데이터 디렉토리."""
    from dartlab import config as _cfg
    from dartlab.core.dataConfig import DATA_RELEASES

    subDir = DATA_RELEASES[category]["dir"]
    return Path(_cfg.dataDir) / subDir


def _freshnessPath(ticker: str, category: str = "edgarDocs") -> Path:
    """freshness 사이드카 파일 경로."""
    return _edgarDataDir(category) / f"{ticker}.freshness"


def _isFreshnessCheckExpired(
    ticker: str,
    category: str = "edgarDocs",
    *,
    ttlHours: int = _FRESHNESS_TTL_HOURS,
) -> bool:
    """TTL 게이트: 마지막 체크로부터 ttlHours 이내면 False."""
    fp = _freshnessPath(ticker, category)
    if not fp.exists():
        return True
    ageSeconds = time.time() - fp.stat().st_mtime
    return ageSeconds > ttlHours * 3600


def _saveFreshnessResult(result: EdgarFreshnessResult, category: str = "edgarDocs") -> None:
    """체크 결과를 사이드카 파일에 기록."""
    fp = _freshnessPath(result.ticker, category)
    fp.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "checkedAt": time.time(),
        "isFresh": result.isFresh,
        "localLatestFiling": result.localLatestFiling,
        "missingCount": result.missingCount,
        "source": result.source,
    }
    fp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _loadLocalAccessionNos(ticker: str) -> tuple[set[str], str | None]:
    """로컬 docs parquet에서 accession_no 세트 + 최신 filing_date."""
    path = _edgarDataDir("edgarDocs") / f"{ticker}.parquet"
    if not path.exists():
        return set(), None

    try:
        schema = pl.read_parquet_schema(path)
        if "accession_no" not in schema:
            return set(), None

        selectCols = ["accession_no"]
        hasFilingDate = "filing_date" in schema
        if hasFilingDate:
            selectCols.append("filing_date")

        df = pl.scan_parquet(path).select(selectCols).unique(subset=["accession_no"]).collect()
        if df.is_empty():
            return set(), None
        accessions = set(df["accession_no"].drop_nulls().to_list())
        latestDate = None
        if hasFilingDate:
            latestDate = df["filing_date"].drop_nulls().max()
        return accessions, str(latestDate) if latestDate is not None else None
    except (pl.exceptions.ComputeError, pl.exceptions.SchemaError, OSError):
        return set(), None


def _resolveCik(ticker: str) -> str | None:
    """ticker → CIK 해석."""
    from dartlab.core.dataLoader import loadEdgarListedUniverse

    universe = loadEdgarListedUniverse()
    match = universe.filter(pl.col("ticker") == ticker.upper())
    if match.height > 0:
        return match["cik"][0]
    return None


def checkEdgarFreshness(ticker: str, *, forceCheck: bool = False) -> EdgarFreshnessResult:
    """EDGAR ticker freshness 체크.

    L1: TTL 게이트 (24h)
    L2: 로컬 파일 존재 확인
    L3: SEC submissions API로 원격 accession_no 비교
    """
    normalized = ticker.upper()

    # L1: TTL 게이트
    if not forceCheck and not _isFreshnessCheckExpired(normalized):
        return EdgarFreshnessResult(
            ticker=normalized,
            isFresh=True,
            source="ttl_cache",
        )

    # L2: 로컬 데이터 확인
    cik = _resolveCik(normalized)
    docsPath = _edgarDataDir("edgarDocs") / f"{normalized}.parquet"
    financePath = _edgarDataDir("edgar") / f"{cik}.parquet" if cik else None

    docsMissing = not docsPath.exists()
    financeMissing = financePath is None or not financePath.exists()

    if docsMissing and financeMissing:
        result = EdgarFreshnessResult(
            ticker=normalized,
            isFresh=False,
            source="no_local_data",
            docsMissing=True,
            financeMissing=True,
        )
        _saveFreshnessResult(result)
        return result

    # L3: SEC submissions API — accession_no 비교
    if not cik:
        result = EdgarFreshnessResult(
            ticker=normalized,
            isFresh=False,
            source="no_cik",
            docsMissing=docsMissing,
            financeMissing=financeMissing,
        )
        _saveFreshnessResult(result)
        return result

    localAccessions, localLatest = _loadLocalAccessionNos(normalized)

    try:
        from dartlab.providers.edgar.openapi.submissions import (
            findRegularFilings,
            getSubmissionsJson,
        )

        submissions = getSubmissionsJson(cik)
        remoteFilings = findRegularFilings(submissions, sinceYear=2009)
        remoteAccessions = {f["accession_no"] for f in remoteFilings}

        missing = remoteAccessions - localAccessions
        missingAccessions = sorted(missing)

        isFresh = len(missing) == 0 and not financeMissing

        result = EdgarFreshnessResult(
            ticker=normalized,
            isFresh=isFresh,
            localLatestFiling=localLatest,
            missingCount=len(missing),
            missingAccessions=missingAccessions[:20],
            source="sec_api",
            docsMissing=docsMissing,
            financeMissing=financeMissing,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        result = EdgarFreshnessResult(
            ticker=normalized,
            isFresh=not docsMissing and not financeMissing,
            localLatestFiling=localLatest,
            source=f"sec_api_error: {exc}",
            docsMissing=docsMissing,
            financeMissing=financeMissing,
        )

    _saveFreshnessResult(result)
    return result


def scanEdgarMarketFreshness(
    *,
    tier: str = "sp500",
    limit: int | None = None,
) -> pl.DataFrame:
    """tier 내 ticker 전체 freshness 일괄 스캔."""
    from dartlab.core.dataLoader import loadEdgarTargetUniverse

    universe = loadEdgarTargetUniverse(tier)
    tickers = universe["ticker"].to_list()
    if limit:
        tickers = tickers[:limit]

    # ticker → cik 맵 한 번에 구축
    tickerCikMap: dict[str, str] = {}
    for row in universe.select("ticker", "cik").iter_rows(named=True):
        tickerCikMap[row["ticker"]] = row["cik"]

    docsDir = _edgarDataDir("edgarDocs")
    financeDir = _edgarDataDir("edgar")

    records = []
    for t in tickers:
        cik = tickerCikMap.get(t)
        docsPath = docsDir / f"{t}.parquet"
        financePath = financeDir / f"{cik}.parquet" if cik else None

        hasDocs = docsPath.exists()
        hasFinance = financePath is not None and financePath.exists()

        records.append({
            "ticker": t,
            "cik": cik or "",
            "hasDocs": hasDocs,
            "hasFinance": hasFinance,
            "status": "complete" if hasDocs and hasFinance else "partial" if hasDocs or hasFinance else "missing",
        })

    return pl.DataFrame(records) if records else pl.DataFrame()


def collectEdgarMissing(
    ticker: str,
    *,
    categories: list[str] | None = None,
) -> dict[str, int]:
    """누락된 데이터만 수집. 반환: {"finance": N, "docs": N}."""
    from dartlab.providers.edgar.openapi.batch import batchCollectEdgar

    cats = categories or ["finance", "docs"]
    results = batchCollectEdgar(
        [ticker],
        categories=cats,
        incremental=False,  # 강제 재수집
        showProgress=False,
    )
    return results.get(ticker.upper(), {})
