# 09. 평가, ADR, 위험, 개선 원장

## 1. 평가 원칙

평가 대상은 구현되지 않은 제품의 성능이 아니라 이 계획의 구현 가능성, 현재 근거, 계약 완전성, 검증 가능성이다. 95점은 문서가 멋지다는 점수가 아니다. 구현자가 재조사 없이 시작할 수 있고, 실패를 기계적으로 차단할 수 있는지를 채점한다.

합격:

- 총점 95점 이상
- 핵심 영역별 최저점 충족
- kill gate 0
- 모든 만점 항목에 현재 근거, 목표 계약, 검증 방법, 인수 기준 존재

## 2. 독립 100점 루브릭

| 영역 | 배점 | 핵심 최저점 |
|---|---:|---:|
| A 제품 진실과 범위 | 12 | 12 |
| B 전수 catalog와 범위 증명 | 15 | 14 |
| C 전용 엔진과 기존 시스템 격리 | 16 | 15 |
| D 지식·근거·시간·재현성 | 15 | 15 |
| E 엔진 호출과 simulation | 9 | 8 |
| F RAG 선행 준비 | 10 | 9 |
| G 3D scene data contract | 8 | 7 |
| H 제품급 비기능 | 10 | 9 |
| I 실행 roadmap와 검증 loop | 5 | 5 |
| 합계 | 100 | 총점 95 이상 |

세부 판정은 각 영역에서 다음 네 증거가 있어야 만점이다.

1. 현재 상태의 실제 경로·revision·수치
2. typed target contract와 책임
3. test, command, metric
4. boolean 또는 수치 인수 기준

## 3. 현재 독립 평가

전문 평가자가 최종 문서군을 같은 rubric으로 채점한 뒤 이 절을 확정한다. 초안 단계의 자가 점수를 최종 점수로 쓰지 않는다.

| Round | 평가자 | A | B | C | D | E | F | G | H | I | 합계 | kill gate | 판정 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| R0 | 초기 적대 reviewer rubric | 미채점 | 미채점 | 미채점 | 미채점 | 미채점 | 미채점 | 미채점 | 미채점 | 미채점 | 미채점 | 0 | rubric 확정 |
| R1 | 독립 적대 reviewer | 12 | 14 | 15 | 14 | 7 | 9 | 8 | 10 | 4 | 93 | 0 | 실패, D/E/I 최저점 미달 |
| R2 | 독립 적대 reviewer | 12 | 14 | 16 | 15 | 9 | 10 | 8 | 10 | 5 | 99 | 0 | 합격, configured repo-set 1점 감점 |
| R3 | 독립 적대 reviewer | 12 | 14 | 16 | 15 | 9 | 10 | 7 | 10 | 5 | 98 | 0 | 합격, 최신 worktree census와 scene manifest 감점 |
| R4 | 독립 적대 reviewer | 12 | 15 | 16 | 15 | 9 | 10 | 7 | 10 | 5 | 99 | 0 | 합격, resident tile deep immutability 1점 감점 |
| R5 | 독립 적대 reviewer | 12 | 15 | 16 | 15 | 9 | 10 | 7 | 10 | 5 | 99 | 0 | 합격, CPU admission과 GPU readiness 순서 1점 감점 |
| R6 | 독립 적대 reviewer | 12 | 15 | 16 | 15 | 9 | 10 | 8 | 10 | 5 | 100 | 0 | reviewer 합격 뒤 공간 교차 감사에서 blocker 2건 발견 |
| R7 | 독립 적대 reviewer | 12 | 15 | 16 | 15 | 9 | 10 | 8 | 10 | 5 | 100 | 0 | 최종 합격, 공간 교차 감사 CLOSED, blocker 0 |
| R8 | 독립 적대 reviewer | 12 | 15 | 16 | 15 | 9 | 10 | 8 | 10 | 5 | 100 | 0 | 최신 HF drift 반영 재확인, blocker 0 |

