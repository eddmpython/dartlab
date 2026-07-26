"""story 멀티포맷 렌더링 (html/markdown/json/ascii)."""

from __future__ import annotations

import json
from typing import Any


def renderHtml(story, *, chartDir: str | None = None) -> str:
    """HTML 렌더링. chart_dir 지정 시 ChartBlock을 SVG 이미지로 삽입."""
    from dartlab.story.blocks import (
        ChartBlock,
        FlagBlock,
        HeadingBlock,
        MetricBlock,
        TableBlock,
        TextBlock,
    )

    parts: list[str] = []
    parts.append(
        f"<h2 style='font-family:Pretendard,-apple-system,sans-serif'>{story.corpName} ({story.stockCode})</h2>"
    )

    if story.summaryCard:
        card = story.summaryCard
        cardParts = []
        if card.conclusion:
            cardParts.append(f"<strong>{card.conclusion}</strong>")
        if card.grades:
            gradeStr = " | ".join(f"{k} {v}" for k, v in card.grades.items())
            cardParts.append(f"<span style='color:#888'>{gradeStr}</span>")
        for s in card.strengths:
            cardParts.append(f"<span style='color:#2e7d32'>+ {s}</span>")
        for w in card.warnings:
            cardParts.append(f"<span style='color:#f9a825'>- {w}</span>")
        parts.append(
            "<div style='border:2px solid #333;padding:12px;margin:8px 0;border-radius:4px'>"
            + "<br/>".join(cardParts)
            + "</div>"
        )

    if story.circulationSummary:
        parts.append(
            f"<div style='border:1px solid #ddd;padding:12px;margin:8px 0;border-radius:4px'>"
            f"<strong>재무 순환 서사</strong><br/>"
            f"{'<br/>'.join(story.circulationSummary.split(chr(10)))}</div>"
        )

    detailMode = getattr(story.layout, "detail", True)

    for section in story.sections:
        if not detailMode:
            parts.append(f"<h3>{section.title}</h3>")
            if section.summary:
                parts.append(f"<p style='color:#888'>{section.summary}</p>")
            continue
        if section.threads:
            for t in section.threads:
                colorMap = {"critical": "#d32f2f", "warning": "#f9a825", "positive": "#2e7d32", "neutral": "#757575"}
                color = colorMap.get(t.severity, "#757575")
                parts.append(
                    f"<div style='border-left:3px solid {color};padding:4px 12px;margin:4px 0'>"
                    f"<strong style='color:{color}'>>> {t.title}</strong></div>"
                )
        for block in section.blocks:
            if isinstance(block, HeadingBlock):
                parts.append(f"<{block.htmlTag}>{block.title}</{block.htmlTag}>")
            elif isinstance(block, TextBlock):
                parts.append(f"<p>{block.text}</p>")
            elif isinstance(block, MetricBlock):
                rows = "".join(f"<tr><td>{label}</td><td>{value}</td></tr>" for label, value in block.metrics)
                parts.append(f"<table>{rows}</table>")
            elif isinstance(block, TableBlock):
                if hasattr(block.df, "_repr_html_"):
                    parts.append(block.df._repr_html_())
            elif isinstance(block, ChartBlock):
                title = block.spec.get("title", "") if isinstance(block.spec, dict) else ""
                rendered_chart = False
                if chartDir and isinstance(block.spec, dict):
                    from dartlab.viz.spec import VizSpec

                    key = title.replace(" ", "_")[:30] or "chart"
                    img_path = f"{chartDir}/chart-{key}.svg"
                    try:
                        vs = VizSpec.fromDict(block.spec)
                        if vs.toImage(img_path):
                            parts.append(f"<img src='assets/chart-{key}.svg' alt='{title}' style='max-width:100%'>")
                            rendered_chart = True
                    except (ImportError, ValueError, OSError, TypeError):
                        pass
                if not rendered_chart:
                    spec_json = json.dumps(block.spec, ensure_ascii=False, default=str)
                    parts.append(
                        f"<div class='dl-chart' data-spec='{spec_json}'>"
                        f"<p style='color:#888;font-size:0.85em'>[chart: {title}]</p></div>"
                    )
            elif isinstance(block, FlagBlock):
                for f in block.flags:
                    parts.append(f"<p>{block.icon} {f}</p>")
            elif hasattr(block, "render"):
                parts.append(block.render("html"))

    return "<div style='display:flex;flex-direction:column;gap:16px'>" + "".join(parts) + "</div>"


