# 12. 빌드 플랜 — 판독·레버·프로파일러·연쇄 실행 정본 (06+10+11 승계)

상태: v1.0 (2026-07-05 전체 PRD 검토 산출물. 삭제된 `weekly-uplift-shortlist/02-build.md` 의 후신)
번호 규약: 본 플랜의 단계는 **R0~R6** (09 부채 원장의 P7/P9/P12, 07 로드맵 Phase 와 구분).
설계 근거는 06(판독·sweep·§5c 일단위·§7b 시그니처 스택)·10(레버 원장)·11(프로파일러·연쇄)이 정본이고
본 문서는 파일·순서·게이트·런북만 담는다 (설계 중복 금지).

## 0. 불변 원칙 (전 단계 공통)

- 신규 능력은 `tests/_attempts/shortlist/` 에서 개념확립 후 본진 (졸업게이트 8단계, CLAUDE.md).
- 메모리: Company 객체 루프 금지 (table.py 무bake·벌크 parquet 직독). 병렬 dartlab import ≤ 2.
- 신규 src 모듈 push 전: `dartlabGuard --scope l0-l15` 미러 + `publicApiCoverage`/`productSmoke
  --suite quick` (신규 verb 는 `publicApiScenarios.yml` 등록) 선제 실행.
- 지표·채점 코드는 버전 해시로 봉인, 봉인 이력 소급 재채점 금지 (06 §7b).
- UI 단계(R6)는 commit 까지 자율·push 는 운영자 눈검수 승인 후 (CLAUDE.md).

## 1. 모듈 지도 (전부 `src/dartlab/simulate/` 내부, 신설 엔진 0)

| 파일 | 공개 계약 | 의존 (하향만) | 단계 |
|---|---|---|---|
| reading.py | Reading dataclass + 임계 상수 SSOT (06 §2) | core | R1 |
| surfaces.py | `enumerateSurfaces()` 자동 열거 + 방향화 선언 테이블. **정규화: 래퍼 보고서(주요사항보고서 등) 괄호 내 하위타입 추출 필수** (11 실측 함정) | core.extractionCatalog·scan/quant guide·allFilings 타입 | R1 |
| table.py | `setTable(week, market)` 전종목 x 전표면 입력 행렬. 벌크 parquet 직독 (gov/prices·allFilings·HF panel). **fundDaily 일별 재무 그리드 포함 (§5)** | gather bulk·frame·scan | R1 |
| profile.py | `profile(code, asOf)` PIT 버전드 형질 dict + 관계 엣지 (11 §2 전수) | frame.inventory·extractionCatalog·allFilings 이력·quant | R1 골격 → R4 전수 |
| opine.py | 표면별 판독 산출 (방향화 선언 적용 + 기권 1급) | reading·surfaces·table | R1 |
| readingScorecard.py | 버킷 중립 채점 + FM 주단위 t + FDR/SPA 깔때기 + 형질 버킷 축 + gross/floor/net | reading + numpy 자급 부트스트랩 | R1~R2 |
| sweep.py | 격자 벡터화 + 강건성 선정 + **PBO·열화기울기·P(OOS손실)·중앙값 4종 자동 보고** + DSR | numpy (pboCscv 승격) | R2 |
| combine.py | AdaHedge 표면 결합 (후회 곡선 산출, 조정 나사 0) | numpy | R2 |
| board.py | board100/top10 파생 뷰 + red-flag 게이트 + net-of-cost 게이트 + never-claim 문구 | opine·sweep·profile | R2 |
| cascade.py | 4·5층 배선 (산업 착지·관계 전파) + **DAG-as-data JSON** (11 §4) | profile·opine·macro/industry verb | R5 |
| runweek.py | 주간 오케스트레이션 + 해시체인 블록 발행 | 전부 | R3 |
| expectationCycle 확장 | `issueReadings`/`scoreReadingsDue` (issueMacro 동형, 유일 writer) | expectationLedger | R1 |
| entry 확장 | `dartlab.simulate` 계열 verb 노출 (readings/board/profile) | 전부 | R2 |

테스트 미러 = `tests/simulate/` (structureMirror 룰7). 가드 2종 상주: replay 항등성 + look-ahead
카나리아 (06 §5c) 는 `tests/simulate/test_pitGuards.py` 로 기계화.

