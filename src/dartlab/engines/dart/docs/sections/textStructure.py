from __future__ import annotations

import hashlib
import re
from typing import Any, Literal

from dartlab.engines.dart.docs.sections.mapper import mapSectionTitle, stripSectionPrefix

TextNodeType = Literal["heading", "body"]

_MULTISPACE_RE = re.compile(r"\s+")
_TRAILING_PUNCT_RE = re.compile(r"[\s\-–—:：;,]+$")
_RE_ROMAN = re.compile(r"^(?:[IVXivx]+)\.\s+(.+)$")
_RE_NUMERIC = re.compile(r"^(?:\d+)\.\s+(.+)$")
_RE_KOREAN = re.compile(r"^(?:[가-힣])\.\s+(.+)$")
_RE_PAREN_NUM = re.compile(r"^\((\d+)\)\s*(.+)$")
_RE_PAREN_KOR = re.compile(r"^\(([가-힣])\)\s*(.+)$")
_RE_CIRCLED = re.compile(r"^([①-⑳])\s*(.+)$")
_RE_BRACKET = re.compile(r"^\[(.+?)\]$|^【(.+?)】$")
_RE_SHORT_PAREN = re.compile(r"^\(([^)]+)\)$")
_RE_HEADING_NOISE = re.compile(r"^(?:단위|주\d|참고|출처|비고)\b")
_RE_NONWORD = re.compile(r"[^0-9A-Za-z가-힣]+")
_RE_TEMPORAL_MARKER = re.compile(r"^(?:\d{4}년(?:\s*\d{1,2}월)?|\d{4}[./]\d{1,2})$")


def _clean_line(line: str) -> str:
    return line.replace("\u00a0", " ").replace("\t", " ").rstrip()


def _normalize_heading_text(text: str) -> str:
    cleaned = stripSectionPrefix(text.strip())
    cleaned = cleaned.strip("[]【】")
    m = _RE_SHORT_PAREN.match(cleaned)
    if m:
        cleaned = m.group(1).strip()
    cleaned = cleaned.replace("ㆍ", "·")
    cleaned = _MULTISPACE_RE.sub(" ", cleaned)
    cleaned = _TRAILING_PUNCT_RE.sub("", cleaned)
    return cleaned.strip()


def _heading_key(text: str) -> str:
    normalized = _normalize_heading_text(text)
    normalized = normalized.replace("·", "").replace("ㆍ", "")
    normalized = _RE_NONWORD.sub("", normalized)
    return normalized.strip()


def _canonical_heading_key(
    labelText: str,
    labelKey: str,
    *,
    level: int,
    topic: str | None,
) -> str:
    if level == 1 and isinstance(topic, str) and topic:
        mapped = mapSectionTitle(labelText)
        if mapped == topic:
            return f"@topic:{topic}"
    return labelKey


def _is_temporal_marker(text: str) -> bool:
    normalized = _normalize_heading_text(text)
    return bool(_RE_TEMPORAL_MARKER.fullmatch(normalized))


def _body_anchor(text: str) -> str:
    normalized = _MULTISPACE_RE.sub(" ", text.strip())
    if not normalized:
        return "empty"
    anchor = normalized[:96]
    return hashlib.md5(anchor.encode("utf-8")).hexdigest()[:12]


def _detect_heading(line: str) -> tuple[int, str, bool] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("|"):
        return None
    if len(stripped) > 120:
        return None

    m = _RE_BRACKET.match(stripped)
    if m:
        text = m.group(1) or m.group(2) or ""
        structural = not _is_temporal_marker(text)
        return (1, text.strip(), structural)

    m = _RE_ROMAN.match(stripped)
    if m:
        return (1, m.group(1).strip(), True)

    m = _RE_NUMERIC.match(stripped)
    if m:
        return (1, m.group(1).strip(), True)

    m = _RE_KOREAN.match(stripped)
    if m:
        return (2, m.group(1).strip(), True)

    m = _RE_PAREN_NUM.match(stripped)
    if m:
        return (3, m.group(2).strip(), True)

    m = _RE_PAREN_KOR.match(stripped)
    if m:
        return (4, m.group(2).strip(), True)

    m = _RE_CIRCLED.match(stripped)
    if m:
        return (4, m.group(2).strip(), True)

    m = _RE_SHORT_PAREN.match(stripped)
    if m:
        inner = m.group(1).strip()
        if inner and len(inner) <= 48 and not _RE_HEADING_NOISE.match(inner):
            structural = not _is_temporal_marker(inner)
            return (3, inner, structural)

    return None


