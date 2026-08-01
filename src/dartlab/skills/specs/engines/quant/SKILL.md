---
id: engines.quant
title: Quant
kind: curated
scope: builtin
status: observed
category: engines
purpose: Quant 엔진은 가격, 기술적 신호, 팩터, 리스크, 텍스트/공시, 횡단면 랭킹, 포트폴리오, 백테스트를 46개 축으로 실행하는 정량 분석 스킬이다. 트리거 - '퀀트', '팩터', '백테스트', '모멘텀', '기술적 신호'.
whenToUse:
  - Quant
  - quant
  - 모멘텀
  - 변동성
  - 팩터
  - 백테스트
  - 포트폴리오
  - 기술적 지표
  - 멀티팩터 순위
inputs:
  - axis
  - stockCode 또는 ticker
  - 종목 리스트
  - market
  - benchmarkMode
  - style/rule
outputs:
  - guide DataFrame
  - axis별 DataFrame 또는 dict
  - 괴리 대표 product
  - backtest/portfolio result
  - assumptions/flags
capabilityRefs:
  - quant
  - Company.quant
knowledgeRefs:
  - start.dartlabSkillOs
  - engines.gather
  - engines.analysis
sourceRefs:
  - dartlab://skills/engines.quant
requiredEvidence:
  - target
  - period
  - metric
  - benchmark
  - valueRef
  - dateRef
  - executionRef
  - sourceRef
expectedOutputs:
  - 선택한 quant axis
  - 공개 호출
  - 기간/벤치마크/가정
  - 대표 반환 형태
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: limited
failureModes:
  - 기간/벤치마크 없는 성과 수치를 말함
  - 단일 종목 축과 횡단면/포트폴리오 축을 혼동함
  - 백테스트 결과를 미래 성과 보장처럼 표현함
forbidden:
  - 투자 성과를 보장하지 않는다.
  - 기간, 수수료/슬리피지 가정, 벤치마크 없이 백테스트 결론을 내지 않는다.
  - 공개 API 호출법, guide 축, 반환 형태가 바뀌었는데 이 skill을 갱신하지 않은 상태로 완료 처리하지 않는다.
examples:
  - 삼성전자 기술적 판단
  - 모멘텀 가치 퀄리티 멀티팩터 점검
  - 종목 리스트 리스크패리티 포트폴리오
  - dartlab.quant 46 축 가이드
  - DCF 가치평가 (Damodaran)
  - 베타와 시장 민감도 측정
  - 백테스트 trendFollow 전략
procedure:
  - dartlab.quant() 로 46 축 가이드 DataFrame 확인.
  - axis 선택 (지표 · 판단 · 베타 · 순위 · 리스크패리티 · backtest 등).
  - 단일 종목은 dartlab.quant(axis, code), 종목 리스트는 dartlab.quant(axis, [code1, code2]).
  - 결과의 period · benchmark · valueRef · dateRef · executionRef 묶음.
  - 백테스트 결론은 미래 성과 보장 아님 - 가정 (수수료 · 슬리피지 · 벤치마크) 명시.
linkedSkills:
  - engines.quant.damodaranValuation
  - engines.quant.indicators
  - engines.quant.factor
  - engines.gather
  - engines.analysis
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-07-18'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
visualRefs:
  - "engines.viz.scenarioVisuals"
  - "engines.viz.tableBackedChart"
---

## 엔진 역할

`quant`는 가격/거래량/수급/팩터/공시 텍스트/포트폴리오/전략을 정량적으로 계산하는 L2 엔진이다. 재무제표의 회계적 인과 해석은 `analysis`, 시장 레벨 매크로 해석은 `macro`, 후보 유니버스 발굴은 `scan`이 담당한다.

## 공개 호출 방식

```python
import dartlab

guide = dartlab.quant()

tech = dartlab.quant("지표", "005930")
verdict = dartlab.quant("판단", "005930")
beta = dartlab.quant("베타", "005930", benchmarkMode="sector")
ranking = dartlab.quant("순위")
portfolio = dartlab.quant("리스크패리티", ["005930", "000660"])
bt = dartlab.quant("backtest", "005930", style="trendFollow")

c = dartlab.Company("005930")
company_quant = c.quant("모멘텀")
divergence = c.quant("괴리")
```

`괴리`는 Quant 대표 제품이다. 공시 이익 변화, 시장 횡단면 이익 서프라이즈 프록시,
가격 반응을 비교한다. 실제 애널리스트 컨센서스가 없으면 이를 기대치로 가장하지 않고
`product.gaps`에 `quant.analystConsensus`로 남긴다.

```text
classification: underReaction | confirmation | overOptimism | deteriorationPriced | inconclusive
fundamental, expectation, price,
product{conclusion, confidence, evidence, gaps, scenarios, falsifiers, payload}
```

## 강행 호출 룰 (agent 답변 품질 회귀 차단)

46 axis 질문 (베타·모멘텀·변동성·factor·forecast·backtest 등) 에서 다음 4 룰 강행 - 위반 시 refs=0 회귀.

1. **1 차 도구는 EngineCall 강제**. `EngineCall(apiRef="quant", args={"axis": "베타", "stockCode": "005930"})` 양식. **RunPython 직접 numpy/polars 계산은 engine 결과 부재 시에만 fallback** - 처음부터 raw 계산 금지.
2. **본문 안 숫자에 inline ref 표기 필수** - `[tableRef:...]` 또는 `[valueRef:...]` 형식. ref 없는 quant 결과는 답변 보류.
3. **backtest 결과는 `executionRef` 명시** - 백테스트 일자 / 룰 / 파라미터 ref 박지 않으면 hindsight 환각.
4. **forecast/walkforward 같은 가정 강한 축은 `[conf:30]` 기본** - 가정 (lookahead window · trend assumption) 본문에 명시.

