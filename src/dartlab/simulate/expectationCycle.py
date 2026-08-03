"""Expectation cycle : the sole collector/scorer sealing engine forecasts into the ledger.

Roles:
- ``issueMacro``  : call the L2 macro fan verb, seal quantile expectations plus point-in-time
  naive baselines (random-walk / persistence / seasonal-naive) into the ledger. Idempotent per
  (variable, horizon, targetPeriod, issuedLive): re-runs within the same month skip existing rows.
- ``scoreDue``    : join due unscored rows with the latest actuals and append score rows.
  Not-yet-published actuals are skipped inside a grace window; past the grace window a missing
  actual is sealed as an error row (no silent survivorship).
- ``buildScorecard`` : aggregate scores per (domain, variable, freq, horizon, issuedLive) with the
  sample gates (verified=False forces the "미검증" label).

This module is the only writer of the ledger. L2 engines stay ledger-blind; the downward-only
import contract makes that structural (L2 cannot import L2.5).
"""

from __future__ import annotations

import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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

_LOG = logging.getLogger(__name__)

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


@dataclass
class _RevenueIssueContext:
    """한 revenue 발행 실행의 공통 상태."""

    live: bool
    horizons: tuple[int, ...]
    issuedAt: str
    asOf: str | None
    existing: set[tuple]
    rows: list[ExpectationSpec]


def _loadRevenueForecast(
    code: str,
    resultByCode: dict | None,
    annualByCode: dict[str, dict[int, float]] | None,
) -> tuple[Any, dict[int, float]]:
    """주입 결과 또는 Company 분석에서 매출 예측과 연간 이력을 함께 가져온다."""
    if resultByCode is not None:
        return resultByCode.get(code), (annualByCode or {}).get(code) or {}
    import dartlab
    from dartlab.analysis.financial._forecastCalcsInputs import _runForecastRevenue

    with getattr(dartlab, "Company")(code) as company:
        annual = _annualRevenueMap(company)
        result = _runForecastRevenue(company)
    return result, annual


def _appendRevenueForecastRows(
    code: str,
    result: Any,
    annual: dict[int, float],
    scenarios: dict[str, list[float]],
    context: _RevenueIssueContext,
) -> bool:
    """한 회사의 연간 시나리오를 중복 없는 quantile 기대 행으로 봉인한다."""
    basePath = scenarios["base"]
    bullPath = scenarios["bull"]
    bearPath = scenarios["bear"]
    baseYear = max(annual)
    history = [annual[year] for year in sorted(annual)][-11:]
    differences = [current - previous for previous, current in zip(history, history[1:])]
    sigma = statistics.pstdev(differences) if len(differences) >= 3 else 0.0
    lastRevenue = history[-1]
    issuedAny = False
    for horizon in context.horizons:
        if horizon > len(basePath):
            continue
        targetPeriod = f"FY{baseYear + horizon}"
        variable = f"{code}.revenue"
        if (variable, horizon, targetPeriod, context.live) in context.existing:
            continue
        p25, p50, p75 = sorted([bearPath[horizon - 1], basePath[horizon - 1], bullPath[horizon - 1]])
        quantiles = {
            5: p50 - _TAIL_FACTOR * max(p50 - p25, 0.0),
            25: p25,
            50: p50,
            75: p75,
            95: p50 + _TAIL_FACTOR * max(p75 - p50, 0.0),
        }
        standardError = sigma * (horizon**0.5)
        rowWarnings = ("scenarioQuantileApprox",) + (() if context.live else ("backfill",))
        context.rows.append(
            ExpectationSpec(
                expectationId=buildExpectationId("revenue", variable, "Y", horizon, targetPeriod, context.issuedAt),
                domain="revenue",
                variable=variable,
                unit="KRW",
                freq="Y",
                horizon=horizon,
                targetPeriod=targetPeriod,
                issuedAt=context.issuedAt,
                issuedLive=context.live,
                asOf=context.asOf or context.issuedAt[:10],
                engine=_ENGINE_REVENUE,
                engineVersion=str(getattr(result, "method", "") or "ensemble"),
                kind="quantiles",
                quantiles=quantiles,
                baselines={
                    "randomWalk": (
                        {key: lastRevenue + zScore * standardError for key, zScore in _Z.items()}
                        if standardError > 0
                        else None
                    ),
                    "persistence": lastRevenue,
                    "seasonalNaive": None,
                },
                sourceRefs=(f"dart://{code}", f"baseFY={baseYear}"),
                warnings=rowWarnings,
            )
        )
        issuedAny = True
    return issuedAny


