"""표면 직교화 : 신규 표면 기여를 기존 앙상블에 residualize (MMC 동형) (L2.5 simulate).

전수 스캔이 수백 표면을 등재하면 상당수가 소수 아이디어의 중복이다 (모멘텀 4변형 = 사실상 1
아이디어). 이 모듈은 신규 표면의 기여를 기존 앙상블에 residualize 한 뒤 측정한다 (06 §4, Numerai
MMC 동형). 주별 횡단면에서 후보 표면 신호를 앙상블 신호에 회귀해 잔차(앙상블이 설명 못 하는
부분)만 남기고, 그 잔차 신호의 채점 t/스프레드로 증분 기여를 잰다. 중복 표면은 잔차 t 가
붕괴하므로 이중 계산이 차단된다 (원시 t 는 높아도 증분 t 는 0).

- ``residualizeWeekly`` : 주별 횡단면 OLS 잔차 (후보 ~ 앙상블 + 절편).
- ``mmcContribution`` : 후보 표면의 원시 vs 증분(잔차) 스프레드·t → 중복 판정.

Layer: L2.5 simulate. numpy · polars · readingScorecard 만 의존 (하향).
"""

from __future__ import annotations

import numpy as np
import polars as pl

from dartlab.simulate.readingScorecard import _weeklyT


def _scoreWide(readings: pl.DataFrame, surfacesWanted: list[str]) -> pl.DataFrame:
    """(code, week, surface, score) → wide (week, code, <surface>...). 요청 표면만."""
    sub = readings.filter(pl.col("surface").is_in(surfacesWanted))
    return sub.pivot(values="score", index=["week", "code"], on="surface", aggregate_function="first")


def residualizeWeekly(readings: pl.DataFrame, candidate: str, ensemble: list[str]) -> pl.DataFrame:
    """후보 표면 신호를 주별 횡단면에서 앙상블에 회귀 → 잔차 신호 (week, code, resid).

    Args:
        readings: (code, week, surface, score).
        candidate: 잔차를 낼 후보 표면.
        ensemble: 직교화 대상 기존 표면 목록.

    Returns:
        (week, code, resid). resid = 후보 score - OLS 적합(앙상블 + 절편). 앙상블이 비면 잔차 =
        중심화 후보 (증분 = 원시). 종목이 회귀 최소 표본 미만인 주는 스킵.
    """
    wide = _scoreWide(readings, [candidate] + ensemble)
    out = []
    for w in wide["week"].unique().to_list():
        wk = wide.filter(pl.col("week") == w).drop_nulls([candidate])
        y = wk[candidate].to_numpy().astype(float)
        codes = wk["code"].to_list()
        cols = [c for c in ensemble if c in wk.columns]
        if not cols or wk.height < len(cols) + 3:
            resid = y - y.mean()
        else:
            X = wk.select(cols).fill_null(0.5).to_numpy().astype(float)
            X = np.hstack([np.ones((X.shape[0], 1)), X])
            beta, *_ = np.linalg.lstsq(X, y, rcond=None)
            resid = y - X @ beta
        out.append(pl.DataFrame({"week": [w] * len(codes), "code": codes, "resid": resid}))
    if not out:
        return pl.DataFrame(schema={"week": pl.Int64, "code": pl.Utf8, "resid": pl.Float64})
    return pl.concat(out)


def _spreadT(signal: pl.DataFrame, labels: pl.DataFrame, valueCol: str) -> tuple[float, float]:
    """신호 (week, code, <valueCol>) 를 주별 Q5-Q1 스프레드 → (평균 스프레드, 주단위 t)."""
    j = signal.join(labels.select("code", "week", "exNeutral"), on=["code", "week"], how="inner")
    dq = j.with_columns(q=(pl.col(valueCol).rank() / pl.len()).over("week").mul(5).ceil().clip(1, 5).cast(pl.Int32))
    wk = dq.group_by(["week", "q"]).agg(ex=pl.col("exNeutral").mean())
    sp = wk.pivot(values="ex", index="week", on="q").drop_nulls()
    if "5" not in sp.columns or "1" not in sp.columns:
        return 0.0, 0.0
    diff = sp["5"] - sp["1"]
    return float(diff.mean()), _weeklyT(diff)


def mmcContribution(
    readings: pl.DataFrame, labels: pl.DataFrame, candidate: str, ensemble: list[str], *, redundantFrac: float = 0.4
) -> dict:
    """후보 표면의 원시 vs 증분(잔차) 기여 → 중복 판정. 이중 계산 차단.

    Args:
        readings: (code, week, surface, direction, score).
        labels: weeklyLabels 산출.
        candidate: 후보 표면. ensemble: 기존 앙상블 표면 목록.
        redundantFrac: 증분 t 가 원시 t 의 이 비율 미만이면 중복 (기본 0.4).

    Returns:
        {"rawT","rawSpread","residualT","residualSpread","redundant"}. redundant = 앙상블이
        후보를 거의 설명(증분 t 붕괴) = 이중 계산 위험. 승급 시 증분 t 를 써야 한다.
    """
    cand = readings.filter(pl.col("surface") == candidate).select("week", "code", "score")
    rawSpread, rawT = _spreadT(cand, labels, "score")
    resid = residualizeWeekly(readings, candidate, ensemble)
    residSpread, residT = _spreadT(resid, labels, "resid")
    redundant = abs(residT) < redundantFrac * abs(rawT) if abs(rawT) > 1e-9 else False
    return {
        "rawT": rawT,
        "rawSpread": rawSpread,
        "residualT": residT,
        "residualSpread": residSpread,
        "redundant": bool(redundant),
    }
