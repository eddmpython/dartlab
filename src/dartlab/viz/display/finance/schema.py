"""viz/finance JSON 표준 스키마.

frontend 가 ChartRenderer / TableRenderer 분기에 쓰는 단일 계약.
모든 view (statements · ratios · breakdown · snapshot) 가 동일 모양 반환.

원칙:
- 컬러·hex 없음. `intent` 는 의미 슬롯만 (primary/positive/negative/neutral/accent).
  실제 hex 매핑은 frontend 가 결정.
- 모든 key 는 영문 camelCase. 한국어는 `label` 필드 한 곳.
- periodKind 인코딩 1종: "annual" | "quarterly".
- categories.length == series[i].data.length 일관.
- breakdown 은 categories=항목명, series 1개 (data=값들).
"""

from __future__ import annotations

from typing import Literal, TypedDict

# 생성 컨텍스트와 기간 종류는 재무 화면만의 것이 아니다. `viz.schema` 가 정본이고 여기서는
# 그대로 다시 내보낸다. 예전에는 두 파일이 `Meta` 와 `makeMeta` 를 글자까지 똑같이 갖고
# 있어서, 한쪽에 필드를 더하면 같은 view 가 어느 모듈을 거쳤는지에 따라 다른 meta 를 달았다.
from dartlab.viz.schema import Meta, PeriodKind, makeMeta

__all__ = [
    "EvidenceBinding",
    "Meta",
    "PeriodKind",
    "Series",
    "SeriesAxis",
    "SeriesIntent",
    "SeriesPoint",
    "SeriesType",
    "View",
    "ViewKind",
    "makeBinding",
    "makeMeta",
]

ViewKind = Literal[
    "trend",  # 시계열 (line/bar): categories=기간, series=지표
    "snapshot",  # 단일 기간 막대: categories=항목, series 1개
    "breakdown",  # 구성 (pie): categories=항목, series 1개 (data=값)
    "table",  # 표: categories=기간, series=행
    "waterfall",  # 폭포: categories=단계, series=값+측정종류
    "matrix",  # 2D 행렬 (heatmap): categories=X축, series=Y축×values
]

SeriesIntent = Literal["primary", "positive", "negative", "neutral", "accent"]

SeriesAxis = Literal["left", "right"]
SeriesType = Literal["bar", "line", "area"]


class SeriesPoint(TypedDict, total=False):
    """waterfall 단일 스텝."""

    value: float | None
    measure: Literal["absolute", "relative", "total"]


class Series(TypedDict, total=False):
    """series 단일 시리즈.

    - key: 영문 식별자 (예: "revenue", "operatingMargin")
    - label: 표시명 (다국어 가능, 기본 한국어)
    - data: 값 리스트 (categories 와 길이 일치)
    - unit: "원" | "%" | "회" | "일" | "배" 등
    - intent: 의미 슬롯 (None 이면 frontend 기본 컬러)
    - axis: "left" | "right" (기본 left)
    - type: "bar" | "line" | "area" (combo 차트용, 기본은 kind 에서 결정)
    - points: waterfall 용 step 리스트 (data 대신 사용)
    """

    key: str
    label: str
    data: list[float | None]
    points: list[SeriesPoint]
    unit: str
    intent: SeriesIntent
    axis: SeriesAxis
    type: SeriesType


class EvidenceBinding(TypedDict, total=False):
    """차트 → 원본 표 drill-back 진입점."""

    source: str  # "dart" | "edgar"
    stockCode: str
    topic: str  # "IS" | "BS" | "CF" | "ratios"
    periodKind: PeriodKind
    periods: list[str]
    tableRef: str  # "finance:005930:IS:annual"


class View(TypedDict, total=False):
    """viz/finance view 표준 출력.

    frontend ChartRenderer 가 kind 만 보고 분기 가능.
    """

    kind: ViewKind
    title: str
    categories: list[str]
    series: list[Series]
    evidenceBinding: EvidenceBinding
    meta: Meta
    options: dict  # kind 별 부가 옵션 (stacked, dual, ...)


def makeBinding(
    stockCode: str,
    topic: str,
    periodKind: PeriodKind,
    periods: list[str],
    *,
    source: str = "dart",
) -> EvidenceBinding:
    """EvidenceBinding 표준 생성."""
    return {
        "source": source,
        "stockCode": str(stockCode),
        "topic": topic,
        "periodKind": periodKind,
        "periods": list(periods),
        "tableRef": f"finance:{stockCode}:{topic}:{periodKind}",
    }
