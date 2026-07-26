"""Analysis 대표 제품 조립기.

기존 ``종합평가`` 축 아래에서 같은 Analysis 엔진의 직접 계산을 조합한다.
다른 L2 엔진을 호출하지 않으며, 계산 실패와 데이터 결손을 0으로 바꾸지 않는다.
"""

from __future__ import annotations

import importlib
from datetime import date
from typing import Any

from dartlab.core.memory import memoizedCalc

_COMPONENTS = (
    ("earnings", "marginTrend", "dartlab.analysis.financial.profitability", "calcMarginTrend", True),
    ("earnings", "growthTrend", "dartlab.analysis.financial.growthAnalysis", "calcGrowthTrend", True),
    ("cash", "cashQuality", "dartlab.analysis.financial.cashflow", "calcCashQuality", True),
    ("resilience", "leverageTrend", "dartlab.analysis.financial.stability", "calcLeverageTrend", True),
    ("resilience", "coverageTrend", "dartlab.analysis.financial.stability", "calcCoverageTrend", True),
    (
        "quality",
        "earningsQualityFlags",
        "dartlab.analysis.financial.earningsQuality",
        "calcEarningsQualityFlags",
        True,
    ),
)

_REQUIRED_DOMAINS = ("earnings", "cash", "resilience", "quality")
_EXPECTED_ERROR_TYPES = (
    KeyError,
    ValueError,
    TypeError,
    AttributeError,
    ArithmeticError,
    ImportError,
    RuntimeError,
    OSError,
)


@memoizedCalc
def calcRepresentativeAnalysis(company: Any, *, basePeriod: str | None = None) -> dict[str, Any]:
    """기업의 재무, 현금, 안정성, 가치 근거를 한 대표 결과로 조립한다.

    각 계산의 원본 반환은 ``blocks``에 보존한다. 필수 계산이 실패하거나
    현금흐름 0 채움처럼 의심스러운 결과가 나오면 해당 영역을 성공으로
    간주하지 않고 ``coverage``와 ``gaps``에 이유를 남긴다.
    """
    blocks: dict[str, dict[str, Any]] = {}
    coverageRows: list[dict[str, Any]] = []
    gaps: list[dict[str, str]] = []

    for domain, blockKey, moduleName, functionName, required in _COMPONENTS:
        value, failure = _runComponent(company, moduleName, functionName, basePeriod=basePeriod)
        state, reason = _componentState(blockKey, value, failure)
        blocks.setdefault(domain, {})[blockKey] = value
        sourceRef = f"representative.blocks.{domain}.{blockKey}"
        coverageRows.append(
            {
                "id": f"{domain}.{blockKey}",
                "domain": domain,
                "required": required,
                "status": state,
                "sourceRef": sourceRef,
                "reason": reason,
            }
        )
        if state != "observed":
            gaps.append(
                {
                    "id": f"analysis.{domain}.{blockKey}",
                    "status": "partial" if state == "partial" else "missing",
                    "reason": reason,
                    "sourceRef": sourceRef,
                }
            )

    domainCoverage = {}
    for domain in _REQUIRED_DOMAINS:
        rows = [row for row in coverageRows if row["domain"] == domain and row["required"]]
        observed = sum(row["status"] == "observed" for row in rows)
        domainCoverage[domain] = {
            "status": "observed" if observed > 0 else "missing",
            "observed": observed,
            "expected": len(rows),
        }

    observedRequiredDomains = sum(row["status"] == "observed" for row in domainCoverage.values())
    observedComponents = sum(row["status"] == "observed" for row in coverageRows)
    assessment = _buildAssessment(blocks, observedRequiredDomains)

    return {
        "blocks": blocks,
        "coverage": {
            "requiredDomains": list(_REQUIRED_DOMAINS),
            "observedRequiredDomains": observedRequiredDomains,
            "domainCoverage": domainCoverage,
            "observedComponents": observedComponents,
            "totalComponents": len(coverageRows),
            "components": coverageRows,
        },
        "assessment": assessment,
        "gaps": gaps,
    }