R1 감점 근거는 프로젝트 계약 엔진 folder와 source digest 누락, capability schema authority 부재, durable control-plane SSOT 부재, dirty byte replay 불완전, simulator 실존 admission과의 불일치, existing ask/EngineCall mapping과 검증 명령 부족이었다. 공간·RAG 전문 검토에서는 ProjectionState, community lineage, immutable evidence lifecycle, SceneSourcePort와 QuestionConstellation의 세부 계약도 blocker로 제기됐다. P2에서 각 항목을 실제 파일과 인수 gate로 닫았다.

R2는 99점으로 모든 핵심 최저점과 kill gate를 통과했다. 유일 감점은 현재 4개 HF repo를 전부 실측했지만 미래 설정 변경 때 authority repo 집합을 동적으로 조립하는 함수와 mutation test가 없다는 점이었다. P3에서 `HF_REPO`, `HF_MEDIA_REPO`, `DATA_RELEASES[*].repo`의 합집합을 정본으로 만들고 configured repo 추가·누락·비설정 주입 test를 추가했다. 병행 공간 감사에서 발견된 DTO, 의미 LOD 보존 필드, visibility scope, AnswerDraft replay input, U8 승인 이름도 P3에서 닫고 R3를 요청한다.

R3는 최신 dirty worktree에 추가된 `lensProducts` 때문에 DATA_RELEASES 실측이 41에서 42로 변한 점과 SceneManifest의 generation/payload schema authority가 덜 닫힌 점을 감점했다. P4에서 current source digest와 42/32/10/39 split을 다시 고정하고, manifest/request/envelope/decoder/scheduler/parent-child/recovery equality를 타입과 mutation gate로 일치시켰다. 데이터 전문 감사가 추가로 찾은 capability eligibility 분모, C2 range terminal, simulator artifact semantic decoder tree도 P4에서 닫았다.

R4는 99점으로 B를 만점 복구했고 유일하게 scheduler resident tile의 shallow readonly를 감점했다. P5에서 decoded input의 ownership을 private resident store로 이전하고 buffer 없는 deep-readonly handle만 공개하며, stage와 recovery 직전 private byte digest를 다시 검증한 fresh copy만 renderer에 넘기도록 닫았다.

R5는 P5 불변성을 확인했지만 CPU resident admission이 GPU stage 성공 전 child readiness로 세일 수 있는 상태 공백을 감점했다. P6에서 CPU_ADMITTED, GPU_READY, VISIBLE, RECOVERING, QUARANTINED, EVICTED 상태와 stage/transition/recovery result 기록 API를 분리하고 accepted result 전 quorum과 parent eviction을 0으로 강제했다.

R6 적대 reviewer는 P6 뒤 100점을 부여했지만 공간 교차 감사 S6는 recovery 실패 뒤 RECOVERING 상태가 종결되지 않는 문제와 transition commit 전 child pin 및 100% coverage proof 부재를 발견했다. 이 때문에 R6 점수를 최종점으로 고정하지 않는다. P7에서 recovery terminal 전이, semantic fallback, coverage proof, atomic pin, duplicate와 out-of-order 차단을 계약과 mutation gate로 추가했다.

R7은 P7 뒤 전체 문서군을 다시 평가해 100점을 부여했다. 공간 전문가도 recovery terminal state, semantic tree fallback, all-child 또는 재계산된 100% coverage subset, atomic pin, memory-pressure race와 duplicate/out-of-order 차단을 CLOSED로 판정했다. A부터 I까지 핵심 최저점을 전부 충족했고 K01부터 K20까지 PASS, blocker 0이다.

최종 검증 중 `dartlab-data` live revision이 바뀌어 P8에서 4개 HF repo를 다시 전수 집계했다. R8은 새 revision `fa2adde3f796a6b5db8ff57f8ea30f4a85d554f7`, 전체 77,757파일과 304,535,378,430 bytes, format과 prefix 분포까지 문서와 원격이 일치함을 확인하고 100점을 재확정했다. 이 값은 고정 경계가 아니라 2026-07-18 13:45:51 Asia/Seoul 관측 기준선이다.

## 4. Kill gates

하나라도 해당하면 총점과 무관하게 실패한다.

