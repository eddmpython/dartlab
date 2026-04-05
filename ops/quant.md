# Quant

종목 레벨 정량분석 엔진. 기술적 지표부터 팩터 모델, 텍스트 감성, 포트폴리오 최적화까지.

| 항목 | 내용 |
|------|------|
| 레이어 | L1 |
| 진입점 | `dartlab.quant("축명", "종목코드")` |
| 소비 | gather(price, flow), scan 프리빌드 parquet, docs/changes parquet |
| 생산 | ai(L3)가 정량 판단에 소비, review가 기술적 섹션에 소비 |
| 축 | 29축 7그룹 |

## 설계 원칙

- **축 기반 디스패치** — macro/scan과 동일 패턴 (`_AXIS_REGISTRY` + `_ALIASES` + lazy import)
- **numpy 전용** — GARCH, HMM, HRP 전부 numpy 직접 구현. 외부 통계 라이브러리 0
- **DART/EDGAR 동시 지원** — market="auto" (6자리=KR, 알파벳=US)
- **메모리 안전** — scan parquet은 lazy scan, 포트폴리오는 순차 OHLCV 로드
- **analysis(L2) import 금지** — 펀더멘털 데이터는 scan 프리빌드 경유

## API

```python
import dartlab

# 가이드
dartlab.quant()                                # 29축 카탈로그

# 단일 종목 (축 + 종목코드)
dartlab.quant("모멘텀", "005930")              # 모멘텀 분석
dartlab.quant("momentum", "005930")            # 영문 키
dartlab.quant("변동성", "AAPL")               # EDGAR 종목
dartlab.quant("꼬리위험", "005930")            # CVaR, 최대낙폭, Sortino

# 횡단면 (종목 불필요)
dartlab.quant("순위")                          # 멀티팩터 복합 순위
dartlab.quant("스크린")                        # 팩터 스크리닝

# 포트폴리오 (종목 리스트)
dartlab.quant("평균분산", ["005930","000660"])  # Markowitz

# accessor 패턴
dartlab.quant.momentum("005930")
dartlab.quant.verdict("005930")
```

## 축 체계 (7그룹 29축)

### A. 기술적 (technical) — 가격 전용

| 축 | key | 설명 | 상태 |
|---|---|---|---|
| 지표 | indicators | 45개 기술적 지표 DataFrame | 구현 |
| 신호 | signals | 9개 매매 신호 | 구현 |
| 판단 | verdict | 강세/중립/약세 종합 판단 | 구현 |
| 모멘텀 | momentum | 12-1개월 횡단면, 시계열, 52주 신고가 | 구현 |
| 변동성 | volatility | GARCH(1,1), HAR-RV, 기간구조 | 구현 |
| 레짐 | regime | Hamilton 2-state HMM, 추세추종 | 구현 |
| 패턴 | pattern | 캔들스틱 10종, 지지/저항 | 구현 |

### B. 리스크 (risk) — 가격 + 벤치마크

| 축 | key | 설명 | 상태 |
|---|---|---|---|
| 베타 | beta | 시장 베타 + CAPM | 구현 |
| 팩터 | factor | FF5 + q-factor 분해 | stub |
| 꼬리위험 | tailrisk | CVaR, 최대낙폭, Sortino | 구현 |
| 잔여수익 | residual | 팩터 제거 후 잔여 모멘텀 | stub |

### C. 미시구조 (microstructure) — 가격 + 거래량/수급

| 축 | key | 설명 | 상태 |
|---|---|---|---|
| 유동성 | liquidity | Amihud, Roll 스프레드, 회전율 | 구현 |
| 수급 | flow | 기관/외국인 매매 (KR전용) | 구현 |
| 거래량 | volume | OBV 추세, 거래량-가격 괴리 | 구현 |

### D. 펀더멘털 퀀트 (fundamental) — scan 프리빌드

| 축 | key | 설명 | 상태 |
|---|---|---|---|
| 괴리 | divergence | 재무-기술적 괴리 진단 | 구현 |
| 퀄리티 | quality | Asness 퀄리티 팩터 복합 | stub |
| 가치 | value | PBR/PER/PSR 가치 신호 | stub |
| 이익모멘텀 | earnings | SUE, PEAD, 수정 모멘텀 | stub |

### E. 텍스트/공시 (text) — dartlab 고유

| 축 | key | 설명 | 상태 |
|---|---|---|---|
| 공시심리 | sentiment | Loughran-McDonald 감성 스코어링 | stub |
| 톤변화 | toneChange | 기간별 공시 톤 변화 감지 | stub |
| 이벤트신호 | eventSignal | allFilings 이벤트 기반 신호 | stub |
| 리스크텍스트 | riskText | 리스크 팩터 텍스트 델타 | stub |
| 거버넌스퀀트 | governanceQuant | 지배구조 품질 정량화 | stub |

### F. 횡단면 (crossSection) — 시장 레벨

| 축 | key | 설명 | 상태 |
|---|---|---|---|
| 순위 | ranking | 멀티팩터 복합 순위 | stub |
| 페어 | pairs | 공적분 페어 탐색 | stub |
| 스크린 | screen | 팩터 스크리닝 프리셋 | stub |

### G. 포트폴리오 (portfolio) — 멀티종목

