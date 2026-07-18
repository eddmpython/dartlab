# 06. 공간 projection과 진짜 3D 계약

## 1. 3D의 지위

3D는 Universe의 원본이 아니다. 같은 object, statement, relation, evidence graph를 사람이 전체적으로 탐색할 수 있게 x, y, z 공간으로 투영한 presentation layer다.

공간에 가깝다는 이유로 지식 관계를 만들 수 없고, 좌표가 바뀌어도 지식 ID는 바뀌지 않는다. 3D를 끄더라도 검색, 관계, 근거, 원문 접근은 동일하게 가능해야 한다.

## 2. 3D 착수 차단선

다음이 모두 통과하기 전 renderer implementation은 0줄이다.

- G0 full census
- G1 identity, temporal, provenance
- G2 capability execution and replay
- G3 query
- U4 `RetrievalEvidencePack`의 G4E 검증
- runtime-only projection benchmark 계획 승인

full generative RAG의 G4R 품질 평가는 내부 3D 뒤 U7에서 수행한다. 3D 착수 전에 필요한 것은 모델 답변이 아니라 query와 RetrievalEvidencePack의 G4E 구조·근거 검증이다.

## 3. 진짜 3D 정의

다음을 모두 만족해야 3D다.

- 모든 renderable object가 실제 `x`, `y`, `z`를 가짐
- perspective camera가 6DoF position/orientation을 가짐
- depth buffer와 occlusion이 동작
- camera orbit, pan, dolly, fly가 깊이를 실제로 바꿈
- GPU picking이 ray 또는 ID buffer로 3차원 object를 선택
- near/far plane과 frustum culling이 있음
- z축을 0으로 고정한 node 비율이 1% 미만, 예외는 명시된 plane overlay만
- 2D screenshot을 회전시키거나 CSS perspective를 붙인 것이 아님

2D force graph, Canvas 점구름, 산업 bubble, 모든 node의 z=0, 카메라가 zoom만 하는 화면은 실패다.

## 4. Spatial Projection 입력

```text
ProjectionRequest
  snapshotId
  projectionVersion
  objectScope
  relationScope
  timeContext
  activeLens
  stabilityBaseProjectionId?
  budget
  seed
```

`activeLens`는 finance, filing, industry, timeline 같은 강조 조건이지 별도 우주를 만들지 않는다. source DART/EDGAR도 filter 또는 style channel이지 top-level universe partition이 아니다.

### 4.1 ProjectionState

안정 좌표는 이전 projection 상태 없이 증명할 수 없다. `ProjectionState`는 지식 원천이 아닌 재생성 가능한 파생 상태다.

```text
ProjectionState
  projectionStateId
  baseProjectionStateId?
  snapshotId
  projectionVersion
  compilerVersion
  schemaVersion
  inputGraphDigest
  visibilityScopeDigest
  coordinateSystemVersion
  quantizationVersion
  logicalCoordinateMapDigest
  communityLineageDigest
  outputDigest
  createdAt
  persistenceMode       EPHEMERAL | APPROVED_DERIVED
  rollbackProjectionStateId?
```

U5는 두 snapshot fixture를 한 process에서 계산해 알고리즘과 상태 전이를 검증하는 gate다. 제품 G5는 다음 중 하나를 만족해야 한다.

1. 이전 snapshot과 projection을 원천에서 runtime 재생해 `ProjectionState`를 SLO 안에 복원
2. runtime SLO 실패 실측 뒤 Bake Decision과 운영자 승인을 받은 `APPROVED_DERIVED` ProjectionState를 읽음

승인 없는 persistent coordinate map과 tile은 금지한다. G5가 persistence를 암묵적으로 가정하지 않도록 U5와 U6 사이에 Projection State Decision gate를 둔다.

## 5. Scene 계약

### 5.1 SceneManifest

```text
SceneManifest
  sceneId
  snapshotId
  projectionVersion
  projectionDigest
  visibilityScopeDigest
  generation
  coordinateSystem
  rootTileId
  bounds
  objectCount
  relationCount
  tileCount
  lodPolicyVersion
  payloadSchemaVersion
  styleSchemaVersion
  createdFrom
```

SceneManifest가 원천 payload를 포함하지 않는다. runtime 계산 결과가 기본이며, 영속 tile은 Bake Decision 승인을 받기 전 만들지 않는다.