| ID | 즉시 실패 조건 |
|---|---|
| K01 | DART, EDGAR, 기업별로 별도 우주 정의 |
| K02 | HF 전체, 엔진 전체, 블로그 전체 중 하나를 표본이나 선택 범위로 축소 |
| K03 | 현재 회사 수나 파일 수를 고정 경계로 사용 |
| K04 | EDGAR를 보조 또는 후속 source로 강등 |
| K05 | 2D force graph, point cloud, bubble을 3D 완성으로 포장 |
| K06 | 데이터 엔진 전에 renderer 구현 |
| K07 | 기존 engine, workbench, simulator가 Universe를 import |
| K08 | 기존 SSOT를 복제해 새 canonical source 생성 |
| K09 | runtime 불가 실측과 운영자 승인 없는 bake |
| K10 | 존재하지 않는 engine 또는 axis 발명 |
| K11 | OBSERVED, DERIVED, SIMULATED, ASSERTED, INFERRED 혼합 |
| K12 | locator, revision, time, engine version, parameter, seed 재현 필드 누락 |
| K13 | RAG를 vector later 한 줄로 미룸 |
| K14 | browser에 전체 원문·node·relation 일괄 적재 |
| K15 | 외부 문서와 blog를 trusted prompt로 처리 |
| K16 | 운영자 승인 전 public route, button, nav 노출 |
| K17 | 현재 저장소 실측 없이 stack 이름만 나열 |
| K18 | sample test로 전체 coverage를 주장 |
| K19 | broken ref, 근거 없는 claim, ID collision, snapshot 비결정성을 허용하며 제품급 선언 |
| K20 | 기존 시스템 무변경을 dependency와 file digest로 증명하지 못함 |

## 5. ADR

### ADR-001, root Universe는 하나

- 결정: source, market, company는 filter와 object namespace다.
- 기각: DART 우주, EDGAR 우주, 기업별 universe instance.
- 이유: 전체 관계와 cross-source evidence를 분절하고 사용자의 "전체" 요구를 위반한다.

### ADR-002, data engine first

- 결정: census, ID, provenance, query가 renderer보다 먼저다.
- 기각: attractive 3D prototype first.
- 이유: visual node가 무엇인지 증명하지 못한 상태에서는 다시 2D 장식이 된다.

### ADR-003, read-only downstream integration

- 결정: Universe만 기존 system을 소비한다.
- 기각: engine, simulator, UI workbench에 Universe hook 삽입.
- 이유: 기존 ownership과 SSOT를 오염시키고 rollback을 어렵게 한다.

### ADR-004, runtime SSOT

- 결정: live tree와 runtime catalog가 source와 query 기본이며, 감사에 필요한 최소 control-plane만 durable하다.
- 기각: prebuilt manifest, duplicated graph, baked scene를 기본 전제로 둠.
- 이유: project runtime rule과 source freshness를 지킨다.

### ADR-005, live tree와 declaration의 union

- 결정: HF live tree와 `DATA_RELEASES`를 reconcile한다.
- 기각: 어느 하나를 전체 truth로 사용.
- 이유: 현재 live-only path와 declared-empty slot이 모두 존재한다.

### ADR-006, capability union

- 결정: capabilities, registry, callable presence를 합쳐 drift를 보존한다.
- 기각: 현재 capability mirror만 사용.
- 이유: analysis 22 axis 누락 같은 gap을 숨기지 않는다.

### ADR-007, epistemic class 강제

- 결정: observation, deterministic derivation, simulation, authored claim, model inference, assumption 분리.
- 기각: generic fact node.
- 이유: simulation과 LLM이 원천 사실을 오염하는 것을 막는다.

### ADR-008, bitemporal plus operational time

- 결정: valid, period, filed, known, observed, ingested time 분리.
- 기각: 단일 date.
- 이유: PIT와 공시 정정 재현에 필수다.

### ADR-009, lazy row and cell

- 결정: business key 또는 revision-scoped locator로 지연 해소.
- 기각: 모든 행과 셀을 선 graph node화.
- 이유: 304.5GB source와 browser·graph capacity에 맞지 않는다.

