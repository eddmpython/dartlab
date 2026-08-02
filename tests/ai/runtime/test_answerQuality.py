from __future__ import annotations

from dartlab.ai.runtime.answerQuality import classifyEvidenceContract, evaluateAnswerQuality


def _refs() -> list[dict]:
    return [
        {"id": "table:005930:IS:2026Q1", "kind": "tableRef", "payload": {"period": "2026Q1"}},
        {
            "id": "value:005930:IS:2026Q1:sales",
            "kind": "valueRef",
            "payload": {"value": 133873444000000, "period": "2026Q1"},
        },
        {"id": "date:005930:IS:2026Q1", "kind": "dateRef", "payload": {"period": "2026Q1"}},
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
        {"id": "doc:005930:audit:2024", "kind": "docRef", "payload": {"dataAsOf": "2025-03-18"}},
        {"id": "date:005930:audit:2024", "kind": "dateRef", "payload": {"dataAsOf": "2025-03-18"}},
    ]
    answer = "2025년 3월 18일 공시 기준 감사의견은 적정이다. doc:005930:audit:2024 date:005930:audit:2024"

    report = evaluateAnswerQuality("2024년 감사의견은?", answer, refs, completionSucceeded=True, failed=False)

    assert classifyEvidenceContract("2024년 감사의견은?") == "documentary"
    assert report.passed is True
    assert report.contract == "documentary"
