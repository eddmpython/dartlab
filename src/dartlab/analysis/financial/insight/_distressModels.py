"""distress 부실 모델 인터프리터 + 정규화 — Altman/Ohlson/Beneish/Sloan/Piotroski/Merton/Audit.

distress.py 822 줄 분할. 6 _interpret* + 6 _normalize* + Merton/Audit 인터프리터
약 376 줄. distress.py 의 facade (calcDistress + cashRunway + riskFactors) 책임만 유지.

BC: distress 모듈에서 모든 _interpret* / _normalize* import 가능 (re-export).
"""

from __future__ import annotations

from dartlab.analysis.financial.insight.types import ModelScore


def _interpretOhlson(probability: float) -> ModelScore:
    """Ohlson O-Score 부도확률 → ModelScore 해석.

    Parameters
    ----------
    probability : float
        부도 확률 (%).

    Returns
    -------
    ModelScore
        name : str — 'Ohlson O-Score'
        rawValue : float — 부도 확률 (%)
        zone : str — 'safe' | 'gray' | 'distress'
        interpretation : str — 해석 텍스트
    """
    if probability < 1:
        zone, interp = "safe", "부도 확률 극히 낮음. 재무구조 건전."
    elif probability < 10:
        zone, interp = "gray", "부도 확률 낮으나 모니터링 필요."
    elif probability < 30:
        zone, interp = "distress", "부도 확률 유의미. 재무구조 점검 필요."
    else:
        zone, interp = "distress", "부도 확률 매우 높음. 즉각적 재무 점검 권고."
    return ModelScore(
        name="Ohlson O-Score",
        rawValue=round(probability, 2),
        displayValue=f"P(부도) {probability:.1f}%",
        zone=zone,
        interpretation=interp,
        reference="Ohlson (1980), 9변수 로지스틱, 학술 적중률 96.1%",
    )


def _interpretAltmanZpp(score: float) -> ModelScore:
    """Altman Z''-Score → ModelScore 해석.

    Parameters
    ----------
    score : float
        Z''-Score 값.

    Returns
    -------
    ModelScore
        name : str — 'Altman Z''-Score'
        rawValue : float — Z'' 값
        zone : str — 'safe' | 'gray' | 'distress'
        interpretation : str — 해석 텍스트
    """
    if score > 2.6:
        zone, interp = "safe", "비제조업/신흥시장 기준 안전 영역."
    elif score >= 1.1:
        zone, interp = "gray", "회색 영역. 추가 모니터링 권고."
    else:
        zone, interp = "distress", "부실 영역. 즉각적 대응 필요."
    return ModelScore(
        name="Altman Z''-Score",
        rawValue=round(score, 2),
        displayValue=f"Z'' = {score:.2f}",
        zone=zone,
        interpretation=interp,
        reference="Altman (1995), 비제조업/신흥시장 변형 4변수",
    )


def _interpretAltmanZ(score: float) -> ModelScore:
    """Altman Z-Score → ModelScore 해석.

    Parameters
    ----------
    score : float
        Z-Score 값.

    Returns
    -------
    ModelScore
        name : str — 'Altman Z-Score'
        rawValue : float — Z 값
        zone : str — 'safe' | 'gray' | 'distress'
        interpretation : str — 해석 텍스트
    """
    if score > 2.99:
        zone, interp = "safe", "제조업 기준 안전 영역."
    elif score >= 1.81:
        zone, interp = "gray", "회색 영역. 추가 모니터링 권고."
    else:
        zone, interp = "distress", "부실 영역. 부도 위험 높음."
    return ModelScore(
        name="Altman Z-Score",
        rawValue=round(score, 2),
        displayValue=f"Z = {score:.2f}",
        zone=zone,
        interpretation=interp,
        reference="Altman (1968), 상장 제조업 5변수 판별모형",
    )


