# 06. Progress Ledger

## 현재 상태

- [x] 저장소 운영 규칙과 Skill OS의 architecture, API, UI, data lineage, testing 계약 재확인
- [x] HF repository 68,199파일 전수 byte 계수
- [x] staging, compatibility, active 수명주기 분리
- [x] capability, Skill OS, Analysis Graph, core engine axis 계수
- [x] live map meta, ecosystem, company egograph 실측
- [x] DART 및 EDGAR panel schema 동형 확인
- [x] current relation source, type, evidence, degree, self-loop 전수 감사
- [x] `OCI` hub 오탐 원인 확인
- [x] existing search sidecar, DataCore, range runtime, entity graph sidecar 재사용 경계 확인
- [x] product, ontology, runtime, UX, execution, 3-year maintenance 설계
- [x] `/universe` 독립 public route 결정
- [x] P0~U6 work packet과 commit 및 rollback 순서 작성
- [x] attempts evidence matrix와 기존 world/search 실험 재사용 지도 작성
- [x] `/universe` public beta, GA, 장기 route 운영 계약 작성
- [x] U0 attempts category 생성
- [x] U0-T01 current graph truth census 실행
- [x] 제품 혁신, 시각 혁신, 기술 및 증거 관점 교차 토론
- [x] P0 변화 우주와 Thesis Kill-Chain, P1 판정 우주와 한미 Twin 우선순위 확정
- [x] SourceSnapshotSet, UniverseFlightPlan, UniverseFlightReceipt, SceneBeat, EvidenceReceipt, GapReceipt 계획 계약 확정
- [x] snapshot, workflow, visual, policy attempts 하위 category 생성
- [x] U0-T02 graph factual admission 강화
- [x] U0-S01 SourceSnapshotSet과 legacy replay guard
- [x] U0-P02 RedistributionReceipt와 upstream public admission guard
- [x] U0-L01 6 output archetype과 환경별 LensAvailability guard
- [x] U0-W01 append-only change replay 계약과 live DART readiness census
- [x] U0-W02 generic recipe workflow projection과 live conclusion gate
- [x] U0-I01 canonical entity, security, filing ID와 live historical identity census
- [x] U0-E01 exact document evidence resolver와 live search catalog census
- [x] U0-O01 assertion identity, append-only lineage, bitemporal query contract
- [x] U0 identity, evidence, assertion, projection attempts
- [x] U0-P01 bounded projection live atlas, industry, company 3-scene validation
- [x] U0-V01 non-color visual grammar와 30-card comprehension scoring contract
- [x] U0-V02 live 3-scene deterministic logical layout와 cross-browser anchor contract
- [ ] U0 workflow, visual, information yield attempts
- [ ] U1~U2 implementation
- [ ] U3 artifact 변경 승인 여부
- [ ] UI 눈검수 및 push 승인

## 결정 원장

