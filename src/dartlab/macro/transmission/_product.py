"""Macro 대표 제품인 기업 전달경로의 내부 Lens Product 조립기."""

from __future__ import annotations

from typing import Any

_COMPANY_EVIDENCE_USABLE_RATIO = 0.5


def buildTransmissionProduct(result: dict[str, Any]) -> dict[str, Any]:
    """전파 결과의 데이터, 회사 근거, 방향성을 공통 제품 계약으로 만든다."""
    from dartlab.synth.lensContract import validateLensProduct

    stockCode = result.get("stockCode")
    target = str(stockCode or f"{result['market']}:{result.get('sectorKey') or 'market'}")
    drivers = result.get("drivers") if isinstance(result.get("drivers"), list) else []
    edges = result.get("edges") if isinstance(result.get("edges"), list) else []
    observedDrivers = [
        row for row in drivers if isinstance(row, dict) and row.get("sourceLineage", {}).get("status") == "observed"
    ]
    companyEdges = [
        row
        for row in edges
        if isinstance(row, dict) and row.get("resolvedEvidenceLevel") in {"companyObserved", "companyPartial"}
    ]
    companyCoverage = len(companyEdges) / len(edges) if edges and stockCode else 0.0

    gaps = _gaps(result, edges, stockCode=stockCode)
    if not edges or not observedDrivers:
        status = "blocked"
    elif stockCode and companyCoverage >= _COMPANY_EVIDENCE_USABLE_RATIO:
        status = "usable"
    else:
        status = "partial"
    if status in {"partial", "blocked"} and not gaps:
        gaps.append(
            {
                "id": "macro.transmission.coverage",
                "status": "partial" if status == "partial" else "blocked",
                "reason": "기업 전달경로를 확정할 직접 근거가 충분하지 않습니다.",
            }
        )

    impactEdges = companyEdges if stockCode and companyEdges else edges
    headwinds = sum(row.get("impactDirection") == "headwind" for row in impactEdges)
    tailwinds = sum(row.get("impactDirection") == "tailwind" for row in impactEdges)
    if headwinds > tailwinds:
        label = "거시 역풍 경로 우세"
    elif tailwinds > headwinds:
        label = "거시 순풍 경로 우세"
    elif observedDrivers:
        label = "거시 전파 경로 혼재"
    else:
        label = "거시 전달 판단 보류"
    summary = _summary(
        label,
        observedCount=len(observedDrivers),
        driverCount=len(drivers),
        companyEdgeCount=len(companyEdges),
        edgeCount=len(edges),
        companyBound=bool(stockCode),
    )

    macroCoverage = len(observedDrivers) / len(drivers) if drivers else 0.0
    score = round((macroCoverage * 60) + (companyCoverage * 40 if stockCode else 0), 1)
    level = "blocked" if status == "blocked" else "high" if score >= 80 else "medium" if score >= 50 else "low"

    evidence = []
    for row in observedDrivers:
        lineage = row["sourceLineage"]
        evidence.append(
            {
                "id": f"macro.driver.{row['id']}",
                "kind": "macroObservation",
                "sourceRef": f"{lineage['artifactPath']}#{row['sourceSeriesId']}",
                "status": "observed",
                "observedAt": lineage.get("date"),
                "detail": f"{row['labelKr']} 최신 관측과 직전 변화",
            }
        )
    usedCompanyEvidence = _usedCompanyEvidence(companyEdges)
    for row in usedCompanyEvidence:
        evidence.append(
            {
                "id": f"macro.company.{row.get('id')}",
                "kind": "companyFinancialEvidence",
                "sourceRef": str(row.get("sourceRef") or "dartlab://analysis/product"),
                "status": "derived",
                "observedAt": None,
                "detail": str(row.get("label") or "기업 재무 근거"),
            }
        )
    falsifiers = _falsifiers(edges)
    claims = _macroClaims(
        edges,
        evidence,
        falsifiers,
        asOf=result.get("asOf"),
        dataAsOf=result.get("dataAsOf"),
    )

    product = {
        "schemaVersion": 1,
        "identity": {
            "target": target,
            "market": result["market"],
            "engine": "macro",
            "axis": "전파",
            "version": "1",
        },
        "time": {
            "asOf": result.get("asOf"),
            "dataAsOf": result.get("dataAsOf"),
            "period": None,
            "knowledgeBoundary": result.get("asOf"),
        },
        "status": status,
        "conclusion": {"label": label, "summary": summary},
        "confidence": {
            "level": level,
            "score": score,
            "method": "macroObservationAndCompanyEvidenceCoverage",
        },
        "drivers": [_driverRow(row) for row in observedDrivers],
        "claims": claims,
        "evidence": evidence,
        "assumptions": [
            {
                "id": "edgeSign",
                "value": "registryPrior",
                "reason": "경로 부호와 시차는 기업별 회귀계수가 아니라 registry prior입니다.",
            }
        ],
        "gaps": gaps,
        "scenarios": _scenarios(edges),
        "falsifiers": falsifiers,
        "payload": {
            "blockRefs": ["drivers", "edges", "regimeEvidence"],
            "companyBound": bool(stockCode),
            "companyEdgeCount": len(companyEdges),
            "edgeCount": len(edges),
        },
    }
    validateLensProduct(product, legacy=result)
    return product


