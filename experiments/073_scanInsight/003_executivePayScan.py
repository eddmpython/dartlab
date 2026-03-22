"""실험 ID: 073-003
실험명: executivePay + employee 전수 스캔 — 임원보수/직원급여 비율 시장 분포

목적:
- executivePayAllTotal + employee를 전종목 스캔
- 임원 1인 평균보수 vs 직원 1인 평균급여 비율 (pay ratio) 분포
- 업종별/시장별 차이, 극단값 파악

가설:
1. 임원 1인 평균보수 / 직원 1인 평균급여 배율 중앙값이 3~5배
2. pay ratio 10배 이상 기업이 전체의 5% 이상 존재
3. 업종별로 pay ratio에 유의미한 차이가 있다

방법:
1. _scan_parquets로 executivePayAllTotal + employee 전수 스캔
2. 최신 연도 + 최적 분기(Q2 선호) 기준 종목별:
   - 임원: jan_avrg_mendng_am (1인 평균 연간보수, 원)
   - 직원: jan_salary_am (1인 평균 연간급여, 원), sm (직원수) → 가중평균
3. pay ratio = 임원 1인평균보수 / 직원 1인평균급여 (둘 다 연간/원)
4. listing 조인으로 업종별/시장별 분석

단위 확인:
- jan_avrg_mendng_am: 1인 평균 연간보수(원) — 동화약품 97,000,000 = 9700만원/연 ✓
- jan_salary_am: 1인 평균 연간급여(원) — 동화약품 남 19,000,000원 ≈ fyer_salary_totamt/sm ✓
- fyer_salary_totamt: 연간급여총액(원)

결과 (2025년 기준, 2,427종목 매칭):
- executivePayAllTotal: 110,813행, 2,636종목 → 2,474 유효
- employee: 300,371행, 2,641종목 → 2,441 유효
- 임원 1인평균보수: 평균 12,203만원, 중앙값 7,600만원, 최대 21.8억원
- 직원 1인평균급여: 평균 5,705만원, 중앙값 3,019만원
- pay ratio (임원/직원 연봉 배율):
  - 평균: 20.7배 (극단값 포함), 중앙값: 2.5배
  - Q1: 1.7배, Q3: 3.9배
  - 구간 분포:
    | 0~1배: 169 (7.0%) | 1~2배: 649 (26.7%) | 2~3배: 620 (25.5%) |
    | 3~5배: 578 (23.8%) | 5~10배: 314 (12.9%) | 10~20배: 61 (2.5%) |
    | 20배+: 36 (1.5%)   |
  - 10배 이상: 97개 (4.0%)
  - 5배 이상: 411개 (16.9%)
- 시장별: 유가 중앙값 3.0배, 코스닥 중앙값 2.3배 (유가가 약간 높음)
- 업종별 높은 곳(중앙값): 비료/농약(5.7), 부동산(3.9), 선박(3.7)
- 업종별 낮은 곳(중앙값): 펄프/종이(1.1), 신탁(1.65), 영상음향(1.65)
- 극단 이상치: 직원급여 2~4만원/연인 기업 약 20개 → 직원 없거나 파트타임 데이터 이슈

결론:
- 가설1 기각: 중앙값 2.5배 (3~5배 예상보다 낮음). 한국 시장 임원보수가 상대적으로 낮은 수준
- 가설2 기각: 10배 이상 4.0% (5% 미만). 다만 5배 이상은 16.9%로 유의미
- 가설3 채택: 업종간 차이 존재 (비료 5.7배 vs 펄프 1.1배, 약 5배 차이)
- 주의: 직원급여 극소값(2~4만원/연) 기업이 평균 배율을 왜곡 → 중앙값이 더 신뢰할 만
- 유가증권이 코스닥보다 약간 높은 건 대기업 CEO 보수 효과
- governance scan의 세 번째 축으로 유효. 다만 극단값 필터 필요

실험일: 2026-03-19
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def _scan_parquets(api_type: str, keep_cols: list[str]) -> pl.DataFrame:
    """report parquet에서 특정 apiType만 LazyFrame 스캔."""
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


def _parse_won(s: str | None) -> float | None:
    """원(won) 문자열 → float. 콤마 제거."""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    s = s.strip().replace(",", "")
    if s in ("", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


QUARTER_ORDER = {"2분기": 1, "4분기": 2, "3분기": 3, "1분기": 4}


def _pick_best_quarter(df: pl.DataFrame) -> pl.DataFrame:
    """Q2 선호, 없으면 Q4, Q3, Q1 순으로 최적 분기 선택."""
    quarters = df["quarter"].unique().to_list()
    best = sorted(quarters, key=lambda q: QUARTER_ORDER.get(q, 99))
    if best:
        return df.filter(pl.col("quarter") == best[0])
    return df


def scan_executive_pay() -> pl.DataFrame:
    """executivePayAllTotal 전수 스캔 → 종목별 임원 1인평균보수(만원/연)."""
    raw = _scan_parquets(
        "executivePayAllTotal",
        ["stockCode", "year", "quarter", "nmpr", "mendng_totamt", "jan_avrg_mendng_am"],
    )
    if raw.is_empty():
        print("executivePayAllTotal 데이터 없음")
        return pl.DataFrame()

    print(f"executivePayAllTotal 원본: {raw.shape[0]}행, {raw['stockCode'].n_unique()}종목")

    # 최신 연도: jan_avrg_mendng_am이 유효("-"이 아닌) 행 500개 이상
    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        ok = sub.filter(
            pl.col("jan_avrg_mendng_am").is_not_null()
            & (pl.col("jan_avrg_mendng_am") != "-")
            & (pl.col("jan_avrg_mendng_am") != "")
        ).shape[0]
        if ok >= 500:
            latest_year = y
            break
    if latest_year is None:
        print("충분한 데이터 없음")
        return pl.DataFrame()

    latest = raw.filter(pl.col("year") == latest_year)
    print(f"기준 연도({latest_year}): {latest.shape[0]}행, {latest['stockCode'].n_unique()}종목")

    # 종목별: 최적 분기 → nmpr 가중평균 jan_avrg_mendng_am
    results = []
    for code, group in latest.group_by("stockCode"):
        code_val = code[0]
        qdf = _pick_best_quarter(group)

        weighted_sum = 0.0
        total_nmpr = 0

        for row in qdf.iter_rows(named=True):
            nmpr = _parse_won(row.get("nmpr"))
            avg_pay = _parse_won(row.get("jan_avrg_mendng_am"))
            if nmpr and nmpr > 0 and avg_pay and avg_pay > 0:
                weighted_sum += nmpr * avg_pay
                total_nmpr += int(nmpr)

        avg_pay_won = weighted_sum / total_nmpr if total_nmpr > 0 else None

        results.append({
            "종목코드": code_val,
            "임원수": total_nmpr if total_nmpr > 0 else None,
            "임원1인보수_만원": round(avg_pay_won / 10000, 0) if avg_pay_won else None,
        })

    df = pl.DataFrame(results)
    valid = df.filter(pl.col("임원1인보수_만원").is_not_null() & (pl.col("임원1인보수_만원") > 0))
    print(f"임원보수 집계: {df.shape[0]}종목 (유효: {valid.shape[0]})")

    pays = valid["임원1인보수_만원"].drop_nulls()
    print(f"\n=== 임원 1인평균보수 분포 (만원/연) ===")
    print(f"평균: {pays.mean():,.0f}")
    print(f"중앙값: {pays.median():,.0f}")
    print(f"최소: {pays.min():,.0f}")
    print(f"최대: {pays.max():,.0f}")

    return df


def scan_employee() -> pl.DataFrame:
    """employee 전수 스캔 → 종목별 직원 1인평균급여(만원/연)."""
    raw = _scan_parquets(
        "employee",
        ["stockCode", "year", "quarter", "sexdstn", "sm",
         "jan_salary_am", "fyer_salary_totamt"],
    )
    if raw.is_empty():
        print("employee 데이터 없음")
        return pl.DataFrame()

    print(f"\nemployee 원본: {raw.shape[0]}행, {raw['stockCode'].n_unique()}종목")

    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        ok = sub.filter(
            pl.col("jan_salary_am").is_not_null()
            & (pl.col("jan_salary_am") != "-")
            & (pl.col("jan_salary_am") != "")
        ).shape[0]
        if ok >= 500:
            latest_year = y
            break
    if latest_year is None:
        print("충분한 데이터 없음")
        return pl.DataFrame()

    latest = raw.filter(pl.col("year") == latest_year)
    print(f"기준 연도({latest_year}): {latest.shape[0]}행, {latest['stockCode'].n_unique()}종목")

    # 종목별: 최적 분기 → sm(직원수) 가중평균 jan_salary_am(1인 연간급여)
    results = []
    for code, group in latest.group_by("stockCode"):
        code_val = code[0]
        qdf = _pick_best_quarter(group)

        weighted_sum = 0.0
        total_emp = 0

        for row in qdf.iter_rows(named=True):
            emp = _parse_won(row.get("sm"))
            sal = _parse_won(row.get("jan_salary_am"))
            if emp and emp > 0 and sal and sal > 0:
                weighted_sum += emp * sal
                total_emp += int(emp)

        avg_annual_won = weighted_sum / total_emp if total_emp > 0 else None

        results.append({
            "종목코드": code_val,
            "총직원수": total_emp if total_emp > 0 else None,
            "직원1인급여_만원": round(avg_annual_won / 10000, 0) if avg_annual_won else None,
        })

    df = pl.DataFrame(results)
    valid = df.filter(pl.col("직원1인급여_만원").is_not_null() & (pl.col("직원1인급여_만원") > 0))
    print(f"직원급여 집계: {df.shape[0]}종목 (유효: {valid.shape[0]})")

    sals = valid["직원1인급여_만원"].drop_nulls()
    print(f"\n=== 직원 1인평균급여 분포 (만원/연) ===")
    print(f"평균: {sals.mean():,.0f}")
    print(f"중앙값: {sals.median():,.0f}")
    print(f"최소: {sals.min():,.0f}")
    print(f"최대: {sals.max():,.0f}")

    return df


def compute_pay_ratio(exec_df: pl.DataFrame, emp_df: pl.DataFrame) -> pl.DataFrame:
    """임원보수/직원급여 비율 계산.

    둘 다 만원/연 단위이므로 바로 비율 계산.
    pay ratio = 임원1인보수 / 직원1인급여
    """
    merged = exec_df.join(emp_df, on="종목코드", how="inner")
    merged = merged.filter(
        pl.col("임원1인보수_만원").is_not_null()
        & pl.col("직원1인급여_만원").is_not_null()
        & (pl.col("임원1인보수_만원") > 0)
        & (pl.col("직원1인급여_만원") > 0)
    )

    merged = merged.with_columns(
        (pl.col("임원1인보수_만원") / pl.col("직원1인급여_만원")).round(1).alias("배율")
    )

    print(f"\n=== pay ratio (임원/직원 연봉 배율) ===")
    print(f"매칭 종목: {merged.shape[0]}")

    ratios = merged["배율"].drop_nulls()
    if ratios.len() == 0:
        return merged

    print(f"평균: {ratios.mean():.1f}배")
    print(f"중앙값: {ratios.median():.1f}배")
    print(f"최소: {ratios.min():.1f}배")
    print(f"최대: {ratios.max():.1f}배")
    print(f"Q1(25%): {ratios.quantile(0.25):.1f}배")
    print(f"Q3(75%): {ratios.quantile(0.75):.1f}배")

    # 구간 분포
    bins = [0, 1, 2, 3, 5, 10, 20, 50, 100, 200]
    total = ratios.len()
    print(f"\n=== 배율 구간별 분포 ===")
    for i in range(len(bins) - 1):
        lo, hi = bins[i], bins[i + 1]
        cnt = ratios.filter((ratios >= lo) & (ratios < hi)).len()
        pct = cnt / total * 100
        bar = "█" * int(pct / 2)
        print(f"{lo:3d}~{hi:3d}배: {cnt:4d} ({pct:5.1f}%) {bar}")
    over = ratios.filter(ratios >= 200).len()
    if over:
        print(f"200배+: {over:4d} ({over/total*100:5.1f}%)")

    # 10배 이상
    over10 = ratios.filter(ratios >= 10).len()
    print(f"\n10배 이상: {over10}개 ({over10/total*100:.1f}%)")
    over5 = ratios.filter(ratios >= 5).len()
    print(f"5배 이상: {over5}개 ({over5/total*100:.1f}%)")

    return merged


def analyze_by_market(merged: pl.DataFrame) -> None:
    """시장별/업종별 pay ratio 분석."""
    from dartlab.engines.dart.scan.network.scanner import load_listing

    _, _, _, listing_meta = load_listing()

    rows = []
    for row in merged.iter_rows(named=True):
        meta = listing_meta.get(row["종목코드"], {})
        if meta:
            rows.append({**row, "시장": meta.get("market", ""), "업종": meta.get("industry", "")})

    if not rows:
        return

    df = pl.DataFrame(rows)

    # 시장별
    market_stats = (
        df.group_by("시장")
        .agg([
            pl.col("배율").mean().alias("평균배율"),
            pl.col("배율").median().alias("중앙값"),
            pl.col("종목코드").count().alias("종목수"),
        ])
        .sort("평균배율", descending=True)
    )
    print(f"\n=== 시장별 pay ratio ===")
    print(market_stats)

    # 업종별 (5개 이상)
    industry_stats = (
        df.group_by("업종")
        .agg([
            pl.col("배율").mean().alias("평균배율"),
            pl.col("배율").median().alias("중앙값"),
            pl.col("종목코드").count().alias("종목수"),
        ])
        .filter(pl.col("종목수") >= 5)
        .sort("평균배율", descending=True)
    )
    print(f"\n=== pay ratio 높은 업종 ===")
    print(industry_stats.head(10))
    print(f"\n=== pay ratio 낮은 업종 ===")
    print(industry_stats.tail(10))

    # 극단값: 10배 이상
    extreme = df.filter(pl.col("배율") >= 10).sort("배율", descending=True)
    print(f"\n=== pay ratio 10배 이상 ({extreme.shape[0]}개) ===")
    print(extreme.select(["종목코드", "임원수", "임원1인보수_만원", "직원1인급여_만원", "배율", "업종"]).head(15))


if __name__ == "__main__":
    exec_df = scan_executive_pay()
    if exec_df.is_empty():
        print("임원보수 데이터 없음, 종료")
        sys.exit(1)

    emp_df = scan_employee()
    if emp_df.is_empty():
        print("직원급여 데이터 없음, 종료")
        sys.exit(1)

    merged = compute_pay_ratio(exec_df, emp_df)
    if not merged.is_empty():
        analyze_by_market(merged)
