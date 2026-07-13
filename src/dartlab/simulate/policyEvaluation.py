"""Raw paired-origin OOS episode ledger and deterministic policy statistics."""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass, replace
from datetime import date
from hashlib import sha256
from pathlib import Path

import numpy as np

from dartlab.simulate.admissionRegistry import AdmissionVerifier
from dartlab.simulate.vintage import canonicalPayloadBytes, canonicalPayloadHash
from dartlab.simulate.world import (
    ConstraintSpec,
    ObjectiveSpec,
    PathTrace,
    ScenarioPath,
    SimulationRun,
    StrategySpec,
    constraintContractHash,
    objectiveContractHash,
    pathSetAdmissionSubjectHash,
    strategyContractHash,
    traceRootFor,
)

_EPISODE_SCHEMA = "policy-oos-episode-v1"
_REPORT_SCHEMA = "policy-evaluation-report-v1"
_BOOTSTRAP_METHOD = "paired-stationary-bootstrap-v1"
_BOOTSTRAP_REPLICATES = 9_999
_MIN_ORIGINS = 40
_MIN_EFFECTIVE_BLOCKS = 8
_MIN_TAIL_EFFECTIVE_PATHS = 20.0
_NO_PARAMETER_CONTRACT = sha256(b"dartlab.policy-oos.no-parameter-contract.v1").hexdigest()


class PolicyEvaluationError(ValueError):
    """OOS episode의 pairing, 원자료, 원장 또는 통계 계약이 잘못되면 발생한다."""


def _validDigest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value.lower())


def _dateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")[:8]
    if len(text) != 8 or not text.isdigit():
        raise PolicyEvaluationError(f"invalid {label}: {value}")
    return text


def _dateValue(value: str, label: str) -> date:
    text = _dateText(value, label)
    return date(int(text[:4]), int(text[4:6]), int(text[6:8]))


@dataclass(frozen=True)
class PolicyPathPrimitive:
    """한 origin의 공통 path에서 두 전략의 step 원재료와 trace 결속을 보존한다."""

    pathId: str
    pathOrdinal: int
    pathWeight: float
    parameterDrawHash: str
    baselineMetricByStep: tuple[float, ...]
    candidateMetricByStep: tuple[float, ...]
    baselineBreachesByStep: tuple[tuple[str, ...], ...]
    candidateBreachesByStep: tuple[tuple[str, ...], ...]
    baselineTraceHash: str
    candidateTraceHash: str


@dataclass(frozen=True)
class PolicyOosEpisode:
    """한 OOS origin의 동일 run·path·draw 위 paired 정책 원자료를 봉인한다."""

    episodeId: str
    originKey: str
    originOrdinal: int
    originAsOf: str
    outcomeThrough: str
    outcomeAvailableAt: str
    evaluationKnowledgeAsOf: str
    evidenceKind: str
    runHash: str
    resultHash: str
    traceRoot: str
    executableHash: str
    parameterHash: str
    dataVintageHash: str
    pathAdmissionReceiptId: str
    pathContentHash: str
    pathRuleId: str
    pathRuleVersion: str
    pathRuleHash: str
    parameterContractHash: str
    outcomeVintageReceiptId: str
    baselineStrategyId: str
    baselinePolicyVersion: str
    baselineStrategyContractHash: str
    candidateStrategyId: str
    candidatePolicyVersion: str
    candidateStrategyContractHash: str
    objective: ObjectiveSpec
    objectiveContractHash: str
    constraintContractHash: str
    paths: tuple[PolicyPathPrimitive, ...]
    admissionStatus: str = "documented"
    schemaVersion: str = _EPISODE_SCHEMA


@dataclass(frozen=True)
class PolicyOosLedgerSnapshot:
    """검증된 append-only episode 순서와 현재 row-chain root를 반환한다."""

    episodes: tuple[PolicyOosEpisode, ...]
    ledgerRoot: str


@dataclass(frozen=True)
class PolicyEvaluationSpec:
    """사전 고정한 materiality, CVaR 비열등, bootstrap, 표본 하한을 선언한다."""

    materialityMargin: float
    cvarNonInferiorityMargin: float = 0.0
    cvarTailFraction: float = 0.2
    confidenceLevel: float = 0.95
    bootstrapReplicates: int = _BOOTSTRAP_REPLICATES
    minOrigins: int = _MIN_ORIGINS
    minEffectiveBlocks: int = _MIN_EFFECTIVE_BLOCKS
    minTailEffectivePaths: float = _MIN_TAIL_EFFECTIVE_PATHS
    bootstrapMethod: str = _BOOTSTRAP_METHOD


