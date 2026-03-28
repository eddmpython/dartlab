"""finance Super Tool — 재무 데이터 통합 dispatcher.

통합 대상: get_data, list_modules, compute_ratios, compute_growth,
yoy_analysis, detect_anomalies, get_report_data, search_data, quality, decompose
"""

from __future__ import annotations

from typing import Any

import polars as pl

from ..defaults.helpers import df_to_md


def registerFinanceTool(company: Any, registerTool) -> None:
    """finance Super Tool 등록."""

    # ── 동적 enum: 모듈 목록 ──
    moduleEnum: list[str] = []
    moduleDesc = ""
    try:
        from dartlab.ai.context.builder import scan_available_modules

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
            from dartlab.providers.dart.report.types import API_TYPE_LABELS

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
            return f"[데이터 없음] '{module}' 데이터가 없습니다. 대안: finance(action='modules')로 사용 가능한 목록을 확인하세요."
        if isinstance(data, pl.DataFrame):
            return df_to_md(data)
        if isinstance(data, dict):
            return "\n".join(f"- {k}: {v}" for k, v in data.items())
        if isinstance(data, list):
            return "\n".join(f"- {item}" for item in data[:20])
        return str(data)[:2000]

    def _modules(**_kw) -> str:
        """사용 가능한 모듈 목록."""
        from dartlab.ai.context.builder import scan_available_modules

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
            return f"[데이터 없음] '{module}' DataFrame 데이터가 없습니다. 대안: finance(action='modules')로 사용 가능한 목록을 확인하세요."
        pivoted = pivot_accounts(data)
        if "year" not in pivoted.columns:
            return "연도 데이터가 부족합니다. 대안: finance(action='data', module='IS')로 원본 데이터를 확인하세요."
        return df_to_md(growth_matrix(pivoted))

    def _yoy(module: str = "", **_kw) -> str:
        """전년대비 변동률."""
        if not module:
            return "module을 지정하세요."
        from dartlab.tools.table import pivot_accounts, yoy_change

        data = getattr(company, module, None)
        if not isinstance(data, pl.DataFrame):
            return f"[데이터 없음] '{module}' DataFrame 데이터가 없습니다. 대안: finance(action='modules')로 사용 가능한 목록을 확인하세요."
        if "계정명" in data.columns:
            data = pivot_accounts(data)
        if "year" not in data.columns:
            return "year 컬럼이 없습니다."
        return df_to_md(yoy_change(data))

    def _anomalies(module: str = "", **_kw) -> str:
        """이상치 탐지."""
        if not module:
            return "module을 지정하세요."
        from dartlab.ai.aiParser import detect_anomalies

        data = getattr(company, module, None)
        if not isinstance(data, pl.DataFrame):
            return f"[데이터 없음] '{module}' DataFrame 데이터가 없습니다. 대안: finance(action='modules')로 사용 가능한 목록을 확인하세요."
        anomalies = detect_anomalies(data, use_llm=False, threshold_pct=50.0)
        if not anomalies:
            return f"'{module}'에서 이상치가 발견되지 않았습니다."
        return "\n".join(
            f"- [{a.severity}] {a.column} {a.year}: {a.description} (변동 {a.change_pct:+.1f}%)" for a in anomalies
        )

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
        from dartlab.ai.metadata import MODULE_META

        results: list[str] = []
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
            return f"[데이터 없음] '{keyword}'와 관련된 재무 데이터가 없습니다. 대안: explore(action='search', keyword='{keyword}')로 공시 원문을 검색하세요."
        return "\n\n".join(results)

    def _quality(**_kw) -> str:
        """이익의 질 종합 분석."""
        from dartlab.ai.context.company_adapter import get_headline_ratios

        r = get_headline_ratios(company)
        if r is None:
            return "[데이터 없음] 재무비율 계산 불가."
        lines = ["## 이익의 질 (Earnings Quality)"]
        accrual = getattr(r, "sloanAccrualRatio", None)
        if accrual is not None:
            lbl = "양호" if abs(accrual) < 5 else ("주의" if abs(accrual) < 10 else "위험")
            lines.append(f"- **Accrual Ratio**: {accrual:.1f}% ({lbl}) -- |값|<5% 양호, >10% 이익 과대 의심")
        ocfNi = getattr(r, "operatingCfToNetIncome", None)
        if ocfNi is not None:
            lbl = "양호" if ocfNi >= 100 else ("보통" if ocfNi >= 50 else "주의")
            lines.append(f"- **영업CF/순이익**: {ocfNi:.0f}% ({lbl}) -- >=100% 양호")
        beneish = getattr(r, "beneishMScore", None)
        if beneish is not None:
            lbl = "정상" if beneish < -1.78 else "조작의심"
            lines.append(f"- **Beneish M-Score**: {beneish:.2f} ({lbl}) -- <-1.78 정상")
        ccc = getattr(r, "ccc", None)
        dso = getattr(r, "dso", None)
        dio = getattr(r, "dio", None)
        dpo = getattr(r, "dpo", None)
        if ccc is not None:
            parts = []
            if dso is not None:
                parts.append(f"DSO:{dso:.0f}")
            if dio is not None:
                parts.append(f"DIO:{dio:.0f}")
            if dpo is not None:
                parts.append(f"DPO:{dpo:.0f}")
            detail = f" ({' + '.join(parts)})" if parts else ""
            lines.append(f"- **CCC**: {ccc:.0f}일{detail}")
        wc = getattr(r, "workingCapital", None)
        if wc is not None:
            from dartlab.ai.context.formatting import _format_won

            lines.append(f"- **운전자본**: {_format_won(wc)}")
        if len(lines) == 1:
            return "[데이터 없음] 이익의 질 지표 계산 불가."
        return "\n".join(lines)

    def _decompose(**_kw) -> str:
        """DuPont 3요소 분해 시계열."""
        from dartlab.ai.context.company_adapter import get_ratio_series

        rs = get_ratio_series(company)
        if rs is None:
            return "[데이터 없음] 비율 시계열 없음."
        periods = getattr(rs, "periods", None)
        roe_s = getattr(rs, "roe", None)
        dm_s = getattr(rs, "dupontMargin", None)
        dt_s = getattr(rs, "dupontTurnover", None)
        dl_s = getattr(rs, "dupontLeverage", None)
        if not roe_s or not dm_s or not dt_s or not dl_s:
            return "[데이터 없음] DuPont 분해 시계열이 부족합니다."
        lines = [
            "## DuPont 분해 시계열",
            "| 기간 | ROE | 순이익률 | 자산회전율 | 레버리지 |",
            "| --- | --- | --- | --- | --- |",
        ]
        n = min(len(roe_s), len(dm_s), len(dt_s), len(dl_s))
        for i in range(n):
            period = periods[i] if periods and i < len(periods) else f"T{i}"
            r_val = f"{roe_s[i]:.1f}%" if roe_s[i] is not None else "-"
            m_val = f"{dm_s[i]:.1f}%" if dm_s[i] is not None else "-"
            t_val = f"{dt_s[i]:.2f}x" if dt_s[i] is not None else "-"
            l_val = f"{dl_s[i]:.2f}x" if dl_s[i] is not None else "-"
            lines.append(f"| {period} | {r_val} | {m_val} | {t_val} | {l_val} |")
        return "\n".join(lines)

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
        "quality": _quality,
        "decompose": _decompose,
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
        "description": f"보고서 API 타입. {reportApiDesc}"
        if reportApiDesc
        else "보고서 API 타입 (예: dividend, employee)",
    }
    if reportApiEnum:
        apiTypeSchema["enum"] = reportApiEnum

    registerTool(
        "finance",
        finance,
        "재무 숫자 데이터 조회/분석 — 재무제표(IS/BS/CF), 재무비율, 성장률, 배당, 임원보수 등.\n"
        "\n"
        "✓ 이 도구를 쓰는 경우: 매출, 영업이익, ROE, 부채비율 등 숫자 기반 재무 질문\n"
        "✓ 배당·최대주주·임원보수 → finance(action='report', apiType='dividend/majorHolder/executive')\n"
        "✗ 이 도구를 쓰지 않는 경우: 사업개요, 리스크, 경영진분석 등 서술형 질문 → explore 사용\n"
        "\n"
        "action별 동작:\n"
        "- data: 재무제표 조회 (module 필수). 예: finance(action='data', module='IS')\n"
        "- modules: 사용 가능한 모듈 목록. 어떤 module이 있는지 모를 때 호출\n"
        "- ratios: 재무비율 자동 계산 (ROE, 부채비율 등)\n"
        "- growth: CAGR 성장률 (module 필수)\n"
        "- yoy: 전년대비 변동률 (module 필수). 예: finance(action='yoy', module='IS')\n"
        "- anomalies: 이상치 탐지 (module 필수)\n"
        "- report: 정기보고서 정형 데이터 (apiType 필수). 예: finance(action='report', apiType='dividend')\n"
        "- search: 키워드로 데이터 검색 (keyword 필수)\n"
        "- quality: 이익의 질 종합 (Accrual Ratio, Beneish M-Score, OCF/NI, CCC)\n"
        "- decompose: DuPont 3요소 분해 시계열 (ROE = 순이익률 x 자산회전율 x 레버리지)\n"
        "\n"
        "연쇄 사용: 숫자 확인 후 explore(action='search')로 공시 원문에서 변화 원인을 찾으세요.\n"
        "data 결과의 모든 금액은 백만원 단위(DART 원본 그대로, 보정 없음).\n"
        "module이 뭔지 모르면 먼저 finance(action='modules')로 확인하세요.\n"
        "\n"
        "반환: 마크다운 테이블 (숫자 데이터). 데이터 없으면 '[데이터 없음]' 메시지.",
        {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "data",
                        "modules",
                        "ratios",
                        "growth",
                        "yoy",
                        "anomalies",
                        "report",
                        "search",
                        "quality",
                        "decompose",
                    ],
                    "description": "data=데이터, modules=목록, ratios=비율, growth=성장률, yoy=전년대비, anomalies=이상치, report=보고서, search=검색, quality=이익의질, decompose=DuPont분해",
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
