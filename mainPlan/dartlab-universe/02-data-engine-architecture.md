# 02. Universe 전용 데이터 엔진 아키텍처

## 1. 결론

Universe는 기존 데이터 작업대에 의미 로직을 끼워 넣는 기능이 아니다. 기존 source authority를 읽기 전용으로 소비하는 독립 제품 통합 계층이다.

초기 구현은 오직 `tests/_attempts/dartlabUniverse/`에 둔다. 기존 코드가 Universe를 모르고도 모든 census, identity, provenance, query 계약을 증명한 다음에만 `src/dartlab/universe/` 승격을 별도 ADR로 결정한다. 승격 전에는 `dartlab.universe()` 같은 공개 API를 만들지 않는다.

## 2. 의존 방향

```text
authoritative systems, unchanged
  HF repositories
  blog and media catalog
  dartlab public facade and live capability registry
  DART and EDGAR Company providers
  simulator receipts
  UI data workbench transport
            |
            | read only
            v
Universe adapters
  -> census and reconciliation
  -> identity and temporal resolver
  -> object, statement, evidence graph
  -> capability registry and executor
  -> structured and hybrid query
            |
            +-> future spatial projection
            +-> future RAG tools

forbidden reverse edges
  existing engine -> Universe
  simulator -> Universe
  UI fetch core -> Universe
  blog build -> Universe
```

### 2.1 기계 가드

Phase U0부터 다음 import가 0개인지 검사한다.

```text
src/dartlab/{analysis,credit,gather,industry,macro,providers,quant,scan,simulate,synth,story}/**
  imports dartlab.universe

ui/packages/runtime/src/data/**
  imports a Universe implementation module
```

기존 package가 새 package를 import하면 테스트 이전에 architecture gate가 실패한다.

## 3. 계층 배치

### 3.1 시도 단계

```text
tests/_attempts/dartlabUniverse/
  census.py
  contracts.py
  canonical.py
  sources/
  identity/
  graph/
  execution/
  query/
  validation/
  test_*.py
```

이 거처에서는 `tmp_path`와 in-memory DuckDB만 쓴다. repo에 catalog, index, embedding, tile을 생성해서 커밋하지 않는다.

### 3.2 졸업 후보

모든 U0부터 U4 gate를 통과하고 architecture 승인을 받으면 다음 신규 package를 후보로 한다.

```text
src/dartlab/universe/
  __init__.py                 # 내부 package 표식, root export 없음
  contracts.py
  canonical.py
  kernel.py
  catalog/
    census.py
    descriptorCrawler.py
    reconcile.py
    snapshot.py
    delta.py
  controlPlane/
    store.py
    cas.py
    schemas.py
  sources/
    hfSource.py
    releaseOverlay.py
    capabilitySource.py
    blogSource.py
    contentCompanionSource.py
    mediaSource.py
    podcastSource.py
    dartIdentitySource.py
    edgarIdentitySource.py
    simulatorReceiptSource.py
  identity/
    resolver.py
    aliases.py
    ledger.py
  graph/
    statements.py
    relations.py
    provenance.py
  execution/
    registry.py
    schemaDescriptor.py
    sandbox.py
    runner.py
    jobs.py
    receipts.py
  query/
    planner.py
    structured.py
    lexical.py
    graph.py
  validation/
    coverage.py
    temporal.py
    leakage.py
    replay.py
```

이 package는 기존 L0부터 L3를 바꾸는 shared core가 아니다. 여러 계층의 공개 surface를 소비하는 downstream product integration layer다. 정확한 architecture tier는 승격 ADR에서 `operation.architecture`와 Skill OS에 먼저 등록한다.

## 4. Kernel 내부 인터페이스

공개 DartLab API가 아닌 Universe 내부 계약이다.

```python
class UniverseKernel:
    def census(self, request: CensusRequest) -> CensusResult: ...
    def openSnapshot(self, refs: SourceRevisionSet) -> UniverseSnapshot: ...
    def resolve(self, ref: ExternalRef, snapshotId: str) -> ResolutionResult: ...
    def getObject(self, objectId: str, snapshotId: str) -> UniverseObject: ...
    def traverse(self, query: GraphQuery) -> GraphResult: ...
    def planQuery(self, query: UniverseQuery) -> QueryPlan: ...
    def execute(self, request: ExecutionRequest) -> UniverseExecution: ...
```

규칙:

