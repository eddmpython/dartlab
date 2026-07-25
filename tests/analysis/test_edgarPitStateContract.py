"""Owner and compatibility-contract tests for EDGAR point-in-time state compilation."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, timedelta
from hashlib import sha256

import polars as pl
import pytest

from dartlab.analysis.financial import edgarPitState as owner
from dartlab.simulate import edgarPitState as compatibility


def makeFiling() -> pl.DataFrame:
    """Build one coherent quarterly filing with four standalone flow periods."""

    stock = {
        "CashAndCashEquivalentsAtCarryingValue": 10.0,
        "AccountsReceivableNetCurrent": 20.0,
        "InventoryNet": 5.0,
        "AccountsPayableCurrent": 15.0,
        "PropertyPlantAndEquipmentNet": 30.0,
        "Assets": 100.0,
        "Liabilities": 60.0,
        "StockholdersEquity": 40.0,
        "LongTermDebtCurrent": 8.0,
        "LongTermDebtNoncurrent": 12.0,
    }
    rows = [
        {
            "namespace": "us-gaap",
            "tag": tag,
            "unit": "USD",
            "val": value,
            "form": "10-Q",
            "filed": "2025-01-30",
            "start": None,
            "end": "2024-12-31",
            "accn": "fixed",
        }
        for tag, value in stock.items()
    ]
    fiscalEnd = date(2024, 12, 31)
    for lag in range(3, -1, -1):
        quarterEnd = fiscalEnd - timedelta(days=91 * lag)
        quarterStart = quarterEnd - timedelta(days=89)
        for tag, value in (
            ("RevenueFromContractWithCustomerExcludingAssessedTax", 100.0),
            ("OperatingIncomeLoss", 20.0),
        ):
            rows.append(
                {
                    "namespace": "us-gaap",
                    "tag": tag,
                    "unit": "USD",
                    "val": value,
                    "form": "10-Q",
                    "filed": "2025-01-30",
                    "start": quarterStart.isoformat(),
                    "end": quarterEnd.isoformat(),
                    "accn": "fixed",
                }
            )
    return pl.DataFrame(rows)


def testCompatibilityShimReexportsOwnerObjects() -> None:
    """The legacy module must expose the exact owner-layer objects."""

    names = (
        "CompiledFinancialState",
        "CompiledQuarterlyFinancialState",
        "EdgarStateError",
        "FactEvidence",
        "QuarterFlow",
        "compileEdgarFinancialState",
        "compileEdgarQuarterlyFinancialState",
    )
    for name in names:
        assert getattr(compatibility, name) is getattr(owner, name)


def testOwnerKeepsFixedPointInTimeBehavior() -> None:
    """The owner compiler must preserve the established reduced-state result."""

    compiled = owner.compileEdgarFinancialState(makeFiling(), knowledgeAsOf="20250228")
    assert compiled.state.cash == 10.0
    assert compiled.state.debt == 20.0
    assert compiled.state.revenue == 400.0
    assert compiled.state.operatingMargin == pytest.approx(0.2)
    assert compiled.fiscalThrough == "20241231"
    assert compiled.revisionPolicy == "asKnown"


def testFlowCompilerSucceedsWithoutStockFacts() -> None:
    """Flow-only 요청은 stock 결손과 무관하게 동일 filing lineage를 컴파일한다."""

    facts = makeFiling().filter(pl.col("start").is_not_null())
    compiled = owner.compileEdgarQuarterlyFlowState(
        facts,
        knowledgeAsOf="20250228",
    )

    assert compiled.quarterRevenue == 100.0
    assert compiled.quarterOperatingProfit == 20.0
    assert compiled.ttmRevenue == 400.0
    assert compiled.fiscalThrough == "20241231"
    assert len(compiled.evidence) == 8


def testRevenueCompilerSucceedsWithoutOperatingProfitOrStockFacts() -> None:
    facts = makeFiling().filter(
        (pl.col("start").is_not_null()) & (pl.col("tag") == "RevenueFromContractWithCustomerExcludingAssessedTax")
    )

    compiled = owner.compileEdgarQuarterlyRevenueState(
        facts,
        knowledgeAsOf="20250228",
    )

    assert compiled.quarterRevenue == 100.0
    assert compiled.ttmRevenue == 400.0
    assert compiled.fiscalThrough == "20241231"
    assert len(compiled.evidence) == 4


def testFlowCompilerFallsBackOnlyToLatestCoherentFourQuarterWindow() -> None:
    latestRows = []
    for tag, accession in (
        ("RevenueFromContractWithCustomerExcludingAssessedTax", "latest-revenue"),
        ("OperatingIncomeLoss", "latest-operating"),
    ):
        latestRows.append(
            {
                "namespace": "us-gaap",
                "tag": tag,
                "unit": "USD",
                "val": 100.0,
                "form": "10-Q",
                "filed": "2025-04-30",
                "start": "2025-01-02",
                "end": "2025-04-01",
                "accn": accession,
            }
        )
    facts = pl.concat(
        (
            makeFiling().filter(pl.col("start").is_not_null()),
            pl.DataFrame(latestRows),
        )
    )

    compiled = owner.compileEdgarQuarterlyFlowState(
        facts,
        knowledgeAsOf="20250501",
    )

    assert compiled.fiscalThrough == "20241231"
    assert compiled.warnings == ("latestIncompleteFlow:20250401",)
    with pytest.raises(owner.EdgarStateError, match="share one accession"):
        owner.compileEdgarQuarterlyFlowState(
            facts,
            knowledgeAsOf="20250501",
            fiscalThrough="20250401",
        )


def testOwnerCompilerOutputMatchesCanonicalGolden() -> None:
    """최적화된 selector가 직렬화 evidence 필드와 순서를 모두 보존해야 한다."""

    facts = makeFiling()
    annual = owner.compileEdgarFinancialState(facts, knowledgeAsOf="20250228")
    quarterly = owner.compileEdgarQuarterlyFinancialState(facts, knowledgeAsOf="20250228")

    def seal(value) -> str:
        raw = json.dumps(
            asdict(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return sha256(raw).hexdigest()

    assert seal(annual) == "27f8aa35e476c5db672efdeba89f0c8d0629e6c0d0cc57d450d61596f883378b"
    assert seal(quarterly) == "7ea473968bfb2d9ca2a3e35639a43ba0bfda9828137654bf238500017d1af753"


def testQuarterEvidenceUsesOneIndexedPolarsFilterPass(monkeypatch: pytest.MonkeyPatch) -> None:
    """분기 선택이 기간과 태그마다 Polars plan을 다시 만들지 않아야 한다."""

    pit = owner._normalize(makeFiling(), "20250228")
    originalFilter = pl.DataFrame.filter
    filterCalls = 0

    def countedFilter(frame, *predicates, **constraints):
        nonlocal filterCalls
        filterCalls += 1
        return originalFilter(frame, *predicates, **constraints)

    monkeypatch.setattr(pl.DataFrame, "filter", countedFilter)
    evidence = owner._quarterEvidence(
        pit,
        "revenueQuarter",
        owner._REVENUE_TAGS,
        fiscalThrough="20241231",
    )

    assert filterCalls == 1
    assert tuple(evidence) == ("20241231", "20241001", "20240702", "20240402")


@pytest.mark.parametrize(
    ("column", "value"),
    (
        ("filed", "2025-01-30-extra"),
        ("end", "2024-02-31"),
    ),
)
def testOwnerRejectsMalformedAndImpossibleFactDates(column: str, value: str) -> None:
    """PIT selection must not truncate or normalize invalid source dates."""

    facts = makeFiling().with_columns(pl.lit(value).alias(column))
    with pytest.raises(owner.EdgarStateError, match="EDGAR facts contain invalid dates"):
        owner.compileEdgarFinancialState(facts, knowledgeAsOf="20250228")

    with pytest.raises(owner.EdgarStateError, match="invalid date"):
        owner.compileEdgarFinancialState(makeFiling(), knowledgeAsOf="20250231")
