"""Finance 도구 — 데이터 조회/비율/성장/YoY/이상치/요약/보고서."""

from __future__ import annotations

from typing import Any

import polars as pl

from .helpers import df_to_md, format_tool_value


def register_finance_tools(company: Any, register_tool) -> None:
    """재무 데이터 관련 도구를 등록한다."""
    from dartlab.core.capabilities import CapabilityKind

    # 0. list_modules
    def list_modules() -> str:
        from dartlab.engines.ai.context.builder import scan_available_modules

        modules = scan_available_modules(company)
        if not modules:
            return "사용 가능한 데이터 모듈이 없습니다."
        lines = ["| 모듈명 | 설명 | 유형 | 행수 |", "| --- | --- | --- | --- |"]
        for m in modules:
            lines.append(f"| `{m['name']}` | {m['label']} | {m.get('type', '-')} | {m.get('rows', '-')} |")
        return "\n".join(lines)

    register_tool(
        "list_modules",
        list_modules,
        "이 기업에서 조회 가능한 모든 데이터 모듈(BS, IS, CF, dividend, audit 등) 목록을 반환합니다. "
        "사용 시점: get_data에 넣을 모듈명을 모를 때. "
        "사용하지 말 것: 공시 원문(sections) 목록이 필요하면 list_topics를 사용하세요. "
        "list_modules는 재무/정형 데이터, list_topics는 공시 문서 목록입니다.",
        {"type": "object", "properties": {}},
    )

    # 1. get_data
    def get_data(module_name: str) -> str:
        data = getattr(company, module_name, None) if hasattr(company, module_name) else company.show(module_name)
        if data is None:
            from dartlab.engines.ai.metadata import MODULE_META

            suggestions = [
                f"`{n}` ({m.label})"
                for n, m in MODULE_META.items()
                if module_name.lower() in n.lower() or module_name.lower() in m.label.lower()
            ]
            msg = f"'{module_name}' 데이터가 없습니다."
            if suggestions:
                msg += f" 유사한 모듈: {', '.join(suggestions[:5])}"
            msg += " `list_modules` 도구로 사용 가능한 모듈을 확인하세요."
            return msg
        if isinstance(data, pl.DataFrame):
            return df_to_md(data)
        if isinstance(data, dict):
            return "\n".join(f"- {k}: {v}" for k, v in data.items())
        if isinstance(data, list):
            return "\n".join(f"- {item}" for item in data[:20])
        return str(data)[:2000]

    from dartlab.core.registry import buildModuleDescription

    register_tool(
        "get_data",
        get_data,
        "기업의 재무/공시 데이터를 조회합니다. "
        "주요 module_name: "
        f"{buildModuleDescription()}. "
        "모듈명을 모르면 먼저 `list_modules`를 호출하세요.",
        {
            "type": "object",
            "properties": {
                "module_name": {
                    "type": "string",
                    "description": "조회할 모듈명 (예: BS, IS, CF, dividend, audit, fsSummary)",
                },
            },
            "required": ["module_name"],
        },
        kind=CapabilityKind.DATA,
        requires_company=True,
        ai_hint="회사 바인딩 데이터 모듈 조회",
    )

    # 1b. search_data
    def search_data(keyword: str) -> str:
        from dartlab.engines.ai.metadata import MODULE_META

        results = []
        keyword_lower = keyword.lower()

        for name, meta in MODULE_META.items():
            try:
                data = getattr(company, name, None)
                if data is None:
                    continue
                if isinstance(data, pl.DataFrame) and data.height > 0:
                    matched_cols = [c for c in data.columns if keyword_lower in c.lower()]
                    if "계정명" in data.columns:
                        matched_rows = data.filter(pl.col("계정명").str.contains(f"(?i){keyword}"))
                        if matched_rows.height > 0:
                            results.append(f"### {meta.label} (`{name}`) — 계정명 매칭 {matched_rows.height}건")
                            results.append(df_to_md(matched_rows, max_rows=10))
                    elif matched_cols:
                        results.append(f"### {meta.label} (`{name}`) — 컬럼 매칭: {', '.join(matched_cols)}")
                elif isinstance(data, dict):
                    matched_keys = [
                        k for k in data if keyword_lower in str(k).lower() or keyword_lower in str(data[k]).lower()
                    ]
                    if matched_keys:
                        results.append(f"### {meta.label} (`{name}`)")
                        for k in matched_keys[:5]:
                            results.append(f"- {k}: {data[k]}")
            except (AttributeError, KeyError, RuntimeError, TypeError, ValueError):
                continue

        if not results:
            return f"'{keyword}'와 관련된 데이터를 찾지 못했습니다. 다른 키워드를 시도하거나 `list_modules`로 사용 가능한 데이터를 확인하세요."
        return "\n\n".join(results)

    register_tool(
        "search_data",
        search_data,
        "키워드로 모든 데이터 모듈을 검색합니다. "
        "특정 계정과목(예: '매출액', '부채'), 지표명, 또는 컬럼명으로 검색합니다. "
        "어떤 모듈에 데이터가 있는지 모를 때 유용합니다.",
        {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "검색할 키워드 (예: '매출', '부채비율', 'R&D', '이자비용')",
                },
            },
            "required": ["keyword"],
        },
    )

    # 2. compute_ratios
    def compute_ratios() -> str:
        from dartlab.tools.table import ratio_table

        bs = getattr(company, "BS", None)
        is_ = getattr(company, "IS", None)
        if not isinstance(bs, pl.DataFrame) or not isinstance(is_, pl.DataFrame):
            return "BS 또는 IS 데이터가 없어 재무비율을 계산할 수 없습니다."
        result = ratio_table(bs, is_)
        return df_to_md(result)

    register_tool(
        "compute_ratios",
        compute_ratios,
        "재무상태표(BS)와 손익계산서(IS)로 핵심 재무비율을 자동 계산합니다. "
        "반환: 부채비율, 유동비율, 영업이익률, 순이익률, ROE, ROA (연도별 테이블). "
        "사용 시점: 건전성/수익성 분석, 비율 추세 확인. "
        "사용하지 말 것: 원본 BS/IS 수치 자체가 필요하면 get_data를 사용하세요.",
        {"type": "object", "properties": {}},
        kind=CapabilityKind.ANALYSIS,
        requires_company=True,
    )

    # 3. find_anomalies
    def find_anomalies(module_name: str, threshold_pct: float = 50.0) -> str:
        from dartlab.engines.ai.aiParser import detect_anomalies

        data = getattr(company, module_name, None)
        if not isinstance(data, pl.DataFrame):
            return f"'{module_name}' DataFrame 데이터가 없습니다."
        anomalies = detect_anomalies(data, use_llm=False, threshold_pct=threshold_pct)
        if not anomalies:
            return f"'{module_name}'에서 이상치가 발견되지 않았습니다."
        lines = []
        for a in anomalies:
            lines.append(f"- [{a.severity}] {a.column} {a.year}: {a.description} (변동 {a.change_pct:+.1f}%)")
        return "\n".join(lines)

    register_tool(
        "detect_anomalies",
        find_anomalies,
        "재무 데이터에서 이상치(급격한 YoY 변동, 부호 반전)를 자동 탐지합니다. "
        "사용 시점: 리스크 분석, 이상 징후 확인, '뭔가 이상한 게 있어?' 질문. "
        "사용하지 말 것: 정상적인 재무 추세 분석에는 compute_ratios나 yoy_analysis가 적절합니다.",
        {
            "type": "object",
            "properties": {
                "module_name": {
                    "type": "string",
                    "description": "분석할 모듈명 (예: BS, IS, CF)",
                },
                "threshold_pct": {
                    "type": "number",
                    "description": "이상치 판정 기준 YoY 변동률 (기본 50%)",
                    "default": 50.0,
                },
            },
            "required": ["module_name"],
        },
    )

    # 4. compute_growth
    def compute_growth(module_name: str) -> str:
        from dartlab.tools.table import growth_matrix, pivot_accounts

        data = getattr(company, module_name, None)
        if not isinstance(data, pl.DataFrame):
            return f"'{module_name}' DataFrame 데이터가 없습니다."
        pivoted = pivot_accounts(data)
        if "year" not in pivoted.columns:
            return "연도 데이터가 부족하여 성장률을 계산할 수 없습니다."
        result = growth_matrix(pivoted)
        return df_to_md(result)

    register_tool(
        "compute_growth",
        compute_growth,
        "다기간 CAGR(복합연간성장률) 매트릭스를 계산합니다. 1Y, 2Y, 3Y, 5Y 성장률 반환. "
        "사용 시점: 성장성 분석, '매출 성장률이 어떻게 돼?' 질문. "
        "사용하지 말 것: 단순 전년 대비는 yoy_analysis가 더 적절합니다.",
        {
            "type": "object",
            "properties": {
                "module_name": {
                    "type": "string",
                    "description": "분석할 모듈명 (예: IS, dividend)",
                },
            },
            "required": ["module_name"],
        },
    )

    # 5. yoy_analysis
    def yoy_analysis(module_name: str) -> str:
        from dartlab.tools.table import pivot_accounts, yoy_change

        data = getattr(company, module_name, None)
        if not isinstance(data, pl.DataFrame):
            return f"'{module_name}' DataFrame 데이터가 없습니다."
        if "계정명" in data.columns:
            data = pivot_accounts(data)
        if "year" not in data.columns:
            return "year 컬럼이 없어 YoY 분석을 할 수 없습니다."
        result = yoy_change(data)
        return df_to_md(result)

    register_tool(
        "yoy_analysis",
        yoy_analysis,
        "데이터의 전년 대비(YoY) 변동률을 계산합니다. 각 항목의 연도별 증감률(%)을 반환. "
        "사용 시점: '작년 대비 어떻게 변했어?', 수익성/배당 추이 분석. "
        "사용하지 말 것: 다년간 CAGR이 필요하면 compute_growth를 사용하세요.",
        {
            "type": "object",
            "properties": {
                "module_name": {
                    "type": "string",
                    "description": "분석할 모듈명 (예: IS, BS, dividend)",
                },
            },
            "required": ["module_name"],
        },
    )

    # 6. get_summary
    def get_summary(module_name: str) -> str:
        from dartlab.tools.table import pivot_accounts, summary_stats

        data = getattr(company, module_name, None)
        if not isinstance(data, pl.DataFrame):
            return f"'{module_name}' DataFrame 데이터가 없습니다."
        if "계정명" in data.columns:
            data = pivot_accounts(data)
        result = summary_stats(data)
        return df_to_md(result)

    register_tool(
        "get_summary",
        get_summary,
        "데이터의 요약 통계(평균, 최솟값, 최댓값, 표준편차, CAGR, 추세)를 계산합니다. "
        "사용 시점: 전반적 데이터 개요, 장기 추세 요약이 필요할 때. "
        "사용하지 말 것: 특정 연도 수치가 필요하면 get_data, 비율은 compute_ratios를 사용하세요.",
        {
            "type": "object",
            "properties": {
                "module_name": {
                    "type": "string",
                    "description": "분석할 모듈명 (예: IS, BS, dividend)",
                },
            },
            "required": ["module_name"],
        },
    )

    # 7b. get_report_data
    def get_report_data(api_type: str) -> str:
        report = getattr(company, "report", None)
        if report is None:
            return "정기보고서 데이터가 없습니다."
        df = report.extract(api_type)
        if df is None:
            from dartlab.engines.dart.report.types import API_TYPE_LABELS

            available = ", ".join(f"`{k}` ({v})" for k, v in list(API_TYPE_LABELS.items())[:10])
            return f"'{api_type}' 데이터가 없습니다. 사용 가능한 타입 예시: {available}"
        return df_to_md(df)

    register_tool(
        "get_report_data",
        get_report_data,
        "DART 정기보고서 API의 표준화된 정형 데이터를 조회합니다. "
        "api_type: dividend(배당), employee(직원), executive(임원), majorHolder(최대주주), "
        "auditOpinion(감사의견), capitalChange(증자감자), stockTotal(주식총수), treasuryStock(자기주식). "
        "사용 시점: 배당·직원·임원·주주 등 정형화된 수치가 필요할 때. get_data(BS/IS)와는 다른 소스. "
        "사용하지 말 것: 공시 원문 텍스트가 필요하면 show_topic을 사용하세요.",
        {
            "type": "object",
            "properties": {
                "api_type": {
                    "type": "string",
                    "description": "조회할 API 타입 (예: dividend, employee, majorHolder)",
                },
            },
            "required": ["api_type"],
        },
        kind=CapabilityKind.DATA,
        requires_company=True,
    )
