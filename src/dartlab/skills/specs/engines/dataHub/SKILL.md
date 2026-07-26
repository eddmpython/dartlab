---
id: engines.dataHub
title: DartLab DataHub
kind: curated
scope: builtin
status: observed
category: engines
purpose: DataHub는 L1, L1.5, L2의 원천, 정규 데이터, 횡단 데이터, 분석 자산을 하나의 자동 발견 카탈로그와 bounded query 계약으로 제공한다. 외부 프로세스의 범용 데이터 API, factor store projection, 시뮬레이터 입력 스냅샷에 같은 계약을 쓴다. 트리거는 '데이터허브', '데이터 작업대', '팩터 스토어', '전종목 DART EDGAR 조회'다.
whenToUse:
  - dataHub
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
  - materialization mode
  - structured materialization receipt
outputs:
  - DataCatalogResult
  - DataResult
  - typed DataPartition
  - coverage와 gap
  - snapshot과 lineage
  - 실제 결과 content hash와 data snapshot
  - execution receipt
  - 구조화 DataLineage와 QualityAssertion
  - Polars와 Arrow table
  - 전종목 source shard coverage와 opaque continuation
  - KR과 US 현재 상장 factor universe coverage와 opaque continuation
  - immutable generation receipt
  - durable remote job와 lease 상태
  - 무손실 원격 DataResult
capabilityRefs:
  - dataHub
  - dataHub.catalog
  - dataHub.query
knowledgeRefs:
  - start.dartlabSkillOs
  - engines.dataHub.foundation
  - engines.company
  - engines.gather
  - engines.scan
  - engines.analysis
sourceRefs:
  - dartlab://skills/engines.dataHub
requiredEvidence:
  - assetId
  - assetVersionId
  - snapshotId
  - dataSnapshotId
  - DataPartition.contentHash
  - contractHash
  - coverage
  - gaps
  - lineageRefs
  - executionReceipts
  - materializationReceipt
  - qualityAssertions
expectedOutputs:
  - 선택한 stable asset ID와 projection
  - bounded partition 결과
  - 시점 지원 여부와 honest gap
  - 같은 snapshot에 결박된 lineage와 receipt
  - 저장 모드에서는 exact materialization receipt
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
  - 원천 접근 entity 수를 strict factor 성공 entity 수로 과장함
  - cold materialization을 첫 응답 즉시 전종목 적재라고 설명함
  - receipt 없이 offline exact generation을 재생한다고 주장함
forbidden:
  - DataHub를 특정 분석 엔진 묶음으로 축소하지 않는다.
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
  - EDGAR 단일 종목의 revision-aware 재무 feature를 knownAt 기준으로 조회
  - DART KR과 EDGAR US 현재 상장 universe의 revision-aware 재무 feature를 한 query와 continuation으로 순회
  - immutable generation을 다른 process에서 receipt만으로 재생
  - 외부 process에서 sync 또는 asyncio client로 query 제출
  - 여러 host worker가 durable queue를 원자 claim해 실행
procedure:
  - dartlab.dataHub()로 catalog와 query 두 public axis를 확인한다.
  - dartlab.dataHub("catalog")로 owner, layer, kind, temporalSupport, queryable을 조회한다.
  - stable assetId를 선택하고 단일 view면 DataQuery, 혼합 view면 asset별 DataRequest에 subjects, measures, projection, time을 명시한다.
  - dartlab.dataHub("query", assetId, query=...) 또는 dartlab.dataHub("query", query=DataQuery(requests=(...)))를 호출한다.
  - status, coverage, gaps를 먼저 검사한 뒤 partition data를 소비한다.
  - pageable resource와 owner 계산 결과를 한 소비 흐름으로 읽을 때 result.iterPages() 또는 result.iterAllArrowBatches()를 사용한다.
  - 수동 재개가 필요하면 partial result의 continuation만 다음 query에 전달하고 원 질의를 덮어쓰지 않는다.
  - 저장이 필요하면 runtime, reuse, refresh, offline 중 의미에 맞는 materialization mode를 query에 지정한다.
  - 다른 process의 exact 재생에는 DataResult.materializationReceipt를 보존하고 offline mode에 그대로 전달한다.
  - snapshotId, dataSnapshotId, contractHash, partition contentHash, lineageRefs, executionReceipts, materializationReceipt를 함께 보존한다.
