"""finance authoritative namespace accessor.

company.py에서 분리된 accessor 클래스.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from dartlab.engines.dart.company import Company


class _FinanceAccessor:
    """finance authoritative namespace."""

    def __init__(self, company: "Company"):
        self._company = company

    @property
    def raw(self) -> pl.DataFrame | None:
        return self._company.rawFinance

    @property
    def BS(self) -> pl.DataFrame | None:
        return self._company._financeOrDocsStatement("BS")

    @property
    def IS(self) -> pl.DataFrame | None:
        return self._company._financeOrDocsStatement("IS")

    @property
    def CIS(self) -> pl.DataFrame | None:
        return self._company._financeOrDocsStatement("CIS")

    @property
    def CF(self) -> pl.DataFrame | None:
        return self._company._financeOrDocsStatement("CF")

    @property
    def timeseries(self):
        return self._company._getFinanceBuild("q", "CFS")

    @property
    def annual(self):
        return self._company._getFinanceBuild("y", "CFS")

    @property
    def cumulative(self):
        return self._company._getFinanceBuild("cum", "CFS")

    @property
    def ratios(self):
        return self._company.getRatios("CFS")

    @property
    def ratioSeries(self):
        return self._company._ratioSeries()

    @property
    def sce(self):
        return self._company._sce()

    @property
    def SCE(self):
        return self._company._sce()

    @property
    def sceMatrix(self):
        return self._company._sceMatrix()
