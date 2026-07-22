# 05. Signature Data Prism

## 1. 제품 판정

Data Workbench의 최종 정체성은 factor store가 아니다. DartLab이 소유하거나 발견한 모든 데이터 자산을 하나의 진입점에서 목적별 view로 바꾸는 `Data Prism`이다.

```text
                    factor view     quant, technical, ML
owner native data   narrative view  story, research, AI evidence
catalog + query  -> graph view      relation, transmission, causality
                    native view     simulator, domain engine, audit
                    resource view   external locator, bulk handoff
```

외부 사용자는 `dartlab.data("query", ...)` 한 번만 호출한다. 내부 simulator도 같은 계약을 쓴다. 계산은 quant, scan, analysis 등 원래 owner가 수행하고 data는 발견, 실행, view 변환, 시간 진실성, 계보, 품질, transport를 담당한다.

## 2. 공식 설계 조사와 흡수한 개념

### Feast에서 흡수

[Feast Feature View](https://docs.feast.dev/getting-started/concepts/feature-view)의 entity, schema, source, TTL 결박과 [point-in-time join](https://docs.feast.dev/getting-started/concepts/point-in-time-joins)의 row별 event timestamp cutoff를 factor view 원칙으로 흡수했다. 다만 online store와 offline store를 제품 정체성으로 삼지 않는다. DartLab에서는 factor가 여러 projection 중 하나다.

### Apache Iceberg에서 흡수

[Iceberg introduction](https://iceberg.apache.org/docs/latest/)의 immutable snapshot, time travel, schema evolution, hidden partition 원칙을 `snapshotId`, `assetVersionId`, `contractHash`, partition 보존에 반영했다. 물리 table format을 강제하지 않고 federated runtime snapshot 의미만 흡수했다.

### OpenLineage에서 흡수

[OpenLineage facets](https://openlineage.io/docs/spec/facets/)의 run, job, input dataset, output dataset 분리와 [data quality assertions](https://openlineage.io/docs/spec/facets/dataset-facets/data_quality_assertions/)의 expected, observed, success 구조를 경량 `DataLineage`, `QualityAssertion`에 반영했다. 문자열 lineage ref도 호환을 위해 유지한다.

### Apache Arrow Flight와 Polars에서 흡수

[Arrow Flight](https://arrow.apache.org/docs/format/Flight.html)의 record batch stream과 descriptor 기반 transport를 외부 전달 목표로 삼았다. 현재 1차 구현은 `DataPartition.toArrow()`와 `DataResult.toArrow()`이며, 네트워크 Flight server는 별도 transport 배포 범위다. [Polars lazy optimizations](https://docs.pola.rs/user-guide/lazy/optimizations/)의 predicate, projection, slice pushdown은 owner가 지원하는 asset부터 단계적으로 적용한다. data가 owner 전체 결과를 먼저 읽고 숨기는 방식은 장기적으로 제거한다.

### 하이브리드 검색에서 흡수

[Weaviate hybrid search](https://docs.weaviate.io/weaviate/concepts/search/hybrid-search)의 keyword와 vector 병렬 검색, fusion, metadata filtering 개념을 narrative view의 검색 방향으로 채택했다. 현재 구현은 documentId, chunkId, section, language, contentHash, 시간, provenance가 있는 검색 준비형 table이다. embedding이나 vector index를 미리 굽지는 않는다. DartLab의 기존 runtime 검색 역량과 결합할 수 있는 식별 계약만 제공한다.

### Great Expectations에서 흡수

[Great Expectations의 expectation](https://docs.greatexpectations.io/docs/core/define_expectations/)처럼 품질을 설명문이 아닌 검증 결과로 반환한다. 각 partition은 row budget, byte budget, provenance, temporal truth assertion을 데이터와 함께 가진다.

## 3. DartLab 고유 공통 spine

모든 projection을 같은 표로 억지 통합하지 않는다. 대신 아래 의미 spine을 공유한다.

| 영역 | 공통 의미 |
|---|---|
| identity | assetId, assetVersionId, requestId |
| business key | entityId, measureId 또는 documentId, chunkId 또는 graph node, edge ID |
| bitemporal | eventAt, availableAt, knownAt, temporalStatus |
| revision | revisionId, snapshotId, contractHash |
| evidence | sourceRef, evidenceRef, execution receipt |
| quality | status, gaps, QualityAssertion |
| transport | native object, Polars, Arrow |

핵심은 schema 동일성이 아니라 의미 동일성이다. factor row와 narrative chunk가 동일한 시간 및 근거 규칙을 따르므로 시뮬레이션 결과와 자연어 근거를 같은 snapshot에서 재현할 수 있다.

## 4. 혼합 query 계약

```python
import dartlab
from dartlab.data import (
    DataQuery,
    DataRequest,
    FactorProjection,
    NarrativeProjection,
)

result = dartlab.data(
    "query",
    query=DataQuery(
        requests=(
            DataRequest(
                assetId="scan.ratio",
                requestId="technicalFactor",
                projection=FactorProjection(
                    measures=("roe",),
                    unit="percent",
                    frequency="Y",
                ),
                measures=("roe",),
            ),
            DataRequest(
                assetId="gather.narrative",
                requestId="filingEvidence",
                projection=NarrativeProjection(),
                subjects=("005930",),
            ),
            DataRequest(
                assetId="analysis.simulationInputs",
                requestId="scenarioState",
                subjects=("005930",),
            ),
        )
    ),
)

factor = result.byRequest("technicalFactor")
evidence = result.byRequest("filingEvidence")
arrowTables = result.toArrow()
```

Python contract object 없이 JSON mapping만으로도 같은 query를 호출할 수 있다. 따라서 AI EngineCall, 별도 Python 프로세스, notebook, server adapter가 공개 축을 새로 만들 필요가 없다.

## 5. 용도별 책임

### Factor store

`FactorProjection`은 entity, measure, time, value, unit, frequency, revision, source, evidence를 canonical long으로 반환한다. 최신 전용 asset은 `knownAt=None`과 `LATEST_ONLY`를 유지한다. 현재 시각을 knowledge time으로 꾸미지 않는다.

### Quant와 technical

RSI, momentum, volatility, quality score 같은 계산은 quant, scan 또는 indicator owner가 수행한다. Data Workbench는 그 asset을 실행하고 factor view로 내보낸다. 이 경계 덕분에 동일 계산식이 data 안에 복제되지 않는다.

### Narrative와 AI evidence

`NarrativeProjection`은 단순 문자열 배열이 아니다. documentId, chunkId, section, text, language, contentHash, eventAt, availableAt, knownAt, revisionId, sourceRef, evidenceRef를 가진다. keyword, semantic, hybrid retrieval과 답변 인용에 같은 chunk identity를 쓸 수 있다.

### Simulation

simulator는 `analysis.simulationInputs` native view를 소비한다. 혼합 query를 쓰는 외부 오케스트레이터는 같은 snapshot envelope 안에 factor 신호, 공시 근거, simulation state를 함께 요청할 수 있다. data가 simulate를 import하지 않는 단방향은 유지한다.

### Graph

`GraphProjection`은 node와 edge를 보존하고 asset revision, source, execution evidence를 동봉한다. scalar flatten으로 관계 방향과 predicate를 잃지 않는다.

## 6. 데이터 전수 활용의 정확한 의미

2026-07-22 실측 catalog는 353개 asset을 발견한다. 이 중 171개는 현재 runtime에서 queryable이며, 182개는 concept, owner metadata, method, private resource, nested 또는 범위 밖 asset이라 catalog-only다.

따라서 "모든 데이터를 다 활용한다"는 두 단계로 구분해야 한다.

1. 발견과 분류: 현재 대상 asset 353개 모두 catalog에 들어온다.
2. 값 물질화: 정책과 executor가 있는 171개만 즉시 query할 수 있다.

catalog-only를 누락으로 숨기지 않는다. `queryable=False`, visibility, temporalSupport, gap으로 이유를 드러낸다. private 데이터나 실행 불가능한 개념 메타데이터를 억지로 값처럼 반환하지 않는 것이 완성도다.

## 7. 현재 완성 범위와 다음 확장

현재 완료:

- 두 public axis 유지
- asset별 혼합 projection 한 번 호출
- factor, narrative, graph, native, records, resource view
- request별 독립 subjects, measures, time, params
- 구조화 lineage와 quality assertion
- Polars와 Arrow 즉시 변환
- simulator 동일 query 계약 유지
- 외부 JSON mapping 호출
- latest-only temporal truth 보존

후속 transport 및 scale 범위:

- 실제 Arrow Flight server와 ticket 기반 streaming
- owner별 predicate, projection, slice pushdown
- redeemable continuation token
- knownAt vintage를 실제 제공하는 source 확대
- narrative hybrid retrieval adapter와 reranker
- quality suite의 도메인별 expectation 확대

이 항목들은 현재 의미 계약을 바꾸지 않고 확장할 수 있다. 특히 vector index나 precomputed 복제본은 runtime SSOT가 불가능함이 증명되고 사용자 승인을 받은 경우에만 도입한다.
