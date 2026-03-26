"""실험 ID: 073-006
실험명: employee 전수 스캔 — 업종별 급여 분포 + 인력 구조

목적:
- employee를 전종목 스캔
- 업종별 평균급여 분포, 남녀 급여 격차, 근속연수 분포
- workforce 인사이트의 기초 데이터

가설:
1. 업종별 평균급여 차이가 2배 이상 (최고 업종 vs 최저 업종)
2. 남녀 평균급여 격차가 20% 이상
3. 평균 근속연수가 10년 이상인 업종이 5개 이상

방법:
1. _scan_parquets로 employee 전수 스캔
2. 최신 연도 + 최적 분기(Q2) 기준
3. 종목별 남/여/전체 직원수, 평균급여(연), 근속연수 집계
4. listing 조인으로 업종별 분석

결과 (2025년 기준, 2,639종목):
- employee 원본: 300,371행, 2,641종목 → 2,421 유효 (급여 100만원 이상)
- 평균급여: 평균 5,752만원, 중앙값 3,026만원, 최대 30.8억원(이상치)
- 남녀 격차(2,406종목): 남 6,149만원 vs 여 4,577만원 → 격차 25.6%
- 평균근속: 평균 7.2년, 중앙값 6.2년, 10년 이상 503종목
- 업종별 급여(중앙값 기준):
  - 높은 업종: 석유정제(7,417), 신탁(7,402), 금융지원(7,173), 보험(5,523)
  - 낮은 업종: 일반교습(2,412), 도축(2,358), 무점포소매(2,717)
- 근속 높은 업종: 연료가스(18.0년), 석유정제(15.3), 보험(14.2), 펄프(13.2)
- 시장별: 유가 중앙값 3,621만원(근속 10.0년) > 코스닥 2,863만원(5.8년)

결론:
- 가설1 채택: 최고 석유정제(7,417) vs 최저 도축(2,358) = 3.1배 차이 (2배 이상)
- 가설2 채택: 남녀 급여 격차 25.6% (20% 이상)
- 가설3 채택: 근속 10년 이상 업종 10개+ (연료가스, 석유정제, 보험, 펄프, TV방송 등)
- 주의: 상품중개업 평균급여 34.6억은 증권사 자기매매 수익 포함 이상치 → 중앙값 사용 권장
- 유가증권이 코스닥보다 급여/근속 모두 높음 (대기업 효과)
- workforce scan의 기초 데이터로 충분. 매출/이익 결합 시 인력 효율성 인사이트 가능

실험일: 2026-03-19
"""

from __future__ import annotations

import re
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


def _parse_tenure(s: str | None) -> float | None:
    """근속연수 문자열 → 년(float). '12년9개월' → 12.75"""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip()
    if s in ("", "-"):
        return None
    m = re.match(r"(\d+)년\s*(\d+)?개?월?", s)
    if m:
        years = int(m.group(1))
        months = int(m.group(2)) if m.group(2) else 0
        return years + months / 12
    try:
        return float(s)
    except ValueError:
        return None


QUARTER_ORDER = {"2분기": 1, "4분기": 2, "3분기": 3, "1분기": 4}


def _pick_best_quarter(df: pl.DataFrame) -> pl.DataFrame:
    quarters = df["quarter"].unique().to_list()
    best = sorted(quarters, key=lambda q: QUARTER_ORDER.get(q, 99))
    return df.filter(pl.col("quarter") == best[0]) if best else df


