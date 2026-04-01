"""dartlab 독립 신용평가 엔진 (dCR).

공시 데이터만으로 재현 가능한 독립 신용등급을 산출한다.
7축 정량 스코어링 + 업종별 차등 + 시계열 안정화 → dCR-AAA ~ dCR-D.

사용법::

    import dartlab

    dartlab.credit("005930")                    # 삼성전자 신용등급
    c = dartlab.Company("005930")
    c.credit()                                  # Company-bound
    c.credit(detail=True)                       # 7축 상세 포함

설계 원칙:
    1. 재현 가능성 — 같은 입력 → 같은 등급
    2. 투명성 — 모든 근거 공개
    3. 보수주의 — 의심스러우면 낮게
    4. 지속 발전 — audit가 엔진을 발전시킨다
    5. 독립성 — dartlab만의 판단

ops/credit.md 참조.
"""

from __future__ import annotations

from typing import Any


def credit(stockCode: str, *, detail: bool = False, basePeriod: str | None = None) -> dict | None:
    """신용등급 산출 단일 진입점.

    Parameters
    ----------
    stockCode : 종목코드 또는 ticker
    detail : True이면 7축 상세 + 모든 지표 포함
    basePeriod : 분석 기준 기간 (None이면 최신)

    Returns
    -------
    dict | None
        등급 결과. 데이터 부족 시 None.
    """
    from dartlab.credit.engine import evaluate

    return evaluate(stockCode, detail=detail, basePeriod=basePeriod)
