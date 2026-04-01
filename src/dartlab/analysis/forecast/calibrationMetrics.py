"""확률 캘리브레이션 메트릭 — Brier Score + 신뢰도 다이어그램 데이터.

네이트 실버 원칙: "80% 확률 예측이 정말 80% 맞는지" 검증.
기상청이 예측에 성공한 핵심 이유: 확률 구간별 적중률을 추적한다.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CalibrationBin:
    """단일 확률 구간의 캘리브레이션."""

    binLower: float  # 구간 하한 (예: 0.7)
    binUpper: float  # 구간 상한 (예: 0.8)
    meanPredicted: float  # 평균 예측 확률
    meanActual: float  # 실제 적중률
    count: int  # 예측 건수
    gap: float  # |meanPredicted - meanActual|


@dataclass
class CalibrationReport:
    """전체 캘리브레이션 리포트."""

    brierScore: float  # 0~1 (낮을수록 좋음)
    brierSkill: float | None  # 기저율 대비 스킬 (>0이면 기저율보다 나음)
    bins: list[CalibrationBin]  # reliability diagram 데이터
    totalPredictions: int
    baseRate: float  # 실제 "상승" 비율
    maxCalibrationGap: float  # 최대 구간 괴리
    isWellCalibrated: bool  # 모든 구간 gap < 0.10


def computeBrierScore(
    predictions: list[float],
    outcomes: list[int],
) -> float:
    """Brier Score = mean((predicted - actual)^2).

    0 = 완벽, 1 = 최악.
    """
    if not predictions or len(predictions) != len(outcomes):
        return 1.0
    total = sum((p - o) ** 2 for p, o in zip(predictions, outcomes))
    return total / len(predictions)


def buildCalibrationBins(
    predictions: list[float],
    outcomes: list[int],
    nBins: int = 5,
) -> list[CalibrationBin]:
    """확률 구간별 적중률 계산 (reliability diagram 데이터)."""
    if not predictions:
        return []

    binWidth = 1.0 / nBins
    bins: list[CalibrationBin] = []

    for i in range(nBins):
        lower = i * binWidth
        upper = (i + 1) * binWidth

        preds = []
        acts = []
        for p, o in zip(predictions, outcomes):
            if lower <= p < upper or (i == nBins - 1 and p == upper):
                preds.append(p)
                acts.append(o)

        if preds:
            meanP = sum(preds) / len(preds)
            meanA = sum(acts) / len(acts)
            bins.append(
                CalibrationBin(
                    binLower=round(lower, 2),
                    binUpper=round(upper, 2),
                    meanPredicted=round(meanP, 4),
                    meanActual=round(meanA, 4),
                    count=len(preds),
                    gap=round(abs(meanP - meanA), 4),
                )
            )

    return bins


def generateCalibrationReport(
    predictions: list[float],
    outcomes: list[int],
) -> CalibrationReport | None:
    """전체 캘리브레이션 리포트 생성."""
    if not predictions or len(predictions) < 5:
        return None

    brier = computeBrierScore(predictions, outcomes)
    bins = buildCalibrationBins(predictions, outcomes)
    baseRate = sum(outcomes) / len(outcomes) if outcomes else 0.5

    # Brier Skill Score: 1 - (brier / brier_ref), brier_ref = baseRate*(1-baseRate)
    brierRef = baseRate * (1 - baseRate)
    brierSkill = 1 - (brier / brierRef) if brierRef > 0 else None

    maxGap = max((b.gap for b in bins), default=0.0)
    wellCalibrated = all(b.gap < 0.10 for b in bins) if bins else False

    return CalibrationReport(
        brierScore=round(brier, 4),
        brierSkill=round(brierSkill, 4) if brierSkill is not None else None,
        bins=bins,
        totalPredictions=len(predictions),
        baseRate=round(baseRate, 4),
        maxCalibrationGap=round(maxGap, 4),
        isWellCalibrated=wellCalibrated,
    )
