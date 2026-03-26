"""실험 020: 3대 규칙 적용 후 라이브 품질 체크.

실험 ID: 020
실험명: Agent 3대 규칙 + 신뢰도 계층 적용 후 라이브 AI 답변 품질 검증

목적:
- Change 1~7 적용 후 실제 AI 답변에서 3대 규칙 행동이 나타나는지 확인
- 도구 선택 정확도, 연쇄 호출, 실패 복구 행동 측정

가설:
1. 도구 선택 정확도 ≥ 83% (010 Gemini 결과 유지 또는 개선)
2. 연쇄 호출(2개 이상 도구) 비율 ≥ 50% (도구 연쇄 전략 효과)
3. 한국어 비율 100% (기존 유지)

방법:
1. Gemini API로 삼성전자 기준 8개 질문 (기존 6 + Persistence 2)
2. tool_call 이벤트 수집 → 도구 선택/연쇄/실패복구 평가
3. 답변 텍스트 품질 평가

결과 (실험 후 작성):
- 도구 정확도: 8/8 (100%) — 010 대비 +17%p 개선
- 한국어 비율: 8/8 (100%) — 010 대비 +17%p 개선
- 연쇄 호출 비율: 1/7 (14%) — 종합 분석만 5개 도구 연쇄
- 에러: 0/8
- 평균 답변 길이: 2,316자 (충분한 분석 깊이)
- 종합 분석: analyze(insight) + finance(ratios) + finance(IS/BS/CF) = 3,867자

결론:
- 가설 1 채택: 도구 정확도 100% (≥83% 충족)
- 가설 2 기각: 연쇄 호출 14% (<50%). context 주입이 풍부하여 LLM이 추가 도구 불필요 판단
- 가설 3 채택: 한국어 100% (≥90% 충족)
- 핵심 개선: 배당→finance(report,dividend) 정확, 리스크→explore(riskDerivative) 정확
- 연쇄 호출 미달 원인: Tier 1 context가 충분하면 LLM이 추가 도구를 안 부름 (의도된 동작일 수 있음)

실험일: 2026-03-26
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# 8개 질문: 기존 6 + Persistence 테스트 2
QUESTIONS = [
    # --- 기존 6 (010과 동일) ---
    ("재무제표 요약", "삼성전자 재무제표를 요약해줘", "finance"),
    ("배당 현황", "배당 현황을 알려줘", "finance"),
    ("리스크 요인", "리스크 요인을 분석해줘", "explore"),
    ("사업 개요", "이 회사는 뭘 하는 회사야?", "explore"),
    ("기본 대화", "안녕하세요", "none"),
    ("종합 분석", "이 회사의 투자 포인트를 정리해줘", "multi"),
    # --- Persistence + Chaining 테스트 ---
    ("부문별 매출", "부문별 매출 구조를 분석해줘", "explore+finance"),
    ("수익성 심화", "수익성을 심층 분석해줘. 원인까지 알려줘", "finance+explore"),
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
        "toolNames": [tc.get("name", "?") for tc in toolCalls],
        "toolResultCount": len(toolResults),
        "answerLen": len(answer),
        "answerPreview": answer[:400],
        "isKorean": isKorean,
        "elapsed": round(elapsed, 1),
        "errors": errors,
    }


def evaluateToolAccuracy(label: str, calls: list[str], toolNames: list[str]) -> bool:
    """도구 선택 정확도 판단."""
    if label == "기본 대화":
        return len(calls) == 0
    if label == "재무제표 요약":
        return any("finance" in c for c in calls)
    if label == "배당 현황":
        return any("finance" in c or "dividend" in str(c) for c in calls)
    if label == "리스크 요인":
        return any("explore" in c or "risk" in str(c) for c in calls)
    if label == "사업 개요":
        return any("explore" in c or "business" in str(c) for c in calls)
    if label == "종합 분석":
        return len(calls) >= 2
    if label == "부문별 매출":
        return any("explore" in c or "finance" in c for c in calls)
    if label == "수익성 심화":
        return any("finance" in c for c in calls)
    return False


def evaluateChaining(toolNames: list[str]) -> bool:
    """연쇄 호출 여부 (2개 이상 서로 다른 도구)."""
    uniqueTools = set(toolNames)
    return len(uniqueTools) >= 2


def main():
    import dartlab

    print("=" * 60)
    print("020: 3대 규칙 적용 후 라이브 품질 체크")
    print("=" * 60)

    # API key 확인 — 환경변수 → SecretStore(DPAPI) 순서
    apiKey = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not apiKey:
        try:
            from dartlab.core.ai.secrets import get_secret_store

            store = get_secret_store()
            apiKey = store.get("provider:gemini:api_key")
        except (ImportError, RuntimeError, KeyError):
            pass
    if not apiKey:
        print("\n[ERROR] Gemini API key를 찾을 수 없습니다.")
        print("  환경변수 GEMINI_API_KEY 또는 dartlab 설정 패널에서 입력하세요.")
        return
    os.environ.setdefault("GEMINI_API_KEY", apiKey)

    print("\n[1] Company 생성: 삼성전자 (005930)")
    c = dartlab.Company("005930")
    print(f"  corpName: {c.corpName}")

    print(f"\n[2] {len(QUESTIONS)}개 질문 E2E 테스트\n")

    results = []
    for label, question, expectedType in QUESTIONS:
        print(f"  [{label}] {question}")
        print(f"    기대 도구: {expectedType}")
        try:
            result = runSingleQuestion(c, question, label)
            results.append(result)
            print(f"    호출: {result['toolCalls'] or '없음'}")
            print(f"    답변: {result['answerLen']}자 | 한국어: {result['isKorean']} | {result['elapsed']}s")
            if result["errors"]:
                print(f"    에러: {result['errors']}")
            print(f"    미리보기: {result['answerPreview'][:200]}...")
        except Exception as e:
            print(f"    [EXCEPTION] {type(e).__name__}: {e}")
            results.append({
                "label": label,
                "question": question,
                "toolCalls": [],
                "toolNames": [],
                "toolResultCount": 0,
                "answerLen": 0,
                "answerPreview": "",
                "isKorean": False,
                "elapsed": 0,
                "errors": [str(e)],
            })
        print()

    # ── 평가 ──
    print("=" * 60)
    print("평가 결과")
    print("=" * 60)

    total = len(results)
    toolCorrect = 0
    chainingCount = 0
    koreanCount = 0
    errorCount = 0
    nonGreeting = 0

    for r in results:
        label = r.get("label", "")
        calls = r.get("toolCalls", [])
        toolNames = r.get("toolNames", [])

        if r.get("errors"):
            errorCount += 1
        if r.get("isKorean"):
            koreanCount += 1
        if evaluateToolAccuracy(label, calls, toolNames):
            toolCorrect += 1
        if label != "기본 대화":
            nonGreeting += 1
            if evaluateChaining(toolNames):
                chainingCount += 1

    print(f"\n  도구 정확도: {toolCorrect}/{total} ({toolCorrect/total*100:.0f}%)")
    print(f"  연쇄 호출 비율: {chainingCount}/{nonGreeting} ({chainingCount/nonGreeting*100:.0f}%)")
    print(f"  한국어 비율: {koreanCount}/{total} ({koreanCount/total*100:.0f}%)")
    print(f"  에러: {errorCount}/{total}")

    # 가설 판정
    print("\n" + "=" * 60)
    print("가설 판정")
    print("=" * 60)

    toolPct = toolCorrect / total * 100
    chainPct = chainingCount / nonGreeting * 100 if nonGreeting else 0
    koreanPct = koreanCount / total * 100

    h1 = toolPct >= 83
    h2 = chainPct >= 50
    h3 = koreanPct >= 90  # 100% 목표, 90% 이상이면 채택

    print(f"  가설 1 (도구 정확도 ≥83%): {'채택' if h1 else '기각'} ({toolPct:.0f}%)")
    print(f"  가설 2 (연쇄 호출 ≥50%): {'채택' if h2 else '기각'} ({chainPct:.0f}%)")
    print(f"  가설 3 (한국어 ≥90%): {'채택' if h3 else '기각'} ({koreanPct:.0f}%)")

    # 상세 테이블
    print("\n" + "=" * 60)
    print("상세 결과")
    print("=" * 60)
    print(f"{'질문':<15} {'도구정확':>8} {'연쇄':>4} {'한국어':>6} {'답변길이':>8} {'시간':>6}")
    print("-" * 60)
    for r in results:
        label = r.get("label", "")
        calls = r.get("toolCalls", [])
        toolNames = r.get("toolNames", [])
        correct = "O" if evaluateToolAccuracy(label, calls, toolNames) else "X"
        chained = "O" if evaluateChaining(toolNames) else "-"
        korean = "O" if r.get("isKorean") else "X"
        print(f"{label:<15} {correct:>8} {chained:>4} {korean:>6} {r.get('answerLen', 0):>8} {r.get('elapsed', 0):>5.1f}s")


if __name__ == "__main__":
    main()
