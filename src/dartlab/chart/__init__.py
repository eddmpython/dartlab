"""시각화 엔진 -- scan급 독립 진입점.

사용법::

    import dartlab

    dartlab.chart()                       # 가이드 (축 목록 + 사용법)
    dartlab.chart("revenue", c)           # 매출 차트 -> Plotly Figure
    dartlab.chart("auto", c)              # 자동: 가용 데이터 기반 전체 차트
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl

# ── Axis Registry ────────────────────────────────────────


@dataclass(frozen=True)
class _AxisEntry:
    """chart 축 메타데이터."""

    fn: str
    specFn: str | None
    label: str
    description: str
    example: str


_AXIS_REGISTRY: dict[str, _AxisEntry] = {
    "revenue": _AxisEntry(
        fn="revenue",
        specFn="spec_revenue_trend",
        label="매출 추이",
        description="매출 + 영업이익률 콤보 차트",
        example='chart("revenue", c)',
    ),
    "cashflow": _AxisEntry(
        fn="cashflow",
        specFn="spec_cashflow_waterfall",
        label="현금흐름",
        description="OCF/ICF/FCF 폭포 차트",
        example='chart("cashflow", c)',
    ),
    "dividend": _AxisEntry(
        fn="dividend",
        specFn="spec_dividend",
        label="배당",
        description="DPS + 배당수익률 + 배당성향",
        example='chart("dividend", c)',
    ),
    "balance": _AxisEntry(
        fn="balance_sheet",
        specFn="spec_balance_sheet",
        label="자산 구성",
        description="자산/부채/자본 구성 차트",
        example='chart("balance", c)',
    ),
    "profitability": _AxisEntry(
        fn="profitability",
        specFn="spec_profitability",
        label="수익성",
        description="ROE, 영업이익률, 순이익률 추이",
        example='chart("profitability", c)',
    ),
    "radar": _AxisEntry(
        fn=None,
        specFn="spec_insight_radar",
        label="인사이트 레이더",
        description="10영역 인사이트 레이더 차트",
        example='chart("radar", c)',
    ),
    "ratio": _AxisEntry(
        fn=None,
        specFn="spec_ratio_sparklines",
        label="비율 스파크라인",
        description="주요 재무비율 스파크라인",
        example='chart("ratio", c)',
    ),
    "heatmap": _AxisEntry(
        fn=None,
        specFn="spec_diff_heatmap",
        label="변화 히트맵",
        description="공시 변화 히트맵",
        example='chart("heatmap", c)',
    ),
    "auto": _AxisEntry(
        fn=None,
        specFn=None,
        label="자동 감지",
        description="가용 데이터 기반 전체 차트 자동 생성",
        example='chart("auto", c)',
    ),
}


# ── Aliases ──────────────────────────────────────────────


_ALIASES: dict[str, str] = {
    "매출": "revenue",
    "매출추이": "revenue",
    "현금": "cashflow",
    "현금흐름": "cashflow",
    "배당": "dividend",
    "자산": "balance",
    "자산구성": "balance",
    "수익성": "profitability",
    "레이더": "radar",
    "비율": "ratio",
    "히트맵": "heatmap",
    "변화": "heatmap",
    "자동": "auto",
    "전체": "auto",
}


def _resolveAxis(axis: str) -> str:
    """축 이름 또는 alias -> 정규 축 이름."""
    lower = axis.lower()
    if lower in _AXIS_REGISTRY:
        return lower
    if axis in _ALIASES:
        return _ALIASES[axis]
    if lower in _ALIASES:
        return _ALIASES[lower]
    available = ", ".join(sorted(_AXIS_REGISTRY))
    raise ValueError(f"알 수 없는 chart 축: '{axis}'. 가용 축: {available}")


# ── Chart Class ──────────────────────────────────────────


class Chart:
    """시각화 엔진 -- Plotly 기반 재무 차트.

    Capabilities:
        - revenue: 매출 + 영업이익률 콤보
        - cashflow: OCF/ICF/FCF 폭포
        - dividend: DPS + 배당수익률 + 배당성향
        - balance: 자산/부채/자본 구성
        - profitability: ROE, 영업이익률, 순이익률
        - radar: 10영역 인사이트 레이더
        - ratio: 주요 재무비율 스파크라인
        - heatmap: 공시 변화 히트맵
        - auto: 가용 데이터 기반 전체 차트

    Args:
        axis: 차트 축. None이면 가이드 반환.
        company: Company 객체.
        **kwargs: 축별 옵션 (n_years 등).

    Returns:
        Plotly Figure 또는 가이드 DataFrame.

    Requires:
        데이터: Company (자동 다운로드)
        패키지: plotly (pip install dartlab[charts])

    Example::

        import dartlab
        c = dartlab.Company("005930")
        dartlab.chart()                   # 가이드
        dartlab.chart("revenue", c)       # 매출 차트
        dartlab.chart("auto", c)          # 전체 자동
    """

    def __call__(
        self,
        axis: str | None = None,
        company: Any = None,
        **kwargs: Any,
    ) -> Any:
        """축(axis)별 차트 생성."""
        if axis is None:
            return self._guide()

        resolved = _resolveAxis(axis)

        if company is None:
            return self._describe(resolved)

        return self._run(resolved, company, **kwargs)

    # ── internal ──

    def _guide(self) -> pl.DataFrame:
        """가이드 DataFrame 반환."""
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

    def _describe(self, axis: str) -> pl.DataFrame:
        """축 설명 반환."""
        entry = _AXIS_REGISTRY[axis]
        return pl.DataFrame(
            [
                {
                    "axis": axis,
                    "label": entry.label,
                    "description": entry.description,
                    "example": entry.example,
                    "requires": "Company + plotly",
                }
            ]
        )

    def _run(self, axis: str, company: Any, **kwargs: Any) -> Any:
        """실제 차트 생성."""
        from dartlab.tools import chart as _chart

        entry = _AXIS_REGISTRY[axis]

        # auto: 전체 ChartSpec 리스트 -> Figure 리스트
        if axis == "auto":
            specs = _chart.auto_chart(company)
            return [_chart.chart_from_spec(s) for s in specs]

        # specFn만 있는 축 (radar, ratio, heatmap)
        if entry.fn is None and entry.specFn is not None:
            specFn = getattr(_chart, entry.specFn)
            spec = specFn(company, **kwargs)
            if spec is None:
                return None
            return _chart.chart_from_spec(spec)

        # fn이 있는 축 (revenue, cashflow, dividend, balance, profitability)
        fn = getattr(_chart, entry.fn)
        return fn(company, **kwargs)

    def __repr__(self) -> str:
        axes = ", ".join(sorted(_AXIS_REGISTRY))
        return f"Chart(axes=[{axes}])"
