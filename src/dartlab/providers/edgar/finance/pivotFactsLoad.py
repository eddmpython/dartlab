"""edgar pivot 팩트 로딩/분류 — pivot.py 분할 (규칙 3 LoC).

_splitStmtFacts / _storeMappedValue / _loadFacts / _autoDownloadEdgarFinance /
_guessStmt — XBRL fact DataFrame 의 statement 분류 + 디스크 로딩.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import polars as pl

from dartlab.providers.edgar.finance.mapper import EdgarMapper

_SUPPORTED_FINANCE_NAMESPACES: tuple[str, ...] = ("us-gaap", "ifrs-full")


def _selectFinanceNamespace(df: pl.DataFrame) -> pl.DataFrame:
    """statement fact에 사용할 단일 taxonomy를 선택한다."""
    if "namespace" not in df.columns:
        raise ValueError("EDGAR companyfacts에 namespace 컬럼이 없습니다")
    available = sorted(str(value) for value in df["namespace"].drop_nulls().unique().to_list())
    for namespace in _SUPPORTED_FINANCE_NAMESPACES:
        if namespace in available:
            return df.filter(pl.col("namespace") == namespace)
    availableLabel = ", ".join(available) if available else "<empty>"
    supportedLabel = ", ".join(_SUPPORTED_FINANCE_NAMESPACES)
    raise ValueError(f"지원하는 EDGAR 재무 taxonomy가 없습니다: available={availableLabel}, supported={supportedLabel}")


def _financeNamespace(df: pl.DataFrame) -> str:
    """선택이 끝난 fact frame의 단일 taxonomy를 반환한다."""
    values = df["namespace"].drop_nulls().unique().to_list()
    if len(values) != 1:
        raise ValueError(f"EDGAR 재무 fact는 단일 taxonomy여야 합니다: namespaces={values}")
    return str(values[0])


def _mapFactTag(tag: str, stmt: str, namespace: str) -> str | None:
    """taxonomy별 XBRL concept를 공통 snakeId SSOT로 정규화한다."""
    if namespace == "us-gaap":
        return EdgarMapper.mapToDart(tag, stmt)

    from dartlab.core.accounts.aliases import SNAKEID_ALIASES
    from dartlab.core.accounts.normalize import AccountNormalizer

    snakeId = AccountNormalizer.get().normalize(f"{namespace}_{tag}", tag)
    if snakeId is None:
        snakeId = EdgarMapper.mapToDart(tag, stmt)
    return SNAKEID_ALIASES.get(snakeId, snakeId) if snakeId is not None else None


def _isCommonFactTag(tag: str, namespace: str) -> bool:
    return namespace == "us-gaap" and EdgarMapper.isCommonTag(tag)


def _splitStmtFacts(df: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """XBRL fact 를 sj_div (BS/IS/CF/CI) 로 분류 + USD only 필터.

    XBRL ``unit`` 컬럼이 USD/USDshare/share/USDxshares/pure 등 혼합. 같은 tag 에
    다른 unit 의 entry 가 있을 경우 (소수) 잘못된 합산 위험. 통화성 stmt (BS/IS/CF/CI)
    는 USD only 로 필터링.
    """
    if df.height == 0:
        return {}
    df = _selectFinanceNamespace(df)
    namespace = _financeNamespace(df)

    # XBRL unit 정규화 (USD only).
    # USD/shares(EPS)·shares·pure 등 은 통화 재무제표에 섞이면 스케일 오염 →
    # 별도 경로로 처리 (pivot 밖). test_l2Coverage 의 basic/diluted_earnings_per_share
    # 는 별도 EPS 전용 빌더가 필요 (follow-up).
    if "unit" in df.columns:
        df = df.filter(pl.col("unit") == "USD")
    if df.height == 0:
        return {}

    stmtTags = EdgarMapper.classifyTagsByStmt()

    # standardAccounts의 stmt가 가장 정확 — 태그별 1개 stmt만 배정
    primaryStmt = EdgarMapper.getPrimaryStmtMap()  # tag → stmt (1:1)

    allTags = df.select("tag").unique().to_series().to_list()
    tagToStmt: dict[str, str] = {}
    for tag in allTags:
        # 1순위: standardAccounts의 primary stmt (정확)
        if tag in primaryStmt:
            tagToStmt[tag] = primaryStmt[tag]
        # 2순위: classifyTagsByStmt (충돌 가능 — 첫 번째만)
        elif tag in {t for tags in stmtTags.values() for t in tags}:
            for stmt in ["IS", "BS", "CF", "CI"]:
                if tag in stmtTags.get(stmt, set()):
                    tagToStmt[tag] = stmt
                    break
        elif (snakeId := _mapFactTag(tag, "", namespace)) is not None:
            mappedStmt = EdgarMapper.getAccountStmt(snakeId)
            if mappedStmt in ("IS", "BS", "CF", "CI"):
                tagToStmt[tag] = mappedStmt
        # 3순위: 휴리스틱 (None이면 제외)
        else:
            guessed = _guessStmt(tag)
            if guessed:
                tagToStmt[tag] = guessed

    stmtDfs: dict[str, pl.DataFrame] = {}
    for stmt in ["IS", "BS", "CF", "CI"]:
        stmtTagList = [t for t, s in tagToStmt.items() if s == stmt]
        if not stmtTagList:
            continue
        stmtDf = df.filter(pl.col("tag").is_in(stmtTagList))
        if stmtDf.height > 0:
            stmtDfs[stmt] = stmtDf
    return stmtDfs


def _storeMappedValue(
    stmtValues: dict[str, dict[str, float]],
    stmtSources: dict[str, dict[str, str]],
    dartSid: str,
    period: str,
    value: float,
    isCommon: bool,
) -> None:
    if dartSid not in stmtValues:
        stmtValues[dartSid] = {}
        stmtSources[dartSid] = {}

    prevSource = stmtSources.get(dartSid, {}).get(period)
    if prevSource is None or (prevSource == "learned" and isCommon):
        stmtValues[dartSid][period] = value
        stmtSources.setdefault(dartSid, {})[period] = "common" if isCommon else "learned"


def _loadFacts(edgarDir: Path, cik: str) -> Optional[pl.DataFrame]:
    path = edgarDir / f"{cik}.parquet"
    if not path.exists():
        path = _autoDownloadEdgarFinance(cik, path)
        if path is None:
            return None
    df = pl.read_parquet(path)
    if df.height == 0:
        return df
    return _selectFinanceNamespace(df)


def _autoDownloadEdgarFinance(cik: str, dest: Path) -> Optional[Path]:
    """SEC EDGAR companyfacts API에서 재무 데이터를 자동 다운로드."""
    from urllib.error import URLError

    from dartlab.core.edgarClient import EdgarApiError
    from dartlab.core.messaging import emit

    emit("edgar:sec_download", cik=cik)
    try:
        from dartlab.core.edgarClient import (
            companyFactsToRows,
            getCompanyFactsJson,
        )

        payload = getCompanyFactsJson(cik)
        df = companyFactsToRows(payload)
        if df.is_empty():
            emit("edgar:empty", cik=cik)
            return None
        dest.parent.mkdir(parents=True, exist_ok=True)
        df.write_parquet(dest)
        emit("edgar:save_done", path=str(dest))
        return dest
    except EdgarApiError as e:
        emit("edgar:download_failed", cik=cik, error=str(e))
        response = getattr(e.__cause__, "response", None)
        if getattr(response, "status_code", None) == 404:
            return None
        raise RuntimeError(f"EDGAR companyfacts 자동 다운로드 실패: cik={cik}, error={type(e).__name__}: {e}") from e
    except (URLError, OSError, RuntimeError) as e:
        emit("edgar:download_failed", cik=cik, error=str(e))
        raise RuntimeError(f"EDGAR companyfacts 자동 다운로드 실패: cik={cik}, error={type(e).__name__}: {e}") from e


def _guessStmt(tag: str) -> str | None:
    """XBRL 태그명에서 재무제표 유형을 추정. 매칭 없으면 None (IS에 넣지 않음)."""
    tagLower = tag.lower()

    # CF 키워드 (가장 명확)
    cfKeywords = [
        "cashflow",
        "cash_flow",
        "netcash",
        "payment",
        "proceeds",
        "repayment",
        "issuance",
        "capex",
        "purchaseof",
        "saleof",
    ]
    for kw in cfKeywords:
        if kw in tagLower:
            return "CF"

    # IS 키워드 (명시적으로만)
    isKeywords = [
        "revenue",
        "sales",
        "costofgood",
        "costofrevenue",
        "grossprofit",
        "operatingincome",
        "operatingexpense",
        "sellinggeneral",
        "researchand",
        "interestexpense",
        "incometax",
        "netincome",
        "earningspershare",
        "dilutedearnings",
        "basicearnings",
        "operatingloss",
        "netloss",
        "otheroperating",
        "comprehensiveincome",
    ]
    for kw in isKeywords:
        if kw in tagLower:
            return "IS"

    # BS 키워드
    bsKeywords = [
        "asset",
        "liabilit",
        "equity",
        "receivable",
        "payable",
        "inventory",
        "inventories",
        "cash",
        "debt",
        "borrowing",
        "goodwill",
        "intangible",
        "property",
        "plant",
        "deferred",
        "accruedliabilit",
        "leasecurrent",
        "leasenoncurrent",
        "retainedearning",
        "treasurystock",
        "commonstock",
    ]
    for kw in bsKeywords:
        if kw in tagLower:
            return "BS"

    # detail/note 패턴은 NT(주석) → IS/BS/CF에 넣지 않음
    if "detail" in tagLower or "note" in tagLower:
        return None

    # 매칭 없으면 None — IS에 쓰레기가 들어가는 것을 방지
    return None
