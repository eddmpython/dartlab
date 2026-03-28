from __future__ import annotations

import re as _re
from typing import Any

from dartlab import Company

from ..api.common import HANDLED_API_ERRORS
from ..cache import company_cache
from ..models import TocChapter, TocResponse, TocTopic

_VALID_CODE = _re.compile(r"^[A-Za-z0-9가-힣]{1,20}$")


def get_company(code: str) -> Company:
    """종목코드로 Company를 조회하거나 생성한다 (캐시 활용)."""
    if not _VALID_CODE.match(code):
        raise ValueError(f"유효하지 않은 종목코드: {code!r}")
    cached = company_cache.get(code)
    if cached:
        return cached[0]
    company = Company(code)
    company_cache.put(code, company, None)
    return company


def safe_topic_label(company, topic: str) -> str:
    """topic의 한글 라벨을 안전하게 반환한다."""
    try:
        return company._topicLabel(topic)
    except AttributeError:
        return topic


def _find_prev_comparable(periods: list[str], target: str) -> str | None:
    import re

    match = re.fullmatch(r"(\d{4})(Q[1-4])?", target)
    if not match:
        return None
    year, quarter = int(match.group(1)), match.group(2)
    best: str | None = None
    best_year = -1
    for period in periods:
        if period == target:
            continue
        period_match = re.fullmatch(r"(\d{4})(Q[1-4])?", period)
        if not period_match:
            continue
        period_year, period_quarter = int(period_match.group(1)), period_match.group(2)
        if quarter == period_quarter and period_year < year and period_year > best_year:
            best = period
            best_year = period_year
    return best


def filter_blocks_by_period(blocks: list, period: str) -> list:
    """뷰어 블록을 지정 기간과 직전 비교 기간만 남기도록 필터링한다."""
    filtered = []
    for block in blocks:
        if block.data is None:
            filtered.append(block)
            continue

        all_periods = block.meta.periods if block.meta.periods else []
        if period not in all_periods:
            filtered.append(block)
            continue

        prev = _find_prev_comparable(all_periods, period)
        keep_periods = [p for p in [period, prev] if p is not None and p in block.data.columns]
        non_period_cols = [column for column in block.data.columns if column not in all_periods]
        select_cols = non_period_cols + keep_periods

        from copy import copy

        new_block = copy(block)
        new_block.data = block.data.select([column for column in select_cols if column in block.data.columns])
        new_block.meta = type(block.meta)(
            unit=block.meta.unit,
            scale=block.meta.scale,
            scaleDivisor=block.meta.scaleDivisor,
            periods=keep_periods,
            rowCount=block.meta.rowCount,
            colCount=len(keep_periods),
        )
        filtered.append(new_block)
    return filtered


def build_toc(company: Company) -> dict[str, Any]:
    """뷰어 목차(Table of Contents)를 구성한다."""
    sec = company.sections
    if sec is None:
        return TocResponse(stockCode=company.stockCode, corpName=company.corpName, chapters=[]).model_dump()

    import re as _re

    import polars as pl

    chapter_map: dict[str, list[TocTopic]] = {}
    chapter_order: list[str] = []
    seen_topics: set[str] = set()

    finance_topics = ("BS", "IS", "CIS", "CF", "SCE", "ratios")
    finance_chapter = "III. 재무에 관한 사항"
    for topic in finance_topics:
        try:
            df = getattr(company, topic, None) if topic != "ratios" else None
            if topic == "ratios":
                ratio_pair = company._ratioSeries() if getattr(company, "_hasFinance", False) else None
                if ratio_pair is None:
                    continue
            elif df is None:
                continue
        except (AttributeError, TypeError):
            continue
        seen_topics.add(topic)
        if finance_chapter not in chapter_map:
            chapter_map[finance_chapter] = []
            chapter_order.append(finance_chapter)
        chapter_map[finance_chapter].append(
            TocTopic(topic=topic, label=safe_topic_label(company, topic), textCount=0, tableCount=1)
        )

    period_re = _re.compile(r"^\d{4}(Q[1-4])?$")
    period_cols = sorted([col for col in sec.columns if period_re.fullmatch(col)], reverse=True)
    latest2 = period_cols[:2] if len(period_cols) >= 2 else []

    if "topic" in sec.columns:
        for row in sec.iter_rows(named=True):
            topic = row.get("topic")
            if not isinstance(topic, str) or not topic or topic in seen_topics:
                continue
            seen_topics.add(topic)

            topic_frame = sec.filter(pl.col("topic") == topic)
            block_types = topic_frame["blockType"] if "blockType" in topic_frame.columns else None
            text_count = block_types.eq("text").sum() if block_types is not None else topic_frame.height
            table_count = block_types.eq("table").sum() if block_types is not None else 0

            has_changes = False
            if latest2 and block_types is not None:
                text_rows = topic_frame.filter(pl.col("blockType") == "text")
                for text_row in text_rows.iter_rows(named=True):
                    current = str(text_row.get(latest2[0]) or "").strip()
                    previous = str(text_row.get(latest2[1]) or "").strip()
                    if current and previous and current != previous:
                        has_changes = True
                        break

            chapter_value = topic_frame.item(0, "chapter") if "chapter" in topic_frame.columns else None
            chapter = chapter_value if isinstance(chapter_value, str) and chapter_value else "기타"
            if chapter not in chapter_map:
                chapter_map[chapter] = []
                chapter_order.append(chapter)
            chapter_map[chapter].append(
                TocTopic(
                    topic=topic,
                    label=safe_topic_label(company, topic),
                    textCount=int(text_count),
                    tableCount=int(table_count),
                    hasChanges=has_changes,
                )
            )

    roman_order = {
        "I": 1,
        "II": 2,
        "III": 3,
        "IV": 4,
        "V": 5,
        "VI": 6,
        "VII": 7,
        "VIII": 8,
        "IX": 9,
        "X": 10,
        "XI": 11,
        "XII": 12,
    }

    def _chapter_sort_key(chapter: str) -> tuple[int, str]:
        prefix = chapter.split(".")[0].strip()
        return (roman_order.get(prefix, 99), chapter)

    sorted_chapters = sorted(chapter_order, key=_chapter_sort_key)
    chapters = [TocChapter(chapter=chapter, topics=chapter_map[chapter]) for chapter in sorted_chapters]
    return TocResponse(stockCode=company.stockCode, corpName=company.corpName, chapters=chapters).model_dump()


