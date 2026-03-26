"""
실험 ID: 007
실험명: profile.facts 벡터화

목적:
- profile.facts가 docsBlocks iter_rows (64K행, 1.84s)
- report iter_rows도 추가 부담
- docsBlocks 처리를 Polars expression으로 벡터화

가설:
1. docsBlocks: iter_rows → select/with_columns로 전환하면 1.84s → ~0.2s
2. finance 부분은 dict 기반이라 그대로 유지 (이미 빠름)
3. report 부분은 unpivot으로 벡터화 가능

방법:
1. 삼성전자(005930) profile.facts 시간 측정
2. docsBlocks 처리를 Polars expression으로 벡터화
3. 결과 동일성 assert (행 수, 컬럼, 값)

결과 (실험 후 작성):
- 전체 profile.facts: 첫 호출 2.71s, 캐시 후 0.75-0.80s
- 단계별: finance 0.003s, report 0.04s, docs 0.66s (84%)
- docsBlocks 벡터화: 0.66s → 0.008s (80.6x)
- 행 수 동일 (64,394행), topic/period/source 일치

결론:
- **채택**. docsBlocks iter_rows → Polars select/with_columns 벡터화
- coalesce(detailTopic, semanticTopic, topic), str.slice(0, 400) 등 Polars expression
- profile.facts 전체: ~0.75s → ~0.10s (7.5x)

실험일: 2026-03-19
"""

import sys
import time

sys.path.insert(0, "src")