linkedSkills:
  - engines.dataHub.foundation
  - engines.company
  - engines.gather
  - engines.scan
  - engines.analysis
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-07-26'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 역할과 위치

`dataHub`는 특정 엔진의 별칭이 아니다. L1의 provider와 gather, L1.5의 scan, frame, synth, reference, L2의 analysis, credit, industry, macro, quant가 소유한 데이터 제품을 위에서 연합하는 독립 데이터 플랫폼이다.

```text
simulate, story, Universe, AI
              ↓
       DartLab DataHub
              ↓
      L2 분석 데이터 제품
              ↓
     L1.5 횡단, 정규화 제품
              ↓
       L1 원천, provider 제품
```

하위 owner가 `dataProduct.py`에 metadata provider를 선언하면 중앙 엔진 목록을 수정하지 않아도 다음 catalog snapshot에 자동 반영된다. source와 계산식의 소유권은 하위 엔진에 남고, `dataHub`는 발견, 검증, 실행 예산, projection, lineage 결박을 담당한다.

## 공개 호출 방식

public axis는 둘뿐이다.

```python
import dartlab

dartlab.dataHub()             # catalog, query 가이드
dartlab.dataHub("catalog")   # metadata-only 발견
dartlab.dataHub("query", ...) # stable asset query
```

factor, records, graph, narrative, resource는 새 axis가 아니라 `query`의 typed projection이다. 따라서 같은 asset을 native schema 그대로 쓸 수도 있고 factor store 형태로 투영할 수도 있다. `DataRequest`를 사용하면 한 query에서 asset마다 서로 다른 projection을 지정할 수 있다.

다른 프로세스와 머신은 같은 의미 계약을 versioned remote API로 사용한다.

```python
from dartlab.dataHub import AsyncDataHubClient, DataHubClient

with DataHubClient("https://host", clientToken) as hub:
    job = hub.query(query, wait=False, idempotencyKey="daily-close")
    result = hub.wait(job.jobId)

async with AsyncDataHubClient("https://host", clientToken) as hub:
    result = await hub.query(query)
```

분산 worker는 `python -m dartlab.dataHub.workerPlane --base-url https://host --worker-id node-a`로 실행한다. 여러 worker가 같은 durable queue를 pull하되 원자 lease와 epoch가 한 job의 중복 확정을 차단한다.

## 카탈로그

```python
from dartlab.dataHub import CatalogQuery

allAssets = dartlab.dataHub("catalog")
l2Assets = dartlab.dataHub(
    "catalog",
    query=CatalogQuery(layers=("L2",), search="valuation"),
)
```

`DataAssetDescriptor`는 최소 `assetId`, `assetVersionId`, `owner`, `layer`, `kind`, `sourceRef`, `queryable`, `temporalSupport`, `selectorKind`, `selectorRequired`, `concurrencyGroup`, executor metadata를 가진다. catalog는 값을 물질화하지 않는다. private, out-of-scope, 폐기, catalog-only 자산도 분류를 위해 보이지만 `queryable=False`로 차단된다.

## 범용 query

```python
from dartlab.dataHub import DataQuery, NativeProjection, QueryBudget

result = dartlab.dataHub(
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

page = dartlab.dataHub(
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

for partitionKey, batch in page.iterAllArrowBatches(
    maxRows=65536,
    maxBytes=8 * 1024 * 1024,
):
    consume(partitionKey, batch)
```

첫 호출은 전체 원천을 메모리에 한꺼번에 올린다는 뜻이 아니다. query 하나가 작업 단위를 등록하고 `iterAllArrowBatches()`가 opaque continuation을 내부에서 자동 소비한다는 뜻이다. 각 page와 Arrow batch는 row, byte, time, shard 상한 안에서 반환된다. `iterPages()`는 page envelope가 필요한 소비자용이고 checkpoint callback으로 다음 token을 process restart용 저장소에 기록할 수 있다. `DataPartition.selector`와 `DataResult.universeCoverage`는 source shard 수, 선택 shard 수, 완료 shard 수, cursor 위치, market, source provider를 노출한다. DART는 `KR`과 `dart`, EDGAR는 `US`와 `edgar`로 구분된다.

