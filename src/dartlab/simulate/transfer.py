"""The macro to fundamentals edge transfer, the only math the L2.5 driver DAG owns.

A simulate node is either a thin call into an L2 leaf or this single owned edge: the linear map from a macro scenario
(GDP / interest rate / FX) onto a company's revenue / margin / WACC, parameterized by a sector
elasticity.

Born-clean: this module imports its constants (`BASELINE_FX`, `BASELINE_RATE`) and the elasticity
type forward from `dartlab.synth.scenario` (L1.5). L2.5 → L1.5 is a legal single-direction import.
It does NOT import from the legacy simulation flow
(`analysis/forecast/simulation.py::_applyMacroShock`, `_simScenario`, `_simMonteCarlo`); that flow
stays untouched. The arithmetic here is a faithful, byte-for-byte port of the legacy transfer.

Layer: L2.5. Forward imports: L1.5 (`synth`).
"""

from __future__ import annotations

from dartlab.synth.scenario import (
    BASELINE_FX,
    BASELINE_RATE,
    SectorElasticity,
)

# `SectorElasticity` is the elasticity contract consumed below. It exposes the fields the
# transfer reads: revenueToGdp (GDP 1%p -> revenue multiplier, beta), revenueToFx (FX 10% weaker
# -> revenue %), marginToGdp (GDP 1%p -> margin bps), nimToRate (rate 100bps -> NIM bps,
# financials only).


def transferMacroToFundamentals(
    baseRevenue: float,
    baseMargin: float,
    gdp: float,
    rate: float,
    fx: float,
    elasticity: SectorElasticity,
    baseWacc: float,
) -> tuple[float, float, float]:
    """Map one year of macro scalars onto adjusted revenue / margin / WACC (single-year transfer).

    Capabilities:
        The linear macro→fundamentals edge: applies a GDP shock and an FX shock to revenue, a
        GDP shock and (for financials) a rate/NIM shock to margin, and a half-pass-through of the
        rate change to WACC. Byte-identical to the legacy `_applyMacroShock` arithmetic; the only
        signature change is taking the per-year macro scalars directly (the DAG node already holds
        the macro vector) instead of `(scenario, yearIdx)`.

    Args:
        baseRevenue: the prior year's (or base-year's) revenue level, in currency units.
        baseMargin: the prior year's operating margin, in percent.
        gdp: this year's GDP growth, in percent.
        rate: this year's policy/interest rate, in percent.
        fx: this year's FX level (e.g. KRW/USD); shock is measured vs `BASELINE_FX`.
        elasticity: the sector's `SectorElasticity` (revenueToGdp / revenueToFx / marginToGdp /
            nimToRate).
        baseWacc: the base discount rate, in percent.

    Returns:
        tuple[float, float, float]: ``(adjustedRevenue, adjustedMargin, adjustedWacc)``.
        `adjustedMargin` is floored at -50 (legacy ``max(adjustedMargin, -50)``).

    Raises:
        None — pure arithmetic; callers handle absent/invalid inputs upstream.

    Example:
        >>> from dartlab.synth.scenario import SectorElasticity
        >>> e = SectorElasticity(1.8, 0.8, 50, 0, "high")  # 반도체
        >>> rev, mgn, wacc = transferMacroToFundamentals(
        ...     100.0, 10.0, gdp=-3.0, rate=1.0, fx=1600, elasticity=e, baseWacc=10.0)
        >>> round(rev, 4), round(mgn, 4), round(wacc, 4)
        (95.3075, 8.5, 9.25)

    Guide:
        This is a single year. To chain a horizon (each year's adjusted output feeds the next),
        use `transferRevenuePath`, which owns the prevRev/prevMargin carry the legacy
        `simulateScenario` performed.

    When:
        Inside a driver node that holds one year's macro scalars and needs the fundamental impact.

    How:
        Apply GDP and FX shocks to revenue, GDP and (financials) rate shocks to margin, and half
        the rate change to WACC; floor margin at -50.

    SeeAlso:
        - ``transferRevenuePath``: the horizon carry built on this function.
        - ``dartlab.synth.scenario.SectorElasticity``: the elasticity contract.
        - ``dartlab.synth.scenario.getElasticity``: sector-key -> elasticity lookup.

    Requires:
        `BASELINE_FX` / `BASELINE_RATE` from `synth.scenario` (the macro baselines the shock is
        measured against).

    AIContext:
        The output is a deterministic transform of assumptions, not a forecast — always surface
        the elasticity and the macro path used so the assumption is auditable.

    LLM Specifications:
        AntiPatterns:
            - Quoting `adjustedRevenue` as a prediction rather than a scenario transform.
            - Forgetting that FX shock is relative to `BASELINE_FX`, not absolute.
            - Assuming inflation flows through: cpi/inflation has NO transfer channel here. The
              preset (`MacroScenario.cpi`, a 3-year list) carries an inflation path but this edge
              reads only gdp/rate/fx -> revenue/margin/wacc has 0 effect from cpi (nominal-real
              undecomposed). Treat a cpi-sensitive question as out-of-channel, not transmitted.
        OutputSchema: ``tuple[float, float, float]`` = (revenue, margin %, wacc %).
        Prerequisites: numeric base metrics + a `SectorElasticity`.
        Freshness: inherits the freshness of the base metrics and the macro path supplied.
        Dataflow: (gdp, fx vs baseline) -> revenue; (gdp, rate vs baseline) -> margin;
            rate vs baseline -> wacc.
        TargetMarkets: KR (BASELINE_FX in KRW/USD); US transfer requires US baselines/elasticity.
    """
    # GDP shock
    revGdpEffect = elasticity.revenueToGdp * gdp / 100

    # FX shock (change vs baseline)
    fxChangePct = (fx - BASELINE_FX) / BASELINE_FX * 100
    revFxEffect = elasticity.revenueToFx * fxChangePct / 1000  # beta per 10%

    adjustedRevenue = baseRevenue * (1 + revGdpEffect + revFxEffect)

    # margin shock
    marginShockBps = elasticity.marginToGdp * gdp / 100
    # NIM shock (financials)
    rateChange = rate - BASELINE_RATE
    nimShockBps = elasticity.nimToRate * rateChange / 100
    adjustedMargin = baseMargin + marginShockBps + nimShockBps

    # WACC: 50% of rate change
    adjustedWacc = baseWacc + rateChange * 0.5

    return adjustedRevenue, max(adjustedMargin, -50), adjustedWacc


