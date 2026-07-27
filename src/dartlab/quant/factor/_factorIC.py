"""calcFactorIC + calcFactorICAll + _FACTOR_KEY_MAP — 팩터 Information Coefficient 평가.

Grinold & Kahn Fundamental Law 의 IC 시계열 산출. KR scan finance.parquet 의 횡단면 데이터로
일별 Spearman IC + ICIR + HitRate 계산. calcFactorIC 단일 팩터 / calcFactorICAll 4 팩터 일괄.

분리 사유: quant/factor/calc.py god module 분리 (963줄 → 단계적 감축).
"""

from __future__ import annotations

import logging

import numpy as np

from dartlab.core.memory import withMemoryBudget
from dartlab.quant.strategy.metrics import TRADING_DAYS

log = logging.getLogger(__name__)

_FACTOR_KEY_MAP = {
    "size": ("marketCap", False),
    "value": ("bookToMarket", True),
    "quality": ("roe", True),
    "investment": ("assetGrowth", False),
    "smb": ("marketCap", False),
    "hml": ("bookToMarket", True),
    "rmw": ("roe", True),
    "cma": ("assetGrowth", False),
}


@withMemoryBudget(limitMb=300)
def calcFactorIC(
    factorName: str = "value",
    *,
    market: str = "KR",
    horizon: int = 1,
    asof: str | None = None,
) -> dict | None:
    """팩터 Information Coefficient — Grinold & Kahn 표준 IC mean/std/ICIR/HitRate.

    Capabilities:
        팩터별 일별 횡단면 Spearman IC 시계열 (corr(factor rank, forward return rank)) 을
        non-overlapping h-일 stepping 으로 산출하고 평균 IC · 표준편차 · ICIR · HitRate ·
        t-stat 까지 단일 dict 로 반환. Alphalens 표준 + Fundamental Law (IR ≈ IC × √breadth)
        의 IC 원료. tear sheet 의 long-short Sharpe 와 독립 평가.

    Parameters
    ----------
    factorName : str, default "value"
        "size" | "value" | "quality" | "investment" (별칭 smb/hml/rmw/cma 허용).
    market : str, default "KR"
        KR 만 지원 (연말 MKTCAP/펀더멘털 SSOT).
    horizon : int, default 1
        forward return 기간 (일). 1 / 5 / 20 권장.

    Returns
    -------
    dict | None
        factorName : str — 대문자 팩터명
        horizon : int — forward return 기간 (일)
        market : str — "KR"
        fundYear : str — 펀더멘털 기준 연도 (전년, look-ahead 방지)
        retYear : str — 수익률 관측 연도 (당해, Q2~Q4)
        nStocks : int — IC 계산 종목 수
        nDays : int — IC 시계열 관측 일 수
        icMean : float — 평균 Spearman IC (-1~1)
        icStd : float — IC 표준편차
        icir : float — IC Information Ratio (연환산)
        hitRate : float — IC > 0 비율 (%)
        tStat : float — icMean × √nDays / icStd
        interpretation : str — 정성 평가
        notes : str — 데이터 source

    Raises
    ------
    ValueError
        factorName 미인식. market != "KR".

    Example
    -------
    >>> ic = calcFactorIC("value", horizon=5)
    >>> ic["icir"], ic["interpretation"]
    (0.42, '중간 예측력 (value)')

    Guide
    -----
    Spearman (rank 기반) — outlier robust. forward return = log(close[t+h]/close[t]). 전년
    연말 펀더멘털 snapshot → 당해 Q2~Q4 으로 look-ahead bias 방지. **non-overlapping h-일
    stepping** 으로 자기상관 제거 + ICIR 인플레이션 방지. 한 시점 cross-section 20 종목
    미만 제외. ICIR = icMean / icStd × √(252/h).

    See Also:
        - ``dartlab.quant.factor.calc.calcFactorTearSheet`` : long-short Sharpe (Alphalens 보완)
        - ``dartlab.quant.factor.calc.decomposeFactor`` : 종목 FF5 loadings
        - ``dartlab.quant.factor.calc.fundamentalLawIR`` : IC + breadth → IR

    When:
        Alphalens IC 표준 진입점 + Fundamental Law IC 원료.

    How:
        scan finance.parquet → 펀더멘털 rank (t-1) + forward return rank (t+h)
        → Spearman IC 시계열 → mean/std/ICIR/HitRate/t-stat.

    Requires
    --------
    - L1.5 scan: finance.parquet (KR)
    - L1 gather: 일별 OHLCV (당해 Q2~Q4)
    - 한 시점 cross-section ≥ 20 종목

    AIContext
    ---------
    "value 팩터가 예측력 있나" 답변 진입점. ICIR > 0.5 = 강한, > 0.3 = 중간, < 0.1 = 노이즈.
    hitRate 와 함께 인용하면 안정성 + 평균치 입체적 답변. horizon 별 비교 (1d/5d/20d) 로
    예측 horizon 답변 가능.
    """
    fname = factorName.lower().strip()
    if fname not in _FACTOR_KEY_MAP:
        raise ValueError(
            f"factorName 알 수 없음: {factorName!r} — 허용: size/value/quality/investment (또는 smb/hml/rmw/cma)"
        )
    metric_key, reverse_sign = _FACTOR_KEY_MAP[fname]

    if market != "KR":
        return None

    try:
        from dartlab.gather.bulkData.hfBulk import loadFiltered
        from dartlab.quant.factor.build import _buildUniverseMetrics, _latestYear
        from dartlab.quant.screen.dataAccess import loadScanParquet
        from dartlab.synth.scanBridge import extractAnnualConsolidated
    except Exception as exc:  # noqa: BLE001
        log.warning("calcFactorIC import 실패: %s", type(exc).__name__)
        return None

    try:
        lf = loadScanParquet("finance", market)
        if lf is None:
            return None
        snap = extractAnnualConsolidated(lf.collect(engine="streaming"))
        year = _latestYear(snap)
        if year is None:
            return None
    except Exception as exc:  # noqa: BLE001
        log.warning("calcFactorIC year 추출 실패: %s", type(exc).__name__)
        return None

    # look-ahead bias 방지: 전년도 펀더멘털 → 당해년도 수익률
    # (전년 12월말 데이터는 당해년도 Q1 이후 공시되므로 실전 예측 가능)
    try:
        fund_year = str(int(str(year)) - 1)
    except ValueError:
        return None
    ret_year = str(year)

    metrics = _buildUniverseMetrics(market, fund_year)
    if len(metrics) < 50:
        return None

    scores = {code: m[metric_key] for code, m in metrics.items() if m.get(metric_key) is not None}
    if len(scores) < 50:
        return None
    if reverse_sign:
        # higher raw = higher factor exposure (good)
        pass

    try:
        long_df = loadFiltered(
            start=f"{ret_year}-04-01",
            end=f"{ret_year}-12-31",
            adjustment="raw",
            asof=asof,
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("calcFactorIC loadFiltered 실패: %s", type(exc).__name__)
        return None
    if long_df is None or long_df.is_empty():
        return None

    import polars as pl

    codes = list(scores.keys())
    sub = long_df.filter(pl.col("ISU_CD").is_in(codes)).select(["BAS_DD", "ISU_CD", "TDD_CLSPRC"])
    if sub.is_empty():
        return None

    wide = sub.pivot(values="TDD_CLSPRC", index="BAS_DD", on="ISU_CD", aggregate_function="first").sort(
        "BAS_DD"
    )  # polars-streaming-unsupported: pivot
    date_col = wide.get_column("BAS_DD").to_numpy()
    stock_cols = [c for c in wide.columns if c != "BAS_DD"]
    if len(stock_cols) < 20:
        return None

    px = wide.select(stock_cols).to_numpy().astype(np.float64)
    # forward log returns horizon h — non-overlapping stepping (자기상관 제거)
    h = max(1, int(horizon))
    if px.shape[0] <= h + 1:
        return None
    start_indices = np.arange(0, px.shape[0] - h, h)
    if len(start_indices) < 10:
        return None
    with np.errstate(divide="ignore", invalid="ignore"):
        fwd = np.log(px[start_indices + h] / px[start_indices])

    score_vec = np.array([scores[c] for c in stock_cols], dtype=np.float64)

    ic_series = []
    for t in range(fwd.shape[0]):
        row = fwd[t]
        valid = np.isfinite(row) & np.isfinite(score_vec)
        if valid.sum() < 20:
            continue
        sr = _rank1d(score_vec[valid])
        rr = _rank1d(row[valid])
        if sr.std() == 0 or rr.std() == 0:
            continue
        ic = float(np.corrcoef(sr, rr)[0, 1])
        if np.isfinite(ic):
            ic_series.append(ic)

    if len(ic_series) < 10:
        return None

    # non-overlapping h-일 IC → 연간 관측 수 = 252/h
    periods_per_year = TRADING_DAYS / h
    ic_arr = np.asarray(ic_series, dtype=np.float64)
    ic_mean = float(ic_arr.mean())
    ic_std = float(ic_arr.std(ddof=1))
    icir = (ic_mean / ic_std * np.sqrt(periods_per_year)) if ic_std > 0 else 0.0
    hit_rate = float((ic_arr > 0).mean()) * 100
    t_stat = ic_mean / (ic_std / np.sqrt(len(ic_arr))) if ic_std > 0 else 0.0

    return {
        "factorName": fname.upper(),
        "horizon": h,
        "market": market,
        "fundYear": fund_year,
        "retYear": ret_year,
        "nStocks": len(stock_cols),
        "nDays": int(len(ic_arr)),
        "icMean": round(ic_mean, 4),
        "icStd": round(ic_std, 4),
        "icir": round(icir, 3),
        "hitRate": round(hit_rate, 2),
        "tStat": round(float(t_stat), 2),
        "interpretation": _interpretIC(icir, fname, nDays=len(ic_arr)),
        "notes": (
            f"Spearman cross-sectional IC. fundYear={fund_year} → retYear={ret_year} Q2~Q4, "
            f"horizon={h}d non-overlap stepping, score={metric_key}. "
            "전년 연말 펀더멘털 → 당해 수익률 (look-ahead bias 방지), "
            "non-overlap 으로 자기상관 제거."
        ),
    }


from dartlab.quant.factor._calcRegression import _interpretIC, _rank1d


@withMemoryBudget(limitMb=500)
def calcFactorICAll(*, market: str = "KR", horizon: int = 5) -> dict | None:
    """4 팩터 (size/value/quality/investment) 의 Cross-Sectional IC 종합.

    Capabilities:
        - 4 팩터 동시 IC + ICIR 평가 + strongest 식별
        - story factor IC 블록 직접 진입

    Args:
        market: ``"KR"`` 만 지원.
        horizon: forward return 기간. 기본 ``5`` (주간 시그널).

    Returns:
        dict — market/year/horizon/factors/strongest/interpretation. 데이터 부재 None.

    Guide:
        Grinold-Kahn Ch.5 IC 횡단면 정의. ICIR ≥ 0.5 = useful, ≥ 0.75 = exceptional.

    When:
        Story factor IC 블록 + AI "유효 팩터" 답변.

    How:
        4 팩터 순회 → calcFactorIC → max(|ICIR|) 선정.

    Requires:
        scan finance.parquet + market 가용.

    Raises:
        없음 — 데이터 부재 시 None.

    Example:
        >>> r = calcFactorICAll(market="KR")
        >>> r["strongest"]
        'quality'

    See Also:
        - calcFactorIC : 단일 팩터 IC
        - factor.ranking.icTimeSeries : 일반 IC 시계열

    AIContext:
        "유효한 팩터" 답변 시 strongest + 각 팩터 ICIR 인용.
    """
    rows = []
    for fname in ("size", "value", "quality", "investment"):
        ic = calcFactorIC(fname, market=market, horizon=horizon)
        if ic is not None:
            rows.append(ic)
    if not rows:
        return None
    strongest = max(rows, key=lambda x: abs(x.get("icir", 0)))
    return {
        "market": market,
        "fundYear": rows[0].get("fundYear"),
        "retYear": rows[0].get("retYear"),
        "horizon": horizon,
        "factors": rows,
        "strongest": strongest.get("factorName"),
        "interpretation": (
            f"{market} 시장 IC 최강 팩터: {strongest.get('factorName')} "
            f"(ICIR={strongest.get('icir')}, {strongest.get('interpretation')})"
        ),
    }


# 0.10 BC 깸 — snake_case alias 제거.

__all__ = ["_FACTOR_KEY_MAP", "calcFactorIC", "calcFactorICAll"]
