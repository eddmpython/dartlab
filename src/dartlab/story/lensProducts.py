"""다섯 공개 렌즈의 대표 제품을 Story 소비 계약으로 모은다.

이 모듈은 L3 조립기다. 각 엔진의 공개 대표 축을 호출하고 이미 검증된
``product`` 블록을 수집할 뿐, 점수나 통합 결론을 새로 계산하지 않는다.
원본 결과는 같은 Company 세션에서 재사용할 수 있도록 내부 bundle에만 둔다.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from dartlab.story.lensTensions import classifyLensTensions
from dartlab.synth.lensContract import validatePublicLensBundle

_ENGINE_ORDER = ("analysis", "credit", "industry", "quant", "macro")

_REPORT_ENGINES: dict[str, tuple[str, ...]] = {
    "full": _ENGINE_ORDER,
    "executive": _ENGINE_ORDER,
    "credit": ("analysis", "credit"),
    "valuation": ("analysis", "quant"),
    "growth": ("analysis", "industry", "quant"),
    "crisis": ("analysis", "credit", "macro"),
    "audit": ("analysis",),
    "dividend": ("analysis", "credit"),
    "governance": ("analysis", "industry"),
    "macro": ("analysis", "industry", "macro"),
    "thesis": _ENGINE_ORDER,
    # 스냅샷 계열(요약, snapshot)의 착지점이다. 여기 없으면 fallback 이 렌즈 하나짜리로
    # 조용히 내려앉아서, audit 처럼 일부러 좁힌 것과 등록을 빠뜨린 것이 구분되지 않는다.
    "dashboard": _ENGINE_ORDER,
}


def enginesForReportType(reportType: str | None) -> tuple[str, ...]:
    """보고서 관점에 필요한 렌즈만 안정된 순서로 반환한다."""
    return _REPORT_ENGINES.get(str(reportType or "full"), ("analysis",))


def collectLensProducts(
    company: Any,
    *,
    engines: Iterable[str] | None = None,
    basePeriod: str | None = None,
    refresh: bool = False,
) -> dict[str, Any]:
    """각 공개 대표 축에서 Lens Product를 수집한다.

    반환 bundle의 ``products``는 공개 가능한 공통 계약이고 ``results``는
    Report 같은 같은 세션 소비자가 재계산을 피하기 위한 내부 원본이다.
    엔진 호출 실패나 계약 누락은 가짜 product로 채우지 않고 ``gaps``에 남긴다.
    """
    selected = _normalizeEngines(engines)
    cache = _companyCache(company)
    products: dict[str, dict[str, Any]] = {}
    results: dict[str, dict[str, Any]] = {}
    gaps: list[dict[str, str]] = []

    for engine in selected:
        cacheKey = f"{engine}:{basePeriod or 'latest'}"
        cached = None if refresh else cache.get(cacheKey)
        if isinstance(cached, dict) and "state" in cached:
            record = cached
        else:
            record = _callEngine(company, engine, basePeriod=basePeriod)
            cache[cacheKey] = record

        result = record.get("result")
        product = result.get("product") if isinstance(result, dict) else None
        if isinstance(result, dict):
            results[engine] = result
        if isinstance(product, dict) and product.get("identity", {}).get("engine") == engine:
            products[engine] = product
            continue

        gaps.append(
            {
                "engine": engine,
                "status": str(record.get("state") or "missing"),
                "reason": str(record.get("reason") or "대표 제품 계약이 결과에 없습니다."),
            }
        )

    statusCounts: dict[str, int] = {}
    for product in products.values():
        status = str(product.get("status") or "unknown")
        statusCounts[status] = statusCounts.get(status, 0) + 1

    target = str(getattr(company, "stockCode", "") or getattr(company, "code", "") or "")
    market = str(getattr(company, "market", "") or "").upper()
    tensions = classifyLensTensions(products)
    return {
        "schemaVersion": 1,
        "target": target,
        "market": market,
        "engines": list(selected),
        "products": products,
        "tensions": tensions,
        "results": results,
        "statusCounts": statusCounts,
        "gaps": gaps,
        "noComposite": True,
    }


def publicLensBundle(bundle: dict[str, Any] | None) -> dict[str, Any] | None:
    """내부 원본을 제거하고 제품에서 canonical tension을 다시 만든 공개 bundle을 반환한다."""
    requiredCore = {"schemaVersion", "target", "market", "engines", "products", "statusCounts", "gaps"}
    if not isinstance(bundle, dict) or not requiredCore.issubset(bundle):
        return None
    publicBundle = {
        key: bundle.get(key)
        for key in (
            "schemaVersion",
            "target",
            "market",
            "engines",
            "products",
            "statusCounts",
            "gaps",
            "noComposite",
        )
    }
    products = publicBundle.get("products")
    publicBundle["tensions"] = classifyLensTensions(products) if isinstance(products, dict) else None
    validatePublicLensBundle(publicBundle)
    return publicBundle


def lensSummary(products: dict[str, Any] | None) -> list[dict[str, Any]]:
    """렌더러용으로 각 product의 직접 필드만 투영한다."""
    rows = []
    source = products if isinstance(products, dict) else {}
    for engine in _ENGINE_ORDER:
        product = source.get(engine)
        if not isinstance(product, dict):
            continue
        conclusion = product.get("conclusion") if isinstance(product.get("conclusion"), dict) else {}
        confidence = product.get("confidence") if isinstance(product.get("confidence"), dict) else {}
        time = product.get("time") if isinstance(product.get("time"), dict) else {}
        rows.append(
            {
                "engine": engine,
                "status": product.get("status"),
                "label": conclusion.get("label"),
                "summary": conclusion.get("summary"),
                "confidenceLevel": confidence.get("level"),
                "confidenceScore": confidence.get("score"),
                "asOf": time.get("asOf"),
                "dataAsOf": time.get("dataAsOf"),
                "period": time.get("period"),
            }
        )
    return rows


def _normalizeEngines(engines: Iterable[str] | None) -> tuple[str, ...]:
    requested = set(engines or _ENGINE_ORDER)
    unknown = requested - set(_ENGINE_ORDER)
    if unknown:
        raise ValueError(f"지원하지 않는 lens engine: {sorted(unknown)}")
    return tuple(engine for engine in _ENGINE_ORDER if engine in requested)


def _companyCache(company: Any) -> dict[str, Any]:
    root = getattr(company, "_cache", None)
    if isinstance(root, dict):
        value = root.setdefault("_storyLensProducts", {})
        if isinstance(value, dict):
            return value
    value = getattr(company, "_storyLensProducts", None)
    if isinstance(value, dict):
        return value
    try:
        value = {}
        setattr(company, "_storyLensProducts", value)
        return value
    except (AttributeError, TypeError):
        return {}


def _callEngine(company: Any, engine: str, *, basePeriod: str | None) -> dict[str, Any]:
    try:
        if engine == "analysis":
            result = company.analysis("종합평가", basePeriod=basePeriod)
        elif engine == "credit":
            result = company.credit("등급", detail=True, basePeriod=basePeriod)
        elif engine == "industry":
            industry = getattr(company, "industry", None)
            if callable(industry):
                result = industry()
            else:
                from dartlab.industry.product import blockedIndustryResult

                result = blockedIndustryResult(
                    company,
                    reason="이 시장에는 검증된 산업 가치사슬 taxonomy와 관계 manifest가 아직 없습니다.",
                )
        elif engine == "quant":
            result = company.quant("괴리")
        elif engine == "macro":
            result = company.macro("전파")
        else:
            raise ValueError(f"지원하지 않는 lens engine: {engine}")
    except Exception as exc:  # noqa: BLE001, 한 렌즈 실패가 Story 전체를 막지 않는다.
        return {"state": "blocked", "reason": f"{type(exc).__name__}: {str(exc)[:180]}", "result": None}

    if not isinstance(result, dict):
        return {"state": "missing", "reason": "대표 축 결과가 dict가 아닙니다.", "result": None}
    if not isinstance(result.get("product"), dict):
        return {"state": "missing", "reason": "대표 축 결과에 product 계약이 없습니다.", "result": result}
    return {"state": "ok", "reason": "", "result": result}


__all__ = ["collectLensProducts", "enginesForReportType", "lensSummary", "publicLensBundle"]