| 날짜 | 결정 | 근거 |
|---|---|---|
| 2026-07-15 | 제품명은 DartLab Universe | ontology는 내부 physics, universe는 사용자 surface |
| 2026-07-15 | 276GB 전량 graph copy 기각 | staging 153.91GB, compatibility 63.66GB, active 58.19GB |
| 2026-07-15 | 새 public engine 기각 | 기존 226 capability와 147 core axes 재사용 |
| 2026-07-15 | relation과 assertion 분리 | current `(from,to,type)` dedup이 시간 및 revision 손실 |
| 2026-07-15 | existing edge는 candidate hint | sourceRef 및 time 0, OCI 4,474 edge 오탐 |
| 2026-07-15 | Evidence on Demand 우선 | exact BM25 range와 panel source가 이미 존재 |
| 2026-07-15 | U3는 승인 게이트 | runtime SSOT 우선, 새 bake 무승인 금지 |
| 2026-07-15 | 2D 기본, 3D optional | 분석, 모바일, 접근성, vendor 독립성 |
| 2026-07-15 | `/universe` 독립 route | ontology, evidence, time, lens는 시장 지도와 다른 제품 작업. runtime과 artifact를 공유해 중복 방지 |
| 2026-07-15 | 3년 운영 모델 포함 | schema, owner, deprecation, quality, incident, cost를 제품 계약으로 승격 |
| 2026-07-15 | U0-T01 attempt 실행 | 현재 HF graph에서 sourceRef 및 availableAt을 모두 가진 observed 적격 edge 0 |
| 2026-07-15 | P0는 변화 우주와 Thesis Kill-Chain | 변화는 공시 및 관측의 시간 자산, Kill-Chain은 recipe의 requiredEvidence와 falsifier를 직접 제품 가치로 전환 |
| 2026-07-15 | P1은 판정 우주와 한미 Twin | scan의 PASS, FAIL, MISSING과 DART, EDGAR 동형 panel이 DartLab 고유 자산 |
| 2026-07-15 | Evidence Shock Theater P0 및 P1 기각 | current edge는 factual causal path가 아니고 기존 BFS와 임의 감쇠는 evidence admission이 없음 |
| 2026-07-15 | 전량 3D 점구름 기각 | 정보 수율, 접근성, evidence 판독, runtime ROI가 없음 |
| 2026-07-15 | SourceSnapshotSet 도입 | 단일 map buildId는 search, panel, finance, capability, recipe exact replay를 보장하지 못함 |
| 2026-07-15 | query knownAt을 assertion identity에서 제거 | 미래 효력 공시를 허용하고 같은 assertion이 query cutoff마다 다른 ID가 되는 오류 방지 |
| 2026-07-15 | 시각은 의미 좌표와 L0~L5 representation 교체 | current map의 무작위 force와 화면 전체 복제 대신 SVG, bounded Cosmos, DOM reference surface 분리 |
| 2026-07-15 | U0-T02 factual admission 실행 | live 20,560 edge에서 document ID, section, exact locator, direction, sourcePublishedAt, availableAt, validFrom, policy receipt, observed status와 admitted 모두 0 |
| 2026-07-15 | U0-S01 SourceSnapshotSet 실행 | source 10개 중 HF 8개와 recipe Git blob 1개는 immutable, live capability catalog 1개는 manifest 부재로 unreplayable. 같은 set hash 2/2 일치, legacy buildId exact replay 차단 |
| 2026-07-15 | U0-P02 RedistributionReceipt 실행 | live reviewed receipt 0/10으로 publicReady false. synthetic 12건에서 unknown, localOnly, blocked, expired, prohibited, metadataOnly 확대와 금지 upstream false accept 0 |
| 2026-07-15 | U0-L01 LensAvailability 실행 | capability 226개에 runtime, archetype, unit, coverage, missing 선언 0. Skill OS 286개에 publicBrowser 선언 0. synthetic 6 archetype 및 3환경 8건 통과, current public lens ready 0 |
| 2026-07-15 | U0-W01 change replay 실행 | synthetic revision 8/8 보존, 다섯 변화 각 1, look-ahead 0, evidence 5/5, 미래 metadata 누출 0. live DART 30개는 filing ID만 30/30이고 exact time, revisionId, rowKey 0/30이라 public exact replay 차단 |
| 2026-07-15 | U0-W02 workflow projection 실행 | tested recipe 정렬 앞 10개의 procedure 80, requiredEvidence 60, negative candidate 29를 100% 보존, hash 10/10, adapter와 fact promotion 0. qualified falsifier 0이라 live conclude 0 유지 |
| 2026-07-15 | U0-I01 canonical identity 실행 | KR 및 US entity와 filing exact 160/160, KRX ISIN 2,872/2,872, ambiguous selectedId 0. KRX issuer gap 130, historical validity KR 및 US 0, local US filing issuer 2라 live historical registry 차단 |
| 2026-07-15 | U0-E01 exact evidence 실행 | Search catalog 381,149행의 document, section, sourceRef, content hash는 100%지만 exact text span, table row/header, exact time, row source version, predicate/direction은 0. Synthetic 8/8 통과, reviewed gold와 transfer 미측정으로 live assertion evidence 차단 |
| 2026-07-15 | U0-O01 assertion ontology 실행 | Relation과 assertion ID, append-only correction, validAt과 knownAt, Ref와 VintageRef 결속을 synthetic 9/9로 확정. Public edge 20,560은 relation candidate로 unique하지만 assertion ID, evidence, source time, validity, admitted status, ready 모두 0이고 self-loop 13이라 fact lane 차단 |
| 2026-07-15 | U0-P01 bounded projection 실행 | 새 bake 없이 atlas 18/35, 반도체 26/34, 삼성 egograph 50/60 node/edge로 bounded projection. Reverse input hash 3/3, bound, seed, lane violation 0. Candidate 303, derived 50, fact 0을 보존해 compiler는 promote |
| 2026-07-15 | U0-V01 visual grammar 실행 | 7개 status의 non-color signature 7/7, evidence와 aria 30/30, confidence opacity 0, DOM card와 scoring test 8/8. 실제 participant 0/12와 response 0/360이라 comprehension 90%는 미측정, production visual admission 차단 |
| 2026-07-16 | U0-V02 deterministic layout 실행 | Live Atlas 18, industry 26, company 50 node를 20회씩 순서 교란해 logical hash 60/60, 세 viewport anchor 180/180. Chrome, Firefox, WebKit 180회 실측 hash 180/180, 최대 drift 0px. Valid time 0/94는 합성하지 않고 unknown lane으로 보존해 layout contract promote |