def parseTextStructureWithState(
    text: str,
    *,
    sourceBlockOrder: int,
    topic: str | None = None,
    initialHeadings: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, Any]]]:
    nodes: list[dict[str, object]] = []
    stack: list[dict[str, object]] = [dict(item) for item in (initialHeadings or [])]
    bodyLines: list[str] = []
    segmentOrder = 0

    def flush_body() -> None:
        nonlocal bodyLines, segmentOrder
        body = "\n".join(bodyLines).strip()
        bodyLines = []
        if not body:
            return

        pathLabels = [str(item["label"]) for item in stack]
        pathKeys = [str(item["key"]) for item in stack if str(item["key"])]
        pathText = " > ".join(pathLabels) if pathLabels else None
        pathKey = " > ".join(pathKeys) if pathKeys else None
        parentPathKey = " > ".join(pathKeys[:-1]) if len(pathKeys) > 1 else None
        level = int(stack[-1]["level"]) if stack else 0
        anchor = _body_anchor(body)
        # Text row identity should follow outline path first.
        # Raw coarse block order is preserved separately as sourceBlockOrder.
        stableKeyBase = f"body|p:{pathKey}" if pathKey else f"body|lv:{level}|a:{anchor}"
        nodes.append(
            {
                "textNodeType": "body",
                "textStructural": True,
                "textLevel": level,
                "textPath": pathText,
                "textPathKey": pathKey,
                "textParentPathKey": parentPathKey,
                "segmentOrder": segmentOrder,
                "segmentKeyBase": stableKeyBase,
                "text": body,
            }
        )
        segmentOrder += 1

    for rawLine in text.splitlines():
        line = _clean_line(rawLine)
        stripped = line.strip()
        if not stripped:
            if bodyLines:
                bodyLines.append("")
            continue

        heading = _detect_heading(stripped)
        if heading is None:
            bodyLines.append(stripped)
            continue

        flush_body()
        level, label, structural = heading
        labelText = _normalize_heading_text(label)
        labelKey = _heading_key(label)
        stackKey = _canonical_heading_key(labelText, labelKey, level=level, topic=topic)
        redundantTopicAlias = (
            structural
            and bool(stack)
            and level == 1
            and str(stackKey).startswith("@topic:")
            and int(stack[-1]["level"]) == level
            and str(stack[-1]["key"]) == stackKey
        )

        if structural and not redundantTopicAlias:
            while stack and int(stack[-1]["level"]) >= level:
                stack.pop()
            stack.append({"level": level, "label": labelText, "key": stackKey})
            pathLabels = [str(item["label"]) for item in stack]
            pathKeys = [str(item["key"]) for item in stack if str(item["key"])]
            pathText = " > ".join(pathLabels) if pathLabels else None
            pathKey = " > ".join(pathKeys) if pathKeys else None
            parentPathKey = " > ".join(pathKeys[:-1]) if len(pathKeys) > 1 else None
            segmentKeyBase = f"heading|lv:{level}|p:{pathKey or stackKey}"
        else:
            currentPathKeys = [str(item["key"]) for item in stack if str(item["key"])]
            pathText = labelText
            keyPrefix = "@alias" if redundantTopicAlias else "@marker"
            pathKey = f"{keyPrefix}:{labelKey}"
            parentPathKey = " > ".join(currentPathKeys) if currentPathKeys else None
            segmentKind = "alias" if redundantTopicAlias else "marker"
            segmentKeyBase = f"heading|{segmentKind}|lv:{level}|p:{pathKey}"
        nodes.append(
            {
                "textNodeType": "heading",
                "textStructural": structural and not redundantTopicAlias,
                "textLevel": level,
                "textPath": pathText,
                "textPathKey": pathKey,
                "textParentPathKey": parentPathKey,
                "segmentOrder": segmentOrder,
                "segmentKeyBase": segmentKeyBase,
                "text": stripped,
            }
        )
        segmentOrder += 1

    flush_body()
    return nodes, [dict(item) for item in stack]


def parseTextStructure(
    text: str,
    *,
    sourceBlockOrder: int,
    topic: str | None = None,
) -> list[dict[str, object]]:
    nodes, _stack = parseTextStructureWithState(text, sourceBlockOrder=sourceBlockOrder, topic=topic)
    return nodes


__all__ = ["TextNodeType", "parseTextStructure", "parseTextStructureWithState"]