## 호출 동작

무인자 `dartlab.quant()`는 46개 축 가이드 DataFrame을 반환한다. axis와 종목을 주면 가격/거래량/재무/공시 snapshot을 읽어 축별 결과를 계산한다.

축은 단일 종목 축, 종목 불필요 횡단면 축, 종목 리스트 포트폴리오 축, rule/style 기반 전략 축으로 나뉜다. 필요한 입력이 없으면 가이드 또는 오류/제한을 반환하고 값을 만들지 않는다.

## 전체 축/메서드 목록

| axis | label | group | 대표 호출 |
| --- | --- | --- | --- |
| indicators | 지표 | 기술적 | `dartlab.quant("지표", "005930")` |
| signals | 신호 | 기술적 | `dartlab.quant("신호", "005930")` |
| verdict | 판단 | 기술적 | `dartlab.quant("판단", "005930")` |
| momentum | 모멘텀 | 기술적 | `dartlab.quant("모멘텀", "005930")` |
| volatility | 변동성 | 기술적 | `dartlab.quant("변동성", "005930")` |
| forecast | 예측 | 기술적 | `dartlab.quant("예측", "005930", horizon=5)` |
| marketContext | 시장맥락 | 리스크 | `dartlab.quant("시장맥락", "005930")` |
| regime | 레짐 | 기술적 | `dartlab.quant("레짐", "005930")` |
| pattern | 패턴 | 기술적 | `dartlab.quant("패턴", "005930")` |
| chartPatterns | 차트패턴 | 기술적 | `dartlab.quant("차트패턴", "005930")` |
| beta | 베타 | 리스크 | `dartlab.quant("베타", "005930")` |
| benchmark | 벤치마크 | 리스크 | `dartlab.quant("벤치마크", "005930")` |
| factor | 팩터 | 리스크 | `dartlab.quant("팩터", "005930")` |
| tailrisk | 꼬리위험 | 리스크 | `dartlab.quant("꼬리위험", "005930")` |
| residual | 잔여수익 | 리스크 | `dartlab.quant("잔여수익", "005930")` |
| liquidity | 유동성 | 미시구조 | `dartlab.quant("유동성", "005930")` |
| flow | 수급 | 미시구조 | `dartlab.quant("수급", "005930")` |
| volume | 거래량 | 미시구조 | `dartlab.quant("거래량", "005930")` |
| divergence | 괴리 | 펀더멘털 | `dartlab.quant("괴리", "005930")` |
| quality | 퀄리티 | 펀더멘털 | `dartlab.quant("퀄리티", "005930")` |
| value | 가치 | 펀더멘털 | `dartlab.quant("가치", "005930")` |
| earnings | 이익모멘텀 | 펀더멘털 | `dartlab.quant("이익모멘텀", "005930")` |
| sentiment | 공시심리 | 텍스트/공시 | `dartlab.quant("공시심리", "005930")` |
| toneChange | 톤변화 | 텍스트/공시 | `dartlab.quant("톤변화", "005930")` |
| eventSignal | 이벤트신호 | 텍스트/공시 | `dartlab.quant("이벤트신호", "005930")` |
| riskText | 리스크텍스트 | 텍스트/공시 | `dartlab.quant("리스크텍스트", "005930")` |
| governanceQuant | 거버넌스퀀트 | 텍스트/공시 | `dartlab.quant("거버넌스퀀트", "005930")` |
| ranking | 순위 | 횡단면 | `dartlab.quant("순위")` |
| pairs | 페어 | 횡단면 | `dartlab.quant("페어")` |
| screen | 스크린 | 횡단면 | `dartlab.quant("스크린")` |
| altman | Altman Z/Z'' + 적용성 원장 | 펀더멘털 | `dartlab.quant("altman")` |
| piotroski | Piotroski F | 펀더멘털 | `dartlab.quant("piotroski")` |
| beneish | Beneish M 비발행 계약 | 펀더멘털 | `dartlab.quant("beneish")` |
| accruals | Sloan Accrual | 펀더멘털 | `dartlab.quant("accruals")` |
| qfactor | q-factor | 펀더멘털 | `dartlab.quant("qfactor")` |
| qmj | QMJ | 펀더멘털 | `dartlab.quant("qmj")` |
| bab | BAB 저베타 | 리스크 | `dartlab.quant("bab")` |
| surprise | 이익서프라이즈 | 펀더멘털 | `dartlab.quant("surprise")` |
| fundmom | 펀더-가격 모멘텀 | 펀더멘털 | `dartlab.quant("fundmom")` |
| meanvar | 평균분산 | 포트폴리오 | `dartlab.quant("평균분산", ["005930", "000660"])` |
| riskparity | 리스크패리티 | 포트폴리오 | `dartlab.quant("리스크패리티", ["005930", "000660"])` |
| allocation | 자산배분 | 포트폴리오 | `dartlab.quant("자산배분", ["005930", "000660"])` |
| strategy | 전략 | 전략 DSL | `dartlab.quant("strategy", "005930", rule=myRule)` |
| backtest | 백테스트 | 전략 DSL | `dartlab.quant("backtest", "005930", style="trendFollow")` |
| style | 스타일 | 전략 DSL | `dartlab.quant("style", "005930", name="all")` |
| entry | 진입진단 | 전략 DSL | `dartlab.quant("entry", "005930", style="all")` |
| walkforward | 워크포워드 | 전략 DSL | `dartlab.quant("walkforward", "005930", style="meanReversion")` |
| multi | 멀티자산 | 전략 DSL | `dartlab.quant("multi", ["005930", "000660"], style="trendFollow")` |

