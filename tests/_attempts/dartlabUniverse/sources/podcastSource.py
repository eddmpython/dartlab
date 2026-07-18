"""Podcast episode metadata와 발행 companion의 존재를 전수 열거한다."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from ..canonical import PodcastCensus, PodcastRecord, canonicalDigest


def _readMapping(path: Path, kind: str) -> dict[str, Any]:
    if kind == "yaml":
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    else:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path.name} 최상위 값이 dict가 아님")
    return loaded


def enumeratePodcasts(root: Path) -> PodcastCensus:
    """Episode directory를 누락 없이 열거하고 metadata 존재를 기록한다.

    Args:
        root: repository의 `blog` directory.

    Returns:
        episode record와 parse error.

    Raises:
        FileNotFoundError: podcast root가 없을 때.

    Example:
        ``enumeratePodcasts(repoRoot / "blog")``.
    """
    episodeRoot = (root / "_podcasts" / "episodes").resolve()
    if not episodeRoot.is_dir():
        raise FileNotFoundError(episodeRoot)
    records = []
    errors = []
    for episodeDir in sorted(path for path in episodeRoot.iterdir() if path.is_dir()):
        relativePath = episodeDir.relative_to(root.resolve()).as_posix()
        episodePath = episodeDir / "episode.yaml"
        publishedPath = episodeDir / "published.json"
        episodeData = {}
        publishedData = {}
        try:
            if episodePath.is_file():
                episodeData = _readMapping(episodePath, "yaml")
            if publishedPath.is_file():
                publishedData = _readMapping(publishedPath, "json")
        except Exception as exc:
            errors.append(f"{relativePath}:{type(exc).__name__}:{exc}")
        sourceBytes = b""
        for path in (episodePath, publishedPath, episodeDir / "brief.json"):
            if path.is_file():
                sourceBytes += path.name.encode("utf-8") + b"\0" + path.read_bytes() + b"\0"
        youtubeId = str(episodeData.get("youtubeId") or publishedData.get("youtubeId") or "").strip() or None
        title = str(episodeData.get("title") or publishedData.get("title") or "").strip() or None
        episodeId = str(episodeData.get("id") or episodeData.get("episodeId") or episodeDir.name)
        records.append(
            PodcastRecord(
                episodeId=episodeId,
                relativePath=relativePath,
                title=title,
                youtubeId=youtubeId,
                hasEpisodeMetadata=episodePath.is_file(),
                hasPublishedReceipt=publishedPath.is_file(),
                hasScript=(episodeDir / "script.md").is_file(),
                metadataDigest=hashlib.sha256(sourceBytes).hexdigest(),
            )
        )
    orderedRecords = tuple(sorted(records, key=lambda record: record.relativePath))
    orderedErrors = tuple(sorted(errors))
    return PodcastCensus(
        episodes=orderedRecords,
        parseErrors=orderedErrors,
        digest=canonicalDigest({"episodes": orderedRecords, "parseErrors": orderedErrors}),
    )
