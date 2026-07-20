"""Blog Markdown 전체를 source-bound virtual AST evidence로 검색한다."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from markdown_it import MarkdownIt
from markdown_it.token import Token

from ..canonical import canonicalDigest
from ..catalog.models import CatalogEvidence, CatalogState
from ..ids import blogBlockIds, logicalId
from .adapters import LexicalAdapterContext
from .lanes import LaneHit, LaneResult
from .models import QueryLane, RetrievedEvidence, UniverseQuery, normalizeSearchTerms

BLOG_AST_SCHEMA_VERSION = "du-blog-ast-v1"
_HTML_TAG_RE = re.compile(r"<[^>]+>")


@dataclass(frozen=True, slots=True)
class BlogAstBlock:
    schemaVersion: str
    blockId: str
    blockVersionId: str
    postObjectId: str
    resourceVersionId: str
    blockKind: str
    ordinal: int
    headingLineage: tuple[str, ...]
    lineStart: int
    lineEnd: int
    textDigest: str
    searchTerms: tuple[str, ...]
    attributes: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class BlogAstReport:
    postCount: int
    blockCount: int
    frontmatterFieldCount: int
    imageCount: int
    linkCount: int
    externalVideoCount: int
    staleResourceCount: int
    parseErrors: tuple[str, ...]
    digest: str


def _splitFrontmatter(text: str) -> tuple[dict[str, Any], str, int]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("frontmatter 시작 경계 누락")
    try:
        endIndex = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as exc:
        raise ValueError("frontmatter 종료 경계 누락") from exc
    loaded = yaml.safe_load("\n".join(lines[1:endIndex])) or {}
    if not isinstance(loaded, dict):
        raise ValueError("frontmatter 최상위 값이 dict가 아님")
    return loaded, "\n".join(lines[endIndex + 1 :]), endIndex + 1


def _inlineText(token: Token) -> str:
    if token.type != "inline":
        return token.content
    values = []
    for child in token.children or ():
        if child.type in {"text", "code_inline"}:
            values.append(child.content)
        elif child.type in {"softbreak", "hardbreak"}:
            values.append(" ")
        elif child.type == "image":
            values.append(child.content)
    return "".join(values).strip()


def _serializeFrontmatter(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


class BlogAstIndex:
    """현재 Git byte를 catalog resource digest와 맞춘 process-local AST index."""

    def __init__(self, repoRoot: Path, catalog: CatalogState):
        self.repoRoot = repoRoot.resolve()
        self.catalog = catalog
        self.blocks: tuple[BlogAstBlock, ...] = ()
        self.report = BlogAstReport(0, 0, 0, 0, 0, 0, 0, (), "")
        self._blockById: dict[str, BlogAstBlock] = {}
        self._evidenceById: dict[str, CatalogEvidence] = {}
        self._postings: dict[str, set[str]] = {}
        self._build()

    @staticmethod
    def _block(
        *,
        postObjectId: str,
        resourceVersionId: str,
        blockKind: str,
        ordinal: int,
        headingLineage: tuple[str, ...],
        lineStart: int,
        lineEnd: int,
        text: str,
        attributes: tuple[tuple[str, str], ...] = (),
    ) -> BlogAstBlock:
        normalizedText = text.strip()
        textDigest = canonicalDigest({"kind": blockKind, "text": normalizedText})
        stableKey = f"{blockKind.casefold()}:{ordinal}"
        blockId, blockVersionId = blogBlockIds(
            postObjectId,
            headingLineage,
            stableKey,
            textDigest,
        )
        return BlogAstBlock(
            schemaVersion=BLOG_AST_SCHEMA_VERSION,
            blockId=blockId,
            blockVersionId=blockVersionId,
            postObjectId=postObjectId,
            resourceVersionId=resourceVersionId,
            blockKind=blockKind,
            ordinal=ordinal,
            headingLineage=headingLineage,
            lineStart=lineStart,
            lineEnd=lineEnd,
            textDigest=textDigest,
            searchTerms=normalizeSearchTerms(normalizedText),
            attributes=tuple(sorted(attributes)),
        )

    def _parsePost(
        self,
        *,
        postObjectId: str,
        resourceVersionId: str,
        text: str,
    ) -> tuple[BlogAstBlock, ...]:
        frontmatter, body, bodyOffset = _splitFrontmatter(text)
        blocks: list[BlogAstBlock] = []
        ordinalByScope: dict[tuple[tuple[str, ...], str], int] = {}
        headingStack: list[str] = []

        def append(
            kind: str,
            value: str,
            *,
            lineStart: int,
            lineEnd: int,
            lineage: tuple[str, ...] | None = None,
            attributes: tuple[tuple[str, str], ...] = (),
        ) -> None:
            activeLineage = tuple(headingStack) if lineage is None else lineage
            scope = (activeLineage, kind)
            ordinal = ordinalByScope.get(scope, 0)
            ordinalByScope[scope] = ordinal + 1
            blocks.append(
                self._block(
                    postObjectId=postObjectId,
                    resourceVersionId=resourceVersionId,
                    blockKind=kind,
                    ordinal=ordinal,
                    headingLineage=activeLineage,
                    lineStart=lineStart,
                    lineEnd=lineEnd,
                    text=value,
                    attributes=attributes,
                )
            )

        for key in sorted(frontmatter):
            value = _serializeFrontmatter(frontmatter[key])
            append(
                "FRONTMATTER_FIELD",
                f"{key} {value}",
                lineStart=1,
                lineEnd=bodyOffset,
                lineage=(),
                attributes=(("field", str(key)),),
            )
            if key == "youtubeId" and str(frontmatter[key] or "").strip():
                append(
                    "EXTERNAL_VIDEO",
                    f"YouTube {frontmatter[key]}",
                    lineStart=1,
                    lineEnd=bodyOffset,
                    lineage=(),
                    attributes=(("provider", "YOUTUBE"), ("externalId", str(frontmatter[key]).strip())),
                )

        parser = MarkdownIt("commonmark").enable("table")
        tokens = parser.parse(body)
        index = 0
        while index < len(tokens):
            token = tokens[index]
            lineMap = token.map or [0, 0]
            lineStart = bodyOffset + int(lineMap[0]) + 1
            lineEnd = bodyOffset + int(lineMap[1])
            if token.type == "heading_open" and index + 1 < len(tokens):
                inline = tokens[index + 1]
                title = _inlineText(inline)
                level = int(token.tag[1])
                headingStack = headingStack[: level - 1]
                while len(headingStack) < level - 1:
                    headingStack.append("")
                headingStack.append(title)
                append(
                    "HEADING",
                    title,
                    lineStart=lineStart,
                    lineEnd=lineEnd,
                    attributes=(("level", str(level)),),
                )
            elif token.type == "paragraph_open" and index + 1 < len(tokens):
                inline = tokens[index + 1]
                append("PARAGRAPH", _inlineText(inline), lineStart=lineStart, lineEnd=lineEnd)
                for child in inline.children or ():
                    if child.type == "image":
                        append(
                            "IMAGE",
                            f"{child.content} {child.attrGet('src') or ''}",
                            lineStart=lineStart,
                            lineEnd=lineEnd,
                            attributes=(
                                ("alt", child.content),
                                ("src", child.attrGet("src") or ""),
                                ("title", child.attrGet("title") or ""),
                            ),
                        )
                    elif child.type == "link_open":
                        href = child.attrGet("href") or ""
                        append(
                            "LINK",
                            href,
                            lineStart=lineStart,
                            lineEnd=lineEnd,
                            attributes=(("href", href),),
                        )
            elif token.type in {"fence", "code_block"}:
                append(
                    "CODE_BLOCK",
                    token.content,
                    lineStart=lineStart,
                    lineEnd=lineEnd,
                    attributes=(("language", token.info.strip()),),
                )
            elif token.type == "tr_open":
                values = []
                cursor = index + 1
                while cursor < len(tokens) and tokens[cursor].type != "tr_close":
                    if tokens[cursor].type == "inline":
                        values.append(_inlineText(tokens[cursor]))
                    cursor += 1
                append("TABLE_ROW", " | ".join(values), lineStart=lineStart, lineEnd=lineEnd)
            elif token.type == "html_block":
                append(
                    "HTML_BLOCK",
                    _HTML_TAG_RE.sub(" ", token.content),
                    lineStart=lineStart,
                    lineEnd=lineEnd,
                )
            index += 1
        return tuple(blocks)

    def _build(self) -> None:
        resourceByVersion = {item.resourceVersionId: item for item in self.catalog.resources}
        blogObjects = tuple(
            item
            for item in self.catalog.objects
            if item.objectKind == "BLOG_POST"
            and len(item.resourceRefs) == 1
            and resourceByVersion[item.resourceRefs[0]].sourceKind == "GIT_BLOG"
        )
        blocks = []
        errors = []
        stale = 0
        for obj in blogObjects:
            resource = resourceByVersion[obj.resourceRefs[0]]
            locator = dict(resource.locator)
            path = self.repoRoot / locator["path"]
            try:
                raw = path.read_bytes()
                if hashlib.sha256(raw).hexdigest() != resource.contentDigest:
                    stale += 1
                    continue
                blocks.extend(
                    self._parsePost(
                        postObjectId=obj.objectId,
                        resourceVersionId=resource.resourceVersionId,
                        text=raw.decode("utf-8"),
                    )
                )
            except Exception as exc:
                errors.append(f"{locator.get('path', obj.objectId)}:{type(exc).__name__}")
        self.blocks = tuple(sorted(blocks, key=lambda item: (item.postObjectId, item.lineStart, item.blockId)))
        self._blockById = {item.blockId: item for item in self.blocks}
        for block in self.blocks:
            for term in block.searchTerms:
                self._postings.setdefault(term, set()).add(block.blockId)
            resource = resourceByVersion[block.resourceVersionId]
            selector = (
                ("astPath", f"/blocks/{block.blockId}"),
                ("blockKind", block.blockKind),
                ("lineStart", str(block.lineStart)),
                ("lineEnd", str(block.lineEnd)),
            )
            locator = resource.locator + selector
            evidenceId = logicalId(
                "query-evidence",
                (block.postObjectId, block.resourceVersionId, selector, block.textDigest),
            )
            self._evidenceById[evidenceId] = CatalogEvidence(
                evidenceId=evidenceId,
                objectId=block.postObjectId,
                resourceVersionId=block.resourceVersionId,
                sourceKind=resource.sourceKind,
                sourceRef=resource.sourceRef,
                sourceRevision=resource.sourceRevision,
                locator=locator,
                selector=selector,
                contentDigest=resource.contentDigest,
                retrievedAt=resource.observedAt,
                visibility=resource.visibility,
                licenseRef=resource.licenseRef,
                quoteDigest=block.textDigest,
            )
        counts = {
            kind: sum(item.blockKind == kind for item in self.blocks)
            for kind in ("FRONTMATTER_FIELD", "IMAGE", "LINK", "EXTERNAL_VIDEO")
        }
        base = BlogAstReport(
            postCount=len(blogObjects),
            blockCount=len(self.blocks),
            frontmatterFieldCount=counts["FRONTMATTER_FIELD"],
            imageCount=counts["IMAGE"],
            linkCount=counts["LINK"],
            externalVideoCount=counts["EXTERNAL_VIDEO"],
            staleResourceCount=stale,
            parseErrors=tuple(sorted(errors)),
            digest="",
        )
        self.report = BlogAstReport(
            postCount=base.postCount,
            blockCount=base.blockCount,
            frontmatterFieldCount=base.frontmatterFieldCount,
            imageCount=base.imageCount,
            linkCount=base.linkCount,
            externalVideoCount=base.externalVideoCount,
            staleResourceCount=base.staleResourceCount,
            parseErrors=base.parseErrors,
            digest=canonicalDigest(base),
        )

    def search(self, query: UniverseQuery, context: LexicalAdapterContext) -> LaneResult:
        terms = tuple(item for item in query.searchTerms if len(item) >= 2)
        blockScores: dict[str, float] = {}
        matchedTerms: dict[str, set[str]] = {}
        blockCount = max(len(self.blocks), 1)
        for term in terms:
            postings = self._postings.get(term, ())
            if not postings:
                continue
            inverseFrequency = math.log1p(blockCount / len(postings))
            for blockId in postings:
                block = self._blockById[blockId]
                if block.postObjectId not in context.objectById:
                    continue
                blockScores[blockId] = blockScores.get(blockId, 0.0) + inverseFrequency
                matchedTerms.setdefault(blockId, set()).add(term)
        bestByPost: dict[str, str] = {}
        for blockId in sorted(blockScores, key=lambda item: (-blockScores[item], item)):
            postId = self._blockById[blockId].postObjectId
            bestByPost.setdefault(postId, blockId)
        ordered = tuple(sorted(bestByPost.values(), key=lambda item: (-blockScores[item], item)))
        selected = ordered[: query.budget.lexicalLimit]
        maxScore = blockScores[ordered[0]] if ordered else 1.0
        evidenceByBlock = {
            dict(item.selector)["astPath"].removeprefix("/blocks/"): item for item in self._evidenceById.values()
        }
        hits = tuple(
            LaneHit(
                candidateRef=self._blockById[blockId].postObjectId,
                candidateKind="OBJECT",
                laneScore=blockScores[blockId] / maxScore,
                reasonCodes=tuple(
                    sorted(
                        {
                            f"BLOG_AST:{self._blockById[blockId].blockKind}",
                            *(f"TERM:{term}" for term in matchedTerms[blockId]),
                        }
                    )
                ),
                evidenceOverride=(evidenceByBlock[blockId],),
            )
            for blockId in selected
        )
        return LaneResult(
            lane=QueryLane.LEXICAL,
            hits=hits,
            candidateCount=len(ordered),
            withheldCount=0,
            truncated=len(ordered) > len(selected),
            reasonCode="LIMIT" if len(ordered) > len(selected) else ("COMPLETE" if hits else "NO_TERM_MATCH"),
        )

    def verifyRetrieved(self, retrieved: RetrievedEvidence) -> bool:
        return (
            retrieved.candidateKind == "OBJECT"
            and self._evidenceById.get(retrieved.evidence.evidenceId) == retrieved.evidence
            and retrieved.candidateRef == retrieved.evidence.objectId
        )
