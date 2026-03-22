"""공시뷰어 presentation layer.

Company.show()와 프론트엔드 사이의 변환 레이어.
sections 원본 데이터를 프론트엔드가 바로 렌더링할 수 있는 구조로 변환한다.

핵심:
- 블록 분류: finance / report / text / structured / raw_markdown
- finance topic은 sections 우회 → 속도 보장
- text 블록에 changeSummary + inline diff 포함
- 블록 메타데이터 (단위, 스케일, periods 등)
"""

from __future__ import annotations

import difflib
import hashlib
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

import polars as pl

if TYPE_CHECKING:
    from dartlab.engines.company.dart.company import Company

_PERIOD_RE = re.compile(r"^\d{4}(Q[1-4])?$")
_FINANCE_TOPICS = frozenset({"BS", "IS", "CIS", "CF", "SCE", "ratios"})
_MAX_DIFF_PAIRS = 40  # 충분히 크게 — 전체 변경 쌍
_MAX_ANNOTATE_PERIODS = 10  # 최대 몇 기간까지 blame 추적


def _isPeriod(name: str) -> bool:
    return bool(_PERIOD_RE.fullmatch(name))


def _periodCols(df: pl.DataFrame) -> list[str]:
    return [c for c in df.columns if _isPeriod(c)]


BlockKind = Literal["text", "structured", "raw_markdown", "finance", "report"]
TextSectionStatus = Literal["stable", "updated", "new", "stale"]
TextViewStatus = Literal["stable", "updated", "new"]
PeriodKind = Literal["annual", "quarterly"]
DiffChunkKind = Literal["same", "added", "removed"]


@dataclass
class BlockMeta:
    """블록 표시 메타데이터."""

    unit: str | None = None
    scale: str | None = None
    scaleDivisor: float = 1.0
    periods: list[str] = field(default_factory=list)
    rowCount: int = 0
    colCount: int = 0


@dataclass
class InlineDiff:
    """한 기간 쌍의 문장 수준 diff."""

    fromPeriod: str
    toPeriod: str
    additions: list[str] = field(default_factory=list)
    deletions: list[str] = field(default_factory=list)


@dataclass
class AnnotatedLine:
    """최신 텍스트의 한 줄 + blame + 변경 빈도."""

    text: str
    since: str  # 이 문장이 처음 등장한 기간
    frequency: int = 0  # 이 문장이 존재하는 기간 수
    totalPeriods: int = 0  # 전체 기간 수
    isHeading: bool = False

    @property
    def stability(self) -> str:
        """안정도: stable / recent / volatile."""
        if self.totalPeriods == 0:
            return "stable"
        ratio = self.frequency / self.totalPeriods
        if ratio >= 0.7:
            return "stable"
        if ratio >= 0.3:
            return "recent"
        return "volatile"


@dataclass
class ChangeDigestItem:
    """변경 요약 카드의 개별 항목."""

    kind: str  # "numeric", "added", "removed", "wording"
    text: str  # 표시 텍스트


@dataclass
class ChangeDigest:
    """최신 변경의 요약 카드."""

    fromPeriod: str
    toPeriod: str
    items: list[ChangeDigestItem] = field(default_factory=list)
    wordingCount: int = 0  # "외 N건 문구 수정"


@dataclass
class ChangeSummary:
    """text 블록의 기간간 변경 요약 + inline diff + annotated blame."""

    totalPeriods: int = 0
    changedPairs: int = 0
    latestChange: str | None = None
    changes: list[dict[str, str]] = field(default_factory=list)
    diffs: list[InlineDiff] = field(default_factory=list)
    annotated: list[AnnotatedLine] = field(default_factory=list)
    digest: ChangeDigest | None = None  # 변경 요약 카드


@dataclass
class ViewerBlock:
    """프론트엔드가 소비하는 블록 단위."""

    block: int
    kind: BlockKind
    source: str
    data: pl.DataFrame | None = None
    meta: BlockMeta = field(default_factory=BlockMeta)
    changeSummary: ChangeSummary | None = None
    rawMarkdown: dict[str, str] | None = None
    textType: str | None = None  # "heading" | "body" | None (non-text)
    textLevel: int | None = None  # sections textLevel (heading 계층 1~4)


@dataclass
class PeriodRef:
    """절대 기간 라벨의 canonical 표현."""

    label: str
    year: int
    quarter: int | None = None
    kind: PeriodKind = "annual"
    sortKey: int = 0


@dataclass
class ViewerDiffChunk:
    """선택 period 원문 위치에 맞춘 diff chunk."""

    kind: DiffChunkKind
    paragraphs: list[str] = field(default_factory=list)


@dataclass
class ViewerTextHeading:
    """body section을 위한 구조 anchor heading."""

    block: int
    text: str
    period: PeriodRef
    level: int = 0  # heading 계층 (1~4, 0=unknown)


@dataclass
class ViewerTextView:
    """특정 period snapshot과 직전 comparable period diff."""

    period: PeriodRef
    prevPeriod: PeriodRef | None = None
    body: str = ""
    status: TextViewStatus = "stable"
    diff: list[ViewerDiffChunk] = field(default_factory=list)
    digest: ChangeDigest | None = None


@dataclass
class ViewerTextTimelineEntry:
    """section 상단 timeline item."""

    period: PeriodRef
    prevPeriod: PeriodRef | None = None
    status: TextViewStatus = "stable"


@dataclass
class ViewerTextSection:
    """텍스트 전용 보고서의 본문 섹션."""

    id: str
    order: int
    bodyBlock: int
    headingPath: list[ViewerTextHeading] = field(default_factory=list)
    latest: ViewerTextView | None = None
    latestPeriod: PeriodRef | None = None
    firstPeriod: PeriodRef | None = None
    periodCount: int = 0
    status: TextSectionStatus = "stable"
    latestChange: str | None = None
    preview: str | None = None
    timeline: list[ViewerTextTimelineEntry] = field(default_factory=list)
    views: dict[str, ViewerTextView] = field(default_factory=dict)


@dataclass
class ViewerDocumentEntry:
    """textDocument의 통합 항목 — text section 또는 non-text block 참조."""

    kind: str  # "section" | "block_ref"
    order: int  # blockOrder 기반 정렬 키
    sectionId: str | None = None  # kind="section"일 때 — sections[].id
    blockRef: int | None = None  # kind="block_ref"일 때 — blocks[].block 번호
    blockKind: str | None = None  # "structured" | "finance" | "raw_markdown" 등


