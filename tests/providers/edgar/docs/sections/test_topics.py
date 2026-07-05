"""EDGAR docs topic 택소노미 SSOT 불변식 (data-free, CI 상주).

topics.py 는 흩어져 있던 라벨 dict 를 모은 SSOT. company facade·docs 열거기·인벤토리가 재사용한다.
"""

from __future__ import annotations

from dartlab.providers.edgar.docs.sections.topics import (
    _10K_ITEM_LABELS,
    _10Q_ITEM_LABELS,
    _itemIdToLabel,
    topicChapterLabel,
)


def test_topicChapterLabelResolvesFinance():
    """재무 5표 topic 은 (Financial Statements, label)."""
    assert topicChapterLabel("BS") == ("Financial Statements", "Balance Sheet")
    assert topicChapterLabel("IS")[0] == "Financial Statements"


def test_topicChapterLabelResolves10K():
    """10-K::itemId 는 _10K_ITEM_LABELS 매핑."""
    assert topicChapterLabel("10-K::item1Business") == ("Part I", "Business")
    assert topicChapterLabel("10-K::item7Mdna") == ("Part II", "MD&A")
    assert topicChapterLabel("10-K::item11ExecutiveCompensation")[0] == "Part III"


def test_topicChapterLabelResolves10Q():
    """10-Q::itemId 는 _10Q_ITEM_LABELS 매핑."""
    assert topicChapterLabel("10-Q::partIItem2Mdna") == ("Part I", "MD&A")


def test_topicChapterLabelUnknownFallback():
    """미매핑(20-F 등)은 (formType, itemIdToLabel) fallback."""
    chapter, label = topicChapterLabel("20-F::item5OperatingResults")
    assert chapter == "20-F"
    assert "Operating" in label


def test_itemIdToLabelHumanizes():
    """camelCase itemId 를 사람이 읽는 label 로."""
    assert _itemIdToLabel("item5AOperatingResults") == "Operating Results"


def test_labelDictsCoverStandardItems():
    """10-K 27+ / 10-Q 11 표준 Item 커버(SEC 양식 완전)."""
    assert len(_10K_ITEM_LABELS) >= 27
    assert len(_10Q_ITEM_LABELS) >= 11
    assert "item1Business" in _10K_ITEM_LABELS
    assert "item8FinancialStatements" in _10K_ITEM_LABELS


def test_companyFacadeReusesTopics():
    """company facade 는 topics SSOT 의 _topicChapterLabel 을 재사용(중복 제거 확인)."""
    from dartlab.providers.edgar.company import _topicChapterLabel as companyResolver
    from dartlab.providers.edgar.docs.sections.topics import _topicChapterLabel as ssotResolver

    assert companyResolver is ssotResolver
