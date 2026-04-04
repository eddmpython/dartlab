"""Reflexion 엔진 — 코드 실행 에러 시 구조화된 복구 피드백 생성.

core.py의 _streamWithCodeExecution() 에러 피드백을 강화한다.
단순히 "에러를 읽고 진단하세요"가 아니라,
에러 패턴 DB에서 유사 에러의 올바른 코드를 찾아 구체적 복구 가이드를 제공.
"""

from __future__ import annotations

import logging
import re

log = logging.getLogger(__name__)


def enrich_error_feedback(
    result: str,
    code: str,
    stock_code: str | None = None,
) -> str:
    """에러 실행 결과에 복구 힌트를 추가한 피드백 메시지 생성.

    Args:
        result: 코드 실행 결과 (에러 포함)
        code: 실행한 코드
        stock_code: 종목코드 (있으면)

    Returns:
        LLM에 피드백할 강화된 에러 메시지
    """
    # 기본 에러 피드백
    feedback_parts = [
        "코드 실행 결과:\n\n",
        f"```\n{result}\n```\n\n",
    ]

    # 에러 패턴 DB에서 유사 패턴 검색
    recovery_hints = _lookupRecoveryHints(result, code)

    if recovery_hints:
        feedback_parts.append("## 유사 에러 복구 가이드\n\n")
        feedback_parts.append(recovery_hints)
        feedback_parts.append("\n\n")

    # 빠른 진단 규칙 (DB 검색 없이 즉시 적용)
    quick_fix = _quickDiagnose(result, code)
    if quick_fix:
        feedback_parts.append(f"**즉시 수정**: {quick_fix}\n\n")

    feedback_parts.append(
        "위 가이드를 참고하여 코드를 수정하세요. "
        "같은 코드를 반복하지 마세요. "
        "API를 모르겠으면 `dartlab.capabilities(search='키워드')`로 검색하세요."
    )

    return "".join(feedback_parts)


def _lookupRecoveryHints(error_text: str, code: str) -> str:
    """error_patterns DB에서 유사 에러의 올바른 코드를 검색."""
    try:
        from dartlab.ai.selfai.error_patterns import lookup
    except ImportError:
        return ""

    patterns = lookup(error_text, limit=2)
    if not patterns:
        return ""

    hints = []
    for p in patterns:
        if p.correct_code:
            hints.append(
                f"- **{p.error_type}** (발생 {p.frequency}회): "
                f"`{p.wrong_code}` → `{p.correct_code}`"
            )

    return "\n".join(hints) if hints else ""


# ── 빠른 진단 규칙 (하드코딩, DB 불필요) ─────────────────────

_QUICK_RULES: list[tuple[re.Pattern, str, str]] = [
    # analysis 인자 부족
    (
        re.compile(r"analysis\(\) .*(takes|missing).*positional argument", re.IGNORECASE),
        r'\.analysis\("(\w+)"\)',
        'analysis()는 2인자 필수: c.analysis("financial", "수익성"). '
        "그룹: financial, valuation, forecast",
    ),
    # macro keyword arg
    (
        re.compile(r"macro\(\) got an unexpected keyword argument", re.IGNORECASE),
        r"macro\(",
        'macro()는 위치인자만: dartlab.macro("사이클"). '
        "축: 사이클, 금리, 자산, 심리, 유동성, 종합",
    ),
    # Polars .empty
    (
        re.compile(r"has no attribute 'empty'", re.IGNORECASE),
        r"\.empty",
        "Polars에 .empty 없음. len(df) == 0 또는 df.height == 0 사용",
    ),
    # Polars .iterrows
    (
        re.compile(r"has no attribute 'iterrows'", re.IGNORECASE),
        r"\.iterrows\(",
        "Polars에 .iterrows() 없음. df.iter_rows(named=True) 사용",
    ),
    # Polars .sort_values
    (
        re.compile(r"has no attribute 'sort_values'", re.IGNORECASE),
        r"\.sort_values\(",
        'Polars에 .sort_values() 없음. df.sort("col") 사용',
    ),
    # KeyError — 존재하지 않는 키
    (
        re.compile(r"KeyError:", re.IGNORECASE),
        r"\[",
        "반환값에 해당 키가 없음. 먼저 print(result.keys()) 또는 print(df.columns)로 확인",
    ),
    # c.sections 메모리 초과
    (
        re.compile(r"(MemoryError|killed|OOM)", re.IGNORECASE),
        r"c\.sections",
        'c.sections는 409MB. c.show("IS") 등 개별 topic 조회 사용',
    ),
    # review 남용
    (
        re.compile(r"review", re.IGNORECASE),
        r"\.review\(",
        'review()는 보고서 요청 시만 사용. 분석에는 c.analysis("financial", "축")을 사용',
    ),
]


def _quickDiagnose(error_text: str, code: str) -> str:
    """에러와 코드를 빠르게 매칭하여 즉시 수정 가이드 반환."""
    for error_re, code_pattern, fix in _QUICK_RULES:
        if error_re.search(error_text) and re.search(code_pattern, code):
            return fix
    return ""


def record_execution(
    code: str,
    result: str,
    is_error: bool,
    stock_code: str | None = None,
) -> None:
    """코드 실행 결과를 에러 패턴 DB에 기록 (에러인 경우만).

    core.py에서 코드 실행 후 호출하여 에러 패턴을 자동 축적.
    """
    if not is_error:
        return

    try:
        from dartlab.ai.selfai.error_patterns import record

        tool_name = _detectTool(code)
        record(
            error_text=result,
            wrong_code=code[:2000],
            tool_name=tool_name,
        )
    except ImportError:
        pass


def _detectTool(code: str) -> str:
    """코드에서 주요 도구 감지."""
    if ".analysis(" in code:
        return "analysis"
    if "dartlab.macro(" in code:
        return "macro"
    if "dartlab.scan(" in code:
        return "scan"
    if ".credit(" in code:
        return "credit"
    if ".review(" in code:
        return "review"
    if ".gather(" in code:
        return "gather"
    return ""
