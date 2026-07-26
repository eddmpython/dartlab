# 06. 전수 인증과 Hardening 결과

## 1. 판정

Data Workbench 공통 실행과 projection 계층은 signature-grade로 판정한다. 근거는 W8 당시 queryable 170개 전수 라우팅과 모든 engine asset의 공통 projection, 실제 owner 격리 실행이다. 이후 추가된 callable은 각 확장 절의 집중 회귀와 실데이터 감사로 별도 검증했다.

다만 `queryable`은 executor와 정책이 있어 query를 시도할 수 있다는 뜻이다. 모든 외부 원천이 항상 non-empty이고 모든 owner 계산이 기본 30초 안에 끝난다는 뜻은 아니다. 이 차이를 gap과 시간 등급으로 보존한다.

## 2. 현재 catalog

| 항목 | 실측 |
|---|---:|
| 전체 asset | 355 |
| queryable | 172 |
| catalog-only | 183 |
| engineAxis | 146 |
| callable | 3 |
| resource locator | 23 |
| L1 queryable | 39 |
| L1.5 queryable | 28 |
| L2 queryable | 105 |

`gather.calendar`는 registry에 남아 있지만 호출하면 항상 폐기 예외를 내므로 `queryable=False`와 `executorKind=catalog`로 바로잡았다. catalog에서 삭제하지 않아 폐기 이유와 drift는 계속 추적된다.

## 3. 전수 계약 인증

아래 표는 W8 당시 queryable 170개 baseline이며, 위 현재 catalog 172개와 분모가 다르다. W10의 171번째 callable asset은 공통 feature 집중 회귀와 실제 AAPL smoke로 별도 인증해 §8에 기록했고, 이후 확장은 각 절에 따로 기록한다.

| gate | 범위 | 결과 |
|---|---:|---:|
| executor 해소 | queryable 170 | 170 통과 |
| 한 번의 혼합 query 라우팅 | queryable 170 | 170 partition 통과 |
| records projection | engine 146 | 146 통과 |
| narrative projection | engine 146 | 146 통과 |
| factor projection | engine 146 | 146 통과 |
| Arrow 변환 | projection 438 | 438 통과 |
| graph 방향과 evidence | industry graph 9 | 9 통과 |
| resource locator 무적재 | resource 23 | 23 통과 |

이 행렬은 synthetic owner output으로 Data Workbench의 공통 실행, projection, transport 배관을 전수 검증한다. owner 계산 자체의 정확성은 다음 실제 실행 gate에서 별도로 본다.

## 4. 실제 170개 실행

모든 queryable asset을 별도 Python 프로세스에서 실행했다. 한 프로세스가 멈춰도 다음 자산을 막지 않도록 격리했고, 결과는 최대 5행과 1MB로 제한했다. 잘못된 target은 registry의 targetType과 실제 예시에 맞춰 다시 실행했다.

| 최종 상태 | 자산 수 | 의미 |
|---|---:|---|
| interactive success | 146 | 30초 이내 non-empty 결과 |
| batch success | 17 | 30초 초과, 180초 이내 non-empty 결과 |
| `NO_DATA` | 4 | owner가 현재 probe에서 빈 결과 반환 |
| owner contract failure | 1 | owner 내부 시간 계약 위반 |
| 180초 초과 | 2 | 격리 상한 안에 완료되지 않음 |

실제 non-empty 성공은 163개다. batch 성공 17개에는 가치와 factor 계산, 대형 scan, narrative, 원문 문서처럼 원천 또는 전종목 계산 비용이 큰 축이 포함된다.

### 성공으로 가장하지 않은 7개

| asset | 최종 판정 | 근거 |
|---|---|---|
| `analysis.종합평가` | owner contract failure | Lens Product의 `latestPeriod=2026`이 2026-07-22 knowledge boundary 뒤로 해석됨 |
| `gather.peers` | `NO_DATA` | 005930 probe에서 빈 결과 |
| `gather.research` | `NO_DATA` | 전체 조회 probe에서도 빈 결과 |
| `gather.sector` | `NO_DATA` | 005930 probe에서 빈 결과 |
| `scan.macroBeta` | `NO_DATA` | 005930 제한 probe에서 빈 DataFrame |
| `quant.sentiment` | batch timeout | 180초 격리 상한 초과 |
| `scan.network` | batch timeout | 180초 격리 상한 초과 |

