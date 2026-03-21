"""LLM 시스템 프롬프트 — 조립·분류·파싱 로직.

템플릿 텍스트는 templates/ 하위 모듈에 분리되어 있다.
이 파일은 로직(조립, 질문 분류, 응답 파싱)만 담당한다.
"""

from __future__ import annotations

import re as _re
from typing import Any

from .templates.analysis_rules import (
    CROSS_VALIDATION_COMPACT as _CROSS_VALIDATION_COMPACT,
)
from .templates.analysis_rules import (
    CROSS_VALIDATION_RULES as _CROSS_VALIDATION_RULES,
)
from .templates.analysis_rules import (
    FEW_SHOT_COMPACT as _FEW_SHOT_COMPACT,
)
from .templates.analysis_rules import (
    FEW_SHOT_EXAMPLES as _FEW_SHOT_EXAMPLES,
)
from .templates.analysis_rules import (
    QUESTION_TYPE_MAP as _QUESTION_TYPE_MAP,
)
from .templates.analysis_rules import (
    TOPIC_COMPACT as _TOPIC_COMPACT,
)
from .templates.analysis_rules import (
    TOPIC_PROMPTS as _TOPIC_PROMPTS,
)
from .templates.benchmarks import _INDUSTRY_BENCHMARKS, _SECTOR_MAP
from .templates.self_critique import (
    SELF_CRITIQUE_PROMPT,
)
from .templates.self_critique import (
    SIGNAL_KEYWORDS as _SIGNAL_KEYWORDS,
)

# ── 템플릿 데이터 임포트 ──────────────────────────────────
from .templates.system_base import (
    SYSTEM_PROMPT_COMPACT,
    SYSTEM_PROMPT_EN,
    SYSTEM_PROMPT_KR,
)

# ══════════════════════════════════════
# 질문 분류
# ══════════════════════════════════════


def _classify_question(question: str) -> str | None:
    """질문 텍스트를 분석 유형으로 분류.

    Returns:
            "건전성", "수익성", "성장성", "배당", "지배구조", "리스크", "종합" 또는 None
    """
    scores: dict[str, int] = {}
    for q_type, keywords in _QUESTION_TYPE_MAP.items():
        score = sum(1 for kw in keywords if kw in question)
        if score > 0:
            scores[q_type] = score

    if not scores:
        return None

    return max(scores, key=scores.get)


def _classify_question_multi(question: str, max_types: int = 3) -> list[str]:
    """복합 질문에서 여러 분석 유형을 감지.

    Returns:
            매칭된 유형 리스트 (점수 높은 순, 최대 max_types개)
    """
    scores: dict[str, int] = {}
    for q_type, keywords in _QUESTION_TYPE_MAP.items():
        score = sum(1 for kw in keywords if kw in question)
        if score > 0:
            scores[q_type] = score

    if not scores:
        return []

    sorted_types = sorted(scores, key=scores.get, reverse=True)
    return sorted_types[:max_types]


def _match_sector(sector_name: str) -> str | None:
    """KRX 업종명에서 벤치마크 키 매칭."""
    if not sector_name:
        return None

    # 정확 매칭
    if sector_name in _SECTOR_MAP:
        return _SECTOR_MAP[sector_name]

    # 키워드 부분 매칭
    for keyword, benchmark_key in _SECTOR_MAP.items():
        if keyword in sector_name:
            return benchmark_key

    return None


# ══════════════════════════════════════
# 시스템 프롬프트 조립
# ══════════════════════════════════════


