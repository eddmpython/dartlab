"""실험 ID: 099-003
실험명: 질문 복잡도 기반 Adaptive Context Tier

목적:
- 현재 _resolve_context_tier()는 provider 기반 → ollama는 무조건 skeleton.
- "ROE는?" 같은 단순 질문과 "종합 분석해줘" 같은 복합 질문이 같은 context를 받는 문제.
- 질문 복잡도 점수를 기반으로 tier를 동적 결정하여 context 과부족을 해소한다.
- Adaptive RAG (Jeong 2024) 기법 적용.

가설:
1. 복잡도 점수([유형수] + [모듈 키워드수])로 tier를 결정하면
   단순 질문은 skeleton(빠름), 복합 질문은 focused(풍부)로 적절 분배.
2. 복합 질문에서 focused tier가 더 나은 답변을 생성한다.

방법:
1. _classify_question_multi()로 유형 수 산출
2. 질문 내 모듈 키워드(재무, 배당, 임원 등) 카운트
3. complexity = len(q_types) + len(module_keywords_matched)
4. [1-2]=skeleton, [3-4]=focused, [5+]=full
5. 15건 질문에 대해 현재(always skeleton) vs adaptive tier 비교

결과:

### Phase 0: 복잡도 스코어링 (10건)

| topic | complexity | tier | qTypes | moduleMatches |
|-------|-----------|------|--------|---------------|
| simple_ratio | 1 | skeleton | ['수익성'] | [] |
| simple_dividend | 2 | skeleton | ['배당'] | ['배당'] |
| simple_employee | 2 | skeleton | ['인력'] | ['직원'] |
| medium_fs | 1 | skeleton | [] | ['재무제표'] |
| medium_executive | 3 | focused | ['지배구조'] | ['임원', '보수'] |
| medium_mdna | 1 | skeleton | [] | ['경영진 분석'] |
| medium_risk | 5 | focused | ['리스크', '기타'] | ['파생상품', '리스크', '분석해줘'] |
| complex_compare | 12 | focused | ['지배구조', '기타', '배당'] | ['재무제표', '배당', '임원', '보수', '종합', '분석해줘', '비교'] |
| complex_full | 12 | focused | ['기타', '건전성', '성장성'] | ['재무제표', '사업 구조', '매출 구성', '유동성', '전체', '분석해줘'] |
| complex_risk_all | 11 | focused | ['리스크', '기타', '건전성'] | ['감사', '파생상품', '리스크', '우발채무', '내부통제', '종합', '분석해줘'] |

→ 복잡도 분류가 의도대로 동작: simple(1-2)=skeleton, medium-complex(3+)=focused.

### Run 1: full tier 포함 (OOM 발견)

| topic | B-tier | A-tier | B-tools | A-tools | B답변 | A답변 |
|-------|--------|--------|---------|---------|------|------|
| simple_ratio | skeleton | skeleton | compute_ratios | search_company | 80자 | 285자 |
| medium_fs | skeleton | skeleton | get_data | get_data, show_topic | 1313자 | 2913자 |
| complex_full | skeleton | full* | - | OOM | 893자 | OOM |

*full tier에서 삼성전자(대기업) sections 전체 로드 시 MemoryError 발생.

### Run 2: focused 상한 (성공)

| topic | B-tier(skeleton) | A-tier(adaptive) | B-tools | A-tools | B답변 | A답변 |
|-------|---------|---------|---------|---------|------|------|
| simple_ratio | skeleton | skeleton | compute_ratios | compute_ratios | 128자 | 111자 |
| medium_fs | skeleton | skeleton | search_company | get_data | 495자 | 263자 |
| complex_compare | skeleton | focused | show_topic×3, get_report_data×2 | (없음) | 5439자 | 1436자 |

**역설적 발견**: complex_compare에서 focused tier(풍부한 context)가 오히려 답변 품질 저하.
- skeleton: context 부족 → tool 5개 적극 호출 → 5439자 풍부한 답변
- focused: context에 데이터 포함 → tool 미호출 → 1436자 빈약한 답변
- **tool calling이 사전 context 주입보다 효과적**이라는 결론.

결론:
1. 가설1 부분 채택 — 복잡도 스코어링은 정상 동작 (simple=skeleton, complex=focused 분배 합리적).
2. 가설2 기각 — **focused tier가 오히려 답변 악화**. skeleton + tool calling이 focused without tools보다 우수.
   focused tier에서는 context가 풍부하여 LLM이 tool을 호출하지 않지만, 정작 context 품질이 tool 결과보다 낮음.
3. **full tier는 대기업에서 OOM** — focused가 실질적 상한이지만, focused도 이점이 미미.
4. **핵심 발견**: tool-capable provider에서는 skeleton + 적극적 tool calling이 최적 전략.
   context tier를 높이는 것보다 002의 Tool Route Hint로 올바른 tool을 호출하게 하는 것이 압도적으로 효과적.
5. **흡수 방향**: context tier 동적 변경은 ROI 낮음.
   대신 skeleton tier를 유지하면서 002의 Tool Route Hint를 기본 적용하는 것이 최적.

실험일: 2026-03-25
"""

