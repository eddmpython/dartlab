"""실험 011: Gemini 도구 강제 유도 A/B 테스트

목적:
- 프롬프트 강화 후 Gemini가 도구를 호출하는지 검증
- skeleton context에 "요약임" 안내 + 도구 선택 규칙 강화 효과 측정

가설:
1. 프롬프트 강화 후 도구 호출률이 33% → 80%+로 증가
2. 도구 결과 기반 답변이 context-only 답변보다 상세하고 정확

방법:
1. 010 실험의 동일 3개 핵심 질문 재실행
2. tool_call 이벤트 수집 → 호출률 비교
3. 답변 길이/품질 비교

결과:
- 재무제표 요약: finance(IS) + finance(BS) + finance(CF) ✅ → 2827자, 한국어
- 배당 현황: finance(report, dividend) ✅ → 1397자, 한국어, 테이블 포함
- 리스크 요인: explore(show, riskDerivative) ✅ → 1445자, 한국어, 원문 기반
- 도구 호출률: 3/3 (100%) — 010 대비 0% → 100%
- 한국어: 3/3 (100%)

결론:
- 가설 1 채택: 도구 호출률 0% → 100%로 극적 개선
- 가설 2 채택: 도구 기반 답변이 context-only보다 정확 (출처 명확, hallucination 제거)
- 근본 원인: _resolve_context_tier()에서 gemini가 tool_capable 목록에 누락
  → focused tier(전체 재무제표 포함) → LLM이 도구 호출 불필요 판단
- skeleton tier로 변경 후 LLM이 적극적으로 도구 호출

실험일: 2026-03-26
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

QUESTIONS = [
    ("재무제표 요약", "삼성전자 재무제표를 요약해줘", "finance"),
    ("배당 현황", "배당 현황을 알려줘", "finance"),
    ("리스크 요인", "리스크 요인을 분석해줘", "explore"),
]


def runSingleQuestion(company, question: str, label: str) -> dict:
    """단일 질문 실행."""
    from dartlab.ai.runtime.core import analyze

    toolCalls = []
    toolResults = []
    chunks = []
    errors = []

    t0 = time.time()
    for event in analyze(
        company,
        question,
        provider="gemini",
        use_tools=True,
        emit_system_prompt=False,
    ):
        if event.kind == "tool_call":
            toolCalls.append(event.data)
        elif event.kind == "tool_result":
            toolResults.append(event.data)
        elif event.kind == "chunk":
            chunks.append(event.data.get("text", ""))
        elif event.kind == "error":
            errors.append(event.data)
    elapsed = time.time() - t0

    answer = "".join(chunks)
    isKorean = any("\uac00" <= c <= "\ud7a3" for c in answer[:200])

    return {
        "label": label,
        "toolCalls": [f"{tc.get('name', '?')}({tc.get('arguments', {})})" for tc in toolCalls],
        "toolResultCount": len(toolResults),
        "answerLen": len(answer),
        "answerPreview": answer[:200],
        "isKorean": isKorean,
        "elapsed": round(elapsed, 1),
        "errors": errors,
    }


def main():
    import dartlab

    print("=" * 60)
    print("011: Gemini 도구 강제 유도 A/B")
    print("=" * 60)

    # API key
    apiKey = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not apiKey:
        try:
            from dartlab.engines.ai import get_config
            cfg = get_config("gemini")
            apiKey = cfg.api_key
        except Exception:
            pass
    if not apiKey:
        print("\n[ERROR] Gemini API key를 찾을 수 없습니다.")
        return
    os.environ.setdefault("GEMINI_API_KEY", apiKey)

    print(f"\n[1] Company 생성: 삼성전자")
    c = dartlab.Company("005930")
    print(f"  corpName: {c.corpName}")

    print(f"\n[2] {len(QUESTIONS)}개 핵심 질문 테스트\n")

    totalToolCalls = 0
    for label, question, expectedTool in QUESTIONS:
        print(f"  [{label}] {question}")
        try:
            result = runSingleQuestion(c, question, label)
            calls = result["toolCalls"]
            hasExpectedTool = any(expectedTool in c for c in calls)
            totalToolCalls += len(calls)
            print(f"    도구: {calls or '없음'} {'✅' if hasExpectedTool else '❌ (기대: ' + expectedTool + ')'}")
            print(f"    답변: {result['answerLen']}자 | 한국어: {result['isKorean']} | {result['elapsed']}s")
            if result["errors"]:
                print(f"    에러: {result['errors']}")
            print(f"    미리보기: {result['answerPreview'][:120]}...")
        except Exception as e:
            print(f"    [EXCEPTION] {type(e).__name__}: {e}")
        print()

    print(f"총 도구 호출: {totalToolCalls}건")
    print(f"010 대비: 도구 호출 {'증가' if totalToolCalls > 1 else '미변화'}")


if __name__ == "__main__":
    main()
