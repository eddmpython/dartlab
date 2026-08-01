"""Company Industry 대표 제품 조립기."""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any, Callable

from dartlab.synth.rowAccess import strictFloat as _number

_EXPECTED_ERRORS = (
    KeyError,
    ValueError,
    TypeError,
    AttributeError,
    ArithmeticError,
    ImportError,
    RuntimeError,
    OSError,
)


def companyIndustryResult(company: Any) -> dict[str, Any]:
    """회사 위치와 산업 내부 자산을 한 번에 조립한다."""
    from dartlab.industry.build.pipeline import loadEdges, loadNodes
    from dartlab.industry.calcs.companyCalcs import calcChainPosition, calcSectorCycle, calcSectorMetrics
    from dartlab.industry.calcs.concentration import calcIndustryConcentration, calcSupplyInsights
    from dartlab.industry.calcs.profitPoolDynamics import calcProfitPoolDynamics

    position = _safeCall(calcChainPosition, company)
    if not isinstance(position, dict):
        return blockedIndustryResult(company, reason="산업 가치사슬의 primary 위치 매핑이 없습니다.")

    industryId = str(position.get("industry") or "")
    nodes = _safeCall(loadNodes) or []
    edges = _safeCall(loadEdges) or []
    sectorMetrics = _safeCall(calcSectorMetrics, company)
    sectorCycle = _safeCall(calcSectorCycle, company, sectorMetrics=sectorMetrics)
    profitPool = _safeCall(calcProfitPoolDynamics, industryId) if industryId else None
    industryConcentration = _safeCall(calcIndustryConcentration, industryId, nodes) if industryId else None
    supplyConcentration = _safeCall(calcSupplyInsights, str(getattr(company, "stockCode", "")), edges, nodes)
    relationships = _relationshipSummary(str(getattr(company, "stockCode", "")), industryId, edges)

    result: dict[str, Any] = dict(position)
    result["stockCode"] = str(getattr(company, "stockCode", "") or "unknown")
    result["market"] = str(getattr(company, "market", "") or "unknown").upper()
    result["sectorMetrics"] = sectorMetrics
    result["sectorCycle"] = sectorCycle
    result["profitPool"] = profitPool
    result["relationships"] = relationships
    result["concentration"] = {
        "industry": industryConcentration,
        "supply": supplyConcentration,
    }
    result["product"] = buildIndustryProduct(company, result)
    return result


def blockedIndustryResult(company: Any, *, reason: str) -> dict[str, Any]:
    """미지원 시장 또는 위치 결손을 구조화된 blocked 결과로 반환한다."""
    result: dict[str, Any] = {
        "industry": None,
        "industryName": None,
        "stage": None,
        "stageName": None,
        "role": None,
        "stream": None,
        "confidence": 0.0,
        "source": None,
        "updatedAt": None,
        "mappingUpdatedAt": None,
        "financialPeriod": None,
        "peers": [],
        "stockCode": str(getattr(company, "stockCode", "") or getattr(company, "ticker", "") or "unknown"),
        "market": str(getattr(company, "market", "") or "unknown").upper(),
        "sectorMetrics": None,
        "sectorCycle": None,
        "profitPool": None,
        "relationships": None,
        "concentration": None,
        "blockedReason": reason,
    }
    result["product"] = buildIndustryProduct(company, result)
    return result


