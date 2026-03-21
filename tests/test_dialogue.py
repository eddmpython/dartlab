"""dialogue 상태/모드 유틸 테스트."""

import pytest

pytestmark = pytest.mark.unit

from dartlab.server.dialogue import build_conversation_state, build_dialogue_policy, conversation_state_to_meta
from dartlab.server.models import HistoryMessage, HistoryMeta, ViewContext


def test_build_conversation_state_from_view_context():
    state = build_conversation_state(
        "이 부분 왜 이래?",
        view_context=ViewContext(
            type="viewer",
            company={"corpName": "삼성전자", "stockCode": "005930", "market": "dart"},
            topic="dividend",
            topicLabel="배당",
        ),
    )
    assert state.company == "삼성전자"
    assert state.stock_code == "005930"
    assert state.market == "dart"
    assert state.topic == "dividend"
    assert state.topic_label == "배당"
    assert state.dialogue_mode == "follow_up"


def test_build_conversation_state_detects_coding_mode():
    state = build_conversation_state("이 버그 고치고 테스트도 추가해줘")
    assert state.dialogue_mode == "coding"
    assert state.user_goal == "코드 작업 실행 또는 검토"


def test_build_conversation_state_supports_legacy_view_context_hint():
    state = build_conversation_state(
        "왜 배당이 줄었지?\n[사용자가 현재 삼성전자(005930) 공시를 보고 있습니다 — 현재 섹션: 배당(dividend)]"
    )
    assert state.company == "삼성전자"
    assert state.stock_code == "005930"
    assert state.topic == "dividend"
    assert state.question == "왜 배당이 줄었지?"


def test_build_conversation_state_uses_history_meta():
    state = build_conversation_state(
        "계속 보자",
        history=[
            HistoryMessage(
                role="assistant",
                text="이전 답변",
                meta=HistoryMeta(
                    company="삼성전자",
                    stockCode="005930",
                    market="dart",
                    topic="risk",
                    topicLabel="리스크",
                    modules=["IS", "BS"],
                ),
            )
        ],
    )
    assert state.company == "삼성전자"
    assert state.modules == ("IS", "BS")
    assert state.dialogue_mode == "follow_up"


def test_conversation_state_meta_and_policy():
    state = build_conversation_state(
        "AAPL에서 어떤 데이터가 있어?",
        view_context=ViewContext(
            type="viewer",
            company={"corpName": "Apple Inc.", "stockCode": "AAPL", "market": "edgar"},
        ),
    )
    payload = conversation_state_to_meta(state)
    policy = build_dialogue_policy(state)
    assert payload["dialogueMode"] == state.dialogue_mode
    assert payload["market"] == "edgar"
    assert "대화 모드" in policy
    assert "현재 회사" in policy
    assert "응답 템플릿" in policy
    assert "가능한 것:" in policy


def test_coding_policy_reflects_runtime_guard(monkeypatch):
    monkeypatch.setenv("DARTLAB_HOST", "0.0.0.0")
    monkeypatch.delenv("DARTLAB_ENABLE_CODING_RUNTIME", raising=False)
    state = build_conversation_state("이 버그 고치고 테스트 추가해줘")
    policy = build_dialogue_policy(state)
    assert "비활성화" in policy
    assert "텍스트 기반 수정안" in policy


def test_company_analysis_policy_includes_result_template():
    state = build_conversation_state(
        "삼성전자 수익성 분석해줘",
        view_context=ViewContext(
            type="viewer",
            company={"corpName": "삼성전자", "stockCode": "005930", "market": "dart"},
            topic="IS",
            topicLabel="손익계산서",
        ),
    )
    policy = build_dialogue_policy(state)
    assert state.dialogue_mode == "company_analysis"
    assert "한줄 결론" in policy
    assert "근거 표" in policy
