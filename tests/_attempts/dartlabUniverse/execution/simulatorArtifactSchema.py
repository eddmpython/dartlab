"""Simulator artifact 의미를 exact receipt tuple에 결박하는 descriptor registry."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from dartlab.simulate.admissionRegistry import AdmissionReceipt

from ..canonical import canonicalDigest


@dataclass(frozen=True, slots=True)
class SimulatorArtifactSchemaDescriptor:
    descriptorId: str
    receiptVersion: str
    kind: str
    ruleId: str
    ruleVersion: str
    ruleHash: str
    issuerExecutableHash: str
    artifactRole: str
    mediaType: str
    schemaVersion: str
    decoderId: str
    decoderDigest: str
    subjectHashRule: str
    subjectBinding: str | None
    parentRoles: tuple[str, ...]
    fieldBindings: tuple[tuple[str, str], ...]
    requiredSemanticFields: tuple[str, ...]
    seedPolicy: str
    status: str = "ACTIVE"

    @property
    def exactKey(self) -> tuple[str, str, str, str, str, str]:
        return (
            self.receiptVersion,
            self.kind,
            self.ruleId,
            self.ruleVersion,
            self.ruleHash,
            self.issuerExecutableHash,
        )


class SimulatorArtifactSchemaRegistry:
    def __init__(self, descriptors: tuple[SimulatorArtifactSchemaDescriptor, ...] = ()) -> None:
        records = {}
        for descriptor in descriptors:
            if descriptor.exactKey in records:
                raise ValueError(f"simulator schema exact tuple 중복: {descriptor.exactKey}")
            records[descriptor.exactKey] = descriptor
        self._records = records

    def resolve(self, receipt: AdmissionReceipt) -> SimulatorArtifactSchemaDescriptor | None:
        key = (
            receipt.receiptVersion,
            receipt.kind,
            receipt.ruleId,
            receipt.ruleVersion,
            receipt.ruleHash,
            receipt.issuerExecutableHash,
        )
        return self._records.get(key)

    @property
    def descriptors(self) -> tuple[SimulatorArtifactSchemaDescriptor, ...]:
        return tuple(sorted(self._records.values(), key=lambda item: item.exactKey))

    @property
    def digest(self) -> str:
        return canonicalDigest(self.descriptors)


def buildSimulatorArtifactDescriptor(**fields: Any) -> SimulatorArtifactSchemaDescriptor:
    """Exact tuple와 의미 계약에서 descriptor ID를 계산한다."""
    provisional = SimulatorArtifactSchemaDescriptor(descriptorId="", **fields)
    descriptorId = f"du:v1:simulator-schema:{canonicalDigest(provisional)}"
    return replace(provisional, descriptorId=descriptorId)


_DEFAULT_REGISTRY = SimulatorArtifactSchemaRegistry()


def resolveSimulatorArtifactDescriptor(
    receipt: AdmissionReceipt,
    descriptors: SimulatorArtifactSchemaRegistry | tuple[SimulatorArtifactSchemaDescriptor, ...] | None = None,
) -> SimulatorArtifactSchemaDescriptor | None:
    """Receipt 6-tuple이 정확히 같은 active descriptor만 반환한다."""
    if descriptors is None:
        registry = _DEFAULT_REGISTRY
    elif isinstance(descriptors, SimulatorArtifactSchemaRegistry):
        registry = descriptors
    else:
        registry = SimulatorArtifactSchemaRegistry(descriptors)
    descriptor = registry.resolve(receipt)
    return descriptor if descriptor is not None and descriptor.status == "ACTIVE" else None
