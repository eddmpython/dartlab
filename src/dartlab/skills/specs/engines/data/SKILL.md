---
id: engines.data
title: Unified Data Workbench
kind: curated
scope: builtin
status: observed
category: engines
purpose: Data Workbench는 L1, L1.5, L2의 원천, 정규 데이터, 횡단 데이터, 분석 자산을 하나의 자동 발견 카탈로그와 bounded query 계약으로 제공한다. 외부 프로세스의 범용 데이터 API, factor store projection, 시뮬레이터 입력 스냅샷에 같은 계약을 쓴다. 트리거는 '데이터 작업대', '팩터 스토어', '전종목 DART EDGAR 조회'다.
whenToUse:
  - data
  - 데이터 작업대
  - 데이터 스토어
  - 팩터 스토어
  - 자산 카탈로그
  - 데이터 lineage
  - PIT query
  - 시뮬레이터 입력
  - 여러 엔진 데이터 통합
inputs:
  - catalog filter
  - stable asset ID
  - subjects
  - measures
  - projection
  - asset별 DataRequest
  - validAt 또는 knownAt
  - query budget
  - opaque continuation token
outputs:
  - DataCatalogResult
  - DataResult
  - typed DataPartition
  - coverage와 gap
  - snapshot과 lineage
  - execution receipt
  - 구조화 DataLineage와 QualityAssertion
  - Polars와 Arrow table
  - 전종목 source shard coverage와 opaque continuation
capabilityRefs:
  - data
  - data.catalog
  - data.query
knowledgeRefs:
  - start.dartlabSkillOs
  - engines.data.foundation
  - engines.company
  - engines.gather
  - engines.scan
  - engines.analysis
sourceRefs:
  - dartlab://skills/engines.data
requiredEvidence:
  - assetId
  - assetVersionId
  - snapshotId
  - contractHash
  - coverage
  - gaps
  - lineageRefs
  - executionReceipts
  - qualityAssertions
expectedOutputs:
  - 선택한 stable asset ID와 projection
  - bounded partition 결과
  - 시점 지원 여부와 honest gap
  - 같은 snapshot에 결박된 lineage와 receipt
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: limited
    notes:
      - packaged snapshot과 브라우저에서 실행 가능한 owner asset만 query할 수 있다.
failureModes:
  - quant, credit, scan, AI 일부만 데이터 작업대 전체인 것처럼 설명함
  - factor를 별도 최상위 엔진이나 고정 저장 스키마로 만듦
  - latest 값을 과거 knownAt 라벨로 바꿈
  - catalog 조회 중 owner 값을 실행함
  - 여러 partition의 row, byte 예산을 각각 적용해 전체 예산을 초과함
  - private, nested, bulk resource payload를 무제한 로드함
  - 전종목 DART와 EDGAR를 호출자가 종목별 반복 호출함
  - continuation과 함께 원 질의 override를 전송함
  - 빈 owner 결과를 성공 partition으로 반환함
  - 공유 Company 상태를 쓰는 owner를 동시에 초기화해 경쟁 상태를 만듦
forbidden:
  - Data Workbench를 특정 분석 엔진 묶음으로 축소하지 않는다.
  - factor, graph, narrative, resource를 public axis로 늘리지 않는다. 모두 query projection이다.
  - PIT 미지원 asset을 과거 시점 성공으로 반환하지 않는다.
  - unit이 없는 값을 factor row로 가장하지 않는다.
  - gap을 0 또는 빈 성공으로 바꾸지 않는다.
  - data 계층에서 simulate, story, AI를 역참조하지 않는다.
examples:
  - L1, L1.5, L2 전체 asset catalog 조회
  - scan.ratio를 factor projection으로 외부 프로세스에서 사용
  - 여러 owner의 native 결과를 partition으로 한 번에 조회
  - 한 query에서 factor, narrative, simulation input을 서로 다른 DataRequest로 조회
  - knownAt 지원 여부를 fail-closed로 검증
  - 시뮬레이터 재무 입력을 snapshot과 receipt로 고정
  - DART와 EDGAR 전종목 원천을 한 query와 한 continuation chain으로 순회
