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

### 2026-07-26 W14

- immutable generation의 warm page 재생을 전체 page ledger scan에서 ordinal 직접 조회로 변경해 page 수 증가에 따른 반복 scan 제거
- production materialization store를 root와 timeout 조합별로 재사용하고 immutable terminal manifest를 process당 제한된 16개 root까지 검증 cache
- CAS가 이미 수행한 SHA-256 검증을 replay와 publication 계층에서 중복 수행하지 않도록 정리
- reader lease 최종 검증과 release를 한 SQLite transaction으로 합쳐 page 재생의 ledger 연결을 5회에서 2회로 축소
- 8 page, page당 100행, 60회 warm replay 실측에서 p50 93.278ms에서 51.501ms로 44.8%, p95 116.479ms에서 57.471ms로 50.7% 단축
- fresh owner process fixture에서 종목 8개 대비 64개 batch의 p50 처리량이 초당 3.794개에서 18.276개로 4.82배 증가했고 최대 payload는 411,008 bytes로 8MiB 상한의 4.9%
- DART와 EDGAR 계산 owner page 상한을 8개에서 64개로 확대
- 실제 local-only 첫 page 단일 실측에서 KR은 8개 3.737초에서 64개 9.242초, US는 8개 3.910초에서 64개 5.644초
- 완료 종목 처리량은 KR 2.14개/초에서 6.92개/초로 3.24배, US 2.05개/초에서 11.34개/초로 5.53배 증가
- 64개 page도 30초 기본 예산의 31% 이하였으며 row, byte, time budget과 continuation이 더 작은 실제 경계를 계속 강제

### 2026-07-26 W15

- canonical 엔진 폴더와 공개 진입점을 `src/dartlab/dataHub/`, `dartlab.dataHub(...)`로 전환
- `dartlab.data`는 기존 소비자를 위한 callable compatibility alias로 유지
- capability key를 `dataHub.catalog`, `dataHub.query`로 승격하고 Skill OS 정본을 `engines.dataHub`로 이동
- `/api/dataHub/v1` versioned catalog, job, result, cancel, worker lease API 추가
- request와 result를 private SHA-256 CAS에 저장하고 SQLite에는 digest, 상태, 우선순위, 시도 수, lease epoch만 보존
- idempotency key, 원자 claim, heartbeat, lease 만료 재queue, bounded retry, stale completion 차단 구현
- client와 worker bearer token을 역할별로 분리하고 서로 대체할 수 없게 고정
- `DataHubClient`, `AsyncDataHubClient`에 local과 같은 catalog와 query 의미, submit, wait, cancel, result 계약 추가
- pull 기반 `DataHubWorker`와 `python -m dartlab.dataHub.workerPlane` 실행 진입점 추가
- remote wire에서 bounded Arrow materialization page, continuation, immutable receipt를 digest 검증 후 복원
- control plane, remote, public surface 집중 회귀 13건 통과
- 이동된 DataHub 전수 회귀는 504개를 분할 실행해 501개 통과와 환경 의존 3개 skip 확인

### 2026-07-26 W16

