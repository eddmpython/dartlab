# 08. 단계별 구현, 테스트, 롤백 계획

## 1. 실행 원칙

이 문서는 구현 승인 후의 순서를 정의한다. 현재 세션은 문서만 만든다. 운영자 승인 전 코드 작업은 시작하지 않는다.

모든 단계는 이전 gate의 기계 증거를 입력으로 받는다. "대체로 됨"이나 sample 성공으로 다음 단계로 넘어가지 않는다.

## 2. 전체 단계

| Phase | 목표 | 기존 파일 수정 | 다음 단계 차단 gate |
|---|---|---:|---|
| U0 | full census attempts | 0 | G0 |
| U1 | contract, ID, temporal, provenance | 0 | G1 |
| U2 | 전용 kernel과 capability executor | 0 | G2 |
| U3 | 전체 catalog, identity, evidence graph | 0 | G0+G1 재검증 |
| U4 | UI 없는 query와 RetrievalEvidencePack | 0 | G3, G4E |
| U5 | spatial projection 알고리즘과 semantic LOD | 0 | G5A fixture gate |
| U5B | ProjectionState runtime 또는 bake decision | 0, 승인 시 신규 파생 artifact만 | 제품 G5 |
| U6 | 독립 local 3D harness | 0 | G6, G7 renderer subset |
| U7 | standalone 생성 RAG evaluation | 0 | G4R, security subset |
| U8 | 승격·local integration·운영자 검수 | 승인된 최소 파일만 | 전체 G7 + 운영자 승인 |
| U9 | 공개 연결 | 별도 명시 승인 후 | 공개 release checklist |

U9는 자동 착수하지 않는다. U8이 성공해도 운영자가 공개를 명령하지 않으면 route와 button은 영구히 0개다.

## 3. U0, full census attempts

### 3.1 신규 파일

```text
tests/_attempts/dartlabUniverse/
  __init__.py
  census.py
  benchmark.py
  canonical.py
  sources/hfSource.py
  sources/releaseOverlay.py
  sources/capabilitySource.py
  sources/blogSource.py
  sources/contentCompanionSource.py
  sources/mediaSource.py
  sources/podcastSource.py
  validation/coverage.py
  testCensus.py
  testCoverage.py
  testProtectedPaths.py
```

### 3.2 함수

- `discoverConfiguredHfRepositories() -> ConfiguredRepoSet`
- `discoverHfRepositories(configuredRepoSet, token) -> list[PinnedRepo]`
- `enumerateHfTree(repo, revision) -> Iterator[DiscoveredFile]`
- `readReleaseOverlay() -> list[ReleaseDeclaration]`
- `enumerateCapabilities() -> CapabilityCensus`
- `enumerateBlog(root) -> BlogCensus`
- `enumerateContentCompanions(root) -> CompanionCensus`
- `reconcileMedia(catalog, hfTree, blogRefs) -> MediaCensus`
- `enumeratePodcasts(root) -> PodcastCensus`
- `buildCoverageLedger(discovery) -> CoverageLedger`
- `runMetadataCensusBenchmark(census) -> BenchmarkReport`
- `assertProtectedPathsUnchanged(before, after)`

### 3.3 테스트

- configured repo set이 `HF_REPO`, `HF_MEDIA_REPO`, 모든 `DATA_RELEASES[*].repo`의 합집합과 일치
- 현재 관측 configured repo 4개의 revision pin, count를 expected 상수로 사용하지 않음
- fixture에 5번째 configured repo를 추가하면 자동 발견되고 누락 시 G0 실패
- unconfigured repo를 DartLab authority로 주입하면 100% reject
- live file count와 discovered count 일치
- live-only와 declared-only path 분류
- 모든 format 분류 또는 explicit unsupported
- capability runtime/registry union
- blog 100% parse
- blog tree의 `brief.json`, `CREDITS.md`, cards, carousel, episode, published, youtube, imagegen과 unknown companion 100% 분류
- media referenced, unreferenced, broken reconciliation
- private access denied가 full G0를 실패시키는지
- 동일 revision census digest 결정론
- G0가 parquet와 Arrow payload body를 읽지 않는지 network operation assertion
- protected existing file digest 변화 0

### 3.4 인수 증거

