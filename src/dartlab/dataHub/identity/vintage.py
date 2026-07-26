"""Provider-neutral point-in-time data vintage contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from datetime import date
from hashlib import sha256
from typing import Mapping

REVISION_POLICIES = {"asKnown", "latestRetained", "revisedHistory", "synthetic", "explicitAssumption"}
COVERAGE_KINDS = {"asOfExact", "latestOnly", "periodOnly", "synthetic"}


class VintageError(ValueError):
    """빈티지의 시점, 내용 결속, 수정 정책 계약이 잘못되면 발생한다."""


def _validDigest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value.lower())


def _dateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")
    if len(text) != 8 or not text.isdigit():
        raise VintageError(f"invalid vintage {label}: {value}")
    try:
        date(int(text[:4]), int(text[4:6]), int(text[6:8]))
    except ValueError as error:
        raise VintageError(f"invalid vintage {label}: {value}") from error
    return text


def _canonical(value):
    if hasattr(value, "__dataclass_fields__"):
        return {item.name: _canonical(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise VintageError(f"unsupported vintage payload type: {type(value).__name__}")


def canonicalPayloadBytes(payload) -> bytes:
    """빈티지 내용 결속에 쓰는 정규 JSON 바이트를 반환한다.

    Args:
        payload: Dataclass, mapping, sequence 또는 JSON scalar로 구성된 값.

    Returns:
        결정적 key 순서와 compact separator를 적용한 UTF-8 JSON bytes.

    Raises:
        VintageError: 지원하지 않는 payload type이 포함된 경우.

    Example:
        ``content = canonicalPayloadBytes({"value": 1})``
    """

    return json.dumps(_canonical(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonicalPayloadHash(payload) -> str:
    """정규화한 실제 값의 SHA-256 내용 해시를 반환한다.

    Args:
        payload: 내용 identity를 발급할 JSON-compatible 값.

    Returns:
        정규 payload bytes의 64자리 SHA-256 hex digest.

    Raises:
        VintageError: 지원하지 않는 payload type이 포함된 경우.

    Example:
        ``digest = canonicalPayloadHash({"value": 1})``
    """

    return sha256(canonicalPayloadBytes(payload)).hexdigest()


def worldStatePayloadHash(
    values: Mapping[str, float | None],
    *,
    step: int,
    asOf: str,
    refs: tuple[str, ...],
) -> str:
    """초기 세계 상태의 실제 값, 시점, 근거를 빈티지 payload와 결속한다.

    Args:
        values: 상태 변수 ID별 값.
        step: 상태가 속한 simulation step.
        asOf: 상태의 valid-time cutoff.
        refs: 상태를 뒷받침하는 source reference tuple.

    Returns:
        세계 상태 payload의 64자리 SHA-256 hex digest.

    Raises:
        VintageError: 값이나 근거에 지원하지 않는 payload type이 포함된 경우.

    Example:
        ``digest = worldStatePayloadHash({"cash": 1.0}, step=0, asOf="20250101", refs=("src",))``
    """

    return canonicalPayloadHash(
        {
            "artifactKind": "worldState",
            "values": values,
            "step": int(step),
            "asOf": str(asOf),
            "refs": tuple(refs),
        }
    )


@dataclass(frozen=True)
class VintageRef:
    """공급자와 무관하게 원본, 정규 payload, 공개시점, 수정 범위를 지칭한다."""

    artifactKind: str
    provider: str
    artifactId: str
    artifactHash: str
    payloadHash: str
    knowledgeAsOf: str
    availableAt: str
    revisionPolicy: str
    coverage: str
    fiscalThrough: str = ""
    eventThrough: str = ""
    fitThrough: str = ""
    receiptId: str = ""
    contractHash: str = ""
    sourceRefs: tuple[str, ...] = ()
    schemaVersion: str = "vintage-ref-v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "sourceRefs", tuple(self.sourceRefs))


def validateVintageRef(
    vintage: VintageRef,
    *,
    decisionAsOf: str,
    expectedArtifactKind: str | None = None,
    expectedPayloadHash: str | None = None,
) -> VintageRef:
    """빈티지의 내용 해시와 시간 인과 및 수정, 범위 계약을 검증한다.

    Args:
        vintage: 검증할 provider-neutral vintage reference.
        decisionAsOf: 소비자가 허용하는 최종 knowledge cutoff.
        expectedArtifactKind: 선택적인 artifact kind 불변식.
        expectedPayloadHash: 선택적인 실제 payload hash 불변식.

    Returns:
        모든 계약을 통과한 원래 ``VintageRef``.

    Raises:
        VintageError: Identity, digest, 시간 순서, revision 또는 coverage가 잘못된 경우.

    Example:
        ``validated = validateVintageRef(vintage, decisionAsOf="20250131")``
    """

    if not isinstance(vintage, VintageRef) or vintage.schemaVersion != "vintage-ref-v1":
        raise VintageError("vintage protocol mismatch")
    if not vintage.artifactKind or not vintage.provider or not vintage.artifactId:
        raise VintageError("vintage identity fields are incomplete")
    if expectedArtifactKind is not None and vintage.artifactKind != expectedArtifactKind:
        raise VintageError("vintage artifact kind mismatch")
    for label, value in (("artifact", vintage.artifactHash), ("payload", vintage.payloadHash)):
        if not _validDigest(value):
            raise VintageError(f"vintage {label} hash is invalid")
    if expectedPayloadHash is not None and vintage.payloadHash != expectedPayloadHash:
        raise VintageError("vintage payload hash mismatch")
    if vintage.contractHash and not _validDigest(vintage.contractHash):
        raise VintageError("vintage contract hash is invalid")
    if vintage.receiptId and not _validDigest(vintage.receiptId):
        raise VintageError("vintage receipt identifier is invalid")
    if vintage.revisionPolicy not in REVISION_POLICIES or vintage.coverage not in COVERAGE_KINDS:
        raise VintageError("vintage revision or coverage contract is invalid")
    availableAt = _dateText(vintage.availableAt, "availableAt")
    knowledgeAsOf = _dateText(vintage.knowledgeAsOf, "knowledgeAsOf")
    decisionCutoff = _dateText(decisionAsOf, "decisionAsOf")
    if availableAt > knowledgeAsOf:
        raise VintageError("vintage evidence is newer than knowledgeAsOf")
    if knowledgeAsOf > decisionCutoff:
        raise VintageError("vintage knowledge is newer than decisionAsOf")
    for label, value in (
        ("fiscalThrough", vintage.fiscalThrough),
        ("eventThrough", vintage.eventThrough),
        ("fitThrough", vintage.fitThrough),
    ):
        if value and _dateText(value, label) > availableAt:
            raise VintageError(f"vintage {label} is newer than availableAt")
    return vintage


def isExactAsKnown(vintage: VintageRef) -> bool:
    """빈티지가 자동 admission에 필요한 exact as-known 조건인지 반환한다.

    Args:
        vintage: Revision과 coverage 계약을 확인할 vintage reference.

    Returns:
        ``asKnown`` revision과 ``asOfExact`` coverage를 모두 가지면 ``True``.

    Raises:
        없음. 전달된 dataclass 필드만 비교한다.

    Example:
        ``exact = isExactAsKnown(vintage)``
    """

    return vintage.revisionPolicy == "asKnown" and vintage.coverage == "asOfExact"
