"""템플릿 CRUD 저장소 — ~/.dartlab/templates/ 기반 파일 스토어.

사용법::

    from dartlab.export.store import TemplateStore
    store = TemplateStore()

    store.save(template)          # 저장 (신규 or 업데이트)
    store.list()                  # 전체 목록
    store.get("t_1234567890")     # 단일 조회
    store.delete("t_1234567890")  # 삭제
"""

from __future__ import annotations

import json
from pathlib import Path

from dartlab.export.template import PRESETS, ExcelTemplate


def _defaultDir() -> Path:
    """기본 템플릿 저장 디렉토리."""
    return Path.home() / ".dartlab" / "templates"


class TemplateStore:
    """파일 기반 템플릿 CRUD.

    저장 구조: {storeDir}/{templateId}.json
    프리셋은 "preset_" prefix로 구분하며 삭제/수정 불가.
    """

    def __init__(self, storeDir: Path | None = None):
        self._dir = storeDir or _defaultDir()
        self._dir.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[ExcelTemplate]:
        """프리셋 + 사용자 템플릿 전체 목록."""
        result: list[ExcelTemplate] = list(PRESETS.values())

        for p in sorted(self._dir.glob("*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                t = ExcelTemplate.fromDict(data)
                if not t.templateId.startswith("preset_"):
                    result.append(t)
            except (json.JSONDecodeError, KeyError):
                continue
        return result

    def get(self, templateId: str) -> ExcelTemplate | None:
        """ID로 단일 조회."""
        if templateId.startswith("preset_"):
            for preset in PRESETS.values():
                if preset.templateId == templateId:
                    return preset
            return None

        path = self._dir / f"{templateId}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return ExcelTemplate.fromDict(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def save(self, template: ExcelTemplate) -> str:
        """저장 (신규 or 업데이트). templateId 반환."""
        if template.templateId.startswith("preset_"):
            raise ValueError("프리셋 템플릿은 수정할 수 없습니다.")

        import time

        template.updatedAt = time.time()
        path = self._dir / f"{template.templateId}.json"
        path.write_text(template.toJson(), encoding="utf-8")
        return template.templateId

    def delete(self, templateId: str) -> bool:
        """삭제. 프리셋은 삭제 불가."""
        if templateId.startswith("preset_"):
            return False
        path = self._dir / f"{templateId}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def exists(self, templateId: str) -> bool:
        """존재 여부 확인."""
        if templateId.startswith("preset_"):
            return any(p.templateId == templateId for p in PRESETS.values())
        return (self._dir / f"{templateId}.json").exists()
