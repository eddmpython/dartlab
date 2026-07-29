"""Pyodide-specific parquet loading for ``core.dataLoader``."""

from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, cast

import polars as pl

from dartlab.core.dataConfig import DATA_RELEASES, HF_BASE_URL, hfBaseUrl, resolveDataCategory
from dartlab.core.dataLoaderContract import (
    applyEagerQuery,
    projectedColumns,
    validateRefreshPolicy,
    validateShardKey,
)


class PyodideParquetError(OSError):
    """Pyodide parquet 읽기·검증·저장 실패."""

    def __init__(self, operation: str, target: str | Path, cause: BaseException):
        self.operation = operation
        self.target = str(target)
        super().__init__(f"Pyodide parquet {operation} 실패: {self.target} ({type(cause).__name__}: {cause})")


def arrowToPolars(arrowTable) -> pl.DataFrame:
    """pyarrow Table 를 polars DataFrame 으로 (WASM 세이프 3-tier).

    polars WASM wheel 은 pl.from_arrow 가 내부에서 pyarrow 를 lazy import 하다
    실패할 수 있다. from_arrow 우선, 실패 시 polars.dependencies 에 pyarrow 를
    직접 주입 후 재시도, 최후에는 to_pydict 전량 복제로 강등한다.
    readParquetSafe 와 loadDataPyodide 가 공유하는 변환 SSOT.
    """
    try:
        return cast(pl.DataFrame, pl.from_arrow(arrowTable))
    except (ModuleNotFoundError, ImportError):
        import importlib

        import pyarrow as _pa  # noqa: F811

        try:
            _pdeps = cast(Any, importlib.import_module("polars.dependencies"))

            lazyImport = getattr(_pdeps, "_lazy_import", None)
            cacheClear = getattr(lazyImport, "cache_clear", None)
            if callable(cacheClear):
                cacheClear()
            setattr(_pdeps, "pyarrow", _pa)
        except (AttributeError, TypeError):
            pass
        try:
            return cast(pl.DataFrame, pl.from_arrow(arrowTable))
        except (ModuleNotFoundError, ImportError):
            return pl.DataFrame(arrowTable.to_pydict())


@contextmanager
def openParquetFile(source: str | Path | bytes | bytearray | memoryview) -> Iterator[Any]:
    """경로는 seekable stream으로, 메모리 payload는 BytesIO로 parquet을 연다."""
    import io

    import pyarrow.parquet as pq

    if isinstance(source, (bytes, bytearray, memoryview)):
        with io.BytesIO(source) as stream:
            yield pq.ParquetFile(stream)
        return

    with Path(source).open("rb") as stream:
        yield pq.ParquetFile(stream)


def readParquetFrame(
    source: str | Path | bytes | bytearray | memoryview,
    *,
    columns: list[str] | None = None,
) -> pl.DataFrame:
    """Pyodide parquet을 projection read한 뒤 Polars로 변환한다."""
    with openParquetFile(source) as parquet:
        return arrowToPolars(parquet.read(columns=columns))