## 2. R0 — 실측 잔여 (본진 착수 전, _attempts 에서)

완료 기준 = 수치가 05 원장에 기록되고 방향 결정이 닫힘.

1. surfaces 정규화 v2 (래퍼 하위타입 추출)로 **이벤트 표면 전 타입 재실측** (기존 실측치는 하위
   타입 뭉갬 상태였음. 894→5,135 급 표본 변화 예상)
2. 이벤트 표면 편입 재실측: 강화 게이트 n≥100 & |med|≥1% + **사이즈 버킷 중립 타깃** + FM 주단위 t
3. 내부자 매수 정제 실측 (취득/처분 x 비정기 x 규모. 2~3배 가설 검증. 공시 본문 파싱 필요 시
   frame 재사용)
4. fundDaily 선결 실측 2건: ① HF panel parquet 전종목 벌크 스캔 비용 (Company 객체 없이 파일
   직독) ② panel 분기값 ↔ allFilings 실적공시 rcept_dt 매핑 커버리지 (G3. 정정공시 vintage 처리
   포함)
5. panel PIT 함정 실측 (정정 look-ahead) + fund 표면 v0 (SRW SUE + EAR)
6. 표면 상관 행렬 → 수축 클러스터 (readingScorecard 입력)
7. SPA 인증 1회전 (322+ 타입 전수, numpy 정상성 부트스트랩) · AdaHedge·ACI 프로토타입 (후회
   곡선·커버리지 곡선 실물)

## 3. R1 — 본진 골격 (졸업게이트 통과분만 이동)

- §1 표의 R1 행. 각 파일 9섹션 docstring + 단위 테스트 동반.
- issueReadings 첫 라이브 발행 = **bootstrap 아님** (issuedLive=True 는 실제 주간 사이클만).
- 완료 기준: `dartlab.simulate` 로 1주 전 시장 판독 발행 → 5거래일 후 자동 채점이 로컬에서 end-to-end.

## 4. R2 — sweep·결합·파생 뷰 / R3 — 라이브 런북

- R2 완료 기준: 주간 블록에 4종 sweep 통계·후회 곡선·board100/top10 이 포함되고 전부 원장
  순수함수 (외부인 재계산 가능).
- R3 런북 (주간, 자동화는 CI cron 승인 후): 금요일 마감 후 `runweek` → 봉인 블록 발행 (해시체인
  + OpenTimestamps 앵커) → 익주 금요일 채점 블록. 실패 시: 그 주 블록 결번 금지, "미발행" 블록
  명시 발행 (빈 주도 증거, 06 §7b). KR/US 는 시장별 블록.

## 5. 재무 일별환산 구현 스펙 (fundDaily. 06 §5c 의 코드 계약)

**개념 재확정 (재검토 결론)**: 일별화 = 보간이 아니라 3층 분리다. ① 피처 = PIT 계단 + 이벤트
타임 (유일한 모델 입력) ② nowcast = 시뮬 등재 (`simulated:nowcast`, 공시 도착 시 skill curve
채점) ③ 매끈한 분해 곡선 = 표시 전용. 그리고 "분기 데이터인데 일별 신호"의 실체는 **계단 분자
x 매일 움직이는 분모** (E/P·B/M·재무x가격 괴리는 가격이 움직여서 매일 갱신된다).

```
fundDaily(market, asOf) -> 일별 그리드 (code x date x 재무 피처):
  1. 분기 이벤트 테이블: panel 분기값 + 실적공시 rcept_dt (R0-4 매핑. 잠정실적 공시가 선행하면
     그 값·그 날짜가 이벤트, 정기보고서는 확정 이벤트로 별도 행 = 이중 이벤트 둘 다 보존)
  2. effective_date = rcept_dt (장후 접수는 익영업일). 정정공시 = 새 vintage 행 append
     (최초 보고값 불변. replay 는 해당 시점 vintage 만 조회)
  3. 일별 격자에 join_asof(backward) + stalenessAge(경과 거래일) 동반
  4. TTM = 이벤트마다 재계산 (KR Q4 = 연간 - 3Q 누적, 유도 시점 = 사업보고서 rcept_dt)
  5. 파생 일별 피처: E/P·B/M·S/P·accruals (계단 분자 / 당일 종가·시총) + SRW SUE + τ + peer
     기공시 SUE (같은 업종 ragged edge)
  6. 가드: look-ahead 카나리아 (rcept_dt 이전 값 존재 = fail) + replay 항등성
```

