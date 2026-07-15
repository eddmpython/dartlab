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
| input | source path, buildId, 표본, cutoff |
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
| U0-I01 | canonical legal entity ID가 복원되는가 | KR 50, US 30 | exact ID 100%, ambiguous auto resolve 0 | reference resolver 우선 보강 | 대기 |
| U0-E01 | edge hint에서 exact source를 찾는가 | positive 100, negative 100 | resolution 95%, false accept 1% 이하 | predicate별 source lane 재설계 | 대기 |
| U0-O01 | revision과 시간을 보존하는가 | multi-filing fixture | history 손실 0, look-ahead 0 | assertion schema 수정 | 대기 |
| U0-P01 | bounded scene이 결정론적인가 | atlas, industry, company | bounds 100%, hash 일치 100% | priority/truncation 수정 | 대기 |
| U0-G01 | release gold를 통과하는가 | positive 300, negative 300 | precision 98%, false accept 1% 이하 | U1 금지 | 대기 |
| U2-R01 | public runtime 예산 안에서 evidence가 열리는가 | reference browsers | cold P95 5초, 2MB 이하 | runtime 최적화 후 U3 토론 | 대기 |
| U2-L01 | 엔진 output을 generic lens로 보이는가 | 6 lens fixtures | axis별 adapter 0, 결손 보존 | Ref contract 보강 | 대기 |
| U4-C01 | KR과 US가 같은 질문을 받는가 | paired 20 | 20/20 conformance | market lane 분리 유지 | 대기 |
| U5-V01 | 3D가 같은 scene을 소비하는가 | 3 scene sizes | extra truth request 0 | 3D 기각 또는 보류 | 대기 |

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

판정: graph artifact와 layout은 재사용할 가치가 있지만, 현재 edge를 factual assertion으로 재사용할 수는 없다.

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

이 중 `inspectGraphTruth`만 현재 존재한다. 나머지는 해당 attempt가 시작될 때 이름과 책임을 확정한다.

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
