# Macro

시장 레벨 매크로 분석 엔진. Company 없이 경제 환경을 해석한다.

| 항목 | 내용 |
|------|------|
| 레이어 | L2 |
| 진입점 | `dartlab.macro()` |
| 소비 | gather(L1) — FRED/ECOS, scan finance.parquet |
| 생산 | ai(L3)가 매크로 환경 판단에 소비 |
| 축 | 11축: 사이클, 금리, 자산, 심리, 유동성, 예측, 위기, 재고, 기업집계, 교역, 종합 |

## 설계 원칙

- **Company 불필요** — 종목코드 없이 동작
- **macro ↛ analysis** — 같은 L2지만 상호 import 금지. 해석 조합은 AI(L3)의 몫
- **numpy만** — Hamilton RS, Kalman DFM, Nelson-Siegel 전부 numpy 직접 구현. 외부 통계 라이브러리 0
- 3계층: L0(core/finance 순수함수) → L1(gather 수집) → L2(macro 분석축)
- 공통 헬퍼: `_helpers.py`의 `get_gather`, `fetch_latest`, `fetch_series_list`, `collect_timeseries` — 중복 코드 제거, 로깅 통합
- **as_of/overrides 관통** — 전체 11축에 백테스트(`as_of`) + 시나리오(`overrides`) 지원

## API

```python
import dartlab

# 기본
dartlab.macro()                       # 가이드
dartlab.macro("사이클")               # 4국면 판별
dartlab.macro("금리")                 # 금리 + Nelson-Siegel + BEI 분해
dartlab.macro("자산")                 # 5대 자산 + Cu/Au + 금 3요인
dartlab.macro("심리")                 # 공포탐욕 + ISM 바로미터
dartlab.macro("유동성")               # M2 + 연준 B/S + NFCI + 자체 FCI
dartlab.macro("예측")                 # LEI + 침체확률 + Sahm + Hamilton RS + Nowcast
dartlab.macro("위기")                 # Credit-to-GDP + GHS + Minsky + Koo + Fisher
dartlab.macro("재고")                 # ISM 재고순환 4국면
dartlab.macro("기업집계")             # 전종목 이익/Ponzi/레버리지
dartlab.macro("교역", market="KR")    # 교역조건 + 수출이익 선행
dartlab.macro("종합")                 # 10축 + 40전략 + 포트폴리오 매핑

# 시나리오 시뮬레이션
dartlab.macro("사이클", overrides={"hy_spread": 600, "vix": 35})

# 백테스트 (과거 시점 재현)
dartlab.macro("금리", as_of="2022-01-01")

# 한국
dartlab.macro("교역", market="KR")
```

---

## 축별 가이드

### 사이클 (cycle)

4국면: 확장 → 둔화 → 침체 → 회복. 투자 의사결정의 출발점.

| 키 | 의미 | 활용 |
|---|---|---|
| `phase` | expansion/slowdown/contraction/recovery | 자산배분의 뼈대 |
| `confidence` | high/medium/low | low = 전환기 = 가장 중요 |
| `transition` | 전환 시퀀스 | 국면 전환 임박 신호 |
| `sectorStrategy` | 업종별 overweight/neutral/underweight | 섹터 로테이션 |

주의: HY + 장단기차 동시 악화 → 침체 강화. VIX 단독 급등은 일시적 가능. KR은 CLI 의존(느림).

### 금리 (rates)

금리 방향 + DKW 분해 + Nelson-Siegel + BEI/실질금리 4분면.

| 키 | 의미 | 활용 |
|---|---|---|
| `outlook.direction` | cut/hold/hike | 가장 중요한 방향 |
| `expectation.spread2yFf` | 2Y-FF 스프레드 | 음수 = 시장이 인하 기대 |
| `decomposition` | 명목 = 실질 + BEI + 기간프리미엄 | 금리 원천 분해 (US만) |
| `yieldCurve` | Nelson-Siegel β0(Level)/β1(Slope)/β2(Curvature) | 수익률곡선 형태 |
| `realRateRegime` | tightening/reflation/goldilocks/deflation | BEI×실질금리 4분면 |
| `employment/inflation` | 고용/물가 상태 | 금리 방향의 근거 |

### 자산 (assets)

5대 자산 + 금 3요인 + Cu/Au + VIX 구간.