## 핵심 실측 스냅샷

```text
HF total                 68,199 files / 275,755,437,729 bytes
search staging           2,173 files / 153,910,337,279 bytes
compatibility surfaces  11,344 files / 63,656,962,973 bytes
active and other        54,682 files / 58,188,137,477 bytes
current map              2,664 nodes / 20,560 edges / 34 industries
map ecosystem            6,015,606 bytes
map atlas                27,517 bytes
company payload total   79,517,001 bytes
capabilities             226
skills                   286
core dispatch axes       147
panel_text edges          17,400
panel_table edges            208
self loops                    13
OCI incident edges         4,474
exact edge sourceRef            0
snapshot sources               10
immutable snapshot sources      9
unreplayable sources             1 capabilityCatalog
snapshot hash repeat           2/2
reviewed policy receipts        0/10
public policy ready            false
policy negative false accept       0
capability return contracts       83/226
capability lens declarations       0/226
Skill OS publicBrowser              0/286
current public lens ready               0
synthetic replay revisions            8/8
synthetic replay change types         5/5
synthetic replay look-ahead              0
synthetic replay evidence             5/5
DART replay sample files                30
DART replay sample rows            359,115
DART rcept_no coverage               30/30
DART sourcePublishedAt coverage       0/30
DART availableAt coverage             0/30
DART revisionId coverage              0/30
DART rowKey coverage                  0/30
DART observed revision groups             0
DART live exact replay ready          false
recipes                                 156
tested recipes                           30
tested complete workflow contract        22
workflow sample recipes                  10
workflow procedure preserved          80/80
workflow required evidence accounted  60/60
workflow falsifier candidates         29/29
workflow qualified falsifiers              0
workflow evidence gaps                    60
workflow live conclusions                  0
workflow flight hash repeat            10/10
workflow dedicated adapters                0
workflow model fact promotions             0
identity exact sample                160/160
KRX ISIN security              2,872/2,872
KRX security issuer links      2,742/2,872
KRX security issuer gaps               130
US multi-security CIK                1,473
KR historical validity fields            0
US historical validity fields            0
US local filing issuers                   2
identity ambiguous auto resolve           0
historical identity ready             false
search catalog rows                 381,149
search section locator          381,149/381,149
search content hash            381,149/381,149
exact text locator                          0
exact table row and header                  0
exact evidence time                         0
row immutable source version                0
evidence predicate and direction            0
assertion evidence ready                     0
reviewed evidence positive               0/100
reviewed evidence hard negative          0/100
synthetic evidence regression              8/8
public evidence transfer measured        false
graph relation candidate unique   20,560/20,560
graph assertion ID                           0
graph supersedes link                        0
graph exact evidence                         0
graph sourcePublishedAt                      0
graph availableAt                            0
graph validFrom                              0
graph admitted status                        0
graph assertion ready                        0
synthetic assertion regression             9/9
synthetic assertion history loss             0
synthetic future knowledge leak               0
atlas projection input                    34/50 nodes/edges
atlas projection output                   18/35 nodes/edges
industry projection input                125/85 nodes/edges
industry projection output                26/34 nodes/edges
company projection input                178/218 nodes/edges
company projection output                 50/60 nodes/edges
projection candidate edges                  303
projection derived edges                      50
projection fact edges                          0
projection repeated hash                     3/3
projection bound violations                    0
projection seed loss                           0
projection lane violations                     0
synthetic projection regression              8/8
visual grammar states                         7/7
visual deterministic cards                  30/30
visual non-color signatures                   7/7
visual color-only collisions                    0
visual evidence affordance                  30/30
visual aria coverage                        30/30
visual confidence opacity usage                 0
visual machine regression                     8/8
visual reviewed participants                  0/12
visual reviewed responses                    0/360
visual comprehension accuracy           unmeasured
layout live scenes                              3
layout live nodes                              94
layout valid time known                      0/94
layout valid time unknown                   94/94
layout logical hash repeat                  60/60
layout three-viewport anchor repeat        180/180
layout browser measurements                180/180
layout browser maximum drift                   0px
layout force iterations                          0
```