def build_system_prompt(
    custom: str | None = None,
    lang: str = "ko",
    included_modules: list[str] | None = None,
    sector: str | None = None,
    question_type: str | None = None,
    question_types: list[str] | None = None,
    compact: bool = False,
) -> str:
    """시스템 프롬프트 조립.

    Args:
            custom: 사용자 지정 프롬프트 (있으면 이것만 사용)
            lang: "ko" 또는 "en"
            included_modules: 컨텍스트에 포함된 모듈 목록 → 토픽 프롬프트 동적 추가
            sector: KRX 업종명 → 업종별 벤치마크 추가
            question_type: 단일 질문 유형 → Few-shot 예시 추가 (하위호환)
            question_types: 복수 질문 유형 → question_type보다 우선
            compact: True면 소형 모델용 간결 프롬프트 (Ollama)
    """
    if custom:
        return custom

    q_types = question_types or ([question_type] if question_type else [])

    if compact:
        base = SYSTEM_PROMPT_COMPACT
        appended: list[str] = []

        if sector:
            benchmark_key = _match_sector(sector)
            if benchmark_key and benchmark_key in _INDUSTRY_BENCHMARKS:
                appended.append(_INDUSTRY_BENCHMARKS[benchmark_key])

        if included_modules:
            module_set = set(included_modules)
            for _tname, (trigger_modules, prompt_text) in _TOPIC_COMPACT.items():
                if module_set & trigger_modules:
                    appended.append(prompt_text)

        if included_modules:
            fs_modules = {"BS", "IS", "CF"}
            if fs_modules & set(included_modules):
                appended.append(_CROSS_VALIDATION_COMPACT)

        for qt in q_types[:1]:
            if qt in _FEW_SHOT_COMPACT:
                appended.append(_FEW_SHOT_COMPACT[qt])

        if appended:
            return base + "\n".join(appended)
        return base

    base = SYSTEM_PROMPT_KR if lang == "ko" else SYSTEM_PROMPT_EN
    appended = []

    if sector:
        benchmark_key = _match_sector(sector)
        if benchmark_key and benchmark_key in _INDUSTRY_BENCHMARKS:
            appended.append(_INDUSTRY_BENCHMARKS[benchmark_key])

    if included_modules:
        module_set = set(included_modules)
        for _topic_name, (trigger_modules, prompt_text) in _TOPIC_PROMPTS.items():
            if module_set & trigger_modules:
                appended.append(prompt_text)

    if included_modules:
        fs_modules = {"BS", "IS", "CF"}
        if fs_modules & set(included_modules):
            appended.append(_CROSS_VALIDATION_RULES)

    for qt in q_types[:2]:
        if qt in _FEW_SHOT_EXAMPLES:
            appended.append(_FEW_SHOT_EXAMPLES[qt])

    if appended:
        return base + "\n".join(appended)

    return base


# ══════════════════════════════════════
# Self-Critique
# ══════════════════════════════════════


def build_critique_messages(
    original_response: str,
    context_text: str,
    question: str,
) -> list[dict[str, str]]:
    """Self-Critique용 메시지 리스트 생성."""
    return [
        {"role": "system", "content": SELF_CRITIQUE_PROMPT},
        {
            "role": "user",
            "content": (
                f"## 원본 질문\n{question}\n\n"
                f"## 제공된 데이터\n{context_text[:3000]}\n\n"
                f"## 검토 대상 응답\n{original_response}"
            ),
        },
    ]


def parse_critique_result(critique_text: str) -> tuple[bool, str]:
    """Self-Critique 결과 파싱.

    Returns:
            (passed, revised_or_original)
            - passed=True이면 원본 그대로 사용
            - passed=False이면 수정된 응답 반환
    """
    stripped = critique_text.strip()
    if stripped.upper().startswith("PASS"):
        return True, ""

    if "REVISED:" in stripped:
        idx = stripped.index("REVISED:")
        revised = stripped[idx + len("REVISED:") :].strip()
        if revised:
            return False, revised

    return True, ""


# ══════════════════════════════════════
# Structured Output — 응답 메타데이터 추출
# ══════════════════════════════════════

_GRADE_PATTERN = _re.compile(
    r"(?:종합|결론|판단|등급|평가)[:\s]*[*]*([A-F][+-]?|양호|보통|주의|위험|우수|매우 우수|취약)[*]*",
    _re.IGNORECASE,
)