def issueRevenue(
    codes: list[str],
    *,
    live: bool = True,
    horizons: tuple[int, ...] = (1, 2, 3),
    baseDir: Path | None = None,
    resultByCode: dict | None = None,
    annualByCode: dict[str, dict[int, float]] | None = None,
    asOf: str | None = None,
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
    if not live and (asOf is None or resultByCode is None or annualByCode is None):
        raise ValueError("revenue backfill은 asOf와 PIT-sealed resultByCode/annualByCode가 필요합니다")
    issuedAt = _nowUtc()
    existing = _existingKeys(baseDir)
    rows: list[ExpectationSpec] = []
    context = _RevenueIssueContext(live, horizons, issuedAt, asOf, existing, rows)
    skipped: dict[str, str] = {}
    for code in codes:
        try:
            result, annual = _loadRevenueForecast(code, resultByCode, annualByCode)
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
            issuedAny = _appendRevenueForecastRows(code, result, annual, scen, context)
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
    asOf: str | None = None,
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
    if not live and (asOf is None or seriesByCode is None or annualByCode is None):
        raise ValueError("earnings backfill은 asOf와 PIT-sealed seriesByCode/annualByCode가 필요합니다")
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

                with getattr(dartlab, "Company")(code) as company:  # 힙 가드: with = OomTripwire + cleanupCache
                    ts = company._buildFinanceSeries(freq="Q")
                    series = ts[0] if isinstance(ts, tuple) else ts
                    annual = _annualMetricMap(company, "IS", "sales")
            if not isinstance(series, dict) or not series:
                skipped[code] = "분기 재무 시계열 없음"
                continue
            if not annual:
                skipped[code] = "연간 매출 이력 없음"
                continue
            baseFY = max(annual)
            baseRev = annual[baseFY]
            maxH = max(h for h in horizons if h in revByH)
            if any(revByH[h]["targetPeriod"] != f"FY{baseFY + h}" for h in revByH):
                skipped[code] = "매출 기대 targetPeriod와 PIT baseFY 불일치"
                continue
            if not live and any(str(row.get("asOf", "")) != asOf for row in revByH.values()):
                skipped[code] = "매출 기대 asOf와 earnings backfill asOf 불일치"
                continue
            import json as _json

            # 봉인된 절대 매출레벨 경로 (D2 앵커): proforma 가 이 레벨을 매출로 직접 사용해
            # E-3표 매출 == 봉인 매출기대 분위. growth 는 테스트 주입 fn 계약(성장률)용으로만 역산.
            levelByQ: dict[int, list[float]] = {}
            for q in (25, 50, 75):
                levels = []
                for h in range(1, maxH + 1):
                    if h not in revByH:
                        break
                    levels.append(float(_json.loads(revByH[h]["quantiles"])[str(q)]))
                levelByQ[q] = levels
            pfByQ = {}
            for q, levels in levelByQ.items():
                if proformaFn is not None:
                    prev, growth = baseRev, []
                    for lv in levels:
                        growth.append((lv / prev - 1.0) * 100.0 if prev > 0 else 0.0)
                        prev = lv
                    pfByQ[q] = proformaFn(series, growth, f"expGrid_p{q}")
                else:
                    from dartlab.analysis.financial.proforma import buildProforma

                    pfByQ[q] = buildProforma(
                        series,
                        revenueGrowthPath=[0.0] * len(levels),
                        revenueLevelPath=levels,
                        scenarioName=f"expGrid_p{q}",
                    )
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
                    bsBalancedRaw = getattr(pfYear, "bs_balanced", None)
                    for stmt, account in _PF_ACCOUNTS:
                        accountValue = getattr(pfYear, account, None)
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
                                "value": float(accountValue) if accountValue is not None else None,
                                "bsBalanced": bool(bsBalancedRaw) if bsBalancedRaw is not None else None,
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
                            asOf=str(revByH[h].get("asOf") or asOf or issuedAt[:10]),
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


def _seriesQuarterValues(series, periods: list[str], key: str, year: str) -> dict[str, float]:
    """_buildFinanceSeries(freq="Q") 시계열에서 한 해의 분기 값 {"2026Q3": v}.

    발행 게이트("실제값이 이미 데이터에 있나")와 분기 채점의 공용 실제값 소스.
    panel("is") 는 최근 분기창만 있고 Q4 열이 아예 없어(분기보고서 구조) 둘 다 부적합.
    """
    vals = (series.get("IS") or {}).get(key) or []
    out: dict[str, float] = {}
    for p, v in zip(periods, vals):
        if v is None or not p.startswith(f"{year}-Q"):
            continue
        out[f"{year}Q{p.split('-Q')[1]}"] = float(v)
    return out


def _seriesSeasonality(series, periods: list[str], key: str, years: list[str]) -> list[float]:
    """_buildFinanceSeries(freq="Q") 시계열에서 Q1~Q4 비중 (panel("is") 는 Q4 열이 없어 부적합)."""
    byYear: dict[str, list[float]] = {}
    for y in years:
        vals = _seriesQuarterValues(series, periods, key, y)
        ordered = [vals[f"{y}Q{q}"] for q in range(1, 5) if f"{y}Q{q}" in vals]
        if len(ordered) == 4:
            byYear[y] = ordered
    from dartlab.analysis.forecast.scenarioSim import seasonalSharesFromYearQuarters

    return seasonalSharesFromYearQuarters(byYear)


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


@dataclass(frozen=True)
class _QuarterlySourceRequest:
    """한 회사의 분기 계절성과 공시완료 분기를 구하는 입력."""

    code: str
    baseFiscalYear: int
    horizons: tuple[int, ...]
    revenueByHorizon: dict[int, dict]
    seasonalityByCode: dict[str, tuple[list[float], list[float]]] | None
    publishedByCode: dict[str, set[str]] | None


@dataclass(frozen=True)
class _QuarterlyCodeInputs:
    """한 회사의 분기 분해에 필요한 부모 기대와 계절성."""

    code: str
    revenueByHorizon: dict[int, dict]
    operatingByHorizon: dict[int, dict]
    revenueWeights: list[float]
    operatingWeights: list[float]
    published: set[str]


@dataclass
class _QuarterlyIssueContext:
    """분기 기대와 proforma 행을 함께 봉인하는 공통 실행 상태."""

    live: bool
    issuedAt: str
    nowYm: str
    existing: set[tuple]
    proformaExisting: set[tuple[str, str, int]]
    rows: list[ExpectationSpec]
    proformaRows: list[dict]


def _quarterlySeasonality(request: _QuarterlySourceRequest) -> tuple[list[float], list[float], set[str]]:
    """주입값 또는 Company 재무 시계열에서 계절성과 공시완료 분기를 구한다."""
    if request.seasonalityByCode is not None:
        revenueWeights, operatingWeights = request.seasonalityByCode[request.code]
        return revenueWeights, operatingWeights, (request.publishedByCode or {}).get(request.code, set())
    import dartlab

    seasonYears = [
        str(request.baseFiscalYear - offset) for offset in range(3) if request.baseFiscalYear - offset >= 2019
    ]
    targetFiscalYears = {
        str(int(request.revenueByHorizon[horizon]["targetPeriod"][2:])) for horizon in request.horizons
    }
    with getattr(dartlab, "Company")(request.code) as company:
        timeseries = company._buildFinanceSeries(freq="Q")
        series = timeseries[0] if isinstance(timeseries, tuple) else timeseries
        periods = timeseries[1] if isinstance(timeseries, tuple) else []
    revenueWeights = _seriesSeasonality(series, periods, "sales", seasonYears)
    operatingWeights = _seriesSeasonality(series, periods, "operating_profit", seasonYears)
    published = {
        period for year in targetFiscalYears for period in _seriesQuarterValues(series, periods, "sales", year)
    }
    return revenueWeights, operatingWeights, published


def _appendQuarterlyHorizon(
    horizon: int,
    companyInputs: _QuarterlyCodeInputs,
    context: _QuarterlyIssueContext,
) -> None:
    """한 연간 부모의 Q1~Q4 기대와 E-3 proforma 행을 함께 추가한다."""
    import json as _json

    revenueParent = companyInputs.revenueByHorizon[horizon]
    fiscalYear = int(revenueParent["targetPeriod"][2:])
    parentByMetric = {
        "revenue": (revenueParent, companyInputs.revenueWeights),
        "operatingProfit": (companyInputs.operatingByHorizon.get(horizon), companyInputs.operatingWeights),
    }
    revenueParentId = revenueParent["expectationId"]
    for quarter in range(1, 5):
        targetPeriod = f"{fiscalYear}Q{quarter}"
        if context.live and targetPeriod in companyInputs.published:
            continue
        nowcast = context.live and _quarterEndYm(targetPeriod) < context.nowYm
        for metric, domain, proformaAccount in _QTR_METRICS:
            parent, weights = parentByMetric[metric]
            if parent is None:
                continue
            variable = f"{companyInputs.code}.{metric}"
            weight = weights[quarter - 1]
            annualQuantiles = {int(key): float(value) for key, value in _json.loads(parent["quantiles"]).items()}
            flat = all(abs(value - 0.25) < 1e-9 for value in weights)
            if (variable, quarter, targetPeriod, context.live) not in context.existing:
                context.rows.append(
                    ExpectationSpec(
                        expectationId=buildExpectationId(
                            domain,
                            variable,
                            "Q",
                            quarter,
                            targetPeriod,
                            context.issuedAt,
                        ),
                        domain=domain,
                        variable=variable,
                        unit="KRW",
                        freq="Q",
                        horizon=quarter,
                        targetPeriod=targetPeriod,
                        issuedAt=context.issuedAt,
                        issuedLive=context.live,
                        asOf=context.issuedAt[:10],
                        engine=_ENGINE_SEASONAL,
                        engineVersion="seasonalShares3y",
                        kind="quantiles",
                        quantiles={key: value * weight for key, value in annualQuantiles.items()},
                        baselines={"persistence": None, "seasonalNaive": None, "randomWalk": None},
                        sourceRefs=(parent["expectationId"], f"share={weight:.4f}"),
                        warnings=("seasonalSplitOfAnnual", "scenarioQuantileApprox")
                        + (("flatSeasonalityFallback",) if flat else ())
                        + (("quarterEndedAtIssue",) if nowcast else ())
                        + (() if context.live else ("backfill",)),
                    )
                )
            for quantile in (25, 50, 75):
                if (revenueParentId, targetPeriod, quantile) in context.proformaExisting:
                    continue
                context.proformaRows.append(
                    {
                        "parentId": revenueParentId,
                        "code": companyInputs.code,
                        "issuedAt": context.issuedAt,
                        "issuedLive": context.live,
                        "targetPeriod": targetPeriod,
                        "quantile": quantile,
                        "statement": "IS",
                        "account": proformaAccount,
                        "value": annualQuantiles[quantile] * weight,
                        "bsBalanced": True,
                    }
                )


def issueQuarterlyIs(
    codes: list[str],
    *,
    live: bool = True,
    years: tuple[int, ...] = (1, 2),
    baseDir: Path | None = None,
    seasonalityByCode: dict[str, tuple[list[float], list[float]]] | None = None,
    publishedByCode: dict[str, set[str]] | None = None,
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
    Look-ahead 차단은 달력이 아니라 데이터 기준: 실제값이 이미 SSOT 시계열에 존재하는 분기만
    발행 제외한다 (분기말이 지났어도 분기보고서 미공시면 정당한 예측 대상 = nowcast,
    "quarterEndedAtIssue" 경고 봉인으로 성적표에서 일반 예측과 분리 집계). horizon
    is the quarter's position in the fiscal year (1~4), so re-sweeps stay idempotent per
    (variable, horizon, targetPeriod, issuedLive) and the scorecard pools by quarter position.
    Baselines are sealed as None like issueEarnings (skill 미산출 부채, P4b 트랙).

    Args:
        codes: stock codes with sealed annual revenue expectations.
        live: backfill flag (parent rows must match).
        years: annual parent horizons to split (기본 Y1·Y2 -> 당해 잔여분기 + 차년 4분기).
        baseDir: ledger root override.
        seasonalityByCode: injected {code: (revW, oiW)} 4-weights (테스트용, skips Company).
        publishedByCode: injected {code: {"2026Q1", ...}} 공시완료 분기 (테스트용).
        now: 'YYYY-MM' clock override (테스트용).

    Returns:
        (sealed rows, skipped census).
    """
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
    context = _QuarterlyIssueContext(live, issuedAt, nowYm, existing, pfExisting, rows, pfRows)
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
            request = _QuarterlySourceRequest(
                code,
                baseFy,
                tuple(hs),
                revByH,
                seasonalityByCode,
                publishedByCode,
            )
            revW, oiW, published = _quarterlySeasonality(request)
            companyInputs = _QuarterlyCodeInputs(code, revByH, opByH, revW, oiW, published)
            for hy in hs:
                _appendQuarterlyHorizon(hy, companyInputs, context)
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

                with getattr(dartlab, "Company")(code) as company:  # 힙 가드: with = OomTripwire + cleanupCache
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


def _annualActual(
    row: dict, nowYm: str, fundCache: dict, annualRevenueByCode, fundamentalsByCode
) -> tuple[object, bool]:
    """연간 실적 실제값을 찾는다. 사업보고서 마감이 지나야 기한이 온다.

    실제값 정의가 봉인되지 않은 지표는 채점하지 않는다. 정의 없이 채점하면 무엇과 견줬는지
    설명할 수 없는 성적이 남는다.

    Returns:
        ``(실제값, 보류여부)``.
    """
    fy = int(row["targetPeriod"][2:])  # "FY2026" -> 2026
    dueYm = f"{fy + 1}-{_REV_DUE_MONTH:02d}"
    if nowYm < dueYm:
        return None, True  # 해당 회계연도 보고 전
    code, metric = row["variable"].split(".", 1)
    section, _key = _METRIC_KEYS.get(metric, (None, None))
    if section is None:
        return None, True  # actual 정의가 봉인되지 않은 metric 은 채점 불가 (P4b)
    cacheKey = f"{code}.{metric}"
    if cacheKey not in fundCache:
        _fillAnnualCache(fundCache, code, metric, cacheKey, annualRevenueByCode, fundamentalsByCode)
    actual = fundCache.get(cacheKey, {}).get(fy)
    if actual is None and _ymDiff(nowYm, dueYm) < _REV_GRACE_MONTHS:
        return None, True  # 공시와 연결 집계 지연. 유예 안이라 보류
    return actual, False


def _creditActual(row: dict, nowYm: str, historyByCode) -> tuple[object, bool]:
    """신용등급 유지 여부의 실제값을 찾는다. 분기말 다음 달이 기한이다.

    분기말 이후에 기록된 등급만 본다. 그 전 기록은 발행 시점에 이미 알던 것이라 채점 근거가
    되지 못한다.

    Returns:
        ``(실제값, 보류여부)``.
    """
    import json as _json

    dueYm = _ymAdd(_quarterEndYm(row["targetPeriod"]), 1)
    if nowYm < dueYm:
        return None, True
    code = row["variable"].split(".", 1)[0]
    fromGrade = (_json.loads(row["direction"]) or {}).get("fromGrade")
    if historyByCode is not None:
        hist = historyByCode.get(code) or []
    else:
        from dartlab.credit.monitoring.history import loadHistory

        hist = loadHistory(code)
    after = [
        entry.get("grade") or (entry.get("result") or {}).get("grade")
        for entry in hist
        if str(entry.get("timestamp", entry.get("date", "")))[:7] >= _quarterEndYm(row["targetPeriod"])
    ]
    actual = None
    if after and after[-1]:
        actual = "stay" if after[-1] == fromGrade else "changed"
    if actual is None and _ymDiff(nowYm, dueYm) < _CREDIT_GRACE_MONTHS:
        return None, True  # 다음 분기 등급 미산출. 유예 안이라 보류
    return actual, False


def _quarterlyActual(row: dict, nowYm: str, qtrCache: dict, quarterlyByCode) -> tuple[object, bool]:
    """분기 손익 실제값을 찾는다. 분기보고서 45 일 규정이라 분기말 두 달 뒤가 기한이다.

    분기 발행은 손익계산서 지표만 다룬다. 그 밖의 지표는 실제값 정의가 봉인돼 있지 않아
    채점할 수 없고, 억지로 채점하면 정의가 없는 것을 틀렸다고 기록하게 된다.

    Returns:
        ``(실제값, 보류여부)``.
    """
    dueYm = _ymAdd(_quarterEndYm(row["targetPeriod"]), _QTR_DUE_LAG_MONTHS)
    if nowYm < dueYm:
        return None, True
    code, metric = row["variable"].split(".", 1)
    section, _key = _METRIC_KEYS.get(metric, (None, None))
    if section != "IS":
        return None, True  # 분기 발행은 IS 지표 한정 (_QTR_METRICS)
    year = row["targetPeriod"][:4]
    cacheKey = f"{code}.{metric}.{year}"
    if cacheKey not in qtrCache:
        _fillQuarterCache(qtrCache, code, metric, year, cacheKey, quarterlyByCode)
    actual = qtrCache.get(cacheKey, {}).get(row["targetPeriod"])
    if actual is None and _ymDiff(nowYm, dueYm) < _REV_GRACE_MONTHS:
        return None, True  # 공시와 집계 지연. 유예 안이라 보류
    return actual, False


def _macroActual(row: dict, nowYm: str, monthlyBySeries: dict) -> tuple[object, bool]:
    """거시 지표의 실제값을 찾는다.

    Returns:
        ``(실제값, 보류여부)``. 보류면 채점하지 않고 원장에 그대로 남긴다. 발표 지연과
        진짜 결측을 구분하려면 유예 기간이 지나야 하고, 그 전에 오류로 봉인하면 되돌릴 수 없다.
    """
    age = _ymDiff(nowYm, row["targetPeriod"])
    if age < 1:
        return None, True  # 아직 기한 전
    sid = row["variable"].split(".", 1)[1]
    actual = monthlyBySeries.get(sid, {}).get(row["targetPeriod"])
    if actual is None and age < 1 + _SCORE_GRACE_MONTHS:
        return None, True  # 발표 지연. 유예 안이라 보류
    return actual, False


def _priceActual(row: dict, nowYm: str, closeByCodeMonth) -> tuple[object, bool]:
    """주가 방향의 실제값을 찾는다. 발행가 대비 종가로 상승과 하락을 가른다.

    Returns:
        ``(실제값, 보류여부)``. 시세를 못 구했고 유예 안이면 보류한다.
    """
    import json as _json

    age = _ymDiff(nowYm, row["targetPeriod"])
    if age < 1:
        return None, True
    code = row["variable"].split(".", 1)[0]
    issuePrice = (_json.loads(row["direction"]) or {}).get("issuePrice")
    if closeByCodeMonth is not None:
        close = (closeByCodeMonth.get(code) or {}).get(row["targetPeriod"])
    else:
        close = _monthCloseViaGather(code, row["targetPeriod"])
    actual = None
    if close is not None and issuePrice:
        actual = "up" if float(close) >= float(issuePrice) else "down"
    if actual is None and age < 1 + _PRICE_GRACE_MONTHS:
        return None, True  # 시세 조회 실패. 유예 안이라 보류
    return actual, False


def _fillQuarterCache(qtrCache: dict, code: str, metric: str, year: str, cacheKey: str, quarterlyByCode) -> None:
    """분기 실제값을 캐시에 채운다. 주입값이 있으면 그것을 쓰고 없으면 회사에서 읽는다.

    한 번 회사를 열 때 IS 지표를 전부 담는다. 같은 회사를 지표마다 다시 여는 것이 이 순환에서
    가장 비싼 일이기 때문이다.

    실제값은 `_buildFinanceSeries(freq="Q")` 로 읽는다. `panel("is")` 는 Q4 열이 없어 4 분기가
    통째로 결측으로 잡힌다.
    """
    if quarterlyByCode is not None:
        qtrCache[cacheKey] = (quarterlyByCode.get(code) or {}).get(metric, {})
        return
    import dartlab

    try:
        with getattr(dartlab, "Company")(code) as company:  # 힙 가드: with = OomTripwire + cleanupCache
            ts = company._buildFinanceSeries(freq="Q")
            qSeries = ts[0] if isinstance(ts, tuple) else ts
            qPeriods = ts[1] if isinstance(ts, tuple) else []
        for metricName, (section, key) in _METRIC_KEYS.items():
            if section == "IS":
                qtrCache[f"{code}.{metricName}.{year}"] = _seriesQuarterValues(qSeries, qPeriods, key, year)
    except (ValueError, KeyError, AttributeError, TypeError) as exc:
        # 원인을 남긴다. 조용히 빈 값을 꽂으면 그 예측은 실제값 조회 실패로 채점되고,
        # 채점된 id 는 미채점 목록에서 빠져 다시 시도되지 않는다. 일시적 오류 하나가
        # 영구 오답으로 굳는다.
        _LOG.warning("분기 실제값 조회 실패 (%s, %s: %s)", cacheKey, type(exc).__name__, exc)
        qtrCache[cacheKey] = {}


def _fillAnnualCache(
    fundCache: dict, code: str, metric: str, cacheKey: str, annualRevenueByCode, fundamentalsByCode
) -> None:
    """연간 실제값을 캐시에 채운다. 주입 경로가 둘이라 지표에 따라 갈린다."""
    injected = None
    if metric == "revenue" and annualRevenueByCode is not None:
        injected = annualRevenueByCode.get(code, {})
    elif fundamentalsByCode is not None:
        injected = (fundamentalsByCode.get(code) or {}).get(metric, {})
    if injected is not None:
        fundCache[cacheKey] = injected
        return
    import dartlab

    try:
        with getattr(dartlab, "Company")(code) as company:  # 힙 가드: with = OomTripwire + cleanupCache
            for metricName, (section, key) in _METRIC_KEYS.items():  # 한 번 로드에 3 metric 전부
                fundCache[f"{code}.{metricName}"] = _annualMetricMap(company, section, key)
    except (ValueError, KeyError, AttributeError, TypeError) as exc:
        # 위 분기 경로와 같은 이유로 원인을 남긴다.
        _LOG.warning("연간 실제값 조회 실패 (%s, %s: %s)", cacheKey, type(exc).__name__, exc)
        fundCache[cacheKey] = {}


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
            actual, pending = _macroActual(row, nowYm, monthlyBySeries)
            if pending:
                continue
        elif row["domain"] in ("revenue", "earnings") and row["freq"] == "Q":
            actual, pending = _quarterlyActual(row, nowYm, qtrCache, quarterlyByCode)
            if pending:
                continue
        elif row["domain"] in ("revenue", "earnings"):
            actual, pending = _annualActual(row, nowYm, fundCache, annualRevenueByCode, fundamentalsByCode)
            if pending:
                continue
        elif row["domain"] == "credit":
            actual, pending = _creditActual(row, nowYm, historyByCode)
            if pending:
                continue
        elif row["domain"] == "price":
            actual, pending = _priceActual(row, nowYm, closeByCodeMonth)
            if pending:
                continue
        else:
            continue  # 미지원 domain 은 채점 보류 (원장에 그대로 남는다)
        if isinstance(actual, bool) or (actual is not None and not isinstance(actual, (float, int, str))):
            raise TypeError(f"채점 actual 타입이 유효하지 않습니다: {type(actual).__name__}")
        normalizedActual = float(actual) if isinstance(actual, int) else actual
        scores.append(scoreExpectation(specFromRow(row), normalizedActual, scoredAt=scoredAt, actualAsOf=scoredAt[:10]))
    appendScores(scores, baseDir=baseDir)
    return scores


def buildScorecard(*, baseDir: Path | None = None) -> dict:
    """Aggregate the ledger into the scorecard payload consumed by the terminal.

    Returns:
        dict with generatedAt, totals, and per-group calibration where each group key is
        ``{domain}.{variable}.{freq}{horizon}.{live|backfill}`` (+ ``.nowcast`` suffix for
        rows sealed after quarter end but before publication). Groups below the sample gate carry
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
        for r in exps.select(
            ["expectationId", "domain", "variable", "horizon", "freq", "issuedLive", "warnings"]
        ).iter_rows(named=True)
    }
    grouped: dict[str, list] = {}
    seen: set[str] = set()
    for row in scores.iter_rows(named=True):
        m = meta.get(row["expectationId"])
        if m is None:
            continue
        seen.add(row["expectationId"])
        # freq 포함 필수: 분기(h=Q1~4)와 연간(h=1~3)이 같은 variable 을 쓴다.
        # nowcast(분기말 경과 후 발행)는 일반 예측과 혼합 집계 금지 -> 별도 그룹.
        key = f"{m['domain']}.{m['variable']}.{m['freq']}{m['horizon']}.{'live' if m['issuedLive'] else 'backfill'}"
        if "quarterEndedAtIssue" in (m["warnings"] or ""):
            key += ".nowcast"
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
