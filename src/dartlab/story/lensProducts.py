"""다섯 공개 렌즈의 대표 제품을 Story 소비 계약으로 모은다.

이 모듈은 L3 조립기다. 각 엔진의 공개 대표 축을 호출하고 이미 검증된
``product`` 블록을 수집할 뿐, 점수나 통합 결론을 새로 계산하지 않는다.
같은 Company 세션에서는 검증된 product와 신용 패널에 필요한 최소 필드만 재사용한다.
엔진의 대형 내부 결과를 Story 생명주기 동안 붙잡아 두지 않는다.
"""

from __future__ import annotations

import re
from calendar import monthrange
from collections.abc import Iterable
from typing import Any

from dartlab.story.lensTensions import classifyLensTensions
from dartlab.synth.lensContract import validateLensProduct, validatePublicLensBundle

_ENGINE_ORDER = ("analysis", "credit", "industry", "quant", "macro")

_CREDIT_RESULT_FIELDS = (
    "grade",
    "gradeRaw",
    "score",
    "healthScore",
    "pdEstimate",
    "outlook",
    "investmentGrade",
    "axes",
)

_REPORT_ENGINES: dict[str, tuple[str, ...]] = {
    # 투자 메모의 9차원에 직접 쓰이는 렌즈만 선계산한다. 신용·퀀트는 질문이
    # 해당 결손을 요구할 때 EngineCall로 보충하고, 첫 브리프의 cold-start에서
    # 전 시장 가격 패널과 신용 모델을 무조건 적재하지 않는다.
    "investment": ("analysis", "industry", "macro"),
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
    같은 세션 소비자가 재계산을 피하기 위한 최소 내부 투영이다.
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
            record = _compactEngineRecord(engine, _callEngine(company, engine, basePeriod=basePeriod))
            cache[cacheKey] = record

        result = record.get("result")
        product = result.get("product") if isinstance(result, dict) else None
        if isinstance(result, dict):
            results[engine] = result
        if isinstance(product, dict) and product.get("identity", {}).get("engine") == engine:
            products[engine] = product
            for productGap in product.get("gaps", []):
                if not isinstance(productGap, dict):
                    continue
                gap = dict(productGap)
                gap["engine"] = engine
                gaps.append(gap)
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

    target = str(getattr(company, "stockCode", "") or "")
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


def isLensProductPromotable(product: Any) -> bool:
    """공개 계약상 usable인 제품만 판단으로 승격할 수 있다."""
    return isinstance(product, dict) and product.get("status") == "usable"


def lensSummary(products: dict[str, Any] | None) -> list[dict[str, Any]]:
    """렌더러용 직접 필드를 투영하되 usable이 아닌 판단은 봉인한다."""
    rows = []
    source = products if isinstance(products, dict) else {}
    for engine in _ENGINE_ORDER:
        product = source.get(engine)
        if not isinstance(product, dict):
            continue
        rawConclusion = product.get("conclusion")
        rawConfidence = product.get("confidence")
        rawTime = product.get("time")
        conclusion = rawConclusion if isinstance(rawConclusion, dict) else {}
        confidence = rawConfidence if isinstance(rawConfidence, dict) else {}
        time = rawTime if isinstance(rawTime, dict) else {}
        usable = isLensProductPromotable(product)
        rows.append(
            {
                "engine": engine,
                "status": product.get("status"),
                "label": conclusion.get("label") if usable else None,
                "summary": conclusion.get("summary") if usable else None,
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
                result = industry(basePeriod=basePeriod) if basePeriod is not None else industry()
            else:
                from dartlab.industry.product import blockedIndustryResult

                result = blockedIndustryResult(
                    company,
                    reason="이 시장에는 검증된 산업 가치사슬 taxonomy와 관계 manifest가 아직 없습니다.",
                )
        elif engine == "quant":
            asOf = _basePeriodAsOf(basePeriod)
            if basePeriod is not None and asOf is None:
                return {
                    "state": "blocked",
                    "reason": f"quant 렌즈가 해석할 수 없는 basePeriod입니다: {basePeriod}",
                    "result": None,
                }
            result = company.quant("괴리", **({"asOf": asOf} if asOf else {}))
        elif engine == "macro":
            asOf = _basePeriodAsOf(basePeriod)
            if basePeriod is not None and asOf is None:
                return {
                    "state": "blocked",
                    "reason": f"macro 렌즈가 해석할 수 없는 basePeriod입니다: {basePeriod}",
                    "result": None,
                }
            result = company.macro("전파", **({"asOf": asOf} if asOf else {}))
        else:
            raise ValueError(f"지원하지 않는 lens engine: {engine}")
    except Exception as exc:  # noqa: BLE001, 한 렌즈 실패가 Story 전체를 막지 않는다.
        return {"state": "blocked", "reason": f"{type(exc).__name__}: {str(exc)[:180]}", "result": None}

    if not isinstance(result, dict):
        return {"state": "missing", "reason": "대표 축 결과가 dict가 아닙니다.", "result": None}
    product = result.get("product")
    if not isinstance(product, dict):
        return {"state": "missing", "reason": "대표 축 결과에 product 계약이 없습니다.", "result": result}
    if product.get("identity", {}).get("engine") != engine:
        return {
            "state": "blocked",
            "reason": f"대표 제품 engine이 호출 축과 다릅니다: {engine}",
            "result": None,
        }
    try:
        validateLensProduct(product, legacy=result)
    except (TypeError, ValueError) as exc:
        return {
            "state": "blocked",
            "reason": f"대표 제품 계약 검증 실패: {str(exc)[:180]}",
            "result": None,
        }
    return {"state": "ok", "reason": "", "result": result}


def _compactEngineRecord(engine: str, record: dict[str, Any]) -> dict[str, Any]:
    """Story에 필요한 필드만 남겨 대형 엔진 결과의 수명을 끊는다."""
    rawResult = record.get("result")
    if not isinstance(rawResult, dict):
        return {
            "state": record.get("state"),
            "reason": record.get("reason"),
            "result": None,
        }

    compactResult: dict[str, Any] = {}
    product = rawResult.get("product")
    if isinstance(product, dict):
        compactResult["product"] = product
    if engine == "credit":
        for field in _CREDIT_RESULT_FIELDS:
            if field in rawResult:
                compactResult[field] = rawResult[field]
    return {
        "state": record.get("state"),
        "reason": record.get("reason"),
        "result": compactResult,
    }


def _basePeriodAsOf(basePeriod: str | None) -> str | None:
    """재무 기간을 시장·거시 엔진이 받는 ISO cutoff로 보수적으로 바꾼다."""
    if basePeriod is None:
        return None
    value = str(basePeriod).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value
    annual = re.fullmatch(r"(\d{4})", value)
    if annual:
        return f"{annual.group(1)}-12-31"
    quarter = re.fullmatch(r"(\d{4})Q([1-4])", value, flags=re.IGNORECASE)
    if quarter:
        year = int(quarter.group(1))
        month = int(quarter.group(2)) * 3
        return f"{year:04d}-{month:02d}-{monthrange(year, month)[1]:02d}"
    monthly = re.fullmatch(r"(\d{4})-(\d{2})", value)
    if monthly:
        year, month = int(monthly.group(1)), int(monthly.group(2))
        if 1 <= month <= 12:
            return f"{year:04d}-{month:02d}-{monthrange(year, month)[1]:02d}"
    return None


__all__ = [
    "collectLensProducts",
    "enginesForReportType",
    "isLensProductPromotable",
    "lensSummary",
    "publicLensBundle",
]