### ADR-010, DuckDB and Arrow baseline

- 결정: 외부 graph/vector DB 전 in-memory baseline.
- 기각: Neo4j, Qdrant, GraphRAG를 선결.
- 이유: 기존 stack으로 요구를 못 푸는지 먼저 측정한다.

### ADR-011, 3D is projection

- 결정: knowledge ID와 scene coordinate 분리.
- 기각: force layout coordinate를 지식 저장.
- 이유: stable identity, mental map, non-3D 접근을 지킨다.

### ADR-012, existing AI workbench reuse

- 결정: 미래 RAG는 existing EngineCall과 ask workbench의 후속 tool surface.
- 기각: 별도 uncontrolled agent loop.
- 이유: evidence ref와 tool governance를 재사용한다.

### ADR-013, public exposure needs separate command

- 결정: local product completion과 public exposure를 분리.
- 기각: 구현 완료 시 route 자동 연결.
- 이유: 운영자가 직접 본 뒤 명령한다는 요구를 보장한다.

### ADR-014, durable Universe control plane

- 결정: snapshot, identity, mapping, taxonomy, schema descriptor, license, receipt, approval, invalidation은 `control.sqlite`와 content-addressed object store의 append-only state다.
- 기각: process memory, markdown ledger, 임시 log를 제품 정본으로 사용.
- 이유: source copy나 performance bake 없이도 decision과 execution replay를 지속하려면 Universe가 소유하는 최소 durable state가 필요하다.

### ADR-015, G0 metadata와 C2 payload crawl 분리

- 결정: G0는 revision, path, oid, byte, format의 C0/C1 census이고 schema와 row count는 U3 C2 lazy crawl이다.
- 기각: 304.5GB payload의 schema와 row count를 60초 metadata SLO에 결합.
- 이유: 전수 범위를 줄이지 않으면서 실행 불가능한 gate를 만들지 않는다.

### ADR-016, Universe-local SchemaDescriptor

- 결정: signature, type hint, live docstring, Skill OS 근거를 validated machine contract로 정규화하며 근거 부족 callable은 실행 차단한다.
- 기각: argsSchema가 없는 현재 catalog를 실행 준비 완료로 간주하거나 engine API를 수정.
- 이유: 현재 argsSchema 0, outputSchema 0이라는 실측 gap을 기존 시스템 변경 없이 닫아야 한다.

### ADR-017, simulator signed receipt only

- 결정: `admissionRegistry.py::AdmissionVerifier`가 검증한 기존 signed receipt만 simulation evidence 후보로 받는다.
- 기각: Universe가 별도 SimulatorReceiptEnvelope를 공식 simulator contract처럼 발명.
- 이유: issuer, signature, ruleHash, artifactHash, parent chain을 보존하고 scratch output의 승격을 막는다.

### ADR-018, ProjectionState와 scene ports

- 결정: stable coordinate의 input version을 ProjectionState로 명시하고 SceneSourcePort, TileSchedulerPort, RendererPort를 분리한다.
- 기각: snapshot만 같으면 좌표도 같다고 주장하거나 renderer가 knowledge query와 tile cache를 함께 소유.
- 이유: incremental mental map, rollback, resource recovery와 renderer 교체 가능성을 동시에 보장한다.

### ADR-019, configured HF authority set

- 결정: HF 전체 범위는 `HF_REPO`, `HF_MEDIA_REPO`, 모든 `DATA_RELEASES[*].repo`의 동적 합집합이다.
- 기각: 현재 관측된 4개 repo ID를 expected 상수로 유지.
- 이유: 새 private 또는 domain repo가 설정에 추가될 때 Universe 범위가 조용히 과거 상태로 고정되는 것을 막는다.

### ADR-020, 생성과 검증 재현성 분리

- 결정: model 호출은 generation receipt로 고정하고, VerifiedAnswerBundle은 immutable AnswerDraft byte와 verifier version으로 byte replay한다.
- 기각: non-deterministic model 재호출 결과가 항상 같은 답변 byte를 만든다고 주장.
- 이유: 생성 provider의 비결정성을 숨기지 않으면서 claim 검증 결과는 완전히 재현한다.

