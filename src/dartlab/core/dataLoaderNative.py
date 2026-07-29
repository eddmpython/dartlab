"""Native parquet·IPC 선택, 검증, 손상 복구."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import polars as pl

from dartlab.core.dataLoaderContract import DataArtifactError, collectLazyQuery
from dartlab.core.logger import getLogger

_log = getLogger(__name__)
_READ_ERRORS = (OSError, pl.exceptions.PolarsError)


def validateParquetArtifact(path: Path) -> None:
    """Canonical 확정 전에 모든 parquet batch를 bounded memory로 decode한다."""
    try:
        frame = pl.scan_parquet(str(path))
        schema = frame.collect_schema()
        if not schema:
            raise ValueError("schema가 비어 있습니다")
        for batch in frame.collect_batches(chunk_size=65_536, engine="streaming"):
            del batch
    except MemoryError:
        raise
    except (OSError, ValueError, pl.exceptions.PolarsError) as exc:
        raise DataArtifactError("무결성 검증", path, exc) from exc


def readNativeWithRecovery(
    stockCode: str,
    path: Path,
    category: str,
    *,
    sinceYear: int | None,
    refresh: str,
    columns: list[str] | None,
    predicate: pl.Expr | None,
    reacquire: Callable[[], None],
) -> pl.DataFrame:
    """Canonical 손상을 구분해 network 허용 시 정확히 한 번 재조달한다."""
    try:
        return _readNativeFrame(
            stockCode,
            path,
            category,
            sinceYear=sinceYear,
            columns=columns,
            predicate=predicate,
        )
    except _READ_ERRORS as firstError:
        if not _isCanonicalArtifactFailure(path):
            raise
        if refresh == "local_only":
            _discardCanonicalArtifact(path, prior=firstError)
            firstError.add_note("손상된 local_only cache를 무효화했으며 network 재조달은 수행하지 않았습니다")
            raise

        _log.warning(
            "canonical parquet 손상으로 1회 재조달합니다 (category=%s, stockCode=%s, error=%s)",
            category,
            stockCode,
            type(firstError).__name__,
        )
        _discardCanonicalArtifact(path, prior=firstError)
        try:
            reacquire()
        except Exception as recoveryError:
            recoveryError.add_note(f"최초 parquet 읽기 실패: {type(firstError).__name__}: {firstError}")
            raise
        try:
            return _readNativeFrame(
                stockCode,
                path,
                category,
                sinceYear=sinceYear,
                columns=columns,
                predicate=predicate,
            )
        except _READ_ERRORS as retryError:
            retryError.add_note(f"최초 parquet 읽기 실패: {type(firstError).__name__}: {firstError}")
            if _isCanonicalArtifactFailure(path):
                _discardCanonicalArtifact(path, prior=retryError)
            raise


def _readNativeFrame(
    stockCode: str,
    path: Path,
    category: str,
    *,
    sinceYear: int | None,
    columns: list[str] | None,
    predicate: pl.Expr | None,
) -> pl.DataFrame:
    """최신 IPC mirror를 우선하되 canonical parquet을 단일 fallback으로 둔다."""
    ipcPath = _freshIpcMirror(path, stockCode=stockCode, category=category)
    if ipcPath is None:
        return _readParquetFrame(path, sinceYear=sinceYear, columns=columns, predicate=predicate)
    try:
        return _readIpcFrame(ipcPath, sinceYear=sinceYear, columns=columns, predicate=predicate)
    except MemoryError:
        raise
    except Exception as ipcError:
        try:
            frame = _readParquetFrame(path, sinceYear=sinceYear, columns=columns, predicate=predicate)
        except MemoryError:
            raise
        except Exception as parquetError:
            parquetError.add_note(f"IPC mirror 읽기 실패: {type(ipcError).__name__}: {ipcError}")
            raise
        _log.warning(
            "IPC mirror 읽기 실패로 canonical parquet을 사용합니다 (category=%s, stockCode=%s, error=%s)",
            category,
            stockCode,
            type(ipcError).__name__,
        )
        _discardIpcMirror(ipcPath, prior=ipcError)
        return frame


def _readIpcFrame(
    path: Path,
    *,
    sinceYear: int | None,
    columns: list[str] | None,
    predicate: pl.Expr | None,
) -> pl.DataFrame:
    if sinceYear is None and columns is None and predicate is None:
        return pl.read_ipc(str(path), memory_map=True)
    return collectLazyQuery(
        pl.scan_ipc(str(path), memory_map=True),
        sinceYear=sinceYear,
        columns=columns,
        predicate=predicate,
    )


def _readParquetFrame(
    path: Path,
    *,
    sinceYear: int | None,
    columns: list[str] | None,
    predicate: pl.Expr | None,
) -> pl.DataFrame:
    if sinceYear is None and columns is None and predicate is None:
        return pl.read_parquet(str(path))
    return collectLazyQuery(
        pl.scan_parquet(str(path)),
        sinceYear=sinceYear,
        columns=columns,
        predicate=predicate,
    )


def _freshIpcMirror(path: Path, *, stockCode: str, category: str) -> Path | None:
    ipcPath = path.with_suffix(".arrow")
    try:
        if not ipcPath.is_file() or ipcPath.stat().st_mtime < path.stat().st_mtime:
            return None
    except OSError as exc:
        _log.warning("IPC mirror freshness 확인 실패로 parquet을 사용합니다 (%s: %s)", type(exc).__name__, exc)
        return None

    try:
        canonicalSchema = pl.read_parquet_schema(str(path))
    except MemoryError:
        raise
    except (OSError, ValueError, pl.exceptions.PolarsError) as canonicalError:
        try:
            pl.read_ipc_schema(str(ipcPath))
        except MemoryError:
            raise
        except (OSError, ValueError, pl.exceptions.PolarsError) as ipcError:
            canonicalError.add_note(f"IPC mirror schema 확인 실패: {type(ipcError).__name__}: {ipcError}")
        _log.warning(
            "canonical schema 확인 실패로 IPC mirror를 사용하지 않습니다 (category=%s, stockCode=%s, error=%s)",
            category,
            stockCode,
            type(canonicalError).__name__,
        )
        raise
    try:
        ipcSchema = pl.read_ipc_schema(str(ipcPath))
    except MemoryError:
        raise
    except (OSError, ValueError, pl.exceptions.PolarsError) as exc:
        _log.warning(
            "IPC mirror schema 확인 실패로 canonical parquet을 사용합니다 (category=%s, stockCode=%s, error=%s)",
            category,
            stockCode,
            type(exc).__name__,
        )
        _discardIpcMirror(ipcPath, prior=exc)
        return None
    if ipcSchema != canonicalSchema:
        mismatch = ValueError(f"IPC={ipcSchema!r}, canonical={canonicalSchema!r}")
        _log.warning(
            "IPC mirror schema 불일치로 canonical parquet을 사용합니다 (category=%s, stockCode=%s)",
            category,
            stockCode,
        )
        _discardIpcMirror(ipcPath, prior=mismatch)
        return None
    return ipcPath


def _discardIpcMirror(path: Path, *, prior: BaseException) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError as cleanupError:
        _log.warning(
            "손상 IPC mirror 무효화 실패 (%s, prior=%s): %s",
            path,
            type(prior).__name__,
            cleanupError,
        )


def _isCanonicalArtifactFailure(path: Path) -> bool:
    try:
        validateParquetArtifact(path)
    except DataArtifactError:
        return True
    return False


def _discardCanonicalArtifact(path: Path, *, prior: BaseException) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError as cleanupError:
        error = DataArtifactError("손상 cache 정리", path, cleanupError)
        error.add_note(f"선행 읽기 실패: {type(prior).__name__}: {prior}")
        raise error from cleanupError
    for sidecar in (path.with_suffix(".parquet.etag"), path.with_suffix(".arrow")):
        try:
            sidecar.unlink(missing_ok=True)
        except OSError as cleanupError:
            _log.warning(
                "손상 cache sidecar 정리 실패 (%s, prior=%s): %s",
                sidecar,
                type(prior).__name__,
                cleanupError,
            )


__all__ = ["readNativeWithRecovery", "validateParquetArtifact"]