## axis-specific 회피 (회귀 가드)

각 axis 의 sub-spec 본문은 base SKILL.md 의 axis 표에 흡수됨 (2026-05-18 Phase C 정리). standalone 유지: `engines.quant.forecast` · `walkforward` · `scanBacktest` · `marketContext` (algorithm 구체).

| axis | axis-specific 회피 |
| --- | --- |
| accruals | Sloan accruals 한 지표로 분식 단정 X (Beneish + 정합성 동반); (NI−CFO)/TA 분기 vs 연결 vs 별도 scope 혼용 X |
| allocation | ERC 가중치 윈도우 (60D vs 252D) 명시; covariance shrinkage (ledoit-wolf) 방법 명시 |
| altman | auto는 비금융사 Z'' 한 모델(1.1/2.6); 명시 Z는 제조업+동일 회계연도 시총 필수; 시총 결손을 Z'로 대체 X; `methodology`·`coverage` 없이 인용 X |
| bab | BAB 레버리지 가정 미명시 수익률 인용 X; 252D beta 가 미래 beta 일치 가정 X |
| backtest | in-sample 결과를 OOS 약속으로 X (ruleFactory walk-forward 또는 외부 holdout 필요); 고정 Rule cpcv stress를 OOS로 부르지 않기; look-ahead bias 점검 없이 verdict X |
| benchmark | 벤치마크 (KOSPI/KRX300/섹터) 명시 없이 outperformance X; 시총가중 vs 동일가중 차이 무시 X |
| beneish | 현재 canonical LTD/current maturities/tax payable/순수 감가상각 계약이 없어 structured unavailable만 반환; proxy M·clean/red flag를 계산하거나 인용 X |
| beta | benchmarkMode (market/sector/style/auto) 명시; 회귀 기간 (3y/5y/10y) 명시 |
| chartPatterns | 차트 패턴 → 자동 매매 신호 단정 X (거래량/시장환경 동반); 목표가 패턴만으로 단언 X (fundamental anchor) |
| damodaranValuation | 적자 회사에 PER 기반 보정 없이 DCF 단정 X |
| divergence | 공시 이익, 기대 프록시, 가격 반응의 괴리 한 신호로 매매 X; expectation.method가 실제 컨센서스인지 프록시인지 확인; mean reversion 가정 명시 |
| earnings | SUE 한 분기로 PEAD 단정 X (다분기 누적); 컨센서스 추정기관 수/편차 명시 |
| entry | 진입진단 = 실시간 진단만 (백테스트 검증 X); 스톱/청산 단일 룰 X (변동성/리스크 한도 동반) |
| eventSignal | 이벤트 (M&A/경영진) 단일 신호로 가격 영향 단정 X; 공시 발표 vs 가격 반영 시점 차이 명시 |
| factor | 팩터 (size/value/momentum/quality/vol) 분류 명시; 단일 팩터로 *전략* 단정 X (멀티팩터) |
| flow | 기관/외국인 매매 단방향 신호 단정 X; 보고 시점 (당일 vs T+1) 명시 |
| fundmom | earnings + 12-1 모멘텀 합성 가중치 명시; Chordia-Shivakumar 미국 표본 KR 동일 가정 X |
| governanceQuant | 사외이사 비율/감사의견 단일 지표 단정 X (다지표 결합); 정량 점수만으로 인과 단정 X (정성 보고서 동반) |
| indicators | 30+ 지표 임의 선택 X (분석 의도 그룹 선택); 같은 지표 다른 lookback 혼용 X |
| liquidity | Amihud 비유동성 한 지표로 시장 충격 단정 X; Roll 스프레드 가정 위배 시점 명시 |
| meanvar | Markowitz MV 입력 추정 윈도우 명시; sample mean 노이즈를 진짜 결과로 단정 X |
| momentum | 단일 lookback 만으로 *추세* 단정 X (다중 cross-check); ADTV 낮은 종목 신뢰도 명시 |
| multi | 현재 equal 초기자본 strategy sleeve만 지원; 동일 시장·기간 경계와 내부 결측 stale NAV 정책, point-in-time universe 부재 명시; inv_vol/risk_parity 성과 인용 X |
| pairs | 공적분 → 영구 관계 단정 X (구조 변화 시 재검증); spread mean reversion 가정 명시 |
| pattern | 캔들스틱 한 봉으로 추세 단정 X (거래량/다음 봉 confirmation); 지지/저항 자동 탐지 단언 X (zigzag 파라미터 의존) |
| piotroski | F-score 8+ 만으로 *우량* 단정 X (시총/산업 분기); 단일 분기 만으로 X (4+ 분기 시계열) |
| qfactor | Hou-Xue-Zhang q-factor 미국 표본 KR 동일 가정 X; ROE + (-assetGrowth) 합성 가중치 명시 |
| qmj | QMJ (Quality Minus Junk) 미국 기준 KR 동일 가정 X; Profitability + Safety 합성 가중치 명시 |
| quality | quality 산식 (ROE/GP-A/accrual/debt) 분류 명시; 단일 metric 으로 *quality* 단정 X |
| ranking | universe (전종목 vs 산업) 명시; 결손 종목 처리 (skip vs flag) 명시 |
| regime | Hamilton 2-state HMM 학습 윈도우 의존성 명시; Viterbi 추정을 미래 예측으로 단정 X |
| residual | 팩터 모델 (FF3/FF5/Carhart) 명시; 잔여 모멘텀 회귀 윈도우 명시 |
| riskparity | HRP 클러스터링 거리 (correlation) 명시; 모든 시장 환경 우월 단정 X |
| riskText | 리스크 팩터 텍스트 단일 신호로 가격 인과 단정 X; 한국어 NLP 모델/사전 명시 |
| screen | 상위 종목을 곧바로 매수 추천 X (정성 + 분석 파이프라인); 스타일 (가치/모멘텀/퀄리티/저변동) 명시 |
| sentiment | EXTERNAL CONTENT 마커 무시 X; 단일 keyword 빈도로 *심리* 단정 X (다중 keyword) |
| signalReview | 백테스트 가정 (수수료/슬리피지/리밸런싱) 없이 성과 X |
| signals | 골든크로스/RSI/MACD/볼린저 단일 신호 X (다지표 confirm); 표준 파라미터 (RSI 14/MACD 12-26-9) 명시 |
| strategy | 사용자 룰 in-sample 결과 OOS 단정 X; sizing/stop 파라미터 (벤치 fix vs ATR) 명시 |
| style | 8 스타일 프리셋 결과 절대 점수 단정 X (KR reproducibility); meanReversion은 직전 252일/최소 60일, lowVolDefensive는 직전 최대 5년/최소 1년 형성 표본만 사용; 스타일 명시 |
| surprise | Bernard-Thomas PEAD 미국 결과 KR 동일 가정 X; YoY NI z-score 분모 (sigma) 정의 명시 |
| tailrisk | CVaR/MDD 한 지표 단정 X (다지표 결합); VaR/CVaR 신뢰수준 (95%/99%) 명시 |
| toneChange | 공시 톤 변화 한 신호로 가격 인과 단정 X; NLP 모델/사전 (한국어 LM) 명시 |
| value | 단일 멀티플 (PER 만) *value* 단정 X (PER/PBR/PSR/EV-EBITDA 종합); cycle peak PER 낮음 = *value trap* 가능성 |
| verdict | 단일 신호 기반 verdict X (5+ 신호 종합); 가격 기준일 (latestAsOf) 명시 |
| volatility | GARCH(1,1)/HAR-RV 모델 가정/윈도우 명시; 역사적 변동성 (252D) 으로 미래 단정 X (조건부 모델 동반) |
| volume | OBV 추세 한 지표로 매매 X (가격 추세 동반); 거래량/가격 괴리 한 신호로 미래 단정 X |
| worldClass | 가정 (윈도우/가중치/리밸런싱) 명시 없이 Sharpe/IR X; quant 본체 axis_registry 외 임의 디렉터리 추가 X |

