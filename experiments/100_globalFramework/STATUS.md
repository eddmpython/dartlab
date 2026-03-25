# 100 — 세계적 기업분석 프레임워크 검증

## 목표
Morningstar, GuruFocus, Greenwald, Penman, Simply Wall St 등 세계적 기업분석 프레임워크를
dartlab 인프라(sections, gather, finance, analysis) 위에서 실증 검증한다.

## 실험 목록

| 파일 | 주제 | 상태 |
|------|------|------|
| 001_wacc.py | CAPM Beta + WACC 산출 검증 | **완료** — 10종목 WACC 5.1-10.8%, 90% 합리적 범위 |
| 002_coreEarnings.py | 비경상 항목 분리, Core Earnings | **완료** — CV 개선 60%, NAVER에서 극적 효과 |
| 003_predictability.py | Business Predictability 점수 | **완료** — 10년 연간 기준, NAVER 7.2 ~ 한전 1.6 |
| 004_moat.py | Economic Moat 5소스 정량 프록시 | **완료** — 삼성전자 5.1 1위, ROIC 보너스 전종목 0 |
| 005_epv.py | EPV / Franchise Value | **완료** — KB금융 Franchise +137조, 삼성전자 -173조 |
| 006_residualIncome.py | 잔여이익 모델 | **완료** — 삼성전자·NAVER·셀트리온·삼성바이오 가치 창출 |
| 007_uncertainty.py | Uncertainty Rating + Fair Value 밴드 | **완료** — NAVER Medium, 한전 Extreme, 5단계 분류 성공 |
| 008_forwardMultiple.py | Forward P/E, PEG | **완료** — 정규화마진·CAGR 정상, 시총 블로커 |
| 009_snowflake.py | 5축 30체크 Snowflake 캘리브레이션 | **완료** — 삼성전자 15/30 1위, 17/30 산출 가능 |

## 핵심 결과

### 001_wacc (2026-03-25)
- **Beta**: yfinance 1년 일별 수익률로 10종목 모두 산출 (0.55~1.22)
- **WACC**: 5.1%~10.8%, 평균 7.7%, 90% 합리적 범위
- **Kd**: finance_costs 부적합 → 회사채 AA- 프록시 사용이 실무 표준

### 002_coreEarnings (2026-03-25)
- **방식**: Core = 연간 operating_profit × (1-세율), Reported = 연간 net_profit
- **결과**: CV 개선 3/5 (60%) — NAVER(0.34 vs 1.95), POSCO, KB금융에서 효과
- **방향**: 제조업 op_profit 기반 + 금융업 보고이익 유지

### 003_predictability (2026-03-25)
- **방식**: 연간 매출CV + 영업이익CV + 연속성장 + 무적자 = 0~10점
- **결과**: NAVER 7.2(5년 연속성장), 삼성전자 6.5, 한국전력 1.6(적자5년)
- **방향**: 금융업 매출 프록시 필요 (KB금융 sales 부재)

### 004_moat (2026-03-25)
- **방식**: 5소스(원가·무형·전환·네트워크·규모) + ROIC 보너스 = 최대 12점
- **결과**: 삼성전자 5.1, NAVER·카카오 4.8, 한국전력 1.2. ROIC 보너스 전종목 0
- **방향**: ROIC 보너스 임계 하향(8→5%), Moat 판정 임계값 조정

### 005_epv (2026-03-25)
- **방식**: NAV=총자산-총부채, EPV=NormalizedEarnings/WACC, Franchise=EPV-NAV
- **결과**: Franchise > 0 = KB금융(+137조), 한국전력(+31조), 삼성바이오(+3.6조)
- **해석**: 금융업은 수익력>>자산, 제조업은 자산집약→Franchise 음수가 정상

### 006_residualIncome (2026-03-25)
- **방식**: RI = NI - Ke×기초자기자본, 연간 기준
- **결과**: 가치 창출 = 삼성전자(ROE 13.2%), NAVER(30.2%), 셀트리온(13.0%), 삼성바이오(7.6%)
- **결과**: 가치 파괴 = 한국전력(ROE -6.1%), 카카오(2.2%), LG화학(7.3%)
- **NAVER ROE 30.2%** — 경자산 플랫폼의 극적 자본효율

### 007_uncertainty (2026-03-25)
- **방식**: 매출CV + DOL + D/E + 영업CV → 0~100점 → 5단계
- **결과**: Medium(NAVER·삼성전자), High(셀트리온·POSCO·카카오·LG화학·현대차), Very High(삼성바이오), Extreme(한국전력)
- **방향**: 업종 기본 tier + Fair Value 밴드 synthesizer 연동

### 008_forwardMultiple (2026-03-25)
- **방식**: 연간 정규화마진(3년) × 매출(1+CAGR) × (1-세율)
- **결과**: 마진·CAGR 정상 산출. 삼성바이오 33%, NAVER 17.4%, LG화학 3.0%
- **블로커**: 시총 N/A → Forward P/E·PEG 미산출

### 009_snowflake (2026-03-25)
- **방식**: 5축(Past/Health/Future/Value/Div) × 6체크 = 30개
- **결과**: 삼성전자 15/30 1위, Health 6/6 만점. 17/30 산출 가능(57%)
- **성공**: OCF·FCF 연간 집계 정상 작동. Past·Health 100% 산출
- **블로커**: Value 6체크 전부 시총 의존

## 공통 발견사항

1. **timeseries는 분기 데이터** — `getAnnualValues()`는 분기값 리스트 반환. 연간 집계 시 IS/CF는 Q1+Q2+Q3+Q4 합산, BS는 Q4값 사용
2. **올바른 snakeId**: `operating_cashflow`(CF), `purchase_of_property_plant_and_equipment`(CF), `total_stockholders_equity`(BS)
3. **금융업 분리 필수**: KB금융은 sales 부재, BS Q4 매핑 일부 이슈
4. **시가총액 소스 블로커**: yfinance KRX 시총 비가용 → gather.price() 활용 필요
5. **한국 시장 ROIC**: 글로벌 기준 낮음(5~7%) → Moat 임계값 한국 시장에 맞게 조정 필요