## 6. 명시 기각안

- 출처별 galaxy를 별도 DB로 만드는 구조
- current 2,664 company hard-code
- EDGAR를 future phase로 미루기
- `DATA_RELEASES`만 HF 전체라 부르기
- simulator mirror 994 selector를 전체라 부르기
- all capability pre-execution
- blog whole-document embedding only
- image/video metadata 무시
- LLM entity extraction을 canonical relation으로 자동 저장
- vector-only RAG
- all edge simultaneous render
- full graph force simulation in browser
- UMAP/ForceAtlas fresh coordinates every snapshot
- node마다 Three.js Object3D
- static landing Python emulation
- raw fetch and self cache in UI surface
- public button or route before operator approval

## 7. 위험 원장

| ID | 위험 | 가능성 | 영향 | 완화 | owner | 종료 조건 |
|---|---|---:|---:|---|---|---|
| R01 | HF tree와 semantic declaration drift | 높음 | 높음 | union census, orphan state | data engine | G0 100% reconcile |
| R02 | private repo 접근 환경 불일치 | 중간 | 높음 | visibility scope, access-denied fail | operator/security | private full census green |
| R03 | cross-source company false merge | 중간 | 치명 | corpCode/CIK anchor, unresolved default | identity | false merge 0 gold set |
| R04 | accounting concept false equivalence | 높음 | 높음 | mapping type와 conflict preservation | domain/data | mapping gold 100% |
| R05 | row identity drift | 높음 | 중간 | revision-scoped locator honesty | data | replay test green |
| R06 | catalog runtime latency | 중간 | 높음 | profile, projection read, delta | performance | p95 SLO green |
| R07 | premature bake pressure | 높음 | 높음 | Bake Decision gate | architecture/operator | approval evidence or runtime green |
| R08 | capability schema incomplete | 높음 | 높음 | reject active status, gap ledger | engine owners | G2 schema coverage 100% |
| R09 | simulation fact leakage | 중간 | 치명 | class invariant, receipt admission | simulator/validation | leakage mutation 0 |
| R10 | blog prompt injection | 높음 | 치명 | untrusted channel, tool policy | security/AI | adversarial corpus 0 escalation |
| R11 | citation supports wrong claim | 중간 | 치명 | claim verifier and counter evidence | AI/evidence | precision 98%+ |
| R12 | 3D mental map instability | 높음 | 높음 | pinned incremental projection | spatial | G5 stability green |
| R13 | browser memory and GPU overflow | 높음 | 높음 | semantic LOD, tile budget | renderer | G6 stress green |
| R14 | 2D graph presented as 3D | 중간 | 치명 | 3D checklist and review | product/QA | all criteria true |
| R15 | inaccessible canvas | 높음 | 높음 | semantic tree and keyboard parity | accessibility | manual and automated green |
| R16 | public/private cache bleed | 낮음 | 치명 | scope in plan and cache key | security | leakage tests 0 |
| R17 | existing dirty work overwritten | 중간 | 높음 | protected digest manifest | implementation | changed existing 0 |
| R18 | renderer stack churn | 중간 | 중간 | RendererPort and benchmark | renderer | candidate decision ADR |
| R19 | engine이 기존 data 또는 사용자 경로를 씀 | 중간 | 치명 | worker env redirect, write guard, protected digest | execution/security | protected mutation 0 |
| R20 | control-plane database 또는 CAS 손상 | 낮음 | 치명 | append-only, fsync, integrity check, head rollback | data engine | corruption drill 100% |
| R21 | dirty worktree가 commit digest만으로 재현 불가 | 높음 | 높음 | local CAS byte capture 또는 NONREPLAYABLE 차단 | provenance | dirty replay 100% |

## 8. 열린 결정과 종료 조건

핵심 제품 계약은 열려 있지 않다. 아래는 benchmark 뒤 고르는 implementation choice다.