def loadDataPyodide(
    stockCode: str,
    category: str,
    *,
    sinceYear: int | None = None,
    asOf: str | None = None,
    refresh: str = "auto",
    columns: list[str] | None = None,
    predicate: pl.Expr | None = None,
) -> pl.DataFrame:
    """Pyodide 환경에서 HF cache parquet을 무결성 복구와 projection으로 읽는다."""
    import pyarrow as pa

    category = resolveDataCategory(category)
    validateShardKey(stockCode)
    validateRefreshPolicy(category, refresh, pyodide=True)
    dirPath = DATA_RELEASES[category]["dir"]
    path = _dataPath(stockCode, dirPath)
    downloadAllowed = refresh != "local_only"
    refreshAllowed = downloadAllowed and os.environ.get("DARTLAB_NO_REFRESH") != "1"
    fetched = False

    if not path.exists():
        if not downloadAllowed:
            raise FileNotFoundError(f"Pyodide 로컬 parquet 없음: {path}")
        pyodideFetchToFS(stockCode, category, dirPath, path)
        fetched = True
    elif refresh == "force_check" and refreshAllowed:
        pyodideFetchToFS(stockCode, category, dirPath, path)
        fetched = True

    try:
        df = _readDataFrame(
            path,
            category=category,
            sinceYear=sinceYear,
            asOf=asOf,
            columns=columns,
            predicate=predicate,
        )
    except MemoryError:
        raise
    except (OSError, pa.ArrowInvalid) as exc:
        if fetched:
            _discardCorruptCache(path, prior=exc)
            raise PyodideParquetError("읽기", path, exc) from exc
        if not downloadAllowed:
            _discardCorruptCache(path, prior=exc)
            raise PyodideParquetError("읽기", path, exc) from exc
        try:
            pyodideFetchToFS(stockCode, category, dirPath, path)
            fetched = True
        except MemoryError:
            raise
        except (RuntimeError, OSError) as fetchExc:
            _discardCorruptCache(path, prior=fetchExc)
            error = PyodideParquetError("손상 cache 재조달", path, fetchExc)
            error.add_note(f"최초 읽기 실패: {type(exc).__name__}: {exc}")
            raise error from fetchExc
        try:
            df = _readDataFrame(
                path,
                category=category,
                sinceYear=sinceYear,
                asOf=asOf,
                columns=columns,
                predicate=predicate,
            )
        except MemoryError:
            raise
        except (OSError, pa.ArrowInvalid) as retryExc:
            _discardCorruptCache(path, prior=retryExc)
            error = PyodideParquetError("손상 cache 재조달", path, retryExc)
            error.add_note(f"최초 읽기 실패: {type(exc).__name__}: {exc}")
            raise error from retryExc
        except pa.ArrowException as retryExc:
            error = PyodideParquetError("재조달 후 읽기", path, retryExc)
            error.add_note(f"최초 읽기 실패: {type(exc).__name__}: {exc}")
            raise error from retryExc
    except pa.ArrowException as exc:
        raise PyodideParquetError("읽기", path, exc) from exc

    if category == "edgarDocs" and asOf is not None and not _isFreshAsOf(df, asOf):
        if fetched or not refreshAllowed:
            cause = ValueError(f"최신 filing_date가 요청 asOf {asOf}에 미달")
            raise PyodideParquetError("asOf 신선도 검증", path, cause) from cause
        pyodideFetchToFS(stockCode, category, dirPath, path)
        try:
            df = _readDataFrame(
                path,
                category=category,
                sinceYear=sinceYear,
                asOf=asOf,
                columns=columns,
                predicate=predicate,
            )
        except MemoryError:
            raise
        except (OSError, pa.ArrowInvalid) as exc:
            _discardCorruptCache(path, prior=exc)
            raise PyodideParquetError("asOf 재조달 후 읽기", path, exc) from exc
        except pa.ArrowException as exc:
            raise PyodideParquetError("asOf 재조달 후 읽기", path, exc) from exc
        if not _isFreshAsOf(df, asOf):
            cause = ValueError(f"HF snapshot의 최신 filing_date가 요청 asOf {asOf}에 미달")
            raise PyodideParquetError("asOf 신선도 검증", path, cause) from cause

    df = applyEagerQuery(
        df,
        sinceYear=sinceYear,
        columns=columns,
        predicate=predicate,
    )

    from dartlab.core.dataLoaderNormalize import normalizeLoadedFrame

    return normalizeLoadedFrame(df, category)


def _dataPath(stockCode: str, dirPath: str) -> Path:
    """Pyodide 가 공유하는 고정 데이터 cache 경로를 만든다."""
    return Path(f"/data/{dirPath}/{stockCode}.parquet")


def _discardCorruptCache(path: Path, *, prior: BaseException) -> None:
    """손상 판정 cache를 제거하고 정리 실패도 원인과 함께 드러낸다."""
    try:
        path.unlink(missing_ok=True)
    except OSError as cleanupExc:
        error = PyodideParquetError("손상 cache 정리", path, cleanupExc)
        error.add_note(f"선행 읽기 실패: {type(prior).__name__}: {prior}")
        raise error from cleanupExc


