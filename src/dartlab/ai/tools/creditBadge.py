"""dCR 신용등급 badge 헬퍼 — Track G (Ask 모드 자율 등급 노출).

Company.panel 응답에 자동 부착되는 가벼운 badge dict 를 만든다. 외부 등급 (S&P/Moody's)
의존 없이 dartlab credit engine 의 self-rated dCR 등급을 답변 헤더 chip 으로 즉시 노출.

부착 정책:
- Company.panel 호출 시 BS/IS/CF 와 무관하게 *1 회* 평가. 실패 (데이터 부족·금융사 fallback 부족)
  시 None 반환 — engineCall 은 그 경우 dcrBadge 키 생략.
- 신뢰도: method="ratio" (deterministic financial ratios) → base 80. evaluateCompany 가 시계열·CHS·
  Notch 보정까지 계산하므로 단일 비율보다 충분.
"""

from __future__ import annotations

from typing import Any

from dartlab.core.confidence import baseScore


def getDcrBadge(company: Any) -> dict[str, Any] | None:
    """Company 인스턴스 → dCR badge dict 또는 None.

    반환 키:
        grade (str) — "dCR-AA+" 형식.
        gradeRaw (str) — "AA+" (chip 표시용).
        score (float) — 0-100 위험점수 (0 = 최우량).
        healthScore (float) — 100 - score (UI 양의 방향).
        pdEstimate (float | None) — 1 년 부도확률 (%).
        outlook (str) — "안정적"/"긍정적"/"부정적".
        investmentGrade (bool).
        axes (list[dict]) — 발행 가능한 비금융 7 축 점수 상세. 각 항목: name/weight/score.
        confidence (int) — 0-100.
        confidenceMethod (str) — "ratio".

    실패 또는 금융 ``diagnostic_only`` 시 None. engineCall 은 None 이면 dcrBadge 생략.
    """
    if company is None:
        return None
    try:
        from dartlab.credit.engine import evaluateCompany
    except ImportError:
        return None
    try:
        result = evaluateCompany(company, detail=False)
    except Exception:
        return None
    if not isinstance(result, dict) or not result.get("grade"):
        return None
    axes_raw = result.get("axes") or []
    axes: list[dict[str, Any]] = []
    for axis in axes_raw:
        if not isinstance(axis, dict):
            continue
        axes.append(
            {
                "name": axis.get("name") or axis.get("label") or "",
                "weight": axis.get("weight"),
                "score": axis.get("score"),
            }
        )
    return {
        "grade": result.get("grade"),
        "gradeRaw": result.get("gradeRaw"),
        "score": result.get("score"),
        "healthScore": result.get("healthScore"),
        "pdEstimate": result.get("pdEstimate"),
        "outlook": result.get("outlook"),
        "investmentGrade": result.get("investmentGrade"),
        "axes": axes,
        "confidence": baseScore("ratio"),
        "confidenceMethod": "ratio",
    }


__all__ = ["getDcrBadge"]
