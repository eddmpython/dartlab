"""gather() 통합 진입점 — scan()과 동일한 3단계 패턴.

dartlab.gather()                       -> 가이드 (축 목록)
dartlab.gather("price", "005930")      -> 주가 시계열
dartlab.gather("flow", "005930")       -> 수급 동향
dartlab.gather("macro")                -> KR 거시지표 전체
dartlab.gather("macro", "CPI")         -> 단일 지표
dartlab.gather("news", "삼성전자")      -> 뉴스
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl


@dataclass(frozen=True)
class _GatherAxisEntry:
    """gather 축 메타데이터."""

    label: str
    description: str
    example: str
    targetRequired: bool = True


_AXIS_REGISTRY: dict[str, _GatherAxisEntry] = {
    "price": _GatherAxisEntry(
        label="주가",
        description="OHLCV 시계열 (기본 1년) — Naver/Yahoo/FMP fallback",
        example='gather("price", "005930")',
    ),
    "flow": _GatherAxisEntry(
        label="수급",
        description="외국인/기관 매매 동향 (KR 전용)",
        example='gather("flow", "005930")',
    ),
    "macro": _GatherAxisEntry(
        label="거시지표",
        description="ECOS(KR 12개) / FRED(US 25개) 거시 시계열",
        example='gather("macro") 또는 gather("macro", "CPI")',
        targetRequired=False,
    ),
    "news": _GatherAxisEntry(
        label="뉴스",
        description="Google News RSS — 최근 30일",
        example='gather("news", "삼성전자")',
    ),
}

_ALIASES: dict[str, str] = {
    "주가": "price",
    "수급": "flow",
    "거시": "macro",
    "매크로": "macro",
    "뉴스": "news",
}


def _resolveAxis(axis: str) -> str:
    """축 이름/별칭 -> 정규 키."""
    lower = axis.lower()
    if lower in _AXIS_REGISTRY:
        return lower
    if axis in _ALIASES:
        return _ALIASES[axis]
    if lower in _ALIASES:
        return _ALIASES[lower]
    available = ", ".join(sorted(_AXIS_REGISTRY))
    raise ValueError(f"알 수 없는 gather 축: '{axis}'. 가용 축: {available}")


class GatherEntry:
    """외부 시장 데이터 통합 수집 — 4축, 전부 Polars DataFrame.

    Capabilities:
        - price: OHLCV 시계열 (KR Naver/US Yahoo, 기본 1년, 최대 6000거래일)
        - flow: 외국인/기관 수급 동향 (KR 전용, Naver)
        - macro: ECOS(KR 12개) / FRED(US 25개) 거시지표 시계열
        - news: Google News RSS 뉴스 수집 (최근 30일)
        - 자동 fallback 체인, circuit breaker, TTL 캐시

    AIContext:
        - ask()/chat()에서 주가/수급/거시 데이터를 컨텍스트로 주입 가능
        - 기업 분석 시 시장 데이터 보충 자료로 활용

    Guide:
        - "주가 추이 보여줘" -> gather("price", "005930")
        - "외국인 매매 동향" -> gather("flow", "005930")
        - "금리 추이 알려줘" -> gather("macro", "BASE_RATE") 또는 gather("macro", "FEDFUNDS")
        - "최근 뉴스 찾아줘" -> gather("news", "삼성전자")
        - "미국 거시지표 전체" -> gather("macro", market="US") 또는 gather("US")
        - 주가+수급은 scan과 다름. scan은 재무 기반 횡단, gather는 시장 실시간.

    SeeAlso:
        - scan: 재무 기반 전종목 횡단분석 (거버넌스, 현금흐름 등)
        - Company: 개별 종목 공시/재무 데이터
        - analysis: 14축 전략분석 (재무비율, 수익구조 등)

    Args:
        axis: 축 이름 ("price", "flow", "macro", "news"). None이면 가이드 반환.
        target: 종목코드/지표코드/검색어. 축별로 다름.
        **kwargs: market ("KR"/"US"), start, end, days 등 축별 옵션.

    Returns:
        pl.DataFrame — 축별 시계열 데이터. axis=None이면 4축 가이드 DataFrame.

    Requires:
        price/flow/news: 없음 (공개 API)
        macro: API 키 — ECOS_API_KEY (KR) 또는 FRED_API_KEY (US)

    Example::

        import dartlab
        dartlab.gather()                              # 가이드
        dartlab.gather("price", "005930")             # 삼성전자 1년 OHLCV
        dartlab.gather("flow", "005930")              # 수급
        dartlab.gather("macro")                       # KR 거시 전체
        dartlab.gather("macro", "FEDFUNDS")           # 자동 US 감지
        dartlab.gather("news", "삼성전자")             # 뉴스
    """

    def __call__(
        self,
        axis: str | None = None,
        target: str | None = None,
        **kwargs: Any,
    ) -> pl.DataFrame:
        if axis is None:
            return self._guide()

        resolved = _resolveAxis(axis)
        entry = _AXIS_REGISTRY[resolved]

        if entry.targetRequired and target is None:
            raise ValueError(f'gather("{resolved}")에는 대상이 필요합니다.\n  예: {entry.example}')

        return self._run(resolved, target, **kwargs)

    def _run(self, axis: str, target: str | None, **kwargs: Any) -> pl.DataFrame:
        """축별 실행 디스패치."""
        from dartlab.gather import getDefaultGather

        g = getDefaultGather()

        _marketExplicit = "market" in kwargs
        market = kwargs.pop("market", "KR")
        start = kwargs.pop("start", None)
        end = kwargs.pop("end", None)

        if axis == "price":
            return g.price(target, market=market, start=start, end=end)
        if axis == "flow":
            return g.flow(target, market=market)
        if axis == "macro":
            if target is None:
                return g.macro(market, start=start, end=end)
            if _marketExplicit:
                return g.macro(market, target, start=start, end=end)
            return g.macro(target, start=start, end=end)
        if axis == "news":
            days = kwargs.pop("days", 30)
            return g.news(target, market=market, days=days)

        raise ValueError(f"미지원 gather 축: {axis}")

    def _guide(self) -> pl.DataFrame:
        """가이드 DataFrame — 축 목록 + 설명 + 사용 예시."""
        rows = [
            {
                "axis": key,
                "label": entry.label,
                "description": entry.description,
                "example": entry.example,
            }
            for key, entry in _AXIS_REGISTRY.items()
        ]
        return pl.DataFrame(rows)

    def __repr__(self) -> str:
        lines = [f"Gather -- {len(_AXIS_REGISTRY)}축 외부 시장 데이터"]
        for key, entry in _AXIS_REGISTRY.items():
            lines.append(f"  {key:12s} {entry.label} -- {entry.description}")
        lines.append("")
        lines.append("사용법: gather(), gather('축', '대상')")
        return "\n".join(lines)
