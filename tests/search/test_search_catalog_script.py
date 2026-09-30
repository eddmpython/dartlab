"""Search source catalog script tests."""

from __future__ import annotations

import json
import subprocess
import sys
import types
from importlib import util
from pathlib import Path

import polars as pl
import pytest


def _loadBuildSearchCatalogScript():
    path = Path(".github/scripts/search/buildSearchCatalog.py")
    spec = util.spec_from_file_location("buildSearchCatalogScript", path)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_remoteReconciliationMergesAllBatchesBeforePublish(tmp_path, monkeypatch):
    import huggingface_hub

    from dartlab.pipeline import searchCatalog
    from dartlab.providers.dart.search.sourceCatalog import writeSourceCatalogArtifacts

    module = _loadBuildSearchCatalogScript()
    first = tmp_path / "005930.parquet"
    second = tmp_path / "000660.parquet"
    for path in [first, second]:
        pl.DataFrame({"rceptNo": [f"{path.stem}old"], "contentRaw": ["1분기"]}).write_parquet(path)
    previous = writeSourceCatalogArtifacts("dartPanel", [first, second], outDir=tmp_path / "previous")
    manifest = json.loads(previous["manifest"].read_text(encoding="utf-8"))
    for path in [first, second]:
        pl.DataFrame({"rceptNo": [f"{path.stem}new"], "contentRaw": ["반기"]}).write_parquet(path)
    monkeypatch.setattr(
        huggingface_hub,
        "HfApi",
        lambda: types.SimpleNamespace(repo_info=lambda *args, **kwargs: types.SimpleNamespace(sha="pinned")),
    )
    monkeypatch.setattr(module, "_downloadRemotePreviousManifest", lambda *args, **kwargs: manifest)
    monkeypatch.setattr(module, "_downloadRemotePreviousCatalog", lambda *args, **kwargs: previous["catalog"])

    def batches(*args, **kwargs):
        assert kwargs["revision"] == "pinned"
        yield [first]
        yield [second]

    monkeypatch.setattr(searchCatalog, "reconcileSourceFiles", batches)
    published = []
    monkeypatch.setattr(
        module, "_upload", lambda source, result, prefix, **kwargs: published.append(pl.read_parquet(result["catalog"]))
    )
    module.main(
        [
            "--source",
            "dartPanel",
            "--input",
            str(tmp_path / "none"),
            "--out-dir",
            str(tmp_path / "out"),
            "--compare-remote-manifest",
            "--merge-previous-catalog",
            "--reconcile-remote-source",
            "--upload",
        ]
    )
    assert len(published) == 1
    assert set(published[0]["rceptNo"]) == {"005930new", "000660new"}
    current = json.loads((tmp_path / "out" / "dartPanel.source_manifest.json").read_text(encoding="utf-8"))
    assert current["sourceRevision"] == "pinned"
    assert len(current["files"]) == 2


@pytest.mark.parametrize("catalogChanged", [False, True])
def test_reconcilePublishAcceptsUnrelatedCommitsButRejectsCatalogRace(tmp_path, monkeypatch, catalogChanged):
    import huggingface_hub

    module = _loadBuildSearchCatalogScript()
    monkeypatch.setenv("HF_TOKEN", "test-token")
    manifest = tmp_path / "dartPanel.source_manifest.json"
    manifest.write_text("{}", encoding="utf-8")

    class Api:
        def repo_info(self, *args, **kwargs):
            return types.SimpleNamespace(sha="current")

        def get_paths_info(self, repo, names, **kwargs):
            digest = "changed" if catalogChanged and kwargs["revision"] == "current" else "same"
            return [types.SimpleNamespace(path=name, blob_id=digest) for name in names]

    monkeypatch.setattr(huggingface_hub, "HfApi", lambda **kwargs: Api())
    commits = []
    monkeypatch.setattr(module, "_uploadFiles", lambda *args, **kwargs: commits.append(kwargs["parentCommit"]))
    if catalogChanged:
        with pytest.raises(RuntimeError, match="catalog changed"):
            module._upload("dartPanel", {"manifest": manifest}, "dart/searchCatalog", parentCommit="original")
        assert commits == []
    else:
        module._upload("dartPanel", {"manifest": manifest}, "dart/searchCatalog", parentCommit="original")
        assert commits == ["current"]


