"""실험 017: 결정론적 도구 호출 평가 (BFCL-style)

목적:
- BFCL(Berkeley Function Calling Leaderboard) 방식: 도구 호출을 AST 레벨에서
  결정론적으로 검증. LLM-as-judge가 아닌 정확한 매칭.
- 013/014의 10개 질문을 포함하여 15개 표준 평가 세트 구성.
- 모든 모델에서 재사용 가능한 결정론적 eval runner.

가설:
1. Phase 1-4 적용 후 Gemini 기준 전체 도구 정확도 85%+ 달성
2. 자동 eval runner로 회귀 감지 가능

방법:
1. 15개 표준 질문 (재무 5 + 공시 3 + 분석 3 + 시장 1 + 메타 2 + 대화 1)
2. 각 질문별 expected: (tool, action, 핵심 param)
3. 실제 도구 호출과 AST 매칭: 도구명 일치 + action 일치 + 필수 param 포함
4. Gemini 2.5 Flash로 실행

결과:
- 전체 정확도: 10/15 (67%) — strict 매칭
- 도구명 정확도: 11/15 (73%)
- action 정확도: 10/15 (67%)
- param 정확도: 14/15 (93%)
- 에러: 0/15

| 카테고리 | 정확도 |
|---------|--------|
| 재무 | 5/5 (100%) |
| 공시 | 2/3 (67%) |
| 분석 | 1/3 (33%) |
| 시장 | 0/1 (0%) |
| 메타 | 1/2 (50%) |
| 대화 | 1/1 (100%) |

실패 5건 분석:
1. 공시검색: explore(show, rawMaterial) — LLM이 search 대신 직접 topic 조회 (합리적 대안)
2. 인사이트: light mode로 빠져서 agent loop 미진입 (질문 분류 이슈)
3. 섹터: explore(info) 선택 — 기업 정보에 섹터가 포함되므로 합리적
4. 주가: system(searchCompany) — market tool 미인식 (기존 이슈)
5. 데이터상태: light mode로 빠져서 tool 미호출

실질 정확도 (합리적 대안 수용): 12/15 (80%)
- 공시검색, 섹터는 LLM이 합리적 대안을 선택한 것으로 판단

결론:
- 가설 1 부분 채택: strict 67% / 실질 80% (85% 미달)
- 가설 2 채택: 자동 eval runner로 15개 케이스 결정론적 검증 가능
- 재무 카테고리 100% — Phase 1-2(ACI + Response Contract + tool_choice)가 핵심 효과
- 남은 개선점:
  - **질문 분류 이슈**: "투자등급", "데이터 상태" 등이 light mode로 빠지는 문제
  - **market tool 노출**: tool_choice=any에서도 market 대신 system 선택
  - 이는 description/contract 문제가 아닌 core.py의 질문 분류 로직 문제

실험일: 2026-03-26
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# ── 15개 표준 평가 세트 ──
# (label, question, expectedTool, expectedAction, expectedParam)
# expectedTool=None → 도구 호출 없어야 함
EVAL_CASES = [
    # 재무 (5)
    ("재무제표", "재무제표를 요약해줘", "finance", "data", "IS"),
    ("배당", "배당 현황을 알려줘", "finance", "report", "dividend"),
    ("ROE", "ROE가 어떻게 되나요?", "finance", "ratios", ""),
    ("성장률", "매출 성장률을 알려줘", "finance", "", ""),  # data 또는 growth
    ("재무건전성", "부채비율과 유동비율은?", "finance", "ratios", ""),
    # 공시 (3)
    ("사업개요", "이 회사는 뭘 하는 회사야?", "explore", "show", "businessOverview"),
    ("리스크", "리스크 요인을 분석해줘", "explore", "show", "risk"),
    ("공시검색", "원재료 관련 공시 내용을 찾아줘", "explore", "search", "원재료"),
    # 분석 (3)
    ("인사이트", "투자등급이 어떻게 돼?", "analyze", "insight", ""),
    ("밸류에이션", "적정주가를 알려줘", "analyze", "valuation", ""),
    ("섹터", "이 회사 업종이 뭐야?", "analyze", "sector", ""),
    # 시장 (1)
    ("주가", "현재 주가가 얼마야?", "market", "price", ""),
    # 메타 (2)
    ("기능문의", "뭘 물어볼 수 있어?", "system", "features", ""),
    ("데이터상태", "어떤 데이터가 준비돼 있어?", "system", "dataStatus", ""),
    # 대화 (1)
    ("대화", "안녕하세요", None, None, None),
]


def runSingleCase(company, question: str) -> dict:
    """단일 질문 실행 — 첫 tool_call 수집."""
    from dartlab.engines.ai.runtime.core import analyze

    toolCalls = []
    chunks = []

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
        elif event.kind == "chunk":
            chunks.append(event.data.get("text", ""))
    elapsed = time.time() - t0

    firstCall = toolCalls[0] if toolCalls else None
    return {
        "firstToolName": firstCall.get("name", "") if firstCall else None,
        "firstToolArgs": firstCall.get("arguments", {}) if firstCall else None,
        "totalToolCalls": len(toolCalls),
        "answerLen": len("".join(chunks)),
        "elapsed": round(elapsed, 1),
    }


def evaluateCase(result: dict, expected: tuple) -> dict:
    """AST-level 매칭."""
    _, _, expTool, expAction, expParam = expected

    toolName = result["firstToolName"]
    toolArgs = result["firstToolArgs"] or {}

    if expTool is None:
        toolMatch = toolName is None
        actionMatch = True
        paramMatch = True
    else:
        toolMatch = toolName == expTool
        actualAction = toolArgs.get("action", "")
        # action이 비어있으면 도구명만 매칭
        actionMatch = actualAction == expAction if expAction else True
        if expParam:
            allArgs = str(toolArgs)
            paramMatch = expParam.lower() in allArgs.lower()
        else:
            paramMatch = True

    return {
        **result,
        "toolMatch": toolMatch,
        "actionMatch": actionMatch,
        "paramMatch": paramMatch,
        "allMatch": toolMatch and actionMatch and paramMatch,
    }


def main():
    import dartlab

    print("=" * 60)
    print("017: 결정론적 도구 호출 평가 (BFCL-style)")
    print("=" * 60)

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

    print("\n[1] Company 생성: 삼성전자 (005930)")
    c = dartlab.Company("005930")
    print(f"  corpName: {c.corpName}")

    print(f"\n[2] {len(EVAL_CASES)}개 eval 케이스 실행\n")

    results = []
    for case in EVAL_CASES:
        label, question, expTool, expAction, expParam = case
        expStr = f"{expTool}({expAction}, {expParam})" if expTool else "도구 없음"
        print(f"  [{label}] {question}")
        print(f"    기대: {expStr}")

        try:
            result = runSingleCase(c, question)
            evaluated = evaluateCase(result, case)
            results.append({"label": label, **evaluated})

            status = "✅" if evaluated["allMatch"] else "❌"
            actualTool = result["firstToolName"]
            actualArgs = result["firstToolArgs"]
            print(f"    실제: {actualTool}({actualArgs}) | {result['elapsed']}s")
            print(
                f"    판정: {status} (tool:{evaluated['toolMatch']}, action:{evaluated['actionMatch']}, param:{evaluated['paramMatch']})"
            )
        except Exception as e:
            print(f"    [EXCEPTION] {type(e).__name__}: {e}")
            results.append({"label": label, "allMatch": False, "error": str(e)})
        print()

    # ── 요약 ──
    print("=" * 60)
    print("요약")
    print("=" * 60)
    total = len(results)
    allMatch = sum(1 for r in results if r.get("allMatch"))
    toolMatch = sum(1 for r in results if r.get("toolMatch", False))
    actionMatch = sum(1 for r in results if r.get("actionMatch", False))
    paramMatch = sum(1 for r in results if r.get("paramMatch", False))
    errCount = sum(1 for r in results if r.get("error"))

    print(f"  전체 정확도: {allMatch}/{total} ({allMatch / total * 100:.0f}%)")
    print(f"  도구명 정확도: {toolMatch}/{total} ({toolMatch / total * 100:.0f}%)")
    print(f"  action 정확도: {actionMatch}/{total} ({actionMatch / total * 100:.0f}%)")
    print(f"  param 정확도: {paramMatch}/{total} ({paramMatch / total * 100:.0f}%)")
    print(f"  에러: {errCount}/{total}")

    # 카테고리별 분석
    categories = {
        "재무": [r for r in results if r["label"] in ("재무제표", "배당", "ROE", "성장률", "재무건전성")],
        "공시": [r for r in results if r["label"] in ("사업개요", "리스크", "공시검색")],
        "분석": [r for r in results if r["label"] in ("인사이트", "밸류에이션", "섹터")],
        "시장": [r for r in results if r["label"] == "주가"],
        "메타": [r for r in results if r["label"] in ("기능문의", "데이터상태")],
        "대화": [r for r in results if r["label"] == "대화"],
    }
    print("\n  카테고리별:")
    for cat, catResults in categories.items():
        correct = sum(1 for r in catResults if r.get("allMatch"))
        print(f"    {cat}: {correct}/{len(catResults)}")

    # 013/014 대비
    print(f"\n  [013 대비] 60% → {allMatch / total * 100:.0f}%")
    print(f"  [014 대비] 80% → {allMatch / total * 100:.0f}%")


if __name__ == "__main__":
    main()
