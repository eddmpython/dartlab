"""Company capability catalog와 provider/legacy 구현 표면의 경계."""

from __future__ import annotations

import inspect

import pytest

pytestmark = pytest.mark.unit

_ROUTER_MEMBERS = {"canHandle", "priority", "listing", "search", "resolve", "codeName", "status"}
_COMPATIBILITY_STORY_MEMBERS = {"causalWeights", "valuationImpact", "storyTree", "narrativeDiff"}


def testCompanyCatalogExcludesProviderRouterAndCompatibilityMethods() -> None:
    from dartlab.reference.capability import buildCapabilities

    capabilities = buildCapabilities()

    assert not {f"Company.{name}" for name in _ROUTER_MEMBERS} & set(capabilities)
    assert not {f"Company.{name}" for name in _COMPATIBILITY_STORY_MEMBERS} & set(capabilities)
    assert {"Company.story", "Company.reportModel", "Company.simulate"} <= set(capabilities)


def testCompanyCatalogNeverReflectsStaticOrClassMethods() -> None:
    from dartlab.providers.dart.company import Company
    from dartlab.reference.capability.builder import _companyMemberDoc

    reflected = {
        name for name in dir(Company) if not name.startswith("_") and _companyMemberDoc(Company, name) is not None
    }
    staticOrClass = {
        name
        for name in dir(Company)
        if isinstance(inspect.getattr_static(Company, name, None), (staticmethod, classmethod))
    }

    assert reflected.isdisjoint(staticOrClass)


def testCompatibilityStoryMethodsRemainPythonCallableForKrAndUs() -> None:
    from dartlab.providers.dart.company import Company as DartCompany
    from dartlab.providers.edgar.company import Company as EdgarCompany

    for companyClass in (DartCompany, EdgarCompany):
        for name in _COMPATIBILITY_STORY_MEMBERS:
            assert callable(getattr(companyClass, name))


def testEngineCallRejectsCompatibilityStoryMethodBeforeCompanyResolution() -> None:
    from dartlab.ai.tools.engineCall import engineCall

    result = engineCall({"apiRef": "Company.storyTree", "args": {"stockCode": "005930"}})

    assert result.ok is False
    assert result.error == "unknown_api_ref"
