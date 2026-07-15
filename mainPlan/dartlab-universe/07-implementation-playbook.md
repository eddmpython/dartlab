# 07. Implementation Playbook

> 목적: 다음 작업자가 이 문서와 연결된 계약만 읽고 U0부터 public GA까지 순서대로 실행한다.
> 실행 단위: work packet 1개, 검증, 원장 갱신, commit 1개가 기본이다.
> 금지: phase 건너뛰기, UI 선행, sourceRef 없는 fact 승격, 승인 없는 artifact bake

## 1. 작업 운영 계약

모든 work packet은 같은 8단계를 따른다.

1. `06-progress-ledger.md`에서 직전 packet의 종료 증거를 확인한다.
2. 영향 경로의 현재 상태와 본 계획의 정합성 및 ROI를 재검한다.
3. 선행 attempt의 input buildId, 실행 명령, 결과, falsifier를 확인한다.
4. 명시된 파일과 심볼만 변경한다.
5. packet 전용 테스트를 실행한다.
6. Guard quick 또는 package check를 실행한다.
7. `06-progress-ledger.md`에 결과와 다음 행동을 기록한다.
8. 본인 변경 경로만 명시 stage하고 한글 commit 1개로 닫는다.

packet이 실패하면 다음 packet으로 넘어가지 않는다. 실패 결과는 attempt README와 progress ledger에 남기고 설계를 고친 뒤 같은 packet을 다시 실행한다.

## 2. Phase 0: 계획 및 작업면 동결

### P0-01 현재 상태 재검

선행 조건: 없음.

실행:

1. master 여부와 worktree status를 기록한다.
2. `landing`, `ui`, map builder, search runtime, industry engine의 실제 경로를 확인한다.
3. HF `meta.json`, `atlas.json`, `ecosystem.json`의 buildId와 schema를 기록한다.
4. capability와 Skill OS 수를 다시 측정한다.
5. 기존 대량 삭제가 남아 있으면 U1을 시작하지 않고 U0만 진행한다.

산출:

- `01-current-state-audit.md` 기준 commit과 artifact buildId 갱신
- `06-progress-ledger.md` preflight 행

종료 조건:

- 계획의 모든 production 경로가 현재 존재하거나, active refactor blocker로 명시됨
- U0가 production worktree와 독립적으로 실행 가능함

### P0-02 route 및 ownership 동결

선행 조건: P0-01.

실행:

1. public product route를 `/universe`로 고정한다.
2. `/map`은 기존 시장 지도와 deep link를 유지한다.
3. route 간 component import를 금지한다.
4. contracts, runtime, renderer adapter만 공유하도록 owner를 정한다.
5. `/universe` URL schema와 release state를 `09-public-route-release-contract.md`로 고정한다.

종료 조건:

- `/map` 변경 없이 `/universe`를 끌 수 있음
- loader와 cache는 공유하되 UI source 복사가 없음

## 3. Phase U0: Truth Gate attempts

U0에서는 production code와 UI를 만들지 않는다. 모든 코드는 `tests/_attempts/dartlabUniverse/` 안에 둔다.

### U0-T01 current graph truth census

상태: 완료.

