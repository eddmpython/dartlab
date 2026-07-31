"""배당 추이 스캔 -- DPS 3개년 시계열 + 패턴 분류."""

from __future__ import annotations

import polars as pl

from dartlab.core.logger import getLogger
from dartlab.scan.io.accounts import amountExpr

_log = getLogger(__name__)


from dartlab.scan.io.parquet import scanParquets


def _classifyPattern(
    dps0: float | None,
    dps1: float | None,
    dps2: float | None,
) -> str:
    """3개년 DPS → 배당 패턴 분류.

    Parameters
    ----------
    dps0 : float | None
        당기 주당배당금 (원).
    dps1 : float | None
        전기 주당배당금 (원).
    dps2 : float | None
        전전기 주당배당금 (원).

    Returns
    -------
    str
        패턴명. 다음 중 하나:
        무배당 / 시작 / 중단 / 연속증가 / 연속감소 / 안정 / 증가 / 감소 / 불규칙.
    """
    has0 = dps0 is not None and dps0 > 0
    has1 = dps1 is not None and dps1 > 0
    has2 = dps2 is not None and dps2 > 0

    if not has0 and not has1 and not has2:
        return "무배당"
    if has0 and not has1:
        return "시작"
    if not has0 and has1:
        return "중단"
    if has0 and has1 and has2:
        assert dps0 is not None and dps1 is not None and dps2 is not None
        if dps0 > dps1 > dps2:
            return "연속증가"
        if dps0 < dps1 < dps2:
            return "연속감소"
        # +-10% 이내 안정
        if dps1 > 0 and abs(dps0 - dps1) / dps1 <= 0.1:
            return "안정"
        if dps0 >= dps1:
            return "증가"
        return "감소"
    if has0 and has1:
        assert dps0 is not None and dps1 is not None
        if dps0 > dps1:
            return "증가"
        if dps0 < dps1:
            return "감소"
        return "안정"
    return "불규칙"


