"""실험 ID: 073-012
실험명: capitalChange 전수 스캔 — 증자/감자 현황

목적:
- capitalChange를 전종목 스캔
- 증자/감자 유형별 분포, 최근 활동 기업, 시장별 차이

가설:
1. 최근 3년 증자/감자 활동이 있는 기업이 전체의 20% 이상
2. 유상증자(제3자배정)가 가장 빈번한 증자 유형
3. 코스닥이 유가보다 증자 빈도가 높다 (성장 자금 수요)

방법:
1. _scan_parquets로 capitalChange 전수 스캔
2. isu_dcrs_stle(증감자 형태) 유효 데이터 필터
3. 최근 3년 기준 증자/감자 유형별 집계
4. listing 조인으로 시장별/업종별 분석

결과 (2,380종목 유효):
- capitalChange 원본: 910,971행, 2,655종목 → 유효(형태≠"-"): 820,716행, 2,380종목
- 전체 유형 분포: 전환권행사(265K) > 신주인수권행사(138K) > 주식매수선택권행사(120K) > 유상증자제3자배정(104K)
- 종목별 집계:
  - 증자 이력: 2,307개 (96.9%)
  - 감자 이력: 458개 (19.2%)
  - 최근 3년 활동: 1,307개 (54.9%)
- 최근 3년(2023~) 이벤트: 61,394행, 1,307종목
  - 전환권행사(29K) > 주식매수선택권행사(13K) > 신주인수권행사(7.5K) > 유상증자제3자배정(5.3K)
- 시장별:
  - 유가: 증자 91.3%, 감자 24.5%, 최근3년 37.4%
  - 코스닥: 증자 98.8%, 감자 17.2%, 최근3년 60.3%
  - 코넥스: 증자 98.1%, 감자 18.5%, 최근3년 59.3%
- 증자횟수(증자기업): 평균 327.5회, 중앙값 159회, 최대 5,992회

결론:
- 가설1 채택: 최근 3년 활동 54.9% (20% 이상, 예상보다 훨씬 높음)
- 가설2 기각: 전환권행사(265K)가 최다. 유상증자(제3자배정)는 4위(104K). CB/BW 행사가 실질 증자 주류
- 가설3 채택: 코스닥 60.3% vs 유가 37.4% (코스닥이 최근 증자 활동 1.6배 높음)
- 거의 모든 기업(96.9%)이 증자 이력 보유 — 상장사는 자본시장 활용이 일상
- 전환권/신주인수권 행사가 전체 증자의 63%를 차지 → 메자닌 금융이 한국 증자의 핵심
- 유가는 증자 빈도 낮고 감자 비율 높음(24.5%) — 성숙 기업의 자본 구조 최적화
- capital scan에서 배당(010)/자사주(011)와 결합 시 순환원율 계산 가능

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


def _parse_date_year(s) -> int | None:
    """'2021.06.15' 또는 '2021-06-15' → 2021."""
    if s is None:
        return None
    s = str(s).strip()
    if s in ("", "-"):
        return None
    for sep in (".", "-"):
        if sep in s:
            parts = s.split(sep)
            if len(parts) >= 1:
                try:
                    y = int(parts[0])
                    if 1990 <= y <= 2030:
                        return y
                except ValueError:
                    pass
    return None


# 증자/감자 분류
INCREASE_TYPES = {
    "유상증자(주주배정)", "유상증자(제3자배정)", "유상증자(일반공모)",
    "전환권행사", "신주인수권행사", "주식매수선택권행사",
    "무상증자",
}
DECREASE_TYPES = {
    "유상감자", "무상감자",
}


def scan_capital_change() -> pl.DataFrame:
    raw = _scan_parquets(
        "capitalChange",
        ["stockCode", "year", "quarter", "isu_dcrs_stle", "isu_dcrs_stock_knd",
         "isu_dcrs_qy", "isu_dcrs_de", "isu_dcrs_mstvdv_fval_amount",
         "isu_dcrs_mstvdv_amount"],
    )
    if raw.is_empty():
        print("capitalChange 데이터 없음")
        return pl.DataFrame()

    print(f"capitalChange 원본: {raw.shape[0]}행, {raw['stockCode'].n_unique()}종목")

    # 유효 데이터만 (isu_dcrs_stle != "-" and not null)
    valid = raw.filter(
        pl.col("isu_dcrs_stle").is_not_null()
        & (pl.col("isu_dcrs_stle") != "-")
        & (pl.col("isu_dcrs_stle") != "")
    )
    print(f"유효 데이터: {valid.shape[0]}행, {valid['stockCode'].n_unique()}종목")

    # 유형 분포
    print(f"\n=== 증감자 유형 분포 ===")
    type_dist = valid["isu_dcrs_stle"].value_counts().sort("count", descending=True)
    print(type_dist)

    # 최근 3년 (isu_dcrs_de 기준)
    recent_rows = []
    for row in valid.iter_rows(named=True):
        event_year = _parse_date_year(row.get("isu_dcrs_de"))
        if event_year and event_year >= 2023:
            recent_rows.append({**row, "event_year": event_year})

    if not recent_rows:
        # fallback: year 컬럼 기준
        years = sorted(valid["year"].unique().to_list(), reverse=True)
        recent_years = years[:3]
        for row in valid.iter_rows(named=True):
            if row.get("year") in recent_years:
                recent_rows.append({**row, "event_year": None})

    recent = pl.DataFrame(recent_rows) if recent_rows else pl.DataFrame()
    print(f"\n최근 3년(2023~) 이벤트: {recent.shape[0]}행, {recent['stockCode'].n_unique()}종목")

    if not recent.is_empty():
        print(f"\n최근 3년 유형 분포:")
        print(recent["isu_dcrs_stle"].value_counts().sort("count", descending=True))

    # 종목별 집계
    results = []
    for code, group in valid.group_by("stockCode"):
        code_val = code[0]
        increase_count = 0
        decrease_count = 0
        total_increase_qty = 0
        total_decrease_qty = 0
        recent_activity = False
        types_seen: set[str] = set()

        for row in group.iter_rows(named=True):
            stle = row.get("isu_dcrs_stle", "")
            qty = _parse_num(row.get("isu_dcrs_qy"))
            event_year = _parse_date_year(row.get("isu_dcrs_de"))

            if stle in INCREASE_TYPES:
                increase_count += 1
                if qty and qty > 0:
                    total_increase_qty += int(qty)
            elif stle in DECREASE_TYPES:
                decrease_count += 1
                if qty and qty > 0:
                    total_decrease_qty += int(qty)

            types_seen.add(stle)
            if event_year and event_year >= 2023:
                recent_activity = True

        results.append({
            "종목코드": code_val,
            "증자횟수": increase_count,
            "감자횟수": decrease_count,
            "증자주수": total_increase_qty,
            "감자주수": total_decrease_qty,
            "최근3년활동": recent_activity,
            "유형수": len(types_seen),
        })

    df = pl.DataFrame(results)
    total = df.shape[0]
    has_increase = df.filter(pl.col("증자횟수") > 0).shape[0]
    has_decrease = df.filter(pl.col("감자횟수") > 0).shape[0]
    recent_active = df.filter(pl.col("최근3년활동") == True).shape[0]

    print(f"\n=== 종목별 집계: {total}종목 ===")
    print(f"증자 이력 있음: {has_increase}개 ({has_increase/total*100:.1f}%)")
    print(f"감자 이력 있음: {has_decrease}개 ({has_decrease/total*100:.1f}%)")
    print(f"최근 3년 활동: {recent_active}개 ({recent_active/total*100:.1f}%)")

    # 증자횟수 분포
    inc_counts = df.filter(pl.col("증자횟수") > 0)["증자횟수"]
    if inc_counts.len() > 0:
        print(f"\n=== 증자횟수 분포 (증자 기업 {inc_counts.len()}개) ===")
        print(f"평균: {inc_counts.mean():.1f}회")
        print(f"중앙값: {inc_counts.median():.0f}회")
        print(f"최대: {inc_counts.max()}회")

    return df


def analyze_by_market(df: pl.DataFrame) -> None:
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

    for market in ["유가", "코스닥", "코넥스"]:
        sub = merged.filter(pl.col("시장") == market)
        if sub.is_empty():
            continue
        total = sub.shape[0]
        inc = sub.filter(pl.col("증자횟수") > 0).shape[0]
        dec = sub.filter(pl.col("감자횟수") > 0).shape[0]
        recent = sub.filter(pl.col("최근3년활동") == True).shape[0]
        print(f"\n=== {market} ({total}종목) ===")
        print(f"증자 이력: {inc}개 ({inc/total*100:.1f}%)")
        print(f"감자 이력: {dec}개 ({dec/total*100:.1f}%)")
        print(f"최근 3년: {recent}개 ({recent/total*100:.1f}%)")


if __name__ == "__main__":
    df = scan_capital_change()
    if not df.is_empty():
        analyze_by_market(df)
