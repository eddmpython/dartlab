"""Capability 발견과 EngineCall 실행 권한의 분리 계약."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def testCanonicalCompanyExecutionRefsAreFormalThirteen() -> None:
    from dartlab.reference.capability.execution import CANONICAL_COMPANY_CAPABILITY_REFS

    assert CANONICAL_COMPANY_CAPABILITY_REFS == {
        "Company.panel",
        "Company.select",
        "Company.trace",
        "Company.filings",
        "Company.analysis",
        "Company.credit",
        "Company.gather",
        "Company.quant",
        "Company.macro",
        "Company.story",
        "Company.reportModel",
        "Company.industry",
        "Company.simulate",
    }


@pytest.mark.parametrize(
    "apiRef",
    [
        "Company.panel",
        "Company.story",
        "dataHub.catalog",
        "dataHub.query",
        "scan.growth",
        "analysis.가치평가",
        "gather.price",
        "compare",
        "simulate",
        "search",
    ],
)
def testCanonicalDataAndAnalysisRefsAreEngineCallable(apiRef: str) -> None:
    from dartlab.reference.capability.execution import isEngineCallableRef

    assert isEngineCallableRef(apiRef) is True


@pytest.mark.parametrize(
    "apiRef",
    [
        "Company.diff",
        "Company.audit",
        "Company.storyTree",
        "Company.canHandle",
        "ask",
        "Company",
        "Story",
        "collect",
        "setup",
        "aiContract.comparison.same_axis",
    ],
)
def testReferenceOnlyAndInternalRefsAreNotEngineCallable(apiRef: str) -> None:
    from dartlab.reference.capability.execution import isEngineCallableRef

    assert isEngineCallableRef(apiRef) is False


def testBuiltCatalogMarksEveryEntryWithExecutionBoundary() -> None:
    from dartlab.reference.capability import buildCapabilities

    capabilities = buildCapabilities()

    assert capabilities
    assert all(isinstance(entry.get("engineCallable"), bool) for entry in capabilities.values())
    assert all(entry.get("executionGuide") for entry in capabilities.values())
    assert capabilities["Company.panel"]["engineCallable"] is True
    assert capabilities["Company.diff"]["engineCallable"] is False
    assert capabilities["scan.growth"]["engineCallable"] is True
    assert capabilities["aiContract.comparison.same_axis"]["engineCallable"] is False


def testReadCapabilityCarriesExecutionBoundaryInRefAndRows(monkeypatch: pytest.MonkeyPatch) -> None:
    from dartlab.ai.tools.readCapability import readCapability
    from dartlab.reference.capability import search as capabilitySearch

    entry = {
        "summary": "기간 차이",
        "engineCallable": False,
        "executionGuide": "공개 참조 전용입니다.",
    }
    monkeypatch.setattr(capabilitySearch, "searchCapabilities", lambda *args, **kwargs: [("Company.diff", entry, 9.0)])

    result = readCapability("Company.diff")

    assert result.refs[0].payload["engineCallable"] is False
    assert result.data["capabilities"][0]["engineCallable"] is False
    assert result.data["capabilities"][0]["executionGuide"] == "공개 참조 전용입니다."


def testReadSkillInlineCarriesExecutionBoundary() -> None:
    from dartlab.ai.tools.readSkill import _inlineCapabilities

    details = _inlineCapabilities(["Company.panel", "Company.diff"], isTopRank=True)

    assert details["Company.panel"]["engineCallable"] is True
    assert details["Company.diff"]["engineCallable"] is False
    assert "EngineCall" in str(details["Company.panel"]["executionGuide"])
    assert "참조 전용" in str(details["Company.diff"]["executionGuide"])


def testCanonicalReplacementRefsPreferExecutableDeclaredPaths() -> None:
    from dartlab.reference.capability.execution import canonicalReplacementRefs

    assert canonicalReplacementRefs("Company.panel") == ("Company.panel",)
    assert canonicalReplacementRefs("Company.disclosure") == ("Company.filings",)
    assert canonicalReplacementRefs(
        "Company.legacy",
        {"capabilityRefs": ["Company.analysis", "Company.diff", "Company.analysis"]},
    ) == ("Company.analysis",)
    assert canonicalReplacementRefs("Company.unknown") == ("Company.panel",)
    assert canonicalReplacementRefs("Unknown.reference") == ()


def testEngineCallContractKeepsCanonicalTargetAndDeclaredOptions() -> None:
    from dartlab.reference.capability.execution import engineCallContract

    company = engineCallContract("Company.panel")
    assert company["tool"] == "EngineCall"
    assert company["argsContract"]["stockCode"]["required"] is True

    axis = engineCallContract(
        "analysis.가치평가",
        {
            "declared": {
                "targetRequired": True,
                "targetType": "stockCode",
                "options": ["period", "method"],
                "returnType": "dict",
            },
            "example": "dartlab.analysis('가치평가', stockCode='005930')",
        },
    )
    assert axis["argsContract"]["target"] == {"required": True, "type": "stockCode"}
    assert axis["optionNames"] == ["period", "method"]
    assert axis["returnType"] == "dict"
    assert "가치평가" in axis["nativeExample"]
    assert engineCallContract("Company.diff") == {}


def testLoadAnalysisGraphCompilesLiveCapabilityContracts() -> None:
    from dartlab.reference.capability.builder import loadAnalysisGraph

    graph = loadAnalysisGraph()

    assert graph["graphVersion"] == 2
    assert len(graph["sourceHash"]) == 16
    assert "company.statement_fact" in graph["contracts"]
    assert graph["routes"]
    assert graph["processMaps"]
