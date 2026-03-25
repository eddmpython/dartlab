"""market Super Tool — 시장 데이터 통합 dispatcher.

통합 대상: get_current_price, get_consensus, get_fund_flow, get_price_history,
screen_market, benchmark_sector
"""

from __future__ import annotations

from typing import Callable

from ..defaults.helpers import format_tool_value


def registerMarketTool(registerTool: Callable) -> None:
    """market Super Tool 등록."""

    def _price(code: str = "", **_kw) -> str:
        if not code:
            return "code(종목코드)를 지정하세요."
        try:
            from dartlab.engines.gather.naver import getCurrentPrice

            result = getCurrentPrice(code)
            return format_tool_value(result, max_rows=5, max_chars=1000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError) as e:
            return f"현재가 조회 실패: {e}"

    def _consensus(code: str = "", **_kw) -> str:
        if not code:
            return "code를 지정하세요."
        try:
            from dartlab.engines.gather.naver import getConsensus

            result = getConsensus(code)
            return format_tool_value(result, max_rows=10, max_chars=2000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError) as e:
            return f"컨센서스 조회 실패: {e}"

    def _history(code: str = "", days: str = "365", **_kw) -> str:
        if not code:
            return "code를 지정하세요."
        try:
            from dartlab.engines.gather.naver import getPriceHistory

            result = getPriceHistory(code, days=int(days))
            return format_tool_value(result, max_rows=30, max_chars=3000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError) as e:
            return f"주가 이력 조회 실패: {e}"

    def _screen(criteria: str = "", **_kw) -> str:
        if not criteria:
            return "criteria(조건)를 지정하세요."
        try:
            from dartlab.engines.ai.tools.defaults.scan import _screen_market_impl

            return _screen_market_impl(criteria)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError) as e:
            return f"스크리닝 실패: {e}"

    _ACTIONS = {
        "price": _price,
        "consensus": _consensus,
        "history": _history,
        "screen": _screen,
    }

    def market(action: str, code: str = "", days: str = "365", criteria: str = "") -> str:
        """시장 데이터 통합 도구."""
        handler = _ACTIONS.get(action)
        if not handler:
            return f"알 수 없는 action: {action}. 가능: {', '.join(_ACTIONS.keys())}"
        return handler(code=code, days=days, criteria=criteria)

    registerTool(
        "market",
        market,
        "시장 데이터 조회. 현재가, 컨센서스, 주가이력, 스크리닝.\n"
        "action별 동작:\n"
        "- price: 현재 주가 (code 필수)\n"
        "- consensus: 애널리스트 컨센서스 (code 필수)\n"
        "- history: 주가 이력 (code 필수, days 선택)\n"
        "- screen: 시장 스크리닝 (criteria 필수)",
        {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["price", "consensus", "history", "screen"],
                    "description": "price=현재가, consensus=컨센서스, history=주가이력, screen=스크리닝",
                },
                "code": {
                    "type": "string",
                    "description": "종목코드 (예: 005930)",
                    "default": "",
                },
                "days": {
                    "type": "string",
                    "description": "주가이력 기간(일). 기본 365",
                    "default": "365",
                },
                "criteria": {
                    "type": "string",
                    "description": "스크리닝 조건 (action=screen일 때)",
                    "default": "",
                },
            },
            "required": ["action"],
        },
        category="global",
        questionTypes=("투자", "종합"),
        priority=70,
    )
