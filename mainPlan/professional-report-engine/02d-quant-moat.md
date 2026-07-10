# 02d · 능력 격상 — 정량 해자 (quantitative moat)

> 출처: 경제적 해자/경쟁우위 측정 전문가 조사(Mauboussin·Greenwald·Damodaran). 코드 직독 file:line 증거 기반. 01 능력 원장에서 "경쟁/해자(정량 moat) = 🔴 정성 엔진 부재"로 flag 된 항목의 정공법 격상안.
>
> **사상**: 정직 스킵 = 능력부족(00 §1). 그러나 "이 회사는 강한 브랜드 해자가 있다"식 정성 산문 = 환각(00 §9 — 금지). 프로의 길은 회사가 *이미 보유한* 시계열에서 **측정 가능한** 해자 평가를 산출하는 것 — ROIC 지속성·초과수익 내구성·사이클 관통 마진 안정성·점유율 궤적·재투자 회수율. 이건 분석이지 날조가 아니다.

---

## 0. 결론 먼저 (verdict)

**빌드 가능 — 벽이 아니다.** 정량 해자 점수의 입력 시계열은 dartlab 에 **이미 라이브로 존재**한다 (ROIC-WACC 스프레드 시계열·5단계 마진 시계열·동종 백분위 분포·재투자 회수율·자산회전). 현존 `calcMoatProxy`(`intrinsic.py:113`)는 **5y avg 단일 스칼라 + 하드코딩 WACC 8%** 의 아마추어 proxy — 지속성·내구성·안정성을 측정 못 한다. 격상 = 새 데이터 창조가 아니라 **흩어진 시계열을 Mauboussin/Greenwald 표준 컴포넌트로 묶고, 정성 환각 없이 measurable 경계를 명시**하는 일.

단 하나의 진짜 벽: **switching cost·network effect·brand 같은 정성 해자 원천은 공시에서 직접 측정 불가** — 정량 내구성 지표로 *근사*하거나 "미측정"으로 명시한다(§3). 이 경계를 흐리는 순간 환각이 된다.

---

## 1. Substrate inventory — 무엇이 시계열로 있는가

### 1.1 🟢 라이브 — 그대로 컴포넌트가 됨

| 입력 시계열 | SSOT (file:line) | 반환 키 | 해자 컴포넌트로 |
|---|---|---|---|
| **ROIC 시계열 + WACC 스프레드** | `analysis/financial/_investmentAnalysisRoic.py:107` `calcRoicTimeline` | `history[].roic`, `history[].spread`, `history[].waccEstimate` | **초과수익 지속성·내구성의 1차 입력** (핵심) |
| WACC 회사별 추정 | `_investmentAnalysisRoic.py:28` `_estimateWacc` | float (CAPM, beta·시총 반영) | spread = ROIC − WACC 의 분모. **하드코딩 8% 졸업** |
| Damodaran Excess Return 분해 | `core/utils/calc.py:52` `decomposeRoic` | `excessReturnPct`, `excessReturnAbs`, `operatingMargin`, `assetTurnover`, `dominantDriver` | 초과수익 절대규모 + margin/turnover 원천 |
| EVA 시계열 (절대 초과수익) | `analysis/financial/_investmentAnalysisEva.py:22` `calcEvaTimeline` | `history[].eva`, `nopatReturn` | 초과수익 절대값 추이 (Stern Stewart) |
| **5단계 마진 시계열** | `analysis/financial/profitability.py:55` `calcMarginTrend` | `history[].grossMargin`, `operatingMargin`, `netMargin` (+ YoY) | **사이클 관통 마진 안정성(CV)의 입력** |
| 듀퐁 5요소 (자산회전·레버리지) | `profitability.py:245` `calcReturnTrend` | `history[].assetTurnover`, `leverage`, `roe` | 자본집약/장벽 proxy + 회전 안정성 |
| **재투자율 + CAPEX/매출** | `analysis/financial/_capitalAllocationReinvest.py:19` `calcReinvestment` | `history[].capexToRevenue`, `retentionRate` | **증분 ROIC(재투자 회수율) 입력** |
| FCF 사용처 (잔여=war chest) | `_capitalAllocationReinvest.py:127` `calcFcfUsage` | `history[].residual`, `fcf` | 재투자 runway 보조 |
| 투자 강도 (CAPEX·무형비율) | `_investmentAnalysisRoic.py:321` `calcInvestmentIntensity` | `capexToRevenue`, `intangibleRatio`, `tangibleRatio` | 자본집약 장벽 proxy |
| **동종 백분위 분포** (OPM/ROE/CAGR) | `industry/calcs/companyCalcs.py:209` `calcSectorMetrics` | `myOpmPercentile`, `myRoePercentile`, `opmDistribution{p10..p90}` | **상대 우위(업종 내 위치) 입력** |
| 가치사슬 위치 + peers | `companyCalcs.py:12` `calcChainPosition` | `stage`, `stream`, `peers[]` | 비교 유니버스 정의 |
| **산업 집중도 HHI/CR3** | `industry/calcs/concentration.py:333` `calcIndustryConcentration` | `hhi`, `top3Ratio`, `hhiRisk`, `topN[]` | 시장구조(과점=장벽) proxy |
| 공급망 집중도 HHI | `concentration.py:202` `calcSupplyInsights` | `hhi`, `top1Ratio`, `top3Ratio` | 협상력 proxy (보조) |

