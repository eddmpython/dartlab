"""Finance/report 데이터를 LLM context 마크다운으로 변환하는 함수들."""

from __future__ import annotations

import re
from typing import Any

import polars as pl

from dartlab.engines.ai.context.company_adapter import get_headline_ratios, get_ratio_series
from dartlab.engines.ai.context.formatting import _format_won, df_to_markdown
from dartlab.engines.ai.metadata import MODULE_META

_CONTEXT_ERRORS = (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError)

# ══════════════════════════════════════
# 질문 유형별 모듈 매핑 (registry 자동 생성 + override)
# ══════════════════════════════════════

from dartlab.core.registry import buildQuestionModules

# registry에 없는 모듈(sections topic 전용 등)은 override로 추가
_QUESTION_MODULES_OVERRIDE: dict[str, list[str]] = {
    "공시": [],
    "배당": ["treasuryStock"],
    "자본": ["treasuryStock"],
    "사업": ["businessOverview"],
}

_QUESTION_MODULES: dict[str, list[str]] = {}
for _qt, _mods in buildQuestionModules().items():
    _QUESTION_MODULES[_qt] = list(_mods)
for _qt, _extra in _QUESTION_MODULES_OVERRIDE.items():
    _QUESTION_MODULES.setdefault(_qt, []).extend(m for m in _extra if m not in _QUESTION_MODULES.get(_qt, []))

_ALWAYS_INCLUDE_MODULES = {"employee"}

_CONTEXT_MODULE_BUDGET = 6000  # 총 모듈 context 글자 수 상한 (focused tier 기본값)


def _resolve_context_budget(tier: str = "focused") -> int:
    """컨텍스트 tier별 모듈 예산."""
    return {
        "skeleton": 2000,  # tool-capable: 최소 맥락, 도구로 보충
        "focused": 6000,  # 현재 기본값
        "full": 12000,  # non-tool 모델: 최대한 포함
    }.get(tier, 6000)


def _topic_name_set(company: Any) -> set[str]:
    """Company.topics에서 실제 topic 이름만 안전하게 추출."""
    try:
        topics = getattr(company, "topics", None)
    except _CONTEXT_ERRORS:
        return set()

    if topics is None:
        return set()

    if isinstance(topics, pl.DataFrame):
        if "topic" not in topics.columns:
            return set()
        return {t for t in topics["topic"].drop_nulls().to_list() if isinstance(t, str) and t}

    if isinstance(topics, pl.Series):
        return {t for t in topics.drop_nulls().to_list() if isinstance(t, str) and t}

    try:
        return {str(t) for t in topics if isinstance(t, str) and t}
    except TypeError:
        return set()


def _resolve_module_data(company: Any, module_name: str) -> Any:
    """AI context용 모듈 해석.

    1. Company property/direct attr
    2. registry 기반 lazy parser (_get_primary)
    3. 실제 존재하는 topic에 한해 show()
    """
    data = getattr(company, module_name, None)
    if data is not None:
        return data

    get_primary = getattr(company, "_get_primary", None)
    if callable(get_primary):
        try:
            data = get_primary(module_name)
        except _CONTEXT_ERRORS:
            data = None
        except (FileNotFoundError, ImportError, IndexError):
            data = None
        if data is not None:
            return data

    if hasattr(company, "show") and module_name in _topic_name_set(company):
        try:
            return company.show(module_name)
        except _CONTEXT_ERRORS:
            return None

    return None


def _extract_module_context(company: Any, module_name: str, max_rows: int = 10) -> str | None:
    """registry 모듈 → 마크다운 요약. DataFrame/dict/list/text 모두 처리."""
    try:
        data = _resolve_module_data(company, module_name)
        if data is None:
            return None

        if callable(data) and not isinstance(data, type):
            try:
                data = data()
            except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError):
                return None

        meta = MODULE_META.get(module_name)
        label = meta.label if meta else module_name

        if isinstance(data, pl.DataFrame):
            if data.is_empty():
                return None
            md = df_to_markdown(data, max_rows=max_rows, meta=meta, compact=True)
            return f"## {label}\n{md}"

        if isinstance(data, dict):
            items = list(data.items())[:max_rows]
            lines = [f"## {label}"]
            for k, v in items:
                lines.append(f"- {k}: {v}")
            return "\n".join(lines)

        if isinstance(data, list):
            if not data:
                return None
            lines = [f"## {label}"]
            for item in data[:max_rows]:
                if hasattr(item, "title") and hasattr(item, "chars"):
                    lines.append(f"- **{item.title}** ({item.chars}자)")
                else:
                    lines.append(f"- {item}")
            if len(data) > max_rows:
                lines.append(f"(... 상위 {max_rows}건, 전체 {len(data)}건)")
            return "\n".join(lines)

        text = str(data)
        if len(text) > 300:
            text = text[:300] + f"... (전체 {len(str(data))}자, show_topic('{module_name}')으로 전문 확인)"
        return f"## {label}\n{text}" if text.strip() else None

    except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError):
        return None


