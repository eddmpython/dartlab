"""실험 ID: 073-008
실험명: salaryGrowth — 급여 성장률 vs 매출 성장률

목적:
- employee 시계열로 급여 성장률 추출
- finance IS 시계열로 매출 성장률 추출
- 급여↑>매출↑ = 인건비 부담 증가 기업 식별

가설:
1. 급여 성장률 중앙값이 연 3~5%
2. 매출 대비 급여 성장률이 높은(급여>매출) 기업이 30% 이상
3. 코스닥이 유가보다 급여>매출 비율이 높다

방법:
1. employee 2개년도(최신 vs 직전) 급여 비교 → 급여 성장률
2. finance IS 2개년도 매출 비교 → 매출 성장률
3. 급여성장률 - 매출성장률 = 인건비 부담 지수
4. listing 조인으로 시장별/업종별 분석

결과 (2,223종목, 급여 2024→2025 / 매출 2023→2024):
- 급여 성장률: 평균 59.9%(이상치), 중앙값 3.1%
- 매출 성장률: 평균 31.0%(이상치), 중앙값 -0.0%
- 인건비부담(급여-매출): 평균 28.9%p, 중앙값 4.2%p
- 급여>매출: 1,258개 (56.6%)
- 시장별:
  - 유가: 급여 중앙값 +3.4%, 매출 중앙값 +1.1%, 급여>매출 55.5%
  - 코스닥: 급여 중앙값 +2.9%, 매출 중앙값 -1.5%, 급여>매출 57.0%
- 주의: 급여는 2024→2025(report), 매출은 2023→2024(finance 완전연도). 시점 1년 차이

결론:
- 가설1 채택: 급여 성장률 중앙값 3.1% (3~5% 범위 내)
- 가설2 채택: 급여>매출 기업 56.6% (30% 이상, 예상보다 높음)
- 가설3 기각: 코스닥 57.0% vs 유가 55.5% — 거의 동일 (유의미한 차이 아님)
- 코스닥 매출 중앙값이 -1.5% (역성장) → 급여는 오르는데 매출은 줄어드는 기업 다수
- 유가는 매출도 +1.1% 성장 → 급여 인상과 매출 성장이 어느 정도 동행
- 인건비 부담 중앙값 4.2%p → 절반 이상의 기업이 매출 대비 급여 부담 증가중
- workforce scan 보완 데이터로 유용. 수익성(영업이익률) 결합 시 더 정밀한 분석 가능

실험일: 2026-03-19
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def _scan_parquets(api_type: str, keep_cols: list[str]) -> pl.DataFrame:
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


def _parse_num(s) -> float | None:
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


QUARTER_ORDER = {"2분기": 1, "4분기": 2, "3분기": 3, "1분기": 4}


def _pick_best_quarter(df: pl.DataFrame) -> pl.DataFrame:
    quarters = df["quarter"].unique().to_list()
    best = sorted(quarters, key=lambda q: QUARTER_ORDER.get(q, 99))
    return df.filter(pl.col("quarter") == best[0]) if best else df


def _weighted_avg_salary(group: pl.DataFrame) -> float | None:
    """가중평균 급여(만원/연)."""
    total_emp, total_wsum = 0, 0.0
    for row in group.iter_rows(named=True):
        emp = _parse_num(row.get("sm"))
        sal = _parse_num(row.get("jan_salary_am"))
        if emp and emp > 0 and sal and sal > 0:
            total_emp += int(emp)
            total_wsum += emp * sal
    if total_emp > 0:
        return total_wsum / total_emp / 10000  # 만원/연
    return None


def scan_salary_growth() -> dict[str, dict]:
    """employee 2개년도 급여 비교."""
    raw = _scan_parquets(
        "employee",
        ["stockCode", "year", "quarter", "sm", "jan_salary_am"],
    )
    if raw.is_empty():
        return {}

    years = sorted(raw["year"].unique().to_list(), reverse=True)
    # 유효 2개년도 찾기
    valid_years = []
    for y in years:
        sub = raw.filter(pl.col("year") == y)
        ok = sub.filter(pl.col("jan_salary_am").is_not_null() & (pl.col("jan_salary_am") != "-")).shape[0]
        if ok >= 500:
            valid_years.append(y)
            if len(valid_years) == 2:
                break
    if len(valid_years) < 2:
        print("2개년도 데이터 부족")
        return {}

    y_new, y_old = valid_years[0], valid_years[1]
    print(f"급여 비교: {y_old} → {y_new}")

    result = {}
    for code in raw["stockCode"].unique().to_list():
        grp_new = raw.filter((pl.col("stockCode") == code) & (pl.col("year") == y_new))
        grp_old = raw.filter((pl.col("stockCode") == code) & (pl.col("year") == y_old))
        if grp_new.is_empty() or grp_old.is_empty():
            continue

        sal_new = _weighted_avg_salary(_pick_best_quarter(grp_new))
        sal_old = _weighted_avg_salary(_pick_best_quarter(grp_old))

        if sal_new and sal_old and sal_old > 100:  # 100만원 이상
            growth = (sal_new - sal_old) / sal_old * 100
            result[code] = {"급여성장률": round(growth, 1), "급여_신": round(sal_new, 0), "급여_구": round(sal_old, 0)}

    return result


REVENUE_IDS = {"Revenue", "Revenues", "revenue", "revenues",
               "ifrs-full_Revenue", "dart_Revenue",
               "RevenueFromContractsWithCustomers"}
REVENUE_NMS = {"매출액", "수익(매출액)", "영업수익", "매출", "순영업수익"}


def scan_revenue_growth() -> dict[str, float]:
    """finance IS 2개년도 매출 비교."""
    from dartlab.core.dataLoader import _dataDir

    finance_dir = Path(_dataDir("finance"))
    parquet_files = sorted(finance_dir.glob("*.parquet"))
    print(f"finance parquets: {len(parquet_files)}개")

    result: dict[str, float] = {}
    for i, pf in enumerate(parquet_files):
        if i % 500 == 0:
            print(f"  {i}/{len(parquet_files)}...")
        code = pf.stem

        try:
            df = pl.read_parquet(str(pf))
        except (pl.exceptions.ComputeError, OSError):
            continue

        if df.is_empty() or "account_id" not in df.columns:
            continue

        is_df = df.filter(
            pl.col("sj_div").is_in(["IS", "CIS"])
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
        )
        if is_df.is_empty():
            continue

        cfs = is_df.filter(pl.col("fs_nm").str.contains("연결"))
        target = cfs if not cfs.is_empty() else is_df

        rev_rows = target.filter(
            pl.col("account_id").is_in(list(REVENUE_IDS))
            | pl.col("account_nm").is_in(list(REVENUE_NMS))
        )
        if rev_rows.is_empty():
            rev_rows = target.filter(pl.col("account_nm").str.contains("매출"))
            if rev_rows.is_empty():
                continue

        # 불완전 연도 제외 (2025+ = 분기 누적 혼재, 연간 비교 불가)
        complete_years = sorted(
            [y for y in rev_rows["bsns_year"].unique().to_list() if y <= "2024"],
            reverse=True,
        )
        if len(complete_years) < 2:
            continue

        # 최신 완전 2개년
        new_rev = None
        old_rev = None
        for row in rev_rows.filter(pl.col("bsns_year") == complete_years[0]).iter_rows(named=True):
            val = _parse_num(row.get("thstrm_amount"))
            if val and val > 0:
                if new_rev is None or val > new_rev:
                    new_rev = val
        for row in rev_rows.filter(pl.col("bsns_year") == complete_years[1]).iter_rows(named=True):
            val = _parse_num(row.get("thstrm_amount"))
            if val and val > 0:
                if old_rev is None or val > old_rev:
                    old_rev = val

        if new_rev and old_rev and old_rev > 0:
            result[code] = round((new_rev - old_rev) / old_rev * 100, 1)

    print(f"매출 성장률: {len(result)}종목")
    return result


def compute_salary_vs_revenue() -> pl.DataFrame:
    sal_map = scan_salary_growth()
    print(f"급여 성장률: {len(sal_map)}종목")

    rev_map = scan_revenue_growth()

    # 매칭
    rows = []
    for code in sal_map:
        if code not in rev_map:
            continue
        sg = sal_map[code]["급여성장률"]
        rg = rev_map[code]
        burden = sg - rg  # 양수 = 급여가 매출보다 빠르게 성장

        rows.append({
            "종목코드": code,
            "급여성장률": sg,
            "매출성장률": rg,
            "인건비부담": round(burden, 1),
            "급여>매출": burden > 0,
        })

    df = pl.DataFrame(rows)
    total = df.shape[0]
    print(f"\n=== 급여 vs 매출 성장률 ({total}종목) ===")

    sg_vals = df["급여성장률"]
    rg_vals = df["매출성장률"]
    burden_vals = df["인건비부담"]
    sal_exceeds = df.filter(pl.col("급여>매출") == True).shape[0]

    print(f"급여 성장률: 평균 {sg_vals.mean():.1f}%, 중앙값 {sg_vals.median():.1f}%")
    print(f"매출 성장률: 평균 {rg_vals.mean():.1f}%, 중앙값 {rg_vals.median():.1f}%")
    print(f"인건비부담(급여-매출): 평균 {burden_vals.mean():.1f}%p, 중앙값 {burden_vals.median():.1f}%p")
    print(f"급여>매출: {sal_exceeds}개 ({sal_exceeds/total*100:.1f}%)")

    return df


def analyze_by_market(df: pl.DataFrame) -> None:
    from dartlab.market.network.scanner import load_listing
    _, _, _, listing_meta = load_listing()

    rows = []
    for row in df.iter_rows(named=True):
        meta = listing_meta.get(row["종목코드"], {})
        if meta:
            rows.append({**row, "시장": meta.get("market", "")})

    if not rows:
        return
    merged = pl.DataFrame(rows)

    for market in ["유가", "코스닥"]:
        sub = merged.filter(pl.col("시장") == market)
        if sub.is_empty():
            continue
        total = sub.shape[0]
        exceeds = sub.filter(pl.col("급여>매출") == True).shape[0]
        sg = sub["급여성장률"].median()
        rg = sub["매출성장률"].median()
        print(f"\n=== {market} ({total}종목) ===")
        print(f"급여 성장률 중앙값: {sg:.1f}%")
        print(f"매출 성장률 중앙값: {rg:.1f}%")
        print(f"급여>매출: {exceeds}개 ({exceeds/total*100:.1f}%)")


if __name__ == "__main__":
    df = compute_salary_vs_revenue()
    if not df.is_empty():
        analyze_by_market(df)
