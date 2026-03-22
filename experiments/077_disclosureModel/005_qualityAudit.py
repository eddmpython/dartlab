"""
실험 ID: 005
실험명: 30개사 샘플 품질 검사

목적:
- 파인튜닝 학습 데이터로 쓸 수 있는 품질인지 검증
- 매핑률, 텍스트 완결성, 테이블 파싱 성공률 측정
- 품질 이슈 유형 분류 및 비율 산출

가설:
1. topic 매핑률 95%+ (unmapped topic 5% 미만)
2. 텍스트 완결성 90%+ (빈 셀 10% 미만)
3. 전체 품질 스코어 90%+

방법:
1. DART 15개사 + EDGAR 15개사 랜덤 샘플 (seed 42)
2. 각 회사별 측정:
   a. topic 매핑률: unmapped/unknown topic 비율
   b. 텍스트 완결성: 최신 2개 기간에서 non-null 텍스트 비율
   c. 텍스트 길이 적정성: 10자 미만 텍스트 비율 (너무 짧으면 품질 의심)
   d. 테이블 파싱: 마크다운 테이블 구조 보존 여부 (| 포함 비율)
3. 종합 품질 스코어 = (매핑률 + 완결성 + 적정성) / 3

결과 (실행 후 작성):

결론 (실행 후 작성):

실험일: 2026-03-20
"""

import random
import re
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from dartlab.config import dataDir


def _period_cols(df: pl.DataFrame) -> list[str]:
    return [c for c in df.columns if re.match(r"^\d{4}(Q[1-4])?$", c)]


def _load_sections(code: str, market: str) -> pl.DataFrame | None:
    try:
        if market == "DART":
            from dartlab.engines.company.dart.docs.sections.pipeline import sections
        else:
            from dartlab.engines.company.edgar.docs.sections.pipeline import sections
        return sections(code)
    except Exception:
        return None


def _audit_company(code: str, market: str) -> dict | None:
    """단일 회사 품질 감사."""
    df = _load_sections(code, market)
    if df is None or df.height == 0:
        return None

    periods = _period_cols(df)
    if not periods:
        return None

    # 1. topic 매핑률 — unknown/unmapped topic 비율
    topics = df["topic"].unique().to_list()
    unmapped = [t for t in topics if t and ("unknown" in t.lower() or "unmapped" in t.lower() or t.startswith("_"))]
    mapping_rate = 1 - len(unmapped) / len(topics) if topics else 0

    # 2. 텍스트 완결성 — 최신 2개 기간의 non-null 비율
    recent_periods = periods[:2]
    total_cells = 0
    non_null_cells = 0
    for p in recent_periods:
        if p in df.columns:
            col = df[p]
            total_cells += col.len()
            non_null_cells += col.drop_nulls().len()
            # 빈 문자열도 null로 취급
            non_null_cells -= (col.drop_nulls() == "").sum()
    completeness = non_null_cells / total_cells if total_cells else 0

    # 3. 텍스트 길이 적정성 — 10자 미만 비율
    text_df = df.filter(pl.col("blockType") == "text")
    short_count = 0
    total_text_values = 0
    for p in recent_periods:
        if p in text_df.columns:
            vals = text_df[p].drop_nulls().to_list()
            for v in vals:
                if v:
                    total_text_values += 1
                    if len(v.strip()) < 10:
                        short_count += 1
    adequacy = 1 - short_count / total_text_values if total_text_values else 0

    # 4. 테이블 파싱 — | 포함 비율
    table_df = df.filter(pl.col("blockType") == "table")
    table_ok = 0
    table_total = 0
    for p in recent_periods:
        if p in table_df.columns:
            vals = table_df[p].drop_nulls().to_list()
            for v in vals:
                if v:
                    table_total += 1
                    if "|" in v:
                        table_ok += 1
    table_parse_rate = table_ok / table_total if table_total else 1.0

    quality_score = (mapping_rate + completeness + adequacy) / 3

    return {
        "code": code,
        "market": market,
        "topics": len(topics),
        "periods": len(periods),
        "rows": df.height,
        "mapping_rate": mapping_rate,
        "completeness": completeness,
        "adequacy": adequacy,
        "table_parse_rate": table_parse_rate,
        "quality_score": quality_score,
        "unmapped_topics": unmapped,
    }


def main():
    data = Path(dataDir)
    random.seed(42)

    dart_files = sorted((data / "dart" / "docs").glob("*.parquet"))
    edgar_files = sorted((data / "edgar" / "docs").glob("*.parquet"))
    dart_sample = random.sample(dart_files, min(15, len(dart_files)))
    edgar_sample = random.sample(edgar_files, min(15, len(edgar_files)))

    results = []
    for market, samples in [("DART", dart_sample), ("EDGAR", edgar_sample)]:
        print(f"\n--- {market} ---")
        for f in samples:
            r = _audit_company(f.stem, market)
            if r:
                results.append(r)
                print(
                    f"  {r['code']}: topics={r['topics']} periods={r['periods']} "
                    f"map={r['mapping_rate']:.2f} comp={r['completeness']:.2f} "
                    f"adeq={r['adequacy']:.2f} table={r['table_parse_rate']:.2f} "
                    f"Q={r['quality_score']:.2f}"
                )
                if r["unmapped_topics"]:
                    print(f"    unmapped: {r['unmapped_topics']}")
            else:
                print(f"  {f.stem}: SKIP (no data)")

    # 전체 집계
    print(f"\n{'='*60}")
    df = pl.DataFrame([
        {k: v for k, v in r.items() if k != "unmapped_topics"}
        for r in results
    ])

    for market in ["DART", "EDGAR"]:
        sub = df.filter(pl.col("market") == market)
        if sub.height == 0:
            continue
        print(f"\n{market} ({sub.height}개사):")
        for col in ["mapping_rate", "completeness", "adequacy", "table_parse_rate", "quality_score"]:
            med = sub[col].median()
            avg = sub[col].mean()
            mn = sub[col].min()
            print(f"  {col}: median={med:.3f} mean={avg:.3f} min={mn:.3f}")

    all_scores = df["quality_score"]
    print(f"\n전체 품질 스코어:")
    print(f"  median: {all_scores.median():.3f}")
    print(f"  mean: {all_scores.mean():.3f}")
    print(f"  min: {all_scores.min():.3f}")
    print(f"  90%+ 달성: {'YES' if all_scores.mean() >= 0.9 else 'NO'}")


if __name__ == "__main__":
    main()
