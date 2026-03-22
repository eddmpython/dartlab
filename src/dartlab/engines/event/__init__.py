"""Event Study 엔진 — 공시 발표일 전후 주가 비정상 수익률 분석.

공시 발표 타이밍이 주가에 미치는 영향을 정량적으로 측정한다.
학술 Event Study 방법론을 자동화하여 dartlab 사용자가 즉시 활용 가능.

사용법::

    import dartlab

    c = dartlab.Company("005930")
    c.eventStudy()                              # 전체 공시 → 주가 영향
    c.eventStudy(event_type="사업보고서")          # 유형별 필터
    c.eventStudy(window=EventWindow(pre=5, post=10))  # 커스텀 윈도우

의존성::

    pip install dartlab[event]   # yfinance 포함
"""

from dartlab.engines.event.study import analyze_events, impacts_to_dataframe
from dartlab.engines.event.types import EventImpact, EventStudyResult, EventWindow

__all__ = [
    "analyze_events",
    "impacts_to_dataframe",
    "EventImpact",
    "EventStudyResult",
    "EventWindow",
]
