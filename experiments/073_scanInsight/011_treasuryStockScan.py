"""실험 ID: 073-011
실험명: treasuryStock 전수 스캔 — 자사주 보유/취득 현황

목적:
- treasuryStock을 전종목 스캔
- 자사주 보유 기업 비율, 취득/처분 활동, 업종별 분포

가설:
1. 자사주 보유 기업이 전체의 30% 이상
2. 유가증권이 코스닥보다 자사주 보유 비율이 높다
3. 최근 1년 자사주 취득이 있는 기업이 전체의 10% 이상

방법:
1. _scan_parquets로 treasuryStock 전수 스캔
2. 최신 연도 기준 종목별 자사주 보유/취득/처분 수량 추출
3. listing 조인으로 시장별/업종별 분석

결과 (2025년 기준, 2,652종목):
- treasuryStock 원본: 1,058,997행, 2,652종목
- 기준 연도(2025): 30,668행, 2,652종목
- 자사주 보유: 1,505개 (56.7%)
- 당기 취득: 491개 (18.5%)
- 시장별:
  - 유가: 529/805 (65.7%), 당기 취득 159 (19.8%)
  - 코스닥: 971/1,683 (57.7%), 당기 취득 330 (19.6%)
  - 코넥스: 0/110 (0.0%), 당기 취득 0 (0.0%)

결론:
- 가설1 채택: 자사주 보유 56.7% (30% 이상 충족, 예상보다 높음)
- 가설2 채택: 유가 65.7% > 코스닥 57.7% (유가가 더 높음, 차이는 8%p)
- 가설3 채택: 당기 취득 18.5% (10% 이상)
- 코넥스는 자사주 보유/취득 0건 — 소형 기업의 주주환원 부재
- 유가/코스닥 간 당기 취득 비율은 거의 동일(19.8% vs 19.6%)
- capital scan의 자사주 축 데이터로 충분. 배당(010)과 결합 시 순환원율 계산 가능

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


def scan_treasury_stock() -> pl.DataFrame:
    raw = _scan_parquets(
        "treasuryStock",
        ["stockCode", "year", "quarter", "stock_knd", "acqs_mth1",
         "bsis_qy", "change_qy_acqs", "change_qy_dsps", "change_qy_incnr", "trmend_qy"],
    )
    if raw.is_empty():
        print("treasuryStock 데이터 없음")
        return pl.DataFrame()

    print(f"treasuryStock 원본: {raw.shape[0]}행, {raw['stockCode'].n_unique()}종목")

    # 최신 연도 (trmend_qy 유효 500개 이상)
    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        ok = sub.filter(pl.col("trmend_qy").is_not_null() & (pl.col("trmend_qy") != "-")).shape[0]
        if ok >= 300:
            latest_year = y
            break
    if latest_year is None:
        print("충분한 데이터 없음")
        return pl.DataFrame()

    latest = raw.filter(pl.col("year") == latest_year)
    q2 = latest.filter(pl.col("quarter") == "2분기")
    if not q2.is_empty() and q2.shape[0] > 200:
        latest = q2
    print(f"기준 연도({latest_year}): {latest.shape[0]}행, {latest['stockCode'].n_unique()}종목")

    results = []
    for code, group in latest.group_by("stockCode"):
        code_val = code[0]
        total_held = 0
        total_acqs = 0
        total_dsps = 0

        for row in group.iter_rows(named=True):
            held = _parse_num(row.get("trmend_qy"))
            acqs = _parse_num(row.get("change_qy_acqs"))
            dsps = _parse_num(row.get("change_qy_dsps"))
            if held and held > 0:
                total_held += int(held)
            if acqs and acqs > 0:
                total_acqs += int(acqs)
            if dsps and dsps > 0:
                total_dsps += int(dsps)

        results.append({
            "종목코드": code_val,
            "기말보유": total_held,
            "당기취득": total_acqs,
            "당기처분": total_dsps,
            "보유여부": total_held > 0,
            "취득활동": total_acqs > 0,
        })

    df = pl.DataFrame(results)
    total = df.shape[0]
    holding = df.filter(pl.col("보유여부") == True).shape[0]
    acquiring = df.filter(pl.col("취득활동") == True).shape[0]

    print(f"\n종목별 집계: {total}종목")
    print(f"자사주 보유: {holding}개 ({holding/total*100:.1f}%)")
    print(f"당기 취득: {acquiring}개 ({acquiring/total*100:.1f}%)")

    return df


def analyze_by_market(df: pl.DataFrame) -> None:
    from dartlab.engines.dart.scan.network.scanner import load_listing
    _, _, _, listing_meta = load_listing()

    rows = []
    for row in df.iter_rows(named=True):
        meta = listing_meta.get(row["종목코드"], {})
        if meta:
            rows.append({**row, "시장": meta.get("market", ""), "업종": meta.get("industry", "")})

    if not rows:
        return
    merged = pl.DataFrame(rows)

    for market in ["유가", "코스닥", "코넥스"]:
        sub = merged.filter(pl.col("시장") == market)
        if sub.is_empty():
            continue
        total = sub.shape[0]
        holding = sub.filter(pl.col("보유여부") == True).shape[0]
        acq = sub.filter(pl.col("취득활동") == True).shape[0]
        print(f"\n=== {market} ({total}종목) ===")
        print(f"자사주 보유: {holding}개 ({holding/total*100:.1f}%)")
        print(f"당기 취득: {acq}개 ({acq/total*100:.1f}%)")


if __name__ == "__main__":
    df = scan_treasury_stock()
    if not df.is_empty():
        analyze_by_market(df)