def test_build_search_catalog_script_subprocess(tmp_path) -> None:
    source = tmp_path / "news.parquet"
    outDir = tmp_path / "out"
    pl.DataFrame(
        [
            {
                "url": "https://n.example/a",
                "date": "20260615",
                "title": "뉴스 헤드라인",
                "content": "반도체 뉴스",
            }
        ]
    ).write_parquet(source)

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/buildSearchCatalog.py",
            "--source",
            "newsPublic",
            "--input",
            str(source),
            "--out-dir",
            str(outDir),
        ],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert Path(result["manifest"]).exists()
    assert Path(result["catalog"]).exists()
    manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
    assert manifest["completenessCheck"]["valid"] is True


def test_build_search_catalog_script_has_upload_contract() -> None:
    text = Path(".github/scripts/search/buildSearchCatalog.py").read_text(encoding="utf-8")
    assert "--upload" in text
    assert "dart/searchCatalog" in text
    assert "--merge-previous-catalog" in text
    assert "--previous-catalog" in text
    assert "writeMergedSourceCatalogArtifacts" in text
    assert "create_commit" in text
    assert "CommitOperationAdd" in text
    assert "api.upload_file" in text
    assert "--min-files" in text
    assert "--min-catalog-rows" in text
    assert "GITHUB_RUN_ID" in text
    assert "producerRun" in text
    assert "--compare-remote-manifest" in text
    assert "--require-previous-manifest" in text
    assert "previousManifest" in text


def test_build_search_catalog_script_reads_github_run_lineage(monkeypatch) -> None:
    module = _loadBuildSearchCatalogScript()
    monkeypatch.setenv("GITHUB_WORKFLOW", "Original SSOT Sync")
    monkeypatch.setenv("GITHUB_JOB", "allfilings")
    monkeypatch.setenv("GITHUB_RUN_ID", "12345")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "2")
    monkeypatch.setenv("GITHUB_SHA", "abc123")
    monkeypatch.setenv("GITHUB_REF_NAME", "master")

    lineage = module._githubProducerRun("allFilings")

    assert lineage["system"] == "githubActions"
    assert lineage["workflow"] == "Original SSOT Sync"
    assert lineage["job"] == "allfilings"
    assert lineage["runId"] == "12345"
    assert lineage["artifactName"] == "search-catalog-allFilings-allfilings-12345"


def test_build_search_catalog_upload_batches_manifest_and_catalog(tmp_path, monkeypatch) -> None:
    module = _loadBuildSearchCatalogScript()

    class FakeOperation:
        def __init__(self, *, path_in_repo: str, path_or_fileobj: str) -> None:
            self.path_in_repo = path_in_repo
            self.path_or_fileobj = path_or_fileobj

    monkeypatch.setitem(sys.modules, "huggingface_hub", types.SimpleNamespace(CommitOperationAdd=FakeOperation))

    class FakeApi:
        def __init__(self) -> None:
            self.commits: list[dict] = []

        def create_commit(self, *, repo_id: str, repo_type: str, operations: list, commit_message: str) -> None:
            self.commits.append(
                {
                    "repo": repo_id,
                    "repoType": repo_type,
                    "message": commit_message,
                    "paths": [operation.path_in_repo for operation in operations],
                }
            )

    manifest = tmp_path / "allFilings.source_manifest.json"
    catalog = tmp_path / "allFilings.catalog_snapshot.parquet"
    manifest.write_text("{}", encoding="utf-8")
    catalog.write_bytes(b"catalog")
    api = FakeApi()

    uploaded = module._uploadFiles(
        api,
        "repo",
        [
            (manifest, "dart/searchCatalog/allFilings/allFilings.source_manifest.json"),
            (catalog, "dart/searchCatalog/allFilings/allFilings.catalog_snapshot.parquet"),
        ],
        commitMessage="Publish source catalog",
    )

    assert uploaded == api.commits[0]["paths"]
    assert api.commits == [
        {
            "repo": "repo",
            "repoType": "dataset",
            "message": "Publish source catalog",
            "paths": [
                "dart/searchCatalog/allFilings/allFilings.source_manifest.json",
                "dart/searchCatalog/allFilings/allFilings.catalog_snapshot.parquet",
            ],
        }
    ]


