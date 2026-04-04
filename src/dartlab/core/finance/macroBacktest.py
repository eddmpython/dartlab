"""매크로 walk-forward 백테스트 — 과거 시점에서 신호 재현 + 적중률 측정.

순수 판정 함수. core/ 계층 소속.

방법론: rolling re-estimation (Fed 2019)
- 매 분기(또는 월) cutoff를 이동하며 매크로 분석 재실행
- NBER 침체 날짜와 비교하여 precision/recall 측정
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


# NBER 공식 침체 구간 (미국)
_NBER_RECESSIONS = [
    (date(2001, 3, 1), date(2001, 11, 1)),   # 닷컴
    (date(2007, 12, 1), date(2009, 6, 1)),    # GFC
    (date(2020, 2, 1), date(2020, 4, 1)),     # 코로나
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


def _is_in_recession(d: date) -> bool:
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
    """walk-forward 백테스트 실행.

    Args:
        startDate: 시작 날짜 (YYYY-MM-DD)
        endDate: 종료 날짜
        stepMonths: 스텝 크기 (개월)
        market: "US" | "KR"
        recessionThreshold: 침체 판정 임계값 (recessionProb ≥ 이 값이면 침체)

    Returns:
        BacktestResult: 시점별 신호 + precision/recall
    """
    from datetime import datetime

    start = datetime.strptime(startDate, "%Y-%m-%d").date()
    end = datetime.strptime(endDate, "%Y-%m-%d").date()

    points: list[BacktestPoint] = []
    current = start

    while current <= end:
        as_of_str = current.strftime("%Y-%m-%d")

        # 해당 시점에서 매크로 분석
        phase = None
        recession_prob = None
        overall = None
        score = None

        try:
            from dartlab.macro.cycle import analyze_cycle

            cycle_result = analyze_cycle(market=market, as_of=as_of_str)
            phase = cycle_result.get("phase")
        except Exception:
            pass

        try:
            from dartlab.macro.forecast import analyze_forecast

            forecast_result = analyze_forecast(market=market, as_of=as_of_str)
            rp = forecast_result.get("recessionProb")
            if rp:
                recession_prob = rp.get("probability")
        except Exception:
            pass

        actual = _is_in_recession(current)

        points.append(BacktestPoint(
            asOf=as_of_str,
            phase=phase,
            recessionProb=recession_prob,
            overall=overall,
            score=score,
            actualRecession=actual,
        ))

        # 다음 스텝
        month = current.month + stepMonths
        year = current.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        current = date(year, month, 1)

    # 적중률 계산
    tp = fp = fn = 0
    recession_calls = 0
    actual_recessions = sum(1 for p in points if p.actualRecession)

    for p in points:
        called_recession = (
            (p.recessionProb is not None and p.recessionProb >= recessionThreshold)
            or p.phase == "contraction"
        )
        if called_recession:
            recession_calls += 1
        if called_recession and p.actualRecession:
            tp += 1
        elif called_recession and not p.actualRecession:
            fp += 1
        elif not called_recession and p.actualRecession:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None

    desc = f"백테스트 {startDate}~{endDate} ({len(points)}시점): "
    if precision is not None:
        desc += f"precision={precision:.1%}, recall={recall:.1%}"
    else:
        desc += "침체 판정 없음"

    return BacktestResult(
        points=points,
        totalPoints=len(points),
        recessionCalls=recession_calls,
        actualRecessions=actual_recessions,
        truePositives=tp,
        falsePositives=fp,
        falseNegatives=fn,
        precision=precision,
        recall=recall,
        description=desc,
    )