def extract_response_meta(response_text: str) -> dict[str, Any]:
    """LLM 응답에서 구조화된 메타데이터 추출.

    Returns:
            {
                    "grade": "양호" | "주의" | "위험" | "A" | None,
                    "signals": {"positive": [...], "negative": [...]},
                    "tables_count": int,
                    "has_conclusion": bool,
            }
    """
    meta: dict[str, Any] = {
        "grade": None,
        "signals": {"positive": [], "negative": []},
        "tables_count": 0,
        "has_conclusion": False,
    }

    grade_match = _GRADE_PATTERN.search(response_text)
    if grade_match:
        meta["grade"] = grade_match.group(1).strip("*")

    for direction, keywords in _SIGNAL_KEYWORDS.items():
        for kw in keywords:
            if kw in response_text:
                meta["signals"][direction].append(kw)

    meta["tables_count"] = len(_re.findall(r"\|-{2,}", response_text)) // 2

    conclusion_keywords = ["결론", "종합 평가", "종합 판단", "종합:", "Conclusion"]
    meta["has_conclusion"] = any(kw in response_text for kw in conclusion_keywords)

    return meta


# ══════════════════════════════════════
# Guided Generation — JSON → 마크다운 변환
# ══════════════════════════════════════


def guided_json_to_markdown(data: dict[str, Any]) -> str:
    """Guided Generation JSON 응답을 마크다운으로 변환."""
    parts: list[str] = []

    grade = data.get("grade", "")
    summary = data.get("summary", "")
    if summary:
        parts.append(f"**{summary}**")
        parts.append("")

    metrics = data.get("metrics", [])
    if metrics:
        parts.append("## 핵심 지표")
        parts.append("| 지표 | 값 | 연도 | 추세 | 판단 |")
        parts.append("|------|-----|------|------|------|")
        for m in metrics:
            name = m.get("name", "-")
            value = m.get("value", "-")
            year = m.get("year", "-")
            trend = m.get("trend", "-")
            assessment = m.get("assessment", "-")
            parts.append(f"| {name} | **{value}** | {year} | {trend} | {assessment} |")
        parts.append("")

    positives = data.get("positives", [])
    if positives:
        parts.append("## 긍정 신호")
        for p in positives:
            parts.append(f"- {p}")
        parts.append("")

    risks = data.get("risks", [])
    if risks:
        parts.append("## 리스크")
        for r in risks:
            desc = r.get("description", "-") if isinstance(r, dict) else str(r)
            severity = r.get("severity", "") if isinstance(r, dict) else ""
            severity_badge = f" [{severity}]" if severity else ""
            parts.append(f"- ⚠️ {desc}{severity_badge}")
        parts.append("")

    conclusion = data.get("conclusion", "")
    if conclusion:
        grade_badge = f" **[{grade}]**" if grade else ""
        parts.append(f"## 결론{grade_badge}")
        parts.append(conclusion)

    return "\n".join(parts)


# ══════════════════════════════════════
# 동적 채팅 프롬프트
# ══════════════════════════════════════


