"""실험 ID: 073-016
실험명: maturityRisk — 만기 집중도 + 이자보상배율 교차 위험

목적:
- 014 bondScan(단기비중) + finance IS(이자보상배율) 교차
- "단기만기 집중 + 이자보상배율 낮음" = 차환 위험 기업 식별
- 시장별 위험 기업 분포

가설:
1. 이자보상배율 1배 미만(이자비용>영업이익) 기업이 전체의 20% 이상
2. 단기집중(단기비중50%+) + 이자보상배율 1배 미만 = 고위험 기업이 사채발행 기업의 10% 이상
3. 코스닥이 유가보다 고위험 기업 비율이 높다

방법:
1. 014 corporateBond 단기비중 재활용
2. finance IS에서 영업이익, 이자비용 추출 → 이자보상배율 계산
3. 교차: 단기비중 × 이자보상배율 → 위험 등급 분류
4. listing 조인으로 시장별 분석

결과 (2,523종목 이자보상배율 + 783종목 사채교차):
- 이자보상배율 전체 (2,523종목):
  - 평균: 1.0배, 중앙값: 0.8배
  - 1배 미만: 1,327개 (52.6%)
  - 0배 미만 (영업손실): 971개 (38.5%)
- 사채발행 + 이자보상배율 교차 (783종목):
  - 고위험 (단기50%+ & ICR<1): 142개 (18.1%)
  - 주의 (단기50%+ 또는 ICR<1): 418개 (53.4%)
  - 관찰 (ICR<3): 119개 (15.2%)
  - 안전 (ICR≥3): 104개 (13.3%)
- 시장별:
  - 유가: 고위험 16.9%, 주의 43.7%, 안전+관찰 39.4%
  - 코스닥: 고위험 19.3%, 주의 61.3%, 안전+관찰 19.3%
- 고위험 worst 10: ICR -37.95~-8.28, 단기비중 56~100%

결론:
- 가설1 채택: ICR 1배 미만 52.6% (20% 이상, 예상보다 훨씬 높음). 전체 상장사 절반이 이자비용>영업이익
- 가설2 채택: 고위험(단기50%+ICR<1) 142개 = 사채발행 기업의 18.1% (10% 이상)
- 가설3 채택: 코스닥 고위험 19.3% vs 유가 16.9%. 코스닥이 약간 높음
- 사채 발행 기업 중 "안전"은 13.3%에 불과 — 대부분 주의 이상
- 코스닥은 안전+관찰이 19.3%뿐 → 사채 발행 코스닥 기업의 80.7%가 주의 이상
- ICR 0 미만(영업손실) 기업이 38.5% → 한국 상장사 수익성 양극화 심각
- debt축 3개 실험 완료. 종합: 사채 발행 기업 30%, 대부분 위험 수준, 코스닥이 더 취약

실험일: 2026-03-19
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


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


# ── IS 이자보상배율 스캔 ──

OP_IDS = {"ProfitLossFromOperatingActivities", "profitLossFromOperatingActivities",
           "ifrs-full_ProfitLossFromOperatingActivities", "dart_OperatingIncomeLoss"}
OP_NMS = {"영업이익", "영업이익(손실)"}
INTEREST_IDS = {"FinanceCosts", "financeCosts", "ifrs-full_FinanceCosts", "InterestExpense"}
INTEREST_NMS = {"이자비용", "금융비용", "금융원가"}


def scan_interest_coverage() -> dict[str, float]:
    """finance IS → 이자보상배율 = 영업이익 / 이자비용."""
    from dartlab.core.dataLoader import _dataDir

    finance_dir = Path(_dataDir("finance"))
    parquet_files = sorted(finance_dir.glob("*.parquet"))
    print(f"finance parquets: {len(parquet_files)}개")

    result: dict[str, float] = {}
    errors = 0

    for i, pf in enumerate(parquet_files):
        if i % 500 == 0:
            print(f"  {i}/{len(parquet_files)}...")
        code = pf.stem

        try:
            df = pl.read_parquet(str(pf))
        except (pl.exceptions.ComputeError, OSError):
            errors += 1
            continue

        if df.is_empty() or "account_id" not in df.columns:
            continue

        # IS/CIS
        is_df = df.filter(
            pl.col("sj_div").is_in(["IS", "CIS"])
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
        )
        if is_df.is_empty():
            continue

        cfs = is_df.filter(pl.col("fs_nm").str.contains("연결"))
        target = cfs if not cfs.is_empty() else is_df

        years = sorted(target["bsns_year"].unique().to_list(), reverse=True)
        if not years:
            continue
        latest = target.filter(pl.col("bsns_year") == years[0])

        op_income = None
        interest_exp = None

        for row in latest.iter_rows(named=True):
            aid = row.get("account_id", "")
            anm = row.get("account_nm", "")
            val = _parse_num(row.get("thstrm_amount"))

            if (aid in OP_IDS or anm in OP_NMS) and val is not None:
                if op_income is None:
                    op_income = val
            elif (aid in INTEREST_IDS or anm in INTEREST_NMS) and val is not None:
                if interest_exp is None:
                    interest_exp = abs(val)  # 이자비용은 보통 양수이나 음수일 수도

        if op_income is not None and interest_exp and interest_exp > 0:
            result[code] = op_income / interest_exp

    print(f"이자보상배율 스캔 완료: {len(result)}종목 (에러: {errors})")
    return result


# ── corporateBond 단기비중 ──

def scan_bond_short_ratio() -> dict[str, float]:
    """corporateBond → 종목별 단기(1년이내) 비중(%)."""
    raw = _scan_parquets(
        "corporateBond",
        ["stockCode", "year", "quarter", "remndr_exprtn2", "sm", "yy1_below"],
    )
    if raw.is_empty():
        return {}

    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        ok = sub.filter(pl.col("sm").is_not_null() & (pl.col("sm") != "-")).shape[0]
        if ok >= 200:
            latest_year = y
            break
    if latest_year is None:
        return {}

    latest = raw.filter(pl.col("year") == latest_year)
    totals = latest.filter(pl.col("remndr_exprtn2") == "합계")
    if totals.is_empty() or totals["stockCode"].n_unique() < 50:
        totals = latest

    result = {}
    for code, group in totals.group_by("stockCode"):
        code_val = code[0]
        total_sm = 0
        short_1y = 0
        for row in group.iter_rows(named=True):
            sm = _parse_num(row.get("sm"))
            y1 = _parse_num(row.get("yy1_below"))
            if sm and sm > 0:
                total_sm = max(total_sm, sm)
            if y1 and y1 > 0:
                short_1y = max(short_1y, y1)
        if total_sm > 0:
            result[code_val] = round(short_1y / total_sm * 100, 1)
    return result


def compute_maturity_risk() -> pl.DataFrame:
    print("이자보상배율 스캔 (finance IS)...")
    icr_map = scan_interest_coverage()

    print("\n단기비중 스캔 (corporateBond)...")
    short_map = scan_bond_short_ratio()
    print(f"  사채 발행: {len(short_map)}종목")

    # 이자보상배율 전체 분포
    icr_vals = list(icr_map.values())
    if icr_vals:
        import statistics
        # 이상치 제거 (|-100| ~ |100|)
        bounded = [v for v in icr_vals if -100 <= v <= 100]
        print(f"\n=== 이자보상배율 전체 ({len(icr_map)}종목, 이상치 제거 {len(bounded)}) ===")
        print(f"평균: {statistics.mean(bounded):.1f}배")
        print(f"중앙값: {statistics.median(bounded):.1f}배")

        under1 = sum(1 for v in icr_vals if v < 1)
        under0 = sum(1 for v in icr_vals if v < 0)
        print(f"1배 미만: {under1}개 ({under1/len(icr_vals)*100:.1f}%)")
        print(f"0배 미만 (영업손실): {under0}개 ({under0/len(icr_vals)*100:.1f}%)")

    # 교차: 사채 발행 + 이자보상배율
    rows = []
    for code in short_map:
        short_ratio = short_map[code]
        icr = icr_map.get(code)
        if icr is None:
            continue

        # 위험 등급
        if short_ratio >= 50 and icr < 1:
            risk = "고위험"
        elif short_ratio >= 50 or icr < 1:
            risk = "주의"
        elif icr < 3:
            risk = "관찰"
        else:
            risk = "안전"

        rows.append({
            "종목코드": code,
            "단기비중": short_ratio,
            "이자보상배율": round(icr, 2),
            "위험등급": risk,
        })

    df = pl.DataFrame(rows)
    total = df.shape[0]
    print(f"\n=== 사채발행 + 이자보상배율 매칭: {total}종목 ===")

    for grade in ["고위험", "주의", "관찰", "안전"]:
        cnt = df.filter(pl.col("위험등급") == grade).shape[0]
        print(f"{grade}: {cnt}개 ({cnt/total*100:.1f}%)")

    # 고위험 상세
    high_risk = df.filter(pl.col("위험등급") == "고위험")
    if not high_risk.is_empty():
        print(f"\n=== 고위험 기업 (단기50%+ & ICR<1) {high_risk.shape[0]}개 ===")
        worst = high_risk.sort("이자보상배율").head(10)
        print(worst.select(["종목코드", "단기비중", "이자보상배율"]))

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
        high = sub.filter(pl.col("위험등급") == "고위험").shape[0]
        warn = sub.filter(pl.col("위험등급") == "주의").shape[0]
        print(f"\n=== {market} ({total}종목) ===")
        print(f"고위험: {high}개 ({high/total*100:.1f}%)")
        print(f"주의: {warn}개 ({warn/total*100:.1f}%)")
        print(f"안전+관찰: {total-high-warn}개 ({(total-high-warn)/total*100:.1f}%)")


if __name__ == "__main__":
    df = compute_maturity_risk()
    if not df.is_empty():
        analyze_by_market(df)
