"""frame.workbench (Dossier) 조립 view 불변식.

available 은 로컬 데이터 없으면 present 전부 False 지만 조직 구조는 유효(데이터 무관 실행 가능).
실제 추출 스팟체크는 로컬 panel/report 필요라 별도(requires_data).
"""

from __future__ import annotations

from dartlab.core.extractionCatalog import CATEGORIES, getExtractionConcepts
from dartlab.frame.workbench import Dossier, dossier


def test_dossierFactory():
    """dossier() 는 code 바인딩 Dossier 를 연다."""
    d = dossier("005930")
    assert isinstance(d, Dossier)
    assert d.code == "005930" and d.marketNs == "kr"


def test_availableCoversCatalogStructure():
    """available 조직맵은 9 카테고리 전수 + 카탈로그 개념 전수를 담는다(데이터 무관)."""
    amap = dossier("005930").available()
    assert set(amap.keys()) == set(CATEGORIES)
    total = sum(len(v) for v in amap.values())
    assert total == len(getExtractionConcepts())
    # 각 항목은 conceptId/label/present/parity 키.
    sample = amap["financialStatement"][0]
    assert {"conceptId", "label", "present", "parity"} <= set(sample.keys())


def test_forecastHintDelegatesToL2():
    """예측은 워크벤치 소유 X, L2(analysis) 위임 힌트."""
    hint = dossier("005930").forecastHint()
    assert hint["engine"] == "analysis"
    assert "analysis" in hint["call"]


def test_extractUnknownConceptNone():
    """미등록 conceptId 는 None(계약 방어)."""
    assert dossier("005930").extract("존재하지않음") is None


def test_extractSegmentTableIsCrossSection():
    """segmentTable(횡단) 은 단일사 dossier 에서 None(scan 경로 위임)."""
    assert dossier("005930").extract("segment.salesByProduct") is None
