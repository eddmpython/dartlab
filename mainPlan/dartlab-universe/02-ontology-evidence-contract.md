# 02. Ontology and Evidence Contract

## 1. 원칙

온톨로지는 데이터 사본이 아니다. stable identity, predicate 의미, 시간, 근거, 공개 경계를 정의하는 작은 계약이다.

Universe는 다음을 분리한다.

- **Entity**: 장기간 유지되는 개체
- **Observation**: 특정 시점의 값
- **Assertion**: 한 source가 주장하는 관계 또는 속성
- **Relation**: 같은 subject, predicate, object assertion들을 묶은 presentation view
- **Projection**: 질문과 시점에 맞춘 일회성 scene

## 2. Canonical ID

### 개체 ID

| kind | 형식 | 예 | 안정성 원칙 |
|---|---|---|---|
| KR legal entity | `kr:dart:corp:{corpCode}` | `kr:dart:corp:00126380` | 종목코드보다 DART corpCode 우선 |
| KR security | `kr:krx:security:{isin}` | ISIN 존재 시 사용 | stockCode 변경과 법인 분리 |
| KR security fallback | `kr:krx:stock:{stockCode}` | `kr:krx:stock:005930` | fallback임을 kind로 명시 |
| US legal entity | `us:sec:cik:{cik10}` | `us:sec:cik:0000320193` | ticker보다 CIK 우선 |
| US security | `us:{exchange}:ticker:{ticker}` | `us:nasdaq:ticker:AAPL` | entity와 별도, validity 필요 |
| DART filing | `kr:dart:filing:{rceptNo}` | 접수번호 | 원문 deep link 기준 |
| SEC filing | `us:sec:filing:{accessionNo}` | accession number | 원문 deep link 기준 |
| industry | `dartlab:industry:{id}` | `dartlab:industry:semiconductor` | taxonomy version과 함께 |
| skill | `dartlab:skill:{skillId}` | `dartlab:skill:engines.credit` | Lens Plane만 |
| capability | `dartlab:capability:{apiRef}` | capability key | Lens Plane만 |

현재 map의 stockCode는 presentation key다. identity SSOT로 승격하지 않는다. ID resolver는 `reference` 및 listing resolver가 소유하고, UI가 독자 alias dict를 만들지 않는다.

## 3. UniverseNode

```text
UniverseNode
  id: string
  kind: entity | security | filing | industry | metric | event
  label: string
  market: KR | US | GLOBAL | null
  attributes: bounded map
  validFrom: ISO date | null
  validTo: ISO date | null
  dataAsOf: ISO date | null
  sourceRefs: string[]
  redistributionClass: public | metadataOnly | localOnly | unknown
```

노드 attribute에는 큰 원문, 전체 시계열, 중첩 DataFrame을 넣지 않는다. 큰 값은 sourceRef나 tableRef로 가리킨다.

## 4. Assertion과 Relation

### UniverseAssertion

```text
UniverseAssertion
  assertionId: sha256 canonical payload
  subjectId: canonical entity id
  predicate: controlled predicate id
  objectId: canonical entity id | null
  literal: typed literal | null
  eventAt: ISO date | null
  validFrom: ISO date | null
  validTo: ISO date | null
  availableAt: ISO datetime
  knowledgeAsOf: ISO datetime
  revisionId: string
  evidenceRefs: string[]
  provenance: string[]
  method: directTable | directText | deterministicCalc | entityMatch | modelInference | scenario
  evidenceClass: A | B | C | D
  extractionConfidence: 0..1 | null
  status: candidate | observed | corroborated | disputed | retracted | scenario
  redistributionClass: public | metadataOnly | localOnly | unknown
  schemaVersion: universeAssertion.v1
```

### UniverseRelation

Relation은 assertion을 파괴적으로 dedup한 저장 행이 아니다.

```text
UniverseRelation
  relationId: sha256(subjectId, predicate, objectId)
  subjectId
  predicate
  objectId
  assertionIds[]
  currentStatus
  validFromMin
  validToMax
  strongestEvidenceClass
```

UI는 relation 하나를 엣지로 그린다. Evidence Drawer는 그 아래 assertion timeline을 연다. 현재 `(from, to, type)` dedup은 presentation 단계에서만 허용한다.

## 5. Predicate registry

MVP controlled predicate는 작게 시작한다.

| predicate | 방향 | 허용 근거 | 비고 |
|---|---|---|---|
| `suppliesTo` | supplier -> buyer | direct table A, exact text B | product, amount, ratio optional |
| `sellsTo` | seller -> customer | direct table A, exact text B | supplier와 같은 의미로 섞지 않음 |
| `ownsStakeIn` | owner -> investee | official ownership table A | ownershipPct literal |
| `affiliatedWith` | symmetric view | official group evidence A/B | underlying assertions 방향 보존 |
| `classifiedIn` | entity -> industry | taxonomy or official classification | taxonomyVersion 필수 |
| `filed` | entity -> filing | filing metadata A | availableAt 필수 |
| `reportsMetric` | entity -> observation | filing or standardized finance | graph에는 summary only |
| `peerOf` | symmetric candidate | taxonomy and rule | factual corporate relation 아님 |
| `derivedFrom` | artifact -> source | deterministic provenance | causal edge 아님 |
| `scenarioAffects` | scenario -> entity/metric | scenario only | factual relation과 분리 |

새 predicate는 다음을 모두 가져야 한다.

- owner engine
- canonical direction
- inverse label
- allowed subject/object kinds
- evidence admission rule
- time semantics
- public redistribution rule
- positive 및 hard-negative gold

## 6. 근거 등급

