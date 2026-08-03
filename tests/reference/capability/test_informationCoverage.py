from __future__ import annotations

from dartlab.reference.capability import loadCapabilities
from dartlab.reference.capability.analysisGraph import coveragePacketForQuestion


def testStatementFactCoverageSelectsCompanyPanelAndRequiredEvidence() -> None:
    packet = coveragePacketForQuestion("삼성전자 2024년 연간 매출액은?")

    assert packet["candidateCapabilityRefs"][0] == "Company.panel"
    assert set(("target", "metric", "period", "value")).issubset(packet["requiredEvidence"])


def testCompositeCoverageKeepsValuationIndustryAndMacroFacets() -> None:
    packet = coveragePacketForQuestion("삼성전자 산업 경쟁력과 금리 환율 영향을 반영해 가치평가해줘")
    candidates = set(packet["candidateCapabilityRefs"])

    assert {"analysis.가치평가", "industry", "macro"}.issubset(candidates)
    assert "comparison.same_axis" not in packet["contractIds"]


def testScreeningCoveragePrioritizesScan() -> None:
    packet = coveragePacketForQuestion("ROE가 높고 부채비율이 낮은 종목을 스크리닝해줘")

    assert packet["candidateCapabilityRefs"][0] == "scan"


def testDocumentCoverageRequiresExactDocumentAndCanonicalReplacement() -> None:
    packet = coveragePacketForQuestion("삼성전자 2024년 핵심감사사항과 관련 금액은?")

    assert "docRef" in packet["requiredEvidence"]
    assert {"Company.filings", "Company.panel"}.issubset(packet["candidateCapabilityRefs"])
    audit = next(row for row in packet["referenceOnlyMatches"] if row["apiRef"] == "Company.audit")
    assert "Company.panel" in audit["replacementRefs"]


def testCoveragePacketIsBoundedAndOnlySuggestsExecutableCapabilities() -> None:
    packet = coveragePacketForQuestion("매출 산업 금리 환율 신용 주가 시나리오 비교 스크리닝 가치평가", limit=12)
    catalog = loadCapabilities()

    assert len(packet["candidateCapabilityRefs"]) <= 12
    assert len(packet.get("referenceOnlyMatches") or []) <= 5
    assert all(catalog[ref]["engineCallable"] for ref in packet["candidateCapabilityRefs"])
    assert packet["catalog"]["total"] == len(catalog)


def testEveryExecutableCapabilityCarriesStructuredEngineCallContract() -> None:
    catalog = loadCapabilities()
    executable = {apiRef: entry for apiRef, entry in catalog.items() if entry["engineCallable"]}

    assert executable
    assert all(entry.get("execution", {}).get("tool") == "EngineCall" for entry in executable.values())
    assert all(entry.get("execution", {}).get("apiRef") == apiRef for apiRef, entry in executable.items())
    assert sum(bool(entry.get("example")) for entry in executable.values()) >= 150


def testBroadInvestmentIntentRoutesToNineDimensionDecisionMemo() -> None:
    packet = coveragePacketForQuestion("삼성전자 005930 지금 투자할 만한지 종합 분석해줘")

    assert packet["contractIds"][0] == "investment.decision_memo"
    assert packet["candidateCapabilityRefs"][0] == "Company.reportModel"
    assert packet["questionTypes"] == ["investment_decision"]
    assert packet["acceptanceCriteria"]["minUsableDimensions"] == 7
    assert len(packet["acceptanceCriteria"]["requiredDimensions"]) == 9
    assert packet["failurePolicy"]["blockedHardCoreMeans"] == "insufficient"
