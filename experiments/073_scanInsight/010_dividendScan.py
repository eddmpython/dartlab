"""실험 ID: 073-010
실험명: dividend 전수 스캔 — 배당 현황 시장 분포

목적:
- dividend를 전종목 스캔
- 배당금/배당수익률/배당성향 분포
- 배당 연속 기업 파악

가설:
1. 배당금을 지급하는 기업이 전체의 50% 이상
2. 현금배당수익률 중앙값이 1~3%
3. 유가증권이 코스닥보다 배당 비율이 높다

방법:
1. _scan_parquets로 dividend 전수 스캔
2. 최신 연도 기준 종목별 주당배당금, 배당수익률, 배당성향 추출
3. se(구분) 행에서 핵심 지표 파싱
4. listing 조인으로 업종별/시장별 분석

결과 (2024년 기준, 2,652종목):
- dividend 원본: 1,255,819행, 2,652종목
- 배당 지급: 1,204개 (45.4%), 무배당: 1,448개 (54.6%)
- 주당배당금(배당기업): 중앙값 200원, 평균 105만원(이상치 포함)
- 배당수익률(배당기업): 평균 3.1%, 중앙값 2.6%
- 시장별 배당 비율:
  - 유가: 563/805 (69.9%), 수익률 중앙값 3.2%
  - 코스닥: 616/1,683 (36.6%), 수익률 중앙값 2.1%
  - 코넥스: 6/110 (5.5%), 수익률 중앙값 1.9%
- 업종별 배당 비율: 연료가스/석유정제/교습 100%, R&D 1.4%, 영화 3.0%
- 금융업 수익률 높음: 금융지원 7.1%, 기타금융 3.9%

결론:
- 가설1 기각: 배당 지급 45.4% (50% 미만). 무배당이 과반수
- 가설2 채택: 배당수익률 중앙값 2.6% (1~3% 범위 내)
- 가설3 채택: 유가 69.9% vs 코스닥 36.6% (유가가 거의 2배)
- R&D/바이오는 배당 거의 없음 (73개 중 1개만), 전통 제조/에너지는 배당 일반적
- capital scan의 기초 데이터로 충분. 자사주/증자와 결합 시 순환원율 계산 가능
- 주의: stock_knd(보통주/우선주) 구분이 대부분 null → 보통주 기준으로 보는 게 안전

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


def _parse_num(s: str | None) -> float | None:
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


def scan_dividend() -> pl.DataFrame:
    """dividend 전수 스캔 → 종목별 배당 현황."""
    raw = _scan_parquets(
        "dividend",
        ["stockCode", "year", "quarter", "se", "stock_knd", "thstrm", "frmtrm", "lwfr"],
    )
    if raw.is_empty():
        print("dividend 데이터 없음")
        return pl.DataFrame()

    print(f"dividend 원본: {raw.shape[0]}행, {raw['stockCode'].n_unique()}종목")

    # 최신 연도 (Q4 우선 — 배당은 결산 후 확정)
    # thstrm(당기) 값이 있는 연도 찾기
    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        q4 = sub.filter(pl.col("quarter") == "4분기")
        target = q4 if not q4.is_empty() else sub
        ok = target.filter(
            pl.col("thstrm").is_not_null()
            & (pl.col("thstrm") != "-")
            & (pl.col("thstrm") != "")
        ).shape[0]
        if ok >= 100:
            latest_year = y
            break
    if latest_year is None:
        print("충분한 데이터 없음")
        return pl.DataFrame()

    latest = raw.filter(pl.col("year") == latest_year)
    q4 = latest.filter(pl.col("quarter") == "4분기")
    if not q4.is_empty():
        latest = q4
    print(f"기준 연도({latest_year}): {latest.shape[0]}행, {latest['stockCode'].n_unique()}종목")

    # se 분포 확인
    print(f"\nse 분포:\n{latest['se'].value_counts().sort('count', descending=True).head(15)}")

    # 종목별: 핵심 지표 추출
    DPS_KEYS = {"주당 현금배당금(원)", "주당현금배당금(원)", "주당현금배당금", "현금배당금(원)"}
    YIELD_KEYS = {"현금배당수익률(%)", "현금배당수익률"}
    PAYOUT_KEYS = {"현금배당성향(%)", "현금배당성향", "(연결)현금배당성향(%)", "(별도)현금배당성향(%)"}
    TOTAL_KEYS = {"현금배당금총액(백만원)", "현금배당금총액"}

    results = []
    for code, group in latest.group_by("stockCode"):
        code_val = code[0]
        dps = None
        div_yield = None
        payout = None
        total_div = None

        for row in group.iter_rows(named=True):
            se = row.get("se", "")
            if not se:
                continue
            val = _parse_num(row.get("thstrm"))

            if se in DPS_KEYS and val is not None:
                if dps is None or val > dps:
                    dps = val
            elif se in YIELD_KEYS and val is not None:
                if div_yield is None or val > div_yield:
                    div_yield = val
            elif se in PAYOUT_KEYS and val is not None:
                payout = val
            elif se in TOTAL_KEYS and val is not None:
                total_div = val

        has_dividend = dps is not None and dps > 0

        results.append({
            "종목코드": code_val,
            "주당배당금": dps if dps else 0.0,
            "배당수익률": div_yield if div_yield else 0.0,
            "배당성향": payout if payout else 0.0,
            "배당총액_백만": total_div if total_div else 0.0,
            "배당여부": has_dividend,
        })

    df = pl.DataFrame(results)
    total = df.shape[0]
    paying = df.filter(pl.col("배당여부") == True).shape[0]
    print(f"\n종목별 집계: {total}종목")
    print(f"배당 지급: {paying}개 ({paying/total*100:.1f}%)")
    print(f"무배당: {total - paying}개 ({(total-paying)/total*100:.1f}%)")

    # 배당 기업만 통계
    payers = df.filter(pl.col("배당여부") == True)
    if not payers.is_empty():
        dps_vals = payers["주당배당금"].drop_nulls()
        yield_vals = payers["배당수익률"].drop_nulls()

        print(f"\n=== 주당배당금 분포 (원) — 배당 기업 {payers.shape[0]}개 ===")
        print(f"평균: {dps_vals.mean():,.0f}")
        print(f"중앙값: {dps_vals.median():,.0f}")
        print(f"최소: {dps_vals.min():,.0f}")
        print(f"최대: {dps_vals.max():,.0f}")

        if yield_vals.len() > 0:
            print(f"\n=== 배당수익률 분포 (%) — {yield_vals.len()}개 ===")
            print(f"평균: {yield_vals.mean():.1f}%")
            print(f"중앙값: {yield_vals.median():.1f}%")
            print(f"최소: {yield_vals.min():.1f}%")
            print(f"최대: {yield_vals.max():.1f}%")

    return df


def analyze_by_market(df: pl.DataFrame) -> None:
    """시장별/업종별 배당 분석."""
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
    for market in ["유가", "코스닥", "코넥스"]:
        sub = merged.filter(pl.col("시장") == market)
        if sub.is_empty():
            continue
        total = sub.shape[0]
        paying = sub.filter(pl.col("배당여부") == True).shape[0]
        yields = sub.filter(pl.col("배당수익률").is_not_null() & (pl.col("배당수익률") > 0))["배당수익률"]
        median_yield = yields.median() if yields.len() > 0 else 0
        print(f"\n=== {market} ({total}종목) ===")
        print(f"배당 지급: {paying}개 ({paying/total*100:.1f}%)")
        print(f"배당수익률 중앙값: {median_yield:.1f}%" if median_yield else "")

    # 업종별 배당 비율 (5개 이상)
    industry_stats = (
        merged.group_by("업종")
        .agg([
            pl.col("배당여부").sum().alias("배당기업수"),
            pl.col("종목코드").count().alias("종목수"),
            pl.col("배당수익률").filter(pl.col("배당수익률") > 0).median().alias("중앙값수익률"),
        ])
        .filter(pl.col("종목수") >= 5)
        .with_columns((pl.col("배당기업수") / pl.col("종목수") * 100).round(1).alias("배당비율"))
        .sort("배당비율", descending=True)
    )
    print(f"\n=== 배당 비율 높은 업종 ===")
    print(industry_stats.head(10))
    print(f"\n=== 배당 비율 낮은 업종 ===")
    print(industry_stats.tail(10))


if __name__ == "__main__":
    df = scan_dividend()
    if not df.is_empty():
        analyze_by_market(df)
