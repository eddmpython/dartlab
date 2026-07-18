# 04. Capability, 엔진 실행, 시뮬레이터 격리

## 1. 전체의 의미

"엔진별 호출 가능한 모든 데이터"는 모든 axis를 전 종목에 미리 실행해 결과를 쌓는다는 뜻이 아니다. 모든 실존 callable을 발견하고, 실제 입력·출력·안정성·비용·권한을 catalog하며, 요청 시 재현 가능한 방식으로 호출할 수 있다는 뜻이다.

미리 전수 실행하면 다음 문제가 생긴다.

- 원천 revision과 엔진 code가 바뀔 때 결과 폭증
- runtime SSOT 위반과 별도 데이터 원천 생성
- 수백 axis 곱하기 전 종목의 비용 폭발
- 결손과 실패를 오래된 성공 결과로 위장
- simulation과 observation 혼합

따라서 capability는 영구 catalog 대상이고 execution은 on-demand 또는 명시된 validation cohort에서만 생성한다.

## 2. 현재 capability authority

| authority | 역할 | 현재 관측 |
|---|---|---:|
| `dartlab.capabilities()` | 전체 공개 surface와 설명 live builder | 226 |
| engine registry | 실제 axis dispatch key | 147 |
| `Company` facade | 단일 기업 공개 method | 63 capability key |
| root callable presence | 실제 top-level callable 검증 | runtime 검사 |
| Skill OS | 올바른 사용 절차와 안정성 설명 | 보조 authority |

숫자는 snapshot 관측값이고 테스트 상수가 아니다. 매 census에서 union을 다시 계산한다.

## 3. Capability reconciliation

각 candidate에 다음 검사를 적용한다.

```text
documented = key in dartlab.capabilities()
registered = axis in actual registry
callable = public facade exists and is callable
skillLinked = capabilityRef exists in Skill OS
schemaComplete = args and output schema are machine-valid
```

상태:

- `ACTIVE`: documented, registered, callable, schema complete
- `CALLABLE_UNMIRRORED`: 실제 호출 가능하나 capability mirror 누락
- `MIRRORED_MISSING`: 설명만 있고 callable 또는 registry 없음
- `HIDDEN_PREVIEW`: callable이지만 공개 안정성 없음
- `SCHEMA_INCOMPLETE`: 입력 또는 출력 계약 미완
- `DEPRECATED`: successor가 명시된 과거 surface
- `REJECTED_INTERNAL`: 내부 helper라 public 실행 금지

현재 analysis 22축이 capability prefix 목록에서 누락되는 drift와 `simulate`의 preview 상태는 그대로 ledger에 남긴다. Universe가 이를 숨기거나 안정 공개 API로 승격하지 않는다.

### 3.1 Schema authority와 closure

현재 `loadCapabilities()` 관측에서는 226개 중 `argsSchema` 0개, `outputSchema` 0개, `returnSchema` 27개, declared 125개다. 따라서 capability를 발견했다는 사실과 안전하게 실행할 수 있다는 주장은 분리한다.

schema authority 우선순위:

1. 실제 public callable의 Python signature와 type hint
2. live capability record와 docstring
3. 기존 Skill OS의 사용 계약
4. 위 근거로 만든 Universe-local `SchemaDescriptor`

```text
SchemaDescriptor
  descriptorId
  apiRef
  axis?
  sourceRevision
  sourceDigest
  extractionEvidenceRefs[]
  argsSchema
  outputSchema
  validationCorpusRef
  validationReportRef
  reviewer
  version
  status               CANDIDATE, VALIDATED, STALE, REJECTED, SUPERSEDED
```

4번은 기존 API를 만들거나 바꾸는 선언이 아니다. 실존 callable에 대해 1번부터 3번까지의 근거를 기계 계약으로 정규화한 Universe 전용 제어 평면 record다. docstring만으로 type, required, unit, enum, output shape가 확정되지 않으면 추측하지 않고 `SCHEMA_INCOMPLETE`로 둔다.

closure workflow:

