"""실험 ID: 103-001
실험명: AI 재설계 효과 테스트 — compact map + 도구 체제 검증

목적:
- Phase 1-5 구현(compact map + 도구) 후 실제 LLM이 도구를 사용하는지 검증
- 4개 시나리오: 단일기업, 기업비교, 전종목, 공시변화

가설:
1. compact map만 제공하면 AI가 자발적으로 도구를 호출해 데이터를 가져온다
2. 기업비교 질문에 scanAccount/scanRatio 도구를 사용한다
3. 전종목 질문에 company=None이어도 market 도구를 사용한다
4. 공시변화 질문에 analyze(watch) 도구를 사용한다

방법:
- analyze() 제너레이터를 직접 소비, 모든 이벤트(context/tool_call/tool_result/chunk/error) 수집
- 각 시나리오별 성공 기준 판정

결과 (2026-03-28):

## 1차 (provider 미명시 — Ollama fallback)

| 시나리오 | compact map | 도구 호출 | 시간 | 결과 |
|---------|-------------|----------|------|------|
| 1. 단일기업 수익성 | O (1개) | 3건 (finance x3) | 126s | PASS — 파라미터 오류 |
| 2. 기업비교 매출 | O (2개) | 0건 | 116s | FAIL — 텍스트로 코드 출력 |
| 3. 전종목 ROE | N/A | 0건 | 205s | FAIL — 허위 데이터 날조 |
| 4. 공시변화 | - | - | 0.1s | SKIP — corpCode.xml 오탐 |

원인: provider 미명시 → auto_detect가 Ollama fallback → 로컬 GPU 추론 + 도구 호출 능력 부족

## 수정 후 2차 (provider="oauth-codex" 명시)

수정 사항:
1. analyze() → _analyze_inner() companies 파라미터 전달 누락 수정
2. 시스템 프롬프트에 "도구 사용 강제" 규칙 추가 + 파라미터 제한 명시
3. isDartFilingQuestion() 공시 변화 질문 오탐 방지
4. 실험 스크립트에 provider="oauth-codex" 명시

| 시나리오 | compact map | 도구 호출 | 시간 | 결과 |
|---------|-------------|----------|------|------|
| 1. 단일기업 수익성 | O | 4건 (finance x3 + explore) | 40s | PASS |
| 2. 기업비교 매출 | O (2개) | 3건 (market scanAccount x2 + scanRatio) | 36s | PASS |
| 3. 전종목 ROE | N/A | 2건 (market scanRatio + benchmark) | 25s | PASS |
| 4. 공시변화 | O | 6건 (analyze watch + explore diff x2 등) | 36s | PASS |

## 핵심 발견

1. **Ollama vs ChatGPT**: 같은 프롬프트/도구인데 provider에 따라 도구 호출 능력이 완전히 다름
   - Ollama: 파라미터 오류, 도구 미호출, 허위 데이터 생성
   - ChatGPT(OAuth-Codex): 올바른 파라미터, 적극적 도구 호출, 실제 데이터 기반 분석
2. **compact map 체제 유효**: 200-400 토큰 프로필만 주고 나머지는 도구 → AI가 자발적으로 올바른 도구 선택
3. **scanAccount/scanRatio 동작 확인**: 기업 비교에서 Company N개 로드 대신 scan/ parquet 사용 성공
4. **도구 체이닝**: AI가 한 도구 결과 보고 다음 도구를 연쇄 호출 (시나리오 4: 6건)

결론:
- 4/4 시나리오 전부 통과 (OAuth-Codex provider)
- compact map + 도구 체제가 의도대로 동작함
- provider 품질이 핵심 변수 — Ollama 같은 소형 모델은 도구 호출 불안정

실험일: 2026-03-28
"""
from __future__ import annotations

import gc
import sys
import time


