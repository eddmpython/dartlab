"""이익 모멘텀 - SUE + PEAD.

학술 근거: Ball & Brown (1968), Bernard & Thomas (1989).
"""

from __future__ import annotations

import logging

import numpy as np
import polars as pl

from dartlab.core.market import resolveMarket
from dartlab.quant.screen.dataAccess import loadScanParquet
from dartlab.synth.scanBridge import extractAnnualConsolidated, isEdgarSchema

log = logging.getLogger(__name__)


def _parse(val) -> float | None:
    """문자열/숫자 → float. core SSOT 사용."""
    if isinstance(val, (int, float)):
        return float(val)
    from dartlab.core.utils.helpers import parseNumStr

    return parseNumStr(val)


def calcEarnings(stockCode: str, *, market: str = "auto", **kwargs) -> dict:
    """SUE + PEAD 이익 모멘텀 분석.

    Capabilities:
        Standardized Unexpected Earnings (SUE = (latest - mean) / std) 로
        실적 서프라이즈 강도 측정 + PEAD (Post-Earnings Announcement Drift,
        Bernard-Thomas 1989) 신호 강도 판정. 영업이익 시계열 추세 라벨링
        (consistent_growth / mostly_growing / mostly_declining / mixed).

    Args:
        stockCode: 종목코드 또는 ticker.
        market: "KR" | "US" | "auto".

    Returns:
        dict:
            - ``stockCode``/``market``: 식별.
            - ``sue`` (float): SUE 배.
            - ``latestOpIncome``/``prevMean`` (float): 최근/과거 평균 영업이익.
            - ``peadSignal`` (str): positive_drift / negative_drift /
              mild_positive / mild_negative / none.
            - ``peadStrength`` (str): strong / moderate / weak.
            - ``earningsTrend`` (str): consistent_growth / mostly_growing /
              mostly_declining / mixed.
            - ``opIncomeHistory`` (dict[str, float]): 연도별 영업이익.
            - 또는 ``error`` (str): 데이터 부족.

    Raises:
        없음 (error 키).

    Example:
        >>> r = calcEarnings("005930")
        >>> r["sue"], r["peadSignal"]
        (2.3, 'positive_drift')

    Guide:
        - SUE > 2 = strong positive surprise, < -2 = strong negative.
        - PEAD 효과: 발표 후 60~90 일 sue 방향으로 drift (학술 검증).
        - earningsTrend "consistent_growth" + sue > 0 = 강한 기본 momentum.

    See Also:
        - ``calcEventSignal``: 공시 이벤트 (실적 외)
        - ``calcMomentum``: 가격 모멘텀
        - ``calcCAR``: event-study 누적 초과수익

    When:
        Quant 실적 모멘텀 축 진입점 + AI 어닝 서프라이즈 답변.

    How:
        scan parquet → 영업이익 시계열 → SUE 산식 → PEAD 강도 라벨 + 추세
        라벨 합성.

    Requires:
        scan finance parquet (연결 영업이익) + 충분한 시계열 (5+ 년 권장).

    AIContext:
        SUE 절대값 + peadSignal + earningsTrend 함께. KR 회사 어닝 시즌 (4월/
        7월/10월/1월) 직후 본 신호 모니터링. 영업이익 vs 순이익 차이 (KR
        은 영업이익 주축, US 는 EPS).

    LLM Specifications:
        AntiPatterns:
            - SUE 단독 인용 - earningsTrend + peadStrength 함께.
            - 발표 직전에 본 함수 호출 - drift 효과는 발표 후 60+ 일.
        OutputSchema:
            ``{stockCode, market, sue: float, latestOpIncome: float, prevMean:
              float, peadSignal: str, peadStrength: str, earningsTrend: str,
              opIncomeHistory: dict}``.
        Prerequisites:
            scan finance parquet 시계열 5+ 년.
        Freshness:
            분기 (실적 발표 직후).
        Dataflow:
            finance parquet → 연도별 영업이익 → mean/std → SUE → drift signal
            라벨 + trend 라벨.
        TargetMarkets: KR (DART 영업이익), US (EDGAR operating_profit).
    """
    market = resolveMarket(stockCode, market)
    result: dict = {"stockCode": stockCode, "market": market}

    lf = loadScanParquet("finance", market)
    if lf is None:
        return {**result, "error": "finance.parquet 없음"}
    try:
        full = lf.filter(pl.col("stockCode") == stockCode).collect(engine="streaming")
    except (KeyError, ValueError, TypeError, AttributeError) as e:
        return {**result, "error": str(e)}
    if full.is_empty():
        return {**result, "error": "영업이익 데이터 없음"}

    edgar = isEdgarSchema(full)
    annual = extractAnnualConsolidated(full)

    yearly: dict[str, float] = {}
    if edgar:
        # EDGAR: operating_profit 컬럼 직접 사용
        yearCol = "fy"
        for row in annual.iter_rows(named=True):
            y = str(row.get(yearCol, ""))
            v = row.get("operating_profit")
            if y and v is not None:
                try:
                    v = float(v)
                except (ValueError, TypeError):
                    continue
                if y not in yearly or abs(v) > abs(yearly.get(y, 0)):
                    yearly[y] = v
    else:
        # DART: sj_div + account_nm 필터
        stock = annual.filter(pl.col("sj_div").is_in(["IS", "CIS"]) & pl.col("account_nm").str.contains("영업이익"))
        for row in stock.iter_rows(named=True):
            y = row.get("bsns_year")
            v = _parse(row.get("thstrm_amount"))
            if y and v is not None:
                if y not in yearly or abs(v) > abs(yearly.get(y, 0)):
                    yearly[y] = v

    if len(yearly) < 2:
        return {**result, "error": f"연도 부족 ({len(yearly)}개)"}

    yrs = sorted(yearly.keys())
    vals = [yearly[y] for y in yrs]
    result["years"] = yrs
    result["opIncomeHistory"] = {y: v for y, v in zip(yrs, vals)}

    latest = vals[-1]
    prev = np.array(vals[:-1], dtype=np.float64)
    mu = float(np.mean(prev))
    sd = float(np.std(prev, ddof=1)) if len(prev) > 1 else 0

    sue = float((latest - mu) / sd) if sd > 0 else (3.0 if latest > mu else -3.0 if latest < mu else 0.0)
    result["sue"] = round(sue, 4)
    result["latestOpIncome"] = latest
    result["prevMean"] = round(mu, 0)

    if abs(sue) > 2:
        result["peadSignal"] = "positive_drift" if sue > 0 else "negative_drift"
        result["peadStrength"] = "strong"
    elif abs(sue) > 1:
        result["peadSignal"] = "mild_positive" if sue > 0 else "mild_negative"
        result["peadStrength"] = "moderate"
    else:
        result["peadSignal"] = "none"
        result["peadStrength"] = "weak"

    if len(vals) >= 3:
        diffs = [vals[i] - vals[i - 1] for i in range(1, len(vals))]
        pos = sum(1 for d in diffs if d > 0)
        r = pos / len(diffs)
        result["earningsTrend"] = (
            "consistent_growth"
            if r == 1
            else "mostly_growing"
            if r >= 0.7
            else "mostly_declining"
            if r <= 0.3
            else "mixed"
        )
    return result