이 절의 기능은 `resource.finance`와 `resource.edgar` 원천 shard 순회다. 원천 paging 자체를 모든 계산 owner의 factor paging으로 바꿔 말하지 않는다.

continuation은 private control plane에 결박된 opaque capability다. 별도 프로세스가 token만 전달해 재개할 수 있고, 이미 commit된 page는 원천 provider 접촉 없이 동일하게 replay된다. 이어지는 page는 최초 발급 때 고정한 timeout을 다시 사용한다. 각 public page 진입은 영속 sweep cursor를 이용한 작은 bounded maintenance step을 한 번 실행하므로, 만료 chain과 CAS artifact 정리가 요청 하나를 무제한 점유하지 않는다. token query에는 assets, target, budget 등 원 질의 override를 함께 보내지 않는다.

## DART와 EDGAR 현재 상장 계산 feature 순회

`analysis.dartFinancialFeatures`와 `analysis.edgarFinancialFeatures`는 KR과 US 현재 상장 universe의 계산 factor를 runtime continuation으로 순회한다. 호출자는 종목별 함수를 반복하지 않고 한 query로 두 시장 전체 작업을 등록한다.

```python
import dartlab

first = dartlab.dataHub(
    "query",
    query={
        "requests": [
            {
                "assetId": "analysis.dartFinancialFeatures",
                "requestId": "krListedPit",
                "universe": {"markets": ["KR"], "membership": "listed"},
                "projection": {
                    "kind": "factor",
                    "measures": [
                        "financial.revenue",
                        "financial.operatingMargin",
                    ],
                },
                "time": {"knownAt": "20260723"},
            },
            {
                "assetId": "analysis.edgarFinancialFeatures",
                "requestId": "usListedPit",
                "universe": {"markets": ["US"], "membership": "listed"},
                "projection": {
                    "kind": "factor",
                    "measures": [
                        "financial.revenue",
                        "financial.operatingMargin",
                    ],
                },
                "time": {"knownAt": "20260723"},
            }
        ],
        "budget": {
            "maxRows": 100000,
            "maxBytes": 64 * 1024 * 1024,
            "timeoutMs": 120000,
            "maxAssets": 4,
            "maxSubjects": 20000,
            "maxConcurrency": 2,
        },
    },
)

for page in first.iterPages():
    consume(page)
```

전종목 완주는 실측으로 인증했다. KR은 42 page 355.007초, US는 121 page 605.024초, 두 시장 혼합은 162 page 852.738초로 `iterPages()`가 수동 token loop 없이 끝까지 소비했다. 혼합 실행은 엔티티 10,344개를 한 query로 등록했고 factor row 8,932개는 단일 시장 완주 합계와 정확히 일치했다. page 수는 세 경우 모두 `ceil(엔티티/64)` 예측치와 맞았고 `snapshotId`는 전 page에서 단일 유지됐다.

한 query는 전체 universe와 계산 계약을 고정한다는 뜻이다. 첫 응답에서 전종목을 모두 계산하거나 메모리에 적재한다는 뜻이 아니다. owner lane 한 page는 종목 시도 64개를 넘지 않으며 row, byte, time 예산이 먼저 소진되면 더 작아진다. 종목별 실패는 gap과 누적 universe coverage에 남고 cursor는 다음 종목으로 진행한다.

continuation은 원 query, contract, 외부 Arrow schema, source manifest, universe membership, entity와 source ID mapping, DART 결산월, requested measure를 digest로 고정한다. 미완료 token을 재개할 때 source, universe, owner code, requested measure가 바뀌면 실패한다. commit된 page replay는 source와 owner를 다시 접촉하지 않는다. token은 private control plane에 24시간 임시 보존된다.

