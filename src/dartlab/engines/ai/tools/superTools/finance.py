"""finance Super Tool — 재무 데이터 통합 dispatcher.

통합 대상: get_data, list_modules, compute_ratios, compute_growth,
yoy_analysis, get_summary, detect_anomalies, get_report_data,
compare_companies, timeseries_filter, custom_ratio, search_data
"""

from __future__ import annotations

from typing import Any

import polars as pl

from ..defaults.helpers import df_to_md, format_tool_value


def registerFinanceTool(company: Any, registerTool) -> None:
    """finance Super Tool 등록."""

    # ── 동적 enum: 모듈 목록 ──
    moduleEnum: list[str] = []
    moduleDesc = ""
    try:
        from dartlab.engines.ai.context.builder import scan_available_modules

        mods = scan_available_modules(company)
        if mods:
            moduleEnum = [m["name"] for m in mods]
            moduleDesc = ", ".join(f"{m['name']}={m['label']}" for m in mods[:15])
    except (ImportError, AttributeError, KeyError, TypeError, ValueError):
        pass

    # ── 동적 enum: report API 타입 ──
    reportApiEnum: list[str] = []
    reportApiDesc = ""
    try:
        report = getattr(company, "report", None)
        if report is not None:
            available = getattr(report, "availableApiTypes", None)
            if available:
                reportApiEnum = list(available) if not isinstance(available, list) else available
        if reportApiEnum:
            from dartlab.engines.company.dart.report.types import API_TYPE_LABELS

            reportApiDesc = ", ".join(f"{k}={API_TYPE_LABELS.get(k, k)}" for k in reportApiEnum[:15])
    except (ImportError, AttributeError, KeyError, TypeError, ValueError):
        pass

    # ── action 핸들러 ──

    def _data(module: str = "", **_kw) -> str:
        """모듈 데이터 조회."""
        if not module:
            return "module을 지정하세요."
        data = getattr(company, module, None) if hasattr(company, module) else company.show(module)
        if data is None:
            return f"'{module}' 데이터가 없습니다. action=modules로 사용 가능한 목록을 확인하세요."
        if isinstance(data, pl.DataFrame):
            return df_to_md(data)
        if isinstance(data, dict):
            return "\n".join(f"- {k}: {v}" for k, v in data.items())
        if isinstance(data, list):
            return "\n".join(f"- {item}" for item in data[:20])
        return str(data)[:2000]

    def _modules(**_kw) -> str:
        """사용 가능한 모듈 목록."""
        from dartlab.engines.ai.context.builder import scan_available_modules

        modules = scan_available_modules(company)
        if not modules:
            return "사용 가능한 데이터 모듈이 없습니다."
        lines = ["| 모듈명 | 설명 | 유형 | 행수 |", "| --- | --- | --- | --- |"]
        for m in modules:
            lines.append(f"| `{m['name']}` | {m['label']} | {m.get('type', '-')} | {m.get('rows', '-')} |")
        return "\n".join(lines)

    def _ratios(**_kw) -> str:
        """재무비율 계산."""
        from dartlab.tools.table import ratio_table

        bs = getattr(company, "BS", None)
        is_ = getattr(company, "IS", None)
        if not isinstance(bs, pl.DataFrame) or not isinstance(is_, pl.DataFrame):
            return "BS 또는 IS 데이터가 없어 재무비율을 계산할 수 없습니다."
        return df_to_md(ratio_table(bs, is_))

    def _growth(module: str = "", **_kw) -> str:
        """CAGR 성장률 매트릭스."""
        if not module:
            return "module을 지정하세요."
        from dartlab.tools.table import growth_matrix, pivot_accounts

        data = getattr(company, module, None)
        if not isinstance(data, pl.DataFrame):
            return f"'{module}' DataFrame 데이터가 없습니다."
        pivoted = pivot_accounts(data)
        if "year" not in pivoted.columns:
            return "연도 데이터가 부족합니다."
        return df_to_md(growth_matrix(pivoted))

    def _yoy(module: str = "", **_kw) -> str:
        """전년대비 변동률."""
        if not module:
            return "module을 지정하세요."
        from dartlab.tools.table import pivot_accounts, yoy_change

        data = getattr(company, module, None)
        if not isinstance(data, pl.DataFrame):
            return f"'{module}' DataFrame 데이터가 없습니다."
        if "계정명" in data.columns:
            data = pivot_accounts(data)
        if "year" not in data.columns:
            return "year 컬럼이 없습니다."
        return df_to_md(yoy_change(data))

    def _anomalies(module: str = "", **_kw) -> str:
        """이상치 탐지."""
        if not module:
            return "module을 지정하세요."
        from dartlab.engines.ai.aiParser import detect_anomalies

        data = getattr(company, module, None)
        if not isinstance(data, pl.DataFrame):
            return f"'{module}' DataFrame 데이터가 없습니다."
        anomalies = detect_anomalies(data, use_llm=False, threshold_pct=50.0)
        if not anomalies:
            return f"'{module}'에서 이상치가 발견되지 않았습니다."
        return "\n".join(f"- [{a.severity}] {a.column} {a.year}: {a.description} (변동 {a.change_pct:+.1f}%)" for a in anomalies)

    def _report(apiType: str = "", **_kw) -> str:
        """정기보고서 정형 데이터."""
        if not apiType:
            return "apiType을 지정하세요."
        report = getattr(company, "report", None)
        if report is None:
            return "정기보고서 데이터가 없습니다."
        df = report.extract(apiType)
        if df is None:
            return f"'{apiType}' 데이터가 없습니다."
        return df_to_md(df)

    def _search(keyword: str = "", **_kw) -> str:
        """키워드로 모듈 데이터 검색."""
        if not keyword:
            return "keyword를 지정하세요."
        from dartlab.engines.ai.metadata import MODULE_META

        results: list[str] = []
        keywordLower = keyword.lower()
        for name, meta in MODULE_META.items():
            try:
                data = getattr(company, name, None)
                if data is None:
                    continue
                if isinstance(data, pl.DataFrame) and data.height > 0:
                    if "계정명" in data.columns:
                        matched = data.filter(pl.col("계정명").str.contains(f"(?i){keyword}"))
                        if matched.height > 0:
                            results.append(f"### {meta.label} (`{name}`) — {matched.height}건")
                            results.append(df_to_md(matched, max_rows=10))
            except (AttributeError, KeyError, RuntimeError, TypeError, ValueError):
                continue
        if not results:
            return f"'{keyword}'와 관련된 데이터를 찾지 못했습니다."
        return "\n\n".join(results)

    # ── dispatch ──
    _ACTIONS = {
        "data": _data,
        "modules": _modules,
        "ratios": _ratios,
        "growth": _growth,
        "yoy": _yoy,
        "anomalies": _anomalies,
        "report": _report,
        "search": _search,
    }

    def finance(action: str, module: str = "", apiType: str = "", keyword: str = "") -> str:
        """재무 데이터 통합 도구."""
        handler = _ACTIONS.get(action)
        if not handler:
            return f"알 수 없는 action: {action}. 가능: {', '.join(_ACTIONS.keys())}"
        return handler(module=module, apiType=apiType, keyword=keyword)

    # ── schema ──
    moduleSchema: dict[str, Any] = {
        "type": "string",
        "description": f"모듈명. {moduleDesc}" if moduleDesc else "모듈명 (예: BS, IS, CF, ratios)",
    }
    if moduleEnum:
        moduleSchema["enum"] = moduleEnum

    apiTypeSchema: dict[str, Any] = {
        "type": "string",
        "description": f"보고서 API 타입. {reportApiDesc}" if reportApiDesc else "보고서 API 타입 (예: dividend, employee)",
    }
    if reportApiEnum:
        apiTypeSchema["enum"] = reportApiEnum

    registerTool(
        "finance",
        finance,
        "재무 데이터 조회/분석. 재무제표, 비율, 성장률, 이상치, 정형 보고서 데이터 접근.\n"
        "action별 동작:\n"
        "- data: 모듈 데이터 조회 (module 필수)\n"
        "- modules: 사용 가능한 모듈 목록\n"
        "- ratios: 재무비율 자동 계산\n"
        "- growth: CAGR 성장률 (module 필수)\n"
        "- yoy: 전년대비 변동률 (module 필수)\n"
        "- anomalies: 이상치 탐지 (module 필수)\n"
        "- report: 정기보고서 정형 데이터 (apiType 필수)\n"
        "- search: 키워드로 데이터 검색 (keyword 필수)",
        {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["data", "modules", "ratios", "growth", "yoy", "anomalies", "report", "search"],
                    "description": "data=데이터조회, modules=목록, ratios=재무비율, growth=성장률, yoy=전년대비, anomalies=이상치, report=정형보고서, search=검색",
                },
                "module": moduleSchema,
                "apiType": apiTypeSchema,
                "keyword": {
                    "type": "string",
                    "description": "검색 키워드 (action=search일 때)",
                    "default": "",
                },
            },
            "required": ["action"],
        },
        category="finance",
        questionTypes=("건전성", "수익성", "성장성", "배당", "리스크", "종합"),
        priority=90,
    )
