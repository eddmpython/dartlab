"""실험 ID: 073-002
실험명: outsideDirector 전수 스캔 — 사외이사 비율 시장 분포

목적:
- outsideDirector report를 전종목 스캔
- 사외이사 수, 비율(사외이사/전체이사) 분포
- 업종별/시장별(유가/코스닥) 차이 파악

가설:
1. 유가증권 기업이 코스닥보다 사외이사 비율이 높다 (규제 차이)
2. 사외이사 0명 기업이 전체의 20% 이상 존재
3. 업종별 사외이사 비율 차이가 유의미하다

방법:
1. outsideDirector + executive를 전수 스캔
2. executive에서 총이사수, 사외이사수 추출
3. 사외이사 비율 = 사외이사 / 전체이사
4. listing 조인으로 업종별/시장별 분석

결과 (2025년 기준, 2,641종목):
- executive 원본: 1,063,609행, 2,647종목
- 사외이사 비율: 평균 13.5%, 중앙값 11.5%, 최대 68.2%
- 구간 분포:
  |  0~10%: 1,207 (45.7%) | 10~20%: 692 (26.2%) | 20~30%: 454 (17.2%) |
  | 30~40%: 151 (5.7%)    | 40~50%: 89 (3.4%)   | 50%+: 48 (1.8%)     |
- 사외이사 0명: 822개 (31.1%)
- 시장별:
  - 코스닥: 14.3% (0명 422개/1,674)
  - 유가: 13.7% (0명 271개/803)
  - 코넥스: 0.5% (0명 108개/110)
- 업종별 높은 곳: 골판지(25.6%), 전기통신공사(22.3%), 무점포소매(22.1%)
- 업종별 낮은 곳: 도축(3.6%), 해상운송(5.3%), 기타운송서비스(5.3%), 보험(7.0%)

결론:
- 가설1 기각: 유가(13.7%) ≒ 코스닥(14.3%), 예상과 달리 비슷. 코넥스만 극단적으로 낮음
- 가설2 채택: 사외이사 0명 31.1% (20% 초과)
- 가설3 채택: 업종간 최대 22%p 차이 (골판지 25.6% vs 도축 3.6%)
- 주의: 사외이사 비율이 ofcps에서 "사외" 포함으로 추출 → rgist_exctv_at의 "사외이사" 기준과 교차 검증 필요
- 보험업 사외이사 비율이 7%로 낮은 건 의외 → 대형 보험사 임원 수가 많아서 비율 희석?
- governance scan의 두 번째 축으로 유효

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


def _parse_int(s: str | None) -> int | None:
    if s is None or s.strip() in ("", "-"):
        return None
    try:
        return int(s.replace(",", "").replace(".0", ""))
    except ValueError:
        return None


def scan_executive() -> pl.DataFrame:
    """executive 전수 스캔 → 종목별 이사 구성."""
    raw = _scan_parquets(
        "executive",
        ["stockCode", "year", "quarter", "nm", "sexdstn", "rgist_exctv_at", "ofcps",
         "fte_at", "chrg_job", "mxmm_shrholdr_relate"],
    )
    if raw.is_empty():
        print("executive 데이터 없음")
        return pl.DataFrame()

    print(f"executive 원본: {raw.shape[0]}행, {raw['stockCode'].n_unique()}종목")
    print(f"연도: {sorted(raw['year'].unique().to_list())}")

    # 데이터가 충분한 최신 연도 (ofcps non-null이 1000개 이상)
    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        ofcps_ok = sub.filter(pl.col("ofcps").is_not_null()).shape[0] if "ofcps" in sub.columns else 0
        if ofcps_ok > 1000:
            latest_year = y
            break
    if latest_year is None:
        print("충분한 데이터 없음")
        return pl.DataFrame()

    latest = raw.filter(pl.col("year") == latest_year)
    print(f"기준 연도({latest_year}): {latest.shape[0]}행, {latest['stockCode'].n_unique()}종목")

    # rgist_exctv_at: 등기여부, ofcps: 직위 (사내이사, 사외이사, 기타비상무이사 등)
    if "rgist_exctv_at" in latest.columns:
        print(f"\n등기여부 분포:\n{latest['rgist_exctv_at'].value_counts().sort('count', descending=True).head(10)}")
    if "ofcps" in latest.columns:
        print(f"\n직위 분포:\n{latest['ofcps'].value_counts().sort('count', descending=True).head(15)}")

    # 종목별 이사 구성 집계
    def _is_outside(ofcps: str | None) -> bool:
        if ofcps is None:
            return False
        return "사외" in ofcps

    def _is_registered(rgist: str | None) -> bool:
        if rgist is None:
            return False
        return "등기" in rgist or rgist == "Y" or rgist == "사내이사"

    results = []
    for code, group in latest.group_by("stockCode"):
        code_val = code[0]
        total = group.shape[0]
        outside = 0
        registered = 0
        for row in group.iter_rows(named=True):
            if _is_outside(row.get("ofcps")):
                outside += 1
            if row.get("rgist_exctv_at") in ("등기임원", "사내이사", "사외이사"):
                registered += 1

        ratio = outside / total * 100 if total > 0 else 0
        results.append({
            "종목코드": code_val,
            "총임원수": total,
            "사외이사수": outside,
            "사외이사비율": round(ratio, 1),
        })

    df = pl.DataFrame(results)
    print(f"\n종목별 집계: {df.shape[0]}종목")

    # 분포 통계
    ratios = df["사외이사비율"]
    print(f"\n=== 사외이사 비율 분포 ===")
    print(f"평균: {ratios.mean():.1f}%")
    print(f"중앙값: {ratios.median():.1f}%")
    print(f"최소: {ratios.min():.1f}%")
    print(f"최대: {ratios.max():.1f}%")

    # 사외이사 0명
    zero = df.filter(pl.col("사외이사수") == 0)
    print(f"\n사외이사 0명: {zero.shape[0]}개 ({zero.shape[0]/df.shape[0]*100:.1f}%)")

    # 구간 분포
    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    total_cnt = ratios.len()
    print(f"\n=== 구간별 분포 ===")
    for i in range(len(bins) - 1):
        lo, hi = bins[i], bins[i + 1]
        cnt = ratios.filter((ratios >= lo) & (ratios < hi)).len()
        pct = cnt / total_cnt * 100
        bar = "█" * int(pct / 2)
        print(f"{lo:3d}~{hi:3d}%: {cnt:4d} ({pct:5.1f}%) {bar}")

    return df


def analyze_by_market(df: pl.DataFrame) -> None:
    """시장별/업종별 사외이사 비율 분석."""
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
            pl.col("사외이사비율").mean().alias("평균비율"),
            pl.col("사외이사비율").median().alias("중앙값"),
            pl.col("사외이사수").filter(pl.col("사외이사수") == 0).count().alias("0명기업"),
            pl.col("종목코드").count().alias("종목수"),
        ])
        .sort("평균비율", descending=True)
    )
    print(f"\n=== 시장별 사외이사 비율 ===")
    print(market_stats)

    # 업종별 (5개 이상)
    industry_stats = (
        merged.group_by("업종")
        .agg([
            pl.col("사외이사비율").mean().alias("평균비율"),
            pl.col("종목코드").count().alias("종목수"),
        ])
        .filter(pl.col("종목수") >= 5)
        .sort("평균비율", descending=True)
    )
    print(f"\n=== 사외이사 비율 높은 업종 ===")
    print(industry_stats.head(10))
    print(f"\n=== 사외이사 비율 낮은 업종 ===")
    print(industry_stats.tail(10))


if __name__ == "__main__":
    df = scan_executive()
    if not df.is_empty():
        analyze_by_market(df)
