"""요청 사이 최소 간격을 지키는 대기 원시.

"마지막 요청 이후 ``minInterval`` 이 지날 때까지 기다린다" 는 같은 규칙을 gather 의
비동기 수집 클라이언트(DART·EDGAR 배치)와 gather·providers 의 동기 클라이언트가 함께
쓴다. gather 와 providers 는 같은 L1 형제라 서로 import 하지 못하므로 공용 자리는
L0 core 다.

동기 경로는 ``time.monotonic``, 비동기 경로는 이벤트 루프 시계를 읽는다. 시계가 다르고
동기 쪽은 호출자가 마지막 요청 시각을 따로 갱신하므로 한 함수로 합치지 않는다.
"""

from __future__ import annotations

import asyncio
import time


def waitMinInterval(lastRequestAt: float, minInterval: float) -> None:
    """마지막 요청 이후 최소 간격이 지날 때까지 현재 스레드를 재운다.

    Args:
        lastRequestAt: 마지막 요청 시각. ``time.monotonic`` 기준 초.
        minInterval: 두 요청 사이 최소 간격 (초). 0 이하면 대기 없이 즉시 반환한다.

    Returns:
        None. 마지막 요청 시각 갱신은 호출자 몫이다. 응답을 받은 시각을 기록할지
        요청을 보낸 시각을 기록할지가 클라이언트마다 다르기 때문이다.

    Raises:
        없음.

    Example:
        >>> waitMinInterval(0.0, 0.0)

    Requires:
        호출자가 ``time.monotonic`` 으로 잰 마지막 요청 시각을 들고 있어야 한다.

    SeeAlso:
        ``awaitMinInterval`` . 같은 규칙의 asyncio 판.
    """
    if minInterval <= 0:
        return
    now = time.monotonic()
    elapsed = now - lastRequestAt
    if elapsed < minInterval:
        time.sleep(minInterval - elapsed)


async def awaitMinInterval(lastRequest: float, minInterval: float) -> float:
    """마지막 요청 이후 최소 간격이 지날 때까지 이벤트 루프를 양보하고 새 시각을 돌려준다.

    Args:
        lastRequest: 마지막 요청 시각. 이벤트 루프 시계 기준 초.
        minInterval: 두 요청 사이 최소 간격 (초).

    Returns:
        float. 대기 후 다시 읽은 이벤트 루프 시각. 호출자가 그대로 자기
        마지막 요청 시각에 넣는다.

    Raises:
        없음.

    Example:
        >>> import asyncio
        >>> asyncio.run(awaitMinInterval(0.0, 0.0)) >= 0.0
        True

    Requires:
        실행 중인 이벤트 루프.

    SeeAlso:
        ``waitMinInterval`` . 같은 규칙의 동기 판.
    """
    now = asyncio.get_event_loop().time()
    elapsed = now - lastRequest
    if elapsed < minInterval:
        await asyncio.sleep(minInterval - elapsed)
    return asyncio.get_event_loop().time()
