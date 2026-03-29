"""순수 Python OLS 회귀 + 통계 유틸리티.

외부 의존성 없음. analysis/ 계층이 아닌 core/ 계층 소속.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def ols(x: list[float], y: list[float]) -> tuple[float, float, float]:
    """단순 선형 회귀 (OLS)."""
    n = len(x)
    if n < 2:
        return 0.0, 0.0, 0.0

    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi**2 for xi in x)

    denom = n * sum_x2 - sum_x**2
    if abs(denom) < 1e-12:
        return 0.0, sum_y / n, 0.0

    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n

    mean_y = sum_y / n
    ss_tot = sum((yi - mean_y) ** 2 for yi in y)
    ss_res = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))

    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return slope, intercept, max(0.0, r_squared)


@dataclass
class MultiOlsResult:
    """다변량 OLS 결과."""

    coefficients: list[float]  # [intercept, b1, b2, ...]
    rSquared: float
    adjRSquared: float
    residuals: list[float]
    standardErrors: list[float]
    tStats: list[float]
    nObs: int
    nFeatures: int


def olsMulti(
    X: list[list[float]],
    y: list[float],
    *,
    addIntercept: bool = True,
) -> MultiOlsResult | None:
    """다변량 OLS -- 순수 Python, (X'X)^-1 X'y.

    Parameters
    ----------
    X : 행 = 관측치, 열 = 독립변수
    y : 종속변수
    addIntercept : True이면 절편 열(1) 자동 추가

    Returns
    -------
    MultiOlsResult | None -- 데이터 부족/특이행렬이면 None
    """
    n = len(y)
    if n < 2 or len(X) != n:
        return None

    k0 = len(X[0]) if X else 0
    if k0 == 0:
        return None

    # 절편 열 추가
    if addIntercept:
        Xa = [[1.0] + row for row in X]
    else:
        Xa = [list(row) for row in X]

    k = len(Xa[0])  # 총 변수 수 (절편 포함)
    if n <= k:
        return None

    # X'X 계산
    xtx = [[0.0] * k for _ in range(k)]
    for row in Xa:
        for i in range(k):
            for j in range(i, k):
                v = row[i] * row[j]
                xtx[i][j] += v
                if i != j:
                    xtx[j][i] += v

    # X'y 계산
    xty = [0.0] * k
    for idx in range(n):
        for j in range(k):
            xty[j] += Xa[idx][j] * y[idx]

    # (X'X)^-1 via Gauss-Jordan
    inv = invertMatrix(xtx)
    if inv is None:
        return None

    # b = (X'X)^-1 X'y
    coeffs = [0.0] * k
    for i in range(k):
        for j in range(k):
            coeffs[i] += inv[i][j] * xty[j]

    # 잔차, R-squared
    meanY = sum(y) / n
    ssTot = sum((yi - meanY) ** 2 for yi in y)
    residuals = []
    ssRes = 0.0
    for idx in range(n):
        pred = sum(coeffs[j] * Xa[idx][j] for j in range(k))
        r = y[idx] - pred
        residuals.append(r)
        ssRes += r * r

    rSq = 1 - ssRes / ssTot if ssTot > 1e-15 else 0.0
    rSq = max(0.0, rSq)
    adjRSq = 1 - (1 - rSq) * (n - 1) / (n - k) if n > k else 0.0

    # 표준오차, t-통계량
    mse = ssRes / (n - k) if n > k else 0.0
    se = []
    tStats = []
    for i in range(k):
        vari = inv[i][i] * mse
        sei = math.sqrt(max(vari, 0.0))
        se.append(sei)
        tStats.append(coeffs[i] / sei if sei > 1e-15 else 0.0)

    return MultiOlsResult(
        coefficients=coeffs,
        rSquared=rSq,
        adjRSquared=adjRSq,
        residuals=residuals,
        standardErrors=se,
        tStats=tStats,
        nObs=n,
        nFeatures=k0,
    )


def invertMatrix(m: list[list[float]]) -> list[list[float]] | None:
    """Gauss-Jordan 역행렬 (순수 Python)."""
    n = len(m)
    # augmented [M | I]
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(m)]

    for col in range(n):
        # 피벗 선택 (부분 피벗)
        maxVal = abs(aug[col][col])
        maxRow = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > maxVal:
                maxVal = abs(aug[row][col])
                maxRow = row
        if maxVal < 1e-12:
            return None  # 특이행렬
        if maxRow != col:
            aug[col], aug[maxRow] = aug[maxRow], aug[col]

        pivot = aug[col][col]
        for j in range(2 * n):
            aug[col][j] /= pivot

        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            for j in range(2 * n):
                aug[row][j] -= factor * aug[col][j]

    return [row[n:] for row in aug]


def detectStructuralBreak(vals: list[float], minSegment: int = 4) -> int | None:
    """Chow Test 기반 구조적 변화점 감지."""
    n = len(vals)
    if n < minSegment * 2:
        return None

    xAll = list(range(n))
    _, _, r2Full = ols([float(x) for x in xAll], vals)
    meanY = sum(vals) / n
    ssTot = sum((v - meanY) ** 2 for v in vals)
    ssrFull = ssTot * (1 - r2Full) if ssTot > 0 else 0

    bestBreak: int | None = None
    bestF = 0.0
    k = 2

    for bp in range(minSegment, n - minSegment + 1):
        x1 = [float(i) for i in range(bp)]
        y1 = vals[:bp]
        x2 = [float(i) for i in range(bp, n)]
        y2 = vals[bp:]

        _, _, r21 = ols(x1, y1)
        _, _, r22 = ols(x2, y2)

        ssTot1 = sum((v - sum(y1) / len(y1)) ** 2 for v in y1) if len(y1) > 0 else 0
        ssTot2 = sum((v - sum(y2) / len(y2)) ** 2 for v in y2) if len(y2) > 0 else 0

        ssr1 = ssTot1 * (1 - r21) if ssTot1 > 0 else 0
        ssr2 = ssTot2 * (1 - r22) if ssTot2 > 0 else 0

        ssrSplit = ssr1 + ssr2
        denom = ssrSplit / max(n - 2 * k, 1)
        if denom < 1e-12:
            continue

        fStat = ((ssrFull - ssrSplit) / k) / denom

        if fStat > bestF:
            bestF = fStat
            bestBreak = bp

    df = max(n - 2 * k, 1)
    fCritical = 3.0 + max(0, 10 - df) * 0.3

    if bestF > fCritical and bestBreak is not None:
        return bestBreak
    return None


def coefficientOfVariation(values: list[float]) -> float:
    """변동계수 (CV = stdev / |mean|)."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    if abs(mean) < 1e-12:
        return float("inf")
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance) / abs(mean)


# 하위호환 alias (기존 코드에서 _ prefix로 사용)
_ols = ols
_olsMulti = olsMulti
_invertMatrix = invertMatrix
_detectStructuralBreak = detectStructuralBreak
_coefficientOfVariation = coefficientOfVariation