def buildIndustryProduct(company: Any, result: dict[str, Any]) -> dict[str, Any]:
    """Company Industry 결과를 공통 Lens Product v1으로 표현한다."""
    from dartlab.synth.lensContract import validateLensProduct

    target = str(
        getattr(company, "stockCode", "") or getattr(company, "ticker", "") or result.get("stockCode") or "unknown"
    )
    market = str(getattr(company, "market", "") or result.get("market") or "unknown").upper()
    today = date.today().isoformat()
    mappingUpdatedAt = result.get("mappingUpdatedAt") or result.get("updatedAt")
    mappingUpdatedAt = mappingUpdatedAt if isinstance(mappingUpdatedAt, str) else None
    financialPeriod = result.get("financialPeriod")
    financialPeriod = financialPeriod if isinstance(financialPeriod, str) else None

    blocks = {
        "position": bool(result.get("industry") and result.get("stage")),
        "sectorMetrics": isinstance(result.get("sectorMetrics"), dict),
        "sectorCycle": isinstance(result.get("sectorCycle"), dict),
        "profitPool": isinstance(result.get("profitPool"), dict) and bool(result["profitPool"].get("stage시계열")),
        "relationships": isinstance(result.get("relationships"), dict)
        and int(result["relationships"].get("count") or 0) > 0,
        "concentration": isinstance(result.get("concentration"), dict)
        and any(isinstance(value, dict) and bool(value) for value in result["concentration"].values()),
    }
    observedCount = sum(blocks.values())

    gaps: list[dict[str, Any]] = []
    for block, observed in blocks.items():
        if observed:
            continue
        gaps.append(
            {
                "id": f"industry.{block}",
                "status": "missing",
                "reason": f"{block} 근거를 확보하지 못했습니다.",
                "sourceRef": block,
            }
        )
    gaps.append(
        {
            "id": "industry.demandPricingDriver",
            "status": "unsupported",
            "reason": "수요 동인과 가격 결정력은 갱신시점을 가진 명시 데이터 모델이 아직 없습니다.",
            "sourceRef": "taxonomy",
        }
    )
    blockedReason = result.get("blockedReason")
    if blockedReason:
        gaps.insert(
            0,
            {
                "id": "industry.position",
                "status": "blocked",
                "reason": str(blockedReason),
                "sourceRef": "blockedReason",
            },
        )

    relationships = result.get("relationships") if isinstance(result.get("relationships"), dict) else {}
    if relationships and float(relationships.get("evidenceCoverage") or 0) < 50:
        gaps.append(
            {
                "id": "industry.relationshipEvidence",
                "status": "partial",
                "reason": "관계 근거가 있는 edge 비율이 50% 미만입니다.",
                "sourceRef": "relationships.evidenceCoverage",
            }
        )
    if relationships and float(relationships.get("amountCoverage") or 0) < 20:
        gaps.append(
            {
                "id": "industry.relationshipAmount",
                "status": "partial",
                "reason": "거래금액이 관측된 관계 비율이 20% 미만입니다.",
                "sourceRef": "relationships.amountCoverage",
            }
        )

    if not blocks["position"]:
        status = "blocked"
    elif observedCount >= 4:
        status = "usable"
    else:
        status = "partial"

    mappingConfidence = _number(result.get("confidence")) or 0.0
    coverageRatio = observedCount / len(blocks)
    confidenceScore = round(min(100.0, mappingConfidence * 50 + coverageRatio * 50), 1)
    if status == "blocked":
        confidenceLevel = "blocked"
    elif confidenceScore >= 80:
        confidenceLevel = "high"
    elif confidenceScore >= 55:
        confidenceLevel = "medium"
    else:
        confidenceLevel = "low"

    conclusion = _conclusion(result, status, observedCount, len(blocks))
    drivers = _drivers(result)
    evidence = _evidence(target, result, blocks)
    assumptions = _assumptions(result)
    falsifiers = _falsifiers(result)
    dataAsOf = {
        "mappingUpdatedAt": mappingUpdatedAt,
        "financialPeriod": financialPeriod,
        "retrievedAt": today,
    }
    claims = _industryClaims(
        drivers,
        evidence,
        falsifiers,
        asOf=today,
        dataAsOf=dataAsOf,
        period=financialPeriod,
    )
    blockRefs = [
        key
        for key in ("industry", "stage", "sectorMetrics", "sectorCycle", "profitPool", "relationships", "concentration")
        if key in result
    ]

    product = {
        "schemaVersion": 1,
        "identity": {
            "target": target,
            "market": market,
            "engine": "industry",
            "axis": "회사위치",
            "version": "1",
        },
        "time": {
            "asOf": today,
            "dataAsOf": dataAsOf,
            "period": financialPeriod,
            "knowledgeBoundary": today,
        },
        "status": status,
        "conclusion": conclusion,
        "confidence": {
            "level": confidenceLevel,
            "score": confidenceScore,
            "method": "mappingConfidenceAndBlockCoverage",
        },
        "drivers": drivers,
        "claims": claims,
        "evidence": evidence,
        "assumptions": assumptions,
        "gaps": gaps,
        "scenarios": [],
        "falsifiers": falsifiers,
        "payload": {
            "blockRefs": blockRefs,
            "coverage": {
                "observedBlocks": observedCount,
                "totalBlocks": len(blocks),
                "blocks": blocks,
            },
            "peerCount": len(result.get("peers") or []),
            "relationshipCoverage": {
                "count": relationships.get("count"),
                "evidenceCoverage": relationships.get("evidenceCoverage"),
                "amountCoverage": relationships.get("amountCoverage"),
                "ratioCoverage": relationships.get("ratioCoverage"),
            },
        },
    }
    validateLensProduct(product, legacy=result)
    return product


