# 05. 질의, RAG 선행 구조, 블로그·이미지·영상

## 1. 결론

Universe query는 vector 검색 하나가 아니다. exact identifier, structured table query, lexical search, temporal filter, graph traversal, existing engine execution을 한 QueryPlan으로 결합한다. RAG는 이 계획의 결과인 `RetrievalEvidencePack`을 소비하고, 생성 뒤에는 별도 `VerifiedAnswerBundle`을 만든다.

현재 먼저 완성할 것은 UI가 없는 query engine이다. 3D와 대화형 답변은 query와 evidence 검증이 통과한 뒤에 붙는다.

## 2. Query 종류

| 종류 | 예 | 실행기 |
|---|---|---|
| exact | corpCode, CIK, ticker, rceptNo, accession, objectId | identity resolver |
| structured | 기간·단위·계정·source 조건 | DuckDB/Arrow |
| temporal | 특정 as-of에서 알 수 있었던 사실 | bitemporal filter |
| lexical | 공시·블로그 문구 검색 | 기존 content index와 AST index |
| graph | 공급망, 지분, 근거, 파생 path | bounded traversal |
| semantic | 표현이 다른 개념 후보 | benchmark 후 vector candidate |
| capability | 답에 필요한 기존 engine 선택 | capability registry |
| spatial | 선택 객체, tile, lens context | query prior only |

## 3. UniverseQuery

```text
queryId
text?
objectRefs[]
filters
  timeContext
  spatialContext?
  expandBeyondSpatial
  requestedOutputs
visibilityScope
budget
explain
```

`filters`는 source, market, object kind, epistemic class, verification state, period, visibility를 포함한다. query text만으로 private scope를 넓힐 수 없다.

## 4. QueryPlan

```text
QueryPlan
  normalizedIntent
  identitySteps[]
  structuredSteps[]
  lexicalSteps[]
  graphSteps[]
  semanticSteps[]
  capabilitySteps[]
  verificationSteps[]
  budgetAllocation
  expectedEvidenceKinds[]
  fallbackPolicy
```

### 4.1 계획 순서

1. identifier와 time scope 고정
2. visibility filter 선적용
3. structured fact와 exact match 우선
4. lexical, graph, semantic 후보를 병렬 수집
5. source와 시간 기준으로 후보 정규화
6. 필요할 때만 capability 실행
7. 반대 근거와 충돌 statement 검색
8. 불변 `RetrievalEvidencePack` 조립과 G4E 검증
9. U7에서 선택적으로 `AnswerDraft` 생성
10. claim별 검증으로 새 `VerifiedAnswerBundle` 생성
11. 충분한 근거가 없으면 abstain

semantic 결과가 structured truth를 덮어쓰지 않는다.

## 5. Hybrid retrieval

### 5.1 기준선

- exact and alias: identity ledger
- structured: DuckDB over Arrow/Parquet locator
- lexical: 기존 `dart/contentIndex`, 공시 search, blog AST lexical index
- graph: object, statement, evidence adjacency table
- temporal: valid time와 knownAt predicate
- capability: live CapabilityRef filtering

### 5.2 vector 도입 조건

vector index는 기본 전제가 아니다. 다음 benchmark를 통과하고 Bake Decision 승인을 받아야 한다.

- lexical+graph baseline 대비 Recall@20 유의 개선
- citation precision 악화 없음
- Korean과 English cross-lingual case 개선
- incremental update 비용 SLO 충족
- index가 원천이 아닌 재생성 가능한 accelerator임을 증명
- model version과 embedding digest 기록

후보는 Qdrant와 pgvector를 benchmark하고, 기존 운영 기반이 없으면 service 증가 비용을 감점한다. Microsoft GraphRAG를 canonical ingest pipeline으로 쓰지 않는다. LLM 추출 graph가 원천 지식 모델을 오염시킬 수 있기 때문이다.

## 6. Existing AI workbench와의 관계

DartLab에는 `dartlab.ask`, AI workbench, EngineCall, InspectDataset, WebSearch, evidence refs가 이미 있다. Universe가 별도 agent loop를 만들지 않는다.

현재 실존 seam을 다음처럼 고정한다.