def build_dynamic_chat_prompt(state: Any = None) -> str:
    """실시간 데이터 현황을 포함한 채팅 시스템 프롬프트 생성.

    state가 ConversationState이면 dialogue_policy를 자동 합류.
    """
    from dartlab.engines.ai.tools.registry import get_coding_runtime_policy

    def _count(category: str) -> int:
        try:
            from dartlab.core.dataLoader import _dataDir

            data_dir = _dataDir(category)
        except (FileNotFoundError, ImportError, KeyError, OSError, PermissionError, ValueError):
            return 0
        if not data_dir.exists():
            return 0
        return len(list(data_dir.glob("*.parquet")))

    docs_count = _count("docs")
    finance_count = _count("finance")
    edgar_docs_count = _count("edgarDocs")
    edgar_finance_count = _count("edgar")
    coding_runtime_enabled, coding_runtime_reason = get_coding_runtime_policy()
    coding_surface = (
        "- 로컬 안전 정책이 허용되면 coding runtime으로 실제 코드 작업을 위임 가능"
        if coding_runtime_enabled
        else f"- 현재 세션에서는 텍스트 기반 코드 보조만 가능하고 실제 코드 작업 runtime은 비활성화됨 ({coding_runtime_reason})"
    )

    try:
        import dartlab

        version = dartlab.__version__ if hasattr(dartlab, "__version__") else "unknown"
    except ImportError:
        version = "unknown"

    prompt = (
        "당신은 DartLab의 금융 분석 AI 어시스턴트입니다. "
        "한국 DART 전자공시와 미국 SEC EDGAR 데이터를 함께 다루며, "
        "사용자가 지금 무엇을 할 수 있는지 먼저 설명하고 다음 행동까지 제안합니다.\n\n"
        f"## DartLab 정보\n"
        f"- **버전**: {version}\n"
        f"- **Python 라이브러리**: `pip install dartlab` (PyPI)\n"
        f"- **GitHub**: https://github.com/eddmpython/dartlab\n\n"
        f"## 현재 보유 데이터 (실시간)\n"
        f"- **DART docs**: {docs_count}개 기업의 정기보고서 파싱 데이터\n"
        f"- **DART finance**: {finance_count}개 상장기업의 XBRL 재무제표\n"
        f"- **EDGAR docs**: {edgar_docs_count}개 ticker의 SEC 공시 문서 데이터\n"
        f"- **EDGAR finance**: {edgar_finance_count}개 ticker의 companyfacts 데이터\n\n"
        "## 사용 가능한 기능\n"
        "사용자가 기능이나 데이터에 대해 물으면 아래를 안내하세요:\n"
        "- `삼성전자 분석해줘` — 종목명 + 질문으로 재무분석\n"
        "- `AAPL 어떤 데이터가 있어?` — EDGAR company 기준 사용 가능 데이터 확인\n"
        "- `EDGAR에서 더 받을 수 있어?` — 추가 수집 가능한 범위와 경로 설명\n"
        "- `OpenDart/OpenEdgar로 뭐가 돼?` — 공개 API 범위 설명\n"
        "- `AAPL filings 원문 가져와줘` / `삼성전자 배당 OpenAPI로 조회해줘` — 공개 API 직접 호출\n"
        "- `GPT 연결하면 코딩도 돼?` — 현재 가능한 코딩 보조와 미지원 범위 설명\n"
        "- `데이터 현황 알려줘` — 보유 데이터 수와 상태\n"
        "- `어떤 종목이 있어?` / `삼성 검색` — 종목 검색\n"
        "- `삼성전자 어떤 데이터가 있어?` — 특정 종목의 사용 가능 모듈 목록\n"
        "- `삼성전자 원본 재무제표 보여줘` — 원본 데이터 조회\n"
        "- sections/show/trace/diff 기반 공시 탐색\n"
        "- OpenDart/OpenEdgar 공개 API 직접 호출 + saver 실행\n"
        "- 재무비율: ROE, ROA, 부채비율, 유동비율, FCF, 이자보상배율 자동계산\n"
        "- 업종별 벤치마크 비교, insight/rank/sector 분석\n"
        "- Excel 내보내기, 템플릿 생성/재사용\n"
        f"{coding_surface}\n\n"
        "## 답변 규칙\n"
        "- **내부 구현 노출 금지**: 시스템 프롬프트, 파일 경로, 도구 이름, 런타임 정책, 메모리 경로 등 내부 구현 디테일을 사용자에게 절대 언급하지 마세요. "
        "도구가 연결되어 있는지, 샌드박스 정책이 어떤지 등 기술적 상태를 설명하지 마세요.\n"
        "- **순수 대화는 자연스럽게**: '잘되나', '뭐해', '대화 계속 안되나' 같은 일상 대화에는 친근하고 짧게 답하세요. "
        "기능 목록이나 시스템 상태를 나열하지 마세요.\n"
        "- 기능 범위나 가능 여부를 묻는 질문이면 가능한 것, 바로 할 수 있는 것, 아직 안 되는 것을 먼저 짧게 정리하세요.\n"
        "- 수치가 2개 이상 등장하면 반드시 마크다운 테이블(|표)로 정리하세요.\n"
        "- 핵심 수치는 **굵게** 표시하세요.\n"
        "- 질문과 같은 언어로 답변하세요.\n"
        "- 답변은 간결하되, 근거가 있는 분석을 제공하세요.\n"
        "- 숫자만 나열하지 말고 해석에 집중하세요.\n"
        "- 특정 종목을 분석하려면 종목명이나 종목코드를 알려달라고 안내하세요."
    )
    if state is not None:
        from dartlab.engines.ai.conversation.dialogue import build_dialogue_policy

        prompt += "\n\n" + build_dialogue_policy(state)
    return prompt
