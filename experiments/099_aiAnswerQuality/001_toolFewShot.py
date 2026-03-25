"""실험 ID: 099-001
실험명: Tool-Use Few-Shot Grounding — tool 호출 정확도 향상

목적:
- LLM이 tool을 호출할 때 올바른 파라미터(topic, apiType, module)를 선택하도록
  시스템 프롬프트에 정확한 few-shot 예시를 추가한다
- Gorilla (UC Berkeley), ToolBench (Tsinghua) 기법 적용

가설:
1. get_data/get_report_data의 정확한 호출 예시 10개를 추가하면 tool parameter 정확도 50% → 80%+
2. 프롬프트 토큰 증가(~400토큰)는 답변 품질을 저하시키지 않는다

방법:
1. 097 실험의 15건 질문을 baseline으로 사용
2. system_base.py의 도구 예시 섹션에 few-shot 블록을 monkey-patch로 삽입
3. 동일 15건 질문 replay → tool call name/args 정확도 비교
4. A: baseline (현재 프롬프트) vs B: few-shot 추가

결과:
3건 핵심 질문(fsSummary, executivePay, mdnaOverview)으로 Baseline vs Few-Shot V1 vs V2 비교:

| topic | Baseline tools | Few-Shot V2 tools | 정확? |
|-------|---------------|-------------------|------|
| fsSummary | get_data("fsSummary") + show_topic("fsSummary","3") | get_data("fsSummary") | 부분 (IS/BS 미호출) |
| executivePay | get_report_data("executive") ✅ | get_report_data("executive") ✅ | 정확 (이미 정확) |
| mdnaOverview | show_topic("executive") ❌ 18자 | show_topic("executive") ❌ 758자 | 실패 (few-shot으로 극복 불가) |

- Few-Shot V1 (단순 예시 나열): mdnaOverview에서 executive → businessOverview로 drift. 개선 미미.
- Few-Shot V2 (질문→도구 매핑 테이블 + 경고): mdnaOverview 여전히 show_topic("executive") 호출.
- executivePay는 baseline부터 이미 정확 → few-shot 불필요.
- fsSummary는 fsSummary 모듈을 호출하지만 IS/BS를 직접 호출하지 않음.

결론:
1. 가설1 기각 — few-shot 예시만으로 tool parameter 정확도를 80%까지 올리기 어려움
2. 가설2 채택 — 프롬프트 증가(~500토큰)로 답변 품질 저하 없음
3. **핵심 발견**: 문제는 프롬프트가 아니라 LLM이 "경영진 분석"→"executive"로 번역하는 강한 편향.
   "mdnaOverview"라는 topic명이 비직관적이고, LLM이 한국어 질문에서 정확한 영문 topic명을 추론하지 못함.
4. **개선 방향**: few-shot 대신 **시스템 측 결정론적 매핑**(질문 키워드 → 추천 tool+args)을
   context에 사전 주입하는 방식이 필요. 이건 003_adaptiveContextTier에서 다룸.

실험일: 2026-03-25
"""

from __future__ import annotations

import gc
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

# 097과 동일한 15건 질문
QUESTIONS = [
    {"topic": "companyOverview", "question": "삼성전자 회사 개요에서 최근 변동 사항이 있나"},
    {"topic": "dividend", "question": "삼성전자 배당 현황과 최근 3년 변화 알려줘"},
    {"topic": "businessOverview", "question": "삼성전자 사업보고서 기준 사업 구조와 매출 구성 설명해줘"},
    {"topic": "productService", "question": "삼성전자 주요 제품별 매출 추이와 시장 점유율 알려줘"},
    {"topic": "riskDerivative", "question": "삼성전자 파생상품 및 리스크 관리 현황 분석해줘"},
    {"topic": "rawMaterial", "question": "삼성전자 원재료 조달 구조와 가격 변동 영향 분석해줘"},
    {"topic": "fsSummary", "question": "삼성전자 재무제표 요약 기준 최근 3년 주요 지표 변화 알려줘"},
    {"topic": "consolidatedNotes", "question": "삼성전자 연결재무제표 주석에서 중요 회계 정책 변경 사항 있나"},
    {"topic": "mdnaOverview", "question": "삼성전자 경영진 분석 의견에서 올해 핵심 이슈가 뭔지 정리해줘"},
    {"topic": "liquidityAndCapitalResources", "question": "삼성전자 유동성과 자본 조달 상황 분석해줘"},
    {"topic": "internalControl", "question": "삼성전자 내부통제 시스템 현황과 감사 의견 알려줘"},
    {"topic": "majorHolder", "question": "삼성전자 최대주주 및 특수관계인 지분 변동 현황 알려줘"},
    {"topic": "employee", "question": "삼성전자 직원 수 변화와 평균 근속연수 추이 알려줘"},
    {"topic": "executivePay", "question": "삼성전자 등기임원 보수 총액과 개인별 보수 현황 알려줘"},
    {"topic": "contingentLiability", "question": "삼성전자 우발채무 및 약정사항 현황 분석해줘"},
]

