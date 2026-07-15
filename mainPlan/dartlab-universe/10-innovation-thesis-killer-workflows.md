# 10. Innovation Thesis and Killer Workflows

> 상태: 제품, 시각, 기술 교차 토론 수렴본
> 결정: P0는 변화 우주와 Thesis Kill-Chain, P1은 판정 우주와 한미 Twin이다.

## 1. 혁신의 정의

DartLab Universe의 혁신은 많은 점을 동시에 그리는 데 있지 않다. 사용자가 질문 하나를 넣었을 때 다음 연쇄를 끊김 없이 재현하는 데 있다.

```text
질문
  -> 주장
  -> 필요한 근거
  -> 반증 조건
  -> 당시 공개된 관측
  -> 원문 또는 표
  -> 엔진 판정
  -> 남은 결손
  -> 공유 가능한 재현 receipt
```

이 제품은 그래프 뷰어가 아니라 **evidence telescope이자 analysis compiler**다. 275.76GB의 모든 데이터를 화면에 올리지 않고, 질문에 답하는 데 필요한 정보만 의미 있는 좌표와 장면 순서로 컴파일한다.

### 혁신 판정 질문

새 기능은 다음 질문에 모두 답해야 한다.

1. 이 기능은 DartLab의 공시, 재무, 엔진, Skill OS를 함께 써야만 강해지는가.
2. 일반 그래프보다 사용자가 더 빨리 근거 있는 결론 또는 반증에 도달하는가.
3. 모든 시각적 주장을 원문, 파생식, 시나리오 가정 중 하나로 되돌릴 수 있는가.
4. 현재 데이터로 가능한 부분과 attempt 이후 가능한 부분이 분리되어 있는가.
5. 2D와 table에서 완전하며 3D 없이도 제품 가치가 유지되는가.

하나라도 아니면 제품 기능이 아니라 데모 효과다.

## 2. 제품 서명

제품의 한 문장 서명은 다음으로 확정한다.

**질문을 움직이면 우주가 바뀌고, 장면을 열면 주장과 반증과 원문이 같은 시간축에서 연결된다.**

이를 세 가지 반복 가능한 동작으로 표현한다.

| 동작 | 사용자 언어 | 제품 응답 |
|---|---|---|
| 이동 | 과거에는 무엇이 달랐나 | 변화만 남긴 장면과 before/after evidence |
| 추적 | 이 투자 논리는 어디서 깨지나 | assumption부터 falsifier까지 이어진 Kill-Chain |
| 대조 | 다른 조건 또는 시장에서는 무엇이 달랐나 | PASS, FAIL, MISSING과 KR, US 동형 비교 |

## 3. 공통 제품 계약

### UniverseFlightPlan

`ProjectionSpec` 하나는 한 장면을 결정한다. 사용자의 조사 과정은 여러 장면과 증거 개방 순서를 가져야 하므로 별도 계약이 필요하다.

```text
UniverseFlightPlan
  schemaVersion: universeFlightPlan.v1
  flightId: canonical hash
  questionRef: optional local reference
  objective: investigate | compare | falsify | explain
  snapshotSetId: SourceSnapshotSet id
  beats: SceneBeat[]
```

plan 실행 결과는 `UniverseFlightReceipt`에 beat별 EvidenceReceipt와 GapReceipt, outputHash를 보존한다. 실행시각은 의미 hash에서 제외한다.

### SceneBeat

```text
SceneBeat
  beatId
  intent: orient | focus | compare | evidence | falsify | conclude
  projectionSpec
  selectedIds[]
  expectedEvidenceRefs[]
  transition: replace | diff | overlay
  narration: deterministic short label
```

`SceneBeat[]`는 영화식 자동 비행이 아니다. 사용자가 어느 단계에서 무엇을 보았는지 재현하는 조사 장부다. 각 beat는 URL에서 직접 열 수 있고, 건너뛰기와 되돌리기가 가능해야 한다.

### EvidenceReceipt

```text
EvidenceReceipt
  receiptId
  claimId
  evidenceRefs[]
  derivationRefs[]
  falsifierRefs[]
  sourceSnapshotIds[]
  status: supported | contradicted | missing | scenario
  validAt
  knownAt
  generatedAt
```

화면의 node, edge, color, size, 순위, 변화 표식은 하나 이상의 receipt를 가져야 한다. 장식 배경과 navigation 표시는 제외하지만 데이터처럼 보이는 mark에는 예외가 없다.

### GapReceipt

결손은 빈값이 아니라 정보다.