| 키 | 의미 |
|---|---|
| `assets` | 자산별 방향 + 해석 |
| `goldDrivers` | 금 = f(실질금리, 달러, 안전자산). 어느 요인이 지배적인지 |
| `copperGold` | Cu/Au ratio. 상승 = 산업수요 확대, 하락 = 안전자산 선호 |
| `vixRegime` | complacent/normal/anxious/fear/panic + 분할매수 차수 |

### 심리 (sentiment)

공포탐욕 0-100 + ISM 자산배분.

| 키 | 의미 |
|---|---|
| `fearGreed.score` | 0-100. <25 극단공포(매수), >75 극단탐욕(경계) |
| `ismAllocation` | ISM >55 risk-on, <50 risk-off |
| `vixRegime.buySignal` | 0/1/2/3 분할매수 차수 |

### 유동성 (liquidity)

M2 + 연준 B/S + 신용스프레드 + NFCI + 자체 FCI.

| 키 | 의미 |
|---|---|
| `regime` | abundant/normal/tight |
| `nfci` | Chicago Fed 금융상태지수 (US, 주간, FRED 직접) |
| `fci` | 자체 FCI — GS 방식 5변수 z-score (US+KR) |
| `capexPressure` | HY 스프레드 → 설비투자 압력 |

FCI 구현: `fci = w₁z(정책금리) + w₂z(장기금리) + w₃z(HY) + w₄z(-주가) + w₅z(환율)`
가중치: 금리 0.35, 스프레드 0.25, 주가 0.25, 환율 0.15 (GS 논문 참고).
**한국 FCI — 오픈소스 최초**: 기준금리 + 국고3Y + 회사채AA + USDKRW.

### 예측 (forecast)

LEI + 침체확률 + Sahm Rule + Hamilton RS + GDP Nowcast.

| 키 | 의미 |
|---|---|
| `recessionProb` | Cleveland Fed 프로빗 침체확률 (0-1). >0.3 경계 |
| `lei` | Conference Board LEI 복제. expansion/caution/recession_warning |
| `sahmRule` | 실업률 3M MA - 12M 최저 MA. ≥0.5%p 침체 신호 |
| `hamiltonRegime` | 2-regime Markov Switching. contraction 확률 |
| `nowcast` | GDP 실시간 추정 (DFM Kalman) |

### 위기 (crisis)

Credit-to-GDP gap + GHS + Minsky 5단계 + Koo BSR + Fisher Debt-Deflation.

| 키 | 의미 |
|---|---|
| `creditGap` | BIS 신용/GDP 갭. >10%p 최고 경고, CCyB 0-2.5% |
| `ghsScore` | 3년 신용팽창+자산급등 → 위기확률. 정상 7%, 위험 40% |
| `minskyPhase` | displacement→boom→overtrading→discredit→revulsion |
| `kooRecession` | 민간 금융잉여 + 저금리 = 대차대조표 침체. 재정 확대 필수 |
| `fisherDeflation` | DSR + CPI + NPL → 부채-디플레이션 악순환 위험 |
| `krHousingStress` | 한국 아파트가격 YoY + 가계부채 (KR만) |
| `recessionDashboard` | 프로빗+LEI+ISM+신용+스프레드 종합 |

### 재고 (inventory)

ISM 재고순환 4국면 + 자산배분 바로미터.

| 키 | 의미 |
|---|---|
| `inventoryPhase` | active_restock(회복) → passive_restock(확장) → active_destock(수축) → passive_destock(바닥) |
| `ismBarometer` | ISM 수준별 주식/금리 시사점. <55+하락 = 인상종결 |
| `ismAllocation` | risk-on / neutral / risk-off |

### 기업집계 (corporate)

전종목 재무제표 → 이익사이클, Ponzi비율, 레버리지. scan/finance.parquet 기반.

| 키 | 의미 | 실측 (2025 DART) |
|---|---|---|
| `earningsCycle` | 전종목 영업이익 YoY | 2023 -30.9% → 2024 +38.6% → 2025 -19.5% |
| `ponziRatio` | ICR<1 기업 비중 (Minsky 취약) | 2021 16.8% → 2025 32.8% |
| `leverageCycle` | 부채비율 중간값 | 2023 70.4% → 2025 88.6% |

### 교역 (trade) — KR 전용

