"""frame.inventory 완전 인벤토리 불변식.

데이터 없이 실행 가능한 계약·헬퍼 불변식 + 미존재 회사 빈 결과. 실제 열거 스팟체크는 로컬 panel 필요.
"""

from __future__ import annotations

import polars as pl

from dartlab.frame.inventory import (
    _narrativeConceptIndex,
    _normalizeTitle,
    _noteConceptIndex,
    reportInventory,
)


def test_emptyBoardEmptyInventory():
    """빈 board 주입 시 빈 인벤토리(예외 없음, 네트워크 무접촉)."""
    inv = reportInventory("000000000", board=pl.DataFrame())
    assert inv["summary"]["total"] == 0
    assert inv["units"] == []


def test_normalizeTitleStripsNumberPrefix():
    """정규화는 번호 접두를 제거(회사 간 안정 키)."""
    assert _normalizeTitle("8. 재고자산") == "재고자산"
    assert _normalizeTitle("II. 사업의 내용") == "사업의 내용"
    assert _normalizeTitle("재무위험관리") == "재무위험관리"


def test_noteConceptIndexNonEmpty():
    """노트 conceptIndex 는 카탈로그 노트 canonicalKey family 를 커버."""
    idx = _noteConceptIndex()
    assert idx.get("NT_D82638") == "note.inventory"
    assert idx.get("NT_D83511") == "note.tax"


def test_narrativeConceptIndexNonEmpty():
    """내러티브 conceptIndex 는 (키워드, conceptId) 쌍."""
    idx = _narrativeConceptIndex()
    keywords = {kw for kw, _ in idx}
    assert "매출 및 수주" in keywords
    assert any(cid == "narrative.salesOrder" for _, cid in idx)


def test_inventoryShapeContract():
    """인벤토리 반환 계약(빈 board 로 shape 검증, 네트워크 무접촉)."""
    inv = reportInventory("000000000", board=pl.DataFrame())
    assert set(inv.keys()) == {"code", "units", "summary"}
    assert set(inv["summary"].keys()) >= {"total", "byKind"}