def _readDataFrame(
    path: Path,
    *,
    category: str,
    sinceYear: int | None,
    asOf: str | None,
    columns: list[str] | None,
    predicate: pl.Expr | None,
) -> pl.DataFrame:
    """필터 보조열을 포함한 최소 projection으로 로컬 parquet을 읽는다."""
    with openParquetFile(path) as parquet:
        schemaNames = parquet.schema_arrow.names
        projected = _projectedColumns(
            schemaNames,
            category=category,
            sinceYear=sinceYear,
            asOf=asOf,
            columns=columns,
            predicate=predicate,
        )
        return arrowToPolars(parquet.read(columns=projected))


def _projectedColumns(
    schemaNames: list[str],
    *,
    category: str,
    sinceYear: int | None,
    asOf: str | None,
    columns: list[str] | None,
    predicate: pl.Expr | None,
) -> list[str] | None:
    """최종 반환열과 필터 보조열을 합쳐 parquet projection을 만든다."""
    return projectedColumns(
        schemaNames,
        category=category,
        sinceYear=sinceYear,
        asOf=asOf,
        columns=columns,
        predicate=predicate,
    )


def _isFreshAsOf(df: pl.DataFrame, asOf: str) -> bool:
    """EDGAR frame이 요청 asOf 이상의 filing을 포함하는지 판정한다."""
    if "filing_date" not in df.columns or df.is_empty():
        return False
    latest = df.select(pl.col("filing_date").cast(pl.String, strict=False).drop_nulls().max()).item()
    return latest is not None and str(latest) >= asOf


def pyodideFetchScanLite(dataDirForCategory) -> None:
    """Pyodide: scan 경량 프리빌드(`finance-lite.parquet`)만 받아 FS에 저장."""
    from dartlab.core.messaging import emit

    scanDir = Path(dataDirForCategory("scan"))
    scanDir.mkdir(parents=True, exist_ok=True)
    dest = scanDir / "finance-lite.parquet"

    try:
        pyodideFetchToFS("finance-lite", "scan", "dart/scan", dest)
    except (RuntimeError, OSError) as exc:
        emit("scan:prebuild_failed", error=str(exc))
        raise

    if not dest.exists() or dest.stat().st_size < 1024 * 1024:
        emit(
            "scan:prebuild_incomplete",
            missing=["finance-lite.parquet (수신 실패 또는 1MB 미만)"],
        )
        raise RuntimeError("scan finance-lite 수신 실패. 네트워크/HF 응답 확인 후 재시도하세요.")

    sizeMb = dest.stat().st_size / 1024 / 1024
    emit("scan:prebuild_ready_lite", sizeStr=f"{sizeMb:.1f}MB")


def _decodeUserDefined(text: str) -> bytes:
    """x-user-defined 로 받은 응답 텍스트 → 원본 바이트.

    그 charset 은 바이트 0x00~0xFF 를 코드포인트 U+0000~U+00FF / U+F780~U+F7FF 로 1:1 사상하므로
    하위 8비트만 취하면 원본이다. 옛 구현은 ``bytes(ord(c) & 0xFF for c in text)`` 로 문자마다 파이썬을
    돌았고, 12.8MB panel 보드에서만 1,300 만 회라 수 초를 먹었다. 문자열을 UTF-16LE 로 한 번 인코딩하면
    (C 레벨) 문자당 2바이트 배열이 되고, numpy 로 하위 바이트만 벡터로 뽑는다. 결과는 byte-identical.
    numpy 부재 등 예외 시 옛 루프로 폴백한다(정확성 우선).
    """
    try:
        import numpy as _np

        codes = _np.frombuffer(text.encode("utf-16-le"), dtype="<u2")
        return codes.astype(_np.uint8).tobytes()
    except (ImportError, ModuleNotFoundError, AttributeError, TypeError, ValueError, UnicodeError):
        return bytes(ord(c) & 0xFF for c in text)


