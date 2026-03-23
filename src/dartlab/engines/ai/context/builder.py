"""Company 데이터를 LLM context로 변환.

메타데이터 기반 컬럼 설명, 파생 지표 자동계산, 분석 힌트를 포함하여
LLM이 정확하게 분석할 수 있는 구조화된 마크다운 컨텍스트를 생성한다.

분할 모듈:
- formatting.py: DataFrame 마크다운 변환, 포맷팅, 파생 지표 계산
- finance_context.py: 재무/공시 데이터 → LLM 컨텍스트 마크다운 생성
"""

from __future__ import annotations

from typing import Any

import polars as pl

from dartlab.engines.ai.context.company_adapter import get_headline_ratios
from dartlab.engines.ai.context.finance_context import (
    _QUESTION_ACCOUNT_FILTER,
    _QUESTION_MODULES,  # noqa: F401 — re-export for tests
    _build_finance_engine_section,
    _build_ratios_section,
    _build_report_sections,
    _detect_year_hint,
    _get_quarter_counts,
    _resolve_module_data,
    detect_year_range,
    scan_available_modules,
)
from dartlab.engines.ai.context.formatting import (
    _compute_derived_metrics,
    _filter_key_accounts,
    _format_usd,
    _format_won,
    _get_sector,  # noqa: F401 — re-export for runtime/core.py
    df_to_markdown,
)
from dartlab.engines.ai.metadata import MODULE_META

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
    }
)
_ROUTE_HYBRID_KEYWORDS = frozenset({"종합", "전반", "전체", "비교"})
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


