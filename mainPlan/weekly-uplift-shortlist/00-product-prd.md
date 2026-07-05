# 00. 제품 PRD : 주간 상승후보 100 → 근거 10

> 목표 원문: "dartlab 데이터를 최고 극상으로 이용해서 향후 1주일 상승예상종목 100종목 > 근거가 높은 10종목까지를 리스트업할 수 있는 방법을 기획한다. dartlab 의 모든 엔진을 이용하거나 부족하면 더 특정 데이터와 개념이 필요함을 기획해라."

## 1. 제품 정의

매주 1회(기본: 각 시장 금요일 장 마감 후) 실행되는 판독-채점 시뮬레이터:

```
유니버스 : KR 전상장사 (~2,800) + US EDGAR 커버 상장사 (시장별 완결, 혼합 순위 없음)
   │  위생 필터 (명시 제외만, silent cap 금지)
   ▼
엔진 판독기 8종 x 전종목 : 각 엔진이 독립 의견 발행 (방향 ±1 / 중립 / 기권 + 강도 + refs)
   │  전량 즉시 expectation ledger 봉인 (top 선정 전에 봉인)
   ▼
5거래일 후 전 판독 자동 채점 → 엔진 성적표 (reader x 시장 x 산업 x 레짐 x 종목, 수축 추정)
   │  측정된 신뢰도 = 메타 가중
   ▼
board100 (시장별) : 신뢰도 가중 합의 상위 100 + reader 별 의견 분해
   │  합류 룰 (신뢰 상위 독립 reader ≥ 3 동일 방향) + red-flag 게이트 + forecast 비모순
   ▼
top10 (시장별) : 종목별 dossier = reader 의견 + 그 reader 의 해당 세그먼트 트랙레코드
```

핵심 설계 사상 4가지:

1. **선정기가 아니라 시뮬레이터다.** 목적은 "오를 기업 고르기"가 아니라, 모든 회사에 대한 엔진별 의견을 빠짐없이 발행·채점해 **어떤 엔진이 강한 근거인지, 어떤 시장·산업·종목에서 정확한지**를 데이터로 만드는 것이다. 후보 목록은 그 원장의 파생 뷰다.
2. **합성이지 발명이 아니다.** 판독기는 전부 기존 엔진 verb 의 어댑터다. 신규 코드는 (a) EngineReading 계약 + 판독기 8종, (b) 채점기·성적표(수축 추정), (c) 신뢰도 가중 메타 결합, (d) ledger collector 뿐이다. 가중치는 임의 상수도 일회성 회귀도 아니라 **누적 성적에서 나온다** (02 §5).
3. **"근거가 높다" = 트랙레코드 있는 독립 엔진들이 같은 종목에서 합류하고, 반증(red flag)이 없다.** 단일 엔진 의견은 근거가 아니다.
4. **정직성은 봉인에서 나온다.** 전 판독이 선정 이전에 불변 봉인되므로, 잘 맞은 주만 골라 말하는 selection bias 가 구조적으로 불가능하다. 반복-채점-개선 루프가 누적되면 그 원장 자체가 데이터 자산이다.

## 2. 타깃 사용자

terminal-strategy-lab §2 의 교집합 타깃을 상속: "무료 도구를 쓰는 한국 세미프로. 펀더멘털로 회사를 판단하되, 그 판단이 시간과 횡단면 위에서 실제로 작동했는지를 규칙으로 검증하려는 사람." 본 플랜은 그 사용자에게 "이번 주 어디를 먼저 조사할까"의 조사 착수 목록(watchlist seed)을 준다. 매매 지시가 아니다.

## 3. 산출물 계약

### 3.0 readings (전종목 x reader, 매주 · 1차 산출물)

| 컬럼 | 내용 |
|---|---|
| stockCode/ticker · market | 종목 식별 (KR/US) |
| reader · asOf · horizon | 판독기 id · 판독 기준일 · 5거래일 |
| direction · score · coverageOk · abstainReason | 의견 (기권 1급 출력) |
| refs | 근거 dateRef/datasetRef |

전량 ledger 봉인 후 5거래일 뒤 채점되어 **reader scorecard** (reader x 시장 x 산업 x 레짐 x 종목, empirical-Bayes 수축 + 표본 게이트) 가 함께 산출물이 된다. 이 두 테이블이 제품의 핵심 자산이고 board/top 은 파생이다.

### 3.1 board100 (시장별 DataFrame)

| 컬럼 | 내용 |
|---|---|
| stockCode/ticker · corpName · market | 종목 식별 (KR: KOSPI/KOSDAQ/KONEX, US: EDGAR 커버) |
| asOf | 판독 기준일 (가격 기준 최종 거래일) |
| combined | 신뢰도 가중 합의 점수 |
| rankTotal | 시장 내 순위 (시장 간 혼합 없음) |
| reader 별 direction·score | 8 판독기 의견 분해 (기권 포함) |
| coverage | 참여 reader 수 / 기권 사유 요약 |
| flags | red flag·결측·한계 (null 유지, 0 대체 금지) |
| refs | datasetAsOf · reader 별 dateRef (엔진 evidence 규약 준수) |

### 3.2 top10 dossier (종목당 1건)

