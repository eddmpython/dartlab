"""매크로 사이클 분석 — 4국면 판별 + 전환 시퀀스."""

from __future__ import annotations

from dartlab.core.finance.macroCycle import (
    classifyCycle,
    detectTransitionSequence,
)


def _fetch_indicators(market: str) -> dict[str, float | None]:
    """gather에서 사이클 판별에 필요한 지표 수집."""
    from dartlab.gather import getDefaultGather

    g = getDefaultGather()
    indicators: dict[str, float | None] = {}

    if market.upper() == "US":
        # HY 스프레드
        try:
            hy_df = g.macro("BAMLH0A0HYM2")
            if hy_df is not None and len(hy_df) > 0:
                vals = hy_df.get_column("value").drop_nulls()
                if len(vals) > 0:
                    indicators["hy_spread"] = float(vals[-1]) * 100  # % → bps
                    if len(vals) >= 63:  # ~3개월
                        indicators["hy_spread_3m_change"] = (float(vals[-1]) - float(vals[-63])) * 100
        except Exception:
            pass

        # 장단기 스프레드 (10Y-2Y)
        try:
            ts_df = g.macro("T10Y2Y")
            if ts_df is not None and len(ts_df) > 0:
                vals = ts_df.get_column("value").drop_nulls()
                if len(vals) > 0:
                    indicators["term_spread"] = float(vals[-1])
        except Exception:
            pass

        # VIX
        try:
            vix_df = g.macro("VIXCLS")
            if vix_df is not None and len(vix_df) > 0:
                vals = vix_df.get_column("value").drop_nulls()
                if len(vals) > 0:
                    indicators["vix"] = float(vals[-1])
        except Exception:
            pass

        # 금 YoY (GOLDAMGBD228NLBM)
        try:
            gold_df = g.macro("GOLDAMGBD228NLBM")
            if gold_df is not None and len(gold_df) > 0:
                vals = gold_df.get_column("value").drop_nulls()
                if len(vals) >= 252:  # ~1년
                    current = float(vals[-1])
                    year_ago = float(vals[-252])
                    if year_ago > 0:
                        indicators["gold_yoy"] = (current / year_ago - 1) * 100
        except Exception:
            pass

        # BEI (기대인플레이션)
        try:
            bei_df = g.macro("T10YIE")
            if bei_df is not None and len(bei_df) > 0:
                vals = bei_df.get_column("value").drop_nulls()
                if len(vals) > 0:
                    indicators["bei_10y"] = float(vals[-1])
        except Exception:
            pass

        # CPI YoY
        try:
            cpi_df = g.macro("CPIAUCSL")
            if cpi_df is not None and len(cpi_df) > 0:
                vals = cpi_df.get_column("value").drop_nulls()
                if len(vals) >= 12:
                    current = float(vals[-1])
                    year_ago = float(vals[-12])
                    if year_ago > 0:
                        indicators["cpi_yoy"] = (current / year_ago - 1) * 100
        except Exception:
            pass

    elif market.upper() == "KR":
        # 한국은 CLI(경기선행지수)를 주요 신호로 사용
        try:
            cli_df = g.macro("CLI")
            if cli_df is not None and len(cli_df) > 0:
                vals = cli_df.get_column("value").drop_nulls()
                if len(vals) >= 2:
                    indicators["cli_mom"] = float(vals[-1]) - float(vals[-2])
        except Exception:
            pass

        # 원/달러 환율 변화 (위험회피 proxy)
        try:
            fx_df = g.macro("USDKRW")
            if fx_df is not None and len(fx_df) > 0:
                vals = fx_df.get_column("value").drop_nulls()
                if len(vals) > 0:
                    indicators["vix"] = None  # KR에는 VIX 직접 없음
        except Exception:
            pass

    return indicators


def analyze_cycle(*, market: str = "US", **kwargs) -> dict:
    """경제 사이클 분석.

    Returns:
        dict: phase, transition, indicators 등
    """
    indicators = _fetch_indicators(market)
    cycle = classifyCycle(indicators)
    transition = detectTransitionSequence(cycle.phase, indicators)

    result: dict = {
        "market": market.upper(),
        "phase": cycle.phase,
        "phaseLabel": cycle.label,
        "confidence": cycle.confidence,
        "signals": list(cycle.signals),
        "sectorStrategy": cycle.sectorStrategy,
        "transition": None,
    }

    if transition is not None:
        result["transition"] = {
            "from": transition.fromPhase,
            "to": transition.toPhase,
            "progress": transition.progress,
            "triggered": list(transition.triggered),
            "pending": list(transition.pending),
        }

    # 시계열: gather DataFrame에서 최근 6개월분 포함
    from dartlab.macro._helpers import recent_timeseries

    ts: dict = {}
    try:
        from dartlab.gather import getDefaultGather

        g = getDefaultGather()
        for label, sid in [("hy_spread", "BAMLH0A0HYM2"), ("vix", "VIXCLS"), ("term_spread", "T10Y2Y")]:
            ts[label] = recent_timeseries(g.macro(sid))
    except Exception:
        pass
    result["timeseries"] = ts

    return result