### 5.2 SceneNode

```text
nodeId
targetKind          OBJECT | PROXY
targetId
position: [x, y, z]
radius
importance
kind
epistemicClass
verificationState
clusterId
lodLevel
labelPriority
pickId
styleToken
detailRef
```

`targetKind=OBJECT`일 때 targetId는 Universe objectId다. L0부터 L2의 community는 canonical knowledge object가 아니라 projection-only proxy다.

### 5.3 SceneProxy

```text
proxyId
proxyVersionId
communityLogicalId
communityVersionId
memberDigest
memberCount
representativeObjectIds[]
representativeRuleVersion
primaryHomeClusterId
secondaryMemberships[]
drillTargetTileId
kindHistogram
sourceHistogram
epistemicHistogram
verificationHistogram
periodRange
statementCount
statementRefSetDigest
evidenceCount
evidenceRefSetDigest
relationTypeDirectionHistogram
```

모든 object는 primary home cluster를 정확히 하나 가진다. 다중 semantic membership은 secondaryMemberships에만 두며 count conservation에서는 primary home만 센다.

### 5.4 SceneEdge

```text
edgeId
relationType
fromNodeId
toNodeId
weight
epistemicClass
verificationState
evidenceCount
lodLevel
aggregateCount
styleToken
detailRef
```

aggregate edge의 endpoint는 object node 또는 SceneProxy다. `relationTypeDirectionHistogram`으로 relation type과 direction별 count를 함께 보존하며 aggregate count를 단일 법적·재무 관계처럼 설명하지 않는다.

### 5.5 SceneTile Envelope

```text
sceneId
snapshotId
projectionVersion
projectionDigest
lodPolicyVersion
payloadSchemaVersion
visibilityScopeDigest
generation
tileId
parentTileId?
childTileIds[]
bounds3d
coordinateOriginQ
encoding
screenSpaceError
lodLevel
nodeCount
edgeCount
clusterSummaries[]
contentRef
contentDigest
byteSize
nextCursor?
```

scene, snapshot, projection, visibility, generation이 현재 renderer state와 다르면 tile을 stage하기 전에 거절한다. contentDigest가 같아도 visibilityScopeDigest가 다르면 재사용하지 않는다.

## 6. 의미 LOD

거리만 줄이는 LOD가 아니라 의미를 보존하는 LOD다.

| level | 보이는 것 | payload |
|---|---|---|
| L0 | 전체 Universe root | 총수, source·kind·상태 분포 |
| L1 | 대형 community | community proxy, 주요 object, aggregate relations |
| L2 | cluster tile | cluster member summary와 tile-pair edge |
| L3 | 개별 object | object node와 선택 relation |
| L4 | document, section, table | 근거 경로와 세부 locator |
| L5 | row와 cell | 요청 시 지연 해소되는 virtual object |

각 proxy가 보존할 항목:

- 포함 object 수
- object kind 분포
- source 분포
- epistemic class 분포
- verification state 분포
- 기간 범위
- 대표 object와 선정 근거
- statement와 evidence 수
- aggregate relation type과 count

### 6.1 Meaning Preservation

LOD 전환은 다음 보존식을 모두 만족해야 한다.

```text
parent.memberCount = count(unique primary-home members in children)
parent.kindHistogram = sum(children.kindHistogram)
parent.sourceHistogram = sum(children.sourceHistogram)
parent.epistemicHistogram = sum(children.epistemicHistogram)
parent.verificationHistogram = sum(children.verificationHistogram)
parent.periodRange = [min(child.periodRange.start), max(child.periodRange.end)]
parent.statementCount = count(union(child statement refs))
parent.statementRefSetDigest = hash(sorted union(child statement refs))
parent.evidenceCount = count(union(child evidence refs))
parent.evidenceRefSetDigest = hash(sorted union(child evidence refs))
parent.relationTypeDirectionHistogram = count(canonical internal and boundary edge IDs grouped by relation type and direction)
```

`meaningPreservation = passedConservationAssertions / totalConservationAssertions`로 계산하고 G5는 100%를 요구한다. source, period, statement, evidence와 relation direction assertion도 분모에 포함한다. secondary semantic membership은 memberCount 합계에 중복 산입하지 않는다. 같은 relation이 internal과 boundary 집합에 이중 산입되면 실패한다. 선택 object와 evidence path는 proxy 전환 전후 100% addressable해야 한다.

