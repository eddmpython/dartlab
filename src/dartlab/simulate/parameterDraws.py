"""Typed, PIT-aware provenance receipts for joint path parameter draws.

The receipt in this module documents exact draw content and its data vintage.
It is deliberately not an admission certificate: a local SHA digest proves
content consistency, not issuer authority. Policy recommendation therefore
remains fail-closed until an independently trusted evidence registry exists.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, replace
from hashlib import sha256
from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:
    from dartlab.simulate.world import ScenarioPath

_DISTRIBUTION_KINDS = {"jointEmpirical", "jointParametric", "stressEnvelope"}
_REVISION_POLICIES = {"asKnown", "latestRetained", "revisedHistory", "synthetic", "explicitAssumption"}
_COVERAGE_KINDS = {"asOfExact", "latestOnly", "periodOnly", "synthetic"}
_RULES = (
    "parameter-draw-provenance-v1: exact joint draw set, generator, seed, fit cutoff, "
    "knowledge cutoff, history status, and distribution artifact are content-bound; "
    "receipt is documented provenance, not independent admission"
)


class ParameterDrawError(ValueError):
    """Raised when parameter draw provenance is incomplete or inconsistent."""


@dataclass(frozen=True)
class ParameterDrawSetReceipt:
    """Document the exact joint parameter draw set and the vintage that produced it."""

    receiptId: str
    schemaVersion: str
    status: str
    distributionId: str
    distributionKind: str
    generatorVersion: str
    seed: int
    parameterNames: tuple[str, ...]
    parameterUnits: tuple[tuple[str, str], ...]
    parameterSchemaHash: str
    frequency: str
    stepSpan: int
    maxAdmittedStep: int
    fitThrough: str
    availableAt: str
    knowledgeAsOf: str
    revisionPolicy: str
    coverage: str
    distributionArtifactHash: str
    drawSetHash: str
    nDraws: int
    rules: str


def _hash(payload) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(raw.encode("utf-8")).hexdigest()


def _dateText(value: str) -> str:
    text = str(value).replace("-", "")[:8]
    if len(text) != 8 or not text.isdigit():
        raise ParameterDrawError(f"invalid parameter draw date: {value}")
    return text


def _validDigest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value.lower())


def _drawContract(paths: tuple[ScenarioPath, ...]) -> tuple[tuple[str, ...], str]:
    if not paths:
        raise ParameterDrawError("parameter draw receipt needs at least one path")
    if len({path.pathId for path in paths}) != len(paths):
        raise ParameterDrawError("parameter draw paths must have unique identifiers")
    parameterSets = {tuple(sorted(path.parameterDraws)) for path in paths}
    if len(parameterSets) != 1 or not next(iter(parameterSets), ()):
        raise ParameterDrawError("joint parameter draws must share the same parameter names")
    names = next(iter(parameterSets))
    rows = []
    for path in paths:
        values = {}
        for name in names:
            value = float(path.parameterDraws[name])
            if not math.isfinite(value):
                raise ParameterDrawError(f"parameter draw is not finite: {path.pathId}.{name}")
            values[name] = value
        rows.append(
            {
                "pathId": path.pathId,
                "draws": values,
                "weight": path.weight,
                "weightKind": path.weightKind,
            }
        )
    return names, _hash({"draws": rows})


def _receiptPayload(receipt: ParameterDrawSetReceipt) -> dict:
    return {
        "schemaVersion": receipt.schemaVersion,
        "status": receipt.status,
        "distributionId": receipt.distributionId,
        "distributionKind": receipt.distributionKind,
        "generatorVersion": receipt.generatorVersion,
        "seed": receipt.seed,
        "parameterNames": receipt.parameterNames,
        "parameterUnits": receipt.parameterUnits,
        "parameterSchemaHash": receipt.parameterSchemaHash,
        "frequency": receipt.frequency,
        "stepSpan": receipt.stepSpan,
        "maxAdmittedStep": receipt.maxAdmittedStep,
        "fitThrough": receipt.fitThrough,
        "availableAt": receipt.availableAt,
        "knowledgeAsOf": receipt.knowledgeAsOf,
        "revisionPolicy": receipt.revisionPolicy,
        "coverage": receipt.coverage,
        "distributionArtifactHash": receipt.distributionArtifactHash,
        "drawSetHash": receipt.drawSetHash,
        "nDraws": receipt.nDraws,
        "rules": receipt.rules,
    }


def issueParameterDrawSetReceipt(
    paths: tuple[ScenarioPath, ...],
    *,
    distributionId: str,
    distributionKind: str,
    generatorVersion: str,
    seed: int,
    parameterUnits: Mapping[str, str],
    frequency: str,
    stepSpan: int,
    maxAdmittedStep: int,
    fitThrough: str,
    availableAt: str,
    knowledgeAsOf: str,
    revisionPolicy: str,
    coverage: str,
    distributionArtifactHash: str,
) -> ParameterDrawSetReceipt:
    """Issue a non-authoritative receipt for one exact joint draw ensemble."""

    if not distributionId or not generatorVersion:
        raise ParameterDrawError("parameter draw receipt needs distribution and generator identifiers")
    if distributionKind not in _DISTRIBUTION_KINDS:
        raise ParameterDrawError(f"unknown parameter distribution kind: {distributionKind}")
    if int(seed) < 0:
        raise ParameterDrawError("parameter draw seed must be nonnegative")
    if not frequency or stepSpan < 1 or maxAdmittedStep < 1:
        raise ParameterDrawError("parameter draw receipt needs a valid step contract and horizon")
    fitCutoff = _dateText(fitThrough)
    availableCutoff = _dateText(availableAt)
    knowledgeCutoff = _dateText(knowledgeAsOf)
    if fitCutoff > availableCutoff:
        raise ParameterDrawError("parameter distribution fitThrough is newer than availableAt")
    if availableCutoff > knowledgeCutoff:
        raise ParameterDrawError("parameter distribution evidence is newer than knowledgeAsOf")
    if revisionPolicy not in _REVISION_POLICIES or coverage not in _COVERAGE_KINDS:
        raise ParameterDrawError("parameter draw receipt needs valid revision and coverage contracts")
    if not _validDigest(distributionArtifactHash):
        raise ParameterDrawError("parameter distribution artifact needs a content digest")
    parameterNames, drawSetHash = _drawContract(paths)
    cleanUnits = tuple(sorted((str(name), str(unit)) for name, unit in parameterUnits.items()))
    if tuple(name for name, _ in cleanUnits) != parameterNames or any(not unit for _, unit in cleanUnits):
        raise ParameterDrawError("parameter draw units must exactly cover the parameter names")
    if any(
        path.frequency != frequency or path.stepSpan != stepSpan or len(path.steps) > maxAdmittedStep for path in paths
    ):
        raise ParameterDrawError("parameter draw receipt step contract mismatch")
    parameterSchemaHash = _hash({"namesAndUnits": cleanUnits})
    provisional = ParameterDrawSetReceipt(
        receiptId="",
        schemaVersion="parameter-draw-receipt-v1",
        status="documented" if revisionPolicy == "asKnown" and coverage == "asOfExact" else "retrospectiveOnly",
        distributionId=distributionId,
        distributionKind=distributionKind,
        generatorVersion=generatorVersion,
        seed=int(seed),
        parameterNames=parameterNames,
        parameterUnits=cleanUnits,
        parameterSchemaHash=parameterSchemaHash,
        frequency=frequency,
        stepSpan=stepSpan,
        maxAdmittedStep=maxAdmittedStep,
        fitThrough=fitCutoff,
        availableAt=availableCutoff,
        knowledgeAsOf=knowledgeCutoff,
        revisionPolicy=revisionPolicy,
        coverage=coverage,
        distributionArtifactHash=distributionArtifactHash.lower(),
        drawSetHash=drawSetHash,
        nDraws=len(paths),
        rules=_RULES,
    )
    return replace(provisional, receiptId=_hash(_receiptPayload(provisional)))


def validateParameterDrawSetReceipt(
    paths: tuple[ScenarioPath, ...],
    receipt: ParameterDrawSetReceipt,
    *,
    decisionAsOf: str | None = None,
) -> None:
    """Recompute the receipt digest, exact draw set, and PIT ordering."""

    if receipt.receiptId != _hash(_receiptPayload(receipt)):
        raise ParameterDrawError("parameter draw receipt digest mismatch")
    if receipt.schemaVersion != "parameter-draw-receipt-v1" or receipt.rules != _RULES:
        raise ParameterDrawError("parameter draw receipt protocol mismatch")
    if receipt.status not in {"documented", "retrospectiveOnly"}:
        raise ParameterDrawError("parameter draw receipt has an invalid status")
    if receipt.distributionKind not in _DISTRIBUTION_KINDS:
        raise ParameterDrawError("parameter draw receipt has an invalid distribution kind")
    if not _validDigest(receipt.distributionArtifactHash):
        raise ParameterDrawError("parameter distribution artifact needs a content digest")
    names, drawSetHash = _drawContract(paths)
    if names != receipt.parameterNames or len(paths) != receipt.nDraws:
        raise ParameterDrawError("parameter draw receipt contract mismatch")
    if tuple(
        name for name, unit in receipt.parameterUnits if unit
    ) != receipt.parameterNames or receipt.parameterSchemaHash != _hash({"namesAndUnits": receipt.parameterUnits}):
        raise ParameterDrawError("parameter draw unit schema mismatch")
    if drawSetHash != receipt.drawSetHash:
        raise ParameterDrawError("parameter draw set hash mismatch")
    if receipt.stepSpan < 1 or receipt.maxAdmittedStep < 1 or not receipt.frequency:
        raise ParameterDrawError("parameter draw receipt has an invalid step contract")
    if any(
        path.frequency != receipt.frequency
        or path.stepSpan != receipt.stepSpan
        or len(path.steps) > receipt.maxAdmittedStep
        for path in paths
    ):
        raise ParameterDrawError("parameter draw receipt step contract mismatch")
    if _dateText(receipt.fitThrough) > _dateText(receipt.availableAt):
        raise ParameterDrawError("parameter distribution fitThrough is newer than availableAt")
    if _dateText(receipt.availableAt) > _dateText(receipt.knowledgeAsOf):
        raise ParameterDrawError("parameter distribution evidence is newer than knowledgeAsOf")
    if receipt.revisionPolicy not in _REVISION_POLICIES or receipt.coverage not in _COVERAGE_KINDS:
        raise ParameterDrawError("parameter draw receipt has invalid revision or coverage")
    if receipt.status == "documented" and (receipt.revisionPolicy != "asKnown" or receipt.coverage != "asOfExact"):
        raise ParameterDrawError("documented parameter draws need exact as-known history")
    for path in paths:
        if not path.knowledgeAsOf:
            raise ParameterDrawError(f"parameter draws need a path knowledge cutoff: {path.pathId}")
        if _dateText(receipt.knowledgeAsOf) > _dateText(path.knowledgeAsOf):
            raise ParameterDrawError(f"parameter draw receipt is newer than path: {path.pathId}")
    if decisionAsOf is not None and _dateText(receipt.knowledgeAsOf) > _dateText(decisionAsOf):
        raise ParameterDrawError("parameter draw receipt is newer than decision state")


def bindParameterDrawSetReceipt(
    paths: tuple[ScenarioPath, ...],
    receipt: ParameterDrawSetReceipt,
) -> tuple[ScenarioPath, ...]:
    """Attach a validated shared receipt to every path in the exact draw set."""

    validateParameterDrawSetReceipt(paths, receipt)
    return tuple(replace(path, parameterDrawReceipt=receipt) for path in paths)