`pytest` stdout이 아니라 machine-readable `CensusResult`를 test artifact로 남긴다. repo에 커밋하지 않고 CI artifact 또는 `tmp_path`만 사용한다.

### 3.5 rollback

신규 attempts directory만 제거하면 된다. 원천, runtime, UI, data file은 변경되지 않는다.

## 4. U1, contract와 identity

### 4.1 신규 파일

```text
tests/_attempts/dartlabUniverse/
  contracts.py
  ids.py
  temporal.py
  provenance.py
  controlPlane/store.py
  controlPlane/cas.py
  identity/resolver.py
  identity/ledger.py
  identity/dartIdentitySource.py
  identity/edgarIdentitySource.py
  identity/conceptMapping.py
  testContracts.py
  testIds.py
  testIdentity.py
  testTemporal.py
  testProvenance.py
```

### 4.2 함수

- `canonicalJson(value) -> bytes`
- `logicalId(kind, canonicalTuple) -> str`
- `versionId(logicalId, revisionTuple) -> str`
- `resolveOrganization(identifierRefs, ledger) -> ResolutionResult`
- `resolveConcept(sourceConcept, mappingLedger) -> MappingResult`
- `enumerateDartIdentities() -> Iterator[IdentityEvidence]`
- `enumerateEdgarIdentities() -> Iterator[IdentityEvidence]`
- `appendControlDecision(record, expectedHead) -> ControlHead`
- `captureDirtyInput(path, cas) -> DirtyCaptureRef`
- `validateStatement(statement) -> ValidationReport`
- `validateEvidence(evidence, snapshot) -> ValidationReport`
- `asOfFilter(statement, validAt, knownAt) -> bool`

### 4.3 test corpus

- DART corpCode와 stockCode 변경
- EDGAR CIK와 ticker 변경
- 동명이인 기업
- cross-listed legal entity candidate
- merger, spin-off, delisting, relisting
- K-IFRS와 US-GAAP exact/broader/narrower/unresolved mapping
- filing correction과 retraction
- blog block rewrite와 deletion
- business-key 없는 parquet row locator
- `src/dartlab/providers/dart/company.py`의 corpCode, stockCode, name evidence와 변경 fixture
- `src/dartlab/gather/edgar/identity.py`의 CIK, ticker, title evidence와 변경 fixture
- control.sqlite crash, concurrent head, supersede, rollback, CAS missing object
- clean git input, dirty byte capture, capture-disabled nonreplayable input

### 4.4 인수 기준

- ID collision 0
- 동일 input ID 일치 100%
- 자동 false merge 0
- evidence/derivation coverage 100%
- PIT leakage 0
- correction과 tombstone replay 성공
- approved control decision만 query 입력으로 보임
- dirty `LOCAL_CAPTURED` byte replay 100%, `NONREPLAYABLE`의 G1 통과 0
- control plane corruption과 CAS digest mismatch 차단 100%

### 4.5 rollback

U1 신규 파일 제거. identity ledger는 attempts fixture이며 기존 identifier source를 수정하지 않는다.

## 5. U2, 전용 kernel과 execution

### 5.1 신규 파일

```text
tests/_attempts/dartlabUniverse/
  kernel.py
  execution/registry.py
  execution/schemaDescriptor.py
  execution/admission.py
  execution/runner.py
  execution/sandbox.py
  execution/receipts.py
  execution/simulatorReceiptSource.py
  execution/simulatorArtifactSchema.py
  execution/simulatorDecoderRegistry.py
  testKernel.py
  testCapabilityRegistry.py
  testExecution.py
  testSimulatorIsolation.py
```

### 5.2 함수

- `buildCapabilityRegistry(census) -> UniverseCapabilityRegistry`
- `extractSchemaDescriptor(capability, authorities) -> SchemaDescriptor`
- `validateSchemaDescriptor(descriptor, corpus) -> ValidationReport`
- `admitExecution(request, registry, policy) -> AdmissionDecision`
- `buildWorkerEnvironment(workerRoot) -> Mapping[str, str]`
- `installWriteGuard(allowlist) -> AuditGuard`
- `runCapability(admitted, cancelToken) -> ExecutionReceipt`
- `normalizeOutput(value, schema) -> OutputEnvelope`
- `verifySimulatorAdmission(databasePath, artifactRoot, receiptId, trustedIssuerConfigRef) -> RegistrationResult`
- `resolveSimulatorArtifactDescriptor(receipt) -> SimulatorArtifactSchemaDescriptor`
- `decodeSimulatorReceiptTree(rootReceipt, descriptors) -> SimulatorSemanticBundle`
- `validateSimulatorSemanticBundle(bundle, snapshot) -> ValidationReport`
- `replayExecution(receipt) -> ReplayResult`

