"""extractionCatalog 불변식 + EDGAR 태그 SSOT 드리프트 가드.

카탈로그는 순수 데이터라 로컬 데이터 없이 항상 실행 가능(CI 상주 게이트). census(실제 커버리지)는
로컬 parquet 필요라 별도 CLI(tests/audit/extractionCoverageCensus.py).
"""

from __future__ import annotations

import dataclasses
import hashlib
import json

import pytest

from dartlab.core.extractionCatalog import (
    AXIS_TYPES,
    CATEGORIES,
    VALUE_TYPES,
    DartSource,
    EdgarSource,
    ExtractionConcept,
    HonestNull,
    catalogSummary,
    conceptsByCategory,
    edgarTagsFor,
    getConcept,
    getExtractionConcepts,
    parityMatrix,
    resolveNoteKey,
)
from dartlab.core.extractionCatalog.catalog import _buildIndex, _buildNoteAliases
from dartlab.core.extractionCatalog.models import DartSource as ModelDartSource


def test_conceptIdUnique():
    """conceptId 는 전역 유일."""
    ids = [c.conceptId for c in getExtractionConcepts()]
    assert len(ids) == len(set(ids)), "중복 conceptId 존재"


def test_manifestOrderContentAndPublicTypeIdentityRemainStable():
    """물리 분할이 88개 manifest 값·순서와 public type identity를 바꾸지 않는다."""
    concepts = getExtractionConcepts()
    payload = json.dumps(
        [dataclasses.asdict(concept) for concept in concepts],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()

    assert hashlib.sha256(payload).hexdigest() == ("3f4e8d14b2be6b3bd7b6c3158d28b281857a2c36e6f1ac674c1579fd1c824d09")
    assert DartSource is ModelDartSource
    assert all(getConcept(concept.conceptId) is concept for concept in concepts)


def test_manifestAssemblyRejectsSilentLastWrite():
    """중복 conceptId와 서로 다른 note alias canonical key를 fail-fast한다."""
    concept = getExtractionConcepts()[0]
    with pytest.raises(ValueError, match="중복 extraction conceptId"):
        _buildIndex((concept, concept))

    first = ExtractionConcept(
        "note.first",
        "note",
        "충돌라벨",
        DartSource("note", "NT_FIRST"),
        HonestNull("EDGAR 구조 부재"),
        registered=True,
    )
    second = ExtractionConcept(
        "note.second",
        "note",
        "충돌라벨",
        DartSource("note", "NT_FIRST"),
        HonestNull("EDGAR 구조 부재"),
        registered=True,
    )
    with pytest.raises(ValueError, match="note alias 충돌"):
        _buildNoteAliases((first, second))


def test_modelRejectsInvalidManifestRows():
    """빈 HonestNull과 미등록 source/category를 wheel import 전에 거부한다."""
    with pytest.raises(ValueError, match="reason"):
        HonestNull(" ")
    with pytest.raises(ValueError, match="DART surface"):
        DartSource("unknown", "key")
    with pytest.raises(ValueError, match="registered"):
        ExtractionConcept(
            "not.note",
            "capital",
            "잘못된 등록",
            DartSource("report", "capital"),
            HonestNull("EDGAR 구조 부재"),
            registered=True,
        )


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
    """DART-anchored narrative 개념은 narrativeAnchor(chapter, section) 를 가진다.

    US-only narrative(edgarOnly Item, dart=HonestNull)는 DART panel 앵커가 없으므로 예외.
    """
    for c in getExtractionConcepts(category="narrative"):
        if isinstance(c.dart, DartSource):
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
        assert isinstance(c.dart, DartSource)
        key = c.dart.key
        assert resolveNoteKey(c.conceptId) == key, f"{c.conceptId} conceptId 해소 실패"
        assert resolveNoteKey(c.conceptId.removeprefix("note.")) == key, f"{c.conceptId} bareName 해소 실패"
        assert resolveNoteKey(c.label) == key, f"{c.conceptId} label({c.label}) 해소 실패"

    unregistered = [c for c in getExtractionConcepts(category="note") if not c.registered]
    for c in unregistered:
        assert resolveNoteKey(c.conceptId) is None
        assert resolveNoteKey(c.conceptId.removeprefix("note.")) is None
        assert resolveNoteKey(c.label) is None


def test_resolveNoteKeyUnknownReturnsNone():
    """미등록 이름은 None(폴백 무발동, 기존 경로 보존)."""
    assert resolveNoteKey("존재하지않는노트") is None
    assert resolveNoteKey("NT_D826380") is None  # canonicalKey 자체는 별칭 아님(무한재귀 방지)


def test_toDictRoundtrip():
    """toDict 는 parity 포함 직렬화 dict 를 낸다."""
    concept = getConcept("note.tax")
    assert concept is not None
    d = concept.toDict()
    assert d["conceptId"] == "note.tax"
    assert d["parity"] in ("both", "dartOnly", "edgarOnly", "none")
    assert d["edgar"] is not None
    assert d["edgar"]["surface"] == "xbrlTag"


def test_toDictSerializesHonestNullOnEitherProvider():
    """구조적 부재는 provider 어느 쪽이든 사유를 잃거나 예외를 내지 않는다."""
    for concept in getExtractionConcepts():
        payload = concept.toDict()
        if isinstance(concept.dart, HonestNull):
            assert payload["dart"] == {
                "surface": "honestNull",
                "reason": concept.dart.reason,
            }
        if isinstance(concept.edgar, HonestNull):
            assert payload["edgar"] == {
                "surface": "honestNull",
                "reason": concept.edgar.reason,
            }


def test_summaryAndParityConsistent():
    """catalogSummary 총계 = 카테고리 합 = parity 합."""
    s = catalogSummary()
    assert s["total"] == sum(s["byCategory"].values())
    assert s["total"] == sum(s["parity"].values())
    assert s["total"] == len(getExtractionConcepts())
    assert len(s["honestNull"]) == 28
    assert len(s["dartHonestNull"]) == 8
    assert len(s["edgarHonestNull"]) == 20


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
    assert {key: len(value) for key, value in pm.items()} == {
        "both": 60,
        "dartOnly": 20,
        "edgarOnly": 8,
        "none": 0,
    }


def test_edgarItemTaxonomyDriftGuard():
    """카탈로그 EDGAR Item category map 은 providers 정본 topic 택소노미와 동일 키(SSOT 수렴).

    한쪽만 바뀌면 실패해 drift 차단. 정본(providers.edgar.docs.sections.topics) 갱신 시 양쪽 동시 갱신.
    """
    from dartlab.core.extractionCatalog import edgarItemCategory
    from dartlab.providers.edgar.docs.sections import topics as tp

    ssot = set(tp._10K_ITEM_LABELS) | set(tp._10Q_ITEM_LABELS)
    cat = set(edgarItemCategory())
    assert cat == ssot, f"EDGAR Item 택소노미 drift: ssot-cat={ssot - cat}, cat-ssot={cat - ssot}"


def test_edgarItemCategoryValid():
    """모든 EDGAR Item category 는 CATEGORIES 어휘."""
    from dartlab.core.extractionCatalog import edgarItemCategory

    for topicId, category in edgarItemCategory().items():
        assert category in CATEGORIES, f"{topicId}: 미등록 category {category}"


def test_edgarItemReverseIndexValid():
    """edgarItemToConcept 의 모든 대표 conceptId 는 실재 개념."""
    from dartlab.core.extractionCatalog import edgarItemToConcept

    for topicId, conceptId in edgarItemToConcept().items():
        assert getConcept(conceptId) is not None, f"{topicId} -> 미실재 conceptId {conceptId}"


def test_edgarOnlyItemsShape():
    """US-only Item(8) 은 dart=HonestNull + edgar item surface(EDGAR<->DART 비대칭 정직 기록)."""
    edgarOnly = [c for c in getExtractionConcepts() if c.conceptId.startswith("edgar.")]
    assert len(edgarOnly) == 8, f"edgarOnly Item 8 기대, 실제 {len(edgarOnly)}"
    for c in edgarOnly:
        assert isinstance(c.dart, HonestNull) and c.dart.reason.strip(), f"{c.conceptId}: dart HonestNull 사유 필요"
        assert isinstance(c.edgar, EdgarSource) and c.edgar.surface == "item", f"{c.conceptId}: edgar item surface 필요"


def test_edgarItemCoverageMeasures():
    """edgarItemCoverage 는 실재 topicId 대비 카탈로그 커버리지를 측정(생존편향 차단, US side)."""
    from dartlab.core.extractionCatalog import edgarItemCoverage

    cov = edgarItemCoverage(["item1Business", "item7Mdna", "item999NonStandard"])
    assert cov["present"] == 3
    assert cov["catalogued"] == 2
    assert cov["uncatalogued"] and cov["uncatalogued"][0][0] == "item999NonStandard"


def test_conceptForEdgarItemResolves():
    """conceptForEdgarItem 은 topicId 를 대표 개념으로 해소(inventory Item enrich)."""
    from dartlab.core.extractionCatalog import conceptForEdgarItem

    mdna = conceptForEdgarItem("item7Mdna")
    cybersecurity = conceptForEdgarItem("item1CCybersecurity")
    assert mdna is not None and mdna.conceptId == "narrative.mdna"
    assert cybersecurity is not None and cybersecurity.conceptId == "edgar.cybersecurity"
    assert conceptForEdgarItem("item999NonStandard") is None
