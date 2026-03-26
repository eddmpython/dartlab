"""실험 009: Super Tool 라이브 E2E — ollama qwen3:4b 실제 답변 품질

실험 ID: 009
실험명: Super Tool 모드 라이브 AI 답변 품질 검증

목적:
- Super Tool 모드(8개 도구)에서 ollama qwen3:4b가 올바른 도구를 선택하는지
- 한국어 질문에 한국어로 답변하는지
- "비용의 성격별분류" 같은 난이도 높은 질문에서 정확한 topic을 찾는지
- 기존 96개 도구 모드 대비 개선 확인

가설:
1. tool 선택 정확도 80%+ (기존 50%대)
2. 한국어 답변 비율 80%+ (기존 50%대)
3. "비용의 성격별분류" → explore(search) 또는 explore(show, fsSummary/consolidatedNotes)
4. 에러율 0%

방법:
1. 삼성전자(005930) + Super Tool + ollama qwen3:4b
2. 10개 질문 시나리오
3. 측정: tool 호출, 답변 길이, 한국어 여부, 답변 미리보기

결과:

=== qwen3:4b 전체 10건 실행 (Super Tool 8개 도구, max_turns=5) ===

| 질문 | 기대 | 실제 tool | 답변 | Ko | 평가 |
|------|------|----------|------|---|------|
| 하이닉스 사업 | explore(show,businessOverview) | system(searchCompany)+market(price) | 442자 영어 에러설명 | X | ❌ |
| 재무제표 요약 | finance(data,IS/BS) | (없음) | 713자 hallucination | O | ❌ 허위수치 |
| 비용성격별분류 | explore(search/show) | (없음) | 320자 추천만 | O | △ 올바른 제안이나 미실행 |
| 배당 현황 | finance(report,dividend) | finance(report,dividend) ✅ + finance(stockCode=에러) | 645자 영어 에러 | X | △ 1st call 정확 |
| 리스크 요인 | explore(show,riskDerivative) | analyze(insight) | 850자 영어 에러 | X | ❌ |
| 안녕하세요 | 도구없음 | (없음) ✅ | 81자 | O | ✅ |
| 뭘 물어볼 수 있어 | system(features) | system(features) ✅ | 206자 영어 에러 | X | △ tool 정확 but import 에러 |
| 경영진 분석 | explore(show,mdnaOverview) | analyze(insight)+system(spec) | 82자 | O | ❌ |
| 최대주주 현황 | finance(report,majorHolder) | finance(report,majorHolder) ✅ + chart(에러) | 547자 영어 에러 | X | △ 1st call 정확 |
| 원재료 조달 | explore(show,rawMaterial) | finance(data,sections) | 3044자 영어 | X | ❌ |

핵심 수치 (4b):
- tool 정확도 (1st call): 3/9 (33%) — 배당/최대주주/편의성만 정확
- 한국어: 4/10 (40%) — 가설2 기각
- hallucination: 2/10 (재무/비용) — 도구 없이 답변 시 100% 허위
- import 에러: 3건 (chart, insight, features)

=== qwen3:latest (8b) 추가 3건 (max_turns=3) ===

| 질문 | 기대 | 실제 tool | 답변 | Ko | 평가 |
|------|------|----------|------|---|------|
| 재무제표 요약 | finance(data,IS) | finance(data,sections) — wrong module | 3548자 무의미 | O | △ |
| 리스크 요인 | explore(show,riskDerivative) | (없음) | 1840자 hallucination | O | ❌ |
| 배당 현황 | finance(report,dividend) | explore(topic='dividend') — action 누락 | 1036자 에러 | O | ❌ |

- tool 정확도: 0/3 (0%), 한국어: 100%

결론:
- 가설1 기각: tool 정확도 qwen3:4b=33%, qwen3:8b=0%. Super Tool enum/라벨 개선에도 불구하고 소형 모델은 action dispatch 패턴을 이해하지 못함
- 가설2 부분채택: 한국어 4b=75%, 8b=100%. 8b는 한국어 일관
- 가설3 미검증: 비용성격별분류 질문까지 도달 못함 (기본 질문부터 실패)
- 가설4 기각: 에러 다수 (chart import, system 반복 등)

개선 방안 수집:
1. [P0] Plan-Execute 패턴 필수: 소형 모델은 agent_loop(LLM이 스스로 도구 선택)이 작동하지 않음. 시스템이 질문을 분류하고 도구 호출 계획을 생성해야 함
2. [P0] Hallucination 방지: 도구 호출 없이 답변 생성 시 "데이터를 조회하겠습니다" 강제 삽입 또는 tool 호출 필수 모드
3. [P1] chart Super Tool import 에러 수정 (완료)
4. [P1] system 프롬프트에 도구 선택 규칙 강화 (완료, 효과 미미)
5. [P2] 8b 이상 모델에서 재검증 필요 (14b+ 권장)
6. [P2] 영어 답변 회귀 — 4b 모델에서 한국어 강제가 약함

실험일: 2026-03-25
"""