이 7개는 Data Workbench가 오류를 만든 사례가 아니다. 작업대는 assetId와 requestId가 있는 gap으로 owner 상태를 보존한다. owner가 정상화되면 public data 계약 변경 없이 다시 성공할 수 있다.

## 5. Hardening에서 고친 결함

### Descriptor 기반 selector

기존 실행기는 analysis, credit, quant 같은 owner 이름으로 subject 처리를 분기했다. 이 때문에 optional macro target이 유실될 수 있었다. 지금은 `selectorKind`와 `selectorRequired`만 사용한다. 필수 입력이 없으면 owner 호출 전 `MISSING_SELECTOR`다.

### 빈 성공 제거

기존 native projection은 `None`을 1행 성공, 빈 DataFrame을 0행 성공으로 만들 수 있었다. resource locator처럼 payload가 의도적으로 없는 projection만 예외로 두고 나머지는 `NO_DATA`로 실패 또는 partial 처리한다.

### 안전한 동시 실행

`maxConcurrency`는 이전에 선언만 있고 사용되지 않았다. 지금은 독립 task를 작은 thread window로 병렬 실행하고 결과는 요청 순서로 조립한다. 실제 병렬화 중 Company 초기화 경쟁 상태를 발견했기 때문에 analysis, credit, quant는 `companyData` group으로 서로 직렬화한다. 같은 asset의 중복 request도 동시에 실행하지 않는다.

혼합 query의 첫 factor table이 전체 row budget을 독점하는 문제도 실제 격리 wheel에서 발견했다. 실행기는 뒤 task마다 최소 1행과 작은 byte 여유를 예약한다. 1,000행 예산에서 factor 999행과 narrative 1행이 함께 성공했고 요청 순서도 유지됐다.

### 실제 owner 결함 발견

quant.entry와 quant.style은 `dipBuy`가 등록하지 않은 camelCase Signal key를 참조해 실패했다. `rsi_low`, `rsi_high` 실제 key로 수정하고 단위 회귀와 실제 두 asset 재실행을 통과했다.

## 6. 실제 혼합 query

다음 네 자산을 한 query에서 실행했다.

- L1 `gather.price`
- L2 `credit.grade`
- L2 `macro.cycle`
- L2 `analysis.simulationInputs`

결과는 4.278초, status `ok`, partition 4개, gap 0개, Arrow table 4개, quality assertion 16개였다. Company 공유 상태 group을 적용하기 전에는 동일 query에서 credit 초기화 경쟁이 재현됐고, 적용 후 사라졌다.

새 임시 가상환경에 최종 wheel을 설치한 외부 smoke에서도 source checkout이 아닌 `site-packages` 경로를 확인했다. 설치본은 catalog 353개와 queryable 170개를 발견하고, factor 999행과 narrative 1행을 같은 query에서 반환했으며 Arrow table 2개를 만들었다.

## 7. 남은 물리 한계

- runtime `timeoutMs`는 owner Python 호출을 강제 종료하지 못하는 협력적 제한이다. 전수 인증 runner는 프로세스 격리로 이 한계를 보완했다.
- row와 byte budget은 owner 결과를 받은 뒤 projection에서 적용된다. owner별 predicate, projection, slice pushdown은 별도 최적화가 필요하다.
- `analysis.edgarFinancialFeatures`가 실제 filing cutoff를 쓰는 knownAt feature를 제공하지만, retained companyfacts가 historical admission snapshot 전체를 보존하지 않아 exact가 아니라 conditional이다.
- raw DART와 EDGAR resource 및 두 시장의 계산 feature는 opaque continuation을 지원한다. pageable, eager 혼합 query는 outer continuation 하나를 사용한다. versioned HTTP API와 원격 분산 worker는 지원하며, Arrow Flight 전용 server와 control plane multi-primary storage는 확장 범위다.
- cold materialization은 현재 요청 process에서 terminal generation을 동기적으로 구축한다. 별도 scheduler와 distributed worker는 없다.
- fresh child의 write guard는 Python과 알려진 데이터 writer를 차단하지만 임의 native syscall을 막는 적대적 OS sandbox는 아니다. 설치된 trusted owner 실행 격리로 사용한다.
- receipt 재생은 같은 `DARTLAB_HOME` 또는 같은 private storage를 보는 process 범위다. 원격 인증과 권한 분리는 별도 service plane이 필요하다.

