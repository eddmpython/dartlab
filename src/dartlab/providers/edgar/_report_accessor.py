"""EDGAR Company.report 네임스페이스 — XBRL 기반 구조화 데이터.

DART report가 OpenDART API 28 apiType으로 접근하듯,
EDGAR report는 XBRL facts + 10-K sections에서 구조화 데이터를 추출한다.

현재 지원 apiType:
- dividend: 배당 (CF dividends_paid + IS basic_eps + DPS)
- treasuryStock: 자사주 (XBRL treasury_stock)
- stockTotal: 발행주식총수 (XBRL shares_outstanding)

향후 확장:
- employee: 직원 현황 (10-K Item 1 텍스트 파싱)
- auditOpinion: 감사의견 (10-K Item 9A)
- corporateBond: 사채 (10-K notes)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import polars as pl

if TYPE_CHECKING:
    from dartlab.providers.edgar.company import Company


class _ReportAccessor:
    """EDGAR report 네임스페이스 — DART report와 인터페이스 통일."""

    def __init__(self, company: "Company"):
        self._company = company
        self._cache: dict[str, Any] = {}

    @property
    def apiTypes(self) -> list[str]:
        """지원 apiType 목록."""
        return list(_SUPPORTED.keys())

    @property
    def availableApiTypes(self) -> list[str]:
        """데이터가 실제 존재하는 apiType."""
        available = []
        for api_type in _SUPPORTED:
            df = self.extract(api_type)
            if df is not None and not df.is_empty():
                available.append(api_type)
        return available

    def extract(self, apiType: str) -> pl.DataFrame | None:
        """apiType별 데이터 추출."""
        if apiType in self._cache:
            return self._cache[apiType]
        fn = _SUPPORTED.get(apiType)
        if fn is None:
            return None
        result = fn(self._company)
        self._cache[apiType] = result
        return result

    def __getattr__(self, name: str) -> pl.DataFrame | None:
        """apiType을 속성으로 접근: c.report.dividend"""
        if name.startswith("_"):
            raise AttributeError(name)
        if name in _SUPPORTED:
            return self.extract(name)
        raise AttributeError(f"EDGAR report에 '{name}' apiType 없음. 지원: {list(_SUPPORTED.keys())}")

    def __repr__(self) -> str:
        return f"EdgarReport(apiTypes={self.apiTypes})"


# ── apiType 구현 ──


def _extractDividend(company: "Company") -> pl.DataFrame | None:
    """배당 데이터 — CF dividends_paid + IS DPS 시계열."""
    from dartlab.core.show import isPeriodColumn, selectFromShow

    cf = company.CF
    is_df = company.IS
    if cf is None:
        return None

    divs = selectFromShow(cf, ["dividends_paid"])
    dps = selectFromShow(is_df, ["dividends_per_share"]) if is_df is not None else None

    rows: list[dict] = []
    if divs is not None:
        pcols = [c for c in divs.columns if isPeriodColumn(c)]
        for p in pcols:
            row: dict[str, Any] = {"period": p}
            for r in divs.iter_rows(named=True):
                row["dividendTotal"] = r.get(p)
            if dps is not None:
                for r in dps.iter_rows(named=True):
                    row["dps"] = r.get(p)
            rows.append(row)
    return pl.DataFrame(rows) if rows else None


def _extractTreasuryStock(company: "Company") -> pl.DataFrame | None:
    """자사주 데이터 — BS treasury_stock 시계열."""
    from dartlab.core.show import isPeriodColumn, selectFromShow

    bs = company.BS
    if bs is None:
        return None
    ts = selectFromShow(bs, ["treasury_stock"])
    if ts is None:
        return None
    pcols = [c for c in ts.columns if isPeriodColumn(c)]
    rows = []
    for p in pcols:
        val = ts[p][0]
        rows.append({"period": p, "treasuryStock": val})
    return pl.DataFrame(rows) if rows else None


def _extractStockTotal(company: "Company") -> pl.DataFrame | None:
    """발행주식총수 — profile sharesOutstanding."""
    shares = getattr(company._profileAccessor, "sharesOutstanding", None)
    if shares is None:
        return None
    return pl.DataFrame([{"sharesOutstanding": shares}])


# ── 지원 apiType 매핑 ──

_SUPPORTED: dict[str, Any] = {
    "dividend": _extractDividend,
    "treasuryStock": _extractTreasuryStock,
    "stockTotal": _extractStockTotal,
}
