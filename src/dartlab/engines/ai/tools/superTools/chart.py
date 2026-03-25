"""chart Super Tool — UI/차트 통합 dispatcher.

통합 대상: navigate_viewer, show_chart, create_chart, render_dashboard
"""

from __future__ import annotations

from typing import Any

from ..defaults.helpers import format_tool_value


def registerChartTool(company: Any, registerTool) -> None:
    """chart Super Tool 등록."""

    def _navigate(target: str = "", **_kw) -> str:
        try:
            from dartlab.core.capabilities import UiAction
            from dartlab.engines.ai.tools.defaults.helpers import ui_action_json

            action = UiAction.navigate(
                topic=target,
                stock_code=getattr(company, "stockCode", getattr(company, "ticker", None)),
                company=getattr(company, "corpName", None),
            )
            return ui_action_json(action)
        except (ImportError, AttributeError, TypeError, ValueError) as e:
            return f"뷰어 네비게이션 실패: {e}"

    def _showChart(chartType: str = "", module: str = "", **_kw) -> str:
        try:
            import json

            from dartlab.tools.chart import _SPEC_GENERATORS, auto_chart

            if not chartType or chartType == "auto":
                specs = auto_chart(company)
            else:
                gen = _SPEC_GENERATORS.get(chartType)
                if gen is None:
                    available = ", ".join(_SPEC_GENERATORS.keys())
                    return f"'{chartType}' 차트 없음. 가능: {available}"
                result = gen(company)
                specs = [result] if result is not None else []
            if not specs:
                return "차트 생성에 필요한 재무 데이터가 없습니다."
            return json.dumps({"charts": specs}, ensure_ascii=False)
        except (ImportError, AttributeError, TypeError, ValueError) as e:
            return f"차트 생성 실패: {e}"

    _ACTIONS = {
        "navigate": _navigate,
        "chart": _showChart,
    }

    def chart(action: str, target: str = "", chartType: str = "", module: str = "") -> str:
        """UI/차트 통합 도구."""
        handler = _ACTIONS.get(action)
        if not handler:
            return f"알 수 없는 action: {action}. 가능: {', '.join(_ACTIONS.keys())}"
        return handler(target=target, chartType=chartType, module=module)

    registerTool(
        "chart",
        chart,
        "UI 제어/차트 생성.\n"
        "action별 동작:\n"
        "- navigate: 뷰어 특정 위치로 이동 (target 필수)\n"
        "- chart: 차트 생성 (chartType, module 필수)",
        {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["navigate", "chart"],
                    "description": "navigate=뷰어이동, chart=차트생성",
                },
                "target": {
                    "type": "string",
                    "description": "이동할 topic/위치 (action=navigate일 때)",
                    "default": "",
                },
                "chartType": {
                    "type": "string",
                    "description": "차트 종류 (action=chart일 때)",
                    "default": "",
                },
                "module": {
                    "type": "string",
                    "description": "데이터 모듈 (action=chart일 때)",
                    "default": "",
                },
            },
            "required": ["action"],
        },
        category="ui",
        questionTypes=("종합",),
        priority=40,
    )
