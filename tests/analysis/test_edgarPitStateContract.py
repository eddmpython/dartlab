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


def makeFilingWithoutOperatingIncome(
    *,
    componentTags: tuple[tuple[str, float], ...],
    componentAccession: str = "fixed",
) -> pl.DataFrame:
    """`OperatingIncomeLoss` 없이 영업이익 구성요소만 태깅한 filing을 만든다."""

    frame = makeFiling().filter(pl.col("tag") != "OperatingIncomeLoss")
    fiscalEnd = date(2024, 12, 31)
    rows = []
    for lag in range(3, -1, -1):
        quarterEnd = fiscalEnd - timedelta(days=91 * lag)
        quarterStart = quarterEnd - timedelta(days=89)
        for tag, value in componentTags:
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
                    "accn": componentAccession,
                }
            )
    return pl.concat([frame, pl.DataFrame(rows)], how="vertical")


def testOperatingProfitIsDerivedFromGrossProfitMinusOperatingExpenses() -> None:
    """소계 태그가 없어도 같은 접수의 구성요소로 영업이익을 유도한다."""

    facts = makeFilingWithoutOperatingIncome(
        componentTags=(("GrossProfit", 35.0), ("OperatingExpenses", 15.0)),
    )
    compiled = owner.compileEdgarFinancialState(facts, knowledgeAsOf="20250228")

    assert compiled.state.revenue == 400.0
    assert compiled.state.operatingMargin == pytest.approx(0.2)
    operatingEvidence = [item for item in compiled.evidence if item.conceptId == "operatingProfitQuarter"]
    assert operatingEvidence
    assert all(item.status == "derived" for item in operatingEvidence)
    assert all(item.tag == "GrossProfit-OperatingExpenses" for item in operatingEvidence)


def testOperatingProfitIsDerivedFromRevenueMinusTotalCosts() -> None:
    """매출총이익이 없으면 매출에서 총비용을 빼는 두 번째 유도로 넘어간다."""

    facts = makeFilingWithoutOperatingIncome(
        componentTags=(("CostsAndExpenses", 80.0),),
    )
    compiled = owner.compileEdgarFinancialState(facts, knowledgeAsOf="20250228")

    assert compiled.state.operatingMargin == pytest.approx(0.2)
    operatingEvidence = [item for item in compiled.evidence if item.conceptId == "operatingProfitQuarter"]
    assert all(item.status == "derived" for item in operatingEvidence)


def testDerivationRefusesComponentsFromAnotherAccession() -> None:
    """서로 다른 접수의 구성요소는 섞지 않는다. 유도 없이 실패해야 한다."""

    facts = makeFilingWithoutOperatingIncome(
        componentTags=(("GrossProfit", 35.0), ("OperatingExpenses", 15.0)),
        componentAccession="other-accession",
    )
    with pytest.raises(owner.EdgarStateError):
        owner.compileEdgarFinancialState(facts, knowledgeAsOf="20250228")


def testLineageAccessionsTreatObservedAndSameAccessionDerivationAsOneFiling() -> None:
    """관측 하나와 같은 접수 안의 구성요소 유도는 한 filing lineage 다."""

    observed = owner.FactEvidence(
        conceptId="revenueQuarter",
        value=100.0,
        unit="USD",
        currency="USD",
        kind="flowQuarter",
        fiscalStart="20241001",
        fiscalEnd="20241231",
        filedAt="20250130",
        accession="acc-1",
        form="10-Q",
        tag="Revenues",
        status="observed",
    )
    derived = owner.FactEvidence(
        conceptId="operatingProfitQuarter",
        value=20.0,
        unit="USD",
        currency="USD",
        kind="flowQuarter",
        fiscalStart="20241001",
        fiscalEnd="20241231",
        filedAt="20250130",
        accession="acc-1",
        form="10-Q",
        tag="GrossProfit-OperatingExpenses",
        status="derived",
        derivation="gross profit minus operating expenses in one accession",
        derivationInputs=(
            "acc-1|GrossProfit|20241001|20241231",
            "acc-1|OperatingExpenses|20241001|20241231",
        ),
    )

    assert owner._lineageAccessions(observed) == owner._lineageAccessions(derived)

    foreign = owner.FactEvidence(**{**asdict(derived), "derivationInputs": ("acc-2|GrossProfit|20241001|20241231",)})
    assert owner._lineageAccessions(observed) != owner._lineageAccessions(foreign)


