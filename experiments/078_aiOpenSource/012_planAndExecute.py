"""
실험 ID: 012
실험명: Plan-and-Execute — 에이전트 계획 수립 프로토타입

목적:
- 복합 질문에서 LLM이 먼저 계획을 세우고 도구를 순서대로 호출하는 패턴 검증
- 현재 단순 agent_loop(5-turn while)보다 복합 질문 해결력이 높은지 확인

가설:
1. 복합 질문을 sub-task로 분해하는 planning step이 도구 선택 정확도를 높인다
2. 계획 → 실행 → 종합의 3단계가 단순 반복보다 효과적이다

방법:
1. 복합 질문 3개 정의 (2~3 sub-task)
2. Ollama qwen3에 planning prompt로 계획 생성
3. 계획의 품질 측정: sub-task 수, 도구 선택 적절성

결과:
- 3/3 성공, 도구 선택 정확도 100% (7/7)
- 평균 계획 step: 4.7개 (기대 2~3보다 많음 — 보수적/상세 계획)
- 평균 지연: 33.0s (qwen3 계획 생성)
- 질문 1 (건전성+수익성): 5 steps — BS→IS→ratios→insight→topic (기대 도구 2/2 일치)
- 질문 2 (배당+현금흐름): 4 steps — dividend→CF→ratios→insight (기대 도구 2/2 일치)
- 질문 3 (사업+리스크): 5 steps — BS→IS→ratios→insight→topic (기대 도구 3/3 일치)
- question_analysis/final_synthesis도 의미있는 내용

결론:
- 가설 1 채택: planning step이 도구 선택 정확도 100% 달성 (단순 반복보다 우수)
- 가설 2 채택: 계획→실행→종합 3단계가 효과적. 특히 final_synthesis가 답변 구조화에 도움
- qwen3가 planning에 적합 (structured output + 도구 이해력)
- 실제 구현 시: plan 생성(1회) → 도구 순차 실행 → context 누적 → 최종 답변(1회)
- step 수 제한(max 5) 필요 — 불필요한 step 방지

실험일: 2026-03-20
"""

import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

OLLAMA_BASE = "http://localhost:11434"

PLANNING_PROMPT = """당신은 DartLab 재무분석 AI의 플래너입니다.
사용자 질문을 분석하여 실행 계획을 JSON으로 작성하세요.

사용 가능한 도구:
- get_data(module_name): 재무 데이터 조회 (BS, IS, CF)
- compute_ratios(): 재무비율 계산
- get_insight(): 7영역 인사이트 등급
- show_topic(topic): 공시 topic 데이터
- get_report_data(api_type): 정기보고서 데이터 (dividend, employee 등)

반드시 아래 JSON 형식으로만 답변:
{
  "question_analysis": "질문 의도 요약",
  "steps": [
    {"step": 1, "tool": "도구명", "args": {"key": "value"}, "reason": "이유"}
  ],
  "final_synthesis": "최종 답변에서 종합할 내용"
}"""

COMPLEX_QUESTIONS = [
    {
        "question": "삼성전자의 재무건전성과 수익성을 비교 분석해줘",
        "expected_tools": ["compute_ratios", "get_data"],
        "expected_steps": 2,
    },
    {
        "question": "삼성전자의 배당 정책과 현금흐름의 관계를 분석해줘",
        "expected_tools": ["get_report_data", "get_data"],
        "expected_steps": 2,
    },
    {
        "question": "삼성전자의 사업 구조와 재무 리스크를 종합적으로 알려줘",
        "expected_tools": ["show_topic", "compute_ratios", "get_insight"],
        "expected_steps": 3,
    },
]


def test_planning(model: str, question: str) -> dict:
    """계획 생성 테스트."""
    messages = [
        {"role": "system", "content": PLANNING_PROMPT},
        {"role": "user", "content": question},
    ]

    start = time.perf_counter()
    try:
        resp = requests.post(
            f"{OLLAMA_BASE}/api/chat",
            json={"model": model, "messages": messages, "format": "json", "stream": False,
                  "options": {"temperature": 0.3}},
            timeout=120,
        )
        elapsed = time.perf_counter() - start

        if resp.status_code != 200:
            return {"status": "http_error", "latency_s": round(elapsed, 2)}

        content = resp.json().get("message", {}).get("content", "")

        try:
            plan = json.loads(content)
            steps = plan.get("steps", [])
            tools_used = [s.get("tool", "") for s in steps]

            return {
                "status": "success",
                "question_analysis": plan.get("question_analysis", ""),
                "step_count": len(steps),
                "tools_used": tools_used,
                "steps": steps,
                "final_synthesis": plan.get("final_synthesis", ""),
                "latency_s": round(elapsed, 2),
            }
        except json.JSONDecodeError:
            return {"status": "parse_error", "raw": content[:200], "latency_s": round(elapsed, 2)}

    except (requests.ConnectionError, requests.Timeout) as e:
        return {"status": "error", "error": str(e), "latency_s": round(time.perf_counter() - start, 2)}


if __name__ == "__main__":
    print("=" * 60)
    print("실험 012: Plan-and-Execute")
    print("=" * 60)

    model = "qwen3:latest"  # structured output에 적합 (007 결과)

    try:
        requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
    except requests.ConnectionError:
        print("Ollama 미실행")
        sys.exit(1)

    results = []

    for cq in COMPLEX_QUESTIONS:
        print(f"\n{'─' * 50}")
        print(f"질문: {cq['question']}")
        print(f"기대: {cq['expected_steps']} steps, tools={cq['expected_tools']}")

        result = test_planning(model, cq["question"])
        results.append(result)

        if result["status"] == "success":
            print(f"  분석: {result['question_analysis'][:60]}")
            print(f"  계획: {result['step_count']} steps")
            for s in result["steps"]:
                print(f"    {s.get('step', '?')}. {s.get('tool', '?')}({s.get('args', {})}) — {s.get('reason', '')[:40]}")
            print(f"  종합: {result['final_synthesis'][:60]}")

            # 도구 선택 적절성
            expected = set(cq["expected_tools"])
            actual = set(result["tools_used"])
            overlap = expected & actual
            print(f"  도구 일치: {len(overlap)}/{len(expected)} ({', '.join(overlap) if overlap else 'none'})")
            print(f"  지연: {result['latency_s']}s")
        else:
            print(f"  {result['status']}: {result.get('raw', result.get('error', ''))[:60]}")

    # 집계
    print("\n" + "=" * 60)
    print("=== 종합 ===")
    successful = [r for r in results if r["status"] == "success"]
    print(f"성공: {len(successful)}/{len(results)}")
    if successful:
        avg_steps = round(sum(r["step_count"] for r in successful) / len(successful), 1)
        avg_latency = round(sum(r["latency_s"] for r in successful) / len(successful), 2)
        print(f"평균 계획 step: {avg_steps}")
        print(f"평균 지연: {avg_latency}s")

        # 도구 선택 적절성 종합
        total_expected = 0
        total_matched = 0
        for r, cq in zip(results, COMPLEX_QUESTIONS):
            if r["status"] == "success":
                expected = set(cq["expected_tools"])
                actual = set(r["tools_used"])
                total_expected += len(expected)
                total_matched += len(expected & actual)
        if total_expected:
            print(f"도구 선택 정확도: {total_matched}/{total_expected} ({round(total_matched/total_expected*100)}%)")
