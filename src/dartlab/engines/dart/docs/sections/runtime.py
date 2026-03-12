"""학습된 rules 기반 sections 수평화 runtime."""

from __future__ import annotations

import re

from dartlab.engines.dart.docs.sections.artifacts import loadProjectionRules

_RE_SPLIT_SUFFIX = re.compile(r" \[\d+/\d+\]$")
_RE_MAJOR_HEADING = re.compile(r"^([가-힣])\.\s*(.+)$")
_CHAPTER_BY_MAJOR = {
    1: "I",
    2: "II",
    3: "III",
    4: "IV",
    5: "V",
    6: "VI",
    7: "VII",
    8: "VIII",
    9: "IX",
    10: "X",
    11: "XI",
    12: "XII",
}
_CHAPTER_II_SPLIT_SOURCE = "주요제품및원재료등"
_CHAPTER_II_SPLIT_FALLBACK_TARGETS = ("productService", "rawMaterial")


def chapterFromMajorNum(majorNum: int) -> str | None:
    return _CHAPTER_BY_MAJOR.get(majorNum)


def baseChunkPath(path: str) -> str:
    return _RE_SPLIT_SUFFIX.sub("", path)


def chapterTeacherTopics(rows: list[dict[str, object]]) -> dict[str, set[str]]:
    teacher: dict[str, set[str]] = {}
    for row in rows:
        chapter = row["chapter"]
        topic = row["topic"]
        if not isinstance(chapter, str) or not isinstance(topic, str):
            continue
        teacher.setdefault(chapter, set()).add(topic)
    return teacher


def projectionSuppressedTopics() -> dict[str, set[str]]:
    rules = loadProjectionRules("chapterII")
    return {"II": set(rules.keys())}


def splitByMajorHeading(text: str) -> list[tuple[str, str]]:
    lines = [line.rstrip() for line in text.splitlines()]
    segments: list[tuple[str, list[str]]] = []
    currentLabel = "(root)"
    currentLines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _RE_MAJOR_HEADING.match(stripped):
            if currentLines:
                segments.append((currentLabel, currentLines))
            currentLabel = stripped
            currentLines = []
            continue
        currentLines.append(stripped)

    if currentLines:
        segments.append((currentLabel, currentLines))

    return [(label, "\n".join(body).strip()) for label, body in segments if body]


def extractSemanticUnits(topic: str, text: str) -> list[tuple[str, str]]:
    if topic in {"segmentOverview", "segmentFinancialSummary", "riskDerivative"}:
        return splitByMajorHeading(text)
    return []


def _routeChapterIISegment(sourceTopic: str, label: str, body: str) -> str | None:
    joined = f"{label}\n{body}"
    if sourceTopic != _CHAPTER_II_SPLIT_SOURCE:
        return None
    if "원재료" in joined or "생산설비" in joined:
        return "rawMaterial"
    if "제품" in joined or "서비스" in joined:
        return "productService"
    return None


def applyProjections(
    rows: list[dict[str, object]],
    teacherTopics: dict[str, set[str]],
) -> list[dict[str, object]]:
    if not rows:
        return rows

    rules = loadProjectionRules("chapterII")
    if not rules:
        return rows

    out = list(rows)
    existing = {
        (row["chapter"], row["topic"])
        for row in rows
        if isinstance(row.get("chapter"), str) and isinstance(row.get("topic"), str)
    }
    splitBuffers: dict[tuple[str, str], list[str]] = {}

    for row in rows:
        chapter = row.get("chapter")
        topic = row.get("topic")
        text = row.get("text")
        if chapter != "II" or not isinstance(topic, str) or not isinstance(text, str):
            continue

        if topic == _CHAPTER_II_SPLIT_SOURCE:
            segments = splitByMajorHeading(text) or [("(root)", text)]
            matchedTargets: set[str] = set()
            for label, body in segments:
                target = _routeChapterIISegment(topic, label, body)
                if not target or target not in teacherTopics.get("II", set()):
                    continue
                splitBuffers.setdefault((chapter, target), []).append(body)
                matchedTargets.add(target)
            for target in _CHAPTER_II_SPLIT_FALLBACK_TARGETS:
                if target not in teacherTopics.get("II", set()) or target in matchedTargets:
                    continue
                splitBuffers.setdefault((chapter, target), []).append(text)
            continue

        for target in rules.get(topic, []):
            if target not in teacherTopics.get("II", set()):
                continue
            key = (chapter, target)
            if key in existing:
                continue
            out.append(
                {
                    "chapter": chapter,
                    "topic": target,
                    "text": text,
                    "majorNum": row.get("majorNum"),
                    "orderSeq": row.get("orderSeq"),
                    "sourceTopic": topic,
                    "projectionKind": "directRule",
                }
            )
            existing.add(key)

    for (chapter, target), bodies in splitBuffers.items():
        key = (chapter, target)
        if key in existing or not bodies:
            continue
        out.append(
            {
                "chapter": chapter,
                "topic": target,
                "text": "\n".join(bodies),
                "majorNum": 2,
                "orderSeq": 0,
                "sourceTopic": _CHAPTER_II_SPLIT_SOURCE,
                "projectionKind": "headingRule",
            }
        )
        existing.add(key)

    return out
