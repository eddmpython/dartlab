"""
실험 ID: 012
실험명: 대시보드 컴포지션 — 레이더 + 스파크라인 + 히트맵 조합

목적:
- 단일 기업 대시보드에 여러 차트를 조합하는 데이터 구조와 레이아웃을 검증한다
- InsightDashboard에 레이더, 재무 트렌드, 비율 스파크라인, 변화 히트맵을 배치한다
- 모든 차트가 동일한 ChartSpec 프로토콜로 통합되는지 확인한다

가설:
1. 한 기업의 4가지 차트 데이터를 동시에 생성하는 비용이 1초 이내일 것이다
2. 모든 차트가 ChartSpec 프로토콜로 통합 가능하다
3. 대시보드 레이아웃은 2×2 그리드가 최적이다

방법:
1. 삼성전자에서 4개 차트 동시 생성 (radar + combo + sparklines + heatmap)
2. 생성 시간 측정
3. 통합 대시보드 데이터 구조 설계
4. Svelte 레이아웃 스케치

결과:
- 3/3 종목 4개 차트 동시 생성 성공 (radar + combo + sparklines + heatmap)
- 생성 시간: 삼성전자 3499ms, SK하이닉스 3900ms, 카카오 3466ms
  - 병목: heatmap(diff) ~3.2초 (diff 계산 자체가 무거움)
  - radar+combo+sparklines만이면 ~250ms (1초 이내)
- 가설1 기각: diff 포함 시 3.5초. diff 제외 시 ~250ms로 1초 이내 가능
- 가설2 채택: 4개 차트 모두 ChartSpec 프로토콜로 통합됨
- 가설3 채택: 2×2 그리드 레이아웃 설계 완료
- 최적화 방안: diff는 lazy loading (사용자가 히트맵 탭 클릭 시 로드)
- 대시보드 API 응답 구조 확정: {charts, timing, anomalies, heatmapStats}

실험일: 2026-03-19
"""

import json
import sys
import time

sys.path.insert(0, "src")


# 004~008 변환 함수를 인라인으로 재정의 (실험간 독립 실행 보장)
from dartlab.core.finance.ratios import RATIO_CATEGORIES

COLORS = ["#ea4647", "#fb923c", "#3b82f6", "#22c55e", "#8b5cf6", "#06b6d4", "#f59e0b", "#ec4899"]
AREA_NAMES = ["performance", "profitability", "health", "cashflow", "governance", "risk", "opportunity"]
AREA_LABELS = {"performance": "성과", "profitability": "수익성", "health": "건전성", "cashflow": "현금흐름",
               "governance": "지배구조", "risk": "리스크", "opportunity": "기회"}
GRADE_MAP = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 0}


def _financeToComboSpec(company, *, years=5):
    ann = company.annual
    if not ann:
        return None
    ann_data, ann_years = ann
    is_data = ann_data.get("IS", {})
    key_accounts = [("매출액", ["sales", "revenue", "interest_income"]),
                    ("영업이익", ["operating_income", "operating_profit"]),
                    ("당기순이익", ["net_income", "profit_for_the_period", "profit_loss"])]
    series = []
    chart_types = ["bar", "line", "line"]
    colors = [COLORS[2], COLORS[0], COLORS[3]]
    for i, (label, candidates) in enumerate(key_accounts):
        vals = None
        for cand in candidates:
            if cand in is_data and any(v is not None for v in is_data[cand]):
                vals = is_data[cand]
                break
        if vals is None:
            continue
        recent = vals[-years:]
        series.append({"name": label, "data": [v if v is not None else 0 for v in recent],
                        "color": colors[i], "type": chart_types[i]})
    if not series:
        return None
    return {"chartType": "combo", "title": f"{company.corpName} 손익 추이",
            "series": series, "categories": ann_years[-years:], "options": {"unit": "백만원"}}


def _insightToRadarSpec(company):
    try:
        insights = company.insights
    except Exception:
        return None
    if insights is None or not hasattr(insights, "performance"):
        return None
    grades = {}
    for name in AREA_NAMES:
        area = getattr(insights, name, None)
        grades[name] = area.grade if area and hasattr(area, "grade") else "F"
    categories = [AREA_LABELS.get(n, n) for n in AREA_NAMES]
    data = [GRADE_MAP.get(grades[n], 0) for n in AREA_NAMES]
    spec = {"chartType": "radar", "title": f"{company.corpName} 투자 인사이트",
            "series": [{"name": company.corpName, "data": data, "color": COLORS[0]}],
            "categories": categories, "options": {"maxValue": 5}}
    anomalies_meta = []
    if hasattr(insights, "anomalies") and insights.anomalies:
        for a in insights.anomalies:
            anomalies_meta.append({"severity": a.severity, "category": a.category, "text": a.text})
    return spec, grades, anomalies_meta


