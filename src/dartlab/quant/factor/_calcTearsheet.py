"""quant/factor/calc.py tearsheet + multi-factor risk 분리.

calc.py 693 줄 분할. calcFactorTearSheet (129) + calcMultiFactorRisk (139) +
calcFactorTearSheetAll (46) 합 약 316 줄. calc.py 의 facade (decomposeFactor +
factorExposureLimits + hedgeRatio + decomposeRisk + residualRiskForecast +
residualAlphaIR) 책임 유지.

BC: factor.calc 모듈에서 3 함수 모두 import 가능 (re-export).
순환 import 회피: decomposeFactor · decomposeRisk · residualAlphaIR · residualRiskForecast
는 함수 내부 lazy import.
"""

from __future__ import annotations

import logging

import numpy as np

from dartlab.core.market import resolveMarket
from dartlab.core.memory import withMemoryBudget
from dartlab.core.polarsUtil import isEmptyDf
from dartlab.quant.factor._calcRegression import _interpretFactorSharpe, _interpretRiskDecomp
from dartlab.quant.screen.dataAccess import fetchOhlcv, ohlcvToArrays
from dartlab.quant.strategy.metrics import TRADING_DAYS, calcIR, fundamentalLawIR


def _lazyDecomposeFactor(*args, **kwargs):
    """lazy proxy → factor.calc.decomposeFactor (순환 import 회피)."""
    from dartlab.quant.factor.calc import decomposeFactor

    return decomposeFactor(*args, **kwargs)


log = logging.getLogger(__name__)