def _section_key_to_module_name(key: str) -> str:
    if key.startswith("report_"):
        return key.removeprefix("report_")
    if key.startswith("module_"):
        return key.removeprefix("module_")
    if key.startswith("section_"):
        return key.removeprefix("section_")
    return key


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

    q_set = set(q_types)
    for keyword in _ROUTE_REPORT_KEYWORDS:
        if keyword in question:
            return "report"

    if any(keyword in question for keyword in _ROUTE_SECTIONS_KEYWORDS):
        return "sections"

    if q_set & _ROUTE_SECTIONS_TYPES:
        return "sections"

    if q_set and q_set.issubset(_ROUTE_FINANCE_TYPES):
        return "finance"

    if any(keyword in question for keyword in _ROUTE_FINANCE_KEYWORDS):
        return "finance"

    if q_set and len(q_set) > 1:
        return "hybrid"

    if q_set & {"종합"}:
        return "hybrid"

    if any(keyword in question for keyword in _ROUTE_HYBRID_KEYWORDS):
        return "hybrid"

    return "finance" if q_set else "hybrid"


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

    def append(topic: str) -> None:
        if topic in _SECTIONS_ROUTE_EXCLUDE_TOPICS:
            return
        if topic in availableSet and topic not in selected:
            selected.append(topic)

    if include:
        for name in include:
            append(name)

    for name in _resolve_tables(question, None, exclude):
        append(name)

    for q_type in q_types:
        for topic in _SECTIONS_TYPE_DEFAULTS.get(q_type, []):
            append(topic)

    for keyword, topics in _SECTIONS_KEYWORD_TOPICS.items():
        if keyword in question:
            for topic in topics:
                append(topic)

    if not selected and availableTopics:
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

    result: dict[str, str] = {}
    for topic in topics:
        outline = sections.outline(topic) if hasattr(sections, "outline") else None
        if outline is None or not isinstance(outline, pl.DataFrame) or outline.is_empty():
            continue

        label_fn = getattr(company, "_topicLabel", None)
        label = label_fn(topic) if callable(label_fn) else topic
        lines = [f"\n## {label}"]
        lines.append(df_to_markdown(outline.head(6 if compact else 10), max_rows=6 if compact else 10, compact=True))

        if compact:
            if "preview" in outline.columns:
                previews = [
                    text.strip()
                    for text in outline["preview"].drop_nulls().to_list()
                    if isinstance(text, str) and text.strip()
                ]
                if previews:
                    lines.append("\n### 핵심 preview")
                    lines.extend(f"- {preview}" for preview in previews[:2])
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

    from dartlab.engines.ai.conversation.prompts import _classify_question_multi

    q_types = _classify_question_multi(question, max_types=2)
    route = _resolve_context_route(question, include=include, q_types=q_types)
    report_modules = _resolve_report_modules_for_question(question, include=include, exclude=exclude)

    acct_filters: dict[str, set[str]] = {}
    if compact:
        for qt in q_types:
            for sj, ids in _QUESTION_ACCOUNT_FILTER.get(qt, {}).items():
                acct_filters.setdefault(sj, set()).update(ids)

    if route in {"finance", "hybrid"}:
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

                for sj in ("IS", "BS", "CF"):
                    af = acct_filters.get(sj) if acct_filters else None
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

        ratios_section = _build_ratios_section(company, compact=compact, q_types=q_types or None)
        if ratios_section:
            modules_dict["ratios"] = ratios_section
            if "ratios" not in included:
                included.append("ratios")

    if route == "report":
        requested_report_modules = report_modules or ["dividend", "employee", "majorHolder", "executive", "audit"]
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

    has_docs = getattr(company, "_hasDocs", False)

    if has_docs and include:
        tables_requested = _resolve_tables(question, include, exclude)
        qualitative_tables = [t for t in tables_requested if t not in _FINANCIAL_ONLY]

        if exclude:
            qualitative_tables = [t for t in qualitative_tables if t not in exclude]

        for name in qualitative_tables:
            try:
                data = _resolve_module_data(company, name)
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

                section = _build_module_section(name, data, compact=compact)
                if not section:
                    continue
                modules_dict[name] = section
                if name not in included:
                    included.append(name)

            except _CONTEXT_ERRORS:
                continue

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
        if name in modules_dict:
            parts.append(modules_dict[name])
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
    from dartlab.engines.ai.context.formatting import _KEY_ACCOUNTS_MAP

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

    from dartlab.engines.ai.conversation.prompts import _classify_question_multi

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
                    "아래 데이터는 현재 포함되지 않았지만 `get_data` 도구로 조회할 수 있습니다:\n"
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
        from dartlab.engines.analysis.insight import analyze

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
    lines.append("깊이 분석이 필요하면 `show_topic(topic)`으로 원문을, `diff_topic(topic)`으로 상세 변화를 확인하세요.")
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
            f"전체 목록은 `list_topics` 도구로 조회하세요."
        )

    lines = [
        "\n## 조회 가능한 공시 topic 목록",
        "`show_topic` 도구에 아래 topic을 넣으면 상세 데이터를 조회할 수 있습니다.",
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
        from dartlab.engines.analysis.insight.pipeline import analyze

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

    # 분석 가이드
    if is_us:
        parts.extend(
            [
                "",
                "## DartLab Analysis Guide",
                "All filing data is structured as **sections** (topic × period horizontalization).",
                "- `list_topics()` → full topic list | `show_topic(topic)` → block index → `show_topic(topic, N)` → data",
                "- `get_evidence(topic)` → original filing text for citations",
                "- `diff_topic(topic)` → period-over-period changes | `trace_topic(topic)` → source provenance",
                "- `get_data(BS/IS/CF)` → financials | `compute_ratios()` → ratios",
                "- `get_insight()` → 7-area grades | `get_topic_coverage()` → data availability",
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
                "- `list_topics()` → 전체 topic 목록 (평균 120+개)",
                "- `show_topic(topic)` → 블록 목차 → `show_topic(topic, N)` → 실제 데이터",
                "- `get_evidence(topic)` → 원문 증거 검색 (인용용)",
                "- `diff_topic(topic)` → 기간간 변화 | `trace_topic(topic)` → 출처 추적",
                "- `get_data(BS/IS/CF)` → 재무제표 | `compute_ratios()` → 재무비율",
                "- `get_insight()` → 7영역 종합 등급 | `get_report_data(apiType)` → 정기보고서",
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
