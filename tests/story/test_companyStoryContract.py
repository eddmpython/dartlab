from __future__ import annotations

import pytest

from dartlab.providers.dart.company import Company as DartCompany
from dartlab.providers.edgar.company import Company as EdgarCompany

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("companyClass", [DartCompany, EdgarCompany])
def test_company_story_accepts_official_report_type_alias(monkeypatch, companyClass) -> None:
    from dartlab.story import registry

    captured = {}

    def fakeBuildStory(company, **kwargs):
        captured.update(kwargs)
        return kwargs

    monkeypatch.setattr(registry, "buildStory", fakeBuildStory)

    result = companyClass._storyImpl(object(), reportType="credit")

    assert result["type"] == "credit"
    assert captured["type"] == "credit"


@pytest.mark.parametrize("companyClass", [DartCompany, EdgarCompany])
def test_company_story_accepts_matching_type_and_report_type(monkeypatch, companyClass) -> None:
    from dartlab.story import registry

    monkeypatch.setattr(registry, "buildStory", lambda company, **kwargs: kwargs)

    result = companyClass._storyImpl(object(), type="audit", reportType="audit")

    assert result["type"] == "audit"


@pytest.mark.parametrize("companyClass", [DartCompany, EdgarCompany])
def test_company_story_rejects_conflicting_type_names(monkeypatch, companyClass) -> None:
    from dartlab.story import registry

    called = False

    def fakeBuildStory(company, **kwargs):
        nonlocal called
        called = True
        return kwargs

    monkeypatch.setattr(registry, "buildStory", fakeBuildStory)

    with pytest.raises(ValueError, match="같은 값"):
        companyClass._storyImpl(object(), type="credit", reportType="audit")

    assert called is False
