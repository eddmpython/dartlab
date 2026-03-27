"""Company 데이터를 LLM context로 변환.

메타데이터 기반 컬럼 설명, 파생 지표 자동계산, 분석 힌트를 포함하여
LLM이 정확하게 분석할 수 있는 구조화된 마크다운 컨텍스트를 생성한다.

분할 모듈:
- formatting.py: DataFrame 마크다운 변환, 포맷팅, 파생 지표 계산
- finance_context.py: 재무/공시 데이터 → LLM 컨텍스트 마크다운 생성
"""

from __future__ import annotations

import re
from typing import Any

import polars as pl

from dartlab.ai.context.company_adapter import get_headline_ratios
from dartlab.ai.context.finance_context import (
    _QUESTION_ACCOUNT_FILTER,
    _QUESTION_MODULES,  # noqa: F401 — re-export for tests
    _build_finance_engine_section,
    _build_ratios_section,
    _build_report_sections,
    _buildQuarterlySection,
    _detect_year_hint,
    _get_quarter_counts,
    _resolve_module_data,
    _topic_name_set,
    detect_year_range,
    scan_available_modules,
)
from dartlab.ai.context.formatting import (
    _compute_derived_metrics,
    _filter_key_accounts,
    _format_usd,
    _format_won,
    _get_sector,  # noqa: F401 — re-export for runtime/core.py
    df_to_markdown,
)
from dartlab.ai.metadata import MODULE_META

_CONTEXT_ERRORS = (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError)

_ROUTE_FINANCE_TYPES = frozenset({"건전성", "수익성", "성장성", "자본"})
_ROUTE_SECTIONS_TYPES = frozenset({"사업", "리스크", "공시"})
_ROUTE_REPORT_KEYWORDS: dict[str, str] = {
    "배당": "dividend",
    "직원": "employee",
    "임원": "executive",
    "최대주주": "majorHolder",
    "주주": "majorHolder",
    "감사": "audit",
    "자기주식": "treasuryStock",
}
_ROUTE_SECTIONS_KEYWORDS = frozenset(
    {
        "공시",
        "사업",
        "리스크",
        "관계사",
        "지배구조",
        "근거",
        "변화",
        "최근 공시",
        "무슨 사업",
        "뭐하는",
        "어떤 회사",
        "ESG",
        "환경",
        "사회적 책임",
        "탄소",
        "기후",
        "공급망",
        "공급사",
        "고객 집중",
        "변화 감지",
        "무엇이 달라",
        "공시 변경",
    }
)
_ROUTE_HYBRID_KEYWORDS = frozenset({"종합", "전반", "전체", "비교", "밸류에이션", "적정 주가", "목표가", "DCF"})
_ROUTE_FINANCE_KEYWORDS = frozenset(
    {
        "재무",
        "영업이익",
        "영업이익률",
        "매출",
        "순이익",
        "실적",
        "현금흐름",
        "부채",
        "자산",
        "수익성",
        "건전성",
        "성장성",
        "이익률",
        "마진",
        "revenue",
        "profit",
        "margin",
        "cash flow",
        "cashflow",
        "debt",
        "asset",
    }
)
_ROUTE_REPORT_FINANCE_HINTS = frozenset(
    {
        "지속 가능",
        "지속가능",
        "지속성",
        "현금흐름",
        "현금",
        "실적",
        "영업이익",
        "순이익",
        "커버",
        "판단",
        "평가",
        "가능한지",
    }
)
_ROUTE_DISTRESS_KEYWORDS = frozenset(
    {
        "부실",
        "부실 징후",
        "위기 징후",
        "재무 위기",
        "유동성 위기",
        "자금 압박",
        "상환 부담",
        "이자보상",
        "존속 가능",
        "going concern",
        "distress",
    }
)
_SUMMARY_REQUEST_KEYWORDS = frozenset({"종합", "전반", "전체", "요약", "개괄", "한눈에"})
_QUARTERLY_HINTS = frozenset(
    {
        "분기",
        "분기별",
        "quarterly",
        "quarter",
        "Q1",
        "Q2",
        "Q3",
        "Q4",
        "1분기",
        "2분기",
        "3분기",
        "4분기",
        "반기",
        "반기별",
        "QoQ",
        "전분기",
    }
)


def _detectGranularity(question: str) -> str:
    """질문에서 시간 단위 감지: 'quarterly' | 'annual'."""
    if any(k in question for k in _QUARTERLY_HINTS):
        return "quarterly"
    return "annual"


_SECTIONS_TYPE_DEFAULTS: dict[str, list[str]] = {
    "사업": ["businessOverview", "productService", "salesOrder"],
    "리스크": ["riskDerivative", "contingentLiability", "internalControl"],
    "공시": ["disclosureChanges", "subsequentEvents", "otherReference"],
    "지배구조": ["governanceOverview", "boardOfDirectors", "holderOverview"],
}
_SECTIONS_KEYWORD_TOPICS: dict[str, list[str]] = {
    "관계사": ["affiliateGroupDetail", "subsidiaryDetail", "investedCompany"],
    "지배구조": ["governanceOverview", "boardOfDirectors", "holderOverview"],
    "무슨 사업": ["businessOverview", "productService"],
    "뭐하는": ["businessOverview", "productService"],
    "어떤 회사": ["businessOverview", "companyHistory"],
    "최근 공시": ["disclosureChanges", "subsequentEvents"],
    "변화": ["disclosureChanges", "businessStatus"],
    "ESG": ["governanceOverview", "boardOfDirectors"],
    "환경": ["businessOverview"],
    "공급망": ["segments", "rawMaterial"],
    "공급사": ["segments", "rawMaterial"],
    "변화 감지": ["disclosureChanges", "businessStatus"],
}
_FINANCIAL_ONLY = {"BS", "IS", "CF", "fsSummary", "ratios"}
_SECTIONS_ROUTE_EXCLUDE_TOPICS = {
    "fsSummary",
    "financialStatements",
    "financialNotes",
    "consolidatedStatements",
    "consolidatedNotes",
    "dividend",
    "employee",
    "majorHolder",
    "audit",
}
_FINANCE_STATEMENT_MODULES = frozenset({"BS", "IS", "CF", "CIS", "SCE"})
_FINANCE_CONTEXT_MODULES = _FINANCE_STATEMENT_MODULES | {"ratios"}
_BALANCE_SHEET_HINTS = frozenset({"부채", "자산", "유동", "차입", "자본", "레버리지", "건전성", "안전"})
_CASHFLOW_HINTS = frozenset({"현금흐름", "현금", "fcf", "자금", "커버", "배당지급", "지속 가능", "지속가능"})
_INCOME_STATEMENT_HINTS = frozenset(
    {"매출", "영업이익", "순이익", "수익", "마진", "이익률", "실적", "원가", "비용", "판관비"}
)
_RATIO_HINTS = frozenset({"비율", "마진", "이익률", "수익성", "건전성", "성장성", "안정성", "지속 가능", "지속가능"})
_DIRECT_HINT_MAP: dict[str, list[str]] = {
    "성격별 비용": ["costByNature"],
    "비용의 성격": ["costByNature"],
    "인건비": ["costByNature"],
    "감가상각": ["costByNature"],
    "광고선전비": ["costByNature"],
    "판매촉진비": ["costByNature"],
    "지급수수료": ["costByNature"],
    "운반비": ["costByNature"],
    "물류비": ["costByNature"],
    "연구개발": ["rnd"],
    "r&d": ["rnd"],
    "세그먼트": ["segments"],
    "부문정보": ["segments"],
    "사업부문": ["segments"],
    "부문별": ["segments"],
    "제품별": ["productService"],
    "서비스별": ["productService"],
}
_CANDIDATE_ALIASES = {
    "segment": "segments",
    "operationalAsset": "tangibleAsset",
}
_MARGIN_DRIVER_MARGIN_HINTS = frozenset({"영업이익률", "마진", "이익률", "margin"})
_MARGIN_DRIVER_COST_HINTS = frozenset({"비용 구조", "원가 구조", "비용", "원가", "판관비", "매출원가"})
_BUSINESS_CHANGE_HINTS = frozenset({"사업 변화", "사업변화", "사업 구조", "사업구조"})
_PERIOD_COLUMN_RE = re.compile(r"^\d{4}(?:Q[1-4])?$")


def _section_key_to_module_name(key: str) -> str:
    if key.startswith("report_"):
        return key.removeprefix("report_")
    if key.startswith("module_"):
        return key.removeprefix("module_")
    if key.startswith("section_"):
        return key.removeprefix("section_")
    return key


def _module_name_to_section_keys(name: str) -> list[str]:
    return [
        name,
        f"report_{name}",
        f"module_{name}",
        f"section_{name}",
    ]