procedure:
  - dartlab.data()로 catalog와 query 두 public axis를 확인한다.
  - dartlab.data("catalog")로 owner, layer, kind, temporalSupport, queryable을 조회한다.
  - stable assetId를 선택하고 단일 view면 DataQuery, 혼합 view면 asset별 DataRequest에 subjects, measures, projection, time을 명시한다.
  - dartlab.data("query", assetId, query=...) 또는 dartlab.data("query", query=DataQuery(requests=(...)))를 호출한다.
  - status, coverage, gaps를 먼저 검사한 뒤 partition data를 소비한다.
  - partial resource 결과는 result.continuation만 다음 query에 전달하고 원 질의를 덮어쓰지 않는다.
  - snapshotId, contractHash, lineageRefs, executionReceipts를 결과와 함께 보존한다.
linkedSkills:
  - engines.data.foundation
  - engines.company
  - engines.gather
  - engines.scan
  - engines.analysis
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-07-23'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 역할과 위치

`data`는 특정 엔진의 별칭이 아니다. L1의 provider와 gather, L1.5의 scan, frame, synth, reference, L2의 analysis, credit, industry, macro, quant가 소유한 데이터 제품을 위에서 연합하는 독립 작업대다.

```text
simulate, story, Universe, AI
              ↓
 Unified Data Workbench
              ↓
      L2 분석 데이터 제품
              ↓
     L1.5 횡단, 정규화 제품
              ↓
       L1 원천, provider 제품
```

하위 owner가 `dataProduct.py`에 metadata provider를 선언하면 중앙 엔진 목록을 수정하지 않아도 다음 catalog snapshot에 자동 반영된다. source와 계산식의 소유권은 하위 엔진에 남고, `data`는 발견, 검증, 실행 예산, projection, lineage 결박을 담당한다.

## 공개 호출 방식

public axis는 둘뿐이다.

```python
import dartlab

dartlab.data()             # catalog, query 가이드
dartlab.data("catalog")   # metadata-only 발견
dartlab.data("query", ...) # stable asset query
```

factor, records, graph, narrative, resource는 새 axis가 아니라 `query`의 typed projection이다. 따라서 같은 asset을 native schema 그대로 쓸 수도 있고 factor store 형태로 투영할 수도 있다. `DataRequest`를 사용하면 한 query에서 asset마다 서로 다른 projection을 지정할 수 있다.

## 카탈로그

```python
from dartlab.data import CatalogQuery

allAssets = dartlab.data("catalog")
l2Assets = dartlab.data(
    "catalog",
    query=CatalogQuery(layers=("L2",), search="valuation"),
)
```

`DataAssetDescriptor`는 최소 `assetId`, `assetVersionId`, `owner`, `layer`, `kind`, `sourceRef`, `queryable`, `temporalSupport`, `selectorKind`, `selectorRequired`, `concurrencyGroup`, executor metadata를 가진다. catalog는 값을 물질화하지 않는다. private, out-of-scope, 폐기, catalog-only 자산도 분류를 위해 보이지만 `queryable=False`로 차단된다.

## 범용 query

```python
from dartlab.data import DataQuery, NativeProjection, QueryBudget

result = dartlab.data(
    "query",
    assets=("analysis.수익성", "credit.overview"),
    query=DataQuery(
        subjects=("005930",),
        projection=NativeProjection(),
        budget=QueryBudget(maxRows=10000, maxBytes=16 * 1024 * 1024),
    ),
)
```

owner별 native schema를 억지로 한 표로 합치지 않는다. `DataResult.partitions`가 asset과 selector별 schema를 보존한다. 전체 query 단위로 asset 수, subject 수, row 수, byte 수, 실행 기한을 제한한다. `maxConcurrency`는 독립 request를 병렬 실행하지만 같은 `concurrencyGroup`과 같은 asset은 직렬화한다.

