# 046_insightEngine — 인사이트 분석 엔진

## 실험 현황

| 실험 | 상태 | 결과 |
|------|------|------|
| 001_dataMapping | 완료 | dartlab 데이터로 DartWings 인사이트 입력값 100% 커버 가능 확인 |
| 002_insightPrototype | 완료 | 5영역 + Risk/Opportunity 프로토타입 동작 확인 |
| 003_multiCompanyTest | 완료 | 5종목 교차검증, 불완전 연도 + 금융업 이슈 발견 |
| 004_incompleteYear | 완료 | 불완전 연도 제외(전략 A)가 가장 안정적 |
| 005_financialSector | 완료 | 금융업 자동 감지 100% 정확 (6/6) |
| 006_correctedRevalidation | 완료 | Performance/Health 보정 후 5종목 재검증 |
| 007_financialProfitability | 완료 | 금융업 계정 구조 탐색, ratios.py getTTM 문제 발견 |
| 008_financialInsightIntegration | 완료 | 금융업 Profitability/Cashflow 보정 통합 |
| 009_massValidation | 완료 | 20종목 대규모 검증. Cashflow A편중, Opportunity 분별력 부족 발견 |
| 010_gradingCalibration | 완료 | 등급 분별력 개선. Cashflow/Opportunity/Health 재설계 성공 |
| 011_anomalyDetection | 완료 | 6개 이상치 룰, 26건 탐지(13/20종목), 금융업 오탐 보정 |
| 012_summaryTextGeneration | 완료 | 20종목 전부 고유 요약, 5개 프로필 분류, 조사 처리 |

## 최종 등급 매트릭스 (010 기준, 20종목)

| 종목 | Perf | Profit | Health | CF | Gov | Risk | Opp |
|------|:----:|:------:|:------:|:--:|:---:|:----:|:---:|
| 삼성전자 | A | B | A | B | B | B | A |
| SK하이닉스 | A | A | A | B | B | A | A |
| 현대자동차 | D | B | F | F | A | D | C |
| POSCO홀딩스 | F | C | B | B | B | F | D |
| NAVER | B | B | B | B | N | A | B |
| 카카오 | D | D | C | B | N | B | D |
| KB금융 | D | B | C | A | B | C | C |
| 신한지주 | B | C | C | A | B | C | C |
| 미래에셋증권 | B | C | C | A | A | A | C |
| 삼성생명 | B | B | B | A | N | B | C |
| LG화학 | F | D | D | C | A | F | C |
| LG에너지솔루션 | F | C | D | C | B | F | C |
| LG전자 | D | C | D | B | A | C | C |
| LG | F | A | A | B | A | D | A |
| 기아 | D | A | C | B | A | A | C |
| 셀트리온 | C | A | B | B | B | C | B |
| 삼성물산 | D | B | B | B | A | A | C |
| SK이노베이션 | F | F | F | B | A | D | D |
| SK | F | C | F | C | N | D | C |
| 한국전력 | B | F | F | B | A | D | C |

## 이상치 탐지 결과 (011 기준)

| 종목 | 건수 | 주요 이상치 |
|------|:----:|------|
| LG | 4 | 이익↑ CF↓, 재고과잉, 차입변동, 마진개선 |
| 카카오 | 3 | 이익 대비 CF감소, 장기차입 급증, 영업외손익 급변 |
| LG화학 | 3 | 이익↑ CF↓, 영업외손익 급변, 단기차입 급증 |
| LG에너지솔루션 | 3 | 이익↑ CF↓, 단기차입 급증, 마진개선 |
| 현대자동차 | 2 | 순이익 흑자+영업CF 적자, 차입 보전 |
| SK | 2 | 단기차입금 +512%, 영업외손익 급변 |
| 셀트리온 | 2 | 이익↑ CF↓, 마진개선 |
| SK하이닉스 | 2 | 단기차입 급증, 마진개선 |
| 이상 없음 | — | 삼성전자, POSCO, NAVER, KB금융, 신한지주, 미래에셋, 삼성물산 |

## 기업 프로필 분류 (012 기준)

| 프로필 | 종목 수 | 종목 |
|--------|:------:|------|
| premium | 5 | 삼성전자, SK하이닉스, NAVER, 미래에셋증권, 삼성생명 |
| stable | 1 | 삼성물산 |
| mixed | 6 | 카카오, KB금융, 신한지주, LG전자, 기아, 셀트리온 |
| caution | 8 | 현대차, POSCO홀딩스, LG화학, LG에너지, LG, SK이노, SK, 한전 |

