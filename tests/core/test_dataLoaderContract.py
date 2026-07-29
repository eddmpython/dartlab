"""Native ``loadData`` request·acquisition 계약 회귀."""

from __future__ import annotations

import logging
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def _stubNativeRoot(monkeypatch: pytest.MonkeyPatch, dataDir: Path) -> None:
    from dartlab.core import dataLoader

    monkeypatch.setattr(dataLoader, "_dataDir", lambda _category: dataDir)
    monkeypatch.setattr(dataLoader, "_shouldRefreshHfCategory", lambda *_args, **_kwargs: False)
    monkeypatch.setattr("dartlab.core.memory.checkMemoryAndGc", lambda *_args, **_kwargs: None)


def test_requestContractHelpersAreDirectlyEnforced(tmp_path: Path) -> None:
    """경로와 refresh helper 자체도 runtime 계약을 직접 보장한다."""
    from dartlab.core.dataLoaderContract import (
        resolveShardPath,
        validateRefreshPolicy,
        validateShardKey,
    )

    assert validateShardKey("KR/2026-07-29") == ("KR", "2026-07-29")
    assert resolveShardPath(tmp_path, "KR/2026-07-29") == (tmp_path / "KR" / "2026-07-29.parquet").resolve()
    validateRefreshPolicy("edgarDocs", "force_rebuild", pyodide=False)
    with pytest.raises(ValueError, match="refresh"):
        validateRefreshPolicy("edgarDocs", "force_rebuild", pyodide=True)


def test_queryContractHelpersShareFilterAndProjection() -> None:
    """native lazy와 eager query helper가 같은 year·predicate·projection을 낸다."""
    from dartlab.core.dataLoaderContract import (
        applyEagerQuery,
        collectLazyQuery,
        projectedColumns,
    )

    source = pl.DataFrame(
        {
            "year": ["2022", "2024", "2024"],
            "kind": ["keep", "drop", "keep"],
            "value": [1, 2, 3],
        }
    )
    predicate = pl.col("kind") == "keep"
    expected = pl.DataFrame({"value": [3]})

    lazyResult = collectLazyQuery(
        source.lazy(),
        sinceYear=2023,
        columns=["value"],
        predicate=predicate,
    )
    eagerResult = applyEagerQuery(
        source,
        sinceYear=2023,
        columns=["value"],
        predicate=predicate,
    )
    projection = projectedColumns(
        source.columns,
        category="finance",
        sinceYear=2023,
        asOf=None,
        columns=["value"],
        predicate=predicate,
    )

    assert lazyResult.equals(expected)
    assert eagerResult.equals(expected)
    assert projection == ["year", "kind", "value"]


def test_nativeArtifactHelpersValidateAndReadCanonical(tmp_path: Path) -> None:
    """native artifact 검증과 읽기 helper를 orchestration 밖에서도 직접 고정한다."""
    from dartlab.core.dataLoaderNative import (
        readNativeWithRecovery,
        validateParquetArtifact,
    )

    path = tmp_path / "005930.parquet"
    pl.DataFrame({"value": [7]}).write_parquet(path)
    validateParquetArtifact(path)

    result = readNativeWithRecovery(
        "005930",
        path,
        "panel",
        sinceYear=None,
        refresh="local_only",
        columns=None,
        predicate=None,
        reacquire=lambda: pytest.fail("정상 canonical 재조달 금지"),
    )

    assert result["value"].to_list() == [7]


def test_yearsDescKeepsPublicEmptyAndOrderingContract() -> None:
    """dataLoader 공개 연도 helper의 빈 입력과 내림차순 계약을 고정한다."""
    from dartlab.core.dataLoader import yearsDesc

    assert yearsDesc(None) == []
    assert yearsDesc(pl.DataFrame({"value": [1]})) == []
    assert yearsDesc(pl.DataFrame({"year": [2022, 2024, 2023, 2024]}), limit=2) == [2024, 2023]


def test_nestedShardKeyStaysInsideCategory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """news 계열의 합법적인 ``MARKET/day`` shard key는 유지한다."""
    from dartlab.core.dataLoader import loadData

    dataDir = tmp_path / "news"
    path = dataDir / "KR" / "2026-07-29.parquet"
    path.parent.mkdir(parents=True)
    pl.DataFrame({"value": [1]}).write_parquet(path)
    _stubNativeRoot(monkeypatch, dataDir)

    result = loadData("KR/2026-07-29", "newsRss", refresh="local_only")

    assert result["value"].to_list() == [1]