def _build_report_sections(
    company: Any,
    compact: bool = False,
    q_types: list[str] | None = None,
    tier: str = "focused",
    report_names: list[str] | None = None,
) -> dict[str, str]:
    """reportEngine pivot 결과 + 질문 유형별 모듈 자동 주입 → LLM context 섹션 dict."""
    report = getattr(company, "report", None)
    sections: dict[str, str] = {}
    budget = _resolve_context_budget(tier)
    requested_reports = set(report_names or ["dividend", "employee", "majorHolder", "executive", "audit"])

    # 질문 유형별 추가 모듈 주입
    extra_modules: set[str] = set() if report_names is not None else set(_ALWAYS_INCLUDE_MODULES)
    if q_types and report_names is None:
        for qt in q_types:
            for mod in _QUESTION_MODULES.get(qt, []):
                extra_modules.add(mod)

    # 하드코딩된 기존 report 모듈들의 이름 (중복 방지용)
    _HARDCODED_REPORT = {"dividend", "employee", "majorHolder", "executive", "audit"}
    if report_names:
        for mod in report_names:
            if mod not in _HARDCODED_REPORT:
                extra_modules.add(mod)

    # 동적 모듈 주입 (하드코딩에 없는 것만)
    budget_used = 0
    for mod in sorted(extra_modules - _HARDCODED_REPORT):
        if budget_used >= budget:
            break
        content = _extract_module_context(company, mod, max_rows=8 if compact else 12)
        if content:
            budget_used += len(content)
            sections[f"module_{mod}"] = content

    if report is None:
        return sections

    max_years = 3 if compact else 99

    div = getattr(report, "dividend", None) if "dividend" in requested_reports else None
    if div is not None and div.years:
        display_years = div.years[-max_years:]
        offset = len(div.years) - len(display_years)
        lines = ["## 배당 시계열 (정기보고서)"]
        header = "| 연도 | " + " | ".join(str(y) for y in display_years) + " |"
        sep = "| --- | " + " | ".join(["---"] * len(display_years)) + " |"
        lines.append(header)
        lines.append(sep)

        def _fmtList(vals):
            return [str(round(v)) if v is not None else "-" for v in vals]

        lines.append("| DPS(원) | " + " | ".join(_fmtList(div.dps[offset:])) + " |")
        lines.append(
            "| 배당수익률(%) | "
            + " | ".join([f"{v:.2f}" if v is not None else "-" for v in div.dividendYield[offset:]])
            + " |"
        )
        latest_dps = div.dps[-1] if div.dps else None
        latest_yield = div.dividendYield[-1] if div.dividendYield else None
        if latest_dps is not None or latest_yield is not None:
            lines.append("")
            lines.append("### 배당 핵심 요약")
            if latest_dps is not None:
                lines.append(f"- 최근 연도 DPS: {int(round(latest_dps))}원")
            if latest_yield is not None:
                lines.append(f"- 최근 연도 배당수익률: {latest_yield:.2f}%")
            if len(display_years) >= 3:
                recent_dps = [
                    f"{year}:{int(round(value)) if value is not None else '-'}원"
                    for year, value in zip(display_years[-3:], div.dps[offset:][-3:], strict=False)
                ]
                lines.append("- 최근 3개년 DPS 추이: " + " → ".join(recent_dps))
        sections["report_dividend"] = "\n".join(lines)

    emp = getattr(report, "employee", None) if "employee" in requested_reports else None
    if emp is not None and emp.years:
        display_years = emp.years[-max_years:]
        offset = len(emp.years) - len(display_years)
        lines = ["## 직원현황 (정기보고서)"]
        header = "| 연도 | " + " | ".join(str(y) for y in display_years) + " |"
        sep = "| --- | " + " | ".join(["---"] * len(display_years)) + " |"
        lines.append(header)
        lines.append(sep)

        def _fmtEmp(vals):
            return [f"{int(v):,}" if v is not None else "-" for v in vals]

        def _fmtSalary(vals):
            return [f"{int(v):,}" if v is not None else "-" for v in vals]

        lines.append("| 총 직원수(명) | " + " | ".join(_fmtEmp(emp.totalEmployee[offset:])) + " |")
        lines.append("| 평균월급(천원) | " + " | ".join(_fmtSalary(emp.avgMonthlySalary[offset:])) + " |")
        sections["report_employee"] = "\n".join(lines)

    mh = getattr(report, "majorHolder", None) if "majorHolder" in requested_reports else None
    if mh is not None and mh.years:
        lines = ["## 최대주주 (정기보고서)"]
        if compact:
            latest_ratio = mh.totalShareRatio[-1] if mh.totalShareRatio else None
            ratio_str = f"{latest_ratio:.2f}%" if latest_ratio is not None else "-"
            lines.append(f"- {mh.years[-1]}년 합산 지분율: {ratio_str}")
        else:
            header = "| 연도 | " + " | ".join(str(y) for y in mh.years) + " |"
            sep = "| --- | " + " | ".join(["---"] * len(mh.years)) + " |"
            lines.append(header)
            lines.append(sep)
            lines.append(
                "| 합산 지분율(%) | "
                + " | ".join([f"{v:.2f}" if v is not None else "-" for v in mh.totalShareRatio])
                + " |"
            )

        if mh.latestHolders:
            holder_limit = 3 if compact else 5
            if not compact:
                lines.append("")
                lines.append(f"### 최근 주요주주 ({mh.years[-1]}년)")
            for h in mh.latestHolders[:holder_limit]:
                ratio = f"{h['ratio']:.2f}%" if h.get("ratio") is not None else "-"
                relate = f" ({h['relate']})" if h.get("relate") else ""
                lines.append(f"- {h['name']}{relate}: {ratio}")
        sections["report_majorHolder"] = "\n".join(lines)

    exe = getattr(report, "executive", None) if "executive" in requested_reports else None
    if exe is not None and exe.totalCount > 0:
        lines = [
            "## 임원현황 (정기보고서)",
            f"- 총 임원수: {exe.totalCount}명",
            f"- 사내이사: {exe.registeredCount}명",
            f"- 사외이사: {exe.outsideCount}명",
        ]
        sections["report_executive"] = "\n".join(lines)

    aud = getattr(report, "audit", None) if "audit" in requested_reports else None
    if aud is not None and aud.years:
        lines = ["## 감사의견 (정기보고서)"]
        display_aud = list(zip(aud.years, aud.opinions, aud.auditors))
        if compact:
            display_aud = display_aud[-2:]
        for y, opinion, auditor in display_aud:
            opinion = opinion or "-"
            auditor = auditor or "-"
            lines.append(f"- {y}년: {opinion} ({auditor})")
        sections["report_audit"] = "\n".join(lines)

    return sections


