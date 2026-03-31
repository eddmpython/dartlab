"""review 멀티포맷 렌더링 (html/markdown/json)."""

from __future__ import annotations

import json
from typing import Any


def renderHtml(review) -> str:
    """HTML 렌더링."""
    from dartlab.review.blocks import (
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
                tag = "h3" if block.level == 1 else "h4"
                parts.append(f"<{tag}>{block.title}</{tag}>")
            elif isinstance(block, TextBlock):
                parts.append(f"<p>{block.text}</p>")
            elif isinstance(block, MetricBlock):
                rows = "".join(f"<tr><td>{label}</td><td>{value}</td></tr>" for label, value in block.metrics)
                parts.append(f"<table>{rows}</table>")
            elif isinstance(block, TableBlock):
                if hasattr(block.df, "_repr_html_"):
                    parts.append(block.df._repr_html_())
            elif isinstance(block, FlagBlock):
                icon = "⚠" if block.kind == "warning" else "✦"
                for f in block.flags:
                    parts.append(f"<p>{icon} {f}</p>")
            elif hasattr(block, "render"):
                parts.append(block.render("html"))

    return "<div style='display:flex;flex-direction:column;gap:16px'>" + "".join(parts) + "</div>"


def renderMarkdown(review) -> str:
    """마크다운 렌더링."""
    from dartlab.review.blocks import (
        FlagBlock,
        HeadingBlock,
        MetricBlock,
        TableBlock,
        TextBlock,
    )

    parts: list[str] = []
    parts.append(f"## {review.corpName} ({review.stockCode})\n")

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

    if review.circulationSummary:
        parts.append(f"> **재무 순환 서사**\n> {review.circulationSummary.replace(chr(10), chr(10) + '> ')}")

    detailMode = getattr(review.layout, "detail", True)

    # 6막 전환 경계 매핑 (섹션 key → 전환 key)
    _ACT_BOUNDARIES = {
        "수익성": "1→2",    # 1막 끝 → 2막 시작
        "현금흐름": "2→3",  # 2막 끝 → 3막 시작
        "자금조달": "3→4",  # 3막 끝 → 4막 시작
        "자산구조": "4→5",  # 4막 끝 → 5막 시작
        "가치평가": "5→6",  # 5막 끝 → 6막 시작
    }

    for section in review.sections:
        # 막 전환 인과 문장 삽입
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
        if section.threads:
            for t in section.threads:
                icon = {"critical": "[!!]", "warning": "[!]", "positive": "[+]", "neutral": "[-]"}
                parts.append(f"**{icon.get(t.severity, '')} {t.title}**")
        for block in section.blocks:
            if isinstance(block, HeadingBlock):
                prefix = "###" if block.level == 1 else "####"
                parts.append(f"{prefix} {block.title}")
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
                        # Q4 fallback 컬럼 → 연도 라벨로 치환 (2025Q4 → 2025)
                        pdf.columns = [c[:-2] if isinstance(c, str) and c.endswith("Q4") else c for c in pdf.columns]
                        parts.append(pdf.to_markdown(index=False))
                        rendered = True
                    except (ImportError, Exception):
                        pass
                if not rendered:
                    # Polars str() fallback — shape/타입 행 제거
                    raw = str(block.df)
                    cleaned = []
                    for l in raw.split("\n"):
                        if l.startswith("shape:"):
                            continue
                        # --- 행 (separator) 과 타입 행 (str, i64, f64 등) 제거
                        inner = l.replace("│", "").replace("┆", "").strip()
                        tokens = inner.split()
                        if tokens and all(
                            t in ("---", "str", "i64", "f64", "i32", "u32", "bool", "date", "null") for t in tokens
                        ):
                            continue
                        cleaned.append(l)
                    parts.append("\n".join(cleaned))
            elif isinstance(block, FlagBlock):
                icon = "⚠" if block.kind == "warning" else "✦"
                for f in block.flags:
                    parts.append(f"- {icon} {f}")
            elif hasattr(block, "render"):
                parts.append(block.render("markdown"))

    return "\n\n".join(parts)


def renderJson(review) -> str:
    """JSON 렌더링."""
    from dartlab.review.blocks import (
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
