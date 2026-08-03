"""Capability discovery와 EngineCall 실행 권한 사이의 정본 경계."""

from __future__ import annotations

import re

CANONICAL_COMPANY_CAPABILITY_REFS = frozenset(
    {
        "Company.panel",
        "Company.select",
        "Company.trace",
        "Company.filings",
        "Company.analysis",
        "Company.credit",
        "Company.gather",
        "Company.quant",
        "Company.macro",
        "Company.story",
        "Company.reportModel",
        "Company.industry",
        "Company.simulate",
    }
)

CANONICAL_DATA_HUB_CAPABILITY_REFS = frozenset({"dataHub", "dataHub.catalog", "dataHub.query"})
CANONICAL_AXIS_ENGINES = frozenset({"gather", "macro", "industry", "quant", "credit", "analysis"})
CANONICAL_TOP_LEVEL_CAPABILITY_REFS = frozenset(
    {
        "analysis",
        "capabilities",
        "codeToName",
        "compare",
        "credit",
        "data",
        "dataHub",
        "gather",
        "help",
        "industry",
        "listing",
        "macro",
        "nameToCode",
        "pastInsight",
        "quant",
        "scan",
        "search",
        "searchName",
        "sectorInsights",
        "simulate",
    }
)


def isEngineCallableRef(apiRef: str) -> bool:
    """Capability ref가 EngineCall 단일 실행 계약에 포함되는지 판정한다.

    Catalog 등재는 검색/문서 발견 계약이고 실행 권한이 아니다. Company는 formal
    facade 13개만, dataHub는 catalog/query만, axis 엔진은 등록 축만 허용한다.
    점 없는 top-level ref도 명시적인 read/analysis-safe allowlist만 허용한다.
    """
    ref = str(apiRef or "").strip()
    if not ref or ref.startswith("aiContract.") or ref.startswith("_") or "._" in ref:
        return False
    # Analysis Graph의 reference-only 계약은 실제 엔진 축과 같은 이름을 쓸 수 있다.
    # ``scan.market``/``scan.industry``가 그 사례로, 이름 모양만 보고 실행을 허용하면
    # 존재하지 않는 scan 축으로 dispatch 된다. 계약 metadata의 kind를 먼저 확인한다.
    from dartlab.reference.capability.registry import getAnalysisContractSpecs

    contract = getAnalysisContractSpecs().get(ref)
    if isinstance(contract, dict) and contract.get("kind") == "ai_contract":
        return False
    if ref.startswith("Company."):
        return ref in CANONICAL_COMPANY_CAPABILITY_REFS
    if ref in CANONICAL_DATA_HUB_CAPABILITY_REFS:
        return True
    if ref == "capabilities" or ref == "scan" or ref.startswith("scan."):
        return True
    head, separator, axis = ref.partition(".")
    if separator:
        return bool(axis) and head in CANONICAL_AXIS_ENGINES
    return ref in CANONICAL_TOP_LEVEL_CAPABILITY_REFS


def canonicalReplacementRefs(apiRef: str, entry: dict | None = None) -> tuple[str, ...]:
    """참조 전용 capability가 가리키는 canonical 실행 경로를 결정한다."""
    ref = str(apiRef or "").strip()
    if isEngineCallableRef(ref):
        return (ref,)
    metadata = entry or {}
    declared = tuple(str(value) for value in metadata.get("capabilityRefs") or () if isEngineCallableRef(str(value)))
    if declared:
        return tuple(dict.fromkeys(declared))
    direct = {
        "Company": ("Company.panel", "Company.analysis"),
        "Fred": ("macro",),
        "OpenDart": ("gather.dartDoc", "Company.filings"),
        "Story": ("Company.story",),
        "SelectResult": ("Company.select",),
    }.get(ref)
    if direct:
        return direct
    if not ref.startswith("Company."):
        return ()

    method = ref.split(".", 1)[1].casefold()
    groups: tuple[tuple[frozenset[str], tuple[str, ...]], ...] = (
        (
            frozenset({"disclosure", "filings", "livefilings", "readfiling", "update"}),
            ("Company.filings",),
        ),
        (frozenset({"flow", "news", "calendar", "market", "currency"}), ("Company.gather",)),
        (frozenset({"sector", "sectorparams", "rank", "network"}), ("Company.industry", "Company.analysis")),
        (frozenset({"debt", "audit"}), ("Company.credit", "Company.analysis", "Company.panel")),
        (frozenset({"ask"}), ("Company.analysis", "Company.story")),
        (frozenset({"validatestory"}), ("Company.story",)),
        (frozenset({"report"}), ("Company.reportModel",)),
    )
    for names, replacements in groups:
        if method in names:
            return replacements

    discovered: list[str] = []
    seeAlso = str(metadata.get("seeAlso") or "")
    for token in re.findall(r"(?:Company\.)?[A-Za-z][A-Za-z0-9]*", seeAlso):
        candidate = token if token.startswith("Company.") else f"Company.{token}"
        if candidate in CANONICAL_COMPANY_CAPABILITY_REFS and candidate not in discovered:
            discovered.append(candidate)
    if discovered:
        return tuple(discovered[:3])
    return ("Company.panel",)