from __future__ import annotations

import gc
import sys
import time

sys.path.insert(0, "src")

SCENARIOS = [
    # (question, category, expectedAction)
    ("하이닉스의 사업은 뭘 운영하는거지", "사업", "explore(show, businessOverview)"),
    ("삼성전자 재무제표 요약해줘", "재무", "finance(data, IS/BS)"),
    ("비용의 성격별분류 5년치 보자", "주석", "explore(search/show, fsSummary/consolidatedNotes)"),
    ("배당 현황 알려줘", "배당", "finance(report, dividend)"),
    ("이 회사의 리스크 요인은?", "리스크", "explore(show, riskDerivative)"),
    ("안녕하세요", "기본대화", "도구 없음"),
    ("뭘 물어볼 수 있어?", "편의성", "system(features)"),
    ("경영진 분석 의견 보여줘", "MD&A", "explore(show, mdnaOverview)"),
    ("최대주주 현황", "주주", "finance(report, majorHolder)"),
    ("원재료 조달 현황", "원재료", "explore(show, rawMaterial)"),
]


def runOne(question: str, company):
    """하나의 질문을 Super Tool 모드로 실행."""
    from dartlab.ai.runtime.core import analyze

    toolCalls = []
    answerParts = []
    t0 = time.time()

    for event in analyze(
        company,
        question,
        provider="ollama",
        model="qwen3:4b",
        use_tools=True,
        max_turns=5,
    ):
        if event.kind == "tool_call":
            tc = event.data
            name = tc.get("name", "")
            args = tc.get("arguments", {})
            toolCalls.append(f"{name}({args})")
        elif event.kind == "chunk":
            chunk = event.data if isinstance(event.data, str) else event.data.get("text", "")
            answerParts.append(chunk)
        elif event.kind == "error":
            answerParts.append(f"[ERROR: {event.data}]")

    elapsed = time.time() - t0
    answer = "".join(answerParts)
    isKorean = any(0xAC00 <= ord(ch) <= 0xD7A3 for ch in answer[:300])

    return {
        "toolCalls": toolCalls,
        "answerLen": len(answer),
        "isKorean": isKorean,
        "elapsed": elapsed,
        "answerPreview": answer[:300],
    }


def main():
    import dartlab

    company = dartlab.Company("005930")
    print(f"Company: {company.corpName}")
    print("=" * 70)

    results = []
    for question, category, expected in SCENARIOS:
        print(f"\n{'─' * 60}")
        print(f"[{category}] {question}")
        print(f"  기대: {expected}")
        print(f"{'─' * 60}")

        try:
            r = runOne(question, company)
            results.append({**r, "question": question, "category": category, "expected": expected, "error": None})
            print(f"  Tools: {r['toolCalls']}")
            print(f"  답변: {r['answerLen']}자, Korean={r['isKorean']}, {r['elapsed']:.1f}s")
            print(f"  미리보기: {r['answerPreview'][:200]}...")
        except Exception as e:
            results.append({"question": question, "category": category, "error": str(e)})
            print(f"  ERROR: {e}")

        gc.collect()

    # 요약
    print("\n" + "=" * 70)
    print("요약")
    print("=" * 70)

    total = len(results)
    errors = sum(1 for r in results if r.get("error"))
    success = total - errors
    withTools = sum(1 for r in results if not r.get("error") and r.get("toolCalls"))
    korean = sum(1 for r in results if not r.get("error") and r.get("isKorean"))

    print(f"총: {total}, 성공: {success}, 에러: {errors}")
    if success:
        print(f"Tool 사용: {withTools}/{success}")
        print(f"한국어: {korean}/{success}")

    # 도구 선택 정확도 판정
    print("\n--- 도구 선택 상세 ---")
    for r in results:
        if r.get("error"):
            print(f"  ❌ [{r['category']}] ERROR: {r['error']}")
            continue
        calls = r.get("toolCalls", [])
        callStr = ", ".join(calls) if calls else "(없음)"
        print(f"  [{r['category']}] {r['question'][:30]}...")
        print(f"    기대: {r['expected']}")
        print(f"    실제: {callStr}")

    del company
    gc.collect()


if __name__ == "__main__":
    main()
