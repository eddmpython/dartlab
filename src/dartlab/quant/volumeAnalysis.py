"""거래량 분석 — OBV 추세, 거래량-가격 괴리, 누적분배.

기존 indicators.py의 vobv, vadl, vmfi 위에 해석 레이어를 구축.
"""

from __future__ import annotations

import numpy as np

from dartlab.quant._helpers import fetch_ohlcv, ohlcv_to_arrays, resolve_market


def analyze_volume(stockCode: str, *, market: str = "auto", **kwargs) -> dict:
    """거래량 종합 분석.

    Args:
        stockCode: 종목코드 또는 ticker.
        market: "KR" | "US" | "auto".

    Returns:
        dict with obvTrend, volumePriceDivergence, adLine 등.
    """
    market = resolve_market(stockCode, market)
    ohlcv = fetch_ohlcv(stockCode, **kwargs)
    if ohlcv is None or ohlcv.is_empty():
        return {"error": f"{stockCode} 주가 데이터 없음"}

    arr = ohlcv_to_arrays(ohlcv)
    close = arr.get("close")
    volume = arr.get("volume")
    high = arr.get("high", close)
    low = arr.get("low", close)

    if close is None or volume is None or len(close) < 20:
        return {"error": f"{stockCode} 데이터 부족"}

    n = len(close)
    result: dict = {
        "stockCode": stockCode,
        "market": market,
        "dataPoints": n,
    }

    # ── OBV (On-Balance Volume) 추세 ──
    from dartlab.quant.indicators import vobv

    obv = vobv(close, volume)
    if len(obv) >= 20:
        obv_20 = obv[-20:]
        # OBV 선형회귀 기울기로 추세 판단
        x = np.arange(20, dtype=np.float64)
        slope = _linreg_slope(x, obv_20)
        result["obvSlope"] = round(float(slope), 2)
        result["obvTrend"] = "상승" if slope > 0 else "하락"

        # OBV vs 가격 괴리
        price_20 = close[-20:]
        price_slope = _linreg_slope(x, price_20)
        if slope > 0 and price_slope < 0:
            result["obvDivergence"] = "bullish_divergence"
        elif slope < 0 and price_slope > 0:
            result["obvDivergence"] = "bearish_divergence"
        else:
            result["obvDivergence"] = "confirm"

    # ── 누적분배선 (A/D Line) ──
    from dartlab.quant.indicators import vadl

    adl = vadl(high, low, close, volume)
    if len(adl) >= 20:
        adl_20 = adl[-20:]
        x = np.arange(20, dtype=np.float64)
        adl_slope = _linreg_slope(x, adl_20)
        result["adLineTrend"] = "누적" if adl_slope > 0 else "분배"

    # ── 거래량 이동평균 비율 ──
    if n >= 20:
        vol_sma20 = float(np.mean(volume[-20:]))
        vol_current = float(np.mean(volume[-5:]))  # 최근 5일 평균
        vol_ratio = vol_current / vol_sma20 if vol_sma20 > 0 else 1
        result["volumeRatio"] = round(vol_ratio, 2)
        if vol_ratio > 2.0:
            result["volumeSignal"] = "급증"
        elif vol_ratio > 1.3:
            result["volumeSignal"] = "증가"
        elif vol_ratio < 0.5:
            result["volumeSignal"] = "급감"
        elif vol_ratio < 0.7:
            result["volumeSignal"] = "감소"
        else:
            result["volumeSignal"] = "보통"

    # ── MFI (Money Flow Index) ──
    from dartlab.quant.indicators import vmfi

    mfi = vmfi(high, low, close, volume)
    if not np.all(np.isnan(mfi)):
        latest_mfi = float(mfi[~np.isnan(mfi)][-1])
        result["mfi"] = round(latest_mfi, 2)
        if latest_mfi > 80:
            result["mfiSignal"] = "과매수"
        elif latest_mfi < 20:
            result["mfiSignal"] = "과매도"
        else:
            result["mfiSignal"] = "중립"

    # ── 거래량-가격 상관관계 ──
    if n >= 20:
        price_changes = np.diff(close[-21:])
        vol_changes = volume[-20:]
        corr = _correlation(price_changes, vol_changes)
        result["volumePriceCorrelation"] = round(float(corr), 4)
        # 양의 상관: 가격 상승 시 거래량 증가 (건강한 추세)
        # 음의 상관: 가격 상승 시 거래량 감소 (추세 약화)

    # ── Force Index ──
    from dartlab.quant.indicators import vforceIndex

    fi = vforceIndex(close, volume, period=13)
    if not np.all(np.isnan(fi)):
        latest_fi = float(fi[~np.isnan(fi)][-1])
        result["forceIndex"] = round(latest_fi, 2)
        result["forceIndexSignal"] = "매수" if latest_fi > 0 else "매도"

    # ── 종합 판단 ──
    bullish = 0
    bearish = 0
    if result.get("obvDivergence") == "bullish_divergence":
        bullish += 2
    elif result.get("obvDivergence") == "bearish_divergence":
        bearish += 2
    if result.get("obvTrend") == "상승":
        bullish += 1
    else:
        bearish += 1
    if result.get("adLineTrend") == "누적":
        bullish += 1
    else:
        bearish += 1
    if result.get("mfiSignal") == "과매도":
        bullish += 1
    elif result.get("mfiSignal") == "과매수":
        bearish += 1
    if result.get("volumeSignal") in ("급증", "증가") and result.get("obvTrend") == "상승":
        bullish += 1

    total = bullish + bearish
    if total > 0:
        score = (bullish - bearish) / total
        if score > 0.3:
            result["volumeVerdict"] = "bullish"
        elif score < -0.3:
            result["volumeVerdict"] = "bearish"
        else:
            result["volumeVerdict"] = "neutral"
        result["volumeScore"] = round(score, 2)

    return result


def _linreg_slope(x: np.ndarray, y: np.ndarray) -> float:
    """단순 선형회귀 기울기."""
    n = len(x)
    if n < 2:
        return 0.0
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    denom = np.sum((x - x_mean) ** 2)
    if denom == 0:
        return 0.0
    return float(np.sum((x - x_mean) * (y - y_mean)) / denom)


def _correlation(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson 상관계수."""
    if len(a) != len(b) or len(a) < 2:
        return 0.0
    std_a = np.std(a)
    std_b = np.std(b)
    if std_a == 0 or std_b == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])
