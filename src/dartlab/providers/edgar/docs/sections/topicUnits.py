"""EDGAR docs 보고서 단위 경량 열거 (topic 목록만, 본문 무접촉).

한 filer 의 SEC 보고서에 실재하는 모든 섹션 단위(10-K/10-Q/20-F Item)를 안정 topic handle 과 함께 열거한다.
`pipeline.sections()` 는 topic x period 본문(content_plain/raw)을 materialize 해 무겁다. 본 모듈은 열거만
필요하므로 **topic 컬럼만 projection** 한다(OOM 가드): artifact 있으면 `loadSectionsLong(columns=[topic,
blockType])` distinct, 없으면 legacy docs parquet 의 section_title 만 scan 후 `mapSectionTitle`. 반환 handle
은 `sections()` 가 emit 하는 topic 과 동일(``form::itemId``)이라 `get(handle)` round-trip 이 보장된다.

**계층 (providers/edgar/docs/sections, L1)**: core(dataLoader)·같은 sections 형제(topics·mapper·
sectionsStorage) 만 import. frame(L1.5) 인벤토리·audit census 가 downward 로 재사용(DRY).
"""

from __future__ import annotations

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.polarsUtil import isEmptyDf
from dartlab.providers.edgar.docs.sections.mapper import mapSectionTitle
from dartlab.providers.edgar.docs.sections.sectionsStorage import (
    hasSectionsArtifact,
    loadSectionsLong,
)
from dartlab.providers.edgar.docs.sections.topics import topicChapterLabel


def _unit(topic: str, hasText: bool, hasTable: bool) -> dict:
    """topic 을 (chapter, label) 해소해 단위 dict 로 만든다."""
    form, itemId = topic.split("::", 1) if "::" in topic else ("", topic)
    chapter, title = topicChapterLabel(topic)
    return {
        "topic": topic,
        "form": form,
        "itemId": itemId,
        "chapter": chapter,
        "title": title,
        "hasText": hasText,
        "hasTable": hasTable,
    }


def _fromArtifact(ticker: str) -> list[dict] | None:
    """sections artifact 에서 topic 컬럼만 projection 해 열거 (본문 페이지fault 0)."""
    long = loadSectionsLong(ticker, columns=["topic", "blockType"])
    if long is None or long.is_empty() or "topic" not in long.columns:
        return None
    hasBlock = "blockType" in long.columns
    out: list[dict] = []
    for key, sub in long.group_by("topic"):
        topic = key[0] if isinstance(key, tuple) else key
        if not topic:
            continue
        blocks = set(sub.get_column("blockType").drop_nulls().to_list()) if hasBlock else set()
        hasText = ("text" in blocks) or ("heading" in blocks) or not blocks
        hasTable = "table" in blocks
        out.append(_unit(topic, hasText, hasTable))
    return out


def _fromLegacy(ticker: str) -> list[dict] | None:
    """legacy docs parquet 의 section_title 만 scan 해 열거 (artifact 부재 fallback).

    미존재 ticker 의 loadData 자동 다운로드 실패(ValueError/네트워크)는 삼켜 [] 로 수렴(열거 전용).
    """
    try:
        df = loadData(ticker, category="edgarDocs")
    except (ValueError, OSError, pl.exceptions.PolarsError):
        return None
    if isEmptyDf(df) or "section_title" not in df.columns or "form_type" not in df.columns:
        return None
    pairs = df.select(["form_type", "section_title"]).drop_nulls().unique()
    seen: dict[str, dict] = {}
    for row in pairs.iter_rows(named=True):
        form = str(row["form_type"] or "")
        title = str(row["section_title"] or "")
        if not form or not title:
            continue
        topic = mapSectionTitle(form, title)
        seen.setdefault(topic, _unit(topic, hasText=True, hasTable=False))
    return list(seen.values())


def topicUnits(ticker: str) -> list[dict]:
    """한 US filer 의 보고서 섹션 단위(SEC Item)를 topic handle 과 함께 열거한다.

    artifact 우선(topic 컬럼 projection), 부재 시 legacy docs scan. 본문은 읽지 않는다(열거 전용).

    Args:
        ticker: US ticker (예 "AAPL").

    Returns:
        [{topic, form, itemId, chapter, title, hasText, hasTable}] 리스트. topic 은 ``form::itemId``
        (예 "10-K::item1Business")로 `sections()`/`get(handle)` 와 round-trip 일치. 데이터 부재 시 [].

    Raises:
        없음.

    Example:
        >>> from dartlab.providers.edgar.docs.sections.topicUnits import topicUnits
        >>> [u["topic"] for u in topicUnits("AAPL")][:1]  # doctest: +SKIP
        ['10-K::item1Business']

    Capabilities:
        - 손 카탈로그 없이 US 보고서 전 섹션(Item) 단위를 경량 열거(본문 무접촉, OOM 안전).

    Guide:
        - "이 미국 회사 보고서에 뭐가 다 있나" -> topicUnits(ticker).
        - 단위 실제 추출 -> pipeline.sections(ticker).filter(topic == handle).

    AIContext:
        US 사업보고서 인벤토리/횡단 census 의 열거 원천. DART panel 열거의 EDGAR 대응.

    Requires:
        - sections artifact 또는 legacy edgarDocs parquet. core.dataLoader·sections.topics·mapper.
    """
    units = _fromArtifact(ticker) if hasSectionsArtifact(ticker) else None
    if units is None:
        units = _fromLegacy(ticker)
    return units or []


__all__ = ["topicUnits"]