@dataclass
class ViewerTextDocument:
    """인터리브 문서 — text section과 non-text block을 원본 순서대로."""

    topic: str
    mode: str = "timeline_text"
    periods: list[PeriodRef] = field(default_factory=list)
    latestPeriod: PeriodRef | None = None
    firstPeriod: PeriodRef | None = None
    sectionCount: int = 0
    updatedCount: int = 0
    newCount: int = 0
    staleCount: int = 0
    stableCount: int = 0
    sections: list[ViewerTextSection] = field(default_factory=list)
    entries: list[ViewerDocumentEntry] = field(default_factory=list)


# ── 메인 진입점 ──


def viewerBlocks(company: Company, topic: str) -> list[ViewerBlock]:
    """topic의 모든 블록을 ViewerBlock 리스트로 반환."""
    if topic in _FINANCE_TOPICS:
        blk = _buildFinanceBlock(company, topic)
        return [blk] if blk else []

    sec = company.sections
    if sec is None:
        return []

    topicFrame = sec.filter(pl.col("topic") == topic)
    if topicFrame.is_empty():
        return []

    periodCols = _periodCols(topicFrame)
    blocks: list[ViewerBlock] = []

    if "blockOrder" not in topicFrame.columns:
        return []

    blockOrders = topicFrame["blockOrder"].unique().sort().to_list()

    for bo in blockOrders:
        boRows = topicFrame.filter(pl.col("blockOrder") == bo)
        bt = boRows["blockType"][0] if "blockType" in boRows.columns else "text"
        source = boRows["source"][0] if "source" in boRows.columns else "docs"

        if source == "finance":
            blk = _buildFinanceBlock(company, topic)
            if blk:
                blk.block = bo
                blocks.append(blk)
        elif source == "report":
            blk = _buildReportBlock(company, topic, bo)
            if blk:
                blocks.append(blk)
        elif bt == "text":
            blk = _buildTextBlock(boRows, bo, periodCols)
            if blk:
                blocks.append(blk)
        elif bt == "table":
            blk = _buildTableBlock(company, topic, topicFrame, bo, periodCols)
            if blk:
                blocks.append(blk)

    return blocks


def viewerTextDocument(topic: str, blocks: list[ViewerBlock]) -> ViewerTextDocument | None:
    """인터리브 문서 — text section과 non-text block을 원본 순서대로 구성.

    - body text block → ViewerTextSection (timeline/diff 포함)
    - heading block → 다음 body의 headingPath로 흡수
    - non-text block → ViewerDocumentEntry(kind="block_ref")로 원본 위치 보존
    - entries가 원본 blockOrder 순서를 그대로 유지
    """
    textBlocks = [b for b in blocks if b.kind == "text"]
    if not textBlocks:
        # text가 없어도 non-text block만으로 entries 구성 가능
        nonTextBlocks = [b for b in blocks if b.kind != "text"]
        if not nonTextBlocks:
            return None
        entries = [
            ViewerDocumentEntry(
                kind="block_ref",
                order=b.block,
                blockRef=b.block,
                blockKind=b.kind,
            )
            for b in sorted(nonTextBlocks, key=lambda item: item.block)
        ]
        return ViewerTextDocument(topic=topic, entries=entries)

    textPeriods = sorted(
        {period for block in textBlocks for period in _textPeriodMap(block).keys()},
        key=_periodSortKey,
    )
    if not textPeriods:
        return None

    topicLatestPeriod = textPeriods[-1]
    sections: list[ViewerTextSection] = []
    entries: list[ViewerDocumentEntry] = []
    pendingHeadings: list[ViewerBlock] = []

    for block in sorted(blocks, key=lambda item: item.block):
        if block.kind == "text" and block.textType == "heading":
            pendingHeadings.append(block)
            continue

        if block.kind == "text" and block.textType == "body":
            section = _buildTextSection(
                topic=topic,
                block=block,
                headingBlocks=pendingHeadings,
                order=len(sections),
                topicLatestPeriod=topicLatestPeriod,
            )
            if section is not None:
                sections.append(section)
                entries.append(
                    ViewerDocumentEntry(
                        kind="section",
                        order=block.block,
                        sectionId=section.id,
                    )
                )
            pendingHeadings = []
            continue

        # non-text block — 원본 위치에 block_ref entry 삽입
        if pendingHeadings:
            pendingHeadings = []
        entries.append(
            ViewerDocumentEntry(
                kind="block_ref",
                order=block.block,
                blockRef=block.block,
                blockKind=block.kind,
            )
        )

    if not sections and not entries:
        return None

    updatedCount = sum(1 for s in sections if s.status == "updated")
    newCount = sum(1 for s in sections if s.status == "new")
    staleCount = sum(1 for s in sections if s.status == "stale")
    stableCount = sum(1 for s in sections if s.status == "stable")

    return ViewerTextDocument(
        topic=topic,
        periods=[_periodRef(period) for period in sorted(textPeriods, key=_periodSortKey, reverse=True)],
        latestPeriod=_periodRef(textPeriods[-1]),
        firstPeriod=_periodRef(textPeriods[0]),
        sectionCount=len(sections),
        updatedCount=updatedCount,
        newCount=newCount,
        staleCount=staleCount,
        stableCount=stableCount,
        sections=sections,
        entries=entries,
    )


# ── Finance 블록 ──


def _buildFinanceBlock(company: Company, topic: str) -> ViewerBlock | None:
    """finance topic을 sections 우회하여 직접 로드."""
    df = company._showFinanceTopic(topic)
    if df is None or not isinstance(df, pl.DataFrame):
        return None

    if topic in {"IS", "BS", "CIS", "CF", "SCE"} and "계정명" in df.columns:
        df = company._cleanFinanceDataFrame(df, topic)

    periods = _periodCols(df)
    # 기간 역순 정렬 (최신 먼저)
    sortedPeriods = sorted(periods, key=_periodSortKey, reverse=True)
    nonPeriodCols = [c for c in df.columns if c not in periods]
    df = df.select(nonPeriodCols + sortedPeriods)
    periods = sortedPeriods
    scale, divisor = _detectScale(df, periods)

    return ViewerBlock(
        block=0,
        kind="finance",
        source="finance",
        data=df,
        meta=BlockMeta(
            unit="원",
            scale=scale,
            scaleDivisor=divisor,
            periods=periods,
            rowCount=df.height,
            colCount=len(df.columns),
        ),
    )