def _build_module_section(name: str, data: Any, *, compact: bool, max_rows: int | None = None) -> str | None:
    meta = MODULE_META.get(name)
    label = meta.label if meta else name
    max_rows_value = max_rows or (8 if compact else 15)

    if isinstance(data, pl.DataFrame):
        if data.is_empty():
            return None
        md = df_to_markdown(data, max_rows=max_rows_value, meta=meta, compact=True)
        return f"\n## {label}\n{md}"

    if isinstance(data, dict):
        items = list(data.items())[:max_rows_value]
        lines = [f"\n## {label}"]
        lines.extend(f"- {k}: {v}" for k, v in items)
        return "\n".join(lines)

    if isinstance(data, list):
        max_items = min(meta.maxRows if meta else 10, 5 if compact else 10)
        lines = [f"\n## {label}"]
        for item in data[:max_items]:
            if hasattr(item, "title") and hasattr(item, "chars"):
                lines.append(f"- **{item.title}** ({item.chars}자)")
            else:
                lines.append(f"- {item}")
        if len(data) > max_items:
            lines.append(f"(... 상위 {max_items}건, 전체 {len(data)}건)")
        return "\n".join(lines)

    text = str(data).strip()
    if not text:
        return None
    max_text = 500 if compact else 1000
    return f"\n## {label}\n{text[:max_text]}"


def _resolve_context_route(
    question: str,
    *,
    include: list[str] | None,
    q_types: list[str],
) -> str:
    if include:
        return "hybrid"

    if _detectGranularity(question) == "quarterly":
        return "hybrid"

    if _has_margin_driver_pattern(question):
        return "hybrid"

    if _has_distress_pattern(question):
        return "finance"

    if _has_recent_disclosure_business_pattern(question):
        return "sections"

    question_lower = question.lower()
    q_set = set(q_types)
    has_report = any(keyword in question for keyword in _ROUTE_REPORT_KEYWORDS)
    has_sections = any(keyword in question for keyword in _ROUTE_SECTIONS_KEYWORDS) or bool(
        q_set & _ROUTE_SECTIONS_TYPES
    )
    has_finance_keyword = any(keyword in question_lower for keyword in _ROUTE_FINANCE_KEYWORDS)
    has_finance = has_finance_keyword or bool(q_set & _ROUTE_FINANCE_TYPES)
    has_report_finance_hint = any(keyword in question for keyword in _ROUTE_REPORT_FINANCE_HINTS)

    if has_report and (has_finance_keyword or has_sections or has_report_finance_hint):
        return "hybrid"

    for keyword in _ROUTE_REPORT_KEYWORDS:
        if keyword in question:
            return "report"

    if has_sections:
        return "sections"

    if q_set and q_set.issubset(_ROUTE_FINANCE_TYPES):
        return "finance"

    if has_finance:
        return "finance"

    if q_set and len(q_set) > 1:
        return "hybrid"

    if q_set & {"종합"}:
        return "hybrid"

    if any(keyword in question for keyword in _ROUTE_HYBRID_KEYWORDS):
        return "hybrid"

    return "finance" if q_set else "hybrid"


def _append_unique(items: list[str], value: str | None) -> None:
    if value and value not in items:
        items.append(value)


def _normalize_candidate_module(name: str) -> str:
    return _CANDIDATE_ALIASES.get(name, name)


def _question_has_any(question: str, keywords: set[str] | frozenset[str]) -> bool:
    lowered = question.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _has_distress_pattern(question: str) -> bool:
    return _question_has_any(question, _ROUTE_DISTRESS_KEYWORDS)


def _has_margin_driver_pattern(question: str) -> bool:
    return (
        _question_has_any(question, _MARGIN_DRIVER_MARGIN_HINTS)
        and _question_has_any(question, _MARGIN_DRIVER_COST_HINTS)
        and _question_has_any(question, _BUSINESS_CHANGE_HINTS)
    )


def _has_recent_disclosure_business_pattern(question: str) -> bool:
    lowered = question.lower()
    return "최근 공시" in lowered and _question_has_any(question, _BUSINESS_CHANGE_HINTS)


def _resolve_direct_hint_modules(question: str) -> list[str]:
    selected: list[str] = []
    lowered = question.lower()
    for keyword, modules in _DIRECT_HINT_MAP.items():
        if keyword.lower() in lowered:
            for module_name in modules:
                _append_unique(selected, _normalize_candidate_module(module_name))
    return selected


def _apply_question_specific_boosts(question: str, selected: list[str]) -> None:
    if _has_distress_pattern(question):
        for module_name in ("BS", "IS", "CF", "ratios"):
            _append_unique(selected, module_name)

    if _has_margin_driver_pattern(question):
        for module_name in ("IS", "costByNature", "businessOverview", "productService"):
            _append_unique(selected, module_name)

    if _has_recent_disclosure_business_pattern(question):
        for module_name in ("businessOverview", "productService"):
            _append_unique(selected, module_name)


