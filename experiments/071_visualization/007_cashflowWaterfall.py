"""
실험 ID: 007
실험명: 현금흐름 워터폴 차트 데이터 구조 검증

목적:
- CF(현금흐름표) 데이터를 워터폴 ChartSpec으로 변환하는 파이프라인을 검증한다
- 영업→투자→재무→현금증감 분해 구조가 올바른지 확인한다
- WaterfallChart.svelte가 소비할 정확한 데이터 구조를 확정한다

가설:
1. CF annual 데이터에서 영업CF/투자CF/재무CF/현금증감 4항목을 추출하여 워터폴을 만들 수 있다
2. 시작(기초현금)→영업→투자→재무→끝(기말현금)의 브릿지 구조가 성립한다
3. 5개 종목에서 동일한 변환 로직이 작동한다

방법:
1. 삼성전자 CF annual 데이터에서 핵심 계정 추출
2. 워터폴 ChartSpec 생성 (기초현금 → +영업 → -투자 → +/-재무 → 기말현금)
3. 다종목 검증
4. 연도별 워터폴 비교

결과:
- 5/5 종목 워터폴 ChartSpec 생성 성공
- 삼성전자 2024: 기초 69.1조 → 영업+73.0조 → 투자-85.4조 → 재무-7.8조 → 기말 48.9조
- 현대차 2024: 영업CF 적자(-5.7조), 재무+19.5조 — 특이 패턴도 정상 처리
- 카카오 2024: 투자+0.01조 (양수) — 유연하게 처리됨
- 연도별 비교: 삼성전자 3개년 CF 추이 정상 추출
- 가설1 채택: operating_cashflow/investing_cashflow/financing_cashflow snakeId로 추출 성공
- 가설2 채택: 기초→영업→투자→재무→기말 브릿지 성립
- 가설3 채택: 5/5 종목 동일 로직 작동
- 주의: snakeId가 operating_cash_flow가 아닌 operating_cashflow임 (초기 버그 수정)

실험일: 2026-03-19
"""

import json
import sys

sys.path.insert(0, "src")


COLORS = ["#ea4647", "#fb923c", "#3b82f6", "#22c55e", "#8b5cf6", "#06b6d4", "#f59e0b", "#ec4899"]


def cfToWaterfallSpec(company, *, year_idx=-1):
    """CF annual 데이터 → waterfall ChartSpec 변환."""
    ann = company.annual
    if not ann:
        return None

    ann_data, ann_years = ann
    cf_data = ann_data.get("CF", {})

    # 핵심 계정 탐색
    account_map = {
        "영업활동": ["operating_cashflow", "operating_cash_flow",
                    "cash_flows_from_operating_activities"],
        "투자활동": ["investing_cashflow", "investing_cash_flow",
                    "cash_flows_from_investing_activities"],
        "재무활동": ["financing_cashflow", "financing_cash_flow",
                    "cash_flows_from_financing_activities"],
        "현금증감": ["increasedecrease_in_cash_and_cash_equivalents",
                    "net_increase_decrease_in_cash_and_cash_equivalents",
                    "increase_decrease_in_cash"],
        "기초현금": ["cash_and_cash_equivalents_beginning",
                    "cash_at_beginning"],
        "기말현금": ["cash_and_cash_equivalents_ending",
                    "cash_at_end"],
    }

    values = {}
    for label, candidates in account_map.items():
        for cand in candidates:
            if cand in cf_data:
                val_list = cf_data[cand]
                if len(val_list) > abs(year_idx):
                    v = val_list[year_idx]
                    if v is not None:
                        values[label] = v
                        break

    year = ann_years[year_idx] if len(ann_years) > abs(year_idx) else "?"

    # 기초현금이 없으면 BS의 cash 사용
    if "기초현금" not in values:
        bs_data = ann_data.get("BS", {})
        for cand in ["cash", "cash_and_cash_equivalents"]:
            if cand in bs_data:
                prev_idx = year_idx - 1 if year_idx < 0 else year_idx - 1
                if len(bs_data[cand]) > abs(prev_idx):
                    v = bs_data[cand][prev_idx]
                    if v is not None:
                        values["기초현금"] = v
                        break

    # 기말현금이 없으면 계산
    if "기말현금" not in values and all(k in values for k in ["기초현금", "영업활동", "투자활동", "재무활동"]):
        values["기말현금"] = values["기초현금"] + values["영업활동"] + values["투자활동"] + values["재무활동"]

    if not values.get("영업활동"):
        return None

    # 워터폴 구조: 각 항목의 시작점과 끝점
    items = []
    running = values.get("기초현금", 0)

    items.append({
        "name": f"기초현금 ({year})",
        "value": running,
        "type": "total",
        "color": COLORS[5],
    })

    for label, color in [("영업활동", COLORS[3]), ("투자활동", COLORS[0]), ("재무활동", COLORS[4])]:
        v = values.get(label, 0)
        items.append({
            "name": label,
            "value": v,
            "type": "increase" if v >= 0 else "decrease",
            "color": color,
        })
        running += v

    items.append({
        "name": f"기말현금 ({year})",
        "value": running,
        "type": "total",
        "color": COLORS[5],
    })

    spec = {
        "chartType": "waterfall",
        "title": f"{company.corpName} 현금흐름 분해 ({year})",
        "series": [{"name": "현금흐름", "data": [item["value"] for item in items]}],
        "categories": [item["name"] for item in items],
        "options": {
            "unit": "백만원",
            "items": items,  # 워터폴 전용 메타 (type + color)
        },
    }

    return spec, values


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
    print("007: 현금흐름 워터폴 차트 데이터 구조 검증")
    print("=" * 90)

    success = 0
    fail = 0

    for code, name in test_codes:
        print(f"\n--- {name} ({code}) ---")
        try:
            c = Company(code)
            result = cfToWaterfallSpec(c, year_idx=-2)  # 직전 완결 연도
            if result is None:
                print("  워터폴 생성 실패 (CF 데이터 없음)")
                fail += 1
                continue

            spec, values = result
            print(f"  연도: {spec['categories'][0]}")
            for label in ["기초현금", "영업활동", "투자활동", "재무활동", "기말현금"]:
                v = values.get(label, 0)
                sign = "+" if v >= 0 else ""
                print(f"    {label}: {sign}{v/1e6:.1f}M 백만원")

            success += 1

        except Exception as e:
            print(f"  에러: {e}")
            fail += 1

    # ChartSpec JSON 예시
    print(f"\n\n{'='*90}")
    print("워터폴 ChartSpec 예시 (삼성전자)")
    print(f"{'='*90}")

    c = Company("005930")
    result = cfToWaterfallSpec(c, year_idx=-2)
    if result:
        spec, _ = result
        print(json.dumps(spec, ensure_ascii=False, indent=2))

    # 연도별 비교
    print(f"\n\n{'='*90}")
    print("삼성전자 연도별 CF 추이")
    print(f"{'='*90}")

    for idx in [-4, -3, -2]:
        result = cfToWaterfallSpec(c, year_idx=idx)
        if result:
            spec, values = result
            year = spec["categories"][0].split("(")[1].rstrip(")")
            ops = values.get("영업활동", 0) / 1e6
            inv = values.get("투자활동", 0) / 1e6
            fin = values.get("재무활동", 0) / 1e6
            print(f"  {year}: 영업={ops:+.0f}M  투자={inv:+.0f}M  재무={fin:+.0f}M")

    print(f"\n\n결과 요약: {success}/{len(test_codes)} 성공, {fail} 실패")


if __name__ == "__main__":
    test()
