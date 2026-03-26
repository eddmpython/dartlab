"""하위호환 re-export — 실제 구현은 engines.common.finance.extract."""

from dartlab.core.finance.extract import (
    getAnnualValues,
    getLatest,
    getRevenueGrowth3Y,
    getTTM,
)

__all__ = ["getTTM", "getLatest", "getAnnualValues", "getRevenueGrowth3Y"]
