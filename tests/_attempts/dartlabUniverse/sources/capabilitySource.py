"""라이브 capability와 실존 registry axis를 별도 authority로 전수 열거한다."""

from __future__ import annotations

import hashlib
import importlib
from pathlib import Path

from dartlab.reference.capability import loadCapabilities

from ..canonical import CapabilityCensus, RegistryRecord, canonicalDigest

_REGISTRY_TARGETS = (
    ("analysis", "dartlab.analysis.financial._registry", "_AXIS_REGISTRY", "AXIS_REGISTRY"),
    ("credit", "dartlab.credit", "_AXIS_REGISTRY", "AXIS_REGISTRY"),
    ("industry", "dartlab.industry", "_AXIS_REGISTRY", "AXIS_REGISTRY"),
    ("macro", "dartlab.macro", "_AXIS_REGISTRY", "AXIS_REGISTRY"),
    ("quant", "dartlab.quant._registry", "_AXIS_REGISTRY", "AXIS_REGISTRY"),
    ("scan", "dartlab.scan.router", "_AXIS_REGISTRY", "AXIS_REGISTRY"),
    ("story", "dartlab.story.reportTypes", "REPORT_TYPES", "REPORT_TYPE_REGISTRY"),
)


def _sourceDigest(module: object) -> tuple[str, str] | None:
    rawPath = getattr(module, "__file__", None)
    if not rawPath:
        return None
    path = Path(rawPath).resolve()
    if not path.is_file():
        return None
    return path.as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()


def enumerateCapabilities() -> CapabilityCensus:
    """Runtime capability와 7개 registry surface의 합집합을 열거한다.

    Args:
        없음.

    Returns:
        runtime ID, registry record, source byte digest와 import error.

    Raises:
        loadCapabilities 자체가 실패하면 예외를 전달한다.

    Example:
        ``enumerateCapabilities().runtimeIds``.
    """
    runtime = loadCapabilities()
    if not isinstance(runtime, dict):
        raise TypeError("loadCapabilities 반환은 dict여야 함")
    runtimeIds = tuple(sorted(str(key) for key in runtime))
    records = []
    sourceDigests = []
    errors = []
    for owner, moduleName, attributeName, sourceKind in _REGISTRY_TARGETS:
        try:
            module = importlib.import_module(moduleName)
            registry = getattr(module, attributeName)
            if not isinstance(registry, dict):
                raise TypeError(f"{attributeName}가 dict가 아님")
            digest = _sourceDigest(module)
            if digest is not None:
                sourceDigests.append(digest)
            for axisId, entry in registry.items():
                records.append(
                    RegistryRecord(
                        recordId=f"{owner}.{axisId}",
                        owner=owner,
                        sourceKind=sourceKind,
                        hidden=bool(getattr(entry, "hidden", False)),
                    )
                )
        except Exception as exc:
            errors.append(f"{owner}:{type(exc).__name__}")
    orderedRecords = tuple(sorted(records, key=lambda record: (record.owner, record.recordId)))
    orderedDigests = tuple(sorted(set(sourceDigests)))
    orderedErrors = tuple(sorted(errors))
    digest = canonicalDigest(
        {
            "runtimeIds": runtimeIds,
            "registryRecords": orderedRecords,
            "sourceDigests": orderedDigests,
            "errors": orderedErrors,
        }
    )
    return CapabilityCensus(
        runtimeIds=runtimeIds,
        registryRecords=orderedRecords,
        sourceDigests=orderedDigests,
        errors=orderedErrors,
        digest=digest,
    )