def _interpretBeneish(score: float) -> ModelScore:
    """Beneish M-Score → ModelScore 해석.

    Parameters
    ----------
    score : float
        M-Score 값.

    Returns
    -------
    ModelScore
        name : str — 'Beneish M-Score'
        rawValue : float — M 값
        zone : str — 'safe' | 'gray' | 'distress'
        interpretation : str — 이익 조작 가능성 해석
    """
    if score > -1.78:
        zone, interp = "distress", "이익 조작 가능성 높음. 회계 품질 의심."
    elif score > -2.22:
        zone, interp = "gray", "이익 조작 가능성 존재. 추가 검토 필요."
    else:
        zone, interp = "safe", "이익 조작 가능성 낮음. 회계 품질 양호."
    return ModelScore(
        name="Beneish M-Score",
        rawValue=round(score, 2),
        displayValue=f"M = {score:.2f}",
        zone=zone,
        interpretation=interp,
        reference="Beneish (1999), 8변수, cutoff -2.22",
    )


def _interpretSloan(ratio: float) -> ModelScore:
    """Sloan Accrual Ratio → ModelScore 해석.

    Parameters
    ----------
    ratio : float
        발생주의 이익 비율 (%).

    Returns
    -------
    ModelScore
        name : str — 'Sloan Accrual'
        rawValue : float — 비율 (%)
        zone : str — 'safe' | 'gray' | 'distress'
        interpretation : str — 이익 품질 해석
    """
    abs_r = abs(ratio)
    if abs_r > 20:
        zone, interp = "distress", "발생주의 이익 비중 과다. 이익 품질 의심."
    elif abs_r > 10:
        zone, interp = "gray", "발생주의 이익 비중 다소 높음. 모니터링 필요."
    else:
        zone, interp = "safe", "발생주의 이익 비중 정상. 현금 기반 이익 건전."
    return ModelScore(
        name="Sloan Accrual",
        rawValue=round(ratio, 2),
        displayValue=f"{ratio:.1f}%",
        zone=zone,
        interpretation=interp,
        reference="Sloan (1996), |Accrual/TA| > 10% 주의",
    )


def _interpretPiotroski(score: int) -> ModelScore:
    """Piotroski F-Score → ModelScore 해석.

    Parameters
    ----------
    score : int
        F-Score (0~9) (점).

    Returns
    -------
    ModelScore
        name : str — 'Piotroski F-Score'
        rawValue : float — F 값 (점)
        zone : str — 'safe' | 'gray' | 'distress'
        interpretation : str — 펀더멘탈 해석
    """
    if score >= 7:
        zone, interp = "safe", "펀더멘탈 강건. 수익성·레버리지·효율성 양호."
    elif score >= 5:
        zone, interp = "gray", "펀더멘탈 보통. 일부 지표 개선 필요."
    elif score >= 3:
        zone, interp = "gray", "펀더멘탈 취약. 다수 지표 악화."
    else:
        zone, interp = "distress", "펀더멘탈 심각하게 취약. 전반적 악화."
    return ModelScore(
        name="Piotroski F-Score",
        rawValue=float(score),
        displayValue=f"F = {score}/9",
        zone=zone,
        interpretation=interp,
        reference="Piotroski (2000), 9항목 바이너리, F>=7 강건",
    )


# ── 정량 축 점수 정규화 (0~100, 높을수록 위험) ──


def _normalizeOhlson(p: float) -> float:
    """Ohlson 부도확률 → 0~100 정규화 (높을수록 위험).

    Parameters
    ----------
    p : float
        부도 확률 (%).

    Returns
    -------
    float
        normalized : float — 정규화 점수 (0~100) (점)
    """
    return min(p, 100)


def _normalizeZpp(z: float) -> float:
    """Z''-Score → 0~100 정규화 (높을수록 위험).

    Parameters
    ----------
    z : float
        Z''-Score 값.

    Returns
    -------
    float
        normalized : float — 정규화 점수 (0~100) (점)
    """
    if z < 1.1:
        return 100
    if z > 2.6:
        return 0
    return (1 - (z - 1.1) / 1.5) * 100


