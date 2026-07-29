"""DART Company routing과 L0 DataEntry metadata 경계 회귀."""

from __future__ import annotations

import pytest

from dartlab.core.registry import DataEntry, registerEntry, resolveAlias, unregisterEntry
from dartlab.providers.dart.company import _getModuleEntries, _resolveTopic
from dartlab.providers.dart.topicStandard import resolveTopicAlias

pytestmark = [pytest.mark.unit]


@pytest.mark.parametrize(
    ("alias", "canonical"),
    [
        ("board", "boardOfDirectors"),
        ("cashflow", "CF"),
        ("tangible", "tangibleAsset"),
        ("relatedParty", "relatedPartyTx"),
    ],
)
def testCompanyAliasesBelongToDartTopicOwner(alias: str, canonical: str) -> None:
    """Company alias는 DART owner에서 해소되고 L0 entry alias와 섞이지 않는다."""
    assert resolveTopicAlias(alias) == canonical
    assert _resolveTopic(alias) == canonical
    assert resolveAlias(alias) == alias


def testCompanyModuleProjectionFiltersGenericRegistry() -> None:
    """Company는 L0 registry 중 실행 가능한 report/disclosure 엔트리만 소비한다."""
    reportEntry = DataEntry(
        name="__company_report_plugin",
        label="report",
        category="report",
        dataType="custom",
        description="report plugin",
        modulePath="plugin.report",
        funcName="loadReport",
    )
    analysisEntry = DataEntry(
        name="__company_analysis_plugin",
        label="analysis",
        category="analysis",
        dataType="custom",
        description="analysis plugin",
        modulePath="plugin.analysis",
        funcName="analyze",
    )
    try:
        registerEntry(reportEntry, source="test:company-report")
        registerEntry(analysisEntry, source="test:company-analysis")
        projected = {entry.name for entry in _getModuleEntries()}

        assert reportEntry.name in projected
        assert analysisEntry.name not in projected
    finally:
        unregisterEntry(reportEntry.name)
        unregisterEntry(analysisEntry.name)
