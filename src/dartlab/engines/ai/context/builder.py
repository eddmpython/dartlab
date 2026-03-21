"""Company 데이터를 LLM context로 변환.

메타데이터 기반 컬럼 설명, 파생 지표 자동계산, 분석 힌트를 포함하여
LLM이 정확하게 분석할 수 있는 구조화된 마크다운 컨텍스트를 생성한다.
"""

from __future__ import annotations

import re
from typing import Any

import polars as pl

from dartlab.engines.ai.context.company_adapter import get_headline_ratios, get_ratio_series
from dartlab.engines.ai.metadata import MODULE_META, ModuleMeta

_CONTEXT_ERRORS = (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError)

# ══════════════════════════════════════
# reportEngine 기반 컨텍스트 (2차 데이터 소스)
# ══════════════════════════════════════


_QUESTION_MODULES: dict[str, list[str]] = {
    "건전성": ["audit", "internalControl", "contingentLiability", "relatedPartyTx"],
    "수익성": ["segments", "costByNature", "productService", "salesOrder"],
    "성장성": ["rnd", "salesOrder", "segments", "productService", "subsidiary"],
    "배당": ["dividend", "shareCapital", "capitalChange"],
    "지배구조": [
        "majorHolder",
        "executive",
        "executivePay",
        "boardOfDirectors",
        "auditSystem",
        "shareholderMeeting",
    ],
    "리스크": ["contingentLiability", "sanction", "riskDerivative", "relatedPartyTx",
              "riskFactor", "rawMaterial"],
    "투자": ["rnd", "tangibleAsset", "subsidiary", "affiliate", "fundraising"],
    "종합": ["dividend", "employee", "majorHolder", "audit", "rnd", "segments"],
    "공시": [],
    "사업": ["productService", "segments", "companyHistory", "salesOrder",
            "rawMaterial", "businessOverview"],
}

_ALWAYS_INCLUDE_MODULES = {"employee"}

_CONTEXT_MODULE_BUDGET = 6000  # 총 모듈 context 글자 수 상한


def _extract_module_context(company: Any, module_name: str, max_rows: int = 10) -> str | None:
    """registry 모듈 → 마크다운 요약. DataFrame/dict/list/text 모두 처리."""
    try:
        data = getattr(company, module_name, None)
        if data is None:
            data = company.show(module_name) if hasattr(company, "show") else None
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


def _build_report_sections(company: Any, compact: bool = False, q_types: list[str] | None = None) -> dict[str, str]:
    """reportEngine pivot 결과 + 질문 유형별 모듈 자동 주입 → LLM context 섹션 dict."""
    report = getattr(company, "report", None)
    sections: dict[str, str] = {}

    # 질문 유형별 추가 모듈 주입
    extra_modules: set[str] = set(_ALWAYS_INCLUDE_MODULES)
    if q_types:
        for qt in q_types:
            for mod in _QUESTION_MODULES.get(qt, []):
                extra_modules.add(mod)

    # 하드코딩된 기존 report 모듈들의 이름 (중복 방지용)
    _HARDCODED_REPORT = {"dividend", "employee", "majorHolder", "executive", "audit"}

    # 동적 모듈 주입 (하드코딩에 없는 것만)
    budget_used = 0
    for mod in sorted(extra_modules - _HARDCODED_REPORT):
        if budget_used >= _CONTEXT_MODULE_BUDGET:
            break
        content = _extract_module_context(company, mod, max_rows=8 if compact else 12)
        if content:
            budget_used += len(content)
            sections[f"module_{mod}"] = content

    if report is None:
        return sections

    sections: dict[str, str] = {}
    max_years = 3 if compact else 99

    div = getattr(report, "dividend", None)
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
        sections["report_dividend"] = "\n".join(lines)

    emp = getattr(report, "employee", None)
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

    mh = getattr(report, "majorHolder", None)
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

    exe = getattr(report, "executive", None)
    if exe is not None and exe.totalCount > 0:
        lines = [
            "## 임원현황 (정기보고서)",
            f"- 총 임원수: {exe.totalCount}명",
            f"- 사내이사: {exe.registeredCount}명",
            f"- 사외이사: {exe.outsideCount}명",
        ]
        sections["report_executive"] = "\n".join(lines)

    aud = getattr(report, "audit", None)
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


