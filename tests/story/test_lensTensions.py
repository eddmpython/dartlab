"""Story의 렌즈 틈 조합 계약 회귀."""

from __future__ import annotations

from copy import deepcopy

import pytest

from dartlab.story.lensTensions import canonicalTensionJson, classifyLensTensions

pytestmark = pytest.mark.unit


def _claim(
    claimId: str,
    direction: str,
    *,
    comparisonKey: str,
    basis: str,
    horizon: str,
    period: str = "2025Q4",
    relation: str | None = None,
) -> dict:
    row = {
        "id": claimId,
        "label": f"label:{claimId}",
        "comparisonKey": comparisonKey,
        "basis": basis,
        "direction": direction,
        "horizon": horizon,
        "asOf": "2026-07-22",
        "dataAsOf": period,
        "period": period,
        "status": "derived",
        "sourceRef": f"fixture://{claimId}",
        "evidenceRefs": [f"evidence.{claimId}"],
        "falsifierRefs": ["reversal"],
    }
    if relation is not None:
        row["relation"] = relation
    return row


def _product(engine: str, claims: list[dict], *, status: str = "usable") -> dict:
    return {
        "identity": {"target": "005930", "market": "KR", "engine": engine},
        "time": {"asOf": "2026-07-22", "knowledgeBoundary": "2026-07-22"},
        "status": status,
        "conclusion": {"label": f"{engine} 원문", "summary": "판정 입력이 아닌 문구"},
        "confidence": {"score": 99.0},
        "drivers": [],
        "claims": claims,
        "evidence": [
            {
                "id": f"evidence.{claim['id']}",
                "sourceRef": claim["sourceRef"],
                "status": "derived",
            }
            for claim in claims
        ],
        "gaps": [],
        "falsifiers": [
            {"id": "reversal", "condition": "다음 관측에서 방향 반전", "sourceRef": f"fixture://{engine}/break"}
        ],
    }


def _products() -> dict:
    return {
        "analysis": _product(
            "analysis",
            [
                _claim(
                    "analysis.operatingIncomeCagr",
                    "supportive",
                    comparisonKey="growth",
                    basis="companyFundamentals",
                    horizon="multiYear",
                ),
                _claim(
                    "analysis.revenueCagr",
                    "supportive",
                    comparisonKey="growth",
                    basis="companyFundamentals",
                    horizon="multiYear",
                ),
                _claim(
                    "analysis.operatingMargin",
                    "supportive",
                    comparisonKey="profitability",
                    basis="companyFundamentals",
                    horizon="latestPeriod",
                ),
                _claim(
                    "analysis.cashConversion",
                    "adverse",
                    comparisonKey="cashConversion",
                    basis="companyFundamentals",
                    horizon="latestPeriod",
                ),
            ],
        ),
        "credit": _product(
            "credit",
            [
                _claim(
                    "credit.debtService",
                    "adverse",
                    comparisonKey="debtService",
                    basis="creditNarrative",
                    horizon="latestPeriod",
                )
            ],
        ),
        "industry": _product(
            "industry",
            [
                _claim(
                    "industry.cycle",
                    "adverse",
                    comparisonKey="industryCycle",
                    basis="industryCycle",
                    horizon="currentCycle",
                )
            ],
        ),
        "quant": _product(
            "quant",
            [
                _claim(
                    "quant.fundamentalPriceRelation",
                    "unknown",
                    comparisonKey="fundamentalPriceRelation",
                    basis="marketBehavior",
                    horizon="latestDecision",
                    relation="underReaction",
                ),
                _claim(
                    "quant.fundamental",
                    "supportive",
                    comparisonKey="fundamentalMomentum",
                    basis="marketBehavior",
                    horizon="latestPeriod",
                ),
                _claim(
                    "quant.priceReaction",
                    "adverse",
                    comparisonKey="marketReaction",
                    basis="marketBehavior",
                    horizon="currentMarket",
                ),
            ],
        ),
        "macro": _product(
            "macro",
            [
                _claim(
                    "macro.companyTransmission",
                    "adverse",
                    comparisonKey="macroTransmission",
                    basis="macroCompanyEdges",
                    horizon="currentCycle",
                )
            ],
        ),
    }


def testFiveCatalogPatternsAreDeterministicAndHaveNoCompositeVerdict() -> None:
    result = classifyLensTensions(_products())

    assert [row["patternId"] for row in result["items"]] == [
        "fundamentalPriceDivergence",
        "earningsCashDivergence",
        "growthCreditTradeoff",
        "industryExecutionCounterforce",
        "macroCompanyCounterforce",
    ]
    assert result["noComposite"] is True
    assert {row["status"] for row in result["items"]} == {"active"}
    serialized = canonicalTensionJson(result)
    assert all(key not in serialized for key in ('"score"', '"recommendation"', '"verdict"', '"conclusion"'))