@dataclass(frozen=True)
class PolicyEvaluationReport:
    """원시 episode에서 재계산한 통계적 적격성과 비-admission 상태를 보존한다."""

    reportId: str
    status: str
    admissionStatus: str
    ledgerRoot: str
    episodeIds: tuple[str, ...]
    nOrigins: int
    originStart: str
    originEnd: str
    blockLength: int
    effectiveBlockCount: int
    bootstrapMethod: str
    bootstrapReplicates: int
    bootstrapSeed: int
    bootstrapIndexHash: str
    confidenceLevel: float
    primaryEstimate: float
    primaryLowerBound: float
    materialityMargin: float
    candidateCvarMean: float
    baselineCvarMean: float
    cvarDeltaEstimate: float
    cvarDeltaLowerBound: float
    cvarNonInferiorityMargin: float
    cvarTailFraction: float
    minimumTailEffectivePaths: float
    candidateHardBreachCount: int
    baselineHardBreachCount: int
    candidateStrategyContractHash: str
    baselineStrategyContractHash: str
    objectiveContractHash: str
    constraintContractHash: str
    pathRuleHash: str
    parameterContractHash: str
    reasons: tuple[str, ...]
    schemaVersion: str = _REPORT_SCHEMA


def _episodePayload(episode: PolicyOosEpisode) -> dict:
    return {name: getattr(episode, name) for name in episode.__dataclass_fields__ if name != "episodeId"}


def _validatePathPrimitive(row: PolicyPathPrimitive, horizon: int) -> None:
    if not row.pathId or row.pathOrdinal < 0:
        raise PolicyEvaluationError("policy path primitive identity is invalid")
    if not math.isfinite(row.pathWeight) or row.pathWeight <= 0:
        raise PolicyEvaluationError("policy path primitive needs a positive finite weight")
    if not _validDigest(row.parameterDrawHash):
        raise PolicyEvaluationError("policy path parameter draw hash is invalid")
    if len(row.baselineMetricByStep) != horizon or len(row.candidateMetricByStep) != horizon:
        raise PolicyEvaluationError("policy path metric horizon mismatch")
    if len(row.baselineBreachesByStep) != horizon or len(row.candidateBreachesByStep) != horizon:
        raise PolicyEvaluationError("policy path constraint horizon mismatch")
    if any(not math.isfinite(float(value)) for value in (*row.baselineMetricByStep, *row.candidateMetricByStep)):
        raise PolicyEvaluationError("policy path metric contains a non-finite value")
    if not _validDigest(row.baselineTraceHash) or not _validDigest(row.candidateTraceHash):
        raise PolicyEvaluationError("policy path trace hash is invalid")


def _validateEpisode(episode: PolicyOosEpisode) -> None:
    if episode.schemaVersion != _EPISODE_SCHEMA or episode.admissionStatus != "documented":
        raise PolicyEvaluationError("policy episode protocol mismatch")
    for label, value in (
        ("episode", episode.episodeId),
        ("origin", episode.originKey),
        ("run", episode.runHash),
        ("result", episode.resultHash),
        ("trace", episode.traceRoot),
        ("executable", episode.executableHash),
        ("parameter", episode.parameterHash),
        ("data vintage", episode.dataVintageHash),
        ("path receipt", episode.pathAdmissionReceiptId),
        ("path content", episode.pathContentHash),
        ("path rule", episode.pathRuleHash),
        ("parameter contract", episode.parameterContractHash),
        ("outcome receipt", episode.outcomeVintageReceiptId),
        ("baseline contract", episode.baselineStrategyContractHash),
        ("candidate contract", episode.candidateStrategyContractHash),
        ("objective contract", episode.objectiveContractHash),
        ("constraint contract", episode.constraintContractHash),
    ):
        if not _validDigest(value):
            raise PolicyEvaluationError(f"policy episode {label} hash is invalid")
    if episode.episodeId != canonicalPayloadHash(_episodePayload(episode)):
        raise PolicyEvaluationError("policy episode content hash mismatch")
    origin = _dateValue(episode.originAsOf, "originAsOf")
    outcome = _dateValue(episode.outcomeThrough, "outcomeThrough")
    available = _dateValue(episode.outcomeAvailableAt, "outcomeAvailableAt")
    knowledge = _dateValue(episode.evaluationKnowledgeAsOf, "evaluationKnowledgeAsOf")
    if not origin < outcome <= available <= knowledge:
        raise PolicyEvaluationError("policy episode outcome timing is invalid")
    if episode.evidenceKind != "modelReplay":
        raise PolicyEvaluationError("policy episode cannot claim observed intervention evidence")
    if (
        episode.originOrdinal < 0
        or not episode.pathRuleId
        or not episode.pathRuleVersion
        or not episode.baselineStrategyId
        or not episode.candidateStrategyId
        or episode.baselineStrategyId == episode.candidateStrategyId
        or not episode.candidatePolicyVersion
    ):
        raise PolicyEvaluationError("policy episode identity contract is incomplete")
    if not episode.paths:
        raise PolicyEvaluationError("policy episode needs raw paired path rows")
    horizon = len(episode.paths[0].candidateMetricByStep)
    for row in episode.paths:
        _validatePathPrimitive(row, horizon)
    if tuple(row.pathOrdinal for row in episode.paths) != tuple(range(len(episode.paths))):
        raise PolicyEvaluationError("policy episode path ordinals are not contiguous")
    if len({row.pathId for row in episode.paths}) != len(episode.paths):
        raise PolicyEvaluationError("policy episode contains duplicate path ids")
    if episode.objectiveContractHash != objectiveContractHash(episode.objective):
        raise PolicyEvaluationError("policy episode objective contract mismatch")