def _format_won(val: float) -> str:
    """원 단위 숫자를 읽기 좋은 한국어 단위로 변환."""
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    if abs_val >= 1e12:
        return f"{sign}{abs_val / 1e12:,.1f}조"
    if abs_val >= 1e8:
        return f"{sign}{abs_val / 1e8:,.0f}억"
    if abs_val >= 1e4:
        return f"{sign}{abs_val / 1e4:,.0f}만"
    if abs_val >= 1:
        return f"{sign}{abs_val:,.0f}"
    return "0"


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

    lines = [f"## {sj_labels.get(sj_div, sj_div)}", "(단위: 억/조원)", header, sep]
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
            from dartlab.engines.sector.types import Sector

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

    acct_filters: dict[str, set[str]] = {}
    if compact:
        for qt in q_types:
            for sj, ids in _QUESTION_ACCOUNT_FILTER.get(qt, {}).items():
                acct_filters.setdefault(sj, set()).update(ids)

    fe_loaded = False
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
                header += f"⚠️ **부분 연도 주의**: {notes} (해당 연도는 분기 누적이므로 전년 연간과 직접 비교 불가)\n"

            header_parts.append(header)

            for sj in ("IS", "BS", "CF"):
                af = acct_filters.get(sj) if acct_filters else None
                section = _build_finance_engine_section(series, years, sj, n_years, af, quarter_counts=quarter_counts)
                if section:
                    modules_dict[sj] = section
                    included.append(sj)
                    fe_loaded = True

    ratios_section = _build_ratios_section(company, compact=compact, q_types=q_types or None)
    if ratios_section:
        modules_dict["ratios"] = ratios_section
        if "ratios" not in included:
            included.append("ratios")

    report_sections = _build_report_sections(company, compact=compact, q_types=q_types)
    for key, section in report_sections.items():
        modules_dict[key] = section
        included.append(key)

    has_docs = getattr(company, "_hasDocs", False)

    if has_docs:
        _FINANCIAL_ONLY = {"BS", "IS", "CF", "fsSummary", "ratios"}
        tables_requested = _resolve_tables(question, include, exclude)
        qualitative_tables = [t for t in tables_requested if t not in _FINANCIAL_ONLY]

        if exclude:
            qualitative_tables = [t for t in qualitative_tables if t not in exclude]

        cache = getattr(company, "_cache", {})

        for name in qualitative_tables:
            if not include and name not in cache:
                continue

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

                section_parts = [f"\n## {label}"]

                max_rows_qual = 8 if compact else 15
                if isinstance(data, pl.DataFrame):
                    md = df_to_markdown(data, max_rows=max_rows_qual, meta=meta, compact=True)
                    section_parts.append(md)
                elif isinstance(data, dict):
                    items = list(data.items())
                    if compact:
                        items = items[:8]
                    dict_lines = [f"- {k}: {v}" for k, v in items]
                    section_parts.append("\n".join(dict_lines))
                elif isinstance(data, list):
                    max_items = min(meta.maxRows if meta else 10, 5 if compact else 10)
                    list_lines = []
                    for item in data[:max_items]:
                        if hasattr(item, "title") and hasattr(item, "chars"):
                            list_lines.append(f"- **{item.title}** ({item.chars}자)")
                        else:
                            list_lines.append(f"- {item}")
                    if len(data) > max_items:
                        list_lines.append(f"(... 상위 {max_items}건, 전체 {len(data)}건)")
                    section_parts.append("\n".join(list_lines))
                else:
                    max_text = 500 if compact else 1000
                    section_parts.append(str(data)[:max_text])

                modules_dict[name] = "\n".join(section_parts)
                included.append(name)

            except _CONTEXT_ERRORS:
                continue

    if not fe_loaded:
        text, inc = build_context(company, question, include, exclude, compact=True)
        modules_dict_fallback: dict[str, str] = {"_full": text}
        # _full fallback에서도 topics/insights 포함
        _topics_fb = _build_topics_section(company)
        if _topics_fb:
            modules_dict_fallback["_topics"] = _topics_fb
            inc.append("_topics")
        _insights_fb = _build_insights_section(company)
        if _insights_fb:
            modules_dict_fallback["_insights"] = _insights_fb
            inc.append("_insights")
        return modules_dict_fallback, inc, ""

    # ── 동적 topic 목록 + insights 자동 포함 ──
    # dartlab에 기능이 추가되면 AI가 자동으로 인식하도록
    # Company의 실제 topics에서 동적 생성
    _topics_section = _build_topics_section(company, compact=compact)
    if _topics_section:
        modules_dict["_topics"] = _topics_section
        included.append("_topics")

    _change_section = _build_change_summary(company)
    if _change_section:
        modules_dict["_changes"] = _change_section
        included.append("_changes")

    _insights_section = _build_insights_section(company)
    if _insights_section:
        modules_dict["_insights"] = _insights_section
        included.append("_insights")

    return modules_dict, included, "\n".join(header_parts)


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


