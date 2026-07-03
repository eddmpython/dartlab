"""Expectation cycle : the sole collector/scorer sealing engine forecasts into the ledger.

Roles (mainPlan/expectation-grid/01 §2.4):
- ``issueMacro``  : call the L2 macro fan verb, seal quantile expectations plus point-in-time
  naive baselines (random-walk / persistence / seasonal-naive) into the ledger. Idempotent per
  (variable, horizon, targetPeriod, issuedLive): re-runs within the same month skip existing rows.
- ``scoreDue``    : join due unscored rows with the latest actuals and append score rows.
  Not-yet-published actuals are skipped inside a grace window; past the grace window a missing
  actual is sealed as an error row (no silent survivorship).
- ``buildScorecard`` : aggregate scores per (domain, variable, horizon, issuedLive) with the
  sample gates of mainPlan/expectation-grid/02 §4 (verified=False forces the "미검증" label).

This module is the only writer of the ledger. L2 engines stay ledger-blind; the downward-only
import contract makes that structural (L2 cannot import L2.5).
"""

from __future__ import annotations

import statistics
from datetime import datetime, timezone
from pathlib import Path

from dartlab.simulate.expectationLedger import (
    appendExpectations,
    appendScores,
    readExpectations,
    readScores,
)
from dartlab.synth.expectationSpec import (
    ExpectationScore,
    ExpectationSpec,
    aggregateCalibration,
    buildExpectationId,
    scoreExpectation,
)

_Z = {5: -1.645, 25: -0.674, 50: 0.0, 75: 0.674, 95: 1.645}
_ENGINE_MACRO = "macro.simulate.simulateMacro"
# (fan label, gather seriesId, fan quantile key prefix). level vars use "q", logdiff100 "level_q".
_MACRO_VARS: dict[str, tuple[tuple[str, str, str], ...]] = {
    "KR": (
        ("소비자물가", "CPI", "level_q"),
        ("기준금리", "BASE_RATE", "q"),
        ("원/달러", "USDKRW", "level_q"),
    ),
}
_MIN_N_BY_FREQ = {"M": 24, "Q": 40, "Y": 40}
_SCORE_GRACE_MONTHS = 2  # target this many months past due with no actual -> sealed error row


def _nowUtc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="minutes")


def _ymAdd(ym: str, k: int) -> str:
    y, m = int(ym[:4]), int(ym[5:7])
    t = y * 12 + (m - 1) + k
    return f"{t // 12}-{t % 12 + 1:02d}"


def _ymDiff(a: str, b: str) -> int:
    """Months from b to a (a minus b)."""
    return (int(a[:4]) * 12 + int(a[5:7])) - (int(b[:4]) * 12 + int(b[5:7]))


def _existingKeys(baseDir: Path | None) -> set[tuple[str, int, str, bool]]:
    df = readExpectations(baseDir=baseDir)
    if df is None:
        return set()
    return {
        (r["variable"], r["horizon"], r["targetPeriod"], r["issuedLive"])
        for r in df.select(["variable", "horizon", "targetPeriod", "issuedLive"]).iter_rows(named=True)
    }


