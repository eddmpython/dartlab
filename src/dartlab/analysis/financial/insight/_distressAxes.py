"""부실 스코어카드 5 축 조립 (distress.calcDistress 의 축별 seam).

축마다 "모델 목록 수집 → 정규화 평균 → 요약 문장 → DistressAxis" 라는 같은 모양이
반복된다. calcDistress 본문에서 그 되풀이를 축 하나당 함수 하나로 떼어낸다.
가중치는 Merton 사용 여부로만 갈리므로 useMerton 을 인자로 받는다.
"""

from __future__ import annotations

from dartlab.analysis.financial.insight._distressModels import (
    _interpretAltmanZ,
    _interpretAltmanZpp,
    _interpretAuditRedFlags,
    _interpretBeneish,
    _interpretMerton,
    _interpretOhlson,
    _interpretPiotroski,
    _interpretSloan,
    _normalizeBeneish,
    _normalizeFScore,
    _normalizeMerton,
    _normalizeOhlson,
    _normalizeSloan,
    _normalizeZ,
    _normalizeZpp,
)
from dartlab.analysis.financial.insight.types import Anomaly, DistressAxis, ModelScore
from dartlab.analysis.financial.ratios import RatioResult


def _quantAxis(ratios: RatioResult, useMerton: bool) -> tuple[DistressAxis, list[ModelScore]]:
    """정량 축 (O-Score, Z''-Score, Z-Score).

    Parameters
    ----------
    ratios : RatioResult
        재무비율 계산 결과.
    useMerton : bool
        Merton 축 사용 여부. 가중치만 바꾼다.

    Returns
    -------
    tuple[DistressAxis, list[ModelScore]]
        axis : DistressAxis. models : list[ModelScore] (모델 수 집계용).
    """
    models: list[ModelScore] = []
    norms: list[float] = []

    if ratios.ohlsonProbability is not None:
        models.append(_interpretOhlson(ratios.ohlsonProbability))
        norms.append(_normalizeOhlson(ratios.ohlsonProbability))

    if ratios.altmanZppScore is not None:
        models.append(_interpretAltmanZpp(ratios.altmanZppScore))
        norms.append(_normalizeZpp(ratios.altmanZppScore))

    if ratios.altmanZScore is not None:
        models.append(_interpretAltmanZ(ratios.altmanZScore))
        norms.append(_normalizeZ(ratios.altmanZScore))

    score = sum(norms) / len(norms) if norms else 0
    zones = [m.zone for m in models]
    if not models:
        summary = "정량 모델 데이터 부족."
    elif all(z == "safe" for z in zones):
        summary = f"{len(models)}개 모델 모두 안전 영역."
    elif any(z == "distress" for z in zones):
        nDistress = sum(1 for z in zones if z == "distress")
        summary = f"{nDistress}/{len(models)}개 모델 부실 영역. 즉각 점검 필요."
    else:
        summary = f"{len(models)}개 모델 회색 영역 포함. 모니터링 권고."

    axis = DistressAxis(
        name="정량 분석",
        score=round(score, 1),
        weight=0.30 if useMerton else 0.40,
        models=models,
        summary=summary,
    )
    return axis, models


def _earningsQualityAxis(ratios: RatioResult, useMerton: bool) -> tuple[DistressAxis, list[ModelScore]]:
    """이익 품질 축 (Beneish M, Sloan Accrual, Piotroski F).

    Parameters
    ----------
    ratios : RatioResult
        재무비율 계산 결과.
    useMerton : bool
        Merton 축 사용 여부. 가중치만 바꾼다.

    Returns
    -------
    tuple[DistressAxis, list[ModelScore]]
        axis : DistressAxis. models : list[ModelScore] (모델 수 집계용).
    """
    models: list[ModelScore] = []
    norms: list[float] = []

    if ratios.beneishMScore is not None:
        models.append(_interpretBeneish(ratios.beneishMScore))
        norms.append(_normalizeBeneish(ratios.beneishMScore))

    if ratios.sloanAccrualRatio is not None:
        models.append(_interpretSloan(ratios.sloanAccrualRatio))
        norms.append(_normalizeSloan(ratios.sloanAccrualRatio))

    if ratios.piotroskiFScore is not None:
        models.append(_interpretPiotroski(ratios.piotroskiFScore))
        norms.append(_normalizeFScore(ratios.piotroskiFScore))

    score = sum(norms) / len(norms) if norms else 0
    if not models:
        summary = "이익 품질 모델 데이터 부족."
    elif all(m.zone == "safe" for m in models):
        summary = f"{len(models)}개 지표 모두 양호. 이익 품질 건전."
    elif any(m.zone == "distress" for m in models):
        summary = "이익 품질 의심 지표 존재. 회계 검토 권고."
    else:
        summary = "이익 품질 보통. 일부 지표 모니터링 필요."

    axis = DistressAxis(
        name="이익 품질",
        score=round(score, 1),
        weight=0.15 if useMerton else 0.20,
        models=models,
        summary=summary,
    )
    return axis, models