from __future__ import annotations

import gc
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))


# 모듈 키워드 → 매칭 가중치
MODULE_KEYWORDS = {
    "재무제표": 1, "손익": 1, "재무상태": 1, "현금흐름": 1,
    "배당": 1, "직원": 1, "임원": 1, "보수": 1,
    "최대주주": 1, "지분": 1, "감사": 1,
    "경영진 분석": 1, "사업 구조": 1, "매출 구성": 1,
    "파생상품": 1, "리스크": 1, "원재료": 1,
    "우발채무": 1, "내부통제": 1, "유동성": 1,
    "주석": 1, "회사 개요": 1, "제품": 1,
    "종합": 2, "전체": 2, "분석해줘": 1, "비교": 2,
}


def scoreComplexity(question: str) -> dict:
    """질문 복잡도 점수를 산출한다."""
    from dartlab.engines.ai.conversation.prompts import _classify_question_multi

    qTypes = _classify_question_multi(question)
    moduleMatches = [kw for kw in MODULE_KEYWORDS if kw in question]
    moduleScore = sum(MODULE_KEYWORDS[kw] for kw in moduleMatches)
    complexity = len(qTypes) + moduleScore

    if complexity <= 2:
        tier = "skeleton"
    else:
        # full tier는 삼성전자 등 대기업에서 OOM 리스크 → focused가 실질적 상한
        tier = "focused"

    return {
        "qTypes": qTypes,
        "moduleMatches": moduleMatches,
        "complexity": complexity,
        "tier": tier,
    }


QUESTIONS = [
    {"topic": "simple_ratio", "question": "삼성전자 ROE 알려줘"},
    {"topic": "simple_dividend", "question": "삼성전자 배당 현황 알려줘"},
    {"topic": "simple_employee", "question": "삼성전자 직원 수 알려줘"},
    {"topic": "medium_fs", "question": "삼성전자 재무제표 요약 기준 최근 3년 주요 지표 변화 알려줘"},
    {"topic": "medium_executive", "question": "삼성전자 등기임원 보수 총액과 개인별 보수 현황 알려줘"},
    {"topic": "medium_mdna", "question": "삼성전자 경영진 분석 의견에서 올해 핵심 이슈가 뭔지 정리해줘"},
    {"topic": "medium_risk", "question": "삼성전자 파생상품 및 리스크 관리 현황 분석해줘"},
    {"topic": "complex_compare", "question": "삼성전자 재무제표와 배당, 임원 보수를 종합 비교 분석해줘"},
    {"topic": "complex_full", "question": "삼성전자 사업 구조, 매출 구성, 재무제표, 유동성 전체를 종합 분석해줘"},
    {"topic": "complex_risk_all", "question": "삼성전자 우발채무, 파생상품, 내부통제, 감사 의견을 리스크 관점에서 종합 분석해줘"},
]