## 등급 분포 진화

### 전체 분포
| 버전 | A | B | C | D | F | N |
|------|---|---|---|---|---|---|
| 009 | 23.6% | 37.1% | 12.9% | 8.6% | 15.0% | 2.9% |
| 010 | 21.4% | 28.6% | 22.1% | 13.6% | 11.4% | 2.9% |

### 주요 개선 (009→010)
| 카테고리 | 009 | 010 | 변화 |
|----------|-----|-----|------|
| Cashflow | A:14 B:5 F:1 | A:4 B:12 C:3 F:1 | A 편중 해소 (70%→20%) |
| Opportunity | A:5 B:15 | A:3 B:2 C:12 D:3 | B 편중 해소, 4단계 분산 |
| Health | A:3 B:5 C:8 F:4 | A:3 B:5 C:5 D:3 F:4 | D 등급 생성 |
| Risk | A:5 B:3 C:4 F:8 | A:5 B:3 C:4 D:5 F:3 | F 편중 해소 |

## 확립된 설계 패턴

### 금융업 감지 (005)
- 신호 2개 이상이면 금융업 (오탐 0/20)
- 신호: revenue없음+opIncome있음, 부채>500%, 유동자산없음, 이자수익, 순이자수익, 보험수익

### 불완전 연도 처리 (004)
- 최신 연도 분기 수 < 4 → 해당 연도 제외

### 금융업 수익성 (007+008)
- ROE >10% 우수, >8% 양호, >5% 보통 / ROA >0.7% 양호 / CIR <50% 효율적

### Cashflow 분별력 (010)
- FCF 마진(FCF/매출) 기준 세분화: >15% 우수, >5% 양호, >0% 보통
- CF 추세(전년 대비) 가점/감점

### Opportunity 분별력 (010)
- strong≥3 + total≥5 → A, strong≥2 → B, strong≥1 or positive≥3 → C, positive≥1 → D

### Governance 점수제 (010)
- 최대주주 지분(0~3점) + 감사의견(0~2점) + 배당(0~3점) → maxScore 대비 등급

### Risk 세분화 (010)
- danger≥2 → F, danger=1 → D, warning>3 → D, warning>1 → C, 그 외 B

### 이상치 탐지 룰 (011)
- earningsQuality: 이익↑ but 영업CF↓ (금융업 제외)
- workingCapital: 매출채권/재고 급증 > 매출 증가
- balanceSheetShift: BS 항목 ±50% 이상 급변, 자본잠식
- cashBurn: 현금 급감, 영업CF적자+재무CF양수 (금융업 제외)
- marginDivergence: 영업이익률 ±5%p 이상 변동, 영업외손익 급변
- financialSector: 금융업 부채비율 ±100%p 변동, 순이익 급감

### 요약 생성 패턴 (012)
- 프로필 분류: premium/growth/stable/mixed/caution/distress
- 한국어 조사 자동 처리 (은/는, 이/가)
- 핵심 수치 1개 + 이상치 danger 시 경고문 삽입

## 남은 이슈

1. **Governance A/B 편중** (A:9 B:7, C/D/F 없음)
   - 감사의견 적정 + 배당 실시가 대부분이라 자연적 편중
   - 향후 사외이사 비율, 임원 보수 등 추가 지표로 세분화 가능

2. **Governance N 4종목** (NAVER, 카카오, 삼성생명, SK)
   - report parquet 미보유 → docs 데이터 확충 필요

3. **ratios.py getTTM 3년 데이터 문제**
   - 연간 시계열 3년 → TTM None → 인사이트에서 getLatest로 우회 중
   - ratios.py 자체 수정 검토 (getLatest fallback 추가?)

4. **영문 종목명 조사 처리**
   - NAVER은, LG은, SK은 → 받침 판단 불가 (한글 유니코드 범위 외)

## 다음 단계

- **패키지 흡수**: 010+011+012 로직을 `src/dartlab/engines/insightEngine/`로 이전
- **업종별 세분화**: 자동차/건설 부채비율, 유틸리티 특수성
- **Valuation 인사이트**: 주가 데이터 소스 결정 후 Phase 2
