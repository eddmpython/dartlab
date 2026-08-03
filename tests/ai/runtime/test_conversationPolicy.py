from __future__ import annotations

import pytest

from dartlab.ai.runtime.conversationPolicy import buildConversationGuide, followUpQuestions
from dartlab.reference.capability.analysisGraph import coveragePacketForQuestion

pytestmark = pytest.mark.unit


def testInvestmentQuestionGetsDecisionFrameWithoutRawQuestion() -> None:
    question = "삼성전자 005930 지금 투자할 만한지 종합 분석해줘"
    guide = buildConversationGuide(question)

    assert guide["mode"] == "investmentDecision"
    assert "반대논지" in guide["answerShape"]
    assert "가치·리스크" in guide["stages"]
    assert question not in str(guide)
    assert len(followUpQuestions(guide)) == 3


def testGenericBetterQuestionGetsSameAxisComparisonContract() -> None:
    question = "삼성전자와 SK하이닉스 중 뭐가 더 나아?"
    coverage = coveragePacketForQuestion(question)
    guide = buildConversationGuide(question, coverage=coverage)

    assert "comparison.same_axis" in coverage["contractIds"]
    assert guide["mode"] == "companyComparison"
    assert "같은 기간·지표·가정" in guide["decisionGoal"]


def testStatementFactSeparatesCompanyTrendFromMarketScreen() -> None:
    trend = buildConversationGuide("삼성전자 005930 최근 5년 매출과 영업이익 추이")
    screen = buildConversationGuide("코스피에서 ROE가 높고 부채비율이 낮은 종목을 스크리닝해줘")

    assert trend["mode"] == "performanceTrend"
    assert screen["mode"] == "screening"
    assert "함정" in screen["answerShape"]


def testDisclosureQuestionGetsImpactAndLeadingSignalFrame() -> None:
    guide = buildConversationGuide("삼성전자 최근 공시에서 가장 큰 리스크는?")

    assert guide["mode"] == "disclosureReview"
    assert "재무 영향" in guide["answerShape"]
    assert any("선행 신호" in question for question in followUpQuestions(guide))