- `census()`는 payload 전체를 내려받지 않는다.
- `openSnapshot()`은 원본 copy가 아니라 revision과 digest 묶음을 연다.
- `resolve()`는 불확실하면 `UNRESOLVED`를 반환하고 추측 merge를 하지 않는다.
- `execute()`는 live capability registry에 없는 engine/axis를 거절한다.
- 모든 반환은 snapshotId와 provenance completeness를 포함한다.

## 5. Source Adapter 공통 계약

```python
class UniverseSourceAdapter(Protocol):
    sourceKind: SourceKind
    def discover(self, scope: VisibilityScope) -> DiscoveryStream: ...
    def pin(self, discovered: DiscoveredSource) -> PinnedSource: ...
    def describe(self, pinned: PinnedSource) -> ResourceDescriptor: ...
    def open(self, locator: SourceLocator, projection: Projection) -> BytesOrRows: ...
```

오류는 예외 문자열로 소실하지 않고 다음 typed state로 바꾼다.

- `ACCESS_DENIED`
- `NOT_FOUND`
- `REVISION_MOVED`
- `UNSUPPORTED_FORMAT`
- `DESCRIPTOR_BLOCKED_RANGE`
- `SCHEMA_MISMATCH`
- `STALE_SOURCE`
- `RATE_LIMITED`
- `TIMEOUT`
- `PARTIAL`
- `CORRUPT`

`PARTIAL`을 success로 변환하지 않는다. 각 오류에는 sourceRef, operation, retryability, observedAt, causeCode를 붙인다.

## 6. Adapter별 책임

| adapter | 입력 authority | 출력 | 오류와 경계 |
|---|---|---|---|
| HF tree | repo id와 token scope | revision-pinned file resource | HEAD 이동 시 pinned revision 유지 |
| release overlay | `DATA_RELEASES` code revision | 의미 label, public, nested, expected repo | live tree를 삭제하거나 대체하지 않음 |
| DART identity | Company facade와 corp metadata | corpCode 중심 organization ref | stockCode 단독 merge 금지 |
| EDGAR identity | OpenEdgar, Company facade, ticker map | CIK 중심 organization ref | ticker 단독 merge 금지 |
| capability | `dartlab.capabilities()`와 registry | typed CapabilityRef와 drift | 내부 helper를 공개 capability로 승격 금지 |
| blog | git file와 Markdown AST | post, section, block, authored claim | HTML/Markdown은 untrusted content |
| media | `media/catalog.json`과 HF media tree | content-addressed media resource | orphan도 삭제하지 않고 상태화 |
| podcast | episode metadata와 publish record | episode와 external media locator | script 부재를 transcript로 위장 금지 |
| simulator receipt | 명시 등록된 receipt | `SIMULATED` execution and result | `data/` 전체 자동 scan 금지 |

### 6.1 HF Adapter

동작:

1. `dartlab.core.dataConfig`의 `HF_REPO`, `HF_MEDIA_REPO`, `DATA_RELEASES[*].repo`를 읽어 configured authority repo 집합 조립
2. repo별 full commit revision 고정
3. 해당 revision의 모든 path, LFS oid, size, extension 발견
4. header 또는 metadata만으로 format 판정
5. U0에서는 repo, revision, path, oid, size, format만 조사
6. parquet와 Arrow schema·row count는 U3 C2 descriptor crawl에서 pinned range read로 조사
7. `DATA_RELEASES` 의미 overlay 결합
8. live-only path는 `LIVE_UNREGISTERED`
9. declared-only path는 `DECLARED_EMPTY`, `FROZEN`, `MISSING` 중 하나

HF tree의 모든 payload를 내려받는 행위는 G0에서 금지한다. U3 C2에서 schema 조회가 range read로 불가능한 파일만 제한된 byte budget 아래 읽고 receipt를 남긴다.

### 6.1.1 Python network operation matrix

| operation | owner | network path | disk write | 허용 이유 |
|---|---|---|---|---|
| discover repo and pin revision | Universe `hfSource` | official `huggingface_hub.HfApi` metadata | 0 | 기존 release loader가 live unregistered tree를 열거하지 못함 |
| enumerate file metadata | Universe `hfSource` | pinned tree metadata | 0 | C0/C1 전수성 전용 |
| known semantic data query | existing public DartLab facade/provider | 기존 loader/gather/provider 경계 | 기존 계약 따름, worker sandbox 내부 | Universe가 원천 해석을 중복하지 않음 |
| arbitrary file C2 descriptor | Universe `hfSource.openRange` | pinned revision HTTP Range only | control-plane descriptor만 | live-only file schema 확인 전용 |
| bounded whole-object descriptor fallback | Universe `hfSource.openBoundedObject` | pinned revision, object size 32MiB 이하만 | worker temp only, 종료 시 삭제 | range가 불가능한 작은 descriptor 후보 |
| unbounded full file download | 없음 | 금지 | 금지 | Universe source 책임 아님 |
| UI data read | existing `data/fetch.request()` | registered origin | 기존 cache gate | UI transport SSOT |