- 합의 요약: 동일 방향 독립 reader 목록 + 각 reader 의 의견·강도·dateRef + **그 reader 의 해당 시장·산업 트랙레코드** (수축 추정치·표본 수·미검증 여부).
- 이벤트 타임라인: 최근 공시/수주/내부자/자사주/리서치 발간 (id·date·url, listing/watch 재사용. US 는 8-K/Form 4).
- forecast reading: `quant("예측", horizon=5)` 점예측 + 90% 구간 (구간이 방향과 모순이면 top10 탈락 사유 기록).
- 리스크 패널: disclosureRisk·audit·credit·Altman·유동성 하위 신호 (통과했어도 값 공개).
- 한계 명시: 기권 reader 목록, 데이터 시차, "가격수익 기준(배당 제외)" 문구.

### 3.3 ledger 봉인 레코드 (expectation-grid 계약)

- 단위: **readings 전량** = ExpectationSpec 행 (reader 별, domain="shortlist", variable="fwdReturn5d", horizon=5거래일, kind=direction+score). board100/top10 소속은 파생 플래그.
- 채점 기준: 시장 내 초과수익 (벤치마크 2종 병기: 유니버스 동일가중 평균 + 시장지수 KOSPI/KOSDAQ 또는 S&P500).
- 채점: 5거래일 경과 후 `scoreDue` 가 실제 수익률 join → reader scorecard 갱신. 파생 축: hitRate(reader x 시장 x 산업 x 레짐), spread(top10 vs board100 vs 유니버스), precision@10.
- issuedLive=True 만 성적표 인정. replay bootstrap 레코드는 issuedLive=False 영구 구분 (03 §3).

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
| 시스템 | 전종목 x 8 판독기 주간 발행·봉인·채점이 자동 완주 (KR 먼저, US 는 판독기별 데이터 게이트 통과분부터). 실행 1회 완주 < 30분(로컬, 시장당), peak 메모리 예산 준수(04 §6) |
| 판독 완전성 | 유니버스 전 종목이 매주 reader 별 "판독/중립/기권" 셋 중 하나로 기록됨. silent 누락 0 |
| 근거 품질 | top10 전 종목이 합류 룰(신뢰 상위 독립 reader ≥ 3 동일 방향 + red flag 0 + forecast 비모순) 충족. dossier 에 reader 트랙레코드 인용 완비 |
| 성적표 | reader scorecard 가 시장·산업·레짐 분해 + 수축 추정 + 표본 게이트("미검증" 라벨)로 산출. 어떤 엔진이 강한 근거인지가 수치로 답해짐 |
| 사전 검증 | 17년 주간 PIT replay 로 판독기별 bootstrap 성적(issuedLive=False) + 합의 분위 스프레드 밴드 리포트 |
| 라이브 검증 | 발행 → 봉인 → 채점 → 성적표 갱신 사이클 최소 1회 실측 증명. 이후 매주 자동 누적 |
| 운영 | 주간 런북 1페이지 + 실패 주 스킵을 원장에 기록 (silent skip 금지) |

## 6. 비목표

- 일중/실시간 신호 (EOD 전용). 체결강도·호가·틱 데이터 도입 없음.
- 포지션 사이징·리스크 관리·매도 신호 (조사 착수 목록까지가 제품).
- 새 시계열 예측 모델 (기존 conformal forecast 소비만).
- 시장 간 혼합 순위 (KR·US 는 같은 계약·같은 코드로 각 시장 내 완결. 통합 뷰는 파생 표기만).
- 유료 데이터 구독 (무료 티어 only 규약. 갭 원장의 승격 경로도 전부 무료 공공/공개 소스).

## 7. goal 대비 정정 1건

goal 은 "상승예상 100종목"이라 말하지만, 정직 규약상 산출물의 자기규정은 "상승 후보(candidate) 100종목"이다. 예상(forecast)이라는 단어는 ledger 에 봉인되는 기대 레코드에만 쓰고, 사용자 대면 표면에서는 후보·근거·성적의 3어휘로 통일한다. 기능은 동일하고 언어만 정직해진다.

## 8. 승인 필요 (착수 전 운영자 결정 5건)

| # | 결정 | 기본 제안 | 근거 |
|---|---|---|---|
| A1 | 신규 L3 모듈 `src/dartlab/shortlist/` 신설 (최상위 verb `dartlab.shortlist`) | 승인 요청 | 다엔진 조합 + 주기 실행 + ledger 봉인은 story(보고서 조합기)와 산출물이 다름. 04 §1 배치 증명 |
| A2 | ledger collector 확장: `simulate/expectationCycle.py` 에 `issueReadings`(전종목 x reader) + 채점 경로 추가 | 승인 요청 | simulate 가 유일 writer 계약 유지. 볼륨(연 ~3M 행, 연도 샤딩 parquet) 포함 expectation-grid 진행과 조율 필요 |
| A3 | 갭 G1 (KR 전종목 투자자별 수급 벌크 sync 신설, gov prices 패턴) | P4 로 이연, 별도 승인 | 신규 sync 파이프라인 = 운영 세금. v0 는 flow reader 부분 커버(결합 상위 후보 lazy fetch) + 기권 표기 |
| A4 | naverTheme 신호의 로컬 전용 사용 (공개 산출물 미포함) | 승인 요청 | 네이버 편집저작물 재배포 금지 계약. 로컬 참고 컬럼으로만, HF/터미널 표면 0 |
| A5 | 갭 G9 (US 전종목 일별 가격 벌크 백본 신설) | P0 실측 후 상정 | US price/forecast reader 활성의 선결. 무료·재배포 가능 소스(Stooq 등) 실측이 먼저. 그 전까지 US 는 fund/event/text/credit reader 부터 활성 (EDGAR panel·filings·watcher 가 이미 커버) |
