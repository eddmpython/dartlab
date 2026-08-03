from __future__ import annotations

from dartlab.ai.runtime.answerQuality import (
    claimCellContractForQuestion,
    classifyEvidenceContract,
    evaluateAnswerQuality,
)


def _refs() -> list[dict]:
    return [
        {
            "id": "table:005930:IS:2026Q1",
            "kind": "tableRef",
            "payload": {"period": "2026Q1", "rows": [{"metric": "sales", "value": 133873444000000}]},
        },
        {
            "id": "value:005930:IS:2026Q1:sales",
            "kind": "valueRef",
            "payload": {"stockCode": "005930", "metric": "sales", "value": 133873444000000, "period": "2026Q1"},
        },
        {
            "id": "date:005930:IS:2026Q1",
            "kind": "dateRef",
            "payload": {"stockCode": "005930", "period": "2026Q1"},
        },
    ]


def testQuantitativeAnswerBindsExactValueAndPeriodOutsideCitationIds():
    answer = (
        "2026년 1분기 매출은 133,873,444,000,000원이다. "
        "table:005930:IS:2026Q1 value:005930:IS:2026Q1:sales date:005930:IS:2026Q1"
    )

    report = evaluateAnswerQuality("2026년 1분기 매출은?", answer, _refs(), completionSucceeded=True, failed=False)

    assert report.passed is True
    assert report.contract == "quantitative"
    assert report.score == 100


def testFiscalYearEvidenceBindsNaturalKoreanYear():
    refs = [
        {
            "id": "table:005930:IS:2024FY",
            "kind": "tableRef",
            "payload": {"rowCount": 1, "rows": [{"item": "매출액", "value": 300870903000000}]},
        },
        {
            "id": "value:005930:IS:2024FY:sales",
            "kind": "valueRef",
            "payload": {"item": "매출액", "period": "2024FY", "value": 300870903000000},
        },
        {
            "id": "date:005930:IS:2024FY",
            "kind": "dateRef",
            "payload": {"period": "2024FY"},
        },
    ]
    answer = (
        "삼성전자의 2024년 연간 매출액은 300,870,903,000,000원이다. "
        "table:005930:IS:2024FY value:005930:IS:2024FY:sales date:005930:IS:2024FY"
    )

    report = evaluateAnswerQuality(
        "삼성전자 2024년 연간 매출액은?", answer, refs, completionSucceeded=True, failed=False, readSkillCalls=1
    )

    assert report.passed is True


def testRoundedKoreanTrillionDisplayBindsExactEvidenceValue():
    refs = _refs()
    refs[1]["payload"]["value"] = 300870903000000
    refs[1]["payload"]["formatted"] = "300.9조원"
    answer = (
        "2026년 1분기 매출은 300.871조원이다. table:005930:IS:2026Q1 value:005930:IS:2026Q1:sales date:005930:IS:2026Q1"
    )

    report = evaluateAnswerQuality("2026년 1분기 매출은?", answer, refs, completionSucceeded=True, failed=False)

    assert report.passed is True


def testWrongRoundedKoreanTrillionDisplayIsRejected():
    refs = _refs()
    refs[1]["payload"]["value"] = 300870903000000
    answer = (
        "2026년 1분기 매출은 301.5조원이다. table:005930:IS:2026Q1 value:005930:IS:2026Q1:sales date:005930:IS:2026Q1"
    )

    report = evaluateAnswerQuality("2026년 1분기 매출은?", answer, refs, completionSucceeded=True, failed=False)

    assert report.passed is False
    assert "value_binding_mismatch" in report.issues


def testQuantitativeAnswerRejectsValueThatDoesNotMatchPayload():
    answer = "2026년 1분기 매출은 1원이다. table:005930:IS:2026Q1 value:005930:IS:2026Q1:sales date:005930:IS:2026Q1"

    report = evaluateAnswerQuality("2026년 1분기 매출은?", answer, _refs(), completionSucceeded=True, failed=False)

    assert report.passed is False
    assert "value_binding_mismatch" in report.issues


def testCitationIdAloneCannotPretendToBindDate():
    answer = (
        "매출은 133,873,444,000,000원이다. table:005930:IS:2026Q1 value:005930:IS:2026Q1:sales date:005930:IS:2026Q1"
    )

    report = evaluateAnswerQuality("매출은?", answer, _refs(), completionSucceeded=True, failed=False)

    assert report.passed is False
    assert "date_binding_mismatch" in report.issues


