# 05. Execution, Validation, and Maintenance

## 1. 실행 원칙

- 한 번에 한 phase만 완료한다.
- 새 capability는 `tests/_attempts/dartlabUniverse/`에서 실데이터로 졸업한 뒤 production으로 이동한다.
- runtime HF 직독을 먼저 소진한다.
- U3 artifact schema 확장은 측정과 운영자 승인 전 착수하지 않는다.
- `/universe`를 독립 제품 route로 만들되 `/map`, search, scan, industry, capability와 데이터 및 runtime 기능을 중복 구현하지 않는다.
- UI는 브라우저 눈검수 전 push하지 않는다.

work packet 단위 실행 순서와 commit 경계는 `07-implementation-playbook.md`, attempt 가설과 falsifier는 `08-attempts-evidence-matrix.md`, route와 release는 `09-public-route-release-contract.md`, 제품 혁신과 시각 gate는 `10-innovation-thesis-killer-workflows.md`부터 `12-innovation-validation-scorecard.md`가 정본이다.

## 2. Phase U0: Truth Gate

### 목표

현재 edge를 사실, 후보, 오류로 분류하고 assertion, source snapshot, workflow, visual grammar, public policy를 실데이터로 검증한다.

### 작업

- graph census와 anomaly report
- canonical ID resolver probe
- relation과 assertion grouping prototype
- exact sourceRef resolution probe
- reviewed positive 300개 및 hard-negative 300개 fixture
- `OCI`, self-loop, 동일 회사명, ticker 변경, 정정공시 회귀핀
- redistributionClass admission test
- SourceSnapshotSet과 change replay
- recipe to SceneBeat 및 falsifier 보존
- semantic LOD, 상태 판독, layout 결정론, renderer bakeoff
- source별 RedistributionReceipt와 LensAvailability

### 종료 조건

- positive precision >= 0.98
- hard-negative false accept <= 0.01
- fact layer sourceRef 100%
- time order 오류 0
- observed self-loop 0
- observed 단일 hub 5% 초과 0 또는 explicit reviewed whitelist
- historical replay look-ahead 0
- workflow 단계, requiredEvidence, falsifier 유실 0
- fact, candidate, derived, scenario 판독 90% 이상
- public mark policy receipt coverage 100%

## 3. Phase U1: Serverless Scene

### 목표

독립 `/universe` route에 atlas-first semantic LOD, 34개 산업 변화 우주, 첫 3개 Thesis Kill-Chain을 도입하고, 기존 `/map`은 현재 제품으로 유지한다.

### 작업

- Universe contract type 추가
- `marketMap()` 일괄 load를 meta, atlas, industry, company로 분리
- Projection Compiler와 deterministic limit
- UniverseFlightPlan, SceneBeat, EvidenceReceipt, GapReceipt
- 변화 우주 snapshot diff와 Claim Ledger
- 성장 지속성, 신용 취약, 공시 변화 workflow registry
- existing `IndustryAtlas`, `EcosystemMap`, `CompanyCard`의 low-level renderer와 artifact loader만 adapter로 재사용
- `/universe` route와 독립 `UniverseSurface` 추가
- table equivalent view
- diagnostics와 build/dataAsOf 표시

### 종료 조건

- initial map data <= 150KB gzip
- ecosystem은 explicit company view 전 network request 0
- share URL deterministic scene hash 일치
- WebGL 실패 시 table 및 SVG 동작
- baseline 대비 information yield 개선

## 4. Phase U2: Evidence on Demand

### 목표

기존 search range sidecar와 panel source에서 exact evidence를 해소한다.

### 작업

- edge hint to evidence query compiler
- search result constraints와 sourceRef 후보
- panel cited row resolver
- Evidence Drawer와 assertion timeline
- validAt 및 knownAt filter
- candidate에서 observed로 session promotion
- failure reason taxonomy

### 종료 조건

- gold 300 relation evidence resolution >= 95%
- cold P95 <= 5초, first cold transfer provisional 4MB 이하, 이후 edge incremental 2MB 이하
- unresolved edge fact promotion 0
- external content untrusted contract 위반 0

## 5. Phase U3: Approved Artifact Extension

### 선행 게이트

