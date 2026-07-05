"""분기 재무의 일 단위 사용 : PIT 계단 + 이벤트타임(SUE/EAR) + 표시전용 분해 (L2.5 simulate).

분기 재무를 퀀트가 일 단위로 잘라 쓰는 계약이다 (06 §5c). 규율: **피처는 PIT 계단 + 이벤트타임만**.
① PIT 계단: 공시 발효(rceptDate)에서 계단식 carry-forward (as-of, 보간 절대 금지 = 미래 누설).
② 이벤트타임: 실적 발표 기준 τ(경과일)·SUE(계절차 표준화 서프라이즈)·EAR(발표창 초과수익).
③ 분해(Chow-Lin/Denton)는 **표시 전용**이라 displayOnly 라벨을 달고 피처로 쓰지 않는다 (분기 값을
매끄럽게 월/일로 나누면 미래 정보가 과거로 샌다). ④ 이중 이벤트(잠정 vs 확정 실적)는 vintage 로
분리. nowcast(현분기 추정)는 시뮬 종류로 등재되며 simulated 라벨 필수 (실측과 분리).

- ``fundDailyStep`` : 일별 PIT 계단 재무 + τ (보간 0).
- ``sue`` / ``ear`` : 이벤트타임 서프라이즈 · 발표창 초과수익.
- ``chowLinDisplay`` : 표시 전용 시계열 분해 (displayOnly, 피처 금지 가드).

Layer: L2.5 simulate. table (finance grid·일 가격) · numpy · polars 만 의존.
"""

from __future__ import annotations

import numpy as np
import polars as pl

_EAR_WINDOW = 3  # 실적 발표 초과수익 창 (거래일)
_SUE_MIN_HISTORY = 6  # SUE 표준화 최소 계절차 표본


def fundDailyStep(grid: pl.DataFrame, tradingDates: pl.DataFrame, account: str = "netIncome") -> pl.DataFrame:
    """분기 재무 → 일별 PIT 계단 (as-of carry) + τ 경과일. 보간 0 (미래 누설 차단).

    Args:
        grid: table.scanFinanceGrid 산출 (code, period, rceptDate, account, amount).
        tradingDates: (date) 거래일. account: 계단화할 계정.

    Returns:
        (code, date, amount, rceptDate, tau). amount = date 이하 최신 공시 계단값 (보간 아님),
        tau = date - rceptDate 경과일 (이벤트타임 피처). 미공시 이전 date 는 결과 없음.
    """
    g = (
        grid.filter(pl.col("account") == account)
        .select("code", "rceptDate", "amount")
        .drop_nulls("rceptDate")
        .sort(["code", "rceptDate"])
    )
    dates = tradingDates.select("date").unique().sort("date")
    codes = g.select("code").unique()
    grid2 = codes.join(dates, how="cross").sort(["code", "date"])
    out = grid2.join_asof(g, left_on="date", right_on="rceptDate", by="code", strategy="backward").drop_nulls(
        "rceptDate"
    )
    return out.with_columns(
        tau=(pl.col("date").str.to_date("%Y%m%d") - pl.col("rceptDate").str.to_date("%Y%m%d")).dt.total_days()
    ).select("code", "date", "amount", "rceptDate", "tau")


def sue(grid: pl.DataFrame, account: str = "netIncome") -> pl.DataFrame:
    """계절차 표준화 실적 서프라이즈 SUE → (code, period, rceptDate, sue). 이벤트타임 피처.

    SUE = (X_q - X_{q-4}) / std(계절차 이력). 계절 랜덤워크 기대(전년동기) 대비 표준화 서프라이즈.
    표본(_SUE_MIN_HISTORY) 미달 종목은 sue null (0 대체 금지).
    """
    g = (
        grid.filter(pl.col("account") == account)
        .select("code", "period", "rceptDate", "amount")
        .drop_nulls(["period", "amount"])
        .sort(["code", "period"])
    )
    g = g.with_columns(seasDiff=pl.col("amount") - pl.col("amount").shift(4).over("code"))
    g = g.with_columns(
        sueStd=pl.col("seasDiff").rolling_std(8, min_samples=_SUE_MIN_HISTORY).over("code"),
        n=pl.col("seasDiff").is_not_null().cum_sum().over("code"),
    )
    return g.with_columns(
        sue=pl.when((pl.col("sueStd") > 0) & (pl.col("n") >= _SUE_MIN_HISTORY))
        .then(pl.col("seasDiff") / pl.col("sueStd"))
        .otherwise(None)
    ).select("code", "period", "rceptDate", "sue")


def ear(grid: pl.DataFrame, dailyPrices: pl.DataFrame, *, window: int = _EAR_WINDOW) -> pl.DataFrame:
    """실적 발표창 초과수익 EAR → (code, period, rceptDate, ear). 이벤트타임 피처.

    발표일(rceptDate)의 다음 거래일부터 window 거래일 누적 수익 - 시장 등가중 누적 (횡단 초과).
    발표일이 거래일이 아니면 직후 거래일에 정렬.
    """
    px = dailyPrices.filter(pl.col("close") > 0).sort(["code", "date"])
    px = px.with_columns(ret=(pl.col("close") / pl.col("close").shift(1).over("code") - 1))
    mkt = px.group_by("date").agg(mktRet=pl.col("ret").median()).sort("date")
    px = px.join(mkt, on="date", how="left").with_columns(exRet=pl.col("ret") - pl.col("mktRet"))
    # 각 종목 발표 이벤트: rceptDate 직후 거래일부터 window 누적 초과.
    ev = grid.select("code", "period", "rceptDate").drop_nulls("rceptDate").unique()
    codePx = {c: sub.sort("date") for c, sub in px.group_by("code")}
    rows = []
    for e in ev.iter_rows(named=True):
        sub = codePx.get((e["code"],))
        if sub is None:
            continue
        after = sub.filter(pl.col("date") > e["rceptDate"]).head(window)
        if after.height == 0:
            continue
        rows.append(
            {"code": e["code"], "period": e["period"], "rceptDate": e["rceptDate"], "ear": float(after["exRet"].sum())}
        )
    if not rows:
        return pl.DataFrame(schema={"code": pl.Utf8, "period": pl.Utf8, "rceptDate": pl.Utf8, "ear": pl.Float64})
    return pl.DataFrame(rows)


def chowLinDisplay(quarterly: np.ndarray, periodsPerQuarter: int = 3) -> dict:
    """분기 값을 하위 빈도로 매끄럽게 분해 (Denton 비례, **표시 전용**). displayOnly 라벨 강제.

    Args:
        quarterly: 분기 시계열 값.
        periodsPerQuarter: 분기당 하위 기간 수 (월=3).

    Returns:
        {"series": 분해 시계열, "displayOnly": True, "warning": 피처 사용 금지}. 분해는 분기 값을
        매끄럽게 나눠 미래 정보가 과거로 새므로(look-ahead) 채점 피처로 절대 쓰지 않는다.
    """
    q = np.asarray(quarterly, dtype=float)
    # 비례 Denton 근사: 각 분기 값을 하위 기간에 균등 배분 후 인접 분기로 선형 매끄럽게.
    fine = np.repeat(q / periodsPerQuarter, periodsPerQuarter)
    if fine.size >= 3:
        fine = np.convolve(fine, np.ones(3) / 3, mode="same")
    return {
        "series": fine.tolist(),
        "displayOnly": True,
        "warning": "표시 전용. 분해값을 채점 피처로 쓰면 look-ahead (분기 값이 과거로 샘).",
    }
