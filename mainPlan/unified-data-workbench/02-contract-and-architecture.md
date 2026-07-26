# 02. 계약과 아키텍처

분산·원격·비동기 실행면은 [07-datahub-distributed-runtime.md](07-datahub-distributed-runtime.md)를 정본으로 한다.

## 1. 공개 facade

```python
dartlab.dataHub("catalog", query=CatalogQuery(...))
dartlab.dataHub("query", assets=(...), query=DataQuery(...))
```

no-arg 호출은 두 axis와 사용 예를 담은 guide DataFrame을 반환한다. 알 수 없는 axis는 fail-fast한다. accessor chain과 detail helper를 공개하지 않는다.

## 2. asset identity

```text
assetId: quant.quality
assetVersionId: descriptor, schema, owner capability revision digest
snapshotId: query 당시 source revision set과 execution plan digest
measureId: scan.ratio 안의 roe처럼 asset 내부 선택 단위
```

assetId는 안정 논리 ID다. schema나 구현 변경을 ID rename으로 숨기지 않고 version ID로 표현한다.

## 3. descriptor

각 owner는 metadata-only `dataProduct` provider를 소유한다. dataHub는 top-level package를 열거하고 provider가 선언한 descriptor만 실행 후보로 받는다.

필수 필드:

```text
owner
layer
assetId
kind
executorRef 또는 resourceRef
inputSchema
nativeOutputSchema
temporalSupport
visibility
licenseRef
costClass
```

새 axis는 owner registry에 등록되면 provider가 자동 projection한다. 새 engine은 자기 package에 provider 하나를 선언한다. dataHub 중앙 파일에 engine 이름을 추가하지 않는다. descriptor가 없는 새 package도 catalog에서 `UNCLASSIFIED_OWNER`로 나타나 조용히 누락되지 않는다.

catalog discovery는 네트워크나 값 실행을 하지 않는다. metadata import에 side effect가 있으면 provider가 실패다.

## 4. query 계약

```python
@dataclass(frozen=True)
class DataQuery:
    subjects: tuple[str, ...]
    measures: tuple[str, ...]
    universe: UniverseSelection | None
    projection: Projection
    time: TimeContext | None
    filters: tuple[Filter, ...]
    budget: QueryBudget
    completeness: CompletenessPolicy
    lineage: LineagePolicy
    materialization: MaterializationDirective
```

`subjects`와 `universe`는 동시에 지정하지 않는다. `subjects`는 명시 entity의 eager 실행이고, `UniverseSelection(markets=("US",), membership="listed")`는 owner가 지원할 때 현재 상장 universe를 작업대가 해소하는 계약이다. historical `asOf`, `allKnown`, `explicit` 지원 여부는 owner별로 실행 전에 검증한다.

Projection은 sealed union이다.

```text
NativeProjection
RecordsProjection
FactorProjection
GraphProjection
NarrativeProjection
ResourceProjection
```

문서나 graph에 FactorProjection을 요청하면 실행 전에 `PROJECTION_INCOMPATIBLE`로 거부한다. 여러 native asset은 하나의 flat table로 합치지 않고 asset별 partition으로 반환한다.

## 5. canonical record 계층

### Resource

원문 payload를 복제하지 않고 revision-fixed locator, media type, schema fingerprint, visibility, license를 표현한다.

### Statement

subject, predicate, object/value, valid time, known time, epistemic class, evidence를 가진다. narrative와 graph는 이 계층을 사용할 수 있다.

### Observation

factor-compatible scalar 또는 text observation이다.

```text
assetId
measureId
entityId
eventAt
availableAt
knownAt
period
value
valueText
unit
currency
frequency
revisionId
sourceRef
evidenceRefs
derivationRef
status
```

FactorProjection은 Observation만 entity, time, measure long schema로 투영한다.

## 6. PIT

시간은 최소한 다음을 구분한다.

- `eventAt`: 경제적 사건 또는 측정 시점
- `availableAt`: source가 외부에 공개된 시점
- `knownAt`: query가 허용하는 지식 절단점
- `validAt`: statement가 유효한 시점
- `revisionId`: 정정과 재발행 구분

검증식은 `eventAt <= availableAt <= knownAt`이다. owner executor가 knownAt을 실제로 받을 수 없으면 data가 결과 label만 바꾸지 않는다. historical query를 거부하고 최신 query만 허용한다.

## 7. execution과 budget

query plan은 catalog만으로 작성한다. 값 실행은 admission 뒤 수행한다.

```text
maxRows
maxBytes
timeoutMs
maxAssets
maxSubjects
maxConcurrency
continuation
```

DataFrame은 Arrow IPC 또는 Polars partition으로 전달하고, 큰 결과는 batch와 continuation으로 나눈다. 전체 원천의 eager concat은 금지한다.

### 7.1 DART와 EDGAR 계산 feature runtime paging

`analysis.dartFinancialFeatures`와 `analysis.edgarFinancialFeatures`는 `FactorProjection`, 각 시장의 현재 `listed` universe, 부분 성공 정책 조합에서 owner 계산을 continuation page로 실행한다. 호출자는 종목별 반복문을 만들지 않고 한 `dataHub("query", ...)`에 KR과 US universe를 함께 등록할 수 있다. 명시한 `subjects`는 이 paging 경로로 바꾸지 않고 기존 eager `subjectFanout`으로 실행한다.

