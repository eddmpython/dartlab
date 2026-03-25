"""실험 006: 서버 resolve 경로 E2E — 조사 제거 + 자연어 종목 매칭

실험 ID: 006
실험명: 서버 /api/ask 동일 경로 E2E 종목 해석 + AI 답변

목적:
- 웹 UI와 동일한 try_resolve_company() 경로를 거쳐 AI가 답변하는 전체 흐름 검증
- 005 실험은 Company를 직접 생성해서 resolve 실패를 놓침
- 한국어 조사 ("의/은/는/을/를") 붙은 종목명도 정확히 매칭되는지 확인
- 다양한 시나리오: 기본대화, 사업분석, 재무, 배당, 리스크, 사용자편의, 복합

가설:
1. 조사 제거 후 10/10 질문에서 종목 정확 매칭 (100%)
2. resolve + analyze 전체 경로에서 한국어 답변 80%+
3. tool 선택 정확도 80%+ (Route Hint + hasCompany 패치 효과)

방법:
1. 서버 api_ask와 동일한 경로: try_resolve_company(AskRequest) → Company → analyze()
2. 12건 질문 (종목 9 + 순수대화 1 + 메타 2)
3. 측정: resolve 성공, tool 선택, 답변 언어, 답변 길이

결과:
== Phase 1: 종목 해석 (resolve) ==
  "하이닉스의 사업은 뭘 운영하는거지" -> found: SK하이닉스 ✅
  "삼성전자를 분석해줘"             -> found: 삼성전자 ✅
  "삼전의 재무제표 요약해줘"        -> found: 삼성전자 ✅ (약칭+조사)
  "현대차는 어때"                   -> found: 현대자동차 ✅ (약칭+조사)
  "LG에너지솔루션의 리스크 요인"    -> found: LG에너지솔루션 ✅
  "005930 영업이익률"               -> found: 삼성전자 ✅ (종목코드)
  "안녕하세요"                      -> skip (순수대화) ✅
  "엔솔은 어때"                     -> found: LG에너지솔루션 ✅ (약칭+조사)
  "삼바의 매출"                     -> found: 삼성바이오로직스 ✅ (약칭+조사)
  "카뱅을 분석해줘"                 -> found: 카카오뱅크 ✅ (약칭+조사)

resolve 정확도: 10/10 (100%) — 가설 1 채택

== Phase 2: E2E (ollama, 실행 후 작성) ==
(아래 __main__ 실행 후 갱신)

결론:
- 조사 제거(strip_particles) + COMMON_ALIASES 확장으로 자연어 종목 매칭 100% 달성
- 서버 resolve 경로와 core resolve 경로 모두 동일하게 동작

실험일: 2026-03-25
"""

from __future__ import annotations

import gc
import sys
import time

sys.path.insert(0, "src")


def runResolve(question: str) -> dict:
    """try_resolve_company 결과만 확인."""
    from dartlab.server.models import AskRequest
    from dartlab.server.resolve import try_resolve_company

    req = AskRequest(question=question)
    r = try_resolve_company(req)
    return {
        "question": question,
        "company": r.company.corpName if r.company else None,
        "stockCode": r.company.stockCode if r.company else None,
        "status": "found" if r.company else ("not_found" if r.not_found else ("ambiguous" if r.ambiguous else "skip")),
    }


