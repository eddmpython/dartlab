"""scan 공용 유틸리티 — report parquet 스캔, 숫자 파싱, listing 로드."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import polars as pl

from dartlab.core.logger import getLogger
from dartlab.core.utils.helpers import parseNumStr
from dartlab.scan.io.accounts import (
    EQ_IDS as EQ_IDS,
)
from dartlab.scan.io.accounts import (
    EQ_NMS as EQ_NMS,
)
from dartlab.scan.io.accounts import (
    LIABILITY_IDS as LIABILITY_IDS,
)
from dartlab.scan.io.accounts import (
    LIABILITY_NMS as LIABILITY_NMS,
)
from dartlab.scan.io.accounts import (
    NI_IDS as NI_IDS,
)
from dartlab.scan.io.accounts import (
    NI_NMS as NI_NMS,
)
from dartlab.scan.io.accounts import (
    OP_IDS as OP_IDS,
)
from dartlab.scan.io.accounts import (
    OP_NMS as OP_NMS,
)
from dartlab.scan.io.accounts import (
    REVENUE_IDS as REVENUE_IDS,
)
from dartlab.scan.io.accounts import (
    REVENUE_NMS as REVENUE_NMS,
)
from dartlab.scan.io.accounts import (
    TA_IDS as TA_IDS,
)
from dartlab.scan.io.accounts import (
    TA_NMS as TA_NMS,
)
from dartlab.scan.io.accounts import amountExpr
from dartlab.scan.io.accounts import (
    extractAccount as extractAccount,
)
from dartlab.scan.io.accounts import (
    preferConsolidatedPerCompany as preferConsolidatedPerCompany,
)
from dartlab.scan.io.accounts import (
    preferConsolidatedPerCompanyLazy as preferConsolidatedPerCompanyLazy,
)
from dartlab.scan.io.calendar import (
    QUARTER_ORDER as QUARTER_ORDER,
)
from dartlab.scan.io.calendar import (
    _calendarizeWithFmMap,
)
from dartlab.scan.io.calendar import (
    filterLatestPeriodPerStock as filterLatestPeriodPerStock,
)
from dartlab.scan.io.calendar import (
    filterLatestPeriodPerStockLazy as filterLatestPeriodPerStockLazy,
)
from dartlab.scan.io.calendar import (
    filterLatestPerStock as filterLatestPerStock,
)
from dartlab.scan.io.calendar import (
    filterLatestPerStockLazy as filterLatestPerStockLazy,
)
from dartlab.scan.io.calendar import (
    findLatestYear as findLatestYear,
)
from dartlab.scan.io.calendar import (
    parseDateYear as parseDateYear,
)
from dartlab.scan.io.calendar import (
    pickBestQuarter as pickBestQuarter,
)
from dartlab.scan.io.lite import (
    _LITE_ACCOUNTS_BS as _LITE_ACCOUNTS_BS,
)
from dartlab.scan.io.lite import (
    _LITE_ACCOUNTS_CF as _LITE_ACCOUNTS_CF,
)
from dartlab.scan.io.lite import (
    _LITE_ACCOUNTS_IS as _LITE_ACCOUNTS_IS,
)
from dartlab.scan.io.lite import (
    LITE_ACCOUNTS as LITE_ACCOUNTS,
)
from dartlab.scan.io.lite import (
    LITE_SINCE_YEAR as LITE_SINCE_YEAR,
)
from dartlab.scan.io.lite import (
    LITE_SJ_DIVS as LITE_SJ_DIVS,
)

_log = getLogger(__name__)

_scanDownloaded = False


class ScanDataError(RuntimeError):
    """scan 공용 데이터의 다운로드, 저장소, schema 또는 실행 실패."""

    def __init__(self, stage: str, message: str, *, source: str | Path | None = None) -> None:
        self.stage = stage
        self.source = str(source) if source is not None else None
        sourceLabel = f", source={self.source}" if self.source else ""
        super().__init__(f"scan data failed: stage={stage}{sourceLabel}: {message}")


# scan 프리빌드 루트 필수 파일 — HF `dart/scan/` 루트에 있어야 하는 산출물.
# 과거 `allow_patterns="dart/scan/**/*.parquet"` 버그로 루트 파일이 누락된
# 불완전 캐시 상태 환경이 존재한다 (report/ 12개만 받아진 상태). 이 리스트로
# 완전성을 검증해 한 개라도 없으면 재다운로드를 강제한다.
_REQUIRED_SCAN_ROOT_FILES: tuple[str, ...] = (
    "finance.parquet",
    "changes.parquet",
    "sharesOutstanding.parquet",
)

# scan/report/ 안 필수 prebuild. 빌더 `scan/builders/kr/report/build.SCAN_API_TYPES` 에서
# 파생(1:1 자동 동기화). 별도 하드리스트 유지 시 drift 회귀(shortTermBond/commercialPaper/
# investedCompany 누락 -> dartlab.scan("debt") silent thrift error, 2026-05-17)를 원천 차단.
# 정합성은 tests/scan/test_prebuild_contract.py::test_required_report_matches_builder 가 강제.
from dartlab.scan.builders.kr.report.build import SCAN_API_TYPES as _SCAN_API_TYPES

_REQUIRED_REPORT_FILES: tuple[str, ...] = tuple(f"{apiType}.parquet" for apiType in _SCAN_API_TYPES)


def _isScanRootComplete(scanDir: Path) -> bool:
    """scan 프리빌드 루트 필수 파일 존재 확인."""

    return all((scanDir / name).exists() for name in _REQUIRED_SCAN_ROOT_FILES)


def _isScanReportComplete(scanDir: Path) -> bool:
    """scan/report 필수 prebuild 파일 존재 확인."""

    reportDir = scanDir / "report"
    if not reportDir.is_dir():
        return False
    return all((reportDir / name).exists() for name in _REQUIRED_REPORT_FILES)


def _missingScanFiles(scanDir: Path, *, requireReports: bool) -> list[str]:
    """현재 scanDir 기준으로 부족한 prebuild 상대 경로를 반환한다."""

    missing = [name for name in _REQUIRED_SCAN_ROOT_FILES if not (scanDir / name).exists()]
    if requireReports:
        reportDir = scanDir / "report"
        missing.extend(f"report/{name}" for name in _REQUIRED_REPORT_FILES if not (reportDir / name).exists())
    return missing


def _downloadScanFile(scanDir: Path, relativePath: str) -> None:
    """HF `scan` 카테고리의 단일 prebuild 파일을 원자적으로 다운로드한다."""

    import os
    import shutil

    from dartlab.core.dataConfig import DATA_RELEASES, hfBaseUrl, repoFor
    from dartlab.core.dataLoader import _downloadWithRetry

    rel = relativePath.replace("\\", "/")
    dest = scanDir / Path(rel)
    tmp = dest.with_name(f"{dest.name}.tmp")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if tmp.exists():
        tmp.unlink()

    hfPath = f"{DATA_RELEASES['scan']['dir']}/{rel}"
    try:
        from huggingface_hub import hf_hub_download

        from dartlab.core.hfRetry import retryHfCall

        # HF read SSOT(core.hfRetry) — 자체 5-retry 루프 삭제, 429/503/504 단일 백오프 정책으로 수렴.
        downloaded = Path(
            retryHfCall(
                hf_hub_download,
                repo_id=repoFor("scan"),
                repo_type="dataset",
                filename=hfPath,
                token=os.environ.get("HF_TOKEN") or None,
            )
        )
        shutil.copyfile(downloaded, tmp)
    except Exception as hubError:  # noqa: BLE001 - hub 실패 원인은 fallback 실패 시 함께 보존
        _log.warning("scan prebuild HF hub download failed for %s: %s", rel, hubError)
        try:
            _downloadWithRetry(f"{hfBaseUrl('scan')}/{rel}", tmp)
        except Exception as resolveError:  # noqa: BLE001 - 서로 다른 공급 경로의 원인을 함께 보존
            raise ExceptionGroup(
                f"scan prebuild download failed: {rel}",
                [hubError, resolveError],
            ) from resolveError

    if not tmp.exists() or tmp.stat().st_size <= 0:
        if tmp.exists():
            tmp.unlink()
        raise RuntimeError(f"empty scan prebuild download: {rel}")
    if rel.endswith(".parquet"):
        from dartlab.core.dataLoaderNative import validateParquetArtifact

        try:
            # core.dataLoader._download 와 동일 계약: canonical 확정 전 무결성 검증.
            # 실패 시 DataArtifactError(OSError) 로 전파되어 기존 로컬 파일이 유지된다.
            validateParquetArtifact(tmp)
        except OSError:
            tmp.unlink(missing_ok=True)
            raise
    tmp.replace(dest)
    if rel.endswith(".parquet"):
        from dartlab.core.dataLoader import _saveEtag

        # freshness 재검증(_refreshScanFile)이 쓸 ETag 사이드카. 실패해도 경고만 (best-effort).
        _saveEtag(rel[: -len(".parquet")], dest, "scan")


# 프로세스 내 freshness 재확인 간격. 오프라인·프록시 차단 환경에서 TTL 만료 후
# 매 scan 호출마다 HEAD 재시도로 지연이 반복되는 것을 막는다 (etag mtime 은 성공
# 시에만 갱신되므로 세션 간 신선도 보장은 그대로 유지된다).
_SCAN_FRESHNESS_RECHECK_SECONDS = 900.0
_scanFreshnessCheckedAt: dict[str, float] = {}


def _refreshScanFile(scanDir: Path, relativePath: str) -> None:
    """존재하는 prebuild 하나를 ETag 로 재검증하고 원격이 최신이면 재다운로드한다.

    core.dataLoader 의 canonical freshness 스택(`_checkRemoteFreshness`)을 그대로 쓴다.
    확인 실패(None)와 다운로드 실패는 기존 로컬 파일 유지로 강등한다 (scan 은 매 호출
    경로라 여기서 죽으면 로컬 자산이 있는데도 전 축이 멈춘다).
    """

    from dartlab.core.dataLoader import _checkRemoteFreshness

    rel = relativePath.replace("\\", "/")
    if not rel.endswith(".parquet"):
        return
    dest = scanDir / Path(rel)
    stale = _checkRemoteFreshness(rel[: -len(".parquet")], dest, "scan")
    if stale is None:
        _log.warning("scan prebuild 신선도 확인 실패. 로컬 파일을 그대로 쓴다 (%s)", rel)
        return
    if stale is not True:
        etagPath = dest.with_suffix(".parquet.etag")
        if etagPath.exists():
            # etag mtime = 마지막 확인 시각. fresh 확인도 TTL 리셋 (core refreshFromHf 와 동일).
            etagPath.touch()
        return
    try:
        _downloadScanFile(scanDir, rel)
    except (ExceptionGroup, OSError, RuntimeError, ValueError) as exc:
        _log.warning("scan prebuild 갱신 실패. 기존 파일을 유지한다 (%s): %s", rel, exc)


def _maybeRefreshScanFile(scanDir: Path, relativePath: str) -> None:
    """TTL(12h) 게이트를 통과했을 때만 단일 prebuild 의 원격 재검증을 수행한다.

    게이트는 core `_shouldRefreshDart` 재사용: etag 사이드카 mtime 기준 12h,
    사이드카 없는 구세대 파일은 mtime 84h 유예 후 1회 강제 재조달(자가 치유).
    `DARTLAB_NO_REFRESH=1` 이면 core 게이트가 항상 False 를 돌려줘 network 0회.
    """

    import time

    from dartlab.core.dataLoader import _shouldRefreshDart

    rel = relativePath.replace("\\", "/")
    dest = scanDir / Path(rel)
    if not dest.exists():
        return
    last = _scanFreshnessCheckedAt.get(rel)
    now = time.monotonic()
    if last is not None and now - last < _SCAN_FRESHNESS_RECHECK_SECONDS:
        return
    if not _shouldRefreshDart(dest, "auto"):
        return
    _scanFreshnessCheckedAt[rel] = now
    _refreshScanFile(scanDir, rel)


def _refreshStaleScanFiles(scanDir: Path, *, requireReports: bool) -> None:
    """필수 prebuild 전체를 TTL 게이트 후 ETag 재검증한다 (HF 일일 갱신 추적)."""

    rels = list(_REQUIRED_SCAN_ROOT_FILES)
    if requireReports:
        rels.extend(f"report/{name}" for name in _REQUIRED_REPORT_FILES)
    for rel in rels:
        _maybeRefreshScanFile(scanDir, rel)


def ensureScanArtifact(relativePath: str) -> Path:
    """공통 root 외 선택 artifact 하나를 확보하고 존재와 크기를 검증한다."""

    scanDir = _ensureScanData()
    destination = scanDir / relativePath
    if destination.exists() and destination.stat().st_size > 0:
        _maybeRefreshScanFile(scanDir, relativePath)
        return destination
    try:
        _downloadScanFile(scanDir, relativePath)
    except Exception as exc:
        raise ScanDataError(
            "artifact_download",
            f"{type(exc).__name__}: {exc}",
            source=destination,
        ) from exc
    if not destination.exists() or destination.stat().st_size <= 0:
        raise ScanDataError(
            "artifact_incomplete",
            "download did not create a non-empty artifact",
            source=destination,
        )
    return destination


def _isScanComplete(scanDir: Path) -> bool:
    """scan 프리빌드 루트 + report/ 필수 파일 모두 존재 확인.

    root artifact (_REQUIRED_SCAN_ROOT_FILES)와 report prebuild (_REQUIRED_REPORT_FILES)가 모두
    있어야 True. 둘 중 하나 누락 시 _ensureScanData() 가 재다운로드 강제.
    """
    return _isScanRootComplete(scanDir) and _isScanReportComplete(scanDir)


def financeScanPath(scanDir: Path) -> Path:
    """전종목 finance 프리빌드 경로 (환경별 SSOT).

    데스크톱은 전량 ``finance.parquet``(~307MB), 브라우저(pyodide)는 같은 스키마의 경량본
    ``finance-lite.parquet``(~20MB) 을 쓴다. 축 모듈이 파일명을 각자 하드코딩하면 브라우저에서
    없는 파일을 보고 조용히 빈 결과로 떨어지므로, 어느 파일을 쓸지는 여기 한 곳이 정한다.

    Args:
        scanDir: ``_ensureScanData()`` 가 돌려준 scan 프리빌드 디렉토리.

    Returns
    -------
    Path
        환경에 맞는 finance 프리빌드 parquet 경로.
    """
    from dartlab.core.dataLoader import _IS_PYODIDE

    return scanDir / ("finance-lite.parquet" if _IS_PYODIDE else "finance.parquet")


def lazyParquet(path: Path | str, *, columns: list[str] | None = None) -> pl.LazyFrame:
    """parquet → LazyFrame (pyodide WASM 호환).

    polars WASM wheel 에는 ``scan_parquet`` 이 없다(``PyLazyFrame.new_from_parquet`` 부재).
    그 환경에서는 pyarrow 로 전량 읽고 ``.lazy()`` 로 올린다. 뒤따르는 filter/group_by/str 연산은
    WASM 에서도 동일하게 동작한다(실측). 데스크톱은 ``pl.scan_parquet`` 그대로라 push-down 유지.

    Args:
        path: parquet 파일 경로.
        columns: 열 프로젝션. pyodide 경로에서만 읽기 단계에 적용된다.
    """
    from dartlab.core.dataLoader import _IS_PYODIDE, readParquetSafe

    if not _IS_PYODIDE:
        return pl.scan_parquet(str(path))
    return readParquetSafe(str(path), columns=columns).lazy()


def parquetColumns(path: Path | str) -> list[str]:
    """parquet 열 이름만 읽는다 (본문 미독).

    ``lazyParquet(path).collect_schema()`` 은 pyodide 경로에서 파일 전량을 읽어 버린다(20MB 재독).
    스키마만 필요한 자리(예: stockCode 열 존재 확인)는 이 함수를 쓴다.
    """
    from dartlab.core.dataLoader import _IS_PYODIDE

    if not _IS_PYODIDE:
        return pl.scan_parquet(str(path)).collect_schema().names()
    import pyarrow.parquet as pq

    return list(pq.read_schema(str(path)).names)


def collectScan(lz: pl.LazyFrame) -> pl.DataFrame:
    """LazyFrame 수집 (pyodide WASM 호환).

    데스크톱은 streaming 엔진으로 메모리 피크를 눌러 수집한다. polars WASM 은 streaming 엔진이
    없어(``Invalid engine argument``) 기본 엔진으로 수집한다. 브라우저가 다루는 경량본은 작아서
    메모리 문제가 없다.
    """
    from dartlab.core.dataLoader import _IS_PYODIDE

    if _IS_PYODIDE:
        return lz.collect()  # polars-streaming-unsupported (WASM 엔진 부재)
    return lz.collect(engine="streaming")


def scanLatestAccountValues(
    scanPath: Path,
    accountSpecs: dict[str, tuple[set[str], set[str], set[str] | None]],
    *,
    amountCol: str = "thstrm_amount",
) -> pl.DataFrame:
    """finance prebuild를 한 번 읽어 회사별 최신 기간 계정을 wide로 집계한다."""

    if not accountSpecs:
        raise ValueError("accountSpecs는 비어 있을 수 없습니다")

    sourceColumns = set(parquetColumns(scanPath))
    required = {
        "stockCode",
        "bsns_year",
        "sj_div",
        "fs_nm",
        "account_id",
        "account_nm",
        amountCol,
    }
    missing = sorted(required - sourceColumns)
    if missing:
        raise ScanDataError(
            "finance_schema",
            f"missing columns: {', '.join(missing)}",
            source=scanPath,
        )

    projected = [*sorted(required), *(["reprt_nm"] if "reprt_nm" in sourceColumns else [])]
    accountIds: set[str] = set()
    accountNms: set[str] = set()
    statementDivs: set[str] = set()
    for ids, names, divisions in accountSpecs.values():
        accountIds.update(ids)
        accountNms.update(names)
        if divisions is not None:
            statementDivs.update(divisions)

    matched = pl.col("account_id").is_in(accountIds) | pl.col("account_nm").is_in(accountNms)
    if statementDivs:
        matched &= pl.col("sj_div").is_in(statementDivs)
    validStatement = pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표")
    source = lazyParquet(scanPath, columns=projected).select(projected).filter(validStatement & matched)
    latest = filterLatestPeriodPerStockLazy(
        preferConsolidatedPerCompanyLazy(source),
    ).with_columns(amountExpr(amountCol).alias("_scanAmount"))

    expressions: list[pl.Expr] = []
    for name, (ids, names, divisions) in accountSpecs.items():
        accountMatched = pl.col("account_id").is_in(ids) | pl.col("account_nm").is_in(names)
        if divisions is not None:
            accountMatched &= pl.col("sj_div").is_in(divisions)
        expressions.append(
            pl.col("_scanAmount").filter(accountMatched & pl.col("_scanAmount").is_not_null()).first().alias(name)
        )

    return collectScan(
        latest.group_by(["stockCode", "bsns_year"]).agg(expressions),
    )


def _ensureScanData(*, requireReports: bool = False) -> Path:
    """scan 프리빌드 디렉토리 확인.

    일반 환경: 루트 필수 파일(finance/changes/sharesOutstanding) 이 모두 존재하면
    TTL(12h) 게이트 후 ETag 재검증(`_refreshStaleScanFiles`)만 수행하고 반환한다.
    HF 는 매일 갱신되므로 존재 확인만으로 끝내면 로컬이 영구 stale 로 굳는다.
    하나라도 없으면 HF scan 카테고리에서 자동 다운로드한다. report axis 호출자는
    requireReports=True 로 report prebuild 까지 보장한다.

    Pyodide(브라우저): 경량본 `finance-lite.parquet` 1 개만 요구한다.

    Returns
    -------
    Path
        scan 프리빌드 디렉토리 경로 (~/.dartlab/data/scan/).
    """
    from dartlab.core.dataLoader import _IS_PYODIDE, _dataDir
    from dartlab.core.messaging import emit

    scanDir = Path(_dataDir("scan"))

    global _scanDownloaded

    # Pyodide: finance-lite.parquet 단일 파일만 요구 (전체 프리빌드는 용량상 불가).
    # 없으면 HF 에서 받는다. 예전엔 여기서 다운로드를 안 하고 곧장 반환해, 브라우저의 scan 이
    # 늘 프리빌드 없는 상태로 돌아 조용히 0 행을 냈다(전용 로더가 있는데도 호출되지 않았다).
    if _IS_PYODIDE:
        liteParquet = scanDir / "finance-lite.parquet"
        if _scanDownloaded and liteParquet.exists():
            return scanDir
        if liteParquet.exists():
            _scanDownloaded = True
            return scanDir
        emit("scan:prebuild_download_lite")
        from dartlab.core.dataLoaderPyodide import pyodideFetchScanLite

        try:
            pyodideFetchScanLite(_dataDir)
        except (OSError, RuntimeError, ValueError) as exc:
            emit("scan:prebuild_failed", error=str(exc))
            raise ScanDataError(
                "prebuild_download",
                f"{type(exc).__name__}: {exc}",
                source=liteParquet,
            ) from exc
        if not liteParquet.exists() or liteParquet.stat().st_size <= 0:
            raise ScanDataError(
                "prebuild_incomplete",
                "finance-lite.parquet was not created",
                source=liteParquet,
            )
        _scanDownloaded = True
        return scanDir

    if _scanDownloaded and not _missingScanFiles(scanDir, requireReports=requireReports):
        _refreshStaleScanFiles(scanDir, requireReports=requireReports)
        return scanDir

    if not _missingScanFiles(scanDir, requireReports=requireReports):
        _scanDownloaded = True
        _refreshStaleScanFiles(scanDir, requireReports=requireReports)
        return scanDir

    # 루트 필수 파일 누락 (신규 사용자 또는 과거 버그로 불완전 캐시)
    emit("scan:prebuild_missing")
    missing = _missingScanFiles(scanDir, requireReports=requireReports)
    try:
        for rel in missing:
            _downloadScanFile(scanDir, rel)
    except (ExceptionGroup, OSError, RuntimeError, ValueError) as e:
        emit("scan:prebuild_failed", error=str(e))
        raise ScanDataError(
            "prebuild_download",
            f"{type(e).__name__}: {e}",
            source=scanDir,
        ) from e

    missingAfter = _missingScanFiles(scanDir, requireReports=requireReports)
    if missingAfter:
        emit("scan:prebuild_incomplete", missing=", ".join(missingAfter[:8]))
        raise ScanDataError(
            "prebuild_incomplete",
            f"missing artifacts: {', '.join(missingAfter)}",
            source=scanDir,
        )

    _scanDownloaded = True
    fileCount = len(_REQUIRED_SCAN_ROOT_FILES) + (len(_REQUIRED_REPORT_FILES) if requireReports else 0)
    emit("scan:prebuild_ready", fileCount=fileCount)

    return scanDir


def latestDataRows(group: pl.DataFrame, col: str) -> pl.DataFrame:
    """종목 group 에서 ``col`` 이 실값(null/'-'/공백 아님)인 행의 **최신 연도** 부분집합을 반환한다.

    이벤트성/희소 report apiType(공모자금사용·5억+보수·채무증권 등)은 최신 연도 filing 이
    "해당사항없음"(status-only, ``-``)일 수 있어 단순 ``max(year)`` 가 과거 실데이터를 놓친다.
    본 헬퍼는 실값이 있는 연도 중 최신을 골라 그 오탐을 차단한다. 실값 행이 없으면 빈 DataFrame.

    Args:
        group: 한 종목의 report 행 group (``year`` 컬럼 필요).
        col: 실값 존재를 판정할 값 컬럼 이름.

    Returns:
        최신 실데이터 연도의 행 부분집합. 없으면 ``group.head(0)`` (빈).
    """
    if col not in group.columns or "year" not in group.columns:
        return group.head(0)
    withData = group.filter(~pl.col(col).cast(pl.Utf8).fill_null("").str.strip_chars().is_in(["", "-"]))
    years = [y for y in withData["year"].to_list() if y]
    if not years:
        return group.head(0)
    return withData.filter(pl.col("year") == max(years))


def scanParquets(apiType: str, keepCols: list[str]) -> pl.DataFrame:
    """report parquet에서 특정 apiType만 LazyFrame 스캔.

    scan/report/{apiType}.parquet 프리빌드가 있으면 단일 파일에서 즉시 로드.
    없으면 종목별 parquet 순회 (fallback).

    Parameters
    ----------
    api_type : str
        DART API 유형 (예: "majorHolder", "auditReport").
    keep_cols : list[str]
        추출할 컬럼 목록 (예: ["stockCode", "year", "지분율"]).

    Returns
    -------
    pl.DataFrame
        keep_cols 중 존재하는 컬럼만 포함한 전종목 결과.
        데이터 없으면 빈 DataFrame.

    Raises
    ------
    ScanDataError
        존재하는 prebuild 또는 raw report parquet가 손상됐거나 schema 계약이 깨진 경우.

    Examples
    --------
    >>> from dartlab.scan.io.parquet import scanParquets
    >>> df = scanParquets("majorHolder", ["stockCode", "year", "지분율"])
    >>> df.height > 0
    True

    Guide:
        - 호출 컨텍스트 가이드.

    Capabilities:
        - prebuild ``scan/report/{apiType}.parquet`` 우선 lazy scan → 없으면 종목별 raw report
          parquet 순회로 자동 fallback. apiType 매칭 + keep_cols 동적 적응 (스키마 변화 흡수).

    AIContext:
        scan 비재무 axis (governance/workforce/capital/audit/...) 가 모두 본 함수로 LazyFrame
        획득. AI agent 가 호출 시 빈 결과는 raw 데이터 부재 → ``hint:market_data_needed`` 이벤트
        emit (UI 가 사용자에게 다운로드 안내).

    Guide:
        - keepCols 에 stockCode/year/quarter 외 axis 핵심 컬럼이 최소 1 개 있어야 (없으면 skip).
        - 종목별 fallback 은 메모리 부담 — prebuild 우선.

    When:
        scan 비재무 axis 가 호출. 사용자 직접 호출은 prototype 한정.

    How:
        ``_ensureScanData`` → prebuild file 존재 시 lazy scan + keep_cols select → 없으면 raw
        report 디렉토리 종목별 lazy + apiType filter → vertical_relaxed concat.

    Requires:
        - 로컬 ``data/dart/scan/report/{apiType}.parquet`` (``buildReport`` 산출) 또는
          ``data/dart/report/{stockCode}.parquet`` (fallback)

    SeeAlso:
        - :func:`scanFinanceParquets` — finance 전용 (sj_div 필터 + 계정 매칭)
        - :func:`dartlab.scan.builders.kr.core.buildReport` — source 빌드
        - :data:`SCAN_API_TYPES` — 처리 apiType 12 종 list
    """
    # 1순위: 프리빌드 scan parquet (없으면 자동 다운로드 시도)
    scanDir = _ensureScanData(requireReports=True)
    scan_path = scanDir / "report" / f"{apiType}.parquet"
    if scan_path.exists():
        try:
            lf = pl.scan_parquet(str(scan_path))
            schema_names = lf.collect_schema().names()
            available = [c for c in keepCols if c in schema_names]
            non_meta = [c for c in available if c not in ("stockCode", "year", "quarter")]
            if non_meta:
                return lf.select(available).collect(engine="streaming")
            raise ScanDataError(
                "report_prebuild_schema",
                f"none of the requested value columns exist: {keepCols}",
                source=scan_path,
            )
        except ScanDataError:
            raise
        except (pl.exceptions.PolarsError, OSError) as exc:
            raise ScanDataError(
                "report_prebuild_read",
                f"{type(exc).__name__}: {exc}",
                source=scan_path,
            ) from exc

    # 2순위: 종목별 순회 (fallback)
    from dartlab.core.dataLoader import _dataDir

    report_dir = Path(_dataDir("report"))
    parquet_files = sorted(report_dir.glob("*.parquet"))

    if not parquet_files:
        from dartlab.core.messaging import emit

        emit("hint:market_data_needed", category="report", fn=apiType)
        return pl.DataFrame()

    frames: list[pl.LazyFrame] = []
    for pf in parquet_files:
        try:
            lf = pl.scan_parquet(str(pf))
            schema_names = lf.collect_schema().names()
            if "apiType" not in schema_names:
                continue
            available = [c for c in keepCols if c in schema_names]
            non_meta = [c for c in available if c not in ("stockCode", "year", "quarter")]
            if not non_meta:
                continue
            lf = lf.filter(pl.col("apiType") == apiType).select(available)
            frames.append(lf)
        except (pl.exceptions.PolarsError, OSError) as exc:
            raise ScanDataError(
                "report_raw_read",
                f"{type(exc).__name__}: {exc}",
                source=pf,
            ) from exc

    if not frames:
        return pl.DataFrame()

    all_cols: set[str] = set()
    for lf in frames:
        all_cols.update(lf.collect_schema().names())
    unified: list[pl.LazyFrame] = []
    for lf in frames:
        missing = all_cols - set(lf.collect_schema().names())
        if missing:
            lf = lf.with_columns([pl.lit(None).alias(c) for c in missing])
        unified.append(lf.select(sorted(all_cols)))

    try:
        return pl.concat(unified).collect(engine="streaming")
    except (pl.exceptions.PolarsError, OSError) as exc:
        raise ScanDataError(
            "report_raw_collect",
            f"{type(exc).__name__}: {exc}",
            source=report_dir,
        ) from exc


def loadListing():
    """상장사 목록 로드.

    Returns
    -------
    pl.DataFrame
        종목코드, 종목명, 업종 등 상장사 기본 정보.

    Raises
    ------
    network.scanner.loadListing 가 발생시키는 예외 전파.

    Examples
    --------
    >>> from dartlab.scan.io.parquet import loadListing
    >>> df = loadListing()
    >>> "stockCode" in df.columns
    True

    Notes
    -----
    network/scanner.py 의 load_listing 에 위임.
    """
    from dartlab.scan.network.scanner import loadListing as _ll

    return _ll()


_RAW_FINANCE_DEFAULT_COLS: tuple[str, ...] = (
    "stockCode",
    "bsns_year",
    "reprt_nm",
    "reprt_code",
    "sj_div",
    "fs_nm",
    "account_id",
    "account_nm",
    "thstrm_amount",
    "thstrm_add_amount",
)


def _sqlEscapeLiteral(value: str) -> str:
    """SQL string literal 안의 ``'`` 를 ``''`` 로 escape.

    DART account_id / account_nm 에는 ``dart_(1)총매출액`` · ``ifrs-full_Revenue`` 같이
    SQL injection 위험은 없지만 ``'`` 가 포함된 키가 있어 IN 절 파싱이 깨진다.
    standard SQL 의 doubled-quote escape 만 적용.
    """
    return value.replace("'", "''")


def _loadRawFinanceViaDuckDb(
    financeDir: Path,
    *,
    sjDivs: list[str] | None = None,
    sinceYear: int | None = None,
    accountIds: set[str] | list[str] | None = None,
    accountNms: set[str] | list[str] | None = None,
    columns: tuple[str, ...] | list[str] | None = None,
) -> pl.LazyFrame | None:
    """raw ``finance/*.parquet`` glob → DuckDB streaming SQL → polars LazyFrame.

    프리빌드 합본 ``finance.parquet`` 이 없을 때 사용하는 fallback path. DuckDB 가
    parallel parquet scan + predicate pushdown + 자동 spill-to-disk 로 처리하여
    종목별 ThreadPool 순회 대비 빠르고 메모리 안전 (DuckDB native heap 만 사용,
    Python/Polars RSS 누적 없음).

    ``scan/finance.parquet`` 와 동일한 스키마로 반환되므로 호출자는 기존 후처리
    (``_scanFinanceFromLazy`` · ``_scanAccountFromMerged`` lazyFrame 경로) 를 그대로
    재사용한다.

    SQL 단에는 selectivity 가 높고 SQL injection 안전한 (sj_div / bsns_year) 필터만
    push-down. ``account_id`` · ``account_nm`` 매칭은 raw 데이터에 ``'`` 같은 특수
    문자가 포함된 키 (예: ``dart_(1)총매출액``) 가 있어 polars 단에서 ``is_in`` 으로
    처리한다.

    Parameters
    ----------
    financeDir : Path
        종목별 raw parquet (``{stockCode}.parquet``) 디렉토리.
    sjDivs : list[str] | None
        ``sj_div`` 필터 (예: ``["IS", "CIS"]``). None 이면 미적용.
    sinceYear : int | None
        ``bsns_year >= sinceYear`` 필터. None 이면 미적용.
    accountIds : set[str] | list[str] | None
        ``account_id`` IN 절 push-down. None/빈 컬렉션이면 미적용. ``accountNms`` 와
        OR 결합 — 두 키 어느 쪽이라도 매칭되면 통과.
    accountNms : set[str] | list[str] | None
        ``account_nm`` IN 절 push-down. None/빈 컬렉션이면 미적용.
    columns : tuple[str, ...] | list[str] | None
        반환 LazyFrame 의 SELECT 컬럼. None 이면 ``_RAW_FINANCE_DEFAULT_COLS`` 10 컬럼
        (필수 메타 + 금액). ``stockCode`` 가 포함되면 raw 의 ``stock_code`` 가 자동
        alias 된다.

    Returns
    -------
    pl.LazyFrame | None
        합본 스키마 (``stockCode`` 포함) LazyFrame. raw 디렉토리가 없거나 비었으면 None.

    Raises
    ------
    ScanDataError
        DuckDB를 불러오지 못했거나 raw parquet query가 실패한 경우.

    Notes
    -----
    - 스키마 변동 흡수: ``union_by_name=True`` 로 종목별 컬럼 차이 자동 합산.
    - ``stockCode`` 컬럼은 raw 의 ``stock_code`` (snake_case) 를 rename. 둘 다 없으면
      None 반환.
    - 결산월 캘린더 환원은 적용되지 않음 — fallback path 에서는 빌더 변환을 거치지
      않으므로 호출자가 필요시 별도 처리.
    """
    if not financeDir.exists():
        return None
    files = sorted(financeDir.glob("*.parquet"))
    if not files:
        return None

    try:
        import duckdb
    except ImportError as exc:
        raise ScanDataError(
            "finance_duckdb_import",
            f"{type(exc).__name__}: {exc}",
            source=financeDir,
        ) from exc

    pattern = str(financeDir / "*.parquet").replace("\\", "/")
    where: list[str] = []
    if sjDivs:
        # sj_div 는 고정 값셋 (IS/CIS/BS/CF) 이라 escape 불요
        sjList = ", ".join(f"'{s}'" for s in sjDivs)
        where.append(f"sj_div IN ({sjList})")
    if sinceYear is not None:
        where.append(f"TRY_CAST(bsns_year AS INTEGER) >= {int(sinceYear)}")
    if accountIds or accountNms:
        clauses: list[str] = []
        if accountIds:
            aiList = ", ".join(f"'{_sqlEscapeLiteral(s)}'" for s in accountIds)
            clauses.append(f"account_id IN ({aiList})")
        if accountNms:
            anList = ", ".join(f"'{_sqlEscapeLiteral(s)}'" for s in accountNms)
            clauses.append(f"account_nm IN ({anList})")
        where.append("(" + " OR ".join(clauses) + ")")

    con = duckdb.connect(":memory:")
    try:
        escapedPattern = _sqlEscapeLiteral(pattern)
        schemaRows = con.sql(f"DESCRIBE SELECT * FROM read_parquet('{escapedPattern}', union_by_name=true)").fetchall()
        sourceColumns = {str(row[0]) for row in schemaRows}
        filterColumns = {
            *(["sj_div"] if sjDivs else []),
            *(["bsns_year"] if sinceYear is not None else []),
            *(["account_id"] if accountIds else []),
            *(["account_nm"] if accountNms else []),
        }
        missingFilters = sorted(filterColumns - sourceColumns)
        if missingFilters:
            raise ScanDataError(
                "finance_raw_schema",
                f"missing filter columns: {', '.join(missingFilters)}",
                source=financeDir,
            )

        selectCols = list(columns) if columns else list(_RAW_FINANCE_DEFAULT_COLS)
        if columns:
            normalizedSource = sourceColumns | ({"stockCode"} if "stock_code" in sourceColumns else set())
            missingSelect = sorted(set(selectCols) - normalizedSource)
            if missingSelect:
                raise ScanDataError(
                    "finance_raw_schema",
                    f"missing selected columns: {', '.join(missingSelect)}",
                    source=financeDir,
                )
        selectExprs: list[str] = []
        for column in selectCols:
            if column == "stockCode":
                if "stock_code" in sourceColumns:
                    selectExprs.append('"stock_code" AS "stockCode"')
                elif "stockCode" in sourceColumns:
                    selectExprs.append('"stockCode"')
                else:
                    raise ScanDataError(
                        "finance_raw_schema",
                        "missing stock_code or stockCode",
                        source=financeDir,
                    )
            elif column in sourceColumns:
                selectExprs.append(f'"{column}"')

        selectSql = ", ".join(selectExprs)
        whereSql = (" WHERE " + " AND ".join(where)) if where else ""
        sql = f"SELECT {selectSql} FROM read_parquet('{escapedPattern}', union_by_name=true){whereSql}"
        df = con.sql(sql).pl()
    except ScanDataError:
        raise
    except Exception as exc:
        raise ScanDataError(
            "finance_duckdb_query",
            f"{type(exc).__name__}: {exc}",
            source=financeDir,
        ) from exc
    finally:
        con.close()

    if df.is_empty():
        return df.lazy()

    # 캘린더 환원 — prebuild 합본 (buildFinance) 와 스키마 동등화. 비12월 결산
    # 회사의 bsns_year/reprt_nm 를 결산월 SSOT 기준으로 캘린더 기준으로 환원.
    if "bsns_year" in df.columns and "reprt_nm" in df.columns:
        df = _calendarizeWithFmMap(df)

    return df.lazy()


def _scanFinanceFromLazy(
    lz: pl.LazyFrame,
    accountIds: set[str],
    accountNms: set[str],
    amountCol: str,
) -> dict[str, float]:
    """LazyFrame (합본 또는 raw glob) → 종목별 최신 연도 매칭 계정 값.

    ``_scanFinanceFromMerged`` (프리빌드 단일 파일) 와 ``_loadRawFinanceViaDuckDb``
    (raw glob fallback) 가 공유하는 후처리. fs_nm 의 연결 우선 + 종목별 latestYear
    + 매칭 row 첫 값.

    Parameters
    ----------
    lz : pl.LazyFrame
        sj_div 필터까지 적용된 LazyFrame. ``stockCode`` · ``bsns_year`` ·
        ``fs_nm`` · ``account_id`` · ``account_nm`` · ``amountCol`` 컬럼 필요.
    accountIds : set[str]
        매칭할 ``account_id`` 집합.
    accountNms : set[str]
        매칭할 ``account_nm`` 집합.
    amountCol : str
        금액 컬럼명.

    Returns
    -------
    dict[str, float]
        {종목코드: 금액(원)} — 종목별 최신 연도 첫 매칭 계정의 값.
    """
    scCol = "stockCode"
    schemaNames = set(lz.collect_schema().names())
    required = [scCol, "bsns_year", "fs_nm", "account_id", "account_nm", amountCol]
    missing = [col for col in required if col not in schemaNames]
    if missing:
        raise ScanDataError(
            "finance_schema",
            f"missing columns: {', '.join(missing)}",
        )

    base = lz.select(required).filter(
        (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
        & (pl.col("account_id").is_in(list(accountIds)) | pl.col("account_nm").is_in(list(accountNms)))
    )

    def _collectLatest(source: pl.LazyFrame) -> pl.DataFrame:
        latestYear = source.group_by(scCol).agg(pl.col("bsns_year").max().alias("_maxYear"))
        return (
            source.join(latestYear, on=scCol)
            .filter(pl.col("bsns_year") == pl.col("_maxYear"))
            .drop("_maxYear")
            .collect(engine="streaming")
        )

    # 연결 우선은 유니버스 전체가 아니라 회사별로 판정한다. 다른 회사가 연결
    # 재무제표를 냈다는 이유로 별도만 내는 회사가 사라지면 안 된다.
    matched = _collectLatest(preferConsolidatedPerCompanyLazy(base, scCol))

    result: dict[str, float] = {}
    for row in matched.iter_rows(named=True):
        code = row.get(scCol, "")
        if code and code not in result:
            val = parseNumStr(row.get(amountCol))
            if val is not None:
                result[code] = val

    return result


def _scanFinanceFromMerged(
    scanPath: Path,
    sjDivs: list[str],
    accountIds: set[str],
    accountNms: set[str],
    amountCol: str,
) -> dict[str, float]:
    """합산 finance parquet에서 종목별 최신 연도 값 추출 (프리빌드 경로).

    프리빌드 ``finance.parquet`` 을 lazy scan + sj_div 필터 후 ``_scanFinanceFromLazy``
    로 위임. raw glob fallback 도 동일 후처리를 공유한다.
    """
    lz = pl.scan_parquet(str(scanPath)).filter(pl.col("sj_div").is_in(sjDivs))
    return _scanFinanceFromLazy(lz, accountIds, accountNms, amountCol)


_VALUATION_REQUIRED_COLS: tuple[str, ...] = (
    "stockCode",
    "marketCap",
    "per",
    "pbr",
    "dividendYield",
    "current",
    "snapshotAt",
)


def loadValuationSnapshot() -> tuple[pl.DataFrame | None, datetime | None]:
    """일일 prebuild 된 밸류에이션 스냅샷 parquet 로드.

    ``dart/scan/valuation.parquet`` 는 GH Actions cron (KST 04:00) 이 네이버 API 에서
    시가총액·PER·PBR·배당수익률·현재가를 전종목 수집해 HuggingFace 에 배포한 파일이다.
    ``_ensureScanData()`` 가 HF 자동 다운로드를 보장한다.

    Returns
    -------
    frame : pl.DataFrame | None
        prebuild snapshot. 필수 컬럼 누락이나 파일 부재 시 ``None``.
    snapshotAt : datetime | None
        수집 시각 (UTC). 파일 부재 시 ``None``.

    Raises
    ------
    ScanDataError
        존재하는 valuation snapshot이 손상됐거나 필수 schema 계약을 어긴 경우.

    Examples
    --------
    >>> from dartlab.scan.io.parquet import loadValuationSnapshot
    >>> frame, ts = loadValuationSnapshot()
    >>> frame is None or "stockCode" in frame.columns
    True

    Notes
    -----
    - 호출자는 ``None`` 인 경우 네이버 실시간 수집 (``_fetchAll``) 으로 fallback 한다.
    - 스냅샷이 1일 이상 오래된 경우 상위 경로 ``_maybeWarnStale("scan")`` 가 경고.

    Guide:
        - 호출 컨텍스트 가이드.

    Capabilities:
        - ``data/dart/scan/valuation.parquet`` 로드 + 필수 컬럼 (``stockCode/marketCap/per/pbr/
          dividendYield/current/snapshotAt``) 검증 + snapshotAt UTC 타입 normalize.

    AIContext:
        ``scanValuation`` (refresh=False 경로) 가 본 함수로 prebuild 시도. AI agent 가 valuation
        axis 호출 시 1 차 ≤1 초 응답의 데이터 source.

    Guide:
        - 필수 7 컬럼 중 하나라도 누락 시 (None, None) — 호출자가 fallback path 로 전환.
        - snapshotAt 으로 데이터 freshness 명시 (호출자가 사용자에게 "N 시간 전 수집" 안내).

    When:
        호출 컨텍스트 안에서.

    How:
        ``_ensureScanData`` → 존재 시 TTL 게이트 ETag 재검증, 부재 시 HF snapshot
        best-effort 다운로드 → read → 필수 컬럼 + 빈 df 가드 →
        snapshotAt datetime/string → datetime 변환 → tuple 반환.

    Requires:
        - ``data/dart/scan/valuation.parquet``. 로컬 부재 시 HF ``dart/scan/valuation.parquet``
          (``buildValuation`` cron 산출, 매일 배포) 자동 다운로드 시도.

    SeeAlso:
        - :func:`dartlab.scan.builders.kr.core.buildValuation` — prebuild 빌더
        - :func:`dartlab.scan.financial.valuation.scanValuation` — 본 함수 호출자
    """
    scanDir = _ensureScanData()
    path = scanDir / "valuation.parquet"
    if path.exists():
        _maybeRefreshScanFile(scanDir, "valuation.parquet")
    else:
        # 콜드스타트 배선: HF 에 매일 배포되는 snapshot 을 먼저 시도한다 (1초대).
        # 실패해도 기존 계약 유지: (None, None) 반환으로 호출자가 실시간 수집 폴백.
        try:
            _downloadScanFile(scanDir, "valuation.parquet")
        except (ExceptionGroup, OSError, RuntimeError, ValueError) as exc:
            _log.warning("valuation prebuild 다운로드 실패. 실시간 수집 폴백 (%s)", exc)
    if not path.exists():
        return None, None
    try:
        frame = pl.read_parquet(str(path))
    except (pl.exceptions.PolarsError, OSError) as exc:
        raise ScanDataError(
            "valuation_snapshot_read",
            f"{type(exc).__name__}: {exc}",
            source=path,
        ) from exc
    missing = [c for c in _VALUATION_REQUIRED_COLS if c not in frame.columns]
    if missing:
        raise ScanDataError(
            "valuation_snapshot_schema",
            f"missing columns: {', '.join(missing)}",
            source=path,
        )
    if frame.is_empty():
        return None, None
    first = frame["snapshotAt"][0]
    if isinstance(first, datetime):
        snapshotAt: datetime | None = first
    else:
        try:
            snapshotAt = datetime.fromisoformat(str(first))
        except (TypeError, ValueError):
            snapshotAt = None
    return frame, snapshotAt


def scanFinanceParquets(
    statement: str,
    accountIds: set[str],
    accountNms: set[str],
    *,
    amountCol: str = "thstrm_amount",
) -> dict[str, float]:
    """finance parquet 전수 스캔 → 종목별 계정 값.

    scan/finance.parquet 프리빌드가 있으면 단일 파일에서 즉시 필터.
    없으면 종목별 parquet 순회 (fallback).

    Parameters
    ----------
    statement : str
        재무제표 구분 (예: "IS", "BS", "CF").
    account_ids : set[str]
        매칭할 account_id 집합.
    account_nms : set[str]
        매칭할 account_nm 집합.
    amount_col : str
        금액 컬럼명 (기본 "thstrm_amount").

    Returns
    -------
    dict[str, float]
        {종목코드: 금액(원)} — 종목별 최신 연도 첫 매칭 계정의 값.

    Raises
    ------
    ScanDataError
        존재하는 prebuild, raw finance parquet 또는 필수 schema가 손상된 경우.

    Examples
    --------
    >>> from dartlab.scan.io.parquet import scanFinanceParquets
    >>> revMap = scanFinanceParquets("IS", {"Revenue"}, {"매출액"})
    >>> revMap.get("005930")  # 삼성전자 최신년 매출액
    250000000000000

    Guide:
        - 호출 컨텍스트 가이드.

    Capabilities:
        - prebuild ``scan/finance.parquet`` 우선 LazyFrame scan + sj_div + 계정 ID/이름 필터 →
          종목별 최신 연도 첫 매칭 값. 없으면 raw glob DuckDB streaming SQL fallback.
        - 연결재무 우선 (fs_nm contains "연결") + 최신 bsns_year per stock + accountIds 또는
          accountNms 중 어느 한쪽 매치.

    AIContext:
        scan financial axis (profitability/growth/quality/...) 와 ``scanAccount`` 가 본 함수로
        종목별 매출/영업이익/순이익 등의 latest 값을 dict 로 받는다. AI 가 횡단 재무 지표 매핑이
        필요할 때 본 함수가 1 차 source.

    Guide:
        - accountIds (XBRL tag) + accountNms (한글 표시명) 중 어느 한쪽이 매칭되면 통과.
          ``REVENUE_IDS`` / ``REVENUE_NMS`` 같이 module 상수가 SSOT.
        - prebuild 없으면 자동으로 raw glob DuckDB 경로 — 메모리 안전 (네이티브 spill-to-disk).

    When:
        scan financial 7 axis 함수 내부에서. 직접 사용은 prototype.

    How:
        ``_ensureScanData`` → prebuild scan/finance.parquet 시도 ``_scanFinanceFromMerged`` →
        실패 시 ``_loadRawFinanceViaDuckDb`` (raw glob streaming SQL) + ``_scanFinanceFromLazy``.

    Requires:
        - 로컬 ``data/dart/scan/finance.parquet`` (``buildFinance`` 산출) 또는
          ``data/dart/finance/{stockCode}.parquet`` (DuckDB fallback)
        - DuckDB 패키지 (fallback 경로)

    SeeAlso:
        - :func:`scanParquets` — report 전용 (apiType 매칭)
        - :func:`_loadRawFinanceViaDuckDb` · :func:`_scanFinanceFromLazy` · :func:`_scanFinanceFromMerged`
        - :data:`REVENUE_IDS` · :data:`OP_IDS` · :data:`NI_IDS` · :data:`TA_IDS` · :data:`EQ_IDS`
    """
    sj_divs = [statement] if statement != "IS" else ["IS", "CIS"]

    # 1순위: 프리빌드 scan parquet (없으면 자동 다운로드 시도)
    scanDir = _ensureScanData()
    scan_path = scanDir / "finance.parquet"
    if scan_path.exists():
        try:
            return _scanFinanceFromMerged(scan_path, sj_divs, accountIds, accountNms, amountCol)
        except ScanDataError:
            raise
        except (pl.exceptions.PolarsError, OSError) as exc:
            raise ScanDataError(
                "finance_prebuild_read",
                f"{type(exc).__name__}: {exc}",
                source=scan_path,
            ) from exc

    # 2순위: raw glob → DuckDB streaming SQL (fallback)
    from dartlab.core.dataLoader import _dataDir

    finance_dir = Path(_dataDir("finance"))
    lz = _loadRawFinanceViaDuckDb(
        finance_dir,
        sjDivs=sj_divs,
        accountIds=accountIds,
        accountNms=accountNms,
    )
    if lz is None:
        return {}

    _log.info("scanFinanceParquets: DuckDB raw glob fallback 사용")
    try:
        return _scanFinanceFromLazy(lz, accountIds, accountNms, amountCol)
    except ScanDataError:
        raise
    except (pl.exceptions.PolarsError, OSError) as exc:
        raise ScanDataError(
            "finance_raw_transform",
            f"{type(exc).__name__}: {exc}",
            source=finance_dir,
        ) from exc
