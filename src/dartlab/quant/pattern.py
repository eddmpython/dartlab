"""캔들스틱 패턴 + 지지/저항 분석.

주요 캔들스틱 10종 패턴 인식 + zigzag 기반 지지/저항 수준.
"""

from __future__ import annotations

import numpy as np

from dartlab.quant._helpers import fetch_ohlcv, ohlcv_to_arrays, resolve_market


def analyze_pattern(stockCode: str, *, market: str = "auto", lookback: int = 20, **kwargs) -> dict:
    """캔들스틱 패턴 + 지지/저항 분석.

    Args:
        stockCode: 종목코드 또는 ticker.
        market: "KR" | "US" | "auto".
        lookback: 패턴 탐색 기간 (일).

    Returns:
        dict with patterns, supportLevels, resistanceLevels.
    """
    market = resolve_market(stockCode, market)
    ohlcv = fetch_ohlcv(stockCode, **kwargs)
    if ohlcv is None or ohlcv.is_empty():
        return {"error": f"{stockCode} 주가 데이터 없음"}

    arr = ohlcv_to_arrays(ohlcv)
    o = arr.get("open")
    h = arr.get("high")
    lo = arr.get("low")
    c = arr.get("close")
    dates = arr.get("date", [])

    if o is None or h is None or lo is None or c is None or len(c) < 5:
        return {"error": f"{stockCode} OHLC 데이터 부족"}

    n = len(c)
    result: dict = {
        "stockCode": stockCode,
        "market": market,
        "dataPoints": n,
    }

    # ── 캔들스틱 패턴 10종 탐색 ──
    patterns = []
    start = max(2, n - lookback)

    for i in range(start, n):
        body = c[i] - o[i]
        abs_body = abs(body)
        upper_shadow = h[i] - max(o[i], c[i])
        lower_shadow = min(o[i], c[i]) - lo[i]
        full_range = h[i] - lo[i]

        if full_range == 0:
            continue

        date_str = str(dates[i])[:10] if i < len(dates) else str(i)
        body_ratio = abs_body / full_range

        # 1. Doji (도지) — 몸통이 전체의 10% 미만
        if body_ratio < 0.1:
            patterns.append({"date": date_str, "pattern": "doji", "label": "도지", "signal": "반전 가능"})

        # 2. Hammer (망치형) — 하단 그림자 ≥ 몸통 2배, 상단 그림자 작음
        elif lower_shadow >= abs_body * 2 and upper_shadow < abs_body * 0.5 and body > 0:
            patterns.append({"date": date_str, "pattern": "hammer", "label": "망치형", "signal": "상승 반전"})

        # 3. Inverted Hammer (역망치형)
        elif upper_shadow >= abs_body * 2 and lower_shadow < abs_body * 0.5 and body > 0:
            patterns.append({"date": date_str, "pattern": "invertedHammer", "label": "역망치형", "signal": "상승 반전"})

        # 4. Hanging Man (교수형) — 망치와 같지만 상승 추세에서
        elif lower_shadow >= abs_body * 2 and upper_shadow < abs_body * 0.5 and body < 0:
            patterns.append({"date": date_str, "pattern": "hangingMan", "label": "교수형", "signal": "하락 반전"})

        # 5. Shooting Star (유성형)
        elif upper_shadow >= abs_body * 2 and lower_shadow < abs_body * 0.5 and body < 0:
            patterns.append({"date": date_str, "pattern": "shootingStar", "label": "유성형", "signal": "하락 반전"})

        # 2일 패턴
        if i >= 1:
            prev_body = c[i - 1] - o[i - 1]
            abs_prev_body = abs(prev_body)

            # 6. Bullish Engulfing (상승장악형) — 양봉이 전일 음봉을 완전히 감쌈
            if prev_body < 0 and body > 0 and abs_body > abs_prev_body * 1.0:
                if o[i] <= c[i - 1] and c[i] >= o[i - 1]:
                    patterns.append({"date": date_str, "pattern": "bullishEngulfing", "label": "상승장악형", "signal": "상승 반전"})

            # 7. Bearish Engulfing (하락장악형)
            elif prev_body > 0 and body < 0 and abs_body > abs_prev_body * 1.0:
                if o[i] >= c[i - 1] and c[i] <= o[i - 1]:
                    patterns.append({"date": date_str, "pattern": "bearishEngulfing", "label": "하락장악형", "signal": "하락 반전"})

            # 8. Piercing Line (관통형)
            if prev_body < 0 and body > 0:
                mid_prev = (o[i - 1] + c[i - 1]) / 2
                if o[i] < c[i - 1] and c[i] > mid_prev and c[i] < o[i - 1]:
                    patterns.append({"date": date_str, "pattern": "piercingLine", "label": "관통형", "signal": "상승 반전"})

            # 9. Dark Cloud Cover (먹구름형)
            if prev_body > 0 and body < 0:
                mid_prev = (o[i - 1] + c[i - 1]) / 2
                if o[i] > c[i - 1] and c[i] < mid_prev and c[i] > o[i - 1]:
                    patterns.append({"date": date_str, "pattern": "darkCloudCover", "label": "먹구름형", "signal": "하락 반전"})

        # 3일 패턴
        if i >= 2:
            # 10. Morning Star (샛별형) — 큰 음봉 + 작은 몸통 + 큰 양봉
            prev2_body = c[i - 2] - o[i - 2]
            prev1_body = c[i - 1] - o[i - 1]
            if (prev2_body < 0 and abs(prev2_body) > full_range * 0.3
                    and abs(prev1_body) < abs(prev2_body) * 0.3
                    and body > 0 and abs_body > abs(prev2_body) * 0.5):
                patterns.append({"date": date_str, "pattern": "morningStar", "label": "샛별형", "signal": "상승 반전"})

    result["patterns"] = patterns[-10:]  # 최근 10개만
    result["patternCount"] = len(patterns)

    # ── 지지/저항 수준 (zigzag 기반 pivot points) ──
    pivots = _find_pivots(h, lo, threshold=0.05)
    if pivots:
        current_price = float(c[-1])
        supports = sorted([p["price"] for p in pivots if p["type"] == "low" and p["price"] < current_price], reverse=True)
        resistances = sorted([p["price"] for p in pivots if p["type"] == "high" and p["price"] > current_price])

        result["supportLevels"] = [round(s, 2) for s in supports[:3]]
        result["resistanceLevels"] = [round(r, 2) for r in resistances[:3]]
        result["currentPrice"] = round(current_price, 2)

        # 가장 가까운 지지/저항까지 거리
        if supports:
            result["nearestSupport"] = round(supports[0], 2)
            result["supportDistance"] = round((current_price - supports[0]) / current_price * 100, 2)
        if resistances:
            result["nearestResistance"] = round(resistances[0], 2)
            result["resistanceDistance"] = round((resistances[0] - current_price) / current_price * 100, 2)

    # ── 최근 패턴 종합 신호 ──
    if patterns:
        recent = patterns[-5:]
        bullish = sum(1 for p in recent if "상승" in p.get("signal", ""))
        bearish = sum(1 for p in recent if "하락" in p.get("signal", ""))
        if bullish > bearish:
            result["patternVerdict"] = "bullish"
        elif bearish > bullish:
            result["patternVerdict"] = "bearish"
        else:
            result["patternVerdict"] = "neutral"
    else:
        result["patternVerdict"] = "no_pattern"

    return result