def _polarsToMarkdown(df) -> str:
    """Polars DataFrame을 마크다운 테이블로 변환 (박스 아트 제거)."""
    from dartlab.story.utils import fmtAmt

    try:
        cols = df.columns
        header = "| " + " | ".join(str(c) for c in cols) + " |"
        sep = "| " + " | ".join("---" for _ in cols) + " |"
        rows = []
        for row in df.iter_rows():
            cells = []
            for v in row:
                if v is None:
                    cells.append("-")
                elif isinstance(v, float):
                    cells.append(fmtAmt(v))
                else:
                    cells.append(str(v))
            rows.append("| " + " | ".join(cells) + " |")
        return "\n".join([header, sep] + rows)
    except (TypeError, ValueError, AttributeError):
        return str(df)


# ── 6막 전환 경계 매핑 (섹션 key → 전환 key) ──
_MD_ACT_BOUNDARIES: dict[str, str] = {
    "수익성": "1→2",
    "현금흐름": "2→3",
    "자금조달": "3→4",
    "자산구조": "4→5",
    "가치평가": "5→6",
}

_THREAD_SEVERITY_ICON: dict[str, str] = {
    "critical": "[!!]",
    "warning": "[!]",
    "positive": "[+]",
    "neutral": "[-]",
}


def _mdRenderSummaryCard(summaryCard) -> str | None:
    """요약 카드 한 블록. 반환: markdown 문자열 or None."""
    if not summaryCard:
        return None
    lines: list[str] = []
    if summaryCard.conclusion:
        lines.append(f"**{summaryCard.conclusion}**")
    for s in summaryCard.strengths:
        lines.append(f"- [+] {s}")
    for w in summaryCard.warnings:
        lines.append(f"- [-] {w}")
    return "\n".join(lines) if lines else None


def _mdRenderLensProducts(story) -> str | None:
    """다섯 렌즈의 직접 결론만 표로 보여준다. 통합 점수는 만들지 않는다."""
    from dartlab.story.lensProducts import lensSummary

    rows = lensSummary(getattr(story, "lensProducts", {}))
    if not rows:
        return None
    lines = ["### 분석 렌즈", "", "| 렌즈 | 상태 | 판단 | 신뢰도 | 데이터 시점 |", "| --- | --- | --- | --- | --- |"]
    for row in rows:
        confidence = row.get("confidenceLevel") or "unknown"
        if row.get("confidenceScore") is not None:
            confidence = f"{confidence} ({row['confidenceScore']})"
        dataAsOf = row.get("dataAsOf")
        if isinstance(dataAsOf, dict):
            dataAsOf = dataAsOf.get("sourceDataAsOf") or dataAsOf.get("date") or dataAsOf.get("retrievedAt")
        when = dataAsOf or row.get("period") or row.get("asOf") or "미상"
        lines.append(
            f"| {row['engine']} | {row.get('status') or 'unknown'} | "
            f"{row.get('label') or '판단 없음'} | {confidence} | {when} |"
        )
    lines.append("")
    lines.append("렌즈별 판단은 독립 결과이며 통합 점수나 단일 등급으로 합산하지 않습니다.")
    return "\n".join(lines)


