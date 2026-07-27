"""계수 보정의 PIT 원시 연산. 날짜·다이제스트·유한값·source 계약 해시.

스칼라 반쪽과 벡터 반쪽이 글자 그대로 같은 판정을 쓰는 자리만 모았다.
두 반쪽이 각자 복제하면 "언제를 안 시점으로 보는가" 가 조용히 갈라지므로,
시점 판정과 근거 식별자 판정은 여기 한 벌만 둔다.
"""

from __future__ import annotations

import math
from datetime import date

from dartlab.simulate.driverCalibrationContracts import (
    _BASE_RECEIPT_WARNINGS,
    _CALIBRATION_METHODS,
    _OBSERVABLE_TARGET_KINDS,
    DriverCalibrationError,
    DriverCalibrationTarget,
    DriverCoefficientOosSpec,
)
from dartlab.simulate.driverRegistry import DriverRegistryResult
from dartlab.simulate.operatingBridge import (
    OPERATING_TARGET_UNITS,
    OperatingBridgeError,
    sourceFactorContractHash,
)


def _dateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")[:8]
    if len(text) != 8 or not text.isdigit():
        raise DriverCalibrationError(f"invalid {label}: {value}")
    return text


def _validDigest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value.lower())


def _validateReceiptIds(receiptIds: tuple[str, ...], label: str) -> None:
    if len(set(receiptIds)) != len(receiptIds) or any(not _validDigest(receiptId) for receiptId in receiptIds):
        raise DriverCalibrationError(f"{label} receipt identifiers are invalid")


def _dateParts(value: str, label: str) -> tuple[int, int, int]:
    text = _dateText(value, label)
    year = int(text[:4])
    month = int(text[4:6])
    day = int(text[6:8])
    try:
        date(year, month, day)
    except ValueError as error:
        raise DriverCalibrationError(f"invalid {label}: {value}") from error
    return year, month, day


def _periodIndex(value: str, frequency: str, label: str) -> int:
    year, month, day = _dateParts(value, label)
    normalized = frequency.lower()
    if normalized in {"day", "daily"}:
        return date(year, month, day).toordinal()
    if normalized in {"month", "monthly"}:
        return year * 12 + month - 1
    if normalized in {"quarter", "quarterly"}:
        return year * 4 + (month - 1) // 3
    if normalized in {"year", "yearly", "annual"}:
        return year
    raise DriverCalibrationError(f"unsupported coefficient OOS frequency: {frequency}")


def _validateOosHorizon(originEventTime: str, targetEventTime: str, spec: DriverCoefficientOosSpec) -> None:
    originIndex = _periodIndex(originEventTime, spec.frequency, "originEventTime")
    targetIndex = _periodIndex(targetEventTime, spec.frequency, "targetEventTime")
    distance = targetIndex - originIndex
    if distance <= 0:
        raise DriverCalibrationError("coefficient OOS target event must be after origin event")
    if distance % spec.stepSpan:
        raise DriverCalibrationError("coefficient OOS horizon does not align with stepSpan")
    admittedStep = distance // spec.stepSpan
    if admittedStep > spec.maxAdmittedStep:
        raise DriverCalibrationError("coefficient OOS horizon exceeds maxAdmittedStep")


def _finite(value: float | None, label: str) -> float:
    if value is None:
        raise DriverCalibrationError(f"{label} is missing")
    number = float(value)
    if not math.isfinite(number):
        raise DriverCalibrationError(f"{label} must be finite")
    return number


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _driverSourceFactorContractHash(
    *,
    variableId: str,
    unit: str,
    frequency: str,
    timing: str,
    transformId: str,
) -> str:
    try:
        return sourceFactorContractHash(
            variableId=variableId,
            unit=unit,
            frequency=frequency,
            timing=timing,
            transformId=transformId,
        )
    except OperatingBridgeError as error:
        raise DriverCalibrationError("coefficient source factor contract is incomplete") from error


def _assertClose(left: float, right: float, label: str) -> None:
    if not math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12):
        raise DriverCalibrationError(f"coefficient OOS report {label} mismatch")


def _validateTarget(target: DriverCalibrationTarget) -> None:
    if (
        not target.targetVariableId
        or target.targetShock not in OPERATING_TARGET_UNITS
        or target.targetUnit != OPERATING_TARGET_UNITS[target.targetShock]
        or not target.labelProviderId
        or not target.labelDatasetId
        or not target.labelSourceRefs
        or not target.historyStatus
    ):
        raise DriverCalibrationError("calibration target contract is incomplete")
    if target.targetEvidenceKind not in _OBSERVABLE_TARGET_KINDS:
        raise DriverCalibrationError("coefficient calibration target must be an observable label")
    if target.targetProxyRef:
        raise DriverCalibrationError("proxy target labels cannot fit operating coefficients")
    _validateReceiptIds(target.labelParentReceiptIds, "label parent")


def _sourceFactor(registryResult: DriverRegistryResult, variableId: str):
    matches = tuple(factor for factor in registryResult.pathSet.factorSpecs if factor.variableId == variableId)
    if len(matches) != 1:
        raise DriverCalibrationError(f"source variable must match one registry factor: {variableId}")
    return matches[0]


def _oosRejectionReasons(receipt, spec, *, nOrigins: int, skill: float, rmse: float, bias: float) -> list[str]:
    """held-out 판정 거부 사유를 순서대로 모은다.

    스칼라 계수와 벡터 계수가 문자 그대로 같은 사유 목록을 쓴다. 사유 이름과 그
    나열 순서가 보고서 내용 해시에 들어가므로, 두 반쪽이 각자 목록을 들고 있으면
    한쪽만 고쳐졌을 때 같은 판정이 다른 신분을 갖게 된다.
    """
    reasons: list[str] = []
    if receipt.historyStatus != "asKnown":
        reasons.append("receiptHistoryNotAsKnown")
    disallowedWarnings = tuple(warning for warning in receipt.warnings if warning not in _BASE_RECEIPT_WARNINGS)
    if disallowedWarnings:
        reasons.append("receiptHasNonAdmissionWarnings")
    if nOrigins < spec.minOosOrigins:
        reasons.append("oosOriginsBelowMinimum")
    if skill < spec.minSkillVsBaseline:
        reasons.append("skillBelowThreshold")
    if rmse > spec.maxRmse:
        reasons.append("rmseAboveThreshold")
    if abs(bias) > spec.maxAbsBias:
        reasons.append("biasAboveThreshold")
    if not receipt.sourceParentReceiptIds:
        reasons.append("fitSourceParentsMissing")
    if not receipt.labelParentReceiptIds:
        reasons.append("fitLabelParentsMissing")
    if not spec.sourceParentReceiptIds:
        reasons.append("oosSourceParentsMissing")
    if not spec.labelParentReceiptIds:
        reasons.append("oosLabelParentsMissing")
    return reasons
