"""Raw paired-origin OOS episode ledger and deterministic policy statistics."""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass, replace
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Mapping

import numpy as np
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dartlab.simulate.admissionRegistry import (
    AdmissionVerifier,
    TrustedIssuer,
    artifactPath,
    issueAdmissionReceipt,
    putAdmissionArtifact,
)
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
_EPISODE_RULE_ID = "paired-origin-policy-oos-episode"
_EPISODE_RULE_VERSION = "1"
_EPISODE_RULE_HASH = sha256(b"dartlab.paired-origin-policy-oos-episode.v1").hexdigest()
_BATCH_SCHEMA = "policy-oos-batch-v1"
_BATCH_RULE_ID = "paired-origin-policy-oos-batch"
_BATCH_RULE_VERSION = "1"
_BATCH_RULE_HASH = sha256(b"dartlab.paired-origin-policy-oos-batch.v1").hexdigest()
_CERTIFICATE_SCHEMA = "policy-evaluation-certificate-v1"
_CERTIFICATE_RULE_ID = "paired-origin-policy-evaluation"
_CERTIFICATE_RULE_VERSION = "1"
_CERTIFICATE_RULE_HASH = sha256(b"dartlab.paired-origin-policy-evaluation.v1").hexdigest()


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
    episodeReceiptId: str = ""
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
    executableHash: str
    candidateStrategyContractHash: str
    baselineStrategyContractHash: str
    objectiveContractHash: str
    constraintContractHash: str
    pathRuleHash: str
    parameterContractHash: str
    reasons: tuple[str, ...]
    schemaVersion: str = _REPORT_SCHEMA


@dataclass(frozen=True)
class PolicyEpisodeBatch:
    """서명된 episode 전부와 원장 checkpoint를 동결한 batch manifest다."""

    batchId: str
    batchReceiptId: str
    ledgerRoot: str
    checkpointSequence: int
    checkpointRowHash: str
    episodeIds: tuple[str, ...]
    episodeReceiptIds: tuple[str, ...]
    originStart: str
    originEnd: str
    knowledgeAsOf: str
    executableHash: str
    baselineStrategyContractHash: str
    candidateStrategyContractHash: str
    objectiveContractHash: str
    constraintContractHash: str
    pathRuleHash: str
    parameterContractHash: str
    status: str = "admitted"
    schemaVersion: str = _BATCH_SCHEMA


@dataclass(frozen=True)
class PolicyEvaluationCertificate:
    """raw batch 재계산 결과와 policyAdmitted 서명 receipt를 결속한다."""

    certificateId: str
    certificateReceiptId: str
    batchId: str
    batchReceiptId: str
    knowledgeAsOf: str
    executableHash: str
    baselineStrategyContractHash: str
    candidateStrategyContractHash: str
    objectiveContractHash: str
    constraintContractHash: str
    pathRuleHash: str
    parameterContractHash: str
    spec: PolicyEvaluationSpec
    report: PolicyEvaluationReport
    status: str
    schemaVersion: str = _CERTIFICATE_SCHEMA


@dataclass(frozen=True)
class PolicyAdmissionEvidence:
    """runtime이 원장 checkpoint부터 인증서까지 함께 재검증하는 입력 묶음이다."""

    snapshot: PolicyOosLedgerSnapshot
    batch: PolicyEpisodeBatch
    certificate: PolicyEvaluationCertificate


def _episodePayload(episode: PolicyOosEpisode) -> dict:
    return {
        name: getattr(episode, name)
        for name in episode.__dataclass_fields__
        if name not in {"episodeId", "episodeReceiptId"}
    }


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
    if episode.schemaVersion != _EPISODE_SCHEMA or episode.admissionStatus not in {"documented", "admitted"}:
        raise PolicyEvaluationError("policy episode protocol mismatch")
    if episode.admissionStatus == "admitted" and not _validDigest(episode.episodeReceiptId):
        raise PolicyEvaluationError("admitted policy episode needs a signed receipt")
    if episode.admissionStatus == "documented" and episode.episodeReceiptId:
        raise PolicyEvaluationError("documented policy episode cannot claim a signed receipt")
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


def parameterContractHashFor(paths: tuple[ScenarioPath, ...]) -> str:
    """현재 경로 집합의 parameter-measure 계약을 policy 인증서와 비교 가능한 hash로 반환한다."""

    return _parameterContractHash(paths)


def _reportPayload(report: PolicyEvaluationReport) -> dict:
    return {name: getattr(report, name) for name in report.__dataclass_fields__ if name != "reportId"}


def _batchPayload(batch: PolicyEpisodeBatch) -> dict:
    return {
        name: getattr(batch, name) for name in batch.__dataclass_fields__ if name not in {"batchId", "batchReceiptId"}
    }


def _certificatePayload(certificate: PolicyEvaluationCertificate) -> dict:
    return {
        name: getattr(certificate, name)
        for name in certificate.__dataclass_fields__
        if name not in {"certificateId", "certificateReceiptId"}
    }


