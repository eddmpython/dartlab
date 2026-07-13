"""Translate annual macro innovations into audited company financial shocks."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from hashlib import sha256
from typing import Mapping

from dartlab.simulate.world import (
    LawSpec,
    ScenarioPath,
    StrategySpec,
    VariableSpec,
    WorldModel,
    WorldState,
    bindAdmittedPathContent,
    simulateWorld,
)


@dataclass(frozen=True)
class FinancialBridgeAudit:
    """거시 경로와 회사 재무 충격 사이의 변환 근거와 승격 상태를 보존한다."""

    bridgeHash: str
    lawId: str
    lawCertificateId: str
    sourcePathCertificates: tuple[str, ...]
    validationStatus: str
    maxAdmittedStep: int
    warnings: tuple[str, ...]
    sourcePathContentHashes: tuple[str, ...]
    knowledgeAsOf: str
    historyStatus: str


@dataclass(frozen=True)
class FinancialBridgeResult:
    """financial world가 직접 소비할 경로와 변환 감사기록을 반환한다."""

    paths: tuple[ScenarioPath, ...]
    audit: FinancialBridgeAudit


def _hash(payload) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(raw.encode("utf-8")).hexdigest()


def _cleanCoefficients(values: Mapping[str, float], factors: set[str], label: str) -> dict[str, float]:
    unknown = set(values) - factors
    if unknown:
        raise ValueError(f"{label} has unknown factors: {sorted(unknown)}")
    clean = {str(name): float(value) for name, value in values.items()}
    if any(not math.isfinite(value) for value in clean.values()):
        raise ValueError(f"{label} must be finite")
    return clean


def buildFinancialBridgeLaw(
    *,
    factorUnits: Mapping[str, str],
    demandLogCoefficients: Mapping[str, float],
    marginChangeCoefficients: Mapping[str, float],
    debtRateChangeCoefficients: Mapping[str, float],
    baseDebtRate: float,
    evidenceKind: str = "explicitAssumption",
    status: str = "active",
) -> LawSpec:
    """거시 혁신을 연간 수요, 마진 증분, 차입금리 상태로 옮기는 법칙을 만든다."""

    factors = set(factorUnits)
    if not factors or any(not str(unit) for unit in factorUnits.values()):
        raise ValueError("financial bridge needs explicit factor units")
    demand = _cleanCoefficients(demandLogCoefficients, factors, "demand coefficients")
    margin = _cleanCoefficients(marginChangeCoefficients, factors, "margin coefficients")
    debt = _cleanCoefficients(debtRateChangeCoefficients, factors, "debt-rate coefficients")
    baseRate = float(baseDebtRate)
    if not math.isfinite(baseRate) or baseRate < 0 or baseRate > 1:
        raise ValueError("baseDebtRate must be in [0, 1]")
    orderedFactors = tuple(sorted(factors))

    def bridge(ctx):
        """한 기간의 거시 혁신을 회사 재무 충격 세 값으로 변환한다."""

        logGrowth = sum(demand.get(factor, 0.0) * ctx.shocks[factor] for factor in orderedFactors)
        marginChange = sum(margin.get(factor, 0.0) * ctx.shocks[factor] for factor in orderedFactors)
        rateChange = sum(debt.get(factor, 0.0) * ctx.shocks[factor] for factor in orderedFactors)
        return {
            "demandGrowth": math.expm1(logGrowth),
            "marginChange": marginChange,
            "debtRate": min(1.0, max(0.0, ctx.prior["debtRate"] + rateChange)),
        }

    return LawSpec(
        lawId="macroToFinancialShock",
        outputs=("demandGrowth", "marginChange", "debtRate"),
        priorInputs=("debtRate",),
        shockInputs=orderedFactors,
        evidenceKind=evidenceKind,
        provenance="simulate.financialBridge:buildFinancialBridgeLaw",
        version="1",
        status=status,
        parameters={
            "factorUnits": json.dumps(dict(sorted(factorUnits.items())), sort_keys=True),
            "demandLogCoefficients": json.dumps(dict(sorted(demand.items())), sort_keys=True),
            "marginChangeCoefficients": json.dumps(dict(sorted(margin.items())), sort_keys=True),
            "debtRateChangeCoefficients": json.dumps(dict(sorted(debt.items())), sort_keys=True),
            "baseDebtRate": baseRate,
        },
        fn=bridge,
    )


def bridgeFinancialPaths(paths: tuple[ScenarioPath, ...], law: LawSpec) -> FinancialBridgeResult:
    """동일한 연간 거시 경로를 인증된 회사 재무 충격 경로로 변환한다."""

    if not paths:
        raise ValueError("financial bridge needs at least one source path")
    factorUnits = json.loads(str(law.parameters.get("factorUnits", "{}")))
    baseDebtRate = float(law.parameters.get("baseDebtRate", float("nan")))
    variables = tuple(VariableSpec(name, unit, "shock") for name, unit in sorted(factorUnits.items())) + (
        VariableSpec("demandGrowth", "ratioChangePerYear", "metric", lower=-1.0),
        VariableSpec("marginChange", "ratioPointChangePerYear", "metric", lower=-1.0, upper=1.0),
        VariableSpec("debtRate", "ratio", "state", lower=0.0, upper=1.0),
    )
    model = WorldModel(
        "company-financial-shock-bridge",
        "1",
        variables,
        (),
        (law,),
        stepFrequency="year",
    )
    horizon = len(paths[0].steps)
    strategy = StrategySpec("bridge", ({},) * horizon, isBaseline=True)
    sourceCutoffs = {path.knowledgeAsOf for path in paths}
    sourceHistoryStatuses = {path.historyStatus for path in paths}
    sourceKnowledgeAsOf = next(iter(sourceCutoffs)) if len(sourceCutoffs) == 1 else ""
    sourceHistoryStatus = next(iter(sourceHistoryStatuses)) if len(sourceHistoryStatuses) == 1 else "mixed"
    run = simulateWorld(
        model,
        WorldState(
            {"debtRate": baseDebtRate},
            asOf=sourceKnowledgeAsOf,
            knowledgeAsOf=sourceKnowledgeAsOf,
            decisionAsOf=sourceKnowledgeAsOf,
        ),
        paths,
        (strategy,),
    )
    traces = {trace.pathId: trace for trace in run.traces}
    lawCertificate = law.certificate
    admitted = (
        all(path.validationStatus == "admitted" for path in paths)
        and law.status == "active"
        and lawCertificate is not None
        and lawCertificate.status == "admitted"
        and sourceHistoryStatus == "asKnown"
        and bool(sourceKnowledgeAsOf)
    )
    validationStatus = "admitted" if admitted else "retrospectiveOnly"
    maxAdmittedStep = min(lawCertificate.maxAdmittedStep, *(path.maxAdmittedStep for path in paths)) if admitted else 0
    sourceCertificates = tuple(sorted({path.certificateId for path in paths if path.certificateId}))
    sourceContentHashes = tuple(sorted({path.admissionContentHash for path in paths if path.admissionContentHash}))
    combinedCertificate = (
        _hash(
            {
                "lawCertificate": lawCertificate.certificateId,
                "sourceCertificates": sourceCertificates,
                "sourceContentHashes": sourceContentHashes,
                "sourceKnowledgeAsOf": sourceKnowledgeAsOf,
                "sourceHistoryStatus": sourceHistoryStatus,
                "frequency": "year",
                "stepSpan": 1,
                "horizon": horizon,
            }
        )
        if admitted
        else ""
    )
    bridged: list[ScenarioPath] = []
    for source in paths:
        trace = traces[source.pathId]
        steps = tuple(
            {
                "demandGrowth": step.after["demandGrowth"],
                "marginChange": step.after["marginChange"],
                "debtRate": step.after["debtRate"],
            }
            for step in trace.steps
        )
        bridged.append(
            ScenarioPath(
                pathId=f"financial-{source.pathId}",
                steps=steps,
                weight=source.weight,
                weightKind=source.weightKind,
                refs=source.refs + (law.provenance,),
                frequency="year",
                stepSpan=1,
                certificateId=combinedCertificate,
                validationStatus=validationStatus,
                maxAdmittedStep=maxAdmittedStep,
                knowledgeAsOf=sourceKnowledgeAsOf,
                historyStatus=sourceHistoryStatus,
            )
        )
    if admitted:
        bridged = list(bindAdmittedPathContent(tuple(bridged)))
    warnings = []
    if not admitted:
        warnings.append(f"bridgeEvidence:{law.evidenceKind}")
    payload = [{"pathId": path.pathId, "steps": [dict(step) for step in path.steps]} for path in bridged]
    audit = FinancialBridgeAudit(
        bridgeHash=_hash(payload),
        lawId=law.lawId,
        lawCertificateId=lawCertificate.certificateId if lawCertificate is not None else "",
        sourcePathCertificates=sourceCertificates,
        validationStatus=validationStatus,
        maxAdmittedStep=maxAdmittedStep,
        warnings=tuple(warnings),
        sourcePathContentHashes=sourceContentHashes,
        knowledgeAsOf=sourceKnowledgeAsOf,
        historyStatus=sourceHistoryStatus,
    )
    return FinancialBridgeResult(tuple(bridged), audit)