def testDocumentaryQuestionDoesNotInventAValueRequirement():
    refs = [
        {
            "id": "doc:005930:audit:2024",
            "kind": "docRef",
            "payload": {
                "period": "2024Q4",
                "dataAsOf": "2025-03-18",
                "fields": {"adt_opinion": "적정의견"},
            },
        },
        {
            "id": "date:005930:audit:2024",
            "kind": "dateRef",
            "payload": {"period": "2024Q4", "dataAsOf": "2025-03-18"},
        },
    ]
    answer = "2024년 감사의견은 적정이다. doc:005930:audit:2024 date:005930:audit:2024"

    report = evaluateAnswerQuality("2024년 감사의견은?", answer, refs, completionSucceeded=True, failed=False)

    assert classifyEvidenceContract("2024년 감사의견은?") == "documentary"
    assert report.passed is True
    assert report.contract == "documentary"


def testDocumentaryAuditAnswerMustBindOpinionAndKeyAuditMatter():
    refs = [
        {
            "id": "doc:005930:audit:2024",
            "kind": "docRef",
            "payload": {
                "period": "2024Q4",
                "fields": {
                    "adt_opinion": "적정의견",
                    "core_adt_matter": "건설중인자산의 감가상각개시시점 평가",
                },
            },
        },
        {"id": "date:005930:audit:2024", "kind": "dateRef", "payload": {"period": "2024Q4"}},
    ]
    answer = (
        "2024년 감사의견은 적정이며 핵심감사사항은 건설중인자산의 감가상각개시시점 평가다. "
        "doc:005930:audit:2024 date:005930:audit:2024"
    )

    report = evaluateAnswerQuality(
        "2024년 감사의견과 핵심감사사항은?", answer, refs, completionSucceeded=True, failed=False
    )

    assert report.passed is True


def testDocumentaryAuditAnswerRejectsContradictoryOpinion():
    refs = [
        {
            "id": "doc:005930:audit:2024",
            "kind": "docRef",
            "payload": {"period": "2024Q4", "fields": {"adt_opinion": "적정의견"}},
        },
        {"id": "date:005930:audit:2024", "kind": "dateRef", "payload": {"period": "2024Q4"}},
    ]
    answer = "2024년 감사의견은 부적정이다. doc:005930:audit:2024 date:005930:audit:2024"

    report = evaluateAnswerQuality("2024년 감사의견은?", answer, refs, completionSucceeded=True, failed=False)

    assert report.passed is False
    assert "document_claim_mismatch" in report.issues


def testCitationRejectsCanonicalIdUsedOnlyAsALongerForgedToken():
    answer = (
        "2026년 1분기 매출은 133,873,444,000,000원이다. "
        "table:005930:IS:2026Q1:FORGED "
        "value:005930:IS:2026Q1:sales:FORGED "
        "date:005930:IS:2026Q1:FORGED"
    )

    report = evaluateAnswerQuality("2026년 1분기 매출은?", answer, _refs(), completionSucceeded=True, failed=False)

    assert report.passed is False
    assert report.citedRefIds == ()
    assert "source_ref_missing" in report.issues


def testEmptyEvidencePayloadsCannotPassByIdAlone():
    refs = [
        {"id": "table:empty", "kind": "tableRef", "payload": {}},
        {"id": "value:empty", "kind": "valueRef", "payload": {}},
        {"id": "date:empty", "kind": "dateRef", "payload": {}},
    ]

    report = evaluateAnswerQuality(
        "매출은?",
        "2026년 1분기 매출은 1원이다. table:empty value:empty date:empty",
        refs,
        completionSucceeded=True,
        failed=False,
    )

    assert report.passed is False
    assert "evidence_payload_empty" in report.issues
    assert "value_ref_missing" in report.issues
    assert "date_ref_missing" in report.issues


def testEmptyTableRowsAreNotUsableSourceEvidence():
    refs = _refs()
    refs[0] = {
        "id": "table:005930:IS:2026Q1",
        "kind": "tableRef",
        "payload": {"period": "2026Q1", "rowCount": 0, "rows": []},
    }
    answer = (
        "2026년 1분기 매출은 133,873,444,000,000원이다. "
        "table:005930:IS:2026Q1 value:005930:IS:2026Q1:sales date:005930:IS:2026Q1"
    )

    report = evaluateAnswerQuality("2026년 1분기 매출은?", answer, refs, completionSucceeded=True, failed=False)

    assert report.passed is False
    assert "table_evidence_empty" in report.issues
    assert "source_ref_missing" in report.issues