def _validateBatch(batch: PolicyEpisodeBatch) -> None:
    if batch.schemaVersion != _BATCH_SCHEMA or batch.status != "admitted":
        raise PolicyEvaluationError("policy episode batch protocol mismatch")
    for label, value in (
        ("batch", batch.batchId),
        ("batch receipt", batch.batchReceiptId),
        ("ledger root", batch.ledgerRoot),
        ("checkpoint row", batch.checkpointRowHash),
        ("executable", batch.executableHash),
        ("baseline contract", batch.baselineStrategyContractHash),
        ("candidate contract", batch.candidateStrategyContractHash),
        ("objective contract", batch.objectiveContractHash),
        ("constraint contract", batch.constraintContractHash),
        ("path rule", batch.pathRuleHash),
        ("parameter contract", batch.parameterContractHash),
    ):
        if not _validDigest(value):
            raise PolicyEvaluationError(f"policy episode batch {label} hash is invalid")
    if (
        batch.batchId != canonicalPayloadHash(_batchPayload(batch))
        or batch.checkpointSequence < 1
        or batch.ledgerRoot != batch.checkpointRowHash
        or len(batch.episodeIds) != batch.checkpointSequence
        or len(batch.episodeReceiptIds) != batch.checkpointSequence
        or len(set(batch.episodeIds)) != len(batch.episodeIds)
        or len(set(batch.episodeReceiptIds)) != len(batch.episodeReceiptIds)
        or any(not _validDigest(value) for value in (*batch.episodeIds, *batch.episodeReceiptIds))
    ):
        raise PolicyEvaluationError("policy episode batch manifest mismatch")
    if not (
        _dateText(batch.originStart, "batch originStart")
        <= _dateText(batch.originEnd, "batch originEnd")
        <= _dateText(batch.knowledgeAsOf, "batch knowledgeAsOf")
    ):
        raise PolicyEvaluationError("policy episode batch timing mismatch")


def _validateCertificate(certificate: PolicyEvaluationCertificate) -> None:
    if certificate.schemaVersion != _CERTIFICATE_SCHEMA or certificate.status not in {
        "policyAdmitted",
        "rejected",
    }:
        raise PolicyEvaluationError("policy evaluation certificate protocol mismatch")
    for label, value in (
        ("certificate", certificate.certificateId),
        ("certificate receipt", certificate.certificateReceiptId),
        ("batch", certificate.batchId),
        ("batch receipt", certificate.batchReceiptId),
        ("executable", certificate.executableHash),
        ("baseline contract", certificate.baselineStrategyContractHash),
        ("candidate contract", certificate.candidateStrategyContractHash),
        ("objective contract", certificate.objectiveContractHash),
        ("constraint contract", certificate.constraintContractHash),
        ("path rule", certificate.pathRuleHash),
        ("parameter contract", certificate.parameterContractHash),
    ):
        if not _validDigest(value):
            raise PolicyEvaluationError(f"policy evaluation certificate {label} hash is invalid")
    if certificate.certificateId != canonicalPayloadHash(_certificatePayload(certificate)):
        raise PolicyEvaluationError("policy evaluation certificate content hash mismatch")
    _dateText(certificate.knowledgeAsOf, "certificate knowledgeAsOf")


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


def _validateIssuerKey(
    privateKey: bytes,
    *,
    issuerId: str,
    issuerKeyId: str,
    trustedIssuers: Mapping[str, TrustedIssuer],
) -> None:
    trusted = trustedIssuers.get(issuerKeyId)
    if trusted is None or trusted.issuerId != issuerId or trusted.status != "trusted":
        raise PolicyEvaluationError("policy issuer key is not trusted")
    try:
        public = (
            Ed25519PrivateKey.from_private_bytes(privateKey)
            .public_key()
            .public_bytes(
                serialization.Encoding.Raw,
                serialization.PublicFormat.Raw,
            )
        )
    except ValueError as error:
        raise PolicyEvaluationError("policy issuer private key is invalid") from error
    if public != trusted.publicKey:
        raise PolicyEvaluationError("policy issuer private key does not match the allowlist")


def _requireReceipt(
    verifier: AdmissionVerifier,
    receiptId: str,
    *,
    kind: str,
    subjectHash: str | None = None,
    statuses: set[str],
):
    receipt = verifier.verify(receiptId, expectedSubjectHash=subjectHash, expectedKind=kind)
    if receipt.status not in statuses:
        raise PolicyEvaluationError(f"policy parent is not admitted: {kind}")
    return receipt


def _requireRule(receipt, *, ruleId: str, ruleVersion: str, ruleHash: str) -> None:
    if (receipt.ruleId, receipt.ruleVersion, receipt.ruleHash) != (ruleId, ruleVersion, ruleHash):
        raise PolicyEvaluationError(f"typed admission rule mismatch: {receipt.kind}")


def _validateEpisodeReceipt(episode: PolicyOosEpisode, receipt) -> None:
    _requireRule(
        receipt,
        ruleId=_EPISODE_RULE_ID,
        ruleVersion=_EPISODE_RULE_VERSION,
        ruleHash=_EPISODE_RULE_HASH,
    )
    if (
        receipt.artifactHash != episode.episodeId
        or receipt.knowledgeAsOf != _dateText(episode.evaluationKnowledgeAsOf, "evaluationKnowledgeAsOf")
        or episode.pathAdmissionReceiptId not in receipt.parentReceiptIds
        or episode.outcomeVintageReceiptId not in receipt.parentReceiptIds
    ):
        raise PolicyEvaluationError("policy episode receipt contract mismatch")


