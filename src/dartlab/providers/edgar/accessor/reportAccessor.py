"""EDGAR Company.report 네임스페이스 — XBRL 기반 구조화 데이터.

DART report가 OpenDART API 28 apiType으로 접근하듯,
EDGAR report는 XBRL facts + 10-K sections에서 구조화 데이터를 추출한다.

지원 apiType (14개):
- dividend: 배당
- treasuryStock: 자사주
- stockTotal: 발행주식총수
- employee: 직원 현황 (XBRL + 10-K Item 1 regex)
- auditOpinion: 감사의견 + 감사비용
- corporateBond: 사채/부채 구조
- executive: 임원 현황 (10-K Item 10 파싱)
- majorHolder: 주요 주주 (XBRL shares)
- executivePay: 임원 보수 (stock compensation)
- capitalChange: 증자/감자 (주식 발행/소각)
- outsideDirector: 사외이사 (10-K Item 10 텍스트)
- minorityHolder: 비지배지분 (XBRL NoncontrollingInterest)
- investedCompany: 타법인 출자 (XBRL 투자 태그)
- debtSecurities: 채무증권 (CP/단기사채/AFS/HTM)
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
        """지원 apiType 목록.

        Returns:
            apiType 문자열 리스트.

        Raises:
            없음.

        Example:
            >>> c._report.apiTypes

        LLM Specifications:
            AntiPatterns:
                - apiType 추측 X — 14 종 _SUPPORTED 명시.
                - report 부재 회사 → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel("dividend"/"treasuryStock"/...)``.
            OutputSchema:
                - pl.DataFrame 또는 None.
            Prerequisites:
                - 본 회사 SEC companyfacts.parquet + 10-K sections (선택).
            Freshness:
                - SEC EDGAR 갱신 시점.
            Dataflow:
                - apiType → _SUPPORTED dispatch → extractor 위임 → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR XBRL + 10-K) 한정.
        """
        return list(_SUPPORTED.keys())

    @property
    def availableApiTypes(self) -> list[str]:
        """데이터가 실제 존재하는 apiType.

        Returns:
            데이터 있는 apiType 리스트.

        Raises:
            없음.

        Example:
            >>> c._report.availableApiTypes

        SeeAlso:
            - ``_SUPPORTED`` (모듈) — 14 apiType → extractor 매핑.
            - ``providers.edgar.report.*`` — 개별 extractor 모듈.

        Requires:
            - polars

        Capabilities:
            - XBRL companyfacts + 10-K sections 기반 14 apiType (dividend/treasuryStock/employee/audit/
              executive/majorHolder/...) 위임 dispatch. DART 28 apiType 와 인터페이스 통일.

        Guide:
            - 사용자 API 는 ``c.panel("dividend"/...)`` — 본 namespace 직접 호출 X.

        AIContext:
            internal report accessor — AI 가 직접 호출 X.

        LLM Specifications:
            AntiPatterns:
                - apiType 추측 X — 14 종 _SUPPORTED 명시.
                - report 부재 회사 → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel("dividend"/"treasuryStock"/...)``.
            OutputSchema:
                - pl.DataFrame 또는 None.
            Prerequisites:
                - 본 회사 SEC companyfacts.parquet + 10-K sections (선택).
            Freshness:
                - SEC EDGAR 갱신 시점.
            Dataflow:
                - apiType → _SUPPORTED dispatch → extractor 위임 → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR XBRL + 10-K) 한정.
        """
        available = []
        for apiType in _SUPPORTED:
            df = self.extract(apiType)
            if df is not None and not df.is_empty():
                available.append(apiType)
        return available

    def extract(self, apiType: str) -> pl.DataFrame | None:
        """apiType 별 데이터 추출.

        Args:
            apiType: 14 종 apiType 중 하나.

        Returns:
            DataFrame 또는 None.

        Raises:
            OSError: report artifact 로드 실패.
            ValueError: report extractor 값 계약 위반.
            polars.exceptions.PolarsError: report artifact schema 또는 변환 실패.

        Example:
            >>> c._report.extract("dividend")

        SeeAlso:
            - ``_SUPPORTED`` (모듈) — 14 apiType → extractor 매핑.
            - ``providers.edgar.report.*`` — 개별 extractor 모듈.

        Requires:
            - polars

        Capabilities:
            - XBRL companyfacts + 10-K sections 기반 14 apiType (dividend/treasuryStock/employee/audit/
              executive/majorHolder/...) 위임 dispatch. DART 28 apiType 와 인터페이스 통일.

        Guide:
            - 사용자 API 는 ``c.panel("dividend"/...)`` — 본 namespace 직접 호출 X.

        AIContext:
            internal report accessor — AI 가 직접 호출 X.

        LLM Specifications:
            AntiPatterns:
                - apiType 추측 X — 14 종 _SUPPORTED 명시.
                - report 부재 회사 → None. caller None 분기 의무.
                - 본 namespace 직접 호출 X — 사용자 API 는 ``c.panel("dividend"/"treasuryStock"/...)``.
            OutputSchema:
                - pl.DataFrame 또는 None.
            Prerequisites:
                - 본 회사 SEC companyfacts.parquet + 10-K sections (선택).
            Freshness:
                - SEC EDGAR 갱신 시점.
            Dataflow:
                - apiType → _SUPPORTED dispatch → extractor 위임 → 본 namespace.
            TargetMarkets:
                - US (SEC EDGAR XBRL + 10-K) 한정.
        """
        if apiType in self._cache:
            return self._cache[apiType]
        fn = _SUPPORTED.get(apiType)
        if fn is None:
            return None
        result = fn(self._company)
        self._cache[apiType] = result
        return result

    def __getattr__(self, name: str) -> pl.DataFrame | None:
        """내부 attr 접근 — Company 의 ``_report`` 가 사용. 사용자는 ``c.panel(name)``."""
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
    from dartlab.providers._common.show import isPeriodColumn, selectFromShow

    cf = company.panel("CF")
    isDf = company.panel("IS")
    if cf is None:
        return None

    divs = selectFromShow(cf, ["dividends_paid"])
    dps = selectFromShow(isDf, ["dividends_per_share"]) if isDf is not None else None

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
    from dartlab.providers._common.show import isPeriodColumn, selectFromShow

    bs = company.panel("BS")
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


# ── 신규 extractor wrapper ──


def _extractEmployee(company: "Company") -> pl.DataFrame | None:
    from dartlab.providers.edgar.report.employee import extractEmployee

    return extractEmployee(company)


def _extractAuditOpinion(company: "Company") -> pl.DataFrame | None:
    from dartlab.providers.edgar.report.auditOpinion import extractAuditOpinion

    return extractAuditOpinion(company)


def _extractCorporateBond(company: "Company") -> pl.DataFrame | None:
    from dartlab.providers.edgar.report.corporateBond import extractCorporateBond

    return extractCorporateBond(company)


def _extractExecutive(company: "Company") -> pl.DataFrame | None:
    from dartlab.providers.edgar.report.executive import extractExecutive

    return extractExecutive(company)


def _extractMajorHolder(company: "Company") -> pl.DataFrame | None:
    from dartlab.providers.edgar.report.majorHolder import extractMajorHolder

    return extractMajorHolder(company)


def _extractExecutivePay(company: "Company") -> pl.DataFrame | None:
    from dartlab.providers.edgar.report.executivePay import extractExecutivePay

    return extractExecutivePay(company)


def _extractCapitalChange(company: "Company") -> pl.DataFrame | None:
    from dartlab.providers.edgar.report.capitalChange import extractCapitalChange

    return extractCapitalChange(company)


def _extractOutsideDirector(company: "Company") -> pl.DataFrame | None:
    from dartlab.providers.edgar.report.outsideDirector import extractOutsideDirector

    return extractOutsideDirector(company)


def _extractMinorityHolder(company: "Company") -> pl.DataFrame | None:
    from dartlab.providers.edgar.report.minorityHolder import extractMinorityHolder

    return extractMinorityHolder(company)


def _extractInvestedCompany(company: "Company") -> pl.DataFrame | None:
    from dartlab.providers.edgar.report.investedCompany import extractInvestedCompany

    return extractInvestedCompany(company)


def _extractDebtSecurities(company: "Company") -> pl.DataFrame | None:
    from dartlab.providers.edgar.report.debtSecurities import extractDebtSecurities

    return extractDebtSecurities(company)


# ── 지원 apiType 매핑 ──

_SUPPORTED: dict[str, Any] = {
    "dividend": _extractDividend,
    "treasuryStock": _extractTreasuryStock,
    "stockTotal": _extractStockTotal,
    "employee": _extractEmployee,
    "auditOpinion": _extractAuditOpinion,
    "corporateBond": _extractCorporateBond,
    "executive": _extractExecutive,
    "majorHolder": _extractMajorHolder,
    "executivePay": _extractExecutivePay,
    "capitalChange": _extractCapitalChange,
    "outsideDirector": _extractOutsideDirector,
    "minorityHolder": _extractMinorityHolder,
    "investedCompany": _extractInvestedCompany,
    "debtSecurities": _extractDebtSecurities,
}
