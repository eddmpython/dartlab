"""저장 유틸 — eddmpython 호환 포맷 + 컬럼 한글화.

finance 추가 컬럼: stock_code, corp_name, reprt_nm, fs_div, collect_status
report 추가 컬럼:  apiType, apiName, stockCode, corpCode, year, quarter, collectStatus
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

# ── 매핑 테이블 ────────────────────────────────────────────

from dartlab.engines.company.dart.openapi.constants import (
    CODE_TO_QUARTER_KR as _REPRT_NM,
    KR_TO_API_TYPE as _KR_TO_API_TYPE,
)

_FS_NM_TO_DIV: dict[str, str] = {
    "연결재무제표": "CFS",
    "재무제표": "OFS",
}

_API_NAMES: dict[str, str] = {
    "irdsSttus": "증자(감자)현황",
    "alotMatter": "배당에관한사항",
    "tesstkAcqsDspsSttus": "자기주식취득및처분현황",
    "hyslrSttus": "최대주주현황",
    "hyslrChgSttus": "최대주주변동현황",
    "mrhlSttus": "소액주주현황",
    "exctvSttus": "임원현황",
    "empSttus": "직원등현황",
    "hmvAuditIndvdlBySttus": "이사ㆍ감사의개인별보수현황",
    "hmvAuditAllSttus": "이사ㆍ감사전체의보수현황",
    "indvdlByPay": "개인별보수지급금액",
    "otrCprInvstmntSttus": "타법인출자현황",
    "eleStockIstySttus": "주식등의대량보유상황보고서",
    "stockTotqySttus": "주식총수현황",
    "accnutAdtorNmNdAdtOpinion": "회계감사인의명칭및감사의견",
    "adtServcCnclsSttus": "감사용역체결현황",
    "unrstExctvMendngSttus": "미등기임원보수현황",
    "accnutAdtorNonAdtServcCnclsSttus": "감사비감사계약현황",
    "outcmpnyDrctrNdChangeSttus": "사외이사및변동현황",
    "cprndNrdmpBlce": "회사채미상환잔액",
    "srtpdPsndbtNrdmpBlce": "단기사채미상환잔액",
    "entrprsBilScritsNrdmpBlce": "기업어음미상환잔액",
    "detScritsIsuAcmslt": "채무증권발행실적",
    "cndlCaplScritsNrdmpBlce": "조건부자본증권미상환잔액",
    "newCaplScritsNrdmpBlce": "신종자본증권미상환잔액",
    "prvsrpCptalUseDtls": "공모자금용도상세",
    "pssrpCptalUseDtls": "공모자금사용내역",
    "drctrAdtAllMendngSttusGmtsckConfmAmount": "이사감사보수총회인정금액",
    "drctrAdtAllMendngSttusMendngPymntamtTyCl": "이사감사보수지급형태별",
    "piicDecsn": "유상증자결정",
    "fricDecsn": "무상증자결정",
    "crtskcrtDecsn": "유무상증자결정",
    "crcaDecsn": "감자결정",
    "tesstkAcqsDecsn": "자기주식취득결정",
    "tesstkDspsDecsn": "자기주식처분결정",
    "mrgDecsn": "합병결정",
    "divDecsn": "분할결정",
    "stkExtrDecsn": "주식교환이전결정",
    "bsnTrfDecsn": "사업양도결정",
    "bsnInhDecsn": "사업양수결정",
    "otcprStkInvscDecsn": "타법인주식양도결정",
    "otcprStkInvscrInhDecsn": "타법인주식양수결정",
    "cvbdIsDecsn": "전환사채발행결정",
    "bdwtIsDecsn": "신주인수권부사채발행결정",
    "exbdIsDecsn": "교환사채발행결정",
    "dfOcr": "부도발생",
    "bsnsSspd": "영업정지",
    "crtRcvBg": "회생절차개시",
    "dsRsn": "해산사유발생",
    "bnkMngtPcbg": "채권관리절차개시",
    "bnkMngtPcsp": "채권관리절차중단",
    "wdCocobdIsDecsn": "조건부자본증권발행결정",
    "ovLstDecsn": "해외상장결정",
    "ovDlstDecsn": "해외상장폐지결정",
    "ovLst": "해외상장",
    "ovDlst": "해외상장폐지",
}

# 컬럼 한글화 매핑
_FINANCE_KR: dict[str, str] = {
    "bsns_year": "사업연도",
    "reprt_code": "보고서코드",
    "reprt_nm": "보고서명",
    "corp_code": "고유번호",
    "corp_name": "회사명",
    "stock_code": "종목코드",
    "fs_div": "재무제표구분",
    "fs_nm": "재무제표명",
    "sj_div": "재무제표종류",
    "sj_nm": "재무제표종류명",
    "account_id": "계정ID",
    "account_nm": "계정명",
    "account_detail": "계정상세",
    "thstrm_nm": "당기명",
    "thstrm_dt": "당기일자",
    "thstrm_amount": "당기금액",
    "thstrm_add_amount": "당기누적금액",
    "frmtrm_nm": "전기명",
    "frmtrm_dt": "전기일자",
    "frmtrm_amount": "전기금액",
    "frmtrm_add_amount": "전기누적금액",
    "bfefrmtrm_nm": "전전기명",
    "bfefrmtrm_dt": "전전기일자",
    "bfefrmtrm_amount": "전전기금액",
    "ord": "정렬순서",
    "currency": "통화",
    "collect_status": "수집상태",
}

_REPORT_KR: dict[str, str] = {
    "rcept_no": "접수번호",
    "rcept_dt": "접수일자",
    "corp_cls": "법인구분",
    "corp_code": "고유번호",
    "corp_name": "회사명",
    "stock_code": "종목코드",
    "stockCode": "종목코드",
    "corpCode": "고유번호",
    "apiType": "보고서유형",
    "apiName": "보고서명",
    "year": "사업연도",
    "quarter": "분기",
    "collectStatus": "수집상태",
    "stlm_dt": "결산일",
    "se": "구분",
    "thstrm": "당기",
    "frmtrm": "전기",
    "lwfr": "전전기",
    "stock_knd": "주식종류",
}

_FILINGS_KR: dict[str, str] = {
    "corp_code": "고유번호",
    "corp_name": "회사명",
    "stock_code": "종목코드",
    "corp_cls": "법인구분",
    "report_nm": "보고서명",
    "rcept_no": "접수번호",
    "flr_nm": "공시제출인명",
    "rcept_dt": "접수일자",
    "rm": "비고",
}

_COMPANY_KR: dict[str, str] = {
    "corp_code": "고유번호",
    "corp_name": "회사명",
    "corp_name_eng": "영문명",
    "stock_name": "종목명",
    "stock_code": "종목코드",
    "ceo_nm": "대표자",
    "corp_cls": "법인구분",
    "jurir_no": "법인등록번호",
    "bizr_no": "사업자등록번호",
    "adres": "주소",
    "hm_url": "홈페이지",
    "ir_url": "IR홈페이지",
    "phn_no": "전화번호",
    "fax_no": "팩스번호",
    "induty_code": "업종코드",
    "est_dt": "설립일",
    "acc_mt": "결산월",
}


# ── enrich 함수 ────────────────────────────────────────────


def enrichFinance(
    df: pl.DataFrame,
    stockCode: str,
    corpName: str,
) -> pl.DataFrame:
    """재무제표 DataFrame에 eddmpython 호환 컬럼 추가."""
    if df.height == 0:
        return df

    enriched = df
    if "stock_code" not in df.columns:
        enriched = enriched.with_columns(pl.lit(stockCode).alias("stock_code"))
    if "corp_name" not in df.columns:
        enriched = enriched.with_columns(pl.lit(corpName).alias("corp_name"))
    if "reprt_nm" not in df.columns and "reprt_code" in df.columns:
        enriched = enriched.with_columns(
            pl.col("reprt_code").replace_strict(_REPRT_NM, default="기타").alias("reprt_nm")
        )
    if "fs_div" not in df.columns:
        if "fs_nm" in df.columns:
            enriched = enriched.with_columns(
                pl.col("fs_nm").replace_strict(_FS_NM_TO_DIV, default="CFS").alias("fs_div")
            )
        else:
            enriched = enriched.with_columns(pl.lit("CFS").alias("fs_div"))
    if "fs_nm" not in df.columns and "fs_div" in enriched.columns:
        enriched = enriched.with_columns(
            pl.col("fs_div")
            .replace_strict({"CFS": "연결재무제표", "OFS": "재무제표"}, default="재무제표")
            .alias("fs_nm")
        )
    if "collect_status" not in df.columns:
        enriched = enriched.with_columns(pl.lit("collected").alias("collect_status"))

    return enriched


def enrichReport(
    df: pl.DataFrame,
    stockCode: str,
    corpCode: str,
    apiType: str,
    apiEndpoint: str,
) -> pl.DataFrame:
    """보고서 DataFrame에 eddmpython 호환 컬럼 추가."""
    if df.height == 0:
        return df

    # eddmpython 호환: apiType은 영문 camelCase
    engApiType = _KR_TO_API_TYPE.get(apiType, apiType)
    apiName = _API_NAMES.get(apiEndpoint, apiType)
    enriched = df

    # apiType은 항상 영문으로 덮어쓰기 (API 응답에 한글이 들어올 수 있음)
    enriched = enriched.with_columns(pl.lit(engApiType).alias("apiType"))
    if "apiName" not in df.columns:
        enriched = enriched.with_columns(pl.lit(apiName).alias("apiName"))
    if "stockCode" not in df.columns:
        enriched = enriched.with_columns(pl.lit(stockCode).alias("stockCode"))
    if "corpCode" not in df.columns:
        enriched = enriched.with_columns(pl.lit(corpCode).alias("corpCode"))
    if "year" not in df.columns:
        if "bsns_year" in df.columns:
            enriched = enriched.with_columns(pl.col("bsns_year").alias("year"))
        elif "stlm_dt" in df.columns:
            enriched = enriched.with_columns(pl.col("stlm_dt").str.slice(0, 4).alias("year"))
    if "quarter" not in df.columns:
        if "reprt_code" in df.columns:
            enriched = enriched.with_columns(
                pl.col("reprt_code").replace_strict(_REPRT_NM, default="기타").alias("quarter")
            )
        elif "stlm_dt" in df.columns:
            enriched = enriched.with_columns(
                pl.col("stlm_dt")
                .str.slice(5, 2)
                .replace_strict(
                    {"03": "1분기", "06": "2분기", "09": "3분기", "12": "4분기"},
                    default="기타",
                )
                .alias("quarter")
            )
    if "collectStatus" not in df.columns:
        enriched = enriched.with_columns(pl.lit(1, dtype=pl.Int64).alias("collectStatus"))

    return enriched


# ── 컬럼 한글화 ────────────────────────────────────────────


def korColumns(
    df: pl.DataFrame,
    category: str = "finance",
) -> pl.DataFrame:
    """컬럼명을 한글로 변환.

    Parameters
    ----------
    df : pl.DataFrame
        변환할 DataFrame.
    category : str
        "finance", "report", "filings" 중 하나.

    Returns
    -------
    pl.DataFrame
        한글 컬럼명 DataFrame.

    Examples
    --------
    >>> df = s.finance(2023)
    >>> korColumns(df, "finance")
    """
    mapping = {
        "finance": _FINANCE_KR,
        "report": _REPORT_KR,
        "filings": _FILINGS_KR,
        "company": _COMPANY_KR,
    }.get(category, {})

    # 중복 방지: 이미 사용된 한글명은 건너뜀
    usedNames: set[str] = set()
    renames: dict[str, str] = {}
    for col in df.columns:
        krName = mapping.get(col)
        if krName and krName not in usedNames:
            renames[col] = krName
            usedNames.add(krName)

    if renames:
        return df.rename(renames)
    return df


# ── 저장 ───────────────────────────────────────────────────


def save(
    df: pl.DataFrame,
    path: str | Path,
) -> Path:
    """DataFrame을 파일로 저장. 확장자로 포맷 자동 감지.

    저장은 항상 원본 컬럼명으로. 한글화는 korColumns()로 조회 시에만.

    Parameters
    ----------
    df : pl.DataFrame
        저장할 데이터.
    path : str | Path
        저장 경로. .parquet 또는 .csv

    Returns
    -------
    Path
        저장된 파일 경로.
    """
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    # 기존 파일이 있으면 누적 (append + 중복 제거)
    if dest.exists():
        existing = pl.read_parquet(dest)
        combined = pl.concat([existing, df], how="diagonal_relaxed")
        # 중복 제거: 모든 컬럼 기준 unique
        combined = combined.unique()
        combined.write_parquet(dest)
    else:
        df.write_parquet(dest)

    return dest