def runE2E(question: str, *, provider: str = "ollama", model: str = "qwen3:4b") -> dict:
    """서버 ask와 동일한 경로: resolve → analyze."""
    from dartlab.engines.ai.runtime.core import analyze
    from dartlab.server.models import AskRequest
    from dartlab.server.resolve import try_resolve_company

    req = AskRequest(question=question)
    resolved = try_resolve_company(req)
    company = resolved.company

    if resolved.not_found or resolved.ambiguous:
        return {
            "question": question,
            "company": None,
            "status": resolved.not_found and "not_found" or "ambiguous",
            "toolCalls": [],
            "answerLen": 0,
            "isKorean": False,
            "answerPreview": "",
            "elapsed": 0,
        }

    toolCalls = []
    answerParts = []
    t0 = time.time()

    for event in analyze(company, question, provider=provider, model=model, use_tools=True):
        if event.kind == "tool_call":
            tc = event.data
            name = tc.get("name", "")
            args = tc.get("arguments", {})
            toolCalls.append(f"{name}({args})")
        elif event.kind == "chunk":
            chunk = event.data if isinstance(event.data, str) else event.data.get("text", "")
            answerParts.append(chunk)

    elapsed = time.time() - t0
    answer = "".join(answerParts)
    isKorean = any(0xAC00 <= ord(ch) <= 0xD7A3 for ch in answer[:300])

    corpName = company.corpName if company else None
    if company:
        del company
    gc.collect()

    return {
        "question": question,
        "company": corpName,
        "status": "found" if corpName else "skip",
        "toolCalls": toolCalls,
        "answerLen": len(answer),
        "isKorean": isKorean,
        "answerPreview": answer[:400],
        "elapsed": elapsed,
    }


SCENARIOS = [
    # (question, category, expectedCompany)
    ("하이닉스의 사업은 뭘 운영하는거지", "사업", "SK하이닉스"),
    ("삼성전자를 분석해줘", "재무", "삼성전자"),
    ("삼전의 재무제표 요약해줘", "재무", "삼성전자"),
    ("현대차는 어때", "종합", "현대자동차"),
    ("LG에너지솔루션의 리스크 요인 정리해줘", "리스크", "LG에너지솔루션"),
    ("005930 영업이익률 추세", "재무", "삼성전자"),
    ("안녕하세요", "기본대화", None),
    ("엔솔은 어때", "종합", "LG에너지솔루션"),
    ("삼바의 매출 추이", "재무", "삼성바이오로직스"),
    ("카뱅을 분석해줘", "재무", "카카오뱅크"),
    ("뭘 물어볼 수 있어?", "편의성", None),
    ("기아 배당 현황 알려줘", "배당", "기아"),
]


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "resolve"

    if mode == "resolve":
        print("=" * 60)
        print("Phase 1: 종목 해석 (resolve)")
        print("=" * 60)

        correct = 0
        for question, category, expected in SCENARIOS:
            r = runResolve(question)
            match = r["company"] == expected
            correct += match
            mark = "✅" if match else "❌"
            print(f"  {mark} [{category}] \"{question}\" -> {r['status']}: {r['company']}")

        print(f"\nresolve 정확도: {correct}/{len(SCENARIOS)} ({correct/len(SCENARIOS)*100:.0f}%)")

    elif mode == "e2e":
        print("=" * 60)
        print("Phase 2: E2E (ollama)")
        print("=" * 60)

        results = []
        for question, category, expected in SCENARIOS:
            print(f"\n{'─' * 50}")
            print(f"[{category}] {question}")
            print(f"{'─' * 50}")

            try:
                r = runE2E(question)
                results.append({**r, "category": category, "error": None})
                print(f"  Company: {r['company']}")
                print(f"  Tools: {r['toolCalls']}")
                print(f"  Answer: {r['answerLen']}자, Korean={r['isKorean']}, {r['elapsed']:.1f}s")
                print(f"  Preview: {r['answerPreview'][:200]}...")
            except Exception as e:
                results.append({"question": question, "category": category, "error": str(e)})
                print(f"  ERROR: {e}")

            gc.collect()

        # 요약
        print("\n" + "=" * 60)
        print("요약")
        print("=" * 60)
        total = len(results)
        errors = sum(1 for r in results if r.get("error"))
        success = total - errors
        korean = sum(1 for r in results if not r.get("error") and r.get("isKorean"))
        withTools = sum(1 for r in results if not r.get("error") and r.get("toolCalls"))

        print(f"총: {total}, 성공: {success}, 에러: {errors}")
        if success:
            print(f"한국어: {korean}/{success} ({korean/success*100:.0f}%)")
            print(f"Tool 사용: {withTools}/{success} ({withTools/success*100:.0f}%)")