U2 성능 또는 성공률 예산 실패를 반복 측정하고 운영자가 명시 승인해야 한다.

### 허용 범위

- 기존 map artifact의 additive optional fields
- assertion pointer와 source/time fields
- meta quality summary와 schema version
- existing map workflow의 stage, validate, promote, rollback

### 금지

- 새 `graph/` derivative warehouse
- 별도 graph DB
- 전체 panel triple bake
- 원본 또는 search artifact 복사
- 기존 edge field 삭제

## 6. Phase U4: Cross-market

### 목표

DART와 EDGAR의 동형 panel 및 표준 finance로 동일 질문을 비교한다.

### 작업

- corpCode, CIK, security mapping
- market-specific filing deep link
- disclosureKey와 finance account alignment
- FX 및 unit normalization은 명시 lens로만
- US relation은 SEC sourceRef 있는 것만 observed

### 종료 조건

- 20개 KR/US paired question conformance
- entity name fuzzy auto-link 0
- currency 및 unit 누락 0
- dataAsOf mismatch 표시 100%

## 7. Phase U5: Galaxy Lens

### 선행 게이트

- U0~U4 제품 졸업
- renderer interface 안정
- 2D와 table product task 100% 유지
- dependency license 및 bundle review 통과

### 종료 조건

- 같은 ProjectionSpec과 scene hash 사용
- mobile 자동 off
- peak heap 및 fps 예산 통과
- 3D 전용 truth 또는 기능 0

## 7.1 Phase U6: Public Beta and GA

### 목표

같은 `/universe` route를 local review, public beta, GA 순서로 승격하고 운영 계약을 실제 장애와 rollback으로 검증한다.

### 작업

- production build의 실제 `/universe` 눈검수
- desktop 및 mobile network, heap, accessibility 검증
- public beta 14일 SLO 관찰
- relation lane, renderer, route, map buildId rollback drill
- navigation, SEO, share URL, stale buildId 동작 확인

### 종료 조건

- critical incident 0
- fact sourceRef coverage 100%
- hard negative false accept 1% 이하
- atlas availability 99.9%
- rollback 15분 이내
- 운영자 UI 눈검수와 push 승인

## 영향 파일

변경 범위는 U0 attempts, U1~U2 runtime 및 surface, 승인 후 U3 builder로 분리한다. 각 phase는 아래 명시 경로 밖의 파일을 임의로 넓히지 않는다.

### U0 신규 attempts

- `tests/_attempts/dartlabUniverse/truth/graphTruthProbe.py`: source, type, degree, hub, self-loop, evidence coverage
- `tests/_attempts/dartlabUniverse/identity/entityIdentityProbe.py`: corpCode, CIK, security 분리
- `tests/_attempts/dartlabUniverse/evidence/exactEvidenceProbe.py`: edge hint에서 sourceRef 찾는 실험
- `tests/_attempts/dartlabUniverse/ontology/assertionContract.py`: canonical payload, assertionId, admission rule
- `tests/_attempts/dartlabUniverse/projection/boundedProjection.py`: semantic LOD, deterministic truncation, time filter
- `tests/_attempts/dartlabUniverse/snapshot/`: SourceSnapshotSet과 change replay
- `tests/_attempts/dartlabUniverse/workflow/`: recipe, SceneBeat, falsifier와 information yield
- `tests/_attempts/dartlabUniverse/visual/`: 상태 판독, layout, density, accessibility, renderer bakeoff
- `tests/_attempts/dartlabUniverse/policy/`: RedistributionReceipt와 LensAvailability
- `tests/_attempts/dartlabUniverse/fixtures/reviewedPositive.jsonl`: reviewed positive
- `tests/_attempts/dartlabUniverse/fixtures/hardNegative.jsonl`: 오탐과 충돌
- `tests/_attempts/dartlabUniverse/README.md`: Inputs, Method, Results, Limits, Decision 원장

### U1 및 U2 production 후보

