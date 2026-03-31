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

from dartlab import config as _dartlabConfig
from dartlab.core.dataConfig import DATA_RELEASES
from dartlab.providers.dart.openapi.client import DartClient

# ── 내부 상수 ──────────────────────────────────────────────
from dartlab.providers.dart.openapi.constants import (
    CODE_TO_LABEL as _CODE_TO_LABEL,
)
from dartlab.providers.dart.openapi.constants import (
    QUARTER_TO_CODE as _QUARTER_TO_CODE,
)
from dartlab.providers.dart.openapi.corpCode import (
    findCorpCode,
    loadCorpCodes,
    searchCompanies,
)
from dartlab.providers.dart.openapi.dateUtil import defaultEnd, defaultStart, parseDate
from dartlab.providers.dart.openapi.disclosure import (
    CORP_CLASS,
    FILING_TYPES,
    _resolveCorpCode,
    companyInfo,
    listFilings,
)
from dartlab.providers.dart.openapi.saver import (
    enrichFinance,
    enrichReport,
)
from dartlab.providers.dart.openapi.saver import (
    save as _saveFile,
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


def _dataPath(category: str, stockCode: str) -> Path:
    """dartlab 데이터 디렉토리 내 저장 경로.

    {dataDir}/dart/{category}/{stockCode}.parquet
    """
    subDir = DATA_RELEASES.get(category, {}).get("dir", f"dart/{category}")
    dest = Path(_dartlabConfig.dataDir) / subDir / f"{stockCode}.parquet"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


# ── 내부 유틸 ──────────────────────────────────────────────


def _buildPeriods(
    start: int,
    end: int | None,
    quarterly: bool,
    quarter: str,
) -> list[tuple[str, str]]:
    """(bsnsYear, reprtCode) 리스트 생성."""
    endYear = end if end is not None else start
    if endYear < start:
        raise ValueError(f"start({start}) > end({endYear}): 시작 연도가 종료 연도보다 큽니다")
    if start < 2015:
        raise ValueError(f"start={start}: OpenDART는 2015년 이후 데이터만 제공합니다")

    years = range(start, endYear + 1)
    quarters = ["Q1", "Q2", "Q3", "Q4"] if quarterly else [quarter]

    periods = []
    for y in years:
        for q in quarters:
            code = _QUARTER_TO_CODE.get(q, "11011")
            periods.append((str(y), code))
    return periods


def _periodLabel(bsnsYear: str, reprtCode: str) -> str:
    label = _CODE_TO_LABEL.get(reprtCode, reprtCode)
    return f"{bsnsYear} {label}"


def _fetchSeries(
    client: DartClient,
    endpoint: str,
    corpCode: str,
    corpName: str,
    periods: list[tuple[str, str]],
    title: str,
    extraParams: dict | None = None,
) -> pl.DataFrame:
    """여러 기간 연속 조회 → concat + rich.progress."""
    from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn

    frames: list[pl.DataFrame] = []

    progress = Progress(SpinnerColumn(), TextColumn("[bold blue]{task.description}"), BarColumn(), MofNCompleteColumn())
    _task = progress.add_task(f"{title} | {corpName}", total=len(periods))
    with progress:
        for bsnsYear, reprtCode in periods:
            progress.update(_task, description=f"{title} | {corpName} | {_periodLabel(bsnsYear, reprtCode)}")

            params: dict[str, str] = {
                "corp_code": corpCode,
                "bsns_year": bsnsYear,
                "reprt_code": reprtCode,
            }
            if extraParams:
                params.update(extraParams)

            df = client.getDf(f"{endpoint}.json", params)
            if df.height > 0:
                frames.append(df)
            progress.advance(_task)

    if not frames:
        return pl.DataFrame()
    return pl.concat(frames, how="diagonal_relaxed")


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
        if isinstance(keys, list):
            self._client = DartClient(apiKeys=keys)
        elif isinstance(keys, str):
            self._client = DartClient(apiKey=keys)
        else:
            self._client = DartClient()

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
        """공시 목록 조회.

        Parameters
        ----------
        corp : str | None
            기업 (종목코드 / 회사명 / corp_code). None이면 전체 시장.
        start : 유연한 날짜 | None
            시작일. None이면 1년 전.
        end : 유연한 날짜 | None
            종료일. None이면 오늘.
        type : str | None
            공시유형 (A=정기, B=주요사항, C=발행, D=지분, E=기타 등).
        final : bool
            최종보고서만.
        market : str | None
            법인구분 (Y=유가증권, K=코스닥, N=코넥스, E=기타).

        Examples
        --------
        >>> d.filings("삼성전자")
        >>> d.filings("005930", "2024")
        >>> d.filings("삼성전자", "2024-01", "2024-06")
        >>> d.filings(start="2024-03-14")
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
        """
        return companyInfo(self._client, corp)

    # ── 회사 검색 ──────────────────────────────────────────

    def search(
        self,
        query: str,
        listed: bool = False,
    ) -> pl.DataFrame:
        """회사명 검색.

        Examples
        --------
        >>> d.search("삼성")
        >>> d.search("카카오", listed=True)
        """
        return searchCompanies(self._client, query, listedOnly=listed)

    # ── corp_code ──────────────────────────────────────────

    def corpCode(self, query: str) -> str | None:
        """종목코드 / 회사명 → 8자리 corp_code.

        Examples
        --------
        >>> d.corpCode("005930")    # "00126380"
        >>> d.corpCode("삼성전자")  # "00126380"
        """
        return findCorpCode(self._client, query)

    def corpCodes(self, refresh: bool = False) -> pl.DataFrame:
        """corp_code 전체 목록 (11만+건, 24시간 캐시)."""
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
        """재무제표 조회 — 단건 또는 연속.

        Parameters
        ----------
        corp : str
            종목코드 / 회사명 / corp_code.
        start : str | int | None
            사업연도. None이면 최근 연도.
        end : int | None
            종료 연도. start~end 연속 조회.
        q : int | None
            분기 선택. None=연간, 0=Q1~Q4 전부, 1=Q1, 2=Q2, 3=Q3, 4=사업보고서.
        consolidated : bool
            True=연결, False=별도.
        full : bool
            True면 전체 계정.

        Examples
        --------
        >>> d.finstate("삼성전자")                        # 최근 연간
        >>> d.finstate("삼성전자", 2023, q=2)             # 2023 Q2
        >>> d.finstate("삼성전자", 2020, end=2024)        # 연간 5년
        >>> d.finstate("삼성전자", 2020, end=2024, q=0)   # 분기별 20건
        >>> d.finstate("삼성전자", 2020, end=2024, q=2)   # Q2만 5건
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
            return self._client.getDf(f"{endpoint}.json", params)

        corpName = self._resolveCorpName(corp)
        return _fetchSeries(
            self._client,
            endpoint,
            corpCodeStr,
            corpName,
            periods,
            "재무제표",
            extraParams,
        )

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
        """사업보고서 주요정보 API — 단건 또는 연속.

        Parameters
        ----------
        corp : str
            종목코드 / 회사명 / corp_code.
        reportType : str
            카테고리명. ``Dart.reportTypes()``로 목록 확인.
        start : str | int | None
            사업연도. None이면 최근 연도.
        end : int | None
            종료 연도. start~end 연속 조회.
        q : int | None
            분기 선택. None=연간, 0=Q1~Q4 전부, 1=Q1, 2=Q2, 3=Q3, 4=사업보고서.

        Examples
        --------
        >>> d.report("삼성전자", "배당")
        >>> d.report("삼성전자", "배당", 2020, end=2024)
        >>> d.report("삼성전자", "배당", 2020, end=2024, q=0)   # 분기별
        >>> d.report("삼성전자", "배당", 2020, end=2024, q=2)   # Q2만
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
        """
        corpCodeStr = _resolveCorpCode(self._client, corp)
        return self._client.getDf("majorstock.json", {"corp_code": corpCodeStr})

    def executiveShares(self, corp: str) -> pl.DataFrame:
        """임원·주요주주 소유보고.

        Examples
        --------
        >>> d.executiveShares("삼성전자")
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
        if corp.isdigit() and len(corp) == 6:
            match = df.filter(pl.col("stock_code") == corp)
            if match.height > 0:
                return match["corp_name"][0]
        elif corp.isdigit() and len(corp) == 8:
            match = df.filter(pl.col("corp_code") == corp)
            if match.height > 0:
                return match["corp_name"][0]
        return corp

    @staticmethod
    def filingTypes() -> dict[str, str]:
        """공시유형 코드표."""
        return dict(FILING_TYPES)

    @staticmethod
    def markets() -> dict[str, str]:
        """법인구분 코드표."""
        return dict(CORP_CLASS)

    @staticmethod
    def reportTypes() -> list[str]:
        """사업보고서 API 지원 카테고리."""
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


# ── DartCompany — 회사 프록시 ──────────────────────────────


def _autoEnd() -> int:
    """현재 연도."""
    return datetime.now().year


def _resolveQ(q: int | None, hasRange: bool) -> tuple[bool, str]:
    """q 파라미터 → (quarterly, quarter) 변환.

    q=None + 범위 → Q1~Q4 전부 (quarterly=True)
    q=None + 단건 → annual (quarterly=False)
    q=1    → Q1만
    q=2    → Q2만
    q=3    → Q3만
    q=4    → annual(사업보고서)만
    """
    if q is None:
        if hasRange:
            return True, "annual"  # 범위 → 전분기
        return False, "annual"  # 단건 → 연간 1건

    if q == 0:
        return True, "annual"  # 명시적 전분기

    qMap = {1: "Q1", 2: "Q2", 3: "Q3", 4: "annual"}
    quarter = qMap.get(q)
    if quarter is None:
        raise ValueError(f"q는 0~4 또는 None: q={q}")
    return False, quarter


class DartCompany:
    """회사별 프록시 — 메서드 5개로 전체 API 접근.

    ``d("삼성전자")``로 생성.

    핵심 규칙:
    - start만 주면 end는 자동으로 현재 연도
    - start도 안 주면 최근 1건
    - q 생략 → Q1~Q4 전부 / q=1 → Q1만 / q=2 → Q2만

    Examples
    --------
    >>> s = d("삼성전자")
    >>> s.finance(2022)                # 2022~현재 Q1~Q4 전부
    >>> s.finance(2022, q=4)           # 2022~현재 사업보고서만
    >>> s.report("배당", 2020)         # 2020~현재 Q1~Q4 전부
    >>> s.filings("2024")
    >>> s.info()
    >>> s.shares()
    """

    def __init__(self, dart: Dart, corp: str):
        self._dart = dart
        self._corp = corp

    def report(
        self,
        category: str,
        start: str | int | None = None,
        *,
        end: int | None = None,
        q: int | None = None,
    ) -> pl.DataFrame:
        """사업보고서 56개 카테고리 조회.

        start만 주면 end는 현재 연도까지 자동.

        Parameters
        ----------
        category : str
            카테고리명 (배당, 직원, 임원, 최대주주, 주식총수 등).
        start : int | None
            시작 연도. None이면 최근 1건.
        end : int | None
            종료 연도. None + start있으면 현재 연도.
        q : int | None
            분기 선택. None=Q1~Q4 전부, 1=Q1, 2=Q2, 3=Q3, 4=사업보고서.

        Examples
        --------
        >>> s.report("배당")                  # 최근 1건
        >>> s.report("배당", 2022)            # 2022~현재 Q1~Q4 전부
        >>> s.report("배당", 2022, q=4)       # 2022~현재 사업보고서만
        >>> s.report("배당", 2022, q=2)       # 2022~현재 Q2만
        >>> s.report("직원", 2022, end=2023)  # 2022~2023 Q1~Q4
        """
        if start is not None and end is None:
            end = _autoEnd()
        # DartCompany: start 있으면 기본 전분기 → q=0으로 변환
        effectiveQ = q
        if q is None and start is not None:
            effectiveQ = 0
        return self._dart.report(
            self._corp,
            category,
            start,
            end=end,
            q=effectiveQ,
        )

    def finance(
        self,
        start: str | int | None = None,
        *,
        end: int | None = None,
        q: int | None = None,
        consolidated: bool = True,
        full: bool = False,
    ) -> pl.DataFrame:
        """재무제표 조회.

        start만 주면 end는 현재 연도까지 자동.

        Parameters
        ----------
        start : int | None
            시작 연도. None이면 최근 1건.
        end : int | None
            종료 연도. None + start있으면 현재 연도.
        q : int | None
            분기 선택. None=Q1~Q4 전부, 1=Q1, 2=Q2, 3=Q3, 4=사업보고서.
        full : bool
            True면 전체 계정.
        consolidated : bool
            True=연결, False=별도.

        Examples
        --------
        >>> s.finance()                       # 최근 1건
        >>> s.finance(2022)                   # 2022~현재 Q1~Q4 전부
        >>> s.finance(2022, q=4)              # 2022~현재 사업보고서만
        >>> s.finance(2022, q=2)              # 2022~현재 Q2만
        >>> s.finance(2023, end=2023)         # 2023 Q1~Q4
        >>> s.finance(2020, full=True)        # 전체 계정
        """
        if start is not None and end is None:
            end = _autoEnd()
        effectiveQ = q
        if q is None and start is not None:
            effectiveQ = 0
        return self._dart.finstate(
            self._corp,
            start,
            end=end,
            q=effectiveQ,
            consolidated=consolidated,
            full=full,
        )

    def filings(
        self,
        start: str | datetime | date | None = None,
        end: str | datetime | date | None = None,
        *,
        type: str | None = None,
        final: bool = False,
    ) -> pl.DataFrame:
        """공시 목록 조회.

        Examples
        --------
        >>> s.filings()                  # 최근 1년
        >>> s.filings("2024")            # 2024년 전체
        >>> s.filings("2024-01", "2024-06")
        >>> s.filings(type="A")          # 정기공시만
        >>> s.filings(final=True)        # 최종보고서만
        """
        return self._dart.filings(
            self._corp,
            start,
            end,
            type=type,
            final=final,
        )

    def info(self) -> dict[str, str]:
        """기업 개황.

        Examples
        --------
        >>> s.info()
        """
        return self._dart.company(self._corp)

    def shares(
        self,
        type: Literal["major", "executive", "all"] = "all",
    ) -> pl.DataFrame | dict[str, pl.DataFrame]:
        """지분공시.

        Parameters
        ----------
        type : str
            "major" = 대량보유만, "executive" = 임원만, "all" = 둘 다.

        Examples
        --------
        >>> s.shares()                # {"major": ..., "executive": ...}
        >>> s.shares("major")         # 대량보유만
        >>> s.shares("executive")     # 임원만
        """
        if type == "major":
            return self._dart.majorShareholders(self._corp)
        if type == "executive":
            return self._dart.executiveShares(self._corp)
        return {
            "major": self._dart.majorShareholders(self._corp),
            "executive": self._dart.executiveShares(self._corp),
        }

    def document(
        self,
        rceptNo: str,
        savePath: str | Path | None = None,
    ) -> Path:
        """공시서류 다운로드.

        Examples
        --------
        >>> s.document(filings["rcept_no"][0])
        """
        return self._dart.document(rceptNo, savePath)

    def documentText(self, rceptNo: str) -> str:
        """공시서류 텍스트 추출.

        Examples
        --------
        >>> s.documentText(filings["rcept_no"][0])
        """
        return self._dart.documentText(rceptNo)

    # ── 저장 ──────────────────────────────────────────────

    def saveFinance(
        self,
        start: str | int | None = None,
        *,
        end: int | None = None,
        q: int | None = None,
        full: bool = True,
    ) -> Path:
        """재무제표 조회 → {dataDir}/dart/finance/{stockCode}.parquet 저장.

        eddmpython/dartlab 호환 포맷. full=True 기본 (전체 계정).

        Examples
        --------
        >>> s.saveFinance(2020)         # 2020~현재 전분기
        >>> s.saveFinance(2023, q=4)    # 2023 사업보고서만
        """
        stockCode = self._resolveStockCode()
        corpName = self._dart._resolveCorpName(self._corp)
        path = _dataPath("finance", stockCode)

        # CFS + OFS 양쪽 수집 (릴리즈 호환)
        frames: list[pl.DataFrame] = []
        for consolidated in (True, False):
            df = self.finance(start, end=end, q=q, full=full, consolidated=consolidated)
            if df.height > 0:
                fsDiv = "CFS" if consolidated else "OFS"
                if "fs_div" not in df.columns:
                    df = df.with_columns(pl.lit(fsDiv).alias("fs_div"))
                frames.append(df)

        if not frames:
            return path
        combined = pl.concat(frames, how="diagonal_relaxed")
        enriched = enrichFinance(combined, stockCode, corpName)
        return _saveFile(enriched, path)

    def _resolveStockCode(self) -> str:
        """종목코드 해석."""
        if self._corp.isdigit() and len(self._corp) == 6:
            return self._corp
        df = loadCorpCodes(self._dart._client)
        match = df.filter(pl.col("corp_name") == self._corp)
        if match.height > 0:
            code = match["stock_code"][0].strip()
            if code:
                return code
        match = df.filter(pl.col("corp_name").str.contains(self._corp, literal=True))
        if match.height > 0:
            code = match["stock_code"][0].strip()
            if code:
                return code
        return ""

    def saveReport(
        self,
        start: str | int | None = None,
        *,
        end: int | None = None,
        q: int | None = None,
        categories: list[str] | None = None,
    ) -> Path:
        """전체 보고서 누적 저장 → {dataDir}/dart/report/{stockCode}.parquet.

        eddmpython 호환 — 1파일에 22개 apiType 누적.

        Parameters
        ----------
        start, end, q : report()와 동일.
        categories : list[str] | None
            저장할 카테고리 목록. None이면 주요 22개 전부.

        Examples
        --------
        >>> s.saveReport(2020)                    # 2020~현재 전분기
        >>> s.saveReport(2023, q=4)               # 2023 사업보고서만
        >>> s.saveReport(2020, categories=["배당","직원"])  # 일부만
        """
        from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn

        targets = categories or _PERIODIC_REPORT_CATEGORIES
        stockCode = self._resolveStockCode()
        corpCodeStr = _resolveCorpCode(self._dart._client, self._corp)
        corpName = self._dart._resolveCorpName(self._corp)
        frames: list[pl.DataFrame] = []

        _progress = Progress(SpinnerColumn(), TextColumn("[bold blue]{task.description}"), BarColumn(), MofNCompleteColumn())
        _task = _progress.add_task(f"보고서 저장 | {corpName}", total=len(targets))
        with _progress:
            for cat in targets:
                _progress.update(_task, description=f"보고서 저장 | {corpName} | {cat}")
                try:
                    df = self.report(cat, start, end=end, q=q)
                    if df.height > 0:
                        endpoint = _REPORT_ENDPOINTS.get(cat, cat)
                        enriched = enrichReport(df, stockCode, corpCodeStr, cat, endpoint)
                        frames.append(enriched)
                except (ValueError, KeyError, RuntimeError, OSError):
                    pass
                _progress.advance(_task)

        path = _dataPath("report", stockCode)
        if not frames:
            return _saveFile(pl.DataFrame(), path)

        combined = pl.concat(frames, how="diagonal_relaxed")
        return _saveFile(combined, path)

    def saveFilings(
        self,
        start: str | datetime | date | None = None,
        end: str | datetime | date | None = None,
        *,
        type: str | None = None,
        final: bool = False,
    ) -> Path:
        """공시목록 누적 저장 → {dataDir}/dart/filings/{stockCode}.parquet.

        기존 파일이 있으면 합쳐서 누적. 중복(rcept_no) 자동 제거.

        Examples
        --------
        >>> s.saveFilings()               # 최근 1년 공시 목록 저장
        >>> s.saveFilings("2020")         # 2020년~현재 누적
        >>> s.saveFilings("2020", type="A")  # 정기공시만
        """
        df = self.filings(start, end, type=type, final=final)
        stockCode = self._resolveStockCode()
        path = _dataPath("filings", stockCode)
        return _saveFile(df, path)

    def xbrl(
        self,
        year: str | int | None = None,
        *,
        q: int | None = None,
    ) -> Path:
        """XBRL 재무제표 원본 파일 다운로드 → {dataDir}/dart/xbrl/{stockCode}_{year}_{q}.zip.

        Parameters
        ----------
        year : int | None
            사업연도. None이면 최근 연도.
        q : int | None
            분기. None이면 사업보고서(Q4).

        Returns
        -------
        Path
            저장된 ZIP 파일 경로.

        Examples
        --------
        >>> s.xbrl(2023)         # 2023 사업보고서 XBRL
        >>> s.xbrl(2024, q=2)    # 2024 반기 XBRL
        """
        corpCodeStr = _resolveCorpCode(self._dart._client, self._corp)
        bsnsYear = str(year) if year else str(datetime.now().year - 1)
        _, quarter = _resolveQ(q, hasRange=False)
        reprtCode = _QUARTER_TO_CODE.get(quarter, "11011")

        raw = self._dart._client.getBytes(
            "fnlttXbrl.xml",
            {"corp_code": corpCodeStr, "reprt_code": reprtCode},
        )

        stockCode = self._resolveStockCode()
        qLabel = q if q else 4
        xbrlDir = Path(_dartlabConfig.dataDir) / "dart" / "xbrl"
        xbrlDir.mkdir(parents=True, exist_ok=True)
        dest = xbrlDir / f"{stockCode}_{bsnsYear}_Q{qLabel}.zip"
        dest.write_bytes(raw)
        return dest

    def __repr__(self) -> str:
        methods = "report | finance | filings | info | shares | saveFinance | saveReport | saveFilings | xbrl"
        return f"DartCompany('{self._corp}') — {methods}"


OpenDart = Dart
OpenDartCompany = DartCompany
