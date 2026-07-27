"""buildView — catalog 의 cardKey → 완성된 View dict.

설계 사상 (SSOT):
- catalog 의 SeriesPlan 이 series 모양 + 색상 + **데이터 정의** 까지 한 곳에 선언.
- builder 는 norm DataFrame 을 한 번 만들고 SeriesPlan 의 데이터 정의 보고
  자동으로 추출 + 합성 + 비율 + YoY 계산.
- statements/ratios 함수 신설 0 — accounts.py 의 표준 28 항목만 활용.

SeriesPlan 데이터 정의 우선순위 (한 series 마다 하나):
1. ratio    — {num, den, scale?}     비율 = sum(num) / sum(den) * scale
2. yoy      — account 문자열          YoY % = (cur-prev)/prev * 100
3. compose  — {accountKey: sign}     가산 합성
4. account  — 단일 표준 항목         extractSeries 단일 호출

위 4 가지 다 없으면 catalog 의 `statementsCall` 호출 fallback (legacy
호환 — analysis.* topic / 기존 ratios.profitability 등).
"""

from __future__ import annotations

import importlib
from datetime import datetime, timezone
from typing import Any

from dartlab.viz.adapterPlans import ADAPTER_PLANS, ALWAYS, NORM_ADAPTERS
from dartlab.viz.catalog import CATALOG
from dartlab.viz.data import _cache, normalize, ratios, statements  # noqa: F401 — _cache.getCompany + normalize 호환
from dartlab.viz.display.finance._cache import getNormFinance, getTtmNorm
from dartlab.viz.display.finance.accounts import allStock, extractSeries
from dartlab.viz.display.finance.periods import lastNPeriods
from dartlab.viz.schema import (
    CatalogEntry,
    PeriodKind,
    Series,
    SeriesPlan,
    View,
    makeBinding,
    makeMeta,
)

_ANALYSIS_PREFIX = "analysis."


def _selectNorm(company: Any, useTtm: bool) -> Any:
    """useTtm True → TTM 화 norm (분기 IS/CF 4Q 합산). False → raw norm."""
    return getTtmNorm(company) if useTtm else getNormFinance(company)


def _sumWeighted(norm: Any, terms: dict[str, int], periods: list[str]) -> list[float | None]:
    """compose 또는 ratio 의 분자/분모 가산.

    terms = {accountKey: sign} 형태. 각 항목 extractSeries 후 sign 곱해 합산.
    한 기간이라도 None 이면 그 기간 결과 None (보수적).
    """
    n = len(periods)
    if not terms:
        return [None] * n
    series_by_key = {k: extractSeries(norm, k, periods) for k in terms}
    out: list[float | None] = []
    for i in range(n):
        total: float = 0.0
        valid = False
        for k, sign in terms.items():
            v = series_by_key[k][i]
            if v is None:
                continue
            total += sign * float(v)
            valid = True
        out.append(total if valid else None)
    return out


def _ratioSeries(norm: Any, ratio: dict[str, Any], periods: list[str]) -> list[float | None]:
    """ratio = {num, den, scale?, denMethod?} → 시계열.

    denMethod (분모 처리):
        - "latest" : 시점값 그대로 (default, legacy).
        - "average": (begin+end)/2 trailing-2 평균. textbook ROE 정공법 — stock
          분모 (BS 항목) 일 때만 의미 있음. flow/stock 자동 판정 안 됨.
          명시 안 했고 den_terms 가 *모두* stock 이면 자동 "average" 적용.
    """
    num_terms: dict[str, int] = ratio.get("num") or ratio.get("numerator") or {}
    den_terms: dict[str, int] = ratio.get("den") or ratio.get("denominator") or {}
    scale = float(ratio.get("scale", 100))
    denMethod: str = ratio.get("denMethod") or ("average" if allStock(den_terms.keys()) else "latest")
    num = _sumWeighted(norm, num_terms, periods)
    den_raw = _sumWeighted(norm, den_terms, periods)
    if denMethod == "average":
        # trailing-2 평균 — i==0 은 자기값. textbook (begin+end)/2 ROE 일치.
        den: list[float | None] = []
        for i in range(len(periods)):
            cur = den_raw[i]
            if cur is None:
                den.append(None)
                continue
            if i == 0:
                den.append(cur)
                continue
            prev = den_raw[i - 1]
            den.append((cur + prev) / 2 if prev is not None else cur)
    else:
        den = den_raw
    out: list[float | None] = []
    for i in range(len(periods)):
        n, d = num[i], den[i]
        if n is None or d is None or d == 0:
            out.append(None)
        else:
            out.append(n / d * scale)
    return out