| Decision | 후보 | 현재 default | 결정 시점 | 종료 증거 |
|---|---|---|---|---|
| persistent catalog 필요 여부 | none, DuckDB file, Parquet | none, runtime | U3 SLO 실패 후 | profile + operator approval |
| graph backend | DuckDB adjacency, Neo4j | DuckDB | U4 deep traversal benchmark | latency/cost comparison |
| vector backend | none, Qdrant, pgvector | none | lexical/graph ablation 후 | Recall gain + bake approval |
| projection artifact | runtime, persisted tiles | runtime | U5/U6 SLO 후 | runtime impossibility + approval |
| renderer | Three WebGPU, PlayCanvas | Three benchmark | U6 | same scene performance report |
| local service integration | standalone, FastAPI route | standalone | U8 | G0-G7 + operator approval |
| existing ask integration | standalone tools, workbench tools | standalone | U8 | RAG security + architecture approval |
| public exposure | none, read-only, compute service | none | operator direct review 후 | explicit command + new plan |

## 9. 전문가 토론 합성

### 데이터 엔진 관점

- HF live tree가 선언 registry보다 넓으므로 union reconcile이 필수다.
- capability mirror alone은 analysis axis를 놓친다.
- local simulator와 `data/` 전체 자동 scan은 scratch 오염을 만든다.
- Universe는 별도 L4 product integration layer 후보이나 attempts 졸업이 먼저다.

### 공간·RAG 관점

- 모든 행을 물리 node로 만들지 않고 virtual locator를 쓴다.
- statement와 evidence를 edge property보다 1급 객체로 둔다.
- stable 3D는 seeded hierarchy와 incremental pinning이 필요하다.
- spatial context는 retrieval prior이지 evidence가 아니다.
- RAG는 hybrid query, engine tool, RetrievalEvidencePack, counter-evidence를 함께 쓴다.

### 적대 reviewer 관점

- 제품 진실, full catalog, 격리, provenance, RAG, 3D, SLO, roadmap을 100점 rubric으로 분해했다.
- 95점 이상이어도 kill gate가 하나면 실패다.
- 현재 evidence, target contract, validation, acceptance 네 가지가 없는 항목은 만점이 아니다.

## 10. 개선 이력