**공통 forbidden** (모든 axis): 성과 보장 표현 X · 기간/benchmark/가정 명시 없이 수익률 인용 X · 정량 신호를 인과 분석 결론으로 제시 X.

## 대표 반환 형태

```text
dartlab.quant()
-> DataFrame
   axis, label, description, example, group
```

축 실행은 DataFrame 또는 dict를 반환한다.

```text
target, period, priceDate/latestAsOf, benchmark,
metric, value, score/signal/rank, assumptions, flags
```

백테스트/전략 축은 기간, 룰, 스타일, 포지션, 수익률, drawdown, Sharpe/DSR/PBO 성격의 검증 값을 포함할 수 있다. 포트폴리오 축은 종목별 weight, risk contribution, covariance/correlation 기반 가정을 포함할 수 있다.

## Top-level helper (axis 미등록)

`scanBacktest` 는 axis 가 아닌 attribute 로만 호출한다 (registry dispatcher 의 `fn(stockCode, **kw)` 계약과 시그니처가 어긋나기 때문 - 첫 인자가 DataFrame).

```python
top = dl.scan("valuation").filter(pl.col("등급") == "A").sort("PER").head(20)
result = dl.quant.scanBacktest(top, style="trendFollow", topN=20)
result.scanContext  # {'universeSize': 20, 'scanResultHash': '...', ...}
```

세부 sub-spec: `engines.quant.scanBacktest`.

## evidence 기준

정량 결과는 target, period, benchmark, metric, value, dateRef, executionRef가 필요하다. 백테스트는 수수료, 슬리피지, 리밸런싱, in-sample/out-of-sample 구분을 확인한다.

## 기본 실행 순서

1. 단일 종목, 횡단면, 포트폴리오, 전략 중 작업 유형을 구분한다.
2. 축을 모르면 `dartlab.quant()`로 guide를 확인한다.
3. 필요한 target 또는 종목 리스트를 넣어 axis를 실행한다.
4. 기간, benchmark, assumptions, flags를 확인한다.
5. 재무적 의미 해석은 `analysis`, 후보 발굴은 `scan`, 보고서 조합은 `story`로 넘긴다.

## 기본 검증

스킬은 공개 실행 문서다. `dartlab.quant()` guide 축, 공개 호출, 대표 반환 키가 바뀌면 이 파일과 관련 응용 스킬을 같은 변경에서 갱신한다.


---

# 흡수된 sub-spec 본문 (Phase D, 2026-05-18)

## (흡수) engines.quant.forecast 본문

## 엔진 역할

`forecast` 축은 종목의 일별 수익률 시계열에 4 개의 numpy-only 모델 (Naive · AR(1) · ETS-Holt · Theta) 중 하나를 자동 선택해 fit 하고, horizon-step 후 점예측 + 90% Conformal prediction interval 을 산출한다. 모든 통계는 분포 가정 없는 split conformal 방식으로 보정된다.

## 공개 호출 방식

