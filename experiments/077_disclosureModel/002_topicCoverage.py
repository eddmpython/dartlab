"""
실험 ID: 002
실험명: topic × market 커버리지 매트릭스

목적:
- topic별 몇 개 회사가 해당 데이터를 보유하는지 측정
- DART/EDGAR 간 topic 겹침/차이 파악
- 파인튜닝 학습에 충분한 다양성이 있는지 판단

가설:
1. 상위 10개 topic은 전체 회사의 80%+ 커버리지
2. DART/EDGAR 공통 topic이 5개+ 존재 (교차 학습 가능)
3. 평균 텍스트 길이는 topic마다 10배+ 차이 (긴 topic = 풍부한 학습 자료)

방법:
1. 001에서와 동일하게 전체 회사 sections 로드
2. topic별: 보유 회사 수, 평균/중앙값 텍스트 길이(문자 수), blockType 비율
3. DART/EDGAR별 top 20 topic 출력
4. 공통 topic 교집합 확인

결과 (실행 후 작성):

결론 (실행 후 작성):

실험일: 2026-03-20
"""

import re
import sys
from collections import defaultdict
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
            from dartlab.providers.dart.docs.sections.pipeline import sections
        else:
            from dartlab.providers.edgar.docs.sections.pipeline import sections
        return sections(code)
    except Exception:
        return None


def _measure_text_lengths(df: pl.DataFrame) -> dict:
    """topic별 텍스트 길이 측정."""
    periods = _period_cols(df)
    if not periods:
        return {}

    result = {}
    for topic in df["topic"].unique().to_list():
        topic_df = df.filter(pl.col("topic") == topic)
        text_df = topic_df.filter(pl.col("blockType") == "text")
        table_df = topic_df.filter(pl.col("blockType") == "table")

        # 텍스트 길이: 모든 기간 컬럼의 non-null 값 길이 합산
        text_lengths = []
        for p in periods:
            if p in text_df.columns:
                vals = text_df[p].drop_nulls().to_list()
                text_lengths.extend(len(v) for v in vals if v)

        avg_len = sum(text_lengths) / len(text_lengths) if text_lengths else 0
        result[topic] = {
            "text_rows": text_df.height,
            "table_rows": table_df.height,
            "avg_text_len": avg_len,
            "total_text_chars": sum(text_lengths),
        }
    return result


def main():
    data = Path(dataDir)

    # topic → { market → { companies: set, total_text_chars: int, ... } }
    topic_stats: dict[str, dict[str, dict]] = defaultdict(
        lambda: {
            "DART": {"companies": set(), "total_text_chars": 0, "text_rows": 0, "table_rows": 0, "text_lengths": []},
            "EDGAR": {"companies": set(), "total_text_chars": 0, "text_rows": 0, "table_rows": 0, "text_lengths": []},
        }
    )

    for market, subdir in [("DART", "dart/docs"), ("EDGAR", "edgar/docs")]:
        files = sorted((data / subdir).glob("*.parquet"))
        print(f"{market}: {len(files)} files")
        for i, f in enumerate(files):
            if i % 100 == 0:
                print(f"  {market} progress: {i}/{len(files)}")
            df = _load_sections(f.stem, market)
            if df is None or df.height == 0:
                continue
            measures = _measure_text_lengths(df)
            for topic, m in measures.items():
                bucket = topic_stats[topic][market]
                bucket["companies"].add(f.stem)
                bucket["total_text_chars"] += m["total_text_chars"]
                bucket["text_rows"] += m["text_rows"]
                bucket["table_rows"] += m["table_rows"]
                if m["avg_text_len"] > 0:
                    bucket["text_lengths"].append(m["avg_text_len"])

    # 결과 출력
    print(f"\n{'='*80}")
    print(f"고유 topic 수: {len(topic_stats)}")

    for market in ["DART", "EDGAR"]:
        print(f"\n--- {market} Top 20 topics (by company count) ---")
        ranked = []
        for topic, stats in topic_stats.items():
            s = stats[market]
            if s["companies"]:
                avg_len = (
                    sum(s["text_lengths"]) / len(s["text_lengths"])
                    if s["text_lengths"] else 0
                )
                ranked.append({
                    "topic": topic,
                    "companies": len(s["companies"]),
                    "text_rows": s["text_rows"],
                    "table_rows": s["table_rows"],
                    "avg_text_len": int(avg_len),
                    "total_MB": s["total_text_chars"] / 1_000_000,
                })
        ranked.sort(key=lambda x: x["companies"], reverse=True)
        print(f"{'topic':<35} {'companies':>8} {'text':>6} {'table':>6} {'avgLen':>8} {'totalMB':>8}")
        for r in ranked[:20]:
            print(
                f"{r['topic']:<35} {r['companies']:>8} "
                f"{r['text_rows']:>6} {r['table_rows']:>6} "
                f"{r['avg_text_len']:>8} {r['total_MB']:>8.1f}"
            )

    # 공통 topic
    dart_topics = {t for t, s in topic_stats.items() if s["DART"]["companies"]}
    edgar_topics = {t for t, s in topic_stats.items() if s["EDGAR"]["companies"]}
    common = dart_topics & edgar_topics
    print(f"\n--- 공통 topic ---")
    print(f"DART only: {len(dart_topics - edgar_topics)}")
    print(f"EDGAR only: {len(edgar_topics - dart_topics)}")
    print(f"공통: {len(common)}")
    if common:
        for t in sorted(common):
            d = len(topic_stats[t]["DART"]["companies"])
            e = len(topic_stats[t]["EDGAR"]["companies"])
            print(f"  {t}: DART {d} / EDGAR {e}")


if __name__ == "__main__":
    main()
