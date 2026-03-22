"""
실험 ID: 013
실험명: ChartSpec → Plotly 왕복 검증

목적:
- chart.py에 추가한 spec_xxx() 8개 함수와 chart_from_spec() 범용 변환기를 검증한다
- 10종목에서 auto_chart()가 데이터 가용성에 따라 올바른 ChartSpec을 생성하는지 확인한다
- ChartSpec → Plotly Figure 변환이 에러 없이 완료되는지 확인한다

가설:
1. 10종목 모두에서 auto_chart()가 최소 3개 ChartSpec을 생성할 것이다
2. 모든 ChartSpec이 chart_from_spec()으로 Plotly Figure 변환에 성공할 것이다
3. spec_xxx() 8개 중 revenue_trend, balance_sheet, profitability는 전 종목에서 성공할 것이다

방법:
1. 10개 종목에서 auto_chart() 실행 → 생성된 spec 개수 기록
2. 각 spec에 대해 chart_from_spec() 실행 → 성공/실패 기록
3. spec_xxx() 개별 함수도 전수 검증
4. ChartSpec JSON 구조 유효성 확인 (chartType, series, categories 필수)

결과:
- 10/10 종목 auto_chart() 성공. 최소 6개, 최대 7개, 평균 6.8개 ChartSpec 생성
- 35/35 chart_from_spec() 왕복 변환 성공 (실패 0건)
- spec_xxx() 개별 함수 성공률:
  - 100%: revenue_trend, cashflow, profitability, insight_radar, ratio_sparklines, diff_heatmap (6개)
  - 80%: balance_sheet (금융업 2종목 current_assets 미보유)
  - 0%: dividend (report.dividend DataFrame 구조 불일치 → 추후 개선)
- ChartSpec JSON 크기: 전체 ~11KB (삼성전자 기준). sparkline 5.2KB 최대, radar 295B 최소
- 가설1 채택: 최소 6개 ≥ 3개 기준 충족
- 가설2 채택: chart_from_spec() 실패 0건 (radar fillcolor → rgba 변환으로 해결)
- 가설3 부분 채택: 전종목 100% 함수 6개, balance_sheet 80%, dividend 0%

실험일: 2026-03-19
"""

import json
import sys
import time

sys.path.insert(0, "src")


