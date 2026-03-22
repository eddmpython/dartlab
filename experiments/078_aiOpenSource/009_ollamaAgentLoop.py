"""
실험 ID: 009
실험명: Ollama Agent Loop — Ollama tool calling으로 agent_loop 종단 테스트

목적:
- 008에서 llama3.2가 tool calling 100% 정확함을 확인
- 실제 dartlab agent_loop에서 Ollama tool calling이 종단 동작하는지 검증
- OllamaProvider에 complete_with_tools() 추가 시 예상 동작 확인

가설:
1. OllamaProvider에 complete_with_tools()를 구현하면 agent_loop이 정상 동작한다
2. llama3.2로 삼성전자 재무건전성 질문에 올바른 도구를 호출한다
3. 도구 결과를 받은 후 최종 답변을 생성한다

방법:
1. OllamaProvider를 monkeypatch하여 complete_with_tools() 추가
2. agent_loop에서 실제 삼성전자 Company + Ollama 조합 테스트
3. tool_call/tool_result 콜백으로 호출 추적

결과:
- 1차 시도 (전체 39개 도구): 실패 — llama3.2가 도구를 선택하지 못하고 텍스트로 답변
- 2차 시도 (핵심 5개 도구): 성공!
  - get_insight 도구 호출 1회
  - 도구 결과 114 chars 수신
  - 최종 답변 355 chars 생성 (부채비율/유동비율 언급)
  - 수치는 hallucination (llama3.2 3B 한계) — compute_ratios를 호출하지 않음
- /v1/ OpenAI 호환 API에서 tool_calls 정상 반환 확인
- monkeypatch로 OllamaProvider.complete_with_tools() 구현 검증 완료

결론:
- 가설 1 채택: complete_with_tools() 구현하면 agent_loop 정상 동작
- 가설 2 부분 채택: 도구 호출은 하지만 최적 도구 선택은 아님 (get_insight vs compute_ratios)
- 가설 3 채택: 도구 결과 수신 후 최종 답변 생성 성공
- **핵심 발견**: 소형 모델은 도구 수를 5-10개로 제한해야 정확한 선택이 가능
- **다음 단계**: OllamaProvider에 complete_with_tools() 정식 구현 + 도구 수 제한 전략

실험일: 2026-03-20
"""

import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

OLLAMA_BASE = "http://localhost:11434"


def ollama_complete_with_tools(self, messages, tools):
    """OllamaProvider용 complete_with_tools 구현 (monkeypatch용)."""
    from dartlab.engines.ai.types import ToolCall, ToolResponse

    # OpenAI 호환 API 사용
    payload = {
        "model": self.resolved_model,
        "messages": messages,
        "tools": tools,
        "temperature": self.config.temperature,
    }

    try:
        resp = requests.post(
            f"{self.config.base_url or OLLAMA_BASE}/v1/chat/completions",
            json=payload,
            timeout=120,
        )
        data = resp.json()
        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})
        finish = choice.get("finish_reason", "stop")

        answer = msg.get("content") or ""
        tool_calls_raw = msg.get("tool_calls", [])

        tool_calls = []
        for tc in tool_calls_raw:
            func = tc.get("function", {})
            args = func.get("arguments", "{}")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            tool_calls.append(
                ToolCall(
                    id=tc.get("id", f"call_{len(tool_calls)}"),
                    name=func.get("name", ""),
                    arguments=args,
                )
            )

        return ToolResponse(
            answer=answer,
            provider="ollama",
            model=self.resolved_model,
            context_tables=[],
            tool_calls=tool_calls,
            finish_reason="tool_calls" if tool_calls else finish,
        )
    except (requests.ConnectionError, requests.Timeout, json.JSONDecodeError) as e:
        return ToolResponse(
            answer=f"Error: {e}",
            provider="ollama",
            model=self.resolved_model,
            context_tables=[],
            tool_calls=[],
            finish_reason="error",
        )


