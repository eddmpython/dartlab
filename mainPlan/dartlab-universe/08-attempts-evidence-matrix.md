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
| U0-I01 | canonical legal entity ID가 복원되는가 | KR 50, US 30, security와 filing sample | exact ID 100%, ambiguous auto resolve 0 | reference resolver 우선 보강 | 계약 완료, historical registry 차단 |
| U0-E01 | edge hint에서 exact source를 찾는가 | search catalog 381,149행과 synthetic positive 및 negative | resolution 95%, false accept 1% 이하 | predicate별 source lane 재설계 | 계약 완료, live source와 reviewed gold 차단 |
| U0-O01 | revision과 시간을 보존하는가 | synthetic multi-filing correction과 public edge 20,560 | history 손실 0, look-ahead 0 | assertion schema 수정 | 계약 완료, live assertion source 차단 |
| U0-P01 | bounded scene이 결정론적인가 | live atlas, semiconductor, Samsung egograph와 synthetic graph | bounds 100%, hash 일치 100% | priority/truncation 수정 | 완료, projection promote |
| U0-S01 | source 전체가 재현 가능한가 | map, search, panel, finance, catalog | source version 또는 unreplayable 100% | exact replay 문구 금지 | 완료, capability unreplayable |
| U0-P02 | public field가 승인됐는가 | source와 field registry | public mark receipt 100%, false accept 0 | source lane 차단 | 완료, live 0/10 차단 |
| U0-L01 | lens가 환경에서 실제 가능한가 | 6 output archetype | unavailable 오표시 0, missing 보존 | 해당 lens 숨김 | 완료, live ready 0 |
| U0-W01 | 변화를 look-ahead 없이 재생하는가 | synthetic 8 revision과 DART 30개 deterministic schema sample | revision 100%, look-ahead 0, evidence 95% | 변화 우주 범위 축소 | 계약 완료, live source 차단 |
| U0-W02 | recipe를 반증 workflow로 만드는가 | tested recipe 정렬 앞 10개와 qualified synthetic fixture | 단계, 근거, falsifier 유실 0 | Kill-Chain 보류 | 계약 완료, live conclusion 차단 |
| U0-V01 | evidence 상태를 읽는가 | 7 state, 30 card, task participant | 판독 90% 이상 | visual grammar 재설계 | 계약 완료, participant 0/12 차단 |
| U0-V02 | layout이 재현되는가 | live 3 scene, 3 browser, 20 replay | logical hash 일치, 같은 viewport 및 DPR anchor 1px 이하 | layout 교체 | 완료, layout promote |
| U0-V03 | 밀도에서 생략이 정직한가 | 250, 500, 1,000 node, desktop 및 mobile | collision 2% 이하, receipt 100% | lower LOD | 완료, density promote |
| U0-V04 | 이중 시간을 이해하는가 | revision task 12개, participant 12명 | validAt, knownAt, combined 판독 90% 이상 | Time Lens 재설계 | 계약 완료, participant 0/12 차단 |
| U0-V05 | 접근성 표면이 동등한가 | keyboard, reader, low GPU | 핵심 task 100% | renderer 기각 | 계약 완료, named reader 수동 gate |
| U0-V06 | 새 renderer가 필요한가 | SVG, Cosmos, DOM, 후보 | task, frame, heap, bundle 개선 | 새 dependency 기각 | 완료, Canvas 2D promote |
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

## 4.7 U0-I01 결과

명령:

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/identity/entityIdentityProbe.py
```

결과:

```text
krLegalSampleCanonical              50/50
usLegalSampleCanonical              30/30
krFilingSampleCanonical             50/50
usFilingSampleCanonical             30/30
exactIdentifierCoverage              100%
krxIsinSecurityCanonical       2,872/2,872
ambiguousAliasAutoResolve                0
krxSecurityIssuerLink           2,742/2,872
krxSecurityIssuerGap                   130
usMultiSecurityCik                   1,473
krHistoricalValidityFields               0
usHistoricalValidityFields               0
usLocalFilingIssuers                     2
syntheticRegression                    9/9 PASS
historicalAliasReady                 false
liveReady                            false
```

판정: exact provider identifier와 entity, security, filing kind 분리 contract는 합격이다. 그러나 security issuer link, alias validity와 special-case gold가 불완전해 current lookup을 historical identity로 승격할 수 없다. 이름과 ticker의 first-row 또는 fuzzy 해소는 금지하고 reference owner 보강 전 live registry를 차단한다.

## 4.8 U0-E01 결과

명령:

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/evidence/exactEvidenceProbe.py
```

결과:

```text
catalogFileCount                         3
catalogRowCount                    381,149
documentRowCount              381,149/381,149
sectionLocatorRowCount         381,149/381,149
sourceRefRowCount              381,149/381,149
contentHashRowCount            381,149/381,149
sourceDataAsOfRowCount         381,149/381,149
adapterVersionRowCount         381,149/381,149
exactTextLocatorRowCount                     0
exactTableLocatorRowCount                    0
exactTimeRowCount                            0
immutableSourceVersionRowCount               0
semanticDirectionRowCount                    0
assertionEvidenceReadyRowCount               0
reviewedPositiveCount                    0/100
reviewedHardNegativeCount                0/100
publicTransferMetricsReady               false
syntheticRegression                        8/8 PASS
liveReady                                false
```

판정: Existing search catalog는 document와 section 수준의 exact lookup 후보로는 완전하지만 assertion-grade evidence는 아니다. Whole-section sourceRef, content hash, dataAsOf, adapter version을 char span, table row/header, availability timestamp, immutable source bytes version으로 확대 해석하지 않는다. Synthetic resolver는 text와 table positive를 해소하고 wrong entity, wrong predicate, unknown direction, missing time, mutable version, altered locator, multiple exact source를 모두 fail closed했다. Resolver contract는 합격이지만 reviewed 100 및 100 gold, live exact field, public cold 및 incremental transfer가 없어 live evidence admission은 `revise`로 차단한다.

## 4.9 U0-O01 결과

명령:

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/ontology/assertionContract.py
```

결과:

```text
edgeCount                         20,560
uniqueRelationCandidateCount      20,560
selfLoopCount                         13
assertionIdCount                       0
supersedesCount                        0
exactEvidenceCount                     0
sourcePublishedAtCount                 0
availableAtCount                       0
validFromCount                         0
validToCount                           0
admittedStatusCount                    0
assertionReadyCount                    0
syntheticRegression                  9/9 PASS
historyLossCount                       0
futureKnowledgeLeakCount               0
liveReady                           false
```

판정: Relation ID는 subject, predicate, object, direction의 canonical hash로 고정하고 assertion ID는 filing evidence, source snapshot, source time, validity, event, status, supersedes를 추가로 결속했다. Evidence 입력 순서와 query knownAt은 assertion identity를 바꾸지 않는다. Correction은 predecessor를 ledger에서 삭제하지 않고 같은 relation의 단방향 lineage로만 연결한다. Production `Ref` exact payload와 `VintageRef`의 asKnown 및 asOfExact를 그대로 통과했다. Synthetic contract는 합격이다. 그러나 public 20,560 edge에는 assertion source field가 모두 0이고 self-loop 13개가 남아 있어 live admission은 `revise`다. Current edge는 relation candidate lane에만 둔다.

## 4.10 U0-P01 결과

명령:

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/projection/boundedProjection.py
```

결과:

```text
scene                  input node/edge    bound node/edge    output node/edge
atlas                          34/50              34/50              18/35
semiconductor industry       125/85              50/80              26/34
Samsung company             178/218              50/80              50/60

candidateInputEdges             303
derivedInputEdges                50
factInputEdges                    0
repeatedSceneHash               3/3
hardBoundViolation                0
seedLoss                         0
laneViolation                     0
syntheticRegression             8/8 PASS
boundedProjectionLiveReady      true
```

판정: Current public artifact 3종을 bytes hash로 묶은 SourceSnapshotSet과 같은 generic compiler를 사용해 새 bake 없이 bounded logical scene을 만들었다. Depth, lane, explicit priority와 stable edge ID로 truncation하고 생략 수와 이유를 receipt에 남겼다. Reverse input에서도 scene hash 3/3이 일치했고 hard bound, seed retention, dangling edge, lane admission 위반은 0이었다. Atlas aggregate flow 50개는 derived, industry와 company relation 303개는 candidate로 유지했으며 fact는 0이다. U0-P01은 `promote`다. 이 결론은 bounded projection compiler에만 해당하며 evidence 및 visual gate를 우회하지 않는다.

## 4.11 U0-V01 결과

명령:

```powershell
node tests/_attempts/dartlabUniverse/visual/visualGrammarProbe.mjs
```

결과:

```text
stateCount                         7
cardCount                         30
uniqueNonColorSignatureCount      7/7
colorOnlyCollisionCount             0
evidenceAffordanceCoverage       30/30
ariaCoverage                     30/30
renderedCardCount                30/30
confidenceOpacityUsageCount          0
machineRegression                  8/8 PASS
reviewedParticipantCount          0/12
reviewedResponseCount            0/360
comprehensionAccuracy       unmeasured
contractReady                      true
comprehensionReady                false
liveReady                         false
```