def _yoySeries(norm: Any, account: str, periods: list[str]) -> list[float | None]:
    """단일 account 의 YoY (%). periods 가 시간 순 정렬이라고 가정."""
    base = extractSeries(norm, account, periods)
    out: list[float | None] = [None]
    for i in range(1, len(periods)):
        prev, curr = base[i - 1], base[i]
        if prev is None or curr is None or prev == 0:
            out.append(None)
        else:
            out.append((curr - prev) / abs(prev) * 100)
    return out


def _analysisCallSeries(spec: dict[str, Any], stockCode: str, periods: list[str]) -> list[float | None] | None:
    """analysisCall = {module, fn, outputKey, [outputType]} → 시계열.

    module: "valuation.dFV" 처럼 dartlab.analysis.* 하위 경로.
    fn: 호출 함수명. 인자는 Company 객체 (자동 주입).
    outputKey: 반환 dict 의 어떤 키를 시리즈로 쓸지. dot-path 지원 (예: "history.roic").
    outputType: "timeseries" (기본, period 매칭) 또는 "scalar" (모든 period 같은 값).
    """
    moduleName = spec.get("module")
    fnName = spec.get("fn")
    outputKey = spec.get("outputKey", "")
    outputType = spec.get("outputType", "timeseries")
    if not moduleName or not fnName:
        return None
    try:
        mod = importlib.import_module(f"dartlab.analysis.{moduleName}")
    except ImportError:
        return None
    fn = getattr(mod, fnName, None)
    if fn is None:
        return None
    company = _cache.getCompany(stockCode)
    try:
        result = fn(company)
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(result, dict):
        return None

    def _drill(d: Any, path: str) -> Any:
        # outputKey "history.mScore" 형태: "history" 까지 dict 워킹 + 나머지는 per-row 키 (행 안에서 찾음).
        cur = d
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return cur if isinstance(cur, list) else None
        return cur

    val = _drill(result, outputKey) if outputKey else result

    if outputType == "scalar":
        try:
            num = float(val) if val is not None else None
            return [num] * len(periods)
        except (TypeError, ValueError):
            return None

    # timeseries: list[dict] 인 경우 period 기준 매칭. period 키 이름은 자유 ("period"/"yr"/"quarter").
    # period 포맷 차이 (analysis "2024" ↔ builder "2024-FY", "2024Q3" ↔ "2024-Q3") 흡수.
    if isinstance(val, list):
        lookup: dict[str, float] = {}
        for row in val:
            if not isinstance(row, dict):
                continue
            row_period = row.get("period") or row.get("yr") or row.get("quarter") or row.get("date")
            row_value = row.get("value") or row.get(outputKey.split(".")[-1])
            if row_period is not None and row_value is not None:
                try:
                    f = float(row_value)
                except (TypeError, ValueError):
                    continue
                rp = str(row_period)
                lookup[rp] = f
                if len(rp) == 4 and rp.isdigit():
                    lookup[f"{rp}-FY"] = f
                elif len(rp) == 6 and rp[:4].isdigit() and rp[4] == "Q":
                    lookup[f"{rp[:4]}-Q{rp[5]}"] = f
        return [lookup.get(p) for p in periods]
    return None


def _seriesDataFromPlan(
    plan: SeriesPlan, norm: Any, periods: list[str], stockCode: str = ""
) -> list[float | None] | None:
    """SeriesPlan 의 데이터 정의 → 시계열. None 반환 시 fallback (raw lookup)."""
    if "ratio" in plan:
        return _ratioSeries(norm, plan["ratio"], periods)
    if "yoy" in plan:
        return _yoySeries(norm, plan["yoy"], periods)
    if "compose" in plan:
        return _sumWeighted(norm, plan["compose"], periods)
    if "account" in plan:
        return extractSeries(norm, plan["account"], periods)
    if "analysisCall" in plan and stockCode:
        return _analysisCallSeries(plan["analysisCall"], stockCode, periods)
    return None