def test_build_search_catalog_script_blocks_empty_full_snapshot(tmp_path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/buildSearchCatalog.py",
            "--source",
            "allFilings",
            "--input",
            str(tmp_path / "missing" / "*.parquet"),
            "--out-dir",
            str(tmp_path / "out"),
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )

    assert proc.returncode != 0
    assert "source catalog completeness failed" in proc.stderr


def test_build_search_catalog_script_requires_previous_manifest(tmp_path) -> None:
    source = tmp_path / "news.parquet"
    pl.DataFrame([{"url": "https://n.example/a", "date": "20260615", "title": "뉴스"}]).write_parquet(source)

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/buildSearchCatalog.py",
            "--source",
            "newsPublic",
            "--input",
            str(source),
            "--out-dir",
            str(tmp_path / "out"),
            "--require-previous-manifest",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )

    assert proc.returncode != 0
    assert "previous source manifest required" in proc.stderr


def test_build_search_catalog_script_blocks_previous_manifest_drop(tmp_path) -> None:
    current = tmp_path / "current.parquet"
    previous = tmp_path / "previous.source_manifest.json"
    pl.DataFrame(
        [
            {
                "url": "https://n.example/a",
                "date": "20260615",
                "title": "남은 뉴스",
            }
        ]
    ).write_parquet(current)
    previous.write_text(
        json.dumps(
            {
                "source": "newsPublic",
                "snapshotScope": "full",
                "files": [{"path": f"{idx}.parquet", "rowCount": 1} for idx in range(100)],
                "totalRows": 100,
                "completenessCheck": {"catalogRows": 100},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/buildSearchCatalog.py",
            "--source",
            "newsPublic",
            "--input",
            str(current),
            "--out-dir",
            str(tmp_path / "out"),
            "--previous-manifest",
            str(previous),
            "--max-file-drop-ratio",
            "0.05",
            "--max-row-drop-ratio",
            "0.05",
            "--max-catalog-row-drop-ratio",
            "0.05",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )

    assert proc.returncode != 0
    assert "previousFileDrop:1/100:maxDrop=0.05" in proc.stderr
    assert "previousRowDrop:1/100:maxDrop=0.05" in proc.stderr


def test_build_search_catalog_script_merges_previous_news_catalog_without_date_drop(tmp_path) -> None:
    from dartlab.providers.dart.search.catalog import normalizeCatalogRows

    current = tmp_path / "2026-06-16.parquet"
    previousManifest = tmp_path / "newsPublic.source_manifest.json"
    previousCatalog = tmp_path / "newsPublic.catalog_snapshot.parquet"
    pl.DataFrame(
        [
            {
                "url": "https://n.example/new",
                "date": "20260616",
                "title": "새 뉴스",
                "content": "새로운 유상증자 뉴스",
            }
        ]
    ).write_parquet(current)
    normalizeCatalogRows(
        [
            {
                "source": "newsPublic",
                "url": "https://n.example/old",
                "date": "20260616",
                "title": "이전 뉴스",
                "content": "이전 날짜 stale 뉴스",
            },
            {
                "source": "newsPublic",
                "url": "https://n.example/keep",
                "date": "20260615",
                "title": "보존 뉴스",
                "content": "보존할 뉴스",
            },
        ]
    ).write_parquet(previousCatalog)
    previousManifest.write_text(
        json.dumps(
            {
                "source": "newsPublic",
                "snapshotScope": "full",
                "dataAsOf": "20260616",
                "files": [
                    {"path": str(tmp_path / "2026-06-15.parquet").replace("\\", "/"), "rowCount": 1},
                    {"path": str(current).replace("\\", "/"), "rowCount": 1},
                ],
                "totalRows": 2,
                "completenessCheck": {"catalogRows": 2},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            ".github/scripts/search/buildSearchCatalog.py",
            "--source",
            "newsPublic",
            "--input",
            str(current),
            "--out-dir",
            str(tmp_path / "out"),
            "--previous-manifest",
            str(previousManifest),
            "--previous-catalog",
            str(previousCatalog),
            "--merge-previous-catalog",
            "--min-files",
            "2",
            "--min-rows",
            "2",
            "--min-catalog-rows",
            "2",
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )

    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
    catalog = pl.read_parquet(result["catalog"])
    assert manifest["snapshotScope"] == "full"
    assert manifest["deltaSource"]["catalogRows"] == 1
    assert set(catalog.get_column("url").to_list()) == {
        "https://n.example/new",
        "https://n.example/old",
        "https://n.example/keep",
    }
