"""사업부문 매출구성 스캔. 전 상장사 부문 비중·집중도(HHI)·다각화 등급.

Capabilities:
    - prebuild ``salesByProduct.parquet`` (종목당 1 행) 을 읽어 사업부문 매출구성 횡단면을
      반환한다. 사업보고서 "매출 및 수주상황" 표에서 뽑은 단위-불변 지표.

Args:
    Public entry point accepts logging options only.

Returns:
    종목당 1 행 부문 mix DataFrame.

Example:
    >>> import dartlab
    >>> dartlab.scan("salesByProduct").sort("hhi").head()

Guide:
    절대 매출 랭킹은 finance scan 을 쓴다. 본 축은 "가장 다각화된/집중된" mix 랭킹용.
    회사별 원표는 터미널 businessTables (런타임 직독) 가 렌더한다.

SeeAlso:
    ``scan.builders.kr.salesByProduct`` (prebuild source) · ``scan.orders`` (동료 공시파생 축).

Requires:
    prebuild ``data/dart/scan/salesByProduct.parquet`` (HF 자동 다운로드).

AIContext:
    Agent 가 ``scan("salesByProduct")`` 호출 시 dispatch. "사업 다각화 높은 회사",
    "특정 부문 집중 종목" 스크리닝 source. read-time panel 파싱은 OOM 이라 하지 않는다.

LLM Specifications:
    AntiPatterns: read-time panel 파싱 금지 (prebuild consolidation SSOT). 절대매출 비교 금지.
    OutputSchema: stockCode·period·nSegments·topSegment·topSharePct·hhi·grade·segments.
    Prerequisites: prebuild salesByProduct.parquet 존재 (첫 베이크 전이면 빈 프레임).
    Freshness: scan prebuild 사이클 산출물.
    Dataflow: HF salesByProduct.parquet -> lazy read -> 종목 필터.
    TargetMarkets: KR DART 정기보고서.
"""

from __future__ import annotations

import polars as pl

from dartlab.scan.io.parquet import _downloadScanFile, _ensureScanData

_FILE = "salesByProduct.parquet"
_SBP_READ_SCHEMA = {
    "stockCode": pl.Utf8,
    "period": pl.Utf8,
    "nSegments": pl.Int32,
    "topSegment": pl.Utf8,
    "topSharePct": pl.Float64,
    "hhi": pl.Float64,
    "grade": pl.Utf8,
    "topSegmentTrend": pl.Float64,
    "segments": pl.Utf8,
    "source": pl.Utf8,
}


def _emptyFrame() -> pl.DataFrame:
    return pl.DataFrame(schema=_SBP_READ_SCHEMA)


def scanSalesByProduct(*, verbose: bool = True) -> pl.DataFrame:
    """전 상장사 사업부문 매출구성 스캔 (부문 비중·HHI·다각화 등급).

    Parameters
    ----------
    verbose : bool, default True
        진행 라인 출력 여부 (현재 read-only 라 미사용, 시그니처 일관성 유지).

    Returns
    -------
    pl.DataFrame
        컬럼 (종목당 1 행):

        - stockCode (str): 종목코드
        - period (str): 사용한 사업보고서 기간 (예: 2023Q4)
        - nSegments (int): 양수 매출 사업부문 수
        - topSegment (str): 최대 매출 부문명
        - topSharePct (float): 최대 부문 비중 (%)
        - hhi (float): 부문 비중 Herfindahl 지수 (0~1, 높을수록 집중)
        - grade (str): 다각화 등급 (단일사업/집중/주력집중/균형/분산)
        - topSegmentTrend (float | None): 최대 부문 비중 전기 대비 변화 (pp)
        - segments (str): 상위 5 부문 "부문:비중%" 요약
        - source (str): 데이터 출처 (panel:salesOrder)

    Raises
    ------
    polars.PolarsError
        salesByProduct.parquet 손상 시.

    Examples
    --------
    >>> import dartlab
    >>> df = dartlab.scan("salesByProduct")
    >>> df.filter(pl.col("grade") == "분산").sort("nSegments", descending=True).head()  # doctest: +SKIP

    Capabilities:
        - prebuild 통합본을 read 로 반환 (종목당 1 행). read-time panel 파싱 없음.
        - 첫 베이크 전이거나 파일 부재 시 빈 DataFrame (축 무회귀, "데이터 없음" 표시).

    AIContext:
        "사업 다각화" 스크리닝·1 사 부문 mix 등급 source. panel 매출및수주 표에서 굽는다.

    Guide:
        - 절대 매출 랭킹은 finance scan. 본 축은 mix/집중도 (단위-불변).
        - grade 는 nSegments·HHI 조합. 부문 계·합계 행은 빌드 시 이미 배제.

    When:
        cross-company 다각화 스크리닝 시. 대시보드 부문 mix 카드 빌드 시.

    How:
        ``_ensureScanData`` 로 표준 필수본 확인 후 salesByProduct.parquet best-effort 단일
        다운로드. 있으면 read, 없으면 빈 프레임.

    Requires:
        prebuild ``data/dart/scan/salesByProduct.parquet`` (``buildSalesByProductScan`` 산출).

    SeeAlso:
        - :func:`dartlab.scan.builders.kr.salesByProduct.buildSalesByProductScan` (source 빌드)
        - :func:`dartlab.scan.orders.scanOrders` (동료 공시파생 KR 축)
    """
    scanDir = _ensureScanData()
    path = scanDir / _FILE
    if not path.exists():
        # salesByProduct 는 _REQUIRED 아님 (첫 베이크 전 404 로 타 축 깨짐 방지). 단일 best-effort.
        try:
            _downloadScanFile(scanDir, _FILE)
        except (OSError, RuntimeError, ValueError):
            return _emptyFrame()
    if not path.exists():
        return _emptyFrame()

    return pl.read_parquet(str(path))


__all__ = ["scanSalesByProduct"]