def _resolveLegacyCall(topic: str, stockCode: str, useTtm: bool = False) -> tuple[str, Any, Any]:
    """statementsCall fallback 용 — topic → (kind, context, module)."""
    company = _cache.getCompany(stockCode)
    if topic.startswith(_ANALYSIS_PREFIX):
        moduleName = topic[len(_ANALYSIS_PREFIX) :]
        mod = importlib.import_module(f"dartlab.analysis.financial.{moduleName}")
        return "analysis", company, mod
    if topic == "ratios":
        norm = _selectNorm(company, useTtm)
        return "data", norm, ratios
    if topic in ("IS", "BS", "CF"):
        norm = _selectNorm(company, useTtm)
        return "data", norm, statements
    raise ValueError(f"viz.builder: unknown topic '{topic}'")


def _callLegacy(
    kind: str, context: Any, mod: Any, callName: str, nPeriods: int, periodKind: PeriodKind
) -> dict[str, Any]:
    fn = getattr(mod, callName, None)
    if fn is None:
        raise ValueError(f"viz.builder: 모듈 '{mod.__name__}' 에 '{callName}' 없음")
    if kind == "analysis":
        result = fn(context)
        return result if isinstance(result, dict) else {}
    return fn(context, nPeriods, periodKind)


def _extractFromRaw(raw: dict[str, Any], key: str, nPeriods: int) -> list[float | None]:
    """legacy raw dict 에서 key 시계열 추출. 3 패턴 지원."""
    if key in raw:
        v = raw[key]
        if isinstance(v, list):
            return v
    rows = raw.get("rows")
    if isinstance(rows, list):
        for r in rows:
            if isinstance(r, dict) and r.get("key") == key:
                return list(r.get("values") or [])
    history = raw.get("history")
    if isinstance(history, list) and history:
        return [h.get(key) if isinstance(h, dict) else None for h in history]
    return [None] * nPeriods


def _periodsFromRaw(raw: dict[str, Any]) -> list[str]:
    p = raw.get("periods")
    if isinstance(p, list):
        return [str(x) for x in p]
    history = raw.get("history")
    if isinstance(history, list):
        return [str(h.get("period", "")) for h in history if isinstance(h, dict)]
    return []


def _materializeSeries(plan: SeriesPlan, data: list[float | None]) -> Series:
    series: Series = {}
    for field in ("key", "label", "color", "intent", "unit", "type", "axis", "stack"):
        if field in plan:
            series[field] = plan[field]  # type: ignore[literal-required]
    series["data"] = data
    return series


_NON_TREND_KINDS = frozenset(
    {
        "kpiTile",
        "diffView",
        "topList",
        "comparisonTable",
        "gauge",
        "phaseIndicator",
        "sankey",
        "scatter",
        "matrix",
        "radar",
        "waterfall",
        "narrativeBridge",
        "scoreBadge",
    }
)


def _adapterArgs(plan, company, stockCode, norm, periods):
    """계획이 선언한 인자 모양대로 빌더 인자를 만든다."""
    if plan.arg == "company":
        return (company,)
    if plan.arg == "stockCode":
        return (stockCode,)
    return (norm, periods)


def _applyAdapterPlan(plan, result: dict, view: dict[str, Any]) -> None:
    """빌더 결과를 계획대로 view 에 합친다."""
    if plan.full:
        view.update(result)
    else:
        for key, mode, default in plan.fields:
            if mode == ALWAYS:
                view[key] = result.get(key, default)
            elif key in result:
                view[key] = result[key]
    if plan.mergeOptions and "options" in result:
        view["options"] = {**view.get("options", {}), **result["options"]}


