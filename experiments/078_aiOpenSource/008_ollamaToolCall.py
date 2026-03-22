"""
실험 ID: 008
실험명: Ollama Tool Calling — /api/chat tools 파라미터 검증

목적:
- Ollama 0.3.0+에서 tool calling API가 실제로 동작하는지 모델별 검증
- dartlab agent loop에서 사용할 수 있는지 판단

가설:
1. qwen3, gemma2는 tool calling을 지원한다
2. llama3.2(3B)는 tool calling 미지원 또는 품질 낮음
3. Ollama /api/chat의 tools 파라미터가 OpenAI 호환 형식과 동일

방법:
1. 설치된 모델 목록 확인
2. 각 모델에 간단한 tool calling 요청 전송
3. 응답에서 tool_calls 파싱 성공 여부 확인
4. 도구 선택 정확도 측정 (5개 시나리오)

결과:
- 테스트: 3개 모델 × 5개 시나리오 = 15 호출
- qwen3: tool_call 100%, 정확도 80% (사업개요→get_company_info 오선택), 평균 7.38s
- gemma2: tool calling 미지원 (http_error) — Ollama가 gemma2에서 tools를 지원하지 않음
- llama3.2 (3B): tool_call 100%, 정확도 100%, 평균 3.54s — 가장 빠르고 정확
- OpenAI 호환 API (/v1/chat/completions): qwen3에서 tool_calls=1 정상 반환

결론:
- 가설 1 수정: qwen3는 지원(80%), gemma2는 미지원
- 가설 2 기각: llama3.2(3B)가 오히려 100% 정확 — 소형 모델이 tool calling에 더 나을 수 있음
- 가설 3 채택: /api/chat과 /v1/ 모두 동작 (qwen3 기준)
- **핵심 발견**: llama3.2가 dartlab agent loop에 적합. gemma2는 tool calling 불가.
- OllamaProvider에 complete_with_tools() 구현 시 /v1/ 경로 활용 가능

실험일: 2026-03-20
"""

import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

OLLAMA_BASE = "http://localhost:11434"