def _relationshipSummary(stockCode: str, industryId: str, edges: list[Any]) -> dict[str, Any]:
    related = [
        edge
        for edge in edges
        if (getattr(edge, "fromCode", None) == stockCode or getattr(edge, "toCode", None) == stockCode)
        and (not industryId or getattr(edge, "industry", None) == industryId)
    ]
    count = len(related)
    byType = Counter(str(getattr(edge, "edgeType", "") or "unknown") for edge in related)
    evidenceCount = sum(bool(getattr(edge, "evidence", None)) for edge in related)
    amountCount = sum(_number(getattr(edge, "amount", None)) is not None for edge in related)
    ratioCount = sum(_number(getattr(edge, "ratio", None)) is not None for edge in related)

    ordered = sorted(
        related,
        key=lambda edge: (
            bool(getattr(edge, "evidence", None)),
            _number(getattr(edge, "amount", None)) is not None,
            _number(getattr(edge, "confidence", None)) or 0.0,
            abs(_number(getattr(edge, "amount", None)) or 0.0),
        ),
        reverse=True,
    )
    top = [
        {
            "fromCode": getattr(edge, "fromCode", ""),
            "fromName": getattr(edge, "fromName", ""),
            "toCode": getattr(edge, "toCode", ""),
            "toName": getattr(edge, "toName", ""),
            "type": getattr(edge, "edgeType", ""),
            "product": getattr(edge, "product", ""),
            "confidence": getattr(edge, "confidence", None),
            "source": getattr(edge, "source", ""),
            "evidence": getattr(edge, "evidence", ""),
            "amount": getattr(edge, "amount", None),
            "ratio": getattr(edge, "ratio", None),
        }
        for edge in ordered[:12]
    ]
    return {
        "count": count,
        "byType": dict(byType),
        "evidenceCoverage": round(evidenceCount / count * 100, 1) if count else 0.0,
        "amountCoverage": round(amountCount / count * 100, 1) if count else 0.0,
        "ratioCoverage": round(ratioCount / count * 100, 1) if count else 0.0,
        "top": top,
    }


def _conclusion(result: dict[str, Any], status: str, observed: int, total: int) -> dict[str, str]:
    if status == "blocked":
        return {
            "label": "산업 위치 판단 불가",
            "summary": str(result.get("blockedReason") or "가치사슬 위치 근거가 없습니다."),
        }
    industryName = str(result.get("industryName") or result.get("industry") or "산업")
    stageName = str(result.get("stageName") or result.get("stage") or "미분류 공정")
    parts = [f"{industryName} 가치사슬의 {stageName} 위치입니다."]
    cycle = result.get("sectorCycle")
    if isinstance(cycle, dict) and cycle.get("phase"):
        parts.append(f"산업 국면은 {cycle['phase']}입니다.")
    profitPool = result.get("profitPool")
    if isinstance(profitPool, dict) and profitPool.get("판정"):
        leader = profitPool.get("리더_끝해")
        leaderName = leader[1] if isinstance(leader, (list, tuple)) and len(leader) > 1 else None
        parts.append(f"이익풀은 {profitPool['판정']}이며 최근 유효연도 리더는 {leaderName or '미확인'}입니다.")
    parts.append(f"대표 근거 블록 {observed}/{total}개를 확보했습니다.")
    return {"label": f"{industryName} · {stageName}", "summary": " ".join(parts)}


