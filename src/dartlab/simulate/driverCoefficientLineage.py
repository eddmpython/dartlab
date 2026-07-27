"""계수 승인의 부모 계보. 서명 부모 검증과 커버리지 아티팩트 대조.

계수 모듈 가운데 파일시스템과 JSON 을 만지는 곳은 여기뿐이다. 이 관심사를 빼면
적합·판정 모듈은 순수 계산으로 남고, 아티팩트 부재나 비정규 JSON 같은 입출력
실패는 전부 이 경계 한 곳에서 계수 오류로 번역된다.
"""

from __future__ import annotations

import json

from dartlab.simulate.admissionRegistry import AdmissionReceipt, AdmissionVerifier, artifactPath
from dartlab.simulate.driverCalibrationContracts import (
    PARENT_COVERAGE_VERSION,
    DriverCalibrationError,
)
from dartlab.simulate.driverCalibrationKernel import _assertClose, _dateText, _finite
from dartlab.simulate.vintage import canonicalPayloadBytes


def _verifyCoefficientParent(
    admissionVerifier: AdmissionVerifier,
    receiptId: str,
    *,
    role: str,
    allowedKinds: set[str],
    maxKnowledgeAsOf: str,
    decisionAsOf: str,
) -> AdmissionReceipt:
    try:
        parent = admissionVerifier.verify(receiptId)
    except RuntimeError as error:
        raise DriverCalibrationError(f"coefficient parent admission verification failed: {error}") from error
    if (
        parent.kind not in allowedKinds
        or parent.status != "verifiedVintage"
        or parent.revisionPolicy != "asKnown"
        or parent.coverage != "asOfExact"
    ):
        raise DriverCalibrationError(f"coefficient {role} parent receipt must be verified vintage")
    if _dateText(parent.knowledgeAsOf, f"{role} parent knowledgeAsOf") > _dateText(
        maxKnowledgeAsOf,
        f"{role} parent maxKnowledgeAsOf",
    ):
        raise DriverCalibrationError(f"coefficient {role} parent knowledge is after coefficient cutoff")
    if _dateText(parent.issuedAt, f"{role} parent issuedAt") > _dateText(decisionAsOf, "decisionAsOf"):
        raise DriverCalibrationError(f"coefficient {role} parent is not available by decisionAsOf")
    return parent


def _coverageRow(
    *,
    ref: str,
    role: str,
    eventTime: str,
    availableAt: str,
    value: float,
    unit: str,
) -> dict:
    if not ref or role not in {"source", "label"} or not unit:
        raise DriverCalibrationError("coefficient parent coverage row is incomplete")
    return {
        "ref": ref,
        "role": role,
        "eventTime": _dateText(eventTime, "parent coverage eventTime"),
        "availableAt": _dateText(availableAt, "parent coverage availableAt"),
        "value": _finite(value, "parent coverage value"),
        "unit": unit,
    }


def _coverageRowsFromManifest(payload: dict, *, role: str) -> tuple[dict, ...]:
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise DriverCalibrationError("coefficient parent coverage manifest is malformed")
    out = []
    for item in rows:
        if not isinstance(item, dict):
            raise DriverCalibrationError("coefficient parent coverage row is malformed")
        rowRole = str(item.get("role", ""))
        if rowRole not in {"source", "label"}:
            raise DriverCalibrationError("coefficient parent coverage row role is invalid")
        if rowRole != role:
            continue
        out.append(
            _coverageRow(
                ref=str(item.get("ref", "")),
                role=rowRole,
                eventTime=str(item.get("eventTime", "")),
                availableAt=str(item.get("availableAt", "")),
                value=item.get("value"),
                unit=str(item.get("unit", "")),
            )
        )
    return tuple(out)


def _coverageRowsFromProviderBatch(payload: dict, *, role: str) -> tuple[dict, ...]:
    observations = payload.get("observations")
    if not isinstance(observations, list):
        raise DriverCalibrationError("coefficient provider batch coverage artifact is malformed")
    out = []
    for item in observations:
        if not isinstance(item, dict):
            raise DriverCalibrationError("coefficient provider batch observation is malformed")
        out.append(
            _coverageRow(
                ref=str(item.get("observationId", "")),
                role=role,
                eventTime=str(item.get("eventAt", "")),
                availableAt=str(item.get("availableAt", "")),
                value=item.get("value"),
                unit=str(item.get("unit", "")),
            )
        )
    return tuple(out)