혼합 query에서는 앞 partition이 전체 row budget을 독점하지 않도록 뒤 실행 task마다 최소 1행과 작은 byte 여유를 예약한다. 결과 partition 순서는 실제 완료 순서가 아니라 요청 순서를 따른다.

## DART와 EDGAR 전종목 원천 순회

전종목 조회는 종목별 API를 호출자가 반복하는 방식이 아니다. 한 mapping query가 DART와 EDGAR request를 함께 등록하고, 작업대가 서로 다른 Arrow schema를 partition으로 보존한 채 하나의 opaque continuation chain으로 순회한다.

```python
import dartlab

page = dartlab.data(
    "query",
    query={
        "requests": [
            {
                "assetId": "resource.finance",
                "requestId": "dartAll",
                "params": {"columns": ["stock_code", "account_id", "thstrm_amount"]},
            },
            {
                "assetId": "resource.edgar",
                "requestId": "edgarAll",
                "params": {"columns": ["cik", "tag", "val"]},
            },
        ],
        "budget": {
            "maxRows": 100000,
            "maxBytes": 64 * 1024 * 1024,
            "timeoutMs": 120000,
        },
    },
)

while page.continuation is not None:
    page = dartlab.data("query", query={"continuation": page.continuation})
```

첫 호출은 전체 원천을 메모리에 한꺼번에 올린다는 뜻이 아니다. query 하나가 작업 단위를 등록한다는 뜻이며, 각 page는 row, byte, time, shard 상한 안에서 반환된다. `DataPartition.selector`와 `DataResult.universeCoverage`는 source shard 수, 선택 shard 수, 완료 shard 수, cursor 위치, market, source provider를 노출한다. DART는 `KR`과 `dart`, EDGAR는 `US`와 `edgar`로 구분된다.

continuation은 private control plane에 결박된 opaque capability다. 별도 프로세스가 token만 전달해 재개할 수 있고, 이미 commit된 page는 원천 provider 접촉 없이 동일하게 replay된다. 이어지는 page는 최초 발급 때 고정한 timeout을 다시 사용한다. 각 public page 진입은 영속 sweep cursor를 이용한 작은 bounded maintenance step을 한 번 실행하므로, 만료 chain과 CAS artifact 정리가 요청 하나를 무제한 점유하지 않는다. token query에는 assets, target, budget 등 원 질의 override를 함께 보내지 않는다.

## 혼합 Data Prism query

```python
from dartlab.data import DataQuery, DataRequest, FactorProjection, NarrativeProjection

result = dartlab.data(
    "query",
    query=DataQuery(
        requests=(
            DataRequest(
                "scan.ratio",
                "technicalFactor",
                projection=FactorProjection(measures=("roe",), unit="percent"),
                measures=("roe",),
            ),
            DataRequest(
                "gather.narrative",
                "filingEvidence",
                projection=NarrativeProjection(),
                subjects=("005930",),
            ),
            DataRequest(
                "analysis.simulationInputs",
                "scenarioState",
                subjects=("005930",),
            ),
        )
    ),
)

factor = result.byRequest("technicalFactor")
arrowTables = result.toArrow()
```

이 호출은 factor store, narrative evidence, simulator input을 별도 엔진으로 분리하지 않는다. 계산은 각 owner가 수행하고 Data Workbench는 같은 snapshot, lineage, quality, budget으로 묶는다. JSON mapping만으로도 동일하게 호출할 수 있어 외부 프로세스와 AI EngineCall이 Python contract 객체를 만들 필요가 없다.

## 호출 동작

`catalog`는 owner의 metadata provider, registry, resource manifest, extraction concept, Company capability를 읽되 실제 값을 실행하지 않는다. `query`는 asset version을 해소하고 temporal support와 policy를 먼저 검사한 뒤 owner의 공개 callable을 실행한다. 결과는 projection하고 전체 query budget을 적용한 다음 coverage, gap, lineage, receipt와 함께 반환한다.

