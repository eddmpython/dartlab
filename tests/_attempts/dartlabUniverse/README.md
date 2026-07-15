# DartLab Universe attempts

> 상태: U0 진행 중. production 배선 금지
> 목적: Universe의 신규 의미 계약을 실데이터로 반증하고, 통과한 계약만 본진에 이관한다.

## 카테고리 한 줄

현재 HF truth와 기존 엔진을 이용해 entity, assertion, evidence, time, source snapshot, workflow, visual grammar, public policy, bounded projection의 제품 적격성을 순서대로 검증한다.

## 하위 책임

| category | 책임 |
|---|---|
| `truth/` | current graph 센서스와 factual admission |
| `snapshot/` | SourceSnapshotSet과 change replay |
| `workflow/` | recipe, SceneBeat, falsifier, information yield |
| `visual/` | 상태 판독, layout, density, 접근성, renderer bakeoff |
| `fixtures/` | reviewed release gold admission, quota, precision, false acceptance |
| `policy/` | RedistributionReceipt와 LensAvailability |
| `identity/`, `evidence/`, `ontology/`, `projection/` | canonical ID, exact source, assertion, bounded scene |

## 졸업 순서

1. 카테고리와 가설 원장 확정
2. 현재 공개 graph truth census
3. graph admission 강화와 SourceSnapshotSet
4. public policy receipt와 LensAvailability
5. canonical entity와 exact evidence resolution
6. assertion, revision, time contract와 change replay
7. bounded projection과 deterministic scene
8. recipe workflow와 visual qualification
9. public runtime latency, transfer, information yield
10. cross-market conformance와 optional 3D uplift
11. 덕지덕지 제거와 9섹션 docstring 확정
12. reviewed gold와 hard negative 통과 후에만 production 후보 이관

상세 실험 순서와 판정값은 [mainPlan의 attempts matrix](../../../mainPlan/dartlab-universe/08-attempts-evidence-matrix.md)가 정본이다.