같은 날 후속 live meta 재감사:

```text
map buildId              20260715-084444
map commitSha            bc10468
ecosystem bytes          6,015,104
atlas bytes                 27,517
industryStats bytes        244,656
search index bytes          306,450
company payload bytes    79,532,356
finance dataAsOf         2026-07-15T08:37:55Z
dart dataAsOf            null
```

최초 감사 수치는 지우지 않는다. 후속 snapshot은 SourceSnapshotSet 필요성을 강화하는 갱신 기록이다.

## 외부 기술 사실

- [HF dataset card](https://huggingface.co/datasets/eddmpython/dartlab-data): 276GB, CC BY 4.0, KR 약 2,700사와 US 약 1,000사, Parquet 직접 접근
- [hyparquet](https://github.com/hyparam/hyparquet): browser HTTP range, row 및 column projection
- [Cosmograph library docs](https://cosmograph.app/docs-lib/): Parquet와 browser graph rendering 가능. 본 계획은 current cosmos renderer를 adapter 뒤에 두며 full product 종속을 전제하지 않음

## 구현 전 blocker

1. U0 gold positive 및 hard negative set이 없다.
2. exact evidence resolver의 cold P95와 cold initialization 포함 transfer가 아직 측정되지 않았다.
3. source version 10개는 SourceSnapshotSet으로 묶였지만 capability catalog의 immutable manifest가 없고 panel dataAsOf가 null이다. 따라서 current public exact replay는 아직 금지한다.
4. RedistributionReceipt와 LensAvailability admission contract는 있지만 reviewed receipt는 0/10, Skill OS publicBrowser 선언은 0/286, current public lens ready는 0이다. map field의 upstream policy lineage도 결속되지 않았다.
5. DART finance 정렬 앞 30개, 359,115 row에 rcept_no는 있지만 sourcePublishedAt, availableAt, revisionId, rowKey가 0/30이고 observed revision group도 0이다. U0-W01 synthetic 계약은 통과했지만 live 변화 우주 exact replay는 금지한다.
6. Tested recipe 30개에 explicit falsifier field가 없고 selected 10개의 qualified falsifier는 0이다. U0-W02 compiler는 candidate 29개를 보존하지만 verificationRefs와 execution evidence 전까지 live Kill-Chain conclude를 만들지 않는다.
7. KRX security 130개는 DART issuer exact link가 없고 KR 및 US alias validity field는 0이다. U0-I01 exact ID contract는 통과했지만 historical identity registry는 reference owner 보강 전 금지한다.
8. Search catalog 381,149행은 section sourceRef와 content hash를 모두 갖지만 exact span, table row/header, publication 및 availability timestamp, row-level immutable source version, predicate와 direction은 0이다. U0-E01 resolver 계약은 통과했지만 reviewed positive 100, hard negative 100과 public transfer 측정 전 live assertion evidence는 금지한다.
9. Public ecosystem 20,560 relation candidate는 unique하지만 assertion ID, supersedes, exact evidence, source time, validity와 admitted status가 전부 0이다. U0-O01 synthetic contract는 통과했지만 current edge의 fact lane 입장은 계속 0이다.
10. U0-P01 bounded projection은 live 3-scene에서 통과했지만 fact edge는 0이다. U0-V01~V05 comprehension과 accessibility가 완료되기 전 public UI production 이관은 금지한다.
11. U0-V01 grammar machine contract는 통과했지만 reviewed participant는 0/12, reviewed response는 0/360이고 comprehension accuracy는 미측정이다. 실제 review 전 시각 문법 합격을 주장하지 않는다.
12. U0-V02 layout contract는 통과했지만 current live node의 valid time은 0/94다. Unknown time lane을 보존하고 U0-V04 전 실제 시간 순서를 주장하지 않는다.
13. `scan-screener-os`의 public valuation licensing P0가 승인 대기다. Universe는 해당 필드를 사용하지 않아야 한다.
14. workspace의 landing 및 ui 대량 삭제는 본 작업과 무관한 기존 변경이다. U1 production 착수 전에 frontend host가 정상 상태인지 재검해야 한다.

## 다음 단일 행동

`tests/_attempts/dartlabUniverse/visual/`에서 U0-V03 density and omission probe를 구현한다. 250, 500, 1,000 node deterministic fixture에서 label collision, active node 및 edge 상한, LOD 축소, omitted count와 reason receipt를 측정한다. 전체 node를 무조건 표시하지 않고 desktop 및 mobile budget별 lower LOD가 숨긴 항목을 100% 설명해야 한다.
