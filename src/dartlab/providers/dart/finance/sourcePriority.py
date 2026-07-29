"""DART 재무제표 CFS/OFS 원본 선택 정책.

연결·별도 재무제표를 행 단위로 섞지 않고, 연도·분기·재무제표 시트 단위로
하나의 원본을 선택한다. 선호 원본이 불완전하고 대체 원본의 계정 coverage가
strict superset일 때만 시트 전체를 대체한다.
"""

from __future__ import annotations

import logging

import polars as pl

_log = logging.getLogger(__name__)


def applyCfsPriority(df: pl.DataFrame, pref: str) -> pl.DataFrame:
    """시트 단위로 CFS/OFS 원본을 하나만 선택한다.

    Args:
        df: DART 재무 원본 DataFrame.
        pref: 선호 원본. ``"CFS"`` 또는 ``"OFS"``.

    Returns:
        시트별로 선택된 원본 행만 남긴 DataFrame.

    Raises:
        Polars 변환에 실패하면 해당 예외를 전달한다.

    Example:
        >>> import polars as pl
        >>> raw = pl.DataFrame({"fs_div": ["CFS"]})
        >>> applyCfsPriority(raw, "CFS").height
        1
    """
    if "fs_div" not in df.columns:
        return df

    available = set(df["fs_div"].drop_nulls().unique().to_list())
    if len(available) <= 1:
        return df

    groupCols = ["bsns_year", "reprt_nm", "sj_div"]
    if not all(c in df.columns for c in groupCols):
        return df

    fallback = "OFS" if pref == "CFS" else "CFS"
    accountId = (
        pl.col("account_id").fill_null("").cast(pl.Utf8).str.strip_chars() if "account_id" in df.columns else pl.lit("")
    )
    accountName = (
        pl.col("account_nm").fill_null("").cast(pl.Utf8).str.strip_chars() if "account_nm" in df.columns else pl.lit("")
    )
    coverageKey = (
        pl.when(accountId.is_in(["", "-표준계정코드 미사용-"]))
        .then(pl.concat_str([pl.lit("name"), accountName], separator=":"))
        .otherwise(pl.concat_str([pl.lit("id"), accountId], separator=":"))
    )

    amountCols = [c for c in ("thstrm_amount", "thstrm_add_amount") if c in df.columns]
    if amountCols:
        usableAmount = pl.any_horizontal(
            [pl.col(c).is_not_null() & ~pl.col(c).cast(pl.Utf8).str.strip_chars().is_in(["", "-"]) for c in amountCols]
        )
    else:
        usableAmount = pl.lit(True)

    coverageRows = (
        df.with_columns(coverageKey.alias("_coverageKey"), usableAmount.alias("_usableAmount"))
        .filter(pl.col("_usableAmount") & ~pl.col("_coverageKey").is_in(["id:", "name:"]))
        .select([*groupCols, "fs_div", "_coverageKey"])
        .unique()
    )
    coverageBySheet: dict[tuple[str, str, str, str], set[str]] = {}
    for row in coverageRows.iter_rows():
        sheetKey = (str(row[0]), str(row[1]), str(row[2]))
        source = str(row[3])
        coverageBySheet.setdefault((*sheetKey, source), set()).add(str(row[4]))

    sourceRows = df.select([*groupCols, "fs_div"]).drop_nulls("fs_div").unique()
    sourcesBySheet: dict[tuple[str, str, str], set[str]] = {}
    for row in sourceRows.iter_rows():
        sheetKey = (str(row[0]), str(row[1]), str(row[2]))
        sourcesBySheet.setdefault(sheetKey, set()).add(str(row[3]))

    decisionRows: list[dict[str, object]] = []
    for rawSheet in df.select(groupCols).unique().iter_rows():
        sheetKey = (str(rawSheet[0]), str(rawSheet[1]), str(rawSheet[2]))
        sources = sourcesBySheet.get(sheetKey, set())
        if not sources:
            continue
        if pref not in sources:
            target = fallback if fallback in sources else min(sources)
        else:
            preferredCoverage = coverageBySheet.get((*sheetKey, pref), set())
            fallbackCoverage = coverageBySheet.get((*sheetKey, fallback), set())
            fallbackDominates = bool(fallbackCoverage) and preferredCoverage < fallbackCoverage
            target = fallback if fallbackDominates else pref
            if fallbackDominates:
                _log.warning(
                    "finance source fallback: sheet=%s preferred=%s coverage=%d fallback=%s coverage=%d",
                    "/".join(sheetKey),
                    pref,
                    len(preferredCoverage),
                    fallback,
                    len(fallbackCoverage),
                )
        decisionRows.append({**dict(zip(groupCols, rawSheet, strict=True)), "_targetFs": target})

    sheetSources = pl.DataFrame(
        decisionRows,
        schema={**{col: df.schema[col] for col in groupCols}, "_targetFs": pl.Utf8},
    )
    return (
        df.join(sheetSources.select(groupCols + ["_targetFs"]), on=groupCols, how="left")
        .filter(pl.col("fs_div") == pl.col("_targetFs"))
        .drop("_targetFs")
    )