### 5.3 fixture

- deterministic lightweight engine
- hidden preview axis
- invalid axis
- missing schema
- transient network failure
- slow and cancellable worker
- partial DataFrame
- simulator signed receipt valid/invalid issuer/broken chain/missing artifact
- simulator kind/rule/schema descriptor exact match, stale decoder, unknown schema, subject mismatch, parent role mismatch
- stochastic result missing seed, missing snapshot/assumption/asOf, receipt/decoded vintage mismatch
- hard-coded write, subprocess write, protected path mutation
- crash before and after CAS object commit과 동시 idempotency request

### 5.4 인수 기준

- live capability reconcile 100%
- invented axis 0
- candidate catalogCoverage 100%, eligible callable executionReadiness 100%
- 모든 candidate의 eligibility와 gap 상태 100% 분류, ineligible 항목은 explicit reason 필수
- eligible callable의 schema gap은 전부 validated descriptor로 폐쇄, blocked eligible 0
- schema widening mutation 100% reject, source digest 변경 시 descriptor 100% `STALE`
- timeout, cancel, retry, idempotency 통과
- deterministic digest 100%
- invalid simulator admission receipt reject 100%
- 등록 result root와 reachable parent receipt semantic descriptor/decode coverage 100%
- uninterpreted 또는 incomplete semantic artifact의 execution/graph 승격 0
- `SIMULATED` leakage 0
- worker allowlist 밖 write와 기존 보호 경로 mutation 0
- duplicate success receipt 0, crash orphan recovery 100%

### 5.5 rollback

신규 attempts execution layer 제거. engine, simulator, server를 수정하지 않았으므로 runtime rollback이 없다.

## 6. U3, 전체 catalog와 evidence graph

### 6.1 신규 파일

```text
tests/_attempts/dartlabUniverse/
  catalog/compiler.py
  catalog/descriptorCrawler.py
  catalog/snapshot.py
  catalog/delta.py
  graph/statements.py
  graph/relations.py
  graph/query.py
  testCatalog.py
  testSnapshot.py
  testDelta.py
  testEvidenceGraph.py
```

### 6.2 구현

- in-memory DuckDB table schema
- Arrow object, statement, relation, evidence batch
- row/cell virtual locator
- format-aware C2 schema와 row-count descriptor lazy crawl
- pinned range read 우선, 32MiB 이하 bounded whole-object fallback, 그 이상 range 불가 시 explicit terminal reason
- full discovery to catalog state transition
- snapshot root digest
- source delta and tombstone
- bounded graph traversal

### 6.3 인수 기준

- C0와 C1 100%
- C2 structured candidate가 `DESCRIBED`, `UNSUPPORTED_FORMAT`, `DESCRIPTOR_BLOCKED_RANGE`, `PARSE_ERROR`, `ACCESS_DENIED` 중 하나로 100% 종결
- descriptor-eligible Parquet, Arrow, JSON, NPZ, Markdown, YAML, image metadata의 `DESCRIBED` 100%, 다른 terminal 상태 0
- opaque binary의 magic, source meaning, explicit reason 없는 unsupported 분류 0
- `DESCRIBED` item의 schema fingerprint 100%, row count 또는 unavailable reason 100%
- every discovered item catalog state 보유
- source payload canonical copy 0
- same snapshot digest 100%
- delta 추가·수정·삭제 누락 0
- statement to original path 단절 0
- current 304.5GB fixture metadata census에서 RSS와 latency SLO 통과

### 6.4 Bake blocker

DuckDB file, parquet catalog, precomputed graph를 repo나 HF에 쓰지 않는다. runtime SLO가 실패하면 profile report와 대안을 먼저 운영자에게 제시한다.

## 7. U4, UI 없는 query와 RetrievalEvidencePack

### 7.1 신규 파일

