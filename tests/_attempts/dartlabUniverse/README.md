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

## 금지

- attempt 결과를 자동으로 HF truth 또는 map artifact에 쓰지 않는다.
- 현재 edge의 confidence 숫자만으로 observed 승격하지 않는다.
- sourceRef와 availableAt이 없는 edge를 public fact layer에 넣지 않는다.
- 단일 map buildId로 search, panel, finance exact replay를 주장하지 않는다.
- `eventAt <= availableAt`을 보편 규칙으로 강제하지 않는다.
- information yield 근거 없이 새 renderer dependency나 3D를 production에 넣지 않는다.
- U0 졸업 전 `src/dartlab/**`에 Universe 전용 신규 능력을 배치하지 않는다.
