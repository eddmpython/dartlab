"""dartlab 독립 신용평가 엔진 (dCR).

공시 데이터만으로 재현 가능한 독립 신용등급을 산출한다.
7축 정량 스코어링 + 업종별 차등 + 시계열 안정화 → dCR-AAA ~ dCR-D.

사용법::

    import dartlab

    # 루트 함수
    dartlab.credit("005930")                # 삼성전자 등급 종합
    dartlab.credit("005930", "채무상환")     # 채무상환 축만

    # Company-bound
    c = dartlab.Company("005930")
    c.credit()                              # 등급 종합
    c.credit("채무상환")                     # 축별 접근
    c.credit(detail=True)                   # 7축 상세 + 지표 시계열

    # review 경유 보고서
    c.review("신용평가")                     # 신용평가 전문 보고서
    c.review("신용평가").toMarkdown()         # 마크다운 출력

ops/credit.md 참조.
"""

from __future__ import annotations

# ── 7축 레지스트리 ──

_CREDIT_AXES: dict[str, str] = {
    "채무상환": "채무상환능력",
    "자본구조": "자본구조",
    "유동성": "유동성",
    "현금흐름": "현금흐름",
    "사업안정성": "사업안정성",
    "재무신뢰성": "재무신뢰성",
    "공시리스크": "공시리스크",
}

_ALIASES: dict[str, str] = {
    "repayment": "채무상환",
    "leverage": "자본구조",
    "capital": "자본구조",
    "liquidity": "유동성",
    "cashflow": "현금흐름",
    "business": "사업안정성",
    "reliability": "재무신뢰성",
    "disclosure": "공시리스크",
    "채무상환능력": "채무상환",
    "사업위험": "사업안정성",
    "사업": "사업안정성",
    "신뢰성": "재무신뢰성",
    "공시": "공시리스크",
}


def _resolveAxis(axis: str) -> str | None:
    """축 이름 또는 alias → 정규 축 이름."""
    if axis in _CREDIT_AXES:
        return axis
    if axis in _ALIASES:
        return _ALIASES[axis]
    lower = axis.lower()
    if lower in _ALIASES:
        return _ALIASES[lower]
    return None


def _filterAxis(result: dict, axis: str) -> dict | None:
    """등급 결과에서 특정 축만 추출."""
    resolved = _resolveAxis(axis)
    if resolved is None:
        available = ", ".join(sorted(_CREDIT_AXES))
        raise ValueError(
            f"알 수 없는 신용평가 축: '{axis}'. 가용 축: {available}\n"
            f"  사용법: c.credit() 으로 전체 신용평가 결과를 확인하세요."
        )

    fullName = _CREDIT_AXES[resolved]
    for a in result.get("axes", []):
        if a.get("name") == fullName:
            return {
                "axis": fullName,
                "score": a.get("score"),
                "weight": a.get("weight"),
                "metrics": a.get("metrics", []),
                "grade": result.get("grade"),
                "overallScore": result.get("score"),
            }
    return None


def credit(
    stockCode: str, axis: str | None = None, *, detail: bool = False, basePeriod: str | None = None
) -> dict | None:
    """신용등급 산출 단일 진입점.

    Parameters
    ----------
    stockCode : 종목코드 또는 ticker
    axis : 축 이름 (None이면 전체, "채무상환" 등이면 해당 축만)
    detail : True이면 7축 상세 + 모든 지표 포함
    basePeriod : 분석 기준 기간 (None이면 최신)

    Returns
    -------
    dict | None
        등급 결과. axis 지정 시 해당 축만 반환.
    """
    from dartlab.credit.engine import evaluate

    result = evaluate(stockCode, detail=detail or (axis is not None), basePeriod=basePeriod)
    if result is None:
        return None

    if axis is not None:
        return _filterAxis(result, axis)

    return result


def creditCompany(
    company, axis: str | None = None, *, detail: bool = False, basePeriod: str | None = None
) -> dict | None:
    """Company 객체로 신용등급 산출 (Company-bound용)."""
    from dartlab.credit.engine import evaluateCompany

    result = evaluateCompany(company, detail=detail or (axis is not None), basePeriod=basePeriod)
    if result is None:
        return None

    if axis is not None:
        return _filterAxis(result, axis)

    return result


def axes() -> dict[str, str]:
    """가용한 7축 목록."""
    return dict(_CREDIT_AXES)
