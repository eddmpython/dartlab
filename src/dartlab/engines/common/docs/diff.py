"""sections DataFrame 위 기간간 텍스트 diff.

sections 수평화 DataFrame(topic × period)에서 인접 기간 텍스트 변화를 감지한다.
DART/EDGAR 공통으로 사용. 060-003 실험으로 검증된 hash 기반 비교 + difflib 줄 단위 세부 diff.

사용법::

    from dartlab.engines.common.docs.diff import sectionsDiff, topicDiff

    df = sectionsDiff(sections)
    detail = topicDiff(sections, "사업의 개요", "2025", "2024")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import polars as pl

_PERIOD_RE = re.compile(r"^\d{4}(Q[1-4])?$")


def _isPeriodCol(name: str) -> bool:
    return bool(_PERIOD_RE.fullmatch(name))


def _periodCols(df: pl.DataFrame) -> list[str]:
    return [c for c in df.columns if _isPeriodCol(c)]


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
            self.summaries,
            key=lambda s: s.changeRate,
            reverse=True,
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
    hasTopic = "topic" in sections.columns
    if not hasTopic:
        return DiffResult()

    # hash + len 벡터화 (md5 → xxhash64, ~6x 속도 향상)
    hashExprs = []
    lenExprs = []
    for p in periods:
        hashExprs.append(
            pl.when(pl.col(p).is_not_null())
            .then(pl.col(p).cast(pl.Utf8).hash())
            .otherwise(pl.lit(None, dtype=pl.UInt64))
            .alias(f"_h_{p}")
        )
        lenExprs.append(
            pl.when(pl.col(p).is_not_null())
            .then(pl.col(p).cast(pl.Utf8).str.len_bytes())
            .otherwise(pl.lit(None, dtype=pl.UInt32))
            .alias(f"_len_{p}")
        )

    work = sections.with_columns(hashExprs + lenExprs)

    # to_list()로 추출 (iter_rows(named=True) 대비 dict 오버헤드 제거)
    topicList = work.get_column("topic").to_list()
    chapterList = work.get_column("chapter").to_list() if hasChapter else [None] * work.height

    hashLists = {p: work.get_column(f"_h_{p}").to_list() for p in periods}
    lenLists = {p: work.get_column(f"_len_{p}").to_list() for p in periods}

    entries: list[DiffEntry] = []
    summaries: list[DiffSummary] = []

    for rowIdx in range(work.height):
        topic = topicList[rowIdx]
        if not topic:
            continue
        chapter = chapterList[rowIdx]

        prevHash: int | None = None
        prevPeriod: str | None = None
        changedCount = 0
        totalPeriods = 0

        for p in periods:
            h = hashLists[p][rowIdx]
            if h is None:
                continue
            totalPeriods += 1

            if prevHash is not None and prevPeriod is not None:
                if h != prevHash:
                    changedCount += 1
                    entries.append(
                        DiffEntry(
                            topic=topic,
                            chapter=chapter,
                            fromPeriod=prevPeriod,
                            toPeriod=p,
                            status="CHANGED",
                            fromLen=lenLists[prevPeriod][rowIdx] or 0,
                            toLen=lenLists[p][rowIdx] or 0,
                        )
                    )

            prevHash = h
            prevPeriod = p

        summaries.append(
            DiffSummary(
                topic=topic,
                chapter=chapter,
                totalPeriods=totalPeriods,
                changedCount=changedCount,
                stableCount=max(0, totalPeriods - 1 - changedCount),
            )
        )

    return DiffResult(entries=entries, summaries=summaries)


@dataclass
class CharPart:
    """글자 단위 diff 조각."""

    kind: str  # "equal" | "insert" | "delete"
    text: str


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
        None,
        fromLines,
        toLines,
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


def lineDiffDataFrame(
    sections: pl.DataFrame,
    topic: str,
    fromPeriod: str,
    toPeriod: str,
) -> pl.DataFrame | None:
    """줄 단위 diff를 인터리빙 순서 DataFrame으로 반환.

    Args:
        sections: topic(행) × period(열) DataFrame.
        topic: diff할 topic명.
        fromPeriod: 이전 기간.
        toPeriod: 이후 기간.

    Returns:
        DataFrame(line, status, text) 또는 None.
    """
    import difflib

    topicCol = "topic"
    if topicCol not in sections.columns:
        return None
    if fromPeriod not in sections.columns or toPeriod not in sections.columns:
        return None

    filtered = sections.filter(pl.col(topicCol) == topic)
    if filtered.height == 0:
        return None

    fromText = str(filtered.item(0, fromPeriod) or "")
    toText = str(filtered.item(0, toPeriod) or "")
    fromLines = fromText.splitlines()
    toLines = toText.splitlines()
    rows: list[dict[str, str | int]] = []
    lineNo = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
        None,
        fromLines,
        toLines,
    ).get_opcodes():
        if tag == "equal":
            for line in fromLines[i1:i2]:
                lineNo += 1
                rows.append({"line": lineNo, "status": " ", "text": line})
        elif tag == "insert":
            for line in toLines[j1:j2]:
                lineNo += 1
                rows.append({"line": lineNo, "status": "+", "text": line})
        elif tag == "delete":
            for line in fromLines[i1:i2]:
                lineNo += 1
                rows.append({"line": lineNo, "status": "-", "text": line})
        elif tag == "replace":
            for line in fromLines[i1:i2]:
                lineNo += 1
                rows.append({"line": lineNo, "status": "-", "text": line})
            for line in toLines[j1:j2]:
                lineNo += 1
                rows.append({"line": lineNo, "status": "+", "text": line})
    return pl.DataFrame(rows) if rows else None


def topicHistoryDataFrame(diffResult: DiffResult, topic: str) -> pl.DataFrame:
    """특정 topic의 기간별 변경 이력 DataFrame."""
    topicEntries = [e for e in diffResult.entries if e.topic == topic]
    if not topicEntries:
        return pl.DataFrame(
            {
                "fromPeriod": [],
                "toPeriod": [],
                "status": [],
                "fromLen": [],
                "toLen": [],
                "delta": [],
                "deltaRate": [],
            }
        )
    return pl.DataFrame(
        [
            {
                "fromPeriod": e.fromPeriod,
                "toPeriod": e.toPeriod,
                "status": e.status,
                "fromLen": e.fromLen,
                "toLen": e.toLen,
                "delta": e.toLen - e.fromLen,
                "deltaRate": round((e.toLen - e.fromLen) / e.fromLen, 3) if e.fromLen > 0 else None,
            }
            for e in topicEntries
        ]
    )


def diffSummaryDataFrame(diffResult: DiffResult) -> pl.DataFrame:
    """전체 topic 변경 요약 DataFrame."""
    return pl.DataFrame(
        [
            {
                "chapter": s.chapter,
                "topic": s.topic,
                "periods": s.totalPeriods,
                "changed": s.changedCount,
                "stable": s.stableCount,
                "changeRate": round(s.changeRate, 3),
            }
            for s in diffResult.summaries
        ]
    )


def charDiff(fromText: str, toText: str) -> list[CharPart]:
    """두 텍스트의 글자 단위 diff.

    diff-match-patch를 사용하여 변경된 글자 위치를 정확히 찾는다.
    semantic cleanup을 적용하여 사람이 읽기 좋은 단위로 정리한다.

    Args:
        fromText: 이전 텍스트.
        toText: 이후 텍스트.

    Returns:
        CharPart 리스트 — kind("equal"|"insert"|"delete") + text.
    """
    import diff_match_patch as dmp_module

    dmp = dmp_module.diff_match_patch()
    diffs = dmp.diff_main(fromText, toText)
    dmp.diff_cleanupSemantic(diffs)

    _OP_MAP = {0: "equal", 1: "insert", -1: "delete"}
    return [CharPart(kind=_OP_MAP[op], text=text) for op, text in diffs if text]
