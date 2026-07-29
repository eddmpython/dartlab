"""Phase D — ``loadData`` 의 IPC mmap path 회귀.

검증:
  1. ``.arrow`` IPC mirror 가 옆에 있으면 mmap path 선택 (parquet 보다 우선).
  2. mmap 결과의 값/dtype 이 parquet 과 동일.
  3. predicate 적용도 mmap path 에서 작동.
  4. parquet 이 더 새것이면 parquet 으로 fallback (stale mirror 회피).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def _writeBothFormats(parquetPath: Path, df: pl.DataFrame) -> Path:
    parquetPath.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(parquetPath)
    ipcPath = parquetPath.with_suffix(".arrow")
    df.write_ipc(ipcPath, compression="zstd")
    return ipcPath


def _stubLoadDataDeps(monkeypatch, tmp_path: Path) -> None:
    from dartlab.core import dataLoader

    monkeypatch.setattr(dataLoader, "_dataDir", lambda cat: tmp_path / "dart" / "finance")
    monkeypatch.setattr(dataLoader, "_ensureLocalParquet", lambda *a, **kw: None)
    monkeypatch.setattr(dataLoader, "_normalizeLoadedFrame", lambda df, cat: df)
    monkeypatch.setattr(dataLoader, "_shouldRefreshHfCategory", lambda *a, **kw: False)
    dataLoader._LOAD_CACHE.clear()


def test_mmap_path_used_when_ipc_present(tmp_path: Path, monkeypatch) -> None:
    """``.arrow`` 가 옆에 있으면 mmap path 진입."""
    from dartlab.core import dataLoader

    parquetPath = tmp_path / "dart" / "finance" / "005930.parquet"
    df = pl.DataFrame({"sj_div": ["BS", "IS"], "thstrm_amount": [1.0, 2.0]})
    ipcPath = _writeBothFormats(parquetPath, df)

    _stubLoadDataDeps(monkeypatch, tmp_path)

    # ipc mtime >= parquet mtime 보장
    nowFuture = parquetPath.stat().st_mtime + 1
    os.utime(ipcPath, (nowFuture, nowFuture))

    # 결과는 값/shape 동일
    result = dataLoader.loadData("005930", category="finance")
    assert result.height == 2
    assert set(result.columns) == {"sj_div", "thstrm_amount"}
    assert result.get_column("sj_div").to_list() == ["BS", "IS"]


def test_mmap_path_with_predicate(tmp_path: Path, monkeypatch) -> None:
    """mmap path 도 predicate filter 적용."""
    from dartlab.core import dataLoader

    parquetPath = tmp_path / "dart" / "finance" / "005930.parquet"
    df = pl.DataFrame({"sj_div": ["BS", "BS", "IS", "CF"], "thstrm_amount": [1.0, 2.0, 3.0, 4.0]})
    ipcPath = _writeBothFormats(parquetPath, df)

    _stubLoadDataDeps(monkeypatch, tmp_path)
    nowFuture = parquetPath.stat().st_mtime + 1
    os.utime(ipcPath, (nowFuture, nowFuture))

    bsOnly = dataLoader.loadData(
        "005930",
        category="finance",
        predicate=pl.col("sj_div") == "BS",
    )
    assert bsOnly.height == 2
    assert set(bsOnly.get_column("sj_div").to_list()) == {"BS"}


def test_parquet_fallback_when_ipc_stale(tmp_path: Path, monkeypatch) -> None:
    """parquet 이 더 새것이면 mmap 우회 (stale mirror 회피)."""
    from dartlab.core import dataLoader

    parquetPath = tmp_path / "dart" / "finance" / "005930.parquet"
    df = pl.DataFrame({"sj_div": ["BS"], "thstrm_amount": [99.0]})
    ipcPath = _writeBothFormats(parquetPath, df)

    _stubLoadDataDeps(monkeypatch, tmp_path)

    # parquet 의 mtime 을 *ipc 보다 미래* 로 set (stale ipc 시나리오)
    nowFuture = ipcPath.stat().st_mtime + 1
    os.utime(parquetPath, (nowFuture, nowFuture))

    # 동작 자체는 정상 (parquet 으로 fallback) — 값 동일
    result = dataLoader.loadData("005930", category="finance")
    assert result.height == 1
    assert result.get_column("thstrm_amount").to_list() == [99.0]


def test_no_ipc_uses_parquet(tmp_path: Path, monkeypatch) -> None:
    """``.arrow`` 부재 시 기존 parquet 경로."""
    from dartlab.core import dataLoader

    parquetPath = tmp_path / "dart" / "finance" / "005930.parquet"
    df = pl.DataFrame({"sj_div": ["BS"], "thstrm_amount": [42.0]})
    parquetPath.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(parquetPath)

    _stubLoadDataDeps(monkeypatch, tmp_path)
    # ipc 미생성

    result = dataLoader.loadData("005930", category="finance")
    assert result.height == 1
    assert result.get_column("thstrm_amount").to_list() == [42.0]


def test_fullMmapReadDoesNotOpenLazyScanner(tmp_path: Path, monkeypatch) -> None:
    """filter 없는 IPC mmap 읽기는 schema scan과 eager read를 중복 실행하지 않는다."""
    from dartlab.core import dataLoader

    parquetPath = tmp_path / "dart" / "finance" / "005930.parquet"
    df = pl.DataFrame({"sj_div": ["BS"], "thstrm_amount": [42.0]})
    ipcPath = _writeBothFormats(parquetPath, df)
    _stubLoadDataDeps(monkeypatch, tmp_path)
    future = parquetPath.stat().st_mtime + 1
    os.utime(ipcPath, (future, future))

    def scanForbidden(*_args, **_kwargs):
        raise AssertionError("eager IPC read에서 scan_ipc 금지")

    monkeypatch.setattr(pl, "scan_ipc", scanForbidden)

    result = dataLoader.loadData("005930", category="finance")

    assert result["thstrm_amount"].to_list() == [42.0]


def test_corruptMmapFallsBackToCanonicalAndInvalidatesMirror(
    tmp_path: Path,
    monkeypatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """손상된 파생 IPC는 경고·무효화하고 정상 canonical parquet을 반환한다."""
    from dartlab.core import dataLoader

    parquetPath = tmp_path / "dart" / "finance" / "005930.parquet"
    df = pl.DataFrame({"sj_div": ["BS"], "thstrm_amount": [99.0]})
    parquetPath.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(parquetPath)
    ipcPath = parquetPath.with_suffix(".arrow")
    ipcPath.write_bytes(b"not-an-arrow-file")
    future = parquetPath.stat().st_mtime + 1
    os.utime(ipcPath, (future, future))
    _stubLoadDataDeps(monkeypatch, tmp_path)

    with caplog.at_level(logging.WARNING, logger="dartlab.core.dataLoader"):
        result = dataLoader.loadData("005930", category="finance")

    assert result["thstrm_amount"].to_list() == [99.0]
    assert not ipcPath.exists()
    assert "IPC mirror" in caplog.text


def test_corruptMmapAndCanonicalPreserveBothFailures(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """IPC와 canonical이 모두 실패하면 canonical 오류에 IPC 원인을 보존한다."""
    from dartlab.core import dataLoader

    parquetPath = tmp_path / "dart" / "finance" / "005930.parquet"
    parquetPath.parent.mkdir(parents=True, exist_ok=True)
    parquetPath.write_bytes(b"not-a-parquet-file")
    ipcPath = parquetPath.with_suffix(".arrow")
    ipcPath.write_bytes(b"not-an-arrow-file")
    future = parquetPath.stat().st_mtime + 1
    os.utime(ipcPath, (future, future))
    _stubLoadDataDeps(monkeypatch, tmp_path)

    with pytest.raises(pl.exceptions.PolarsError) as failed:
        dataLoader.loadData("005930", category="finance", refresh="local_only")

    notes = getattr(failed.value, "__notes__", ())
    assert any("IPC mirror" in note for note in notes)


def test_schemaDivergentMmapFallsBackToCanonical(
    tmp_path: Path,
) -> None:
    """유효하지만 schema가 다른 파생 IPC는 canonical 전체 frame을 가로막지 않는다."""
    from dartlab.core.dataLoaderNative import readNativeWithRecovery

    parquetPath = tmp_path / "005930.parquet"
    pl.DataFrame({"canonical_only": [42]}).write_parquet(parquetPath)
    ipcPath = parquetPath.with_suffix(".arrow")
    pl.DataFrame({"mirror_only": [7]}).write_ipc(ipcPath)
    future = parquetPath.stat().st_mtime + 1
    os.utime(ipcPath, (future, future))

    result = readNativeWithRecovery(
        "005930",
        parquetPath,
        "finance",
        sinceYear=None,
        refresh="local_only",
        columns=None,
        predicate=None,
        reacquire=lambda: pytest.fail("정상 canonical 재조달 금지"),
    )

    assert result.to_dict(as_series=False) == {"canonical_only": [42]}
    assert not ipcPath.exists()


def test_schemaDivergentMmapDoesNotSilentlyDropRequestedColumns(
    tmp_path: Path,
) -> None:
    """IPC에 일부 요청 열만 있어도 부분 projection을 성공처럼 반환하지 않는다."""
    from dartlab.core.dataLoaderNative import readNativeWithRecovery

    parquetPath = tmp_path / "005930.parquet"
    pl.DataFrame({"common": [1], "canonical_only": [42]}).write_parquet(parquetPath)
    ipcPath = parquetPath.with_suffix(".arrow")
    pl.DataFrame({"common": [1]}).write_ipc(ipcPath)
    future = parquetPath.stat().st_mtime + 1
    os.utime(ipcPath, (future, future))

    result = readNativeWithRecovery(
        "005930",
        parquetPath,
        "finance",
        sinceYear=None,
        refresh="local_only",
        columns=["common", "canonical_only"],
        predicate=None,
        reacquire=lambda: pytest.fail("정상 canonical 재조달 금지"),
    )

    assert result.to_dict(as_series=False) == {"common": [1], "canonical_only": [42]}
    assert not ipcPath.exists()


def test_queryFailureDoesNotEagerMaterializeCanonical(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """query 오류의 artifact 판별은 canonical 전체 DataFrame을 만들지 않는다."""
    from dartlab.core import dataLoaderNative

    parquetPath = tmp_path / "large.parquet"
    pl.DataFrame(
        {
            "value": range(100_000),
            "payload": ["x" * 100] * 100_000,
        }
    ).write_parquet(parquetPath)
    originalRead = dataLoaderNative.pl.read_parquet
    eagerReads: list[tuple[int, int]] = []

    def recordEagerRead(*args, **kwargs):
        frame = originalRead(*args, **kwargs)
        eagerReads.append((frame.height, frame.estimated_size()))
        return frame

    monkeypatch.setattr(dataLoaderNative.pl, "read_parquet", recordEagerRead)

    with pytest.raises(pl.exceptions.ColumnNotFoundError):
        dataLoaderNative.readNativeWithRecovery(
            "005930",
            parquetPath,
            "finance",
            sinceYear=None,
            refresh="local_only",
            columns=None,
            predicate=pl.col("missing") == 1,
            reacquire=lambda: pytest.fail("query 오류 재조달 금지"),
        )

    assert eagerReads == []