def _parameterContractHash(paths: tuple[ScenarioPath, ...]) -> str:
    receipts = {path.parameterDrawReceipt for path in paths if path.parameterDraws}
    if not receipts:
        return _NO_PARAMETER_CONTRACT
    if None in receipts or len(receipts) != 1:
        raise PolicyEvaluationError("policy episode paths need one parameter provenance contract")
    receipt = next(iter(receipts))
    return canonicalPayloadHash(
        {
            "distributionId": receipt.distributionId,
            "distributionKind": receipt.distributionKind,
            "generatorVersion": receipt.generatorVersion,
            "parameterNames": receipt.parameterNames,
            "parameterUnits": receipt.parameterUnits,
            "frequency": receipt.frequency,
            "stepSpan": receipt.stepSpan,
            "revisionPolicy": receipt.revisionPolicy,
            "coverage": receipt.coverage,
        }
    )


def _reportPayload(report: PolicyEvaluationReport) -> dict:
    return {name: getattr(report, name) for name in report.__dataclass_fields__ if name != "reportId"}


def _traceMetric(trace: PathTrace, objective: ObjectiveSpec) -> tuple[float, ...]:
    values = tuple(float(step.after[objective.metric]) for step in trace.steps)
    if not values or any(not math.isfinite(value) for value in values):
        raise PolicyEvaluationError("policy trace objective primitive is missing or non-finite")
    return values


