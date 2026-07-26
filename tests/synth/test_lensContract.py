"""다섯 공개 분석 렌즈의 공통 product 계약 회귀."""

from __future__ import annotations

from copy import deepcopy

import pytest

from dartlab.story.lensProducts import publicLensBundle
from dartlab.story.lensTensions import classifyLensTensions
from dartlab.synth.lensContract import validateLensProduct, validatePublicLensBundle

pytestmark = pytest.mark.unit


def _product(*, status: str = "usable") -> dict:
    gaps = []
    if status != "usable":
        gaps = [{"id": "finance.latest", "status": "missing", "reason": "latest filing unavailable"}]
    return {
        "schemaVersion": 1,
        "identity": {
            "target": "005930",
            "market": "KR",
            "engine": "analysis",
            "axis": "종합평가",
            "version": "1",
        },
        "time": {
            "asOf": "2026-07-18",
            "dataAsOf": {"latestPeriod": "2025Q4", "retrievedAt": "2026-07-18"},
            "period": "2025Q4",
            "knowledgeBoundary": "2026-07-18",
        },
        "status": status,
        "conclusion": {"label": "양호", "summary": "현금창출력과 재무안정성이 유지되고 있습니다."},
        "confidence": {"level": "high", "score": 82.0, "method": "coverageWeighted"},
        "drivers": [{"id": "cash", "label": "영업현금흐름", "direction": "positive"}],
        "evidence": [
            {
                "id": "analysis.scorecard",
                "kind": "executionRef",
                "sourceRef": "dartlab://analysis/005930/scorecard",
                "status": "derived",
            }
        ],
        "assumptions": [],
        "gaps": gaps,
        "scenarios": [],
        "falsifiers": [{"id": "cashBreak", "condition": "영업현금흐름 2개 기간 연속 음수"}],
        "payload": {"blockRefs": ["scorecard"]},
    }


def testValidProductAndLegacyBlockRefs() -> None:
    product = _product()
    validateLensProduct(product, legacy={"stockCode": "005930", "scorecard": {"grade": "A"}})


@pytest.mark.parametrize("status", ["partial", "blocked", "notApplicable"])
def testNonUsableStatusRequiresGap(status: str) -> None:
    product = _product(status=status)
    product["gaps"] = []
    with pytest.raises(ValueError, match="gaps"):
        validateLensProduct(product)


def testUsableRequiresEvidence() -> None:
    product = _product()
    product["evidence"] = []
    with pytest.raises(ValueError, match="evidence"):
        validateLensProduct(product)


def testRejectsUnknownEngineAndStatus() -> None:
    product = _product()
    product["identity"]["engine"] = "story"
    with pytest.raises(ValueError, match="engine"):
        validateLensProduct(product)

    product = _product()
    product["status"] = "ready"
    with pytest.raises(ValueError, match="status"):
        validateLensProduct(product)


def testRejectsConfidenceOutsideRange() -> None:
    product = _product()
    product["confidence"]["score"] = 101
    with pytest.raises(ValueError, match="0 이상 100"):
        validateLensProduct(product)


def testRejectsLookAheadBoundary() -> None:
    product = _product()
    product["time"]["asOf"] = "2026-07-19"
    with pytest.raises(ValueError, match="knowledgeBoundary"):
        validateLensProduct(product)


@pytest.mark.parametrize(
    "data_as_of",
    [
        "2026-07-19",
        "2026Q4",
        {"latestPeriod": "2026Q4", "retrievedAt": "2026-07-18"},
        {"latestPeriod": "2025Q4", "retrievedAt": "2026-07-19"},
    ],
)
def testRejectsDataAsOfAfterKnowledgeBoundary(data_as_of: object) -> None:
    product = _product()
    product["time"]["dataAsOf"] = data_as_of
    with pytest.raises(ValueError, match="dataAsOf"):
        validateLensProduct(product)


def testRejectsLegacyIdentityConflict() -> None:
    product = _product()
    with pytest.raises(ValueError, match="target"):
        validateLensProduct(product, legacy={"stockCode": "000660", "scorecard": {}})


def testRejectsMissingLegacyBlockReference() -> None:
    product = deepcopy(_product())
    product["payload"]["blockRefs"] = ["scorecard", "cashFlow"]
    with pytest.raises(ValueError, match="blockRefs"):
        validateLensProduct(product, legacy={"stockCode": "005930", "scorecard": {}})


def _withClaim() -> dict:
    product = _product()
    product["claims"] = [
        {
            "id": "analysis.cashConversion",
            "label": "현금 전환",
            "comparisonKey": "cashConversion",
            "basis": "companyFundamentals",
            "direction": "supportive",
            "horizon": "latestPeriod",
            "asOf": "2026-07-18",
            "dataAsOf": "2025Q4",
            "period": "2025Q4",
            "status": "derived",
            "sourceRef": "dartlab://analysis/005930/scorecard",
            "evidenceRefs": ["analysis.scorecard"],
            "falsifierRefs": ["cashBreak"],
        }
    ]
    return product


def testTypedClaimResolvesExistingEvidenceAndFalsifier() -> None:
    validateLensProduct(_withClaim())


def testTypedClaimRejectsUnresolvedReferences() -> None:
    product = _withClaim()
    product["claims"][0]["evidenceRefs"] = ["analysis.missing"]
    with pytest.raises(ValueError, match="evidenceRefs"):
        validateLensProduct(product)

    product = _withClaim()
    product["claims"][0]["falsifierRefs"] = ["missingBreak"]
    with pytest.raises(ValueError, match="falsifierRefs"):
        validateLensProduct(product)


