"""Finance 도구 — 데이터 조회/비율/성장/YoY/이상치/요약/보고서."""

from __future__ import annotations

from typing import Any

import polars as pl

from .helpers import df_to_md, format_tool_value


def _unwrap_timeseries(ts: Any) -> dict | None:
    """timeseries가 (dict, list) tuple이면 dict만 꺼낸다."""
    if ts is None:
        return None
    if isinstance(ts, tuple):
        return ts[0] if ts else None
    return ts


def _build_company_data_bundle(company: Any):
    """Company → CompanyDataBundle 빌드 (안전하게 — 실패 시 빈 bundle)."""
    from dartlab.analysis.forecast.revenueForecast import CompanyDataBundle

    bundle = CompanyDataBundle()

    # 세그먼트 매출
    try:
        seg = getattr(company, "segments", None)
        if seg is not None:
            rev = getattr(seg, "revenue", None)
            if rev is not None and hasattr(rev, "columns"):
                bundle.segmentRevenue = rev
    except (AttributeError, TypeError):
        pass

    # 수주/매출 (salesOrder)
    try:
        so = getattr(company, "salesOrder", None)
        if so is not None:
            bundle.salesDf = getattr(so, "salesDf", None)
            bundle.orderDf = getattr(so, "orderDf", None)
    except (AttributeError, TypeError):
        pass

    # 수출비율 추출 시도 (salesOrder salesDf에서)
    try:
        if bundle.salesDf is not None and hasattr(bundle.salesDf, "columns"):
            df = bundle.salesDf
            if "label" in df.columns:
                labels = df["label"].to_list()
                for i, lab in enumerate(labels):
                    if lab and "수출" in str(lab):
                        # 첫 번째 값 컬럼에서 수출 비율 추출
                        val_cols = [c for c in df.columns if c != "label"]
                        if val_cols:
                            total_row = None
                            for j, l2 in enumerate(labels):
                                if l2 and "합계" in str(l2):
                                    total_row = j
                                    break
                            if total_row is not None:
                                export_val = df[val_cols[0]][i]
                                total_val = df[val_cols[0]][total_row]
                                if total_val and total_val > 0:
                                    bundle.export_ratio = float(export_val) / float(total_val)
                        break
    except (AttributeError, TypeError, IndexError, ZeroDivisionError):
        pass

    return bundle


