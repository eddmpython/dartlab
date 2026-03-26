"""포커스/diff 컨텍스트 빌드 — server 의존성 없는 순수 로직.

server/chat.py의 build_focus_context(), build_diff_context()에서 추출.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from .dialogue import ConversationState


def _stringify_focus_value(value: Any, *, max_rows: int = 12, max_chars: int = 2400) -> str:
    from dartlab.ai.context.builder import df_to_markdown

    if value is None:
        return "(데이터 없음)"
    if isinstance(value, pl.DataFrame):
        return df_to_markdown(value, max_rows=max_rows, compact=True)
    text = str(value)
    return text if len(text) <= max_chars else text[:max_chars] + "\n... (truncated)"


def _build_topic_diff_snippet(company: Any, topic: str, *, max_entries: int = 3) -> str | None:
    """특정 topic의 최근 기간간 변화를 요약 텍스트로 반환."""
    if not hasattr(company, "diff"):
        return None
    try:
        topic_diff_df = company.diff(topic)
    except (AttributeError, KeyError, TypeError, ValueError):
        return None
    if topic_diff_df is None or not isinstance(topic_diff_df, pl.DataFrame) or topic_diff_df.height == 0:
        return None

    lines = ["### 기간간 변화 이력"]
    for row in topic_diff_df.head(max_entries).iter_rows(named=True):
        from_p = row.get("fromPeriod", "?")
        to_p = row.get("toPeriod", "?")
        status = row.get("status", "?")
        from_len = row.get("fromLen", 0)
        to_len = row.get("toLen", 0)
        delta = to_len - from_len
        sign = "+" if delta > 0 else ""
        lines.append(f"- {from_p} → {to_p}: **{status}** (글자수 {from_len:,} → {to_len:,}, {sign}{delta:,})")
    return "\n".join(lines)


def build_focus_context(company: Any, state: ConversationState) -> str | None:
    """현재 viewer/topic 맥락을 LLM 입력용 근거 블록으로 승격."""
    if not state.topic or not hasattr(company, "show"):
        return None

    lines = ["## 현재 사용자가 보고 있는 섹션"]
    lines.append(f"- topic: `{state.topic}`")
    if state.topic_label:
        lines.append(f"- label: {state.topic_label}")
    if state.period:
        lines.append(f"- period: {state.period}")
    if state.company and state.stock_code:
        lines.append(f"- company: {state.company} ({state.stock_code})")

    # 뷰어에서 선택한 블록 데이터가 있으면 직접 삽입
    if state.viewer_data:
        vd = state.viewer_data
        lines.append("")
        lines.append("### 사용자가 선택한 블록")
        if vd.get("topicLabel"):
            lines.append(f"- 주제: {vd['topicLabel']}")
        if vd.get("blockType"):
            lines.append(f"- 유형: {vd['blockType']}")
        if vd.get("preview"):
            lines.append(f"- 미리보기: {vd['preview']}")
        table = vd.get("table")
        if table and table.get("columns") and table.get("rows"):
            cols = table["columns"]
            rows = table["rows"]
            lines.append("")
            lines.append("#### 블록 테이블 데이터")
            lines.append("| " + " | ".join(str(c) for c in cols) + " |")
            lines.append("| " + " | ".join("---" for _ in cols) + " |")
            for row in rows[:30]:
                vals = [str(row.get(c, "")) for c in cols]
                lines.append("| " + " | ".join(vals) + " |")
            if len(rows) > 30:
                lines.append(f"... 외 {len(rows) - 30}행")
        lines.append("")
        lines.append("위 블록 데이터를 근거로 분석해주세요.")

    try:
        if state.period:
            overview = company.show(state.topic, period=state.period)
        else:
            overview = company.show(state.topic)
    except (AttributeError, KeyError, TypeError, ValueError):
        overview = None

    if isinstance(overview, pl.DataFrame) and overview.height > 0:
        lines.append("")
        lines.append("### 블록 목차")
        lines.append(_stringify_focus_value(overview, max_rows=6))

        block_col = (
            "block" if "block" in overview.columns else "blockOrder" if "blockOrder" in overview.columns else None
        )
        if block_col:
            first_block = overview.row(0, named=True).get(block_col)
            if isinstance(first_block, int):
                try:
                    block_value = company.show(state.topic, first_block)
                except (AttributeError, KeyError, TypeError, ValueError):
                    block_value = None
                if block_value is not None:
                    lines.append("")
                    lines.append(f"### 현재 섹션 대표 block={first_block}")
                    lines.append(_stringify_focus_value(block_value))

    # 실제 텍스트 본문 포함
    if isinstance(overview, pl.DataFrame) and overview.height > 0:
        block_col_for_text = (
            "block" if "block" in overview.columns else "blockOrder" if "blockOrder" in overview.columns else None
        )
        if block_col_for_text:
            text_chars = 0
            max_text_body = 4000
            for row in overview.iter_rows(named=True):
                btype = row.get("type", row.get("blockType", ""))
                if btype != "text":
                    continue
                bidx = row.get(block_col_for_text)
                if not isinstance(bidx, int):
                    continue
                try:
                    block_value = company.show(state.topic, bidx)
                except (AttributeError, KeyError, TypeError, ValueError):
                    continue
                if block_value is None:
                    continue
                body = _stringify_focus_value(block_value, max_rows=20, max_chars=2000)
                if text_chars + len(body) > max_text_body:
                    break
                lines.append("")
                lines.append(f"### 공시 원문 (block {bidx})")
                lines.append(body)
                text_chars += len(body)

    if hasattr(company, "trace"):
        try:
            trace = company.trace(state.topic)
        except (AttributeError, KeyError, TypeError, ValueError):
            trace = None
        if trace:
            lines.append("")
            lines.append("### source trace")
            lines.append(_stringify_focus_value(trace, max_chars=1600))

    diff_text = _build_topic_diff_snippet(company, state.topic)
    if diff_text:
        lines.append("")
        lines.append(diff_text)

    return "\n".join(lines)


def build_diff_context(company: Any, *, top_n: int = 8) -> str | None:
    """전체 sections diff 요약을 LLM 컨텍스트 문자열로 변환."""
    if not hasattr(company, "diff"):
        return None
    try:
        summary_df = company.diff()
    except (AttributeError, KeyError, TypeError, ValueError):
        return None
    if summary_df is None or not isinstance(summary_df, pl.DataFrame) or summary_df.height == 0:
        return None

    changed_col = "changed" if "changed" in summary_df.columns else "changedCount"
    periods_col = "periods" if "periods" in summary_df.columns else "totalPeriods"
    rate_col = "changeRate"

    if changed_col not in summary_df.columns:
        return None

    agg_cols = [
        pl.col(periods_col).max().alias("periods"),
        pl.col(changed_col).sum().alias("changed"),
    ]
    if rate_col in summary_df.columns:
        agg_cols.append(pl.col(rate_col).max().alias("changeRate"))
    group_cols = ["topic"]
    if "chapter" in summary_df.columns:
        group_cols.insert(0, "chapter")
    summary_df = summary_df.group_by(group_cols).agg(agg_cols)
    changed_col = "changed"
    periods_col = "periods"

    _FINANCE_TOPICS = {
        "financialNotes",
        "financialStatements",
        "consolidatedStatements",
        "auditReport",
        "auditOpinion",
    }
    summary_df = summary_df.filter(~pl.col("topic").is_in(_FINANCE_TOPICS))

    changed = summary_df.filter(pl.col(changed_col) > 0)
    if changed.height == 0:
        return None

    if rate_col in changed.columns:
        changed = changed.sort([rate_col, changed_col], descending=[True, False]).head(top_n)
    else:
        changed = changed.sort(changed_col, descending=True).head(top_n)

    lines = [
        "## 공시 텍스트 변화 핫스팟",
        f"최근 기간간 텍스트 변경이 많은 topic {changed.height}개:",
        "",
        "| topic | 기간수 | 변경횟수 | 변화율 |",
        "|-------|--------|----------|--------|",
    ]
    for row in changed.iter_rows(named=True):
        topic = row.get("topic", "?")
        total = row.get(periods_col, 0)
        cnt = row.get(changed_col, 0)
        rate = row.get(rate_col, cnt / max(total - 1, 1) if total > 1 else 0)
        lines.append(f"| {topic} | {total} | {cnt} | {rate:.0%} |")

    lines.append("")
    lines.append("변화율이 높은 섹션은 사업 전략, 리스크, 실적 변동 등 핵심 변화를 담고 있을 가능성이 높습니다.")
    return "\n".join(lines)
