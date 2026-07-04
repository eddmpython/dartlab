# 00. 제품 PRD : 주간 상승후보 100 → 근거 10

> 목표 원문: "dartlab 데이터를 최고 극상으로 이용해서 향후 1주일 상승예상종목 100종목 > 근거가 높은 10종목까지를 리스트업할 수 있는 방법을 기획한다. dartlab 의 모든 엔진을 이용하거나 부족하면 더 특정 데이터와 개념이 필요함을 기획해라."

## 1. 제품 정의

매주 1회(기본: 금요일 장 마감 후) 실행되는 깔때기 파이프라인:

```
전상장사 (~2,800, KOSPI+KOSDAQ+KONEX)
   │  위생 필터 (명시 제외만, silent cap 금지)
   ▼
신호 수확 (6 family x 신호 레지스트리, 전 엔진 횡단)
   │  cross-sectional percentile rank 합성
   ▼
board100 : 합성점수 상위 100 (family 점수·커버리지·flag 동행)
   │  합류(confluence) 룰 + red-flag 게이트 + conformal 비모순
   ▼
top10 : 독립 근거 합류 10종목 + 종목별 evidence dossier
   │  발행 즉시
   ▼
expectation ledger 봉인 (100 전체) → 5거래일 후 자동 채점 → 성적표 누적
```

핵심 설계 사상 3가지:

1. **합성이지 발명이 아니다.** 신호 계산은 전부 기존 엔진 verb 재사용. 본 플랜의 신규 코드는 (a) 신호 레지스트리, (b) rank 합성, (c) 합류/게이트 판정, (d) ledger collector 뿐이다.
2. **"근거가 높다" = 서로 독립인 신호 family 가 같은 종목에서 합류하고, 반증(red flag)이 없고, 그 판정 방식 자체의 사후 성적이 공개 원장에 쌓인다.** 단일 신호 상위는 근거가 아니다 (quant/scan 스킬의 axis-specific 회피 룰과 정합).
3. **예측의 정직성은 봉인에서 나온다.** 상승 "예상"은 발행 시점에 불변 봉인되고 실제 5거래일 수익률로 채점된다. 잘 맞는 주만 골라 말하는 selection bias 를 구조적으로 차단하기 위해 top10 이 아니라 board100 전체를 봉인한다.

## 2. 타깃 사용자

terminal-strategy-lab §2 의 교집합 타깃을 상속: "무료 도구를 쓰는 한국 세미프로. 펀더멘털로 회사를 판단하되, 그 판단이 시간과 횡단면 위에서 실제로 작동했는지를 규칙으로 검증하려는 사람." 본 플랜은 그 사용자에게 "이번 주 어디를 먼저 조사할까"의 조사 착수 목록(watchlist seed)을 준다. 매매 지시가 아니다.

## 3. 산출물 계약

### 3.1 board100 (DataFrame)

| 컬럼 | 내용 |
|---|---|
| stockCode · corpName · market | 종목 식별 (KOSPI/KOSDAQ/KONEX) |
| asOf | 신호 기준일 (가격 기준 최종 거래일) |
| composite | 합성점수 (0~1 rank 스케일) |
| rankTotal | 유니버스 내 순위 |
| price* · flow* · event* · fund* · text* · context* | family 별 점수 + 구성 신호 rank |
| coverage | 계산에 실제 참여한 family 수 / 신호 수 |
| flags | red flag·결측·한계 (null 유지, 0 대체 금지) |
| refs | datasetAsOf · 신호별 dateRef (scan/quant evidence 규약 준수) |

### 3.2 top10 dossier (종목당 1건)

- 합류 요약: 상위 분위에 든 독립 family 목록 + 각 family 의 대표 신호 값·rank·dateRef.
- 이벤트 타임라인: 최근 공시/수주/내부자/자사주/리서치 발간 (id·date·url, listing/watch 재사용).
- conformal forecast: `quant("예측", code, horizon=5)` 점예측 + 90% 구간 (구간이 방향과 모순이면 top10 탈락 사유 기록).
- 리스크 패널: disclosureRisk·audit·credit·Altman·유동성 하위 신호 (통과했어도 값 공개).
- 한계 명시: 커버리지 결측 family, 데이터 시차, "가격수익 기준(배당 제외)" 문구.

### 3.3 ledger 봉인 레코드 (expectation-grid 계약)

- 단위: board100 각 종목 = ExpectationSpec 1행. domain="shortlist", variable="fwdReturn5d", horizon=5(거래일), kind=direction+point.
- direction: 상승 (초과수익 기준 벤치마크 2종 병기: KOSPI/KOSDAQ 동일가중 유니버스 평균, 시장지수).
- 채점: 5거래일 경과 후 `scoreDue` 가 실제 수익률 join. 성적표 축: hitRate(방향), spread(top10 vs board100 vs 유니버스), precision@10.
- issuedLive=True 만 성적표 인정. 백필 금지 (03 §4).