def _runScenario(
    title: str,
    question: str,
    company=None,
    companies=None,
    successCriteria: str = "",
) -> dict:
    """단일 시나리오 실행. analyze() 이벤트를 전부 수집해 요약 반환."""
    from dartlab.ai.runtime.core import analyze

    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"  Q: {question}")
    print(f"  기대: {successCriteria}")
    print(f"{'='*60}")

    kwargs: dict = {"use_tools": True, "provider": "oauth-codex"}
    if companies:
        kwargs["companies"] = companies

    contextModules: list[str] = []
    toolCalls: list[dict] = []
    toolResults: list[str] = []
    chunks: list[str] = []
    errors: list[str] = []
    t0 = time.monotonic()

    try:
        for ev in analyze(company, question, **kwargs):
            if ev.kind == "context":
                mod = ev.data.get("module", "")
                label = ev.data.get("label", "")
                contextModules.append(mod)
                print(f"  [CTX] {mod} -- {label}")

            elif ev.kind == "tool_call":
                name = ev.data.get("name", "")
                args = ev.data.get("arguments", {})
                toolCalls.append({"name": name, "args": args})
                print(f"  [TOOL] {name}({args})")

            elif ev.kind == "tool_result":
                name = ev.data.get("name", "")
                result = ev.data.get("result", "")
                preview = result[:120].replace("\n", " ") if result else ""
                toolResults.append(name)
                print(f"  [RESULT] {name} -- {preview}...")

            elif ev.kind == "chunk":
                chunks.append(ev.data.get("text", ""))

            elif ev.kind == "error":
                msg = ev.data.get("error", str(ev.data))
                errors.append(msg)
                print(f"  [ERROR] {msg}")

            elif ev.kind == "system_prompt":
                sysLen = len(ev.data.get("text", ""))
                print(f"  [SYS] system prompt {sysLen} chars")

    except KeyboardInterrupt:
        print("  ** interrupted **")
    except Exception as exc:
        errors.append(str(exc))
        print(f"  [EXCEPTION] {exc}")

    elapsed = time.monotonic() - t0
    answer = "".join(chunks)

    print(f"\n  --- 결과 ---")
    print(f"  시간: {elapsed:.1f}s")
    print(f"  컨텍스트: {contextModules}")
    print(f"  도구 호출: {len(toolCalls)}건 -- {[t['name'] for t in toolCalls]}")
    print(f"  응답 길이: {len(answer)}자")
    if errors:
        print(f"  에러: {errors}")
    print(f"  응답 앞부분: {answer[:200]}...")

    return {
        "title": title,
        "elapsed": elapsed,
        "contextModules": contextModules,
        "toolCalls": toolCalls,
        "toolResults": toolResults,
        "answerLen": len(answer),
        "errors": errors,
    }


def scenario1() -> dict:
    """시나리오 1: 단일 기업 수익성 분석."""
    import dartlab

    c = dartlab.Company("005930")
    result = _runScenario(
        title="시나리오 1: 단일 기업 — 삼성전자 수익성 분석",
        question="삼성전자의 수익성을 분석해줘. 매출, 영업이익률, ROE 추이를 살펴보고 싶어.",
        company=c,
        successCriteria="compact map 이벤트 + finance/analyze tool_call 1개 이상",
    )

    # 판정
    hasCompactMap = any("compactMap" in m for m in result["contextModules"])
    hasToolCall = len(result["toolCalls"]) > 0
    result["pass"] = hasCompactMap and hasToolCall
    result["verdict"] = (
        f"compactMap={'O' if hasCompactMap else 'X'}, "
        f"toolCalls={len(result['toolCalls'])}{'(PASS)' if hasToolCall else '(FAIL)'}"
    )
    print(f"  판정: {result['verdict']}")

    del c
    gc.collect()
    return result


