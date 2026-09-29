"""Deterministic driver node definitions for the L3 scenario engine.

This module holds the deterministic (lens=None) driver nodes and the function that builds a
`DriverSheet` for one scenario. Each node is one of two kinds:

- a thin call into an L2 leaf (`proforma` -> `analysis.financial.proforma.buildProforma`), or
- the single owned macro->fundamentals edge (`rev.path` -> `simulate.transfer`), plus the preset
  pass-through (`macro.path`) and a minimal FCFF discount off the proforma path (`dcf`).

Node graph (deterministic minimum set, §5). Every macro variable and every transfer channel is its
own node, so the audit shows which input moves which number and a rate shock reaches the value:

    macro.path (preset GDP)    macro.rate (preset policy rate)    macro.fx (preset KRW/USD)
      rev.path    <- macro.path, macro.fx     revenue channel
      margin.path <- macro.path, macro.rate   operating-margin channel
      wacc.path   <- macro.rate               discount-rate channel
        proforma  <- rev.path, margin.path    buildProforma L2 leaf: growth path + margin shock
          dcf     <- proforma, wacc.path      FCFF discount at the per-year scenario WACC

Every registry fn matches the `evaluateSheet` contract:
``fn(node, sheet, depValues) -> (value, vector, provenance, refs, frozenInputs, asOf, latestAsOf)``.

Snapshot discipline (§13b-5): the company's base metrics (revenue / margin / shares / sector
elasticity / WACC / net debt) are read ONCE into the sheet snapshot by `buildSnapshot` before
evaluation; no node reloads data mid-eval, so a re-run is byte-identical.

honest-gap (§3): a missing leaf or absent base metric yields a node value of None (never 0); the
caller (`run.py`) reads that as a `partial` quality status.

Born-clean (§10): this module does NOT import the legacy simulation flow
(`analysis/forecast/simulation.py`, `_applyMacroShock`, `_simScenario`). It imports forward only:
L0 (`core.utils.extract`), L1.5 (`synth.scenario`), and L2 leafs
(`analysis.financial.proforma.buildProforma`, the `analysis.financial._valuationInputs` sector /
series / shares accessors). The FCFF discount in the `dcf` node ports the legacy terminal-value
formula and discounts each year at that year's scenario WACC, so the value reflects THIS scenario's
proforma FCF and rate path.

Layer: L3. Forward imports: L0 (core), L1.5 (synth), L2 (analysis.financial/dataHub).
"""

from __future__ import annotations

import json
from typing import Any

from dartlab.analysis.financial._valuationInputs import _resolveSectorKey
from dartlab.analysis.financial.dataAssets import _periodKey
from dartlab.analysis.financial.proforma import buildProforma
from dartlab.core.utils.extract import getLatest, getTTM
from dartlab.simulate.sheet import DriverNode, DriverSheet, NodeValue
from dartlab.synth.scenario import (
    DEFAULT_ELASTICITY,
    SectorElasticity,
    getElasticity,
    getPresetScenarios,
)

# Registry fn keys (one per driverId). The DriverNode.fn dispatch keys the sheet registry.
_FN_MACRO = "simulate.macroPath"
_FN_MACRO_RATE = "simulate.macroRatePath"
_FN_MACRO_FX = "simulate.macroFxPath"
_FN_REV = "simulate.revPath"
_FN_MARGIN = "simulate.marginPath"
_FN_WACC = "simulate.waccPath"
_FN_PROFORMA = "simulate.proforma"
_FN_DCF = "simulate.dcf"

# Driver ids (§5 node table).
DRIVER_MACRO = "macro.path"
DRIVER_RATE = "macro.rate"
DRIVER_FX = "macro.fx"
DRIVER_REV = "rev.path"
DRIVER_MARGIN = "margin.path"
DRIVER_WACC = "wacc.path"
DRIVER_PROFORMA = "proforma"
DRIVER_DCF = "dcf"

# The public verb is KR-only (entry.py blocks other markets). The presets and elasticities are KR
# baselines; a US run needs US presets and elasticities first, so this is the one place it is fixed.
_PRESET_MARKET = "KR"

_DEFAULT_BASE_WACC = 10.0  # legacy baseWacc default when sectorParams.discountRate is absent.
_DEFAULT_MARGIN = 10.0  # legacy fallback when operating margin is unavailable.
_TAX_RATE = 0.22  # legacy KR corporate effective-rate default for the FCFF proxy.
_TERMINAL_GROWTH_CAP = 3.0  # legacy terminal growth cap.


def _baseMetrics(series: dict) -> dict[str, float | None]:
    """Extract the base revenue / margin / net debt the simulate snapshot needs (born-clean).

    Capabilities:
        Reads the minimal base metrics the driver DAG consumes (TTM revenue, operating margin,
        and net debt) directly from a finance series using L0 extract helpers. Replicates the
        same accounts the legacy `_extractBaseMetrics` reads (sales/operating_profit and the
        debt/cash balance-sheet lines) without importing the legacy simulation flow.

    Args:
        series: a finance series dict (``{sjDiv: {account: [..]}}``) as built by
            ``analysis.simulationInputs`` Data Workbench asset.

    Returns:
        dict[str, float | None]: ``{"revenue", "margin", "netDebt"}``. Values are None when
        the underlying accounts are absent (honest-gap, never 0).

    Raises:
        None. Every lookup is None-tolerant.

    Example:
        >>> _baseMetrics({"IS": {"sales": [None]}})["revenue"] is None
        True

    Requires:
        L0 ``getTTM`` / ``getLatest`` (no dartlab analysis import).
    """
    rev = getTTM(series, "IS", "sales") or getTTM(series, "IS", "revenue")
    oi = getTTM(series, "IS", "operating_profit") or getTTM(series, "IS", "operating_income")
    margin = (oi / rev * 100) if rev and oi and rev > 0 else None

    cash = getLatest(series, "BS", "cash_and_cash_equivalents")
    stb = getLatest(series, "BS", "shortterm_borrowings")
    ltb = getLatest(series, "BS", "longterm_borrowings")
    bonds = getLatest(series, "BS", "debentures")
    if cash is None or stb is None or ltb is None or bonds is None:
        netDebt = None
    else:
        netDebt = stb + ltb + bonds - cash

    return {"revenue": rev, "margin": margin, "netDebt": netDebt}