def _find_pivots(high: np.ndarray, low: np.ndarray, threshold: float = 0.05) -> list[dict]:
    """간이 zigzag로 pivot points 탐색.

    Args:
        high: 고가 배열.
        low: 저가 배열.
        threshold: 전환 판단 임계값 (5%).

    Returns:
        list of {"idx", "price", "type": "high"|"low"}
    """
    n = len(high)
    if n < 5:
        return []

    pivots = []
    # 초기 방향
    direction = 1  # 1 = 상승 탐색, -1 = 하락 탐색
    last_high_idx = 0
    last_low_idx = 0
    last_high = float(high[0])
    last_low = float(low[0])

    for i in range(1, n):
        h_val = float(high[i])
        l_val = float(low[i])

        if direction == 1:
            if h_val > last_high:
                last_high = h_val
                last_high_idx = i
            elif last_high > 0 and (last_high - l_val) / last_high >= threshold:
                pivots.append({"idx": last_high_idx, "price": last_high, "type": "high"})
                direction = -1
                last_low = l_val
                last_low_idx = i
        else:
            if l_val < last_low:
                last_low = l_val
                last_low_idx = i
            elif last_low > 0 and (h_val - last_low) / last_low >= threshold:
                pivots.append({"idx": last_low_idx, "price": last_low, "type": "low"})
                direction = 1
                last_high = h_val
                last_high_idx = i

    return pivots
