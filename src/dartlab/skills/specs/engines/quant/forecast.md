---
id: engines.quant.forecast
title: Quant Forecast — 가격 예측
category: engines
kind: curated
status: observed
purpose: Naive/AR(1)/ETS-Holt/Theta 기반 1~30 일 forecast. horizon 명시 + 경험적 예측밴드.
sourceRefs:
  - dartlab://skills/engines.quant.forecast
knowledgeRefs:
  - engines.quant
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: limited
  pyodide:
    status: limited
whenToUse:
  - short-term price forecast
  - horizon 1~30 days
  - Naive / AR(1) / ETS-Holt / Theta 합성
---

## 엔진 역할

`forecast` 축은 종목의 일별 수익률 시계열에 4 개의 numpy-only 모델 (Naive · AR(1) · ETS-Holt · Theta) 중 하나를 자동 선택해 fit 하고, horizon-step 후 점예측과 held-out one-step residual 분위수 기반 경험적 예측밴드를 산출한다. calibration residual은 expanding-window OOS 방식이지만, 누적 밴드는 `sqrt(h)` 휴리스틱이므로 유한표본 coverage를 보장하는 conformal interval이 아니다.

## 공개 호출 방식

```python
import dartlab

# 자동 dispatch (ADF p-value 기반)
r = dartlab.quant("예측", "005930", horizon=5)

# 명시 ensemble — 결과는 모델 평균
r = dartlab.quant("예측", "005930", horizon=10, models=["etsHolt", "theta"])

# US 종목 auto-detect
r = dartlab.quant("forecast", "AAPL", horizon=20)

# 회사 accessor
c = dartlab.Company("005930")
r = c.quant("예측", horizon=5)
```

## 호출 동작

`dartlab.quant("예측", stockCode, ...)` 가 dispatch 진입. 다음 순서로 진행:

1. stockCode → market auto-detect (KR 6 자리 vs US ticker)
2. OHLCV 시계열 수집 — 부족 시 error dict 반환
3. log-return 시계열 변환 + ADF p-value 계산
4. `_pickModel` 로 모델 선택 (아래 룰)
5. fit + horizon-step forecast 생성
6. expanding-window held-out residual 분위수로 명목 90% 경험적 밴드 산출
7. `forecastTable` + `summary` dict 반환

## 모델 dispatch 룰 (`_pickModel`)

1. `n < 60` → `naive` (데이터 부족 — drift 평균만 사용)
2. ADF p-value < 0.05 → `ar1` (평균회귀 시계열엔 ρ·y_prev 점추정이 정석. theta 는
   SES 가 마지막 점프에 끌려가 비현실 점추정을 낼 수 있어 자동 선택에서 제외 —
   cycle 1 dogfood 회귀 결과)
3. else → `etsHolt` (level + trend, no seasonality — Holt linear)

`models` 인자 명시 시 dispatch 무시하고 강제 사용 (1 개면 단일, 여러 개면 평균 ensemble).
Theta 는 명시 호출 (`models=["theta"]`) 시에만 사용. log-return 시계열은 거의 항상
stationary 라 theta 의 가정 (trend + 평균회귀 분해) 이 잘 맞지 않는다.

## 대표 반환 형태

```text
{
  "stockCode": "005930",
  "market": "KR",
  "lastClose": 75000.0,
  "lastDate": "2026-05-08",
  "modelChosen": "etsHolt",
  "modelsConsidered": ["etsHolt"],
  "horizon": 5,
  "nObs": 1006,                     # log-return 시계열 길이
  "calibSize": 201,                 # held-out one-step residual 개수
  "pAdfStationary": 0.4231,         # ADF p-value (dispatch 근거)
  "conformalHalfWidth": 0.018562,   # BC 필드: 일별 log-return 경험적 half-width
  "intervalMethod": "expandingWindowHeldoutResidualQuantile",
  "nominalLevel": 90.0,
  "coverageGuaranteed": false,
  "cumulativeBandMethod": "sqrtHHeuristic",
  "forecastTable": [
    {
      "horizon": 1,
      "pointForecast": 0.0012,      # 일별 log-return
      "lowerBound": -0.0174,
      "upperBound": 0.0198,
      "cumLogReturn": 0.0012,
      "cumLowerBound": -0.0174,
      "cumUpperBound": 0.0198,
      "pricePoint": 75090.0,        # last_close * exp(cum)
      "priceLower": 73708.0,
      "priceUpper": 76503.0
    },
    ...
  ],
  "summary": "etsHolt: +0.60% over 5d ([-3.55%, +4.75%] 90% empirical band; cumulative sqrt(h) heuristic)"
}
```