# 기대하는 도구 호출 (topic → 올바른 도구+파라미터)
EXPECTED_TOOLS = {
    "companyOverview": [("show_topic", {"topic": "companyOverview"})],
    "dividend": [("get_report_data", {"api_type": "dividend"})],
    "businessOverview": [("show_topic", {"topic": "businessOverview"})],
    "productService": [("show_topic", {"topic": "productService"})],
    "riskDerivative": [("show_topic", {"topic": "riskDerivative"})],
    "rawMaterial": [("show_topic", {"topic": "rawMaterial"})],
    "fsSummary": [("get_data", {"module_name": "IS"}), ("get_data", {"module_name": "BS"})],
    "consolidatedNotes": [("show_topic", {"topic": "consolidatedNotes"})],
    "mdnaOverview": [("show_topic", {"topic": "mdnaOverview"})],
    "liquidityAndCapitalResources": [("show_topic", {"topic": "liquidityAndCapitalResources"})],
    "internalControl": [("show_topic", {"topic": "internalControl"})],
    "majorHolder": [("get_report_data", {"api_type": "majorHolder"})],
    "employee": [("get_report_data", {"api_type": "employee"})],
    "executivePay": [("get_report_data", {"api_type": "executive"})],
    "contingentLiability": [("show_topic", {"topic": "contingentLiability"})],
}

# few-shot 블록 (실험용 — 성공하면 system_base.py에 흡수)
FEW_SHOT_SUPPLEMENT = """

## 도구 호출 정확한 예시 (반드시 이 형식을 따르세요)

**재무제표 데이터 조회** — `get_data(module_name)`:
- 손익계산서: `get_data(module_name="IS")` → 매출/영업이익/순이익 시계열
- 재무상태표: `get_data(module_name="BS")` → 자산/부채/자본 시계열
- 현금흐름표: `get_data(module_name="CF")` → 영업/투자/재무 현금흐름
- 재무비율: `get_data(module_name="ratios")` → ROE/부채비율/영업이익률 등
- 재무요약: `get_data(module_name="fsSummary")` → 최근 5년 요약

**정기보고서 정형 데이터** — `get_report_data(api_type)`:
- 배당: `get_report_data(api_type="dividend")` → DPS/배당수익률/배당성향
- 직원: `get_report_data(api_type="employee")` → 직원수/평균급여/근속연수
- 임원 보수: `get_report_data(api_type="executive")` → 임원별 보수/성과급
- 최대주주: `get_report_data(api_type="majorHolder")` → 지분율/변동
- 감사의견: `get_report_data(api_type="auditOpinion")` → 적정/한정/부적정

**공시 원문 접근** — `show_topic(topic)`:
- 사업 개요: `show_topic(topic="businessOverview")`
- 경영진 분석: `show_topic(topic="mdnaOverview")`
- 위험 요인: `show_topic(topic="riskFactor")`
- 파생상품: `show_topic(topic="riskDerivative")`
- 원재료: `show_topic(topic="rawMaterial")`
- 우발채무: `show_topic(topic="contingentLiability")`
- 내부통제: `show_topic(topic="internalControl")`

**원칙**: 재무 숫자 → `get_data`, 보고서 정형 → `get_report_data`, 공시 원문 → `show_topic`
"""