## 7. Progressive streaming

```text
camera and query state
  -> tile priority queue
  -> parent proxy retained
  -> child tile request
  -> worker decode and validation
  -> GPU buffer upload
  -> atomic parent-child transition
```

규칙:

- child가 준비되기 전 parent를 지우지 않는다.
- 선택 object는 LOD와 관계없이 reveal한다.
- 모든 edge를 동시에 load하거나 render하지 않는다.
- edge는 tile pair와 relation type으로 aggregate한다.
- 선택 경로, search result, evidence path만 상세 edge로 승격한다.
- label은 viewport budget과 priority를 사용한다.
- 검색 결과는 현재 LOD를 건너뛰어 target tile을 직접 연다.
- browser에 전체 원문, 전체 node, 전체 relation을 한 번에 넣지 않는다.

OGC 3D Tiles의 HLOD, bounding volume, screen-space error, progressive refinement 개념을 참고하되 지리 좌표 형식을 그대로 채택하지 않는다. [OGC 3D Tiles 1.1](https://docs.ogc.org/cs/22-025r4/22-025r4.html)

## 8. 안정 좌표

UMAP이나 ForceAtlas를 매 snapshot 전체에 다시 돌려 제품 좌표로 쓰지 않는다. mental map을 보존하는 hybrid projection을 쓴다.

### 8.1 목표 알고리즘

1. 검증된 typed relation graph 구성
2. canonical object ID 순서로 graph 정렬
3. Leiden 기반 계층 community version 후보 계산
4. 이전 community와 신규 후보를 overlap score로 matching
5. retained community는 기존 communityLogicalId를 유지
6. member set digest는 communityVersionId에만 포함
7. top-level community를 deterministic 3D anchor에 배치
8. community 내부만 seeded, single-thread 3D UMAP 또는 bounded force refinement
9. 이전 object 좌표를 stability constraint로 pin
10. 신규 object는 이웃 weighted barycenter와 ID-derived 3D jitter에 배치
11. 변경된 community만 재계산
12. projection minor에서는 기존 object 이동 budget 강제
13. 전체 재배치는 projection major에서만 허용하고 transition map 보존

### 8.2 Community lineage

최초 snapshot의 communityLogicalId는 projection namespace, level, initial member digest로 만든다. 다음 snapshot부터 member digest로 logical ID를 다시 만들지 않는다.

```text
overlapScore(old,new) = |old members intersect new members| / max(|old|, |new|)
```

- score 0.80 이상인 maximum-weight one-to-one match는 `RETAINED`
- 여러 new 후보가 한 old에 0.50 이상이면 가장 높은 후보가 ID를 유지하고 나머지는 `SPLIT_FROM`
- 여러 old가 한 new에 0.50 이상이면 최대 overlap old의 ID를 유지하고 `MERGED_FROM` refs를 기록
- match 없는 new는 `NEW`
- successor 없는 old는 `RETIRED`
- 동점은 shared importance sum, 그다음 lexical community ID 순서로 결정

모든 version은 `communityVersionId = hash(communityLogicalId, sortedMemberDigest, projectionVersion)`를 가진다. lineage ledger가 없거나 tie-break가 비결정적이면 minor projection으로 승격할 수 없다.

Leiden은 연결된 community를 목표로 하는 baseline 후보다. [Leiden 논문](https://www.nature.com/articles/s41598-019-41695-z)

UMAP과 HUMAP은 내부 배치와 계층 mental-map benchmark 후보다. [UMAP 논문](https://arxiv.org/abs/1802.03426), [HUMAP 논문](https://arxiv.org/abs/2106.07718)

ForceAtlas2는 작은 community refinement benchmark만 허용한다. 전체 Universe 기본 좌표로 쓰지 않는다. [ForceAtlas2 논문](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0098679)

### 8.3 좌표계와 결정론

Canonical coordinate contract:

- right-handed coordinate system
- Y-up
- root cube half extent `1,000,000 Q`
- canonical position은 signed int32 `[xQ, yQ, zQ]`
- `1 Q = root diameter / 2,000,000`
- node와 community input은 logical ID 오름차순 정렬
- layout은 fixed dependency version, fixed seed, single-thread CPU baseline
- float64 layout 결과를 round-half-even으로 Q 단위 quantization
- GPU에는 `float32(positionQ - tileOriginQ)`와 scale을 보내 floating origin 사용
- anchor minimum separation은 두 radius 합의 1.05배
- collision은 ID-derived 3D jitter를 최대 8회 적용
- 8회 뒤에도 collision 또는 root bounds overflow면 `PROJECTION_REJECTED`

같은 OS, CPU architecture, dependency fingerprint에서는 pre-quantization과 serialized Q byte equality를 요구한다. 교차 환경에서는 pre-quantization float가 아니라 quantized Q equality 100%를 요구한다. 이 gate를 통과하지 못한 UMAP/force 구현은 제품 좌표 후보에서 탈락한다.

### 8.4 안정성 metric

```text
coordinateDeterminism = identical coordinates / unchanged objects
normalizedDisplacement = distance(old,new) / oldClusterRadius
clusterContinuity = retained co-membership / prior co-membership
```

G5 기준:

- 동일 snapshot과 projection version의 좌표 byte 안정성 100%
- 1% 이하 증분 data 후 기존 node normalized displacement p95 2% 이하
- cluster continuity 98% 이상
- query와 camera 변화로 base coordinate 변경 0
- selected object 유실 0

## 9. 관계와 공간의 분리

relation은 지식 graph에서 오고 position은 projection에서 온다.

- relation 없는 공간 이웃을 edge로 그리지 않는다.
- inferred similarity edge는 `INFERRED`와 confidence를 표시한다.
- aggregate edge를 개별 법적·재무 관계로 설명하지 않는다.
- source별 색은 가능하지만 DART와 EDGAR를 서로 떨어진 별도 우주로 고정하지 않는다.
- epistemic class는 색 외에도 glyph, line pattern, text label로 구분한다.

## 10. Picking과 drill-down

```text
Universe root
  -> community
  -> cluster
  -> organization or concept
  -> filing or blog post
  -> section
  -> table
  -> row
  -> cell
  -> source original
```

각 단계는 `objectId`, `snapshotId`, `detailRef`, `evidenceRef`를 유지한다. 3D pick 결과가 UI local index만 반환하면 실패다.

GPU pick ID는 frame-local integer일 수 있으나 stable objectId와 mapping한다. picking collision 0, stale pick mapping 0이 gate다.

## 11. Scene source, scheduler, renderer ports

지식·scene 계약이 특정 library type을 import하지 않도록 세 port를 분리한다.

```ts
type ApplyResult =
  | { status: 'accepted'; generation: number }
  | { status: 'rejected'; reason: 'stale' | 'scope' | 'digest' | 'schema' }
  | { status: 'resource-pressure'; requiredBytes: number; availableBytes: number };

type DeepReadonly<T> = T extends (...args: never[]) => unknown
  ? T
  : T extends ReadonlyArray<infer U>
    ? ReadonlyArray<DeepReadonly<U>>
    : T extends object
      ? { readonly [K in keyof T]: DeepReadonly<T[K]> }
      : T;

interface TileRequest {
  sceneId: string;
  snapshotId: string;
  projectionVersion: string;
  projectionDigest: string;
  lodPolicyVersion: string;
  payloadSchemaVersion: string;
  visibilityScopeDigest: string;
  generation: number;
  tileId: string;
  parentTileId?: string;
  priority: number;
  expectedContentDigest?: string;
}

interface DecodedSceneTile {
  readonly envelope: DeepReadonly<SceneTileEnvelope>;
  readonly decodedContentDigest: string;
  readonly nodeBuffer: ArrayBuffer;
  readonly nodeBufferDigest: string;
  readonly edgeBuffer: ArrayBuffer;
  readonly edgeBufferDigest: string;
  readonly pickMap: ReadonlyMap<number, { readonly targetKind: 'OBJECT' | 'PROXY'; readonly targetId: string }>;
  readonly pickMapDigest: string;
  readonly residentPayloadDigest: string;
  readonly cpuBytes: number;
  readonly estimatedGpuBytes: number;
}

interface ResidentTileHandle {
  readonly residentId: string;
  readonly sceneId: string;
  readonly generation: number;
  readonly tileId: string;
  readonly envelopeDigest: string;
  readonly nodeBufferDigest: string;
  readonly edgeBufferDigest: string;
  readonly pickMapDigest: string;
  readonly residentPayloadDigest: string;
  readonly cpuBytes: number;
  readonly estimatedGpuBytes: number;
}

type ResidentAdmissionResult =
  | { status: 'accepted'; generation: number; handle: ResidentTileHandle }
  | { status: 'rejected'; reason: 'stale' | 'scope' | 'digest' | 'schema' }
  | { status: 'resource-pressure'; requiredBytes: number; availableBytes: number };

type ResidentMaterializationResult =
  | { status: 'accepted'; generation: number; tile: DecodedSceneTile }
  | { status: 'rejected'; reason: 'stale' | 'scope' | 'digest' | 'schema' };

type ResidentLifecycleState =
  | 'CPU_ADMITTED'
  | 'GPU_READY'
  | 'VISIBLE'
  | 'RECOVERING'
  | 'QUARANTINED'
  | 'EVICTED';

interface TransitionCoverageProof {
  readonly coverageProofVersion: string;
  readonly parentBoundsDigest: string;
  readonly childBoundsUnionDigest: string;
  readonly parentSemanticSetDigest: string;
  readonly childSemanticSetDigest: string;
  readonly coveredChildTileIds: ReadonlyArray<string>;
  readonly boundsCoverageRatio: 1;
  readonly semanticCoverageRatio: 1;
  readonly proofDigest: string;
}

interface TileTransition {
  readonly transitionId: string;
  readonly sceneId: string;
  readonly generation: number;
  readonly parentTileId: string;
  readonly childTileIds: ReadonlyArray<string>;
  readonly requiredReadyChildIds: ReadonlyArray<string>;
  readonly coverageProof?: TransitionCoverageProof;
}

interface PreparedTileTransition {
  readonly transition: DeepReadonly<TileTransition>;
  readonly pinToken: string;
  readonly preparationDigest: string;
}

type TransitionPreparationResult =
  | { status: 'accepted'; generation: number; prepared: PreparedTileTransition }
  | { status: 'rejected'; reason: 'stale' | 'scope' | 'digest' | 'schema' | 'coverage' }
  | { status: 'resource-pressure'; requiredBytes: number; availableBytes: number };

interface RecoveryEntry {
  readonly handle: ResidentTileHandle;
  readonly previousState: 'GPU_READY' | 'VISIBLE';
}

interface RecoveryBatch {
  readonly recoveryId: string;
  readonly sceneId: string;
  readonly generation: number;
  readonly entries: ReadonlyArray<RecoveryEntry>;
}

interface ViewportState { width: number; height: number; devicePixelRatio: number; }
interface CameraState { sceneId: string; generation: number; positionWorld: [number, number, number]; orientation: [number, number, number, number]; poseDigest: string; near: number; far: number; fovY: number; }
interface SelectionState { sceneId: string; generation: number; targetIds: string[]; }
interface PointerState { sceneId: string; generation: number; x: number; y: number; }
interface PickResult { sceneId: string; generation: number; tileId: string; targetKind: 'OBJECT' | 'PROXY'; targetId: string; }
type PickResponse = { status: 'hit'; result: PickResult } | { status: 'miss' } | { status: 'rejected'; reason: 'stale' | 'scope' };
interface RenderBudget { maxCpuBytes: number; maxGpuBytes: number; maxVisibleNodes: number; maxVisibleEdges: number; }
interface RenderResourceUsage { cpuBytes: number; gpuBytes: number; tileCount: number; nodeCount: number; edgeCount: number; }

interface SceneSourcePort {
  requestTile(request: TileRequest, signal: AbortSignal): Promise<SceneTileEnvelope>;
  retryTile(request: TileRequest, attempt: number, signal: AbortSignal): Promise<SceneTileEnvelope>;
  authorize(request: TileRequest, visibilityScopeDigest: string): Promise<boolean>;
}

interface TileSchedulerPort {
  setGeneration(generation: number): void;
  prioritize(requests: TileRequest[]): void;
  admitResident(tile: DecodedSceneTile): ResidentAdmissionResult;
  recordStageResult(handle: ResidentTileHandle, result: ApplyResult): ApplyResult;
  prepareTransition(input: TileTransition): TransitionPreparationResult;
  recordTransitionResult(input: PreparedTileTransition, result: ApplyResult): ApplyResult;
  quarantineResident(handle: ResidentTileHandle, reason: 'digest' | 'scope' | 'schema'): void;
  beginRecovery(manifest: SceneManifest): RecoveryBatch;
  recordRecoveryResult(batch: RecoveryBatch, result: ApplyResult): ApplyResult;
  cancelGeneration(generation: number): void;
  evictToBudget(maxCpuBytes: number, maxGpuBytes: number): string[];
  gpuResidentTiles(): ReadonlyArray<ResidentTileHandle>;
  materializeForUpload(handle: ResidentTileHandle): Promise<ResidentMaterializationResult>;
}

interface UniverseRendererPort {
  mount(target: HTMLElement): Promise<void>;
  beginScene(manifest: SceneManifest): Promise<ApplyResult>;
  stageTile(tile: DecodedSceneTile): Promise<ApplyResult>;
  commitTransition(input: PreparedTileTransition): Promise<ApplyResult>;
  evictTile(tileId: string, generation: number): ApplyResult;
  clearScene(sceneId: string): void;
  resize(viewport: ViewportState): void;
  setCamera(camera: CameraState): ApplyResult;
  setSelection(selection: SelectionState): ApplyResult;
  pick(pointer: PointerState): Promise<PickResponse>;
  setQuality(budget: RenderBudget): void;
  getResourceUsage(): RenderResourceUsage;
  recoverDevice(manifest: SceneManifest, residentTiles: ReadonlyArray<DecodedSceneTile>): Promise<ApplyResult>;
  dispose(): void;
}
```

SceneSourcePort가 authorization과 request/abort/retry를, TileSchedulerPort가 parent retention, child readiness quorum, generation cancel, eviction을 소유한다. renderer는 network와 retry를 모른다.

`setGeneration`은 accepted SceneManifest.generation과 같은 값만 받을 수 있다. 새 generation은 successor manifest로 `beginScene`을 통과한 뒤에만 활성화하며 scheduler와 renderer를 따로 앞서가게 하지 않는다.

`SceneManifest`가 renderer의 authoritative scene, snapshot, projectionVersion, projectionDigest, visibilityScopeDigest, generation, LOD와 payload schema를 설정한다. 검증은 다음처럼 나눈다.

- request와 envelope의 sceneId, snapshotId, projectionVersion, projectionDigest, lodPolicyVersion, visibilityScopeDigest는 manifest와 같아야 한다.
- request와 envelope끼리 payloadSchemaVersion, generation, tileId, parentTileId가 같아야 한다.
- payloadSchemaVersion은 manifest와 allowlisted decoder schema가 모두 지원해야 한다.
- generation은 accepted manifest와 scheduler current generation이 모두 같아야 한다.
- 첫 request만 `tileId == manifest.rootTileId`, `parentTileId` 없음이어야 한다.
- child request는 resident parent envelope의 `childTileIds`에 tileId가 있고 request.parentTileId와 envelope.parentTileId가 그 parent를 가리켜야 한다.
- expectedContentDigest가 있으면 envelope.contentDigest와 같아야 한다.
- decode 뒤에는 `decodedContentDigest == envelope.contentDigest`를 확인하고 node buffer, edge buffer, pick map digest와 이들을 묶은 residentPayloadDigest를 다시 계산한다.

camera, selection, pointer와 transition의 scene 또는 generation이 현재 manifest와 다르면 `stale`로 거절한다. pick은 frame-local ID가 아니라 stable targetId까지 해소된 경우에만 반환한다.

`admitResident`는 decoded input buffer와 pick map을 scheduler private resident store로 복사하거나 transferable ownership을 받아 원래 producer reference를 폐기하고 state를 `CPU_ADMITTED`로 둔다. store 내부 byte와 canonical envelope는 외부로 노출하지 않는다. 반환하는 `ResidentTileHandle`은 deep-readonly metadata와 digest만 가지며 buffer를 갖지 않고 runtime에서 freeze한다. `residentPayloadDigest = hash(envelopeDigest, nodeBufferDigest, edgeBufferDigest, pickMapDigest)`다.

초기 stage와 device recovery 모두 `materializeForUpload(handle)`을 거친다. scheduler는 private store의 envelope, node/edge buffer와 pick map digest를 그 시점에 다시 계산하고 handle과 일치할 때만 deep-cloned envelope, 새 node buffer, 새 edge buffer, 새 pick map으로 구성된 disposable tile을 반환한다. store-owned object reference는 하나도 반환하지 않는다. renderer는 canonical resident state가 아닌 이 복사본만 소유한다. envelope, buffer 또는 pick map 복사본 변경은 private resident state를 바꿀 수 없다. mismatch는 해당 resident를 격리하고 `digest` 거절을 반환하며 GPU upload 0이다.

stage와 LOD transition 순서:

```text
admitResident(decoded) -> CPU_ADMITTED
  -> materializeForUpload(handle)
  -> renderer.stageTile(copy)
  -> recordStageResult(handle, result)
       accepted          -> GPU_READY, child quorum에 포함
       resource-pressure -> CPU_ADMITTED 유지, retry 가능, quorum 변화 0
       rejected          -> QUARANTINED, quorum 변화 0
  -> prepareTransition(transition)
       coverage 100%와 required child 전부 GPU_READY를 원자적으로 검증
       accepted -> parent와 required children pin, PreparedTileTransition 발급
  -> renderer.commitTransition(prepared)
  -> recordTransitionResult(prepared, result)
       accepted -> children VISIBLE, 그때만 parent eviction 가능
       그 외     -> child pin 해제, parent 유지, blank frame 0
```

`readinessQuorum` 같은 단순 개수는 사용하지 않는다. `requiredReadyChildIds`가 `childTileIds` 전체이면 전부 GPU_READY여야 한다. subset이면 `coverageProof`가 필수이며 coverage verifier가 parent bounds와 semantic target set을 그 subset이 각각 정확히 100% 보존한다고 canonical digest와 원소 집합으로 다시 계산해야 한다. proof에 적힌 ratio 값만 신뢰하지 않는다. 빈 집합, 중복 ID, parent가 광고하지 않은 child, required 집합 밖의 covered ID, bounds 또는 semantic coverage 100% 미만은 거절한다.

`prepareTransition`은 current generation의 required child가 전부 GPU_READY이고 coverage 검증이 통과할 때 parent와 required child를 한 transaction에서 pin하고 buffer 없는 `PreparedTileTransition`을 발급한다. renderer와 `recordTransitionResult`는 이 준비 객체만 받는다. pinToken, preparationDigest, transitionId와 generation이 정확히 일치하지 않거나 duplicate, out-of-order, 이미 종료된 result면 state 변화 없이 거절한다. `evictToBudget`은 transition result가 기록되기 전 pinned parent와 pinned child, selected tile을 제거할 수 없다. accepted result에서만 child가 VISIBLE이 되고 parent eviction이 가능하다. reject, resource pressure, stale, generation cancel은 child pin을 해제하고 parent를 유지한다.

`recordStageResult`와 `recordTransitionResult`는 handle 또는 prepared transition generation과 renderer result generation이 current generation과 모두 같을 때만 state를 전이한다.

device loss가 나면 `beginRecovery`가 current `GPU_READY`와 `VISIBLE` handle을 `RECOVERING`으로 옮기고 각각의 이전 상태를 담은 immutable `RecoveryBatch`를 반환한다. coordinator는 각 handle을 recovery 직전에 materialize하고 전부 성공한 복사본만 `recoverDevice`에 전달한다. renderer는 GPU state를 전부 버리고 manifest, prepared tile copies, camera, selection 순으로 replay한다.

`recordRecoveryResult`는 한 batch를 반드시 terminal로 만든다. accepted이면 각 entry의 이전 GPU_READY 또는 VISIBLE 상태를 복원한다. resource pressure면 전부 CPU_ADMITTED로 돌려 저품질 또는 축소 batch retry를 허용한다. digest, scope, schema reject면 전부 QUARANTINED로, stale reject와 generation cancel이면 EVICTED로 옮긴다. 어느 terminal 결과 뒤에도 RECOVERING 잔존은 0이어야 한다. materialization 하나라도 실패하면 renderer 호출 없이 그 reject를 batch 전체에 기록한다. device loss 뒤에는 GPU parent proxy도 존재하지 않으므로 복구 accepted 전까지 3D가 유지된다고 주장하지 않고, 별도 semantic tree fallback과 복구 상태를 표시한다. 각 resident의 manifest scope, projection digest, generation과 resident payload digest를 다시 검사하며 새 generation은 이전 recovery와 pending transition을 취소하고 위 terminal 전이와 pin 해제를 원자적으로 끝낸다.

## 12. Renderer 후보와 판정

### 12.1 1순위 prototype

`Three.js WebGPURenderer + TSL`을 RendererPort 뒤에서 benchmark한다.

- WebGPU 우선
- WebGL2 fallback 가능성
- Svelte와 얇은 integration
- typed buffer, instancing, BatchedMesh 활용

공식 문서도 WebGPURenderer를 experimental로 설명하므로 product contract가 Three.js object model에 종속되면 안 된다. [Three.js WebGPURenderer](https://threejs.org/manual/en/webgpurenderer)

구현 원칙:

- node 하나당 `Object3D` 생성 금지
- Svelte reactive state에 node 수십만 개 저장 금지
- typed arrays와 GPU instance/storage buffer
- worker에서 tile decode, LOD selection, edge aggregation
- GPU picking
- device loss recovery
- renderer dispose 시 buffer와 listener 전량 해제

### 12.2 비교 benchmark

| 후보 | 용도 | 채택 조건 |
|---|---|---|
| PlayCanvas | WebGPU 안정성과 engine 비교 | Three baseline보다 안정성·성능 우세 |
| deck.gl | 대규모 point와 picking 기준 | graph UX 채택 아님, 수치 benchmark |
| CesiumJS | HLOD streaming 개념 | 지리 엔진 전체 채택 아님 |
| Cosmograph | 대규모 graph interaction 참고 | 2D 중심이라 최종 3D 엔진 채택 금지 |
| raw WebGPU | 최종 fallback 후보 | engine overhead가 blocker임을 실측했을 때만 |

deck.gl의 공개 성능 설명은 외부 참고값일 뿐 DartLab gate는 자체 기기에서 다시 측정한다. [deck.gl performance](https://deck.gl/docs/developer-guide/performance)

## 13. Style contract

style은 의미를 숨기지 않는다.

| 상태 | 시각 채널 |
|---|---|
| OBSERVED | solid glyph + text label on detail |
| DERIVED | outlined ring + `파생` label |
| SIMULATED | dashed orbit + `시뮬레이션` label |
| ASSERTED | quote glyph + `저자 주장` label |
| INFERRED | dotted halo + `추론` label |
| CONFLICTED | split marker + conflict count |
| MISSING/PARTIAL | hollow marker + reason label |

색만으로 상태를 전달하지 않는다.

## 14. 2D 위장 방지 review

내부 검수 체크:

- 임의로 camera를 90도 돌렸을 때 실제 depth 분포가 보이는가
- occlusion과 parallax가 동작하는가
- z coordinate 분산이 0이 아닌가
- pick ray가 앞뒤 object를 구분하는가
- fly-through로 cluster 내부에 진입 가능한가
- 2D fallback screenshot과 3D mode가 실제 interaction에서 다른가
- 3D를 꺼도 동일 object와 evidence를 찾을 수 있는가

하나라도 아니면 3D 완료로 선언하지 않는다.

## 15. G5와 G6 인수 기준

### G5 Projection

- 좌표 byte 안정성 100%
- ID와 position mapping 누락 0
- 증분 이동 p95 2% 이하
- cluster continuity 98% 이상
- community lineage 없는 minor projection 0
- meaningPreservation 100%
- base coordinate를 query가 바꾼 사례 0
- L0부터 L5까지 drill-down path 단절 0
- ProjectionState runtime replay SLO 통과 또는 승인된 APPROVED_DERIVED state 존재
- visibilityScopeDigest가 다른 ProjectionState 재사용 0
- 승인 없는 persistent projection artifact 0

### G6 Renderer

- x, y, z, depth, occlusion, camera, picking 계약 전부 통과
- z=0 강제 node 1% 미만
- parent-child LOD blank frame 0
- selected object loss 0
- WebGL2 fallback에서 기능 손실 0, 밀도 저하만 허용
- device loss 후 state 복구
- stale generation, snapshot, visibility tile 수용 0
- admitResident 뒤 resident payload mutation 또는 recovery digest mismatch 수용 0
- resource pressure를 success로 처리한 사례 0
- 30분 탐색 memory 증가율 5% 이하
- public route와 button 0
