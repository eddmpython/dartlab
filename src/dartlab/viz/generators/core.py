"""Company → VizSpec(ChartSpec) 자동 생성기 8종.

기존 ``tools/chart.py``의 ``spec_*`` 함수를 통합.

사용법::

    from dartlab.viz.generators import spec_revenue_trend, auto_chart

    spec = spec_revenue_trend(company)   # → dict (ChartSpec)
    specs = auto_chart(company)          # → list[dict]
"""

from __future__ import annotations

from typing import Any

from dartlab.core.palette import COLORS
from dartlab.synth.ratioCategories import RATIO_CATEGORIES
from dartlab.viz.spec.refs import chartEvidenceBinding

# ── 7영역 인사이트 상수 ──

_AREA_NAMES = ["performance", "profitability", "health", "cashflow", "governance", "risk", "opportunity"]
_AREA_LABELS = {
    "performance": "성과",
    "profitability": "수익성",
    "health": "건전성",
    "cashflow": "현금흐름",
    "governance": "지배구조",
    "risk": "리스크",
    "opportunity": "기회",
}
_GRADE_MAP = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 0}


def _safeVal(v: Any) -> float:
    """None → 0, 나머지 float 변환."""
    if v is None:
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _nullableNum(v: Any) -> float | None:
    """가격 row 용 숫자 변환. 결손은 0 이 아니라 None 으로 보존."""
    if v is None:
        return None
    if isinstance(v, str):
        v = v.replace(",", "").strip()
        if not v or v in {"-", "—"}:
            return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _rowValue(row: dict[str, Any], *keys: str) -> Any:
    """대소문자/원천별 컬럼 alias 를 흡수해 row 값을 읽는다."""
    if not row:
        return None
    lower_map = {str(k).lower(): v for k, v in row.items()}
    for key in keys:
        if key in row:
            return row[key]
        lowered = key.lower()
        if lowered in lower_map:
            return lower_map[lowered]
    return None


def _rowsFromAny(rows: Any) -> list[dict[str, Any]]:
    """Polars/Pandas/list[dict] 를 price-chart generator 입력으로 정규화."""
    if rows is None:
        return []
    if hasattr(rows, "to_dicts"):
        return list(rows.to_dicts())
    if hasattr(rows, "to_dict"):
        try:
            return list(rows.to_dict("records"))
        except TypeError:
            pass
    if isinstance(rows, list):
        return [dict(row) for row in rows if isinstance(row, dict)]
    return []


def _movingAverage(values: list[float | None], window: int) -> list[float | None]:
    out: list[float | None] = []
    for i in range(len(values)):
        chunk = values[max(0, i - window + 1) : i + 1]
        nums = [v for v in chunk if v is not None]
        if len(nums) < window:
            out.append(None)
        else:
            out.append(sum(nums) / len(nums))
    return out


