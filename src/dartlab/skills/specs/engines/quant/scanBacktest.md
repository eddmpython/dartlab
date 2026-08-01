---
id: engines.quant.scanBacktest
title: Quant Scan Backtest
category: engines
kind: curated
status: observed
purpose: scan rule 의 historical universe 적용 backtest — slippage/cost 명시 + walk-forward.
sourceRefs:
  - dartlab://skills/engines.quant.scanBacktest
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
  - scan rule historical backtest
  - universe 변동 효과 측정
  - slippage / cost 명시
---

## 엔진 역할

`scanBacktest` 는 scan 결과 universe + signalFn (또는 style) → ``multiAssetBacktest`` 호출의 wrapper. 내부 로직 0 — 모든 백테스트는 ``multiAssetBacktest`` SSOT 가 처리. 본 helper 의 책임은 ① universe 추출, ② signalFn → Rule 변환, ③ scanContext SHA-1 기록.

## architecture 룰 준수

- quant → scan import **금지** (역방향). scan 결과는 사용자가 호출자에서 추출해 ``pl.DataFrame`` 입력으로 전달.
- 본 helper 는 ``dartlab.scan`` 을 import 하지 않음 — 단지 stockCode 컬럼이 있는 DataFrame 만 받는다.
- axis 미등록 — registry dispatcher 의 ``fn(stockCode=stockCode, **kwargs)`` 계약은 첫 인자가 stockCode. scanBacktest 의 첫 인자는 DataFrame 이라 어긋남. ``dartlab.quant("scanBacktest", ...)`` 호출 X.

## 공개 호출 방식

```python
import dartlab as dl
import polars as pl

# scan 으로 valuation 등급 A 추리고 trendFollow 스타일 백테스트
top = dl.scan("valuation").filter(pl.col("등급") == "A").sort("PER").head(20)
result = dl.quant.scanBacktest(top, style="trendFollow", topN=20)
result.sharpe, result.mdd, result.scanContext

# signalFn 직접 정의 — 단순 momentum 시그널
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
2. signalFn 또는 style 둘 중 하나 필수 — 미지정 시 error
3. universeCol 자동 감지 (`stockCode` → `종목코드` → `stock_code` → `corp_code`)
4. scanResult.head(topN) 로 universe 추출 — 사용자가 사전 sort/filter 책임
5. signalFn 우선, fallback 으로 style → STYLE_REGISTRY 의 build 함수
6. multiAssetBacktest 호출 (weighting=equal/inv_vol/risk_parity)
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
    trades=pl.DataFrame | None,   # 종목별 trade 이력 (stock_code 컬럼 포함)
    sharpe=float,                 # Sharpe ratio
    sortino=float,
    mdd=float,                    # 최대낙폭 (음수)
    dsr=float | None,             # nTrials 명시 시 Deflated Sharpe Ratio
    pbo=float | None,
    style=str,                    # "style:trendFollow" 또는 "signalFn"
    scanContext=dict,             # universe 출처 추적 — 본 helper 신규 필드
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
- metric: sharpe / mdd / dsr, PBO는 다중 trial 비교가 가능할 때만
- 가정: fee_bps, slip_bps, weighting
- scanContext.scanResultHash: universe 출처

## 자기 검증 노트

- 빈 scanResult → BacktestResult(status="error", reason="empty scanResult")
- signalFn / style 둘 다 미지정 → error
- 같은 universe 두 번 호출 → 같은 scanResultHash
- multiAssetBacktest 직접 호출 vs scanBacktest 의 결과 sharpe ε 이내 일치 (회귀 가드)

## 한계 및 비목표

- universe 의 등급/sort 자동 추출 X — 사용자가 사전에 ``scanResult.filter(...).sort(...).head(N)`` 책임
- multi-period 백테스트 (월별 리밸런싱) 는 본 helper 범위 밖 — ``multiAssetBacktest`` 가 정적 가중치만 지원
- forecast 모델의 fold 마다 재학습 (walk-forward refit) 은 후속 PR

## 기본 검증

스킬 변경 시 본 파일 + `engines.quant` SKILL.md 의 top-level helper 섹션 + `tests/test_quant_scanBacktest.py` + `Quant.scanBacktest` 메서드 (`__init__.py`) + `BacktestResult.scanContext` 필드 5 곳을 같은 변경에서 갱신한다.
