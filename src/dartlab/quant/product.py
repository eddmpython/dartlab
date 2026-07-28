"""Quant 대표 제품인 펀더멘털과 가격 반응 괴리 조립기.

기존 ``괴리`` 축의 공개 키는 유지한다. 이 모듈은 Quant 내부의 공시 이익,
횡단면 기대 프록시, 가격 반응을 비교하고 공통 Lens Product 블록을 만든다.
실제 애널리스트 컨센서스가 없는 경우 이를 기대치로 가장하지 않는다.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from dartlab.synth.rowAccess import strictFloat as _number


def buildDivergenceResult(
    stockCode: str,
    market: str,
    *,
    technical: dict[str, Any] | None,
    earnings: dict[str, Any] | None,
    expectation: dict[str, Any] | None,
    priceAsOf: str | None,
    asOf: str | None = None,
) -> dict[str, Any]:
    """공시 펀더멘털, 기대 프록시, 가격 반응의 일치와 괴리를 판정한다."""
    decisionDate = asOf or date.today().isoformat()
    fundamental = _fundamentalBlock(earnings)
    expectationBlock = _expectationBlock(expectation)
    price = _priceBlock(technical)
    classification = _classify(fundamental.get("score"), expectationBlock.get("score"), price.get("score"))
    label, diagnosis, legacyLabel = _classificationText(classification)

    result: dict[str, Any] = {
        "target": stockCode,
        "stockCode": stockCode,
        "market": market,
        "asOf": decisionDate,
        "financialGrade": None,
        "technicalVerdict": price.get("verdict"),
        "technicalScore": technical.get("score", 0) if isinstance(technical, dict) else 0,
        "divergence": legacyLabel,
        "diagnosis": diagnosis,
        "matrix": f"{fundamental.get('direction', 'unknown')}_{price.get('direction', 'unknown')}",
        "classification": classification,
        "fundamental": fundamental,
        "expectation": expectationBlock,
        "price": price,
    }
    result["product"] = _buildProduct(
        result,
        label=label,
        diagnosis=diagnosis,
        priceAsOf=priceAsOf,
        decisionDate=decisionDate,
    )
    return result


def _fundamentalBlock(value: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("error"):
        return {"status": "missing", "score": None, "direction": "unknown", "source": value}
    sue = _number(value.get("sue"))
    trend = value.get("earningsTrend")
    trendScore = {
        "consistent_growth": 1.0,
        "mostly_growing": 0.5,
        "mixed": 0.0,
        "mostly_declining": -0.7,
    }.get(trend)
    parts = []
    if sue is not None:
        parts.append(_clamp(sue / 2.0))
    if trendScore is not None:
        parts.append(trendScore)
    score = round(sum(parts) / len(parts), 3) if parts else None
    return {
        "status": "observed" if score is not None else "missing",
        "score": score,
        "direction": _direction(score),
        "sue": sue,
        "earningsTrend": trend,
        "peadSignal": value.get("peadSignal"),
        "period": _latestPeriod(value),
        "source": value,
    }


def _expectationBlock(value: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("error"):
        return {
            "status": "missing",
            "score": None,
            "direction": "unknown",
            "method": "crossSectionalEarningsSurpriseProxy",
            "source": value,
        }
    scoreValue = _number(value.get("score"))
    score = round(_clamp(scoreValue / 2.0), 3) if scoreValue is not None else None
    return {
        "status": "estimated" if score is not None else "missing",
        "score": score,
        "direction": _direction(score),
        "method": "crossSectionalEarningsSurpriseProxy",
        "zScore": scoreValue,
        "category": value.get("category"),
        "period": value.get("year"),
        "universe": value.get("universe"),
        "source": value,
    }


def _priceBlock(value: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("error"):
        return {"status": "missing", "score": None, "direction": "unknown", "source": value}
    rawScore = _number(value.get("score"))
    score = round(_clamp(rawScore / 4.0), 3) if rawScore is not None else None
    return {
        "status": "observed" if score is not None else "missing",
        "score": score,
        "direction": _direction(score),
        "verdict": value.get("verdict"),
        "rsi": value.get("rsi"),
        "adx": value.get("adx"),
        "benchmarkUsed": value.get("benchmarkUsed"),
        "source": value,
    }


def _classify(fundamental: Any, expectation: Any, price: Any) -> str:
    f = _number(fundamental)
    e = _number(expectation)
    p = _number(price)
    if f is None or p is None:
        return "inconclusive"
    combinedFundamental = f if e is None else 0.65 * f + 0.35 * e
    if combinedFundamental >= 0.25 and p <= -0.25:
        return "underReaction"
    if combinedFundamental <= -0.25 and p >= 0.25:
        return "overOptimism"
    if combinedFundamental >= 0.2 and p >= 0.2:
        return "confirmation"
    if combinedFundamental <= -0.2 and p <= -0.2:
        return "deteriorationPriced"
    return "inconclusive"


def _classificationText(classification: str) -> tuple[str, str, str]:
    rows = {
        "underReaction": (
            "펀더멘털 개선 미반영",
            "공시 이익 변화는 개선 방향이지만 가격 반응은 약합니다. 미반영 기회와 시장의 선행 위험 판단을 함께 확인해야 합니다.",
            "괴리",
        ),
        "confirmation": (
            "펀더멘털과 가격 확인",
            "공시 이익 변화와 가격 반응이 같은 개선 방향을 가리킵니다. 이후 실적에서 개선 지속 여부가 핵심입니다.",
            "순풍",
        ),
        "overOptimism": (
            "가격 기대 과열 가능성",
            "공시 이익 변화는 약한데 가격 반응은 강합니다. 기대의 근거와 다음 실적 확인이 필요합니다.",
            "위험",
        ),
        "deteriorationPriced": (
            "실적 악화 가격 반영",
            "공시 이익 변화와 가격 반응이 함께 약합니다. 악화가 멈추는 반증 신호 전까지 보수적으로 해석합니다.",
            "경고",
        ),
        "inconclusive": (
            "괴리 판단 보류",
            "펀더멘털, 기대 프록시, 가격 반응의 방향이 뚜렷하게 갈리지 않거나 필요한 근거가 부족합니다.",
            "미정",
        ),
    }
    return rows[classification]


def _buildProduct(
    legacy: dict[str, Any],
    *,
    label: str,
    diagnosis: str,
    priceAsOf: str | None,
    decisionDate: str,
) -> dict[str, Any]:
    from dartlab.synth.lensContract import validateLensProduct

    blocks = [legacy["fundamental"], legacy["expectation"], legacy["price"]]
    available = sum(block.get("status") in {"observed", "estimated"} for block in blocks)
    gaps: list[dict[str, Any]] = []
    if legacy["fundamental"].get("status") != "observed":
        gaps.append(
            {
                "id": "quant.fundamental",
                "status": "missing",
                "reason": "비교 가능한 공시 이익 시계열이 없습니다.",
                "sourceRef": "dartlab://quant/earnings",
            }
        )
    if legacy["expectation"].get("status") != "estimated":
        gaps.append(
            {
                "id": "quant.expectationProxy",
                "status": "missing",
                "reason": "시장 횡단면 이익 서프라이즈 프록시를 계산하지 못했습니다.",
                "sourceRef": "dartlab://quant/surprise",
            }
        )
    gaps.append(
        {
            "id": "quant.analystConsensus",
            "status": "unsupported",
            "reason": "현재 결과는 실제 애널리스트 컨센서스가 아니라 횡단면 이익 서프라이즈를 기대 프록시로 사용합니다.",
            "sourceRef": "dartlab://gather/revenueConsensus",
        }
    )
    if legacy["price"].get("status") != "observed":
        gaps.append(
            {
                "id": "quant.priceReaction",
                "status": "missing",
                "reason": "가격 반응을 계산할 충분한 시계열이 없습니다.",
                "sourceRef": "dartlab://quant/verdict",
            }
        )

    status = "blocked" if available == 0 else "partial" if available < 3 else "usable"
    if status == "usable":
        gaps = [gap for gap in gaps if gap["id"] == "quant.analystConsensus"]
    clarity = 1.0 if legacy["classification"] != "inconclusive" else 0.4
    score = round((available / 3 * 80) + (clarity * 20), 1)
    if legacy["classification"] == "inconclusive":
        score = min(score, 65.0)
    level = "blocked" if status == "blocked" else "high" if score >= 80 else "medium" if score >= 50 else "low"

    evidence = []
    for key, kind, sourceRef in (
        ("fundamental", "disclosureFundamental", "dartlab://quant/earnings"),
        ("expectation", "expectationProxy", "dartlab://quant/surprise"),
        ("price", "marketReaction", "dartlab://quant/verdict"),
    ):
        block = legacy[key]
        if block.get("status") in {"observed", "estimated"}:
            evidence.append(
                {
                    "id": f"quant.{key}",
                    "kind": kind,
                    "sourceRef": sourceRef,
                    "status": "estimated" if block.get("status") == "estimated" else "derived",
                    "observedAt": priceAsOf if key == "price" else None,
                    "detail": f"괴리 판정의 {key} 입력",
                }
            )

    drivers = [
        {
            "id": key,
            "label": labelText,
            "score": legacy[key].get("score"),
            "direction": legacy[key].get("direction"),
            "sourceRef": f"{key}.score",
        }
        for key, labelText in (
            ("fundamental", "공시 이익 변화"),
            ("expectation", "시장 기대 프록시"),
            ("price", "가격 반응"),
        )
        if legacy[key].get("score") is not None
    ]
    period = legacy["fundamental"].get("period") or legacy["expectation"].get("period")
    falsifiers = _falsifiers(legacy["classification"])
    claims = _quantClaims(
        legacy,
        evidence,
        falsifiers,
        asOf=decisionDate,
        priceAsOf=priceAsOf,
        period=str(period) if period is not None else None,
    )
    product = {
        "schemaVersion": 1,
        "identity": {
            "target": legacy["stockCode"],
            "market": legacy["market"],
            "engine": "quant",
            "axis": "괴리",
            "version": "1",
        },
        "time": {
            "asOf": decisionDate,
            "dataAsOf": priceAsOf,
            "period": str(period) if period is not None else None,
            "knowledgeBoundary": decisionDate,
        },
        "status": status,
        "conclusion": {"label": label, "summary": diagnosis},
        "confidence": {"level": level, "score": score, "method": "threeBlockCoverageAndSignalClarity"},
        "drivers": drivers,
        "claims": claims,
        "evidence": evidence,
        "assumptions": [
            {
                "id": "expectationMethod",
                "value": "crossSectionalEarningsSurpriseProxy",
                "reason": "실제 컨센서스가 없으므로 시장 내 상대 서프라이즈를 제한된 기대 프록시로 사용합니다.",
            }
        ],
        "gaps": gaps,
        "scenarios": _scenarios(legacy["classification"]),
        "falsifiers": falsifiers,
        "payload": {
            "blockRefs": ["fundamental", "expectation", "price"],
            "classification": legacy["classification"],
        },
    }
    validateLensProduct(product, legacy=legacy)
    return product


def _scenarios(classification: str) -> list[dict[str, Any]]:
    return [
        {
            "id": "confirmation",
            "condition": "다음 공시 이익과 가격 반응이 현재 펀더멘털 방향을 확인",
            "classification": "confirmation",
        },
        {
            "id": "reversal",
            "condition": "다음 공시 이익 또는 가격 추세가 현재 방향을 반전",
            "classification": "inconclusive" if classification == "confirmation" else "reassessment",
        },
    ]


def _falsifiers(classification: str) -> list[dict[str, Any]]:
    common = {
        "underReaction": "다음 실적에서 이익 개선이 소멸하거나 가격 약세의 기업 고유 원인이 확인됨",
        "confirmation": "다음 실적이 악화되거나 가격이 추세를 이탈함",
        "overOptimism": "실제 컨센서스 상향과 다음 실적 개선이 가격 강세를 뒷받침함",
        "deteriorationPriced": "이익 추세가 반전되고 가격이 중기 추세를 회복함",
        "inconclusive": "세 입력이 같은 방향으로 2회 연속 확인됨",
    }
    return [{"id": "classificationBreak", "condition": common[classification]}]


def _quantClaims(
    legacy: dict[str, Any],
    evidence: list[dict[str, Any]],
    falsifiers: list[dict[str, Any]],
    *,
    asOf: str,
    priceAsOf: str | None,
    period: str | None,
) -> list[dict[str, Any]]:
    evidenceById = {str(row.get("id")): row for row in evidence if row.get("id")}
    falsifierIds = {str(row.get("id")) for row in falsifiers if row.get("id")}
    if "classificationBreak" not in falsifierIds:
        return []

    claims = []
    definitions = (
        (
            "fundamental",
            "quant.fundamental",
            "fundamentalMomentum",
            "latestPeriod",
            legacy["fundamental"].get("period") or period,
        ),
        ("price", "quant.priceReaction", "marketReaction", "currentMarket", priceAsOf),
    )
    for blockKey, claimId, comparisonKey, horizon, dataAsOf in definitions:
        block = legacy[blockKey]
        evidenceId = f"quant.{blockKey}"
        evidenceRow = evidenceById.get(evidenceId)
        if evidenceRow is None or block.get("status") != "observed" or not evidenceRow.get("sourceRef"):
            continue
        claims.append(
            {
                "id": claimId,
                "label": "공시 이익 변화" if blockKey == "fundamental" else "가격 반응",
                "comparisonKey": comparisonKey,
                "basis": "marketBehavior",
                "direction": _claimDirection(block.get("direction")),
                "horizon": horizon,
                "asOf": asOf,
                "dataAsOf": str(dataAsOf) if dataAsOf is not None else None,
                "period": period,
                "status": "observed",
                "sourceRef": str(evidenceRow["sourceRef"]),
                "evidenceRefs": [evidenceId],
                "falsifierRefs": ["classificationBreak"],
                **({"value": block["score"]} if block.get("score") is not None else {}),
            }
        )

    relationEvidence = [
        evidenceId
        for evidenceId in ("quant.fundamental", "quant.expectation", "quant.price")
        if evidenceId in evidenceById
    ]
    sourceRow = evidenceById.get("quant.fundamental") or evidenceById.get("quant.price")
    if relationEvidence and sourceRow and sourceRow.get("sourceRef"):
        claims.append(
            {
                "id": "quant.fundamentalPriceRelation",
                "label": "펀더멘털과 가격의 관계",
                "comparisonKey": "fundamentalPriceRelation",
                "basis": "marketBehavior",
                "direction": "unknown",
                "horizon": "latestDecision",
                "asOf": asOf,
                "dataAsOf": priceAsOf,
                "period": period,
                "status": "derived",
                "sourceRef": str(sourceRow["sourceRef"]),
                "evidenceRefs": relationEvidence,
                "falsifierRefs": ["classificationBreak"],
                "relation": str(legacy["classification"]),
            }
        )
    return sorted(claims, key=lambda row: row["id"])


def _claimDirection(value: Any) -> str:
    return {"positive": "supportive", "negative": "adverse", "neutral": "neutral"}.get(str(value), "unknown")


def _latestPeriod(value: dict[str, Any]) -> str | None:
    years = value.get("years")
    if isinstance(years, list) and years:
        return str(years[-1])
    history = value.get("opIncomeHistory")
    if isinstance(history, dict) and history:
        return str(max(history))
    return None


def _direction(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 0.2:
        return "positive"
    if score <= -0.2:
        return "negative"
    return "neutral"


def _clamp(value: float) -> float:
    return max(-1.0, min(1.0, float(value)))


__all__ = ["buildDivergenceResult"]
