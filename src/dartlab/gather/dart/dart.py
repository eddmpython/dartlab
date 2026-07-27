"""Dart — OpenDART API 클라이언트.

사용법 1 — 회사 객체 (추천):
    from dartlab import Dart

    d = Dart()
    s = d("삼성전자")

    s.finance(2020)                      # 2020~현재 Q1~Q4 전부
    s.report("배당", 2020)               # 배당 2020~현재
    s.filings("2024")                    # 공시 목록
    s.info()                             # 기업 개황
    s.shares()                           # 지분공시
    s.saveFinance("삼성전자.parquet", 2020)  # 저장 (eddmpython 호환)

사용법 2 — 직접 호출:
    d.finstate("삼성전자", 2020, end=2024, q=0)
    d.report("삼성전자", "배당", 2020, end=2024)
    d.finstateMulti(["삼성전자", "SK하이닉스"], 2023)
"""

from __future__ import annotations

import io
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Literal

import polars as pl

import dartlab.config as _dartlabConfig
from dartlab.core.dartBuild import (
    enrichFinance,
    enrichReport,
)
from dartlab.core.dartBuild import (
    save as _saveFile,
)
from dartlab.core.dartClient import DartClient

# ── 내부 상수 ──────────────────────────────────────────────
from dartlab.core.dartConstants import (
    CODE_TO_LABEL as _CODE_TO_LABEL,
)
from dartlab.core.dartConstants import (
    QUARTER_TO_CODE as _QUARTER_TO_CODE,
)
from dartlab.core.dartDateUtil import defaultEnd, defaultStart, parseDate
from dartlab.core.dataConfig import DATA_RELEASES
from dartlab.core.market import isKrStockCode, normalizeKrCode
from dartlab.gather.dart.corpCode import (
    findCorpCode,
    loadCorpCodes,
    searchCompanies,
)
from dartlab.gather.dart.disclosure import (
    CORP_CLASS,
    FILING_TYPES,
    _resolveCorpCode,
    companyInfo,
    listFilings,
)

# 사업보고서 주요정보 29개 + 주요사항보고 27개 = 56개 카테고리
_REPORT_ENDPOINTS: dict[str, str] = {
    # ── 사업보고서 주요정보 (정기보고서) ──
    "증자감자": "irdsSttus",
    "배당": "alotMatter",
    "자기주식": "tesstkAcqsDspsSttus",
    "최대주주": "hyslrSttus",
    "최대주주변동": "hyslrChgSttus",
    "소액주주": "mrhlSttus",
    "임원": "exctvSttus",
    "직원": "empSttus",
    "이사회임원개인보수": "hmvAuditIndvdlBySttus",
    "이사회임원전체보수": "hmvAuditAllSttus",
    "개인별보수": "indvdlByPay",
    "타법인출자": "otrCprInvstmntSttus",
    "대주주지분변동": "eleStockIstySttus",
    # 추가 보고서 (미등기임원, 채무증권, 감사, 주식총수 등)
    "미등기임원보수": "unrstExctvMendngSttus",
    "주식총수": "stockTotqySttus",
    "회계감사인": "accnutAdtorNmNdAdtOpinion",
    "감사용역체결": "adtServcCnclsSttus",
    "감사비감사계약": "accnutAdtorNonAdtServcCnclsSttus",
    "사외이사변동": "outcmpnyDrctrNdChangeSttus",
    "회사채미상환": "cprndNrdmpBlce",
    "단기사채미상환": "srtpdPsndbtNrdmpBlce",
    "기업어음미상환": "entrprsBilScritsNrdmpBlce",
    "채무증권발행실적": "detScritsIsuAcmslt",
    "조건부자본증권미상환": "cndlCaplScritsNrdmpBlce",
    "신종자본증권미상환": "newCaplScritsNrdmpBlce",
    "공모자금용도": "prvsrpCptalUseDtls",
    "공모자금사용": "pssrpCptalUseDtls",
    "이사감사보수총회인정": "drctrAdtAllMendngSttusGmtsckConfmAmount",
    "이사감사보수지급형태": "drctrAdtAllMendngSttusMendngPymntamtTyCl",
    # ── 주요사항보고 ──
    "부도": "dfOcr",
    "영업정지": "bsnsSspd",
    "회생절차개시": "crtRcvBg",
    "해산사유": "dsRsn",
    "유상증자결정": "piicDecsn",
    "무상증자결정": "fricDecsn",
    "유무상증자결정": "crtskcrtDecsn",
    "감자결정": "crcaDecsn",
    "자기주식취득결정": "tesstkAcqsDecsn",
    "자기주식처분결정": "tesstkDspsDecsn",
    "합병결정": "mrgDecsn",
    "분할결정": "divDecsn",
    "주식교환이전결정": "stkExtrDecsn",
    "사업양도결정": "bsnTrfDecsn",
    "사업양수결정": "bsnInhDecsn",
    "타법인주식양도결정": "otcprStkInvscDecsn",
    "타법인주식양수결정": "otcprStkInvscrInhDecsn",
    "전환사채발행결정": "cvbdIsDecsn",
    "신주인수권부사채발행결정": "bdwtIsDecsn",
    "교환사채발행결정": "exbdIsDecsn",
    "채권관리절차개시": "bnkMngtPcbg",
    "채권관리절차중단": "bnkMngtPcsp",
    "조건부자본증권발행결정": "wdCocobdIsDecsn",
    "해외상장결정": "ovLstDecsn",
    "해외상장폐지결정": "ovDlstDecsn",
    "해외상장": "ovLst",
    "해외상장폐지": "ovDlst",
}

