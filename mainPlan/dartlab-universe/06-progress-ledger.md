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
- [ ] U0 identity, evidence, assertion, projection attempts
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
6. `scan-screener-os`의 public valuation licensing P0가 승인 대기다. Universe는 해당 필드를 사용하지 않아야 한다.
7. workspace의 landing 및 ui 대량 삭제는 본 작업과 무관한 기존 변경이다. U1 production 착수 전에 frontend host가 정상 상태인지 재검해야 한다.

## 다음 단일 행동

`tests/_attempts/dartlabUniverse/workflow/`에서 U0-W02 workflow projection probe를 구현한다. tested recipe 10개의 procedure, requiredEvidence, falsifier를 orient, focus, evidence, falsify, conclude `SceneBeat[]`로 lossless compile한다. missing required evidence는 GapReceipt로 보존하고 open falsifier가 없는 conclude를 차단한다. same input flight hash 불일치 또는 단계, 근거, 반증 유실 1건이면 Kill-Chain production 이관을 금지한다.
