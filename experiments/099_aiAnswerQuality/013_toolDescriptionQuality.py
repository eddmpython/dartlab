"""실험 013: Tool Description 품질 강화 검증 (ACI 원칙)

목적:
- Anthropic ACI 원칙 적용: "✓ 언제 쓰는가 / ✗ 쓰지 않을 때 / 호출 예시"를
  Super Tool description에 추가한 후 도구 선택 정확도 변화 측정

가설:
1. description에 경계(✓/✗)와 예시를 추가하면 도구 선택 정확도가 향상된다
2. 특히 explore vs finance 경계가 명확해져 혼동이 줄어든다

방법:
1. 10개 표준 질문 세트를 Gemini 2.5 Flash에게 던짐
2. 각 질문별 첫 tool_call의 도구명, action, 파라미터 정확도 측정
3. 기대값과 비교하여 정확도 산출

결과:
- 전체 정확도: 6/10 (60%)
- 도구명 정확도: 7/10 (70%)
- action 정확도: 7/10 (70%)
- 파라미터 정확도: 8/10 (80%)
- 에러: 0/10

| 질문 | 기대 | 실제 | 판정 |
|------|------|------|------|
| 사업개요 | explore(show, businessOverview) | 도구 미호출 | ❌ context에 이미 답 존재 |
| 재무제표 | finance(data, IS) | finance(data, IS) | ✅ |
| 배당 | finance(report, dividend) | finance(report, dividend) | ✅ |
| 리스크 | explore(show, riskFactor) | explore(show, riskDerivative) | ❌ topic 혼동 |
| ROE | finance(ratios) | finance(ratios) | ✅ |
| 인사이트 | analyze(insight) | 도구 미호출 | ❌ context에 이미 답 존재 |
| 밸류에이션 | analyze(valuation) | analyze(valuation) | ✅ |
| 주가 | market(price) | 도구 미호출 | ❌ context에 이미 답 존재 |
| 대화 | 없음 | 없음 | ✅ |
| 기능문의 | system(features) | system(features) | ✅ |

결론:
- 가설 1 부분 채택: description 강화로 도구를 호출할 때의 정확도는 높음 (호출된 7건 중 6건 정확)
- 가설 2 부분 채택: explore vs finance 경계 명확 (혼동 0건)
- 핵심 발견: 3건의 실패는 description 문제가 아니라 **context에 이미 답이 있어서 도구를 안 쓰는 문제**
  - skeleton context에 사업개요 요약, 인사이트 등급, 현재가가 이미 포함되어 있으면 LLM이 도구 호출 불필요 판단
  - 이는 Phase 2의 Response Contract + tool_choice 강제로 해결해야 함
- riskFactor vs riskDerivative 혼동은 topic description 보강으로 해결 가능

실험일: 2026-03-26
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# 10개 표준 질문 + 기대 도구 호출
QUESTIONS = [
    # (label, question, expectedTool, expectedAction, expectedParam)
    ("사업개요", "이 회사는 뭘 하는 회사야?", "explore", "show", "businessOverview"),
    ("재무제표", "재무제표를 요약해줘", "finance", "data", "IS"),
    ("배당", "배당 현황을 알려줘", "finance", "report", "dividend"),
    ("리스크", "리스크 요인을 분석해줘", "explore", "show", "riskFactor"),
    ("ROE분석", "ROE가 어떻게 되나요?", "finance", "ratios", ""),
    ("인사이트", "투자등급이 어떻게 돼?", "analyze", "insight", ""),
    ("밸류에이션", "적정주가를 알려줘", "analyze", "valuation", ""),
    ("주가", "현재 주가가 얼마야?", "market", "price", ""),
    ("대화", "안녕하세요", None, None, None),  # 도구 호출 없어야 함
    ("기능문의", "뭘 물어볼 수 있어?", "system", "features", ""),
]


def runSingleQuestion(company, question: str, label: str) -> dict:
    """단일 질문 실행 — 첫 tool_call만 수집."""
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

    answer = "".join(chunks)
    firstCall = toolCalls[0] if toolCalls else None

    return {
        "label": label,
        "question": question,
        "firstToolName": firstCall.get("name", "") if firstCall else None,
        "firstToolArgs": firstCall.get("arguments", {}) if firstCall else None,
        "totalToolCalls": len(toolCalls),
        "answerLen": len(answer),
        "elapsed": round(elapsed, 1),
    }


def evaluateResult(result: dict, expected: tuple) -> dict:
    """기대값과 비교하여 정확도 판정."""
    _, _, expTool, expAction, expParam = expected

    actual = result
    toolName = actual["firstToolName"]
    toolArgs = actual["firstToolArgs"] or {}

    # 도구 호출 안 해야 하는 경우
    if expTool is None:
        toolCorrect = toolName is None
        actionCorrect = True
        paramCorrect = True
    else:
        toolCorrect = toolName == expTool
        actualAction = toolArgs.get("action", "")
        actionCorrect = actualAction == expAction if expAction else True
        # 파라미터 정확도: 핵심 파라미터가 포함되어 있는지
        if expParam:
            allArgs = str(toolArgs)
            paramCorrect = expParam in allArgs
        else:
            paramCorrect = True

    return {
        **actual,
        "toolCorrect": toolCorrect,
        "actionCorrect": actionCorrect,
        "paramCorrect": paramCorrect,
        "allCorrect": toolCorrect and actionCorrect and paramCorrect,
    }


def main():
    import dartlab

    print("=" * 60)
    print("013: Tool Description 품질 강화 검증 (ACI 원칙)")
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

    print("\n[1] Company 생성: 삼성전자 (005930)")
    c = dartlab.Company("005930")
    print(f"  corpName: {c.corpName}")

    print(f"\n[2] {len(QUESTIONS)}개 질문 도구 선택 정확도 테스트\n")

    results = []
    for expected in QUESTIONS:
        label, question, expTool, expAction, expParam = expected
        print(f"  [{label}] {question}")
        print(f"    기대: {expTool}({expAction}, {expParam})" if expTool else "    기대: 도구 호출 없음")
        try:
            result = runSingleQuestion(c, question, label)
            evaluated = evaluateResult(result, expected)
            results.append(evaluated)

            status = "✅" if evaluated["allCorrect"] else "❌"
            print(f"    실제: {result['firstToolName']}({result['firstToolArgs']}) | {result['elapsed']}s")
            print(f"    판정: {status} (도구:{evaluated['toolCorrect']}, action:{evaluated['actionCorrect']}, param:{evaluated['paramCorrect']})")
        except Exception as e:
            print(f"    [EXCEPTION] {type(e).__name__}: {e}")
            results.append({"label": label, "allCorrect": False, "error": str(e)})
        print()

    # 요약
    print("=" * 60)
    print("요약")
    print("=" * 60)
    total = len(results)
    allCorrect = sum(1 for r in results if r.get("allCorrect"))
    toolCorrect = sum(1 for r in results if r.get("toolCorrect", False))
    actionCorrect = sum(1 for r in results if r.get("actionCorrect", False))
    paramCorrect = sum(1 for r in results if r.get("paramCorrect", False))
    errCount = sum(1 for r in results if r.get("error"))

    print(f"  전체 정확도: {allCorrect}/{total} ({allCorrect / total * 100:.0f}%)")
    print(f"  도구명 정확도: {toolCorrect}/{total} ({toolCorrect / total * 100:.0f}%)")
    print(f"  action 정확도: {actionCorrect}/{total} ({actionCorrect / total * 100:.0f}%)")
    print(f"  파라미터 정확도: {paramCorrect}/{total} ({paramCorrect / total * 100:.0f}%)")
    print(f"  에러: {errCount}/{total}")


if __name__ == "__main__":
    main()
