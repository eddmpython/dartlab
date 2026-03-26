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
            "concentration",
            "revenueFlags",
        ],
        "helper": (
            "① 매출 집중도(HHI)와 부문별 이익률 차이로 수익 구조 편중을 본다\n"
            "② 부문별 매출 추이와 YoY로 성장 부문을 식별한다\n"
            "③ 매출 성장률(YoY, 3Y CAGR)로 중기 방향성을 본다"
        ),
        "aiGuide": (
            "매출 집중도(HHI)가 높으면 단일 부문 의존 리스크를 짚어라. "
            "부문별 이익률 차이가 크면 수익 구조 편중을 언급하라. "
            "성장 부문과 정체 부문을 구분하고, 매출 YoY/3Y CAGR 방향성을 평가하라. "
            "내수/수출 비중이 한쪽으로 치우치면 지역 리스크를 언급하라."
        ),
    },
    "자금조달": {
        "title": "자금 조달 — 돈을 어디서 조달하는가",
        "partId": "1-2",
        "keys": [
            "capitalTimeline",
            "debtTimeline",
            "interestBurden",
            "liquidity",
            "capitalFlags",
        ],
        "helper": (
            "① 부채비율·순차입금으로 조달 구조를 본다\n"
            "② 이자보상배율로 이자 감당 능력을 확인한다\n"
            "③ 유동비율로 단기 지급 능력을 확인한다"
        ),
        "aiGuide": (
            "부채비율과 순차입금 수준으로 재무 안정성을 평가하라. "
            "이자보상배율이 3배 미만이면 이자 감당 위험을 경고하라. "
            "단기/장기 차입 비중으로 차환 리스크를 짚어라. "
            "순현금이면 재무 여유를 언급하라."
        ),
    },
}

TEMPLATE_ORDER = ["수익구조", "자금조달"]
