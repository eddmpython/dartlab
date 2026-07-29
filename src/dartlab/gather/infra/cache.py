"""Gather 엔진 TTL 캐시 — 데이터 유형별 만료 + LRU 축출."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass

# hit/miss/evict 카운터 record (telemetry SSOT, A 트랙 O1)
from .telemetry import recordCacheEvict, recordCacheHit, recordCacheMiss

# TTL 상수 — `infra.ttl` SSOT 에서 import (G+ P-Q4, env override 가능)
from .ttl import (
    TTL_DEFAULT,
    TTL_DIVIDENDS,
    TTL_FLOW,
    TTL_HISTORY,
    TTL_INDEX_MEMBERS,
    TTL_INSIDER,
    TTL_MACRO,
    TTL_MAJOR_HOLDER,
    TTL_MARKET_CAP,
    TTL_NEWS,
    TTL_OWNERSHIP,
    TTL_PRICE,
    TTL_SECTOR,
    TTL_SHORT_SELLING,
    TTL_SNAPSHOT,
    TTL_SPLITS,
)

# 데이터 유형 → TTL 매핑
_TTL_MAP: dict[str, int] = {
    "price": TTL_PRICE,
    "flow": TTL_FLOW,
    "sector_per": TTL_SECTOR,
    "sector_info": TTL_SECTOR,
    "history": TTL_HISTORY,
    "snapshot": TTL_SNAPSHOT,
    "news": TTL_NEWS,
    "dividends": TTL_DIVIDENDS,
    "splits": TTL_SPLITS,
    "macro": TTL_MACRO,
    "short_selling": TTL_SHORT_SELLING,
    "insider": TTL_INSIDER,
    "major_holder": TTL_MAJOR_HOLDER,
    "index_members": TTL_INDEX_MEMBERS,
    "market_cap": TTL_MARKET_CAP,
    "ownership": TTL_OWNERSHIP,
}


def buildCacheSlot(dataType: str, **dimensions: object) -> str:
    """데이터 종류와 결과를 바꾸는 인자를 정규화한 캐시 슬롯을 만든다.

    Capabilities:
        같은 요청은 같은 문자열 키가 되도록 차원 이름을 정렬하고 시장 코드를 대문자로 맞춘다.

    AIContext:
        gather 도구가 요청 차원을 누락해 다른 결과를 같은 캐시에 섞지 않도록 식별자를 만든다.

    Guide:
        결과를 바꾸는 모든 인자를 ``dimensions`` 로 넘기고, 관측 목적 인자는 제외한다.

    When:
        종목·시장·기간처럼 복합 차원을 가진 수집 결과를 캐시에 저장하거나 조회할 때 사용한다.

    How:
        데이터 종류 뒤에 정렬된 ``name=value`` 차원을 결합하고 ``None`` 차원은 생략한다.

    Args:
        dataType: ``history`` 같은 데이터 종류.
        **dimensions: 결과를 구분하는 이름 있는 차원.

    Returns:
        결정적으로 정규화된 캐시 슬롯 문자열.

    Requires:
        없음.

    Raises:
        ValueError: ``dataType`` 이 비어 있는 경우.

    Example:
        >>> buildCacheSlot("history", market="kr", start="2026-01-01")
        'history|market=KR|start=2026-01-01'

    SeeAlso:
        ``GatherCache.getTyped`` 와 ``GatherCache.putTyped`` 가 이 슬롯을 소비한다.
    """
    base = str(dataType).strip()
    if not base:
        raise ValueError("dataType은 비어 있을 수 없습니다")
    parts = [base]
    for name in sorted(dimensions):
        value = dimensions[name]
        if value is None:
            continue
        normalized = str(value).strip()
        if name == "market":
            normalized = normalized.upper()
        parts.append(f"{name}={normalized}")
    return "|".join(parts)


@dataclass(slots=True)
class _CacheEntry:
    value: object
    expires_at: float


class GatherCache:
    """TTL 기반 LRU 캐시 — thread-safe + 용량 제한.

    - 데이터 유형별 TTL 자동 적용
    - max_entries 초과 시 가장 오래된 항목 축출
    - 종목별 일괄 무효화 지원
    - stale-while-revalidate: 만료 데이터를 별도 보관하여 최후 fallback 제공
    """

    def __init__(self, maxEntries: int = 200) -> None:
        self._store: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._stale: dict[str, object] = {}  # 만료 시 마지막 값 보존
        self._max = maxEntries
        self._stale_max = maxEntries  # stale도 용량 제한
        self._lock = threading.Lock()

    def get(self, key: str) -> object | None:
        """캐시 조회 — 만료되었으면 stale로 이동 후 None 반환.

        Capabilities: thread-safe LRU + TTL 만료 자동 stale 이전 + hit/miss telemetry.
        AIContext: gather mixin (price/flow/...) 의 cache hit 단일 진입점.
        Guide: 만료된 데이터는 _stale 보관 — getStale 로 fallback.
        When: gather mixin 메서드의 첫 단계.
        How: lock → store lookup → TTL 비교 → telemetry record.

        Parameters
        ----------
        key : str
            캐시 키 (예: "005930:price").

        Returns
        -------
        object | None
            캐시된 값 — 유효한 항목이 있을 때.
            None — 키가 없거나 TTL 만료 시 (만료 데이터는 stale로 이동).

        Raises
        ------
        없음.

        Requires
        --------
        ``self._lock`` (threading.Lock) + ``self._store`` OrderedDict.

        Example
        -------
        >>> v = cache.get("005930:price")

        See Also
        --------
        getStale : 만료 데이터 fallback.
        put · getTyped : 동행 인터페이스.
        """
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                isHit = False
            elif time.monotonic() > entry.expires_at:
                # stale store에 보존 후 live에서 제거
                self._stale[key] = entry.value
                del self._store[key]
                self._trimStale()
                isHit = False
            else:
                self._store.move_to_end(key)
                value = entry.value
                isHit = True
        if isHit:
            recordCacheHit()
            return value
        recordCacheMiss()
        return None

    def put(self, key: str, value: object, ttl: int = TTL_DEFAULT) -> None:
        """캐시 저장 — max_entries 초과 시 가장 오래된 항목 LRU 축출.

        Capabilities: thread-safe write + LRU 축출 + evict telemetry.
        AIContext: gather mixin 의 fetch 직후 cache 저장 진입.
        Guide: 기존 키 덮어쓰기 + stale 제거.
        When: 가격/수급 fetch 직후 cache 저장 시.
        How: lock → 기존 key 제거 → store insert → max 초과 시 popitem(last=False).

        Parameters
        ----------
        key : str
            캐시 키 (예: "005930:price").
        value : object
            저장할 데이터.
        ttl : int
            만료 시간 (초). 기본 TTL_DEFAULT (3600초).

        Returns
        -------
        None
            기존 키가 있으면 덮어쓰고, stale 항목도 제거한다.

        Raises
        ------
        없음.

        Requires
        --------
        ``self._lock`` + ``self._store`` + ``self._max``.

        Example
        -------
        >>> cache.put("005930:price", snap, ttl=300)

        See Also
        --------
        putTyped : 데이터 유형별 TTL 자동.
        get : 동행 read.
        """
        evictCount = 0
        with self._lock:
            if key in self._store:
                del self._store[key]
            self._stale.pop(key, None)  # 새 값 → stale 제거
            self._store[key] = _CacheEntry(
                value=value,
                expires_at=time.monotonic() + ttl,
            )
            while len(self._store) > self._max:
                self._store.popitem(last=False)
                evictCount += 1
        for _ in range(evictCount):
            recordCacheEvict()

    def _trimStale(self) -> None:
        """stale store 용량 제한 — 삽입순으로 가장 오래된 항목부터 제거 (lock 내에서 호출).

        Returns
        -------
        None
            stale_max 초과분만큼 가장 오래된 항목을 삭제한다.
        """
        while len(self._stale) > self._stale_max:
            # dict는 삽입순 — 가장 오래된 것 제거
            first_key = next(iter(self._stale))
            del self._stale[first_key]

    def getStale(self, key: str) -> object | None:
        """만료된 데이터 반환 — stale-while-revalidate 패턴의 최후 fallback.

        Capabilities: ``self._stale[key]`` lookup — TTL 만료 후 보존된 마지막 값.
        AIContext: 외부 API 모두 실패 시 stale 데이터로 graceful degradation 진입.
        Guide: TTL 만료 = 신선도 떨어짐 (사용자 표시 시 warning 권장).
        When: fetch 모든 source 실패 후 캐시 stale fallback 필요 시.
        How: ``with self._lock: return self._stale.get(key)``.

        Parameters
        ----------
        key : str
            캐시 키 (예: "005930:price").

        Returns
        -------
        object | None
            만료 후 보존된 마지막 값.
            None — stale 항목이 없을 때.

        Raises
        ------
        없음.

        Requires
        --------
        ``self._stale`` dict + ``self._lock``.

        Example
        -------
        >>> stale = cache.getStale("005930:price")

        See Also
        --------
        getTyped(allowStale=True) : 통합 인터페이스.
        get : live 항목 read.
        """
        with self._lock:
            return self._stale.get(key)

    def getTyped(self, stockCode: str, dataType: str, *, allowStale: bool = False) -> object | None:
        """데이터 유형별 캐시 조회 — "{stock_code}:{data_type}" 키로 자동 조합.

        Capabilities: stockCode + dataType → 키 조합 + get + (선택) getStale fallback.
        AIContext: gather mixin 의 사용자-friendly cache 진입 — 키 조합 자동.
        Guide: allowStale=True 시 외부 API 실패 graceful — 사용자에게 warning 표시 책임.
        When: gather mixin (price/flow/sector/...) 의 첫 단계.
        How: ``key = f'{stockCode}:{dataType}'`` → get → allowStale 시 getStale fallback.

        Parameters
        ----------
        stock_code : str
            종목코드 또는 캐시 prefix ("005930", "KR:005930" 등).
        data_type : str
            데이터 유형 ("price", "flow", "snapshot" 등).
        allow_stale : bool
            True이면 live 미스 시 만료 데이터도 반환. 기본 False.

        Returns
        -------
        object | None
            캐시된 값 (PriceSnapshot, ConsensusData, pl.DataFrame 등).
            None — 캐시 미스이고 allow_stale=False이거나 stale도 없을 때.

        Raises
        ------
        없음.

        Requires
        --------
        get / getStale 인터페이스.

        Example
        -------
        >>> snap = cache.getTyped("005930", "price")

        See Also
        --------
        putTyped : 동행 write.
        get · getStale : 위임 대상.
        """
        key = f"{stockCode}:{dataType}"
        result = self.get(key)
        if result is not None:
            return result
        if allowStale:
            return self.getStale(key)
        return None

    def putTyped(self, stockCode: str, dataType: str, value: object) -> None:
        """데이터 유형에 맞는 TTL로 저장 — _TTL_MAP에서 자동 매핑.

        Capabilities: stockCode + dataType → 키 + _TTL_MAP TTL 자동 + put 위임.
        AIContext: gather mixin 의 cache write — 데이터 유형별 TTL 자동.
        Guide: dataType 미등록 시 TTL_DEFAULT (3600s).
        When: fetch 직후 cache 저장 시.
        How: ``_TTL_MAP.get(dataType, TTL_DEFAULT)`` → ``self.put(key, value, ttl)``.

        Parameters
        ----------
        stock_code : str
            종목코드 또는 캐시 prefix.
        data_type : str
            데이터 유형 ("price", "flow" 등). _TTL_MAP에 없으면 TTL_DEFAULT (3600초).
        value : object
            저장할 데이터.

        Returns
        -------
        None
            "{stock_code}:{data_type}" 키로 적절한 TTL과 함께 저장한다.

        Raises
        ------
        없음.

        Requires
        --------
        ``_TTL_MAP`` + ``self.put`` 가용.

        Example
        -------
        >>> cache.putTyped("005930", "price", snap)

        See Also
        --------
        getTyped : 동행 read.
        put : 위임 대상.
        """
        ttl = _TTL_MAP.get(dataType.partition("|")[0], TTL_DEFAULT)
        self.put(f"{stockCode}:{dataType}", value, ttl)

    def invalidate(self, stockCode: str) -> None:
        """특정 종목의 모든 캐시 제거 — live + stale 양쪽에서 prefix 매칭 삭제.

        Capabilities: stockCode prefix 매칭 키 모두 store + stale 에서 삭제.
        AIContext: 사용자 신선 데이터 강제 / live 가격 갱신 진입.
        Guide: 종목 한정 — 전체 invalidate 는 clear().
        When: gather.invalidate(stockCode) 사용자 호출 시.
        How: lock → store + stale prefix match → 키 삭제.

        Parameters
        ----------
        stock_code : str
            종목코드 ("005930"). "{stock_code}:" prefix로 시작하는 모든 키를 제거.

        Returns
        -------
        None
            해당 종목의 price, flow 등 모든 데이터 유형 캐시를 삭제한다.

        Raises
        ------
        없음.

        Requires
        --------
        ``self._lock`` + ``self._store`` + ``self._stale``.

        Example
        -------
        >>> cache.invalidate("005930")

        See Also
        --------
        clear : 전체 캐시 비우기.
        engine.Gather.invalidate : 본 메서드 caller.
        """
        with self._lock:
            prefix = f"{stockCode}:"
            for store in (self._store, self._stale):
                keys = [k for k in store if k.startswith(prefix)]
                for k in keys:
                    del store[k]

    def clear(self) -> None:
        """전체 캐시 초기화 — live + stale 모두 비운다.

        Capabilities: store + stale dict 모두 비움.
        AIContext: 테스트 fixture / dartlab 종료 시 진입.
        Guide: invalidate(stockCode) 와 다름 — 모든 종목 영향.
        When: 테스트 setup/teardown / 메모리 회수 시.
        How: lock → ``self._store.clear()`` + ``self._stale.clear()``.

        Returns
        -------
        None
            모든 캐시 항목을 제거한다. size가 0이 된다.

        Raises
        ------
        없음.

        Requires
        --------
        ``self._lock`` + ``self._store`` + ``self._stale``.

        Example
        -------
        >>> cache.clear()

        See Also
        --------
        invalidate : 종목 단위 제거.
        """
        with self._lock:
            self._store.clear()
            self._stale.clear()

    @property
    def size(self) -> int:
        """캐시에 저장된 live 항목 수 (stale 제외).

        Capabilities: ``len(self._store)`` — live OrderedDict 만.
        AIContext: 캐시 차지 진단 / 디버깅 진입.
        Guide: stale 제외 — 진짜 메모리 사용 = size + len(_stale).
        When: cache 상태 진단 / dashboard 표시 시.
        How: ``len(self._store)``.

        Returns
        -------
        int
            현재 live 캐시에 저장된 항목 수 (개).

        Raises
        ------
        없음.

        Requires
        --------
        ``self._store`` OrderedDict.

        Example
        -------
        >>> cache.size

        See Also
        --------
        clear : 전체 size 0 만들기.
        """
        return len(self._store)

    def __repr__(self) -> str:
        return f"GatherCache(entries={self.size}, max={self._max})"