def _normalizePriceRows(rows: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in _rowsFromAny(rows):
        date = _rowValue(row, "date", "Date", "BAS_DD", "basDd", "날짜")
        close = _nullableNum(_rowValue(row, "close", "Close", "TDD_CLSPRC", "CLSPRC_IDX", "종가"))
        if date is None or close is None:
            continue
        normalized.append(
            {
                "date": str(date),
                "open": _nullableNum(_rowValue(row, "open", "Open", "TDD_OPNPRC", "OPNPRC_IDX", "시가")),
                "high": _nullableNum(_rowValue(row, "high", "High", "TDD_HGPRC", "HGPRC_IDX", "고가")),
                "low": _nullableNum(_rowValue(row, "low", "Low", "TDD_LWPRC", "LWPRC_IDX", "저가")),
                "close": close,
                "volume": _nullableNum(_rowValue(row, "volume", "Volume", "ACC_TRDVOL", "거래량")),
            }
        )
    return sorted(normalized, key=lambda item: item["date"])


_FETCH_ERRORS = (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError)


def _annualBuild(company: Any):
    """연간 재무 시계열 `(series, years)`. 없으면 None.

    예전에는 `company.annual` 속성을 읽었다. 그 이름은 공개 표면에서 빠졌고
    `getattr(..., None)` 이 늘 None 을 돌려줘서, 이 값에 기대는 생성기 셋이 회사 자료와
    무관하게 항상 None 을 반환했다. 회사가 이미 갖고 있는 finance 빌드를 그대로 쓴다.
    """
    build = getattr(company, "_getFinanceBuild", None)
    if build is None:
        return None
    try:
        return build("y")
    except _FETCH_ERRORS:
        return None


def _ratioBuild(company: Any):
    """비율 시계열 `(seriesData, periods)`. 없으면 None.

    옛 `company.ratioSeries` 속성 자리. 지금 공급원은 `companyContext.getRatioSeries` 다.
    """
    try:
        from dartlab.analysis.financial.companyContext import getRatioSeries

        return getRatioSeries(company)
    except (ImportError, *_FETCH_ERRORS):
        return None


def _capitalFrame(company: Any):
    """배당 지표를 생성기가 기대하는 `year`/`dps` 형태로 맞춘다. 없으면 None.

    옛 `company.dividend` 속성 자리. 지금 남은 공급원은 `capital` 축의 현재 시점 한 행이라
    연도별 시계열이 아니다. 없는 시계열을 지어내지 않고 현재 한 점만 같은 열 이름으로 준다.
    """
    import polars as pl

    try:
        df = company.capital()
    except _FETCH_ERRORS:
        return None
    if df is None or getattr(df, "height", 0) == 0:
        return None
    row = df.row(0, named=True)
    if row.get("DPS") is None:
        return None
    frame = {"year": ["현재"], "dps": [row["DPS"]]}
    if row.get("배당수익률") is not None:
        frame["dividendYield"] = [row["배당수익률"]]
    return pl.DataFrame(frame)


def _insightResult(company: Any):
    """재무 인사이트 결과. 없으면 None.

    옛 `company.insights` accessor 자리. 지금 산출 경로는 인사이트 파이프라인이다.
    """
    try:
        from dartlab.analysis.financial.insight.pipeline import analyzeFinancial

        return analyzeFinancial(getattr(company, "stockCode", ""), company)
    except (ImportError, *_FETCH_ERRORS):
        return None


def _meta(company: Any, source: str) -> dict:
    """ChartSpec meta 블록 생성."""
    return {
        "source": source,
        "stockCode": getattr(company, "stockCode", ""),
        "corpName": getattr(company, "corpName", ""),
    }


def _withVisualContext(
    spec: dict,
    *,
    purpose: str,
    evidenceIds: list[str] | None = None,
    binding: dict[str, Any] | None = None,
) -> dict:
    """Add optional visual-policy fields while preserving ChartSpec compatibility.

    binding 은 차트 단위 evidenceBinding dict (refs.chartEvidenceBinding 결과).
    drill-back 회로의 진입점 — emit_chart 가드를 통과하려면 binding 또는
    evidenceIds 가 채워져 있어야 한다.
    """
    spec["purpose"] = purpose
    if evidenceIds:
        spec["evidenceIds"] = evidenceIds
    if binding:
        spec["evidenceBinding"] = binding
    return spec


# ── spec 생성기 8종 ──


def specRevenueTrend(company: Any, *, nYears: int = 5) -> dict | None:
    """IS 매출·영업이익·순이익 combo 차트 ChartSpec."""
    ann = _annualBuild(company)
    if not ann:
        return None
    ann_data, ann_years = ann
    is_data = ann_data.get("IS", {})

    key_accounts = [
        ("매출액", ["sales", "revenue", "interest_income"]),
        ("영업이익", ["operating_income", "operating_profit"]),
        ("당기순이익", ["net_income", "profit_for_the_period", "profit_loss"]),
    ]
    chart_types = ["bar", "line", "line"]
    colors = [COLORS[2], COLORS[0], COLORS[3]]

    series = []
    for i, (label, candidates) in enumerate(key_accounts):
        vals = None
        for cand in candidates:
            if cand in is_data and any(v is not None for v in is_data[cand]):
                vals = is_data[cand]
                break
        if vals is None:
            continue
        recent = vals[-nYears:]
        series.append(
            {
                "name": label,
                "data": [_safeVal(v) for v in recent],
                "color": colors[i],
                "type": chart_types[i],
            }
        )

    if not series:
        return None
    periods = list(ann_years[-nYears:])
    return _withVisualContext(
        {
            "chartType": "combo",
            "title": f"{company.corpName} 손익 추이",
            "series": series,
            "categories": periods,
            "options": {"unit": "백만원"},
            "meta": _meta(company, "finance"),
        },
        purpose="trend",
        evidenceIds=["finance:IS"],
        binding=chartEvidenceBinding(
            stockCode=getattr(company, "stockCode", ""),
            source="finance",
            topic="IS",
            periodKind="Y",
            periods=periods,
        ),
    )


def specCashflowWaterfall(company: Any) -> dict | None:
    """CF 워터폴 브릿지 ChartSpec."""
    ann = _annualBuild(company)
    if not ann:
        return None
    ann_data, ann_years = ann
    cf_data = ann_data.get("CF", {})

    accts = {
        "cash_and_cash_equivalents_beginning": "기초현금",
        "operating_cashflow": "영업활동",
        "investing_cashflow": "투자활동",
        "financing_cashflow": "재무활동",
        "cash_and_cash_equivalents_ending": "기말현금",
    }
    vals = {}
    for key, label in accts.items():
        arr = cf_data.get(key, [])
        vals[label] = _safeVal(arr[-1]) if arr else 0.0

    if vals["기초현금"] == 0 and vals["영업활동"] == 0:
        return None

    labels = ["기초현금", "영업활동", "투자활동", "재무활동", "기말현금"]
    data = [vals[lb] for lb in labels]

    return _withVisualContext(
        {
            "chartType": "waterfall",
            "title": f"{company.corpName} 현금흐름 브릿지 ({ann_years[-1]})",
            "series": [{"name": "현금흐름", "data": data, "color": COLORS[2]}],
            "categories": labels,
            "options": {"unit": "백만원"},
            "meta": _meta(company, "finance"),
        },
        purpose="bridge",
        evidenceIds=["finance:CF"],
        binding=chartEvidenceBinding(
            stockCode=getattr(company, "stockCode", ""),
            source="finance",
            topic="CF",
            periodKind="Y",
            periods=[str(ann_years[-1])],
        ),
    )


def specBalanceSheet(company: Any, *, nYears: int = 5) -> dict | None:
    """BS 유동/비유동 자산 stacked bar ChartSpec."""
    ann = _annualBuild(company)
    if not ann:
        return None
    ann_data, ann_years = ann
    bs_data = ann_data.get("BS", {})

    accounts = [
        ("유동자산", "current_assets", COLORS[2]),
        ("비유동자산", "noncurrent_assets", COLORS[3]),
    ]
    series = []
    for label, key, color in accounts:
        arr = bs_data.get(key, [])
        if not arr:
            continue
        recent = arr[-nYears:]
        series.append(
            {
                "name": label,
                "data": [_safeVal(v) for v in recent],
                "color": color,
                "type": "bar",
                "stack": "assets",
            }
        )

    if not series:
        return None
    periods = list(ann_years[-nYears:])
    return _withVisualContext(
        {
            "chartType": "bar",
            "title": f"{company.corpName} 자산 구성",
            "series": series,
            "categories": periods,
            "options": {"unit": "백만원", "stacked": True},
            "meta": _meta(company, "finance"),
        },
        purpose="composition",
        evidenceIds=["finance:BS"],
        binding=chartEvidenceBinding(
            stockCode=getattr(company, "stockCode", ""),
            source="finance",
            topic="BS",
            periodKind="Y",
            periods=periods,
        ),
    )


def specProfitability(company: Any, *, nYears: int = 5) -> dict | None:
    """수익성 비율 라인 ChartSpec (ratioSeries 기반)."""
    rs = _ratioBuild(company)
    if rs is None:
        return None
    if isinstance(rs, tuple) and len(rs) == 2:
        ratio_dict = rs[0].get("RATIO", {})
        periods = rs[1]
    else:
        return None

    metrics = [
        ("ROE", "roe", COLORS[0]),
        ("영업이익률", "operatingMargin", COLORS[2]),
        ("순이익률", "netMargin", COLORS[3]),
    ]
    series = []
    for label, key, color in metrics:
        vals = ratio_dict.get(key, [])
        if not vals or not any(v is not None for v in vals):
            continue
        recent = vals[-nYears * 4 :]  # 분기별
        series.append(
            {
                "name": label,
                "data": [_safeVal(v) for v in recent],
                "color": color,
                "type": "line",
            }
        )

    if not series:
        return None
    chart_periods = list(periods[-len(series[0]["data"]) :])
    return _withVisualContext(
        {
            "chartType": "line",
            "title": f"{company.corpName} 수익성 추이",
            "series": series,
            "categories": chart_periods,
            "options": {"unit": "%"},
            "meta": _meta(company, "finance"),
        },
        purpose="trend",
        evidenceIds=["finance:ratioSeries"],
        binding=chartEvidenceBinding(
            stockCode=getattr(company, "stockCode", ""),
            source="finance",
            topic="RATIO",
            periodKind="Q",
            periods=chart_periods,
        ),
    )


def specDividend(company: Any) -> dict | None:
    """배당 시계열 combo ChartSpec."""
    # 예전에는 `report.dividend` 를 먼저 봤다. 그 경로는 폐기 예정이라 경고를 내고, 돌려주는
    # 표도 DART 원본 열(se·thstrm·frmtrm)이라 아래가 기대하는 year/dps 형태가 아니다. 그래서
    # 값이 있는데도 늘 형태 검사에서 걸려 None 이 됐고, `_capitalFrame` 까지 가지도 못했다.
    div_df = _capitalFrame(company)
    if div_df is None:
        return None
    if "year" not in div_df.columns or "dps" not in div_df.columns:
        return None

    df = div_df.sort("year")
    years = [str(y) for y in df["year"].to_list()]
    dps_vals = [_safeVal(v) for v in df["dps"].to_list()]

    if not years or all(v == 0 for v in dps_vals):
        return None

    series: list[dict] = [{"name": "DPS(원)", "data": dps_vals, "color": COLORS[2], "type": "bar"}]

    if "dividendYield" in df.columns:
        series.append(
            {
                "name": "배당수익률(%)",
                "data": [_safeVal(v) for v in df["dividendYield"].to_list()],
                "color": COLORS[0],
                "type": "line",
            }
        )

    return _withVisualContext(
        {
            "chartType": "combo",
            "title": f"{company.corpName} 배당 분석",
            "series": series,
            "categories": years,
            "options": {"unit": "원", "secondaryY": ["배당수익률(%)"]},
            "meta": _meta(company, "finance"),
        },
        purpose="trend",
        evidenceIds=["report:dividend"],
        binding=chartEvidenceBinding(
            stockCode=getattr(company, "stockCode", ""),
            source="report",
            topic="dividend",
            periodKind="Y",
            periods=years,
        ),
    )


def specInsightRadar(company: Any) -> dict | None:
    """7영역 인사이트 레이더 ChartSpec."""
    insights = _insightResult(company)
    if insights is None or not hasattr(insights, "performance"):
        return None

    grades = {}
    for name in _AREA_NAMES:
        area = getattr(insights, name, None)
        grades[name] = area.grade if area and hasattr(area, "grade") else "F"

    categories = [_AREA_LABELS.get(n, n) for n in _AREA_NAMES]
    data = [_GRADE_MAP.get(grades[n], 0) for n in _AREA_NAMES]

    return _withVisualContext(
        {
            "chartType": "radar",
            "title": f"{company.corpName} 투자 인사이트",
            "series": [{"name": company.corpName, "data": data, "color": COLORS[0]}],
            "categories": categories,
            "options": {"maxValue": 5},
            "meta": _meta(company, "insight"),
        },
        purpose="comparison",
        evidenceIds=["insight:grades"],
        binding=chartEvidenceBinding(
            stockCode=getattr(company, "stockCode", ""),
            source="analysis",
            topic="insightGrades",
            extra={"axes": list(_AREA_NAMES)},
        ),
    )


def specRatioSparklines(company: Any) -> dict | None:
    """비율 스파크라인 배열 ChartSpec."""
    rs = _ratioBuild(company)
    if rs is None:
        return None
    if isinstance(rs, tuple) and len(rs) == 2:
        ratio_dict = rs[0].get("RATIO", {})
        periods = rs[1]
    else:
        return None

    sparklines = []
    for cat_name, fields in RATIO_CATEGORIES:
        cat_items = []
        for field_name in fields:
            vals = ratio_dict.get(field_name, [])
            if not vals:
                continue
            valid_count = sum(1 for v in vals if v is not None)
            if valid_count < 2:
                continue
            latest = next((v for v in reversed(vals) if v is not None), None)
            recent_valid = [v for v in vals[-8:] if v is not None]
            trend = (
                "up"
                if len(recent_valid) >= 2 and recent_valid[-1] > recent_valid[-2]
                else ("down" if len(recent_valid) >= 2 else "neutral")
            )
            cat_items.append(
                {
                    "field": field_name,
                    "values": [_safeVal(v) for v in vals[-20:]],
                    "latest": latest,
                    "trend": trend,
                }
            )
        if cat_items:
            sparklines.append({"category": cat_name, "metrics": cat_items[:3]})

    if not sparklines:
        return None
    chart_periods = list(periods[-20:])
    return _withVisualContext(
        {
            "chartType": "sparkline",
            "title": f"{company.corpName} 비율 스파크라인",
            "series": sparklines,
            "categories": chart_periods,
            "options": {},
            "meta": _meta(company, "finance"),
        },
        purpose="trend",
        evidenceIds=["finance:ratioSeries"],
        binding=chartEvidenceBinding(
            stockCode=getattr(company, "stockCode", ""),
            source="finance",
            topic="RATIO",
            periodKind="Q",
            periods=chart_periods,
        ),
    )


def specDiffHeatmap(company: Any) -> dict | None:
    """diff 변화 밀도 히트맵 ChartSpec."""
    try:
        diff_df = company.diff()
    except (AttributeError, TypeError, OSError):
        return None
    if diff_df is None or not hasattr(diff_df, "shape") or diff_df.shape[0] == 0:
        return None

    change_rates: dict[str, float] = {}
    for row in diff_df.iter_rows(named=True):
        topic = row["topic"]
        rate = row.get("changeRate", 0) or 0
        change_rates[topic] = float(rate)

    sorted_topics = sorted(change_rates.items(), key=lambda x: x[1], reverse=True)[:30]
    heatmap_data = []
    for topic, rate in sorted_topics:
        intensity = "high" if rate >= 0.5 else ("medium" if rate >= 0.2 else "low")
        heatmap_data.append({"topic": topic, "changeRate": round(rate, 4), "intensity": intensity})

    return _withVisualContext(
        {
            "chartType": "heatmap",
            "title": f"{company.corpName} 공시 변화 밀도",
            "series": [{"name": "변화율", "data": heatmap_data}],
            "categories": [d["topic"] for d in heatmap_data],
            "options": {"colorScale": {"low": "#22c55e", "medium": "#f59e0b", "high": "#ea4647"}},
            "meta": _meta(company, "panel"),
        },
        purpose="evidence",
        evidenceIds=["panel:diff"],
        binding=chartEvidenceBinding(
            stockCode=getattr(company, "stockCode", ""),
            source="panel",
            topic="diff",
            extra={"topicCount": len(heatmap_data)},
        ),
    )


# ── 레지스트리 ──

# ── Phase A 신규 spec ──


def specPeerRadar(peerData: dict) -> dict | None:
    """4축(수익성/성장/품질/부채) 백분위 레이더 차트 spec.

    peer_data: calcPeerPosition 반환 dict.
    """
    axes = [
        ("수익성", peerData.get("profitability_pct")),
        ("성장성", peerData.get("growth_pct")),
        ("이익품질", peerData.get("quality_pct")),
        ("안정성", 100 - peerData.get("debt_pct", 50) if peerData.get("debt_pct") is not None else None),
    ]
    vals = [v if v is not None else 50 for _, v in axes]
    labels = [a[0] for a in axes]

    return {
        "chartType": "radar",
        "title": "시장 내 위치 (백분위)",
        "series": [{"name": "백분위", "data": vals, "color": COLORS[0]}],
        "categories": labels,
        "options": {"unit": "%", "maxValue": 100},
        "purpose": "comparison",
        "evidenceIds": ["scan:peerPosition"],
        "meta": {
            "source": "scan/extended::calcPeerPosition",
            "statement": "PEER",
            "total_stocks": peerData.get("total_stocks"),
        },
        "evidenceBinding": chartEvidenceBinding(
            stockCode=peerData.get("stockCode", ""),
            source="scan",
            topic="peerPosition",
            extra={"axes": labels, "totalStocks": peerData.get("total_stocks")},
        ),
    }


def specSensitivityHeatmap(grid: list[dict]) -> dict | None:
    """DCF 민감도 히트맵 spec.

    grid: sensitivityAnalysis 반환 list[{wacc, g, fairValue}].
    """
    if not grid:
        return None
    waccs = sorted({r["wacc"] for r in grid})
    gs = sorted({r["g"] for r in grid})
    matrix = []
    for g_val in gs:
        row = []
        for w_val in waccs:
            fv = next((r["fairValue"] for r in grid if r["wacc"] == w_val and r["g"] == g_val), None)
            row.append(fv)
        matrix.append(row)

    return {
        "chartType": "heatmap",
        "title": "DCF 민감도 (WACC × 성장률)",
        "series": [{"name": f"{g:.1f}%", "data": row} for g, row in zip(gs, matrix, strict=False)],
        "categories": [f"{w:.1f}%" for w in waccs],
        "options": {"unit": "원", "yLabels": [f"{g:.1f}%" for g in gs]},
        "purpose": "valuation",
        "evidenceIds": ["valuation:sensitivity"],
        "meta": {"source": "core/finance/dcf::sensitivityAnalysis", "statement": "PRICE"},
        "evidenceBinding": chartEvidenceBinding(
            stockCode="",
            source="valuation",
            topic="sensitivity",
            extra={"gridSize": len(grid)},
        ),
    }


def specMarginTrend(history: list[dict]) -> dict | None:
    """마진 3축(매출총이익/영업이익/순이익률) 시계열 line spec."""
    if not history:
        return None
    periods = [h.get("period", "") for h in history]
    return {
        "chartType": "line",
        "title": "마진 추이",
        "series": [
            {
                "name": "매출총이익률",
                "data": [h.get("grossMargin") for h in history],
                "color": COLORS[0],
                "type": "line",
            },
            {
                "name": "영업이익률",
                "data": [h.get("operatingMargin") for h in history],
                "color": COLORS[1],
                "type": "line",
            },
            {"name": "순이익률", "data": [h.get("netMargin") for h in history], "color": COLORS[2], "type": "line"},
        ],
        "categories": periods,
        "options": {"unit": "%"},
        "purpose": "trend",
        "evidenceIds": ["finance:IS"],
        "meta": {"source": "analysis/financial::calcMarginTrend", "statement": "IS"},
        "evidenceBinding": chartEvidenceBinding(
            stockCode="",
            source="finance",
            topic="IS",
            periodKind="Q",
            periods=periods,
            extra={"derivation": "calcMarginTrend"},
        ),
    }


def specLeverageTrend(history: list[dict]) -> dict | None:
    """부채비율 시계열 line spec."""
    if not history:
        return None
    periods = [h.get("period", "") for h in history]
    return {
        "chartType": "line",
        "title": "레버리지 추이",
        "series": [
            {"name": "부채비율", "data": [h.get("debtRatio") for h in history], "color": COLORS[3], "type": "line"}
        ],
        "categories": periods,
        "options": {"unit": "%"},
        "purpose": "risk",
        "evidenceIds": ["finance:BS"],
        "meta": {"source": "analysis/financial::calcLeverage", "statement": "BS"},
        "evidenceBinding": chartEvidenceBinding(
            stockCode="",
            source="finance",
            topic="BS",
            periodKind="Q",
            periods=periods,
            extra={"derivation": "calcLeverage"},
        ),
    }


def specGrowthYoyBar(history: list[dict]) -> dict | None:
    """매출/영업이익/순이익 YoY bar chart spec."""
    if not history:
        return None
    periods = [h.get("period", "") for h in history]
    return {
        "chartType": "bar",
        "title": "성장률 YoY",
        "series": [
            {"name": "매출 YoY", "data": [h.get("revenueYoY") for h in history], "color": COLORS[0], "type": "bar"},
            {"name": "영업이익 YoY", "data": [h.get("opYoY") for h in history], "color": COLORS[1], "type": "bar"},
        ],
        "categories": periods,
        "options": {"unit": "%"},
        "purpose": "trend",
        "evidenceIds": ["finance:IS"],
        "meta": {"source": "analysis/financial::calcRevenueGrowth", "statement": "IS"},
        "evidenceBinding": chartEvidenceBinding(
            stockCode="",
            source="finance",
            topic="IS",
            periodKind="Q",
            periods=periods,
            extra={"derivation": "calcRevenueGrowth"},
        ),
    }


def specRevenueScenarioBand(history: list[dict], forecasts: dict | None) -> dict | None:
    """매출 과거 실적 + Base/Bull/Bear 전망 밴드 spec."""
    if not history:
        return None
    periods = [h.get("period", "") for h in history]
    actuals = [h.get("revenue") for h in history]

    series: list[dict] = [{"name": "실적", "data": actuals, "color": COLORS[0], "type": "line"}]
    categories = periods

    if forecasts:
        fwd_periods = forecasts.get("periods", [])
        categories = periods + fwd_periods
        actuals_ext = actuals + [None] * len(fwd_periods)
        series[0]["data"] = actuals_ext

        for key, label, color in [
            ("base", "Base", COLORS[1]),
            ("bull", "Bull", COLORS[4]),
            ("bear", "Bear", COLORS[3]),
        ]:
            vals = forecasts.get(key, [])
            if vals:
                series.append({"name": label, "data": [None] * len(periods) + vals, "color": color, "type": "line"})

    return {
        "chartType": "line",
        "title": "매출 전망 시나리오 밴드",
        "series": series,
        "categories": categories,
        "options": {"unit": "원"},
        "purpose": "valuation",
        "evidenceIds": ["forecast:revenue"],
        "meta": {"source": "analysis/forecast", "statement": "IS"},
        "evidenceBinding": chartEvidenceBinding(
            stockCode="",
            source="forecast",
            topic="revenue",
            periodKind="MIXED",
            periods=categories,
            extra={"forecastKeys": list((forecasts or {}).keys()) if forecasts else []},
        ),
    }


# ── Phase 1.5 신규 chartType 8 종 ─────────────────────────────────────────


def specPeerMatrix(
    rows: list[dict],
    metrics: list[str],
    *,
    stockCode: str,
    corpName: str = "",
) -> dict | None:
    """동종업종 peer × metric 매트릭스.

    rows: ``[{"stockCode": "005930", "corpName": "삼성전자",
              "values": {"PER": 12.3, "ROE": 18.5, ...}}, ...]``
    metrics: 컬럼 라벨 리스트. 첫 행은 본 기업 (highlight=True).
    """
    if not rows or not metrics:
        return None
    series = []
    for metric in metrics:
        series.append(
            {
                "name": metric,
                "data": [_safeVal(r.get("values", {}).get(metric)) for r in rows],
            }
        )
    return {
        "chartType": "peer-matrix",
        "title": f"{corpName or stockCode} 동종업종 비교",
        "series": series,
        "categories": [r.get("corpName") or r.get("stockCode", "") for r in rows],
        "options": {
            "metrics": metrics,
            "highlightStockCode": stockCode,
            "rowMeta": [{"stockCode": r.get("stockCode"), "corpName": r.get("corpName")} for r in rows],
        },
        "purpose": "comparison",
        "evidenceIds": ["industry:peers"],
        "meta": {"source": "industry/peers", "statement": "PEER"},
        "evidenceBinding": chartEvidenceBinding(
            stockCode=stockCode,
            source="industry",
            topic="peers",
            extra={"peerCount": len(rows), "metricCount": len(metrics)},
        ),
    }


def specKpiRibbon(
    items: list[dict],
    *,
    stockCode: str,
    corpName: str = "",
) -> dict | None:
    """Hero KPI 카드 8 개 — landing KpiRibbon 의 ChartSpec 형태.

    items: ``[{"id", "label", "value", "unit", "period",
               "delta", "deltaTone", "tone", "note", "sparkValues",
               "valueRef"}, ...]``. 각 item 의 `valueRef` 는 EvidencePanel 진입점.
    """
    if not items:
        return None
    # KpiRibbon 은 series 가 카드 단위 — series.data 는 spark 막대.
    series = []
    for it in items:
        spark = list(it.get("sparkValues") or [])
        series.append(
            {
                "name": it.get("label", ""),
                "data": spark,
                "kpi": {
                    "id": it.get("id"),
                    "label": it.get("label"),
                    "value": it.get("value"),
                    "unit": it.get("unit"),
                    "period": it.get("period"),
                    "delta": it.get("delta"),
                    "deltaTone": it.get("deltaTone"),
                    "tone": it.get("tone"),
                    "note": it.get("note"),
                    "valueRef": it.get("valueRef"),
                },
            }
        )
    return {
        "chartType": "kpi-ribbon",
        "title": f"{corpName or stockCode} 핵심 지표",
        "series": series,
        "categories": [it.get("id", str(i)) for i, it in enumerate(items)],
        "options": {"cardCount": len(items)},
        "purpose": "comparison",
        "evidenceIds": ["finance:kpi"],
        "meta": {"source": "review/kpi", "statement": "KPI"},
        "evidenceBinding": chartEvidenceBinding(
            stockCode=stockCode,
            source="review",
            topic="kpi",
            extra={"cardCount": len(items)},
        ),
    }


def specHoverSpark(
    *,
    stockCode: str,
    source: str,
    topic: str,
    account: str,
    accountLabel: str = "",
    periods: list[str],
    values: list[float | None],
    unit: str = "",
    rceptMap: dict[str, str] | None = None,
) -> dict | None:
    """statement table row hover 용 단일 sparkline.

    statement table 의 한 row 위에 마우스를 올렸을 때 우측 popover 에 표시.
    rceptMap 으로 datapoint 별 filing deep-link 이 가능하다.
    """
    if not periods or not values:
        return None
    from dartlab.viz.spec.refs import seriesPointRefs

    return {
        "chartType": "hover-spark",
        "title": accountLabel or account,
        "series": [
            {
                "name": accountLabel or account,
                "data": [_safeVal(v) for v in values],
                "color": COLORS[0],
                "type": "line",
                "pointRefs": seriesPointRefs(
                    stockCode=stockCode,
                    source=source,
                    topic=topic,
                    account=account,
                    periods=periods,
                    rceptMap=rceptMap,
                ),
            }
        ],
        "categories": list(periods),
        "options": {"unit": unit},
        "purpose": "trend",
        "evidenceIds": [f"{source}:{topic}:{account}"],
        "meta": {"source": f"{source}/{topic}", "statement": topic},
        "evidenceBinding": chartEvidenceBinding(
            stockCode=stockCode,
            source=source,
            topic=topic,
            periods=list(periods),
            extra={"account": account},
        ),
    }


def specIncomeTrendMatrix(
    view: dict,
    *,
    stockCode: str,
    corpName: str = "",
) -> dict | None:
    """IncomeConversionView 흡수 — 매출/영업이익/순이익 + 마진 멀티-시리즈.

    view: ``{"periods", "revenue": ChartPointSeries, "op": ..., "net": ...,
             "opMargin": ..., "netMargin": ..., "latestPeriod", "sourceMode",
             "watch", "coverageNotes"}`` (companyDashboardModel.ts 의
    IncomeConversionView 와 동일 형태).
    """
    if not view or not view.get("periods"):
        return None
    periods = list(view["periods"])
    series = []
    for key, label, color, kind in [
        ("revenue", "매출액", COLORS[2], "bar"),
        ("op", "영업이익", COLORS[0], "line"),
        ("net", "당기순이익", COLORS[3], "line"),
        ("opMargin", "영업이익률", COLORS[0], "line"),
        ("netMargin", "순이익률", COLORS[3], "line"),
    ]:
        s = view.get(key) or {}
        vals = list(s.get("values") or [])
        if not vals:
            continue
        series.append(
            {
                "name": label,
                "data": [_safeVal(v) for v in vals],
                "color": color,
                "type": kind,
                "axis": "margin" if key.endswith("Margin") else "amount",
                "unit": s.get("unit", ""),
            }
        )
    if not series:
        return None
    return {
        "chartType": "income-trend-matrix",
        "title": view.get("title") or f"{corpName or stockCode} 손익 전환 매트릭스",
        "series": series,
        "categories": periods,
        "options": {
            "secondaryY": ["영업이익률", "순이익률"],
            "sourceMode": view.get("sourceMode", ""),
            "watch": bool(view.get("watch")),
            "coverageNotes": view.get("coverageNotes", []),
        },
        "purpose": "trend",
        "evidenceIds": ["finance:IS"],
        "meta": {"source": view.get("sourceLabel", "finance/IS"), "statement": "IS"},
        "evidenceBinding": chartEvidenceBinding(
            stockCode=stockCode,
            source="finance",
            topic="IS",
            periodKind="MIXED",
            periods=periods,
            extra={"latestPeriod": view.get("latestPeriod"), "viewId": view.get("id")},
        ),
    }


def specBalanceStructureTrend(
    view: dict,
    *,
    stockCode: str,
    corpName: str = "",
) -> dict | None:
    """BalanceStructureView 흡수 — 자산/부채/자본 구조 + 추세 + 델타.

    view: companyDashboardModel.ts 의 BalanceStructureView 와 동일 형태.
    """
    if not view or not view.get("periods"):
        return None
    periods = list(view["periods"])
    series = []
    for parts_key, group_label in [
        ("assetTrendParts", "자산"),
        ("fundingTrendParts", "조달"),
        ("equityTrendParts", "자본"),
    ]:
        for part in view.get(parts_key) or []:
            series.append(
                {
                    "name": f"{group_label}::{part.get('label', part.get('id', ''))}",
                    "data": [_safeVal(v) for v in (part.get("values") or [])],
                    "shares": [_safeVal(v) for v in (part.get("shares") or [])],
                    "color": part.get("color", COLORS[0]),
                    "type": "bar",
                    "stack": parts_key,
                    "tone": part.get("tone", "neutral"),
                    "unit": part.get("unit", ""),
                    "missing": bool(part.get("missing")),
                }
            )
    if not series:
        return None
    return {
        "chartType": "balance-structure-trend",
        "title": view.get("title") or f"{corpName or stockCode} 자산 구조 추이",
        "series": series,
        "categories": periods,
        "options": {
            "totalAssetsSeries": [_safeVal(v) for v in view.get("totalAssetsSeries") or []],
            "totalFundingSeries": [_safeVal(v) for v in view.get("totalFundingSeries") or []],
            "assetDeltaParts": view.get("assetDeltaParts", []),
            "debtRatio": view.get("debtRatio"),
            "sourceMode": view.get("sourceMode", ""),
            "coverageNotes": view.get("coverageNotes", []),
        },
        "purpose": "composition",
        "evidenceIds": ["finance:BS"],
        "meta": {"source": view.get("sourceLabel", "finance/BS"), "statement": "BS"},
        "evidenceBinding": chartEvidenceBinding(
            stockCode=stockCode,
            source="finance",
            topic="BS",
            periodKind="MIXED",
            periods=periods,
            extra={"latestPeriod": view.get("period"), "viewId": view.get("id")},
        ),
    }


def specCashflowSignedMatrix(
    view: dict,
    *,
    stockCode: str,
    corpName: str = "",
) -> dict | None:
    """CashflowBridgeView 흡수 — 영업/투자/재무 signed bars + 최신 패널.

    view: companyDashboardModel.ts 의 CashflowBridgeView 와 동일 형태.
    """
    if not view or not view.get("periods"):
        return None
    periods = list(view["periods"])
    raw_series = view.get("series") or []
    series = []
    palette = [COLORS[2], COLORS[3], COLORS[0], COLORS[1], COLORS[4]]
    for i, s in enumerate(raw_series):
        vals = list(s.get("values") or [])
        if not vals:
            continue
        series.append(
            {
                "name": s.get("label", s.get("id", f"series_{i}")),
                "data": [_safeVal(v) for v in vals],
                "color": palette[i % len(palette)],
                "type": "bar",
                "signed": True,
                "tone": s.get("tone", "neutral"),
                "unit": s.get("unit", ""),
            }
        )
    if not series:
        return None
    return {
        "chartType": "cashflow-signed-matrix",
        "title": view.get("title") or f"{corpName or stockCode} 현금흐름 signed",
        "series": series,
        "categories": periods,
        "options": {
            "latest": view.get("latest", []),
            "sourceMode": view.get("sourceMode", ""),
            "coverageNotes": view.get("coverageNotes", []),
        },
        "purpose": "bridge",
        "evidenceIds": ["finance:CF"],
        "meta": {"source": view.get("sourceLabel", "finance/CF"), "statement": "CF"},
        "evidenceBinding": chartEvidenceBinding(
            stockCode=stockCode,
            source="finance",
            topic="CF",
            periodKind="MIXED",
            periods=periods,
            extra={"viewId": view.get("id")},
        ),
    }


def specPriceChart(
    rows: Any,
    *,
    stockCode: str,
    corpName: str = "",
    market: str = "KR",
    benchmarkRows: Any | None = None,
    benchmarkName: str = "",
    events: list[dict[str, Any]] | None = None,
    movingAverages: tuple[int, ...] = (20, 60),
) -> dict | None:
    """OHLCV 가격 row 를 ``price-chart`` ChartSpec 으로 변환.

    rows 는 ``g.history(...)`` / ``dartlab.gather("price", ...)`` 결과처럼
    date/open/high/low/close/volume 컬럼을 가진 Polars/Pandas/DataFrame 또는
    list[dict] 를 받는다. KRX index raw 컬럼 (BAS_DD, CLSPRC_IDX 등) 도 흡수한다.
    """
    price_rows = _normalizePriceRows(rows)
    if len(price_rows) < 2:
        return None

    dates = [row["date"] for row in price_rows]
    closes = [row["close"] for row in price_rows]
    series = [
        {
            "name": "종가",
            "data": closes,
            "color": COLORS[2],
            "type": "line",
        }
    ]
    overlays = []
    for i, window in enumerate(movingAverages):
        if window <= 1:
            continue
        ma = _movingAverage(closes, window)
        if any(v is not None for v in ma):
            key = f"ma{window}"
            for row, value in zip(price_rows, ma, strict=False):
                row[key] = value
            overlays.append(key)
            series.append(
                {
                    "name": f"MA{window}",
                    "data": ma,
                    "color": COLORS[(i + 4) % len(COLORS)],
                    "type": "line",
                    "overlay": True,
                }
            )

    benchmark_series: list[dict[str, Any]] = []
    benchmark_rows = _normalizePriceRows(benchmarkRows)
    if benchmark_rows:
        benchmark_by_date = {row["date"]: row["close"] for row in benchmark_rows}
        values = [benchmark_by_date.get(date) for date in dates]
        base = next((v for v in values if v not in (None, 0)), None)
        if base:
            benchmark_series = [
                {"date": date, "value": (value / base * 100) if value else None}
                for date, value in zip(dates, values, strict=False)
            ]

    source = "gather.price"
    return {
        "chartType": "price-chart",
        "title": f"{corpName or stockCode} 주가 · 거래량",
        "data": price_rows,
        "series": series,
        "categories": dates,
        "options": {
            "mode": "candlestick",
            "unit": "원" if market.upper() == "KR" else "USD",
            "volumeUnit": "주",
            "overlays": overlays,
            "benchmarkName": benchmarkName,
            "benchmarkSeries": benchmark_series,
            "events": events or [],
        },
        "purpose": "market_context",
        "evidenceIds": [f"gather:price:{market}:{stockCode}"],
        "meta": {
            "source": source,
            "stockCode": stockCode,
            "corpName": corpName,
            "market": market,
        },
        "evidenceBinding": chartEvidenceBinding(
            stockCode=stockCode,
            source="gather",
            topic="price",
            periodKind="D",
            periods=dates,
            extra={"market": market, "rowCount": len(price_rows)},
        ),
    }


def specEvidenceCoverage(
    items: list[dict],
    *,
    stockCode: str,
    corpName: str = "",
) -> dict | None:
    """근거 소스 커버리지 — EvidenceCoverageView 흡수.

    items: ``[{"label", "status": "ready"|"lazy"|"fallback"|"missing",
               "source", "url"}, ...]``
    """
    if not items:
        return None
    return {
        "chartType": "evidence-coverage",
        "title": f"{corpName or stockCode} 근거 커버리지",
        "series": [
            {
                "name": "coverage",
                "data": [it.get("status") for it in items],
                "items": items,
            }
        ],
        "categories": [it.get("label", "") for it in items],
        "options": {"itemCount": len(items)},
        "purpose": "evidence",
        "evidenceIds": ["coverage:status"],
        "meta": {"source": "review/coverage", "statement": "COVERAGE"},
        "evidenceBinding": chartEvidenceBinding(
            stockCode=stockCode,
            source="review",
            topic="coverage",
            extra={"itemCount": len(items)},
        ),
    }


SPEC_GENERATORS = {
    "revenue_trend": specRevenueTrend,
    "cashflow": specCashflowWaterfall,
    "balance_sheet": specBalanceSheet,
    "profitability": specProfitability,
    "dividend": specDividend,
    "insight_radar": specInsightRadar,
    "ratio_sparklines": specRatioSparklines,
    "diff_heatmap": specDiffHeatmap,
}


def autoChart(company: Any) -> list[dict]:
    """사용 가능한 모든 ChartSpec 리스트를 자동 생성.

    데이터가 없는 차트는 건너뛴다.
    """
    specs = []
    for gen in [
        specRevenueTrend,
        specBalanceSheet,
        specProfitability,
        specCashflowWaterfall,
        specDividend,
        specInsightRadar,
        specRatioSparklines,
        specDiffHeatmap,
    ]:
        try:
            s = gen(company)
            if s is not None:
                specs.append(s)
        except (AttributeError, KeyError, OSError, TypeError, ValueError):
            continue
    return specs
