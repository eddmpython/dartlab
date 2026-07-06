"""KR scan 주석(note) 횡단 프리빌드 (추출 카탈로그 구동, panel note 표 SSOT).

Capabilities:
    - 추출 카탈로그(``core.extractionCatalog``)의 registered 단일축 note 개념마다 전 상장사 panel 을
      순회해 ``readNoteStatements`` 로 항목x기간 표를 뽑고, long 스택으로 ``scan/note/{bareName}.parquet``
      횡단면을 굽는다. 재고자산 하위분류, 리스 부채/자산, 법인세 구성, 판관비 항목 등 노트 lineitem 을
      전종목 스크리닝 가능하게 만드는 원자 소스.

Args:
    Public entry points accept logging options.

Returns:
    Generated ``note/{bareName}.parquet`` paths.

Example:
    >>> from dartlab.scan.builders.kr.notes import buildNotes
    >>> paths = buildNotes(verbose=True)

Guide:
    노트 추출 로직은 ``providers.dart.panel.cell.readNoteStatements`` 가 SSOT 다. 본 모듈은 전종목
    순회 + long 스택 + 개념별 병합만 담당하고 파싱을 재구현하지 않는다(위임). 단일축이 아닌 다축
    matrix 주석(세그먼트 등)은 ``readNoteStatements`` 가 자동 제외하므로 파일이 생성되지 않는다.

SeeAlso:
    ``scan.builders.kr.report.build`` (동일 개념별 배치 패턴) · ``scan.note`` (런타임 reader)
    · ``providers.dart.panel.cell.readNoteStatements`` (추출 SSOT).

Requires:
    panel artifact (``data/dart/panel/{code}.parquet``). 네트워크 미사용 (offline 안전).

AIContext:
    ``scan("note", "재고자산")`` 축의 prebuild source. 회사별 panel 정렬/파싱은 콜드 read + OOM 비용이
    커 런타임 횡단이 불가하므로 prebuild consolidation 으로 개념당 1 파일을 굽는다.

LLM Specifications:
    AntiPatterns: read-time 전종목 panel 파싱 금지 (Rust 힙 OOM). 노트 파싱 재구현 금지 (cell 위임).
    OutputSchema: ``note/{bareName}.parquet`` (long: stockCode/account/label/period/value).
    Prerequisites: 로컬 ``data/dart/panel/{code}.parquet`` (Data Sync/HF full seed).
    Freshness: 주간 full 프리빌드 사이클 (annual 노트, 증분 미대상).
    Dataflow: panel -> readNoteStatements(회사당 1회 정렬) -> long 스택 -> 개념별 merge -> parquet.
    TargetMarkets: KR DART 정기보고서 주석.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path

import polars as pl

from dartlab.core.extractionCatalog import DartSource, getExtractionConcepts
from dartlab.scan.builders.kr.common import BATCH_SIZE as _BATCH
from dartlab.scan.builders.kr.common import mergeBatchFiles as _mergeBatchFiles
from dartlab.scan.builders.kr.common import panelDir as _panelDir
from dartlab.scan.builders.kr.common import releaseNativeMemory as _releaseNativeMemory
from dartlab.scan.builders.kr.common import say as _say
from dartlab.scan.builders.kr.common import scanDir as _scanDir

# note 횡단 long 스키마 (개념별 parquet 공통). value 는 raw valueRaw (숫자화는 소비자 scanNote).
_NOTE_LONG_COLUMNS = ("stockCode", "account", "label", "period", "value")
_NOTE_LONG_SCHEMA = {
    "stockCode": pl.Utf8,
    "account": pl.Utf8,
    "label": pl.Utf8,
    "period": pl.Utf8,
    "value": pl.Utf8,
}


def _noteConceptSpecs() -> list[tuple[str, str, str]]:
    """카탈로그에서 횡단 프리빌드 대상 note 개념을 도출한다: (bareName, ntKey, label).

    registered=True + valueType in (amount, rate) 인 note 개념만 (순수 text 주석 제외). bareName 은
    conceptId 에서 ``note.`` prefix 를 뗀 것(파일명 + scan target 키). 카탈로그가 SSOT 라 손 선별 0.

    Returns:
        ``[(bareName, ntKey, label), ...]`` (conceptId 정의 순서 보존).

    Raises:
        없음.

    Example:
        >>> ("inventory", "NT_D826380", "재고자산") in _noteConceptSpecs()
        True
    """
    specs: list[tuple[str, str, str]] = []
    for c in getExtractionConcepts(category="note"):
        if not c.registered or c.valueType not in ("amount", "rate"):
            continue
        if not isinstance(c.dart, DartSource):
            continue
        bare = c.conceptId.removeprefix("note.")
        specs.append((bare, c.dart.key, c.label))
    return specs


# 횡단 프리빌드 대상 note 개념 SSOT. 카탈로그 registered 단일축 note 에서 도출 (contract 로 정합 강제).
SCAN_NOTE_CONCEPTS: list[tuple[str, str, str]] = _noteConceptSpecs()


def _wideToLong(wide: pl.DataFrame, code: str) -> pl.DataFrame | None:
    """readNoteStatements wide(account/label/기간열) -> long(stockCode/account/label/period/value).

    기간열(account/label 이 아닌 컬럼)을 unpivot 해 null/빈 값 행을 떨군다. value 는 raw 문자열 유지.

    Args:
        wide: ``readNoteStatements`` 가 반환한 항목x기간 wide (컬럼 account, label, 기간들).
        code: 종목코드 (long 태깅).

    Returns:
        _NOTE_LONG_SCHEMA long DataFrame 또는 None (기간열/값 없음).

    Raises:
        없음.
    """
    periodCols = [c for c in wide.columns if c not in ("account", "label")]
    if not periodCols:
        return None
    long = wide.unpivot(
        index=["account", "label"], on=periodCols, variable_name="period", value_name="value"
    ).with_columns(pl.col("value").cast(pl.Utf8))
    long = long.filter(pl.col("value").is_not_null() & (pl.col("value").str.strip_chars() != ""))
    if long.is_empty():
        return None
    return long.with_columns(pl.lit(code).alias("stockCode")).select(list(_NOTE_LONG_COLUMNS))


def buildNotes(*, verbose: bool = True) -> list[Path]:
    """전종목 panel 주석 -> 개념별 ``scan/note/{bareName}.parquet`` 횡단 프리빌드.

    :data:`SCAN_NOTE_CONCEPTS` 각 개념마다 전 상장사 panel 을 순회하며 ``readNoteStatements`` (회사당 1회
    정렬 위임) 로 항목x기간 표를 뽑아 long 으로 스택하고, ``report.build.buildReport`` 와 동일한 개념별
    배치 청크 -> 병합 패턴으로 파일당 하나로 합친다. 데이터가 하나도 없는 개념(다축 matrix 주석 등)은
    파일이 생성되지 않는다 (정직 gap).

    Parameters
    ----------
    verbose : bool
        진행 로그 출력 여부.

    Returns
    -------
    list[Path]
        생성된 개념별 parquet 경로 목록. 데이터 없는 개념은 제외.

    Raises
    ------
    polars.PolarsError
        parquet write/merge 실패 시.

    Examples
    --------
    >>> from dartlab.scan.builders.kr.notes import buildNotes
    >>> paths = buildNotes(verbose=True)  # doctest: +SKIP

    Capabilities:
        - 카탈로그 registered 단일축 note 를 전종목 횡단 long 으로 굽는 단일 진입점. 회사당 1회 정렬로
          registered 노트 전부를 뽑아 개념별 bucket 에 push, _BATCH(200) 도달 시 청크 flush.

    AIContext:
        ``scan("note", 이름)`` 축의 1차 source. buildScan full 모드 단계로 실행된다.

    Guide:
        - 출력 경로: ``data/dart/scan/note/{bareName}.parquet`` (bareName = conceptId 에서 note. 제거).
        - 파싱은 ``providers.dart.panel.cell.readNoteStatements`` 위임. 본 함수는 순회/스택/병합만.

    When:
        주간 full 프리빌드 (PREBUILD_FULL). 증분 사이클은 대상 아님 (annual 노트 + 시드 데이터손실 회피).

    How:
        panel glob -> 회사별 ``readNoteStatements(code, ntKeys)`` -> 개념별 ``_wideToLong`` -> batch flush
        -> 개념별 ``_mergeBatchFiles`` (diagonal_relaxed).

    Requires:
        - 로컬 ``data/dart/panel/{code}.parquet`` (full seed) + ``core.extractionCatalog``.

    SeeAlso:
        - :data:`SCAN_NOTE_CONCEPTS` · :func:`dartlab.providers.dart.panel.cell.readNoteStatements`
        - :func:`dartlab.scan.builders.kr.report.build.buildReport` (동일 배치 패턴)
    """
    panelRoot = _panelDir()
    if not panelRoot.exists():
        if verbose:
            _say("panel 디렉토리 없음 - note 빌드 건너뜀")
        return []
    codes = sorted(p.stem for p in panelRoot.glob("*.parquet"))
    if not codes:
        if verbose:
            _say("panel parquet 없음 - note 빌드 건너뜀")
        return []

    specs = SCAN_NOTE_CONCEPTS
    ntToBare = {ntKey: bare for bare, ntKey, _ in specs}
    ntKeys = [ntKey for _, ntKey, _ in specs]
    outDir = _scanDir() / "note"
    outDir.mkdir(parents=True, exist_ok=True)

    if verbose:
        _say(f"[note] {len(codes)}종목 -> {len(specs)}개 note 개념 횡단 (panel readNoteStatements 위임)")

    batchDirs: dict[str, Path] = {}
    batchIdx: dict[str, int] = {}
    chunks: dict[str, list[pl.DataFrame]] = {}
    rowCounts: dict[str, int] = {}
    for bare, _, _ in specs:
        bd = outDir / f"_tmp_{bare}"
        bd.mkdir(parents=True, exist_ok=True)
        batchDirs[bare] = bd
        batchIdx[bare] = 0
        chunks[bare] = []
        rowCounts[bare] = 0

    def _flush(bare: str) -> None:
        if not chunks[bare]:
            return
        batch = pl.concat(chunks[bare], how="diagonal_relaxed")
        idx = batchIdx[bare]
        batch.write_parquet(str(batchDirs[bare] / f"batch_{idx:03d}.parquet"), compression="zstd")
        del batch
        chunks[bare] = []
        batchIdx[bare] = idx + 1

    t0 = time.perf_counter()
    processed = 0
    for i, code in enumerate(codes):
        try:
            from dartlab.providers.dart.panel.cell import readNoteStatements

            noteMap = readNoteStatements(code, ntKeys, freq="year")
        except (pl.exceptions.PolarsError, OSError, ValueError):
            noteMap = {}
        if noteMap:
            processed += 1
        for ntKey, wide in noteMap.items():
            bare = ntToBare.get(ntKey)
            if bare is None:
                continue
            long = _wideToLong(wide, code)
            if long is None:
                continue
            chunks[bare].append(long)
            rowCounts[bare] += long.height
            if len(chunks[bare]) >= _BATCH:
                _flush(bare)

        if (i + 1) % 200 == 0:
            _releaseNativeMemory()
        if verbose and (i + 1) % 500 == 0:
            _say(f"  [{i + 1}/{len(codes)}] {processed}종목 데이터 {time.perf_counter() - t0:.0f}s")

    outputs: list[Path] = []
    for bare, _, _ in specs:
        _flush(bare)
        if batchIdx[bare] == 0:
            shutil.rmtree(batchDirs[bare], ignore_errors=True)
            continue
        outPath = outDir / f"{bare}.parquet"
        _mergeBatchFiles(batchDirs[bare], outPath, how="diagonal_relaxed")
        shutil.rmtree(batchDirs[bare], ignore_errors=True)
        _releaseNativeMemory()
        outputs.append(outPath)
        if verbose:
            diskMb = outPath.stat().st_size / 1024 / 1024
            _say(f"  {bare}: {rowCounts[bare]:,}행, {diskMb:.1f}MB")

    if verbose:
        _say(f"  note 완료: {len(outputs)}개 개념, {time.perf_counter() - t0:.0f}초")
    return outputs


def buildNotesSafe(*, verbose: bool = True) -> list[Path]:
    """note 횡단 풀 빌드 (실패해도 전체 scan 진행).

    Parameters
    ----------
    verbose : bool
        진행 로그 출력 여부.

    Returns
    -------
    list[Path]
        생성된 note parquet 경로 목록. 실패 시 빈 목록.

    Raises
    ------
    없음 (선택 산출물이라 알려진 실패를 흡수).

    Examples
    --------
    >>> buildNotesSafe(verbose=False)  # doctest: +SKIP

    Capabilities:
        note 산출물을 optional step 으로 만들어, 실패해도 finance/report 등 핵심 scan 산출물 빌드를 막지
        않는다. ``buildScan`` 이 full 모드에서 호출한다.

    AIContext:
        ``buildScan`` 이 salesByProduct 다음 단계로 (full 모드) 호출. ``scan("note", 이름)`` 축의 source.

    Guide:
        보호 wrapper 다. 실제 계산은 :func:`buildNotes` 가 담당한다.

    When:
        주간 full 프리빌드 사이클, salesByProduct 빌드 직후.

    How:
        :func:`buildNotes` 실행 후 알려진 런타임/파일 오류를 빈 목록으로 변환한다.

    Requires:
        panel artifact (full seed) + ``core.extractionCatalog``.

    SeeAlso:
        :func:`dartlab.scan.builders.kr.core.buildScan`.
    """
    try:
        if verbose:
            _say("[note] 주석 횡단 full 빌드 시작 (panel readNoteStatements SSOT)")
        return buildNotes(verbose=verbose)
    except (FileNotFoundError, RuntimeError, OSError, ValueError, pl.exceptions.PolarsError) as exc:
        if verbose:
            _say(f"[note] 실패: {exc}")
        return []


__all__ = [
    "SCAN_NOTE_CONCEPTS",
    "buildNotes",
    "buildNotesSafe",
]
