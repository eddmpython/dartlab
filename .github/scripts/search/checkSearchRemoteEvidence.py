"""Audit remote HF evidence required for search productization.

The check verifies that source search catalogs and current contentIndex
manifests exist in the HF dataset, follows contentIndex ``fileSources`` to
required staged files, and reads ``source_manifest_set.json`` so operators can
prove the index preserves source-owner run lineage. Tests can pass
``--remote-root`` to exercise the same path against a local fake HF tree.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


DEFAULT_SOURCES = "allFilings,dartPanel,edgarPanel,newsPublic"
DEFAULT_TIERS = "full,lite"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-id", help="HF dataset repository id. Defaults to DartLab contentIndex repo.")
    parser.add_argument("--remote-root", help="Local fake HF root for tests and offline drills.")
    parser.add_argument("--expected-sources", default=DEFAULT_SOURCES)
    parser.add_argument("--content-tiers", default=DEFAULT_TIERS)
    parser.add_argument("--out", required=True, help="JSON report path.")
    parser.add_argument("--fail-on-missing", action="store_true")
    args = parser.parse_args(argv)

    report = auditRemoteEvidence(
        repoId=args.repo_id or _defaultRepoId(),
        expectedSources=_splitCsv(args.expected_sources),
        contentTiers=_splitCsv(args.content_tiers),
        remoteRoot=Path(args.remote_root) if args.remote_root else None,
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"valid": report["valid"], "errors": report["errors"]}, ensure_ascii=False))
    if args.fail_on_missing and not report["valid"]:
        return 1
    return 0


def auditRemoteEvidence(
    *,
    repoId: str,
    expectedSources: list[str],
    contentTiers: list[str],
    remoteRoot: Path | None = None,
) -> dict[str, Any]:
    remote = _RemoteInventory(repoId=repoId, remoteRoot=remoteRoot)
    sourceCatalog = _auditSourceCatalog(
        repoId=repoId,
        remote=remote,
        expectedSources=expectedSources,
        remoteRoot=remoteRoot,
    )
    contentIndex = _auditContentIndex(
        repoId=repoId,
        remote=remote,
        contentTiers=contentTiers,
        remoteRoot=remoteRoot,
    )
    errors = [*sourceCatalog["errors"], *contentIndex["errors"]]
    blockers = _blockers(sourceCatalog=sourceCatalog, contentIndex=contentIndex)
    return {
        "valid": not errors,
        "errors": errors,
        "blockers": blockers,
        "repoId": repoId,
        "remoteRoot": str(remoteRoot or ""),
        "inventoryMode": remote.inventoryMode,
        "fileCount": remote.fileCount(),
        "checkedFileCount": remote.checkedFileCount(),
        "sourceCatalog": sourceCatalog,
        "contentIndex": contentIndex,
    }


def _auditSourceCatalog(
    *,
    repoId: str,
    remote: _RemoteInventory,
    expectedSources: list[str],
    remoteRoot: Path | None,
) -> dict[str, Any]:
    errors: list[str] = []
    sources: dict[str, Any] = {}
    for source in expectedSources:
        manifestPath = f"dart/searchCatalog/{source}/{source}.source_manifest.json"
        catalogPath = f"dart/searchCatalog/{source}/{source}.catalog_snapshot.parquet"
        manifestExists = remote.exists(manifestPath)
        catalogExists = remote.exists(catalogPath)
        if not manifestExists:
            errors.append(f"missingSourceManifest:{source}")
        if not catalogExists:
            errors.append(f"missingSourceCatalog:{source}")
        manifest = _loadJsonPath(repoId=repoId, repoPath=manifestPath, remoteRoot=remoteRoot) if manifestExists else {}
        sources[source] = {
            "manifestPath": manifestPath,
            "catalogPath": catalogPath,
            "manifestExists": manifestExists,
            "catalogExists": catalogExists,
            "manifest": _sourceManifestSummary(manifest),
        }
    missingSources = [
        source for source, item in sources.items() if not item["manifestExists"] or not item["catalogExists"]
    ]
    return {
        "valid": not errors,
        "errors": errors,
        "expectedSources": expectedSources,
        "missingSources": missingSources,
        "sources": sources,
    }


def _auditContentIndex(
    *,
    repoId: str,
    remote: _RemoteInventory,
    contentTiers: list[str],
    remoteRoot: Path | None,
) -> dict[str, Any]:
    errors: list[str] = []
    manifests: dict[str, Any] = {}
    for tier in contentTiers:
        manifestPath = (
            "dart/contentIndex/manifest.json" if tier == "full" else f"dart/contentIndex/{tier}/manifest.json"
        )
        repoPrefix = "dart/contentIndex" if tier == "full" else f"dart/contentIndex/{tier}"
        exists = remote.exists(manifestPath)
        if not exists:
            errors.append(f"missingContentManifest:{tier}")
        manifest = _loadJsonPath(repoId=repoId, repoPath=manifestPath, remoteRoot=remoteRoot) if exists else {}
        manifestSummary = _contentManifestSummary(
            manifest,
            repoPrefix=repoPrefix,
            remote=remote,
            repoId=repoId,
            remoteRoot=remoteRoot,
        )
        errors.extend(f"missingContentFileSource:{tier}:{rel}" for rel in manifestSummary["missingFileSources"])
        errors.extend(
            f"missingContentFileSourceMapping:{tier}:{rel}" for rel in manifestSummary["missingFileSourceMappings"]
        )
        hasDelta = manifestSummary.get("hasDelta") is True
        deltaFiles = manifestSummary["deltaFileSources"]
        if hasDelta and not deltaFiles:
            errors.append(f"missingDeltaFiles:{tier}")
        if not hasDelta:
            errors.extend(f"staleDeltaFileSource:{tier}:{rel}" for rel in deltaFiles)
        manifests[tier] = {
            "manifestPath": manifestPath,
            "exists": exists,
            "manifest": manifestSummary,
        }
    return {
        "valid": not errors,
        "errors": errors,
        "tiers": contentTiers,
        "manifests": manifests,
    }


class _RemoteInventory:
    def __init__(self, *, repoId: str, remoteRoot: Path | None) -> None:
        self.repoId = repoId
        self.remoteRoot = remoteRoot
        self.inventoryMode = "localRecursive" if remoteRoot is not None else "targetedProbe"
        self._localFiles: set[str] | None = None
        self._existsCache: dict[str, bool] = {}
        self._checked: set[str] = set()

    def exists(self, repoPath: str) -> bool:
        normalized = repoPath.strip().lstrip("/")
        if not normalized:
            return False
        self._checked.add(normalized)
        cached = self._existsCache.get(normalized)
        if cached is not None:
            return cached
        if self.remoteRoot is not None:
            exists = normalized in self._localFileSet()
        else:
            exists = self._hfFileExists(normalized)
        self._existsCache[normalized] = exists
        return exists

    def fileCount(self) -> int | None:
        if self.remoteRoot is None:
            return None
        return len(self._localFileSet())

    def checkedFileCount(self) -> int:
        return len(self._checked)

    def _localFileSet(self) -> set[str]:
        if self._localFiles is None:
            if self.remoteRoot is None or not self.remoteRoot.exists():
                self._localFiles = set()
            else:
                self._localFiles = {
                    path.relative_to(self.remoteRoot).as_posix()
                    for path in self.remoteRoot.rglob("*")
                    if path.is_file()
                }
        return self._localFiles

    def _hfFileExists(self, repoPath: str) -> bool:
        from huggingface_hub import HfApi

        from dartlab.core.hfRetry import retryHfCall

        return bool(
            retryHfCall(
                HfApi(token=os.environ.get("HF_TOKEN") or None).file_exists,
                repo_id=self.repoId,
                filename=repoPath,
                repo_type="dataset",
                token=os.environ.get("HF_TOKEN") or None,
            )
        )


def _loadJsonPath(*, repoId: str, repoPath: str, remoteRoot: Path | None) -> dict[str, Any]:
    try:
        if remoteRoot is not None:
            path = remoteRoot / repoPath
            return json.loads(path.read_text(encoding="utf-8"))

        from huggingface_hub import hf_hub_download

        from dartlab.core.hfRetry import retryHfCall

        with tempfile.TemporaryDirectory(prefix="dartlab-search-remote-evidence-") as tmp:
            path = retryHfCall(
                hf_hub_download,
                repo_id=repoId,
                repo_type="dataset",
                filename=repoPath,
                local_dir=tmp,
                token=os.environ.get("HF_TOKEN") or None,
            )
            return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_loadError": f"{type(exc).__name__}:{exc}"}


def _sourceManifestSummary(manifest: dict[str, Any]) -> dict[str, Any]:
    files = manifest.get("files") if isinstance(manifest.get("files"), list) else []
    return {
        "loadError": manifest.get("_loadError"),
        "source": manifest.get("source"),
        "snapshotScope": manifest.get("snapshotScope"),
        "dataAsOf": manifest.get("dataAsOf"),
        "builtAt": manifest.get("builtAt"),
        "totalRows": manifest.get("totalRows"),
        "changedRows": manifest.get("changedRows"),
        "deletedRows": manifest.get("deletedRows"),
        "fileCount": len(files),
        "producer": manifest.get("producer"),
        "producerRun": manifest.get("producerRun") if isinstance(manifest.get("producerRun"), dict) else {},
    }


def _contentManifestSummary(
    manifest: dict[str, Any],
    *,
    repoPrefix: str,
    remote: _RemoteInventory,
    repoId: str,
    remoteRoot: Path | None,
) -> dict[str, Any]:
    fileSources = manifest.get("fileSources") if isinstance(manifest.get("fileSources"), dict) else {}
    requiredFiles = manifest.get("requiredFiles") if isinstance(manifest.get("requiredFiles"), list) else []
    deltaFileSources = sorted(
        {str(k) for k in fileSources if str(k).startswith("delta")}
        | {str(n) for n in requiredFiles if isinstance(n, str) and n.startswith("delta")}
    )
    missingMappings: list[str] = []
    missingSources: list[str] = []
    for rel in requiredFiles:
        if not isinstance(rel, str) or not rel or rel == "manifest.json":
            continue
        if manifest.get("publishMode") == "manifestPointer" and rel not in fileSources:
            missingMappings.append(rel)
            continue
        repoPath = _repoPathFor(str(fileSources.get(rel) or rel), repoPrefix=repoPrefix)
        if not remote.exists(repoPath):
            missingSources.append(rel)
    manifestSet = _loadContentSourceManifestSet(
        manifest,
        repoPrefix=repoPrefix,
        repoId=repoId,
        remoteRoot=remoteRoot,
        remote=remote,
    )
    manifestSetPayload = manifestSet.get("payload") if isinstance(manifestSet.get("payload"), dict) else {}
    manifestSetSources = _sourceManifestSetSources(manifestSetPayload or manifest.get("sourceManifestSet"))
    missingProducerRun = _sourceManifestSetProducerRunMissingSources(manifestSetPayload)
    graphCatalog = _entityGraphCatalogSummary(
        manifest,
        repoPrefix=repoPrefix,
        remote=remote,
    )
    return {
        "loadError": manifest.get("_loadError"),
        "artifactVersion": manifest.get("artifactVersion"),
        "schemaVersion": manifest.get("schemaVersion"),
        "builtAt": manifest.get("builtAt"),
        "publishMode": manifest.get("publishMode"),
        "mainDataAsOf": manifest.get("mainDataAsOf"),
        "deltaDataAsOf": manifest.get("deltaDataAsOf"),
        "hasDelta": manifest.get("hasDelta"),
        "sourceDataAsOf": manifest.get("sourceDataAsOf") or {},
        "nDocsBySource": manifest.get("nDocsBySource") or {},
        "sourceManifestSetId": manifest.get("sourceManifestSetId") or "",
        "sourceManifestSetSources": manifestSetSources,
        "sourceManifestSetLoadError": manifestSet.get("loadError") or "",
        "sourceManifestSetRepoPath": manifestSet.get("repoPath") or "",
        "sourceManifestSetProducerRunMissingSources": missingProducerRun,
        "entityGraphCatalog": graphCatalog,
        "requiredFiles": requiredFiles,
        "fileSourcesCount": len(fileSources),
        "missingFileSourceMappings": missingMappings,
        "missingFileSources": missingSources,
        "deltaFileSources": deltaFileSources,
        "stagingPrefix": manifest.get("stagingPrefix") or "",
    }


def _loadContentSourceManifestSet(
    manifest: dict[str, Any],
    *,
    repoPrefix: str,
    repoId: str,
    remoteRoot: Path | None,
    remote: _RemoteInventory,
) -> dict[str, Any]:
    requiredFiles = manifest.get("requiredFiles") if isinstance(manifest.get("requiredFiles"), list) else []
    if "source_manifest_set.json" not in requiredFiles:
        return {"repoPath": "", "payload": {}, "loadError": ""}
    fileSources = manifest.get("fileSources") if isinstance(manifest.get("fileSources"), dict) else {}
    repoPath = _repoPathFor(
        str(fileSources.get("source_manifest_set.json") or "source_manifest_set.json"), repoPrefix=repoPrefix
    )
    if not remote.exists(repoPath):
        return {"repoPath": repoPath, "payload": {}, "loadError": "missingFile"}
    payload = _loadJsonPath(repoId=repoId, repoPath=repoPath, remoteRoot=remoteRoot)
    loadError = str(payload.get("_loadError") or "") if isinstance(payload, dict) else "notObject"
    return {"repoPath": repoPath, "payload": payload if isinstance(payload, dict) else {}, "loadError": loadError}


def _entityGraphCatalogSummary(
    manifest: dict[str, Any],
    *,
    repoPrefix: str,
    remote: _RemoteInventory,
) -> dict[str, Any]:
    requiredFiles = manifest.get("requiredFiles") if isinstance(manifest.get("requiredFiles"), list) else []
    fileSources = manifest.get("fileSources") if isinstance(manifest.get("fileSources"), dict) else {}
    meta = manifest.get("entityGraphCatalog") if isinstance(manifest.get("entityGraphCatalog"), dict) else {}
    rel = "entityGraphCatalog.parquet"
    if rel not in requiredFiles:
        return {"present": False, "required": False}
    repoPath = _repoPathFor(str(fileSources.get(rel) or rel), repoPrefix=repoPrefix)
    return {
        "present": True,
        "required": True,
        "repoPath": repoPath,
        "fileSourceExists": remote.exists(repoPath),
        "schemaVersion": meta.get("schemaVersion") or "",
        "nEntities": meta.get("nEntities"),
        "stockCodeCount": meta.get("stockCodeCount"),
        "dataAsOf": meta.get("dataAsOf") or "",
    }


def _sourceManifestSetSources(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return []
    sources = value.get("sources")
    if not isinstance(sources, list):
        return []
    out: list[str] = []
    for item in sources:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source") or "")
        if source:
            out.append(source)
    return out


def _sourceManifestSetProducerRunMissingSources(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return []
    sources = value.get("sources")
    if not isinstance(sources, list):
        return []
    out: list[str] = []
    for item in sources:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source") or "")
        producerRun = item.get("producerRun") if isinstance(item.get("producerRun"), dict) else {}
        required = ("workflow", "job", "runId", "sha", "artifactName")
        if source and any(not str(producerRun.get(field) or "").strip() for field in required):
            out.append(source)
    return out


def _repoPathFor(raw: str, *, repoPrefix: str) -> str:
    return raw if raw.startswith(f"{repoPrefix}/") else f"{repoPrefix}/{raw.lstrip('/')}"


def _blockers(*, sourceCatalog: dict[str, Any], contentIndex: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if sourceCatalog["missingSources"]:
        blockers.append("sourceCatalogMissing")
    missingTiers = [tier for tier, item in contentIndex["manifests"].items() if not item["exists"]]
    if missingTiers:
        blockers.append("contentIndexManifestMissing")
    if any(str(error).startswith("missingContentFileSource") for error in contentIndex.get("errors") or []):
        blockers.append("contentIndexFileSourceMissing")
    if any(
        str(error).startswith(("missingDeltaFiles", "staleDeltaFileSource"))
        for error in contentIndex.get("errors") or []
    ):
        blockers.append("contentIndexDeltaInconsistent")
    return blockers


def _splitCsv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _defaultRepoId() -> str:
    from dartlab.core.dataConfig import repoFor

    return repoFor("contentIndex")


if __name__ == "__main__":
    raise SystemExit(main())