def _resolve_candidate_modules(
    question: str,
    *,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> list[str]:
    selected: list[str] = []

    if include:
        for name in include:
            _append_unique(selected, _normalize_candidate_module(name))
    else:
        for module_name in _resolve_direct_hint_modules(question):
            _append_unique(selected, module_name)

        for name in _resolve_tables(question, None, exclude):
            _append_unique(selected, _normalize_candidate_module(name))

    _apply_question_specific_boosts(question, selected)

    if exclude:
        excluded = {_normalize_candidate_module(name) for name in exclude}
        selected = [name for name in selected if name not in excluded]

    specific_modules = set(selected) - (_FINANCE_CONTEXT_MODULES | {"fsSummary"})
    if specific_modules and not _question_has_any(question, _SUMMARY_REQUEST_KEYWORDS):
        selected = [name for name in selected if name != "fsSummary"]

    return selected


def _available_sections_topics(company: Any) -> set[str]:
    docs = getattr(company, "docs", None)
    sections = getattr(docs, "sections", None)
    if sections is None:
        return set()

    manifest = sections.outline() if hasattr(sections, "outline") else None
    if isinstance(manifest, pl.DataFrame) and "topic" in manifest.columns:
        return {topic for topic in manifest["topic"].drop_nulls().to_list() if isinstance(topic, str) and topic}

    if hasattr(sections, "topics"):
        try:
            return {topic for topic in sections.topics() if isinstance(topic, str) and topic}
        except _CONTEXT_ERRORS:
            return set()
    return set()


def _available_report_modules(company: Any) -> set[str]:
    report = getattr(company, "report", None)
    if report is None:
        return set()

    for attr_name in ("availableApiTypes", "apiTypes"):
        try:
            values = getattr(report, attr_name, None)
        except _CONTEXT_ERRORS:
            values = None
        if isinstance(values, list):
            return {str(value) for value in values if isinstance(value, str) and value}
    return set()


def _available_notes_modules(company: Any) -> set[str]:
    notes = getattr(company, "notes", None)
    if notes is None:
        docs = getattr(company, "docs", None)
        notes = getattr(docs, "notes", None) if docs is not None else None
    if notes is None or not hasattr(notes, "keys"):
        return set()

    try:
        return {str(value) for value in notes.keys() if isinstance(value, str) and value}
    except _CONTEXT_ERRORS:
        return set()


def _resolve_candidate_plan(
    company: Any,
    question: str,
    *,
    route: str,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> dict[str, list[str]]:
    requested = _resolve_candidate_modules(question, include=include, exclude=exclude)
    sections_set = _available_sections_topics(company) if route in {"sections", "hybrid"} else set()
    report_set = _available_report_modules(company) if route in {"report", "hybrid"} else set()
    notes_set = _available_notes_modules(company) if route == "hybrid" else set()
    explicit_direct = set(_resolve_direct_hint_modules(question))
    boosted_direct: list[str] = []
    _apply_question_specific_boosts(question, boosted_direct)
    explicit_direct.update(name for name in boosted_direct if name not in _FINANCE_CONTEXT_MODULES)
    if include:
        explicit_direct.update(_normalize_candidate_module(name) for name in include)

    sections: list[str] = []
    report: list[str] = []
    finance: list[str] = []
    direct: list[str] = []
    verified: list[str] = []

    for name in requested:
        normalized = _normalize_candidate_module(name)
        if normalized in _FINANCE_CONTEXT_MODULES:
            if route in {"finance", "hybrid"}:
                _append_unique(finance, normalized)
                _append_unique(verified, normalized)
            continue
        if normalized in sections_set and normalized not in _SECTIONS_ROUTE_EXCLUDE_TOPICS:
            _append_unique(sections, normalized)
            _append_unique(verified, normalized)
            continue
        if normalized in report_set:
            _append_unique(report, normalized)
            _append_unique(verified, normalized)
            continue
        if normalized in notes_set and normalized in explicit_direct:
            _append_unique(direct, normalized)
            _append_unique(verified, normalized)
            continue

        if normalized in explicit_direct:
            data = _resolve_module_data(company, normalized)
            if data is not None:
                _append_unique(direct, normalized)
                _append_unique(verified, normalized)

    return {
        "requested": requested,
        "sections": sections,
        "report": report,
        "finance": finance,
        "direct": direct,
        "verified": verified,
    }


def _resolve_finance_modules_for_question(
    question: str,
    *,
    q_types: list[str],
    route: str,
    candidate_plan: dict[str, list[str]],
) -> list[str]:
    selected: list[str] = []
    finance_candidates = [name for name in candidate_plan.get("finance", []) if name in _FINANCE_STATEMENT_MODULES]

    if _has_margin_driver_pattern(question):
        _append_unique(selected, "IS")

    if route == "finance":
        if _question_has_any(question, _INCOME_STATEMENT_HINTS):
            _append_unique(selected, "IS")
        if _question_has_any(question, _BALANCE_SHEET_HINTS):
            _append_unique(selected, "BS")
        if _question_has_any(question, _CASHFLOW_HINTS):
            _append_unique(selected, "CF")
        if not selected:
            selected.extend(["IS", "BS", "CF"])
    elif route == "hybrid":
        has_finance_signal = bool(finance_candidates) and (
            _question_has_any(question, _BALANCE_SHEET_HINTS | _CASHFLOW_HINTS | _RATIO_HINTS)
            or bool(set(q_types) & _ROUTE_FINANCE_TYPES)
            or any(name in candidate_plan.get("report", []) for name in ("dividend", "shareCapital"))
        )
        if not has_finance_signal:
            return []

        for module_name in finance_candidates:
            _append_unique(selected, module_name)

        if not selected:
            if _question_has_any(question, _CASHFLOW_HINTS):
                selected.extend(["IS", "CF"])
            elif _question_has_any(question, _BALANCE_SHEET_HINTS):
                selected.extend(["IS", "BS"])
            else:
                selected.append("IS")

    if route == "finance" or _question_has_any(question, _RATIO_HINTS) or bool(set(q_types) & _ROUTE_FINANCE_TYPES):
        _append_unique(selected, "ratios")
    elif route == "hybrid" and {"dividend", "shareCapital"} & set(candidate_plan.get("report", [])):
        _append_unique(selected, "ratios")

    return selected


def _build_direct_module_context(
    company: Any,
    modules: list[str],
    *,
    compact: bool,
    question: str,
) -> dict[str, str]:
    result: dict[str, str] = {}
    for name in modules:
        try:
            data = _resolve_module_data(company, name)
        except _CONTEXT_ERRORS:
            data = None
        if data is None:
            continue
        if isinstance(data, pl.DataFrame):
            data = _trim_period_columns(data, question, compact=compact)
        section = _build_module_section(name, data, compact=compact)
        if section:
            result[name] = section
    return result


def _trim_period_columns(data: pl.DataFrame, question: str, *, compact: bool) -> pl.DataFrame:
    if data.is_empty():
        return data

    period_cols = [column for column in data.columns if isinstance(column, str) and _PERIOD_COLUMN_RE.fullmatch(column)]
    if len(period_cols) <= 1:
        return data

    def sort_key(value: str) -> tuple[int, int]:
        if "Q" in value:
            year, quarter = value.split("Q", 1)
            return int(year), int(quarter)
        return int(value), 9

    ordered_periods = sorted(period_cols, key=sort_key)
    keep_periods = _detect_year_hint(question)
    if compact:
        keep_periods = min(keep_periods, 5)
    else:
        keep_periods = min(keep_periods, 8)
    if len(ordered_periods) <= keep_periods:
        return data

    selected_periods = ordered_periods[-keep_periods:]
    base_columns = [column for column in data.columns if column not in period_cols]
    return data.select(base_columns + selected_periods)


def _build_response_contract(
    question: str,
    *,
    included_modules: list[str],
    route: str,
) -> str | None:
    lines = ["## 응답 계약", "- 아래 모듈은 이미 로컬 dartlab 데이터에서 확인되어 포함되었습니다."]
    lines.append(f"- 포함 모듈: {', '.join(included_modules)}")
    lines.append("- 포함된 모듈을 보고도 '데이터가 없다'고 말하지 마세요.")
    lines.append("- 핵심 결론 1~2문장을 먼저 제시하고, 바로 근거 표나 근거 bullet을 붙이세요.")
    lines.append(
        "- `explore()` 같은 도구 호출 계획이나 내부 절차 설명을 답변 본문에 쓰지 말고 바로 분석 결과를 말하세요."
    )
    lines.append(
        "- 답변 본문에서는 `IS/BS/CF/ratios/TTM/topic/period/source` 같은 내부 약어나 필드명을 그대로 쓰지 말고 "
        "`손익계산서/재무상태표/현금흐름표/재무비율/최근 4분기 합산/항목/시점/출처`처럼 사용자 언어로 바꾸세요."
    )
    lines.append(
        "- `costByNature`, `businessOverview`, `productService` 같은 내부 모듈명도 각각 "
        "`성격별 비용 분류`, `사업의 개요`, `제품·서비스`처럼 바꿔 쓰세요."
    )

    module_set = set(included_modules)
    if "costByNature" in module_set:
        lines.append("- `costByNature`가 있으면 상위 비용 항목 3~5개와 최근 기간 변화 방향을 먼저 요약하세요.")
        lines.append("- 기간이 명시되지 않아도 최신 시점과 최근 추세를 먼저 답하고, 연도 기준을 다시 묻지 마세요.")
    if "dividend" in module_set:
        lines.append("- `dividend`가 있으면 DPS·배당수익률·배당성향을 먼저 요약하세요.")
        lines.append(
            "- `dividend`가 있는데도 배당 데이터가 없다고 말하지 마세요. 첫 문장이나 첫 표에서 DPS와 배당수익률을 직접 인용하세요."
        )
    if {"dividend", "IS", "CF"} <= module_set or {"dividend", "CF"} <= module_set:
        lines.append("- `dividend`와 `IS/CF`가 같이 있으면 배당의 이익/현금흐름 커버 여부를 한 줄로 명시하세요.")
    if _has_distress_pattern(question):
        lines.append(
            "- `부실 징후` 질문이면 건전성 결론을 먼저 말하고, 수익성·현금흐름·차입 부담 순으로 짧게 정리하세요."
        )
    if route == "sections" or any(keyword in question for keyword in ("근거", "왜", "최근 공시 기준", "출처")):
        lines.append("- 근거 질문이면 `topic`, `period`, `source`를 최소 2개 명시하세요.")
        lines.append(
            "- `period`와 `source`는 outline 표에 나온 실제 값을 쓰세요. '최근 공시 기준' 같은 포괄 표현으로 뭉개지 마세요."
        )
        lines.append("- 본문에서는 `topic/period/source` 대신 `항목/시점/출처`처럼 자연어를 쓰세요.")
    hasQuarterly = any(m.endswith("_quarterly") for m in module_set)
    if hasQuarterly:
        lines.append("- **분기별 데이터가 포함되었습니다. '분기 데이터가 없다'고 절대 말하지 마세요.**")
        lines.append("- 분기별 추이를 테이블로 정리하고, 전분기 대비(QoQ)와 전년동기 대비(YoY) 변화를 함께 보여주세요.")
        lines.append(
            "- `IS_quarterly`, `CF_quarterly` 같은 내부명 대신 `분기별 손익계산서`, `분기별 현금흐름표`로 쓰세요."
        )

    # ── 도구 추천 힌트 ──
    hasFinancial = {"IS", "BS"} <= module_set or {"IS", "CF"} <= module_set
    if hasFinancial:
        lines.append(
            "- **추가 분석 추천**: `finance(action='ratios')`로 재무비율 확인, "
            "`explore(action='search', keyword='...')`로 변화 원인 파악."
        )
    elif not module_set & {"IS", "BS", "CF", "ratios"}:
        lines.append(
            "- **재무 데이터 미포함**: `finance(action='modules')`로 사용 가능 모듈 확인, "
            "`explore(action='topics')`로 topic 목록 확인 추천."
        )
    return "\n".join(lines)


def _build_clarification_context(
    company: Any,
    question: str,
    *,
    candidate_plan: dict[str, list[str]],
) -> str | None:
    if _has_margin_driver_pattern(question):
        return None

    lowered = question.lower()
    module_set = set(candidate_plan.get("verified", []))
    has_cost_by_nature = "costByNature" in module_set
    if not has_cost_by_nature and "costByNature" in set(candidate_plan.get("requested", [])):
        try:
            has_cost_by_nature = _resolve_module_data(company, "costByNature") is not None
        except _CONTEXT_ERRORS:
            has_cost_by_nature = False
    has_is = "IS" in module_set or "IS" in set(candidate_plan.get("requested", []))
    if not has_cost_by_nature or not has_is:
        return None
    if "비용" not in lowered:
        return None
    if any(keyword in lowered for keyword in ("성격", "인건비", "감가상각", "광고선전", "판관", "매출원가")):
        return None

    return (
        "## Clarification Needed\n"
        "- 현재 로컬에서 두 해석이 모두 가능합니다.\n"
        "- `costByNature`: 인건비·감가상각비 같은 성격별 비용 분류\n"
        "- `IS`: 매출원가·판관비 같은 기능별 비용 총액\n"
        "- 사용자의 의도가 둘 중 어느 쪽인지 결론을 바꾸므로, 먼저 한 문장으로 어느 관점을 원하는지 확인하세요.\n"
        "- 확인 질문은 한 문장만 하세요. 같은 문장을 반복하지 마세요."
    )


def _resolve_report_modules_for_question(
    question: str,
    *,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> list[str]:
    modules: list[str] = []

    for keyword, name in _ROUTE_REPORT_KEYWORDS.items():
        if keyword in question and name not in modules:
            modules.append(name)

    if include:
        for name in include:
            if (
                name in {"dividend", "employee", "majorHolder", "executive", "audit", "treasuryStock"}
                and name not in modules
            ):
                modules.append(name)

    if exclude:
        modules = [name for name in modules if name not in exclude]

    return modules


def _resolve_sections_topics(
    company: Any,
    question: str,
    *,
    q_types: list[str],
    candidates: list[str] | None = None,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    limit: int = 2,
) -> list[str]:
    docs = getattr(company, "docs", None)
    sections = getattr(docs, "sections", None)
    if sections is None:
        return []

    manifest = sections.outline() if hasattr(sections, "outline") else None
    available = (
        manifest["topic"].drop_nulls().to_list()
        if isinstance(manifest, pl.DataFrame) and "topic" in manifest.columns
        else sections.topics()
        if hasattr(sections, "topics")
        else []
    )
    availableTopics = [topic for topic in available if isinstance(topic, str) and topic]
    availableSet = set(availableTopics)
    if not availableSet:
        return []

    selected: list[str] = []
    isQuarterly = _detectGranularity(question) == "quarterly"

    def append(topic: str) -> None:
        if topic in _SECTIONS_ROUTE_EXCLUDE_TOPICS:
            if not (isQuarterly and topic == "fsSummary"):
                return
        if topic in availableSet and topic not in selected:
            selected.append(topic)

    if isQuarterly:
        append("fsSummary")

    if include:
        for name in include:
            append(name)

    if _has_recent_disclosure_business_pattern(question):
        append("disclosureChanges")
        append("businessOverview")

    candidate_source = _resolve_tables(question, None, exclude) if candidates is None else candidates
    for name in candidate_source:
        append(name)

    for q_type in q_types:
        for topic in _SECTIONS_TYPE_DEFAULTS.get(q_type, []):
            append(topic)

    for keyword, topics in _SECTIONS_KEYWORD_TOPICS.items():
        if keyword in question:
            for topic in topics:
                append(topic)

    if candidates is None and not selected and availableTopics:
        selected.append(availableTopics[0])

    return selected[:limit]


def _build_sections_context(
    company: Any,
    topics: list[str],
    *,
    compact: bool,
) -> dict[str, str]:
    docs = getattr(company, "docs", None)
    sections = getattr(docs, "sections", None)
    if sections is None:
        return {}

    try:
        context_slices = getattr(docs, "contextSlices", None) if docs is not None else None
    except _CONTEXT_ERRORS:
        context_slices = None

    result: dict[str, str] = {}
    for topic in topics:
        outline = sections.outline(topic) if hasattr(sections, "outline") else None
        if outline is None or not isinstance(outline, pl.DataFrame) or outline.is_empty():
            continue

        label_fn = getattr(company, "_topicLabel", None)
        label = label_fn(topic) if callable(label_fn) else topic
        lines = [f"\n## {label}"]
        lines.append(df_to_markdown(outline.head(6 if compact else 10), max_rows=6 if compact else 10, compact=True))

        topic_slices = _select_section_slices(context_slices, topic)
        if isinstance(topic_slices, pl.DataFrame) and not topic_slices.is_empty():
            lines.append("\n### 핵심 근거")
            for row in topic_slices.head(2 if compact else 4).iter_rows(named=True):
                period = row.get("period", "-")
                source_topic = row.get("sourceTopic") or row.get("topic") or topic
                block_type = "표" if row.get("isTable") or row.get("blockType") == "table" else "문장"
                slice_text = _truncate_section_slice(str(row.get("sliceText") or ""), compact=compact)
                if not slice_text:
                    continue
                lines.append(f"#### 시점: {period} | 출처: {source_topic} | 유형: {block_type}")
                lines.append(slice_text)

        if compact:
            if ("preview" in outline.columns) and not (
                isinstance(topic_slices, pl.DataFrame) and not topic_slices.is_empty()
            ):
                preview_lines: list[str] = []
                for row in outline.head(2).iter_rows(named=True):
                    preview = row.get("preview")
                    if not isinstance(preview, str) or not preview.strip():
                        continue
                    period = row.get("period", "-")
                    title = row.get("title", "-")
                    preview_lines.append(
                        f"- period: {period} | source: docs | title: {title} | preview: {preview.strip()}"
                    )
                if preview_lines:
                    lines.append("\n### 핵심 preview")
                    lines.extend(preview_lines)
            result[f"section_{topic}"] = "\n".join(lines)
            continue

        try:
            raw_sections = sections.raw if hasattr(sections, "raw") else None
        except _CONTEXT_ERRORS:
            raw_sections = None

        topic_rows = (
            raw_sections.filter(pl.col("topic") == topic)
            if isinstance(raw_sections, pl.DataFrame) and "topic" in raw_sections.columns
            else None
        )

        block_builder = getattr(company, "_buildBlockIndex", None)
        block_index = (
            block_builder(topic_rows) if callable(block_builder) and isinstance(topic_rows, pl.DataFrame) else None
        )

        if isinstance(block_index, pl.DataFrame) and not block_index.is_empty():
            lines.append("\n### block index")
            lines.append(
                df_to_markdown(block_index.head(4 if compact else 6), max_rows=4 if compact else 6, compact=True)
            )

            block_col = (
                "block"
                if "block" in block_index.columns
                else "blockOrder"
                if "blockOrder" in block_index.columns
                else None
            )
            type_col = (
                "type" if "type" in block_index.columns else "blockType" if "blockType" in block_index.columns else None
            )
            sample_block = None
            if block_col:
                for row in block_index.iter_rows(named=True):
                    block_no = row.get(block_col)
                    block_type = row.get(type_col)
                    if isinstance(block_no, int) and block_type in {"text", "table"}:
                        sample_block = block_no
                        break
            if sample_block is not None:
                show_section_block = getattr(company, "_showSectionBlock", None)
                block_data = (
                    show_section_block(topic_rows, block=sample_block)
                    if callable(show_section_block) and isinstance(topic_rows, pl.DataFrame)
                    else None
                )
                section = _build_module_section(topic, block_data, compact=compact, max_rows=4 if compact else 6)
                if section:
                    lines.append("\n### 대표 block")
                    lines.append(section.replace(f"\n## {label}", "", 1).strip())

        result[f"section_{topic}"] = "\n".join(lines)

    return result


def _build_changes_context(company: Any, *, compact: bool = True) -> str:
    """sections 변화 요약을 LLM 컨텍스트용 마크다운으로 변환.

    전체 sections(97MB) 대신 변화분(23%)만 요약하여 제공.
    LLM이 추가 도구 호출 없이 "무엇이 바뀌었는지" 즉시 파악 가능.
    """
    docs = getattr(company, "docs", None)
    sections = getattr(docs, "sections", None)
    if sections is None or not hasattr(sections, "changeSummary"):
        return ""

    try:
        summary = sections.changeSummary(topN=8 if compact else 15)
    except (AttributeError, TypeError, ValueError, pl.exceptions.PolarsError):
        return ""

    if summary is None or summary.is_empty():
        return ""

    lines = ["\n## 공시 변화 요약"]
    lines.append("| topic | 변화유형 | 건수 | 평균크기변화 |")
    lines.append("|-------|---------|------|------------|")
    for row in summary.iter_rows(named=True):
        topic = row.get("topic", "")
        changeType = row.get("changeType", "")
        count = row.get("count", 0)
        avgDelta = row.get("avgDelta", 0)
        sign = "+" if avgDelta and avgDelta > 0 else ""
        lines.append(f"| {topic} | {changeType} | {count} | {sign}{avgDelta} |")

    # 최근 기간 주요 변화 미리보기
    try:
        changes = sections.changes()
    except (AttributeError, TypeError, ValueError, pl.exceptions.PolarsError):
        changes = None

    if changes is not None and not changes.is_empty():
        # 가장 최근 기간 전환에서 structural/appeared 변화만 발췌
        latestPeriod = changes.get_column("toPeriod").max()
        recent = changes.filter(
            (pl.col("toPeriod") == latestPeriod) & pl.col("changeType").is_in(["structural", "appeared"])
        )
        if not recent.is_empty():
            lines.append(f"\n### 최근 주요 변화 ({latestPeriod})")
            for row in recent.head(5 if compact else 10).iter_rows(named=True):
                topic = row.get("topic", "")
                ct = row.get("changeType", "")
                preview = row.get("preview", "")
                if preview:
                    preview = preview[:120] + "..." if len(preview) > 120 else preview
                lines.append(f"- **{topic}** [{ct}]: {preview}")

    return "\n".join(lines)


def _select_section_slices(context_slices: Any, topic: str) -> pl.DataFrame | None:
    if not isinstance(context_slices, pl.DataFrame) or context_slices.is_empty():
        return None

    required_columns = {"topic", "periodOrder", "sliceText"}
    if not required_columns <= set(context_slices.columns):
        return None

    detail_col = pl.col("detailTopic") if "detailTopic" in context_slices.columns else pl.lit(None)
    semantic_col = pl.col("semanticTopic") if "semanticTopic" in context_slices.columns else pl.lit(None)
    block_priority_col = pl.col("blockPriority") if "blockPriority" in context_slices.columns else pl.lit(0)
    slice_idx_col = pl.col("sliceIdx") if "sliceIdx" in context_slices.columns else pl.lit(0)

    matched = context_slices.filter((pl.col("topic") == topic) | (detail_col == topic) | (semantic_col == topic))
    if matched.is_empty():
        return None

    return matched.with_columns(
        pl.when(detail_col == topic)
        .then(3)
        .when(semantic_col == topic)
        .then(2)
        .when(pl.col("topic") == topic)
        .then(1)
        .otherwise(0)
        .alias("matchPriority")
    ).sort(
        ["periodOrder", "matchPriority", "blockPriority", "sliceIdx"],
        descending=[True, True, True, False],
    )


def _truncate_section_slice(text: str, *, compact: bool) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    max_chars = 500 if compact else 1200
    if len(stripped) <= max_chars:
        return stripped
    return stripped[:max_chars].rstrip() + " ..."


def build_context_by_module(
    company: Any,
    question: str,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    compact: bool = False,
) -> tuple[dict[str, str], list[str], str]:
    """financeEngine 우선 compact 컨텍스트 빌더 (모듈별 분리).

    1차: financeEngine annual + ratios (빠르고 정규화된 수치)
    2차: docsParser 정성 데이터 (배당, 감사, 임원 등 — 질문에 맞는 것만)

    Args:
            compact: True면 소형 모델용으로 연도/행수 제한 (Ollama).

    Returns:
            (modules_dict, included_list, header_text)
            - modules_dict: {"IS": "## 손익계산서\n...", "BS": "...", ...}
            - included_list: ["IS", "BS", "CF", "ratios", ...]
            - header_text: 기업명 + 데이터 기준 라인
    """
    from dartlab import config

    orig_verbose = config.verbose
    config.verbose = False
    try:
        return _build_compact_context_modules_inner(company, question, include, exclude, compact, orig_verbose)
    finally:
        config.verbose = orig_verbose


def _build_compact_context_modules_inner(
    company: Any,
    question: str,
    include: list[str] | None,
    exclude: list[str] | None,
    compact: bool,
    orig_verbose: bool,
) -> tuple[dict[str, str], list[str], str]:
    n_years = _detect_year_hint(question)
    if compact:
        n_years = min(n_years, 4)
    modules_dict: dict[str, str] = {}
    included: list[str] = []

    header_parts = [f"# {company.corpName} ({company.stockCode})"]

    try:
        detail = getattr(company, "companyOverviewDetail", None)
        if detail and isinstance(detail, dict):
            info_parts = []
            if detail.get("ceo"):
                info_parts.append(f"대표: {detail['ceo']}")
            if detail.get("mainBusiness"):
                info_parts.append(f"주요사업: {detail['mainBusiness']}")
            if info_parts:
                header_parts.append("> " + " | ".join(info_parts))
    except _CONTEXT_ERRORS:
        pass

    from dartlab.ai.conversation.prompts import _classify_question_multi

    q_types = _classify_question_multi(question, max_types=2)
    route = _resolve_context_route(question, include=include, q_types=q_types)
    report_modules = _resolve_report_modules_for_question(question, include=include, exclude=exclude)
    candidate_plan = _resolve_candidate_plan(company, question, route=route, include=include, exclude=exclude)
    selected_finance_modules = _resolve_finance_modules_for_question(
        question,
        q_types=q_types,
        route=route,
        candidate_plan=candidate_plan,
    )

    acct_filters: dict[str, set[str]] = {}
    if compact:
        for qt in q_types:
            for sj, ids in _QUESTION_ACCOUNT_FILTER.get(qt, {}).items():
                acct_filters.setdefault(sj, set()).update(ids)

    statement_modules = [name for name in selected_finance_modules if name in _FINANCE_STATEMENT_MODULES]
    if statement_modules:
        annual = getattr(company, "annual", None)
        if annual is not None:
            series, years = annual
            quarter_counts = _get_quarter_counts(company)
            if years:
                yr_min = years[max(0, len(years) - n_years)]
                yr_max = years[-1]
                header = f"\n**데이터 기준: {yr_min}~{yr_max}년** (가장 최근: {yr_max}년, 금액: 억/조원)\n"

                partial = [y for y in years[-n_years:] if quarter_counts.get(y, 4) < 4]
                if partial:
                    notes = ", ".join(f"{y}년=Q1~Q{quarter_counts[y]}" for y in partial)
                    header += (
                        f"⚠️ **부분 연도 주의**: {notes} (해당 연도는 분기 누적이므로 전년 연간과 직접 비교 불가)\n"
                    )

                header_parts.append(header)

                for sj in statement_modules:
                    af = acct_filters.get(sj) if acct_filters and sj in {"IS", "BS", "CF"} else None
                    section = _build_finance_engine_section(
                        series,
                        years,
                        sj,
                        n_years,
                        af,
                        quarter_counts=quarter_counts,
                    )
                    if section:
                        modules_dict[sj] = section
                        included.append(sj)

        if _detectGranularity(question) == "quarterly" and statement_modules:
            ts = getattr(company, "timeseries", None)
            if ts is not None:
                tsSeries, tsPeriods = ts
                for sj in statement_modules:
                    if sj in {"IS", "CF"}:
                        af = acct_filters.get(sj) if acct_filters else None
                        qSection = _buildQuarterlySection(
                            tsSeries,
                            tsPeriods,
                            sj,
                            nQuarters=8,
                            accountFilter=af,
                        )
                        if qSection:
                            qKey = f"{sj}_quarterly"
                            modules_dict[qKey] = qSection
                            included.append(qKey)

        if "ratios" in selected_finance_modules:
            ratios_section = _build_ratios_section(company, compact=compact, q_types=q_types or None)
            if ratios_section:
                modules_dict["ratios"] = ratios_section
                if "ratios" not in included:
                    included.append("ratios")

    requested_report_modules = report_modules or candidate_plan.get("report", [])
    if route == "report":
        requested_report_modules = requested_report_modules or [
            "dividend",
            "employee",
            "majorHolder",
            "executive",
            "audit",
        ]
        report_sections = _build_report_sections(
            company,
            compact=compact,
            q_types=q_types,
            tier="focused" if compact else "full",
            report_names=requested_report_modules,
        )
        for key, section in report_sections.items():
            modules_dict[key] = section
            included_name = _section_key_to_module_name(key)
            if included_name not in included:
                included.append(included_name)

    if route == "hybrid" and requested_report_modules:
        report_sections = _build_report_sections(
            company,
            compact=compact,
            q_types=q_types,
            tier="focused" if compact else "full",
            report_names=requested_report_modules,
        )
        for key, section in report_sections.items():
            modules_dict[key] = section
            included_name = _section_key_to_module_name(key)
            if included_name not in included:
                included.append(included_name)

    if route in {"sections", "hybrid"}:
        topics = _resolve_sections_topics(
            company,
            question,
            q_types=q_types,
            candidates=candidate_plan.get("sections"),
            include=include,
            exclude=exclude,
            limit=1 if route == "hybrid" else 2,
        )
        sections_context = _build_sections_context(company, topics, compact=compact)
        for key, section in sections_context.items():
            modules_dict[key] = section
            included_name = _section_key_to_module_name(key)
            if included_name not in included:
                included.append(included_name)

    if route == "finance":
        _financeSectionsTopics = ["businessStatus", "businessOverview"]
        availableTopicSet = _topic_name_set(company)
        lightTopics = [t for t in _financeSectionsTopics if t in availableTopicSet]
        if lightTopics:
            lightContext = _build_sections_context(company, lightTopics[:1], compact=True)
            for key, section in lightContext.items():
                modules_dict[key] = section
                included_name = _section_key_to_module_name(key)
                if included_name not in included:
                    included.append(included_name)

    # 변화 컨텍스트 — sections 변화분만 LLM에 전달 (roundtrip 감소)
    if route in {"sections", "hybrid"}:
        changes_context = _build_changes_context(company, compact=compact)
        if changes_context:
            modules_dict["_changes"] = changes_context
            if "_changes" not in included:
                included.append("_changes")

    direct_sections = _build_direct_module_context(
        company,
        candidate_plan.get("direct", []),
        compact=compact,
        question=question,
    )
    for key, section in direct_sections.items():
        modules_dict[key] = section
        if key not in included:
            included.append(key)

    response_contract = _build_response_contract(question, included_modules=included, route=route)
    if response_contract:
        modules_dict["_response_contract"] = response_contract

    clarification_context = _build_clarification_context(company, question, candidate_plan=candidate_plan)
    if clarification_context:
        modules_dict["_clarify"] = clarification_context

    if not modules_dict:
        text, inc = build_context(company, question, include, exclude, compact=True)
        return {"_full": text}, inc, ""

    deduped_included: list[str] = []
    for name in included:
        if name not in deduped_included:
            deduped_included.append(name)

    return modules_dict, deduped_included, "\n".join(header_parts)


def build_compact_context(
    company: Any,
    question: str,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> tuple[str, list[str]]:
    """financeEngine 우선 compact 컨텍스트 빌더 (하위호환).

    build_context_by_module 결과를 단일 문자열로 합쳐 반환한다.
    """
    modules_dict, included, header = build_context_by_module(
        company,
        question,
        include,
        exclude,
        compact=True,
    )
    if "_full" in modules_dict:
        return modules_dict["_full"], included

    parts = [header] if header else []
    for name in included:
        for key in _module_name_to_section_keys(name):
            if key in modules_dict:
                parts.append(modules_dict[key])
                break
    return "\n".join(parts), included


# ══════════════════════════════════════
# 질문 키워드 → 자동 포함 데이터 매핑
# ══════════════════════════════════════

from dartlab.core.registry import buildKeywordMap

# registry aiKeywords 자동 역인덱스 (~55 모듈 키워드)
_KEYWORD_MAP = buildKeywordMap()

# 재무제표 직접 매핑 (registry 범위 밖 — BS/IS/CF 등 재무 코드)
_FINANCIAL_MAP: dict[str, list[str]] = {
    "재무": ["BS", "IS", "CF", "fsSummary", "costByNature"],
    "건전성": ["BS", "audit", "contingentLiability", "internalControl", "bond"],
    "수익": ["IS", "segments", "productService", "costByNature"],
    "실적": ["IS", "segments", "fsSummary", "productService", "salesOrder"],
    "매출": ["IS", "segments", "productService", "salesOrder"],
    "영업이익": ["IS", "fsSummary", "segments"],
    "순이익": ["IS", "fsSummary"],
    "현금": ["CF", "BS"],
    "자산": ["BS", "tangibleAsset", "investmentInOther"],
    "성장": ["IS", "CF", "productService", "salesOrder", "rnd"],
    "원가": ["costByNature", "IS"],
    "비용": ["costByNature", "IS"],
    "배당": ["dividend", "IS", "shareCapital"],
    "자본": ["BS", "capitalChange", "shareCapital", "fundraising"],
    "투자": ["CF", "rnd", "subsidiary", "investmentInOther", "tangibleAsset"],
    "부채": ["BS", "bond", "contingentLiability", "capitalChange"],
    "리스크": ["contingentLiability", "sanction", "riskDerivative", "audit", "internalControl"],
    "지배": ["majorHolder", "executive", "boardOfDirectors", "holderOverview"],
}

# 복합 분석 (여러 재무제표 조합)
_COMPOSITE_MAP: dict[str, list[str]] = {
    "ROE": ["IS", "BS", "fsSummary"],
    "ROA": ["IS", "BS", "fsSummary"],
    "PER": ["IS", "fsSummary", "dividend"],
    "PBR": ["BS", "fsSummary"],
    "EPS": ["IS", "fsSummary", "dividend"],
    "EBITDA": ["IS", "CF", "fsSummary"],
    "ESG": ["employee", "boardOfDirectors", "sanction", "internalControl"],
    "거버넌스": ["majorHolder", "executive", "boardOfDirectors", "audit"],
    "지배구조": ["majorHolder", "executive", "boardOfDirectors", "audit"],
    "인력현황": ["employee", "executivePay"],
    "주주환원": ["dividend", "shareCapital", "capitalChange"],
    "부채위험": ["BS", "bond", "contingentLiability"],
    "부채구조": ["BS", "bond", "contingentLiability"],
    "종합진단": ["BS", "IS", "CF", "fsSummary", "dividend", "majorHolder", "audit", "employee"],
    "스캔": ["BS", "IS", "dividend", "majorHolder", "audit", "employee"],
    "전반": ["BS", "IS", "CF", "fsSummary", "audit", "majorHolder"],
    "종합": ["BS", "IS", "CF", "fsSummary", "audit", "majorHolder"],
    # 영문
    "revenue": ["IS", "segments", "productService"],
    "profit": ["IS", "fsSummary"],
    "debt": ["BS", "bond", "contingentLiability"],
    "cash flow": ["CF"],
    "cashflow": ["CF"],
    "dividend": ["dividend", "IS", "shareCapital"],
    "growth": ["IS", "CF", "productService", "rnd"],
    "risk": ["contingentLiability", "sanction", "riskDerivative", "audit"],
    "audit": ["audit", "auditSystem", "internalControl"],
    "governance": ["majorHolder", "executive", "boardOfDirectors"],
    "employee": ["employee", "executivePay"],
    "subsidiary": ["subsidiary", "affiliateGroup", "investmentInOther"],
    "capex": ["CF", "tangibleAsset"],
    "operating": ["IS", "fsSummary", "segments"],
}

# 자연어 질문 패턴
_NATURAL_LANG_MAP: dict[str, list[str]] = {
    "돈": ["BS", "CF"],
    "벌": ["IS", "fsSummary"],
    "잘": ["IS", "fsSummary", "segments"],
    "위험": ["contingentLiability", "sanction", "riskDerivative", "audit", "internalControl"],
    "안전": ["BS", "audit", "contingentLiability", "internalControl"],
    "건강": ["BS", "IS", "CF", "audit"],
    "전망": ["IS", "CF", "rnd", "segments", "mdna"],
    "비교": ["IS", "BS", "CF", "fsSummary"],
    "추세": ["IS", "BS", "CF", "fsSummary"],
    "트렌드": ["IS", "BS", "CF", "fsSummary"],
    "분석": ["BS", "IS", "CF", "fsSummary"],
    "어떤 회사": ["companyOverviewDetail", "companyOverview", "business", "companyHistory"],
    "무슨 사업": ["business", "productService", "segments", "companyOverviewDetail"],
    "뭐하는": ["business", "productService", "segments", "companyOverviewDetail"],
    "어떤 사업": ["business", "productService", "segments", "companyOverviewDetail"],
}

# 병합: registry 키워드 → 재무제표 → 복합 → 자연어 (후순위가 오버라이드)
_TOPIC_MAP: dict[str, list[str]] = {**_KEYWORD_MAP, **_FINANCIAL_MAP, **_COMPOSITE_MAP, **_NATURAL_LANG_MAP}

# 항상 포함되는 기본 컨텍스트
_BASE_CONTEXT = ["fsSummary"]


# ══════════════════════════════════════
# 토픽 매핑
# ══════════════════════════════════════


def _resolve_tables(question: str, include: list[str] | None, exclude: list[str] | None) -> list[str]:
    """질문과 include/exclude로 포함할 테이블 목록 결정.

    개선: 대소문자 무시, 부분매칭, 복합 키워드 지원.
    """
    tables: list[str] = list(_BASE_CONTEXT)

    if include:
        tables.extend(include)
    else:
        q_lower = question.lower()
        matched_count = 0

        for keyword, table_names in _TOPIC_MAP.items():
            # 대소문자 무시 매칭
            if keyword.lower() in q_lower:
                matched_count += 1
                for t in table_names:
                    if t not in tables:
                        tables.append(t)

        # 매핑 안 됐으면 기본 재무제표 포함
        if matched_count == 0:
            tables.extend(["BS", "IS", "CF"])

        # 너무 많은 모듈이 매칭되면 상위 우선순위만 (토큰 절약)
        # 핵심 모듈(BS/IS/CF/fsSummary)은 항상 유지
        _CORE = {"fsSummary", "BS", "IS", "CF"}
        if len(tables) > 12:
            core = [t for t in tables if t in _CORE]
            non_core = [t for t in tables if t not in _CORE]
            tables = core + non_core[:8]

    if exclude:
        tables = [t for t in tables if t not in exclude]

    return tables


# ══════════════════════════════════════
# 컨텍스트 조립
# ══════════════════════════════════════


def build_context(
    company: Any,
    question: str,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    max_rows: int = 30,
    compact: bool = False,
) -> tuple[str, list[str]]:
    """질문과 Company 인스턴스로부터 LLM context 텍스트 조립.

    Args:
            compact: True면 핵심 계정만, 억/조 단위, 간결 포맷 (소형 모델용).

    Returns:
            (context_text, included_table_names)
    """
    from dartlab.ai.context.formatting import _KEY_ACCOUNTS_MAP

    tables_to_include = _resolve_tables(question, include, exclude)

    # fsSummary 중복 제거: BS+IS 둘 다 있으면 fsSummary 스킵
    if compact and "fsSummary" in tables_to_include:
        has_bs = "BS" in tables_to_include
        has_is = "IS" in tables_to_include
        if has_bs and has_is:
            tables_to_include = [t for t in tables_to_include if t != "fsSummary"]

    from dartlab import config

    orig_verbose = config.verbose
    config.verbose = False

    sections = []
    included = []

    sections.append(f"# {company.corpName} ({company.stockCode})")

    try:
        detail = getattr(company, "companyOverviewDetail", None)
        if detail and isinstance(detail, dict):
            info_parts = []
            if detail.get("ceo"):
                info_parts.append(f"대표: {detail['ceo']}")
            if detail.get("mainBusiness"):
                info_parts.append(f"주요사업: {detail['mainBusiness']}")
            if detail.get("foundedDate"):
                info_parts.append(f"설립: {detail['foundedDate']}")
            if info_parts:
                sections.append("> " + " | ".join(info_parts))
    except _CONTEXT_ERRORS:
        pass

    year_range = detect_year_range(company, tables_to_include)
    if year_range:
        sections.append(
            f"\n**데이터 기준: {year_range['min_year']}~{year_range['max_year']}년** (가장 최근: {year_range['max_year']}년)"
        )
        if not compact:
            sections.append("이후 데이터는 포함되어 있지 않습니다.\n")

    if compact:
        sections.append("\n금액: 억/조원 표시 (원본 백만원)\n")
    else:
        sections.append("")
        sections.append("모든 금액은 별도 표기 없으면 백만원(millions KRW) 단위입니다.")
        sections.append("")

    for name in tables_to_include:
        try:
            data = getattr(company, name, None)
            if data is None:
                continue

            if callable(data) and not isinstance(data, type):
                try:
                    result = data()
                    if hasattr(result, "FS") and isinstance(getattr(result, "FS", None), pl.DataFrame):
                        data = result.FS
                    elif isinstance(result, pl.DataFrame):
                        data = result
                    else:
                        data = result
                except _CONTEXT_ERRORS:
                    continue

            meta = MODULE_META.get(name)
            label = meta.label if meta else name
            desc = meta.description if meta else ""

            section_parts = [f"\n## {label}"]
            if not compact and desc:
                section_parts.append(desc)

            if isinstance(data, pl.DataFrame):
                display_df = data
                if compact and name in _KEY_ACCOUNTS_MAP:
                    display_df = _filter_key_accounts(data, name)

                md = df_to_markdown(display_df, max_rows=max_rows, meta=meta, compact=compact)
                section_parts.append(md)

                derived = _compute_derived_metrics(name, data, company)
                if derived:
                    section_parts.append(derived)

            elif isinstance(data, dict):
                dict_lines = []
                for k, v in data.items():
                    dict_lines.append(f"- {k}: {v}")
                section_parts.append("\n".join(dict_lines))

            elif isinstance(data, list):
                effective_max = meta.maxRows if meta else 20
                if compact:
                    effective_max = min(effective_max, 10)
                list_lines = []
                for item in data[:effective_max]:
                    if hasattr(item, "title") and hasattr(item, "chars"):
                        list_lines.append(f"- **{item.title}** ({item.chars}자)")
                    else:
                        list_lines.append(f"- {item}")
                if len(data) > effective_max:
                    list_lines.append(f"(... 상위 {effective_max}건, 전체 {len(data)}건)")
                section_parts.append("\n".join(list_lines))

            else:
                max_text = 1000 if compact else 2000
                section_parts.append(str(data)[:max_text])

            if not compact and meta and meta.analysisHints:
                hints = " | ".join(meta.analysisHints)
                section_parts.append(f"> 분석 포인트: {hints}")

            sections.append("\n".join(section_parts))
            included.append(name)

        except _CONTEXT_ERRORS:
            continue

    from dartlab.ai.conversation.prompts import _classify_question_multi

    _q_types = _classify_question_multi(question, max_types=2) if question else []
    report_sections = _build_report_sections(company, q_types=_q_types)
    for key, section in report_sections.items():
        sections.append(section)
        included.append(key)

    if not compact:
        available_modules = scan_available_modules(company)
        available_names = {m["name"] for m in available_modules}
        not_included = available_names - set(included)
        if not_included:
            available_list = []
            for m in available_modules:
                if m["name"] in not_included:
                    info = f"`{m['name']}` ({m['label']}"
                    if m.get("rows"):
                        info += f", {m['rows']}행"
                    info += ")"
                    available_list.append(info)
            if available_list:
                sections.append(
                    "\n---\n### 추가 조회 가능한 데이터\n"
                    "아래 데이터는 현재 포함되지 않았지만 `finance(action='data', module=...)` 도구로 조회할 수 있습니다:\n"
                    + ", ".join(available_list[:15])
                )

    # ── 정보 배치 최적화: 핵심 수치를 context 끝에 반복 (Lost-in-the-Middle 대응) ──
    key_facts = _build_key_facts_recap(company, included)
    if key_facts:
        sections.append(key_facts)

    config.verbose = orig_verbose

    return "\n".join(sections), included


def _build_key_facts_recap(company: Any, included: list[str]) -> str | None:
    """context 끝에 핵심 수치를 간결하게 반복 — Lost-in-the-Middle 문제 대응."""
    lines: list[str] = []

    ratios = get_headline_ratios(company)
    if ratios is not None and hasattr(ratios, "roe"):
        facts = []
        if ratios.roe is not None:
            facts.append(f"ROE {ratios.roe:.1f}%")
        if ratios.operatingMargin is not None:
            facts.append(f"영업이익률 {ratios.operatingMargin:.1f}%")
        if ratios.debtRatio is not None:
            facts.append(f"부채비율 {ratios.debtRatio:.1f}%")
        if ratios.currentRatio is not None:
            facts.append(f"유동비율 {ratios.currentRatio:.1f}%")
        if ratios.fcf is not None:
            facts.append(f"FCF {_format_won(ratios.fcf)}")
        if facts:
            lines.append("---")
            lines.append(f"**[핵심 지표 요약] {' | '.join(facts)}**")

    # insight 등급 요약 (있으면)
    try:
        from dartlab.analysis.financial.insight import analyze

        stockCode = getattr(company, "stockCode", None)
        if stockCode:
            result = analyze(stockCode, company=company)
            if result is not None:
                grades = result.grades()
                grade_parts = [f"{k}={v}" for k, v in grades.items() if v != "N"]
                if grade_parts:
                    lines.append(f"**[인사이트 등급] {result.profile} — {', '.join(grade_parts[:5])}**")
    except (ImportError, AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError):
        pass

    if not lines:
        return None
    return "\n".join(lines)


def _build_change_summary(company: Any, max_topics: int = 5) -> str | None:
    """기간간 변화가 큰 topic top-N을 자동 요약하여 AI 컨텍스트에 제공."""
    try:
        diff_df = company.diff()
    except _CONTEXT_ERRORS:
        return None

    if diff_df is None or (isinstance(diff_df, pl.DataFrame) and diff_df.is_empty()):
        return None

    if not isinstance(diff_df, pl.DataFrame):
        return None

    # changeRate > 0 인 topic만 필터, 상위 N개
    if "changeRate" not in diff_df.columns or "topic" not in diff_df.columns:
        return None

    changed = diff_df.filter(pl.col("changeRate") > 0).sort("changeRate", descending=True)
    if changed.is_empty():
        return None

    top = changed.head(max_topics)
    lines = [
        "\n## 주요 변화 (최근 공시 vs 직전)",
        "| topic | 변화율 | 기간수 |",
        "| --- | --- | --- |",
    ]
    for row in top.iter_rows(named=True):
        rate_pct = round(row["changeRate"] * 100, 1)
        periods = row.get("periods", "")
        lines.append(f"| `{row['topic']}` | {rate_pct}% | {periods} |")

    lines.append("")
    lines.append(
        "깊이 분석이 필요하면 `explore(action='show', topic=topic)`으로 원문을, `explore(action='diff', topic=topic)`으로 상세 변화를 확인하세요."
    )
    return "\n".join(lines)


def _build_topics_section(company: Any, compact: bool = False) -> str | None:
    """Company의 topics 목록을 LLM이 사용할 수 있는 마크다운으로 변환.

    dartlab에 topic이 추가되면 자동으로 LLM 컨텍스트에 포함된다.

    Args:
            compact: True면 상위 10개 + 총 개수 요약 (93% 토큰 절감)
    """
    topics = getattr(company, "topics", None)
    if topics is None:
        return None
    if isinstance(topics, pl.DataFrame):
        if "topic" not in topics.columns:
            return None
        topic_list = [topic for topic in topics["topic"].drop_nulls().to_list() if isinstance(topic, str) and topic]
    elif isinstance(topics, pl.Series):
        topic_list = [topic for topic in topics.drop_nulls().to_list() if isinstance(topic, str) and topic]
    elif isinstance(topics, list):
        topic_list = [topic for topic in topics if isinstance(topic, str) and topic]
    else:
        try:
            topic_list = [topic for topic in list(topics) if isinstance(topic, str) and topic]
        except TypeError:
            return None
    if not topic_list:
        return None

    if compact:
        top10 = topic_list[:10]
        return (
            f"\n## 공시 topic ({len(topic_list)}개)\n"
            f"주요: {', '.join(top10)}\n"
            f"전체 목록은 `explore(action='topics')` 도구로 조회하세요."
        )

    lines = [
        "\n## 조회 가능한 공시 topic 목록",
        "`explore(action='show', topic=...)` 도구에 아래 topic을 넣으면 상세 데이터를 조회할 수 있습니다.",
        "",
    ]

    # index가 있으면 label 정보 포함
    index_df = getattr(company, "index", None)
    if isinstance(index_df, pl.DataFrame) and index_df.height > 0:
        label_col = "label" if "label" in index_df.columns else None
        source_col = "source" if "source" in index_df.columns else None
        for row in index_df.head(60).iter_rows(named=True):
            topic = row.get("topic", "")
            label = row.get(label_col, topic) if label_col else topic
            source = row.get(source_col, "") if source_col else ""
            lines.append(f"- `{topic}` ({label}) [{source}]")
    else:
        for t in topic_list[:60]:
            lines.append(f"- `{t}`")

    return "\n".join(lines)


def _build_insights_section(company: Any) -> str | None:
    """Company의 7영역 인사이트 등급을 컨텍스트에 자동 포함."""
    stockCode = getattr(company, "stockCode", None)
    if not stockCode:
        return None

    try:
        from dartlab.analysis.financial.insight.pipeline import analyze

        result = analyze(stockCode, company=company)
    except (ImportError, AttributeError, FileNotFoundError, OSError, RuntimeError, TypeError, ValueError):
        return None
    if result is None:
        return None

    area_labels = {
        "performance": "실적",
        "profitability": "수익성",
        "health": "건전성",
        "cashflow": "현금흐름",
        "governance": "지배구조",
        "risk": "리스크",
        "opportunity": "기회",
    }

    lines = [
        "\n## 인사이트 등급 (자동 분석)",
        f"프로파일: **{result.profile}**",
        "",
        "| 영역 | 등급 | 요약 |",
        "| --- | --- | --- |",
    ]
    for key, label in area_labels.items():
        ir = getattr(result, key, None)
        grade = result.grades().get(key, "N")
        summary = ir.summary if ir else "-"
        lines.append(f"| {label} | {grade} | {summary} |")

    if result.anomalies:
        lines.append("")
        lines.append("### 이상치 경고")
        for a in result.anomalies[:5]:
            lines.append(f"- [{a.severity}] {a.text}")

    if result.summary:
        lines.append(f"\n{result.summary}")

    return "\n".join(lines)


# ══════════════════════════════════════
# Tiered Context Pipeline
# ══════════════════════════════════════

# skeleton tier에서 사용할 핵심 ratios 키
_SKELETON_RATIO_KEYS = ("roe", "debtRatio", "currentRatio", "operatingMargin", "fcf", "revenueGrowth3Y")

# skeleton tier에서 사용할 핵심 계정 (매출/영업이익/총자산)
_SKELETON_ACCOUNTS_KR: dict[str, list[tuple[str, str]]] = {
    "IS": [("sales", "매출액"), ("operating_profit", "영업이익")],
    "BS": [("total_assets", "자산총계")],
}
_SKELETON_ACCOUNTS_EN: dict[str, list[tuple[str, str]]] = {
    "IS": [("sales", "Revenue"), ("operating_profit", "Operating Income")],
    "BS": [("total_assets", "Total Assets")],
}


def build_context_skeleton(company: Any) -> tuple[str, list[str]]:
    """skeleton tier: ~500 토큰. tool calling provider용 최소 컨텍스트.

    핵심 비율 6개 + 매출/영업이익/총자산 3계정 + insight 등급 1줄.
    상세 데이터는 도구로 조회하도록 안내.
    EDGAR(US) / DART(KR) 자동 감지.
    """
    market = getattr(company, "market", "KR")
    is_us = market == "US"
    fmt_val = _format_usd if is_us else _format_won
    skel_accounts = _SKELETON_ACCOUNTS_EN if is_us else _SKELETON_ACCOUNTS_KR
    unit_label = "USD" if is_us else "억/조원"

    parts = [f"# {company.corpName} ({company.stockCode})"]
    if is_us:
        parts[0] += " | Market: US (SEC EDGAR) | Currency: USD"
    parts.append("⚠️ 아래는 참고용 요약입니다. 질문에 답하려면 반드시 도구(explore/finance)로 상세 데이터를 조회하세요.")
    included = []

    # 핵심 계정 3개 (최근 3년)
    annual = getattr(company, "annual", None)
    if annual is not None:
        series, years = annual
        quarter_counts = _get_quarter_counts(company)
        if years:
            display_years = years[-3:]
            display_labeled = []
            for y in display_years:
                qc = quarter_counts.get(y, 4)
                if qc < 4:
                    display_labeled.append(f"{y}(~Q{qc})")
                else:
                    display_labeled.append(y)
            display_reversed = list(reversed(display_labeled))
            year_offset = len(years) - 3

            col_header = "Account" if is_us else "계정"
            header = f"| {col_header} | " + " | ".join(display_reversed) + " |"
            sep = "| --- | " + " | ".join(["---"] * len(display_reversed)) + " |"
            rows = []
            for sj, accts in skel_accounts.items():
                sj_data = series.get(sj, {})
                for snake_id, label in accts:
                    vals = sj_data.get(snake_id)
                    if not vals:
                        continue
                    sliced = vals[max(0, year_offset) :]
                    cells = [fmt_val(v) if v is not None else "-" for v in reversed(sliced)]
                    rows.append(f"| {label} | " + " | ".join(cells) + " |")

            if rows:
                partial = [y for y in display_years if quarter_counts.get(y, 4) < 4]
                partial_note = ""
                if partial:
                    notes = ", ".join(f"{y}=Q1~Q{quarter_counts[y]}" for y in partial)
                    partial_note = f"\n⚠️ {'Partial year' if is_us else '부분 연도'}: {notes}"
                section_title = f"Key Financials ({unit_label})" if is_us else f"핵심 수치 ({unit_label})"
                parts.extend(["", f"## {section_title}{partial_note}", header, sep, *rows])
                included.extend(["IS", "BS"])

    # 핵심 비율 6개
    ratios = get_headline_ratios(company)
    if ratios is not None and hasattr(ratios, "roe"):
        ratio_lines = []
        for key in _SKELETON_RATIO_KEYS:
            val = getattr(ratios, key, None)
            if val is None:
                continue
            label_map_kr = {
                "roe": "ROE",
                "debtRatio": "부채비율",
                "currentRatio": "유동비율",
                "operatingMargin": "영업이익률",
                "fcf": "FCF",
                "revenueGrowth3Y": "매출3Y CAGR",
            }
            label_map_en = {
                "roe": "ROE",
                "debtRatio": "Debt Ratio",
                "currentRatio": "Current Ratio",
                "operatingMargin": "Op. Margin",
                "fcf": "FCF",
                "revenueGrowth3Y": "Rev. 3Y CAGR",
            }
            label = (label_map_en if is_us else label_map_kr).get(key, key)
            if key == "fcf":
                ratio_lines.append(f"- {label}: {fmt_val(val)}")
            else:
                ratio_lines.append(f"- {label}: {val:.1f}%")
        if ratio_lines:
            section_title = "Key Ratios" if is_us else "핵심 비율"
            parts.extend(["", f"## {section_title}", *ratio_lines])
            included.append("ratios")

    # 주요 공시 변화 (경량 — 상위 3개 topic)
    change_summary = _build_change_summary(company, max_topics=3)
    if change_summary:
        parts.append(change_summary)
        included.append("diff")

    # 분석 가이드
    if is_us:
        parts.extend(
            [
                "",
                "## DartLab Analysis Guide",
                "All filing data is structured as **sections** (topic × period horizontalization).",
                "- `explore(action='topics')` → full topic list | `explore(action='show', topic=...)` → block index → data",
                "- `explore(action='search', keyword=...)` → original filing text for citations",
                "- `explore(action='diff', topic=...)` → period-over-period changes | `explore(action='trace', topic=...)` → source provenance",
                "- `finance(action='data', module='BS/IS/CF')` → financials | `finance(action='ratios')` → ratios",
                "- `analyze(action='insight')` → 7-area grades | `explore(action='coverage')` → data availability",
                "",
                "**Note**: This is a US company (SEC EDGAR). No `report` namespace — all narrative data via sections.",
                "**Procedure**: Understand question → explore topics → retrieve data → cross-verify → synthesize answer",
            ]
        )
    else:
        parts.extend(
            [
                "",
                "## DartLab 분석 가이드",
                "이 기업의 모든 공시 데이터는 **sections** (topic × 기간 수평화)으로 구조화되어 있습니다.",
                "- `explore(action='topics')` → 전체 topic 목록 (평균 120+개)",
                "- `explore(action='show', topic=...)` → 블록 목차 → 실제 데이터",
                "- `explore(action='search', keyword=...)` → 원문 증거 검색 (인용용)",
                "- `explore(action='diff', topic=...)` → 기간간 변화 | `explore(action='trace', topic=...)` → 출처 추적",
                "- `finance(action='data', module='BS/IS/CF')` → 재무제표 | `finance(action='ratios')` → 재무비율",
                "- `analyze(action='insight')` → 7영역 종합 등급 | `explore(action='report', apiType=...)` → 정기보고서",
                "",
                "**분석 절차**: 질문 이해 → 관련 topic 탐색 → 원문 데이터 조회 → 교차 검증 → 종합 답변",
                "**핵심**: '데이터 없음'으로 답하기 전에 반드시 도구로 확인. sections에 거의 모든 공시 데이터가 있습니다.",
            ]
        )

    return "\n".join(parts), included


def build_context_focused(
    company: Any,
    question: str,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> tuple[dict[str, str], list[str], str]:
    """focused tier: ~2,000 토큰. tool calling 미지원 provider용.

    skeleton + 질문 유형별 관련 모듈만 포함 (compact 형식).
    """
    return build_context_by_module(company, question, include, exclude, compact=True)


ContextTier = str  # "skeleton" | "focused" | "full"


def build_context_tiered(
    company: Any,
    question: str,
    tier: ContextTier,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> tuple[dict[str, str], list[str], str]:
    """tier별 context 빌더. streaming.py에서 호출.

    Args:
        tier: "skeleton" | "focused" | "full"

    Returns:
        (modules_dict, included_list, header_text)
    """
    if tier == "skeleton":
        text, included = build_context_skeleton(company)
        return {"_skeleton": text}, included, ""
    elif tier == "focused":
        return build_context_focused(company, question, include, exclude)
    else:
        return build_context_by_module(company, question, include, exclude, compact=False)