def _validateEpisodePathArtifact(episode: PolicyOosEpisode, pathReceipt, verifier: AdmissionVerifier) -> None:
    if pathReceipt.artifactHash != episode.pathContentHash:
        raise PolicyEvaluationError("policy episode path receipt artifact mismatch")
    horizon = len(episode.paths[0].candidateMetricByStep)
    if (
        pathReceipt.ruleId != episode.pathRuleId
        or pathReceipt.ruleVersion != episode.pathRuleVersion
        or pathReceipt.ruleHash != episode.pathRuleHash
        or pathReceipt.maxAdmittedStep != horizon
    ):
        raise PolicyEvaluationError("policy episode path admission contract mismatch")
    try:
        payload = json.loads(artifactPath(verifier.artifactRoot, pathReceipt.artifactHash).read_text(encoding="utf-8"))
        artifactRows = payload["paths"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise PolicyEvaluationError("policy episode path-set artifact is malformed") from error
    if not isinstance(artifactRows, list) or len(artifactRows) != len(episode.paths):
        raise PolicyEvaluationError("policy episode raw rows do not match the admitted path set")
    for primitive, artifactRow in zip(episode.paths, artifactRows, strict=True):
        if not isinstance(artifactRow, dict):
            raise PolicyEvaluationError("policy episode path-set artifact row is malformed")
        weight = 1.0 if artifactRow.get("weight") is None else float(artifactRow["weight"])
        parameterDraws = artifactRow.get("parameterDraws")
        steps = artifactRow.get("steps")
        if (
            primitive.pathId != artifactRow.get("pathId")
            or primitive.pathWeight != weight
            or not isinstance(parameterDraws, dict)
            or primitive.parameterDrawHash != canonicalPayloadHash(parameterDraws)
            or not isinstance(steps, list)
            or len(steps) != horizon
            or artifactRow.get("frequency") != pathReceipt.frequency
            or int(artifactRow.get("stepSpan", 0)) != pathReceipt.stepSpan
            or int(artifactRow.get("maxAdmittedStep", -1)) != horizon
        ):
            raise PolicyEvaluationError("policy episode raw path primitive drifted from its admitted artifact")
    parentReceipts = tuple(verifier.verify(receiptId) for receiptId in pathReceipt.parentReceiptIds)
    vintageParents = tuple(
        receipt
        for receipt in parentReceipts
        if receipt.kind == "dataVintage"
        and receipt.status == "verifiedVintage"
        and receipt.revisionPolicy == "asKnown"
        and receipt.coverage == "asOfExact"
    )
    origin = _dateText(episode.originAsOf, "originAsOf")
    if not vintageParents or any(
        _dateText(receipt.issuedAt, "path vintage issuedAt") > origin for receipt in vintageParents
    ):
        raise PolicyEvaluationError("policy episode path set lacks an origin-available exact vintage parent")


def admitPolicyOosEpisode(
    episode: PolicyOosEpisode,
    databasePath: str | Path,
    artifactRoot: str | Path,
    *,
    privateKey: bytes,
    initialStateReceiptId: str,
    modelReceiptId: str,
    baselineStrategyReceiptId: str,
    candidateStrategyReceiptId: str,
    parameterDrawReceiptId: str = "",
    issuerId: str,
    issuerKeyId: str,
    issuerExecutableHash: str,
    issuedAt: str,
    trustedIssuers: Mapping[str, TrustedIssuer],
) -> PolicyOosEpisode:
    """typed parent를 재검증한 documented episode만 서명된 admitted evidence로 승격한다."""

    _validateEpisode(episode)
    if episode.admissionStatus != "documented":
        raise PolicyEvaluationError("only documented policy episodes can enter the typed signer")
    _validateIssuerKey(
        privateKey,
        issuerId=issuerId,
        issuerKeyId=issuerKeyId,
        trustedIssuers=trustedIssuers,
    )
    verifier = AdmissionVerifier(databasePath, artifactRoot, trustedIssuers)
    pathReceipt = _requireReceipt(
        verifier,
        episode.pathAdmissionReceiptId,
        kind="pathSet",
        subjectHash=episode.pathContentHash,
        statuses={"admitted"},
    )
    _validateEpisodePathArtifact(episode, pathReceipt, verifier)
    outcomeReceipt = _requireReceipt(
        verifier,
        episode.outcomeVintageReceiptId,
        kind="dataVintage",
        statuses={"verifiedVintage"},
    )
    initialReceipt = _requireReceipt(
        verifier,
        initialStateReceiptId,
        kind="initialState",
        subjectHash=episode.dataVintageHash,
        statuses={"admitted"},
    )
    modelReceipt = _requireReceipt(
        verifier,
        modelReceiptId,
        kind="modelExecutable",
        subjectHash=episode.executableHash,
        statuses={"admitted"},
    )
    baselineReceipt = _requireReceipt(
        verifier,
        baselineStrategyReceiptId,
        kind="strategy",
        subjectHash=episode.baselineStrategyContractHash,
        statuses={"admitted"},
    )
    candidateReceipt = _requireReceipt(
        verifier,
        candidateStrategyReceiptId,
        kind="strategy",
        subjectHash=episode.candidateStrategyContractHash,
        statuses={"admitted"},
    )
    decisionParents = [pathReceipt, initialReceipt, modelReceipt, baselineReceipt, candidateReceipt]
    parentIds = [
        episode.pathAdmissionReceiptId,
        episode.outcomeVintageReceiptId,
        initialStateReceiptId,
        modelReceiptId,
        baselineStrategyReceiptId,
        candidateStrategyReceiptId,
    ]
    if episode.parameterContractHash != _NO_PARAMETER_CONTRACT:
        parameterReceipt = _requireReceipt(
            verifier,
            parameterDrawReceiptId,
            kind="parameterDraw",
            subjectHash=episode.parameterContractHash,
            statuses={"admitted"},
        )
        decisionParents.append(parameterReceipt)
        parentIds.append(parameterDrawReceiptId)
    elif parameterDrawReceiptId:
        raise PolicyEvaluationError("parameter receipt was supplied to a no-parameter episode")
    origin = _dateText(episode.originAsOf, "originAsOf")
    if any(_dateText(receipt.issuedAt, "decision parent issuedAt") > origin for receipt in decisionParents):
        raise PolicyEvaluationError("policy decision parent was issued after the origin")
    outcomeThrough = _dateText(episode.outcomeThrough, "outcomeThrough")
    outcomeKnowledge = _dateText(outcomeReceipt.knowledgeAsOf, "outcome knowledge")
    if (
        outcomeKnowledge < outcomeThrough
        or outcomeKnowledge > _dateText(episode.outcomeAvailableAt, "outcomeAvailableAt")
        or _dateText(outcomeReceipt.issuedAt, "outcome issuedAt")
        > _dateText(episode.evaluationKnowledgeAsOf, "evaluationKnowledgeAsOf")
    ):
        raise PolicyEvaluationError("policy outcome receipt timing is invalid")
    if _dateText(issuedAt, "episode issuedAt") < _dateText(episode.evaluationKnowledgeAsOf, "evaluationKnowledgeAsOf"):
        raise PolicyEvaluationError("policy episode cannot be issued before evaluation knowledge")
    admitted = replace(episode, episodeId="", admissionStatus="admitted")
    admitted = replace(admitted, episodeId=canonicalPayloadHash(_episodePayload(admitted)))
    artifactHash = putAdmissionArtifact(artifactRoot, canonicalPayloadBytes(_episodePayload(admitted)))
    if artifactHash != admitted.episodeId:
        raise PolicyEvaluationError("policy episode artifact hash mismatch")
    receipt = issueAdmissionReceipt(
        databasePath,
        artifactRoot,
        privateKey=privateKey,
        kind="policyEpisode",
        subjectHash=admitted.episodeId,
        artifactHash=artifactHash,
        parentReceiptIds=tuple(parentIds),
        ruleId=_EPISODE_RULE_ID,
        ruleVersion=_EPISODE_RULE_VERSION,
        ruleHash=_EPISODE_RULE_HASH,
        issuerId=issuerId,
        issuerKeyId=issuerKeyId,
        issuerExecutableHash=issuerExecutableHash,
        knowledgeAsOf=episode.evaluationKnowledgeAsOf,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency=pathReceipt.frequency,
        stepSpan=pathReceipt.stepSpan,
        maxAdmittedStep=pathReceipt.maxAdmittedStep,
        status="admitted",
        issuedAt=issuedAt,
        trustedIssuers=trustedIssuers,
    )
    _validateEpisodeReceipt(admitted, receipt)
    signed = replace(admitted, episodeReceiptId=receipt.receiptId)
    _validateEpisode(signed)
    return signed


def _episodeFromPayload(episodeId: str, episodeReceiptId: str, payload: dict) -> PolicyOosEpisode:
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
        return PolicyOosEpisode(episodeId=episodeId, episodeReceiptId=episodeReceiptId, **payload)
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
                episode_receipt_id TEXT NOT NULL,
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


def _rowHash(previousHash: str, episodeId: str, originKey: str, episodeReceiptId: str) -> str:
    return sha256(
        b"dartlab.policy-oos-ledger-row.v1\0"
        + previousHash.encode("ascii")
        + episodeId.encode("ascii")
        + originKey.encode("ascii")
        + episodeReceiptId.encode("ascii")
    ).hexdigest()


def appendPolicyOosEpisode(
    databasePath: str | Path,
    episode: PolicyOosEpisode,
    *,
    admissionVerifier: AdmissionVerifier | None = None,
) -> None:
    """검증한 raw episode를 중복 origin 없이 append-only 원장에 추가한다."""

    _validateEpisode(episode)
    database = Path(databasePath)
    if not database.exists():
        raise PolicyEvaluationError("policy OOS ledger is unavailable")
    if episode.admissionStatus == "admitted":
        if admissionVerifier is None:
            raise PolicyEvaluationError("admitted policy episode needs a runtime verifier")
        receipt = admissionVerifier.verify(
            episode.episodeReceiptId,
            expectedSubjectHash=episode.episodeId,
            expectedKind="policyEpisode",
        )
        if receipt.status != "admitted":
            raise PolicyEvaluationError("policy episode receipt is not admitted")
        _validateEpisodeReceipt(episode, receipt)
    with sqlite3.connect(database) as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("SELECT row_hash FROM policy_oos_episodes ORDER BY seq DESC LIMIT 1").fetchone()
        previousHash = str(row[0]) if row is not None else ""
        try:
            connection.execute(
                "INSERT INTO policy_oos_episodes "
                "(episode_id, origin_key, episode_receipt_id, payload_json, previous_row_hash, row_hash) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    episode.episodeId,
                    episode.originKey,
                    episode.episodeReceiptId,
                    canonicalPayloadBytes(_episodePayload(episode)).decode("utf-8"),
                    previousHash,
                    _rowHash(previousHash, episode.episodeId, episode.originKey, episode.episodeReceiptId),
                ),
            )
        except sqlite3.IntegrityError as error:
            raise PolicyEvaluationError("duplicate policy OOS episode or origin") from error