# 테스트용 도구 정의 (Ollama tools format)
TEST_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_company_info",
            "description": "기업의 기본 정보를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_data",
            "description": "기업의 재무/공시 데이터를 조회합니다. BS, IS, CF 등.",
            "parameters": {
                "type": "object",
                "properties": {
                    "module_name": {
                        "type": "string",
                        "description": "조회할 모듈명 (BS, IS, CF, ratios 등)",
                    }
                },
                "required": ["module_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_ratios",
            "description": "재무비율을 계산합니다 (부채비율, ROE 등).",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "show_topic",
            "description": "공시 topic의 데이터를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "조회할 topic"},
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_insight",
            "description": "기업의 7영역 인사이트 분석 등급(A~F)을 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]

# 테스트 시나리오: (질문, 기대하는 도구명)
TEST_SCENARIOS = [
    ("삼성전자의 기본 정보를 알려줘", "get_company_info"),
    ("재무상태표 보여줘", "get_data"),
    ("부채비율과 ROE를 계산해줘", "compute_ratios"),
    ("사업개요를 보여줘", "show_topic"),
    ("인사이트 등급을 알려줘", "get_insight"),
]


def check_ollama() -> list[str]:
    """Ollama 상태 및 모델 확인."""
    try:
        resp = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        models = [m["name"] for m in resp.json().get("models", [])]
        return models
    except requests.ConnectionError:
        return []


def test_tool_calling(model: str, question: str, expected_tool: str) -> dict:
    """단일 모델/질문에 대해 tool calling 테스트."""
    messages = [
        {"role": "system", "content": "당신은 DartLab 재무분석 도우미입니다. 질문에 맞는 도구를 호출하세요."},
        {"role": "user", "content": question},
    ]

    payload = {
        "model": model,
        "messages": messages,
        "tools": TEST_TOOLS,
        "stream": False,
    }

    start = time.perf_counter()
    try:
        resp = requests.post(f"{OLLAMA_BASE}/api/chat", json=payload, timeout=60)
        elapsed = time.perf_counter() - start

        if resp.status_code != 200:
            return {
                "model": model,
                "question": question[:30],
                "expected": expected_tool,
                "status": "http_error",
                "status_code": resp.status_code,
                "latency_s": round(elapsed, 2),
            }

        data = resp.json()
        message = data.get("message", {})
        tool_calls = message.get("tool_calls", [])
        content = message.get("content", "")

        if tool_calls:
            first_call = tool_calls[0]
            called_name = first_call.get("function", {}).get("name", "")
            called_args = first_call.get("function", {}).get("arguments", {})
            correct = called_name == expected_tool

            return {
                "model": model,
                "question": question[:30],
                "expected": expected_tool,
                "called": called_name,
                "arguments": called_args,
                "correct": correct,
                "status": "tool_call",
                "num_calls": len(tool_calls),
                "latency_s": round(elapsed, 2),
            }
        else:
            return {
                "model": model,
                "question": question[:30],
                "expected": expected_tool,
                "status": "no_tool_call",
                "content_preview": content[:100],
                "latency_s": round(elapsed, 2),
            }

    except requests.Timeout:
        return {
            "model": model,
            "question": question[:30],
            "expected": expected_tool,
            "status": "timeout",
            "latency_s": 60.0,
        }
    except (requests.ConnectionError, json.JSONDecodeError) as e:
        return {
            "model": model,
            "question": question[:30],
            "expected": expected_tool,
            "status": "error",
            "error": str(e),
            "latency_s": round(time.perf_counter() - start, 2),
        }


if __name__ == "__main__":
    print("=" * 60)
    print("실험 008: Ollama Tool Calling")
    print("=" * 60)

    models = check_ollama()
    if not models:
        print("\nOllama 미실행 또는 모델 없음")
        sys.exit(1)

    print(f"\n설치된 모델: {models}")

    all_results = {}

    for model in models:
        print(f"\n{'─' * 50}")
        print(f"모델: {model}")
        print(f"{'─' * 50}")

        model_results = []
        for question, expected in TEST_SCENARIOS:
            result = test_tool_calling(model, question, expected)
            model_results.append(result)

            status = result["status"]
            if status == "tool_call":
                mark = "✓" if result["correct"] else "✗"
                print(f"  {mark} {question[:25]:>25} → {result['called']} (expect: {expected}) {result['latency_s']}s")
            elif status == "no_tool_call":
                print(f"  - {question[:25]:>25} → 도구 미호출 (text: {result['content_preview'][:40]}...) {result['latency_s']}s")
            else:
                print(f"  ! {question[:25]:>25} → {status} {result.get('latency_s', '?')}s")

        # 모델별 집계
        total = len(model_results)
        tool_called = sum(1 for r in model_results if r["status"] == "tool_call")
        correct = sum(1 for r in model_results if r.get("correct", False))
        avg_latency = round(sum(r.get("latency_s", 0) for r in model_results) / total, 2)

        print(f"\n  요약: tool_call {tool_called}/{total}, 정확 {correct}/{total}, 평균 {avg_latency}s")
        all_results[model] = {
            "results": model_results,
            "tool_call_rate": round(tool_called / total * 100, 1),
            "accuracy": round(correct / total * 100, 1),
            "avg_latency_s": avg_latency,
        }

    # 종합
    print("\n" + "=" * 60)
    print("=== 모델별 비교 ===")
    print("=" * 60)
    print(f"{'모델':>20} {'tool_call률':>12} {'정확도':>8} {'평균지연':>8}")
    for model, summary in all_results.items():
        print(f"{model:>20} {summary['tool_call_rate']:>10}% {summary['accuracy']:>6}% {summary['avg_latency_s']:>6}s")

    # OpenAI 호환 경로도 테스트
    print("\n--- OpenAI 호환 API (/v1/chat/completions) ---")
    for model in models[:1]:  # 첫 번째 모델만
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "도구를 사용하세요."},
                {"role": "user", "content": "재무상태표 보여줘"},
            ],
            "tools": TEST_TOOLS,
        }
        try:
            resp = requests.post(f"{OLLAMA_BASE}/v1/chat/completions", json=payload, timeout=60)
            data = resp.json()
            choices = data.get("choices", [{}])
            msg = choices[0].get("message", {}) if choices else {}
            tool_calls = msg.get("tool_calls", [])
            print(f"  {model}: status={resp.status_code} tool_calls={len(tool_calls)}")
            if tool_calls:
                print(f"    → {tool_calls[0].get('function', {}).get('name', '?')}")
            else:
                print(f"    → content: {msg.get('content', '')[:80]}")
        except (requests.ConnectionError, requests.Timeout, json.JSONDecodeError) as e:
            print(f"  {model}: ERROR {e}")
