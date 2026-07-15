# 12. Innovation Validation Scorecard

> 상태: 기능 채택과 기각의 정본
> 원칙: 혁신성은 수사로 승인하지 않고 evidence receipt로 승인한다.

## 1. 점수표 목적

이 점수표는 새 기능, 장면, renderer, artifact를 다음 중 하나로 판정한다.

- `promote`: 다음 phase로 이동
- `revise`: 가설 또는 표현을 수정하고 같은 attempt 반복
- `hold`: 데이터 또는 선행 계약이 준비될 때까지 보류
- `reject`: 제품에서 제거하고 기각 근거를 보존

점수는 kill condition을 덮지 못한다. source 없는 fact 1건처럼 치명 조건이 발생하면 총점과 관계없이 reject다.

## 2. 혁신성 7축

각 축은 0점부터 5점이다.

| 축 | 0점 | 3점 | 5점 |
|---|---|---|---|
| DartLab 고유성 | 일반 그래프 데모 | DartLab data 일부 사용 | 공시, 엔진, Skill OS, evidence가 결합되어야 성립 |
| 정보 수율 | node 수만 증가 | 기존 task와 비슷 | 검증 claim, 반증, 근거 회수가 유의하게 개선 |
| 증거 무결성 | 출처 역추적 불가 | 일부 receipt | 모든 data mark가 source, derivation, gap 중 하나로 복귀 |
| 데이터 준비도 | 새 정본 필요 | attempt 필요 | current truth와 runtime으로 즉시 재현 |
| 시각 판독성 | 설명 후에도 혼동 | 학습 후 사용 | 상태, 시간, 결손을 90% 이상 정확히 판독 |
| runtime 및 유지보수 | 서버 또는 사본 필수 | bounded adapter | 서버 0 floor, 공통 contract, source별 rollback |
| 접근성 및 동등성 | canvas 또는 3D 전용 | 제한된 table | keyboard와 table에서 핵심 task 100% 완료 |

### 승격 기준

- 총점 28점 이상
- 증거 무결성 5점
- 데이터 준비도 3점 이상
- 시각 판독성 4점 이상
- runtime 및 유지보수 4점 이상
- 접근성 및 동등성 4점 이상
- 해당 phase의 kill condition 0건

## 3. 현재 기능 예비 판정

예비 점수는 토론 결과다. attempt 결과가 나오면 덮어쓴다.

| 기능 | 고유성 | 수율 | 증거 | 준비 | 시각 | 유지 | 접근 | 합계 | 현재 판정 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 변화 우주 | 5 | 5 | 4 | 3 | 5 | 4 | 4 | 30 | P0, snapshot attempt 선행 |
| Thesis Kill-Chain | 5 | 5 | 4 | 3 | 5 | 4 | 4 | 30 | P0, workflow attempt 선행 |
| 판정 우주 | 5 | 4 | 4 | 2 | 4 | 4 | 5 | 28 | P1, scan 및 license gate |
| 한미 Twin | 5 | 4 | 4 | 3 | 4 | 4 | 5 | 29 | P1, identity 및 unit gate |
| Evidence Shock Theater | 4 | 3 | 1 | 0 | 5 | 2 | 3 | 18 | hold, P0 및 P1 기각 |
| 전량 3D 점구름 | 1 | 0 | 0 | 2 | 1 | 0 | 0 | 4 | reject |

## 4. readiness gate

### TruthReady

- legal entity exact identity
- predicate admission rule
- sourceRef 또는 derivationRef
- sourcePublishedAt와 availableAt
- valid interval과 revision
- redistribution 및 license receipt

### SnapshotReady

- source별 version, ETag 또는 immutable path
- map, search, panel, finance source를 한 set으로 결속
- same set replay 가능
- missing source version을 숨기지 않음

### LensReady

- scalar, series, table, ranking, distribution, scenario archetype 선언
- public, local, unavailable 환경별 상태
- unit, coverage, missing policy
- capabilityRef와 evidenceRef
- client 전종목 재계산 없음

### SceneReady

- bounded mark budget
- deterministic layout와 scene hash
- semantic coordinate와 LOD
- omitted receipt
- table 동등 표면
- renderer 내부 fetch 0

### ProductReady

- information yield 비교
- state comprehension
- keyboard 및 mobile task
- share replay
- failure와 rollback drill
- 운영자 눈검수