EDGAR revenue 또는 operating margin만 요청하면 stock state와 분리된 strict flow compiler를 사용한다. measure를 비우거나 stock measure가 하나라도 포함되면 기존 full-state strict compiler를 유지한다. 원천 접근 성공률과 factor 성공률은 같은 수치로 보고하지 않는다.

명시한 `subjects`는 기존 eager `subjectFanout` 경로를 유지한다. historical `asOf`, `allKnown`, `requireComplete`는 지원하지 않는다. pageable resource, 계산 owner, 일반 eager asset의 혼합은 outer continuation 하나로 지원한다.

실제 읽기 전용 감사에서 DART는 2,661개 중 2,352개 strict feature 성공, 88.3878%였다. EDGAR는 2026-07-26 기준 7,683개 universe에서 measure 미지정 또는 stock measure를 포함하는 full-state strict compiler가 2,420개 성공, 31.4981%였고 `financial.revenue`와 `financial.operatingMargin`만 요청하는 flow-only compiler가 3,256개 성공, 42.3793%였다. `financial.revenue` 단독은 4,038개 성공, 52.5576%다. 이 세 EDGAR 수치와 원천 접근 성공률은 서로 바꿔 쓰지 않는다. 나머지는 누락하지 않고 source, PIT filing, flow window, lineage, stock state, balance, unit, revision gap으로 분류했다.

EDGAR full-state 성공률은 요청하지 않은 세분 항목을 요구하지 않도록 정정한 결과다. 필수 앵커는 자산총계, 부채총계, 연결자본 셋이고 현금, 매출채권, 재고, 매입채무, 유형자산, 차입금은 태깅되지 않으면 0으로 두고 `imputedZeroComponents` 경고에 남긴다. `otherNetAssets`가 잔차 플러그라 임퓨트한 금액은 플러그로 흡수되고 대차 항등식은 실제 앵커 값으로 검사한다. 세분성은 줄지만 항등식, PIT cutoff, 4분기 연속성, 동일 accession lineage, revision 충돌 검증은 그대로다.

위 백분율의 분모 7,683은 NYSE, Nasdaq, CBOE 전 티커라 ADR, ETF, 펀드, 워런트, 다중 클래스가 함께 들어 있다. 성공률을 시장 커버리지로 읽지 않는다. 실측 분해는 다음과 같다. 449개는 companyfacts parquet 자체가 없고, 80개 표본에서 47.5%는 SEC 원본이 404, 50.0%는 태그 20개 미만 껍데기, 2.5%만 실데이터를 가진 수집 갭이었다. 1,456개는 parquet은 있으나 cutoff 이전 10-K 또는 10-Q가 없는 ETF, 펀드, 20-F 외국기업이다. 이 둘을 뺀 사업회사 5,778개 기준으로 다시 재면 revenue 단독 69.9%, flow-only 56.4%, full-state 41.9%다.

남은 결손의 책임 소재도 실측했다. 단독분기 매출 행을 4개 이상 가진 회사는 97.8%가 성공하므로 컴파일러는 병목이 아니다. 나머지는 분기 흐름을 YTD와 연간으로만 태깅하는 filer 관행이라 태그 확장으로 열리지 않는다.

## Immutable generation과 다른 process 재생

materialization은 새 axis가 아니라 기존 query의 정책이다.

```python
built = dartlab.dataHub(
    "query",
    query={
        "requests": [...],
        "budget": {...},
        "materialization": {"mode": "refresh"},
    },
)
receipt = built.materializationReceipt

offline = dartlab.dataHub(
    "query",
    query={
        "materialization": {
            "mode": "offline",
            "receipt": receipt,
        }
    },
)
```

- `runtime`: 저장 없이 기존 bounded continuation을 실행한다.
- `reuse`: 같은 logical query의 최신 READY generation을 먼저 찾고, 없으면 cold build한다.
- `refresh`: 현재 source와 contract를 다시 계획해 exact generation을 build하거나 동일 READY를 재사용한다.
- `offline`: receipt가 가리키는 exact READY generation만 읽는다.

