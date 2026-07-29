"""scan finance account labels and extraction helpers."""

from __future__ import annotations

import polars as pl

from dartlab.core.utils.helpers import parseNumStr
from dartlab.scan.io.calendar import filterLatestPeriodPerStock

# 같은 회계 개념의 snake_id / 표시명 변형을 한 곳에 통합.
# 신규 변형 발견 시 여기서만 추가 → scan/{efficiency,growth,profitability,valuation} 자동 반영.

REVENUE_IDS = {"Revenue", "revenue", "ifrs-full_Revenue", "dart_Revenue"}
REVENUE_NMS = {"매출액", "수익(매출액)", "영업수익"}

OP_IDS = {
    "ProfitLossFromOperatingActivities",
    "operatingIncome",
    "ifrs-full_ProfitLossFromOperatingActivities",
    "dart_OperatingIncomeLoss",
}
OP_NMS = {"영업이익", "영업이익(손실)"}

NI_IDS = {
    "ProfitLoss",
    "netIncome",
    "ifrs-full_ProfitLoss",
    "dart_ProfitLoss",
    "ProfitLossAttributableToOwnersOfParent",
}
NI_NMS = {"당기순이익", "당기순이익(손실)"}

TA_IDS = {"Assets", "totalAssets", "ifrs-full_Assets", "dart_Assets"}
TA_NMS = {"자산총계", "자산 총계"}

EQ_IDS = {
    "Equity",
    "equity",
    "ifrs-full_Equity",
    "EquityAttributableToOwnersOfParent",
    "ifrs-full_EquityAttributableToOwnersOfParent",
}
EQ_NMS = {"자본총계", "자본 총계", "지배기업 소유주지분"}

LIABILITY_IDS = {"Liabilities", "ifrs-full_Liabilities", "ifrs_Liabilities", "dart_Liabilities"}
LIABILITY_NMS = {"부채총계", "총부채", "부채 총계"}


def amountExpr(amtCol: str) -> pl.Expr:
    """회계 숫자 문자열을 Polars 식 하나로 정규화한다."""

    raw = pl.col(amtCol).cast(pl.Utf8).str.strip_chars()
    negative = raw.str.contains(r"^[△▲]") | (raw.str.starts_with("(") & raw.str.ends_with(")"))
    numeric = (
        raw.str.replace(r"^[△▲]", "")
        .str.strip_chars("() ")
        .str.replace_all(",", "")
        .str.replace_all("%", "")
        .str.strip_chars()
        .cast(pl.Float64, strict=False)
    )
    return pl.when(negative).then(-numeric.abs()).otherwise(numeric)


_amountExpr = amountExpr


def aggregateAccountValues(
    target: pl.DataFrame,
    groupCols: list[str],
    accountSpecs: dict[str, tuple[set[str], set[str], set[str] | None]],
    *,
    amtCol: str = "thstrm_amount",
) -> pl.DataFrame:
    """여러 계정 값을 그룹별로 한 번에 집계한다.

    ``accountSpecs`` 값은 ``(account_ids, account_names, sj_divs)``다.
    ``sj_divs``가 지정돼도 입력에 ``sj_div``가 없으면 계정 식별자만 사용한다.
    각 계정은 첫 유효 금액을 선택해 기존 :func:`extractAccount` 계약을 보존한다.
    """

    required = {*groupCols, "account_id", "account_nm", amtCol}
    if target.is_empty():
        return pl.DataFrame(
            schema={
                **{col: target.schema.get(col, pl.Utf8) for col in groupCols},
                **{name: pl.Float64 for name in accountSpecs},
            }
        )
    missing = sorted(required - set(target.columns))
    if missing:
        raise ValueError(f"account aggregation에 필요한 컬럼이 없습니다: {', '.join(missing)}")

    amountCol = "_scanAmount"
    work = target.with_columns(amountExpr(amtCol).alias(amountCol))
    expressions: list[pl.Expr] = []
    for name, (ids, names, statementDivs) in accountSpecs.items():
        matched = pl.col("account_id").is_in(ids) | pl.col("account_nm").is_in(names)
        if statementDivs is not None and "sj_div" in target.columns:
            matched &= pl.col("sj_div").is_in(statementDivs)
        expressions.append(pl.col(amountCol).filter(matched & pl.col(amountCol).is_not_null()).first().alias(name))
    return work.group_by(groupCols).agg(expressions)