판정: Fact, candidate, derived, disputed, retracted, scenario, unknown은 color를 제외한 stroke, pattern, glyph, label, evidence action, aria phrase 조합으로 7/7 분리했다. Confidence는 opacity와 분리해 badge 및 marker로만 표현한다. Deterministic 30-card answer key, semantic DOM reference, participant별 30문항 completeness, reviewer와 reviewedAt gate를 구현했고 machine contract 8/8은 합격이다. 그러나 실제 participant와 reviewed response가 0이므로 판독 90%는 미측정이다. U0-V01은 `revise`이며 participant 12명과 360개 review 전 production visual admission을 차단한다.

## 4.12 U0-V02 결과

명령:

```powershell
uv run python -X utf8 -m tests._attempts.dartlabUniverse.visual.liveLayoutFixture --compact
node --test tests/_attempts/dartlabUniverse/visual/testDeterministicLayoutProbe.mjs
node tests/_attempts/dartlabUniverse/visual/deterministicLayoutProbe.mjs --live
tests/_attempts/dartlabUniverse/visual/browserLayoutAudit.ps1
```

결과:

```text
liveSceneCount                         3
atlasNodeCount                       18
industryNodeCount                    26
companyNodeCount                     50
totalNodeCount                       94
validTimeKnownCount                0/94
validTimeUnknownCount             94/94
logicalHashRepeat                  60/60
threeViewportAnchorHash          180/180
browserMeasurement               180/180
browserLogicalHash               180/180
browserAnchorHash                180/180
browserViewportAndDpr            180/180
maximumAnchorDriftPx                    0
forceIterationCount                    0
nodeRegression                    10/10 PASS
pythonRegression                    2/2 PASS
layoutContractReady                   true
```

판정: U0-P01 live bounded projection 세 장면을 renderer 독립 logical coordinate로 투영했다. Industry stage는 semantic x anchor, valid order와 time unknown은 y anchor, evidence status는 stable offset이며 force iteration은 0이다. Input 순서를 scene별 20회 교란해 logical hash 60/60과 세 viewport anchor 180/180이 같았고 Chrome, Firefox, WebKit의 180회 실측 최대 drift는 0px였다. Current artifact의 valid time은 0/94이므로 임의 순서를 합성하지 않고 94개를 unknown time lane으로 보존했다. U0-V02 layout contract는 `promote`지만 실제 시간 판독과 visual comprehension 및 production admission은 계속 차단한다.

## 4.13 U0-V03 결과

명령:

```powershell
node --check tests/_attempts/dartlabUniverse/visual/densityOmissionProbe.mjs
node --test tests/_attempts/dartlabUniverse/visual/testDensityOmissionProbe.mjs
node tests/_attempts/dartlabUniverse/visual/densityOmissionProbe.mjs
```

결과:

```text
densityCaseCount                         6
budgetCompliantCases                   6/6
exactOmissionReceiptCases              6/6
reverseInputReceiptHash                6/6
maximumCalculatedLabelCollision          0%
maximumDomLabelCollision                 0%
desktop1000ActiveNode                500/500
desktop1000ActiveEdge              1,000/1,000
desktop1000VisibleLabel               57/80
desktop1000OmittedNode                  500
mobile1000ActiveNode                 250/250
mobile1000ActiveEdge                 500/500
mobile1000VisibleLabel                 40/40
mobile1000OmittedNode                    750
machineRegression                      8/8 PASS
densityContractReady                      true
```

판정: 250, 500, 1,000 node fixture에 desktop 500 node, 1,000 edge, 80 label과 mobile 250 node, 500 edge, 40 label 상한을 적용했다. Stable priority와 semantic anchor로 active representation을 고르고 계산 rectangle 및 실제 1280x720, 390x844 DOM에서 label collision은 0%였다. Node, edge, label omission은 budget, omitted endpoint, collision reason으로 6/6 전부 설명했고 reverse input receipt hash도 6/6 일치했다. Aggregate receipt는 omitted member, status count, coverage, quantile, top changes를 보존한다. U0-V03 density contract는 `promote`지만 FPS, heap, hit-test, accessibility와 renderer bakeoff는 아직 미측정이다.

## 4.14 U0-V04 결과

명령:

```powershell
node --check tests/_attempts/dartlabUniverse/visual/bitemporalComprehensionProbe.mjs
node --test tests/_attempts/dartlabUniverse/visual/testBitemporalComprehensionProbe.mjs
node tests/_attempts/dartlabUniverse/visual/bitemporalComprehensionProbe.mjs
```

결과:

```text
revisionTaskCount                         12
answerCombinationCount                  4/4
separateControlCoverage               12/12
combinedSliderUsageCount                   0
ariaCoverage                          12/12
renderedTaskCount                     12/12
machineRegression                       9/9 PASS
reviewedParticipantCount               0/12
reviewedTaskResponseCount              0/144
reviewedAxisAnswerCount                0/288
validAtAccuracy                   unmeasured
knownAtAccuracy                   unmeasured
combinedAccuracy                  unmeasured
contractReady                           true
comprehensionReady                     false
liveReady                              false
```

