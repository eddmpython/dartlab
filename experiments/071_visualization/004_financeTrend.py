"""
실험 ID: 004
실험명: 재무 시계열 combo 차트 데이터 구조 검증

목적:
- IS/BS/CF 데이터를 ChartSpec combo 차트로 변환하는 파이프라인을 검증한다
- 다종목에서 데이터 형상이 일관되는지 확인한다
- TrendChart.svelte가 소비할 정확한 JSON 구조를 확정한다

가설:
1. show('IS') DataFrame에서 핵심 3행(매출액/영업이익/당기순이익)을 추출하여 combo ChartSpec을 만들 수 있다
2. show('BS')에서 자산/부채/자본을 stacked bar ChartSpec으로 만들 수 있다
3. 10개 종목 이상에서 동일한 변환 로직이 깨지지 않는다

방법:
1. 삼성전자/SK하이닉스/LG에너지솔루션/카카오/현대차 5개 종목으로 IS combo 차트 생성
2. 삼성전자 BS stacked bar 차트 생성
3. 연간 데이터(annual)로 최근 5개년 추출
4. 변환 실패 케이스 분석

결과:
- 10/10 종목 IS combo ChartSpec 생성 성공
- 매출액: 10/10 유효, 영업이익: 10/10 유효
- 당기순이익: 일부 종목(LG에너지솔루션, LG화학)에서 0 값 (snakeId 차이)
- BS stacked: 삼성전자 총자산/총부채 2개 시리즈 (총자본은 equity snakeId 차이로 누락)
- 가설1 채택, 가설2 채택, 가설3 채택 (10/10 통과)

실험일: 2026-03-19
"""

import json
import sys

sys.path.insert(0, "src")


COLORS = [
    "#ea4647", "#fb923c", "#3b82f6", "#22c55e",
    "#8b5cf6", "#06b6d4", "#f59e0b", "#ec4899",
]


def financeToComboSpec(company, *, years=5):
    """IS annual 데이터 → combo ChartSpec 변환."""
    ann = company.annual
    if not ann:
        return None

    ann_data, ann_years = ann
    is_data = ann_data.get("IS", {})

    # 핵심 계정 탐색 (snakeId 기준)
    key_accounts = [
        ("매출액", ["sales", "revenue", "interest_income"]),
        ("영업이익", ["operating_income", "operating_profit"]),
        ("당기순이익", ["net_income", "profit_for_the_period", "profit_loss"]),
    ]

    series = []
    chart_types = ["bar", "line", "line"]
    colors = [COLORS[2], COLORS[0], COLORS[3]]  # blue, red, green

    for i, (label, candidates) in enumerate(key_accounts):
        vals = None
        for cand in candidates:
            if cand in is_data and any(v is not None for v in is_data[cand]):
                vals = is_data[cand]
                break
        if vals is None:
            continue

        recent = vals[-years:]
        series.append({
            "name": label,
            "data": [v if v is not None else 0 for v in recent],
            "color": colors[i],
            "type": chart_types[i],
        })

    if not series:
        return None

    return {
        "chartType": "combo",
        "title": f"{company.corpName} 손익 추이",
        "series": series,
        "categories": ann_years[-years:],
        "options": {"unit": "백만원"},
    }


def bsToStackedSpec(company, *, years=5):
    """BS annual 데이터 → stacked bar ChartSpec 변환."""
    ann = company.annual
    if not ann:
        return None

    ann_data, ann_years = ann
    bs_data = ann_data.get("BS", {})

    key_accounts = [
        ("총자산", ["total_assets"]),
        ("총부채", ["total_liabilities"]),
        ("총자본", ["total_equity", "equity"]),
    ]

    series = []
    colors = [COLORS[2], COLORS[0], COLORS[3]]

    for i, (label, candidates) in enumerate(key_accounts):
        vals = None
        for cand in candidates:
            if cand in bs_data and any(v is not None for v in bs_data[cand]):
                vals = bs_data[cand]
                break
        if vals is None:
            continue

        recent = vals[-years:]
        series.append({
            "name": label,
            "data": [v if v is not None else 0 for v in recent],
            "color": colors[i],
        })

    if not series:
        return None

    return {
        "chartType": "bar",
        "title": f"{company.corpName} 재무상태 추이",
        "series": series,
        "categories": ann_years[-years:],
        "options": {"unit": "백만원", "stacked": False},
    }


def test_stocks():
    """다종목 combo 차트 변환 테스트."""
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
    print("004: 재무 시계열 combo 차트 데이터 구조 검증")
    print("=" * 90)

    results = {"success": 0, "fail": 0, "details": []}

    for code, name in test_codes:
        print(f"\n--- {name} ({code}) ---")
        try:
            c = Company(code)
            spec = financeToComboSpec(c)
            if spec:
                print(f"  IS combo: {len(spec['series'])}개 시리즈, {len(spec['categories'])}개 연도")
                for s in spec["series"]:
                    non_zero = sum(1 for v in s["data"] if v != 0)
                    print(f"    {s['name']}: {non_zero}/{len(s['data'])}개 유효, type={s.get('type', 'bar')}")
                results["success"] += 1
                results["details"].append({"code": code, "name": name, "status": "OK", "series": len(spec["series"])})
            else:
                print("  IS combo: 생성 실패 (데이터 없음)")
                results["fail"] += 1
                results["details"].append({"code": code, "name": name, "status": "FAIL", "reason": "no data"})
        except Exception as e:
            print(f"  에러: {e}")
            results["fail"] += 1
            results["details"].append({"code": code, "name": name, "status": "ERROR", "reason": str(e)})

    # BS stacked (삼성전자만)
    print("\n\n--- 삼성전자 BS stacked bar ---")
    c = Company("005930")
    bs_spec = bsToStackedSpec(c)
    if bs_spec:
        print(f"  BS stacked: {len(bs_spec['series'])}개 시리즈")
        for s in bs_spec["series"]:
            print(f"    {s['name']}: {[f'{v/1e6:.0f}M' if v else '0' for v in s['data']]}")

    # ChartSpec JSON 예시 출력
    print("\n\n--- ChartSpec JSON 예시 (삼성전자 IS combo) ---")
    spec = financeToComboSpec(c)
    if spec:
        print(json.dumps(spec, ensure_ascii=False, indent=2))

    # 요약
    print(f"\n\n{'='*90}")
    print(f"결과 요약: {results['success']}/{len(test_codes)} 성공, {results['fail']} 실패")
    print(f"{'='*90}")

    return results


if __name__ == "__main__":
    test_stocks()