1. source digest를 고정하고 signature, type hint, capability record, docstring, Skill OS를 추출한다.
2. args field는 실제 signature parameter 또는 문서화되고 sandbox에서 관측된 `**kwargs` key만 허용한다.
3. output field는 validation cohort에서 실제 관측됐거나 source contract가 optional로 명시한 field만 허용한다.
4. valid, invalid, boundary input corpus와 output mutation test를 실행한다.
5. domain reviewer가 evidence ref와 report digest를 확인한 뒤 `VALIDATED` decision을 append한다.
6. source digest가 바뀌면 descriptor를 자동 `STALE`로 내려 execution admission을 다시 닫는다.

descriptor가 기존 callable보다 더 넓은 arg, axis, output guarantee를 선언하면 `SCHEMA_WIDENING`으로 거절한다. 관측 cohort 밖 shape는 `additionalProperties`로 묵인하지 않고 explicit union, optional 또는 incomplete 상태로 모델링한다.

두 coverage를 별도로 계산한다.

```text
catalogCoverage = classifiedCandidates / discoveredCandidates
executionReadiness = validatedSchemaCallable / eligibleCallable
```

`eligibleCallable`은 schema 상태를 보기 전에 결정한다. 실존 public facade가 callable이고, 내부 helper 또는 deprecated surface가 아니며, 지원 runtimeBoundary와 권한 정책이 정해진 항목이다. `SCHEMA_INCOMPLETE`를 이유로 분모에서 빼지 않는다. eligible 항목 중 descriptor가 `VALIDATED`가 아니면 실행 admission은 닫히고 G2도 실패한다. explicit blocked 상태는 catalog reconciliation은 종결하지만 executionReadiness 분자를 늘리지 않는다. G2는 catalogCoverage와 executionReadiness 모두 100%, blocked eligible 0이어야 하므로 schema가 끝나지 않은 엔진을 숨기거나 실행 가능하다고 과장할 수 없다.

## 4. CapabilityRef 계약

```text
capabilityId
kind
apiRef
engine
axis
targetScope
argsSchema
outputSchema
runtimeBoundary
determinism
seedPolicy
costClass
memoryClass
timeoutMs
retryPolicy
cachePolicy
concurrencyClass
maturity
visibility
sourceRevision
sourceDigest
status
gapReasons[]
```

### 4.1 호출 형태

axis engine은 오직 기존 facade를 쓴다.

```python
dartlab.analysis("현금흐름", target="005930")
dartlab.scan("profitability", ...)
dartlab.gather("krx", ...)
```

문서 예시는 형태를 설명할 뿐 각 args가 현재 schema에서 유효하다는 보장이 아니다. 실제 argsSchema validation을 통과한 호출만 실행한다. 내부 module function을 우회 호출하지 않는다.

### 4.2 runtimeBoundary

- `PUBLIC_BROWSER_READ`: public HF payload를 읽는 순수 조회
- `LOCAL_PYTHON`: 로컬 Python과 공개 facade 필요
- `LOCAL_SECRET`: API key 또는 private data 필요
- `REMOTE_COMPUTE`: 미래 인증 service 필요
- `PREVIEW_LOCAL`: 안정 계약 전 local-only

browser에서 `LOCAL_PYTHON`, `LOCAL_SECRET`, `PREVIEW_LOCAL`을 실행하지 않는다.

## 5. ExecutionRequest

```text
requestId
capabilityId
snapshotId
targetRefs[]
args
assumptionRefs[]
visibilityScope
budget
priority
deadline
idempotencyKey
requestedBy
```

admission은 다음 순서다.

1. capability 존재와 상태 확인
2. visibility와 caller 권한 확인
3. args schema validation
4. target identity resolution
5. source snapshot freshness 확인
6. budget과 concurrency admission
7. idempotency lookup
8. queue 또는 reject

거절도 ExecutionReceipt를 남긴다.

## 6. 실행 오케스트레이션

### 6.1 job 상태

```text
QUEUED -> ADMITTED -> RUNNING -> SUCCEEDED
                           |-> PARTIAL
                           |-> FAILED
                           |-> TIMED_OUT
                           |-> CANCELLED
QUEUED/ADMITTED ---------->|-> REJECTED
```

