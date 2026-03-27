"""전종목 scan 프리빌드 빌더.

docs → changes, finance → 합산, report → apiType별 분리.
실험 014/015에서 검증된 로직을 프로덕션화.
배치를 중간 파일로 쓰고 마지막에 합산하여 segfault 방지.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path

import polars as pl

# scanner에서 실제 사용하는 apiType 10개
SCAN_API_TYPES = [
    "majorHolder",
    "executive",
    "employee",
    "executivePayAllTotal",
    "executivePayIndividual",
    "auditOpinion",
    "dividend",
    "treasuryStock",
    "capitalChange",
    "corporateBond",
]

_BATCH = 200


def _scanDir() -> Path:
    """scan 출력 디렉토리."""
    from dartlab.core.dataLoader import _dataDir

    return Path(_dataDir("scan"))


def _docsDir() -> Path:
    from dartlab.core.dataLoader import _dataDir

    return Path(_dataDir("docs"))


def _financeDir() -> Path:
    from dartlab.core.dataLoader import _dataDir

    return Path(_dataDir("finance"))


def _reportDir() -> Path:
    from dartlab.core.dataLoader import _dataDir

    return Path(_dataDir("report"))


def _log(msg: str) -> None:
    print(msg)


def _mergeBatchFiles(batchDir: Path, outputPath: Path, *, how: str = "vertical") -> int:
    """배치 파일들을 읽어서 1개로 합산. 반환: 총 행수."""
    batchFiles = sorted(batchDir.glob("batch_*.parquet"))
    if not batchFiles:
        return 0

    parts = [pl.read_parquet(str(f)) for f in batchFiles]
    merged = pl.concat(parts, how=how)
    merged.write_parquet(str(outputPath), compression="zstd")
    totalRows = merged.height
    del merged, parts
    return totalRows


# ── changes ──────────────────────────────────────────────────────────


def _buildRawChanges(parquetPath: Path, stockCode: str, sinceYear: int = 2021) -> pl.DataFrame | None:
    """raw docs parquet → section 단위 changes."""
    try:
        raw = pl.read_parquet(str(parquetPath))
    except (pl.exceptions.PolarsError, OSError):
        return None

    needed = {"year", "section_order", "section_title", "section_content"}
    if not needed.issubset(set(raw.columns)):
        return None

    raw = raw.filter(pl.col("year").cast(pl.Utf8).str.to_integer(strict=False) >= sinceYear - 1)
    if raw.height < 2:
        return None

    work = raw.select(["year", "section_order", "section_title", "section_content"])
    work = work.sort(["section_order", "section_title", "year"])

    work = work.with_columns([
        pl.col("year").shift(1).over(["section_order", "section_title"]).alias("_prevYear"),
        pl.col("section_content").shift(1).over(["section_order", "section_title"]).alias("_prevContent"),
    ])

    work = work.with_columns([
        pl.col("section_content").hash().alias("_hash"),
        pl.col("_prevContent").hash().alias("_prevHash"),
        pl.col("section_content").str.len_chars().alias("sizeB"),
        pl.col("_prevContent").str.len_chars().alias("sizeA"),
        pl.col("section_content").str.slice(0, 200).alias("preview"),
    ])

    changes = work.filter(
        pl.col("_prevYear").is_not_null()
        & ~(pl.col("section_content").is_null() & pl.col("_prevContent").is_null())
        & (
            (pl.col("_hash") != pl.col("_prevHash"))
            | pl.col("section_content").is_null()
            | pl.col("_prevContent").is_null()
        )
    )

    if changes.height == 0:
        return None

    numPattern = r"[\d,.]+"
    changes = changes.with_columns([
        pl.col("section_content").str.replace_all(numPattern, "N").alias("_stripped"),
        pl.col("_prevContent").str.replace_all(numPattern, "N").alias("_prevStripped"),
    ])

    changes = changes.with_columns(
        pl.when(pl.col("_prevContent").is_null())
        .then(pl.lit("appeared"))
        .when(pl.col("section_content").is_null())
        .then(pl.lit("disappeared"))
        .when(pl.col("_stripped") == pl.col("_prevStripped"))
        .then(pl.lit("numeric"))
        .when(
            (pl.col("sizeA") > 0)
            & ((pl.col("sizeB").cast(pl.Int64) - pl.col("sizeA").cast(pl.Int64)).abs().cast(pl.Float64)
               / pl.col("sizeA").cast(pl.Float64) > 0.5)
        )
        .then(pl.lit("structural"))
        .otherwise(pl.lit("wording"))
        .alias("changeType")
    )

    changes = changes.filter(pl.col("year").cast(pl.Utf8).str.to_integer(strict=False) >= sinceYear)

    return changes.select([
        pl.col("_prevYear").alias("fromPeriod"),
        pl.col("year").alias("toPeriod"),
        pl.col("section_title").alias("sectionTitle"),
        pl.col("changeType"),
        pl.col("sizeA"),
        pl.col("sizeB"),
        (pl.col("sizeB").cast(pl.Int64) - pl.col("sizeA").cast(pl.Int64)).alias("sizeDelta"),
        pl.col("preview"),
        pl.lit(stockCode).alias("stockCode"),
    ])


def buildChanges(*, sinceYear: int = 2021, verbose: bool = True) -> Path | None:
    """docs → changes 프리빌드. 반환: 출력 parquet 경로."""
    docsDir = _docsDir()
    outDir = _scanDir()
    outDir.mkdir(parents=True, exist_ok=True)
    outputPath = outDir / "changes.parquet"
    batchDir = outDir / "_tmp_changes"
    batchDir.mkdir(parents=True, exist_ok=True)

    allFiles = sorted(docsDir.glob("*.parquet"))
    if not allFiles:
        if verbose:
            _log("docs parquet 없음 — changes 빌드 건너뜀")
        return None

    if verbose:
        _log(f"[changes] {len(allFiles)}종목, sinceYear={sinceYear}")

    t0 = time.perf_counter()
    batchChunks: list[pl.DataFrame] = []
    success = 0
    failed = 0
    totalRows = 0
    batchIdx = 0

    for i, pf in enumerate(allFiles):
        result = _buildRawChanges(pf, pf.stem, sinceYear)
        if result is not None and result.height > 0:
            batchChunks.append(result)
            totalRows += result.height
            success += 1
        else:
            failed += 1

        if len(batchChunks) >= _BATCH or i == len(allFiles) - 1:
            if batchChunks:
                batch = pl.concat(batchChunks)
                batch.write_parquet(str(batchDir / f"batch_{batchIdx:03d}.parquet"), compression="zstd")
                del batch
                batchChunks = []
                batchIdx += 1

        if verbose and (i + 1) % 500 == 0:
            _log(f"  [{i+1}/{len(allFiles)}] {success}ok {failed}fail {totalRows:,}rows {time.perf_counter()-t0:.0f}s")

    if batchIdx == 0:
        if verbose:
            _log("  changes 결과 없음")
        shutil.rmtree(batchDir, ignore_errors=True)
        return None

    _mergeBatchFiles(batchDir, outputPath)
    shutil.rmtree(batchDir, ignore_errors=True)

    elapsed = time.perf_counter() - t0
    diskMb = outputPath.stat().st_size / 1024 / 1024
    if verbose:
        _log(f"  완료: {success}종목, {totalRows:,}행, {diskMb:.1f}MB, {elapsed:.0f}초")

    return outputPath


# ── finance ──────────────────────────────────────────────────────────


def buildFinance(*, sinceYear: int = 2021, verbose: bool = True) -> Path | None:
    """finance 전종목 합산. 반환: 출력 parquet 경로."""
    finDir = _financeDir()
    outDir = _scanDir()
    outDir.mkdir(parents=True, exist_ok=True)
    outputPath = outDir / "finance.parquet"
    batchDir = outDir / "_tmp_finance"
    batchDir.mkdir(parents=True, exist_ok=True)

    allFiles = sorted(finDir.glob("*.parquet"))
    if not allFiles:
        if verbose:
            _log("finance parquet 없음 — 빌드 건너뜀")
        return None

    if verbose:
        _log(f"[finance] {len(allFiles)}종목, sinceYear={sinceYear}")

    t0 = time.perf_counter()
    batchChunks: list[pl.DataFrame] = []
    success = 0
    totalRows = 0
    batchIdx = 0

    for i, pf in enumerate(allFiles):
        try:
            df = pl.read_parquet(str(pf))
        except (pl.exceptions.PolarsError, OSError):
            continue

        if "stockCode" not in df.columns and "stock_code" not in df.columns:
            df = df.with_columns(pl.lit(pf.stem).alias("stockCode"))
        elif "stock_code" in df.columns and "stockCode" not in df.columns:
            df = df.rename({"stock_code": "stockCode"})

        if "bsns_year" in df.columns:
            df = df.filter(
                pl.col("bsns_year").cast(pl.Utf8).str.to_integer(strict=False) >= sinceYear
            )

        if df.height == 0:
            continue

        batchChunks.append(df)
        totalRows += df.height
        success += 1

        if len(batchChunks) >= _BATCH or i == len(allFiles) - 1:
            if batchChunks:
                batch = pl.concat(batchChunks, how="diagonal_relaxed")
                batch.write_parquet(str(batchDir / f"batch_{batchIdx:03d}.parquet"), compression="zstd")
                del batch
                batchChunks = []
                batchIdx += 1

        if verbose and (i + 1) % 500 == 0:
            _log(f"  [{i+1}/{len(allFiles)}] {success}ok {totalRows:,}rows {time.perf_counter()-t0:.0f}s")

    if batchIdx == 0:
        if verbose:
            _log("  finance 결과 없음")
        shutil.rmtree(batchDir, ignore_errors=True)
        return None

    _mergeBatchFiles(batchDir, outputPath, how="diagonal_relaxed")
    shutil.rmtree(batchDir, ignore_errors=True)

    elapsed = time.perf_counter() - t0
    diskMb = outputPath.stat().st_size / 1024 / 1024
    if verbose:
        _log(f"  완료: {success}종목, {totalRows:,}행, {diskMb:.1f}MB, {elapsed:.0f}초")

    return outputPath


# ── report ───────────────────────────────────────────────────────────


def buildReport(*, sinceYear: int = 2021, verbose: bool = True) -> list[Path]:
    """report → apiType별 분리 parquet. 반환: 생성된 파일 경로 목록."""
    repDir = _reportDir()
    outDir = _scanDir() / "report"
    outDir.mkdir(parents=True, exist_ok=True)

    allFiles = sorted(repDir.glob("*.parquet"))
    if not allFiles:
        if verbose:
            _log("report parquet 없음 — 빌드 건너뜀")
        return []

    if verbose:
        _log(f"[report] {len(allFiles)}종목 → apiType별 분리")

    t0 = time.perf_counter()

    # apiType별 배치 디렉토리
    apiBatchDirs: dict[str, Path] = {}
    apiBatchIdx: dict[str, int] = {}
    apiChunks: dict[str, list[pl.DataFrame]] = {}
    apiRows: dict[str, int] = {}
    for at in SCAN_API_TYPES:
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
            df = df.with_columns(
                pl.col("year").cast(pl.Utf8).str.to_integer(strict=False).alias("_yearInt")
            )
            df = df.filter(
                pl.col("_yearInt").is_null() | (pl.col("_yearInt") >= sinceYear)
            ).drop("_yearInt")

        processed += 1

        for apiType in SCAN_API_TYPES:
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

        if verbose and (i + 1) % 500 == 0:
            _log(f"  [{i+1}/{len(allFiles)}] {processed}ok {time.perf_counter()-t0:.0f}s")

    # 남은 청크 flush + 합산
    outputs: list[Path] = []
    for apiType in SCAN_API_TYPES:
        # 남은 청크 쓰기
        if apiChunks[apiType]:
            batch = pl.concat(apiChunks[apiType], how="diagonal_relaxed")
            idx = apiBatchIdx[apiType]
            batch.write_parquet(
                str(apiBatchDirs[apiType] / f"batch_{idx:03d}.parquet"),
                compression="zstd",
            )
            del batch
            apiBatchIdx[apiType] = idx + 1

        if apiBatchIdx[apiType] == 0:
            shutil.rmtree(apiBatchDirs[apiType], ignore_errors=True)
            continue

        outPath = outDir / f"{apiType}.parquet"
        _mergeBatchFiles(apiBatchDirs[apiType], outPath, how="diagonal_relaxed")
        shutil.rmtree(apiBatchDirs[apiType], ignore_errors=True)

        diskMb = outPath.stat().st_size / 1024 / 1024
        outputs.append(outPath)
        if verbose:
            _log(f"  {apiType}: {apiRows[apiType]:,}행, {diskMb:.1f}MB")

    elapsed = time.perf_counter() - t0
    if verbose:
        _log(f"  report 완료: {len(outputs)}개 apiType, {elapsed:.0f}초")

    return outputs


# ── 전체 빌드 ────────────────────────────────────────────────────────


def buildScan(*, sinceYear: int = 2021, verbose: bool = True) -> dict[str, Path | list[Path] | None]:
    """changes + finance + report 전체 프리빌드."""
    if verbose:
        _log(f"전종목 scan 프리빌드 시작 (sinceYear={sinceYear})")
        _log("=" * 60)

    results: dict[str, Path | list[Path] | None] = {}

    results["changes"] = buildChanges(sinceYear=sinceYear, verbose=verbose)
    results["finance"] = buildFinance(sinceYear=sinceYear, verbose=verbose)
    results["report"] = buildReport(sinceYear=sinceYear, verbose=verbose)

    if verbose:
        _log("=" * 60)
        scanDir = _scanDir()
        if scanDir.exists():
            totalMb = sum(
                f.stat().st_size for f in scanDir.rglob("*.parquet")
            ) / 1024 / 1024
            _log(f"scan 전체: {totalMb:.1f}MB")

    return results
