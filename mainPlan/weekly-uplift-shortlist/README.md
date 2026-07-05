# Weekly Uplift Shortlist : 주간 상승후보 100 → 근거 10 깔때기 PRD Index

상태: 완전 설계 v0.3 (2026-07-05. v0.1 신호 깔때기 → v0.2 학습 가중 → v0.3 운영자 지시로 **엔진별 전종목 판독기 + EDGAR 통합** 구조 전환). **P0 착수는 운영자 승인 대기** (승인 필요 5건 = 00 §8).
범위: dartlab 전 엔진이 **매주 모든 회사(KR 전상장사 + EDGAR 커버 US 상장사)에 대해 각자 판독(방향·강도·기권)을 발행**하고, 전량 봉인 후 5거래일 뒤 자동 채점해 엔진별 성적표를 누적하는 시뮬레이터. "상승 후보 100 → 근거 10" 목록은 이 판독 원장의 파생 뷰다.

---

## 한 줄 결정

이 플랜은 "오를 기업을 고르는 예측기"가 아니라 **판독-채점 시뮬레이터**를 짓는다. 엔진별 판독기 8종이 매주 전종목에 독립 의견을 내고(기권 포함), 전량 발행 시점에 봉인되고, 1주 뒤 전부 채점되어 "어떤 엔진이, 어떤 시장·산업·종목에서, 얼마나 정확한가"가 데이터로 누적된다. 후보 100/10 은 그 측정된 신뢰도로 가중한 합의의 파생 뷰일 뿐이다. 트랙레코드는 과거로 돌아가 만들 수 없으므로, 오늘 봉인을 시작한 쪽만 시간 해자를 가진다 (expectation-grid 와 동일 명제). DART 만이 아니라 EDGAR 를 같은 계약으로 통합한다: 판독기·채점기·성적표는 시장 파라미터화된 단일 코드이고, 시장 간 순위 혼합은 하지 않는다 (시장 내 상대 판독 + 시장별 벤치마크).

## 선행 자산 접점 (이 플랜이 새로 짓지 않는 것)

| 기존 자산 | 위치 | 본 플랜의 소비 방식 |
|---|---|---|
| 전종목 일별 가격/시총 17년+ (gov/prices, date 샤딩) | `gather/bulkData/hfBulk.py` (category govPrices) | PRICE/유동성 신호의 원천. 런타임 직독, 별도 베이크 없음 |
| quant 횡단면/신호 자산 (momentum·volume·eventStudy·tripleBarrier·alphas 9종) | `src/dartlab/quant/{signal,alphas,labels}` | 신호 함수 재사용. 재구현 금지 |
| scan 횡단면 24축 (valuation·growth·disclosureRisk·orders·insider·capital 등) | `src/dartlab/scan/**` | FUND/EVENT family 원천 |
| 공시 diff 스코어러 (watcher) | `scan/watch/{scanner,scorer,digest}.py` | EVENT family 의 공시 변화 점수 |
| narrative pulse + regime (Pettitt change-point) | `gather("narrative")` + `scan/narrativeRegime.py` | TEXT family + 레짐 가중 입력 |
| macro 15축 (cycle·rates·시뮬레이션 BVAR) | `dartlab.macro(...)` | CONTEXT family + 레짐 판정 |
| expectation ledger (발행 봉인 + 자동 채점 + 성적표) | `simulate/{expectationLedger,expectationCycle}.py` | 매주 100종목 방향 기대를 봉인·채점하는 검증척추 |
| 유니버스 주간 replay 백테스트 자산 | `mainPlan/_done/terminal-strategy-lab` (U1) | 사전 PIT replay 검증 하네스 재사용 |
| conformal forecast (5d 점예측 + 90% 구간) | `dartlab.quant("예측", code, horizon=5)` | top10 최종 게이트 (방향 비모순 확인) |
| EDGAR panel (raw XBRL 자급 파싱) + filings + watcher 10-K topic | `providers/edgar` + `scan/watch` | US fund/event/text reader 의 원천 (01 §2.5) |

## 문서 지도

1. [00-product-prd.md](00-product-prd.md) : 제품 정의 · 산출물 계약 · 정직 규약(never-claim 상속) · 성공 기준 · 비목표 · **승인 필요 4건**
2. [01-signal-inventory.md](01-signal-inventory.md) : 전 엔진 신호 전수 인벤토리(엔진 x 신호 x 공개 verb x PIT 주의) + **갭 원장 G1~G8** (부족 데이터·개념)
3. [02-scoring-and-funnel.md](02-scoring-and-funnel.md) : 6단 깔때기 · 신호 레지스트리 계약 · rank 합성 수학 · 레짐 가중 · 합류(confluence) 룰 · red-flag 게이트
4. [03-validation-and-honesty.md](03-validation-and-honesty.md) : PIT 공리 · 17년 주간 replay 사전검증 · ledger 봉인 채점 · 표본 게이트 · folk-stat 천장 · 투자자문 아님 규약
5. [04-architecture-and-phases.md](04-architecture-and-phases.md) : 배치(L3 신설) · import 방향 증명 · 파일/함수/테스트/롤백 · P0~P5 · CI 게이트 체크리스트
6. [05-progress-ledger.md](05-progress-ledger.md) : 진행원장

## 경계 (claim 금지)

- 예측 모델 신설 0. 시계열 모델은 기존 `quant("예측")` conformal 만 소비.
- 봉인·채점 원장은 `simulate` 가 유일 writer (expectation-grid 계약 준수). 본 플랜은 collector verb 1개만 추가.
- 백테스트 통계 엄밀성 언어는 `terminal-strategy-lab/04-honesty-and-rigor.md` 의 never-claim 7선을 그대로 상속.
- 터미널 UI 서피스는 P5 로 격리 (별도 눈검수 + push 승인 게이트). P0~P4 는 라이브러리/CLI 까지만.
- 매수 추천 아님: 산출물 어디에도 "매수/추천/검증된 팩터" 라벨 0. 이름부터 shortlist(후보 목록)다.

## 완성 정의 (goal 원문 기준)

엔진별 판독기가 매주 전종목(KR 전상장사, US 는 데이터 백본 게이트 통과 판독기부터)에 판독을 발행·봉인하고, 5거래일 뒤 자동 채점되어 엔진 성적표가 누적되며, 그 신뢰도 가중 합의로 "상승 후보 100 → 근거 10"이 evidence(판독기별 의견 + 해당 세그먼트 트랙레코드)와 함께 매주 산출되는 상태. 최소 1회 발행 → 채점 → 성적표 갱신 사이클이 실데이터로 증명되어야 한다. 부족 데이터·개념은 01 갭 원장(G1~G10)에 승격 경로와 함께 전수 기록됨 (이 문서군으로 충족).