def _periodLabel(key: tuple[int, int]) -> str:
    """정규 기간 키를 공개 표기 ``YYYY-Qn`` 으로 바꾼다."""
    return f"{key[0]:04d}-Q{key[1]}"


def _sliceSeriesAsOf(series: dict, periods: list[str], asOf: str | None) -> tuple[dict, str, str, str]:
    """분기 재무 시리즈를 요청 기간까지 절단하고 effective/latest 라벨을 반환한다.

    Returns:
        ``(slicedSeries, effectiveAsOf, latestAsOf, requestedAsOf)``. 현재 저장소의 재무 시리즈는
        공시 접수일 vintage 를 보존하지 않으므로 이 함수는 fiscal-period PIT 이며, 정정공시 이전
        값까지 복원하는 filing-vintage PIT 는 아니다. 호출자가 이 제한을 warnings 로 노출한다.
    """
    if not periods:
        requested = str(asOf) if asOf is not None else "latest"
        return series, requested, "latest", requested

    keyed = [(_periodKey(period), idx) for idx, period in enumerate(periods)]
    latestKey = max(key for key, _ in keyed)
    requestedKey = latestKey if asOf is None else _periodKey(asOf)
    if requestedKey < min(key for key, _ in keyed) or requestedKey > latestKey:
        raise ValueError(
            f"asOf={asOf!r} 는 가용 기간 {_periodLabel(min(key for key, _ in keyed))}~"
            f"{_periodLabel(latestKey)} 밖입니다."
        )

    kept = [idx for key, idx in keyed if key <= requestedKey]
    effectiveKey = max(key for key, _ in keyed if key <= requestedKey)
    sliced: dict[str, dict[str, list]] = {}
    for sjDiv, accounts in series.items():
        sliced[sjDiv] = {}
        for account, values in accounts.items():
            sliced[sjDiv][account] = [values[idx] if idx < len(values) else None for idx in kept]
    return sliced, _periodLabel(effectiveKey), _periodLabel(latestKey), _periodLabel(requestedKey)


