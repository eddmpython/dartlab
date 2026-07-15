# 08. Attempts and Evidence Matrix

> 정본: Universe의 신규 능력은 이 원장의 가설, 실측, falsifier를 통과하기 전 production에 들어갈 수 없다.
> category: `tests/_attempts/dartlabUniverse/`

## 1. 디렉터리 계약

```text
tests/_attempts/dartlabUniverse/
  README.md
  __init__.py
  truth/
    graphTruthProbe.py
    testGraphTruthProbe.py
  snapshot/
    README.md
    sourceSnapshotSetProbe.py
    changeReplayProbe.py
  workflow/
    README.md
    workflowProjectionProbe.py
    flightPlanContract.py
  visual/
    README.md
    visualGrammarProbe.mjs
    rendererBakeoff.mjs
  policy/
    README.md
    redistributionReceiptProbe.py
    lensAvailabilityProbe.py
  identity/
    entityIdentityProbe.py
    testEntityIdentityProbe.py
  evidence/
    exactEvidenceProbe.py
    testExactEvidenceProbe.py
  ontology/
    assertionContract.py
    testAssertionContract.py
  projection/
    boundedProjection.py
    testBoundedProjection.py
  runtime/
    evidenceBudgetProbe.mjs
    evidenceBudgetFixture.json
  crossMarket/
    panelConformanceProbe.py
    testPanelConformanceProbe.py
  renderer/
    sceneStressProbe.mjs
    sceneStressFixture.json
  fixtures/
    reviewedPositive.jsonl
    hardNegative.jsonl
```

각 하위 폴더는 책임 하나만 가진다. public import는 category `__init__.py`가 소유하고, production code가 attempt deep path를 import하지 않는다.

## 2. 공통 attempt 기록 형식

모든 attempt는 README 결론 표에 다음을 기록한다.

| 필드 | 의미 |
|---|---|
| attemptId | 변경되지 않는 ID |
| hypothesis | 한 문장 가설 |
| input | source path, snapshotSetId 또는 legacy buildId, 표본, cutoff |
| command | 재현 명령 |
| metrics | 정량 결과 |
| falsifier | 가설을 기각하는 조건 |
| decision | promote, revise, reject 중 하나 |
| next | 다음 단일 행동 |

Python demo의 module docstring에는 `결과` 섹션을 둔다. 출력 파일을 임의로 쌓지 않고 stdout JSON을 기본으로 한다. gold와 hard negative처럼 review 자산인 fixture만 git에 보존한다.

## 3. 전체 증거 행렬