def testMissingComponentIsImputedAndAbsorbedByResidualPlug() -> None:
    """재고 미태깅은 결손이 아니라 세분성 부족이다. 항등식은 그대로 닫힌다."""

    facts = makeFiling().filter(pl.col("tag") != "InventoryNet")
    compiled = owner.compileEdgarFinancialState(facts, knowledgeAsOf="20250228")

    assert compiled.state.inventories == 0.0
    assert compiled.state.equity == 40.0
    assert any(item.startswith("imputedZeroComponents:") for item in compiled.warnings)
    assert "inventories" in next(item for item in compiled.warnings if item.startswith("imputedZeroComponents:"))
    # 미태깅 재고 5.0 은 사라지지 않고 잔차 플러그로 이동한다.
    baseline = owner.compileEdgarFinancialState(makeFiling(), knowledgeAsOf="20250228")
    assert compiled.state.otherNetAssets == pytest.approx(baseline.state.otherNetAssets + 5.0)


def testDebtFreeCompanyIsNotAFailure() -> None:
    """이자부부채 태그가 하나도 없는 회사는 실패가 아니라 무차입이다."""

    facts = makeFiling().filter(~pl.col("tag").is_in(["LongTermDebtCurrent", "LongTermDebtNoncurrent"]))
    compiled = owner.compileEdgarFinancialState(facts, knowledgeAsOf="20250228")

    assert compiled.state.debt == 0.0
    assert "totalDebt" in next(item for item in compiled.warnings if item.startswith("imputedZeroComponents:"))
    debtEvidence = next(item for item in compiled.evidence if item.conceptId == "totalDebt")
    assert debtEvidence.derivation == "no interest-bearing debt tagged in this accession"


def testAnchorConceptsAreStillRequired() -> None:
    """자산총계, 부채총계, 자본은 임퓨트 대상이 아니다."""

    for anchorTag in ("Assets", "Liabilities", "StockholdersEquity"):
        facts = makeFiling().filter(pl.col("tag") != anchorTag)
        with pytest.raises(owner.EdgarStateError):
            owner.compileEdgarFinancialState(facts, knowledgeAsOf="20250228")


def testNoncontrollingInterestClosesTheBalanceIdentity() -> None:
    """지배주주 자본만 태깅되면 비지배지분을 더해야 항등식이 닫힌다."""

    facts = makeFiling().with_columns(
        pl.when(pl.col("tag") == "Liabilities").then(pl.lit(55.0)).otherwise(pl.col("val")).alias("val")
    )
    nci = facts.filter(pl.col("tag") == "StockholdersEquity").with_columns(
        pl.lit("MinorityInterest").alias("tag"),
        pl.lit(5.0).alias("val"),
    )
    compiled = owner.compileEdgarFinancialState(pl.concat([facts, nci]), knowledgeAsOf="20250228")

    assert compiled.state.equity == 45.0
    equityEvidence = next(item for item in compiled.evidence if item.conceptId == "equityIncludingNci")
    assert equityEvidence.status == "derived"
    assert equityEvidence.tag == "StockholdersEquity+MinorityInterest"


def testStockCandidateTraversalPrefersTheFilingThatAlsoHasFlow() -> None:
    """대차만 있는 최신 filing 때문에 흐름 있는 직전 filing 을 놓치지 않는다."""

    base = makeFiling()
    newerStockOnly = base.filter(pl.col("start").is_null()).with_columns(
        pl.lit("newer").alias("accn"),
        pl.lit("2025-04-30").alias("filed"),
        pl.lit("2025-03-31").alias("end"),
    )
    compiled = owner.compileEdgarFinancialState(
        pl.concat([base, newerStockOnly]),
        knowledgeAsOf="20250501",
    )

    assert compiled.fiscalThrough == "20241231"
    assert {item.accession for item in compiled.evidence if item.kind == "stock"} == {"fixed"}


