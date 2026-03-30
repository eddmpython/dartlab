"""DartLab MCP 서버 -- 한국 상장기업 전자공시 분석.

설치 후 바로 사용::

    pip install dartlab
    # Claude Code / Codex에서 "삼성전자 분석해줘" → 바로 동작

수동 설정 (.mcp.json)::

    {
        "mcpServers": {
            "dartlab": {
                "command": "uv",
                "args": ["run", "python", "-X", "utf8", "-m", "dartlab.mcp"]
            }
        }
    }

자동 설정::

    dartlab mcp --install   # .mcp.json 자동 생성
"""

from __future__ import annotations

import json
import logging
import sys
import time
import traceback
from typing import Any

_log = logging.getLogger("dartlab.mcp")
_log.addHandler(logging.StreamHandler(sys.stderr))
_log.setLevel(logging.INFO)

_CACHE_MAX = 5
_CACHE_TTL = 600
_cache: dict[str, tuple[Any, float]] = {}


def _getCompany(stockCode: str) -> Any:
    """종목코드로 Company 인스턴스 (캐싱)."""
    entry = _cache.get(stockCode)
    if entry:
        obj, ts = entry
        if (time.monotonic() - ts) < _CACHE_TTL:
            return obj
        del _cache[stockCode]
    from dartlab import Company
    _log.info("Company('%s') loading...", stockCode)
    c = Company(stockCode)
    if len(_cache) >= _CACHE_MAX:
        del _cache[next(iter(_cache))]
    _cache[stockCode] = (c, time.monotonic())
    _log.info("Company('%s') ready", stockCode)
    return c