def buildPolicyOosEpisode(
    run: SimulationRun,
    paths: tuple[ScenarioPath, ...],
    baseline: StrategySpec,
    candidate: StrategySpec,
    objective: ObjectiveSpec,
    constraints: tuple[ConstraintSpec, ...],
    *,
    originOrdinal: int,
    outcomeThrough: str,
    outcomeAvailableAt: str,
    evaluationKnowledgeAsOf: str,
    outcomeVintageReceiptId: str,
    admissionVerifier: AdmissionVerifier,
) -> PolicyOosEpisode:
    """full paired run의 path별 step 원재료만 읽어 documented OOS episode를 만든다."""

    if run.retainedTraceCount != run.traceCount or len(run.traces) != run.traceCount:
        raise PolicyEvaluationError("policy OOS episode requires full retained traces")
    if traceRootFor(run.traces) != run.traceRoot:
        raise PolicyEvaluationError("policy OOS trace root mismatch")
    if not run.decisionAsOf:
        raise PolicyEvaluationError("policy OOS run needs a decision cutoff")
    if baseline.strategyId == candidate.strategyId or not baseline.isBaseline or candidate.isBaseline:
        raise PolicyEvaluationError("policy OOS episode needs one baseline and one candidate")
    if not candidate.policyVersion:
        raise PolicyEvaluationError("policy OOS candidate must be frozen and versioned")
    if set(evaluation.strategyId for evaluation in run.evaluations) != {baseline.strategyId, candidate.strategyId}:
        raise PolicyEvaluationError("policy OOS run must contain only the paired strategies")
    if objective not in run.objectives or tuple(constraints) != run.constraints:
        raise PolicyEvaluationError("policy OOS objective or constraint contract mismatch")
    if not paths or run.pathAdmissionReceiptId != paths[0].admissionReceiptId:
        raise PolicyEvaluationError("policy OOS run path receipt mismatch")
    if any(path.admissionReceiptId != run.pathAdmissionReceiptId for path in paths):
        raise PolicyEvaluationError("policy OOS paths do not share one admission receipt")
    pathContentHash = pathSetAdmissionSubjectHash(paths)
    if any(path.admissionContentHash != pathContentHash for path in paths):
        raise PolicyEvaluationError("policy OOS path content binding mismatch")
    pathReceipt = admissionVerifier.verify(
        run.pathAdmissionReceiptId,
        expectedSubjectHash=pathContentHash,
        expectedKind="pathSet",
    )
    outcomeReceipt = admissionVerifier.verify(outcomeVintageReceiptId, expectedKind="dataVintage")
    origin = _dateText(run.decisionAsOf, "originAsOf")
    if pathReceipt.status != "admitted" or _dateText(pathReceipt.issuedAt, "path issuedAt") > origin:
        raise PolicyEvaluationError("policy OOS path was not admitted by the origin")
    if (
        outcomeReceipt.status != "verifiedVintage"
        or outcomeReceipt.revisionPolicy != "asKnown"
        or outcomeReceipt.coverage != "asOfExact"
    ):
        raise PolicyEvaluationError("policy OOS outcome needs an exact as-known vintage")
    if _dateText(outcomeReceipt.knowledgeAsOf, "outcome knowledge") > _dateText(
        outcomeAvailableAt, "outcomeAvailableAt"
    ):
        raise PolicyEvaluationError("policy OOS outcome receipt is newer than outcomeAvailableAt")
    if _dateText(outcomeReceipt.issuedAt, "outcome issuedAt") > _dateText(
        evaluationKnowledgeAsOf, "evaluationKnowledgeAsOf"
    ):
        raise PolicyEvaluationError("policy OOS outcome receipt was unavailable at evaluation")
    traceByKey = {(trace.strategyId, trace.pathId): trace for trace in run.traces}
    rows: list[PolicyPathPrimitive] = []
    for ordinal, path in enumerate(paths):
        baselineTrace = traceByKey.get((baseline.strategyId, path.pathId))
        candidateTrace = traceByKey.get((candidate.strategyId, path.pathId))
        if baselineTrace is None or candidateTrace is None:
            raise PolicyEvaluationError("policy OOS pair is missing a common path trace")
        if len(baselineTrace.steps) != len(candidateTrace.steps):
            raise PolicyEvaluationError("policy OOS paired trace horizon mismatch")
        rows.append(
            PolicyPathPrimitive(
                pathId=path.pathId,
                pathOrdinal=ordinal,
                pathWeight=1.0 if path.weight is None else float(path.weight),
                parameterDrawHash=canonicalPayloadHash(dict(path.parameterDraws)),
                baselineMetricByStep=_traceMetric(baselineTrace, objective),
                candidateMetricByStep=_traceMetric(candidateTrace, objective),
                baselineBreachesByStep=tuple(step.breaches for step in baselineTrace.steps),
                candidateBreachesByStep=tuple(step.breaches for step in candidateTrace.steps),
                baselineTraceHash=canonicalPayloadHash(baselineTrace),
                candidateTraceHash=canonicalPayloadHash(candidateTrace),
            )
        )
    baselineHash = strategyContractHash(baseline)
    candidateHash = strategyContractHash(candidate)
    objectiveHash = objectiveContractHash(objective)
    constraintHash = constraintContractHash(constraints)
    parameterContract = _parameterContractHash(paths)
    originKey = canonicalPayloadHash(
        {
            "protocol": _EPISODE_SCHEMA,
            "originAsOf": origin,
            "outcomeThrough": _dateText(outcomeThrough, "outcomeThrough"),
            "executableHash": run.executableHash,
            "baselineContract": baselineHash,
            "candidateContract": candidateHash,
            "objectiveContract": objectiveHash,
            "constraintContract": constraintHash,
            "pathRuleHash": pathReceipt.ruleHash,
            "parameterContract": parameterContract,
        }
    )
    provisional = PolicyOosEpisode(
        episodeId="",
        originKey=originKey,
        originOrdinal=int(originOrdinal),
        originAsOf=origin,
        outcomeThrough=_dateText(outcomeThrough, "outcomeThrough"),
        outcomeAvailableAt=_dateText(outcomeAvailableAt, "outcomeAvailableAt"),
        evaluationKnowledgeAsOf=_dateText(evaluationKnowledgeAsOf, "evaluationKnowledgeAsOf"),
        evidenceKind="modelReplay",
        runHash=run.runHash,
        resultHash=run.resultHash,
        traceRoot=run.traceRoot,
        executableHash=run.executableHash,
        parameterHash=run.parameterHash,
        dataVintageHash=run.dataVintageHash,
        pathAdmissionReceiptId=run.pathAdmissionReceiptId,
        pathContentHash=pathContentHash,
        pathRuleId=pathReceipt.ruleId,
        pathRuleVersion=pathReceipt.ruleVersion,
        pathRuleHash=pathReceipt.ruleHash,
        parameterContractHash=parameterContract,
        outcomeVintageReceiptId=outcomeVintageReceiptId,
        baselineStrategyId=baseline.strategyId,
        baselinePolicyVersion=baseline.policyVersion,
        baselineStrategyContractHash=baselineHash,
        candidateStrategyId=candidate.strategyId,
        candidatePolicyVersion=candidate.policyVersion,
        candidateStrategyContractHash=candidateHash,
        objective=objective,
        objectiveContractHash=objectiveHash,
        constraintContractHash=constraintHash,
        paths=tuple(rows),
    )
    episode = replace(provisional, episodeId=canonicalPayloadHash(_episodePayload(provisional)))
    _validateEpisode(episode)
    return episode