def testUnavailableDateIsNotUsableEvenWhenDateRefExists():
    refs = _refs()
    refs[2] = {
        "id": "date:005930:IS:unavailable",
        "kind": "dateRef",
        "payload": {"value": "unavailable", "specified": False},
    }
    answer = (
        "2026년 1분기 매출은 133,873,444,000,000원이다. "
        "table:005930:IS:2026Q1 value:005930:IS:2026Q1:sales date:005930:IS:unavailable"
    )

    report = evaluateAnswerQuality("2026년 1분기 매출은?", answer, refs, completionSucceeded=True, failed=False)

    assert report.passed is False
    assert "date_evidence_unavailable" in report.issues
    assert "date_ref_missing" in report.issues


def testExplicitQuestionTargetMustMatchCitedEvidenceTarget():
    refs = [
        {
            "id": "table:000660:IS:2026Q1",
            "kind": "tableRef",
            "payload": {"stockCode": "000660", "rows": [{"metric": "sales", "value": 1}]},
        },
        {
            "id": "value:000660:IS:2026Q1:sales",
            "kind": "valueRef",
            "payload": {"stockCode": "000660", "metric": "sales", "period": "2026Q1", "value": 1},
        },
        {
            "id": "date:000660:IS:2026Q1",
            "kind": "dateRef",
            "payload": {"stockCode": "000660", "period": "2026Q1"},
        },
    ]
    answer = "2026년 1분기 매출은 1원이다. table:000660:IS:2026Q1 value:000660:IS:2026Q1:sales date:000660:IS:2026Q1"

    report = evaluateAnswerQuality(
        "005930의 2026년 1분기 매출은?", answer, refs, completionSucceeded=True, failed=False
    )

    assert report.passed is False
    assert "target_evidence_mismatch" in report.issues


def testRequestedMetricMustMatchCitedValueEvidenceMetric():
    refs = [
        {
            "id": "table:005930:IS:2026Q1",
            "kind": "tableRef",
            "payload": {"stockCode": "005930", "rows": [{"metric": "operatingProfit", "value": 1}]},
        },
        {
            "id": "value:005930:IS:2026Q1:operatingProfit",
            "kind": "valueRef",
            "payload": {"stockCode": "005930", "metric": "operatingProfit", "period": "2026Q1", "value": 1},
        },
        {
            "id": "date:005930:IS:2026Q1",
            "kind": "dateRef",
            "payload": {"stockCode": "005930", "period": "2026Q1"},
        },
    ]
    answer = (
        "2026년 1분기 매출은 1원이다. "
        "table:005930:IS:2026Q1 value:005930:IS:2026Q1:operatingProfit date:005930:IS:2026Q1"
    )

    report = evaluateAnswerQuality(
        "005930의 2026년 1분기 매출은?", answer, refs, completionSucceeded=True, failed=False
    )

    assert report.passed is False
    assert "metric_evidence_mismatch" in report.issues


def testNamedQuestionTargetMustMatchEvidenceTitle():
    refs = _refs()
    refs[0]["title"] = "SK하이닉스 손익계산서 2026Q1"
    answer = (
        "2026년 1분기 매출은 133,873,444,000,000원이다. "
        "table:005930:IS:2026Q1 value:005930:IS:2026Q1:sales date:005930:IS:2026Q1"
    )

    report = evaluateAnswerQuality(
        "삼성전자의 2026년 1분기 매출은?", answer, refs, completionSucceeded=True, failed=False
    )

    assert report.passed is False
    assert "target_evidence_mismatch" in report.issues


def testNamedQuestionTargetAcceptsMatchingEvidenceTitle():
    refs = _refs()
    refs[0]["title"] = "삼성전자 손익계산서 2026Q1"
    answer = (
        "2026년 1분기 매출은 133,873,444,000,000원이다. "
        "table:005930:IS:2026Q1 value:005930:IS:2026Q1:sales date:005930:IS:2026Q1"
    )

    report = evaluateAnswerQuality(
        "삼성전자의 2026년 1분기 매출은?", answer, refs, completionSucceeded=True, failed=False
    )

    assert report.passed is True


def testCoreAuditMatterUsesDocumentaryContract():
    assert classifyEvidenceContract("최신 사업보고서의 핵심감사사항은?") == "documentary"


def _fiveYearMetricRefs(*, complete: bool) -> list[dict]:
    refs: list[dict] = [
        {
            "id": "table:005930:IS:2021-2025",
            "kind": "tableRef",
            "payload": {"stockCode": "005930", "rowCount": 2, "periods": [f"{year}FY" for year in range(2021, 2026)]},
        }
    ]
    for year in range(2021, 2026):
        refs.append(
            {
                "id": f"date:005930:IS:{year}FY",
                "kind": "dateRef",
                "payload": {"stockCode": "005930", "period": f"{year}FY"},
            }
        )
    cells = [(2025, "revenue", 500), (2025, "operating_profit", 50)]
    if complete:
        cells = [
            (year, metric, year * 10 + offset)
            for year in range(2021, 2026)
            for metric, offset in (("revenue", 1), ("operating_profit", 2))
        ]
    for year, metric, value in cells:
        refs.append(
            {
                "id": f"value:005930:IS:{year}FY:{metric}",
                "kind": "valueRef",
                "payload": {
                    "stockCode": "005930",
                    "canonicalMetricId": metric,
                    "period": f"{year}FY",
                    "value": value,
                },
            }
        )
    return refs