def buildAnalysisProduct(
    company: Any,
    legacy: dict[str, Any],
    *,
    basePeriod: str | None = None,
) -> dict[str, Any]:
    """``종합평가``의 공통 Lens Product v1 블록을 만든다."""
    from dartlab.synth.lensContract import validateLensProduct

    representative = legacy.get("representative")
    target = str(getattr(company, "stockCode", "") or "unknown")
    market = str(getattr(company, "market", "") or "unknown").upper()
    today = date.today().isoformat()

    if not isinstance(representative, dict):
        representative = {"coverage": {}, "assessment": {}, "gaps": []}

    coverage = representative.get("coverage") if isinstance(representative.get("coverage"), dict) else {}
    assessment = representative.get("assessment") if isinstance(representative.get("assessment"), dict) else {}
    components = coverage.get("components") if isinstance(coverage.get("components"), list) else []
    observed = [row for row in components if isinstance(row, dict) and row.get("status") == "observed"]
    requiredObserved = int(coverage.get("observedRequiredDomains") or 0)
    requiredTotal = len(_REQUIRED_DOMAINS)

    gaps = _productGaps(representative.get("gaps"))
    if not observed:
        status = "blocked"
        if not gaps:
            gaps.append(
                {
                    "id": "analysis.representative",
                    "status": "blocked",
                    "reason": "대표 판단을 만들 직접 재무 근거가 없습니다.",
                }
            )
    elif requiredObserved < requiredTotal:
        status = "partial"
    else:
        status = "usable"

    coverageRatio = requiredObserved / requiredTotal if requiredTotal else 0.0
    confidenceScore = round(coverageRatio * 100, 1)
    if status == "blocked":
        confidenceLevel = "blocked"
    elif confidenceScore >= 80:
        confidenceLevel = "high"
    elif confidenceScore >= 50:
        confidenceLevel = "medium"
    else:
        confidenceLevel = "low"

    label = str(assessment.get("label") or "판단 보류")
    summary = str(
        assessment.get("summary") or f"필수 분석 영역 {requiredObserved}/{requiredTotal}개에서 근거를 확보했습니다."
    )
    if status == "blocked":
        label = "판단 보류"
        summary = "대표 판단을 만들 직접 재무 근거가 없어 결론을 차단했습니다."
    elif status == "partial":
        summary = f"{summary} 필수 분석 영역은 {requiredObserved}/{requiredTotal}개가 관측됐습니다."

    latestPeriod = _latestPeriod(representative) or basePeriod
    dataAsOf = legacy.get("dataAsOf")
    if not isinstance(dataAsOf, (str, dict)):
        dataAsOf = {"latestPeriod": latestPeriod, "retrievedAt": today}

    evidence = [
        {
            "id": f"analysis.{row.get('id')}",
            "kind": "calculationBlock",
            "sourceRef": f"dartlab://analysis/{target}/{row.get('sourceRef')}",
            "status": "derived",
            "detail": "Analysis 내부 직접 계산 결과",
        }
        for row in observed
    ]
    drivers = assessment.get("drivers") if isinstance(assessment.get("drivers"), list) else []
    falsifiers = _falsifiers(assessment)
    claims = _analysisClaims(
        drivers,
        evidence,
        falsifiers,
        asOf=today,
        dataAsOf=dataAsOf,
        defaultPeriod=latestPeriod,
    )

    product = {
        "schemaVersion": 1,
        "identity": {
            "target": target,
            "market": market,
            "engine": "analysis",
            "axis": "종합평가",
            "version": "1",
        },
        "time": {
            "asOf": today,
            "dataAsOf": dataAsOf,
            "period": latestPeriod,
            "knowledgeBoundary": today,
        },
        "status": status,
        "conclusion": {"label": label, "summary": summary},
        "confidence": {
            "level": confidenceLevel,
            "score": confidenceScore,
            "method": "requiredDomainCoverage",
        },
        "drivers": drivers,
        "claims": claims,
        "evidence": evidence,
        "assumptions": _assumptionRows(legacy.get("assumptions")),
        "gaps": gaps,
        "scenarios": _scenarioRows(representative),
        "falsifiers": falsifiers,
        "payload": {
            "blockRefs": ["scorecard", "piotroski", "summaryFlags", "representative"],
            "coverage": coverage,
            "assessment": assessment,
        },
    }
    validateLensProduct(product, legacy=legacy)
    return product