- `ui/packages/contracts/src/universe.ts`: projection 및 scene type
- `ui/packages/contracts/src/index.ts`: contract export
- `ui/packages/runtime/src/data/universe/projection.ts`: compile, filters, stable limits
- `ui/packages/runtime/src/data/universe/load.ts`: LOD loader, DataCore only
- `ui/packages/runtime/src/data/universe/evidence.ts`: search 및 panel evidence resolver
- `ui/packages/runtime/src/data/universe/time.ts`: validAt, knownAt filter
- `ui/packages/runtime/src/data/universe/index.ts`: public runtime exports
- `ui/packages/surfaces/src/universe/UniverseSurface.svelte`: scene orchestrator
- `ui/packages/surfaces/src/universe/components/EvidenceDrawer.svelte`: assertion and source surface
- `ui/packages/surfaces/src/universe/components/TimeLens.svelte`: bitemporal controls
- `ui/packages/surfaces/src/universe/components/LensTray.svelte`: existing capability lens selection
- `ui/packages/surfaces/src/universe/components/RelationTable.svelte`: graph-equivalent accessible view
- `ui/packages/surfaces/src/universe/renderers/canvas2dRenderer.ts`: U0-V06에서 승격한 dependency-free bounded graph adapter
- `ui/packages/surfaces/src/map/components/EcosystemMap.svelte`: UniverseRenderer adapter
- `ui/packages/surfaces/src/map/components/IndustryAtlas.svelte`: scene input adapter
- `ui/packages/surfaces/src/universe/index.ts`: exports
- `landing/src/lib/browser/dartlabBrowser.ts`: atlas-first loader methods
- `landing/src/lib/browser/types.ts`: bundle types
- `landing/src/routes/universe/+page.ts`: initial meta 및 atlas only
- `landing/src/routes/universe/+page.svelte`: Universe shell and state

### U3 승인 후 후보

- `src/dartlab/industry/types.py`: assertion-aware additive contract
- `src/dartlab/industry/build/edges.py`: exact source fields, no destructive assertion dedup, mention boundary guard
- `.github/scripts/prebuild/buildIndustryMap.py`: company edge assertion pointer와 meta quality summary
- `.github/workflows/mapBuild.yml`: candidate validate, promote, rollback evidence
- `src/dartlab/skills/specs/engines/industry/SKILL.md`: 실제 public edge 반환 계약 동기화

### 건드리지 않는 정본

- `src/dartlab/ai/contracts.py`: `Ref` 재사용, 중복 Universe ref type 금지
- `src/dartlab/simulate/stateCompiler.py`: observation 시간 의미 재사용
- `src/dartlab/simulate/vintage.py`: vintage 시간 인과 재사용
- `src/dartlab/reference/capability/builder.py`: capability live builder 유지
- `ui/packages/runtime/src/data/fetch/request.ts`: DataCore 소비, Universe 전용 fetch core 신설 금지

## 영향 함수/심볼

| 심볼 | phase | 계약 |
|---|---|---|
| `ProjectionSpec` | U1 | scene 요청, content hash ID |
| `UniverseNode` | U1 | stable entity presentation |
| `UniverseRelation` | U0/U1 | grouped assertion view |
| `UniverseAssertion` | U0/U2 | evidence, time, status, policy |
| `compileProjection` | U1 | deterministic bounded scene |
| `loadUniverseMeta` | U1 | meta only |
| `loadMarketAtlas` | U1 | atlas only |
| `loadIndustryProjection` | U1 | L2 lazy |
| `loadCompanyProjection` | U1 | L3 lazy |
| `resolveAssertionEvidence` | U2 | hint to exact Ref |
| `applyKnowledgeCutoff` | U2 | availableAt and knowledgeAsOf filter |
| `marketMap` | U1 | `/map` compatibility wrapper, eager default 금지 |
| `IndustryEdge` | U3 | additive compatibility only |
| `extractDocsEdges` | U3 | partial substring match 금지, source row 보존 |
| `buildAllEdges` | U3 | assertion 보존, relation grouping은 후단 |
| `buildCompanyEgograph` | U3 | optional assertionRefs serialization |
| `_buildMeta` | U3 | counts, quality, schema and source freshness |

## 테스트

테스트는 data quality, contract, time, runtime, UX의 다섯 묶음으로 실행하고, 각 production phase는 대응 묶음이 같은 커밋에 동행해야 한다.

### U0 data quality

