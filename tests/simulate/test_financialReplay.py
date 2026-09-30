"""Financial replay integrates first-filing states, observed actions and the actual tournament."""

from dataclasses import replace
from pathlib import Path

import polars as pl
import pytest

from dartlab.simulate.financialReplay import REPLAY_METRICS, buildEdgarFinancialReplay
from dartlab.simulate.hindcast import WorldModelTournamentSpec, runWorldModelTournament


def replayFacts() -> pl.DataFrame:
    periods = (
        ("2024-01-01", "2024-03-31", "2024-04-30"),
        ("2024-04-01", "2024-06-30", "2024-07-30"),
        ("2024-07-01", "2024-09-30", "2024-10-30"),
        ("2024-10-01", "2024-12-31", "2025-01-30"),
        ("2025-01-01", "2025-03-31", "2025-04-30"),
        ("2025-04-01", "2025-06-30", "2025-07-30"),
    )
    stocks = {
        "CashAndCashEquivalentsAtCarryingValue": 20.0,
        "AccountsReceivableNetCurrent": 10.0,
        "InventoryNet": 5.0,
        "AccountsPayableCurrent": 10.0,
        "PropertyPlantAndEquipmentNet": 50.0,
        "Assets": 120.0,
        "Liabilities": 70.0,
        "StockholdersEquity": 50.0,
        "LongTermDebtCurrent": 10.0,
        "LongTermDebtNoncurrent": 20.0,
    }
    flows = {
        "RevenueFromContractWithCustomerExcludingAssessedTax": 100.0,
        "OperatingIncomeLoss": 20.0,
        "DepreciationDepletionAndAmortization": 2.0,
        "IncomeTaxExpenseBenefit": 3.0,
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest": 15.0,
        "NetIncomeLoss": 12.0,
        "PaymentsOfDividends": 2.0,
        "InterestExpense": 1.0,
        "PaymentsToAcquirePropertyPlantAndEquipment": 4.0,
        "ProceedsFromIssuanceOfLongTermDebt": 0.0,
        "RepaymentsOfLongTermDebt": 1.0,
        "ProceedsFromRepaymentsOfCommercialPaper": 0.0,
    }
    return pl.DataFrame(
        [
            {
                "namespace": "us-gaap",
                "tag": tag,
                "unit": "USD",
                "val": value,
                "form": "10-Q",
                "filed": filed,
                "start": start if isFlow else None,
                "end": end,
                "accn": filed,
            }
            for start, end, filed in periods
            for isFlow, values in ((False, stocks), (True, flows))
            for tag, value in values.items()
        ]
    )


def tournament(replay):
    return runWorldModelTournament(
        replay.models,
        replay.episodes,
        WorldModelTournamentSpec("20250801", REPLAY_METRICS, dict.fromkeys(REPLAY_METRICS, 1.0), "carry", 40),
    )


@pytest.mark.unit
def testFinancialReplayRunsExistingTournamentWithHonestCoverage() -> None:
    replay = buildEdgarFinancialReplay(replayFacts(), entityId="TEST", knowledgeAsOf="20250801")
    assert len(replay.episodes) == 2 and replay.census.height == 6
    assert replay.census.filter(pl.col("status") == "stateGap").height == 3
    episode = replay.episodes[0]
    assert episode.initialState.values["revenue"] == 1
    assert episode.observedPolicy.actionsByStep[0] == {
        "capexRatio": 0.04,
        "inventoryRatio": 0.05,
        "borrow": 0.0,
        "repay": 0.01,
    }
    assert episode.realizedPath.historyStatus == "realizedOutcome"
    assert episode.originAsOf < episode.outcomeAvailableAt
    assert set(replay.evidence["role"]) == {"initial", "parameter", "action", "outcome"}
    report = tournament(replay)
    assert report.episodeCount == 2 and report.modelCount == 2
    assert report.selectionStatus == "insufficientEvidence" and not report.selectedModelId
    assert report.admissionStatus == "notAdmitted"