def scan_employee() -> pl.DataFrame:
    """employee 전수 스캔 → 종목별 인력 현황."""
    raw = _scan_parquets(
        "employee",
        ["stockCode", "year", "quarter", "sexdstn", "sm",
         "jan_salary_am", "fyer_salary_totamt", "avrg_cnwk_sdytrn",
         "rgllbr_co", "cnttk_co"],
    )
    if raw.is_empty():
        print("employee 데이터 없음")
        return pl.DataFrame()

    print(f"employee 원본: {raw.shape[0]}행, {raw['stockCode'].n_unique()}종목")

    # 최신 연도
    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        ok = sub.filter(
            pl.col("jan_salary_am").is_not_null()
            & (pl.col("jan_salary_am") != "-")
        ).shape[0]
        if ok >= 500:
            latest_year = y
            break
    if latest_year is None:
        print("충분한 데이터 없음")
        return pl.DataFrame()

    latest = raw.filter(pl.col("year") == latest_year)
    print(f"기준 연도({latest_year}): {latest.shape[0]}행, {latest['stockCode'].n_unique()}종목")

    results = []
    for code, group in latest.group_by("stockCode"):
        code_val = code[0]
        qdf = _pick_best_quarter(group)

        # 전체 가중평균
        total_emp, total_sal_wsum = 0, 0.0
        male_emp, male_sal_wsum = 0, 0.0
        female_emp, female_sal_wsum = 0, 0.0
        tenure_wsum, tenure_cnt = 0.0, 0

        for row in qdf.iter_rows(named=True):
            sex = row.get("sexdstn")
            emp = _parse_won(row.get("sm"))
            sal = _parse_won(row.get("jan_salary_am"))
            tenure = _parse_tenure(row.get("avrg_cnwk_sdytrn"))

            if emp and emp > 0 and sal and sal > 0:
                total_emp += int(emp)
                total_sal_wsum += emp * sal
                if sex == "남":
                    male_emp += int(emp)
                    male_sal_wsum += emp * sal
                elif sex == "여":
                    female_emp += int(emp)
                    female_sal_wsum += emp * sal

            if emp and emp > 0 and tenure and tenure > 0:
                tenure_wsum += emp * tenure
                tenure_cnt += int(emp)

        avg_sal = total_sal_wsum / total_emp / 10000 if total_emp > 0 else None  # 만원/연
        male_avg = male_sal_wsum / male_emp / 10000 if male_emp > 0 else None
        female_avg = female_sal_wsum / female_emp / 10000 if female_emp > 0 else None
        avg_tenure = tenure_wsum / tenure_cnt if tenure_cnt > 0 else None

        results.append({
            "종목코드": code_val,
            "총직원수": total_emp if total_emp > 0 else None,
            "남직원수": male_emp if male_emp > 0 else None,
            "여직원수": female_emp if female_emp > 0 else None,
            "평균급여_만원": round(avg_sal, 0) if avg_sal else None,
            "남평균급여_만원": round(male_avg, 0) if male_avg else None,
            "여평균급여_만원": round(female_avg, 0) if female_avg else None,
            "평균근속_년": round(avg_tenure, 1) if avg_tenure else None,
        })

    df = pl.DataFrame(results)
    valid = df.filter(pl.col("평균급여_만원").is_not_null() & (pl.col("평균급여_만원") > 100))
    print(f"직원현황 집계: {df.shape[0]}종목 (유효: {valid.shape[0]})")

    # 전체 분포
    sals = valid["평균급여_만원"].drop_nulls()
    print(f"\n=== 평균급여 분포 (만원/연) ===")
    print(f"평균: {sals.mean():,.0f}")
    print(f"중앙값: {sals.median():,.0f}")
    print(f"최소: {sals.min():,.0f}")
    print(f"최대: {sals.max():,.0f}")

    # 남녀 격차
    both = valid.filter(
        pl.col("남평균급여_만원").is_not_null() & pl.col("여평균급여_만원").is_not_null()
        & (pl.col("남평균급여_만원") > 100) & (pl.col("여평균급여_만원") > 100)
    )
    if not both.is_empty():
        m_avg = both["남평균급여_만원"].mean()
        f_avg = both["여평균급여_만원"].mean()
        gap_pct = (m_avg - f_avg) / m_avg * 100
        print(f"\n=== 남녀 급여 격차 ({both.shape[0]}종목) ===")
        print(f"남 평균: {m_avg:,.0f}만원, 여 평균: {f_avg:,.0f}만원")
        print(f"격차: {gap_pct:.1f}% (남 대비 여 낮음)")

    # 근속연수
    tenures = valid.filter(pl.col("평균근속_년").is_not_null())["평균근속_년"].drop_nulls()
    if tenures.len() > 0:
        print(f"\n=== 평균근속연수 분포 (년) ===")
        print(f"평균: {tenures.mean():.1f}")
        print(f"중앙값: {tenures.median():.1f}")
        print(f"10년 이상: {tenures.filter(tenures >= 10).len()}종목")

    return df


def analyze_by_industry(df: pl.DataFrame) -> None:
    """업종별 급여/인력 분석."""
    from dartlab.market.network.scanner import load_listing

    _, _, _, listing_meta = load_listing()

    rows = []
    for row in df.iter_rows(named=True):
        meta = listing_meta.get(row["종목코드"], {})
        if meta:
            rows.append({**row, "시장": meta.get("market", ""), "업종": meta.get("industry", "")})

    if not rows:
        return

    merged = pl.DataFrame(rows).filter(
        pl.col("평균급여_만원").is_not_null() & (pl.col("평균급여_만원") > 100)
    )

    # 업종별 (5개 이상)
    industry_stats = (
        merged.group_by("업종")
        .agg([
            pl.col("평균급여_만원").mean().alias("평균급여"),
            pl.col("평균급여_만원").median().alias("중앙값급여"),
            pl.col("총직원수").sum().alias("총인원"),
            pl.col("평균근속_년").mean().alias("평균근속"),
            pl.col("종목코드").count().alias("종목수"),
        ])
        .filter(pl.col("종목수") >= 5)
        .sort("평균급여", descending=True)
    )
    print(f"\n=== 급여 높은 업종 ===")
    print(industry_stats.head(10))
    print(f"\n=== 급여 낮은 업종 ===")
    print(industry_stats.tail(10))

    # 근속 높은 업종
    tenure_stats = industry_stats.filter(pl.col("평균근속").is_not_null()).sort("평균근속", descending=True)
    print(f"\n=== 근속연수 높은 업종 ===")
    print(tenure_stats.head(10))

    # 시장별
    market_stats = (
        merged.group_by("시장")
        .agg([
            pl.col("평균급여_만원").mean().alias("평균급여"),
            pl.col("평균급여_만원").median().alias("중앙값급여"),
            pl.col("평균근속_년").mean().alias("평균근속"),
            pl.col("종목코드").count().alias("종목수"),
        ])
        .sort("평균급여", descending=True)
    )
    print(f"\n=== 시장별 급여 ===")
    print(market_stats)


if __name__ == "__main__":
    df = scan_employee()
    if not df.is_empty():
        analyze_by_industry(df)