따라서 현재 제품은 단일 프로세스와 외부 Python 소비에 강력한 범용 데이터 작업대다. 분산 서버에서 hard cancellation, streaming, owner pushdown까지 갖춘 최종 물리 플랫폼이라고 부르지는 않는다.

## 8. 2026-07-23 W10 revision-aware feature 확장

data 공통 계층에 feature registry, observation, vintage, revision-aware query 계약을 추가했다. `analysis.edgarFinancialFeatures`는 subject와 knownAt을 받는 두 번째 callable asset이며 로컬 EDGAR companyfacts에서 operating-company reduced financial feature를 만든다. catalog는 354개, queryable은 171개가 됐다.

AAPL 실제 로컬 smoke에서 revenue와 operating margin 두 feature를 한 공개 query로 반환했다. 관측의 `knownAt`은 query cutoff가 아니라 실제 최대 filing date였고, 인접 cutoff는 같은 evidence에 대해 동일 observation ID와 revision ID를 유지했다. 현재 보존 이력의 한계는 `latestRetained`, `periodOnly`, `conditional`로 표시했다.

W10 종료 시점의 이 확장은 전종목 raw resource continuation을 전종목 factor store로 바꾸지 않았다. feature callable은 명시한 subject를 처리하는 `subjectFanout`이었고, immutable generation과 전종목 계산 paging은 당시 미구현이었다.

## 9. 2026-07-23 W11 EDGAR 현재 상장 universe 확장

W11은 W10의 명시 subject 경로를 없애지 않고, 같은 `analysis.edgarFinancialFeatures`에 US 현재 `listed` universe를 지정한 경우만 계산 owner continuation으로 확장했다. 외부 프로세스와 simulator를 포함한 소비자는 종목별 함수를 반복하지 않고 한 `data("query", ...)`로 universe와 feature 계산을 등록하고 `iterPages()`로 같은 결과 계약을 소비할 수 있다.

한 page는 종목 시도 8개를 넘지 않는다. row, byte, time 예산이 먼저 소진되면 더 작은 page를 반환한다. 종목 계산 실패는 gap과 누적 universe coverage에 남기고 cursor는 다음 종목으로 진행한다. continuation은 원 query, contract, 외부 Arrow schema, `resource.edgar` source manifest, universe membership과 ticker, CIK mapping을 고정한다. 미완료 token에서 source나 universe가 바뀌면 owner 실행 전에 실패하고, commit된 page replay는 source와 owner를 다시 접촉하지 않는다. token은 private control plane에서 24시간 임시 보존된다.

synthetic 10종목은 8개와 2개 두 page로 전부 완료했다. row budget 3 회귀에서는 3개, 3개, 3개, 1개로 중복과 누락 없이 완료했다. source drift, CIK drift, 실패 cursor, commit replay, 명시 subject eager 유지, historical universe preflight를 포함한 owner paging 집중 회귀 10건이 통과했다. data 전체 회귀 기준은 365건 통과와 환경 의존 2건 skip이며, 이후 추가된 owner 집중 회귀도 통과했다.

실제 로컬 smoke는 US 현재 상장 7,669개를 한 query에 등록했다. 첫 page는 8개를 시도해 1개 성공, 7개 gap, 21.415초였고 다음 continuation을 발급했다. 이 실측은 실제 universe 해소와 첫 page 계산을 증명하지만, 7,669개 전 page의 실제 완주 시간이나 성공률을 인증하지 않는다.

따라서 W11은 외부에서 factor projection으로 재사용할 수 있는 runtime 작업대 경로였지만 당시에는 영구 generation이 아니었다. 이후 단계에서 DART 계산 feature, mixed outer chain, immutable generation과 offline receipt 재생으로 확장했다.

