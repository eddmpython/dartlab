# 03. 지식, 동일성, 근거, 시간, 재현 계약

## 1. 모델 원칙

단순 node와 edge만으로는 값, 단위, 기간, 출처, 반대 근거, 계산 과정을 표현할 수 없다. Universe는 resource, object, statement, evidence, relation, capability, execution, snapshot을 구분한다.

```text
UniverseResource  원천에서 다시 열 수 있는 주소
UniverseObject    의미 있는 논리 대상
UniverseStatement 근거와 시간 상태를 가진 주장 또는 값
UniverseRelation  object 사이의 typed 연결
UniverseEvidence  원문 안의 정확한 locator
UniverseCapability 기존 callable 능력에 대한 ref
UniverseExecution 실제 실행과 결과 영수증
UniverseSnapshot  원천 revision 묶음과 coverage 상태
```

## 2. 공통 enum

### 2.1 EpistemicClass

| 값 | 의미 | 예 |
|---|---|---|
| `OBSERVED` | 원천에서 직접 읽음 | 공시 금액, 접수일, 가격 |
| `DERIVED` | 동일 입력으로 결정론 계산 | 비율, 재무 분석 axis 결과 |
| `SIMULATED` | 가정 아래 미래·반사실 생성 | scenario path |
| `ASSERTED` | 사람이나 콘텐츠가 주장 | 블로그 문장, 보고서 해석 |
| `INFERRED` | 모델·확률 연결기가 추론 | entity 후보, semantic relation |
| `ASSUMPTION` | 계산에 명시 투입된 전제 | WACC, 성장률, shock |

### 2.2 VerificationState

`DISCOVERED`, `ADDRESSABLE`, `STRUCTURED`, `UNRESOLVED`, `VERIFIED`, `CONFLICTED`, `RETRACTED`, `TOMBSTONED`, `REJECTED`

### 2.3 Visibility

`PUBLIC`, `LOCAL`, `PRIVATE`, `RESTRICTED`, `UNKNOWN`

`UNKNOWN`은 public으로 직렬화할 수 없다.

## 3. UniverseResource

```text
resourceId          stable logical ID
versionId           revision-specific ID
kind                dataset, file, table, media, document, block, row, cell...
label
namespace
sourceRef
payloadLocator
contentSelector
contentDigest
mediaType
schemaRef
byteSize
rowCount
visibility
licenseRef
status
discoveredAt
observedAt
```

규칙:

- `resourceId`는 logical source identity를, `versionId`는 revision과 content digest를 포함한다.
- payload 본문이 아니라 locator를 저장한다.
- rowCount를 알 수 없으면 null과 gapReason을 저장한다. 0으로 바꾸지 않는다.
- license unknown은 공개 가능을 뜻하지 않는다.

## 4. UniverseObject

```text
objectId
versionId
kind
canonicalLabel
aliases[]
identifierRefs[]
resourceRefs[]
epistemicClass
verificationState
validTime
systemTime
visibility
attributes
schemaVersion
```

권장 object kind:

- `MARKET`
- `JURISDICTION`
- `ORGANIZATION`
- `SECURITY`
- `DATASET`
- `FILE`
- `FILING`
- `DOCUMENT`
- `SECTION`
- `TABLE`
- `CONCEPT`
- `ACCOUNT`
- `BLOG_POST`
- `PARAGRAPH`
- `MEDIA`
- `VIDEO_SEGMENT`
- `CAPABILITY`
- `SCENARIO`
- `QUESTION_SESSION`

kind 추가는 schema version bump와 migration test가 필요하다.

## 5. UniverseStatement

중요한 사실과 주장은 edge property가 아니라 statement object다.

```text
statementId
subjectRef
predicate
objectRef?          object relation일 때
value?              scalar, text, array일 때
valueType?
unit?
currency?
scale?
scope               consolidated, separate, segment, market...
period
validTime
systemTime
epistemicClass
verificationState
evidenceRefs[]
derivationRef?
assumptionRefs[]
confidence?
conflictGroupId?
```

불변식:

- `objectRef`와 `value` 중 정확히 하나가 필요하다.
- `OBSERVED`는 evidenceRefs가 1개 이상이다.
- `DERIVED`, `SIMULATED`, `INFERRED`는 derivationRef가 필수다.
- `SIMULATED`는 assumptionRefs가 1개 이상이다.
- confidence가 높아도 `INFERRED`가 `OBSERVED`가 되지 않는다.
- conflict는 한 값을 덮어쓰지 않고 conflictGroup 안에 병존한다.

## 6. UniverseRelation