- `OCI`가 일반 영문 content에서 entity match되지 않음
- exact 법인 표기와 alias boundary는 match
- from과 to가 같은 assertion 차단
- 같은 relation의 다른 period와 rceptNo가 서로 다른 assertionId
- revision이 이전 assertion을 삭제하지 않음
- sourceRef 없는 directText는 candidate 유지
- `localOnly` 및 `unknown`은 public projection에서 차단

### contract

- canonical JSON key order와 hash 결정론
- current 및 previous schema reader fixture
- unknown optional field ignored
- unknown predicate와 redistribution class fail closed
- maxNodes, maxEdges, maxDepth hard bound
- same spec, same sources, same scene hash

### time

- `sourcePublishedAt <= availableAt`
- valid interval과 knownAt 독립 변화
- 미래 효력 event 또는 validFrom 허용
- query knownAt과 assertionId 독립
- future filing look-ahead 차단
- corrected filing as-known 재현
- missing time은 0이나 오늘로 채우지 않고 unknown

### runtime

- atlas request에 ecosystem request 0
- company load 전 company JSON request 0
- request dedup 동일 range 1회
- failure가 cache success로 남지 않음
- evidence resolver byte budget
- stale snapshotSetId, legacy buildId, schema mismatch를 구분하고 fail closed
- WebGL context loss table fallback

### UX

- fact, candidate, derived, scenario 패턴 스냅샷
- keyboard node와 relation selection
- screen reader relation summary
- reduced motion
- mobile 320, 375, 768 widths
- share URL round trip
- Evidence Drawer source deep link

### Guard Index 및 전체 게이트

구현 착수 시 `operation.testing`, `operation.code`, `operation.architecture`의 Guard Index 절차로 실제 selector를 확정한다. 최소 실행은 다음과 같다.

```powershell
uv run python -X utf8 tests/run.py preflight
```

추가로 영향 package의 check와 test, `/universe` 및 `/map` 실제 브라우저 눈검수, HF range 실측을 수행한다. 전체 `pytest tests/ -v`는 사용하지 않는다.

## 8. 3년 유지보수 모델

### 소유권

| 계약 | owner | review trigger |
|---|---|---|
| entity ID | reference | listing, CIK, ticker mapping 변경 |
| sourceRef 및 filing | gather/providers/search | source schema 및 deep link 변경 |
| relation predicate | industry | extractor 또는 taxonomy 변경 |
| observation | source engine | unit, frequency, revision 변경 |
| capability lens | capability/skills owner | docstring, returns, requiredEvidence 변경 |
| projection | UI runtime | scene contract 및 cache 변경 |
| rendering | UI surfaces | dependency, browser, accessibility 변경 |
| public policy | data source owner | license 또는 redistribution 변경 |

### release cadence

- daily: source freshness와 current artifact health
- weekly: assertion canary, hub anomaly, unresolved evidence rate
- monthly: reviewed gold 추가, dependency 및 browser matrix
- quarterly: schema compatibility, predicate registry, storage staging retention report
- annually: major migration 필요성, vendor and license review, dead surface removal

### schema 및 deprecation

- minor additive field는 changelog와 fixture 동행
- major는 RFC, dual-reader, shadow report, cutover evidence 필요
- previous reader 제거는 90일 또는 2개 minor release 중 긴 기간 이후
- predicate deprecation은 `deprecatedBy`와 migration rule 제공
- share URL schema는 최소 1년 read compatibility 목표

### 데이터 수명주기

- Truth Plane current: source owner retention
- compatibility docs: 삭제 금지, scene source에서는 제외
- search staging: search ops가 current pointer와 rollback window 기준으로 관리
- browser cache: snapshotSetId namespace와 bounded TTL, legacy map source는 buildId 포함
- session assertion: local cache only, source truth로 자동 승격 금지
- approved map assertion pointer: existing map lifecycle과 함께 stage/promote/rollback

### 품질 flywheel

- unresolved edge click을 로컬 diagnostics로 export 가능
- 운영자 review 후 gold 또는 hard negative로 승격
- gold는 predicate, language, market, source, evidence class 균형 유지
- auto-generated candidate는 release gold로 인정하지 않음
- precision gate를 먼저 지키고 candidate recall은 별도 추적

