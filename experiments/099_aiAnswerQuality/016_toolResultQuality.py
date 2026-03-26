"""실험 016: 도구 결과 품질 + 에러 투명성 검증

목적:
- Super Tool 에러/빈 결과 시 LLM에 대안 행동을 유도하는 메시지가 효과적인지 검증.
- Pipeline 에러 경고가 context에 포함되어 LLM이 인지하는지 확인.

가설:
1. 에러 메시지에 "대안: ..." 제안이 있으면, LLM이 대안 도구를 호출하는 비율이 높아진다
2. Pipeline 경고가 context에 포함되면, LLM이 "일부 분석이 실패했습니다"를 답변에 반영한다

방법:
1. 의도적으로 실패하기 어려운 환경이므로, 에러 메시지 포맷을 직접 검증
2. Super Tool 에러 반환 문자열에 "대안:" 패턴이 포함되어 있는지 확인
3. Pipeline warnings 메커니즘이 정상 동작하는지 확인

결과:
- Super Tool 에러 메시지 검증: 7개 도구 × 에러 패턴 확인
- Pipeline warnings: 조용한 실패 → context 경고 주입 메커니즘 설치

| 도구 | 에러 시 대안 제안 | 빈 결과 시 안내 |
|------|-----------------|---------------|
| explore | ✅ "action='topics'로 확인하세요" | ✅ "사용 가능한 topic이 없습니다" |
| finance | ✅ "action=modules로 확인하세요" | ✅ "데이터가 없습니다" |
| analyze | ✅ "대안: finance(action='ratios')..." | ✅ "데이터를 생성할 수 없습니다" |
| market | ✅ "네트워크 연결 확인" / "대안: analyze..." | ✅ "code를 지정하세요" |
| openapi | △ 기본 에러 메시지만 | ✅ "endpoint를 지정하세요" |
| system | △ 기본 에러 메시지만 | ✅ "회사를 먼저 선택하면..." |
| chart | ✅ "가능: {available}" | ✅ "재무 데이터가 없습니다" |

결론:
- 가설 1: 코드 레벨 검증 — 핵심 4개 도구(explore, finance, analyze, market)에
  에러 시 "대안:" 패턴 설치 완료. 실제 LLM 반응은 E2E 테스트에서 검증 필요.
- 가설 2: pipeline.py에 warnings 수집 + context 주입 메커니즘 설치 완료.
  실패 시 "[참고] 일부 분석이 실패했습니다: {엔진명}. 도구를 직접 호출하여 보충하세요."
- Phase 4는 코드 레벨 방어벽 설치이며, 실제 효과는 Phase 5 E2E에서 통합 검증.

실험일: 2026-03-26
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


def checkSuperToolErrorPatterns():
    """Super Tool 에러 메시지에 대안 제안 패턴이 있는지 검증."""
    import importlib
    import inspect

    toolDir = os.path.join(
        os.path.dirname(__file__), "..", "..", "src", "dartlab", "engines", "ai", "tools", "superTools"
    )

    results = {}
    altPattern = re.compile(r"대안[:：]|확인하세요|네트워크|가능:")

    for fname in sorted(os.listdir(toolDir)):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        toolName = fname[:-3]
        fpath = os.path.join(toolDir, fname)
        with open(fpath, encoding="utf-8") as f:
            source = f.read()

        # except 블록 내 return 문에서 대안 제안 패턴 찾기
        exceptBlocks = re.findall(r"except\s*\(.*?\).*?:\s*\n\s*return\s+f?\"(.+?)\"", source, re.DOTALL)
        hasAlt = any(altPattern.search(block) for block in exceptBlocks)

        # 빈 결과 처리 패턴
        emptyPatterns = re.findall(r"return\s+(?:f?\".*(?:없습니다|지정하세요|확인하세요).*\")", source)

        results[toolName] = {
            "exceptBlocks": len(exceptBlocks),
            "hasAlternativeSuggestion": hasAlt,
            "emptyResultHandlers": len(emptyPatterns),
        }

    return results


def checkPipelineWarnings():
    """Pipeline warnings 메커니즘이 설치되어 있는지 검증."""
    pipelinePath = os.path.join(
        os.path.dirname(__file__), "..", "..", "src", "dartlab", "engines", "ai", "runtime", "pipeline.py"
    )
    with open(pipelinePath, encoding="utf-8") as f:
        source = f.read()

    hasWarningsList = "warnings: list[str]" in source or "warnings:" in source
    hasWarningAppend = "warnings.append" in source
    hasWarningInject = "일부 분석이 실패했습니다" in source

    return {
        "hasWarningsList": hasWarningsList,
        "hasWarningAppend": hasWarningAppend,
        "hasWarningInject": hasWarningInject,
    }


def main():
    print("=" * 60)
    print("016: 도구 결과 품질 + 에러 투명성 검증")
    print("=" * 60)

    print("\n[1] Super Tool 에러 메시지 패턴 검증\n")
    toolResults = checkSuperToolErrorPatterns()
    for name, info in toolResults.items():
        alt = "✅" if info["hasAlternativeSuggestion"] else "△"
        print(
            f"  {name}: except {info['exceptBlocks']}개 | 대안 제안: {alt} | 빈 결과 핸들러: {info['emptyResultHandlers']}개"
        )

    print("\n[2] Pipeline Warnings 메커니즘 검증\n")
    pipelineResults = checkPipelineWarnings()
    for key, val in pipelineResults.items():
        status = "✅" if val else "❌"
        print(f"  {key}: {status}")

    print("\n[3] 요약")
    altCount = sum(1 for r in toolResults.values() if r["hasAlternativeSuggestion"])
    totalTools = len(toolResults)
    print(f"  대안 제안 포함 도구: {altCount}/{totalTools}")
    print(f"  Pipeline warnings: {'설치됨' if all(pipelineResults.values()) else '미완료'}")


if __name__ == "__main__":
    main()
