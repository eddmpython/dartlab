"""블로그 frontmatter와 본문 구조를 손실 없이 metadata census한다."""

from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from ..canonical import BlogCensus, BlogPostRecord, canonicalDigest

_FRONTMATTER_BOUNDARY = "---"
_MARKDOWN_IMAGE_RE = re.compile(r"!\[[^]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")
_MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^]]+\]\(([^)\s]+)(?:\s+[^)]*)?\)")
_HEADING_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$", re.MULTILINE)
_FENCE_RE = re.compile(r"^\s*```", re.MULTILINE)
_IMAGE_FIELDS = ("ogImage", "cardPreview", "thumbnail", "cover", "image")


def _splitFrontmatter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FRONTMATTER_BOUNDARY:
        raise ValueError("frontmatter 시작 경계 누락")
    try:
        endIndex = next(index for index in range(1, len(lines)) if lines[index].strip() == _FRONTMATTER_BOUNDARY)
    except StopIteration as exc:
        raise ValueError("frontmatter 종료 경계 누락") from exc
    raw = "\n".join(lines[1:endIndex])
    loaded = yaml.safe_load(raw) or {}
    if not isinstance(loaded, dict):
        raise ValueError("frontmatter 최상위 값이 dict가 아님")
    return loaded, "\n".join(lines[endIndex + 1 :])


def _dateText(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _paragraphCount(body: str) -> int:
    count = 0
    inFence = False
    activeParagraph = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            inFence = not inFence
            activeParagraph = False
            continue
        structural = (
            inFence
            or not stripped
            or stripped.startswith(("#", "|", ">", "- ", "* ", "+ "))
            or bool(re.match(r"^\d+\.\s", stripped))
        )
        if structural:
            activeParagraph = False
            continue
        if not activeParagraph:
            count += 1
            activeParagraph = True
    return count


def _imageRefs(frontmatter: dict[str, Any], body: str) -> tuple[str, ...]:
    refs = set(_MARKDOWN_IMAGE_RE.findall(body))
    for field in _IMAGE_FIELDS:
        value = frontmatter.get(field)
        if isinstance(value, str) and value.strip():
            refs.add(value.strip())
    return tuple(sorted(refs))


def enumerateBlog(root: Path) -> BlogCensus:
    """모든 정규 블로그 post의 frontmatter와 본문 구조를 parse한다.

    Args:
        root: repository의 `blog` directory.

    Returns:
        post record와 parse error가 포함된 census.

    Raises:
        FileNotFoundError: blog root가 없을 때.

    Example:
        ``enumerateBlog(repoRoot / "blog")``.
    """
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    posts = []
    errors = []
    for indexPath in sorted(root.glob("[0-9][0-9]-*/*/index.md")):
        relativePath = indexPath.relative_to(root).as_posix()
        try:
            rawBytes = indexPath.read_bytes()
            text = rawBytes.decode("utf-8")
            frontmatter, body = _splitFrontmatter(text)
            category = indexPath.parent.parent.name
            slug = indexPath.parent.name
            fenceCount = len(_FENCE_RE.findall(body))
            if fenceCount % 2:
                raise ValueError("code fence 불균형")
            youtubeId = str(frontmatter.get("youtubeId") or "").strip() or None
            posts.append(
                BlogPostRecord(
                    relativePath=relativePath,
                    category=category,
                    slug=slug,
                    title=str(frontmatter.get("title") or "").strip() or None,
                    publishedAt=_dateText(frontmatter.get("date") or frontmatter.get("publishedAt")),
                    youtubeId=youtubeId,
                    contentDigest=hashlib.sha256(rawBytes).hexdigest(),
                    frontmatterDigest=canonicalDigest(frontmatter),
                    headingCount=len(_HEADING_RE.findall(body)),
                    tableRowCount=len(_TABLE_ROW_RE.findall(body)),
                    codeBlockCount=fenceCount // 2,
                    paragraphCount=_paragraphCount(body),
                    imageRefs=_imageRefs(frontmatter, body),
                    linkRefs=tuple(sorted(set(_MARKDOWN_LINK_RE.findall(body)))),
                )
            )
        except Exception as exc:
            errors.append(f"{relativePath}:{type(exc).__name__}:{exc}")
    orderedPosts = tuple(sorted(posts, key=lambda post: post.relativePath))
    orderedErrors = tuple(sorted(errors))
    return BlogCensus(
        posts=orderedPosts,
        parseErrors=orderedErrors,
        digest=canonicalDigest({"posts": orderedPosts, "parseErrors": orderedErrors}),
    )
