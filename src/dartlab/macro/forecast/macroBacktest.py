"""매크로 과거검증 경계.

현재 provider는 최신 수정치의 관측일 cutoff만 제공한다. 빈티지와 공표 지연이
확보되기 전에는 point-in-time 성과지표를 발행하지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

# NBER 공식 침체 구간 (미국)
_NBER_RECESSIONS = [
    (date(2001, 3, 1), date(2001, 11, 1)),  # 닷컴
    (date(2007, 12, 1), date(2009, 6, 1)),  # GFC
    (date(2020, 2, 1), date(2020, 4, 1)),  # 코로나
]


@dataclass(frozen=True)
class BacktestPoint:
    """백테스트 단일 시점 결과."""

    asOf: str  # 기준 날짜
    phase: str | None  # 사이클 국면
    recessionProb: float | None  # 침체 확률
    overall: str | None  # 종합 판정
    score: float | None  # 종합 점수
    actualRecession: bool  # NBER 기준 실제 침체 여부


@dataclass(frozen=True)
class BacktestResult:
    """walk-forward 백테스트 결과."""

    points: list[BacktestPoint]
    totalPoints: int
    recessionCalls: int  # 침체 판정 횟수
    actualRecessions: int  # 실제 침체 시점 수
    truePositives: int  # 침체 판정 + 실제 침체
    falsePositives: int  # 침체 판정 + 실제 비침체
    falseNegatives: int  # 비침체 판정 + 실제 침체
    precision: float | None  # TP / (TP + FP)
    recall: float | None  # TP / (TP + FN)
    description: str
    status: str = "unavailable"
    reason: str | None = None
    asOfMode: str = "observationDateCutoff"
    vintageSafe: bool = False
    releaseLagSafe: bool = False
    performanceEligible: bool = False


def _isInRecession(d: date) -> bool:
    """NBER 기준 침체 구간에 있는지 확인."""
    for start, end in _NBER_RECESSIONS:
        if start <= d <= end:
            return True
    return False


def walkForwardBacktest(
    startDate: str = "2005-01-01",
    endDate: str = "2024-01-01",
    stepMonths: int = 3,
    market: str = "US",
    recessionThreshold: float = 0.3,
) -> BacktestResult:
    """빈티지 자료가 없는 매크로 성과검증을 구조적으로 차단한다.

    Capabilities:
        현재 데이터 공급자는 관측일 cutoff만 제공하며 당시 공개된 빈티지와
        공표 지연을 재현하지 못한다. 따라서 precision/recall을 계산하지 않는다.

    Args:
        startDate: 시작 날짜 (YYYY-MM-DD).
        endDate: 종료 날짜.
        stepMonths: 스텝 크기 (개월). 기본 3 (분기).
        market: ``"US"`` | ``"KR"``.
        recessionThreshold: 침체 판정 임계 (기본 0.3).

    Returns:
        status="unavailable", precision=None, recall=None인 BacktestResult.

    Example:
        >>> r = walkForwardBacktest("2005-01-01", "2020-01-01")
        >>> r.status, r.precision
        ('unavailable', None)

    Guide:
        ALFRED/FRED vintage와 release date가 연결된 뒤에만 성과평가를 활성화한다.

    When:
        매크로 모델 정확성 검증 + 새 신호 도입 시 회귀 가드.

    How:
        입력 날짜 검증 → PIT 전제 미충족 사유와 함께 차단 결과 반환.

    Requires:
        현재 미충족: 시리즈별 vintage와 공표시점 데이터.

    Raises:
        ValueError: 날짜 형식·범위 또는 stepMonths가 잘못된 경우.

    See Also:
        - analyzeForecast : recessionProb 입력
        - analyzeCycle : phase 입력
        - clevelandProbit : 단일 모델

    AIContext:
        status와 reason만 인용한다. precision/recall은 발행하지 않는다.

    LLM Specifications:
        AntiPatterns:
            - stepMonths 1 로 N=240+ 호출 (FRED rate limit + polars 힙)
            - recessionThreshold 임의 (0.3 표준)
            - observation-date cutoff 결과를 point-in-time 성과로 해석
        OutputSchema:
            BacktestResult ``(status, reason, asOfMode, vintageSafe,
            releaseLagSafe, performanceEligible, precision, recall)``.
        Prerequisites: ALFRED/FRED vintage + 시리즈별 공표일.
        Freshness: 정적 결과 (한 번 실행).
        Dataflow: date 순회 → 시점별 분석 → confusion matrix.
        TargetMarkets: US (NBER). KR NBER 대체 (BOK 경기순환) 필요.
    """
    from datetime import datetime

    start = datetime.strptime(startDate, "%Y-%m-%d").date()
    end = datetime.strptime(endDate, "%Y-%m-%d").date()

    if start > end:
        raise ValueError("startDate는 endDate보다 늦을 수 없습니다.")
    if stepMonths <= 0:
        raise ValueError("stepMonths는 1 이상이어야 합니다.")

    reason = (
        "현재 매크로 provider는 최신 수정치의 관측일 cutoff만 지원하며 "
        "빈티지와 공표 지연을 재현하지 못해 성과지표를 발행할 수 없습니다."
    )

    return BacktestResult(
        points=[],
        totalPoints=0,
        recessionCalls=0,
        actualRecessions=0,
        truePositives=0,
        falsePositives=0,
        falseNegatives=0,
        precision=None,
        recall=None,
        description=reason,
        reason=reason,
    )
