"""review 멀티포맷 렌더링 (html/markdown/json)."""

from __future__ import annotations

import json
from typing import Any


def renderHtml(review) -> str:
    """HTML 렌더링."""
    from dartlab.review.blocks import (
        ChartBlock,
        FlagBlock,
        HeadingBlock,
        MetricBlock,
        TableBlock,
        TextBlock,
    )

    parts: list[str] = []
    parts.append(
        f"<h2 style='font-family:Pretendard,-apple-system,sans-serif'>{review.corpName} ({review.stockCode})</h2>"
    )

    if review.summaryCard:
        card = review.summaryCard
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

    if review.circulationSummary:
        parts.append(
            f"<div style='border:1px solid #ddd;padding:12px;margin:8px 0;border-radius:4px'>"
            f"<strong>재무 순환 서사</strong><br/>"
            f"{'<br/>'.join(review.circulationSummary.split(chr(10)))}</div>"
        )

    detailMode = getattr(review.layout, "detail", True)

    for section in review.sections:
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
                spec_json = json.dumps(block.spec, ensure_ascii=False, default=str)
                title = block.spec.get("title", "") if isinstance(block.spec, dict) else ""
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
                    # 과학 표기법 방지 — 큰 수는 조/억으로
                    if abs(v) >= 1e12:
                        cells.append(f"{v / 1e12:.1f}조")
                    elif abs(v) >= 1e8:
                        cells.append(f"{v / 1e8:.0f}억")
                    elif abs(v) >= 1e4:
                        cells.append(f"{v:,.0f}")
                    else:
                        cells.append(f"{v:,.2f}" if v != int(v) else f"{int(v):,}")
                else:
                    cells.append(str(v))
            rows.append("| " + " | ".join(cells) + " |")
        return "\n".join([header, sep] + rows)
    except (TypeError, ValueError, AttributeError):
        return str(df)


