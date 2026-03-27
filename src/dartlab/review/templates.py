"""review 템플릿 — 미리 정의된 블록 조합.

c.review("수익구조") → 수익구조 템플릿의 keys 블록만 조립.
c.review()           → 전체 템플릿 순서대로 조립.
"""

from __future__ import annotations

TEMPLATES: dict[str, dict] = {
    "수익구조": {
        "title": "수익 구조 — 이 회사는 무엇으로 돈을 버는가",
        "partId": "1-1",
        "keys": [
            "profile",
            "segmentComposition",
            "segmentTrend",
            "region",
            "product",
            "growth",
            "growthContribution",
            "concentration",
            "revenueQuality",
            "revenueFlags",
        ],
        "helper": (
            "① 매출 집중도(HHI)와 부문별 이익률 차이로 수익 구조 편중을 본다\n"
            "② 부문별 매출 추이와 YoY로 성장 부문을 식별한다\n"
            "③ 매출 성장률(YoY, 3Y CAGR)로 중기 방향성을 본다\n"
            "④ 성장 기여 분해로 어디에서 성장이 왔는지 본다\n"
            "⑤ 영업CF/순이익, 총이익률 추세로 매출 품질을 확인한다"
        ),
        "aiGuide": (
            "매출 집중도(HHI)가 높으면 단일 부문 의존 리스크를 짚어라. "
            "부문별 이익률 차이가 크면 수익 구조 편중을 언급하라. "
            "성장 부문과 정체 부문을 구분하고, 매출 YoY/3Y CAGR 방향성을 평가하라. "
            "내수/수출 비중이 한쪽으로 치우치면 지역 리스크를 언급하라. "
            "영업CF/순이익이 40% 미만이면 이익의 현금 뒷받침 부족을 경고하라. "
            "총이익률이 악화 추세면 원가 구조 변화를 짚어라."
        ),
    },
    "자금조달": {
        "title": "자금 조달 — 돈을 어디서 조달하는가",
        "partId": "1-2",
        "keys": [
            "fundingSources",
            "capitalTimeline",
            "debtTimeline",
            "interestBurden",
            "liquidity",
            "capitalFlags",
        ],
        "helper": (
            "① 내부유보/주주자본/금융차입/영업조달 4원천 비중을 본다\n"
            "② 이익잉여금 비중이 높으면 자기 힘으로 성장\n"
            "③ 금융차입 비중이 높으면 이자보상배율과 만기를 확인한다\n"
            "④ 유동비율로 단기 지급 능력을 확인한다"
        ),
        "aiGuide": (
            "내부유보 vs 금융차입 비중으로 자금조달 성격을 먼저 판단하라. "
            "이익잉여금이 자산의 50% 이상이면 자기 힘으로 성장한 회사다. "
            "금융차입 40% 이상이면 이자보상배율과 차환 리스크를 반드시 짚어라. "
            "영업조달(매입채무·선수금)이 크면 영업력으로 자금을 조달하는 구조다. "
            "비중 추이에서 금융차입이 늘고 내부유보가 줄면 자금조달 구조 악화 신호다."
        ),
    },
}

TEMPLATE_ORDER = ["수익구조", "자금조달"]