generation key는 asset, source, query, universe, contract, schema digest 여섯 개를 결박한다. BUILDING은 reader에게 보이지 않는다. Arrow page와 terminal manifest는 private CAS에 저장하고 READY ledger 전이를 publication point로 사용한다. SQLite에는 digest, 상태, 수치, lease만 저장한다.

같은 `DARTLAB_HOME`을 보는 fresh process는 receipt만으로 catalog, owner, source 호출 없이 재생한다. public page 한 번에 목표 materialization page payload를 하나만 읽는다. cold build는 terminal generation을 동기적으로 완성한 뒤 첫 page와 receipt를 반환하며, warm replay는 한 page만 읽는다.

private runtime root 정본은 `DARTLAB_HOME/dataHub` 하나다. 레거시 경로나 이중 경로 폴백은 두지 않는다.

이 저장 계약은 factor에만 한정되지 않는다. native, narrative, graph, records, resource projection도 같은 immutable generation을 쓴다. 같은 machine 또는 공유 private storage의 exact replay와 함께 versioned remote API, 역할 분리 인증, durable job, 다중 host pull worker를 지원한다.

## 혼합 Data Prism query

```python
from dartlab.dataHub import DataQuery, DataRequest, FactorProjection, NarrativeProjection

result = dartlab.dataHub(
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

이 호출은 factor store view, narrative evidence, simulator input을 별도 엔진으로 분리하지 않는다. 계산은 각 owner가 수행하고 DataHub는 같은 snapshot, lineage, quality, budget으로 묶는다. JSON mapping만으로도 동일하게 호출할 수 있어 외부 프로세스와 AI EngineCall이 Python contract 객체를 만들 필요가 없다. EngineCall과 HTTP master API는 nested DataFrame과 Series를 문자열로 바꾸지 않고 schema, 전체 행 수, bounded row preview, continuation을 구조적으로 보존한다.

## 호출 동작

`catalog`는 owner의 metadata provider, registry, resource manifest, extraction concept, Company capability를 읽되 실제 값을 실행하지 않는다. `query`는 asset version을 해소하고 temporal support와 policy를 먼저 검사한 뒤 owner의 공개 callable을 실행한다. 결과는 projection하고 전체 query budget을 적용한 다음 coverage, gap, lineage, receipt와 함께 반환한다.

필수 subject 또는 measure가 없으면 owner 실행 전에 `MISSING_SELECTOR`로 실패한다. owner가 `None`, 빈 DataFrame, 빈 mapping 또는 빈 sequence를 반환하면 locator-only resource를 제외하고 `NO_DATA` gap이다. 빈 결과를 성공으로 소비하지 않는다.

## Factor store로 사용

```python
from dartlab.dataHub import DataQuery, FactorProjection