def testTextConfidenceAndInputOrderDoNotChangeClassification() -> None:
    products = _products()
    expected = canonicalTensionJson(classifyLensTensions(products))
    changed = {key: deepcopy(value) for key, value in reversed(list(products.items()))}
    for product in changed.values():
        product["conclusion"] = {"label": "완전히 다른 문구", "summary": "무시되어야 함"}
        product["confidence"]["score"] = 1.0
        product["claims"].reverse()

    assert canonicalTensionJson(classifyLensTensions(changed)) == expected


def testPartialProductMissingEvidenceAndTimeMismatchFailClosed() -> None:
    products = _products()
    products["credit"]["status"] = "partial"
    result = classifyLensTensions(products)
    evaluation = next(row for row in result["evaluations"] if row["patternId"] == "growthCreditTradeoff")
    assert evaluation == {"patternId": "growthCreditTradeoff", "status": "blocked", "reason": "productNotUsable"}

    products = _products()
    products["credit"]["claims"][0]["evidenceRefs"] = []
    result = classifyLensTensions(products)
    assert "growthCreditTradeoff" not in {row["patternId"] for row in result["items"]}

    products = _products()
    products["credit"]["claims"][0]["period"] = "2024Q4"
    result = classifyLensTensions(products)
    evaluation = next(row for row in result["evaluations"] if row["patternId"] == "growthCreditTradeoff")
    assert evaluation["reason"] == "timeMismatch"

    products = _products()
    products["industry"]["time"]["knowledgeBoundary"] = "2026-07-21"
    result = classifyLensTensions(products)
    evaluation = next(row for row in result["evaluations"] if row["patternId"] == "industryExecutionCounterforce")
    assert evaluation["reason"] == "timeMismatch"


def testCatalogRejectsSemanticHorizonDrift() -> None:
    products = _products()
    for claim in products["analysis"]["claims"]:
        if claim["id"] in {"analysis.operatingIncomeCagr", "analysis.revenueCagr"}:
            claim["horizon"] = "latestPeriod"

    result = classifyLensTensions(products)
    assert "growthCreditTradeoff" not in {row["patternId"] for row in result["items"]}
    assert "earningsCashDivergence" not in {row["patternId"] for row in result["items"]}


def testUnrelatedProductGapDoesNotBlockGroundedClaim() -> None:
    products = _products()
    products["credit"]["gaps"] = [
        {
            "id": "credit.axis.disclosureRisk",
            "status": "missing",
            "reason": "이 claim과 무관한 축 결손",
            "sourceRef": "axes.disclosureRisk",
        }
    ]

    result = classifyLensTensions(products)

    assert "growthCreditTradeoff" in {row["patternId"] for row in result["items"]}


def testClaimSpecificEvidenceAndTimeBoundaryFailClosed() -> None:
    products = _products()
    creditEvidence = products["credit"]["evidence"][0]
    creditEvidence["status"] = "missing"
    result = classifyLensTensions(products)
    assert "growthCreditTradeoff" not in {row["patternId"] for row in result["items"]}

    products = _products()
    products["credit"]["claims"][0]["dataAsOf"] = "2026-07-23"
    result = classifyLensTensions(products)
    assert "growthCreditTradeoff" not in {row["patternId"] for row in result["items"]}

    products = _products()
    products["credit"]["claims"][0]["dataAsOf"] = "2026Q4"
    result = classifyLensTensions(products)
    assert "growthCreditTradeoff" not in {row["patternId"] for row in result["items"]}

    products = _products()
    products["credit"]["evidence"].append({"id": "evidence.other", "sourceRef": "fixture://other", "status": "derived"})
    products["credit"]["claims"][0]["sourceRef"] = "fixture://other"
    result = classifyLensTensions(products)
    assert "growthCreditTradeoff" not in {row["patternId"] for row in result["items"]}


def testStableIdDoesNotDependOnPolarityAndProvenanceComesFromProducts() -> None:
    products = _products()
    first = classifyLensTensions(products)
    firstItem = next(row for row in first["items"] if row["patternId"] == "earningsCashDivergence")

    changed = deepcopy(products)
    for claim in changed["analysis"]["claims"]:
        if claim["id"] in {"analysis.operatingIncomeCagr", "analysis.revenueCagr"}:
            claim["direction"] = "adverse"
        if claim["id"] == "analysis.cashConversion":
            claim["direction"] = "supportive"
    second = classifyLensTensions(changed)
    secondItem = next(row for row in second["items"] if row["patternId"] == "earningsCashDivergence")
    assert secondItem["id"] == firstItem["id"]

    sourceRefs = {
        row["sourceRef"]
        for product in products.values()
        for key in ("drivers", "evidence", "falsifiers")
        for row in product[key]
        if row.get("sourceRef")
    }
    for item in first["items"]:
        assert all(side["sourceRef"] in sourceRefs for side in item["sides"])
        assert all(row.get("sourceRef") in sourceRefs for row in item["falsifiers"] if row.get("sourceRef"))