def _mdRenderTemplateHeader(story, templateName: str | None, tmplInfo: dict) -> list[str]:
    """스토리 템플릿 표시 블록. 반환: markdown 문자열 리스트."""
    if not templateName:
        return []
    parts: list[str] = []
    allTemplates = getattr(story, "templates", []) or []
    if len(allTemplates) > 1:
        parts.append(f"**스토리: {' + '.join(allTemplates)}**")
    else:
        desc = tmplInfo.get("description", "") if tmplInfo else ""
        parts.append(f"**스토리: {templateName}** - {desc}")
    keyQuestions = tmplInfo.get("keyQuestions", []) if tmplInfo else []
    if keyQuestions:
        qLines = [f"  - {q}" for q in keyQuestions]
        parts.append("> **핵심 질문**\n" + "\n".join(f"> {q}" for q in qLines))
    return parts


def _mdRenderSectionHeader(section, mainAct: str, _ACT_HEADERS, renderedActs: set, actFocus: dict) -> list[str]:
    """섹션 막 헤더 + actFocus 인트로. 반환: markdown 문자열 리스트."""
    if not mainAct or mainAct in renderedActs:
        return []
    renderedActs.add(mainAct)
    parts: list[str] = []
    if mainAct not in _ACT_HEADERS:
        parts.append(f"\n---\n\n# {section.title}\n")
        if section.helper:
            parts.append(f"> {section.helper}")
        return parts
    actTitle, actQuestion = _ACT_HEADERS[mainAct]
    parts.append(f"\n---\n\n# {actTitle}\n")
    parts.append(f"> **핵심 질문**: {actQuestion}")
    focus = actFocus.get(mainAct)
    if focus:
        parts.append(f"> **이 기업의 관전 포인트**: {focus}")
    return parts


def _mdRenderBlock(block, chartDir: str | None, blockTypes: dict) -> list[str]:
    """단일 block → markdown 라인 리스트. 반환: 빈 리스트면 미지원."""
    HeadingBlock = blockTypes["HeadingBlock"]
    TextBlock = blockTypes["TextBlock"]
    MetricBlock = blockTypes["MetricBlock"]
    TableBlock = blockTypes["TableBlock"]
    ChartBlock = blockTypes["ChartBlock"]
    FlagBlock = blockTypes["FlagBlock"]

    isEmphasized = getattr(block, "emphasized", False)
    if isinstance(block, HeadingBlock):
        mark = "\u2605 " if isEmphasized else ""
        return [f"{block.markdownPrefix} {mark}{block.title}"]
    if isinstance(block, TextBlock):
        return [block.text]
    if isinstance(block, MetricBlock):
        return [f"- **{label}**: {value}" for label, value in block.metrics]
    if isinstance(block, TableBlock):
        return [_mdRenderTableBlock(block)]
    if isinstance(block, ChartBlock):
        return [_mdRenderChartBlock(block, chartDir)]
    if isinstance(block, FlagBlock):
        return [f"- {block.icon} {f}" for f in block.flags]
    if hasattr(block, "render"):
        return [block.render("markdown")]
    return []


def _mdRenderTableBlock(block) -> str:
    """TableBlock → markdown table (pandas fallback polars)."""
    if hasattr(block.df, "to_pandas"):
        try:
            pdf = block.df.to_pandas()
            pdf.columns = [c[:-2] if isinstance(c, str) and c.endswith("Q4") else c for c in pdf.columns]
            return pdf.to_markdown(index=False)
        except (ImportError, Exception):
            pass
    return _polarsToMarkdown(block.df)


def _mdRenderChartBlock(block, chartDir: str | None) -> str:
    """ChartBlock → 이미지 참조 또는 [chart: ...] placeholder."""
    title = block.spec.get("title", "차트") if isinstance(block.spec, dict) else "차트"
    if chartDir and isinstance(block.spec, dict):
        from dartlab.viz.spec import VizSpec

        key = block.spec.get("title", "chart").replace(" ", "_")[:30]
        img_path = f"{chartDir}/chart-{key}.svg"
        try:
            vs = VizSpec.fromDict(block.spec)
            if vs.toImage(img_path):
                return f"![{title}](assets/chart-{key}.svg)"
        except (ImportError, ValueError, OSError, TypeError):
            pass
    return f"*[chart: {title}]*"