def _df(obj) -> str:
    """DataFrame/객체를 문자열로."""
    if obj is None:
        return "데이터 없음"
    if hasattr(obj, "to_pandas"):
        return obj.to_pandas().to_string()
    return str(obj)[:8000]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Instructions -- LLM에게 사용법을 알려준다
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_MCP_INSTRUCTIONS = """\
dartlab은 한국 상장기업 전자공시(DART) 분석 도구입니다.

## review vs analysis
- companyReview: analysis 전체 축을 한번에 실행한 정리된 보고서. 사용자에게 보여줄 최종 보고서가 필요할 때만 사용.
- companyAnalysis: 특정 영역의 원본 데이터 + 계산 결과. 너(AI)가 직접 데이터를 보고 해석할 때 사용.
- companyInsights: 7영역 등급 요약. 빠른 판단에 사용.
- 기본적으로 companyInsights나 companyAnalysis로 데이터를 직접 보고 네가 해석하라.
- companyReview는 사용자가 "보고서 만들어줘"라고 명시할 때만 사용.

## 도구 사용 흐름
1. 종목코드를 모르면 → searchCompany
2. 빠른 판단 → companyInsights (등급 + 프로파일)
3. 심층 분석 → companyAnalysis("수익구조") 등 필요한 축을 직접 호출
4. 원본 데이터 → companyFinancials, companyRatios
5. 밸류에이션 → companyValuation, companyForecast
6. 시장 비교 → marketScan
7. 정리된 보고서 → companyReview (사용자가 요청할 때만)

## 규칙
- 분석 요청 시 되묻지 말고 즉시 도구를 호출하라.
- 숫자만 나열하지 말고 원인, 추세, 시사점을 해석하라.
- 한국어 질문에는 한국어로 답변하라.
- 도구로 확인되지 않은 수치를 인용하지 마라.
- 현재 한국 DART 기업만 지원한다.
"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MCP 도구 정의
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_STOCK = {"type": "string", "description": "종목코드 (005930) 또는 회사명 (삼성전자)"}

_TOOLS: list[dict] = [
    # ── 1순위: 직접 보고 판단 ──
    {
        "name": "companyInsights",
        "description": (
            "[먼저 사용] 7영역 등급 (A~F) + 투자 프로파일 + 핵심 서사. "
            "수익성, 안정성, 성장성, 현금흐름, 효율성, 투자효율, 밸류에이션. "
            "분석 요청 시 이 도구로 먼저 전체 그림을 파악한 뒤, 필요한 영역을 companyAnalysis로 파고들어라."
        ),
        "params": {"stockCode": _STOCK},
        "required": ["stockCode"],
    },
    {
        "name": "searchCompany",
        "description": "한국 상장기업 검색. 종목코드(005930), 회사명(삼성전자), 부분검색(삼성) 가능. 종목코드를 모를 때 먼저 사용.",
        "params": {"query": {"type": "string", "description": "검색어"}},
        "required": ["query"],
    },

    # ── 재무 데이터 (깊이가 필요할 때) ──
    {
        "name": "companyFinancials",
        "description": "재무제표 원본 조회. IS(손익), BS(재무상태), CF(현금흐름), CIS(포괄손익), SCE(자본변동) 중 선택.",
        "params": {
            "stockCode": _STOCK,
            "statement": {"type": "string", "description": "IS / BS / CF / CIS / SCE", "enum": ["IS", "BS", "CF", "CIS", "SCE"]},
        },
        "required": ["stockCode", "statement"],
    },
    {
        "name": "companyRatios",
        "description": "재무비율 55개 시계열. ROE, ROA, 부채비율, 영업이익률, PER, PBR 등.",
        "params": {"stockCode": _STOCK},
        "required": ["stockCode"],
    },
    {
        "name": "companyAnalysis",
        "description": (
            "14축 재무 심층 분석. review보다 세밀한 데이터가 필요할 때 사용. "
            "축: 수익구조, 안정성, 성장성, 현금흐름, 자금조달, 자산구조, 수익성, 효율성, "
            "이익품질, 비용구조, 자본배분, 투자효율, 재무정합성, 종합평가"
        ),
        "params": {
            "stockCode": _STOCK,
            "axis": {"type": "string", "description": "분석 축 (생략 시 가이드 반환)"},
        },
        "required": ["stockCode"],
    },

    # ── 전망/가치평가 ──
    {
        "name": "companyValuation",
        "description": "종합 밸류에이션 (DCF + DDM + 상대가치 + RIM). 적정가치 범위, 현재가 대비 고평가/저평가 판정.",
        "params": {"stockCode": _STOCK},
        "required": ["stockCode"],
    },
    {
        "name": "companyForecast",
        "description": "매출 예측 (Base/Bull/Bear 시나리오). 선형회귀 + CAGR + 이동평균 앙상블.",
        "params": {"stockCode": _STOCK},
        "required": ["stockCode"],
    },

    # ── 공시 원문/비교 ──
    {
        "name": "companyShow",
        "description": "공시 토픽 원문 조회. 예: businessOverview(사업개요), revenue(매출), riskFactors(위험요인). companyTopics로 목록 확인.",
        "params": {
            "stockCode": _STOCK,
            "topic": {"type": "string", "description": "토픽명"},
        },
        "required": ["stockCode", "topic"],
    },
    {
        "name": "companyTopics",
        "description": "이 기업에서 조회 가능한 공시 토픽 목록. companyShow의 topic에 쓸 수 있는 값.",
        "params": {"stockCode": _STOCK},
        "required": ["stockCode"],
    },
    {
        "name": "companyDiff",
        "description": "기간간 공시 텍스트 변경 비교. 사업 방향 전환, 리스크 변화 감지.",
        "params": {
            "stockCode": _STOCK,
            "topic": {"type": "string", "description": "토픽명 (생략 시 전체 요약)"},
        },
        "required": ["stockCode"],
    },

    # ── 거버넌스/감사 ──
    {
        "name": "companyGovernance",
        "description": "지배구조 분석 (사외이사 비율, 감사위원, 최대주주 지분율, 시장 비교).",
        "params": {"stockCode": _STOCK},
        "required": ["stockCode"],
    },
    {
        "name": "companyAudit",
        "description": "감사 리스크 (감사의견, 감사인 변경, 계속기업 불확실성, 핵심감사사항).",
        "params": {"stockCode": _STOCK},
        "required": ["stockCode"],
    },

    # ── 기본 정보 ──
    {
        "name": "companyProfile",
        "description": "기업 기본 정보 (회사명, 업종, 시장, 대표자, 설립일).",
        "params": {"stockCode": _STOCK},
        "required": ["stockCode"],
    },
    {
        "name": "companySections",
        "description": "전체 데이터 구조 지도 (topic x period). 이 기업에 어떤 데이터가 있는지 한눈에 확인.",
        "params": {"stockCode": _STOCK},
        "required": ["stockCode"],
    },

    # ── 시장 전체 ──
    {
        "name": "marketScan",
        "description": (
            "한국 시장 전체 횡단분석. "
            "축: governance(지배구조), workforce(인력/급여), capital(주주환원), "
            "debt(부채), screen(스크리닝), profitability(수익성), growth(성장성)"
        ),
        "params": {"axis": {"type": "string", "description": "분석 축"}},
        "required": ["axis"],
    },

    # ── 보고서 (사용자가 명시적으로 요청할 때만) ──
    {
        "name": "companyReview",
        "description": (
            "정리된 종합 보고서 (마크다운). 사용자가 '보고서 만들어줘'라고 명시할 때만 사용. "
            "일반 분석에는 companyInsights + companyAnalysis로 직접 해석하라. "
            "section 지정 시 해당 섹션만 반환. "
            "유효 섹션: 수익구조, 자금조달, 자산구조, 현금흐름, 수익성, 성장성, 안정성, "
            "효율성, 종합평가, 이익품질, 비용구조, 자본배분, 투자효율, 재무정합성, "
            "가치평가, 지배구조, 공시변화, 비교분석, 매출전망"
        ),
        "params": {
            "stockCode": _STOCK,
            "section": {"type": "string", "description": "특정 섹션만 조회 (생략 시 전체)"},
        },
        "required": ["stockCode"],
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 도구 실행
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _executeTool(name: str, args: dict) -> str:
    """MCP 도구 실행."""
    import dartlab

    code = args.get("stockCode")

    try:
        if name == "companyReview":
            c = _getCompany(code)
            section = args.get("section")
            if section:
                return c.review(section).toMarkdown()
            return c.review().toMarkdown()

        if name == "companyInsights":
            return str(_getCompany(code).insights)[:8000]

        if name == "searchCompany":
            return _df(dartlab.search(args["query"]))

        if name == "companyFinancials":
            return _df(getattr(_getCompany(code), args["statement"], None))

        if name == "companyRatios":
            return _df(_getCompany(code).ratios)

        if name == "companyAnalysis":
            c = _getCompany(code)
            axis = args.get("axis")
            return _df(c.analysis(axis) if axis else c.analysis())

        if name == "companyValuation":
            return _df(_getCompany(code).valuation())

        if name == "companyForecast":
            return _df(_getCompany(code).forecast())

        if name == "companyShow":
            return str(_getCompany(code).show(args["topic"]))[:8000]

        if name == "companyTopics":
            return json.dumps(_getCompany(code).topics, ensure_ascii=False, indent=2)

        if name == "companyDiff":
            c = _getCompany(code)
            topic = args.get("topic")
            return str(c.diff(topic) if topic else c.diff())[:8000]

        if name == "companyGovernance":
            return _df(_getCompany(code).governance())

        if name == "companyAudit":
            return str(_getCompany(code).audit())[:8000]

        if name == "companyProfile":
            p = _getCompany(code).profile
            if hasattr(p, "__dict__"):
                return json.dumps(
                    {k: str(v)[:500] for k, v in p.__dict__.items() if not k.startswith("_")},
                    ensure_ascii=False, indent=2,
                )
            return str(p)[:8000]

        if name == "companySections":
            return _df(_getCompany(code).sections)

        if name == "marketScan":
            return _df(dartlab.scan(args["axis"]))

        return f"Unknown tool: {name}"

    except Exception as e:
        _log.error("Tool %s error: %s\n%s", name, e, traceback.format_exc())
        return f"Error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MCP 서버 생성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def create_server():
    """MCP 서버 인스턴스 생성."""
    try:
        from mcp.server import Server
        from mcp.server.lowlevel.server import ReadResourceContents
        from mcp.types import Resource, TextContent, Tool
    except ImportError as exc:
        raise ImportError("MCP SDK 필요: uv add 'mcp[cli]>=1.0'") from exc

    app = Server("dartlab", instructions=_MCP_INSTRUCTIONS)
    _log.info("MCP 서버 초기화 -- %d 도구", len(_TOOLS))

    @app.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name=t["name"],
                description=t["description"],
                inputSchema={
                    "type": "object",
                    "properties": t["params"],
                    "required": t["required"],
                },
            )
            for t in _TOOLS
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        _log.info("call_tool: %s(%s)", name, list(arguments.keys()))
        return [TextContent(type="text", text=_executeTool(name, arguments))]

    @app.list_resources()
    async def list_resources() -> list[Resource]:
        resources = [
            Resource(
                uri="dartlab://info",
                name="DartLab",
                description="한국 상장기업 전자공시 분석 도구 (DART)",
                mimeType="application/json",
            ),
        ]
        for code in _cache:
            resources.append(Resource(
                uri=f"dartlab://company/{code}/topics",
                name=f"{code} topics",
                description=f"{code} 조회 가능 토픽",
                mimeType="application/json",
            ))
        return resources

    @app.read_resource()
    async def read_resource(uri: str) -> list[ReadResourceContents]:
        uri_str = str(uri)
        if uri_str == "dartlab://info":
            import dartlab
            return [ReadResourceContents(
                content=json.dumps({
                    "version": getattr(dartlab, "__version__", "unknown"),
                    "tools": len(_TOOLS),
                    "cached": list(_cache.keys()),
                }, ensure_ascii=False, indent=2),
                mime_type="application/json",
            )]
        if uri_str.startswith("dartlab://company/"):
            parts = uri_str.replace("dartlab://company/", "").split("/", 1)
            if len(parts) == 2 and parts[1] == "topics":
                return [ReadResourceContents(
                    content=json.dumps(_getCompany(parts[0]).topics, ensure_ascii=False, indent=2),
                    mime_type="application/json",
                )]
        return [ReadResourceContents(content="Unknown resource", mime_type="text/plain")]

    return app


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 설치 헬퍼 -- dartlab mcp --install
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def installMcpConfig(targetDir: str | None = None) -> str:
    """프로젝트에 .mcp.json을 자동 생성한다.

    Returns:
        생성된 파일 경로.
    """
    import os
    from pathlib import Path

    root = Path(targetDir) if targetDir else Path.cwd()
    mcpFile = root / ".mcp.json"

    config: dict = {}
    if mcpFile.exists():
        try:
            config = json.loads(mcpFile.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            config = {}

    servers = config.setdefault("mcpServers", {})
    if "dartlab" in servers:
        return f"이미 등록됨: {mcpFile}"

    servers["dartlab"] = {
        "command": "uv",
        "args": ["run", "python", "-X", "utf8", "-m", "dartlab.mcp"],
    }
    mcpFile.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    return f"생성 완료: {mcpFile}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 엔트리포인트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_stdio():
    """stdio 모드로 MCP 서버 실행."""
    import asyncio
    try:
        from mcp.server.stdio import stdio_server
    except ImportError as exc:
        raise ImportError("MCP SDK 필요: uv add 'mcp[cli]>=1.0'") from exc

    app = create_server()

    async def _main():
        async with stdio_server() as (read_stream, write_stream):
            _log.info("DartLab MCP 서버 시작 (stdio)")
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(_main())


if __name__ == "__main__":
    run_stdio()
