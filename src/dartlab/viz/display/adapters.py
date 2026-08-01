"""analysis/* 함수 결과 → kind 별 View spec 변환 어댑터.

각 함수는 (company, ...) 받아 dict | list | None. 다양한 출력 shape 을
방어적으로 파싱해 View 의 kind 별 필드 (tiles/items/rows/gauge value/...) 채움.

원칙:
- 실패 (None / 빈 dict / 미존재 키) 시 빈 spec 반환 — 카드는 "데이터 없음" 표시.
- 함수 시그니처 변화에 대비 try/except — 절대 view build 자체를 중단시키지 않음.
"""

from __future__ import annotations

import importlib
from typing import Any

from dartlab.core.logger import getLogger
from dartlab.viz.data import normalize  # noqa: F401 (_cache.getNormFinance 호출 시 lazy 사용)
from dartlab.viz.display.finance._cache import getNormFinance
from dartlab.viz.display.finance.accounts import extractSeries

_log = getLogger(__name__)


def _normAndPeriods(company: Any, limit: int, freq: str = "annual") -> tuple[Any, list[Any]]:
    """정규화 재무와 최근 `limit` 기간을 함께 얻는다.

    이 세 줄을 어댑터 여덟 곳이 그대로 복붙해 쓰고 있었다. 일곱 곳은 `except Exception`
    으로 통째로 삼켜 빈 차트를 냈고 한 곳은 아예 감싸지 않았다. 같은 동작이 자리마다
    다르게 실패하고 있었다는 뜻이라 한 자리로 모은다.

    표현층은 화면 하나를 못 그려도 프로세스를 죽이지 않는 것이 맞다. 다만 조용히
    지나가면 안 된다. 왜 비었는지가 로그에 남아야 빈 차트와 깨진 코드를 구분한다.

    Returns:
        `(norm, periods)`. 재무를 못 읽으면 `(None, [])`.
    """
    from dartlab.viz.display.finance.periods import lastNPeriods

    try:
        norm = getNormFinance(company)
        periods = lastNPeriods(norm, limit, freq)
    except Exception as exc:  # noqa: BLE001
        _log.debug("재무 기간 로드 실패 (limit=%s, freq=%s): %s", limit, freq, exc)
        return None, []
    return norm, list(periods or [])


def _safeCall(modulePath: str, fnName: str, company: Any, *args: Any, **kwargs: Any) -> Any:
    """analysis 모듈 함수 안전 호출 — import / call 실패 시 None."""
    try:
        mod = importlib.import_module(modulePath)
    except ImportError:
        return None
    fn = getattr(mod, fnName, None)
    if fn is None:
        return None
    try:
        return fn(company, *args, **kwargs)
    except Exception:  # noqa: BLE001
        return None


def _toFloat(v: Any) -> float | None:
    """안전 float 변환. 실패 시 None."""
    if v is None:
        return None
    try:
        f = float(v)
        if f != f or f == float("inf") or f == float("-inf"):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _drill(obj: Any, path: str) -> Any:
    """dot-path 로 dict/객체 안 값 추출. 실패 시 None."""
    cur = obj
    for part in path.split("."):
        if cur is None:
            return None
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif hasattr(cur, part):
            cur = getattr(cur, part)
        else:
            return None
    return cur


# ─────────────────────────────────────────────────────────────
# kpiTile / diffView — norm 의 마지막 2 기간 자동 추출.
# ─────────────────────────────────────────────────────────────