@pytest.mark.parametrize(
    "stockCode",
    (
        "../outside",
        r"..\outside",
        "/absolute",
        r"C:\absolute",
        r"KR\C:\absolute",
        "KR//day",
        "KR/ day",
    ),
)
def test_shardKeyCannotEscapeCategory(
    stockCode: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """절대·drive·상위 경로와 비정규 shard key를 데이터 경로로 쓰지 않는다."""
    from dartlab.core.dataLoader import loadData

    dataDir = tmp_path / "category"
    dataDir.mkdir()
    pl.DataFrame({"secret": [7]}).write_parquet(tmp_path / "outside.parquet")
    _stubNativeRoot(monkeypatch, dataDir)

    with pytest.raises(ValueError, match="stockCode"):
        loadData(stockCode, "panel", refresh="local_only")


def test_nativeRejectsUnknownRefreshBeforeDataAccess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """native도 지원하지 않는 refresh를 auto처럼 해석하지 않는다."""
    from dartlab.core.dataLoader import loadData

    _stubNativeRoot(monkeypatch, tmp_path)

    with pytest.raises(ValueError, match="refresh"):
        loadData("005930", "panel", refresh="force")


def test_genericLocalOnlyMissingNeverDownloads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """일반 HF category의 local_only cache 부재는 network 0회로 실패한다."""
    from dartlab.core import dataLoader

    _stubNativeRoot(monkeypatch, tmp_path)

    def downloadForbidden(*_args, **_kwargs):
        raise AssertionError("local_only download 금지")

    monkeypatch.setattr(dataLoader, "_downloadFromHf", downloadForbidden)

    with pytest.raises(FileNotFoundError, match="로컬 parquet 없음"):
        dataLoader.loadData("missing", "panel", refresh="local_only")


def test_edgarLocalOnlyMissingNeverDispatchesLoader(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SEC bulk category도 local_only cache 부재 시 provider를 호출하지 않는다."""
    from dartlab.core import dataLoader

    _stubNativeRoot(monkeypatch, tmp_path)

    def loaderForbidden(_category: str):
        raise AssertionError("local_only loader dispatch 금지")

    monkeypatch.setattr("dartlab.core.loaders.getLoader", loaderForbidden)

    with pytest.raises(FileNotFoundError, match="로컬 parquet 없음"):
        dataLoader.loadData("AAPL", "edgar", refresh="local_only")


def test_edgarForceCheckReachesProviderAsPolicy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SEC bulk provider까지 bool 축약 없이 정규화된 refresh 정책을 보존한다."""
    from dartlab.core import dataLoader

    _stubNativeRoot(monkeypatch, tmp_path)
    captured: dict[str, object] = {}

    class FakeLoader:
        def ensure(self, _stockCode, path, **kwargs):
            captured.update(kwargs)
            pl.DataFrame({"value": [1]}).write_parquet(path)

    monkeypatch.setattr("dartlab.core.loaders.getLoader", lambda _category: FakeLoader())

    result = dataLoader.loadData("AAPL", "edgar", refresh="force_check")

    assert result["value"].to_list() == [1]
    assert captured["refresh"] == "force_check"


def test_edgarDocsForceRebuildRemainsSupported(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """native EDGAR docs의 명시적 전체 재구축 정책은 유지한다."""
    from dartlab.core import dataLoader

    _stubNativeRoot(monkeypatch, tmp_path)
    captured: dict[str, object] = {}

    class FakeLoader:
        def ensure(self, _stockCode, path, **kwargs):
            captured.update(kwargs)
            pl.DataFrame({"year": ["2024"], "value": [1]}).write_parquet(path)

    monkeypatch.setattr("dartlab.core.loaders.getLoader", lambda _category: FakeLoader())

    result = dataLoader.loadData("AAPL", "edgarDocs", refresh="force_rebuild")

    assert result["value"].to_list() == [1]
    assert captured["refresh"] == "force_rebuild"


def test_edgarDocsDefaultYearMatchesNativeAndPyodide(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """EDGAR docs의 기본 2009 시작 연도를 native read에도 실제 적용한다."""
    from dartlab.core import dataLoader

    pl.DataFrame(
        {
            "year": ["2008", "2009", "2024"],
            "value": [0, 1, 2],
        }
    ).write_parquet(tmp_path / "AAPL.parquet")
    _stubNativeRoot(monkeypatch, tmp_path)

    result = dataLoader.loadData("AAPL", "edgarDocs", refresh="local_only")

    assert result["year"].to_list() == ["2009", "2024"]


def test_corruptCanonicalRecoversExactlyOnce(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """기존 native cache 손상은 관측·무효화 후 정확히 한 번 재조달한다."""
    from dartlab.core import dataLoader

    path = tmp_path / "005930.parquet"
    path.write_bytes(b"invalid parquet")
    _stubNativeRoot(monkeypatch, tmp_path)
    downloads = 0

    def recover(_stockCode: str, target: Path, _category: str) -> None:
        nonlocal downloads
        downloads += 1
        pl.DataFrame({"value": [9]}).write_parquet(target)

    monkeypatch.setattr(dataLoader, "_downloadFromHf", recover)

    with caplog.at_level(logging.WARNING, logger="dartlab.core.dataLoader"):
        result = dataLoader.loadData("005930", "panel")

    assert result["value"].to_list() == [9]
    assert downloads == 1
    assert "손상" in caplog.text


def test_corruptCanonicalPreservesArbitraryReacquireFailure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """재조달 공급자 예외 종류와 무관하게 최초 artifact 손상 원인을 보존한다."""
    from dartlab.core import dataLoader

    class ProviderFailure(Exception):
        pass

    path = tmp_path / "005930.parquet"
    path.write_bytes(b"invalid parquet")
    _stubNativeRoot(monkeypatch, tmp_path)

    def failReacquire(*_args, **_kwargs):
        raise ProviderFailure("provider unavailable")

    monkeypatch.setattr(dataLoader, "_downloadFromHf", failReacquire)

    with pytest.raises(ProviderFailure) as failed:
        dataLoader.loadData("005930", "panel")

    assert any("최초 parquet 읽기 실패" in note for note in getattr(failed.value, "__notes__", ()))


def test_corruptCanonicalLocalOnlyInvalidatesWithoutNetwork(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """local_only 손상 cache는 고정하지 않고 제거하되 network는 열지 않는다."""
    from dartlab.core import dataLoader

    path = tmp_path / "005930.parquet"
    path.write_bytes(b"invalid parquet")
    _stubNativeRoot(monkeypatch, tmp_path)

    def downloadForbidden(*_args, **_kwargs):
        raise AssertionError("local_only recovery download 금지")

    monkeypatch.setattr(dataLoader, "_downloadFromHf", downloadForbidden)

    with pytest.raises(pl.exceptions.PolarsError) as failed:
        dataLoader.loadData("005930", "panel", refresh="local_only")

    assert not path.exists()
    assert any("local_only" in note for note in getattr(failed.value, "__notes__", ()))
