"""
실험 ID: 108-001
실험명: tradix 벡터화 지표를 dartlab gather("price") OHLCV에 연결

목적:
- gather("price")가 반환하는 OHLCV DataFrame에서 tradix 지표를 계산할 수 있는지 검증
- 성능(1초 이내), 정합성, Polars 변환 확인

가설:
1. gather("price") → NumPy 변환 → tradix 지표 계산이 1초 이내
2. RSI, MACD, 볼린저밴드가 정상적으로 계산되고 NaN 처리가 올바름
3. 3~5개 종목으로 확장해도 안정적

방법:
1. gather("price", "005930") 호출 → Polars DataFrame
2. .to_numpy()로 변환 → tradix indicators 직접 호출
3. 결과를 Polars DataFrame으로 병합
4. 5개 종목 반복 실행 + 시간 측정

결과 (실험 후 작성):
| 종목 | 데이터 | 수집 | 지표계산 | RSI | MACD | BB위치 |
|------|--------|------|---------|-----|------|--------|
| 005930 | 244일 | 1.7s | 11.1ms | 52.8 | +297 | 55.5% |
| 000660 | 244일 | 1.3s | 6.4ms | 47.5 | -3820 | 29.9% |
| 035720 | 244일 | 0.5s | 4.0ms | 42.3 | -2237 | 29.9% |
| 051910 | 244일 | 0.9s | 6.6ms | 48.6 | -5344 | 56.6% |
| 006400 | 244일 | 0.9s | 4.3ms | 59.7 | +7329 | 118.7% |

요약: 지표계산 평균 6.5ms, 주가수집 평균 1.0s, 총 5.2s/5종목
NaN 비율: RSI 5.7%, MACD 10.2%, BB 7.8% (초기 워밍업 기간)

결론:
- 가설1 채택: 지표 계산 6.5ms — 수집(1.0s) 대비 무시할 수준. 병목은 네이버 API
- 가설2 채택: RSI/MACD/BB 모두 정상 계산, NaN은 워밍업 기간(14~26일)에만 발생
- 가설3 채택: 5종목 안정적, 총 5.2초 (종목당 1초)
- Polars ↔ NumPy 변환 비용 무시할 수준
- tradix indicators.py는 dartlab에 독립 이식 가능 (순수 NumPy, 외부 의존성 없음)
- 006400(삼성SDI) BB위치 118.7% = 상단 돌파 → 과매수 신호 정상 탐지

실험일: 2026-04-01
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import polars as pl

# tradix vectorized indicators 직접 로드 (import 충돌 우회)
import importlib.util

TRADIX_INDICATORS = Path("c:/Users/MSI/OneDrive/Desktop/sideProject/tradix/vectorized/indicators.py")
spec = importlib.util.spec_from_file_location("tradix_indicators", TRADIX_INDICATORS)
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)

vsma = _mod.vsma
vema = _mod.vema
vrsi = _mod.vrsi
vmacd = _mod.vmacd
vbollinger = _mod.vbollinger
vatr = _mod.vatr
vstochastic = _mod.vstochastic
vroc = _mod.vroc
vmomentum = _mod.vmomentum


def _gatherPrice(code: str) -> pl.DataFrame | None:
    """gather("price")로 OHLCV 가져오기."""
    from dartlab.gather.entry import GatherEntry
    g = GatherEntry()
    try:
        return g("price", code)
    except Exception as e:
        print(f"  {code} 수집 실패: {e}")
        return None


def _calcIndicators(df: pl.DataFrame) -> pl.DataFrame:
    """OHLCV DataFrame → 10개 기술적 지표 추가."""
    close = df["close"].to_numpy().astype(np.float64)
    high = df["high"].to_numpy().astype(np.float64)
    low = df["low"].to_numpy().astype(np.float64)

    # 10개 지표 계산
    sma20 = vsma(close, 20)
    sma60 = vsma(close, 60)
    ema12 = vema(close, 12)
    rsi14 = vrsi(close, 14)
    macd_line, macd_signal, macd_hist = vmacd(close)
    bb_upper, bb_middle, bb_lower = vbollinger(close, 20, 2.0)
    atr14 = vatr(high, low, close, 14)
    stoch_k, stoch_d = vstochastic(high, low, close)
    roc12 = vroc(close, 12)
    mom10 = vmomentum(close, 10)

    # Polars DataFrame에 추가
    result = df.with_columns([
        pl.Series("sma20", sma20),
        pl.Series("sma60", sma60),
        pl.Series("ema12", ema12),
        pl.Series("rsi14", rsi14),
        pl.Series("macd", macd_line),
        pl.Series("macdSignal", macd_signal),
        pl.Series("macdHist", macd_hist),
        pl.Series("bbUpper", bb_upper),
        pl.Series("bbLower", bb_lower),
        pl.Series("atr14", atr14),
        pl.Series("stochK", stoch_k),
        pl.Series("stochD", stoch_d),
        pl.Series("roc12", roc12),
        pl.Series("momentum10", mom10),
    ])

    return result


def main():
    print("=== 108-001: tradix 지표 → dartlab gather 연결 ===\n")

    codes = ["005930", "000660", "035720", "051910", "006400"]  # 삼성전자, SK하이닉스, 카카오, LG화학, 삼성SDI

    results = {}
    for code in codes:
        print(f"--- {code} ---")
        t0 = time.time()

        # 1. 주가 수집
        df = _gatherPrice(code)
        if df is None or df.is_empty():
            print(f"  데이터 없음")
            results[code] = {"status": "NO_DATA"}
            continue
        t_gather = time.time() - t0

        # 2. 지표 계산
        t1 = time.time()
        enriched = _calcIndicators(df)
        t_calc = time.time() - t1

        # 3. 결과 확인
        total = time.time() - t0
        n = enriched.height
        last = enriched.tail(1).to_dicts()[0]

        rsi_val = last.get("rsi14")
        macd_val = last.get("macd")
        bb_pos = None
        if last.get("bbUpper") and last.get("bbLower") and last.get("close"):
            bb_range = last["bbUpper"] - last["bbLower"]
            if bb_range > 0:
                bb_pos = round((last["close"] - last["bbLower"]) / bb_range * 100, 1)

        print(f"  {n}일 데이터, 수집 {t_gather:.1f}s, 지표계산 {t_calc*1000:.1f}ms, 총 {total:.1f}s")
        print(f"  최신: close={last['close']}, RSI={rsi_val:.1f}, MACD={macd_val:.1f}, BB위치={bb_pos}%")

        # NaN 비율 확인
        nan_cols = {}
        for col in ["rsi14", "macd", "bbUpper", "atr14", "stochK"]:
            nan_count = enriched[col].null_count() + enriched.filter(pl.col(col).is_nan()).height
            nan_cols[col] = round(nan_count / n * 100, 1)
        print(f"  NaN%: {nan_cols}")

        results[code] = {
            "status": "OK",
            "rows": n,
            "gatherSec": round(t_gather, 2),
            "calcMs": round(t_calc * 1000, 2),
            "totalSec": round(total, 2),
            "lastRSI": round(rsi_val, 1) if rsi_val and not np.isnan(rsi_val) else None,
            "lastMACD": round(macd_val, 1) if macd_val and not np.isnan(macd_val) else None,
            "bbPosition": bb_pos,
        }
        print()

    # 요약
    print("=== 요약 ===")
    calc_times = [r["calcMs"] for r in results.values() if r.get("calcMs")]
    gather_times = [r["gatherSec"] for r in results.values() if r.get("gatherSec")]
    print(f"지표 계산: 평균 {np.mean(calc_times):.1f}ms (max {max(calc_times):.1f}ms)")
    print(f"주가 수집: 평균 {np.mean(gather_times):.1f}s (max {max(gather_times):.1f}s)")
    print(f"총 처리: {sum(r.get('totalSec', 0) for r in results.values()):.1f}s / {len(codes)}종목")

    import json
    outPath = Path("experiments/108_quantEngine/001_result.json")
    outPath.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[SAVED] {outPath}")


if __name__ == "__main__":
    main()
