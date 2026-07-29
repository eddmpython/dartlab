"""프로세스 RSS, bounded cache, 메모이제이션, OOM guard의 L0 facade."""

from dartlab.core.memory.cache import (
    BoundedCache,
    CachePolicy,
    lookupCache,
)
from dartlab.core.memory.guards import (
    MemoryBudgetExceeded,
    MemoryScope,
    OomTripwire,
    finalizeMemoryScope,
    withMemoryBudget,
)
from dartlab.core.memory.memoization import memoizedCalc
from dartlab.core.memory.metrics import (
    PRESSURE_CRITICAL_MB,
    PRESSURE_EMERGENCY_MB,
    PRESSURE_FATAL_MB,
    PRESSURE_WARNING_MB,
    checkMemoryAndGc,
    cleanupBetweenCompanies,
    getMemoryMb,
    getPeakRssMb,
)

__all__ = [
    "PRESSURE_CRITICAL_MB",
    "PRESSURE_EMERGENCY_MB",
    "PRESSURE_FATAL_MB",
    "PRESSURE_WARNING_MB",
    "BoundedCache",
    "CachePolicy",
    "MemoryBudgetExceeded",
    "MemoryScope",
    "OomTripwire",
    "checkMemoryAndGc",
    "cleanupBetweenCompanies",
    "finalizeMemoryScope",
    "getMemoryMb",
    "getPeakRssMb",
    "lookupCache",
    "memoizedCalc",
    "withMemoryBudget",
]
