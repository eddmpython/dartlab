# 11. Visual Information Physics

> 상태: 시각 혁신 계약
> 원칙: 화면의 위치, 모양, 색, 움직임은 모두 분석 의미 또는 상호작용 의미를 가져야 한다.

## 1. 시각 목표

Universe는 정보 우주를 흉내 내는 배경이 아니라, 대규모 정보를 압축하고 다시 근거까지 펼치는 분석 계기다.

사용자는 매 확대 단계에서 다음을 잃지 않아야 한다.

- 내가 전체에서 어디에 있는가
- 무엇이 바뀌었는가
- 무엇이 사실이고 무엇이 후보 또는 시나리오인가
- 무엇이 생략되었는가
- 이 표식의 근거는 무엇인가

progressive visual analytics는 중간 결과를 보여줄 때 추가 시각 복잡도를 최소화하고 visual anchor를 유지해야 한다고 정리한다. Universe는 이 원칙을 고정 좌표, representation 교체, 명시적 omitted receipt로 구현한다. 참고: [Progressive Visual Analytics review](https://www.mdpi.com/2227-9709/5/3/31)

## 2. 의미 좌표

force simulation이 데이터 의미를 결정하지 않는다. 각 장면은 task에 맞는 좌표계를 선언한다.

| 장면 | x축 | y축 | 반경 또는 깊이 |
|---|---|---|---|
| 산업 atlas | value-chain stage 또는 정렬된 industry order | market 및 industry lane | aggregate 규모 |
| 회사 분포 | 선택 metric percentile | industry 또는 market lane | peer distance |
| 회사 ego | 관계 단계 또는 유효 시간 | predicate lane | seed로부터 hop |
| 변화 우주 | validAt 또는 knownAt | industry, metric, filing lane | 변화 크기 |
| Kill-Chain | 주장 순서 | fact, derived, gap, scenario lane | evidence depth |
| 한미 Twin | 동일 metric 또는 disclosure topic | KR 및 US mirror lane | source 및 section depth |

2.5D를 쓸 경우 z축은 assertion depth 또는 layer 분리에만 쓴다. 임의 원근감, 점수, 중요도를 동시에 넣지 않는다.

동적 그래프의 mental map은 모든 task에서 무조건 안정적일수록 좋다고 단정할 수 없다. 따라서 Universe는 화면 전체를 고정하는 대신 industry, seed, selected relation 같은 anchor만 고정하고 task별 comprehension attempt로 검증한다. 참고: [Dynamic graph mental map study](https://www.sciencedirect.com/science/article/pii/S107158191300102X)

## 3. L0부터 L5까지 representation 교체

확대는 같은 점을 크게 만드는 동작이 아니다.

| LOD | 표현 | 핵심 질문 | 기본 mark budget |
|---|---|---|---:|
| L0 | 34개 산업 territory와 weather halo | 어디가 변하고 있는가 | node 34, label 34 |
| L1 | stage cluster와 bundled flow | 산업은 어떤 공정으로 이어지는가 | node 120, edge 180 |
| L2 | 회사 분포와 local orbit | 어떤 회사가 분포의 어디에 있는가 | desktop node 500 |
| L3 | company ego와 relation lane | 누구와 어떤 관계인가 | edge 1,000 이하 |
| L4 | evidence fan과 assertion timeline | 왜 이 관계를 말하는가 | assertion 20 이하 |
| L5 | filing span, table cell, metric series | 원문과 수치는 정확히 무엇인가 | viewport 기반 |

LOD 전환에는 들어가는 임계값과 나오는 임계값을 다르게 두는 hysteresis를 적용한다. 확대와 축소 경계에서 representation이 깜박이지 않게 한다.

`기타 N개` aggregate는 삭제된 데이터가 아니다. 다음을 포함하는 집계 receipt다.

- memberCount
- observedCount
- candidateCount
- unknownCount
- omittedCount
- coverage
- quantiles
- topChanges
- omissionReason

## 4. 시각 채널 예산

| 의미 | 시각 채널 | 금지 |
|---|---|---|
| 선택 metric | node fill 1개 | 여러 metric을 rainbow로 겹침 |
| 비교 metric | 크기 1개, log 또는 percentile 범례 | raw 금액을 반경에 직접 사용 |
| entity kind | shape | 색과 shape를 같은 의미에 중복 |
| evidence status | 선 패턴과 종단 glyph | opacity 하나로 confidence 표현 |
| freshness | clock ring | 낮은 점수 색과 혼합 |
| unknown | hollow mark와 `?` | 0 또는 fail 색으로 표현 |
| disputed | split glyph 또는 충돌 marker | 평균값으로 상쇄 |
| selected path | width와 focus halo | 전체 화면 animation |

한 장면에는 primary metric 1개와 comparison metric 1개만 둔다. color는 metric 또는 status 중 하나에만 쓰고 다른 의미는 패턴과 shape로 분리한다.

label은 중요도, 선택, 검색 결과, 변화량에 따라 우선순위를 가진다. current Cosmos의 dynamic label 동작을 그대로 신뢰하지 않고 label policy를 scene contract에 둔다. full Cosmograph를 후보로 검토할 때는 공식 clustering과 label 우선순위 기능을 bakeoff에서만 평가한다. 참고: [Cosmograph clustering](https://cosmograph.app/docs-lib/features/clustering/), [Cosmograph labels](https://cosmograph.app/docs-lib/features/labels/)

## 5. 동기화된 네 표면

정보량은 한 canvas에 모두 넣지 않는다.

```text
Spatial Scene
  위치, 흐름, 분포, 선택

Evidence Ribbon
  validAt, knownAt, sourcePublishedAt, availableAt, revision

Claim Ledger
  claim, status, evidence, falsifier, gap

Metric Surface
  table, distribution, time series, units, coverage
```

네 표면은 같은 `sceneId`, `claimId`, `receiptId`, `selectionId`를 쓴다. scene에서 edge를 선택하면 ledger row와 evidence ribbon이 함께 선택된다. table에서 row를 선택해도 같은 동작을 한다.

knowledge graph와 시각 표현을 분리하는 선언형 접근은 데이터 의미와 chart 표현이 서로 독립적으로 진화할 수 있게 한다. Universe도 ontology가 renderer grammar를 직접 소유하지 않게 한다. 참고: [Knowledge graph and declarative visualization](https://www.nature.com/articles/s41597-022-01352-z)

## 6. 재현 가능한 narrative camera

카메라는 `SceneBeat[]`를 순서대로 보여준다.

```text
overview -> focus -> path -> evidence -> lens -> compare -> falsify
```

규칙:

- beat마다 사용자가 멈추고 table로 전환할 수 있다.
- 자동 재생은 기본 off다.
- camera binary가 아니라 projection과 selection을 저장한다.
- transition은 replace, diff, overlay 중 하나다.
- decorative fly-through와 흔들림을 쓰지 않는다.
- reduced motion에서는 transition 없이 최종 frame을 연다.

분석 과정의 provenance를 별도 knowledge graph로 기록하는 연구는 사용자의 분석 action, insight, artifact를 연결해 재현성을 높이는 방향을 제시한다. Universe는 더 작은 `SceneBeat`와 `EvidenceReceipt`로 필요한 범위만 구현한다. 참고: [Visual Analytics Knowledge Graph](https://arxiv.org/abs/2204.00585), [Visual analytics provenance framework](https://www.osti.gov/biblio/1286885)

## 7. renderer 포트폴리오

renderer 하나가 모든 task를 소유하지 않는다.

| 표면 | 기본 후보 | 사용 범위 |
|---|---|---|
| L0 atlas와 flow | SVG | territory, bundled path, label, keyboard focus |
| L2 및 L3 bounded graph | current `@cosmograph/cosmos` adapter | desktop 500 node, mobile 250 node |
| L4 evidence fan | SVG 또는 Canvas with DOM focus mirror | assertion과 source path |
| L5 원문과 표 | DOM table 및 chart | exact 읽기와 export |
| 밀도 집계 후보 | deck.gl HexagonLayer attempt | 회사 분포 집계만 |
| 2.5D 및 3D | lazy optional adapter | uplift 통과 시 presentation |

deck.gl HexagonLayer는 GPU aggregation을 지원하지만 Universe 도입 근거가 아니다. `U0-V06 rendererBakeoff`에서 현재 SVG 또는 Canvas 집계보다 정확성과 정보 수율이 나을 때만 후보로 남긴다. 참고: [deck.gl HexagonLayer](https://deck.gl/docs/api-reference/aggregation-layers/hexagon-layer), [deck.gl performance](https://deck.gl/docs/developer-guide/performance)

Three.js WebGPURenderer는 WebGPU와 WebGL 2 fallback을 제공하지만, WebGPU 자체는 모든 주요 환경에서 Baseline으로 볼 수 없다. 따라서 3D는 U5 optional이며 browser capability detection과 2D 복귀가 필수다. 참고: [Three.js WebGPURenderer](https://threejs.org/docs/pages/WebGPURenderer.html), [MDN WebGPU](https://developer.mozilla.org/en-US/docs/Web/API/GPU/getPreferredCanvasFormat)

## 8. UniverseRenderer v2 계약

```text
UniverseRenderer
  mount(container, accessibilityBridge)
  setScene(scene)
  applyScenePatch(atomicPatch)
  setSelection(ids)
  setLabelPolicy(policy)
  setCameraPreset(preset)
  hitTest(point)
  focusById(id)
  measure()
  recoverContext()
  destroy()
```

필수 불변식:

- renderer 내부 fetch 0
- ontology 또는 engine import 0
- scene patch는 atomic
- camera와 layout은 deterministic seed를 사용
- 모든 interactive mark는 keyboard focus ID를 가짐
- context loss 후 2초 안에 table 또는 SVG로 복귀
- renderer 교체 후 claim, receipt, selection 집합이 동일

## 9. 성능과 밀도 예산

| 항목 | desktop | mobile |
|---|---:|---:|
| active node | 500 | 250 |
| active edge | 1,000 | 500 |
| visible label | 80, attempt에서 축소 가능 | 40, attempt에서 축소 가능 |
| interaction frame P95 | 45fps 이상 | 30fps 이상 |
| hit test P95 | 50ms 이하 | 80ms 이하 |
| initial visual data gzip | 150KB 이하 | 150KB 이하 |
| working heap 목표 | 256MB 이하 | 128MB 이하 |
| context fallback | 2초 이하 | 2초 이하 |

기존 runtime 상한보다 시각 목표 heap을 더 낮게 둔다. 초과하면 lower LOD, aggregate, label 축소 순으로 degrade하고 missing 또는 omitted count를 숨기지 않는다.

## 10. 접근성과 동등성

- Canvas interactive mark마다 1대1 DOM focus target 또는 동등한 focus list를 둔다.
- 모든 scene 작업은 relation table과 claim ledger에서 완료 가능해야 한다.
- 색 없이 entity kind와 status를 구분할 수 있어야 한다.
- screen reader summary는 선택 claim, evidence status, validAt, knownAt, gap을 읽는다.
- focus order는 SceneBeat 순서와 일치한다.
- high contrast, 200% zoom, keyboard only, reduced motion을 release gate에 넣는다.
- 3D만 가능한 선택, evidence open, filter, share 기능을 만들지 않는다.

## 11. 시각 attempts

| ID | 질문 | 표본 | 합격 | kill 조건 |
|---|---|---|---|---|
| U0-V01 | 상태 문법을 정확히 읽는가 | 30 scene card, 12명 | fact, candidate, derived, scenario 90% 이상 | confidence를 opacity만으로 표현 |
| U0-V02 | layout이 재현되는가 | 3 browser, 20 replay | logical coordinate hash 일치, 같은 viewport와 DPR에서 anchor 오차 1px 이하 | 재실행마다 company 위치 이동 |
| U0-V03 | 밀도에서 정보가 보존되는가 | 250, 500, 1,000 node fixture | omitted receipt 100%, collision 2% 이하 | 전체 node를 무조건 표시 |
| U0-V04 | 이중 시간을 이해하는가 | 12 revision task | validAt, knownAt 정답 90% 이상 | 한 slider로 두 시간을 혼합 |
| U0-V05 | 접근성이 동등한가 | keyboard, reader, low GPU | 핵심 task 100% 완료 | canvas에만 가능한 작업 |
| U0-V06 | renderer bakeoff가 필요한가 | SVG, Cosmos, DOM, 후보 adapter | task, frame, heap, bundle 비교 | 새 dependency가 개선 없음 |
| U5-X01 | 2.5D 또는 3D가 나은가 | discovery와 path task | 2D 대비 성공률 또는 발견률 개선 | 3D만 가능한 기능 또는 멀미 증가 |

2026-07-15 U0-V01 실행 결과: Fact, candidate, derived, disputed, retracted, scenario, unknown 7개 상태를 stroke, pattern, glyph, label, evidence action, aria phrase의 non-color signature로 모두 분리했다. Deterministic card 30개에서 evidence affordance와 aria coverage는 30/30, confidence opacity 사용은 0, machine regression은 8/8이다. Reviewed participant는 0/12, response는 0/360이고 comprehension accuracy는 미측정이다. Grammar contract는 완료했지만 실제 판독 90% 전 production visual admission은 차단한다. `tests/_attempts/dartlabUniverse/visual/README.md`가 response schema와 실행 명령을 소유한다.

2026-07-16 U0-V02 실행 결과: Live Atlas, industry, company의 94개 node를 scene별 20회 순서 교란해 logical hash 60/60, 세 viewport anchor hash 180/180을 얻었다. Chrome, Firefox, WebKit 180회 실측에서도 logical 및 anchor hash가 180/180 일치했고 최대 drift는 0px였다. Force iteration은 0이며 industry stage, valid order 또는 unknown time lane, evidence status만 좌표 의미에 사용한다. Current artifact의 valid time 0/94는 추정하지 않고 unknown 94/94로 receipt에 남긴다. Layout contract만 promote하며 U0-V01 comprehension과 U0-V04 time comprehension은 계속 독립 gate다.

2026-07-16 U0-V03 실행 결과: 250, 500, 1,000 node의 desktop 및 mobile 6 case에서 active mark와 label budget, exact omission receipt, reverse input hash가 모두 6/6 통과했다. 1,000 node는 desktop 500과 mobile 250으로 lower LOD를 적용하고 omitted 500 및 750 node를 aggregate receipt로 보존한다. 1280x720과 390x844 실제 DOM label collision은 0%였고 visible label은 desktop 최대 57/80, mobile 40/40이었다. Density contract만 promote하며 frame, heap, hit-test, accessibility 및 renderer selection은 U0-V05와 U0-V06에 남긴다.

## 12. 유지보수 규칙

- visual grammar token은 renderer package가 아니라 universe contract가 소유한다.
- layout algorithm 변경은 golden scene과 comprehension 재검증이 필요하다.
- renderer dependency는 분기마다 license, bundle, browser, context-loss를 감사한다.
- label budget과 LOD threshold는 telemetry 없는 reference replay fixture로 회귀 검증한다.
- decorative effect는 제품 metric을 개선한 attempt receipt가 없으면 추가하지 않는다.
- full Cosmograph, deck.gl, Three.js는 production dependency가 아니라 bakeoff 후보로 시작한다.

## 영향 파일

- `mainPlan/dartlab-universe/04-product-ux.md`
- `mainPlan/dartlab-universe/08-attempts-evidence-matrix.md`
- `tests/_attempts/dartlabUniverse/visual/`
- production 졸업 후 `ui/packages/contracts/src/universe.ts`
- production 졸업 후 `ui/packages/surfaces/src/universe/renderers/`
- production 졸업 후 `ui/packages/surfaces/src/universe/components/ClaimLedger.svelte`

## 영향 함수/심볼

- `UniverseRenderer`
- `VisualGrammar`
- `LabelPolicy`
- `ScenePatch`
- `SceneBeat`
- `AggregateReceipt`
- `measureRendererBudget`
- `buildAccessibilityBridge`

## 테스트

- semantic LOD representation snapshot
- label collision과 anchor drift 측정
- renderer별 scene hash 및 receipt 집합 동등성
- keyboard, screen reader, reduced motion, high contrast
- low GPU와 context loss fallback
- desktop 및 mobile frame, heap, hit-test budget
- 2D 대비 2.5D 및 3D task uplift

## 롤백

- renderer adapter는 동일 scene contract 뒤에 있으므로 prior adapter로 복귀한다.
- label 또는 layout 회귀는 visual grammar version을 previous로 되돌린다.
- 2.5D와 3D는 chunk와 feature state를 끄고 2D와 table을 유지한다.
- dependency 문제가 생기면 SVG와 DOM reference renderer를 유지한다.

## 평가

### 전문 개발자 평가

현재 map의 force layout과 상시 label 갱신을 Universe의 제품 물리로 복제하지 않는다. 의미 좌표, LOD representation 교체, immutable scene, table 기준 surface를 분리해 renderer를 교체할 수 있다. 새 시각 dependency는 bakeoff를 통과하기 전 추가하지 않으며, 성능과 접근성 실패는 lower LOD와 reference renderer로 격리된다.

### 전문 PM 평가

우주 감성은 별 배경이 아니라 거시에서 원문까지 자연스럽게 깊어지는 경험에서 나온다. 변화 우주와 Kill-Chain이 서로 다른 시각 문법을 갖되 같은 evidence receipt를 공유해 기억 가능한 제품 서명을 만든다. 정보 밀도를 생략 없는 집계와 동기화된 표면으로 확보하므로 화려함과 분석성이 경쟁하지 않는다.