교역조건 + 대용치 + 수출이익 선행 + 양국 선행지수.

| 키 | 의미 |
|---|---|
| `termsOfTrade` | 수출물가/수입물가 비율 |
| `totProxy` | 환율YoY - 유가YoY (투자전략 12) |
| `exportProfit` | 교역조건 + 수출량 → 수출기업 이익 선행 |
| `leadingRelativeStrength` | US LEI vs KR CLI → 환율 방향 |

### 종합 (summary)

10축 + 40전략 + 포트폴리오 매핑.

| 키 | 의미 |
|---|---|
| `overall` | favorable/neutral/unfavorable |
| `score` | 종합 점수 |
| `contributions` | 축별 점수 기여도 |
| `allocation` | 주식/채권/금/현금 % (regime × phase 매핑) |
| `strategies` | 40개 전략 active/direction/strength/confidence |

---

## 시나리오 + 백테스트

### 시나리오 시뮬레이션 (overrides)

모든 축의 `_fetch_*` 데이터를 직접 교체하여 "만약 X가 바뀌면?" 시뮬레이션.

```python
baseline = dartlab.macro("종합")
scenario = dartlab.macro("종합", overrides={"hy_spread": 600, "vix": 35})
# scenario["score"] < baseline["score"]  → 위기 환경에서 점수 하락 확인
```

### 백테스트 (as_of)

전체 축에 `as_of` 파라미터 → gather 시계열을 해당 날짜까지만 사용.

```python
past = dartlab.macro("사이클", as_of="2022-01-01")
# 2022년 1월 시점의 데이터만으로 사이클 판별
```

### walk-forward 프레임워크

```python
from dartlab.core.finance.macroBacktest import walkForwardBacktest
result = walkForwardBacktest("2005-01-01", "2024-01-01", stepMonths=3)
# result.precision, result.recall — NBER 침체 기준 적중률
```

---

## 포트폴리오 매핑

`portfolioMapping.py` — regime × phase → 자산배분 가중치.

| 종합 판정 | 주식 | 채권 | 금 | 현금 |
|----------|------|------|---|------|
| favorable + expansion | 70% | 20% | 5% | 5% |
| favorable + recovery | 60% | 25% | 5% | 10% |
| neutral | 50% | 30% | 10% | 10% |
| unfavorable + slowdown | 30% | 40% | 15% | 15% |
| unfavorable + contraction | 20% | 40% | 20% | 20% |

미세 조정: 극단공포 → 주식 +10%p(역투자), FCI 긴축 → 채권 +5%p, Minsky 과열 → 금 +5%p.

---

## 축 조합 가이드

| 질문 | 보는 축 | 판단 기준 |
|------|---------|----------|
| 경기 침체가 오나? | forecast + cycle + crisis | 프로빗 >30% + 둔화/침체 + Minsky 과열 이후 |
| 금리는 어떻게 되나? | rates + forecast + liquidity | 인하기대(2Y-FF 음수) + LEI 하락 + 유동성 긴축 |
| 한국 수출은? | trade + inventory + corporate | ToT 악화 + 적극감축 + 이익수축 |
| 지금 주식 사도 되나? | sentiment + cycle + crisis | F&G <25 + 회복기 + 위기점수 낮음 |
| 금융위기 가능성? | crisis + liquidity + corporate | Gap>10 + GHS>50 + Ponzi>30% |
| 환율 방향은? | trade + assets + rates | 양국 선행지수 + 달러인덱스 + 금리차 |

---

## 방법론 상세

### Hamilton Regime Switching (1989)

GDP 성장률이 2개 국면(확장/침체)을 오가는 Markov Switching 모델.

수학: `y_t = μ_{s_t} + φ·y_{t-1} + ε_t`, s_t ∈ {0,1} Markov chain.
추정: Hamilton 필터(forward) → Kim smoother(backward) → EM 반복.
구현: `regimeSwitching.py` — numpy 직접, 539줄. EM maxIter=100.
출력: filteredProbs, smoothedProbs, currentRegime, currentProb, params.
한계: 사후 판별에 강하지만 실시간 전환점 2-3분기 지연.

### Kalman DFM GDP Nowcasting (Banbura 2011)

여러 월간 지표에서 공통 팩터를 추출하여 GDP 실시간 추정.