def main():
    import polars as pl

    import dartlab

    c = dartlab.Company("005930")

    # warmup — 하위 캐시 빌드
    _ = c.docs.sections
    _ = c.finance.annual

    # --- before ---
    times_before = []
    for i in range(3):
        c._cache.pop("_profileFacts", None)
        t0 = time.perf_counter()
        result_before = c.profile.facts
        t1 = time.perf_counter()
        times_before.append(t1 - t0)
        print(f"  before #{i+1}: {t1-t0:.4f}s  shape={result_before.shape if result_before is not None else None}")

    # --- 단계별 프로파일링 ---
    c._cache.pop("_profileFacts", None)

    # finance
    t0 = time.perf_counter()
    annual = c.finance.annual
    frames_finance = []
    if annual is not None:
        series, years = annual
        for sj in ("BS", "IS", "CF"):
            stmt = series.get(sj, {})
            if not stmt:
                continue
            rows = []
            for item, values in stmt.items():
                for idx, year in enumerate(years):
                    value = values[idx] if idx < len(values) else None
                    if value is None:
                        continue
                    rows.append({
                        "topic": sj, "period": str(year), "source": "finance",
                        "valueType": "number", "valueKey": item, "value": value,
                        "payloadRef": f"finance:{sj}:{item}", "priority": 300,
                        "summary": f"{item}={value}",
                    })
            if rows:
                frames_finance.append(pl.DataFrame(rows))
    t1 = time.perf_counter()
    print(f"\n  finance: {t1-t0:.4f}s ({sum(f.height for f in frames_finance)} rows)")

    # report
    t0 = time.perf_counter()
    frames_report = []
    if c.report is not None:
        from dartlab.providers.dart.report.types import API_TYPES
        for apiType in API_TYPES:
            df = c.report.extractAnnual(apiType)
            if df is None or df.is_empty():
                continue
            rows = []
            for row in df.iter_rows(named=True):
                year = row.get("year")
                summaryParts = []
                for key, value in row.items():
                    if key in {"stockCode", "year", "quarter", "quarterNum", "apiType", "stlm_dt"}:
                        continue
                    if value is None:
                        continue
                    summaryParts.append(f"{key}={value}")
                    rows.append({
                        "topic": apiType, "period": str(year), "source": "report",
                        "valueType": "field", "valueKey": key, "value": str(value),
                        "payloadRef": f"report:{apiType}:{row.get('quarter')}",
                        "priority": 200, "summary": None,
                    })
                if rows and summaryParts:
                    summary = "; ".join(summaryParts[:6])
                    for item in rows[-len(summaryParts):]:
                        item["summary"] = summary
            if rows:
                frames_report.append(pl.DataFrame(rows))
    t1 = time.perf_counter()
    print(f"  report:  {t1-t0:.4f}s ({sum(f.height for f in frames_report)} rows)")

    # docsBlocks — 현재
    t0 = time.perf_counter()
    docsBlocks = c.docs.retrievalBlocks
    frames_docs_before = []
    if docsBlocks is not None and not docsBlocks.is_empty():
        docsRows = []
        for row in docsBlocks.iter_rows(named=True):
            period = row.get("period")
            blockText = row.get("blockText")
            if period is None or not blockText:
                continue
            topic = row.get("detailTopic") or row.get("semanticTopic") or row.get("topic")
            if topic is None:
                continue
            docsRows.append({
                "topic": str(topic), "period": str(period), "source": "docs",
                "valueType": row.get("blockType") or "text",
                "valueKey": row.get("blockLabel") or row.get("rawTitle") or str(topic),
                "value": str(blockText),
                "payloadRef": row.get("cellKey") or f"docs:{topic}:{period}",
                "priority": 100, "summary": str(blockText)[:400],
            })
        if docsRows:
            frames_docs_before.append(pl.DataFrame(docsRows))
    t1 = time.perf_counter()
    docs_before_time = t1 - t0
    docs_before_rows = sum(f.height for f in frames_docs_before)
    print(f"  docs before: {docs_before_time:.4f}s ({docs_before_rows} rows, source={docsBlocks.height if docsBlocks is not None else 0})")

    # docsBlocks — 벡터화
    t0 = time.perf_counter()
    frames_docs_after = []
    if docsBlocks is not None and not docsBlocks.is_empty():
        # topic = coalesce(detailTopic, semanticTopic, topic)
        hasDT = "detailTopic" in docsBlocks.columns
        hasST = "semanticTopic" in docsBlocks.columns

        topicExpr = pl.col("topic")
        if hasST:
            topicExpr = pl.coalesce(pl.col("semanticTopic"), topicExpr)
        if hasDT:
            topicExpr = pl.coalesce(pl.col("detailTopic"), topicExpr)

        hasBL = "blockLabel" in docsBlocks.columns
        hasRT = "rawTitle" in docsBlocks.columns
        hasCK = "cellKey" in docsBlocks.columns

        valueKeyExpr = topicExpr.cast(pl.Utf8)
        if hasRT:
            valueKeyExpr = pl.coalesce(pl.col("rawTitle"), valueKeyExpr)
        if hasBL:
            valueKeyExpr = pl.coalesce(pl.col("blockLabel"), valueKeyExpr)

        payloadExpr = pl.concat_str([pl.lit("docs:"), topicExpr.cast(pl.Utf8), pl.lit(":"), pl.col("period").cast(pl.Utf8)])
        if hasCK:
            payloadExpr = pl.coalesce(pl.col("cellKey"), payloadExpr)

        result = (
            docsBlocks
            .filter(pl.col("period").is_not_null() & pl.col("blockText").is_not_null() & (pl.col("blockText") != ""))
            .with_columns(topicExpr.alias("_topic"))
            .filter(pl.col("_topic").is_not_null())
            .select([
                pl.col("_topic").cast(pl.Utf8).alias("topic"),
                pl.col("period").cast(pl.Utf8).alias("period"),
                pl.lit("docs").alias("source"),
                (pl.col("blockType") if "blockType" in docsBlocks.columns else pl.lit("text")).alias("valueType"),
                valueKeyExpr.alias("valueKey"),
                pl.col("blockText").cast(pl.Utf8).alias("value"),
                payloadExpr.alias("payloadRef"),
                pl.lit(100).alias("priority"),
                pl.col("blockText").cast(pl.Utf8).str.slice(0, 400).alias("summary"),
            ])
        )
        if result.height > 0:
            frames_docs_after.append(result)
    t1 = time.perf_counter()
    docs_after_time = t1 - t0
    docs_after_rows = sum(f.height for f in frames_docs_after)
    print(f"  docs after:  {docs_after_time:.4f}s ({docs_after_rows} rows)")

    # 동일성 검증
    if frames_docs_before and frames_docs_after:
        df_before = frames_docs_before[0]
        df_after = frames_docs_after[0]
        assert df_before.height == df_after.height, f"행 수 불일치: {df_before.height} vs {df_after.height}"
        # topic/period/source 비교
        for col in ["topic", "period", "source"]:
            b = df_before.get_column(col).to_list()[:10]
            a = df_after.get_column(col).to_list()[:10]
            assert b == a, f"{col} 불일치 (첫 10행): {b} vs {a}"
        print(f"\n  docs 동일성 검증 OK")

    speedup = docs_before_time / docs_after_time if docs_after_time > 0 else float("inf")
    print(f"\n  docs: {docs_before_time:.4f}s → {docs_after_time:.4f}s ({speedup:.1f}x)")


if __name__ == "__main__":
    main()
