"""
실험 ID: 008
실험명: topic × period 텍스트 변화 밀도 히트맵

목적:
- diff() 데이터를 히트맵 ChartSpec으로 변환하는 파이프라인을 검증한다
- 어떤 topic이 어떤 기간에 크게 바뀌었는지 시각적으로 조감한다
- HeatmapChart.svelte가 소비할 정확한 데이터 구조를 확정한다

가설:
1. diff() DataFrame에서 topic별 changeRate를 히트맵 데이터로 변환 가능하다
2. changeRate > 0.3인 핫스팟이 전체의 20% 이하일 것이다
3. 3개 종목에서 동일한 변환 로직이 작동한다

방법:
1. 삼성전자 diff() 데이터에서 topic × period 변화율 매트릭스 생성
2. 히트맵 ChartSpec 변환
3. 핫스팟 분석 (높은 changeRate)
4. 다종목 비교

결과:
- 3/3 종목 히트맵 ChartSpec 생성 성공
- 삼성전자: 41 topic, 핫스팟(≥0.3) 13개(43%), 최대 changeRate 1.0
- SK하이닉스: 40 topic, 핫스팟 7개(23%), 평균 changeRate 0.206
- 카카오: 43 topic, 핫스팟 10개(33%), 평균 changeRate 0.292
- 가설1 채택: diff DataFrame에서 topic별 changeRate 히트맵 변환 성공
- 가설2 기각: 핫스팟 비율이 삼성전자 43%로 예상(20%)보다 높음
  - companyOverview, dividend 등 매 기간 변경되는 topic이 많음
- 가설3 채택: 3/3 종목 동일 변환 로직 작동

실험일: 2026-03-19
"""

import json
import sys

sys.path.insert(0, "src")

COLORS = ["#ea4647", "#fb923c", "#3b82f6", "#22c55e", "#8b5cf6", "#06b6d4", "#f59e0b", "#ec4899"]


def diffToHeatmapSpec(company):
    """diff() → heatmap ChartSpec 변환."""
    try:
        diff_df = company.diff()
    except Exception:
        return None

    if diff_df is None or not hasattr(diff_df, "shape") or diff_df.shape[0] == 0:
        return None

    # diff columns: chapter, topic, periods, changed, stable, changeRate
    topics = diff_df["topic"].unique().to_list()
    change_rates = {}

    for row in diff_df.iter_rows(named=True):
        topic = row["topic"]
        rate = row.get("changeRate", 0)
        if rate is None:
            rate = 0
        change_rates[topic] = float(rate)

    # 상위 30개 topic만 (히트맵 가시성)
    sorted_topics = sorted(change_rates.items(), key=lambda x: x[1], reverse=True)[:30]

    # 히트맵 데이터: [{topic, changeRate, category}]
    heatmap_data = []
    for topic, rate in sorted_topics:
        # 변화 강도 분류
        if rate >= 0.5:
            intensity = "high"
        elif rate >= 0.2:
            intensity = "medium"
        else:
            intensity = "low"

        heatmap_data.append({
            "topic": topic,
            "changeRate": round(rate, 4),
            "intensity": intensity,
        })

    spec = {
        "chartType": "heatmap",
        "title": f"{company.corpName} 공시 변화 밀도",
        "data": heatmap_data,
        "options": {
            "colorScale": {
                "low": "#22c55e",     # green = 안정
                "medium": "#f59e0b",  # amber = 주의
                "high": "#ea4647",    # red = 변화 큼
            },
        },
    }

    stats = {
        "totalTopics": len(topics),
        "analyzedTopics": len(sorted_topics),
        "hotspots": sum(1 for _, r in sorted_topics if r >= 0.3),
        "avgChangeRate": sum(r for _, r in sorted_topics) / len(sorted_topics) if sorted_topics else 0,
        "maxChangeRate": sorted_topics[0][1] if sorted_topics else 0,
    }

    return spec, stats


def test():
    from dartlab import Company

    test_codes = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035720", "카카오"),
    ]

    print("=" * 90)
    print("008: topic × period 텍스트 변화 밀도 히트맵")
    print("=" * 90)

    for code, name in test_codes:
        print(f"\n{'='*60}")
        print(f"{name} ({code})")
        print(f"{'='*60}")

        try:
            c = Company(code)
            result = diffToHeatmapSpec(c)
            if result is None:
                print("  diff 데이터 없음")
                continue

            spec, stats = result
            print(f"  전체 topic: {stats['totalTopics']}개")
            print(f"  분석 대상: {stats['analyzedTopics']}개 (상위 30)")
            print(f"  핫스팟(≥0.3): {stats['hotspots']}개 ({stats['hotspots']/stats['analyzedTopics']*100:.0f}%)")
            print(f"  평균 changeRate: {stats['avgChangeRate']:.4f}")
            print(f"  최대 changeRate: {stats['maxChangeRate']:.4f}")

            # 상위 10 핫스팟
            print(f"\n  상위 10 변화 topic:")
            for item in spec["data"][:10]:
                bar = "█" * int(item["changeRate"] * 20)
                print(f"    {item['topic']:<30} {item['changeRate']:.4f} {bar} [{item['intensity']}]")

        except Exception as e:
            print(f"  에러: {e}")

    # ChartSpec JSON
    print(f"\n\n{'='*90}")
    print("히트맵 ChartSpec 예시 (삼성전자 상위 5)")
    print(f"{'='*90}")

    c = Company("005930")
    result = diffToHeatmapSpec(c)
    if result:
        spec, _ = result
        spec["data"] = spec["data"][:5]  # 예시용 축소
        print(json.dumps(spec, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    test()
