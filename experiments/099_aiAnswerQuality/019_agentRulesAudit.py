"""실험 019: Agent 3대 규칙 + 데이터 신뢰도 계층 결정론적 검증.

실험 ID: 019
실험명: 시스템 프롬프트 3대 규칙 + 도구 연쇄 + 신뢰도 계층 적용 검증

목적:
- Change 1~7 적용 후, 시스템 프롬프트와 Super Tool description에
  핵심 키워드/구조가 올바르게 포함되었는지 결정론적으로 검증

가설:
1. KR/EN/Compact 프롬프트에 Planning, Persistence, Tool Chaining 키워드 존재
2. 7개 Super Tool description에 연쇄 안내 키워드 존재
3. 실패 복구 예시 최소 3개 존재
4. 데이터 신뢰도 계층 테이블 존재
5. analysis_rules에 안티패턴 예시 존재
6. builder.py에 도구 추천 힌트 존재

방법:
1. 시스템 프롬프트 텍스트에서 키워드 검색
2. Super Tool 파일에서 registerTool description 내 연쇄 키워드 검색
3. analysis_rules.py에서 안티패턴 키워드 검색
4. builder.py에서 도구 추천 힌트 검색

결과 (실험 후 작성):
- 38/38 전체 통과
- KR/EN/Compact 3개 프롬프트에 3대 규칙 키워드 모두 존재
- 7개 Super Tool description에 연쇄 안내 모두 존재
- 데이터 신뢰도 계층 KR/EN 양쪽 존재
- 안티패턴 예시 + 올바른 복구 예시 모두 존재
- builder.py 도구 추천 힌트 정상 동작

결론:
- 채택. 7개 변경 전부 결정론적 검증 통과.
- GPT-4.1/Anthropic ACI/Bloomberg 기법 기반 시스템 프롬프트 강화 완료.

실험일: 2026-03-26
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "src" / "dartlab"
PASS = 0
FAIL = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    """검증 결과 출력."""
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} — {detail}")


def test_system_prompts() -> None:
    """Check 1: KR/EN/Compact 프롬프트 3대 규칙 키워드."""
    print("\n[Check 1] 시스템 프롬프트 3대 규칙")
    from dartlab.ai.conversation.templates.system_base import (
        SYSTEM_PROMPT_COMPACT,
        SYSTEM_PROMPT_EN,
        SYSTEM_PROMPT_KR,
    )

    # KR
    check("KR: Planning 키워드", "분석 전략" in SYSTEM_PROMPT_KR or "Planning" in SYSTEM_PROMPT_KR)
    check("KR: Persistence 키워드", "포기 금지" in SYSTEM_PROMPT_KR or "Persistence" in SYSTEM_PROMPT_KR)
    check("KR: Tool Chaining 키워드", "도구 연쇄" in SYSTEM_PROMPT_KR or "Tool Chaining" in SYSTEM_PROMPT_KR)
    check("KR: 질문 유형별 도구 순서 테이블", "질문 유형" in SYSTEM_PROMPT_KR and "1차 도구" in SYSTEM_PROMPT_KR)
    check("KR: 실패 복구 경로", "실패 복구" in SYSTEM_PROMPT_KR)

    # EN
    check("EN: Planning keyword", "Analysis Strategy" in SYSTEM_PROMPT_EN or "Planning" in SYSTEM_PROMPT_EN)
    check("EN: Persistence keyword", "Never Give Up" in SYSTEM_PROMPT_EN or "Persistence" in SYSTEM_PROMPT_EN)
    check("EN: Tool Chaining keyword", "Tool Chaining" in SYSTEM_PROMPT_EN)
    check("EN: Question type tool table", "Question Type" in SYSTEM_PROMPT_EN and "1st Tool" in SYSTEM_PROMPT_EN)
    check("EN: Failure Recovery paths", "Failure Recovery" in SYSTEM_PROMPT_EN)

    # Compact
    check("Compact: 3대 규칙 키워드", "Planning" in SYSTEM_PROMPT_COMPACT or "3대 규칙" in SYSTEM_PROMPT_COMPACT)
    check("Compact: Persistence", "Persistence" in SYSTEM_PROMPT_COMPACT or "포기 금지" in SYSTEM_PROMPT_COMPACT)
    check("Compact: Tool Chaining", "Tool Chaining" in SYSTEM_PROMPT_COMPACT or "2인조" in SYSTEM_PROMPT_COMPACT)


def test_data_reliability() -> None:
    """Check 2: 데이터 신뢰도 계층."""
    print("\n[Check 2] 데이터 신뢰도 계층")
    from dartlab.ai.conversation.templates.system_base import (
        SYSTEM_PROMPT_EN,
        SYSTEM_PROMPT_KR,
    )

    check("KR: 신뢰도 테이블", "데이터 출처 신뢰도" in SYSTEM_PROMPT_KR)
    check("KR: finance 최고 신뢰", "최고" in SYSTEM_PROMPT_KR and "XBRL" in SYSTEM_PROMPT_KR)
    check("KR: 상충 시 finance 우선", "finance를 신뢰" in SYSTEM_PROMPT_KR)
    check("EN: Reliability table", "Data Source Reliability" in SYSTEM_PROMPT_EN)
    check("EN: finance highest", "Highest" in SYSTEM_PROMPT_EN and "XBRL" in SYSTEM_PROMPT_EN)
    check("EN: conflict finance wins", "trust finance" in SYSTEM_PROMPT_EN)


def test_failure_recovery_examples() -> None:
    """Check 3: 실패 복구 예시 최소 3개."""
    print("\n[Check 3] 실패 복구 예시")
    from dartlab.ai.conversation.templates.system_base import SYSTEM_PROMPT_KR

    # 실패 복구 예시는 "→" 연쇄 패턴으로 카운트 (데이터 없음 + 대안 경로)
    recovery_lines = [line for line in SYSTEM_PROMPT_KR.split("\n") if "→" in line and ("데이터 없음" in line or "복구" in line or "보강" in line)]
    check(f"실패 복구 예시 ≥3개 (발견: {len(recovery_lines)})", len(recovery_lines) >= 3)

    check("복합 분석 예시 존재", "복합 분석 예시" in SYSTEM_PROMPT_KR)


def test_super_tool_descriptions() -> None:
    """Check 4: 7개 Super Tool description 연쇄 안내."""
    print("\n[Check 4] Super Tool 연쇄 안내")

    tools_dir = ROOT / "ai" / "tools" / "superTools"
    expected = {
        "explore.py": "연쇄 사용",
        "finance.py": "연쇄 사용",
        "analyze.py": "연쇄 사용",
        "market.py": "외부 소스",
        "chart.py": "시각화",
        "system.py": "시스템 메타",
        "openapi.py": "기본 도구로 부족",
    }

    for filename, keyword in expected.items():
        filepath = tools_dir / filename
        content = filepath.read_text(encoding="utf-8")
        check(f"{filename}: '{keyword}' 키워드", keyword in content, f"'{keyword}' not found")


def test_analysis_rules_antipattern() -> None:
    """Check 5: analysis_rules 안티패턴 예시."""
    print("\n[Check 5] 안티패턴 예시")
    from dartlab.ai.conversation.templates.analysis_rules import FEW_SHOT_EXAMPLES

    check("안티패턴 키 존재", "안티패턴" in FEW_SHOT_EXAMPLES)
    if "안티패턴" in FEW_SHOT_EXAMPLES:
        content = FEW_SHOT_EXAMPLES["안티패턴"]
        check("안티패턴 1: 도구 미호출", "도구를 호출하지 않고" in content or "도구 호출 없이" in content)
        check("안티패턴 2: 한 번 실패 포기", "포기" in content or "대안 시도 없이" in content)
        check("올바른 복구 예시", "올바른" in content or "좋은 예" in content)


def test_builder_tool_hints() -> None:
    """Check 6: builder.py 도구 추천 힌트."""
    print("\n[Check 6] builder.py 도구 추천 힌트")

    builder_path = ROOT / "ai" / "context" / "builder.py"
    content = builder_path.read_text(encoding="utf-8")

    check("도구 추천 힌트 블록", "도구 추천 힌트" in content)
    check("재무 데이터 포함 시 ratios 추천", "finance(action='ratios')" in content)
    check("재무 데이터 미포함 시 modules 추천", "finance(action='modules')" in content)


def test_en_response_contract() -> None:
    """Check 7: EN 프롬프트에 Response Contract 존재."""
    print("\n[Check 7] EN Response Contract")
    from dartlab.ai.conversation.templates.system_base import SYSTEM_PROMPT_EN

    check("EN: Response Contract", "Response Contract" in SYSTEM_PROMPT_EN)
    check("EN: finance tool citation rule", "finance tool results" in SYSTEM_PROMPT_EN)
    check("EN: explore tool citation rule", "explore tool results" in SYSTEM_PROMPT_EN)


if __name__ == "__main__":
    test_system_prompts()
    test_data_reliability()
    test_failure_recovery_examples()
    test_super_tool_descriptions()
    test_analysis_rules_antipattern()
    test_builder_tool_hints()
    test_en_response_contract()

    print(f"\n{'='*50}")
    print(f"결과: {PASS} PASS / {FAIL} FAIL / {PASS + FAIL} TOTAL")
    if FAIL > 0:
        print("❌ 일부 검증 실패")
        sys.exit(1)
    else:
        print("✅ 전체 검증 통과")