## 5. SourceSnapshotSet gate

단일 map `buildId`는 search, panel, finance, recipe, capability 결과를 재현하지 못한다.

```text
SourceSnapshotSet
  schemaVersion: sourceSnapshotSet.v1
  snapshotSetId: canonical hash
  createdAt
  sources[]:
    sourceId
    origin
    path
    versionOrEtag
    payloadHash: optional
    dataAsOf
    redistributionReceiptId
  mapBuildId
  capabilityCatalogVersion
  recipeCatalogVersion
```

규칙:

- `snapshotSetId`는 query cutoff를 포함하지 않는다.
- `createdAt`도 snapshotSetId에서 제외하고 source identity와 version만 hash한다.
- source version을 구하지 못하면 `unreplayable`을 기록한다.
- current와 historical replay를 같은 것으로 표시하지 않는다.
- share URL은 snapshotSetId를 우선하고 legacy buildId는 compatibility field로만 읽는다.
- source 하나를 rollback해도 나머지 snapshot identity를 다시 계산한다.

## 6. 시간 gate

`eventAt <= availableAt`은 보편 규칙이 아니다. 계약 체결 공시가 미래 효력일을 말할 수 있기 때문이다.

검증 규칙은 다음과 같다.

```text
sourcePublishedAt <= availableAt
validFrom <= validTo, both present
assertion visible when availableAt <= knownAt
assertion applicable when validFrom <= validAt <= validTo, open end allowed
```

- `eventAt`은 사건의 의미 시각으로 선택 필드다.
- `knowledgeAsOf` 또는 `knownAt`은 assertion identity에 넣지 않고 ProjectionSpec에 둔다.
- 같은 assertion을 다른 knownAt으로 질의해도 assertionId는 바뀌지 않는다.
- missing time을 오늘, 0, filing period end로 추정하지 않는다.

## 7. policy gate

dataset card의 라이선스만으로 upstream source 전체의 재배포를 승인하지 않는다.

```text
RedistributionReceipt
  receiptId
  sourceId
  allowedFields[]
  prohibitedFields[]
  attributionText
  attributionUrl
  policyVersion
  reviewedAt
  decision: public | metadataOnly | localOnly | blocked
```

`unknown`, `localOnly`, 만료된 receipt는 public scene에서 fail closed다. 파생값도 source lineage가 금지 source에 닿으면 자동 public이 되지 않는다.

## 8. attempts 순서

| 순서 | ID | 핵심 산출물 | 합격 | 실패 시 |
|---:|---|---|---|---|
| 1 | U0-T02 | 강화 graph truth probe | exact span, direction, time coverage 공개 | 현재 edge candidate 유지 |
| 2 | U0-S01 | SourceSnapshotSet | source version 누락 0 또는 unreplayable 명시 | exact replay 문구 금지 |
| 3 | U0-P02 | redistribution receipt | public field 100% receipt | source lane 차단 |
| 4 | U0-L01 | LensAvailability | 6 output archetype과 환경 상태 | 해당 lens 숨김 |
| 5 | U0-W01 | changeReplay | synthetic revision 8/8, look-ahead 0, evidence 5/5. live exact fields 0/30 | 계약 완료, live 변화 우주 차단 |
| 6 | U0-V01 | visual grammar | 상태 판독 90% 이상 | grammar 재설계 |
| 7 | U0-W02 | workflowProjection | 단계, 근거, 반증 유실 0 | Kill-Chain 보류 |
| 8 | U0-V06 | renderer bakeoff | task, frame, heap, bundle 개선 | 새 dependency 기각 |
| 9 | U1-Y01 | information yield | baseline 대비 개선 | 기능 revise 또는 reject |
| 10 | U4-C01 | cross-market conformance | 20쌍 identity, unit, period | Twin 자동 overlay 금지 |
| 11 | U5-X01 | 3D uplift | 2D 대비 task 개선 | 3D reject |

## 9. 사용자 검증 설계

### task set

1. 최근 정정이 현재 판단을 바꾼 회사를 찾는다.
2. 주어진 thesis의 가장 빠른 falsifier를 찾는다.
3. 조건 하나를 바꿔 near-miss가 member가 되는 이유를 설명한다.
4. KR과 US 회사의 동일 metric과 결손을 찾는다.
5. relation 하나를 exact 공시 span까지 추적한다.

### 비교군