def _buildSpecDrivenFields(adapterName: str, spec: dict, company: Any, norm, periods: list[str]) -> dict[str, Any]:
    """표로 못 적는 네 어댑터. spec 을 읽거나 결과가 비면 다른 데이터로 대신한다.

    나머지는 "빌더 하나 부르고 키 옮기기"라 표로 충분한데, 이 넷은 spec 의 내용에 따라
    호출이 달라지거나 실패 시 다른 경로를 탄다. 표에 억지로 우겨넣으면 표가 표가 아니게
    되므로 여기 남긴다.
    """
    from dartlab.viz.display import adapters

    if adapterName in ("kpiFromNorm", "diffFromNorm"):
        fields: dict[str, Any] = {"tiles": adapters.buildKpiTilesFromNorm(norm, periods, spec.get("tilePlans", []))}
        if adapterName == "diffFromNorm":
            fields["periodLabel"] = spec.get("periodLabel", "YoY")
        return fields
    if adapterName == "flagsTopList":
        flags = adapters._safeCall(spec.get("module", ""), spec.get("fn", ""), company)
        items = adapters.buildTopListFromFlags(flags)
        # analysis 함수 결과 비면 norm 기반 fallback.
        if not items:
            items = adapters.buildAnomalyTopList(company)
        return {"items": items, "direction": spec.get("direction", "desc")}
    if adapterName == "snowflakeKpi":
        return {"tiles": adapters.buildSnowflakeKpi(company, spec.get("tilePlans", []))}
    return {"tiles": adapters.buildQuantComingSoon(spec.get("label", "준비 중")).get("tiles", [])}


_SPEC_DRIVEN_ADAPTERS = frozenset({"kpiFromNorm", "diffFromNorm", "flagsTopList", "snowflakeKpi", "quantComingSoon"})


def _buildKindSpecView(
    entry: CatalogEntry,
    company: Any,
    stockCode: str,
    periodKind: PeriodKind,
    nPeriods: int,
    useTtm: bool = False,
) -> View | None:
    """kpiTile/diffView/topList/comparisonTable/gauge/phaseIndicator/sankey/scatter dispatch.

    entry.dataSpec 의 `adapter` 키로 어댑터 선택. None 반환 시 호출자가 trend fallback.

    어느 빌더를 어떤 인자로 부르고 결과를 어떻게 합칠지는 `viz.adapterPlans` 의 표가 정한다.
    예전에는 여기 47 갈래 사슬이 있었는데, 갈래마다 하는 일이 같고 세 가지만 달라서 새 카드를
    붙일 때 옆 갈래를 복사하게 됐고 그러다 options 병합 같은 것이 갈래마다 어긋났다.
    """
    kind = entry.get("kind")
    spec = entry.get("dataSpec") or {}
    adapterName = spec.get("adapter", "")
    # _NON_TREND_KINDS 외에도 trend kind 가 adapter 명시한 경우 처리.
    # (P-DASH-V1 D6: capitalAllocationBars 는 kind=trend 지만 adapter dispatch 필요.)
    if kind not in _NON_TREND_KINDS and not adapterName:
        return None

    norm = None
    periods: list[str] = []
    if adapterName in NORM_ADAPTERS:
        norm = _selectNorm(company, useTtm)
        periods = lastNPeriods(norm, nPeriods, periodKind)

    view: dict[str, Any] = {
        "kind": kind,
        "title": entry.get("title", ""),
        "categories": periods,
        "series": [],
        "options": dict(entry.get("options") or {}),
    }

    if adapterName in _SPEC_DRIVEN_ADAPTERS:
        view.update(_buildSpecDrivenFields(adapterName, spec, company, norm, periods))
    else:
        plan = ADAPTER_PLANS.get(adapterName)
        if plan is not None:
            from dartlab.viz.display import adapters

            builder = getattr(adapters, plan.builder)
            _applyAdapterPlan(plan, builder(*_adapterArgs(plan, company, stockCode, norm, periods)), view)
        # 표에 없는 이름은 빈 spec 으로라도 kind 를 보존한다.

    view["evidenceBinding"] = makeBinding(stockCode, entry.get("topic", "BS"), periodKind, periods or [])
    view["meta"] = makeMeta(
        stockCode,
        corpName=getattr(company, "corpName", None),
        periodKind=periodKind,
        periods=periods,
        generatedAt=datetime.now(timezone.utc).isoformat(),
    )
    if "layout" in entry:
        view["layout"] = dict(entry["layout"])
    return view  # type: ignore[return-value]


