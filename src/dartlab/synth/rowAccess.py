"""행 접근과 수치 강제변환 primitive SSOT. rowsOf, firstValue, toFloat, safeDiv.

L1.5 synth 본체. 엔진 결과는 polars DataFrame, dict 목록, 단일 dict 중 아무 모양으로나 온다.
그것을 dict 목록 하나로 펴고, 대소문자가 흔들리는 key 에서 값을 꺼내고, 무엇이 들어오든
float 아니면 None 으로 좁히는 네 가지가 여러 판독기에 흩어져 있었다. eventRadar 와
thesisKillChain 과 evidenceForensics 가 같은 본문을 각자 갖고 있었고, 한쪽만 고치면 같은
자료를 읽는 두 판독기가 서로 다른 답을 냈다.

수치 규약:
- 나눗셈은 분모가 None 또는 0 이면 None. 예외를 던지지 않는다.
- NaN 은 float 이 아니라 None 으로 본다 (`number != number`).
- 강제변환 실패도 None. 어느 쪽인지 구분이 필요하면 부르는 쪽이 미리 검사한다.

`stats.py` 와 형제다. 그쪽은 numpy 배열 통계, 이쪽은 행과 스칼라 접근이다.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import polars as pl


def rowsOf(data: Iterable[Mapping[str, Any]] | pl.DataFrame | Mapping[str, Any] | None) -> list[dict[str, Any]]:
    """무슨 모양으로 오든 dict 목록 하나로 편다.

    Args:
        data: DataFrame, dict 목록, 단일 dict, None 중 하나.

    Returns:
        dict 목록. 읽을 것이 없으면 빈 목록.
    """
    if data is None:
        return []
    if isinstance(data, pl.DataFrame):
        return [dict(row) for row in data.to_dicts()]
    if isinstance(data, Mapping):
        return [dict(data)]
    if isinstance(data, str):
        return []
    rows: list[dict[str, Any]] = []
    for item in data:
        if isinstance(item, Mapping):
            rows.append(dict(item))
    return rows


def firstValue(row: Mapping[str, Any], *keys: str) -> Any:
    """주어진 key 를 차례로 보며 처음 나오는 None 아닌 값을 준다.

    엔진마다 같은 뜻을 rcept_dt, filedAt, publishedAt 처럼 다르게 부르고 대소문자도
    흔들린다. 정확히 일치하는 key 를 먼저 보고, 없으면 소문자로 맞춰 다시 본다.

    Args:
        row: 읽을 행.
        keys: 우선순위 순서의 key 이름들.

    Returns:
        처음 찾은 값. 전부 없거나 None 이면 None.
    """
    lowered = {str(key).lower(): key for key in row}
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
        actual = lowered.get(key.lower())
        if actual is not None and row[actual] is not None:
            return row[actual]
    return None


def latestDate(items: Iterable[Any], *, keys: Sequence[str]) -> str | None:
    """행 또는 행 목록들을 훑어 가장 늦은 날짜 문자열을 준다.

    날짜 key 이름은 판독기마다 다르므로 부르는 쪽이 준다. 행이 아닌 것과 빈 문자열은
    조용히 건너뛴다. 없는 날짜와 못 읽은 날짜를 구분할 방법이 원래부터 없다.

    Args:
        items: 행 목록 또는 단일 행이 섞여 들어올 수 있는 나열.
        keys: 날짜로 볼 key 이름들. 우선순위 순서.

    Returns:
        문자열 비교로 가장 큰 날짜. 하나도 없으면 None.
    """
    dates: list[str] = []
    for item in items:
        rows = item if isinstance(item, list) else [item]
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            value = firstValue(row, *keys)
            if value is None:
                continue
            text = str(value)
            if text:
                dates.append(text)
    return max(dates) if dates else None


def evidenceSummary(rows: list[dict[str, Any]]) -> str:
    """행들에서 근거 문구를 찾아 한 줄로 준다. 없으면 어떤 열이 있었는지라도 말한다.

    Args:
        rows: 근거를 찾을 행 목록.

    Returns:
        처음 만난 근거 문구. 행이 없으면 "no rows", 근거 열이 비어 있으면 열 이름 나열.
    """
    if not rows:
        return "no rows"
    for row in rows:
        if row.get("evidence"):
            return str(row["evidence"])
    return ", ".join(rows[0].keys())


def toFloat(value: Any) -> float | None:
    """무엇이 오든 float 아니면 None 으로 좁힌다. NaN 도 None 이다."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return number


def safeDiv(numerator: float | None, denominator: float | None) -> float | None:
    """분모가 None 이거나 0 이면 None. 그 밖에는 나눈 값."""
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def diff(left: float | None, right: float | None) -> float | None:
    """한쪽이라도 None 이면 None. 그 밖에는 뺀 값."""
    if left is None or right is None:
        return None
    return left - right


def pctChange(current: float | None, previous: float | None) -> float | None:
    """직전 대비 변화율. 직전이 None 이거나 0 이면 None."""
    if current is None or previous in (None, 0):
        return None
    return (current - previous) / abs(previous)
