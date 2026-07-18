"""중앙 media catalog, HF object tree, blog reference를 양방향 대조한다."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from ..canonical import DiscoveredFile, MediaCensus, canonicalDigest

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_OBJECT_PREFIX = "objects/sha256/"


def _loadCatalog(catalog: Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(catalog, Path):
        loaded = json.loads(catalog.read_text(encoding="utf-8"))
    else:
        loaded = catalog
    if not isinstance(loaded, dict):
        raise ValueError("media catalog 최상위 값은 dict여야 함")
    return loaded


def _allStrings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _allStrings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _allStrings(item)


def _objectPathFromRef(ref: str) -> str | None:
    cleaned = ref.strip()
    if cleaned.startswith(_OBJECT_PREFIX):
        return cleaned
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"}:
        return None
    parts = unquote(parsed.path).strip("/").split("/")
    if "resolve" not in parts:
        return None
    resolveIndex = parts.index("resolve")
    remoteParts = parts[resolveIndex + 2 :]
    remotePath = "/".join(remoteParts)
    return remotePath if remotePath.startswith(_OBJECT_PREFIX) else None


def reconcileMedia(
    catalog: Path | dict[str, Any],
    hfTree: Iterable[DiscoveredFile],
    blogRefs: Iterable[str],
) -> MediaCensus:
    """Catalog object, HF live path, blog reference의 누락과 고아를 계산한다.

    Args:
        catalog: `media/catalog.json` path 또는 이미 읽은 dict.
        hfTree: pinned HF media metadata tree.
        blogRefs: blog frontmatter와 본문에서 발견한 image reference.

    Returns:
        referenced, unreferenced, missing, broken 상태를 가진 media census.

    Raises:
        ValueError: catalog 최상위 계약이 깨진 경우.

    Example:
        ``reconcileMedia(path, files, refs)``.
    """
    data = _loadCatalog(catalog)
    objects = data.get("objects")
    aliases = data.get("files")
    posts = data.get("posts")
    collections = data.get("collections")
    manifests = data.get("manifests")
    for name, value in (
        ("objects", objects),
        ("files", aliases),
        ("posts", posts),
        ("collections", collections),
        ("manifests", manifests),
    ):
        if not isinstance(value, dict):
            raise ValueError(f"media catalog {name}는 dict여야 함")

    errors = []
    objectPathByDigest = {}
    for digest, metadata in objects.items():
        if not _SHA256_RE.fullmatch(str(digest)) or not isinstance(metadata, dict):
            errors.append(f"INVALID_OBJECT:{digest}")
            continue
        path = str(metadata.get("path") or "")
        if not path.startswith(f"{_OBJECT_PREFIX}{digest[:2]}/{digest}"):
            errors.append(f"OBJECT_PATH_MISMATCH:{digest}")
            continue
        if not isinstance(metadata.get("bytes"), int) or int(metadata["bytes"]) < 0:
            errors.append(f"OBJECT_SIZE_INVALID:{digest}")
        objectPathByDigest[str(digest)] = path

    referencedDigests = set()
    for alias, digest in aliases.items():
        normalized = str(digest)
        if normalized not in objects:
            errors.append(f"ALIAS_TARGET_MISSING:{alias}")
        else:
            referencedDigests.add(normalized)
    for ref in _allStrings({"posts": posts, "collections": collections, "manifests": manifests}):
        if ref in aliases:
            referencedDigests.add(str(aliases[ref]))
        elif ref in objects:
            referencedDigests.add(ref)
        else:
            objectPath = _objectPathFromRef(ref)
            if objectPath:
                for digest, path in objectPathByDigest.items():
                    if path == objectPath:
                        referencedDigests.add(digest)
                        break

    liveObjectPaths = {file.path for file in hfTree if file.path.startswith(_OBJECT_PREFIX)}
    expectedObjectPaths = set(objectPathByDigest.values())
    missingObjectPaths = tuple(sorted(expectedObjectPaths - liveObjectPaths))
    unregisteredHfObjectPaths = tuple(sorted(liveObjectPaths - expectedObjectPaths))

    brokenBlogRefs = []
    for ref in sorted(set(str(item).strip() for item in blogRefs if str(item).strip())):
        if ref in aliases:
            digest = str(aliases[ref])
            path = objectPathByDigest.get(digest)
            if not path or path not in liveObjectPaths:
                brokenBlogRefs.append(ref)
            else:
                referencedDigests.add(digest)
            continue
        objectPath = _objectPathFromRef(ref)
        if objectPath is not None:
            if objectPath not in liveObjectPaths or objectPath not in expectedObjectPaths:
                brokenBlogRefs.append(ref)
            else:
                digest = next((key for key, value in objectPathByDigest.items() if value == objectPath), None)
                if digest:
                    referencedDigests.add(digest)

    unreferenced = tuple(sorted(set(objectPathByDigest) - referencedDigests))
    orderedErrors = tuple(sorted(set(errors)))
    digest = canonicalDigest(
        {
            "catalogVersion": data.get("version"),
            "repo": data.get("repo"),
            "objects": objectPathByDigest,
            "aliases": aliases,
            "posts": posts,
            "collections": collections,
            "manifests": manifests,
            "missingObjectPaths": missingObjectPaths,
            "unregisteredHfObjectPaths": unregisteredHfObjectPaths,
            "brokenBlogRefs": brokenBlogRefs,
            "unreferenced": unreferenced,
            "errors": orderedErrors,
        }
    )
    return MediaCensus(
        objectCount=len(objects),
        aliasCount=len(aliases),
        postCount=len(posts),
        collectionCount=len(collections),
        manifestCount=len(manifests),
        missingObjectPaths=missingObjectPaths,
        unregisteredHfObjectPaths=unregisteredHfObjectPaths,
        brokenBlogRefs=tuple(sorted(set(brokenBlogRefs))),
        unreferencedObjectDigests=unreferenced,
        errors=orderedErrors,
        digest=digest,
    )