## 10. 2026-07-23 W12 DART, mixed outer chain, process isolation

`analysis.dartFinancialFeatures`를 KR 현재 상장 universe 계산 owner로 추가했다. DART finance exact parquet bytes, source digest, 종목 identity, 회사별 결산월을 owner 호출에 함께 결박한다. 실제 2,661개 공식 전수 감사 실행 구간에서 2,352개가 strict PIT factor를 만들었고 성공률은 88.3878%였다. 이 구간의 loader와 network 호출은 0회였고 시작과 종료 source snapshot이 같았다. 309개 실패도 source missing, schema missing, 4분기 window, currency, balance identity gap으로 보존했다.

공식 감사 준비 전에 잘못 실행한 loader가 `data/dart/finance/006660.parquet`를 한 번 갱신한 사고는 `tests/_attempts/dataWorkbenchDartScale/README.md`에 이전과 현재 digest를 기록했다. eager probe가 macro와 news 파일을 자동 갱신한 별도 사고는 `tests/_attempts/dataWorkbenchProcessDeadline/README.md`에 영향 파일을 기록했다. 두 사고를 숨기거나 공식 실행 구간의 source 불변 판정으로 덮지 않는다.

EDGAR full-state strict 전수 감사는 7,669개 중 632개, 8.24097% 성공이었다. revenue와 operating margin만 요청할 때 요청하지 않은 stock state를 제거한 production flow-only compiler는 3,136개, 40.8919% 성공했다. 2,504개와 32.6509%p 증가했지만 PIT cutoff, 4분기 연속성, 동일 accession lineage, revision 충돌 검증은 유지했다. 전수 실행은 223.016초, p50 82.996ms, p95 286.363ms였고 loader와 network는 0회, listing과 5,667개 unique source hash 변화도 0개였다.

DART와 EDGAR 계산 owner는 한 query에서 함께 등록할 수 있다. raw resource, 계산 owner, eager asset이 섞이면 lower token을 외부에 노출하지 않고 outer continuation 하나로 순회한다. 일반 eager callable과 engine axis는 fresh process에서 한 번 실행해 bounded content seal을 만들고 resume은 owner를 다시 호출하지 않는다.

process supervisor는 public deadline에서 cleanup reserve를 먼저 떼고 spawn, IPC drain, terminate, kill, Job Object close, join, zero-live 확인을 끝낸다. Python socket, subprocess, filesystem writer와 Polars, PyArrow, Pandas, NumPy의 알려진 native writer를 fail-closed한다. 이 경계는 trusted installed owner의 side effect 격리이며 임의 C extension syscall에 대한 보안 sandbox는 아니다.

## 11. 2026-07-23 W13 immutable generation과 receipt

기존 query에 `runtime`, `reuse`, `refresh`, `offline` 정책을 추가했다. asset, source, query, universe, contract, schema의 exact digest 여섯 개가 generation key를 결정한다. SQLite ledger는 digest, 상태, 수치, lease만 저장하고 Arrow page와 terminal manifest는 private CAS에 둔다.

한 builder epoch만 BUILDING page를 추가하고 terminal manifest와 READY 전환을 publication point로 사용한다. reader는 한 lease에서 manifest와 목표 page를 함께 검증한다. page payload는 public page당 한 번만 읽는다. live reader가 있는 generation은 GC가 전환하지 못하고 모든 maintenance 단계는 호출당 상한을 가진다.

fresh spawned process가 structured receipt만 받아 page 0과 continuation page 1을 재생하는 회귀에서 catalog, owner, source 호출은 각각 0회였고 materialization page payload read는 page당 1회였다. page read 도중 GC를 강제한 race에서도 READY generation 전이는 0이었다. materialization 집중 회귀 19건이 통과했다.

이 구현으로 factor store는 별도 제품이나 public axis가 아니라 Data Workbench의 FactorProjection과 immutable generation 조합이 됐다. 같은 저장 계약은 native, narrative, graph, records, resource projection에도 적용된다.