def runAdaptiveTest(questions: list[dict], useTierOverride: str | None, stockCode: str = "005930") -> list[dict]:
    """질문 실행 → tool 호출 + 답변 길이 수집."""
    import dartlab
    from dartlab.engines.ai.runtime import core as coreModule
    from dartlab.engines.ai.runtime.core import analyze

    dartlab.llm.configure(provider="ollama", model="qwen3:latest")
    c = dartlab.Company(stockCode)

    # monkey-patch _resolve_context_tier
    originalResolve = coreModule._resolve_context_tier

    results = []
    for i, q in enumerate(questions):
        comp = scoreComplexity(q["question"])
        effectiveTier = useTierOverride or comp["tier"]
        print(f"  [{i + 1}/{len(questions)}] {q['topic']} | complexity={comp['complexity']} | tier={effectiveTier}")

        # tier를 강제 지정하는 monkey-patch
        coreModule._resolve_context_tier = lambda _p, _t, _tier=effectiveTier: _tier

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
            results.append({
                "topic": q["topic"], "error": str(e),
                "toolCalls": [], "answerLen": 0, "tier": effectiveTier,
                "complexity": comp,
            })
            continue
        finally:
            coreModule._resolve_context_tier = originalResolve

        answer = "".join(chunks)
        toolNames = [(tc.get("name", ""), tc.get("arguments", {})) for tc in toolCalls]
        print(f"    tools: {[t[0] for t in toolNames]}, answer: {len(answer)}자")

        results.append({
            "topic": q["topic"],
            "toolCalls": toolCalls,
            "answerLen": len(answer),
            "tier": effectiveTier,
            "complexity": comp,
        })
        gc.collect()

    return results


def main():
    # Phase 0: 복잡도 스코어링만 먼저 확인
    print("=" * 60)
    print("Phase 0: 질문 복잡도 스코어링")
    print("=" * 60)
    print(f"\n| topic | complexity | tier | qTypes | moduleMatches |")
    print(f"|-------|-----------|------|--------|---------------|")
    for q in QUESTIONS:
        comp = scoreComplexity(q["question"])
        print(f"| {q['topic']} | {comp['complexity']} | {comp['tier']} | {comp['qTypes']} | {comp['moduleMatches']} |")

    # Phase A: 항상 skeleton (현재 동작)
    print(f"\n{'=' * 60}")
    print("Phase A: Always Skeleton (Baseline)")
    print(f"{'=' * 60}")
    # 3건만 대표 테스트 (메모리 안전)
    testQuestions = [
        QUESTIONS[0],  # simple_ratio (skeleton 적합)
        QUESTIONS[3],  # medium_fs (skeleton 부적합?)
        QUESTIONS[7],  # complex_compare (skeleton 부적합)
    ]
    baselineResults = runAdaptiveTest(testQuestions, useTierOverride="skeleton")
    gc.collect()

    # Phase B: adaptive tier (skeleton or focused)
    print(f"\n{'=' * 60}")
    print("Phase B: Adaptive Tier (skeleton/focused)")
    print(f"{'=' * 60}")
    adaptiveResults = runAdaptiveTest(testQuestions, useTierOverride=None)

    # 비교
    print(f"\n{'=' * 60}")
    print("결과 비교")
    print(f"{'=' * 60}")
    print(f"\n| topic | B-tier | A-tier | B-tools | A-tools | B답변 | A답변 |")
    print(f"|-------|--------|--------|---------|---------|------|------|")
    for br, ar in zip(baselineResults, adaptiveResults):
        bTools = [tc.get("name", "?") for tc in br.get("toolCalls", [])]
        aTools = [tc.get("name", "?") for tc in ar.get("toolCalls", [])]
        print(f"| {br['topic']} | {br['tier']} | {ar['tier']} | {bTools} | {aTools} | {br.get('answerLen', 0)} | {ar.get('answerLen', 0)} |")


if __name__ == "__main__":
    main()
