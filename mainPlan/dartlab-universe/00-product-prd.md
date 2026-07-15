# 00. Product PRD

## 1. 문제 정의

DartLab에는 한국과 미국 공시, 재무, 주가, 거시, 뉴스 메타, 산업 관계, 검색 인덱스와 147개 핵심 엔진 축이 있다. 지금 사용자는 이를 회사 화면, 검색, 스크리너, 산업 지도, AI 답변으로 따로 경험한다.

문제는 데이터가 적어서가 아니다.

- 어떤 데이터가 어떤 엔진과 연결되는지 한눈에 보이지 않는다.
- 산업 지도 관계가 정확한 문서, 시점, 공개 가능 시점으로 돌아가지 못한다.
- 전량 그래프는 커 보이지만 질문에 답하는 밀도는 낮다.
- 숫자, 문장, 산업 관계, 계산 결과, 시나리오가 한 장면에서 사실처럼 섞일 위험이 있다.
- public 정적 웹과 local 분석 환경이 다른 데이터 경로를 만들면 장기 유지보수가 무너진다.

## 2. 제품 한 문장

**DartLab Universe는 질문을 변화, 주장, 반증, 원문으로 컴파일하고, 공시와 시장 데이터 및 기존 엔진을 재현 가능한 장면으로 투영하는 evidence-native 금융 우주다.**

## 3. 제품 서명

회사를 선택한 뒤 5초 안에 다음 질문의 답 또는 답할 수 없는 이유를 열 수 있어야 한다.

1. 이 회사는 산업과 밸류체인 어디에 있는가.
2. 누구와 어떤 관계가 있는가.
3. 그 관계를 어떤 공시의 어느 시점에서 확인했는가.
4. analysis, credit, macro, quant, scan 렌즈로 보면 무엇이 달라지는가.
5. 두 시점 사이에서 무엇이 생기고 정정되고 사라졌는가.
6. 현재 thesis를 깨뜨릴 가장 가까운 falsifier는 무엇인가.

대표 제품 서명은 P0 변화 우주와 Thesis Kill-Chain이다. P1은 판정 우주와 한미 Twin이다. 전량 3D와 자동 충격 전파는 대표 기능이 아니다.

## 4. 목표 사용자와 핵심 작업

| 사용자 | 핵심 작업 | 제품 응답 |
|---|---|---|
| 개인 투자자 | 회사의 공급망과 위험을 빠르게 이해 | 회사 중심 1-hop, 관계 상태, 근거 drawer, 신용 및 재무 렌즈 |
| 분석가 | 특정 시점에 알 수 있던 사실만 재구성 | validAt와 knowledgeAsOf 이중 시간 필터, revision 보존 |
| 개발자 및 데이터 사용자 | DartLab 데이터와 엔진의 연결을 이해 | capability lens, source path, projection JSON, share URL |
| 교육 사용자 | 거시에서 산업, 회사, 재무로 인과를 따라감 | 6막 camera path와 단계별 설명 |
| AI agent | 검산 가능한 작은 작업 공간을 요청 | ProjectionSpec, bounded evidence bundle, Ref 목록 |

## 5. 네 평면 제품 모델

### Truth Plane

HF Parquet과 기존 map 및 search artifact가 데이터 정본이다. Universe는 이를 복사해 새 진실을 만들지 않는다.

### Meaning Plane

개체 ID, 관계 predicate, assertion, 시간, sourceRef, 공개 경계를 정의한다. 의미 계약은 렌더러와 독립이다.

### Lens Plane

엔진은 그래프의 노드가 아니다. 같은 evidence bundle을 수익성, 신용, 매크로, 정량, 산업, 횡단 비교 관점으로 바꾸는 연산 렌즈다. 새 엔진별 UI adapter 대신 표준 `Ref`, `tableRef`, `valueRef`, `dateRef`를 projection 입력으로 받는다.

### Scene Plane

사용자 질문과 zoom level에 따라 작은 subgraph와 표 및 시계열을 만든다. scene은 disposable하며 정본이 아니다.

## 6. 대표 시나리오

### S1. 삼성전자 공급망 근거 추적

1. 34개 산업 atlas에서 반도체를 연다.
2. 삼성전자를 선택한다.
3. 기본 사실 레이어에는 sourceRef를 확인한 관계만 보인다.
4. 후보 레이어를 켜면 저신뢰 본문 매칭이 점선으로 추가된다.
5. 엣지를 클릭하면 접수번호, 기간, sectionPath, 원문 snippet과 공개 가능 시점이 열린다.
6. credit 렌즈를 켜면 연결사의 취약축을 색으로 덧입히되 관계 사실과 계산을 분리한다.

### S2. 변화 우주

1. knownAt A와 B를 선택한다.
2. 산업 및 회사 위치는 유지하고 created, corrected, retracted, newlyKnown만 남긴다.
3. 변화 하나를 열면 before와 after source span 또는 table cell이 열린다.
4. 현재값이 과거 장면에 역주입되지 않았음을 SourceSnapshotSet receipt로 확인한다.

### S3. Thesis Kill-Chain

1. 회사와 성장 지속성 thesis를 선택한다.
2. tested recipe가 assumption, fragility, trigger, tripwire, falsifier를 선언한다.
3. 각 단계는 observed, derived, missing, scenario lane 중 하나에 놓인다.
4. falsifier가 없는 주장은 결론으로 승격하지 않는다.
5. 사용자는 claim에서 exact 원문과 현재 판정까지 왕복한다.