def _episodeFromPayload(episodeId: str, payload: dict) -> PolicyOosEpisode:
    try:
        payload["objective"] = ObjectiveSpec(**payload["objective"])
        payload["paths"] = tuple(
            PolicyPathPrimitive(
                **{
                    **row,
                    "baselineMetricByStep": tuple(row["baselineMetricByStep"]),
                    "candidateMetricByStep": tuple(row["candidateMetricByStep"]),
                    "baselineBreachesByStep": tuple(tuple(item) for item in row["baselineBreachesByStep"]),
                    "candidateBreachesByStep": tuple(tuple(item) for item in row["candidateBreachesByStep"]),
                }
            )
            for row in payload["paths"]
        )
        return PolicyOosEpisode(episodeId=episodeId, **payload)
    except (KeyError, TypeError, ValueError) as error:
        raise PolicyEvaluationError("policy episode row payload is malformed") from error


def initializePolicyOosLedger(databasePath: str | Path) -> None:
    """mutation 차단 trigger와 hash chain이 있는 raw OOS episode 원장을 만든다."""

    path = Path(databasePath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS policy_oos_episodes (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                episode_id TEXT NOT NULL UNIQUE,
                origin_key TEXT NOT NULL UNIQUE,
                payload_json TEXT NOT NULL,
                previous_row_hash TEXT NOT NULL,
                row_hash TEXT NOT NULL UNIQUE
            );
            CREATE TRIGGER IF NOT EXISTS policy_oos_no_update
            BEFORE UPDATE ON policy_oos_episodes
            BEGIN
                SELECT RAISE(ABORT, 'policy OOS episodes are append-only');
            END;
            CREATE TRIGGER IF NOT EXISTS policy_oos_no_delete
            BEFORE DELETE ON policy_oos_episodes
            BEGIN
                SELECT RAISE(ABORT, 'policy OOS episodes are append-only');
            END;
            """
        )


def _rowHash(previousHash: str, episodeId: str, originKey: str) -> str:
    return sha256(
        b"dartlab.policy-oos-ledger-row.v1\0"
        + previousHash.encode("ascii")
        + episodeId.encode("ascii")
        + originKey.encode("ascii")
    ).hexdigest()


def appendPolicyOosEpisode(databasePath: str | Path, episode: PolicyOosEpisode) -> None:
    """검증한 raw episode를 중복 origin 없이 append-only 원장에 추가한다."""

    _validateEpisode(episode)
    database = Path(databasePath)
    if not database.exists():
        raise PolicyEvaluationError("policy OOS ledger is unavailable")
    with sqlite3.connect(database) as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("SELECT row_hash FROM policy_oos_episodes ORDER BY seq DESC LIMIT 1").fetchone()
        previousHash = str(row[0]) if row is not None else ""
        try:
            connection.execute(
                "INSERT INTO policy_oos_episodes "
                "(episode_id, origin_key, payload_json, previous_row_hash, row_hash) VALUES (?, ?, ?, ?, ?)",
                (
                    episode.episodeId,
                    episode.originKey,
                    canonicalPayloadBytes(_episodePayload(episode)).decode("utf-8"),
                    previousHash,
                    _rowHash(previousHash, episode.episodeId, episode.originKey),
                ),
            )
        except sqlite3.IntegrityError as error:
            raise PolicyEvaluationError("duplicate policy OOS episode or origin") from error


def readPolicyOosLedger(databasePath: str | Path) -> PolicyOosLedgerSnapshot:
    """전체 sequence와 row chain 및 episode 내용을 다시 계산해 읽는다."""

    database = Path(databasePath)
    if not database.exists():
        raise PolicyEvaluationError("policy OOS ledger is unavailable")
    try:
        connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
        rows = connection.execute(
            "SELECT seq, episode_id, origin_key, payload_json, previous_row_hash, row_hash "
            "FROM policy_oos_episodes ORDER BY seq"
        ).fetchall()
        connection.close()
    except sqlite3.Error as error:
        raise PolicyEvaluationError("policy OOS ledger is unavailable") from error
    episodes: list[PolicyOosEpisode] = []
    previousHash = ""
    for expectedSequence, row in enumerate(rows, start=1):
        sequence, episodeId, originKey, payloadJson, storedPrevious, storedHash = row
        if sequence != expectedSequence or storedPrevious != previousHash:
            raise PolicyEvaluationError("policy OOS ledger chain mismatch")
        expectedHash = _rowHash(previousHash, str(episodeId), str(originKey))
        if storedHash != expectedHash:
            raise PolicyEvaluationError("policy OOS ledger row hash mismatch")
        try:
            payload = json.loads(str(payloadJson))
        except json.JSONDecodeError as error:
            raise PolicyEvaluationError("policy OOS ledger payload is malformed") from error
        episode = _episodeFromPayload(str(episodeId), payload)
        _validateEpisode(episode)
        if episode.originKey != originKey:
            raise PolicyEvaluationError("policy OOS ledger origin key mismatch")
        episodes.append(episode)
        previousHash = expectedHash
    return PolicyOosLedgerSnapshot(tuple(episodes), previousHash)


def _reduce(values: tuple[float, ...], objective: ObjectiveSpec) -> float:
    if objective.reducer == "terminal":
        value = values[-1]
    elif objective.reducer == "minimum":
        value = min(values)
    elif objective.reducer == "maximum":
        value = max(values)
    elif objective.reducer == "cumulative":
        value = sum(values)
    else:
        raise PolicyEvaluationError("policy OOS objective reducer is invalid")
    return value if objective.direction == "maximize" else -value


def weightedLowerCvar(
    values: tuple[float, ...], weights: tuple[float, ...], tailFraction: float
) -> tuple[float, float]:
    """분수 경계질량을 포함한 exact weighted lower-tail CVaR와 tail ESS를 반환한다."""

    if len(values) != len(weights) or not values or not 0 < tailFraction <= 1:
        raise PolicyEvaluationError("weighted CVaR contract is invalid")
    if any(not math.isfinite(value) for value in (*values, *weights)) or any(weight <= 0 for weight in weights):
        raise PolicyEvaluationError("weighted CVaR inputs must be positive finite weights and finite values")
    totalWeight = sum(weights)
    target = totalWeight * tailFraction
    used = 0.0
    total = 0.0
    normalizedTailMasses: list[float] = []
    for _, value, weight in sorted(
        zip(range(len(values)), values, weights, strict=True), key=lambda row: (row[1], row[0])
    ):
        take = min(weight, target - used)
        if take > 0:
            total += value * take
            used += take
            normalizedTailMasses.append(take / totalWeight)
        if used >= target - 1e-12:
            break
    if used <= 0:
        raise PolicyEvaluationError("weighted CVaR has no tail mass")
    effectivePaths = tailFraction**2 / sum(mass**2 for mass in normalizedTailMasses)
    return total / used, effectivePaths


def _episodeStatistics(episode: PolicyOosEpisode, spec: PolicyEvaluationSpec) -> tuple[float, float, float, int, int]:
    objective = episode.objective
    weights = tuple(row.pathWeight for row in episode.paths)
    baseline = tuple(_reduce(row.baselineMetricByStep, objective) for row in episode.paths)
    candidate = tuple(_reduce(row.candidateMetricByStep, objective) for row in episode.paths)
    denominator = sum(weights)
    meanDelta = (
        sum(weight * (right - left) for left, right, weight in zip(baseline, candidate, weights, strict=True))
        / denominator
    )
    baselineCvar, baselineEss = weightedLowerCvar(baseline, weights, spec.cvarTailFraction)
    candidateCvar, candidateEss = weightedLowerCvar(candidate, weights, spec.cvarTailFraction)
    baselineBreaches = sum(len(items) for row in episode.paths for items in row.baselineBreachesByStep)
    candidateBreaches = sum(len(items) for row in episode.paths for items in row.candidateBreachesByStep)
    return meanDelta, candidateCvar - baselineCvar, min(baselineEss, candidateEss), baselineBreaches, candidateBreaches


def _validateSpec(spec: PolicyEvaluationSpec) -> None:
    if (
        not math.isfinite(spec.materialityMargin)
        or spec.materialityMargin <= 0
        or not math.isfinite(spec.cvarNonInferiorityMargin)
        or spec.cvarNonInferiorityMargin < 0
        or not 0 < spec.cvarTailFraction <= 0.5
        or not 0.5 < spec.confidenceLevel < 1
        or spec.bootstrapMethod != _BOOTSTRAP_METHOD
        or spec.bootstrapReplicates < _BOOTSTRAP_REPLICATES
        or spec.minOrigins < _MIN_ORIGINS
        or spec.minEffectiveBlocks < _MIN_EFFECTIVE_BLOCKS
        or spec.minTailEffectivePaths < _MIN_TAIL_EFFECTIVE_PATHS
    ):
        raise PolicyEvaluationError("policy evaluation spec weakens the admission floor")


def _blockLength(episodes: tuple[PolicyOosEpisode, ...]) -> int:
    n = len(episodes)
    if n < 2:
        return 1
    originDates = [_dateValue(episode.originAsOf, "originAsOf") for episode in episodes]
    gaps = sorted(max(1, (right - left).days) for left, right in zip(originDates, originDates[1:]))
    medianGap = gaps[len(gaps) // 2]
    outcomeHorizon = max(
        (_dateValue(episode.outcomeThrough, "outcomeThrough") - _dateValue(episode.originAsOf, "originAsOf")).days
        for episode in episodes
    )
    return min(n, max(2, math.ceil(n ** (1 / 3)), math.ceil(outcomeHorizon / medianGap)))


def _stationaryIndices(n: int, blockLength: int, replicates: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    indices = np.empty((replicates, n), dtype=np.int32)
    restartProbability = 1.0 / blockLength
    for sample in range(replicates):
        current = int(rng.integers(0, n))
        indices[sample, 0] = current
        for position in range(1, n):
            if float(rng.random()) < restartProbability:
                current = int(rng.integers(0, n))
            else:
                current = (current + 1) % n
            indices[sample, position] = current
    return indices


def _basicLowerBound(values: np.ndarray, indices: np.ndarray, confidenceLevel: float) -> tuple[float, float]:
    estimate = float(np.mean(values))
    bootstrap = np.mean(values[indices], axis=1)
    errorQuantile = float(np.quantile(bootstrap - estimate, confidenceLevel, method="higher"))
    return estimate, estimate - errorQuantile


def evaluatePolicyOos(snapshot: PolicyOosLedgerSnapshot, spec: PolicyEvaluationSpec) -> PolicyEvaluationReport:
    """전체 origin raw rows에서 mean materiality와 separate-CVaR 비열등을 paired 재계산한다."""

    _validateSpec(spec)
    if not snapshot.episodes:
        raise PolicyEvaluationError("policy evaluation needs OOS episodes")
    episodes = tuple(sorted(snapshot.episodes, key=lambda episode: (episode.originAsOf, episode.originOrdinal)))
    for episode in episodes:
        _validateEpisode(episode)
    origins = [episode.originAsOf for episode in episodes]
    originKeys = [episode.originKey for episode in episodes]
    if len(set(origins)) != len(origins) or len(set(originKeys)) != len(originKeys):
        raise PolicyEvaluationError("policy evaluation contains duplicate origins")
    ordinals = [episode.originOrdinal for episode in episodes]
    if ordinals != list(range(ordinals[0], ordinals[0] + len(ordinals))):
        raise PolicyEvaluationError("policy evaluation origin ordinal gap")
    contractFields = (
        "evidenceKind",
        "executableHash",
        "pathRuleId",
        "pathRuleVersion",
        "pathRuleHash",
        "parameterContractHash",
        "baselineStrategyId",
        "baselinePolicyVersion",
        "baselineStrategyContractHash",
        "candidateStrategyId",
        "candidatePolicyVersion",
        "candidateStrategyContractHash",
        "objectiveContractHash",
        "constraintContractHash",
        "admissionStatus",
    )
    for fieldName in contractFields:
        if len({getattr(episode, fieldName) for episode in episodes}) != 1:
            raise PolicyEvaluationError(f"policy evaluation contract drift: {fieldName}")
    ledgerHash = canonicalPayloadHash(
        {"ledgerRoot": snapshot.ledgerRoot, "episodeIds": tuple(episode.episodeId for episode in episodes)}
    )
    specHash = canonicalPayloadHash(spec)
    seed = int.from_bytes(
        sha256(b"dartlab.policy-oos-bootstrap-v1\0" + bytes.fromhex(ledgerHash) + bytes.fromhex(specHash)).digest()[:8],
        "big",
    )
    blockLength = _blockLength(episodes)
    indices = _stationaryIndices(len(episodes), blockLength, spec.bootstrapReplicates, seed)
    statistics = [_episodeStatistics(episode, spec) for episode in episodes]
    meanDeltas = np.array([item[0] for item in statistics], dtype=np.float64)
    cvarDeltas = np.array([item[1] for item in statistics], dtype=np.float64)
    primaryEstimate, primaryLower = _basicLowerBound(meanDeltas, indices, spec.confidenceLevel)
    cvarEstimate, cvarLower = _basicLowerBound(cvarDeltas, indices, spec.confidenceLevel)
    tailEss = min(item[2] for item in statistics)
    baselineBreaches = sum(item[3] for item in statistics)
    candidateBreaches = sum(item[4] for item in statistics)
    baselineCvars = []
    candidateCvars = []
    for episode in episodes:
        weights = tuple(row.pathWeight for row in episode.paths)
        objective = episode.objective
        baselineValues = tuple(_reduce(row.baselineMetricByStep, objective) for row in episode.paths)
        candidateValues = tuple(_reduce(row.candidateMetricByStep, objective) for row in episode.paths)
        baselineCvars.append(weightedLowerCvar(baselineValues, weights, spec.cvarTailFraction)[0])
        candidateCvars.append(weightedLowerCvar(candidateValues, weights, spec.cvarTailFraction)[0])
    effectiveBlocks = len(episodes) // blockLength
    reasons: list[str] = []
    if len(episodes) < spec.minOrigins:
        reasons.append("insufficientOrigins")
    if effectiveBlocks < spec.minEffectiveBlocks:
        reasons.append("insufficientIndependentBlocks")
    if tailEss < spec.minTailEffectivePaths:
        reasons.append("insufficientTailEffectivePaths")
    if primaryLower < spec.materialityMargin:
        reasons.append("primaryMaterialityLcbFailed")
    if cvarLower < -spec.cvarNonInferiorityMargin:
        reasons.append("cvarNonInferiorityLcbFailed")
    if candidateBreaches:
        reasons.append("candidateHardConstraintBreach")
    status = (
        "statisticallyEligible"
        if not reasons
        else ("insufficientEvidence" if reasons[0].startswith("insufficient") else "rejected")
    )
    provisional = PolicyEvaluationReport(
        reportId="",
        status=status,
        admissionStatus="documented",
        ledgerRoot=snapshot.ledgerRoot,
        episodeIds=tuple(episode.episodeId for episode in episodes),
        nOrigins=len(episodes),
        originStart=episodes[0].originAsOf,
        originEnd=episodes[-1].originAsOf,
        blockLength=blockLength,
        effectiveBlockCount=effectiveBlocks,
        bootstrapMethod=spec.bootstrapMethod,
        bootstrapReplicates=spec.bootstrapReplicates,
        bootstrapSeed=seed,
        bootstrapIndexHash=sha256(indices.tobytes(order="C")).hexdigest(),
        confidenceLevel=spec.confidenceLevel,
        primaryEstimate=primaryEstimate,
        primaryLowerBound=primaryLower,
        materialityMargin=spec.materialityMargin,
        candidateCvarMean=float(np.mean(candidateCvars)),
        baselineCvarMean=float(np.mean(baselineCvars)),
        cvarDeltaEstimate=cvarEstimate,
        cvarDeltaLowerBound=cvarLower,
        cvarNonInferiorityMargin=spec.cvarNonInferiorityMargin,
        cvarTailFraction=spec.cvarTailFraction,
        minimumTailEffectivePaths=tailEss,
        candidateHardBreachCount=candidateBreaches,
        baselineHardBreachCount=baselineBreaches,
        candidateStrategyContractHash=episodes[0].candidateStrategyContractHash,
        baselineStrategyContractHash=episodes[0].baselineStrategyContractHash,
        objectiveContractHash=episodes[0].objectiveContractHash,
        constraintContractHash=episodes[0].constraintContractHash,
        pathRuleHash=episodes[0].pathRuleHash,
        parameterContractHash=episodes[0].parameterContractHash,
        reasons=tuple(reasons),
    )
    return replace(provisional, reportId=canonicalPayloadHash(_reportPayload(provisional)))
