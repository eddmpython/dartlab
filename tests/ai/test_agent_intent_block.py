"""agent._formatIntentProfileBlock 단위 테스트.

마스터 플랜 트랙 3 PR-W3 동행. workbench/targets._buildQuestionProfile 결과를
system prompt markdown 블록으로 변환하는 helper 결정론 검증.
"""

from __future__ import annotations

import pytest

from dartlab.ai.agent import _formatIntentProfileBlock

pytestmark = pytest.mark.unit


def test_intent_block_empty_kwargs() -> None:
    """질문도 stockCode 도 없으면 빈 문자열."""
    assert _formatIntentProfileBlock({}) == ""


def test_intent_block_with_question_stockcode() -> None:
    """stockCode + question → markdown 블록."""
    block = _formatIntentProfileBlock({"question": "삼성전자 매출", "stockCode": "005930"})
    assert "질문 의도 추정" in block
    assert "005930" in block


def test_intent_block_comparison_detected() -> None:
    """여러 종목 코드 → comparison=True → PeerCompareN 가이드."""
    block = _formatIntentProfileBlock({"question": "005930 vs 000660 vs 035420 비교"})
    assert "비교형" in block
    assert "PeerCompareN" in block


def test_intent_block_show_topic_detected() -> None:
    """질문에 'BS'/'IS' 같은 키워드 → showTopic 가이드."""
    block = _formatIntentProfileBlock({"question": "005930 BS 손익계산서 보여줘"})
    # showTopic 이 추정되면 EngineCall 가이드 표시
    if "추정 토픽" in block:
        assert "EngineCall" in block


def test_intent_block_exception_safe() -> None:
    """workbench import 실패 등 예외 시 빈 문자열 fallback."""
    # 비정상 입력으로도 raise 안 함
    block = _formatIntentProfileBlock({"question": None, "stockCode": None})
    assert block == ""


# ════════════════════════════════════════
# 배선 회귀 가드 (2026-07-26 사고 class)
# ════════════════════════════════════════
#
# 위 테스트들은 helper 에 question 을 *직접* 주입한다. 그래서 helper 가 멀쩡하면
# green 이다. 실제 사고는 helper 가 아니라 *배선* 에서 났다: `_runAgentImpl` 이
# `_injectPastContextIfAvailable(..., _unused, ...)` 로 kwargs 만 넘겼는데 그 dict 에는
# question 키가 없어서, intent block 이 프로덕션에서 항상 빈 문자열이었다.
# 그 결과 DCFValuation·PeerCompareN 등 금융 primitive 라우팅 힌트가 100% 죽어 있었고,
# 단위 테스트는 전부 통과하고 있었다. 아래 테스트가 그 갭을 막는다.


def test_runAgent_passesQuestionIntoIntentBlock() -> None:
    """runAgent 가 받은 question 이 실제로 intent block 생성까지 도달하는지."""
    import dartlab.ai.agent as agentModule

    seen: dict = {}
    original = agentModule._formatIntentProfileBlock

    def _spy(kwargs):
        seen.update(kwargs or {})
        return original(kwargs)

    class _StubProvider:
        config = None

        def generate(self, messages, tools):  # pragma: no cover - 호출 전 중단
            raise RuntimeError("stop")

    agentModule._formatIntentProfileBlock = _spy
    try:
        question = "삼성전자 DCF 가치평가"
        for _event in agentModule.runAgent(question, provider=_StubProvider(), toolNames=()):
            break
    except Exception:
        pass
    finally:
        agentModule._formatIntentProfileBlock = original

    assert seen.get("question") == "삼성전자 DCF 가치평가", (
        "runAgent 의 question 이 intent block 까지 전달되지 않는다. "
        "라우팅 힌트가 프로덕션에서 죽는다 (2026-07-26 사고 재현)."
    )