수학: 관측 `y_t = Λf_t + e_t`, 상태 `f_t = Af_{t-1} + η_t`. Kalman 필터 predict-update.
추정: PCA 초기화 → Kalman 필터/스무더 → EM 반복 (Λ, A, Q, R 갱신).
구현: `nowcast.py` — numpy 직접, 387줄. 결측(NaN) 자동 처리.
한계: 동일 주파수만. 혼합 주파수(주간+월간+분기) 미지원.

### Nelson-Siegel 수익률곡선 (1987)

수익률곡선 전체를 3팩터로 분해.

수학: `y(τ) = β₀ + β₁[(1-e^{-τ/λ})/(τ/λ)] + β₂[(1-e^{-τ/λ})/(τ/λ) - e^{-τ/λ}]`
- β₀ = Level (장기 수준), β₁ = Slope (기울기, -β₁ = 장단기차), β₂ = Curvature (곡률)
추정: λ grid search (0.3~6.0) + OLS.
구현: `yieldCurve.py` — numpy 직접. 입력: DGS1~DGS30 8개 만기.
활용: Slope가 음수(역전) → 침체 예고. 기존 T10Y3M 스프레드보다 정교.

### Cleveland Fed 프로빗 (Estrella-Mishkin 1996)

10Y-3M 스프레드 → 12개월 내 침체 확률.

수학: `P(recession) = Φ(α + β·spread)`, α=-0.5333, β=-0.6330 (하드코딩).
구현: `regimeSwitching.py` — `math.erf`로 CDF 직접 구현.
실적: 지난 8번 미국 침체 전부 사전 감지. 리드타임 6-18개월 편차.

### Sahm Rule (2019)

실업률 3개월 이동평균 - 12개월 최저 3개월 이동평균.

수학: `sahm = MA3(current) - min(MA3, past 12 months)`. ≥0.5%p → 침체.
한계: 2024년 0.57%p 도달했으나 실제 침체 없음 (false positive). 단독 의존 금지.

### BIS Credit-to-GDP Gap (2014)

신용/GDP 비율과 장기 트렌드의 편차. Basel III 공식 지표.

수학: `gap = actual - trend`. trend = 단측 HP 필터(λ=400,000).
구현: `crisisDetector.py` — EMA 재귀 근사 (`alpha = 1/(1+√λ)`).
활용: gap >2%p → CCyB 발동, >10%p → 최고 경고.

### GHS 금융위기 예측 (2022 Journal of Finance)

3년간 신용 팽창 + 자산가격 급등 동시 → 위기 확률 급등.

근거: 42개국 1950-2016 실증. 정상 ~7%, 동시 발생 ~40%.
구현: `crisisDetector.py` — 신용 3Y 변화 + 자산 3Y 수익률 복합 스코어.

### Minsky 5단계 (Kindleberger-Minsky)

displacement → boom → overtrading → discredit → revulsion.

정량화: creditGap(boom), HY<300+VIX<15(overtrading), HY>600(discredit), DXY급등(revulsion).
구현: `crisisDetector.py` — 점수 기반 판별, 최고 점수 단계 선택.

### Koo Balance Sheet Recession (2009)

민간 금융잉여(저축-투자) + 저금리 = 대차대조표 침체. 금리 인하 무효, 재정 확대 필수.

구현: `crisisDetector.py` — FRED W987RC1Q027SBEA(저축), GPDI(투자), GDP.

### Fisher Debt-Deflation (1933)

과잉 부채 → 디스트레스 매각 → 물가 하락 → 실질 부채 증가 → 악순환.

구현: `crisisDetector.py` — DSR(TDSP) + NPL(DRSFRMACBS) + CPI YoY 조합.

### FCI 금융환경지수 (Hatzius 2010)

여러 금융 변수를 하나의 지수로 합성.

구현 2가지:
1. NFCI 직접 소비 — FRED `NFCI` (Chicago Fed 105변수 DFM, 주간)
2. 자체 FCI — GS 방식 5변수 z-score. `fci.py`.

---

## 백테스트 결과 (실제 FRED 데이터, 2000-2024)

### Cleveland Fed 프로빗 — 3/3 침체 사전 감지

