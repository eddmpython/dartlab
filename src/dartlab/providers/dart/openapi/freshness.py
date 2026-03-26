"""DART 공시 freshness 감지 + 증분 수집 트리거.

3-Layer Freshness:
- L1: HF ETag (dataLoader._checkRemoteFreshness)
- L2: TTL 폴백 (_utils._DART_FRESHNESS_TTL_DAYS)
- L3: DART API 직접 조회 (이 모듈) — rcept_no 비교로 누락 공시 감지
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

import polars as pl

_FRESHNESS_TTL_HOURS = 24


@dataclass
class FreshnessResult:
    """종목 freshness 체크 결과."""

    stockCode: str
    isFresh: bool
    localLatest: str | None = None
    missingCount: int = 0
    missingFilings: list[dict] = field(default_factory=list)
    source: str = "unknown"
    # finance/report freshness
    financeMissing: list[str] = field(default_factory=list)
    reportMissing: list[str] = field(default_factory=list)


def _freshnessPath(stockCode: str, category: str = "docs") -> Path:
    """freshness 사이드카 파일 경로."""
    from dartlab.core.dataLoader import _dataDir

    return _dataDir(category) / f"{stockCode}.freshness"


def _isFreshnessCheckExpired(stockCode: str, category: str = "docs", *, ttlHours: int = _FRESHNESS_TTL_HOURS) -> bool:
    """TTL 게이트: 마지막 체크로부터 ttlHours 이내면 False."""
    fp = _freshnessPath(stockCode, category)
    if not fp.exists():
        return True
    ageSeconds = time.time() - fp.stat().st_mtime
    return ageSeconds > ttlHours * 3600


def _saveFreshnessResult(result: FreshnessResult, category: str = "docs") -> None:
    """체크 결과를 사이드카 파일에 기록."""
    fp = _freshnessPath(result.stockCode, category)
    fp.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "checkedAt": time.time(),
        "isFresh": result.isFresh,
        "localLatest": result.localLatest,
        "missingCount": result.missingCount,
        "source": result.source,
    }
    fp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _loadLocalRceptNos(stockCode: str) -> tuple[set[str], str | None]:
    """로컬 docs parquet에서 rcept_no 세트 + 최신 rcept_dt."""
    from dartlab.core.dataLoader import _dataDir

    path = _dataDir("docs") / f"{stockCode}.parquet"
    if not path.exists():
        return set(), None

    df = pl.scan_parquet(path).select("rcept_no", "rcept_date").unique(subset=["rcept_no"]).collect()
    if df.is_empty():
        return set(), None

    rceptNos = set(df["rcept_no"].drop_nulls().to_list())
    latestDt = df["rcept_date"].drop_nulls().max()
    return rceptNos, latestDt


def _checkFinanceReportFreshness(stockCode: str) -> tuple[list[str], list[str]]:
    """finance/report parquet에서 최근 기간 누락 여부 체크.

    Returns (financeMissing, reportMissing) — 누락된 기간 라벨 리스트.
    예: ["2025Q4", "2025Q3"]
    """
    from dartlab.providers.dart.openapi.batch import (
        _buildAllPeriods,
        _dataPath,
        _existingFinancePeriods,
        _existingReportPeriods,
    )
    from dartlab.providers.dart.openapi.constants import CODE_TO_QUARTER

    now = datetime.now()
    currentYear = now.year
    currentMonth = now.month
    # 최근 2년치 기간만 체크 (너무 먼 과거는 무시)
    # 미래 기간 제외: 분기 공시는 해당 분기 종료 후 ~45일 뒤 제출
    # Q1(3월말) → 5월, Q2(6월말) → 8월, Q3(9월말) → 11월, Q4(12월말) → 다음해 3월
    quarterCutoff = {
        "11001": 5,  # Q1 → 5월 이후에야 가능
        "11012": 8,  # Q2 → 8월 이후
        "11013": 11,  # Q3 → 11월 이후
        "11014": 3,  # Q4 → 다음해 3월 이후
    }
    allRecent = _buildAllPeriods(currentYear - 1)
    recentPeriods = []
    for y, c in allRecent:
        yr = int(y)
        cutMonth = quarterCutoff.get(c, 12)
        if c == "11014":  # Q4는 다음해
            if yr + 1 > currentYear or (yr + 1 == currentYear and currentMonth < cutMonth):
                continue
        else:
            if yr > currentYear or (yr == currentYear and currentMonth < cutMonth):
                continue
        recentPeriods.append((y, c))

    # finance
    financePath = _dataPath("finance", stockCode)
    existingFin = _existingFinancePeriods(financePath)
    financeMissing = []
    for y, c in recentPeriods:
        if (y, c) not in existingFin:
            q = CODE_TO_QUARTER.get(c, "Q4")
            financeMissing.append(f"{y}{q}")

    # report
    from dartlab.providers.dart.openapi.constants import CODE_TO_QUARTER_KR

    reportPath = _dataPath("report", stockCode)
    existingRep = _existingReportPeriods(reportPath)
    reportMissing = []
    # report는 (year, quarterKr, apiType)이므로 기간만 체크 (apiType 무관)
    existingRepPeriods = {(y, q) for y, q, _t in existingRep}
    for y, c in recentPeriods:
        qKr = CODE_TO_QUARTER_KR.get(c, "4분기")
        if (y, qKr) not in existingRepPeriods:
            q = CODE_TO_QUARTER.get(c, "Q4")
            reportMissing.append(f"{y}{q}")

    return financeMissing, reportMissing


def checkFreshness(
    stockCode: str,
    *,
    ttlHours: int = _FRESHNESS_TTL_HOURS,
    forceCheck: bool = False,
    includeFinanceReport: bool = True,
) -> FreshnessResult:
    """종목의 로컬 데이터가 최신인지 DART API로 확인."""
    from dartlab.core.guidance import emit
    from dartlab.providers.dart.openapi.dartKey import hasDartApiKey

    # TTL 게이트
    if not forceCheck and not _isFreshnessCheckExpired(stockCode, ttlHours=ttlHours):
        return FreshnessResult(stockCode=stockCode, isFresh=True, source="ttl_cache")

    # API 키 체크
    if not hasDartApiKey():
        result = FreshnessResult(stockCode=stockCode, isFresh=True, source="no_key")
        return result

    emit("freshness:checking", stockCode=stockCode)

    # 로컬 상태
    localRceptNos, localLatest = _loadLocalRceptNos(stockCode)
    if not localRceptNos:
        result = FreshnessResult(stockCode=stockCode, isFresh=True, localLatest=localLatest, source="no_local")
        _saveFreshnessResult(result)
        return result

    # DART API 조회 — 로컬 최신일 이후 정기공시만
    from dartlab.providers.dart.openapi.client import DartClient
    from dartlab.providers.dart.openapi.dartKey import resolveDartKeys
    from dartlab.providers.dart.openapi.disclosure import listFilings

    keys = resolveDartKeys()
    client = DartClient(apiKeys=keys)

    startDate = localLatest.replace("-", "") if localLatest else "20160101"
    try:
        filings = listFilings(client, stockCode, start=startDate, filingType="A", finalOnly=True)
    except (ValueError, RuntimeError, OSError):
        result = FreshnessResult(stockCode=stockCode, isFresh=True, localLatest=localLatest, source="api_error")
        _saveFreshnessResult(result)
        return result

    if filings.is_empty():
        result = FreshnessResult(stockCode=stockCode, isFresh=True, localLatest=localLatest, source="dart_api")
        emit("freshness:fresh", stockCode=stockCode)
        _saveFreshnessResult(result)
        return result

    # diff
    remoteRceptNos = set(filings["rcept_no"].drop_nulls().to_list())
    missing = remoteRceptNos - localRceptNos

    # finance/report 기간 체크
    finMissing: list[str] = []
    repMissing: list[str] = []
    if includeFinanceReport:
        try:
            finMissing, repMissing = _checkFinanceReportFreshness(stockCode)
        except (ValueError, OSError, ImportError):
            pass

    if not missing:
        allFresh = not finMissing and not repMissing
        result = FreshnessResult(
            stockCode=stockCode,
            isFresh=allFresh,
            localLatest=localLatest,
            source="dart_api",
            financeMissing=finMissing,
            reportMissing=repMissing,
        )
        if allFresh:
            emit("freshness:fresh", stockCode=stockCode)
        _saveFreshnessResult(result)
        return result

    missingFilings = (
        filings.filter(pl.col("rcept_no").is_in(list(missing)))
        .select("rcept_no", "rcept_dt", "report_nm")
        .sort("rcept_dt", descending=True)
        .to_dicts()
    )
    latestReport = missingFilings[0]["report_nm"] if missingFilings else ""

    result = FreshnessResult(
        stockCode=stockCode,
        isFresh=False,
        localLatest=localLatest,
        missingCount=len(missing),
        missingFilings=missingFilings,
        source="dart_api",
        financeMissing=finMissing,
        reportMissing=repMissing,
    )
    emit("freshness:stale", stockCode=stockCode, count=len(missing), latestReport=latestReport)
    _saveFreshnessResult(result)
    return result


def scanMarketFreshness(
    *,
    stockCodes: list[str] | None = None,
    days: int = 7,
) -> pl.DataFrame:
    """시장 전체 freshness 스캔. 로컬 데이터가 있는 종목 중 새 공시가 있는 것."""
    from dartlab.core.dataLoader import _dataDir
    from dartlab.core.guidance import emit
    from dartlab.providers.dart.openapi.client import DartClient
    from dartlab.providers.dart.openapi.dartKey import hasDartApiKey, resolveDartKeys
    from dartlab.providers.dart.openapi.disclosure import listFilings

    if not hasDartApiKey():
        emit("freshness:noKey")
        return pl.DataFrame(
            schema={"stockCode": pl.Utf8, "corpName": pl.Utf8, "newCount": pl.Int64, "latestReport": pl.Utf8}
        )

    # 로컬 종목 목록
    if stockCodes is None:
        docsDir = _dataDir("docs")
        if docsDir.exists():
            stockCodes = [f.stem for f in docsDir.glob("*.parquet")]
        else:
            stockCodes = []

    if not stockCodes:
        return pl.DataFrame(
            schema={"stockCode": pl.Utf8, "corpName": pl.Utf8, "newCount": pl.Int64, "latestReport": pl.Utf8}
        )

    # 전체 시장 정기공시 조회 (기업 미지정, 날짜 범위)
    keys = resolveDartKeys()
    client = DartClient(apiKeys=keys)
    end = datetime.now()
    start = end - timedelta(days=days)
    startStr = start.strftime("%Y%m%d")
    endStr = end.strftime("%Y%m%d")

    try:
        filings = listFilings(client, start=startStr, end=endStr, filingType="A", finalOnly=True)
    except (ValueError, RuntimeError, OSError):
        return pl.DataFrame(
            schema={"stockCode": pl.Utf8, "corpName": pl.Utf8, "newCount": pl.Int64, "latestReport": pl.Utf8}
        )

    if filings.is_empty():
        emit("freshness:scanDone", total=len(stockCodes), staleCount=0)
        return pl.DataFrame(
            schema={"stockCode": pl.Utf8, "corpName": pl.Utf8, "newCount": pl.Int64, "latestReport": pl.Utf8}
        )

    # 내 종목만 필터
    localSet = set(stockCodes)
    filings = filings.filter(pl.col("stock_code").is_in(list(localSet)))

    if filings.is_empty():
        emit("freshness:scanDone", total=len(stockCodes), staleCount=0)
        return pl.DataFrame(
            schema={"stockCode": pl.Utf8, "corpName": pl.Utf8, "newCount": pl.Int64, "latestReport": pl.Utf8}
        )

    # 종목별로 로컬 rcept_no와 비교
    rows: list[dict] = []
    for code in filings["stock_code"].unique().to_list():
        if not code:
            continue
        localRceptNos, _ = _loadLocalRceptNos(code)
        subset = filings.filter(pl.col("stock_code") == code)
        remoteNos = set(subset["rcept_no"].drop_nulls().to_list())
        missing = remoteNos - localRceptNos
        if missing:
            latestRow = (
                subset.filter(pl.col("rcept_no").is_in(list(missing)))
                .sort("rcept_dt", descending=True)
                .row(0, named=True)
            )
            rows.append(
                {
                    "stockCode": code,
                    "corpName": latestRow.get("corp_name", ""),
                    "newCount": len(missing),
                    "latestReport": latestRow.get("report_nm", ""),
                }
            )

    emit("freshness:scanDone", total=len(stockCodes), staleCount=len(rows))

    if not rows:
        return pl.DataFrame(
            schema={"stockCode": pl.Utf8, "corpName": pl.Utf8, "newCount": pl.Int64, "latestReport": pl.Utf8}
        )

    return pl.DataFrame(rows).sort("newCount", descending=True)


def collectMissing(
    stockCode: str,
    *,
    categories: list[str] | None = None,
) -> dict[str, int]:
    """누락된 공시를 증분 수집. 기존 ZipDocsCollector/batch 인프라 활용."""
    from dartlab.providers.dart.openapi.dartKey import hasDartApiKey

    if not hasDartApiKey():
        from dartlab.core.guidance import emit

        emit("collect:no_key")
        return {}

    cats = categories or ["docs", "finance", "report"]
    result: dict[str, int] = {}

    if "docs" in cats:
        result["docs"] = _collectMissingDocs(stockCode)

    if "finance" in cats or "report" in cats:
        result.update(_collectMissingFinanceReport(stockCode, cats))

    return result


def _collectMissingDocs(stockCode: str) -> int:
    """docs 증분 수집 — ZipDocsCollector 활용."""
    try:
        from dartlab.providers.dart.openapi.zipCollector import ZipDocsCollector

        collector = ZipDocsCollector(stockCode)
        return collector.collect()
    except (ValueError, KeyError, RuntimeError, OSError):
        return 0


def _collectMissingFinanceReport(stockCode: str, cats: list[str]) -> dict[str, int]:
    """finance/report 증분 수집 — batch 인프라 활용."""
    result: dict[str, int] = {}

    try:
        from dartlab.providers.dart.openapi.batch import batchCollect

        batchCats = [c for c in cats if c in ("finance", "report")]
        if not batchCats:
            return result

        counts = batchCollect([stockCode], categories=batchCats, incremental=True)
        for cat in batchCats:
            result[cat] = counts.get(stockCode, {}).get(cat, 0) if isinstance(counts.get(stockCode), dict) else 0
    except (ValueError, KeyError, RuntimeError, OSError):
        for cat in cats:
            if cat in ("finance", "report"):
                result.setdefault(cat, 0)

    return result