### 1.2 🟡 부분 — 시계열이 얕거나 횡단면뿐

| 입력 | 한계 | 영향 |
|---|---|---|
| **시장 점유율 궤적** | `calcSectorMetrics` 는 **단일 최신 연도 횡단면 백분위**만. 점유율 *추세*(gaining/defending/losing) 시계열은 미산출 | 점유율 궤적 = ROIC 시계열의 회사별 매출 share 를 panel 에서 **직접 합성**해야 (§4) — 새 산출이지만 raw 는 scan/panel 에 존재 |
| 업종 사이클 phase | `companyCalcs.py:353` `calcSectorCycle` — 현재 단일연도(confidence 0.5). docstring 자인 "scan finance.parquet 연도별 history 채워지면 시계열 활성" | 마진 안정성은 회사 자체 `calcMarginTrend` 시계열로 충분 — 사이클 phase 는 보조 |
| ROIC history 길이 | `_MAX_YEARS = 8` (`_investmentAnalysisRoic.py:12`). 실제 DART 패널은 보통 5~8년 | 지속성(연속 양수 햇수) 측정에 **충분**. 단 "전체 사이클 관통" 주장은 데이터 길이 명시 필요 |

### 1.3 🔴 미보유 — 진짜 벽 (정성 해자 원천)

| 미측정 차원 | 왜 공시에서 불가 | 처리 |
|---|---|---|
| **Switching cost** | 고객 이탈률·계약 lock-in 은 미공시 | 마진 안정성(낮은 CV) + ROIC 내구성으로 *간접 신호* — "측정 아닌 근사" 명시 |
| **Network effect** | 사용자수·양면시장 데이터 미공시 | 측정 불가 — `unmeasured` 명시. 매출 가속+마진 유지 동반은 *약한 정황*일 뿐 |
| **Brand / intangible** | 브랜드 가치는 BS 영업권(피인수 시만)·무형비율로만 보임 | `intangibleRatio` 는 M&A 신호이지 brand 가 아님 — 혼동 금지(§3) |
| **규제 면허·특허 폭** | 텍스트 공시, 정량화 불가 | 미측정. (특허 *건수*는 별 의미 없음) |

---

## 2. 정량 해자 method — 컴포넌트 + dartlab 필드 + 등급 합성

> 설계 원칙: 블랙박스 금지(00 §4 verdict noComposite 와 정합 — moat 등급은 *컴포넌트를 보여주는 진단*이지 단일 합성점수 아님). 각 컴포넌트는 **값 + 증거 + 측정/미측정 라벨**을 함께 emit. Mauboussin "Measuring the Moat"(2016) + Greenwald "Competition Demystified" + Damodaran 의 ROIC-WACC fade 골격.

