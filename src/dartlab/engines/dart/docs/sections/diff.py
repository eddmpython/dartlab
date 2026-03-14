"""sections DataFrame 위 기간간 텍스트 diff.

sections 수평화 DataFrame(topic × period)에서 인접 기간 텍스트 변화를 감지한다.
060-003 실험으로 검증된 hash 기반 비교 + difflib 줄 단위 세부 diff.

사용법::

    from dartlab.engines.dart.docs.sections.diff import sectionsDiff, topicDiff

    df = sectionsDiff(sections)
    detail = topicDiff(sections, "사업의 개요", "2025", "2024")
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

import polars as pl

_PERIOD_RE = re.compile(r"^\d{4}(Q[1-4])?$")


def _isPeriodCol(name: str) -> bool:
    return bool(_PERIOD_RE.fullmatch(name))


def _periodCols(df: pl.DataFrame) -> list[str]:
    return [c for c in df.columns if _isPeriodCol(c)]


def _textHash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:12]


@dataclass
class DiffEntry:
    """하나의 topic에 대한 인접 기간 변화 정보."""

    topic: str
    chapter: str | None
    fromPeriod: str
    toPeriod: str
    status: str
    fromLen: int
    toLen: int


@dataclass
class DiffSummary:
    """topic별 변화 요약."""

    topic: str
    chapter: str | None
    totalPeriods: int
    changedCount: int
    stableCount: int

    @property
    def changeRate(self) -> float:
        if self.totalPeriods <= 1:
            return 0.0
        return self.changedCount / (self.totalPeriods - 1)


@dataclass
class DiffResult:
    """전체 diff 결과."""

    entries: list[DiffEntry] = field(default_factory=list)
    summaries: list[DiffSummary] = field(default_factory=list)

    @property
    def totalChanges(self) -> int:
        return len(self.entries)

    def topChanged(self, n: int = 10) -> list[DiffSummary]:
        return sorted(
            self.summaries, key=lambda s: s.changeRate, reverse=True,
        )[:n]

    def stable(self) -> list[DiffSummary]:
        return [s for s in self.summaries if s.changedCount == 0]


def sectionsDiff(sections: pl.DataFrame) -> DiffResult:
    """sections DataFrame에서 기간간 변화를 감지한다.

    Args:
        sections: topic(행) × period(열) DataFrame. chapter 컬럼 있으면 활용.

    Returns:
        DiffResult — entries(변화 지점 목록) + summaries(topic별 요약).
    """
    periods = _periodCols(sections)
    if len(periods) < 2:
        return DiffResult()

    hasChapter = "chapter" in sections.columns
    entries: list[DiffEntry] = []
    summaries: list[DiffSummary] = []

    for row in sections.iter_rows(named=True):
        topic = row.get("topic", "")
        chapter = row.get("chapter") if hasChapter else None
        if not topic:
            continue

        prevHash: str | None = None
        prevPeriod: str | None = None
        changedCount = 0
        totalPeriods = 0

        for period in periods:
            text = row.get(period)
            if text is None:
                continue
            totalPeriods += 1
            curHash = _textHash(str(text))

            if prevHash is not None and prevPeriod is not None:
                if curHash != prevHash:
                    changedCount += 1
                    entries.append(DiffEntry(
                        topic=topic,
                        chapter=chapter,
                        fromPeriod=prevPeriod,
                        toPeriod=period,
                        status="CHANGED",
                        fromLen=len(str(row.get(prevPeriod, ""))),
                        toLen=len(str(text)),
                    ))

            prevHash = curHash
            prevPeriod = period

        summaries.append(DiffSummary(
            topic=topic,
            chapter=chapter,
            totalPeriods=totalPeriods,
            changedCount=changedCount,
            stableCount=max(0, totalPeriods - 1 - changedCount),
        ))

    return DiffResult(entries=entries, summaries=summaries)


@dataclass
class LineDiff:
    """줄 단위 diff 결과."""

    fromPeriod: str
    toPeriod: str
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    kept: list[str] = field(default_factory=list)

    @property
    def totalLines(self) -> int:
        return len(self.added) + len(self.removed) + len(self.kept)


def topicDiff(
    sections: pl.DataFrame,
    topic: str,
    fromPeriod: str,
    toPeriod: str,
) -> LineDiff | None:
    """특정 topic의 두 기간 텍스트를 줄 단위로 diff한다.

    Args:
        sections: topic(행) × period(열) DataFrame.
        topic: diff할 topic명.
        fromPeriod: 이전 기간 (예: "2024").
        toPeriod: 이후 기간 (예: "2025").

    Returns:
        LineDiff 또는 None (해당 topic/기간 데이터 없을 때).
    """
    topicCol = "topic"
    if topicCol not in sections.columns:
        return None
    if fromPeriod not in sections.columns or toPeriod not in sections.columns:
        return None

    filtered = sections.filter(pl.col(topicCol) == topic)
    if filtered.height == 0:
        return None

    fromText = filtered.item(0, fromPeriod)
    toText = filtered.item(0, toPeriod)

    if fromText is None and toText is None:
        return None

    fromLines = str(fromText or "").splitlines()
    toLines = str(toText or "").splitlines()

    added: list[str] = []
    removed: list[str] = []
    kept: list[str] = []

    import difflib
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
        None, fromLines, toLines,
    ).get_opcodes():
        if tag == "equal":
            kept.extend(fromLines[i1:i2])
        elif tag == "insert":
            added.extend(toLines[j1:j2])
        elif tag == "delete":
            removed.extend(fromLines[i1:i2])
        elif tag == "replace":
            removed.extend(fromLines[i1:i2])
            added.extend(toLines[j1:j2])

    return LineDiff(
        fromPeriod=fromPeriod,
        toPeriod=toPeriod,
        added=added,
        removed=removed,
        kept=kept,
    )