| 침체 | 감지 | 리드타임 |
|------|------|---------|
| 2001년 (닷컴) | ✅ | 2-8개월 전 |
| 2007년 (GFC) | ✅ | 7-16개월 전 |
| 2020년 (코로나) | ✅ | 5-8개월 전 |

"12개월 이내 침체 시작" 예측 성능 (월간, 300관측):

| 임계값 | precision | recall | FPR | F1 |
|--------|-----------|--------|------|-----|
| 0.10 | 33.1% | **100%** | 30.3% | 49.7% |
| 0.15 | 39.2% | 97.4% | 22.6% | 55.9% |
| **0.20** | **45.5%** | **89.7%** | 16.1% | **60.3%** |
| 0.25 | 41.3% | 66.7% | 14.2% | 51.0% |
| 0.30 | 38.3% | 46.2% | 11.1% | 41.9% |
| 0.40 | 17.2% | 12.8% | 9.2% | 14.7% |

**최적: 임계값 0.20에서 recall 90%, precision 46%, F1 60%.** 임계값 0.10이면 recall 100%(모든 침체 감지)이지만 FP 많음. 0.20이 가장 균형.
3번의 침체를 전부 사전 감지. FP는 금리 역전 후 침체까지 6-18개월 지연 구간에서 발생.

### Sahm Rule — 3/3 트리거 (후행)

| 침체 | 트리거 | 시차 |
|------|--------|------|
| 2001년 | ✅ | 후행 4개월 |
| 2007년 | ✅ | 후행 2개월 |
| 2020년 | ✅ | 후행 2개월 |

Sahm은 침체 시작 후 2-4개월에 트리거 — **확인 지표**(선행 아님).

### 금리역전 (10Y-3M < 0) — 3/3 선행

| 침체 | 역전 시점 | 리드타임 |
|------|---------|---------|
| 2001년 | 2000-07 | 8개월 |
| 2007년 | 2006-08 | 16개월 |
| 2020년 | 2019-05 | 9개월 |

수익률곡선 역전은 가장 일관된 선행지표 — 8-16개월 선행.

### Nelson-Siegel 현재 상태 (2026-04-04)

```
β0(Level) = 5.32, β1(Slope) = -1.60, β2(Curvature) = -1.84
→ 실효 기울기 +1.60%p — 가파른 정상 (경기 확장/인플레 기대)
RMSE = 0.052 (피팅 우수)
```

### 침체확률 → S&P500 12개월 수익률

| 조건 | 12M 후 S&P500 평균 | 관측 수 |
|------|-------------------|---------|
| 침체확률 ≥30% | **+21.9%** | 19 |
| 침체확률 <10% | +5.2% | 35 |

**역설적 결과**: 침체확률이 높을 때 주식이 더 올랐다. 이유: 금리 역전 후 12개월은 대부분 침체 직전 + 금리 인하 기대 → 자산 반등. 이것은 "금리 역전 = 즉시 매도" 전략이 틀렸다는 실증이다.

### 금리역전 → S&P500 12개월 수익률

| 조건 | 12M 후 S&P500 평균 | 관측 수 |
|------|-------------------|---------|
| 10Y-3M < 0 (역전) | **+20.9%** | 20 |
| 10Y-3M > 1.5%p (정상) | +4.5% | 18 |

역전 후 12개월은 대부분 주식 상승 구간이다. 침체는 역전 후 8-16개월에 오고, 시장은 이미 반영. 역전은 "지금 팔아라"가 아니라 "12-18개월 후에 대비하라"가 맞다.

### 자체 FCI 현재 상태

```
FCI = -0.55 (완화)
요소: 정책금리 -0.27, 장기금리 -0.51, 신용스프레드 -0.80, 주가 -2.00, 환율 +1.20
→ 주가 강세 + 스프레드 안정이 완화를 주도. 달러 강세만 긴축 방향.
```

### 기업집계 실측 (2021-2025, DART 2745종목)

| 연도 | 영업이익 합계 | YoY | Ponzi비율 | 부채비율 중간값 |
|------|-------------|-----|----------|-------------|
| 2021 | 108.5조 | — | 16.8% | 72.3% |
| 2022 | 105.4조 | -2.9% | 25.8% | 71.9% |
| 2023 | 72.8조 | **-30.9%** | 25.3% | 70.4% |
| 2024 | 100.9조 | +38.6% | 32.4% | 74.1% |
| 2025 | 81.2조 | -19.5% | **32.8%** | **88.6%** |