### C1. 초과수익 지속성 (excessReturnPersistence) — *핵심, Mauboussin 1번 지표*

ROIC−WACC 스프레드의 **레벨 × 내구성**. 해자의 정의 = "초과수익을 *얼마나 오래* 방어하는가".

```
입력: calcRoicTimeline(c)["history"][].spread   (= roic − waccEstimate)
산출:
  spreadLatest        : 최신 spread (%p)
  spreadMean          : N년 평균 spread (%p)
  positiveYears       : spread > 0 연속 햇수 (history 최신→과거 순회)
  positiveRatio       : spread > 0 비율 (양수기간 / 전체기간)
  spreadTrend         : 선형 기울기 부호 (widening / stable / narrowing)
  spreadVolatility    : spread 표준편차 (낮을수록 방어 견고)
판정 기여:
  지속 고스프레드(mean ≥ 5%p AND positiveRatio ≥ 0.8) = 강한 해자 증거
  변동 큰/축소 추세 = 해자 침식 신호
```

### C2. 사이클 관통 마진 안정성 (marginStability) — *Greenwald 가격결정력*

총·영업마진의 **변동계수(CV) + 레벨**. 낮은 CV + 높은 레벨 = 가격결정력(원가 전가·수요 비탄력) = 해자.

```
입력: calcMarginTrend(c)["history"][].grossMargin / .operatingMargin
산출:
  opMarginMean, opMarginCV   (CV = std/mean, 낮을수록 안정)
  grossMarginMean, grossMarginCV
  marginFloor                : 최저 연도 마진 (불황기 방어선)
  marginCompression          : peak−trough 낙폭 (%p)
판정 기여:
  opMarginCV ≤ 0.15 AND opMarginMean ≥ 업종 median = 가격결정력 증거
  높은 CV = cyclical/commodity = 해자 약함 (사이클 기업 정직 인정)
주의: 금융업은 calcMarginTrend 가 금융이익 기준 — isFinancial 분기 존중(profitability.py:121)
```

### C3. 상대 우위 + 점유율 궤적 (relativePosition) — *업종 내 위치*

```
입력(레벨): calcSectorMetrics(c) → myOpmPercentile / myRoePercentile
입력(구조): calcIndustryConcentration(industryId) → hhi / top3Ratio
입력(궤적): §4 신규 calcMarketShareTrend — panel 매출 share 시계열
산출:
  opmPercentile, roePercentile  : 동종 분포 내 위치 (높을수록 우위)
  industryHHI, industryStructure: 과점(집중)일수록 신규진입 장벽
  shareTrajectory               : "gaining" | "defending" | "losing" (3년 share 기울기)
판정 기여:
  상위 사분위(percentile ≥ 75) + 점유율 방어/확대 = 우위 지속
  과점 시장(HHI ≥ 2500)에서 상위 = 구조적 장벽
```

### C4. 재투자 경제성 (reinvestmentEconomics) — *증분 ROIC, 성장이 가치증가인가*

성장이 *가치 창출형*인지: 재투자된 자본의 증분 수익률.

```
입력: calcRoicTimeline(c)["history"][].nopat / .investedCapital
산출:
  incrementalRoic  : ΔNOPAT(t,t-k) / ΔInvestedCapital(t,t-k)  (k=3 권장, 노이즈 완화)
  reinvestmentRate : calcReinvestment → capexToRevenue / retentionRate
  growthQuality    : incrementalRoic vs waccEstimate 비교
판정 기여:
  incrementalRoic > WACC = 성장이 가치 증가 (해자 있는 성장)
  incrementalRoic < WACC AND 높은 재투자 = 가치 파괴 성장 (해자 없음·경계)
주의: ΔIC 가 음수/극소면 incrementalRoic 불안정 → None 처리 + "재투자 미미" 라벨
```

### C5. 자본집약 장벽 proxy (capitalBarriers) — *보조*