# 정기보고서 전체 28개 카테고리 (saveReport 기본값)
_PERIODIC_REPORT_CATEGORIES: list[str] = [
    # eddmpython 기본 22개
    "배당",
    "직원",
    "임원",
    "최대주주",
    "최대주주변동",
    "소액주주",
    "자기주식",
    "증자감자",
    "이사회임원전체보수",
    "이사회임원개인보수",
    "개인별보수",
    "타법인출자",
    "주식총수",
    "회계감사인",
    "감사용역체결",
    "감사비감사계약",
    "사외이사변동",
    "미등기임원보수",
    "회사채미상환",
    "단기사채미상환",
    "공모자금용도",
    "공모자금사용",
    # 추가 정기보고서 6개
    "대주주지분변동",
    "기업어음미상환",
    "신종자본증권미상환",
    "채무증권발행실적",
    "이사감사보수총회인정",
    "이사감사보수지급형태",
]


class Dart:
    """OpenDART API 통합 클라이언트.

    Parameters
    ----------
    keys : str | list[str] | None
        API 키. 문자열 1개 또는 리스트(로테이션).
        None이면 환경변수 자동 탐색.

    Examples
    --------
    >>> d = Dart()
    >>> d = Dart("your_api_key")
    >>> d = Dart(["key1", "key2", "key3"])
    """

    def __init__(self, keys: str | list[str] | None = None):
        try:
            if isinstance(keys, list):
                self._client = DartClient(apiKeys=keys)
            elif isinstance(keys, str):
                self._client = DartClient(apiKey=keys)
            else:
                self._client = DartClient()
        except ValueError:
            # DART 키 없음 → 원격 서버 프록시 fallback
            from dartlab.gather.dart.remote import RemoteDartClient

            self._client = RemoteDartClient()

    # ── 공시 검색 ──────────────────────────────────────────

    def filings(
        self,
        corp: str | None = None,
        start: str | datetime | date | None = None,
        end: str | datetime | date | None = None,
        *,
        type: str | None = None,
        final: bool = False,
        market: Literal["Y", "K", "N", "E"] | None = None,
    ) -> pl.DataFrame:
        """OpenDART 공시 목록 조회 — corp/start/end/type/final/market 다축 필터.

        Args:
            corp: 기업 식별자 또는 None (전체 시장).
            start: 시작일 (str/datetime/date) 또는 None.
            end: 종료일 또는 None.
            type: 공시 유형 코드 또는 None.
            final: 최종본만. 기본 False.
            market: 법인구분 또는 None.

        Returns:
            pl.DataFrame — OpenDART list endpoint 원본 컬럼.

        Example:
            >>> # d.filings("삼성전자", "2024-01", "2024-06")

        Raises:
            없음.
        """
        startDate = parseDate(start, asEnd=False) or defaultStart()
        endDate = parseDate(end, asEnd=True) or defaultEnd()

        return listFilings(
            self._client,
            corp=corp,
            start=startDate,
            end=endDate,
            filingType=type,
            finalOnly=final,
            corpClass=market,
        )

    # ── 기업 정보 ──────────────────────────────────────────

    def company(self, corp: str) -> dict[str, str]:
        """기업 개황 조회.

        Examples
        --------
        >>> d.company("삼성전자")
        >>> d.company("005930")

        Args:
            corp: 인자.

        Raises:
            없음.

        Returns:
            dict — 기업 개황 정보 (corpCode/corpName/stockName/stockCode 등).
        """
        return companyInfo(self._client, corp)

    # ── 회사 검색 ──────────────────────────────────────────

    def search(
        self,
        query: str,
        listed: bool = False,
        *,
        limit: int | None = None,
    ) -> pl.DataFrame:
        """OpenDART 회사명 검색 — substring 매칭 (corpCode + name + ticker).

        Args:
            query: 검색어 (한국어/영문/숫자).
            listed: 상장사만 필터. 기본 False.
            limit: 최대 row 수. None → 무제한.

        Returns:
            pl.DataFrame — 매칭된 회사 메타 (corp_code/corp_name/stock_code/modify_date).

        Example:
            >>> # d.search("삼성", limit=10)
            >>> # d.search("LG", listed=True)

        Raises:
            없음.
        """
        return searchCompanies(self._client, query, listedOnly=listed, limit=limit)

    # ── corp_code ──────────────────────────────────────────

    def corpCode(self, query: str) -> str | None:
        """종목코드 / 회사명 → 8 자리 corp_code 1 매칭 변환.

        Args:
            query: 종목코드 6 / 회사명 (한국어/영문).

        Returns:
            str | None — 8 자리 corp_code 또는 매칭 없음 시 None.

        Example:
            >>> # d.corpCode("005930")  # "00126380"
            >>> # d.corpCode("삼성전자")  # "00126380"

        Raises:
            없음.
        """
        return findCorpCode(self._client, query)

    def corpCodes(self, refresh: bool = False) -> pl.DataFrame:
        """corp_code 전체 목록 (11만+건, 24시간 캐시).

        Args:
            refresh: 인자.

        Raises:
            없음.

        Example:
            >>> corpCodes(...)

        Returns:
            pl.DataFrame — DART OpenAPI 응답 정규화 결과.
        """
        return loadCorpCodes(self._client, refresh=refresh)

    # ── 재무제표 ───────────────────────────────────────────

    def finstate(
        self,
        corp: str,
        start: str | int | None = None,
        *,
        end: int | None = None,
        q: int | None = None,
        consolidated: bool = True,
        full: bool = False,
    ) -> pl.DataFrame:
        """OpenDART 재무제표 조회 — 단건 또는 연속 기간 (연간/분기 자동).

        Args:
            corp: 종목코드 6 / 회사명 / corp_code 8.
            start: 사업연도 (int 또는 str). None → 최근 연도.
            end: 종료 연도 (int). None → start 만.
            q: 분기 선택. None=연간, 0~4.
            consolidated: True=CFS, False=OFS. full=True 시만 의미.
            full: True → 전체 계정. False → 주요 계정만.

        Returns:
            pl.DataFrame — OpenDART finstate 원본 컬럼 (account_id, account_nm, thstrm_amount 등).

        Example:
            >>> # d.finstate("삼성전자")  # 최근 연간
            >>> # d.finstate("삼성전자", 2020, end=2024, q=0)  # 분기별 20건

        Raises:
            없음.
        """
        corpCodeStr = _resolveCorpCode(self._client, corp)
        startYear = int(start) if start else datetime.now().year - 1
        endpoint = "fnlttSinglAcntAll" if full else "fnlttSinglAcnt"

        extraParams: dict[str, str] = {}
        if full:
            extraParams["fs_div"] = "CFS" if consolidated else "OFS"

        quarterly, quarter = _resolveQ(q, hasRange=end is not None)
        periods = _buildPeriods(startYear, end, quarterly, quarter)

        if len(periods) == 1:
            bsnsYear, reprtCode = periods[0]
            params: dict[str, str] = {
                "corp_code": corpCodeStr,
                "bsns_year": bsnsYear,
                "reprt_code": reprtCode,
                **extraParams,
            }
            df = self._client.getDf(f"{endpoint}.json", params)
            _maybeValidateFinance(df)
            return df

        corpName = self._resolveCorpName(corp)
        df = _fetchSeries(
            self._client,
            endpoint,
            corpCodeStr,
            corpName,
            periods,
            "재무제표",
            extraParams,
        )
        _maybeValidateFinance(df)
        return df

    def finstateMulti(
        self,
        corps: list[str],
        year: str | int | None = None,
        *,
        q: int | None = None,
    ) -> pl.DataFrame:
        """다중기업 재무제표 비교 (한 번의 API 호출).

        Parameters
        ----------
        corps : list[str]
            기업 리스트 (종목코드/회사명/corp_code 혼용 가능).
        year : str | int | None
            사업연도. None이면 최근 연도.
        q : int | None
            분기 선택. None=연간, 1=Q1, 2=Q2, 3=Q3, 4=사업보고서.

        Examples
        --------
        >>> d.finstateMulti(["삼성전자", "SK하이닉스"], 2023)
        >>> d.finstateMulti(["삼성전자", "SK하이닉스"], 2023, q=2)

        Raises:
            없음.

        Args:
            corps: 회사명 또는 stockCode 리스트.
            year: 사업연도 (예 2024). None 이면 직전 연도.
            q: 분기 (1~4). None 이면 4분기 (사업보고서).

        Returns:
            pl.DataFrame — DART OpenAPI 응답 정규화 결과.
              일 호출 한도 (개인 1만/일) 내 호출.
        """
        corpCodes = [_resolveCorpCode(self._client, c) for c in corps]
        bsnsYear = str(year) if year else str(datetime.now().year - 1)
        _, quarter = _resolveQ(q, hasRange=False)
        reprtCode = _QUARTER_TO_CODE.get(quarter, "11011")

        return self._client.getDf(
            "fnlttMultiAcnt.json",
            {
                "corp_code": ",".join(corpCodes),
                "bsns_year": bsnsYear,
                "reprt_code": reprtCode,
            },
        )

    def xbrlTaxonomy(
        self,
        category: str = "BS1",
    ) -> pl.DataFrame:
        """XBRL 택사노미 (표준 계정 체계).

        Parameters
        ----------
        category : str
            sj_div 코드. 사용 가능:
            BS1/BS2/BS3 (재무상태표), IS1/IS2/IS3 (손익계산서),
            CIS1/CIS2 (포괄손익), CF1/CF2/CF3 (현금흐름).

        Examples
        --------
        >>> d.xbrlTaxonomy("BS1")   # 재무상태표
        >>> d.xbrlTaxonomy("IS1")   # 손익계산서
        >>> d.xbrlTaxonomy("CF1")   # 현금흐름표

        Raises:
            없음.

        Args:
            category: report 카테고리 (배당/주식총수/자기주식 등).

        Returns:
            pl.DataFrame — DART OpenAPI 응답 정규화 결과.
        """
        return self._client.getDf(
            "xbrlTaxonomy.json",
            {"sj_div": category},
        )

    # ── 보고서 API (44개 + 주요사항 28개) ──────────────────

    def report(
        self,
        corp: str,
        reportType: str,
        start: str | int | None = None,
        *,
        end: int | None = None,
        q: int | None = None,
    ) -> pl.DataFrame:
        """사업보고서 주요정보 API — 28 reportType × 단건/연속 기간 자동.

        Args:
            corp: 종목코드 / 회사명 / corp_code.
            reportType: 28 종 중 1 (배당/직원/임원/...). ``Dart.reportTypes()`` 로 확인.
            start: 사업연도. None → 최근 연도.
            end: 종료 연도. None → start 만.
            q: 분기 선택. None=연간, 0~4.

        Raises:
            ValueError: reportType 이 28 종 외.

        Returns:
            pl.DataFrame — reportType 별 컬럼 가변 (DART API 원본).

        Example:
            >>> # d.report("삼성전자", "배당", 2020, end=2024, q=2)  # 5 년 Q2
        """
        corpCodeStr = _resolveCorpCode(self._client, corp)
        startYear = int(start) if start else datetime.now().year - 1

        endpoint = _REPORT_ENDPOINTS.get(reportType)
        if endpoint is None:
            available = ", ".join(sorted(_REPORT_ENDPOINTS.keys()))
            raise ValueError(f"'{reportType}'은 알 수 없는 보고서 유형입니다.\n사용 가능: {available}")

        quarterly, quarter = _resolveQ(q, hasRange=end is not None)
        periods = _buildPeriods(startYear, end, quarterly, quarter)

        if len(periods) == 1:
            bsnsYear, reprtCode = periods[0]
            return self._client.getDf(
                f"{endpoint}.json",
                {
                    "corp_code": corpCodeStr,
                    "bsns_year": bsnsYear,
                    "reprt_code": reprtCode,
                },
            )

        corpName = self._resolveCorpName(corp)
        return _fetchSeries(
            self._client,
            endpoint,
            corpCodeStr,
            corpName,
            periods,
            reportType,
        )

    # ── 지분공시 ───────────────────────────────────────────

    def majorShareholders(self, corp: str) -> pl.DataFrame:
        """대량보유 상황보고 (5% 이상).

        Examples
        --------
        >>> d.majorShareholders("삼성전자")

        Args:
            corp: 인자.

        Raises:
            없음.

        Returns:
            pl.DataFrame — DART OpenAPI 응답 정규화 결과.
              일 호출 한도 (개인 1만/일) 내 호출.
        """
        corpCodeStr = _resolveCorpCode(self._client, corp)
        return self._client.getDf("majorstock.json", {"corp_code": corpCodeStr})

    def executiveShares(self, corp: str) -> pl.DataFrame:
        """임원·주요주주 소유보고.

        Examples
        --------
        >>> d.executiveShares("삼성전자")

        Args:
            corp: 인자.

        Raises:
            없음.

        Returns:
            pl.DataFrame — DART OpenAPI 응답 정규화 결과.
              일 호출 한도 (개인 1만/일) 내 호출.
        """
        corpCodeStr = _resolveCorpCode(self._client, corp)
        return self._client.getDf("elestock.json", {"corp_code": corpCodeStr})

    # ── 공시 서류 ──────────────────────────────────────────

    def document(
        self,
        rceptNo: str,
        savePath: str | Path | None = None,
    ) -> Path:
        """공시서류 원본 다운로드 (ZIP).

        Parameters
        ----------
        rceptNo : str
            접수번호 (filings()의 rcept_no 컬럼).
        savePath : str | Path | None
            저장 경로. None이면 현재 디렉토리에 {rceptNo}.zip.

        Returns
        -------
        Path
            저장된 파일 경로.

        Examples
        --------
        >>> path = d.document("20240312000736")
        >>> path = d.document("20240312000736", "~/downloads/samsung.zip")

        Raises:
            없음.

        Args:
            rceptNo: DART 접수번호 (14 자리 또는 그 형식).
            savePath: 저장 경로. None 이면 메모리만.

        Returns:
            Path — 저장된 파일 경로.
              일 호출 한도 (개인 1만/일) 내 호출.
        """
        raw = self._client.getBytes("document.xml", {"rcept_no": rceptNo})
        dest = Path(savePath) if savePath else Path(f"{rceptNo}.zip")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        return dest

    def documentText(self, rceptNo: str) -> str:
        """공시서류 원본 텍스트 추출 (ZIP 내 XML/HTML).

        Parameters
        ----------
        rceptNo : str
            접수번호.

        Returns
        -------
        str
            공시서류 본문 (HTML/XML). 가장 큰 파일 선택.

        Examples
        --------
        >>> html = d.documentText("20240312000736")

        Raises:
            없음.

        Args:
            rceptNo: DART 접수번호 (14 자리 또는 그 형식).

        Returns:
            str — DART OpenAPI 응답 텍스트.
              일 호출 한도 (개인 1만/일) 내 호출.
        """
        raw = self._client.getBytes("document.xml", {"rcept_no": rceptNo})
        zf = zipfile.ZipFile(io.BytesIO(raw))

        names = zf.namelist()
        if not names:
            raise ValueError(f"공시서류 ZIP이 비어있습니다: {rceptNo}")
        largest = max(names, key=lambda n: zf.getinfo(n).file_size)
        content = zf.read(largest)

        # 인코딩 시도: euc-kr → utf-8
        for encoding in ("euc-kr", "utf-8", "cp949"):
            try:
                return content.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        return content.decode("utf-8", errors="replace")

    # ── 유틸 ───────────────────────────────────────────────

    def _resolveCorpName(self, corp: str) -> str:
        """progress bar 표시용 회사명 해석."""
        df = loadCorpCodes(self._client)
        if isKrStockCode(corp):
            match = df.filter(pl.col("stock_code") == normalizeKrCode(corp))
            if match.height > 0:
                return match["corp_name"][0]
        elif corp.isdigit() and len(corp) == 8:
            match = df.filter(pl.col("corp_code") == corp)
            if match.height > 0:
                return match["corp_name"][0]
        return corp

    @staticmethod
    def filingTypes() -> dict[str, str]:
        """공시유형 코드표.

        Args:
            (인자 자동 생성).

        Raises:
            없음.

        Example:
            >>> filingTypes(...)

        Returns:
            dict — 기업 개황 정보 (corpCode/corpName/stockName/stockCode 등).
        """
        return dict(FILING_TYPES)

    @staticmethod
    def markets() -> dict[str, str]:
        """법인구분 코드표.

        Args:
            (인자 자동 생성).

        Raises:
            없음.

        Example:
            >>> markets(...)

        Returns:
            dict — 기업 개황 정보 (corpCode/corpName/stockName/stockCode 등).
        """
        return dict(CORP_CLASS)

    @staticmethod
    def reportTypes() -> list[str]:
        """사업보고서 API 지원 카테고리.

        Args:
            (인자 자동 생성).

        Raises:
            없음.

        Example:
            >>> reportTypes(...)

        Returns:
            list[str] — 결과 목록.
        """
        return sorted(_REPORT_ENDPOINTS.keys())

    def __call__(self, corp: str) -> DartCompany:
        """회사 객체 생성 — 한글 메서드로 모든 API 접근.

        Examples
        --------
        >>> s = d("삼성전자")
        >>> s.재무(2020, end=2024)
        >>> s.배당(2023)
        >>> s.공시("2024")
        """
        return DartCompany(self, corp)

    def __repr__(self) -> str:
        n = len(self._client._keys)
        return f"Dart(keys={n})"


OpenDart = Dart

# ── 재내보내기 (분리: dartHelpers.py · dartCompany.py) ────────
# dart.py 의 메서드가 _resolveQ/_buildPeriods 등을 사용하므로 module-level import.
# 순환(dartCompany↔dart)은 dartCompany 측에서 끊는다 — dartCompany 는 Dart 를
# TYPE_CHECKING 으로, 본 모듈 상수(_REPORT_ENDPOINTS 등)를 메서드 내부 lazy import.
from dartlab.gather.dart.dartCompany import (  # noqa: E402  re-export
    DartCompany,
    OpenDartCompany,
    _autoEnd,
    _resolveQ,
)
from dartlab.gather.dart.dartHelpers import (  # noqa: E402  re-export
    _buildPeriods,
    _dataPath,
    _fetchSeries,
    _maybeValidateFinance,
    _periodLabel,
)
