# 04. 검증과 진행 원장

## 1. 단계

| 단계 | 목표 | 상태 |
|---|---|---|
| W0 | 전문가 토론, 저장소 전수 조사, 범위와 API 확정 | 완료 |
| W1 | PRD, ADR, 계약, 보호 경계 확정 | 완료 |
| W2 | data package, owner discovery, catalog | 완료 |
| W3 | query, PIT, typed projection, bounded result | 완료 |
| W4 | simulator adoption과 parity | 완료 |
| W5 | public facade, external smoke, Skill OS | 완료 |
| W6 | compatibility cleanup와 완료 감사 | 완료 |
| W7 | Signature Data Prism 혼합 query, evidence, quality, Arrow | 완료 |
| W8 | 170개 전수 실행, selector, 빈 결과, 동시성 hardening | 완료 |
| W9 | 실제 content 봉인, 외부 구조 보존, 전종목 자동 page 소비 | 완료 |
| W10 | 공통 feature observation 계약과 실제 EDGAR PIT factor 수직 슬라이스 | 완료 |
| W11 | EDGAR 현재 상장 universe 계산 feature runtime continuation | 완료 |

## 2. unit과 contract test

- catalog no-arg와 검색
- unknown axis fail-fast
- descriptor schema validation
- duplicate asset ID와 version drift
- owner package 추가 시 중앙 목록 변경 0
- descriptor 없는 package가 `UNCLASSIFIED_OWNER`로 표면화
- discovery network call 0
- native, records, factor, graph, narrative, resource projection
- incompatible projection preflight reject
- validAt, knownAt, availableAt ordering
- PIT unsupported fail-closed
- visibility와 license redaction
- row, byte, time, asset, subject budget
- continuation replay
- systemic outage와 subject gap 구분
- result와 lineage snapshot equality
- Arrow와 JSON round-trip

## 3. 전수성 gate

고정 숫자를 제품 경계로 쓰지 않지만 현재 baseline을 drift 탐지에 사용한다.

- DATA_RELEASES 42 전수 분류
- public 32와 private 10 가시성 보존
- 실존 axis 147 전수 분류, 실행 가능 146과 폐기 1 분리
- analysis 22 누락 0
- extraction concept 88 전수 분류
- L1, L1.5, L2 owner package 전수 상태 부여
- invented callable asset 0

새 asset과 owner는 증가를 허용한다. silent disappearance는 실패다.

## 4. 실데이터 matrix

| case | asset 종류 | 필수 판정 |
|---|---|---|
| KR 005930 | finance, panel, narrative, scan ratio, analysis | native와 factor, period, sourceRef |
| US AAPL | EDGAR finance, sections, price, quant | native, resource, cross-market identity |
| multi company | scan account와 ratio | bounded batch, continuation, entity coverage |
| macro | FRED와 ECOS, macro axis | frequency, unit, latest snapshot |
| disclosure event | DART와 EDGAR filing | eventAt, availableAt, document locator |
| graph | industry edge와 evidence | direction, predicate, source evidence |
| simulator | state observation과 replay | same query contract, vintage leak 0 |

## 5. 실행 명령

프로젝트 규칙에 따라 전체 pytest를 기본으로 돌리지 않는다.

```powershell
uv run python -X utf8 tests/run.py preflight
uv run python -X utf8 tests/audit/dartlabGuard.py strict --scope l0-l15 --providers dart,edgar
& 'C:\Program Files\Git\bin\bash.exe' tests/test-lock.sh tests/data/test_contracts.py -v
& 'C:\Program Files\Git\bin\bash.exe' tests/test-lock.sh tests/data/test_catalog.py -v
& 'C:\Program Files\Git\bin\bash.exe' tests/test-lock.sh tests/data/test_query.py -v
& 'C:\Program Files\Git\bin\bash.exe' tests/test-lock.sh tests/simulate/test_data_workbench_bridge.py -v
```

실데이터와 외부 설치 smoke는 별도 명령으로 실행하고 network 불가를 성공으로 간주하지 않는다.