| ID | 질문 | 입력 | 합격 | 실패 시 결정 | 상태 |
|---|---|---|---|---|---|
| U0-T01 | 현재 graph가 fact로 입장 가능한가 | HF ecosystem | sourceRef와 availableAt coverage | 기존 edge candidate 강등 | 완료 |
| U0-T02 | exact admission 필드가 실제 있는가 | HF ecosystem과 source candidates | span, section, direction, time, policy 분리 계수 | current edge candidate 유지 | 완료 |
| U0-I01 | canonical legal entity ID가 복원되는가 | KR 50, US 30 | exact ID 100%, ambiguous auto resolve 0 | reference resolver 우선 보강 | 대기 |
| U0-E01 | edge hint에서 exact source를 찾는가 | positive 100, negative 100 | resolution 95%, false accept 1% 이하 | predicate별 source lane 재설계 | 대기 |
| U0-O01 | revision과 시간을 보존하는가 | multi-filing fixture | history 손실 0, look-ahead 0 | assertion schema 수정 | 대기 |
| U0-P01 | bounded scene이 결정론적인가 | atlas, industry, company | bounds 100%, hash 일치 100% | priority/truncation 수정 | 대기 |
| U0-S01 | source 전체가 재현 가능한가 | map, search, panel, finance, catalog | source version 또는 unreplayable 100% | exact replay 문구 금지 | 완료, capability unreplayable |
| U0-P02 | public field가 승인됐는가 | source와 field registry | public mark receipt 100%, false accept 0 | source lane 차단 | 완료, live 0/10 차단 |
| U0-L01 | lens가 환경에서 실제 가능한가 | 6 output archetype | unavailable 오표시 0, missing 보존 | 해당 lens 숨김 | 완료, live ready 0 |
| U0-W01 | 변화를 look-ahead 없이 재생하는가 | synthetic 8 revision과 DART 30개 deterministic schema sample | revision 100%, look-ahead 0, evidence 95% | 변화 우주 범위 축소 | 계약 완료, live source 차단 |
| U0-W02 | recipe를 반증 workflow로 만드는가 | tested recipe 정렬 앞 10개와 qualified synthetic fixture | 단계, 근거, falsifier 유실 0 | Kill-Chain 보류 | 계약 완료, live conclusion 차단 |
| U0-V01 | evidence 상태를 읽는가 | 30 card, task participant | 판독 90% 이상 | visual grammar 재설계 | 대기 |
| U0-V02 | layout이 재현되는가 | 3 browser, 20 replay | logical hash 일치, 같은 viewport 및 DPR anchor 1px 이하 | layout 교체 | 대기 |
| U0-V03 | 밀도에서 생략이 정직한가 | 250, 500, 1,000 node | collision 2% 이하, receipt 100% | lower LOD | 대기 |
| U0-V04 | 이중 시간을 이해하는가 | revision task 12개 | 시간 판독 90% 이상 | Time Lens 재설계 | 대기 |
| U0-V05 | 접근성 표면이 동등한가 | keyboard, reader, low GPU | 핵심 task 100% | renderer 기각 | 대기 |
| U0-V06 | 새 renderer가 필요한가 | SVG, Cosmos, DOM, 후보 | task, frame, heap, bundle 개선 | 새 dependency 기각 | 대기 |
| U0-G01 | release gold를 통과하는가 | positive 300, negative 300 | precision 98%, false accept 1% 이하 | U1 금지 | 대기 |
| U1-Y01 | workflow가 실제로 더 유용한가 | 5 task, baseline과 Universe | information yield 개선 | revise 또는 reject | 대기 |
| U2-R01 | public runtime 예산 안에서 evidence가 열리는가 | reference browsers | cold P95 5초, first cold 4MB provisional, incremental 2MB | runtime 최적화 후 U3 토론 | 대기 |
| U2-L01 | 엔진 output을 generic lens로 보이는가 | 6 lens fixtures | axis별 adapter 0, 결손 보존 | Ref contract 보강 | 대기 |
| U4-C01 | KR과 US가 같은 질문을 받는가 | paired 20 | 20/20 conformance | market lane 분리 유지 | 대기 |
| U5-X01 | 3D가 같은 scene에서 task를 개선하는가 | 3 scene sizes와 discovery task | extra truth request 0, 2D 대비 uplift | 3D 기각 | 대기 |

## 4. U0-T01 결과

명령:

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/truth/graphTruthProbe.py
```

결과:

```text
sourceVersion              2026-04-14
nodeCount                  2,664
edgeCount                 20,560
linkedNodeCount            2,656
isolatedNodeCount              8
selfLoopCount                 13
panel_text                17,400
panel_table                  208
network                    2,952
exactSourceRefEdgeCount        0
exactAvailableAtEdgeCount      0
observedEligibleEdgeCount      0
OCI incidentEdgeCount      4,474
OCI unique neighbor degree 2,585
```

판정: graph artifact와 layout은 candidate topology로 재사용할 가치가 있지만, 현재 edge를 factual assertion으로 재사용할 수는 없다. U0-T01은 필드 존재 센서스다. exact span, section, direction, public policy까지 admission한 결과로 해석하지 않으며 U0-T02가 이를 강화한다.

## 4.1 U0-T02 결과

명령:

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/truth/factualAdmissionProbe.py
```

결과:

```text
edgeCount                  20,560
stableSourceRefCount            0
documentIdCount                 0
sectionPathCount                0
exactLocatorCount               0
directionVerifiedCount          0
sourcePublishedAtCount          0
availableAtCount                0
validFromCount                  0
policyReceiptCount              0
observedStatusCount             0
admittedEdgeCount               0
selfLoopCount                  13
```