- current `/map`
- evidence table
- Universe 2D
- optional candidate renderer

### 지표

- task completion rate
- median completion time
- factual error count
- exact evidence open rate
- falsifier discovery rate
- missing 및 omitted recall
- interaction count
- workload 5점 척도
- motion discomfort와 accessibility failure

12명 이하의 작은 표본은 탐색 판정으로만 쓰고, release claim은 반복 표본과 fixture replay를 함께 요구한다.

## 10. 시각 기각표

다음 중 하나면 해당 장면을 release하지 않는다.

- label collision 2% 초과
- logical coordinate hash 불일치 또는 같은 viewport와 DPR에서 고정 anchor 재실행 오차 1px 초과
- fact, candidate, derived, scenario 판독 90% 미만
- unknown을 0 또는 낮은 점수로 오인
- omitted count 또는 reason 누락
- desktop 45fps, mobile 30fps 목표 실패 후 degrade 없음
- context loss 후 table 또는 SVG 복귀 실패
- 3D에서만 완료 가능한 핵심 task
- decorative effect가 information yield를 낮춤

## 11. 결정 receipt

모든 attempt 결론은 다음 형태로 `tests/_attempts/dartlabUniverse/README.md`와 progress ledger에 남긴다.

```text
DecisionReceipt
  attemptId
  hypothesis
  sourceSnapshotSetId
  command
  metrics
  killConditionsObserved[]
  scoreBefore
  scoreAfter
  decision
  owner
  decidedAt
  nextSingleAction
```

실패한 attempt를 지우지 않는다. 새 가설은 새 attemptId 또는 revision으로 남긴다.

## 12. 장기 운영

- 주간: source snapshot과 gap reason drift
- 월간: evidence resolution, look-ahead, policy receipt, scene 결정론
- 분기: information yield, renderer dependency, browser 및 접근성 matrix
- 반기: 기능별 7축 재평가와 dead workflow 제거
- 연간: schema major migration, source 계약, 3D 유지 ROI

점수가 낮아진 기능은 효과를 추가해 숨기지 않고 workflow를 축소하거나 제거한다.

## 영향 파일

- `mainPlan/dartlab-universe/06-progress-ledger.md`
- `mainPlan/dartlab-universe/08-attempts-evidence-matrix.md`
- `tests/_attempts/dartlabUniverse/snapshot/README.md`
- `tests/_attempts/dartlabUniverse/workflow/README.md`
- `tests/_attempts/dartlabUniverse/visual/README.md`
- `tests/_attempts/dartlabUniverse/policy/README.md`
- production 졸업 후 `ui/packages/contracts/src/universe.ts`

## 영향 함수/심볼

- `SourceSnapshotSet`
- `RedistributionReceipt`
- `LensAvailability`
- `DecisionReceipt`
- `scoreInnovationCandidate`
- `validateSnapshotReplay`
- `validatePublicPolicy`

## 테스트

- score threshold와 kill condition 우선순위
- snapshot canonical hash와 source 누락
- legacy buildId compatibility
- 시간 필터와 assertion identity 독립성
- policy fail-closed와 파생 lineage
- decision receipt schema 및 revision 보존
- reference browser task와 renderer budget

## 롤백

- scorecard는 production runtime을 변경하지 않는다.
- 잘못된 기준은 기존 결론을 지우지 않고 기준 version과 정정 receipt를 추가한다.
- snapshot 또는 policy gate가 실패하면 해당 source lane만 차단한다.
- renderer와 workflow는 독립 release state로 이전 stable 버전에 복귀한다.

## 평가

### 전문 개발자 평가

단일 buildId, 잘못된 시간 부등식, dataset 단위 라이선스 가정을 source별 snapshot, query cutoff, redistribution receipt로 교정했다. 기능 점수와 별개인 kill condition을 두어 화려한 결과가 source 누락을 상쇄하지 못하게 했다. 모든 신규 계약은 attempts에서 fixture와 실데이터를 함께 검증한 뒤 production에 이관한다.

### 전문 PM 평가

혁신을 주관적 감탄이 아니라 고유성, 정보 수율, 증거, 준비도, 판독성, 유지보수, 접근성으로 평가할 수 있게 했다. P0와 P1의 우선순위가 명확하고, 사용자가 실제로 더 빨리 근거와 반증을 찾는지가 최종 채택 기준이므로 장기적으로 기능 과잉을 줄인다.
