# 00. 현재 상태와 조사 Thesis

Date: 2026-06-17 KST
Mode: 조사 전용. 구현 없음.

## 1. DartLab을 다시 이해한 결과

DartLab은 단순 재무제표 라이브러리가 아니다. 현재 구조는 다음 네 축을 동시에 겨냥한다.

| 축 | 현재 자산 | 혁신성의 의미 |
| --- | --- | --- |
| 원천 데이터 | DART/EDGAR/gather/provider/pipeline, parquet artifact | 원천 row를 근거로 삼는 분석 OS |
| 분석 엔진 | scan/frame/synth/reference, analysis/credit/macro/quant/industry/story | 회사간, 기간간, 시장간, 엔진간 비교 가능성 |
| AI 작업대 | Skill OS, canonical tools, MCP protocol, evidence refs | AI가 외워 답하지 않고 도구와 근거로 답하는 구조 |
| UI 작업대 | public/local shared runtime, data/fetch SSOT, local API gate | 같은 데이터 계약을 브라우저와 로컬 앱에서 재사용 |

`operation.philosophy` 기준의 핵심은 "많은 기능"이 아니라 비교 가능성과 근거 환류다. 따라서 기술 후보도 "더 멋진 스택"이 아니라 다음 질문에 답해야 한다.

1. 같은 데이터를 더 낮은 메모리로 더 넓게 비교하게 하는가?
2. 분석 결과가 어느 원천 row/job/run에서 왔는지 추적 가능한가?
3. AI가 tool/evidence 계약을 어기면 자동으로 드러나는가?
4. public/local UI가 같은 데이터 계약을 유지하면서 더 빠르게 탐색하게 하는가?
5. CI가 통과/실패뿐 아니라 어떤 증거 묶음으로 통과했는지 남기는가?

## 2. 현재 강점

### Search productization

`mainPlan/search-productization`은 이미 단순 검색을 넘어 운영형 retrieval fabric에 가깝다.

- `sourceManifest.py`, `sourceCatalog.py`, `sourceCatalogMerge.py`: source별 snapshot과 manifest.
- `facetPlanner.py`: receipt/date/report/company/freshness facet 추출.
- `answerability.py`: facet mismatch를 no-answer 사유로 내림.
- `evidencePack.py`: sourceRef, source, report, section, date, snippet evidence card.
- `memoryCard.py`: LLM turn에서 재사용 가능한 compact evidence.
- `goldLog.py`, `qualityGate.py`, `canaryPack.py`: query-log gold와 canary 운영.

결론: vector DB를 붙이는 방식은 우선순위가 낮다. 현재의 sparse-first, facet-first, evidence-first 검색 구조를 AI workbench와 UI에 더 깊게 연결하는 것이 맞다.

### AI/MCP surface

`src/dartlab/ai/tools/registry.py`는 다음 규칙을 이미 코드로 강제한다.

- 데이터 단일 호출은 `EngineCall` 우선.
- `RunPython`은 EngineCall 결과 후처리, 다단 결합, Polars 가공 전용.
- `ReadSkill`과 `ReadCapability`로 Skill OS와 public API docstring을 먼저 탐색.
- `WebSearch`는 외부 최신 정보용으로 분리.

`src/dartlab/mcp/protocol.py`는 ask, ReadSkill, ReadCapability, EngineCall, RunPython 등 canonical surface를 MCP로 노출한다.

결론: LangGraph/CrewAI 같은 agent framework로 본체를 갈아엎을 필요가 없다. 더 필요한 것은 structured tool schema, execution trace, ref/evidence 검증이다.

### UI data SSOT

`ui/packages/runtime/src/data/fetch/request.ts`는 origin 해소, in-flight dedup, TTL cache, resilient fetch, Parquet row read를 한 진입점으로 묶는다. `data/origins/registry.ts`는 HF/HF range/news/naver/local gate를 origin registry로 다룬다.

`ui/packages/runtime/src/adapters/local/api/stream.ts`와 `sources/aiSource.ts`는 local AI stream을 `AiStreamEvent`로 전달하고, `TEXT_MESSAGE_CONTENT`, `TOOL_CALL_RESULT`, `RUN_ERROR` 같은 AG-UI 호환 이벤트 표면을 이미 갖는다.

결론: 프론트 혁신은 framework 재작성보다 browser-side Parquet, virtualized evidence table, visual/a11y regression을 현 data SSOT에 흡수하는 쪽이다.

### CI/Test operation

`tests/run.py`는 gate, tier, deps, command, env, timeout을 모두 보유하는 CI SSOT다. `.github/workflows/ci-fast.yml`은 matrix dispatch와 artifact upload만 담당한다.

