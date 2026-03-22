"""DartLab MCP 서버 — Claude Desktop / Claude Code / Cursor 연동.

사용법::

        # stdio 모드로 서버 실행
        dartlab mcp

        # 또는 직접 실행
        python -m dartlab.mcp

Claude Desktop config.json 예시::

        {
            "mcpServers": {
                "dartlab": {
                    "command": "uv",
                    "args": ["run", "dartlab", "mcp"]
                }
            }
        }

Claude Code (~/.claude/settings.json)::

        {
            "mcpServers": {
                "dartlab": {
                    "command": "uv",
                    "args": ["--directory", "/path/to/dartlab", "run", "dartlab", "mcp"]
                }
            }
        }
"""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any

# stderr 로깅 — stdout은 MCP stdio 프로토콜 전용
_log = logging.getLogger("dartlab.mcp")
_log.addHandler(logging.StreamHandler(sys.stderr))
_log.setLevel(logging.INFO)

# 회사 세션 캐시 — LRU 5개, TTL 600초, 무한 누적 방지
_MCP_CACHE_MAX = 5
_MCP_CACHE_TTL = 600
_company_cache: dict[str, tuple[Any, float]] = {}


def _get_or_create_company(stock_code: str | None) -> Any | None:
    """종목코드로 Company 인스턴스 가져오기 (LRU 캐싱, TTL 600초, 최대 5개)."""
    if not stock_code:
        return None
    entry = _company_cache.get(stock_code)
    if entry is not None:
        company, created = entry
        if (time.monotonic() - created) < _MCP_CACHE_TTL:
            return company
        del _company_cache[stock_code]

    from dartlab import Company

    _log.info("Company('%s') 로딩 중...", stock_code)
    c = Company(stock_code)
    # LRU 퇴출: 가장 오래된 항목 제거
    if len(_company_cache) >= _MCP_CACHE_MAX:
        oldest = next(iter(_company_cache))
        _log.info("캐시 퇴출: %s", oldest)
        del _company_cache[oldest]
    _company_cache[stock_code] = (c, time.monotonic())
    _log.info("Company('%s') 로딩 완료 — 캐시 %d/%d", stock_code, len(_company_cache), _MCP_CACHE_MAX)
    return c