def buildKpiTilesFromNorm(norm: Any, periods: list[str], tilePlans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """norm + tilePlans → KpiTile dict list (P-DASH-V1 D11: sparkline + range bar).

    tilePlans 각 항목: {label, account?: str, ratio?: dict, unit, intent, subtitle?}.

    출력 tile 각 항목:
        - value/prev/unit/intent/subtitle (기존)
        - sparkline: list[float] — 최근 8 분기 데이터 (카드 우측 mini line).
        - rangeMin/rangeMax: 자체 5y range (카드 하단 percentile bar).
    """
    tiles: list[dict[str, Any]] = []
    for plan in tilePlans:
        label = plan.get("label", "")
        unit = plan.get("unit", "")
        intent = plan.get("intent", "primary")
        subtitle = plan.get("subtitle", "")
        data: list[float | None] = []
        if "account" in plan:
            data = extractSeries(norm, plan["account"], periods)
        elif "yoy" in plan:
            base = extractSeries(norm, plan["yoy"], periods)
            data = [None]
            for k in range(1, len(periods)):
                p, c = base[k - 1], base[k]
                if p is None or c is None or p == 0:
                    data.append(None)
                else:
                    data.append((c - p) / abs(p) * 100)
        elif "ratio" in plan:
            ratio = plan["ratio"]
            num_terms = ratio.get("num") or {}
            den_terms = ratio.get("den") or {}
            scale = float(ratio.get("scale", 100))
            num = _sumWeighted(norm, num_terms, periods)
            den = _sumWeighted(norm, den_terms, periods)
            data = [(n / d * scale) if (n is not None and d is not None and d != 0) else None for n, d in zip(num, den)]
        elif "compose" in plan:
            data = _sumWeighted(norm, plan["compose"], periods)
        last, prev = _lastTwo(data)

        # sparkline — 최근 8 기간 (또는 가능한 만큼).
        nonNone = [v for v in data if v is not None]
        sparkline = nonNone[-8:] if len(nonNone) >= 1 else []
        # 5y range — 최근 20 분기 또는 5 년 (annual) 의 min/max.
        rangeWindow = nonNone[-20:] if nonNone else []
        rangeMin = min(rangeWindow) if rangeWindow else None
        rangeMax = max(rangeWindow) if rangeWindow else None

        tile: dict[str, Any] = {
            "label": label,
            "value": last,
            "prev": prev,
            "unit": unit,
            "intent": intent,
            "subtitle": subtitle,
        }
        if sparkline:
            tile["sparkline"] = sparkline
        if rangeMin is not None:
            tile["rangeMin"] = rangeMin
        if rangeMax is not None:
            tile["rangeMax"] = rangeMax
        tiles.append(tile)
    return tiles


def _sumWeighted(norm: Any, terms: dict[str, int], periods: list[str]) -> list[float | None]:
    """compose / ratio 가산 — builder._sumWeighted 와 동일 로직 복제 (순환 import 회피)."""
    n = len(periods)
    if not terms:
        return [None] * n
    series_by_key = {k: extractSeries(norm, k, periods) for k in terms}
    out: list[float | None] = []
    for i in range(n):
        total = 0.0
        valid = False
        for k, sign in terms.items():
            v = series_by_key[k][i]
            if v is None:
                continue
            total += sign * float(v)
            valid = True
        out.append(total if valid else None)
    return out


def _lastTwo(arr: list[float | None]) -> tuple[float | None, float | None]:
    """마지막 2 개 비 None 값. (last, prev) — last 가 가장 최근."""
    last: float | None = None
    prev: float | None = None
    for v in reversed(arr):
        if v is None:
            continue
        if last is None:
            last = v
        else:
            prev = v
            break
    return last, prev


def buildDuPontRadar(norm: Any, periods: list[str]) -> dict[str, Any]:
    """DuPont 3-factor radar — 마지막 4 기간을 각 polygon 으로.

    axes: [순이익률 (%), 자산회전율 (회 ×100), 레버리지 (배 ×10)]
        scale 보정으로 3 축이 비슷한 magnitude → polar 가 한쪽에 쏠리지 않게.
    polygon: 마지막 4 기간 (당기·전기·1y 전·2y 전) — 시각적 시계열.

    Args:
        norm: 정규화 finance DataFrame.
        periods: 시간 라벨 list (마지막 = 최신).

    Returns:
        {categories: [axis label], series: [{key, label, color, data: [axis 값]}]}.
        data 모두 None 이면 호출자가 fallback.
    """
    if not periods:
        return {"categories": [], "series": []}

    npm = _sumWeighted(norm, {"netIncome": 1}, periods)
    rev = _sumWeighted(norm, {"revenue": 1}, periods)
    assets = _sumWeighted(norm, {"assets": 1}, periods)
    equity = _sumWeighted(norm, {"equity": 1}, periods)

    def _ratio(num: list[float | None], den: list[float | None], scale: float, i: int) -> float | None:
        n = num[i] if i < len(num) else None
        d = den[i] if i < len(den) else None
        if n is None or d is None or d == 0:
            return None
        return (n / d) * scale

    axesLabels = ["순이익률(%)", "자산회전(회×100)", "레버리지(배×10)"]

    sample = periods[-4:] if len(periods) >= 4 else periods
    palette = ["#dc2626", "#f97316", "#a78bfa", "#9ca3af"]
    series: list[dict[str, Any]] = []
    for offset, period in enumerate(sample):
        i = len(periods) - len(sample) + offset
        m = _ratio(npm, rev, 100, i)
        t = _ratio(rev, assets, 100, i)
        l = _ratio(assets, equity, 10, i)
        data = [m, t, l]
        if all(v is None for v in data):
            continue
        isCurrent = offset == len(sample) - 1
        series.append(
            {
                "key": f"p{offset}",
                "label": f"{period}{'(당기)' if isCurrent else ''}",
                "color": palette[len(sample) - 1 - offset]
                if (len(sample) - 1 - offset) < len(palette)
                else palette[-1],
                "data": data,
                "type": "radar",
                "unit": "",
            }
        )

    return {"categories": axesLabels, "series": series}


# ─────────────────────────────────────────────────────────────
# topList — analysis 함수가 list[str] 또는 list[dict] 반환.
# ─────────────────────────────────────────────────────────────


def buildTopListFromFlags(flags: Any) -> list[dict[str, Any]]:
    """analysis flags 함수 결과 (list[str] 또는 list[tuple] 또는 list[dict]) → TopListItem."""
    if not flags or not isinstance(flags, list):
        return []
    items: list[dict[str, Any]] = []
    for f in flags:
        if isinstance(f, str):
            items.append({"label": f, "value": None, "unit": "", "delta": None})
        elif isinstance(f, tuple) and len(f) >= 2:
            items.append({"label": str(f[0]), "description": str(f[1])})
        elif isinstance(f, dict):
            items.append(
                {
                    "label": str(f.get("label") or f.get("name") or f.get("key") or "?"),
                    "value": _toFloat(f.get("value") or f.get("score")),
                    "unit": f.get("unit", ""),
                    "delta": _toFloat(f.get("delta")),
                    "description": str(f.get("description", f.get("desc", ""))),
                }
            )
    return items


# ─────────────────────────────────────────────────────────────
# gauge — distress / Altman Z / Beneish M.
# ─────────────────────────────────────────────────────────────


def buildDistressGauge(company: Any) -> dict[str, Any]:
    """analysis의 단일 Z'' 원장에서 최신 점수와 임계값을 가져온다."""
    res = _safeCall("dartlab.analysis.financial._stabilityDistress", "calcDistressScore", company)
    if not isinstance(res, dict) or res.get("status") != "ok":
        return {}
    z = _toFloat(res.get("latestScore"))
    history = res.get("history") or []
    period = history[0].get("period") if history and isinstance(history[0], dict) else None
    if z is None:
        return {}
    minValue = min(-5.0, float(int(z) - 1))
    maxValue = max(10.0, float(int(z) + 2))
    return {
        "value": round(z, 2),
        "minValue": minValue,
        "maxValue": maxValue,
        "bands": [
            {"fromValue": minValue, "toValue": 1.1, "label": "위험", "intent": "negative"},
            {"fromValue": 1.1, "toValue": 2.6, "label": "주의", "intent": "accent"},
            {"fromValue": 2.6, "toValue": maxValue, "label": "안전", "intent": "positive"},
        ],
        "unit": "",
        "subtitle": f"Altman Z'' (비금융) · {period or '최신'} · >2.6 안전 / 1.1~2.6 회색 / <1.1 위험",
    }


def buildScenarioSensitivity(company: Any) -> dict[str, Any]:
    """매출 변동 × 마진 변동 → 영업이익 변동 % heatmap (P-DASH-V1 D15).

    base = 최근 기간 매출·영업이익률. 3×3 matrix:
        rev shifts:  -10% / 0% / +10%
        margin shifts: -2pp / 0 / +2pp

    각 cell = (base 영업이익 대비 변동 영업이익 - 1) × 100 %.

    Returns: {cells, rowOrder, colOrder, tone}.
    """
    norm, periods = _normAndPeriods(company, 4)
    if not periods:
        return {}
    p = periods[-1]
    rv = _toFloat(extractSeries(norm, "revenue", [p])[0]) or 0.0
    oi = _toFloat(extractSeries(norm, "operatingIncome", [p])[0]) or 0.0
    if rv <= 0 or oi <= 0:
        return {}
    baseMargin = oi / rv  # 0.xx
    revShifts = [("매출 -10%", -0.10), ("매출 0%", 0.0), ("매출 +10%", 0.10)]
    marginShifts = [("마진 -2pp", -0.02), ("마진 0", 0.0), ("마진 +2pp", 0.02)]
    cells: list[dict[str, Any]] = []
    for marginLabel, mShift in marginShifts:
        for revLabel, rShift in revShifts:
            newRev = rv * (1 + rShift)
            newMargin = baseMargin + mShift
            newOi = newRev * newMargin
            change = (newOi - oi) / oi * 100 if oi != 0 else 0.0
            cells.append(
                {
                    "row": marginLabel,
                    "col": revLabel,
                    "value": round(change, 1),
                    "unit": "%",
                }
            )
    return {
        "cells": cells,
        "rowOrder": [m for m, _ in marginShifts],
        "colOrder": [r for r, _ in revShifts],
        "tone": "diverging",
    }


def buildDistressDecomp(company: Any) -> dict[str, Any]:
    """단일 분석 원장의 Altman Z'' 4 인자 분해.

    각 인자 X1~X5 의 값 + 계수 가중 기여도 (점수에 얼마나 기여했는지).
    높은 절대 기여 인자가 분석 핵심.

    Returns:
        {items: [{label, value(인자값), unit, delta(가중 기여)}, ...]}
        기여도 절대값 내림차순 정렬.
    """
    res = _safeCall("dartlab.analysis.financial._stabilityDistress", "calcDistressScore", company)
    if not isinstance(res, dict) or res.get("status") != "ok":
        return {}
    history = res.get("history") or []
    latest = next((row for row in history if isinstance(row, dict) and row.get("zScore") is not None), None)
    if latest is None:
        return {}
    factors = [
        ("X1 운전자본/자산", _toFloat(latest.get("x1_wcTa")), 6.56),
        ("X2 이익잉여금/자산", _toFloat(latest.get("x2_reTa")), 3.26),
        ("X3 영업이익/자산", _toFloat(latest.get("x3_ebitTa")), 6.72),
        ("X4 장부자본/부채", _toFloat(latest.get("x4_bveTl")), 1.05),
    ]
    if any(value is None for _label, value, _coef in factors):
        return {}
    items = [
        {
            "label": label,
            "value": round(val, 3),
            "unit": "배",
            "delta": round(val * coef, 3),  # 가중 기여 (Z 에 대한)
            "description": f"× {coef} = {val * coef:.2f}",
        }
        for label, val, coef in factors
        if val is not None
    ]
    items.sort(key=lambda x: abs(x.get("delta") or 0.0), reverse=True)
    return {"items": items, "direction": "desc"}


def buildBeneishGauge(company: Any) -> dict[str, Any]:
    """Canonical 입력 계약이 복구될 때까지 Beneish gauge를 발행하지 않는다."""
    _ = company
    return {}


# ─────────────────────────────────────────────────────────────
# phaseIndicator — lifeCycle.calcLifeCycle.
# ─────────────────────────────────────────────────────────────

LIFE_CYCLE_PHASES = ["도입", "성장", "성숙Ⅰ", "성숙Ⅱ", "쇠퇴", "회복"]


def buildLifeCyclePhase(company: Any) -> dict[str, Any]:
    """CF 3축 부호 + 매출 성장률 + ROE 로 단계 추정 (Dickinson 모델 단순화).

    부호 패턴:
      CFO+ CFI- CFF+  → 도입 (성장 자금 확보)
      CFO+ CFI- CFF-  → 성장
      CFO+ CFI- CFF-  + 매출증가 둔화 → 성숙Ⅰ
      CFO+ CFI+ CFF-  → 성숙Ⅱ (자산 처분)
      CFO- CFI- CFF+  → 쇠퇴
      CFO+ CFI+ CFF+  → 회복 / 비정형
    """
    norm, periods = _normAndPeriods(company, 8)
    if len(periods) < 2:
        return {}
    p = periods[-1]
    cfo = _toFloat(extractSeries(norm, "cfOperating", [p])[0])
    cfi = _toFloat(extractSeries(norm, "cfInvesting", [p])[0])
    cff = _toFloat(extractSeries(norm, "cfFinancing", [p])[0])
    if cfo is None or cfi is None or cff is None:
        return {}
    # 매출 성장률.
    rev_series = [_toFloat(v) for v in extractSeries(norm, "revenue", periods)]
    growth = None
    if len(rev_series) >= 2 and rev_series[-2] not in (None, 0):
        growth = (rev_series[-1] - rev_series[-2]) / abs(rev_series[-2]) * 100
    # 단계 결정.
    sgn = (1 if cfo > 0 else -1, 1 if cfi > 0 else -1, 1 if cff > 0 else -1)
    if sgn == (1, -1, 1):
        idx = 0  # 도입
    elif sgn == (1, -1, -1):
        idx = 1 if (growth is not None and growth >= 10) else 2  # 성장 / 성숙Ⅰ
    elif sgn == (1, 1, -1):
        idx = 3  # 성숙Ⅱ
    elif cfo < 0:
        idx = 4  # 쇠퇴
    else:
        idx = 5  # 회복
    # 신뢰도 — 부호 차원 명확도 (절대값 / 자산).
    ta = _toFloat(extractSeries(norm, "assets", [p])[0]) or 1.0
    magnitude = (abs(cfo) + abs(cfi) + abs(cff)) / (3 * abs(ta))
    confidence = min(1.0, magnitude * 4)
    sgn_str = ("+" if cfo > 0 else "-") + ("+" if cfi > 0 else "-") + ("+" if cff > 0 else "-")
    subtitle = f"CFO{sgn_str[0]} CFI{sgn_str[1]} CFF{sgn_str[2]}"
    if growth is not None:
        subtitle += f" · 매출 YoY {growth:+.1f}%"
    return {
        "phases": LIFE_CYCLE_PHASES,
        "current": idx,
        "confidence": confidence,
        "subtitle": subtitle,
    }


# ─────────────────────────────────────────────────────────────
# sankey — 자본배분 (CFO → CapEx + 배당 + 부채상환 + 잉여)
# ─────────────────────────────────────────────────────────────


def buildCashflowAllocationSankey(norm: Any, periods: list[str]) -> dict[str, Any]:
    """[DEPRECATED — P-DASH-V1 D6] norm 마지막 기간 CFO 분해 sankey.

    Sankey 는 자본배분 시각화 표준 아니다 (Wall Street Prep / Damodaran).
    대안: capitalAllocationBars (stacked over time) · capitalAllocationWaterfall (단년).
    본 함수는 backward-compat 용 — catalog 의 sankey 카드는 D6 에서 폐기됨.
    """
    if not periods:
        return {}
    last = periods[-1]
    cfo = extractSeries(norm, "cfOperating", [last])[0]
    capex_raw = extractSeries(norm, "capex", [last])[0]
    dividends_raw = extractSeries(norm, "dividendsPaid", [last])[0]
    cfo_v = _toFloat(cfo) or 0.0
    capex = abs(_toFloat(capex_raw) or 0.0)
    dividends = abs(_toFloat(dividends_raw) or 0.0)
    if cfo_v <= 0:
        return {}
    used = min(capex + dividends, cfo_v)
    surplus = max(cfo_v - used, 0.0)
    nodes = [{"name": "영업현금흐름"}, {"name": "설비투자"}, {"name": "배당"}, {"name": "잉여"}]
    links: list[dict[str, Any]] = []
    if capex > 0:
        links.append({"source": 0, "target": 1, "value": capex})
    if dividends > 0:
        links.append({"source": 0, "target": 2, "value": dividends})
    if surplus > 0:
        links.append({"source": 0, "target": 3, "value": surplus})
    if not links:
        return {}
    return {"nodes": nodes, "links": links}


# ─────────────────────────────────────────────────────────────
# 자본배분 — stacked bar over time + waterfall (sankey 대체).
# Wall Street Prep / Damodaran 정통 시각화.
# ─────────────────────────────────────────────────────────────


def buildCapitalAllocationBars(norm: Any, periods: list[str]) -> dict[str, Any]:
    """연도 × {CapEx · 배당 · 부채상환 · 잉여} stacked bar 시계열.

    Returns:
        {seriesPlan-like: [series with data list]}  builder 가 view.series 에 박음.

    Buckets:
        - capEx (음수→양수 변환, intent=negative): -capex
        - dividends (intent=accent): -dividendsPaid
        - debtRepay (intent=negative): -cfFinancing 중 부채 부분 (근사)
        - surplus (intent=positive): max(cfOperating - 사용처, 0)

    데이터 부족 시 빈 dict.
    """
    if not periods or len(periods) < 2:
        return {}

    capexSeries: list[float | None] = []
    divSeries: list[float | None] = []
    debtRepaySeries: list[float | None] = []
    surplusSeries: list[float | None] = []

    cfoVals = extractSeries(norm, "cfOperating", periods)
    capexVals = extractSeries(norm, "capex", periods)
    divVals = extractSeries(norm, "dividendsPaid", periods)
    cffVals = extractSeries(norm, "cfFinancing", periods)

    for i in range(len(periods)):
        cfo = _toFloat(cfoVals[i]) or 0.0
        capex = abs(_toFloat(capexVals[i]) or 0.0)
        div = abs(_toFloat(divVals[i]) or 0.0)
        cff = _toFloat(cffVals[i]) or 0.0
        # 부채상환 = 음수 재무CF − 배당 (배당도 재무CF 음수에 포함되어있을 가능성).
        debtRepay = max(-cff - div, 0.0) if cff < 0 else 0.0
        used = capex + div + debtRepay
        surplus = max(cfo - used, 0.0)
        capexSeries.append(capex if capex > 0 else None)
        divSeries.append(div if div > 0 else None)
        debtRepaySeries.append(debtRepay if debtRepay > 0 else None)
        surplusSeries.append(surplus if surplus > 0 else None)

    # 모든 시리즈가 None 일 가능성 — 데이터 0.
    nonNone = sum(1 for s in (capexSeries, divSeries, debtRepaySeries, surplusSeries) for v in s if v is not None)
    if nonNone == 0:
        return {}

    # ChartContainer + Bar stack 으로 그릴 series list 반환.
    # finance.py 의 색 코드 (COLORS) 직접 import 회피 — render 가 palette 적용.
    return {
        "series": [
            {
                "key": "capex",
                "label": "설비투자",
                "intent": "negative",
                "unit": "원",
                "type": "bar",
                "stack": "alloc",
                "data": capexSeries,
            },
            {
                "key": "dividends",
                "label": "배당",
                "intent": "accent",
                "unit": "원",
                "type": "bar",
                "stack": "alloc",
                "data": divSeries,
            },
            {
                "key": "debtRepay",
                "label": "부채상환",
                "intent": "neutral",
                "unit": "원",
                "type": "bar",
                "stack": "alloc",
                "data": debtRepaySeries,
            },
            {
                "key": "surplus",
                "label": "잉여",
                "intent": "positive",
                "unit": "원",
                "type": "bar",
                "stack": "alloc",
                "data": surplusSeries,
            },
        ],
    }


def buildCapitalAllocationWaterfall(norm: Any, periods: list[str]) -> dict[str, Any]:
    """단년 자본배분 waterfall — 영업CF → -CapEx → -배당 → -부채상환 → ΔCash.

    Returns 마지막 기간 분해. 데이터 부족 시 빈 dict.

    series 1 개 — recharts BarChart 가 measure 메타로 absolute/relative 분리.
    """
    if not periods:
        return {}
    last = periods[-1]
    cfo = _toFloat(extractSeries(norm, "cfOperating", [last])[0]) or 0.0
    capex = abs(_toFloat(extractSeries(norm, "capex", [last])[0]) or 0.0)
    div = abs(_toFloat(extractSeries(norm, "dividendsPaid", [last])[0]) or 0.0)
    cff = _toFloat(extractSeries(norm, "cfFinancing", [last])[0]) or 0.0
    debtRepay = max(-cff - div, 0.0) if cff < 0 else 0.0
    surplus = cfo - capex - div - debtRepay

    if cfo <= 0:
        return {}

    # categories + points (measure 메타).
    categories = ["영업CF", "-설비투자", "-배당", "-부채상환", "잉여"]
    points = [
        {"value": cfo, "measure": "absolute"},
        {"value": -capex if capex > 0 else 0.0, "measure": "relative"},
        {"value": -div if div > 0 else 0.0, "measure": "relative"},
        {"value": -debtRepay if debtRepay > 0 else 0.0, "measure": "relative"},
        {"value": surplus, "measure": "total"},
    ]
    return {
        "categories": categories,
        "series": [
            {
                "key": "waterfall",
                "label": "자본배분 waterfall",
                "unit": "원",
                "type": "bar",
                "points": points,
                "data": [p["value"] for p in points],
            }
        ],
    }


# ─────────────────────────────────────────────────────────────
# scatter — peerBenchmark 4사분면.
# ─────────────────────────────────────────────────────────────


def buildPeerScatter(company: Any) -> dict[str, Any]:
    """norm 으로 회사의 최근 8 기간 (ROE, 부채비율) 점들 + 최근값 self 표시.

    동종 데이터 wiring 은 후속 (peerBenchmark). 현재는 회사 자체 시간축 산점도.
    각 기간이 하나의 점, 최근 기간이 self (별표).
    """
    norm, periods = _normAndPeriods(company, 12)
    if len(periods) < 2:
        return {}
    points: list[dict[str, Any]] = []
    for p in periods:
        ni = _toFloat(extractSeries(norm, "netIncome", [p])[0])
        eq = _toFloat(extractSeries(norm, "equity", [p])[0])
        tl = _toFloat(extractSeries(norm, "liabilities", [p])[0])
        if ni is None or eq is None or tl is None or eq <= 0:
            continue
        roe = ni / eq * 100
        de = tl / eq * 100
        points.append({"x": roe, "y": de, "label": p, "self": p == periods[-1]})
    if not points:
        return {}
    # 참조선 = 시계열 중앙값.
    sorted_x = sorted(p["x"] for p in points)
    sorted_y = sorted(p["y"] for p in points)
    median_x = sorted_x[len(sorted_x) // 2]
    median_y = sorted_y[len(sorted_y) // 2]
    return {
        "points": points,
        "xLabel": "ROE",
        "yLabel": "부채비율",
        "xUnit": "%",
        "yUnit": "%",
        "xRef": round(median_x, 2),
        "yRef": round(median_y, 2),
    }


def buildPeerComparison(company: Any) -> dict[str, Any]:
    """norm 의 최근값 vs 회사 자체 5년 중앙값 (peer median 자리 대체).

    동종 wiring 후속. 현재는 회사 시계열의 분포 (자신과 자기 중앙값 비교).
    """
    norm, periods = _normAndPeriods(company, 12)
    if len(periods) < 3:
        return {}

    def _series(numTerms, denTerms, scale):
        out = []
        for p in periods:
            n = _sumWeighted(norm, numTerms, [p])[0] if numTerms else None
            d = _sumWeighted(norm, denTerms, [p])[0] if denTerms else None
            if n is None or d is None or d == 0:
                out.append(None)
            else:
                out.append(n / d * scale)
        return out

    def _percentile(vals: list[float], v: float) -> float:
        sorted_v = sorted(vals)
        if not sorted_v:
            return 50.0
        below = sum(1 for x in sorted_v if x < v)
        return round(below / len(sorted_v) * 100, 1)

    metrics = [
        ("매출총이익률", {"grossProfit": 1}, {"revenue": 1}, 100, "%", True),
        ("영업이익률", {"operatingIncome": 1}, {"revenue": 1}, 100, "%", True),
        ("ROE", {"netIncome": 1}, {"equity": 1}, 100, "%", True),
        ("ROA", {"netIncome": 1}, {"assets": 1}, 100, "%", True),
        ("부채비율", {"liabilities": 1}, {"equity": 1}, 100, "%", False),
        ("유동비율", {"currentAssets": 1}, {"currentLiabilities": 1}, 100, "%", True),
        ("자산회전율", {"revenue": 1}, {"assets": 1}, 1, "회", True),
        ("영업CF/매출", {"cfOperating": 1}, {"revenue": 1}, 100, "%", True),
    ]
    rows: list[dict[str, Any]] = []
    for label, num, den, scale, unit, higher in metrics:
        series = _series(num, den, scale)
        non_null = [v for v in series if v is not None]
        if len(non_null) < 2:
            continue
        latest = series[-1]
        if latest is None:
            continue
        sorted_v = sorted(non_null)
        median = sorted_v[len(sorted_v) // 2]
        p25 = sorted_v[len(sorted_v) // 4]
        p75 = sorted_v[(3 * len(sorted_v)) // 4]
        pct = _percentile(non_null, latest) if higher else (100 - _percentile(non_null, latest))
        rows.append(
            {
                "label": label,
                "self": round(latest, 2),
                "peerMedian": round(median, 2),
                "peerP25": round(p25, 2),
                "peerP75": round(p75, 2),
                "percentile": pct,
                "unit": unit,
                "higherIsBetter": higher,
            }
        )
    if not rows:
        return {}
    return {"rows": rows, "peerCount": len(periods)}


def buildAnomalyTopList(company: Any) -> list[dict[str, Any]]:
    """전년 대비 변동 큰 지표 top 5 — 변동 절대값 기준 정렬.

    경고성 (large change) + 정상 (small change) 모두 표시. 임계 기반 hard cut 폐기.
    """
    norm, periods = _normAndPeriods(company, 4)
    if len(periods) < 2:
        return []

    def _ratio(num: dict, den: dict, p: str) -> float | None:
        n = _sumWeighted(norm, num, [p])[0]
        d = _sumWeighted(norm, den, [p])[0]
        if n is None or d is None or d == 0:
            return None
        return n / d

    last = periods[-1]
    prev = periods[-2]
    metrics = [
        ("DSO (매출채권 회수일수)", {"receivables": 365}, {"revenue": 1}, "일"),
        ("DIO (재고자산 회수일수)", {"inventories": 365}, {"costOfSales": 1}, "일"),
        ("매출원가율", {"costOfSales": 1}, {"revenue": 1}, "%"),
        ("판관비율", {"sga": 1}, {"revenue": 1}, "%"),
        ("영업CF/순이익", {"cfOperating": 1}, {"netIncome": 1}, "%"),
        ("부채자본비율", {"liabilities": 1}, {"equity": 1}, "%"),
        ("유동비율", {"currentAssets": 1}, {"currentLiabilities": 1}, "%"),
        ("재고/자산", {"inventories": 1}, {"assets": 1}, "%"),
    ]
    items: list[dict[str, Any]] = []
    for label, num, den, unit in metrics:
        l = _ratio(num, den, last)
        p = _ratio(num, den, prev)
        if l is None or p is None or p == 0:
            continue
        delta_pct = (l - p) / abs(p) * 100
        scale = 1 if unit == "일" else 100
        l_disp = l * scale
        p_disp = p * scale
        items.append(
            {
                "label": label,
                "value": round(l_disp, 1),
                "unit": unit,
                "delta": round(delta_pct, 1),
                "description": f"{p_disp:.1f} → {l_disp:.1f} {unit} ({delta_pct:+.1f}% YoY)",
                "_abs_delta": abs(delta_pct),
            }
        )
    # 변동 절대값 기준 top 5.
    items.sort(key=lambda x: x.pop("_abs_delta", 0), reverse=True)
    return items[:6]


_ACT_LABELS = ["1막 사업", "2막 수익", "3막 현금", "4막 안정", "5막 배분", "6막 미래"]


def buildNarrativeBridge(company: Any) -> dict[str, Any]:
    """Story view 6 막 전환 자연어 — `story.narrative.buildActTransitions` 5 줄 + 종합 1 줄.

    Returns:
        {transitions: [{from, to, text}, ...], summaryLine: str}.
        engine 호출 실패하면 빈 transitions 반환 (renderer 가 placeholder 표시).
    """
    transitions: list[dict[str, str]] = []
    summary = ""
    try:
        from dartlab.story import narrative as _narr

        tdict = _narr.buildActTransitions(company) or {}
        for i in range(1, 6):
            key = f"{i}→{i + 1}"
            text = tdict.get(key, "")
            if not text:
                continue
            transitions.append(
                {
                    "from": _ACT_LABELS[i - 1],
                    "to": _ACT_LABELS[i],
                    "text": text,
                }
            )
        try:
            # 여기서는 블록맵이 없다. 예전 코드도 company._blockMap 을 읽었지만 그 이름이
            # Company 에 없어 늘 빈 dict 였다. 블록을 보는 detector 는 그대로 건너뛴다.
            threads = _narr.detectThreads(company, {}) or []
            summary = _narr.buildCirculationSummary(threads) or ""
        except (AttributeError, ValueError, TypeError):
            summary = ""
    except (ImportError, AttributeError, ValueError, TypeError):
        pass
    return {"transitions": transitions, "summaryLine": summary}


_GRADE_BUCKETS = [
    (90, "A+"),
    (80, "A"),
    (70, "B+"),
    (60, "B"),
    (50, "C+"),
    (40, "C"),
    (0, "D"),
]


def buildSnowflakeAlert(company: Any) -> dict[str, Any]:
    """Snowflake alert — 회계 기반 측정 한계 안내 1 줄.

    radar / scoreBadge 가 시장가 의존 metric 폐기 후 회계 대체임을 운영자에게 노출.
    """
    return {
        "transitions": [
            {
                "from": "측정 한계",
                "to": "회계 기반",
                "text": (
                    "시장가 의존 metric (PER/PBR/배당수익률) → 회계 대체로 정규화. "
                    "Owner Earnings Yield · 매출 CAGR3y · ROE+ROA+ROIC · Piotroski F-Score · 배당성향+RE 누적."
                ),
            },
            {
                "from": "정통 Simply Wall St",
                "to": "dartlab 회계 기반",
                "text": (
                    "Simply Wall St 의 시가총액 의존 5 차원과는 점수 분포 다름. 회계 정보만으로 가치/성장/안전 평가."
                ),
            },
        ],
        "summaryLine": "회계 기반 5 차원 — 시장가 부재 환경의 합성 평점",
    }


def buildSnowflakeKpi(company: Any, tilePlans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Snowflake 단일 차원 KPI — tilePlan.dim 별 0~5 점.

    intrinsic.calcSnowflake5Score 한 번 호출 + 각 tilePlan 의 dim 값 추출.
    """
    try:
        from dartlab.analysis.financial import intrinsic as _intr

        scores = _intr.calcSnowflake5Score(company) or {}
    except (ImportError, AttributeError, ValueError, TypeError):
        scores = {}
    tiles: list[dict[str, Any]] = []
    for plan in tilePlans or []:
        dim = plan.get("dim", "")
        val = scores.get(dim)
        if isinstance(val, (int, float)):
            value: float | None = float(val)
        else:
            value = None
        tiles.append(
            {
                "label": plan.get("label", dim),
                "value": value,
                "prev": None,
                "unit": plan.get("unit", "점"),
                "intent": plan.get("intent", "primary"),
                "sparkline": [],
            }
        )
    return tiles


def buildScoreBadge(company: Any) -> dict[str, Any]:
    """Snowflake 종합 평점 카드 — 5 차원 점수 × 20 평균 → grade + 한 줄 서사."""
    try:
        from dartlab.analysis.financial import intrinsic as _intr

        scores = _intr.calcSnowflake5Score(company) or {}
    except (ImportError, AttributeError, ValueError, TypeError):
        scores = {}
    dims = [
        ("value", "Value"),
        ("future", "Future"),
        ("past", "Past"),
        ("health", "Health"),
        ("dividend", "Dividend"),
    ]
    dimList = [{"key": k, "label": label, "score": float(scores.get(k, 0) or 0)} for k, label in dims]
    vals = [d["score"] for d in dimList if isinstance(d["score"], (int, float))]
    if vals:
        overall = sum(vals) / len(vals) * 20.0
    else:
        overall = 0.0
    grade = "D"
    for cut, g in _GRADE_BUCKETS:
        if overall >= cut:
            grade = g
            break
    parts = " · ".join(f"{d['label']} {d['score']:.1f}/5" for d in dimList)
    summaryLine = f"{parts} — 종합 {overall:.0f}점 ({grade})"
    return {
        "grade": grade,
        "overallScore": round(overall, 1),
        "dimensions": dimList,
        "summaryLine": summaryLine,
    }


# ─────────────────────────────────────────────────────────────
# 정통 깊이 강화 adapter 6 (2026-05-19) — analysis 엔진 시계열 wrapping.
# Penman ROE 분해 / ROIC-WACC spread / 세그먼트 매출 / 세그먼트 집중도 /
# Operating Leverage·Breakeven / Distress 모델 ensemble.
# ─────────────────────────────────────────────────────────────


def buildPenmanRoeBars(company: Any) -> dict[str, Any]:
    """calcPenmanDecomposition → RNOA + LeverageEffect stacked + ROCE line.

    ROCE = RNOA + FLEV × SPREAD. RNOA 가 영업 동력, leverageEffect (= FLEV × SPREAD)
    가 부채 효과. 두 stack 합산이 ROCE.
    """
    res = _safeCall("dartlab.analysis.financial._profitabilityDeep", "calcPenmanDecomposition", company)
    history = _drill(res, "history") if isinstance(res, dict) else None
    if not isinstance(history, list) or len(history) < 1:
        return {}
    periods: list[str] = []
    rnoa: list[float | None] = []
    levEffect: list[float | None] = []
    roce: list[float | None] = []
    for row in history:
        if not isinstance(row, dict):
            continue
        periods.append(str(row.get("period", "")))
        rnoa.append(_toFloat(row.get("rnoa")))
        levEffect.append(_toFloat(row.get("leverageEffect")))
        roce.append(_toFloat(row.get("roce")))
    if not periods:
        return {}
    return {
        "categories": periods,
        "series": [
            {
                "key": "rnoa",
                "label": "영업력 (RNOA)",
                "color": "var(--chart-2)",
                "intent": "primary",
                "unit": "%",
                "type": "bar",
                "stack": "roce",
                "data": rnoa,
            },
            {
                "key": "leverageEffect",
                "label": "레버리지 효과",
                "color": "var(--chart-4)",
                "intent": "accent",
                "unit": "%",
                "type": "bar",
                "stack": "roce",
                "data": levEffect,
            },
            {
                "key": "roce",
                "label": "ROCE 합산",
                "color": "var(--chart-1)",
                "intent": "primary",
                "unit": "%",
                "type": "line",
                "data": roce,
            },
        ],
    }


def buildRoicWaccGap(company: Any) -> dict[str, Any]:
    """calcRoicTimeline → ROIC line + WACC 8% 가정 + spread bar (양수 가치창출 / 음수 자본파괴).

    spread = ROIC − WACC. WACC 단순 가정 (Damodaran 한국 평균 7~9% → 8%). 정밀 WACC
    필요 시 후속 PR (CAPM β·rf·equity risk premium 산출).
    """
    res = _safeCall("dartlab.analysis.financial._investmentAnalysisRoic", "calcRoicTimeline", company)
    history = _drill(res, "history") if isinstance(res, dict) else None
    if not isinstance(history, list) or len(history) < 1:
        return {}
    WACC = 8.0
    periods: list[str] = []
    roicList: list[float | None] = []
    waccList: list[float | None] = []
    spreadList: list[float | None] = []
    for row in history:
        if not isinstance(row, dict):
            continue
        period = row.get("period")
        if period is None:
            continue
        periods.append(str(period))
        roic = _toFloat(row.get("roic"))
        roicList.append(roic)
        waccList.append(WACC)
        spreadList.append(roic - WACC if roic is not None else None)
    if not periods:
        return {}
    return {
        "categories": periods,
        "series": [
            {
                "key": "roic",
                "label": "ROIC",
                "color": "var(--chart-1)",
                "intent": "primary",
                "unit": "%",
                "type": "line",
                "data": roicList,
            },
            {
                "key": "wacc",
                "label": "WACC (≈8%)",
                "color": "var(--chart-4)",
                "intent": "neutral",
                "unit": "%",
                "type": "line",
                "data": waccList,
            },
            {
                "key": "spread",
                "label": "Spread (ROIC−WACC)",
                "color": "var(--chart-5)",
                "intent": "positive",
                "unit": "%p",
                "type": "bar",
                "data": spreadList,
            },
        ],
    }


def buildSegmentBreakdown(company: Any) -> dict[str, Any]:
    """calcSegmentTrend → 부문별 매출 stacked bar.

    top 6 부문만 (`_MAX_SEGMENTS` 정통). 영업이익률 별도 색 라인은 부문 ×
    line 폭증 — 매출 stack 만 노출하고 영업이익률 추세는 별도 카드.
    """
    res = _safeCall("dartlab.analysis.financial._revenueSegment", "calcSegmentTrend", company)
    if not isinstance(res, dict):
        return {}
    yearCols = res.get("yearCols") or []
    rows = res.get("rows") or []
    if not yearCols or not rows:
        return {}
    # period 역순 정렬 (yearCols 가 최신→과거 라 시각화는 과거→최신)
    periods = list(reversed(yearCols))
    palette = [f"var(--chart-{i})" for i in (2, 3, 5, 6, 7, 8)]
    series: list[dict[str, Any]] = []
    for idx, row in enumerate(rows[:6]):
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or f"부문 {idx + 1}")
        values = row.get("values") or {}
        data = [_toFloat(values.get(p)) for p in periods]
        if all(v is None for v in data):
            continue
        series.append(
            {
                "key": f"seg{idx}",
                "label": name,
                "color": palette[idx % len(palette)],
                "intent": "primary" if idx == 0 else "accent",
                "unit": "원",
                "type": "bar",
                "stack": "segment",
                "data": data,
            }
        )
    if not series:
        return {}
    return {"categories": periods, "series": series}


def buildSegmentConcentration(company: Any) -> dict[str, Any]:
    """calcConcentration → HHI 시계열 line + 최대 부문 비중 line.

    HHI > 5000 = 고집중 (단일 사업 위험). topPct = 최대 부문 매출 비중.
    """
    res = _safeCall("dartlab.analysis.financial._revenueGrowth", "calcConcentration", company)
    if not isinstance(res, dict):
        return {}
    hhiHistory = res.get("hhiHistory") or []
    if not isinstance(hhiHistory, list) or len(hhiHistory) < 1:
        # fallback — 단일 시점만 있을 때
        hhi = _toFloat(res.get("hhi"))
        topPct = _toFloat(res.get("topPct"))
        if hhi is None and topPct is None:
            return {}
        return {
            "categories": ["최신"],
            "series": [
                {
                    "key": "hhi",
                    "label": "HHI 집중도",
                    "color": "var(--chart-3)",
                    "intent": "negative",
                    "unit": "",
                    "type": "line",
                    "data": [hhi],
                },
                {
                    "key": "topPct",
                    "label": "1위 부문 비중",
                    "color": "var(--chart-2)",
                    "intent": "accent",
                    "unit": "%",
                    "type": "line",
                    "axis": "right",
                    "data": [topPct],
                },
            ],
        }
    periods: list[str] = []
    hhiList: list[float | None] = []
    for row in hhiHistory:
        if not isinstance(row, dict):
            continue
        # calcConcentration uses "year" key (not "period"). topPct 은 history 행에 없어 시계열 series 생략.
        periods.append(str(row.get("year") or row.get("period") or ""))
        hhiList.append(_toFloat(row.get("hhi")))
    # 오래된 → 최신 순서 강제 (calcConcentration 은 newest first)
    if periods and len(periods) > 1 and periods[0] > periods[-1]:
        periods.reverse()
        hhiList.reverse()
    if not periods:
        return {}
    topPctNow = _toFloat(res.get("topPct"))
    label = f"HHI 집중도 (현재 1위 {topPctNow:.1f}%)" if topPctNow is not None else "HHI 집중도"
    return {
        "categories": periods,
        "series": [
            {
                "key": "hhi",
                "label": label,
                "color": "var(--chart-3)",
                "intent": "negative",
                "unit": "",
                "type": "line",
                "data": hhiList,
            },
        ],
        "options": {
            "refLines": [
                {"value": 2500, "label": "2500 (보통)", "intent": "neutral"},
                {"value": 5000, "label": "5000 (고집중)", "intent": "negative"},
            ],
        },
    }


def buildDolBreakeven(company: Any) -> dict[str, Any]:
    """calcOperatingLeverage + calcBreakevenEstimate → DOL bar + 안전마진 line.

    DOL (영업레버리지) 클수록 매출 변동에 영업이익 민감. 안전마진 = (매출 − BEP)/매출 ×100.
    """
    dol_res = _safeCall("dartlab.analysis.financial.costStructure", "calcOperatingLeverage", company)
    bep_res = _safeCall("dartlab.analysis.financial.costStructure", "calcBreakevenEstimate", company)
    dolHistory = _drill(dol_res, "history") if isinstance(dol_res, dict) else None
    bepHistory = _drill(bep_res, "history") if isinstance(bep_res, dict) else None
    if not isinstance(dolHistory, list):
        dolHistory = []
    if not isinstance(bepHistory, list):
        bepHistory = []
    if not dolHistory and not bepHistory:
        return {}
    periodSet: list[str] = []
    seen: set[str] = set()
    for row in dolHistory:
        if isinstance(row, dict):
            p = str(row.get("period", ""))
            if p and p not in seen:
                periodSet.append(p)
                seen.add(p)
    for row in bepHistory:
        if isinstance(row, dict):
            p = str(row.get("period", ""))
            if p and p not in seen:
                periodSet.append(p)
                seen.add(p)
    if not periodSet:
        return {}
    # 과거 → 최신 (정통 분석 시각화 방향)
    periods = sorted(periodSet)
    dolLookup = {str(row.get("period", "")): _toFloat(row.get("dol")) for row in dolHistory if isinstance(row, dict)}
    safetyLookup = {
        str(row.get("period", "")): _toFloat(row.get("marginOfSafety")) for row in bepHistory if isinstance(row, dict)
    }
    return {
        "categories": periods,
        "series": [
            {
                "key": "dol",
                "label": "영업레버리지 (DOL)",
                "color": "var(--chart-2)",
                "intent": "accent",
                "unit": "배",
                "type": "bar",
                "data": [dolLookup.get(p) for p in periods],
            },
            {
                "key": "marginOfSafety",
                "label": "안전마진",
                "color": "var(--chart-5)",
                "intent": "positive",
                "unit": "%",
                "type": "line",
                "axis": "right",
                "data": [safetyLookup.get(p) for p in periods],
            },
        ],
    }


def buildDistressEnsembleGauge(company: Any) -> dict[str, Any]:
    """calcDistressEnsemble → Altman 계열 한 표 + 적용 가능 모델 다수결 gauge.

    agreement (다수파 일치도, %) 를 gauge value 로. ensemble label ("안전"|"주의"|"위험")
    + 모델별 verdict 카운트는 subtitle.
    """
    res = _safeCall("dartlab.analysis.financial._stabilityDistress", "calcDistressEnsemble", company)
    if not isinstance(res, dict):
        return {}
    agreement = _toFloat(res.get("agreement"))
    ensemble = res.get("ensemble") or ""
    safeCount = res.get("safeCount") or 0
    dangerCount = res.get("dangerCount") or 0
    total = res.get("total") or 0
    if agreement is None or not total:
        return {}
    # ensemble label 별 invert: "안전" 이면 agreement 높을수록 좋음, "위험" 이면 agreement 높을수록 나쁨.
    # gauge value = 안전 확신도 (safeCount/total × 100). 0~100 단순.
    safetyScore = safeCount / total * 100 if total > 0 else None
    if safetyScore is None:
        return {}
    return {
        "value": round(safetyScore, 1),
        "minValue": 0.0,
        "maxValue": 100.0,
        "bands": [
            {"fromValue": 0.0, "toValue": 30.0, "label": "위험", "intent": "negative"},
            {"fromValue": 30.0, "toValue": 60.0, "label": "주의", "intent": "accent"},
            {"fromValue": 60.0, "toValue": 100.0, "label": "안전", "intent": "positive"},
        ],
        "unit": "%",
        "subtitle": f"적용 모델 {total}개 다수결 — {ensemble} · 안전 {safeCount}/{total} · 위험 {dangerCount}/{total} · 일치도 {agreement:.0f}%",
    }


def buildSnowflakeRadar(company: Any) -> dict[str, Any]:
    """5 정통 axis 0~10 점수 radar — Simply Wall St "Snowflake" 패턴.

    각 axis 절대 임계값 (peer 불필요, industry-agnostic):
      - 수익성   ROE %               : 0/5/10/15/20 → 0/3/6/8/10p
      - 자본효율 ROIC %              : 동일
      - 안정성   자기자본/자산 %     : 0/20/40/60/80
      - 유동성   유동비율 (배)       : 0.5/1.0/1.5/2.0/3.0
      - 현금흐름 FCF/매출 %          : -5/0/5/10/15

    최근 4 분기 평균 (단일 분기 노이즈 흡수). 데이터 부족 axis 는 0p 처리 (radar 표시).
    회사 강·약점이 한 장에 보임.
    """
    from dartlab.viz.display.finance.accounts import extractSeries

    norm, periods = _normAndPeriods(company, 4, "quarterly")
    if not periods:
        return {}

    def _avg(values: list[float | None]) -> float | None:
        valid = [v for v in values if v is not None]
        return sum(valid) / len(valid) if valid else None

    def _ratio(numKey: str, denKey: str, scale: float = 100.0) -> float | None:
        num = extractSeries(norm, numKey, periods)
        den = extractSeries(norm, denKey, periods)
        outs = []
        for n, d in zip(num, den):
            if n is not None and d is not None and d != 0:
                outs.append(n / d * scale)
        return _avg(outs) if outs else None

    def _score(v: float | None, points: list[tuple[float, float]]) -> float | None:
        if v is None:
            return None
        if v <= points[0][0]:
            return points[0][1]
        if v >= points[-1][0]:
            return points[-1][1]
        for i in range(len(points) - 1):
            v0, s0 = points[i]
            v1, s1 = points[i + 1]
            if v0 <= v <= v1:
                return round(s0 + (v - v0) / (v1 - v0) * (s1 - s0), 1)
        return None

    roe = _ratio("netIncome", "equity")
    roicRes = _safeCall("dartlab.analysis.financial._investmentAnalysisRoic", "calcRoicTimeline", company)
    roicHist = _drill(roicRes, "history") if isinstance(roicRes, dict) else None
    roicValues: list[float] = []
    if isinstance(roicHist, list):
        for row in roicHist[-4:]:
            if isinstance(row, dict):
                v = _toFloat(row.get("roic") or row.get("value"))
                if v is not None:
                    roicValues.append(v)
    roic = _avg(roicValues) if roicValues else None
    equityRatio = _ratio("equity", "assets")
    currentRatio = _ratio("currentAssets", "currentLiabilities", scale=1.0)
    # 표준 28 계정 키 = "cfOperating" / "capex" / "revenue".
    ocf = extractSeries(norm, "cfOperating", periods)
    capex = extractSeries(norm, "capex", periods)
    revenue = extractSeries(norm, "revenue", periods)
    fcfMargins: list[float] = []
    for o, c, r in zip(ocf, capex, revenue):
        if o is not None and c is not None and r is not None and r != 0:
            fcfMargins.append((o - abs(c)) / r * 100)
    fcfMargin = _avg(fcfMargins) if fcfMargins else None

    axes = [
        ("수익성 (ROE)", roe, [(0, 0), (5, 3), (10, 6), (15, 8), (20, 10)], "%"),
        ("자본효율 (ROIC)", roic, [(0, 0), (5, 3), (10, 6), (15, 8), (20, 10)], "%"),
        ("안정성 (자기자본/자산)", equityRatio, [(0, 0), (20, 3), (40, 6), (60, 8), (80, 10)], "%"),
        ("유동성 (유동비율)", currentRatio, [(0.5, 0), (1.0, 3), (1.5, 6), (2.0, 8), (3.0, 10)], "배"),
        ("현금흐름 (FCF/매출)", fcfMargin, [(-5, 0), (0, 3), (5, 6), (10, 8), (15, 10)], "%"),
    ]
    categories = [a[0] for a in axes]
    scores = [_score(a[1], a[2]) for a in axes]
    rawValues = [a[1] for a in axes]
    rawUnits = [a[3] for a in axes]
    return {
        "categories": categories,
        "series": [
            {
                "key": "score",
                "label": "점수 (0~10)",
                "color": "var(--chart-2)",
                "type": "radar",
                "data": [s if s is not None else 0 for s in scores],
                "unit": "점",
                "intent": "primary",
            },
        ],
        "options": {
            "rawValues": rawValues,
            "rawUnits": rawUnits,
            "max": 10,
        },
    }


__all__ = [
    "LIFE_CYCLE_PHASES",
    "buildBeneishGauge",
    "buildCapitalAllocationBars",
    "buildCapitalAllocationWaterfall",
    "buildCashflowAllocationSankey",
    "buildDistressDecomp",
    "buildDistressEnsembleGauge",
    "buildDistressGauge",
    "buildDolBreakeven",
    "buildKpiTilesFromNorm",
    "buildLifeCyclePhase",
    "buildNarrativeBridge",
    "buildPeerComparison",
    "buildPeerScatter",
    "buildPenmanRoeBars",
    "buildRoicWaccGap",
    "buildScenarioSensitivity",
    "buildScoreBadge",
    "buildSegmentBreakdown",
    "buildSnowflakeRadar",
    "buildSegmentConcentration",
    "buildSnowflakeAlert",
    "buildSnowflakeKpi",
    "buildSnowflakeRadar",
    "buildTopListFromFlags",
    # quant 탭 adapter (가격·기술·모멘텀·변동성·베타·예측·placeholder + RSI/MACD sub-pane).
    "buildQuantPriceTrend",
    "buildQuantRsiTrend",
    "buildQuantMacdTrend",
    "buildQuantVerdictKpi",
    "buildQuantMomentumKpi",
    "buildQuantVolatilityKpi",
    "buildQuantBetaKpi",
    "buildQuantForecastKpi",
    "buildQuantComingSoon",
    # backtest 6 카드 (8 style 일괄 backtest 1 회 + cache).
    "buildQuantEquityCurve",
    "buildQuantDrawdownChart",
    "buildQuantMonthlyHeatmap",
    "buildQuantStyleMatrix",
    "buildQuantRollingSharpe",
    "buildQuantAnnualReturns",
    # risk 4 카드.
    "buildQuantBetaScatter",
    "buildQuantVolatilityTerm",
    "buildQuantDrawdownDistribution",
    "buildQuantSnowflakeRadar",
    # forecast 3 카드 (이벤트 스터디는 후행).
    "buildQuantForecastFan",
    "buildQuantMonteCarloPaths",
    "buildQuantRegimePhase",
]


# ─────────────────────────────────────────────────────────────
# quant 탭 어댑터 — dartlab.quant 엔진 axis 산출물 → KPI tile / trend.
# stockCode 직접 받음 (company.rawFinance 와 무관, 가격 데이터 자체 fetch).
# 실패 (network · 데이터 부족) 시 빈 spec → frontend 에서 "데이터 없음" 표시.
# ─────────────────────────────────────────────────────────────


def _safeQuantCall(modulePath: str, fnName: str, stockCode: str, **kwargs: Any) -> Any:
    """quant 모듈 함수 안전 호출. import / 실행 실패 → None."""
    try:
        mod = importlib.import_module(modulePath)
    except ImportError:
        return None
    fn = getattr(mod, fnName, None)
    if fn is None:
        return None
    try:
        return fn(stockCode, **kwargs)
    except Exception:  # noqa: BLE001
        return None


def buildQuantPriceTrend(stockCode: str) -> dict[str, Any]:
    """최근 1 년 OHLCV 캔들스틱 + 거래량 + SMA(20)/SMA(60) overlay.

    kind=candle. categories=날짜 (YYYY-MM-DD), series 5 개:
      - open/high/low/close: 캔들 (type=bar 표시는 frontend candle renderer)
      - sma20/sma60: 라인 overlay
      - volume: 하단 separate pane (type=bar)

    gather/quant.signal.momentum.fetchOhlcv 자동 fetch (Naver/Yahoo).
    """
    from datetime import date, timedelta

    start = (date.today() - timedelta(days=400)).isoformat()
    try:
        from dartlab.quant.signal.momentum import fetchOhlcv  # type: ignore[import-untyped]
    except ImportError:
        return {"categories": [], "series": []}
    try:
        ohlcv = fetchOhlcv(stockCode, start=start)
    except Exception:  # noqa: BLE001
        return {"categories": [], "series": []}

    if ohlcv is None:
        return {"categories": [], "series": []}
    try:
        rows = ohlcv.to_dicts() if hasattr(ohlcv, "to_dicts") else list(ohlcv)
    except Exception:  # noqa: BLE001
        return {"categories": [], "series": []}
    if not rows:
        return {"categories": [], "series": []}
    # 최근 252 거래일만 (1 년).
    rows = rows[-252:]
    categories: list[str] = []
    opens: list[float | None] = []
    highs: list[float | None] = []
    lows: list[float | None] = []
    closes: list[float | None] = []
    volumes: list[float | None] = []
    for r in rows:
        d = r.get("date") or r.get("Date")
        # ISO 날짜 strict 형식 (lightweight-charts: 'YYYY-MM-DD').
        ds = str(d)[:10] if d is not None else ""
        categories.append(ds)
        opens.append(_toFloat(r.get("open") or r.get("Open")))
        highs.append(_toFloat(r.get("high") or r.get("High")))
        lows.append(_toFloat(r.get("low") or r.get("Low")))
        closes.append(_toFloat(r.get("close") or r.get("Close")))
        volumes.append(_toFloat(r.get("volume") or r.get("Volume")))

    def _sma(arr: list[float | None], window: int) -> list[float | None]:
        out: list[float | None] = []
        buf: list[float] = []
        for v in arr:
            if v is not None:
                buf.append(v)
                if len(buf) > window:
                    buf.pop(0)
                out.append(sum(buf) / len(buf) if len(buf) == window else None)
            else:
                out.append(None)
        return out

    sma20 = _sma(closes, 20)
    sma60 = _sma(closes, 60)

    # 매수/매도 marker — calcSignals.recentEvents 의 시점 + 방향.
    # frontend CandleChart 가 spec.options.markers 보고 lightweight-charts setMarkers.
    markers: list[dict[str, Any]] = []
    signals = _safeQuantCall("dartlab.quant.screen.axTechnical", "calcSignals", stockCode)
    if isinstance(signals, dict):
        events = signals.get("recentEvents") or []
        for ev in events:
            if not isinstance(ev, dict):
                continue
            ds = str(ev.get("date") or "")[:10]
            direction = str(ev.get("direction") or "")
            evType = str(ev.get("type") or "")
            if not ds:
                continue
            isBuy = direction in ("매수", "buy", "long", "bullish")
            isSell = direction in ("매도", "sell", "short", "bearish")
            if not (isBuy or isSell):
                continue
            markers.append(
                {
                    "time": ds,
                    "position": "belowBar" if isBuy else "aboveBar",
                    "color": "#ef4444" if isBuy else "#2563eb",
                    "shape": "arrowUp" if isBuy else "arrowDown",
                    "text": evType,
                }
            )

    return {
        "categories": categories,
        "series": [
            {
                "key": "open",
                "label": "시가",
                "color": "#94a3b8",
                "intent": "neutral",
                "unit": "원",
                "type": "line",
                "axis": "left",
                "data": opens,
            },
            {
                "key": "high",
                "label": "고가",
                "color": "#94a3b8",
                "intent": "neutral",
                "unit": "원",
                "type": "line",
                "axis": "left",
                "data": highs,
            },
            {
                "key": "low",
                "label": "저가",
                "color": "#94a3b8",
                "intent": "neutral",
                "unit": "원",
                "type": "line",
                "axis": "left",
                "data": lows,
            },
            {
                "key": "close",
                "label": "종가",
                "color": "#2563eb",
                "intent": "primary",
                "unit": "원",
                "type": "line",
                "axis": "left",
                "data": closes,
            },
            {
                "key": "sma20",
                "label": "SMA(20)",
                "color": "#10b981",
                "intent": "accent",
                "unit": "원",
                "type": "line",
                "axis": "left",
                "data": sma20,
            },
            {
                "key": "sma60",
                "label": "SMA(60)",
                "color": "#f59e0b",
                "intent": "accent",
                "unit": "원",
                "type": "line",
                "axis": "left",
                "data": sma60,
            },
            {
                "key": "volume",
                "label": "거래량",
                "color": "#94a3b8",
                "intent": "neutral",
                "unit": "주",
                "type": "bar",
                "axis": "right",
                "data": volumes,
            },
        ],
        "options": {"markers": markers},
    }


def _calcIndicatorsDf(stockCode: str) -> Any:
    """calcIndicators DataFrame — RSI/MACD 카드 공용 데이터원. cache 없음 (server 측 단일 thread 반복 호출은 가격 캐시 hit 후 모두 sub-second)."""
    return _safeQuantCall("dartlab.quant.screen.axTechnical", "calcIndicators", stockCode)


def buildQuantRsiTrend(stockCode: str) -> dict[str, Any]:
    """RSI(14) sub-pane trend — 과매수(70) · 과매도(30) 참조선.

    series 1 + options.refLines 2.
    """
    df = _calcIndicatorsDf(stockCode)
    if df is None or not hasattr(df, "columns") or "rsi14" not in df.columns:
        return {"categories": [], "series": []}
    try:
        rows = df.tail(252).to_dicts()
    except Exception:  # noqa: BLE001
        return {"categories": [], "series": []}
    categories = [str(r.get("date"))[:10] for r in rows]
    rsi = [_toFloat(r.get("rsi14")) for r in rows]
    return {
        "categories": categories,
        "series": [
            {
                "key": "rsi14",
                "label": "RSI(14)",
                "color": "#8b5cf6",
                "intent": "primary",
                "unit": "%",
                "type": "line",
                "axis": "left",
                "data": rsi,
            },
        ],
        "options": {
            "refLines": [
                {"value": 70, "label": "과매수", "color": "#ef4444"},
                {"value": 30, "label": "과매도", "color": "#10b981"},
            ],
            "yDomain": [0, 100],
        },
    }


def buildQuantMacdTrend(stockCode: str) -> dict[str, Any]:
    """MACD sub-pane — line + signal + histogram bar."""
    df = _calcIndicatorsDf(stockCode)
    if df is None or not hasattr(df, "columns") or "macd" not in df.columns:
        return {"categories": [], "series": []}
    try:
        rows = df.tail(252).to_dicts()
    except Exception:  # noqa: BLE001
        return {"categories": [], "series": []}
    categories = [str(r.get("date"))[:10] for r in rows]
    macd = [_toFloat(r.get("macd")) for r in rows]
    sig = [_toFloat(r.get("macdSignal")) for r in rows]
    hist = [_toFloat(r.get("macdHist")) for r in rows]
    return {
        "categories": categories,
        "series": [
            {
                "key": "macdHist",
                "label": "Histogram",
                "color": "#94a3b8",
                "intent": "neutral",
                "unit": "",
                "type": "bar",
                "axis": "left",
                "data": hist,
            },
            {
                "key": "macd",
                "label": "MACD",
                "color": "#2563eb",
                "intent": "primary",
                "unit": "",
                "type": "line",
                "axis": "left",
                "data": macd,
            },
            {
                "key": "macdSignal",
                "label": "Signal",
                "color": "#f59e0b",
                "intent": "accent",
                "unit": "",
                "type": "line",
                "axis": "left",
                "data": sig,
            },
        ],
        "options": {"refLines": [{"value": 0, "label": "", "color": "#475569"}]},
    }


def _kpiTile(label: str, value: Any, *, unit: str = "", intent: str = "primary", subtitle: str = "") -> dict[str, Any]:
    """간이 KpiTile dict 생성."""
    return {
        "label": label,
        "value": _toFloat(value),
        "prev": None,
        "unit": unit,
        "intent": intent,
        "subtitle": subtitle,
    }


def buildQuantVerdictKpi(stockCode: str) -> dict[str, Any]:
    """quant.verdict → 6 tile KPI (점수·판정·RSI·ADX·BB위치·SMA 돌파)."""
    result = _safeQuantCall("dartlab.quant.screen.axTechnical", "calcVerdict", stockCode)
    if result is None or not isinstance(result, dict) or result.get("error"):
        return {"tiles": []}
    verdict = str(result.get("verdict", "—"))
    intentByVerdict = {
        "강세": "positive",
        "중립": "neutral",
        "약세": "negative",
    }
    score = result.get("score")
    rsi = result.get("rsi")
    adx = result.get("adx")
    bb = result.get("bbPosition")
    aboveSma20 = result.get("aboveSma20")
    aboveSma60 = result.get("aboveSma60")
    tiles = [
        _kpiTile("판단", score, unit="점", intent=intentByVerdict.get(verdict, "neutral"), subtitle=verdict),
        _kpiTile("RSI(14)", rsi, unit="%", intent="primary", subtitle="과매수 70+ / 과매도 30-"),
        _kpiTile("ADX", adx, unit="%", intent="primary", subtitle="추세 강도 25+ 강함"),
        _kpiTile("BB 위치", bb, unit="%", intent="neutral", subtitle="0=하단 100=상단"),
        _kpiTile(
            "SMA20 돌파",
            1.0 if aboveSma20 else 0.0,
            unit="",
            intent="positive" if aboveSma20 else "negative",
            subtitle="단기 추세",
        ),
        _kpiTile(
            "SMA60 돌파",
            1.0 if aboveSma60 else 0.0,
            unit="",
            intent="positive" if aboveSma60 else "negative",
            subtitle="중기 추세",
        ),
    ]
    return {"tiles": tiles}


def buildQuantMomentumKpi(stockCode: str) -> dict[str, Any]:
    """quant.momentum → 4 tile KPI (12-1m or 6-1m · TS 1m · 52w high · streak).

    데이터 252 일 미만일 때 momentum12_1=None → 6-1m fallback. crashRisk 는
    문자열 ("low"/"high") · streak/streakDirection 가 추가 정보.
    """
    result = _safeQuantCall("dartlab.quant.signal.momentum", "calcMomentum", stockCode)
    if result is None or not isinstance(result, dict) or result.get("error"):
        return {"tiles": []}
    mom12_1 = result.get("momentum12_1")
    mom6_1 = result.get("momentum6_1")
    # momentum12_1 우선, None 이면 6-1 fallback.
    momPrimary = mom12_1 if mom12_1 is not None else mom6_1
    momLabel = "12-1m 모멘텀" if mom12_1 is not None else "6-1m 모멘텀 (fallback)"
    ts1m = _drill(result, "tsMomentum.1m.return")
    ts1mSignal = str(_drill(result, "tsMomentum.1m.signal") or "—")
    high52 = result.get("highRatio52w")
    streak = result.get("streak")
    streakDir = str(result.get("streakDirection") or "")
    verdict = str(result.get("momentumVerdict") or "—")
    intentByVerdict = {
        "strong_bullish": "positive",
        "bullish": "positive",
        "neutral": "neutral",
        "bearish": "negative",
        "strong_bearish": "negative",
    }
    intentMom = intentByVerdict.get(verdict, "primary")
    tiles = [
        _kpiTile(
            momLabel,
            momPrimary * 100 if isinstance(momPrimary, (int, float)) else momPrimary,
            unit="%",
            intent=intentMom,
            subtitle=f"verdict={verdict}",
        ),
        _kpiTile(
            "1m 수익률 (TS)",
            ts1m * 100 if isinstance(ts1m, (int, float)) else ts1m,
            unit="%",
            intent="primary",
            subtitle=f"signal={ts1mSignal}",
        ),
        _kpiTile(
            "52주 신고가 비율",
            high52 * 100 if isinstance(high52, (int, float)) else high52,
            unit="%",
            intent="primary",
            subtitle="95%+ 강한 추세 (George-Hwang)",
        ),
        _kpiTile(
            f"연속 {streakDir or '추세'}",
            streak,
            unit="일",
            intent="positive" if streakDir == "상승" else ("negative" if streakDir == "하락" else "neutral"),
            subtitle="동일 방향 연속 일수",
        ),
    ]
    return {"tiles": tiles}


def buildQuantVolatilityKpi(stockCode: str) -> dict[str, Any]:
    """quant.volatility → 4 tile KPI (20일·60일 RV · HAR-RV · GARCH · 레짐)."""
    result = _safeQuantCall("dartlab.quant.risk.volatility", "calcVolatility", stockCode)
    if result is None or not isinstance(result, dict) or result.get("error"):
        return {"tiles": []}
    rv20 = result.get("realizedVol_20d")
    rv60 = result.get("realizedVol_60d")
    harRV = result.get("harRV")
    garch = result.get("garchVol")
    regime = str(result.get("volRegime") or "—")
    shape = str(result.get("volCurveShape") or "")
    intentByRegime = {"low": "positive", "normal": "neutral", "high": "negative", "extreme": "negative"}
    tiles = [
        _kpiTile(
            "RV 20일 (연환산)",
            rv20 * 100 if isinstance(rv20, (int, float)) and rv20 < 5 else rv20,
            unit="%",
            intent=intentByRegime.get(regime, "primary"),
            subtitle=f"regime={regime}",
        ),
        _kpiTile(
            "RV 60일",
            rv60 * 100 if isinstance(rv60, (int, float)) and rv60 < 5 else rv60,
            unit="%",
            intent="primary",
            subtitle=f"커브={shape or '—'}",
        ),
        _kpiTile(
            "HAR-RV",
            harRV * 100 if isinstance(harRV, (int, float)) and harRV < 5 else harRV,
            unit="%",
            intent="accent",
            subtitle="Heterogeneous AR (1d+5d+22d)",
        ),
        _kpiTile(
            "GARCH(1,1)",
            garch * 100 if isinstance(garch, (int, float)) and garch < 5 else garch,
            unit="%",
            intent="primary",
            subtitle="조건부 — 다음날 예측",
        ),
    ]
    return {"tiles": tiles}


def buildQuantBetaKpi(stockCode: str) -> dict[str, Any]:
    """quant.beta → 4 tile KPI (β · R² · CAPM 기대 · 상대강도)."""
    result = _safeQuantCall("dartlab.quant.screen.axTechnical", "calcBeta", stockCode)
    if result is None or not isinstance(result, dict) or result.get("error"):
        return {"tiles": []}
    beta = result.get("value")
    r2 = result.get("r2")
    capm = result.get("capmExpected")
    rs = result.get("relativeStrength")
    interp = str(result.get("interpretation", ""))
    tiles = [
        _kpiTile("β", beta, unit="배", intent="primary", subtitle=interp[:30] if interp else "시장 민감도"),
        _kpiTile("R²", r2, unit="%", intent="neutral", subtitle="시장 설명력"),
        _kpiTile("CAPM 기대", capm, unit="%", intent="accent", subtitle="rf + β × 시장프리미엄"),
        _kpiTile("상대강도", rs, unit="배", intent="primary", subtitle="벤치마크 대비"),
    ]
    return {"tiles": tiles}


def buildQuantForecastKpi(stockCode: str) -> dict[str, Any]:
    """quant.forecast → 4 tile KPI (point · CI 폭 · model · 정상성).

    horizon=5 일 일별 수익률 예측. forecastTable: [{date, point, lower, upper, ...}].
    누적은 합성. 90% Conformal interval (predictive coverage 보장).
    """
    result = _safeQuantCall("dartlab.quant.benchmark.forecast", "forecastReturns", stockCode, horizon=5)
    if result is None or not isinstance(result, dict) or result.get("error"):
        return {"tiles": []}
    table = result.get("forecastTable") or []
    halfWidth = result.get("conformalHalfWidth")
    model = str(result.get("modelChosen", "auto"))
    pAdf = result.get("pAdfStationary")
    summary = result.get("summary") or {}
    # 누적 수익률 — table 의 일별 point 합산 (log-return 가정이면 합, simple 이면 곱-1).
    # summary 에 있으면 우선 사용.
    cumPoint = summary.get("cumulativeReturn") if isinstance(summary, dict) else None
    if cumPoint is None and isinstance(table, list):
        try:
            pts = [_toFloat(row.get("point") if isinstance(row, dict) else None) for row in table]
            valid = [p for p in pts if p is not None]
            cumPoint = sum(valid) if valid else None
        except Exception:  # noqa: BLE001
            cumPoint = None
    pointFloat = _toFloat(cumPoint)
    intent = (
        "positive"
        if pointFloat is not None and pointFloat > 0
        else "negative"
        if pointFloat is not None and pointFloat < 0
        else "neutral"
    )
    tiles = [
        _kpiTile(
            "5일 누적 예측",
            cumPoint * 100 if isinstance(cumPoint, (int, float)) and abs(cumPoint) < 1 else cumPoint,
            unit="%",
            intent=intent,
            subtitle=f"model={model}",
        ),
        _kpiTile(
            "90% CI 반폭",
            halfWidth * 100 if isinstance(halfWidth, (int, float)) and halfWidth < 1 else halfWidth,
            unit="%",
            intent="accent",
            subtitle="Conformal predictive coverage 90%",
        ),
        _kpiTile(
            "정상성 p-value",
            pAdf,
            unit="",
            intent="primary",
            subtitle="ADF — 0.05 미만이면 정상",
        ),
        _kpiTile(
            "예측 모델",
            len(result.get("modelsConsidered") or []),
            unit="개",
            intent="neutral",
            subtitle=f"선택={model}",
        ),
    ]
    return {"tiles": tiles}


def buildQuantComingSoon(label: str = "준비 중") -> dict[str, Any]:
    """placeholder KPI 1 tile — 미구현 카드 graceful 빈 표시."""
    return {
        "tiles": [
            {
                "label": label,
                "value": None,
                "prev": None,
                "unit": "",
                "intent": "neutral",
                "subtitle": "엔진 wiring 진행 중 — 다음 commit 에서 실값",
            }
        ]
    }


# ─────────────────────────────────────────────────────────────
# 백테스트 6 카드 — 1 stockCode 당 8 style backtest 1 회만, module-level cache.
# 6 카드 (equity·drawdown·monthly heatmap·style matrix·rolling sharpe·annual)
# 가 동일 cache 결과 공유.
# ─────────────────────────────────────────────────────────────


_BACKTEST_CACHE: dict[str, dict[str, Any]] = {}
_BACKTEST_CACHE_LIMIT = 8


def _backtestAllStyles(stockCode: str) -> dict[str, Any] | None:
    """8 style backtest 일괄 — module-level LRU cache (max 8 종목).

    반환:
        {
          stockCode, dates: list[str], close: list[float],
          buyHoldEquity: list[float],
          results: {style: BacktestResult},  # 8 style
          returns: {style: list[float]},
          equities: {style: list[float]},
        }
    """
    if stockCode in _BACKTEST_CACHE:
        return _BACKTEST_CACHE[stockCode]
    try:
        import dartlab
        from dartlab.quant.signal.momentum import fetchOhlcv
        from dartlab.quant.strategy import backtest, presets
    except ImportError:
        return None

    try:
        company = dartlab.Company(stockCode)
        ohlcv = fetchOhlcv(stockCode)
    except Exception:  # noqa: BLE001
        return None
    if ohlcv is None or not hasattr(ohlcv, "to_dicts"):
        return None

    try:
        close = ohlcv["close"].to_numpy()
        high = ohlcv["high"].to_numpy()
        low = ohlcv["low"].to_numpy()
        open_ = ohlcv["open"].to_numpy()
        volume = ohlcv["volume"].to_numpy()
        dates = [str(d)[:10] for d in ohlcv["date"].to_list()]
    except Exception:  # noqa: BLE001
        return None
    if len(close) < 30:
        return None

    # buy-hold baseline equity (normalize 시작=1.0).
    import numpy as np

    bh = (close / close[0]).tolist()

    reg = presets.STYLE_REGISTRY()
    results: dict[str, Any] = {}
    equities: dict[str, list[float]] = {"buyHold": bh}
    returns: dict[str, list[float]] = {}
    for styleKey, builder in reg.items():
        try:
            rule = builder(company)
            r = backtest.vectorBacktest(
                close,
                rule,
                open_=open_,
                high=high,
                low=low,
                volume=volume,
                dates=dates,
                style=styleKey,
            )
            results[styleKey] = r
            eq = getattr(r, "equity", None)
            rt = getattr(r, "returns", None)
            if eq is not None and hasattr(eq, "tolist"):
                equities[styleKey] = eq.tolist()
            elif eq is not None:
                equities[styleKey] = list(eq)
            if rt is not None and hasattr(rt, "tolist"):
                returns[styleKey] = rt.tolist()
            elif rt is not None:
                returns[styleKey] = list(rt)
        except Exception:  # noqa: BLE001
            continue

    out = {
        "stockCode": stockCode,
        "dates": dates,
        "close": close.tolist(),
        "buyHoldEquity": bh,
        "results": results,
        "equities": equities,
        "returns": returns,
    }
    _BACKTEST_CACHE[stockCode] = out
    if len(_BACKTEST_CACHE) > _BACKTEST_CACHE_LIMIT:
        # FIFO eviction.
        oldest = next(iter(_BACKTEST_CACHE))
        if oldest != stockCode:
            _BACKTEST_CACHE.pop(oldest, None)
    return out


_STYLE_COLORS = {
    "buyHold": "#94a3b8",
    "trendFollow": "#2563eb",
    "meanReversion": "#ef4444",
    "breakout": "#f59e0b",
    "dipBuy": "#10b981",
    "eventDriven": "#8b5cf6",
    "flowFollow": "#ec4899",
    "lowVolDefensive": "#06b6d4",
    "seasonalKR": "#a855f7",
}
_STYLE_LABELS = {
    "buyHold": "Buy & Hold",
    "trendFollow": "추세추종",
    "meanReversion": "평균회귀",
    "breakout": "돌파",
    "dipBuy": "눌림목매수",
    "eventDriven": "이벤트",
    "flowFollow": "수급추종",
    "lowVolDefensive": "저변동방어",
    "seasonalKR": "한국캘린더",
}


def buildQuantEquityCurve(stockCode: str) -> dict[str, Any]:
    """8 style equity overlay + buy-hold baseline. trend kind.

    9 라인 (buyHold + 8 style). 시작 1.0 normalize. 사용자 즉시 비교 가능.
    """
    bt = _backtestAllStyles(stockCode)
    if bt is None:
        return {"categories": [], "series": []}
    dates = bt["dates"]
    eqs = bt["equities"]
    series: list[dict[str, Any]] = []
    for key, data in eqs.items():
        if not data or all(v is None or v == 0 for v in data):
            continue
        intent = "primary" if key == "buyHold" else "accent"
        series.append(
            {
                "key": key,
                "label": _STYLE_LABELS.get(key, key),
                "color": _STYLE_COLORS.get(key, "#64748b"),
                "intent": intent,
                "unit": "배",
                "type": "line",
                "axis": "left",
                "data": data,
            }
        )
    return {"categories": dates, "series": series}


def buildQuantDrawdownChart(stockCode: str) -> dict[str, Any]:
    """Drawdown trend — best style (sharpe 1 위) 의 equity 에서 (equity / runMax - 1) 시계열.

    음수 면적. 0 참조선.
    """
    bt = _backtestAllStyles(stockCode)
    if bt is None:
        return {"categories": [], "series": []}
    # best style 선택 — buyHold 제외, sharpe 가장 높은 style.
    results = bt.get("results") or {}
    best_key = None
    best_sharpe = float("-inf")
    for k, r in results.items():
        s = getattr(r, "sharpe", None) or 0
        if s > best_sharpe:
            best_sharpe = s
            best_key = k
    if best_key is None:
        return {"categories": [], "series": []}
    eq = bt["equities"].get(best_key) or []
    if not eq:
        return {"categories": [], "series": []}
    run_max = 0.0
    dd: list[float | None] = []
    for v in eq:
        if v is None:
            dd.append(None)
            continue
        if v > run_max:
            run_max = v
        dd.append((v / run_max - 1) * 100 if run_max > 0 else 0)
    return {
        "categories": bt["dates"],
        "series": [
            {
                "key": "drawdown",
                "label": f"Drawdown ({_STYLE_LABELS.get(best_key, best_key)})",
                "color": "#ef4444",
                "intent": "negative",
                "unit": "%",
                "type": "area",
                "axis": "left",
                "data": dd,
            }
        ],
        "options": {"refLines": [{"value": 0, "label": "", "color": "#475569"}]},
    }


def _monthlyReturns(dates: list[str], returns: list[float]) -> dict[tuple[int, int], float]:
    """(year, month) → 월간 누적수익률 (%). returns 는 일별 simple return."""
    out: dict[tuple[int, int], list[float]] = {}
    for d, r in zip(dates, returns):
        if r is None or len(d) < 7:
            continue
        try:
            y = int(d[:4])
            m = int(d[5:7])
        except ValueError:
            continue
        out.setdefault((y, m), []).append(r)
    # 일별 simple return 합 ≈ 월간 (작은 값 가정). 정확 = (1+r1)*(1+r2)... - 1.
    monthly: dict[tuple[int, int], float] = {}
    for ym, rs in out.items():
        cum = 1.0
        for r in rs:
            cum *= 1 + r
        monthly[ym] = (cum - 1) * 100
    return monthly


def buildQuantMonthlyHeatmap(stockCode: str) -> dict[str, Any]:
    """Monthly Returns Heatmap — matrix kind. row=year, col=month, cells=수익률 %.

    best style returns 기반.
    """
    bt = _backtestAllStyles(stockCode)
    if bt is None:
        return {"cells": []}
    results = bt.get("results") or {}
    best_key = None
    best_sharpe = float("-inf")
    for k, r in results.items():
        s = getattr(r, "sharpe", None) or 0
        if s > best_sharpe:
            best_sharpe = s
            best_key = k
    if best_key is None:
        return {"cells": []}
    rets = bt["returns"].get(best_key) or []
    if not rets:
        return {"cells": []}
    monthly = _monthlyReturns(bt["dates"], rets)
    if not monthly:
        return {"cells": []}
    years = sorted({y for y, _ in monthly.keys()})
    cells: list[dict[str, Any]] = []
    for y in years:
        for m in range(1, 13):
            v = monthly.get((y, m))
            cells.append({"row": str(y), "col": f"{m}월", "value": v, "unit": "%"})
    return {
        "cells": cells,
        "rowOrder": [str(y) for y in years],
        "colOrder": [f"{m}월" for m in range(1, 13)],
        "tone": "diverging",
        "options": {"styleKey": best_key, "styleLabel": _STYLE_LABELS.get(best_key, best_key)},
    }


def buildQuantStyleMatrix(stockCode: str) -> dict[str, Any]:
    """8 style 성과 매트릭스 — comparisonTable kind. row=style, col=Sharpe/Sortino/MDD/WinRate/Expectancy/Turnover.

    각 row 의 self 값 = 본 종목 style 성과. peer 자리는 0 (single-stock context).
    """
    bt = _backtestAllStyles(stockCode)
    if bt is None:
        return {"rows": []}
    results = bt.get("results") or {}
    if not results:
        return {"rows": []}
    rows: list[dict[str, Any]] = []
    for styleKey, r in results.items():
        sharpe = getattr(r, "sharpe", None)
        sortino = getattr(r, "sortino", None)
        mddVal = getattr(r, "mdd", None)
        winrateVal = getattr(r, "winrate", None)
        expectancyVal = getattr(r, "expectancy", None)
        turnoverVal = getattr(r, "turnover", None)
        # comparisonTable 의 row 는 single metric — 본 카드는 style x metric 행렬이라
        # 형식 차이. 대신 multi-column row 구조로 변형 (label=style, self=sharpe, percentile=원본 6 column dict).
        rows.append(
            {
                "label": _STYLE_LABELS.get(styleKey, styleKey),
                "self": _toFloat(sharpe),
                "peerMedian": _toFloat(sortino),
                "peerP25": _toFloat(mddVal),
                "peerP75": _toFloat(winrateVal),
                "percentile": _toFloat(expectancyVal),
                "unit": "배",
                "higherIsBetter": True,
            }
        )
    return {
        "rows": rows,
        "peerCount": 0,
        "options": {
            "columnLabels": ["전략", "Sharpe", "Sortino", "MaxDD", "WinRate", "Expectancy"],
            "styleMatrix": True,
        },
    }


def buildQuantRollingSharpe(stockCode: str) -> dict[str, Any]:
    """Rolling 252-day Sharpe — best style returns 기반. trend kind."""
    bt = _backtestAllStyles(stockCode)
    if bt is None:
        return {"categories": [], "series": []}
    results = bt.get("results") or {}
    best_key = None
    best_sharpe = float("-inf")
    for k, r in results.items():
        s = getattr(r, "sharpe", None) or 0
        if s > best_sharpe:
            best_sharpe = s
            best_key = k
    if best_key is None:
        return {"categories": [], "series": []}
    rets = bt["returns"].get(best_key) or []
    if len(rets) < 60:
        return {"categories": [], "series": []}
    import numpy as np

    window = 60  # ~3 개월. 252 면 단일 종목 1 년 데이터에서 1 점만 — 60 일이 적합.
    arr = np.array([(r if r is not None else 0.0) for r in rets], dtype=float)
    sharpe: list[float | None] = [None] * len(arr)
    for i in range(window, len(arr)):
        w = arr[i - window : i]
        mu = float(np.mean(w))
        sd = float(np.std(w, ddof=1))
        sharpe[i] = (mu / sd) * (252**0.5) if sd > 0 else None
    return {
        "categories": bt["dates"],
        "series": [
            {
                "key": "rollSharpe",
                "label": f"Rolling Sharpe ({_STYLE_LABELS.get(best_key, best_key)})",
                "color": "#10b981",
                "intent": "primary",
                "unit": "배",
                "type": "line",
                "axis": "left",
                "data": sharpe,
            }
        ],
        "options": {
            "refLines": [
                {"value": 0, "label": "", "color": "#475569"},
                {"value": 1, "label": "양호", "color": "#10b981"},
            ]
        },
    }


def buildQuantBetaScatter(stockCode: str) -> dict[str, Any]:
    """β 산점도 — 시장 일별 수익률 X, 종목 일별 수익률 Y + OLS 회귀선 ref.

    scatter kind. xRef=시장 평균, yRef=종목 평균. 박스 안 β/α/R² 표시는 frontend.
    """
    try:
        import numpy as np

        from dartlab.quant.benchmark.data import fetchBenchmarkOhlcv
        from dartlab.quant.signal.momentum import fetchOhlcv
    except ImportError:
        return {"points": []}
    try:
        stock = fetchOhlcv(stockCode)
        bench = fetchBenchmarkOhlcv(market="KR")
    except Exception:  # noqa: BLE001
        return {"points": []}
    if stock is None or bench is None:
        return {"points": []}
    try:
        s_dates = [str(d)[:10] for d in stock["date"].to_list()]
        s_close = stock["close"].to_numpy()
        b_dates = [str(d)[:10] for d in bench["date"].to_list()]
        b_close = bench["close"].to_numpy()
    except Exception:  # noqa: BLE001
        return {"points": []}
    # 날짜 매칭.
    b_map = {d: b_close[i] for i, d in enumerate(b_dates)}
    matched_s: list[float] = []
    matched_b: list[float] = []
    for i, d in enumerate(s_dates):
        if d in b_map:
            matched_s.append(s_close[i])
            matched_b.append(b_map[d])
    if len(matched_s) < 30:
        return {"points": []}
    s_arr = np.array(matched_s)
    b_arr = np.array(matched_b)
    s_ret = (s_arr[1:] / s_arr[:-1] - 1) * 100
    b_ret = (b_arr[1:] / b_arr[:-1] - 1) * 100
    points = [
        {"x": float(bx), "y": float(sx), "label": f"{i}", "self": False} for i, (bx, sx) in enumerate(zip(b_ret, s_ret))
    ]
    # OLS β/α/R².
    bm = float(np.mean(b_ret))
    sm = float(np.mean(s_ret))
    cov = float(np.mean((b_ret - bm) * (s_ret - sm)))
    var_b = float(np.var(b_ret))
    beta = cov / var_b if var_b > 0 else 0.0
    alpha = sm - beta * bm
    ss_tot = float(np.sum((s_ret - sm) ** 2))
    ss_res = float(np.sum((s_ret - (alpha + beta * b_ret)) ** 2))
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    return {
        "points": points,
        "xLabel": "시장 (KOSPI) 일별 수익률",
        "yLabel": f"{stockCode} 일별 수익률",
        "xUnit": "%",
        "yUnit": "%",
        "xRef": round(bm, 3),
        "yRef": round(sm, 3),
        "options": {
            "betaSummary": {
                "beta": round(beta, 3),
                "alpha": round(alpha, 4),
                "r2": round(r2, 3),
                "n": len(points),
            },
        },
    }


def buildQuantVolatilityTerm(stockCode: str) -> dict[str, Any]:
    """변동성 Term Structure — 5d/20d/60d/120d realized 시계열 (rolling std, 연환산).

    trend kind. 4 line. 단일 시점 KPI 대신 시간에 따른 변동성 진화.
    """
    try:
        import numpy as np

        from dartlab.quant.signal.momentum import fetchOhlcv
    except ImportError:
        return {"categories": [], "series": []}
    try:
        ohlcv = fetchOhlcv(stockCode)
    except Exception:  # noqa: BLE001
        return {"categories": [], "series": []}
    if ohlcv is None:
        return {"categories": [], "series": []}
    try:
        dates = [str(d)[:10] for d in ohlcv["date"].to_list()]
        close = ohlcv["close"].to_numpy()
    except Exception:  # noqa: BLE001
        return {"categories": [], "series": []}
    if len(close) < 130:
        return {"categories": [], "series": []}
    rets = np.diff(close) / close[:-1]

    def _rollingVol(window: int) -> list[float | None]:
        out: list[float | None] = [None] * len(close)
        for i in range(window, len(rets) + 1):
            w = rets[i - window : i]
            sd = float(np.std(w, ddof=1))
            out[i] = sd * (252**0.5) * 100  # 연환산 %
        return out

    rv5 = _rollingVol(5)
    rv20 = _rollingVol(20)
    rv60 = _rollingVol(60)
    rv120 = _rollingVol(120)
    return {
        "categories": dates,
        "series": [
            {
                "key": "rv5",
                "label": "5d",
                "color": "#ef4444",
                "intent": "accent",
                "unit": "%",
                "type": "line",
                "axis": "left",
                "data": rv5,
            },
            {
                "key": "rv20",
                "label": "20d",
                "color": "#f59e0b",
                "intent": "accent",
                "unit": "%",
                "type": "line",
                "axis": "left",
                "data": rv20,
            },
            {
                "key": "rv60",
                "label": "60d",
                "color": "#10b981",
                "intent": "accent",
                "unit": "%",
                "type": "line",
                "axis": "left",
                "data": rv60,
            },
            {
                "key": "rv120",
                "label": "120d",
                "color": "#2563eb",
                "intent": "primary",
                "unit": "%",
                "type": "line",
                "axis": "left",
                "data": rv120,
            },
        ],
    }


def buildQuantDrawdownDistribution(stockCode: str) -> dict[str, Any]:
    """Drawdown 깊이 분포 — best style equity 의 모든 drawdown 깊이 히스토그램.

    trend kind, bar. categories=깊이 구간 (0-2%, 2-5%, 5-10%, 10-15%, 15-20%, 20%+),
    series=빈도 (일수). 사용자가 *이 종목 이 전략의 drawdown 통계 분포*.
    """
    bt = _backtestAllStyles(stockCode)
    if bt is None:
        return {"categories": [], "series": []}
    results = bt.get("results") or {}
    best_key = None
    best_sharpe = float("-inf")
    for k, r in results.items():
        s = getattr(r, "sharpe", None) or 0
        if s > best_sharpe:
            best_sharpe = s
            best_key = k
    if best_key is None:
        return {"categories": [], "series": []}
    eq = bt["equities"].get(best_key) or []
    if not eq:
        return {"categories": [], "series": []}
    # drawdown sequence — 모든 시점 dd %.
    run_max = 0.0
    depths: list[float] = []
    for v in eq:
        if v is None:
            continue
        if v > run_max:
            run_max = v
        if run_max > 0:
            dd = (1 - v / run_max) * 100  # 양수 깊이 %.
            depths.append(dd)
    # 구간 bin.
    bins = [(0, 2, "0~2%"), (2, 5, "2~5%"), (5, 10, "5~10%"), (10, 15, "10~15%"), (15, 20, "15~20%"), (20, 999, "20%+")]
    counts = [sum(1 for d in depths if lo <= d < hi) for lo, hi, _ in bins]
    labels = [lbl for _, _, lbl in bins]
    return {
        "categories": labels,
        "series": [
            {
                "key": "freq",
                "label": f"빈도 ({_STYLE_LABELS.get(best_key, best_key)})",
                "color": "#ef4444",
                "intent": "negative",
                "unit": "일",
                "type": "bar",
                "axis": "left",
                "data": counts,
            }
        ],
    }


def _normalizeScore(v: float | None, lo: float, hi: float) -> float:
    """v 를 [lo, hi] 범위에서 0~5 점으로 정규화. 범위 밖 clamp."""
    if v is None:
        return 0.0
    if hi <= lo:
        return 0.0
    s = (v - lo) / (hi - lo) * 5
    return max(0.0, min(5.0, s))


def buildQuantForecastFan(stockCode: str) -> dict[str, Any]:
    """Forecast Fan Chart — N-day horizon × {pointForecast, lower/upperBound} band.

    forecastReturns(horizon=20) → forecastTable 10/20 row. trend kind 4 series:
      - lastClose anchor (1 점)
      - pricePoint (point forecast 시계열)
      - priceLower / priceUpper (90% Conformal band, area-like 2 line)
    """
    result = _safeQuantCall("dartlab.quant.benchmark.forecast", "forecastReturns", stockCode, horizon=20)
    if result is None or not isinstance(result, dict) or result.get("error"):
        return {"categories": [], "series": []}
    table = result.get("forecastTable") or []
    if not isinstance(table, list) or len(table) == 0:
        return {"categories": [], "series": []}
    lastClose = _toFloat(result.get("lastClose"))
    lastDate = str(result.get("lastDate") or "today")[:10]
    # categories — last date + horizon 1..N. forecastTable horizon 인덱스로 라벨.
    categories = [lastDate] + [f"+{int(r.get('horizon', i + 1))}일" for i, r in enumerate(table)]
    points: list[float | None] = [lastClose]
    lowers: list[float | None] = [lastClose]
    uppers: list[float | None] = [lastClose]
    for row in table:
        if not isinstance(row, dict):
            continue
        points.append(_toFloat(row.get("pricePoint")))
        lowers.append(_toFloat(row.get("priceLower")))
        uppers.append(_toFloat(row.get("priceUpper")))
    model = str(result.get("modelChosen", "auto"))
    return {
        "categories": categories,
        "series": [
            {
                "key": "upper",
                "label": "90% CI 상단",
                "color": "#10b981",
                "intent": "accent",
                "unit": "원",
                "type": "line",
                "axis": "left",
                "data": uppers,
            },
            {
                "key": "point",
                "label": f"점 예측 ({model})",
                "color": "#2563eb",
                "intent": "primary",
                "unit": "원",
                "type": "line",
                "axis": "left",
                "data": points,
            },
            {
                "key": "lower",
                "label": "90% CI 하단",
                "color": "#ef4444",
                "intent": "accent",
                "unit": "원",
                "type": "line",
                "axis": "left",
                "data": lowers,
            },
        ],
    }


def buildQuantMonteCarloPaths(stockCode: str) -> dict[str, Any]:
    """Monte Carlo GBM 100 paths × 20 day horizon + VaR/CVaR.

    drift μ = 평균 일별 수익률, σ = 일별 std (last 252 day).
    paths = lastClose × exp((μ − σ²/2)t + σ × sqrt(t) × Z).
    trend kind. 25/50/75 percentile band + median bold line. options.varCvar 표기.
    """
    try:
        import numpy as np

        from dartlab.quant.signal.momentum import fetchOhlcv
    except ImportError:
        return {"categories": [], "series": []}
    try:
        ohlcv = fetchOhlcv(stockCode)
    except Exception:  # noqa: BLE001
        return {"categories": [], "series": []}
    if ohlcv is None:
        return {"categories": [], "series": []}
    try:
        close = ohlcv["close"].to_numpy()
        lastDate = str(ohlcv["date"].to_list()[-1])[:10]
    except Exception:  # noqa: BLE001
        return {"categories": [], "series": []}
    if len(close) < 30:
        return {"categories": [], "series": []}
    rets = np.diff(np.log(close[-252:]))
    mu = float(np.mean(rets))
    sigma = float(np.std(rets, ddof=1))
    lastClose = float(close[-1])
    horizon = 20
    nPaths = 200
    rng = np.random.default_rng(seed=42)
    # GBM simulation.
    Z = rng.standard_normal(size=(nPaths, horizon))
    log_paths = np.cumsum((mu - sigma**2 / 2) + sigma * Z, axis=1)
    paths = lastClose * np.exp(log_paths)
    # 25/50/75 percentile time series.
    p25 = np.percentile(paths, 25, axis=0).tolist()
    p50 = np.percentile(paths, 50, axis=0).tolist()
    p75 = np.percentile(paths, 75, axis=0).tolist()
    # VaR / CVaR 5% (horizon 끝).
    final = paths[:, -1]
    var5 = float(np.percentile(final, 5))
    cvar5 = float(np.mean(final[final <= var5])) if (final <= var5).any() else var5
    categories = [lastDate] + [f"+{i + 1}일" for i in range(horizon)]
    return {
        "categories": categories,
        "series": [
            {
                "key": "p75",
                "label": "75 percentile",
                "color": "#10b981",
                "intent": "accent",
                "unit": "원",
                "type": "line",
                "axis": "left",
                "data": [lastClose] + p75,
            },
            {
                "key": "p50",
                "label": "Median",
                "color": "#2563eb",
                "intent": "primary",
                "unit": "원",
                "type": "line",
                "axis": "left",
                "data": [lastClose] + p50,
            },
            {
                "key": "p25",
                "label": "25 percentile",
                "color": "#ef4444",
                "intent": "accent",
                "unit": "원",
                "type": "line",
                "axis": "left",
                "data": [lastClose] + p25,
            },
        ],
        "options": {
            "varCvar": {"var5": round(var5, 0), "cvar5": round(cvar5, 0), "lastClose": lastClose, "nPaths": nPaths},
        },
    }


def buildQuantRegimePhase(stockCode: str) -> dict[str, Any]:
    """HMM regime phase indicator — 약세/중립/강세/강한상승 4 phase + bullProb confidence.

    phaseIndicator kind. current=현재 phase index, confidence=bullProb.
    """
    result = _safeQuantCall("dartlab.quant.regime.hmm", "calcRegime", stockCode)
    if result is None or not isinstance(result, dict) or result.get("error"):
        return {"phases": [], "current": 0, "confidence": None}
    regimeLabel = str(result.get("regimeLabel") or result.get("trendVerdict") or "").lower()
    trendVerdict = str(result.get("trendVerdict") or "").lower()
    bullProb = _toFloat(result.get("bullProb"))
    phases = ["약세", "중립", "상승", "강한 상승"]
    current = 1  # default 중립.
    if "강한" in regimeLabel or "strong" in trendVerdict:
        current = 3
    elif "강세" in regimeLabel or "bull" in regimeLabel or "up" in trendVerdict:
        current = 2
    elif "약세" in regimeLabel or "bear" in regimeLabel or "down" in trendVerdict:
        current = 0
    return {
        "phases": phases,
        "current": current,
        "confidence": bullProb,
        "subtitle": f"HMM {regimeLabel or trendVerdict or '—'} · bullProb {bullProb:.2f}"
        if bullProb is not None
        else regimeLabel,
    }


def buildQuantSnowflakeRadar(stockCode: str) -> dict[str, Any]:
    """Snowflake 5 axis radar — Technical / Momentum / RiskInverse / Factor / Forecast.

    각 축 0~5 점 (Simply Wall St 스타일). radar kind.
    """
    # 5 axis 종합.
    verdict = _safeQuantCall("dartlab.quant.screen.axTechnical", "calcVerdict", stockCode) or {}
    momentum = _safeQuantCall("dartlab.quant.signal.momentum", "calcMomentum", stockCode) or {}
    volatility = _safeQuantCall("dartlab.quant.risk.volatility", "calcVolatility", stockCode) or {}
    beta = _safeQuantCall("dartlab.quant.screen.axTechnical", "calcBeta", stockCode) or {}
    forecast = _safeQuantCall("dartlab.quant.benchmark.forecast", "forecastReturns", stockCode, horizon=5) or {}

    # Technical: verdict score (-5~+5) → 0~5.
    tech = _normalizeScore(_toFloat(verdict.get("score")), -5, 5)
    # Momentum: momentum12_1 또는 6_1 — 0% ~ 100% 가 0~5.
    mom_val = momentum.get("momentum12_1")
    if mom_val is None:
        mom_val = momentum.get("momentum6_1")
    mom = _normalizeScore(_toFloat(mom_val), 0, 1.0)  # 100% → 5 점.
    # RiskInverse: 변동성 낮을수록 좋음 (KR 평균 25~30%) — RV20 0.2 → 5, 0.8 → 0.
    rv20 = _toFloat(volatility.get("realizedVol_20d"))
    risk_inv = _normalizeScore(-(rv20 if rv20 is not None else 0.8), -0.8, -0.2)  # 0.2 → 5, 0.8 → 0
    # Factor: R² 0~1 (시장 설명력 = 안정성 일부) — *0~100* 단위면 /100.
    r2 = _toFloat(beta.get("r2"))
    if r2 is not None and r2 > 1:
        r2 /= 100
    fac = _normalizeScore(r2, 0, 0.8)
    # Forecast: conformal CI 폭이 좁을수록 양호 (신뢰), point 양수일수록 좋음. 종합 = (point - halfWidth) 양수 정도.
    point = _toFloat(
        forecast.get("summary", {}).get("cumulativeReturn") if isinstance(forecast.get("summary"), dict) else None
    )
    half = _toFloat(forecast.get("conformalHalfWidth"))
    fc_signal = (point if point is not None else 0) - (half if half is not None else 0.1)
    fc = _normalizeScore(fc_signal, -0.1, 0.05)
    return {
        "categories": ["기술", "모멘텀", "리스크(역)", "팩터", "예측"],
        "series": [
            {
                "key": "snowflake",
                "label": "종합",
                "color": "#2563eb",
                "intent": "primary",
                "unit": "점",
                "type": "line",
                "axis": "left",
                "data": [round(tech, 2), round(mom, 2), round(risk_inv, 2), round(fac, 2), round(fc, 2)],
            }
        ],
        "options": {"maxValue": 5},
    }


def buildQuantAnnualReturns(stockCode: str) -> dict[str, Any]:
    """연도별 수익률 bar — best style. trend kind (categories=연도, series bar)."""
    bt = _backtestAllStyles(stockCode)
    if bt is None:
        return {"categories": [], "series": []}
    results = bt.get("results") or {}
    best_key = None
    best_sharpe = float("-inf")
    for k, r in results.items():
        s = getattr(r, "sharpe", None) or 0
        if s > best_sharpe:
            best_sharpe = s
            best_key = k
    if best_key is None:
        return {"categories": [], "series": []}
    rets = bt["returns"].get(best_key) or []
    annual: dict[int, float] = {}
    for d, r in zip(bt["dates"], rets):
        if r is None or len(d) < 4:
            continue
        try:
            y = int(d[:4])
        except ValueError:
            continue
        annual.setdefault(y, 1.0)
        annual[y] *= 1 + r
    years = sorted(annual.keys())
    data = [(annual[y] - 1) * 100 for y in years]
    return {
        "categories": [str(y) for y in years],
        "series": [
            {
                "key": "annual",
                "label": f"연수익률 ({_STYLE_LABELS.get(best_key, best_key)})",
                "color": "#2563eb",
                "intent": "primary",
                "unit": "%",
                "type": "bar",
                "axis": "left",
                "data": data,
            }
        ],
    }
