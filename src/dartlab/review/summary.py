"""review 요약 카드 + 섹션 요약 생성."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SummaryCard:
    """review 최상단 요약 카드."""

    conclusion: str = ""
    strengths: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    grades: dict[str, str] = field(default_factory=dict)


def buildSummaryCard(threads, scorecardData, sections) -> SummaryCard:
    """narrative threads + scorecard 등급 + 섹션 flags로 요약 카드 생성."""
    from dartlab.review.blocks import FlagBlock

    card = SummaryCard()

    # ── 등급: scorecard 데이터에서 추출 ──
    if scorecardData:
        for item in scorecardData.get("items", []):
            card.grades[item["area"]] = item["grade"]

    # ── 강점/경고: threads에서 추출 ──
    for t in threads:
        if t.severity == "positive":
            card.strengths.append(t.title)
        elif t.severity in ("critical", "warning"):
            card.warnings.append(t.title)

    # ── flags에서 보충 (threads가 부족할 때) ──
    opportunityFlags: list[str] = []
    warningFlags: list[str] = []
    for sec in sections:
        for block in sec.blocks:
            if isinstance(block, FlagBlock):
                if block.kind == "opportunity":
                    opportunityFlags.extend(block.flags)
                else:
                    warningFlags.extend(block.flags)

    # strengths 부족 시 opportunity flags로 보충 (최대 3개)
    for f in opportunityFlags:
        if len(card.strengths) >= 3:
            break
        if f not in card.strengths:
            card.strengths.append(f)
    card.strengths = card.strengths[:3]

    # warnings 부족 시 warning flags로 보충 (최대 3개)
    for f in warningFlags:
        if len(card.warnings) >= 3:
            break
        if f not in card.warnings:
            card.warnings.append(f)
    card.warnings = card.warnings[:3]

    # ── 한줄 결론 ──
    card.conclusion = _buildConclusion(threads, card.grades)

    return card


def _buildConclusion(threads, grades: dict[str, str]) -> str:
    """threads 톤 + 등급으로 한줄 결론 생성."""
    criticals = [t for t in threads if t.severity == "critical"]
    positives = [t for t in threads if t.severity == "positive"]

    # 등급 요약
    gradeParts = []
    for area in ("수익성", "성장성", "안정성", "효율성", "현금흐름"):
        g = grades.get(area)
        if g:
            gradeParts.append(f"{area} {g}")
    gradeStr = " | ".join(gradeParts) if gradeParts else ""

    if criticals and positives:
        return f"{positives[0].title} -- 다만 {criticals[0].title}"
    if criticals:
        return criticals[0].title
    if positives:
        return positives[0].title
    if gradeStr:
        return gradeStr
    return ""


def buildSectionSummary(section) -> str:
    """섹션의 blocks + threads에서 1-2줄 핵심 요약 생성."""
    from dartlab.review.blocks import FlagBlock, MetricBlock, TableBlock, TextBlock

    parts: list[str] = []

    # 핵심 지표 (첫 MetricBlock의 첫 1-2개 metric)
    for block in section.blocks:
        if isinstance(block, MetricBlock) and block.metrics:
            for label, value in block.metrics[:2]:
                parts.append(f"{label} {value}")
            break

    # MetricBlock이 없으면 TextBlock에서 첫 문장 (profile 등)
    if not parts:
        for block in section.blocks:
            if isinstance(block, TextBlock) and block.text and block.text.strip():
                text = block.text.strip()
                # 첫 문장만 (마침표 또는 줄바꿈 기준)
                for sep in (".", "\n"):
                    idx = text.find(sep)
                    if idx > 0:
                        text = text[:idx]
                        break
                if len(text) <= 80:
                    parts.append(text)
                break

    # TextBlock도 없으면 TableBlock label + 첫 행 요약
    if not parts:
        for block in section.blocks:
            if isinstance(block, TableBlock) and hasattr(block.df, "columns"):
                try:
                    df = block.df
                    if df.height > 0 and len(df.columns) >= 2:
                        firstRow = df.row(0)
                        parts.append(f"{firstRow[0]}: {firstRow[1]}")
                except (IndexError, AttributeError):
                    pass
                break

    # thread title (있으면 1개, 단 parts가 비어있거나 thread가 다른 정보일 때)
    if section.threads:
        threadTitle = section.threads[0].title
        # parts에 이미 같은 내용이 없으면 추가
        if not any(threadTitle in p for p in parts):
            parts.append(threadTitle)

    # 가장 중요한 flag (warning 우선, 1개)
    for block in section.blocks:
        if isinstance(block, FlagBlock) and block.flags:
            parts.append(block.flags[0])
            break

    return " / ".join(parts[:3]) if parts else ""
