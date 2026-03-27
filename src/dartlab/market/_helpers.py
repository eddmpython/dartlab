"""scan 공용 유틸리티 — report parquet 스캔, 숫자 파싱, listing 로드."""

from __future__ import annotations

from pathlib import Path

import polars as pl


def scan_parquets(api_type: str, keep_cols: list[str]) -> pl.DataFrame:
    """report parquet에서 특정 apiType만 LazyFrame 스캔.

    scan/report/{apiType}.parquet 프리빌드가 있으면 단일 파일에서 즉시 로드.
    없으면 종목별 parquet 순회 (fallback).
    """
    from dartlab.core.dataLoader import _dataDir

    # 1순위: 프리빌드 scan parquet
    scan_path = Path(_dataDir("scan")) / "report" / f"{api_type}.parquet"
    if scan_path.exists():
        try:
            lf = pl.scan_parquet(str(scan_path))
            schema_names = lf.collect_schema().names()
            available = [c for c in keep_cols if c in schema_names]
            non_meta = [c for c in available if c not in ("stockCode", "year", "quarter")]
            if non_meta:
                return lf.select(available).collect()
        except (pl.exceptions.PolarsError, OSError):
            pass  # fallback to per-file scan

    # 2순위: 종목별 순회 (fallback)
    report_dir = Path(_dataDir("report"))
    parquet_files = sorted(report_dir.glob("*.parquet"))

    if not parquet_files:
        from dartlab.core.guidance import emit

        emit("hint:market_data_needed", category="report", fn=api_type)
        return pl.DataFrame()

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
    from dartlab.market.network.scanner import load_listing as _ll

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


def _scanFinanceFromMerged(
    scanPath: Path,
    sjDivs: list[str],
    accountIds: set[str],
    accountNms: set[str],
    amountCol: str,
) -> dict[str, float]:
    """합산 finance parquet에서 종목별 최신 연도 값 추출."""
    scCol = "stockCode" if "stockCode" in pl.scan_parquet(str(scanPath)).collect_schema().names() else "stock_code"

    target = (
        pl.scan_parquet(str(scanPath))
        .filter(
            pl.col("sj_div").is_in(sjDivs)
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
        )
        .collect()
    )

    if target.is_empty() or "account_id" not in target.columns:
        return {}

    # 연결 우선
    cfs = target.filter(pl.col("fs_nm").str.contains("연결"))
    target = cfs if not cfs.is_empty() else target

    # 종목별 최신 연도만
    latestYear = (
        target.group_by(scCol)
        .agg(pl.col("bsns_year").max().alias("_maxYear"))
    )
    target = target.join(latestYear, on=scCol).filter(pl.col("bsns_year") == pl.col("_maxYear")).drop("_maxYear")

    # 계정 매칭
    matched = target.filter(
        pl.col("account_id").is_in(list(accountIds)) | pl.col("account_nm").is_in(list(accountNms))
    )

    result: dict[str, float] = {}
    for row in matched.iter_rows(named=True):
        code = row.get(scCol, "")
        if code and code not in result:
            val = parse_num(row.get(amountCol))
            if val is not None:
                result[code] = val

    return result


def scan_finance_parquets(
    statement: str,
    account_ids: set[str],
    account_nms: set[str],
    *,
    amount_col: str = "thstrm_amount",
) -> dict[str, float]:
    """finance parquet 전수 스캔 → {종목코드: 값}.

    scan/finance.parquet 프리빌드가 있으면 단일 파일에서 즉시 필터.
    없으면 종목별 parquet 순회 (fallback).
    """
    from dartlab.core.dataLoader import _dataDir

    sj_divs = [statement] if statement != "IS" else ["IS", "CIS"]

    # 1순위: 프리빌드 scan parquet
    scan_path = Path(_dataDir("scan")) / "finance.parquet"
    if scan_path.exists():
        try:
            return _scanFinanceFromMerged(scan_path, sj_divs, account_ids, account_nms, amount_col)
        except (pl.exceptions.PolarsError, OSError):
            pass  # fallback

    # 2순위: 종목별 순회 (fallback)
    finance_dir = Path(_dataDir("finance"))
    parquet_files = sorted(finance_dir.glob("*.parquet"))

    result: dict[str, float] = {}
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
