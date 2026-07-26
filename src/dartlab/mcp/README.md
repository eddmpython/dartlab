# mcp/ — L4 외부 LLM 진입점

> Model Context Protocol 서버 — Claude Desktop / Codex CLI / Cursor 등 외부 도구가 dartlab 호출하는 진입점.

---

## 진입점

```bash
# stdio (로컬)
claude mcp add dartlab -- dartlab mcp

# 또는 코덱스 / cursor
codex mcp add dartlab -- dartlab mcp
```

`dartlab mcp` 명령 = `dartlab.cli.main:main mcp` → `dartlab.mcp.server` 시작.

---

## 공개 tool 카탈로그

| tool | 역할 |
|------|------|
| `ask` | 자연어 질문 → AI 워크벤치 답변 + ref |
| `ReadSkill` | Skill OS 257 노드 검색 |
| `ReadCapability` | dartlab 공개 API docstring 검색 |
| `EngineCall` | 단일 capability 1회 호출 (apiRef + args) |
| `RunPython` | Polars 다단 계산 (ref 발급) |
| `CompileVisual` | 차트 spec codegen → visualRef |
| `SaveArtifact` | 큰 표/차트 별도 저장 → artifactRef |
| `GroundingCheck` / `LookAheadGuard` | evidence flow 가드 |
| (자동 생성, 후속) `ListPlugins` | 외부 plugin 목록 (T5-5) |

총 ~32 tool 수동 등록. `ai/tools/_autogen.py` (T11-1) 로 120+ 자동 변환 후속.

---

## 룰

- L4 소비자 — 다른 계층 import 자유 (L0~L3 + L1.5)
- 외부 LLM 진입 → 본문 untrusted (T2-5 audit + `wrapExternalInResult`)
- MCP 서버는 *상태 없음* (state-less) — 매 호출 독립 ref

---

## 관련

- [src/dartlab/skills/specs/runtime/mcp.md](../skills/specs/runtime/mcp.md) — MCP 본문 spec
- [src/dartlab/skills/specs/runtime/mcpWorkbench.md](../skills/specs/runtime/mcpWorkbench.md) — workbench 운영
- [src/dartlab/ai/tools/_autogen.py](../ai/tools/_autogen.py) (T11-1) — engine 함수 자동 tool
