"""panel 전종목 batch 빌드. builder의 격리 프로세스 단일 빌드를 bounded fan-out한다.

각 회사 build가 공시 변환 자식 프로세스를 직접 관리하므로 본 batch는 최대 2개 회사만 thread로
오케스트레이션한다. 단일 빌드는 ``builder``, 기준선은 ``baseline``에 있고 본 모듈은
bounded fan-out과 CLI만 소유한다.

LLM Specifications:
    AntiPatterns:
        - 회사 전체 future 선제 제출 금지. 실행 worker 수만큼만 pending.
        - 변환을 batch thread 안에서 재구현 금지. builder.buildPanel 위임.
        - 단일 빌드 로직 중복 금지 — builder.buildPanel 위임.
    OutputSchema:
        - ``buildPanelAll(*, refPath, outBaseDir, codes, numWorkers) -> dict[code, (periodCount, totalRow)]``.
    Prerequisites:
        - 전종목 zip + ref parquet.
    Freshness:
        - 분기 incremental — changed code 만.
    Dataflow:
        - codes → bounded threads → _buildOne(builder.buildPanel) → 공시 격리 process → 집계.
    TargetMarkets:
        - KR (DART).
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path

import polars as pl

import dartlab.config as _cfg

from .baseline import buildPanelBaseline
from .builder import buildPanel, panelXbrlRefPath

_log = logging.getLogger(__name__)


def _buildOneWithRef(
    args: tuple[str, str, str],
    refDf: pl.DataFrame,
) -> tuple[str, int, int, float]:
    """단일 회사 builder에 위임하고 통계만 붙인다."""

    code, _refPath, outBaseDir = args
    t0 = time.perf_counter()
    result = buildPanel(code, refDf=refDf, outBaseDir=Path(outBaseDir), overwrite=True, verbose=False)
    return (code, len(result), sum(result.values()), time.perf_counter() - t0)


def _buildOne(args: tuple[str, str, str]) -> tuple[str, int, int, float]:
    """독립 호출용 단일 회사 entry. ref를 읽고 builder 실패를 그대로 전파한다.

    Args:
        args: ``(code, refPath, outBaseDir)``.

    Returns:
        ``(code, periodCount, totalRow, elapsedSeconds)``.

    Raises:
        FileNotFoundError: ref 또는 회사 source가 없을 때.
        PanelBuildError: 회사 변환 또는 publish 실패.

    Example:
        >>> _buildOne(("005930", "ref.parquet", "data/dart/panel"))  # doctest: +SKIP
    """

    _code, refPath, _outBaseDir = args
    return _buildOneWithRef(args, pl.read_parquet(refPath))


def buildPanelAll(
    *,
    refPath: str | Path | None = None,  # None = 패키지 동봉 panelXbrlRefPath() (data/ 아님)
    outBaseDir: str | Path = "data/dart/panel",
    codes: list[str] | None = None,
    numWorkers: int = 2,
    skipExisting: bool = True,  # resumable — 이미 빌드된 {code}.parquet 건너뜀 (크래시 후 재실행 이어감)
    progressEvery: int = 50,
    verbose: bool = True,
) -> dict[str, tuple[int, int]]:
    """전종목 panel 빌드. 최대 2개 회사의 격리 빌드를 병렬 오케스트레이션한다.

    Args:
        refPath: panelXbrlRef ref parquet.
        outBaseDir: 출력 base dir.
        codes: 종목 list. None = ``data/original/dart/docs/`` 의 모든 종목.
        numWorkers: 동시 회사 수. 기본 2, 최대 2.
        progressEvery: 진행 로그 빈도.
        verbose: 진행 로그.

    Returns:
        ``{code: (periodCount, totalRow)}`` dict.

    Raises:
        FileNotFoundError: ref 또는 회사 source가 없을 때.
        PanelBuildError: 종목별 변환 또는 발행 실패.

    Example:
        >>> buildPanelAll(codes=["005930", "005380"])  # doctest: +SKIP

    SeeAlso:
        - ``builder.buildPanel`` — 단일 종목 빌드 (worker 가 위임).
        - ``baseline.buildPanelBaseline`` — 5 baseline 검증.

    Requires:
        - data/original/dart/docs/{code}/*.zip 전종목.

    Capabilities:
        - 전종목 panel artifact를 allocator 누적 없이 재개 가능한 형태로 생산.

    Guide:
        - CI sync 잡 또는 운영자. 최대 2개 회사만 동시 실행.

    AIContext:
        - thread는 회사 오케스트레이션만 하고 변환은 builder의 제한 수명 process가 담당.

    When:
        - 전종목(또는 changed codes) 을 일괄 빌드할 때 (CI sync / 운영자).

    How:
        - bounded thread window로 builder.buildPanel 실행 → 통계 집계.

    LLM Specifications:
        AntiPatterns:
            - 전종목 future를 한꺼번에 제출하지 않는다.
            - 2개를 넘는 회사 동시 변환 금지.
        OutputSchema:
            - ``dict[str, tuple[int, int]]``.
        Prerequisites:
            - 전종목 zip + ref parquet.
        Freshness:
            - 분기 incremental — changed code 만.
        Dataflow:
            - codes → bounded threads → _buildOne → 격리 process → 집계.
        TargetMarkets:
            - KR (DART).
    """
    if codes is None:
        baseDir = Path(_cfg.dataDir) / "original" / "dart" / "docs"
        codes = sorted([d.name for d in baseDir.iterdir() if d.is_dir()])

    refPathStr = str(refPath if refPath is not None else panelXbrlRefPath())  # 패키지 동봉 ref (data/ 아님)
    outBaseStr = str(outBaseDir)
    Path(outBaseStr).mkdir(parents=True, exist_ok=True)
    if numWorkers < 1 or numWorkers > 2:
        raise ValueError("panel batch numWorkers는 메모리 안전을 위해 1 또는 2여야 합니다")

    if skipExisting:  # resumable — 이미 빌드 산출 있는 종목 제외 (크래시·중단 후 재실행이 이어감)
        total = len(codes)
        codes = [c for c in codes if not (Path(outBaseStr) / f"{c}.parquet").exists()]
        if verbose:
            _log.info("buildPanelAll: skipExisting — %d/%d 잔여 (%d 이미 빌드)", len(codes), total, total - len(codes))

    if verbose:
        _log.info("buildPanelAll: %d 종목, %d workers", len(codes), numWorkers)

    args = [(c, refPathStr, outBaseStr) for c in codes]
    result: dict[str, tuple[int, int]] = {}
    processed = 0
    totalRows = 0
    t0 = time.perf_counter()
    refDf = pl.read_parquet(refPathStr)
    argsIterator = iter(args)
    executor = ThreadPoolExecutor(max_workers=numWorkers, thread_name_prefix="panel-company")
    pending: dict[Future[tuple[str, int, int, float]], tuple[str, str, str]] = {}

    def submitNext() -> bool:
        """다음 회사 하나만 executor에 제출한다.

        Args:
            없음.

        Returns:
            제출했으면 True, 입력이 소진됐으면 False.

        Raises:
            없음.

        Example:
            >>> submitNext()  # doctest: +SKIP
        """

        try:
            nextArgs = next(argsIterator)
        except StopIteration:
            return False
        pending[executor.submit(_buildOneWithRef, nextArgs, refDf)] = nextArgs
        return True

    for _ in range(numWorkers):
        if not submitNext():
            break
    try:
        while pending:
            future = next(as_completed(pending))
            pending.pop(future)
            code, pcount, rowCount, _elapsed = future.result()
            result[code] = (pcount, rowCount)
            processed += 1
            totalRows += rowCount
            if verbose and processed % progressEvery == 0:
                wall = time.perf_counter() - t0
                rate = processed / wall if wall > 0 else 0
                eta = (len(codes) - processed) / rate if rate > 0 else 0
                _log.info(
                    "[%d/%d] %.1f code/s, ETA %.1f min, totalRows=%d",
                    processed,
                    len(codes),
                    rate,
                    eta / 60,
                    totalRows,
                )
            submitNext()
    finally:
        executor.shutdown(wait=True, cancel_futures=True)
    if verbose:
        wall = time.perf_counter() - t0
        _log.info("완료: %d codes, %d totalRows, %.1f min", len(codes), totalRows, wall / 60)
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
    ap.add_argument("--ref", type=str, default=str(panelXbrlRefPath()), help="ref parquet (기본=패키지 동봉)")
    ap.add_argument("--out", type=str, default="data/dart/panel", help="출력 base dir")
    ap.add_argument("--all", action="store_true", help="전종목 빌드")
    ap.add_argument("--spine", action="store_true", help="정부 서식 뼈대(spineData.py) 생성 — 기준 종목 1개")
    ap.add_argument(
        "--noteTaxonomy", action="store_true", help="주석 뼈대(noteTaxonomyData.py) 생성 — 전 corpus XBRL 학습"
    )
    ap.add_argument("--minFreq", type=int, default=3, help="noteTaxonomy 제목 총빈도 하한 (노이즈 컷)")
    ap.add_argument(
        "--dominanceRatio", type=float, default=0.8, help="noteTaxonomy 최빈코드 지배비율 하한 (모호제목 제외)"
    )
    ap.add_argument("--workers", type=int, default=2, choices=(1, 2), help="동시 회사 수 (메모리 가드, 기본 2)")
    ap.add_argument("--rebuild", action="store_true", help="--all 시 이미 빌드된 종목도 재빌드 (기본=resumable skip)")
    args = ap.parse_args()

    refDf: pl.DataFrame | None = None
    refPath = Path(args.ref)
    if refPath.exists():
        refDf = pl.read_parquet(str(refPath))
        _log.info("ref table load: %s (%d entry)", refPath, refDf.height)

    if args.spine:
        from .spineBuilder import buildSpine

        # 기준 종목 1개 (정부 표준 서식이라 한 회사 reference 로 충분). 첫 --codes 또는 기본.
        codes = [c.strip() for c in args.codes.split(",") if c.strip()]
        stats = buildSpine(codes[0] if codes else "005930", refDf=refDf, verbose=True)
        _log.info("=== spine 완료: code=%d, rows=%d ===", stats["code"], stats["rows"])
        return

    if args.noteTaxonomy:
        from .noteTaxonomy import buildAndWrite

        stats = buildAndWrite(verbose=True, minFreq=args.minFreq, dominanceRatio=args.dominanceRatio)
        _log.info(
            "=== noteTaxonomy 완료: entries=%d (minFreq=%d, dominanceRatio=%.2f) ===",
            stats["entries"],
            args.minFreq,
            args.dominanceRatio,
        )
        return

    if args.all:
        buildPanelAll(refPath=args.ref, outBaseDir=args.out, numWorkers=args.workers, skipExisting=not args.rebuild)
        return

    codes = [c.strip() for c in args.codes.split(",") if c.strip()] or None
    out = buildPanelBaseline(codes=codes, refDf=refDf, verbose=True)
    total = sum(sum(p.values()) for p in out.values())
    _log.info("=== 완료 %d 종목, %d panel rows ===", len(out), total)


if __name__ == "__main__":
    _main()
