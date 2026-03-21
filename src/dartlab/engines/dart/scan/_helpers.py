"""scan 공용 유틸리티 — report parquet 스캔, 숫자 파싱, listing 로드."""

from __future__ import annotations

from pathlib import Path

import polars as pl


def scan_parquets(api_type: str, keep_cols: list[str]) -> pl.DataFrame:
    """report parquet에서 특정 apiType만 LazyFrame 스캔.

    keep_cols 중 실제 존재하는 컬럼만 선택하며, 핵심 컬럼(meta 제외)이
    하나도 없는 parquet는 건너뛴다.  파일 간 스키마가 다르면 null 패딩으로 통합.
    """
    from dartlab.core.dataLoader import _dataDir

    report_dir = Path(_dataDir("report"))
    parquet_files = sorted(report_dir.glob("*.parquet"))

    frames: list[pl.LazyFrame] = []
    for pf in parquet_files:
        try:
            lf = pl.scan_parquet(str(pf))
            schema_names = lf.collect_schema().names()
            if "apiType" not in schema_names:
                continue
            available = [c for c in keep_cols if c in schema_names]
            non_meta = [c for c in available if c not in ("stockCode", "year", "quarter")]
            if not non_meta:
                continue
            lf = lf.filter(pl.col("apiType") == api_type).select(available)
            frames.append(lf)
        except (pl.exceptions.ComputeError, OSError):
            continue

    if not frames:
        return pl.DataFrame()

    all_cols: set[str] = set()
    for lf in frames:
        all_cols.update(lf.collect_schema().names())
    unified: list[pl.LazyFrame] = []
    for lf in frames:
        missing = all_cols - set(lf.collect_schema().names())
        if missing:
            lf = lf.with_columns([pl.lit(None).alias(c) for c in missing])
        unified.append(lf.select(sorted(all_cols)))

    return pl.concat(unified).collect()


def parse_num(s) -> float | None:
    """문자열/숫자 → float. '-', '', None → None."""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip().replace(",", "")
    if s in ("", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def find_latest_year(raw: pl.DataFrame, check_col: str, min_count: int = 500) -> str | None:
    """check_col에 유효 데이터가 min_count 이상인 가장 최근 연도 반환."""
    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        ok = sub.filter(pl.col(check_col).is_not_null() & (pl.col(check_col) != "-") & (pl.col(check_col) != "")).shape[
            0
        ]
        if ok >= min_count:
            return y
    return None


QUARTER_ORDER = {"2분기": 1, "4분기": 2, "3분기": 3, "1분기": 4}


def pick_best_quarter(df: pl.DataFrame) -> pl.DataFrame:
    """가장 선호하는 분기만 필터 (Q2 > Q4 > Q3 > Q1)."""
    quarters = df["quarter"].unique().to_list()
    best = sorted(quarters, key=lambda q: QUARTER_ORDER.get(q, 99))
    return df.filter(pl.col("quarter") == best[0]) if best else df


def load_listing():
    """상장사 목록 로드 (network/scanner.py 위임)."""
    from dartlab.engines.dart.scan.network.scanner import load_listing as _ll

    return _ll()


def parse_date_year(s) -> int | None:
    """'2021.06.15' 또는 '2021-06-15' → 2021."""
    if s is None:
        return None
    s = str(s).strip()
    if s in ("", "-"):
        return None
    for sep in (".", "-"):
        if sep in s:
            parts = s.split(sep)
            if parts:
                try:
                    y = int(parts[0])
                    if 1990 <= y <= 2030:
                        return y
                except ValueError:
                    pass
    return None


def scan_finance_parquets(
    statement: str,
    account_ids: set[str],
    account_nms: set[str],
    *,
    amount_col: str = "thstrm_amount",
) -> dict[str, float]:
    """finance parquet 전수 스캔 → {종목코드: 값}.

    statement: "BS", "IS", "CIS" 등
    account_ids/account_nms: 매칭 대상
    """
    from dartlab.core.dataLoader import _dataDir

    finance_dir = Path(_dataDir("finance"))
    parquet_files = sorted(finance_dir.glob("*.parquet"))

    result: dict[str, float] = {}
    sj_divs = [statement] if statement != "IS" else ["IS", "CIS"]
    for pf in parquet_files:
        code = pf.stem
        try:
            # lazy scan: 필터를 Rust 엔진으로 밀어넣어 메모리 절감
            target = (
                pl.scan_parquet(str(pf))
                .filter(
                    pl.col("sj_div").is_in(sj_divs)
                    & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
                )
                .collect()
            )
        except (pl.exceptions.PolarsError, OSError):
            continue

        if target.is_empty() or "account_id" not in target.columns:
            continue

        cfs = target.filter(pl.col("fs_nm").str.contains("연결"))
        target = cfs if not cfs.is_empty() else target

        years = sorted(target["bsns_year"].unique().to_list(), reverse=True)
        if not years:
            continue
        latest = target.filter(pl.col("bsns_year") == years[0])

        for row in latest.iter_rows(named=True):
            aid = row.get("account_id", "")
            anm = row.get("account_nm", "")
            val = parse_num(row.get(amount_col))
            if (aid in account_ids or anm in account_nms) and val is not None:
                result[code] = val
                break

    return result