_KEY_ACCOUNTS_BS = {
    "자산총계",
    "유동자산",
    "비유동자산",
    "부채총계",
    "유동부채",
    "비유동부채",
    "자본총계",
    "지배기업소유주지분",
    "현금및현금성자산",
    "매출채권",
    "재고자산",
    "유형자산",
    "무형자산",
    "투자부동산",
    "단기차입금",
    "장기차입금",
    "사채",
}

_KEY_ACCOUNTS_IS = {
    "매출액",
    "매출원가",
    "매출총이익",
    "판매비와관리비",
    "영업이익",
    "영업손실",
    "금융수익",
    "금융비용",
    "이자비용",
    "이자수익",
    "법인세비용차감전순이익",
    "법인세비용",
    "당기순이익",
    "당기순손실",
    "지배기업소유주지분순이익",
}

_KEY_ACCOUNTS_CF = {
    "영업활동현금흐름",
    "영업활동으로인한현금흐름",
    "투자활동현금흐름",
    "투자활동으로인한현금흐름",
    "재무활동현금흐름",
    "재무활동으로인한현금흐름",
    "현금및현금성자산의순증가",
    "현금및현금성자산의증감",
    "기초현금및현금성자산",
    "기말현금및현금성자산",
}

_KEY_ACCOUNTS_MAP = {
    "BS": _KEY_ACCOUNTS_BS,
    "IS": _KEY_ACCOUNTS_IS,
    "CF": _KEY_ACCOUNTS_CF,
}


def _filter_key_accounts(df: pl.DataFrame, module_name: str) -> pl.DataFrame:
    """재무제표에서 핵심 계정만 필터링."""
    if "계정명" not in df.columns or module_name not in _KEY_ACCOUNTS_MAP:
        return df

    key_set = _KEY_ACCOUNTS_MAP[module_name]
    mask = pl.lit(False)
    for keyword in key_set:
        mask = mask | pl.col("계정명").str.contains(keyword)

    filtered = df.filter(mask)
    if filtered.height < 5:
        return df
    return filtered


def _format_krw(val: float) -> str:
    """백만원 단위 숫자를 읽기 좋은 한국어 단위로 변환."""
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    if abs_val >= 1_000_000:
        return f"{sign}{abs_val / 1_000_000:,.1f}조"
    if abs_val >= 10_000:
        return f"{sign}{abs_val / 10_000:,.0f}억"
    if abs_val >= 1:
        return f"{sign}{abs_val:,.0f}"
    if abs_val > 0:
        return f"{sign}{abs_val:.4f}"
    return "0"


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


# ══════════════════════════════════════
# 질문 키워드 → 자동 포함 데이터 매핑
# ══════════════════════════════════════