`discover`, `pin`, `describe`는 metadata-only다. `openRange`와 `openBoundedObject`는 U3 descriptor crawler만 호출할 수 있고 allowlisted repo, pinned revision, max bytes, range count, response digest를 receipt에 남긴다. 32MiB보다 큰데 range descriptor를 만들 수 없는 object는 전량 다운로드하지 않고 terminal classification `DESCRIPTOR_BLOCKED_RANGE`와 row-count-unavailable reason을 남긴다. 이 상태는 census reconciliation에는 포함되지만 descriptor-eligible item의 U3 합격으로 세지 않는다. generic `download()` API는 만들지 않는다.

Attempts import allowlist:

- Python stdlib
- `huggingface_hub` metadata client
- `dartlab` root public facade와 `dartlab.capabilities()`
- registry module은 census read-only introspection에서만
- `dartlab.core.dataLoader` private helper 직접 호출 금지
- provider private helper 직접 호출 금지

### 6.2 Capability Adapter

세 원천의 합집합을 쓴다.

```text
liveCapabilities = dartlab.capabilities()
liveAxes         = actual engine registries
rootPresence     = callable(getattr(dartlab, name, None))
```

각 항목은 `MATCHED`, `CALLABLE_UNMIRRORED`, `MIRRORED_MISSING`, `HIDDEN_PREVIEW`, `SCHEMA_INCOMPLETE`로 reconcile한다. 현재 analysis 22축이 builder prefix 출력에서 누락되는 현상을 숨기지 않는다.

### 6.3 Blog, Media, Podcast Adapter

Markdown은 AST로 파싱하며 원문 offset을 잃지 않는다. `media/catalog.json`의 3,120 object, 2,808 file alias, 275 post mapping과 HF media tree를 병렬 reconcile한다. `blog/_podcasts/episodes`의 13개 `episode.yaml`, 13개 `published.json`은 episode metadata로 등록하되 추적 script가 없으면 transcript를 생성한 것으로 표시하지 않는다.

### 6.4 Simulator Receipt Adapter

Universe가 `src/dartlab/simulate` 내부 함수를 전수 import하거나 `data/` 78,164개를 자동 등록하면 local cache와 scratch가 지식으로 오염된다. 현재 실존 admission authority는 `src/dartlab/simulate/admissionRegistry.py`의 `AdmissionVerifier`와 signed append-only receipt다. Universe adapter 입력은 임의 envelope가 아니라 다음 네 locator다.

```text
databasePath
artifactRoot
receiptId
trustedIssuerConfigRef
```

adapter는 `AdmissionVerifier(databasePath, artifactRoot, trustedIssuers)`로 signature, issuer, artifact hash, ruleHash, revisionPolicy, coverage, parent chain과 receipt status를 검증한다. 이 검증은 byte와 admission claim의 무결성을 증명하지만 artifact byte 내부의 assumptions, seed, snapshot과 result schema를 자동 증명하지 않는다.

의미 해석은 Universe control plane의 승인된 `SimulatorArtifactSchemaDescriptor`가 별도로 담당한다.

```text
SimulatorArtifactSchemaDescriptor
  descriptorId
  receiptVersion
  kind
  ruleId
  ruleVersion
  ruleHash
  issuerExecutableHash
  artifactRole             VINTAGE_INPUT, ASSUMPTION_SET, LAW_SET, SIMULATION_RESULT
  artifactMediaType
  artifactSchemaVersion
  decoderRef
  decoderSourceDigest
  subjectHashRule
  parentRoleRules[]
  fieldBindings
  requiredSemanticFields[]
  stochastic
  validationCorpusRef
  validationReportRef
  reviewer
  status                   CANDIDATE, VALIDATED, STALE, REJECTED, SUPERSEDED
```

descriptor match는 receipt의 `receiptVersion + kind + ruleId + ruleVersion + ruleHash + issuerExecutableHash` exact tuple이다. decoder는 arbitrary code를 실행하지 않는 Universe-owned allowlisted JSON, Arrow 또는 binary parser이며 source digest가 바뀌면 `STALE`다. artifact schema version을 byte 안에서 확인할 수 없거나 subjectHashRule, parent role, required field binding이 맞지 않으면 의미 해석을 거절한다.