```
입력: calcReturnTrend → assetTurnover 시계열 / calcInvestmentIntensity → capexToRevenue
산출:
  assetTurnoverMean, assetTurnoverStability(CV)
  capexIntensityMean
판정 기여(약): 높고 안정적인 capex intensity = 신규 진입에 대규모 선투자 필요(장벽)
            단 자본집약 ≠ 해자 (commodity 도 자본집약) → 보조 신호로만, 단독 판정 금지
```

### 등급 합성 (composeMoatRating) — 블랙박스 아님

```
입력: C1~C5 컴포넌트 dict
규칙(투명·결정론):
  wide   : C1(mean spread ≥ 5%p AND positiveRatio ≥ 0.8)
           AND C2(opMarginCV ≤ 0.20)
           AND C3(percentile ≥ 60)
  narrow : C1(mean spread ≥ 0 AND positiveRatio ≥ 0.5) — 초과수익 있으나 내구성/안정성 1개 미달
  none   : mean spread < 0 OR positiveRatio < 0.5 (자본비용 미회수)
출력:
  rating          : "wide" | "narrow" | "none"
  components       : {C1..C5 각 값 + 측정/미측정 라벨}
  evidence         : 각 컴포넌트가 인용한 history period + 수치 (evidenceRef 결박)
  unmeasured       : ["switchingCost", "networkEffect", "brand"] — 명시적 미측정 목록
  confidence       : historyYears / 8 (데이터 길이 기반, 짧으면 보수적)
  noComposite      : true  (단일 0~100 점수 금지 — verdict 블록 규약과 정합)
```

핵심: **rating 은 컴포넌트 게이트의 논리곱이지 가중평균 점수가 아니다.** "wide 78점" 같은 인플레 점수(`feedback_plan_score_not_signature`) 금지 — 각 게이트 통과/미달을 보여준다.

---

## 3. Measurable vs honest-unmeasured 경계 (정직선)

| 차원 | 측정 가능? | dartlab 방법 | 정직 한계 |
|---|---|---|---|
| 초과수익 지속성 | ✅ 직접 | C1: ROIC−WACC 시계열 | WACC 는 *추정*(CAPM beta) — 회사별이나 점추정. spread ±2%p 밴드로 해석 |
| 마진 안정성/가격결정력 | ✅ 직접 | C2: 마진 CV | "가격결정력"은 마진 안정의 *해석* — 비용구조 개선과 구분 불가(단, drivers 분해로 일부 분리) |
| 업종 내 상대 우위 | ✅ 직접 | C3: 백분위 | peerCount 작으면(< 5) 분포 신뢰 약함 — confidence 하향 |
| 시장구조 장벽 | 🟡 근사 | C3: HHI | 집중≠해자 (담합·규제일 수도). 구조적 정황일 뿐 |
| 점유율 궤적 | 🟡 합성 | §4 신규 (panel share) | 비상장 경쟁사 매출 누락 시 share 과대 — 유니버스 명시 필수 |
| 재투자 회수율 | ✅ 직접 | C4: 증분 ROIC | ΔIC 노이즈 — k=3 평활 + 음수 IC None 처리 |
| 자본 장벽 | 🟡 약근사 | C5: capex intensity | commodity 도 자본집약 → 단독 판정 금지 |
| **Switching cost** | ❌ 미측정 | (마진 안정으로 *간접 정황*) | **"측정 아닌 정황"** 명시. 직접 수치 없음 |
| **Network effect** | ❌ 미측정 | 없음 | `unmeasured` 명시. 환각 금지 |
| **Brand** | ❌ 미측정 | (intangibleRatio 는 M&A 신호이지 brand 아님) | 혼동 금지 — 영업권 ≠ 브랜드가치 |
| 규제·특허 폭 | ❌ 미측정 | 없음 | `unmeasured` 명시 |

