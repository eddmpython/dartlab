"""KR scan 서술 지표 횡단 프리빌드 (panel narrativeMetric 위임, 수주잔고·가동률).

panel 의 서술 표에서 뽑은 정량 지표(수주잔고·가동률)를 전종목 순회로 굽는다. 파싱은
``providers.dart.panel.narrativeMetric.readMetrics`` 가 SSOT (본 모듈은 순회 + 스택만, 재구현 0).
confidence 컬럼을 함께 저장해 소비자가 신뢰도 필터(high/mid) 가능. 추출 실패는 정직 gap(행 없음).

Capabilities:
    - 전 상장사 panel 을 회사당 1회 로드해 등록 지표 전부를 뽑아 ``scan/narrativeMetrics.parquet``
      (종목당 1행, 값 + confidence) 로 굽는다. 수주잔고(백로그)·가동률 스크리닝의 원자 소스.

Args:
    Public entry points accept logging options.

Returns:
    Generated ``narrativeMetrics.parquet`` path or None.

Example:
    >>> from dartlab.scan.builders.kr.narrativeMetrics import buildNarrativeMetrics
    >>> buildNarrativeMetrics(verbose=True)  # doctest: +SKIP

Guide:
    파싱 로직은 ``panel.narrativeMetric`` 이 SSOT. 본 모듈은 전종목 순회 + 행 스택 + parquet 저장만.

SeeAlso:
    ``providers.dart.panel.narrativeMetric.readMetrics`` (추출 SSOT) · ``scan.narrativeMetric`` (런타임 reader).

Requires:
    panel artifact (``data/dart/panel/{code}.parquet``). 네트워크 미사용 (offline 안전).

LLM Specifications:
    AntiPatterns: read-time 전종목 panel 파싱 금지 (Rust 힙 OOM). 표 파싱 재구현 금지 (narrativeMetric 위임).
    OutputSchema: ``narrativeMetrics.parquet`` (stockCode + {metricId} + {metricId}_conf).
    Prerequisites: 로컬 ``data/dart/panel/{code}.parquet`` (Data Sync/HF full seed).
    Freshness: 주간 full 프리빌드 사이클 (annual 서술 지표).
    Dataflow: panel -> readMetrics(회사당 1회 로드) -> 종목별 행 스택 -> parquet.
    TargetMarkets: KR DART 정기보고서 서술 표.
"""

from __future__ import annotations

import time
from pathlib import Path

import polars as pl

from dartlab.providers.dart.panel.narrativeMetric import metricCatalog, readMetrics
from dartlab.scan.builders.kr.common import panelDir as _panelDir
from dartlab.scan.builders.kr.common import releaseNativeMemory as _releaseNativeMemory
from dartlab.scan.builders.kr.common import say as _say
from dartlab.scan.builders.kr.common import scanDir as _scanDir


def buildNarrativeMetrics(*, verbose: bool = True) -> Path | None:
    """전종목 panel 서술 표 -> ``scan/narrativeMetrics.parquet`` 횡단 프리빌드.

    ``metricCatalog()`` 의 모든 지표를 회사당 1회 panel 로드(``readMetrics``)로 뽑아 종목당 1행으로
    스택한다. 값 컬럼(metricId, 원/%) + confidence 컬럼(metricId_conf, high/mid/low)을 함께 저장.
    데이터 없는 종목은 행이 생기지 않는다 (정직 gap).

    Parameters
    ----------
    verbose : bool
        진행 로그 출력 여부.

    Returns
    -------
    Path | None
        생성된 parquet 경로. 데이터가 하나도 없으면 None.

    Raises
    ------
    polars.PolarsError
        parquet write 실패 시.

    Examples
    --------
    >>> from dartlab.scan.builders.kr.narrativeMetrics import buildNarrativeMetrics
    >>> buildNarrativeMetrics(verbose=True)  # doctest: +SKIP

    Capabilities:
        - 전 상장사 서술 지표(수주잔고·가동률)를 종목당 1행 wide 로 횡단 프리빌드. confidence 동봉.

    AIContext:
        ``scan("narrativeMetric")`` 축의 1차 source. buildScan full 모드 단계로 실행된다.

    Guide:
        - 출력 경로: ``data/dart/scan/narrativeMetrics.parquet``.
        - 파싱은 ``panel.narrativeMetric.readMetrics`` 위임. 본 함수는 순회/스택/저장만.

    When:
        주간 full 프리빌드 (PREBUILD_FULL). 증분 사이클은 대상 아님.

    How:
        panel glob -> 회사별 ``readMetrics(code)`` -> 종목별 행 dict -> pl.DataFrame -> parquet.

    Requires:
        - 로컬 ``data/dart/panel/{code}.parquet`` (full seed) + ``panel.narrativeMetric``.

    SeeAlso:
        - :func:`dartlab.providers.dart.panel.narrativeMetric.readMetrics` (추출 SSOT)
        - :func:`dartlab.scan.narrativeMetric.scanNarrativeMetric` (런타임 reader)
    """
    panelRoot = _panelDir()
    if not panelRoot.exists():
        if verbose:
            _say("panel 디렉토리 없음. narrativeMetric 빌드 건너뜀")
        return None
    codes = sorted(p.stem for p in panelRoot.glob("*.parquet"))
    if not codes:
        if verbose:
            _say("panel parquet 없음. narrativeMetric 빌드 건너뜀")
        return None

    metricIds = [m["metricId"] for m in metricCatalog()]
    if verbose:
        _say(f"[narrativeMetric] {len(codes)}종목 x {len(metricIds)}지표 횡단 (panel readMetrics 위임)")

    t0 = time.perf_counter()
    rows: list[dict] = []
    for i, code in enumerate(codes):
        try:
            mm = readMetrics(code, metricIds)
        except (pl.exceptions.PolarsError, OSError, ValueError):
            mm = {}
        if mm:
            row: dict = {"stockCode": code}
            for mid, res in mm.items():
                row[mid] = float(res["value"])
                row[f"{mid}_conf"] = res["confidence"]
            rows.append(row)
        if (i + 1) % 200 == 0:
            _releaseNativeMemory()
        if verbose and (i + 1) % 500 == 0:
            _say(f"  [{i + 1}/{len(codes)}] {len(rows)}종목 데이터 {time.perf_counter() - t0:.0f}s")

    if not rows:
        if verbose:
            _say("[narrativeMetric] 추출 데이터 0. parquet 미생성")
        return None

    df = pl.DataFrame(rows, infer_schema_length=None)
    outDir = _scanDir()
    outDir.mkdir(parents=True, exist_ok=True)
    out = outDir / "narrativeMetrics.parquet"
    df.write_parquet(str(out), compression="zstd")
    if verbose:
        _say(f"[narrativeMetric] {df.height}종목 -> {out.name} ({time.perf_counter() - t0:.0f}s)")
    return out


def buildNarrativeMetricsSafe(*, verbose: bool = True) -> Path | None:
    """``buildNarrativeMetrics`` 예외 흡수 wrapper.

    빌드 실패(파싱·IO)가 buildScan 전체를 깨지 않게 흡수한다 (축 무회귀). 실패는 None 반환.

    Parameters
    ----------
    verbose : bool
        진행 로그 출력 여부.

    Returns
    -------
    Path | None
        생성 parquet 경로 또는 None (데이터 부재/실패).
    """
    try:
        return buildNarrativeMetrics(verbose=verbose)
    except (pl.exceptions.PolarsError, OSError, ValueError) as e:  # noqa: BLE001 흡수 의도
        if verbose:
            _say(f"[narrativeMetric] 빌드 실패 흡수: {e}")
        return None