검증된 receipt tree와 descriptor tree를 결합한 뒤에만 다음 `SimulatorSemanticBundle`을 만든다.

- simulator capability ref, root receipt ID와 parent receipt IDs
- target refs, input source refs와 snapshotId
- assumptions, law refs, vintage refs
- receipt `knowledgeAsOf`, revisionPolicy, coverage, frequency, stepSpan, maxAdmittedStep와 decoded asOf/knownAt
- seedPolicy와 seed, deterministic이면 `NOT_APPLICABLE`
- simulator version, code revision, dependency fingerprint와 issuerExecutableHash
- result schema version, output locator, artifactHash와 inner output digest
- visibility, decode descriptor ID, decode report digest
- epistemic class 고정값 `SIMULATED`

receipt field와 decoded field가 중복되면 exact match해야 한다. stochastic descriptor인데 seed가 없거나 sourceSnapshotId, assumptions, target, asOf, schema version 중 descriptor 필수 항목이 없으면 `REJECTED_INCOMPLETE_SIMULATION_SEMANTICS`다. descriptor가 없거나 stale이면 byte는 `VERIFIED_ARTIFACT_UNINTERPRETED`로 catalog하되 execution result나 graph evidence로 승격하지 않는다.

서명되지 않은 임의 JSON이나 단순 result path는 admission receipt로 승격하지 않는다. 검증 실패는 `REJECTED_INVALID_ADMISSION_RECEIPT`, 공식 receipt 없이 별도 등록한 실험 결과는 `UNREGISTERED_PREVIEW`다. 등록된 simulation result root에서 도달 가능한 receipt tree의 descriptor와 decode coverage는 100%여야 G2를 통과한다. Universe는 admission database와 artifact를 read-only로 열며 simulator의 registry를 수정하지 않는다.

## 7. Runtime SSOT와 저장 경계

### 7.1 기본

- live source를 runtime에서 discover한다.
- snapshot은 revision과 locator의 논리 manifest다.
- catalog query는 in-memory DuckDB 또는 process-local cache로 시작한다.
- process cache는 삭제해도 원천에서 재생성 가능해야 한다.
- repo 또는 HF에 commit한 performance manifest, prebuilt graph, embedding, tile은 기본값이 아니다.

### 7.2 Universe control-plane SSOT

다음은 원천 copy나 성능 accelerator가 아니라 Universe가 소유해야 하는 감사·결정 상태다. runtime bake 금지와 구분한다.

- source snapshot root manifest
- identity merge/split decision
- concept mapping decision
- relation taxonomy version
- capability schema descriptor
- simulator artifact schema descriptor와 decode decision
- license review
- execution receipt와 명시 저장된 execution output
- operator approval
- invalidation and tombstone ledger

Attempts fixture authority:

```text
tests/_attempts/dartlabUniverse/controlPlane/schemas/
tests/_attempts/dartlabUniverse/controlPlane/fixtures/
```

실제 runtime candidate:

```text
DARTLAB_UNIVERSE_HOME/
  control.sqlite
  objects/sha256/
  locks/
```

기본 `DARTLAB_UNIVERSE_HOME`은 user local application data 아래의 전용 경로이며 repo `data/`와 분리한다. control.sqlite는 append-only record와 supersession을, object store는 explicit execution output이나 dirty LOCAL capture처럼 replay에 필요한 immutable bytes만 보관한다. bulk HF source와 precomputed full graph를 복사하지 않는다.

```text
ControlRecord
  recordId
  recordType
  schemaVersion
  payloadDigest
  evidenceRefs[]
  proposedBy
  approvedBy?
  approvedAt?
  supersedesRecordId?
  status            PROPOSED | APPROVED | REJECTED | SUPERSEDED | TOMBSTONED
  createdAt
```

owner는 Universe control-plane이다. approved record는 in-place update하지 않고 새 record가 supersede한다. rollback은 이전 approved record ID를 active pointer로 되돌리고 invalidation을 남긴다. 이 state는 제품 재현성에 필수라 Bake Decision 대상이 아니지만 public data source로 승격할 수 없다.

### 7.3 Bake Decision

다음 네 가지가 모두 있어야 파생 artifact를 논의할 수 있다.

