# viz/ — 차트 spec codegen

> dartlab 분석 결과를 *차트 spec* 으로 변환. 표현/전송 헬퍼 (비즈니스 로직 0).

| 모듈 | 역할 |
|------|------|
| `viz/charts/` | 차트 종류별 spec generator (line / bar / heatmap / candle) |
| `viz/display/` | 표시 형식 (finance / sections) |
| `viz/compile.py` | CompileVisual MCP tool wrapper |

## 룰

- 비즈니스 로직 0 — 모든 계산은 L2 엔진 결과 받기만
- shadcn defaults — 색·음영·border 임의 변경 금지 (memory/ui.md 2절)
- bento 12-col row 강행 (memory/ui.md 2절)

## 관련

- [memory/ui.md](../../../) — UI 규칙
- [src/dartlab/skills/specs/runtime/](../skills/specs/runtime/) — runtime 카테고리
