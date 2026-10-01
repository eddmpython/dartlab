"""scan finance.parquet 스키마 브릿지 — DART/EDGAR 통일 인터페이스.

DART scan parquet (행 기반):
    stockCode, bsns_year, fs_div, sj_div, account_nm, thstrm_amount, ...

EDGAR scan parquet (컬럼 기반):
    stockCode, fy, sales, operating_profit, net_profit, total_assets, ...

이 모듈은 두 스키마를 자동 감지하여 통일된 방식으로 계정을 추출한다.
corporateAggregate, quant ranking/screening/earningsMomentum 등에서 사용.
"""

from __future__ import annotations

import logging
from typing import overload

import polars as pl

log = logging.getLogger(__name__)

# ── DART 한글 → EDGAR snake_case 매핑 ──

ACCOUNT_MAP: dict[str, str] = {
    "매출액": "sales",
    "수익(매출액)": "sales",
    "영업수익": "sales",
    "영업이익": "operating_profit",
    "영업이익(손실)": "operating_profit",
    "영업이익 (손실)": "operating_profit",
    "당기순이익": "net_profit",
    "당기순이익(손실)": "net_profit",
    "부채총계": "total_liabilities",
    "자본총계": "total_stockholders_equity",
    "자산총계": "total_assets",
    "유동자산": "current_assets",
    "유동부채": "current_liabilities",
    "이자비용": "interest_expense",
    "금융비용": "interest_expense",
    "금융원가": "interest_expense",
    "감가상각비": "depreciation_amortization",
    "재고자산": "inventories",
    "매출채권": "trade_and_other_receivables",
    "매입채무": "trade_and_other_payables",
}

# 역방향 매핑 (EDGAR → DART)
_REVERSE_MAP: dict[str, list[str]] = {}
for _kr, _en in ACCOUNT_MAP.items():
    _REVERSE_MAP.setdefault(_en, []).append(_kr)


def isEdgarSchema(df: pl.DataFrame | pl.LazyFrame) -> bool:
    """DataFrame이 EDGAR 스키마인지 판별.

    Parameters
    ----------
    df : pl.DataFrame | pl.LazyFrame
        scan finance parquet.

    Returns
    -------
    bool
        True — EDGAR (fy 컬럼 존재, fs_nm 없음).
        False — DART (fs_nm 또는 sj_div 존재).
    """
    cols = df.collect_schema().names() if isinstance(df, pl.LazyFrame) else df.columns
    return "fy" in cols and "fs_nm" not in cols


@overload
def extractAnnualConsolidated(df: pl.DataFrame) -> pl.DataFrame: ...


@overload
def extractAnnualConsolidated(df: pl.LazyFrame) -> pl.LazyFrame: ...


def extractAnnualConsolidated(df: pl.DataFrame | pl.LazyFrame) -> pl.DataFrame | pl.LazyFrame:
    """연간 연결 재무 데이터 추출 — DART/EDGAR 자동 분기.

    Parameters
    ----------
    df : pl.DataFrame | pl.LazyFrame
        scan finance.parquet 데이터 또는 지연 실행 계획.

    Returns
    -------
    pl.DataFrame | pl.LazyFrame
        DART: 연결재무제표 + 4분기 행만.
        EDGAR: 그대로 반환 (이미 연간 연결 기준).
        입력의 eager/lazy 형태를 유지한다.
    """
    if isEdgarSchema(df):
        return df
    # DART
    columns = df.collect_schema().names() if isinstance(df, pl.LazyFrame) else df.columns
    if "fs_nm" in columns:
        return df.filter((pl.col("fs_nm") == "연결재무제표") & (pl.col("reprt_nm") == "4분기"))
    if "fs_div" in columns:
        return df.filter(pl.col("fs_div") == "CFS")
    return df


def getAccountValue(
    df: pl.DataFrame,
    account: str,
    *,
    year: str | None = None,
) -> dict[str, float]:
    """통일 계정 추출 — DART/EDGAR 자동 분기.

    Parameters
    ----------
    df : pl.DataFrame
        extractAnnualConsolidated 결과.
    account : str
        계정명 (한글 또는 영문). 예: "영업이익", "operating_profit".
    year : str | None
        특정 연도만 필터. None이면 전체.

    Returns
    -------
    dict[str, float]
        {종목코드: 금액} 매핑.
    """
    if isEdgarSchema(df):
        return _getAccountEdgar(df, account, year=year)
    return _getAccountDart(df, account, year=year)