## 6. fatal gate

다음 중 하나라도 참이면 공개 승격과 삭제를 중단한다.

1. data와 simulate 양방향 import
2. lower owner가 data import
3. historical query가 latest 값에 asOf label만 붙임
4. 실존 registry axis 또는 owner resource가 조용히 누락
5. catalog discovery 중 data fetch나 engine execution
6. private locator 또는 token 노출
7. factor에 source revision, timing, evidence가 없음
8. document와 graph의 scalar flatten 손실
9. no-arg 또는 wildcard가 eager 전수 물질화
10. provider 전체 장애가 partial success로 보임
11. ignored U5 사용자 source 손실
12. public API, docs, Skill OS, 6 JSON 산출물 drift

## 7. 진행 원장

### 2026-07-22 W0

- 아키텍처, API, 이관 세 관점 조사 완료
- 두 차례 API 상호 반박 완료
- 최종 API를 `catalog`, `query` 두 axis로 확정
- factor와 lineage를 독립 axis에서 제외
- Mirror의 fake asOf와 6엔진 범위 한계 확인
- Universe U0부터 U4의 선별 승격 범위와 U5 보호 경계 확정
- targeted Universe kernel test 3건 green

### 2026-07-22 W1부터 W5

- `src/dartlab/data/` 독립 엔진과 root `dartlab.data` 공개 표면 구현
- public axis를 `catalog`, `query` 두 개로 고정
- L1, L1.5, L2 owner-local `dataProduct.py` 자동 발견 구현
- registry axis 147개, resource 42개, extraction concept 88개, Company surface 64개 분류
- owner-declared callable asset `analysis.simulationInputs` 추가
- native, records, factor, graph, narrative, resource typed projection 구현
- validAt, knownAt 분리와 unsupported PIT owner 실행 전 차단
- row, byte, asset, subject, 실행 기한 전체 query 예산 적용
- private와 nested resource 차단, bulk locator 무적재, bulk payload 차단
- simulator 재무 입력을 동일 `data("query")` 계약으로 전환
- simulator 결과에 data snapshot, contract hash, lineage, receipt 노출
- JSON mapping 입력과 AI EngineCall 외부 호출 검증
- 구 `simulate.mirror` 드라이버 제거, 순수 kernel을 `data.factorKernel`로 이관
- `engines.data` Skill을 운영자 전용 문서에서 범용 Data Workbench 계약으로 교체
- Skill OS 6개 JSON 산출물 수동 동기화와 재검사 완료

### 2026-07-22 W6

- 외부 wheel 빌드와 격리 환경 의존성 설치 완료
- 설치된 wheel에서 catalog 353개 자산 자동 발견 확인
- 설치된 wheel에서 `data("query", "scan.fields")` bounded materialization 성공
- 설치된 wheel에서 `EngineCall(apiRef="data")` catalog 호출 성공
- data와 simulator 집중 회귀 57건 통과
- Skill OS artifact sync 5건과 graph 17건 통과
- L0부터 L1.5 strict guard 7개 규칙 통과
- top-level cycle 0건, Data Workbench purity 위반 0건
- 공개 API manifest와 coverage에 `dartlab.data` 반영 후 quick product smoke 4건 통과
- 새 data 엔진 addEngine round trip strict 통과
- 저장소 전체 preflight를 시도하고 작업대 관련 공개 API와 gather mirror 누락을 수정했다. 전체 runner는 mutation smoke 자식 프로세스를 남긴 채 상한을 초과해 관련 하위 gate를 개별 검증했다.

### 2026-07-22 W7

