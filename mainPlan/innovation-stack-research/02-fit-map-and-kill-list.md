# 02. Fit Map and Kill List

Date: 2026-06-17 KST
Mode: 조사 전용. 구현 없음.

## 1. 기존 mainPlan 흡수 지도

| 기존 PRD | 이번 조사에서 연결되는 후보 | 흡수 원칙 |
| --- | --- | --- |
| `search-productization` | Lineage-as-Guard, CI Evidence Bus, Browser Parquet evidence inspect | `dartlab.search(...)` 공개 표면 유지. evidence card/sourceRef/query-log gold를 강화 |
| `ai-workbench-connector` | MCP hardening, Structured Outputs, GenAI trace, Evidence Pack envelope | AI를 호스팅하지 않음. 외부 AI가 안전 조회하는 connector plane 유지 |
| `polars-gpu-backend` | Polars GPU opt-in, DuckDB OOC 비교 baseline | GPU는 compute-bound opt-in. OOC는 DuckDB source scan으로 별도 검증 |
| 현재 data workbench 계약 | Browser Parquet Workbench, origins registry 확장 | raw fetch 금지. `data/fetch`와 `data/origins` 아래로만 연결 |
| 현재 UI platform 계약 | Playwright visual/aria, TanStack Virtual | shared runtime과 public/local parity 유지 |
| `terminal-improvement` | sourceRef/evidence command, CI proof view, workbench command palette | 터미널은 새 분석 엔진 소유자가 아니라 evidence/workflow 소비자 |
| `table-export` | Evidence table export, sourceRef-bound export metadata | export artifact에 lineage/sourceRef metadata 포함 |

## 2. 기술별 소유권

### DuckDB source-native OOC

Owner PRD: `polars-gpu-backend` 또는 새 attempts 트랙
Code owner 후보:

- `src/dartlab/scan/io/cross.py`
- `src/dartlab/pipeline`
- `src/dartlab/providers/*/search/sourceManifest.py`

금지:

- 기존 `DuckDbCrossScan` 주석만 고치고 OOC 해결로 간주.
- public API에 SQL 문자열 직접 노출.
- sourceRef/manifest 없이 임시 parquet path만 넘김.

### Lineage-as-Guard

Owner PRD: 이 조사에서 설계 후 `search-productization`과 `ai-workbench-connector`로 분할
Code owner 후보:

- `src/dartlab/pipeline`
- `src/dartlab/providers/dart/search/*Manifest*.py`
- `src/dartlab/ai/contracts.py`
- `tests/audit`

금지:

- 처음부터 OpenLineage backend/Marquez 운영.
- lineage가 로그 문자열로만 남고 테스트 가능한 JSON이 없음.
- evidenceRef와 sourceRef가 분리되어 UI에서 추적 불가.

### AG-UI/MCP contract

Owner PRD: `ai-workbench-connector` + UI runtime
Code owner 후보:

- `src/dartlab/mcp/protocol.py`
- `src/dartlab/ai/tools/registry.py`
- `ui/packages/contracts`
- `ui/packages/runtime/src/adapters/local/api/stream.ts`

금지:

- local UI 전용 event와 external connector event가 따로 진화.
- raw trace를 사용자-facing evidence로 오인.
- MCP generated tools 부활.

### CI Evidence Bus

Owner PRD: 운영/테스트 규칙
Code owner 후보:

- `tests/run.py`
- `.github/workflows/ci-fast.yml`
- `.github/workflows/publish.yml`
- `tests/audit`

금지:

- YAML에 gate logic 중복.
- artifact path만 있고 JSON summary/schema 없음.
- realdata와 fixture 통과를 같은 release evidence로 취급.

### Browser Parquet Workbench

Owner 계약: Skill OS `operation.ui` (UI 런타임 데이터층) + `operation.architecture`
Code owner 후보:

- `ui/packages/runtime/src/data/fetch`
- `ui/packages/runtime/src/data/origins`
- `ui/packages/runtime/src/data/parquet`
- `landing/src/lib/data/duckdb*.ts`

