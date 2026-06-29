"""scanner.scanNotes — panel SSOT 노트 구조 카탈로그 추출 검증.

_noteTitleFromContent(제목 정규화)는 순수(unit). scanNotes(panel 직독)는 requires_data.
"""

from __future__ import annotations

import pytest

from dartlab.providers.mappers.scanner import _noteTitleFromContent, scanNotes


@pytest.mark.unit
class TestNoteTitleFromContent:
    def test_strips_number_and_scope(self) -> None:
        assert _noteTitleFromContent("<P>8. 재고자산 (연결)</P>") == "재고자산"
        assert _noteTitleFromContent("4. 영업부문 (연결)") == "영업부문"
        assert _noteTitleFromContent("23. 비용의 성격별 분류 (별도)") == "비용의 성격별 분류"

    def test_rejects_non_title(self) -> None:
        # 표·산문(끝이 숫자/길다)은 제목 아님 → ""
        assert _noteTitleFromContent("<TABLE>취득원가 4,547 (292) 4,255</TABLE>") == ""
        assert _noteTitleFromContent("공시금액 급여 844,451 퇴직급여 12,571") == ""
        assert _noteTitleFromContent("") == ""
        assert _noteTitleFromContent(None) == ""


@pytest.mark.requires_data
class TestScanNotes:
    def test_returns_structured_catalog(self) -> None:
        items = scanNotes("005930")
        assert isinstance(items, dict)
        assert len(items) > 50  # 삼성전자 = 수백 라인아이템
        # 각 항목 스키마
        sample = next(iter(items.values()))
        for key in ("type", "category", "canonicalKey", "noteShape", "foreignCurrency", "count", "years"):
            assert key in sample
        # canonicalKey 는 NT_ 코드, noteShape 는 두 값 중 하나
        assert all(v["canonicalKey"].startswith("NT_") for v in items.values())
        assert all(v["noteShape"] in ("composition", "lineitem") for v in items.values())

    def test_missing_company_empty(self) -> None:
        assert scanNotes("999999") == {}
