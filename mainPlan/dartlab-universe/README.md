# DartLab Universe

> 상태: U0-G04 original source binding 및 human-only promotion compiler 완료, reviewed gold 차단
> 기준일: 2026-07-16 KST
> 제품명: DartLab Universe
> 정본 경계: HF 데이터는 진실, 온톨로지는 의미 계약, 엔진은 렌즈, Universe는 요청 시점 투영

## 결론

DartLab의 데이터를 공개 웹에서 우주처럼 탐색하는 제품은 가능하다. 다만 275.76GB를 전부 노드와 엣지로 복제하는 방식은 제품도 아니고 유지 가능한 아키텍처도 아니다.

정공 설계는 다음 네 평면을 분리한다.

1. **Truth Plane**: `eddmpython/dartlab-data`의 DART, EDGAR, KRX, 거시, 검색 Parquet이 정본이다.
2. **Meaning Plane**: 회사, 공시, 산업, 지표, 관측, 관계 assertion의 ID와 시간 및 근거 계약만 정의한다.
3. **Lens Plane**: 226개 capability와 286개 Skill OS 항목, analysis 22축, scan 27축 등 기존 엔진이 질문에 맞는 투영을 만든다.
4. **Scene Plane**: 브라우저가 질문과 확대 수준에 필요한 50~500개 노드만 HF에서 직독해 2D 또는 선택적 3D 장면으로 렌더링한다.

제품의 혁신은 노드 개수가 아니다. 사용자가 질문을 움직였을 때 **무엇이 바뀌었는지, 어떤 논리가 어디서 깨지는지, 왜 연결됐는지, 당시 무엇을 알 수 있었는지**를 원문까지 같은 조사 흐름에서 확인하는 데 있다.

최종 제품 서명은 다음 네 workflow다.

1. P0 변화 우주: 두 시점 사이의 생성, 정정, 소멸만 exact before/after evidence와 재생
2. P0 Thesis Kill-Chain: assumption, fragility, trigger, tripwire, falsifier를 근거 lane으로 연결
3. P1 판정 우주: 조건과 회사의 PASS, FAIL, MISSING, near-miss를 공간화
4. P1 한미 Twin: KR과 US의 동일 공시, 계정, 기간, 단위와 결손을 mirror 비교

## 제품 불변 결정

- 새 Neo4j, RDF 서버, 벡터 DB, 상시 백엔드를 두지 않는다.
- 새 `dartlab.universe()` 공개 엔진을 만들지 않는다. 공개 Python 계약은 기존 엔진 축 dispatch를 유지한다.
- 모든 관측값을 노드로 만들지 않는다. 안정된 개체만 노드이며, 수백만 관측은 Parquet과 표 및 시계열로 남긴다.
- 관계 하나와 그 관계를 뒷받침하는 여러 assertion을 분리한다.
- 사실, 파생, 추론, 시나리오를 같은 엣지 스타일이나 같은 신뢰 등급으로 섞지 않는다.
- 2D 분석 화면과 table이 기본이다. 3D Galaxy는 같은 immutable scene을 소비하고 task uplift를 증명해야 하는 지연 로드 렌더러일 뿐이다.
- public 제품 경로는 독립 `/universe`다. 기존 `/map`은 현재 시장 지도 역할을 유지한다.
- 라우트와 제품 상태는 분리하지만 DataCore, map artifact, renderer adapter, evidence resolver는 공유한다. route 간 코드 복사는 금지한다.
- 공개와 로컬은 같은 HF 직독 배선을 쓴다. AI와 무거운 동적 계산만 로컬 서버 또는 기존 `/api/ask`가 담당한다.
- 새 bake나 그래프 사본은 런타임 실측 실패와 운영자 명시 승인 전에는 만들지 않는다.
- 단일 map buildId로 exact replay를 약속하지 않는다. map, search, panel, finance, capability, recipe의 source version을 묶은 `SourceSnapshotSet`을 쓴다.
- assertion identity에 query의 knownAt을 넣지 않는다. 원천 발행시각, 공개 가능시각, 유효구간을 저장하고 knownAt은 projection filter로만 적용한다.

## 가장 먼저 고칠 제품 위험

현재 `edges.json` 20,560건 중 17,400건은 `panel_text` 회사명 부분문자열 매칭이다. 정확한 `rceptNo`, `sourceRef`, `period`, `availableAt`은 0건이다. `OCI`처럼 3글자 영문명이 거의 모든 본문에 걸려 한 회사에 4,474개 엣지가 붙고, self-loop도 13건 존재한다.

따라서 첫 구현은 화려한 3D가 아니다. 다음 품질 경계를 먼저 세운다.

- `observed` 또는 `corroborated` assertion은 정확한 sourceRef 없이는 화면의 사실 레이어에 들어갈 수 없다.
- 현재 저신뢰 엣지는 `candidate` 탐색 레이어로 강등하고 기본값에서는 숨긴다.
- self-loop, 허브 폭발, 이름 부분문자열 오탐, 시점 역전, 중복 assertion을 기계적으로 차단한다.
- 사용자가 엣지를 열면 기존 검색 range sidecar와 회사 panel에서 근거를 요청 시점에 확인한다.