def calcFactorTearSheet(
    factorName: str = "smb",
    *,
    market: str = "KR",
) -> dict | None:
    """팩터 tear sheet — long-short 시계열의 Sharpe / 누적수익 / MDD / Win Rate (Alphalens 표준).

    Capabilities:
        - 4 표준 Fama-French 팩터 (smb / hml / rmw / cma) 의 정량 평가 metric
        - Long-short 일별 시계열 (factorBuild.buildFactors) 기반
        - 연환산 수익 / 변동성 / Sharpe / 누적수익 / Win Rate / Max Drawdown
        - 실/proxy 구분 (isRealFamaFrench) 노출 — KRX 시총 직접 vs book proxy

    AIContext:
        - story 6막-3 시장분석 섹션이 자동 호출 (`factorTearSheetBlock`)
        - 4 팩터 동시 평가로 한국 시장 알파 원천 정량화
        - Sharpe > 1.0 = 강한 alpha, > 0.5 = 약한 alpha, < 0 = 역방향

    Guide:
        - "size 팩터 평가" → calcFactorTearSheet("smb")
        - "value 팩터" → calcFactorTearSheet("hml")
        - "quality 팩터" → calcFactorTearSheet("rmw")
        - "investment 팩터" → calcFactorTearSheet("cma")

    See Also:
        - factorBuild.buildFactors : SMB/HML/RMW/CMA 시계열 빌드
        - decomposeFactor : 단일 종목 FF5 회귀 (loadings)
        - calcStrategySnapshot : 8 검증 스타일 백테스트

    When:
        Alphalens 팩터 평가 + AI 한국 시장 알파 원천 답변.

    How:
        buildFactors → 일별 long-short 시계열 → 연환산 수익/변동성/Sharpe/MDD/
        Win Rate.

    Requires:
        scan finance.parquet + 일별 OHLCV (해당 연도).

    Raises:
        없음 — 실패는 None.

    Args:
        factorName: ``"smb"`` | ``"hml"`` | ``"rmw"`` | ``"cma"`` (대소문자 무관). 기본 ``"smb"``.
        market: ``"KR"`` | ``"US"``. 기본 ``"KR"``.

    Returns:
        dict
            factorName : str — 팩터명 (대문자, 예: "SMB")
            market : str — "KR" / "US"
            year : str — fundamental 기준 연도
            universe : int — 종목 수
            nObs : int — 일별 시계열 관측 수 (거래일)
            longShortAnnualReturn : float — Long-short 연환산 수익 (%)
            longShortAnnualVol : float — 연환산 변동성 (%)
            longShortSharpe : float — Sharpe ratio (배, mean/std × √252)
            longShortCumReturn : float — 누적 수익 (%, 전기간)
            longShortWinRate : float — 양수 일자 비율 (%)
            maxDrawdown : float — 최대낙폭 (%, 음수)
            sizeSource : str — "KRX_MKTCAP" 또는 "book_equity_proxy"
            bmSource : str — "equity/marketCap" 또는 "equity/assets_proxy"
            isRealFamaFrench : bool — KRX 시총 기반 진짜 FF 인지
            highN : int | None — Long 종목 수 (HML 의 경우 high-BM, 그 외 N/A)
            lowN : int | None — Short 종목 수
            interpretation : str — 정성 평가 ("강한 alpha (소형주 프리미엄)" 등)
            notes : str — 데이터 source 안내

    Examples:
        >>> from dartlab.quant.factor.calc import calcFactorTearSheet
        >>> ts = calcFactorTearSheet("smb")
        >>> print(ts["longShortSharpe"], ts["interpretation"])
        0.85 약한 alpha (소형주 프리미엄)

    Notes:
        - Alphalens-style 표준 metric. 단 Cross-sectional IC (mean / std / IR) 는 별도 트랙
          (현재는 long-short 기반 단순 metric — 후속 강화).
        - Sharpe 는 risk-free 0 가정 (한국 시장 단기 RF 무시).
        - Max Drawdown 은 누적 (1+r) 시계열의 peak-to-trough.
        - factorBuild.buildFactors() 가 캐시 → 같은 세션 재호출 빠름.
    """
    fname = factorName.lower().strip()
    if fname not in {"smb", "hml", "rmw", "cma"}:
        raise ValueError(f"factorName 알 수 없음: {factorName!r} — 허용: smb, hml, rmw, cma")

    from dartlab.quant.factor.build import buildFactors

    fb = buildFactors(market)
    if fb is None:
        return None
    arr = fb.get(fname)
    if arr is None or len(arr) < 30:
        return None

    arr = np.asarray(arr, dtype=np.float64)
    arr = arr[~np.isnan(arr)]
    if len(arr) < 30:
        return None

    annualMean = float(np.mean(arr) * 252) * 100
    annualStd = float(np.std(arr, ddof=1) * np.sqrt(252)) * 100
    sharpe = annualMean / annualStd if annualStd > 0 else 0.0
    cumReturn = float(np.exp(np.sum(arr)) - 1) * 100
    winRate = float(np.mean(arr > 0)) * 100

    # Max Drawdown
    cum = np.cumprod(1 + arr)
    peak = np.maximum.accumulate(cum)
    dd = (cum - peak) / peak
    maxDD = float(np.min(dd)) * 100

    # 종목 수 — 팩터별 다름
    longN = lowN = None
    if fname == "smb":
        longN, lowN = fb.get("smallN"), fb.get("bigN")
    elif fname == "hml":
        longN, lowN = fb.get("highBmN"), fb.get("lowBmN")

    return {
        "factorName": fname.upper(),
        "market": market,
        "year": fb.get("year"),
        "universe": fb.get("universe"),
        "nObs": int(len(arr)),
        "longShortAnnualReturn": round(annualMean, 2),
        "longShortAnnualVol": round(annualStd, 2),
        "longShortSharpe": round(sharpe, 2),
        "longShortCumReturn": round(cumReturn, 2),
        "longShortWinRate": round(winRate, 2),
        "maxDrawdown": round(maxDD, 2),
        "sizeSource": fb.get("sizeSource"),
        "bmSource": fb.get("bmSource"),
        "isRealFamaFrench": bool(fb.get("isRealFamaFrench", False)),
        "highN": longN,
        "lowN": lowN,
        "interpretation": _interpretFactorSharpe(sharpe, fname),
        "notes": fb.get("notes", ""),
    }