## 4. 정직 규약 (불가침)

terminal-strategy-lab 04 never-claim 을 본 제품 언어로 상속:

1. "예상 종목" 표현은 항상 "규칙 기반 후보(candidate). 투자 추천 아님" 봉인 문구 동행.
2. "검증된 팩터" · "시장을 이긴다" · "적중률 보장" 단어 0 (grep 게이트).
3. 사전 replay 의 IC·t-stat 수치 단정 금지. 분위 스프레드는 밴드·"눈으로" 수준까지 (표본 ~회 명시).
4. 수익률은 "가격수익(배당·정조정 제외)" 로만 지칭.
5. 폐지 종목 처리: 가격 보존형 유니버스(폐지 사유 미구분) 문구 필수.
6. live 성적은 표본 게이트(03 §5) 통과 전 "미검증" 라벨 강제 (expectation-grid 02 §4 와 동일).
7. 미빌드 상태에서 성능 주장 금지. precision@10 목표치는 존재하지 않는다. 측정 결과만 존재한다.

## 5. 성공 기준

| 층 | 기준 |
|---|---|
| 시스템 | 전상장사 유니버스에서 주 1회 board100+top10 산출. 실행 1회 완주 < 30분(로컬), peak 메모리 예산 준수(04 §6) |
| 근거 품질 | top10 전 종목이 합류 룰(독립 family ≥ 3 상위분위 + red flag 0 + forecast 비모순) 충족. evidence table 에 refs 완비 |
| 커버리지 정직 | family 별 커버리지 리포트 동행 (예: FLOW family 는 G1 승격 전 부분 커버 명시). 결측 0 대체 0건 |
| 사전 검증 | 17년 주간 PIT replay 에서 합성점수 분위별 5거래일 forward 스프레드 밴드 리포트 산출 (수치 과장 없이) |
| 라이브 검증 | 봉인 → 채점 사이클 최소 1회 실측 증명. 이후 매주 자동 누적 |
| 운영 | 주간 런북 1페이지 (실행·검수·봉인·예외) + 실패 시 해당 주 스킵을 원장에 기록 (silent skip 금지) |

## 6. 비목표

- 일중/실시간 신호 (EOD 전용). 체결강도·호가·틱 데이터 도입 없음.
- 포지션 사이징·리스크 관리·매도 신호 (조사 착수 목록까지가 제품).
- 새 시계열 예측 모델 (기존 conformal forecast 소비만).
- 미국(EDGAR) 유니버스 (v0 = KR 전상장사. US 확장은 데이터 대칭 확인 후 별도 사이클).
- 유료 데이터 구독 (무료 티어 only 규약. 갭 원장의 승격 경로도 전부 무료 공공/공개 소스).

## 7. goal 대비 정정 1건

goal 은 "상승예상 100종목"이라 말하지만, 정직 규약상 산출물의 자기규정은 "상승 후보(candidate) 100종목"이다. 예상(forecast)이라는 단어는 ledger 에 봉인되는 기대 레코드에만 쓰고, 사용자 대면 표면에서는 후보·근거·성적의 3어휘로 통일한다. 기능은 동일하고 언어만 정직해진다.

## 8. 승인 필요 (착수 전 운영자 결정 4건)

| # | 결정 | 기본 제안 | 근거 |
|---|---|---|---|
| A1 | 신규 L3 모듈 `src/dartlab/shortlist/` 신설 (최상위 verb `dartlab.shortlist`) | 승인 요청 | 다엔진 조합 + 주기 실행 + ledger 봉인은 story(보고서 조합기)와 산출물이 다름. 04 §1 배치 증명 |
| A2 | ledger collector 확장: `simulate/expectationCycle.py` 에 `issueShortlist`/채점 경로 추가 | 승인 요청 | simulate 가 유일 writer 계약 유지. expectation-grid 진행과 충돌 없는지 확인 필요 |
| A3 | 갭 G1 (전종목 투자자별 수급 벌크 sync 신설, gov prices 패턴) | P4 로 이연, 별도 승인 | 신규 sync 파이프라인 = 운영 세금. v0 는 FLOW family 부분 커버(상위 후보 대상 lazy fetch)로 시작 |
| A4 | naverTheme 신호의 로컬 전용 사용 (공개 산출물 미포함) | 승인 요청 | 네이버 편집저작물 재배포 금지 계약. 로컬 참고 컬럼으로만, HF/터미널 표면 0 |
