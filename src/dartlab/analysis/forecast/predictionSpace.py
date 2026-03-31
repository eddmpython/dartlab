"""Prediction Space — 매출 변화를 설명하는 6대 보편 축.

전체 기업에 공통으로 작용하는 외부 축을 실시간 데이터로 계산한다.
기업별 차이는 SECTOR_ELASTICITY(25개 섹터 탄성치)로 구분.

6대 축:
- businessCycle (경기): CLI, IPI
- interestRate (금리): BASE_RATE, TREASURY_3Y
- fxRate (환율): USDKRW
- commodity (원자재): PPI, WTI
- sentiment (심리): CSI, BSI
- liquidity (유동성): M2

사용법::

    from dartlab.analysis.forecast.predictionSpace import getPredictionSpace

    space = getPredictionSpace()
    if space:
        print(space.axes["businessCycle"].level)    # -1.0 ~ +1.0
        print(space.impactOn("반도체"))              # 축별 매출 영향 %
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

log = logging.getLogger(__name__)


# ── 데이터 구조 ──


@dataclass
class AxisState:
    """단일 예측 축의 현재 상태."""

    name: str
    label: str
    level: float  # -1.0 (수축) ~ +1.0 (팽창)
    direction: str  # "improving" | "deteriorating" | "stable"
    momentum: float  # -1.0 ~ +1.0
    confidence: str  # "high" | "medium" | "low"
    indicators: dict[str, float | None] = field(default_factory=dict)
    asOf: str = ""


@dataclass
class PredictionSpace:
    """6대 보편 예측 축."""

    axes: dict[str, AxisState] = field(default_factory=dict)
    timestamp: str = ""
    dataFreshness: str = "unavailable"

    def impactOn(self, sectorKey: str | None) -> dict[str, float]:
        """섹터별 매출 영향 추정 (%).

        SECTOR_ELASTICITY의 탄성치를 사용하여
        각 축 상태 → 매출 변화율로 변환.
        """
        from dartlab.core.finance.scenario import getElasticity

        e = getElasticity(sectorKey)
        impacts: dict[str, float] = {}

        bc = self.axes.get("businessCycle")
        if bc:
            impacts["businessCycle"] = bc.level * e.revenueToGdp * 3.0

        ir = self.axes.get("interestRate")
        if ir:
            if e.nimToRate > 0:
                impacts["interestRate"] = ir.level * e.nimToRate / 100
            else:
                impacts["interestRate"] = -ir.level * 0.5

        fx = self.axes.get("fxRate")
        if fx:
            impacts["fxRate"] = fx.level * e.revenueToFx * 2.0

        cm = self.axes.get("commodity")
        if cm:
            commodityProducers = {"화학", "철강", "에너지/자원", "Energy", "Materials"}
            if sectorKey in commodityProducers:
                impacts["commodity"] = cm.level * 2.0
            else:
                impacts["commodity"] = -cm.level * 1.0

        st = self.axes.get("sentiment")
        if st and e.cyclicality in ("high", "moderate"):
            impacts["sentiment"] = st.level * 1.5

        lq = self.axes.get("liquidity")
        if lq:
            impacts["liquidity"] = lq.level * 0.5

        return {k: round(v, 2) for k, v in impacts.items()}

    def summary(self) -> dict:
        """AI 컨텍스트용 요약."""
        return {
            "axes": {
                name: {
                    "label": ax.label,
                    "state": "expansion" if ax.level > 0.2 else "contraction" if ax.level < -0.2 else "neutral",
                    "direction": ax.direction,
                    "level": round(ax.level, 2),
                    "momentum": round(ax.momentum, 2),
                }
                for name, ax in self.axes.items()
            },
            "timestamp": self.timestamp,
            "freshness": self.dataFreshness,
        }


# ── 축 정의 ──

_AXIS_DEFS = {
    "businessCycle": {
        "label": "경기축",
        "indicators": ["CLI", "IPI", "MANUFACTURING"],
        "market": "KR",
        "normalize": "index",  # 100 기준
    },
    "interestRate": {
        "label": "금리축",
        "indicators": ["BASE_RATE", "TREASURY_3Y"],
        "market": "KR",
        "normalize": "zscore",
    },
    "fxRate": {
        "label": "환율축",
        "indicators": ["USDKRW"],
        "market": "KR",
        "normalize": "price",
        "baseline": 1300,  # 중립 환율 기준
    },
    "commodity": {
        "label": "원자재축",
        "indicators": ["PPI"],
        "market": "KR",
        "normalize": "index",
    },
    "sentiment": {
        "label": "심리축",
        "indicators": ["CSI", "BSI"],
        "market": "KR",
        "normalize": "index",
    },
    "liquidity": {
        "label": "유동성축",
        "indicators": ["M2"],
        "market": "KR",
        "normalize": "growth",
    },
}


# ── 정규화 함수 ──


def _clamp(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _normalizeIndex(values: list[float]) -> float:
    """지수형 (100 기준). CLI, CSI, BSI, IPI 등."""
    if not values:
        return 0.0
    latest = values[-1]
    return _clamp((latest - 100) / 20)


def _normalizeZscore(values: list[float]) -> float:
    """Z-score (2년 평균/표준편차 기준)."""
    if len(values) < 6:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = variance**0.5
    if std < 0.001:
        return 0.0
    return _clamp((values[-1] - mean) / std / 2)


def _normalizePrice(values: list[float], baseline: float) -> float:
    """가격형 (기준가 대비 편차)."""
    if not values or baseline == 0:
        return 0.0
    latest = values[-1]
    return _clamp((latest - baseline) / baseline * 5)


def _normalizeGrowth(values: list[float]) -> float:
    """성장률형 (YoY 변화율)."""
    if len(values) < 13:
        return 0.0
    current = values[-1]
    yearAgo = values[-13] if len(values) >= 13 else values[0]
    if yearAgo == 0:
        return 0.0
    yoy = (current - yearAgo) / abs(yearAgo)
    return _clamp(yoy * 5)


def _computeDirection(values: list[float], nMonths: int = 3) -> tuple[str, float]:
    """3개월 추세로 방향 + 모멘텀 계산."""
    if len(values) < nMonths:
        return "stable", 0.0

    recent = values[-nMonths:]
    if len(recent) < 2:
        return "stable", 0.0

    # 단순 기울기
    n = len(recent)
    xMean = (n - 1) / 2
    yMean = sum(recent) / n
    num = sum((i - xMean) * (y - yMean) for i, y in enumerate(recent))
    den = sum((i - xMean) ** 2 for i in range(n))
    slope = num / den if den > 0 else 0.0

    # 정규화 모멘텀
    scale = abs(yMean) if yMean != 0 else 1.0
    momentum = _clamp(slope / scale * 10)

    threshold = 0.1
    if momentum > threshold:
        return "improving", momentum
    elif momentum < -threshold:
        return "deteriorating", momentum
    else:
        return "stable", momentum


# ── 축 상태 계산 ──


def _computeAxisState(axisName: str, axisDef: dict, macroData: dict) -> AxisState | None:
    """단일 축의 상태를 계산."""
    indicators = axisDef["indicators"]
    normalizeType = axisDef["normalize"]
    label = axisDef["label"]

    # 지표 값 수집
    allValues: list[list[float]] = []
    indicatorVals: dict[str, float | None] = {}
    asOf = ""

    for indName in indicators:
        series = macroData.get(indName)
        if series is None or len(series) == 0:
            indicatorVals[indName] = None
            continue

        vals = [v for v in series if v is not None]
        if not vals:
            indicatorVals[indName] = None
            continue

        indicatorVals[indName] = vals[-1]
        allValues.append(vals)

    if not allValues:
        return None

    # 주 지표 (첫 번째)의 값으로 정규화
    primaryVals = allValues[0]

    if normalizeType == "index":
        level = _normalizeIndex(primaryVals)
    elif normalizeType == "zscore":
        level = _normalizeZscore(primaryVals)
    elif normalizeType == "price":
        baseline = axisDef.get("baseline", 1300)
        level = _normalizePrice(primaryVals, baseline)
    elif normalizeType == "growth":
        level = _normalizeGrowth(primaryVals)
    else:
        level = 0.0

    # 보조 지표가 있으면 평균
    if len(allValues) > 1:
        secondaryLevels = []
        for vals in allValues[1:]:
            if normalizeType == "index":
                secondaryLevels.append(_normalizeIndex(vals))
            elif normalizeType == "zscore":
                secondaryLevels.append(_normalizeZscore(vals))

        if secondaryLevels:
            # 주 지표 2x, 보조 1x 가중
            totalWeight = 2 + len(secondaryLevels)
            level = (level * 2 + sum(secondaryLevels)) / totalWeight

    direction, momentum = _computeDirection(primaryVals)

    # 신뢰도
    nAvailable = sum(1 for v in indicatorVals.values() if v is not None)
    if nAvailable == len(indicators):
        confidence = "high"
    elif nAvailable >= 1:
        confidence = "medium"
    else:
        confidence = "low"

    return AxisState(
        name=axisName,
        label=label,
        level=round(level, 3),
        direction=direction,
        momentum=round(momentum, 3),
        confidence=confidence,
        indicators=indicatorVals,
    )


# ── 매크로 데이터 fetch ──


def _fetchMacroData() -> dict[str, list[float]]:
    """ECOS/FRED에서 필요한 지표를 가져온다.

    Gather 레이어의 캐싱을 활용하므로 반복 호출 비용 낮음.
    """
    from dartlab.gather import getDefaultGather

    g = getDefaultGather()
    result: dict[str, list[float]] = {}

    # 필요한 지표 목록
    krIndicators = ["CLI", "IPI", "MANUFACTURING", "BASE_RATE", "TREASURY_3Y", "USDKRW", "PPI", "CSI", "BSI", "M2"]

    for ind in krIndicators:
        try:
            df = g.macro("KR", ind, start="2023-01-01")
            if df is not None and len(df) > 0:
                valCol = [c for c in df.columns if c != "date"]
                if valCol:
                    vals = df[valCol[0]].to_list()
                    result[ind] = [v for v in vals if v is not None]
        except (ValueError, TypeError, AttributeError, KeyError) as e:
            log.debug("매크로 지표 %s 로드 실패: %s", ind, e)

    return result


# ── 세션 캐시 ──

_SPACE_CACHE: PredictionSpace | None = None
_CACHE_TS: float = 0
_CACHE_TTL = 3600  # 1시간


def getPredictionSpace(*, forceRefresh: bool = False) -> PredictionSpace | None:
    """보편 예측 공간을 가져온다.

    첫 호출 시 매크로 데이터 fetch (2-5초).
    이후 세션 내 캐시 반환 (마이크로초).
    API 키 없으면 None.
    """
    global _SPACE_CACHE, _CACHE_TS

    if not forceRefresh and _SPACE_CACHE and (time.monotonic() - _CACHE_TS < _CACHE_TTL):
        return _SPACE_CACHE

    macroData = _fetchMacroData()
    if not macroData:
        return None

    from datetime import datetime

    axes: dict[str, AxisState] = {}
    for axisName, axisDef in _AXIS_DEFS.items():
        state = _computeAxisState(axisName, axisDef, macroData)
        if state is not None:
            axes[axisName] = state

    if not axes:
        return None

    space = PredictionSpace(
        axes=axes,
        timestamp=datetime.now().isoformat(),
        dataFreshness="fresh" if len(axes) >= 4 else "partial",
    )

    _SPACE_CACHE = space
    _CACHE_TS = time.monotonic()
    return space
