"""알파 팩터가 공유하는 횡단면 변환.

알파는 전종목을 한 시점에 줄 세워 비교하는 것이라, 원값을 그대로 쓰지 않고 순위나 표준화된
점수로 바꾼 뒤 합친다. 그 변환은 팩터마다 다르지 않으므로 여기 한 번만 적는다.

예전에는 백분위 순위가 qFactor, qmj, fundamentalMomentum 세 파일에 글자까지 똑같이 복사돼
있었다. 팩터를 하나 더 붙일 때 옆 파일에서 복사하게 되고, 그러다 한 곳만 tie 처리나 결측
처리를 바꾸면 같은 유니버스에서 팩터마다 다른 줄 세우기가 된다.
"""

from __future__ import annotations

import numpy as np


def percentileRank(values: list[float]) -> list[float]:
    """값 목록을 0~1 백분위 순위로 바꾼다. 작을수록 0 에 가깝다.

    Args:
        values: 같은 시점 전종목의 팩터 원값. 길이 1 이면 전부 0.0 이다.

    Returns:
        입력과 같은 순서, 같은 길이의 백분위 목록.

    Raises:
        없음.

    Example:
        ``percentileRank([10.0, 30.0, 20.0])`` 은 ``[0.0, 1.0, 0.5]``.
    """
    arr = np.asarray(values, dtype=np.float64)
    ranks = np.full(len(arr), np.nan, dtype=np.float64)
    finiteIndices = np.flatnonzero(np.isfinite(arr))
    if finiteIndices.size == 0:
        return list(ranks)
    if finiteIndices.size == 1:
        ranks[finiteIndices[0]] = 0.0
        return list(ranks)

    finiteValues = arr[finiteIndices]
    order = np.argsort(finiteValues, kind="mergesort")
    sortedValues = finiteValues[order]
    sortedRanks = np.empty(finiteIndices.size, dtype=np.float64)
    start = 0
    while start < finiteIndices.size:
        end = start + 1
        while end < finiteIndices.size and sortedValues[end] == sortedValues[start]:
            end += 1
        averageRank = (start + end - 1) / 2.0
        sortedRanks[start:end] = averageRank
        start = end
    finiteRanks = np.empty(finiteIndices.size, dtype=np.float64)
    finiteRanks[order] = sortedRanks / (finiteIndices.size - 1)
    ranks[finiteIndices] = finiteRanks
    return list(ranks)


__all__ = ["percentileRank"]
