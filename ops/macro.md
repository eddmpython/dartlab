# Macro

시장 레벨 매크로 분석 엔진. Company 없이 경제 환경을 해석한다.
dartlab의 4가지 비교 가능성 중 "시장 내/시장 간 비교"를 담당한다.

| 항목 | 내용 |
|------|------|
| 레이어 | L2 |
| 진입점 | `dartlab.macro()` |
| 소비 | gather(L1) — FRED/ECOS, scan finance.parquet |
| 생산 | ai(L3)가 매크로 환경 판단에 소비 |
| 축 | 11축 + 종합: 사이클, 금리, 자산, 심리, 유동성, 예측, 위기, 재고, 기업집계, 교역, 종합 |

## 설계 원칙

- **Company 불필요** — 시장 레벨 분석이므로 종목코드 없이 동작
- **macro ↛ analysis, analysis ↛ macro** — 같은 L2지만 상호 import 금지
- 해석의 조합은 AI(L3)의 몫
- market 파라미터로 KR/US 지원
- 3계층: L0(core/finance 순수함수) → L1(gather 데이터수집) → L2(macro 분석축)
- **외부 통계 라이브러리 없음** — Hamilton RS, Kalman DFM, Nelson-Siegel 전부 numpy 직접 구현

## API

```python
import dartlab

dartlab.macro()                       # 가이드 (축 목록)
dartlab.macro("사이클")               # 경제 사이클 4국면 판별
dartlab.macro("금리")                 # 금리 방향 + 고용/물가
dartlab.macro("자산")                 # 5대 자산 + Cu/Au ratio
dartlab.macro("심리")                 # 공포탐욕 + ISM 바로미터
dartlab.macro("유동성")               # M2 + 연준 B/S + NFCI
dartlab.macro("예측")                 # LEI + 침체확률 + Hamilton RS + Nowcast
dartlab.macro("위기")                 # Credit-to-GDP + GHS + Minsky/Koo/Fisher
dartlab.macro("재고")                 # ISM 재고순환 4국면
dartlab.macro("기업집계")             # 전종목 이익/Ponzi/레버리지 사이클
dartlab.macro("교역", market="KR")    # 교역조건 + 수출이익 선행
dartlab.macro("종합")                 # 전 10축 + 40개 전략 대시보드
```

## 11축 체계

### 기존 5축

| 축 | key | 핵심 |
|---|---|---|
| 사이클 | cycle | HY/VIX/금리차 임계값 4국면 + 전환 시퀀스 |
| 금리 | rates | DKW분해 + FedWatch근사 + 고용/물가 + BEI/실질금리 분해 |
| 자산 | assets | 5대자산 + 금3요인 + Cu/Au ratio |
| 심리 | sentiment | CNN F&G 근사 + ISM 자산배분 바로미터 |
| 유동성 | liquidity | M2/연준BS/스프레드 + 설비투자 압력 + NFCI |

### 신규 6축

| 축 | key | 핵심 | 학술 근거 |
|---|---|---|---|
| 예측 | forecast | LEI 복제 + Cleveland Fed 프로빗 + Sahm Rule + Hamilton RS + GDP Nowcasting | Estrella(1996), Hamilton(1989), Sahm(2019), Banbura(2011) |
| 위기 | crisis | Credit-to-GDP gap + GHS 위기예측 + Minsky 5단계 + Koo BSR + Fisher Debt-Deflation + 한국 부동산 스트레스 | BIS(2014), GHS(2022 JoF), Minsky, Koo(2009), Fisher(1933) |
| 재고 | inventory | ISM 재고순환 4국면(Kitchin) + ISM 자산배분 + ISM<55 인상종결 | Kitchin(1923), CB LEI |
| 기업집계 | corporate | 전종목 영업이익 합계 YoY, ICR<1 Ponzi 비율, 부채비율 중간값 | bottom-up 집계 (dartlab 독자) |
| 교역 | trade | 교역조건 + 대용치(환율-유가) + 수출이익 선행 + 양국 선행지수 + 반도체 사이클 | 투자전략 11/12/31 |
| 종합 | summary | 10축 종합 점수 + 40개 투자전략 활성/비활성 대시보드 | — |

## 40개 투자전략 대시보드

summary 축에서 40개 투자전략의 활성 여부를 실시간 판별:

| 주제 | 축 | 전략 번호 |
|---|---|---|
| 경기순환 | cycle + forecast | 1, 6, 7, 8, 9, 16 |
| 선행지수/교역조건 | trade + forecast | 5, 10, 11, 12, 14, 15, 31 |
| 금리/통화정책 | rates | 4, 19, 20, 21, 22, 28, 29, 30, 37, 39, 40 |
| 환율/달러 | assets + trade | 3, 23, 24, 25, 26, 27, 38 |
| 주가/시장 | forecast + sentiment | 2, 5, 10, 13, 17 |
| 물가/신용 | rates + liquidity + crisis | 18, 32, 33, 34, 35, 36 |