def preferConsolidatedPerCompany(
    frame: pl.DataFrame,
    stockCodeCol: str = "stockCode",
) -> pl.DataFrame:
    """회사마다 연결재무제표를 우선하고 없는 회사는 별도를 남긴다."""

    if frame.is_empty() or "fs_nm" not in frame.columns or stockCodeCol not in frame.columns:
        return frame
    ranked = frame.with_columns(pl.when(pl.col("fs_nm").str.contains("연결")).then(0).otherwise(1).alias("_fsRank"))
    best = ranked.group_by(stockCodeCol).agg(pl.col("_fsRank").min().alias("_bestFsRank"))
    return (
        ranked.join(best, on=stockCodeCol)
        .filter(pl.col("_fsRank") == pl.col("_bestFsRank"))
        .drop("_fsRank", "_bestFsRank")
    )


def preferConsolidatedPerCompanyLazy(
    frame: pl.LazyFrame,
    stockCodeCol: str = "stockCode",
) -> pl.LazyFrame:
    """LazyFrame에 회사별 연결 우선 규칙을 적용한다."""

    columns = set(frame.collect_schema().names())
    if "fs_nm" not in columns or stockCodeCol not in columns:
        return frame
    ranked = frame.with_columns(pl.when(pl.col("fs_nm").str.contains("연결")).then(0).otherwise(1).alias("_fsRank"))
    best = ranked.group_by(stockCodeCol).agg(pl.col("_fsRank").min().alias("_bestFsRank"))
    return (
        ranked.join(best, on=stockCodeCol)
        .filter(pl.col("_fsRank") == pl.col("_bestFsRank"))
        .drop("_fsRank", "_bestFsRank")
    )


def aggregateLatestAccountValues(
    target: pl.DataFrame,
    accountSpecs: dict[str, tuple[set[str], set[str], set[str] | None]],
    *,
    stockCodeCol: str = "stockCode",
    yearCol: str = "bsns_year",
    amtCol: str = "thstrm_amount",
) -> pl.DataFrame:
    """회사별 선호 재무제표의 최신연도 계정을 한 번에 집계한다."""

    outputSchema = {
        stockCodeCol: target.schema.get(stockCodeCol, pl.Utf8),
        yearCol: target.schema.get(yearCol, pl.Utf8),
        **{name: pl.Float64 for name in accountSpecs},
    }
    if target.is_empty():
        return pl.DataFrame(schema=outputSchema)

    required = {stockCodeCol, yearCol, "fs_nm", "account_id", "account_nm", amtCol}
    missing = sorted(required - set(target.columns))
    if missing:
        raise ValueError(f"latest account aggregation에 필요한 컬럼이 없습니다: {', '.join(missing)}")

    latest = filterLatestPeriodPerStock(
        preferConsolidatedPerCompany(target, stockCodeCol),
        stockCodeCol,
        yearCol,
    )
    return aggregateAccountValues(
        latest,
        [stockCodeCol, yearCol],
        accountSpecs,
        amtCol=amtCol,
    )


def extractAccount(sub: pl.DataFrame, ids: set[str], nms: set[str], amtCol: str = "thstrm_amount") -> float | None:
    """DataFrame에서 account_id/account_nm 매칭 → 금액 추출.

    Parameters
    ----------
    sub : pl.DataFrame
        단일 종목의 재무 데이터.
    ids : set[str]
        매칭할 account_id 집합.
    nms : set[str]
        매칭할 account_nm 집합.
    amtCol : str
        금액 컬럼명 (기본 "thstrm_amount").

    Returns
    -------
    float | None
        첫 매칭 계정의 금액 (원). 매칭 없으면 None.

    Raises
    ------
    없음 — row.get 기본값 + parseNumStr None 폴백.

    Examples
    --------
    >>> from dartlab.scan.io.parquet import extractAccount
    >>> rev = extractAccount(subDf, {"Revenue"}, {"매출액"})

    Guide:
        account_id (XBRL tag) 또는 account_nm (한글 표시명) 매칭 row 중 첫 유효 amount 반환.

    Capabilities:
        ``parseNumStr`` 로 콤마/문자열 정수 변환.

    AIContext:
        scan financial 7 axis 의 per-file fallback 경로가 본 함수로 단일 종목 단면에서 계정 값 추출.

    When:
        scan/finance.parquet 합본 없거나 종목별 처리 필요할 때.

    How:
        row iterate → 첫 매칭 row 의 amount → parseNumStr → 반환.

    Requires:
        ``account_id`` · ``account_nm`` · ``amtCol`` 컬럼.

    SeeAlso:
        ``scanFinanceParquets`` — 횡단 합본 dict 반환.
    """
    for row in sub.iter_rows(named=True):
        aid = row.get("account_id", "")
        anm = row.get("account_nm", "")
        if aid in ids or anm in nms:
            val = parseNumStr(row.get(amtCol))
            if val is not None:
                return val
    return None
