# Quant

주가 기술적 분석 엔진. gather("price") OHLCV를 소비하여 보조지표와 신호를 계산.

| 항목 | 내용 |
|------|------|
| 레이어 | L1 |
| 진입점 | `dartlab.quant()`, `c.quant()` |
| 소비 | gather/price (OHLCV), NumPy |
| 생산 | 25개 지표, 9개 신호, 종합 판단 |
| 원본 | tradix 벡터화 엔진에서 이식 |

## 사용법

```python
import dartlab

dartlab.quant("005930")                # 종합 판단 (강세/중립/약세)
dartlab.quant("005930", "indicators")  # 25개 지표 DataFrame

c = dartlab.Company("005930")
c.quant()                              # Company 연결
c.quant("indicators")                  # 지표 DataFrame
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

## 성능

- 지표 계산: 6.5ms / 종목 (순수 NumPy)
- 병목: 주가 수집 1~3초 (네이버/야후 API)

## 설계 원칙

- 순수 NumPy — Polars/Pandas 의존 없음 (indicators.py, signals.py)
- gather에서 OHLCV 수집, quant에서 계산, analysis에서 참조 가능
- scanner는 Company를 import하지 않는다 (역의존 방지)
- 향후 확장: 백테스트 엔진, 전략 빌더, 포트폴리오 최적화

## 관련 코드

| 경로 | 역할 |
|------|------|
| `src/dartlab/quant/__init__.py` | Quant 클래스 (진입점) |
| `src/dartlab/quant/indicators.py` | 25개 벡터화 지표 |
| `src/dartlab/quant/signals.py` | 9개 신호 발생기 |
| `src/dartlab/quant/analyzer.py` | 종합 분석 + 판단 |
