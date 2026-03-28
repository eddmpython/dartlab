"""gather Super Tool -- 외부 시장 데이터 수집 dispatcher.

주가/컨센서스/히스토리 등 외부 소스 데이터 조회.
market.py에서 scan과 무관한 외부 데이터 action을 흡수한다.
"""

from __future__ import annotations

from typing import Callable

from ..defaults.helpers import format_tool_value


def registerGatherTool(registerTool: Callable) -> None:
    """gather Super Tool 등록."""

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
                f"[오류] 컨센서스 조회 실패: {e}. 대안: analysis(action='valuation')으로 자체 밸류에이션을 확인하세요."
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

    _ACTIONS = {
        "price": _price,
        "consensus": _consensus,
        "history": _history,
    }

    def gather(action: str, code: str = "", days: str = "365") -> str:
        """외부 시장 데이터 수집 도구."""
        handler = _ACTIONS.get(action)
        if not handler:
            return f"알 수 없는 action: {action}. 가능: {', '.join(_ACTIONS.keys())}"
        return handler(code=code, days=days)

    registerTool(
        "gather",
        gather,
        "외부 시장 데이터 수집 -- 주가, 컨센서스, 주가이력.\n"
        "\n"
        "- price: 현재 주가 (code 필수)\n"
        "- consensus: 애널리스트 컨센서스 (code 필수)\n"
        "- history: 주가 이력 (code 필수, days로 기간 조절)\n"
        "\n"
        "반환: 마크다운 텍스트. 조회 실패 시 '[오류]' 메시지.",
        {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["price", "consensus", "history"],
                    "description": "price=현재가, consensus=컨센서스, history=주가이력",
                },
                "code": {
                    "type": "string",
                    "description": "종목코드 (예: 005930)",
                },
                "days": {
                    "type": "string",
                    "description": "주가이력 기간(일). 기본 365",
                    "default": "365",
                },
            },
            "required": ["action", "code"],
        },
        category="global",
        questionTypes=("투자", "종합"),
        priority=65,
    )