def build_viewer(company: Company, topic: str) -> dict[str, Any]:
    """topic별 뷰어 블록과 텍스트 문서를 직렬화하여 반환한다."""
    from dartlab.providers.dart.docs.viewer import (
        serializeViewerBlock,
        serializeViewerTextDocument,
        viewerBlocks,
        viewerTextDocument,
    )

    if not hasattr(company, "_viewer_cache"):
        company._viewer_cache = {}
    if topic in company._viewer_cache:
        blocks = company._viewer_cache[topic]
    else:
        blocks = viewerBlocks(company, topic)
        company._viewer_cache[topic] = blocks

    return {
        "stockCode": company.stockCode,
        "corpName": company.corpName,
        "topic": topic,
        "topicLabel": safe_topic_label(company, topic),
        "period": None,
        "blocks": [serializeViewerBlock(block) for block in blocks],
        "textDocument": serializeViewerTextDocument(viewerTextDocument(topic, blocks)),
    }


def build_diff_summary(company: Company, topic: str) -> dict[str, Any] | None:
    """topic의 기간 간 변경 요약(변경률, 추가/삭제 발췌)을 생성한다."""
    try:
        from dartlab.core.docs.diff import sectionsDiff

        sec = company.docs.sections
        if sec is None:
            return None

        diff_result = sectionsDiff(sec)
        topic_summaries = [summary for summary in diff_result.summaries if summary.topic == topic]
        total_changed = sum(summary.changedCount for summary in topic_summaries)
        max_periods = max((summary.totalPeriods for summary in topic_summaries), default=0)
        change_rate = (
            round(total_changed / max(1, (max_periods - 1) * len(topic_summaries)), 3) if topic_summaries else 0.0
        )

        topic_entries = [entry for entry in diff_result.entries if entry.topic == topic]
        added: list[str] = []
        removed: list[str] = []
        latest_from: str | None = None
        latest_to: str | None = None

        if topic_entries:
            import difflib

            import polars as pl

            latest = max(topic_entries, key=lambda entry: entry.toPeriod)
            latest_from = latest.fromPeriod
            latest_to = latest.toPeriod

            filtered = sec.filter(pl.col("topic") == topic)
            for row in filtered.iter_rows(named=True):
                from_text = str(row.get(latest_from) or "").strip()
                to_text = str(row.get(latest_to) or "").strip()
                if not from_text and not to_text:
                    continue
                if from_text == to_text:
                    continue
                from_lines = from_text.splitlines()
                to_lines = to_text.splitlines()
                for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, from_lines, to_lines).get_opcodes():
                    if tag in ("insert", "replace"):
                        for line in to_lines[j1:j2]:
                            line = line.strip()
                            if line and len(added) < 3:
                                added.append(line[:120])
                    if tag in ("delete", "replace"):
                        for line in from_lines[i1:i2]:
                            line = line.strip()
                            if line and len(removed) < 3:
                                removed.append(line[:120])
                if len(added) >= 3 and len(removed) >= 3:
                    break

        return {
            "stockCode": company.stockCode,
            "corpName": company.corpName,
            "topic": topic,
            "changeRate": change_rate,
            "changedCount": total_changed,
            "totalPeriods": max_periods,
            "latestFrom": latest_from,
            "latestTo": latest_to,
            "added": added,
            "removed": removed,
        }
    except HANDLED_API_ERRORS:
        return None
