"""
실험 ID: 006
실험명: 인사이트 등급 레이더 차트 데이터 변환 검증

목적:
- 7영역 인사이트 등급(A~F)을 레이더 ChartSpec으로 변환하는 파이프라인을 검증한다
- 다종목에서 등급 분포와 레이더 형태를 확인한다
- RadarChart.svelte가 소비할 정확한 데이터 구조를 확정한다

가설:
1. 7영역 등급을 수치(A=5, B=4, C=3, D=2, F=0)로 변환하여 레이더 차트를 만들 수 있다
2. 다종목에서 등급 분포가 다양하여 레이더 차트가 시각적으로 구분 가능하다
3. anomalies 정보를 레이더 차트 위에 마커로 표시할 수 있다

방법:
1. 10개 종목 인사이트 등급 수집
2. 레이더 ChartSpec 변환
3. 등급 분포 통계
4. 다중 종목 비교 레이더 (overlay)

결과:
- 10/10 종목 레이더 ChartSpec 생성 성공
- 등급 분포: 성과 A:2/F:4, 수익성 A:5, 건전성 A:2/C:4, 현금흐름 B:7, 지배구조 B:7
- 레이더 형태: 삼성전자[5,5,5,4,4,4,5] vs 카카오[0,3,3,4,4,2,3] — 명확히 구분 가능
- 비교 레이더(3종목 overlay) ChartSpec 생성 성공
- anomalies: 카카오 3개, 현대차 1개(영업CF 적자) 등 다양
- 가설1 채택: 7영역 수치 변환 완벽 작동
- 가설2 채택: 종목별 레이더 형태가 시각적으로 명확히 구분됨
- 가설3 채택: anomalies 메타데이터 추출 가능

실험일: 2026-03-19
"""

import json
import sys

sys.path.insert(0, "src")


GRADE_MAP = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 0}
AREA_NAMES = ["performance", "profitability", "health", "cashflow", "governance", "risk", "opportunity"]
AREA_LABELS = {
    "performance": "성과",
    "profitability": "수익성",
    "health": "건전성",
    "cashflow": "현금흐름",
    "governance": "지배구조",
    "risk": "리스크",
    "opportunity": "기회",
}
COLORS = ["#ea4647", "#fb923c", "#3b82f6", "#22c55e", "#8b5cf6", "#06b6d4", "#f59e0b", "#ec4899"]


def insightToRadarSpec(company, *, use_korean=True):
    """인사이트 등급 → radar ChartSpec 변환."""
    try:
        insights = company.insights
    except Exception:
        return None

    if insights is None or not hasattr(insights, "performance"):
        return None

    grades = {}
    for name in AREA_NAMES:
        area = getattr(insights, name, None)
        if area and hasattr(area, "grade"):
            grades[name] = area.grade
        else:
            grades[name] = "F"

    categories = [AREA_LABELS.get(n, n) if use_korean else n for n in AREA_NAMES]
    data = [GRADE_MAP.get(grades[n], 0) for n in AREA_NAMES]

    spec = {
        "chartType": "radar",
        "title": f"{company.corpName} 투자 인사이트",
        "series": [{"name": company.corpName, "data": data, "color": COLORS[0]}],
        "categories": categories,
        "options": {"maxValue": 5},
    }

    # anomalies 메타데이터
    anomalies_meta = []
    if hasattr(insights, "anomalies") and insights.anomalies:
        for anom in insights.anomalies:
            anomalies_meta.append({
                "severity": anom.severity,
                "category": anom.category,
                "text": anom.text,
            })

    return spec, grades, anomalies_meta


def compare_radar(companies):
    """다종목 비교 레이더 ChartSpec."""
    series = []
    for i, c in enumerate(companies):
        result = insightToRadarSpec(c, use_korean=True)
        if result is None:
            continue
        spec, grades, _ = result
        series.append({
            "name": c.corpName,
            "data": spec["series"][0]["data"],
            "color": COLORS[i % len(COLORS)],
        })

    if not series:
        return None

    return {
        "chartType": "radar",
        "title": "기업 비교 인사이트",
        "series": series,
        "categories": [AREA_LABELS[n] for n in AREA_NAMES],
        "options": {"maxValue": 5},
    }


def test():
    from dartlab import Company

    test_codes = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("373220", "LG에너지솔루션"),
        ("035720", "카카오"),
        ("005380", "현대차"),
        ("068270", "셀트리온"),
        ("035420", "NAVER"),
        ("051910", "LG화학"),
        ("006400", "삼성SDI"),
        ("028260", "삼성물산"),
    ]

    print("=" * 90)
    print("006: 인사이트 등급 레이더 차트 데이터 변환 검증")
    print("=" * 90)

    all_grades = {}
    success = 0
    fail = 0

    for code, name in test_codes:
        print(f"\n--- {name} ({code}) ---")
        try:
            c = Company(code)
            result = insightToRadarSpec(c)
            if result is None:
                print("  인사이트 데이터 없음")
                fail += 1
                continue

            spec, grades, anomalies = result
            grade_str = " ".join(f"{AREA_LABELS[k]}={v}" for k, v in grades.items())
            print(f"  등급: {grade_str}")
            print(f"  레이더 데이터: {spec['series'][0]['data']}")
            if anomalies:
                print(f"  이상치: {len(anomalies)}개")
                for a in anomalies[:3]:
                    print(f"    [{a['severity']}] {a['text']}")

            all_grades[name] = grades
            success += 1

        except Exception as e:
            print(f"  에러: {e}")
            fail += 1

    # 등급 분포 통계
    print(f"\n\n{'='*90}")
    print("등급 분포 통계")
    print(f"{'='*90}")

    if all_grades:
        for area in AREA_NAMES:
            grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
            for company_grades in all_grades.values():
                g = company_grades.get(area, "F")
                grade_counts[g] = grade_counts.get(g, 0) + 1
            dist = " ".join(f"{g}:{n}" for g, n in grade_counts.items() if n > 0)
            print(f"  {AREA_LABELS[area]:<8}: {dist}")

    # 비교 레이더 ChartSpec 예시
    print(f"\n\n{'='*90}")
    print("비교 레이더 ChartSpec (삼성전자 vs SK하이닉스 vs 카카오)")
    print(f"{'='*90}")

    companies = [Company(c) for c in ["005930", "000660", "035720"]]
    compare_spec = compare_radar(companies)
    if compare_spec:
        print(json.dumps(compare_spec, ensure_ascii=False, indent=2))

    # 요약
    print(f"\n\n{'='*90}")
    print(f"결과 요약: {success}/{len(test_codes)} 성공, {fail} 실패")
    print(f"{'='*90}")


if __name__ == "__main__":
    test()