def _normalizeZ(z: float) -> float:
    """Z-Score → 0~100 정규화 (높을수록 위험).

    Parameters
    ----------
    z : float
        Z-Score 값.

    Returns
    -------
    float
        normalized : float — 정규화 점수 (0~100) (점)
    """
    if z < 1.81:
        return 100
    if z > 2.99:
        return 0
    return (1 - (z - 1.81) / 1.18) * 100


def _normalizeBeneish(m: float) -> float:
    """Beneish M-Score → 0~100 정규화 (높을수록 위험).

    Parameters
    ----------
    m : float
        M-Score 값.

    Returns
    -------
    float
        normalized : float — 정규화 점수 (0~80) (점)
    """
    if m > -1.78:
        return 80
    if m > -2.22:
        return 50
    return max(0, 25 + (m + 2.22) * 10)


def _normalizeSloan(ratio: float) -> float:
    """Sloan Accrual Ratio → 0~100 정규화 (높을수록 위험).

    Parameters
    ----------
    ratio : float
        발생주의 이익 비율 (%).

    Returns
    -------
    float
        normalized : float — 정규화 점수 (0~80) (점)
    """
    abs_r = abs(ratio)
    if abs_r > 20:
        return 80
    if abs_r > 10:
        return 50
    return abs_r * 5


def _normalizeFScore(f: int) -> float:
    """Piotroski F-Score → 0~100 정규화 (높을수록 위험).

    Parameters
    ----------
    f : int
        F-Score (0~9) (점).

    Returns
    -------
    float
        normalized : float — 정규화 점수 (0~80) (점)
    """
    if f <= 2:
        return 80
    if f <= 4:
        return 50
    if f <= 6:
        return 25
    return 0


# ── Merton D2D 해석 ──


def _interpretMerton(result: dict) -> ModelScore:
    """Merton D2D → ModelScore. ``result`` 는 ``{"d2d", "pd", "converged"}`` 키를 가진 dict."""
    d2d = result["d2d"]
    if d2d > 4.0:
        zone, interp = "safe", "부도 거리 매우 충분. 시장이 평가하는 신용 건전성 우수."
    elif d2d > 2.0:
        zone, interp = "gray", "부도 거리 보통. 시장 변동성 확대 시 주의."
    elif d2d > 1.0:
        zone, interp = "distress", "부도 거리 부족. 자산가치가 부채에 근접."
    else:
        zone, interp = "distress", "부도 거리 극히 부족. 부도 임박 가능성."
    return ModelScore(
        name="Merton D2D",
        rawValue=round(d2d, 3),
        displayValue=f"D2D = {d2d:.2f}, PD = {result['pd']:.2f}%",
        zone=zone,
        interpretation=interp,
        reference="Merton (1974), 구조 모형. Moody's KMV 글로벌 표준.",
    )


def _interpretAuditRedFlags(flagCount: int, hasCritical: bool) -> ModelScore:
    """감사 Red Flag 수 → ModelScore."""
    if flagCount == 0:
        zone, interp = "safe", "감사 관련 Red Flag 없음."
    elif hasCritical:
        zone, interp = "distress", f"심각한 감사 Red Flag {flagCount}건. 부실 징후 가능."
    elif flagCount <= 2:
        zone, interp = "gray", f"감사 주의 신호 {flagCount}건. 모니터링 필요."
    else:
        zone, interp = "distress", f"감사 Red Flag {flagCount}건 누적. 회계 품질 점검 필요."
    return ModelScore(
        name="Audit Red Flags",
        rawValue=float(flagCount),
        displayValue=f"{flagCount}건" + (" (심각 포함)" if hasCritical else ""),
        zone=zone,
        interpretation=interp,
        reference="PCAOB AS 3101, ISA 570/701/705, SOX 302/404",
    )


def _normalizeMerton(d2d: float) -> float:
    """D2D → 0~100 (높을수록 위험). D2D>4→0, D2D<0.5→100."""
    if d2d > 4.0:
        return 0.0
    if d2d < 0.5:
        return 100.0
    return (1 - (d2d - 0.5) / 3.5) * 100


# ── 유동성 경보 ──
