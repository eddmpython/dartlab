"""DART 전용 복수 기업 비교 분석 클래스.

문자열은 KR 종목코드/회사명으로 해석한다.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import polars as pl

from dartlab.engines.dart.company import Company

_log = logging.getLogger("dartlab.engines.dart.compare")

AnyCompany = Company


_RATIO_FIELDS: dict[str, list[tuple[str, str]]] = {
    "profitability": [
        ("roe", "ROE (%)"),
        ("roa", "ROA (%)"),
        ("operatingMargin", "영업이익률 (%)"),
        ("netMargin", "순이익률 (%)"),
        ("grossMargin", "매출총이익률 (%)"),
        ("ebitdaMargin", "EBITDA마진 (%)"),
        ("costOfSalesRatio", "매출원가율 (%)"),
        ("sgaRatio", "판관비율 (%)"),
    ],
    "stability": [
        ("debtRatio", "부채비율 (%)"),
        ("currentRatio", "유동비율 (%)"),
        ("quickRatio", "당좌비율 (%)"),
        ("equityRatio", "자기자본비율 (%)"),
        ("interestCoverage", "이자보상배율 (x)"),
        ("netDebtRatio", "순차입금비율 (%)"),
        ("noncurrentRatio", "비유동비율 (%)"),
    ],
    "growth": [
        ("revenueGrowth3Y", "매출 3Y CAGR (%)"),
        ("revenueGrowth", "매출 YoY (%)"),
        ("operatingProfitGrowth", "영업이익 YoY (%)"),
        ("netProfitGrowth", "순이익 YoY (%)"),
        ("assetGrowth", "자산 YoY (%)"),
        ("equityGrowthRate", "자본 YoY (%)"),
    ],
    "efficiency": [
        ("totalAssetTurnover", "총자산회전율 (x)"),
        ("inventoryTurnover", "재고자산회전율 (x)"),
        ("receivablesTurnover", "매출채권회전율 (x)"),
        ("payablesTurnover", "매입채무회전율 (x)"),
    ],
    "cashflow": [
        ("fcf", "FCF"),
        ("operatingCfMargin", "영업CF마진 (%)"),
        ("operatingCfToNetIncome", "영업CF/순이익 (%)"),
        ("capexRatio", "CAPEX비율 (%)"),
        ("dividendPayoutRatio", "배당성향 (%)"),
    ],
    "valuation": [
        ("per", "PER (x)"),
        ("pbr", "PBR (x)"),
        ("psr", "PSR (x)"),
        ("evEbitda", "EV/EBITDA (x)"),
    ],
}

_SCALE_FIELDS: list[tuple[str, str]] = [
    ("revenueTTM", "매출(TTM)"),
    ("operatingIncomeTTM", "영업이익(TTM)"),
    ("netIncomeTTM", "순이익(TTM)"),
    ("totalAssets", "총자산"),
    ("totalEquity", "자본(지배)"),
    ("totalLiabilities", "부채총계"),
    ("cash", "현금성자산"),
    ("marketCap", "시가총액"),
    ("fcf", "FCF"),
    ("netDebt", "순차입금"),
]

_INSIGHT_AREAS = [
    "performance",
    "profitability",
    "health",
    "cashflow",
    "governance",
    "risk",
    "opportunity",
]


def _resolveCompany(arg: Any) -> AnyCompany:
    """문자열이면 DART Company로 변환, 아니면 그대로 반환."""
    if isinstance(arg, Company):
        return arg
    if isinstance(arg, str):
        return Company(arg)
    raise TypeError(f"str 또는 DART Company여야 합니다: {type(arg)}")


class Compare:
    """복수 기업 비교 분석.

    Example::

        c = Compare("005930", "000660")       # 문자열 직접
        c = Compare(Company("005930"), Company("000660"))

        c.ratios          # 전체 비율 비교 DataFrame
        c.profitability   # 수익성 비율만
        c.scale           # 규모 비교
        c.roeHistory      # ROE 연도별 추이
    """

    def __init__(self, *args: AnyCompany | str):
        if len(args) < 2:
            raise ValueError("비교하려면 최소 2개 기업이 필요합니다")
        self.companies: list[AnyCompany] = [_resolveCompany(a) for a in args]
        self._cache: dict[str, Any] = {}

    def __repr__(self):
        names = [c.corpName for c in self.companies]
        return f"Compare({', '.join(names)})"

    @property
    def _isAllKR(self) -> bool:
        return all(c.market == "KR" for c in self.companies)

    @property
    def _isMixed(self) -> bool:
        markets = {c.market for c in self.companies}
        return len(markets) > 1

    def _getName(self, c: AnyCompany) -> str:
        return c.corpName

    def _getMarket(self, c: AnyCompany) -> str:
        return c.market

    def _getId(self, c: AnyCompany) -> str:
        return getattr(c, "ticker", None) or getattr(c, "stockCode", "")

    def _baseRow(self, c: AnyCompany) -> dict[str, Any]:
        row: dict[str, Any] = {
            "name": self._getName(c),
            "market": self._getMarket(c),
            "id": self._getId(c),
        }
        if self._isMixed:
            row["currency"] = c.currency
        return row

    def _ratioCategory(self, category: str) -> pl.DataFrame:
        cacheKey = f"_ratio_{category}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        fields = _RATIO_FIELDS.get(category, [])
        rows = []
        for c in self.companies:
            r = c.ratios
            row = self._baseRow(c)
            if r is not None:
                for fieldName, _ in fields:
                    row[fieldName] = getattr(r, fieldName, None)
            rows.append(row)

        df = pl.DataFrame(rows)
        self._cache[cacheKey] = df
        return df

    # ══════════════════════════════════════
    # 재무비율 비교 — 전체 + 카테고리별
    # ══════════════════════════════════════

    @property
    def ratios(self) -> pl.DataFrame:
        """기업별 재무비율 비교 (전체 30+ 비율)."""
        if "_ratios" in self._cache:
            return self._cache["_ratios"]

        rows = []
        for c in self.companies:
            r = c.ratios
            row = self._baseRow(c)
            if r is not None:
                for fields in _RATIO_FIELDS.values():
                    for fieldName, _ in fields:
                        row[fieldName] = getattr(r, fieldName, None)
            rows.append(row)

        df = pl.DataFrame(rows)
        self._cache["_ratios"] = df
        return df

    @property
    def profitability(self) -> pl.DataFrame:
        """수익성 비율 비교 (ROE, ROA, 마진 등)."""
        return self._ratioCategory("profitability")

    @property
    def stability(self) -> pl.DataFrame:
        """안정성 비율 비교 (부채비율, 유동비율 등)."""
        return self._ratioCategory("stability")

    @property
    def growth(self) -> pl.DataFrame:
        """성장성 비율 비교 (매출/이익 성장률 등)."""
        return self._ratioCategory("growth")

    @property
    def efficiency(self) -> pl.DataFrame:
        """효율성 비율 비교 (회전율 등)."""
        return self._ratioCategory("efficiency")

    @property
    def cashflowRatios(self) -> pl.DataFrame:
        """현금흐름 비율 비교 (FCF, CF마진 등)."""
        return self._ratioCategory("cashflow")

    @property
    def valuation(self) -> pl.DataFrame:
        """밸류에이션 비율 비교 (PER, PBR 등)."""
        return self._ratioCategory("valuation")

    # ══════════════════════════════════════
    # 규모 비교 (절대값)
    # ══════════════════════════════════════

    @property
    def scale(self) -> pl.DataFrame:
        """기업별 규모 비교 (매출, 자산, 시총 등 절대값).

        KR+US 혼합 시 currency 컬럼이 추가된다 (KRW/USD).
        """
        if "_scale" in self._cache:
            return self._cache["_scale"]

        rows = []
        for c in self.companies:
            r = c.ratios
            row = self._baseRow(c)
            if r is not None:
                for fieldName, _ in _SCALE_FIELDS:
                    row[fieldName] = getattr(r, fieldName, None)
            rows.append(row)

        df = pl.DataFrame(rows)
        self._cache["_scale"] = df
        return df

    # ══════════════════════════════════════
    # 인사이트 비교
    # ══════════════════════════════════════

    @property
    def insights(self) -> pl.DataFrame:
        """기업별 인사이트 등급 비교 테이블."""
        if "_insights" in self._cache:
            return self._cache["_insights"]

        rows = []
        for c in self.companies:
            ins = c.insights
            row = self._baseRow(c)
            if ins is not None:
                for area in _INSIGHT_AREAS:
                    result = getattr(ins, area, None)
                    row[area] = result.grade if result else None
                row["profile"] = ins.profile
            rows.append(row)

        df = pl.DataFrame(rows)
        self._cache["_insights"] = df
        return df

    @property
    def insightDetails(self) -> pl.DataFrame:
        """기업별 인사이트 등급 + 요약 상세 비교 테이블."""
        if "_insightDetails" in self._cache:
            return self._cache["_insightDetails"]

        rows = []
        for c in self.companies:
            ins = c.insights
            row = self._baseRow(c)
            if ins is not None:
                for area in _INSIGHT_AREAS:
                    result = getattr(ins, area, None)
                    if result:
                        row[f"{area}_grade"] = result.grade
                        row[f"{area}_summary"] = result.summary
                    else:
                        row[f"{area}_grade"] = None
                        row[f"{area}_summary"] = None
                row["profile"] = ins.profile
                row["summary"] = ins.summary
            rows.append(row)

        df = pl.DataFrame(rows)
        self._cache["_insightDetails"] = df
        return df

    # ══════════════════════════════════════
    # 연도별 절대값 시계열 비교
    # ══════════════════════════════════════

    @property
    def revenue(self) -> pl.DataFrame:
        """기업별 연도별 매출 비교 테이블."""
        return self._annualMetric("IS", "sales")

    @property
    def operatingProfit(self) -> pl.DataFrame:
        """기업별 연도별 영업이익 비교 테이블."""
        return self._annualMetric("IS", "operating_profit")

    @property
    def netIncome(self) -> pl.DataFrame:
        """기업별 연도별 순이익 비교 테이블."""
        return self._annualMetric("IS", "net_profit")

    @property
    def totalAssets(self) -> pl.DataFrame:
        """기업별 연도별 총자산 비교 테이블."""
        return self._annualMetric("BS", "total_assets")

    @property
    def equity(self) -> pl.DataFrame:
        """기업별 연도별 자본(지배기업) 비교 테이블."""
        return self._annualMetric("BS", "owners_of_parent_equity")

    @property
    def operatingCashflow(self) -> pl.DataFrame:
        """기업별 연도별 영업활동CF 비교 테이블."""
        return self._annualMetric("CF", "operating_cashflow")

    def _annualMetric(self, stmt: str, snakeId: str) -> pl.DataFrame:
        """연도별 단일 지표 비교."""
        cacheKey = f"_annual_{stmt}_{snakeId}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        allYears: set[str] = set()
        companyData: list[tuple[dict[str, Any], dict[str, float | None]]] = []

        for c in self.companies:
            annual = c.annual
            baseRow = self._baseRow(c)
            if annual is None:
                companyData.append((baseRow, {}))
                continue
            aSeries, years = annual
            vals = aSeries.get(stmt, {}).get(snakeId, [])
            yearMap = {}
            for i, y in enumerate(years):
                if i < len(vals):
                    yearMap[y] = vals[i]
            allYears.update(yearMap.keys())
            companyData.append((baseRow, yearMap))

        sortedYears = sorted(allYears)
        rows = []
        for baseRow, yearMap in companyData:
            row = dict(baseRow)
            for y in sortedYears:
                row[y] = yearMap.get(y)
            rows.append(row)

        df = pl.DataFrame(rows)
        self._cache[cacheKey] = df
        return df

    # ══════════════════════════════════════
    # 연도별 비율 시계열 비교
    # ══════════════════════════════════════

    def ratioHistory(self, ratioName: str) -> pl.DataFrame:
        """특정 비율의 연도별 추이 비교.

        Args:
            ratioName: 비율 snakeId (예: "roe", "debtRatio", "operatingMargin")

        Returns:
            DataFrame — name | 2019 | 2020 | ... 형태
        """
        cacheKey = f"_ratioHist_{ratioName}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        allYears: set[str] = set()
        companyData: list[tuple[str, dict[str, Optional[float]]]] = []

        for c in self.companies:
            name = self._getName(c)
            rs = c.ratioSeries
            if rs is None:
                companyData.append((name, {}))
                continue
            ratioDict, years = rs
            vals = ratioDict.get("RATIO", {}).get(ratioName, [])
            yearMap = {}
            for i, y in enumerate(years):
                if i < len(vals):
                    yearMap[y] = vals[i]
            allYears.update(yearMap.keys())
            companyData.append((name, yearMap))

        sortedYears = sorted(allYears)
        rows = []
        for name, yearMap in companyData:
            row: dict[str, Any] = {"name": name}
            for y in sortedYears:
                row[y] = yearMap.get(y)
            rows.append(row)

        df = pl.DataFrame(rows)
        self._cache[cacheKey] = df
        return df

    @property
    def roeHistory(self) -> pl.DataFrame:
        """ROE 연도별 추이 비교."""
        return self.ratioHistory("roe")

    @property
    def debtRatioHistory(self) -> pl.DataFrame:
        """부채비율 연도별 추이 비교."""
        return self.ratioHistory("debtRatio")

    @property
    def marginHistory(self) -> pl.DataFrame:
        """영업이익률 연도별 추이 비교."""
        return self.ratioHistory("operatingMargin")

    @property
    def netMarginHistory(self) -> pl.DataFrame:
        """순이익률 연도별 추이 비교."""
        return self.ratioHistory("netMargin")

    @property
    def currentRatioHistory(self) -> pl.DataFrame:
        """유동비율 연도별 추이 비교."""
        return self.ratioHistory("currentRatio")

    # ══════════════════════════════════════
    # KR 전용 — 정기보고서 비교 (report)
    # ══════════════════════════════════════

    @property
    def dividendCompare(self) -> pl.DataFrame | None:
        """배당 시계열 비교 (KR 전용).

        DPS, 배당수익률을 기업별로 비교한다.
        모든 기업이 KR이 아니면 None.
        """
        if not self._isAllKR:
            _log.debug("dividendCompare: KR 전용 — US 기업 포함 시 None")
            return None
        return self._reportTimeseries(
            "dividend",
            [
                ("dps", "DPS (원)"),
                ("dividendYield", "배당수익률 (%)"),
            ],
        )

    @property
    def employeeCompare(self) -> pl.DataFrame | None:
        """직원현황 비교 (KR 전용).

        총 직원수, 평균 월급을 기업별로 비교한다.
        모든 기업이 KR이 아니면 None.
        """
        if not self._isAllKR:
            _log.debug("employeeCompare: KR 전용 — US 기업 포함 시 None")
            return None
        return self._reportTimeseries(
            "employee",
            [
                ("totalEmployee", "총 직원수"),
                ("avgMonthlySalary", "평균 월급 (만원)"),
            ],
        )

    @property
    def majorHolderCompare(self) -> pl.DataFrame | None:
        """최대주주 지분율 비교 (KR 전용).

        최대주주 + 특수관계인 합산 지분율을 기업별로 비교한다.
        모든 기업이 KR이 아니면 None.
        """
        if not self._isAllKR:
            _log.debug("majorHolderCompare: KR 전용 — US 기업 포함 시 None")
            return None
        return self._reportTimeseries(
            "majorHolder",
            [
                ("totalShareRatio", "최대주주 지분율 (%)"),
            ],
        )

    @property
    def auditCompare(self) -> pl.DataFrame | None:
        """감사의견 비교 (KR 전용).

        감사인, 감사의견을 기업별로 비교한다.
        모든 기업이 KR이 아니면 None.
        """
        if not self._isAllKR:
            _log.debug("auditCompare: KR 전용 — US 기업 포함 시 None")
            return None
        cacheKey = "_auditCompare"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        allYears: set[int] = set()
        companyData: list[tuple[str, dict[int, str], dict[int, str]]] = []

        for c in self.companies:
            name = self._getName(c)
            audit = c.report.audit
            if audit is None:
                companyData.append((name, {}, {}))
                continue
            opinionMap = {}
            auditorMap = {}
            for i, y in enumerate(audit.years):
                if i < len(audit.opinions):
                    opinionMap[y] = audit.opinions[i]
                if i < len(audit.auditors):
                    auditorMap[y] = audit.auditors[i]
            allYears.update(opinionMap.keys())
            companyData.append((name, opinionMap, auditorMap))

        sortedYears = sorted(allYears)
        rows = []
        for name, opinionMap, auditorMap in companyData:
            row: dict[str, Any] = {"name": name}
            for y in sortedYears:
                row[f"{y}_opinion"] = opinionMap.get(y)
                row[f"{y}_auditor"] = auditorMap.get(y)
            rows.append(row)

        df = pl.DataFrame(rows) if rows else pl.DataFrame()
        self._cache[cacheKey] = df
        return df

    def _reportTimeseries(
        self,
        reportName: str,
        fields: list[tuple[str, str]],
    ) -> pl.DataFrame | None:
        """KR report 시계열 비교 공통 로직."""
        cacheKey = f"_report_{reportName}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        allYears: set[int] = set()
        companyData: list[tuple[str, dict[str, dict[int, float | None]]]] = []

        for c in self.companies:
            name = self._getName(c)
            result = getattr(c.report, reportName, None)
            if result is None:
                companyData.append((name, {}))
                continue
            fieldMaps: dict[str, dict[int, float | None]] = {}
            for fieldAttr, _ in fields:
                vals = getattr(result, fieldAttr, [])
                yearMap: dict[int, float | None] = {}
                for i, y in enumerate(result.years):
                    if i < len(vals):
                        yearMap[y] = vals[i]
                fieldMaps[fieldAttr] = yearMap
                allYears.update(yearMap.keys())
            companyData.append((name, fieldMaps))

        sortedYears = sorted(allYears)
        rows = []
        for name, fieldMaps in companyData:
            row: dict[str, Any] = {"name": name}
            for y in sortedYears:
                for fieldAttr, _ in fields:
                    col = f"{y}_{fieldAttr}" if len(fields) > 1 else str(y)
                    row[col] = fieldMaps.get(fieldAttr, {}).get(y)
            rows.append(row)

        df = pl.DataFrame(rows) if rows else pl.DataFrame()
        self._cache[cacheKey] = df
        return df
