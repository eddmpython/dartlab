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
    REPORT_PROMPT as _REPORT_PROMPT,
)
from .templates.analysis_rules import (
    REPORT_PROMPT_COMPACT as _REPORT_PROMPT_COMPACT,
)
from .templates.analysis_rules import (
    TOPIC_COMPACT as _TOPIC_COMPACT,
)
from .templates.analysis_rules import (
    TOPIC_PROMPTS as _TOPIC_PROMPTS,
)

# ── 템플릿 데이터 임포트 ──────────────────────────────────
from .templates.analysisPhilosophy import (
    ANALYSIS_PHILOSOPHY_COMPACT as _PHILOSOPHY_COMPACT,
)
from .templates.analysisPhilosophy import (
    ANALYSIS_PHILOSOPHY_KR as _PHILOSOPHY_KR,
)
from .templates.benchmarks import _INDUSTRY_BENCHMARKS, _SECTOR_MAP
from .templates.self_critique import (
    SELF_CRITIQUE_PROMPT,
)
from .templates.self_critique import (
    SIGNAL_KEYWORDS as _SIGNAL_KEYWORDS,
)
from .templates.system_base import (
    EDGAR_SUPPLEMENT_EN,
    EDGAR_SUPPLEMENT_KR,
    SYSTEM_PROMPT_COMPACT,
    SYSTEM_PROMPT_EN,
    SYSTEM_PROMPT_KR,
)

# ── 플러그인 시스템 프롬프트 ──────────────────────────────────

_PLUGIN_SYSTEM_PROMPT = """
## 플러그인 확장 시스템
- dartlab은 플러그인으로 확장 가능합니다. `uv pip install dartlab-plugin-xxx` 한 줄로 새 데이터/도구/분석을 추가할 수 있습니다.
- 사용자가 "플러그인 만들어줘", "커스텀 분석 만들기", "ESG 플러그인" 같은 요청을 하면 `create_plugin` 도구를 사용하세요.
- `create_plugin`은 즉시 사용 가능한 완전한 패키지 구조(pyproject.toml + register 함수 + 로직 파일)를 자동 생성합니다.
- 분석 중 플러그인 추천 힌트가 제공되면, 답변 끝에 자연스럽게 안내하세요.
"""

# ── 도구 카탈로그 (자동 생성 파일에서 로드) ──────────────────────
try:
    from ._generatedCatalog import TOOL_CATALOG as _TOOL_CATALOG_FULL
except ImportError:
    _TOOL_CATALOG_FULL = (
        "## 보충 도구 사용 규칙\n"
        "- 분석 브리핑에 이미 포함된 수치는 도구를 재호출하지 마세요.\n"
        "- 브리핑에 없는 추가 정보(공시 원문, 실시간 주가, 웹 검색)만 도구로 조회하세요.\n"
        "- 도구 목록은 generateSpec.py 실행 후 자동 생성됩니다.\n"
    )

# company=None일 때 company 카테고리 도구 제거
_COMPANY_CATEGORIES = {"company", "finance", "analysis", "ui"}


def _filterCatalogForNoCompany(catalog: str) -> str:
    """company=None일 때 company 종속 도구 섹션 + 연쇄 패턴을 제거한다."""
    lines = catalog.split("\n")
    filtered: list[str] = []
    skip = False
    inChainSection = False
    for line in lines:
        # 도구 연쇄 패턴 섹션 제거 (company 도구 참조)
        if line.startswith("## 도구 연쇄 패턴"):
            inChainSection = True
            continue
        if inChainSection:
            if line.startswith("## "):
                inChainSection = False
            else:
                continue

        if line.startswith("### "):
            # category 확인: "### explore (priority: 95, category: company)"
            skip = False
            for cat in _COMPANY_CATEGORIES:
                if f"category: {cat}" in line:
                    skip = True
                    break
        if not skip:
            filtered.append(line)
    return "\n".join(filtered)


_TOOL_CATALOG = _TOOL_CATALOG_FULL
_TOOL_CATALOG_NO_COMPANY = _filterCatalogForNoCompany(_TOOL_CATALOG_FULL)

# ── 스킬 매칭 헬퍼 ──────────────────────────────────