def testRecentFiveYearsRequiresEveryMetricPeriodClaimCell():
    refs = _fiveYearMetricRefs(complete=False)
    citations = " ".join(ref["id"] for ref in refs)
    answer = f"2021년, 2022년, 2023년, 2024년, 2025년 매출과 영업이익은 500원과 50원이다. {citations}"

    report = evaluateAnswerQuality(
        "삼성전자 005930 최근 5년 매출과 영업이익 추이",
        answer,
        refs,
        completionSucceeded=True,
        failed=False,
        readSkillCalls=1,
    )

    assert report.passed is False
    assert "claim_cell_coverage_incomplete" in report.issues
    assert report.requiredClaimCells == 10
    assert report.coveredClaimCells == 2


def testClaimCellContractMakesRecentMetricMatrixExplicit():
    contract = claimCellContractForQuestion("삼성전자 005930 최근 5년 매출과 영업이익 추이")

    assert contract == {
        "targets": ["005930"],
        "targetCount": 1,
        "metrics": ["revenue", "operating_profit"],
        "period": {"kind": "recent", "count": 5, "unit": "fiscal_year"},
        "requiredCells": 10,
        "completionRule": "every_target_metric_period_requires_canonical_value_ref",
    }


def testClaimCellContractExpandsExplicitPeerComparisonMatrix():
    contract = claimCellContractForQuestion(
        "삼성전자와 SK하이닉스의 2024년 매출과 영업이익 비교",
        comparison={"minTargets": 2},
    )

    assert contract["targetCount"] == 2
    assert contract["targets"] == ["sk하이닉스", "삼성전자"]
    assert contract["period"] == {"kind": "explicit", "periods": ["2024"]}
    assert contract["requiredCells"] == 4


def testRecentFiveYearsPassesWithCompleteMetricPeriodClaimCells():
    refs = _fiveYearMetricRefs(complete=True)
    values = " ".join(str(ref["payload"]["value"]) for ref in refs if ref["kind"] == "valueRef")
    citations = " ".join(ref["id"] for ref in refs)
    answer = f"2021년, 2022년, 2023년, 2024년, 2025년의 매출과 영업이익은 각각 {values}원이다. {citations}"

    report = evaluateAnswerQuality(
        "삼성전자 005930 최근 5년 매출과 영업이익 추이",
        answer,
        refs,
        completionSucceeded=True,
        failed=False,
        readSkillCalls=1,
    )

    assert report.passed is True
    assert report.requiredClaimCells == 10
    assert report.coveredClaimCells == 10


def testRunPythonLocalValuesCannotBecomeGroundingWithoutCanonicalLineage():
    refs = [
        {
            "id": "table:local:python",
            "kind": "tableRef",
            "source": "execution:local:1",
            "payload": {"rows": [{"metric": "revenue", "value": 999}]},
        },
        {
            "id": "value:local:revenue",
            "kind": "valueRef",
            "source": "execution:local:1",
            "payload": {"canonicalMetricId": "revenue", "period": "2025FY", "value": 999},
        },
        {
            "id": "date:local:2025FY",
            "kind": "dateRef",
            "source": "execution:local:1",
            "payload": {"period": "2025FY"},
        },
    ]
    answer = "2025년 매출은 999원이다. table:local:python value:local:revenue date:local:2025FY"

    report = evaluateAnswerQuality(
        "2025년 매출은?", answer, refs, completionSucceeded=True, failed=False, readSkillCalls=1
    )

    assert report.passed is False
    assert "derived_evidence_lineage_missing" in report.issues


