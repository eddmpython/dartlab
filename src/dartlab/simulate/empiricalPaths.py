"""PIT-frozen joint moving-block paths with explicit admission evidence."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from hashlib import sha256

import numpy as np
import polars as pl

from dartlab.simulate.world import ScenarioPath

GENERATOR_VERSION = "joint-moving-block-v1"
ADMISSION_RULES = (
    "path-admission-v1: every required factor and step needs n>=minOrigins, abs(cov90-0.90)<=0.10, and crps<crpsCarry"
)


class EmpiricalPathError(ValueError):
    """Raised when an empirical path set cannot be built honestly."""


@dataclass(frozen=True)
class PathVariable:
    """Bind one shock identifier to a source column and explicit unit."""

    variableId: str
    sourceColumn: str
    unit: str


@dataclass(frozen=True)
class PathMeasureCertificate:
    """Bind an admitted horizon to a generator, grid, variables, and curves."""

    certificateId: str
    status: str
    generatorVersion: str
    frequency: str
    stepSpan: int
    variables: tuple[tuple[str, str], ...]
    knowledgeAsOf: str
    historyStatus: str
    maxAdmittedStep: int
    nOrigins: int
    calibrationHash: str
    rules: str


@dataclass(frozen=True)
class EmpiricalPathAudit:
    """Describe the frozen input and all resampling choices."""

    pathSetHash: str
    inputHash: str
    generatorVersion: str
    method: str
    knowledgeAsOf: str
    historyStatus: str
    frequency: str
    stepSpan: int
    variables: tuple[PathVariable, ...]
    observationCount: int
    eventStart: str
    eventEnd: str
    pathCount: int
    horizon: int
    blockLength: int
    seed: int
    weightLabel: str
    validationStatus: str
    certificateId: str
    maxAdmittedStep: int
    sampledBlocks: tuple[tuple[tuple[str, str], ...], ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class EmpiricalPathSet:
    """A common path ensemble and its audit record."""

    paths: tuple[ScenarioPath, ...]
    audit: EmpiricalPathAudit


def _hash(payload) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(raw.encode("utf-8")).hexdigest()


def _dateText(value: str) -> str:
    text = str(value).replace("-", "")[:8]
    if len(text) != 8 or not text.isdigit():
        raise EmpiricalPathError(f"invalid date: {value}")
    return text


def _variableKey(variables: tuple[PathVariable, ...]) -> tuple[tuple[str, str], ...]:
    return tuple((variable.variableId, variable.unit) for variable in variables)


def issuePathMeasureCertificate(
    curves: pl.DataFrame,
    variables: tuple[PathVariable, ...],
    *,
    knowledgeAsOf: str,
    frequency: str,
    stepSpan: int = 1,
    historyStatus: str,
    minOrigins: int = 20,
    coverageTolerance: float = 0.10,
) -> PathMeasureCertificate:
    """Convert complete OOS curves into an explicit last admitted step."""

    required = {"factor", "h", "cov90", "crps", "crpsCarry", "n"}
    if not required.issubset(curves.columns):
        raise EmpiricalPathError(f"calibration curves missing columns: {sorted(required - set(curves.columns))}")
    if stepSpan < 1 or not frequency:
        raise EmpiricalPathError("invalid certificate step contract")
    factors = tuple(variable.variableId for variable in variables)
    if not factors or len(set(factors)) != len(factors):
        raise EmpiricalPathError("path variables must be unique")
    clean = curves.filter(pl.col("factor").is_in(list(factors))).sort(["h", "factor"])
    maxObserved = int(clean["h"].max()) if clean.height else 0
    maxAdmitted = 0
    for step in range(1, maxObserved + 1):
        rows = clean.filter(pl.col("h") == step)
        if set(rows["factor"].to_list()) != set(factors):
            break
        passed = all(
            int(row["n"]) >= minOrigins
            and abs(float(row["cov90"]) - 0.90) <= coverageTolerance
            and float(row["crps"]) < float(row["crpsCarry"])
            for row in rows.iter_rows(named=True)
        )
        if not passed:
            break
        maxAdmitted = step
    status = "admitted" if historyStatus == "asKnown" and maxAdmitted >= 1 else "rejected"
    curvePayload = clean.to_dicts()
    calibrationHash = _hash(curvePayload)
    payload = {
        "status": status,
        "generatorVersion": GENERATOR_VERSION,
        "frequency": frequency,
        "stepSpan": stepSpan,
        "variables": _variableKey(variables),
        "knowledgeAsOf": _dateText(knowledgeAsOf),
        "historyStatus": historyStatus,
        "maxAdmittedStep": maxAdmitted,
        "minOrigins": minOrigins,
        "coverageTolerance": coverageTolerance,
        "calibrationHash": calibrationHash,
        "rules": ADMISSION_RULES,
    }
    return PathMeasureCertificate(
        certificateId=_hash(payload),
        status=status,
        generatorVersion=GENERATOR_VERSION,
        frequency=frequency,
        stepSpan=stepSpan,
        variables=_variableKey(variables),
        knowledgeAsOf=_dateText(knowledgeAsOf),
        historyStatus=historyStatus,
        maxAdmittedStep=maxAdmitted,
        nOrigins=int(clean["n"].min()) if clean.height else 0,
        calibrationHash=calibrationHash,
        rules=ADMISSION_RULES,
    )


def _validateCertificate(
    certificate: PathMeasureCertificate,
    variables: tuple[PathVariable, ...],
    *,
    frequency: str,
    stepSpan: int,
    horizon: int,
    historyStatus: str,
) -> None:
    if certificate.status != "admitted":
        raise EmpiricalPathError("path certificate is not admitted")
    if certificate.generatorVersion != GENERATOR_VERSION:
        raise EmpiricalPathError("path certificate generator mismatch")
    if certificate.frequency != frequency or certificate.stepSpan != stepSpan:
        raise EmpiricalPathError("path certificate step contract mismatch")
    if certificate.historyStatus != historyStatus:
        raise EmpiricalPathError("path certificate history status mismatch")
    if certificate.variables != _variableKey(variables):
        raise EmpiricalPathError("path certificate variable or unit mismatch")
    if certificate.maxAdmittedStep < horizon:
        raise EmpiricalPathError("requested horizon exceeds maxAdmittedStep")


def buildJointBlockPaths(
    panel: pl.DataFrame,
    variables: tuple[PathVariable, ...],
    *,
    knowledgeAsOf: str,
    frequency: str,
    stepSpan: int = 1,
    horizon: int,
    pathCount: int,
    blockLength: int,
    seed: int,
    historyStatus: str = "revisedHistory",
    minObservations: int = 30,
    certificate: PathMeasureCertificate | None = None,
    refs: tuple[str, ...] = (),
) -> EmpiricalPathSet:
    """Build common joint paths from only observations available by the cutoff."""

    if not variables or len({v.variableId for v in variables}) != len(variables):
        raise EmpiricalPathError("path variable identifiers must be unique")
    if len({v.sourceColumn for v in variables}) != len(variables):
        raise EmpiricalPathError("path source columns must be unique")
    if any(not variable.unit for variable in variables):
        raise EmpiricalPathError("every path variable needs a unit")
    required = {"eventTime", "availableAt", *(variable.sourceColumn for variable in variables)}
    if not required.issubset(panel.columns):
        raise EmpiricalPathError(f"panel missing columns: {sorted(required - set(panel.columns))}")
    if min(horizon, pathCount, blockLength, stepSpan, minObservations) < 1 or not frequency:
        raise EmpiricalPathError("path dimensions and step contract must be positive")
    cutoff = _dateText(knowledgeAsOf)
    dated = panel.with_columns(
        pl.col("eventTime").cast(pl.Utf8).str.replace_all("-", "").str.slice(0, 8).alias("__event"),
        pl.col("availableAt").cast(pl.Utf8).str.replace_all("-", "").str.slice(0, 8).alias("__available"),
    )
    malformed = dated.filter(
        (pl.col("__event").str.len_chars() != 8)
        | (pl.col("__available").str.len_chars() != 8)
        | ~pl.col("__event").str.contains(r"^\d{8}$")
        | ~pl.col("__available").str.contains(r"^\d{8}$")
    )
    if malformed.height:
        raise EmpiricalPathError("panel contains malformed eventTime or availableAt")
    frozen = (
        dated.filter((pl.col("__event") <= cutoff) & (pl.col("__available") <= cutoff))
        .sort(["__event", "__available"])
        .unique(subset=["__event"], keep="last", maintain_order=True)
        .sort("__event")
    )
    valueCols = [variable.sourceColumn for variable in variables]
    complete = frozen.drop_nulls(valueCols)
    dropped = frozen.height - complete.height
    for column in valueCols:
        values = complete[column].cast(pl.Float64, strict=False)
        if values.null_count() or any(not math.isfinite(float(value)) for value in values):
            raise EmpiricalPathError(f"non-finite path variable: {column}")
        complete = complete.with_columns(values.alias(column))
    if complete.height < max(minObservations, blockLength):
        raise EmpiricalPathError(f"insufficient joint support: {complete.height} < {max(minObservations, blockLength)}")
    if certificate is not None:
        _validateCertificate(
            certificate,
            variables,
            frequency=frequency,
            stepSpan=stepSpan,
            horizon=horizon,
            historyStatus=historyStatus,
        )
    validationStatus = "admitted" if certificate is not None else "retrospectiveOnly"
    certificateId = certificate.certificateId if certificate is not None else ""
    maxAdmittedStep = certificate.maxAdmittedStep if certificate is not None else 0
    selected = complete.select("__event", "__available", *valueCols)
    inputRows = selected.to_dicts()
    inputHash = _hash(inputRows)
    dates = selected["__event"].to_list()
    matrix = selected.select(valueCols).to_numpy()
    rng = np.random.default_rng(int(seed))
    paths: list[ScenarioPath] = []
    sampledBlocks: list[tuple[tuple[str, str], ...]] = []
    for pathIndex in range(pathCount):
        indices: list[int] = []
        blocks: list[tuple[str, str]] = []
        while len(indices) < horizon:
            take = min(blockLength, horizon - len(indices))
            start = int(rng.integers(0, complete.height - blockLength + 1))
            indices.extend(range(start, start + take))
            blocks.append((dates[start], dates[start + take - 1]))
        steps = tuple(
            {
                variable.variableId: float(matrix[rowIndex, variableIndex])
                for variableIndex, variable in enumerate(variables)
            }
            for rowIndex in indices
        )
        sampleHash = _hash({"indices": indices, "inputHash": inputHash})[:12]
        pathRefs = tuple(refs) + tuple(f"sourceBlock:{start}:{end}" for start, end in blocks)
        paths.append(
            ScenarioPath(
                f"joint-mbb-{seed}-{pathIndex:05d}-{sampleHash}",
                steps,
                weight=1.0 / pathCount,
                weightKind="resampled",
                refs=pathRefs,
                frequency=frequency,
                stepSpan=stepSpan,
                certificateId=certificateId,
                validationStatus=validationStatus,
                maxAdmittedStep=maxAdmittedStep,
            )
        )
        sampledBlocks.append(tuple(blocks))
    pathPayload = [
        {
            "pathId": path.pathId,
            "steps": [dict(step) for step in path.steps],
            "refs": path.refs,
            "frequency": path.frequency,
            "stepSpan": path.stepSpan,
            "validationStatus": path.validationStatus,
            "certificateId": path.certificateId,
        }
        for path in paths
    ]
    warnings = [f"historyStatus:{historyStatus}"]
    if dropped:
        warnings.append(f"droppedIncompleteJointRows:{dropped}")
    audit = EmpiricalPathAudit(
        pathSetHash=_hash(pathPayload),
        inputHash=inputHash,
        generatorVersion=GENERATOR_VERSION,
        method="jointMovingBlockBootstrap",
        knowledgeAsOf=cutoff,
        historyStatus=historyStatus,
        frequency=frequency,
        stepSpan=stepSpan,
        variables=tuple(variables),
        observationCount=complete.height,
        eventStart=dates[0],
        eventEnd=dates[-1],
        pathCount=pathCount,
        horizon=horizon,
        blockLength=blockLength,
        seed=int(seed),
        weightLabel="empiricalResamplingMeasure",
        validationStatus=validationStatus,
        certificateId=certificateId,
        maxAdmittedStep=maxAdmittedStep,
        sampledBlocks=tuple(sampledBlocks),
        warnings=tuple(warnings),
    )
    return EmpiricalPathSet(tuple(paths), audit)
