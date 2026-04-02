# Quant (analysis 축)

주가 기술적 분석. gather("price") OHLCV를 소비하여 보조지표와 신호를 계산.
**analysis 엔진의 "quant" 그룹 축**으로 접근한다. 독립 엔진이 아님.

| 항목 | 내용 |
|------|------|
| 레이어 | L2 (analysis 하위) |
| 진입점 | `c.analysis("quant", "기술적분석")` |
| 소비 | gather/price (OHLCV), NumPy |
| 생산 | 25개 지표, 9개 신호, 종합 판단, 재무-기술적 괴리 진단 |
| 원본 | tradix 벡터화 엔진에서 이식 |

## 사용법

```python
import dartlab
c = dartlab.Company("005930")

c.analysis("quant", "기술적분석")      # 종합 판단 + 재무 괴리 진단
c.analysis("quant")                    # quant 그룹 가이드
```

## 지표 25개

### 추세 (7개)
| 지표 | 함수 | 기본값 |
|------|------|--------|
| SMA | vsma | 20, 60, 120 |
| EMA | vema | 12, 26 |
| MACD | vmacd | 12/26/9 |
| ADX | vadx | 14 |
| PSAR | vpsar | 0.02/0.02/0.2 |
| SuperTrend | vsupertrend | 10/3.0 |
| Ichimoku | (향후) | — |

### 모멘텀 (7개)
| 지표 | 함수 | 범위 |
|------|------|------|
| RSI | vrsi | 0~100 |
| Stochastic | vstochastic | 0~100 |
| ROC | vroc | % |
| Momentum | vmomentum | 절대값 |
| Williams %R | vwilliamsR | -100~0 |
| CCI | vcci | ±100 기준 |
| CMO | vcmo | -100~+100 |

### 변동성 (4개)
| 지표 | 함수 |
|------|------|
| Bollinger Bands | vbollinger |
| ATR | vatr |
| Keltner Channel | vkeltner |
| Donchian Channel | vdonchian |

### 거래량 (4개)
| 지표 | 함수 |
|------|------|
| OBV | vobv |
| MFI | vmfi |
| Force Index | vforceIndex |
| Elder Ray | velderRay |

## 신호 9개

| 신호 | 함수 | 반환 |
|------|------|------|
| 크로스오버 | vcrossover | +1 |
| 크로스언더 | vcrossunder | -1 |
| 양방향 | vcross | ±1 |
| 골든크로스 | vgoldenCross | ±1 |
| RSI 신호 | vrsiSignal | ±1 |
| MACD 신호 | vmacdSignal | ±1 |
| 볼린저 신호 | vbollingerSignal | ±1 |
| 채널 돌파 | vbreakoutSignal | ±1 |
| ADX 필터 | vTrendFilter | ±1 |

## 종합 판단

RSI 레벨(±2) + SMA20 추세(±1) + SMA60 추세(±1) = 점수 -4 ~ +4

| 점수 | 판단 |
|------|------|
| ≥ +2 | 강세 |
| -1 ~ +1 | 중립 |
| ≤ -2 | 약세 |

## 상대강도 + 베타

```python
c.analysis("quant", "기술적분석")            # verdict에 relativeStrength, beta 포함
c.analysis("quant", "기술적분석")  # beta는 결과 dict에 포함    # 베타 + CAPM 상세
```

### 상대강도 (Relative Strength)
- 종목 RSI - 시장(KOSPI) RSI
- 양수: 시장 대비 강세, 음수: 시장 대비 약세

### 실측 베타 (OLS)
- 종목 일간수익률 vs KOSPI 일간수익률 → OLS 회귀
- 반환: beta, alpha(연환산%), rSquared, nObs, capm(기대수익률%)
- CAPM: E(R) = Rf(3.5%) + β × MRP(6.5%)

### 시장 지수 수집
```python
dartlab.gather("price", "KOSPI")    # 코스피 지수 OHLCV (네이버)
dartlab.gather("price", "코스닥")   # 코스닥 지수
dartlab.gather("price", "KPI200")   # 코스피200
```

## 성능

- 지표 계산: 6.5ms / 종목 (순수 NumPy)
- 시장 지수 수집: 0.1초 (네이버 차트 API)
- 베타 계산: 1ms 미만 (OLS)
- 병목: 종목 주가 수집 1~3초 (네이버/야후 API)

## 설계 원칙

- 순수 NumPy — Polars/Pandas 의존 없음 (indicators.py, signals.py)
- gather에서 OHLCV 수집, quant에서 계산
- 시장 지수(KOSPI/KOSDAQ)는 네이버 차트 API 직접 수집
- scanner는 Company를 import하지 않는다 (역의존 방지)
- 향후 확장: 백테스트 엔진, 전략 빌더, 포트폴리오 최적화

## 관련 코드

| 경로 | 역할 |
|------|------|
| `src/dartlab/quant/__init__.py` | Quant 클래스 (진입점) |
| `src/dartlab/quant/indicators.py` | 45개 벡터화 지표 |
| `src/dartlab/quant/signals.py` | 9개 신호 발생기 |
| `src/dartlab/quant/analyzer.py` | 종합 분석 + 판단 + 상대강도 + 베타 |