- Feast, Iceberg, OpenLineage, Arrow Flight, Polars, Weaviate, Great Expectations 공식 설계 조사
- Data Prism attempt에서 혼합 projection과 결정적 narrative evidence 3건 통과
- `DataRequest` asset별 projection override를 기존 `query` axis에 승격
- 한 호출에서 factor, narrative, graph, native, records, resource view 혼합 가능
- narrative에 documentId, chunkId, language, contentHash, 시간, source, evidence spine 적용
- factor latest-only knownAt 현재 시각 자동 주입 제거
- partition별 구조화 DataLineage와 QualityAssertion 결박
- `byRequest`, `toPolars`, `toArrow` 외부 소비 adapter 추가
- Python contract object 없는 JSON mapping 혼합 query 검증
- 기존 단일 asset query 호환 포함 data 집중 회귀 16건 통과
- 로컬 실측 import 1.1454초, cold catalog 1.1971초, warm catalog 18.1ms
- 2개 owner 혼합 factor와 narrative query median 19.338ms, p95 23.652ms, Arrow 변환 median 0.547ms
- 당시 격리 wheel 설치본에서 catalog 353개, queryable 171개, 혼합 factor와 narrative, Arrow 2개 table 검증
- data와 simulator 집중 회귀 43건, attempt와 Skill OS 회귀 25건 통과
- workbench purity 위반 0건, top-level cycle 0건
- L0부터 L1.5 strict guard 7개 규칙, public API coverage, quick product smoke 4건 통과
- 전체 preflight는 두 번 실행했으나 runner가 자식 mutation smoke를 남긴 채 각각 124초와 304초 상한을 초과했다. 잔존 프로세스는 PID tree를 확인해 종료하고 관련 하위 gate를 개별 검증했다.

### 2026-07-22 W8

- 항상 예외를 내는 폐기 축 `gather.calendar`를 catalog-only로 정정해 queryable 170개 확정
- `selectorKind`, `selectorRequired`를 descriptor에 추가하고 owner 이름 하드코딩 제거
- 필수 selector 누락을 owner 실행 전 `MISSING_SELECTOR`로 차단
- `None`, 빈 DataFrame, 빈 mapping과 sequence를 `NO_DATA` gap으로 판정
- `maxConcurrency`를 실제 실행 window에 적용하고 결과 순서를 요청 순서로 고정
- analysis, credit, quant의 Company 공유 상태를 `companyData` concurrency group으로 직렬화
- queryable 170개 전수 executor 해소와 한 번의 혼합 query 라우팅 통과
- engine asset 146개에 records, narrative, factor projection 438개 cell과 Arrow 438개 table 통과
- industry graph 9개 전체에서 node, edge 방향, evidence 보존 통과
- 실제 queryable 170개를 격리 프로세스에서 모두 실행
- 실제 non-empty 성공 163개, 이 중 30초 이내 146개와 30초 초과 180초 이내 17개
- `NO_DATA` 4개, owner 시간 계약 오류 1개, 180초 초과 2개를 성공으로 가장하지 않고 분리
- quant.entry와 quant.style을 막던 dipBuy Signal key 두 곳 수정 후 실제 재실행 성공
- L1 price, L2 credit와 macro, simulator input의 실제 4자산 혼합 query 4.278초, partition 4개, Arrow table 4개, quality assertion 16개 확인
- 앞 partition이 row budget을 독점하지 않도록 뒤 task마다 최소 1행과 byte 여유 예약
- 최종 격리 wheel 설치본에서 catalog 353개와 queryable 170개, factor 999행, narrative 1행, Arrow table 2개 확인

### 2026-07-23 W9

- catalog version set인 기존 `snapshotId`와 실제 반환값을 결박한 `dataSnapshotId`를 분리
- 모든 표준 partition에 schema와 값 기반 `contentHash` 및 `contentSealed` quality assertion 추가
- 실행 영수증을 query metadata만이 아니라 실제 반환 content hash에 결박
- 같은 query와 같은 값의 identity 안정성, 값 변경 시 content hash, receipt, data snapshot 동시 변경 검증
- resource Arrow payload의 검증된 inner IPC digest를 partition content identity로 승격
- simulator 입력이 catalog snapshot 대신 실제 content-sealed data snapshot을 소비하도록 전환
- EngineCall 20행, HTTP 200행 bounded JSON preview로 nested DataFrame과 Series 구조 보존
- 첫 `DataResult`의 `iterPages()`와 `iterAllArrowBatches()`가 opaque continuation을 자동 소비하도록 추가
- 한 Python 소비 흐름에서 DART 5개와 EDGAR 4개 synthetic shard를 중복과 누락 없이 완주
- resource owner의 description과 read가 single-use manifest session을 공유해 전수 manifest 순회를 page당 3회에서 2회로 축소
- strict mutable source의 pre-snapshot과 반환 전 post-validation, committed replay 무접촉 계약 유지