def _fetchBytesPyodide(url: str, *, allowOpenUrl: bool = False) -> bytes:
    """브라우저에서 URL 하나를 바이트로 받는다. tier 를 순서대로 시도한다.

    tier 1 (opportunistic): JSPI stack-switching 되는 브라우저(Chrome 137+)면 sync 로
    async fetch. tier 2 (reliable): 동기 XMLHttpRequest. 웹워커에서 항상 동작한다
    (webloop 실행 중이라 run_until_complete 경로는 죽어 제거함). 동기 XHR 은 arraybuffer 를
    못 받으므로 텍스트로 받아 바이트로 되돌린다. charset 은 x-user-defined 여야 무손실이다
    (iso-8859-1 라벨은 브라우저가 windows-1252 로 해석해 0x8A 가 U+0160 이 되고 latin-1
    인코딩이 깨진다. 실측 확인). tier 3 (optional): ``open_url``. HTTP status 를 검사하지
    않아 404 본문을 그대로 돌려주므로, 호출부가 parquet magic 으로 걸러낼 때만 켠다.

    이 사슬이 두 함수에 통째로 복붙돼 있었고 양쪽 다 tier 별 실패 사유를 버렸다. 그래서
    브라우저에서 데이터가 안 나올 때 CORS 인지 404 인지 JSPI 미지원인지 구분할 방법이
    없었다. 이제 사유를 모아 예외 메시지에 싣는다. 브라우저는 붙어서 디버깅하기 어려운
    자리라 이 정보가 유일한 단서다.

    Raises:
        RuntimeError: 모든 tier 실패. 메시지에 tier 별 사유가 줄 단위로 들어간다.
    """
    reasons: list[str] = []

    try:
        from pyodide.ffi import run_sync  # type: ignore[import-not-found]
        from pyodide.http import pyfetch  # type: ignore[import-not-found]

        resp = run_sync(pyfetch(url))
        if resp.status == 200:
            return bytes(run_sync(resp.bytes()))
        reasons.append(f"pyfetch: HTTP {resp.status}")
    except MemoryError:
        raise
    except Exception as exc:  # noqa: BLE001
        reasons.append(f"pyfetch: {type(exc).__name__}: {exc}")

    try:
        from js import XMLHttpRequest  # type: ignore[import-not-found]

        xhr = XMLHttpRequest.new()
        xhr.open("GET", url, False)
        xhr.overrideMimeType("text/plain; charset=x-user-defined")
        xhr.send()
        if xhr.status == 200:
            return _decodeUserDefined(xhr.responseText)
        reasons.append(f"XHR: HTTP {xhr.status}")
    except MemoryError:
        raise
    except Exception as exc:  # noqa: BLE001
        reasons.append(f"XHR: {type(exc).__name__}: {exc}")

    if allowOpenUrl:
        try:
            from pyodide.http import open_url  # type: ignore[import-not-found]

            raw = open_url(url).read()
            return raw.encode("latin-1") if isinstance(raw, str) else raw
        except MemoryError:
            raise
        except Exception as exc:  # noqa: BLE001
            reasons.append(f"open_url: {type(exc).__name__}: {exc}")

    raise RuntimeError("Pyodide fetch 실패: " + url + "\n  " + "\n  ".join(reasons))


def loadCorpListPyodide() -> pl.DataFrame:
    """Pyodide: HF ``metadata/corpList.parquet`` (gov 발행 상장사 목록)을 직독한다.

    브라우저에서 KRX API(``kind.krx.co.kr``)는 CORS 로 막혀 회사명↔종목코드 해석이 죽는다.
    같은 목록이 gov 축으로 HF 에 발행돼 있으므로(회사명·종목코드 포함) 그걸 직독해 노트북에서도
    ``Company("삼성전자")`` 이름 해석이 되게 한다. fetch 는 데이터 로더와 동일한 tier(JSPI pyfetch →
    동기 XHR + ``_decodeUserDefined``) 를 쓴다. 실패 시 예외를 던져 호출부가 빈 목록으로 저하한다.
    """
    import pyarrow as pa

    url = f"{HF_BASE_URL}/metadata/corpList.parquet"
    try:
        return readParquetFrame(_fetchBytesPyodide(url))
    except MemoryError:
        raise
    except (OSError, pa.ArrowException) as exc:
        raise PyodideParquetError("회사 목록 읽기", url, exc) from exc