금지:

- component에서 직접 `fetch(...)`.
- origin registry 우회.
- 브라우저에서 투자 판단용 계산을 새로 구현.

## 3. Kill List

### Spark/Ray/Dask/Daft 전면 도입

기각 이유:

- DartLab의 문제는 클러스터 스케줄러보다 sourceRef/evidence-bound local analytical workflow다.
- 운영자가 상시 클러스터를 관리해야 한다.
- `tests/run.py` fast/preflight 모델과 맞지 않는다.

재검토 조건:

- 단일 머신/DuckDB/Polars로 해결 불가능한 100GB 이상 정기 workload가 생기고, release proof에 클러스터 artifact가 필요해질 때.

### Vector DB 전면 교체

기각 이유:

- `search-productization`은 이미 source intent, facet, answerability, evidence card, query-log gold를 갖고 있다.
- dense retrieval을 전면화하면 no-answer, source isolation, first citation guarantee가 약해질 수 있다.

허용:

- R* 후보 안에서 chunk evidence를 고르는 sidecar.
- query-log gold로 recall/precision이 검증된 limited lane.

### LangGraph/CrewAI 본체 교체

기각 이유:

- DartLab의 본체는 Skill OS + canonical tool registry + evidence gate다.
- 새 framework는 도구 표면을 늘리고 운영 규칙을 희석할 가능성이 크다.

허용:

- 외부 connector interop demo.
- MCP client 또는 AG-UI client compatibility layer.

### React/Next 전면 재플랫폼

기각 이유:

- UI 공유 runtime, data/fetch, public/local parity가 이미 Svelte/Vite 구조로 정리되어 있다.
- 재플랫폼은 사용자 가치보다 회귀 위험이 크다.

허용:

- headless utility 수준의 TanStack Virtual.
- Playwright 기반 visual/a11y regression.

### Rust 전면 재작성

기각 이유:

- Polars/DuckDB/uv/Ruff/ty/Rolldown처럼 Rust 기반 성능은 이미 의존 도구로 흡수 가능하다.
- DartLab의 핵심 복잡도는 금융/공시 semantics와 evidence contract다.

허용:

- 병목이 실측된 작은 parser/indexer를 PyO3/maturin으로 분리하는 장기 후보.

### Notebook-first 제품화

기각 이유:

- DartLab의 운영 원칙은 public API, Skill OS, UI workbench, CI gates다.
- notebook은 재현성, gate, sourceRef 보존이 약해지기 쉽다.

허용:

- marimo 같은 notebook은 demo/diagnostic artifact로 제한.

### Lakehouse 과잉 도입

기각 대상:

- Iceberg, lakeFS, full metadata catalog server.

기각 이유:

- 현재는 HF manifest, source catalog, content index manifest가 더 가볍고 맞다.

허용:

- manifest hash, snapshot id, rollback pointer 같은 개념만 내부화.

## 4. 우선순위 재정렬 규칙

새 후보가 나오면 다음 순서로 판정한다.

1. 현재 DartLab 코드에 이미 anchor가 있는가?
2. sourceRef/evidence/lineage를 강화하는가?
3. public API 증가 없이 흡수 가능한가?
4. `tests/_attempts`에서 1일 안에 작은 실측이 가능한가?
5. 기존 mainPlan owner가 명확한가?
6. 실패해도 기존 사용자 workflow를 깨지 않는가?

위 6개 중 4개 미만이면 watch 또는 kill로 둔다.

## 5. 지금 당장 하면 안 되는 일

- `DuckDbCrossScan`을 "이미 OOC"로 홍보.
- 검색 품질 문제를 embedding/vector DB로 바로 치환.
- UI 성능 문제를 framework 재작성으로 치환.
- AI 답변 품질 문제를 agent framework 교체로 치환.
- CI 신뢰 문제를 gate 개수 증가로만 치환.
- public API를 기술 후보마다 하나씩 늘림.