def transferRevenuePath(
    baseRevenue: float,
    baseMargin: float,
    gdpPath: list[float],
    ratePath: list[float],
    fxPath: list[float],
    elasticity: SectorElasticity,
    baseWacc: float,
) -> tuple[list[float], list[float], list[float]]:
    """Chain the single-year transfer over a horizon, carrying revenue/margin forward each year.

    Capabilities:
        Applies `transferMacroToFundamentals` for each year of the macro paths, feeding each
        year's adjusted revenue and margin in as the next year's base — the prevRev/prevMargin
        carry the legacy `simulateScenario` performed inside its loop (the leaf transfer itself is
        single-year). Produces the revenue / margin / WACC time vectors a `rev.path` driver node
        carries.

    Args:
        baseRevenue: the base-year revenue level (year 0's input base).
        baseMargin: the base-year operating margin (percent).
        gdpPath: per-year GDP growth (percent).
        ratePath: per-year policy/interest rate (percent).
        fxPath: per-year FX level (e.g. KRW/USD).
        elasticity: the sector's `SectorElasticity`.
        baseWacc: the base discount rate (percent), held constant as the per-year WACC base.

    Returns:
        tuple[list[float], list[float], list[float]]: ``(revPath, marginPath, waccPath)``, each of
        length ``min(len(gdpPath), len(ratePath), len(fxPath))``.

    Raises:
        None — empty/short paths simply yield a shorter (possibly empty) horizon.

    Example:
        >>> from dartlab.synth.scenario import SectorElasticity
        >>> e = SectorElasticity(1.8, 0.8, 50, 0, "high")
        >>> r, m, w = transferRevenuePath(
        ...     100.0, 10.0, [-3.0, -1.0, 0.5], [1.0, 1.5, 2.0], [1600, 1580, 1550], e, 10.0)
        >>> len(r)
        3

    Guide:
        The carry is what makes a recession compound: year 1's depressed revenue is the base year
        2 grows/shrinks from. A `proforma` node downstream converts this absolute revenue path
        into a year-over-year growth path before calling the L2 leaf (that conversion is edge
        wiring, owned by the node, not leaf math).

    When:
        Inside a `rev.path` driver node that holds the full macro horizon for one scenario.

    How:
        Loop the years, calling `transferMacroToFundamentals`, then carry (prevRev, prevMargin) =
        (adjRev, adjMargin) so each shock persists into the next year.

    SeeAlso:
        - ``transferMacroToFundamentals``: the single-year transfer this chains.
        - ``dartlab.analysis.financial.proforma.buildProforma``: the L2 leaf that consumes the
          growth path derived from this output.

    Requires:
        The three macro paths and a `SectorElasticity` (see `transferMacroToFundamentals`).

    AIContext:
        Report the full path, not just the last year — the trajectory (drawdown then recovery) is
        the point of a scenario, and the carry makes early-year shocks persist.

    LLM Specifications:
        AntiPatterns:
            - Quoting only the terminal revenue and losing the carry-driven trajectory.
            - Assuming WACC compounds — only revenue and margin carry; WACC is re-derived per year
              from the rate change vs baseline.
        OutputSchema: ``tuple[list[float], list[float], list[float]]`` (revenue, margin %, wacc %).
        Prerequisites: aligned macro paths + a `SectorElasticity`.
        Freshness: inherits the base metrics' freshness and the supplied macro path.
        Dataflow: for each year -> transferMacroToFundamentals(prevRev, prevMargin, ...) ->
            append -> carry (prevRev, prevMargin) = (adjRev, adjMargin).
        TargetMarkets: KR baseline (KRW FX); US requires US baselines/elasticity.
    """
    revPath: list[float] = []
    marginPath: list[float] = []
    waccPath: list[float] = []
    prevRev = baseRevenue
    prevMargin = baseMargin
    horizon = min(len(gdpPath), len(ratePath), len(fxPath))
    for yr in range(horizon):
        adjRev, adjMargin, adjWacc = transferMacroToFundamentals(
            prevRev, prevMargin, gdpPath[yr], ratePath[yr], fxPath[yr], elasticity, baseWacc
        )
        revPath.append(adjRev)
        marginPath.append(adjMargin)
        waccPath.append(adjWacc)
        prevRev = adjRev
        prevMargin = adjMargin
    return revPath, marginPath, waccPath
