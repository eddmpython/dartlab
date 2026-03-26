"""질문 키워드 → 추천 도구 힌트 생성.

LLM이 한국어 질문에서 영문 tool parameter를 정확히 추론하지 못하는 문제를
시스템 측 결정론적 매핑으로 해결한다.

실험 099-002/004에서 검증: paramAccuracy 16.7% → 100%.

NOTE: core.py에서 deprecated 처리됨. Super Tool enum description이 대체.
"""

from __future__ import annotations

# 질문 키워드 → 추천 도구 호출 매핑
# key: 질문에 포함될 한국어 키워드
# value: 추천 도구 + args + 사유 리스트
ROUTE_HINTS: dict[str, list[dict]] = {
    "재무제표": [
        {"tool": "finance", "args": {"action": "data", "module": "IS"}, "reason": "손익계산서 시계열"},
        {"tool": "finance", "args": {"action": "data", "module": "BS"}, "reason": "재무상태표 시계열"},
        {"tool": "finance", "args": {"action": "ratios"}, "reason": "재무비율"},
    ],
    "배당": [
        {"tool": "explore", "args": {"action": "report", "apiType": "dividend"}, "reason": "배당 정형 데이터"},
    ],
    "직원": [
        {"tool": "explore", "args": {"action": "report", "apiType": "employee"}, "reason": "직원 정형 데이터"},
    ],
    "임원": [
        {"tool": "explore", "args": {"action": "report", "apiType": "executive"}, "reason": "임원 보수 정형 데이터"},
    ],
    "보수": [
        {"tool": "explore", "args": {"action": "report", "apiType": "executive"}, "reason": "임원 보수 정형 데이터"},
    ],
    "최대주주": [
        {"tool": "explore", "args": {"action": "report", "apiType": "majorHolder"}, "reason": "최대주주 지분 데이터"},
    ],
    "지분": [
        {"tool": "explore", "args": {"action": "report", "apiType": "majorHolder"}, "reason": "지분 변동 데이터"},
    ],
    "감사": [
        {"tool": "explore", "args": {"action": "report", "apiType": "auditOpinion"}, "reason": "감사의견"},
        {"tool": "explore", "args": {"action": "show", "topic": "internalControl"}, "reason": "내부통제"},
    ],
    "경영진 분석": [
        {"tool": "explore", "args": {"action": "show", "topic": "mdnaOverview"}, "reason": "경영진 분석 의견 (MD&A)"},
    ],
    "분석 의견": [
        {"tool": "explore", "args": {"action": "show", "topic": "mdnaOverview"}, "reason": "경영진 분석 의견"},
    ],
    "사업 구조": [
        {"tool": "explore", "args": {"action": "show", "topic": "businessOverview"}, "reason": "사업의 내용"},
    ],
    "매출 구성": [
        {"tool": "explore", "args": {"action": "show", "topic": "businessOverview"}, "reason": "매출 구성"},
        {"tool": "finance", "args": {"action": "data", "module": "IS"}, "reason": "매출 수치"},
    ],
    "파생상품": [
        {"tool": "explore", "args": {"action": "show", "topic": "riskDerivative"}, "reason": "파생상품 현황"},
    ],
    "리스크": [
        {"tool": "explore", "args": {"action": "show", "topic": "riskFactor"}, "reason": "위험 요인"},
    ],
    "원재료": [
        {"tool": "explore", "args": {"action": "show", "topic": "rawMaterial"}, "reason": "원재료 조달"},
    ],
    "우발채무": [
        {"tool": "explore", "args": {"action": "show", "topic": "contingentLiability"}, "reason": "우발채무/약정"},
    ],
    "내부통제": [
        {"tool": "explore", "args": {"action": "show", "topic": "internalControl"}, "reason": "내부통제 현황"},
    ],
    "유동성": [
        {
            "tool": "explore",
            "args": {"action": "show", "topic": "liquidityAndCapitalResources"},
            "reason": "유동성/자본 조달",
        },
        {"tool": "finance", "args": {"action": "data", "module": "BS"}, "reason": "유동자산/부채 수치"},
    ],
    "주석": [
        {"tool": "explore", "args": {"action": "show", "topic": "consolidatedNotes"}, "reason": "연결재무제표 주석"},
    ],
    "회사 개요": [
        {"tool": "explore", "args": {"action": "show", "topic": "companyOverview"}, "reason": "회사 개요"},
    ],
    "제품": [
        {"tool": "explore", "args": {"action": "show", "topic": "productService"}, "reason": "주요 제품/서비스"},
    ],
    "비용": [
        {"tool": "explore", "args": {"action": "show", "topic": "fsSummary"}, "reason": "비용의 성격별분류 포함"},
    ],
    "성격별": [
        {"tool": "explore", "args": {"action": "show", "topic": "fsSummary"}, "reason": "비용의 성격별분류"},
    ],
    "재무 요약": [
        {"tool": "explore", "args": {"action": "show", "topic": "fsSummary"}, "reason": "재무제표 요약"},
        {"tool": "finance", "args": {"action": "data", "module": "IS"}, "reason": "손익계산서"},
    ],
    "사업": [
        {"tool": "explore", "args": {"action": "show", "topic": "businessOverview"}, "reason": "사업의 내용"},
    ],
    "건전성": [
        {"tool": "finance", "args": {"action": "ratios"}, "reason": "재무비율"},
        {"tool": "finance", "args": {"action": "data", "module": "BS"}, "reason": "재무상태표"},
    ],
    "부문": [
        {"tool": "explore", "args": {"action": "show", "topic": "fsSummary"}, "reason": "부문별 정보"},
    ],
    "자회사": [
        {"tool": "explore", "args": {"action": "show", "topic": "affiliateGroup"}, "reason": "계열사/자회사 현황"},
    ],
    "관계사": [
        {"tool": "explore", "args": {"action": "show", "topic": "relatedPartyTx"}, "reason": "관계사 거래"},
    ],
    "수주": [
        {"tool": "explore", "args": {"action": "show", "topic": "salesOrder"}, "reason": "수주 현황"},
    ],
    "영업이익": [
        {"tool": "finance", "args": {"action": "data", "module": "IS"}, "reason": "손익계산서 시계열"},
    ],
    "매출": [
        {"tool": "finance", "args": {"action": "data", "module": "IS"}, "reason": "손익계산서 시계열"},
    ],
}


def buildToolRouteHint(question: str) -> str:
    """질문에서 키워드를 매칭하여 추천 도구 힌트 텍스트를 생성한다."""
    matched: list[dict] = []
    for keyword, hints in ROUTE_HINTS.items():
        if keyword in question:
            for h in hints:
                key = (h["tool"], str(h["args"]))
                if key not in [(m["tool"], str(m["args"])) for m in matched]:
                    matched.append(h)

    if not matched:
        return ""

    lines = [
        "## 추천 도구 호출 (시스템 분석 결과)",
        "아래 도구를 호출하면 이 질문에 필요한 데이터를 얻을 수 있습니다:",
        "",
    ]
    for h in matched:
        argsStr = ", ".join(f'{k}="{v}"' for k, v in h["args"].items())
        lines.append(f"- `{h['tool']}({argsStr})` — {h['reason']}")
    lines.append("")
    lines.append("위 도구를 **먼저** 호출한 뒤, 결과를 기반으로 답변하세요.")
    return "\n".join(lines)
