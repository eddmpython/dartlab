"""
실험 ID: 009
실험명: topic 커버리지 매트릭스 (sections 데이터 품질 감사)

목적:
- sections DataFrame에서 topic × period 커버리지 매트릭스를 생성한다
- 어떤 topic이 어떤 기간에 데이터가 있는지 한눈에 보는 감사 도구
- HeatmapChart.svelte와 공유할 수 있는 데이터 구조를 확정한다

가설:
1. sections에서 topic별 기간 커버리지를 이진(있음/없음) 매트릭스로 추출 가능하다
2. 대부분의 topic이 90%+ 기간 커버리지를 가지지만, 일부 topic은 sparse할 것이다
3. 이 매트릭스가 데이터 품질 감사에 유용하다

방법:
1. 삼성전자 sections에서 topic × period 존재 여부 매트릭스 생성
2. 커버리지 통계 (topic별 fill rate)
3. sparse topic 식별
4. 히트맵 형태로 변환

결과:
- 삼성전자: 64 topic, 53기간. 100% 커버리지 20개, sparse(<50%) 25개
  - sparse 대부분 finance/report topic(1기간만 존재) — 정상 (sections에 merge된 것)
  - 평균 커버리지 50.6%
- SK하이닉스: 63 topic, 53기간. 100% 커버리지 21개, sparse 23개
  - 평균 커버리지 52.3%
- 가설1 채택: topic × period 이진 매트릭스 추출 가능
- 가설2 부분 채택: 핵심 docs topic은 90%+ 커버리지이나, finance/report merge topic이 sparse를 끌어올림
- 가설3 채택: 데이터 품질 감사에 유용 (sparse topic = 데이터 구멍 식별 가능)

실험일: 2026-03-19
"""

import sys

sys.path.insert(0, "src")


def sectionCoverageMatrix(company):
    """sections → topic × period 커버리지 매트릭스."""
    try:
        sections = company.sections
    except Exception:
        return None

    if sections is None:
        return None

    sec_df = sections.df if hasattr(sections, "df") else sections
    if not hasattr(sec_df, "shape"):
        return None

    # 메타 컬럼 vs 기간 컬럼 분리
    meta_cols = {"chapter", "topic", "blockType", "blockOrder", "sourceBlockOrder",
                 "textNodeType", "textStructural", "textLevel", "textPathKey",
                 "textPathVariants", "textPathVariantCount",
                 "textSemanticPathKey", "textSemanticParentPathKey",
                 "textComparablePathKey", "cadenceScope", "cadenceKey",
                 "latestAnnualPeriod", "latestQuarterlyPeriod", "nodeType"}
    period_cols = [c for c in sec_df.columns if c not in meta_cols]

    # topic별 기간 커버리지
    topics = sec_df["topic"].unique().to_list()
    coverage = {}

    for topic in topics:
        topic_rows = sec_df.filter(sec_df["topic"] == topic)
        filled = 0
        total = len(period_cols)

        for p in period_cols:
            col_vals = topic_rows[p].to_list()
            has_data = any(v is not None and v != "" for v in col_vals)
            if has_data:
                filled += 1

        coverage[topic] = {
            "filled": filled,
            "total": total,
            "rate": filled / total if total > 0 else 0,
            "rows": topic_rows.shape[0],
        }

    return coverage, period_cols, topics


def test():
    from dartlab import Company

    print("=" * 90)
    print("009: topic 커버리지 매트릭스")
    print("=" * 90)

    for code, name in [("005930", "삼성전자"), ("000660", "SK하이닉스")]:
        print(f"\n{'='*60}")
        print(f"{name} ({code})")
        print(f"{'='*60}")

        try:
            c = Company(code)
            result = sectionCoverageMatrix(c)
            if result is None:
                print("  sections 데이터 없음")
                continue

            coverage, period_cols, topics = result
            print(f"  기간: {len(period_cols)}개 ({period_cols[0]}~{period_cols[-1]})")
            print(f"  topic: {len(topics)}개")

            # 커버리지별 분류
            full = []      # 100%
            high = []      # 80%+
            medium = []    # 50-80%
            sparse = []    # <50%

            for topic, info in sorted(coverage.items(), key=lambda x: x[1]["rate"], reverse=True):
                rate = info["rate"]
                if rate >= 1.0:
                    full.append(topic)
                elif rate >= 0.8:
                    high.append(topic)
                elif rate >= 0.5:
                    medium.append(topic)
                else:
                    sparse.append(topic)

            print(f"\n  커버리지 분포:")
            print(f"    100%: {len(full)}개 topic")
            print(f"    80%+: {len(high)}개 topic")
            print(f"    50-80%: {len(medium)}개 topic")
            print(f"    <50%: {len(sparse)}개 topic")

            # sparse topic 상세
            if sparse:
                print(f"\n  sparse topic (<50% 커버리지):")
                for topic in sparse[:15]:
                    info = coverage[topic]
                    bar = "█" * int(info["rate"] * 20) + "░" * (20 - int(info["rate"] * 20))
                    print(f"    {topic:<30} {info['filled']:>3}/{info['total']} ({info['rate']*100:5.1f}%) {bar} rows={info['rows']}")

            # 전체 평균 커버리지
            avg_rate = sum(info["rate"] for info in coverage.values()) / len(coverage) if coverage else 0
            print(f"\n  전체 평균 커버리지: {avg_rate*100:.1f}%")

        except Exception as e:
            print(f"  에러: {e}")

    # 히트맵 변환 예시
    print(f"\n\n{'='*90}")
    print("히트맵 데이터 구조 예시 (삼성전자 상위 10 topic)")
    print(f"{'='*90}")

    c = Company("005930")
    result = sectionCoverageMatrix(c)
    if result:
        import json
        coverage, period_cols, _ = result
        top10 = sorted(coverage.items(), key=lambda x: x[1]["rate"])[:10]
        heatmap_data = []
        for topic, info in top10:
            heatmap_data.append({
                "topic": topic,
                "coverage": round(info["rate"], 4),
                "filled": info["filled"],
                "total": info["total"],
            })
        print(json.dumps(heatmap_data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    test()
