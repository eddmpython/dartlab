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

    # ── compare_companies ──

    def compare_companies(codes: str, metrics: str = "revenue,operating_income,net_income,total_assets,roe") -> str:
        """복수 종목 핵심 지표 비교표를 생성합니다."""
        from dartlab import Company as _Company

        code_list = [c.strip() for c in codes.split(",") if c.strip()]
        metric_list = [m.strip() for m in metrics.split(",") if m.strip()]
        if len(code_list) < 2:
            return "비교하려면 2개 이상의 종목코드를 쉼표로 구분해 주세요."

        rows: list[dict] = []
        for code in code_list[:5]:
            try:
                c = _Company(code)
                row: dict = {"종목": f"{c.corpName} ({c.stockCode})"}
                ratios = getattr(c, "ratios", None)
                if ratios is not None and isinstance(ratios, pl.DataFrame):
                    for m in metric_list:
                        matched = ratios.filter(pl.col("항목") == m)
                        if not matched.is_empty():
                            cols = [c for c in matched.columns if c != "항목"]
                            if cols:
                                row[m] = str(matched[cols[-1]][0])
                rows.append(row)
            except (ValueError, FileNotFoundError, OSError):
                rows.append({"종목": code, "error": "데이터 없음"})

        if not rows:
            return "비교 데이터를 찾을 수 없습니다."
        result_df = pl.DataFrame(rows)
        return df_to_md(result_df)

    register_tool(
        "compare_companies",
        compare_companies,
        "복수 종목의 핵심 재무 지표를 비교 테이블로 생성합니다. "
        "사용자가 '삼성전자 vs SK하이닉스', '종목 비교', '어떤 회사가 나은지' 같은 요청을 할 때 사용하세요.",
        {
            "type": "object",
            "properties": {
                "codes": {
                    "type": "string",
                    "description": "비교할 종목코드/종목명을 쉼표로 구분 (예: 005930,000660,035420)",
                },
                "metrics": {
                    "type": "string",
                    "description": "비교할 지표를 쉼표로 구분. 기본: revenue,operating_income,net_income,total_assets,roe",
                    "default": "revenue,operating_income,net_income,total_assets,roe",
                },
            },
            "required": ["codes"],
        },
        kind=CapabilityKind.ANALYSIS,
    )

    # ── custom_ratio ──

    def custom_ratio(numerator: str, denominator: str, label: str = "사용자정의비율") -> str:
        """사용자 정의 재무비율을 계산합니다."""
        if company is None:
            return "회사를 먼저 선택하세요."
        try:
            ts = getattr(company, "timeseries", None)
            if ts is None or not isinstance(ts, dict):
                return "시계열 데이터가 없습니다."
            num_data = ts.get(numerator)
            den_data = ts.get(denominator)
            if num_data is None:
                return f"'{numerator}' 계정을 찾을 수 없습니다."
            if den_data is None:
                return f"'{denominator}' 계정을 찾을 수 없습니다."

            results: list[dict] = []
            for period in sorted(set(num_data.keys()) & set(den_data.keys())):
                n, d = num_data[period], den_data[period]
                if n is not None and d is not None and d != 0:
                    results.append({"기간": period, label: round(n / d * 100, 2)})
            if not results:
                return "계산 가능한 기간이 없습니다."
            return df_to_md(pl.DataFrame(results))
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            return f"비율 계산 실패: {e}"

    register_tool(
        "custom_ratio",
        custom_ratio,
        "사용자 정의 재무비율을 계산합니다. 분자/분모 계정명을 지정하면 기간별 비율(%)을 반환합니다. "
        "사용자가 '연구개발비/매출 비율', '인건비/영업이익' 같은 커스텀 비율을 요청할 때 사용하세요.",
        {
            "type": "object",
            "properties": {
                "numerator": {"type": "string", "description": "분자 계정명 (예: research_development)"},
                "denominator": {"type": "string", "description": "분모 계정명 (예: revenue)"},
                "label": {"type": "string", "description": "결과 컬럼 라벨", "default": "사용자정의비율"},
            },
            "required": ["numerator", "denominator"],
        },
        kind=CapabilityKind.ANALYSIS,
        requires_company=True,
    )

    # ── timeseries_filter ──

    def timeseries_filter(account: str, since: str = "", until: str = "") -> str:
        """특정 계정의 시계열 데이터를 기간 필터링하여 반환한다."""
        if company is None:
            return "회사를 먼저 선택하세요."
        try:
            ts = getattr(company, "timeseries", None)
            if ts is None or not isinstance(ts, dict):
                return "시계열 데이터가 없습니다."
            data = ts.get(account)
            if data is None:
                available = ", ".join(list(ts.keys())[:20])
                return f"'{account}' 계정을 찾을 수 없습니다. 사용 가능: {available}"

            rows: list[dict] = []
            for period in sorted(data.keys()):
                if since and period < since:
                    continue
                if until and period > until:
                    continue
                val = data[period]
                if val is not None:
                    rows.append({"기간": period, account: val})
            if not rows:
                return f"'{account}' 계정의 해당 기간 데이터가 없습니다."
            return df_to_md(pl.DataFrame(rows))
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            return f"시계열 필터 실패: {e}"

    register_tool(
        "timeseries_filter",
        timeseries_filter,
        "특정 계정의 시계열 데이터를 기간 범위로 필터링하여 반환합니다. "
        "사용자가 '최근 3년 매출 추이', '2020년부터 영업이익', '특정 계정 시계열' 같은 요청을 할 때 사용하세요. "
        "account는 계정명(snakeId), since/until은 기간 필터(예: 2020, 2022Q2)입니다.",
        {
            "type": "object",
            "properties": {
                "account": {"type": "string", "description": "계정명 (예: revenue, operating_income, total_assets)"},
                "since": {"type": "string", "description": "시작 기간 (예: 2020, 2021Q1)", "default": ""},
                "until": {"type": "string", "description": "종료 기간 (예: 2024, 2024Q4)", "default": ""},
            },
            "required": ["account"],
        },
        kind=CapabilityKind.ANALYSIS,
        requires_company=True,
    )

    # ── get_ratio_series ──

    def get_ratio_series(ratio: str = "") -> str:
        """재무비율 시계열 조회."""
        rs = getattr(company, "ratioSeries", None)
        if rs is None:
            return "ratioSeries 데이터가 없습니다. compute_ratios()로 현재 비율을 확인하세요."
        if ratio:
            val = rs.get(ratio) if isinstance(rs, dict) else getattr(rs, ratio, None)
            if val is None:
                available = list(rs.keys()) if isinstance(rs, dict) else dir(rs)
                return f"'{ratio}' 비율이 없습니다. 사용 가능: {', '.join(str(k) for k in available[:20])}"
            return format_tool_value(val, max_rows=20, max_chars=3000)
        return format_tool_value(rs, max_rows=30, max_chars=4000)

    register_tool(
        "get_ratio_series",
        get_ratio_series,
        "재무비율의 연도별 시계열 데이터를 조회합니다. "
        "ratio를 지정하면 해당 비율만, 비워두면 전체 비율 시계열을 반환합니다. "
        "사용 시점: '부채비율 추이', 'ROE 3년간 변화', '비율 트렌드' 같은 추세 분석. "
        "사용하지 말 것: 현재 시점 비율만 필요하면 compute_ratios가 빠릅니다.",
        {
            "type": "object",
            "properties": {
                "ratio": {
                    "type": "string",
                    "description": "조회할 비율명 (예: roe, debtRatio, currentRatio). 비워두면 전체",
                    "default": "",
                },
            },
        },
        kind=CapabilityKind.DATA,
        requires_company=True,
    )

    # ── get_timeseries ──

    def get_timeseries(account: str, statement: str = "IS") -> str:
        """특정 계정의 분기별/연도별 시계열 조회."""
        ts_func = getattr(company, "timeseries", None)
        if ts_func is None:
            return "timeseries 인터페이스가 없습니다. get_data(IS/BS/CF)로 전체 재무제표를 조회하세요."
        try:
            result = ts_func(account, statement) if callable(ts_func) else ts_func
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            return f"timeseries('{account}', '{statement}') 실패: {e}"
        return format_tool_value(result, max_rows=20, max_chars=3000)

    register_tool(
        "get_timeseries",
        get_timeseries,
        "특정 계정과목의 분기별/연도별 시계열을 조회합니다. "
        "예: get_timeseries('sales', 'IS') → 매출액 분기별 시계열. "
        "사용 시점: 특정 계정의 세밀한 추이 분석, 분기별 패턴 확인. "
        "사용하지 말 것: 전체 재무제표가 필요하면 get_data(IS/BS/CF)를 사용하세요.",
        {
            "type": "object",
            "properties": {
                "account": {
                    "type": "string",
                    "description": "계정명 (snakeId, 예: sales, operating_profit, total_assets, net_income)",
                },
                "statement": {
                    "type": "string",
                    "description": "재무제표 유형 (IS, BS, CF)",
                    "default": "IS",
                },
            },
            "required": ["account"],
        },
        kind=CapabilityKind.DATA,
        requires_company=True,
    )
