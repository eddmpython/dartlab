"""
실험 ID: 010
실험명: 기간 타임라인 변화 마커·이벤트 플래그 오버레이

목적:
- 기간 타임라인에 변화 마커와 이벤트 플래그를 오버레이하는 데이터 구조를 검증한다
- diff 데이터에서 기간별 변화 강도를 추출하여 TimelineBar 컴포넌트에 시각적 힌트를 제공한다
- 연도별 주요 이벤트(대규모 변화, anomaly)를 타임라인에 표시하는 구조를 확정한다

가설:
1. diff 데이터에서 기간별 전체 changeRate를 집계하여 타임라인 마커를 만들 수 있다
2. anomalies와 결합하여 기간별 "사건 밀도"를 계산할 수 있다
3. 이 데이터가 기존 TimelineBar.svelte에 props로 전달 가능한 형태다

방법:
1. 삼성전자 diff 데이터에서 기간별 변화 집계
2. insights anomalies에서 기간 정보 추출 (가능한 경우)
3. 타임라인 annotation 데이터 구조 설계
4. 다종목 검증

결과:
- 3/3 종목 타임라인 annotation 생성 성공
- 삼성전자: 53기간, 평균 fill rate 40.3%, 완전(≥90%) 7기간, 부족(<30%) 32기간
- 관찰: 메타 컬럼(textPathKey 등)이 기간 컬럼에 섞임 → 기간 컬럼 필터링 개선 필요
  - 실제 기간 컬럼은 YYYYQN 패턴으로 필터해야 함
  - 현재는 메타/기간 구분이 set 기반이라 새 메타 컬럼 추가 시 누락 위험
- hotspot: companyOverview가 모든 종목에서 changeRate 1.0 (매 기간 변경)
- 가설1 채택: 기간별 fill rate 집계 가능 (정확도는 컬럼 필터 개선 후)
- 가설2 부분 채택: anomalies에 기간 정보가 없어 결합 불가 → diff 핫스팟으로 대체
- 가설3 채택: TimelineBar props 형태 전달 가능

실험일: 2026-03-19
"""

import json
import sys

sys.path.insert(0, "src")


def timelineAnnotations(company):
    """diff + insights → 타임라인 annotation 데이터 생성."""
    # diff에서 기간별 변화 집계
    try:
        diff_df = company.diff()
    except Exception:
        diff_df = None

    period_events = {}

    if diff_df is not None and hasattr(diff_df, "shape") and diff_df.shape[0] > 0:
        # diff columns: chapter, topic, periods, changed, stable, changeRate
        for row in diff_df.iter_rows(named=True):
            rate = row.get("changeRate", 0) or 0
            changed = row.get("changed", 0) or 0
            if rate > 0.1:  # 의미 있는 변화만
                # periods는 해당 topic이 커버하는 기간 수
                period_events.setdefault("_global", []).append({
                    "topic": row["topic"],
                    "changeRate": float(rate),
                    "changed": int(changed),
                })

    # sections에서 기간별 데이터 존재 여부
    try:
        sections = company.sections
        sec_df = sections.df if hasattr(sections, "df") else sections
    except Exception:
        sec_df = None

    period_stats = {}
    if sec_df is not None and hasattr(sec_df, "shape"):
        meta_cols = {"chapter", "topic", "blockType", "blockOrder", "sourceBlockOrder",
                     "textNodeType", "textStructural", "textLevel", "textPathKey",
                     "textPathVariants", "textPathVariantCount",
                     "textSemanticPathKey", "textSemanticParentPathKey",
                     "textComparablePathKey", "cadenceScope", "cadenceKey",
                     "latestAnnualPeriod", "latestQuarterlyPeriod", "nodeType"}
        period_cols = [c for c in sec_df.columns if c not in meta_cols]

        for p in period_cols:
            col = sec_df[p].to_list()
            filled = sum(1 for v in col if v is not None and v != "")
            total = len(col)
            period_stats[p] = {
                "period": p,
                "filled": filled,
                "total": total,
                "fillRate": filled / total if total > 0 else 0,
            }

    # 타임라인 annotation 구성
    annotations = []
    for period, stats in sorted(period_stats.items(), reverse=True):
        annotation = {
            "period": period,
            "fillRate": round(stats["fillRate"], 4),
            "dataPoints": stats["filled"],
            "markers": [],
        }

        # fill rate에 따른 마커
        if stats["fillRate"] < 0.3:
            annotation["markers"].append({
                "type": "warning",
                "text": "데이터 부족",
            })
        elif stats["fillRate"] >= 0.9:
            annotation["markers"].append({
                "type": "complete",
                "text": "데이터 충분",
            })

        annotations.append(annotation)

    # 전체 변화 핫스팟 (상위 5개 topic)
    global_events = period_events.get("_global", [])
    hotspots = sorted(global_events, key=lambda x: x["changeRate"], reverse=True)[:5]

    return {
        "annotations": annotations,
        "hotspots": hotspots,
        "periodCount": len(period_stats),
        "avgFillRate": sum(s["fillRate"] for s in period_stats.values()) / len(period_stats) if period_stats else 0,
    }


def test():
    from dartlab import Company

    test_codes = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035720", "카카오"),
    ]

    print("=" * 90)
    print("010: 기간 타임라인 변화 마커·이벤트 플래그")
    print("=" * 90)

    for code, name in test_codes:
        print(f"\n{'='*60}")
        print(f"{name} ({code})")
        print(f"{'='*60}")

        try:
            c = Company(code)
            result = timelineAnnotations(c)

            print(f"  기간 수: {result['periodCount']}개")
            print(f"  평균 fill rate: {result['avgFillRate']*100:.1f}%")

            # 기간별 fill rate 분포
            annotations = result["annotations"]
            complete = sum(1 for a in annotations if a["fillRate"] >= 0.9)
            sparse = sum(1 for a in annotations if a["fillRate"] < 0.3)
            print(f"  완전(≥90%): {complete}개 기간")
            print(f"  부족(<30%): {sparse}개 기간")

            # 최근 5개 기간 상세
            print(f"\n  최근 5개 기간:")
            for a in annotations[:5]:
                bar = "█" * int(a["fillRate"] * 20) + "░" * (20 - int(a["fillRate"] * 20))
                markers = ", ".join(m["type"] for m in a["markers"])
                marker_str = f" [{markers}]" if markers else ""
                print(f"    {a['period']:<12} {a['fillRate']*100:5.1f}% {bar} pts={a['dataPoints']}{marker_str}")

            # 핫스팟
            if result["hotspots"]:
                print(f"\n  변화 핫스팟 (상위 5):")
                for h in result["hotspots"]:
                    print(f"    {h['topic']:<30} changeRate={h['changeRate']:.4f}")

        except Exception as e:
            print(f"  에러: {e}")

    # TimelineBar props 예시
    print(f"\n\n{'='*90}")
    print("TimelineBar annotation props 예시")
    print(f"{'='*90}")

    c = Company("005930")
    result = timelineAnnotations(c)
    # 최근 8개 기간만
    props = {
        "annotations": result["annotations"][:8],
        "hotspots": result["hotspots"],
    }
    print(json.dumps(props, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    test()
