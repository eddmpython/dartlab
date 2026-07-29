"""K-IFRS 주석 내부 dispatch — Plan v10 P2 에서 ``c.notes`` property 가 제거되어
사용자 진입점은 ``c.panel("inventory")`` · ``c.panel("receivables")`` 등 통합.

이 모듈은 show topic 매핑이 호출하는 내부 추출 함수들을 묶는다.

주석 항목 추가 시 ``core/dataEntry.py`` 의 내장 카탈로그에 DataEntry 한 줄 추가
(extractor + notesDispatch 명시) 하면 자동 반영. 별도 하드코딩 dispatch dict 없음.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import TYPE_CHECKING, Any

from dartlab.core.logger import getLogger
from dartlab.core.memory import BoundedCache
from dartlab.core.registry import getEntries

_log = getLogger(__name__)

if TYPE_CHECKING:
    import polars as pl


# Q1.2 (2026-04-21): _NOTES_DISPATCH 하드코딩 제거 — registry 에서 동적 생성.
# `category="notes"` 엔트리 중 `notesDispatch` + `extractor` 가 설정된 것만 포함.
def _buildDispatch() -> "OrderedDict[str, tuple[str, str, Any]]":
    dispatch: OrderedDict[str, tuple[str, str, Any]] = OrderedDict()
    for e in getEntries(category="notes"):
        if e.notesDispatch is None or e.extractor is None:
            continue
        # "notes.receivables" → "receivables" bare name
        bareName = e.name.removeprefix("notes.") if e.name.startswith("notes.") else e.name
        dispatch[bareName] = (e.notesDispatch[0], e.notesDispatch[1], e.extractor)
    return dispatch


_NOTES_DISPATCH: OrderedDict[str, tuple[str, str, Any]] = _buildDispatch()

# core/registry.py와 동기화된 외부 인터페이스 (하위 호환)
_REGISTRY = _NOTES_DISPATCH

# 한글→영문 역매핑
_KR_MAP: dict[str, str] = {v[1]: k for k, v in _REGISTRY.items()}


class Notes:
    """K-IFRS 주석 데이터 통합 접근.

    모든 항목은 Polars DataFrame | None을 반환한다.
    영문 속성 또는 한글 딕셔너리 키로 접근 가능. lazy 로딩 + 캐싱.

    반환 DataFrame 구조:
        - notesDetail 기반 (inventory, borrowings 등): 항목 × 연도 (항목 열 + 2025, 2024, ... 열)
        - tangibleAsset/affiliates: 카테고리 × 기초/기말 변동 (카테고리 열 + 연도_기초, 연도_기말, ... 열)
        - segments: 부문 × 연도 (부문명 열 + 연도별 매출 열)
        - costByNature: 비용항목 × 연도 시계열

    panel("financialNotes")와의 차이:
        - notes: 파싱된 정규화 DataFrame. AI/코드 분석용 최적.
        - show: 원문 마크다운. 사용자 원문 확인용.
    """

    _company: Any
    _cache: BoundedCache

    def __init__(self, company: Any):
        object.__setattr__(self, "_company", company)
        object.__setattr__(self, "_cache", BoundedCache(maxEntries=20, pressureMb=1200.0))

    def __getattr__(self, name: str) -> pl.DataFrame | None:
        if name.startswith("_"):
            raise AttributeError(name)
        if name in _REGISTRY:
            return self._get(name)
        raise AttributeError(f"Notes에 '{name}' 항목이 없습니다. 지원: {list(_REGISTRY.keys())}")

    def __getitem__(self, key: str) -> pl.DataFrame | None:
        eng = _KR_MAP.get(key, key)
        if eng not in _REGISTRY:
            raise KeyError(f"Notes에 '{key}' 항목이 없습니다. 지원: {list(_KR_MAP.keys())}")
        return self._get(eng)

    def _get(self, name: str, period: str = "y") -> pl.DataFrame | None:
        cacheKey = f"{name}:{period}"
        cacheHit, cached = self._cache.lookup(cacheKey)
        if cacheHit:
            return cached

        spec = _REGISTRY[name]
        module, krName, extractor = spec

        from dartlab.core.messagingContext import Context

        if Context().verbose:
            periodLabel = {"y": "", "q": " (분기)", "h": " (반기)"}.get(period, "")
            _log.info("  ▶ %s · %s%s", self._company.corpName, krName, periodLabel)

        try:
            if module == "notesDetail":
                result = self._company._call_notesDetail(krName, period=period)
            else:
                result = self._company._callModule(module)
            df = extractor(result) if result else None
        except (FileNotFoundError, ValueError, KeyError, AttributeError):
            import logging

            logging.getLogger(__name__).debug("notes(%s) failed", name, exc_info=True)
            df = None

        self._cache[cacheKey] = df
        return df

    def quarterly(self, name: str) -> pl.DataFrame | None:
        """분기 주석 데이터 반환 (내부 dispatch).

        Company 의 ``_notesAccessor`` 가 호출. 사용자는 ``c.panel("inventory")`` 처럼
        통합 진입점을 사용하고, 분기/연간 토글은 show 의 freq 파라미터로 제어한다.

        분기보고서(Q1/Q3) + 반기보고서 + 사업보고서 주석을 모두 파싱.

        Args:
            name: 인자.

        Raises:
            없음.

        Example:
            >>> quarterly(...)

        Returns:
            pl.DataFrame 또는 None — 카테고리 결과.

        SeeAlso:
            - ``c.panel("inventory"/...)`` — public surface.

        Requires:
            - dartlab

        Capabilities:
            - K-IFRS notes 카테고리 dispatch — registry 기반.

        Guide:
            - 사용자 API 는 ``c.panel()`` — 본 모듈 직접 호출 X.

        AIContext:
            internal notes dispatch — AI 직접 호출 X.

        LLM Specifications:
            AntiPatterns:
                - 본 모듈 직접 호출 X — c.panel("inventory"/...) 위임.
                - notes 카테고리 추측 X — registry 등록 키만.
            OutputSchema:
                - pl.DataFrame 또는 None.
            Prerequisites:
                - 본 회사 docs notes 본문 + core/dataEntry.py 등록.
            Freshness:
                - docs 갱신 시점.
            Dataflow:
                - category → notesDispatch → extractor → 본 함수.
            TargetMarkets:
                - KR (DART) K-IFRS notes.
        """
        eng = _KR_MAP.get(name, name)
        if eng not in _REGISTRY:
            raise KeyError(f"Notes에 '{name}' 항목이 없습니다. 지원: {list(_REGISTRY.keys())}")
        return self._get(eng, period="q")

    def all(self, period: str = "y") -> dict[str, pl.DataFrame | None]:
        """모든 주석 항목을 dict로 반환.

        Args:
            period: 인자.

        Raises:
            없음.

        Example:
            >>> all(...)

        Returns:
            dict[str, pl.DataFrame | None] — 카테고리 별 결과.

        LLM Specifications:
            AntiPatterns:
                - 본 모듈 직접 호출 X — c.panel("inventory"/...) 위임.
                - notes 카테고리 추측 X — registry 등록 키만.
            OutputSchema:
                - pl.DataFrame 또는 None.
            Prerequisites:
                - 본 회사 docs notes 본문 + core/dataEntry.py 등록.
            Freshness:
                - docs 갱신 시점.
            Dataflow:
                - category → notesDispatch → extractor → 본 함수.
            TargetMarkets:
                - KR (DART) K-IFRS notes.
        """
        return {name: self._get(name, period=period) for name in _REGISTRY}

    def keys(self) -> list[str]:
        """지원하는 영문 속성명 목록.

        Args:
            (인자 자동 생성).

        Raises:
            없음.

        Example:
            >>> keys(...)

        Returns:
            list[str] — 카테고리 키 목록.

        LLM Specifications:
            AntiPatterns:
                - 본 모듈 직접 호출 X — c.panel("inventory"/...) 위임.
                - notes 카테고리 추측 X — registry 등록 키만.
            OutputSchema:
                - pl.DataFrame 또는 None.
            Prerequisites:
                - 본 회사 docs notes 본문 + core/dataEntry.py 등록.
            Freshness:
                - docs 갱신 시점.
            Dataflow:
                - category → notesDispatch → extractor → 본 함수.
            TargetMarkets:
                - KR (DART) K-IFRS notes.
        """
        return list(_REGISTRY.keys())

    def keysKr(self) -> list[str]:
        """지원하는 한글 키워드 목록.

        Args:
            (인자 자동 생성).

        Raises:
            없음.

        Example:
            >>> keysKr(...)

        Returns:
            list[str] — 카테고리 키 목록.

        LLM Specifications:
            AntiPatterns:
                - 본 모듈 직접 호출 X — c.panel("inventory"/...) 위임.
                - notes 카테고리 추측 X — registry 등록 키만.
            OutputSchema:
                - pl.DataFrame 또는 None.
            Prerequisites:
                - 본 회사 docs notes 본문 + core/dataEntry.py 등록.
            Freshness:
                - docs 갱신 시점.
            Dataflow:
                - category → notesDispatch → extractor → 본 함수.
            TargetMarkets:
                - KR (DART) K-IFRS notes.
        """
        return list(_KR_MAP.keys())

    def __repr__(self) -> str:
        cached = [k for k in _REGISTRY if k in self._cache]
        return f"Notes({len(cached)}/{len(_REGISTRY)} loaded)"

    def __contains__(self, key: str) -> bool:
        return key in _REGISTRY or key in _KR_MAP
