"""HF content index publish helpers.

Search index publishing must avoid exposing partial artifacts as current.
This module uploads every artifact into a run-scoped staging prefix first,
then publishes only the current `manifest.json` pointer. The pointer manifest
maps required files to the staging prefix through `fileSources`.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

from dartlab.core.dataConfig import DATA_RELEASES, repoFor
from dartlab.core.hfRetry import retryHfCall

MANIFEST_NAME = "manifest.json"


def contentIndexRepoPrefix(*, tier: str = "full") -> str:
    """Return the HF repo prefix for a search content index tier.

    Args:
        tier: `"full"` uses the flat contentIndex prefix. Other tiers use a
            subdirectory under that prefix.

    Returns:
        HF repository path prefix.

    Raises:
        없음.

    Example:
        >>> contentIndexRepoPrefix(tier="full").endswith("contentIndex")
        True
        >>> contentIndexRepoPrefix(tier="lite").endswith("contentIndex/lite")
        True
    """
    ciDir = DATA_RELEASES["contentIndex"]["dir"]
    cleanTier = (tier or "full").strip()
    return ciDir if cleanTier == "full" else f"{ciDir}/{cleanTier}"


def orderedPublishFiles(files: Iterable[str]) -> list[str]:
    """Deduplicate publish files and move manifest to the end.

    Args:
        files: File names relative to an index directory.

    Returns:
        Unique file names with `manifest.json` last when present.

    Raises:
        없음.

    Example:
        >>> orderedPublishFiles(["manifest.json", "main.npz", "main.npz"])
        ['main.npz', 'manifest.json']
    """
    seen: set[str] = set()
    out: list[str] = []
    hasManifest = False
    for name in files:
        clean = str(name).replace("\\", "/").strip("/")
        if not clean or clean in seen:
            continue
        seen.add(clean)
        if clean == MANIFEST_NAME:
            hasManifest = True
            continue
        out.append(clean)
    if hasManifest:
        out.append(MANIFEST_NAME)
    return out


def publishContentIndexFiles(
    *,
    token: str | None,
    indexDir: str | Path,
    files: Iterable[str],
    tier: str = "full",
    runId: str | None = None,
    api: Any | None = None,
    repoId: str | None = None,
    obsoleteCurrentFiles: Iterable[str] = (),
    requireSelfcheck: bool = True,
    previousManifestPath: str | Path | None = None,
    promoteCurrent: bool = True,
) -> dict[str, Any]:
    """Publish search index files through staging and a current manifest pointer.

    Args:
        token: HF write token. May be None when `api` is injected by tests.
        indexDir: Local content index directory.
        files: Candidate file names relative to `indexDir`.
        tier: `"full"` or tier subdirectory such as `"lite"`.
        runId: Optional run identifier for the staging path.
        api: Optional HfApi-like object for tests.
        repoId: Optional HF dataset id for tests.
        obsoleteCurrentFiles: Legacy current files to delete in non-manifest
            publish mode. Manifest-pointer publish keeps old current files for
            rollback compatibility and ignores this list.
        requireSelfcheck: True validates the local manifest, required files,
            hashes, and optional canary queries before any upload.
        previousManifestPath: Optional current manifest to seed `fileSources`
            from before a delta publish. New files uploaded in this call always
            override preserved paths.
        promoteCurrent: True uploads the pointer manifest to the current
            prefix. False uploads only run-scoped staging artifacts and a
            staging pointer manifest, so gates can validate the candidate
            before current is changed.

    Returns:
        Publish summary with repo paths.

    Raises:
        FileNotFoundError: If `manifest.json` is requested but missing.
        ValueError: If product manifest selfcheck fails.

    Example:
        >>> callable(publishContentIndexFiles)
        True
    """
    base = Path(indexDir)
    ordered = orderedPublishFiles(files)
    manifestRequested = MANIFEST_NAME in ordered
    if manifestRequested and not (base / MANIFEST_NAME).exists():
        raise FileNotFoundError(base / MANIFEST_NAME)

    existing = [name for name in ordered if (base / name).exists()]
    if manifestRequested and MANIFEST_NAME not in existing:
        raise FileNotFoundError(base / MANIFEST_NAME)
    if not existing:
        return {"uploaded": [], "stagingPrefix": "", "currentPrefix": "", "repoId": repoId or repoFor("contentIndex")}
    if requireSelfcheck and manifestRequested:
        preflight = preflightContentIndexPublish(base)
        if not preflight["valid"]:
            raise ValueError(f"contentIndex publish selfcheck failed: {preflight['errors']}")

    if api is None:
        from huggingface_hub import HfApi

        api = HfApi(token=token)
    repo = repoId or repoFor("contentIndex")
    currentPrefix = contentIndexRepoPrefix(tier=tier)
    safeRunId = _safeRunId(runId, tier=tier)
    stagingPrefix = f"{currentPrefix}/_staging/{safeRunId}"

    nonManifest = [name for name in existing if name != MANIFEST_NAME]
    currentManifestMode = MANIFEST_NAME in existing
    uploadItems: list[tuple[Path, str]] = [(base / name, f"{stagingPrefix}/{name}") for name in nonManifest]
    if currentManifestMode:
        with tempfile.TemporaryDirectory(prefix="dartlab-search-manifest-") as tmp:
            currentManifest = _writeCurrentPointerManifest(
                base / MANIFEST_NAME,
                Path(tmp) / MANIFEST_NAME,
                files=nonManifest,
                stagingPrefix=stagingPrefix,
                previousManifestPath=previousManifestPath,
            )
            uploadItems.append((currentManifest, f"{stagingPrefix}/{MANIFEST_NAME}"))
            if promoteCurrent:
                uploadItems.append((currentManifest, f"{currentPrefix}/{MANIFEST_NAME}"))
            uploaded = _uploadMany(
                api,
                repo,
                uploadItems,
                commitMessage=f"Publish search contentIndex {tier} {safeRunId}",
            )
    else:
        uploaded = _uploadMany(
            api,
            repo,
            uploadItems,
            commitMessage=f"Publish search contentIndex staging {tier} {safeRunId}",
        )
        for name in nonManifest:
            uploaded.append(_uploadOne(api, repo, base / name, f"{currentPrefix}/{name}"))
        for name in orderedPublishFiles(obsoleteCurrentFiles):
            try:
                retryHfCall(
                    api.delete_file,
                    path_in_repo=f"{currentPrefix}/{name}",
                    repo_id=repo,
                    repo_type="dataset",
                )
            except Exception:  # noqa: BLE001 - stale file deletion is best-effort.
                pass

    return {
        "uploaded": uploaded,
        "stagingPrefix": stagingPrefix,
        "currentPrefix": currentPrefix,
        "candidateManifestPath": f"{stagingPrefix}/{MANIFEST_NAME}",
        "currentManifestPath": f"{currentPrefix}/{MANIFEST_NAME}",
        "promoted": bool(promoteCurrent) if currentManifestMode else True,
        "tier": tier,
        "repoId": repo,
        "publishMode": "manifestPointer" if currentManifestMode else "legacyFiles",
        "selfcheck": preflight if requireSelfcheck and manifestRequested else None,
    }


def promoteCandidateManifest(
    *,
    token: str | None,
    candidateManifestPath: str,
    tier: str = "full",
    api: Any | None = None,
    repoId: str | None = None,
    remoteRoot: str | Path | None = None,
) -> dict[str, Any]:
    """Promote a staged candidate manifest to the current manifest pointer.

    Args:
        token: HF write token. May be None when `api` or `remoteRoot` is used.
        candidateManifestPath: Manifest path inside the HF dataset repo.
        tier: Content index tier.
        api: Optional HfApi-like object for tests.
        repoId: Optional HF dataset id for tests.
        remoteRoot: Optional local fake HF root.

    Returns:
        Promotion summary.

    Raises:
        FileNotFoundError: If the candidate manifest is missing.
        ValueError: If the candidate manifest is not object JSON.

    Example:
        >>> callable(promoteCandidateManifest)
        True
    """
    candidate = str(candidateManifestPath or "").replace("\\", "/").strip("/")
    if not candidate:
        raise ValueError("candidateManifestPath is required")
    repo = repoId or repoFor("contentIndex")
    currentPath = f"{contentIndexRepoPrefix(tier=tier)}/{MANIFEST_NAME}"
    if remoteRoot is not None:
        src = Path(remoteRoot) / candidate
        _validateManifestFile(src)
        dst = Path(remoteRoot) / currentPath
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        return _promotionSummary(
            repo=repo,
            tier=tier,
            candidate=candidate,
            currentPath=currentPath,
            uploaded=[currentPath],
            remoteRoot=remoteRoot,
        )

    if api is None:
        from huggingface_hub import HfApi

        api = HfApi(token=token)

    from dartlab.core.hfRetry import retryHfCall

    with tempfile.TemporaryDirectory(prefix="dartlab-search-promote-") as tmp:
        from huggingface_hub import hf_hub_download

        local = Path(
            retryHfCall(
                hf_hub_download,
                repo_id=repo,
                repo_type="dataset",
                filename=candidate,
                local_dir=tmp,
            )
        )
        _validateManifestFile(local)
        retryHfCall(
            api.upload_file,
            path_or_fileobj=str(local),
            path_in_repo=currentPath,
            repo_id=repo,
            repo_type="dataset",
        )
    return _promotionSummary(
        repo=repo,
        tier=tier,
        candidate=candidate,
        currentPath=currentPath,
        uploaded=[currentPath],
        remoteRoot=remoteRoot,
    )


def preflightContentIndexPublish(indexDir: str | Path) -> dict[str, Any]:
    """Validate a content index directory before HF publish.

    Args:
        indexDir: Local content index directory containing `manifest.json`.

    Returns:
        dict: Selfcheck result with validity and errors.

    Raises:
        None.

    Example:
        >>> preflightContentIndexPublish("missing")["valid"]
        False
    """
    from dartlab.providers.dart.search.localUpdate import selfcheckLocalIndex

    result = selfcheckLocalIndex(indexDir, requireManifest=True, requireLoadable=True)
    return {
        "valid": bool(result.get("valid")),
        "errors": list(result.get("errors") or []),
        "manifestValid": bool(result.get("manifestValid")),
    }


def _uploadOne(api: Any, repo: str, src: Path, dstPath: str) -> str:
    retryHfCall(
        api.upload_file,
        path_or_fileobj=str(src),
        path_in_repo=dstPath,
        repo_id=repo,
        repo_type="dataset",
    )
    print(f"  [ok] {dstPath} ({src.stat().st_size / 1024 / 1024:.1f} MB)")
    return dstPath


def _uploadMany(api: Any, repo: str, items: list[tuple[Path, str]], *, commitMessage: str) -> list[str]:
    if not items:
        return []
    if not hasattr(api, "create_commit"):
        return [_uploadOne(api, repo, src, dstPath) for src, dstPath in items]

    try:
        from huggingface_hub import CommitOperationAdd
    except Exception:  # noqa: BLE001 - old test environments can fall back to upload_file.
        return [_uploadOne(api, repo, src, dstPath) for src, dstPath in items]

    operations = [CommitOperationAdd(path_in_repo=dstPath, path_or_fileobj=str(src)) for src, dstPath in items]
    retryHfCall(
        api.create_commit,
        repo_id=repo,
        repo_type="dataset",
        operations=operations,
        commit_message=commitMessage,
    )
    uploaded = [dstPath for _, dstPath in items]
    for src, dstPath in items:
        print(f"  [ok] {dstPath} ({src.stat().st_size / 1024 / 1024:.1f} MB)")
    return uploaded


def _writeCurrentPointerManifest(
    srcManifest: Path,
    dstManifest: Path,
    *,
    files: Iterable[str],
    stagingPrefix: str,
    previousManifestPath: str | Path | None = None,
) -> Path:
    payload = json.loads(srcManifest.read_text(encoding="utf-8"))
    fileSources = _loadPreviousFileSources(previousManifestPath)
    currentFileSources = payload.get("fileSources")
    if isinstance(currentFileSources, dict):
        fileSources.update(
            {
                str(rel): str(repoPath)
                for rel, repoPath in currentFileSources.items()
                if isinstance(rel, str) and isinstance(repoPath, str) and rel and repoPath
            }
        )
    if not isinstance(fileSources, dict):
        fileSources = {}
    requiredFiles = payload.get("requiredFiles") if isinstance(payload.get("requiredFiles"), list) else []
    if requiredFiles:
        required = {str(name) for name in requiredFiles}
        fileSources = {name: repoPath for name, repoPath in fileSources.items() if name in required}
    for name in files:
        fileSources[name] = f"{stagingPrefix}/{name}"
    payload["fileSources"] = fileSources
    payload["publishMode"] = "manifestPointer"
    payload["stagingPrefix"] = stagingPrefix
    payload["promotedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    dstManifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return dstManifest


def _validateManifestFile(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"candidate manifest is not object JSON: {path}")
    return payload


def _promotionSummary(
    *,
    repo: str,
    tier: str,
    candidate: str,
    currentPath: str,
    uploaded: list[str],
    remoteRoot: str | Path | None,
) -> dict[str, Any]:
    return {
        "promoted": True,
        "tier": tier,
        "repoId": repo,
        "candidateManifestPath": candidate,
        "currentManifestPath": currentPath,
        "uploaded": uploaded,
        "remoteRoot": str(remoteRoot or ""),
    }


def _loadPreviousFileSources(previousManifestPath: str | Path | None) -> dict[str, str]:
    if previousManifestPath is None:
        return {}
    path = Path(previousManifestPath)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    raw = payload.get("fileSources")
    if not isinstance(raw, dict):
        return {}
    return {
        str(rel): str(repoPath)
        for rel, repoPath in raw.items()
        if isinstance(rel, str) and isinstance(repoPath, str) and rel and repoPath
    }


def _safeRunId(runId: str | None, *, tier: str) -> str:
    raw = (
        runId
        or os.environ.get("GITHUB_RUN_ID")
        or os.environ.get("GITHUB_SHA", "")[:12]
        or time.strftime("%Y%m%d%H%M%S")
    )
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", f"{tier}-{raw}").strip("-")
    return safe or f"{tier}-{time.strftime('%Y%m%d%H%M%S')}"