@pytest.mark.unit
def testLaterFilingsCannotChangeOriginParametersOrInitialState() -> None:
    facts = replayFacts()
    first = buildEdgarFinancialReplay(facts, entityId="TEST", knowledgeAsOf="20250801")
    # A later filing changes a depreciation fact used only at a later origin.
    changed = facts.with_columns(
        pl.when((pl.col("filed") == "2025-04-30") & (pl.col("tag") == "DepreciationDepletionAndAmortization"))
        .then(4.0)
        .otherwise(pl.col("val"))
        .alias("val")
    )
    second = buildEdgarFinancialReplay(changed, entityId="TEST", knowledgeAsOf="20250801")
    assert first.episodes[0].initialState == second.episodes[0].initialState
    assert first.episodes[0].realizedPath.parameterDraws == second.episodes[0].realizedPath.parameterDraws
    assert first.episodes[1].realizedPath.parameterDraws != second.episodes[1].realizedPath.parameterDraws
    cutoff = buildEdgarFinancialReplay(facts, entityId="TEST", knowledgeAsOf="20250501")
    assert len(cutoff.episodes) == 1
    assert cutoff.episodes[0] == first.episodes[0]


@pytest.mark.unit
def testMissingActionsStayCensusGapsAndReportedZerosRemainUsable() -> None:
    facts = replayFacts().filter(
        ~((pl.col("filed") == "2025-04-30") & (pl.col("tag") == "ProceedsFromIssuanceOfLongTermDebt"))
    )
    replay = buildEdgarFinancialReplay(facts, entityId="TEST", knowledgeAsOf="20250801")
    assert len(replay.episodes) == 1
    assert "missing quarter flows: termBorrow" in replay.census["reason"].to_list()


@pytest.mark.unit
def testEpisodeHashBindsFinancialParameters() -> None:
    replay = buildEdgarFinancialReplay(replayFacts(), entityId="TEST", knowledgeAsOf="20250801")
    first = tournament(replay)
    episode = replay.episodes[0]
    updated = replace(
        episode,
        realizedPath=replace(
            episode.realizedPath, parameterDraws={**episode.realizedPath.parameterDraws, "depreciationRate": 0.06}
        ),
    )
    second = tournament(replace(replay, episodes=(updated, *replay.episodes[1:])))
    assert first.episodeHashes[0] != second.episodeHashes[0]
    assert first.tournamentHash != second.tournamentHash


@pytest.mark.unit
def testEmptyReplayKeepsTableSchemas() -> None:
    replay = buildEdgarFinancialReplay(replayFacts(), entityId="TEST", knowledgeAsOf="20240101")
    assert replay.episodes == () and replay.models == ()
    assert replay.census.is_empty() and "status" in replay.census.columns
    assert replay.evidence.is_empty() and "value" in replay.evidence.columns


@pytest.mark.unit
def testNonAdjacentQuarterIsNotReplayed() -> None:
    facts = replayFacts().filter(pl.col("end") != "2025-03-31")
    replay = buildEdgarFinancialReplay(facts, entityId="TEST", knowledgeAsOf="20250801")
    assert not replay.episodes


@pytest.mark.unit
def testMixedCompaniesAreRejected() -> None:
    facts = replayFacts().with_row_index().with_columns((pl.col("index") % 2).cast(pl.String).alias("cik"))
    with pytest.raises(ValueError, match="one company"):
        buildEdgarFinancialReplay(facts, entityId="TEST", knowledgeAsOf="20250801")


@pytest.mark.realData
@pytest.mark.serial
def testAaplFinancialReplayReachesTournament() -> None:
    path = Path("data/edgar/finance/0000320193.parquet")
    if not path.exists():
        pytest.skip("local AAPL companyfacts unavailable")
    replay = buildEdgarFinancialReplay(pl.read_parquet(path), entityId="AAPL", knowledgeAsOf="20230930")
    assert len(replay.episodes) >= 10
    report = runWorldModelTournament(
        replay.models,
        replay.episodes,
        WorldModelTournamentSpec("20230930", REPLAY_METRICS, dict.fromkeys(REPLAY_METRICS, 1.0), "carry", 40),
    )
    assert report.episodeCount == len(replay.episodes) and report.admissionStatus == "notAdmitted"
