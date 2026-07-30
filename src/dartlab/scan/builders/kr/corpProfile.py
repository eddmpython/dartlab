"""DART companyInfo 기반 KR 상장사 profile artifact 계약."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import polars as pl

CORP_PROFILE_SCHEMA_VERSION = 2
CORP_PROFILE_SCHEMA = {
    "corp_code": pl.Utf8,
    "stockCode": pl.Utf8,
    "corp_name": pl.Utf8,
    "jurir_no": pl.Utf8,
    "bizr_no": pl.Utf8,
    "acc_mt": pl.Utf8,
    "induty_code": pl.Utf8,
    "est_dt": pl.Utf8,
    "corp_cls": pl.Utf8,
    "profileSchemaVersion": pl.Int16,
}
_JURIR_NO = re.compile(r"\s*([0-9]{6})-?([0-9]{7})\s*")


class CorpProfileIdentityError(RuntimeError):
    """상장사 법인 identity profile이 없거나 모순될 때의 오류."""


def normalizeJurirNo(value: object) -> str | None:
    """법인등록번호를 13자리 숫자로 정규화하고 다른 값은 거부한다.

    Args:
        value: 원본 법인등록번호.

    Returns:
        13자리 숫자 문자열 또는 유효하지 않을 때 None.

    Raises:
        없음.

    Example:
        >>> normalizeJurirNo("123456-1234567")
        '1234561234567'
    """

    matched = _JURIR_NO.fullmatch(str(value or ""))
    if matched is None:
        return None
    return "".join(matched.groups())


def normalizeCorpProfileRow(row: dict[str, Any]) -> dict[str, str | int]:
    """legacy와 최신 companyInfo 행을 canonical profile schema로 정규화한다.

    Args:
        row: 기존 또는 신규 corpProfile 행.

    Returns:
        누락 필드와 row version을 채운 canonical 행.

    Raises:
        없음.

    Example:
        >>> normalizeCorpProfileRow({"corp_code": "A"})["profileSchemaVersion"]
        1
    """

    versionValue = row.get("profileSchemaVersion", 1)
    try:
        version = int(versionValue or 1)
    except (TypeError, ValueError):
        version = 1
    normalized: dict[str, str | int] = {}
    for column in CORP_PROFILE_SCHEMA:
        if column != "profileSchemaVersion":
            normalized[column] = str(row.get(column, "") or "")
    normalized["profileSchemaVersion"] = version
    return normalized


def _profilePath() -> Path:
    from dartlab.core.dataLoader import _dataDir

    return Path(_dataDir("scan")) / "corpProfile.parquet"


def _loadFiscalMonthMap() -> dict[str, int]:
    """profile의 결산월을 읽되 선택 artifact의 정상 부재는 빈 보강으로 표현한다."""

    profilePath = _profilePath()
    if not profilePath.exists():
        return {}
    try:
        frame = pl.scan_parquet(profilePath).select("stockCode", "acc_mt").collect(engine="streaming")
    except (pl.exceptions.PolarsError, OSError):
        return {}

    result: dict[str, int] = {}
    for stockCode, accMt in frame.iter_rows():
        if not stockCode or not accMt:
            continue
        try:
            month = int(str(accMt).replace("월", "").strip())
        except (TypeError, ValueError, AttributeError):
            continue
        if 1 <= month <= 12:
            result[stockCode] = month
    return result


def _loadJurirStockMap(profilePath: Path | None = None) -> dict[str, str]:
    """완료된 v2 profile의 법인등록번호를 상장 종목코드로 strict하게 연결한다."""

    profilePath = profilePath or _profilePath()
    if not profilePath.exists():
        raise CorpProfileIdentityError(f"corpProfile identity artifact 부재: {profilePath}")
    try:
        lazy = pl.scan_parquet(profilePath)
        actualSchema = lazy.collect_schema()
        if actualSchema != CORP_PROFILE_SCHEMA:
            raise CorpProfileIdentityError(
                f"corpProfile identity schema 불일치: {actualSchema}. buildCorpProfile backfill이 필요합니다"
            )
        profile = lazy.select(
            "stockCode",
            "jurir_no",
            "profileSchemaVersion",
        ).collect(engine="streaming")
    except CorpProfileIdentityError:
        raise
    except (pl.exceptions.PolarsError, OSError) as exc:
        raise CorpProfileIdentityError(f"corpProfile identity read 실패: {profilePath}") from exc

    incomplete = profile.filter(
        pl.col("profileSchemaVersion").is_null() | (pl.col("profileSchemaVersion") < CORP_PROFILE_SCHEMA_VERSION)
    )
    if not incomplete.is_empty():
        sample = incomplete["stockCode"].head(10).to_list()
        raise CorpProfileIdentityError(
            f"corpProfile identity backfill 미완료: rows={incomplete.height}, sample={sample}"
        )

    jurirToCode: dict[str, str] = {}
    for stockCode, jurirNo, _ in profile.iter_rows():
        normalized = normalizeJurirNo(jurirNo)
        if not stockCode or normalized is None:
            continue
        prior = jurirToCode.get(normalized)
        if prior is not None and prior != stockCode:
            raise CorpProfileIdentityError(
                f"corpProfile 법인등록번호 충돌: jurirNo={normalized}, stockCodes={prior},{stockCode}"
            )
        jurirToCode[normalized] = stockCode
    if not jurirToCode:
        raise CorpProfileIdentityError(f"corpProfile에 유효한 법인등록번호가 없습니다: {profilePath}")
    return jurirToCode