2023년 반도체 불황으로 이익 30% 급감. 2024년 회복했으나 2025년 재하락.
Ponzi비율 32.8% — **상장기업 3분의 1이 영업이익으로 이자를 감당 못 함**.
레버리지 88.6% — 2023년 대비 18%p 급등.

---

### Hamilton Regime Switching (2000-2024, 분기 GDP)

- 수렴: 17회, 0.14초 (maxIter=50)
- μ_expansion=3.01, μ_contraction=2.50
- 2001년 침체 구간: contraction 확률 평균 **99.7%**
- 2007년 GFC: 23.0% (분기 데이터 한계)

### 성능 (축별 호출 시간)

| 축 | 시간 | 비고 |
|---|---|---|
| 사이클 | 4.8s | FRED 6개 시리즈 |
| 금리 | 5.3s | FRED 9개 + Nelson-Siegel 8개 |
| 예측 | 7.5s | LEI + Hamilton EM + Kalman DFM |
| 종합 | 8.2s | 10축 + 40전략 + 포트폴리오 |
| 교역 | 0.4s | ECOS 5개 (KR) |

대부분 FRED/ECOS API 대기 시간. Hamilton EM 자체는 0.14초.

재현: `uv run python -X utf8 scripts/macro_backtest.py`

---

## 40개 투자전��

summary 축에서 40개 전략의 활성/비활성을 실시간 판별. 각 전략에 `strength`(0-1)과 `confidence`(high/medium/low).

### 경기순환 (6개): 1, 6, 7, 8, 9, 16
### 선행지수/교역조건 (7개): 5, 10, 11, 12, 14, 15, 31
### 금리/통화정책 (10개): 4, 17, 19, 20, 22, 28, 30, 34, 37, 40
### 환율/달러 (6개): 3, 23, 24, 25, 27, 38
### 물가/신용 (6개): 13, 18, 32, 33, 35, 36

상세: `core/finance/strategyRules.py` — `evaluateStrategies()` 함수.
ops 이전 버전에 40개 전략 전체 테이블이 있으므로, 여기서는 그룹만 명시.

---

## 코드 품질

| 지표 | 수치 |
|------|------|
| L2 모듈 | 12개 파일, ~2,400줄 |
| L0 순수함수 | 14개 파일, ~5,000줄 |
| 단위 테스트 | 38개 (test_macro_l0.py) |
| bare except (L2) | **0개** (구체적 예외 + logging) |
| bare except (_helpers) | 6개 (의도적 — httpx/Polars 포함 전체 포착, log.debug) |
| getDefaultGather 호출 | 8회 (24→8 최적화) |
| 공통 헬퍼 | 8개 (fetch_latest, fetch_yoy, collect_timeseries 등) |
| as_of 실제 동작 | 11/11축 |
| overrides 실제 동작 | 11/11축 |

---

## 관련 코드

| 경로 | 역할 |
|------|------|
| `src/dartlab/macro/` | 11축 + 종합 + 헬퍼 + spec |
| `src/dartlab/macro/_helpers.py` | 공통 fetch 헬퍼 8개 + as_of/overrides 지원 |
| `src/dartlab/core/finance/regimeSwitching.py` | 프로빗 + LEI + Sahm + Hamilton RS |
| `src/dartlab/core/finance/nowcast.py` | Kalman DFM Nowcasting |
| `src/dartlab/core/finance/yieldCurve.py` | Nelson-Siegel |
| `src/dartlab/core/finance/crisisDetector.py` | Credit-to-GDP + GHS + Minsky + Koo + Fisher |
| `src/dartlab/core/finance/macroCycle.py` | 사이클 + Cu/Au + BEI 분해 |
| `src/dartlab/core/finance/fci.py` | 자체 FCI (US + KR) |
| `src/dartlab/core/finance/inventoryCycle.py` | 재고순환 + ISM |
| `src/dartlab/core/finance/termsOfTrade.py` | 교역조건 |
| `src/dartlab/core/finance/corporateAggregate.py` | 기업집계 |
| `src/dartlab/core/finance/strategyRules.py` | 40개 전략 룰엔진 |
| `src/dartlab/core/finance/portfolioMapping.py` | regime → 자산배분 |
| `src/dartlab/core/finance/macroBacktest.py` | walk-forward 백테스트 |
| `src/dartlab/gather/fred/catalog.py` | FRED ~77개 시리즈 |
| `src/dartlab/gather/ecos/catalog.py` | ECOS ~53개 지표 |
| `src/dartlab/macro/report.py` | 경제분석 보고서 조립 (3막 서사) |
| `src/dartlab/macro/mbuilders.py` | macro dict → review Block 변환 |
| `src/dartlab/macro/mcatalog.py` | 보고서 섹션 메타데이터 |
| `src/dartlab/macro/charts.py` | macro ChartSpec 생성기 |
| `src/dartlab/macro/narrative.py` | 서사 자동 생성 (순환요약 + 막간전환) |
| `scripts/publish_macro_report.py` | 보고서 자동 발간 스크립트 |
| `.github/workflows/macroReport.yml` | 매월 자동 발간 GitHub Actions |
| `tests/test_macro_l0.py` | L0 단위 테스트 38개 |

