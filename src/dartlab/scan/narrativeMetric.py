"""서술 지표(수주잔고·가동률) 횡단 스캔. prebuild narrativeMetrics.parquet 직독.

Capabilities:
    - prebuild ``narrativeMetrics.parquet`` (종목당 1 행) 을 읽어 사업보고서 서술 표에서 뽑은 정량
      지표(수주잔고·가동률)를 confidence 와 함께 반환한다. read-time panel 파싱 없음.

Args:
    Public entry point accepts logging option only.

Returns:
    종목당 1 행 서술 지표 DataFrame.

Example:
    >>> import dartlab
    >>> dartlab.scan("narrativeMetric").filter(pl.col("backlog_conf") == "high").head()  # doctest: +SKIP

Guide:
    수주잔고는 flow(단일 수주공시, scan("orders"))가 아니라 stock(백로그). 백로그커버 = 수주잔고/매출.
    confidence high/mid 만 신뢰 스크리닝에 쓰고 low 는 참고. 값 부재 = 정직 gap(행 없음/None).

SeeAlso:
    ``scan.builders.kr.narrativeMetrics`` (prebuild source) · ``providers.dart.panel.narrativeMetric`` (추출 SSOT).

Requires:
    prebuild ``data/dart/scan/narrativeMetrics.parquet`` (HF best-effort 다운로드).

LLM Specifications:
    AntiPatterns: read-time panel 파싱 금지 (prebuild consolidation SSOT). low confidence 를 확정값 단정 금지.
    OutputSchema: stockCode + backlog(원) + backlog_conf + utilizationRate(%) + utilizationRate_conf.
    Prerequisites: prebuild parquet 존재 (첫 베이크 전이면 빈 프레임).
    Freshness: scan prebuild 사이클 산출물.
    Dataflow: HF narrativeMetrics.parquet -> lazy read -> 종목 필터.
    TargetMarkets: KR DART 정기보고서 서술 표.
"""

from __future__ import annotations

import polars as pl

from dartlab.scan.io.parquet import _downloadScanFile, _ensureScanData, _maybeRefreshScanFile

_FILE = "narrativeMetrics.parquet"
_READ_SCHEMA = {
    "stockCode": pl.Utf8,
    "backlog": pl.Float64,
    "backlog_conf": pl.Utf8,
    "utilizationRate": pl.Float64,
    "utilizationRate_conf": pl.Utf8,
}


def _emptyFrame() -> pl.DataFrame:
    return pl.DataFrame(schema=_READ_SCHEMA)


def scanNarrativeMetric(*, verbose: bool = True) -> pl.DataFrame:
    """전 상장사 사업보고서 서술 지표 스캔 (수주잔고·가동률 + confidence).

    Parameters
    ----------
    verbose : bool, default True
        진행 라인 출력 여부 (read-only 라 현재 미사용, 시그니처 일관성).

    Returns
    -------
    pl.DataFrame
        컬럼 (종목당 1 행, 지표 부재 종목은 해당 값 null):

        - stockCode (str): 종목코드
        - backlog (float | None): 수주잔고 (원)
        - backlog_conf (str | None): 수주잔고 신뢰도 (high/mid/low)
        - utilizationRate (float | None): 가동률 (%)
        - utilizationRate_conf (str | None): 가동률 신뢰도

    Raises
    ------
    polars.PolarsError
        narrativeMetrics.parquet 손상 시.

    Examples
    --------
    >>> import dartlab
    >>> df = dartlab.scan("narrativeMetric")
    >>> df.filter(pl.col("backlog_conf") == "high").sort("backlog", descending=True).head()  # doctest: +SKIP

    Capabilities:
        - prebuild 통합본을 read 로 반환 (종목당 1 행). read-time panel 파싱 없음.
        - 첫 베이크 전이거나 파일 부재 시 빈 DataFrame (축 무회귀).

    AIContext:
        "수주잔고 큰 회사"·"가동률 높은 제조사" 스크리닝 source. 백로그커버(수주잔고/매출)로 성장 가시성.

    Guide:
        - 신뢰 스크리닝은 confidence high/mid. 절대 수주 flow 는 scan("orders").
        - 값 부재는 서식 부재/저신뢰 정직 gap. 억지 추정 안 함.

    When:
        수주 가시성·가동률 cross-company 스크리닝 시.

    How:
        ``_ensureScanData`` 후 narrativeMetrics.parquet best-effort 단일 다운로드. 있으면 read, 없으면 빈 프레임.

    Requires:
        prebuild ``data/dart/scan/narrativeMetrics.parquet`` (``buildNarrativeMetrics`` 산출).

    SeeAlso:
        - :func:`dartlab.scan.builders.kr.narrativeMetrics.buildNarrativeMetrics` (source 빌드)
        - :func:`dartlab.providers.dart.panel.narrativeMetric.readMetric` (추출 SSOT)
    """
    scanDir = _ensureScanData()
    path = scanDir / _FILE
    if not path.exists():
        try:
            _downloadScanFile(scanDir, _FILE)
        except (ExceptionGroup, OSError, RuntimeError, ValueError):
            return _emptyFrame()
    else:
        # HF 는 매일 갱신되므로 TTL 게이트 후 ETag 재검증 (실패 시 로컬 유지).
        _maybeRefreshScanFile(scanDir, _FILE)
    if not path.exists():
        return _emptyFrame()
    return pl.read_parquet(str(path))


__all__ = ["scanNarrativeMetric"]
