"""End-to-end deterministic scenario run (L2.5, internal). `runScenario`.

A simulate result is always a set of node values carrying
``ref + quality gate status + provenance + asOf``. This module wires
the born-clean foundation into one run:

    buildSnapshot(company)             # read base metrics ONCE (§13b-5)
      -> buildScenarioSheet(snapshot)  # macro -> rev -> proforma -> dcf (registry §5)
        -> evaluateSheet(sheet)        # deterministic topo executor (§6.2)
          -> SimulationResult          # ref + quality status + provenance + asOf (§3)

`runScenario` is internal. Callable top-level and Company surfaces attach the current lens
products as context while the deterministic DriverSheet remains unchanged. Play and
DriverRegistry convergence remain separate phases. honest-gap (§3): a missing leaf or absent base metric leaves the corresponding
field None and downgrades the node's quality status to ``partial`` - never silently 0.

Born-clean (§10): imports forward only - L2.5 `registry`/`sheet` (which themselves import L0/L1.5/
L2). The legacy `analysis/forecast/simulation.py` flow is never touched.

Layer: L3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dartlab.simulate.registry import (
    DRIVER_DCF,
    DRIVER_MACRO,
    DRIVER_PROFORMA,
    DRIVER_REV,
    buildScenarioSheet,
    buildSnapshot,
    validateScenarioSpec,
)
from dartlab.simulate.sheet import NodeValue, evaluateSheet


@dataclass(frozen=True)
class NodeAudit:
    """Per-node audit record surfaced on a SimulationResult (§3).

    driverId   : the node's driver id (``macro.path`` / ``rev.path`` / ``proforma`` / ``dcf``).
    status     : ``"ok"`` when the node produced a value, ``"partial"`` on an honest data gap.
    provenance : the node's formula tag (``preset:..`` / ``transfer:..`` / ``proforma:..`` / ``dcf:..``).
    refs       : grounding ref addresses (leaf refs).
    inputsHash : the deterministic memoization key (stable across re-runs on identical inputs).
    asOf       : data vintage used.
    latestAsOf : latest available vintage.
    """

    driverId: str
    status: str
    provenance: str
    refs: tuple[str, ...]
    inputsHash: str
    asOf: str
    latestAsOf: str


@dataclass(frozen=True)
class DataGapEvidence:
    """Data Workbench gap을 문자열로 축약하지 않고 보존한 입력 근거."""

    code: str
    message: str
    assetId: str | None = None
    subject: str | None = None
    systemic: bool = False
    requestId: str | None = None


@dataclass(frozen=True)
class DataPartitionEvidence:
    """시뮬레이션 입력 partition의 selector, 시점, content seal."""

    assetId: str
    assetVersionId: str
    requestId: str | None
    selector: tuple[tuple[str, str], ...]
    temporalStatus: str
    contentHash: str | None
    truncated: bool


@dataclass(frozen=True)
class DataQualityEvidence:
    """Data Workbench quality assertion의 결과와 severity."""

    assertionId: str
    success: bool | None
    severity: str
    assetId: str


@dataclass(frozen=True)
class DataEvidence:
    """Data Workbench 결과 envelope에서 계산 입력과 관련된 근거를 무손실 투영한다."""

    status: str
    requestedAssets: int
    resolvedAssets: int
    succeededPartitions: int
    failedPartitions: int
    assets: tuple[tuple[str, str], ...]
    gaps: tuple[DataGapEvidence, ...]
    partitions: tuple[DataPartitionEvidence, ...]
    qualityAssertions: tuple[DataQualityEvidence, ...]
    catalogSnapshotId: str
    dataSnapshotId: str
    contractHash: str
    lineageRefs: tuple[str, ...]
    executionReceipts: tuple[str, ...]
    materializationReceiptJson: str | None


@dataclass(frozen=True)
class SimulationResult:
    """One deterministic scenario run's result - values + ref/quality/provenance per node (§3).

    Capabilities:
        Carries the scenario's revenue / margin / proforma-FCF paths, the dcf per-share value, and
        a per-node `NodeAudit` (status / provenance / refs / inputsHash / asOf). honest-gap: any
        field that depended on an absent leaf or base metric is None and its node `status` is
        ``"partial"``.

    Fields:
        scenarioName  : the scenario id this run used.
        horizon       : number of forecast years.
        revenuePath   : per-year absolute revenue (None when base revenue absent).
        marginPath    : per-year operating margin (%) - carried from the transfer node frozen input.
        fcfPath       : per-year proforma FCF (None on a proforma gap).
        proformaYears : number of ProFormaYear projections the L2 leaf produced.
        terminalRevenue : the proforma terminal-year revenue (the proforma node value).
        dcfPerShare   : the dcf node's per-share value (None when shares / FCF absent).
        enterpriseValue : the dcf node's enterprise value (PV of FCF + terminal value).
        nodes         : driverId -> NodeAudit (provenance / refs / quality status / asOf).
        asOf          : the run's data vintage.
        latestAsOf    : latest available vintage.
        requestedAsOf : the caller's normalized requested fiscal period.
        quality       : overall ``"ok"`` if every node is ok, else ``"partial"``.
        assumptions   : explicit defaults used by the run.
        warnings      : data limitations and honest-gap reasons.
        dataInputGaps : Data Workbench가 입력과 함께 반환한 completeness/PIT gap.
        dataEvidence  : coverage, asset version, partition seal, quality, receipt 전체 입력 envelope.
    """

    scenarioName: str
    horizon: int
    revenuePath: tuple[float | None, ...] | None
    marginPath: tuple[float, ...] | None
    fcfPath: tuple[float | None, ...] | None
    proformaYears: int
    terminalRevenue: float | None
    dcfPerShare: float | None
    enterpriseValue: float | None
    nodes: dict[str, NodeAudit]
    asOf: str
    latestAsOf: str
    requestedAsOf: str
    quality: str = "ok"
    assumptions: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    lensProducts: dict[str, dict[str, Any]] = field(default_factory=dict)
    assumptionLedger: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    dataSnapshotId: str = ""
    dataCatalogSnapshotId: str = ""
    dataContractHash: str = ""
    dataLineageRefs: tuple[str, ...] = field(default_factory=tuple)
    dataExecutionReceipts: tuple[str, ...] = field(default_factory=tuple)
    dataInputGaps: tuple[str, ...] = field(default_factory=tuple)
    dataEvidence: DataEvidence | None = None


def _dataEvidence(snapshot: dict) -> DataEvidence | None:
    raw = snapshot.get("dataEvidence")
    if not isinstance(raw, dict):
        return None
    rawCoverage = raw.get("coverage")
    coverage = rawCoverage if isinstance(rawCoverage, dict) else {}
    return DataEvidence(
        status=str(raw.get("status", "unknown")),
        requestedAssets=int(coverage.get("requestedAssets", 0)),
        resolvedAssets=int(coverage.get("resolvedAssets", 0)),
        succeededPartitions=int(coverage.get("succeededPartitions", 0)),
        failedPartitions=int(coverage.get("failedPartitions", 0)),
        assets=tuple((str(row[0]), str(row[1])) for row in raw.get("assets", ())),
        gaps=tuple(DataGapEvidence(**row) for row in raw.get("gaps", ())),
        partitions=tuple(DataPartitionEvidence(**row) for row in raw.get("partitions", ())),
        qualityAssertions=tuple(DataQualityEvidence(**row) for row in raw.get("qualityAssertions", ())),
        catalogSnapshotId=str(raw.get("catalogSnapshotId", "")),
        dataSnapshotId=str(raw.get("dataSnapshotId", "")),
        contractHash=str(raw.get("contractHash", "")),
        lineageRefs=tuple(raw.get("lineageRefs", ())),
        executionReceipts=tuple(raw.get("executionReceipts", ())),
        materializationReceiptJson=raw.get("materializationReceiptJson"),
    )


def _audit(driverId: str, nv: NodeValue) -> NodeAudit:
    """Wrap a NodeValue into a NodeAudit, marking status partial on an honest gap."""
    status = "ok" if nv.value is not None else "partial"
    return NodeAudit(
        driverId=driverId,
        status=status,
        provenance=nv.provenance,
        refs=nv.refs,
        inputsHash=nv.inputsHash,
        asOf=nv.asOf,
        latestAsOf=nv.latestAsOf,
    )


def runScenario(
    company: Any,
    *,
    scenario: str = "baseline",
    horizon: int = 3,
    asOf: str | None = None,
    lensBundle: dict[str, Any] | None = None,
) -> SimulationResult:
    """Run one deterministic scenario on a company, end to end (§3 internal driver).

    Capabilities:
        Reads the company's base metrics ONCE into a frozen snapshot, wires the deterministic
        ``macro.path -> rev.path -> proforma -> dcf`` DriverSheet for the named scenario, evaluates
        it with the topological executor, and assembles a `SimulationResult` carrying the
        revenue / margin / FCF paths, the dcf per-share value, and a per-node audit
        (provenance / refs / quality status / inputsHash / asOf). honest-gap: a missing leaf or
        absent base metric leaves the field None and downgrades the node status to ``partial`` -
        never 0. Deterministic by construction: re-running on the same company / scenario yields
        identical per-node `inputsHash`es (no RNG on this path).

    Args:
        company: a `Company` (DART/EDGAR) instance to simulate. Read forward via the L2 finance
            accessors (`_buildFinanceSeries`, `sector`, `sectorParams`).
        scenario: the scenario id - a key of `synth.scenario.getPresetScenarios("KR")` (e.g.
            ``"baseline"``, ``"adverse"``, ``"semiconductor_down"``).
        horizon: number of forecast years. It cannot exceed the selected preset path.
        asOf: explicit fiscal period (YYYY or YYYY-Qn). This is period-scoped PIT, not filing
            receipt-date vintage reconstruction.

    Returns:
        SimulationResult: the scenario's paths + dcf per-share value + per-node audit + overall
        quality status (``"ok"`` / ``"partial"``).

    Raises:
        TypeError: if scenario or horizon has the wrong type.
        ValueError: if scenario, horizon, or asOf is outside its supported domain, or from the
            executor on malformed wiring.

    Example:
        >>> from dartlab.providers.dart.company import Company  # doctest: +SKIP
        >>> r = runScenario(Company("005930"), scenario="baseline")  # doctest: +SKIP
        >>> r.scenarioName, len(r.revenuePath)  # doctest: +SKIP
        ('baseline', 3)

    Guide:
        This is the deterministic path. ``lensBundle`` preserves lens assumptions and scenarios
        as context but never overrides DriverSheet inputs. To compare scenarios, call once per
        scenario over the same company; baseline vs adverse differ only in the macro preset, so a lower
        adverse revenue path is the expected qualitative signal. The result is the audit object -
        read each node's provenance / refs to explain the number.

    When:
        Internally, to compute a deterministic scenario answer for the public `simulate` verb.

    How:
        buildSnapshot (read once) -> buildScenarioSheet -> evaluateSheet -> assemble
        SimulationResult from the four node values.

    SeeAlso:
        - ``dartlab.simulate.registry.buildScenarioSheet``: the node wiring.
        - ``dartlab.simulate.sheet.evaluateSheet``: the deterministic executor.
        - ``dartlab.synth.scenario.getPresetScenarios``: valid scenario ids.

    Requires:
        A constructed `Company`. The proforma node needs a finance series with IS/BS/CF ≥ ~3 years
        for a non-partial result.

    AIContext:
        The output is a deterministic transform of frozen assumptions, not a forecast - always
        surface the scenario id, the per-node provenance/refs, and `asOf`. A ``partial`` quality
        means a data gap (a None field), not a zero value; report the gap, do not impute 0.

    LLM Specifications:
        AntiPatterns:
            - Quoting `dcfPerShare` as a target price - it is a scenario-conditioned transform.
            - Treating a None `revenuePath` as 0 - it is an honest base-revenue gap.
            - Re-running with a different `asOf` and comparing inputsHashes - vintage is part of
              the hash.
        OutputSchema: ``SimulationResult`` (see its field docstring).
        Prerequisites: a `Company` with a finance series.
        Freshness: inherits the company's latest finance period as `asOf`/`latestAsOf`.
        Dataflow: company -> snapshot -> sheet -> evaluateSheet -> SimulationResult.
        TargetMarkets: KR (getPresetScenarios("KR") + KR elasticity); US needs US presets.
    """
    validateScenarioSpec(scenario, horizon)
    snapshot = buildSnapshot(company, asOf=asOf)
    sheet = buildScenarioSheet(snapshot, scenario=scenario, horizon=horizon)
    out = evaluateSheet(sheet)

    macroId = f"{DRIVER_MACRO}@{scenario}#all"
    revId = f"{DRIVER_REV}@{scenario}#all"
    proformaId = f"{DRIVER_PROFORMA}@{scenario}#all"
    dcfId = f"{DRIVER_DCF}@{scenario}#all"

    revNv = out[revId]
    proformaNv = out[proformaId]
    dcfNv = out[dcfId]

    # margin path rides in the rev node's frozen input, which is not surfaced on the NodeValue;
    # recompute it deterministically from the same snapshot transfer for the result (the audit
    # node still carries the authoritative provenance/refs/hash).
    marginPath = _marginPathFromSnapshot(snapshot, scenario, horizon)

    nodes = {
        DRIVER_MACRO: _audit(DRIVER_MACRO, out[macroId]),
        DRIVER_REV: _audit(DRIVER_REV, revNv),
        DRIVER_PROFORMA: _audit(DRIVER_PROFORMA, proformaNv),
        DRIVER_DCF: _audit(DRIVER_DCF, dcfNv),
    }
    assumptions = tuple(snapshot.get("assumptions", ()))
    snapshotWarnings = tuple(snapshot.get("warnings", ()))
    dataInputGaps = tuple(snapshot.get("dataInputGaps", ()))
    dataEvidence = _dataEvidence(snapshot)
    dataEvidencePartial = dataEvidence is not None and (
        dataEvidence.status != "ok"
        or dataEvidence.failedPartitions > 0
        or any(assertion.success is not True for assertion in dataEvidence.qualityAssertions)
        or any(partition.truncated for partition in dataEvidence.partitions)
    )
    quality = (
        "ok"
        if all(a.status == "ok" for a in nodes.values())
        and not assumptions
        and not snapshotWarnings
        and not dataInputGaps
        and not dataEvidencePartial
        else "partial"
    )

    warnings: list[str] = list(snapshotWarnings)
    warnings.extend(f"data input gap - {gap}" for gap in dataInputGaps)
    if snapshot.get("baseRevenue") is None:
        warnings.append("base revenue absent - scenario path unavailable (honest-gap)")
    if snapshot.get("shares") in (None, 0):
        warnings.append("shares unavailable - dcf per-share unavailable (honest-gap)")

    products = lensBundle.get("products") if isinstance(lensBundle, dict) else {}
    if not isinstance(products, dict):
        products = {}
    assumptionLedger = _assumptionLedger(assumptions, products)

    return SimulationResult(
        scenarioName=scenario,
        horizon=horizon,
        revenuePath=revNv.vector,
        marginPath=marginPath,
        fcfPath=proformaNv.vector,
        proformaYears=len(proformaNv.vector) if proformaNv.vector else 0,
        terminalRevenue=proformaNv.value,
        dcfPerShare=dcfNv.value,
        enterpriseValue=dcfNv.vector[0] if dcfNv.vector else None,
        nodes=nodes,
        asOf=snapshot["asOf"],
        latestAsOf=snapshot["latestAsOf"],
        requestedAsOf=snapshot.get("requestedAsOf", snapshot["asOf"]),
        quality=quality,
        assumptions=assumptions,
        warnings=tuple(warnings),
        lensProducts=products,
        assumptionLedger=assumptionLedger,
        dataSnapshotId=str(snapshot.get("dataSnapshotId", "")),
        dataCatalogSnapshotId=str(snapshot.get("dataCatalogSnapshotId", "")),
        dataContractHash=str(snapshot.get("dataContractHash", "")),
        dataLineageRefs=tuple(snapshot.get("dataLineageRefs", ())),
        dataExecutionReceipts=tuple(snapshot.get("dataExecutionReceipts", ())),
        dataInputGaps=dataInputGaps,
        dataEvidence=dataEvidence,
    )


def _assumptionLedger(
    deterministicAssumptions: tuple[str, ...],
    products: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """시뮬레이션 가정과 렌즈 맥락을 변경 없이 한 원장에 투영한다.

    렌즈의 가정과 시나리오는 설명 맥락이다. 결정론 DriverSheet 입력을
    덮어쓰지 않았음을 ``appliedToDriverSheet=False``로 명시한다.
    """
    rows: list[dict[str, Any]] = [
        {
            "source": "simulate",
            "kind": "deterministicAssumption",
            "id": value,
            "appliedToDriverSheet": True,
        }
        for value in deterministicAssumptions
    ]
    for engine, product in products.items():
        if not isinstance(product, dict):
            continue
        for assumption in product.get("assumptions") or []:
            if isinstance(assumption, dict):
                rows.append(
                    {
                        "source": engine,
                        "kind": "lensAssumptionContext",
                        "appliedToDriverSheet": False,
                        "value": assumption,
                    }
                )
        for scenario in product.get("scenarios") or []:
            if isinstance(scenario, dict):
                rows.append(
                    {
                        "source": engine,
                        "kind": "lensScenarioContext",
                        "appliedToDriverSheet": False,
                        "value": scenario,
                    }
                )
    return tuple(rows)


def _marginPathFromSnapshot(snapshot: dict, scenario: str, horizon: int) -> tuple[float, ...] | None:
    """Deterministically recompute the margin path for the result (same transfer as the rev node).

    The rev node carries the margin path in its frozen input (hashed, audited), but the executor
    does not surface frozen inputs on `NodeValue`. The result recomputes it from the same snapshot
    + preset via the same transfer, so the number shown matches the audited node byte-for-byte.
    Returns None on an honest base-revenue gap.
    """
    from dartlab.simulate.transfer import transferRevenuePath
    from dartlab.synth.scenario import getPresetScenarios

    baseRevenue = snapshot.get("baseRevenue")
    if baseRevenue is None or snapshot.get("parameterVintageStatus", "available") != "available":
        return None
    baseMargin = snapshot["baseMargin"] if snapshot.get("baseMargin") is not None else 10.0
    presets = getPresetScenarios("KR")
    sc = presets[scenario]
    _rev, marginPath, _wacc = transferRevenuePath(
        baseRevenue,
        baseMargin,
        list(sc.gdpGrowth[:horizon]),
        list(sc.interestRate[:horizon]),
        list(sc.krwUsd[:horizon]),
        snapshot["elasticity"],
        snapshot["baseWacc"],
    )
    return tuple(marginPath)
