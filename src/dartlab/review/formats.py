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

    for section in review.sections:
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

    for section in review.sections:
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
                if hasattr(block.df, "to_pandas"):
                    try:
                        parts.append(block.df.to_pandas().to_markdown(index=False))
                    except ImportError:
                        parts.append(str(block.df))
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

    sections: list[dict[str, Any]] = []
    for section in review.sections:
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
        sections.append(
            {
                "key": section.key,
                "title": section.title,
                "blocks": items,
            }
        )

    return json.dumps(
        {"stockCode": review.stockCode, "corpName": review.corpName, "sections": sections},
        ensure_ascii=False,
        default=str,
    )
