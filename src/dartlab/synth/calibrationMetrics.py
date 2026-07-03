"""확률 캘리브레이션 메트릭 : Brier Score + 신뢰도 다이어그램 데이터.

네이트 실버 원칙: "80% 확률 예측이 정말 80% 맞는지" 검증.
기상청이 예측에 성공한 핵심 이유: 확률 구간별 적중률을 추적한다.

L1.5 synth 배치 (analysis 에서 승격, 2026-07-03): 이진 방향 채점을 analysis(forwardTest)와
simulate(expectation 원장 채점)가 함께 쓰므로 공용 계산 자리인 synth 가 정위치다
(선례 = ``synth.eventStudy``). 옛 경로 ``analysis.forecast.calibrationMetrics`` 는
re-export 호환 stub 로 유지된다.
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

    Capabilities:
        - 확률 예측의 평균 제곱 오차 계산
        - 캘리브레이션 베이스 지표 제공

    Parameters
    ----------
    predictions : list[float]
        예측 확률 목록 (0~1).
    outcomes : list[int]
        실제 결과 목록 (0 또는 1).

    Returns
    -------
    float
        Brier Score (0~1). 데이터 없으면 1.0.

    Guide:
        예측 확률·실제 결과 두 리스트를 같은 길이로 정렬해 호출한다.

    When:
        확률 예측의 정확도를 단일 스칼라로 요약할 때.

    How:
        generateCalibrationReport 내부 호출 또는 단독 사용 가능.

    Requires:
        predictions·outcomes 길이 동일, 값은 [0,1] 구간.

    Raises:
        없음. 데이터 부족 시 1.0 반환.

    Example:
        >>> computeBrierScore([0.7, 0.3], [1, 0])
        0.09

    See Also:
        - buildCalibrationBins : 구간별 적중률 계산
        - generateCalibrationReport : 전체 리포트 생성

    AIContext:
        AI 답변 시 "예측 정확도 Brier=X" 형태로 인용한다.
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
    """확률 구간별 적중률 계산 (reliability diagram 데이터).

    Capabilities:
        - 확률 구간별 평균 예측·실제 적중률 산출
        - 신뢰도 다이어그램 시각화 데이터 제공

    Parameters
    ----------
    predictions : list[float]
        예측 확률 목록 (0~1).
    outcomes : list[int]
        실제 결과 목록 (0 또는 1).
    nBins : int
        구간 수 (기본 5).

    Returns
    -------
    list[CalibrationBin]
        구간별 예측/실제 평균 + 괴리.

    Guide:
        nBins 등분으로 [0,1] 을 나눠 각 구간 내 예측·실제 평균을 묶는다.

    When:
        "80% 예측이 정말 80% 맞는가" 구간별 검증할 때.

    How:
        generateCalibrationReport 가 내부적으로 호출. 단독 시각화도 가능.

    Requires:
        predictions·outcomes 길이 동일, 값은 [0,1] 구간.

    Raises:
        없음. 빈 입력 시 빈 리스트.

    Example:
        >>> bins = buildCalibrationBins([0.1, 0.9], [0, 1], nBins=2)
        >>> len(bins)
        2

    See Also:
        - computeBrierScore : 단일 스칼라 정확도
        - generateCalibrationReport : 전체 리포트 생성

    AIContext:
        AI 답변 시 reliability diagram 구간별 표로 인용.
    """
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
    """전체 캘리브레이션 리포트 생성.

    Capabilities:
        - Brier·Brier Skill·구간별 적중률을 한 리포트로 묶음
        - 캘리브레이션 합격 여부 자동 판정

    Parameters
    ----------
    predictions : list[float]
        예측 확률 목록 (0~1).
    outcomes : list[int]
        실제 결과 목록 (0 또는 1).

    Returns
    -------
    CalibrationReport | None
        Brier Score, Skill Score, 구간별 적중률. 데이터 5개 미만이면 None.

    Guide:
        예측-결과 페어가 5 개 이상 축적된 시점에 한 번 호출.

    When:
        모델/시나리오의 확률 보정도를 종합 평가할 때.

    How:
        computeBrierScore + buildCalibrationBins 결과를 묶어 dataclass 반환.

    Requires:
        predictions·outcomes 길이 동일, ≥5 건.

    Raises:
        없음. 데이터 부족 시 None 반환.

    Example:
        >>> r = generateCalibrationReport([0.5]*10, [1,0]*5)
        >>> r.totalPredictions
        10

    See Also:
        - computeBrierScore : 정확도 지표
        - buildCalibrationBins : 구간별 통계

    AIContext:
        AI 답변 시 캘리브레이션 합격/실패 판정 근거로 인용.
    """
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
