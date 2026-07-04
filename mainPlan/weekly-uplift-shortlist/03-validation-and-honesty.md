# 03. 검증과 정직성 : PIT replay + 봉인 채점

> 두 겹의 검증: (a) **사전** = 17년 주간 PIT replay 로 "이 깔때기가 과거에 어떤 분위 스프레드를 보였는가" 밴드 리포트, (b) **사후** = expectation ledger 라이브 봉인·채점으로 "지금부터의 성적" 누적. (a)는 출시 게이트, (b)가 제품의 영구 척추다.

## 1. PIT 공리 (불가침, strategy-lab 01 상속)

- decisionT < fillT: t주 금요일 마감 데이터로 계산한 board 는 다음 거래일 이후 구간 수익률로만 채점.
- 재무 신호는 회계기간 말이 아니라 **rcept_dt(공시 접수일)** 기준으로 그 시점에 알 수 있던 값만 사용 (PIT 근사 라벨).
- 공표 시차가 있는 신호(수급 T+1 등)는 SignalSpec.pitLagDays 로 asOf 를 보정.
- look-ahead 점검 없이 어떤 성과 문장도 쓰지 않는다.

## 2. 사전 replay 하네스 (G7 을 닫는 P0 산출물)

- 데이터: gov/prices 17년+ (가격 보존형, 폐지 사유 미구분 문구 필수).
- 프로토콜: 매주 금요일 asOf → S0~S4 실행(라이브와 동일 코드 경로) → forward 5거래일 가격수익 → composite 5분위 스프레드 + board100/top10(k≥3) 그룹 수익 분포.
- 벤치마크 2종 병기: 유니버스 동일가중 평균, KOSPI/KOSDAQ 지수.
- 신호 커버리지의 역사적 한계 정직 표기: FLOW/TEXT family 는 과거 구간 데이터가 없거나 부분적이므로, replay 는 "가용 family 만 참여한 열화판" 임을 리포트 머리에 명시. PRICE+FUND 위주 replay 결과를 전체 깔때기 성능으로 승격 claim 금지.
- 산출물: 분위별 주간 스프레드 분포 밴드(연도별 소계 포함) + 커버리지 표. IC·t-stat 수치 단정 없음 (folk-stat 천장, 아래 §5).

## 3. 사후 검증 : expectation ledger 통합 (A2)

- 발행 시점에 board100 전 종목을 ExpectationSpec 으로 봉인 (00 §3.3). top10 만 봉인하면 자기 채점에 selection bias 가 생기므로 100 전체 + top10 플래그.
- writer 는 `simulate` 만 (expectation-grid 계약: L2 엔진은 ledger-blind, collector 가 유일 writer). 본 플랜은 `expectationCycle` 에 `issueShortlist` collector 1개 + 주간 actuals join 채점 경로를 추가한다. 저장·스키마·append-only·재채점 append 규약은 기존 ledger 그대로.
- 성적표 축: 주별 hitRate(방향, 벤치마크 대비), top10 vs board100 vs 유니버스 스프레드, precision@10. `buildScorecard` 의 표본 게이트 상속: N 미달이면 "미검증" 라벨 강제.
- issuedLive=True 만 성적 인정. 과거 주차를 소급 발행(백필)해 트랙레코드를 만드는 행위 금지 (레코드는 만들 수 있으나 issuedLive=False 로 영구 구분).

## 4. 실패의 기록

- 어떤 주에 파이프라인이 실패(데이터 미도착·엔진 오류)하면 그 주는 스킵을 원장에 명시 기록 (silent skip = 생존편향).
- 합류 미달로 top10 이 N<10 이면 N 개만 발행하고 미달 사실 기록 (02 §6.4).
- 채점 시 actuals 미도착(거래정지 등)은 grace window 후 error row 로 봉인 (expectationCycle 기존 규약 그대로).

## 5. folk-stat 천장 (수치 주장의 상한)

| 주장하고 싶은 것 | 허용 상한 |
|---|---|
| "top 분위가 좋았다" | 분위 스프레드 밴드 + 표본 주 수 명시. "눈으로 구분되는 계단" 수준 서술 |
| IC·t-stat·유의성 | 수치 단정 금지. 주간 표본이 커도 신호 간 상관·레짐 의존으로 유효 표본은 작다 |
| live 적중률 | 표본 게이트 통과 전 "미검증". 통과 후에도 기간·벤치마크·가격수익 기준 동행 |
| "이 조합이 작동한다" | 금지. "이 기간·이 유니버스에서 이 규칙을 적용했다면(과거 가정)" 로만 |

## 6. 투자자문 아님 규약 (표면 문구 봉인)

- 모든 산출물(표·dossier·CLI 출력) 하단 고정 문구: "규칙 기반 후보 목록이다. 투자 추천·자문이 아니며 성과를 보장하지 않는다. 가격수익(배당·정조정 제외) 기준."
- 금지 어휘 grep 게이트 (P2 테스트로 기계화): 추천·매수·확실·보장·검증된 팩터·시장을 이긴다·world-class 계열.
- top10 의 "근거(evidence)"라는 단어는 "독립 신호의 합류 + 반증 부재 + 공개 성적 원장" 의 3요소 정의로만 사용 (00 §1).

## 7. 자기 개선 루프 (성적이 설계로 돌아오는 길)

- 분기마다 ledger 성적을 신호 family 별로 분해 리뷰 (어느 family 가 합류 기여를 했는가).
- 신호 추가/제거·가중 변경은 이 리뷰 근거 + held-out 규약(변경 후 최소 N주 라이브 재측정) 을 거쳐 선언 변경으로만. 주중 임시 변경 금지 (레코드 오염).
- 이 루프 자체가 expectation-grid 의 "시간 해자" 명제의 실행이다: 성적표가 쌓일수록 후발 주자가 복제할 수 없는 자산이 된다.