# ── Report 블록 ──


def _buildReportBlock(company: Company, topic: str, bo: int) -> ViewerBlock | None:
    """report source 블록."""
    df = company._showReportTopic(topic)
    if df is None or not isinstance(df, pl.DataFrame):
        return None

    periods = _periodCols(df)
    # 기간 역순 정렬 (최신 먼저) — finance/structured와 일관성
    sortedPeriods = sorted(periods, key=_periodSortKey, reverse=True)
    nonPeriodCols = [c for c in df.columns if c not in periods]
    df = df.select(nonPeriodCols + sortedPeriods)
    periods = sortedPeriods

    return ViewerBlock(
        block=bo,
        kind="report",
        source="report",
        data=df,
        meta=BlockMeta(
            periods=periods,
            rowCount=df.height,
            colCount=len(df.columns),
        ),
    )


# ── Text 블록 ──


def _classifyTextType(text: str) -> str:
    """text 블록을 heading(소제목) vs body(서술형)로 분류."""
    if not text or not text.strip():
        return "heading"
    lines = [l for l in text.strip().split("\n") if l.strip()]
    lineCount = len(lines)
    charCount = sum(len(l) for l in lines)

    if lineCount <= 2 and charCount <= 80:
        return "heading"
    return "body"


def _buildTextBlock(boRows: pl.DataFrame, bo: int, periodCols: list[str]) -> ViewerBlock | None:
    """text 블록. heading이면 changeSummary 없이, body면 전체 변경 분석."""
    keepCols = [c for c in periodCols if c in boRows.columns]
    nonNullCols = [c for c in keepCols if boRows[c].null_count() < boRows.height]
    if not nonNullCols:
        return None

    textDf = boRows.select(nonNullCols)

    # 최신 기간 텍스트로 heading/body 분류
    row = boRows.row(0, named=True)
    latestText = str(row.get(nonNullCols[-1], ""))
    textType = str(row.get("textNodeType") or "")
    if textType not in {"heading", "body"}:
        textType = _classifyTextType(latestText)
    if row.get("textStructural") is False and textType == "heading":
        textType = "body"

    # textLevel — sections 메타데이터에서 heading 계층 읽기
    rawLevel = row.get("textLevel")
    textLevel = int(rawLevel) if rawLevel is not None and rawLevel == rawLevel else None

    # heading이면 changeSummary 생성 안 함
    summary = _buildChangeSummary(boRows, nonNullCols) if textType == "body" else None

    return ViewerBlock(
        block=bo,
        kind="text",
        source="docs",
        data=textDf,
        meta=BlockMeta(
            periods=nonNullCols,
            rowCount=1,
            colCount=len(nonNullCols),
        ),
        changeSummary=summary,
        textType=textType,
        textLevel=textLevel,
    )


def _textPeriodMap(block: ViewerBlock) -> dict[str, str]:
    """text block의 period -> text 매핑."""
    if block.data is None or block.data.is_empty():
        return {}
    row = block.data.row(0, named=True)
    result: dict[str, str] = {}
    for key, value in row.items():
        if not _isPeriod(str(key)):
            continue
        if value is None:
            continue
        text = str(value).strip()
        if text:
            result[str(key)] = text
    return result


def _periodRef(period: str) -> PeriodRef:
    """기간 문자열을 canonical ref로 변환."""
    year, quarter = _periodSortKey(period)
    quarterVal = quarter if quarter < 5 else None
    return PeriodRef(
        label=period,
        year=year,
        quarter=quarterVal,
        kind="quarterly" if quarterVal is not None else "annual",
        sortKey=(year * 10) + quarter,
    )


def _selectNearestPeriodText(
    periodMap: dict[str, str], targetPeriod: str | None = None
) -> tuple[str | None, str | None]:
    """targetPeriod와 가장 가까운 텍스트를 반환한다.

    같은 기간 우선, 없으면 target 이하 가장 최근, 그래도 없으면 전체 최신.
    """
    if not periodMap:
        return (None, None)

    periods = sorted(periodMap.keys(), key=_periodSortKey)
    if targetPeriod is None:
        chosen = periods[-1]
        return (chosen, periodMap[chosen])

    if targetPeriod in periodMap:
        return (targetPeriod, periodMap[targetPeriod])

    targetKey = _periodSortKey(targetPeriod)
    previous = [period for period in periods if _periodSortKey(period) <= targetKey]
    chosen = previous[-1] if previous else periods[-1]
    return (chosen, periodMap[chosen])


def _classifyTextSectionStatus(
    firstPeriod: str,
    latestPeriod: str,
    periodCount: int,
    topicLatestPeriod: str,
    summary: ChangeSummary | None,
    latestViewStatus: TextViewStatus | None = None,
) -> TextSectionStatus:
    if latestPeriod != topicLatestPeriod:
        return "stale"
    if periodCount == 1 and firstPeriod == latestPeriod:
        return "new"
    if summary is None or summary.changedPairs == 0:
        return "updated" if latestViewStatus == "updated" else "stable"

    latestChangedTo = None
    if summary.digest is not None:
        latestChangedTo = summary.digest.toPeriod
    elif summary.changes:
        latestChangedTo = summary.changes[-1].get("to")

    if latestChangedTo == latestPeriod:
        return "updated"
    if latestViewStatus == "updated":
        return "updated"
    return "stable"


def _classifyTextViewStatus(
    *,
    currentText: str,
    prevText: str | None,
) -> TextViewStatus:
    if prevText is None:
        return "new"
    if currentText == prevText:
        return "stable"
    return "updated"


def _findPreviousComparablePeriod(periods: list[str], currentPeriod: str) -> str | None:
    """현재 period의 직전 동주기 period를 찾는다."""
    for period in reversed(periods):
        if _periodSortKey(period) >= _periodSortKey(currentPeriod):
            continue
        if _isSameReportType(period, currentPeriod):
            return period
    return None