# ══════════════════════════════════════
# financeEngine 기반 컨텍스트 (1차 데이터 소스)
# ══════════════════════════════════════

_YEAR_HINT_KEYWORDS: dict[str, int] = {
    "최근": 3,
    "올해": 3,
    "작년": 3,
    "전년": 3,
    "추이": 5,
    "트렌드": 5,
    "추세": 5,
    "변화": 5,
    "성장": 5,
    "흐름": 5,
    "전체": 15,
    "역사": 15,
    "장기": 10,
}


def _detect_year_hint(question: str) -> int:
    """질문에서 필요한 연도 범위 추출."""
    year_match = re.search(r"(20\d{2})", question)
    if year_match:
        return 3

    for keyword, n in _YEAR_HINT_KEYWORDS.items():
        if keyword in question:
            return n

    return 5


_FE_DISPLAY_ACCOUNTS = {
    "BS": [
        ("total_assets", "자산총계"),
        ("current_assets", "유동자산"),
        ("noncurrent_assets", "비유동자산"),
        ("total_liabilities", "부채총계"),
        ("current_liabilities", "유동부채"),
        ("noncurrent_liabilities", "비유동부채"),
        ("owners_of_parent_equity", "자본총계"),
        ("cash_and_cash_equivalents", "현금성자산"),
        ("trade_and_other_receivables", "매출채권"),
        ("inventories", "재고자산"),
        ("tangible_assets", "유형자산"),
        ("intangible_assets", "무형자산"),
        ("shortterm_borrowings", "단기차입금"),
        ("longterm_borrowings", "장기차입금"),
    ],
    "IS": [
        ("sales", "매출액"),
        ("cost_of_sales", "매출원가"),
        ("gross_profit", "매출총이익"),
        ("selling_and_administrative_expenses", "판관비"),
        ("operating_profit", "영업이익"),
        ("finance_income", "금융수익"),
        ("finance_costs", "금융비용"),
        ("profit_before_tax", "법인세차감전이익"),
        ("income_taxes", "법인세비용"),
        ("net_profit", "당기순이익"),
    ],
    "CF": [
        ("operating_cashflow", "영업활동CF"),
        ("investing_cashflow", "투자활동CF"),
        ("cash_flows_from_financing_activities", "재무활동CF"),
        ("cash_and_cash_equivalents_end", "기말현금"),
    ],
}


