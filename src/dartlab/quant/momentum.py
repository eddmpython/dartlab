"""모멘텀 분석 — 횡단면/시계열/52주 신고가.

학술 근거:
- Jegadeesh & Titman (1993): 12-1개월 횡단면 모멘텀
- Moskowitz, Ooi, Pedersen (2012): 시계열 모멘텀 (TSMOM)
- George & Hwang (2004): 52주 신고가 비율
- Barroso & Santa-Clara (2015): 모멘텀 크래시 리스크 헤징
"""

from __future__ import annotations

import numpy as np

from dartlab.quant._helpers import fetch_ohlcv, ohlcv_to_arrays, resolve_market


def analyze_momentum(stockCode: str, *, market: str = "auto", **kwargs) -> dict:
    """모멘텀 종합 분석.

    Args:
        stockCode: 종목코드 또는 ticker.
        market: "KR" | "US" | "auto".

    Returns:
        dict with momentum12_1, tsMomentum, highRatio52w, crashRisk 등.
    """
    market = resolve_market(stockCode, market)
    ohlcv = fetch_ohlcv(stockCode, **kwargs)
    if ohlcv is None or ohlcv.is_empty():
        return {"error": f"{stockCode} 주가 데이터 없음"}

    arr = ohlcv_to_arrays(ohlcv)
    if "close" not in arr or len(arr["close"]) < 22:
        return {"error": f"{stockCode} 데이터 부족 (최소 22일 필요)"}

    close = arr["close"]
    n = len(close)

    result: dict = {
        "stockCode": stockCode,
        "market": market,
        "dataPoints": n,
    }

    # ── 12-1개월 횡단면 모멘텀 (Jegadeesh-Titman) ──
    # 최근 1개월 제외, 그 이전 11개월 수익률
    if n >= 252:
        ret_12m = close[-22] / close[-252] - 1  # 12개월 수익률
        ret_1m = close[-1] / close[-22] - 1  # 최근 1개월 수익률
        mom_12_1 = close[-22] / close[-252] - 1  # skip most recent month
        result["momentum12_1"] = round(float(mom_12_1), 4)
        result["return12m"] = round(float(ret_12m), 4)
        result["return1m"] = round(float(ret_1m), 4)
    elif n >= 126:
        ret_6m = close[-22] / close[-126] - 1
        result["momentum6_1"] = round(float(ret_6m), 4)
        result["momentum12_1"] = None
    else:
        result["momentum12_1"] = None

    # ── 시계열 모멘텀 (Moskowitz et al. 2012) ──
    # 과거 12개월 자신의 수익률 부호 → 같은 방향 지속 여부
    ts_signals = {}
    for label, lookback in [("1m", 22), ("3m", 63), ("6m", 126), ("12m", 252)]:
        if n > lookback:
            ret = close[-1] / close[-lookback] - 1
            ts_signals[label] = {
                "return": round(float(ret), 4),
                "signal": "long" if ret > 0 else "short",
            }
    result["tsMomentum"] = ts_signals

    # ── 52주 신고가 비율 (George & Hwang 2004) ──
    if n >= 252:
        high_52w = float(np.max(arr.get("high", close)[-252:]))
        current = float(close[-1])
        ratio = current / high_52w if high_52w > 0 else 0
        result["highRatio52w"] = round(ratio, 4)
        result["high52w"] = round(high_52w, 2)
        # 해석: 0.95+ = 신고가 근접, 0.7- = 크게 하락
        if ratio >= 0.95:
            result["highProximity"] = "신고가 근접"
        elif ratio >= 0.80:
            result["highProximity"] = "상위권"
        elif ratio >= 0.60:
            result["highProximity"] = "중간"
        else:
            result["highProximity"] = "하위권"
    else:
        result["highRatio52w"] = None

    # ── 모멘텀 크래시 리스크 (Barroso & Santa-Clara 2015) ──
    # 최근 실현변동성이 높으면 모멘텀 크래시 위험 증가
    if n >= 126:
        daily_returns = np.diff(np.log(close[-126:]))
        realized_vol = float(np.std(daily_returns) * np.sqrt(252))
        # 변동성 상위 구간이면 모멘텀 위험
        if realized_vol > 0.5:
            crash_risk = "high"
        elif realized_vol > 0.3:
            crash_risk = "medium"
        else:
            crash_risk = "low"
        result["crashRisk"] = crash_risk
        result["realizedVol6m"] = round(realized_vol, 4)
    else:
        result["crashRisk"] = None

    # ── 모멘텀 연속성 (streak) ──
    if n >= 22:
        monthly_returns = []
        for i in range(min(12, n // 22)):
            start_idx = -(i + 1) * 22
            end_idx = -i * 22 if i > 0 else None
            if abs(start_idx) <= n:
                if end_idx is None:
                    mr = close[-1] / close[start_idx] - 1
                else:
                    mr = close[end_idx] / close[start_idx] - 1
                monthly_returns.append(mr)

        if monthly_returns:
            # 최근 연속 양(+)/음(-) 개월 수
            streak = 0
            direction = 1 if monthly_returns[0] > 0 else -1
            for mr in monthly_returns:
                if (mr > 0 and direction > 0) or (mr <= 0 and direction <= 0):
                    streak += 1
                else:
                    break
            result["streak"] = streak * direction
            result["streakDirection"] = "상승" if direction > 0 else "하락"

    # ── 종합 판단 ──
    signals_count = sum(
        1 for v in ts_signals.values()
        if isinstance(v, dict) and v.get("signal") == "long"
    )
    total_signals = len(ts_signals)
    if total_signals > 0:
        if signals_count == total_signals:
            result["momentumVerdict"] = "strong_bullish"
        elif signals_count >= total_signals * 0.75:
            result["momentumVerdict"] = "bullish"
        elif signals_count >= total_signals * 0.5:
            result["momentumVerdict"] = "mixed"
        elif signals_count > 0:
            result["momentumVerdict"] = "bearish"
        else:
            result["momentumVerdict"] = "strong_bearish"

    return result
