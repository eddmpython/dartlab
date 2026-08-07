"""run_workbench — chat-native 진입점이 5 패스 작업대로 elevate 하는 meta tool.

agent.runAgent 의 자율 도구 호출 안에서 호출된다. 내부적으로 WorkbenchLoop 를 동기 실행하고
누적된 refs + answer 를 ToolResult 로 돌려준다.

P-revised: intent regex 키워드 routing 폐기 (`isAnalysisIntent` 삭제). 작업대 활성 경로는
(1) 사용자 명시 mode="analyze" 또는 (2) 모델이 본 도구 호출, 두 가지로 한정 — 회귀 가드
memory/engineering.md 7절.
"""

from __future__ import annotations

from typing import Any

from dartlab.ai.contracts import Ref

from .types import ToolResult


def runWorkbench(
    question: str,
    *,
    stockCode: str | None = None,
    market: str | None = None,
    **kwargs: Any,
) -> ToolResult:
    """5 패스 (BRIEF→WORK→CRITIQUE→COMPOSE→GATE→HARVEST) 작업대 동기 실행.

    Args:
        question: 작업대로 elevate 할 질문 (재정식화 권장)
        stockCode: 종목코드 — KR 6 자리 또는 US ticker (선택)
        market: "KR" / "US" / null (stockCode 동행 권장)

    Returns:
        ToolResult.refs 에 작업대 누적 refs + verifyRef 포함. data["answer"] 에 본문.
    """
    if not question or not question.strip():
        return ToolResult(False, "run_workbench: question 비어 있음", error="empty_question")

    # 지연 import — circular 회피 (workbench → tools → workbench 흐름).
    from dartlab.ai.workbench.loop import GRAPH_NODES, WorkbenchLoop

    forwarded: dict[str, Any] = {}
    if stockCode:
        forwarded["stockCode"] = str(stockCode)
    if market:
        forwarded["market"] = str(market)
    # provider/threadId 등은 호출자 (kernel) 가 forward — kwargs 통째로.
    forwarded.update({k: v for k, v in kwargs.items() if k not in {"stockCode", "market"}})

    accumulated_refs: list[Ref] = []
    answer_text = ""
    verification: dict[str, Any] = {}
    failure: str | None = None

    for event in WorkbenchLoop().stream(question, **forwarded):
        if event.kind == "answer":
            answer_text = str(event.data.get("text") or answer_text)
        elif event.kind == "done":
            for raw in event.data.get("refs") or []:
                if not isinstance(raw, dict):
                    continue
                accumulated_refs.append(
                    Ref(
                        id=str(raw.get("id") or ""),
                        kind=str(raw.get("kind") or ""),
                        title=str(raw.get("title") or ""),
                        source=str(raw.get("source") or ""),
                        payload=raw.get("payload") if isinstance(raw.get("payload"), dict) else {},
                    )
                )
            verification = event.data.get("verification") or {}
            response_meta = event.data.get("responseMeta") or {}
            if response_meta.get("responseStatus") == "failed":
                failure = str(response_meta.get("failureReason") or "workbench_failed")

    summary = (answer_text or "").strip().splitlines()[0] if answer_text else "작업대 실행 완료"
    return ToolResult(
        ok=failure is None and bool(answer_text),
        summary=summary[:200],
        refs=accumulated_refs,
        data={
            "answer": answer_text,
            "verification": verification,
            "graphNodes": list(GRAPH_NODES),
        },
        error=failure,
    )
