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
| `EngineCall` | `engineCallable=true`인 단일 capability 1회 호출 (apiRef + args) |
| `RunPython` | Polars 다단 계산 (ref 발급) |
| `CompileVisual` | 차트 spec codegen → visualRef |
| `SaveArtifact` | 큰 표/차트 별도 저장 → artifactRef |
| `PeerCompareN` / `DCFValuation` 등 | registry의 canonical 분석 primitive |

전체 이름과 JSON schema의 정본은 `tools/list`다. 광고 목록은
`mcp.protocol.mcpAdvertisedToolNames()`가 `ai.tools.registry.CANONICAL_V2`를 추종하며,
같은 목록이 `tools/call` 실행 allowlist다. 목록 밖 legacy alias와 workbench 내부 도구는
`tool_not_advertised`로 거부한다.

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
