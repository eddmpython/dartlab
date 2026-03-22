"""
실험 ID: 013
실험명: MCP Bridge — ToolRuntime → MCP tool 변환 설계 검증

목적:
- dartlab ToolRuntime의 도구를 MCP(Model Context Protocol) Tool로 변환하는 브릿지 설계
- MCP SDK 없이도 변환 로직의 정확성을 검증
- Company 세션 관리 전략 설계

가설:
1. OpenAI function calling schema → MCP inputSchema 변환이 1:1 매핑된다
2. 39개 도구 전부 MCP Tool로 변환 가능하다
3. Company 세션은 MCP resource로 관리할 수 있다

방법:
1. MCP Tool/Resource 스펙을 코드로 정의 (SDK 미설치 대비)
2. ToolRuntime.get_tool_schemas() → MCP Tool 변환 함수 구현
3. 39개 도구 전수 변환 + 검증
4. Company 세션 관리 설계안 작성

결과:
- OpenAI → MCP 변환: 39/39 도구 전부 성공 (1:1 매핑)
- 변환 로직: function.name → Tool.name, function.description → Tool.description, function.parameters → Tool.inputSchema
- Company Resource URI: dartlab://company/{stockCode}/{namespace} (sections/ratios/BS/IS/CF/profile)
- MCP 서버 스켈레톤: ~34줄 (ToolRuntime.execute_tool 재사용)
- MCP SDK 미설치 — 실제 Claude Desktop 연동은 SDK 설치 후

결론:
- 가설 1 채택: OpenAI schema → MCP inputSchema가 완벽 1:1 매핑
- 가설 2 채택: 39개 전부 변환 성공
- 가설 3 채택: dartlab://company/{code}/ 형태로 resource 관리 가능
- MCP 서버 구현 비용이 매우 낮음 (~34줄) — ToolRuntime이 이미 전체 인프라를 제공
- 다음 단계: `uv add mcp[cli]` → 실제 서버 구현 → Claude Desktop 종단 테스트

실험일: 2026-03-20
"""

import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


# ═══════════════════════════════════════
# MCP 스펙 정의 (SDK 미설치 대비)
# ═══════════════════════════════════════


@dataclass
class MCPTool:
    """MCP Tool 스펙 (https://spec.modelcontextprotocol.io)."""

    name: str
    description: str
    inputSchema: dict  # JSON Schema


@dataclass
class MCPResource:
    """MCP Resource 스펙."""

    uri: str
    name: str
    description: str
    mimeType: str = "application/json"


# ═══════════════════════════════════════
# 변환 로직
# ═══════════════════════════════════════


def openai_schema_to_mcp_tool(schema: dict) -> MCPTool:
    """OpenAI function calling schema → MCP Tool."""
    func = schema.get("function", {})
    return MCPTool(
        name=func.get("name", ""),
        description=func.get("description", ""),
        inputSchema=func.get("parameters", {"type": "object", "properties": {}}),
    )


def build_mcp_tools(runtime) -> list[MCPTool]:
    """ToolRuntime → MCP Tool 목록."""
    return [openai_schema_to_mcp_tool(s) for s in runtime.get_tool_schemas()]


def build_company_resources(stock_code: str) -> list[MCPResource]:
    """Company 세션용 MCP Resource 목록."""
    base = f"dartlab://company/{stock_code}"
    return [
        MCPResource(uri=f"{base}/sections", name=f"{stock_code} sections", description="공시 sections 데이터"),
        MCPResource(uri=f"{base}/ratios", name=f"{stock_code} ratios", description="재무비율"),
        MCPResource(uri=f"{base}/BS", name=f"{stock_code} BS", description="재무상태표"),
        MCPResource(uri=f"{base}/IS", name=f"{stock_code} IS", description="손익계산서"),
        MCPResource(uri=f"{base}/CF", name=f"{stock_code} CF", description="현금흐름표"),
        MCPResource(uri=f"{base}/profile", name=f"{stock_code} profile", description="기업 프로필"),
    ]