def testLensAsOfDateIsConcreteAndBindsToAnswer():
    refs = [
        {
            "id": "table:005930:analysis",
            "kind": "tableRef",
            "payload": {"stockCode": "005930", "rows": [{"axis": "quality", "value": "양호"}]},
        },
        {
            "id": "value:005930:analysis:quality",
            "kind": "valueRef",
            "payload": {"stockCode": "005930", "metric": "quality", "value": "양호"},
        },
        {
            "id": "date:005930:analysis:boundary",
            "kind": "dateRef",
            "payload": {"stockCode": "005930", "asOf": "2026-07-18", "knowledgeBoundary": "2026-07-18"},
        },
    ]
    answer = (
        "2026-07-18 기준 품질 판단은 양호다. "
        "table:005930:analysis value:005930:analysis:quality date:005930:analysis:boundary"
    )

    report = evaluateAnswerQuality(
        "005930의 투자 품질은?", answer, refs, completionSucceeded=True, failed=False, readSkillCalls=1
    )

    assert "date_evidence_unavailable" not in report.issues
    assert "date_binding_mismatch" not in report.issues


def testExplicitStockCodePreventsKoreanSentenceFromBecomingTargetLabel():
    refs = _refs()
    answer = (
        "2026년 1분기 매출은 133,873,444,000,000원이다. "
        "table:005930:IS:2026Q1 value:005930:IS:2026Q1:sales date:005930:IS:2026Q1"
    )

    report = evaluateAnswerQuality(
        "삼성전자 005930 지금 투자할 만한지 핵심 논지와 반대논지를 같이 분석해줘",
        answer,
        refs,
        completionSucceeded=True,
        failed=False,
        readSkillCalls=1,
    )

    assert "target_evidence_mismatch" not in report.issues


def testCanonicalCompanyNamePreventsVerbPhraseFromBecomingTargetLabel():
    refs = _refs()
    refs[0]["title"] = "삼성전자 손익계산서 2026Q1"
    answer = (
        "2026년 1분기 매출은 133,873,444,000,000원이다. "
        "table:005930:IS:2026Q1 value:005930:IS:2026Q1:sales date:005930:IS:2026Q1"
    )

    report = evaluateAnswerQuality(
        "삼성전자 지금 투자할 만한지 핵심 논지와 반대논지를 같이 분석해줘",
        answer,
        refs,
        completionSucceeded=True,
        failed=False,
        readSkillCalls=1,
    )

    assert "target_evidence_mismatch" not in report.issues


def testQualitativeLensValueAllowsPunctuationAndLimitedWordingChange():
    refs = [
        {
            "id": "table:005930:macro",
            "kind": "tableRef",
            "payload": {"stockCode": "005930", "rows": [{"axis": "macro", "value": "혼재"}]},
        },
        {
            "id": "value:005930:macro:conclusion",
            "kind": "valueRef",
            "payload": {
                "stockCode": "005930",
                "label": "거시 전파 경로 혼재",
                "value": "거시 전파 경로 혼재",
            },
        },
        {
            "id": "date:005930:macro:boundary",
            "kind": "dateRef",
            "payload": {"stockCode": "005930", "asOf": "2026-08-03"},
        },
    ]
    answer = (
        "2026-08-03 기준 거시 전파 평가는 혼재다. "
        "table:005930:macro value:005930:macro:conclusion date:005930:macro:boundary"
    )

    report = evaluateAnswerQuality(
        "005930 투자 판단", answer, refs, completionSucceeded=True, failed=False, readSkillCalls=1
    )

    assert "value_binding_mismatch" not in report.issues


def testScenarioRangeBindsCanonicalMatrixWithoutRepeatingMiddleValue():
    rows = [
        {"scenario": "bear", "perShareValue": 18_835.3605},
        {"scenario": "base", "perShareValue": 20_441.8777},
        {"scenario": "bull", "perShareValue": 22_613.6481},
    ]
    refs = [
        {
            "id": "dcf:005930:matrix",
            "kind": "tableRef",
            "payload": {
                "stockCode": "005930",
                "period": "2026Q1",
                "unit": "KRW",
                "rowCount": 3,
                "rows": rows,
            },
        },
        *[
            {
                "id": f"dcf:005930:{row['scenario']}",
                "kind": "valueRef",
                "payload": {
                    "stockCode": "005930",
                    "period": "2026Q1",
                    "axis": "valuation",
                    "scenario": row["scenario"],
                    "unit": "KRW",
                    "value": row["perShareValue"],
                },
            }
            for row in rows
        ],
        {
            "id": "dcf:005930:date:2026Q1",
            "kind": "dateRef",
            "payload": {"stockCode": "005930", "period": "2026Q1"},
        },
    ]
    answer = (
        "2026년 1분기 DCF 범위는 18,835~22,614원이다. "
        "dcf:005930:matrix dcf:005930:bear dcf:005930:base dcf:005930:bull dcf:005930:date:2026Q1"
    )

    report = evaluateAnswerQuality(
        "005930 투자 판단", answer, refs, completionSucceeded=True, failed=False, readSkillCalls=1
    )

    assert report.passed is True