```text
tests/_attempts/dartlabUniverse/
  query/planner.py
  query/structured.py
  query/lexical.py
  query/graph.py
  query/hybrid.py
  query/retrievalEvidencePack.py
  validation/claims.py
  fixtures/universeGoldenQueries.json
  testQueryPlanner.py
  testHybridQuery.py
  testRetrievalEvidencePack.py
  testPromptInjection.py
```

### 7.2 구현

- exact identity first planning
- structured, lexical, graph lane
- existing content index adapter
- capability selection and optional execution
- contradictory evidence search
- immutable RetrievalEvidencePack
- model 없는 locator, visibility, lane coverage G4E validator
- CLI formatter and JSON output

vector lane은 U4 baseline에 포함하지 않는다. baseline 대비 개선을 증명한 별도 attempt만 허용한다.

### 7.3 인수 기준

- exact Recall@1 100%
- golden Recall@20 95% 이상
- structured number 100%
- RetrievalEvidencePack locator completeness 100%
- public/private leakage 0
- prompt injection tool escalation 0
- 3D 없이 original drill-down 성공
- G4E 통과, AnswerDraft 생성은 아직 0

## 8. U5, spatial projection과 semantic LOD

### 8.1 신규 파일

```text
tests/_attempts/dartlabUniverse/
  spatial/contracts.py
  spatial/community.py
  spatial/communityLineage.py
  spatial/layout.py
  spatial/projectionState.py
  spatial/stability.py
  spatial/lod.py
  spatial/tiles.py
  fixtures/projectionSmall.json
  fixtures/projectionStress.py
  testSpatialContracts.py
  testLayoutDeterminism.py
  testLayoutStability.py
  testSemanticLod.py
```

### 8.2 benchmark

- deterministic anchor only baseline
- Leiden plus seeded 3D layout
- UMAP/HUMAP internal layout candidate
- bounded ForceAtlas2 refinement candidate
- incremental 1%, 5%, 20% delta

### 8.3 G5A fixture 인수 기준

- x/y/z valid 100%
- coordinate byte stability 100%
- 1% delta displacement p95 2% 이하
- cluster continuity 98% 이상
- community lineage 결정론 100%
- meaningPreservation 100%
- source, period, statement, evidence, relation type/direction conservation assertion 100%
- L0부터 L5 object, statement, evidence drill path 단절 0
- selected object loss 0
- persistent tile 0, 별도 승인 전

G5A는 두 snapshot fixture와 current graph를 한 process에서 검증하는 알고리즘 gate다. 제품 G5를 뜻하지 않는다.

## 9. U5B, Projection State Decision

### 9.1 runtime path 우선

이전 snapshot의 ProjectionState를 원천에서 다시 계산하고 다음 SLO를 측정한다.

- prior state replay p95 30초 이하
- 1% delta incremental p95 5초 이하
- RSS 2GB 이하
- quantized coordinate equality 100%

통과하면 `persistenceMode=EPHEMERAL`로 제품 G5를 닫고 U6로 간다.

### 9.2 Bake Decision

runtime SLO가 실패하면 자동 bake하지 않는다. profile, 병목, runtime 최적화 대안, 운영 비용, rollback을 운영자에게 제시한다. 승인 시에만 `APPROVED_DERIVED` ProjectionState를 신규 파생 artifact로 저장한다.

필수 필드:

- base projection state ID
- logical coordinate map
- community lineage
- compiler, schema, input, output digest
- quantization version
- visibility scope
- rollback state ID

원천 payload와 renderer tile은 포함하지 않는다. 승인 거절 시 U6는 차단된다.

## 10. U6, 독립 local 3D harness

### 10.1 신규 파일

기존 UI package와 landing route를 쓰지 않는다.

```text
tests/_attempts/dartlabUniverse/renderer/
  package.json
  vite.config.ts
  index.html
  src/contracts.ts
  src/sceneSourcePort.ts
  src/tileScheduler.ts
  src/residentTileStore.ts
  src/transitionCoverageVerifier.ts
  src/rendererPort.ts
  src/threeWebgpuRenderer.ts
  src/tileWorker.ts
  src/semanticTree.ts
  src/main.ts
  tests/renderer.spec.ts
  tests/accessibility.spec.ts
```

### 10.2 구현

- typed buffer renderer
- depth, occlusion, 6DoF camera
- GPU picking
- tile streaming and atomic LOD swap
- scene/snapshot/projection/visibility/generation stale envelope reject
- parent retention, coverage-complete child readiness, transition pinning, cancellation, CPU/GPU budget eviction
- semantic tree
- reduced motion
- WebGL2 fallback
- device loss recovery