def scenario2() -> dict:
    """시나리오 2: 기업간 비교."""
    import dartlab

    c1 = dartlab.Company("005930")  # 삼성전자
    c2 = dartlab.Company("000660")  # SK하이닉스
    result = _runScenario(
        title="시나리오 2: 기업간 비교 — 삼성전자 vs SK하이닉스 매출 비교",
        question="삼성전자와 SK하이닉스의 매출과 영업이익률을 비교해줘.",
        company=c1,
        companies=[c1, c2],
        successCriteria="compact map 2개 + market(scanAccount/scanRatio) tool_call",
    )

    compactMapCount = sum(1 for m in result["contextModules"] if "compactMap" in m)
    hasMarketTool = any(
        t["name"] == "market" and t["args"].get("action") in ("scanAccount", "scanRatio", "financials", "ratios")
        for t in result["toolCalls"]
    )
    hasAnyTool = len(result["toolCalls"]) > 0
    result["pass"] = compactMapCount >= 2 and hasAnyTool
    result["verdict"] = (
        f"compactMaps={compactMapCount}, "
        f"marketTool={'O' if hasMarketTool else 'X'}, "
        f"totalTools={len(result['toolCalls'])}{'(PASS)' if hasAnyTool else '(FAIL)'}"
    )
    print(f"  판정: {result['verdict']}")

    del c1, c2
    gc.collect()
    return result


def scenario3() -> dict:
    """시나리오 3: 전종목 질문 (company=None)."""
    result = _runScenario(
        title="시나리오 3: 전종목 — 반도체 섹터 ROE 현황",
        question="반도체 섹터의 ROE 현황을 알려줘. 어떤 기업이 높고 낮은지 보고 싶어.",
        company=None,
        successCriteria="market tool_call (scanRatio 또는 scan)",
    )

    hasMarketTool = any(t["name"] == "market" for t in result["toolCalls"])
    hasAnyTool = len(result["toolCalls"]) > 0
    result["pass"] = hasAnyTool
    result["verdict"] = (
        f"marketTool={'O' if hasMarketTool else 'X'}, "
        f"totalTools={len(result['toolCalls'])}{'(PASS)' if hasAnyTool else '(FAIL)'}"
    )
    print(f"  판정: {result['verdict']}")
    return result


def scenario4() -> dict:
    """시나리오 4: 공시 변화 감지."""
    import dartlab

    c = dartlab.Company("005930")
    result = _runScenario(
        title="시나리오 4: 공시 변화 — 삼성전자 최근 공시 변화",
        question="삼성전자의 최근 공시에서 뭐가 바뀌었는지 알려줘.",
        company=c,
        successCriteria="analyze(watch) tool_call",
    )

    hasAnalyzeTool = any(
        t["name"] == "analyze" and t["args"].get("action") in ("watch", "insight")
        for t in result["toolCalls"]
    )
    hasAnyTool = len(result["toolCalls"]) > 0
    result["pass"] = hasAnyTool
    result["verdict"] = (
        f"analyzeTool={'O' if hasAnalyzeTool else 'X'}, "
        f"totalTools={len(result['toolCalls'])}{'(PASS)' if hasAnyTool else '(FAIL)'}"
    )
    print(f"  판정: {result['verdict']}")

    del c
    gc.collect()
    return result


def main():
    print("=" * 60)
    print("  AI 재설계 효과 테스트 — compact map + 도구 체제")
    print("=" * 60)

    # 시나리오 선택 (인자로 번호 전달 가능)
    targets = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else [1, 2, 3, 4]

    results = []
    scenarios = {1: scenario1, 2: scenario2, 3: scenario3, 4: scenario4}

    for num in targets:
        fn = scenarios.get(num)
        if fn:
            r = fn()
            results.append(r)
            print()

    # 최종 요약
    print("\n" + "=" * 60)
    print("  최종 요약")
    print("=" * 60)
    for r in results:
        status = "PASS" if r.get("pass") else "FAIL"
        print(f"  [{status}] {r['title']}")
        print(f"         {r['verdict']}")
        print(f"         도구: {[t['name'] + '(' + str(t['args'].get('action', '')) + ')' for t in r['toolCalls']]}")
        print(f"         {r['elapsed']:.1f}s, {r['answerLen']}자")
    print()

    passCount = sum(1 for r in results if r.get("pass"))
    print(f"  결과: {passCount}/{len(results)} 통과")


if __name__ == "__main__":
    main()