### dependency와 vendor 관리

- renderer adapter 밖에서 vendor type import 금지
- dependency lockfile, license, bundle diff, browser support 기록
- 3D dependency는 optional chunk
- package가 폐기돼도 table, SVG atlas, DataCore, ProjectionSpec은 유지
- Cosmograph full product의 상업 조건과 현재 open-source cosmos renderer를 혼동하지 않음

### 운영 SLO

| SLO | 목표 | breach 대응 |
|---|---:|---|
| atlas availability | 99.9% | previous build or atlas-only |
| fact sourceRef coverage | 100% | candidate 강등 |
| data freshness disclosure | 100% | stale badge와 source lane 차단 |
| evidence P95 | <= 5s | U2 optimize, U3 approval review |
| hard negative false accept | <= 1% | predicate lane disable |
| public localOnly leak | 0 | release block, artifact rollback |

### 장애 playbook

- source stale: 해당 lens만 stale 처리, graph identity 유지
- map bad build: previous buildId로 pointer rollback
- relation false-positive spike: predicate/source lane feature flag off
- schema mismatch: atlas-only fail closed
- browser memory regression: max scene limit 하향, table default
- renderer vulnerability: renderer adapter disable, SVG/table 유지
- license issue: redistributionClass source lane 즉시 차단

## 롤백

롤백 단위는 phase와 schema version이다. 한 source나 renderer 실패가 `/map`까지 되돌리게 만들지 않고, `/universe`의 가장 작은 안전 단위만 비활성화한다.

### U0

attempts와 docs만 있다. production 영향 0.

### U1

기존 `/map`과 `marketMap()`을 유지한다. `/universe` release state를 disabled로 바꾸면 기존 map과 data artifact는 변하지 않는다.

### U2

Evidence Drawer와 resolver를 끄면 relation은 candidate-only로 남는다. sourceRef 없는 edge를 fact로 fallback하지 않는다.

### U3

additive schema만 허용한다. current manifest를 이전 buildId로 되돌리고, current/previous dual reader로 기존 client를 보호한다. 원격 파일 삭제는 롤백 방법이 아니며 사용하지 않는다.

### U4

market filter를 KR-only로 되돌린다. KR canonical ID와 scene은 영향받지 않는다.

### U5

3D chunk와 toggle을 제거하고 2D renderer를 유지한다. data 및 URL contract는 동일하다.

## 평가

기술 정확성과 제품 완결성을 별도로 검토했으며, 두 평가에서 발견한 관계 품질, runtime SSOT, 3D 우선순위, cross-market 범위 문제를 phase와 gate에 반영했다.

### 전문 개발자 평가

가장 어려운 부분은 대규모 렌더링이 아니라 identity, assertion, time, evidence다. 현재 browser runtime은 range와 cache가 이미 서 있어 500개 이하 scene은 충분히 가능하다. 반면 current edge extractor는 부분문자열과 destructive dedup 때문에 factual graph로 사용할 수 없다. 그래서 U0와 U2를 선행하고 U3를 승인 게이트로 둔 순서가 맞다.

장기 유지보수 면에서는 새 graph server와 새 공개 엔진을 만들지 않는 결정이 가장 중요하다. capability를 standard ref로 소비하면 147축 adapter가 생기지 않는다. L2 cross import도 피한다. renderer, projection, source truth가 분리되어 vendor 교체와 데이터 수정이 독립적이다.

### 전문 PM 평가

제품은 "우주처럼 보인다"가 아니라 "데이터가 연결되고 근거로 돌아간다"로 성공을 정의한다. `/universe` 독립 route가 이 약속의 owner다. 사용자가 즉시 체감할 순서는 atlas 속도, fact와 candidate 분리, evidence drawer, time lens다. 3D를 마지막에 둔 것은 scope 축소가 아니라 거짓 relation을 화려하게 확대하는 위험을 제거한 것이다.

MVP는 KR relation에서 시작하지만 DART와 EDGAR 동형 panel을 계약에 포함해 cross-market 천장을 열어뒀다. 모든 관측을 node로 만들지 않아도 search와 lens로 58GB active truth를 접근할 수 있으므로 "엄청난 양의 데이터"라는 목표를 잃지 않는다.
