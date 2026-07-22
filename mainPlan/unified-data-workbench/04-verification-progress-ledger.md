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
- 실존 axis 147 전수 분류
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
4. 147축 또는 owner resource가 조용히 누락
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
- 저장소 전체 preflight 실행 완료. 작업대 관련 공개 API와 gather mirror 누락은 수정했다. 남은 실패는 기존 사용자 작업의 포맷 30개, 로컬 블로그 미디어 2개, 기존 provider 역방향 import 1개, 기존 노트북 공개 계약 2개와 Windows shell wheel 명령 호환 문제로 분리했다.
