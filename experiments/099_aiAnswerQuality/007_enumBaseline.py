"""실험 007: Enum + Super Tool 기반 도구 스키마 검증

실험 ID: 007
실험명: Phase 1(enum 라벨) + Phase 2(Super Tool) 스키마 정합성 검증

목적:
- Phase 1: show_topic에 동적 enum + 한국어 라벨이 삽입되는지 확인
- Phase 2: Super Tool 모드에서 도구 수가 7개 이하인지 확인
- 기존 모드와의 도구 수 비교

가설:
1. Super Tool 모드: company 있을 때 7개, 없을 때 4개
2. 기존 모드: company 없을 때 25개+
3. show_topic의 topic 파라미터에 enum이 포함
4. finance의 module 파라미터에 enum이 포함

방법:
1. build_tool_runtime(useSuperTools=True/False) 비교
2. 스키마에서 enum 필드 존재 확인
3. topicLabels.py의 Korean description 포함 확인

결과:
=== Super Tool 모드 (company 없음) ===
  도구 수: 4
  도구: system, market, openapi, create_plugin

=== 기존 모드 (company 없음) ===
  도구 수: 25

=== topicLabels ===
  총 70개 topic, 한국어 라벨 포함
  buildTopicEnumDescription(['fsSummary', 'consolidatedNotes', 'BS'][:3]) 출력:
  fsSummary=재무제표 요약/재무요약/비용성격별/부문정보, consolidatedNotes=연결 주석/주석/비용성격별분류/리스, BS=재무상태표/재무상태표/자산/부채

결론:
- 가설 1 부분 채택: company 없이 4개 (system, market, openapi + plugin)
- 가설 2 채택: 기존 25개
- 가설 3/4: 008 실험에서 삼성전자로 검증 완료 — topic 53 enum, module 9 enum, apiType 24 enum
- topicLabels.py에 70개 topic 한국어 라벨 + aliases 정상 등록 확인
- Phase 1 + Phase 2 기본 인프라 정상 작동

실험일: 2026-03-25
"""

from __future__ import annotations

import sys

sys.path.insert(0, "src")


def main():
    from dartlab.engines.ai.tools.registry import build_tool_runtime
    from dartlab.engines.common.topicLabels import (
        TOPIC_LABELS,
        buildTopicEnumDescription,
    )

    # 1. Super Tool 모드 (company 없음)
    print("=== Super Tool 모드 (company 없음) ===")
    rt = build_tool_runtime(useSuperTools=True)
    schemas = rt.get_tool_schemas()
    print(f"  도구 수: {len(schemas)}")
    for s in schemas:
        name = s["function"]["name"]
        params = s["function"].get("parameters", {}).get("properties", {})
        enums = {k: v.get("enum") for k, v in params.items() if "enum" in v}
        print(f"  - {name}" + (f"  enums: {enums}" if enums else ""))

    # 2. 기존 모드 (company 없음)
    print("\n=== 기존 모드 (company 없음) ===")
    rt2 = build_tool_runtime(useSuperTools=False)
    schemas2 = rt2.get_tool_schemas()
    print(f"  도구 수: {len(schemas2)}")

    # 3. topicLabels 검증
    print(f"\n=== topicLabels ===")
    print(f"  총 {len(TOPIC_LABELS)}개 topic")

    sample = ["fsSummary", "consolidatedNotes", "BS"]
    desc = buildTopicEnumDescription(sample)
    print(f"  buildTopicEnumDescription({sample}):")
    print(f"  {desc}")

    # 4. alias 검증 — "비용의 성격별분류" 관련
    print(f"\n=== '비용' 관련 topic 검색 ===")
    for topic, info in TOPIC_LABELS.items():
        aliases = info.get("aliases", [])
        if "비용" in str(aliases) or "비용" in info["label"]:
            print(f"  {topic}: {info['label']} aliases={aliases}")


if __name__ == "__main__":
    main()