_TOPIC_MAP: dict[str, list[str]] = {
    # ── 재무제표 ──
    "재무": ["BS", "IS", "CF", "fsSummary", "costByNature"],
    "건전성": ["BS", "audit", "contingentLiability", "internalControl", "bond"],
    "수익": ["IS", "segment", "productService", "costByNature"],
    "실적": ["IS", "segment", "fsSummary", "productService", "salesOrder"],
    "매출": ["IS", "segment", "productService", "salesOrder"],
    "영업이익": ["IS", "fsSummary", "segment"],
    "순이익": ["IS", "fsSummary"],
    "현금": ["CF", "BS"],
    "자산": ["BS", "tangibleAsset", "investmentInOther"],
    "유형자산": ["tangibleAsset"],
    "성장": ["IS", "CF", "productService", "salesOrder", "rnd"],
    "원가": ["costByNature", "IS"],
    "비용": ["costByNature", "IS"],
    # ── 배당·자본 ──
    "배당": ["dividend", "IS", "shareCapital"],
    "자본": ["BS", "capitalChange", "shareCapital", "fundraising"],
    "증자": ["fundraising", "capitalChange", "shareCapital"],
    "감자": ["fundraising", "capitalChange"],
    "자기주식": ["shareCapital", "capitalChange"],
    "주식": ["shareCapital", "capitalChange", "fundraising"],
    # ── 주주·지배구조 ──
    "주주": ["majorHolder", "holderOverview", "dividend", "shareCapital", "shareholderMeeting"],
    "지배": ["majorHolder", "executive", "boardOfDirectors", "holderOverview"],
    "임원": ["executive", "executivePay", "boardOfDirectors"],
    "보수": ["executivePay", "employee"],
    "급여": ["employee", "executivePay"],
    "이사회": ["boardOfDirectors", "executive"],
    "사외이사": ["boardOfDirectors", "executive"],
    "직원": ["employee"],
    "주총": ["shareholderMeeting"],
    # ── 감사·통제·리스크 ──
    "감사": ["audit", "auditSystem", "internalControl"],
    "내부통제": ["internalControl", "auditSystem"],
    "리스크": ["contingentLiability", "sanction", "riskDerivative", "audit", "internalControl"],
    "소송": ["contingentLiability", "sanction"],
    "보증": ["contingentLiability"],
    "제재": ["sanction"],
    "파생": ["riskDerivative"],
    "환율": ["riskDerivative"],
    "환위험": ["riskDerivative"],
    # ── 투자·사업 ──
    "투자": ["CF", "rnd", "subsidiary", "investmentInOther", "tangibleAsset"],
    "연구": ["rnd"],
    "연구개발": ["rnd"],
    "R&D": ["rnd"],
    "기술": ["rnd", "business"],
    "자회사": ["subsidiary", "affiliateGroup", "investmentInOther"],
    "계열사": ["affiliateGroup", "relatedPartyTx", "subsidiary"],
    "계열": ["affiliateGroup", "relatedPartyTx"],
    "관계사": ["affiliateGroup", "relatedPartyTx", "subsidiary"],
    "출자": ["investmentInOther"],
    "제품": ["productService"],
    "수주": ["salesOrder"],
    "설비": ["tangibleAsset", "rawMaterial"],
    "원재료": ["rawMaterial", "costByNature"],
    "채무증권": ["bond"],
    "사채": ["bond"],
    "부채": ["BS", "bond", "contingentLiability", "capitalChange"],
    # ── 서술·개요 ──
    "사업": ["business", "companyOverview", "companyOverviewDetail", "companyHistory"],
    "개요": ["companyOverviewDetail", "companyOverview"],
    "연혁": ["companyHistory"],
    "정관": ["articlesOfIncorporation"],
    "MD&A": ["mdna"],
    "경영진단": ["mdna"],
    "대손": ["otherFinance"],
    "재고": ["otherFinance"],
    # ── 복합 분석 ──
    "ROE": ["IS", "BS", "fsSummary"],
    "ROA": ["IS", "BS", "fsSummary"],
    "PER": ["IS", "fsSummary", "dividend"],
    "PBR": ["BS", "fsSummary"],
    "EPS": ["IS", "fsSummary", "dividend"],
    "EBITDA": ["IS", "CF", "fsSummary"],
    "부문": ["segment"],
    "세그먼트": ["segment"],
    "ESG": ["employee", "boardOfDirectors", "sanction", "internalControl"],
    "신용등급": ["companyOverview"],
    # ── 스캔 ──
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
    # ── 영문 동의어 ──
    "revenue": ["IS", "segment", "productService"],
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
    "operating": ["IS", "fsSummary", "segment"],
    # ── 자연어 질문 패턴 ──
    "돈": ["BS", "CF"],
    "벌": ["IS", "fsSummary"],
    "잘": ["IS", "fsSummary", "segment"],
    "위험": ["contingentLiability", "sanction", "riskDerivative", "audit", "internalControl"],
    "안전": ["BS", "audit", "contingentLiability", "internalControl"],
    "건강": ["BS", "IS", "CF", "audit"],
    "전망": ["IS", "CF", "rnd", "segment", "mdna"],
    "비교": ["IS", "BS", "CF", "fsSummary"],
    "추세": ["IS", "BS", "CF", "fsSummary"],
    "트렌드": ["IS", "BS", "CF", "fsSummary"],
    "분석": ["BS", "IS", "CF", "fsSummary"],
    "어떤 회사": ["companyOverviewDetail", "companyOverview", "business", "companyHistory"],
    "무슨 사업": ["business", "productService", "segment", "companyOverviewDetail"],
    "뭐하는": ["business", "productService", "segment", "companyOverviewDetail"],
    "어떤 사업": ["business", "productService", "segment", "companyOverviewDetail"],
}

