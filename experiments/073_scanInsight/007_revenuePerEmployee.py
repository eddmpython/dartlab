"""실험 ID: 073-007
실험명: revenuePerEmployee — 직원당 매출 시장 분포

목적:
- finance IS(매출액) + employee(직원수) 전수 스캔
- 직원당 매출(revenue per employee) 업종별 분포
- 인력 효율성 인사이트

가설:
1. 직원당 매출 중앙값이 3~5억원
2. 업종별 직원당 매출 차이가 10배 이상
3. 유가증권이 코스닥보다 직원당 매출이 높다

방법:
1. finance parquet 전종목 스캔 → 최신 연도 매출액 추출
2. 006 employee 결과에서 직원수 재사용
3. 직원당 매출 = 매출액 / 총직원수
4. listing 조인으로 업종별/시장별 분석

결과 (2025년 기준, 2,345종목):
- finance 매출 스캔: 2,743 parquets → 2,518종목 매출 추출
- employee 직원수: 2,477종목
- 매칭: 2,345종목 (직원당 매출 100만~100억 필터)
- 직원당 매출: 평균 4.2억, 중앙값 1.8억, Q1 0.9억, Q3 3.8억
- 구간 분포:
  | 0~1억: 677 (28.9%) | 1~2억: 575 (24.5%) | 2~3억: 312 (13.3%) |
  | 3~5억: 346 (14.8%) | 5~10억: 253 (10.8%) | 10~20억: 101 (4.3%) |
  | 20~50억: 58 (2.5%) | 50~100억: 23 (1.0%) |
- 시장별: 유가 중앙값 3.3억 > 코스닥 1.4억 (2.4배 차이)
- 업종별 높은 곳(중앙값): 경영컨설팅(47.9억), 기타금융(16.9억), 연료가스(15.7억)
- 업종별 낮은 곳(중앙값): R&D(0.4억), 기타과학기술(0.6억), 소프트웨어(0.7억)

결론:
- 가설1 기각: 중앙값 1.8억 (3~5억 예상보다 낮음). 코스닥 소기업이 다수
- 가설2 채택: 최고 경영컨설팅(47.9억) vs 최저 R&D(0.4억) = 120배 차이 (10배 초과)
- 가설3 채택: 유가 3.3억 vs 코스닥 1.4억 (유가가 2.4배 높음)
- R&D/바이오/소프트웨어가 직원당 매출 최하위 → 매출 전 단계 기업 많음
- 금융/에너지/해운이 최상위 → 자본/자산 집약적 비즈니스
- workforce scan에서 급여 대비 매출 효율(매출/급여 비율)까지 확장 가능

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


def _parse_won(s: str | None) -> float | None:
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
    quarters = df["quarter"].unique().to_list()
    best = sorted(quarters, key=lambda q: QUARTER_ORDER.get(q, 99))
    return df.filter(pl.col("quarter") == best[0]) if best else df


# ── finance 전수 스캔 (매출) ──────────────────────────────


REVENUE_ACCOUNT_IDS = {
    "Revenue", "Revenues", "revenue", "revenues",
    "ifrs-full_Revenue", "ifrs_Revenue",
    "dart_Revenue",
    "RevenueFromContractsWithCustomers",
    # 매출 관련 일반적 계정
}
REVENUE_ACCOUNT_NMS = {"매출액", "수익(매출액)", "영업수익", "매출", "순영업수익"}


def scan_revenue() -> dict[str, float]:
    """finance parquet 전종목 → 최신 연도 매출액(원)."""
    from dartlab.core.dataLoader import _dataDir

    finance_dir = Path(_dataDir("finance"))
    parquet_files = sorted(finance_dir.glob("*.parquet"))
    print(f"finance parquets: {len(parquet_files)}개")

    revenue_map: dict[str, float] = {}
    errors = 0

    for i, pf in enumerate(parquet_files):
        if i % 500 == 0:
            print(f"  {i}/{len(parquet_files)}...")
        code = pf.stem  # 종목코드

        try:
            df = pl.read_parquet(str(pf))
        except (pl.exceptions.ComputeError, OSError):
            errors += 1
            continue

        if df.is_empty() or "account_id" not in df.columns:
            continue

        # IS(손익계산서) 매출액 필터
        is_df = df.filter(
            (pl.col("sj_div").is_in(["IS", "CIS"]))
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
        )
        if is_df.is_empty():
            continue

        # 매출 계정 찾기
        rev_rows = is_df.filter(
            pl.col("account_id").is_in(list(REVENUE_ACCOUNT_IDS))
            | pl.col("account_nm").is_in(list(REVENUE_ACCOUNT_NMS))
        )
        if rev_rows.is_empty():
            # fallback: account_nm에 '매출' 포함
            rev_rows = is_df.filter(pl.col("account_nm").str.contains("매출"))
            if rev_rows.is_empty():
                continue

        # 최신 연도 (CFS 우선)
        # 연결재무제표 우선
        cfs = rev_rows.filter(pl.col("fs_nm").str.contains("연결"))
        target = cfs if not cfs.is_empty() else rev_rows

        # 최신 연도
        years = sorted(target["bsns_year"].unique().to_list(), reverse=True)
        if not years:
            continue

        latest = target.filter(pl.col("bsns_year") == years[0])
        # thstrm_amount (당기) 사용
        if "thstrm_amount" not in latest.columns:
            continue

        amounts = []
        for row in latest.iter_rows(named=True):
            val = row.get("thstrm_amount")
            if val is not None:
                parsed = _parse_won(str(val))
                if parsed and parsed > 0:
                    amounts.append(parsed)

        if amounts:
            revenue_map[code] = max(amounts)  # 가장 큰 매출 값 (연간 기준)

    print(f"매출 스캔 완료: {len(revenue_map)}종목 (에러: {errors})")
    return revenue_map


def scan_employee_count() -> dict[str, int]:
    """employee 전수 스캔 → 종목별 총직원수."""
    raw = _scan_parquets(
        "employee",
        ["stockCode", "year", "quarter", "sm", "jan_salary_am"],
    )
    if raw.is_empty():
        return {}

    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        ok = sub.filter(
            pl.col("jan_salary_am").is_not_null() & (pl.col("jan_salary_am") != "-")
        ).shape[0]
        if ok >= 500:
            latest_year = y
            break
    if latest_year is None:
        return {}

    latest = raw.filter(pl.col("year") == latest_year)
    emp_map: dict[str, int] = {}

    for code, group in latest.group_by("stockCode"):
        code_val = code[0]
        qdf = _pick_best_quarter(group)
        total = 0
        for row in qdf.iter_rows(named=True):
            emp = _parse_won(row.get("sm"))
            if emp and emp > 0:
                total += int(emp)
        if total > 0:
            emp_map[code_val] = total

    return emp_map


def compute_revenue_per_employee(
    revenue_map: dict[str, float],
    emp_map: dict[str, int],
) -> pl.DataFrame:
    """직원당 매출 계산."""
    rows = []
    for code in revenue_map:
        if code in emp_map and emp_map[code] > 0:
            rev = revenue_map[code]
            emp = emp_map[code]
            rpe = rev / emp  # 원/인
            rows.append({
                "종목코드": code,
                "매출_억원": round(rev / 100000000, 0),
                "직원수": emp,
                "직원당매출_만원": round(rpe / 10000, 0),
            })

    if not rows:
        return pl.DataFrame()

    df = pl.DataFrame(rows)
    # 이상치 필터: 직원당 매출 100만원 미만 또는 100억 이상 제외
    valid = df.filter(
        (pl.col("직원당매출_만원") >= 100) & (pl.col("직원당매출_만원") <= 1000000)
    )
    print(f"\n=== 직원당 매출 ({valid.shape[0]}종목) ===")
    rpe = valid["직원당매출_만원"].drop_nulls()
    print(f"평균: {rpe.mean():,.0f}만원")
    print(f"중앙값: {rpe.median():,.0f}만원")
    print(f"최소: {rpe.min():,.0f}만원")
    print(f"최대: {rpe.max():,.0f}만원")
    print(f"Q1: {rpe.quantile(0.25):,.0f}만원")
    print(f"Q3: {rpe.quantile(0.75):,.0f}만원")

    # 구간 분포 (억원 단위)
    bins_eok = [0, 1, 2, 3, 5, 10, 20, 50, 100]  # 억원
    bins = [b * 10000 for b in bins_eok]  # 만원 변환
    total = rpe.len()
    print(f"\n=== 직원당 매출 구간별 분포 (억원) ===")
    for i in range(len(bins) - 1):
        lo, hi = bins[i], bins[i + 1]
        cnt = rpe.filter((rpe >= lo) & (rpe < hi)).len()
        pct = cnt / total * 100
        bar = "█" * int(pct / 2)
        print(f"{bins_eok[i]:3d}~{bins_eok[i+1]:3d}억: {cnt:4d} ({pct:5.1f}%) {bar}")
    over = rpe.filter(rpe >= 1000000).len()
    if over:
        print(f"100억+: {over:4d}")

    return valid


def analyze_by_market(df: pl.DataFrame) -> None:
    """업종별/시장별 직원당 매출 분석."""
    from dartlab.engines.company.dart.scan.network.scanner import load_listing

    _, _, _, listing_meta = load_listing()

    rows = []
    for row in df.iter_rows(named=True):
        meta = listing_meta.get(row["종목코드"], {})
        if meta:
            rows.append({**row, "시장": meta.get("market", ""), "업종": meta.get("industry", "")})

    if not rows:
        return

    merged = pl.DataFrame(rows)

    # 시장별
    market_stats = (
        merged.group_by("시장")
        .agg([
            pl.col("직원당매출_만원").mean().alias("평균"),
            pl.col("직원당매출_만원").median().alias("중앙값"),
            pl.col("종목코드").count().alias("종목수"),
        ])
        .sort("평균", descending=True)
    )
    print(f"\n=== 시장별 직원당 매출 ===")
    print(market_stats)

    # 업종별 (5개 이상)
    industry_stats = (
        merged.group_by("업종")
        .agg([
            pl.col("직원당매출_만원").mean().alias("평균"),
            pl.col("직원당매출_만원").median().alias("중앙값"),
            pl.col("종목코드").count().alias("종목수"),
        ])
        .filter(pl.col("종목수") >= 5)
        .sort("중앙값", descending=True)
    )
    print(f"\n=== 직원당 매출 높은 업종 (중앙값) ===")
    print(industry_stats.head(10))
    print(f"\n=== 직원당 매출 낮은 업종 (중앙값) ===")
    print(industry_stats.tail(10))


if __name__ == "__main__":
    print("=" * 60)
    print("매출 스캔 (finance)...")
    revenue_map = scan_revenue()

    print("\n직원수 스캔 (employee)...")
    emp_map = scan_employee_count()
    print(f"직원수: {len(emp_map)}종목")

    df = compute_revenue_per_employee(revenue_map, emp_map)
    if not df.is_empty():
        analyze_by_market(df)