def readPolicyOosLedger(
    databasePath: str | Path,
    *,
    admissionVerifier: AdmissionVerifier | None = None,
) -> PolicyOosLedgerSnapshot:
    """전체 sequence와 row chain 및 episode 내용을 다시 계산해 읽는다."""

    database = Path(databasePath)
    if not database.exists():
        raise PolicyEvaluationError("policy OOS ledger is unavailable")
    try:
        connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
        rows = connection.execute(
            "SELECT seq, episode_id, origin_key, episode_receipt_id, payload_json, previous_row_hash, row_hash "
            "FROM policy_oos_episodes ORDER BY seq"
        ).fetchall()
        connection.close()
    except sqlite3.Error as error:
        raise PolicyEvaluationError("policy OOS ledger is unavailable") from error
    episodes: list[PolicyOosEpisode] = []
    previousHash = ""
    for expectedSequence, row in enumerate(rows, start=1):
        sequence, episodeId, originKey, episodeReceiptId, payloadJson, storedPrevious, storedHash = row
        if sequence != expectedSequence or storedPrevious != previousHash:
            raise PolicyEvaluationError("policy OOS ledger chain mismatch")
        expectedHash = _rowHash(previousHash, str(episodeId), str(originKey), str(episodeReceiptId))
        if storedHash != expectedHash:
            raise PolicyEvaluationError("policy OOS ledger row hash mismatch")
        try:
            payload = json.loads(str(payloadJson))
        except json.JSONDecodeError as error:
            raise PolicyEvaluationError("policy OOS ledger payload is malformed") from error
        episode = _episodeFromPayload(str(episodeId), str(episodeReceiptId), payload)
        _validateEpisode(episode)
        if episode.admissionStatus == "admitted":
            if admissionVerifier is None:
                raise PolicyEvaluationError("admitted policy episode needs a runtime verifier")
            receipt = admissionVerifier.verify(
                episode.episodeReceiptId,
                expectedSubjectHash=episode.episodeId,
                expectedKind="policyEpisode",
            )
            if receipt.status != "admitted":
                raise PolicyEvaluationError("policy episode receipt is not admitted")
            _validateEpisodeReceipt(episode, receipt)
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
        executableHash=episodes[0].executableHash,
        candidateStrategyContractHash=episodes[0].candidateStrategyContractHash,
        baselineStrategyContractHash=episodes[0].baselineStrategyContractHash,
        objectiveContractHash=episodes[0].objectiveContractHash,
        constraintContractHash=episodes[0].constraintContractHash,
        pathRuleHash=episodes[0].pathRuleHash,
        parameterContractHash=episodes[0].parameterContractHash,
        reasons=tuple(reasons),
    )
    return replace(provisional, reportId=canonicalPayloadHash(_reportPayload(provisional)))


