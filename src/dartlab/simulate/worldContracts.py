"""Contract digests, signable admission artifacts, and law certificates.

이 모듈은 "무엇을 서명 대상으로 삼는가"만 정한다. 전략 계약 hash, 경로 집합 아티팩트,
법칙 인증서는 모두 실행기 바깥(감사자, 서명 발급기, admission 레지스트리)에서도 그대로
다시 계산돼야 하는 값이라, 실행 경로와 같은 파일에 있으면 실행 사정에 끌려 바뀌기 쉽다.
자료형(`worldTypes`)만 알고 컴파일러나 실행기는 모르는 자리에 두어 그 결속을 끊는다.
"""

from __future__ import annotations

import json
import math
from dataclasses import replace
from hashlib import sha256
from typing import Mapping

from dartlab.simulate.admissionRegistry import (
    AdmissionRegistryError,
    AdmissionVerifier,
    artifactPath,
)
from dartlab.simulate.worldTypes import (
    LAW_CERTIFICATE_STATUS_SET,
    ActionSpec,
    ConstraintSpec,
    LawCertificate,
    LawSpec,
    ObjectiveSpec,
    PathTrace,
    ScenarioPath,
    SimulationSpecError,
    StrategySpec,
    WorldState,
    _canonical,
    _comparableDate,
    _stableHash,
    _validDigest,
)

LAW_EVIDENCE_RECEIPT_KIND = "lawEvidence"
ACTION_EVIDENCE_RECEIPT_KIND = "actionEvidence"
_EVIDENCE_SOURCE_RECEIPT_KINDS = {
    "dataVintage",
    "providerObservationBatch",
    "pointInTimeState",
    "initialState",
}


def strategyContractHash(strategy: StrategySpec) -> str:
    """행동 일정 또는 정책 실행물과 버전, 근거를 하나의 전략 계약 hash로 묶는다.

    Args:
        strategy: 정적 행동 일정 또는 폐루프 정책 명세.

    Returns:
        전략 계약의 SHA-256 digest.

    Raises:
        TypeError: 전략 명세를 정규 JSON으로 직렬화할 수 없는 경우.

    Example:
        ``digest = strategyContractHash(strategy)``
    """

    return _stableHash({"strategy": strategy})


def objectiveContractHash(objective: ObjectiveSpec) -> str:
    """목적 지표, 기간 축약, 방향, 위험 계약을 재사용 가능한 hash로 묶는다.

    Args:
        objective: 평가 목적 명세.

    Returns:
        목적 계약의 SHA-256 digest.

    Raises:
        TypeError: 목적 명세를 정규 JSON으로 직렬화할 수 없는 경우.

    Example:
        ``digest = objectiveContractHash(objective)``
    """

    return _stableHash({"objective": objective})


def constraintContractHash(constraints: tuple[ConstraintSpec, ...]) -> str:
    """모든 hard constraint의 순서와 임계 계약을 하나의 hash로 묶는다.

    Args:
        constraints: 실행 중 강제할 제약 명세 묶음.

    Returns:
        제약 계약의 SHA-256 digest.

    Raises:
        TypeError: 제약 명세를 정규 JSON으로 직렬화할 수 없는 경우.

    Example:
        ``digest = constraintContractHash(constraints)``
    """

    return _stableHash({"constraints": constraints})


def dataVintageHashFor(initial: WorldState, paths: tuple[ScenarioPath, ...]) -> str:
    """Bind the exact initial state and ordered future path set.

    Args:
        initial: Current or historical decision-time world state.
        paths: Ordered common future paths used by every strategy.

    Returns:
        SHA-256 digest used by ``SimulationRun.dataVintageHash``.

    Raises:
        SimulationSpecError: Raised by the caller if inputs violate runtime contracts.

    Example:
        ``digest = dataVintageHashFor(initial, paths)``
    """

    return _stableHash({"initial": initial, "paths": paths})