| Round | 발견 | 개선 |
|---|---|---|
| P0 | 과거 renderer-first와 public 노출 위험 | 관련 제품 code 제거 상태를 전제로 data-engine-first 재기획 |
| P1 | `DATA_RELEASES`만으로 HF 전체를 정의할 위험 | live tree union과 drift state 추가 |
| P1 | data/media 두 repo만 세는 위험 | original/private repo를 포함한 4 repo 실측 |
| P1 | capability mirror를 전체로 오인 | runtime, registry, callable presence reconciliation |
| P1 | blog image만 보고 video/podcast 누락 | YouTube ID와 podcast metadata 계약 추가 |
| P1 | simulator 내부를 데이터 source로 scan할 위험 | receipt-only adapter와 SIMULATED 강제 |
| P1 | snapshot이 baked copy로 오인될 위험 | logical revision manifest, runtime default, Bake Decision 명시 |
| P1 | 3D 위치가 knowledge relation을 오염 | projection 분리와 spatial-prior-only 규칙 추가 |
| P1 | 95점 자체가 과장될 위험 | plan-quality score와 product performance 분리 |
| P2 | G0가 304.5GB schema/row count와 60초 SLO를 혼합 | C0/C1 metadata census와 U3 C2 lazy descriptor crawl 분리 |
| P2 | 엔진 contract folder, source digest와 schema gap이 불완전 | 전체 folder census table, SchemaDescriptor authority, catalog/execution coverage 분리 |
| P2 | 중요한 decision과 receipt의 durable SSOT가 없음 | append-only control.sqlite, CAS, head, supersede, rollback 계약 추가 |
| P2 | dirty worktree digest만으로 byte replay 불가 | clean commit 또는 local CAS byte capture, NONREPLAYABLE gate 추가 |
| P2 | simulator adapter가 실존 API와 어긋남 | AdmissionVerifier의 databasePath, artifactRoot, receiptId, trusted issuer 계약으로 교체 |
| P2 | engine이 기존 data와 cache를 쓸 수 있음 | worker env redirect, audit write guard, OS sandbox blocker, protected digest 추가 |
| P2 | existing ask와 EngineCall 결합이 추상적 | 실제 symbol, ToolResult, Ref, AnswerDraft, runGate mapping test 추가 |
| P2 | evidence와 spatial overlay lifecycle이 모호 | immutable RetrievalEvidencePack, AnswerDraft, VerifiedAnswerBundle과 QuestionConstellation 계약 추가 |
| P2 | stable 3D coordinate의 선행 상태와 port가 불명확 | ProjectionState, community lineage, proxy 보존식, 세 scene port와 U5B 결정 추가 |
| P3 | 현재 HF 4개가 미래에도 고정될 위험 | configured repo authority 동적 union과 add/missing/unconfigured mutation gate 추가 |
| P3 | scene port DTO와 stale 판정 입력이 불완전 | TileRequest, decoded tile, transition, camera, selection, pick, budget DTO와 apply result 완결 |
| P3 | 의미 LOD가 source, period, statement, relation direction을 잃어도 통과 가능 | SceneProxy field, set digest, 방향별 conservation 식과 test 추가 |
| P3 | ProjectionState visibility와 G4R 재현 입력 모순 | visibilityScopeDigest와 immutable AnswerDraft, generation receipt 경계 추가 |
| P3 | U8 승인 이름이 표와 상태 전이에서 다름 | LOCAL_INTEGRATION_APPROVED, INTERNAL_SURFACE_BUILD_APPROVED, INTERNAL_VISUAL_ACCEPTED로 단일화 |
| P4 | dirty dataConfig에 lensProducts가 추가돼 census 수치 drift | current byte digest와 DATA_RELEASES 42/32/10, repo split 39/2/1로 재실측 |
| P4 | blocked eligible schema와 G2 100% 분모 모순 | eligibility를 schema 전에 고정하고 blocked eligible 0을 G2에 강제 |
| P4 | signed simulator artifact의 내부 의미가 증명되지 않음 | exact rule tuple schema descriptor, safe decoder, semantic bundle과 parent-tree coverage 추가 |
| P4 | scene manifest, child tile, recovery equality가 모호 | generation/payload schema, parent-advertised child, readonly decoded resident replay 계약 추가 |
| P5 | resident admission 뒤 decoded buffer가 변조돼 recovery를 오염할 수 있음 | private resident store ownership, digest-only immutable handle, upload 전 재검증과 mutation fixture 추가 |
| P6 | CPU resident admission이 GPU stage 전 readiness quorum에 포함될 수 있음 | stage, transition, recovery 결과 기반 상태 머신과 accepted 전 quorum/eviction 0 gate 추가 |
| P7 | recovery 실패 상태와 transition commit 전 coverage/pinning race | recovery terminal 상태 100%, semantic fallback, coverage proof, atomic parent/child pin과 race mutation gate 추가 |
| P8 | 최종 검증 중 `dartlab-data` live revision drift | 4개 repo 재전수 집계, revision·파일·bytes·format·prefix 기준선 갱신, 이전 수치 잔존 0 검증 |

P8 뒤 데이터 전문가는 CLOSED, 독립 reviewer R8은 100점, kill gate 0, blocker 0으로 최종 합격했다.

## 11. 개발자와 PM 이중 평가

### 11.1 Developer assessment

| 질문 | 현재 판정 | 구현 gate |
|---|---|---|
| 현재 repo에서 시작 위치가 명확한가 | PASS, attempts 경로와 함수 명시 | U0 file map 그대로 시작 |
| 기존 의존 방향을 지키는가 | PASS, reverse import 금지 | protected digest와 import test |
| runtime SSOT를 지키는가 | PASS, source/query runtime과 최소 durable audit state 분리 | Bake Decision 없는 accelerator 0, control head replay 100% |
| contract가 구현 가능한가 | PASS, typed field와 state 정의 | schema mutation test |
| test와 rollback이 충분한가 | PASS, phase별 명시 | 각 gate green 전 next 금지 |

