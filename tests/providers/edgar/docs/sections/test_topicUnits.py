"""EDGAR docs 경량 열거기 topicUnits 불변식.

data-free 계약(빈/미존재 ticker) + 로컬 데이터 있으면 round-trip 스팟체크. topicUnits 는 topic 컬럼만
읽어(본문 무접촉) OOM 안전. handle 은 `sections()` 가 emit 하는 topic 과 동일해야 round-trip 성립.
"""

from __future__ import annotations

import pytest

from dartlab.providers.edgar.docs.sections.sectionsStorage import hasSectionsArtifact
from dartlab.providers.edgar.docs.sections.topicUnits import topicUnits

_FIXTURE = "AAPL"
_HAS_DATA = hasSectionsArtifact(_FIXTURE)


def test_missingTickerEmpty():
    """미존재 ticker 는 빈 리스트(예외 없음)."""
    assert topicUnits("ZZZNONEXISTENT000") == []


@pytest.mark.skipif(not _HAS_DATA, reason="로컬 edgar sections 데이터 없음")
def test_enumeratesFormNamespacedTopics():
    """열거 handle 은 form-namespaced topic(form::itemId)."""
    units = topicUnits(_FIXTURE)
    assert units, "AAPL 은 Item 을 열거해야"
    for u in units:
        assert "::" in u["topic"]
        assert u["topic"].split("::", 1)[0] in ("10-K", "10-Q", "20-F", "40-F")
        assert u["itemId"] and u["title"] and u["chapter"]


@pytest.mark.skipif(not _HAS_DATA, reason="로컬 edgar sections 데이터 없음")
def test_topicUniqueness():
    """topic handle 은 filer 내 유일(collision 0)."""
    topics = [u["topic"] for u in topicUnits(_FIXTURE)]
    assert len(topics) == len(set(topics)), "topic collision"


@pytest.mark.skipif(not _HAS_DATA, reason="로컬 edgar sections 데이터 없음")
def test_roundTripAgainstSections():
    """모든 열거 topic 은 sections() 에 실재(get round-trip 보장 by construction)."""
    from dartlab.providers.edgar.docs.sections.pipeline import sections

    sec = sections(_FIXTURE)
    assert sec is not None
    present = set(sec.get_column("topic").unique().to_list())
    enumerated = {u["topic"] for u in topicUnits(_FIXTURE)}
    assert enumerated <= present, f"열거 topic 이 sections 에 부재: {enumerated - present}"
