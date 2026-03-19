"""데이터 소스 디스커버리 — registry 기반 자동 소스 트리 빌드.

Company 인스턴스를 받아 실제 사용 가능한 데이터 소스를 탐색하고,
카테고리별 트리 구조로 반환한다.

소비처:
- export/excel.py      → 내보내기 가능 모듈 자동 결정
- server API           → GET /api/sources/{stockCode}
- UI                   → ExcelExportPanel 소스 선택
- LLM tool             → create_template에서 소스 제안
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import polars as pl

from dartlab.core.registry import DataEntry, getEntries

if TYPE_CHECKING:
    from dartlab.engines.dart.company import Company


@dataclass
class SourceItem:
    """단일 데이터 소스 항목."""

    name: str
    label: str
    category: str
    dataType: str
    description: str
    available: bool
    columns: list[str] = field(default_factory=list)
    rowCount: int = 0


@dataclass
class SourceTree:
    """카테고리별 소스 트리."""

    stockCode: str
    corpName: str
    categories: dict[str, list[SourceItem]] = field(default_factory=dict)

    @property
    def totalSources(self) -> int:
        return sum(len(items) for items in self.categories.values())

    @property
    def availableSources(self) -> int:
        return sum(1 for items in self.categories.values() for item in items if item.available)

    def flat(self) -> list[SourceItem]:
        """카테고리 무관하게 전체 소스 flat list."""
        result = []
        for items in self.categories.values():
            result.extend(items)
        return result

    def availableFlat(self) -> list[SourceItem]:
        """사용 가능한 소스만 flat list."""
        return [s for s in self.flat() if s.available]

    def toDict(self) -> dict[str, Any]:
        """JSON 직렬화용 dict."""
        return {
            "stockCode": self.stockCode,
            "corpName": self.corpName,
            "totalSources": self.totalSources,
            "availableSources": self.availableSources,
            "categories": {
                cat: [
                    {
                        "name": s.name,
                        "label": s.label,
                        "category": s.category,
                        "dataType": s.dataType,
                        "description": s.description,
                        "available": s.available,
                        "columns": s.columns,
                        "rowCount": s.rowCount,
                    }
                    for s in items
                ]
                for cat, items in self.categories.items()
            },
        }


_CATEGORY_ORDER = ["finance", "report", "disclosure", "notes", "analysis", "raw"]

_FINANCE_NAMES = frozenset({"IS", "BS", "CF"})


def _probeFinance(c: Company, entry: DataEntry) -> SourceItem:
    """finance 카테고리 엔트리 프로브."""
    available = c._hasFinance
    return SourceItem(
        name=entry.name,
        label=entry.label,
        category=entry.category,
        dataType=entry.dataType,
        description=entry.description,
        available=available,
    )


def _probeNotes(c: Company, entry: DataEntry) -> SourceItem:
    """notes 카테고리 엔트리 프로브 (lazy — 실제 로드하지 않음)."""
    available = c._hasDocs
    return SourceItem(
        name=entry.name,
        label=entry.label,
        category=entry.category,
        dataType=entry.dataType,
        description=entry.description,
        available=available,
    )


def _probeRaw(c: Company, entry: DataEntry) -> SourceItem:
    """raw 카테고리 엔트리 프로브."""
    reqMap = {"docs": c._hasDocs, "finance": c._hasFinance, "report": c._hasReport}
    available = reqMap.get(entry.requires or "", False)
    return SourceItem(
        name=entry.name,
        label=entry.label,
        category=entry.category,
        dataType=entry.dataType,
        description=entry.description,
        available=available,
    )


def _probeAnalysis(c: Company, entry: DataEntry) -> SourceItem:
    """analysis 카테고리 엔트리 프로브."""
    if entry.requires == "finance":
        available = c._hasFinance
    else:
        available = True
    return SourceItem(
        name=entry.name,
        label=entry.label,
        category=entry.category,
        dataType=entry.dataType,
        description=entry.description,
        available=available,
    )


def _probeModule(c: Company, entry: DataEntry) -> SourceItem:
    """report/disclosure 카테고리 엔트리 프로브.

    실제 데이터를 getattr로 로드하여 available, columns, rowCount를 채운다.
    """
    reqMap = {"docs": c._hasDocs, "finance": c._hasFinance, "report": c._hasReport}
    reqOk = reqMap.get(entry.requires or "", True)
    if not reqOk:
        return SourceItem(
            name=entry.name,
            label=entry.label,
            category=entry.category,
            dataType=entry.dataType,
            description=entry.description,
            available=False,
        )

    attrName = entry.funcName or entry.name
    if entry.name in _FINANCE_NAMES:
        attrName = entry.name
    try:
        data = getattr(c, attrName, None)
    except (AttributeError, RuntimeError, TypeError, ValueError):
        data = None

    columns: list[str] = []
    rowCount = 0
    available = data is not None

    if isinstance(data, pl.DataFrame):
        columns = data.columns
        rowCount = data.height
        if rowCount == 0:
            available = False
    elif isinstance(data, dict):
        columns = list(data.keys())
        rowCount = len(data)

    return SourceItem(
        name=entry.name,
        label=entry.label,
        category=entry.category,
        dataType=entry.dataType,
        description=entry.description,
        available=available,
        columns=columns,
        rowCount=rowCount,
    )


def discoverSources(c: Company) -> SourceTree:
    """Company의 사용 가능한 데이터 소스를 탐색하여 SourceTree 반환.

    registry의 모든 엔트리를 순회하며, 각 카테고리에 맞는 프로브로
    데이터 존재 여부를 확인한다.
    """
    tree = SourceTree(stockCode=c.stockCode, corpName=c.corpName)

    probeMap = {
        "finance": _probeFinance,
        "notes": _probeNotes,
        "raw": _probeRaw,
        "analysis": _probeAnalysis,
    }

    for entry in getEntries():
        probe = probeMap.get(entry.category, _probeModule)
        item = probe(c, entry)
        tree.categories.setdefault(entry.category, []).append(item)

    ordered: dict[str, list[SourceItem]] = {}
    for cat in _CATEGORY_ORDER:
        if cat in tree.categories:
            ordered[cat] = tree.categories[cat]
    for cat in tree.categories:
        if cat not in ordered:
            ordered[cat] = tree.categories[cat]
    tree.categories = ordered

    return tree