# 한글 라벨 → snakeId 역매핑 (Phase 5 validation용)
ACCOUNT_LABEL_TO_SNAKE: dict[str, str] = {}
for _sj_accounts in _FE_DISPLAY_ACCOUNTS.values():
    for _snake_id, _label in _sj_accounts:
        ACCOUNT_LABEL_TO_SNAKE[_label] = _snake_id

_QUESTION_ACCOUNT_FILTER: dict[str, dict[str, set[str]]] = {
    "건전성": {
        "BS": {
            "total_assets",
            "total_liabilities",
            "owners_of_parent_equity",
            "current_assets",
            "current_liabilities",
            "cash_and_cash_equivalents",
            "shortterm_borrowings",
            "longterm_borrowings",
        },
        "IS": {"operating_profit", "finance_costs", "net_profit"},
        "CF": {"operating_cashflow", "investing_cashflow"},
    },
    "수익성": {
        "IS": {
            "sales",
            "cost_of_sales",
            "gross_profit",
            "selling_and_administrative_expenses",
            "operating_profit",
            "net_profit",
        },
        "BS": {"owners_of_parent_equity", "total_assets"},
    },
    "성장성": {
        "IS": {"sales", "operating_profit", "net_profit"},
        "CF": {"operating_cashflow"},
    },
    "배당": {
        "IS": {"net_profit"},
        "BS": {"owners_of_parent_equity"},
    },
    "현금": {
        "CF": {
            "operating_cashflow",
            "investing_cashflow",
            "cash_flows_from_financing_activities",
            "cash_and_cash_equivalents_end",
        },
        "BS": {"cash_and_cash_equivalents"},
    },
}


def _get_quarter_counts(company: Any) -> dict[str, int]:
    """company.timeseries periods에서 연도별 분기 수 계산."""
    ts = getattr(company, "timeseries", None)
    if ts is None:
        return {}
    _, periods = ts
    counts: dict[str, int] = {}
    for p in periods:
        year = p.split("-")[0] if "-" in p else p[:4]
        counts[year] = counts.get(year, 0) + 1
    return counts


def _build_finance_engine_section(
    series: dict,
    years: list[str],
    sj_div: str,
    n_years: int,
    account_filter: set[str] | None = None,
    quarter_counts: dict[str, int] | None = None,
) -> str | None:
    """financeEngine annual series → compact 마크다운 테이블.

    Args:
            account_filter: 이 set에 속한 snake_id만 표시. None이면 전체.
    """
    accounts = _FE_DISPLAY_ACCOUNTS.get(sj_div, [])
    if account_filter:
        accounts = [(sid, label) for sid, label in accounts if sid in account_filter]
    if not accounts:
        return None

    display_years = years[-n_years:]

    # 부분 연도 표시: IS/CF는 4분기 미만이면 "(~Q3)" 등 표시, BS는 시점잔액이므로 불필요
    display_years_labeled = []
    for y in display_years:
        qc = (quarter_counts or {}).get(y, 4)
        if sj_div != "BS" and qc < 4:
            display_years_labeled.append(f"{y}(~Q{qc})")
        else:
            display_years_labeled.append(y)
    display_years_reversed = list(reversed(display_years_labeled))

    # 최신 연도가 부분이면 YoY 비교 무의미
    latest_year = display_years[-1]
    latest_partial = sj_div != "BS" and (quarter_counts or {}).get(latest_year, 4) < 4

    sj_data = series.get(sj_div, {})
    if not sj_data:
        return None

    rows_data = []
    for snake_id, label in accounts:
        vals = sj_data.get(snake_id)
        if not vals:
            continue
        year_offset = len(years) - n_years
        sliced = vals[year_offset:] if year_offset >= 0 else vals
        has_data = any(v is not None for v in sliced)
        if has_data:
            rows_data.append((label, list(reversed(sliced))))

    if not rows_data:
        return None

    sj_labels = {"BS": "재무상태표", "IS": "손익계산서", "CF": "현금흐름표"}
    header = "| 계정 | " + " | ".join(display_years_reversed) + " | YoY |"
    sep = "| --- | " + " | ".join(["---"] * len(display_years_reversed)) + " | --- |"

    # 기간 메타데이터 명시
    sj_meta = {"BS": "시점 잔액", "IS": "기간 flow (standalone)", "CF": "기간 flow (standalone)"}
    meta_line = f"(단위: 억/조원 | {sj_meta.get(sj_div, 'standalone')})"
    if latest_partial:
        meta_line += f" ⚠️ {display_years_labeled[-1]}은 부분연도 — 연간 직접 비교 불가"

    lines = [f"## {sj_labels.get(sj_div, sj_div)}", meta_line, header, sep]
    for label, vals in rows_data:
        cells = []
        for v in vals:
            cells.append(_format_won(v) if v is not None else "-")
        # YoY: 부분 연도면 비교 불가
        if latest_partial:
            yoy_str = "-"
        else:
            yoy_str = _calc_yoy(vals[0], vals[1] if len(vals) > 1 else None)
        lines.append(f"| {label} | " + " | ".join(cells) + f" | {yoy_str} |")

    return "\n".join(lines)