def makeStockOnlyCandidates(accessionCount: int) -> pl.DataFrame:
    """흐름 없는 대차 접수를 여러 개 얹어 후보 순회를 강제한다.

    ``makeFiling`` 의 대차 행만 복제해 접수, 접수일, 기간말만 바꾼다. 흐름이 없으므로
    어떤 추가 접수도 상태를 세우지 못하고, 컴파일러는 원본 접수까지 전부 훑는다.
    """

    base = makeFiling()
    stockRows = base.filter(pl.col("start").is_null())
    frames = [base]
    for index in range(accessionCount):
        endDate = date(2025, 3, 31) + timedelta(days=91 * index)
        frames.append(
            stockRows.with_columns(
                pl.lit(f"extra{index}").alias("accn"),
                pl.lit((endDate + timedelta(days=30)).isoformat()).alias("filed"),
                pl.lit(endDate.isoformat()).alias("end"),
            )
        )
    return pl.concat(frames)


def testStockCandidateWalkDoesNotReenterPolarsPerCandidate() -> None:
    """후보 접수가 늘어도 대차 선택이 Polars plan 을 다시 만들지 않아야 한다.

    ``testQuarterEvidenceUsesOneIndexedPolarsFilterPass`` 가 흐름 경로에 세운 규칙과
    같다. 접수 하나의 대차 행은 수십 줄이라, 태그마다 ``filter`` 를 부르면 비용이
    데이터가 아니라 Polars 호출 고정비로 결정되고 후보 수에 곱해진다.
    """

    def walk(accessionCount: int) -> tuple[int, int]:
        """후보를 전부 소진하며 Polars ``filter`` 호출 수와 후보 수를 잰다."""
        pit = owner._normalize(makeStockOnlyCandidates(accessionCount), "20400101")
        originalFilter = pl.DataFrame.filter
        calls = 0

        def countedFilter(frame, *predicates, **constraints):
            """DataFrame.filter 호출을 세고 원본으로 위임한다."""
            nonlocal calls
            calls += 1
            return originalFilter(frame, *predicates, **constraints)

        pl.DataFrame.filter = countedFilter
        try:
            candidates = list(owner._stockCandidates(pit))
        finally:
            pl.DataFrame.filter = originalFilter
        return calls, len(candidates)

    fewCalls, fewCandidates = walk(4)
    manyCalls, manyCandidates = walk(40)

    assert (fewCandidates, manyCandidates) == (5, 41)
    assert fewCalls == manyCalls == 1


def testManyStockCandidatesStillSelectTheFilingThatHasFlow() -> None:
    """색인 경로도 흐름 있는 접수를 그대로 고르고 값을 바꾸지 않는다."""

    compiled = owner.compileEdgarFinancialState(
        makeStockOnlyCandidates(40),
        knowledgeAsOf="20400101",
    )
    reference = owner.compileEdgarFinancialState(makeFiling(), knowledgeAsOf="20250228")

    assert compiled.fiscalThrough == "20241231"
    assert {item.accession for item in compiled.evidence if item.kind == "stock"} == {"fixed"}
    assert compiled.state == reference.state
    assert compiled.warnings == ("latestIncompleteFiling:20341218",)


def testFlowCompilerRunsOncePerFiscalEndNotPerAccession() -> None:
    """같은 기간말을 공유하는 접수가 여럿이어도 흐름 컴파일은 기간말당 한 번이다.

    후보는 접수 단위라 정정 공시가 쌓이면 같은 기간말이 반복된다. 흐름 컴파일은
    ``pit`` 과 기간말만 읽으므로 접수마다 다시 부르면 같은 결과를 다시 계산한다.
    """

    base = makeFiling()
    stockRows = base.filter(pl.col("start").is_null())
    restatements = [
        stockRows.with_columns(
            pl.lit(f"restated{index}").alias("accn"),
            pl.lit(f"2025-0{index + 2}-15").alias("filed"),
        )
        for index in range(3)
    ]
    pit = owner._normalize(pl.concat([base, *restatements]), "20250601")
    requested: list[str] = []

    def countingCompiler(_pit: pl.DataFrame, fiscalThrough: str) -> tuple[()]:
        """호출된 기간말을 기록하고 흐름 결손으로 실패한다."""
        requested.append(fiscalThrough)
        raise owner.EdgarStateError("no flow for this fiscal end")

    assert len(list(owner._stockCandidates(pit))) == 4

    with pytest.raises(owner.EdgarStateError, match="no flow for this fiscal end"):
        owner._compileStockWithFlow(pit, countingCompiler)

    assert requested == ["20241231"]