def traceRootFor(traces: tuple[PathTrace, ...]) -> str:
    """보존된 전체 trace 순서에서 실행기와 동일한 chain root를 다시 계산한다.

    Args:
        traces: 보존된 경로 실행 trace 묶음.

    Returns:
        trace 개수와 순서 체인을 묶은 SHA-256 digest.

    Raises:
        TypeError: trace를 정규 JSON으로 직렬화할 수 없는 경우.

    Example:
        ``root = traceRootFor(run.retainedTraces)``
    """

    traceChain = sha256()
    for trace in traces:
        traceChain.update(bytes.fromhex(_stableHash({"trace": trace})))
    return _stableHash({"traceCount": len(traces), "traceChain": traceChain.hexdigest()})


def _pathSetPayload(paths: tuple[ScenarioPath, ...]) -> dict:
    return {
        "paths": [
            {
                "pathId": path.pathId,
                "steps": [dict(step) for step in path.steps],
                "weight": path.weight,
                "weightKind": path.weightKind,
                "refs": path.refs,
                "frequency": path.frequency,
                "stepSpan": path.stepSpan,
                "certificateId": path.certificateId,
                "validationStatus": path.validationStatus,
                "maxAdmittedStep": path.maxAdmittedStep,
                "parameterDraws": path.parameterDraws,
                "parameterDrawReceipt": path.parameterDrawReceipt,
                "knowledgeAsOf": path.knowledgeAsOf,
                "historyStatus": path.historyStatus,
                "vintage": path.vintage,
            }
            for path in paths
        ]
    }


