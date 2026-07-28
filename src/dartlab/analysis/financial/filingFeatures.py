"""EDGAR filing evidence를 lower-owner plain feature envelope로 변환한다."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any

import polars as pl

from dartlab.analysis.financial._filingEvidence import _dateText, _sourceRefs
from dartlab.analysis.financial.edgarPitState import (
    CompiledQuarterlyFinancialState,
    CompiledQuarterlyFlowState,
    CompiledQuarterlyRevenueState,
    compileEdgarQuarterlyFinancialState,
    compileEdgarQuarterlyFlowState,
    compileEdgarQuarterlyRevenueState,
    flowSelectionRuleDigest,
    stateSelectionRuleDigest,
)

_FINANCIAL_ADAPTER_RULE = b"dartlab.edgar-quarterly-financial-state-adapter.v1"
_FLOW_ADAPTER_RULE = b"dartlab.edgar-quarterly-flow-feature-adapter.v1"

# adapter 버전과 실제 태그 선택 규칙을 함께 결박한다. 태그 우선순위가 바뀌면 같은 원천에서도
# 다른 값이 선택되므로 계약 identity도 반드시 달라져야 한다. adapter 버전 문자열만 쓰면 옛
# 태그 규칙으로 구운 READY generation 과 관측이 현행 계약인 것처럼 통과한다.
EDGAR_FINANCIAL_FEATURE_NORMALIZATION_HASH = sha256(
    _FINANCIAL_ADAPTER_RULE + b"|" + stateSelectionRuleDigest().encode("ascii")
).hexdigest()
EDGAR_FLOW_FEATURE_NORMALIZATION_HASH = sha256(
    _FLOW_ADAPTER_RULE + b"|" + flowSelectionRuleDigest().encode("ascii")
).hexdigest()


@dataclass(frozen=True)
class EdgarFinancialFeatureMapping:
    """EDGAR compiled financial state field와 feature meaning의 owner-local 결합."""

    variableId: str
    fieldName: str
    unit: str
    evidenceRole: str
    timing: str
    transformId: str
    lower: float | None
    upper: float | None


EDGAR_FINANCIAL_FEATURE_MAPPINGS: tuple[EdgarFinancialFeatureMapping, ...] = (
    EdgarFinancialFeatureMapping(
        "financial.revenue",
        "revenue",
        "USD",
        "deterministicDerived",
        "flow",
        "standalone-quarter-flow-v1",
        0.0,
        None,
    ),
    EdgarFinancialFeatureMapping(
        "financial.operatingMargin",
        "operatingMargin",
        "ratio",
        "deterministicDerived",
        "ratio",
        "operating-profit-div-revenue-v1",
        -1.0,
        1.0,
    ),
    EdgarFinancialFeatureMapping(
        "financial.cash",
        "cash",
        "USD",
        "observed",
        "stock",
        "latest-filing-instant-v1",
        0.0,
        None,
    ),
    EdgarFinancialFeatureMapping(
        "financial.debt",
        "debt",
        "USD",
        "deterministicDerived",
        "stock",
        "interest-bearing-debt-normalized-v1",
        0.0,
        None,
    ),
    EdgarFinancialFeatureMapping(
        "financial.receivables",
        "receivables",
        "USD",
        "observed",
        "stock",
        "latest-filing-instant-v1",
        0.0,
        None,
    ),
    EdgarFinancialFeatureMapping(
        "financial.inventories",
        "inventories",
        "USD",
        "observed",
        "stock",
        "latest-filing-instant-v1",
        0.0,
        None,
    ),
    EdgarFinancialFeatureMapping(
        "financial.payables",
        "payables",
        "USD",
        "observed",
        "stock",
        "latest-filing-instant-v1",
        0.0,
        None,
    ),
    EdgarFinancialFeatureMapping(
        "financial.ppe",
        "ppe",
        "USD",
        "observed",
        "stock",
        "latest-filing-instant-v1",
        0.0,
        None,
    ),
    EdgarFinancialFeatureMapping(
        "financial.otherNetAssets",
        "otherNetAssets",
        "USD",
        "deterministicDerived",
        "stock",
        "balance-residual-other-net-assets-v1",
        None,
        None,
    ),
    EdgarFinancialFeatureMapping(
        "financial.equity",
        "equity",
        "USD",
        "observed",
        "stock",
        "latest-filing-instant-v1",
        None,
        None,
    ),
)
_FLOW_ONLY_MEASURES = frozenset(
    {
        "financial.revenue",
        "financial.operatingMargin",
    }
)


def _canonicalHash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


def _mappingValue(
    compiled: (CompiledQuarterlyFinancialState | CompiledQuarterlyFlowState | CompiledQuarterlyRevenueState),
    mapping: EdgarFinancialFeatureMapping,
) -> float:
    if isinstance(compiled, CompiledQuarterlyRevenueState):
        if mapping.variableId == "financial.revenue":
            return float(compiled.quarterRevenue)
        raise ValueError(f"revenue-only compiler가 지원하지 않는 measure입니다: {mapping.variableId}")
    if isinstance(compiled, CompiledQuarterlyFlowState):
        if mapping.variableId == "financial.revenue":
            return float(compiled.quarterRevenue)
        if mapping.variableId == "financial.operatingMargin":
            return float(compiled.quarterOperatingProfit / compiled.quarterRevenue)
        raise ValueError(f"flow-only compiler가 지원하지 않는 measure입니다: {mapping.variableId}")
    return float(getattr(compiled.state, mapping.fieldName))


def _stableEvidencePayload(
    compiled: (CompiledQuarterlyFinancialState | CompiledQuarterlyFlowState | CompiledQuarterlyRevenueState),
    mappings: tuple[EdgarFinancialFeatureMapping, ...],
    *,
    normalizationRuleHash: str,
    flowOnly: bool,
) -> dict[str, Any]:
    """Query cutoff을 제외하고 값, 선택 evidence, 의미만 revision identity에 넣는다."""

    return {
        "schemaVersion": ("edgar-quarterly-flow-evidence-v1" if flowOnly else "edgar-quarterly-financial-evidence-v1"),
        "fiscalThrough": compiled.fiscalThrough,
        "reportingCurrency": compiled.reportingCurrency,
        "frequency": compiled.frequency,
        "values": {item.variableId: _mappingValue(compiled, item) for item in mappings},
        "evidence": tuple(asdict(item) for item in compiled.evidence),
        "normalizationRuleHash": normalizationRuleHash,
    }


def _featureSpecs(
    mappings: tuple[EdgarFinancialFeatureMapping, ...],
) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "variableId": item.variableId,
            "signalId": item.variableId,
            "providerId": "edgar",
            "datasetId": "quarterly-financial",
            "unit": item.unit,
            "role": "observedFeature",
            "evidenceRole": item.evidenceRole,
            "frequency": "quarter",
            "timing": item.timing,
            "transformId": item.transformId,
            "maxStalenessDays": 400,
            "lower": item.lower,
            "upper": item.upper,
        }
        for item in mappings
    )


def _selectedMappings(
    measures: Sequence[str],
) -> tuple[tuple[EdgarFinancialFeatureMapping, ...], bool]:
    if isinstance(measures, (str, bytes)):
        raise TypeError("EDGAR feature measures는 string sequence여야 합니다")
    requested = tuple(measures)
    if any(type(item) is not str or not item or item != item.strip() for item in requested):
        raise ValueError("EDGAR feature measure ID가 유효하지 않습니다")
    if len(requested) != len(set(requested)):
        raise ValueError("EDGAR feature measures에 중복이 있습니다")
    byId = {mapping.variableId: mapping for mapping in EDGAR_FINANCIAL_FEATURE_MAPPINGS}
    unknown = tuple(item for item in requested if item not in byId)
    if unknown:
        raise ValueError(f"EDGAR feature measure가 지원되지 않습니다: {', '.join(unknown)}")
    if not requested:
        return EDGAR_FINANCIAL_FEATURE_MAPPINGS, False
    requestedSet = set(requested)
    mappings = tuple(mapping for mapping in EDGAR_FINANCIAL_FEATURE_MAPPINGS if mapping.variableId in requestedSet)
    return mappings, requestedSet.issubset(_FLOW_ONLY_MEASURES)


def buildEdgarFinancialFeatureInput(
    facts: pl.DataFrame,
    *,
    entityId: str,
    knownAt: str,
    validAt: str | None = None,
    measures: Sequence[str] = (),
) -> dict[str, Any]:
    """EDGAR companyfacts를 cutoff-stable plain feature envelope로 만든다.

    Args:
        facts: 한 회사의 SEC companyfacts table.
        entityId: ``US:TICKER`` 형태의 canonical entity identity.
        knownAt: 소비자가 허용하는 filing knowledge cutoff.
        validAt: 선택 가능한 fiscal event cutoff. 생략하면 knownAt 시점의 최신 분기.
        measures: 생성할 feature ID. 비우면 기존 strict full-state 전체를 생성한다.

    Returns:
        Data Workbench가 상위 계층에서 검증할 ``feature-observation-input-v1`` mapping.

    Raises:
        ValueError: Entity, cutoff, fact schema 또는 coherent state가 잘못된 경우.

    Example:
        ``payload = buildEdgarFinancialFeatureInput(facts, entityId="US:AAPL", knownAt="20250201")``
    """

    if not entityId.startswith("US:") or len(entityId.partition(":")[2]) == 0:
        raise ValueError("EDGAR feature entityId는 US:ENTITY 형식이어야 합니다")
    mappings, flowOnly = _selectedMappings(measures)
    cutoff = _dateText(knownAt, "knownAt")
    selectedFacts = facts
    if validAt is not None:
        valid = _dateText(validAt, "validAt")
        if "end" not in facts.columns:
            raise ValueError("EDGAR facts에 end가 없습니다")
        selectedFacts = facts.filter(
            pl.col("end").is_not_null()
            & (pl.col("end").cast(pl.Utf8).str.replace_all("-", "").str.slice(0, 8) <= valid)
        )
    compiled: CompiledQuarterlyFinancialState | CompiledQuarterlyFlowState | CompiledQuarterlyRevenueState
    if flowOnly:
        if {item.variableId for item in mappings} == {"financial.revenue"}:
            compiled = compileEdgarQuarterlyRevenueState(
                selectedFacts,
                knowledgeAsOf=cutoff,
            )
        else:
            compiled = compileEdgarQuarterlyFlowState(
                selectedFacts,
                knowledgeAsOf=cutoff,
            )
        normalizationRuleHash = EDGAR_FLOW_FEATURE_NORMALIZATION_HASH
    else:
        compiled = compileEdgarQuarterlyFinancialState(
            selectedFacts,
            knowledgeAsOf=cutoff,
        )
        normalizationRuleHash = EDGAR_FINANCIAL_FEATURE_NORMALIZATION_HASH
    availableAt = max(_dateText(item.filedAt, "filedAt") for item in compiled.evidence)
    stablePayload = _stableEvidencePayload(
        compiled,
        mappings,
        normalizationRuleHash=normalizationRuleHash,
        flowOnly=flowOnly,
    )
    evidenceHash = _canonicalHash(stablePayload)
    sourceRefs = _sourceRefs(compiled)
    vintage = {
        "artifactKind": ("edgarCompiledFlowEvidence" if flowOnly else "edgarCompiledFinancialEvidence"),
        "provider": "edgar",
        "artifactId": f"{entityId}:{compiled.fiscalThrough}:{evidenceHash}",
        "artifactHash": evidenceHash,
        "payloadHash": evidenceHash,
        "knowledgeAsOf": availableAt,
        "availableAt": availableAt,
        "revisionPolicy": "latestRetained",
        "coverage": "periodOnly",
        "fiscalThrough": compiled.fiscalThrough,
        "contractHash": normalizationRuleHash,
        "sourceRefs": sourceRefs,
    }
    observations = tuple(
        {
            "providerId": "edgar",
            "datasetId": "quarterly-financial",
            "entityId": entityId,
            "signalId": item.variableId,
            "value": _mappingValue(compiled, item),
            "unit": item.unit,
            "frequency": "quarter",
            "timing": item.timing,
            "transformId": item.transformId,
            "evidenceRole": item.evidenceRole,
            "eventAt": compiled.fiscalThrough,
            "availableAt": availableAt,
            "knowledgeAsOf": availableAt,
            "availabilityPrecision": "date",
            "revisionId": evidenceHash,
            "vintage": vintage,
            "normalizationRuleHash": normalizationRuleHash,
        }
        for item in mappings
    )
    return {
        "schemaVersion": "feature-observation-input-v1",
        "specs": _featureSpecs(mappings),
        "observations": observations,
    }


__all__ = [
    "EDGAR_FINANCIAL_FEATURE_MAPPINGS",
    "EDGAR_FINANCIAL_FEATURE_NORMALIZATION_HASH",
    "EDGAR_FLOW_FEATURE_NORMALIZATION_HASH",
    "EdgarFinancialFeatureMapping",
    "buildEdgarFinancialFeatureInput",
]
