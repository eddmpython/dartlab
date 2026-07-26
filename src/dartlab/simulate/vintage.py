"""Compatibility re-exports for provider-neutral vintage contracts."""

from dartlab.dataHub.identity.vintage import (
    COVERAGE_KINDS,
    REVISION_POLICIES,
    VintageError,
    VintageRef,
    canonicalPayloadBytes,
    canonicalPayloadHash,
    isExactAsKnown,
    validateVintageRef,
    worldStatePayloadHash,
)

__all__ = [
    "COVERAGE_KINDS",
    "REVISION_POLICIES",
    "VintageError",
    "VintageRef",
    "canonicalPayloadBytes",
    "canonicalPayloadHash",
    "isExactAsKnown",
    "validateVintageRef",
    "worldStatePayloadHash",
]
