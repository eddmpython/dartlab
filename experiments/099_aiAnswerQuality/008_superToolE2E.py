"""실험 008: Super Tool E2E — 기존 101개 vs 7개 Super Tool 비교

실험 ID: 008
실험명: Super Tool 모드 E2E 스키마 + 도구 수 비교

목적:
- Super Tool 모드에서 도구 수 대폭 감소 확인
- 동적 enum (topic, module, apiType) 스키마 정합성 확인
- buildToolPrompt의 Super Tool 전용 분석 절차 생성 확인
- explore(search) 동적 키워드 검색 동작 확인

가설:
1. Super Tool 모드: company 있을 때 ≤ 8개 (7 super + plugin)
2. 기존 모드: company 있을 때 80개+
3. explore의 target에 동적 enum이 포함
4. finance의 module에 동적 enum이 포함
5. explore(search, '비용') → fsSummary, consolidatedNotes 반환

방법:
1. 삼성전자(005930) Company 생성
2. build_tool_runtime(useSuperTools=True/False) 비교
3. 스키마에서 enum 필드 추출
4. explore(action='search', keyword='비용') 직접 실행
5. buildToolPrompt 내용 검증

결과:
=== Phase 1: Company 없이 ===
  Super Tool: 4개, Legacy: 25개

=== Phase 2: 삼성전자 바인딩 ===
  Super Tool: 8개 (7 super + 1 plugin), Legacy: 96개
  explore: action 7 enum, target 53 enum (동적 topic)
  finance: action 8 enum, module 9 enum (동적), apiType 24 enum (동적)
  analyze: action 7 enum
  system/market/openapi/chart: action enum 포함

=== Phase 3: explore(search) ===
  '비용' → 2건 (fsSummary, consolidatedNotes)
  '배당' → 1건 (dividend)
  '리스크' → 0건 (topicLabels에 "리스크" aliases 없음 — "위험" 등록됨)
  '원재료' → 1건 (rawMaterial)
  '주석' → 2건 (consolidatedNotes, financialNotes)

=== Phase 4: buildToolPrompt ===
  Super Tool 전용 분석 절차 포함 확인 ✅
  explore()/finance()/analyze() 기반 전문가 플로우 생성 ✅

결론:
- 가설 1 채택: Super Tool 8개 (≤ 10)
- 가설 2 채택: Legacy 96개
- 가설 3 채택: explore target에 53개 동적 topic enum
- 가설 4 채택: finance module에 9개 동적 enum
- 가설 5 부분 채택: '비용' → fsSummary, consolidatedNotes 정확 반환
  단 "리스크"는 topicLabels에 정확히 "리스크"가 aliases에 없어서 미매칭
  → riskDerivative aliases에 "리스크" 추가 필요

실험일: 2026-03-25
"""

from __future__ import annotations

import gc
import sys

sys.path.insert(0, "src")


def main():
    import dartlab
    from dartlab.ai.tools.registry import build_tool_runtime
    from dartlab.ai.tools.selector import buildToolPrompt

    print("=" * 60)
    print("Phase 1: Company 없이 도구 수 비교")
    print("=" * 60)

    rt_super = build_tool_runtime(useSuperTools=True)
    rt_legacy = build_tool_runtime(useSuperTools=False)
    print(f"  Super Tool (no company): {len(rt_super.get_tool_schemas())}개")
    print(f"  Legacy (no company): {len(rt_legacy.get_tool_schemas())}개")

    print("\n" + "=" * 60)
    print("Phase 2: Company 바인딩 도구 수 비교")
    print("=" * 60)

    company = dartlab.Company("005930")
    print(f"  Company: {company.corpName}")

    rt_super2 = build_tool_runtime(company, useSuperTools=True)
    rt_legacy2 = build_tool_runtime(company, useSuperTools=False)
    superSchemas = rt_super2.get_tool_schemas()
    legacySchemas = rt_legacy2.get_tool_schemas()
    print(f"  Super Tool (with company): {len(superSchemas)}개")
    print(f"  Legacy (with company): {len(legacySchemas)}개")

    print("\n  --- Super Tool 스키마 ---")
    for s in superSchemas:
        name = s["function"]["name"]
        params = s["function"].get("parameters", {}).get("properties", {})
        enumFields = {}
        for k, v in params.items():
            if "enum" in v:
                enumFields[k] = len(v["enum"])
        enumInfo = f"  enums: {enumFields}" if enumFields else ""
        print(f"  - {name}{enumInfo}")

    print("\n" + "=" * 60)
    print("Phase 3: explore(search) 동적 검색 테스트")
    print("=" * 60)

    testKeywords = ["비용", "배당", "리스크", "원재료", "주석"]
    for kw in testKeywords:
        result = rt_super2.execute_tool("explore", {"action": "search", "keyword": kw})
        lines = result.strip().split("\n")
        topicCount = sum(1 for l in lines if l.startswith("- `"))
        print(f"  '{kw}' → {topicCount}건: {lines[0][:80]}")

    print("\n" + "=" * 60)
    print("Phase 4: buildToolPrompt Super Tool 전용 절차 확인")
    print("=" * 60)

    # Super Tool 모드로 빌드 후 prompt 생성
    rt_super3 = build_tool_runtime(company, useSuperTools=True)
    prompt = buildToolPrompt(rt_super3)
    hasSuper = "Super Tool" in prompt
    print(f"  Super Tool 절차 포함: {hasSuper}")
    if hasSuper:
        for line in prompt.split("\n"):
            if "Super Tool" in line or "explore(" in line or "finance(" in line:
                print(f"    {line}")

    # 메모리 정리
    del company
    gc.collect()

    print("\n" + "=" * 60)
    print("요약")
    print("=" * 60)


if __name__ == "__main__":
    main()
