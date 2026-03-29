"""테이블 가공 엔진 -- scan급 독립 진입점.

사용법::

    import dartlab

    dartlab.table()                              # 가이드 (축 목록 + 사용법)
    dartlab.table("yoy", c.IS)                   # YoY 변동률
    dartlab.table("format", c.BS, unit="억원")    # 한국어 단위
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl


# ── Axis Registry ────────────────────────────────────────


@dataclass(frozen=True)
class _AxisEntry:
    """table 축 메타데이터."""

    fn: str
    label: str
    description: str
    example: str
    targetName: str  # 첫 번째 위치 인자의 tools/table.py 파라미터명


_AXIS_REGISTRY: dict[str, _AxisEntry] = {
    "yoy": _AxisEntry(
        fn="yoy_change",
        label="YoY 변동률",
        description="전년 동기 대비 변동률 컬럼 추가",
        example='table("yoy", c.IS)',
        targetName="df",
    ),
    "summary": _AxisEntry(
        fn="summary_stats",
        label="요약 통계",
        description="평균/최소/최대/표준편차/CAGR/추세",
        example='table("summary", c.dividend)',
        targetName="df",
    ),
    "pivot": _AxisEntry(
        fn="pivot_accounts",
        label="계정 피벗",
        description="행=연도, 열=계정명 피벗 테이블",
        example='table("pivot", c.IS)',
        targetName="df",
    ),
    "format": _AxisEntry(
        fn="format_korean",
        label="한국어 단위",
        description="조원/억원/만원 단위 포맷팅",
        example='table("format", c.BS, unit="억원")',
        targetName="df",
    ),
    "growth": _AxisEntry(
        fn="growth_matrix",
        label="성장률 행렬",
        description="기간별 성장률 매트릭스",
        example='table("growth", c.IS)',
        targetName="df",
    ),
    "ratio": _AxisEntry(
        fn="ratio_table",
        label="재무비율",
        description="ROE/ROA/부채비율 등 재무비율 테이블",
        example='table("ratio", c.IS)',
        targetName="df",
    ),
}


# ── Aliases ──────────────────────────────────────────────


_ALIASES: dict[str, str] = {
    "변동률": "yoy",
    "전년비": "yoy",
    "요약": "summary",
    "통계": "summary",
    "피벗": "pivot",
    "포맷": "format",
    "한국어": "format",
    "단위": "format",
    "성장": "growth",
    "성장률": "growth",
    "비율": "ratio",
    "재무비율": "ratio",
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
    raise ValueError(f"알 수 없는 table 축: '{axis}'. 가용 축: {available}")


# ── Table Class ──────────────────────────────────────────


class Table:
    """테이블 가공 엔진 -- DataFrame 변환/포맷팅.

    Capabilities:
        - yoy: 전년 동기 대비 변동률
        - summary: 평균/CAGR/추세 요약
        - pivot: 계정별 피벗 테이블
        - format: 한국어 단위 포맷팅
        - growth: 성장률 행렬
        - ratio: 재무비율 계산

    Args:
        axis: 가공 축. None이면 가이드 반환.
        target: 가공 대상 DataFrame.
        **kwargs: 축별 옵션 (unit, value_cols 등).

    Returns:
        pl.DataFrame -- 가공된 데이터. axis=None이면 가이드 DataFrame.

    Example::

        import dartlab
        c = dartlab.Company("005930")
        dartlab.table()                          # 가이드
        dartlab.table("yoy", c.IS)               # YoY 변동률
        dartlab.table("format", c.BS, unit="억원") # 한국어 단위
    """

    def __call__(
        self,
        axis: str | None = None,
        target: Any = None,
        **kwargs: Any,
    ) -> pl.DataFrame:
        """축(axis)별 테이블 가공."""
        if axis is None:
            return self._guide()

        resolved = _resolveAxis(axis)

        if target is None:
            return self._describe(resolved)

        return self._run(resolved, target, **kwargs)

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
                    "requires": "pl.DataFrame",
                }
            ]
        )

    def _run(self, axis: str, target: Any, **kwargs: Any) -> Any:
        """실제 테이블 가공."""
        from dartlab.tools import table as _table

        entry = _AXIS_REGISTRY[axis]
        fn = getattr(_table, entry.fn)
        return fn(target, **kwargs)

    def __repr__(self) -> str:
        axes = ", ".join(sorted(_AXIS_REGISTRY))
        return f"Table(axes=[{axes}])"
