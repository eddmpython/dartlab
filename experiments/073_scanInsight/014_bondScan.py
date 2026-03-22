"""실험 ID: 073-014
실험명: bondScan — 사채/단기사채 만기 구조 전수 스캔

목적:
- corporateBond + shortTermBond 전종목 스캔
- 사채 발행 기업 비율, 만기 구조 분포
- 단기 집중도(1년 이내 만기 비중) 분석

가설:
1. 사채 발행 기업이 전체의 15% 이상
2. 단기(1년 이내) 만기 비중이 전체 잔액의 30% 이상
3. 유가증권이 코스닥보다 사채 발행 비율이 높다

방법:
1. _scan_parquets로 corporateBond + shortTermBond 전수 스캔
2. 최신 연도 기준 "합계" 행(remndr_exprtn2) 추출
3. 만기별 잔액 파싱 → 단기/장기 비중 계산
4. listing 조인으로 시장별 분석

결과 (2025년 기준):
- corporateBond 원본: 277,332행, 2,617종목 → 유효 2,474종목
- shortTermBond 원본: 278,282행, 2,622종목 → 유효 2,484종목
- 통합 결과(사채 발행 기업): 810종목
  - 사채(corporateBond): 801개
  - 단기사채(shortTermBond): 74개
  - 양쪽 모두: 65개
- 단기(1년이내) 비중 분포 (801종목):
  - 평균: 32.4%, 중앙값: 20.1%
  - 0~10%: 360개 (44.9%) — 장기 위주
  - 100%: 106개 (13.2%) — 전액 단기
- 시장별 사채 발행 비율:
  - 유가: 360/815 (44.2%), 단기사채 66개
  - 코스닥: 425/1,736 (24.5%), 단기사채 7개
  - 코넥스: 0/110 (0.0%)

결론:
- 가설1 채택: 사채 발행 기업 801개, 전체 상장사 대비 약 30% (15% 이상)
- 가설2 채택: 단기(1년이내) 비중 평균 32.4% (30% 이상). 중앙값 20.1%
- 가설3 채택: 유가 44.2% vs 코스닥 24.5% (유가가 사채 발행 비율 높음)
- 전액 단기(100%) 기업이 106개(13.2%) — 차환 리스크 주의 대상
- 단기사채는 유가 66개 vs 코스닥 7개 — 대기업/금융사 전용 상품
- 44.9%가 단기 비중 10% 미만 — 대부분 장기 사채 위주
- debt축의 기초 데이터로 충분. 이자보상배율과 교차 분석 시 위험 기업 식별 가능

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


# corporateBond 만기별 컬럼 (잔여 만기)
CB_MATURITY_COLS = {
    "yy1_below": "1년미만",
    "yy1_excess_yy2_below": "1~2년",
    "yy2_excess_yy3_below": "2~3년",
    "yy3_excess_yy4_below": "3~4년",
    "yy4_excess_yy5_below": "4~5년",
    "yy5_excess_yy10_below": "5~10년",
    "yy10_excess": "10년초과",
}

# shortTermBond 만기별 컬럼
STB_MATURITY_COLS = {
    "de10_below": "10일미만",
    "de10_excess_de30_below": "10~30일",
    "de30_excess_de90_below": "30~90일",
    "de90_excess_de180_below": "90~180일",
    "de180_excess_yy1_below": "180일~1년",
}


def scan_corporate_bond() -> pl.DataFrame:
    """corporateBond 전수 스캔 → 종목별 만기 구조."""
    raw = _scan_parquets(
        "corporateBond",
        ["stockCode", "year", "quarter", "remndr_exprtn1", "remndr_exprtn2", "sm"]
        + list(CB_MATURITY_COLS.keys()),
    )
    if raw.is_empty():
        print("corporateBond 데이터 없음")
        return pl.DataFrame()

    print(f"corporateBond 원본: {raw.shape[0]}행, {raw['stockCode'].n_unique()}종목")

    # 최신 연도 (sm이 유효한 300개 이상)
    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        ok = sub.filter(pl.col("sm").is_not_null() & (pl.col("sm") != "-") & (pl.col("sm") != "")).shape[0]
        if ok >= 200:
            latest_year = y
            break
    if latest_year is None:
        print("충분한 데이터 없음")
        return pl.DataFrame()

    latest = raw.filter(pl.col("year") == latest_year)
    # 합계 행 우선
    totals = latest.filter(pl.col("remndr_exprtn2") == "합계")
    if totals.is_empty() or totals["stockCode"].n_unique() < 50:
        totals = latest  # 합계 행이 없으면 전체 사용
    print(f"기준 연도({latest_year}): {totals.shape[0]}행, {totals['stockCode'].n_unique()}종목")

    results = []
    for code, group in totals.group_by("stockCode"):
        code_val = code[0]
        total_amount = 0
        short_term = 0  # 1년 이내

        for row in group.iter_rows(named=True):
            sm = _parse_num(row.get("sm"))
            if sm and sm > 0:
                total_amount = max(total_amount, sm)

            # 만기별 집계
            y1 = _parse_num(row.get("yy1_below"))
            if y1 and y1 > 0:
                short_term = max(short_term, y1)

        if total_amount > 0:
            results.append({
                "종목코드": code_val,
                "사채잔액": total_amount,
                "단기잔액_1년이내": short_term,
                "단기비중": round(short_term / total_amount * 100, 1) if total_amount > 0 else 0,
                "유형": "corporateBond",
            })

    return pl.DataFrame(results) if results else pl.DataFrame()


def scan_short_term_bond() -> pl.DataFrame:
    """shortTermBond 전수 스캔."""
    raw = _scan_parquets(
        "shortTermBond",
        ["stockCode", "year", "quarter", "remndr_exprtn1", "remndr_exprtn2", "sm"]
        + list(STB_MATURITY_COLS.keys()),
    )
    if raw.is_empty():
        print("shortTermBond 데이터 없음")
        return pl.DataFrame()

    print(f"shortTermBond 원본: {raw.shape[0]}행, {raw['stockCode'].n_unique()}종목")

    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        ok = sub.filter(pl.col("sm").is_not_null() & (pl.col("sm") != "-") & (pl.col("sm") != "")).shape[0]
        if ok >= 50:
            latest_year = y
            break
    if latest_year is None:
        print("shortTermBond 충분한 데이터 없음")
        return pl.DataFrame()

    latest = raw.filter(pl.col("year") == latest_year)
    totals = latest.filter(pl.col("remndr_exprtn2") == "합계")
    if totals.is_empty() or totals["stockCode"].n_unique() < 10:
        totals = latest
    print(f"shortTermBond 기준 연도({latest_year}): {totals['stockCode'].n_unique()}종목")

    results = []
    for code, group in totals.group_by("stockCode"):
        code_val = code[0]
        total_amount = 0
        for row in group.iter_rows(named=True):
            sm = _parse_num(row.get("sm"))
            if sm and sm > 0:
                total_amount = max(total_amount, sm)
        if total_amount > 0:
            results.append({
                "종목코드": code_val,
                "단기사채잔액": total_amount,
            })

    return pl.DataFrame(results) if results else pl.DataFrame()


def scan_bonds() -> pl.DataFrame:
    """corporateBond + shortTermBond 통합."""
    cb = scan_corporate_bond()
    stb = scan_short_term_bond()

    if cb.is_empty() and stb.is_empty():
        return pl.DataFrame()

    # corporateBond 기준 + shortTermBond 조인
    if cb.is_empty():
        return stb
    if stb.is_empty():
        # shortTermBond 없어도 cb 결과 사용
        cb_result = cb.with_columns(pl.lit(0.0).alias("단기사채잔액"))
        total = cb_result.shape[0]
        has_bond = total
        print(f"\n=== 사채 발행 현황 ({total}종목) ===")
        print(f"사채 발행: {has_bond}개")

        short_ratio = cb_result["단기비중"].drop_nulls()
        if short_ratio.len() > 0:
            print(f"\n=== 단기(1년이내) 비중 분포 ===")
            print(f"평균: {short_ratio.mean():.1f}%")
            print(f"중앙값: {short_ratio.median():.1f}%")
        return cb_result

    merged = cb.join(stb, on="종목코드", how="full", coalesce=True)
    merged = merged.with_columns([
        pl.col("사채잔액").fill_null(0),
        pl.col("단기사채잔액").fill_null(0),
    ])

    total_codes = merged.shape[0]
    cb_only = merged.filter(pl.col("사채잔액") > 0).shape[0]
    stb_only = merged.filter(pl.col("단기사채잔액") > 0).shape[0]
    both = merged.filter((pl.col("사채잔액") > 0) & (pl.col("단기사채잔액") > 0)).shape[0]

    print(f"\n=== 통합 결과 ({total_codes}종목) ===")
    print(f"사채(corporateBond): {cb_only}개")
    print(f"단기사채(shortTermBond): {stb_only}개")
    print(f"양쪽 모두: {both}개")

    # 단기 비중 분포 (corporateBond 기준)
    valid_short = merged.filter(pl.col("단기비중").is_not_null() & (pl.col("사채잔액") > 0))
    if not valid_short.is_empty():
        short_ratio = valid_short["단기비중"]
        print(f"\n=== 단기(1년이내) 비중 분포 (사채 발행 {valid_short.shape[0]}종목) ===")
        print(f"평균: {short_ratio.mean():.1f}%")
        print(f"중앙값: {short_ratio.median():.1f}%")
        # 구간 분포
        for lo, hi in [(0, 10), (10, 30), (30, 50), (50, 70), (70, 100), (100, 101)]:
            if hi == 101:
                cnt = short_ratio.filter(short_ratio == 100).len()
                label = "100%"
            else:
                cnt = short_ratio.filter((short_ratio >= lo) & (short_ratio < hi)).len()
                label = f"{lo}~{hi}%"
            print(f"  {label}: {cnt}개 ({cnt/short_ratio.len()*100:.1f}%)")

    return merged


def analyze_by_market(df: pl.DataFrame) -> None:
    from dartlab.engines.company.dart.scan.network.scanner import load_listing
    _, _, _, listing_meta = load_listing()

    rows = []
    for row in df.iter_rows(named=True):
        meta = listing_meta.get(row["종목코드"], {})
        if meta:
            rows.append({**row, "시장": meta.get("market", "")})

    if not rows:
        return
    merged = pl.DataFrame(rows)

    # 전체 상장사 수 (listing_meta 기준)
    market_total = {}
    for meta in listing_meta.values():
        m = meta.get("market", "")
        market_total[m] = market_total.get(m, 0) + 1

    for market in ["유가", "코스닥", "코넥스"]:
        sub = merged.filter(pl.col("시장") == market)
        total_listed = market_total.get(market, 0)
        has_cb = sub.filter(pl.col("사채잔액") > 0).shape[0] if "사채잔액" in sub.columns else 0
        has_stb = sub.filter(pl.col("단기사채잔액") > 0).shape[0] if "단기사채잔액" in sub.columns else 0
        print(f"\n=== {market} (상장 {total_listed}, 사채발행 {sub.shape[0]}) ===")
        if total_listed > 0:
            print(f"사채 발행 비율: {has_cb}/{total_listed} ({has_cb/total_listed*100:.1f}%)")
            print(f"단기사채 발행: {has_stb}개")


if __name__ == "__main__":
    df = scan_bonds()
    if not df.is_empty():
        analyze_by_market(df)