def _workbenchFinanceInputs(company: Any, asOf: str | None) -> tuple[dict, dict[str, Any]]:
    """통합 Data Workbench를 통해 시뮬레이터의 read-once 재무 입력을 취득한다."""
    import dartlab
    from dartlab.dataHub import DataQuery, TimeContext

    subject = str(getattr(company, "stockCode", None) or "bound-company")
    time = TimeContext(validAt=asOf) if asOf is not None else None
    dataCall = getattr(dartlab, "dataHub")
    result = dataCall(
        "query",
        "analysis.simulationInputs",
        query=DataQuery(
            subjects=(subject,),
            time=time,
            completeness="requireComplete",
        ),
        _runtimeBindings={"analysis.simulationInputs": {"company": company}},
    )
    dataInputGaps = tuple(f"{gap.code}:{gap.message}" for gap in result.gaps)
    coverage = getattr(result, "coverage", None)
    dataEvidence = {
        "status": str(getattr(result, "status", "unknown")),
        "coverage": {
            "requestedAssets": int(getattr(coverage, "requestedAssets", 0)),
            "resolvedAssets": int(getattr(coverage, "resolvedAssets", 0)),
            "succeededPartitions": int(getattr(coverage, "succeededPartitions", 0)),
            "failedPartitions": int(getattr(coverage, "failedPartitions", 0)),
        },
        "assets": tuple((str(asset.assetId), str(asset.assetVersionId)) for asset in getattr(result, "assets", ())),
        "gaps": tuple(
            {
                "code": str(gap.code),
                "message": str(gap.message),
                "assetId": gap.assetId,
                "subject": gap.subject,
                "systemic": bool(gap.systemic),
                "requestId": gap.requestId,
            }
            for gap in result.gaps
        ),
        "partitions": tuple(
            {
                "assetId": str(partition.asset.assetId),
                "assetVersionId": str(partition.asset.assetVersionId),
                "requestId": partition.requestId,
                "selector": tuple(partition.selector),
                "temporalStatus": str(partition.temporalStatus),
                "contentHash": partition.contentHash,
                "truncated": bool(partition.truncated),
            }
            for partition in result.partitions
        ),
        "qualityAssertions": tuple(
            {
                "assertionId": str(assertion.assertionId),
                "success": assertion.success,
                "severity": str(assertion.severity),
                "assetId": str(assertion.assetId),
            }
            for assertion in getattr(result, "qualityAssertions", ())
        ),
        "catalogSnapshotId": str(result.snapshotId),
        "dataSnapshotId": str(result.dataSnapshotId or ""),
        "contractHash": str(result.contractHash),
        "lineageRefs": tuple(result.lineageRefs),
        "executionReceipts": tuple(result.executionReceipts),
        "materializationReceiptJson": (
            json.dumps(result.materializationReceipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            if getattr(result, "materializationReceipt", None) is not None
            else None
        ),
    }
    if result.partitions:
        if len(result.partitions) != 1:
            raise RuntimeError("simulation input 결과의 partition 수가 1이 아닙니다")
        partition = result.partitions[0]
        if partition.asset.assetId != "analysis.simulationInputs":
            raise RuntimeError("simulation input 결과가 요청 asset과 일치하지 않습니다")
        if partition.truncated or not partition.contentHash:
            raise RuntimeError("simulation input partition이 완전한 content seal을 갖지 못했습니다")
        if coverage is None or (
            coverage.requestedAssets != 1
            or coverage.resolvedAssets != 1
            or coverage.succeededPartitions != 1
            or coverage.failedPartitions != 0
        ):
            raise RuntimeError("simulation input 결과의 coverage 계약이 완전하지 않습니다")
        payload = partition.data
        if isinstance(payload, dict):
            if result.dataSnapshotId is None:
                raise RuntimeError("simulation input 결과가 content-sealed snapshot이 아닙니다")
            metadata = {
                "dataSnapshotId": result.dataSnapshotId,
                "dataCatalogSnapshotId": result.snapshotId,
                "dataContractHash": result.contractHash,
                "dataLineageRefs": result.lineageRefs,
                "dataExecutionReceipts": result.executionReceipts,
                "dataInputGaps": dataInputGaps,
                "dataEvidence": dataEvidence,
            }
            return payload, metadata
    for gap in result.gaps:
        if gap.code == "ASSET_EXECUTION_FAILED" and "asOf" in gap.message:
            raise ValueError(gap.message)
    requested = str(asOf) if asOf is not None else "latest"
    return {
        "series": None,
        "asOf": requested,
        "latestAsOf": "latest",
        "requestedAsOf": requested,
    }, {
        "dataSnapshotId": result.dataSnapshotId or "",
        "dataCatalogSnapshotId": result.snapshotId,
        "dataContractHash": result.contractHash,
        "dataLineageRefs": result.lineageRefs,
        "dataExecutionReceipts": result.executionReceipts,
        "dataInputGaps": dataInputGaps,
        "dataEvidence": dataEvidence,
    }


def buildSnapshot(company: Any, *, asOf: str | None = None) -> dict:
    """Read a company's frozen base metrics ONCE into a simulate snapshot (§13b-5).

    Capabilities:
        Loads the read-once inputs the deterministic driver DAG consumes (the finance series,
        base revenue / operating margin / net debt, shares outstanding, sector elasticity, and
        base WACC) into a flat dict the registry fns read during evaluation. After this call no
        node reloads data, so an `evaluateSheet` re-run over the snapshot is byte-identical.

    Args:
        company: a `Company` (DART/EDGAR) instance. Read forward via the L2
            Data Workbench simulation input asset, `_resolveSectorKey`, and `sectorParams`.
        asOf: an explicit data-vintage label to stamp on every node. When None, falls back to the
            company's latest finance period (or ``"latest"`` if unavailable).

    Returns:
        dict: the snapshot with keys ``series`` (dict | None), ``baseRevenue`` (float | None),
        ``baseMargin`` (float | None), ``netDebt`` (float), ``shares`` (int | None),
        ``elasticity`` (SectorElasticity), ``sectorKey`` (str | None), ``baseWacc`` (float),
        ``asOf`` (str), ``latestAsOf`` (str). Missing accounts leave revenue/margin None
        (honest-gap), never 0.

    Raises:
        ValueError: 요청 시점이 가용 재무 범위를 벗어나거나 owner 입력 계약이 잘못된 경우.
        RuntimeError: Data Workbench 결과가 완전한 단일 partition/content seal 계약을 어긴 경우.

    Example:
        >>> snap = buildSnapshot(Company("005930"))  # doctest: +SKIP
        >>> set(snap) >= {"series", "baseRevenue", "elasticity", "shares"}  # doctest: +SKIP
        True

    Guide:
        Build the snapshot once per `runScenario`; reuse it across the per-scenario sheet so the
        elasticity / base metrics are identical for baseline vs adverse (only the macro path
        differs). Read by the registry fns, never mutated during evaluation.

    SeeAlso:
        - ``buildScenarioSheet``: wires a `DriverSheet` over this snapshot.
        - ``dartlab.analysis.financial.dataAssets.simulationInputs``: series + shares.
        - ``dartlab.synth.scenario.getElasticity``: sector-key -> elasticity.

    Requires:
        A `Company` exposing `_buildFinanceSeries`, `sector`, and `sectorParams`.

    AIContext:
        The snapshot is frozen assumptions, not a forecast. Surface `sectorKey`, `elasticity`,
        and `asOf` so the scenario is auditable; a None revenue means "data absent", not zero.

    LLM Specifications:
        AntiPatterns:
            - Re-reading the company inside a node fn. Breaks snapshot determinism (§13b-5).
            - Treating a None baseRevenue as 0. It is an honest data gap.
        OutputSchema: ``dict`` with the keys listed under Returns.
        Prerequisites: a constructed `Company`.
        Freshness: inherits the company's latest finance period as `asOf`/`latestAsOf`.
        Dataflow: company -> series + shares -> base metrics + elasticity + WACC -> snapshot dict.
        TargetMarkets: KR (semiconductor elasticity baselines); US needs US baselines.
    """
    # proforma와 TTM 추출기는 분기 시리즈를 소비한다. 과거 구현은 연간 시리즈에 getTTM을 적용해
    # 최근 4개 연도를 합산하는 오류가 있었다. shares 조회의 기존 fallback만 재사용하고, 계산
    # 시리즈는 반드시 Q 경로에서 한 번 읽어 asOf 절단한다.
    workbenchInput, workbenchMetadata = _workbenchFinanceInputs(company, asOf)
    series = workbenchInput["series"]
    shares = workbenchInput.get("shares")
    effectiveAsOf = workbenchInput["asOf"]
    latestAsOf = workbenchInput["latestAsOf"]
    requestedAsOf = workbenchInput["requestedAsOf"]
    base = _baseMetrics(series) if series else {"revenue": None, "margin": None, "netDebt": None}

    parameterVintageAvailable = effectiveAsOf == latestAsOf
    sectorKey = _resolveSectorKey(company) if parameterVintageAvailable else None
    elasticity = getElasticity(sectorKey) if sectorKey else DEFAULT_ELASTICITY
    assumptions: list[str] = []
    warnings: list[str] = []
    if sectorKey is None:
        assumptions.append("defaultSectorElasticity")
    if not parameterVintageAvailable:
        warnings.append("historicalSimulationParametersUnavailable")

    sectorParams = None
    if parameterVintageAvailable:
        try:
            sectorParams = getattr(company, "sectorParams", None)
        except (AttributeError, ValueError):
            sectorParams = None
    rawWacc = getattr(sectorParams, "discountRate", None)
    if rawWacc is None:
        assumptions.append("baseWacc10Pct")
    baseWacc = rawWacc if rawWacc is not None else _DEFAULT_BASE_WACC
    rawTerminalGrowth = getattr(sectorParams, "growthRate", None)
    if rawTerminalGrowth is None:
        assumptions.append("terminalGrowth3Pct")
    terminalGrowth = min(
        rawTerminalGrowth if rawTerminalGrowth is not None else _TERMINAL_GROWTH_CAP, _TERMINAL_GROWTH_CAP
    )
    if base["margin"] is None and base["revenue"] is not None:
        assumptions.append("baseMargin10Pct")
    if base["netDebt"] is None:
        warnings.append("netDebtUnavailable")

    if effectiveAsOf != latestAsOf and shares is None:
        warnings.append("historicalSharesUnavailable")
    if asOf is not None:
        warnings.append("periodScopedPitOnly")

    return {
        "series": series,
        "baseRevenue": base["revenue"],
        "baseMargin": base["margin"],
        "netDebt": base["netDebt"],
        "shares": shares,
        "elasticity": elasticity,
        "sectorKey": sectorKey,
        "baseWacc": float(baseWacc),
        "terminalGrowth": float(terminalGrowth),
        "asOf": effectiveAsOf,
        "latestAsOf": latestAsOf,
        "requestedAsOf": requestedAsOf,
        "assumptions": tuple(assumptions),
        "warnings": tuple(warnings),
        "parameterVintageStatus": "available" if parameterVintageAvailable else "unavailable",
        **workbenchMetadata,
    }


def validateScenarioSpec(scenario: str, horizon: int, *, market: str = "KR") -> None:
    """프리셋에 실제로 존재하는 시나리오와 경로 길이만 허용한다."""
    if not isinstance(scenario, str):
        raise TypeError("scenario 는 문자열이어야 합니다.")
    presets = getPresetScenarios(market)
    if scenario not in presets:
        valid = ", ".join(sorted(presets))
        raise ValueError(f"알 수 없는 scenario={scenario!r}; 유효값: {valid}")
    if isinstance(horizon, bool) or not isinstance(horizon, int):
        raise TypeError("horizon 은 정수여야 합니다.")
    if horizon <= 0:
        raise ValueError("horizon 은 1 이상이어야 합니다.")
    preset = presets[scenario]
    maxHorizon = min(len(preset.gdpGrowth), len(preset.interestRate), len(preset.krwUsd))
    if horizon > maxHorizon:
        raise ValueError(f"horizon={horizon} 은 scenario={scenario!r}의 가용 경로 {maxHorizon}년을 초과합니다.")


# ──────────────────────────────────────────────────────────────────────
# §5 deterministic node fns. Each matches the evaluateSheet 7-tuple contract
# ──────────────────────────────────────────────────────────────────────


def nodeIdFor(driverId: str, scenarioId: str) -> str:
    """Return the §6.1 node id of one driver in one scenario.

    Args:
        driverId: a driver id such as ``DRIVER_REV``.
        scenarioId: the scenario id such as ``"baseline"``.

    Returns:
        str: ``"{driverId}@{scenarioId}#all"``. The deterministic core folds the period coordinate
        into the node vector, so the period key is always ``all``.

    Raises:
        None.

    Example:
        >>> nodeIdFor("rev.path", "baseline")
        'rev.path@baseline#all'
    """
    return f"{driverId}@{scenarioId}#all"


def _depValue(depValues: dict, driverId: str, node: DriverNode) -> NodeValue:
    """같은 시나리오의 상류 node 값을 driver id 로 찾는다. 배선이 틀리면 기본값 없이 실패한다."""
    key = nodeIdFor(driverId, node.scenarioId)
    if key not in depValues:
        raise ValueError(f"{node.nodeId} needs its {driverId} dependency")
    return depValues[key]


def _depVector(depValues: dict, driverId: str, node: DriverNode) -> list[float]:
    """상류 거시 경로 벡터를 꺼낸다. 프리셋 경로에 결손이 있으면 0 으로 메우지 않고 실패한다."""
    vector = _depValue(depValues, driverId, node).vector
    if vector is None or any(value is None for value in vector):
        raise ValueError(f"{node.nodeId} got an incomplete {driverId} path")
    return [float(value) for value in vector]


def _gapValue(prefix: str, reason: str, snap: dict):
    """정직한 결손 node 값. 값과 벡터는 None 이고 사유가 provenance 와 frozen input 에 남는다."""
    return None, None, f"{prefix}:gap({reason})", (), {"gap": reason}, snap["asOf"], snap["latestAsOf"]


def _channelGap(snap: dict) -> str | None:
    """매출·마진 채널을 계산할 수 없는 사유. 과거 시점은 파라미터 vintage 가 없어 기권한다."""
    if snap.get("parameterVintageStatus", "available") != "available":
        return "historical_parameter_vintage_absent"
    if snap["baseRevenue"] is None:
        return "baseRevenue_absent"
    return None


def _effectiveBaseMargin(snap: dict) -> float:
    """전달 채널의 기준 영업이익률. 결손이면 기본값을 쓰고 buildSnapshot 이 가정으로 남긴다."""
    return float(snap["baseMargin"]) if snap["baseMargin"] is not None else _DEFAULT_MARGIN


def _presetNode(node: DriverNode, sheet: DriverSheet, variable: str):
    """프리셋 거시 변수 하나의 경로를 root node 로 낸다. 모르는 시나리오는 KeyError 로 실패한다."""
    snap = sheet.snapshot
    horizon = snap["horizon"]
    scenario = getPresetScenarios(_PRESET_MARKET)[node.scenarioId]
    source = {"gdp": scenario.gdpGrowth, "rate": scenario.interestRate, "fx": scenario.krwUsd}[variable]
    path = [float(value) for value in source[:horizon]]
    frozen = {"variable": variable, "path": path}
    refs = (f"synth.scenario:PRESET_SCENARIOS_{_PRESET_MARKET}/{scenario.name}#{variable}",)
    value = path[-1] if path else None
    return value, tuple(path), f"preset:{node.scenarioId}", refs, frozen, snap["asOf"], snap["latestAsOf"]


def _fnMacroPath(node: DriverNode, sheet: DriverSheet, depValues: dict):
    """`macro.path` node: the preset GDP path for the node's scenario (§5).

    Capabilities:
        Emits the preset GDP path for the scenario named by ``node.scenarioId`` from
        `synth.scenario.getPresetScenarios` (KR), truncated to the snapshot horizon. The
        representative value is terminal-year GDP and the vector is the GDP path. The rate and
        FX paths are their own root nodes (`macro.rate`, `macro.fx`), so every downstream channel
        reads its macro inputs through dependencies rather than re-reading the preset.

    Args:
        node: the macro.path DriverNode (its `scenarioId` selects the preset).
        sheet: the DriverSheet (its `snapshot["horizon"]` truncates the path).
        depValues: empty (macro.path is a root node).

    Returns:
        tuple: ``(gdpTerminal, gdpVector, provenance, refs, frozenInputs, asOf, latestAsOf)``
        with ``provenance = "preset:{scenarioId}"`` and ``frozenInputs = {"variable", "path"}``.

    Raises:
        KeyError: if validation was bypassed and the scenario id is unknown.

    Example:
        >>> # wired by buildScenarioSheet; not called directly.

    Requires:
        ``synth.scenario.getPresetScenarios`` and the snapshot's ``horizon`` / ``asOf``.
    """
    return _presetNode(node, sheet, "gdp")


def _fnMacroRate(node: DriverNode, sheet: DriverSheet, depValues: dict):
    """`macro.rate` node: the preset policy-rate path for the node's scenario (root node)."""
    return _presetNode(node, sheet, "rate")


def _fnMacroFx(node: DriverNode, sheet: DriverSheet, depValues: dict):
    """`macro.fx` node: the preset KRW/USD path for the node's scenario (root node)."""
    return _presetNode(node, sheet, "fx")


def _fnRevPath(node: DriverNode, sheet: DriverSheet, depValues: dict):
    """`rev.path` node: the revenue channel of the owned macro->fundamentals edge (§2/§5).

    Capabilities:
        Chains `simulate.transfer.transferRevenueChannel` over the GDP and FX dependency paths onto
        base revenue + sector elasticity, producing the scenario's absolute revenue vector. The
        margin and WACC channels are separate nodes. honest-gap: if base revenue is absent the
        node value is None (never 0).

    Args:
        node: the rev.path DriverNode (depends on the scenario's macro.path and macro.fx).
        sheet: the DriverSheet whose snapshot holds base revenue and elasticity.
        depValues: the GDP and FX NodeValues of the same scenario.

    Returns:
        tuple: ``(revTerminal, revVector, provenance, refs, frozenInputs, asOf, latestAsOf)`` with
        ``provenance`` describing the transfer; value/vector are None when base revenue is absent.

    Raises:
        ValueError: if the GDP or FX dependency is missing or incomplete.

    Example:
        >>> # wired by buildScenarioSheet; not called directly.

    Requires:
        The macro.path and macro.fx dependency vectors and the snapshot base metrics.
    """
    from dartlab.simulate.transfer import transferRevenueChannel

    snap = sheet.snapshot
    gap = _channelGap(snap)
    if gap is not None:
        # honest-gap: no base revenue or no parameter vintage -> no scenario path.
        return _gapValue("transfer", gap, snap)

    elasticity: SectorElasticity = snap["elasticity"]
    gdp = _depVector(depValues, DRIVER_MACRO, node)
    fx = _depVector(depValues, DRIVER_FX, node)
    revPath = transferRevenueChannel(snap["baseRevenue"], gdp, fx, elasticity)
    frozen = {"baseRevenue": snap["baseRevenue"], "rev": revPath}
    prov = "transfer:rev*(1+bgdp*gdp+bfx*fxDelta)"
    refs = ("simulate.transfer:transferRevenueChannel",)
    value = revPath[-1] if revPath else None
    return value, tuple(revPath), prov, refs, frozen, snap["asOf"], snap["latestAsOf"]


def _fnMarginPath(node: DriverNode, sheet: DriverSheet, depValues: dict):
    """`margin.path` node: the operating-margin channel of the transfer (GDP, rate for financials).

    Capabilities:
        Carries the base operating margin over the horizon with the sector's GDP margin shock and
        the rate NIM shock (non-zero only for financials), floored at -50 each year. The proforma
        node applies this path as a margin shock on top of its own projection, so the channel
        moves operating profit and FCF instead of being display-only.

    Args:
        node: the margin.path DriverNode (depends on macro.path and macro.rate).
        sheet: the DriverSheet whose snapshot holds base margin and elasticity.
        depValues: the GDP and policy-rate NodeValues of the same scenario.

    Returns:
        tuple: ``(terminalMargin, marginVector, provenance, refs, frozenInputs, asOf, latestAsOf)``;
        value and vector are None on an honest gap.

    Raises:
        ValueError: if the GDP or rate dependency is missing or incomplete.

    Example:
        >>> # wired by buildScenarioSheet; not called directly.
    """
    from dartlab.simulate.transfer import transferMarginChannel

    snap = sheet.snapshot
    gap = _channelGap(snap)
    if gap is not None:
        return _gapValue("transfer", gap, snap)
    baseMargin = _effectiveBaseMargin(snap)
    gdp = _depVector(depValues, DRIVER_MACRO, node)
    rate = _depVector(depValues, DRIVER_RATE, node)
    marginPath = transferMarginChannel(baseMargin, gdp, rate, snap["elasticity"])
    frozen = {"baseMargin": baseMargin, "margin": marginPath}
    prov = "transfer:margin+bm*gdp+nim*rateDelta"
    refs = ("simulate.transfer:transferMarginChannel",)
    value = marginPath[-1] if marginPath else None
    return value, tuple(marginPath), prov, refs, frozen, snap["asOf"], snap["latestAsOf"]


def _fnWaccPath(node: DriverNode, sheet: DriverSheet, depValues: dict):
    """`wacc.path` node: the discount-rate channel of the transfer (half the rate change).

    Capabilities:
        Maps the scenario's policy-rate path onto a per-year WACC path around the snapshot base
        WACC. The dcf node discounts each year at this path, so a rate shock changes the value.

    Args:
        node: the wacc.path DriverNode (depends on macro.rate).
        sheet: the DriverSheet whose snapshot holds the base WACC.
        depValues: the policy-rate NodeValue of the same scenario.

    Returns:
        tuple: ``(terminalWacc, waccVector, provenance, refs, frozenInputs, asOf, latestAsOf)``;
        value and vector are None when the parameter vintage is unavailable.

    Raises:
        ValueError: if the rate dependency is missing or incomplete.

    Example:
        >>> # wired by buildScenarioSheet; not called directly.
    """
    from dartlab.simulate.transfer import transferWaccChannel

    snap = sheet.snapshot
    if snap.get("parameterVintageStatus", "available") != "available":
        return _gapValue("transfer", "historical_parameter_vintage_absent", snap)
    rate = _depVector(depValues, DRIVER_RATE, node)
    waccPath = transferWaccChannel(float(snap["baseWacc"]), rate)
    frozen = {"baseWacc": float(snap["baseWacc"]), "wacc": waccPath}
    prov = "transfer:wacc+0.5*rateDelta"
    refs = ("simulate.transfer:transferWaccChannel",)
    value = waccPath[-1] if waccPath else None
    return value, tuple(waccPath), prov, refs, frozen, snap["asOf"], snap["latestAsOf"]


def _fnProforma(node: DriverNode, sheet: DriverSheet, depValues: dict):
    """`proforma` node: call the L2 leaf buildProforma over the scenario growth path (§2/§5).

    Capabilities:
        Converts the rev.path absolute-revenue vector into the year-over-year growth path
        `buildProforma` expects and the margin.path vector into a per-year operating-margin shock
        over the base margin (edge wiring owned by the node, not leaf math), then calls the L2
        leaf `analysis.financial.proforma.buildProforma` to produce IS/BS/CF projections. The
        node value is the terminal-year revenue; the vector is per-year FCF (so the dcf node can
        discount it). honest-gap: if rev.path or margin.path produced no path the node is None.

    Args:
        node: the proforma DriverNode (depends on rev.path and margin.path).
        sheet: the DriverSheet whose snapshot holds the finance series + base revenue.
        depValues: the rev.path revenue vector and the margin.path margin vector.

    Returns:
        tuple: ``(terminalRevenue, fcfVector, provenance, refs, frozenInputs, asOf, latestAsOf)``
        with ``provenance = "proforma:cashplug,marginShock,years=.."``; value/vector None on gap.

    Raises:
        ValueError: if a dependency is missing. Other leaf gaps are reported as gap values.

    Example:
        >>> # wired by buildScenarioSheet; not called directly.

    Requires:
        The L2 leaf ``buildProforma`` and the snapshot ``series`` / ``baseRevenue``.
    """
    snap = sheet.snapshot
    revNv = _depValue(depValues, DRIVER_REV, node)
    marginNv = _depValue(depValues, DRIVER_MARGIN, node)
    series = snap.get("series")
    base = snap["baseRevenue"]
    if revNv.vector is None or not revNv.vector or series is None or base is None:
        return _gapValue("proforma", "revPath_or_series_absent", snap)
    if marginNv.vector is None or len(marginNv.vector) != len(revNv.vector):
        return _gapValue("proforma", "marginPath_absent", snap)

    revPath = list(revNv.vector)
    growthPath: list[float] = []
    prev = base
    for r in revPath:
        growthPath.append((r / prev - 1.0) * 100.0 if prev else 0.0)
        prev = r
    # The transfer margin path is base margin plus the carried macro shock. The leaf keeps its own
    # ratio-based margin projection and receives only the shock, so the scenario moves operating
    # profit without replacing the historical cost structure.
    baseMargin = _effectiveBaseMargin(snap)
    marginShockPath = [float(margin) - baseMargin for margin in marginNv.vector]

    pf = buildProforma(
        series,
        revenueGrowthPath=growthPath,
        scenarioName=node.scenarioId,
        operatingMarginShockPath=marginShockPath,
    )
    proj = pf.projections
    if not proj:
        frozen = {
            "growthPath": [round(g, 9) for g in growthPath],
            "marginShockPath": [round(m, 9) for m in marginShockPath],
        }
        return None, None, "proforma:gap(no_projections)", (), frozen, snap["asOf"], snap["latestAsOf"]

    fcf = tuple(round(y.fcf, 2) for y in proj)
    frozen = {
        "growthPath": [round(g, 9) for g in growthPath],
        "marginShockPath": [round(m, 9) for m in marginShockPath],
        "series": series,
    }
    prov = f"proforma:cashplug,marginShock,years={len(proj)}"
    refs = ("analysis.financial.proforma:buildProforma",)
    return round(proj[-1].revenue, 2), fcf, prov, refs, frozen, snap["asOf"], snap["latestAsOf"]


def _fnDcf(node: DriverNode, sheet: DriverSheet, depValues: dict):
    """`dcf` node: FCFF discount off the proforma FCF path -> per-share value (§5).

    Capabilities:
        Discounts the proforma node's per-year FCF vector year by year at the wacc.path vector,
        adds a Gordon terminal value at the terminal-year WACC (terminal growth capped at the
        sector cap), nets out the snapshot net debt, and divides by shares for a per-share value.
        It ports the legacy terminal-value formula so the value reflects THIS scenario's proforma
        FCF and rate path rather than re-running an independent model (see module docstring on
        why not `calcDFV`). A flat WACC path reproduces the constant-rate formula exactly.
        honest-gap: a missing FCF path, WACC path or shares yields a None per-share value with a
        partial-marking provenance.

    Args:
        node: the dcf DriverNode (depends on proforma and wacc.path).
        sheet: the DriverSheet whose snapshot holds netDebt / shares / terminalGrowth.
        depValues: the proforma FCF vector and the wacc.path WACC vector of the same scenario.

    Returns:
        tuple: ``(perShare, scalarVector, provenance, refs, frozenInputs, asOf, latestAsOf)``.
        ``scalarVector`` is a 1-tuple of enterprise value; ``perShare`` is None when FCF or shares
        are absent (honest-gap).

    Raises:
        None.

    Example:
        >>> # wired by buildScenarioSheet; not called directly.

    Requires:
        The proforma dep's FCF vector + frozen ``wacc`` and the snapshot ``netDebt`` / ``shares``.
    """
    snap = sheet.snapshot
    pfNv = _depValue(depValues, DRIVER_PROFORMA, node)
    waccNv = _depValue(depValues, DRIVER_WACC, node)
    if pfNv.vector is None or not pfNv.vector:
        return _gapValue("dcf", "fcfPath_absent", snap)
    if any(value is None for value in pfNv.vector):
        return _gapValue("dcf", "fcfPath_incomplete", snap)
    if waccNv.vector is None or len(waccNv.vector) != len(pfNv.vector) or any(value is None for value in waccNv.vector):
        return _gapValue("dcf", "waccPath_absent", snap)
    fcfPath = [float(x) for x in pfNv.vector]
    # WACC: the scenario's per-year path (base WACC plus half the rate change). Discounting year by
    # year at that path is what lets a rate shock move the value; a flat path reproduces the
    # constant-rate formula exactly.
    waccPath = [float(w) for w in waccNv.vector]
    terminalWacc = waccPath[-1]
    terminalGrowth = float(snap["terminalGrowth"])
    if terminalWacc <= terminalGrowth or any(w <= -100.0 for w in waccPath):
        frozen = {
            "gap": "terminalGrowth_not_below_wacc",
            "waccPath": [round(w, 9) for w in waccPath],
            "terminalGrowth": terminalGrowth,
        }
        return (
            None,
            None,
            "dcf:gap(terminalGrowth_not_below_wacc)",
            (),
            frozen,
            snap["asOf"],
            snap["latestAsOf"],
        )

    discount = 1.0
    pvSum = 0.0
    for fcf, wacc in zip(fcfPath, waccPath):
        discount *= 1 + wacc / 100
        pvSum += fcf / discount
    terminalFcf = fcfPath[-1]
    if terminalFcf > 0:
        tv = terminalFcf * (1 + terminalGrowth / 100) / (terminalWacc / 100 - terminalGrowth / 100)
        pvTv = tv / discount
    else:
        pvTv = 0.0
    ev = pvSum + pvTv
    netDebt = snap["netDebt"]
    equityValue = ev - netDebt if netDebt is not None else None
    shares = snap["shares"]
    perShare = (equityValue / shares) if equityValue is not None and shares and shares > 0 else None

    frozen = {
        "waccPath": [round(w, 9) for w in waccPath],
        "terminalGrowth": round(terminalGrowth, 9),
        "netDebt": round(netDebt, 2) if netDebt is not None else None,
        "shares": shares,
    }
    gaps: list[str] = []
    if netDebt is None:
        gaps.append("netDebt_absent")
    if shares is None or shares <= 0:
        gaps.append("shares_absent")
    gap = f"({','.join(gaps)})" if gaps else ""
    prov = f"dcf:fcff,wacc={waccPath[0]:.2f}..{terminalWacc:.2f},g={terminalGrowth:.2f}{gap}"
    refs = ("simulate.registry:fcffDiscount", "analysis.financial.proforma:buildProforma")
    return perShare, (round(ev, 2),), prov, refs, frozen, snap["asOf"], snap["latestAsOf"]


# ──────────────────────────────────────────────────────────────────────
# sheet builder
# ──────────────────────────────────────────────────────────────────────

# (driverId, dependency driverIds, registry fn key, fn). The one wiring table; buildScenarioSheet
# and the result assembly both read it, so a new channel cannot be wired without being audited.
_SHEET_WIRING = (
    (DRIVER_MACRO, (), _FN_MACRO, _fnMacroPath),
    (DRIVER_RATE, (), _FN_MACRO_RATE, _fnMacroRate),
    (DRIVER_FX, (), _FN_MACRO_FX, _fnMacroFx),
    (DRIVER_REV, (DRIVER_MACRO, DRIVER_FX), _FN_REV, _fnRevPath),
    (DRIVER_MARGIN, (DRIVER_MACRO, DRIVER_RATE), _FN_MARGIN, _fnMarginPath),
    (DRIVER_WACC, (DRIVER_RATE,), _FN_WACC, _fnWaccPath),
    (DRIVER_PROFORMA, (DRIVER_REV, DRIVER_MARGIN), _FN_PROFORMA, _fnProforma),
    (DRIVER_DCF, (DRIVER_PROFORMA, DRIVER_WACC), _FN_DCF, _fnDcf),
)
SCENARIO_DRIVER_IDS = tuple(row[0] for row in _SHEET_WIRING)


def buildScenarioSheet(snapshot: dict, *, scenario: str, horizon: int) -> DriverSheet:
    """Wire the deterministic 4-node DriverSheet for one scenario over a frozen snapshot (§5/§6).

    Capabilities:
        Builds the 8-node chain (three macro roots, the revenue / margin / WACC channels,
        ``proforma`` and ``dcf``) for a single scenario from ``_SHEET_WIRING``,
        registering each driver fn and adding the nodes with the §6.1 3-coordinate
        ``{driverId}@{scenarioId}#{periodKey}`` ids. The returned sheet is ready for
        `evaluateSheet`; the snapshot (read once by `buildSnapshot`) is attached with the scenario
        horizon so every node reads from it without reloading data.

    Args:
        snapshot: the frozen base-metric snapshot from `buildSnapshot`.
        scenario: the scenario id (e.g. ``"baseline"`` / ``"adverse"``) - selects the macro preset
            and stamps every node's `scenarioId`.
        horizon: number of forecast years (paths are truncated to this length).

    Returns:
        DriverSheet: a wired sheet with 8 nodes and the deterministic registry. Pass to
        `evaluateSheet` to fill each node's `det`.

    Raises:
        None. Wiring validity (cycle / missing dep) is enforced later by `buildOrder` inside
        `evaluateSheet`.

    Example:
        >>> snap = buildSnapshot(Company("005930"))  # doctest: +SKIP
        >>> sheet = buildScenarioSheet(snap, scenario="baseline", horizon=3)  # doctest: +SKIP
        >>> len(sheet.nodes)  # doctest: +SKIP
        8

    Guide:
        Build one sheet per scenario over a shared snapshot; baseline vs adverse differ only in
        the macro preset (the elasticity / base metrics are identical), which is exactly the
        scenario-comparison contract.

    SeeAlso:
        - ``buildSnapshot``: produces the snapshot this consumes.
        - ``dartlab.simulate.sheet.evaluateSheet``: evaluates the wired sheet.
        - ``dartlab.simulate.run.runScenario``: the end-to-end driver.

    Requires:
        A snapshot dict from `buildSnapshot` (so the nodes have base metrics + asOf).

    AIContext:
        The sheet is the audit object. Each node's `det.provenance`/`refs` tells the user which
        L2 leaf produced it; never blend a (future) lens opinion into `det`.

    LLM Specifications:
        AntiPatterns:
            - Reusing one sheet across scenarios. Each scenario gets its own macro preset / ids.
            - Mutating the snapshot per node. Breaks re-run determinism.
        OutputSchema: ``DriverSheet`` with 8 nodes + an 8-entry registry.
        Prerequisites: a `buildSnapshot` result.
        Freshness: inherits the snapshot's `asOf`/`latestAsOf`.
        Dataflow: snapshot+scenario -> _SHEET_WIRING (register fn + add node per driver) -> sheet.
        TargetMarkets: KR presets (getPresetScenarios("KR")); US needs US presets.
    """
    validateScenarioSpec(scenario, horizon)
    snap = dict(snapshot)
    snap["horizon"] = horizon
    sheet = DriverSheet(snapshot=snap)
    for driverId, deps, fnKey, fn in _SHEET_WIRING:
        sheet.registry[fnKey] = fn
        sheet.add(
            DriverNode(
                nodeIdFor(driverId, scenario),
                driverId,
                scenario,
                "all",
                tuple(nodeIdFor(dep, scenario) for dep in deps),
                fnKey,
            )
        )
    return sheet
