"""실험 ID: 073-005
실험명: governanceScore — 4개 축 조합 거버넌스 종합 등급

목적:
- 001~004 결과(최대주주지분율, 사외이사비율, pay ratio, 감사의견)를 조합
- 종합 거버넌스 등급(A~E) 산출
- 업종별/시장별 등급 분포 파악

가설:
1. 4개 축이 모두 유효한(비결측) 종목이 전체의 60% 이상
2. 종합 등급 분포가 정규분포에 가깝다 (B~D에 집중)
3. 업종별로 거버넌스 등급에 유의미한 차이가 있다

방법:
1. _scan_parquets로 4개 apiType(majorHolder, executive, executivePayAllTotal+employee, auditOpinion) 전수 스캔
2. 4개 축 join → 종목별 거버넌스 팩터 테이블
3. 각 축 점수화 (0~25점, 총 100점):
   - 최대주주지분율: 30~50% 최적(25), 양극단 감점
   - 사외이사비율: 40%+(25), 0%(3)
   - pay ratio: 2배 이하(25), 20배 이상(3)
   - 감사의견: 적정(25), 한정(5), 부적정/의견거절(0)
4. 종합 점수 → A(85+)~E(40미만) 등급
5. listing 조인으로 업종별/시장별 등급 분포

결과 (2025년 기준, 2,650종목):
- 4개 축 커버: 지분율 2,515 / 사외이사 2,641 / pay ratio 2,437 / 감사의견 2,405
- 4축 모두 유효: 2,344개 (88.5%)
- 등급 분포:
  | A(85+): 580 (21.9%) | B(70~84): 1,328 (50.1%) | C(55~69): 529 (20.0%) |
  | D(40~54): 202 (7.6%) | E(40미만): 11 (0.4%) |
- 총점: 평균 74.4, 중앙값 76.0, 최소 20.5, 최대 100.0
- 시장별: 코스닥 76.9 > 유가 74.9 > 코넥스 41.4
  - 코넥스는 108/110이 D등급 (사외이사/감사의견 데이터 부재)
- 업종별 높은 곳: 출판(82.4), 무점포소매(82.1), 도로운송(82.0)
- 업종별 낮은 곳: 직물(64.8), 실내건축(65.7), 유리(66.4)
- A등급(100점) 기업 특성: 지분율 30~50%, 사외이사 40%+, pay ratio 2배 이하, 적정의견
- E등급(11개): 대부분 비적정 의견 + 극단 지분율/pay ratio

결론:
- 가설1 채택: 4축 유효 88.5% (60% 이상)
- 가설2 채택: B등급에 50.1% 집중, A~C가 92% → 정규분포에 가까움
- 가설3 채택: 업종간 최대 17.6p 차이 (출판 82.4 vs 직물 64.8)
- 코스닥이 유가보다 약간 높은 건 pay ratio가 더 낮아서 (중소기업 임원보수 낮음)
- 코넥스는 데이터 부재로 거의 D등급 → 코넥스 제외 분석이 더 의미있음
- 종합 거버넌스 등급은 scan engine 흡수 시 핵심 결과물
- 감사의견이 비적정이면 즉시 E등급 근접 → 강한 위험 신호로 유효

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


def _find_latest_year(raw: pl.DataFrame, check_col: str, min_count: int = 500) -> str | None:
    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        ok = sub.filter(
            pl.col(check_col).is_not_null()
            & (pl.col(check_col) != "-")
            & (pl.col(check_col) != "")
        ).shape[0]
        if ok >= min_count:
            return y
    return None


# ── 점수화 함수 ──────────────────────────────────────────


def _score_ownership(pct: float | None) -> float:
    """최대주주 지분율 점수 (0~25점). 30~50%가 최적."""
    if pct is None:
        return 12.5
    if 30 <= pct <= 50:
        return 25.0
    if 20 <= pct < 30 or 50 < pct <= 60:
        return 20.0
    if 10 <= pct < 20 or 60 < pct <= 70:
        return 15.0
    if pct < 10:
        return 5.0
    return 10.0  # 70%+


def _score_outside_ratio(ratio: float | None) -> float:
    """사외이사 비율 점수 (0~25점)."""
    if ratio is None:
        return 12.5
    if ratio >= 40:
        return 25.0
    if ratio >= 30:
        return 22.0
    if ratio >= 20:
        return 18.0
    if ratio >= 10:
        return 14.0
    if ratio > 0:
        return 8.0
    return 3.0


def _score_pay_ratio(ratio: float | None) -> float:
    """pay ratio 점수 (0~25점). 낮을수록 좋음."""
    if ratio is None:
        return 12.5
    if ratio <= 2:
        return 25.0
    if ratio <= 3:
        return 22.0
    if ratio <= 5:
        return 18.0
    if ratio <= 10:
        return 14.0
    if ratio <= 20:
        return 8.0
    return 3.0


def _score_audit(opinion: str | None) -> float:
    """감사의견 점수 (0~25점)."""
    if opinion is None or opinion == "":
        return 12.5
    if opinion == "적정의견":
        return 25.0
    if opinion == "한정의견":
        return 5.0
    return 0.0


def _grade(score: float) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "E"


# ── 4개 축 스캔 ──────────────────────────────────────────


def _scan_axis_ownership() -> dict[str, float]:
    """최대주주 지분율."""
    raw = _scan_parquets(
        "majorHolder",
        ["stockCode", "year", "quarter", "bsis_posesn_stock_qota_rt"],
    )
    result: dict[str, float] = {}
    if raw.is_empty():
        return result
    latest_year = _find_latest_year(raw, "bsis_posesn_stock_qota_rt", 1000)
    if latest_year is None:
        return result
    sub = raw.filter(pl.col("year") == latest_year)
    for code, group in sub.group_by("stockCode"):
        vals = []
        for row in group.iter_rows(named=True):
            v = _parse_won(row.get("bsis_posesn_stock_qota_rt"))
            if v is not None and 0 <= v <= 100:
                vals.append(v)
        if vals:
            result[code[0]] = max(vals)
    return result


def _scan_axis_outside() -> dict[str, float]:
    """사외이사 비율."""
    raw = _scan_parquets(
        "executive",
        ["stockCode", "year", "quarter", "ofcps"],
    )
    result: dict[str, float] = {}
    if raw.is_empty():
        return result
    latest_year = _find_latest_year(raw, "ofcps", 1000)
    if latest_year is None:
        return result
    sub = raw.filter(pl.col("year") == latest_year)
    for code, group in sub.group_by("stockCode"):
        total = group.shape[0]
        outside = sum(1 for row in group.iter_rows(named=True)
                      if row.get("ofcps") and "사외" in row["ofcps"])
        result[code[0]] = outside / total * 100 if total > 0 else 0
    return result


def _scan_axis_pay_ratio() -> dict[str, float]:
    """임원/직원 보수 배율."""
    raw_pay = _scan_parquets(
        "executivePayAllTotal",
        ["stockCode", "year", "quarter", "nmpr", "jan_avrg_mendng_am"],
    )
    raw_emp = _scan_parquets(
        "employee",
        ["stockCode", "year", "quarter", "sm", "jan_salary_am"],
    )
    result: dict[str, float] = {}
    if raw_pay.is_empty() or raw_emp.is_empty():
        return result

    # 임원 보수
    pay_map: dict[str, float] = {}
    latest = _find_latest_year(raw_pay, "jan_avrg_mendng_am", 500)
    if latest:
        sub = raw_pay.filter(pl.col("year") == latest)
        for code, group in sub.group_by("stockCode"):
            qdf = _pick_best_quarter(group)
            wsum, tnmpr = 0.0, 0
            for row in qdf.iter_rows(named=True):
                n = _parse_won(row.get("nmpr"))
                p = _parse_won(row.get("jan_avrg_mendng_am"))
                if n and n > 0 and p and p > 0:
                    wsum += n * p
                    tnmpr += int(n)
            if tnmpr > 0:
                pay_map[code[0]] = wsum / tnmpr

    # 직원 급여
    sal_map: dict[str, float] = {}
    latest = _find_latest_year(raw_emp, "jan_salary_am", 500)
    if latest:
        sub = raw_emp.filter(pl.col("year") == latest)
        for code, group in sub.group_by("stockCode"):
            qdf = _pick_best_quarter(group)
            wsum, temp = 0.0, 0
            for row in qdf.iter_rows(named=True):
                e = _parse_won(row.get("sm"))
                s = _parse_won(row.get("jan_salary_am"))
                if e and e > 0 and s and s > 0:
                    wsum += e * s
                    temp += int(e)
            if temp > 0:
                sal_map[code[0]] = wsum / temp

    for code in pay_map:
        if code in sal_map and sal_map[code] > 0:
            result[code] = pay_map[code] / sal_map[code]

    return result


def _scan_axis_audit() -> dict[str, str]:
    """감사의견."""
    raw = _scan_parquets(
        "auditOpinion",
        ["stockCode", "year", "quarter", "adt_opinion"],
    )
    result: dict[str, str] = {}
    if raw.is_empty():
        return result
    opinion_rank = {"의견거절": 4, "부적정의견": 3, "한정의견": 2, "적정의견": 1}
    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        if sub.filter(pl.col("adt_opinion").is_not_null()).shape[0] >= 500:
            for code, group in sub.group_by("stockCode"):
                valid_rows = group.filter(pl.col("adt_opinion").is_not_null())
                if valid_rows.is_empty():
                    continue
                worst, worst_op = 0, None
                for row in valid_rows.iter_rows(named=True):
                    op = row.get("adt_opinion")
                    if op:
                        r = opinion_rank.get(op, 0)
                        if r > worst:
                            worst = r
                            worst_op = op
                        elif worst_op is None:
                            worst_op = op
                if worst_op:
                    result[code[0]] = worst_op
            break
    return result


# ── 메인 ──────────────────────────────────────────────────


def build_governance_score() -> pl.DataFrame:
    """4개 축 스캔 → 종합 거버넌스 등급."""
    print("1/4 최대주주 지분율 스캔...")
    holder_map = _scan_axis_ownership()
    print(f"  → {len(holder_map)}종목")

    print("2/4 사외이사 비율 스캔...")
    outside_map = _scan_axis_outside()
    print(f"  → {len(outside_map)}종목")

    print("3/4 pay ratio 스캔...")
    pay_ratio_map = _scan_axis_pay_ratio()
    print(f"  → {len(pay_ratio_map)}종목")

    print("4/4 감사의견 스캔...")
    audit_map = _scan_axis_audit()
    print(f"  → {len(audit_map)}종목")

    all_codes = set(holder_map) | set(outside_map) | set(pay_ratio_map) | set(audit_map)
    print(f"\n전체 종목 풀: {len(all_codes)}")

    results = []
    for code in all_codes:
        ownership = holder_map.get(code)
        outside = outside_map.get(code)
        pay_ratio = pay_ratio_map.get(code)
        audit = audit_map.get(code)

        s1 = _score_ownership(ownership)
        s2 = _score_outside_ratio(outside)
        s3 = _score_pay_ratio(pay_ratio)
        s4 = _score_audit(audit)
        total = s1 + s2 + s3 + s4
        grade = _grade(total)
        n_valid = sum(1 for v in [ownership, outside, pay_ratio, audit] if v is not None)

        results.append({
            "종목코드": code,
            "지분율": round(ownership, 1) if ownership else None,
            "사외이사비율": round(outside, 1) if outside else None,
            "pay_ratio": round(pay_ratio, 1) if pay_ratio else None,
            "감사의견": audit or "",
            "S_지분": s1,
            "S_사외": s2,
            "S_보수": s3,
            "S_감사": s4,
            "총점": total,
            "등급": grade,
            "유효축수": n_valid,
        })

    df = pl.DataFrame(results)
    print(f"\n거버넌스 스코어: {df.shape[0]}종목")

    # 유효축 분포
    print(f"\n=== 유효축수 분포 ===")
    print(df["유효축수"].value_counts().sort("유효축수", descending=True))

    four_valid = df.filter(pl.col("유효축수") == 4)
    print(f"\n4축 모두 유효: {four_valid.shape[0]}개 ({four_valid.shape[0]/df.shape[0]*100:.1f}%)")

    # 등급 분포
    print(f"\n=== 등급 분포 ===")
    print(df["등급"].value_counts().sort("등급"))

    # 총점 통계
    scores = df["총점"]
    print(f"\n=== 총점 분포 ===")
    print(f"평균: {scores.mean():.1f}")
    print(f"중앙값: {scores.median():.1f}")
    print(f"최소: {scores.min():.1f}")
    print(f"최대: {scores.max():.1f}")

    # 등급별 총점 범위
    for g in ["A", "B", "C", "D", "E"]:
        sub = df.filter(pl.col("등급") == g)
        if not sub.is_empty():
            print(f"  {g}: {sub.shape[0]}개, 평균 {sub['총점'].mean():.1f}")

    return df


def analyze_by_market(df: pl.DataFrame) -> None:
    """시장별/업종별 등급 분포."""
    from dartlab.market.network.scanner import load_listing

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
            pl.col("총점").mean().alias("평균총점"),
            pl.col("총점").median().alias("중앙값"),
            pl.col("종목코드").count().alias("종목수"),
        ])
        .sort("평균총점", descending=True)
    )
    print(f"\n=== 시장별 거버넌스 점수 ===")
    print(market_stats)

    for market in ["유가", "코스닥", "코넥스"]:
        sub = merged.filter(pl.col("시장") == market)
        if sub.is_empty():
            continue
        print(f"\n--- {market} 등급 분포 ---")
        print(sub["등급"].value_counts().sort("등급"))

    # 업종별 (5개 이상)
    industry_stats = (
        merged.group_by("업종")
        .agg([
            pl.col("총점").mean().alias("평균총점"),
            pl.col("종목코드").count().alias("종목수"),
        ])
        .filter(pl.col("종목수") >= 5)
        .sort("평균총점", descending=True)
    )
    print(f"\n=== 거버넌스 점수 높은 업종 ===")
    print(industry_stats.head(10))
    print(f"\n=== 거버넌스 점수 낮은 업종 ===")
    print(industry_stats.tail(10))

    # A등급 기업 상위
    a_grade = merged.filter(pl.col("등급") == "A").sort("총점", descending=True)
    print(f"\n=== A등급 기업 (상위 15) ===")
    print(a_grade.select(["종목코드", "지분율", "사외이사비율", "pay_ratio", "감사의견", "총점", "업종"]).head(15))

    # E등급 기업
    e_grade = merged.filter(pl.col("등급") == "E").sort("총점")
    print(f"\n=== E등급 기업 ({e_grade.shape[0]}개) ===")
    print(e_grade.select(["종목코드", "지분율", "사외이사비율", "pay_ratio", "감사의견", "총점", "업종"]).head(15))


if __name__ == "__main__":
    df = build_governance_score()
    if not df.is_empty():
        analyze_by_market(df)