def pyodideFetchToFS(stockCode: str, category: str, dirPath: str, path: Path) -> None:
    """Pyodide: HF에서 parquet을 fetch하여 FS에 저장."""
    url = f"{hfBaseUrl(category)}/{stockCode}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        buf = _fetchBytesPyodide(url, allowOpenUrl=True)
    except RuntimeError as exc:
        raise RuntimeError(
            f"{exc}\n"
            "데이터를 수동으로 로드하세요:\n"
            "  from pyodide.http import pyfetch\n"
            f"  resp = await pyfetch('{url}')\n"
            f"  buf = await resp.bytes()\n"
            f"  import os; os.makedirs('/data/{dirPath}', exist_ok=True)\n"
            f"  open('/data/{dirPath}/{stockCode}.parquet', 'wb').write(buf)"
        ) from exc

    # open_url tier 는 HTTP status 를 검사하지 않으므로 magic을 먼저 확인하고, 임시 파일의 footer와
    # column chunk 경계까지 검증한 뒤에만 최종 cache를 원자 교체한다.
    if len(buf) < 8 or buf[:4] != b"PAR1" or buf[-4:] != b"PAR1":
        cause = ValueError(f"size={len(buf)}, head={buf[:4]!r}")
        raise PyodideParquetError("다운로드 형식 검증", url, cause) from cause

    _storeParquetAtomic(buf, path, url=url)


def _storeParquetAtomic(buf: bytes, path: Path, *, url: str) -> None:
    """다운로드 payload를 임시 파일에서 구조 검증한 뒤 최종 경로로 교체한다."""
    import pyarrow as pa

    tmp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as stream:
            tmp = Path(stream.name)
            written = stream.write(buf)
            if written != len(buf):
                raise OSError(f"부분 쓰기: {written}/{len(buf)} bytes")
        _validateParquetStructure(tmp)
        tmp.replace(path)
    except MemoryError as exc:
        if tmp is not None:
            try:
                tmp.unlink(missing_ok=True)
            except OSError as cleanupExc:
                exc.add_note(
                    f"Pyodide parquet OOM 후 임시 파일 정리 실패: {tmp} ({type(cleanupExc).__name__}: {cleanupExc})"
                )
        raise
    except (OSError, pa.ArrowException, ValueError) as exc:
        try:
            if tmp is not None:
                tmp.unlink(missing_ok=True)
        except OSError as cleanupExc:
            error = PyodideParquetError("임시 파일 정리", tmp or path.parent, cleanupExc)
            error.add_note(f"선행 저장 실패: {type(exc).__name__}: {exc}")
            raise error from cleanupExc
        raise PyodideParquetError("다운로드 저장 검증", url, exc) from exc


def _validateParquetStructure(path: Path) -> None:
    """footer와 모든 column chunk가 실제 파일 경계 안에 있는지 확인한다."""
    size = path.stat().st_size
    with openParquetFile(path) as parquet:
        metadata = parquet.metadata
        footerStart = size - 8 - metadata.serialized_size
        if footerStart < 4:
            raise ValueError(f"잘못된 parquet footer 경계: {footerStart}")
        for rowGroupIndex in range(metadata.num_row_groups):
            rowGroup = metadata.row_group(rowGroupIndex)
            for columnIndex in range(rowGroup.num_columns):
                column = rowGroup.column(columnIndex)
                offsets = [
                    offset
                    for offset in (column.dictionary_page_offset, column.data_page_offset)
                    if offset is not None and offset >= 0
                ]
                start = min(offsets) if offsets else column.file_offset
                end = start + column.total_compressed_size
                if start < 4 or end > footerStart:
                    raise ValueError(
                        f"column chunk 경계 초과: {column.path_in_schema} [{start}, {end}) > footer {footerStart}"
                    )


__all__ = [
    "PyodideParquetError",
    "arrowToPolars",
    "loadDataPyodide",
    "openParquetFile",
    "pyodideFetchScanLite",
    "pyodideFetchToFS",
    "readParquetFrame",
]
