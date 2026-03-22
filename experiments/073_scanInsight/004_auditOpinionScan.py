"""실험 ID: 073-004
실험명: auditOpinion 전수 스캔 — 감사의견 시장 분포

목적:
- auditOpinion을 전종목 스캔
- 감사의견 분포 (적정/한정/부적정/의견거절)
- 비적정 기업 특성 파악, 감사법인별 분포

가설:
1. 비적정 의견(한정/부적정/의견거절) 기업이 전체의 3% 이상
2. 감사법인 상위 4개(Big4)가 유가증권 80% 이상 커버
3. 코넥스/코스닥이 유가보다 비적정 비율이 높다

방법:
1. _scan_parquets로 auditOpinion 전수 스캔
2. 최신 연도 기준 종목별 감사의견, 감사법인 추출
3. 비적정 기업 필터 + 시장별/감사법인별 분석

결과 (2025년 기준, 2,598종목):
- auditOpinion 원본: 306,134행, 2,606종목
- 종목별 유효: 2,405종목
- 감사의견 분포:
  | 적정의견: 2,361 (98.2%) | 의견거절: 34 (1.4%) | 한정의견: 9 (0.4%) | 부적정의견: 1 (0.04%) |
- 비적정 합계: 44개 (1.8%)
- 감사법인 상위 5: 삼일(346), 삼정(280), 대주(180), 한영(170), 삼덕(164)
- Big4(삼일/삼정/한영/안진) 커버: 912개 (37.9%)
- 시장별:
  - 유가: 비적정 12개(1.5%), Big4 456개(57.4%)
  - 코스닥: 비적정 29개(1.8%), Big4 452개(27.5%)
  - 코넥스: 비적정 0개, Big4 1개(0.9%)
- 비적정 기업 41개 (listing 매칭): 의견거절 34, 한정의견 6, 부적정의견 1

결론:
- 가설1 기각: 비적정 1.8% (3% 미만). 한국 시장은 적정의견이 압도적
- 가설2 기각: Big4가 유가 57.4%만 커버 (80% 미달). 다만 유가증권 내 Big4 집중도는 가장 높음
- 가설3 부분 채택: 코스닥(1.8%) > 유가(1.5%)이지만 차이 미미
- 의견거절(34개)이 비적정의 주류. 한정의견(9) + 부적정(1)은 극히 드묾
- Big4 커버율이 37.9%로 예상보다 낮음 → 중소형 회계법인이 시장 분산
- governance scan 네 번째 축으로 유효하나, 비적정이 매우 소수 → 이진 플래그로 활용

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


BIG4 = {"삼일회계법인", "삼정회계법인", "한영회계법인", "안진회계법인"}
NON_CLEAN = {"한정의견", "부적정의견", "의견거절"}


def scan_audit_opinion() -> pl.DataFrame:
    """auditOpinion 전수 스캔 → 종목별 감사의견/감사법인."""
    raw = _scan_parquets(
        "auditOpinion",
        ["stockCode", "year", "quarter", "bsns_year", "adtor", "adt_opinion",
         "adt_reprt_spcmnt_matter"],
    )
    if raw.is_empty():
        print("auditOpinion 데이터 없음")
        return pl.DataFrame()

    print(f"auditOpinion 원본: {raw.shape[0]}행, {raw['stockCode'].n_unique()}종목")
    print(f"연도: {sorted(raw['year'].unique().to_list())}")

    # 최신 연도 (adt_opinion non-null 500개 이상)
    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        ok = sub.filter(pl.col("adt_opinion").is_not_null()).shape[0]
        if ok >= 500:
            latest_year = y
            break
    if latest_year is None:
        print("충분한 데이터 없음")
        return pl.DataFrame()

    latest = raw.filter(pl.col("year") == latest_year)
    print(f"기준 연도({latest_year}): {latest.shape[0]}행, {latest['stockCode'].n_unique()}종목")

    # 감사의견 분포
    print(f"\n=== 감사의견 전체 분포 ===")
    print(latest["adt_opinion"].value_counts().sort("count", descending=True))

    # 종목별 대표 감사의견 (Q4 선호, 최악 의견 채택)
    opinion_rank = {"의견거절": 4, "부적정의견": 3, "한정의견": 2, "적정의견": 1}

    results = []
    for code, group in latest.group_by("stockCode"):
        code_val = code[0]
        # adt_opinion non-null인 행만 사용
        valid_rows = group.filter(pl.col("adt_opinion").is_not_null())
        if valid_rows.is_empty():
            valid_rows = group

        worst_rank = 0
        worst_opinion = None
        auditor = None

        for row in valid_rows.iter_rows(named=True):
            op = row.get("adt_opinion")
            if op:
                rank = opinion_rank.get(op, 0)
                if rank > worst_rank:
                    worst_rank = rank
                    worst_opinion = op
                elif worst_opinion is None:
                    worst_opinion = op
            aud = row.get("adtor")
            if aud and aud != "-":
                auditor = aud

        results.append({
            "종목코드": code_val,
            "감사의견": worst_opinion or "",
            "감사법인": auditor or "",
        })

    df = pl.DataFrame(results)
    valid = df.filter(pl.col("감사의견") != "")
    print(f"\n종목별 집계: {df.shape[0]}종목 (유효: {valid.shape[0]})")

    # 의견 분포
    opinion_dist = valid["감사의견"].value_counts().sort("count", descending=True)
    print(f"\n=== 종목별 감사의견 분포 ===")
    print(opinion_dist)

    total = valid.shape[0]
    non_clean = valid.filter(pl.col("감사의견").is_in(list(NON_CLEAN)))
    print(f"\n비적정: {non_clean.shape[0]}개 ({non_clean.shape[0]/total*100:.1f}%)")

    # 감사법인 분포
    auditor_dist = (
        valid.filter(pl.col("감사법인").is_not_null())
        ["감사법인"].value_counts()
        .sort("count", descending=True)
    )
    print(f"\n=== 감사법인 분포 (상위 15) ===")
    print(auditor_dist.head(15))

    # Big4 비율
    big4_cnt = valid.filter(pl.col("감사법인").is_in(list(BIG4)) & (pl.col("감사법인") != "")).shape[0]
    print(f"\nBig4 커버: {big4_cnt}개 ({big4_cnt/total*100:.1f}%)")

    return df


def analyze_by_market(df: pl.DataFrame) -> None:
    """시장별 감사의견 분석."""
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

    # 시장별 감사의견 분포
    for market in ["유가", "코스닥", "코넥스"]:
        sub = merged.filter(pl.col("시장") == market)
        if sub.is_empty():
            continue
        total = sub.shape[0]
        non_clean = sub.filter(pl.col("감사의견").is_in(list(NON_CLEAN))).shape[0]
        big4 = sub.filter(pl.col("감사법인").is_in(list(BIG4))).shape[0]
        print(f"\n=== {market} ({total}종목) ===")
        print(f"비적정: {non_clean}개 ({non_clean/total*100:.1f}%)")
        print(f"Big4: {big4}개 ({big4/total*100:.1f}%)")
        print(sub["감사의견"].value_counts().sort("count", descending=True))

    # 비적정 기업 상세
    non_clean_df = merged.filter(pl.col("감사의견").is_in(list(NON_CLEAN)))
    if not non_clean_df.is_empty():
        print(f"\n=== 비적정 기업 목록 ({non_clean_df.shape[0]}개) ===")
        print(non_clean_df.select(["종목코드", "감사의견", "감사법인", "시장", "업종"]))


if __name__ == "__main__":
    df = scan_audit_opinion()
    if not df.is_empty():
        analyze_by_market(df)
