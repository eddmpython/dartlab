"""
실험 ID: 005
실험명: 비율 시계열 스파크라인 데이터 구조 검증

목적:
- ratioSeries 30+ 비율 지표를 스파크라인 데이터로 변환하는 파이프라인을 검증한다
- 카테고리별 그룹핑과 null 처리가 올바른지 확인한다
- SparklineRow.svelte가 소비할 정확한 데이터 구조를 확정한다

가설:
1. ratioSeries tuple에서 카테고리별 비율 시계열을 추출할 수 있다
2. 대부분의 비율이 10개 이상의 유효 데이터 포인트를 가진다
3. 5개 종목에서 동일한 변환 로직이 작동한다

방법:
1. 삼성전자 ratioSeries에서 6개 카테고리 × 30+ 비율 추출
2. 각 비율의 유효 데이터 포인트 수, 최신값, 추세 방향 분석
3. SparklineRow props 형태로 변환
4. 5개 종목에서 일관성 검증

결과:
- 삼성전자: 35개 비율 전부 39/39 유효 데이터. 전부 10+ 포인트.
- SK하이닉스: 35개 비율, 대부분 39/39. 일부 성장률 27-35/39.
- 카카오/현대차/LG화학: 동일 구조, 유효 데이터 수 다양
- 가설1 채택: 6개 카테고리 × 30+ 비율 추출 성공
- 가설2 채택: 대부분 비율이 35-39개 유효 포인트 (10개 이상)
- 가설3 채택: 5/5 종목 동일 변환 로직 작동
- SparklineRow props: {label, values[39], color, width, height}

실험일: 2026-03-19
"""

import sys

sys.path.insert(0, "src")

from dartlab.engines.common.finance.ratios import RATIO_CATEGORIES


def ratioSeriesToSparklines(company):
    """ratioSeries → 스파크라인 데이터 배열 변환."""
    rs = company.ratioSeries
    if rs is None:
        return None

    # ratioSeries는 tuple: (dict{'RATIO': {snakeId: [vals]}}, periods_list)
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
            latest = None
            for v in reversed(vals):
                if v is not None:
                    latest = v
                    break

            # 추세 계산
            recent_valid = [v for v in vals[-8:] if v is not None]
            if len(recent_valid) >= 2:
                trend = "up" if recent_valid[-1] > recent_valid[-2] else "down"
            else:
                trend = "neutral"

            cat_sparklines.append({
                "field": field_name,
                "values": vals,
                "validCount": valid_count,
                "totalCount": len(vals),
                "latest": latest,
                "trend": trend,
                "periods": periods,
            })

        if cat_sparklines:
            sparklines.append({
                "category": cat_name,
                "metrics": cat_sparklines,
            })

    return sparklines


def test():
    from dartlab import Company

    test_codes = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035720", "카카오"),
        ("005380", "현대차"),
        ("051910", "LG화학"),
    ]

    print("=" * 90)
    print("005: 비율 시계열 스파크라인 데이터 구조 검증")
    print("=" * 90)

    for code, name in test_codes:
        print(f"\n{'='*60}")
        print(f"{name} ({code})")
        print(f"{'='*60}")

        try:
            c = Company(code)
            sparklines = ratioSeriesToSparklines(c)
            if sparklines is None:
                print("  ratioSeries 없음")
                continue

            total_metrics = 0
            total_valid = 0
            for cat in sparklines:
                print(f"\n  [{cat['category']}]")
                for m in cat["metrics"]:
                    total_metrics += 1
                    coverage = f"{m['validCount']}/{m['totalCount']}"
                    latest_str = f"{m['latest']:.2f}" if m['latest'] is not None else "—"
                    trend_symbol = {"up": "▲", "down": "▼", "neutral": "—"}[m["trend"]]
                    print(f"    {m['field']:<28} {coverage:>8}  latest={latest_str:>10}  {trend_symbol}")
                    if m["validCount"] >= 10:
                        total_valid += 1

            print(f"\n  요약: {total_metrics}개 비율, {total_valid}개가 10+ 데이터 포인트")

        except Exception as e:
            print(f"  에러: {e}")

    # Svelte props 예시 출력
    print(f"\n\n{'='*90}")
    print("SparklineRow props 예시 (삼성전자 ROE)")
    print(f"{'='*90}")

    c = Company("005930")
    sparklines = ratioSeriesToSparklines(c)
    if sparklines:
        for cat in sparklines:
            for m in cat["metrics"]:
                if m["field"] == "roe":
                    import json
                    svelte_props = {
                        "label": "ROE",
                        "values": m["values"],
                        "color": "#ea4647",
                        "width": 120,
                        "height": 32,
                    }
                    print(json.dumps(svelte_props, ensure_ascii=False, indent=2))
                    break


if __name__ == "__main__":
    test()