필수 subject 또는 measure가 없으면 owner 실행 전에 `MISSING_SELECTOR`로 실패한다. owner가 `None`, 빈 DataFrame, 빈 mapping 또는 빈 sequence를 반환하면 locator-only resource를 제외하고 `NO_DATA` gap이다. 빈 결과를 성공으로 소비하지 않는다.

## Factor store로 사용

```python
from dartlab.data import DataQuery, FactorProjection

factors = dartlab.data(
    "query",
    "scan.ratio",
    query=DataQuery(
        projection=FactorProjection(
            measures=("roe",),
            unit="percent",
            frequency="Y",
        ),
    ),
)
```

factor row는 `assetId`, `measureId`, `entityId`, `eventAt`, `availableAt`, `knownAt`, `value`, `unit`, `frequency`, `revisionId`, `sourceRef`, `evidenceRef`, `temporalStatus`를 담는다. owner가 unit을 선언하지 않았다면 호출자가 `FactorProjection.unit`을 명시해야 한다. `native` 같은 가짜 단위로 성공시키지 않는다.

최신 전용 asset의 `knownAt`은 `None`이다. query 실행 시각을 knowledge time으로 자동 주입하지 않는다. RSI, momentum, volatility 같은 quant와 technical 계산은 quant, scan 또는 indicator owner가 수행하며 data는 결과를 factor view로 투영한다.

## Narrative evidence로 사용

`NarrativeProjection`은 문자열 목록 대신 `documentId`, `chunkId`, `section`, `text`, `language`, `contentHash`, `eventAt`, `availableAt`, `knownAt`, `revisionId`, `sourceRef`, `evidenceRef`를 가진 table을 반환한다. 이 identity는 keyword, semantic, hybrid retrieval과 답변 인용에서 공통으로 쓸 수 있다. embedding이나 vector index는 runtime SSOT 승인 없이 미리 굽지 않는다.

## 시간과 PIT

```python
from dartlab.data import DataQuery, TimeContext

historical = DataQuery(time=TimeContext(validAt="2024-Q4", knownAt="2025-03-31"))
```

valid time과 knowledge time은 분리한다. descriptor가 실제로 `knownAt`을 executor에 전달할 수 없으면 `PIT_UNSUPPORTED` gap으로 실패한다. latest-only asset을 과거 라벨로 바꾸지 않는다. 시뮬레이터의 `analysis.simulationInputs` asset은 fiscal period `validAt` 절단을 지원하며 filing revision `knownAt`은 지원하지 않는다.

## 대표 반환 형태

`DataResult`는 data와 다음 항목을 같은 snapshot에 묶는다.

- `status`: ok, partial, failed
- `coverage`: 요청, 해소, 성공, 실패 수
- `gaps`: machine-readable 결손과 정책 차단
- `snapshotId`: catalog asset version set
- `contractHash`: asset refs와 query 계약 해시
- `lineageRefs`: source와 실행 ref
- `executionReceipts`: asset version, query, selector에 결박된 영수증
- `DataPartition.lineage`: run, job, dataset 구조의 계보 facet
- `qualityAssertions`: row, byte, provenance, temporal truth 검증 결과

표 형태 partition은 `toPolars()`와 `toArrow()`로 외부 프로세스에 바로 전달한다. 혼합 결과는 `byRequest(requestId)`로 선택한다.

소비자는 partition만 떼어 저장하지 말고 이 envelope를 함께 보존한다.

## 시뮬레이터 내부 사용

