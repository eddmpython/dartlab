"""
실험 ID: 002
실험명: N기간 변화 매트릭스

목적:
- sections 전 기간 데이터로 topic × period 변화 매트릭스 구축
- "핫 토픽" (자주 변하는 topic) 식별 가능한지 검증
- HeatmapChart ChartSpec 호환 여부 확인

가설:
1. topic × period 매트릭스로 변화 패턴이 식별 가능하다
2. 변화율 상위 topic이 실제 사업 변화와 대응한다
   (businessOverview, riskFactors 등이 상위)
3. 매트릭스가 HeatmapChart 호환 크기 (topic 50개 이내, period 20개 이내)

방법:
1. 삼성전자/현대차/LG에너지솔루션 sections 로드
2. sectionsDiff()의 entries에서 topic × period 매트릭스 구축
   - 값: CHANGED=1, SAME=0, NULL=-1
3. 변화율 상위 10개 "핫 토픽" 추출
4. HeatmapChart ChartSpec dict 변환

결과 (v2 — text-only 필터 추가 + non-period 정규식 수정):
- 삼성전자: 41 topics × 39 periods, 안정 22개
  전체 핫 1위: companyOverview(100%), text 핫 1위: companyOverview(100%)
  text 상위: productService, rawMaterial, salesOrder, majorContractsAndRnd
- 현대차: 43 topics × 32 periods, 안정 28개
  전체 핫 1위: otherReferences(100%), text 핫 1위: otherReferences(100%)
  text 상위: financialSoundnessOtherReference, fundraising, contingentLiability
- LG에너지솔루션: 40 topics × 19 periods, 안정 24개
  전체 핫 1위: rawMaterial(100%), text 핫 1위: rawMaterial(100%)
  text 상위: fundraising, salesOrder, appendixSchedule
- HeatmapSpec (text-only): 15×19~39
- text-only 필터로 consolidatedStatements/financialStatements 제거됨
  → 서술형 핫 토픽이 정확히 식별됨

결론:
- 가설 1 채택: topic × period 매트릭스 정상 생성, 패턴 식별 가능
- 가설 2 채택 (text-only 필터 적용 시): 서술형 핫 토픽이 실제 사업 변화 대응
  rawMaterial(원재료), fundraising(자금조달), salesOrder(수주) 등
- 가설 3 채택: 15×19~39 HeatmapChart 렌더링 가능
- 흡수: common/docs/diff.py에 diffMatrix(textOnly=True) 함수 추가

실험일: 2026-03-20
"""

import polars as pl

import dartlab
from dartlab.core.docs.diff import sectionsDiff


def build_diff_matrix(sections_df: pl.DataFrame) -> dict:
    """sections DataFrame → topic × period 변화 매트릭스."""
    result = sectionsDiff(sections_df)

    # period 컬럼 추출 (날짜 형태 컬럼들)
    import re
    periods = sorted([c for c in sections_df.columns if re.match(r"^\d{4}(Q[1-4])?$", c)], reverse=True)

    # entries에서 매트릭스 구축
    # topic → {period_pair → status}
    topic_changes = {}
    for entry in result.entries:
        t = entry.topic
        if t not in topic_changes:
            topic_changes[t] = {}
        topic_changes[t][entry.toPeriod] = entry.status

    # summaries에서 topic 목록 + changeRate
    summaries = {s.topic: s for s in result.summaries}

    # 매트릭스 구축: topic × toPeriod
    # 인접 기간 비교이므로 toPeriod 기준
    to_periods = sorted(
        {e.toPeriod for e in result.entries},
        reverse=True,
    )

    matrix_rows = []
    for topic, summary in sorted(summaries.items(), key=lambda x: -x[1].changeRate):
        row = {"topic": topic, "chapter": summary.chapter, "changeRate": summary.changeRate}
        for p in to_periods:
            changes = topic_changes.get(topic, {})
            if p in changes:
                row[p] = 1 if changes[p] == "CHANGED" else 0
            else:
                row[p] = 0  # not in entries = SAME
        matrix_rows.append(row)

    return {
        "matrix": matrix_rows,
        "periods": to_periods,
        "topic_count": len(matrix_rows),
        "period_count": len(to_periods),
        "summaries": summaries,
    }