@withMemoryBudget(limitMb=300)
def calcMultiFactorRisk(stockCode: str, *, market: str = "auto") -> dict | None:
    """Multi-Factor Risk Decomposition — Barra-style B Σ_f Bᵀ + D 분해.

    Capabilities:
        단일 종목의 총 리스크를 4 팩터 (SMB/HML/RMW/CMA) 공분산 행렬과 노출 (loadings) 의
        quadratic form 으로 systematic 부분과 idiosyncratic (residual) 부분으로 분해. 팩터별
        marginal contribution 까지 산출해 "어느 팩터가 위험 주범" 인지 정량.

    Parameters
    ----------
    stockCode : str
        종목코드 (KR 6 자리 또는 US ticker).
    market : str, default "auto"
        "KR" | "US" | "auto".

    Returns
    -------
    dict | None
        stockCode : str — 입력 echo
        market : str — 해석된 시장
        model : str — "Barra-style FF4 Multi-Factor"
        systematicRisk : float — 팩터 기여 리스크 (연환산 %)
        residualRisk : float — 고유 리스크 (idiosyncratic, 연환산 %)
        totalRisk : float — 합산 (연환산 %)
        systematicShare : float — systematic 비중 (% of total variance)
        factorContributions : dict[str, float] — 팩터별 기여 (% of systematic)
        loadings : dict[str, float] — B 벡터 (팩터별 노출)
        interpretation : str — 정성 평가 ("SMB 의존 강한 소형주" 등)
        decompose 실패 시 error dict 반환.

    Raises
    ------
    없음 (오류는 dict["error"]).

    Example
    -------
    >>> r = calcMultiFactorRisk("005930")
    >>> r["systematicShare"], r["factorContributions"]["SMB"]
    (72.4, 41.8)

    Guide
    -----
    sys_var = B^T Σ_f B (quadratic form). 팩터별 기여 = B_k × (Σ_f B)_k / sys_var 의 marginal
    contribution. systematicShare 가 50% 미만이면 종목 고유 변동 우세 — alpha 분석 우선.
    50% 이상이면 팩터 의존 — factorContributions 최대값을 헤지 대상으로 선택.

    See Also:
        - ``dartlab.quant.factor.calc.decomposeFactor`` : loadings (B) 본체
        - ``dartlab.quant.factor.calc.calcFactorTearSheet`` : 팩터별 Sharpe
        - ``dartlab.quant.factor.residual.calcResidual`` : 잔여 alpha

    When:
        Barra-style 리스크 분해 진입점 + AI 팩터 노출 답변.

    How:
        decomposeFactor (loadings B) → buildFactors (시계열) → Σ_f → B^T Σ_f B
        quadratic → 팩터별 marginal contribution.

    Requires
    --------
    - L1 gather: 주가 OHLCV 60 거래일 이상
    - L1.5 frame: factor build 결과 (SMB/HML/RMW/CMA 시계열)

    AIContext
    ---------
    "총 리스크 30% 중 systematic 22% / idiosyncratic 8%, SMB +45%" 같은 정량 답변 진입점.
    systematicShare 단독 인용보다 최대 factor contribution 까지 한 줄로 묶어 인용 권장.
    """
    decomp = _lazyDecomposeFactor(stockCode, market=market)
    if not decomp or "error" in decomp:
        return decomp

    from dartlab.quant.factor.build import buildFactors

    actual_market = decomp.get("market", market)
    fb = buildFactors(actual_market)
    if fb is None:
        return None

    # 팩터 시계열 stack (사용 가능한 팩터만)
    factor_arrays = []
    factor_names = []
    for name in ("smb", "hml", "rmw", "cma"):
        arr = fb.get(name)
        if arr is not None:
            factor_arrays.append(np.asarray(arr, dtype=np.float64))
            factor_names.append(name.upper())
    if not factor_arrays:
        return None

    ml = min(len(a) for a in factor_arrays)
    if ml < 30:
        return None
    F = np.column_stack([a[-ml:] for a in factor_arrays])  # T × K
    Sigma_f = np.cov(F.T, ddof=1) * 252  # K × K (annualized)

    # 종목의 팩터 노출 B (decomposeFactor loadings)
    loadings = []
    for name in factor_names:
        info = decomp.get(name)
        if isinstance(info, dict):
            loadings.append(float(info.get("loading", 0.0)))
        else:
            loadings.append(0.0)
    B = np.array(loadings, dtype=np.float64)

    # systematic variance = B^T Σ_f B (연환산)
    sys_var = float(B @ Sigma_f @ B)
    sys_var = max(sys_var, 0.0)
    sys_risk_pct = float(np.sqrt(sys_var)) * 100  # %

    # residual = decomposeFactor 의 residualRisk (이미 annualized 비율)
    res_risk_raw = float(decomp.get("residualRisk", 0.0))
    res_var = res_risk_raw**2  # variance
    res_risk_pct = res_risk_raw * 100  # %

    total_var = sys_var + res_var
    total_risk_pct = float(np.sqrt(total_var)) * 100  # %
    sysShare = (sys_var / total_var * 100) if total_var > 0 else 0.0

    # 팩터별 marginal contribution = B_k × (Σ_f B)_k / sys_var
    Sigma_f_B = Sigma_f @ B
    factorContrib: dict[str, float] = {}
    for i, name in enumerate(factor_names):
        marginal = float(Sigma_f_B[i]) * float(B[i])
        contrib = (marginal / sys_var * 100) if sys_var > 0 else 0.0
        factorContrib[name] = round(contrib, 1)

    return {
        "stockCode": stockCode,
        "market": actual_market,
        "model": f"Barra-style FF{len(factor_names)} Multi-Factor",
        "systematicRisk": round(sys_risk_pct, 2),
        "residualRisk": round(res_risk_pct, 2),
        "totalRisk": round(total_risk_pct, 2),
        "systematicShare": round(sysShare, 1),
        "factorContributions": factorContrib,
        "loadings": {n: round(float(B[i]), 3) for i, n in enumerate(factor_names)},
        "interpretation": _interpretRiskDecomp(sysShare, factorContrib),
    }


