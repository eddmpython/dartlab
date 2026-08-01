"""AI prompt와 lens가 실행 불가능한 비정식 capability를 제안하지 않는지 검증한다."""

from __future__ import annotations

from dartlab.ai.lenses.fundamental import FUNDAMENTAL_LENS
from dartlab.ai.lenses.sentiment import SENTIMENT_LENS
from dartlab.ai.workbench.prompts import DARTLAB_CHAT_SYSTEM, WORK_PROMPT

_NON_CANONICAL_REFS = (
    "Company.executivePay",
    "Company.relatedPartyTx",
    "Company.notesDetail",
    "Company.governance",
    "Company.audit",
    "Company.disclosure",
    "Company.readFiling",
    "Company.ratios",
    "Company.financials",
)


def testPromptsDoNotRecommendNonCanonicalCompanyRefs() -> None:
    combined = DARTLAB_CHAT_SYSTEM + WORK_PROMPT

    assert not any(ref in combined for ref in _NON_CANONICAL_REFS)


def testLensHintsUseCanonicalCompanyRefs() -> None:
    hints = FUNDAMENTAL_LENS.capabilityHints + SENTIMENT_LENS.capabilityHints

    assert not any(ref in hints for ref in _NON_CANONICAL_REFS)