def create_server():
    """MCP 서버 인스턴스 생성."""
    try:
        from mcp.server import Server
        from mcp.server.lowlevel.server import ReadResourceContents
        from mcp.types import Resource, TextContent, Tool
    except ImportError as exc:
        raise ImportError("MCP SDK가 필요합니다.\n  uv add 'mcp[cli]>=1.0'\n또는: pip install 'mcp[cli]>=1.0'") from exc

    from dartlab.engines.ai.tools.registry import build_tool_runtime

    from .bridge import build_mcp_tools

    app = Server("dartlab")

    # stock_code 파라미터 정의 — company 필요 도구에 주입
    _STOCK_CODE_PROP = {
        "stock_code": {
            "type": "string",
            "description": "종목코드 (예: 005930) 또는 티커 (예: AAPL). 기업별 도구 호출 시 필수.",
        }
    }

    # company=None 일 때만 노출되는 도구 (stock_code 불필요)
    _runtime_no_company = build_tool_runtime(None, name="mcp-schema-base")
    _base_tool_names = {s["function"]["name"] for s in _runtime_no_company.get_tool_schemas()}

    # dummy object로 전체 도구 스키마 수집 (실제 Company 로딩 없이)
    _runtime_full = build_tool_runtime(object(), name="mcp-schema-full")
    _all_tool_count = _runtime_full.size

    _log.info(
        "MCP 서버 초기화 — 전체 %d 도구 (글로벌 %d + 기업별 %d)",
        _all_tool_count,
        len(_base_tool_names),
        _all_tool_count - len(_base_tool_names),
    )

    # ── list_tools ──

    @app.list_tools()
    async def list_tools() -> list[Tool]:
        mcp_tools = build_mcp_tools(_runtime_full)
        result = []
        for t in mcp_tools:
            schema = dict(t.inputSchema)
            # company 필요 도구에 stock_code 파라미터 주입
            if t.name not in _base_tool_names:
                props = dict(schema.get("properties", {}))
                props.update(_STOCK_CODE_PROP)
                schema["properties"] = props
                req = list(schema.get("required", []))
                if "stock_code" not in req:
                    req.insert(0, "stock_code")
                schema["required"] = req
            result.append(
                Tool(
                    name=t.name,
                    description=t.description,
                    inputSchema=schema,
                )
            )
        return result

    # ── call_tool ──

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        args = dict(arguments)
        stock_code = args.pop("stock_code", None)

        # company-bound 도구인데 stock_code 없으면 에러
        if name not in _base_tool_names and not stock_code:
            return [
                TextContent(
                    type="text",
                    text=f"오류: '{name}'은 기업별 도구입니다. stock_code 파라미터가 필요합니다.\n"
                    f'예: {{"stock_code": "005930", ...}}',
                )
            ]

        try:
            company = _get_or_create_company(stock_code)
        except (FileNotFoundError, ValueError, RuntimeError) as e:
            _log.warning("Company('%s') 생성 실패: %s", stock_code, e)
            return [
                TextContent(
                    type="text",
                    text=f"기업 데이터 로딩 실패 ({stock_code}): {e}",
                )
            ]

        runtime = build_tool_runtime(company, name="mcp-call")

        if not runtime.has_tool(name):
            return [
                TextContent(
                    type="text",
                    text=f"오류: '{name}' 도구를 찾을 수 없습니다. list_tools로 사용 가능한 도구를 확인하세요.",
                )
            ]

        _log.info("call_tool: %s(stock_code=%s, args=%s)", name, stock_code, list(args.keys()))
        result = runtime.execute_tool(name, args)
        return [TextContent(type="text", text=result)]

    # ── list_resources ──

    @app.list_resources()
    async def list_resources() -> list[Resource]:
        resources = [
            Resource(
                uri="dartlab://info",
                name="DartLab 정보",
                description="DartLab 버전, 사용 가능한 도구 수, 캐시된 기업 목록",
                mimeType="application/json",
            ),
        ]
        # 캐시된 기업별 리소스 노출
        for code in _company_cache:
            resources.extend(
                [
                    Resource(
                        uri=f"dartlab://company/{code}/sections",
                        name=f"{code} sections",
                        description=f"{code} 공시 섹션 지도 (topic × period 수평화)",
                        mimeType="application/json",
                    ),
                    Resource(
                        uri=f"dartlab://company/{code}/topics",
                        name=f"{code} topics",
                        description=f"{code} 조회 가능 topic 목록",
                        mimeType="application/json",
                    ),
                    Resource(
                        uri=f"dartlab://company/{code}/ratios",
                        name=f"{code} ratios",
                        description=f"{code} 재무비율 (55개 비율 + 복합지표)",
                        mimeType="application/json",
                    ),
                ]
            )
        return resources

    # ── read_resource ──

    @app.read_resource()
    async def read_resource(uri: str) -> list[ReadResourceContents]:
        uri_str = str(uri)

        def _json_content(data: Any) -> list[ReadResourceContents]:
            return [
                ReadResourceContents(
                    content=json.dumps(data, ensure_ascii=False, indent=2, default=str),
                    mime_type="application/json",
                )
            ]

        def _text_content(text: str) -> list[ReadResourceContents]:
            return [ReadResourceContents(content=text, mime_type="text/plain")]

        # dartlab://info
        if uri_str == "dartlab://info":
            import dartlab

            return _json_content(
                {
                    "version": getattr(dartlab, "__version__", "unknown"),
                    "tools": _all_tool_count,
                    "globalTools": len(_base_tool_names),
                    "companyTools": _all_tool_count - len(_base_tool_names),
                    "cachedCompanies": list(_company_cache.keys()),
                    "cacheMax": _MCP_CACHE_MAX,
                    "cacheTtlSeconds": _MCP_CACHE_TTL,
                }
            )

        # dartlab://company/{code}/{resource}
        if uri_str.startswith("dartlab://company/"):
            parts = uri_str.replace("dartlab://company/", "").split("/", 1)
            if len(parts) != 2:
                return _text_content("잘못된 URI 형식")
            code, resource = parts
            company = _get_or_create_company(code)
            if company is None:
                return _text_content(f"기업 '{code}'를 찾을 수 없습니다")

            if resource == "sections":
                secs = getattr(company, "sections", None)
                if secs is not None and hasattr(secs, "to_dicts"):
                    return _json_content(secs.to_dicts())
                if secs is not None and hasattr(secs, "to_dict"):
                    return _json_content(secs.to_dict())
                return _json_content({"error": "sections 데이터 없음"})

            if resource == "topics":
                topics = getattr(company, "topics", None)
                data = topics if isinstance(topics, list) else list(topics) if topics else []
                return _json_content(data)

            if resource == "ratios":
                ratios = getattr(company, "ratios", None)
                if ratios is not None and hasattr(ratios, "__dict__"):
                    data = {k: v for k, v in ratios.__dict__.items() if not k.startswith("_")}
                elif ratios is not None and hasattr(ratios, "to_dict"):
                    data = ratios.to_dict()
                else:
                    data = {"error": "ratios 데이터 없음"}
                return _json_content(data)

            return _text_content(f"알 수 없는 리소스: {resource}")

        return _text_content(f"알 수 없는 URI: {uri_str}")

    return app


def run_stdio():
    """stdio 모드로 MCP 서버 실행."""
    import asyncio

    try:
        from mcp.server.stdio import stdio_server
    except ImportError as exc:
        raise ImportError("MCP SDK가 필요합니다.\n  uv add 'mcp[cli]>=1.0'\n또는: pip install 'mcp[cli]>=1.0'") from exc

    app = create_server()

    async def _main():
        async with stdio_server() as (read_stream, write_stream):
            _log.info("DartLab MCP 서버 시작 (stdio)")
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(_main())


if __name__ == "__main__":
    run_stdio()