def _trendAxis(anomalies: list[Anomaly], useMerton: bool) -> DistressAxis:
    """추세 축. anomaly 중 시계열 악화 카테고리만 누적한다.

    Parameters
    ----------
    anomalies : list[Anomaly]
        이상치 탐지 결과 전체.
    useMerton : bool
        Merton 축 사용 여부. 가중치만 바꾼다.

    Returns
    -------
    DistressAxis
        추세 분석 축.
    """
    score = 0.0
    trendAnomalies = [a for a in anomalies if a.category in ("trendDeterioration", "cccDeterioration")]
    for a in trendAnomalies:
        if a.severity == "danger":
            score += 40
        elif a.severity == "warning":
            score += 25
        else:
            score += 10
    score = min(score, 100)

    if not trendAnomalies:
        summary = "시계열 악화 패턴 없음."
    else:
        nDanger = sum(1 for a in trendAnomalies if a.severity == "danger")
        summary = f"악화 패턴 {len(trendAnomalies)}건 탐지"
        if nDanger:
            summary += f" (심각 {nDanger}건). 즉각 점검 필요."
        else:
            summary += ". 모니터링 권고."

    return DistressAxis(
        name="추세 분석",
        score=round(score, 1),
        weight=0.25 if useMerton else 0.30,
        summary=summary,
    )


def _auditAxis(anomalies: list[Anomaly]) -> DistressAxis:
    """감사 축. 감사/거버넌스 Red Flag 건수와 심각도로 채점한다.

    Parameters
    ----------
    anomalies : list[Anomaly]
        이상치 탐지 결과 전체.

    Returns
    -------
    DistressAxis
        감사 위험 축. 가중치는 Merton 여부와 무관하게 0.10.
    """
    score = 0.0
    auditAnomalies = [a for a in anomalies if a.category in ("audit", "governance")]
    models: list[ModelScore] = []

    # 감사 Red Flag 수 기반 점수
    nCritical = sum(1 for a in auditAnomalies if a.severity == "danger")
    nTotal = len(auditAnomalies)

    if nTotal > 0:
        models.append(_interpretAuditRedFlags(nTotal, nCritical > 0))

    for a in auditAnomalies:
        if a.severity == "danger":
            score += 50
        elif a.severity == "warning":
            score += 25
    score = min(score, 100)

    if not auditAnomalies:
        summary = "감사 이상징후 없음."
    elif nCritical > 0:
        summary = f"감사 Red Flag {nTotal}건 (심각 {nCritical}건). 즉각 점검 필요."
    else:
        summary = f"감사 이상 {nTotal}건 탐지. 모니터링 권고."

    return DistressAxis(
        name="감사 위험",
        score=round(score, 1),
        weight=0.10,
        models=models,
        summary=summary,
    )


def _marketAxis(mertonResult: dict) -> DistressAxis:
    """시장 기반 축 (Merton D2D).

    Parameters
    ----------
    mertonResult : dict
        ``{"d2d": float, "pd": float, "converged": bool}``.

    Returns
    -------
    DistressAxis
        시장 기반 축.

    Raises
    ------
    KeyError
        d2d 키가 없으면 그대로 전파한다 (기존 동작 유지).
    """
    model = _interpretMerton(mertonResult)
    d2d = mertonResult["d2d"]
    score = _normalizeMerton(d2d)

    if d2d > 4:
        summary = f"D2D {d2d:.2f}. 시장 기반 부도 거리 충분."
    elif d2d > 2:
        summary = f"D2D {d2d:.2f}. 모니터링 필요."
    elif d2d > 1:
        summary = f"D2D {d2d:.2f}. 부실 위험 영역."
    else:
        summary = f"D2D {d2d:.2f}. 부도 임박 영역."

    return DistressAxis(
        name="시장 기반",
        score=round(score, 1),
        weight=0.20,
        models=[model],
        summary=summary,
    )


def _distressLevel(overall: float) -> str:
    """종합 점수를 5 단계 레벨로 매핑.

    Parameters
    ----------
    overall : float
        가중 종합 부실 점수 (0~100).

    Returns
    -------
    str
        'critical' | 'danger' | 'warning' | 'watch' | 'safe'.
    """
    if overall >= 70:
        return "critical"
    if overall >= 50:
        return "danger"
    if overall >= 30:
        return "warning"
    if overall >= 15:
        return "watch"
    return "safe"


__all__ = [
    "_auditAxis",
    "_distressLevel",
    "_earningsQualityAxis",
    "_marketAxis",
    "_quantAxis",
    "_trendAxis",
]
