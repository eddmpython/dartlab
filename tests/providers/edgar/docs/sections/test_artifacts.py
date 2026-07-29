"""providers/edgar/docs/sections/artifacts.py mirror smoke — P6."""

from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.providers.edgar.docs.sections.artifacts  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_load_canonical_rows_callable() -> None:
    """loadCanonicalRows() callable smoke."""
    from dartlab.providers.edgar.docs.sections.artifacts import loadCanonicalRows

    assert callable(loadCanonicalRows)


def test_load_coverage_snapshot_callable() -> None:
    """loadCoverageSnapshot() callable smoke."""
    from dartlab.providers.edgar.docs.sections.artifacts import loadCoverageSnapshot

    assert callable(loadCoverageSnapshot)


def test_load_topic_drafts_callable() -> None:
    """loadTopicDrafts() callable smoke."""
    from dartlab.providers.edgar.docs.sections.artifacts import loadTopicDrafts

    assert callable(loadTopicDrafts)


def test_packaged_artifact_path_callable() -> None:
    """packagedArtifactPath() callable smoke."""
    from dartlab.providers.edgar.docs.sections.artifacts import packagedArtifactPath

    assert callable(packagedArtifactPath)


def test_sections_hf_failure_is_typed_and_retryable(monkeypatch, tmp_path: Path) -> None:
    """원격 실패를 정상 artifact 부재로 삼키거나 영구 캐시하지 않는다."""
    import huggingface_hub

    import dartlab.config as cfg
    from dartlab.core import hfRetry
    from dartlab.providers.edgar.docs.sections import sectionsStorage as storage

    calls = 0

    def failDownload(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise OSError("network down")

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.delenv("DARTLAB_NO_HF_DOWNLOAD", raising=False)
    monkeypatch.setattr(huggingface_hub, "snapshot_download", failDownload)
    monkeypatch.setattr(hfRetry, "retryHfCall", lambda fn, *args, **kwargs: fn(*args, **kwargs))
    storage._HF_DOWNLOAD_ATTEMPTED.clear()

    for _ in range(2):
        with pytest.raises(storage.SectionsArtifactFetchError, match="network down") as excInfo:
            storage._ensureFromHf("aapl")
        assert isinstance(excInfo.value.__cause__, OSError)

    assert calls == 2
    assert "AAPL" not in storage._HF_DOWNLOAD_ATTEMPTED


def test_sections_normal_remote_absence_is_cached(monkeypatch, tmp_path: Path) -> None:
    """정상 다운로드 응답 뒤 artifact가 없을 때만 False이며 같은 process에서 재호출하지 않는다."""
    import huggingface_hub

    import dartlab.config as cfg
    from dartlab.core import hfRetry
    from dartlab.providers.edgar.docs.sections import sectionsStorage as storage

    calls = 0

    def noArtifact(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return str(tmp_path)

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.delenv("DARTLAB_NO_HF_DOWNLOAD", raising=False)
    monkeypatch.setattr(huggingface_hub, "snapshot_download", noArtifact)
    monkeypatch.setattr(hfRetry, "retryHfCall", lambda fn, *args, **kwargs: fn(*args, **kwargs))
    storage._HF_DOWNLOAD_ATTEMPTED.clear()

    assert storage._ensureFromHf("aapl") is False
    assert storage._ensureFromHf("aapl") is False
    assert calls == 1
    assert "AAPL" in storage._HF_DOWNLOAD_ATTEMPTED


def test_sections_corrupt_index_is_not_missing_data(monkeypatch, tmp_path: Path) -> None:
    """손상 index를 정상 부재 None으로 위장하지 않는다."""
    import dartlab.config as cfg
    from dartlab.providers.edgar.docs.sections import sectionsStorage as storage

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    sectionDir = storage.sectionsDir("aapl")
    sectionDir.mkdir(parents=True)
    pl.DataFrame({"period": ["2024Q4"]}).write_parquet(sectionDir / "2024Q4.parquet")
    (sectionDir / "_index.parquet").write_bytes(b"not parquet")

    with pytest.raises(storage.SectionsArtifactReadError, match="index 읽기"):
        storage.loadSectionsIndex("aapl")


def test_sections_projection_schema_error_is_explicit(monkeypatch, tmp_path: Path) -> None:
    """존재하는 artifact의 projection 계약 위반은 None이 아니다."""
    import dartlab.config as cfg
    from dartlab.providers.edgar.docs.sections import sectionsStorage as storage

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    sectionDir = storage.sectionsDir("aapl")
    sectionDir.mkdir(parents=True)
    pl.DataFrame({"unexpected": ["value"]}).write_parquet(sectionDir / "2024Q4.parquet")

    with pytest.raises(storage.SectionsSchemaError, match="요청 컬럼"):
        storage.loadSectionsLong("aapl", columns=["topic", "content_plain"])
