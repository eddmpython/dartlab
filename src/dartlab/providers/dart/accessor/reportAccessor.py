"""DART Company.report 네임스페이스 — 28개 apiType 체계 접근.

company.py에서 분리된 accessor 클래스.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.memory import BoundedCache
from dartlab.core.polarsUtil import isEmptyDf

if TYPE_CHECKING:
    from dartlab.providers.dart.company import Company

# OpenDART 개발가이드 공식 한글 컬럼 매핑 (https://opendart.fss.or.kr/guide/)
REPORT_COL_KR: dict[str, str] = {
    # 증자(감자) 현황 — apiId=2019004
    "isu_dcrs_de": "주식발행(감소)일자",
    "isu_dcrs_stle": "발행(감소)형태",
    "isu_dcrs_stock_knd": "발행(감소)주식종류",
    "isu_dcrs_qy": "발행(감소)수량",
    "isu_dcrs_mstvdv_fval_amount": "주당액면가액",
    "isu_dcrs_mstvdv_amount": "주당가액",
    # 자기주식 취득/처분 — apiId=2019006
    "stock_knd": "주식종류",
    "acqs_mth1": "취득방법(대)",
    "acqs_mth2": "취득방법(중)",
    "acqs_mth3": "취득방법(소)",
    "bsis_qy": "기초수량",
    "change_qy_acqs": "변동수량(취득)",
    "change_qy_dsps": "변동수량(처분)",
    "change_qy_incnr": "변동수량(소각)",
    "trmend_qy": "기말수량",
    # 주식총수 현황 — apiId=2020002
    "se": "구분",
    "isu_stock_totqy": "발행할주식총수",
    "now_to_isu_stock_totqy": "현재까지발행주식총수",
    "now_to_dcrs_stock_totqy": "현재까지감소주식총수",
    "redc": "감자",
    "profit_incnr": "이익소각",
    "rdmstk_repy": "상환주식상환",
    "etc": "기타",
    "istc_totqy": "발행주식총수",
    "tesstk_co": "자기주식수",
    "distb_stock_co": "유통주식수",
    # 타법인 출자 현황 — apiId=2019015
    "inv_prm": "법인명",
    "frst_acqs_de": "최초취득일자",
    "invstmnt_purps": "출자목적",
    "frst_acqs_amount": "최초취득금액",
    "bsis_blce_qy": "기초잔액(수량)",
    "bsis_blce_qota_rt": "기초잔액(지분율)",
    "bsis_blce_acntbk_amount": "기초잔액(장부가액)",
    "incrs_dcrs_acqs_dsps_qy": "증감(취득처분)(수량)",
    "incrs_dcrs_acqs_dsps_amount": "증감(취득처분)(금액)",
    "incrs_dcrs_evl_lstmn": "증감(평가손액)",
    "trmend_blce_qy": "기말잔액(수량)",
    "trmend_blce_qota_rt": "기말잔액(지분율)",
    "trmend_blce_acntbk_amount": "기말잔액(장부가액)",
    "recent_bsns_year_fnnr_sttus_tot_assets": "최근사업연도재무현황(총자산)",
    "recent_bsns_year_fnnr_sttus_thstrm_ntpf": "최근사업연도재무현황(당기순이익)",
    # 최대주주 변동현황 — apiId=2019008
    "change_on": "변동일",
    "mxmm_shrholdr_nm": "최대주주명",
    "posesn_stock_co": "소유주식수",
    "qota_rt": "지분율",
    "change_cause": "변동원인",
    # 소액주주 현황 — apiId=2019009
    "shrholdr_co": "주주수",
    "shrholdr_tot_co": "전체주주수",
    "shrholdr_rate": "주주비율",
    "hold_stock_co": "보유주식수",
    "stock_tot_co": "총발행주식수",
    "hold_stock_rate": "보유주식비율",
    # 사외이사 현황 — apiId=2020012
    "drctr_co": "이사의수",
    "otcmp_drctr_co": "사외이사수",
    "apnt": "사외이사변동(선임)",
    "rlsofc": "사외이사변동(해임)",
    "mdstrm_resig": "사외이사변동(중도퇴임)",
    # 공모자금 사용내역 — apiId=2020016
    "se_nm": "구분",
    "tm": "회차",
    "pay_de": "납입일",
    "pay_amount": "납입금액",
    "on_dclrt_cptal_use_plan": "신고서상자금사용계획",
    "real_cptal_use_sttus": "실제자금사용현황",
    "rs_cptal_use_plan_useprps": "증권신고서자금사용계획(용도)",
    "rs_cptal_use_plan_prcure_amount": "증권신고서자금사용계획(조달금액)",
    "real_cptal_use_dtls_cn": "실제자금사용내역(내용)",
    "real_cptal_use_dtls_amount": "실제자금사용내역(금액)",
    "dffrnc_occrrnc_resn": "차이발생사유",
    # 사모자금 사용내역 — apiId=2020017
    "cptal_use_plan": "자금사용계획",
    "mtrpt_cptal_use_plan_useprps": "주요사항보고서자금사용계획(용도)",
    "mtrpt_cptal_use_plan_prcure_amount": "주요사항보고서자금사용계획(조달금액)",
    # 회사채 미상환 잔액 — apiId=2020006
    "sm": "합계",
    "remndr_exprtn1": "잔여만기(대분류)",
    "remndr_exprtn2": "잔여만기(소분류)",
    "yy1_below": "1년이하",
    "yy1_excess_yy2_below": "1년초과2년이하",
    "yy2_excess_yy3_below": "2년초과3년이하",
    "yy3_excess_yy4_below": "3년초과4년이하",
    "yy4_excess_yy5_below": "4년초과5년이하",
    "yy5_excess_yy10_below": "5년초과10년이하",
    "yy10_excess": "10년초과",
    # 단기사채 미상환 잔액 — apiId=2020005
    "de10_below": "10일이하",
    "de10_excess_de30_below": "10일초과30일이하",
    "de30_excess_de90_below": "30일초과90일이하",
    "de90_excess_de180_below": "90일초과180일이하",
    "de180_excess_yy1_below": "180일초과1년이하",
    "isu_lmt": "발행한도",
    "remndr_lmt": "잔여한도",
    # 감사용역 체결현황 — apiId=2020010
    "bsns_year": "사업연도",
    "adtor": "감사인",
    "cn": "내용",
    "mendng": "보수",
    "tot_reqre_time": "총소요시간",
    "adt_cntrct_dtls_mendng": "감사계약내역(보수)",
    "adt_cntrct_dtls_time": "감사계약내역(시간)",
    "real_exc_dtls_mendng": "실제수행내역(보수)",
    "real_exc_dtls_time": "실제수행내역(시간)",
    # 비감사 용역 계약현황 — apiId=2020011
    "cntrct_cncls_de": "계약체결일",
    "servc_cn": "용역내용",
    "servc_exc_pd": "용역수행기간",
    "servc_mendng": "용역보수",
    # 이사·감사 보수현황 — apiId=2019013
    "nmpr": "인원수",
    "mendng_totamt": "보수총액",
    "jan_avrg_mendng_am": "1인평균보수액",
    # 개인별 보수현황 — apiId=2019012, 2019014
    "nm": "이름",
    "ofcps": "직위",
    "mendng_totamt_ct_incls_mendng": "보수총액비포함보수",
    # 미등기임원 보수현황 — apiId=2020013
    "fyer_salary_totamt": "연간급여총액",
    "jan_salary_am": "1인평균급여액",
    # 공통
    "rm": "비고",
}

# company.py 하위 호환 alias
_REPORT_COL_KR = REPORT_COL_KR


def _deprecationHint(name: str, alternative: str) -> str:
    """폐기 예정 접근자의 안내 문구. 실제로 도는 경로만 적는다.

    예전 문구는 `report.dividend → panel('dividend')` 처럼 영문 축을 권했는데, 그 축은
    존재하지 않아 `panel` 이 None 을 돌려준다. 실측으로 dividend·employee·majorHolder·
    executive 넷 다 옛 접근자는 실데이터(40·84·167·8 행)를 주고 권장 경로는 None 이었다.
    안내를 따르면 자료를 잃는다. panel 의 공시 본문과 이 API 표는 애초에 다른 것이라
    옮겨 갈 자리가 아니었다.
    """
    return f"report.{name} 은 공개 계약이 아니다. {alternative} 로 옮겨라."


def reportFrameInner(stockCode: str, apiType: str, topic: str, *, raw: bool = False) -> pl.DataFrame | None:
    """report apiType 의 정제된 DataFrame 반환 (메타 컬럼 제거, 한글 매핑).

    2015 년 데이터 제외 + 보통주 필터 + ``se`` 컬럼 있으면 ``se × period`` 수평화.
    ``raw=False`` 면 컬럼명을 ``REPORT_COL_KR`` 매핑으로 한글 변경.

    Args:
        stockCode: 종목코드.
        apiType: OpenDART apiType 키 (예: ``"dividend"``).
        topic: topic 이름 (현재 미사용 — 시그니처 호환).
        raw: True 면 원본 영문 컬럼, False 면 한글 매핑.

    Returns:
        정제 DataFrame 또는 None (데이터 부재).

    Raises:
        없음 (예외는 ``extractClean`` 내부에서 잡힘).

    Example:
        >>> reportFrameInner("005930", "stockTotal", "stockTotal")
          period 수평화 또는 행 기반 반환 (d) raw=False 시 한국어 컬럼 라벨화.
    """
    from dartlab.providers.dart.report.extract import extractClean

    df = extractClean(stockCode, apiType)
    if isEmptyDf(df):
        return None

    # 2015년 제외 (sections/finance와 통일)
    df = df.filter(pl.col("year") != 2015)
    if df.is_empty():
        return None

    # stock_knd 필터 (보통주 우선)
    if "stock_knd" in df.columns:
        common = df.filter(pl.col("stock_knd") == "보통주")
        if not common.is_empty():
            df = common

    # se(항목) 컬럼이 있으면 se × period 수평화
    if "se" in df.columns:
        return reportPivotBySe(df, raw=raw)

    # se 없는 apiType → 행 기반 반환
    _META_COLS = {"stlm_dt", "apiType", "stockCode", "year", "quarter", "quarterNum", "stock_knd"}
    dropCols = [c for c in df.columns if c in _META_COLS]
    if dropCols:
        df = df.drop(dropCols)
    if not raw:
        renameMap = {c: REPORT_COL_KR[c] for c in df.columns if c in REPORT_COL_KR}
        if renameMap:
            existing = set(df.columns)
            renameMap = {k: v for k, v in renameMap.items() if v not in existing or k == v}
            if renameMap:
                df = df.rename(renameMap)
    return df


def reportPivotBySe(df: pl.DataFrame, *, raw: bool = False) -> pl.DataFrame | None:
    """report ``se`` (항목) × period 수평화. 분기별 전체 데이터.

    Args:
        df: ``year/quarterNum/se/thstrm`` 컬럼 포함 DataFrame.
        raw: True 면 ``se`` 컬럼 유지, False 면 ``"항목"`` 으로 rename.

    Returns:
        ``se × period`` 수평화 DataFrame 또는 None (``thstrm`` 모두 null).

    Raises:
        없음.

    Example:
        >>> reportPivotBySe(extracted_df)
          period 수평화 또는 행 기반 반환 (d) raw=False 시 한국어 컬럼 라벨화.
    """
    df = df.with_columns((pl.col("year").cast(pl.Utf8) + "Q" + pl.col("quarterNum").cast(pl.Utf8)).alias("_period"))
    # null-only 행 제외
    if "thstrm" in df.columns:
        df = df.filter(pl.col("thstrm").is_not_null())
    if df.is_empty():
        return None

    pivoted = df.pivot(
        on="_period", index="se", values="thstrm", aggregate_function="first"
    )  # polars-streaming-unsupported: pivot

    # period 컬럼 역순 정렬
    periodCols = [c for c in pivoted.columns if c != "se"]
    periodCols.sort(key=lambda p: (int(p[:4]), int(p[-1])), reverse=True)
    result = pivoted.select(["se"] + periodCols)
    if not raw:
        result = result.rename({"se": "항목"})
    return result


class _ReportAccessor:
    """DART 정형공시 28 apiType 내부 accessor.

    Company 의 ``_report`` 속성으로 내부 보관 (private). 사용자는 ``c.panel("dividend")``
    · ``c.panel("treasuryStock")`` 등 공개 진입점을 사용한다 — ``c.report`` 직접 접근은
    Plan v10 에서 제거됐다.

    pivot 함수가 있는 5개(dividend, employee, majorHolder, executive, audit)는
    전용 Result 반환. 나머지는 extractAnnual 기준 DataFrame 반환.
    """

    _PIVOT_NAMES = frozenset({"dividend", "employee", "majorHolder", "executive", "audit"})

    def __init__(self, company: "Company"):
        self._company = company
        self._cache: BoundedCache = BoundedCache(maxEntries=50, pressureMb=1200.0)

    def _pivot(self, name: str) -> Any:
        if name in self._cache:
            return self._cache[name]
        from dartlab.providers.dart.report import (
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
        result = func(self._company.stockCode, baseDf=self._company.rawReport)
        self._cache[name] = result
        return result

    def extract(self, apiType: str) -> pl.DataFrame | None:
        """apiType 별 정제된 DataFrame 반환 (BoundedCache 활용).

        Args:
            apiType: OpenDART apiType 키 (예: ``"dividend"``).

        Returns:
            정제 DataFrame 또는 None.

        Raises:
            없음 (KeyError/ValueError/TypeError/FileNotFoundError 모두 None 반환).

        Example:
            >>> c._report.extract("dividend")
              내부 backing namespace.
        """
        cacheKey = f"_extract_{apiType}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.providers.dart.report import extractClean

        try:
            result = extractClean(self._company.stockCode, apiType, baseDf=self._company.rawReport)
        except (KeyError, ValueError, TypeError, FileNotFoundError):
            result = None
        self._cache[cacheKey] = result
        return result

    def extractAnnual(self, apiType: str, quarterNum: int | None = None) -> pl.DataFrame | None:
        """apiType 별 연간 DataFrame 반환.

        Args:
            apiType: OpenDART apiType 키.
            quarterNum: 특정 분기 (1~4). None 이면 preferred quarter 자동 선택.

        Returns:
            연간 DataFrame 또는 None.

        Raises:
            없음 (모든 예외 None 반환).

        Example:
            >>> c._report.extractAnnual("stockTotal")
              내부 backing namespace.
        """
        cacheKey = f"_annual_{apiType}_{quarterNum}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.providers.dart.report import extractAnnual as _extractAnnual

        try:
            result = _extractAnnual(self._company.stockCode, apiType, quarterNum, baseDf=self._company.rawReport)
        except (KeyError, ValueError, TypeError, FileNotFoundError):
            result = None
        self._cache[cacheKey] = result
        return result

    def result(self, apiType: str, quarterNum: int | None = None) -> Any | None:
        """apiType 별 통일된 Result 반환 — pivot 5 종은 dataclass, 나머지는 generic.

        Args:
            apiType: OpenDART apiType 키.
            quarterNum: 특정 분기.

        Returns:
            ``DividendResult/EmployeeResult/...`` 또는 generic Result 또는 None.

        Raises:
            없음.

        Example:
            >>> c._report.result("dividend")
              내부 backing namespace.
        """
        cacheKey = f"_result_{apiType}_{quarterNum}"
        if cacheKey in self._cache:
            return self._cache[cacheKey]

        if apiType in self._PIVOT_NAMES:
            result = getattr(self, apiType)
            self._cache[cacheKey] = result
            return result

        from dartlab.providers.dart.report import extractResult

        try:
            result = extractResult(self._company.stockCode, apiType, quarterNum, baseDf=self._company.rawReport)
        except (KeyError, ValueError, TypeError, FileNotFoundError):
            result = None
        self._cache[cacheKey] = result
        return result

    def status(self, apiType: str | None = None) -> pl.DataFrame | dict[str, bool]:
        """apiType availability 확인 — 전체 또는 특정.

        Args:
            apiType: 특정 apiType (None 이면 전체 28 종 상태).

        Returns:
            단일이면 ``{apiType: bool}`` dict, 전체면 ``apiType/label/preferredQuarter/...``
            컬럼 DataFrame.

        Raises:
            없음.

        Example:
            >>> c._report.status("dividend")
            >>> c._report.status()  # 전체 28 종
              내부 backing namespace.
        """
        from dartlab.providers.dart.report.types import API_TYPE_LABELS, API_TYPES, PREFERRED_QUARTER

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
        """배당 시계열 — deprecated alias (``c.panel("dividend")`` 권장).

        Returns:
            DividendResult 또는 None.

        Raises:
            DeprecationWarning: 호출 시 발생.

        Example:
            >>> c.panel("dividend")  # 권장
              내부 backing namespace.
        """
        import warnings

        warnings.warn(
            _deprecationHint("dividend", "c.capital() (DPS·배당수익률) 또는 dartlab.scan('dividendTrend')"),
            DeprecationWarning,
            stacklevel=2,
        )
        return self._pivot("dividend")

    @property
    def employee(self):
        """직원현황 시계열 — deprecated alias (``c.panel("employee")`` 권장).

        Returns:
            EmployeeResult 또는 None.

        Raises:
            DeprecationWarning: 호출 시 발생.

        Example:
            >>> c.panel("employee")
              내부 backing namespace.
        """
        import warnings

        warnings.warn(
            _deprecationHint("employee", "c.workforce() (직원수·평균급여·근속)"), DeprecationWarning, stacklevel=2
        )
        return self._pivot("employee")

    @property
    def majorHolder(self):
        """최대주주현황 시계열 — deprecated alias (``c.panel("majorHolder")`` 권장).

        Returns:
            MajorHolderResult 또는 None.

        Raises:
            DeprecationWarning: 호출 시 발생.

        Example:
            >>> c.panel("majorHolder")
              내부 backing namespace.
        """
        import warnings

        warnings.warn(
            _deprecationHint("majorHolder", "c.governance() (지분율) 또는 dartlab.scan('governance')"),
            DeprecationWarning,
            stacklevel=2,
        )
        return self._pivot("majorHolder")

    @property
    def executive(self):
        """임원현황 — deprecated alias (``c.panel("executive")`` 권장).

        Returns:
            ExecutiveResult 또는 None.

        Raises:
            DeprecationWarning: 호출 시 발생.

        Example:
            >>> c.panel("executive")
              내부 backing namespace.
        """
        import warnings

        warnings.warn(
            _deprecationHint("executive", "c.governance() (사외이사비율·겸직) 또는 c.panel('임원')"),
            DeprecationWarning,
            stacklevel=2,
        )
        return self._pivot("executive")

    @property
    def audit(self):
        """감사의견 시계열 — deprecated alias (``c.panel("audit")`` 권장).

        Returns:
            AuditResult 또는 None.

        Raises:
            DeprecationWarning: 호출 시 발생.

        Example:
            >>> c.panel("audit")
              내부 backing namespace.
        """
        import warnings

        warnings.warn(
            _deprecationHint("audit", "c.panel('감사') 또는 dartlab.scan('audit')"), DeprecationWarning, stacklevel=2
        )
        return self._pivot("audit")

    def __getattr__(self, name: str) -> Any:
        """미등록 apiType은 extractAnnual 자동 호출."""
        if name.startswith("_"):
            raise AttributeError(name)
        from dartlab.providers.dart.report.types import API_TYPES

        if name in API_TYPES and name not in self._PIVOT_NAMES:
            return self.extractAnnual(name)
        raise AttributeError(f"ReportAccessor에 '{name}' 항목이 없습니다. apiTypes: {API_TYPES}")

    @property
    def apiTypes(self) -> list[str]:
        """사용 가능한 apiType 전체 목록 (28 종).

        Returns:
            apiType 키 리스트.

        Raises:
            없음.

        Example:
            >>> c._report.apiTypes
              내부 backing namespace.
        """
        from dartlab.providers.dart.report.types import API_TYPES

        return list(API_TYPES)

    @property
    def labels(self) -> dict[str, str]:
        """apiType → 한글명 매핑.

        Returns:
            ``{apiType: 한글 라벨}`` dict.

        Raises:
            없음.

        Example:
            >>> c._report.labels["dividend"]
            '배당'
              내부 backing namespace.
        """
        from dartlab.providers.dart.report.types import API_TYPE_LABELS

        return dict(API_TYPE_LABELS)

    @property
    def availableApiTypes(self) -> list[str]:
        """현재 parquet 에 실제 존재하는 apiType 목록 (BoundedCache).

        Returns:
            존재하는 apiType 키 리스트 (API_TYPES 순서 보존).

        Raises:
            없음 (parquet 부재 시 빈 리스트).

        Example:
            >>> c._report.availableApiTypes
              내부 backing namespace.
        """
        cacheKey = "_availableApiTypes"
        if cacheKey in self._cache:
            return self._cache[cacheKey]
        from dartlab.providers.dart.report.types import API_TYPES

        try:
            raw = loadData(self._company.stockCode, category="report", columns=["apiType"])
        except (FileNotFoundError, RuntimeError, ValueError, TypeError):
            raw = None

        if isEmptyDf(raw) or "apiType" not in raw.columns:
            result: list[str] = []
        else:
            available = set(raw["apiType"].drop_nulls().cast(pl.Utf8).unique().to_list())
            result = [name for name in API_TYPES if name in available]
        self._cache[cacheKey] = result
        return result

    def __repr__(self):
        from dartlab.providers.dart.report.types import API_TYPES

        return f"ReportAccessor({len(API_TYPES)} apiTypes, {len(self._PIVOT_NAMES)} pivots)"