# 항상 포함되는 기본 컨텍스트
_BASE_CONTEXT = ["fsSummary"]


def _get_sector(company: Any) -> str | None:
    """Company에서 업종명 추출."""
    try:
        overview = getattr(company, "companyOverview", None)
        if isinstance(overview, dict):
            sector = overview.get("indutyName") or overview.get("sector")
            if sector:
                return sector

        detail = getattr(company, "companyOverviewDetail", None)
        if isinstance(detail, dict):
            sector = detail.get("sector") or detail.get("indutyName")
            if sector:
                return sector
    except _CONTEXT_ERRORS:
        pass

    return None


# ══════════════════════════════════════
# DataFrame → 마크다운 변환
# ══════════════════════════════════════


def df_to_markdown(
    df: pl.DataFrame,
    max_rows: int = 30,
    meta: ModuleMeta | None = None,
    compact: bool = False,
) -> str:
    """Polars DataFrame → 메타데이터 주석 포함 Markdown 테이블.

    Args:
            compact: True면 숫자를 억/조 단위로 변환 (LLM 컨텍스트용).
    """
    if df is None or df.height == 0:
        return "(데이터 없음)"

    effective_max = meta.maxRows if meta else max_rows
    if compact:
        effective_max = min(effective_max, 20)

    if "year" in df.columns:
        df = df.sort("year", descending=True)

    if df.height > effective_max:
        display_df = df.head(effective_max)
        truncated = True
    else:
        display_df = df
        truncated = False

    parts = []

    is_krw = not meta or meta.unit in ("백만원", "")
    if meta and meta.unit and meta.unit != "백만원":
        parts.append(f"(단위: {meta.unit})")
    elif compact and is_krw:
        parts.append("(단위: 억/조원, 원본 백만원)")

    if not compact and meta and meta.columns:
        col_map = {c.name: c for c in meta.columns}
        described = []
        for col in display_df.columns:
            if col in col_map:
                c = col_map[col]
                desc = f"`{col}`: {c.description}"
                if c.unit:
                    desc += f" ({c.unit})"
                described.append(desc)
        if described:
            parts.append(" | ".join(described))

    cols = display_df.columns
    if not compact and meta and meta.columns:
        col_map = {c.name: c for c in meta.columns}
        header_cells = []
        for col in cols:
            if col in col_map:
                header_cells.append(f"{col} ({col_map[col].description})")
            else:
                header_cells.append(col)
        header = "| " + " | ".join(header_cells) + " |"
    else:
        header = "| " + " | ".join(cols) + " |"

    sep = "| " + " | ".join(["---"] * len(cols)) + " |"

    rows = []
    for row in display_df.iter_rows():
        cells = []
        for i, val in enumerate(row):
            if val is None:
                cells.append("-")
            elif isinstance(val, (int, float)):
                col_name = cols[i]
                if compact and is_krw and col_name.isdigit() and len(col_name) == 4:
                    cells.append(_format_krw(float(val)))
                elif isinstance(val, float):
                    if abs(val) >= 1:
                        cells.append(f"{val:,.0f}")
                    else:
                        cells.append(f"{val:.4f}")
                elif col_name == "year" or (isinstance(val, int) and 1900 <= val <= 2100):
                    cells.append(str(val))
                else:
                    cells.append(f"{val:,}")
            else:
                cells.append(str(val))
        rows.append("| " + " | ".join(cells) + " |")

    parts.append("\n".join([header, sep] + rows))

    if truncated:
        parts.append(f"(상위 {effective_max}행 표시, 전체 {df.height}행)")

    return "\n".join(parts)