```text
GapReceipt
  gapId
  kind: unavailable | notPublic | notApplicable | unresolved | stale | omitted
  ownerSource
  requestedField
  reasonCode
  retryPolicy
```

## 4. P0-A 변화 우주

### 사용자 약속

두 시점 사이에서 새로 생긴 것, 사라진 것, 정정된 것만 남긴다. 현재값을 과거에 역주입하지 않고, 변화 표식 하나를 누르면 before와 after 원문으로 돌아간다.

### 첫 질문

- 이 회사의 최근 2년 공시와 재무에서 무엇이 처음 나타났는가.
- 이 산업의 회사 수, 매출, 수익성 분포는 언제 바뀌었는가.
- 정정 공시가 기존 판단을 어떻게 바꿨는가.

### 장면 순서

1. L0 산업 territory를 고정 좌표로 연다.
2. 사용자가 `knownAt A`와 `knownAt B`를 선택한다.
3. source snapshot 차이를 계산하되 위치는 바꾸지 않는다.
4. created, corrected, retracted, newlyKnown, becameStale로 변화 lane을 분리한다.
5. 회사를 열면 metric, filing, assertion 변화만 L3에 남긴다.
6. 관계를 열면 before와 after assertion을 L4 evidence fan으로 펼친다.
7. L5에서 정확한 공시 span, 표 셀, 재무 관측을 연다.
8. 변화 receipt와 남은 결손을 함께 공유한다.

### 즉시 가능한 첫 데모

기존 `atlas.json`, `timeline.json`, `movers.json`만 사용해 34개 산업 변화 장면을 만든다.

- 산업 좌표는 고정한다.
- 2020년부터 2025년까지 회사 수와 현재 보유 metric의 집계를 바꾼다.
- mover는 현재 시점 신호로만 pulse한다.
- atlas flow와 ecosystem relation은 candidate topology로 표시하고 사실 전파로 설명하지 않는다.
- 이 데모는 공시 revision 재생을 약속하지 않는다. SourceSnapshotSet attempt가 졸업한 뒤 확장한다.

### 선행 attempt와 kill 조건

`U0-S01 SourceSnapshotSet`과 `U0-W01 changeReplay`가 선행한다. DART 30사의 공시 revision과 관측을 두 cutoff에서 재현한다.

- sourcePublishedAt, availableAt, valid interval, revision 보존 100%
- look-ahead 0건
- before 및 after exact evidence 결속 95% 이상
- 현재값의 과거 역주입 1건이면 즉시 기각
- 같은 snapshotSet과 flight plan의 diff hash 불일치 1건이면 production 이관 금지

## 5. P0-B Thesis Kill-Chain

### 사용자 약속

투자 논리를 보기 좋은 메모가 아니라 반증 가능한 경로로 바꾼다.

```text
thesis
  -> assumption
  -> fragility
  -> trigger
  -> propagation
  -> tripwire
  -> falsifier
  -> current verdict
```

### DartLab 고유 자산

Skill OS recipe 156개 중 procedure, requiredEvidence, falsifier를 가진 recipe를 장면 compiler의 입력으로 쓴다. capability 결과는 표준 `Ref`로만 받는다. recipe나 엔진을 그래프 노드로 노출하지 않는다.

### 장면 순서

1. 사용자가 회사, 산업, 비교군과 논제를 선택한다.
2. 검증된 recipe가 필요한 주장 단계와 requiredEvidence를 선언한다.
3. compiler가 각 단계를 `SceneBeat`로 만들고 결손을 먼저 계산한다.
4. observed evidence와 deterministic derivation을 별도 lane에 놓는다.
5. falsifier가 없는 주장에는 결론 beat를 만들지 않는다.
6. tripwire별 현재 관측, 기준치, 단위, coverage를 연다.
7. 충돌 또는 missing은 빨강 점수 대신 별도 gap lane으로 남긴다.
8. 사용자가 판정을 바꾸면 어떤 evidence와 가정이 바뀌었는지 receipt diff를 만든다.

### 첫 제품 템플릿

첫 3개 템플릿만 수동 검토해 연다.

1. 성장 지속성: 매출 성장, 마진, 현금전환, 수주 또는 제품 근거, 둔화 tripwire
2. 신용 취약: 상환, 레버리지, 유동성, 현금흐름, 차환 trigger
3. 공시 변화: 신규 위험 문구, 정정, 감사 및 지배구조 변화, 반복 해소 여부

템플릿은 엔진 계산을 복제하지 않는다. recipe 단계와 capabilityRef를 묶는 선언형 registry다.