def validate_spec(spec: dict) -> list[str]:
    """ChartSpec 구조 유효성 검증. 문제 리스트 반환."""
    issues = []
    if "chartType" not in spec:
        issues.append("chartType 누락")
    if "series" not in spec:
        issues.append("series 누락")
    if "categories" not in spec:
        issues.append("categories 누락")
    if "title" not in spec:
        issues.append("title 누락")
    if "meta" not in spec:
        issues.append("meta 누락")
    else:
        meta = spec["meta"]
        if "source" not in meta:
            issues.append("meta.source 누락")
    # JSON 직렬화 가능 확인
    try:
        json.dumps(spec, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        issues.append(f"JSON 직렬화 실패: {e}")
    return issues


def test():
    print("=" * 90)
    print("013: ChartSpec → Plotly 왕복 검증")
    print("=" * 90)

    from dartlab import Company
    from dartlab.tools.chart import (
        _SPEC_GENERATORS,
        auto_chart,
        chart_from_spec,
    )

    test_codes = [
        ("005930", "삼성전자"),
        ("000660", "SK하이닉스"),
        ("035720", "카카오"),
        ("051910", "LG화학"),
        ("006400", "삼성SDI"),
        ("005380", "현대자동차"),
        ("035420", "NAVER"),
        ("000270", "기아"),
        ("105560", "KB금융"),
        ("055550", "신한지주"),
    ]

    # 1. auto_chart() 전종목 검증
    print("\n[1] auto_chart() 전종목 검증")
    print("-" * 60)

    results = {}
    for code, name in test_codes:
        try:
            c = Company(code)
            t0 = time.perf_counter()
            specs = auto_chart(c)
            elapsed = time.perf_counter() - t0

            chart_types = [s["chartType"] for s in specs]
            results[code] = {"name": name, "count": len(specs), "types": chart_types, "elapsed": elapsed}

            print(f"\n  {name} ({code}): {len(specs)}개 차트, {elapsed*1000:.0f}ms")
            for s in specs:
                issues = validate_spec(s)
                status = "✓" if not issues else f"✗ {issues}"
                print(f"    {s['chartType']:<12} {s.get('title', '')[:30]:<32} {status}")

        except Exception as e:
            results[code] = {"name": name, "count": 0, "types": [], "error": str(e)}
            print(f"\n  {name} ({code}): 에러 — {e}")

    # 2. chart_from_spec() 왕복 검증
    print(f"\n\n[2] chart_from_spec() 왕복 검증")
    print("-" * 60)

    roundtrip_success = 0
    roundtrip_fail = 0

    for code, name in test_codes[:5]:  # 상위 5종목
        try:
            c = Company(code)
            specs = auto_chart(c)
            print(f"\n  {name}: {len(specs)}개 spec → Plotly 변환")

            for s in specs:
                try:
                    fig = chart_from_spec(s)
                    has_data = len(fig.data) > 0
                    print(f"    {s['chartType']:<12} → Figure(traces={len(fig.data)}) {'✓' if has_data else '✗ empty'}")
                    if has_data:
                        roundtrip_success += 1
                    else:
                        roundtrip_fail += 1
                except Exception as e:
                    print(f"    {s['chartType']:<12} → 변환 실패: {e}")
                    roundtrip_fail += 1

        except Exception as e:
            print(f"\n  {name}: 에러 — {e}")

    # 3. spec_xxx() 개별 함수 검증
    print(f"\n\n[3] spec_xxx() 개별 함수 전종목 검증")
    print("-" * 60)

    gen_results = {name: {"success": 0, "fail": 0, "none": 0} for name in _SPEC_GENERATORS}

    for code, name in test_codes:
        try:
            c = Company(code)
            for gen_name, gen_func in _SPEC_GENERATORS.items():
                try:
                    result = gen_func(c)
                    if result is not None:
                        gen_results[gen_name]["success"] += 1
                    else:
                        gen_results[gen_name]["none"] += 1
                except Exception:
                    gen_results[gen_name]["fail"] += 1
        except Exception:
            for gen_name in _SPEC_GENERATORS:
                gen_results[gen_name]["fail"] += 1

    print(f"\n  {'함수':<20} {'성공':>6} {'None':>6} {'에러':>6} {'성공률':>8}")
    print(f"  {'-'*50}")
    for gen_name, counts in gen_results.items():
        total = counts["success"] + counts["none"] + counts["fail"]
        rate = counts["success"] / total * 100 if total > 0 else 0
        print(f"  {gen_name:<20} {counts['success']:>6} {counts['none']:>6} {counts['fail']:>6} {rate:>7.0f}%")

    # 4. JSON 직렬화 크기
    print(f"\n\n[4] ChartSpec JSON 크기")
    print("-" * 60)

    c = Company("005930")
    specs = auto_chart(c)
    for s in specs:
        json_str = json.dumps(s, ensure_ascii=False)
        print(f"  {s['chartType']:<12} {len(json_str):>8} bytes  {s.get('title', '')[:30]}")

    total_size = sum(len(json.dumps(s, ensure_ascii=False)) for s in specs)
    print(f"  {'전체':<12} {total_size:>8} bytes")

    # 5. 결과 요약
    print(f"\n\n{'='*90}")
    print("결과 요약")
    print(f"{'='*90}")

    min_count = min(r["count"] for r in results.values())
    max_count = max(r["count"] for r in results.values())
    avg_count = sum(r["count"] for r in results.values()) / len(results)

    print(f"  auto_chart 생성 수: 최소 {min_count}, 최대 {max_count}, 평균 {avg_count:.1f}")
    print(f"  chart_from_spec 왕복: 성공 {roundtrip_success}, 실패 {roundtrip_fail}")
    print(f"  가설1 {'채택' if min_count >= 3 else '기각'}: 최소 {min_count}개 (목표 ≥3)")
    print(f"  가설2 {'채택' if roundtrip_fail == 0 else '기각'}: 실패 {roundtrip_fail}건")

    # 가설3 검증
    always_success = [n for n, c in gen_results.items() if c["success"] == len(test_codes)]
    print(f"  가설3: 전종목 성공 함수 = {always_success}")


if __name__ == "__main__":
    test()