- DataHub 운영 결함 정정. control plane ledger 에 WAL 저널 활성화. 형제 ledger 두 곳은 이미 쓰고 있었고 이 저장소만 기본 delete 저널이라 reader 가 writer 를 전면 차단했다
- systemic gap 을 query status 실패로 승격. 헌장 D09 가 요구하는 단일 asset 결손과 provider 전체 장애의 구분이 실행 경로에 없었다
- materialization store 와 job ledger 의 bounded maintenance 를 공개 진입에 배선. 두 GC 는 정의만 있고 호출자가 테스트뿐이라 retention 이 한 번도 발동하지 않았고 READY generation 과 terminal job 이 무한 누적되는 상태였다
- maintenance 의 CAS 삭제 실패를 digest 단위로 이연. GC_PENDING 이 durable 마커라 다음 호출에서 재시도되며 파일 하나의 잠금이 같은 트랜잭션의 reader lease 정리와 generation 전이를 rollback 시키지 않는다
- page scan 에 같은 token 기반 bounded 재시도 추가. commit 된 page 는 원천 접촉 없이 replay 되고 실패한 page 는 commit 되지 않으므로 token 재사용이 중복과 누락을 만들지 않는다. 재시도 부재가 전종목 완주 미인증의 실제 원인이었다
- 기본 resume caller 가 참조하던 legacy alias 를 canonical 진입점으로 정정
- EDGAR 매출 태그를 `reference/data/accountMappings.json` 정본에 맞추고 업종 전용 총매출 태그를 후순위로 추가
- normalization rule hash 를 adapter 버전 상수가 아니라 실제 태그 선택 규칙 digest 에서 유도. 기존 상수는 태그 우선순위가 바뀌어도 값이 같아 옛 규칙으로 선택한 관측과 구운 generation 이 현행 계약처럼 통과할 수 있었다
- `OperatingIncomeLoss` 소계가 없는 filer 를 위해 같은 접수 안의 구성요소로 영업이익을 유도. 매출총이익에서 영업비용을 빼거나 매출에서 총비용을 뺀다
- derived quarter lineage 판정을 접수 집합 비교로 정정. 기존 tuple 동일성 비교는 한 접수 안에서 태그 두 개를 쓴 유도와 그 접수의 단일 관측을 다른 lineage 로 잘못 막았다
- 대차 필수 앵커를 자산총계, 부채총계, 연결자본 셋으로 좁히고 나머지 구성요소는 임퓨트 후 `imputedZeroComponents` 경고로 남긴다. `otherNetAssets` 잔차 플러그가 흡수하므로 항등식은 실제 앵커 값으로 그대로 닫힌다
- 지배주주 자본만 태깅된 경우 비지배지분을 더해 연결자본을 만든다. 사전 필터 집합 누락으로 최초 구현이 실행되지 않던 것도 함께 정정했다
- 한 접수의 단위나 값 충돌이 회사 전체를 죽이지 않게 하고, 어떤 후보도 성립하지 않으면 첫 충돌 원인을 그대로 올린다
- stock 후보 순회를 지연 generator 로 바꾸고 대차와 분기 흐름이 함께 성립하는 첫 후보를 선택. 기존에는 구성요소 완전성 요구가 흐름 가용성과 우연히 상관되어 올바른 후보로 떨어졌을 뿐이라 대차만 있는 최신 filing 이 흐름 있는 직전 filing 을 가리면 회사 전체가 실패했다
- 7,683 개 universe 읽기 전용 전수 감사 3 회. full-state strict 632 개에서 2,420 개, 31.4981%. flow-only 3,136 개에서 3,256 개, 42.3793%. revenue 단독 3,902 개에서 4,038 개, 52.5576%. 세 실행 모두 loader 0, network 0, 시작과 종료 source snapshot 동일
- `NO_COHERENT_STOCK_STATE` 는 4,689 개에서 632 개로 줄었다. 뒤 단계 실패 증가는 검증 약화가 아니라 stock 단계를 통과해 도달한 인구가 늘어난 결과이며 항등식 차단 363 건과 단위 충돌 차단 14 건은 그대로 작동한다
- 400 개 표본 진단에서 `OperatingIncomeLoss` 가 없는 73 개 중 유도 구성요소를 가진 것은 9 개뿐이고 61 개는 구성요소가 아예 없다. 남은 영업이익 갭의 대부분은 원천 태깅 부재다
- owner, resource, composite 의 `strictTree` 와 문자열, digest 검증 중복을 `pagingStateCodec` 으로 통합. `_jsonLoad` 와 `_validateQueryPayload` 는 lane 마다 canonical 검사 위치와 state 스키마가 달라 통합 대상에서 제외했다
- `tests/_attempts` 의 DataHub 감사 하네스 11 개가 W15 canonical rename 이후 import 오류로 전부 실행 불가였다. 27 개 참조를 정정해 실적 재현 경로를 복구했다. 다만 이 폴더는 VCS 추적 대상이 아니라 깨끗한 클론에서는 여전히 재현할 수 없다

### 2026-07-26 W16 후속: EDGAR 성공률 분모 정정

W16 최초 기록은 성공률을 티커 7,683 분모로만 적어 시장 커버리지처럼 읽히게 했다.
분모를 실측 분해해 다시 적는다.

- 449 개는 companyfacts parquet 자체가 없다. 80 개 표본을 SEC 원본에 직접 조회한
  결과 47.5% 가 404, 50.0% 가 태그 20 개 미만 껍데기, 2.5% 만 실데이터를 가진
  수집 갭이었다. 대부분 ADR 과 신규 등록 CIK 다.
- 1,456 개는 parquet 은 있으나 cutoff 이전 10-K 또는 10-Q 가 없다. ETF, 펀드,
  20-F 외국기업이라 모집단 밖이다.
- 둘을 뺀 사업회사 5,778 개 기준으로 revenue 단독 69.9%, flow-only 56.4%,
  full-state 41.9% 다.

책임 소재도 갈랐다. 455 개 표본 교차 집계에서 단독분기 매출 행 4 개 이상을 가진
323 개 중 316 개가 성공해 97.8% 다. 재료가 있으면 컴파일러는 실패하지 않는다.
실패는 분기 흐름을 YTD 와 연간으로만 태깅하는 filer 관행이 지배한다.

수집 파이프라인 상태도 확인했다. `edgarSync.yml` 은 매일 UTC 04:30 cron 으로 살아
있고 최근 6 회 중 5 회 성공했다. HuggingFace 배포본과 로컬 스냅샷은 표본 대조에서
행 수, 태그 수, 최신 filed 가 모두 같았다. 로컬 파일 mtime 은 파일을 쓴 시각이지
데이터 시점이 아니다.

기록으로 남길 판단 오류가 하나 있다. 감사 하네스는 재현성을 위해 loader 와 network
호출을 0 으로 막고 로컬만 읽는다. 그 조건에서 나온 `SOURCE_FILE_MISSING` 을 검증
없이 원천 한계로 해석했다. 결론 자체는 실측으로 맞았지만 근거 없이 단정한 절차가
틀렸다. 측정 조건은 결론으로 확대하지 않는다.
