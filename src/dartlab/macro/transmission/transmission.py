"""Macro transmission edge registry for Macro Lens.

This module keeps the market/sector side of Macro Lens inside the L2 macro
engine. It does not import Company or analysis code; company-level exposure
quality remains owned by ``Company.analysis("macro", "매크로민감도")``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

from dartlab.macro.seriesFetch import getGather


@dataclass(frozen=True)
class MacroDriver:
    """Canonical macro driver metadata.

    Args:
        id: Canonical driver id shared with the terminal macro series catalog.
        labelKr: Korean display label.
        source: Source family, for example ``ECOS`` or ``FRED``.
        sourceSeriesId: Original provider series id.
        market: Driver market scope.
        unit: Display unit.
        group: Driver group.
        transform: Intended transformation for comparison.
        directionSemantics: Human-readable directional interpretation.
        defaultLagMonths: Candidate lag range.
        releaseLagDays: Expected publication lag.
        staleAfterDays: Freshness limit.
        requiredAsOfPolicy: Look-ahead policy.

    Returns:
        MacroDriver: Immutable driver registry row.

    Raises:
        없음.

    Example:
        >>> MacroDriver("USDKRW", "원/달러", "ECOS", "USDKRW", "KR", "원", "FX", "level", "...", (0, 3), 1, 10, "observation_date <= price_as_of").id
        'USDKRW'
    """

    id: str
    labelKr: str
    source: str
    sourceSeriesId: str
    market: str
    unit: str
    group: str
    transform: str
    directionSemantics: str
    defaultLagMonths: tuple[int, int]
    releaseLagDays: int
    staleAfterDays: int
    requiredAsOfPolicy: str


@dataclass(frozen=True)
class TransmissionEdge:
    """Macro driver to financial-channel edge.

    Args:
        id: Stable edge id.
        driverId: Canonical driver id.
        market: Edge market scope.
        sectorKeys: Applicable sector keys, or ``("all",)``.
        channel: Macro Lens financial channel.
        financialLine: Financial statement line touched by the edge.
        valuationLever: Valuation lever affected by the channel.
        sign: Directional sign candidate.
        lagMonths: Candidate lag range.
        evidenceLevel: ``observed`` | ``sectorPrior`` | ``template``.
        confidence: Qualitative confidence bucket.
        requiredCompanyEvidence: Company evidence required before quant exposure.
        falsifiers: Conditions that can invalidate the edge.
        sourceRefs: Registry source refs.

    Returns:
        TransmissionEdge: Immutable transmission registry row.

    Raises:
        없음.

    Example:
        >>> TransmissionEdge("x", "USDKRW", "KR", ("all",), "revenue", "매출", "growth", "mixed", (0, 3), "template", "low", (), (), ()).evidenceLevel
        'template'
    """

    id: str
    driverId: str
    market: str
    sectorKeys: tuple[str, ...]
    channel: str
    financialLine: str
    valuationLever: str
    sign: str
    lagMonths: tuple[int, int]
    evidenceLevel: str
    confidence: str
    requiredCompanyEvidence: tuple[str, ...]
    falsifiers: tuple[str, ...]
    sourceRefs: tuple[str, ...]


DRIVER_ALIASES: dict[str, str] = {
    "KRW_USD": "USDKRW",
    "BASE_RATE_KR": "BASE_RATE",
    "WTI": "DCOILWTICO",
    "HY_SPREAD": "BAMLH0A0HYM2",
}

DRIVERS: tuple[MacroDriver, ...] = (
    MacroDriver(
        "USDKRW",
        "원/달러",
        "ECOS",
        "USDKRW",
        "KR",
        "원",
        "FX",
        "level_and_mom_1m",
        "상승은 원화 약세다. 수출 환산매출과 수입원가를 동시에 흔든다.",
        (0, 3),
        1,
        10,
        "observation_date <= price_as_of",
    ),
    MacroDriver(
        "BASE_RATE",
        "한국 기준금리",
        "ECOS",
        "BASE_RATE",
        "KR",
        "%",
        "rates",
        "level_and_delta_3m",
        "상승은 이자비용, 차입 재조달, 할인율 압력을 키운다.",
        (3, 12),
        1,
        45,
        "observation_date <= price_as_of",
    ),
    MacroDriver(
        "CPI",
        "소비자물가 YoY",
        "ECOS",
        "CPI",
        "KR",
        "%",
        "inflation",
        "yoy_and_mom_1m",
        "상승은 가격 전가 여지와 실질수요 둔화 압력을 동시에 만든다.",
        (1, 6),
        20,
        75,
        "observation_date <= price_as_of",
    ),
    MacroDriver(
        "EXPORT",
        "수출 YoY",
        "ECOS",
        "EXPORT",
        "KR",
        "%",
        "trade",
        "yoy_and_mom_1m",
        "상승은 외부수요와 제조업 매출 환경 개선 신호다.",
        (1, 6),
        10,
        45,
        "observation_date <= price_as_of",
    ),
    MacroDriver(
        "DGS10",
        "미국 10년 국채",
        "FRED",
        "DGS10",
        "US",
        "%",
        "rates",
        "level_and_delta_1m",
        "상승은 장기 할인율과 성장주 multiple 압력으로 전파될 수 있다.",
        (0, 6),
        1,
        7,
        "observation_date <= price_as_of",
    ),
    MacroDriver(
        "BAMLH0A0HYM2",
        "미국 HY 스프레드",
        "FRED",
        "BAMLH0A0HYM2",
        "US",
        "%p",
        "credit",
        "level_and_delta_1m",
        "상승은 신용위험과 자금조달 압력 확대 신호다.",
        (0, 3),
        1,
        7,
        "observation_date <= price_as_of",
    ),
    MacroDriver(
        "DCOILWTICO",
        "WTI",
        "FRED",
        "DCOILWTICO",
        "GLOBAL",
        "$",
        "commodity",
        "level_and_pct_1m",
        "상승은 에너지 매출에는 증가 요인, 제조·물류 원가에는 압력 요인일 수 있다.",
        (0, 3),
        1,
        7,
        "observation_date <= price_as_of",
    ),
)

EDGES: tuple[TransmissionEdge, ...] = (
    TransmissionEdge(
        "fx-export-revenue",
        "USDKRW",
        "KR",
        ("semiconductor", "auto", "shipbuilding", "chemical", "battery"),
        "revenue",
        "매출 성장률 / 환산손익",
        "growth",
        "mixed",
        (0, 3),
        "sectorPrior",
        "low",
        ("해외 매출 비중", "외화 매출·매입 통화", "FX 손익 주석"),
        ("달러 원가 비중이 해외 매출 효과를 상쇄", "헤지 정책으로 환산 민감도 약화"),
        ("driver:USDKRW", "macro.transmission:sectorPrior:fx-export"),
    ),
    TransmissionEdge(
        "export-demand-revenue",
        "EXPORT",
        "KR",
        ("semiconductor", "auto", "shipbuilding", "chemical", "battery", "logistics"),
        "revenue",
        "매출 성장률 / 가동률",
        "growth",
        "positive",
        (1, 6),
        "observed",
        "medium",
        ("수출 매출", "주요 제품 수요", "재고와 수주"),
        ("내수 매출 중심", "재고 과잉으로 출하 증가가 매출로 이어지지 않음"),
        ("driver:EXPORT", "macro.transmission:observed:export-demand"),
    ),
    TransmissionEdge(
        "rate-debt-interest",
        "BASE_RATE",
        "KR",
        ("all",),
        "balanceSheet",
        "이자비용 / 차입 재조달",
        "discountRate",
        "negative",
        (3, 12),
        "template",
        "low",
        ("부채비율", "단기차입금", "이자보상배율", "차입금 만기"),
        ("순현금 기업", "고정금리 장기차입 중심", "이자수익이 비용을 상쇄"),
        ("driver:BASE_RATE", "macro.transmission:template:rate-debt"),
    ),
    TransmissionEdge(
        "rate-bank-margin",
        "BASE_RATE",
        "KR",
        ("finance", "bank"),
        "margin",
        "순이자마진 / 조달비용",
        "margin",
        "mixed",
        (1, 6),
        "sectorPrior",
        "low",
        ("예대금리차", "조달 구조", "대손비용", "금리민감자산"),
        ("조달비용이 대출금리보다 빠르게 상승", "대손비용 증가가 NIM 개선을 상쇄"),
        ("driver:BASE_RATE", "macro.transmission:sectorPrior:bank-rate"),
    ),
    TransmissionEdge(
        "hy-risk-premium",
        "BAMLH0A0HYM2",
        "US",
        ("all",),
        "valuation",
        "신용스프레드 / 위험프리미엄",
        "riskPremium",
        "negative",
        (0, 3),
        "observed",
        "medium",
        ("신용등급", "차입 의존도", "만기 구조", "현금 보유"),
        ("무차입 또는 충분한 현금", "방어적 현금흐름", "정부/모회사 지원 가능성"),
        ("driver:BAMLH0A0HYM2", "macro.transmission:observed:credit-spread"),
    ),
    TransmissionEdge(
        "oil-margin-cost",
        "DCOILWTICO",
        "GLOBAL",
        ("chemical", "auto", "logistics", "food", "energy", "utility"),
        "margin",
        "매출총이익률 / 원가율",
        "margin",
        "mixed",
        (0, 3),
        "sectorPrior",
        "low",
        ("원재료 비중", "가격 전가력", "재고 회전", "연료비 비중"),
        ("원가 전가 계약", "재고평가 이익", "에너지 매출 비중 우세"),
        ("driver:DCOILWTICO", "macro.transmission:sectorPrior:oil-margin"),
    ),
    TransmissionEdge(
        "cpi-utility-tariff",
        "CPI",
        "KR",
        ("utility", "food", "retail"),
        "margin",
        "판가 / 비용 전가",
        "margin",
        "mixed",
        (1, 6),
        "template",
        "low",
        ("가격 전가력", "규제 요금", "수요 탄력성"),
        ("가격 규제로 판가 전가 불가", "실질소득 둔화로 물량 감소"),
        ("driver:CPI", "macro.transmission:template:cpi-margin"),
    ),
)

_EVIDENCE_LABELS = {"observed": "OBS", "sectorPrior": "PRIOR", "template": "TPL"}


def analyzeTransmission(
    market: str = "KR",
    *,
    sectorKey: str | None = None,
    stockCode: str | None = None,
    companyEvidence: list[dict[str, Any]] | None = None,
    contextGaps: list[dict[str, Any]] | None = None,
    asOf: str | None = None,
    includeCrossMarket: bool = True,
) -> dict[str, Any]:
    """Return market/sector macro transmission edges for Macro Lens.

    Args:
        market: Target market, currently ``KR`` or ``US``.
        sectorKey: Optional sector key filter. ``all`` edges always survive.
        stockCode: Optional company target bound by ``Company.macro("전파")``.
        companyEvidence: Company financial evidence rows from the public facade.
        contextGaps: Missing company context rows collected by the facade.
        asOf: Optional date cap passed to macro series fetch.
        includeCrossMarket: If true, include US/GLOBAL drivers that can transmit into KR risk appetite.

    Returns:
        dict[str, Any]: ``{market, asOf, dataAsOf, drivers, edges, product}``.
        Driver rows contain ``sourceLineage`` with ``sourceSeriesId``, ``date``, ``value``,
        ``unit``, ``artifactPath`` and ``status``. Edge rows carry ``evidenceLabel`` as
        ``OBS``/``PRIOR``/``TPL``.

    Raises:
        ValueError: Unsupported market.

    Example:
        >>> r = analyzeTransmission("KR", sectorKey="semiconductor")
        >>> r["edges"][0]["evidenceLabel"] in {"OBS", "PRIOR", "TPL"}
        True
    """
    normalizedMarket = market.upper()
    if normalizedMarket not in {"KR", "US"}:
        raise ValueError("market 은 'KR' 또는 'US' 만 지원합니다.")

    marketSet = _marketSet(normalizedMarket, includeCrossMarket=includeCrossMarket)
    selectedEdges = [edge for edge in EDGES if edge.market in marketSet and _sectorMatches(edge, sectorKey)]
    requiredDriverIds = {edge.driverId for edge in selectedEdges}
    driversById = {driver.id: driver for driver in DRIVERS}
    driverRows: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for driverId in sorted(requiredDriverIds):
        driver = driversById.get(driverId)
        if driver is None:
            missing.append(
                {
                    "id": f"driver.{driverId}",
                    "status": "notWiredYet",
                    "reason": "edge references a driver that is absent from DRIVERS",
                    "sourceRef": f"macro.transmission:driver:{driverId}",
                }
            )
            continue
        lineage, lineageMissing = _sourceLineage(driver, asOf=asOf)
        if lineageMissing is not None:
            missing.append(lineageMissing)
        driverRows.append(
            {
                **asdict(driver),
                "defaultLagMonths": list(driver.defaultLagMonths),
                "sourceLineage": lineage,
                "signal": _driverSignal(lineage),
            }
        )

    driverRowsById = {row["id"]: row for row in driverRows}
    edgeRows = [
        _edgeRow(edge, driverRowsById.get(edge.driverId), companyEvidence or [])
        for edge in selectedEdges
        if edge.driverId in driversById
    ]
    result = {
        "target": stockCode or f"{normalizedMarket}:{sectorKey or 'market'}",
        "stockCode": stockCode,
        "market": normalizedMarket,
        "sectorKey": sectorKey,
        "asOf": asOf or date.today().isoformat(),
        "dataAsOf": _latestAsOf(driverRows),
        "drivers": driverRows,
        "edges": edgeRows,
        "regimeEvidence": _regimeEvidence(driverRows),
        "aliases": DRIVER_ALIASES,
        "sourceRefs": [
            "dartlab://macro/transmission",
            "ui/packages/contracts/src/macro.ts::MACRO_SERIES",
            "macro/{ecos,fred}/observations.parquet",
        ],
        "missing": missing,
        "contextGaps": contextGaps or [],
    }
    from dartlab.macro.transmission._product import buildTransmissionProduct

    result["product"] = buildTransmissionProduct(result)
    return result


def _marketSet(market: str, *, includeCrossMarket: bool) -> set[str]:
    if market == "US":
        return {"US", "GLOBAL"} if includeCrossMarket else {"US"}
    return {"KR", "GLOBAL", "US"} if includeCrossMarket else {"KR"}


def _sectorMatches(edge: TransmissionEdge, sectorKey: str | None) -> bool:
    if sectorKey is None or "all" in edge.sectorKeys:
        return True
    return sectorKey in edge.sectorKeys


def _edgeRow(
    edge: TransmissionEdge,
    driver: dict[str, Any] | None,
    companyEvidence: list[dict[str, Any]],
) -> dict[str, Any]:
    matched, matchedRequirements = _matchCompanyEvidence(edge.requiredCompanyEvidence, companyEvidence)
    requiredCount = len(edge.requiredCompanyEvidence)
    coverage = len(matchedRequirements) / requiredCount if requiredCount else 1.0
    if requiredCount and coverage >= 0.5:
        resolvedEvidenceLevel = "companyObserved"
    elif matchedRequirements:
        resolvedEvidenceLevel = "companyPartial"
    else:
        resolvedEvidenceLevel = edge.evidenceLevel
    signal = driver.get("signal") if isinstance(driver, dict) else "missing"
    return {
        **asdict(edge),
        "sectorKeys": list(edge.sectorKeys),
        "lagMonths": list(edge.lagMonths),
        "requiredCompanyEvidence": list(edge.requiredCompanyEvidence),
        "falsifiers": list(edge.falsifiers),
        "sourceRefs": list(edge.sourceRefs),
        "evidenceLabel": _EVIDENCE_LABELS.get(edge.evidenceLevel, "LOCK"),
        "sourceRef": f"macro.transmission:edge:{edge.id}",
        "driverSignal": signal,
        "impactDirection": _impactDirection(signal, edge.sign),
        "resolvedEvidenceLevel": resolvedEvidenceLevel,
        "companyEvidenceCoverage": round(coverage, 3),
        "matchedCompanyRequirements": matchedRequirements,
        "companyEvidence": matched,
    }


def _sourceLineage(driver: MacroDriver, *, asOf: str | None) -> tuple[dict[str, Any], dict[str, str] | None]:
    artifactPath = f"macro/{driver.source.lower()}/observations.parquet"
    base = {
        "source": driver.source,
        "sourceSeriesId": driver.sourceSeriesId,
        "date": None,
        "value": None,
        "previousDate": None,
        "previousValue": None,
        "change": None,
        "unit": driver.unit,
        "artifactPath": artifactPath,
        "asOfPolicy": driver.requiredAsOfPolicy,
        "status": "missing",
    }
    try:
        g = getGather(asOf)
        df = g.macro(driver.sourceSeriesId)
        if df is None or len(df) == 0:
            raise KeyError("empty macro series")
        if "date" not in df.columns or "value" not in df.columns:
            raise KeyError("macro series must contain date/value")
        rows = df.drop_nulls("value").sort("date")
        if len(rows) == 0:
            raise KeyError("macro series has no value")
        latest = rows[-1]
        dateValue = latest["date"][0]
        value = latest["value"][0]
        previousDate = None
        previousValue = None
        change = None
        if len(rows) >= 2:
            previous = rows[-2]
            previousDate = str(previous["date"][0])[:10]
            rawPrevious = previous["value"][0]
            previousValue = float(rawPrevious) if rawPrevious is not None else None
            if value is not None and previousValue is not None:
                change = float(value) - previousValue
        return (
            {
                **base,
                "date": str(dateValue)[:10],
                "value": float(value) if value is not None else None,
                "previousDate": previousDate,
                "previousValue": previousValue,
                "change": change,
                "status": "observed",
            },
            None,
        )
    except (KeyError, ValueError, TypeError, AttributeError, ImportError, RuntimeError) as exc:
        return (
            base,
            {
                "id": f"driver.{driver.id}.latestObservation",
                "status": "missing",
                "reason": f"latest macro observation unavailable: {type(exc).__name__}",
                "sourceRef": f"{artifactPath}#{driver.sourceSeriesId}",
            },
        )


def _latestAsOf(driverRows: list[dict[str, Any]]) -> str | None:
    dates = [row["sourceLineage"].get("date") for row in driverRows if row.get("sourceLineage", {}).get("date")]
    return max(dates) if dates else None


def _driverSignal(lineage: dict[str, Any]) -> str:
    change = lineage.get("change")
    if not isinstance(change, (int, float)) or isinstance(change, bool):
        return "missing"
    if change > 0:
        return "rising"
    if change < 0:
        return "falling"
    return "flat"


def _impactDirection(signal: str, sign: str) -> str:
    if signal not in {"rising", "falling"}:
        return "unresolved"
    if sign == "mixed":
        return "twoSided"
    positiveMove = signal == "rising"
    if sign == "negative":
        return "headwind" if positiveMove else "tailwind"
    if sign == "positive":
        return "tailwind" if positiveMove else "headwind"
    return "unresolved"


def _matchCompanyEvidence(
    requirements: tuple[str, ...],
    companyEvidence: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    matchedRows: list[dict[str, Any]] = []
    matchedRequirements: list[str] = []
    seenRows = set()
    for requirement in requirements:
        normalizedRequirement = _normalizeEvidenceText(requirement)
        for row in companyEvidence:
            if not isinstance(row, dict):
                continue
            searchable = _normalizeEvidenceText(f"{row.get('id', '')} {row.get('label', '')}")
            if not searchable:
                continue
            if normalizedRequirement in searchable or searchable in normalizedRequirement:
                matchedRequirements.append(requirement)
                rowKey = row.get("id") or row.get("sourceRef") or row.get("label")
                if rowKey not in seenRows:
                    seenRows.add(rowKey)
                    matchedRows.append(row)
                break
    return matchedRows, matchedRequirements


def _normalizeEvidenceText(value: str) -> str:
    return "".join(character.lower() for character in str(value) if character.isalnum())


def _regimeEvidence(driverRows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for row in driverRows:
        lineage = row["sourceLineage"]
        evidence.append(
            {
                "id": f"driver:{row['id']}",
                "driverId": row["id"],
                "status": "observed" if lineage["status"] == "observed" else "locked",
                "date": lineage["date"],
                "value": lineage["value"],
                "unit": lineage["unit"],
                "sourceRef": f"{lineage['artifactPath']}#{row['sourceSeriesId']}",
            }
        )
    return evidence