def _calc_yoy(current: float | None, previous: float | None) -> str:
    """YoY 증감률 계산. 부호 전환 시 '-', |변동률|>50%면 ** 강조."""
    from dartlab.engines.common.finance.ratios import yoy_pct

    pct = yoy_pct(current, previous)
    if pct is None:
        return "-"
    sign = "+" if pct >= 0 else ""
    marker = "**" if abs(pct) > 50 else ""
    return f"{marker}{sign}{pct:.1f}%{marker}"


def _build_ratios_section(
    company: Any,
    compact: bool = False,
    q_types: list[str] | None = None,
) -> str | None:
    """financeEngine RatioResult → 마크다운 (질문 유형별 필터링).

    q_types가 주어지면 관련 비율 그룹만 노출하여 토큰 절약.
    None이면 전체 노출.
    """
    ratios = get_headline_ratios(company)
    if ratios is None:
        return None
    if not hasattr(ratios, "roe"):
        return None

    isFinancial = False
    sectorInfo = getattr(company, "sector", None)
    if sectorInfo is not None:
        try:
            from dartlab.engines.analysis.sector.types import Sector

            isFinancial = sectorInfo.sector == Sector.FINANCIALS
        except (ImportError, AttributeError):
            isFinancial = False

    # ── 판단 헬퍼 ──
    def _judge(val: float | None, good: float, caution: float) -> str:
        if val is None:
            return "-"
        return "양호" if val >= good else ("주의" if val >= caution else "위험")

    def _judge_inv(val: float | None, good: float, caution: float) -> str:
        if val is None:
            return "-"
        return "양호" if val <= good else ("주의" if val <= caution else "위험")

    # ── 질문 유형 → 노출 그룹 매핑 ──
    _Q_TYPE_TO_GROUPS: dict[str, list[str]] = {
        "건전성": ["수익성_core", "안정성", "현금흐름", "복합"],
        "수익성": ["수익성", "효율성", "복합"],
        "성장성": ["수익성_core", "성장"],
        "배당": ["수익성_core", "현금흐름"],
        "리스크": ["안정성", "현금흐름", "복합"],
        "투자": ["수익성_core", "성장", "현금흐름"],
        "종합": ["수익성", "안정성", "성장", "효율성", "현금흐름", "복합"],
    }

    active_groups: set[str] = set()
    if q_types:
        for qt in q_types:
            active_groups.update(_Q_TYPE_TO_GROUPS.get(qt, []))
    if not active_groups:
        active_groups = {"수익성", "안정성", "성장", "효율성", "현금흐름", "복합"}

    # "수익성_core"는 수익성의 핵심만 (ROE, ROA, 영업이익률, 순이익률)
    show_profitability_full = "수익성" in active_groups
    show_profitability_core = show_profitability_full or "수익성_core" in active_groups

    roeGood, roeCaution = (8, 5) if isFinancial else (10, 5)
    roaGood, roaCaution = (0.5, 0.2) if isFinancial else (5, 2)

    lines = ["## 핵심 재무비율 (자동계산)"]

    # ── 수익성 ──
    if show_profitability_core:
        prof_rows: list[str] = []
        if ratios.roe is not None:
            prof_rows.append(f"| ROE | {ratios.roe:.1f}% | {_judge(ratios.roe, roeGood, roeCaution)} |")
        if ratios.roa is not None:
            prof_rows.append(f"| ROA | {ratios.roa:.1f}% | {_judge(ratios.roa, roaGood, roaCaution)} |")
        if ratios.operatingMargin is not None:
            prof_rows.append(f"| 영업이익률 | {ratios.operatingMargin:.1f}% | - |")
        if not compact and ratios.netMargin is not None:
            prof_rows.append(f"| 순이익률 | {ratios.netMargin:.1f}% | - |")
        if show_profitability_full:
            if ratios.grossMargin is not None:
                prof_rows.append(f"| 매출총이익률 | {ratios.grossMargin:.1f}% | - |")
            if ratios.ebitdaMargin is not None:
                prof_rows.append(f"| EBITDA마진 | {ratios.ebitdaMargin:.1f}% | - |")
            if not compact and ratios.roic is not None:
                prof_rows.append(f"| ROIC | {ratios.roic:.1f}% | {_judge(ratios.roic, 15, 8)} |")
        if prof_rows:
            lines.append("\n### 수익성")
            lines.append("| 지표 | 값 | 판단 |")
            lines.append("| --- | --- | --- |")
            lines.extend(prof_rows)

    # ── 안정성 ──
    if "안정성" in active_groups:
        stab_rows: list[str] = []
        if ratios.debtRatio is not None:
            stab_rows.append(f"| 부채비율 | {ratios.debtRatio:.1f}% | {_judge_inv(ratios.debtRatio, 100, 200)} |")
        if ratios.currentRatio is not None:
            stab_rows.append(f"| 유동비율 | {ratios.currentRatio:.1f}% | {_judge(ratios.currentRatio, 150, 100)} |")
        if not compact and ratios.quickRatio is not None:
            stab_rows.append(f"| 당좌비율 | {ratios.quickRatio:.1f}% | {_judge(ratios.quickRatio, 100, 50)} |")
        if not compact and ratios.equityRatio is not None:
            stab_rows.append(f"| 자기자본비율 | {ratios.equityRatio:.1f}% | {_judge(ratios.equityRatio, 50, 30)} |")
        if ratios.interestCoverage is not None:
            stab_rows.append(
                f"| 이자보상배율 | {ratios.interestCoverage:.1f}x | {_judge(ratios.interestCoverage, 5, 1)} |"
            )
        if not compact and ratios.debtToEbitda is not None:
            stab_rows.append(f"| Debt/EBITDA | {ratios.debtToEbitda:.1f}x | {_judge_inv(ratios.debtToEbitda, 3, 5)} |")
        if not compact and ratios.netDebt is not None:
            stab_rows.append(
                f"| 순차입금 | {_format_won(ratios.netDebt)} | {'양호' if ratios.netDebt <= 0 else '주의'} |"
            )
        if not compact and ratios.netDebtRatio is not None:
            stab_rows.append(
                f"| 순차입금비율 | {ratios.netDebtRatio:.1f}% | {_judge_inv(ratios.netDebtRatio, 30, 80)} |"
            )
        if stab_rows:
            lines.append("\n### 안정성")
            lines.append("| 지표 | 값 | 판단 |")
            lines.append("| --- | --- | --- |")
            lines.extend(stab_rows)

    # ── 성장성 ──
    if "성장" in active_groups:
        grow_rows: list[str] = []
        if ratios.revenueGrowth is not None:
            grow_rows.append(f"| 매출성장률(YoY) | {ratios.revenueGrowth:.1f}% | - |")
        if ratios.operatingProfitGrowth is not None:
            grow_rows.append(f"| 영업이익성장률 | {ratios.operatingProfitGrowth:.1f}% | - |")
        if ratios.netProfitGrowth is not None:
            grow_rows.append(f"| 순이익성장률 | {ratios.netProfitGrowth:.1f}% | - |")
        if ratios.revenueGrowth3Y is not None:
            grow_rows.append(f"| 매출 3Y CAGR | {ratios.revenueGrowth3Y:.1f}% | - |")
        if not compact and ratios.assetGrowth is not None:
            grow_rows.append(f"| 자산성장률 | {ratios.assetGrowth:.1f}% | - |")
        if grow_rows:
            lines.append("\n### 성장성")
            lines.append("| 지표 | 값 | 판단 |")
            lines.append("| --- | --- | --- |")
            lines.extend(grow_rows)

    # ── 효율성 ──
    if "효율성" in active_groups and not compact:
        eff_rows: list[str] = []
        if ratios.totalAssetTurnover is not None:
            eff_rows.append(f"| 총자산회전율 | {ratios.totalAssetTurnover:.2f}x | - |")
        if ratios.inventoryTurnover is not None:
            eff_rows.append(f"| 재고자산회전율 | {ratios.inventoryTurnover:.1f}x | - |")
        if ratios.receivablesTurnover is not None:
            eff_rows.append(f"| 매출채권회전율 | {ratios.receivablesTurnover:.1f}x | - |")
        if eff_rows:
            lines.append("\n### 효율성")
            lines.append("| 지표 | 값 | 판단 |")
            lines.append("| --- | --- | --- |")
            lines.extend(eff_rows)

    # ── 현금흐름 ──
    if "현금흐름" in active_groups:
        cf_rows: list[str] = []
        if ratios.fcf is not None:
            cf_rows.append(f"| FCF | {_format_won(ratios.fcf)} | {'양호' if ratios.fcf > 0 else '주의'} |")
        if ratios.operatingCfToNetIncome is not None:
            quality = _judge(ratios.operatingCfToNetIncome, 100, 50)
            cf_rows.append(f"| 영업CF/순이익 | {ratios.operatingCfToNetIncome:.0f}% | {quality} |")
        if not compact and ratios.capexRatio is not None:
            cf_rows.append(f"| CAPEX비율 | {ratios.capexRatio:.1f}% | - |")
        if not compact and ratios.dividendPayoutRatio is not None:
            cf_rows.append(f"| 배당성향 | {ratios.dividendPayoutRatio:.1f}% | - |")
        if cf_rows:
            lines.append("\n### 현금흐름")
            lines.append("| 지표 | 값 | 판단 |")
            lines.append("| --- | --- | --- |")
            lines.extend(cf_rows)

    # ── 복합 지표 ──
    if "복합" in active_groups and not compact:
        comp_lines: list[str] = []

        # DuPont 분해
        dm = getattr(ratios, "dupontMargin", None)
        dt = getattr(ratios, "dupontTurnover", None)
        dl = getattr(ratios, "dupontLeverage", None)
        if dm is not None and dt is not None and dl is not None and ratios.roe is not None:
            # 주요 동인 판별
            if dm >= dt and dm >= dl:
                driver = "수익성 주도형"
            elif dt >= dm and dt >= dl:
                driver = "효율성 주도형"
            else:
                driver = "레버리지 주도형"
            comp_lines.append("\n### DuPont 분해")
            comp_lines.append(
                f"ROE {ratios.roe:.1f}% = 순이익률({dm:.1f}%) × 자산회전율({dt:.2f}x) × 레버리지({dl:.2f}x)"
            )
            comp_lines.append(f"→ **{driver}**")

        # Piotroski F-Score
        pf = getattr(ratios, "piotroskiFScore", None)
        if pf is not None:
            pf_label = "우수" if pf >= 7 else ("보통" if pf >= 4 else "취약")
            comp_lines.append("\n### 복합 재무 지표")
            comp_lines.append(f"- **Piotroski F-Score**: {pf}/9 ({pf_label}) — ≥7 우수, 4-6 보통, <4 취약")

        # Altman Z-Score
        az = getattr(ratios, "altmanZScore", None)
        if az is not None:
            az_label = "안전" if az > 2.99 else ("회색" if az >= 1.81 else "부실위험")
            if pf is None:
                comp_lines.append("\n### 복합 재무 지표")
            comp_lines.append(f"- **Altman Z-Score**: {az:.2f} ({az_label}) — >2.99 안전, 1.81-2.99 회색, <1.81 부실")

        # ROIC
        if ratios.roic is not None:
            roic_label = "우수" if ratios.roic >= 15 else ("적정" if ratios.roic >= 8 else "미흡")
            comp_lines.append(f"- **ROIC**: {ratios.roic:.1f}% ({roic_label})")

        # 이익의 질 — CCC
        ccc = getattr(ratios, "ccc", None)
        dso = getattr(ratios, "dso", None)
        dio = getattr(ratios, "dio", None)
        dpo = getattr(ratios, "dpo", None)
        cfni = ratios.operatingCfToNetIncome
        has_quality = ccc is not None or cfni is not None
        if has_quality:
            comp_lines.append("\n### 이익의 질")
            if cfni is not None:
                q = "양호" if cfni >= 100 else ("보통" if cfni >= 50 else "주의")
                comp_lines.append(f"- 영업CF/순이익: {cfni:.0f}% ({q}) — ≥100% 양호")
            if ccc is not None:
                ccc_parts = []
                if dso is not None:
                    ccc_parts.append(f"DSO:{dso:.0f}")
                if dio is not None:
                    ccc_parts.append(f"DIO:{dio:.0f}")
                if dpo is not None:
                    ccc_parts.append(f"DPO:{dpo:.0f}")
                detail = f" ({' + '.join(ccc_parts)})" if ccc_parts else ""
                comp_lines.append(f"- CCC(현금전환주기): {ccc:.0f}일{detail}")

        if comp_lines:
            lines.extend(comp_lines)

    # ── ratioSeries 3년 추세 ──
    ratio_series = get_ratio_series(company)
    if ratio_series is not None and hasattr(ratio_series, "roe") and ratio_series.roe:
        trend_keys = [("roe", "ROE"), ("operatingMargin", "영업이익률"), ("debtRatio", "부채비율")]
        if not compact and "성장" in active_groups:
            trend_keys.append(("revenueGrowth", "매출성장률"))
        trend_lines: list[str] = []
        for key, label in trend_keys:
            series_vals = getattr(ratio_series, key, None)
            if series_vals and len(series_vals) >= 2:
                recent = [f"{v:.1f}%" for v in series_vals[-3:] if v is not None]
                if recent:
                    arrow = (
                        "↗" if series_vals[-1] > series_vals[-2] else "↘" if series_vals[-1] < series_vals[-2] else "→"
                    )
                    trend_lines.append(f"- {label}: {' → '.join(recent)} {arrow}")
        if trend_lines:
            lines.append("")
            lines.append("### 추세 (최근 3년)")
            lines.extend(trend_lines)

    # ── TTM ──
    ttm_lines: list[str] = []
    if ratios.revenueTTM is not None:
        ttm_lines.append(f"- TTM 매출: {_format_won(ratios.revenueTTM)}")
    if ratios.operatingIncomeTTM is not None:
        ttm_lines.append(f"- TTM 영업이익: {_format_won(ratios.operatingIncomeTTM)}")
    if ratios.netIncomeTTM is not None:
        ttm_lines.append(f"- TTM 순이익: {_format_won(ratios.netIncomeTTM)}")
    if ttm_lines:
        lines.append("")
        lines.append("### TTM (최근 4분기 합산)")
        lines.extend(ttm_lines)

    # ── 경고 ──
    if ratios.warnings:
        lines.append("")
        lines.append("### 경고")
        max_warnings = 2 if compact else len(ratios.warnings)
        for w in ratios.warnings[:max_warnings]:
            lines.append(f"- ⚠️ {w}")

    return "\n".join(lines)


