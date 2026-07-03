"""Expectation cycle : the sole collector/scorer sealing engine forecasts into the ledger.

Roles (mainPlan/expectation-grid/01 §2.4):
- ``issueMacro``  : call the L2 macro fan verb, seal quantile expectations plus point-in-time
  naive baselines (random-walk / persistence / seasonal-naive) into the ledger. Idempotent per
  (variable, horizon, targetPeriod, issuedLive): re-runs within the same month skip existing rows.
- ``scoreDue``    : join due unscored rows with the latest actuals and append score rows.
  Not-yet-published actuals are skipped inside a grace window; past the grace window a missing
  actual is sealed as an error row (no silent survivorship).
- ``buildScorecard`` : aggregate scores per (domain, variable, freq, horizon, issuedLive) with the
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
    appendProformaRows,
    appendScores,
    readExpectations,
    readProforma,
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

_ENGINE_REVENUE = "analysis.forecast.revenueForecast.forecastRevenue"
_ENGINE_EARNINGS = "analysis.financial.proforma.buildProforma"
_TAIL_FACTOR = 1.645 / 0.674  # normal approx: p5/p95 from the p25/p75 spread (z-ratio)
_REV_DUE_MONTH = 4  # FY{Y} annual report filed by end of March -> due from {Y+1}-04
_REV_GRACE_MONTHS = 3  # due + grace with no actual -> sealed error row
_QTR_DUE_LAG_MONTHS = 2  # 분기보고서 45일 규정 -> 분기말 +2개월부터 채점 시도
_ENGINE_SEASONAL = "analysis.forecast.scenarioSim.seasonalSharesFromYearQuarters"
# 분기 발행 계정: (지표, 부모 도메인, proforma 계정). scenarioSim 전례(매출·영업이익만,
# 순이익은 분기 부호 요동으로 비중 분해가 무의미) 를 따른다.
_QTR_METRICS = (("revenue", "revenue", "revenue"), ("operatingProfit", "earnings", "operating_income"))
# ledger metric -> (finance series section, key) for annual actuals. fcf joins in P4b once a
# CF-based actual definition is sealed (no expectation without a scoreable actual).
_METRIC_KEYS = {
    "revenue": ("IS", "sales"),
    "operatingProfit": ("IS", "operating_profit"),
    "netIncome": ("IS", "net_profit"),
}
_EARNINGS_METRICS = (("operatingProfit", "operating_income"), ("netIncome", "net_income"))
# 추정 3표 구조화 봉인 계정 (ProFormaYear 전 필드). 요약 3숫자와 별개로 계정 단위 원장을 남긴다.
_PF_ACCOUNTS: tuple[tuple[str, str], ...] = (
    ("IS", "revenue"),
    ("IS", "cogs"),
    ("IS", "gross_profit"),
    ("IS", "sga"),
    ("IS", "depreciation"),
    ("IS", "operating_income"),
    ("IS", "interest_expense"),
    ("IS", "ebt"),
    ("IS", "tax"),
    ("IS", "net_income"),
    ("IS", "ebitda"),
    ("BS", "cash"),
    ("BS", "receivables"),
    ("BS", "inventories"),
    ("BS", "other_current_assets"),
    ("BS", "current_assets"),
    ("BS", "ppe_net"),
    ("BS", "other_noncurrent_assets"),
    ("BS", "total_assets"),
    ("BS", "payables"),
    ("BS", "short_term_debt"),
    ("BS", "other_current_liabilities"),
    ("BS", "current_liabilities"),
    ("BS", "long_term_debt"),
    ("BS", "other_noncurrent_liabilities"),
    ("BS", "total_liabilities"),
    ("BS", "retained_earnings"),
    ("BS", "total_equity"),
    ("CF", "ocf"),
    ("CF", "capex"),
    ("CF", "fcf"),
    ("CF", "dividends"),
    ("CF", "financing_cf"),
    ("CF", "net_cash_change"),
)
_ENGINE_CREDIT = "credit.monitoring.history+scoring.migration"
_ENGINE_PRICE = "analysis.forecast.simulation.monteCarloForecast"
_CREDIT_GRACE_MONTHS = 2
_PRICE_GRACE_MONTHS = 2


def _nowUtc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="minutes")


def _ymAdd(ym: str, k: int) -> str:
    y, m = int(ym[:4]), int(ym[5:7])
    t = y * 12 + (m - 1) + k
    return f"{t // 12}-{t % 12 + 1:02d}"


def _ymDiff(a: str, b: str) -> int:
    """Months from b to a (a minus b)."""
    return (int(a[:4]) * 12 + int(a[5:7])) - (int(b[:4]) * 12 + int(b[5:7]))


def _nextQuarter(ym: str) -> str:
    """The quarter after the one containing ym (e.g. '2026-07' -> '2026Q4')."""
    y, q = int(ym[:4]), (int(ym[5:7]) - 1) // 3 + 1
    return f"{y + 1}Q1" if q == 4 else f"{y}Q{q + 1}"


def _quarterEndYm(quarter: str) -> str:
    """'2026Q4' -> '2026-12'."""
    return f"{quarter[:4]}-{int(quarter[5]) * 3:02d}"


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


def _annualMetricMap(company, section: str = "IS", key: str = "sales") -> dict[int, float]:
    """Complete-fiscal-year sums of a quarterly finance series metric (4 quarters required)."""
    ts = company._buildFinanceSeries(freq="Q")
    series, labels = ts if isinstance(ts, tuple) else (ts, [])
    vals = (series.get(section) or {}).get(key) or []
    byYear: dict[int, list[float]] = {}
    for lab, v in zip(labels, vals):
        if v is None:
            continue
        byYear.setdefault(int(str(lab)[:4]), []).append(float(v))
    return {y: sum(vs) for y, vs in byYear.items() if len(vs) == 4}


def _annualRevenueMap(company) -> dict[int, float]:
    """Complete-fiscal-year revenue sums (compat wrapper over _annualMetricMap)."""
    return _annualMetricMap(company, "IS", "sales")


def issueRevenue(
    codes: list[str],
    *,
    live: bool = True,
    horizons: tuple[int, ...] = (1, 2, 3),
    baseDir: Path | None = None,
    resultByCode: dict | None = None,
    annualByCode: dict[str, dict[int, float]] | None = None,
) -> tuple[list[ExpectationSpec], dict[str, str]]:
    """Issue annual revenue quantile expectations per company and seal them (KR).

    The Bull/Base/Bear scenario paths of the L2 revenue engine map to p75/p50/p25; p5/p95
    tails extend the quartile spread under a normal approximation. The approximation is
    sealed as a warning on every row ("scenarioQuantileApprox"). On the real path each
    issuance is dual-written to the domain record via ``recordForecast`` (09 P9c write-end).

    Args:
        codes: 6-digit stock codes.
        live: False = backfill rows.
        horizons: fiscal years ahead (bounded by the engine's scenario path length).
        baseDir: ledger root override (tests).
        resultByCode: injected {code: RevenueForecastResult-like} (테스트용, skips Company).
        annualByCode: injected {code: {fiscalYear: revenue}} history (테스트용).

    Returns:
        (sealed rows, skipped census {code: reason}). Skips are returned, never silent.
    """
    issuedAt = _nowUtc()
    existing = _existingKeys(baseDir)
    rows: list[ExpectationSpec] = []
    skipped: dict[str, str] = {}
    for code in codes:
        try:
            if resultByCode is not None:
                result = resultByCode.get(code)
                annual = (annualByCode or {}).get(code) or {}
            else:
                import dartlab
                from dartlab.analysis.financial._forecastCalcsHelpers import _runForecastRevenue

                with dartlab.Company(code) as company:  # 힙 가드: with = OomTripwire + cleanupCache
                    annual = _annualRevenueMap(company)
                    result = _runForecastRevenue(company)
            if result is None or not getattr(result, "projected", None):
                skipped[code] = "예측 불가(projected 없음)"
                continue
            scen = getattr(result, "scenarios", None) or {}
            basePath, bullPath, bearPath = scen.get("base"), scen.get("bull"), scen.get("bear")
            if not (basePath and bullPath and bearPath):
                skipped[code] = "시나리오 경로 없음"
                continue
            if not annual:
                skipped[code] = "연간 실적 이력 없음"
                continue
            baseYear = max(annual)
            hist = [annual[y] for y in sorted(annual)][-11:]
            diffs = [b - a for a, b in zip(hist, hist[1:])]
            sigma = statistics.pstdev(diffs) if len(diffs) >= 3 else 0.0
            lastRev = hist[-1]
            issuedAny = False
            for h in horizons:
                if h > len(basePath):
                    continue
                targetPeriod = f"FY{baseYear + h}"
                variable = f"{code}.revenue"
                if (variable, h, targetPeriod, live) in existing:
                    continue
                p25, p50, p75 = sorted([bearPath[h - 1], basePath[h - 1], bullPath[h - 1]])
                quantiles = {
                    5: p50 - _TAIL_FACTOR * max(p50 - p25, 0.0),
                    25: p25,
                    50: p50,
                    75: p75,
                    95: p50 + _TAIL_FACTOR * max(p75 - p50, 0.0),
                }
                se = sigma * (h**0.5)
                rowWarnings = ("scenarioQuantileApprox",) + (() if live else ("backfill",))
                rows.append(
                    ExpectationSpec(
                        expectationId=buildExpectationId("revenue", variable, "Y", h, targetPeriod, issuedAt),
                        domain="revenue",
                        variable=variable,
                        unit="KRW",
                        freq="Y",
                        horizon=h,
                        targetPeriod=targetPeriod,
                        issuedAt=issuedAt,
                        issuedLive=live,
                        asOf=issuedAt[:10],
                        engine=_ENGINE_REVENUE,
                        engineVersion=str(getattr(result, "method", "") or "ensemble"),
                        kind="quantiles",
                        quantiles=quantiles,
                        baselines={
                            "randomWalk": {k: lastRev + z * se for k, z in _Z.items()} if se > 0 else None,
                            "persistence": lastRev,
                            "seasonalNaive": None,
                        },
                        sourceRefs=(f"dart://{code}", f"baseFY={baseYear}"),
                        warnings=rowWarnings,
                    )
                )
                issuedAny = True
            if issuedAny and resultByCode is None and live:
                from dartlab.analysis.forecast.forwardTest import recordForecast

                recordForecast(
                    stockCode=code,
                    horizon=len(basePath),
                    projected=list(result.projected),
                    scenarios={k: list(v) for k, v in scen.items()},
                    sourcesUsed=list(getattr(result, "sources", []) or []),
                    assumptions=list(getattr(result, "assumptions", []) or []),
                )
        except (ValueError, KeyError, AttributeError, TypeError) as exc:
            skipped[code] = f"{type(exc).__name__}: {exc}"
    appendExpectations(rows, baseDir=baseDir)
    return rows, skipped


def issueEarnings(
    codes: list[str],
    *,
    live: bool = True,
    horizons: tuple[int, ...] = (1, 2, 3),
    baseDir: Path | None = None,
    proformaFn=None,
    seriesByCode: dict | None = None,
    annualByCode: dict[str, dict[int, float]] | None = None,
) -> tuple[list[ExpectationSpec], dict[str, str]]:
    """Derive OP/NI expectations from sealed revenue quantile paths via the proforma leaf.

    Not a free forecast: each earnings row is the deterministic accounting cascade
    (``buildProforma`` L2 leaf, the same leaf the simulate DAG uses) applied to the p25/p50/p75
    revenue paths already sealed in the ledger. Lineage: sourceRefs carries the parent revenue
    expectationId. Monotone-cascade approximation is sealed as "revenueQuantileMapped".

    Args:
        codes: stock codes with sealed revenue expectations.
        live: backfill flag (must match the parent revenue rows).
        horizons: fiscal years ahead.
        baseDir: ledger root override.
        proformaFn: injected (series, growthPathPct, name) -> ProFormaResult-like (테스트용).
        seriesByCode: injected finance series dict (테스트용).
        annualByCode: injected {code: {fy: revenue}} for base-year revenue (테스트용).

    Returns:
        (sealed rows, skipped census).
    """
    issuedAt = _nowUtc()
    existing = _existingKeys(baseDir)
    exps = readExpectations(baseDir=baseDir)
    rows: list[ExpectationSpec] = []
    pfRows: list[dict] = []
    pfDf = readProforma(baseDir=baseDir)
    pfExisting: set[tuple[str, str, int]] = (
        set()
        if pfDf is None
        else {
            (r["parentId"], r["targetPeriod"], r["quantile"])
            for r in pfDf.select(["parentId", "targetPeriod", "quantile"]).unique().iter_rows(named=True)
        }
    )
    skipped: dict[str, str] = {}
    for code in codes:
        try:
            revRows = (
                []
                if exps is None
                else [
                    r
                    for r in exps.iter_rows(named=True)
                    if r["domain"] == "revenue"
                    and r["variable"] == f"{code}.revenue"
                    and r["freq"] == "Y"  # 분기 행(issueQuarterlyIs) 혼입 시 연간 캐스케이드 오염
                    and r["issuedLive"] == live
                ]
            )
            if not revRows:
                skipped[code] = "매출 기대 없음(선행 issueRevenue 필요)"
                continue
            latest = max(r["issuedAt"] for r in revRows)
            revByH = {r["horizon"]: r for r in revRows if r["issuedAt"] == latest}
            if seriesByCode is not None:
                series = seriesByCode.get(code)
                annual = (annualByCode or {}).get(code) or {}
            else:
                import dartlab

                with dartlab.Company(code) as company:  # 힙 가드: with = OomTripwire + cleanupCache
                    ts = company._buildFinanceSeries(freq="Q")
                    series = ts[0] if isinstance(ts, tuple) else ts
                    annual = _annualMetricMap(company, "IS", "sales")
            if not annual:
                skipped[code] = "연간 매출 이력 없음"
                continue
            baseFY = max(annual)
            baseRev = annual[baseFY]
            maxH = max(h for h in horizons if h in revByH)
            import json as _json

            pathByQ: dict[int, list[float]] = {}
            for q in (25, 50, 75):
                prev, growth = baseRev, []
                for h in range(1, maxH + 1):
                    if h not in revByH:
                        break
                    qv = _json.loads(revByH[h]["quantiles"])[str(q)]
                    growth.append((qv / prev - 1.0) * 100.0)
                    prev = qv
                pathByQ[q] = growth
            if proformaFn is None:
                from dartlab.analysis.financial.proforma import buildProforma as proformaLeaf
            else:
                proformaLeaf = None
            pfByQ = {}
            for q, growth in pathByQ.items():
                fn = proformaFn or (lambda s, g, n: proformaLeaf(s, revenueGrowthPath=g, scenarioName=n))
                pfByQ[q] = fn(series, growth, f"expGrid_p{q}")
            # E-3표 구조화 봉인 (05 §2): 요약 3숫자와 별개, 자체 존재키로 idempotent.
            for h in range(1, maxH + 1):
                if h not in revByH:
                    continue
                parentId = revByH[h]["expectationId"]
                pfTarget = f"FY{baseFY + h}"
                for q in (25, 50, 75):
                    if (parentId, pfTarget, q) in pfExisting:
                        continue
                    pfYear = pfByQ[q].projections[h - 1]
                    for stmt, account in _PF_ACCOUNTS:
                        pfRows.append(
                            {
                                "parentId": parentId,
                                "code": code,
                                "issuedAt": issuedAt,
                                "issuedLive": live,
                                "targetPeriod": pfTarget,
                                "quantile": q,
                                "statement": stmt,
                                "account": account,
                                "value": float(getattr(pfYear, account, 0.0) or 0.0),
                                "bsBalanced": bool(getattr(pfYear, "bs_balanced", True)),
                            }
                        )
            for metric, pfAttr in _EARNINGS_METRICS:
                for h in range(1, maxH + 1):
                    if h not in revByH:
                        continue
                    variable = f"{code}.{metric}"
                    targetPeriod = f"FY{baseFY + h}"
                    if (variable, h, targetPeriod, live) in existing:
                        continue
                    tri = sorted(float(getattr(pfByQ[q].projections[h - 1], pfAttr)) for q in (25, 50, 75))
                    p25, p50, p75 = tri
                    quantiles = {
                        5: p50 - _TAIL_FACTOR * max(p50 - p25, 0.0),
                        25: p25,
                        50: p50,
                        75: p75,
                        95: p50 + _TAIL_FACTOR * max(p75 - p50, 0.0),
                    }
                    rows.append(
                        ExpectationSpec(
                            expectationId=buildExpectationId("earnings", variable, "Y", h, targetPeriod, issuedAt),
                            domain="earnings",
                            variable=variable,
                            unit="KRW",
                            freq="Y",
                            horizon=h,
                            targetPeriod=targetPeriod,
                            issuedAt=issuedAt,
                            issuedLive=live,
                            asOf=issuedAt[:10],
                            engine=_ENGINE_EARNINGS,
                            engineVersion="proforma-cascade",
                            kind="quantiles",
                            quantiles=quantiles,
                            baselines={"persistence": None, "seasonalNaive": None, "randomWalk": None},
                            sourceRefs=(revByH[h]["expectationId"], f"baseFY={baseFY}"),
                            warnings=("revenueQuantileMapped", "scenarioQuantileApprox")
                            + (() if live else ("backfill",)),
                        )
                    )
        except (ValueError, KeyError, AttributeError, TypeError, RuntimeError, OSError) as exc:
            skipped[code] = f"{type(exc).__name__}: {exc}"
    appendExpectations(rows, baseDir=baseDir)
    appendProformaRows(pfRows, baseDir=baseDir)
    return rows, skipped


def _seriesSeasonality(series, periods: list[str], key: str, years: list[str]) -> list[float]:
    """_buildFinanceSeries(freq="Q") 시계열에서 Q1~Q4 비중 (panel("is") 는 Q4 열이 없어 부적합)."""
    vals = (series.get("IS") or {}).get(key) or []
    byYear: dict[str, list] = {}
    for p, v in zip(periods, vals):
        if "-Q" not in p or v is None:
            continue
        y, q = p.split("-Q")
        if y in years:
            byYear.setdefault(y, [None] * 4)[int(q) - 1] = float(v)
    complete = {y: qs for y, qs in byYear.items() if all(x is not None for x in qs)}
    from dartlab.analysis.forecast.scenarioSim import seasonalSharesFromYearQuarters

    return seasonalSharesFromYearQuarters(complete)


def _latestAnnualByH(exps, *, domain: str, variable: str, live: bool) -> dict[int, dict]:
    """최신 발행 연간 기대 행 {horizon: row} (없으면 빈 dict)."""
    cand = [
        r
        for r in exps.iter_rows(named=True)
        if r["domain"] == domain and r["variable"] == variable and r["freq"] == "Y" and r["issuedLive"] == live
    ]
    if not cand:
        return {}
    latest = max(r["issuedAt"] for r in cand)
    return {r["horizon"]: r for r in cand if r["issuedAt"] == latest}


def issueQuarterlyIs(
    codes: list[str],
    *,
    live: bool = True,
    years: tuple[int, ...] = (1, 2),
    baseDir: Path | None = None,
    seasonalityByCode: dict[str, tuple[list[float], list[float]]] | None = None,
    now: str | None = None,
) -> tuple[list[ExpectationSpec], dict[str, str]]:
    """Split the sealed Y1 annual quantiles into quarterly IS expectations (매출·영업이익).

    Not a new forecast: each quarterly row is the deterministic seasonal split of the annual
    quantile row ALREADY sealed in the ledger (parent lineage in sourceRefs). Seasonal shares
    come from the L2 core ``scenarioSim.seasonalSharesFromYearQuarters`` fed by the company's
    ``_buildFinanceSeries(freq="Q")`` quarters (3-year Q1~Q4 mean shares; panel("is") is not
    usable here: its window lacks Q4 columns), so scenario coherence holds: every quantile
    path is one scenario scaled by the same shares.
    Metrics follow the scenarioSim precedent (매출·영업이익; 순이익은 분기 부호 요동으로 제외).
    Live issuance only covers quarters not yet ended at issue time (look-ahead 차단); horizon
    is the quarter's position in the fiscal year (1~4), so re-sweeps stay idempotent per
    (variable, horizon, targetPeriod, issuedLive) and the scorecard pools by quarter position.
    Baselines are sealed as None like issueEarnings (skill 미산출 부채, P4b 트랙).

    Args:
        codes: stock codes with sealed annual revenue expectations.
        live: backfill flag (parent rows must match).
        years: annual parent horizons to split (기본 Y1·Y2 -> 당해 잔여분기 + 차년 4분기).
        baseDir: ledger root override.
        seasonalityByCode: injected {code: (revW, oiW)} 4-weights (테스트용, skips Company).
        now: 'YYYY-MM' clock override (테스트용).

    Returns:
        (sealed rows, skipped census).
    """
    import json as _json

    issuedAt = _nowUtc()
    nowYm = (now or issuedAt)[:7]
    existing = _existingKeys(baseDir)
    exps = readExpectations(baseDir=baseDir)
    rows: list[ExpectationSpec] = []
    pfRows: list[dict] = []
    pfDf = readProforma(baseDir=baseDir)
    pfExisting: set[tuple[str, str, int]] = (
        set()
        if pfDf is None
        else {
            (r["parentId"], r["targetPeriod"], r["quantile"])
            for r in pfDf.select(["parentId", "targetPeriod", "quantile"]).unique().iter_rows(named=True)
        }
    )
    skipped: dict[str, str] = {}
    if exps is None:
        return rows, dict.fromkeys(codes, "원장 비어있음(선행 issueRevenue 필요)")
    for code in codes:
        try:
            revByH = _latestAnnualByH(exps, domain="revenue", variable=f"{code}.revenue", live=live)
            hs = [h for h in years if h in revByH]
            if not hs:
                skipped[code] = "연간 매출 기대 없음(h1, 선행 issueRevenue 필요)"
                continue
            opByH = _latestAnnualByH(exps, domain="earnings", variable=f"{code}.operatingProfit", live=live)
            baseFy = int(revByH[hs[0]]["targetPeriod"][2:]) - hs[0]  # "FY2026", h=1 -> 기준 2025
            if seasonalityByCode is not None:
                revW, oiW = seasonalityByCode[code]
            else:
                import dartlab

                seasonYears = [str(baseFy - i) for i in range(3) if baseFy - i >= 2019]
                with dartlab.Company(code) as company:  # 힙 가드: with = OomTripwire + cleanupCache
                    ts = company._buildFinanceSeries(freq="Q")
                    series = ts[0] if isinstance(ts, tuple) else ts
                    periods = ts[1] if isinstance(ts, tuple) else []
                revW = _seriesSeasonality(series, periods, "sales", seasonYears)
                oiW = _seriesSeasonality(series, periods, "operating_profit", seasonYears)
            for hy in hs:
                fy = int(revByH[hy]["targetPeriod"][2:])
                parentByMetric = {"revenue": (revByH[hy], revW), "operatingProfit": (opByH.get(hy), oiW)}
                revParentId = revByH[hy]["expectationId"]
                for q in range(1, 5):
                    targetPeriod = f"{fy}Q{q}"
                    if live and _quarterEndYm(targetPeriod) < nowYm:
                        continue  # 이미 끝난 분기: 라이브 기대가 아니다 (look-ahead 차단)
                    for metric, domain, pfAccount in _QTR_METRICS:
                        parent, weights = parentByMetric[metric]
                        if parent is None:
                            continue  # 연간 부모 없음(예: 영업이익 미발행) -> 매출만 분해
                        variable = f"{code}.{metric}"
                        w = weights[q - 1]
                        annualQ = {int(k): float(v) for k, v in _json.loads(parent["quantiles"]).items()}
                        flat = all(abs(x - 0.25) < 1e-9 for x in weights)
                        if (variable, q, targetPeriod, live) not in existing:
                            rows.append(
                                ExpectationSpec(
                                    expectationId=buildExpectationId(domain, variable, "Q", q, targetPeriod, issuedAt),
                                    domain=domain,
                                    variable=variable,
                                    unit="KRW",
                                    freq="Q",
                                    horizon=q,
                                    targetPeriod=targetPeriod,
                                    issuedAt=issuedAt,
                                    issuedLive=live,
                                    asOf=issuedAt[:10],
                                    engine=_ENGINE_SEASONAL,
                                    engineVersion="seasonalShares3y",
                                    kind="quantiles",
                                    quantiles={k: v * w for k, v in annualQ.items()},
                                    baselines={"persistence": None, "seasonalNaive": None, "randomWalk": None},
                                    sourceRefs=(parent["expectationId"], f"share={w:.4f}"),
                                    warnings=("seasonalSplitOfAnnual", "scenarioQuantileApprox")
                                    + (("flatSeasonalityFallback",) if flat else ())
                                    + (() if live else ("backfill",)),
                                )
                            )
                        # E-3표 분기 행: 계보 앵커 = 해당 연도 매출 부모 (issueEarnings 관례 동일)
                        for quantile in (25, 50, 75):
                            if (revParentId, targetPeriod, quantile) in pfExisting:
                                continue
                            pfRows.append(
                                {
                                    "parentId": revParentId,
                                    "code": code,
                                    "issuedAt": issuedAt,
                                    "issuedLive": live,
                                    "targetPeriod": targetPeriod,
                                    "quantile": quantile,
                                    "statement": "IS",
                                    "account": pfAccount,
                                    "value": annualQ[quantile] * w,
                                    "bsBalanced": True,
                                }
                            )
        except (ValueError, KeyError, AttributeError, TypeError, RuntimeError, OSError) as exc:
            skipped[code] = f"{type(exc).__name__}: {exc}"
    appendExpectations(rows, baseDir=baseDir)
    appendProformaRows(pfRows, baseDir=baseDir)
    return rows, skipped


def issueCredit(
    codes: list[str],
    *,
    live: bool = True,
    baseDir: Path | None = None,
    historyByCode: dict[str, list[dict]] | None = None,
    stayProbByGrade: dict[str, float] | None = None,
) -> tuple[list[ExpectationSpec], dict[str, str]]:
    """Issue next-quarter grade-retention direction expectations from credit history.

    prob = the transition-matrix diagonal for the current grade (CreditMetrics cohort),
    predicted = "stay", the current grade sealed in the direction payload for later scoring.
    Companies without a recorded grade history are skipped into the census (the credit
    engine's recordGrade populates history as it runs).

    Args:
        codes: stock codes.
        live: backfill flag.
        baseDir: ledger root override.
        historyByCode: injected {code: history entries} (테스트용).
        stayProbByGrade: injected {grade: stay probability} (테스트용).
    """
    issuedAt = _nowUtc()
    existing = _existingKeys(baseDir)
    rows: list[ExpectationSpec] = []
    skipped: dict[str, str] = {}
    if stayProbByGrade is None:
        from dartlab.credit.scoring.migration import buildTransitionMatrix

        tm = buildTransitionMatrix()
        stayProbByGrade = {r["from_rating"]: float(r.get(r["from_rating"], 0.0)) for r in tm.iter_rows(named=True)}
    for code in codes:
        try:
            if historyByCode is not None:
                hist = historyByCode.get(code) or []
            else:
                from dartlab.credit.monitoring.history import loadHistory

                hist = loadHistory(code)
            if not hist:
                skipped[code] = "credit 이력 없음(recordGrade 미축적)"
                continue
            last = hist[-1]
            grade = last.get("grade") or (last.get("result") or {}).get("grade")
            if not grade or grade not in stayProbByGrade:
                skipped[code] = f"등급 해석 불가: {grade}"
                continue
            targetPeriod = _nextQuarter(issuedAt[:7])
            variable = f"{code}.grade"
            if (variable, 1, targetPeriod, live) in existing:
                continue
            rows.append(
                ExpectationSpec(
                    expectationId=buildExpectationId("credit", variable, "Q", 1, targetPeriod, issuedAt),
                    domain="credit",
                    variable=variable,
                    unit="grade",
                    freq="Q",
                    horizon=1,
                    targetPeriod=targetPeriod,
                    issuedAt=issuedAt,
                    issuedLive=live,
                    asOf=issuedAt[:10],
                    engine=_ENGINE_CREDIT,
                    engineVersion="cohort-v1",
                    kind="direction",
                    direction={"prob": stayProbByGrade[grade], "predicted": "stay", "fromGrade": grade},
                    sourceRefs=(f"credit://{code}",),
                    warnings=() if live else ("backfill",),
                )
            )
        except (ValueError, KeyError, AttributeError, TypeError, OSError) as exc:
            skipped[code] = f"{type(exc).__name__}: {exc}"
    appendExpectations(rows, baseDir=baseDir)
    return rows, skipped


def issuePriceDirection(
    codes: list[str],
    *,
    live: bool = True,
    baseDir: Path | None = None,
    mcUpsideByCode: dict[str, float] | None = None,
    issuePriceByCode: dict[str, float] | None = None,
) -> tuple[list[ExpectationSpec], dict[str, str]]:
    """Issue 12M price-direction probability expectations (direction only, never a target price).

    prob = Monte Carlo upside probability of the valuation engine (sealed as a proxy label
    "mcUpsideProxy"); the issue price is sealed inside the direction payload so scoring
    needs only the target-month close. 00 kill-list: no point price, no recommendation.

    Args:
        codes: stock codes.
        live: backfill flag.
        baseDir: ledger root override.
        mcUpsideByCode: injected {code: upside prob 0~1} (테스트용).
        issuePriceByCode: injected {code: issue close} (테스트용).
    """
    issuedAt = _nowUtc()
    existing = _existingKeys(baseDir)
    rows: list[ExpectationSpec] = []
    skipped: dict[str, str] = {}
    for code in codes:
        try:
            if mcUpsideByCode is not None:
                prob = mcUpsideByCode.get(code)
                issuePrice = (issuePriceByCode or {}).get(code)
            else:
                import dartlab
                from dartlab.analysis.forecast.simulation import monteCarloForecast

                with dartlab.Company(code) as company:  # 힙 가드: with = OomTripwire + cleanupCache
                    ts = company._buildFinanceSeries(freq="Q")
                    series = ts[0] if isinstance(ts, tuple) else ts
                mc = monteCarloForecast(series)
                prob = float(getattr(mc, "upsideProbability", 0.0)) / 100.0
                issuePrice = _monthCloseViaGather(code, None)
            if prob is None or issuePrice is None:
                skipped[code] = "MC 확률 또는 발행가 없음"
                continue
            targetPeriod = _ymAdd(issuedAt[:7], 12)
            variable = f"{code}.priceDirection"
            if (variable, 12, targetPeriod, live) in existing:
                continue
            rows.append(
                ExpectationSpec(
                    expectationId=buildExpectationId("price", variable, "M", 12, targetPeriod, issuedAt),
                    domain="price",
                    variable=variable,
                    unit="prob",
                    freq="M",
                    horizon=12,
                    targetPeriod=targetPeriod,
                    issuedAt=issuedAt,
                    issuedLive=live,
                    asOf=issuedAt[:10],
                    engine=_ENGINE_PRICE,
                    engineVersion="mc-v1",
                    kind="direction",
                    direction={
                        "prob": max(0.0, min(1.0, prob)),
                        "predicted": "up" if prob >= 0.5 else "down",
                        "issuePrice": float(issuePrice),
                    },
                    sourceRefs=(f"price://{code}",),
                    warnings=("mcUpsideProxy",) + (() if live else ("backfill",)),
                )
            )
        except (ValueError, KeyError, AttributeError, TypeError, RuntimeError, OSError) as exc:
            skipped[code] = f"{type(exc).__name__}: {exc}"
    appendExpectations(rows, baseDir=baseDir)
    return rows, skipped


def _monthCloseViaGather(code: str, targetYm: str | None) -> float | None:
    """Month-end close via the public gather price verb (targetYm=None -> latest close)."""
    from dartlab.core.di import getMacroProvider

    g = getMacroProvider().getDefaultGather()  # 싱글턴 차용: close 금지
    df = g.price(code)
    if df is None or getattr(df, "height", 0) == 0:
        return None
    cols = {c.lower(): c for c in df.columns}
    closeCol = cols.get("close") or cols.get("종가")
    dateCol = cols.get("date") or cols.get("날짜")
    if closeCol is None or dateCol is None:
        return None
    rows = [(str(d)[:7], v) for d, v in zip(df.get_column(dateCol), df.get_column(closeCol)) if v is not None]
    if targetYm is None:
        return float(rows[-1][1]) if rows else None
    monthRows = [v for ym, v in rows if ym == targetYm]
    return float(monthRows[-1]) if monthRows else None


def scoreDue(
    *,
    now: str | None = None,
    baseDir: Path | None = None,
    monthlyBySeries: dict[str, dict[str, float]] | None = None,
    annualRevenueByCode: dict[str, dict[int, float]] | None = None,
    fundamentalsByCode: dict[str, dict[str, dict[int, float]]] | None = None,
    historyByCode: dict[str, list[dict]] | None = None,
    closeByCodeMonth: dict[str, dict[str, float]] | None = None,
    quarterlyByCode: dict[str, dict[str, dict[str, float]]] | None = None,
) -> list[ExpectationScore]:
    """Score due unscored rows against the latest actuals; seal errors past the grace window.

    Args:
        now: 'YYYY-MM' clock override (테스트용). Default = current UTC month.
        baseDir: ledger root override.
        monthlyBySeries: injected latest actuals {seriesId: {ym: value}} (테스트용).
        quarterlyByCode: injected {code: {metric: {"2026Q3": value}}} 분기 실적 (테스트용).

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
        sids = {
            r["variable"].split(".", 1)[1]
            for r in due.select(["domain", "variable"]).iter_rows(named=True)
            if r["domain"] == "macro"
        }
        monthlyBySeries = {}
        if sids:
            from dartlab.macro.seriesFetch import fetchMonthlyDict, getGather

            g = getGather(None)
            monthlyBySeries = {sid: fetchMonthlyDict(g, sid) or {} for sid in sids}

    from dartlab.simulate.expectationLedger import specFromRow

    scores: list[ExpectationScore] = []
    fundCache: dict[str, dict[int, float]] = {}
    qtrCache: dict[str, dict[str, float]] = {}  # f"{code}.{metric}.{year}" -> {"2026Q3": v}
    for row in due.iter_rows(named=True):
        if row["domain"] == "macro":
            age = _ymDiff(nowYm, row["targetPeriod"])
            if age < 1:
                continue  # not due yet
            sid = row["variable"].split(".", 1)[1]
            actual = monthlyBySeries.get(sid, {}).get(row["targetPeriod"])
            if actual is None and age < 1 + _SCORE_GRACE_MONTHS:
                continue  # publication lag: stay pending, do not seal an error yet
        elif row["domain"] in ("revenue", "earnings") and row["freq"] == "Q":
            # 분기 IS 기대 (issueQuarterlyIs): 분기보고서 45일 규정 -> 분기말 +2개월 due
            dueYm = _ymAdd(_quarterEndYm(row["targetPeriod"]), _QTR_DUE_LAG_MONTHS)
            if nowYm < dueYm:
                continue
            code, metric = row["variable"].split(".", 1)
            section, key = _METRIC_KEYS.get(metric, (None, None))
            if section != "IS":
                continue  # 분기 발행은 IS 지표 한정 (_QTR_METRICS)
            year = row["targetPeriod"][:4]
            cacheKey = f"{code}.{metric}.{year}"
            if cacheKey not in qtrCache:
                if quarterlyByCode is not None:
                    qtrCache[cacheKey] = (quarterlyByCode.get(code) or {}).get(metric, {})
                else:
                    import dartlab
                    from dartlab.analysis.forecast.scenarioSim import quarterlyValues

                    try:
                        with dartlab.Company(code) as company:  # 힙 가드: with = OomTripwire + cleanupCache
                            isDf = company.panel("is")
                            for m2, (s2, k2) in _METRIC_KEYS.items():  # 한 번 로드에 IS 지표 전부
                                if s2 == "IS":
                                    qtrCache[f"{code}.{m2}.{year}"] = quarterlyValues(isDf, k2, year)
                    except (ValueError, KeyError, AttributeError, TypeError):
                        qtrCache[cacheKey] = {}
            actual = qtrCache.get(cacheKey, {}).get(row["targetPeriod"])
            if actual is None and _ymDiff(nowYm, dueYm) < _REV_GRACE_MONTHS:
                continue  # 공시·집계 지연: grace 안 pending
        elif row["domain"] in ("revenue", "earnings"):
            fy = int(row["targetPeriod"][2:])  # "FY2026" -> 2026
            dueYm = f"{fy + 1}-{_REV_DUE_MONTH:02d}"  # annual report deadline passed
            if nowYm < dueYm:
                continue  # fiscal year not reported yet
            code, metric = row["variable"].split(".", 1)
            section, key = _METRIC_KEYS.get(metric, (None, None))
            if section is None:
                continue  # actual 정의가 봉인되지 않은 metric 은 채점 불가 (P4b)
            cacheKey = f"{code}.{metric}"
            if cacheKey not in fundCache:
                injected = None
                if metric == "revenue" and annualRevenueByCode is not None:
                    injected = annualRevenueByCode.get(code, {})
                elif fundamentalsByCode is not None:
                    injected = (fundamentalsByCode.get(code) or {}).get(metric, {})
                if injected is not None:
                    fundCache[cacheKey] = injected
                else:
                    import dartlab

                    try:
                        with dartlab.Company(code) as company:  # 힙 가드: with = OomTripwire + cleanupCache
                            for m2, (s2, k2) in _METRIC_KEYS.items():  # 한 번 로드에 3 metric 전부
                                fundCache[f"{code}.{m2}"] = _annualMetricMap(company, s2, k2)
                    except (ValueError, KeyError, AttributeError, TypeError):
                        fundCache[cacheKey] = {}
            actual = fundCache.get(cacheKey, {}).get(fy)
            if actual is None and _ymDiff(nowYm, dueYm) < _REV_GRACE_MONTHS:
                continue  # filing/consolidation lag: stay pending inside the grace window
        elif row["domain"] == "credit":
            import json as _json

            dueYm = _ymAdd(_quarterEndYm(row["targetPeriod"]), 1)
            if nowYm < dueYm:
                continue
            code = row["variable"].split(".", 1)[0]
            fromGrade = (_json.loads(row["direction"]) or {}).get("fromGrade")
            if historyByCode is not None:
                hist = historyByCode.get(code) or []
            else:
                from dartlab.credit.monitoring.history import loadHistory

                hist = loadHistory(code)
            after = [
                e.get("grade") or (e.get("result") or {}).get("grade")
                for e in hist
                if str(e.get("timestamp", e.get("date", "")))[:7] >= _quarterEndYm(row["targetPeriod"])
            ]
            actual = None
            if after and after[-1]:
                actual = "stay" if after[-1] == fromGrade else "changed"
            if actual is None and _ymDiff(nowYm, dueYm) < _CREDIT_GRACE_MONTHS:
                continue  # 다음 분기 등급 미산출: grace 안 pending
        elif row["domain"] == "price":
            import json as _json

            age = _ymDiff(nowYm, row["targetPeriod"])
            if age < 1:
                continue
            code = row["variable"].split(".", 1)[0]
            d = _json.loads(row["direction"]) or {}
            issuePrice = d.get("issuePrice")
            if closeByCodeMonth is not None:
                close = (closeByCodeMonth.get(code) or {}).get(row["targetPeriod"])
            else:
                close = _monthCloseViaGather(code, row["targetPeriod"])
            actual = None
            if close is not None and issuePrice:
                actual = "up" if float(close) >= float(issuePrice) else "down"
            if actual is None and age < 1 + _PRICE_GRACE_MONTHS:
                continue  # 시세 조회 실패: grace 안 pending
        else:
            continue  # 미지원 domain 은 채점 보류 (원장에 그대로 남는다)
        scores.append(scoreExpectation(specFromRow(row), actual, scoredAt=scoredAt, actualAsOf=scoredAt[:10]))
    appendScores(scores, baseDir=baseDir)
    return scores


def buildScorecard(*, baseDir: Path | None = None) -> dict:
    """Aggregate the ledger into the scorecard payload consumed by the terminal.

    Returns:
        dict with generatedAt, totals, and per-group calibration where each group key is
        ``{domain}.{variable}.{freq}{horizon}.{live|backfill}``. Groups below the sample gate carry
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
        # freq 포함 필수: 분기(h=Q1~4)와 연간(h=1~3)이 같은 variable 을 쓴다
        key = f"{m['domain']}.{m['variable']}.{m['freq']}{m['horizon']}.{'live' if m['issuedLive'] else 'backfill'}"
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
