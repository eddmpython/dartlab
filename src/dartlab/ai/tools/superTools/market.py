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
            from dartlab.gather.naver import getCurrentPrice

            result = getCurrentPrice(code)
            return format_tool_value(result, max_rows=5, max_chars=1000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError) as e:
            return f"[오류] 현재가 조회 실패: {e}. 네트워크 연결을 확인하세요."

    def _consensus(code: str = "", **_kw) -> str:
        if not code:
            return "code를 지정하세요."
        try:
            from dartlab.gather.naver import getConsensus

            result = getConsensus(code)
            return format_tool_value(result, max_rows=10, max_chars=2000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError) as e:
            return (
                f"[오류] 컨센서스 조회 실패: {e}. 대안: analyze(action='valuation')으로 자체 밸류에이션을 확인하세요."
            )

    def _history(code: str = "", days: str = "365", **_kw) -> str:
        if not code:
            return "code를 지정하세요."
        try:
            from dartlab.gather.naver import getPriceHistory

            result = getPriceHistory(code, days=int(days))
            return format_tool_value(result, max_rows=30, max_chars=3000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError) as e:
            return f"[오류] 주가 이력 조회 실패: {e}. 네트워크 연결을 확인하세요."

    def _screen(criteria: str = "", **_kw) -> str:
        if not criteria:
            return "criteria(조건)를 지정하세요."
        try:
            from dartlab.ai.tools.defaults.scan import _screen_market_impl

            return _screen_market_impl(criteria)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError) as e:
            return f"[오류] 스크리닝 실패: {e}"

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
        "시장/주가 데이터 조회 — 현재가, 컨센서스, 주가이력.\n"
        "\n"
        "✓ 이 도구를 쓰는 경우: '현재 주가?', '애널리스트 목표가?', '최근 1년 주가 추이?'\n"
        "✗ 이 도구를 쓰지 않는 경우: 재무제표 숫자 → finance, 공시 원문 → explore\n"
        "\n"
        "action별 동작:\n"
        "- price: 현재 주가 (code 필수). 예: market(action='price', code='005930')\n"
        "- consensus: 애널리스트 컨센서스 (code 필수)\n"
        "- history: 주가 이력 (code 필수, days 선택)\n"
        "- screen: 시장 스크리닝 (criteria 필수)\n"
        "\n"
        "주가 데이터는 외부 소스(Naver Finance)입니다. 재무 데이터와 시점이 다를 수 있습니다.\n"
        "\n"
        "반환: 마크다운 텍스트 (주가, 테이블). 조회 실패 시 '[오류]' 메시지.",
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