# ══════════════════════════════════════
# 파생 지표 자동계산
# ══════════════════════════════════════


def _find_account_value(df: pl.DataFrame, keyword: str, year_col: str) -> float | None:
    """계정명에서 키워드를 포함하는 행의 값 추출."""
    if "계정명" not in df.columns or year_col not in df.columns:
        return None
    matched = df.filter(pl.col("계정명").str.contains(keyword))
    if matched.height == 0:
        return None
    val = matched.row(0, named=True).get(year_col)
    return val if isinstance(val, (int, float)) else None


def _compute_derived_metrics(name: str, df: pl.DataFrame, company: Any = None) -> str | None:
    """핵심 재무제표에서 YoY 성장률/비율 자동계산.

    개선: ROE, 이자보상배율, FCF, EBITDA 등 추가.
    """
    if name not in ("BS", "IS", "CF") or df is None or df.height == 0:
        return None

    year_cols = sorted(
        [c for c in df.columns if c.isdigit() and len(c) == 4],
        reverse=True,
    )
    if len(year_cols) < 2:
        return None

    lines = []

    if name == "IS":
        targets = {
            "매출액": "매출 성장률",
            "영업이익": "영업이익 성장률",
            "당기순이익": "순이익 성장률",
        }
        for acct, label in targets.items():
            metrics = []
            for i in range(min(len(year_cols) - 1, 3)):
                cur = _find_account_value(df, acct, year_cols[i])
                prev = _find_account_value(df, acct, year_cols[i + 1])
                if cur is not None and prev is not None and prev != 0:
                    yoy = (cur - prev) / abs(prev) * 100
                    metrics.append(f"{year_cols[i]}/{year_cols[i + 1]}: {yoy:+.1f}%")
            if metrics:
                lines.append(f"- {label}: {', '.join(metrics)}")

        # 영업이익률, 순이익률
        latest = year_cols[0]
        rev = _find_account_value(df, "매출액", latest)
        oi = _find_account_value(df, "영업이익", latest)
        ni = _find_account_value(df, "당기순이익", latest)
        if rev and rev != 0:
            if oi is not None:
                lines.append(f"- {latest} 영업이익률: {oi / rev * 100:.1f}%")
            if ni is not None:
                lines.append(f"- {latest} 순이익률: {ni / rev * 100:.1f}%")

        # 이자보상배율 (영업이익 / 이자비용)
        interest = _find_account_value(df, "이자비용", latest)
        if interest is None:
            interest = _find_account_value(df, "금융비용", latest)
        if oi is not None and interest is not None and interest != 0:
            icr = oi / abs(interest)
            lines.append(f"- {latest} 이자보상배율: {icr:.1f}x")

        # ROE (순이익 / 자본총계) — BS가 있을 때
        if company and ni is not None:
            try:
                bs = getattr(company, "BS", None)
                if isinstance(bs, pl.DataFrame) and latest in bs.columns:
                    equity = _find_account_value(bs, "자본총계", latest)
                    if equity and equity != 0:
                        roe = ni / equity * 100
                        lines.append(f"- {latest} ROE: {roe:.1f}%")
                    total_asset = _find_account_value(bs, "자산총계", latest)
                    if total_asset and total_asset != 0:
                        roa = ni / total_asset * 100
                        lines.append(f"- {latest} ROA: {roa:.1f}%")
            except _CONTEXT_ERRORS:
                pass

    elif name == "BS":
        latest = year_cols[0]
        debt = _find_account_value(df, "부채총계", latest)
        equity = _find_account_value(df, "자본총계", latest)
        ca = _find_account_value(df, "유동자산", latest)
        cl = _find_account_value(df, "유동부채", latest)
        ta = _find_account_value(df, "자산총계", latest)

        if debt is not None and equity is not None and equity != 0:
            lines.append(f"- {latest} 부채비율: {debt / equity * 100:.1f}%")
        if ca is not None and cl is not None and cl != 0:
            lines.append(f"- {latest} 유동비율: {ca / cl * 100:.1f}%")
        if debt is not None and ta is not None and ta != 0:
            lines.append(f"- {latest} 부채총계/자산총계: {debt / ta * 100:.1f}%")

        # 총자산 증가율
        for i in range(min(len(year_cols) - 1, 2)):
            cur = _find_account_value(df, "자산총계", year_cols[i])
            prev = _find_account_value(df, "자산총계", year_cols[i + 1])
            if cur is not None and prev is not None and prev != 0:
                yoy = (cur - prev) / abs(prev) * 100
                lines.append(f"- 총자산 증가율 {year_cols[i]}/{year_cols[i + 1]}: {yoy:+.1f}%")

    elif name == "CF":
        latest = year_cols[0]
        op_cf = _find_account_value(df, "영업활동", latest)
        inv_cf = _find_account_value(df, "투자활동", latest)
        fin_cf = _find_account_value(df, "재무활동", latest)

        if op_cf is not None and inv_cf is not None:
            fcf = op_cf + inv_cf
            lines.append(f"- {latest} FCF(영업CF+투자CF): {_format_krw(fcf)}")

        # CF 패턴 해석
        if op_cf is not None and inv_cf is not None and fin_cf is not None:
            pattern = f"{'+' if op_cf >= 0 else '-'}/{'+' if inv_cf >= 0 else '-'}/{'+' if fin_cf >= 0 else '-'}"
            pattern_desc = _interpret_cf_pattern(op_cf >= 0, inv_cf >= 0, fin_cf >= 0)
            lines.append(f"- {latest} CF 패턴(영업/투자/재무): {pattern} → {pattern_desc}")

        for i in range(min(len(year_cols) - 1, 2)):
            cur = _find_account_value(df, "영업활동", year_cols[i])
            prev = _find_account_value(df, "영업활동", year_cols[i + 1])
            if cur is not None and prev is not None and prev != 0:
                yoy = (cur - prev) / abs(prev) * 100
                lines.append(f"- 영업활동CF 변동 {year_cols[i]}/{year_cols[i + 1]}: {yoy:+.1f}%")

    if not lines:
        return None

    return "### 주요 지표 (자동계산)\n" + "\n".join(lines)