def _mdRenderSectionThreads(section, renderedThreads: set) -> list[str]:
    """Thread 제목 표시 (중복 제외). 반환: markdown 문자열 리스트."""
    if not section.threads:
        return []
    lines: list[str] = []
    for t in section.threads:
        if t.title in renderedThreads:
            continue
        renderedThreads.add(t.title)
        icon = _THREAD_SEVERITY_ICON.get(t.severity, "")
        lines.append(f"**{icon} {t.title}**")
    return lines


def _mdRenderSection(
    section,
    story,
    blockTypes: dict,
    renderedActs: set,
    renderedThreads: set,
    _ACT_HEADERS,
    actFocus: dict,
    chartDir: str | None,
    detailMode: bool,
) -> list[str]:
    """단일 섹션 전체 렌더링. 반환: markdown 문자열 리스트."""
    actNum = getattr(section, "partId", "")
    mainAct = actNum.split("-")[0] if actNum else ""

    parts = _mdRenderSectionHeader(section, mainAct, _ACT_HEADERS, renderedActs, actFocus)

    transKey = _MD_ACT_BOUNDARIES.get(section.key)
    if transKey and hasattr(story, "actTransitions") and story.actTransitions:
        trans = story.actTransitions.get(transKey)
        if trans:
            parts.append(f"\n> **{transKey}** {trans}\n")

    if not detailMode:
        parts.append(f"### {section.title}")
        if section.summary:
            parts.append(f"*{section.summary}*")
        return parts

    parts.extend(_mdRenderSectionThreads(section, renderedThreads))

    if not section.blocks:
        parts.append(f"_{section.title}: 데이터가 부족하여 이 섹션은 생략되었습니다._\n")
        return parts

    for block in section.blocks:
        parts.extend(_mdRenderBlock(block, chartDir, blockTypes))
    return parts


def renderMarkdown(story, *, chartDir: str | None = None) -> str:
    """마크다운 렌더링 orchestrator (Q3.1f split).

    chart_dir 지정 시 ChartBlock 을 SVG 로 저장하고 이미지 참조 생성.

    Parameters
    ----------
    story : StoryLayout
        렌더링 대상. sections / summaryCard / circulationSummary /
        actTransitions / template 속성 소비.
    chart_dir : str, optional
        SVG 출력 디렉토리. None 이면 placeholder 로 대체.

    Returns
    -------
    str
        완성된 마크다운 문서 (섹션/요약/막 결론 포함).
    """
    from dartlab.story.blocks import (
        ChartBlock,
        FlagBlock,
        HeadingBlock,
        MetricBlock,
        TableBlock,
        TextBlock,
    )
    from dartlab.story.catalog import ACT_HEADERS

    blockTypes = {
        "HeadingBlock": HeadingBlock,
        "TextBlock": TextBlock,
        "MetricBlock": MetricBlock,
        "TableBlock": TableBlock,
        "ChartBlock": ChartBlock,
        "FlagBlock": FlagBlock,
    }

    templateName = getattr(story, "template", None)
    tmplInfo: dict = {}
    actFocus: dict[str, str] = {}
    if templateName:
        from dartlab.story.templates import STORY_TEMPLATES

        tmplInfo = STORY_TEMPLATES.get(templateName, {})
        actFocus = tmplInfo.get("actFocus", {})

    parts: list[str] = [f"## {story.corpName} ({story.stockCode})\n"]

    card = _mdRenderSummaryCard(story.summaryCard)
    if card:
        parts.append(card)

    lensProducts = _mdRenderLensProducts(story)
    if lensProducts:
        parts.append(lensProducts)

    parts.extend(_mdRenderTemplateHeader(story, templateName, tmplInfo))

    if story.circulationSummary:
        parts.append(f"> **재무 순환 서사**\n> {story.circulationSummary.replace(chr(10), chr(10) + '> ')}")

    detailMode = getattr(story.layout, "detail", True)
    renderedActs: set[str] = set()
    renderedThreads: set[str] = set()
    actSummaryUsedIds: set[str] = set()
    currentAct: str = ""
    currentActSections: list = []

    allThreads: list = []
    for sec in story.sections:
        if sec.threads:
            allThreads.extend(sec.threads)

    for section in story.sections:
        mainAct = getattr(section, "partId", "").split("-")[0]

        if mainAct and mainAct != currentAct and currentAct and currentActSections:
            from dartlab.story.narrate import buildActSummary

            actSummary = buildActSummary(currentAct, currentActSections, allThreads, actSummaryUsedIds)
            if actSummary:
                parts.append(f"\n{actSummary}\n")
            currentActSections = []

        if mainAct:
            currentAct = mainAct

        parts.extend(
            _mdRenderSection(
                section,
                story,
                blockTypes,
                renderedActs,
                renderedThreads,
                ACT_HEADERS,
                actFocus,
                chartDir,
                detailMode,
            )
        )
        currentActSections.append(section)

    if currentAct and currentActSections:
        from dartlab.story.narrate import buildActSummary

        actSummary = buildActSummary(currentAct, currentActSections, allThreads, actSummaryUsedIds)
        if actSummary:
            parts.append(f"\n{actSummary}\n")

    return "\n\n".join(parts)