공개 `simulate` 경로는 `analysis.simulationInputs`를 동일한 `data("query")` 계약으로 조회한다. Data Workbench가 Company 분기 재무를 한 번 읽고 `validAt`까지 절단한 뒤 snapshot, contract hash, lineage, receipt를 반환한다. 시뮬레이터는 그 고정 입력만 DriverSheet 계산에 사용하고 결과에 `dataSnapshotId`, `dataContractHash`, `dataLineageRefs`, `dataExecutionReceipts`를 노출한다.

## Resource 안전 정책

`ResourceProjection(includePayload=False)`는 payload를 읽지 않고 revision-fixed locator만 반환한다. native full-universe paging은 flat company-sharded resource와 EDGAR finance에 한정하며, 다른 bulk, date-shard, nested, private resource는 무제한 메모리 로드를 허용하지 않는다. pageable resource와 eager asset의 혼합 실행, `requireComplete`, resume query override는 실행 전에 차단한다.

shard-local cursor는 이전 page의 모든 행을 다시 건너뛰는 global OFFSET을 사용하지 않는다. 다만 현재 mutable full-integrity 모드는 각 page 전후에 전체 file set과 shard stat을 재검증한다. cache hit은 file set, size, mtime과 저장된 manifest digest를 검증하며, 외부에서 size와 mtime까지 동일하게 위조한 rewrite를 매 page 다시 해시하지는 않는다. 따라서 데이터 읽기는 page shard에 국한되지만 전체 순회를 아직 `O(total rows + shards)` 또는 immutable cryptographic snapshot이라고 주장하지 않는다. immutable generation과 atomic marker가 도입되기 전까지는 현재의 전수 stat 검증 비용을 유지한다.

## 운영 파이프라인

수집 주기, HF 업로드, prebuild 운영은 [engines.data.foundation](dartlab://skills/engines.data.foundation)에서 다룬다. 그 절차는 Data Workbench의 공개 query 계약과 별개이며 `data`를 운영자 전용 개념으로 축소하지 않는다.

## 기본 검증

- `data()` 가이드의 public axis가 `catalog`, `query` 둘뿐인지 확인한다.
- catalog가 현재 owner registry와 resource를 빠짐없이 반영하고 값을 실행하지 않는지 확인한다.
- 같은 catalog를 반복했을 때 snapshot ID와 asset version 순서가 같은지 확인한다.
- knownAt 미지원 asset이 owner 호출 전에 `PIT_UNSUPPORTED`로 실패하는지 확인한다.
- factor projection이 unit, entity, event time, source, evidence 필드를 보존하는지 확인한다.
- row와 byte 예산이 partition별이 아니라 전체 query에 적용되는지 확인한다.
- bulk resource locator가 payload를 읽지 않고, bulk payload 실행은 차단되는지 확인한다.
- DART와 EDGAR 전종목 request가 한 공개 mapping query와 한 token chain으로 이어지는지 확인한다.
- 별도 프로세스 재시작이 token만으로 이어지고 commit page replay가 provider 없이 byte-stable인지 확인한다.
- shard-local cursor의 tiny page, predicate 0행, deep resume에 중복과 누락이 없는지 확인한다.
- source, selected, completed shard 수와 DART, EDGAR market/provider coverage가 정직한지 확인한다.
- simulator result가 data snapshot, contract hash, lineage, receipt를 노출하는지 확인한다.
- 한 query의 DataRequest마다 다른 projection과 owner parameter가 독립 적용되는지 확인한다.
- latest-only factor와 narrative가 knownAt을 발명하지 않는지 확인한다.
- 구조화 lineage, quality assertion과 Arrow 변환이 data와 같은 partition에 결박되는지 확인한다.
- queryable catalog 전체가 한 혼합 query에서 빠짐없이 라우팅되는지 확인한다.
- engine asset 전체가 records, narrative, factor projection과 Arrow 변환을 통과하는지 확인한다.
- 독립 request는 병렬화되고 Company 공유 상태 group은 직렬화되는지 확인한다.
- `None`과 빈 DataFrame이 `NO_DATA`이며 폐기 axis가 queryable이 아닌지 확인한다.
