"""종목 단위 통합 분석 클래스.

사용법::

    from dartlab import Company

    c = Company("005930")       # 한국 (DART)
    c = Company("삼성전자")      # 한국 (회사명)
    c = Company("AAPL")         # 미국 (EDGAR)
    c.BS                        # 재무상태표 DataFrame
    c.ratios                    # 재무비율
    c.insights                  # 인사이트 등급
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dartlab.usCompany import USCompany

import polars as pl

pl.Config.set_fmt_str_lengths(80)
pl.Config.set_tbl_width_chars(200)

from dartlab.core.dataLoader import (
    DART_VIEWER,
    buildIndex,
    extractCorpName,
    loadData,
)
from dartlab.core.kindList import (
    codeToName,
    getKindList,
    nameToCode,
    searchName,
)

# ── 모듈 레지스트리 (core/registry.py에서 자동 생성) ──
# (모듈 import 경로, 함수명, 한글 라벨, primary DataFrame 추출)
# fsSummary/statements는 내부 디스패치 전용 (BS/IS/CF property가 statements를 호출)
from dartlab.core.registry import getModuleEntries as _getModuleEntries
from dartlab.engines.dart.docs.notes import Notes

_MODULE_REGISTRY: list[tuple[str, str, str, Any]] = [
    ("dartlab.engines.dart.docs.finance.summary", "fsSummary", "요약재무정보", None),
    ("dartlab.engines.dart.docs.finance.statements", "statements", "재무제표", None),
] + [
    (e.modulePath, e.funcName, e.label, e.extractor)
    for e in _getModuleEntries()
]

# 모듈명 → 레지스트리 인덱스
_MODULE_INDEX: dict[str, int] = {entry[1]: i for i, entry in enumerate(_MODULE_REGISTRY)}

# all()에서 사용할 순서 (fsSummary, statements 제외 — BS/IS/CF로 대체)
_ALL_PROPERTIES: list[tuple[str, str]] = [
    ("BS", "재무상태표"),
    ("IS", "손익계산서"),
    ("CF", "현금흐름표"),
]
for entry in _MODULE_REGISTRY:
    name = entry[1]
    if name in ("fsSummary", "statements", "companyOverview"):
        continue
    _ALL_PROPERTIES.append((name, entry[2]))


def _import_and_call(modulePath: str, funcName: str, stockCode: str, **kwargs) -> Any:
    """모듈을 lazy import하고 함수 호출."""
    import importlib
    mod = importlib.import_module(modulePath)
    func = getattr(mod, funcName)
    return func(stockCode, **kwargs)


def _ensureData(stockCode: str, category: str) -> bool:
    """로컬에 parquet이 있으면 True, 없으면 다운로드 시도 후 결과 반환."""
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.core.dataLoader import _dataDir, _download
    dest = _dataDir(category) / f"{stockCode}.parquet"
    if dest.exists():
        return True
    try:
        _download(stockCode, dest, category)
        label = DATA_RELEASES[category]["label"]
        print(f"[dartlab] {stockCode} ({label}) 다운로드 완료")
        return True
    except (OSError, RuntimeError):
        return False


class _ReportAccessor:
    """KRCompany.report 네임스페이스 — reportEngine pivot 결과 접근."""

    def __init__(self, company: KRCompany):
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
        result = extractClean(self._company.stockCode, apiType)
        self._cache[cacheKey] = result
        return result

    def extractAnnual(self, apiType: str, quarterNum: int | None = None) -> pl.DataFrame | None:
        """apiType별 연간 DataFrame 반환."""
        cacheKey = f"_annual_{apiType}_{quarterNum}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.dart.report import extractAnnual as _extractAnnual
        result = _extractAnnual(self._company.stockCode, apiType, quarterNum)
        self._cache[cacheKey] = result
        return result

    @property
    def dividend(self):
        """배당 시계열 (DividendResult)."""
        return self._pivot("dividend")

    @property
    def employee(self):
        """직원현황 시계열 (EmployeeResult)."""
        return self._pivot("employee")

    @property
    def majorHolder(self):
        """최대주주현황 시계열 (MajorHolderResult)."""
        return self._pivot("majorHolder")

    @property
    def executive(self):
        """임원현황 (ExecutiveResult)."""
        return self._pivot("executive")

    @property
    def audit(self):
        """감사의견 시계열 (AuditResult)."""
        return self._pivot("audit")

    def __repr__(self):
        from dartlab.engines.dart.report.types import API_TYPES
        return f"ReportAccessor({len(API_TYPES)} apiTypes)"


class KRCompany:
    """DART 기반 한국 상장기업 분석.

    property로 바로 DataFrame에 접근할 수 있다. 접근 시 lazy 로딩 + 캐싱.

    Example::

        c = Company("005930")           # 삼성전자
        c.BS                             # 재무상태표 DataFrame
        c.notes.inventory                # 주석 · 재고자산
        c.notes["재고자산"]               # 동일
        d = c.all()                      # 전체 dict

        import dartlab
        dartlab.verbose = False          # 출력 끄기
    """

    def __init__(self, codeOrName: str):
        if re.match(r"^\d{6}$", codeOrName):
            self.stockCode = codeOrName
        else:
            code = nameToCode(codeOrName)
            if code is None:
                raise ValueError(f"'{codeOrName}'에 해당하는 종목을 찾을 수 없음")
            self.stockCode = code
        self._cache: dict[str, Any] = {}

        self._hasDocs = _ensureData(self.stockCode, "docs")
        self._hasFinance = _ensureData(self.stockCode, "finance")
        self._hasReport = _ensureData(self.stockCode, "report")

        if self._hasDocs:
            df = loadData(self.stockCode, category="docs")
            self.corpName = extractCorpName(df)
        else:
            self.corpName = codeToName(self.stockCode)

        if self._hasFinance:
            from dartlab.engines.dart.finance.pivot import buildTimeseries
            ts = buildTimeseries(self.stockCode)
            if ts is not None:
                self._cache["_finance_q_CFS"] = ts
            else:
                self._hasFinance = False

        if not self._hasDocs and not self._hasFinance and not self._hasReport:
            raise ValueError(f"'{self.stockCode}' 데이터 없음 (docs/finance/report 모두 없음)")

        self.notes = Notes(self) if self._hasDocs else None
        self.report = _ReportAccessor(self) if self._hasReport else None

    def __repr__(self):
        from dartlab import config
        if config.verbose:
            from dartlab.display import printRepr
            from dartlab.engines.dart.docs.notes import _REGISTRY as notesRegistry
            nProps = len([p for p in _ALL_PROPERTIES if p[0] not in ("BS", "IS", "CF")])
            nNotes = len(notesRegistry) if self._hasDocs else 0
            printRepr(self.corpName, self.stockCode, nProps, nNotes)
            return ""
        return f"KRCompany({self.stockCode}, {self.corpName})"

    def guide(self):
        """전체 사용 가이드 출력."""
        from dartlab.display import printGuide
        from dartlab.engines.dart.docs.notes import _REGISTRY as notesRegistry
        props = [p[0] for p in _ALL_PROPERTIES if p[0] not in ("BS", "IS", "CF")]
        if self._hasDocs:
            noteKeys = list(notesRegistry.keys())
            noteKeysKr = [v[1] for v in notesRegistry.values()]
        else:
            noteKeys = []
            noteKeysKr = []
        printGuide(self.corpName, self.stockCode, props, noteKeys, noteKeysKr)

    # ── 내부 호출 ──

    def _call_module(self, name: str, **kwargs) -> Any:
        """모듈 호출 + 캐싱. Notes에서도 사용."""
        if not self._hasDocs:
            return None
        cacheKey = f"{name}:{kwargs}" if kwargs else name
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        idx = _MODULE_INDEX[name]
        entry = _MODULE_REGISTRY[idx]
        result = _import_and_call(entry[0], entry[1], self.stockCode, **kwargs)
        self._cache[cacheKey] = result
        return result

    def _call_notesDetail(self, keyword: str) -> Any:
        """notesDetail 호출 (키워드별 캐싱)."""
        if not self._hasDocs:
            return None
        cacheKey = f"notesDetail:{keyword}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        result = _import_and_call(
            "dartlab.engines.dart.docs.finance.notesDetail", "notesDetail",
            self.stockCode, keyword=keyword,
        )
        self._cache[cacheKey] = result
        return result

    def _get_primary(self, name: str, **kwargs) -> Any:
        """모듈 호출 후 primary DataFrame 추출."""
        from dartlab import config
        idx = _MODULE_INDEX[name]
        entry = _MODULE_REGISTRY[idx]
        label = entry[2]

        if config.verbose:
            print(f"  ▶ {self.corpName} · {label}")

        result = self._call_module(name, **kwargs)
        extractor = entry[3]
        if result is None:
            return None
        if extractor is None:
            return result
        return extractor(result)

    # ── 인덱스·메타 ──

    @staticmethod
    def listing(*, forceRefresh: bool = False) -> pl.DataFrame:
        """KRX 전체 상장법인 목록 (KIND 기준)."""
        return getKindList(forceRefresh=forceRefresh)

    @staticmethod
    def search(keyword: str) -> pl.DataFrame:
        """회사명 부분 검색 (KIND 목록 기준)."""
        return searchName(keyword)

    @staticmethod
    def resolve(codeOrName: str) -> str | None:
        """종목코드 또는 회사명 → 종목코드 변환."""
        if re.match(r"^\d{6}$", codeOrName):
            return codeOrName
        return nameToCode(codeOrName)

    @staticmethod
    def codeName(stockCode: str) -> str | None:
        """종목코드 → 회사명 변환."""
        return codeToName(stockCode)

    @staticmethod
    def status() -> pl.DataFrame:
        """로컬에 보유한 전체 종목 인덱스."""
        return buildIndex()

    def docs(self) -> pl.DataFrame:
        """이 종목의 공시 문서 목록 + DART 뷰어 링크."""
        if not self._hasDocs:
            return pl.DataFrame(schema={"year": pl.Utf8, "rceptDate": pl.Utf8, "rceptNo": pl.Utf8, "reportType": pl.Utf8, "dartUrl": pl.Utf8})
        df = loadData(self.stockCode)
        docs = (
            df.select("year", "rcept_date", "rcept_no", "report_type")
            .unique(subset=["rcept_no"])
            .with_columns(
                pl.lit(DART_VIEWER).add(pl.col("rcept_no")).alias("dartUrl"),
            )
            .rename({
                "report_type": "reportType",
                "rcept_date": "rceptDate",
                "rcept_no": "rceptNo",
            })
            .sort("year", "rceptDate", descending=[True, True])
        )
        return docs

    # ── 원본 데이터 (property) ──

    @property
    def rawDocs(self) -> pl.DataFrame | None:
        """공시 문서 원본 parquet 전체 (가공 전)."""
        if not self._hasDocs:
            return None
        cacheKey = "_rawDocs"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        df = loadData(self.stockCode, category="docs")
        self._cache[cacheKey] = df
        return df

    @property
    def rawFinance(self) -> pl.DataFrame | None:
        """재무제표 원본 parquet 전체 (가공 전)."""
        if not self._hasFinance:
            return None
        cacheKey = "_rawFinance"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        df = loadData(self.stockCode, category="finance")
        self._cache[cacheKey] = df
        return df

    @property
    def rawReport(self) -> pl.DataFrame | None:
        """정기보고서 원본 parquet 전체 (가공 전)."""
        if not self._hasReport:
            return None
        cacheKey = "_rawReport"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        df = loadData(self.stockCode, category="report")
        self._cache[cacheKey] = df
        return df

    # ── 재무제표 (property) ──

    @property
    def BS(self) -> pl.DataFrame | None:
        """재무상태표 DataFrame."""
        r = self._call_module("statements")
        return r.BS if r else None

    @property
    def IS(self) -> pl.DataFrame | None:
        """손익계산서 DataFrame."""
        r = self._call_module("statements")
        return r.IS if r else None

    @property
    def CF(self) -> pl.DataFrame | None:
        """현금흐름표 DataFrame."""
        r = self._call_module("statements")
        return r.CF if r else None

    # ── 정기보고서 (property) ──

    @property
    def dividend(self) -> pl.DataFrame | None:
        """배당 시계열 DataFrame."""
        return self._get_primary("dividend")

    @property
    def majorHolder(self) -> pl.DataFrame | None:
        """최대주주 시계열 DataFrame."""
        return self._get_primary("majorHolder")

    @property
    def employee(self) -> pl.DataFrame | None:
        """직원 현황 시계열 DataFrame."""
        return self._get_primary("employee")

    @property
    def subsidiary(self) -> pl.DataFrame | None:
        """자회사 투자 시계열 DataFrame."""
        return self._get_primary("subsidiary")

    @property
    def bond(self) -> pl.DataFrame | None:
        """채무증권 발행 시계열 DataFrame."""
        return self._get_primary("bond")

    @property
    def shareCapital(self) -> pl.DataFrame | None:
        """주식 현황 시계열 DataFrame."""
        return self._get_primary("shareCapital")

    @property
    def executive(self) -> pl.DataFrame | None:
        """등기임원 집계 시계열 DataFrame."""
        return self._get_primary("executive")

    @property
    def executivePay(self) -> pl.DataFrame | None:
        """임원 보수 시계열 DataFrame."""
        return self._get_primary("executivePay")

    @property
    def audit(self) -> pl.DataFrame | None:
        """감사의견 시계열 DataFrame."""
        return self._get_primary("audit")

    @property
    def boardOfDirectors(self) -> pl.DataFrame | None:
        """이사회 시계열 DataFrame."""
        return self._get_primary("boardOfDirectors")

    @property
    def capitalChange(self) -> pl.DataFrame | None:
        """자본금 변동 시계열 DataFrame."""
        return self._get_primary("capitalChange")

    @property
    def contingentLiability(self) -> pl.DataFrame | None:
        """우발부채 시계열 DataFrame."""
        return self._get_primary("contingentLiability")

    @property
    def internalControl(self) -> pl.DataFrame | None:
        """내부통제 시계열 DataFrame."""
        return self._get_primary("internalControl")

    @property
    def relatedPartyTx(self) -> pl.DataFrame | None:
        """관계자거래 시계열 DataFrame."""
        return self._get_primary("relatedPartyTx")

    @property
    def rnd(self) -> pl.DataFrame | None:
        """R&D 비용 시계열 DataFrame."""
        return self._get_primary("rnd")

    @property
    def sanction(self) -> pl.DataFrame | None:
        """제재 현황 DataFrame."""
        return self._get_primary("sanction")

    @property
    def affiliateGroup(self) -> pl.DataFrame | None:
        """계열사 목록 DataFrame."""
        return self._get_primary("affiliateGroup")

    @property
    def affiliate(self) -> pl.DataFrame | None:
        """관계기업 투자 변동 시계열 DataFrame."""
        return self._get_primary("affiliate")

    @property
    def fundraising(self) -> pl.DataFrame | None:
        """증자/감자 이력 DataFrame."""
        return self._get_primary("fundraising")

    @property
    def productService(self) -> pl.DataFrame | None:
        """주요 제품/서비스 DataFrame."""
        return self._get_primary("productService")

    @property
    def salesOrder(self) -> pl.DataFrame | None:
        """매출/수주 DataFrame."""
        return self._get_primary("salesOrder")

    @property
    def riskDerivative(self) -> pl.DataFrame | None:
        """위험관리/파생거래 DataFrame."""
        return self._get_primary("riskDerivative")

    @property
    def articlesOfIncorporation(self) -> pl.DataFrame | None:
        """정관 변경이력 DataFrame."""
        return self._get_primary("articlesOfIncorporation")

    @property
    def otherFinance(self) -> pl.DataFrame | None:
        """기타 재무 DataFrame."""
        return self._get_primary("otherFinance")

    @property
    def companyHistory(self) -> pl.DataFrame | None:
        """회사 연혁 DataFrame."""
        return self._get_primary("companyHistory")

    @property
    def shareholderMeeting(self) -> pl.DataFrame | None:
        """주주총회 안건 DataFrame."""
        return self._get_primary("shareholderMeeting")

    @property
    def auditSystem(self) -> pl.DataFrame | None:
        """감사제도 DataFrame."""
        return self._get_primary("auditSystem")

    @property
    def investmentInOther(self) -> pl.DataFrame | None:
        """타법인출자 현황 DataFrame."""
        return self._get_primary("investmentInOther")

    @property
    def companyOverviewDetail(self) -> dict | None:
        """회사 개요 상세 (설립일, 상장일, 대표이사 등)."""
        return self._get_primary("companyOverviewDetail")

    # ── 부문정보 (property) ──

    @property
    def segments(self) -> pl.DataFrame | None:
        """부문별 매출 시계열 DataFrame."""
        return self._get_primary("segments")

    # ── 공시 서술 (property) ──

    @property
    def business(self) -> list | None:
        """사업의 내용 섹션 목록."""
        return self._get_primary("business")

    @property
    def overview(self) -> Any:
        """회사 개요 정량 데이터."""
        from dartlab import config
        if config.verbose:
            print(f"  ▶ {self.corpName} · 회사개요정량")
        return self._call_module("companyOverview")

    @property
    def mdna(self) -> str | None:
        """MD&A 개요 텍스트."""
        return self._get_primary("mdna")

    @property
    def rawMaterial(self) -> Any:
        """원재료/설비/시설투자 데이터."""
        from dartlab import config
        if config.verbose:
            print(f"  ▶ {self.corpName} · 원재료설비")
        return self._call_module("rawMaterial")

    # ── holderOverview (별도 함수) ──

    @property
    def holderOverview(self) -> Any:
        """5% 이상 주주, 소액주주, 의결권 현황."""
        if not self._hasDocs:
            return None
        cacheKey = "holderOverview"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab import config
        if config.verbose:
            print(f"  ▶ {self.corpName} · 주주현황")
        result = _import_and_call(
            "dartlab.engines.dart.docs.finance.majorHolder", "holderOverview", self.stockCode,
        )
        self._cache[cacheKey] = result
        return result

    # ── fsSummary (별도 — 파라미터 있음) ──

    def fsSummary(self, ifrsOnly: bool = True, period: str = "y"):
        """요약재무정보 시계열 + 브릿지 매칭 + 전환점 탐지."""
        return self._call_module("fsSummary", ifrsOnly=ifrsOnly, period=period)

    # ── financeEngine (숫자 재무 데이터) ──

    def _getFinanceBuild(self, period: str = "q", fsDivPref: str = "CFS"):
        """finance parquet 시계열 빌드 (캐싱).

        Args:
            period: "q" (분기별 standalone), "y" (연도별), "cum" (분기별 누적).
            fsDivPref: "CFS" (연결) 또는 "OFS" (별도).
        """
        cacheKey = f"_finance_{period}_{fsDivPref}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        from dartlab.engines.dart.finance.pivot import buildAnnual, buildCumulative, buildTimeseries

        builders = {"q": buildTimeseries, "y": buildAnnual, "cum": buildCumulative}
        builder = builders.get(period, buildTimeseries)
        result = builder(self.stockCode, fsDivPref=fsDivPref)
        self._cache[cacheKey] = result
        return result

    def getTimeseries(self, period: str = "q", fsDivPref: str = "CFS"):
        """재무 시계열 조회.

        Args:
            period: "q" (분기별 standalone), "y" (연도별), "cum" (분기별 누적).
            fsDivPref: "CFS" (연결) 또는 "OFS" (별도).

        Returns:
            (series, periods) 또는 None.
            series = {"BS": {"snakeId": [값...]}, "IS": {...}, "CF": {...}}
            periods = ["2016-Q1", ...] (q/cum) 또는 ["2016", ...] (y)

        Example::

            c = Company("005930")
            series, periods = c.getTimeseries("y")
            series, periods = c.getTimeseries("q", fsDivPref="OFS")
        """
        return self._getFinanceBuild(period, fsDivPref)

    def getRatios(self, fsDivPref: str = "CFS"):
        """재무비율 계산.

        Args:
            fsDivPref: "CFS" (연결) 또는 "OFS" (별도).

        Returns:
            RatioResult dataclass.

        Example::

            c = Company("005930")
            c.getRatios().roe
            c.getRatios("OFS").debtRatio
        """
        cacheKey = f"_ratios_{fsDivPref}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.common.finance.ratios import calcRatios
        ts = self._getFinanceBuild("q", fsDivPref)
        if ts is None:
            return None
        series, _ = ts
        result = calcRatios(series)
        self._cache[cacheKey] = result
        return result

    @property
    def ratios(self):
        """재무비율 (연결 기준, ROE, ROA, 마진, 부채비율 등).

        Returns:
            RatioResult dataclass.

        Example::

            c = Company("005930")
            c.ratios.roe            # 8.57
            c.ratios.operatingMargin  # 10.88
            c.ratios.debtRatio      # 27.93
        """
        return self.getRatios("CFS")

    @property
    def timeseries(self):
        """분기별 standalone 시계열 (연결 기준).

        Returns:
            (series, periods) 또는 None.
            series = {"BS": {"snakeId": [값...]}, "IS": {...}, "CF": {...}}
            periods = ["2016-Q1", "2016-Q2", ..., "2024-Q4"]

        Example::

            c = Company("005930")
            series, periods = c.timeseries
            series["IS"]["sales"]  # 분기별 매출 시계열
        """
        return self._getFinanceBuild("q", "CFS")

    @property
    def annual(self):
        """연도별 시계열 (연결 기준).

        Returns:
            (series, years) 또는 None.

        Example::

            c = Company("005930")
            series, years = c.annual
            series["IS"]["sales"]  # 연도별 매출 시계열
        """
        return self._getFinanceBuild("y", "CFS")

    @property
    def cumulative(self):
        """분기별 누적 시계열 (연결 기준).

        Returns:
            (series, periods) 또는 None.

        Example::

            c = Company("005930")
            series, periods = c.cumulative
        """
        return self._getFinanceBuild("cum", "CFS")

    @property
    def sceMatrix(self):
        """자본변동표 연도별 매트릭스 (연결 기준).

        Returns:
            (matrix, years) 또는 None.
            matrix[year][cause][detail] = 금액
            years = ["2016", ..., "2024"]

        Example::

            c = Company("005930")
            matrix, years = c.sceMatrix
            matrix["2024"]["net_income"]["retained_earnings"]
        """
        if not self._hasFinance:
            return None
        cacheKey = "_sceMatrix_CFS"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.dart.finance.pivot import buildSceMatrix
        result = buildSceMatrix(self.stockCode)
        self._cache[cacheKey] = result
        return result

    @property
    def sce(self):
        """자본변동표 연도별 시계열 (연결 기준).

        Returns:
            (series, years) 또는 None.
            series["SCE"]["cause__detail"] = [v2016, ..., v2024]
            years = ["2016", ..., "2024"]

        Example::

            c = Company("005930")
            series, years = c.sce
            series["SCE"]["net_income__retained_earnings"]
        """
        if not self._hasFinance:
            return None
        cacheKey = "_sceAnnual_CFS"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.dart.finance.pivot import buildSceAnnual
        result = buildSceAnnual(self.stockCode)
        self._cache[cacheKey] = result
        return result

    @property
    def ratioSeries(self):
        """재무비율 연도별 시계열 (IS/BS/CF와 동일한 dict 구조).

        Returns:
            ({"RATIO": {snakeId: [v1, v2, ...]}}, years) 또는 None.

        Example::

            c = Company("005930")
            series, years = c.ratioSeries
            series["RATIO"]["roe"]  # [8.69, 13.20, 16.55, ...]
        """
        if not self._hasFinance:
            return None
        cacheKey = "_ratioSeries_CFS"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        annualResult = self.annual
        if annualResult is None:
            return None
        annualSeries, years = annualResult
        from dartlab.engines.common.finance.ratios import calcRatioSeries, toSeriesDict
        rs = calcRatioSeries(annualSeries, years)
        result = toSeriesDict(rs)
        self._cache[cacheKey] = result
        return result

    # ── 섹터 분류 ──

    @property
    def sector(self):
        """WICS 투자 섹터 분류 (KIND 업종 + 키워드 기반).

        Returns:
            SectorInfo (sector, industryGroup, confidence, source).

        Example::

            c = Company("005930")
            c.sector              # SectorInfo(IT/반도체와반도체장비, conf=1.00, src=override)
            c.sector.sector       # Sector.IT
            c.sector.industryGroup  # IndustryGroup.SEMICONDUCTOR
        """
        cacheKey = "_sector"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.sector import classify
        kindDf = getKindList()
        row = kindDf.filter(pl.col("종목코드") == self.stockCode)
        kindIndustry = row["업종"][0] if row.height > 0 and "업종" in kindDf.columns else None
        mainProducts = row["주요제품"][0] if row.height > 0 and "주요제품" in kindDf.columns else None
        result = classify(self.corpName or "", kindIndustry, mainProducts)
        self._cache[cacheKey] = result
        return result

    @property
    def sectorParams(self):
        """현재 종목의 섹터별 밸류에이션 파라미터.

        Returns:
            SectorParams (discountRate, growthRate, perMultiple, ...).

        Example::

            c = Company("005930")
            c.sectorParams.perMultiple   # 15
            c.sectorParams.discountRate  # 13.0
        """
        cacheKey = "_sectorParams"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.sector import getParams
        result = getParams(self.sector)
        self._cache[cacheKey] = result
        return result

    # ── 규모 랭크 ──

    @property
    def rank(self):
        """전체 시장 + 섹터 내 규모 순위 (매출/자산/성장률).

        스냅샷이 없으면 None 반환. buildSnapshot()으로 사전 빌드 필요.

        Returns:
            RankInfo 또는 스냅샷 미빌드 시 None.

        Example::

            from dartlab.engines.insight import buildSnapshot
            buildSnapshot()

            c = Company("005930")
            c.rank                    # RankInfo(삼성전자, 매출 2/2192, 섹터 2/467, large)
            c.rank.revenueRank        # 2
            c.rank.revenueRankInSector # 2
            c.rank.sizeClass          # "large"
        """
        cacheKey = "_rank"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.rank.rank import getRank
        result = getRank(self.stockCode)
        self._cache[cacheKey] = result
        return result

    # ── 인사이트 분석 ──

    @property
    def insights(self):
        """종합 인사이트 분석 (7영역 등급 + 이상치 + 요약).

        Returns:
            AnalysisResult 또는 finance 데이터 없으면 None.

        Example::

            c = Company("005930")
            c.insights.grades()       # {'performance': 'A', ...}
            c.insights.summary        # "삼성전자는 실적, 재무건전성 등..."
            c.insights.anomalies      # [Anomaly(...), ...]
            c.insights.profile        # "premium"
        """
        if not self._hasFinance:
            return None
        cacheKey = "_insights"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.engines.insight import analyze
        result = analyze(self.stockCode, company=self)
        self._cache[cacheKey] = result
        return result

    # ── 전체 추출 ──

    def all(self) -> dict[str, Any]:
        """전체 데이터를 dict로 반환.

        Returns:
            {"BS": DataFrame, "IS": DataFrame, "dividend": DataFrame, ...}
            notes 항목은 "notes" 키 아래 dict로 포함.
            finance 항목은 "timeseries", "ratios" 키로 포함.
        """
        from dartlab import config
        from dartlab.engines.dart.docs.notes import _REGISTRY as notes_registry

        nNotes = len(notes_registry) if self._hasDocs else 0
        total = len(_ALL_PROPERTIES) + nNotes + 3
        result: dict[str, Any] = {}

        if config.verbose:
            from alive_progress import alive_bar
            with alive_bar(total, title=f"▶ {self.corpName}") as bar:
                _log = logging.getLogger("dartlab.company")
                for name, label in _ALL_PROPERTIES:
                    bar.text = label
                    try:
                        config.verbose = False
                        result[name] = getattr(self, name)
                        config.verbose = True
                    except (KeyError, ValueError, TypeError, FileNotFoundError, OSError) as e:
                        _log.debug("all(): %s failed — %s", name, e)
                        result[name] = None
                        config.verbose = True
                    bar()

                if self._hasDocs and self.notes is not None:
                    for noteName in notes_registry:
                        krName = notes_registry[noteName][1]
                        bar.text = krName
                        try:
                            config.verbose = False
                            result.setdefault("notes", {})[noteName] = self.notes._get(noteName)
                            config.verbose = True
                        except (KeyError, ValueError, TypeError, FileNotFoundError, OSError) as e:
                            _log.debug("all(): notes.%s failed — %s", noteName, e)
                            result.setdefault("notes", {})[noteName] = None
                            config.verbose = True
                        bar()

                bar.text = "시계열"
                result["timeseries"] = self.timeseries
                bar()
                bar.text = "연도별"
                result["annual"] = self.annual
                bar()
                bar.text = "재무비율"
                result["ratios"] = self.ratios
                bar()
        else:
            _log = logging.getLogger("dartlab.company")
            for name, label in _ALL_PROPERTIES:
                try:
                    result[name] = getattr(self, name)
                except (KeyError, ValueError, TypeError, FileNotFoundError, OSError) as e:
                    _log.debug("all(): %s failed — %s", name, e)
                    result[name] = None

            if self._hasDocs and self.notes is not None:
                notes_result = {}
                for noteName in notes_registry:
                    try:
                        notes_result[noteName] = self.notes._get(noteName)
                    except (KeyError, ValueError, TypeError, FileNotFoundError, OSError) as e:
                        _log.debug("all(): notes.%s failed — %s", noteName, e)
                        notes_result[noteName] = None
                result["notes"] = notes_result

            result["timeseries"] = self.timeseries
            result["annual"] = self.annual
            result["ratios"] = self.ratios

        return result

    # ── Excel 내보내기 ──

    def toExcel(
        self,
        outputPath: str | None = None,
        modules: list[str] | None = None,
    ) -> str:
        """Excel 파일로 내보내기.

        Args:
            outputPath: 저장 경로. None이면 '{종목코드}_{회사명}.xlsx'.
            modules: 포함할 시트. None이면 전체.
                가능한 값: "IS", "BS", "CF", "ratios", "dividend", "employee"

        Returns:
            저장된 파일 경로.

        Example::

            c = Company("005930")
            c.toExcel()                          # 005930_삼성전자.xlsx
            c.toExcel("output.xlsx")             # 지정 경로
            c.toExcel(modules=["IS", "BS"])      # 시트 선택
        """
        from dartlab.export.excel import exportToExcel
        return exportToExcel(self, outputPath=outputPath, modules=modules)

    # ── get() — 모듈 전체 결과 객체 접근 ──

    def get(self, name: str, **kwargs) -> Any:
        """모듈의 전체 결과 객체를 반환 (복수 DataFrame 접근용).

        Args:
            name: 모듈명 (dividend, audit, statements 등).

        Returns:
            해당 모듈의 Result 객체 전체.

        Example::

            r = c.get("audit")     # AuditResult
            r.opinionDf            # 감사의견
            r.feeDf                # 감사보수
        """
        if name == "holderOverview":
            return self.holderOverview
        return self._call_module(name, **kwargs)

    # ── LLM 분석 ──

    def ask(
        self,
        question: str,
        *,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        provider: str | None = None,
        model: str | None = None,
        stream: bool = False,
        **kwargs,
    ) -> str:
        """LLM에게 이 기업에 대해 질문.

        Args:
            question: 질문 텍스트 (한국어 또는 영어)
            include: 명시적으로 포함할 데이터 ["BS", "dividend", ...]
            exclude: 제외할 데이터
            provider: per-call provider override
            model: per-call model override
            stream: True면 터미널에 스트리밍 출력 후 전체 텍스트 반환
            **kwargs: LLMConfig override (temperature, max_tokens, ...)

        Returns:
            LLM 응답 텍스트

        Example::

            c = Company("005930")
            c.ask("재무 건전성을 분석해줘")
            c.ask("배당 추세", include=["dividend", "IS"])
            c.ask("부채 리스크", provider="ollama", model="llama3.1")
        """
        from dartlab.engines.ai import get_config
        from dartlab.engines.ai.context import (
            _get_sector,
            build_compact_context,
            build_context,
        )
        from dartlab.engines.ai.pipeline import run_pipeline
        from dartlab.engines.ai.prompts import _classify_question, build_system_prompt
        from dartlab.engines.ai.providers import create_provider

        config_ = get_config()
        overrides = {
            k: v
            for k, v in {"provider": provider, "model": model, **kwargs}.items()
            if v is not None
        }
        if overrides:
            config_ = config_.merge(overrides)

        use_compact = config_.provider in ("ollama", "codex", "claude-code")

        if use_compact:
            context_text, included_tables = build_compact_context(
                self, question, include=include, exclude=exclude,
            )
        else:
            context_text, included_tables = build_context(
                self, question, include=include, exclude=exclude,
            )

        if not use_compact:
            pipeline_result = run_pipeline(self, question, included_tables)
            if pipeline_result:
                context_text = context_text + pipeline_result

        sector = _get_sector(self)
        question_type = _classify_question(question)
        system = build_system_prompt(
            config_.system_prompt,
            included_modules=included_tables,
            sector=sector,
            question_type=question_type,
            compact=use_compact,
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"{context_text}\n\n---\n\n질문: {question}"},
        ]

        llm = create_provider(config_)

        if stream:
            chunks = []
            for chunk in llm.stream(messages):
                print(chunk, end="", flush=True)
                chunks.append(chunk)
            print()
            return "".join(chunks)

        response = llm.complete(messages)
        response.context_tables = included_tables

        from dartlab import config
        if config.verbose:
            print(f"  [LLM] {response.provider}/{response.model}")
            if response.usage:
                print(f"  [LLM] tokens: {response.usage.get('total_tokens', '?')}")

        return response.answer

    def chat(
        self,
        question: str,
        *,
        provider: str | None = None,
        model: str | None = None,
        max_turns: int = 5,
        on_tool_call=None,
        on_tool_result=None,
        **kwargs,
    ) -> str:
        """에이전트 모드: LLM이 필요한 도구를 직접 선택하여 분석.

        ask()와 달리 모든 데이터를 미리 로딩하지 않고,
        LLM이 tool calling으로 필요한 데이터를 요청한다.

        Args:
            question: 질문 텍스트
            provider: per-call provider override
            model: per-call model override
            max_turns: 최대 도구 호출 반복 횟수
            on_tool_call: 도구 호출 시 콜백 (UI용)
            on_tool_result: 도구 결과 시 콜백 (UI용)
            **kwargs: LLMConfig override

        Returns:
            LLM 최종 응답 텍스트

        Example::

            c = Company("005930")
            c.chat("재무 건전성을 분석하고 이상 징후를 찾아줘")
            c.chat("배당 추세", provider="ollama", model="llama3.1")
        """
        from dartlab.engines.ai import get_config
        from dartlab.engines.ai.agent import AGENT_SYSTEM_ADDITION, agent_loop
        from dartlab.engines.ai.prompts import build_system_prompt
        from dartlab.engines.ai.providers import create_provider

        config_ = get_config()
        overrides = {
            k: v
            for k, v in {"provider": provider, "model": model, **kwargs}.items()
            if v is not None
        }
        if overrides:
            config_ = config_.merge(overrides)

        system = build_system_prompt(config_.system_prompt) + AGENT_SYSTEM_ADDITION
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"기업: {self.corpName} ({self.stockCode})\n\n{question}"},
        ]

        llm = create_provider(config_)
        return agent_loop(
            llm, messages, self,
            max_turns=max_turns,
            on_tool_call=on_tool_call,
            on_tool_result=on_tool_result,
        )

    @property
    def market(self) -> str:
        """시장 코드."""
        return "KR"

    @property
    def currency(self) -> str:
        """통화 코드."""
        return "KRW"


def _isUSTicker(s: str) -> bool:
    """미국 ticker 형식 판별 (영문 대문자 1~5자리)."""
    return bool(re.match(r"^[A-Za-z]{1,5}$", s))


def Company(codeOrName: str) -> "KRCompany | USCompany":
    """종목코드/회사명/ticker → 적절한 Company 인스턴스 생성.

    판별 규칙:
    - 6자리 숫자 → KRCompany (DART 종목코드)
    - 한글 포함 → KRCompany (회사명 검색)
    - 영문 1~5자리 → USCompany (SEC ticker)

    Example::

        c = Company("005930")       # 삼성전자 (KR)
        c = Company("삼성전자")      # 삼성전자 (KR)
        c = Company("AAPL")         # Apple (US)
    """
    if re.match(r"^\d{6}$", codeOrName):
        return KRCompany(codeOrName)

    if any("\uac00" <= ch <= "\ud7a3" for ch in codeOrName):
        return KRCompany(codeOrName)

    if _isUSTicker(codeOrName):
        from dartlab.usCompany import USCompany
        return USCompany(codeOrName)

    return KRCompany(codeOrName)
