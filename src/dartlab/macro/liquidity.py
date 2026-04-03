"""매크로 유동성 분석 — M2 + 연준 B/S + 신용스프레드."""

from __future__ import annotations

from dartlab.core.finance.liquidity import classifyLiquidityRegime


def _fetch_liquidity_data(market: str) -> dict[str, float | None]:
    """gather에서 유동성 지표 수집."""
    from dartlab.gather import getDefaultGather

    g = getDefaultGather()
    data: dict[str, float | None] = {}

    # M2 YoY
    try:
        m2_df = g.macro("M2SL")
        if m2_df is not None and len(m2_df) > 0:
            vals = m2_df.get_column("value").drop_nulls()
            if len(vals) >= 12:
                current = float(vals[-1])
                year_ago = float(vals[-12])
                if year_ago > 0:
                    data["m2_yoy"] = (current / year_ago - 1) * 100
    except Exception:
        pass

    # 연준 총자산 (WALCL) 3개월 변화율
    try:
        wal_df = g.macro("WALCL")
        if wal_df is not None and len(wal_df) > 0:
            vals = wal_df.get_column("value").drop_nulls()
            if len(vals) >= 13:  # ~3개월 (weekly)
                current = float(vals[-1])
                three_m_ago = float(vals[-13])
                if three_m_ago > 0:
                    data["fed_bs_change_pct"] = (current / three_m_ago - 1) * 100
    except Exception:
        pass

    # HY 스프레드
    try:
        hy_df = g.macro("BAMLH0A0HYM2")
        if hy_df is not None and len(hy_df) > 0:
            vals = hy_df.get_column("value").drop_nulls()
            if len(vals) > 0:
                data["hy_spread"] = float(vals[-1]) * 100  # % → bps
    except Exception:
        pass

    # IG 스프레드
    try:
        ig_df = g.macro("BAMLC0A0CM")
        if ig_df is not None and len(ig_df) > 0:
            vals = ig_df.get_column("value").drop_nulls()
            if len(vals) > 0:
                data["ig_spread"] = float(vals[-1]) * 100  # % → bps
    except Exception:
        pass

    # 역레포 (RRPONTSYD)
    try:
        rrp_df = g.macro("RRPONTSYD")
        if rrp_df is not None and len(rrp_df) > 0:
            vals = rrp_df.get_column("value").drop_nulls()
            if len(vals) >= 63:  # ~3개월
                current = float(vals[-1])
                three_m_ago = float(vals[-63])
                if three_m_ago > 0:
                    data["rrp_change_pct"] = (current / three_m_ago - 1) * 100
                elif current > 0:
                    data["rrp_change_pct"] = 100.0  # 0→양수
    except Exception:
        pass

    return data


def analyze_liquidity(*, market: str = "US", **kwargs) -> dict:
    """유동성 환경 종합 분석.

    Returns:
        dict: regime, signals, raw data
    """
    data = _fetch_liquidity_data(market)
    regime = classifyLiquidityRegime(
        m2_yoy=data.get("m2_yoy"),
        fed_bs_change_pct=data.get("fed_bs_change_pct"),
        hy_spread=data.get("hy_spread"),
        ig_spread=data.get("ig_spread"),
        rrp_change_pct=data.get("rrp_change_pct"),
    )

    result = {
        "market": market.upper(),
        "regime": regime.regime,
        "regimeLabel": regime.regimeLabel,
        "score": regime.score,
        "signals": list(regime.signals),
    }

    # 시계열
    from dartlab.macro._helpers import recent_timeseries

    ts: dict = {}
    try:
        from dartlab.gather import getDefaultGather
        g = getDefaultGather()
        for label, sid in [("m2", "M2SL"), ("hy_spread", "BAMLH0A0HYM2"), ("ig_spread", "BAMLC0A0CM")]:
            ts[label] = recent_timeseries(g.macro(sid))
    except Exception:
        pass
    result["timeseries"] = ts

    return result
