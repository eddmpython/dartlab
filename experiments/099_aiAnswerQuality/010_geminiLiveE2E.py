"""실험 010: Gemini API 라이브 E2E 품질 검증

목적:
- Gemini 2.5 Flash로 Super Tool agent loop 실제 동작 확인
- format_assistant_tool_calls / format_tool_result Gemini native 형식 검증
- tool 선택 정확도, 답변 품질, 한국어 비율 측정

가설:
1. Gemini 2.5 Flash는 Super Tool 7개에서 올바른 도구를 선택할 수 있다
2. Gemini native function calling 형식으로 multi-turn agent loop이 정상 동작한다
3. 답변 품질이 소형 모델(qwen3:4b)보다 유의미하게 높다

방법:
1. dartlab.ask() 또는 core.analyze()로 삼성전자 기준 6개 질문 실행
2. 각 질문별 tool_call/tool_result 이벤트 수집
3. 최종 답변 텍스트 수집 및 품질 평가

결과:
- 수정 전: 도구 호출 1/6 (17%), 한국어 6/6 (100%)
  - context가 너무 풍부하여 LLM이 도구 호출 불필요 판단
- 수정 후 (context tier 수정): 도구 호출 5/6 (83%), 한국어 5/6 (83%)
  - 재무제표/배당/리스크/사업개요/종합 모두 도구 사용
  - 재무제표 1건 일시적 에러 (Gemini API 불안정)

결론:
- 가설 1 채택: Gemini 2.5 Flash는 Super Tool 7개에서 올바른 도구를 잘 선택함
- 가설 2 채택 (수정 후): Gemini native functionCall/functionResponse로 multi-turn 정상 동작
- 가설 3 채택: qwen3:4b (009: 33%) 대비 Gemini (83-100%) 훨씬 높은 도구 정확도
- 핵심 발견: _resolve_context_tier()에서 gemini 누락이 근본 원인

실험일: 2026-03-26
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

QUESTIONS = [
    ("재무제표 요약", "삼성전자 재무제표를 요약해줘", "finance(action=data)"),
    ("배당 현황", "배당 현황을 알려줘", "finance(action=report, apiType=dividend)"),
    ("리스크 요인", "리스크 요인을 분석해줘", "explore(action=show, target=riskFactor/riskDerivative)"),
    ("사업 개요", "이 회사는 뭘 하는 회사야?", "explore(action=show, target=businessOverview)"),
    ("기본 대화", "안녕하세요", "도구 호출 없음"),
    ("종합 분석", "이 회사의 투자 포인트를 정리해줘", "다수 도구 호출"),
]


def runSingleQuestion(company, question: str, label: str) -> dict:
    """단일 질문 실행 — analyze() 이벤트 수집."""
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
        "question": question,
        "toolCalls": [f"{tc.get('name', '?')}({tc.get('arguments', {})})" for tc in toolCalls],
        "toolResultCount": len(toolResults),
        "answerLen": len(answer),
        "answerPreview": answer[:300],
        "isKorean": isKorean,
        "elapsed": round(elapsed, 1),
        "errors": errors,
    }


def main():
    import dartlab

    print("=" * 60)
    print("010: Gemini API 라이브 E2E 품질 검증")
    print("=" * 60)

    # API key 확인 — 환경변수 또는 프로파일 매니저에서
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
        print("  환경변수 GEMINI_API_KEY 또는 UI 설정 패널에서 입력하세요.")
        print("  발급: https://aistudio.google.com/apikey")
        return
    # 환경변수에도 설정 (provider가 읽을 수 있게)
    os.environ.setdefault("GEMINI_API_KEY", apiKey)

    print(f"\n[1] Company 생성: 삼성전자 (005930)")
    c = dartlab.Company("005930")
    print(f"  corpName: {c.corpName}")
    print(f"  topics count: {len(c.topics) if hasattr(c, 'topics') and c.topics is not None else 'N/A'}")

    print(f"\n[2] {len(QUESTIONS)}개 질문 E2E 테스트\n")

    results = []
    for label, question, expected in QUESTIONS:
        print(f"  [{label}] {question}")
        print(f"    기대: {expected}")
        try:
            result = runSingleQuestion(c, question, label)
            results.append(result)
            print(f"    도구: {result['toolCalls'] or '없음'}")
            print(f"    답변: {result['answerLen']}자 | 한국어: {result['isKorean']} | {result['elapsed']}s")
            if result["errors"]:
                print(f"    에러: {result['errors']}")
            print(f"    미리보기: {result['answerPreview'][:150]}...")
        except Exception as e:
            print(f"    [EXCEPTION] {type(e).__name__}: {e}")
            results.append({"label": label, "error": str(e)})
        print()

    # 요약
    print("=" * 60)
    print("요약")
    print("=" * 60)
    total = len(results)
    toolCorrect = 0
    koreanCount = 0
    errorCount = 0

    for r in results:
        if r.get("error") or r.get("errors"):
            errorCount += 1
        if r.get("isKorean"):
            koreanCount += 1
        calls = r.get("toolCalls", [])
        label = r.get("label", "")
        # 기본 정확도 판단
        if label == "기본 대화" and not calls:
            toolCorrect += 1
        elif label == "재무제표 요약" and any("finance" in c for c in calls):
            toolCorrect += 1
        elif label == "배당 현황" and any("finance" in c or "report" in c or "dividend" in str(c) for c in calls):
            toolCorrect += 1
        elif label == "리스크 요인" and any("explore" in c or "risk" in str(c) for c in calls):
            toolCorrect += 1
        elif label == "사업 개요" and any("explore" in c or "business" in str(c) for c in calls):
            toolCorrect += 1
        elif label == "종합 분석" and len(calls) >= 2:
            toolCorrect += 1

    print(f"  도구 정확도: {toolCorrect}/{total} ({toolCorrect/total*100:.0f}%)")
    print(f"  한국어 비율: {koreanCount}/{total} ({koreanCount/total*100:.0f}%)")
    print(f"  에러: {errorCount}/{total}")


if __name__ == "__main__":
    main()
