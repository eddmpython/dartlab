"""Campbell-Hilscher-Szilagyi (2008) 부도확률 모델.

재무제표 + 주가 데이터를 결합한 하이브리드 모델.
"In Search of Distress Risk" Journal of Finance, Dec 2008.

학술적으로 가장 정확한 부도 예측 모델 중 하나.
시계열 부도율 변화를 잘 포착하며, Altman/Ohlson보다 우수한 성능.

입력 변수 (8개):
- NIMTA: Net Income / Market Total Assets
- TLMTA: Total Liabilities / Market Total Assets
- CASHMTA: Cash / Market Total Assets
- SIGMA: Equity Volatility (연환산 일별수익률 표준편차)
- RSIZE: Relative Size = ln(Market Cap / Market Total)
- EXRET: Excess Return (12개월 주가수익률 - 시장수익률)
- MB: Market-to-Book ratio
- PRICE: ln(주가), capped at ln(15)

주가 데이터 없으면 None 반환 (재무제표만으로는 동작 불가).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class CHSResult:
    """CHS 모델 결과."""

    probability: float
    logitScore: float
    zone: str
    interpretation: str

    # 입력 변수 (디버깅/투명성)
    nimta: float | None = None
    tlmta: float | None = None
    cashmta: float | None = None
    sigma: float | None = None
    rsize: float | None = None
    exret: float | None = None
    mb: float | None = None
    price: float | None = None


# Campbell (2008) Table IV, Panel B 계수 (12개월 PD)
_INTERCEPT = -9.164
_COEF_NIMTA = -20.264
_COEF_TLMTA = 1.416
_COEF_CASHMTA = -7.129
_COEF_SIGMA = 1.411
_COEF_RSIZE = -0.045
_COEF_EXRET = -2.132
_COEF_MB = 0.075
_COEF_PRICE = -0.058


def calcCHS(
    netIncome: float | None,
    totalLiabilities: float | None,
    cash: float | None,
    totalAssets: float | None,
    marketCap: float | None,
    equityVolatility: float | None,
    marketTotal: float | None = None,
    excessReturn: float | None = None,
    stockPrice: float | None = None,
) -> CHSResult | None:
    """CHS 부도확률 계산.

    Parameters
    ----------
    netIncome : 당기순이익
    totalLiabilities : 부채총계
    cash : 현금및현금성자산
    totalAssets : 자산총계
    marketCap : 시가총액
    equityVolatility : 주가 변동성 (연환산, 0-1 스케일)
    marketTotal : 시장 전체 시가총액 (RSIZE 계산용, None이면 기본값)
    excessReturn : 12개월 초과수익률 (주가수익률 - 시장수익률, None이면 0)
    stockPrice : 주가 (원, None이면 기본값)

    Returns
    -------
    CHSResult | None
        부도확률 결과. 입력 부족 시 None.
    """
    if any(v is None for v in [netIncome, totalLiabilities, cash, totalAssets, marketCap]):
        return None

    if marketCap <= 0 or totalAssets <= 0:
        return None

    # Market Total Assets = Total Liabilities + Market Cap
    mta = totalLiabilities + marketCap

    if mta <= 0:
        return None

    # 입력 변수 계산
    nimta = netIncome / mta
    tlmta = totalLiabilities / mta
    cashmta = cash / mta

    # 변동성 — 없으면 시장 평균 가정
    sigma = equityVolatility if equityVolatility is not None else 0.40

    # Relative Size — 한국 시장 시가총액 기준
    if marketTotal is None:
        marketTotal = 2_000_000_000_000_000  # 한국 주식시장 ~2000조원 근사
    rsize = math.log(max(marketCap, 1) / marketTotal) if marketTotal > 0 else -10

    # Excess Return — 없으면 0 (neutral)
    exret = excessReturn if excessReturn is not None else 0.0

    # Market-to-Book
    bookEquity = totalAssets - totalLiabilities
    mb = marketCap / bookEquity if bookEquity > 0 else 10.0

    # Price — ln(주가), capped at ln(15)
    if stockPrice is not None and stockPrice > 0:
        priceVar = min(math.log(stockPrice), math.log(15))
    else:
        priceVar = math.log(15)  # cap

    # Logit score
    logit = (
        _INTERCEPT
        + _COEF_NIMTA * nimta
        + _COEF_TLMTA * tlmta
        + _COEF_CASHMTA * cashmta
        + _COEF_SIGMA * sigma
        + _COEF_RSIZE * rsize
        + _COEF_EXRET * exret
        + _COEF_MB * mb
        + _COEF_PRICE * priceVar
    )

    # Probability
    prob = 1 / (1 + math.exp(-logit))
    prob_pct = round(prob * 100, 4)

    # Zone 판정
    if prob_pct < 0.5:
        zone = "safe"
        interp = "CHS 모델 기준 부도 확률 매우 낮음."
    elif prob_pct < 2.0:
        zone = "gray"
        interp = "CHS 모델 기준 부도 확률 보통. 모니터링 필요."
    elif prob_pct < 10.0:
        zone = "distress"
        interp = "CHS 모델 기준 부도 확률 유의미. 재무구조 점검 필요."
    else:
        zone = "distress"
        interp = "CHS 모델 기준 부도 확률 매우 높음. 즉각적 대응 필요."

    return CHSResult(
        probability=prob_pct,
        logitScore=round(logit, 4),
        zone=zone,
        interpretation=interp,
        nimta=round(nimta, 6),
        tlmta=round(tlmta, 4),
        cashmta=round(cashmta, 4),
        sigma=round(sigma, 4),
        rsize=round(rsize, 4),
        exret=round(exret, 4),
        mb=round(mb, 4),
        price=round(priceVar, 4),
    )