## 문서 지도

1. [00-product-prd.md](00-product-prd.md): 사용자 문제, 제품 서명, 범위, 성공 기준
2. [01-current-state-audit.md](01-current-state-audit.md): HF 68,199파일과 엔진 및 현재 지도 실측
3. [02-ontology-evidence-contract.md](02-ontology-evidence-contract.md): ID, assertion, 시간, 근거, 라이선스 계약
4. [03-runtime-public-architecture.md](03-runtime-public-architecture.md): 서버리스 런타임, LOD, projection, 비용 및 장애 격리
5. [04-product-ux.md](04-product-ux.md): 2D 우주, Evidence Drawer, Time Lens, Galaxy 렌즈
6. [05-execution-validation-maintenance.md](05-execution-validation-maintenance.md): 파일과 심볼, 테스트, 단계, 3년 유지보수, 롤백
7. [06-progress-ledger.md](06-progress-ledger.md): 결정 및 승인 대기 원장
8. [07-implementation-playbook.md](07-implementation-playbook.md): 작업자가 순서대로 실행하는 work packet, commit, release 절차
9. [08-attempts-evidence-matrix.md](08-attempts-evidence-matrix.md): `_attempts` 가설, 실측, falsifier, 졸업 원장
10. [09-public-route-release-contract.md](09-public-route-release-contract.md): `/universe` 독립 라우트, `/map` 경계, public beta와 장기 운영 계약
11. [10-innovation-thesis-killer-workflows.md](10-innovation-thesis-killer-workflows.md): 제품 혁신 thesis, P0와 P1 killer workflow, 정보 수율
12. [11-visual-information-physics.md](11-visual-information-physics.md): 의미 좌표, L0~L5 representation, renderer, 접근성
13. [12-innovation-validation-scorecard.md](12-innovation-validation-scorecard.md): 7축 혁신 점수, readiness gate, kill condition

## 구현 순서

1. U0: `tests/_attempts/dartlabUniverse/`에서 graph truth, snapshot, workflow, visual, policy 계약을 실데이터로 검증한다. Bounded projection부터 renderer bakeoff, release gold admission, queue 600행, original source binding 597/600, human-only promotion compiler까지 실행했다. Human decision과 실제 reviewed positive 및 hard negative는 아직 0건이라 U0 graduation과 U1은 차단한다.
2. U1: 독립 `/universe` route에서 기존 atlas를 먼저 띄우고 34개 산업 변화 우주와 첫 3개 Kill-Chain을 연다.
3. U2: 엣지와 claim 클릭 시 기존 브라우저 검색 sidecar와 panel range read로 exact evidence를 찾는 Evidence on Demand를 붙인다.
4. U3: 런타임 근거 확인이 성능 예산을 넘는다는 측정이 있을 때만 기존 map artifact의 additive schema 확장을 토론한다.
5. U4: DART와 EDGAR의 동형 16컬럼 panel과 표준 재무를 사용해 시장간 비교 장면을 연다.
6. U5: 2D 제품과 근거 품질이 졸업한 뒤 같은 projection 계약 위에 선택적 3D Galaxy 렌즈를 얹는다.
7. U6: 같은 `/universe` route를 local review, public beta, GA 순서로 승격하고 운영 SLO와 rollback 훈련을 통과한다.

## 승인 게이트

- 본 폴더는 설계 정본이다. 코드 구현 착수는 운영자 go 이후다.
- `buildIndustryMap.py` 또는 HF map artifact 스키마를 바꾸는 U3는 런타임 실패 실측과 별도 명시 승인이 필요하다.
- `/universe`와 공유 UI 변경은 커밋까지 자율 가능하지만 눈검수와 명시 승인 전 push하지 않는다.
- `scan-screener-os`에 기록된 네이버 파생 valuation 공개 문제를 해결하기 전 Universe는 해당 필드를 확대 노출하거나 새 장면에 사용하지 않는다.

## 영향 파일

상세는 `05-execution-validation-maintenance.md`가 정본이다. 핵심 영향 후보는 다음과 같다.

- `tests/_attempts/dartlabUniverse/ontology/assertionContract.py`
- `tests/_attempts/dartlabUniverse/projection/boundedProjection.py`
- `ui/packages/contracts/src/universe.ts`
- `ui/packages/runtime/src/data/universe/projection.ts`
- `ui/packages/runtime/src/data/universe/evidence.ts`
- `ui/packages/surfaces/src/universe/UniverseSurface.svelte`
- `ui/packages/surfaces/src/universe/components/EvidenceDrawer.svelte`
- `landing/src/lib/browser/dartlabBrowser.ts`
- `landing/src/routes/universe/+page.svelte`
- `src/dartlab/industry/types.py`
- `src/dartlab/industry/build/edges.py`
- `.github/scripts/prebuild/buildIndustryMap.py`