def run_agent_test():
    """실제 agent_loop 종단 테스트."""
    import dartlab
    from dartlab.engines.ai.agent import agent_loop
    from dartlab.engines.ai.providers.ollama import OllamaProvider
    from dartlab.engines.ai.tools_registry import build_tool_runtime
    from dartlab.engines.ai.types import LLMConfig

    # Ollama 가용성 확인
    try:
        resp = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        models = [m["name"] for m in resp.json().get("models", [])]
    except requests.ConnectionError:
        print("Ollama 미실행")
        return

    # llama3.2 우선, 없으면 첫 번째 모델
    model = "llama3.2:latest" if "llama3.2:latest" in models else models[0]
    print(f"모델: {model}")

    # Provider 생성 + monkeypatch
    config = LLMConfig(provider="ollama", model=model, temperature=0.3, max_tokens=1024)
    provider = OllamaProvider(config)

    # complete_with_tools를 monkeypatch
    import types
    provider.complete_with_tools = types.MethodType(ollama_complete_with_tools, provider)
    provider.format_tool_result = lambda tool_call_id, result: {
        "role": "tool", "tool_call_id": tool_call_id, "content": result
    }
    provider.format_assistant_tool_calls = lambda answer, tool_calls: {
        "role": "assistant",
        "content": answer,
        "tool_calls": [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.name, "arguments": json.dumps(tc.arguments, ensure_ascii=False)},
            }
            for tc in tool_calls
        ],
    }

    # Company
    c = dartlab.Company("005930")
    runtime = build_tool_runtime(c, name="ollama-test")

    # 소형 모델은 전체 39개 도구에 혼란 → 핵심 5개만 남김
    core_tools = {"compute_ratios", "get_data", "get_company_info", "get_insight", "show_topic"}
    original_schemas = runtime.get_tool_schemas
    runtime.get_tool_schemas = lambda: [s for s in original_schemas() if s.get("function", {}).get("name") in core_tools]
    print(f"도구 수: {len(runtime.get_tool_schemas())}개 (핵심만)")

    # 콜백으로 추적
    calls = []
    results = []

    def on_tool_call(name, args):
        calls.append({"name": name, "args": args})
        print(f"  → tool_call: {name}({args})")

    def on_tool_result(name, result):
        results.append({"name": name, "result_len": len(result)})
        print(f"  ← tool_result: {name} ({len(result)} chars)")

    messages = [
        {"role": "system", "content": "당신은 DartLab 재무분석 도우미입니다. 도구를 사용하여 분석하세요."},
        {"role": "user", "content": "삼성전자의 재무건전성을 분석해줘. 부채비율과 유동비율을 알려줘."},
    ]

    print("\n질문: 삼성전자의 재무건전성을 분석해줘.")
    print("agent_loop 시작 (max_turns=3)...\n")

    answer = agent_loop(
        provider,
        messages,
        c,
        max_turns=3,
        runtime=runtime,
        on_tool_call=on_tool_call,
        on_tool_result=on_tool_result,
    )

    print(f"\n{'─' * 50}")
    print(f"최종 답변 ({len(answer)} chars):")
    print(answer[:500])
    if len(answer) > 500:
        print("...")

    print(f"\n도구 호출: {len(calls)}회")
    for c_info in calls:
        print(f"  - {c_info['name']}({c_info['args']})")

    print(f"\n도구 결과: {len(results)}회")
    for r_info in results:
        print(f"  - {r_info['name']} → {r_info['result_len']} chars")

    # 성공 판정
    success = len(answer) > 50 and len(calls) > 0
    print(f"\n종단 테스트: {'성공' if success else '실패'}")

    return {
        "model": model,
        "answer_length": len(answer),
        "tool_calls": len(calls),
        "tool_results": len(results),
        "tools_called": [c_info["name"] for c_info in calls],
        "success": success,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("실험 009: Ollama Agent Loop")
    print("=" * 60)

    result = run_agent_test()
    if result:
        print(f"\n결과: {json.dumps(result, ensure_ascii=False, indent=2)}")