def _appendDiffChunk(
    chunks: list[ViewerDiffChunk],
    kind: DiffChunkKind,
    paragraphs: list[str],
) -> None:
    if not paragraphs:
        return
    if chunks and chunks[-1].kind == kind:
        chunks[-1].paragraphs.extend(paragraphs)
        return
    chunks.append(ViewerDiffChunk(kind=kind, paragraphs=list(paragraphs)))


def _buildPositionAnchoredDiff(
    currentText: str,
    prevText: str | None,
) -> list[ViewerDiffChunk]:
    """선택 period 원문 위치 기준 paragraph diff."""
    currentLines = _splitSentences(currentText)
    if prevText is None:
        return [ViewerDiffChunk(kind="same", paragraphs=currentLines)] if currentLines else []

    previousLines = _splitSentences(prevText)
    matcher = difflib.SequenceMatcher(None, previousLines, currentLines, autojunk=False)
    chunks: list[ViewerDiffChunk] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            _appendDiffChunk(chunks, "same", currentLines[j1:j2])
        elif tag == "insert":
            _appendDiffChunk(chunks, "added", currentLines[j1:j2])
        elif tag == "delete":
            _appendDiffChunk(chunks, "removed", previousLines[i1:i2])
        elif tag == "replace":
            _appendDiffChunk(chunks, "removed", previousLines[i1:i2])
            _appendDiffChunk(chunks, "added", currentLines[j1:j2])

    return chunks


def _headingLevel(line: str) -> int:
    """한글 공시 heading 패턴에서 계층 레벨 추출. 0=unknown."""
    import re

    if re.match(r"^[IVX]+\.\s", line):
        return 1
    if re.match(r"^[가나다라마바사아자차카타파하]\.\s", line):
        return 1
    if re.match(r"^\[.+\]$", line) or re.match(r"^【.+】$", line):
        return 1
    if re.match(r"^\d+\.\s", line):
        return 2
    if re.match(r"^\(\d+\)\s", line) or re.match(r"^\([가-힣]\)\s", line):
        return 3
    if re.match(r"^[①②③④⑤⑥⑦⑧⑨⑩]\s", line):
        return 4
    return 0


def _extractInlineHeadingLines(text: str) -> tuple[list[str], str]:
    """body 앞머리의 짧은 heading line을 구조 anchor로 분리한다."""
    if not text or not text.strip():
        return ([], "")

    headings: list[str] = []
    bodyLines: list[str] = []
    bodyStarted = False

    for rawLine in text.splitlines():
        line = rawLine.strip()
        if not line:
            if bodyStarted:
                bodyLines.append("")
            continue
        if not bodyStarted and len(line) <= 72 and _HEADING_RE.match(line):
            headings.append(line)
            continue
        bodyStarted = True
        bodyLines.append(line)

    bodyText = "\n".join(bodyLines).strip()
    if not bodyText:
        return ([], text.strip())
    return (headings, bodyText)


def _buildTextView(
    *,
    period: str,
    periodMap: dict[str, str],
) -> ViewerTextView:
    """section의 한 period snapshot + 직전 동주기 diff."""
    orderedPeriods = sorted(periodMap.keys(), key=_periodSortKey)
    _inlineHeadings, body = _extractInlineHeadingLines(periodMap[period])
    prevPeriod = _findPreviousComparablePeriod(orderedPeriods, period)
    prevText = None
    if prevPeriod is not None:
        _prevInlineHeadings, prevText = _extractInlineHeadingLines(periodMap[prevPeriod])
    status = _classifyTextViewStatus(currentText=body, prevText=prevText)
    inlineDiff = (
        _computeInlineDiff(prevText, body, prevPeriod, period)
        if prevPeriod is not None and prevText is not None
        else None
    )

    return ViewerTextView(
        period=_periodRef(period),
        prevPeriod=_periodRef(prevPeriod) if prevPeriod is not None else None,
        body=body,
        status=status,
        diff=_buildPositionAnchoredDiff(body, prevText),
        digest=_buildDigest([inlineDiff]) if inlineDiff is not None else None,
    )


def _previewText(text: str | None, *, maxChars: int = 140) -> str | None:
    if text is None:
        return None
    paragraphs = _splitSentences(text)
    if not paragraphs:
        return None
    preview = " ".join(paragraphs[:2])
    if len(preview) <= maxChars:
        return preview
    return preview[: maxChars - 3].rstrip() + "..."


def _buildTextSection(
    *,
    topic: str,
    block: ViewerBlock,
    headingBlocks: list[ViewerBlock],
    order: int,
    topicLatestPeriod: str,
) -> ViewerTextSection | None:
    periodMap = _textPeriodMap(block)
    if not periodMap:
        return None

    periods = sorted(periodMap.keys(), key=_periodSortKey)
    latestPeriod = periods[-1]
    latestView = _buildTextView(period=latestPeriod, periodMap=periodMap)
    inlineHeadings, _ = _extractInlineHeadingLines(periodMap[latestPeriod])

    headingPath: list[ViewerTextHeading] = []
    for headingBlock in headingBlocks:
        headingPeriodMap = _textPeriodMap(headingBlock)
        chosenPeriod, headingText = _selectNearestPeriodText(headingPeriodMap, latestPeriod)
        if headingText is None or chosenPeriod is None:
            continue
        headingPath.append(
            ViewerTextHeading(
                block=headingBlock.block,
                text=headingText,
                period=_periodRef(chosenPeriod),
                level=headingBlock.textLevel or _headingLevel(headingText),
            )
        )
    for headingText in inlineHeadings:
        headingPath.append(
            ViewerTextHeading(
                block=block.block,
                text=headingText,
                period=_periodRef(latestPeriod),
                level=_headingLevel(headingText),
            )
        )

    timeline: list[ViewerTextTimelineEntry] = []
    views: dict[str, ViewerTextView] = {}
    for period in sorted(periodMap.keys(), key=_periodSortKey, reverse=True):
        view = _buildTextView(period=period, periodMap=periodMap)
        views[period] = view
        timeline.append(
            ViewerTextTimelineEntry(
                period=view.period,
                prevPeriod=view.prevPeriod,
                status=view.status,
            )
        )

    return ViewerTextSection(
        id=f"{topic}:{block.block}",
        order=order,
        bodyBlock=block.block,
        headingPath=headingPath,
        latest=latestView,
        latestPeriod=_periodRef(latestPeriod),
        firstPeriod=_periodRef(periods[0]),
        periodCount=len(periods),
        status=_classifyTextSectionStatus(
            firstPeriod=periods[0],
            latestPeriod=latestPeriod,
            periodCount=len(periods),
            topicLatestPeriod=topicLatestPeriod,
            summary=block.changeSummary,
            latestViewStatus=latestView.status,
        ),
        latestChange=block.changeSummary.latestChange if block.changeSummary else None,
        preview=_previewText(latestView.body),
        timeline=timeline,
        views=views,
    )


