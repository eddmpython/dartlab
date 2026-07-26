"""검증된 typed lens claim으로 현재 관점 사이의 틈을 조립한다."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from typing import Any

from dartlab.synth.lensContract import _dataAsOfDates, _isoDate

_PATTERN_ORDER = (
    "fundamentalPriceDivergence",
    "earningsCashDivergence",
    "growthCreditTradeoff",
    "industryExecutionCounterforce",
    "macroCompanyCounterforce",
)
_ACTIVE_CLAIM_STATUSES = frozenset({"observed", "derived"})
_DIRECTIONS = frozenset({"supportive", "neutral", "adverse", "unknown"})
_OPPOSITE = {("supportive", "adverse"), ("adverse", "supportive")}
_STALE_GAP_STATUSES = frozenset({"stale", "blocked", "missing"})
_ACTIVE_EVIDENCE_STATUSES = frozenset({"observed", "derived", "estimated"})

_CLAIM_SPECS = {
    "analysis.operatingIncomeCagr": ("growth", "companyFundamentals", "multiYear"),
    "analysis.revenueCagr": ("growth", "companyFundamentals", "multiYear"),
    "analysis.operatingMargin": ("profitability", "companyFundamentals", "latestPeriod"),
    "analysis.cashConversion": ("cashConversion", "companyFundamentals", "latestPeriod"),
    "credit.debtService": ("debtService", "creditNarrative", "latestPeriod"),
    "credit.cashConversion": ("cashConversion", "creditNarrative", "latestPeriod"),
    "credit.capitalStructure": ("capitalStructure", "creditNarrative", "latestPeriod"),
    "credit.liquidity": ("liquidity", "creditNarrative", "latestPeriod"),
    "industry.cycle": ("industryCycle", "industryCycle", "currentCycle"),
    "quant.fundamentalPriceRelation": ("fundamentalPriceRelation", "marketBehavior", "latestDecision"),
    "quant.fundamental": ("fundamentalMomentum", "marketBehavior", "latestPeriod"),
    "quant.priceReaction": ("marketReaction", "marketBehavior", "currentMarket"),
    "macro.companyTransmission": ("macroTransmission", "macroCompanyEdges", "currentCycle"),
}

_PATTERN_TEXT = {
    "fundamentalPriceDivergence": {
        "kind": "divergence",
        "headlineKr": "펀더멘털과 가격 반응이 갈립니다",
        "headlineEn": "Fundamentals and price reaction diverge",
        "mechanismKr": "공시 기반 변화와 시장 가격이 서로 다른 방향을 가리킵니다.",
        "mechanismEn": "Filing-based change and market price point in opposite directions.",
        "questionKr": "가격이 놓친 변화인지, 숫자가 아직 반영하지 못한 위험인지 확인해야 합니다.",
        "questionEn": "Check whether price missed the change or the filings lag an emerging risk.",
    },
    "earningsCashDivergence": {
        "kind": "divergence",
        "headlineKr": "이익 성장과 현금 전환이 갈립니다",
        "headlineEn": "Earnings growth and cash conversion diverge",
        "mechanismKr": "손익의 성장 방향이 영업현금 전환으로 확인되지 않습니다.",
        "mechanismEn": "The earnings trend is not confirmed by operating cash conversion.",
        "questionKr": "운전자본, 일회성 이익, 매출 인식 중 무엇이 차이를 만드는지 확인해야 합니다.",
        "questionEn": "Check whether working capital, one-offs, or revenue recognition explains the gap.",
    },
    "growthCreditTradeoff": {
        "kind": "tradeoff",
        "headlineKr": "성장은 이어지지만 신용 부담이 맞섭니다",
        "headlineEn": "Growth continues against credit pressure",
        "mechanismKr": "성장 근거와 상환능력 또는 유동성 부담이 동시에 관측됩니다.",
        "mechanismEn": "Growth evidence coexists with pressure on debt service or liquidity.",
        "questionKr": "성장이 차입 부담을 낮출 만큼 현금으로 전환되는지 확인해야 합니다.",
        "questionEn": "Check whether growth converts to enough cash to reduce financing pressure.",
    },
    "industryExecutionCounterforce": {
        "kind": "counterforce",
        "headlineKr": "산업 국면과 회사 실행력이 엇갈립니다",
        "headlineEn": "Industry cycle and company execution diverge",
        "mechanismKr": "산업의 방향과 회사의 성장 또는 수익성 방향이 반대로 움직입니다.",
        "mechanismEn": "The industry cycle and company growth or profitability move in opposite directions.",
        "questionKr": "점유율, 제품 믹스, 원가 구조 중 어느 요인이 산업 효과를 바꾸는지 확인해야 합니다.",
        "questionEn": "Check whether share, product mix, or cost structure offsets the industry cycle.",
    },
    "macroCompanyCounterforce": {
        "kind": "counterforce",
        "headlineKr": "거시 전파와 회사 실적이 엇갈립니다",
        "headlineEn": "Macro transmission and company performance diverge",
        "mechanismKr": "회사에 연결된 거시 경로와 실제 재무 방향이 반대로 관측됩니다.",
        "mechanismEn": "Company-bound macro transmission and observed financial direction oppose each other.",
        "questionKr": "가격 전가력, 헤지, 시차 중 무엇이 거시 충격을 흡수하는지 확인해야 합니다.",
        "questionEn": "Check whether pricing, hedging, or lag structure absorbs the macro shock.",
    },
}


def classifyLensTensions(products: dict[str, Any]) -> dict[str, Any]:
    """검증된 typed claim만 사용해 현재 활성 틈과 판독 범위를 반환한다."""
    if not isinstance(products, dict):
        raise TypeError("lens products 는 dict 여야 합니다.")

    evaluators: dict[str, Callable[[dict[str, Any]], tuple[dict[str, Any] | None, str]]] = {
        "fundamentalPriceDivergence": _fundamentalPrice,
        "earningsCashDivergence": _earningsCash,
        "growthCreditTradeoff": _growthCredit,
        "industryExecutionCounterforce": _industryExecution,
        "macroCompanyCounterforce": _macroCompany,
    }
    items: list[dict[str, Any]] = []
    evaluations: list[dict[str, str]] = []
    for patternId in _PATTERN_ORDER:
        tension, reason = evaluators[patternId](products)
        status = "active" if tension is not None else "clear" if reason == "aligned" else "blocked"
        evaluations.append({"patternId": patternId, "status": status, "reason": reason})
        if tension is not None:
            items.append(tension)
    items.sort(key=lambda row: (_PATTERN_ORDER.index(row["patternId"]), row["id"]))
    return {"schemaVersion": 1, "items": items, "evaluations": evaluations, "noComposite": True}


def _fundamentalPrice(products: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    product, reason = _usableProduct(products, "quant")
    if product is None:
        return None, reason
    relation = _claimById(product, "quant.fundamentalPriceRelation")
    fundamental = _claimById(product, "quant.fundamental")
    price = _claimById(product, "quant.priceReaction")
    if not relation or not fundamental or not price:
        return None, "missingTypedClaim"
    if relation.get("relation") not in {"underReaction", "overOptimism"}:
        return None, "aligned"
    if not _opposite(fundamental, price):
        return None, "claimConflict"
    return _buildTension("fundamentalPriceDivergence", product, fundamental, product, price), "active"


def _earningsCash(products: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    product, reason = _usableProduct(products, "analysis")
    if product is None:
        return None, reason
    growth = _firstClaim(product, ("analysis.operatingIncomeCagr", "analysis.revenueCagr"))
    cash = _claimById(product, "analysis.cashConversion")
    if not growth or not cash:
        return None, "missingTypedClaim"
    if not _opposite(growth, cash):
        return None, "aligned"
    return _buildTension("earningsCashDivergence", product, growth, product, cash), "active"


def _growthCredit(products: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    analysis, reason = _usableProduct(products, "analysis")
    if analysis is None:
        return None, reason
    credit, reason = _usableProduct(products, "credit")
    if credit is None:
        return None, reason
    aligned, reason = _productsAligned(analysis, credit)
    if not aligned:
        return None, reason
    growth = _firstClaim(analysis, ("analysis.operatingIncomeCagr", "analysis.revenueCagr"))
    pressure = _firstClaim(
        credit,
        (
            "credit.debtService",
            "credit.cashConversion",
            "credit.capitalStructure",
            "credit.liquidity",
        ),
        direction="adverse",
    )
    if not growth or not pressure:
        return None, "missingTypedClaim" if not growth else "aligned"
    if growth.get("direction") != "supportive":
        return None, "aligned"
    if not _timeAligned(growth, pressure, requireSamePeriodYear=True):
        return None, "timeMismatch"
    return _buildTension("growthCreditTradeoff", analysis, growth, credit, pressure), "active"


def _industryExecution(products: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    industry, reason = _usableProduct(products, "industry")
    if industry is None:
        return None, reason
    analysis, reason = _usableProduct(products, "analysis")
    if analysis is None:
        return None, reason
    aligned, reason = _productsAligned(industry, analysis)
    if not aligned:
        return None, reason
    cycle = _claimById(industry, "industry.cycle")
    execution = _firstClaim(
        analysis,
        ("analysis.operatingIncomeCagr", "analysis.revenueCagr", "analysis.operatingMargin"),
    )
    if not cycle or not execution:
        return None, "missingTypedClaim"
    if not _opposite(cycle, execution):
        return None, "aligned"
    if not _timeAligned(cycle, execution):
        return None, "timeMismatch"
    return _buildTension("industryExecutionCounterforce", industry, cycle, analysis, execution), "active"


def _macroCompany(products: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    macro, reason = _usableProduct(products, "macro")
    if macro is None:
        return None, reason
    analysis, reason = _usableProduct(products, "analysis")
    if analysis is None:
        return None, reason
    aligned, reason = _productsAligned(macro, analysis)
    if not aligned:
        return None, reason
    transmission = _claimById(macro, "macro.companyTransmission")
    performance = _firstClaim(
        analysis,
        ("analysis.operatingIncomeCagr", "analysis.revenueCagr", "analysis.operatingMargin"),
    )
    if not transmission or not performance:
        return None, "missingTypedClaim"
    if not _opposite(transmission, performance):
        return None, "aligned"
    if not _timeAligned(transmission, performance):
        return None, "timeMismatch"
    return _buildTension("macroCompanyCounterforce", macro, transmission, analysis, performance), "active"


def _usableProduct(products: dict[str, Any], engine: str) -> tuple[dict[str, Any] | None, str]:
    product = products.get(engine)
    if not isinstance(product, dict):
        return None, "missingProduct"
    identity = product.get("identity") if isinstance(product.get("identity"), dict) else {}
    if identity.get("engine") != engine:
        return None, "identityMismatch"
    if product.get("status") != "usable":
        return None, "productNotUsable"
    if not isinstance(product.get("claims"), list):
        return None, "missingTypedClaims"
    return product, "ready"


def _claimById(product: dict[str, Any], claimId: str) -> dict[str, Any] | None:
    spec = _CLAIM_SPECS.get(claimId)
    if spec is None:
        return None
    for claim in product.get("claims", []):
        if not isinstance(claim, dict) or claim.get("id") != claimId:
            continue
        if claim.get("status") not in _ACTIVE_CLAIM_STATUSES:
            return None
        if claim.get("direction") not in _DIRECTIONS:
            return None
        evidenceRefs = claim.get("evidenceRefs")
        if not isinstance(evidenceRefs, list) or not evidenceRefs:
            return None
        falsifierRefs = claim.get("falsifierRefs")
        if not isinstance(falsifierRefs, list) or not falsifierRefs:
            return None
        if (claim.get("comparisonKey"), claim.get("basis"), claim.get("horizon")) != spec:
            return None
        evidenceById = {
            str(row.get("id")): row for row in product.get("evidence", []) if isinstance(row, dict) and row.get("id")
        }
        falsifierIds = {
            str(row.get("id")) for row in product.get("falsifiers", []) if isinstance(row, dict) and row.get("id")
        }
        if set(evidenceRefs) - set(evidenceById) or set(falsifierRefs) - falsifierIds:
            return None
        referencedEvidence = [evidenceById[ref] for ref in evidenceRefs]
        if any(row.get("status") not in _ACTIVE_EVIDENCE_STATUSES for row in referencedEvidence):
            return None
        referencedSources = {str(row.get("sourceRef")) for row in referencedEvidence if row.get("sourceRef")}
        if claim.get("sourceRef") not in referencedSources:
            return None
        productTime = product.get("time") if isinstance(product.get("time"), dict) else {}
        if not claim.get("asOf") or claim.get("asOf") != productTime.get("asOf"):
            return None
        try:
            knowledgeBoundary = _isoDate(
                productTime.get("knowledgeBoundary"),
                path="time.knowledgeBoundary",
            )
            claimDataDates = _dataAsOfDates(claim.get("dataAsOf"))
        except (TypeError, ValueError):
            return None
        if knowledgeBoundary is not None and any(value > knowledgeBoundary for value in claimDataDates):
            return None
        return claim
    return None


def _firstClaim(
    product: dict[str, Any],
    claimIds: tuple[str, ...],
    *,
    direction: str | None = None,
) -> dict[str, Any] | None:
    for claimId in claimIds:
        claim = _claimById(product, claimId)
        if claim is not None and (direction is None or claim.get("direction") == direction):
            return claim
    return None


def _opposite(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (str(left.get("direction")), str(right.get("direction"))) in _OPPOSITE


def _timeAligned(left: dict[str, Any], right: dict[str, Any], *, requireSamePeriodYear: bool = False) -> bool:
    if not left.get("asOf") or left.get("asOf") != right.get("asOf"):
        return False
    if requireSamePeriodYear:
        leftYear = _periodYear(left.get("period"))
        rightYear = _periodYear(right.get("period"))
        if leftYear is None or rightYear is None or leftYear != rightYear:
            return False
    return True


def _periodYear(value: Any) -> str | None:
    matches = re.findall(r"(?:19|20)\d{2}", str(value or ""))
    return matches[-1] if matches else None


def _productsAligned(left: dict[str, Any], right: dict[str, Any]) -> tuple[bool, str]:
    leftIdentity = left.get("identity") if isinstance(left.get("identity"), dict) else {}
    rightIdentity = right.get("identity") if isinstance(right.get("identity"), dict) else {}
    if not leftIdentity.get("target") or leftIdentity.get("target") != rightIdentity.get("target"):
        return False, "identityMismatch"
    if not leftIdentity.get("market") or leftIdentity.get("market") != rightIdentity.get("market"):
        return False, "identityMismatch"
    leftTime = left.get("time") if isinstance(left.get("time"), dict) else {}
    rightTime = right.get("time") if isinstance(right.get("time"), dict) else {}
    if not leftTime.get("knowledgeBoundary") or leftTime.get("knowledgeBoundary") != rightTime.get("knowledgeBoundary"):
        return False, "timeMismatch"
    return True, "aligned"


def _buildTension(
    patternId: str,
    leftProduct: dict[str, Any],
    leftClaim: dict[str, Any],
    rightProduct: dict[str, Any],
    rightClaim: dict[str, Any],
) -> dict[str, Any]:
    if not _timeAligned(leftClaim, rightClaim):
        raise ValueError("tension 양쪽 claim의 asOf가 일치해야 합니다.")
    target = str(leftProduct.get("identity", {}).get("target") or "")
    rightTarget = str(rightProduct.get("identity", {}).get("target") or "")
    if not target or target != rightTarget:
        raise ValueError("tension 양쪽 product의 target이 일치해야 합니다.")
    aligned, reason = _productsAligned(leftProduct, rightProduct)
    if not aligned:
        raise ValueError(f"tension 양쪽 product가 정렬되지 않았습니다: {reason}")
    pattern = _PATTERN_TEXT[patternId]
    sides = [
        _side(leftProduct, leftClaim),
        _side(rightProduct, rightClaim),
    ]
    claimKeys = sorted(f"{side['engine']}:{side['claimId']}" for side in sides)
    identity = "|".join([target, patternId, *claimKeys])
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]
    products = [leftProduct] if leftProduct is rightProduct else [leftProduct, rightProduct]
    falsifiers = _falsifiers(products, [leftClaim, rightClaim])
    if not falsifiers:
        raise ValueError("active tension은 상위 렌즈의 falsifier를 1개 이상 가져야 합니다.")
    return {
        "schemaVersion": 1,
        "id": f"{patternId}:{digest}",
        "target": target,
        "patternId": patternId,
        "kind": pattern["kind"],
        "status": "active",
        "asOf": leftClaim["asOf"],
        "headline": {"kr": pattern["headlineKr"], "en": pattern["headlineEn"]},
        "mechanism": {"kr": pattern["mechanismKr"], "en": pattern["mechanismEn"]},
        "question": {"kr": pattern["questionKr"], "en": pattern["questionEn"]},
        "sides": sides,
        "falsifiers": falsifiers,
        "gaps": _limitations(products),
        "algorithmVersion": "1",
        "noComposite": True,
    }


def _side(product: dict[str, Any], claim: dict[str, Any]) -> dict[str, Any]:
    return {
        "engine": product["identity"]["engine"],
        "claimId": claim["id"],
        "label": claim["label"],
        "comparisonKey": claim["comparisonKey"],
        "basis": claim["basis"],
        "direction": claim["direction"],
        "horizon": claim["horizon"],
        "asOf": claim["asOf"],
        "dataAsOf": claim["dataAsOf"],
        "period": claim["period"],
        "status": claim["status"],
        "sourceRef": claim["sourceRef"],
        "evidenceRefs": sorted(set(claim["evidenceRefs"])),
        **({"value": claim["value"]} if "value" in claim else {}),
        **({"unit": claim["unit"]} if claim.get("unit") else {}),
    }


def _falsifiers(products: list[dict[str, Any]], claims: list[dict[str, Any]]) -> list[dict[str, str]]:
    refs = {str(ref) for claim in claims for ref in claim.get("falsifierRefs", []) if ref}
    rows: dict[str, dict[str, str]] = {}
    for product in products:
        engine = str(product.get("identity", {}).get("engine") or "unknown")
        for row in product.get("falsifiers", []):
            if not isinstance(row, dict) or row.get("id") not in refs or not row.get("condition"):
                continue
            key = f"{engine}.{row['id']}"
            item = {
                "id": key,
                "condition": str(row["condition"]),
            }
            if row.get("sourceRef"):
                item["sourceRef"] = str(row["sourceRef"])
            if row.get("driverRef"):
                item["driverRef"] = str(row["driverRef"])
            rows[key] = item
    return [rows[key] for key in sorted(rows)][:6]


def _limitations(products: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for product in products:
        engine = str(product.get("identity", {}).get("engine") or "unknown")
        for row in product.get("gaps", []):
            if not isinstance(row, dict) or row.get("status") in _STALE_GAP_STATUSES:
                continue
            key = f"{engine}.{row.get('id') or 'gap'}"
            rows[key] = {
                "id": key,
                "status": str(row.get("status") or "partial"),
                "reason": str(row.get("reason") or "제한 사항이 있습니다."),
                **({"sourceRef": str(row["sourceRef"])} if row.get("sourceRef") else {}),
            }
    return [rows[key] for key in sorted(rows)][:6]


def canonicalTensionJson(value: dict[str, Any]) -> str:
    """결정론 검증을 위한 정렬 JSON을 반환한다."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = ["canonicalTensionJson", "classifyLensTensions"]