```python
import dartlab

# 자동 dispatch (ADF p-value 기반)
r = dartlab.quant("예측", "005930", horizon=5)

# 명시 ensemble - 결과는 모델 평균
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
2. OHLCV 시계열 수집 - 부족 시 error dict 반환
3. log-return 시계열 변환 + ADF p-value 계산
4. `_pickModel` 로 모델 선택 (아래 룰)
5. fit + horizon-step forecast 생성
6. 90% conformal calib 로 prediction interval 보정
7. `forecastTable` + `summary` dict 반환

## 모델 dispatch 룰 (`_pickModel`)

1. `n < 60` → `naive` (데이터 부족 - drift 평균만 사용)
2. ADF p-value < 0.05 → `ar1` (평균회귀 시계열엔 ρ·y_prev 점추정이 정석. theta 는
   SES 가 마지막 점프에 끌려가 비현실 점추정을 낼 수 있어 자동 선택에서 제외 -
   cycle 1 dogfood 회귀 결과)
3. else → `etsHolt` (level + trend, no seasonality - Holt linear)

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
  "calibSize": 201,                 # conformal calib split 크기
  "pAdfStationary": 0.4231,         # ADF p-value (dispatch 근거)
  "conformalHalfWidth": 0.018562,   # 일별 log-return 단위 90% half-width
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
  "summary": "etsHolt: +0.60% over 5d ([-3.55%, +4.75%] 90% CI)"
}
```

## evidence 기준

forecast 결과를 인용할 때 다음을 함께 명시:
- target: `stockCode`
- period: `lastDate` 와 `nObs`
- metric: `modelChosen`, `conformalHalfWidth`
- value: `forecastTable[h]` 의 점예측 + interval 쌍 (점예측만 X)
- dateRef: `lastDate` (전일 종가 기준)
- executionRef: 호출 캡처

## 자기 검증 노트

- 합성 uptrend (drift +0.0008/day, n=250) → ADF p > 0.05 → etsHolt 선택, cumLogReturn[5] > 0
- 합성 sideways (OU ρ=0.7) → ADF p < 0.05 → ar1 선택, |pointForecast| 작음
- 합성 downtrend → cumLogReturn[5] < 0
- 모든 horizon 에서 lowerBound < pointForecast < upperBound 단조 보장 (conformalHalfWidth ≥ 0)
- NaN/inf 출력 없음 - 데이터 부족 시 명시 error dict
- Cycle 1 회귀 (2026-05-09): 005930 실데이터에서 theta 가 +1.8%/day 비현실 점추정 →
  dispatch 룰을 ar1 로 변경. theta 는 명시 호출 시에만 사용 가능하도록 가드.

## walkForward 결합 (forecastRuleFactory)

forecast 모델을 walk-forward로 OOS 검증하려면 `forecastRuleFactory`를 `walkForward(ruleFactory=...)`에 전달:

```python
from dartlab.quant.benchmark.forecast import forecastRuleFactory
from dartlab.quant.strategy.backtest import walkForward

# Loose mode (default) - point only
factory = forecastRuleFactory(threshold=0.0005, models=["ar1"])
bt = walkForward(close, rule=None, ruleFactory=factory, train=180, test=30, step=30, nTrials=4)
# bt.validation["refit_count"] = fold마다 재학습 횟수
# bt.pbo                         = None (단일 candidate라 판정 불가)
# bt.dsr                         = 명시한 nTrials로 계산한 OOS Deflated Sharpe Ratio
```

### Entry / Exit 룰

**Loose mode (default)** - `requireConfidence=False`:
```
entry = pointForecast > threshold
exit  = pointForecast < -threshold
```

**Strict mode** - `requireConfidence=True`:
```
entry = pointForecast > threshold AND (point - halfWidth) > -threshold
exit  = pointForecast < -threshold OR (point + halfWidth) < -2*threshold
```

일별 log-return 의 conformal half-width 는 일별 σ (~0.5~2%) 와 동급이라 strict 모드의 `lower > -threshold` 가 사실상 영원히 False - entry 0. 일별 단위에서 strict 는 권장 안 함. 누적 horizon 시그널 검증할 때만.

### 검증된 성능 (2026-05-09 dogfood)

- 합성 strong trend (drift +0.3%/day, n=600): forecast loose `sharpe=+9.6, mdd=-1.8%, active=98%` vs 정적 SMA20/60 cross `sharpe=+5.2`
- 005930 KR 4 년 (n=1062): forecast loose `sharpe=+1.12 (thr=0.0005)` / `+0.97 (thr=0.001)` / `+0.87 (thr=0.002)` vs 정적 SMA cross `sharpe=+0.62`
- Sideways (drift=0): thr=0.002 시 active=0 (false positive 차단), thr=0.0005 시 active=48% sharpe=-0.83 (낮은 임계는 noise 들어감)

**threshold 가이드**: 일별 시계열 σ 의 5~10% 범위. 일반적 KR 종목 일별 σ ≈ 1-2% → threshold 0.0005-0.002 권장.

## 한계 및 비목표

- AutoARIMA / TBATS / SARIMA / GARCH-fit 가격 예측은 본 축 범위 밖 (base install SSOT 보존)
- 변동성 예측은 별도 축 `volatility` 의 `forecast=True` 옵션 사용
- 1 일~수십일 이내 단기 forecast 만 의미 있음. 장기 (>60 일) 점예측은 conformal width 가 비대해짐
- pointForecast 는 *기댓값* 이 아니라 *모델 점추정* - 시장 변동성·뉴스·이벤트 충격 미반영

## 기본 검증

스킬 변경 시 본 파일 + `engines.quant` SKILL.md 의 forecast 행 + `tests/test_quant_forecast.py` + `_AXIS_REGISTRY["forecast"]` 4 곳을 같은 변경에서 갱신한다.

## (흡수) engines.quant.marketContext 본문

## 엔진 역할

`marketContext` 축은 가격 시계열 기반 - 일별 log-return 회귀로 시장 베타 + 거시 변수 베타 + 수급 강도를 1 행 evidence 로 묶는다. 모든 회귀는 numpy-only OLS 로 산출.