### 2026-07-23 W10

- feature registry, observation, vintage, revision-aware query 계약을 `dartlab.data` 공통 계층으로 이동
- 기존 simulator import 경로는 compatibility re-export로 유지해 외부 작업대와 simulator의 의미 규칙 통일
- 엄격한 달력 날짜, `MARKET:ID` entity, feature definition과 normalization 결박, duplicate와 normalization drift 차단
- valid time과 knowledge time, staleness, bounds, same-day date precision, missing matrix, 동일 timestamp revision ambiguity를 공통 PIT selector에서 검증
- `observationPIT` 선언 owner가 typed observation envelope 대신 일반 frame을 반환하면 실행 후 fail-closed
- `analysis.edgarFinancialFeatures` callable asset을 catalog에 추가해 전체 354개, queryable 171개, callable 2개로 확장
- 로컬 EDGAR companyfacts 전용 9열 reader와 operating-company reduced financial feature owner 구현
- 외부 JSON mapping 한 번 호출에서 AAPL revenue와 operating margin을 factor row로 반환하고 actual filing time, observation ID, revision ID, feature version, lineage를 보존
- query cutoff가 달라도 같은 evidence와 값이면 동일 observation과 revision identity를 유지
- retained companyfacts의 과거 admission snapshot 부재를 `latestRetained`, `periodOnly`, `conditional` gap으로 표면화
- W10 종료 시점의 전체 시장 원천 DART와 EDGAR continuation과 subject-only PIT feature 범위를 명시적으로 분리
- 공통 feature, actual owner, catalog, query, simulator 집중 회귀 93건 통과
- 작업대 핵심, simulator, architecture, Skill OS 연결 회귀 196건 통과
- continuation, restart, CAS, Arrow, page scan 회귀 207건 통과와 환경 의존 2건 skip
- resource paging과 별도 process resume 회귀 31건 통과
- L0부터 L15 strict guard 7개 규칙, workbench purity, 신규 공개 함수 docstring strict, camelCase, Ruff, targeted Pyright 통과
- W10 종료 시점에는 immutable materialization, historical universe, 전종목 계산 feature paging, offline receipt 재생이 미구현 상태였음

### 2026-07-23 W11

- `analysis.edgarFinancialFeatures`에 `UniverseSelection(markets=("US",), membership="listed")`를 지정하면 호출자 종목 반복 없이 한 `data("query", ...)`로 전체 현재 상장 universe 작업 등록
- 계산 owner용 continuation을 raw resource paging과 분리하되 같은 opaque token 저장소와 24시간 임시 보존 정책을 사용
- 한 page의 종목 시도를 최대 8개로 제한하고 row, byte, time, concurrency 예산을 함께 적용
- 종목별 실패를 `FEATURE_ENTITY_UNAVAILABLE` 등 구조화 gap으로 보존하면서 cursor를 전진시켜 한 실패가 뒤 종목을 막지 않도록 구현
- 원 query, contract, 외부 Arrow schema, `resource.edgar` source manifest, universe membership과 ticker, CIK mapping을 continuation에 digest로 고정
- 미완료 재개 시 source 또는 universe identity drift를 owner 호출 전에 차단하고, commit된 page는 source와 owner 접촉 없이 replay
- 명시한 `subjects`는 기존 eager `subjectFanout` 경로를 유지하고 universe source를 읽지 않도록 회귀 고정
- synthetic 10종목은 첫 page 8개와 다음 page 2개로 중복과 누락 없이 완주
- row budget 3에서는 3개, 3개, 3개, 1개 page로 완주하고 실패 cursor, replay, source drift, CIK drift, historical preflight를 포함한 owner paging 집중 회귀 10건 통과
- data 전체 회귀 365건 통과와 환경 의존 2건 skip 확인. 이후 추가된 owner paging 집중 회귀 10건도 별도 통과
- 실제 로컬 smoke에서 US 현재 상장 7,669개를 한 query에 등록하고 첫 page 8개 시도, 1개 성공, 7개 gap, 21.415초, continuation 발급 확인
- 실제 7,669개 전 page 완주는 아직 인증하지 않았으므로 즉시 전체 계산 완료나 영구 factor store 성능으로 과장하지 않음
- W11 종료 시점에는 historical `asOf`, pageable과 eager 혼합, `requireComplete`, DART 계산 feature, 일반 owner 전체 paging을 실행 전 차단 또는 범위 밖으로 유지
- W11 종료 시점에는 immutable generation과 offline receipt 재생이 아직 없었음

