"""감사의견 표준 범주 정규화.

감사 섹션이나 감사인 이름의 존재는 감사의견이 아니다. 이 모듈은 원문에
명시된 네 표준 범주만 정규화하고, 결측·검토보고서·알 수 없는 표기는 판정하지
않는다.
"""

from __future__ import annotations

import re

_MISSING_MARKERS = {"", "-", "해당없음", "해당사항없음", "없음", "n/a", "na", "none"}


def _compact(raw: object) -> str:
    """비교용으로 공백과 문장부호를 최소 정규화한다."""
    return re.sub(r"[\s_-]+", "", str(raw)).strip().lower()


def normalizeAuditOpinion(raw: object) -> str | None:
    """명시된 감사의견을 네 한국어 표준 범주로 정규화한다.

    ``None`` 은 적정이 아니라 미관측/미지원이다. 특히 ``부적정`` 안의
    ``적정`` 및 ``unqualified`` 안의 ``qualified`` 부분문자열을 잘못
    매칭하지 않도록 부정 범주와 영문 범주 순서를 고정한다.
    """
    if raw is None:
        return None
    text = _compact(raw)
    if text in _MISSING_MARKERS:
        return None
    if "검토" in text or "review" in text or "해당사항" in text:
        return None

    if "의견거절" in text or "감사의견거절" in text or "disclaimerofopinion" in text or text == "disclaimer":
        return "의견거절"
    if "부적정" in text or "adverseopinion" in text or text == "adverse":
        return "부적정의견"
    if "한정" in text:
        return "한정의견"

    if "unqualified" in text or "unmodified" in text:
        return "적정의견"
    if "qualified" in text:
        return "한정의견"
    if "적정" in text:
        return "적정의견"
    return None


def auditOpinionStatus(raw: object) -> str:
    """원문을 ``observed``/``missing``/``ambiguous`` 상태로 분류한다."""
    if normalizeAuditOpinion(raw) is not None:
        return "observed"
    if raw is None:
        return "missing"
    text = _compact(raw)
    if text in _MISSING_MARKERS or "검토" in text or "review" in text or "해당사항" in text:
        return "missing"
    return "ambiguous"


__all__ = ["auditOpinionStatus", "normalizeAuditOpinion"]
