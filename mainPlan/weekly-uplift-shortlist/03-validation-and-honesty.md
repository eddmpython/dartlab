# 03. 검증과 정직성 : PIT replay + 봉인 채점

> 두 겹의 검증: (a) **사전** = 17년 주간 PIT replay 로 "이 깔때기가 과거에 어떤 분위 스프레드를 보였는가" 밴드 리포트, (b) **사후** = expectation ledger 라이브 봉인·채점으로 "지금부터의 성적" 누적. (a)는 출시 게이트, (b)가 제품의 영구 척추다.

## 1. PIT 공리 (불가침, strategy-lab 01 상속)

- decisionT < fillT: t주 금요일 마감 데이터로 계산한 board 는 다음 거래일 이후 구간 수익률로만 채점.
- 재무 신호는 회계기간 말이 아니라 **rcept_dt(공시 접수일)** 기준으로 그 시점에 알 수 있던 값만 사용 (PIT 근사 라벨).
- 공표 시차가 있는 신호(수급 T+1 등)는 SignalSpec.pitLagDays 로 asOf 를 보정.
- look-ahead 점검 없이 어떤 성과 문장도 쓰지 않는다.

## 2. 사전 replay 하네스 (G7 을 닫는 P0 산출물, 판독기 bootstrap 겸용)

- 데이터: KR gov/prices 17년+ (가격 보존형, 폐지 사유 미구분 문구 필수). US replay 는 G9 백본 확보 후 동일 프로토콜.
- 프로토콜: 매주 금요일 asOf → 판독기별 전종목 reading 생성(라이브와 동일 코드 경로) → forward 5거래일 시장 내 초과수익로 판독기별 채점 → reader scorecard bootstrap (전 레코드 issuedLive=False 영구 표기) + 합의 분위 스프레드 밴드.
- reader 내부 가중을 v1(주간 횡단면 회귀)로 승격할 때의 학습 규율:
  - purged walk-forward: train 구간에서만 추정, test 와 embargo ≥ 1주 (5거래일 라벨 겹침 차단).
  - 사전등록: 신호 목록·수축 파라미터·fold 경계를 실행 전에 원장에 고정. 결과 본 뒤 소급 변경 금지.
  - 신호·판독기 진단(주간 rank-IC·부호 일관률)은 등록/탈락 게이트의 내부 근거로만 사용.
- 커버리지의 역사적 한계 정직 표기: flow/text reader 는 과거 구간 데이터가 없거나 부분적이므로, replay bootstrap 은 "가용 reader 의 열화판" 임을 리포트 머리에 명시. price+fund 위주 결과를 전체 시스템 성능으로 승격 claim 금지.
- 산출물: 판독기별 bootstrap 성적(시장·산업 분해) + 합의 분위 스프레드 밴드(연도별 소계) + 커버리지 표. IC·t-stat 수치 단정 없음 (folk-stat 천장, 아래 §5).

## 3. 사후 검증 : expectation ledger 통합 (A2)

- 발행 시점에 **readings 전량**(전종목 x reader, 기권 포함)을 ExpectationSpec 으로 봉인 (00 §3.3). 선정 이전 봉인이라 selection bias 가 구조적으로 불가능. board100/top10 소속은 파생 플래그.
- writer 는 `simulate` 만 (expectation-grid 계약: 엔진은 ledger-blind, collector 가 유일 writer). 본 플랜은 `expectationCycle` 에 `issueReadings` collector + 주간 actuals join 채점 경로를 추가한다. 저장·스키마·append-only·재채점 append 규약은 기존 ledger 그대로 (연 ~3M 행, 연도 샤딩).
- 성적표 축: reader x 시장 x 산업 x 레짐 (수축 추정, 02 §4) + 파생으로 top10/board100 스프레드·precision@10. `buildScorecard` 의 표본 게이트 상속: N 미달 세그먼트 "미검증" 라벨 강제.
- issuedLive=True 만 성적 인정. replay bootstrap 레코드는 issuedLive=False 로 영구 구분. 과거 주차 소급 발행으로 라이브 트랙레코드를 만드는 행위 금지.
- 채점은 시장 내 완결: KR 은 KR 유니버스 초과수익, US 는 US 유니버스 초과수익. 시장 간 성적 혼합 집계 금지.

## 4. 실패의 기록

- 어떤 주에 파이프라인이 실패(데이터 미도착·엔진 오류)하면 그 주는 스킵을 원장에 명시 기록 (silent skip = 생존편향).
- 합류 미달로 top10 이 N<10 이면 N 개만 발행하고 미달 사실 기록 (02 §6.4).
- 채점 시 actuals 미도착(거래정지 등)은 grace window 후 error row 로 봉인 (expectationCycle 기존 규약 그대로).

## 5. folk-stat 천장 (수치 주장의 상한)

| 주장하고 싶은 것 | 허용 상한 |
|---|---|
| "top 분위가 좋았다" | 분위 스프레드 밴드 + 표본 주 수 명시. "눈으로 구분되는 계단" 수준 서술 |
| IC·t-stat·유의성 | 대외 수치 단정 금지. 주간 표본이 커도 신호 간 상관·레짐 의존으로 유효 표본은 작다. 회귀 계수·rank-IC 는 가중 산출·신호 게이트의 내부 근거로만 사용 |
| live 적중률 | 표본 게이트 통과 전 "미검증". 통과 후에도 기간·벤치마크·가격수익 기준 동행 |
| "이 조합이 작동한다" | 금지. "이 기간·이 유니버스에서 이 규칙을 적용했다면(과거 가정)" 로만 |

## 6. 투자자문 아님 규약 (표면 문구 봉인)

- 모든 산출물(표·dossier·CLI 출력) 하단 고정 문구: "규칙 기반 후보 목록이다. 투자 추천·자문이 아니며 성과를 보장하지 않는다. 가격수익(배당·정조정 제외) 기준."
- 금지 어휘 grep 게이트 (P2 테스트로 기계화): 추천·매수·확실·보장·검증된 팩터·시장을 이긴다·world-class 계열.
- top10 의 "근거(evidence)"라는 단어는 "독립 신호의 합류 + 반증 부재 + 공개 성적 원장" 의 3요소 정의로만 사용 (00 §1).

## 7. 자기 개선 루프 (성적이 설계로 돌아오는 길)

- 메타 가중(판독기 신뢰도)은 주간 채점 후 자동 갱신된다 (02 §5, 지수 감쇠). 이것이 "검증해서 성공여부 판독하고 개선한다. 이걸 반복해서 누적한다"의 기계화다.
- 분기마다: (a) reader scorecard 를 시장·산업·레짐 분해로 리뷰 (어느 엔진이 어디서 강한 근거인가), (b) reader 내부 가중 v1 재추정 (§2 사전등록 규율), (c) 판독기·신호 추가/제거를 eventStudy/replay 사전 근거와 함께 레지스트리 선언 변경으로. 주중 임시 변경 금지 (레코드 오염).
- 이 루프 자체가 expectation-grid 의 "시간 해자" 명제의 실행이다: 성적표가 쌓일수록 후발 주자가 복제할 수 없는 자산이 된다.