판정: confidence와 evidence title은 factual admission을 대체하지 못한다. current edge 전체를 candidate topology로 유지한다. U0-E01에서 exact source를 새로 해소하고 U0-O01 assertion contract를 통과하기 전 observed 승격은 0건이어야 한다.

## 4.2 U0-S01 결과

명령:

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/snapshot/sourceSnapshotSetProbe.py
```

결과:

```text
sourceCount                         10
immutableHfSourceCount               8
immutableGitBlobSourceCount          1
unreplayableSourceCount              1 capabilityCatalog
missingDataAsOfSourceCount           1 dartPanelSample
missingRedistributionReceiptCount   10
canonicalHashRepeat                2/2
unitRegression                     8/8 PASS
snapshotSetId  sha256:4a68a0c0129884bc138223ef3d31672c1e7dd5bbbdac33a4816d0f953e54f73a
mapBuildId     20260715-084444
hfRepoCommit   c0260a60859f0ba5a30d452a7c05791d79e9bd1d
```

판정: source version 또는 명시적 unreplayable coverage 100%, 순서와 관측시각 및 OS path 독립 hash, source version 변화 감지, legacy buildId only exact replay 차단을 검증했다. U0-S01 계약은 완료다. 다만 capability catalog는 226개 canonical output hash를 식별할 수 있을 뿐 historical payload를 복원할 immutable manifest가 없으므로 live SourceSnapshotSet의 `exactReplayReady`는 false다. 이 결손을 숨긴 public exact replay 문구는 금지한다. receipt 결손 10개는 U0-P02 입력이다.

## 4.3 U0-P02 결과

명령:

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/policy/redistributionReceiptProbe.py
```

결과:

```text
sourceCount                    10
reviewedReceiptCount            0
validPublicReceiptCount         0
missingReceiptCount            10
publicReady                 false
syntheticRegression          12/12 PASS
negativeFalseAccept             0
```

판정: canonical receiptId, allowed 및 prohibited field, attribution, policyVersion, reviewer, review window, decision과 upstream lineage admission을 구현했다. unknown, localOnly, blocked, expired, metadataOnly 확대, prohibited field와 mixed upstream hard negative의 false accept는 0이었다. 그러나 live reviewed receipt는 0/10이고 current map field의 upstream receipt lineage도 없으므로 publicReady는 false다. HF README의 CC BY 4.0 표기와 OpenDART 활용 안내는 검토 evidence candidate이며 receipt 자체가 아니다. 운영자 review 전 live source를 public으로 자동 승격하지 않는다.

## 4.4 U0-L01 결과

명령:

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/policy/lensAvailabilityProbe.py
```

결과:

```text
capabilityCount                       226
capabilityReturnContractCount          83
capabilityRuntimeDeclarationCount       0
capabilityArchetypeDeclarationCount     0
capabilityUnitDeclarationCount          0
capabilityCoveragePolicyCount           0
capabilityMissingPolicyCount            0
skillCount                            286
skillRuntimeDeclarationCount          286
skillPublicBrowserDeclarationCount      0
reviewedReceiptCount                    0
currentPublicLensReadyCount             0
syntheticRegression                   8/8 PASS
```

판정: explicit LensSpec가 있으면 scalar, series, table, ranking, distribution, scenario 6 archetype과 publicBrowser, localPython, localServer 3환경을 generic contract 하나로 처리할 수 있다. unavailable loader 호출 0, missing zero fill 0을 검증했다. 그러나 현재 capability와 Skill OS에서 public lens 의미와 환경을 추정할 근거가 없고 receipt도 없으므로 live ready는 0이다. 226개 capability별 UI adapter는 기각하고 reviewed LensSpec registry만 production 후보로 둔다.

## 4.5 U0-W01 결과

명령:

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/snapshot/changeReplayProbe.py
```

결과:

```text
syntheticRevisionCount              8
preservedRevisionCount              8
created                             1
corrected                           1
retracted                           1
newlyKnown                          1
stale                               1
lookAheadCount                      0
evidenceBindingCoverage          100%
syntheticRegression               8/8 PASS
dartSampleFiles                    30
dartSampleRows                359,115
rceptNoFileCount                30/30
sourcePublishedAtFileCount       0/30
availableAtFileCount             0/30
revisionIdFileCount              0/30
rowKeyFileCount                  0/30
revisionGroupCount                  0
liveExactReplayReady            false
```