def _episodeSeries(snapshot: PolicyOosLedgerSnapshot) -> tuple[PolicyOosEpisode, ...]:
    if not snapshot.episodes or not _validDigest(snapshot.ledgerRoot):
        raise PolicyEvaluationError("policy batch needs a non-empty verified ledger snapshot")
    episodes = tuple(sorted(snapshot.episodes, key=lambda episode: (episode.originAsOf, episode.originOrdinal)))
    for episode in episodes:
        _validateEpisode(episode)
        if episode.admissionStatus != "admitted":
            raise PolicyEvaluationError("policy batch accepts only admitted episodes")
    ordinals = [episode.originOrdinal for episode in episodes]
    if ordinals != list(range(ordinals[0], ordinals[0] + len(ordinals))):
        raise PolicyEvaluationError("policy batch origin ordinal gap")
    if len({episode.originAsOf for episode in episodes}) != len(episodes):
        raise PolicyEvaluationError("policy batch contains duplicate origins")
    contractFields = (
        "executableHash",
        "baselineStrategyContractHash",
        "candidateStrategyContractHash",
        "objectiveContractHash",
        "constraintContractHash",
        "pathRuleId",
        "pathRuleVersion",
        "pathRuleHash",
        "parameterContractHash",
    )
    for fieldName in contractFields:
        if len({getattr(episode, fieldName) for episode in episodes}) != 1:
            raise PolicyEvaluationError(f"policy batch contract drift: {fieldName}")
    return episodes