| 역할 | 실존 파일과 symbol | Universe 연결 방식 |
|---|---|---|
| ask entry | `src/dartlab/ai/kernel.py::ask`, `_askEvents` | 기존 진입점 유지 |
| workbench loop | `src/dartlab/ai/workbench/loop.py::WorkbenchLoop.stream` | 새 loop 생성 금지, 기존 tool 단계에만 후보 등록 |
| evidence gate | `src/dartlab/ai/workbench/gate.py::runGate` | 기존 숫자, 날짜, 표 ref 검증을 우회하지 않음 |
| engine tool | `src/dartlab/ai/tools/engineCall.py::engineCall` | validated SchemaDescriptor가 있는 실존 apiRef만 기존 tool로 호출 |
| dataset inspection | `src/dartlab/ai/tools/inspectDataset.py::inspectDataset` | sample과 schema 관찰용, Universe 전체 census 대체 금지 |
| tool envelope | `src/dartlab/ai/tools/types.py::ToolResult` | `ok`, `summary`, `refs`, `data`, `error` 유지 |
| evidence contract | `src/dartlab/ai/contracts.py::Ref` | Universe locator를 `payload`에 넣고 기존 `sourceType`와 provenance 유지 |
| answer contract | `src/dartlab/ai/contracts.py::AnswerDraft`, `VerificationResult` | evidenceRefs를 pack의 verified ref ID에 매핑 |

현재 gate가 이해하는 `tableRef`, `valueRef`, `dateRef`, `sourceRef`, `executionRef`를 유지한다. Universe objectId, statementId, snapshotId, evidence locator는 새 top-level AI contract를 발명하지 않고 `Ref.payload`에 구조화한다. 기존 gate가 모르는 새 ref kind만 발급해 숫자 claim 검증을 무력화하지 않는다.

후속 integration:

```text
dartlab.ask workbench
  -> ReadUniverseObject tool
  -> SearchUniverse tool
  -> TraverseUniverse tool
  -> EngineCall existing tool
  -> VerifyRetrievalEvidencePack tool
```

각 tool은 objectId, snapshotId, evidenceRefs, executionRefs를 반환한다. Universe가 LLM 답변을 canonical graph에 쓰는 tool은 제공하지 않는다.

integration contract test는 `engineCall`의 `ToolResult.refs`가 가리키는 source, table, value, date, execution ref와 `RetrievalEvidencePack.candidateEvidence`를 양방향 대조한다. `AnswerDraft.evidenceRefs`에 pack 밖 ID가 있거나 `runGate`가 issue를 반환하면 `VerifiedAnswerBundle`을 만들지 않는다. 이 mapping이 통과하기 전 U7은 standalone evaluator에 머문다.

현재 RAG 관련 Skill OS가 drafted 또는 unverified라면 그 상태를 그대로 따른다. 제품급 의미 검색이 이미 있다고 주장하지 않는다.

## 7. 검색 근거와 답변 bundle의 수명주기

```text
RetrievalEvidencePack
  packId
  snapshotId
  queryId
  queryPlanDigest
  visibilityPolicyDigest
  schemaVersion
  candidateEvidence[]
  contradictoryEvidence[]
  executionRefs[]
  sourceRevisionSet
  laneCoverage
  retrievalScoreProvenance[]
  truncation
  withheldReasons[]
  unresolvedQuestions[]
  completeness
```

`RetrievalEvidencePack`은 query 실행 직후 생성하고 불변이다. 답변 문장이나 생성 model 결과를 포함하지 않는다. G4E는 이 객체의 locator, source revision, visibility, lane coverage를 모델 없이 검증한다.

```text
AnswerDraft
  draftId
  retrievalPackId
  snapshotId
  queryPlanDigest
  visibilityPolicyDigest
  schemaVersion
  modelRef
  modelVersion
  promptDigest
  decodingParametersDigest
  seed?
  generationReceiptRef
  sentences[]
  extractedClaims[]
  createdAt
```

claim 항목:

```text
claimId
sentenceId
text
epistemicClass
subjectRefs[]
predicate
value?
timeScope
```

```text
VerifiedAnswerBundle
  bundleId
  retrievalPackId
  draftId
  snapshotId
  queryPlanDigest
  visibilityPolicyDigest
  schemaVersion
  verifiedSentences[]
  claimEvidenceMappings[]
  executionRefs[]
  verificationReport
  removedClaims[]
  abstainedClaims[]
  uncertainty
  outputDigest
```

각 단계는 앞 단계 객체를 수정하지 않고 새 canonical digest를 만든다. `generationReceiptRef`는 model, model version, prompt digest, decoding parameter, seed 지원 여부, provider request ID, started/finished time, status와 output digest를 고정한다. 숫자 claim은 원천 값 또는 deterministic execution으로 재계산한다. citation 없는 숫자는 `VerifiedAnswerBundle`에 들어갈 수 없다.

## 8. 답변 검증