마지막 세 파일은 U3 승인 전 변경 대상이 아니다.

## 영향 함수/심볼

- 신규 계약: `ProjectionSpec`, `UniverseFlightPlan`, `UniverseFlightReceipt`, `SceneBeat`, `EvidenceReceipt`, `GapReceipt`, `SourceSnapshotSet`, `UniverseNode`, `UniverseRelation`, `UniverseAssertion`, `EvidencePointer`
- 신규 런타임: `compileProjection`, `compileFlightPlan`, `diffSnapshotScenes`, `compileRecipeWorkflow`, `loadProjectionLevel`, `resolveAssertionEvidence`, `applyKnowledgeCutoff`
- 기존 map artifact를 읽는 공유 로더를 atlas 우선 지연 로드 계약으로 정렬하고 `/map`과 `/universe`가 같은 구현을 소비
- 승인 후에만 변경: `IndustryEdge`, `extractDocsEdges`, `extractRawMaterialEdges`, `buildAllEdges`, `buildCompanyEgograph`, `_buildMeta`

## 테스트

- 구조: architecture, public API, UI data wiring, L1.5/L2 import 방향 회귀 0
- 데이터: 300개 reviewed positive assertion과 300개 hard negative, `OCI` 오탐, self-loop, revision, 동일 관계 다중 assertion
- 시간: `sourcePublishedAt <= availableAt`, valid interval과 knownAt 독립 필터, 미래 효력 사건 허용, query cutoff와 assertionId 독립
- 런타임: atlas 초기 전송, industry/company 지연 로드, range fetch byte budget, 실패 격리
- UX: 키보드, reduced motion, 표 대체뷰, 모바일, share URL 동일 projection 재현
- 전체 게이트: `uv run python -X utf8 tests/run.py preflight`, 해당 UI package check/test, 실제 브라우저 눈검수

## 롤백

- U1과 U2는 `/universe` route와 새 scene loader 단위로 끌 수 있다. 기존 `/map`은 변경 없이 보존한다.
- schema는 writer current, reader current 및 직전 1개 버전을 지원한다. 불일치 시 atlas-only로 fail closed한다.
- 새 artifact를 만들지 않는 U0~U2는 HF 원격 롤백이 없다.
- 승인된 U3는 기존 map manifest pointer와 `buildId`로 이전 세대를 복구한다. additive 필드만 허용하고 기존 필드 삭제는 별도 major migration으로 분리한다.
- AI 또는 3D가 실패해도 결정론 2D와 evidence drawer는 계속 동작한다.

## 평가

아래 두 렌즈로 현재 코드와 데이터에 대한 실현 가능성, 제품 목표 적합성, 장기 운영 위험을 독립 검토하고 발견한 갭을 본 설계에 반영했다.

### 전문 개발자 평가

실제 작동 가능성이 높다. 이미 atlas 27KB, industry detail, company 1-hop, 브라우저 Parquet range read, exact BM25 sidecar, cache와 request dedup이 존재한다. 가장 큰 기술 위험은 렌더러가 아니라 relation 품질과 시간 및 sourceRef 손실이다. 이 설계는 그 위험을 U0와 U2에서 먼저 닫고, L2 엔진을 서로 import시키지 않으며, UI sink가 직렬화된 evidence만 조합하게 한다. 별도 graph warehouse를 두지 않아 정정 전파와 운영 비용도 작다.

발견한 갭은 다음처럼 반영했다. 기존 20,560개 edge를 사실로 승격하지 않고 candidate로 강등했다. relation과 assertion을 분리했다. `VariableObservation`, `VintageRef`, `Ref`를 재사용했다. 별도 bake는 U3 승인 게이트로 밀었다. renderer adapter로 특정 그래프 라이브러리 종속을 막았다.

### 전문 PM 평가

사용자의 진짜 목표는 거대한 점구름이 아니라 DartLab만이 가능한 데이터 탐색 경험이다. 제품 서명은 "질문을 움직이면 변화가 보이고, 장면을 열면 주장, 반증, 원문이 이어진다"로 강화했다. `/universe`를 독립 제품 경로로 두어 브랜드와 탐색 문법을 키우고, `/map`은 현재 시장 지도 역할을 유지한다. 2D와 table을 기본으로 둔 것은 우주라는 감성을 포기한 것이 아니라 분석 가능성과 모바일 접근성을 지킨 결정이다. 3D는 증거가 있는 제품 위에만 추가한다.

발견한 갭은 사용자 수용 기준으로 반영했다. 첫 화면 속도, evidence open 시간, 공유 URL 재현, candidate와 fact의 시각 분리, 시장간 비교, 장애 시 atlas-only 동작을 제품 성공 조건으로 넣었다. "모든 데이터를 노드화"는 범위에서 제거했지만, 모든 데이터는 검색과 lens를 통해 접근 가능하게 남겨 대규모 자산의 가치를 보존했다.