def _runComponent(
    company: Any,
    moduleName: str,
    functionName: str,
    *,
    basePeriod: str | None,
) -> tuple[Any, str | None]:
    try:
        module = importlib.import_module(moduleName)
        function = getattr(module, functionName)
        return function(company, basePeriod=basePeriod), None
    except _EXPECTED_ERROR_TYPES as exc:
        return None, type(exc).__name__


def _componentState(blockKey: str, value: Any, failure: str | None) -> tuple[str, str]:
    if failure:
        return "missing", f"계산이 완료되지 않았습니다 ({failure})."
    if value is None or value == {} or value == []:
        return "missing", "가용 데이터가 없어 계산 결과가 비었습니다."
    if blockKey in {"cashFlowOverview", "cashQuality"} and _looksLikeCashZeroFill(value):
        return "partial", "이익 또는 매출은 존재하지만 현금흐름이 전 기간 0이라 결손 가능성이 있습니다."
    return "observed", "계산 근거를 확보했습니다."


def _looksLikeCashZeroFill(value: Any) -> bool:
    if not isinstance(value, dict) or not isinstance(value.get("history"), list):
        return False
    rows = [row for row in value["history"] if isinstance(row, dict)]
    if not rows:
        return False
    hasActivity = any((row.get("revenue") or 0) != 0 or (row.get("netIncome") or 0) != 0 for row in rows)
    cashKeys = ("ocf", "fcf", "icf", "fcfFinancing")
    cashValues = [row.get(key) for row in rows for key in cashKeys if key in row]
    return hasActivity and bool(cashValues) and all(value in (None, 0, 0.0) for value in cashValues)


def _buildAssessment(blocks: dict[str, dict[str, Any]], observedRequiredDomains: int) -> dict[str, Any]:
    drivers: list[dict[str, Any]] = []

    margin = _latestHistoryValue(blocks, "earnings", "marginTrend", "operatingMargin")
    if margin is not None:
        value, period = margin
        contribution = 1 if value >= 15 else 0 if value >= 5 else -1
        drivers.append(
            _driver("operatingMargin", "영업이익률", value, "%", contribution, period, "earnings.marginTrend")
        )

    growth = blocks.get("earnings", {}).get("growthTrend")
    cagr = growth.get("cagr") if isinstance(growth, dict) and isinstance(growth.get("cagr"), dict) else {}
    revenueCagr = _number(cagr.get("revenue"))
    if revenueCagr is not None:
        contribution = 1 if revenueCagr >= 5 else 0 if revenueCagr >= 0 else -1
        drivers.append(
            _driver("revenueCagr", "매출 CAGR", revenueCagr, "%", contribution, None, "earnings.growthTrend")
        )
    operatingCagr = _number(cagr.get("operatingIncome"))
    if operatingCagr is not None:
        contribution = 1 if operatingCagr >= 5 else 0 if operatingCagr >= 0 else -1
        drivers.append(
            _driver(
                "operatingIncomeCagr", "영업이익 CAGR", operatingCagr, "%", contribution, None, "earnings.growthTrend"
            )
        )

    cashQuality = _latestHistoryValue(blocks, "cash", "cashQuality", "ocfToNi")
    if cashQuality is not None and not _looksLikeCashZeroFill(blocks.get("cash", {}).get("cashQuality")):
        value, period = cashQuality
        contribution = 1 if value >= 80 else 0 if value > 0 else -1
        drivers.append(_driver("cashConversion", "OCF/순이익", value, "%", contribution, period, "cash.cashQuality"))

    debtRatio = _latestHistoryValue(blocks, "resilience", "leverageTrend", "debtRatio")
    if debtRatio is not None:
        value, period = debtRatio
        contribution = 1 if value < 100 else 0 if value < 200 else -1
        drivers.append(_driver("debtRatio", "부채비율", value, "%", contribution, period, "resilience.leverageTrend"))

    coverage = _latestHistoryValue(blocks, "resilience", "coverageTrend", "interestCoverage")
    if coverage is not None:
        value, period = coverage
        contribution = 1 if value >= 3 else 0 if value >= 1 else -1
        drivers.append(
            _driver("interestCoverage", "이자보상배율", value, "배", contribution, period, "resilience.coverageTrend")
        )

    scored = [row for row in drivers if isinstance(row.get("scoreContribution"), int)]
    score = sum(row["scoreContribution"] for row in scored)
    if observedRequiredDomains < 2 or len(scored) < 3:
        label = "판단 보류"
    elif score >= 3:
        label = "재무 기반 우수"
    elif score < 0:
        label = "재무 취약 신호"
    else:
        label = "재무 기반 보통"

    positives = [row["label"] for row in scored if row["scoreContribution"] > 0]
    negatives = [row["label"] for row in scored if row["scoreContribution"] < 0]
    summaryParts = [f"{len(scored)}개 핵심 지표를 직접 비교한 결과 {label}입니다."]
    if positives:
        summaryParts.append(f"강점은 {', '.join(positives[:2])}입니다.")
    if negatives:
        summaryParts.append(f"확인할 위험은 {', '.join(negatives[:2])}입니다.")
    return {
        "label": label,
        "summary": " ".join(summaryParts),
        "score": score if scored else None,
        "drivers": drivers,
        "positiveDrivers": positives,
        "negativeDrivers": negatives,
    }


