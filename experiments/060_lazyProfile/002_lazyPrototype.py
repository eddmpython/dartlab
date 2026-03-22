"""
실험 ID: 060-002
실험명: Lazy Profile 프로토타입 — index 속도 비교

목적:
- _buildProfile eager (22초) vs lazy index (sections 메타데이터만) 속도 비교
- lazy 상태에서 index가 동일한 정보를 제공하는지 검증
- show(topic)는 on-demand일 때 개별 topic 속도 확인

가설:
1. lazy index는 sections(0.7초) + finance/report 메타(0.1초) = 0.8초 이내
2. eager 대비 20배 이상 빠를 것
3. show(topic)는 eager와 동일한 결과

방법:
1. eager: c.index 호출 → 시간 측정
2. lazy: sections + finance/report 메타데이터로 index DataFrame 재구성 → 시간 측정
3. 결과 비교

결과 (실험 후 작성):
-

결론:
-

실험일: 2026-03-14
"""

import sys
import time

sys.path.insert(0, "src")

import polars as pl


def lazyIndex(c):
    """sections 메타데이터 + finance/report 존재 여부만으로 index 구성."""
    rows = []

    for stmt in ("BS", "IS", "CIS", "CF", "SCE"):
        df = getattr(c, stmt, None)
        if df is not None:
            periodCols = [col for col in df.columns if col not in ("account", "category", "metric")]
            periods = f"{periodCols[-1]}..{periodCols[0]}" if len(periodCols) > 1 else (periodCols[0] if periodCols else "-")
            rows.append({
                "topic": stmt,
                "kind": "finance",
                "source": "finance",
                "periods": periods,
                "shape": f"{df.height}x{df.width}",
                "preview": f"{df.height} accounts",
            })

    rs = c.finance.ratioSeries
    if rs is not None:
        from dartlab.engines.common.finance.ratios import RATIO_CATEGORIES
        series, years = rs
        ratioData = series.get("RATIO", {})
        metricCount = sum(1 for _, fields in RATIO_CATEGORIES for f in fields if ratioData.get(f) and any(v is not None for v in ratioData[f]))
        periods = f"{years[-1]}..{years[0]}" if len(years) > 1 else (years[0] if years else "-")
        rows.append({
            "topic": "ratios",
            "kind": "finance",
            "source": "finance",
            "periods": periods,
            "shape": f"{metricCount}x{len(years)+2}",
            "preview": f"{metricCount} metrics",
        })

    sec = c.docs.sections
    if sec is not None:
        periodCols = [col for col in sec.columns if col != "topic"]
        periodRange = f"{periodCols[-1]}..{periodCols[0]}" if len(periodCols) > 1 else (periodCols[0] if periodCols else "-")
        for row in sec.iter_rows(named=True):
            topic = row["topic"]
            if not isinstance(topic, str) or not topic:
                continue
            nonNull = sum(1 for col in periodCols if row.get(col) is not None)
            preview = "-"
            for col in periodCols:
                val = row.get(col)
                if val is not None:
                    text = str(val).strip().replace("\n", " ")[:80]
                    preview = f"{col}: {text}"
                    break
            rows.append({
                "topic": topic,
                "kind": "docs",
                "source": "docs",
                "periods": periodRange,
                "shape": f"1x{nonNull}",
                "preview": preview,
            })

    if c._hasReport:
        from dartlab.engines.company.dart.report.types import API_TYPE_LABELS, API_TYPES
        for apiType in API_TYPES:
            df = c.report.extract(apiType)
            if df is not None and not df.is_empty():
                rows.append({
                    "topic": apiType,
                    "kind": "report",
                    "source": "report",
                    "periods": "-",
                    "shape": f"{df.height}x{df.width}",
                    "preview": API_TYPE_LABELS.get(apiType, apiType),
                })

    return pl.DataFrame(rows) if rows else pl.DataFrame(schema={
        "topic": pl.Utf8, "kind": pl.Utf8, "source": pl.Utf8,
        "periods": pl.Utf8, "shape": pl.Utf8, "preview": pl.Utf8,
    })


def main():
    from dartlab.engines.company.dart.company import Company

    c = Company("005930")

    print("=" * 70)
    print("LAZY INDEX")
    print("=" * 70)
    t0 = time.perf_counter()
    idx = lazyIndex(c)
    t1 = time.perf_counter()
    print(f"시간: {t1 - t0:.3f}s")
    print(f"shape: {idx.shape}")
    print(idx.head(20))
    print(f"...(총 {idx.height}행)")

    kinds = idx.group_by("kind").agg(pl.len().alias("count"))
    print(f"\nkind 분포: {kinds}")

    print()
    print("=" * 70)
    print("EAGER INDEX (c.index = profile.index)")
    print("=" * 70)
    t2 = time.perf_counter()
    eagerIdx = c.index
    t3 = time.perf_counter()
    print(f"시간: {t3 - t2:.3f}s")
    print(f"shape: {eagerIdx.shape}")

    print()
    print("=" * 70)
    print("비교")
    print("=" * 70)
    print(f"lazy:  {t1 - t0:.3f}s ({idx.height}행)")
    print(f"eager: {t3 - t2:.3f}s ({eagerIdx.height}행)")
    print(f"배율:  {(t3 - t2) / (t1 - t0):.1f}x" if t1 - t0 > 0 else "N/A")


if __name__ == "__main__":
    main()