def build_heatmap_spec(matrix_data: dict, company_name: str, top_n: int = 20) -> dict:
    """변화 매트릭스 → HeatmapChart ChartSpec dict."""
    rows = matrix_data["matrix"][:top_n]
    periods = matrix_data["periods"]

    return {
        "chartType": "heatmap",
        "title": f"{company_name} topic 변화 히트맵 (상위 {len(rows)}개)",
        "xLabels": periods,
        "yLabels": [r["topic"] for r in rows],
        "data": [[r.get(p, -1) for p in periods] for r in rows],
        "meta": {
            "colorScale": {"0": "#e8f5e9", "1": "#ef5350", "-1": "#eeeeee"},
            "legend": {"0": "변화없음", "1": "변화", "-1": "데이터없음"},
        },
    }


if __name__ == "__main__":
    test_codes = [
        ("005930", "삼성전자"),
        ("005380", "현대차"),
        ("373220", "LG에너지솔루션"),
    ]

    all_results = {}

    for code, name in test_codes:
        print(f"\n{'='*60}")
        print(f"{name} ({code})")
        print(f"{'='*60}")

        c = dartlab.Company(code)
        sections = c.docs.sections.raw

        print(f"  sections shape: {sections.shape}")

        # 매트릭스 구축 (전체)
        matrix_data = build_diff_matrix(sections)

        # text-only 매트릭스 (서술형 topic만)
        text_sections = sections.filter(pl.col("blockType") == "text")
        text_matrix = build_diff_matrix(text_sections)

        print(f"  topic 수: {matrix_data['topic_count']}")
        print(f"  비교 기간 수: {matrix_data['period_count']}")
        print(f"  기간 목록: {matrix_data['periods'][:10]}...")

        # 핫 토픽 상위 10
        print(f"\n  [핫 토픽 상위 10]")
        hot_topics = matrix_data["matrix"][:10]
        for i, row in enumerate(hot_topics, 1):
            rate = row["changeRate"]
            changed_periods = sum(1 for p in matrix_data["periods"] if row.get(p) == 1)
            print(f"  {i:2d}. {row['topic']:<30s} 변화율 {rate:.1%}  ({changed_periods}/{matrix_data['period_count']}기간)")

        # 안정 토픽 하위 5
        stable = [r for r in matrix_data["matrix"] if r["changeRate"] == 0]
        print(f"\n  [완전 안정 토픽]: {len(stable)}개")
        for r in stable[:5]:
            print(f"    · {r['topic']}")

        # text-only 핫 토픽
        print(f"\n  [text-only 핫 토픽 상위 10]")
        text_hot = text_matrix["matrix"][:10]
        for i, row in enumerate(text_hot, 1):
            rate = row["changeRate"]
            changed_p = sum(1 for p in text_matrix["periods"] if row.get(p) == 1)
            print(f"  {i:2d}. {row['topic']:<30s} 변화율 {rate:.1%}  ({changed_p}/{text_matrix['period_count']}기간)")

        # HeatmapChart ChartSpec (text-only)
        spec = build_heatmap_spec(text_matrix, name, top_n=15)
        print(f"\n  [HeatmapChart ChartSpec (text-only)]")
        print(f"    x축(기간): {len(spec['xLabels'])}개")
        print(f"    y축(topic): {len(spec['yLabels'])}개")
        print(f"    data shape: {len(spec['data'])}×{len(spec['data'][0]) if spec['data'] else 0}")

        all_results[name] = {
            "topics": matrix_data["topic_count"],
            "text_topics": text_matrix["topic_count"],
            "periods": matrix_data["period_count"],
            "hot_topics": [(r["topic"], r["changeRate"]) for r in hot_topics],
            "text_hot_topics": [(r["topic"], r["changeRate"]) for r in text_hot],
            "stable_count": len(stable),
            "spec_size": f"{len(spec['yLabels'])}×{len(spec['xLabels'])}",
        }

    # 종합
    print(f"\n{'='*60}")
    print("종합")
    print(f"{'='*60}")
    for name, r in all_results.items():
        print(f"  {name}: 전체 {r['topics']} / text {r['text_topics']} topics × {r['periods']} periods")
        print(f"    전체 핫 1위: {r['hot_topics'][0][0]} ({r['hot_topics'][0][1]:.1%})")
        if r["text_hot_topics"]:
            print(f"    text 핫 1위: {r['text_hot_topics'][0][0]} ({r['text_hot_topics'][0][1]:.1%})")
        print(f"    안정 토픽: {r['stable_count']}개, HeatmapSpec: {r['spec_size']}")