def _coverageRowsFromParent(
    admissionVerifier: AdmissionVerifier,
    parent: AdmissionReceipt,
    *,
    role: str,
) -> tuple[dict, ...]:
    try:
        raw = artifactPath(admissionVerifier.artifactRoot, parent.artifactHash).read_bytes()
    except OSError as error:
        raise DriverCalibrationError("coefficient parent coverage artifact is unavailable") from error
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise DriverCalibrationError("coefficient parent coverage artifact is not canonical JSON") from error
    if canonicalPayloadBytes(payload) != raw:
        raise DriverCalibrationError("coefficient parent coverage artifact is not canonical")
    if not isinstance(payload, dict):
        raise DriverCalibrationError("coefficient parent coverage artifact is malformed")
    schemaVersion = payload.get("schemaVersion")
    if schemaVersion == PARENT_COVERAGE_VERSION:
        return _coverageRowsFromManifest(payload, role=role)
    if schemaVersion == "provider-observation-batch-v1":
        return _coverageRowsFromProviderBatch(payload, role=role)
    raise DriverCalibrationError("coefficient parent coverage artifact is unsupported")


def _coverageIndex(
    admissionVerifier: AdmissionVerifier,
    parents: tuple[AdmissionReceipt, ...],
    *,
    role: str,
) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for parent in parents:
        for row in _coverageRowsFromParent(admissionVerifier, parent, role=role):
            ref = row["ref"]
            if ref in index:
                raise DriverCalibrationError("coefficient parent coverage has duplicate row ref")
            index[ref] = row
    return index


def _verifyParentCoverage(
    admissionVerifier: AdmissionVerifier,
    parents: tuple[AdmissionReceipt, ...],
    expectedRows: tuple[dict, ...],
    *,
    role: str,
    roleLabel: str,
) -> None:
    index = _coverageIndex(admissionVerifier, parents, role=role)
    missing = tuple(row["ref"] for row in expectedRows if row["ref"] not in index)
    if missing:
        raise DriverCalibrationError(f"coefficient {roleLabel} parent coverage missing row refs")
    for expected in expectedRows:
        actual = index[expected["ref"]]
        if (
            actual["role"] != expected["role"]
            or actual["eventTime"] != expected["eventTime"]
            or actual["availableAt"] != expected["availableAt"]
            or actual["unit"] != expected["unit"]
        ):
            raise DriverCalibrationError(f"coefficient {roleLabel} parent coverage row mismatch")
        try:
            _assertClose(actual["value"], expected["value"], f"{roleLabel} parent coverage value")
        except DriverCalibrationError as error:
            raise DriverCalibrationError(f"coefficient {roleLabel} parent coverage row mismatch") from error


def _expectedCoverageRowsFromTraceRows(
    traceRows,
    *,
    role: str,
    sourceUnit: str,
    targetUnit: str,
) -> tuple[dict, ...]:
    rows = []
    for row in traceRows:
        if role == "source":
            rows.append(
                _coverageRow(
                    ref=row.sourceRef,
                    role="source",
                    eventTime=row.originEventTime,
                    availableAt=row.sourceAvailableAt,
                    value=row.sourceValue,
                    unit=sourceUnit,
                )
            )
        elif role == "label":
            rows.append(
                _coverageRow(
                    ref=row.labelSourceRef,
                    role="label",
                    eventTime=row.targetEventTime,
                    availableAt=row.targetAvailableAt,
                    value=row.targetValue,
                    unit=targetUnit,
                )
            )
        else:
            raise DriverCalibrationError("coefficient coverage role is invalid")
    return tuple(rows)


def _expectedMultivariableCoverageRowsFromTraceRows(
    traceRows,
    *,
    role: str,
    targetUnit: str,
) -> tuple[dict, ...]:
    rows = []
    for row in traceRows:
        if role == "source":
            for cell in row.sourceCells:
                rows.append(
                    _coverageRow(
                        ref=cell.sourceRef,
                        role="source",
                        eventTime=cell.eventTime,
                        availableAt=cell.availableAt,
                        value=cell.value,
                        unit=cell.unit,
                    )
                )
        elif role == "label":
            rows.append(
                _coverageRow(
                    ref=row.labelSourceRef,
                    role="label",
                    eventTime=row.targetEventTime,
                    availableAt=row.targetAvailableAt,
                    value=row.targetValue,
                    unit=targetUnit,
                )
            )
        else:
            raise DriverCalibrationError("coefficient vector coverage role is invalid")
    return tuple(rows)
