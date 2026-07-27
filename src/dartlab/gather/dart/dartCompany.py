"""dart/openapi DartCompany — dart.py 분할 (규칙 3 LoC).

DartCompany (회사별 프록시) + _autoEnd / _resolveQ + OpenDartCompany alias.
"""

from __future__ import annotations

import io
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import polars as pl

import dartlab.config as _dartlabConfig
from dartlab.core.dartBuild import (
    enrichFinance,
    enrichReport,
)
from dartlab.core.dartBuild import (
    save as _saveFile,
)
from dartlab.core.dartConstants import (
    QUARTER_TO_CODE as _QUARTER_TO_CODE,
)
from dartlab.core.market import isKrStockCode, normalizeKrCode
from dartlab.gather.dart.corpCode import loadCorpCodes
from dartlab.gather.dart.dartHelpers import _dataPath
from dartlab.gather.dart.disclosure import _resolveCorpCode

if TYPE_CHECKING:
    # dart.py 가 dartCompany 를 re-export(순환) — Dart 는 타입힌트뿐이라 TYPE_CHECKING.
    from dartlab.gather.dart.dart import Dart

# _PERIODIC_REPORT_CATEGORIES·_REPORT_ENDPOINTS 는 dart.py 정의 — 메서드 내부 lazy import
# (dartCompany↔dart 순환 회피).

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

        Raises:
            없음.

        Args:
            category: report 카테고리 (배당/주식총수/자기주식 등).
            start: 시작 연도 또는 ISO 날짜. None 이면 기본값.
            end: 종료 연도. None 이면 현재 연도.
            q: 분기 (1~4). None 이면 4분기 (사업보고서).

        Returns:
            pl.DataFrame — DART OpenAPI 응답 정규화 결과.
              일 호출 한도 (개인 1만/일) 내 호출.
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

        Raises:
            없음.

        Args:
            start: 시작 연도 또는 ISO 날짜. None 이면 기본값.
            end: 종료 연도. None 이면 현재 연도.
            q: 분기 (1~4). None 이면 4분기 (사업보고서).
            consolidated: True 면 연결, False 면 별도.
            full: True 면 모든 계정, False 면 주요 계정만.

        Returns:
            pl.DataFrame — DART OpenAPI 응답 정규화 결과.
              일 호출 한도 (개인 1만/일) 내 호출.
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

        Args:
            start: 인자.
            end: 인자.
            type: 인자.
            final: 인자.

        Raises:
            없음.

        Returns:
            pl.DataFrame — DART OpenAPI 응답 정규화 결과.
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

        Args:
            (인자 자동 생성).

        Raises:
            없음.

        Returns:
            dict — 기업 개황 정보 (corpCode/corpName/stockName/stockCode 등).
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

        Raises:
            없음.

        Args:
            type: 주주 종류 — "major" / "executive" / "all".

        Returns:
            pl.DataFrame 또는 dict[str, pl.DataFrame] — 주주 종류별 결과.
              일 호출 한도 (개인 1만/일) 내 호출.
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

        Args:
            rceptNo: 인자.
            savePath: 인자.

        Raises:
            없음.

        Returns:
            Path — 저장된 파일 경로.
        """
        return self._dart.document(rceptNo, savePath)

    def documentText(self, rceptNo: str) -> str:
        """공시서류 텍스트 추출.

        Examples
        --------
        >>> s.documentText(filings["rcept_no"][0])

        Args:
            rceptNo: 인자.

        Raises:
            없음.

        Returns:
            str — DART OpenAPI 응답 텍스트.
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

        Args:
            start: 인자.
            end: 인자.
            q: 인자.
            full: 인자.

        Raises:
            없음.

        Returns:
            Path — 저장된 파일 경로.
              일 호출 한도 (개인 1만/일) 내 호출.
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
        if isKrStockCode(self._corp):
            return normalizeKrCode(self._corp)
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

        Raises:
            없음.

        Args:
            start: 시작 연도 또는 ISO 날짜. None 이면 기본값.
            end: 종료 연도. None 이면 현재 연도.
            q: 분기 (1~4). None 이면 4분기 (사업보고서).
            categories: 처리 카테고리 리스트. None 이면 전체.

        Returns:
            Path — 저장된 파일 경로.
              일 호출 한도 (개인 1만/일) 내 호출.
        """
        from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TextColumn

        from dartlab.core.logger import getConsole

        # dart.py 정의 상수 — lazy import 로 dartCompany↔dart 순환 회피.
        from dartlab.gather.dart.dart import _PERIODIC_REPORT_CATEGORIES, _REPORT_ENDPOINTS

        targets = categories or _PERIODIC_REPORT_CATEGORIES
        stockCode = self._resolveStockCode()
        corpCodeStr = _resolveCorpCode(self._dart._client, self._corp)
        corpName = self._dart._resolveCorpName(self._corp)
        frames: list[pl.DataFrame] = []

        _progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=getConsole(),
        )
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

        Args:
            start: 인자.
            end: 인자.
            type: 인자.
            final: 인자.

        Raises:
            없음.

        Returns:
            Path — 저장된 파일 경로.
              일 호출 한도 (개인 1만/일) 내 호출.
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

        Raises:
            없음.

        Args:
            year: 사업연도 (예 2024). None 이면 직전 연도.
            q: 분기 (1~4). None 이면 4분기 (사업보고서).

        Returns:
            Path — 저장된 파일 경로.
              일 호출 한도 (개인 1만/일) 내 호출.
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


OpenDartCompany = DartCompany