## 실행 가능한 첫 근거

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/truth/graphTruthProbe.py
uv run python -X utf8 tests/_attempts/dartlabUniverse/truth/factualAdmissionProbe.py
uv run python -X utf8 tests/_attempts/dartlabUniverse/snapshot/sourceSnapshotSetProbe.py
uv run python -X utf8 tests/_attempts/dartlabUniverse/snapshot/changeReplayProbe.py
uv run python -X utf8 tests/_attempts/dartlabUniverse/policy/redistributionReceiptProbe.py
uv run python -X utf8 tests/_attempts/dartlabUniverse/policy/lensAvailabilityProbe.py
uv run python -X utf8 tests/_attempts/dartlabUniverse/workflow/workflowProjectionProbe.py
uv run python -X utf8 tests/_attempts/dartlabUniverse/identity/entityIdentityProbe.py
uv run python -X utf8 tests/_attempts/dartlabUniverse/evidence/exactEvidenceProbe.py
uv run python -X utf8 tests/_attempts/dartlabUniverse/ontology/assertionContract.py
uv run python -X utf8 tests/_attempts/dartlabUniverse/projection/boundedProjection.py
node tests/_attempts/dartlabUniverse/visual/visualGrammarProbe.mjs
node tests/_attempts/dartlabUniverse/visual/deterministicLayoutProbe.mjs --live
tests/_attempts/dartlabUniverse/visual/browserLayoutAudit.ps1
node tests/_attempts/dartlabUniverse/visual/densityOmissionProbe.mjs
node tests/_attempts/dartlabUniverse/visual/bitemporalComprehensionProbe.mjs
node tests/_attempts/dartlabUniverse/visual/accessibilityEquivalenceProbe.mjs
node tests/_attempts/dartlabUniverse/visual/rendererBakeoffProbe.mjs
uv run python -X utf8 tests/_attempts/dartlabUniverse/fixtures/releaseGoldProbe.py
uv run python -X utf8 tests/_attempts/dartlabUniverse/fixtures/releaseGoldReviewQueueProbe.py
uv run python -X utf8 tests/_attempts/dartlabUniverse/fixtures/releaseGoldSourceBindingProbe.py
uv run python -X utf8 tests/_attempts/dartlabUniverse/fixtures/releaseGoldReviewPromotionProbe.py
```

pytest는 repository test lock을 획득한 뒤 attempt test file 하나씩 실행한다.

## 현재 결론 원장

| attempt | 입력 | 실측 | 판정 |
|---|---|---|---|
| U0-T01 graph truth census | HF `landing/map/ecosystem.json`, version `2026-04-14` | node 2,664, edge 20,560, self-loop 13, exact sourceRef 0, exact availableAt 0, observed 적격 0, OCI incident 4,474 | 기존 edge는 fact가 아니라 candidate hint. assertion/evidence 계약 선행 |
| U0-T02 factual admission | 같은 live ecosystem 20,560 edge | document ID, section, exact locator, direction, sourcePublishedAt, availableAt, validFrom, policy receipt, observed status, admitted 모두 0. self-loop 13 | current edge 전부 candidate 유지. exact evidence resolver와 assertion source가 별도로 필요 |
| U0-S01 SourceSnapshotSet | HF 8 source, capability, recipe catalog | source 10, immutable 9, capability catalog unreplayable 1, panel dataAsOf 결손 1, receipt 결손 10, hash 반복 2/2, unit 8/8 | source identity 계약 완료. capability manifest 전까지 public exact replay 금지, U0-P02로 진행 |
| U0-P02 RedistributionReceipt | U0-S01 source 10개와 synthetic policy fixture | live receipt 0/10, publicReady false, synthetic 12/12 PASS, unknown, localOnly, blocked, expired, prohibited, mixed upstream false accept 0 | policy admission 계약 완료. 운영자 reviewed receipt와 upstream field lineage 전까지 live source lane 차단 |
| U0-L01 LensAvailability | capability 226, Skill OS 286, 6 archetype fixture | capability lens semantic 및 runtime 선언 0, Skill OS publicBrowser 0, current public lens ready 0, synthetic 8/8 PASS | generic lens 계약 완료. explicit LensSpec registry와 receipt 전까지 public lens 0 유지 |
| U0-W01 change replay | append-only revision 8개와 DART finance 정렬 앞 30개 | synthetic 다섯 변화 각 1, revision 8/8, look-ahead 0, evidence 100%, test 8/8. live 359,115 row에서 rcept_no 30/30, exact time, revisionId, rowKey 0/30, revision group 0 | replay 계약 완료. live exact 변화 재생은 source field와 reviewed multi-filing fixture 전까지 차단 |
| U0-W02 workflow projection | tested recipe ID 정렬 앞 10개와 synthetic qualified fixture | procedure 80, requiredEvidence 60, negative candidate 29 전부 보존, hash 10/10, adapter 0, test 8/8. qualified falsifier 0, evidence gap 60, live conclude 0 | generic compiler 계약 완료. explicit falsifier와 execution evidence 전까지 live Kill-Chain 결론 차단 |
| U0-I01 canonical identity | DART legal master, KRX security, SEC ticker, KR 50, US 30, filing sample | entity와 filing exact 160/160, KRX ISIN 2,872/2,872, ambiguity auto resolve 0, test 9/9. KRX issuer gap 130, alias validity KR 0 및 US 0, US local filing issuer 2 | canonical ID 계약 완료. reference issuer link, validity, reviewed special-case gold 전까지 live historical registry 차단 |
| U0-E01 exact evidence | DART panel, EDGAR panel, allFilings search catalog 381,149행과 synthetic text 및 table fixture | document, section, sourceRef, contentHash 381,149/381,149. exact span, table row/header, exact time, row source version, predicate/direction, assertion-ready 0. synthetic test 8/8 | resolver 계약 완료. reviewed positive 및 hard negative, exact source field, public transfer 측정 전 live assertion evidence 차단 |
| U0-O01 assertion ontology | Public ecosystem 20,560 edge와 synthetic correction fixture | relation candidate 20,560 unique, assertion ID, evidence, source time, validity, admitted status, assertion-ready 0. self-loop 13. synthetic test 9/9, history loss와 future leak 0 | bitemporal identity 계약 완료. live edge는 전부 candidate 유지, exact assertion source 전 fact lane 차단 |
| U0-P01 bounded projection | Current atlas, semiconductor detail, Samsung egograph와 synthetic graph | live output 18/35, 26/34, 50/60 node/edge. hash 3/3, bound, seed, lane violation 0. candidate 303, derived 50, fact 0. synthetic test 8/8 | projection 계약 promote. 새 bake 불필요. UI comprehension 전 candidate 및 derived scene만 허용 |
| U0-V01 visual grammar | 7 state token과 deterministic 30-card DOM reference fixture | non-color signature 7/7, evidence 및 aria 30/30, confidence opacity 0, test 8/8. reviewed participant 0/12, response 0/360, accuracy 미측정 | grammar contract 완료. 실제 comprehension 90% 전 production visual admission 차단 |
| U0-V02 deterministic layout | Live Atlas 18, industry 26, company 50 node와 3 viewport 및 3 browser | logical hash 60/60, viewport anchor 180/180, browser logical 및 anchor 180/180, max drift 0px, valid time unknown 94/94 | layout contract promote. 시간 합성 금지, U0-V01과 U0-V04 gate 유지 |
| U0-V03 density and omission | 250, 500, 1,000 node와 desktop 및 mobile 6 case | budget 6/6, omission receipt 6/6, reverse hash 6/6, calculated 및 DOM collision 0%, test 8/8 | density contract promote. FPS와 accessibility 및 renderer gate 유지 |
| U0-V04 bitemporal comprehension | validAt와 knownAt이 독립인 12 revision task | answer combination 4/4, separate control 및 aria 12/12, combined slider 0, test 9/9. participant 0/12, task response 0/144 | time grammar contract 완료. 실제 validAt, knownAt, combined 90% 전 Time Lens admission 차단 |
| U0-V05 accessibility equivalence | 핵심 action 6개, spatial 및 relation table, accessibility profile 6개 | command parity 6/6, synthetic task 36/36, browser keyboard spatial 및 table 각 6/6, semantic summary 12/12, reduced motion 0s, high contrast 6/6, 200% zoom overflow 0, mobile low GPU table 6/6, test 11/11 | 접근성 동등 경로 계약 promote. 실제 named screen reader 수동 session 전 production admission 차단 |
| U0-V06 renderer bakeoff | SVG, current Cosmos 1.6.1, DOM table, Canvas 2D와 desktop 500/1,000 및 mobile 250/500 fixture | 각 3회 task 6/6, desktop 최저 138.889fps, mobile 최저 135.135fps, heap budget 8/8. Built-in 17,438B raw 및 5,770B gzip, Cosmos 포함 328,891B 및 97,633B, test 7/7 | Canvas 2D contract promote, 새 external dependency 기각. Cosmos license admission false, 기존 map은 변경하지 않음 |
| U0-G01 release gold admission | Positive 300 및 hard negative 300 sampling plan, optional review 및 prediction JSONL | quota 30개 고정, machine test 19/19, docstring audit 위반 0. reviewed positive 0/300, hard negative 0/300, prediction 0/600. 기존 search gold 106건의 Universe relation 필드 0/106 | admission 및 metric contract 완료. Human review와 exact source field 전 U0 graduation 및 U1 차단 |
| U0-G02 review queue materialization | HF ecosystem graph와 allFilings 및 DART panel catalog 296,856행 | exact mention 182,072개, machine positive 후보 300개, hard-negative challenge 300개. Positive predicate 3/6, negative type 5/12, reviewed 0/600, goldEligible 0/600 | exact catalog locator 검토 큐 완료. Original source version 및 time, US/SEC, 누락 predicate와 negative type, human review 전 gold 승격 차단 |
| U0-G03 original source binding | Machine review queue 600행과 local DART original Parquet | source artifact 306개 SHA-256, exact original occurrence 63,326개. Binding ready 597/600, unique 119, ambiguous 478, source row missing 3, locator parity failure 0 | Original artifact provenance promote. Human locator 선택, predicate/direction 및 time 전 gold 승격 차단 |
| U0-G04 review promotion | Queue 600행, source binding 600행, optional human decision JSONL | human decision 0, promoted positive 0, promoted negative 0. Machine-origin, triple drift, unknown locator, inverted 및 naive time fail closed | Promotion compiler promote. Reviewed 300+300, prediction 600 및 quota gate 전 U0 graduation 차단 |

## 금지

- attempt 결과를 자동으로 HF truth 또는 map artifact에 쓰지 않는다.
- 현재 edge의 confidence 숫자만으로 observed 승격하지 않는다.
- sourceRef와 availableAt이 없는 edge를 public fact layer에 넣지 않는다.
- 단일 map buildId로 search, panel, finance exact replay를 주장하지 않는다.
- `eventAt <= availableAt`을 보편 규칙으로 강제하지 않는다.
- information yield 근거 없이 새 renderer dependency나 3D를 production에 넣지 않는다.
- U0 졸업 전 `src/dartlab/**`에 Universe 전용 신규 능력을 배치하지 않는다.
