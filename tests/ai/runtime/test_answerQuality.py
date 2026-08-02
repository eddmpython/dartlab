from __future__ import annotations

from dartlab.ai.runtime.answerQuality import classifyEvidenceContract, evaluateAnswerQuality


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
