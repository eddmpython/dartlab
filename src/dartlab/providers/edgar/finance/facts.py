"""EDGAR companyfacts의 명시적 local-only owner reader."""

from __future__ import annotations

import hashlib
import io
from collections.abc import Sequence

import polars as pl

EDGAR_FINANCIAL_FEATURE_COLUMNS = (
    "namespace",
    "tag",
    "unit",
    "val",
    "form",
    "filed",
    "start",
    "end",
    "accn",
)


def readCompanyFactsLocal(
    cik: str,
    *,
    columns: Sequence[str] = EDGAR_FINANCIAL_FEATURE_COLUMNS,
    sourcePayload: bytes | None = None,
    expectedIntegrityDigest: str | None = None,
) -> pl.DataFrame:
    """네트워크와 refresh 없이 현재 로컬 EDGAR companyfacts shard를 읽는다.

    Args:
        cik: SEC CIK. 숫자 문자열은 10자리로 정규화한다.
        columns: 반환할 필수 column 이름.
        sourcePayload: Resource manifest digest를 검증할 때 읽은 동일 parquet bytes.
        expectedIntegrityDigest: ``sourcePayload``의 pinned full-file SHA-256.

    Returns:
        요청 column만 가진 한 회사의 companyfacts DataFrame.

    Raises:
        ValueError: CIK, column 또는 verified payload 계약이 잘못된 경우.
        FileNotFoundError: 현재 runtime에 local shard가 없는 경우.

    Example:
        ``facts = readCompanyFactsLocal("0000320193")``
    """

    normalizedCik = str(cik).strip()
    if not normalizedCik.isdigit():
        raise ValueError("EDGAR CIK는 숫자여야 합니다")
    normalizedCik = normalizedCik.zfill(10)
    requested = tuple(columns)
    if not requested or len(set(requested)) != len(requested) or any(type(item) is not str for item in requested):
        raise ValueError("EDGAR companyfacts columns가 유효하지 않습니다")
    if (sourcePayload is None) != (expectedIntegrityDigest is None):
        raise ValueError("EDGAR verified source payload와 digest는 함께 지정해야 합니다")
    if sourcePayload is not None:
        if type(sourcePayload) is not bytes or not sourcePayload:
            raise ValueError("EDGAR verified source payload가 유효하지 않습니다")
        if (
            not isinstance(expectedIntegrityDigest, str)
            or hashlib.sha256(sourcePayload).hexdigest() != expectedIntegrityDigest
        ):
            raise ValueError("RESOURCE_SOURCE_DRIFT: EDGAR verified payload digest가 다릅니다")
        sourceBuffer = io.BytesIO(sourcePayload)
        available = set(pl.read_parquet_schema(sourceBuffer))
        missing = tuple(sorted(set(requested) - available))
        if missing:
            raise ValueError(f"EDGAR companyfacts 필수 columns가 없습니다: {missing}")
        sourceBuffer.seek(0)
        return pl.read_parquet(sourceBuffer, columns=list(requested))

    from dartlab.core.dataLoader import _dataDir

    path = _dataDir("edgar") / f"{normalizedCik}.parquet"
    if not path.is_file():
        raise FileNotFoundError(f"local EDGAR companyfacts shard가 없습니다: {normalizedCik}")
    lazy = pl.scan_parquet(path)
    available = set(lazy.collect_schema().names())
    missing = tuple(sorted(set(requested) - available))
    if missing:
        raise ValueError(f"EDGAR companyfacts 필수 columns가 없습니다: {missing}")
    return lazy.select(*requested).collect(engine="streaming")


__all__ = ["EDGAR_FINANCIAL_FEATURE_COLUMNS", "readCompanyFactsLocal"]