nowcast(v1+)·Chow-Lin 표시 곡선은 R5 이후 (§5b 4계약 등재 경유). MiniFinChart 의 연장·simulated
구간 표시는 R6.

## 6. R4 — 프로파일러 전수 / R5 — 연쇄·DAG

- R4: profile.py 를 형질 8축 전수로 확장 (카탈로그 자동 열거. 손 선별 0) + readingScorecard 에
  형질 버킷 축 + 형질 기여 깔때기. 완료 기준: 유상증자 x 자금조달 형질 분할(실측 1.5배)이
  정식 파이프(중립 타깃 + FM t)로 재현.
- R5: cascade.py (경제→산업 착지 = macroBeta·industry, 관계 전파 = 계열/고객 엣지 x 탄성 가정)
  + DAG-as-data 스키마 확정. 전파 판독도 일반 판독과 동일 봉인·채점 (표면 id `cascade.*`).
  조건부 채점은 06 §5 레짐 규율.

## 7. R6 — 시뮬레이터 UI (재검토 결론)

**원칙: UI 는 계산기가 아니라 원장 뷰어다.** 모든 숫자는 봉인 블록(주간 JSON)의 순수함수이고,
프론트 재계산·자체 추정 0. 데이터는 `runtime/src/data/fetch` + origins 경유 (신규 배선 금지),
공개 산출물은 주간 블록 그 자체 (별도 UI 용 bake 없음 = 런타임-SSOT 정합).

| 뷰 | 내용 | 소비 데이터 |
|---|---|---|
| 주간 보드 | board100/top10 + 표면 의견 분해 + 기권·커버리지 + gross/floor/net 3열 + never-claim | 주간 블록 |
| 회사 한 장 | 프로파일 카드(형질 8축 + 출처·staleness) + 그 회사에 도달한 연쇄 DAG + 재무 연장 차트 | profile + DAG JSON + MiniFinChart **확장** (simulated 구간 라벨. 신규 차트 금지, 재무그래프 정본 = `ui/packages/surfaces/src/terminal/charts/MiniFinChart.svelte`) |
| 성적표 | 표면 x 형질 히트맵 + 후회 곡선 + 커버리지 채점(선언 vs 실측) + 미검증 라벨 그대로 | 성적표 블록 |
| 가정 탐색기 | 가정 슬라이더 = **사전 계산된 sweep 격자 조회** (재계산 0). 강건/최고 가정 대비 뷰 + PBO·중앙값 상시 병기 | sweep 격자 블록 |

- 운영자 메모의 "3D·디시전트리" = 회사 한 장의 DAG 뷰. v0 표현은 트리/산키 (DAG JSON 이 계약
  이므로 3D 는 이후 표현 교체로 가능, 데이터 재배선 0).
- 커스텀 가정(격자 밖 if)은 공개 터미널이 아니라 로컬 앱(:8400)/pyodide 전용 (공개면은 봉인
  산출물만 = 정직 원칙).
- 무중단 규약: 로컬 프리뷰 격리 → 미배선 커밋 → 완결 단위만. push 는 스크린샷 눈검수 + 운영자
  승인 후.

## 8. 게이트·롤백

- 게이트: 각 R 단계 = 관련 테스트 green + 05 원장 기록 + (src 변경 시) 로컬 CI 게이트 2종.
  R3 이후 라이브 규약 변경은 새 시리즈 선언으로만.
- 롤백: simulate/ 신규 파일은 독립적이라 파일 단위 revert 로 안전 (기존 결정론 코어·원장 라이브
  경로는 R1~R2 에서 수정하지 않고 확장만: expectationCycle 은 함수 추가, 기존 함수 시그니처 불변).
- 실패 처리: 주간 사이클 중단 시 결번 금지 (미발행 명시 블록). 데이터 소스 열화(G9 류)는 해당
  표면 기권 처리 (silent 누락 0).