def _getAccountEdgar(df: pl.DataFrame, account: str, *, year: str | None = None) -> dict[str, float]:
    """EDGAR: 직접 컬럼명으로 추출."""
    # 한글이면 영문으로 변환
    col = ACCOUNT_MAP.get(account, account)
    if col not in df.columns:
        return {}

    target = df
    if year and "fy" in df.columns:
        # fy가 int일 수 있으므로 양쪽 타입 맞춤
        try:
            target = target.filter(pl.col("fy") == int(year))
        except (ValueError, TypeError):
            target = target.filter(pl.col("fy").cast(pl.Utf8) == str(year))

    result: dict[str, float] = {}
    for row in target.iter_rows(named=True):
        code = row.get("stockCode", "")
        val = row.get(col)
        if code and val is not None:
            try:
                result[code] = float(val)
            except (ValueError, TypeError):
                pass
    return result


def _getAccountDart(df: pl.DataFrame, account: str, *, year: str | None = None) -> dict[str, float]:
    """DART: account_nm 매칭으로 추출."""
    from dartlab.core.utils.helpers import parseNumStr as parseNumStr

    # 영문이면 한글 목록으로 변환
    if account in _REVERSE_MAP:
        names = set(_REVERSE_MAP[account])
    else:
        names = {account}
        # 한글 → 영문 → 한글 역방향도 시도
        en = ACCOUNT_MAP.get(account)
        if en and en in _REVERSE_MAP:
            names = set(_REVERSE_MAP[en])
        names.add(account)

    # sj_div 추정
    sj = _guessSjDiv(account)

    target = df
    if year and "bsns_year" in df.columns:
        target = target.filter(pl.col("bsns_year") == year)

    if sj and "sj_div" in target.columns:
        target = target.filter(pl.col("sj_div") == sj)

    matched = target.filter(pl.col("account_nm").is_in(list(names)))

    result: dict[str, float] = {}
    for row in matched.iter_rows(named=True):
        code = row.get("stockCode", "")
        val = parseNumStr(row.get("thstrm_amount"))
        if code and val is not None and code not in result:
            result[code] = val
    return result


def sumAccountByYear(
    df: pl.DataFrame,
    account: str,
) -> pl.DataFrame:
    """기간별 계정 합계 — DART/EDGAR 자동 분기.

    Parameters
    ----------
    df : pl.DataFrame
        extractAnnualConsolidated 결과.
    account : str
        계정명 (한글 또는 영문).

    Returns
    -------
    pl.DataFrame
        year : str — 기간
        total : float — 합계 (원 또는 USD)
        count : int — 종목 수
    """
    if isEdgarSchema(df):
        return _sumEdgar(df, account)
    return _sumDart(df, account)


def _sumEdgar(df: pl.DataFrame, account: str) -> pl.DataFrame:
    """EDGAR: 직접 컬럼 group_by."""
    col = ACCOUNT_MAP.get(account, account)
    if col not in df.columns:
        return pl.DataFrame(schema={"year": pl.Utf8, "total": pl.Float64, "count": pl.Int64})

    return (
        df.filter(pl.col(col).is_not_null())
        .with_columns(pl.col("fy").cast(pl.Utf8).alias("year"))
        .group_by("year")
        .agg(
            pl.col(col).cast(pl.Float64, strict=False).sum().alias("total"),
            pl.col("stockCode").n_unique().alias("count"),
        )
        .sort("year")
    )


def _sumDart(df: pl.DataFrame, account: str) -> pl.DataFrame:
    """DART: sj_div + account_nm 필터 후 group_by."""

    if account in _REVERSE_MAP:
        names = set(_REVERSE_MAP[account])
    else:
        names = {account}
        en = ACCOUNT_MAP.get(account)
        if en and en in _REVERSE_MAP:
            names = set(_REVERSE_MAP[en])
        names.add(account)

    sj = _guessSjDiv(account)
    filtered = df.filter(pl.col("account_nm").is_in(list(names)))
    if sj and "sj_div" in filtered.columns:
        filtered = filtered.filter(pl.col("sj_div") == sj)

    return (
        filtered.group_by("bsns_year")
        .agg(
            pl.col("thstrm_amount").cast(pl.Float64, strict=False).sum().alias("total"),
            pl.col("stockCode").n_unique().alias("count"),
        )
        .rename({"bsns_year": "year"})
        .sort("year")
    )


