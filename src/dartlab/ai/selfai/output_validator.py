"""Output Validator — LLM이 생성한 코드를 실행 전에 정적 의미 검증.

AST 구문 검증(coding.py)과 별개로, dartlab API 시그니처와 금지 패턴을
정적으로 검증하여 실행 전에 에러를 차단한다.

검증 실패 시 경고 메시지를 LLM에 피드백하여 코드 수정을 유도.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """검증 결과."""

    passed: bool
    warnings: list[str] = field(default_factory=list)

    def feedback(self) -> str:
        """LLM 피드백용 문자열. 경고가 없으면 빈 문자열."""
        if not self.warnings:
            return ""
        lines = ["코드 검증 경고 (실행 전 자동 감지):"]
        for w in self.warnings:
            lines.append(f"- {w}")
        lines.append("\n위 문제를 수정한 코드를 다시 작성하세요.")
        return "\n".join(lines)


# ── 검증 규칙 ───────────────────────────────────────────────

_RULES: list[tuple[re.Pattern, re.Pattern | None, str]] = [
    # (에러 조건 패턴 on code, 추가 조건 or None, 경고 메시지)

    # analysis()는 반드시 2인자: group, axis
    (
        re.compile(r'\.analysis\(\s*"[^"]+"\s*\)'),  # 1인자만
        None,
        'analysis()는 2인자 필수: c.analysis("financial", "수익성"). '
        "그룹: financial, valuation, forecast",
    ),
    # macro()에 keyword argument 금지
    (
        re.compile(r"macro\(\s*(topic|axis|market)\s*="),
        None,
        'macro()는 위치인자만: dartlab.macro("사이클"). '
        'market은 2번째: dartlab.macro("사이클", market="US")',
    ),
    # c.sections 직접 접근 (409MB 메모리 위험)
    (
        re.compile(r"\bc\.sections\b"),
        None,
        'c.sections는 409MB 메모리 사용. c.show("IS") 등 개별 topic 조회로 대체',
    ),
    # review() 사용 (분석 질문에서는 analysis 우선)
    (
        re.compile(r"\.review\("),
        None,
        'review()는 "보고서" 명시 요청 시만 사용. '
        '분석에는 c.analysis("financial", "축")을 사용',
    ),
    # scan DataFrame join (타임아웃 위험)
    (
        re.compile(r"\.join\("),
        re.compile(r"scan|dartlab\.scan"),  # scan 결과에 join 시도
        "scan DataFrame에 join 금지 (타임아웃 위험). 개별 scan 결과를 순차 해석",
    ),
    # Polars pandas 혼용: .empty
    (
        re.compile(r"\.empty\b"),
        re.compile(r"(df|result|data)"),  # DataFrame 변수에 .empty
        "Polars에 .empty 없음. len(df) == 0 또는 df.height == 0 사용",
    ),
    # Polars pandas 혼용: .iterrows
    (
        re.compile(r"\.iterrows\("),
        None,
        "Polars에 .iterrows() 없음. df.iter_rows(named=True) 사용",
    ),
    # Polars pandas 혼용: .sort_values
    (
        re.compile(r"\.sort_values\("),
        None,
        'Polars에 .sort_values() 없음. df.sort("col") 사용',
    ),
    # Polars pandas 혼용: .to_dict()
    (
        re.compile(r"\.to_dict\(\)"),
        None,
        "Polars에 .to_dict() 없음. df.to_dicts() (리스트) 또는 df.to_dict(as_series=False) 사용",
    ),
    # import dartlab (preamble에서 이미 주입)
    (
        re.compile(r"^import dartlab\s*$", re.MULTILINE),
        None,
        "import dartlab은 preamble에서 이미 주입됨. 중복 import 불필요",
    ),
    # requests 직접 사용 (newsSearch/webSearch 사용해야 함)
    (
        re.compile(r"import requests|requests\.get"),
        None,
        "requests 직접 사용 금지. newsSearch(query) 또는 webSearch(query) 사용",
    ),
]


def validate(code: str) -> ValidationResult:
    """코드를 정적 검증하여 경고 목록을 반환.

    Args:
        code: LLM이 생성한 Python 코드

    Returns:
        ValidationResult — passed=True면 경고 없음
    """
    warnings: list[str] = []

    for pattern, extra_condition, message in _RULES:
        if pattern.search(code):
            # 추가 조건이 있으면 그것도 만족해야 경고
            if extra_condition is None or extra_condition.search(code):
                warnings.append(message)

    return ValidationResult(
        passed=len(warnings) == 0,
        warnings=warnings,
    )