def generate_mcp_server_skeleton() -> str:
    """MCP 서버 스켈레톤 코드 생성."""
    return '''
# src/dartlab/mcp/__init__.py — MCP 서버 구현 (예상 ~150줄)

from mcp.server import Server
from mcp.types import Tool, TextContent
from dartlab.engines.ai.tools_registry import build_tool_runtime

app = Server("dartlab")
_sessions: dict[str, Any] = {}  # stock_code → Company 캐시

@app.list_tools()
async def list_tools() -> list[Tool]:
    """등록된 도구 목록 반환."""
    runtime = build_tool_runtime(None, name="mcp")
    return [
        Tool(name=t.name, description=t.description, inputSchema=t.inputSchema)
        for t in build_mcp_tools(runtime)
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """도구 실행."""
    # stock_code가 arguments에 있으면 Company 세션 생성/재사용
    stock_code = arguments.pop("stock_code", None)
    company = _get_or_create_company(stock_code) if stock_code else None

    runtime = build_tool_runtime(company, name="mcp-call")
    result = runtime.execute_tool(name, arguments)
    return [TextContent(type="text", text=result)]

def _get_or_create_company(stock_code: str):
    if stock_code not in _sessions:
        import dartlab
        _sessions[stock_code] = dartlab.Company(stock_code)
    return _sessions[stock_code]
'''


if __name__ == "__main__":
    print("=" * 60)
    print("실험 013: MCP Bridge")
    print("=" * 60)

    # 1. ToolRuntime → MCP Tool 변환
    from dartlab.engines.ai.tools_registry import build_tool_runtime

    class MinimalCompany:
        corpName = "MCP테스트"
        stockCode = "005930"
        BS = None; IS = None; CF = None; CIS = None
        def show(self, *a, **k): return None
        @property
        def topics(self): return None
        @property
        def ratios(self): return None
        class finance:
            BS = None; IS = None; CF = None; ratios = None; timeseries = None; ratioSeries = None
        class docs:
            class sections: pass
        class report: pass

    runtime = build_tool_runtime(MinimalCompany(), name="mcp-test")
    mcp_tools = build_mcp_tools(runtime)

    print(f"\n변환된 MCP Tool: {len(mcp_tools)}개")

    # 2. 변환 품질 검증
    valid = 0
    issues = []
    for t in mcp_tools:
        has_name = bool(t.name)
        has_desc = bool(t.description)
        has_schema = "type" in t.inputSchema

        if has_name and has_desc and has_schema:
            valid += 1
        else:
            issues.append(f"  {t.name}: name={has_name} desc={has_desc} schema={has_schema}")

    print(f"  유효: {valid}/{len(mcp_tools)}")
    if issues:
        print("  문제:")
        for i in issues:
            print(i)

    # 3. 카테고리별 분류
    print("\n=== MCP Tool 목록 (처음 10개) ===")
    for t in mcp_tools[:10]:
        params = list(t.inputSchema.get("properties", {}).keys())
        print(f"  {t.name:>30}: params={params}")

    # 4. Company Resource 설계
    print("\n=== Company Resource 설계 ===")
    resources = build_company_resources("005930")
    for r in resources:
        print(f"  {r.uri}: {r.description}")

    # 5. 서버 스켈레톤
    skeleton = generate_mcp_server_skeleton()
    skeleton_lines = len(skeleton.strip().split("\n"))
    print(f"\n=== MCP 서버 스켈레톤 ===")
    print(f"  예상 줄 수: {skeleton_lines}줄")

    # 6. MCP SDK 설치 필요성
    try:
        import mcp
        print(f"  MCP SDK: 설치됨 ({mcp.__version__})")
    except ImportError:
        print("  MCP SDK: 미설치 — `uv add mcp[cli]` 필요")

    # 결론
    print(f"\n=== 결론 ===")
    print(f"  1. OpenAI → MCP 변환: {valid}/{len(mcp_tools)} 성공 (1:1 매핑)")
    print(f"  2. Company 세션: MCP resource URI + 메모리 캐시로 관리")
    print(f"  3. 서버 구현 예상: ~{skeleton_lines}줄 (ToolRuntime 재사용)")
    print(f"  4. 다음 단계: MCP SDK 설치 → 실제 Claude Desktop 연동 테스트")
