# 02. 계약과 아키텍처

## 1. 공개 facade

```python
dartlab.data("catalog", query=CatalogQuery(...))
dartlab.data("query", assets=(...), query=DataQuery(...))
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

각 owner는 metadata-only `dataProduct` provider를 소유한다. data는 top-level package를 열거하고 provider가 선언한 descriptor만 실행 후보로 받는다.

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

새 axis는 owner registry에 등록되면 provider가 자동 projection한다. 새 engine은 자기 package에 provider 하나를 선언한다. data 중앙 파일에 engine 이름을 추가하지 않는다. descriptor가 없는 새 package도 catalog에서 `UNCLASSIFIED_OWNER`로 나타나 조용히 누락되지 않는다.

catalog discovery는 네트워크나 값 실행을 하지 않는다. metadata import에 side effect가 있으면 provider가 실패다.

## 4. query 계약

```python
@dataclass(frozen=True)
class DataQuery:
    subjects: tuple[str, ...]
    measures: tuple[str, ...]
    projection: Projection
    time: TimeContext | None
    filters: tuple[Filter, ...]
    budget: QueryBudget
    completeness: CompletenessPolicy
    lineage: LineagePolicy
```

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

## 8. DataResult

```python
@dataclass(frozen=True)
class DataResult:
    status: str
    partitions: tuple[DataPartition, ...]
    assets: tuple[AssetRef, ...]
    schema: ResultSchema
    snapshotId: str
    contractHash: str
    coverage: Coverage
    gaps: tuple[DataGap, ...]
    lineageRefs: tuple[str, ...]
    executionReceipts: tuple[str, ...]
    continuation: str | None
```

systemic outage, policy denial, invalid query는 result-level failure다. 개별 subject 결손만 partition gap이다.

## 9. 의존 방향

data package 내부 후보:

```text
data/
  __init__.py
  entry.py
  contracts.py
  catalog.py
  discovery.py
  planner.py
  execution.py
  projections.py
  lineage.py
  result.py
```

data가 허용하는 import는 core, gather, providers, scan, frame, synth, reference, L2 owner뿐이다. simulate, story, Universe, AI, server, UI를 import하지 않는다.