### 6.2 budget

```text
maxWallMs
maxCpuMs
maxRssBytes
maxNetworkBytes
maxRows
maxOutputBytes
maxToolCalls
maxRetries
```

budget 초과는 silent truncation이 아니라 `PARTIAL` 또는 `REJECTED_BUDGET`이다. 부분 output은 `truncated=true`, returnedRows, estimatedTotalRows, continuation을 가진다.

### 6.3 timeout과 cancel

- cooperative cancel token을 먼저 전달
- 취소 불가능한 CPU 작업은 격리 process에서 실행
- timeout 후 process와 임시 파일 정리
- client disconnect와 server cancel을 구분
- cancel된 output을 cache하지 않음
- long job은 progress event와 heartbeat를 제공

### 6.4 retry

retry 가능한 오류만 지수 backoff와 jitter를 사용한다.

| 오류 | retry |
|---|---|
| rate limit, transient network | 예, Retry-After 우선 |
| timeout | idempotent이고 budget 잔여 시 1회 |
| schema mismatch | 아니오 |
| access denied | 아니오 |
| invalid args | 아니오 |
| deterministic calculation error | 아니오, defect ledger |

모든 attempt는 같은 parent request 아래 별도 receipt를 가진다.

### 6.5 idempotency

```text
idempotencyKey = hash(capabilityId, snapshotId, targetRefs,
                      normalizedArgs, assumptionRefs, seed,
                      engineVersion)
```

동일 key의 완료 execution이 있고 source visibility가 맞으면 replay ref를 반환할 수 있다. non-deterministic execution은 seed와 model version이 없으면 재사용 금지다.

### 6.6 concurrency

capability를 `LIGHT_IO`, `HEAVY_IO`, `CPU`, `MEMORY_HEAVY`, `SECRET_BOUND`, `SIMULATION`으로 분리해 lane별 semaphore를 둔다. 하나의 대형 scan이 interactive object query를 굶기지 못하게 queue를 분리한다.

### 6.7 write isolation

엔진이 기존 data, lineage, cache 또는 사용자 경로를 쓰지 못하도록 모든 실행은 격리 worker process에서만 수행한다.

```text
DARTLAB_DATA_DIR      = workerRoot/data
DARTLAB_LINEAGE_DIR   = workerRoot/lineage
HOME                  = workerRoot/home
XDG_CACHE_HOME        = workerRoot/cache
TEMP, TMP             = workerRoot/tmp
UNIVERSE_OUTPUT_DIR   = workerRoot/output
```

attempts 단계는 Python audit hook으로 `open`, rename, delete, mkdir, subprocess와 socket event를 기록하고 write allowlist 밖의 동작을 즉시 거부한다. native library나 subprocess가 필요한 capability는 OS write sandbox가 증명될 때까지 `EXECUTION_BLOCKED_SANDBOX`다. 실행 전후 repo, project `data/`, configured lineage root와 사용자 보호 경로의 digest를 비교하고 변화가 하나라도 있으면 output을 폐기하고 defect로 기록한다. worker가 성공한 뒤에는 승인된 output만 digest를 계산해 control-plane CAS로 원자적 commit하며 나머지 workerRoot는 제거한다.

## 7. ExecutionReceipt

```text
executionId
requestId
parentExecutionId?
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
budgetUsed
sourceReadStats
outputRefs[]
outputSchemaRef
outputDigest?
gapReasons[]
error?
```

숫자형 output은 dtype, unit, scale, currency, period를 잃지 않는다. DataFrame을 JSON string으로 뭉개는 방식을 bulk 경계로 쓰지 않는다. local service가 나중에 승인되면 Arrow IPC stream을 기본 후보로 benchmark한다.