Developer 최종 합격은 문서 점수가 아니라 U0부터 U7의 실제 test green으로만 확정한다.

### 11.2 Product manager assessment

| 질문 | 현재 판정 | 제품 gate |
|---|---|---|
| 하나의 전체 Universe인가 | PASS | source별 별도 root 0 |
| 사용자가 원한 전체 범위를 줄이지 않았는가 | PASS | HF, engine, content full ledger |
| 3D가 장식이 아닌가 | PASS, data-engine-first와 3D truth test | G0부터 U4 전 renderer 0 |
| 기존 제품을 위험하게 건드리지 않는가 | PASS | U0부터 U7 existing diff 0 |
| 공개 통제가 분리됐는가 | PASS | explicit operator command 전 exposure 0 |

PM 최종 합격은 운영자가 local 실물을 직접 보고 "DartLab 전체 지식 우주"라고 판단한 뒤에만 가능하다. 계획 점수 95 이상은 이 사용자 검수를 대체하지 않는다.

## 12. 문서 자체 검증

```powershell
uv run python -X utf8 -c "from pathlib import Path; fs=[Path('mainPlan/README.md'),*Path('mainPlan/dartlab-universe').glob('*.md')]; bad=[(str(p),i+1) for p in fs for i,line in enumerate(p.read_text(encoding='utf-8').splitlines()) if chr(0x2014) in line or chr(0x2013) in line]; print(bad); raise SystemExit(bool(bad))"
rg -n "2664|2,664|public route|공개 버튼" mainPlan/dartlab-universe
uv run python -X utf8 -c "from pathlib import Path; import re; root=Path('mainPlan/dartlab-universe'); files=list(root.glob('*.md')); links=[]; [links.extend((p, m) for m in re.findall(r'\\[[^]]+\\]\\(([^)]+\\.md)\\)', p.read_text(encoding='utf-8'))) for p in files]; missing=[(str(p),x) for p,x in links if not (p.parent/x).exists()]; print('files',len(files),'missing',missing); raise SystemExit(bool(missing))"
git diff --check -- mainPlan/README.md mainPlan/dartlab-universe
```

추가 audit:

- current file paths가 실제 존재하는지
- 숫자와 revision이 01의 source table과 일치하는지
- 공개 route 승인 표현이 없는지
- persistent artifact가 default로 쓰이지 않았는지
- existing file modification을 계획 초기 단계에 넣지 않았는지
- README 링크와 문서 번호가 완전한지

## 13. 최종 완료 기록

| 항목 | 최종 기록 |
|---|---|
| 완료 상태 | 제품급 구현 계획 완성, 제품 구현 전 |
| 독립 reviewer | R8, 100/100 |
| 핵심 최저점 | A부터 I까지 전부 충족 |
| kill gate | K01부터 K20까지 PASS, 0건 |
| blocker | 0건, 공간 교차 감사 CLOSED |
| 개선 loop | R1 93점 실패 뒤 P2부터 P8까지 개선, R8 최종 합격 |
| 문서 검증 | 12 files, Unicode dash 0, broken Markdown link 0, code fence 불균형 0, `git diff --check` PASS |
| 현재 source 검증 | `dataConfig.py` SHA-256와 42/32/10, repo 39/2/1, configured repo 4 일치. HF 4개 원격 revision과 77,757파일, 304,535,378,430 bytes 일치 |
| 변경 범위 | `mainPlan/README.md`와 `mainPlan/dartlab-universe/*.md`만 포함 |
| commit 정본 | 이 문서를 포함하는 git commit 자체를 정본으로 사용하며 순환적인 hash 자기기록은 하지 않음 |

이 기록은 미구현 제품의 성능 점수가 아니다. 구현자가 기존 시스템을 건드리지 않고 전용 Universe 데이터 엔진부터 시작할 수 있는 범위, 계약, 실패 차단, 검증 가능성의 독립 평가다. 실제 제품 완성 판정은 U0부터 U9까지의 gate와 운영자 직접 검수를 통과한 뒤에만 가능하다.