1. runtime-only 구현의 실제 측정값
2. 실패한 SLO와 원인 profile
3. runtime 최적화 대안과 비용
4. 운영자 명시 승인

승인 후에도 artifact는 원천이 아니라 `DERIVED_ACCELERATOR`다. source revisions, compiler version, schema version, input digest, output digest, expiry, rollback을 가진다.

## 8. 공개 프론트와 로컬 앱 경계

### 8.1 현재 단계

UI 변경은 0개다. `ui/packages`, `landing`, public route를 수정하지 않는다. CLI와 test runner로 데이터 엔진을 검증한다.

### 8.2 나중에 로컬 연결이 승인된 경우

```text
Universe UI surface
  -> contracts port
  -> local runtime source
  -> adapters/local/api/localApi.ts
  -> authenticated local Universe service
  -> UniverseKernel
```

모든 `/api` 호출은 기존 local API gate를 지난다. source component가 raw `fetch`, 직접 URL 합성, 자체 cache Map을 만들지 않는다. long job은 jobId, progress, cancel, retry, receipt stream을 쓴다.

### 8.3 나중에 public read-only 연결이 승인된 경우

public scene/object/search payload도 `data/fetch.request()`와 `data/origins` registry를 경유한다. HF URL을 surface에서 조합하지 않는다. public browser에는 private locator, token, Python engine execution이 없다.

### 8.4 공개 RAG

static landing만으로 engine call과 secure RAG를 수행하지 않는다. 공개 RAG가 승인되면 인증, quota, sandbox를 가진 Universe Query/Compute Service를 별도 설계한다. UI는 제출과 표시만 담당한다.

## 9. Catalog와 graph baseline

외부 graph DB부터 도입하지 않는다.

- canonical object, statement, edge table: Arrow schema
- runtime local query baseline: DuckDB
- Python transformation: Polars와 Arrow
- contract validation: Pydantic 또는 JSON Schema 2020-12
- digest: canonical JSON과 SHA-256
- large source read: DuckDB HTTPFS, parquet projection, row group pruning

Neo4j, Qdrant, pgvector, Elasticsearch는 benchmark 결과가 baseline을 이길 때만 ADR 후보다. 기술 이름을 제품 아키텍처로 선결하지 않는다.

## 10. Snapshot과 delta

`UniverseSnapshot`은 원본 사본이 아니다. 다음 root refs의 결합 hash다.

```text
HF repo revisions
blog git revision and dirty capture refs
media catalog digest
capability catalog digest
identity ledger version
contract schema version
visibility scope
```

delta는 file oid 추가·변경·삭제, git blob 변경, capability source hash 변경, identity ledger 변경을 비교한다. 삭제된 logical object는 tombstone으로 남겨 과거 snapshot을 재현한다.

원격 HEAD가 census 중 바뀌어도 현재 run은 pinned revision으로 끝낸다. 새 HEAD는 다음 snapshot 후보가 된다.

clean committed blog는 git commit과 blob으로 재현한다. dirty worktree는 digest만으로 재현할 수 없으므로 다음 중 하나다.

- bytes를 local control-plane CAS에 저장하고 replayability `LOCAL_CAPTURED` snapshot으로 분류
- capture가 꺼져 있으면 replayability `NONREPLAYABLE`로 분류하고 `VERIFIED` snapshot과 rollback 대상에서 제외

dirty capture는 PUBLIC snapshot으로 승격할 수 없다.

## 11. 공용 개념 승격 정책

Universe 내부 개념을 core나 기존 package로 옮기는 것은 자동 정리가 아니다. 다음을 모두 만족해야 별도 제안할 수 있다.

- Universe 밖 실제 consumer가 2개 이상
- source-specific field가 없는 일반 계약
- 2개 snapshot 이상에서 schema 안정
- unit, property, replay test 통과
- 기존 package owner와 architecture 승인
- 이동 전후 import graph와 rollback 증명

그 전에는 모든 개념을 Universe가 소유한다. 기존 것을 먼저 일반화하거나 작은 개념을 미리 모으지 않는다.

## 12. 아키텍처 인수 기준

- attempts 단계에서 기존 파일 수정 0
- 기존 package에서 Universe import 0
- raw network call이 source adapter 밖에 0
- UI 연결 시 data workbench 우회 0
- simulator internal helper 직접 호출 0
- source payload canonical copy 0
- runtime 불가 실측과 승인 없는 bake 0
- invented public API와 axis 0
- private locator public serialization 0
- package 승격 전 architecture and Skill OS 승인