def _interpret_cf_pattern(op_pos: bool, inv_pos: bool, fin_pos: bool) -> str:
    """현금흐름 패턴 해석."""
    if op_pos and not inv_pos and not fin_pos:
        return "우량 기업형 (영업이익으로 투자+상환)"
    if op_pos and not inv_pos and fin_pos:
        return "성장 투자형 (영업+차입으로 적극 투자)"
    if op_pos and inv_pos and not fin_pos:
        return "구조조정형 (자산 매각+부채 상환)"
    if not op_pos and not inv_pos and fin_pos:
        return "위험 신호 (영업적자인데 차입으로 투자)"
    if not op_pos and inv_pos and fin_pos:
        return "위기 관리형 (자산 매각+차입으로 영업 보전)"
    if not op_pos and inv_pos and not fin_pos:
        return "축소형 (자산 매각으로 부채 상환)"
    return "기타 패턴"


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
        from dartlab.engines.insight import analyze

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
    topic_list = list(topics) if not isinstance(topics, list) else topics
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
        from dartlab.engines.insight.pipeline import analyze

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
_SKELETON_ACCOUNTS: dict[str, list[tuple[str, str]]] = {
    "IS": [("sales", "매출액"), ("operating_profit", "영업이익")],
    "BS": [("total_assets", "자산총계")],
}