def engineCallContract(apiRef: str, entry: dict | None = None) -> dict:
    """실행 가능한 capability의 공통 EngineCall 입력 계약을 구조화한다."""
    if not isEngineCallableRef(apiRef):
        return {}
    metadata = entry or {}
    declared = metadata.get("declared") if isinstance(metadata.get("declared"), dict) else {}
    contract: dict = {
        "tool": "EngineCall",
        "apiRef": apiRef,
        "args": {},
    }
    if apiRef.startswith("Company."):
        contract["argsContract"] = {"stockCode": {"required": True, "type": "stockCode|ticker|companyName"}}
    elif "." in apiRef:
        targetRequired = declared.get("targetRequired")
        if targetRequired is None:
            targetRequired = declared.get("stockRequired")
        targetType = declared.get("targetType") or declared.get("targetParam")
        targetContract: dict = {"required": targetRequired}
        if targetType:
            targetContract["type"] = targetType
        contract["argsContract"] = {"target": targetContract}
        if options := declared.get("options"):
            contract["optionNames"] = list(options) if isinstance(options, list | tuple) else [str(options)]
        if returnType := declared.get("returnType"):
            contract["returnType"] = returnType
    if example := metadata.get("example"):
        contract["nativeExample"] = example
    return contract


def executionGuide(
    apiRef: str,
    *,
    engineCallable: bool | None = None,
    replacementRefs: tuple[str, ...] | None = None,
) -> str:
    """Capability 소비자가 실행 가능성과 대체 경로를 혼동하지 않게 안내한다."""
    allowed = isEngineCallableRef(apiRef) if engineCallable is None else bool(engineCallable)
    if allowed:
        return f'EngineCall({{"apiRef": "{apiRef}", "args": {{...}}}})로 단일 호출할 수 있습니다.'
    replacements = replacementRefs if replacementRefs is not None else canonicalReplacementRefs(apiRef)
    if replacements:
        joined = ", ".join(replacements)
        return f"공개 참조 전용입니다. EngineCall apiRef로 사용하지 말고 canonical 대체 경로를 선택하세요: {joined}."
    return "공개 참조 전용이며 같은 의미의 자동 실행 경로가 없습니다. 설명으로만 사용하세요."


