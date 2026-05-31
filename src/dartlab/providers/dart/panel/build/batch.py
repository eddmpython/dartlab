"""panel 전종목 batch 빌드 (L1 build, multiprocessing) — builder 단일 빌드의 fan-out.

``builder.buildPanel`` 을 종목별 worker 로 병렬 실행 (strict per-corp, memory 무관). ref table 은
``_initWorker`` 가 worker 당 1회 load + token pre-compute → 매 row matchToRef 의 row iter 회피.
단일 빌드(buildPanel/buildPanelBaseline)는 ``builder`` 에, 본 모듈은 병렬 fan-out + CLI entry 만.

LLM Specifications:
    AntiPatterns:
        - Pool.map 금지 — large input memory 폭발. imap_unordered chunk.
        - worker 간 ref 재로드 금지 — _initWorker 1회 load.
        - 단일 빌드 로직 중복 금지 — builder.buildPanel 위임.
    OutputSchema:
        - ``buildPanelAll(*, refPath, outBaseDir, codes, numWorkers) -> dict[code, (periodCount, totalRow)]``.
    Prerequisites:
        - 전종목 zip + ref parquet. multiprocessing.
    Freshness:
        - 분기 incremental — changed code 만.
    Dataflow:
        - codes → Pool(_initWorker) → _buildOne(builder.buildPanel) → 집계.
    TargetMarkets:
        - KR (DART).
"""

from __future__ import annotations

import logging
import multiprocessing as mp
import time
from pathlib import Path

import polars as pl

import dartlab.config as _cfg

from .builder import buildPanel, buildPanelBaseline

_log = logging.getLogger(__name__)

_GLOBAL_REF: pl.DataFrame | None = None


def _initWorker(refPath: str) -> None:
    """multiprocessing worker init — ref table load + token pre-compute.

    refMatcher token set 을 worker 시작 시 한 번 계산 → 매 row matchToRef 의 row iter 회피.

    Args:
        refPath: ref parquet 경로.

    Returns:
        None.

    Raises:
        없음.

    Example:
        >>> _initWorker("data/dart/panelXbrlRef.parquet")  # doctest: +SKIP
    """
    global _GLOBAL_REF
    _GLOBAL_REF = pl.read_parquet(refPath)
    from .refScan.refMatcher import precomputeRefTokens, setGlobalRefTokens

    setGlobalRefTokens(precomputeRefTokens(_GLOBAL_REF))


def _buildOne(args: tuple[str, str, str]) -> tuple[str, int, int, float]:
    """worker entry — (code, refPath, outBaseDir) → (code, periodCount, totalRow, elapsed).

    Args:
        args: ``(code, refPath, outBaseDir)`` 튜플. pickleable.

    Returns:
        ``(code, periodCount, totalRow, elapsed)``. 실패 시 (code, 0, 0, elapsed).

    Raises:
        없음 — 빌드 실패 흡수.

    Example:
        >>> _buildOne(("005930", "ref.parquet", "data/dart/panel"))  # doctest: +SKIP
    """
    code, refPath, outBaseDir = args
    global _GLOBAL_REF
    t0 = time.perf_counter()
    try:
        ref = _GLOBAL_REF
        if ref is None:
            ref = pl.read_parquet(refPath)
        result = buildPanel(code, refDf=ref, outBaseDir=Path(outBaseDir), overwrite=True, verbose=False)
        return (code, len(result), sum(result.values()), time.perf_counter() - t0)
    except (OSError, ValueError, RuntimeError, pl.exceptions.PolarsError) as exc:
        _log.warning("buildPanel 실패 %s: %s", code, exc)
        return (code, 0, 0, time.perf_counter() - t0)