receipt는 process memory나 로그가 정본이 아니다. `control.sqlite` transaction에서 `(idempotencyKey, attempt)` unique constraint로 append하고, 큰 output은 `objects/sha256`에 immutable object로 먼저 fsync한 뒤 locator와 digest를 receipt에 연결한다. crash가 object commit 뒤 receipt commit 전에 발생하면 orphan collector가 참조 없는 object를 격리하고, receipt commit 뒤 object 검증이 실패하면 해당 receipt를 `INVALIDATED` successor로 닫는다. 완료 receipt의 in-place 수정과 같은 key의 중복 성공은 금지한다.

## 8. 결과 지식 승격

Execution output이 곧 canonical fact는 아니다.

| execution 종류 | epistemicClass | statement 승격 조건 |
|---|---|---|
| source accessor | `OBSERVED` 후보 | exact source evidence와 locator 존재 |
| deterministic analysis | `DERIVED` | input refs, engine version, output digest 완전 |
| simulator | `SIMULATED` | assumptions, asOf, seed, path 완전 |
| LLM 또는 확률 model | `INFERRED` | model, prompt digest, evidence, confidence 완전 |
| blog parser | `ASSERTED` | author block locator 존재 |

source accessor가 값을 변환했다면 무조건 OBSERVED가 아니라 transform 성격에 따라 DERIVED다. 타입 승격기는 allowlist가 아니라 provenance path를 검사한다.

## 9. Simulator 격리

### 9.1 현재 판단

`src/dartlab/simulate/`는 강한 local preview 자산이지만 공식 안정 엔진으로 과장하지 않는다. `simulate.mirror.bulkSelects()`가 현재 994 selector를 만든다는 관측도 모든 엔진·종목을 포괄하지 않는다. Universe 전체성의 정본으로 쓸 수 없다.

### 9.2 허용 연결

초기 adapter는 `src/dartlab/simulate/admissionRegistry.py`의 실존 계약만 read-only로 받는다.

```text
SimulatorAdmissionRef
  databasePath
  artifactRoot
  receiptId
  trustedIssuerConfigRef
```

Universe는 trusted issuer config를 local secret boundary에서 읽고 `AdmissionVerifier(databasePath, artifactRoot, trustedIssuers)`를 호출한다. verifier가 확인하는 signed `AdmissionReceipt`의 signature, issuer, ruleHash, revisionPolicy, coverage, artifactHash, parent chain, status를 잃지 않고 Universe evidence로 투영한다. receipt가 가리키는 artifact byte와 digest도 다시 확인한다. 임의 envelope를 기존 simulator API인 것처럼 선언하지 않는다.

그 다음 `SimulatorArtifactSchemaRegistry`에서 receiptVersion, kind, ruleId, ruleVersion, ruleHash, issuerExecutableHash exact tuple을 찾는다. 승인 descriptor는 artifact role, media type, schema version, safe decoder digest, subjectHash rule, parent role, field binding, stochastic seed policy와 required semantic fields를 가진다. 서명 receipt만으로 artifact 내부 의미를 안다고 가정하지 않는다.

root result와 모든 parent artifact를 allowlisted decoder로 해석해 `SimulatorSemanticBundle`을 만든다. receipt의 knowledgeAsOf, revisionPolicy, coverage, frequency, stepSpan, maxAdmittedStep는 decoded asOf, vintage와 exact cross-check한다. target, sourceSnapshotId, assumptions, law refs, seed policy, simulator/code/dependency version, output schema와 digest가 완전해야 한다. 중복 field mismatch, unknown schema, stale decoder, missing seed 또는 parent role mismatch는 의미 admission을 거절한다.

공식 receipt가 없는 별도 experiment output은 `UNREGISTERED_PREVIEW`로만 catalog할 수 있고 G2 execution result나 verified graph evidence가 될 수 없다. invalid signature, unknown issuer, broken parent chain, missing artifact, digest mismatch는 `REJECTED_INVALID_ADMISSION_RECEIPT`다. cryptographic verification만 통과하고 semantic descriptor가 없으면 `VERIFIED_ARTIFACT_UNINTERPRETED`이며 역시 실행 결과가 아니다.

다음 파일 개념은 참고할 수 있으나 Universe가 직접 수정하거나 public contract로 선언하지 않는다.