def sealPolicyOosBatch(
    snapshot: PolicyOosLedgerSnapshot,
    databasePath: str | Path,
    artifactRoot: str | Path,
    *,
    privateKey: bytes,
    issuerId: str,
    issuerKeyId: str,
    issuerExecutableHash: str,
    issuedAt: str,
    trustedIssuers: Mapping[str, TrustedIssuer],
) -> PolicyEpisodeBatch:
    """서명된 episode 집합과 append-only 원장의 현재 checkpoint를 하나의 batch로 동결한다."""

    _validateIssuerKey(
        privateKey,
        issuerId=issuerId,
        issuerKeyId=issuerKeyId,
        trustedIssuers=trustedIssuers,
    )
    episodes = _episodeSeries(snapshot)
    verifier = AdmissionVerifier(databasePath, artifactRoot, trustedIssuers)
    pathContracts: set[tuple[str, int, int, str, str, str]] = set()
    episodeReceiptIds: list[str] = []
    for episode in episodes:
        receipt = _requireReceipt(
            verifier,
            episode.episodeReceiptId,
            kind="policyEpisode",
            subjectHash=episode.episodeId,
            statuses={"admitted"},
        )
        _validateEpisodeReceipt(episode, receipt)
        pathReceipt = _requireReceipt(
            verifier,
            episode.pathAdmissionReceiptId,
            kind="pathSet",
            subjectHash=episode.pathContentHash,
            statuses={"admitted"},
        )
        _validateEpisodePathArtifact(episode, pathReceipt, verifier)
        pathContracts.add(
            (
                pathReceipt.frequency,
                pathReceipt.stepSpan,
                pathReceipt.maxAdmittedStep,
                pathReceipt.ruleId,
                pathReceipt.ruleVersion,
                pathReceipt.ruleHash,
            )
        )
        episodeReceiptIds.append(receipt.receiptId)
    if len(pathContracts) != 1:
        raise PolicyEvaluationError("policy batch path frequency or horizon drift")
    frequency, stepSpan, maxAdmittedStep, _, _, _ = next(iter(pathContracts))
    knowledgeAsOf = max(_dateText(episode.evaluationKnowledgeAsOf, "evaluationKnowledgeAsOf") for episode in episodes)
    if _dateText(issuedAt, "batch issuedAt") < knowledgeAsOf:
        raise PolicyEvaluationError("policy batch cannot be issued before its evidence knowledge")
    provisional = PolicyEpisodeBatch(
        batchId="",
        batchReceiptId="",
        ledgerRoot=snapshot.ledgerRoot,
        checkpointSequence=len(episodes),
        checkpointRowHash=snapshot.ledgerRoot,
        episodeIds=tuple(episode.episodeId for episode in episodes),
        episodeReceiptIds=tuple(episodeReceiptIds),
        originStart=episodes[0].originAsOf,
        originEnd=episodes[-1].originAsOf,
        knowledgeAsOf=knowledgeAsOf,
        executableHash=episodes[0].executableHash,
        baselineStrategyContractHash=episodes[0].baselineStrategyContractHash,
        candidateStrategyContractHash=episodes[0].candidateStrategyContractHash,
        objectiveContractHash=episodes[0].objectiveContractHash,
        constraintContractHash=episodes[0].constraintContractHash,
        pathRuleHash=episodes[0].pathRuleHash,
        parameterContractHash=episodes[0].parameterContractHash,
    )
    batchId = canonicalPayloadHash(_batchPayload(provisional))
    unsigned = replace(provisional, batchId=batchId)
    artifactHash = putAdmissionArtifact(artifactRoot, canonicalPayloadBytes(_batchPayload(unsigned)))
    if artifactHash != batchId:
        raise PolicyEvaluationError("policy batch artifact hash mismatch")
    receipt = issueAdmissionReceipt(
        databasePath,
        artifactRoot,
        privateKey=privateKey,
        kind="policyEpisodeBatch",
        subjectHash=batchId,
        artifactHash=artifactHash,
        parentReceiptIds=tuple(episodeReceiptIds),
        ruleId=_BATCH_RULE_ID,
        ruleVersion=_BATCH_RULE_VERSION,
        ruleHash=_BATCH_RULE_HASH,
        issuerId=issuerId,
        issuerKeyId=issuerKeyId,
        issuerExecutableHash=issuerExecutableHash,
        knowledgeAsOf=knowledgeAsOf,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency=frequency,
        stepSpan=stepSpan,
        maxAdmittedStep=maxAdmittedStep,
        status="admitted",
        issuedAt=issuedAt,
        trustedIssuers=trustedIssuers,
    )
    _requireRule(receipt, ruleId=_BATCH_RULE_ID, ruleVersion=_BATCH_RULE_VERSION, ruleHash=_BATCH_RULE_HASH)
    if receipt.parentReceiptIds != tuple(episodeReceiptIds):
        raise PolicyEvaluationError("policy batch receipt parent mismatch")
    batch = replace(unsigned, batchReceiptId=receipt.receiptId)
    _validateBatch(batch)
    return batch


