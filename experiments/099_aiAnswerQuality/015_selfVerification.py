"""실험 015: Self-Verification (Reflexion 패턴) 검증

목적:
- Reflexion 패턴(Shinn 2023) 기반 자기 검증: LLM 답변의 재무 수치를
  finance 엔진 실제값과 대조하여 불일치 시 correction prompt로 수정.
- validation.py의 extract_numbers + validate_claims를 활용.

가설:
1. 재무 수치를 포함하는 질문에서 LLM이 부정확한 수치를 인용할 때,
   correction prompt 1회로 수정 성공률 80%+ 달성
2. correction 턴은 답변 품질을 높이되 응답 지연은 2초 이내 추가

방법:
1. 삼성전자(005930) 대상 재무 관련 5개 질문
2. 각 질문별 LLM 답변에서 수치 추출 → finance 실제값 대조
3. mismatch 감지 시 correction prompt → 재답변 → 재검증
4. 수정 전후 mismatch 건수 비교

결과:
- 총 질문: 5 (재무 수치 중심)
- correction 발동: 0/5 — mismatch 자체가 없음
- 수치 추출: 20건 (매출 3, 수익성 12, 건전성 4, 배당 1)
- 수치 정확도: 100% (20/20건 mismatch 없음)
- 평균 응답시간: 11.6s
- 에러: 0/5

| 질문 | 도구 | 수치 추출 | mismatch | correction |
|------|------|----------|----------|------------|
| 매출분석 | 1건 | 3건 | 0 | - |
| 수익성 | 1건 | 12건 | 0 | - |
| 재무건전성 | 1건 | 4건 | 0 | - |
| 현금흐름 | 1건 | 0건 | 0 | - |
| 배당 | 1건 | 1건 | 0 | - |

결론:
- 가설 1 검증 불가 (해당 없음): Phase 1-2(ACI + Response Contract + tool_choice=ANY)가
  이미 충분히 효과적이어서 mismatch 자체가 발생하지 않음
- 가설 2 해당 없음: correction 턴이 발동하지 않아 추가 지연 측정 불가
- Self-Verification은 safety net으로 정상 설치됨:
  - validation.py extract_numbers → 20건 수치 추출 성공
  - validate_claims → 0건 mismatch → correction 미발동
  - mismatch 발생 시 자동으로 correction prompt → LLM 재답변 경로 활성화
- Phase 1-2의 효과가 핵심: Response Contract가 "도구 결과 없이 수치 인용 금지"를
  강제하므로, LLM이 항상 도구를 호출하고 실제 데이터를 기반으로 답변
- 향후: hallucination이 높은 provider(Ollama 소형 모델 등)에서 Self-Verification의
  실질적 효과를 검증할 필요 있음

실험일: 2026-03-26
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# 재무 수치 검증이 의미있는 5개 질문
QUESTIONS = [
    ("매출분석", "삼성전자 최근 연간 매출액과 영업이익을 알려줘"),
    ("수익성", "ROE와 영업이익률은 어떻게 되나요?"),
    ("재무건전성", "부채비율과 유동비율을 분석해줘"),
    ("현금흐름", "영업활동현금흐름과 투자활동현금흐름을 비교해줘"),
    ("배당", "최근 배당금과 배당성향을 알려줘"),
]


def runQuestion(company, question: str, label: str) -> dict:
    """단일 질문 실행 — 수치 추출 + 검증."""
    from dartlab.engines.ai.runtime.core import analyze
    from dartlab.engines.ai.runtime.validation import extract_numbers, validate_claims

    chunks = []
    toolCalls = []
    hasCorrectionEvent = False

    t0 = time.time()
    for event in analyze(
        company,
        question,
        provider="gemini",
        use_tools=True,
        validate=True,
        emit_system_prompt=False,
    ):
        if event.kind == "chunk":
            chunks.append(event.data.get("text", ""))
        elif event.kind == "tool_call":
            toolCalls.append(event.data)
        elif event.kind == "correction":
            hasCorrectionEvent = True
    elapsed = time.time() - t0

    fullText = "".join(chunks)

    # 최종 답변에서 수치 추출 + 검증
    claims = extract_numbers(fullText)
    vresult = validate_claims(claims, company)

    return {
        "label": label,
        "question": question,
        "toolCount": len(toolCalls),
        "claimCount": len(claims),
        "mismatchCount": len(vresult.mismatches),
        "mismatches": [
            {
                "label": mm.label,
                "claimed": mm.claimed,
                "actual": mm.actual,
                "diffPct": round(mm.diff_pct, 1),
            }
            for mm in vresult.mismatches
        ],
        "hasCorrectionEvent": hasCorrectionEvent,
        "answerLen": len(fullText),
        "elapsed": round(elapsed, 1),
    }


def main():
    import dartlab

    print("=" * 60)
    print("015: Self-Verification (Reflexion 패턴) 검증")
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

    # baseline: finance 실제값 확인
    print("\n[2] Finance 실제값 baseline")
    try:
        from dartlab.engines.ai.context.company_adapter import get_headline_ratios

        ratios = get_headline_ratios(c)
        if ratios:
            for attr in ["roe", "operatingMargin", "debtRatio", "currentRatio"]:
                val = getattr(ratios, attr, None)
                if val is not None:
                    print(f"  {attr}: {val:.2f}%")
    except Exception as e:
        print(f"  [WARN] ratios 조회 실패: {e}")

    print(f"\n[3] {len(QUESTIONS)}개 재무 질문 Self-Verification 테스트\n")

    results = []
    for label, question in QUESTIONS:
        print(f"  [{label}] {question}")
        try:
            result = runQuestion(c, question, label)
            results.append(result)

            corrected = "✅ correction" if result["hasCorrectionEvent"] else "  (no correction)"
            print(
                f"    도구: {result['toolCount']}건 | 수치: {result['claimCount']}건 | mismatch: {result['mismatchCount']}건 | {result['elapsed']}s"
            )
            print(f"    {corrected}")
            if result["mismatches"]:
                for mm in result["mismatches"]:
                    print(
                        f"    ❌ {mm['label']}: 인용 {mm['claimed']:,.0f} vs 실제 {mm['actual']:,.0f} (차이 {mm['diffPct']:.0f}%)"
                    )
        except Exception as e:
            print(f"    [EXCEPTION] {type(e).__name__}: {e}")
            results.append({"label": label, "mismatchCount": -1, "error": str(e)})
        print()

    # 요약
    print("=" * 60)
    print("요약")
    print("=" * 60)
    total = len(results)
    correctionTriggered = sum(1 for r in results if r.get("hasCorrectionEvent"))
    totalMismatches = sum(r.get("mismatchCount", 0) for r in results if r.get("mismatchCount", 0) > 0)
    totalClaims = sum(r.get("claimCount", 0) for r in results)
    avgElapsed = sum(r.get("elapsed", 0) for r in results) / max(total, 1)
    errCount = sum(1 for r in results if r.get("error"))

    print(f"  총 질문: {total}")
    print(f"  correction 발동: {correctionTriggered}/{total}")
    print(f"  최종 mismatch: {totalMismatches}건 (수치 {totalClaims}건 중)")
    print(f"  평균 응답시간: {avgElapsed:.1f}s")
    print(f"  에러: {errCount}/{total}")
    if totalClaims > 0:
        accuracy = (totalClaims - totalMismatches) / totalClaims * 100
        print(f"  수치 정확도: {accuracy:.0f}%")


if __name__ == "__main__":
    main()