ENGINE_QUESTION_CONTRACTS: dict[str, dict[str, object]] = {
    "Company.reportModel": {
        "contractId": "investment.decision_memo",
        "capabilityRefs": [
            "Company.reportModel",
            "Company.gather",
            "Company.filings",
            "Company.industry",
            "Company.macro",
            "Company.simulate",
        ],
        "tool": "EngineCall",
        "questionTypes": ["investment_decision"],
        "questionTriggers": {
            "any": [
                "투자 분석",
                "종합 분석",
                "투자할 만",
                "투자 포인트",
                "투자논지",
                "투자 논지",
                "투자 매력",
                "살 만한",
                "매수할 만",
                "기업 분석 보고서",
                "investment memo",
                "investment analysis",
                "investable",
            ]
        },
        "toolNames": ["EngineCall", "DCFValuation", "SensitivityAnalysis", "ScenarioOverlay"],
        "requiredEvidence": [
            "target",
            "asOf",
            "investmentDimensions",
            "assumptions",
            "value",
            "executionRef",
        ],
        "evidenceSchema": {
            "targetKeys": ["stockCode", "target"],
            "periodKeys": ["asOf", "period", "dataAsOf"],
            "valueKeys": ["value", "intrinsic", "current", "upside"],
            "basisKeys": ["decisionStatus", "evidenceStrength", "dimensions", "assumptions"],
        },
        "freshness": {"cadence": "filing_market_event_mixed", "discloseMixedAsOf": True},
        "acceptanceCriteria": {
            "requiredDimensions": [
                "thesis",
                "counterThesis",
                "earningsInflection",
                "industryMacroTransmission",
                "valuation",
                "scenarios",
                "catalysts",
                "risks",
                "monitoringTripwires",
            ],
            "hardCoreDimensions": ["thesis", "counterThesis", "earningsInflection", "valuation", "risks"],
            "minUsableDimensions": 7,
            "statusVocabulary": ["usable", "partial", "blocked", "notObserved"],
        },
        "failurePolicy": {
            "blockedHardCoreMeans": "insufficient",
            "noGenericGapFilling": True,
            "noScenarioProbabilitiesWithoutCalibration": True,
            "noPersonalizedTradeInstruction": True,
        },
        "toolArgPolicy": [
            "report_model_investment_first",
            "fill_only_missing_decision_dimensions",
            "catalyst_requires_event_timing_impact_and_invalidation",
            "scenario_driver_differences_required",
            "mixed_as_of_must_be_disclosed",
        ],
        "priority": 130,
    },
    "Company.panel": {
        "contractId": "company.statement_fact",
        "capabilityRefs": ["Company.panel"],
        "tool": "EngineCall",
        "questionTypes": ["statement_fact"],
        "questionTriggers": {
            "any": [
                "매출",
                "영업이익",
                "순이익",
                "자산",
                "부채",
                "자본",
                "재무제표",
                "현금흐름",
                "금액",
                "revenue",
                "operating profit",
                "net income",
                "assets",
                "liabilities",
                "cash flow",
            ]
        },
        "toolNames": ["EngineCall"],
        "requiredEvidence": ["target", "metric", "period", "value"],
        "evidenceSchema": {
            "targetKeys": ["stockCode", "target", "code"],
            "metricKeys": ["metric", "snakeId", "item"],
            "periodKeys": ["period", "latestPeriod", "periods"],
            "valueKeys": ["value", "values"],
        },
        "freshness": {"cadence": "filing_date", "discloseMixedAsOf": True},
        "priority": 100,
    },
    "analysis.가치평가": {
        "contractId": "company.valuation",
        "capabilityRefs": ["analysis.가치평가", "Company.analysis", "Company.panel"],
        "tool": "EngineCall",
        "questionTypes": ["valuation"],
        "questionTriggers": {"any": ["가치평가", "밸류에이션", "적정가", "목표가", "dcf", "valuation", "fair value"]},
        "toolNames": ["EngineCall", "DCFValuation", "SensitivityAnalysis"],
        "requiredEvidence": ["target", "metric", "period", "value", "assumptions"],
        "freshness": {"cadence": "filing_and_market_date", "discloseMixedAsOf": True},
        "priority": 94,
    },
    "industry": {
        "contractId": "company.industry_context",
        "capabilityRefs": ["industry", "Company.industry"],
        "tool": "EngineCall",
        "questionTypes": ["industry_context"],
        "questionTriggers": {"any": ["산업", "업종", "밸류체인", "경쟁구도", "피어", "industry", "sector", "peer"]},
        "toolNames": ["EngineCall"],
        "requiredEvidence": ["target", "industry", "basis"],
        "priority": 91,
    },
    "macro": {
        "contractId": "macro.context",
        "capabilityRefs": ["macro", "Company.macro", "gather.macro"],
        "tool": "EngineCall",
        "questionTypes": ["macro_context"],
        "questionTriggers": {
            "any": ["금리", "환율", "물가", "경기", "거시", "매크로", "rate", "fx", "macro", "inflation"]
        },
        "toolNames": ["EngineCall", "ScenarioOverlay"],
        "requiredEvidence": ["metric", "period", "value", "asOf"],
        "freshness": {"cadence": "mixed", "discloseMixedAsOf": True},
        "priority": 90,
    },
    "credit": {
        "contractId": "company.credit_context",
        "capabilityRefs": ["credit", "Company.credit", "Company.panel"],
        "tool": "EngineCall",
        "questionTypes": ["credit_context"],
        "questionTriggers": {
            "any": ["신용", "부도", "상환", "유동성", "차입", "credit", "default", "liquidity", "leverage"]
        },
        "toolNames": ["EngineCall", "CreditScorecard"],
        "requiredEvidence": ["target", "metric", "period", "value"],
        "priority": 90,
    },
    "quant": {
        "contractId": "company.quant_context",
        "capabilityRefs": ["quant", "Company.quant", "gather.price"],
        "tool": "EngineCall",
        "questionTypes": ["quant_context"],
        "questionTriggers": {
            "any": [
                "주가",
                "수익률",
                "모멘텀",
                "변동성",
                "팩터",
                "백테스트",
                "price",
                "return",
                "momentum",
                "factor",
                "backtest",
            ]
        },
        "toolNames": ["EngineCall"],
        "requiredEvidence": ["target", "metric", "period", "value", "asOf"],
        "freshness": {"cadence": "market_date"},
        "priority": 88,
    },
    "simulate": {
        "contractId": "scenario.simulation",
        "capabilityRefs": ["simulate", "Company.simulate", "macro.scenario"],
        "tool": "EngineCall",
        "questionTypes": ["scenario"],
        "questionTriggers": {
            "any": ["시나리오", "충격", "스트레스", "오르면", "내리면", "scenario", "shock", "stress", "what if"]
        },
        "toolNames": ["EngineCall", "ScenarioOverlay", "ScenarioCompareN"],
        "requiredEvidence": ["target", "period", "assumptions", "value", "executionRef"],
        "priority": 92,
    },
}


__all__ = [
    "CANONICAL_AXIS_ENGINES",
    "CANONICAL_COMPANY_CAPABILITY_REFS",
    "CANONICAL_DATA_HUB_CAPABILITY_REFS",
    "CANONICAL_TOP_LEVEL_CAPABILITY_REFS",
    "ENGINE_QUESTION_CONTRACTS",
    "canonicalReplacementRefs",
    "engineCallContract",
    "executionGuide",
    "isEngineCallableRef",
]