**프로의 핵심**: 측정 가능한 것(C1~C4)은 엄밀히 측정하고, 측정 불가(switching/network/brand)는 `unmeasured` 배열로 *명시적으로 비워둔다*. "삼성전자는 강한 브랜드 해자" 같은 정성 산문은 절대 emit 하지 않는다 — 대신 "ROIC 18%로 WACC 6%p 상회를 7년 연속 방어, 영업마진 CV 0.12 (가격결정력 정황), 단 switching cost·network effect 는 공시 미측정"이라고 쓴다.

---

## 4. Concrete build — L계층 준수 신규 모듈 + 함수

### 4.1 위치 (L2 analysis, find-SSOT-improve)

신규 파일 `src/dartlab/analysis/financial/moat.py` (L2 analysis engine). 기존 `_investmentAnalysisRoic`·`profitability`·`industry/calcs` 결과를 **소비**할 뿐 재계산하지 않음 → 병렬 빌드 아님(`feedback_common_workbench_ssot` 정합). `intrinsic.py:113 calcMoatProxy` 는 **deprecate**(dashboard 간이 카드용 — 신규 `calcMoatScore` 가 대체, intrinsic 은 thin re-export 로 유지하되 신규는 timeline 기반).

⛔ L계층 가드: L2 analysis 는 L2 industry 를 **직접 import 금지**(L2↔L2 cross 0건 CI 강제). C3 의 industry 입력은 `calcSectorDynamics` 가 macroPhase 를 외부 주입받는 패턴(`companyCalcs.py:475`)과 동일하게 — **moat.py 는 industry 결과를 인자로 받고, 호출자(story L3)가 industry 호출 후 주입**한다. 또는 `analysis._run` 이 조립 시 industry 블록을 합성.

### 4.2 함수 (전부 dict 반환 순수함수, @memoizedCalc)

```python
# src/dartlab/analysis/financial/moat.py

@memoizedCalc
def calcExcessReturnPersistence(company, *, basePeriod=None) -> dict | None:
    """C1 — ROIC−WACC spread 의 레벨·연속성·추세·변동성.
    입력: calcRoicTimeline(company) 의 history[].spread.
    반환: {spreadLatest, spreadMean, positiveYears, positiveRatio,
           spreadTrend, spreadVolatility, historyYears, evidence[]}"""

@memoizedCalc
def calcMarginStability(company, *, basePeriod=None) -> dict | None:
    """C2 — 총·영업마진 CV + 레벨 + 불황기 방어선.
    입력: calcMarginTrend(company) 의 history[].operatingMargin/grossMargin.
    반환: {opMarginMean, opMarginCV, grossMarginCV, marginFloor,
           marginCompression, isFinancial, evidence[]}"""

@memoizedCalc
def calcReinvestmentEconomics(company, *, basePeriod=None) -> dict | None:
    """C4 — 증분 ROIC vs WACC (k=3 평활).
    입력: calcRoicTimeline (nopat·investedCapital) + calcReinvestment.
    반환: {incrementalRoic, reinvestmentRate, growthQuality('accretive'|
           'dilutive'|'minimal'), waccEstimate, evidence[]}"""

@memoizedCalc
def calcCapitalBarriers(company, *, basePeriod=None) -> dict | None:
    """C5(보조) — assetTurnover/capex intensity 레벨·안정성.
    입력: calcReturnTrend + calcInvestmentIntensity."""

def calcMarketShareTrend(company, *, peerCodes=None, basePeriod=None) -> dict | None:
    """C3 궤적(신규 합성) — panel 매출 share 3년 추세.
    입력: company.select('IS',['매출액']) 시계열 + peerCodes 의 동일 시계열.
    peerCodes 는 호출자(L3)가 calcChainPosition().peers 에서 주입 (L2↔L2 회피).
    반환: {shareLatest, shareTrend('gaining'|'defending'|'losing'),
           shareSlope, universeNote(상장사 한정 명시), evidence[]}"""

def composeMoatRating(company, *, sectorMetrics=None, industryConc=None,
                      peerCodes=None, basePeriod=None) -> dict | None:
    """등급 합성 — C1~C5 게이트 논리곱. sectorMetrics/industryConc/peerCodes 는
    L3 가 industry 엔진 호출 후 주입(L2↔L2 cross 가드).
    반환: {rating('wide'|'narrow'|'none'), components{C1..C5},
           evidence[], unmeasured[], confidence, noComposite:True}"""

def calcMoatFlags(company, *, basePeriod=None) -> list[str]:
    """해자 침식/강화 1줄 플래그 (calcInvestmentFlags 패턴).
    예: 'ROIC−WACC 스프레드 3년 연속 축소 — 해자 침식 신호'"""
```

