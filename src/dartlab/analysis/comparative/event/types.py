"""Event Study 데이터 타입."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EventWindow:
    """이벤트 윈도우 설정."""

    pre: int = 10  # 이벤트 전 거래일 수
    post: int = 20  # 이벤트 후 거래일 수

    @property
    def total(self) -> int:
        """이벤트 윈도우 전체 거래일 수."""
        return self.pre + self.post + 1

    @property
    def estimation_days(self) -> int:
        """추정 윈도우 기간 (이벤트 윈도우 앞 120일)."""
        return 120


@dataclass
class EventImpact:
    """단일 이벤트의 주가 영향 결과."""

    eventDate: str  # 공시 발표일
    eventType: str  # 공시 유형 (reportType)
    stockCode: str
    corpName: str | None

    car: float  # Cumulative Abnormal Return
    bhar: float  # Buy-and-Hold Abnormal Return
    car_tstat: float  # t-통계량
    car_pvalue: float  # p-value

    pre_car: float  # 이벤트 전 CAR (정보 유출 징후)
    post_car: float  # 이벤트 후 CAR

    window: EventWindow = field(default_factory=EventWindow)


@dataclass
class EventStudyResult:
    """Event Study 전체 결과."""

    stockCode: str
    corpName: str | None
    eventCount: int
    impacts: list[EventImpact]

    # 집계
    meanCar: float
    medianCar: float
    significantCount: int  # p < 0.05인 이벤트 수
    preLeakageCount: int  # 사전 유출 징후 (pre_car > threshold)

    def significant_events(self, alpha: float = 0.05) -> list[EventImpact]:
        """통계적으로 유의한 이벤트만."""
        return [e for e in self.impacts if e.car_pvalue < alpha]