### 10.3 인수 기준

- 2D 위장 방지 checklist 전부 통과
- renderer SLO 통과
- accessibility 자동·수동 gate 통과
- 30분 leak test 통과
- device loss 후 authoritative resident tile replay 100%
- stale 또는 scope mismatch tile 수용 0
- TileRequest와 envelope identity/digest field mutation 100% reject
- manifest 대비 visibilityScopeDigest 또는 projectionDigest mutation 100% reject
- payloadSchemaVersion mismatch 수용 0, stale generation tile 수용 0
- manifest root가 아니거나 parent childTileIds에 광고되지 않은 tile 수용 0
- stale camera, selection, pointer, transition apply 100% reject
- scheduler private resident store와 immutable handle로 device recovery replay 100%
- recovery 중 manifest generation과 다른 resident tile replay 0
- admitResident 뒤 producer envelope, pick map, node/edge buffer mutation이 residentPayloadDigest와 store byte를 바꾼 사례 0
- materialized consumer envelope, pick map, node/edge buffer를 변경한 뒤 재materialize해도 private store와 네 digest 변화 0
- materialized tile과 private store 사이 shared object reference 0
- ResidentTileHandle deep-readonly mutation compile failure와 runtime object freeze test 통과
- test-only corruption hook으로 private resident byte를 바꾸면 materialize/recovery digest reject 100%, GPU upload 0
- initial stage와 recovery upload 직전 nodeBufferDigest, edgeBufferDigest, pickMapDigest, residentPayloadDigest 재검증 100%
- resident admission과 materialize 성공 뒤 stageTile resource-pressure/reject 시 readiness quorum 증가 0, parent eviction 0, blank frame 0
- stageTile accepted와 matching generation의 recordStageResult 전 GPU_READY 전이 0
- 전체 child 또는 bounds와 semantic set 100%를 증명한 subset만 transition 준비 허용, 단순 child 개수 quorum 허용 0
- partial coverage, duplicate child, out-of-order result, stale preparationDigest와 coverage proof digest mutation 100% reject
- prepareTransition accepted 때 parent와 required child 전부 pin, commit result 기록 전 budget eviction 0
- GPU_READY coverage 충족과 commitTransition accepted 전 parent eviction 0
- commitTransition reject/resource-pressure 또는 generation cancel 때 child pin 잔존 0, parent 유지 100%, blank frame 0
- quorum 충족 직후 memory pressure fixture에서 pinned child eviction 0
- recovery accepted만 이전 GPU_READY/VISIBLE 복원, resource pressure는 CPU_ADMITTED, digest/scope/schema reject는 QUARANTINED, stale와 generation cancel은 EVICTED
- recovery terminal 결과마다 RECOVERING 잔존 0, 실패와 cancel 때 semantic tree fallback 가용 100%
- resource pressure를 success로 처리 0
- 공개 route, nav, button 0

### 10.4 cleanup

Playwright, Vite server, browser session을 종료한다. background process 0을 test teardown에서 확인한다.

## 11. U7, standalone RAG evaluation

### 11.1 신규 파일

```text
tests/_attempts/dartlabUniverse/
  rag/retriever.py
  rag/toolPlanner.py
  rag/generationReceipt.py
  rag/answerDraft.py
  rag/answerVerifier.py
  rag/verifiedAnswerBundle.py
  rag/questionConstellation.py
  fixtures/ragGold.json
  testRagQuality.py
  testRagAbstention.py
  testRagSecurity.py
  testExistingWorkbenchMapping.py
```

### 11.2 경계

- existing `dartlab.ask` 코드는 수정하지 않음
- Universe query와 existing public EngineCall을 standalone evaluator에서 조합
- model answer는 canonical graph write 불가
- spatial context는 prior only
- vector는 승인된 benchmark가 있을 때만

### 11.3 인수 기준