def testTypedClaimRejectsInventedSourceAndTime() -> None:
    product = _withClaim()
    product["claims"][0]["sourceRef"] = "dartlab://invented"
    with pytest.raises(ValueError, match="sourceRef"):
        validateLensProduct(product)

    product = _withClaim()
    product["claims"][0]["asOf"] = "2026-07-17"
    with pytest.raises(ValueError, match="asOf"):
        validateLensProduct(product)


def testTypedClaimRejectsLookAheadAndIndirectSource() -> None:
    product = _withClaim()
    product["claims"][0]["dataAsOf"] = "2026-07-19"
    with pytest.raises(ValueError, match="knowledgeBoundary"):
        validateLensProduct(product)

    product = _withClaim()
    product["claims"][0]["dataAsOf"] = "2026Q4"
    with pytest.raises(ValueError, match="knowledgeBoundary"):
        validateLensProduct(product)

    product = _withClaim()
    product["evidence"].append(
        {
            "id": "analysis.other",
            "kind": "executionRef",
            "sourceRef": "dartlab://analysis/005930/other",
            "status": "derived",
        }
    )
    product["claims"][0]["sourceRef"] = "dartlab://analysis/005930/other"
    with pytest.raises(ValueError, match="직접 근거"):
        validateLensProduct(product)


def testTypedClaimRejectsInactiveEvidence() -> None:
    product = _withClaim()
    product["evidence"][0]["status"] = "missing"
    with pytest.raises(ValueError, match="활성 evidence"):
        validateLensProduct(product)


def testRejectsUnparseableDataAsOfInsteadOfSilentlyApproving() -> None:
    for invalid in (
        "sometime-later",
        "2026-07-18T99:99:99Z",
        "2026-07-18T12:30:70+99:99",
    ):
        product = _product()
        product["time"]["dataAsOf"] = invalid
        with pytest.raises(ValueError, match="해석할 수 없습니다"):
            validateLensProduct(product)


def _publicBundleWithActiveTension() -> dict:
    product = _product()
    product["identity"]["engine"] = "quant"
    product["identity"]["axis"] = "괴리"
    product["evidence"] = [
        {
            "id": "quant.fundamental",
            "kind": "disclosureFundamental",
            "sourceRef": "fixture://quant/fundamental",
            "status": "derived",
        },
        {
            "id": "quant.price",
            "kind": "marketReaction",
            "sourceRef": "fixture://quant/price",
            "status": "derived",
        },
    ]
    product["falsifiers"] = [{"id": "classificationBreak", "condition": "다음 관측에서 가격 또는 이익 방향 반전"}]
    product["claims"] = [
        {
            "id": "quant.fundamentalPriceRelation",
            "label": "펀더멘털과 가격 관계",
            "comparisonKey": "fundamentalPriceRelation",
            "basis": "marketBehavior",
            "direction": "unknown",
            "horizon": "latestDecision",
            "asOf": "2026-07-18",
            "dataAsOf": "2026-07-18",
            "period": "2025Q4",
            "status": "derived",
            "sourceRef": "fixture://quant/fundamental",
            "evidenceRefs": ["quant.fundamental", "quant.price"],
            "falsifierRefs": ["classificationBreak"],
            "relation": "underReaction",
        },
        {
            "id": "quant.fundamental",
            "label": "공시 이익 변화",
            "comparisonKey": "fundamentalMomentum",
            "basis": "marketBehavior",
            "direction": "supportive",
            "horizon": "latestPeriod",
            "asOf": "2026-07-18",
            "dataAsOf": "2025Q4",
            "period": "2025Q4",
            "status": "derived",
            "sourceRef": "fixture://quant/fundamental",
            "evidenceRefs": ["quant.fundamental"],
            "falsifierRefs": ["classificationBreak"],
        },
        {
            "id": "quant.priceReaction",
            "label": "가격 반응",
            "comparisonKey": "marketReaction",
            "basis": "marketBehavior",
            "direction": "adverse",
            "horizon": "currentMarket",
            "asOf": "2026-07-18",
            "dataAsOf": "2026-07-18",
            "period": "2025Q4",
            "status": "observed",
            "sourceRef": "fixture://quant/price",
            "evidenceRefs": ["quant.price"],
            "falsifierRefs": ["classificationBreak"],
        },
    ]
    products = {"quant": product}
    return {
        "schemaVersion": 1,
        "target": "005930",
        "market": "KR",
        "engines": ["quant"],
        "products": products,
        "tensions": classifyLensTensions(products),
        "statusCounts": {"usable": 1},
        "gaps": [],
        "noComposite": True,
    }


def testPublicBundleValidatesActiveTensionBackToProducts() -> None:
    bundle = _publicBundleWithActiveTension()

    validatePublicLensBundle(bundle)

    changed = deepcopy(bundle)
    changed["tensions"]["items"][0]["id"] = "invented"
    with pytest.raises(ValueError, match="안정 ID"):
        validatePublicLensBundle(changed)

    changed = deepcopy(bundle)
    changed["tensions"]["items"][0]["falsifiers"][0]["condition"] = "발명된 반증 조건"
    with pytest.raises(ValueError, match="falsifier"):
        validatePublicLensBundle(changed)


def testPublicProjectionRecomputesSemanticTensionAfterProductChange() -> None:
    bundle = _publicBundleWithActiveTension()
    bundle["products"]["quant"]["claims"][0]["relation"] = "aligned"

    public = publicLensBundle(bundle)

    assert public is not None
    assert public["tensions"]["items"] == []
    evaluation = public["tensions"]["evaluations"][0]
    assert evaluation == {
        "patternId": "fundamentalPriceDivergence",
        "status": "clear",
        "reason": "aligned",
    }