def _matchSkillSafe(questionType: str | None, qTypes: list[str]) -> Any:
    """스킬 매칭 (import 실패 시 None)."""
    try:
        from dartlab.ai.skills.registry import matchSkill

        return matchSkill("", questionType=questionType or (qTypes[0] if qTypes else None))
    except (ImportError, OSError):
        return None


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
    report_mode: bool = False,
    market: str = "KR",
    allow_tools: bool = True,
) -> str:
    """시스템 프롬프트 조립 (단일 문자열 반환).

    Args:
            custom: 사용자 지정 프롬프트 (있으면 이것만 사용)
            lang: "ko" 또는 "en"
            included_modules: 컨텍스트에 포함된 모듈 목록 → 토픽 프롬프트 동적 추가
            sector: KRX 업종명 → 업종별 벤치마크 추가
            question_type: 단일 질문 유형 → Few-shot 예시 추가 (하위호환)
            question_types: 복수 질문 유형 → question_type보다 우선
            compact: True면 소형 모델용 간결 프롬프트 (Ollama)
            report_mode: True면 전문 분석보고서 구조 프롬프트 추가
            market: "KR" 또는 "US" — EDGAR 기업이면 US 보충 프롬프트 추가
    """
    static, dynamic = build_system_prompt_parts(
        custom=custom,
        lang=lang,
        included_modules=included_modules,
        sector=sector,
        question_type=question_type,
        question_types=question_types,
        compact=compact,
        report_mode=report_mode,
        market=market,
        allow_tools=allow_tools,
    )
    if dynamic:
        return static + "\n" + dynamic
    return static