def issueMacro(
    *,
    market: str = "KR",
    asOf: str | None = None,
    live: bool = True,
    horizons: tuple[int, ...] = (1, 3, 6, 12),
    baseDir: Path | None = None,
    simResult=None,
    monthlyBySeries: dict[str, dict[str, float]] | None = None,
) -> list[ExpectationSpec]:
    """Issue macro fan expectations for the market's grid variables and seal them.

    Args:
        market: fan market ("KR" v1).
        asOf: data vintage 'YYYY-MM-DD'; None = latest (live issuance).
        live: False marks rows as backfill (never mixed into live scorecards).
        horizons: months ahead to seal.
        baseDir: ledger root override (tests).
        simResult: injected MacroSimResult (테스트용, skips the L2 call).
        monthlyBySeries: injected {seriesId: {ym: value}} point-in-time history (테스트용).

    Returns:
        The sealed rows actually appended (idempotent: existing keys are skipped).
    """
    if simResult is None or monthlyBySeries is None:
        from dartlab.macro.seriesFetch import fetchMonthlyDict, getGather
        from dartlab.macro.simulate import simulateMacro
    if simResult is None:
        simResult = simulateMacro(market, horizon=max(horizons), asOf=asOf)
    if simResult.status != "ok" or not simResult.fan:
        raise ValueError(f"simulateMacro 실패: status={simResult.status} missing={simResult.missing}")
    endYm = (simResult.model.get("endYm") if isinstance(simResult.model, dict) else None) or (asOf or _nowUtc())[:7]
    if monthlyBySeries is None:
        gPit = getGather(asOf)
        monthlyBySeries = {sid: fetchMonthlyDict(gPit, sid) or {} for _, sid, _ in _MACRO_VARS[market]}

    issuedAt = _nowUtc()
    existing = _existingKeys(baseDir)
    rows: list[ExpectationSpec] = []
    for label, sid, qPrefix in _MACRO_VARS[market]:
        rec = simResult.fan.get(label)
        monthly = monthlyBySeries.get(sid) or {}
        histYms = sorted(ym for ym in monthly if ym <= endYm)
        if rec is None or len(histYms) < 24:
            continue
        lastLevel = monthly[histYms[-1]]
        diffs = [monthly[b] - monthly[a] for a, b in zip(histYms[-61:-1], histYms[-60:])]
        sigma = statistics.pstdev(diffs) if len(diffs) >= 12 else 0.0
        for h in horizons:
            targetPeriod = _ymAdd(endYm, h)
            variable = f"{market}.{sid}"
            if (variable, h, targetPeriod, live) in existing:
                continue
            # data-lag honesty: a target month already elapsed at issuance is out-of-model-sample
            # but not a genuine future claim. Seal the fact so scorecards can segregate it.
            rowWarnings = () if live else ("backfill",)
            if _ymDiff(issuedAt[:7], targetPeriod) >= 1:
                rowWarnings = rowWarnings + ("targetElapsedAtIssue",)
            quantiles = {k: float(rec[f"{qPrefix}{k}"][h - 1]) for k in _Z}
            se = sigma * (h**0.5)
            seasonal = monthly.get(_ymAdd(targetPeriod, -12))
            rows.append(
                ExpectationSpec(
                    expectationId=buildExpectationId("macro", variable, "M", h, targetPeriod, issuedAt),
                    domain="macro",
                    variable=variable,
                    unit="level",
                    freq="M",
                    horizon=h,
                    targetPeriod=targetPeriod,
                    issuedAt=issuedAt,
                    issuedLive=live,
                    asOf=asOf or issuedAt[:10],
                    engine=_ENGINE_MACRO,
                    engineVersion="bvar-v1",
                    kind="quantiles",
                    quantiles=quantiles,
                    baselines={
                        "randomWalk": {k: lastLevel + z * se for k, z in _Z.items()},
                        "persistence": lastLevel,
                        "seasonalNaive": seasonal,
                    },
                    sourceRefs=(f"hf://macro/{sid}", f"endYm={endYm}"),
                    warnings=rowWarnings,
                )
            )
    appendExpectations(rows, baseDir=baseDir)
    return rows


