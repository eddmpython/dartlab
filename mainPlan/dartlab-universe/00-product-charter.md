# 00. 제품 헌장과 불변식

## 1. 제품 명제

DartLab이 이미 가진 데이터와 계산 능력은 강하지만 사용자가 전체를 한 지식 공간으로 탐색할 수 없다. 지금은 HF 파일, DART와 EDGAR provider, 엔진 axis, 블로그 글, 이미지, 영상, 로컬 시뮬레이션이 각자의 올바른 거처에 나뉘어 있다. 문제는 분산 자체가 아니라 전체를 빠짐없이 주소화하고 같은 근거 언어로 연결하는 계층이 없다는 점이다.

DartLab Universe는 원천을 한곳으로 복사하는 데이터 레이크가 아니다. 다음 질문에 기계적으로 답하는 지식·질의 엔진이다.

- 무엇이 존재하는가.
- 정확히 어디에 있고 어떤 revision인가.
- 무엇과 어떤 근거로 연결되는가.
- 그 값은 관측, 계산, 시뮬레이션, 사람 주장, 모델 추론 중 무엇인가.
- 어떤 시점에 유효했고 언제 알 수 있었는가.
- 같은 질문과 엔진 호출을 다시 재현할 수 있는가.
- 전체에서 문서, 섹션, 표, 행, 셀, 원문까지 내려갈 수 있는가.

## 2. 단 하나의 전체 우주

Universe의 최상위 root는 하나다.

```text
dartlab:universe
  contains market, organization, instrument, dataset, filing, section,
  table, row locator, cell locator, concept, statement, evidence,
  blog post, paragraph, image, video, capability, execution, scenario
```

시장과 출처는 partition key이자 filter이지 별도 우주가 아니다. DART와 EDGAR는 동일한 전체 안의 동등한 1급 source authority다. 한국 회사와 미국 회사도 서로 다른 우주가 아니라 서로 다른 identifier namespace와 회계·공시 관할을 가진 객체다.

### 2.1 제품 범위의 세 축

| 축 | 포함 기준 | 축소 금지 |
|---|---|---|
| HF 전체 | DartLab 설정이 가리키는 모든 HF 저장소의 라이브 트리와 media repo 전체 | public 파일이나 현재 레지스트리 항목만 고르는 것 금지 |
| 엔진 전체 | `dartlab.capabilities()`, 실존 axis registry, Company facade, root facade와 프로젝트 계약 엔진 folder census의 합집합 | 문서에 적힌 표본 axis만 등록하거나 noncallable folder를 callable로 위장 금지 |
| 콘텐츠 전체 | 모든 blog `index.md`, frontmatter, AST block, 문장, 표, 코드, 링크, 인용, 이미지, 영상 locator | 대표 글·대표 이미지만 임베딩 금지 |

EDGAR는 후속 범위가 아니다. HF의 `edgar/*`, `providers/edgar`, `OpenEdgar`, EDGAR Company surface와 관련 capability를 DART와 같은 G0 census에서 다룬다.

## 3. "모든 데이터"의 운영 정의

전체를 브라우저 메모리에 올리거나 모든 행을 영구 graph node로 만드는 것이 아니다. 모든 발견 항목이 아래 성숙도 중 어디까지 도달했는지 증명하는 것이다.

| 단계 | 이름 | 판정 |
|---|---|---|
| C0 | DISCOVERED | authoritative source census에 나타남 |
| C1 | ADDRESSABLE | revision 고정 locator로 다시 열 수 있음 |
| C2 | STRUCTURED | 형식, 스키마, 크기, 행수 또는 미디어 메타를 해석함 |
| C3 | IDENTIFIED | canonical object 또는 unresolved identity bucket에 연결됨 |
| C4 | RETRIEVABLE | structured, lexical 또는 graph query로 근거까지 찾을 수 있음 |
| C5 | RAG_ELIGIBLE | 권한, 신뢰 유형, 시간, citation locator가 완전함 |

G0 합격은 C0와 C1이 100%이고 실패 항목 수가 0인 상태다. 의미를 모르는 파일도 삭제하거나 숨기지 않는다. C1의 `UNCLASSIFIED` resource로 남기고 C2 미달 사유를 기록한다. 행과 셀은 business key와 revision을 가진 가상 locator로 지연 해소한다.

## 4. 제품 불변식

### U01. 원천 SSOT 불변

HF, 블로그 git, 엔진 registry, 기존 runtime이 원천이다. Universe catalog와 query 결과는 원천을 가리키는 논리 상태다. 원문, parquet, 이미지를 별도 canonical copy로 만들지 않는다. 명시 승인된 engine output byte는 execution receipt 재현용 `DERIVED_OUTPUT`으로만 local CAS에 둘 수 있으며 source authority로 승격하지 않는다.

### U02. 기존 시스템 무지 원칙

기존 엔진, provider, simulator, UI data workbench는 Universe를 import하지 않는다. Universe만 외부에서 공개 surface를 읽는다. 의존 방향 역전은 즉시 실패다.

### U03. 런타임 우선

census, catalog, identity, provenance, query는 원천에서 런타임 계산하는 것이 기본이다. prebuild, bake, 재청크, 영속 파생 index는 런타임 불가를 수치로 증명하고 운영자에게 대안을 설명한 뒤 명시 승인을 받기 전 금지한다.

### U04. 사실 종류 분리

`OBSERVED`, `DERIVED`, `SIMULATED`, `ASSERTED`, `INFERRED`는 저장, 질의, 시각 표현에서 항상 분리된다. 모델 추론이나 블로그 주장이 관측 사실로 자동 승격되는 경로는 없다.

### U05. 재현 가능한 주소

