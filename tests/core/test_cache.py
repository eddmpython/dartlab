"""L0 시계열 TTL 캐시 회귀.

`core/cache.py` 는 테스트 참조 0 이었다. 캐시는 틀려도 값을 돌려주기 때문에 결함이
예외가 아니라 잘못된 숫자로 나타난다. 키가 서로 다른 호출을 같은 칸에 넣으면 A 회사
질의가 B 회사 답을 받고, 만료 판정이 어긋나면 지난 값이 최신으로 읽힌다.

여기서 고정하는 것은 키 분리, 만료, 두 단계 TTL 셋이다.
"""

from __future__ import annotations

import time

import pytest

from dartlab.core.cache import TimeseriesCache, makeKey


def testKeyIsStableForTheSameArguments() -> None:
    """같은 인자는 같은 키다. 흔들리면 캐시가 아예 맞지 않는다."""

    assert makeKey("fred", "GDP", 2026) == makeKey("fred", "GDP", 2026)


def testKeySeparatesDifferentArguments() -> None:
    """다른 질의는 다른 칸이어야 한다. 겹치면 남의 답을 받는다."""

    assert makeKey("fred", "GDP") != makeKey("fred", "CPI")
    assert makeKey("fred", "GDP") != makeKey("ecos", "GDP")


def testKeySeparatesArgumentBoundaries() -> None:
    """인자 경계가 사라지면 서로 다른 조합이 같은 키가 된다.

    구분자 없이 이어붙이면 ("ab", "c") 와 ("a", "bc") 가 충돌한다.
    """

    assert makeKey("ab", "c") != makeKey("a", "bc")


def testCacheReturnsWhatWasStored() -> None:
    """넣은 값을 그대로 돌려준다."""

    cache = TimeseriesCache(ttlDaily=60, ttlOther=60)
    cache.put({"value": 1}, "series", "A")

    assert cache.get("series", "A") == {"value": 1}


def testCacheMissReturnsNoneNotAnEmptyValue() -> None:
    """없는 키는 None 이다. 빈 값을 돌려주면 미조회와 빈 결과가 섞인다."""

    cache = TimeseriesCache(ttlDaily=60, ttlOther=60)

    assert cache.get("series", "없음") is None


def testDifferentKeysDoNotShareOneSlot() -> None:
    """서로 다른 질의가 같은 칸을 쓰면 답이 뒤바뀐다."""

    cache = TimeseriesCache(ttlDaily=60, ttlOther=60)
    cache.put("삼성", "company", "005930")
    cache.put("현대", "company", "005380")

    assert cache.get("company", "005930") == "삼성"
    assert cache.get("company", "005380") == "현대"


def testExpiredEntryIsTreatedAsAbsent() -> None:
    """만료된 값은 없는 것으로 본다. 남아 있으면 지난 값이 최신으로 읽힌다."""

    cache = TimeseriesCache(ttlDaily=60, ttlOther=0)
    cache.put("낡음", "series", "A")
    time.sleep(0.01)

    assert cache.get("series", "A") is None


def testDailyEntriesUseTheDailyTtl() -> None:
    """일간 자료는 더 긴 TTL 을 쓴다. 두 단계가 뒤바뀌면 잦은 재조회나 낡은 값이 된다."""

    cache = TimeseriesCache(ttlDaily=60, ttlOther=0)
    cache.put("일간", "series", "A", daily=True)
    cache.put("기타", "series", "B", daily=False)
    time.sleep(0.01)

    assert cache.get("series", "A") == "일간"
    assert cache.get("series", "B") is None


def testClearRemovesEverything() -> None:
    """비우면 전부 사라진다. 일부가 남으면 갱신 후에도 옛 값이 나온다."""

    cache = TimeseriesCache(ttlDaily=60, ttlOther=60)
    cache.put(1, "a")
    cache.put(2, "b")
    cache.clear()

    assert cache.get("a") is None
    assert cache.get("b") is None


def testStoringFalsyValuesStillCountsAsAHit() -> None:
    """0 이나 빈 목록도 값이다. 거짓으로 보고 미스 처리하면 매번 다시 조회한다."""

    cache = TimeseriesCache(ttlDaily=60, ttlOther=60)
    cache.put(0, "zero")
    cache.put([], "empty")

    assert cache.get("zero") == 0
    assert cache.get("empty") == []


def testOverwritingAKeyReplacesTheValue() -> None:
    """같은 키에 다시 넣으면 최신 값이 이긴다."""

    cache = TimeseriesCache(ttlDaily=60, ttlOther=60)
    cache.put("옛값", "series", "A")
    cache.put("새값", "series", "A")

    assert cache.get("series", "A") == "새값"


def testCacheIsBoundedSoItCannotGrowWithoutLimit() -> None:
    """상한이 없으면 장기 실행에서 메모리가 계속 는다."""

    cache = TimeseriesCache(ttlDaily=60, ttlOther=60, maxEntries=4)
    for index in range(20):
        cache.put(index, "series", index)

    alive = sum(1 for index in range(20) if cache.get("series", index) is not None)

    assert alive <= 4


@pytest.mark.parametrize("parts", [("a",), ("a", "b"), ("a", 1, None), (1.5, True)])
def testKeyIsAlwaysAHexDigest(parts: tuple[object, ...]) -> None:
    """키는 길이가 일정한 hex 여야 저장소가 예측 가능하다."""

    key = makeKey(*parts)

    assert len(key) == 32
    assert all(character in "0123456789abcdef" for character in key)
