"""HF metadata read 병목 회귀 가드."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]


def _loadScript(rel: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sync_new_stocks_uses_prefix_tree_listing(monkeypatch):
    """신규종목 remote code discovery 는 dataset 전체 repo_info 를 열거하지 않는다."""
    import huggingface_hub

    from dartlab.core.dataConfig import DATA_RELEASES

    calls: list[tuple[str, str, bool, bool]] = []

    class FakeApi:
        def __init__(self, token=None):
            self.token = token

        def repo_info(self, **_kwargs):  # noqa: N802
            raise AssertionError("syncNewStocks must not use broad repo_info listing")

        def list_repo_tree(self, *, repo_id, path_in_repo, repo_type, recursive, expand, token=None):  # noqa: N802
            calls.append((repo_id, path_in_repo, recursive, expand))
            return [
                SimpleNamespace(path=f"{path_in_repo}/005930.parquet"),
                SimpleNamespace(path=f"{path_in_repo}/README.md"),
            ]

    monkeypatch.setattr(huggingface_hub, "HfApi", FakeApi)
    mod = _loadScript(".github/scripts/sync/syncNewStocks.py")

    result = mod._remoteParquetCodes(["finance", "report"])

    assert result == {"finance": {"005930"}, "report": {"005930"}}
    assert calls == [
        ("eddmpython/dartlab-data", DATA_RELEASES["finance"]["dir"], True, False),
        ("eddmpython/dartlab-data", DATA_RELEASES["report"]["dir"], True, False),
    ]


def test_sync_new_stocks_degrades_on_listing_failure(monkeypatch):
    """enumeration 실패(429 retry 소진 등) 시 hard-fail 대신 빈 set 으로 degrade(로컬 캐시 폴백)."""
    import huggingface_hub

    class FakeApi:
        def __init__(self, token=None):
            self.token = token

        def list_repo_tree(self, **_kwargs):  # noqa: N802
            raise RuntimeError("simulated HF enumeration failure")

    monkeypatch.setattr(huggingface_hub, "HfApi", FakeApi)
    mod = _loadScript(".github/scripts/sync/syncNewStocks.py")

    # 하드페일 없이 빈 set 반환 → main() 이 _localParquetCodes 로 진행.
    result = mod._remoteParquetCodes(["finance", "report"])
    assert result == {"finance": set(), "report": set()}


def test_prebuild_requires_panel_input():
    """full 모드: prebuild 는 panel 없이 부분 scan 을 만들면 안 된다."""
    mod = _loadScript(".github/scripts/prebuild/prebuildData.py")

    with pytest.raises(SystemExit):
        mod._validateInputCoverage({"finance": 0, "report": 0, "panel": 0}, incremental=False)
    with pytest.raises(SystemExit):
        mod._validateInputCoverage({"finance": 1000, "report": 1000, "panel": 0}, incremental=False)
    with pytest.raises(SystemExit):
        mod._validateInputCoverage({"finance": 1000, "report": 1000, "panel": 100}, incremental=False)

    mod._validateInputCoverage({"finance": 1000, "report": 1000, "panel": 600}, incremental=False)


def test_listRemoteFiles_returns_name_size(monkeypatch):
    """listRemoteFiles 는 카테고리 prefix tree 로 {rel: size} 만 얻고 다운로드하지 않는다."""
    import huggingface_hub

    from dartlab.pipeline import seed

    class FakeApi:
        def __init__(self, token=None):
            self.token = token

        def repo_info(self, **_kwargs):  # noqa: N802
            raise AssertionError("listRemoteFiles must not use broad repo_info listing")

        def list_repo_tree(self, *, repo_id, path_in_repo, repo_type, recursive, expand, token=None):  # noqa: N802
            return [
                SimpleNamespace(path=f"{path_in_repo}/005930.parquet", size=111),
                SimpleNamespace(path=f"{path_in_repo}/000660.parquet", size=222),
                SimpleNamespace(path=f"{path_in_repo}/", size=0),  # 디렉토리 — 제외
            ]

    monkeypatch.setattr(huggingface_hub, "HfApi", FakeApi)
    out = seed.listRemoteFiles("panel")
    assert out == {"dart/panel/005930.parquet": 111, "dart/panel/000660.parquet": 222}


def test_downloadCategoryFiles_downloads_only_given(monkeypatch, tmp_path):
    """downloadCategoryFiles 는 지정 파일만 받고 (다운로드수, 404skip) 반환. 빈 목록은 no-op."""
    from dartlab.pipeline import seed

    calls: list[str] = []

    def fakeDownload(url, dest, token, timeout=60):
        calls.append(url)
        return None if url.endswith("MISSING.parquet") else 100  # None = 404 skip

    monkeypatch.setattr(seed, "_download", fakeDownload)

    n, skip = seed.downloadCategoryFiles(
        "panel",
        ["dart/panel/005930.parquet", "dart/panel/MISSING.parquet"],
        dataDir=str(tmp_path),
    )
    assert n == 1 and skip == 1
    assert any(c.endswith("dart/panel/005930.parquet") for c in calls)
    assert seed.downloadCategoryFiles("panel", [], dataDir=str(tmp_path)) == (0, 0)


def test_prebuild_incremental_allows_zero_panel():
    """증분 모드: panel 로컬 수 = 변경 종목 수라 0 도 정상(전량 보존). 단 전부 0 은 실패."""
    mod = _loadScript(".github/scripts/prebuild/prebuildData.py")

    # finance/report 존재하면 panel 변경 0 은 통과 (no-op 사이클)
    mod._validateInputCoverage({"finance": 1000, "report": 1000, "panel": 0}, incremental=True)
    # base seed 실패로 전부 0 이면 증분이어도 실패
    with pytest.raises(SystemExit):
        mod._validateInputCoverage({"finance": 0, "report": 0, "panel": 0}, incremental=True)


def test_prebuild_base_seed_skips_hf_listing_for_cached_finance_report(monkeypatch, tmp_path):
    """Actions cache 로 finance/report 가 있으면 HF tree listing 을 다시 열지 않는다."""
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.pipeline import seed

    mod = _loadScript(".github/scripts/prebuild/prebuildData.py")

    for cat in ("finance", "report"):
        catDir = tmp_path / DATA_RELEASES[cat]["dir"]
        catDir.mkdir(parents=True)
        (catDir / "005930.parquet").write_bytes(b"cached")

    calledCategories: list[list[str]] = []
    scanSeeded: list[str] = []

    def fakeSeedCategories(categories, *, dataDir=None, token=None):
        calledCategories.append(list(categories))
        return {}

    def fakeSeedKnownScanArtifacts(dataDir):
        scanSeeded.append(dataDir)
        return (0, 0, 0.0)

    monkeypatch.setattr(seed, "seedCategoriesFromHf", fakeSeedCategories)
    monkeypatch.setattr(mod, "_seedKnownScanArtifacts", fakeSeedKnownScanArtifacts)

    mod._seedBaseInputs(str(tmp_path))

    assert calledCategories == []
    assert scanSeeded == [str(tmp_path)]


def test_prebuild_incremental_panel_listing_429_uses_prior_ledger(monkeypatch):
    """HF panel tree listing 이 429 로 막히면 기존 ledger 를 보존하고 no-change 로 진행한다."""
    from dartlab.pipeline import seed
    from dartlab.scan.builders.kr import common

    mod = _loadScript(".github/scripts/prebuild/prebuildData.py")
    prior = {"dart/panel/005930.parquet": 123}

    def fakeListRemoteFiles(category, *, token=None):
        assert category == "panel"
        raise RuntimeError("simulated HF 429")

    monkeypatch.setattr(seed, "listRemoteFiles", fakeListRemoteFiles)
    monkeypatch.setattr(common, "loadScanBuildState", lambda: prior)

    changed, removed, newState = mod._prepareIncrementalPanel("unused")

    assert changed == []
    assert removed == []
    assert newState == prior


def test_data_prebuild_workflow_keeps_long_runs_observable():
    """prebuild 장기 실행은 버퍼링/무로그 실패 없이 heartbeat 와 HF retry cap 을 갖는다."""
    text = (ROOT / ".github/workflows/dataPrebuild.yml").read_text(encoding="utf-8")

    assert text.count("timeout-minutes: 180") == 2
    assert text.count("Free disk space") == 2
    assert text.count("df -h /") >= 7
    assert text.count("free -h || true") >= 6
    assert "uv run python -u -X utf8 .github/scripts/prebuild/prebuildData.py" in text
    assert text.count('PYTHONUNBUFFERED: "1"') == 2
    assert text.count("DARTLAB_SCAN_BATCH_SIZE: '50'") == 2
    assert text.count("POLARS_MAX_THREADS: '2'") == 2
    assert text.count("MALLOC_ARENA_MAX: '2'") == 2
    assert text.count("DARTLAB_HF_RETRY_ATTEMPTS: '3'") == 2
    assert text.count("DARTLAB_HF_RETRY_MAX_SINGLE_WAIT_SECONDS: '120'") == 2
    assert text.count("set +e") == 2
    assert text.count("set -e") == 2
    assert text.count("sleep 60") == 2
    assert "start incremental" in text
    assert "heartbeat incremental elapsed=${elapsed}s" in text
    assert "child incremental exit=${status}" in text
    assert "start full" in text
    assert "heartbeat full elapsed=${elapsed}s" in text
    assert "child full exit=${status}" in text