def issuePolicyEvaluationCertificate(
    snapshot: PolicyOosLedgerSnapshot,
    batch: PolicyEpisodeBatch,
    spec: PolicyEvaluationSpec,
    databasePath: str | Path,
    artifactRoot: str | Path,
    *,
    privateKey: bytes,
    issuerId: str,
    issuerKeyId: str,
    issuerExecutableHash: str,
    issuedAt: str,
    trustedIssuers: Mapping[str, TrustedIssuer],
) -> PolicyEvaluationCertificate:
    """동결 batch의 raw rows를 내부 재계산해 채택 또는 기각 인증서를 발행한다."""

    _validateIssuerKey(
        privateKey,
        issuerId=issuerId,
        issuerKeyId=issuerKeyId,
        trustedIssuers=trustedIssuers,
    )
    _validateBatch(batch)
    episodes = _episodeSeries(snapshot)
    if (
        batch.ledgerRoot != snapshot.ledgerRoot
        or batch.checkpointSequence != len(episodes)
        or batch.checkpointRowHash != snapshot.ledgerRoot
        or batch.episodeIds != tuple(episode.episodeId for episode in episodes)
        or batch.episodeReceiptIds != tuple(episode.episodeReceiptId for episode in episodes)
    ):
        raise PolicyEvaluationError("policy batch does not match the ledger checkpoint")
    verifier = AdmissionVerifier(databasePath, artifactRoot, trustedIssuers)
    batchReceipt = _requireReceipt(
        verifier,
        batch.batchReceiptId,
        kind="policyEpisodeBatch",
        subjectHash=batch.batchId,
        statuses={"admitted"},
    )
    _requireRule(
        batchReceipt,
        ruleId=_BATCH_RULE_ID,
        ruleVersion=_BATCH_RULE_VERSION,
        ruleHash=_BATCH_RULE_HASH,
    )
    if (
        batchReceipt.artifactHash != batch.batchId
        or batchReceipt.parentReceiptIds != batch.episodeReceiptIds
        or batchReceipt.knowledgeAsOf != batch.knowledgeAsOf
    ):
        raise PolicyEvaluationError("policy batch receipt artifact mismatch")
    report = evaluatePolicyOos(snapshot, spec)
    contractValues = (
        report.executableHash,
        report.baselineStrategyContractHash,
        report.candidateStrategyContractHash,
        report.objectiveContractHash,
        report.constraintContractHash,
        report.pathRuleHash,
        report.parameterContractHash,
    )
    batchValues = (
        batch.executableHash,
        batch.baselineStrategyContractHash,
        batch.candidateStrategyContractHash,
        batch.objectiveContractHash,
        batch.constraintContractHash,
        batch.pathRuleHash,
        batch.parameterContractHash,
    )
    if contractValues != batchValues or report.episodeIds != batch.episodeIds:
        raise PolicyEvaluationError("policy evaluation report drifted from the sealed batch")
    status = "policyAdmitted" if report.status == "statisticallyEligible" else "rejected"
    if _dateText(issuedAt, "certificate issuedAt") < batch.knowledgeAsOf:
        raise PolicyEvaluationError("policy certificate cannot be issued before its batch knowledge")
    provisional = PolicyEvaluationCertificate(
        certificateId="",
        certificateReceiptId="",
        batchId=batch.batchId,
        batchReceiptId=batch.batchReceiptId,
        knowledgeAsOf=batch.knowledgeAsOf,
        executableHash=batch.executableHash,
        baselineStrategyContractHash=batch.baselineStrategyContractHash,
        candidateStrategyContractHash=batch.candidateStrategyContractHash,
        objectiveContractHash=batch.objectiveContractHash,
        constraintContractHash=batch.constraintContractHash,
        pathRuleHash=batch.pathRuleHash,
        parameterContractHash=batch.parameterContractHash,
        spec=spec,
        report=report,
        status=status,
    )
    certificateId = canonicalPayloadHash(_certificatePayload(provisional))
    unsigned = replace(provisional, certificateId=certificateId)
    artifactHash = putAdmissionArtifact(artifactRoot, canonicalPayloadBytes(_certificatePayload(unsigned)))
    if artifactHash != certificateId:
        raise PolicyEvaluationError("policy certificate artifact hash mismatch")
    receipt = issueAdmissionReceipt(
        databasePath,
        artifactRoot,
        privateKey=privateKey,
        kind="policyEvaluation",
        subjectHash=batch.candidateStrategyContractHash,
        artifactHash=artifactHash,
        parentReceiptIds=(batch.batchReceiptId,),
        ruleId=_CERTIFICATE_RULE_ID,
        ruleVersion=_CERTIFICATE_RULE_VERSION,
        ruleHash=_CERTIFICATE_RULE_HASH,
        issuerId=issuerId,
        issuerKeyId=issuerKeyId,
        issuerExecutableHash=issuerExecutableHash,
        knowledgeAsOf=batch.knowledgeAsOf,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency=batchReceipt.frequency,
        stepSpan=batchReceipt.stepSpan,
        maxAdmittedStep=batchReceipt.maxAdmittedStep,
        status=status,
        issuedAt=issuedAt,
        trustedIssuers=trustedIssuers,
    )
    _requireRule(
        receipt,
        ruleId=_CERTIFICATE_RULE_ID,
        ruleVersion=_CERTIFICATE_RULE_VERSION,
        ruleHash=_CERTIFICATE_RULE_HASH,
    )
    certificate = replace(unsigned, certificateReceiptId=receipt.receiptId)
    _validateCertificate(certificate)
    return certificate


