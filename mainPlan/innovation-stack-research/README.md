# 혁신성 조사 — DartLab 적용 가능 기술 스택

Status: 조사/우선순위 PRD v0.1
Date: 2026-06-17 KST
Scope: 구현 없음. DartLab의 현재 구조를 더 깊게 이해한 뒤, 외부 최신 기술을 흡수할 위치와 기각 기준을 기록한다.

## 한 줄 결론

DartLab의 혁신성은 "새 프레임워크를 붙이는 것"이 아니라, 공시/재무 원천 데이터, 검색 패브릭, Skill OS, AI workbench, UI 데이터 SSOT를 하나의 evidence-native analytical OS로 묶는 데 있다.

## 이번 조사에서 확정한 방향

1. 최우선은 DuckDB source-native OOC scan, Lineage-as-Guard, AG-UI/MCP 계약 강화, CI Evidence Bus, Browser Parquet Workbench다.
2. Polars GPU, ty, Rolldown, Structured Outputs/GenAI trace, Playwright visual regression은 opt-in 또는 shadow gate로 흡수한다.
3. Spark/Ray/Dask/Daft 전면 도입, vector DB 전면 교체, LangGraph/CrewAI 본체 교체, React 재플랫폼, Rust 전면 재작성은 현 단계에서 기각한다.

## DartLab 내부 관찰

- `src/dartlab/scan/io/cross.py`의 `DuckDbCrossScan`은 이름/주석상 OOC처럼 보이지만, 실제 구현은 Polars streaming collect 후 DuckDB에 등록한다. 진짜 혁신 후보는 "DuckDB 추가"가 아니라 "Parquet/source manifest를 DuckDB가 직접 읽는 cross scan"이다.
- `src/dartlab/providers/dart/search/`는 source manifest, facet planner, evidence pack, memory card, query-log gold, canary까지 이미 갖고 있다. 검색 혁신은 vector DB 교체가 아니라 이 운영형 검색 패브릭을 AI/UI/workbench로 승격하는 것이다.
- `src/dartlab/ai/tools/registry.py`와 `src/dartlab/mcp/protocol.py`는 ReadSkill, ReadCapability, EngineCall, RunPython, WebSearch, SaveArtifact 등의 canonical tool surface를 이미 갖고 있다. AI 혁신은 새 agent framework가 아니라 도구 계약, trace, evidence ref를 더 강하게 만드는 것이다.
- `ui/packages/runtime/src/data/fetch/request.ts`와 `data/origins/registry.ts`는 데이터 호출 SSOT를 이미 제공한다. UI 혁신은 raw fetch를 늘리는 것이 아니라 browser-side Parquet, virtualized evidence table, visual regression을 이 SSOT에 붙이는 것이다.
- `tests/run.py`는 CI gate SSOT다. 새 검증은 별도 CI 체계가 아니라 gate/evidence artifact를 이 파일에 흡수해야 한다.

## 문서 지도

- `tech/`: **기술별 살아있는 조사 원장 (SSOT).** 기술 하나당 파일 하나. 마지막 조사일 / 카테고리별 관찰 / 본 자료 / 채택 결정을 누적. 반복 재조사 방지용. 어떤 기술을 조사하기 전에 여기부터 본다.
- `00-current-state-and-thesis.md`: 현재 DartLab의 자산, 병목, 조사 thesis (2026-06-17 시점 스냅샷).
- `01-priority-stack-register.md`: 후보 기술 스택별 우선순위, DartLab 흡수 방식, 첫 검증.
- `02-fit-map-and-kill-list.md`: 기존 mainPlan과 연결, 기각 목록, 과잉 설계 방지.
- `03-source-ledger-and-next-research.md`: 공식 자료 검증 기록, 다음 실측 질문.
- `04-progress-ledger.md`: 조사 의사결정 로그.

> 참고: `00~04` 는 한 시점의 thesis 스냅샷이고, `tech/` 가 그 위에 얹는 살아있는 기술별 원장이다. 스냅샷이 낡아도 `tech/` 개별 파일은 조사할 때마다 갱신한다.

## 운영 규칙

- 이 조사 문서는 구현 착수 지시가 아니다.
- 구현 전에는 각 후보를 `tests/_attempts/<category>/` 또는 해당 mainPlan의 실험 트랙에서 먼저 검증한다.
- 공개 API를 늘리기보다 기존 `dartlab.search(...)`, `EngineCall`, `RunPython`, UI `data/fetch`, `tests/run.py`를 먼저 확장한다.
- 기존 완료 PRD와 충돌하면 `_done/data-workbench-ssot`, `_done/ui-platform-refactor`, `search-productization`, `ai-workbench-connector`, `polars-gpu-backend`의 경계를 우선한다.
