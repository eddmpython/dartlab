"""Pyodide-specific parquet loading for ``core.dataLoader``."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.core.dataConfig import DATA_RELEASES, hfBaseUrl


def arrowToPolars(arrowTable) -> pl.DataFrame:
    """pyarrow Table 를 polars DataFrame 으로 (WASM 세이프 3-tier).

    polars WASM wheel 은 pl.from_arrow 가 내부에서 pyarrow 를 lazy import 하다
    실패할 수 있다. from_arrow 우선, 실패 시 polars.dependencies 에 pyarrow 를
    직접 주입 후 재시도, 최후에는 to_pydict 전량 복제로 강등한다.
    readParquetSafe 와 loadDataPyodide 가 공유하는 변환 SSOT.
    """
    try:
        return pl.from_arrow(arrowTable)
    except (ModuleNotFoundError, ImportError):
        import pyarrow as _pa  # noqa: F811

        try:
            import polars.dependencies as _pdeps

            _pdeps._lazy_import.cache_clear() if hasattr(_pdeps._lazy_import, "cache_clear") else None
            _pdeps.pyarrow = _pa  # type: ignore[attr-defined]
        except (AttributeError, TypeError):
            pass
        try:
            return pl.from_arrow(arrowTable)
        except (ModuleNotFoundError, ImportError):
            return pl.DataFrame(arrowTable.to_pydict())


def loadDataPyodide(
    stockCode: str,
    category: str,
    *,
    sinceYear: int | None = None,
    columns: list[str] | None = None,
) -> pl.DataFrame:
    """Pyodide 환경: pre-fetched FS 파일 → pyarrow → polars."""
    import io

    import pyarrow.parquet as pq

    dirPath = DATA_RELEASES[category]["dir"]
    path = Path(f"/data/{dirPath}/{stockCode}.parquet")

    if not path.exists():
        pyodideFetchToFS(stockCode, category, dirPath, path)

    arrowTable = pq.read_table(io.BytesIO(path.read_bytes()))
    df = arrowToPolars(arrowTable)

    if sinceYear is not None:
        for colName in ("year", "bsns_year"):
            if colName in df.columns:
                yearCol = pl.col(colName)
                if df.schema[colName] == pl.Utf8:
                    yearCol = yearCol.cast(pl.Int32, strict=False)
                df = df.filter(yearCol >= sinceYear)
                break

    if columns:
        available = [c for c in columns if c in df.columns]
        if available:
            df = df.select(available)

    from dartlab.core.dataLoaderNormalize import normalizeLoadedFrame

    return normalizeLoadedFrame(df, category)


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
    emit("scan:prebuild_ready", fileCount=f"{sizeMb:.1f}MB (finance-lite)")


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
        return (codes & 0xFF).astype(_np.uint8).tobytes()
    except Exception:  # noqa: BLE001 (numpy 부재/메모리 등: 느리지만 정확한 경로)
        return bytes(ord(c) & 0xFF for c in text)


def pyodideFetchToFS(stockCode: str, category: str, dirPath: str, path: Path) -> None:
    """Pyodide: HF에서 parquet을 fetch하여 FS에 저장."""
    url = f"{hfBaseUrl(category)}/{stockCode}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)

    buf = None

    # tier 1 (opportunistic): JSPI stack-switching 되는 브라우저(Chrome 137+)면 sync 로 async fetch.
    try:
        from pyodide.ffi import run_sync  # type: ignore[import-not-found]
        from pyodide.http import pyfetch  # type: ignore[import-not-found]

        resp = run_sync(pyfetch(url))
        if resp.status == 200:
            buf = bytes(run_sync(resp.bytes()))
    except Exception:
        pass

    # tier 2 (reliable): 동기 XMLHttpRequest. 웹워커에서 항상 동작(webloop 실행 중이라 run_until_complete
    # 경로는 죽어 제거함). 동기 XHR 은 arraybuffer 를 못 받으므로 텍스트로 받아 바이트로 되돌린다.
    # charset 은 x-user-defined 여야 무손실이다(iso-8859-1 라벨은 브라우저가 windows-1252 로 해석해
    # 0x8A 가 U+0160 이 되고 latin-1 인코딩이 깨진다. 실측 확인).
    if buf is None:
        try:
            from js import XMLHttpRequest  # type: ignore[import-not-found]

            xhr = XMLHttpRequest.new()
            xhr.open("GET", url, False)
            xhr.overrideMimeType("text/plain; charset=x-user-defined")
            xhr.send()
            if xhr.status == 200:
                buf = _decodeUserDefined(xhr.responseText)
        except Exception:
            pass

    if buf is None:
        try:
            from pyodide.http import open_url  # type: ignore[import-not-found]

            resp = open_url(url)
            raw = resp.read()
            buf = raw.encode("latin-1") if isinstance(raw, str) else raw
        except Exception:
            pass

    if buf is None:
        raise RuntimeError(
            f"Pyodide fetch 실패: {url}\n"
            "데이터를 수동으로 로드하세요:\n"
            "  from pyodide.http import pyfetch\n"
            f"  resp = await pyfetch('{url}')\n"
            f"  buf = await resp.bytes()\n"
            "  import os; os.makedirs('/data/{dirPath}', exist_ok=True)\n"
            f"  open('/data/{dirPath}/{stockCode}.parquet', 'wb').write(buf)"
        )

    # open_url tier 는 HTTP status 를 검사하지 않아 404 등의 에러 본문(HTML/JSON)을 buf 로 반환할 수 있다.
    # 그 garbage 를 FS 에 쓰면 이후 pyarrow read_table 이 ArrowInvalid(ValueError)로 크래시하는데,
    # 호출부(readLong)의 except 가 그걸 못 잡아 c.panel 까지 전파된다. parquet magic(PAR1 head+tail)으로
    # 거부해 부재/404 를 RuntimeError 로 승격 → 호출부가 graceful(빈 결과)로 저하하게 한다.
    if len(buf) < 8 or buf[:4] != b"PAR1" or buf[-4:] != b"PAR1":
        raise RuntimeError(f"Pyodide fetch: parquet 아님 (부재/404 의심): {url} (size={len(buf)}, head={buf[:4]!r})")

    path.write_bytes(buf)


__all__ = ["arrowToPolars", "loadDataPyodide", "pyodideFetchScanLite", "pyodideFetchToFS"]