판정: 미래 효력 선공시, 과거 사건 지연 공시, open interval, inclusive boundary, sourcePublishedAt과 availableAt 차이를 포함한 12개 task에서 valid 및 known answer 네 조합을 모두 만들었다. Query validAt과 knownAt은 assertion identity에 들어가지 않고 reality와 knowledge control, DOM fieldset, aria phrase로 독립 표현된다. Synthetic perfect review는 scoring contract test에만 쓰며 live 결과가 아니다. 실제 participant와 response가 0이므로 U0-V04는 `revise`이며 두 축과 combined accuracy가 각각 90%를 넘기 전 production Time Lens admission을 차단한다.

## 4.15 U0-V05 결과

명령:

```powershell
node --check tests/_attempts/dartlabUniverse/visual/accessibilityEquivalenceProbe.mjs
node --test tests/_attempts/dartlabUniverse/visual/testAccessibilityEquivalenceProbe.mjs
node tests/_attempts/dartlabUniverse/visual/accessibilityEquivalenceProbe.mjs
```

결과:

```text
coreActionCount                            6
surfaceCount                               2
profileCount                               6
commandParity                            6/6
uniqueFocusIdCount                     12/12
keyboardNativeCoverage                 12/12
screenReaderSummaryCoverage            12/12
syntheticProfileTask                    36/36
browserSpatialKeyboardTask                6/6
browserTableKeyboardTask                  6/6
reducedMotionDuration                       0s
highContrastNonColorCoverage              6/6
zoom200HorizontalOverflow               false
mobileLowGpuTableTask                      6/6
mobileLowGpuSpatialSurface                   0
spatialOnlyActionCount                        0
machineRegression                        11/11 PASS
accessibilityContractReady                 true
namedScreenReaderManualSession       unmeasured
productionReady                           false
```

판정: 여섯 핵심 action은 spatial DOM과 relation table에서 같은 command, native keyboard control, screen reader summary와 polite status를 제공했다. 실제 browser keyboard task는 두 surface에서 각각 6/6, reduced motion 0s, high contrast non-color treatment 6/6, 200% zoom horizontal overflow 없음, 390x844 low GPU table fallback 6/6이며 spatial-only action은 0이다. U0-V05 접근성 동등 경로 계약은 `promote`한다. 다만 browser accessibility tree 검증은 실제 named screen reader 수동 session을 대체하지 않으므로 production admission은 `revise`로 차단한다.

## 4.16 U0-V06 결과

명령:

```powershell
node --check tests/_attempts/dartlabUniverse/visual/rendererBakeoffProbe.mjs
node --check tests/_attempts/dartlabUniverse/visual/rendererBakeoffBrowser.mjs
node --test tests/_attempts/dartlabUniverse/visual/testRendererBakeoffProbe.mjs
node tests/_attempts/dartlabUniverse/visual/rendererBakeoffProbe.mjs
```

결과:

```text
desktopFixture                    500 node / 1,000 edge
mobileFixture                       250 node / 500 edge
rendererCount                                         4
trialCountPerRenderer                                 3
desktopTaskReady                                    4/4
mobileTaskReady                                     4/4
desktopPerformanceReady                             4/4
mobilePerformanceReady                              4/4
desktopMinimumFrameP95                       138.889fps
mobileMinimumFrameP95                        135.135fps
builtinPortfolioRawGzip                  17,438B / 5,770B
cosmosIncrementalRawGzip               311,453B / 91,863B
cosmosPortfolioRawGzip                 328,891B / 97,633B
canvas2dIncrementalDependencyBytes                       0
canvasDesktopHeap                              10,645,237B
cosmosDesktopHeap                              14,703,331B
canvasMobileHeap                               10,840,050B
cosmosMobileHeap                               11,389,243B
currentCosmosLicense                           CC-BY-NC-4.0
currentCosmosLicenseReady                              false
candidatePromoted                                      true
newExternalDependencyRequired                          false
machineRegression                                     7/7 PASS
rendererContractReady                                  true
productionReady                                       false
```

판정: SVG, current Cosmos 1.6.1, DOM relation table, Canvas 2D가 desktop과 mobile bounded fixture 및 핵심 task를 100% 보존했고 frame과 heap 예산도 8/8 통과했다. Canvas 2D는 두 환경에서 Cosmos보다 최종 heap이 낮고 외부 dependency가 0이다. Built-in 포트폴리오 bundle은 Cosmos 포함 포트폴리오의 약 5.3%다. U0-V06은 dependency-free Canvas 2D를 `promote`하고 새 external renderer dependency를 기각한다. Current Cosmos는 locked license가 `CC-BY-NC-4.0`이므로 Universe production admission은 false다. 기존 map renderer는 attempt 범위 밖이라 변경하지 않는다.

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
