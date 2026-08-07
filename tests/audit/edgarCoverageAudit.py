"""EDGAR 전종목 PIT feature coverage 를 읽기 전용으로 감사한다.

공개 문서가 인용하는 EDGAR 커버리지 세 수치(full-state strict, flow-only, revenue 단독)를
같은 하네스에서 재현한다. 세 수치의 차이는 요청 measure 하나뿐이므로 도구도 하나다.

감사는 `data/edgar/listedUniverse.parquet` 와 `data/edgar/finance/{CIK}.parquet` 를 읽기
전용으로 열고, 각 파일의 exact bytes 와 SHA-256 을 production owner 에 그대로 넘긴다.
dataLoader 와 network 는 프로세스 수준에서 차단하므로 측정 구간에 원천이 바뀔 수 없다.

CI 는 로컬 EDGAR parquet 을 갖지 않으므로 이 도구를 게이트에 걸지 않는다. 운영자가
수치를 갱신할 때 실행하고, 결과 JSON 을 진행 원장에 붙인다.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import sys
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

from dartlab.analysis.financial.dataAssets import edgarFinancialFeatures
from dartlab.dataHub.catalog.universe import ResolvedMarket
from dartlab.dataHub.paging.owner import _entities, _EntityRef, _sourcePin

_REQUIRED_LISTING_COLUMNS = frozenset(
    {
        "cik",
        "ticker",
        "title",
        "exchange",
        "is_exchange_listed",
        "is_otc",
    }
)
_DIGEST_LENGTH = 64
_SAMPLE_LIMIT = 8
_MAX_WORKERS = 8
_FLOW_MEASURES = ("financial.revenue", "financial.operatingMargin")
_MIN_SOURCE_COVERAGE = 0.90
_MIN_SUCCESS_RATE_BY_MEASURES = {
    (): 0.30,
    _FLOW_MEASURES: 0.40,
    ("financial.revenue",): 0.50,
}
_guardLock = threading.Lock()
_guardLifecycleLock = threading.Lock()
_guardActive = False
_auditHookInstalled = False
_loaderCalls = 0
_networkCalls = 0


class LoaderAccessError(RuntimeError):
    """감사 중 dataLoader 호출을 차단한다."""


class NetworkAccessError(RuntimeError):
    """감사 중 네트워크 연결을 차단한다."""


@dataclass(frozen=True, slots=True)
class _UniverseEntity:
    ticker: str
    cik: str
    title: str
    exchange: str


@dataclass(frozen=True, slots=True)
class _CompanyResult:
    ticker: str
    cik: str
    elapsedMs: float
    status: str
    sourceDigest: str | None = None
    sourceSize: int | None = None
    observationCount: int = 0
    eventAt: str | None = None
    availableAt: str | None = None
    message: str | None = None
    sourceChanged: bool = False


def _networkAuditHook(event: str, _args: tuple[Any, ...]) -> None:
    global _networkCalls
    if not _guardActive or event not in {"socket.connect", "socket.getaddrinfo", "http.client.connect"}:
        return
    with _guardLock:
        _networkCalls += 1
    raise NetworkAccessError(f"network audit event가 차단됐습니다: {event}")


@contextmanager
def _auditGuards():
    """감사 구간에서만 network와 dataLoader를 차단하고 원상 복구한다."""

    global _auditHookInstalled, _guardActive, _loaderCalls, _networkCalls
    with _guardLifecycleLock:
        from dartlab.core import dataLoader

        if not _auditHookInstalled:
            sys.addaudithook(_networkAuditHook)
            _auditHookInstalled = True
        originals: dict[str, Any] = {}

        def blocked(*_args: Any, **_kwargs: Any) -> Any:
            global _loaderCalls
            with _guardLock:
                _loaderCalls += 1
            raise LoaderAccessError("EDGAR coverage audit에서 dataLoader 호출은 금지됩니다")

        _loaderCalls = 0
        _networkCalls = 0
        for name, value in tuple(vars(dataLoader).items()):
            if inspect.isfunction(value) and value.__module__ == dataLoader.__name__:
                originals[name] = value
                setattr(dataLoader, name, blocked)
        _guardActive = True
        try:
            yield
        finally:
            _guardActive = False
            for name, value in originals.items():
                setattr(dataLoader, name, value)


def _readBytes(path: Path) -> bytes:
    with path.open("rb") as source:
        return source.read()


def _digestBytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _digestFile(path: Path) -> tuple[str, int]:
    payload = _readBytes(path)
    return _digestBytes(payload), len(payload)


def _canonicalDigest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _loadUniverse(listingPath: Path) -> tuple[_UniverseEntity, ...]:
    listing = pl.read_parquet(listingPath)
    missing = sorted(_REQUIRED_LISTING_COLUMNS - set(listing.columns))
    if missing:
        raise ValueError(f"EDGAR listing schema 필수 columns가 없습니다: {missing}")
    normalized = (
        listing.filter(pl.col("is_exchange_listed") == True)  # noqa: E712
        .select(
            pl.col("ticker").cast(pl.Utf8).str.to_uppercase().str.strip_chars().alias("ticker"),
            pl.col("cik").cast(pl.Utf8).str.zfill(10).alias("cik"),
            pl.col("title").cast(pl.Utf8).alias("title"),
            pl.col("exchange").cast(pl.Utf8).alias("exchange"),
        )
        .filter((pl.col("ticker").str.len_chars() > 0) & pl.col("cik").str.contains(r"^\d{10}$"))
        .unique("ticker", keep="first")
        .sort("ticker")
    )
    return tuple(
        _UniverseEntity(
            ticker=str(row["ticker"]),
            cik=str(row["cik"]),
            title=str(row["title"]),
            exchange=str(row["exchange"]),
        )
        for row in normalized.iter_rows(named=True)
    )


def classifyError(error: Exception) -> str:
    """감사 실패를 원인별 status code 로 분류한다.

    Requires:
        production owner 가 올린 예외. 메시지 문구로 판별하므로 owner 문구가 바뀌면
        여기도 함께 고쳐야 한다.

    Raises:
        올리지 않는다. 미분류는 ``FEATURE_OTHER_FAILURE`` 로 떨어진다.

    Example:
        >>> classifyError(ValueError("unit conflict"))
        'FEATURE_UNIT_CONFLICT'
    """

    if isinstance(error, LoaderAccessError):
        return "LOADER_ACCESS_ATTEMPT"
    if isinstance(error, NetworkAccessError):
        return "NETWORK_ACCESS_ATTEMPT"
    message = str(error)
    lowered = message.lower()
    if "missing columns" in lowered or "필수 columns" in message:
        return "SOURCE_SCHEMA_MISSING"
    if "invalid date" in lowered or "유효한 parquet" in message:
        return "SOURCE_SCHEMA_INVALID"
    if "knowledgeasof" in lowered or "before known" in lowered:
        return "PIT_NO_FILING_BEFORE_CUTOFF"
    if "non-finite" in lowered:
        return "PIT_NONFINITE_VALUE"
    if "unit conflict" in lowered:
        return "FEATURE_UNIT_CONFLICT"
    if "conflicting" in lowered:
        return "FEATURE_REVISION_CONFLICT"
    if "no stock facts" in lowered:
        return "FEATURE_NO_STOCK_FACTS"
    if "coherent stock state" in lowered:
        return "FEATURE_NO_COHERENT_STOCK_STATE"
    if "balance identity" in lowered:
        return "FEATURE_BALANCE_IDENTITY_FAILED"
    if "revenue must be positive" in lowered:
        return "FEATURE_NONPOSITIVE_REVENUE"
    if (
        "four common standalone" in lowered
        or "four standalone revenue quarters" in lowered
        or "ttm flow quarters" in lowered
        or "ttm quarters" in lowered
    ):
        return "FEATURE_NO_COHERENT_FOUR_QUARTER_WINDOW"
    if "share one accession" in lowered or "share one filing lineage" in lowered:
        return "FEATURE_FLOW_LINEAGE_MISMATCH"
    if "share one fiscal interval" in lowered:
        return "FEATURE_FLOW_INTERVAL_MISMATCH"
    return "FEATURE_OTHER_FAILURE"


def validateEnvelope(
    envelope: dict[str, Any],
    *,
    ticker: str,
    measures: tuple[str, ...],
) -> tuple[int, str, str]:
    """feature envelope 가 하나의 revision 으로 닫히는지 검사한다.

    Requires:
        ``measures`` 가 비어 있지 않으면 요청한 signal 만 정확히 그 순서로 와야 한다.
        비어 있으면 owner 가 고르는 full-state 집합을 그대로 받는다.

    Raises:
        ValueError. schema, matrix 완전성, entity identity, revision 단일성이 깨질 때.

    Example:
        >>> validateEnvelope({"schemaVersion": "x"}, ticker="AAPL", measures=())
        Traceback (most recent call last):
        ValueError: feature envelope schemaVersion이 유효하지 않습니다
    """

    if envelope.get("schemaVersion") != "feature-observation-input-v1":
        raise ValueError("feature envelope schemaVersion이 유효하지 않습니다")
    specs = tuple(envelope.get("specs", ()))
    observations = tuple(envelope.get("observations", ()))
    if not specs or len(specs) != len(observations):
        raise ValueError("feature specs와 observations가 완전한 matrix가 아닙니다")
    if measures:
        signalIds = tuple(str(item.get("signalId")) for item in observations)
        if signalIds != measures:
            raise ValueError("owner가 요청한 measure만 그 순서로 반환하지 않았습니다")
    expectedEntity = f"US:{ticker}"
    entityIds = {str(item.get("entityId")) for item in observations}
    eventDates = {str(item.get("eventAt")) for item in observations}
    availableDates = {str(item.get("availableAt")) for item in observations}
    revisionIds = {str(item.get("revisionId")) for item in observations}
    if entityIds != {expectedEntity}:
        raise ValueError("feature entity identity가 ticker와 일치하지 않습니다")
    if len(eventDates) != 1 or len(availableDates) != 1 or len(revisionIds) != 1:
        raise ValueError("feature observation identity가 하나의 revision으로 닫히지 않습니다")
    return len(observations), next(iter(eventDates)), next(iter(availableDates))


def _compileOne(
    entity: _UniverseEntity,
    *,
    financeRoot: Path,
    knownAt: str,
    measures: tuple[str, ...],
) -> _CompanyResult:
    startedAt = time.perf_counter()
    path = financeRoot / f"{entity.cik}.parquet"
    if not path.is_file():
        return _CompanyResult(entity.ticker, entity.cik, 0.0, "SOURCE_FILE_MISSING")
    sourceDigest: str | None = None
    sourceSize: int | None = None
    sourceChanged = False
    statBefore = None
    try:
        statBefore = path.stat()
        payload = _readBytes(path)
        sourceDigest = _digestBytes(payload)
        sourceSize = len(payload)
        extra: dict[str, Any] = {"measures": measures} if measures else {}
        envelope = edgarFinancialFeatures(
            subject=f"US:{entity.ticker}",
            sourceEntityId=entity.cik,
            sourcePayload=payload,
            sourceIntegrityDigest=sourceDigest,
            knownAt=knownAt,
            **extra,
        )
        observationCount, eventAt, availableAt = validateEnvelope(
            envelope,
            ticker=entity.ticker,
            measures=measures,
        )
        statAfter = path.stat()
        sourceChanged = statBefore.st_size != statAfter.st_size or statBefore.st_mtime_ns != statAfter.st_mtime_ns
        return _CompanyResult(
            entity.ticker,
            entity.cik,
            (time.perf_counter() - startedAt) * 1000,
            "SUCCESS",
            sourceDigest,
            sourceSize,
            observationCount,
            eventAt,
            availableAt,
            sourceChanged=sourceChanged,
        )
    except Exception as error:
        if statBefore is not None and path.is_file():
            statAfter = path.stat()
            sourceChanged = statBefore.st_size != statAfter.st_size or statBefore.st_mtime_ns != statAfter.st_mtime_ns
        return _CompanyResult(
            entity.ticker,
            entity.cik,
            (time.perf_counter() - startedAt) * 1000,
            classifyError(error),
            sourceDigest,
            sourceSize,
            message=str(error),
            sourceChanged=sourceChanged,
        )


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(len(ordered) * quantile) - 1))
    return ordered[index]


def _membershipDigest(entities: tuple[_UniverseEntity, ...]) -> tuple[str, str, bool]:
    ids = tuple(item.ticker for item in entities)
    sourceIds = tuple(sorted((item.ticker, item.cik) for item in entities))
    membershipPayload = {
        "market": "US",
        "provider": "edgar",
        "membership": "listed",
        "ids": ids,
        "sourceIds": sourceIds,
        "entityParams": (),
    }
    digest = _canonicalDigest(membershipPayload)
    membership = ResolvedMarket(
        market="US",
        provider="edgar",
        entityIds=ids,
        membershipDigest=digest,
        sourceEntityIds=sourceIds,
    )
    refs = _entities(membership)
    refIdentityMatches = refs == tuple(_EntityRef(item.ticker, item.cik) for item in entities)
    ownerSourcePin = f"resource-source-full:{'0' * _DIGEST_LENGTH}"
    return digest, _sourcePin(ownerSourcePin, digest), refIdentityMatches


def _verifySources(
    *,
    listingPath: Path,
    listingDigest: str,
    financeRoot: Path,
    entities: tuple[_UniverseEntity, ...],
    results: tuple[_CompanyResult, ...],
) -> dict[str, Any]:
    changed: list[str] = []
    currentListingDigest, _listingSize = _digestFile(listingPath)
    if currentListingDigest != listingDigest:
        changed.append(str(listingPath))
    expectedByCik: dict[str, set[tuple[str | None, int | None]]] = defaultdict(set)
    for item in results:
        expectedByCik[item.cik].add((item.sourceDigest, item.sourceSize))
        if item.sourceChanged:
            changed.append(str(financeRoot / f"{item.cik}.parquet"))
    finalRows: list[tuple[str, str | None, int | None]] = []
    for cik in sorted({item.cik for item in entities}):
        path = financeRoot / f"{cik}.parquet"
        final = _digestFile(path) if path.is_file() else (None, None)
        finalRows.append((cik, final[0], final[1]))
        expected = expectedByCik.get(cik, {(None, None)})
        if len(expected) != 1 or final not in expected:
            changed.append(str(path))
    return {
        "unchanged": not changed,
        "listingDigest": listingDigest,
        "finalListingDigest": currentListingDigest,
        "sourceSetDigest": _canonicalDigest(finalRows),
        "verifiedUniqueSourceFiles": sum(1 for _cik, digest, _size in finalRows if digest is not None),
        "missingUniqueSourceFiles": sum(1 for _cik, digest, _size in finalRows if digest is None),
        "changedSamples": tuple(dict.fromkeys(changed))[:_SAMPLE_LIMIT],
    }


def _auditEdgarCoverage(
    *,
    listingPath: Path,
    financeRoot: Path,
    knownAt: str,
    workers: int,
    limit: int | None,
    measures: tuple[str, ...] = (),
    progressEvery: int = 250,
) -> dict[str, Any]:
    """US 상장 universe 전체에서 production EDGAR feature owner 를 실행하고 집계한다.

    Capabilities:
        loader 와 network 호출 0 을 강제한 채 전종목 compile 을 돌리고, 성공률, 실패
        분류, 지연 분포, 원천 무결성, production entity identity 를 한 report 로 낸다.

    AIContext:
        공개 문서의 EDGAR 커버리지 수치는 전부 이 함수 산출이다. 수치를 인용하기 전에
        같은 ``knownAt`` 과 같은 ``measures`` 로 재현되는지 확인한다.

    Guide:
        ``measures`` 하나가 세 공개 수치를 가른다. 비우면 full-state strict, flow 두 개를
        주면 flow-only, revenue 하나만 주면 revenue 단독이다.

    When:
        원천이 갱신됐거나 compiler 계약을 고쳐 공개 수치를 다시 재야 할 때.

    How:
        listing parquet 으로 universe 를 고정하고 CIK 별 companyfacts bytes 를 owner 에
        직접 넘긴다. 시작과 종료 시점의 SHA-256 을 비교해 측정 구간 불변을 증명한다.

    Requires:
        로컬 `data/edgar/listedUniverse.parquet` 와 `data/edgar/finance/*.parquet`.
        둘 다 없으면 CI 에서는 실행할 수 없다.

    Raises:
        ValueError. listing schema 필수 column 이 없을 때.
        개별 회사 실패는 올리지 않고 status code 로 분류해 report 에 담는다.

    Example:
        >>> report = auditEdgarCoverage(
        ...     listingPath=Path("data/edgar/listedUniverse.parquet"),
        ...     financeRoot=Path("data/edgar/finance"),
        ...     knownAt="20260723",
        ...     workers=4,
        ...     limit=10,
        ... )
        >>> report["passedSafetyGate"]
        True

    See Also:
        Skill OS `operation.architecture` 현재 데이터 작업대 계약.
    """

    listingPayload = _readBytes(listingPath)
    listingDigest = _digestBytes(listingPayload)
    entities = _loadUniverse(listingPath)
    fullUniverseCount = len(entities)
    if limit is not None:
        entities = entities[:limit]
    startedAt = time.perf_counter()
    collected: list[_CompanyResult] = []
    progressCounts: Counter[str] = Counter()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        mapped = executor.map(
            lambda entity: _compileOne(
                entity,
                financeRoot=financeRoot,
                knownAt=knownAt,
                measures=measures,
            ),
            entities,
        )
        for index, item in enumerate(mapped, start=1):
            collected.append(item)
            progressCounts[item.status] += 1
            if progressEvery > 0 and (index % progressEvery == 0 or index == len(entities)):
                elapsed = time.perf_counter() - startedAt
                print(
                    (
                        f"[edgar-coverage] {index}/{len(entities)} "
                        f"success={progressCounts['SUCCESS']} "
                        f"missing={progressCounts['SOURCE_FILE_MISSING']} "
                        f"elapsed={elapsed:.1f}s"
                    ),
                    file=sys.stderr,
                    flush=True,
                )
    results = tuple(collected)
    wallSeconds = time.perf_counter() - startedAt
    sourceIntegrity = _verifySources(
        listingPath=listingPath,
        listingDigest=listingDigest,
        financeRoot=financeRoot,
        entities=entities,
        results=results,
    )
    statusCounts = Counter(item.status for item in results)
    observationCounts = Counter(item.observationCount for item in results if item.status == "SUCCESS")
    examples: dict[str, list[dict[str, str]]] = {}
    for item in results:
        if item.status == "SUCCESS" or len(examples.setdefault(item.status, [])) >= _SAMPLE_LIMIT:
            continue
        examples[item.status].append(
            {
                "ticker": item.ticker,
                "cik": item.cik,
                "message": item.message or item.status,
            }
        )
    successful = [item for item in results if item.status == "SUCCESS"]
    elapsedAll = [item.elapsedMs for item in results]
    elapsedPresent = [item.elapsedMs for item in results if item.status != "SOURCE_FILE_MISSING"]
    membershipDigest, syntheticSourcePin, entityRefMatch = _membershipDigest(entities)
    successCount = len(successful)
    auditedCount = len(results)
    uniqueCikCount = len({item.cik for item in entities})
    successRate = 0.0 if not results else successCount / auditedCount
    verifiedSourceCount = int(sourceIntegrity["verifiedUniqueSourceFiles"])
    sourceCoverage = 0.0 if uniqueCikCount == 0 else verifiedSourceCount / uniqueCikCount
    isFullAudit = limit is None
    minimumSuccessRate = _MIN_SUCCESS_RATE_BY_MEASURES.get(measures)
    gateFailures: list[str] = []
    if auditedCount == 0:
        gateFailures.append("AUDITED_UNIVERSE_EMPTY")
    if verifiedSourceCount == 0:
        gateFailures.append("SOURCE_SET_EMPTY")
    if successCount == 0:
        gateFailures.append("SUCCESS_SET_EMPTY")
    if isFullAudit and auditedCount != fullUniverseCount:
        gateFailures.append("FULL_UNIVERSE_INCOMPLETE")
    if isFullAudit and sourceCoverage < _MIN_SOURCE_COVERAGE:
        gateFailures.append("SOURCE_COVERAGE_BELOW_MINIMUM")
    if isFullAudit and minimumSuccessRate is not None and successRate < minimumSuccessRate:
        gateFailures.append("SUCCESS_RATE_BELOW_MINIMUM")
    if _loaderCalls != 0:
        gateFailures.append("LOADER_ACCESS_ATTEMPT")
    if _networkCalls != 0:
        gateFailures.append("NETWORK_ACCESS_ATTEMPT")
    if not bool(sourceIntegrity["unchanged"]):
        gateFailures.append("SOURCE_CHANGED_DURING_AUDIT")
    if not entityRefMatch:
        gateFailures.append("ENTITY_IDENTITY_MISMATCH")

    report = {
        "schemaVersion": "edgar-coverage-audit-v2",
        "knownAt": knownAt,
        "requestedMeasures": list(measures),
        "fullListedUniverseEntities": fullUniverseCount,
        "auditedEntities": auditedCount,
        "uniqueCiks": uniqueCikCount,
        "successEntities": successCount,
        "successRate": successRate,
        "statusCounts": dict(sorted(statusCounts.items())),
        "observationCountDistribution": {str(key): value for key, value in sorted(observationCounts.items())},
        "latestEventAt": max(
            (item.eventAt for item in successful if item.eventAt is not None),
            default=None,
        ),
        "latestAvailableAt": max(
            (item.availableAt for item in successful if item.availableAt is not None),
            default=None,
        ),
        "latencyMs": {
            "allEntities": {
                "p50": round(_percentile(elapsedAll, 0.5), 3),
                "p95": round(_percentile(elapsedAll, 0.95), 3),
                "max": round(max(elapsedAll, default=0.0), 3),
            },
            "sourcePresent": {
                "p50": round(_percentile(elapsedPresent, 0.5), 3),
                "p95": round(_percentile(elapsedPresent, 0.95), 3),
                "max": round(max(elapsedPresent, default=0.0), 3),
            },
        },
        "wallSeconds": round(wallSeconds, 3),
        "examples": examples,
        "loaderCalls": _loaderCalls,
        "networkCalls": _networkCalls,
        "sourceIntegrity": sourceIntegrity,
        "coverageGate": {
            "fullAudit": isFullAudit,
            "sourceCoverage": sourceCoverage,
            "minimumSourceCoverage": _MIN_SOURCE_COVERAGE if isFullAudit else None,
            "minimumSuccessRate": minimumSuccessRate if isFullAudit else None,
            "failures": gateFailures,
        },
        "productionPinSemantics": {
            "membershipDigest": membershipDigest,
            "syntheticSourcePin": syntheticSourcePin,
            "entityRefIdentityMatches": entityRefMatch,
            "entityParams": "none-required-by-edgar-owner",
            "sourcePayloadIdentity": "sha256-full-parquet-bytes",
        },
    }
    report["passedSafetyGate"] = not gateFailures
    return report


def auditEdgarCoverage(
    *,
    listingPath: Path,
    financeRoot: Path,
    knownAt: str,
    workers: int,
    limit: int | None,
    measures: tuple[str, ...] = (),
    progressEvery: int = 250,
) -> dict[str, Any]:
    """격리 가능한 guard와 coverage floor를 적용해 EDGAR 전수 감사를 실행한다."""

    with _auditGuards():
        return _auditEdgarCoverage(
            listingPath=listingPath,
            financeRoot=financeRoot,
            knownAt=knownAt,
            workers=workers,
            limit=limit,
            measures=measures,
            progressEvery=progressEvery,
        )


def main() -> int:
    """CLI 진입점. report JSON 을 stdout 에 내고 안전 게이트로 exit code 를 정한다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--listing", type=Path, default=Path("data/edgar/listedUniverse.parquet"))
    parser.add_argument(
        "--finance-root",
        dest="financeRoot",
        type=Path,
        default=Path("data/edgar/finance"),
    )
    parser.add_argument("--known-at", dest="knownAt", default="20260723")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--measures",
        default="",
        help=(
            "쉼표로 구분한 요청 measure. 비우면 full-state strict, "
            f"'{','.join(_FLOW_MEASURES)}' 면 flow-only, "
            "'financial.revenue' 면 revenue 단독이다."
        ),
    )
    parser.add_argument("--progress-every", dest="progressEvery", type=int, default=250)
    args = parser.parse_args()
    if args.workers <= 0 or args.workers > _MAX_WORKERS:
        raise ValueError(f"workers는 1부터 {_MAX_WORKERS} 사이여야 합니다")
    if args.limit is not None and args.limit <= 0:
        raise ValueError("limit은 양수여야 합니다")
    if args.progressEvery < 0:
        raise ValueError("progress-every는 0 이상이어야 합니다")
    measures = tuple(item.strip() for item in args.measures.split(",") if item.strip())
    report = auditEdgarCoverage(
        listingPath=args.listing,
        financeRoot=args.financeRoot,
        knownAt=args.knownAt,
        workers=args.workers,
        limit=args.limit,
        measures=measures,
        progressEvery=args.progressEvery,
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["passedSafetyGate"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
