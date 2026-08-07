"""Agent loops — provider-driven ReAct over canonical tool whitelist.

`runToolLoop` 은 어떤 LLMProvider 가 와도 같은 도구 화이트리스트로 분석을
밀어붙인다. chat-native 루프 (`ai/agent.py`) 가 본 모듈을 호출해 도구 자율
조합을 수행한다 — graph 노드 강제 X (회귀 방지: memory/engineering.md 7절).
"""

from .runToolLoop import AgentResult, runToolLoop

__all__ = ["AgentResult", "runToolLoop"]
