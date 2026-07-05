"""비용 바닥 : 고저가 스프레드 추정 + 세율표 + 틱 하한 → net-of-cost 게이트 (L2.5 simulate).

판독의 총초과(gross)는 거래비용으로 상당분이 상쇄된다. 이 모듈은 발행 시점에 종목별 비용
바닥을 결정론으로 봉인해 gross/floor/net 3열을 낸다 (06 §4). 바닥 = 유효 스프레드 추정
(Corwin-Schultz·Abdi-Ranaldo, 일 고저가 자급) + 1틱 하한 + 거래일자 기준 매도 세율 + 유관기관
비용 x2. 실측(2026-07-05): KR 왕복 유효 스프레드 중앙 0.68% → 주간 전량 회전 비용 바닥 약
0.9~1.0%/주. +0.5%/주급 총초과는 비용에 전멸하나, 회피(red-flag) 표면은 회전 0 이라 비용 0 로
가치가 그대로 성립한다.

- ``costFloorWeekly`` : 주말 as-of 트레일링 창에서 종목별 왕복 비용 바닥.
- ``sellTaxRate`` / ``tickFloorFrac`` : 거래일자 기준 세율 · 가격대별 1틱 최소 비용.
- ``netPositive`` : 종목별 기대 엣지 vs 비용 바닥 (회피 종목은 비용 0) → net-of-cost 게이트.

Layer: L2.5 simulate. table (일 고저가 직독) · numpy · polars 만 의존.
"""

from __future__ import annotations

import math

import polars as pl

from dartlab.simulate import table as _table

# 유관기관비용 (거래소·예탁결제 등) 편도 0.0036%. 왕복은 x2.
INST_FEE = 0.000036
# 매도 증권거래세 전환일: 이 날짜부터 양시장 0.20% (이전 0.15%). 거래일자 기준.
_TAX_SWITCH_DATE = "20260101"
_SELL_TAX_BEFORE = 0.0015
_SELL_TAX_AFTER = 0.0020
# KRX 통합 호가단위 (2023 개정): (가격 상한 미만, 틱). 마지막은 상한 없음.
_TICK_TABLE: tuple[tuple[float, float], ...] = (
    (2_000, 1),
    (5_000, 5),
    (20_000, 10),
    (50_000, 50),
    (200_000, 100),
    (500_000, 500),
    (float("inf"), 1_000),
)
_CS_K = 3 - 2 * math.sqrt(2)  # Corwin-Schultz 상수 3 - 2√2
_DEFAULT_WINDOW = 20  # 스프레드 추정 트레일링 거래일 창


def sellTaxRate(tradeDate: str) -> float:
    """거래일자 'YYYYMMDD' → 매도 증권거래세율 (2026-01-01 전 0.15%, 이후 0.20%). 양시장 동일."""
    return _SELL_TAX_AFTER if tradeDate >= _TAX_SWITCH_DATE else _SELL_TAX_BEFORE


def tickFloorFrac(price: float) -> float:
    """가격 → 1틱 비례 최소 비용 (호가단위/가격). 스프레드 추정 하한 (틱보다 좁을 수 없음)."""
    if price is None or price <= 0:
        return 0.0
    for upper, tick in _TICK_TABLE:
        if price < upper:
            return tick / price
    return 0.0


def _sellTaxExpr(dateCol: str = "date") -> pl.Expr:
    """거래일자 컬럼 → 세율 Expr (벡터화)."""
    return pl.when(pl.col(dateCol) >= _TAX_SWITCH_DATE).then(_SELL_TAX_AFTER).otherwise(_SELL_TAX_BEFORE)


def _tickFloorExpr(priceCol: str) -> pl.Expr:
    """가격 컬럼 → 1틱 비례 최소 비용 Expr (호가단위 계단)."""
    expr = pl.lit(0.0)
    for upper, tick in reversed(_TICK_TABLE):
        expr = pl.when(pl.col(priceCol) < upper).then(tick / pl.col(priceCol)).otherwise(expr)
    return expr