def register_finance_tools(company: Any, register_tool) -> None:
    """재무 데이터 관련 도구를 등록한다."""
    from dartlab.core.capabilities import CapabilityKind

    # 0. list_modules
    def list_modules() -> str:
        """사용 가능한 데이터 모듈 목록을 반환한다."""
        from dartlab.ai.context.builder import scan_available_modules

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
        category="finance",
        priority=75,
    )

    # 1. get_data
    def get_data(module_name: str) -> str:
        """모듈명으로 재무/공시 데이터를 조회한다."""
        data = getattr(company, module_name, None) if hasattr(company, module_name) else company.show(module_name)
        if data is None:
            from dartlab.ai.metadata import MODULE_META

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

    # get_data 동적 enum: company에서 사용 가능한 모듈 목록 추출
    moduleEnum: list[str] = []
    try:
        from dartlab.ai.context.builder import scan_available_modules as _scanMods

        _mods = _scanMods(company)
        if _mods:
            moduleEnum = [m["name"] for m in _mods]
    except (ImportError, AttributeError, KeyError, TypeError, ValueError):
        pass
    moduleDesc = buildModuleDescription()
    moduleParamSchema: dict[str, Any] = {
        "type": "string",
        "description": f"조회할 모듈명. {moduleDesc}" if moduleDesc else "조회할 모듈명",
    }
    if moduleEnum:
        moduleParamSchema["enum"] = moduleEnum

    register_tool(
        "get_data",
        get_data,
        "기업의 재무/공시 데이터를 조회합니다. 모듈명을 모르면 먼저 `list_modules`를 호출하세요.",
        {
            "type": "object",
            "properties": {
                "module_name": moduleParamSchema,
            },
            "required": ["module_name"],
        },
        kind=CapabilityKind.DATA,
        requires_company=True,
        ai_hint="회사 바인딩 데이터 모듈 조회",
        category="finance",
        questionTypes=("건전성", "수익성", "성장성", "배당", "리스크", "종합"),
        priority=90,
        dependsOn=("list_modules",),
    )

    # 1b. search_data
    def search_data(keyword: str) -> str:
        """키워드로 모든 데이터 모듈을 검색한다."""
        from dartlab.ai.metadata import MODULE_META

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
        category="finance",
        priority=65,
    )

    # 2. compute_ratios
    def compute_ratios() -> str:
        """BS/IS 기반 핵심 재무비율을 계산한다."""
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
        category="finance",
        questionTypes=("건전성", "수익성", "종합"),
        priority=80,
    )

    # 3. find_anomalies
    def find_anomalies(module_name: str, threshold_pct: float = 50.0) -> str:
        """재무 데이터에서 이상치를 탐지한다."""
        from dartlab.ai.aiParser import detect_anomalies

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
        category="finance",
        questionTypes=("리스크",),
        priority=70,
    )

    # 4. compute_growth
    def compute_growth(module_name: str) -> str:
        """다기간 CAGR 성장률 매트릭스를 계산한다."""
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
        category="finance",
        questionTypes=("성장성",),
        priority=70,
    )

    # 5. yoy_analysis
    def yoy_analysis(module_name: str) -> str:
        """전년 대비 변동률을 계산한다."""
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
        category="finance",
        questionTypes=("성장성",),
        priority=65,
    )

    # 6. get_summary
    def get_summary(module_name: str) -> str:
        """데이터의 요약 통계를 계산한다."""
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
        category="finance",
        priority=55,
    )

    # 7b. get_report_data
    def get_report_data(api_type: str) -> str:
        """DART 정기보고서 API 정형 데이터를 조회한다."""
        report = getattr(company, "report", None)
        if report is None:
            return "정기보고서 데이터가 없습니다."
        df = report.extract(api_type)
        if df is None:
            from dartlab.providers.dart.report.types import API_TYPE_LABELS

            available = ", ".join(f"`{k}` ({v})" for k, v in list(API_TYPE_LABELS.items())[:10])
            return f"'{api_type}' 데이터가 없습니다. 사용 가능한 타입 예시: {available}"
        return df_to_md(df)

    # get_report_data 동적 enum: company.report에서 사용 가능한 API 타입 추출
    reportApiEnum: list[str] = []
    reportApiDesc = ""
    try:
        _report = getattr(company, "report", None)
        if _report is not None:
            _available = getattr(_report, "availableApiTypes", None)
            if _available:
                reportApiEnum = list(_available) if not isinstance(_available, list) else _available
        if reportApiEnum:
            from dartlab.providers.dart.report.types import API_TYPE_LABELS as _apiLabels

            reportApiDesc = ", ".join(f"{k}={_apiLabels.get(k, k)}" for k in reportApiEnum[:15])
    except (ImportError, AttributeError, KeyError, TypeError, ValueError):
        pass

    reportApiParamSchema: dict[str, Any] = {
        "type": "string",
        "description": f"조회할 API 타입. {reportApiDesc}"
        if reportApiDesc
        else "조회할 API 타입 (예: dividend, employee, majorHolder)",
    }
    if reportApiEnum:
        reportApiParamSchema["enum"] = reportApiEnum

    register_tool(
        "get_report_data",
        get_report_data,
        "DART 정기보고서 API의 표준화된 정형 데이터를 조회합니다. "
        "사용 시점: 배당·직원·임원·주주 등 정형화된 수치가 필요할 때. get_data(BS/IS)와는 다른 소스. "
        "사용하지 말 것: 공시 원문 텍스트가 필요하면 show_topic을 사용하세요.",
        {
            "type": "object",
            "properties": {
                "api_type": reportApiParamSchema,
            },
            "required": ["api_type"],
        },
        kind=CapabilityKind.DATA,
        requires_company=True,
        category="finance",
        questionTypes=("배당", "지배구조", "공시"),
        priority=75,
    )

    # compare_companies 제거 — Company N개 생성은 메모리 폭탄.
    # 기업간 비교는 market(action='scanAccount') / market(action='scanRatio')로 대체.

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
        category="finance",
        questionTypes=("건전성", "수익성"),
        priority=55,
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
        category="finance",
        priority=60,
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
        category="finance",
        questionTypes=("건전성", "수익성", "성장성"),
        priority=65,
    )

    # ── get_timeseries ──

    def get_timeseries(account: str, statement: str = "IS") -> str:
        """특정 계정의 분기별/연도별 시계열 조회."""
        ts = getattr(company, "timeseries", None)
        if ts is None:
            return "timeseries 데이터가 없습니다. get_data(IS/BS/CF)로 전체 재무제표를 조회하세요."
        if isinstance(ts, tuple):
            series, periods = ts
            sjData = series.get(statement, {})
            vals = sjData.get(account)
            if vals is None:
                available = list(sjData.keys())[:15]
                return f"'{statement}.{account}' 계정이 없습니다. 사용 가능: {available}"
            recentPeriods = periods[-20:]
            recentVals = vals[-20:]
            from dartlab.ai.context.formatting import _format_won

            lines = [f"## {account} ({statement}) 분기별 시계열", "| 기간 | 값 |", "| --- | --- |"]
            for p, v in zip(recentPeriods, recentVals):
                lines.append(f"| {p} | {_format_won(v) if v is not None else '-'} |")
            return "\n".join(lines)
        try:
            result = ts(account, statement) if callable(ts) else ts
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
        category="finance",
        priority=60,
    )

    # ── 밸류에이션 / 예측 도구 ──────────────────────────────

    def intrinsic_value(model: str = "all") -> str:
        """내재가치 추정 (DCF/DDM/상대가치)."""
        from dartlab.analysis.comparative.sector.params import getParams
        from dartlab.analysis.valuation.valuation import (
            dcfValuation,
            ddmValuation,
            fullValuation,
            relativeValuation,
        )

        series = _unwrap_timeseries(company.finance.timeseries)
        if not series:
            return "재무 시계열 데이터가 없습니다."

        sector_info = getattr(company, "sectorInfo", None)
        sp = getParams(sector_info) if sector_info else None

        mc = getattr(company, "marketCap", None)
        shares = getattr(company, "sharesOutstanding", None)
        price = getattr(company, "currentPrice", None)

        if model == "all":
            result = fullValuation(
                series,
                shares=shares,
                sector_params=sp,
                market_cap=mc,
                current_price=price,
            )
            parts = []
            if result.dcf:
                parts.append(repr(result.dcf))
            if result.ddm:
                parts.append(repr(result.ddm))
            if result.relative:
                parts.append(repr(result.relative))
            parts.append(repr(result))
            return "\n\n".join(parts)
        elif model == "dcf":
            result = dcfValuation(series, shares=shares, sector_params=sp, current_price=price)
            return repr(result)
        elif model == "ddm":
            result = ddmValuation(series, shares=shares, sector_params=sp, current_price=price)
            return repr(result)
        elif model == "relative":
            result = relativeValuation(series, sector_params=sp, market_cap=mc, shares=shares, current_price=price)
            return repr(result)
        else:
            return f"미지원 모델: {model}. 선택지: all, dcf, ddm, relative"

    register_tool(
        "intrinsic_value",
        intrinsic_value,
        "내재가치를 추정합니다. DCF(현금흐름할인), DDM(배당할인), 상대가치(섹터배수) 3가지 모델을 지원합니다. "
        "사용 시점: 적정 주가/기업가치 판단, 저평가/고평가 분석. "
        "model 파라미터: 'all'(종합), 'dcf', 'ddm', 'relative' 중 선택.",
        {
            "type": "object",
            "properties": {
                "model": {
                    "type": "string",
                    "description": "밸류에이션 모델 (all, dcf, ddm, relative)",
                    "default": "all",
                },
            },
        },
        kind=CapabilityKind.ANALYSIS,
        requires_company=True,
        category="valuation",
        questionTypes=("투자",),
        priority=85,
    )

    def forecast(metric: str = "revenue", horizon: str = "3") -> str:
        """시계열 예측."""
        from dartlab.analysis.comparative.sector.params import getParams
        from dartlab.analysis.forecast.forecast import forecastMetric as _fm

        series = _unwrap_timeseries(company.finance.timeseries)
        if not series:
            return "재무 시계열 데이터가 없습니다."

        sector_info = getattr(company, "sectorInfo", None)
        sp = getParams(sector_info) if sector_info else None

        result = _fm(series, metric=metric, horizon=int(horizon), sector_params=sp)
        return repr(result)

    register_tool(
        "forecast",
        forecast,
        "매출/영업이익/순이익/영업CF의 미래 값을 예측합니다. "
        "선형회귀, CAGR 감속, 평균 회귀 중 데이터에 맞는 방법을 자동 선택합니다. "
        "사용 시점: 미래 실적 전망, DCF 입력값 확인. "
        "metric: revenue(매출), operating_income(영업이익), net_income(순이익), operating_cashflow(영업CF).",
        {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "description": "예측 대상 (revenue, operating_income, net_income, operating_cashflow)",
                    "default": "revenue",
                },
                "horizon": {
                    "type": "string",
                    "description": "예측 기간 (년, 1~5)",
                    "default": "3",
                },
            },
        },
        kind=CapabilityKind.ANALYSIS,
        requires_company=True,
        category="valuation",
        questionTypes=("투자", "성장성"),
        priority=70,
    )

    def scenario(current_price: str = "") -> str:
        """시나리오 분석 (Bull/Base/Bear DCF)."""
        from dartlab.analysis.comparative.sector.params import getParams
        from dartlab.analysis.forecast.forecast import scenarioAnalysis as _sa

        series = _unwrap_timeseries(company.finance.timeseries)
        if not series:
            return "재무 시계열 데이터가 없습니다."

        sector_info = getattr(company, "sectorInfo", None)
        sp = getParams(sector_info) if sector_info else None
        shares = getattr(company, "sharesOutstanding", None)
        price = float(current_price) if current_price else getattr(company, "currentPrice", None)

        result = _sa(series, shares=shares, sector_params=sp, current_price=price)
        return repr(result)

    register_tool(
        "scenario",
        scenario,
        "Bull/Base/Bear 3개 시나리오별 DCF 분석을 수행하고 확률 가중 적정가치를 산출합니다. "
        "사용 시점: 투자 의사결정 시 다양한 가능성 검토, 리스크-보상 분석.",
        {
            "type": "object",
            "properties": {
                "current_price": {
                    "type": "string",
                    "description": "현재 주가 (원, 선택사항)",
                    "default": "",
                },
            },
        },
        kind=CapabilityKind.ANALYSIS,
        requires_company=True,
        category="valuation",
        questionTypes=("투자",),
        priority=75,
    )

    def sensitivity(wacc_range: str = "2", growth_range: str = "1") -> str:
        """민감도 분석 (WACC × 영구성장률 매트릭스)."""
        from dartlab.analysis.comparative.sector.params import getParams
        from dartlab.analysis.forecast.forecast import sensitivityAnalysis as _sens

        series = _unwrap_timeseries(company.finance.timeseries)
        if not series:
            return "재무 시계열 데이터가 없습니다."

        sector_info = getattr(company, "sectorInfo", None)
        sp = getParams(sector_info) if sector_info else None
        shares = getattr(company, "sharesOutstanding", None)

        result = _sens(
            series,
            shares=shares,
            sector_params=sp,
            wacc_range=float(wacc_range),
            growth_range=float(growth_range),
        )
        return repr(result)

    register_tool(
        "sensitivity",
        sensitivity,
        "WACC와 영구성장률 조합에 따른 주당 내재가치 민감도 테이블을 생성합니다. "
        "사용 시점: DCF 결과의 핵심 가정 변화에 따른 가치 변동 확인.",
        {
            "type": "object",
            "properties": {
                "wacc_range": {
                    "type": "string",
                    "description": "WACC ± 범위 (%p, 기본 2)",
                    "default": "2",
                },
                "growth_range": {
                    "type": "string",
                    "description": "영구성장률 ± 범위 (%p, 기본 1)",
                    "default": "1",
                },
            },
        },
        kind=CapabilityKind.ANALYSIS,
        requires_company=True,
        category="valuation",
        questionTypes=("투자",),
        priority=60,
    )

    # ── 경제 시나리오 시뮬레이션 도구 ──────────────────────────

    def economic_forecast(scenario: str = "all") -> str:
        """거시경제 시나리오별 실적 시뮬레이션."""
        from dartlab.analysis.comparative.sector.params import getParams
        from dartlab.analysis.forecast.simulation import (
            PRESET_SCENARIOS,
            simulateAllScenarios,
            simulateScenario,
        )

        series = _unwrap_timeseries(company.finance.timeseries)
        if not series:
            return "재무 시계열 데이터가 없습니다."

        sector_info = getattr(company, "sectorInfo", None)
        sp = getParams(sector_info) if sector_info else None
        shares = getattr(company, "sharesOutstanding", None)
        sector_key = sector_info.get("sector", None) if sector_info else None

        if scenario == "all":
            results = simulateAllScenarios(
                series,
                sector_key=sector_key,
                sector_params=sp,
                shares=shares,
            )
            lines = []
            for name, r in results.items():
                lines.append(repr(r))
                lines.append("")
            return "\n".join(lines)

        if scenario in PRESET_SCENARIOS:
            result = simulateScenario(
                series,
                scenario=scenario,
                sector_key=sector_key,
                sector_params=sp,
                shares=shares,
            )
            return repr(result)

        return f"알 수 없는 시나리오: {scenario}. 사용 가능: {', '.join(PRESET_SCENARIOS.keys())}"

    register_tool(
        "economic_forecast",
        economic_forecast,
        "거시경제 시나리오(GDP/금리/환율)에 따른 3년 실적 시뮬레이션을 수행합니다. "
        "업종별 경기감응도(β)를 자동 적용하여 매출·영업이익·FCF 경로를 추정합니다. "
        "사용 시점: 경기침체/금리인상/중국둔화 등 거시 변수가 기업에 미치는 영향 분석. "
        "사전 정의 시나리오: baseline(기준), adverse(경기침체), china_slowdown(중국둔화), "
        "rate_hike(금리인상), semiconductor_down(반도체불황), all(전체).",
        {
            "type": "object",
            "properties": {
                "scenario": {
                    "type": "string",
                    "description": "시나리오 이름 (baseline/adverse/china_slowdown/rate_hike/semiconductor_down/all)",
                    "default": "all",
                },
            },
        },
        kind=CapabilityKind.ANALYSIS,
        requires_company=True,
        category="valuation",
        questionTypes=("리스크", "투자"),
        priority=65,
    )

    def monte_carlo(scenario: str = "baseline", iterations: str = "10000") -> str:
        """Monte Carlo 확률 분포 예측."""
        from dartlab.analysis.comparative.sector.params import getParams
        from dartlab.analysis.forecast.simulation import monteCarloForecast

        series = _unwrap_timeseries(company.finance.timeseries)
        if not series:
            return "재무 시계열 데이터가 없습니다."

        sector_info = getattr(company, "sectorInfo", None)
        sp = getParams(sector_info) if sector_info else None
        shares = getattr(company, "sharesOutstanding", None)
        sector_key = sector_info.get("sector", None) if sector_info else None

        result = monteCarloForecast(
            series,
            sector_key=sector_key,
            sector_params=sp,
            shares=shares,
            scenario=scenario,
            iterations=int(iterations),
        )
        return repr(result)

    register_tool(
        "monte_carlo",
        monte_carlo,
        "Monte Carlo 시뮬레이션으로 매출/영업이익/FCF의 확률 분포(5th~95th 백분위)를 산출합니다. "
        "10,000회 반복으로 기업 실적의 변동성과 위험을 정량화합니다. "
        "사용 시점: 단일 점 추정이 아닌 확률적 범위로 실적 예측이 필요할 때.",
        {
            "type": "object",
            "properties": {
                "scenario": {
                    "type": "string",
                    "description": "기반 거시경제 시나리오 (baseline/adverse/china_slowdown/rate_hike/semiconductor_down)",
                    "default": "baseline",
                },
                "iterations": {
                    "type": "string",
                    "description": "시뮬레이션 반복 횟수 (기본 10000)",
                    "default": "10000",
                },
            },
        },
        kind=CapabilityKind.ANALYSIS,
        requires_company=True,
        category="valuation",
        questionTypes=("리스크", "투자"),
        priority=55,
    )

    def stress_test_tool(scenario: str = "adverse") -> str:
        """CCAR 스타일 스트레스 테스트."""
        from dartlab.analysis.comparative.sector.params import getParams
        from dartlab.analysis.forecast.simulation import stressTest as _st

        series = _unwrap_timeseries(company.finance.timeseries)
        if not series:
            return "재무 시계열 데이터가 없습니다."

        sector_info = getattr(company, "sectorInfo", None)
        sp = getParams(sector_info) if sector_info else None
        sector_key = sector_info.get("sector", None) if sector_info else None

        result = _st(
            series,
            sector_key=sector_key,
            sector_params=sp,
            scenario=scenario,
        )
        return repr(result)

    register_tool(
        "stress_test",
        stress_test_tool,
        "CCAR 스타일 스트레스 테스트를 수행하여 경기침체 시 기업의 생존 가능성을 평가합니다. "
        "3년간 매출/마진 변화, 부채비율 추이, 배당 지속 가능성, 생존 위험도를 산출합니다. "
        "사용 시점: 극단적 경제 상황에서 기업의 재무 복원력 평가.",
        {
            "type": "object",
            "properties": {
                "scenario": {
                    "type": "string",
                    "description": "스트레스 시나리오 (adverse/china_slowdown/semiconductor_down 등)",
                    "default": "adverse",
                },
            },
        },
        kind=CapabilityKind.ANALYSIS,
        requires_company=True,
        category="valuation",
        questionTypes=("리스크",),
        priority=60,
    )

    # ── Pro-Forma 재무제표 예측 ──

    def proforma_forecast(
        growth: str = "5,4,3,2.5,2",
        scenario_name: str = "base",
    ) -> str:
        """3-Statement Pro-Forma 재무제표 생성 (IS→BS→CF 연결 모델)."""
        from dartlab.analysis.forecast.proforma import build_proforma as _build

        series = _unwrap_timeseries(company.finance.timeseries)
        if not series:
            return "재무 시계열 데이터가 없습니다."

        growth_path = [float(g.strip()) for g in growth.split(",")]

        market_info = getattr(company, "market", None)
        market_cap = None
        if market_info and hasattr(market_info, "get"):
            market_cap = market_info.get("marketCap")

        result = _build(
            series,
            revenue_growth_path=growth_path,
            market_cap=market_cap,
            scenario_name=scenario_name,
        )
        return repr(result)

    register_tool(
        "proforma_forecast",
        proforma_forecast,
        "3-Statement Pro-Forma 재무제표를 생성합니다. 과거 비율(중위값) 기반으로 "
        "IS→BS→CF 연결 모델을 구축하고 BS 균형을 검증합니다. "
        "매출 성장 경로를 입력하면 5년간 예측 재무제표가 생성됩니다. "
        "사용 시점: 기업의 미래 재무 상태 시뮬레이션, 투자 분석.",
        {
            "type": "object",
            "properties": {
                "growth": {
                    "type": "string",
                    "description": "연도별 매출 성장률(%), 콤마 구분. 예: '5,4,3,2.5,2'",
                    "default": "5,4,3,2.5,2",
                },
                "scenario_name": {
                    "type": "string",
                    "description": "시나리오 이름 (예: base, optimistic, pessimistic)",
                    "default": "base",
                },
            },
        },
        kind=CapabilityKind.ANALYSIS,
        requires_company=True,
        category="valuation",
        questionTypes=("투자", "성장성"),
        priority=65,
    )

    # ── 매출 앙상블 예측 (7-소스 v3) ──

    def forecast_revenue_tool(horizon: str = "3") -> str:
        """매출 앙상블 예측 v3 — 7소스 + 세그먼트 + 시나리오."""
        from dartlab.analysis.forecast.revenueForecast import (
            forecastRevenue as _fr,
        )

        series = _unwrap_timeseries(company.finance.timeseries)
        if not series:
            return "재무 시계열 데이터가 없습니다."

        stock_code = getattr(company.profile, "stockCode", None) if hasattr(company, "profile") else None
        sector_info = getattr(company, "sectorInfo", None)
        sector_key = sector_info.get("sector", None) if sector_info else None
        market = getattr(company, "market", "KR") or "KR"

        # CompanyDataBundle 빌드 — L1 데이터를 L0에 전달
        bundle = _build_company_data_bundle(company)

        result = _fr(
            series,
            stock_code=stock_code,
            sector_key=sector_key,
            market=market,
            horizon=int(horizon),
            company_data=bundle,
        )

        lines = [repr(result)]

        # 시나리오
        if result.scenarios:
            lines.append("\n## 시나리오 (Base/Bull/Bear)")
            for name, vals in result.scenarios.items():
                prob = result.scenarioProbabilities.get(name, 0)
                vals_str = ", ".join(f"{v / 1e8:,.0f}억" for v in vals)
                lines.append(f"- **{name.title()}** ({prob:.0%}): {vals_str}")

        # 세그먼트
        if result.segmentForecasts:
            lines.append("\n## 세그먼트 Bottom-Up")
            for sf in result.segmentForecasts:
                proj_str = ", ".join(f"{v / 1e8:,.0f}억" for v in sf.projected)
                lines.append(f"- {sf.name}: {proj_str} (lifecycle={sf.lifecycle})")

        # 수주잔고
        if result.backlogSignal:
            bs = result.backlogSignal
            lines.append(
                f"\n## 수주잔고 시그널: {bs.brRatioTrend} (B/R={bs.backlogRevenueRatio:.2f}, 내재성장={bs.impliedRevenueGrowth:.1f}%)"
            )

        # AI 컨텍스트
        if result.aiContext:
            ctx = result.aiContext
            lines.append("\n## AI 보정 참고 컨텍스트")
            if ctx.get("lifecycle"):
                lines.append(f"- 라이프사이클: {ctx['lifecycle']}")
            if ctx.get("roic_growth") is not None:
                lines.append(f"- ROIC 내재 성장률: {ctx['roic_growth']}%")
            if ctx.get("roic_ts_gap") is not None:
                lines.append(f"- ROIC vs 시계열 괴리: {ctx['roic_ts_gap']:+}%p")
            if ctx.get("consensus_vs_ts_gap") is not None:
                lines.append(f"- 컨센서스 vs 시계열 괴리: {ctx['consensus_vs_ts_gap']:+}%p")
            if ctx.get("uncertainty_flags"):
                lines.append(f"- 불확실성: {', '.join(ctx['uncertainty_flags'])}")

        if result.forwardTestKey:
            lines.append(f"\n> Forward test key: `{result.forwardTestKey}`")

        return "\n".join(lines)

    register_tool(
        "forecast_revenue",
        forecast_revenue_tool,
        "매출 앙상블 예측 v3. 7소스(시계열+컨센서스+ROIC+매크로+세그먼트+수주잔고+환율) 결합. "
        "세그먼트 Bottom-Up 예측, 3-시나리오(Base/Bull/Bear) 출력, 수주잔고 선행지표 포함. "
        "사용 시점: 매출 전망, 성장성 평가, 밸류에이션 입력. "
        "forecast 도구와의 차이: forecast는 단일 시계열, forecast_revenue는 다중 소스 앙상블.",
        {
            "type": "object",
            "properties": {
                "horizon": {
                    "type": "string",
                    "description": "예측 기간 (년, 1~5)",
                    "default": "3",
                },
            },
        },
        kind=CapabilityKind.ANALYSIS,
        requires_company=True,
        category="valuation",
        questionTypes=("투자", "성장성"),
        priority=80,
    )

    # ── 확률 가중 주가 목표가 ──

    def price_target_tool(
        current_price: str = "",
        shares: str = "",
        mc_iterations: str = "5000",
    ) -> str:
        """5개 매크로 시나리오 × Pro-Forma → DCF → Monte Carlo → 확률 가중 목표가."""
        from dartlab.analysis.valuation.pricetarget import compute_price_target as _cpt

        series = _unwrap_timeseries(company.finance.timeseries)
        if not series:
            return "재무 시계열 데이터가 없습니다."

        sector_info = getattr(company, "sectorInfo", None)
        sector_key = sector_info.get("sector", None) if sector_info else None

        market_info = getattr(company, "market", None)
        market_cap = None
        cp = None
        sh = None
        if market_info and hasattr(market_info, "get"):
            market_cap = market_info.get("marketCap")
            cp = market_info.get("closePrice") or market_info.get("price")
            sh = market_info.get("sharesOutstanding") or market_info.get("listedShares")

        # 사용자 입력 우선
        if current_price:
            cp = float(current_price)
        if shares:
            sh = int(shares)

        # v2: ContextSignals 수집 (Company 객체에서)
        context_signals = None
        try:
            from dartlab.analysis.forecast.prediction import collectSignals as _cs

            context_signals = _cs(company)
        except (ImportError, TypeError):
            pass

        result = _cpt(
            series,
            sector_key=sector_key,
            current_price=cp,
            shares=sh,
            market_cap=market_cap,
            mc_iterations=int(mc_iterations),
            context_signals=context_signals,
        )
        return repr(result)

    register_tool(
        "price_target",
        price_target_tool,
        "확률 가중 주가 목표가를 산출합니다. 5개 매크로 시나리오(기준/금리인상/중국둔화/반도체하강/경기침체)별 "
        "Pro-Forma 재무제표 → DCF 밸류에이션 → Monte Carlo 5000회 시뮬레이션을 수행합니다. "
        "P10~P90 분포, 현재가 대비 업사이드, 투자 신호(strong_buy~strong_sell)를 제공합니다. "
        "사용 시점: 종합적인 주가 분석, 매수/매도 판단 근거 도출.",
        {
            "type": "object",
            "properties": {
                "current_price": {
                    "type": "string",
                    "description": "현재 주가(원). 빈 문자열이면 market 데이터에서 자동 조회.",
                    "default": "",
                },
                "shares": {
                    "type": "string",
                    "description": "발행주식수. 빈 문자열이면 market 데이터에서 자동 조회.",
                    "default": "",
                },
                "mc_iterations": {
                    "type": "string",
                    "description": "Monte Carlo 반복 횟수 (기본 5000)",
                    "default": "5000",
                },
            },
        },
        kind=CapabilityKind.ANALYSIS,
        requires_company=True,
        category="valuation",
        questionTypes=("투자",),
        priority=85,
    )

    # ── run_simulation ──

    def run_simulation(scenarios: str = "") -> str:
        """경제 시나리오 시뮬레이션."""
        ts = getattr(company.finance, "timeseries", None) if hasattr(company, "finance") else None
        ts = _unwrap_timeseries(ts)
        if ts is None:
            return "시계열 데이터가 없어 시뮬레이션을 실행할 수 없습니다."
        try:
            from dartlab.analysis.forecast.simulation import simulateAllScenarios

            scenarioList = [s.strip() for s in scenarios.split(",") if s.strip()] or None
            result = simulateAllScenarios(
                ts,
                sectorKey=getattr(company, "sectorKey", None),
                scenarios=scenarioList,
            )
            return repr(result) if result else "시뮬레이션 결과가 없습니다."
        except (ImportError, KeyError, OSError, RuntimeError, TypeError, ValueError) as e:
            return f"시뮬레이션 실패: {e}"

    register_tool(
        "run_simulation",
        run_simulation,
        "경제 시나리오 시뮬레이션을 실행합니다. "
        "기준/금리인상/금리인하/경기침체/기술하강 등 매크로 시나리오별 재무 영향을 추정합니다. "
        "사용 시점: '경기침체 시 이 회사는?', '금리 인상 영향', '시나리오 분석' 질문. "
        "사용하지 말 것: 과거 실적 분석에는 compute_ratios/get_data가 적절합니다.",
        {
            "type": "object",
            "properties": {
                "scenarios": {
                    "type": "string",
                    "description": "시나리오 이름 (쉼표 구분). 비워두면 전체 프리셋. 예: baseline,adverse,rate_hike",
                    "default": "",
                },
            },
        },
        kind=CapabilityKind.ANALYSIS,
        requires_company=True,
        category="valuation",
        questionTypes=("투자", "종합"),
        priority=70,
    )
