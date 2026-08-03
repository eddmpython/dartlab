"""설치형 런타임 답변 품질 게이트의 안정 공개 표면."""

from __future__ import annotations

from typing import Any

from . import answerQualityPipeline as _pipeline

EvidenceContract = _pipeline.EvidenceContract
AnswerQualityReport = _pipeline.AnswerQualityReport
AnswerQualityReport.__module__ = __name__


def classifyEvidenceContract(question: str) -> EvidenceContract:
    """질문의 근거 계약을 분류한다."""
    return _pipeline.classifyEvidenceContract(question)


def evaluateAnswerQuality(
    question: str,
    answer: str,
    refs: list[dict[str, Any]],
    *,
    completionSucceeded: bool,
    failed: bool,
    readSkillCalls: int | None = None,
) -> AnswerQualityReport:
    """종료 상태와 근거 결합을 검사한다."""
    return _pipeline.evaluateAnswerQuality(
        question,
        answer,
        refs,
        completionSucceeded=completionSucceeded,
        failed=failed,
        readSkillCalls=readSkillCalls,
    )


def claimCellContractForQuestion(
    question: str,
    *,
    comparison: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """질문의 대상 x 지표 x 기간 완결 조건을 반환한다."""
    return _pipeline.claimCellContractForQuestion(question, comparison=comparison)


__all__ = [
    "AnswerQualityReport",
    "EvidenceContract",
    "claimCellContractForQuestion",
    "classifyEvidenceContract",
    "evaluateAnswerQuality",
]
