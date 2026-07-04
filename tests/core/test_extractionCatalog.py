"""extractionCatalog 불변식 + EDGAR 태그 SSOT 드리프트 가드.

카탈로그는 순수 데이터라 로컬 데이터 없이 항상 실행 가능(CI 상주 게이트). census(실제 커버리지)는
로컬 parquet 필요라 별도 CLI(tests/audit/extractionCoverageCensus.py).
"""

from __future__ import annotations

from dartlab.core.extractionCatalog import (
    AXIS_TYPES,
    CATEGORIES,
    VALUE_TYPES,
    DartSource,
    EdgarSource,
    HonestNull,
    catalogSummary,
    conceptsByCategory,
    edgarTagsFor,
    getConcept,
    getExtractionConcepts,
    parityMatrix,
    resolveNoteKey,
)


def test_conceptIdUnique():
    """conceptId 는 전역 유일."""
    ids = [c.conceptId for c in getExtractionConcepts()]
    assert len(ids) == len(set(ids)), "중복 conceptId 존재"


def test_categoriesValid():
    """모든 개념의 category 는 CATEGORIES 어휘."""
    for c in getExtractionConcepts():
        assert c.category in CATEGORIES, f"{c.conceptId}: 미등록 category {c.category}"


def test_axisAndValueTypesValid():
    """axisType/valueType 은 어휘 안."""
    for c in getExtractionConcepts():
        assert c.axisType in AXIS_TYPES, f"{c.conceptId}: bad axisType {c.axisType}"
        assert c.valueType in VALUE_TYPES, f"{c.conceptId}: bad valueType {c.valueType}"


def test_noteConceptShape():
    """note 개념은 NT_ canonicalKey DART 표면을 가진다."""
    for c in getExtractionConcepts(category="note"):
        assert isinstance(c.dart, DartSource) and c.dart.surface == "note"
        assert c.dart.key.startswith("NT_"), f"{c.conceptId}: NT_ 아님 {c.dart.key}"


def test_narrativeConceptShape():
    """narrative 개념은 narrativeAnchor(chapter, section) 를 가진다."""
    for c in getExtractionConcepts(category="narrative"):
        assert c.narrativeAnchor is not None and len(c.narrativeAnchor) == 2


def test_honestNullHasReason():
    """EDGAR HonestNull 은 사유를 명시(능력부족 포장 금지)."""
    for c in getExtractionConcepts():
        if isinstance(c.edgar, HonestNull):
            assert c.edgar.reason.strip(), f"{c.conceptId}: HonestNull 사유 누락"


def test_registeredNotesResolveByName():
    """등록(first-class) 노트는 conceptId/bareName/한글라벨 3형태 모두 canonicalKey 로 해소된다.

    P1: 고가치 노트 10 + 레거시 12 = first-class 이름 접근. resolveNoteKey 가 panel 폴백의 SSOT.
    """
    reg = [c for c in getExtractionConcepts(category="note") if c.registered]
    assert len(reg) >= 22, f"등록 노트 22+ 기대, 실제 {len(reg)}"
    for c in reg:
        key = c.dart.key
        assert resolveNoteKey(c.conceptId) == key, f"{c.conceptId} conceptId 해소 실패"
        assert resolveNoteKey(c.conceptId.removeprefix("note.")) == key, f"{c.conceptId} bareName 해소 실패"
        assert resolveNoteKey(c.label) == key, f"{c.conceptId} label({c.label}) 해소 실패"


def test_resolveNoteKeyUnknownReturnsNone():
    """미등록 이름은 None(폴백 무발동, 기존 경로 보존)."""
    assert resolveNoteKey("존재하지않는노트") is None
    assert resolveNoteKey("NT_D826380") is None  # canonicalKey 자체는 별칭 아님(무한재귀 방지)


def test_toDictRoundtrip():
    """toDict 는 parity 포함 직렬화 dict 를 낸다."""
    d = getConcept("note.tax").toDict()
    assert d["conceptId"] == "note.tax"
    assert d["parity"] in ("both", "dartOnly", "edgarOnly", "narrative", "none")
    assert d["edgar"]["surface"] == "xbrlTag"


def test_summaryAndParityConsistent():
    """catalogSummary 총계 = 카테고리 합 = parity 합."""
    s = catalogSummary()
    assert s["total"] == sum(s["byCategory"].values())
    assert s["total"] == sum(s["parity"].values())
    assert s["total"] == len(getExtractionConcepts())


def test_conceptsByCategoryKeysAreCategories():
    """conceptsByCategory 키는 CATEGORIES 상주."""
    assert set(conceptsByCategory().keys()) == set(CATEGORIES)


def test_edgarTagSsotDriftGuard():
    """카탈로그 EDGAR 노트 태그(12) 는 providers 정본 `_CATEGORY_TAGS` 와 동일(SSOT 수렴).

    한쪽만 바뀌면 이 테스트가 실패해 drift 를 차단한다. 정본 갱신 시 양쪽 동시 갱신.
    """
    from dartlab.providers.edgar.docs.notesParsers import _CATEGORY_TAGS

    for cat, tags in _CATEGORY_TAGS.items():
        catalogTags = set(edgarTagsFor(cat))
        assert catalogTags == set(tags), (
            f"EDGAR 태그 drift '{cat}': 카탈로그 {sorted(catalogTags)} vs 정본 {sorted(set(tags))}"
        )


def test_parityMatrixCoversAll():
    """parityMatrix 는 전 개념을 분류(합 = 총계)."""
    pm = parityMatrix()
    total = sum(len(v) for v in pm.values())
    assert total == len(getExtractionConcepts())
