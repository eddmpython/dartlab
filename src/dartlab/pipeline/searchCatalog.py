"""Reconcile published source bytes with the files consumed by a search catalog."""

from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Iterator, Mapping

from dartlab.core.hfRetry import retryHfCall
from dartlab.pipeline.seed import _download

PANEL_SOURCE_PATHS = {"dartPanel": "dart/panel", "edgarPanel": "edgar/panel"}


def reconcileSourceFiles(
    source: str,
    previousManifest: Mapping[str, Any],
    *,
    repo: str,
    revision: str,
    workDir: Path,
    token: str | None = None,
) -> Iterator[list[Path]]:
    """Download source files whose published bytes have not reached the catalog.

    Args:
        source: Panel catalog source name.
        previousManifest: Previously published catalog provenance.
        repo: HF dataset repository.
        revision: Immutable revision shared by manifest and source reads.
        workDir: Caller-owned temporary directory for downloaded files.
        token: Optional HF authentication token.

    Returns:
        Batches of at most 100 changed paths, removed after the caller consumes each
        batch. A legacy manifest without SHA256 is reconciled once.

    Raises:
        ValueError: Unsupported source or source integrity mismatch.
        RuntimeError: Published source inventory is unavailable or empty.

    Example:
        >>> callable(reconcileSourceFiles)
        True
    """
    from huggingface_hub import HfApi

    if source not in PANEL_SOURCE_PATHS:
        raise ValueError(f"source reconciliation unsupported: {source}")
    prefix = PANEL_SOURCE_PATHS[source]
    api = HfApi(token=token)
    entries = retryHfCall(lambda: list(api.list_repo_tree(repo, prefix, repo_type="dataset", revision=revision)))
    remote = [entry for entry in entries if entry.path.endswith(".parquet")]
    if not remote:
        raise RuntimeError(f"published source inventory is empty: {source}")
    previous = {Path(row["path"]).name: row for row in previousManifest.get("files", [])}
    changed = []
    for entry in remote:
        digest = entry.lfs.sha256 if entry.lfs else ""
        if not digest:
            raise ValueError(f"source SHA256 unavailable: {entry.path}")
        if previous.get(Path(entry.path).name, {}).get("sha256") != digest:
            changed.append(entry)
    print(
        f"[searchCatalog] {source}: published={len(remote)}, unindexed={len(changed)}, revision={revision}", flush=True
    )

    def download(entry: Any) -> Path:
        """고정 revision의 원문을 받고 크기와 SHA256을 확인한다."""
        path = workDir / entry.path
        size = _download(f"https://huggingface.co/datasets/{repo}/resolve/{revision}/{entry.path}", path, token)
        if size != entry.size:
            raise ValueError(f"source size mismatch: {entry.path}")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != entry.lfs.sha256:
            raise ValueError(f"source SHA256 mismatch: {entry.path}")
        return path

    with ThreadPoolExecutor(max_workers=4) as pool:
        for offset in range(0, len(changed), 100):
            paths = list(pool.map(download, changed[offset : offset + 100]))
            try:
                yield paths
            finally:
                for path in paths:
                    path.unlink(missing_ok=True)
            print(f"[searchCatalog] indexed sources {offset + len(paths)}/{len(changed)}", flush=True)