### 4.3 헬퍼 (재사용 — 신설 최소화)

- CV·기울기·연속햇수: 신규 `_seriesStats(values)` (moat.py 내부) — 5줄, `companyCalcs._distribution` 과 별개(저 함수는 횡단면 백분위용).
- WACC: `_estimateWacc` 재사용 (`_investmentAnalysisRoic.py:28`) — 신규 추정 금지.
- Excess return 절대값: `decomposeRoic` 재사용 (`calc.py:52`).

### 4.4 등록 (axis registry)

신규 축 `"경쟁우위"` (group="financial", partId="6-x", alias `moat`/`competitivePosition`) 를 `_registryAxesA.py` `_AXES_A` 에 `_AxisEntry` 로 추가 + `_GROUPS["financial"]` 리스트 + `_ALIASES` (`_registry.py:17,48`). calcs 튜플 = 위 7함수의 `_CalcEntry`. **engine-add 절차 불요**(새 엔진 아님 — 기존 analysis 축 추가). docstring 9섹션 + camelCase + L계층 import 가드만.

⛔ 빌드/베이크 0 — 전부 런타임 `company.select`·기존 calc 직독(런타임-SSOT 강행규칙 정합). 사전계산 parquet 신설 금지.

---

## 5. Cohort validation / graduation gate

> 00 §10·§8 — 미검증 확신 금지. moat 점수는 **백테스트로 의미를 증명한 뒤** 리포트에 탑재한다. "약하게 추정하고 단정"(`feedback_plan_score_not_signature`)이 operator 가 가장 싫어하는 형태.

### G1. Mean-reversion resistance cohort backtest (핵심 졸업 조건)

해자 이론의 검증 가능한 예측: **고해자 코호트는 ROIC 평균회귀에 저항한다** (Mauboussin 의 ROIC fade 곡선 — wide-moat 기업은 fade 가 느리다).

```
설계:
  1. 기준연도 T (panel 가용 범위). 전상장사 유니버스(scan SSOT).
  2. T 시점 composeMoatRating 으로 wide / narrow / none 3코호트 분류.
     (T 시점 데이터만 사용 — look-ahead 차단)
  3. 각 코호트의 T → T+1..T+k ROIC−WACC spread 궤적 추적.
  4. 검증 가설:
     H1 (지속성): wide 코호트의 spread 가 T+k 까지 유의하게 > none 코호트.
     H2 (저항): wide 코호트의 ROIC fade 기울기 < none 코호트 (덜 평균회귀).
     H3 (마진): wide 코호트의 후속 마진 CV < none 코호트.
  5. 통과 기준(★로버스트 필수): wide−none 의 T+k **중앙값** spread 차이가 0 초과 AND
     winsorized(5/95) 평균 차이가 0 초과 AND wide 중앙값 > 0.
     효과크기 + 표본수 + 코호트별 양(+)비율 동반 보고 (p-hacking 회피).
```