factors = dartlab.dataHub(
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

revision-aware EDGAR 재무 feature도 같은 외부 진입점으로 조회한다.

```python
import dartlab

pit = dartlab.dataHub(
    "query",
    query={
        "requests": [
            {
                "assetId": "analysis.edgarFinancialFeatures",
                "requestId": "aaplPit",
                "subjects": ["AAPL"],
                "projection": {
                    "kind": "factor",
                    "measures": [
                        "financial.revenue",
                        "financial.operatingMargin",
                    ],
                },
                "time": {"knownAt": "2025-02-01"},
            }
        ]
    },
)
```

이 자산은 로컬 EDGAR companyfacts를 한 번 읽고 실제 filing cutoff를 적용한다. 현재 원천이 historical admission snapshot 전체를 보존하지 않으므로 결과는 `latestRetained`, `periodOnly`, `conditional`이다. query cutoff를 관측의 knowledge time이나 revision identity로 복사하지 않는다. 인접 cutoff에서 같은 evidence와 값이 선택되면 같은 observation ID와 revision ID를 유지한다.

일반 factor row는 `assetId`, `measureId`, `entityId`, `eventAt`, `availableAt`, `knownAt`, `value`, `unit`, `frequency`, `revisionId`, `sourceRef`, `evidenceRef`, `temporalStatus`를 담는다. typed feature observation에서 나온 row는 여기에 `featureVersionId`, `observationId`, `featureRegistryHash`, `featureObservationSetHash`, `featureQueryHash`, `normalizationRuleHash`, vintage payload, artifact, contract, receipt identity를 더해 정의, 값, 시점, evidence를 함께 결박한다. owner가 unit을 선언하지 않았다면 호출자가 `FactorProjection.unit`을 명시해야 한다. `native` 같은 가짜 단위로 성공시키지 않는다.

최신 전용 asset의 `knownAt`은 `None`이다. query 실행 시각을 knowledge time으로 자동 주입하지 않는다. RSI, momentum, volatility 같은 quant와 technical 계산은 quant, scan 또는 indicator owner가 수행하며 data는 결과를 factor view로 투영한다.

현재 `FactorProjection`과 `FeatureObservationSet`은 content-sealed factor view와 revision-aware PIT selection을 제공한다. 엄격한 달력 날짜, `MARKET:ID` entity, valid time과 knowledge time, staleness, bounds, same-day conditional, revision ambiguity, missing coverage를 공통 data 계약에서 검증한다. DART와 EDGAR 현재 상장 universe는 계산 feature paging을 지원하고, exact six-pin immutable generation과 receipt를 쓰면 다른 process가 같은 factor page를 owner와 source 호출 없이 재생한다. 원격 query와 분산 materialization worker는 durable job과 lease 경계로 지원하며 historical universe는 아직 지원하지 않는다.

## Narrative evidence로 사용

`NarrativeProjection`은 문자열 목록 대신 `documentId`, `chunkId`, `section`, `text`, `language`, `contentHash`, `eventAt`, `availableAt`, `knownAt`, `revisionId`, `sourceRef`, `evidenceRef`를 가진 table을 반환한다. 이 identity는 keyword, semantic, hybrid retrieval과 답변 인용에서 공통으로 쓸 수 있다. embedding이나 vector index를 추가하면 source와 query pin, atomic generation 정책을 그대로 적용한다.

## 시간과 PIT

```python
from dartlab.dataHub import DataQuery, TimeContext

historical = DataQuery(time=TimeContext(validAt="2024-Q4", knownAt="2025-03-31"))
```

valid time과 knowledge time은 분리한다. descriptor가 실제로 `knownAt`을 executor에 전달할 수 없으면 `PIT_UNSUPPORTED` gap으로 실패한다. factor와 narrative canonical projection은 row별 observation knowledge time과 revision까지 보존할 수 없으면 `OBSERVATION_PIT_METADATA_REQUIRED`로 추가 차단한다. query cutoff를 row의 `knownAt`으로 복사하지 않는다. latest-only asset을 과거 라벨로 바꾸지 않는다. 시뮬레이터의 `analysis.simulationInputs` asset은 fiscal period `validAt` 절단을 지원하며 filing revision `knownAt`은 지원하지 않는다.

PIT factor owner가 `observationPIT=True`를 선언했더라도 실제 반환값이 `FeatureObservationSet` 또는 검증된 `feature-observation-input-v1` envelope가 아니면 `FEATURE_OBSERVATION_ENVELOPE_REQUIRED`로 실패한다. 같은 event, availability, knowledge timestamp에 서로 다른 revision이 남으면 revision ID 문자열 순서로 고르지 않고 ambiguous로 차단한다. `requireExact`는 명시적인 entity scope와 완전한 feature matrix가 필요하며 missing, stale, bounds 위반, same-day date precision, conditional vintage 중 하나라도 있으면 exact가 아니다.

## 대표 반환 형태

`DataResult`는 data와 다음 항목을 같은 snapshot에 묶는다.

- `status`: ok, partial, failed
- `coverage`: 요청, 해소, 성공, 실패 수
- `gaps`: machine-readable 결손과 정책 차단
- `snapshotId`: catalog asset version set
- `dataSnapshotId`: contract, universe, ordered partition content를 결박한 실제 반환 데이터 snapshot. 모든 partition이 봉인될 때만 존재
- `contractHash`: asset refs와 query 계약 해시
- `lineageRefs`: source와 실행 ref
- `executionReceipts`: request identity와 실제 반환 content hash에 결박된 영수증
- `materializationReceipt`: exact immutable generation key, terminal root, six pins
- `DataPartition.contentHash`: schema와 실제 반환값의 deterministic SHA-256 identity
- `DataPartition.lineage`: run, job, dataset 구조의 계보 facet
- `qualityAssertions`: row, byte, provenance, temporal truth 검증 결과

표 형태 partition은 `toPolars()`와 `toArrow()`로 외부 프로세스에 바로 전달한다. 혼합 결과는 `byRequest(requestId)`로 선택한다.

소비자는 partition만 떼어 저장하지 말고 이 envelope를 함께 보존한다.

## 시뮬레이터 내부 사용

공개 `simulate` 경로는 `analysis.simulationInputs`를 동일한 `dataHub("query")` 계약으로 조회한다. DataHub가 Company 분기 재무를 한 번 읽고 `validAt`까지 절단한 뒤 실제 payload 기반 data snapshot, catalog snapshot, contract hash, lineage, receipt를 반환한다. 시뮬레이터는 content seal이 없는 성공 입력을 거부하고 결과에 `dataSnapshotId`, `dataContractHash`, `dataLineageRefs`, `dataExecutionReceipts`를 노출한다.

feature registry, observation, query, vintage 계약의 정본은 `dartlab.dataHub`에 있다. `dartlab.data`는 compatibility re-export로 유지하므로 외부 작업대와 시뮬레이터가 같은 feature 의미와 시점 선택 규칙을 공유한다.

## Resource 안전 정책

`ResourceProjection(includePayload=False)`는 payload를 읽지 않고 revision-fixed locator만 반환한다. native full-universe paging은 flat company-sharded resource와 EDGAR finance에 한정하며, 다른 bulk, date-shard, nested, private resource는 무제한 메모리 로드를 허용하지 않는다. pageable resource 또는 owner 계산과 eager asset의 혼합은 outer continuation 하나로 실행한다. `requireComplete`와 resume query override는 실행 전에 차단한다.

shard-local cursor는 이전 page의 모든 행을 다시 건너뛰는 global OFFSET을 사용하지 않는다. description과 read는 같은 single-use manifest session을 써서 동일 page의 전수 manifest 순회를 3회에서 2회로 줄였다. mutable runtime source는 page 준비 시점과 반환 전 file set과 shard stat을 재검증한다. cache hit은 file set, size, mtime과 저장된 manifest digest를 검증하며, 외부에서 size와 mtime까지 동일하게 위조한 rewrite를 매 page 다시 해시하지는 않는다. exact offline 재현이 필요하면 runtime page가 아니라 READY materialization receipt를 보존한다.

## 운영 파이프라인

수집 주기, HF 업로드, prebuild 운영은 [engines.dataHub.foundation](dartlab://skills/engines.dataHub.foundation)에서 다룬다. 그 절차는 DataHub의 공개 query 계약과 별개이며 `dataHub`를 운영자 전용 개념으로 축소하지 않는다.

## 기본 검증

- `dataHub()` 가이드의 public axis가 `catalog`, `query` 둘뿐인지 확인한다.
- catalog가 현재 owner registry와 resource를 빠짐없이 반영하고 값을 실행하지 않는지 확인한다.
- 같은 catalog를 반복했을 때 snapshot ID와 asset version 순서가 같은지 확인한다.
- knownAt 미지원 asset이 owner 호출 전에 `PIT_UNSUPPORTED`로 실패하는지 확인한다.
- factor projection이 unit, entity, event time, source, evidence 필드를 보존하는지 확인한다.
- row와 byte 예산이 partition별이 아니라 전체 query에 적용되는지 확인한다.
- bulk resource locator가 payload를 읽지 않고, bulk payload 실행은 차단되는지 확인한다.
- DART와 EDGAR 전종목 request가 한 공개 mapping query와 한 token chain으로 이어지는지 확인한다.
- 첫 DataResult의 iterAllArrowBatches()가 수동 token loop 없이 DART와 EDGAR 모든 page를 bounded batch로 소비하는지 확인한다.
- `analysis.dartFinancialFeatures`와 `analysis.edgarFinancialFeatures`의 KR, US 현재 상장 universe가 한 query로 등록되고 owner lane당 최대 64개 종목 시도와 continuation으로 이어지는지 확인한다.
- owner paging의 종목 실패가 gap을 남기고 cursor를 전진시키며, row 예산이 page를 줄여도 중복과 누락이 없는지 확인한다.
- owner continuation이 query, requested measure, contract, schema, source manifest, universe membership, entity와 source ID mapping, DART 결산월 drift를 재개 전에 차단하는지 확인한다.
- EDGAR flow-only measure는 stock fact 없이 성공하고 measure 미지정 또는 stock measure는 full-state strict compiler를 유지하는지 확인한다.
- 명시한 `subjects`는 eager 경로를 유지하고 historical universe와 `requireComplete`는 owner 호출 전에 실패하는지 확인한다.
- pageable, owner, eager 혼합 query가 outer continuation 하나만 반환하고 sealed eager owner를 resume에서 다시 호출하지 않는지 확인한다.
- fresh eager child가 network, subprocess, Python writer와 알려진 데이터 native writer를 차단하고 timeout 뒤 PID와 thread zero-live인지 확인한다.
- 별도 프로세스 재시작이 token만으로 이어지고 commit page replay가 provider 없이 byte-stable인지 확인한다.
- refresh가 exact six-pin READY generation과 receipt를 만들고 reuse와 offline이 같은 receipt를 반환하는지 확인한다.
- fresh process receipt replay가 catalog, owner, source 0회이고 materialization page payload를 public page당 한 번만 읽는지 확인한다.
- 원격 worker complete payload가 bounded DataResult wire와 digest 검증을 통과해야만 succeeded로 전이되는지 확인한다.
- reader lease가 page read와 GC 사이 generation 전이를 막고 bounded maintenance가 결국 artifact를 회수하는지 확인한다.
- shard-local cursor의 tiny page, predicate 0행, deep resume에 중복과 누락이 없는지 확인한다.
- source, selected, completed shard 수와 DART, EDGAR market/provider coverage가 정직한지 확인한다.
- simulator result가 data snapshot, contract hash, lineage, receipt를 노출하는지 확인한다.
- 같은 query와 같은 값은 같은 contentHash, execution receipt, dataSnapshotId를 만들고 값이 바뀌면 셋 모두 바뀌는지 확인한다.
- EngineCall과 HTTP가 nested factor DataFrame을 문자열이 아닌 bounded 구조로 보존하는지 확인한다.
- 한 query의 DataRequest마다 다른 projection과 owner parameter가 독립 적용되는지 확인한다.
- latest-only factor와 narrative가 knownAt을 발명하지 않는지 확인한다.
- observationPIT owner가 일반 DataFrame을 반환하면 typed envelope 요구로 실패하는지 확인한다.
- 동일 timestamp의 서로 다른 revision, stale, bounds 위반, same-day date precision이 exact로 통과하지 않는지 확인한다.
- canonical entity와 달력 날짜, feature version, observation identity가 content hash와 factor row에 결박되는지 확인한다.
- `analysis.edgarFinancialFeatures`의 인접 cutoff가 같은 evidence일 때 동일 revision을 유지하고 현재 보존 범위를 conditional로 표시하는지 확인한다.
- raw DART와 EDGAR paging, 두 시장의 계산 feature paging, immutable materialization 범위를 서로 바꿔 말하지 않는지 확인한다.
- 구조화 lineage, quality assertion과 Arrow 변환이 data와 같은 partition에 결박되는지 확인한다.
- queryable catalog 전체가 한 혼합 query에서 빠짐없이 라우팅되는지 확인한다.
- engine asset 전체가 records, narrative, factor projection과 Arrow 변환을 통과하는지 확인한다.
- 독립 request는 병렬화되고 Company 공유 상태 group은 직렬화되는지 확인한다.
- `None`과 빈 DataFrame이 `NO_DATA`이며 폐기 axis가 queryable이 아닌지 확인한다.
