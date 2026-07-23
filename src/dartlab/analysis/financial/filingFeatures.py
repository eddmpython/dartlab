"""EDGAR filing evidence를 lower-owner plain feature envelope로 변환한다."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from hashlib import sha256
from typing import Any

import polars as pl

from dartlab.analysis.financial.edgarPitState import (
    CompiledQuarterlyFinancialState,
    compileEdgarQuarterlyFinancialState,
)

EDGAR_FINANCIAL_FEATURE_NORMALIZATION_HASH = sha256(b"dartlab.edgar-quarterly-financial-state-adapter.v1").hexdigest()


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


def _dateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")
    if len(text) != 8 or not text.isdigit():
        raise ValueError(f"invalid {label}: {value}")
    try:
        date(int(text[:4]), int(text[4:6]), int(text[6:8]))
    except ValueError as error:
        raise ValueError(f"invalid {label}: {value}") from error
    return text


def _canonicalHash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


def _sourceRefs(compiled: CompiledQuarterlyFinancialState) -> tuple[str, ...]:
    refs = set()
    for item in compiled.evidence:
        refs.add(f"{item.accession}|{item.tag}|{item.fiscalStart}|{item.fiscalEnd}|{item.status}")
        refs.update(item.derivationInputs)
    return tuple(sorted(refs))


def _stableEvidencePayload(compiled: CompiledQuarterlyFinancialState) -> dict[str, Any]:
    """Query cutoff을 제외하고 값, 선택 evidence, 의미만 revision identity에 넣는다."""

    return {
        "schemaVersion": "edgar-quarterly-financial-evidence-v1",
        "fiscalThrough": compiled.fiscalThrough,
        "reportingCurrency": compiled.reportingCurrency,
        "frequency": compiled.frequency,
        "values": {
            item.variableId: float(getattr(compiled.state, item.fieldName)) for item in EDGAR_FINANCIAL_FEATURE_MAPPINGS
        },
        "evidence": tuple(asdict(item) for item in compiled.evidence),
        "normalizationRuleHash": EDGAR_FINANCIAL_FEATURE_NORMALIZATION_HASH,
    }


def _featureSpecs() -> tuple[dict[str, Any], ...]:
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
        for item in EDGAR_FINANCIAL_FEATURE_MAPPINGS
    )


def buildEdgarFinancialFeatureInput(
    facts: pl.DataFrame,
    *,
    entityId: str,
    knownAt: str,
    validAt: str | None = None,
) -> dict[str, Any]:
    """EDGAR companyfacts를 cutoff-stable plain feature envelope로 만든다.

    Args:
        facts: 한 회사의 SEC companyfacts table.
        entityId: ``US:TICKER`` 형태의 canonical entity identity.
        knownAt: 소비자가 허용하는 filing knowledge cutoff.
        validAt: 선택 가능한 fiscal event cutoff. 생략하면 knownAt 시점의 최신 분기.

    Returns:
        Data Workbench가 상위 계층에서 검증할 ``feature-observation-input-v1`` mapping.

    Raises:
        ValueError: Entity, cutoff, fact schema 또는 coherent state가 잘못된 경우.

    Example:
        ``payload = buildEdgarFinancialFeatureInput(facts, entityId="US:AAPL", knownAt="20250201")``
    """

    if not entityId.startswith("US:") or len(entityId.partition(":")[2]) == 0:
        raise ValueError("EDGAR feature entityId는 US:ENTITY 형식이어야 합니다")
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
    compiled = compileEdgarQuarterlyFinancialState(selectedFacts, knowledgeAsOf=cutoff)
    availableAt = max(_dateText(item.filedAt, "filedAt") for item in compiled.evidence)
    stablePayload = _stableEvidencePayload(compiled)
    evidenceHash = _canonicalHash(stablePayload)
    sourceRefs = _sourceRefs(compiled)
    vintage = {
        "artifactKind": "edgarCompiledFinancialEvidence",
        "provider": "edgar",
        "artifactId": f"{entityId}:{compiled.fiscalThrough}:{evidenceHash}",
        "artifactHash": evidenceHash,
        "payloadHash": evidenceHash,
        "knowledgeAsOf": availableAt,
        "availableAt": availableAt,
        "revisionPolicy": "latestRetained",
        "coverage": "periodOnly",
        "fiscalThrough": compiled.fiscalThrough,
        "contractHash": EDGAR_FINANCIAL_FEATURE_NORMALIZATION_HASH,
        "sourceRefs": sourceRefs,
    }
    observations = tuple(
        {
            "providerId": "edgar",
            "datasetId": "quarterly-financial",
            "entityId": entityId,
            "signalId": item.variableId,
            "value": float(getattr(compiled.state, item.fieldName)),
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
            "normalizationRuleHash": EDGAR_FINANCIAL_FEATURE_NORMALIZATION_HASH,
        }
        for item in EDGAR_FINANCIAL_FEATURE_MAPPINGS
    )
    return {
        "schemaVersion": "feature-observation-input-v1",
        "specs": _featureSpecs(),
        "observations": observations,
    }


__all__ = [
    "EDGAR_FINANCIAL_FEATURE_MAPPINGS",
    "EDGAR_FINANCIAL_FEATURE_NORMALIZATION_HASH",
    "EdgarFinancialFeatureMapping",
    "buildEdgarFinancialFeatureInput",
]