def renderJson(story) -> str:
    """JSON 렌더링."""
    from dartlab.story.blocks import (
        ChartBlock,
        FlagBlock,
        HeadingBlock,
        MetricBlock,
        TableBlock,
        TextBlock,
    )

    detailMode = getattr(story.layout, "detail", True)

    sections: list[dict[str, Any]] = []
    for section in story.sections:
        if not detailMode:
            sectionDict: dict[str, Any] = {
                "key": section.key,
                "title": section.title,
                "summary": section.summary,
            }
            sections.append(sectionDict)
            continue
        items: list[dict] = []
        for block in section.blocks:
            if isinstance(block, HeadingBlock):
                items.append({"type": "heading", "title": block.title, "level": block.level})
            elif isinstance(block, TextBlock):
                items.append({"type": "text", "text": block.text})
            elif isinstance(block, MetricBlock):
                items.append(
                    {
                        "type": "metrics",
                        "metrics": [{"label": l, "value": v} for l, v in block.metrics],
                    }
                )
            elif isinstance(block, TableBlock):
                if hasattr(block.df, "to_dicts"):
                    items.append({"type": "table", "label": block.label, "data": block.df.to_dicts()})
            elif isinstance(block, ChartBlock):
                items.append({"type": "chart", "spec": block.spec, "caption": block.caption})
            elif isinstance(block, FlagBlock):
                items.append({"type": "flags", "kind": block.kind, "flags": block.flags})
            elif hasattr(block, "toJson"):
                raw = block.toJson()
                if isinstance(raw, str):
                    try:
                        items.append(json.loads(raw))
                    except json.JSONDecodeError:
                        items.append({"text": raw})
                else:
                    items.append(raw)
        threadDicts = []
        for t in section.threads:
            threadDicts.append(
                {
                    "threadId": t.threadId,
                    "title": t.title,
                    "story": t.story,
                    "severity": t.severity,
                    "involvedSections": t.involvedSections,
                    "evidence": t.evidence,
                }
            )
        sectionDict = {
            "key": section.key,
            "title": section.title,
            "summary": section.summary,
            "blocks": items,
        }
        if threadDicts:
            sectionDict["threads"] = threadDicts
        sections.append(sectionDict)

    result: dict[str, Any] = {
        "stockCode": story.stockCode,
        "corpName": story.corpName,
        "reportType": getattr(story, "reportType", None),
        "sections": sections,
    }
    from dartlab.story.lensProducts import publicLensBundle

    publicBundle = publicLensBundle(getattr(story, "_lensBundle", None))
    if isinstance(publicBundle, dict) and (publicBundle.get("products") or publicBundle.get("gaps")):
        result["lensProducts"] = publicBundle
    if story.summaryCard:
        card = story.summaryCard
        result["summaryCard"] = {
            "conclusion": card.conclusion,
            "strengths": card.strengths,
            "warnings": card.warnings,
            "grades": card.grades,
        }
    if story.circulationSummary:
        result["circulationSummary"] = story.circulationSummary

    return json.dumps(
        result,
        ensure_ascii=False,
        default=str,
    )