## scan.macroBeta 와 책임 분리

| 항목 | quant.marketContext | scan.macroBeta |
|---|---|---|
| 입력 | 일별 가격 시계열 | 연간 매출/이익 시계열 |
| 회귀 단위 | 일별 log-return | 연간 매출 성장률 |
| 윈도우 | 252 d (기본) | 5+ 년 |
| 목표 | 시장 민감도 (β) + 거시 민감도 (FX/금리/물가) + 수급 | 펀더멘털 민감도 (재무 성장 vs GDP/금리/환율) |
| 컬럼 | usdkrwBeta · baseRateBeta · cpiBeta · m2Beta | gdpBeta · rateBeta · fxBeta |
| 사용 시점 | 단기~중기 시장 변동 진단 | 중장기 펀더멘털 시나리오 |

같은 "거시 민감도" 라도 측정 대상 (가격 vs 매출) · 시간 단위 (일/연) · 컬럼명 모두 분리 - silent alias 회피.

## 공개 호출 방식

```python
import dartlab

# KR 기본 (USDKRW · BASE_RATE · CPI · M2)
r = dartlab.quant("시장맥락", "005930")

# 윈도우 2 년
r = dartlab.quant("marketContext", "035420", lookbackDays=504)

# US 자동감지 (FEDFUNDS · DGS10 · DCOILWTICO · CPIAUCSL)
r = dartlab.quant("marketContext", "AAPL")

# 사용자 명시 변수
r = dartlab.quant("시장맥락", "AAPL", macroVars=["FEDFUNDS", "DGS10"])
```

## 호출 동작

`dartlab.quant("marketContext", stockCode, ...)` 가 dispatch 진입. 다음 순서:

1. stockCode → market auto-detect
2. lookback 일수만큼 OHLCV + 시장 지수 + 거시 변수 동시 수집
3. 일별 수익률 시계열 정렬 (날짜 join)
4. 회귀 모델 (CAPM · 거시 · 수급) 각각 fit
5. β / α / R² + 수급 metric 통합 dict 반환

## 회귀 모델

- **CAPM**: r_i = α + β r_m + ε. β = `marketBeta`, α (annualized) = `marketAlpha`, R² = `marketR2`. 시장 지수는 종목 상장 시장 (KOSPI/KOSDAQ) 또는 SPX. `fetchBenchmarkOhlcv` SSOT 재사용.
- **거시 회귀**: r_i = α + β · ΔX + ε. ΔX 는 변수에 따라:
  - 금리 (BASE_RATE/FEDFUNDS/DGS10) → 단순 차분 Δ
  - 그 외 (USDKRW/CPI/M2/oil) → Δlog
  - 결측은 forward-fill (월별 변수 호환). R² 가 작을 수 있다.
- **수급 강도** (KR only): smart money = foreignNet + institutionNet. `smartMoneyNet60d` (60 d 합), `smartMoneyZ60d` (60 d 평균의 252 d 분포 z-score), `flowMomentum20d` (20 d 합).

## 대표 반환 형태

```text
{
  "stockCode": "005930",
  "market": "KR",
  "lookbackDays": 252,
  "dateRef": "2026-05-08",
  "lastClose": 75000.0,
  "marketBeta": 1.12,
  "marketAlpha": 0.035,        # annualized
  "marketR2": 0.482,
  "nObsCAPM": 250,
  "usdkrwBeta": -0.812,        # 음수: 원화 강세 시 +
  "usdkrwBeta_r2": 0.045,
  "baseRateBeta": 0.024,
  "baseRateBeta_r2": 0.002,
  "cpiBeta": 0.18,
  "cpiBeta_r2": 0.001,
  "m2Beta": 0.66,
  "m2Beta_r2": 0.003,
  "macroVarsUsed": ["USDKRW", "BASE_RATE", "CPI", "M2"],
  "smartMoneyNet60d": 12345678,
  "smartMoneyZ60d": +1.23,
  "flowMomentum20d": 4567890,
  "flowAvailable": true,
  "flowNObs": 1006,
  "macroSource": "wide",          # wide / singleFallback / none
  "summary": "β=1.12 · USDKRW β=-0.812 · smartMoney Z=+1.23"
}
```

`macroSource` 단일 키 - wide 호출 성공 시 `"wide"`, wide 실패 후 var 별 fetch 가 일부 성공하면 `"singleFallback"`, 둘 다 실패면 `"none"`. wide 실패 사유는 `macroWideErrorType` 진단 키로 별도 보존.

## evidence 기준

- target: `stockCode`
- period: `lookbackDays`, `dateRef`
- benchmark: 종목 상장 시장 (KOSPI/KOSDAQ/SPX) - `fetchBenchmarkOhlcv` 의 결과
- metric: `marketBeta`, `*Beta` 키 + `_r2` 쌍
- value: 숫자 + R² 함께
- dateRef: `dateRef`
- executionRef: 호출 캡처

## 자기 검증 노트

- 005930 (수출주) `usdkrwBeta` 음/양 부호는 시기에 따라 변할 수 있으나 |β| > 0.3 기대 (FX 민감)
- 035420 (네이버, 내수 IT) `|usdkrwBeta|` 작음 - 환율 비민감
- KOSPI 종목 `marketBeta` ∈ [0.3, 1.8] 합리적 범위
- US 종목 호출 시 flow 자동 비활성 (flowAvailable=False)
- R² < 0.05 인 베타는 *noise* - summary 인용 시 신중

## 한계 및 비목표

