"""3-6 신용평가 — dartlab.credit.calcs로 이동됨.

cross-dependency 방지: analysis ↛ credit.
이 모듈의 calc 함수들은 dartlab.credit.calcs로 이동했다.
review/registry.py는 dartlab.credit.calcs에서 직접 import한다.

마이그레이션::

    # Before
    from dartlab.analysis.financial.creditRating import calcCreditScore

    # After
    from dartlab.credit.calcs import calcCreditScore
"""

from __future__ import annotations


def __getattr__(name: str):
    _MOVED = {
        "calcCreditMetrics",
        "calcCreditScore",
        "calcCreditHistory",
        "calcCashFlowGrade",
        "calcCreditPeerPosition",
        "calcCreditFlags",
    }
    if name in _MOVED:
        raise ImportError(f"{name} has moved to dartlab.credit.calcs. Use: from dartlab.credit.calcs import {name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