def _driver(
    driverId: str,
    label: str,
    value: float,
    unit: str,
    contribution: int,
    period: str | None,
    sourceRef: str,
) -> dict[str, Any]:
    row = {
        "id": driverId,
        "label": label,
        "value": round(value, 2),
        "unit": unit,
        "direction": _direction(contribution),
        "scoreContribution": contribution,
        "sourceRef": sourceRef,
    }
    if period:
        row["period"] = period
    return row


def _direction(contribution: int) -> str:
    return "positive" if contribution > 0 else "negative" if contribution < 0 else "neutral"


def _latestHistoryValue(
    blocks: dict[str, dict[str, Any]], domain: str, blockKey: str, valueKey: str
) -> tuple[float, str | None] | None:
    block = blocks.get(domain, {}).get(blockKey)
    if not isinstance(block, dict) or not isinstance(block.get("history"), list):
        return None
    candidates = []
    for row in block["history"]:
        if not isinstance(row, dict):
            continue
        value = _number(row.get(valueKey))
        if value is not None:
            period = str(row.get("period")) if row.get("period") is not None else None
            candidates.append((period or "", value))
    if not candidates:
        return None
    period, value = max(candidates, key=lambda row: row[0])
    return value, period or None


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _productGaps(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    rows = []
    for row in value:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "id": str(row.get("id") or "analysis.unknown"),
                "status": str(row.get("status") or "missing"),
                "reason": str(row.get("reason") or "근거가 없습니다."),
                **({"sourceRef": str(row["sourceRef"])} if row.get("sourceRef") else {}),
            }
        )
    return rows


def _assumptionRows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        return []
    return [{"id": str(key), "value": item} for key, item in value.items()]


def _scenarioRows(representative: dict[str, Any]) -> list[dict[str, Any]]:
    blocks = representative.get("blocks")
    scenarios = blocks.get("scenarios") if isinstance(blocks, dict) else None
    sensitivity = scenarios.get("scenarioSensitivity") if isinstance(scenarios, dict) else None
    shocks = sensitivity.get("shocks") if isinstance(sensitivity, dict) else None
    if isinstance(shocks, dict):
        return [
            {
                "id": str(key),
                "label": str(key),
                "result": value,
                "sourceRef": "representative.blocks.scenarios.scenarioSensitivity",
            }
            for key, value in shocks.items()
        ]

    assessment = representative.get("assessment") if isinstance(representative.get("assessment"), dict) else {}
    drivers = {
        str(row.get("id")): row for row in assessment.get("drivers", []) if isinstance(row, dict) and row.get("id")
    }
    definitions = (
        ("marginCompression", "operatingMargin", "영업이익률이 현재보다 3%p 하락"),
        ("growthReversal", "revenueCagr", "매출 CAGR이 0% 아래로 전환"),
        ("coverageStress", "interestCoverage", "이자보상배율이 1배 아래로 하락"),
    )
    return [
        {
            "id": scenarioId,
            "label": condition,
            "currentValue": drivers[driverId].get("value"),
            "unit": drivers[driverId].get("unit"),
            "driverRef": driverId,
            "sourceRef": f"representative.assessment.drivers.{driverId}",
        }
        for scenarioId, driverId, condition in definitions
        if driverId in drivers
    ]