- G4R citation precision 98% 이상
- citation coverage 95% 이상
- numeric replay 100%
- immutable AnswerDraft와 verifier version 기반 VerifiedAnswerBundle digest replay 100%
- generation receipt 없는 AnswerDraft 수용 0
- abstention F1 95% 이상
- epistemic class 오류 0
- prompt injection escalation 0
- QuestionConstellation이 base coordinate를 바꾼 사례 0
- RetrievalEvidencePack mutation 0
- `ToolResult`, `Ref.payload`, `AnswerDraft.evidenceRefs`, `runGate` mapping mutation test 통과
- 기존 `engineCall`을 우회한 public apiRef 실행 0

## 12. U8, 승격과 local integration

U0부터 U7을 통과한 뒤에도 자동 승격하지 않는다. 먼저 ADR을 열고 `src/dartlab/universe/`를 신규 downstream layer로 등록한다.

### 12.1 승격 신규 파일 후보

[02-data-engine-architecture.md](02-data-engine-architecture.md)의 package tree를 따른다. attempts 구현을 그대로 복사하지 않고 public boundary와 docstring을 정리해 졸업한다.

`src/dartlab/universe/controlPlane/{store,cas,schemas}.py`는 `DARTLAB_UNIVERSE_HOME/control.sqlite`와 `objects/sha256`를 소유한다. 이 durable state는 source payload copy나 성능 accelerator가 아니라 snapshot, identity, mapping, taxonomy, schema descriptor, license, receipt, approval, invalidation의 재현성 정본이다. 승인된 migration, fsync, backup, integrity check, head rollback drill을 통과하기 전에는 local integration을 시작하지 않는다.

### 12.2 내부 surface 승인 상태 전이

```text
U0부터 U7 gate 완료
  -> 운영자가 harness를 직접 봄
  -> LOCAL_INTEGRATION_APPROVED 명시 명령
  -> stable Universe package, local server, contracts, runtime source 구현
  -> local integration test 통과
  -> INTERNAL_SURFACE_BUILD_APPROVED 명시 명령
  -> local app 전용 surface와 route 구현
  -> 운영자가 완성 local 화면 직접 검수
  -> INTERNAL_VISUAL_ACCEPTED 또는 수정 회귀
  -> U9 공개는 여전히 잠김
```

`LOCAL_INTEGRATION_APPROVED`는 UI surface와 route 권한을 주지 않는다. `INTERNAL_SURFACE_BUILD_APPROVED`는 local app의 surface와 `/universe` route만 허용하며 landing, public runtime, sitemap, nav 권한을 주지 않는다. 내부 surface를 만들 수 있는 승인과 완성 화면을 승인하는 행위를 분리한다.

### 12.3 승인 후 최소 existing file 후보

| file | 변경 목적 | gate |
|---|---|---|
| `src/dartlab/server/api/universe.py` | local-only query/job API 신규 | LOCAL_INTEGRATION_APPROVED |
| `src/dartlab/server/__init__.py` | local router 등록 | LOCAL_INTEGRATION_APPROVED |
| `ui/packages/contracts/src/universe.ts` | port DTO 신규 | LOCAL_INTEGRATION_APPROVED |
| `ui/packages/contracts/src/index.ts` | contract export | LOCAL_INTEGRATION_APPROVED |
| `ui/packages/runtime/src/adapters/local/sources/universeSource.ts` | localApi gate 소비 | LOCAL_INTEGRATION_APPROVED |
| `ui/packages/runtime/src/adapters/local/createLocalRuntime.ts` | port 배선 | LOCAL_INTEGRATION_APPROVED |
| `ui/packages/surfaces/src/universe/*` | 내부 local surface | INTERNAL_SURFACE_BUILD_APPROVED |
| `ui/apps/local/src/routes/universe/+page.svelte` | 운영자가 직접 여는 local-only entry | INTERNAL_SURFACE_BUILD_APPROVED |
| `ui/apps/local/src/routes/universe/+page.ts` | local route load와 no-public metadata | INTERNAL_SURFACE_BUILD_APPROVED |

`data/fetch/request.ts`, origin registry의 의미를 복제하지 않는다. public origin이 실제로 필요해지면 별도 변경안과 테스트를 먼저 제시한다.

기계 검사:

```text
landing/src/routes/** contains universe route = 0
landing sitemap/search/navigation contains universe = 0
public runtime imports local Universe source = 0
ui/apps/local route exists only after build approval
```

local entry는 `ui/apps/local` dev server에서만 열리고 landing build output에 포함되지 않는다.