| 축 | key | 설명 | 상태 |
|---|---|---|---|
| 평균분산 | meanvar | Markowitz 최적화 | stub |
| 리스크패리티 | riskparity | HRP (Lopez de Prado) | stub |
| 자산배분 | allocation | Black-Litterman | stub |

## 학술 근거

| 방법론 | 출처 | 축 |
|---|---|---|
| Fama-French 5-Factor | Fama & French (2015) | factor |
| q-Factor | Hou, Xue, Zhang (2015) | factor |
| Cross-Sectional Momentum | Jegadeesh & Titman (1993) | momentum |
| Time-Series Momentum | Moskowitz, Ooi, Pedersen (2012) | momentum |
| 52-Week High | George & Hwang (2004) | momentum |
| Momentum Crash Hedging | Barroso & Santa-Clara (2015) | momentum |
| GARCH(1,1) | Bollerslev (1986) | volatility |
| HAR-RV | Corsi (2009) | volatility |
| Hamilton Regime Switching | Hamilton (1989) | regime |
| Amihud Illiquidity | Amihud (2002) | liquidity |
| Roll Spread | Roll (1984) | liquidity |
| CVaR/Expected Shortfall | Artzner et al. (1999) | tailrisk |
| Asness Quality | Asness, Frazzini, Pedersen (2019) | quality |
| SUE/PEAD | Ball & Brown (1968), Bernard & Thomas (1989) | earnings |
| Loughran-McDonald | Loughran & McDonald (2011) | sentiment |
| HRP | Lopez de Prado (2016) | riskparity |
| Black-Litterman | Black & Litterman (1992) | allocation |
| Engle-Granger | Engle & Granger (1987) | pairs |

## 지표 45개 (indicators.py)

### 추세 (11개)
SMA, EMA, WMA, DEMA, TEMA, HMA, VWMA, MACD, ADX, PSAR, SuperTrend

### 모멘텀 (10개)
RSI, Stochastic, Stochastic RSI, KDJ, ROC, Momentum, Williams %R, CCI, CMO, Awesome Oscillator, Ultimate Oscillator

### 변동성 (7개)
Bollinger Bands, Bollinger %B, Bollinger Width, ATR, Keltner Channel, Donchian Channel, Ulcer Index

### 거래량 (9개)
OBV, MFI, Force Index, A/D Line, Chaikin Money Flow, Ease of Movement, NVI, PVI, PVT, VWAP

### 특수 (8개)
Elder Ray, TRIX, DPO, Pivot Points, Linear Regression, Zigzag

## 신호 9개 (signals.py)

크로스오버, 크로스언더, 양방향 크로스, 골든크로스, RSI 신호, MACD 신호, 볼린저 신호, 채널 돌파, ADX 필터

## 데이터 흐름

| 타입 | 소스 | 축 |
|---|---|---|
| 가격 전용 | gather("price") | indicators, momentum, volatility, regime, pattern, tailrisk |
| 가격+벤치마크 | gather("price") + 지수 | beta, factor, residual |
| 가격+수급 | gather("flow") | flow |
| scan 프리빌드 | scan/*.parquet | quality, value, earnings, ranking |
| 텍스트 | docs/*.parquet, changes.parquet | sentiment, toneChange, riskText |
| 이벤트 | allFilings/*.parquet | eventSignal |
| 멀티종목 | 순차 OHLCV | meanvar, riskparity, allocation |

## 하위호환

기존 `dartlab.quant("005930", "indicators")` 호출은 DeprecationWarning + 자동 swap.

## review 연동

review는 `extended.py`의 함수를 직접 import (변경 없음):
```python
from dartlab.quant.extended import (
    calcTechnicalSignals, calcMarketBeta,
    calcFundamentalDivergence, calcMarketAnalysisFlags,
    calcTechnicalVerdict,
)
```

## 관련 코드

| 파일 | 역할 |
|------|------|
| `src/dartlab/quant/__init__.py` | 축 기반 Quant 클래스 + 레지스트리 + 디스패치 |
| `src/dartlab/quant/spec.py` | SPEC dict (AI/generateSpec용) |
| `src/dartlab/quant/_helpers.py` | 공용 OHLCV fetch, market 감지, scan parquet 로드 |
| `src/dartlab/quant/_ax_technical.py` | 기존 코드 축 래핑 |
| `src/dartlab/quant/indicators.py` | 45개 지표 (변경 없음) |
| `src/dartlab/quant/signals.py` | 9개 신호 (변경 없음) |
| `src/dartlab/quant/analyzer.py` | verdict + enrichWithIndicators |
| `src/dartlab/quant/extended.py` | beta, divergence, flags (review 연동) |
| `src/dartlab/quant/momentum.py` | 모멘텀 분석 |
| `src/dartlab/quant/tailrisk.py` | 꼬리위험 분석 |
| `src/dartlab/quant/volatility.py` | GARCH + HAR-RV |
| `src/dartlab/quant/regime.py` | HMM 레짐 감지 |
| `src/dartlab/quant/pattern.py` | 캔들스틱 + 지지/저항 |
| `src/dartlab/quant/microstructure.py` | Amihud + Roll + 회전율 |
| `src/dartlab/quant/flowAnalysis.py` | 수급 분석 |
| `src/dartlab/quant/volumeAnalysis.py` | 거래량 분석 |