def renderMarkdown(review) -> str:
    """마크다운 렌더링."""
    from dartlab.review.blocks import (
        ChartBlock,
        FlagBlock,
        HeadingBlock,
        MetricBlock,
        TableBlock,
        TextBlock,
    )

    # ── 6막 헤더 매핑 (partId 주번호 → 막 제목 + 핵심 질문) ──
    _ACT_HEADERS: dict[str, tuple[str, str]] = {
        "1": ("제1막: 이 회사는 뭘 하는가", "매출의 원천은 무엇이고 얼마나 빨리 성장하는가?"),
        "2": ("제2막: 얼마나 잘 하는가", "번 돈이 얼마나 남고, 왜 그만큼 남는가?"),
        "3": ("제3막: 현금이 실제로 도는가", "이익이 현금으로 전환되는가? 이익이 진짜인가?"),
        "4": ("제4막: 자본 구조는 안전한가", "부채를 감당할 수 있는가?"),
        "5": ("제5막: 번 돈을 어떻게 쓰는가", "자산, 배당, 재투자 — 가치를 만드는 배분인가?"),
        "6": ("제6막: 앞으로 어떻게 될 것인가", "적정 가치는 얼마이고, 어떤 리스크가 있는가?"),
    }

    # ── 6막 전환 경계 매핑 (섹션 key → 전환 key) ──
    _ACT_BOUNDARIES: dict[str, str] = {
        "수익성": "1→2",
        "현금흐름": "2→3",
        "자금조달": "3→4",
        "자산구조": "4→5",
        "가치평가": "5→6",
    }

    # 스토리 템플릿에서 actFocus 로드
    actFocus: dict[str, str] = {}
    templateName = getattr(review, "template", None)
    if templateName:
        from dartlab.review.templates import STORY_TEMPLATES

        tmplInfo = STORY_TEMPLATES.get(templateName, {})
        actFocus = tmplInfo.get("actFocus", {})

    parts: list[str] = []
    parts.append(f"## {review.corpName} ({review.stockCode})\n")

    # ── 요약 카드 ──
    if review.summaryCard:
        card = review.summaryCard
        cardLines = []
        if card.conclusion:
            cardLines.append(f"**{card.conclusion}**")
        for s in card.strengths:
            cardLines.append(f"- [+] {s}")
        for w in card.warnings:
            cardLines.append(f"- [-] {w}")
        if cardLines:
            parts.append("\n".join(cardLines))

    # ── 스토리 템플릿 표시 ──
    if templateName:
        desc = tmplInfo.get("description", "") if tmplInfo else ""
        parts.append(f"**스토리: {templateName}** — {desc}")

        # 핵심 질문 표시
        keyQuestions = tmplInfo.get("keyQuestions", []) if tmplInfo else []
        if keyQuestions:
            qLines = [f"  - {q}" for q in keyQuestions]
            parts.append("> **핵심 질문**\n" + "\n".join(f"> {q}" for q in qLines))

    # ── 순환 서사 ──
    if review.circulationSummary:
        parts.append(f"> **재무 순환 서사**\n> {review.circulationSummary.replace(chr(10), chr(10) + '> ')}")

    detailMode = getattr(review.layout, "detail", True)

    # 막 결론 상태 초기화
    from dartlab.review.narrate import resetActSummaryState

    resetActSummaryState()

    # 이미 렌더링된 막 번호 + thread title 추적
    renderedActs: set[str] = set()
    renderedThreads: set[str] = set()
    # 막별 섹션 수집 (막 결론용)
    currentAct: str = ""
    currentActSections: list = []
    # threads 수집 (전체)
    allThreads: list = []
    for sec in review.sections:
        if sec.threads:
            allThreads.extend(sec.threads)

    for section in review.sections:
        # ── 6막 헤더 삽입 (해당 막의 첫 섹션일 때) ──
        actNum = getattr(section, "partId", "")
        mainAct = actNum.split("-")[0] if actNum else ""

        # 막이 바뀌면 이전 막 결론 삽입
        if mainAct and mainAct != currentAct and currentAct and currentActSections:
            from dartlab.review.narrate import buildActSummary

            actSummary = buildActSummary(currentAct, currentActSections, allThreads)
            if actSummary:
                parts.append(f"\n{actSummary}\n")
            currentActSections = []

        if mainAct:
            currentAct = mainAct

        if mainAct and mainAct in _ACT_HEADERS and mainAct not in renderedActs:
            renderedActs.add(mainAct)
            actTitle, actQuestion = _ACT_HEADERS[mainAct]
            parts.append(f"\n---\n\n# {actTitle}\n")
            parts.append(f"> **핵심 질문**: {actQuestion}")

            # actFocus 인트로 (스토리 템플릿이 있을 때)
            focus = actFocus.get(mainAct)
            if focus:
                parts.append(f"> **이 기업의 관전 포인트**: {focus}")

        # ── 막 전환 인과 문장 삽입 ──
        transKey = _ACT_BOUNDARIES.get(section.key)
        if transKey and hasattr(review, "actTransitions") and review.actTransitions:
            trans = review.actTransitions.get(transKey)
            if trans:
                parts.append(f"\n> **{transKey}** {trans}\n")

        if not detailMode:
            parts.append(f"### {section.title}")
            if section.summary:
                parts.append(f"*{section.summary}*")
            continue

        # ── Threads (인과 패턴) — 중복 건너뛰기 ──
        if section.threads:
            for t in section.threads:
                if t.title in renderedThreads:
                    continue
                renderedThreads.add(t.title)
                icon = {"critical": "[!!]", "warning": "[!]", "positive": "[+]", "neutral": "[-]"}
                parts.append(f"**{icon.get(t.severity, '')} {t.title}**")

        # ── 블록 렌더링 ──
        for block in section.blocks:
            isEmphasized = getattr(block, "emphasized", False)

            if isinstance(block, HeadingBlock):
                prefix = block.markdownPrefix
                mark = "\u2605 " if isEmphasized else ""
                parts.append(f"{prefix} {mark}{block.title}")
            elif isinstance(block, TextBlock):
                parts.append(block.text)
            elif isinstance(block, MetricBlock):
                for label, value in block.metrics:
                    parts.append(f"- **{label}**: {value}")
            elif isinstance(block, TableBlock):
                rendered = False
                if hasattr(block.df, "to_pandas"):
                    try:
                        pdf = block.df.to_pandas()
                        pdf.columns = [c[:-2] if isinstance(c, str) and c.endswith("Q4") else c for c in pdf.columns]
                        parts.append(pdf.to_markdown(index=False))
                        rendered = True
                    except (ImportError, Exception):
                        pass
                if not rendered:
                    parts.append(_polarsToMarkdown(block.df))
            elif isinstance(block, ChartBlock):
                title = block.spec.get("title", "\ucc28\ud2b8") if isinstance(block.spec, dict) else "\ucc28\ud2b8"
                parts.append(f"*[chart: {title}]*")
            elif isinstance(block, FlagBlock):
                for f in block.flags:
                    parts.append(f"- {block.icon} {f}")
            elif hasattr(block, "render"):
                parts.append(block.render("markdown"))

        currentActSections.append(section)

    # 마지막 막 결론
    if currentAct and currentActSections:
        from dartlab.review.narrate import buildActSummary

        actSummary = buildActSummary(currentAct, currentActSections, allThreads)
        if actSummary:
            parts.append(f"\n{actSummary}\n")

    return "\n\n".join(parts)


def renderJson(review) -> str:
    """JSON 렌더링."""
    from dartlab.review.blocks import (
        ChartBlock,
        FlagBlock,
        HeadingBlock,
        MetricBlock,
        TableBlock,
        TextBlock,
    )

    detailMode = getattr(review.layout, "detail", True)

    sections: list[dict[str, Any]] = []
    for section in review.sections:
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
        "stockCode": review.stockCode,
        "corpName": review.corpName,
        "sections": sections,
    }
    if review.summaryCard:
        card = review.summaryCard
        result["summaryCard"] = {
            "conclusion": card.conclusion,
            "strengths": card.strengths,
            "warnings": card.warnings,
            "grades": card.grades,
        }
    if review.circulationSummary:
        result["circulationSummary"] = review.circulationSummary

    return json.dumps(
        result,
        ensure_ascii=False,
        default=str,
    )