# ── 문장 분리 + Inline Diff ──

_SENT_SPLIT_RE = re.compile(
    r"(?<=[다음임됨함음음])\.(?:\s|$)|"
    r"\n"
)


def _normalizeTextLine(line: str) -> str:
    """공시 원문 줄 단위 정규화."""
    text = line.replace("\u00a0", " ").replace("\t", " ")
    return re.sub(r"\s+", " ", text).strip()


def _isStructuralHeadingLine(line: str) -> bool:
    """본문 내부의 구조 heading line 여부."""
    if not line:
        return False
    if len(line) > 88:
        return False
    return bool(re.match(r"^\[.+\]$|^【.+】$|^[IVX]+\.\s|^\d+\.\s|^[가-힣]\.\s|^\(\d+\)\s|^\([가-힣]\)\s", line))


def _splitSentences(text: str) -> list[str]:
    """공시 본문을 logical paragraph 단위로 분리한다.

    - 단순 줄바꿈은 문단 연결로 본다.
    - heading line은 diff 대상에서 제외한다.
    - 빈 줄에서 문단을 끊는다.
    """
    if not text or not text.strip():
        return []

    paragraphs: list[str] = []
    current: list[str] = []

    for rawLine in text.strip().split("\n"):
        line = _normalizeTextLine(rawLine)
        if not line:
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
            continue
        if _isStructuralHeadingLine(line):
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
            continue
        current.append(line)

    if current:
        paragraphs.append(" ".join(current).strip())

    return [paragraph for paragraph in paragraphs if paragraph]