def _gaps(result: dict[str, Any], edges: list[dict[str, Any]], *, stockCode: Any) -> list[dict[str, Any]]:
    gaps = []
    for row in result.get("missing") or []:
        if not isinstance(row, dict):
            continue
        status = row.get("status")
        gaps.append(
            {
                "id": str(row.get("id") or "macro.missing"),
                "status": "missing" if status in {"missing", "notWiredYet"} else "partial",
                "reason": str(row.get("reason") or "거시 관측값이 없습니다."),
                **({"sourceRef": str(row["sourceRef"])} if row.get("sourceRef") else {}),
            }
        )
    for row in result.get("contextGaps") or []:
        if isinstance(row, dict):
            gaps.append(dict(row))
    if not stockCode:
        gaps.append(
            {
                "id": "macro.companyBinding",
                "status": "partial",
                "reason": "시장 또는 섹터 경로이며 개별 회사 재무 근거에 바인딩되지 않았습니다.",
                "sourceRef": "dartlab://company/macro/transmission",
            }
        )
    else:
        for edge in edges:
            if edge.get("resolvedEvidenceLevel") not in {"companyObserved", "companyPartial"}:
                gaps.append(
                    {
                        "id": f"macro.edge.{edge.get('id')}.companyEvidence",
                        "status": "partial",
                        "reason": "이 경로에 필요한 회사 직접 근거가 없어 sector prior 또는 template로 남았습니다.",
                        "sourceRef": str(edge.get("sourceRef") or "dartlab://macro/transmission"),
                    }
                )
    return gaps


def _driverRow(row: dict[str, Any]) -> dict[str, Any]:
    lineage = row["sourceLineage"]
    return {
        "id": row["id"],
        "label": row["labelKr"],
        "value": lineage.get("value"),
        "unit": row.get("unit"),
        "signal": row.get("signal"),
        "change": lineage.get("change"),
        "sourceRef": f"{lineage['artifactPath']}#{row['sourceSeriesId']}",
    }


def _usedCompanyEvidence(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    rows = []
    for edge in edges:
        for row in edge.get("companyEvidence") or []:
            if not isinstance(row, dict):
                continue
            key = row.get("id") or row.get("sourceRef") or row.get("label")
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return rows


def _summary(
    label: str,
    *,
    observedCount: int,
    driverCount: int,
    companyEdgeCount: int,
    edgeCount: int,
    companyBound: bool,
) -> str:
    if companyBound:
        return (
            f"{label}입니다. 거시 관측 {observedCount}/{driverCount}개와 "
            f"회사 근거가 연결된 전달경로 {companyEdgeCount}/{edgeCount}개를 확인했습니다."
        )
    return (
        f"{label}입니다. 거시 관측 {observedCount}/{driverCount}개를 확인했지만 "
        "개별 회사 재무 근거에는 아직 바인딩되지 않았습니다."
    )


def _scenarios(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(edge.get("id")),
            "driverId": edge.get("driverId"),
            "condition": f"{edge.get('driverId')} 방향이 반전될 때 {edge.get('financialLine')} 경로 재평가",
            "lagMonths": edge.get("lagMonths"),
        }
        for edge in edges[:5]
    ]


def _falsifiers(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for edge in edges:
        for index, condition in enumerate(edge.get("falsifiers") or []):
            rows.append({"id": f"{edge.get('id')}.{index}", "condition": condition})
    return rows[:12]


def _macroClaims(
    edges: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    falsifiers: list[dict[str, Any]],
    *,
    asOf: Any,
    dataAsOf: Any,
) -> list[dict[str, Any]]:
    if not isinstance(asOf, str) or not asOf:
        return []
    evidenceById = {str(row.get("id")): row for row in evidence if row.get("id")}
    falsifierIds = {str(row.get("id")) for row in falsifiers if row.get("id")}
    usableEdges = [
        edge
        for edge in edges
        if isinstance(edge, dict)
        and edge.get("resolvedEvidenceLevel") == "companyObserved"
        and edge.get("impactDirection") in {"headwind", "tailwind"}
        and isinstance(edge.get("companyEvidence"), list)
        and edge["companyEvidence"]
    ]
    if not usableEdges:
        return []
    headwinds = sum(edge.get("impactDirection") == "headwind" for edge in usableEdges)
    tailwinds = sum(edge.get("impactDirection") == "tailwind" for edge in usableEdges)
    if headwinds == tailwinds:
        return []

    evidenceRefs: set[str] = set()
    claimFalsifiers: set[str] = set()
    for edge in usableEdges:
        for row in edge.get("companyEvidence") or []:
            if not isinstance(row, dict) or not row.get("id"):
                continue
            evidenceId = f"macro.company.{row['id']}"
            if evidenceId in evidenceById:
                evidenceRefs.add(evidenceId)
        edgeId = str(edge.get("id") or "")
        for index, _ in enumerate(edge.get("falsifiers") or []):
            falsifierId = f"{edgeId}.{index}"
            if falsifierId in falsifierIds:
                claimFalsifiers.add(falsifierId)
    if not evidenceRefs or not claimFalsifiers:
        return []
    firstEvidence = evidenceById[sorted(evidenceRefs)[0]]
    if not firstEvidence.get("sourceRef"):
        return []
    return [
        {
            "id": "macro.companyTransmission",
            "label": "기업 직접근거 거시 전달경로",
            "comparisonKey": "macroTransmission",
            "basis": "macroCompanyEdges",
            "direction": "adverse" if headwinds > tailwinds else "supportive",
            "horizon": "currentCycle",
            "asOf": asOf,
            "dataAsOf": dataAsOf if isinstance(dataAsOf, (str, dict)) else None,
            "period": None,
            "status": "derived",
            "sourceRef": str(firstEvidence["sourceRef"]),
            "evidenceRefs": sorted(evidenceRefs),
            "falsifierRefs": sorted(claimFalsifiers),
        }
    ]


__all__ = ["buildTransmissionProduct"]