def medianRatioByYear(
    df: pl.DataFrame,
    numerAccount: str,
    denomAccount: str,
) -> pl.DataFrame:
    """기간별 비율 중간값 — DART/EDGAR 자동 분기.

    Parameters
    ----------
    df : pl.DataFrame
        extractAnnualConsolidated 결과.
    numer_account : str
        분자 계정명.
    denom_account : str
        분모 계정명.

    Returns
    -------
    pl.DataFrame
        year : str — 기간
        median_ratio : float — 중간값 (%)
    """
    if isEdgarSchema(df):
        return _medianRatioEdgar(df, numerAccount, denomAccount)
    return _medianRatioDart(df, numerAccount, denomAccount)


def _medianRatioEdgar(df: pl.DataFrame, numer: str, denom: str) -> pl.DataFrame:
    ncol = ACCOUNT_MAP.get(numer, numer)
    dcol = ACCOUNT_MAP.get(denom, denom)
    if ncol not in df.columns or dcol not in df.columns:
        return pl.DataFrame(schema={"year": pl.Utf8, "median_ratio": pl.Float64})

    valid = df.filter(pl.col(dcol).abs() > 0)
    valid = valid.with_columns(
        (pl.col(ncol) / pl.col(dcol) * 100).alias("ratio"),
        pl.col("fy").cast(pl.Utf8).alias("year"),
    )
    return valid.group_by("year").agg(pl.col("ratio").median().alias("median_ratio")).sort("year")


def _medianRatioDart(df: pl.DataFrame, numer: str, denom: str) -> pl.DataFrame:
    """DART: 기존 corporateAggregate._median_ratio 로직."""
    numer_names = _resolveNames(numer)
    denom_names = _resolveNames(denom)
    sj = _guessSjDiv(numer) or "BS"

    n = df.filter((pl.col("sj_div") == sj) & pl.col("account_nm").is_in(list(numer_names))).select(
        "bsns_year", "stockCode", pl.col("thstrm_amount").cast(pl.Float64, strict=False).alias("numer")
    )
    d = df.filter((pl.col("sj_div") == sj) & pl.col("account_nm").is_in(list(denom_names))).select(
        "bsns_year", "stockCode", pl.col("thstrm_amount").cast(pl.Float64, strict=False).alias("denom")
    )
    joined = n.join(d, on=["bsns_year", "stockCode"], how="inner")
    joined = joined.filter(pl.col("denom").abs() > 0)
    joined = joined.with_columns((pl.col("numer") / pl.col("denom") * 100).alias("ratio"))
    return (
        joined.group_by("bsns_year")
        .agg(pl.col("ratio").median().alias("median_ratio"))
        .rename({"bsns_year": "year"})
        .sort("year")
    )


def _resolveNames(account: str) -> set[str]:
    """계정명 → 매칭 가능한 이름 세트."""
    if account in _REVERSE_MAP:
        return set(_REVERSE_MAP[account])
    names = {account}
    en = ACCOUNT_MAP.get(account)
    if en and en in _REVERSE_MAP:
        names = set(_REVERSE_MAP[en])
    names.add(account)
    return names


def _guessSjDiv(account: str) -> str | None:
    """계정명에서 sj_div 추정."""
    en = ACCOUNT_MAP.get(account, account)
    if en in (
        "sales",
        "operating_profit",
        "net_profit",
        "interest_expense",
        "depreciation_amortization",
        "cost_of_goods_sold",
        "gross_profit",
        "selling_general_and_administrative",
        "research_and_development",
    ):
        return "IS"
    if en in (
        "operating_cashflow",
        "investing_cashflow",
        "financing_cash_flow",
        "capex",
        "dividends_paid",
        "share_repurchase",
    ):
        return "CF"
    return "BS"