def buildView(
    cardKey: str,
    stockCode: str,
    *,
    periodKind: PeriodKind = "annual",
    nPeriods: int = 8,
    useTtm: bool = False,
) -> View:
    """cardKey + stockCode → 완성된 View JSON.

    SeriesPlan 의 데이터 정의 (ratio/yoy/compose/account) 가 우선. 모든 series 가
    데이터 정의 보유 시 statementsCall 호출 없이 norm 만으로 처리. 일부라도
    데이터 정의 없는 series 가 있으면 fallback 으로 statementsCall 결과 lookup.

    kpiTile/diffView/topList/comparisonTable/gauge/phaseIndicator/sankey/scatter 는
    별도 어댑터 dispatch — 시계열 series 가 아닌 kind-별 spec 필드 채움.
    """
    if cardKey not in CATALOG:
        raise KeyError(f"viz.buildView: cardKey '{cardKey}' not in CATALOG")
    entry: CatalogEntry = CATALOG[cardKey]
    topic: str = entry.get("topic", "BS")  # type: ignore[assignment]

    # entry 의 ttmOptOut True → 카드 강제 raw norm. catalog 운영자가 분기 raw
    # 비교가 의도인 카드 (분기-on-분기 매출 YoY 등) 에서 박는 escape hatch.
    if entry.get("ttmOptOut"):
        useTtm = False

    # quant 탭 카드 (topic="price") 는 가격 데이터만 사용 — Company.rawFinance 무관.
    # 동시 7 카드 build 시 Company 생성 fail (데이터셋 miss) 가 fatal 안 되도록 graceful.
    if topic == "price":
        company = None
        corpName = None
        try:
            company = _cache.getCompany(stockCode)
            corpName = getattr(company, "corpName", None)
        except (ValueError, RuntimeError, OSError, AttributeError):
            # quant adapter 는 company 안 써도 됨 — stockCode 로 직접 가격 fetch.
            company = type("_StubCompany", (), {"stockCode": str(stockCode), "corpName": None})()
            corpName = None
    else:
        company = _cache.getCompany(stockCode)
        corpName = getattr(company, "corpName", None)

    # 비-시계열 kind 는 별도 어댑터.
    kind_view = _buildKindSpecView(entry, company, stockCode, periodKind, nPeriods, useTtm)
    if kind_view is not None:
        return kind_view  # type: ignore[return-value]

    plans = entry["seriesPlan"]
    allHaveDataDef = all(
        ("ratio" in p) or ("yoy" in p) or ("compose" in p) or ("account" in p) or ("analysisCall" in p) for p in plans
    )

    if allHaveDataDef and not topic.startswith(_ANALYSIS_PREFIX):
        # 모든 series 가 catalog 정의 → norm 한 번 + 자동 추출
        norm = _selectNorm(company, useTtm)
        periods = lastNPeriods(norm, nPeriods, periodKind)
        series: list[Series] = []
        for plan in plans:
            data = _seriesDataFromPlan(plan, norm, periods, stockCode)
            if data is None:
                data = [None] * len(periods)
            series.append(_materializeSeries(plan, data))
        bindingTopic = topic
    else:
        # legacy: statementsCall 호출 → raw dict → key lookup
        kind, context, mod = _resolveLegacyCall(topic, stockCode, useTtm)
        callName = entry.get("statementsCall")
        if not callName:
            raise ValueError(f"viz.builder: '{cardKey}' 의 seriesPlan 일부에 데이터 정의 누락 + statementsCall 없음")
        raw = _callLegacy(kind, context, mod, callName, nPeriods, periodKind)
        periods = _periodsFromRaw(raw)
        # 일부 series 는 catalog 정의, 일부는 raw lookup — 혼합 처리
        if not topic.startswith(_ANALYSIS_PREFIX) and topic in ("IS", "BS", "CF", "ratios"):
            norm = _selectNorm(company, useTtm)
        else:
            norm = None
        series = []
        for plan in plans:
            data = _seriesDataFromPlan(plan, norm, periods, stockCode) if norm is not None else None
            if data is None:
                data = _extractFromRaw(raw, plan["key"], len(periods))
            series.append(_materializeSeries(plan, data))
        bindingTopic = topic.split(".", 1)[1].upper() if topic.startswith(_ANALYSIS_PREFIX) else topic

    view: View = {
        "kind": entry["kind"],
        "title": entry["title"],
        "categories": periods,
        "series": series,
        "evidenceBinding": makeBinding(stockCode, bindingTopic, periodKind, periods),
        "meta": makeMeta(
            stockCode,
            corpName=corpName,
            periodKind=periodKind,
            periods=periods,
            generatedAt=datetime.now(timezone.utc).isoformat(),
        ),
        "options": dict(entry.get("options") or {}),
    }
    if "layout" in entry:
        view["layout"] = dict(entry["layout"])
    return view


__all__ = ["buildView"]
