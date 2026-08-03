"""검증된 분석 제품을 투자 의사결정 메모 9차원으로 투영한다.

이 모듈은 새 숫자를 계산하지 않는다. ReportModel이 이미 가진 thesis, 렌즈 제품,
밸류에이션, 시나리오를 의사결정용 상태와 함께 엮고, 없는 정보는 blocked로 남긴다.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

_DIMENSION_ORDER = (
    "thesis",
    "counterThesis",
    "earningsInflection",
    "industryMacroTransmission",
    "valuation",
    "scenarios",
    "catalysts",
    "risks",
    "monitoringTripwires",
)
_HARD_CORE = frozenset({"thesis", "counterThesis", "earningsInflection", "valuation", "risks"})
_ACTIVE_CLAIM_STATUSES = frozenset({"observed", "derived", "estimated"})


@dataclass(frozen=True)
class _InvestmentDecisionInputs:
    """정규화된 투자 메모 입력 묶음."""

    thesis: dict[str, Any]
    products: dict[str, Any]
    tensions: dict[str, Any]
    valuation: dict[str, Any]
    scenarios: dict[str, Any]
    catalystEvents: tuple[dict[str, Any], ...]
    resolvedAsOf: str


@dataclass(frozen=True)
class _InvestmentDecisionDraft:
    """최종 공개 메모 전에 필요한 차원과 요약 필드."""

    dimensions: dict[str, dict[str, Any]]
    central: str
    bearCase: str
    triggers: tuple[str, ...]
    analysis: dict[str, Any]
    catalyst: dict[str, Any]


def _decisionDimensions(inputs: _InvestmentDecisionInputs) -> _InvestmentDecisionDraft:
    """정규화된 엔진 제품을 투자 판단 9차원으로 투영한다."""
    central = _text(inputs.thesis.get("central"))
    bearCase = _text(inputs.thesis.get("bearCase"))
    triggers = tuple(_text(value) for value in inputs.thesis.get("triggers") or [] if _text(value))
    thesisRefs = _refsFromThesis(inputs.thesis)
    analysis = _productDimension(inputs.products.get("analysis"), requireTypedClaim=True)
    transmission = _combinedProductDimension(inputs.products, ("industry", "macro"))
    valuationDimension = _valuationDimension(inputs.valuation, inputs.resolvedAsOf)
    scenarioDimension = _scenarioDimension(inputs.scenarios, inputs.resolvedAsOf)
    catalyst = _catalystDimension(inputs.catalystEvents, inputs.resolvedAsOf)
    tensionClaims = _tensionClaims(inputs.tensions)
    dimensions = {
        "thesis": _dimension(
            "usable" if central else "blocked",
            central,
            inputs.resolvedAsOf,
            thesisRefs,
            [] if central else ["검증 가능한 중심 투자논지가 없습니다."],
        ),
        "counterThesis": _dimension(
            "usable" if bearCase else "blocked",
            bearCase,
            inputs.resolvedAsOf,
            thesisRefs,
            [] if bearCase else ["중심논지와 동등한 무게의 반대논지가 없습니다."],
        ),
        "earningsInflection": analysis,
        "industryMacroTransmission": transmission,
        "valuation": valuationDimension,
        "scenarios": scenarioDimension,
        "catalysts": catalyst,
        "risks": _dimension(
            "usable" if bearCase else "blocked",
            " / ".join([bearCase, *tensionClaims]).strip(" /"),
            inputs.resolvedAsOf,
            thesisRefs + _refsFromTensions(inputs.tensions),
            [] if bearCase else ["논지 훼손 경로가 구조화되지 않았습니다."],
            details={"activeTensions": tensionClaims},
        ),
        "monitoringTripwires": _dimension(
            "usable" if triggers else "blocked",
            triggers[0] if triggers else "",
            inputs.resolvedAsOf,
            thesisRefs,
            [] if triggers else ["논지를 폐기하거나 재검토할 정량·사건 기준이 없습니다."],
            details={"tripwires": list(triggers)},
        ),
    }
    return _InvestmentDecisionDraft(dimensions, central, bearCase, triggers, analysis, catalyst)


def _decisionStatus(dimensions: dict[str, dict[str, Any]], usableCount: int) -> str:
    """핵심 차원 결손과 전체 가용 차원 수로 판단 상태를 정한다."""
    hardCoreBlocked = any(dimensions[key]["status"] in {"blocked", "notObserved"} for key in _HARD_CORE)
    if hardCoreBlocked:
        return "insufficient"
    return "supported" if usableCount >= 7 else "mixed"


def _decisionGaps(
    dimensions: dict[str, dict[str, Any]],
    gaps: Iterable[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """상위 제품 결손과 차원별 결손을 하나의 공개 목록으로 합친다."""
    globalGaps = [dict(row) for row in (gaps or []) if isinstance(row, dict)]
    for key, row in dimensions.items():
        globalGaps.extend(
            {"dimension": key, "status": row["status"], "reason": reason} for reason in row.get("gaps") or []
        )
    return globalGaps


def buildInvestmentDecision(
    *,
    thesis: dict[str, Any] | None,
    lensProducts: dict[str, Any] | None,
    lensTensions: dict[str, Any] | None,
    valuation: dict[str, Any] | None,
    scenarios: dict[str, Any] | None,
    asOf: str | None,
    gaps: Iterable[dict[str, Any]] | None = None,
    catalystEvents: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """기존 엔진 산출물을 9차원 투자 의사결정 계약으로 조립한다."""
    products = lensProducts if isinstance(lensProducts, dict) else {}
    inputs = _InvestmentDecisionInputs(
        thesis=thesis if isinstance(thesis, dict) else {},
        products=products,
        tensions=lensTensions if isinstance(lensTensions, dict) else {},
        valuation=valuation if isinstance(valuation, dict) else {},
        scenarios=scenarios if isinstance(scenarios, dict) else {},
        catalystEvents=tuple(dict(row) for row in (catalystEvents or []) if isinstance(row, dict)),
        resolvedAsOf=str(asOf or _latestLensAsOf(products) or ""),
    )
    draft = _decisionDimensions(inputs)
    dimensions = draft.dimensions
    usableCount = sum(row["status"] == "usable" for row in dimensions.values())
    return {
        "schemaVersion": 1,
        "asOf": inputs.resolvedAsOf,
        "decisionStatus": _decisionStatus(dimensions, usableCount),
        "evidenceStrength": _evidenceStrength(dimensions),
        "usableDimensionCount": usableCount,
        "requiredDimensionCount": len(_DIMENSION_ORDER),
        "dimensions": dimensions,
        "summary": {
            "thesis": draft.central,
            "earningsInflection": draft.analysis.get("claim") or "",
            "scenarioAsymmetry": _scenarioAsymmetry(inputs.scenarios),
            "counterThesis": draft.bearCase,
            "nextCheck": draft.catalyst.get("claim") or (draft.triggers[0] if draft.triggers else ""),
        },
        "gaps": _decisionGaps(dimensions, gaps),
        "policy": {
            "personalizedTradeInstruction": False,
            "scenarioProbabilitiesPublished": False,
            "statusVocabulary": ["usable", "partial", "blocked", "notObserved"],
        },
    }


def _dimension(
    status: str,
    claim: str,
    asOf: str,
    refs: Iterable[str],
    gaps: Iterable[str],
    *,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "asOf": asOf,
        "claim": claim,
        "evidenceRefs": list(dict.fromkeys(ref for ref in refs if ref)),
        "gaps": [gap for gap in gaps if gap],
        "details": details or {},
    }


def _productDimension(product: Any, *, requireTypedClaim: bool) -> dict[str, Any]:
    if not isinstance(product, dict):
        return _dimension("blocked", "", "", [], ["대표 재무 분석 제품이 없습니다."])
    time = product.get("time") if isinstance(product.get("time"), dict) else {}
    conclusion = product.get("conclusion") if isinstance(product.get("conclusion"), dict) else {}
    claims = [
        row
        for row in product.get("claims") or []
        if isinstance(row, dict) and row.get("status") in _ACTIVE_CLAIM_STATUSES
    ]
    earningsClaims = [
        row
        for row in claims
        if any(token in str(row.get("id") or "").casefold() for token in ("revenue", "operating", "margin", "cash"))
    ]
    claim = " / ".join(_claimText(row) for row in earningsClaims[:3] if _claimText(row))
    if not claim:
        claim = _text(conclusion.get("summary"))
    productStatus = str(product.get("status") or "blocked")
    if requireTypedClaim:
        # 상위 제품의 partial 사유가 이익품질 보조 블록처럼 실적 변곡과 무관할 수 있다.
        # 이 차원은 매출·이익·마진·현금의 typed claim 자체가 충분한지로 판정한다.
        status = "usable" if len(earningsClaims) >= 3 else "partial" if earningsClaims else "blocked"
    else:
        status = productStatus
    if status not in {"usable", "partial", "blocked", "notObserved"}:
        status = "partial"
    gaps = [_text(row.get("reason")) for row in product.get("gaps") or [] if isinstance(row, dict)]
    if requireTypedClaim and len(earningsClaims) < 3:
        gaps.append(f"실적 변곡 typed claim이 {len(earningsClaims)}/3개만 관측됐습니다.")
    return _dimension(
        status,
        claim,
        _text(time.get("asOf")),
        _refsFromProduct(product),
        gaps,
        details={"claims": earningsClaims[:5]},
    )


def _combinedProductDimension(products: dict[str, Any], engines: tuple[str, ...]) -> dict[str, Any]:
    rows: list[tuple[str, dict[str, Any]]] = []
    for engine in engines:
        product = products.get(engine)
        if isinstance(product, dict):
            rows.append((engine, product))
    if not rows:
        return _dimension("blocked", "", "", [], ["산업·거시 전파 제품이 없습니다."])
    usable = [(engine, row) for engine, row in rows if row.get("status") == "usable"]
    claims = []
    refs: list[str] = []
    dates: list[str] = []
    gaps: list[str] = []
    for engine, product in rows:
        conclusion = product.get("conclusion") if isinstance(product.get("conclusion"), dict) else {}
        summary = _text(conclusion.get("summary"))
        if summary:
            claims.append(f"{engine}: {summary}")
        refs.extend(_refsFromProduct(product))
        time = product.get("time") if isinstance(product.get("time"), dict) else {}
        if time.get("asOf"):
            dates.append(str(time["asOf"]))
        gaps.extend(_text(gap.get("reason")) for gap in product.get("gaps") or [] if isinstance(gap, dict))
    status = "usable" if len(usable) == len(engines) else "partial" if usable else "blocked"
    if len(rows) < len(engines):
        gaps.append("산업 또는 거시 렌즈 중 하나가 누락됐습니다.")
    return _dimension(status, " / ".join(claims), max(dates, default=""), refs, gaps)


def _valuationDimension(valuation: dict[str, Any], asOf: str) -> dict[str, Any]:
    current = valuation.get("current")
    intrinsic = valuation.get("intrinsic")
    reverse = valuation.get("reverseDcf") if isinstance(valuation.get("reverseDcf"), dict) else {}
    if current is None or intrinsic is None:
        return _dimension(
            "blocked",
            "",
            asOf,
            [],
            ["현재가와 내재가치가 함께 있어야 가격 비대칭을 판단할 수 있습니다."],
            details=valuation,
        )
    upside = round((float(intrinsic) - float(current)) / float(current) * 100, 1) if float(current) else None
    claim = f"내재가치 {intrinsic:,} vs 현재가 {current:,} ({upside:+.1f}%)" if upside is not None else ""
    verdict = _text(reverse.get("verdict"))
    if verdict:
        claim += f" / 시장 내재 기대: {verdict}"
    status = "usable" if verdict else "partial"
    return _dimension(
        status,
        claim,
        asOf,
        [],
        [] if verdict else ["reverse DCF의 시장 내재 기대 판독이 없습니다."],
        details={**valuation, "upside": upside},
    )


def _scenarioDimension(scenarios: dict[str, Any], asOf: str) -> dict[str, Any]:
    legs = [row for row in scenarios.get("legs") or [] if isinstance(row, dict)]
    byKey = {str(row.get("key")): row for row in legs}
    if not {"bear", "base", "bull"}.issubset(byKey):
        return _dimension("blocked", "", asOf, [], ["bear/base/bull 3개 시나리오가 완성되지 않았습니다."])
    hasDrivers = all(any(row.get(key) is not None for key in ("growth", "margin", "wacc")) for row in legs)
    claim = " / ".join(_scenarioLegText(key, byKey[key]) for key in ("bear", "base", "bull"))
    return _dimension(
        "usable" if hasDrivers else "partial",
        claim,
        asOf,
        [],
        [] if hasDrivers else ["시나리오별 성장·마진·WACC 차이가 구조화되지 않았습니다."],
        details=scenarios,
    )


def _catalystDimension(events: Iterable[dict[str, Any]] | None, asOf: str) -> dict[str, Any]:
    rows = [dict(row) for row in (events or []) if isinstance(row, dict)]
    observed = [row for row in rows if row.get("status") in {"watch", "usable", "observed"}]
    if observed:
        first = observed[0]
        claim = _text(first.get("claim") or first.get("title") or first.get("event"))
        return _dimension(
            "usable",
            claim,
            _text(first.get("asOf") or first.get("date") or asOf),
            _refsFromRows(observed),
            [],
            details={"events": observed[:10]},
        )
    coverageComplete = bool(rows) and all(row.get("coverageComplete") is True for row in rows)
    return _dimension(
        "notObserved" if coverageComplete else "blocked",
        "관측된 근접 촉매 없음" if coverageComplete else "",
        asOf,
        _refsFromRows(rows),
        [] if coverageComplete else ["최신 공시·뉴스·일정에서 촉매와 예상 시점을 확인해야 합니다."],
    )


def _scenarioAsymmetry(scenarios: dict[str, Any]) -> dict[str, Any]:
    return {
        str(row.get("key")): {"intrinsic": row.get("intrinsic"), "upside": row.get("upside")}
        for row in scenarios.get("legs") or []
        if isinstance(row, dict) and row.get("key") in {"bear", "base", "bull"}
    }


def _scenarioLegText(key: str, row: dict[str, Any]) -> str:
    intrinsic = row.get("intrinsic")
    intrinsicText = f"{intrinsic:,}" if isinstance(intrinsic, int | float) else "근거 없음"
    upside = row.get("upside")
    upsideText = f" ({upside}%)" if isinstance(upside, int | float) else ""
    return f"{key} {intrinsicText}{upsideText}"


def _evidenceStrength(dimensions: dict[str, dict[str, Any]]) -> str:
    statuses = [row["status"] for row in dimensions.values()]
    if all(status == "usable" for status in statuses):
        return "strong"
    if sum(status == "usable" for status in statuses) >= 5:
        return "moderate"
    return "weak"


def _latestLensAsOf(products: dict[str, Any]) -> str:
    dates = []
    for product in products.values():
        time = product.get("time") if isinstance(product, dict) and isinstance(product.get("time"), dict) else {}
        if time.get("asOf"):
            dates.append(str(time["asOf"]))
    return max(dates, default="")


def _refsFromThesis(thesis: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for pillar in thesis.get("pillars") or []:
        if isinstance(pillar, dict):
            refs.extend(_normalizeRefs(pillar.get("refs")))
    return list(dict.fromkeys(refs))


def _refsFromProduct(product: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for row in product.get("evidence") or []:
        if not isinstance(row, dict):
            continue
        refs.extend(_normalizeRefs(row.get("id")))
        refs.extend(_normalizeRefs(row.get("sourceRef")))
    return list(dict.fromkeys(refs))


def _refsFromTensions(tensions: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for row in tensions.get("items") or []:
        if isinstance(row, dict):
            refs.extend(_normalizeRefs(row.get("evidenceRefs")))
            refs.extend(_normalizeRefs(row.get("sourceRefs")))
    return list(dict.fromkeys(refs))


def _refsFromRows(rows: Iterable[dict[str, Any]]) -> list[str]:
    refs: list[str] = []
    for row in rows:
        refs.extend(_normalizeRefs(row.get("evidenceRefs") or row.get("refs") or row.get("sourceRef")))
    return list(dict.fromkeys(refs))


def _normalizeRefs(value: Any) -> list[str]:
    values = value if isinstance(value, list | tuple) else [value]
    refs = []
    for item in values:
        if isinstance(item, dict) and item.get("id"):
            refs.append(str(item["id"]))
        elif isinstance(item, str) and item:
            refs.append(item)
    return refs


def _claimText(row: dict[str, Any]) -> str:
    label = _text(row.get("label") or row.get("id"))
    value = row.get("value")
    unit = _text(row.get("unit"))
    return f"{label} {value}{unit}".strip() if value is not None else label


def _tensionClaims(tensions: dict[str, Any]) -> list[str]:
    claims = []
    for row in tensions.get("items") or []:
        if isinstance(row, dict):
            value = _text(row.get("headline") or row.get("headlineKr") or row.get("mechanism"))
            if value:
                claims.append(value)
    return claims


def _text(value: Any) -> str:
    return str(value).strip() if value not in (None, "") else ""


__all__ = ["buildInvestmentDecision"]