## numpy 직접 구현 방법론

외부 통계 라이브러리(statsmodels, scipy) 없이 numpy만으로 구현:

| 방법론 | 수학 | 파일 |
|---|---|---|
| Hamilton RS | Hamilton 필터 + Kim smoother + EM | regimeSwitching.py |
| GDP Nowcasting | Kalman 필터/스무더 + PCA + EM (DFM) | nowcast.py |
| Nelson-Siegel | Grid search λ + OLS β0/β1/β2 | yieldCurve.py |
| Cleveland Fed 프로빗 | Φ(α+βx), math.erf CDF | regimeSwitching.py |
| Credit-to-GDP gap | 단측 HP 필터 (EMA 재귀 근사) | crisisDetector.py |

## 기업집계 매크로 (dartlab 독자)

scan finance.parquet(전종목 5Y 재무제표)을 집계한 매크로 지표:

| 지표 | 계산 | 의미 |
|---|---|---|
| 이익 사이클 | 전종목 영업이익 합계 YoY | 기업 섹터 이익 방향 |
| Ponzi 비율 | ICR<1 기업 비중 | Minsky 금융 취약성 |
| 레버리지 사이클 | 부채비율 중간값 추이 | 시스템 레버리지 |

실측 결과 (2025년 DART):
- Ponzi 비율 32.8% — 상장기업 1/3이 영업이익으로 이자 미충당
- 레버리지 88.6% — 부채비율 중간값 상승 추세

## 데이터 소스

| 소스 | 시리즈 수 | 용도 |
|---|---|---|
| FRED | ~77개 | 미국 거시 + 금리 + ISM + LEI + 신용 + 수익률곡선 |
| ECOS | ~53개 | 한국 거시 + PPI + BSI + 교역조건 |
| scan parquet | DART 2745종목, EDGAR 6600+ | 기업집계 매크로 |

## L0 순수 함수 (22개)

| 파일 | 함수 | 역할 |
|---|---|---|
| macroCycle.py | classifyCycle | 사이클 4국면 |
| macroCycle.py | copperGoldRatio | Cu/Au 경기 선행 |
| macroCycle.py | realRateRegime | BEI/실질금리 4분면 |
| sentiment.py | calcFearGreedProxy | 공포탐욕 근사 |
| sentiment.py | ismAssetAllocation | ISM 자산배분 |
| sentiment.py | krInflationModel | 한국 물가 = 환율+유가 |
| liquidity.py | classifyLiquidityRegime | 유동성 판정 |
| liquidity.py | capexPressure | 신용스프레드 → 설비투자 |
| regimeSwitching.py | clevelandProbit | 침체확률 프로빗 |
| regimeSwitching.py | conferenceBoardLEI | LEI 복제 |
| regimeSwitching.py | sahmRule | Sahm 침체 지표 |
| regimeSwitching.py | hamiltonRegime | Hamilton RS (EM) |
| nowcast.py | gdpNowcast | DFM Nowcasting (Kalman+EM) |
| yieldCurve.py | nelsonSiegel | 수익률 곡선 분해 |
| crisisDetector.py | creditToGDPGap | BIS 신용 갭 |
| crisisDetector.py | ghsCrisisScore | GHS 위기 예측 |
| crisisDetector.py | recessionDashboard | 침체 종합 |
| crisisDetector.py | minskyPhase | Minsky 5단계 |
| crisisDetector.py | kooBalanceSheetRecession | Koo BSR |
| crisisDetector.py | fisherDebtDeflation | Fisher 부채디플레 |
| inventoryCycle.py | classifyInventoryPhase | 재고순환 4국면 |
| termsOfTrade.py | calcToT, totProxy, exportProfitLeading | 교역조건 |
| corporateAggregate.py | aggregateEarningsCycle, ponziRatio, leverageCycle | 기업집계 |
| strategyRules.py | evaluateStrategies | 40개 전략 평가 |

## 관련 코드

| 경로 | 역할 |
|---|---|
| `src/dartlab/macro/` | 11축 + 종합 |
| `src/dartlab/core/finance/macroCycle.py` | 사이클/자산/Cu-Au/BEI |
| `src/dartlab/core/finance/regimeSwitching.py` | 프로빗/LEI/Sahm/Hamilton |
| `src/dartlab/core/finance/nowcast.py` | Kalman DFM Nowcasting |
| `src/dartlab/core/finance/yieldCurve.py` | Nelson-Siegel |
| `src/dartlab/core/finance/crisisDetector.py` | 위기감지 6함수 |
| `src/dartlab/core/finance/inventoryCycle.py` | 재고순환/ISM |
| `src/dartlab/core/finance/termsOfTrade.py` | 교역조건 |
| `src/dartlab/core/finance/corporateAggregate.py` | 기업집계 |
| `src/dartlab/core/finance/strategyRules.py` | 40개 전략 룰엔진 |