- `simulate/stateCompiler.py`
- `simulate/admissionRegistry.py`
- `simulate/vintage.py`
- `simulate/sheet.py`
- `simulate/simtype.py`
- `simulate/mirror.py`

### 9.3 금지

- `data/` 전체 자동 scan
- `_scratch_*`, cache, 임시 보고서를 지식으로 자동 등록
- assumption 없는 결과 수용
- simulation result를 source fact와 같은 node style로 표시
- 시뮬레이터가 Universe package를 import
- Universe가 private simulator helper를 public axis처럼 호출

## 10. 실패와 부분 결과 계약

```text
ExecutionError
  code
  phase
  retryable
  sourceRefs[]
  messageSafe
  debugRefLocal?
  observedAt
```

대표 code:

- `CAPABILITY_NOT_FOUND`
- `AXIS_NOT_REGISTERED`
- `SCHEMA_INCOMPLETE`
- `TARGET_UNRESOLVED`
- `SOURCE_STALE`
- `DATA_MISSING`
- `ACCESS_DENIED`
- `BUDGET_EXCEEDED`
- `TIMEOUT`
- `CANCELLED`
- `OUTPUT_SCHEMA_MISMATCH`
- `NONDETERMINISTIC_WITHOUT_SEED`
- `INCOMPLETE_SIMULATION_RECEIPT`
- `SIMULATOR_SCHEMA_DESCRIPTOR_MISSING`
- `SIMULATOR_ARTIFACT_SCHEMA_MISMATCH`
- `REJECTED_INCOMPLETE_SIMULATION_SEMANTICS`

UI 또는 CLI는 error code, affected scope, retry 가능 여부, 부분 결과 범위를 정직하게 표시한다.

## 11. 검증 matrix

| 검증 | 방법 | 인수 기준 |
|---|---|---|
| capability census | runtime catalog와 registry union | 발견 항목 100% 분류 |
| fake axis 차단 | 등록되지 않은 axis 실행 | 100% reject |
| args contract | schema property tests | invalid input 실행 0 |
| deterministic replay | 동일 snapshot과 args 재실행 | digest 100% 일치 |
| timeout | sleep/slow fixture | deadline 안에 TIMED_OUT |
| cancel | long CPU fixture | worker 정리, orphan 0 |
| retry | transient source fixture | policy 횟수만 retry |
| idempotency | 동시 동일 request | 중복 실행 0 |
| partial | row/byte budget fixture | silent truncation 0 |
| simulator leakage | result classification test | OBSERVED 승격 0 |
| simulator admission | signed receipt mutation과 issuer fixture | invalid receipt 수용 0 |
| simulator semantics | kind/rule/schema/decoder와 artifact mutation | uninterpreted artifact 승격 0 |
| private leakage | public serializer | private ref 0 |
| receipt completeness | mutation test | 필수 필드 누락 100% reject |
| write isolation | hard-coded path, subprocess, native writer fixture | 보호 경로 mutation 0 |
| durable idempotency | crash point와 동시 request fixture | 중복 성공 receipt 0, orphan 복구 100% |

## 12. G2 인수 기준

- live capability 100% reconcile
- axis registry 100% reconcile
- fake axis와 internal helper 실행 0
- discovered candidate catalogCoverage 100%
- eligible callable의 validated input/output SchemaDescriptor coverage와 executionReadiness 100%
- schema evidence가 불충분한 callable의 실행 admission 0
- deterministic replay digest 일치 100%
- non-deterministic seed 또는 tolerance coverage 100%
- timeout, cancel, retry, idempotency test 전부 통과
- `PARTIAL`을 success로 표시한 사례 0
- simulator result의 `SIMULATED` 분류 위반 0
- signed simulator admission 검증을 우회한 result 0
- 등록된 simulation result root와 reachable parent receipt의 semantic descriptor/decode coverage 100%
- `VERIFIED_ARTIFACT_UNINTERPRETED`를 execution output이나 graph evidence로 승격한 사례 0
- worker allowlist 밖 write와 기존 보호 경로 mutation 0
- 실행 receipt에서 snapshot, version, parameter, seed 필수 누락 0