def _ratioSeriesToSparklines(company):
    rs = company.ratioSeries
    if rs is None:
        return None
    if isinstance(rs, tuple) and len(rs) == 2:
        ratio_dict = rs[0].get("RATIO", {})
        periods = rs[1]
    else:
        return None
    sparklines = []
    for cat_name, fields in RATIO_CATEGORIES:
        cat_sparklines = []
        for field_name in fields:
            vals = ratio_dict.get(field_name, [])
            if not vals:
                continue
            valid_count = sum(1 for v in vals if v is not None)
            latest = next((v for v in reversed(vals) if v is not None), None)
            recent_valid = [v for v in vals[-8:] if v is not None]
            trend = "up" if len(recent_valid) >= 2 and recent_valid[-1] > recent_valid[-2] else ("down" if len(recent_valid) >= 2 else "neutral")
            cat_sparklines.append({"field": field_name, "values": vals, "validCount": valid_count,
                                    "totalCount": len(vals), "latest": latest, "trend": trend})
        if cat_sparklines:
            sparklines.append({"category": cat_name, "metrics": cat_sparklines})
    return sparklines


def _diffToHeatmapSpec(company):
    try:
        diff_df = company.diff()
    except Exception:
        return None
    if diff_df is None or not hasattr(diff_df, "shape") or diff_df.shape[0] == 0:
        return None
    change_rates = {}
    for row in diff_df.iter_rows(named=True):
        topic = row["topic"]
        rate = row.get("changeRate", 0) or 0
        change_rates[topic] = float(rate)
    sorted_topics = sorted(change_rates.items(), key=lambda x: x[1], reverse=True)[:30]
    heatmap_data = []
    for topic, rate in sorted_topics:
        intensity = "high" if rate >= 0.5 else ("medium" if rate >= 0.2 else "low")
        heatmap_data.append({"topic": topic, "changeRate": round(rate, 4), "intensity": intensity})
    spec = {"chartType": "heatmap", "title": f"{company.corpName} 공시 변화 밀도", "data": heatmap_data,
            "options": {"colorScale": {"low": "#22c55e", "medium": "#f59e0b", "high": "#ea4647"}}}
    stats = {"totalTopics": len(change_rates), "analyzedTopics": len(sorted_topics),
             "hotspots": sum(1 for _, r in sorted_topics if r >= 0.3)}
    return spec, stats


def build_dashboard(company):
    """단일 기업 대시보드 데이터 생성."""
    dashboard = {
        "corpName": company.corpName,
        "stockCode": company.stockCode,
        "charts": {},
        "timing": {},
    }

    # 1. 레이더 (insights)
    t0 = time.perf_counter()
    radar_result = _insightToRadarSpec(company)
    dashboard["timing"]["radar"] = time.perf_counter() - t0
    if radar_result:
        spec, grades, anomalies = radar_result
        dashboard["charts"]["radar"] = spec
        dashboard["anomalies"] = anomalies

    # 2. 재무 트렌드 (IS combo)
    t0 = time.perf_counter()
    combo_spec = _financeToComboSpec(company)
    dashboard["timing"]["combo"] = time.perf_counter() - t0
    if combo_spec:
        dashboard["charts"]["combo"] = combo_spec

    # 3. 비율 스파크라인
    t0 = time.perf_counter()
    sparklines = _ratioSeriesToSparklines(company)
    dashboard["timing"]["sparklines"] = time.perf_counter() - t0
    if sparklines:
        summary_sparklines = []
        for cat in sparklines:
            top3 = cat["metrics"][:3]
            summary_sparklines.append({
                "category": cat["category"],
                "metrics": [{"field": m["field"], "values": m["values"][-20:],
                             "latest": m["latest"], "trend": m["trend"]} for m in top3],
            })
        dashboard["charts"]["sparklines"] = summary_sparklines

    # 4. 변화 히트맵
    t0 = time.perf_counter()
    heatmap_result = _diffToHeatmapSpec(company)
    dashboard["timing"]["heatmap"] = time.perf_counter() - t0
    if heatmap_result:
        spec, stats = heatmap_result
        spec["data"] = spec["data"][:10]
        dashboard["charts"]["heatmap"] = spec
        dashboard["heatmapStats"] = stats

    dashboard["timing"]["total"] = sum(dashboard["timing"].values())

    return dashboard