### 선행 attempt와 kill 조건

`U0-W02 workflowProjection`이 tested recipe 10개를 대상으로 실행된다.

- 수동 UI adapter 없이 recipe의 procedure, requiredEvidence, falsifier를 scene으로 컴파일
- 모든 claim에 sourceRef 또는 derivationRef 100%
- 모든 결론 경로에 open falsifier 1개 이상
- 같은 입력의 flight hash 일치 100%
- source 없는 요약 또는 모델 추론이 fact로 승격된 사례 1건이면 즉시 기각
- 일반 evidence table보다 과제 완료시간 또는 정확도가 개선되지 않으면 UX 형태를 재설계

## 6. P1-A 판정 우주

판정 우주는 종목별 단일 점수가 아니다. 조건과 회사의 교차 격자를 공간화한다.

```text
rows: company
columns: condition
cell: PASS | FAIL | MISSING | NOT_APPLICABLE
side products: members | nearMisses | funnel | coverage | unknownCount
```

사용자는 조건을 움직여 어떤 회사가 왜 들어오고 나가는지 본다. near-miss는 threshold까지의 거리와 근거 관측을 보여준다. missing을 fail 또는 0으로 바꾸지 않는다.

선행 조건은 `scan-screener-os` 졸업, `LensAvailability`, `LicenseReceipt`, 결정론 판정 격자다. public 금지 필드 1건 노출 또는 missing과 fail 혼합 1건이면 기능을 닫는다.

## 7. P1-B 한미 Twin

KR과 US 회사를 같은 의미 좌표의 좌우 mirror에 둔다.

### 비교 단위

- legal entity exact ID
- disclosureKey 또는 명시적 cross-market topic
- 표준 account와 단위
- fiscal period와 frequency
- sourcePublishedAt, availableAt, valid interval
- panel 16컬럼의 동형 section 및 content pointer

### 경험

1. 두 회사를 고른다.
2. 공통 질문과 snapshot set을 고정한다.
3. 비교 가능한 항목, 한쪽만 있는 항목, 양쪽 모두 결손인 항목을 분리한다.
4. 같은 metric은 좌우 동일 축과 단위를 쓴다.
5. 공시 문장은 자동 번역을 근거로 쓰지 않고 원문과 section identity를 보존한다.
6. gap을 데이터 부족이 아니라 시장 공시 구조 차이로 설명할 수 있게 한다.

`U4-C01`에서 20쌍을 검증한다. fuzzy entity 연결, 통화 또는 단위 누락, 기간 불일치를 침묵한 사례가 1건이면 자동 겹치기를 기각한다.

## 8. P2와 명시적 기각

### Evidence Shock Theater

P2로 내린다. 현재 relation 20,560건은 factual causal path가 아니며, sourceRef와 availableAt이 모두 없다. 기존 `ShockSimulator`의 양방향 BFS와 임의 감쇠는 재사용하지 않는다.

다음 조건을 모두 통과한 뒤에만 Kill-Chain의 scenario lane으로 제한해 검토한다.

- observed 관계 admission
- signed path receipt
- hindcast 또는 replay
- fact, derived, scenario의 평행 lane
- 가정 변경에 따른 결과 diff

correlation을 전파 방향으로 쓰거나 scenario를 fact와 같은 선으로 그리면 즉시 기각한다.

### 영구 기각

- 2,664개 회사와 모든 공시를 한 번에 그리는 3D 점구름
- capability와 skill을 사용자용 데이터 노드로 노출
- LLM이 predicate 또는 factual edge를 생성
- client에서 전 종목 전 엔진을 실행
- 단일 종합 점수로 PASS, FAIL, MISSING을 덮음
- sourceRef 없는 자동 충격 입자 애니메이션
- 정보 의미가 없는 별, 안개, 배경 particle

## 9. 정보 수율

성공은 node 수가 아니라 **information yield**로 측정한다.

```text
informationYield = 검증 가능한 새 claim 수 / 과제 완료 시간
evidenceYield = 열린 exact evidence 수 / 사용자 핵심 상호작용 수
falsifierYield = 확인 가능한 반증 조건 수 / 결론 수
gapHonesty = 명시된 missing 및 omitted 수 / 실제 missing 및 omitted 수
```

제품 beta에서는 같은 질문을 기존 map, table, Universe로 수행해 완료시간, 정답, 근거 회수, 오판을 비교한다. Universe가 더 화려하지만 개선이 없으면 해당 장면을 기각한다.

## 10. 구현 순서

