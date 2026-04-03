"""시장 레벨 매크로 분석 엔진 — Company 불필요.

dartlab의 핵심 사상 4가지 비교 가능성 중 "시장 내/시장 간 비교"를 담당.
gather(L1)가 수집한 원시 데이터 위에 해석 레이어를 제공한다.

사용법::

    import dartlab

    dartlab.macro()                       # 가이드 (축 목록)
    dartlab.macro("사이클")               # 경제 사이클 판별
    dartlab.macro("금리")                 # 금리 방향 + 고용/물가
    dartlab.macro("자산")                 # 5대 자산 종합 해석
    dartlab.macro("심리")                 # 공포탐욕 + VIX 구간
    dartlab.macro("유동성")               # M2 + 연준 B/S + 신용스프레드
    dartlab.macro("종합")                 # 전체 종합 판정

    dartlab.macro("사이클", market="KR")  # 한국 사이클
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

import polars as pl

# ── Axis Registry ────────────────────────────────────────


@dataclass(frozen=True)
class _AxisEntry:
    """macro 축 메타데이터."""

    module: str
    fn: str
    label: str
    description: str
    example: str


_AXIS_REGISTRY: dict[str, _AxisEntry] = {
    "cycle": _AxisEntry(
        module="dartlab.macro.cycle",
        fn="analyze_cycle",
        label="사이클",
        description="경제 사이클 4국면 판별 + 전환 시퀀스 감지",
        example='macro("사이클")',
    ),
    "rates": _AxisEntry(
        module="dartlab.macro.rates",
        fn="analyze_rates",
        label="금리",
        description="단기/장기 금리 해석 + 고용/물가 + 금리 방향",
        example='macro("금리")',
    ),
    "assets": _AxisEntry(
        module="dartlab.macro.assets",
        fn="analyze_assets",
        label="자산",
        description="5대 자산(단기금리/장기금리/환율/금/VIX) 심층 해석",
        example='macro("자산")',
    ),
    "sentiment": _AxisEntry(
        module="dartlab.macro.sentiment",
        fn="analyze_sentiment",
        label="심리",
        description="시장 공포탐욕 근사 + VIX 구간 + 분할매수 신호",
        example='macro("심리")',
    ),
    "liquidity": _AxisEntry(
        module="dartlab.macro.liquidity",
        fn="analyze_liquidity",
        label="유동성",
        description="M2 + 연준 B/S + 신용스프레드 종합 유동성 환경",
        example='macro("유동성")',
    ),
    "summary": _AxisEntry(
        module="dartlab.macro.summary",
        fn="analyze_summary",
        label="종합",
        description="사이클+금리+자산+심리+유동성 종합 매트릭스",
        example='macro("종합")',
    ),
}

_ALIASES: dict[str, str] = {
    # 한글 → 영문
    "사이클": "cycle",
    "경제사이클": "cycle",
    "경기": "cycle",
    "금리": "rates",
    "금리전망": "rates",
    "자산": "assets",
    "자산신호": "assets",
    "심리": "sentiment",
    "시장심리": "sentiment",
    "공포탐욕": "sentiment",
    "유동성": "liquidity",
    "유동성환경": "liquidity",
    "종합": "summary",
    "매크로종합": "summary",
}


def _resolve(axis: str) -> str:
    """한글/영문 alias → 정규 축 이름으로 변환."""
    lower = axis.strip().lower()
    if lower in _AXIS_REGISTRY:
        return lower
    if axis in _ALIASES:
        return _ALIASES[axis]
    if lower in _ALIASES:
        return _ALIASES[lower]
    # fuzzy hint
    available = list(_AXIS_REGISTRY.keys()) + list(_ALIASES.keys())
    hint = ", ".join(sorted(set(available)))
    msg = f"'{axis}' 축을 찾을 수 없습니다. 사용 가능: {hint}"
    raise KeyError(msg)


# ── Macro 클래스 ────────────────────────────────────────


class Macro:
    """시장 레벨 매크로 분석 — Company 불필요."""

    def __call__(
        self,
        axis: str | None = None,
        *,
        market: str = "US",
        **kwargs: Any,
    ) -> pl.DataFrame | dict:
        """매크로 분석 실행.

        Args:
            axis: 분석 축 (None이면 가이드)
            market: "US" | "KR" (기본 US)
            **kwargs: 축별 추가 파라미터

        Returns:
            가이드 DataFrame 또는 분석 결과 dict
        """
        if axis is None:
            return self._guide()

        key = _resolve(axis)
        entry = _AXIS_REGISTRY[key]
        mod = importlib.import_module(entry.module)
        fn = getattr(mod, entry.fn)
        return fn(market=market, **kwargs)

    def _guide(self) -> pl.DataFrame:
        """축 목록 + 사용법 가이드."""
        rows = []
        for key, entry in _AXIS_REGISTRY.items():
            rows.append(
                {
                    "축": entry.label,
                    "key": key,
                    "설명": entry.description,
                    "예시": entry.example,
                }
            )
        return pl.DataFrame(rows)

    def __repr__(self) -> str:
        axes = ", ".join(e.label for e in _AXIS_REGISTRY.values())
        return f"Macro({axes})"

    # accessor 패턴: macro.cycle, macro.rates ...
    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            key = _resolve(name)
        except KeyError:
            raise AttributeError(f"Macro has no axis '{name}'") from None

        def _run(*, market: str = "US", **kwargs: Any) -> dict:
            entry = _AXIS_REGISTRY[key]
            mod = importlib.import_module(entry.module)
            fn = getattr(mod, entry.fn)
            return fn(market=market, **kwargs)

        return _run
