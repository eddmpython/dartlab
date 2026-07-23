# 06. 전수 인증과 Hardening 결과

## 1. 판정

Data Workbench 공통 계층은 signature-grade로 판정한다. 이유는 일부 대표 예제가 아니라 현재 queryable catalog 전체를 라우팅하고, 모든 engine asset에 공통 projection을 적용하고, 실제 owner 실행까지 전수 수행했기 때문이다.

다만 `queryable`은 executor와 정책이 있어 query를 시도할 수 있다는 뜻이다. 모든 외부 원천이 항상 non-empty이고 모든 owner 계산이 기본 30초 안에 끝난다는 뜻은 아니다. 이 차이를 gap과 시간 등급으로 보존한다.

## 2. 최종 catalog

| 항목 | 실측 |
|---|---:|
| 전체 asset | 354 |
| queryable | 171 |
| catalog-only | 183 |
| engineAxis | 146 |
| callable | 2 |
| resource locator | 23 |
| L1 queryable | 39 |
| L1.5 queryable | 28 |
| L2 queryable | 104 |

`gather.calendar`는 registry에 남아 있지만 호출하면 항상 폐기 예외를 내므로 `queryable=False`와 `executorKind=catalog`로 바로잡았다. catalog에서 삭제하지 않아 폐기 이유와 drift는 계속 추적된다.

## 3. 전수 계약 인증

아래 표는 W8 당시 queryable 170개 baseline이다. W10의 171번째 callable asset은 공통 feature 집중 회귀와 실제 AAPL smoke로 별도 인증했으며 §8에 기록한다.

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
- raw DART와 EDGAR resource는 opaque continuation을 지원한다. 전종목 계산 feature paging과 네트워크 Arrow Flight server는 아직 확장 범위다.

따라서 현재 제품은 단일 프로세스와 외부 Python 소비에 강력한 범용 데이터 작업대다. 분산 서버에서 hard cancellation, streaming, owner pushdown까지 갖춘 최종 물리 플랫폼이라고 부르지는 않는다.

## 8. 2026-07-23 revision-aware feature 확장

data 공통 계층에 feature registry, observation, vintage, revision-aware query 계약을 추가했다. `analysis.edgarFinancialFeatures`는 subject와 knownAt을 받는 두 번째 callable asset이며 로컬 EDGAR companyfacts에서 operating-company reduced financial feature를 만든다. catalog는 354개, queryable은 171개가 됐다.

AAPL 실제 로컬 smoke에서 revenue와 operating margin 두 feature를 한 공개 query로 반환했다. 관측의 `knownAt`은 query cutoff가 아니라 실제 최대 filing date였고, 인접 cutoff는 같은 evidence에 대해 동일 observation ID와 revision ID를 유지했다. 현재 보존 이력의 한계는 `latestRetained`, `periodOnly`, `conditional`로 표시했다.

이 확장은 전종목 raw resource continuation을 전종목 factor store로 바꾸지 않는다. 현재 feature callable은 `subjectFanout`이다. 영구 materialization, historical universe, 전종목 계산 feature paging, offline과 online serving은 runtime SSOT로 불가능하다는 실측, 별도 atomic generation 설계 토론, 명시적 아키텍처 승인 뒤에만 코드와 실행을 진행한다.