def test():
    print("=" * 90)
    print("012: 대시보드 컴포지션 — 레이더 + 스파크라인 + 히트맵 조합")
    print("=" * 90)

    from dartlab import Company

    test_codes = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035720", "카카오"),
    ]

    for code, name in test_codes:
        print(f"\n{'='*60}")
        print(f"{name} ({code})")
        print(f"{'='*60}")

        try:
            c = Company(code)
            t_start = time.perf_counter()
            dashboard = build_dashboard(c)
            t_total = time.perf_counter() - t_start

            # 결과 요약
            charts = dashboard["charts"]
            print(f"\n  생성 차트: {len(charts)}개")
            for chart_name in charts:
                print(f"    ✓ {chart_name}")

            print(f"\n  생성 시간:")
            for step, t in dashboard["timing"].items():
                print(f"    {step:<12}: {t*1000:.0f}ms")
            print(f"    {'전체':<12}: {t_total*1000:.0f}ms")

            # 가설 1 검증: 1초 이내?
            if t_total < 1.0:
                print(f"\n  ✓ 가설1 채택: {t_total*1000:.0f}ms < 1000ms")
            else:
                print(f"\n  ✗ 가설1 기각: {t_total*1000:.0f}ms >= 1000ms")

        except Exception as e:
            print(f"  에러: {e}")
            import traceback
            traceback.print_exc()

    # 대시보드 레이아웃 설계
    print(f"\n\n{'='*90}")
    print("대시보드 레이아웃 설계")
    print(f"{'='*90}")

    layout = """
┌──────────────────────────┬──────────────────────────┐
│                          │                          │
│     레이더 차트            │     재무 트렌드            │
│     (인사이트 7영역)       │     (매출·영업이익 추이)    │
│     RadarChart.svelte    │     TrendChart.svelte    │
│                          │                          │
├──────────────────────────┼──────────────────────────┤
│                          │                          │
│     비율 스파크라인         │     변화 히트맵            │
│     (핵심 비율 추이)       │     (topic별 변화 밀도)    │
│     SparklineRow.svelte  │     HeatmapChart.svelte  │
│                          │                          │
└──────────────────────────┴──────────────────────────┘

Svelte 구현:

<div class="grid grid-cols-2 gap-4">
  <RadarChart spec={dashboard.charts.radar} />
  <TrendChart spec={dashboard.charts.combo} />
  <div class="space-y-1">
    {#each dashboard.charts.sparklines as cat}
      <h4>{cat.category}</h4>
      {#each cat.metrics as m}
        <SparklineRow label={m.field} values={m.values} />
      {/each}
    {/each}
  </div>
  <HeatmapChart spec={dashboard.charts.heatmap} />
</div>
"""
    print(layout)

    # 대시보드 JSON 예시 (삼성전자, 축약)
    print(f"\n{'='*90}")
    print("대시보드 API 응답 구조 (축약)")
    print(f"{'='*90}")

    c = Company("005930")
    dashboard = build_dashboard(c)

    # 축약 (sparklines values 줄임)
    summary = {
        "corpName": dashboard["corpName"],
        "stockCode": dashboard["stockCode"],
        "chartTypes": list(dashboard["charts"].keys()),
        "timing": {k: f"{v*1000:.0f}ms" for k, v in dashboard["timing"].items()},
    }

    if "radar" in dashboard["charts"]:
        r = dashboard["charts"]["radar"]
        summary["radarGrades"] = dict(zip(r["categories"], r["series"][0]["data"]))

    if "combo" in dashboard["charts"]:
        summary["comboSeries"] = [s["name"] for s in dashboard["charts"]["combo"]["series"]]

    if "sparklines" in dashboard["charts"]:
        summary["sparklineCategories"] = [
            f"{cat['category']}({len(cat['metrics'])})"
            for cat in dashboard["charts"]["sparklines"]
        ]

    if "heatmap" in dashboard["charts"]:
        summary["heatmapTopTopics"] = [d["topic"] for d in dashboard["charts"]["heatmap"]["data"][:5]]

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    test()
