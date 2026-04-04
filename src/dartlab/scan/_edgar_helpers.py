"""EDGAR scan 공용 헬퍼 — scanAccount 기반 전종목 재무 지표 계산.

DART scan은 프리빌드 parquet에서 읽지만, EDGAR scan은
providers/edgar/finance/scanAccount.py를 활용하여 전종목 XBRL 데이터를 읽는다.
"""

from __future__ import annotations

import polars as pl


def scan_edgar_accounts(snake_ids: list[str], *, annual: bool = True) -> pl.DataFrame:
    """여러 EDGAR 계정을 한번에 스캔하여 wide DataFrame으로 반환.

    Returns:
        stockCode | corpName | {snakeId}_latest | {snakeId}_prev | ...
    """
    from dartlab.providers.edgar.finance.scanAccount import scanAccount

    base: pl.DataFrame | None = None
    for sid in snake_ids:
        df = scanAccount(sid, annual=annual)
        if df.is_empty():
            continue
        # 가장 데이터가 많은 기간을 선택 (non-null 최다)
        period_cols = [c for c in df.columns if c not in ("stockCode", "corpName")]
        if len(period_cols) < 1:
            continue
        best_col = max(period_cols, key=lambda c: df[c].drop_nulls().len())
        prev_idx = period_cols.index(best_col) + 1
        prev_col = period_cols[prev_idx] if prev_idx < len(period_cols) else None
        select_cols = ["stockCode", "corpName", pl.col(best_col).alias(f"{sid}")]
        if prev_col:
            select_cols.append(pl.col(prev_col).alias(f"{sid}_prev"))
        narrow = df.select(select_cols)
        if base is None:
            base = narrow
        else:
            base = base.join(narrow, on="stockCode", how="outer", suffix=f"_{sid}")
            if f"corpName_{sid}" in base.columns:
                base = base.with_columns(
                    pl.coalesce(pl.col("corpName"), pl.col(f"corpName_{sid}")).alias("corpName")
                ).drop(f"corpName_{sid}")
    return base if base is not None else pl.DataFrame({"stockCode": []})


def safe_div(num: pl.Expr, den: pl.Expr) -> pl.Expr:
    """안전한 나눗셈 — 0이면 None."""
    return pl.when(den != 0).then(num / den).otherwise(None)


def pct(num: pl.Expr, den: pl.Expr) -> pl.Expr:
    """백분율 계산."""
    return (safe_div(num, den) * 100).round(2)


def scan_edgar_raw_tags(tags: list[str], *, annual: bool = True) -> pl.DataFrame:
    """XBRL 태그명으로 직접 ��종목 스캔 (snakeId 매핑 없이).

    Returns: stockCode | corpName | {tag1} | {tag2} | ...
    """
    from dartlab.providers.edgar.report import edgarFinancePath

    edgarDir = edgarFinancePath("_").parent
    if not edgarDir.exists():
        return pl.DataFrame()

    records = []
    for fp in edgarDir.glob("*.parquet"):
        cik = fp.stem
        try:
            df = pl.scan_parquet(fp).filter(
                pl.col("tag").is_in(tags)
                & pl.col("form").is_in(["10-K", "20-F"])
            ).select("tag", "val", "fy", "entityName").collect()

            if df.is_empty():
                continue

            # 최신 연도
            latestFy = df["fy"].max()
            latest = df.filter(pl.col("fy") == latestFy)

            record = {
                "stockCode": cik,
                "corpName": latest["entityName"][0] if latest.height > 0 else "",
            }
            for tag in tags:
                tagRows = latest.filter(pl.col("tag") == tag)
                record[tag] = tagRows["val"][0] if tagRows.height > 0 else None

            records.append(record)
        except (pl.exceptions.ComputeError, OSError):
            continue

    return pl.DataFrame(records) if records else pl.DataFrame()


def grade_by_value(val: pl.Expr, thresholds: list[tuple[float, str]], default: str = "해당없음") -> pl.Expr:
    """값 기반 등급 분류. thresholds는 (상한, 등급) 리스트 (오름차순)."""
    expr = val
    for i, (threshold, label) in enumerate(thresholds):
        if i == 0:
            expr = pl.when(val >= threshold).then(pl.lit(label))
        else:
            expr = expr.when(val >= threshold).then(pl.lit(label))
    return expr.otherwise(pl.lit(default))
