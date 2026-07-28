"""HF 벌크 parquet 의 날짜 키 파싱.

``gov/prices/date/{YYYY}.parquet`` 과 ``gov/indices/date/{YYYY}.parquet`` 은 둘 다
연도로 샤딩돼 있고, 호출자가 넘기는 기간 인자는 ``YYYY-MM-DD`` / ``YYYYMMDD`` /
``date`` / ``YYYY`` 넉 중 아무 모양이나 온다. 그 모양을 ``date`` 하나로 좁히는 규칙은
가격 벌크와 지수 벌크가 같으므로 여기 한 자리에 둔다.
"""

from __future__ import annotations

from datetime import date as _date


def parseDateKey(value: str | _date) -> _date:
    """``YYYY-MM-DD`` / ``YYYYMMDD`` / ``YYYY`` / ``date`` 를 ``date`` 로 좁힌다.

    Capabilities:
        HF 벌크 호출자가 넘긴 기간 인자를 샤드 연도 계산에 쓸 ``date`` 로 정규화한다.

    AIContext:
        벌크 로더가 어느 연도 parquet 을 내려받을지 정하기 직전에 부른다. 인자
        모양이 사람 손으로 온 문자열이라 여기서 한 번 좁히고 그 뒤로는 ``date`` 만 돈다.

    Guide:
        연도만 온 ``"2024"`` 는 그 해 1월 1일로 읽는다. 하이픈은 지우고 앞 여덟 자리만
        본다. 알아볼 수 없으면 조용히 대체값을 만들지 않고 ``ValueError`` 로 끝낸다.

    When:
        ``loadFiltered`` 계열이 ``start`` / ``end`` 를 받아 연도 목록을 만들 때.

    How:
        ``date`` 면 그대로 돌려주고, 아니면 문자열로 바꿔 하이픈을 지운 뒤 길이로 분기한다.

    Requires:
        없음. 순수 함수라 네트워크도 캐시도 보지 않는다.

    Args:
        value: 기간 인자. ``date`` 이거나 ``YYYY-MM-DD`` / ``YYYYMMDD`` / ``YYYY`` 문자열.

    Returns:
        ``datetime.date``. 연도만 온 입력은 그 해 1월 1일.

    Raises:
        ValueError: 여덟 자리도 네 자리도 아니거나 숫자가 아닐 때.

    Example:
        >>> parseDateKey("2024-03-05")
        datetime.date(2024, 3, 5)
        >>> parseDateKey("2024")
        datetime.date(2024, 1, 1)

    SeeAlso:
        ``dartlab.gather.bulkData.hfBulk`` . KR 가격 벌크.
        ``dartlab.gather.bulkData.hfIndexBulk`` . KR 지수 벌크.
    """
    if isinstance(value, _date):
        return value
    s = str(value).replace("-", "").strip()
    if len(s) >= 8:
        return _date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    if len(s) == 4:
        return _date(int(s), 1, 1)
    raise ValueError(f"날짜 포맷 오류: {value!r}")
