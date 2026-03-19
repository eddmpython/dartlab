"""DART Company.report 네임스페이스 — 28개 apiType 체계 접근.

company.py에서 분리된 accessor 클래스.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import polars as pl

if TYPE_CHECKING:
    from dartlab.engines.dart.company import Company


class _ReportAccessor:
    """DART Company.report 네임스페이스 — 28개 apiType 체계 접근.

    pivot 함수가 있는 5개(dividend, employee, majorHolder, executive, audit)는
    전용 Result 반환. 나머지는 extractAnnual 기준 DataFrame 반환.

    Example::

        c.report.dividend         # DividendResult (pivot)
        c.report.treasuryStock    # DataFrame (extractAnnual)
        c.report.extract("dividend")  # DataFrame (정제 원본)
        c.report.apiTypes         # 사용 가능한 apiType 목록
    """

    _PIVOT_NAMES = frozenset({"dividend", "employee", "majorHolder", "executive", "audit"})

    def __init__(self, company: "Company"):
        self._company = company
        self._cache: dict[str, Any] = {}

    def _pivot(self, name: str) -> Any:
        if name in self._cache:
            return self._cache[name]
        from dartlab.engines.dart.report import (
            pivotAudit,
            pivotDividend,
            pivotEmployee,
            pivotExecutive,
            pivotMajorHolder,
        )

        funcs = {
            "dividend": pivotDividend,
            "employee": pivotEmployee,
            "majorHolder": pivotMajorHolder,
            "executive": pivotExecutive,
            "audit": pivotAudit,
        }
        func = funcs.get(name)
        if func is None:
            return None
        result = func(self._company.stockCode)
        self._cache[name] = result
        return result

    def extract(self, apiType: str) -> pl.DataFrame | None:
        """apiType별 정제된 DataFrame 반환."""
        cacheKey = f"_extract_{apiType}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.dart.report import extractClean

        try:
            result = extractClean(self._company.stockCode, apiType)
        except (KeyError, ValueError, TypeError, FileNotFoundError):
            result = None
        self._cache[cacheKey] = result
        return result

    def extractAnnual(self, apiType: str, quarterNum: int | None = None) -> pl.DataFrame | None:
        """apiType별 연간 DataFrame 반환."""
        cacheKey = f"_annual_{apiType}_{quarterNum}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.dart.report import extractAnnual as _extractAnnual

        try:
            result = _extractAnnual(self._company.stockCode, apiType, quarterNum)
        except (KeyError, ValueError, TypeError, FileNotFoundError):
            result = None
        self._cache[cacheKey] = result
        return result

    def result(self, apiType: str, quarterNum: int | None = None) -> Any | None:
        """apiType별 통일된 Result 반환."""
        cacheKey = f"_result_{apiType}_{quarterNum}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        if apiType in self._PIVOT_NAMES:
            result = getattr(self, apiType)
            self._cache[cacheKey] = result
            return result

        from dartlab.engines.dart.report import extractResult

        try:
            result = extractResult(self._company.stockCode, apiType, quarterNum)
        except (KeyError, ValueError, TypeError, FileNotFoundError):
            result = None
        self._cache[cacheKey] = result
        return result

    def status(self, apiType: str | None = None) -> pl.DataFrame | dict[str, bool]:
        """apiType availability 확인."""
        from dartlab.engines.dart.report.types import API_TYPE_LABELS, API_TYPES, PREFERRED_QUARTER

        if apiType is not None:
            return {apiType: self.extract(apiType) is not None}

        rows = []
        for name in API_TYPES:
            rows.append(
                {
                    "apiType": name,
                    "label": API_TYPE_LABELS.get(name, name),
                    "preferredQuarter": PREFERRED_QUARTER.get(name),
                    "isPivot": name in self._PIVOT_NAMES,
                    "available": self.extract(name) is not None,
                }
            )
        return pl.DataFrame(rows)

    @property
    def dividend(self):
        """배당 시계열 (DividendResult)."""
        import warnings

        warnings.warn("report.dividend → show('dividend') 경로 권장", DeprecationWarning, stacklevel=2)
        return self._pivot("dividend")

    @property
    def employee(self):
        """직원현황 시계열 (EmployeeResult)."""
        import warnings

        warnings.warn("report.employee → show('employee') 경로 권장", DeprecationWarning, stacklevel=2)
        return self._pivot("employee")

    @property
    def majorHolder(self):
        """최대주주현황 시계열 (MajorHolderResult)."""
        import warnings

        warnings.warn("report.majorHolder → show('majorHolder') 경로 권장", DeprecationWarning, stacklevel=2)
        return self._pivot("majorHolder")

    @property
    def executive(self):
        """임원현황 (ExecutiveResult)."""
        import warnings

        warnings.warn("report.executive → show('executive') 경로 권장", DeprecationWarning, stacklevel=2)
        return self._pivot("executive")

    @property
    def audit(self):
        """감사의견 시계열 (AuditResult)."""
        import warnings

        warnings.warn("report.audit → show('audit') 경로 권장", DeprecationWarning, stacklevel=2)
        return self._pivot("audit")

    def __getattr__(self, name: str) -> Any:
        """미등록 apiType은 extractAnnual 자동 호출."""
        if name.startswith("_"):
            raise AttributeError(name)
        from dartlab.engines.dart.report.types import API_TYPES

        if name in API_TYPES and name not in self._PIVOT_NAMES:
            return self.extractAnnual(name)
        raise AttributeError(f"ReportAccessor에 '{name}' 항목이 없습니다. apiTypes: {API_TYPES}")

    @property
    def apiTypes(self) -> list[str]:
        """사용 가능한 apiType 목록."""
        from dartlab.engines.dart.report.types import API_TYPES

        return list(API_TYPES)

    @property
    def labels(self) -> dict[str, str]:
        """apiType → 한글명 매핑."""
        from dartlab.engines.dart.report.types import API_TYPE_LABELS

        return dict(API_TYPE_LABELS)

    @property
    def availableApiTypes(self) -> list[str]:
        """현재 parquet에 실제 존재하는 apiType 목록."""
        from dartlab.engines.dart.report.types import API_TYPES

        return [name for name in API_TYPES if self.extract(name) is not None]

    def __repr__(self):
        from dartlab.engines.dart.report.types import API_TYPES

        return f"ReportAccessor({len(API_TYPES)} apiTypes, {len(self._PIVOT_NAMES)} pivots)"