---

## 경제분석 보고서

### 3막 서사 구조

analysis 6막이 기업 내부 인과(매출→마진→현금→부채→배분→가치)를 추적하듯,
macro 3막은 경제 외부 인과(성장→인플레→금리→신용→자산가격)를 추적한다.

```
신호등 대시보드 → 제1막(국면 진단) → 제2막(인과 역추적) → 제3막(전망+리스크) → 자산배분
```

| 막 | 핵심 질문 | 소비 축 |
|---|---|---|
| 신호등 | 한눈에 상태는? | summary 종합 점수 + FCI |
| 제1막 | 지금 어디인가? | cycle + rates + assets + sentiment |
| 제2막 | 왜 이 국면인가? | crisis + liquidity + corporate |
| 제3막 | 다음에 뭐가 오나? | forecast + crisis + trade |
| 배분 | 그래서 뭘 해야 하나? | allocation + strategies |

설계 원칙 (Goldman/BIS/IMF/Bridgewater/Bloomberg 참고):
- 결론 먼저 (Goldman 역피라미드)
- 전파 경로 명시 (BIS 전달 메커니즘)
- 비교 기준 명시 (Bloomberg: 전기 대비, 과거 유사 국면 대비)
- 매 섹션 "So What" (Bloomberg Intelligence)

### API

```python
dartlab.macro.report()                    # Rich 터미널
dartlab.macro.report(fmt="html")          # HTML
dartlab.macro.report(fmt="markdown")      # 마크다운
dartlab.macro.report(market="KR")         # 한국 경제
dartlab.macro.report(as_of="2022-01-01")  # 백테스트 시점 보고서
```

review의 Block/Section/Review 시스템을 그대로 재사용.
ChartBlock으로 viz 엔진 차트 포함.

### 자동 발간 파이프라인

```
매월 1일 → GitHub Actions (macroReport.yml)
  → secrets: FRED_API_KEY + ECOS_API_KEY
  → uv run python scripts/publish_macro_report.py
    → US 보고서 + KR 보고서 + 스냅샷 JSON
    → 전월 대비 diff (국면 전환/점수 급변 감지)
  → 성공: docs/macro-reports/ + blog/06-macro-reports/ 커밋 → GitHub Pages 배포
  → 실패: GitHub Issue 자동 생성 (labels: macro, automated, bug)
```

발간 경로:
- `docs/macro-reports/{YYYY-MM}-US.md` — docs (내부)
- `docs/macro-reports/{YYYY-MM}-KR.md` — docs (내부)
- `docs/macro-reports/snapshots/{YYYY-MM}.json` — 스냅샷 (diff용)
- `blog/06-macro-reports/{YYYY-MM}-us/index.md` — 블로그 (공개)
- `blog/06-macro-reports/{YYYY-MM}-kr/index.md` — 블로그 (공개)

### dartlab 3종 보고서 체계

| 보고서 | 엔진 | 구조 | 발간 | 블로그 카테고리 |
|--------|------|------|------|---------------|
| 기업분석 | review | 6막 인과 | audit 후 수동 | `05-company-reports` |
| 신용분석 | credit | 7축 등급 | publisher.py 수동 | `04-credit-reports` |
| **경제분석** | **macro** | **3막 서사** | **매월 자동 (Actions)** | **`06-macro-reports`** |
