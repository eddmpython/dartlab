"""질문 계약을 투자 분석가가 읽을 수 있는 대화 프레임으로 투영한다."""

from __future__ import annotations

import re
from typing import Any

MODE_BLUEPRINTS: dict[str, dict[str, Any]] = {
    "investmentDecision": {
        "label": "투자 판단",
        "decisionGoal": "투자 논지와 반대논지, 가격에 반영된 기대, 훼손 조건을 함께 판단",
        "answerShape": ["판단", "핵심 논지", "반대논지", "가치·기대", "촉매·리스크", "다음 확인"],
        "stages": ["질문 구조화", "핵심 근거", "반대가설", "가치·리스크", "결론 검산"],
        "followups": [
            "가장 강한 반대논지를 데이터로 검증해줘",
            "현재 가격에 반영된 시장 기대를 역산해줘",
            "다음 실적까지 볼 핵심 지표와 투자논지 훼손 조건을 정리해줘",
        ],
    },
    "companyComparison": {
        "label": "동일 기준 비교",
        "decisionGoal": "모든 대상을 같은 기간·지표·가정으로 비교하고 승자가 바뀌는 조건을 판단",
        "answerShape": ["조건부 결론", "동일 축 비교", "성장·수익성", "가치", "리스크", "선택 조건"],
        "stages": ["비교축 확정", "대상별 근거", "차이 원인", "반대 조건", "결론 검산"],
        "followups": [
            "두 회사의 밸류에이션과 성장 기대를 같은 기준으로 비교해줘",
            "각 회사의 투자 논지를 깨뜨릴 리스크를 비교해줘",
            "베어·베이스 시나리오에서 우위가 바뀌는 조건은?",
        ],
    },
    "screening": {
        "label": "후보 선별",
        "decisionGoal": "유니버스와 필터를 공개하고 숫자가 좋아 보이는 함정까지 걸러 후보를 선별",
        "answerShape": ["유니버스", "필터·계산식", "후보", "제외 이유", "함정", "다음 검증"],
        "stages": ["유니버스 확정", "필터 계산", "후보 검증", "함정 점검", "결과 검산"],
        "followups": [
            "상위 후보를 업종·규모·밸류에이션까지 같은 축으로 비교해줘",
            "일회성 이익이나 회계 착시가 있는 후보를 제외해줘",
            "최종 후보의 투자논지와 훼손 조건을 한 종목씩 정리해줘",
        ],
    },
    "disclosureReview": {
        "label": "공시 영향 분석",
        "decisionGoal": "공시 사실과 해석을 분리하고 실적·현금흐름·밸류에이션으로 이어지는 영향을 판단",
        "answerShape": ["무슨 변화", "중요한 이유", "재무 영향", "반대 해석", "선행 신호", "다음 일정"],
        "stages": ["공시 식별", "본문 근거", "재무 연결", "반대 해석", "결론 검산"],
        "followups": [
            "이 공시가 실적과 현금흐름에 미치는 경로를 분석해줘",
            "과거 유사 공시와 비교해 중요도를 검증해줘",
            "이 리스크가 현실화되는 선행 신호와 다음 일정을 알려줘",
        ],
    },
    "performanceTrend": {
        "label": "실적 추세",
        "decisionGoal": "요청한 수치를 정확히 제시하고 변화가 일시적인지 구조적인지 판단할 출발점을 제공",
        "answerShape": ["요청 수치", "추세", "변곡점", "투자 의미", "불확실성"],
        "stages": ["지표·기간 확정", "수치 확인", "변곡점 점검", "의미 해석", "답변 검산"],
        "followups": [
            "이 추이가 일시적인지 구조적인지 원인을 분석해줘",
            "같은 산업 경쟁사와 같은 지표로 비교해줘",
            "다음 실적에서 이 추세를 확인할 선행 지표는?",
        ],
    },
    "research": {
        "label": "근거 조사",
        "decisionGoal": "질문의 사실과 해석을 분리하고 확인 가능한 결론과 남은 불확실성을 제시",
        "answerShape": ["결론", "근거", "반대 근거", "한계", "다음 확인"],
        "stages": ["질문 구조화", "근거 확인", "대안 점검", "결론 작성", "답변 검산"],
        "followups": [],
    },
}


def buildConversationGuide(
    question: str,
    *,
    coverage: dict[str, Any] | None = None,
    stockCode: str | None = None,
) -> dict[str, Any]:
    """Sig: buildConversationGuide(question, *, coverage=None, stockCode=None) -> dict[str, Any].

    Args: 사용자 질문과 Analysis Graph coverage, 선택적 종목 코드다.
    Returns: 원문 질문을 포함하지 않는 bounded 대화 프레임이다.
    Example: `buildConversationGuide("투자할 만해?", coverage=packet)`.
    """
    if coverage is None:
        from dartlab.reference.capability.analysisGraph import coveragePacketForQuestion

        coverage = coveragePacketForQuestion(question, stockCode=stockCode)

    contractIds = {str(value) for value in coverage.get("contractIds") or ()}
    questionTypes = {str(value) for value in coverage.get("questionTypes") or ()}
    capabilityRefs = {str(value) for value in coverage.get("candidateCapabilityRefs") or ()}
    hasCompanyTarget = bool(stockCode or re.search(r"(?<!\d)\d{6}(?!\d)", question))

    if "investment.decision_memo" in contractIds or "investment_decision" in questionTypes:
        mode = "investmentDecision"
    elif "comparison.same_axis" in contractIds or "company_compare" in questionTypes:
        mode = "companyComparison"
    elif "disclosure_importance" in questionTypes or "disclosure.importance" in contractIds:
        mode = "disclosureReview"
    elif "statement_fact" in questionTypes:
        hasScan = any(value == "scan" or value.startswith("scan.") for value in capabilityRefs)
        mode = "screening" if hasScan and not hasCompanyTarget else "performanceTrend"
    else:
        mode = "research"

    blueprint = MODE_BLUEPRINTS[mode]
    return {
        "mode": mode,
        "label": blueprint["label"],
        "decisionGoal": blueprint["decisionGoal"],
        "answerShape": list(blueprint["answerShape"]),
        "stages": list(blueprint["stages"]),
    }


def followUpQuestions(guide: dict[str, Any]) -> list[str]:
    """Sig: followUpQuestions(guide) -> list[str].

    Args: buildConversationGuide가 만든 대화 프레임이다.
    Returns: 같은 분석을 더 깊게 만드는 최대 세 개 후속 질문이다.
    Example: `followUpQuestions(buildConversationGuide("질문"))`.
    """
    mode = str(guide.get("mode") or "research")
    blueprint = MODE_BLUEPRINTS.get(mode, MODE_BLUEPRINTS["research"])
    return [str(value) for value in blueprint.get("followups") or ()][:3]