```text
relationId
type
fromObjectId
toObjectId
direction
validTime
systemTime
epistemicClass
evidenceRefs[]
derivationRef?
weight?
confidence?
```

relation type은 schema registry에 등록한다. 예:

- `FILE_DESCRIBES_ORGANIZATION`
- `FILING_CONTAINS_SECTION`
- `TABLE_CONTAINS_CONCEPT`
- `SECURITY_ISSUED_BY`
- `ORGANIZATION_SUPPLIES`
- `BLOG_ASSERTS_STATEMENT`
- `MEDIA_ILLUSTRATES_BLOCK`
- `CAPABILITY_ACCEPTS_OBJECT`
- `EXECUTION_DERIVED_STATEMENT`

화면에서 가까움, 같은 cluster, 유사 색상은 relation이 아니다.

## 7. UniverseEvidence

```text
evidenceId
sourceRef
sourceRevision
resourceVersionId
locator
selector
contentDigest
retrievedAt
visibility
licenseRef
quoteDigest?
```

### 7.1 locator 종류

| source | locator 필수 요소 |
|---|---|
| HF file | repo, full commit, path, blob/LFS oid |
| Parquet row | file version, business key 또는 row group과 row offset |
| Parquet cell | row locator, column name, schema digest |
| DART | corpCode, rceptNo, document/section/table locator |
| EDGAR | CIK, accession, form, item/section/concept locator |
| blog | git commit, path, AST node path, character range |
| image | content hash path, optional `xywh` region |
| video/audio | media locator, `t=start,end`, transcript segment ref |
| engine result | executionId, output field path, output digest |

selector는 W3C Web Annotation의 text position/quote 개념과 Media Fragments의 공간·시간 구간을 참고하되, 내부 canonical JSON schema로 고정한다.

## 8. Capability와 Execution

### 8.1 UniverseCapability

```text
capabilityId
kind
apiRef
engine?
axis?
targetScope
argsSchemaRef
outputSchemaRef
runtimeBoundary
determinism
resourceClass
costClass
timeoutPolicy
cachePolicy
maturity
visibility
sourceRevision
sourceDigest
```

`apiRef`는 기존 호출 형태를 그대로 보존한다. engine axis는 `dartlab.{engine}("{axis}", args)`다.

### 8.2 UniverseExecution

```text
executionId
capabilityId
snapshotId
targetRefs[]
normalizedArgs
argsDigest
inputRefs[]
assumptionRefs[]
engineVersion
codeRevision
dependencyFingerprint
seed?
startedAt
finishedAt
status
attempt
timeoutMs
cost
resourceUsage
outputRefs[]
outputDigest?
error?
parentExecutionId?
```

status는 `QUEUED`, `RUNNING`, `SUCCEEDED`, `PARTIAL`, `FAILED`, `CANCELLED`, `TIMED_OUT`, `REJECTED`다. `PARTIAL`은 `SUCCEEDED`가 아니다.

## 9. UniverseSnapshot

```text
snapshotId
schemaVersion
sourceRevisionSet
blogRevision
dirtyCaptureRefs[]
mediaCatalogDigest
capabilityCatalogDigest
identityLedgerVersion
conceptMappingVersion
relationTaxonomyVersion
schemaDescriptorSetVersion
controlPlaneHeadId
visibilityScope
previousSnapshotId?
coverageLedger
validationReportRef
replayability       VERIFIED, LOCAL_CAPTURED, NONREPLAYABLE
createdAt
```

`snapshotId = sha256(canonicalJson(rootInputs))`다. `createdAt`처럼 매 실행마다 변하는 값은 rootInputs에서 제외한다. 같은 입력은 byte-identical snapshotId를 만들어야 한다.

clean worktree의 코드 입력은 git commit과 source digest로 고정한다. dirty worktree의 입력은 경로명만 기록하지 않고 당시 byte를 `DARTLAB_UNIVERSE_HOME/objects/sha256`의 content-addressed object로 캡처한 뒤 `dirtyCaptureRefs`에 path, digest, objectRef를 기록한다. 캡처를 거부하거나 object가 사라지면 `NONREPLAYABLE`이며 G1과 G2를 통과할 수 없다. `LOCAL_CAPTURED`는 그 로컬 CAS에서 byte 복원이 검증된 경우에만 허용한다.

`controlPlaneHeadId`는 이 snapshot을 조립할 때 유효했던 append-only 제어 평면 head다. identity, concept mapping, relation taxonomy, schema descriptor, license decision, simulator admission, approval과 invalidation의 정확한 version을 이 head에서 역추적할 수 있어야 한다.