def _drivers(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if result.get("stage"):
        rows.append(
            {
                "id": "valueChainPosition",
                "label": "가치사슬 위치",
                "value": result.get("stageName") or result.get("stage"),
                "direction": "neutral",
                "sourceRef": "stage",
            }
        )
    metrics = result.get("sectorMetrics")
    if isinstance(metrics, dict):
        for key, label in (
            ("myOpmPercentile", "영업이익률 백분위"),
            ("myCagrPercentile", "매출성장 백분위"),
            ("myRoePercentile", "ROE 백분위"),
        ):
            value = _number(metrics.get(key))
            if value is None:
                continue
            rows.append(
                {
                    "id": key,
                    "label": label,
                    "value": round(value, 1),
                    "unit": "percentile",
                    "direction": "positive" if value >= 60 else "negative" if value < 40 else "neutral",
                    "sourceRef": f"sectorMetrics.{key}",
                }
            )
    cycle = result.get("sectorCycle")
    if isinstance(cycle, dict) and cycle.get("phase"):
        rows.append(
            {
                "id": "sectorCycle",
                "label": "산업 국면",
                "value": cycle.get("phase"),
                "direction": "positive"
                if cycle.get("direction") == "개선"
                else "negative"
                if cycle.get("direction") == "악화"
                else "neutral",
                "sourceRef": "sectorCycle",
            }
        )
    profitPool = result.get("profitPool")
    if isinstance(profitPool, dict) and profitPool.get("판정"):
        rows.append(
            {
                "id": "profitPool",
                "label": "이익풀 동학",
                "value": profitPool.get("판정"),
                "direction": "neutral",
                "sourceRef": "profitPool",
            }
        )
    return rows


def _evidence(target: str, result: dict[str, Any], blocks: dict[str, bool]) -> list[dict[str, Any]]:
    rows = []
    if blocks["position"]:
        rows.append(
            {
                "id": "industry.position",
                "kind": "industryNode",
                "sourceRef": f"dartlab://industry/{target}/position",
                "status": "observed",
                "observedAt": result.get("mappingUpdatedAt") or result.get("updatedAt"),
                "detail": f"source={result.get('source')}, confidence={result.get('confidence')}",
            }
        )
    for block in ("sectorMetrics", "sectorCycle", "profitPool", "relationships", "concentration"):
        if not blocks[block]:
            continue
        rows.append(
            {
                "id": f"industry.{block}",
                "kind": "calculationBlock",
                "sourceRef": f"dartlab://industry/{target}/{block}",
                "status": "derived",
            }
        )
    return rows


def _assumptions(result: dict[str, Any]) -> list[dict[str, Any]]:
    profitPool = result.get("profitPool")
    if not isinstance(profitPool, dict) or not profitPool.get("생존편향주의"):
        return []
    return [
        {
            "id": "survivorshipBias",
            "value": profitPool["생존편향주의"],
            "sourceRef": "profitPool.생존편향주의",
        }
    ]


def _falsifiers(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {
            "id": "positionRemap",
            "condition": "primary 산업 노드의 stage 또는 source가 변경되면 가치사슬 결론을 다시 평가합니다.",
            "sourceRef": "stage",
        }
    ]
    metrics = result.get("sectorMetrics")
    if isinstance(metrics, dict) and _number(metrics.get("myOpmPercentile")) is not None:
        rows.append(
            {
                "id": "opmPercentileBreak",
                "condition": "영업이익률 백분위가 25 미만으로 하락하면 산업 내 경쟁력 결론을 다시 평가합니다.",
                "sourceRef": "sectorMetrics.myOpmPercentile",
            }
        )
    cycle = result.get("sectorCycle")
    if isinstance(cycle, dict) and cycle.get("phase"):
        rows.append(
            {
                "id": "sectorCycleBreak",
                "condition": "산업 국면의 개선 또는 악화 방향이 반전되면 현재 국면 결론을 다시 평가합니다.",
                "sourceRef": "sectorCycle",
            }
        )
    profitPool = result.get("profitPool")
    if isinstance(profitPool, dict) and profitPool.get("리더_끝해"):
        rows.append(
            {
                "id": "profitPoolLeaderChange",
                "condition": "최근 유효연도 이익풀 리더 공정이 바뀌면 현재 산업 구조 결론을 다시 평가합니다.",
                "sourceRef": "profitPool.리더_끝해",
            }
        )
    return rows


def _industryClaims(
    drivers: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    falsifiers: list[dict[str, Any]],
    *,
    asOf: str,
    dataAsOf: dict[str, Any],
    period: str | None,
) -> list[dict[str, Any]]:
    driver = next((row for row in drivers if isinstance(row, dict) and row.get("id") == "sectorCycle"), None)
    if driver is None or not driver.get("sourceRef"):
        return []
    evidenceById = {str(row.get("id")): row for row in evidence if row.get("id")}
    falsifierIds = {str(row.get("id")) for row in falsifiers if row.get("id")}
    evidenceRow = evidenceById.get("industry.sectorCycle")
    if evidenceRow is None or not evidenceRow.get("sourceRef") or "sectorCycleBreak" not in falsifierIds:
        return []
    direction = {"positive": "supportive", "negative": "adverse", "neutral": "neutral"}.get(
        str(driver.get("direction")), "unknown"
    )
    return [
        {
            "id": "industry.cycle",
            "label": str(driver.get("label") or "산업 국면"),
            "comparisonKey": "industryCycle",
            "basis": "industryCycle",
            "direction": direction,
            "horizon": "currentCycle",
            "asOf": asOf,
            "dataAsOf": dataAsOf,
            "period": period,
            "status": "derived",
            "sourceRef": str(evidenceRow["sourceRef"]),
            "evidenceRefs": ["industry.sectorCycle"],
            "falsifierRefs": ["sectorCycleBreak"],
            **({"value": driver["value"]} if "value" in driver else {}),
        }
    ]


def _safeCall(function: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    try:
        return function(*args, **kwargs)
    except _EXPECTED_ERRORS:
        return None


__all__ = ["blockedIndustryResult", "buildIndustryProduct", "companyIndustryResult"]