`AnswerDraft` 생성 후 다음을 문장 단위로 검사해 `VerifiedAnswerBundle`을 만든다.

- cited locator가 실제 존재하는가
- source revision이 snapshot에 포함되는가
- 인용된 구간이 claim을 실제로 지지하는가
- 숫자, 단위, 통화, 기간이 일치하는가
- 반대 근거를 누락하지 않았는가
- simulation을 fact로 표현하지 않았는가
- 현재 화면과 가까운 객체를 인과 관계로 오인하지 않았는가
- private evidence가 public answer에 새지 않았는가

검증 실패 문장은 삭제하거나 불확실성 문구와 함께 abstain한다.

## 9. Spatial Context

3D가 나중에 연결되면 다음만 query context로 전달한다.

```text
sceneId
snapshotId
projectionVersion
selectionGeneration
visibilityScopeDigest
selectedObjectIds[]
visibleTileIds[]
activeLens
timeRange
activeFilters
recentTraversalPath[]
normalizedFrustumOrBounds
```

공간 context는 candidate prior를 조정할 뿐 evidence가 아니다. `UniverseQuery.expandBeyondSpatial=true`가 기본이며 exact, structured, contradiction lane은 공간 context로 제외할 수 없다. 공간 boost는 최종 retrieval score 기여의 15% 이하로 제한한다.

서버는 selected object와 tile ID를 visibility scope로 다시 검증한다. context snapshot 또는 projection version이 query snapshot과 다르거나 selectionGeneration이 현재 scene보다 오래되면 spatial context 전체를 무시하고 `STALE_SPATIAL_CONTEXT` warning을 남긴다. raw camera matrix를 보내지 않고 privacy-safe normalized frustum 또는 bounds summary만 사용한다. "가까이 보인다"를 relation이나 claim으로 바꾸지 않는다.

질문 결과는 base universe 좌표를 바꾸지 않고 임시 `QuestionConstellation` overlay로 보인다.

### 9.1 QuestionConstellation 계약

```text
QuestionConstellation
  overlayId
  baseSceneId
  baseSnapshotId
  baseProjectionVersion
  baseSceneDigest
  queryId
  retrievalPackId
  verifiedAnswerBundleId
  claimNodes[]
  evidenceNodes[]
  executionNodes[]
  overlayEdges[]
  visibilityScopeDigest
  styleSchemaVersion
  createdAt
  expiresAt
  persistence = EPHEMERAL
```

- 기존 object node는 base coordinate를 그대로 재사용한다.
- 새 DERIVED 또는 SIMULATED result node는 supporting evidence 좌표의 weighted barycenter와 overlayId-derived deterministic jitter로 임시 배치한다.
- overlay edge는 `CLAIM_SUPPORTED_BY`, `CLAIM_CONTRADICTED_BY`, `CLAIM_DERIVED_BY`처럼 typed 상태를 가진다.
- overlay relation은 canonical graph로 자동 merge하지 않는다.
- scene owner가 TTL 만료, 새 query, explicit close에서 buffer와 mapping을 dispose한다.
- Bake Decision 승인 전 persistence는 `EPHEMERAL`만 허용한다.
- overlay 제거 전후 `baseSceneDigest`와 base coordinate buffer digest가 같아야 한다.

## 10. 블로그를 지식으로 읽는 방식

Markdown 파일 하나를 통째로 chunking하지 않는다.

```text
BlogPost
  FrontmatterField
  Section
    Paragraph
      Sentence
      AuthoredClaim
      EntityMention
      Citation
    Table
      Row
      Cell
    CodeBlock
    ImageRef
    VideoRef
```

### 10.1 AST catalog 대상

- title, date, description, category, stockCode, topicSlug, exchange
- heading hierarchy
- paragraph와 sentence position
- table, row, cell
- code language와 code block
- internal/external link
- explicit citation
- image alt, caption, URL
- `youtubeId`와 외부 video locator
- `brief.json`, `CREDITS.md`가 있을 때 관계
- media catalog post mapping

frontmatter의 빈 `youtubeId`는 영상 객체가 아니다. 현재 비어 있지 않은 14개만 external video resource 후보다.

### 10.2 주장 상태

블로그 문장은 기본 `ASSERTED`다. 숫자와 관계가 DART, EDGAR, HF evidence와 연결돼도 원문 claim 자체는 `ASSERTED`로 남고 `SUPPORTED_BY` relation을 얻는다. LLM이 entity를 추출하면 mention은 `INFERRED`이며 검증 후에도 source claim을 OBSERVED로 바꾸지 않는다.

