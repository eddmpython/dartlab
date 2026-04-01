"""
실험 ID: 108-005
실험명: 기업 주가 + 재무 교차 — 변동성→할인율, 실측 베타→macroBeta 대체

목적:
- ATR/변동성으로 DCF 할인율 조정 범위 산출 가능한지 검증
- 실측 베타(004에서 검증)가 analysis/valuation에서 쓸 수 있는지 확인
- 매출 시나리오 가중에 주가 추세를 쓸 수 있는지 탐색

가설:
1. 연환산 변동성(일간수익률 표준편차 × √252)이 WACC 할인율 조정에 쓸 수 있음
2. 실측 베타로 CAPM 기대수익률 계산 → 현재 valuation의 WACC와 비교
3. 주가 모멘텀(RSI/SMA 상태) → 시장 기대 방향 → 매출 시나리오 가중

방법:
1. 삼성전자 주가 → 일간수익률 → 연환산 변동성
2. 004에서 산출한 베타 → CAPM: E(R) = Rf + β × (Rm - Rf)
3. analysis/valuation의 현재 WACC/할인율과 비교
4. 3개 종목 확장

결과 (실험 후 작성):
| 종목 | 연환산변동성 | 베타 | CAPM기대수익 | 할인율범위 | 추세 |
|------|-----------|------|-----------|----------|------|
| 삼성전자 | 48.9% | 1.246 | 11.6% | -3~26% | 강세 |
| 카카오 | 53.4% | 0.857 | 9.1% | -7~25% | 약세 |
| 삼성SDI | 58.8% | 1.057 | 10.4% | -7~28% | 강세 |

결론:
- 가설1 부분 채택: 연환산 변동성 49~59% → 변동성 30% 조정 시 할인율 범위 너무 넓음 (음수 발생)
  - **조정 계수를 30%→10%로 줄이면** 실용적 범위: CAPM ± 5%p 정도
  - 또는 변동성 대신 베타만 CAPM에 쓰고, 변동성은 시나리오 폭 결정에 사용
- 가설2 채택: 실측 베타 → CAPM → 기대수익률 10~12% — macroBeta 장애 완전 대체
  - 삼성전자 β=1.25 (시장보다 변동 큼), 카카오 β=0.86 (방어적), 삼성SDI β=1.06 (시장 추종)
  - R²=0.75(삼성전자)는 시장 설명력 매우 높음
- 가설3 확인: 추세 판단(강세/약세)이 시나리오 가중에 쓸 수 있지만, 정량적 가중 공식은 추가 연구 필요
- **실용적 결론**: 베타와 CAPM은 즉시 활용 가능. 변동성 기반 할인율 조정은 계수 튜닝 필요.

실험일: 2026-04-01
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from dartlab.quant import indicators as ind


def _fetchStockPrice(code: str) -> pl.DataFrame | None:
    from dartlab.gather.entry import GatherEntry
    g = GatherEntry()
    try:
        return g("price", code)
    except Exception:
        return None


def _fetchKospi() -> pl.DataFrame:
    import httpx, re
    url = "https://fchart.stock.naver.com/sise.nhn?symbol=KOSPI&timeframe=day&count=300&requestType=0"
    r = httpx.get(url, timeout=15)
    items = re.findall(r'data="([^"]+)"', r.text)
    rows = []
    for item in items:
        parts = item.split("|")
        if len(parts) >= 6:
            try:
                rows.append({
                    "date": f"{parts[0][:4]}-{parts[0][4:6]}-{parts[0][6:8]}",
                    "close": float(parts[4]),
                })
            except ValueError:
                continue
    return pl.DataFrame(rows)


def _calcVolatility(close: np.ndarray) -> dict:
    """일간수익률 → 연환산 변동성."""
    returns = np.diff(close) / close[:-1]
    daily_std = np.std(returns)
    annual_vol = daily_std * np.sqrt(252) * 100
    annual_return = np.mean(returns) * 252 * 100
    return {
        "dailyStd": round(daily_std * 100, 3),
        "annualVol": round(annual_vol, 1),
        "annualReturn": round(annual_return, 1),
    }


def _calcBeta(stock_df: pl.DataFrame, market_df: pl.DataFrame) -> dict:
    """종목 vs 시장 OLS 베타."""
    # 날짜 매칭
    s_dates = set(str(d) for d in stock_df["date"].to_list())
    m_dates = set(str(d) for d in market_df["date"].to_list())
    common = sorted(s_dates & m_dates)
    if len(common) < 30:
        return {"beta": None}

    s = stock_df.with_columns(pl.col("date").cast(pl.Utf8).alias("_d")).filter(pl.col("_d").is_in(common)).sort("_d")
    m = market_df.with_columns(pl.col("date").cast(pl.Utf8).alias("_d")).filter(pl.col("_d").is_in(common)).sort("_d")

    sc = s["close"].to_numpy().astype(np.float64)
    mc = m["close"].to_numpy().astype(np.float64)
    sr = np.diff(sc) / sc[:-1]
    mr = np.diff(mc) / mc[:-1]

    mask = ~(np.isnan(sr) | np.isnan(mr))
    sr, mr = sr[mask], mr[mask]
    if len(sr) < 30:
        return {"beta": None}

    xm, ym = mr.mean(), sr.mean()
    cov = np.sum((mr - xm) * (sr - ym))
    var = np.sum((mr - xm) ** 2)
    beta = cov / var if var > 0 else 0
    return {"beta": round(beta, 3), "nObs": len(sr)}


def main():
    print("=== 108-005: 기업 주가 + 재무 교차 분석 ===\n")

    kospi = _fetchKospi()
    print(f"KOSPI: {kospi.height}일\n")

    # 무위험이자율 (한국 기준금리 proxy)
    Rf = 0.035  # 3.5%
    # 시장 프리미엄 (역사적 평균)
    Rm_minus_Rf = 0.065  # 6.5%

    stocks = [("005930", "삼성전자"), ("035720", "카카오"), ("006400", "삼성SDI")]
    results = {}

    for code, name in stocks:
        print(f"--- {name} ({code}) ---")
        df = _fetchStockPrice(code)
        if df is None or df.is_empty():
            print("  수집 실패")
            continue

        close = df["close"].to_numpy().astype(np.float64)

        # 1. 변동성
        vol = _calcVolatility(close)
        print(f"  변동성: 일간 {vol['dailyStd']}%, 연환산 {vol['annualVol']}%")

        # 2. 실측 베타
        beta_info = _calcBeta(df, kospi)
        beta = beta_info.get("beta")
        print(f"  실측 베타: {beta}")

        # 3. CAPM 기대수익률
        capm = None
        if beta:
            capm = round((Rf + beta * Rm_minus_Rf) * 100, 1)
            print(f"  CAPM 기대수익률: {capm}%  (Rf={Rf*100}% + {beta}×{Rm_minus_Rf*100}%)")

        # 4. 변동성 기반 할인율 범위
        # 저변동성 → 할인율 낮춤, 고변동성 → 할인율 높임
        base_wacc = capm / 100 if capm else 0.10
        vol_adj = vol["annualVol"] / 100 * 0.3  # 변동성의 30%를 조정 폭으로
        wacc_low = round((base_wacc - vol_adj) * 100, 1)
        wacc_high = round((base_wacc + vol_adj) * 100, 1)
        print(f"  할인율 범위: {wacc_low}% ~ {wacc_high}% (CAPM ± 변동성 30%)")

        # 5. 주가 추세 상태
        rsi = ind.vrsi(close, 14)
        sma20 = ind.vsma(close, 20)
        sma60 = ind.vsma(close, 60)
        last_rsi = float(rsi[-1]) if not np.isnan(rsi[-1]) else 50
        above20 = bool(close[-1] > sma20[-1]) if not np.isnan(sma20[-1]) else None
        above60 = bool(close[-1] > sma60[-1]) if not np.isnan(sma60[-1]) else None

        score = 0
        if last_rsi < 30: score += 2
        elif last_rsi < 40: score += 1
        elif last_rsi > 70: score -= 2
        elif last_rsi > 60: score -= 1
        if above20: score += 1
        else: score -= 1
        if above60: score += 1
        else: score -= 1

        verdict = "강세" if score >= 2 else ("약세" if score <= -2 else "중립")
        print(f"  주가 추세: {verdict} (RSI={last_rsi:.0f}, SMA20={'↑' if above20 else '↓'}, SMA60={'↑' if above60 else '↓'})")

        results[code] = {
            "name": name,
            **vol,
            "beta": beta,
            "capm": capm,
            "waccRange": [wacc_low, wacc_high],
            "trend": verdict,
            "trendScore": score,
        }
        print()

    out = {"riskFree": Rf * 100, "marketPremium": Rm_minus_Rf * 100, "stocks": results}
    print(json.dumps(out, ensure_ascii=False, indent=2))

    outPath = Path("experiments/108_quantEngine/005_result.json")
    outPath.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[SAVED] {outPath}")


if __name__ == "__main__":
    main()