def scanDividendTrend(*, verbose: bool = True) -> pl.DataFrame:
    """전종목 배당 추이 스캔 — DPS 3개년 + 패턴 + 등급.

    Parameters
    ----------
    verbose : bool, default True
        진행 상황 출력 여부.

    Returns
    -------
    pl.DataFrame
        stockCode : str — 종목코드
        dpsCurrent : float — 당기 주당배당금 (원)
        dpsPrev : float — 전기 주당배당금 (원)
        dpsPrev2 : float — 전전기 주당배당금 (원)
        dpsGrowth : float — DPS 전기 대비 성장률 (%)
        payoutRatio : float — 현금배당성향 (%)
        yieldCurrent : float — 현금배당수익률 (%)
        pattern : str — 배당 패턴 (무배당/시작/중단/연속증가/연속감소/안정/증가/감소/불규칙)
        grade : str — 배당 등급 (우수/양호/보통/주의/위험/무배당)

    Raises
    ------
    polars.PolarsError
        dividend report parquet 손상 시.

    Examples
    --------
    >>> import dartlab
    >>> df = dartlab.scan("dividendTrend")
    >>> df.filter(pl.col("패턴") == "연속증가").select(["종목코드", "DPS성장"])

    Capabilities:
        - dividend report parquet 에서 종목별 DPS 3 개년 (당/전/전전기) + 성장률 + 배당성향 +
          배당수익률 추출. 패턴 9 종 (무배당/시작/중단/연속증가/연속감소/안정/증가/감소/불규칙)
          분류 + 6 단계 등급 (우수/양호/보통/주의/위험/무배당).
        - 보통주 + Q4 우선 선택. 연결재무 배당성향 우선.

    AIContext:
        Agent 가 ``dartlab.scan("dividendTrend")`` 호출 시 본 함수 dispatch. "고배당주" 스크리닝,
        "연속증가 배당주" watchlist, 배당정책 비교 분석 source.

    Guide:
        - DPS 3 개년 보유한 종목만 패턴 추정 가능. 신규 상장주는 패턴 = "시작" 또는 "무배당".
        - 등급 매핑: 연속증가 = 우수 / 안정 = 양호 / 무배당 = 무배당 / 중단 = 위험.

    When:
        대시보드 배당 카드 빌드 시. cross-company 배당 스크리닝 시.

    How:
        ``scanParquets("dividend", ...)`` → 보통주 + 주당현금배당금 row 필터 → 종목별 3 개년
        wide pivot → 성장률 + 배당성향 + 수익률 column + 패턴 분기 + 등급 분기.

    Requires:
        - 로컬 ``data/dart/scan/report/dividend.parquet`` (``buildReport`` 산출)
        - ``stock_knd == "보통주"`` row 필터

    SeeAlso:
        - :func:`dartlab.scan.builders.kr.core.buildReport` — source 빌드
        - :func:`dartlab.scan.capital.scanCapital` (capital axis) — 배당+자사주 통합 분류
    """
    raw = scanParquets(
        "dividend",
        ["stockCode", "year", "quarter", "se", "thstrm", "frmtrm", "lwfr", "stock_knd"],
    )
    if raw.is_empty():
        return pl.DataFrame()

    if verbose:
        _log.info(f"배당 추이 스캔: {raw.shape[0]}행 로드")

    normalized = raw.with_columns(
        pl.col("year").cast(pl.Utf8).str.strip_chars().cast(pl.Int32, strict=False).alias("_year"),
        pl.when(pl.col("quarter") == "4분기").then(1).otherwise(0).alias("_quarterRank"),
    )
    dpsRows = normalized.filter(
        (pl.col("se") == "주당 현금배당금(원)") & (pl.col("stock_knd") == "보통주") & pl.col("_year").is_not_null()
    )
    if dpsRows.is_empty():
        return pl.DataFrame()

    yearCoverage = (
        dpsRows.filter(pl.col("_quarterRank") == 1)
        .group_by("_year")
        .agg(pl.col("stockCode").n_unique().alias("_companyCount"))
        .sort("_year", descending=True)
    )
    completed = yearCoverage.filter(pl.col("_companyCount") >= 500)
    latestYear = completed["_year"][0] if not completed.is_empty() else dpsRows.select(pl.col("_year").max()).item()
    if latestYear is None:
        return pl.DataFrame()

    if verbose:
        _log.info(f"  기준 연도: {latestYear}")

    selectedYears = (
        dpsRows.group_by("stockCode")
        .agg(
            pl.col("_year").max().alias("_companyLatestYear"),
            (pl.col("_year") == latestYear).any().alias("_hasMarketYear"),
        )
        .with_columns(
            pl.when(pl.col("_hasMarketYear"))
            .then(pl.lit(latestYear))
            .otherwise(pl.col("_companyLatestYear"))
            .alias("_selectedYear")
        )
        .select("stockCode", "_selectedYear")
    )

    def _bestValueRows(source: pl.DataFrame, valueName: str) -> pl.DataFrame:
        return (
            source.join(selectedYears, on="stockCode")
            .filter(pl.col("_year") == pl.col("_selectedYear"))
            .sort(["stockCode", "_quarterRank"], descending=[False, True])
            .group_by("stockCode", maintain_order=True)
            .agg(amountExpr("thstrm").first().alias(valueName))
        )

    dps = (
        dpsRows.join(selectedYears, on="stockCode")
        .filter(pl.col("_year") == pl.col("_selectedYear"))
        .sort(["stockCode", "_quarterRank"], descending=[False, True])
        .group_by("stockCode", maintain_order=True)
        .agg(
            amountExpr("thstrm").first().alias("dpsCurrent"),
            amountExpr("frmtrm").first().alias("dpsPrev"),
            amountExpr("lwfr").first().alias("dpsPrev2"),
        )
    )
    yieldValues = _bestValueRows(
        normalized.filter((pl.col("se") == "현금배당수익률(%)") & (pl.col("stock_knd") == "보통주")),
        "yieldCurrent",
    )
    payoutValues = _bestValueRows(
        normalized.filter(pl.col("se") == "(연결)현금배당성향(%)"),
        "payoutRatio",
    )

    result = (
        dps.join(yieldValues, on="stockCode", how="left")
        .join(payoutValues, on="stockCode", how="left")
        .with_columns(
            pl.when(pl.col("dpsCurrent").is_not_null() & (pl.col("dpsPrev") > 0))
            .then((pl.col("dpsCurrent") - pl.col("dpsPrev")) / pl.col("dpsPrev") * 100)
            .otherwise(None)
            .round(1)
            .alias("dpsGrowth"),
            pl.struct("dpsCurrent", "dpsPrev", "dpsPrev2")
            .map_elements(
                lambda row: _classifyPattern(
                    row["dpsCurrent"],
                    row["dpsPrev"],
                    row["dpsPrev2"],
                ),
                return_dtype=pl.Utf8,
            )
            .alias("pattern"),
        )
        .with_columns(
            pl.when(pl.col("pattern") == "무배당")
            .then(pl.lit("무배당"))
            .when(pl.col("pattern") == "연속증가")
            .then(pl.lit("우수"))
            .when(pl.col("pattern").is_in(["안정", "증가", "시작"]))
            .then(pl.lit("양호"))
            .when(pl.col("pattern").is_in(["감소", "연속감소"]))
            .then(pl.lit("주의"))
            .when(pl.col("pattern") == "중단")
            .then(pl.lit("위험"))
            .otherwise(pl.lit("보통"))
            .alias("grade")
        )
        .select(
            "stockCode",
            "dpsCurrent",
            "dpsPrev",
            "dpsPrev2",
            "dpsGrowth",
            "payoutRatio",
            "yieldCurrent",
            "pattern",
            "grade",
        )
        .sort("stockCode")
    )

    if verbose:
        _log.info(f"배당 추이 스캔 완료: {result.height}종목")
    return result


__all__ = ["scanDividendTrend"]