- 펀더멘털 (재무 vs 거시) 회귀는 `scan.macroBeta` 가 책임. 변수명도 분리 (gdpBeta/rateBeta vs cpiBeta/baseRateBeta)
- 거시 변수 빈도 mismatch (월별 CPI 가 일별 join 시 forward-fill) → R² 가 작은 건 *분포의 본질*
- 다변량 회귀 (multiple regression with controls) 는 본 축 범위 밖 - 단변량 OLS 로 시작
- VAR / cointegration / Granger causality 등 시계열 인과는 본 축 외부

## 기본 검증

스킬 변경 시 본 파일 + `engines.quant` SKILL.md 의 marketContext 행 + `tests/test_quant_marketContext.py` + `_AXIS_REGISTRY["marketContext"]` 4 곳을 같은 변경에서 갱신한다.

## (흡수) engines.quant.scanBacktest 본문

## 엔진 역할

`scanBacktest` 는 scan 결과 universe + signalFn (또는 style) → ``multiAssetBacktest`` 호출의 wrapper. 내부 로직 0 - 모든 백테스트는 ``multiAssetBacktest`` SSOT 가 처리. 본 helper 의 책임은 ① universe 추출, ② signalFn → Rule 변환, ③ scanContext SHA-1 기록.

## architecture 룰 준수

- quant → scan import **금지** (역방향). scan 결과는 사용자가 호출자에서 추출해 ``pl.DataFrame`` 입력으로 전달.
- 본 helper 는 ``dartlab.scan`` 을 import 하지 않음 - 단지 stockCode 컬럼이 있는 DataFrame 만 받는다.
- axis 미등록 - registry dispatcher 의 ``fn(stockCode=stockCode, **kwargs)`` 계약은 첫 인자가 stockCode. scanBacktest 의 첫 인자는 DataFrame 이라 어긋남. ``dartlab.quant("scanBacktest", ...)`` 호출 X.

## 공개 호출 방식

```python
import dartlab as dl
import polars as pl

# scan 으로 valuation 등급 A 추리고 trendFollow 스타일 백테스트
top = dl.scan("valuation").filter(pl.col("등급") == "A").sort("PER").head(20)
result = dl.quant.scanBacktest(top, style="trendFollow", topN=20)
result.sharpe, result.mdd, result.scanContext

# signalFn 직접 정의 - 단순 momentum 시그널
import numpy as np
def momentum_signal(close):
    sma_short = np.convolve(close, np.ones(10) / 10, mode="same")
    sma_long = np.convolve(close, np.ones(50) / 50, mode="same")
    return sma_short > sma_long

result = dl.quant.scanBacktest(top, signalFn=momentum_signal, topN=20)
```

## 호출 동작

`dartlab.quant.scanBacktest(scanResult, ...)` 가 진입. 다음 순서:

1. scanResult 빈 DataFrame / 누락 시 error 반환
2. signalFn 또는 style 둘 중 하나 필수 - 미지정 시 error
3. universeCol 자동 감지 (`stockCode` → `종목코드` → `stock_code` → `corp_code`)
4. scanResult.head(topN) 로 universe 추출 - 사용자가 사전 sort/filter 책임
5. signalFn 우선, fallback 으로 style → STYLE_REGISTRY 의 build 함수
6. multiAssetBacktest 호출 (현재 weighting=equal만 허용, 초기자본 sleeve 간 리밸런싱 없음)
7. BacktestResult.scanContext 에 universe 출처 SHA-1 + signalSource 기록 후 dataclasses.replace

## signalFn / style 우선순위

1. `signalFn` 명시 → 우선 (signalFn 으로 Rule 빌드)
2. signalFn 미지정 + `style` 명시 → STYLE_REGISTRY (`trendFollow` / `meanReversion` / `breakout` / `dipBuy` / `eventDriven` / `flowFollow` / `lowVolDefensive` / `seasonalKR`)
3. 둘 다 미지정 → error

## universe 컬럼 자동 감지

`universeCol="auto"` (default) 시 다음 우선순위로 첫 매칭 컬럼 사용:
1. `stockCode`
2. `종목코드`
3. `stock_code`
4. `corp_code`

명시 override: `universeCol="myCustomCol"`.

## 대표 반환 형태

```text
BacktestResult(
    equity=np.ndarray,            # 누적 자산 시계열
    returns=np.ndarray,           # 일별 포트폴리오 수익률
    positions=np.ndarray,         # sleeve drift를 반영한 실제 총 long exposure
    trades=pl.DataFrame | None,   # 종목별 sleeve trade 이력 (stock_code 컬럼 포함)
    sharpe=float,                 # Sharpe ratio
    sortino=float,
    mdd=float,                    # 최대낙폭 (음수)
    dsr=float | None,             # nTrials 명시 시 Deflated Sharpe Ratio
    pbo=float | None,
    exposure=float,               # 포지션이 0이 아닌 일수 비율
    averageExposure=float,        # 평균 실제 gross capital exposure
    validation=dict,              # calendar gap·초기/최종 sleeve weight·PIT 한계
    style=str,                    # "style:trendFollow" 또는 "signalFn"
    scanContext=dict,             # universe 출처 추적 - 본 helper 신규 필드
    status="ok" | "error",
    reason=str | None,
)
```

빈 universe / 미지정 signal / 잘못된 style → `BacktestResult(status="error", reason=...)` 반환.

## scanContext (BacktestResult 신규 필드)

```text
{
  "universeSize": 20,
  "universeCol": "stockCode",
  "topN": 20,
  "scanResultHash": "a3b1c2d4e5f60718",  # 결정적 SHA-1 (16 자)
  "signalSource": "style:trendFollow",   # 또는 "signalFn"
  "weighting": "equal"
}
```

같은 universe 입력 → 같은 hash. 사용자가 다른 sort/filter 적용 → 다른 hash. universe 출처 추적 가능.

## evidence 기준

