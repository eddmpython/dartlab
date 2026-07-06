"""KR scan report parquet builder.

Capabilities:
    - Splits raw all-company report parquet files into API-type scan sources.

Args:
    Public entry points accept prebuild window and logging options.

Returns:
    Generated report parquet paths.

Example:
    >>> from dartlab.scan.builders.kr.report.build import buildReport
    >>> paths = buildReport(sinceYear=2021, verbose=True)

Guide:
    Report field metadata belongs in ``report.fields`` and ``report.fieldCatalog``.
    This module owns only report source build orchestration.

SeeAlso:
    ``report.fields``, ``scan.io.parquet``, and ``core``.

Requires:
    Raw DART report parquet files with ``apiType`` columns.

AIContext:
    This module provides the non-financial scan source used by governance,
    workforce, capital, debt, audit, and related scan axes.

LLM Specifications:
    AntiPatterns: Do not add finance/docs/valuation build logic here.
    OutputSchema: ``report/{apiType}.parquet`` files.
    Prerequisites: Raw report files under the configured data root.
    Freshness: Rebuilt by the scan prebuild workflow.
    Dataflow: raw report parquet -> apiType buckets -> merged parquet files.
    TargetMarkets: KR DART scan report.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Iterable

import polars as pl

from dartlab.core.extractionCatalog import DartSource, getExtractionConcepts
from dartlab.scan.builders.kr.common import BATCH_SIZE as _BATCH
from dartlab.scan.builders.kr.common import mergeBatchFiles as _mergeBatchFiles
from dartlab.scan.builders.kr.common import releaseNativeMemory as _releaseNativeMemory
from dartlab.scan.builders.kr.common import reportDir as _reportDir
from dartlab.scan.builders.kr.common import say as _say
from dartlab.scan.builders.kr.common import scanDir as _scanDir

# DART report apiType 중 전종목 실측(2026-07-07) payload 0 인 것. 카탈로그엔 개념이 있으나
# 수집 응답이 status-only(데이터 컬럼 전무)라 스크리닝 불가. 손 선별이 아니라 측정에 의한 도태
# (도태는 등재 게이트가 아니라 측정으로: feedback_exhaustive_no_curation). 데이터가 채워지면
# 본 set 에서 빼면 자동 편입된다.
_NO_DATA_REPORT_APITYPES: frozenset[str] = frozenset(
    {"hybridSecurities", "contingentCapital", "executivePayByType", "executivePayTotal"}
)


def _reportApiTypes() -> list[str]:
    """카탈로그 report-surface 개념에서 데이터 보유 apiType 을 도출한다 (SSOT 구동, 손 리스트 0).

    ``core.extractionCatalog`` 의 report 개념(28)에서 실측 무데이터 4 종을 뺀 순서보존 리스트.
    """
    keys = [
        c.dart.key for c in getExtractionConcepts() if isinstance(c.dart, DartSource) and c.dart.surface == "report"
    ]
    return [k for k in keys if k not in _NO_DATA_REPORT_APITYPES]


# 실소비자(scan 엔진 scanParquets + landing 터미널)가 사용하는 apiType SSOT. 카탈로그 도출(28)에서
# 무데이터 4 를 뺀 24. 정합성은 tests/scan/test_prebuild_contract.py 가 강제 (누락 시 fallback
# per-file scan path 가 polars streaming concat 단계에서 thrift error 로 axis 전체 실패).
# scan/io/parquet._REQUIRED_REPORT_FILES 가 본 리스트에서 파생되어 자동 동기화된다.
SCAN_API_TYPES = _reportApiTypes()


def buildReport(*, sinceYear: int = 2016, verbose: bool = True, apiTypes: Iterable[str] | None = None) -> list[Path]:
    """report/*.parquet → apiType별 분리 parquet 프리빌드.

    ``SCAN_API_TYPES`` (카탈로그 도출 24 종: majorHolder/executive/employee/dividend/topPay/
    stockTotal/debtSecurities/...) 의 각 apiType 마다 종목별 raw row 를 모아 별도 parquet 으로
    출력. 단일 합본이 아닌 apiType별 분할 (apiType 마다 스키마·사용 단위가 다르므로).

    Parameters
    ----------
    sinceYear : int
        포함할 최소 ``year`` (``year >= sinceYear``). 기본 2016 — raw 수집 시작 연도와
        일치, 정기보고서 시계열을 전 기간 노출 (터미널 재무 전체화면·우측 팩트).
    verbose : bool
        진행 로그 출력 여부.
    apiTypes : Iterable[str] | None
        생성할 apiType 목록. ``None`` 이면 :data:`SCAN_API_TYPES` 전체를 생성한다.

    Returns
    -------
    list[Path]
        생성된 apiType별 parquet 경로 목록. data 없는 apiType 은 제외.

    Raises
    ------
    polars.PolarsError
        report parquet 손상 또는 ``sink_parquet`` 실패 시.

    Examples
    --------
    >>> from dartlab.scan.builders.kr.report.build import buildReport
    >>> paths = buildReport(sinceYear=2021, verbose=True)
    >>> [p.name for p in paths[:3]]

    Capabilities:
        - 종목별 raw report parquet 을 각 apiType 별로 split. ``apiType`` 컬럼 == 카테고리
          매칭으로 종목 row 를 해당 apiType bucket 에 추가. 200 종목 단위 배치 청크 → merge.
        - apiType 마다 다른 컬럼 스키마 흡수 (``diagonal_relaxed`` concat).

    AIContext:
        ``scan("governance")`` (executive/majorHolder/outsideDirector), ``scan("workforce")``
        (employee/executivePay*), ``scan("capital")`` (dividend/treasuryStock/capitalChange/
        corporateBond), ``scan("audit")`` (auditOpinion/minorityHolder) 등 비재무 scan 축의
        1 차 source. AI 가 axis 호출 시 본 빌드 산출물을 LazyFrame 으로 필터한다.

    Guide:
        - 출력 경로: ``data/dart/scan/report/{apiType}.parquet``
        - 각 apiType 중 일부만 raw 에 있으면 그 apiType 만 생성 (나머지 silent skip).
        - 파일 크기는 apiType 마다 차이 큰 — employee/executive 가 가장 크다.

    When:
        매 prebuild 사이클 (KST 03:00 / 15:00). buildChanges/buildFinance 직후.
        사용자 직접 호출 드물다.

    How:
        ``buildScan`` 의 4 번째 단계. apiType 별 buffer dict (``apiChunks``) 를 유지하면서
        종목당 raw 를 각 apiType 으로 filter → buffer push. ``_BATCH`` (200) 도달 시 임시
        청크 flush. 종료 시 잔존 청크 flush + apiType 마다 ``_mergeBatchFiles`` 단일 파일 머지.
        apiType별 임시 디렉토리 (``_tmp_{apiType}/``) 사용 후 cleanup.

    Requires:
        - 로컬 ``data/dart/report/{stockCode}.parquet`` (Data Sync 가 채움)
        - ``apiType`` 컬럼 (필수, 없으면 종목 skip)

    SeeAlso:
        - :data:`SCAN_API_TYPES` — 처리 대상 각 apiType list
        - :func:`dartlab.scan.builders.kr.core.buildScan` — 본 함수 포함 통합 호출
        - :func:`dartlab.scan.builders.kr.docs.changes.buildChanges`
        - :func:`dartlab.scan.builders.kr.financeBuild.buildFinance`
        - :mod:`dartlab.scan.io.parquet` — :func:`scanParquets` 가 본 빌드 출력 lazy scan
    """
    repDir = _reportDir()
    outDir = _scanDir() / "report"
    outDir.mkdir(parents=True, exist_ok=True)

    selectedApiTypes = tuple(apiTypes) if apiTypes is not None else tuple(SCAN_API_TYPES)
    unknown = sorted(set(selectedApiTypes) - set(SCAN_API_TYPES))
    if unknown:
        raise ValueError(f"알 수 없는 report apiType: {unknown}")

    allFiles = sorted(repDir.glob("*.parquet"))
    if not allFiles:
        if verbose:
            _say("report parquet 없음 — 빌드 건너뜀")
        return []

    if verbose:
        _say(f"[report] {len(allFiles)}종목 → apiType별 분리 ({len(selectedApiTypes)}개)")

    t0 = time.perf_counter()

    apiBatchDirs: dict[str, Path] = {}
    apiBatchIdx: dict[str, int] = {}
    apiChunks: dict[str, list[pl.DataFrame]] = {}
    apiRows: dict[str, int] = {}
    for at in selectedApiTypes:
        bd = outDir / f"_tmp_{at}"
        bd.mkdir(parents=True, exist_ok=True)
        apiBatchDirs[at] = bd
        apiBatchIdx[at] = 0
        apiChunks[at] = []
        apiRows[at] = 0

    processed = 0

    for i, pf in enumerate(allFiles):
        try:
            df = pl.read_parquet(str(pf))
        except (pl.exceptions.PolarsError, OSError):
            continue

        if "apiType" not in df.columns:
            continue

        if "stockCode" not in df.columns and "stock_code" not in df.columns:
            df = df.with_columns(pl.lit(pf.stem).alias("stockCode"))

        if "year" in df.columns:
            df = df.with_columns(pl.col("year").cast(pl.Utf8).str.to_integer(strict=False).alias("_yearInt"))
            df = df.filter(pl.col("_yearInt").is_null() | (pl.col("_yearInt") >= sinceYear)).drop("_yearInt")

        processed += 1

        for apiType in selectedApiTypes:
            sub = df.filter(pl.col("apiType") == apiType)
            if sub.height > 0:
                apiChunks[apiType].append(sub)
                apiRows[apiType] += sub.height

                if len(apiChunks[apiType]) >= _BATCH:
                    batch = pl.concat(apiChunks[apiType], how="diagonal_relaxed")
                    idx = apiBatchIdx[apiType]
                    batch.write_parquet(
                        str(apiBatchDirs[apiType] / f"batch_{idx:03d}.parquet"),
                        compression="zstd",
                    )
                    del batch
                    apiChunks[apiType] = []
                    apiBatchIdx[apiType] = idx + 1
                    _releaseNativeMemory()

        if verbose and (i + 1) % 500 == 0:
            _say(f"  [{i + 1}/{len(allFiles)}] {processed}ok {time.perf_counter() - t0:.0f}s")

    outputs: list[Path] = []
    for apiType in selectedApiTypes:
        if apiChunks[apiType]:
            batch = pl.concat(apiChunks[apiType], how="diagonal_relaxed")
            idx = apiBatchIdx[apiType]
            batch.write_parquet(
                str(apiBatchDirs[apiType] / f"batch_{idx:03d}.parquet"),
                compression="zstd",
            )
            del batch
            apiBatchIdx[apiType] = idx + 1
            _releaseNativeMemory()

        if apiBatchIdx[apiType] == 0:
            shutil.rmtree(apiBatchDirs[apiType], ignore_errors=True)
            continue

        outPath = outDir / f"{apiType}.parquet"
        _mergeBatchFiles(apiBatchDirs[apiType], outPath, how="diagonal_relaxed")
        shutil.rmtree(apiBatchDirs[apiType], ignore_errors=True)
        _releaseNativeMemory()

        diskMb = outPath.stat().st_size / 1024 / 1024
        outputs.append(outPath)
        if verbose:
            _say(f"  {apiType}: {apiRows[apiType]:,}행, {diskMb:.1f}MB")

    elapsed = time.perf_counter() - t0
    if verbose:
        _say(f"  report 완료: {len(outputs)}개 apiType, {elapsed:.0f}초")

    return outputs