| 순서 | work packet | 산출물 | 다음으로 가는 조건 |
|---:|---|---|---|
| 1 | U0-S01 | SourceSnapshotSet contract와 fixture | source version 누락 0 |
| 2 | U0-W01 | change replay diff | look-ahead 0, diff 결정론 |
| 3 | U0-V01 | visual grammar comprehension | 상태 판독 90% 이상 |
| 4 | U1-A01 | 34산업 변화 우주 데모 | atlas budget, table 동등성 |
| 5 | U0-W02 | recipe to Kill-Chain compiler | claim 및 falsifier 유실 0 |
| 6 | U1-W01 | 첫 3개 Kill-Chain 템플릿 | 과제 성능 비교 통과 |
| 7 | U1-V01 | 판정 우주 attempt | missing 보존, license 통과 |
| 8 | U4-C01 | 한미 Twin 20쌍 | identity, unit, period 100% |
| 9 | U5-X01 | 2.5D 또는 3D uplift | 2D 대비 유의한 개선만 유지 |

## 11. 장기 유지보수

- workflow registry는 recipe ID, version, requiredEvidence, falsifier와 capabilityRef만 가진다.
- engine 계산식과 threshold를 Universe에 복사하지 않는다.
- SceneBeat와 EvidenceReceipt reader는 current와 previous를 지원한다.
- deprecated recipe는 기존 receipt 재현을 위해 version만 보존하고 새 flight에서 숨긴다.
- 분기마다 information yield, abandon rate, unresolved gap, source별 failure를 검토한다.
- 제품 서명 4개 중 유지비 대비 정보 수율이 낮은 기능은 renderer가 아니라 workflow 단위로 제거한다.

## 영향 파일

- `mainPlan/dartlab-universe/00-product-prd.md`
- `mainPlan/dartlab-universe/02-ontology-evidence-contract.md`
- `mainPlan/dartlab-universe/03-runtime-public-architecture.md`
- `mainPlan/dartlab-universe/04-product-ux.md`
- `mainPlan/dartlab-universe/08-attempts-evidence-matrix.md`
- `tests/_attempts/dartlabUniverse/snapshot/`
- `tests/_attempts/dartlabUniverse/workflow/`
- production 졸업 후 `ui/packages/contracts/src/universe.ts`
- production 졸업 후 `ui/packages/runtime/src/data/universe/flight.ts`

## 영향 함수/심볼

- `UniverseFlightPlan`
- `UniverseFlightReceipt`
- `SceneBeat`
- `EvidenceReceipt`
- `GapReceipt`
- `SourceSnapshotSet`
- `compileFlightPlan`
- `diffSnapshotScenes`
- `compileRecipeWorkflow`

## 테스트

- snapshot 및 flight canonical hash 결정론
- sourcePublishedAt, availableAt, valid interval, knownAt filter 독립성
- before 및 after evidence 결속
- recipe procedure, requiredEvidence, falsifier 보존
- missing, omitted, stale reason 보존
- table과 scene의 claim 및 receipt 집합 동등성
- 기존 map 또는 table 대비 information yield 비교

## 롤백

- P0 attempt는 production import가 없으므로 category 제거만으로 runtime 영향이 없다.
- 변화 우주는 snapshot diff를 끄고 현재 atlas scene으로 복귀한다.
- Kill-Chain은 flight compiler를 끄고 evidence table로 복귀한다.
- 판정 우주와 한미 Twin은 독립 feature state로 닫고 P0를 유지한다.
- receipt schema 문제는 previous reader로 복귀하고 기존 receipt를 삭제하지 않는다.

## 평가

### 전문 개발자 평가

ProjectionSpec만으로는 사용자의 조사 순서와 반증을 보존할 수 없다는 결함을 `UniverseFlightPlan`, `SceneBeat`, `EvidenceReceipt`로 닫았다. 신규 계산 엔진이나 graph store를 만들지 않고 기존 recipe, capability, Ref, VintageRef를 조립하므로 구조 위반을 줄인다. 가장 위험한 변화 재생, recipe compiler, license, cross-market identity는 attempts를 통과하기 전 production에 들어가지 않는다.

### 전문 PM 평가

변화 우주는 첫눈에 이해되는 시간 서명이고, Thesis Kill-Chain은 반복 사용 이유를 만든다. 판정 우주와 한미 Twin은 DartLab의 횡단 데이터와 KR, US 동형 panel을 제품 차별점으로 바꾼다. 기능 우선순위가 화면 화려함이 아니라 사용자가 근거 있는 판단과 반증에 도달하는 속도로 정렬되었다.