def build_system_prompt_parts(
    custom: str | None = None,
    lang: str = "ko",
    included_modules: list[str] | None = None,
    sector: str | None = None,
    question_type: str | None = None,
    question_types: list[str] | None = None,
    compact: bool = False,
    report_mode: bool = False,
    market: str = "KR",
    allow_tools: bool = True,
    hasCompany: bool = True,
) -> tuple[str, str]:
    """시스템 프롬프트를 (정적, 동적) 2파트로 분리 반환.

    정적 부분: base + 벤치마크 + 토픽 + 교차검증 + Few-shot (캐시 대상)
    동적 부분: report_mode + 플러그인 (매 요청 변경 가능)

    Claude prompt caching의 cache_control breakpoint를 적용할 때
    정적 부분 끝에 마커를 삽입하면 캐시 히트율이 극대화된다.
    """
    if custom:
        return custom, ""

    q_types = question_types or ([question_type] if question_type else [])

    def _strip_tool_guidance(text: str) -> str:
        stripped = text
        if "## 공시 데이터 접근법 (도구 사용)" in stripped:
            stripped = _re.sub(
                r"\n## 공시 데이터 접근법 \(도구 사용\).*?(?=\n## 밸류에이션 분석 프레임워크|\Z)",
                "\n",
                stripped,
                flags=_re.DOTALL,
            )
            stripped = _re.sub(
                r"\n## 분석 시작 프로토콜.*?(?=\n## 데이터 관리 원칙|\Z)",
                "\n",
                stripped,
                flags=_re.DOTALL,
            )
        if "## 공시 도구" in stripped:
            stripped = _re.sub(
                r"\n## 공시 도구.*?(?=\n## 전문가 분석 필수|\Z)",
                "\n",
                stripped,
                flags=_re.DOTALL,
            )
            stripped = _re.sub(
                r"\n## 분석 시작 프로토콜.*?(?=\Z)",
                "\n",
                stripped,
                flags=_re.DOTALL,
            )
        return stripped

    # Code Execution: ```python 코드블록 자동 실행 안내
    _code_execution_guide = (
        "## 코드 실행\n"
        "```python 코드블록을 작성하면 자동 실행되고 결과가 피드백됩니다.\n"
        "\n"
        "**코드 작성 규칙**:\n"
        "- `import dartlab` 하나로 시작.\n"
        "- 어떤 API가 있는지 모르면 `dartlab.capabilities(search='키워드')`로 조회.\n"
        "- 결과는 반드시 `print()`로 출력 (stdout만 캡처됨).\n"
        "- DataFrame은 `print(df)` 또는 `print(df.to_pandas().to_markdown())`.\n"
        "- 실행 실패 시 에러를 읽고 수정 코드를 재생성하세요."
    )

    if compact:
        base = _strip_tool_guidance(SYSTEM_PROMPT_COMPACT) if not allow_tools else SYSTEM_PROMPT_COMPACT
        static_parts: list[str] = [_PHILOSOPHY_COMPACT]
        dynamic_parts: list[str] = []

        benchmark_key = _match_sector(sector) if sector else None
        if benchmark_key and benchmark_key in _INDUSTRY_BENCHMARKS:
            static_parts.append(_INDUSTRY_BENCHMARKS[benchmark_key])
        elif "일반" in _INDUSTRY_BENCHMARKS:
            static_parts.append(_INDUSTRY_BENCHMARKS["일반"])

        if included_modules:
            module_set = set(included_modules)
            for _tname, (trigger_modules, prompt_text) in _TOPIC_COMPACT.items():
                if module_set & trigger_modules:
                    static_parts.append(prompt_text)

        if included_modules:
            fs_modules = {"BS", "IS", "CF"}
            if fs_modules & set(included_modules):
                static_parts.append(_CROSS_VALIDATION_COMPACT)

        for qt in q_types[:1]:
            if qt in _FEW_SHOT_COMPACT:
                static_parts.append(_FEW_SHOT_COMPACT[qt])

        # 동적: skill + report_mode + 플러그인
        _skill = _matchSkillSafe(question_type, q_types)
        if _skill:
            dynamic_parts.append(_skill.toPrompt())

        if report_mode:
            dynamic_parts.append(_REPORT_PROMPT_COMPACT)

        # tool calling provider일 때만 도구 카탈로그 추가
        if allow_tools:
            static_parts.append(_code_execution_guide)
            static_parts.append(_TOOL_CATALOG if hasCompany else _TOOL_CATALOG_NO_COMPANY)

        dynamic_parts.append(
            "\n플러그인: 사용자가 '플러그인 만들어줘'하면 create_plugin 도구 사용. "
            "플러그인 추천 힌트가 있으면 답변 끝에 안내."
        )

        if market == "US":
            static_parts.append(EDGAR_SUPPLEMENT_KR)

        static = base + "\n".join(static_parts) if static_parts else base
        dynamic = "\n".join(dynamic_parts)
        return static, dynamic

    if lang == "ko":
        base = SYSTEM_PROMPT_KR
    else:
        base = SYSTEM_PROMPT_EN
    if not allow_tools:
        base = _strip_tool_guidance(base)
    static_parts = [_PHILOSOPHY_KR]
    dynamic_parts = []

    # 정적: 철학 + 벤치마크 + 토픽 + 교차검증 + Few-shot
    benchmark_key = _match_sector(sector) if sector else None
    if benchmark_key and benchmark_key in _INDUSTRY_BENCHMARKS:
        static_parts.append(_INDUSTRY_BENCHMARKS[benchmark_key])
    elif "일반" in _INDUSTRY_BENCHMARKS:
        static_parts.append(_INDUSTRY_BENCHMARKS["일반"])

    if included_modules:
        module_set = set(included_modules)
        for _topic_name, (trigger_modules, prompt_text) in _TOPIC_PROMPTS.items():
            if module_set & trigger_modules:
                static_parts.append(prompt_text)

    if included_modules:
        fs_modules = {"BS", "IS", "CF"}
        if fs_modules & set(included_modules):
            static_parts.append(_CROSS_VALIDATION_RULES)

    for qt in q_types[:2]:
        if qt in _FEW_SHOT_EXAMPLES:
            static_parts.append(_FEW_SHOT_EXAMPLES[qt])

    # EDGAR(US) 보충 프롬프트
    if market == "US":
        edgar_supp = EDGAR_SUPPLEMENT_EN if lang == "en" else EDGAR_SUPPLEMENT_KR
        static_parts.append(edgar_supp)

    # 동적: skill + report_mode + 플러그인
    _skill = _matchSkillSafe(question_type, q_types)
    if _skill:
        dynamic_parts.append(_skill.toPrompt())

    if report_mode:
        dynamic_parts.append(_REPORT_PROMPT)

    # 코드 실행 가이드 + 도구 카탈로그
    if allow_tools:
        static_parts.append(_code_execution_guide)
        static_parts.append(_TOOL_CATALOG if hasCompany else _TOOL_CATALOG_NO_COMPANY)

    dynamic_parts.append(_PLUGIN_SYSTEM_PROMPT)

    static = base + "\n".join(static_parts) if static_parts else base
    dynamic = "\n".join(dynamic_parts)
    return static, dynamic


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
    from dartlab.ai.tools.registry import get_coding_runtime_policy

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
        from dartlab.ai.conversation.dialogue import build_dialogue_policy

        prompt += "\n\n" + build_dialogue_policy(state)
    return prompt