명령:

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/truth/graphTruthProbe.py
```

실측:

- node 2,664
- edge 20,560
- self-loop 13
- exact sourceRef 0
- exact availableAt 0
- observed 적격 edge 0
- OCI incident edge 4,474, unique neighbor degree 2,585

결정: 기존 edge는 retrieval 및 layout candidate로만 사용한다.

### U0-I01 canonical identity probe

목표: stockCode와 ticker를 presentation key로 제한하고 corpCode, CIK 중심 ID가 실제 자료에서 복원되는지 증명한다.

입력:

- KR 50사: 합병, 상호변경, 우선주, SPAC, 동일 이름 포함
- US 30사: ticker 변경, 복수 class, 동일 이름 포함
- DART company metadata, SEC submissions metadata, listing resolver

실행 순서:

1. `identity/entityIdentityProbe.py`에서 provider metadata를 읽는다.
2. KR legal entity, security, filing ID를 별도로 생성한다.
3. US CIK, security, filing ID를 별도로 생성한다.
4. alias가 둘 이상의 entity로 해소되면 ambiguous로 반환한다.
5. fuzzy name만으로 cross-market link를 만들지 않는다.
6. fixture와 실데이터 결과를 `identity/README.md`에 기록한다.

합격:

- exact identifier 입력 100% deterministic
- ambiguous alias 자동 단일 해소 0건
- legal entity와 security 혼합 0건
- 과거 ticker가 현재 entity로 연결될 때 validity 누락 0건

실패 시: ID registry production 설계를 중단하고 reference owner의 기존 resolver 보강안을 먼저 설계한다.

### U0-E01 exact document evidence probe

목표: current edge hint에서 DART 및 EDGAR exact filing과 section span을 요청 시점에 찾을 수 있는지 측정한다.

입력:

- reviewed positive 100건
- hard negative 100건
- `panel_table`, `panel_text`, `network` 균형 표본
- exact search postings와 panel range read

실행 순서:

1. subject, object, predicate를 search constraint로 컴파일한다.
2. exact entity boundary, filing ID, sectionPath를 요구한다.
3. table 근거는 row와 header를 함께 보존한다.
4. text 근거는 snippet과 char boundary를 보존한다.
5. sourceRef, availableAt, bytes, cold duration을 기록한다.
6. 실패를 `notFound`, `ambiguousEntity`, `directionUnknown`, `timeUnknown`, `sourceUnavailable`로 분류한다.

합격:

- positive sourceRef resolution 95% 이상
- hard negative false accept 1% 이하
- sourceRef 없는 observed 0건
- edge당 cold transfer 2MB 이하 또는 U3 토론 근거로 기록

### U0-O01 assertion and bitemporal contract

목표: 같은 relation의 여러 공시, 정정, 시점이 파괴되지 않는 assertion identity를 증명한다.

실행 순서:

1. canonical payload key와 hash 규칙을 확정한다.
2. relationId와 assertionId를 별도 계산한다.
3. 같은 relation의 다른 rceptNo와 period가 다른 assertionId인지 확인한다.
4. 정정 공시가 이전 assertion을 삭제하지 않는지 확인한다.
5. `eventAt <= availableAt <= knowledgeAsOf`를 강제한다.
6. `validAt`과 `knownAt`을 독립 필터한다.
7. `VintageRef`와 `Ref`로 실제 evidence hash를 묶는다.

합격:

- canonical hash fixture가 OS와 실행 순서에 무관
- revision history 손실 0
- future knowledge leak 0
- missing time을 오늘 또는 0으로 채운 사례 0

### U0-P01 bounded projection probe

목표: 276GB truth를 복제하지 않고 질문당 50~500 node scene을 결정론적으로 만드는지 증명한다.

실행 순서:

1. atlas, industry, company seed 3종 fixture를 만든다.
2. maxDepth, maxNodes, maxEdges hard bound를 적용한다.
3. fact, candidate, derived, scenario lane을 분리한다.
4. stable priority와 truncation을 적용한다.
5. omitted count와 reason을 남긴다.
6. 같은 spec과 buildId의 scene hash를 반복 비교한다.

합격:

- hard bound 초과 0
- 반복 실행 scene hash 불일치 0
- candidate가 fact lane에 들어간 사례 0
- truncation 후 seed 손실 0

### U0-G01 reviewed gold graduation

목표: anecdote가 아닌 release 가능한 품질 원장을 만든다.

구성:

- positive 300건
- hard negative 300건
- predicate, source, market, language, evidence class 균형
- OCI, 동일 회사명, 계열사, 표 header drift, 정정, ticker 변경 필수 포함

합격:

- positive precision 98% 이상
- false acceptance 1% 이하
- sourceRef coverage 100%
- reviewer와 reviewedAt 누락 0

U0 졸업 산출:

- `tests/_attempts/dartlabUniverse/README.md` 결론 원장
- production으로 옮길 contract 목록
- 기각된 아이디어와 이유
- U1 entry 승인 행

## 4. Phase U1: 독립 `/universe` route와 serverless scene

선행 조건:

- U0-I01, U0-O01, U0-P01 합격
- frontend source 대량 삭제 또는 이동이 해소됨
- U0 production 이관 review 완료

### U1-01 contracts 이관

변경:

- `ui/packages/contracts/src/universe.ts`
- `ui/packages/contracts/src/index.ts`

구현 심볼:

- `UniverseNode`
- `UniverseAssertion`
- `UniverseRelation`
- `ProjectionSpec`
- `UniverseScene`
- `EvidencePointer`

규칙:

- attempt contract를 그대로 옮기고 새 필드를 즉흥 추가하지 않는다.
- current와 previous schema fixture를 동행한다.
- unknown predicate와 redistributionClass는 fail closed다.

종료 조건: contract test와 canonical fixture green.

### U1-02 공유 loader 분리

변경:

- `landing/src/lib/browser/dartlabBrowser.ts`
- `landing/src/lib/browser/types.ts`
- `ui/packages/runtime/src/data/universe/load.ts`

구현:

1. `loadUniverseMeta()`
2. `loadMarketAtlas()`
3. `loadIndustryProjection(industryId)`
4. `loadCompanyProjection(stockCode)`
5. `loadObservationSeries(entityId, metricId, range)`

규칙:

- 모든 I/O는 `data/fetch.request()`와 origins registry를 경유한다.
- route 또는 source 안에 raw fetch, URL 상수, cache Map을 만들지 않는다.
- `/map` compatibility loader도 같은 함수를 소비한다.

종료 조건:

- atlas request 시 ecosystem request 0
- company 선택 전 company JSON request 0
- 동일 source/range in-flight request 1회

### U1-03 projection compiler 이관

변경:

- `ui/packages/runtime/src/data/universe/projection.ts`
- `ui/packages/runtime/src/data/universe/time.ts`

구현 순서:

1. schema/buildId 검증
2. public policy admission
3. canonical seed resolution
4. validAt 및 knownAt filter
5. evidence/status filter
6. hard bound
7. stable sort와 truncation
8. scene hash

종료 조건: attempt의 golden projection과 byte-stable 일치.

### U1-04 `/universe` route shell

변경:

- `landing/src/routes/universe/+page.ts`
- `landing/src/routes/universe/+page.svelte`
- `ui/packages/surfaces/src/universe/UniverseSurface.svelte`
- `ui/packages/surfaces/src/universe/url.ts`

첫 화면:

- meta와 atlas만 load
- seed search
- dataAsOf와 coverage
- 2D atlas와 동등 table
- `/map`으로 가는 명시 link

금지:

- `/map` route component import
- ecosystem eager load
- 3D dependency
- evidence가 없는 fact 선

종료 조건:

- initial gzip 150KB 이하
- desktop first data 1.5초 이하
- mobile first data 2.5초 이하
- refresh, back, forward URL state 복원
- `/map` regression 0

### U1-05 renderer adapter

변경:

- `ui/packages/surfaces/src/universe/renderers/UniverseRenderer.ts`
- `ui/packages/surfaces/src/universe/renderers/cosmosRenderer.ts`
- `ui/packages/surfaces/src/universe/components/RelationTable.svelte`

종료 조건:

- renderer package type가 adapter 밖으로 새지 않음
- WebGL 실패 시 SVG 또는 table
- reduced motion과 keyboard path 동작

## 5. Phase U2: evidence, time, lens

### U2-01 evidence resolver

선행 조건: U0-E01 합격.

변경:

- `ui/packages/runtime/src/data/universe/evidence.ts`
- 기존 `filingSearch.ts`는 호출만 하고 복사하지 않음

종료 조건:

- gold resolution 95% 이상
- cold P95 5초 이하
- transfer 2MB 이하
- unresolved fact promotion 0

### U2-02 Evidence Drawer

변경:

- `ui/packages/surfaces/src/universe/components/EvidenceDrawer.svelte`
- `ui/packages/surfaces/src/universe/components/AssertionTimeline.svelte`

표시 순서:

1. relation plain language
2. status와 evidence class
3. validAt, availableAt, knowledgeAsOf
4. assertion timeline
5. filing identity와 section
6. exact text 또는 table row
7. extraction method와 limitation

종료 조건: source deep link, keyboard, screen reader, unresolved reason 통과.

### U2-03 Time Lens

변경:

- `ui/packages/surfaces/src/universe/components/TimeLens.svelte`

종료 조건:

- knownAt 이후 assertion 제거 100%
- validAt과 knownAt 독립 동작
- revision marker 보존

### U2-04 engine lens adapter

변경:

- `ui/packages/runtime/src/data/universe/lenses.ts`
- `ui/packages/surfaces/src/universe/components/LensTray.svelte`

규칙:

- 147개 axis별 adapter를 만들지 않는다.
- standard Ref, tableRef, valueRef, dateRef, executionRef만 소비한다.
- fact relation을 lens output으로 수정하지 않는다.
- primary lens 1개와 comparison lens 1개만 허용한다.

종료 조건:

- industry, financial, credit, macro, quant, scan 6종 contract fixture
- engine output 결손을 0으로 채운 사례 0
- capability docstring 변경 시 generic renderer만으로 표시 가능

## 6. Phase U3: optional artifact extension

U3는 기본 실행 phase가 아니다. U2가 합격하면 건너뛴다.

착수 조건:

1. cold P95 5초 초과 또는 transfer 2MB 초과가 3회 이상 반복
2. runtime 최적화와 range projection을 먼저 소진
3. 실패 원인과 최소 additive field를 문서화
4. 운영자 명시 승인

허용:

- existing company edge의 optional `assertionRefs`, `eventAt`, `availableAt`, `status`
- meta quality summary와 schema version

금지:

- 새 graph warehouse
- 전체 panel triple bake
- 별도 vector DB
- 기존 edge field 삭제

검증:

- stage, validate, promote, rollback
- current와 previous reader
- 기존 `/map` byte contract 회귀 0

## 7. Phase U4: cross-market

### U4-01 identity conformance

- KR corpCode와 US CIK를 canonical legal entity로 사용
- security와 legal entity 분리
- ticker/stockCode validity 보존

### U4-02 panel conformance

- DART와 EDGAR 공통 16컬럼 panel 계약
- disclosureKey와 finance account alignment
- currency와 unit은 lens에서 명시
- name fuzzy auto-link 0

### U4-03 paired product demo

20개 KR/US paired question을 고정한다. 각 질문은 sourceRef, dataAsOf, unit, 결손을 가진다.

종료 조건:

- paired conformance 20/20
- sourceRef 없는 US observed relation 0
- dataAsOf mismatch 표시 100%

## 8. Phase U5: optional 3D Galaxy

선행 조건:

- U0~U4 합격
- 2D, table, Evidence Drawer task 100% 유지
- dependency license, bundle, browser review

실행:

1. `UniverseRenderer`의 3D adapter만 추가한다.
2. 같은 `UniverseScene`과 scene hash를 사용한다.
3. optional chunk로 지연 load한다.
4. mobile, reduced motion, low GPU는 자동 off다.

종료 조건:

- 별도 truth 또는 graph request 0
- desktop P95 45fps 이상
- mobile 기본 off
- 3D 실패 시 2D 즉시 복귀

## 9. Phase U6: public beta와 GA

### U6-01 local review

- `/universe` 실제 production build 경로에서 검수
- 320, 375, 768, 1440 width
- keyboard, screen reader, reduced motion
- network waterfall와 heap capture
- fact/candidate 시각 문법 눈검수

### U6-02 public beta

- 같은 `/universe` route를 beta state로 공개
- navigation에는 Beta label
- unresolved diagnostics는 로컬 export만
- 개인 query 원문 telemetry 0
- rollback drill 1회

### U6-03 GA

- 14일 beta 동안 SLO 위반 없음
- sourceRef coverage 100%
- hard negative false acceptance 1% 이하
- schema rollback과 route disable 훈련 통과
- 운영자 UI 눈검수와 push 승인

## 10. commit 경계

| commit | 범위 | 예시 메시지 |
|---|---|---|
| C0 | attempt category와 첫 probe | `실험: Universe 그래프 사실 적격성 측정` |
| C1 | U0 identity | `실험: Universe 개체 식별 계약 검증` |
| C2 | U0 evidence | `실험: Universe 원문 근거 해소율 측정` |
| C3 | U0 ontology/projection | `실험: Universe assertion과 투영 계약 검증` |
| C4 | contracts | `기능: Universe 장면 계약 추가` |
| C5 | shared runtime | `기능: Universe 지연 로더와 투영 런타임 추가` |
| C6 | route/surface | `기능: 퍼블릭 Universe 독립 화면 추가` |
| C7 | evidence/time | `기능: Universe 근거와 시간 탐색 추가` |
| C8 | lenses | `기능: Universe 엔진 렌즈 연결` |
| C9 | cross-market | `기능: Universe 한미 비교 장면 추가` |
| C10 | optional 3D | `기능: Universe 선택형 Galaxy 렌더러 추가` |

UI가 포함된 C6 이후 commit은 눈검수와 운영자 명시 승인 전 push하지 않는다. 앞선 unpushed commit 범위에도 UI가 포함되면 동일하다.

## 영향 파일

정본 목록은 phase별 본문에 있다. 핵심 owner는 다음과 같다.

- attempts: `tests/_attempts/dartlabUniverse/**`
- plan ledger: `mainPlan/dartlab-universe/**`
- contracts: `ui/packages/contracts/src/universe.ts`
- runtime: `ui/packages/runtime/src/data/universe/**`
- surface: `ui/packages/surfaces/src/universe/**`
- route: `landing/src/routes/universe/**`
- shared browser loader: `landing/src/lib/browser/dartlabBrowser.ts`
- 승인 후 artifact: `src/dartlab/industry/**`, `.github/scripts/prebuild/buildIndustryMap.py`

## 영향 함수/심볼

- `inspectGraphTruth`
- `ProjectionSpec`
- `UniverseNode`
- `UniverseAssertion`
- `UniverseRelation`
- `UniverseScene`
- `compileProjection`
- `loadUniverseMeta`
- `loadMarketAtlas`
- `loadIndustryProjection`
- `loadCompanyProjection`
- `resolveAssertionEvidence`
- `applyKnowledgeCutoff`
- `UniverseRenderer`

## 테스트

1. attempts는 network 없는 deterministic fixture test를 항상 동행한다.
2. live probe는 입력 URL, version, 실행 시각과 결과를 README에 기록한다.
3. production 이관은 attempt golden fixture와 byte-stable conformance를 요구한다.
4. UI runtime은 `checkUiDataWiring`, package test, Svelte check를 통과한다.
5. 최종 gate는 `uv run python -X utf8 tests/run.py preflight`다.
6. 전체 `pytest tests/ -v`는 실행하지 않는다.
7. UI는 실제 route에서 브라우저 눈검수를 통과한다.

## 롤백

- U0: attempts와 문서만 제거하면 production 영향 0이다.
- U1: `/universe` route release state를 off하고 `/map`은 그대로 유지한다.
- U2: evidence/time/lens 모듈을 disable해 atlas와 candidate-only scene을 유지한다.
- U3: 이전 map buildId pointer로 복귀한다. 원격 파일 삭제는 하지 않는다.
- U4: market scope를 KR로 제한한다.
- U5: 3D chunk를 disable하고 2D와 table을 유지한다.
- schema mismatch: atlas-only fail closed다.

## 평가

### 전문 개발자 평가

계획은 신규 능력을 attempts에서 시작하고 production 이관 지점을 contract, runtime, surface, route로 나눴다. 가장 위험한 identity, sourceRef, bitemporal, projection 결정론을 UI보다 먼저 검증한다. `/map`과 `/universe`가 route component를 공유하지 않고 runtime만 공유하므로 제품 분리는 얻되 유지보수 복제는 피한다. U3를 optional 승인 phase로 유지해 runtime SSOT를 지킨다.

발견한 핵심 갭은 active frontend 대량 삭제다. 이를 U1 entry blocker로 명시하고 U0는 계속 진행 가능하게 분리했다. 또 기존 계획에 없던 public beta, rollback drill, commit 경계를 추가해 구현 후 운영 공백을 닫았다.

### 전문 PM 평가

사용자는 우주라는 독립 제품을 원한다. `/universe`가 명확한 브랜드와 share URL owner가 되고 `/map`은 익숙한 시장 지도를 유지하므로 두 작업이 충돌하지 않는다. 사용자가 체감하는 가치 순서는 빠른 atlas, 사실과 후보의 구분, 원문 근거, 시간, 렌즈, cross-market, 3D다. 이 순서를 work packet과 demo acceptance에 그대로 반영했다.

기능 수보다 신뢰 가능한 연결을 먼저 release한다. beta에서 sourceRef coverage와 hard negative를 유지하지 못하면 GA하지 않는 기준이 제품 차별화를 보호한다.