def runTest(questions: list[dict], useFewShot: bool, stockCode: str = "005930") -> list[dict]:
    """질문 실행 → tool 호출 로그 수집."""
    import dartlab
    from dartlab.engines.ai.runtime.core import analyze

    dartlab.llm.configure(provider="ollama", model="qwen3:latest")
    c = dartlab.Company(stockCode)

    if useFewShot:
        # monkey-patch: system_base에 few-shot 추가
        from dartlab.engines.ai.conversation.templates import system_base

        original = system_base.SYSTEM_PROMPT_KR
        system_base.SYSTEM_PROMPT_KR = original + FEW_SHOT_SUPPLEMENT

    results = []
    for i, q in enumerate(questions):
        print(f"  [{i + 1}/{len(questions)}] {q['topic']}")
        toolCalls = []
        chunks = []
        try:
            for ev in analyze(c, q["question"], use_tools=True):
                if ev.kind == "tool_call":
                    toolCalls.append(ev.data)
                elif ev.kind == "chunk":
                    chunks.append(ev.data.get("text", ""))
        except (RuntimeError, TypeError, ValueError, KeyError, OSError) as e:
            print(f"    [ERROR] {e}")
            results.append({"topic": q["topic"], "error": str(e), "toolCalls": [], "answerLen": 0})
            continue

        answer = "".join(chunks)
        results.append({
            "topic": q["topic"],
            "toolCalls": toolCalls,
            "answerLen": len(answer),
            "answerPreview": answer[:200],
        })
        toolNames = [tc.get("name", "") for tc in toolCalls]
        print(f"    tools: {toolNames}, answer: {len(answer)}자")
        gc.collect()

    if useFewShot:
        # restore
        from dartlab.engines.ai.conversation.templates import system_base

        system_base.SYSTEM_PROMPT_KR = original  # noqa: F821

    return results


def scoreToolAccuracy(results: list[dict]) -> dict:
    """tool 호출 정확도 평가."""
    total = 0
    nameCorrect = 0
    paramCorrect = 0

    for r in results:
        topic = r["topic"]
        if topic not in EXPECTED_TOOLS or "error" in r:
            continue

        expected = EXPECTED_TOOLS[topic]
        actual = r.get("toolCalls", [])

        for expName, expArgs in expected:
            total += 1
            # name 매칭: actual 중 하나라도 일치하면 OK
            matchedName = any(tc.get("name") == expName for tc in actual)
            if matchedName:
                nameCorrect += 1
                # param 매칭: 같은 name의 tool에서 args가 일치하면 OK
                for tc in actual:
                    if tc.get("name") == expName:
                        args = tc.get("arguments", {})
                        if all(args.get(k) == v for k, v in expArgs.items()):
                            paramCorrect += 1
                            break

    return {
        "total": total,
        "nameAccuracy": nameCorrect / total if total else 0,
        "paramAccuracy": paramCorrect / total if total else 0,
        "nameCorrect": nameCorrect,
        "paramCorrect": paramCorrect,
    }


def main():
    print("=" * 60)
    print("Phase A: Baseline (현재 프롬프트)")
    print("=" * 60)
    baselineResults = runTest(QUESTIONS, useFewShot=False)

    gc.collect()

    print(f"\n{'=' * 60}")
    print("Phase B: Few-Shot 추가")
    print(f"{'=' * 60}")
    fewShotResults = runTest(QUESTIONS, useFewShot=True)

    # 스코어링
    baselineScore = scoreToolAccuracy(baselineResults)
    fewShotScore = scoreToolAccuracy(fewShotResults)

    print(f"\n{'=' * 60}")
    print("결과 비교")
    print(f"{'=' * 60}")
    print(f"\n| 지표 | Baseline | Few-Shot | 변화 |")
    print(f"|------|---------|---------|------|")
    for key in ["nameAccuracy", "paramAccuracy"]:
        b = baselineScore[key]
        f = fewShotScore[key]
        delta = f - b
        print(f"| {key} | {b:.1%} | {f:.1%} | {delta:+.1%} |")

    # 상세 비교
    print(f"\n### 상세 tool 호출 비교")
    print(f"| topic | baseline tools | fewShot tools | baseline답변 | fewShot답변 |")
    print(f"|-------|---------------|---------------|------------|-----------|")
    for br, fr in zip(baselineResults, fewShotResults):
        bTools = [tc.get("name", "?") for tc in br.get("toolCalls", [])]
        fTools = [tc.get("name", "?") for tc in fr.get("toolCalls", [])]
        print(f"| {br['topic']} | {bTools} | {fTools} | {br.get('answerLen', 0)}자 | {fr.get('answerLen', 0)}자 |")

    # 저장
    outDir = Path(__file__).parent
    outPath = outDir / "001_results.json"
    with open(outPath, "w", encoding="utf-8") as fp:
        json.dump({"baseline": baselineResults, "fewShot": fewShotResults,
                    "baselineScore": baselineScore, "fewShotScore": fewShotScore},
                   fp, ensure_ascii=False, indent=2)
    print(f"\n저장: {outPath}")


if __name__ == "__main__":
    main()