owner lane 한 page는 종목 시도 64개를 넘지 않으며 row, byte, time 예산이 더 작은 경계를 만들 수 있다. 종목별 계산 실패는 machine-readable gap으로 남고 cursor는 실패 종목을 지나 다음 종목으로 전진한다. `requireComplete`와 historical universe는 owner 호출 전에 거부한다.

continuation private state는 원 query, contract, 외부 Arrow schema, source manifest, 상장 membership, entity와 source ID mapping, DART 결산월 같은 entity parameter를 digest로 고정한다. 미완료 token을 재개할 때 source, universe, 요청 measure, owner code가 달라지면 실패한다. commit된 page replay는 source와 owner를 다시 접촉하지 않는다. token의 임시 보존 기한은 24시간이다.

EDGAR는 요청 measure를 owner까지 전달한다. revenue 또는 operating margin만 요청하면 stock state를 요구하지 않는 strict flow compiler를 쓰고, measure를 비우거나 stock measure가 하나라도 있으면 기존 full-state compiler를 유지한다.

### 7.2 mixed outer continuation

resource paging, 계산 owner paging, 일반 eager asset을 한 query에 섞으면 각 lower owner token을 외부에 노출하지 않고 작업대가 outer continuation 하나를 만든다. lane별 Arrow schema와 request order를 보존하며 row, byte, time, concurrency budget을 배분한다.

일반 eager callable과 engine axis는 fresh child process에서 실행하고 결과를 content seal로 고정한다. 이후 page는 owner를 다시 실행하지 않고 seal locator만 소비한다. child는 strict offline, Python write guard, 알려진 Polars, PyArrow, Pandas, NumPy writer 차단, process cleanup과 zero-live 검증을 적용한다. bundle 상한은 192 KiB다. 이 경계는 설치된 trusted owner의 사고성 side effect를 줄이는 실행 격리이며 임의 native syscall을 막는 적대적 OS sandbox는 아니다.

### 7.3 immutable materialization

materialization은 새 public axis가 아니라 `DataQuery.materialization` 정책이다.

```text
runtime: 저장 없이 기존 runtime continuation 실행
reuse: 같은 logical query의 최신 READY generation 우선, 없으면 cold build
refresh: 현재 source와 contract를 계획해 exact generation build 또는 동일 READY 재사용
offline: receipt가 가리키는 exact READY generation만 재생
```

generation identity는 asset, source, query, universe, contract, schema digest 여섯 개를 모두 결박한다. 한 builder lease와 epoch만 page를 추가할 수 있고 BUILDING은 reader에게 보이지 않는다. Arrow page와 terminal manifest를 CAS에 쓴 뒤 SQLite ledger의 READY 전이를 publication point로 사용한다. SQLite에는 digest, 상태, 수치, lease만 저장하고 query 원문, owner identity, continuation token, Arrow payload는 넣지 않는다.

receipt는 generation key, terminal root, 여섯 pin만 가진다. 같은 `DARTLAB_HOME`을 공유하는 다른 process는 receipt만으로 catalog, owner, source 호출 없이 page를 재생한다. public first page와 continuation page는 reader lease 하나에서 manifest와 목표 page를 함께 검증한다. page payload CAS read는 public page당 하나다.

cold build는 기존 composite chain을 terminal까지 동기적으로 소비하며 전체 6시간과 page별 timeout 상한을 함께 적용한다. warm replay는 한 page만 읽는다. reader lease가 살아 있는 READY generation은 GC가 전환하지 못하며 maintenance는 단계별 caller budget을 갖는다.

## 8. DataResult

```python
@dataclass(frozen=True)
class DataResult:
    status: str
    partitions: tuple[DataPartition, ...]
    assets: tuple[AssetRef, ...]
    schema: ResultSchema
    snapshotId: str
    dataSnapshotId: str | None
    contractHash: str
    coverage: Coverage
    gaps: tuple[DataGap, ...]
    lineageRefs: tuple[str, ...]
    executionReceipts: tuple[str, ...]
    continuation: str | None
    universeSnapshotId: str | None
    universeCoverage: tuple[UniverseCoverage, ...]
    materializationReceipt: Mapping[str, Any] | None
```

systemic outage, policy denial, invalid query는 result-level failure다. 개별 subject 결손만 partition gap이다. owner paging의 `universeCoverage`는 요청, 성공, 실패, cursor와 missing sample을 누적해 최종 page까지 보존한다.

## 9. 의존 방향

dataHub package 구조:

```text
dataHub/
  __init__.py
  entry.py
  contracts.py
  catalog.py
  discovery.py
  planner.py
  execution.py
  projections.py
  lineage.py
  materialization/
  continuation/
  controlPlane/
  remote/
  transport/
  workerPlane/
```

dataHub가 허용하는 import는 core, gather, providers, scan, frame, synth, reference, L2 owner뿐이다. simulate, story, Universe, AI, server, UI를 import하지 않는다. server는 반대로 dataHub의 versioned router를 호스팅한다.
