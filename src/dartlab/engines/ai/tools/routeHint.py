"""질문 키워드 → 추천 도구 힌트 생성.

LLM이 한국어 질문에서 영문 tool parameter를 정확히 추론하지 못하는 문제를
시스템 측 결정론적 매핑으로 해결한다.

실험 099-002/004에서 검증: paramAccuracy 16.7% → 100%.
"""

from __future__ import annotations

# 질문 키워드 → 추천 도구 호출 매핑
# key: 질문에 포함될 한국어 키워드
# value: 추천 도구 + args + 사유 리스트
ROUTE_HINTS: dict[str, list[dict]] = {
    "재무제표": [
        {"tool": "get_data", "args": {"module_name": "IS"}, "reason": "손익계산서 시계열"},
        {"tool": "get_data", "args": {"module_name": "BS"}, "reason": "재무상태표 시계열"},
        {"tool": "get_data", "args": {"module_name": "ratios"}, "reason": "재무비율"},
    ],
    "배당": [
        {"tool": "get_report_data", "args": {"api_type": "dividend"}, "reason": "배당 정형 데이터"},
    ],
    "직원": [
        {"tool": "get_report_data", "args": {"api_type": "employee"}, "reason": "직원 정형 데이터"},
    ],
    "임원": [
        {"tool": "get_report_data", "args": {"api_type": "executive"}, "reason": "임원 보수 정형 데이터"},
    ],
    "보수": [
        {"tool": "get_report_data", "args": {"api_type": "executive"}, "reason": "임원 보수 정형 데이터"},
    ],
    "최대주주": [
        {"tool": "get_report_data", "args": {"api_type": "majorHolder"}, "reason": "최대주주 지분 데이터"},
    ],
    "지분": [
        {"tool": "get_report_data", "args": {"api_type": "majorHolder"}, "reason": "지분 변동 데이터"},
    ],
    "감사": [
        {"tool": "get_report_data", "args": {"api_type": "auditOpinion"}, "reason": "감사의견"},
        {"tool": "show_topic", "args": {"topic": "internalControl"}, "reason": "내부통제"},
    ],
    "경영진 분석": [
        {"tool": "show_topic", "args": {"topic": "mdnaOverview"}, "reason": "경영진 분석 의견 (MD&A)"},
    ],
    "분석 의견": [
        {"tool": "show_topic", "args": {"topic": "mdnaOverview"}, "reason": "경영진 분석 의견"},
    ],
    "사업 구조": [
        {"tool": "show_topic", "args": {"topic": "businessOverview"}, "reason": "사업의 내용"},
    ],
    "매출 구성": [
        {"tool": "show_topic", "args": {"topic": "businessOverview"}, "reason": "매출 구성"},
        {"tool": "get_data", "args": {"module_name": "IS"}, "reason": "매출 수치"},
    ],
    "파생상품": [
        {"tool": "show_topic", "args": {"topic": "riskDerivative"}, "reason": "파생상품 현황"},
    ],
    "리스크": [
        {"tool": "show_topic", "args": {"topic": "riskFactor"}, "reason": "위험 요인"},
    ],
    "원재료": [
        {"tool": "show_topic", "args": {"topic": "rawMaterial"}, "reason": "원재료 조달"},
    ],
    "우발채무": [
        {"tool": "show_topic", "args": {"topic": "contingentLiability"}, "reason": "우발채무/약정"},
    ],
    "내부통제": [
        {"tool": "show_topic", "args": {"topic": "internalControl"}, "reason": "내부통제 현황"},
    ],
    "유동성": [
        {"tool": "show_topic", "args": {"topic": "liquidityAndCapitalResources"}, "reason": "유동성/자본 조달"},
        {"tool": "get_data", "args": {"module_name": "BS"}, "reason": "유동자산/부채 수치"},
    ],
    "주석": [
        {"tool": "show_topic", "args": {"topic": "consolidatedNotes"}, "reason": "연결재무제표 주석"},
    ],
    "회사 개요": [
        {"tool": "show_topic", "args": {"topic": "companyOverview"}, "reason": "회사 개요"},
    ],
    "제품": [
        {"tool": "show_topic", "args": {"topic": "productService"}, "reason": "주요 제품/서비스"},
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