> ⛔ **원평균(raw mean) 을 통과 기준으로 쓰지 말 것 (2026-07-06 실측 근거).** `ROIC = NOPAT / 투하자본`
> 이라 투하자본이 0 에 가까운 회사에서 ROIC 가 폭발한다. 전 유니버스 실측에서 `none` 코호트 **원평균
> 66.8%** 가 `wide` **37.1%** 를 앞질러 게이트가 **FAIL 로 오판**됐다. 같은 표본의 **중앙값은 wide
> +7.63% vs none −6.01%**, 양(+)비율 70% vs 26% 로 가설이 명백히 지지된다. 따라서 판정은 중앙값 +
> winsorized 평균으로만 한다.
>
> **실측 결과 (지시적 PASS)**: 형성 2021~2023 · 성과 2025(T+2), 유효 1,071 사 → wide(n=73) median
> +7.63% vs none(n=806) −6.01%. 형성 2021~2022 · 성과 2025(T+3), 유효 1,432 사 → wide(n=133)
> +2.72% vs none(n=1,020) −6.16%. 두 구성 모두 로버스트 기준 통과.
> 한계: WACC 전사공통 8.5%·세율 22% 고정 근사(엔진 정합 아님) · 벌크 연간 지평 5 년(2021~2025)이라
> "형성 3 년 + T+3"(6 년 필요) 동시 충족 불가 · 생존 편향. 상세 = `tests/_attempts/quantMoat/README.md`.
>
> **데이터 경로**: per-Company(`Company(code).select`)가 아니라 **벌크 직독**
> (`data/dart/scan/finance.parquet`, 2,799 종목 × 연간 2021~2025, `buildFinanceJson` 계정 매핑 동형).
> 엔진 정합 WACC 는 `_estimateWacc` 이 회사당 시총·베타를 네트워크로 개별 fetch(~2.6s)하는 구조라
> 유니버스 실행이 막힌다 → 가격 벌크(`data/gov/prices`, `data/krx/prices`) 직독 전환이 선행 과제.

거처: `tests/_attempts/quantMoat/` (졸업 게이트 — `feedback_attempts_graduation_gate`). 백테스트 데모(결과 docstring + README) 통과 후에야 `src/dartlab/analysis/financial/moat.py` 본진 배치. **순서**: ① _attempts 개념확립(코호트 분리 시그널 실측) → ② 모듈화 → ③ 데모 → ④ 클린코드 → ⑤ 9섹션 docstring → ⑥ 본진 + axis 등록.

### G2. Discriminant 검증 (음성 통제)

- **commodity 함정**: 철강·정유(높은 자산회전·낮은 마진 안정)가 none 으로 분류되는지. wide 로 새면 C2 임계 잘못.
- **레버리지 가짜우위**: 고ROE인데 고레버리지(`calcReturnTrend.leverage > 3`)는 ROIC 기반이라 자동 배제되는지 확인(ROE 아닌 ROIC 사용 = 설계 의도).
- **금융업**: isFinancial 분기로 마진 컴포넌트 자동 완화되는지(`profitability.py:121`).

### G3. 알려진 케이스 sanity (코드 검증 아닌 도메인)

KOSPI 대형주 중 직관적 wide(고ROIC·안정마진 소비재/플랫폼) vs none(시클리컬·적자전환)이 등급과 일치하는지 수동 눈검수 5~10사. 불일치 시 임계·컴포넌트 재조정(점수 맞추기 아님 — 분류 논리 점검).

---

## 6. Integration — 리포트 경쟁위치 섹션 + thesis 기둥

### 6.1 서사 아크 §[6] 경쟁위치 (00 §3)

PRD 아크 `[6] 경쟁위치 — peer 백분위·정량 moat·life-cycle` 의 **moat 컴포넌트**가 본 엔진. story L3 builder 가:
```
1. calcChainPosition(c) → peers, industryId  (industry 엔진, L3 가 호출)
2. calcSectorMetrics(c) / calcIndustryConcentration(industryId)  (industry 엔진)
3. composeMoatRating(c, sectorMetrics=…, industryConc=…, peerCodes=peers)  (analysis moat — 주입)
4. exhibit: ROIC−WACC spread 시계열 차트(MiniFinChart SSOT) + 마진 CV + 백분위 산점도
5. verdict 블록: rating + 컴포넌트 게이트 표 + unmeasured 명시 (noComposite:true)
```

### 6.2 Thesis 지지기둥 (00 §4)