- target: universe 종목 리스트 (BacktestResult.trades 의 stock_code 컬럼 or scanContext)
- period: BacktestResult.period
- benchmark: signalFn 또는 style 명시
- metric: sharpe / mdd / dsr, walk-forward PBO는 다중 trial 비교가 가능할 때만
- 가정: fee_bps, slip_bps, weighting
- scanContext.scanResultHash: universe 출처

## 자기 검증 노트

- 빈 scanResult → BacktestResult(status="error", reason="empty scanResult")
- signalFn / style 둘 다 미지정 → error
- 같은 universe 두 번 호출 → 같은 scanResultHash
- multiAssetBacktest 직접 호출 vs scanBacktest 의 결과 sharpe ε 이내 일치 (회귀 가드)

## 한계 및 비목표

- universe 의 등급/sort 자동 추출 X - 사용자가 사전에 ``scanResult.filter(...).sort(...).head(N)`` 책임
- inv_vol/risk_parity와 multi-period 리밸런싱은 causal formation·체결비용 원장이 없어 error
- 현재 equal은 초기 동일자본 strategy sleeve를 끝까지 보유하며 cross-sleeve 리밸런싱을 하지 않음
- 같은 시장·시작일·종료일을 요구하고 내부 결측 거래일은 stale sleeve NAV/position으로 보존해 validation.calendar_gaps에 기록
- 최신 scan universe를 과거에 소급하므로 point-in-time universe 성과가 아니며 validation.universe_point_in_time=False
- forecast 모델의 fold 마다 재학습 (walk-forward refit) 은 후속 PR

## 기본 검증

스킬 변경 시 본 파일 + `engines.quant` SKILL.md 의 top-level helper 섹션 + `tests/test_quant_scanBacktest.py` + `Quant.scanBacktest` 메서드 (`__init__.py`) + `BacktestResult.scanContext` 필드 5 곳을 같은 변경에서 갱신한다.

## (흡수) engines.quant.walkforward 본문

## 엔진 역할

quant 엔진의 워크포워드 축 응용 skill이다. ruleFactory 경로만 train-only refit OOS로 인증하고, 고정 Rule 또는 style 경로는 temporal stress로 표시한다. 단일 candidate API이므로 PBO는 산출하지 않는다. SSOT는 `_AXIS_REGISTRY` (`src/dartlab/quant/__init__.py`)다.

## 공개 호출 방식

```python
import dartlab

# 1. 문자열 호출
result = dartlab.quant("walkforward", "005930", style="trendFollow")

# 2. accessor 호출 (동등)
result = dartlab.quant.walkforward("005930", style="trendFollow")
```

## 호출 동작

종목 005930의 가격 시계열을 읽어 비중복 train/test 경로를 만든다. `step == test`만 허용하며 fold별 신호를 시간순으로 연결한 뒤 한 번의 체결 원장으로 계산한다. 고정 Rule은 `oos=False`, ruleFactory는 `oos=True`다. DSR은 실제 `nTrials`를 명시한 경우에만 계산하고 PBO는 `None`이다.

### ruleFactory 옵션 (forecast OOS 검증)

기본 style 호출은 정적 Rule temporal stress다. forecast 모델처럼 *IS fit + OOS predict* 패턴은 `walkForward(close, rule=None, ruleFactory=...)` 또는 공개 `ruleFactory=` 인자로 호출한다.

```python
from dartlab.quant.benchmark.forecast import forecastRuleFactory
from dartlab.quant.strategy.backtest import walkForward

factory = forecastRuleFactory(threshold=0.002, models=["ar1"])
bt = walkForward(close, rule=None, ruleFactory=factory, train=120, test=30, step=30, nTrials=4)
bt.validation["refit_count"]   # fold마다 재학습 횟수
bt.validation["oos_sharpes"]   # 단일 OOS 원장의 fold 구간 Sharpe
bt.validation["n_trials"]      # DSR에 사용한 실제 탐색 횟수
bt.pbo                           # None, 단일 candidate라 판정 불가
```

`ruleFactory(is_close, oos_len) -> Rule` 시그니처다. 반환 Rule 길이는 정확히 `train + test`여야 한다. test 영역의 첫 forecast는 첫 OOS 시가에 체결되고 마지막 forecast도 마지막 OOS 시가에 도달한다. 배경 호환을 위해 `cpcv`가 `validation`의 alias로 유지된다.

## 대표 반환 형태

strategy 그룹 표준에 따른 dict 또는 DataFrame 반환. 공통 키:

- `stockCode` / `corpName`: 대상 종목 (해당 시)
- `latestAsOf` / `priceDate`: 데이터 기준일
- 축 고유 metric / score / verdict / rank column (정확한 spec 은 `_AXIS_REGISTRY['walkforward'].fn` 함수 docstring 검산)
- `flags` / `assumptions`: 결손 · 가정

전체 키는 base SKILL `engines.quant` 표 + 함수 docstring 으로 검산.

## 기본 실행 순서

1. 대상 종목 (또는 종목 리스트), 기준일, benchmark 확정.
2. 위 공개 호출 그대로 실행.
3. `latestAsOf` / 결손 종목 / `flags` / `assumptions` 점검.
4. 숫자 claim 은 `valueRef` / `dateRef` / `executionRef` 에 묶음.
5. 다축 narrative 조립은 `engines.story` 또는 상위 recipe 가 담당.

## 기본 검증

이 skill 은 공개 실행 문서다. 본 axis 호출 방식, 반환 키, 오류 / 제한 동작이 변경되면 같은 변경에서 본 파일을 갱신한다. SSOT 는 `_AXIS_REGISTRY` (`src/dartlab/quant/__init__.py`) + 함수 docstring.
