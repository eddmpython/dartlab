# 04. Progress Ledger

Date: 2026-06-17 KST

## 조사 로그

1. `CLAUDE.md`, project memory, Skill OS, `operation.architecture`, `operation.code`, `operation.testing`, `operation.apiContract`, `operation.ui`, `operation.dataLineage`를 기준 규칙으로 확인했다.
2. `mainPlan` 운영 규칙은 `feedback_mainplan_operation` 기준으로 확인했다. 새 구현 착수보다 현재 코드/데이터/엔진과 PRD 정합성·ROI 조사가 우선이다.
3. `mainPlan/search-productization`은 단순 검색 계획이 아니라 source manifest, evidence pack, query-log gold, canary, HF round-trip proof를 가진 운영형 검색 fabric으로 판정했다.
4. `mainPlan/ai-workbench-connector`는 AI 호스팅이 아니라 external AI가 DartLab evidence를 안전 조회하는 connector plane으로 판정했다.
5. `mainPlan/polars-gpu-backend`는 GPU 기본 도입이 아니라 opt-in 실측 PRD로 판정했다. DuckDB OOC와 GPU의 문제 영역을 분리했다.
6. 현재 data workbench와 UI platform 계약은 UI raw fetch와 framework rewrite를 막는 경계로 판정했다.
7. `src/dartlab/scan/io/cross.py`를 확인해 현재 `DuckDbCrossScan`이 source-native OOC가 아님을 기록했다.
8. `src/dartlab/providers/dart/search/*`를 확인해 vector DB 전면 교체가 부적합하다고 판정했다.
9. `src/dartlab/ai/tools/registry.py`와 `src/dartlab/mcp/protocol.py`를 확인해 AI 본체 교체보다 tool/evidence contract 강화가 우선이라고 판정했다.
10. `ui/packages/runtime/src/data/fetch/request.ts`, `data/origins/registry.ts`, `adapters/local/api/stream.ts`를 확인해 browser Parquet와 AG-UI mapping을 UI SSOT에 흡수해야 한다고 판정했다.
11. `tests/run.py`와 `.github/workflows/ci-fast.yml`를 확인해 새 검증은 CI Evidence Bus 형태로 gate SSOT에 들어가야 한다고 판정했다.
12. 외부 공식 자료로 Polars GPU, DuckDB Parquet/HTTPFS/WASM, MCP, AG-UI, OpenTelemetry GenAI, Structured Outputs, GitHub attestations, Playwright snapshots, uv/ty, Vite Rolldown, TanStack Virtual, OpenLineage를 확인했다.

## 결정

### D1. "DuckDB 도입"이 아니라 "source-native DuckDB scan"으로 명명한다.

이유:

- 현 의존성에는 이미 DuckDB가 있다.
- 현 `DuckDbCrossScan`은 Polars collect 이후 DuckDB 등록이므로 OOC claim이 약하다.
- 혁신 후보는 Parquet path/source manifest를 DuckDB가 직접 읽는 구조다.

### D2. Vector DB 전면 교체는 기각한다.

이유:

- 검색 제품화는 이미 sparse-first hybrid, source intent, facet planner, answerability, evidence card, query-log gold를 갖고 있다.
- dense retrieval은 R* 후보 안의 evidence sidecar로만 의미가 있다.

### D3. Agent framework 교체는 기각한다.

이유:

- Skill OS와 canonical tool registry가 DartLab의 차별점이다.
- 교체보다 MCP/AG-UI/structured outputs/trace 계약 보강이 더 직접적이다.

### D4. UI 재플랫폼은 기각한다.

이유:

- shared runtime과 data SSOT가 이미 완료 PRD로 정리되어 있다.
- UI 혁신은 browser Parquet, virtual table, sourceRef/evidence inspect, visual regression이다.

### D5. CI Evidence Bus는 P0 후보로 둔다.

이유:

- `tests/run.py`가 gate SSOT라 도입 위치가 명확하다.
- search/product/release proof가 이미 여러 JSON artifact로 흩어져 있다.

## 열린 질문

1. DuckDB source-native scan이 DartLab 실제 parquet layout에서 Polars streaming보다 RSS를 얼마나 줄이는가?
2. 내부 lineage JSON subset을 `search`와 `AI EngineCall` 양쪽에 붙일 때 schema가 과해지지 않는가?
3. AG-UI 공식 event taxonomy와 현 `AiStreamEvent` 이름을 그대로 맞출지, compatibility adapter를 둘지?
4. Browser Parquet Workbench는 public landing bundle budget을 넘지 않는가?
5. ty beta gate가 pyright와 충분히 다른 신호를 주는가?
6. Playwright visual baseline의 업데이트 권한과 drift 절차를 어떻게 둘 것인가?

## 다음 액션 후보

1. `tests/_attempts/crossScanOoc/README.md`와 micro benchmark scaffold 작성.
2. lineage event subset draft 작성.
3. AG-UI event mapping table을 `ai-workbench-connector`에 연결.
4. `tests/run.py` Evidence Bus schema 초안 작성.
5. Browser Parquet Workbench benchmark plan 작성.

## 완료 기준

이 조사 PRD는 다음 상태가 되면 `_done` 이동 후보가 된다.

1. P0 후보 5개가 각 owner PRD 또는 attempts 트랙으로 분리됨.
2. 최소 2개 후보가 local 실측 결과를 가진다.
3. kill list가 관련 PRD에 반영되어 scope creep를 막는다.
4. source ledger가 최신 공식 자료 기준으로 한 번 갱신된다.
