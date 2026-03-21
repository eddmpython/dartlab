"""Scan 도구 — 전수 스캔 분석 + 차트 생성."""

from __future__ import annotations

import json
from typing import Any

import polars as pl

from dartlab.core.capabilities import CapabilityKind

from .helpers import df_to_md, format_tool_value


def register_scan_tools(company: Any, register_tool) -> None:
    """scan 엔진 관련 도구를 등록한다."""

    def get_scan_data(axis: str = "all") -> str:
        if company is None:
            return json.dumps({"error": "회사를 먼저 선택하세요."}, ensure_ascii=False)

        _SCAN_METHODS = {
            "governance": "governance",
            "workforce": "workforce",
            "capital": "capital",
            "debt": "debt",
        }

        if axis == "all":
            parts: list[str] = []
            for key, method_name in _SCAN_METHODS.items():
                method = getattr(company, method_name, None)
                if method is None:
                    continue
                try:
                    result = method()
                    if result is not None and isinstance(result, pl.DataFrame) and not result.is_empty():
                        parts.append(f"### {key}\n{df_to_md(result)}")
                except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError):
                    continue
            return "\n\n".join(parts) if parts else "(scan 데이터 없음)"

        method_name = _SCAN_METHODS.get(axis)
        if method_name is None:
            return f"알 수 없는 축: {axis}. 가능한 값: all, governance, workforce, capital, debt"

        method = getattr(company, method_name, None)
        if method is None:
            return f"{axis} 스캔을 지원하지 않습니다."
        try:
            result = method()
            if result is None or (isinstance(result, pl.DataFrame) and result.is_empty()):
                return f"({axis} 데이터 없음)"
            return format_tool_value(result, max_rows=5)
        except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError) as e:
            return f"{axis} 스캔 실패: {e}"

    register_tool(
        "get_scan_data",
        get_scan_data,
        "기업의 종합 스캔 분석을 조회합니다. "
        "거버넌스(지분율/사외이사/보수비율/감사의견 등급), "
        "인력(직원수/평균급여/성장률/인건비부담), "
        "주주환원(배당/자사주/증자 → 환원형/중립/희석형), "
        "부채구조(부채비율/ICR → 안전/관찰/주의/고위험). "
        "사용자가 '거버넌스', '인력현황', '주주환원', '부채위험', '종합진단' 등을 물을 때 사용하세요.",
        {
            "type": "object",
            "properties": {
                "axis": {
                    "type": "string",
                    "enum": ["all", "governance", "workforce", "capital", "debt"],
                    "description": "스캔 축. all=전체, governance=지배구조, workforce=인력, capital=주주환원, debt=부채",
                    "default": "all",
                },
            },
        },
    )

    # ── create_chart ──

    def create_chart(chart_type: str = "auto") -> str:
        if company is None:
            return json.dumps({"error": "회사를 먼저 선택하세요."}, ensure_ascii=False)

        from dartlab.tools.chart import _SPEC_GENERATORS, auto_chart

        if chart_type == "auto":
            specs = auto_chart(company)
        else:
            gen = _SPEC_GENERATORS.get(chart_type)
            if gen is None:
                available = ", ".join(_SPEC_GENERATORS.keys())
                return json.dumps(
                    {"error": f"'{chart_type}' 차트를 찾을 수 없습니다. 사용 가능: {available}"},
                    ensure_ascii=False,
                )
            result = gen(company)
            specs = [result] if result is not None else []

        if not specs:
            return json.dumps({"error": "차트를 생성할 데이터가 없습니다."}, ensure_ascii=False)

        return json.dumps({"charts": specs}, ensure_ascii=False)

    register_tool(
        "create_chart",
        create_chart,
        "기업의 재무 데이터를 차트로 시각화합니다. "
        "매출 추이, 수익성, 현금흐름, 배당, 인사이트 레이더 등을 ChartSpec JSON으로 생성합니다. "
        "사용자가 '차트 보여줘', '매출 추이 그래프', '시각화' 같은 요청을 할 때 사용하세요.",
        {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": [
                        "auto",
                        "revenue_trend",
                        "cashflow",
                        "balance_sheet",
                        "profitability",
                        "dividend",
                        "insight_radar",
                        "ratio_sparklines",
                        "diff_heatmap",
                    ],
                    "description": (
                        "차트 유형. auto는 사용 가능한 모든 차트를 자동 생성. "
                        "revenue_trend=손익추이, cashflow=현금흐름, balance_sheet=자산구성, "
                        "profitability=수익성추이, dividend=배당분석, insight_radar=인사이트레이더, "
                        "ratio_sparklines=비율스파크라인, diff_heatmap=변화밀도"
                    ),
                    "default": "auto",
                },
            },
        },
        kind=CapabilityKind.WORKFLOW,
        requires_company=True,
        result_kind="chart",
        ai_hint="ChartSpec JSON 생성",
    )
