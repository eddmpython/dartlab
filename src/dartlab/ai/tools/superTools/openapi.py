"""openapi Super Tool — DART/EDGAR OpenAPI 통합 dispatcher.

통합 대상: call_dart_openapi, call_edgar_openapi, search_dart_filings,
get_dart_filing_text, openapi_save, get_openapi_capabilities
"""

from __future__ import annotations

from typing import Callable

from ..defaults.helpers import format_tool_value


def registerOpenapiTool(registerTool: Callable) -> None:
    """openapi Super Tool 등록."""

    def _dartCall(endpoint: str = "", params: str = "", **_kw) -> str:
        if not endpoint:
            return "endpoint를 지정하세요."
        try:
            from dartlab.providers.dart.openapi.dart import callEndpoint

            result = callEndpoint(endpoint, params)
            return format_tool_value(result, max_rows=30, max_chars=5000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError) as e:
            return f"DART API 호출 실패: {e}"

    def _searchFilings(keyword: str = "", **_kw) -> str:
        if not keyword:
            return "keyword를 지정하세요."
        try:
            from dartlab.providers.dart.openapi.dart import searchFilings

            result = searchFilings(keyword)
            return format_tool_value(result, max_rows=20, max_chars=3000)
        except (ImportError, AttributeError, KeyError, TypeError, ValueError, OSError) as e:
            return f"공시 검색 실패: {e}"

    def _capabilities(**_kw) -> str:
        try:
            from dartlab.providers.dart.openapi.dart import getCapabilities

            return getCapabilities()
        except (ImportError, AttributeError) as e:
            return f"API 스펙 조회 실패: {e}"

    _ACTIONS = {
        "dartCall": _dartCall,
        "searchFilings": _searchFilings,
        "capabilities": _capabilities,
    }

    def openapi(action: str, endpoint: str = "", params: str = "", keyword: str = "") -> str:
        """DART/EDGAR OpenAPI 통합 도구."""
        handler = _ACTIONS.get(action)
        if not handler:
            return f"알 수 없는 action: {action}. 가능: {', '.join(_ACTIONS.keys())}"
        return handler(endpoint=endpoint, params=params, keyword=keyword)

    registerTool(
        "openapi",
        openapi,
        "DART/EDGAR OpenAPI 직접 호출 — 실시간 공시 검색, 원본 API 접근.\n"
        "\n"
        "✓ 이 도구를 쓰는 경우: '최근 공시 검색', 'DART API로 직접 조회'\n"
        "✗ 이 도구를 쓰지 않는 경우: 이미 로드된 공시 데이터 → explore, 재무 숫자 → finance\n"
        "\n"
        "action별 동작:\n"
        "- dartCall: DART API 엔드포인트 호출 (endpoint, params 필수)\n"
        "- searchFilings: DART 공시 키워드 검색 (keyword 필수)\n"
        "- capabilities: 사용 가능한 API 목록 조회",
        {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["dartCall", "searchFilings", "capabilities"],
                    "description": "dartCall=API호출, searchFilings=공시검색, capabilities=API목록",
                },
                "endpoint": {
                    "type": "string",
                    "description": "API 엔드포인트 (action=dartCall일 때)",
                    "default": "",
                },
                "params": {
                    "type": "string",
                    "description": "API 파라미터 (JSON 문자열)",
                    "default": "",
                },
                "keyword": {
                    "type": "string",
                    "description": "검색어 (action=searchFilings일 때)",
                    "default": "",
                },
            },
            "required": ["action"],
        },
        category="global",
        questionTypes=("공시",),
        priority=60,
    )