### 2026-07-23 W12

- `analysis.dartFinancialFeatures`를 KR 현재 상장 universe 계산 owner로 추가하고 catalog 355개, queryable 172개로 확장
- exact DART finance bytes, full-file digest, 종목 identity, 상장 membership, 회사별 결산월, knownAt을 한 owner query에 결박
- DART 2,661개 공식 전수 감사 실행 구간에서 2,352개 strict PIT factor 성공, 성공률 88.3878%, loader 0, network 0, 시작과 종료 source snapshot 동일 확인
- EDGAR 7,669개 strict full-state 전수 감사에서 632개 성공, 성공률 8.24097%, local source 접근 7,229개와 factor 성공률을 분리해 기록
- EDGAR revenue와 operating margin 요청을 stock state와 분리한 production flow-only 전수 감사에서 3,136개 성공, 성공률 40.8919%, strict 대비 2,504개와 32.6509%p 증가
- flow-only 전수 감사 223.016초, p50 82.996ms, p95 286.363ms, loader 0, network 0, 5,667개 unique source hash와 listing 불변
- 계산 owner, raw resource, 일반 eager asset을 한 outer continuation으로 섞는 composite scheduler 추가
- 일반 eager callable과 engine axis를 fresh child에서 실행하고 bounded content seal로 고정해 resume owner 재호출 0회
- source, query, contract, schema, owner code와 universe drift를 lower owner 실행 전에 검증
- 파일 크기 가드를 위해 composite, owner, execution, process 책임을 private 모듈과 얇은 호환 파사드로 분리
- 공식 DART 감사 전에 잘못 실행한 loader가 `data/dart/finance/006660.parquet`를 갱신한 사고는 `tests/_attempts/dataWorkbenchDartScale/README.md`에 이전과 현재 digest를 기록하고 추가 덮어쓰기 없이 보존
- eager 실현 가능성 probe가 macro와 news 파일을 자동 갱신한 사고는 `tests/_attempts/dataWorkbenchProcessDeadline/README.md`에 신규 8개와 갱신된 etag 4개를 기록하고 이후 fixture 실행으로 차단

### 2026-07-23 W13

- 기존 `query` axis에 `runtime`, `reuse`, `refresh`, `offline` materialization 정책 추가
- asset, source, query, universe, contract, schema exact pin 여섯 개로 immutable generation identity 구성
- BUILDING 비가시성, single builder epoch와 lease, ordered Arrow CAS page, terminal manifest, atomic READY publication 구현
- SQLite에는 digest, 상태, 수치, lease만 저장하고 query 원문, owner identity, token, Arrow payload 저장 금지
- structured receipt만 받은 fresh process가 catalog, owner, source 호출 0회로 page 0과 continuation page 1 재생
- materialization CAS page payload read는 public page당 정확히 1회
- page read 중 GC race, crash recovery, concurrent builder, corruption, private path, bounded GC를 포함한 19개 집중 회귀 통과
- cold build는 전체 6시간과 page별 timeout 상한, warm replay는 목표 page 하나 적재