def pathSetAdmissionArtifact(paths: tuple[ScenarioPath, ...]) -> bytes:
    """서명 대상 경로 집합을 순서 보존 정규 JSON 아티팩트로 직렬화한다.

    Args:
        paths: admission 대상 scenario path 묶음.

    Returns:
        정규 JSON bytes 아티팩트.

    Raises:
        TypeError: path payload를 정규 JSON으로 직렬화할 수 없는 경우.

    Example:
        ``artifact = pathSetAdmissionArtifact(paths)``
    """

    return json.dumps(
        _canonical(_pathSetPayload(paths)),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def pathSetAdmissionSubjectHash(paths: tuple[ScenarioPath, ...]) -> str:
    """경로 admission 영수증이 서명해야 할 정확한 subject hash를 반환한다.

    Args:
        paths: admission 대상 scenario path 묶음.

    Returns:
        경로 집합 아티팩트의 SHA-256 digest.

    Raises:
        TypeError: path payload를 정규 JSON으로 직렬화할 수 없는 경우.

    Example:
        ``subjectHash = pathSetAdmissionSubjectHash(paths)``
    """

    return sha256(pathSetAdmissionArtifact(paths)).hexdigest()


def _pathSetContentHash(paths: tuple[ScenarioPath, ...]) -> str:
    return pathSetAdmissionSubjectHash(paths)


def bindAdmittedPathContent(paths: tuple[ScenarioPath, ...]) -> tuple[ScenarioPath, ...]:
    """admitted 경로 집합의 실제 내용과 순서를 하나의 공유 hash로 묶는다.

    Args:
        paths: admitted 상태의 경로 집합.

    Returns:
        같은 admission content hash를 가진 경로 집합.

    Raises:
        SimulationSpecError: 경로가 비었거나 admitted, cutoff, history 계약을 만족하지 않는 경우.

    Example:
        ``boundPaths = bindAdmittedPathContent(paths)``
    """

    if not paths or any(path.validationStatus != "admitted" for path in paths):
        raise SimulationSpecError("only a nonempty admitted path set can be content-bound")
    if any(_comparableDate(path.knowledgeAsOf) is None for path in paths):
        raise SimulationSpecError("admitted paths need a comparable knowledge cutoff")
    if any(path.historyStatus != "asKnown" for path in paths):
        raise SimulationSpecError("admitted paths need as-known history")
    contentHash = _pathSetContentHash(paths)
    return tuple(replace(path, admissionContentHash=contentHash) for path in paths)


def bindPathAdmissionReceipt(paths: tuple[ScenarioPath, ...], receiptId: str) -> tuple[ScenarioPath, ...]:
    """내용 결속을 바꾸지 않고 경로 집합 전체에 하나의 서명 영수증을 연결한다.

    Args:
        paths: content-bound admitted 경로 집합.
        receiptId: 경로 집합 admission receipt id.

    Returns:
        같은 admission receipt id를 가진 경로 집합.

    Raises:
        SimulationSpecError: receipt id 또는 content binding이 유효하지 않은 경우.

    Example:
        ``boundPaths = bindPathAdmissionReceipt(paths, receiptId)``
    """

    if not _validDigest(receiptId):
        raise SimulationSpecError("path admission receipt identifier is invalid")
    if not paths or any(path.validationStatus != "admitted" for path in paths):
        raise SimulationSpecError("only admitted paths can bind an admission receipt")
    contentHashes = {path.admissionContentHash for path in paths}
    if len(contentHashes) != 1 or next(iter(contentHashes)) != _pathSetContentHash(paths):
        raise SimulationSpecError("path admission receipt needs exact content binding")
    return tuple(replace(path, admissionReceiptId=receiptId) for path in paths)


def _admissionArtifactBytes(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        _canonical(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _receiptArtifactPayload(admissionVerifier: AdmissionVerifier, artifactHash: str) -> dict:
    try:
        payload = json.loads(artifactPath(admissionVerifier.artifactRoot, artifactHash).read_text(encoding="utf-8"))
    except (OSError, TypeError, UnicodeError, json.JSONDecodeError, AdmissionRegistryError) as error:
        raise SimulationSpecError("evidence admission artifact is malformed") from error
    if not isinstance(payload, dict):
        raise SimulationSpecError("evidence admission artifact is malformed")
    return payload


def _verifyEvidenceSources(receipt, admissionVerifier: AdmissionVerifier) -> None:
    if not receipt.parentReceiptIds:
        raise SimulationSpecError("evidence admission needs source receipts")
    cutoff = _comparableDate(receipt.knowledgeAsOf)
    if cutoff is None:
        raise SimulationSpecError("evidence admission knowledge cutoff is invalid")
    try:
        parents = tuple(admissionVerifier.verify(receiptId) for receiptId in receipt.parentReceiptIds)
    except AdmissionRegistryError as error:
        raise SimulationSpecError("evidence source receipt verification failed") from error
    if any(parent.status not in {"verifiedVintage", "admitted", "policyAdmitted"} for parent in parents):
        raise SimulationSpecError("evidence source receipt is not admitted")
    sources = tuple(parent for parent in parents if parent.kind in _EVIDENCE_SOURCE_RECEIPT_KINDS)
    if not sources:
        raise SimulationSpecError("evidence admission needs a typed source receipt")
    sourceCutoffs = tuple(_comparableDate(source.knowledgeAsOf) for source in sources)
    if any(sourceCutoff is None or sourceCutoff > cutoff for sourceCutoff in sourceCutoffs):
        raise SimulationSpecError("evidence source is newer than its knowledge cutoff")


def _actionEvidencePayload(
    action: ActionSpec,
    *,
    knowledgeAsOf: str,
    frequency: str,
    stepSpan: int,
    maxAdmittedStep: int,
) -> dict:
    return {
        "protocol": "action-evidence-v1",
        "action": {
            "actionId": action.actionId,
            "unit": action.unit,
            "lower": action.lower,
            "upper": action.upper,
            "leadSteps": action.leadSteps,
            "costPerUnit": action.costPerUnit,
            "effectEvidence": action.effectEvidence,
            "provenance": action.provenance,
        },
        "knowledgeAsOf": knowledgeAsOf,
        "frequency": frequency,
        "stepSpan": stepSpan,
        "maxAdmittedStep": maxAdmittedStep,
    }


def actionEvidenceAdmissionArtifact(
    action: ActionSpec,
    *,
    knowledgeAsOf: str,
    frequency: str,
    stepSpan: int = 1,
    maxAdmittedStep: int,
) -> bytes:
    """Return the exact artifact a typed identified-action receipt must sign."""

    cutoff = _comparableDate(knowledgeAsOf)
    if (
        action.effectEvidence != "identifiedIntervention"
        or action.certificateId
        or cutoff is None
        or not frequency
        or stepSpan < 1
        or maxAdmittedStep < 1
    ):
        raise SimulationSpecError("identified action evidence artifact contract is invalid")
    return _admissionArtifactBytes(
        _actionEvidencePayload(
            action,
            knowledgeAsOf=cutoff,
            frequency=frequency,
            stepSpan=stepSpan,
            maxAdmittedStep=maxAdmittedStep,
        )
    )


def bindActionEvidenceReceipt(
    action: ActionSpec,
    receiptId: str,
    admissionVerifier: AdmissionVerifier,
) -> ActionSpec:
    """Bind an identified action only after verifying its typed signed receipt and sources."""

    if action.effectEvidence != "identifiedIntervention" or action.certificateId or not _validDigest(receiptId):
        raise SimulationSpecError("identified action receipt binding is invalid")
    try:
        receipt = admissionVerifier.verify(receiptId, expectedKind=ACTION_EVIDENCE_RECEIPT_KIND)
    except AdmissionRegistryError as error:
        raise SimulationSpecError("identified action receipt verification failed") from error
    if receipt.status != "admitted" or receipt.artifactHash != receipt.subjectHash:
        raise SimulationSpecError("identified action receipt is not admitted")
    _verifyEvidenceSources(receipt, admissionVerifier)
    expected = _actionEvidencePayload(
        action,
        knowledgeAsOf=receipt.knowledgeAsOf,
        frequency=receipt.frequency,
        stepSpan=receipt.stepSpan,
        maxAdmittedStep=receipt.maxAdmittedStep,
    )
    if _receiptArtifactPayload(admissionVerifier, receipt.artifactHash) != _canonical(expected):
        raise SimulationSpecError("identified action receipt contract mismatch")
    return replace(action, certificateId=receipt.receiptId)


def _validateActionEvidenceReceipt(
    action: ActionSpec,
    admissionVerifier: AdmissionVerifier,
    *,
    frequency: str,
    stepSpan: int,
):
    unbound = replace(action, certificateId="")
    rebound = bindActionEvidenceReceipt(unbound, action.certificateId, admissionVerifier)
    try:
        receipt = admissionVerifier.verify(action.certificateId, expectedKind=ACTION_EVIDENCE_RECEIPT_KIND)
    except AdmissionRegistryError as error:
        raise SimulationSpecError("identified action receipt verification failed") from error
    if receipt.frequency != frequency or receipt.stepSpan != stepSpan or receipt.maxAdmittedStep < 1:
        raise SimulationSpecError(f"action evidence step contract mismatch: {action.actionId}")
    if rebound != action:
        raise SimulationSpecError(f"action evidence binding mismatch: {action.actionId}")
    return receipt


def _lawContractPayload(law: LawSpec) -> dict:
    return {
        "outputs": law.outputs,
        "priorInputs": law.priorInputs,
        "currentInputs": law.currentInputs,
        "shockInputs": law.shockInputs,
        "actionInputs": law.actionInputs,
        "pathParameterInputs": law.pathParameterInputs,
        "pathParameterUnits": law.pathParameterUnits,
        "usesActionCost": law.usesActionCost,
    }


def _lawCertificatePayload(certificate: LawCertificate) -> dict:
    return {
        "lawId": certificate.lawId,
        "lawVersion": certificate.lawVersion,
        "evidenceKind": certificate.evidenceKind,
        "contractHash": certificate.contractHash,
        "parameterHash": certificate.parameterHash,
        "executableHash": certificate.executableHash,
        "evidenceHash": certificate.evidenceHash,
        "knowledgeAsOf": certificate.knowledgeAsOf,
        "historyStatus": certificate.historyStatus,
        "frequency": certificate.frequency,
        "stepSpan": certificate.stepSpan,
        "maxAdmittedStep": certificate.maxAdmittedStep,
        "status": certificate.status,
        "rules": certificate.rules,
        "evidenceReceiptId": certificate.evidenceReceiptId,
    }


def _normalizeEvidenceRows(evidenceRows: tuple[Mapping[str, object], ...]) -> list[dict]:
    """검증 행을 형태 검사와 통과 판정까지 마친 정렬된 정규 행으로 바꾼다."""

    normalized: list[dict] = []
    required = {"step", "metric", "estimate", "threshold", "operator"}
    for row in evidenceRows:
        if not required.issubset(row):
            raise SimulationSpecError("law evidence row is incomplete")
        rawStep = row["step"]
        rawEstimate = row["estimate"]
        rawThreshold = row["threshold"]
        if isinstance(rawStep, bool) or not isinstance(rawStep, (int, str)):
            raise SimulationSpecError("law evidence row step is invalid")
        if isinstance(rawEstimate, bool) or not isinstance(rawEstimate, (int, float, str)):
            raise SimulationSpecError("law evidence row estimate is invalid")
        if isinstance(rawThreshold, bool) or not isinstance(rawThreshold, (int, float, str)):
            raise SimulationSpecError("law evidence row threshold is invalid")
        step = int(rawStep)
        operator = str(row["operator"])
        if step < 1 or not str(row["metric"]) or operator not in {"gt", "ge", "lt", "le"}:
            raise SimulationSpecError("law evidence row is invalid")
        estimate = float(rawEstimate)
        threshold = float(rawThreshold)
        if not math.isfinite(estimate) or not math.isfinite(threshold):
            raise SimulationSpecError("law evidence row is not finite")
        passed = {
            "gt": estimate > threshold,
            "ge": estimate >= threshold,
            "lt": estimate < threshold,
            "le": estimate <= threshold,
        }[operator]
        normalized.append(
            {
                "step": step,
                "metric": str(row["metric"]),
                "estimate": estimate,
                "threshold": threshold,
                "operator": operator,
                "passed": passed,
            }
        )
    normalized.sort(key=lambda row: (row["step"], row["metric"]))
    return normalized


def _admittedEvidenceHorizon(normalized: list[dict]) -> int:
    """step 1 부터 끊기지 않고 전부 통과한 구간의 마지막 step을 돌려준다."""

    maxObserved = max((int(row["step"]) for row in normalized), default=0)
    maxAdmittedStep = 0
    for step in range(1, maxObserved + 1):
        stepRows = [row for row in normalized if row["step"] == step]
        if not stepRows or not all(bool(row["passed"]) for row in stepRows):
            break
        maxAdmittedStep = step
    return maxAdmittedStep


def _lawEvidencePayload(
    law: LawSpec,
    normalized: list[dict],
    *,
    knowledgeAsOf: str,
    historyStatus: str,
    frequency: str,
    stepSpan: int,
    rules: str,
) -> dict:
    return {
        "protocol": "law-evidence-v1",
        "lawId": law.lawId,
        "lawVersion": law.version,
        "evidenceKind": law.evidenceKind,
        "contractHash": _stableHash(_lawContractPayload(law)),
        "parameterHash": _stableHash({"parameters": law.parameters}),
        "executableHash": _stableHash({"fn": law.fn}),
        "rows": normalized,
        "knowledgeAsOf": knowledgeAsOf,
        "historyStatus": historyStatus,
        "frequency": frequency,
        "stepSpan": stepSpan,
        "maxAdmittedStep": _admittedEvidenceHorizon(normalized),
        "rules": rules,
    }


def lawEvidenceAdmissionArtifact(
    law: LawSpec,
    *,
    evidenceRows: tuple[Mapping[str, object], ...],
    knowledgeAsOf: str,
    historyStatus: str,
    frequency: str,
    stepSpan: int = 1,
    rules: str,
) -> bytes:
    """Return the exact artifact a typed transition-law evidence receipt must sign."""

    if law.evidenceKind not in {"measuredAssociation", "identifiedIntervention"}:
        raise SimulationSpecError("only measured or identified laws can have evidence artifacts")
    cutoff = _comparableDate(knowledgeAsOf)
    if cutoff is None or not rules or not frequency or stepSpan < 1:
        raise SimulationSpecError("law evidence artifact contract is invalid")
    normalized = _normalizeEvidenceRows(evidenceRows)
    return _admissionArtifactBytes(
        _lawEvidencePayload(
            law,
            normalized,
            knowledgeAsOf=cutoff,
            historyStatus=historyStatus,
            frequency=frequency,
            stepSpan=stepSpan,
            rules=rules,
        )
    )


def _verifyLawEvidenceReceipt(
    law: LawSpec,
    certificate: LawCertificate,
    admissionVerifier: AdmissionVerifier,
) -> None:
    try:
        receipt = admissionVerifier.verify(
            certificate.evidenceReceiptId,
            expectedKind=LAW_EVIDENCE_RECEIPT_KIND,
        )
    except AdmissionRegistryError as error:
        raise SimulationSpecError(f"law evidence receipt verification failed: {law.lawId}") from error
    if receipt.artifactHash != receipt.subjectHash:
        raise SimulationSpecError(f"law evidence receipt artifact mismatch: {law.lawId}")
    _verifyEvidenceSources(receipt, admissionVerifier)
    payload = _receiptArtifactPayload(admissionVerifier, receipt.artifactHash)
    rows = payload.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise SimulationSpecError(f"law evidence rows are malformed: {law.lawId}")
    normalized = _normalizeEvidenceRows(tuple(rows))
    expectedPayload = _lawEvidencePayload(
        law,
        normalized,
        knowledgeAsOf=certificate.knowledgeAsOf,
        historyStatus=certificate.historyStatus,
        frequency=certificate.frequency,
        stepSpan=certificate.stepSpan,
        rules=certificate.rules,
    )
    if payload != _canonical(expectedPayload):
        raise SimulationSpecError(f"law evidence receipt contract mismatch: {law.lawId}")
    expectedStatus = (
        "rejected"
        if certificate.maxAdmittedStep < 1
        else "admitted"
        if certificate.historyStatus == "asKnown"
        else "retrospectiveOnly"
    )
    if (
        receipt.status != expectedStatus
        or certificate.status != expectedStatus
        or receipt.knowledgeAsOf != certificate.knowledgeAsOf
        or receipt.frequency != certificate.frequency
        or receipt.stepSpan != certificate.stepSpan
        or receipt.maxAdmittedStep != certificate.maxAdmittedStep
        or certificate.evidenceHash != _stableHash({"rows": normalized})
    ):
        raise SimulationSpecError(f"law evidence receipt binding mismatch: {law.lawId}")


def issueLawCertificate(
    law: LawSpec,
    *,
    evidenceRows: tuple[Mapping[str, object], ...],
    knowledgeAsOf: str,
    historyStatus: str,
    frequency: str,
    stepSpan: int = 1,
    rules: str,
    evidenceReceiptId: str = "",
    admissionVerifier: AdmissionVerifier | None = None,
) -> LawCertificate:
    """검증 행의 연속 통과 지평과 typed evidence receipt를 법칙 실행물에 바인딩한다.

    Args:
        law: 인증할 transition law 명세.
        evidenceRows: step, metric, estimate, threshold, operator를 가진 검증 행.
        knowledgeAsOf: 증거가 알려진 cutoff.
        historyStatus: 증거의 as-known 또는 retrospective 상태.
        frequency: 법칙과 증거의 시간 격자.
        stepSpan: 한 step이 차지하는 격자 길이.
        rules: 인증 규칙 설명 또는 식별자.
        evidenceReceiptId: Exact signed ``lawEvidence`` receipt identifier.
        admissionVerifier: Trust-anchor-backed verifier for the receipt and source lineage.

    Returns:
        법칙 실행물, 파라미터, 증거, receipt, 지평을 묶은 인증서. Raw rows without a
        verified receipt remain ``documented`` and cannot admit an active empirical law.

    Raises:
        SimulationSpecError: 법칙 종류, cutoff, 증거 행, 지평 계약이 유효하지 않은 경우.

    Example:
        ``certificate = issueLawCertificate(law, evidenceRows=rows, knowledgeAsOf="20220131", historyStatus="asKnown", frequency="quarter", rules="oos-rmse")``
    """

    if law.evidenceKind not in {"measuredAssociation", "identifiedIntervention"}:
        raise SimulationSpecError("only measured or identified laws can be certified")
    cutoff = str(knowledgeAsOf).replace("-", "")[:8]
    if len(cutoff) != 8 or not cutoff.isdigit() or not rules or not frequency or stepSpan < 1:
        raise SimulationSpecError("law certificate needs a valid cutoff and rules")
    normalized = _normalizeEvidenceRows(evidenceRows)
    maxAdmittedStep = _admittedEvidenceHorizon(normalized)
    if maxAdmittedStep < 1:
        status = "rejected"
    elif not evidenceReceiptId:
        status = "documented"
    elif historyStatus == "asKnown":
        status = "admitted"
    else:
        status = "retrospectiveOnly"
    provisional = LawCertificate(
        certificateId="",
        lawId=law.lawId,
        lawVersion=law.version,
        evidenceKind=law.evidenceKind,
        contractHash=_stableHash(_lawContractPayload(law)),
        parameterHash=_stableHash({"parameters": law.parameters}),
        executableHash=_stableHash({"fn": law.fn}),
        evidenceHash=_stableHash({"rows": normalized}),
        knowledgeAsOf=cutoff,
        historyStatus=historyStatus,
        frequency=frequency,
        stepSpan=stepSpan,
        maxAdmittedStep=maxAdmittedStep,
        status=status,
        rules=rules,
        evidenceReceiptId=evidenceReceiptId,
    )
    if evidenceReceiptId:
        if admissionVerifier is None:
            raise SimulationSpecError("law evidence receipt needs an admission verifier")
        _verifyLawEvidenceReceipt(law, provisional, admissionVerifier)
    return LawCertificate(
        certificateId=_stableHash(_lawCertificatePayload(provisional)),
        **{name: getattr(provisional, name) for name in provisional.__dataclass_fields__ if name != "certificateId"},
    )


def _validateLawCertificate(
    law: LawSpec,
    admissionVerifier: AdmissionVerifier | None = None,
) -> None:
    certificate = law.certificate
    if certificate is None:
        raise SimulationSpecError(f"empirical law needs a certificate: {law.lawId}")
    if certificate.status not in LAW_CERTIFICATE_STATUS_SET:
        raise SimulationSpecError(f"invalid law certificate status: {law.lawId}")
    expectedDigest = _stableHash(_lawCertificatePayload(certificate))
    if certificate.certificateId != expectedDigest:
        raise SimulationSpecError(f"law certificate digest mismatch: {law.lawId}")
    expected = {
        "lawId": law.lawId,
        "lawVersion": law.version,
        "evidenceKind": law.evidenceKind,
        "contractHash": _stableHash(_lawContractPayload(law)),
        "parameterHash": _stableHash({"parameters": law.parameters}),
        "executableHash": _stableHash({"fn": law.fn}),
    }
    if any(getattr(certificate, name) != value for name, value in expected.items()):
        raise SimulationSpecError(f"law certificate binding mismatch: {law.lawId}")
    if certificate.status in {"admitted", "retrospectiveOnly"}:
        if not _validDigest(certificate.evidenceReceiptId):
            raise SimulationSpecError(f"law certificate needs an evidence receipt: {law.lawId}")
        if admissionVerifier is not None:
            _verifyLawEvidenceReceipt(law, certificate, admissionVerifier)
    if law.status == "active" and certificate.status != "admitted":
        raise SimulationSpecError(f"active law needs admitted evidence: {law.lawId}")
    if certificate.status == "retrospectiveOnly" and law.status != "partial":
        raise SimulationSpecError(f"retrospective law must be partial: {law.lawId}")
    if certificate.status == "rejected" and law.status != "blocked":
        raise SimulationSpecError(f"rejected law must be blocked: {law.lawId}")