서버를 붙이기 전 control-plane migration은 production-like temp home에서 2회 rehearsal한다. 기존 `data/`, lineage, UI cache를 migration 대상으로 삼지 않는다. 장애 시 server wiring을 끄고 이전 approved control head를 활성화하며 append-only invalidation을 남긴다.

### 12.4 여전히 금지

- `src/dartlab/__init__.py` root export
- public landing route
- public button, menu, nav
- sitemap과 search 노출
- production RAG service
- persistent index와 scene tile

각 항목은 별도 운영자 승인 대상이다.

## 13. U9, 공개 연결

운영자가 직접 local 실물을 본 뒤 공개를 명령한 경우에만 새 plan을 연다. 이 문서는 공개 위치와 UI를 미리 승인하지 않는다.

공개 change set에는 다음이 필요하다.

- 승인 문구와 scope
- public threat model
- public source visibility matrix
- capacity와 cost model
- accessibility manual evidence
- route/button/nav 정확한 diff
- feature flag와 one-change rollback
- canary와 telemetry
- 공개 후 rollback drill

## 14. 전체 test matrix

| 영역 | unit | property | integration | full census | performance | security | accessibility |
|---|---:|---:|---:|---:|---:|---:|---:|
| census | O | O | O | O | O | O |  |
| contracts/ID | O | O | O |  | O | O |  |
| temporal/provenance | O | O | O | O |  | O |  |
| capability execution | O | O | O | O | O | O |  |
| simulator isolation | O | O | O |  | O | O |  |
| query/RetrievalEvidencePack | O | O | O | O | O | O |  |
| projection/LOD | O | O | O | O | O |  | O |
| renderer | O |  | O |  | O | O | O |
| RAG | O |  | O | O | O | O | O |

sample fixture test는 full census gate를 대체하지 않는다.

## 15. 실행 명령

구현 후 기본:

```powershell
uv run pytest tests/_attempts/dartlabUniverse -q
uv run python -X utf8 tests/_attempts/dartlabUniverse/census.py --all --strict --format json
uv run python -X utf8 tests/_attempts/dartlabUniverse/benchmark.py --profile reference-local
uv run pytest tests/_attempts/dartlabUniverse/testExistingWorkbenchMapping.py -q
```

renderer:

```powershell
pnpm --dir tests/_attempts/dartlabUniverse/renderer test
pnpm --dir tests/_attempts/dartlabUniverse/renderer exec playwright test
```

승격 후에는 project canonical lint, architecture, typecheck, test 명령을 추가한다. 이 세션의 문서 검증은 [09-evaluation-decision-ledger.md](09-evaluation-decision-ledger.md)를 따른다.

## 16. Protected path 증명

dirty worktree가 있을 수 있으므로 `git status`만으로 무변경을 증명하지 않는다. U0 시작 시 기존 파일의 content digest manifest를 `tmp_path`에 만들고 종료 시 비교한다.

```text
protectedExisting =
  src/dartlab except newly approved universe package
  ui
  landing
  blog
  media
  data
```

기준:

- Phase U0부터 U7: changedExistingFiles 0
- user-owned preexisting dirty file digest도 시작·종료가 같아야 함
- 새 attempts files만 diff에 나타남

## 17. rollback 원칙

- U0부터 U7: 신규 attempts tree 제거
- stable package: root export와 existing importer가 없으므로 package disable, 단 control-plane approved history와 receipt는 삭제하지 않고 이전 head로 rollback
- local integration: router wiring과 runtime port를 feature flag로 끔
- persistent accelerator가 승인된 경우: active pointer를 이전 verified version으로 원복, 원천 영향 0
- public integration: 별도 canary rollback plan 없으면 시작 금지

데이터 원천을 변경하거나 삭제하는 rollback은 없다. Universe가 source owner가 아니기 때문이다.

## 18. 완료 정의

이 계획의 구현 완료는 다음을 모두 뜻한다.

- G0, G1, G2, G3, G4E, G5, G6, G4R, G7 기계 증거 통과
- 기존 시스템 reverse dependency 0
- public route/button/nav 0, 별도 공개 승인 전
- protected existing files 변경 0 또는 U8에서 승인된 최소 변경만
- 문서와 code contract 정합
- background process cleanup
- commit과 push 전 full scoped test green
- 완료 후 mainPlan 운영 규칙에 따라 `_done` 이관