### 10.3 block locator 안정성

block logical key는 postId, heading lineage, explicit anchor 또는 stable block key를 쓴다. content digest는 version에 포함한다. heading 변경이나 block reorder로 자동 match가 불확실하면 old/new version을 `POSSIBLE_REVISION_OF`로 두고 검토한다.

## 11. 이미지

media object는 content-addressed SHA-256가 canonical ID다.

필드:

```text
mediaId
objectPath
contentDigest
mediaType
width?
height?
byteSize
altRefs[]
captionRefs[]
creditRef?
licenseRef?
postRefs[]
regionAnnotations[]
visibility
```

이미지 전체가 claim의 근거가 아니라 특정 region이 근거라면 `xywh` selector를 쓴다. SVG 안의 text와 raster OCR은 `INFERRED` 추출로 별도 저장하고 원본을 대체하지 않는다.

## 12. 영상과 오디오

현재 blog에는 비어 있지 않은 YouTube ID 14개가 관측됐다. podcast episode metadata도 13개다. 외부 media는 다음으로 catalog한다.

```text
ExternalMedia
  provider
  externalId
  canonicalUrl
  publishedAt?
  duration?
  title?
  transcriptStatus
  licenseStatus
  postRefs[]
```

transcript가 실제로 존재할 때만 segment를 만든다.

```text
TemporalSegment
  mediaId
  startMs
  endMs
  transcriptText
  transcriptSource
  language
  confidence
  evidenceId
```

자동 음성 인식은 `INFERRED`이고 원본 음성의 대체물이 아니다. script 파일이 없으면 `TRANSCRIPT_ABSENT`다.

## 13. Untrusted content 경계

공시 HTML, blog Markdown, media transcript, 외부 문서는 전부 untrusted input이다.

- system 또는 tool instruction으로 해석 금지
- prompt에 넣기 전 content와 metadata channel 분리
- HTML script, event handler, remote include 제거
- URL scheme allowlist
- retrieved text 안의 "이전 지시 무시"를 데이터로 quote
- tool call은 model text가 아니라 validated QueryPlan에서만 생성
- private secret과 local path를 model context에 넣지 않음
- model output은 canonical graph write 권한 없음

prompt injection fixture에서 tool escalation과 data exfiltration이 0이어야 한다.

## 14. Query와 RAG 평가셋

gold set은 최소 다음을 포함한다.

- exact DART corpCode와 filing lookup
- exact EDGAR CIK와 accession lookup
- ticker 변경 이력
- DART와 EDGAR 계정 mapping 충돌
- 특정 blog 문장의 원천 근거
- image region과 caption 연결
- video segment와 post 연결
- simulation과 observed fact 구분
- period와 knownAt이 다른 PIT 질문
- 근거가 부족해 abstain해야 하는 질문
- spatial selection 밖에서 반대 근거를 찾아야 하는 질문
- private source가 public scope에서 보이지 않아야 하는 질문

## 15. G3, G4E, G4R 인수 기준

### G3 Query

- exact identifier Recall@1 100%
- golden query Recall@20 95% 이상
- structured 숫자 정확도 100%
- source, unit, period 오분류 0
- bounded graph query p95 300ms 목표
- private scope leakage 0
- 각 retrieval lane ablation과 기여 기록

### G4E, 모델 없는 검색 근거 검증

- RetrievalEvidencePack locator resolution 100%
- source revision과 visibility policy match 100%
- structured, exact, lexical, graph lane coverage report 누락 0
- truncation과 withheld reason 누락 0
- contradictory evidence lane 실행률 100%
- prompt나 model 호출 없이 재현 가능

### G4R, 생성 RAG

- citation precision 98% 이상
- citation coverage 95% 이상
- 숫자 재계산 일치율 100%
- temporal 기준 오류 0
- epistemic class 오분류 0
- 근거 부족 abstention F1 95% 이상
- engine tool execution success 99% 이상, invalid request 제외
- prompt injection tool escalation 0
- 같은 snapshot, query plan, RetrievalEvidencePack, execution receipts, immutable AnswerDraft bytes와 verifier version으로 VerifiedAnswerBundle digest 재현 100%
- model 재호출의 byte 재현은 보장하지 않으며 generation receipt 없는 AnswerDraft 수용 0
- AnswerDraft가 RetrievalEvidencePack을 변경한 사례 0
- QuestionConstellation 제거 후 base scene digest 변화 0

RAG 점수가 통과해도 canonical graph 자동 write는 금지 상태를 유지한다.