모든 statement는 evidence 또는 derivation을 가진다. locator, source revision, 시간, engine version, parameter, seed 중 필요한 하나라도 없으면 `VERIFIED`가 될 수 없다.

### U06. 동적 전체성

현재 파일 수, 회사 수, 글 수를 상수로 코딩하지 않는다. snapshot마다 discovered, registered, excluded, failed, unresolved를 다시 계산한다.

### U07. 3D 비권위

좌표, cluster, tile, 색, 크기는 projection 결과다. 화면에서 가까워 보인다는 사실은 지식 관계의 근거가 아니다.

### U08. 공개 통제

내부 엔진과 3D가 완성되어도 운영자 직접 검수 전 `/universe` 공개 route, 버튼, 메뉴, sitemap, search 노출은 만들지 않는다. 내부 검수 surface가 필요하면 기존 공개 app이 아닌 격리된 local attempts runner를 사용한다.

### U09. 3D가 없어도 동등한 지식 접근

검색, 객체 상세, 관계, 근거, 원문 drill-down은 3D renderer가 없어도 CLI와 의미 tree에서 가능해야 한다. 3D는 유일한 접근 경로가 아니다.

### U10. 질문이 지식을 오염하지 않음

질문 결과와 임시 성좌 overlay는 session state다. 사용자가 저장해도 question, query plan, evidence refs, execution receipts를 가진 별도 session object로 남고 canonical graph에 자동 merge되지 않는다.

## 5. 사용자 가치

### 5.1 조사자

기업 하나에서 시작해 공시, 계정, 산업 관계, 뉴스, 블로그 해설, 관련 엔진 결과를 한 provenance path로 내려간다. 원문 한 셀까지 검증할 수 있다.

### 5.2 분석가

"이 회사의 현금흐름 악화가 산업과 금리 경로에서 어떻게 보이는가"를 structured query와 existing engine call로 재현한다. 숫자마다 입력 revision과 실행 receipt가 붙는다.

### 5.3 학습자

전체 지식 공간을 이동하며 개념과 실제 기업·공시·표의 연결을 본다. 블로그 문장은 설명으로 읽되 원천 사실과 구분한다.

### 5.4 미래 RAG 사용자

우주에 질문을 던지고 답변 문장마다 데이터 locator, 엔진 호출, 반대 근거, 불확실성을 확인한다. 공간 선택은 검색 prior일 뿐 근거를 대체하지 않는다.

## 6. 비목표

- 주가를 맞히는 예측기
- 매수·매도·목표주가를 선언하는 화면
- 출처별 2D force graph 여러 개
- 모든 파일을 새 DB로 복사하는 중앙 저장소
- 모든 행·셀을 선생성한 초대형 property graph
- 기존 엔진 내부 함수를 직접 호출하는 shortcut
- 블로그 본문을 trusted prompt로 넣는 LLM demo
- Three.js나 특정 renderer에 종속된 지식 모델
- static landing에서 Python 엔진을 흉내 내는 계산
- 현재 2,664개 또는 어떤 기업 수를 전체 범위로 고정하는 것

### 6.1 형제 계획 경계

`mainPlan/_done/dartlab-lens-product-architecture/`는 기존 제품 렌즈와 대표 workflow를 다루는 완료된 별도 사용자 작업이다. 본 계획은 그 파일을 수정하거나 흡수하지 않는다. 현재 운영자 지시에 따라 Universe 데이터 엔진의 독립 attempts는 설계하되, 기존 렌즈·route·UI의 공개 순서와 결합 여부는 U8 이후 다시 결정한다.

## 7. 데이터 엔진 완성의 제품 판정

렌더러 없이 다음 15개가 모두 증명돼야 데이터 엔진이 완성된다.

1. configured HF authority repo 집합의 live tree가 revision과 함께 100% census된다. 현재 관측 configured repo는 4개지만 제품 상수가 아니다.
2. 등록 레지스트리에 없는 live path도 orphan로 숨김 없이 나타난다.
3. 실제 callable capability가 100% catalog되고 가짜 axis가 0개다.
4. eligible callable의 input/output `SchemaDescriptor`가 100% 검증되고 불완전 schema 실행이 0개다.
5. blog 본문, companion artifact와 media의 참조·미참조·깨진 참조가 전수 집계된다.
6. 동일 snapshot 재실행의 logical ID 일치율이 100%다.
7. 모든 verified statement의 evidence 또는 derivation coverage가 100%다.
8. DART와 EDGAR가 동일 identity resolution 규칙과 충돌 보존 규칙을 쓴다.
9. engine execution이 timeout, cancel, retry, seed, output digest를 durable receipt로 남긴다.
10. simulator 결과가 signed admission과 artifact semantic descriptor 검증을 모두 통과하고 `SIMULATED`를 벗어나지 않는다.
11. exact identifier Recall@1이 100%다.
12. 3D 없이 object에서 원문 locator까지 drill-down된다.
13. schema와 row-count C2 descriptor crawl이 모든 structured candidate를 terminal 상태로 종결한다.
14. control-plane head에서 identity, mapping, taxonomy, schema, license, receipt, approval을 100% 역추적한다.
15. 기존 source file 변경이 0개임을 content digest와 git diff로 증명한다.

## 8. 공개 승인 계약

공개는 구현 완료의 자동 결과가 아니다. 다음을 모두 만족하고 운영자가 명시적으로 승인해야 한다.

- G0부터 G7까지 기계 gate 통과
- 내부 검수용 녹화 또는 직접 실행에서 운영자 확인
- 공개할 route, button, nav 위치를 별도 UI 변경안으로 제시
- UI 변경이 기존 data workbench를 경유함을 검증
- 접근성, 보안, 라이선스 검토 통과
- rollback이 한 commit 또는 feature flag로 가능한 상태

승인 문구가 없으면 공개 변경은 0개다.
