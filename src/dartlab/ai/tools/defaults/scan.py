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
        """기업의 종합 스캔 분석을 축별로 조회한다."""
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
        "거버넌스(지분율/사외이사/보수비율/감사의견/소액주주분산 등급), "
        "인력(직원수/평균급여/인건비율/1인당부가가치/성장률), "
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
        category="analysis",
        questionTypes=("지배구조", "건전성", "종합"),
        priority=70,
    )

    # ── get_digest ──

    def get_digest(sector: str = "", top_n: int = 20) -> str:
        """시장 공시 변화 다이제스트."""
        try:
            import dartlab as _dl

            result = _dl.digest(sector=sector or None, top_n=top_n)
            if result is None:
                return "다이제스트 데이터가 없습니다."
            return format_tool_value(result, max_rows=20)
        except (ImportError, KeyError, OSError, RuntimeError, TypeError, ValueError) as e:
            return f"다이제스트 조회 실패: {e}"

    register_tool(
        "get_digest",
        get_digest,
        "시장 전체 공시 변화 다이제스트를 조회합니다. "
        "최근 공시에서 가장 큰 텍스트 변화를 보인 기업/토픽을 요약합니다. "
        "사용 시점: '시장 동향', '이번 주 주요 공시', '어디서 변화가 컸어?' 질문. "
        "사용하지 말 것: 특정 기업 분석에는 diff_topic이 적절합니다.",
        {
            "type": "object",
            "properties": {
                "sector": {
                    "type": "string",
                    "description": "섹터 필터 (예: 'IT', '금융'). 비워두면 전체 시장.",
                    "default": "",
                },
                "top_n": {
                    "type": "integer",
                    "description": "상위 N개 변화 항목 (기본 20)",
                    "default": 20,
                },
            },
        },
        kind=CapabilityKind.ANALYSIS,
        requires_company=False,
        category="analysis",
        questionTypes=("종합",),
        priority=60,
    )

    # ── create_chart ──

    def create_chart(chart_type: str = "auto") -> str:
        """재무 데이터를 ChartSpec JSON으로 시각화한다."""
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
        category="analysis",
        priority=50,
    )

    # ── network_graph ──

    def network_graph(hops: int = 1) -> str:
        """기업 관계망(투자/주주) 데이터를 조회한다."""
        if company is None:
            return "회사를 먼저 선택하세요."
        try:
            net_func = getattr(company, "network", None)
            if net_func is None:
                return "network() 인터페이스가 없습니다."

            members = net_func("members")
            edges = net_func("edges")
            cycles = net_func("cycles")

            parts: list[str] = []
            if isinstance(members, pl.DataFrame) and members.height > 0:
                parts.append(f"### 계열사 ({members.height}개)\n{df_to_md(members.head(20))}")
            if isinstance(edges, pl.DataFrame) and edges.height > 0:
                parts.append(f"### 투자/주주 관계 ({edges.height}건)\n{df_to_md(edges.head(20))}")
            if isinstance(cycles, pl.DataFrame) and cycles.height > 0:
                parts.append(f"### 순환출자 ({cycles.height}건)\n{df_to_md(cycles)}")
            elif isinstance(cycles, pl.DataFrame):
                parts.append("### 순환출자\n순환출자 없음")

            return "\n\n".join(parts) if parts else "네트워크 데이터가 없습니다."
        except (AttributeError, KeyError, TypeError, ValueError, RuntimeError) as e:
            return f"네트워크 조회 실패: {e}"

    register_tool(
        "network_graph",
        network_graph,
        "기업의 투자/주주 관계망(계열사, 투자관계, 순환출자)을 조회합니다. "
        "사용자가 '삼성 계열사', '관계 지도', '순환출자', '지배구조' 같은 요청을 할 때 사용하세요.",
        {
            "type": "object",
            "properties": {
                "hops": {
                    "type": "integer",
                    "description": "관계 탐색 깊이 (1=직접 관계, 2=2단계)",
                    "default": 1,
                },
            },
        },
        kind=CapabilityKind.ANALYSIS,
        requires_company=True,
        category="analysis",
        questionTypes=("지배구조",),
        priority=65,
    )