## evidence 기준

forecast 결과를 인용할 때 다음을 함께 명시:
- target: `stockCode`
- period: `lastDate` 와 `nObs`
- metric: `modelChosen`, `intervalMethod`, `nominalLevel`, `coverageGuaranteed`, `conformalHalfWidth`
- value: `forecastTable[h]` 의 점예측 + interval 쌍 (점예측만 X)
- dateRef: `lastDate` (전일 종가 기준)
- executionRef: 호출 캡처

## 자기 검증 노트

- 합성 uptrend (drift +0.0008/day, n=250) → ADF p > 0.05 → etsHolt 선택, cumLogReturn[5] > 0
- 합성 sideways (OU ρ=0.7) → ADF p < 0.05 → ar1 선택, |pointForecast| 작음
- 합성 downtrend → cumLogReturn[5] < 0
- 모든 horizon 에서 lowerBound < pointForecast < upperBound 순서 보장 (경험적 half-width ≥ 0)
- NaN/inf 출력 없음 — 데이터 부족 시 명시 error dict
- Cycle 1 회귀 (2026-05-09): 005930 실데이터에서 theta 가 +1.8%/day 비현실 점추정 →
  dispatch 룰을 ar1 로 변경. theta 는 명시 호출 시에만 사용 가능하도록 가드.

## walkForward 결합 (forecastRuleFactory)

forecast 모델을 walk-forward로 OOS 검증하려면 `forecastRuleFactory`를 `walkForward(ruleFactory=...)`에 전달:

```python
from dartlab.quant.benchmark.forecast import forecastRuleFactory
from dartlab.quant.strategy.backtest import walkForward

# Loose mode (default) — point only
factory = forecastRuleFactory(threshold=0.0005, models=["ar1"])
bt = walkForward(close, rule=None, ruleFactory=factory, train=180, test=30, step=30, nTrials=4)
# bt.validation["refit_count"] = fold마다 재학습 횟수
# bt.pbo                         = None (단일 candidate라 판정 불가)
# bt.dsr                         = 명시한 nTrials로 계산한 OOS Deflated Sharpe Ratio
```

### Entry / Exit 룰

**Loose mode (default)** — `requireConfidence=False`:
```
entry = pointForecast > threshold
exit  = pointForecast < -threshold
```

**Strict mode** — `requireConfidence=True`:
```
entry = pointForecast > threshold AND (point - halfWidth) > -threshold
exit  = pointForecast < -threshold OR (point + halfWidth) < -2*threshold
```

일별 log-return 의 경험적 half-width 는 일별 σ (~0.5~2%) 와 동급이라 strict 모드의 `lower > -threshold` 가 사실상 영원히 False다. entry 0이며 일별 단위에서 strict 는 권장 안 함. 누적 horizon 시그널 검증할 때만 쓴다.

### 검증된 성능 (2026-05-09 dogfood)

- 합성 strong trend (drift +0.3%/day, n=600): forecast loose `sharpe=+9.6, mdd=-1.8%, active=98%` vs 정적 SMA20/60 cross `sharpe=+5.2`
- 005930 KR 4 년 (n=1062): forecast loose `sharpe=+1.12 (thr=0.0005)` / `+0.97 (thr=0.001)` / `+0.87 (thr=0.002)` vs 정적 SMA cross `sharpe=+0.62`
- Sideways (drift=0): thr=0.002 시 active=0 (false positive 차단), thr=0.0005 시 active=48% sharpe=-0.83 (낮은 임계는 noise 들어감)

**threshold 가이드**: 일별 시계열 σ 의 5~10% 범위. 일반적 KR 종목 일별 σ ≈ 1-2% → threshold 0.0005-0.002 권장.

## 한계 및 비목표

- AutoARIMA / TBATS / SARIMA / GARCH-fit 가격 예측은 본 축 범위 밖 (base install SSOT 보존)
- 변동성 예측은 별도 축 `volatility` 의 `forecast=True` 옵션 사용
- 1 일~수십일 이내 단기 forecast 만 의미 있음. 장기 (>60 일) 누적 밴드는 `sqrt(h)` 휴리스틱 오차가 커짐
- `nominalLevel`은 경험적 분위수의 명목 수준이며 실제 coverage 보장이 아니다
- pointForecast 는 *기댓값* 이 아니라 *모델 점추정* — 시장 변동성·뉴스·이벤트 충격 미반영

## 기본 검증

스킬 변경 시 본 파일 + `engines.quant` SKILL.md 의 forecast 행 + `tests/test_quant_forecast.py` + `_AXIS_REGISTRY["forecast"]` 4 곳을 같은 변경에서 갱신한다.