def detect_year_range(company: Any, tables: list[str]) -> dict | None:
    """포함될 데이터의 연도 범위 감지."""
    all_years: set[int] = set()
    for name in tables:
        try:
            data = getattr(company, name, None)
            if data is None:
                continue
            if isinstance(data, pl.DataFrame):
                if "year" in data.columns:
                    years = data["year"].unique().to_list()
                    all_years.update(int(y) for y in years if y)
                else:
                    year_cols = [c for c in data.columns if c.isdigit() and len(c) == 4]
                    all_years.update(int(c) for c in year_cols)
        except _CONTEXT_ERRORS:
            continue
    if not all_years:
        return None
    sorted_years = sorted(all_years)
    return {"min_year": sorted_years[0], "max_year": sorted_years[-1]}


def scan_available_modules(company: Any) -> list[dict[str, str]]:
    """Company 인스턴스에서 실제 데이터가 있는 모듈 목록을 반환.

    Returns:
            [{"name": "BS", "label": "재무상태표", "type": "DataFrame", "rows": 25}, ...]
    """
    available = []
    for name, meta in MODULE_META.items():
        try:
            data = getattr(company, name, None)
            if data is None:
                continue
            # method인 경우 건너뜀 (fsSummary 등은 호출 비용이 큼)
            if callable(data) and not isinstance(data, type):
                info: dict[str, Any] = {"name": name, "label": meta.label, "type": "method"}
                available.append(info)
                continue
            if isinstance(data, pl.DataFrame):
                info = {
                    "name": name,
                    "label": meta.label,
                    "type": "table",
                    "rows": data.height,
                    "cols": len(data.columns),
                }
            elif isinstance(data, dict):
                info = {"name": name, "label": meta.label, "type": "dict", "rows": len(data)}
            elif isinstance(data, list):
                info = {"name": name, "label": meta.label, "type": "list", "rows": len(data)}
            else:
                info = {"name": name, "label": meta.label, "type": "text"}
            available.append(info)
        except _CONTEXT_ERRORS:
            continue
    return available