def buildPanelAll(
    *,
    refPath: str | Path = "data/dart/panelXbrlRef.parquet",
    outBaseDir: str | Path = "data/dart/panel",
    codes: list[str] | None = None,
    numWorkers: int = 8,
    progressEvery: int = 50,
    verbose: bool = True,
) -> dict[str, tuple[int, int]]:
    """전종목 panel 빌드 — multiprocessing.

    Args:
        refPath: panelXbrlRef ref parquet.
        outBaseDir: 출력 base dir.
        codes: 종목 list. None = ``data/dart/original/docs/`` 의 모든 종목.
        numWorkers: Pool workers (IO heavy, 기본 8).
        progressEvery: 진행 로그 빈도.
        verbose: 진행 로그.

    Returns:
        ``{code: (periodCount, totalRow)}`` dict.

    Raises:
        없음 — 종목별 실패 흡수.

    Example:
        >>> buildPanelAll(codes=["005930", "005380"])  # doctest: +SKIP

    SeeAlso:
        - ``builder.buildPanel`` — 단일 종목 빌드 (worker 가 위임).
        - ``builder.buildPanelBaseline`` — 5 baseline 검증.

    Requires:
        - data/dart/original/docs/{code}/*.zip 전종목. multiprocessing.

    Capabilities:
        - 전종목(~2,900) panel artifact 일괄 생산 (8코어 ~2.6h).

    Guide:
        - CI sync 잡 또는 운영자. memory 무관(strict per-corp worker).

    AIContext:
        - imap_unordered chunk=4 — IO/CPU 균형.

    When:
        - 전종목(또는 changed codes) 을 일괄 빌드할 때 (CI sync / 운영자).

    How:
        - Pool(_initWorker) 로 종목별 builder.buildPanel 병렬 실행 → 통계 집계.

    LLM Specifications:
        AntiPatterns:
            - Pool.map 금지 — large input memory 폭발. imap_unordered.
            - worker 간 ref 재로드 금지 — _initWorker 1회 load.
        OutputSchema:
            - ``dict[str, tuple[int, int]]``.
        Prerequisites:
            - 전종목 zip + ref parquet.
        Freshness:
            - 분기 incremental — changed code 만.
        Dataflow:
            - codes → Pool(_initWorker) → _buildOne → 집계.
        TargetMarkets:
            - KR (DART).
    """
    if codes is None:
        baseDir = Path(_cfg.dataDir) / "dart" / "original" / "docs"
        codes = sorted([d.name for d in baseDir.iterdir() if d.is_dir()])

    if verbose:
        _log.info("buildPanelAll: %d 종목, %d workers", len(codes), numWorkers)

    refPathStr = str(refPath)
    outBaseStr = str(outBaseDir)
    Path(outBaseStr).mkdir(parents=True, exist_ok=True)

    args = [(c, refPathStr, outBaseStr) for c in codes]
    result: dict[str, tuple[int, int]] = {}
    processed = 0
    failed = 0
    totalRows = 0
    t0 = time.perf_counter()
    with mp.Pool(processes=numWorkers, initializer=_initWorker, initargs=(refPathStr,)) as pool:
        for code, pcount, rowCount, _elapsed in pool.imap_unordered(_buildOne, args, chunksize=4):
            result[code] = (pcount, rowCount)
            processed += 1
            totalRows += rowCount
            if pcount == 0:
                failed += 1
            if verbose and processed % progressEvery == 0:
                wall = time.perf_counter() - t0
                rate = processed / wall if wall > 0 else 0
                eta = (len(codes) - processed) / rate if rate > 0 else 0
                _log.info(
                    "[%d/%d] %.1f code/s, ETA %.1f min, totalRows=%d, failed=%d",
                    processed,
                    len(codes),
                    rate,
                    eta / 60,
                    totalRows,
                    failed,
                )
    if verbose:
        wall = time.perf_counter() - t0
        _log.info("완료: %d codes, %d failed, %d totalRows, %.1f min", len(codes), failed, totalRows, wall / 60)
    return result


def _main() -> None:
    """CLI entry — ``python -X utf8 -m dartlab.providers.dart.panel.build --codes 005930``.

    Args:
        없음 (argparse).

    Returns:
        None.

    Raises:
        없음.

    Example:
        >>> _main()  # doctest: +SKIP
    """
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser(description="panel artifact 빌드")
    ap.add_argument("--codes", type=str, default="", help="콤마구분 종목코드. 빈값=5 baseline")
    ap.add_argument("--ref", type=str, default="data/dart/panelXbrlRef.parquet", help="ref parquet")
    ap.add_argument("--out", type=str, default="data/dart/panel", help="출력 base dir")
    ap.add_argument("--all", action="store_true", help="전종목 빌드 (multiprocessing)")
    args = ap.parse_args()

    refDf: pl.DataFrame | None = None
    refPath = Path(args.ref)
    if refPath.exists():
        refDf = pl.read_parquet(str(refPath))
        _log.info("ref table load: %s (%d entry)", refPath, refDf.height)

    if args.all:
        buildPanelAll(refPath=args.ref, outBaseDir=args.out)
        return

    codes = [c.strip() for c in args.codes.split(",") if c.strip()] or None
    out = buildPanelBaseline(codes=codes, refDf=refDf, verbose=True)
    total = sum(sum(p.values()) for p in out.values())
    _log.info("=== 완료 %d 종목, %d panel rows ===", len(out), total)


if __name__ == "__main__":
    _main()