## 12. 2026-07-26 universe snapshot 불변 경계

데이터 집중 회귀 489개를 한 번에 수집하는 과정에서 `testActualKrUsOwnerPlansFitOneOuterState`가 `loadEdgarTargetUniverse()`를 통해 만료된 미국 상장 universe를 자동 갱신했다. 테스트는 7,669개라는 과거 고정 개수도 함께 가정해, 갱신 후 실제 7,683개와 충돌했다. 이 실행이 `data/edgar/listedUniverse.parquet`를 갱신했다는 사실을 숨기지 않는다.

수정 후 Data Workbench의 US universe resolver는 `localOnly=True`로 기존 owner snapshot만 읽는다. 캐시가 없으면 query가 원천을 임의로 만들지 않고 구조화 gap으로 실패한다. 원천 갱신 책임은 gather와 pipeline에 남는다. 규모 회귀는 고정 종목 수가 아니라 US 5,000개 이상, KR 2,000개 이상과 outer state byte budget을 검증한다. updater를 예외로 바꾼 테스트에서도 실제 plan이 통과하므로 query 계획 중 network와 파일 갱신이 0임을 기계적으로 보장한다.

같은 실행에서 중복 테스트 모듈명도 발견했다. `tests/data/test_contracts.py`와 continuation 하위의 동명 파일 때문에 `tests/data` 전체 수집이 불가능했고, data와 resourceStream을 함께 수집할 때 provider 하위의 동명 파일도 충돌했다. 두 계약 테스트를 고유 이름으로 옮겨 통합 수집 사각지대를 제거했다. 최종 집중 검증은 data, local-only core, DART와 EDGAR provider, resourceStream, 외부 HTTP master API, simulator 계약을 합쳐 637개를 수집해 634개 통과와 환경 의존 3개 skip이다. Guard quick은 architecture와 provider 규칙을 모두 통과했고 workbench purity는 계층 역전과 원천 직독 0건을 확인했다.

별도 장시간 격리 감사 21개도 통과했다. owner child 50회 연속 실행에서 성공 50회, zero-live 50회, artifact residue 0개였고 준비 시간은 p50 1.568초, p95 4.539초, 최대 7.989초였다. eager와 owner 혼합 초기 실행 20회도 매회 artifact residue 0개였다.

## 13. 2026-07-26 W14 속도와 효율

warm materialization replay는 ordinal page 하나만 SQLite에서 직접 읽고, immutable terminal manifest는 검증 후 process 안의 16개 root 제한 cache에서 재사용한다. store 초기화도 같은 root와 timeout 조합에서 재사용한다. CAS가 이미 digest를 검증한 payload를 상위 계층에서 다시 SHA-256 계산하지 않고, reader lease의 마지막 검증과 release는 한 transaction으로 끝낸다.

8 page와 page당 100행을 둔 60회 재생 실측에서 SQLite 연결은 호출당 5회에서 2회로 줄었다. p50은 93.278ms에서 51.501ms로 44.8%, p95는 116.479ms에서 57.471ms로 50.7% 단축됐다. terminal manifest는 같은 process의 60회 요청에서 한 번만 읽었다. cache는 최대 16개 manifest로 제한해 속도를 위해 메모리를 무제한 점유하지 않는다.

계산 owner의 page 상한은 8개에서 64개로 높였다. fresh process fixture p50 처리량은 8개 batch의 초당 3.794개에서 64개 batch의 초당 18.276개로 4.82배 증가했고, 64개 payload는 최대 411,008 bytes로 8MiB 상한의 약 4.9%였다.

실제 local-only 첫 page 단일 실측에서 KR은 8개 3.737초에서 64개 9.242초, US는 8개 3.910초에서 64개 5.644초였다. 완료 종목 기준 처리량은 각각 3.24배와 5.53배 증가했다. 두 시장 모두 64개 page가 30초 기본 예산의 31% 이하였고 row, byte, time budget이 먼저 닿으면 더 작은 page를 반환하는 fail-closed 경계는 유지한다. 이 수치는 첫 page 실측이며 전시장 전체 완주 시간 보증으로 확대하지 않는다.