`schemaDescriptorSetVersion`은 capability input/output descriptor와 simulator artifact semantic descriptor의 승인 집합을 함께 고정한다. 둘 중 하나의 source 또는 decoder digest가 바뀌면 새 set version이 필요하며 기존 snapshot을 in-place 갱신하지 않는다.

Snapshot은 다음을 포함하지 않는다.

- 원문 payload copy
- full parquet rows
- renderer 좌표
- model 답변
- 승인 없는 embedding과 index

## 10. 결정론적 ID

ID는 `du:v1:{kind}:{digest}` 형태를 쓴다. digest 입력은 종류별 canonical tuple이다.

| 대상 | logical ID 입력 | version ID 입력 |
|---|---|---|
| HF repo | repo id | repo id + full commit |
| HF file | repo id + normalized path | logical ID + commit + blob oid |
| DART organization | jurisdiction KR + corpCode | logical ID + identifier ledger revision |
| EDGAR organization | jurisdiction US + zero-padded CIK | logical ID + identifier ledger revision |
| security | market namespace + listing identifier + validFrom | logical ID + alias record revision |
| DART filing | corpCode + rceptNo | logical ID + source digest |
| EDGAR filing | CIK + accession | logical ID + source digest |
| blog post | repo + normalized post path | logical ID + git blob digest |
| blog block | post ID + heading lineage + stable block key | logical ID + content digest |
| media | sha256 object digest | 동일 |
| engine capability | public apiRef + axis | logical ID + source digest |
| execution | capability ID + snapshot ID + args digest + target refs + seed | 동일 |

경로는 `/`, Unicode NFC, case policy를 source namespace별로 canonicalize한다. canonical JSON은 key 정렬, NaN 금지, float normalization, timezone UTC 규칙을 쓴다.

## 11. 행과 셀 ID

모든 행을 영구 object로 선생성하지 않는다.

### 11.1 business key가 있을 때

```text
rowId = hash(fileLogicalId, tableId, canonicalBusinessKey)
cellId = hash(rowId, canonicalColumnName)
```

### 11.2 business key가 없을 때

```text
rowVersionId = hash(fileVersionId, rowGroup, rowOffset)
cellVersionId = hash(rowVersionId, columnName)
stability = REVISION_SCOPED
```

revision-scoped locator를 영구 logical identity로 속이지 않는다. 다음 revision의 같은 행과 연결하려면 explicit match relation과 confidence가 필요하다.

## 12. 기업과 개념 동일성

### 12.1 기업

- 한국 법인은 corpCode가 canonical anchor다.
- stockCode는 validFrom/validTo를 가진 security alias다.
- 미국 법인은 CIK가 canonical anchor다.
- ticker는 validFrom/validTo를 가진 security alias다.
- 이름만 같은 기업은 merge하지 않는다.
- cross-listed 또는 법적으로 동일한 조직의 corpCode와 CIK 연결은 authoritative identifier evidence가 있을 때만 `SAME_LEGAL_ENTITY`로 승인한다.
- 모회사, 자회사, 합병 전후 법인은 `RELATED`, `SUCCEEDED_BY`, `CONTROLLED_BY` 관계이지 자동 SAME_AS가 아니다.

### 12.2 DART와 EDGAR 계정

K-IFRS와 US-GAAP concept를 한 계정으로 덮어쓰지 않는다.

```text
sourceConcept
canonicalConceptCandidate
mappingType       exact, broader, narrower, transformed, unresolved
scope
unitRule
signRule
periodRule
evidence
mappingVersion
```

충돌하는 값은 source statement 둘을 보존하고 mapping statement로 연결한다. canonical query는 둘 중 하나를 몰래 선택하지 않고 source, accounting basis, reconciliation gap을 반환한다.

## 13. alias, merge, split 정책

### 13.1 alias

alias record는 `namespace`, `value`, `validFrom`, `validTo`, `sourceEvidence`, `confidence`를 가진다. 현재 ticker나 이름을 과거 전체에 소급하지 않는다.

### 13.2 merge

merge 조건:

- canonical identifier가 동일하거나
- authoritative crosswalk evidence가 있고
- conflicting legal identity가 없고
- merge rule version이 기록되고
- 해당 merge decision이 Universe control plane에 승인 상태로 append됨

자동 merge confidence가 threshold 미만이면 `UNRESOLVED_CLUSTER`로 둔다. 사람이 승인한 merge도 approver와 evidence ref를 남긴다.

### 13.3 split

오병합이 발견되면 과거 object를 지우지 않는다.