| class | 의미 | 예 | fact layer |
|---|---|---|---|
| A | 구조화 원문과 exact document identity | 공시 표, 공식 지분 데이터, exact financial row | 허용 |
| B | exact text span과 entity resolution | 접수번호와 sectionPath를 가진 문장 | 허용, 단 direct text 표시 |
| C | deterministic 파생 | ratio, score, peer rule | relation fact가 아니라 derived lens |
| D | 후보 및 model inference | title-only match, fuzzy name, LLM 추론 | 기본 숨김 |

`extractionConfidence`는 evidenceClass를 대체하지 않는다. confidence 0.9인 잘못된 entity match를 A급 근거처럼 보이는 문제를 막는다.

## 7. 시간 계약

시간은 최소 세 축이다.

- `eventAt` 또는 `validFrom/validTo`: 현실에서 관계나 관측이 유효한 시간
- `availableAt`: public source에서 알 수 있게 된 시간
- `knowledgeAsOf`: 질문 또는 decision cutoff

필수 인과:

```text
eventAt <= availableAt <= knowledgeAsOf
validFrom <= validTo when both exist
```

정정 공시는 이전 assertion을 삭제하지 않는다. 새 revision assertion을 추가하고 이전 것은 `retracted` 또는 `disputed`로 상태 이동한다. `VintageRef`의 asKnown 및 asOfExact 계약을 재사용한다.

Time Lens는 두 독립 필터를 제공한다.

- "그때 실제로 유효했나": validAt
- "그때 알 수 있었나": knowledgeAsOf

## 8. Observation 재사용

수치 관측은 새 graph 전용 타입을 만들지 않고 `VariableObservation` 의미를 재사용한다.

- `entityId`, `signalId`, `value`, `unit`, `frequency`
- `eventAt`, `availableAt`, `knowledgeAsOf`
- `revisionId`, `VintageRef`, `normalizationRuleHash`

Scene에는 최신값, 변화량, 분포 요약만 node attribute로 들어간다. 전체 시계열은 tableRef와 chart로 읽는다.

## 9. EvidencePointer

`Ref`를 정본으로 사용하고 Universe에는 작은 pointer만 둔다.

```text
EvidencePointer
  refId: Ref.id
  kind: docRef | tableRef | valueRef | dateRef | executionRef
  sourceType: internal | external | llm
  sourceRef: stable citation id
  payloadHash: optional
```

문서 근거 payload는 가능한 경우 다음을 가진다.

- `docId`: DART rceptNo 또는 SEC accessionNo
- `page`, `lineStart`, `lineEnd`, `charOffset`
- `sourcePath` 또는 원문 deep link
- `confidence`, `provenance`
- `period`, `sectionPath`, `dataAsOf`

외부 본문은 기존 Workbench untrusted content 계약을 그대로 적용한다.

## 10. 공개 경계

모든 assertion과 observation은 `redistributionClass`를 가진다.

- `public`: public scene과 share URL 허용
- `metadataOnly`: 제목, 발행일, 링크만 허용
- `localOnly`: public projection에서 fail closed
- `unknown`: public projection에서 fail closed

public exporter는 허용 목록이 아니라 차단 목록을 쓰면 안 된다. source owner가 명시적으로 `public`을 선언한 것만 통과한다.

## 11. ProjectionSpec

```text
ProjectionSpec
  schemaVersion: universeProjection.v1
  projectionId: sha256 canonical spec
  seeds: EntityRef[]
  validAt: ISO date | null
  knowledgeAsOf: ISO datetime | null
  nodeKinds: string[]
  predicates: string[]
  evidencePolicy:
    minimumClass: A | B | C | D
    statuses: string[]
    publicOnly: bool
  limits:
    maxNodes: int <= 500
    maxEdges: int <= 1000
    maxDepth: int <= 2
  lenses:
    capabilityRef: string
    evidenceRefs: string[]
  grouping: industry | stage | market | none
  colorBy: controlled metric id
  sizeBy: controlled metric id
  buildId: string
```

질문 원문은 필수가 아니다. ProjectionSpec은 deterministic UI와 AI 모두 만들 수 있다. 같은 spec과 buildId는 같은 scene을 반환해야 한다.

## 12. 엔진 소유권

| 책임 | owner | 금지 |
|---|---|---|
| raw source fetch | gather | relation 해석 |
| source transform/load | providers | L2 계산 |
| identity 및 lookup | reference | L1.5 형제 import |
| 횡단 projection | scan | 회사 raw 생산 |
| 회사 관계 의미 | industry | analysis, credit 직접 import |
| 재무 계산 | analysis | industry relation 생성 |
| 신용 해석 | credit | graph truth 수정 |
| 거시 및 시나리오 | macro | scenario를 fact로 승격 |
| 가격 및 factor | quant | relation source 생성 |
| 다중 엔진 문장 조립 | story | 직접 숫자 계산 |
| 질문 및 evidence gate | ai | 근거 없는 assertion 승격 |
| scene projection 및 render | UI runtime/surface | HF truth 복제 |

L2 엔진끼리는 import하지 않는다. story, AI 또는 UI sink가 직렬화된 output과 ref를 조합한다.

## 13. 스키마 수명주기

- schema 이름과 version은 artifact와 share URL에 포함한다.
- writer는 current만 쓴다.
- reader는 current와 직전 1개를 읽는다.
- minor는 additive optional field만 허용한다.
- predicate 의미, 방향, ID 형식 변경은 major다.
- major migration은 dual-read, shadow comparison, cutover, old reader 제거 순서다.
- unknown field는 무시할 수 있지만 unknown predicate와 unknown redistributionClass는 fail closed한다.
- assertionId는 canonical payload hash라 migration 후 의미가 달라지면 새 ID가 생겨야 한다.

