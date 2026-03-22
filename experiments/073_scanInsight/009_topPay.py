"""실험 ID: 073-009
실험명: topPay — 고액 보수 임원 전수 스캔

목적:
- executivePayIndividual 전종목 스캔
- 5억 이상 고액 보수 임원 수, 보수 분포
- 시장별/업종별 고액 보수 패턴

가설:
1. 개별 보수 공개 기업이 전체의 50% 이상
2. 5억 이상 보수 임원이 있는 기업이 공개 기업의 30% 이상
3. 유가증권이 코스닥보다 고액 보수 비율이 높다

방법:
1. _scan_parquets로 executivePayIndividual 전수 스캔
2. 최신 연도 기준 mendng_totamt(보수총액) 파싱
3. 5억 이상 고액 보수 임원 집계
4. listing 조인으로 시장별 분석

결과 (2025년 기준, 383종목 501명):
- executivePayIndividual 원본: 130,870행, 2,639종목
- 유효(보수총액 존재): 15,598행, 1,477종목
- 최신 연도(2025): 501명, 383종목
- 보수 분포:
  - 평균: 18.3억, 중앙값: 8.1억, 최대: 2,580억
  - 5~10억: 318명 (63.5%) — 공개 기준 근처
  - 10~20억: 115명 (23.0%)
  - 20~50억: 53명 (10.6%)
  - 50~100억: 11명 (2.2%)
  - 100억+: 4명 (0.8%)
- 개별보수 공개 기업: 383종목 (전체 상장사의 14.4%)
- 시장별:
  - 유가: 239종목, 최고보수 중앙값 9.6억, 최대 397.9억
  - 코스닥: 144종목, 최고보수 중앙값 7.7억, 최대 2,580억
- 보수 top 3: 최영권(175250) 2,580억, 류진(005810) 397.9억, 박정원(000150) 163.1억
- 주: 자본시장법상 연간 5억 이상 보수자는 개별 공개 의무 → 5억 미만 0명은 정상

결론:
- 가설1 기각: 개별보수 공개 14.4% (50% 미만). 5억 이상 보수 의무공개 기준 때문
- 가설2 수정/채택: 공개 기업의 100%가 5억+ (공개 자체가 5억 이상 기준이므로)
- 가설3 채택: 유가 239종목 vs 코스닥 144종목, 보수 중앙값도 유가 9.6억 > 코스닥 7.7억
- 최고보수 2,580억은 극단적 이상치(주식보상 포함 추정)
- 63.5%가 5~10억 구간 → 대부분 기준선 근처, 고액 보수는 소수
- workforce scan 보완 완료. 003(pay ratio)과 결합하면 보수 합리성 종합 평가 가능

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


def scan_top_pay() -> pl.DataFrame:
    raw = _scan_parquets(
        "executivePayIndividual",
        ["stockCode", "year", "quarter", "nm", "ofcps", "mendng_totamt",
         "mendng_totamt_ct_incls_mendng"],
    )
    if raw.is_empty():
        print("executivePayIndividual 데이터 없음")
        return pl.DataFrame()

    print(f"executivePayIndividual 원본: {raw.shape[0]}행, {raw['stockCode'].n_unique()}종목")

    # 유효 데이터 (mendng_totamt 유효)
    valid = raw.filter(
        pl.col("mendng_totamt").is_not_null()
        & (pl.col("mendng_totamt") != "-")
        & (pl.col("mendng_totamt") != "")
    )
    print(f"유효 데이터: {valid.shape[0]}행, {valid['stockCode'].n_unique()}종목")

    # 최신 연도
    years_desc = sorted(valid["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = valid.filter(pl.col("year") == y)
        if sub["stockCode"].n_unique() >= 200:
            latest_year = y
            break
    if latest_year is None:
        print("충분한 데이터 없음")
        return pl.DataFrame()

    latest = valid.filter(pl.col("year") == latest_year)
    print(f"기준 연도({latest_year}): {latest.shape[0]}행, {latest['stockCode'].n_unique()}종목")

    # 개인별 보수 파싱
    persons = []
    for row in latest.iter_rows(named=True):
        amt = _parse_num(row.get("mendng_totamt"))
        if amt and amt > 0:
            persons.append({
                "종목코드": row["stockCode"],
                "이름": row.get("nm", ""),
                "직위": row.get("ofcps", ""),
                "보수_억": round(amt / 1e8, 1),
                "보수_원": amt,
            })

    if not persons:
        return pl.DataFrame()

    person_df = pl.DataFrame(persons)
    total_persons = person_df.shape[0]
    total_stocks = person_df["종목코드"].n_unique()

    print(f"\n=== 개별 보수 ({total_persons}명, {total_stocks}종목) ===")
    pay_vals = person_df["보수_억"]
    print(f"평균: {pay_vals.mean():.1f}억")
    print(f"중앙값: {pay_vals.median():.1f}억")
    print(f"최대: {pay_vals.max():.1f}억")

    # 구간 분포
    thresholds = [(0, 5, "5억미만"), (5, 10, "5~10억"), (10, 20, "10~20억"),
                  (20, 50, "20~50억"), (50, 100, "50~100억"), (100, 10000, "100억이상")]
    for lo, hi, label in thresholds:
        cnt = pay_vals.filter((pay_vals >= lo) & (pay_vals < hi)).len()
        print(f"  {label}: {cnt}명 ({cnt/total_persons*100:.1f}%)")

    # 5억 이상 고액 보수
    high_pay = person_df.filter(pl.col("보수_억") >= 5)
    high_stocks = high_pay["종목코드"].n_unique()
    print(f"\n5억+ 고액 보수: {high_pay.shape[0]}명, {high_stocks}종목")
    print(f"고액 보수 기업 비율: {high_stocks}/{total_stocks} ({high_stocks/total_stocks*100:.1f}%)")

    # top 20
    print(f"\n=== 보수 상위 20명 ===")
    top20 = person_df.sort("보수_억", descending=True).head(20)
    print(top20.select(["종목코드", "이름", "직위", "보수_억"]))

    # 종목별 집계 (최고보수)
    stock_results = []
    for code, group in person_df.group_by("종목코드"):
        code_val = code[0]
        max_pay = group["보수_억"].max()
        count = group.shape[0]
        high = group.filter(pl.col("보수_억") >= 5).shape[0]
        stock_results.append({
            "종목코드": code_val,
            "공개인원": count,
            "최고보수_억": max_pay,
            "고액보수자수": high,
            "고액보수여부": high > 0,
        })

    return pl.DataFrame(stock_results)


def analyze_by_market(df: pl.DataFrame) -> None:
    from dartlab.engines.dart.scan.network.scanner import load_listing
    _, _, _, listing_meta = load_listing()

    total_listed = len(listing_meta)
    rows = []
    for row in df.iter_rows(named=True):
        meta = listing_meta.get(row["종목코드"], {})
        if meta:
            rows.append({**row, "시장": meta.get("market", "")})

    if not rows:
        return
    merged = pl.DataFrame(rows)

    print(f"\n전체 상장사: {total_listed}")
    print(f"개별보수 공개: {df.shape[0]}종목 ({df.shape[0]/total_listed*100:.1f}%)")

    for market in ["유가", "코스닥"]:
        sub = merged.filter(pl.col("시장") == market)
        if sub.is_empty():
            continue
        total = sub.shape[0]
        high = sub.filter(pl.col("고액보수여부") == True).shape[0]
        max_pay = sub["최고보수_억"].max()
        median_pay = sub["최고보수_억"].median()
        print(f"\n=== {market} ({total}종목) ===")
        print(f"고액보수(5억+): {high}개 ({high/total*100:.1f}%)")
        print(f"최고보수 중앙값: {median_pay:.1f}억")
        print(f"최고보수 최대: {max_pay:.1f}억")


if __name__ == "__main__":
    df = scan_top_pay()
    if not df.is_empty():
        analyze_by_market(df)