def _spreadEstimators(dailyHL: pl.DataFrame, window: int) -> pl.DataFrame:
    """일 고저종가 → 종목별 일 단위 트레일링 스프레드 추정 (Abdi-Ranaldo·Corwin-Schultz).

    두 추정기 모두 인접 2거래일 쌍을 쓴다. PIT 무결을 위해 쌍 (t-1,t) 값을 후일 t 에 배정하고
    트레일링 rolling_mean 을 쓴다 (주말 as-of 추정이 미래 거래일을 참조하지 않음).
    """
    d = dailyHL.sort(["code", "date"]).with_columns(
        lnH=pl.col("high").log(), lnL=pl.col("low").log(), lnC=pl.col("close").log()
    )
    d = d.with_columns(mid=(pl.col("lnH") + pl.col("lnL")) / 2, hl2=(pl.col("lnH") - pl.col("lnL")).pow(2))
    # Abdi-Ranaldo CHL: x_t = (c - mid)(c - mid_{next}), 쌍을 후일에 배정 = shift(1) 사용.
    d = d.with_columns(
        arX=(pl.col("lnC").shift(1).over("code") - pl.col("mid").shift(1).over("code"))
        * (pl.col("lnC").shift(1).over("code") - pl.col("mid"))
    )
    # Corwin-Schultz: beta = hl2_{t-1}+hl2_t, gamma = (max ln H - min ln L)^2 over 2일.
    lnHmax = pl.max_horizontal(pl.col("lnH"), pl.col("lnH").shift(1).over("code"))
    lnLmin = pl.min_horizontal(pl.col("lnL"), pl.col("lnL").shift(1).over("code"))
    beta = pl.col("hl2").shift(1).over("code") + pl.col("hl2")
    gamma = (lnHmax - lnLmin).pow(2)
    alpha = ((2 * beta).sqrt() - beta.sqrt()) / _CS_K - (gamma / _CS_K).sqrt()
    csS = 2 * (alpha.exp() - 1) / (1 + alpha.exp())
    d = d.with_columns(csS=pl.when(csS > 0).then(csS).otherwise(0.0))
    # 트레일링 창 평균 (PIT: 쌍 값이 후일 배정이라 창은 과거만 참조).
    d = d.with_columns(
        arMean=pl.col("arX").rolling_mean(window, min_samples=window // 2).over("code"),
        csSpread=pl.col("csS").rolling_mean(window, min_samples=window // 2).over("code"),
    )
    return d.with_columns(arSpread=pl.when(pl.col("arMean") > 0).then(2 * pl.col("arMean").sqrt()).otherwise(None))


def costFloorWeekly(weekEnd: pl.DataFrame, dailyHL: pl.DataFrame, *, window: int = _DEFAULT_WINDOW) -> pl.DataFrame:
    """주말 as-of 종목별 왕복 비용 바닥 → (week, code, spread, tickFloor, sellTax, costFloor).

    Args:
        weekEnd: (week, date=그 주 마지막 거래일).
        dailyHL: table.dailyHighLow 산출 (date, code, high, low, close).
        window: 스프레드 추정 트레일링 거래일 창 (기본 20).

    Returns:
        (week, code, spreadAr, spreadCs, spread, tickFloor, sellTax, costFloor). costFloor =
        max(유효스프레드, 1틱) + 매도세(거래일자 기준) + 유관기관비용 x2. spread 는 Abdi-Ranaldo
        우선, 결측 시 Corwin-Schultz 폴백. 스프레드 = 왕복 유효 (매수·매도 교차 1회씩).
    """
    est = _spreadEstimators(dailyHL, window)
    snap = est.join(weekEnd, on="date", how="inner")
    return (
        snap.with_columns(
            spreadAr=pl.col("arSpread"),
            spreadCs=pl.col("csSpread"),
            tickFloor=_tickFloorExpr("close"),
            sellTax=_sellTaxExpr("date"),
        )
        .with_columns(spread=pl.coalesce(pl.col("spreadAr"), pl.col("spreadCs"), pl.col("tickFloor")))
        .with_columns(
            costFloor=pl.max_horizontal(pl.col("spread"), pl.col("tickFloor")) + pl.col("sellTax") + 2 * INST_FEE
        )
        .select("week", "code", "spreadAr", "spreadCs", "spread", "tickFloor", "sellTax", "costFloor")
    )


def netPositive(
    edgeByCode: pl.DataFrame, costFloorByCode: pl.DataFrame, *, avoidCodes: set[str] | None = None
) -> set[str]:
    """종목별 기대 엣지 vs 비용 바닥 → net-of-cost 통과 종목 집합 (board top10 게이트).

    Args:
        edgeByCode: (code, edge) 종목별 기대 엣지 (예 발화 인증표면 net 스프레드 x 방향 합). 주간
            전량 회전 매수 포지션 기준.
        costFloorByCode: (code, costFloor) 종목별 왕복 비용 바닥.
        avoidCodes: 회피(red-flag) 종목 (회전 0 = 비용 0). 이 종목은 비용을 빼지 않는다.

    Returns:
        net = edge - (0 if avoid else costFloor) > 0 인 종목코드 집합.
    """
    avoid = avoidCodes or set()
    j = edgeByCode.join(costFloorByCode.select("code", "costFloor"), on="code", how="left")
    j = j.with_columns(
        effFloor=pl.when(pl.col("code").is_in(list(avoid))).then(0.0).otherwise(pl.col("costFloor").fill_null(0.0))
    ).with_columns(net=pl.col("edge") - pl.col("effFloor"))
    return set(j.filter(pl.col("net") > 0)["code"].to_list())
