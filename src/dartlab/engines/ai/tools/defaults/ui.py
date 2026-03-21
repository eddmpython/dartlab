"""UI 제어 도구 — navigate/chart/comparison/highlight."""

from __future__ import annotations

from typing import Any

from dartlab.core.capabilities import CapabilityChannel, CapabilityKind, UiAction

from .helpers import maybe_int, ui_action_json


def register_ui_tools(company: Any, register_tool) -> None:
    """UI 제어 관련 도구를 등록한다."""

    def _resolve_chart_specs(chart_type: str, data_module: str, metrics: str = "") -> list[dict]:
        if company is None:
            return []

        from dartlab.tools.chart import _SPEC_GENERATORS, auto_chart

        normalized_type = (chart_type or "auto").strip().lower()
        normalized_module = (data_module or "").strip().lower()
        normalized_metrics = (metrics or "").strip().lower()

        if normalized_type == "auto":
            return auto_chart(company)

        direct = _SPEC_GENERATORS.get(normalized_type)
        if direct is not None:
            spec = direct(company)
            return [spec] if spec is not None else []

        mapped_type = "revenue_trend"
        if normalized_type == "radar":
            mapped_type = "insight_radar"
        elif normalized_type == "waterfall":
            mapped_type = "cashflow"
        elif normalized_type == "heatmap":
            mapped_type = "balance_sheet"
        elif "dividend" in normalized_module:
            mapped_type = "dividend"
        elif normalized_module in {"cf", "cashflow", "cash_flow"} or "cash" in normalized_metrics:
            mapped_type = "cashflow"
        elif normalized_module in {"bs", "balance_sheet"} or any(
            token in normalized_metrics for token in ("asset", "debt", "liabil")
        ):
            mapped_type = "balance_sheet"
        elif normalized_module in {"profitability", "ratios"} or any(
            token in normalized_metrics for token in ("margin", "roe", "roa", "profit")
        ):
            mapped_type = "profitability"

        gen = _SPEC_GENERATORS.get(mapped_type)
        if gen is None:
            return []
        spec = gen(company)
        return [spec] if spec is not None else []

    # ── navigate_viewer ──

    def navigate_viewer(topic: str, period: str = "", chapter: str = "") -> str:
        chapter_idx = maybe_int(chapter)
        action = UiAction.navigate(
            topic=topic,
            period=period or None,
            chapter=chapter_idx,
            stock_code=getattr(company, "stockCode", getattr(company, "ticker", None)) if company is not None else None,
            company=getattr(company, "corpName", None) if company is not None else None,
        )
        return ui_action_json(action)

    register_tool(
        "navigate_viewer",
        navigate_viewer,
        "공시 뷰어에서 특정 섹션을 표시합니다. "
        "사용자가 '배당 섹션 보여줘', '사업개요로 이동' 같은 요청을 할 때 사용하세요. "
        "topic은 list_topics로 확인할 수 있습니다.",
        {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "이동할 topic (예: businessOverview, dividend, BS)",
                },
                "period": {
                    "type": "string",
                    "description": "특정 기간 (예: 2024Q4). 비워두면 최신",
                    "default": "",
                },
                "chapter": {
                    "type": "string",
                    "description": "챕터 인덱스. 비워두면 첫 번째",
                    "default": "",
                },
            },
            "required": ["topic"],
        },
        kind=CapabilityKind.UI_ACTION,
        channels=(CapabilityChannel.CHAT, CapabilityChannel.UI),
        result_kind="ui_action",
        ai_hint="공시 뷰어 이동을 트리거하는 UI action",
    )

    # ── show_chart ──

    def show_chart(chart_type: str, data_module: str, metrics: str = "") -> str:
        specs = _resolve_chart_specs(chart_type, data_module, metrics)
        if not specs:
            return ui_action_json(UiAction.toast("차트를 생성할 데이터가 없습니다.", level="warning"))
        return ui_action_json(
            UiAction.render_widget(
                "chart",
                {
                    "spec": specs[0],
                },
                title="AI 생성 차트",
                source={
                    "tool": "show_chart",
                    "chartType": chart_type,
                    "dataModule": data_module,
                    "metrics": [m.strip() for m in metrics.split(",") if m.strip()] if metrics else [],
                },
            )
        )

    register_tool(
        "show_chart",
        show_chart,
        "차트를 생성하여 사용자에게 표시합니다. "
        "chart_type: trend(추세), waterfall(폭포), radar(레이더), heatmap(히트맵). "
        "사용자가 '차트로 보여줘', '추세 그래프' 같은 요청을 할 때 사용하세요.",
        {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "description": "차트 유형 (trend, waterfall, radar, heatmap)",
                },
                "data_module": {
                    "type": "string",
                    "description": "데이터 소스 모듈명 (예: IS, BS, ratios)",
                },
                "metrics": {
                    "type": "string",
                    "description": "쉼표 구분 지표 목록 (예: revenue,operating_income)",
                    "default": "",
                },
            },
            "required": ["chart_type", "data_module"],
        },
        kind=CapabilityKind.UI_ACTION,
        channels=(CapabilityChannel.CHAT, CapabilityChannel.UI),
        requires_company=True,
        result_kind="ui_action",
        ai_hint="ChartRenderer가 바로 렌더 가능한 spec을 포함한 UI action",
    )

    # ── show_comparison ──

    def show_comparison(topics: str, periods: str = "") -> str:
        topic_list = [t.strip() for t in topics.split(",") if t.strip()]
        if not topic_list:
            return ui_action_json(UiAction.toast("비교할 topic이 없습니다.", level="warning"))
        return ui_action_json(
            UiAction.render_widget(
                "comparison",
                {
                    "stockCode": getattr(company, "stockCode", getattr(company, "ticker", None)) if company is not None else None,
                    "topics": topic_list,
                    "periods": [p.strip() for p in periods.split(",") if p.strip()] if periods else [],
                },
                title="기간 비교",
            )
        )

    register_tool(
        "show_comparison",
        show_comparison,
        "기간간 비교 뷰를 표시합니다. "
        "사용자가 '기간 비교', '전년 대비 보여줘' 같은 요청을 할 때 사용하세요.",
        {
            "type": "object",
            "properties": {
                "topics": {
                    "type": "string",
                    "description": "쉼표 구분 topic 목록 (예: BS,IS,CF)",
                },
                "periods": {
                    "type": "string",
                    "description": "쉼표 구분 기간 목록 (예: 2023Q4,2024Q4). 비워두면 최근 2개",
                    "default": "",
                },
            },
            "required": ["topics"],
        },
        kind=CapabilityKind.UI_ACTION,
        channels=(CapabilityChannel.CHAT, CapabilityChannel.UI),
        requires_company=True,
        result_kind="ui_action",
    )

    # ── highlight_section ──

    def highlight_section(topic: str, keyword: str) -> str:
        return ui_action_json(
            UiAction.update(
                "viewer.highlight",
                {
                    "topic": topic,
                    "keyword": keyword,
                    "action": "highlight",
                },
            )
        )

    register_tool(
        "highlight_section",
        highlight_section,
        "특정 섹션에서 키워드를 하이라이트합니다. "
        "사용자가 특정 텍스트를 찾거나 강조하고 싶을 때 사용하세요.",
        {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "대상 topic (예: riskFactor, businessOverview)",
                },
                "keyword": {
                    "type": "string",
                    "description": "하이라이트할 키워드",
                },
            },
            "required": ["topic", "keyword"],
        },
        kind=CapabilityKind.UI_ACTION,
        channels=(CapabilityChannel.CHAT, CapabilityChannel.UI),
        result_kind="ui_action",
    )
