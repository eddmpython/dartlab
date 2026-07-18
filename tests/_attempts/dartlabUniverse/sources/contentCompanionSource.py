"""블로그, 카드, issue, podcast companion 파일을 pattern 독립적으로 열거한다."""

from __future__ import annotations

import fnmatch
import hashlib
from pathlib import Path

from ..canonical import CompanionCensus, CompanionRecord, canonicalDigest

_KNOWN_PATTERNS = (
    ("brief.json", "BRIEF"),
    ("plan.json", "PLAN"),
    ("CREDITS.md", "CREDITS"),
    ("cards.plan.json", "CARDS_PLAN"),
    ("carousel*.yaml", "CAROUSEL"),
    ("carousel*.yml", "CAROUSEL"),
    ("episode.yaml", "PODCAST_EPISODE"),
    ("published.json", "PUBLISHED_RECEIPT"),
    ("youtube.md", "YOUTUBE_NOTE"),
    ("imagegen-extract.json", "IMAGEGEN_EXTRACT"),
    ("script.md", "PODCAST_SCRIPT"),
    ("sourceDoc.md", "PODCAST_SOURCE"),
)
_MEDIA_SUFFIXES = frozenset({".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"})


def _companionKind(relativeToOwner: Path) -> str:
    name = relativeToOwner.name
    for pattern, kind in _KNOWN_PATTERNS:
        if fnmatch.fnmatchcase(name, pattern):
            return kind
    if relativeToOwner.suffix.lower() in _MEDIA_SUFFIXES or "assets" in relativeToOwner.parts:
        return "LOCAL_MEDIA_STAGE"
    return "UNCLASSIFIED_COMPANION"


def _ownerDirectories(root: Path) -> tuple[Path, ...]:
    owners = {path.parent for path in root.glob("[0-9][0-9]-*/*/index.md")}
    for path in root.glob("_issues/*"):
        if path.is_dir():
            owners.add(path)
    for path in root.glob("_podcasts/episodes/*"):
        if path.is_dir():
            owners.add(path)
    return tuple(sorted(owners))


def enumerateContentCompanions(root: Path) -> CompanionCensus:
    """콘텐츠 owner directory 안의 index 외 모든 파일을 분류한다.

    Args:
        root: repository의 `blog` directory.

    Returns:
        알려진 companion과 unknown terminal 분류.

    Raises:
        FileNotFoundError: blog root가 없을 때.

    Example:
        ``enumerateContentCompanions(repoRoot / "blog")``.
    """
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    records = []
    unknown = []
    for owner in _ownerDirectories(root):
        ownerPath = owner.relative_to(root).as_posix()
        for path in sorted(item for item in owner.rglob("*") if item.is_file()):
            relativeToOwner = path.relative_to(owner)
            if relativeToOwner.as_posix() == "index.md" or "__pycache__" in relativeToOwner.parts:
                continue
            kind = _companionKind(relativeToOwner)
            relativePath = path.relative_to(root).as_posix()
            records.append(
                CompanionRecord(
                    relativePath=relativePath,
                    ownerPath=ownerPath,
                    kind=kind,
                    contentDigest=hashlib.sha256(path.read_bytes()).hexdigest(),
                )
            )
            if kind == "UNCLASSIFIED_COMPANION":
                unknown.append(relativePath)
    orderedRecords = tuple(sorted(records, key=lambda record: record.relativePath))
    orderedUnknown = tuple(sorted(unknown))
    return CompanionCensus(
        records=orderedRecords,
        unknownPaths=orderedUnknown,
        digest=canonicalDigest({"records": orderedRecords, "unknownPaths": orderedUnknown}),
    )