### S4. DART와 EDGAR 비교

1. 삼성전자와 Apple을 seed로 선택한다.
2. 같은 `disclosureKey`, 표준 재무 account, 기간 빈도를 맞춘다.
3. 시장별 공시 원문과 정규화 결과를 나란히 연다.
4. 교차시장 관계를 회사명 유사도로 자동 생성하지 않는다.

### S5. 질문을 flight plan으로 변환

질문: "반도체 공급망 중 최근 2년 수익성은 좋아졌지만 신용 취약축이 있는 회사"

- public deterministic 경로: 산업, 기간, metric, credit 조건을 Lens Tray에서 선택한다.
- AI 경로: 기존 Workbench가 skill과 capability를 선택하고 `UniverseFlightPlan`과 그 안의 `ProjectionSpec`을 만든다.
- 두 경로는 같은 projection executor, `SceneBeat[]`, EvidenceReceipt를 사용한다.

## 7. MVP 범위

- public `/universe` 독립 route와 검색, lens, scene, evidence 제품 shell
- 기존 atlas, timeline, movers를 사용한 34개 산업 변화 우주
- 성장 지속성, 신용 취약, 공시 변화 3개 Thesis Kill-Chain
- 기존 map artifact의 atlas, industry, company 3단계 LOD를 공유 런타임에서 지연 로드
- fact와 candidate relation의 시각 및 데이터 계약 분리
- exact evidence를 on demand로 해소하는 Evidence Drawer
- validAt, knowledgeAsOf, dataAsOf 표시
- 기존 산업, 재무, 신용, scan metric을 lens로 적용
- share URL로 seed, filters, lens, time, snapshotSetId, flight plan 재현
- graph와 동등한 table/list view

## 8. 명시적 비목표

- 275.76GB 전량을 노드로 변환
- 모든 공시 문단을 영구 knowledge graph triple로 변환
- Neo4j, RDF endpoint, GraphQL graph server 신설
- LLM이 근거 없이 predicate를 발명하거나 relation을 승격
- 3D를 기본 분석 UI로 사용
- 현재 저신뢰 20,560개 relation을 검증 없이 사실로 공개
- 네이버 localOnly 데이터의 public 확대 노출
- 새 공개 Python 엔진이나 별도 public API surface 신설
- `/map`을 `/universe`로 이름만 바꾸거나 두 route에 동일 화면을 복사
- existing ShockSimulator의 양방향 BFS 또는 임의 감쇠 재사용
- single score로 PASS, FAIL, MISSING 혼합
- source snapshot 없이 exact historical replay 약속

## 9. 성공 지표

### 제품 지표

- atlas cold first data <= 1.5초, 초기 map 데이터 <= 150KB gzip
- industry scene cold <= 2.5초, company scene cold <= 3.5초
- evidence drawer cold P95 <= 5초, warm P95 <= 1.5초
- 공유 URL을 같은 SourceSnapshotSet에서 열면 scene, claim, receipt, filter, lens가 byte-stable하게 재현
- 기본 사실 레이어 assertion sourceRef coverage 100%
- fact와 candidate를 구분하지 못한 usability test 0건
- graph 비지원 환경에서도 table view로 핵심 작업 100% 수행
- baseline 대비 검증 가능한 claim 또는 falsifier의 information yield 개선

### 품질 지표

- reviewed positive 300건 precision >= 0.98
- hard negative 300건 false acceptance <= 0.01
- self-loop 0건, duplicate assertionId 0건
- 단일 비화이트리스트 entity가 observed edge의 5% 초과 시 release 차단
- 시간 순서 오류 0건
- public scene의 `localOnly` provenance 0건

### 유지보수 지표

- 새 데이터 엔진 추가가 Universe core 변경 없이 standard Ref로 렌더 가능
- schema major migration 연 1회 이하
- current와 직전 1개 reader 호환
- 데이터 갱신 실패가 atlas와 기존 회사 화면을 함께 중단시키지 않음
- 서버 0 public floor 유지

## 10. 단계별 가치

| 단계 | 사용자 가치 | 기술 가치 | 종료 조건 |
|---|---|---|---|
| U0 | 거짓 관계를 사실로 보지 않음 | assertion 및 품질 계약 | gold와 hard negative 통과 |
| U1 | 빠른 우주 탐색 | semantic LOD와 lazy load | atlas, industry, company 성능 예산 통과 |
| U1-A | 산업 변화가 보임 | SourceSnapshotSet과 change diff | look-ahead 0, before/after evidence 95% |
| U1-B | thesis를 반증 가능하게 조사 | recipe to SceneBeat compiler | 단계, 근거, falsifier 유실 0 |
| U2 | 클릭하면 원문으로 돌아감 | Evidence on Demand와 receipt | fact layer sourceRef 100% |
| U3 | 필요한 경우 근거 조회 가속 | 기존 map additive schema | 런타임 실패 실측과 승인 |
| U4 | 한국과 미국 비교 | stable global IDs와 cross-market panel | 동일 질문 20개 conformance |
| U5 | 발견과 공유의 우주 감성 | renderer adapter | 2D 졸업 후, 성능 및 접근성 동등 |