def scoreDue(
    *,
    now: str | None = None,
    baseDir: Path | None = None,
    monthlyBySeries: dict[str, dict[str, float]] | None = None,
) -> list[ExpectationScore]:
    """Score due unscored rows against the latest actuals; seal errors past the grace window.

    Args:
        now: 'YYYY-MM' clock override (테스트용). Default = current UTC month.
        baseDir: ledger root override.
        monthlyBySeries: injected latest actuals {seriesId: {ym: value}} (테스트용).

    Returns:
        Appended score rows. A target month is due once it is at least 1 month in the past;
        a due row with no actual inside _SCORE_GRACE_MONTHS stays pending (publication lag),
        beyond it the miss is sealed as an error row.
    """
    due = readExpectations(baseDir=baseDir, unscoredOnly=True)
    if due is None or due.height == 0:
        return []
    nowYm = (now or _nowUtc())[:7]
    scoredAt = _nowUtc()
    if monthlyBySeries is None:
        from dartlab.macro.seriesFetch import fetchMonthlyDict, getGather

        g = getGather(None)
        sids = {r.split(".", 1)[1] for r in due.get_column("variable").to_list()}
        monthlyBySeries = {sid: fetchMonthlyDict(g, sid) or {} for sid in sids}

    from dartlab.simulate.expectationLedger import specFromRow

    scores: list[ExpectationScore] = []
    for row in due.iter_rows(named=True):
        if row["domain"] != "macro":
            continue  # revenue/earnings/credit scoring lands in later phases
        age = _ymDiff(nowYm, row["targetPeriod"])
        if age < 1:
            continue  # not due yet
        sid = row["variable"].split(".", 1)[1]
        actual = monthlyBySeries.get(sid, {}).get(row["targetPeriod"])
        if actual is None and age < 1 + _SCORE_GRACE_MONTHS:
            continue  # publication lag: stay pending, do not seal an error yet
        scores.append(scoreExpectation(specFromRow(row), actual, scoredAt=scoredAt, actualAsOf=scoredAt[:10]))
    appendScores(scores, baseDir=baseDir)
    return scores


def buildScorecard(*, baseDir: Path | None = None) -> dict:
    """Aggregate the ledger into the scorecard payload consumed by the terminal.

    Returns:
        dict with generatedAt, totals, and per-group calibration where each group key is
        ``{domain}.{variable}.h{horizon}.{live|backfill}``. Groups below the sample gate carry
        verified=False; the display contract is that unverified groups render the fixed
        "발행 n건 축적 중 · 캘리브레이션 미검증" label and no performance numbers.
    """
    exps = readExpectations(baseDir=baseDir)
    scores = readScores(baseDir=baseDir)
    card: dict = {
        "schemaVersion": 1,
        "generatedAt": _nowUtc(),
        "displayPolicy": "verified=False 그룹은 성과 숫자 렌더링 금지(고정 미검증 라벨만)",
        "totals": {"issued": 0, "scored": 0, "unscored": 0, "errorRows": 0},
        "groups": {},
    }
    if exps is None:
        return card
    card["totals"]["issued"] = exps.height
    if scores is None:
        card["totals"]["unscored"] = exps.height
        return card
    meta = {
        r["expectationId"]: r
        for r in exps.select(["expectationId", "domain", "variable", "horizon", "freq", "issuedLive"]).iter_rows(
            named=True
        )
    }
    grouped: dict[str, list] = {}
    seen: set[str] = set()
    for row in scores.iter_rows(named=True):
        m = meta.get(row["expectationId"])
        if m is None:
            continue
        seen.add(row["expectationId"])
        key = f"{m['domain']}.{m['variable']}.h{m['horizon']}.{'live' if m['issuedLive'] else 'backfill'}"
        grouped.setdefault(key, []).append((m, row))
    card["totals"]["scored"] = len(seen)
    card["totals"]["unscored"] = exps.height - len(seen)
    for key, pairs in sorted(grouped.items()):
        m0 = pairs[0][0]
        scoreRows = [
            ExpectationScore(
                expectationId=r["expectationId"],
                scoredAt=r["scoredAt"],
                actual=r["actual"],
                actualAsOf=r["actualAsOf"],
                coverageHit90=r["coverageHit90"],
                coverageHit50=r["coverageHit50"],
                pit=r["pit"],
                crps=r["crps"],
                skill=r["skill"],
                brier=r["brier"],
                error=r["error"],
            )
            for _, r in pairs
        ]
        agg = aggregateCalibration(scoreRows, minN=_MIN_N_BY_FREQ.get(m0["freq"], 40))
        card["totals"]["errorRows"] += agg.get("errorRows", 0)
        card["groups"][key] = agg
    return card