def _falsifiers(assessment: dict[str, Any]) -> list[dict[str, Any]]:
    driverIds = {row.get("id") for row in assessment.get("drivers", []) if isinstance(row, dict) and row.get("id")}
    candidates = (
        (
            "marginBreak",
            "operatingMargin",
            "영업이익률이 현재 관측치보다 3%p 이상 하락하면 수익성 결론을 다시 평가합니다.",
        ),
        ("growthBreak", "revenueCagr", "매출 CAGR이 음수로 전환되면 성장 결론을 다시 평가합니다."),
        (
            "cashConversionBreak",
            "cashConversion",
            "영업현금 전환 방향이 정상화되거나 추가 악화되면 현금 전환 결론을 다시 평가합니다.",
        ),
        ("coverageBreak", "interestCoverage", "이자보상배율이 1배 미만이면 안정성 결론을 무효화합니다."),
    )
    return [
        {"id": falsifierId, "condition": condition, "driverRef": driverId}
        for falsifierId, driverId, condition in candidates
        if driverId in driverIds
    ]


def _analysisClaims(
    drivers: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    falsifiers: list[dict[str, Any]],
    *,
    asOf: str,
    dataAsOf: str | dict[str, Any] | None,
    defaultPeriod: str | None,
) -> list[dict[str, Any]]:
    evidenceById = {str(row.get("id")): row for row in evidence if row.get("id")}
    falsifierIds = {str(row.get("id")) for row in falsifiers if row.get("id")}
    definitions = {
        "operatingMargin": (
            "analysis.operatingMargin",
            "profitability",
            "companyFundamentals",
            "latestPeriod",
            "analysis.earnings.marginTrend",
            "marginBreak",
        ),
        "revenueCagr": (
            "analysis.revenueCagr",
            "growth",
            "companyFundamentals",
            "multiYear",
            "analysis.earnings.growthTrend",
            "growthBreak",
        ),
        "operatingIncomeCagr": (
            "analysis.operatingIncomeCagr",
            "growth",
            "companyFundamentals",
            "multiYear",
            "analysis.earnings.growthTrend",
            "growthBreak",
        ),
        "cashConversion": (
            "analysis.cashConversion",
            "cashConversion",
            "companyFundamentals",
            "latestPeriod",
            "analysis.cash.cashQuality",
            "cashConversionBreak",
        ),
    }
    claims = []
    for driver in drivers:
        if not isinstance(driver, dict) or driver.get("id") not in definitions:
            continue
        claimId, comparisonKey, basis, horizon, evidenceId, falsifierId = definitions[str(driver["id"])]
        evidenceRow = evidenceById.get(evidenceId)
        if evidenceRow is None or falsifierId not in falsifierIds or not evidenceRow.get("sourceRef"):
            continue
        claims.append(
            {
                "id": claimId,
                "label": str(driver.get("label") or claimId),
                "comparisonKey": comparisonKey,
                "basis": basis,
                "direction": _claimDirection(driver.get("direction")),
                "horizon": horizon,
                "asOf": asOf,
                "dataAsOf": dataAsOf,
                "period": str(driver.get("period") or defaultPeriod) if driver.get("period") or defaultPeriod else None,
                "status": "derived",
                "sourceRef": str(evidenceRow["sourceRef"]),
                "evidenceRefs": [evidenceId],
                "falsifierRefs": [falsifierId],
                **({"value": driver["value"]} if "value" in driver else {}),
                **({"unit": driver["unit"]} if driver.get("unit") else {}),
            }
        )
    return sorted(claims, key=lambda row: row["id"])


def _claimDirection(value: Any) -> str:
    return {"positive": "supportive", "negative": "adverse", "neutral": "neutral"}.get(str(value), "unknown")


def _latestPeriod(value: Any) -> str | None:
    periods: list[str] = []

    def visit(node: Any) -> None:
        """중첩 payload에서 period 값을 재귀 수집한다."""
        if isinstance(node, dict):
            period = node.get("period")
            if isinstance(period, str) and period:
                periods.append(period)
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return max(periods) if periods else None


__all__ = ["buildAnalysisProduct", "calcRepresentativeAnalysis"]
