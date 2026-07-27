"""팩터 분해 — book-based 횡단면 SMB/HML/RMW/CMA로 회귀.

학술 근거:
- Fama & French (2015): 5-factor model (MKT, SMB, HML, RMW, CMA)
- Hou, Xue, Zhang (2015): q-factor model (별도 구현 예정, 현재는 FF5만)
- Grinold & Kahn (2000), *Active Portfolio Management* Ch.5-7:
  Information Ratio (알파/추적오차) + Fundamental Law + Residual Risk. 팩터 제거
  후 잔여 수익 시계열을 IR 원료로 사용한다.
  IR/Fundamental Law: `quant/strategy/metrics.py`.
  Residual Risk Decomposition: 이 파일 하단 (quant 엔진 내부).

데이터 흐름:
1. factorBuild.buildFactors(market) — scan finance.parquet에서 5분위 포트폴리오
   구성, 동일가중 평균 일별 log return → SMB/HML/RMW/CMA 시계열
2. decomposeFactor — 단일 종목 vs (MKT + 빌드된 팩터) 다변수 OLS

이전 버전(2026-04-06 이전)은 변동성 합성 가짜 프록시를 사용했고 audit에서 진짜
SMB와 음의 상관(−0.51)이 발견됨. 이번 재구현으로 폐기. 자세한 내용은
data/dart/auditQuant/factor.md 참조.

⚠️ 한계:
- size proxy = book equity (시가총액 데이터 미수집). 시총 인프라 추가 후 진짜 시총으로 교체.
- BM proxy = equity/assets. 시총 부재로 진짜 BM 불가.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from dartlab.core.market import resolveMarket
from dartlab.core.memory import withMemoryBudget
from dartlab.core.polarsUtil import isEmptyDf
from dartlab.quant.screen.dataAccess import fetchOhlcv, ohlcvToArrays
from dartlab.quant.strategy.metrics import TRADING_DAYS, calcIR, fundamentalLawIR

log = logging.getLogger(__name__)


def decomposeFactor(stockCode: str, *, market: str = "auto", **kwargs: Any) -> dict:
    """진짜 횡단면 팩터 시계열로 단일 종목 회귀.

    Capabilities:
        - FF5 (MKT/SMB/HML/RMW/CMA) 또는 fallback CAPM 다변수 회귀 → 팩터 로딩 + alpha
        - Grinold/Kahn IR (raw/annualized/expected) + Ch.7 risk decomposition (systematic/residual)

    Args:
        stockCode: 종목코드 또는 ticker.
        market: ``"KR"`` | ``"US"`` | ``"auto"``.
        **kwargs: ``start/end/benchmark/benchmarkMode`` 등.

    Returns:
        dict — 로딩/alpha/R²/IR/risk decomposition/factor 기여도/interpretation.
        ``"error"`` 키 = 데이터 부족.

    Guide:
        Fama-French 2015 표준 + Grinold-Kahn Active Portfolio Management. US 는 현재 FF5
        미빌드 → CAPM fallback. ``dataAdequacy="low"`` 면 회귀 신뢰도 ↓.

    When:
        Quant factor 분해 + AI "이 종목 어느 팩터에 노출" 답변.

    How:
        OHLCV+benchmark fetch → log return → factors load → ``_multiOls`` → IR + 위험 분해.

    Requires:
        OHLCV ≥ 60 봉 + 벤치마크 가용 + (KR 한정) ``buildFactors`` 빌드 완료.

    Raises:
        없음 — 데이터 부족·벤치 없음 시 ``{"error": ...}`` 반환.

    Example:
        >>> r = decomposeFactor("005930", market="KR")
        >>> r["model"], r["informationRatioAnnualized"]
        ('FF5-real', 0.42)

    See Also:
        - buildFactors : factor 시계열 빌드
        - decomposeRisk : 위험 분해
        - factorExposureLimits : 한도 체크

    AIContext:
        "이 종목 팩터 노출" 답변 시 top loading + alpha + IR 인용.
    """
    market = resolveMarket(stockCode, market)
    benchmark = kwargs.pop("benchmark", None)
    benchmarkMode = kwargs.pop("benchmarkMode", "market")

    ohlcv = fetchOhlcv(stockCode, **kwargs)
    if isEmptyDf(ohlcv):
        return {"error": f"{stockCode} 주가 데이터 없음"}
    arr = ohlcvToArrays(ohlcv)
    close = arr.get("close")
    if close is None or len(close) < 60:
        return {"error": f"{stockCode} 데이터 부족 (최소 60일)"}
    stockRet = np.diff(np.log(close))

    from dartlab.quant.benchmark.data import fetchBenchmarkOhlcv

    bench, benchmark_meta = fetchBenchmarkOhlcv(
        stockCode,
        market=market,
        benchmark=benchmark,
        benchmarkMode=benchmarkMode,
        start=kwargs.get("start"),
        end=kwargs.get("end"),
        returnMeta=True,
    )
    if isEmptyDf(bench):
        return {"error": "벤치마크 데이터 없음"}
    bench_close = ohlcvToArrays(bench).get("close")
    if bench_close is None:
        return {"error": "벤치마크 close 없음"}
    benchRet = np.diff(np.log(bench_close))

    # 진짜 횡단면 팩터 시계열 빌드/로드
    if market == "KR":
        from dartlab.quant.factor.build import buildFactors

        factors = buildFactors(market)
    else:
        factors = None  # US는 후순위

    if factors is None:
        # fallback: 1-factor CAPM (MKT만)
        out = _capmFallback(stockCode, market, stockRet, benchRet)
        if "error" not in out:
            out["benchmarkUsed"] = benchmark_meta
        return out

    smb = factors["smb"]
    hml = factors["hml"]
    rmw = factors.get("rmw")
    cma = factors.get("cma")

    # 길이 정렬
    ml = min(len(stockRet), len(benchRet), len(smb), len(hml))
    if rmw is not None:
        ml = min(ml, len(rmw))
    if cma is not None:
        ml = min(ml, len(cma))
    if ml < 30:
        return {"error": f"공통 기간 부족 ({ml}일)"}

    y = stockRet[-ml:]
    cols = [benchRet[-ml:], smb[-ml:], hml[-ml:]]
    names = ["MKT", "SMB", "HML"]
    if rmw is not None:
        cols.append(rmw[-ml:])
        names.append("RMW")
    if cma is not None:
        cols.append(cma[-ml:])
        names.append("CMA")

    X = np.column_stack(cols)
    betas, alpha_val, r2, t_stats, residuals = _multiOls(y, X)

    # Grinold/Kahn Ch.5 — raw IR = mean(residual alpha) / std(residual alpha)
    # residuals 는 팩터 제거 후 잔여 일별 수익 (raw 알파 시계열)
    rawIR = calcIR(residuals) if residuals is not None else float("nan")
    annualizedIR = float(rawIR * np.sqrt(252)) if not np.isnan(rawIR) else float("nan")
    # Fundamental Law 이론 IR (raw IR 을 연간 breadth=252 독립 관측으로 취급할 때의 기대치)
    expectedIR = fundamentalLawIR(rawIR, 252) if not np.isnan(rawIR) else float("nan")

    # Grinold Ch.7 — systematic / residual risk 분해
    riskDecomp = decomposeRisk(
        returns=y,
        factorExposures=betas,
        factorReturns=X,
        annualize=True,
    )
    # residual α series IR (연환산 포함)
    resAlpha = residualAlphaIR(residuals) if residuals is not None else None

    result: dict = {
        "stockCode": stockCode,
        "market": market,
        "model": f"FF{len(names)}-real" if rmw is not None and cma is not None else f"FF{len(names)}",
        "dataPoints": int(ml),
        "dataAdequacy": "low" if ml < 252 else "ok",
        "alpha": round(float(alpha_val * 252), 4),
        "rSquared": round(float(r2), 4),
        "informationRatio": round(float(rawIR), 4) if not np.isnan(rawIR) else None,
        "informationRatioAnnualized": round(float(annualizedIR), 4) if not np.isnan(annualizedIR) else None,
        "expectedIR": round(float(expectedIR), 4) if not np.isnan(expectedIR) else None,
        # Grinold Ch.7 — risk decomposition
        "systematicRisk": round(float(riskDecomp["systematicRisk"]), 4),
        "residualRisk": round(float(riskDecomp["residualRisk"]), 4),
        "totalRisk": round(float(riskDecomp["totalRisk"]), 4),
        "systematicShare": round(float(riskDecomp["systematicShare"]), 4),
        "residualShare": round(float(riskDecomp["residualShare"]), 4),
        "trackingError": round(float(riskDecomp["trackingError"]), 4),
        # residual alpha stats
        "alphaAnnual": round(float(resAlpha["alpha"]), 4) if resAlpha else None,
        "factorYear": factors["year"],
        "factorUniverse": factors["universe"],
        "factorNotes": factors.get("notes"),
        "benchmarkUsed": benchmark_meta,
    }

    for i, name in enumerate(names):
        result[name] = {
            "loading": round(float(betas[i]), 4),
            "tstat": round(float(t_stats[i]), 2) if t_stats is not None else None,
        }

    # 팩터 기여도 (연환산)
    contributions = {}
    for i, name in enumerate(names):
        contributions[name] = round(float(betas[i] * np.mean(X[:, i]) * 252), 4)
    result["contributions"] = contributions

    result["interpretation"] = _interpret(result, names)

    return result


def factorExposureLimits(loadings: dict, *, limits: dict | None = None) -> dict:
    """팩터 익스포저 한도 체크 (책 7장 — 팩터 리스크 관리).

    Capabilities:
        - |loading| > limit 팩터 식별 + 초과분 반대 방향 hedgeSize 계산
        - 기본 한도: MKT 1.5, 나머지 0.5 (보수적)

    Args:
        loadings: ``{factor_name: {loading: float, tstat: float}}`` (decomposeFactor 항목).
        limits: ``{factor_name: max_abs}``. None 이면 기본값.

    Returns:
        dict — limits/breaches/compliant.

    Guide:
        Grinold-Kahn Ch.7. 팩터 위험 관리. breaches 가 있으면 hedge vehicle 로 |loading|
        한도 이내로 조정.

    When:
        팩터 노출 한도 검증 + AI "팩터 베팅 위험" 답변.

    How:
        limits 순회 → |loading| vs limit → 초과 시 hedgeSize = -(loading - sign×lim).

    Requires:
        decomposeFactor 결과의 팩터 dict.

    Raises:
        없음.

    Example:
        >>> r = factorExposureLimits(decomposed_loadings)
        >>> r["compliant"]
        False

    See Also:
        - decomposeFactor : loadings 산출
        - hedgeRatio : 헤지 비율

    AIContext:
        "팩터 위험 한도 초과" 답변 시 breach factor + hedgeSize 인용.
    """
    if limits is None:
        # 기본: MKT 1.5, 나머지 0.5 (보수적)
        limits = {"MKT": 1.5, "SMB": 0.5, "HML": 0.5, "RMW": 0.5, "CMA": 0.5}

    breaches = []
    for name, lim in limits.items():
        info = loadings.get(name)
        if not isinstance(info, dict):
            continue
        ld = float(info.get("loading", 0))
        if abs(ld) > lim:
            # 헤지: 초과분만큼 반대 방향
            hedge_size = -(ld - np.sign(ld) * lim)
            breaches.append(
                {
                    "factor": name,
                    "loading": ld,
                    "limit": lim,
                    "excess": round(ld - np.sign(ld) * lim, 4),
                    "hedgeSize": round(float(hedge_size), 4),
                }
            )

    return {"limits": limits, "breaches": breaches, "compliant": len(breaches) == 0}


def hedgeRatio(targetLoading: float, hedgeLoading: float) -> float:
    """단일 팩터 헤지비율 — target / hedge.

    예: 포트의 SMB loading +0.8을 헤지하려면 SMB-vehicle의 SMB loading이
    +1.0인 경우 hedgeRatio = -0.8 (포트 1당 hedge -0.8).

    Requires:
        target/hedge 팩터 loading 값 (calcExposure 출력).

    Raises:
        없음 — hedgeLoading 0 면 0.0 반환.
    """
    if hedgeLoading == 0:
        return 0.0
    return float(-targetLoading / hedgeLoading)


# ══════════════════════════════════════════════════════════════════════
# Grinold Ch.7 — Residual Risk Model
# ══════════════════════════════════════════════════════════════════════
#
#     Total risk² = Systematic risk² + Residual risk²
#
# systematic = factor exposure 에서 오는 리스크 (hedgeable)
# residual = 종목 고유 (idiosyncratic). IR 의 분모 = tracking error.


def decomposeRisk(
    *,
    returns: np.ndarray,
    factorExposures: np.ndarray,
    factorReturns: np.ndarray,
    annualize: bool = True,
) -> dict:
    """Grinold Ch.7 — systematic / residual 리스크 분해.

    Total risk² = Systematic risk² + Residual risk². systematic = factor exposure 에서
    오는 리스크 (hedgeable). residual = 종목 고유 (idiosyncratic). IR 의 분모 = tracking error.

    Capabilities:
        - 종목 returns 를 systematic (F @ β) + residual 로 분해 → 각 표준편차 + share
        - annualize=True 시 √252 곱 (Trading Days)

    Args:
        returns: 종목 일별 수익률 (T,).
        factorExposures: β 벡터 (K,).
        factorReturns: F 매트릭스 (T × K).
        annualize: True 면 √252 곱. 기본 True.

    Returns:
        dict — systematicRisk/residualRisk/totalRisk/systematicShare/residualShare/trackingError.

    Guide:
        Grinold-Kahn Ch.7 표준. residualShare ≥ 0.6 = 종목 alpha 비중 큼 (factor 비의존).

    When:
        포트 risk 분해 + AI "팩터 위험 vs 종목 위험" 답변.

    How:
        sys_series = F @ β, residual = y - sys_series → var → annualized risk.

    Requires:
        returns 와 factorReturns 행 길이 정합 + factorExposures K 일치.

    Raises:
        없음 — 길이 불일치 시 NaN dict.

    Example:
        >>> r = decomposeRisk(returns=y, factorExposures=betas, factorReturns=X)
        >>> r["residualShare"]
        0.42

    See Also:
        - decomposeFactor : β 산출
        - residualRiskForecast : EWMA 예측
        - residualAlphaIR : 잔여 alpha IR

    AIContext:
        "위험 분해 결과 systematic vs residual" 답변 시 share 인용.
    """
    y = np.asarray(returns, dtype=float)
    beta = np.asarray(factorExposures, dtype=float)
    F = np.asarray(factorReturns, dtype=float)
    if F.ndim == 1:
        F = F.reshape(-1, 1)
    if y.size < 2 or F.shape[0] != y.size:
        return {
            "systematicRisk": float("nan"),
            "residualRisk": float("nan"),
            "totalRisk": float("nan"),
            "systematicShare": float("nan"),
            "residualShare": float("nan"),
            "trackingError": float("nan"),
        }
    sys_series = F @ beta
    residual = y - sys_series
    sys_var = float(np.var(sys_series, ddof=1))
    res_var = float(np.var(residual, ddof=1))
    total_var = sys_var + res_var
    scale = np.sqrt(TRADING_DAYS) if annualize else 1.0
    sys_risk = float(np.sqrt(max(sys_var, 0.0)) * scale)
    res_risk = float(np.sqrt(max(res_var, 0.0)) * scale)
    total_risk = float(np.sqrt(max(total_var, 0.0)) * scale)
    sysShare = float(sys_var / total_var) if total_var > 0 else float("nan")
    res_share = 1.0 - sysShare if not np.isnan(sysShare) else float("nan")
    return {
        "systematicRisk": sys_risk,
        "residualRisk": res_risk,
        "totalRisk": total_risk,
        "systematicShare": sysShare,
        "residualShare": res_share,
        "trackingError": res_risk,
    }


def residualRiskForecast(
    historicalResidual: np.ndarray,
    horizonDays: int = 252,
    halfLifeDays: int = 60,
) -> float:
    """EWMA 기반 잔여 변동성 예측 (Grinold Ch.7 권고).

    Capabilities:
        - 잔여 수익률 시계열에 EWMA (halfLife) 적용 → 가중 평균/분산 → horizon 변동성
        - 표본 < 10 시 NaN 반환

    Args:
        historicalResidual: 팩터 제거 후 잔여 일별 수익률 시계열.
        horizonDays: 예측 기간 (일). 기본 ``252`` (1년).
        halfLifeDays: EWMA 반감기 (일). 기본 ``60``.

    Returns:
        float — horizonDays 기간 잔여 변동성 예측치 (%). 표본 < 10 → NaN.

    Guide:
        Grinold Ch.7 권고 EWMA. halfLife 짧으면 (30) 변동성 변화에 민감, 길면 (120) 안정적.

    When:
        Forward-looking IR 추정 + AI 미래 변동성 답변.

    How:
        ``lam = 0.5^(1/halfLife)`` → exponential weights → 가중 평균/분산 → √(var × horizon).

    Requires:
        historicalResidual 표본 ≥ 10.

    Raises:
        없음.

    Example:
        >>> residualRiskForecast(residuals, horizonDays=252, halfLifeDays=60)
        0.18

    See Also:
        - decomposeRisk : 분해
        - residualAlphaIR : IR

    AIContext:
        "내년 1 년 잔여 변동성 예측" 답변에 인용.
    """
    r = np.asarray(historicalResidual, dtype=float)
    r = r[~np.isnan(r)]
    if r.size < 10:
        return float("nan")
    lam = 0.5 ** (1.0 / halfLifeDays)
    weights = lam ** np.arange(r.size - 1, -1, -1)
    weights /= weights.sum()
    mu = float(np.sum(weights * r))
    var = float(np.sum(weights * (r - mu) ** 2))
    return float(np.sqrt(var * horizonDays))


def residualAlphaIR(residualSeries: np.ndarray, *, annualize: bool = True) -> dict:
    """Grinold 잔여 시계열로부터 raw IR + 연환산 alpha/trackingError.

    Capabilities:
        - 잔여 시계열의 mean/std → rawIR + 연환산 IR + alpha + trackingError 4 통합 지표
        - annualize=False 시 일별 raw 값만 반환

    Args:
        residualSeries: 팩터 제거 후 잔여 일별 수익률 시계열.
        annualize: True 면 √252 곱. 기본 True.

    Returns:
        dict — rawIR/annualizedIR/alpha/trackingError. 표본 < 2 시 NaN dict.

    Guide:
        Grinold-Kahn Ch.5 IR 정의. IR ≥ 0.5 = good, ≥ 1.0 = exceptional alpha.

    When:
        팩터 제거 후 alpha 평가 + AI "이 종목 alpha 얼마" 답변.

    How:
        mu = mean, sd = std, raw_ir = mu/sd. annualize → scale × √252.

    Requires:
        residualSeries 표본 ≥ 2 + std > 0.

    Raises:
        없음.

    Example:
        >>> r = residualAlphaIR(residuals)
        >>> r["annualizedIR"]
        0.42

    See Also:
        - decomposeRisk : 분해 + tracking error
        - strategy.metrics.calcIR : daily IR helper

    AIContext:
        "이 종목 alpha 와 추적오차" 답변 시 alpha + trackingError 인용.
    """
    r = np.asarray(residualSeries, dtype=float)
    r = r[~np.isnan(r)]
    if r.size < 2:
        return {
            "rawIR": float("nan"),
            "annualizedIR": None,
            "alpha": float("nan"),
            "trackingError": float("nan"),
        }
    mu = float(r.mean())
    sd = float(r.std(ddof=1))
    raw_ir = mu / sd if sd > 0 else 0.0
    scale = np.sqrt(TRADING_DAYS) if annualize else 1.0
    return {
        "rawIR": float(raw_ir),
        "annualizedIR": float(raw_ir * np.sqrt(TRADING_DAYS)) if annualize else None,
        "alpha": float(mu * TRADING_DAYS) if annualize else float(mu),
        "trackingError": float(sd * scale),
    }


from dartlab.quant.factor._calcRegression import (
    _capmFallback,
    _interpret,
    _multiOls,
)

# ══════════════════════════════════════════════════════════════════════
# Phase B0 — Alphalens-style Factor Tear Sheet (story 시장분석 섹션)
# ══════════════════════════════════════════════════════════════════════
# ── calcFactorTearSheet + calcMultiFactorRisk + calcFactorTearSheetAll → _calcTearsheet.py 분리 ──
from dartlab.quant.factor._calcTearsheet import (  # noqa: E402, F401
    calcFactorTearSheet,
    calcFactorTearSheetAll,
    calcMultiFactorRisk,
)
