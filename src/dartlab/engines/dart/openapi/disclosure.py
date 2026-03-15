"""공시정보 조회 — OpenDART 공시검색 + 기업개황.

핵심 기능:
- listFilings(): 기업별/날짜별 공시 목록 (자동 페이지네이션)
- companyInfo(): 기업 개황 (대표자, 업종, 주소 등)
"""

from __future__ import annotations

from typing import Literal

import polars as pl

from dartlab.engines.dart.openapi.client import DartClient
from dartlab.engines.dart.openapi.corpCode import findCorpCode

# 공시유형 코드
FILING_TYPES = {
    "A": "정기공시",
    "B": "주요사항보고",
    "C": "발행공시",
    "D": "지분공시",
    "E": "기타공시",
    "F": "외부감사관련",
    "G": "펀드공시",
    "H": "자산유동화",
    "I": "거래소공시",
    "J": "공정위공시",
}

# 법인구분 코드
CORP_CLASS = {
    "Y": "유가증권",
    "K": "코스닥",
    "N": "코넥스",
    "E": "기타",
}


def _resolveCorpCode(client: DartClient, corp: str) -> str:
    """corp_code / 종목코드 / 회사명 → 8자리 corp_code 변환."""
    if len(corp) == 8 and corp.isdigit():
        return corp

    code = findCorpCode(client, corp)
    if code is None:
        raise ValueError(f"'{corp}'에 해당하는 기업을 찾을 수 없습니다.")
    return code


def listFilings(
    client: DartClient,
    corp: str | None = None,
    start: str | None = None,
    end: str | None = None,
    *,
    filingType: str | None = None,
    finalOnly: bool = False,
    corpClass: Literal["Y", "K", "N", "E"] | None = None,
    sort: Literal["date", "crp", "rpt"] = "date",
    ascending: bool = False,
    fetchAll: bool = True,
) -> pl.DataFrame:
    """공시 목록 조회.

    Parameters
    ----------
    client : DartClient
        인증된 클라이언트.
    corp : str | None
        기업 식별자 (종목코드 "005930" / 회사명 "삼성전자" / corp_code).
        None이면 전체 (start 필수).
    start : str | None
        시작일 (YYYYMMDD). corp 없으면 필수.
    end : str | None
        종료일 (YYYYMMDD). 기본값은 오늘.
    filingType : str | None
        공시유형 코드 (A=정기, B=주요사항, C=발행, D=지분, E=기타 등).
    finalOnly : bool
        True면 최종보고서만 (정정 이전 제외).
    corpClass : str | None
        법인구분 (Y=유가증권, K=코스닥, N=코넥스, E=기타).
    sort : str
        정렬 기준 (date=접수일, crp=회사명, rpt=보고서명).
    ascending : bool
        오름차순 정렬 (기본 내림차순).
    fetchAll : bool
        True면 자동 페이지네이션으로 전체 수집.

    Returns
    -------
    pl.DataFrame
        공시 목록. columns: corp_cls, corp_name, corp_code, stock_code,
        report_nm, rcept_no, flr_nm, rcept_dt, rm

    Examples
    --------
    >>> client = DartClient(apiKey="...")
    >>> df = listFilings(client, "005930", "20240101", "20241231")
    >>> df = listFilings(client, "삼성전자", filingType="A")
    >>> df = listFilings(client, start="20240315", end="20240315")
    """
    params: dict[str, str] = {}

    if corp is not None:
        params["corp_code"] = _resolveCorpCode(client, corp)

    if start:
        params["bgn_de"] = start.replace("-", "")
    if end:
        params["end_de"] = end.replace("-", "")

    if filingType:
        params["pblntf_ty"] = filingType
    if finalOnly:
        params["last_reprt_at"] = "Y"
    if corpClass:
        params["corp_cls"] = corpClass

    params["sort"] = sort
    params["sort_mth"] = "asc" if ascending else "desc"

    if fetchAll:
        return client.getDfAll("list.json", params)
    return client.getDf("list.json", params)


def companyInfo(
    client: DartClient,
    corp: str,
) -> dict[str, str]:
    """기업 개황 조회.

    Parameters
    ----------
    corp : str
        기업 식별자 (종목코드 / 회사명 / corp_code).

    Returns
    -------
    dict
        기업 개황 정보. 주요 키:
        - corp_name: 정식 회사명
        - corp_name_eng: 영문명
        - ceo_nm: 대표자명
        - corp_cls: 법인구분 (Y/K/N/E)
        - induty_code: 업종코드
        - est_dt: 설립일
        - acc_mt: 결산월
        - stock_name: 종목명
        - adres: 주소

    Examples
    --------
    >>> client = DartClient(apiKey="...")
    >>> info = companyInfo(client, "005930")
    >>> info["ceo_nm"]
    '한종희'
    """
    corpCode = _resolveCorpCode(client, corp)
    data = client.getJson("company.json", {"corp_code": corpCode})

    exclude = {"status", "message"}
    return {k: v for k, v in data.items() if k not in exclude}