def build_context_skeleton(company: Any) -> tuple[str, list[str]]:
    """skeleton tier: ~500 토큰. tool calling provider용 최소 컨텍스트.

    핵심 비율 6개 + 매출/영업이익/총자산 3계정 + insight 등급 1줄.
    상세 데이터는 도구로 조회하도록 안내.
    """
    parts = [f"# {company.corpName} ({company.stockCode})"]
    included = []

    # 핵심 계정 3개 (최근 3년)
    annual = getattr(company, "annual", None)
    if annual is not None:
        series, years = annual
        quarter_counts = _get_quarter_counts(company)
        if years:
            display_years = years[-3:]
            # 부분 연도 표시
            display_labeled = []
            for y in display_years:
                qc = quarter_counts.get(y, 4)
                if qc < 4:
                    display_labeled.append(f"{y}(~Q{qc})")
                else:
                    display_labeled.append(y)
            display_reversed = list(reversed(display_labeled))
            year_offset = len(years) - 3

            header = "| 계정 | " + " | ".join(display_reversed) + " |"
            sep = "| --- | " + " | ".join(["---"] * len(display_reversed)) + " |"
            rows = []
            for sj, accts in _SKELETON_ACCOUNTS.items():
                sj_data = series.get(sj, {})
                for snake_id, label in accts:
                    vals = sj_data.get(snake_id)
                    if not vals:
                        continue
                    sliced = vals[max(0, year_offset) :]
                    cells = [_format_won(v) if v is not None else "-" for v in reversed(sliced)]
                    rows.append(f"| {label} | " + " | ".join(cells) + " |")

            if rows:
                partial = [y for y in display_years if quarter_counts.get(y, 4) < 4]
                partial_note = ""
                if partial:
                    notes = ", ".join(f"{y}=Q1~Q{quarter_counts[y]}" for y in partial)
                    partial_note = f"\n⚠️ 부분 연도: {notes}"
                parts.extend(["", f"## 핵심 수치 (억/조원){partial_note}", header, sep, *rows])
                included.extend(["IS", "BS"])

    # 핵심 비율 6개
    ratios = get_headline_ratios(company)
    if ratios is not None and hasattr(ratios, "roe"):
        ratio_lines = []
        for key in _SKELETON_RATIO_KEYS:
            val = getattr(ratios, key, None)
            if val is None:
                continue
            label_map = {
                "roe": "ROE",
                "debtRatio": "부채비율",
                "currentRatio": "유동비율",
                "operatingMargin": "영업이익률",
                "fcf": "FCF",
                "revenueGrowth3Y": "매출3Y CAGR",
            }
            label = label_map.get(key, key)
            if key == "fcf":
                ratio_lines.append(f"- {label}: {_format_won(val)}")
            else:
                ratio_lines.append(f"- {label}: {val:.1f}%")
        if ratio_lines:
            parts.extend(["", "## 핵심 비율", *ratio_lines])
            included.append("ratios")

    # insight 등급 1줄
    try:
        from dartlab.engines.insight.pipeline import analyze as _analyze

        result = _analyze(company.stockCode, company=company)
        if result is not None:
            grades = result.grades()
            grade_str = " / ".join(
                f"{lbl}:{grades.get(k, 'N')}"
                for k, lbl in [
                    ("performance", "실적"),
                    ("profitability", "수익성"),
                    ("health", "건전성"),
                    ("cashflow", "CF"),
                ]
                if grades.get(k)
            )
            parts.append(f"\n인사이트: {grade_str}")
            if result.profile:
                parts.append(f"프로파일: {result.profile}")
            included.append("_insights")
    except (ImportError, AttributeError, FileNotFoundError, OSError, RuntimeError, TypeError, ValueError):
        pass

    # 조회 가능한 topics 요약
    topics_raw = getattr(company, "topics", None)
    if topics_raw is not None:
        if isinstance(topics_raw, pl.DataFrame) and "topic" in topics_raw.columns:
            topic_list = topics_raw["topic"].to_list()
        elif isinstance(topics_raw, list):
            topic_list = topics_raw
        else:
            topic_list = list(topics_raw) if topics_raw is not None else []
        if topic_list:
            parts.append(f"\n## 조회 가능한 공시 데이터 ({len(topic_list)}개 topic)")
            parts.append(f"주요: {', '.join(topic_list[:15])}")
            if len(topic_list) > 15:
                parts.append(f"외 {len(topic_list) - 15}개. 전체는 `list_topics()`로 확인.")

    parts.extend(
        [
            "",
            "## DartLab 분석 가이드",
            "이 기업의 모든 공시 데이터는 **sections** (topic × 기간 수평화)으로 구조화되어 있습니다.",
            "- `list_topics()` → 전체 topic 목록 (평균 120+개)",
            "- `show_topic(topic)` → 블록 목차 → `show_topic(topic, N)` → 실제 데이터",
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