def validatePolicyEvaluationCertificate(
    snapshot: PolicyOosLedgerSnapshot,
    batch: PolicyEpisodeBatch,
    certificate: PolicyEvaluationCertificate,
    admissionVerifier: AdmissionVerifier,
    *,
    decisionAsOf: str,
    executableHash: str,
    baselineStrategyContractHash: str,
    candidateStrategyContractHash: str,
    objectiveContractHash: str,
    constraintContractHash: str,
    pathRuleHash: str,
    parameterContractHash: str,
    pathFrequency: str,
    pathStepSpan: int,
    pathHorizon: int,
) -> PolicyEvaluationReport:
    """현재 의사결정 계약과 원장 raw rows에 대해 policyAdmitted 인증서를 완전 재검증한다."""

    _validateBatch(batch)
    _validateCertificate(certificate)
    episodes = _episodeSeries(snapshot)
    if certificate.status != "policyAdmitted":
        raise PolicyEvaluationError("policy evaluation certificate is not admitted")
    if (
        batch.ledgerRoot != snapshot.ledgerRoot
        or batch.checkpointSequence != len(episodes)
        or batch.episodeIds != tuple(episode.episodeId for episode in episodes)
        or batch.episodeReceiptIds != tuple(episode.episodeReceiptId for episode in episodes)
    ):
        raise PolicyEvaluationError("policy evaluation ledger checkpoint mismatch")
    batchReceipt = _requireReceipt(
        admissionVerifier,
        batch.batchReceiptId,
        kind="policyEpisodeBatch",
        subjectHash=batch.batchId,
        statuses={"admitted"},
    )
    certificateReceipt = _requireReceipt(
        admissionVerifier,
        certificate.certificateReceiptId,
        kind="policyEvaluation",
        subjectHash=candidateStrategyContractHash,
        statuses={"policyAdmitted"},
    )
    _requireRule(
        batchReceipt,
        ruleId=_BATCH_RULE_ID,
        ruleVersion=_BATCH_RULE_VERSION,
        ruleHash=_BATCH_RULE_HASH,
    )
    _requireRule(
        certificateReceipt,
        ruleId=_CERTIFICATE_RULE_ID,
        ruleVersion=_CERTIFICATE_RULE_VERSION,
        ruleHash=_CERTIFICATE_RULE_HASH,
    )
    if (
        batchReceipt.artifactHash != batch.batchId
        or batchReceipt.parentReceiptIds != batch.episodeReceiptIds
        or batchReceipt.knowledgeAsOf != batch.knowledgeAsOf
        or certificateReceipt.artifactHash != certificate.certificateId
        or certificate.batchId != batch.batchId
        or certificate.batchReceiptId != batch.batchReceiptId
        or certificateReceipt.parentReceiptIds != (batch.batchReceiptId,)
        or certificate.knowledgeAsOf != batch.knowledgeAsOf
        or certificateReceipt.knowledgeAsOf != certificate.knowledgeAsOf
        or batchReceipt.frequency != pathFrequency
        or certificateReceipt.frequency != pathFrequency
        or batchReceipt.stepSpan != pathStepSpan
        or certificateReceipt.stepSpan != pathStepSpan
        or batchReceipt.maxAdmittedStep != pathHorizon
        or certificateReceipt.maxAdmittedStep != pathHorizon
    ):
        raise PolicyEvaluationError("policy evaluation certificate lineage mismatch")
    decision = _dateText(decisionAsOf, "decisionAsOf")
    if _dateText(certificateReceipt.issuedAt, "certificate issuedAt") > decision:
        raise PolicyEvaluationError("policy evaluation certificate was unavailable at the decision")
    currentContracts = (
        executableHash,
        baselineStrategyContractHash,
        candidateStrategyContractHash,
        objectiveContractHash,
        constraintContractHash,
        pathRuleHash,
        parameterContractHash,
    )
    certificateContracts = (
        certificate.executableHash,
        certificate.baselineStrategyContractHash,
        certificate.candidateStrategyContractHash,
        certificate.objectiveContractHash,
        certificate.constraintContractHash,
        certificate.pathRuleHash,
        certificate.parameterContractHash,
    )
    if currentContracts != certificateContracts:
        raise PolicyEvaluationError("policy evaluation certificate does not bind the current decision contract")
    report = evaluatePolicyOos(snapshot, certificate.spec)
    if report != certificate.report or report.status != "statisticallyEligible":
        raise PolicyEvaluationError("policy evaluation certificate raw-statistic replay mismatch")
    if artifactPath(admissionVerifier.artifactRoot, batch.batchId).read_bytes() != canonicalPayloadBytes(
        _batchPayload(batch)
    ):
        raise PolicyEvaluationError("policy episode batch artifact content mismatch")
    if artifactPath(admissionVerifier.artifactRoot, certificate.certificateId).read_bytes() != canonicalPayloadBytes(
        _certificatePayload(certificate)
    ):
        raise PolicyEvaluationError("policy evaluation certificate artifact content mismatch")
    return report