def _wordLevelDiff(old: str, new: str) -> tuple[str, str]:
    """두 문장의 word-level diff — 변경 부분만 추출."""
    oldWords = old.split()
    newWords = new.split()
    matcher = difflib.SequenceMatcher(None, oldWords, newWords, autojunk=False)
    if matcher.ratio() < 0.3:
        return (old[:150], new[:150])
    delParts: list[str] = []
    addParts: list[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag in ("delete", "replace"):
            delParts.append(" ".join(oldWords[i1:i2]))
        if tag in ("insert", "replace"):
            addParts.append(" ".join(newWords[j1:j2]))
    return (" ".join(delParts), " ".join(addParts))


def _computeInlineDiff(
    fromText: str,
    toText: str,
    fromPeriod: str,
    toPeriod: str,
) -> InlineDiff | None:
    """두 텍스트의 문장 수준 inline diff."""
    fromSents = _splitSentences(fromText)
    toSents = _splitSentences(toText)
    if fromSents == toSents:
        return None

    additions: list[str] = []
    deletions: list[str] = []
    matcher = difflib.SequenceMatcher(None, fromSents, toSents, autojunk=False)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        elif tag == "insert":
            additions.extend(toSents[j1:j2])
        elif tag == "delete":
            deletions.extend(fromSents[i1:i2])
        elif tag == "replace":
            oldChunk = fromSents[i1:i2]
            newChunk = toSents[j1:j2]
            if len(oldChunk) == len(newChunk):
                for o, n in zip(oldChunk, newChunk):
                    wd, wa = _wordLevelDiff(o, n)
                    if wd:
                        deletions.append(wd)
                    if wa:
                        additions.append(wa)
            else:
                deletions.extend(oldChunk)
                additions.extend(newChunk)

    if not additions and not deletions:
        return None

    # 길이 제한
    additions = [a[:200] for a in additions[:15]]
    deletions = [d[:200] for d in deletions[:15]]

    return InlineDiff(
        fromPeriod=fromPeriod,
        toPeriod=toPeriod,
        additions=additions,
        deletions=deletions,
    )


def _buildChangeSummary(boRows: pl.DataFrame, periodCols: list[str]) -> ChangeSummary | None:
    """인접 기간 간 text 변경 감지 + inline diff."""
    if boRows.is_empty():
        return None

    row = boRows.row(0, named=True)
    hashes: list[tuple[str, str]] = []

    for p in periodCols:
        val = row.get(p)
        if val is not None and str(val).strip():
            h = hashlib.md5(str(val).encode(), usedforsecurity=False).hexdigest()[:12]
            hashes.append((p, h))

    if len(hashes) < 2:
        return ChangeSummary(totalPeriods=len(hashes))

    changes: list[dict[str, str]] = []
    diffs: list[InlineDiff] = []

    for i in range(len(hashes) - 1):
        if hashes[i][1] != hashes[i + 1][1]:
            fromPeriod = hashes[i][0]
            toPeriod = hashes[i + 1][0]
            fromText = str(row.get(fromPeriod, ""))
            toText = str(row.get(toPeriod, ""))
            delta = len(toText) - len(fromText)
            changes.append(
                {
                    "from": fromPeriod,
                    "to": toPeriod,
                    "delta": f"{'+' if delta >= 0 else ''}{delta}자",
                }
            )
            # 최근 N개만 inline diff
            if len(diffs) < _MAX_DIFF_PAIRS:
                d = _computeInlineDiff(fromText, toText, fromPeriod, toPeriod)
                if d is not None:
                    diffs.append(d)

    # diffs를 최신순으로 (뒤집기)
    diffs.reverse()

    # annotated blame
    annotated = _buildAnnotatedBlame(row, periodCols)

    # 변경 요약 카드 — 같은 유형 기간 직접 비교
    digest = _buildDigestDirect(row, periodCols)

    return ChangeSummary(
        totalPeriods=len(hashes),
        changedPairs=len(changes),
        latestChange=f"{changes[-1]['from']} → {changes[-1]['to']}" if changes else None,
        changes=changes,
        diffs=diffs,
        annotated=annotated,
        digest=digest,
    )


# ── 변경 요약 카드 (Digest) ──

_NUM_RE = re.compile(r"([\d,]+(?:\.\d+)?)\s*(조|억|만|개|%|명|원|년|기|건|사)?")


def _buildDigestDirect(row: dict[str, Any], periodCols: list[str]) -> ChangeDigest | None:
    """같은 보고서 유형의 이전 기간과 직접 비교하여 digest 생성.

    예: 최신이 2025(연간)이면 2024(연간)과 비교.
        최신이 2025Q1이면 2024Q1과 비교.
    """
    # 최신 기간 찾기
    latest = None
    for p in reversed(periodCols):
        val = row.get(p)
        if val is not None and str(val).strip():
            latest = p
            break
    if latest is None:
        return None

    # 같은 유형의 이전 기간 찾기
    prev = None
    for p in reversed(periodCols):
        if p == latest:
            continue
        val = row.get(p)
        if val is not None and str(val).strip() and _isSameReportType(latest, p):
            prev = p
            break
    if prev is None:
        return None

    # 직접 diff 계산
    fromText = str(row[prev])
    toText = str(row[latest])
    diff = _computeInlineDiff(fromText, toText, prev, latest)
    if diff is None:
        return None

    return _buildDigest([diff])


def _isSameReportType(p1: str, p2: str) -> bool:
    """같은 보고서 유형인지 (연간↔연간, Q1↔Q1 등)."""
    q1 = re.search(r"Q(\d)", p1)
    q2 = re.search(r"Q(\d)", p2)
    if q1 is None and q2 is None:
        return True  # 둘 다 연간
    if q1 and q2:
        return q1.group(1) == q2.group(1)  # 같은 분기
    return False


def _buildDigest(diffs: list[InlineDiff]) -> ChangeDigest | None:
    """최신 diff에서 숫자 변경 추출 + 추가/삭제 분류.

    같은 보고서 유형 간 비교를 우선한다 (연간↔연간, Q1↔Q1).
    """
    if not diffs:
        return None

    # 최신 기간과 같은 유형의 diff를 찾기 (연간↔연간 비교 우선)
    latestPeriod = diffs[0].toPeriod
    latest = None
    for d in diffs:
        if _isSameReportType(latestPeriod, d.toPeriod):
            latest = d
            break
    if latest is None:
        latest = diffs[0]
    items: list[ChangeDigestItem] = []
    wordingCount = 0

    # 1:1 매칭된 쌍에서 숫자 변경 추출
    paired = min(len(latest.deletions), len(latest.additions))
    for idx in range(paired):
        old = latest.deletions[idx]
        new = latest.additions[idx]
        numChanges = _extractNumericChanges(old, new)
        if numChanges:
            for nc in numChanges:
                items.append(ChangeDigestItem(kind="numeric", text=nc))
        else:
            wordingCount += 1

    # 대응 없는 추가/삭제
    for add in latest.additions[paired:]:
        summary = add[:60] + ("..." if len(add) > 60 else "")
        items.append(ChangeDigestItem(kind="added", text=summary))

    for dl in latest.deletions[paired:]:
        summary = dl[:60] + ("..." if len(dl) > 60 else "")
        items.append(ChangeDigestItem(kind="removed", text=summary))

    # 항목 수 제한: numeric 전부 + added/removed 최대 3개
    numericItems = [it for it in items if it.kind == "numeric"]
    addedItems = [it for it in items if it.kind == "added"]
    removedItems = [it for it in items if it.kind == "removed"]

    capped: list[ChangeDigestItem] = []
    capped.extend(numericItems[:10])
    capped.extend(addedItems[:3])
    capped.extend(removedItems[:3])

    extraAdded = max(0, len(addedItems) - 3)
    extraRemoved = max(0, len(removedItems) - 3)
    extraWording = wordingCount + extraAdded + extraRemoved

    return ChangeDigest(
        fromPeriod=latest.fromPeriod,
        toPeriod=latest.toPeriod,
        items=capped,
        wordingCount=extraWording,
    )


def _extractNumericChanges(old: str, new: str) -> list[str]:
    """두 텍스트에서 달라진 숫자를 추출하여 "X → Y" 형태로 반환."""
    oldNums = _NUM_RE.findall(old)
    newNums = _NUM_RE.findall(new)

    if not oldNums or not newNums or len(oldNums) != len(newNums):
        return []

    results = []
    for (oVal, oUnit), (nVal, nUnit) in zip(oldNums, newNums):
        oFull = oVal + oUnit
        nFull = nVal + nUnit
        if oFull != nFull:
            # 주변 컨텍스트 추출 (숫자 앞 10자)
            ctxMatch = re.search(r"(.{0,12})" + re.escape(nVal), new)
            prefix = ctxMatch.group(1).strip() if ctxMatch else ""
            # 앞 컨텍스트에서 의미 있는 키워드
            if prefix and not prefix[-1].isdigit():
                results.append(f"{prefix} {oFull} → {nFull}")
            else:
                results.append(f"{oFull} → {nFull}")

    return results


# ── Annotated Blame ──

_HEADING_RE = re.compile(r"^\[.+\]$|^【.+】$|^[가-힣]\.\s|^\d+\.\s|^\(\d+\)\s|^\([가-힣]\)\s")


def _buildAnnotatedBlame(row: dict[str, Any], periodCols: list[str]) -> list[AnnotatedLine]:
    """최신 텍스트의 각 줄: since(최초 등장) + frequency(존재 기간 수).

    - since: 가장 오래된 기간에서 이 줄이 존재하는 시점
    - frequency: 전체 기간 중 이 줄이 존재하는 기간 수
    - stability: stable(70%+) / recent(30-70%) / volatile(<30%)
    """
    # 기간별 텍스트 수집 (과거→최신)
    allTexts: list[tuple[str, set[str]]] = []
    for p in periodCols:
        val = row.get(p)
        if val is not None and str(val).strip():
            sents = set(_splitSentences(str(val)))
            allTexts.append((p, sents))

    if not allTexts:
        return []

    latestPeriod = allTexts[-1][0]
    latestText = row.get(latestPeriod, "")
    latestLines = _splitSentences(str(latestText))
    if not latestLines:
        return []

    totalPeriods = len(allTexts)
    result: list[AnnotatedLine] = []

    for line in latestLines:
        # 이 줄이 몇 기간에 존재하는지, 최초 등장 기간
        freq = 0
        firstSeen = latestPeriod
        for period, sentSet in allTexts:
            if line in sentSet:
                freq += 1
                if firstSeen == latestPeriod:
                    firstSeen = period

        result.append(
            AnnotatedLine(
                text=line,
                since=firstSeen,
                frequency=freq,
                totalPeriods=totalPeriods,
                isHeading=bool(_HEADING_RE.match(line)),
            )
        )

    return result


# ── Table 블록 ──


def _buildTableBlock(
    company: Company,
    topic: str,
    topicFrame: pl.DataFrame,
    bo: int,
    periodCols: list[str],
) -> ViewerBlock | None:
    """table 블록 — 수평화 시도 후 structured / raw_markdown 분류."""
    from dartlab.engines.company.dart._table_horizontalizer import horizontalizeTableBlock

    result = horizontalizeTableBlock(topicFrame, bo, periodCols, None)

    if result is not None and isinstance(result, pl.DataFrame):
        resPeriods = _periodCols(result)
        firstCol = result.columns[0] if result.columns else ""

        if resPeriods and firstCol and not firstCol.startswith("20"):
            sampleVal = str(result[resPeriods[0]][0]) if result.height > 0 else ""
            if _isRawMarkdown(sampleVal):
                return _buildRawMarkdownBlock(result, bo, resPeriods, firstCol)

            # 파이프 합침 값 감지 → raw_markdown으로 재분류
            if _hasPipeCells(result, resPeriods):
                return _buildRawMarkdownBlock(result, bo, resPeriods, firstCol)

            result = _cleanStructuredTable(result, resPeriods, firstCol)
            resPeriods = _periodCols(result)
            scale, divisor = _detectScale(result, resPeriods)
            return ViewerBlock(
                block=bo,
                kind="structured",
                source="docs",
                data=result,
                meta=BlockMeta(
                    scale=scale,
                    scaleDivisor=divisor,
                    periods=resPeriods,
                    rowCount=result.height,
                    colCount=len(result.columns),
                ),
            )

    # 수평화 실패 — 원본 마크다운
    boRows = topicFrame.filter(pl.col("blockOrder") == bo)
    keepCols = [c for c in periodCols if c in boRows.columns]
    nonNullCols = [c for c in keepCols if boRows[c].null_count() < boRows.height]

    if not nonNullCols:
        return None

    rawMd: dict[str, str] = {}
    row = boRows.row(0, named=True)
    for p in nonNullCols:
        val = row.get(p)
        if val is not None and str(val).strip():
            rawMd[p] = str(val)

    if not rawMd:
        return None

    return ViewerBlock(
        block=bo,
        kind="raw_markdown",
        source="docs",
        data=None,
        meta=BlockMeta(
            periods=list(rawMd.keys()),
            rowCount=1,
            colCount=len(rawMd),
        ),
        rawMarkdown=rawMd,
    )


def _buildRawMarkdownBlock(result: pl.DataFrame, bo: int, resPeriods: list[str], firstCol: str) -> ViewerBlock:
    """수평화 결과가 마크다운 문자열인 경우 raw_markdown으로 분류."""
    rawMd: dict[str, str] = {}
    for p in resPeriods:
        vals = result[p].to_list()
        combined = "\n".join(str(v) for v in vals if v is not None and str(v).strip())
        if combined:
            rawMd[p] = combined

    return ViewerBlock(
        block=bo,
        kind="raw_markdown",
        source="docs",
        data=None,
        meta=BlockMeta(
            periods=list(rawMd.keys()),
            rowCount=1,
            colCount=len(rawMd),
        ),
        rawMarkdown=rawMd,
    )


# ── Structured 테이블 정리 ──


def _periodSortKey(p: str) -> tuple[int, int]:
    """기간 컬럼 정렬키: 2021Q1→(2021,1), 2021→(2021,5), 2021Q4→(2021,4)."""
    m = re.fullmatch(r"(\d{4})(Q([1-4]))?", p)
    if not m:
        return (9999, 0)
    year = int(m.group(1))
    q = int(m.group(3)) if m.group(3) else 5  # 연간은 Q4 뒤
    return (year, q)


def _cleanStructuredTable(df: pl.DataFrame, periodCols: list[str], firstCol: str) -> pl.DataFrame:
    """structured 테이블 정리: 기간 정렬 + 전체 null 컬럼 제거."""
    # 1. 전체 null인 기간 컬럼 제거
    keepPeriods = []
    for p in periodCols:
        if p in df.columns and df[p].null_count() < df.height:
            keepPeriods.append(p)

    # 2. 기간 정렬
    keepPeriods.sort(key=_periodSortKey, reverse=True)

    # 3. 항목 컬럼 + 정렬된 기간 컬럼으로 재구성
    nonPeriodCols = [c for c in df.columns if c not in periodCols]
    orderedCols = nonPeriodCols + keepPeriods

    # 존재하는 컬럼만
    orderedCols = [c for c in orderedCols if c in df.columns]
    return df.select(orderedCols)


# ── 유틸리티 ──


def _isRawMarkdown(text: str) -> bool:
    """셀 값이 마크다운 테이블 원본인지 판별."""
    if not text or len(text) < 5:
        return False
    lines = text.strip().split("\n")
    mdLines = sum(1 for l in lines[:5] if l.strip().startswith("|"))
    return mdLines >= 2


def _hasPipeCells(df: pl.DataFrame, periodCols: list[str]) -> bool:
    """structured 테이블의 셀에 파이프 합침 값이 있는지 감지.

    horizontalizeTableBlock에서 헤더/데이터 컬럼 수 불일치 시
    `" | ".join(vals)` 형태로 합쳐진 셀을 감지한다.
    첫 5행 중 하나라도 " | " 패턴이 있으면 True.
    """
    for col in periodCols[:2]:
        if col not in df.columns:
            continue
        for val in df[col].head(5).to_list():
            if val is not None and " | " in str(val):
                return True
    return False


def _detectScale(df: pl.DataFrame, periodCols: list[str]) -> tuple[str | None, float]:
    """DataFrame 숫자 크기로 추천 스케일 판별."""
    maxAbs = 0.0
    for col in periodCols:
        if col not in df.columns:
            continue
        series = df[col]
        if series.dtype in (pl.Float64, pl.Float32, pl.Int64, pl.Int32):
            absMax = series.drop_nulls().cast(pl.Float64).abs().max()
            if absMax is not None and absMax > maxAbs:
                maxAbs = absMax
        else:
            for val in series.to_list()[:10]:
                if val is None:
                    continue
                s = str(val).strip().replace(",", "")
                try:
                    v = abs(float(s))
                    if v > maxAbs:
                        maxAbs = v
                except ValueError:
                    pass

    if maxAbs >= 1e12:
        return ("억원", 1e8)
    if maxAbs >= 1e8:
        return ("백만원", 1e6)
    return (None, 1.0)


# ── 직렬화 ──


def _serializeChangeDigest(digest: ChangeDigest | None) -> dict[str, Any] | None:
    if digest is None:
        return None
    return {
        "from": digest.fromPeriod,
        "to": digest.toPeriod,
        "items": [{"kind": item.kind, "text": item.text} for item in digest.items],
        "wordingCount": digest.wordingCount,
    }


def _serializePeriodRef(period: PeriodRef | None) -> dict[str, Any] | None:
    if period is None:
        return None
    return {
        "label": period.label,
        "year": period.year,
        "quarter": period.quarter,
        "kind": period.kind,
        "sortKey": period.sortKey,
    }


def _serializeViewerDiffChunk(chunk: ViewerDiffChunk) -> dict[str, Any]:
    return {
        "kind": chunk.kind,
        "paragraphs": chunk.paragraphs,
    }


def _serializeViewerTextView(view: ViewerTextView | None) -> dict[str, Any] | None:
    if view is None:
        return None
    return {
        "period": _serializePeriodRef(view.period),
        "prevPeriod": _serializePeriodRef(view.prevPeriod),
        "body": view.body,
        "status": view.status,
        "diff": [_serializeViewerDiffChunk(chunk) for chunk in view.diff],
        "digest": _serializeChangeDigest(view.digest),
    }


def serializeViewerTextDocument(document: ViewerTextDocument | None) -> dict[str, Any] | None:
    """ViewerTextDocument를 JSON 직렬화 가능한 dict로 변환."""
    if document is None:
        return None

    return {
        "topic": document.topic,
        "mode": document.mode,
        "periods": [_serializePeriodRef(period) for period in document.periods],
        "latestPeriod": _serializePeriodRef(document.latestPeriod),
        "firstPeriod": _serializePeriodRef(document.firstPeriod),
        "sectionCount": document.sectionCount,
        "updatedCount": document.updatedCount,
        "newCount": document.newCount,
        "staleCount": document.staleCount,
        "stableCount": document.stableCount,
        "sections": [
            {
                "id": section.id,
                "order": section.order,
                "bodyBlock": section.bodyBlock,
                "headingPath": [
                    {
                        "block": heading.block,
                        "text": heading.text,
                        "period": _serializePeriodRef(heading.period),
                        "level": heading.level,
                    }
                    for heading in section.headingPath
                ],
                "latest": _serializeViewerTextView(section.latest),
                "latestPeriod": _serializePeriodRef(section.latestPeriod),
                "firstPeriod": _serializePeriodRef(section.firstPeriod),
                "periodCount": section.periodCount,
                "status": section.status,
                "latestChange": section.latestChange,
                "preview": section.preview,
                "timeline": [
                    {
                        "period": _serializePeriodRef(entry.period),
                        "prevPeriod": _serializePeriodRef(entry.prevPeriod),
                        "status": entry.status,
                    }
                    for entry in section.timeline
                ],
                "views": {label: _serializeViewerTextView(view) for label, view in section.views.items()},
            }
            for section in document.sections
        ],
        "entries": [
            {
                "kind": entry.kind,
                "order": entry.order,
                "sectionId": entry.sectionId,
                "blockRef": entry.blockRef,
                "blockKind": entry.blockKind,
            }
            for entry in document.entries
        ],
    }


def serializeViewerBlock(block: ViewerBlock) -> dict[str, Any]:
    """ViewerBlock을 JSON-직렬화 가능한 dict로 변환."""
    result: dict[str, Any] = {
        "block": block.block,
        "kind": block.kind,
        "source": block.source,
        "meta": {
            "unit": block.meta.unit,
            "scale": block.meta.scale,
            "scaleDivisor": block.meta.scaleDivisor,
            "periods": block.meta.periods,
            "rowCount": block.meta.rowCount,
            "colCount": block.meta.colCount,
        },
    }

    if block.data is not None:
        result["data"] = _serializeDf(block.data)
    else:
        result["data"] = None

    if block.changeSummary is not None:
        result["changeSummary"] = {
            "totalPeriods": block.changeSummary.totalPeriods,
            "changedPairs": block.changeSummary.changedPairs,
            "latestChange": block.changeSummary.latestChange,
            "changes": block.changeSummary.changes,
            "diffs": [
                {
                    "from": d.fromPeriod,
                    "to": d.toPeriod,
                    "additions": d.additions,
                    "deletions": d.deletions,
                }
                for d in block.changeSummary.diffs
            ],
            "annotated": [
                {
                    "text": a.text,
                    "since": a.since,
                    "frequency": a.frequency,
                    "totalPeriods": a.totalPeriods,
                    "stability": a.stability,
                    "isHeading": a.isHeading,
                }
                for a in block.changeSummary.annotated
            ],
            "digest": _serializeChangeDigest(block.changeSummary.digest),
        }
    else:
        result["changeSummary"] = None

    if block.rawMarkdown is not None:
        result["rawMarkdown"] = block.rawMarkdown
    else:
        result["rawMarkdown"] = None

    result["textType"] = block.textType

    return result


def _serializeDf(df: pl.DataFrame) -> dict[str, Any]:
    """DataFrame을 {columns, rows} 형태로 직렬화."""
    rows = df.to_dicts()
    for row in rows:
        for k, v in row.items():
            if isinstance(v, float):
                if v != v or v == float("inf") or v == float("-inf"):
                    row[k] = None
    return {
        "columns": df.columns,
        "rows": rows,
    }
