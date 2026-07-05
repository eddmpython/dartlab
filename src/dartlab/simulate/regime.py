"""레짐 조건부 채점 : 결정론 분류기 봉인 + 일치주 채점 + Giacomini-White (L2.5 simulate).

"조건부 시뮬은 원리적으로 채점 불가"의 부분 해결이다 (06 §5). 레짐 분류기(결정론 코드·공개
데이터·버전 해시)를 사전 봉인하고, 조건 태그 판독은 실현 레짐이 일치한 주에만 채점한다.
불일치 주는 "조건 미실현·미채점"으로 두되 airtime 분모(조건이 선언된 주 수)를 기록해, 희귀
조건 뒤에 숨어 무패 기록을 만드는 것을 차단한다. 레짐별 실력 차 주장은 Giacomini-White 조건부
예측력 검정 통과분만 인정한다. 분류기 변경 = 새 시리즈 (소급 재태깅 금지, 버전 해시로 봉인).

- ``classifyRegimes`` : 시장 주간 수익·변동성 → 결정론 4상 레짐 (calm/stress x up/down).
- ``regimeVersionHash`` : 분류기 정의 봉인 해시 (변경 = 새 시리즈).
- ``scoreConditional`` : 조건 태그 판독을 일치주에만 채점 + airtime 분모.
- ``giacominiWhite`` : 조건부 예측력 동일 검정 (Wald chi-square).

Layer: L2.5 simulate. numpy · polars 만 의존.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np
import polars as pl

# 분류기 정의 (변경 시 버전 해시가 바뀌어 새 시리즈가 된다).
_VOL_STRESS_QUANTILE = 0.70  # 트레일링 변동성 이 분위 초과 = stress
_VOL_WINDOW = 13  # 변동성 추정 주 창
_REGIME_DEF = f"v1|volQ={_VOL_STRESS_QUANTILE}|volW={_VOL_WINDOW}|states=calmUp,calmDown,stressUp,stressDown"


def regimeVersionHash() -> str:
    """레짐 분류기 정의의 봉인 해시. 정의 변경 = 해시 변경 = 새 시리즈 (소급 재태깅 금지)."""
    return hashlib.sha256(_REGIME_DEF.encode("utf-8")).hexdigest()[:16]


def marketWeekly(dailyPrices: pl.DataFrame) -> pl.DataFrame:
    """일별 가격 → 시장 주간 수익 (등가중) → (week, mktRet). 레짐 분류 입력."""
    df = dailyPrices.filter(pl.col("close") > 0).sort(["code", "date"])
    df = df.with_columns(ret=(pl.col("close") / pl.col("close").shift(1).over("code") - 1))
    daily = df.group_by("date").agg(mktRet=pl.col("ret").median()).sort("date")
    daily = daily.with_columns(d=pl.col("date").str.to_date("%Y%m%d")).with_columns(
        week=(pl.col("d").dt.iso_year() * 100 + pl.col("d").dt.week())
    )
    return daily.group_by("week").agg(mktRet=(pl.col("mktRet") + 1).product() - 1).sort("week")


def classifyRegimes(marketWeeklyDf: pl.DataFrame) -> pl.DataFrame:
    """시장 주간 수익 → 결정론 4상 레짐 → (week, regime, mktRet, vol).

    Args:
        marketWeeklyDf: (week, mktRet).

    Returns:
        (week, regime, mktRet, vol). regime = {calm,stress}x{Up,Down}. stress = 트레일링
        변동성이 _VOL_STRESS_QUANTILE 분위 초과. Up/Down = 그 주 수익 부호. 전부 PIT (트레일링).
    """
    df = marketWeeklyDf.sort("week").with_columns(vol=pl.col("mktRet").rolling_std(_VOL_WINDOW, min_samples=3))
    volCut = df["vol"].quantile(_VOL_STRESS_QUANTILE)
    if volCut is None:
        volCut = float("inf")
    return df.with_columns(
        regime=pl.concat_str(
            pl.when(pl.col("vol") > volCut).then(pl.lit("stress")).otherwise(pl.lit("calm")),
            pl.when(pl.col("mktRet") >= 0).then(pl.lit("Up")).otherwise(pl.lit("Down")),
        )
    ).select("week", "regime", "mktRet", "vol")


def scoreConditional(readings: pl.DataFrame, regimeByWeek: pl.DataFrame) -> dict:
    """조건 태그 판독을 실현 레짐 일치주에만 채점 + airtime 분모.

    Args:
        readings: (code, week, surface, condition, ...) condition None = 무조건(항상 채점).
        regimeByWeek: (week, regime) classifyRegimes 산출.

    Returns:
        {"scored": 채점 대상 판독(무조건 + 조건일치), "airtime": (condition, liveWeeks, realizedWeeks,
        scoredReadings, airtimeRatio)}. airtimeRatio = 실현/선언 (낮으면 희귀조건 은닉 경고).
    """
    reg = regimeByWeek.select("week", "regime")
    j = readings.join(reg, on="week", how="left")
    uncond = j.filter(pl.col("condition").is_null())
    cond = j.filter(pl.col("condition").is_not_null())
    matched = cond.filter(pl.col("condition") == pl.col("regime"))
    scored = pl.concat([uncond, matched], how="vertical_relaxed") if cond.height else uncond
    # airtime: 조건별 선언 주 vs 실현(일치) 주.
    airRows = []
    for c in cond["condition"].unique().to_list():
        cc = cond.filter(pl.col("condition") == c)
        liveWeeks = cc["week"].n_unique()
        realized = cc.filter(pl.col("condition") == pl.col("regime"))
        realizedWeeks = realized["week"].n_unique()
        airRows.append(
            {
                "condition": c,
                "liveWeeks": liveWeeks,
                "realizedWeeks": realizedWeeks,
                "scoredReadings": realized.height,
                "airtimeRatio": realizedWeeks / liveWeeks if liveWeeks else 0.0,
            }
        )
    airtime = (
        pl.DataFrame(airRows)
        if airRows
        else pl.DataFrame(
            schema={
                "condition": pl.Utf8,
                "liveWeeks": pl.Int64,
                "realizedWeeks": pl.Int64,
                "scoredReadings": pl.Int64,
                "airtimeRatio": pl.Float64,
            }
        )
    )
    return {"scored": scored.drop("regime"), "airtime": airtime}


def _chi2Sf(x: float, df: int) -> float:
    """카이제곱 생존함수 P(X>x) = 정규화 상방 불완전감마 Q(df/2, x/2). scipy 미의존 (NR)."""
    if x <= 0:
        return 1.0
    a, xx = df / 2.0, x / 2.0
    if xx < a + 1:  # 급수 (gser)
        term = 1.0 / a
        s = term
        n = a
        for _ in range(500):
            n += 1
            term *= xx / n
            s += term
            if abs(term) < abs(s) * 1e-12:
                break
        return 1.0 - s * math.exp(-xx + a * math.log(xx) - math.lgamma(a))
    b = xx + 1 - a  # 연분수 (gcf)
    c = 1e300
    d = 1.0 / b
    h = d
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        if abs(d) < 1e-300:
            d = 1e-300
        c = b + an / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-12:
            break
    return h * math.exp(-xx + a * math.log(xx) - math.lgamma(a))


def giacominiWhite(lossA: np.ndarray, lossB: np.ndarray, instruments: np.ndarray) -> dict:
    """Giacomini-White 조건부 예측력 동일 검정 → {"stat","df","pValue"}.

    Args:
        lossA / lossB: 두 예측의 기간별 손실 (예 제곱오차·Brier). d = lossA - lossB.
        instruments: (T x q) 조건 도구 (예 [1, 레짐 지시자]). E[h_t d_t]=0 이 귀무.

    Returns:
        {"stat" Wald chi-square, "df"=q, "pValue"}. 작은 p = 조건부 예측력 차이 있음 (레짐별 실력
        차 주장은 이 통과분만). 손실 동일이면 stat 0, p 1.
    """
    d = np.asarray(lossA, dtype=float) - np.asarray(lossB, dtype=float)
    h = np.asarray(instruments, dtype=float)
    if h.ndim == 1:
        h = h[:, None]
    T, q = h.shape
    z = h * d[:, None]  # (T x q)
    zbar = z.mean(axis=0)
    omega = (z.T @ z) / T  # 귀무 하 E[z]=0 → 2차 모멘트
    try:
        stat = float(T * zbar @ np.linalg.solve(omega, zbar))
    except np.linalg.LinAlgError:
        stat = float(T * zbar @ np.linalg.pinv(omega) @ zbar)
    return {"stat": stat, "df": q, "pValue": _chi2Sf(stat, q)}
