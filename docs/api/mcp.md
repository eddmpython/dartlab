---
title: MCP 서버
---

# MCP 서버

DartLab은 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 서버를 내장하고 있다. Claude Desktop, Claude Code, Cursor 등 MCP 호환 AI 어시스턴트에서 DartLab의 전체 기능을 직접 사용할 수 있다.

## 설치

```bash
uv add "dartlab[mcp]"
```

## 실행

```bash
# CLI
dartlab mcp

# 또는 모듈 직접 실행
python -m dartlab.mcp
```

## 클라이언트 설정

### Claude Desktop

`claude_desktop_config.json` 위치:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "dartlab": {
      "command": "uv",
      "args": ["run", "dartlab", "mcp"]
    }
  }
}
```

### Claude Code

CLI에서 직접 추가:

```bash
claude mcp add dartlab -- uv run dartlab mcp
```

또는 `~/.claude/settings.json` 또는 프로젝트 `.claude/settings.json`에 추가:

```json
{
  "mcpServers": {
    "dartlab": {
      "command": "uv",
      "args": ["run", "dartlab", "mcp"]
    }
  }
}
```

### Cursor

`.cursor/mcp.json`에 Claude Desktop과 동일한 형식으로 추가.

### 설정 자동 생성

각 플랫폼에 맞는 설정 예시를 자동으로 출력할 수 있다:

```bash
dartlab mcp --config claude-desktop
dartlab mcp --config claude-code
dartlab mcp --config cursor
```

## 도구 목록

MCP 서버는 **60개 도구**를 노출한다.

### 글로벌 도구 (16개) — stock_code 불필요

| 도구 | 설명 |
|------|------|
| `get_system_spec` | DartLab 시스템 스펙 조회 |
| `get_engine_spec` | 개별 엔진 스펙 조회 |
| `get_tool_catalog` | 전체 도구 카탈로그 |
| `search_company` | 기업 검색 (이름, 코드, 티커) |
| `download_data` | 데이터 다운로드 |
| `data_status` | 로컬 데이터 상태 확인 |
| `call_dart_openapi` | DART 원본 API 호출 |
| `call_edgar_openapi` | EDGAR 원본 API 호출 |
| `discover_features` | 기능 탐색 |
| `create_plugin` | 커스텀 플러그인 생성 |

### 기업별 도구 (44개) — stock_code 필수

기업별 도구를 호출할 때는 `stock_code` 파라미터가 자동으로 추가된다.

```
예: show_topic(stock_code="005930", topic="BS")
```

| 카테고리 | 주요 도구 |
|---------|----------|
| **공시 조회** | `show_topic`, `list_topics`, `get_sections`, `trace_topic`, `diff_topic` |
| **재무** | `get_financial_statements`, `get_timeseries`, `get_ratios`, `get_ratio_series` |
| **분석** | `get_insight`, `get_ranking`, `get_sector_info`, `get_valuation` |
| **리포트** | `get_report_data`, `list_report_types` |
| **스캔** | `scan_market`, `scan_governance`, `scan_workforce` |
| **차트** | `create_chart_spec`, `list_chart_types` |

## 리소스

MCP 리소스를 통해 구조화된 데이터에 직접 접근할 수 있다.

| URI | 설명 |
|-----|------|
| `dartlab://info` | 버전, 도구 수, 캐시 상태 |
| `dartlab://company/{code}/sections` | 공시 섹션 지도 |
| `dartlab://company/{code}/topics` | 사용 가능한 topic 목록 |
| `dartlab://company/{code}/ratios` | 재무비율 (55개 비율 + 복합지표) |

## 캐시

MCP 서버는 Company 인스턴스를 LRU 캐시로 관리한다:

- **최대 5개** 동시 캐시
- **TTL 600초** (10분) 후 자동 만료
- 캐시 가득 차면 가장 오래된 항목 퇴출

## 사용 예시

### Claude Desktop에서

> "삼성전자 재무상태표 보여줘"

Claude가 자동으로 `show_topic(stock_code="005930", topic="BS")` 호출.

> "AAPL과 MSFT의 ROE를 비교해줘"

Claude가 `get_ratios(stock_code="AAPL")`, `get_ratios(stock_code="MSFT")` 순차 호출 후 비교 분석.

> "현대차의 사업 리스크가 작년과 어떻게 달라졌는지 알려줘"

Claude가 `diff_topic(stock_code="005380", topic="riskFactors")` 호출.

### Claude Code에서

MCP 서버를 등록하면 Claude Code가 코딩 세션 중에 DartLab 도구를 활용할 수 있다:

- 재무 데이터 기반 코드 작성
- 기업 분석 자동화 스크립트 생성
- 공시 텍스트 파싱 결과 검증

## 아키텍처

```
Claude Desktop / Claude Code / Cursor
    ↕ (stdio, JSON-RPC)
DartLab MCP Server
    ↕
AI Tools Registry (ToolRuntime)
    ↕
DartLab Engines (dart / edgar / common)
```

MCP 서버는 DartLab의 AI 도구 레지스트리(`ToolRuntime`)를 MCP 프로토콜로 브릿지한다. 내부적으로 OpenAI function calling 스키마를 MCP Tool 형식으로 변환하므로, DartLab AI 엔진에 등록된 모든 도구가 자동으로 MCP에 노출된다.
