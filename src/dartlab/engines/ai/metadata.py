"""모듈별 LLM 컨텍스트 메타데이터 — core/registry.py 위임 호환 레이어.

기존 MODULE_META, ModuleMeta, ColumnMeta, get_meta 인터페이스를 유지하면서
실제 데이터는 core/registry.py에서 가져온다.

신규 코드에서는 core/registry.py를 직접 사용할 것.
"""

from __future__ import annotations

from dartlab.core.registry import ColumnMeta, DataEntry, getEntries

__all__ = ["ColumnMeta", "ModuleMeta", "MODULE_META", "get_meta"]


class ModuleMeta:
    """registry DataEntry → 기존 ModuleMeta 호환 래퍼."""

    __slots__ = (
        "label",
        "description",
        "unit",
        "columns",
        "analysisHints",
        "relatedModules",
        "maxRows",
    )

    def __init__(self, entry: DataEntry):
        self.label = entry.label
        self.description = entry.description
        self.unit = entry.unit
        self.columns = entry.columns
        self.analysisHints = entry.analysisHints
        self.relatedModules = entry.relatedModules
        self.maxRows = entry.maxRows


def _buildModuleMeta() -> dict[str, ModuleMeta]:
    """registry에서 MODULE_META dict 자동 생성."""
    result: dict[str, ModuleMeta] = {}
    for entry in getEntries():
        if entry.category in ("finance", "raw"):
            continue
        if entry.name.startswith("notes."):
            continue
        result[entry.name] = ModuleMeta(entry)
    return result


MODULE_META: dict[str, ModuleMeta] = _buildModuleMeta()


def get_meta(name: str) -> ModuleMeta | None:
    """모듈명으로 메타데이터 조회."""
    return MODULE_META.get(name)