@withMemoryBudget(limitMb=500)
def calcFactorTearSheetAll(*, market: str = "KR") -> dict | None:
    """4 표준 팩터 (SMB/HML/RMW/CMA) 의 tear sheet 종합 — story 시장분석 섹션 자동 사용.

    Capabilities:
        - 4 팩터 동시 평가 (한 번 buildFactors 호출 후 4개 metric)
        - 각 팩터의 Sharpe 비교 → 한국 시장 강한 alpha 원천 즉시 식별
        - story 의 ``factorTearSheetBlock`` 가 직접 호출

    Args:
        market: ``"KR"`` | ``"US"``. 기본 ``"KR"``.

    Returns:
        dict
            market : str
            year : str
            universe : int
            isRealFamaFrench : bool
            factors : list[dict] — 각 dict 는 calcFactorTearSheet 결과
            strongest : str | None — 가장 강한 |Sharpe| 팩터명
            interpretation : str — 종합 정성 평가

    Guide:
        story 시장분석 블록 표준 진입. KR 4 팩터 (SMB/HML/RMW/CMA) 동시 평가 + 강한 팩터
        식별. US 는 아직 buildFactors 미빌드.

    When:
        Story factor tearsheet 블록 + AI "가장 강한 팩터" 답변.

    How:
        4 팩터 순회 → calcFactorTearSheet → max(|Sharpe|) 선정.

    Requires:
        ``buildFactors`` KR 완료 + 4 팩터 시계열 가용.

    Raises:
        없음 — 데이터 부재 시 None.

    Example:
        >>> r = calcFactorTearSheetAll(market="KR")
        >>> r["strongest"]
        'rmw'

    See Also:
        - calcFactorTearSheet : 단일 팩터
        - buildFactors : 팩터 빌드

    AIContext:
        "한국 시장 가장 강한 팩터" 답변 시 strongest + interpretation 인용.
    """
    factors = []
    for fname in ("smb", "hml", "rmw", "cma"):
        ts = calcFactorTearSheet(fname, market=market)
        if ts is not None:
            factors.append(ts)
    if not factors:
        return None

    strongest = max(factors, key=lambda x: abs(x.get("longShortSharpe", 0)))
    return {
        "market": market,
        "year": factors[0].get("year"),
        "universe": factors[0].get("universe"),
        "isRealFamaFrench": factors[0].get("isRealFamaFrench"),
        "factors": factors,
        "strongest": strongest.get("factorName"),
        "interpretation": (
            f"{market} 시장 가장 강한 팩터: {strongest.get('factorName')} "
            f"(Sharpe={strongest.get('longShortSharpe')}, "
            f"{strongest.get('interpretation')})"
        ),
    }


# IC 평가 함수 — _factorIC.py 분리 (BC: 본 모듈에서 import 가능)
from dartlab.quant.factor._factorIC import _FACTOR_KEY_MAP, calcFactorIC, calcFactorICAll  # noqa: E402, F401
