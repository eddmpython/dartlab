"""저장 유틸 — eddmpython 호환 포맷 + 컬럼 한글화.

finance 추가 컬럼: stock_code, corp_name, reprt_nm, fs_div, collect_status
report 추가 컬럼:  apiType, apiName, stockCode, corpCode, year, quarter, collectStatus
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import polars as pl

# ── 매핑 테이블 ────────────────────────────────────────────
from dartlab.core.dartConstants import (
    CODE_TO_QUARTER_KR as _REPRT_NM,
)
from dartlab.core.dartConstants import (
    KR_TO_API_TYPE as _KR_TO_API_TYPE,
)

_FS_NM_TO_DIV: dict[str, str] = {
    "연결재무제표": "CFS",
    "재무제표": "OFS",
}

_REPRT_NM_TO_CODE: dict[str, str] = {v: k for k, v in _REPRT_NM.items()}

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
    "account_nm": "항목",
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
    """재무제표 DataFrame에 eddmpython 호환 컬럼 추가.

    Args:
        df: 인자.
        stockCode: 인자.
        corpName: 인자.

    Raises:
        없음.

    Example:
        >>> enrichFinance(...)

    Returns:
        pl.DataFrame — 한글화/추가 컬럼 후 결과.

    SeeAlso:
        - ``enrichFinance`` / ``enrichReport`` / ``saveParquet`` — 본 모듈 함수.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - DART finance/report DataFrame → 한글 컬럼 + 추가 컬럼 (corp_name/stock_code 등) + parquet 저장.
          eddmpython 호환 포맷.

    Guide:
        - 운영자 수집 파이프라인 — 사용자 API 직접 호출 X.

    AIContext:
        internal saver — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - eddmpython 호환 컬럼 가정 X — 본 모듈이 한글화/추가.
            - 저장 경로 명시 X → 기본 dataDir 사용.
        OutputSchema:
            - Path / int / pl.DataFrame — 함수별.
        Prerequisites:
            - finance/report 데이터.
        Freshness:
            - 호출 시점.
        Dataflow:
            - DataFrame → 한글 컬럼 + 추가 컬럼 → parquet.
        TargetMarkets:
            - KR (DART) 저장.
    """
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
    """보고서 DataFrame에 eddmpython 호환 컬럼 추가.

    Args:
        df: 인자.
        stockCode: 인자.
        corpCode: 인자.
        apiType: 인자.
        apiEndpoint: 인자.

    Raises:
        없음.

    Example:
        >>> enrichReport(...)

    Returns:
        pl.DataFrame — 한글화/추가 컬럼 후 결과.

    SeeAlso:
        - ``enrichFinance`` / ``enrichReport`` / ``saveParquet`` — 본 모듈 함수.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - DART finance/report DataFrame → 한글 컬럼 + 추가 컬럼 (corp_name/stock_code 등) + parquet 저장.
          eddmpython 호환 포맷.

    Guide:
        - 운영자 수집 파이프라인 — 사용자 API 직접 호출 X.

    AIContext:
        internal saver — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - eddmpython 호환 컬럼 가정 X — 본 모듈이 한글화/추가.
            - 저장 경로 명시 X → 기본 dataDir 사용.
        OutputSchema:
            - Path / int / pl.DataFrame — 함수별.
        Prerequisites:
            - finance/report 데이터.
        Freshness:
            - 호출 시점.
        Dataflow:
            - DataFrame → 한글 컬럼 + 추가 컬럼 → parquet.
        TargetMarkets:
            - KR (DART) 저장.
    """
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

    Raises:
        없음.

    Args:
        df: Polars DataFrame 입력.
        category: finance/report/filings/company.

    Returns:
        pl.DataFrame — 한글화/추가 컬럼 후 결과.

    SeeAlso:
        - ``enrichFinance`` / ``enrichReport`` / ``saveParquet`` — 본 모듈 함수.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - DART finance/report DataFrame → 한글 컬럼 + 추가 컬럼 (corp_name/stock_code 등) + parquet 저장.
          eddmpython 호환 포맷.

    Guide:
        - 운영자 수집 파이프라인 — 사용자 API 직접 호출 X.

    AIContext:
        internal saver — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - eddmpython 호환 컬럼 가정 X — 본 모듈이 한글화/추가.
            - 저장 경로 명시 X → 기본 dataDir 사용.
        OutputSchema:
            - Path / int / pl.DataFrame — 함수별.
        Prerequisites:
            - finance/report 데이터.
        Freshness:
            - 호출 시점.
        Dataflow:
            - DataFrame → 한글 컬럼 + 추가 컬럼 → parquet.
        TargetMarkets:
            - KR (DART) 저장.
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

# Phase A — predicate pushdown 활성화. row group 안 데이터가 sort 순서로 들어가면
# row group statistics (min/max) 가 disjoint 가 되어 pl.scan_parquet().filter() 가
# irrelevant row group 을 skip 한다. category 별 sort 키는 가장 자주 filter 되는 컬럼.
_SORT_BY_CATEGORY: dict[str, list[str]] = {
    "finance": ["sj_div", "fs_div", "bsns_year", "reprt_nm", "account_id"],
    "report": ["apiType", "bsns_year", "rcept_no"],
    "filings": ["bsns_year", "rcept_dt", "rcept_no"],
    "allFilings": ["bsns_year", "rcept_dt", "rcept_no"],
}
_ROW_GROUP_SIZE = 4096


def _categoryForPath(dest: Path) -> str | None:
    """``data/dart/{category}/{stockCode}.parquet`` 경로에서 category 추출."""
    parts = dest.parts
    if "dart" in parts:
        idx = parts.index("dart")
        if idx + 1 < len(parts) - 1:
            return parts[idx + 1]
    return None


def writeParquetSorted(df: pl.DataFrame, dest: Path) -> None:
    """category 자동 추론 + sort + row_group_size 적용 후 원자적 write.

    Phase A 처방 — DART finance/report parquet 의 row group statistics 를
    sort 컬럼 기반 disjoint 으로 만들어 predicate pushdown 을 활성화한다.

    Args:
        df: 저장할 DataFrame.
        dest: 최종 parquet 경로. ``data/dart/{category}/...`` 패턴이면 sort 자동.
            그 외 경로는 sort 없이 write (호환 보존).

    Returns:
        None.

    Raises:
        OSError: 디스크 쓰기 실패.

    Example:
        >>> writeParquetSorted(df, Path("data/dart/finance/005930.parquet"))  # doctest: +SKIP
    """
    cat = _categoryForPath(dest)
    sortBy = _SORT_BY_CATEGORY.get(cat or "", [])
    sortCols = [c for c in sortBy if c in df.columns]
    if sortCols:
        df = df.sort(sortCols)
    tmp = dest.with_name(f"{dest.name}.tmp")
    df.write_parquet(
        tmp,
        compression="zstd",
        statistics=True,
        row_group_size=_ROW_GROUP_SIZE,
    )
    tmp.replace(dest)


def _writeParquetAtomic(df: pl.DataFrame, dest: Path) -> None:
    """Atomic write — Phase A 이후 ``writeParquetSorted`` 로 위임."""
    writeParquetSorted(df, dest)


def _keyExpr(columns: Sequence[str]) -> pl.Expr:
    return pl.concat_str([pl.col(c).cast(pl.Utf8) for c in columns], separator="\x1f")


def _materializeReplacementKeys(df: pl.DataFrame, keyColumns: Sequence[str]) -> pl.DataFrame:
    """Fill known legacy aliases for replacement keys before safe merge."""
    enriched = df
    expressions: list[pl.Expr] = []

    if "reprt_code" in keyColumns and "reprt_code" not in enriched.columns and "reprt_nm" in enriched.columns:
        expressions.append(pl.col("reprt_nm").replace_strict(_REPRT_NM_TO_CODE, default=None).alias("reprt_code"))
    if "fs_div" in keyColumns and "fs_div" not in enriched.columns and "fs_nm" in enriched.columns:
        expressions.append(pl.col("fs_nm").replace_strict(_FS_NM_TO_DIV, default=None).alias("fs_div"))
    if "year" in keyColumns and "year" not in enriched.columns and "bsns_year" in enriched.columns:
        expressions.append(pl.col("bsns_year").alias("year"))
    if "quarter" in keyColumns and "quarter" not in enriched.columns and "reprt_code" in enriched.columns:
        expressions.append(pl.col("reprt_code").replace_strict(_REPRT_NM, default=None).alias("quarter"))
    if "stock_code" in keyColumns and "stock_code" not in enriched.columns and "stockCode" in enriched.columns:
        expressions.append(pl.col("stockCode").alias("stock_code"))
    if "stockCode" in keyColumns and "stockCode" not in enriched.columns and "stock_code" in enriched.columns:
        expressions.append(pl.col("stock_code").alias("stockCode"))
    if "corp_code" in keyColumns and "corp_code" not in enriched.columns and "corpCode" in enriched.columns:
        expressions.append(pl.col("corpCode").alias("corp_code"))
    if "corpCode" in keyColumns and "corpCode" not in enriched.columns and "corp_code" in enriched.columns:
        expressions.append(pl.col("corp_code").alias("corpCode"))

    if expressions:
        enriched = enriched.with_columns(expressions)
    return enriched


def _validateReplacementKeys(df: pl.DataFrame, keyColumns: Sequence[str], *, label: str) -> None:
    missing = [c for c in keyColumns if c not in df.columns]
    if missing:
        raise ValueError(f"safe replacement requires {label} key columns: {missing}")

    if label != "new":
        return

    nullCounts = df.select(pl.any_horizontal([pl.col(c).is_null() for c in keyColumns]).sum().alias("nullKeys"))[
        "nullKeys"
    ][0]
    if nullCounts:
        raise ValueError(f"safe replacement found null {label} key values: {keyColumns}")


def saveReplacingByKeys(
    df: pl.DataFrame,
    path: str | Path,
    keyColumns: Sequence[str],
) -> Path:
    """Save by replacing existing rows that share logical keys with ``df``.

    This is for DART incremental refreshes where a corrected filing maps to an
    already-collected period. It removes only the exact logical keys present in
    the newly collected rows, then appends those new rows.

    Args:
        df: 새로 수집한 행. ``keyColumns`` 를 직접 갖거나 복원 가능한 legacy alias를 가져야 한다.
        path: 교체 병합할 parquet 경로.
        keyColumns: 기존 행 제거 범위를 결정하는 논리 키 컬럼 목록.

    Returns:
        Path — 저장된 parquet 경로.

    Raises:
        ValueError: 새 데이터나 기존 parquet에서 병합 키를 구성할 수 없거나 null 키가 있을 때.

    Example:
        >>> saveReplacingByKeys(df, "data/dart/finance/005930.parquet", ["bsns_year", "reprt_code", "fs_div"])

    SeeAlso:
        - ``save`` — 단순 overwrite 저장.
        - ``enrichFinance`` / ``enrichReport`` — 증분 수집 후 safe replacement 호출 지점.

    Requires:
        - ``df`` 와 기존 parquet 모두 ``keyColumns`` 를 직접 갖거나 legacy alias로 복원 가능해야 한다.
        - key 컬럼은 null 없이 완전해야 한다.

    Capabilities:
        - DART finance/report 증분 refresh 에서 새로 수집한 정기공시 기간만 교체 병합한다.

    Guide:
        - 수집 대상 기간이 명확한 증분 저장에만 사용한다. 키 검증 실패 시 append fallback 없이 중단한다.

    AIContext:
        internal DART saver helper — 기존 HF parquet 전체를 보존하면서 동일 logical key 행만 교체한다.

    LLM Specifications:
        AntiPatterns:
            - key 컬럼 누락 시 append 로 우회.
            - 기존 parquet schema 를 검증하지 않고 overwrite.
        OutputSchema:
            - ``Path`` — 저장된 parquet 경로.
        Prerequisites:
            - polars DataFrame, parquet path, logical replacement key columns.
        Freshness:
            - DART OpenAPI 증분 수집 직후 현재 공시 기간 기준.
        Dataflow:
            - new df → key materialize/validate → existing parquet read → matching keys remove → concat → atomic write.
        TargetMarkets:
            - KR (DART).
    """
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    keyColumns = list(keyColumns)
    df = _materializeReplacementKeys(df, keyColumns)
    _validateReplacementKeys(df, keyColumns, label="new")

    if df.height == 0:
        if not dest.exists():
            _writeParquetAtomic(df, dest)
        return dest

    if not dest.exists():
        _writeParquetAtomic(df.unique(), dest)
        return dest

    existing = _materializeReplacementKeys(pl.read_parquet(dest), keyColumns)
    _validateReplacementKeys(existing, keyColumns, label="existing")

    keyCol = "__dartlab_replace_key"
    newKeys = df.with_columns(_keyExpr(keyColumns).alias(keyCol)).select(keyCol).unique().get_column(keyCol).to_list()
    keep = (
        existing.with_columns(_keyExpr(keyColumns).alias(keyCol))
        .filter(pl.col(keyCol).is_null() | ~pl.col(keyCol).is_in(newKeys))
        .drop(keyCol)
    )
    combined = pl.concat([keep, df], how="diagonal_relaxed").unique()
    _writeParquetAtomic(combined, dest)
    return dest


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

    Raises:
        없음.

    Example:
        >>> save(...)

    Args:
        df: Polars DataFrame 입력.
        path: 저장 경로.

    Returns:
        Path — 저장된 parquet 경로.

    SeeAlso:
        - ``enrichFinance`` / ``enrichReport`` / ``saveParquet`` — 본 모듈 함수.

    Requires:
        - dartlab
        - polars

    Capabilities:
        - DART finance/report DataFrame → 한글 컬럼 + 추가 컬럼 (corp_name/stock_code 등) + parquet 저장.
          eddmpython 호환 포맷.

    Guide:
        - 운영자 수집 파이프라인 — 사용자 API 직접 호출 X.

    AIContext:
        internal saver — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - eddmpython 호환 컬럼 가정 X — 본 모듈이 한글화/추가.
            - 저장 경로 명시 X → 기본 dataDir 사용.
        OutputSchema:
            - Path / int / pl.DataFrame — 함수별.
        Prerequisites:
            - finance/report 데이터.
        Freshness:
            - 호출 시점.
        Dataflow:
            - DataFrame → 한글 컬럼 + 추가 컬럼 → parquet.
        TargetMarkets:
            - KR (DART) 저장.
    """
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    # 기존 파일이 있으면 누적 (append + 중복 제거)
    if dest.exists():
        existing = pl.read_parquet(dest)
        combined = pl.concat([existing, df], how="diagonal_relaxed")
        # 중복 제거: 모든 컬럼 기준 unique
        combined = combined.unique()
        _writeParquetAtomic(combined, dest)
    else:
        _writeParquetAtomic(df, dest)

    return dest