결론: 새 품질 시스템을 추가하지 말고, evidence artifact manifest, visual regression, lineage audit, ty shadow gate를 `tests/run.py` gate로 흡수해야 한다.

## 3. 현재 병목과 과장 제거

### DuckDB OOC 과장

`DuckDbCrossScan.aggregate()`는 현재 아래 경로다.

1. Polars LazyFrame을 `collect(engine="streaming")`.
2. 결과 DataFrame을 DuckDB in-memory connection에 등록.
3. `SELECT * FROM lf` 후 Polars로 반환.

이 경로는 DuckDB가 Parquet를 직접 읽으며 filter/projection pushdown과 spill을 담당하는 구조가 아니다. 따라서 "OOC god mode"라는 주석은 현 구현과 불일치한다.

조사 결론:

- 현 구현을 유지한다면 DuckDB는 fallback relation wrapper일 뿐이다.
- 혁신 후보는 source manifest/path list를 받아 `read_parquet(...)` 또는 S3/HTTPFS scan을 DuckDB가 직접 수행하는 새 cross scan arm이다.
- 이 후보는 `mainPlan/polars-gpu-backend`와 충돌하지 않는다. GPU는 compute-bound opt-in, DuckDB source scan은 memory-bound/OOC arm이다.

### AI 실행 trace 부족

도구 표면은 강하지만, user-facing stream, tool result, evidence ref, final answer 사이의 추적성은 더 강화할 수 있다.

필요한 보강:

- tool call input/output schema snapshot.
- ref issuance ledger.
- answer sentence와 sourceRef binding.
- GenAI/agent trace 속성 중 민감정보 제외 원칙.

### UI 증거 탐색성 부족

data SSOT는 좋지만 사용자가 evidence card, sourceRef, query-log gold, lineage를 탐색하는 workbench 경험은 아직 더 커질 수 있다.

필요한 보강:

- large table virtual scrolling.
- sourceRef/evidence card browser.
- browser-side Parquet inspect.
- visual regression과 aria snapshot으로 UI 계약 고정.

### mainPlan 분산 위험

관련 PRD가 이미 많다.

- `search-productization`
- `ai-workbench-connector`
- `polars-gpu-backend`
- 현재 data workbench 계약
- 현재 UI platform 계약
- `terminal-improvement`

따라서 이 조사는 새 메가 프로젝트가 아니라 우선순위와 흡수 지도를 제공한다. 실제 구현은 기존 소유 PRD 안으로 들어가야 한다.

## 4. 조사 Thesis

### Thesis A: Data plane 혁신은 "더 큰 엔진"이 아니라 source-native scan이다.

DartLab은 이미 Polars, Parquet, DuckDB, pyarrow, HF range reader를 쓴다. 다음 성장은 Spark/Ray가 아니라 source manifest를 보존한 채 DuckDB/Polars/browser가 같은 sourceRef를 읽는 구조다.

### Thesis B: AI 혁신은 agent framework가 아니라 evidence contract다.

DartLab은 Skill OS와 canonical tools를 이미 갖고 있다. 새 framework를 올리는 것보다 MCP/AG-UI/structured outputs/trace를 통해 tool, sourceRef, answerability를 검증해야 한다.

### Thesis C: UI 혁신은 landing 재작성보다 inspection loop다.

사용자는 "예쁜 페이지"보다 공시 원문, 재무 row, evidence card, 검색 결과, AI 답변의 연결을 빠르게 확인해야 한다. Browser Parquet, virtual table, sourceRef deep link, visual regression이 더 큰 효용이다.

### Thesis D: CI 혁신은 gate 수 증가가 아니라 proof bundle이다.

이미 gate가 많다. 다음 단계는 각 gate가 남기는 JSON evidence를 하나의 release/readiness proof로 묶는 것이다.

## 5. 기준선

이번 조사 기준의 "혁신성 있음"은 다음 중 최소 2개를 만족해야 한다.

1. 기존 공개 API를 늘리지 않고 성능/근거/운영성을 개선한다.
2. search/AI/UI/CI 중 둘 이상을 연결한다.
3. sourceRef 또는 lineage를 더 강하게 만든다.
4. `tests/run.py` 또는 existing audit gate에 들어갈 수 있다.
5. `tests/_attempts`에서 작은 실측으로 검증 가능하다.

"혁신성 없음" 또는 "기각" 기준은 다음과 같다.

1. 프레임워크 교체가 주효과다.
2. public API가 늘어나는데 evidence contract는 좋아지지 않는다.
3. 데이터 lineage/sourceRef가 약해진다.
4. 현재 mainPlan의 완료 경계와 충돌한다.
5. 운영자가 새 서버/클러스터/스토리지를 상시 관리해야 한다.