해자 평가는 thesis 의 **검증가능 인과 기둥**이 된다:
- 중심논거 예: "ROIC 18%로 WACC 12%를 6%p 상회, 7년 연속 방어(positiveRatio 1.0) → 자본이 지속적 가치 창출" (형용사 아닌 메커니즘).
- 약세론(반증) 직결: "이 논지를 깨는 단 하나 = ROIC−WACC 스프레드 추세가 narrowing 으로 전환(C1 spreadTrend) 또는 마진 CV 급등" — moat 컴포넌트가 *관점전환 트리거*를 정량 제공.
- evidenceRef: 각 컴포넌트의 `evidence[]` 가 인용한 재무 period·수치 결박.

### 6.3 밸류에이션 연결 (02·A terminal fade)

01 §4 결함4 "Terminal fade 없음(ROIC>WACC 영원 가정)". moat 의 **C1 지속성·C4 증분ROIC** 가 DCF terminal fade 기간을 *근거 있게* 결정: wide=긴 fade(초과수익 오래 방어), none=즉시 WACC 수렴. moat 가 valuation 의 가정을 먹인다(아크 [6]→[7] transition).

### 6.4 UI/계약

신규 verdict 변형 아닌 기존 `verdict(noComposite:true)` + `exhibit` 블록 재사용(00 §7 — 어휘 추가 불요). 차트 전부 MiniFinChart SSOT 위임. 정직 스킵 렌더(미측정 차원은 빈칸 시각화 + "공시 미측정" 라벨) — 01 §5 강함 그대로.

---

## 7. Risks — 빌드 가능성 verdict + 함정

| # | 리스크 | 처리 |
|---|---|---|
| R1 | **WACC 추정 노이즈** — `_estimateWacc` 가 외부 API(beta·시총) 의존, 콜드/실패 시 None | spread None 처리 + C1 은 ROIC 절대레벨 fallback. spread 인용 시 추정 명시 |
| R2 | **점유율 궤적 유니버스** — 비상장 경쟁사 매출 누락 → share 과대 | `universeNote` 로 "상장사 한정" 명시. shareTrend 는 *추세*만 신뢰(절대 share 보수적) |
| R3 | **정성 환각 재유입** — LLM 이 정량 등급에 "브랜드 강력" 산문 덧칠 | unmeasured[] 를 출력에 강제 포함 + story 어휘에 정성 moat 산문 금지 가드(00 §9 정합). untrusted-wrap 과 별개의 *자기 출력* 규율 |
| R4 | **L2↔L2 cross** — moat 가 industry 직접 import 시 CI red | 인자 주입 패턴(§4.1, `calcSectorDynamics` 선례) 강제 — 설계로 차단 |
| R5 | **코호트 backtest look-ahead** — T 분류에 T+ 데이터 누설 | basePeriod 로 T 시점 고정 + panel rcept window 가드(`incident_panel_rcept_window_gap`) |
| R6 | **commodity 오분류** | G2 음성통제 — C2 임계가 시클리컬을 none 으로 거르는지 백테스트 검증 후 탑재 |
| R7 | **history 길이 부족**(신규상장·결측) | confidence = historyYears/8, < 3년이면 rating="insufficient" + 정직 스킵 렌더 |

### Verdict

**빌드 가능. 벽이 아니다 — 단, 측정 가능한 차원에 한해.** C1~C4(초과수익 지속성·마진 안정성·상대 우위·재투자 경제성)는 dartlab 라이브 시계열로 *직접* 측정되며 Mauboussin/Greenwald 표준에 정합한다. C3 점유율 궤적만 panel 합성 신규(raw 는 존재). 진짜 벽 = switching/network/brand 정성 원천 — 이건 측정 불가를 **명시**하는 게 프로의 길이지, 정성 산문으로 메우면 환각이다. 격상의 본질 = 흩어진 시계열을 투명한 게이트로 묶고, `calcMoatProxy`(8% 하드코딩 스칼라)를 시계열 기반 등급으로 졸업시키고, **코호트 mean-reversion backtest(G1)로 의미를 증명한 뒤** 리포트 아크 [6]·thesis 기둥·valuation fade 에 배선하는 것. 검증 전 탑재 금지.