- old object를 `RETRACTED`로 표시
- new objects 생성
- `SPLIT_FROM` relation 생성
- 영향을 받은 statement와 execution을 invalidation ledger에 연결
- 이전 snapshot은 그대로 재현
- 새 snapshot부터 새 identity 적용

### 13.4 ControlDecision

merge, split, concept mapping, relation taxonomy, schema descriptor와 license 판정은 markdown 메모가 아니라 durable decision record다.

```text
decisionId
decisionKind
subjectRefs[]
inputEvidenceRefs[]
ruleVersion
payloadDigest
status             PROPOSED, APPROVED, REJECTED, SUPERSEDED
reviewer
reasonCode
previousDecisionId?
createdAt
approvedAt?
```

결정은 `DARTLAB_UNIVERSE_HOME/control.sqlite`에 append-only로 기록하고 수정 대신 successor로 supersede한다. query, execution, projection은 `APPROVED` decision만 읽는다. 제어 평면 database와 referenced object의 digest가 맞지 않으면 새 snapshot 생성과 execution admission을 차단한다.

## 14. 시간 모델

하나의 `date`로 모든 시간을 표현하지 않는다.

| 필드 | 의미 |
|---|---|
| `validFrom`, `validTo` | 현실에서 값·관계가 유효한 시간 |
| `periodStart`, `periodEnd` | 재무·시계열 측정 기간 |
| `filedAt` | 공시가 제출된 시간 |
| `publishedAt` | 콘텐츠가 발행된 시간 |
| `knownAt` | 해당 정보가 시스템 사용자에게 알려질 수 있었던 최초 시간 |
| `observedAt` | adapter가 실제 관측한 시간 |
| `ingestedAt` | Universe run이 catalog에 포함한 시간 |
| `retractedAt` | 철회·삭제 확인 시간 |

PIT query는 `validTime`과 `knownAt`을 모두 필터한다. period가 과거라고 당시 알 수 있었던 정보인 것은 아니다.

## 15. 수정, 철회, 재작성, 삭제

- 원천 내용 수정: 같은 logical resource, 새 versionId
- 정정 공시: old statement 유지, new statement와 `CORRECTS` relation
- 철회: statement `RETRACTED`, 이유 evidence 연결
- blog rewrite: post logical ID 유지, block version 갱신, 삭제 block tombstone
- HF file delete: logical file tombstone, 과거 version locator 유지
- capability axis 제거: capability tombstone, 과거 execution 재현 가능
- source가 과거 revision을 더 이상 제공하지 않음: `SOURCE_HISTORY_UNAVAILABLE`, 재현 가능하다고 주장 금지

## 16. 근거와 파생 계보

W3C PROV의 Entity, Activity, Agent 개념을 최소 호환 기준으로 삼는다.

```text
source resource
  -> used by execution
  -> generated output resource
  -> supports statement
  -> rendered by projection
```

모든 verified statement에 대해 다음 path가 끊기지 않아야 한다.

```text
statement
  -> evidence or derivation
  -> resource version or execution
  -> source revision and locator
  -> original payload segment
```

execution receipt와 simulator admission receipt는 같은 durable 제어 평면에 저장하되, 큰 output byte는 CAS object로 분리하고 receipt가 digest와 locator를 가리킨다. receipt가 가리키는 output이 없거나 digest가 다르면 성공 상태를 반환하지 않고 `INVALIDATED_OUTPUT`으로 기록한다. 삭제는 허용하지 않고 invalidation 또는 successor receipt를 append한다.

## 17. 재현성 인수 기준

- 동일 root inputs의 snapshotId 일치율 100%
- logical ID collision 0
- deterministic engine replay output digest 일치율 100%
- non-deterministic capability는 seed 또는 허용 오차 계약 100%
- verified statement evidence/derivation coverage 100%
- sourceRevision 누락 0
- parameter와 target ref 누락 0
- `SIMULATED` assumption coverage 100%
- temporal query future leakage 0
- identity auto-merge false positive 0, 불확실 항목은 unresolved
- split 후 과거 snapshot replay 성공
- clean commit snapshot과 dirty local capture snapshot의 byte replay 성공률 100%
- `NONREPLAYABLE` snapshot의 G1, G2 통과 0
- control plane head에서 identity, mapping, taxonomy, schema, license, receipt decision 역추적률 100%
- control.sqlite 손상, CAS object 누락, digest mismatch fixture의 admission 차단률 100%
- supersede 전 snapshot replay와 supersede 후 새 snapshot 판정이 각각 보존됨