def renderAscii(story, *, width: int = 80) -> str:
    """터미널 ASCII 렌더링.

    TextBlock → plain text
    HeadingBlock → 밑줄
    MetricBlock → "label: value" 한 줄
    TableBlock → 간단 문자 표 (첫 3컬럼)
    FlagBlock → "[⚠] severity - message"
    ChartBlock → ``spec.toAscii()``

    Parameters
    ----------
    story : Story
        c.story(...) 결과 객체
    width : int
        콘솔 너비 (기본 80)

    Returns
    -------
    str
        print() 가능한 ASCII/ANSI 문자열
    """
    from dartlab.story.blocks import (
        ChartBlock,
        FlagBlock,
        HeadingBlock,
        MetricBlock,
        TableBlock,
        TextBlock,
    )
    from dartlab.viz import renderAscii

    lines: list[str] = []
    rule = "═" * width

    # 헤더
    corpName = getattr(story, "corpName", "") or getattr(story, "stockCode", "")
    stockCode = getattr(story, "stockCode", "")
    lines.append(rule)
    title = f"  {corpName}  ({stockCode})" if stockCode and corpName != stockCode else f"  {corpName}"
    lines.append(title)
    lines.append(rule)
    lines.append("")

    sections = getattr(story, "sections", []) or []
    for sec in sections:
        secTitle = getattr(sec, "title", "") or getattr(sec, "key", "")
        if not secTitle:
            continue
        lines.append("")
        lines.append(f"■ {secTitle}")
        lines.append("─" * width)

        helper = getattr(sec, "helper", None)
        if helper:
            lines.append(f"  {helper}")

        summary = getattr(sec, "summary", None)
        if summary:
            lines.append("")
            lines.append(f"  » {summary}")

        blocks = getattr(sec, "blocks", []) or []
        for block in blocks:
            if isinstance(block, HeadingBlock):
                text = getattr(block, "text", "") or ""
                if text:
                    lines.append("")
                    lines.append(f"  ▶ {text}")
            elif isinstance(block, TextBlock):
                text = getattr(block, "text", "") or ""
                if text:
                    for line in text.split("\n"):
                        lines.append(f"    {line}")
            elif isinstance(block, MetricBlock):
                label = getattr(block, "label", "")
                value = getattr(block, "value", "")
                lines.append(f"    {label:<24} {value}")
            elif isinstance(block, FlagBlock):
                severity = getattr(block, "severity", "info")
                message = getattr(block, "message", "")
                icon = "⚠" if severity in ("warning", "error", "danger") else "●"
                lines.append(f"    [{icon}] {severity:<8} - {message}")
            elif isinstance(block, TableBlock):
                try:
                    df = getattr(block, "df", None)
                    if df is not None and hasattr(df, "columns"):
                        cols = df.columns[:3]
                        lines.append("    " + " | ".join(str(c) for c in cols))
                        rows = df.head(5).to_numpy().tolist() if hasattr(df, "to_numpy") else []
                        for row in rows:
                            cells = [str(c)[:15] for c in row[:3]]
                            lines.append("    " + " | ".join(cells))
                except Exception:
                    pass
            elif isinstance(block, ChartBlock):
                try:
                    spec = getattr(block, "spec", {}) or {}
                    if spec:
                        chart_text = renderAscii(spec, width=width - 4, height=12)
                        for line in chart_text.split("\n"):
                            lines.append(f"  {line}")
                except Exception:
                    lines.append("    [chart: 렌더 실패]")

        aiOp = getattr(sec, "aiOpinion", None)
        if aiOp:
            lines.append("")
            lines.append(f"  [AI] {aiOp}")

    # Footer
    lines.append("")
    lines.append(rule)
    return "\n".join(lines)