판정: synthetic contract는 query cutoff와 assertion identity를 분리하고, 미래 revision을 diff, artifactHash, sourceRefs에서 제외하며, production VintageRef의 exact as-known 조건을 통과했다. 그러나 live DART sample은 filing ID 외 exact observation time, revision identity, row locator가 없다. 표본은 대표성을 주장하지 않는 정렬 기반 schema census다. U0-W01 계약은 완료하되 live 변화 재생은 `revise`로 차단한다. `rcept_no`에서 임의 시각을 합성하지 않고 reviewed multi-filing fixture가 확보될 때 재심사한다.

## 4.6 U0-W02 결과

명령:

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/workflow/workflowProjectionProbe.py
```

결과:

```text
recipeCount                           156
testedRecipeCount                      30
testedCompleteCoreContractCount        22
selectedRecipeCount                    10
selectedProcedureCount                 80
selectedRecipeStepCount                25
selectedRequiredEvidenceCount          60
selectedSourceRefRecipeCount        10/10
selectedFalsifierCandidateCount        29
selectedQualifiedFalsifierCount         0
testedExplicitVersionFieldCount      0/30
testedExplicitFalsifierFieldCount    0/30
procedurePreservation                100%
requiredEvidenceAccounting           100%
falsifierCandidatePreservation       100%
gapReceiptCount                         60
conclusionBeatCount                      0
modelFactPromotionCount                  0
dedicatedAdapterCount                    0
repeatedFlightHashMatch              10/10
syntheticRegression                    8/8 PASS
liveReady                            false
```

판정: immutable catalog blob과 canonical recipe content hash로 recipeVersion을 재현하고 procedure, recipeSteps, requiredEvidence, sourceRefs, negative condition origin을 generic SceneBeat로 보존했다. failureMode와 forbidden은 qualified falsifier가 아니라 candidate다. VerificationRefs 없는 candidate는 conclude를 열지 않고 missing evidence 60개는 GapReceipt로 남긴다. U0-W02 compiler는 합격이지만 live Kill-Chain 결론은 `revise`로 차단한다.

## 5. existing attempts 재사용 지도

| 기존 category | 이미 증명한 것 | Universe 사용 | 중복 금지 |
|---|---|---|---|
| `searchGraphCatalog` | search hit 뒤 bounded graph sidecar, ranking 비침범 | evidence 결과에 relation card를 붙이는 선례 | live Company traversal 재작성 |
| `empiricalWorldPaths` | 검증된 world path와 empirical binding | scenario relation의 admitted path 표시 | factual relation과 scenario 혼합 |
| `boundedWorldExecution` | trace limit, exact aggregate, bounded memory | 많은 scenario 결과의 bounded display | Universe용 별도 simulation core |
| `pathAdmissionRuntime` | signed path, vintage, decisionAsOf runtime gate | scenario edge provenance와 knownAt | receipt 검증 복제 |
| `worldIntegrity` | world state integrity와 오류 차단 | scene의 derived/scenario integrity 참고 | graph truth 저장소로 사용 |
| `financialWorld` | financial state와 law 표현 | financial lens output 의미 | 관측값을 모두 graph node화 |
| `worldEvolve` | explicit state transition과 paired strategy | U5 이후 scenario camera | MVP fact graph 선행 배선 |

Universe는 위 attempts를 import해 새 의존성을 만드는 것이 아니라, 이미 졸업해 production에 있는 `dartlab.simulate`의 `VintageRef`, admission, bounded execution 계약을 재사용한다.

## 6. gold 작성 계약

### reviewed positive

필수 필드:

- `caseId`
- `subjectId`
- `predicate`
- `objectId`
- `docId`
- `sectionPath`
- `evidenceText` 또는 table row pointer
- `eventAt`
- `validFrom`, `validTo`
- `sourcePublishedAt`
- `availableAt`
- `expectedStatus`
- `reviewer`
- `reviewedAt`

### hard negative

필수 유형:

- 짧은 영문 회사명 일반 단어 충돌
- 동일 회사명 다른 법인
- 회사가 자기 자신을 언급한 self-loop
- 공시 주체와 상대 회사 방향 역전
- 산업 peer를 거래관계로 오인
- 정정 전후 문장 충돌
- 비상장 상대와 상장사 alias 충돌
- 보고서 section title만 같고 본문 근거 없음
- ticker 변경과 과거 legal entity 혼동
- cross-market fuzzy name 충돌

gold는 자동 생성 candidate를 그대로 승인하지 않는다. 사람이 문서 근거를 열어 검토한 뒤에만 `reviewedAt`을 채운다.

## 7. 졸업 체크리스트

- [x] category 생성
- [x] 첫 가설과 실데이터 demo
- [x] truth 책임 하위 모듈 분리
- [x] demo 결과를 module docstring과 README에 기록
- [x] U0-T02 factual admission 필드 전수 계수
- [x] U0-S01 source version, canonical hash, legacy replay guard
- [x] U0-P02 receipt integrity, expiry, field와 upstream admission guard
- [x] U0-L01 6 archetype, 3 environment, missing preservation guard
- [ ] identity, evidence, ontology, projection 모듈화
- [ ] special-case와 중복 rule 제거
- [ ] camelCase와 SSOT 검토
- [ ] full 9섹션 docstring 검토
- [ ] positive 300 및 hard negative 300 통과
- [ ] production 이관 대상과 기각 대상 분리

## 영향 파일

- `tests/_attempts/dartlabUniverse/**`
- `mainPlan/dartlab-universe/06-progress-ledger.md`
- production 이관 시에만 `ui/packages/contracts/src/universe.ts`와 runtime 파일

## 영향 함수/심볼

- `inspectGraphTruth`
- `resolveEntityIdentity`
- `resolveExactEvidence`
- `canonicalAssertionId`
- `compileBoundedProjection`
- `buildSourceSnapshotSet`
- `compileChangeReplay`
- `compileWorkflowProjection`
- `validateVisualGrammar`
- `buildRedistributionReceipt`
- `validateRedistributionReceipt`
- `assessPublicProjection`
- `inspectLensAvailability`
- `resolveLensOutput`

현재 `inspectGraphTruth`, `inspectFactualAdmission`, `buildSourceSnapshotSet`, `assessReplayRequest`, `buildRedistributionReceipt`, `validateRedistributionReceipt`, `assessPublicProjection`, `inspectLensAvailability`, `resolveLensOutput`이 attempt에 존재한다. 나머지는 해당 attempt가 시작될 때 이름과 책임을 확정한다. README의 예정 파일명은 production API 약속이 아니다.

## 테스트

- 각 probe는 network 없는 작은 fixture test를 가진다.
- live run은 별도 명령으로 실행하고 remote failure를 unit failure로 숨기지 않는다.
- test file 하나는 lock wrapper 또는 해당 repo의 공식 단일 파일 절차를 사용한다.
- production 이관 전 attempt fixture를 production contract test가 재사용한다.

## 롤백

attempts는 production import가 없으므로 category를 제거해도 runtime 영향이 없다. 다만 검증 결과와 기각 근거는 mainPlan ledger에 보존한다. 잘못된 live 측정은 기존 행을 지우지 않고 정정 행과 원인을 추가한다.

## 평가

### 전문 개발자 평가

기존 계획의 가장 큰 결함은 U0가 한 덩어리였다는 점이다. identity, evidence, assertion, projection, runtime을 분리하고 각 falsifier를 만들었다. 이미 있는 world, admission, search graph attempts도 재사용 지도로 연결해 같은 개념을 다시 구현할 위험을 줄였다.

### 전문 PM 평가

실험의 성공 기준을 사용자 가치와 연결했다. sourceRef를 못 찾는 edge는 화려해도 제품 가치가 없고, exact evidence와 deterministic share가 있는 작은 scene은 바로 가치가 있다. gold 600건은 출시를 늦추는 문서 작업이 아니라 제품의 신뢰 자산이다.
