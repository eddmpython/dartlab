"""재예보 시험장 : origin 사전등록·다지평 라벨·fan coverage·actualPath IC·h* 규칙 (순수 유닛).

Covers:
- origins: 비중첩 간격 + 지평 도래분만 (표본 겹침 t 부풀림 차단).
- weeklyLabels horizonDays 일반화 (10거래일 forward).
- fanCurves: 합성 RW 매크로에서 곡선 스키마·coverage 산출 (봉인은 tmp 원장).
- actualPathCurves: 수익 = 베타 x 실현충격 완전 구성 → IC ~ 1 전 지평.
- hStar: 사전등록 규칙 판정 (통과 = 지평+1, 위반 첫 걸음).
"""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import polars as pl
import pytest

from dartlab.simulate import hindcast as hc
from dartlab.simulate.driverPaths import (
    DriverAssumptionSource,
    DriverCard,
    DriverFactorSpec,
    DriverPathAudit,
    DriverPathSet,
    buildDriverPathSet,
    driverFactorsToOperatingSpecs,
)
from dartlab.simulate.operatingBridge import (
    OperatingShockBaseline,
    OperatingTransmissionExposure,
    bridgeOperatingPath,
    sourceFactorContractHash,
)
from dartlab.simulate.operatingWorld import (
    OperatingPrimitive,
    buildOperatingStrategy,
    operatingInputsFromPrimitives,
    runOperatingStrategies,
)
from dartlab.simulate.scenarioComposition import (
    OperatingScenarioCase,
    ScenarioCoefficientBinding,
    scenarioCoefficientExposureContractHash,
)
from dartlab.simulate.vintage import canonicalPayloadHash
from dartlab.simulate.world import (
    LawSpec,
    ScenarioPath,
    StrategySpec,
    VariableSpec,
    WorldModel,
    WorldState,
)


def testOriginsNonOverlapping():
    we = pl.DataFrame({"week": list(range(202601, 202641)), "date": [f"2026{i:02d}01" for i in range(1, 41)]})
    ogs = hc.origins(we, start="20260101", gapWeeks=8, steps=8)
    idx = [we["date"].to_list().index(o) for o in ogs]
    assert all(b - a >= 8 for a, b in zip(idx, idx[1:]))  # 비중첩
    assert all(i + 8 < we.height for i in idx)  # 지평 도래분만


def testWeeklyLabelsHorizonDays():
    from dartlab.simulate import readingScorecard as sc

    days = [f"202601{d:02d}" for d in range(1, 26)]
    rows = [
        {"date": d, "code": "a", "close": 100.0 * (1.01**i), "shares": 1.0, "mktcap": 100.0} for i, d in enumerate(days)
    ] + [{"date": d, "code": "b", "close": 50.0, "shares": 1.0, "mktcap": 50.0} for d in days]
    px = pl.DataFrame(rows)
    we = pl.DataFrame({"week": [202601], "date": [days[4]]})
    lab5 = sc.weeklyLabels(we, px, horizonDays=5)
    lab10 = sc.weeklyLabels(we, px, horizonDays=10)
    assert set(lab10["code"].to_list()) == {"a", "b"}
    a5 = lab5.filter(pl.col("code") == "a")["exRaw"][0]
    a10 = lab10.filter(pl.col("code") == "a")["exRaw"][0]
    assert a10 > a5 > 0  # 지평이 길수록 누적 초과 커짐 (b 평탄 대비)


def _rwMacro(n: int = 300, seedStep: float = 0.01) -> pl.DataFrame:
    # 결정론 유사 RW (사인 합성, 난수 금지)
    import math
    from datetime import date, timedelta

    dates = [(date(2024, 1, 1) + timedelta(days=i)).strftime("%Y%m%d") for i in range(n)]
    oil = [70.0 * math.exp(sum(seedStep * math.sin(j / 5.0) for j in range(i))) for i in range(n)]
    return pl.DataFrame({"date": dates, "oil": oil})


def testFanCurvesSchemaAndCoverage(monkeypatch, tmp_path):
    from dartlab.simulate import table

    macro = _rwMacro(240)
    dates = macro["date"].to_list()
    we = pl.DataFrame({"week": list(range(len(dates[::7]))), "date": dates[::7]})
    monkeypatch.setattr(table, "macroDaily", lambda d=None: macro)
    monkeypatch.setattr(table, "weekCalendar", lambda d=None: (pl.DataFrame(), we))
    curves = hc.fanCurves(start=dates[140], steps=4, gapWeeks=4, baseDir=tmp_path)
    assert curves.columns == ["factor", "h", "cov90", "cov50", "crps", "crpsCarry", "skill", "n"]
    assert curves.height > 0 and curves["h"].max() <= 4
    assert ((curves["cov90"] >= 0) & (curves["cov90"] <= 1)).all()


def testActualPathIcPerfectConstruction(monkeypatch):
    from dartlab.simulate import lattice, readingScorecard, table

    macro = _rwMacro(240)
    dates = macro["date"].to_list()
    we = pl.DataFrame({"week": list(range(len(dates[::7]))), "date": dates[::7]})
    codes = [f"c{i:02d}" for i in range(30)]
    betas = pl.DataFrame(
        {
            "code": codes,
            "rateBeta": [None] * 30,
            "fxBeta": [0.0] * 30,
            "oilBeta": [float(i - 15) for i in range(30)],
            "rate10yBeta": [None] * 30,
        }
    )
    monkeypatch.setattr(table, "macroDaily", lambda d=None: macro)
    monkeypatch.setattr(table, "weekCalendar", lambda d=None: (pl.DataFrame(), we))
    monkeypatch.setattr(table, "dailyPrices", lambda d=None: pl.DataFrame())
    monkeypatch.setattr(table, "macroBetaByCodeWide", lambda asOf, baseDir=None, prices=None: betas)
    monkeypatch.setattr(lattice, "winsorizeBetas", lambda b, q=0.01: b)

    def fakeLabels(weekEnd, px, *, horizonDays=5):
        # 실현 초과 = 베타 x 실현 유가수익 완전 구성 (IC=1 이 정답)
        h = horizonDays // 5
        rows = []
        dlist = weekEnd.sort("week")["date"].to_list()
        for wi, d in enumerate(dlist):
            if wi + h >= len(dlist):
                continue
            cur = macro.filter(pl.col("date") <= d)["oil"].drop_nulls()[-1]
            fut = macro.filter(pl.col("date") <= dlist[wi + h])["oil"].drop_nulls()[-1]
            dv = fut / cur - 1.0
            for i, code in enumerate(codes):
                rows.append(
                    {
                        "code": code,
                        "week": weekEnd.sort("week")["week"].to_list()[wi],
                        "exRaw": (i - 15) * dv,
                        "exNeutral": (i - 15) * dv,
                        "scorable": True,
                        "censored": False,
                    }
                )
        return pl.DataFrame(rows)

    monkeypatch.setattr(readingScorecard, "weeklyLabels", fakeLabels)
    firm = hc.actualPathCurves(start=dates[70], steps=3, gapWeeks=3, minCross=20)
    assert firm.height == 3 and (firm["icMean"] > 0.95).all()  # 완전 구성 = IC ~ 1 전 지평


def testHStarRules():
    fan = pl.DataFrame(
        {
            "factor": ["oil"] * 3,
            "h": [1, 2, 3],
            "cov90": [0.9, 0.85, 0.6],
            "cov50": [0.5] * 3,
            "crps": [1.0] * 3,
            "crpsCarry": [1.0] * 3,
            "skill": [1.0] * 3,
            "n": [10] * 3,
        }
    )
    firm = pl.DataFrame(
        {
            "h": [1, 2, 3],
            "icMean": [0.1, 0.05, 0.01],
            "t": [5.0, 2.5, 1.0],
            "nOrigins": [40] * 3,
            "avgCross": [500.0] * 3,
        }
    )
    star = hc.hStar(fan, firm)
    assert star["env"]["oil"] == 3  # cov90 0.6 = |0.6-0.9|>0.1 위반 첫 걸음
    assert star["firm"] == 3  # t<2 첫 걸음
    assert "hstar-v1" in star["rules"]
    assert np.isfinite(star["firm"])


def _tournamentModel(modelId: str, coefficient: float, *, unit: str = "currency") -> WorldModel:
    variables = (
        VariableSpec("demandShock", "units", "shock"),
        VariableSpec("sales", unit, "state"),
    )

    def salesLaw(ctx):
        return {"sales": ctx.prior["sales"] + coefficient * ctx.shocks["demandShock"]}

    return WorldModel(
        modelId,
        "1",
        variables,
        (),
        (
            LawSpec(
                "salesResponse",
                outputs=("sales",),
                priorInputs=("sales",),
                shockInputs=("demandShock",),
                evidenceKind="explicitAssumption",
                provenance=f"test:{modelId}",
                parameters={"coefficient": coefficient},
                fn=salesLaw,
            ),
        ),
        stepFrequency="quarter",
    )


def _tournamentEpisode(index: int, shocks: tuple[float, float], regime: str) -> hc.WorldModelReplayEpisode:
    origin = f"202{index}0101"
    outcome = f"202{index}0901"
    actual: list[dict[str, float]] = []
    sales = 10.0
    for shock in shocks:
        sales += 2.0 * shock
        actual.append({"sales": sales})
    return hc.WorldModelReplayEpisode(
        episodeId=f"episode-{index}",
        originAsOf=origin,
        outcomeAvailableAt=outcome,
        regime=regime,
        initialState=WorldState(
            {"sales": 10.0},
            asOf=origin,
            knowledgeAsOf=origin,
            decisionAsOf=origin,
        ),
        realizedPath=ScenarioPath(
            f"realized-{index}",
            tuple({"demandShock": value} for value in shocks),
            frequency="quarter",
            validationStatus="retrospectiveOnly",
            knowledgeAsOf=outcome,
            historyStatus="realizedOutcome",
        ),
        observedPolicy=StrategySpec("observedPolicy", ({}, {}), isBaseline=True),
        actualByStep=tuple(actual),
    )


def _tournamentSpec(*, minOrigins: int = 4) -> hc.WorldModelTournamentSpec:
    return hc.WorldModelTournamentSpec(
        evaluationKnowledgeAsOf="20250101",
        metrics=("sales",),
        metricScales={"sales": 5.0},
        baselineModelId="baseline",
        minOrigins=minOrigins,
        weightTemperature=0.5,
    )


def testWorldModelTournamentSelectsMeasuredLawWithoutAdmission():
    candidates = (
        _tournamentModel("baseline", 1.0),
        _tournamentModel("measured", 2.0),
        _tournamentModel("overshoot", 3.0),
    )
    episodes = (
        _tournamentEpisode(1, (1.0, 2.0), "calm"),
        _tournamentEpisode(2, (2.0, 1.0), "calm"),
        _tournamentEpisode(3, (3.0, 2.0), "stress"),
        _tournamentEpisode(4, (2.0, 3.0), "stress"),
    )

    report = hc.runWorldModelTournament(candidates, episodes, _tournamentSpec())
    repeated = hc.runWorldModelTournament(tuple(reversed(candidates)), tuple(reversed(episodes)), _tournamentSpec())
    rows = {row.modelId: row for row in report.candidates}

    assert report == repeated
    assert report.evaluationMode == "conditionalOnRealizedPath"
    assert report.status == "documented"
    assert report.admissionStatus == "notAdmitted"
    assert report.selectionStatus == "eligible"
    assert report.selectedModelId == "measured"
    assert rows["measured"].loss == pytest.approx(0.0)
    assert rows["measured"].skillVsBaseline == pytest.approx(1.0)
    assert rows["measured"].comparisonWeight > rows["baseline"].comparisonWeight
    assert sum(row.comparisonWeight for row in report.candidates) == pytest.approx(1.0)
    assert {row.scope for row in report.slices} == {"origin", "horizon", "regime"}
    assert {row.scopeKey for row in report.slices if row.scope == "horizon"} == {"1", "2"}
    assert {row.scopeKey for row in report.slices if row.scope == "regime"} == {"calm", "stress"}
    assert "comparisonWeightsAreNotProbabilities" in report.warnings
    assert len(report.tournamentHash) == 64
    assert len(report.comparisonHash) == 64
    assert all(len(row.candidateHash) == 64 for row in report.candidates)

    changedLaw = replace(candidates[1].laws[0], parameters={"coefficient": 2.0, "contractRevision": "2"})
    changedCandidate = replace(candidates[1], laws=(changedLaw,))
    changedReport = hc.runWorldModelTournament(
        (candidates[0], changedCandidate, candidates[2]),
        episodes,
        _tournamentSpec(),
    )
    assert changedReport.tournamentHash != report.tournamentHash
    assert {row.modelId: row.candidateHash for row in changedReport.candidates}["measured"] != rows[
        "measured"
    ].candidateHash


def testWorldModelTournamentBindsOutcomesAndRejectsUnsafeReplay():
    episodes = (
        _tournamentEpisode(1, (1.0, 2.0), "calm"),
        _tournamentEpisode(2, (2.0, 1.0), "stress"),
    )
    candidates = (
        _tournamentModel("baseline", 1.0),
        _tournamentModel("measured", 2.0),
    )
    first = hc.runWorldModelTournament(candidates, episodes, _tournamentSpec(minOrigins=2))
    changedActual = list(episodes[-1].actualByStep)
    changedActual[-1] = {"sales": changedActual[-1]["sales"] + 4.0}
    changedEpisodes = (*episodes[:-1], replace(episodes[-1], actualByStep=tuple(changedActual)))
    changed = hc.runWorldModelTournament(candidates, changedEpisodes, _tournamentSpec(minOrigins=2))

    assert first.episodeHashes != changed.episodeHashes
    assert first.tournamentHash != changed.tournamentHash
    assert first.candidates != changed.candidates

    with pytest.raises(hc.WorldModelTournamentError, match="outcome is newer"):
        hc.runWorldModelTournament(
            candidates,
            episodes,
            replace(_tournamentSpec(minOrigins=2), evaluationKnowledgeAsOf="20210901"),
        )
    with pytest.raises(hc.WorldModelTournamentError, match="shared variable contract"):
        hc.runWorldModelTournament(
            (candidates[0], _tournamentModel("measured", 2.0, unit="ratio")),
            episodes,
            _tournamentSpec(minOrigins=2),
        )

    insufficient = hc.runWorldModelTournament(
        candidates,
        episodes[:1],
        _tournamentSpec(minOrigins=2),
    )
    assert insufficient.selectionStatus == "insufficientEvidence"
    assert insufficient.selectedModelId == ""
    assert insufficient.admissionStatus == "notAdmitted"


class _OperatingTournamentVerifier:
    def __init__(self, receipts):
        self.receipts = receipts

    def verify(self, receiptId, *, expectedSubjectHash, expectedKind):
        assert expectedKind == "driverCoefficient"
        receipt = self.receipts[receiptId]
        assert receipt.subjectHash == expectedSubjectHash
        return receipt


def _operatingTournamentCandidate(
    modelId: str,
    coefficient: float,
    token: str,
) -> hc.OperatingTransmissionCandidate:
    receiptId = token * 64
    subjectHash = chr(ord(token) + 1) * 64
    parentReceiptIds = (chr(ord(token) + 2) * 64,)
    factorHash = sourceFactorContractHash(
        variableId="demandFactor",
        unit="ratioChangePerStep",
        frequency="quarter",
        timing="innovation",
        transformId="simple-return-v1",
    )
    exposure = OperatingTransmissionExposure(
        exposureId=f"{modelId}-demand",
        sourceVariableId="demandFactor",
        targetShock="demandChange",
        coefficient=coefficient,
        coefficientUnit="ratioChangePerStep/ratioChangePerStep",
        evidenceKind="measuredAssociation",
        sourceRef=f"driverCoefficientAdmission:{receiptId}",
        sourceFrequency="quarter",
        sourceTiming="innovation",
        sourceTransformId="simple-return-v1",
        sourceFactorContractHash=factorHash,
    )
    binding = ScenarioCoefficientBinding(
        admissionReceiptId=receiptId,
        subjectHash=subjectHash,
        ruleHash="1" * 64,
        ruleId="driver-coefficient",
        ruleVersion="1",
        parentReceiptIds=parentReceiptIds,
        sourceVariableIds=("demandFactor",),
        targetShock="demandChange",
        frequency="quarter",
        stepSpan=1,
        maxAdmittedStep=2,
        coefficientVectorHash="2" * 64,
        featureSpecHash="3" * 64,
        designFrameHash="4" * 64,
        exposureContractHash=scenarioCoefficientExposureContractHash((exposure,)),
    )
    receipt = SimpleNamespace(
        receiptId=receiptId,
        subjectHash=subjectHash,
        artifactHash=subjectHash,
        kind="driverCoefficient",
        status="admitted",
        ruleId=binding.ruleId,
        ruleVersion=binding.ruleVersion,
        ruleHash=binding.ruleHash,
        parentReceiptIds=parentReceiptIds,
        frequency="quarter",
        stepSpan=1,
        maxAdmittedStep=2,
    )
    verifier = _OperatingTournamentVerifier({receiptId: receipt})
    return hc.OperatingTransmissionCandidate(
        modelId=modelId,
        modelVersion="1",
        exposures=(exposure,),
        coefficientBindings=(binding,),
        admissionVerifier=verifier,
        refs=(f"candidate:{modelId}",),
    )


def _operatingTournamentInputs(origin: str, knowledgeAsOf: str):
    primitives = (
        OperatingPrimitive("price", 10.0, "currencyPerUnit", "observed", "filing://price"),
        OperatingPrimitive("demandVolume", 100.0, "units", "observed", "filing://demand"),
        OperatingPrimitive("unitCost", 4.0, "currencyPerUnit", "observed", "filing://unit-cost"),
        OperatingPrimitive("fixedCost", 20.0, "currency", "observed", "filing://fixed-cost"),
        OperatingPrimitive("capacityUnits", 1000.0, "units", "observed", "filing://capacity"),
        OperatingPrimitive("cash", 1000.0, "currency", "observed", "filing://cash"),
        OperatingPrimitive("debt", 0.0, "currency", "observed", "filing://debt"),
    )
    raw = operatingInputsFromPrimitives(
        primitives,
        asOf=origin,
        priceElasticity=1.0,
        capacityUnitsPerCurrency=1.0,
    )
    return replace(raw, knowledgeAsOf=knowledgeAsOf, decisionAsOf=origin)


def _operatingTournamentPathSet(
    origin: str,
    outcome: str,
    values: tuple[float, ...],
) -> DriverPathSet:
    factor = DriverFactorSpec(
        "demandFactor",
        "ratioChangePerStep",
        "quarter",
        "innovation",
        "simple-return-v1",
    )
    path = ScenarioPath(
        pathId=f"realized-{origin}",
        steps=tuple({"demandFactor": value} for value in values),
        refs=(f"provider://driver/{origin}",),
        frequency="quarter",
        stepSpan=1,
        validationStatus="retrospectiveOnly",
        knowledgeAsOf=outcome,
        historyStatus="realizedOutcome",
    )
    digest = canonicalPayloadHash({"origin": origin, "outcome": outcome, "steps": path.steps})
    audit = DriverPathAudit(
        pathSetHash=digest,
        inputHash=digest,
        historyInputHash=digest,
        assumptionHash="",
        assumptionStepHashes=(),
        basePathSetHash=digest,
        basePathAdmissionReceiptId="",
        basePathAdmissionContentHash="",
        basePathAdmissionSubjectHash="",
        basePathValidationStatus="retrospectiveOnly",
        basePathMaxAdmittedStep=0,
        overlayHash="",
        registryHash=canonicalPayloadHash({"registry": "actual-driver"}),
        factorContractHash=canonicalPayloadHash((factor,)),
        generatorVersion="actual-driver-replay-v1",
        knowledgeAsOf=outcome,
        frequency="quarter",
        stepSpan=1,
        horizon=len(values),
        pathCount=1,
        blockLength=1,
        seed=0,
        driverCardIds=("actual-driver",),
        assumptionDescriptors=(),
        validationStatus="retrospectiveOnly",
        observedHistoryStatus="realizedOutcome",
        historyStatus="realizedOutcome",
        sourceRefs=(f"provider://driver/{origin}",),
        warnings=(),
    )
    return DriverPathSet((path,), (factor,), audit)


def _operatingTournamentBaselines():
    return tuple(
        OperatingShockBaseline(target, 0.0, unit, "observed", f"provider://baseline/{target}")
        for target, unit in (
            ("marketPriceChange", "ratioChangePerStep"),
            ("demandChange", "ratioChangePerStep"),
            ("unitCostChange", "ratioChangePerStep"),
            ("fixedCostChange", "ratioChangePerStep"),
            ("capacityChange", "ratioChangePerStep"),
            ("debtRate", "effectiveRatePerStep"),
        )
    )


def _operatingTournamentEpisode(
    index: int,
    truth: hc.OperatingTransmissionCandidate,
) -> hc.OperatingModelReplayEpisode:
    origin = f"202{index}0101"
    outcome = f"202{index}1001"
    inputs = _operatingTournamentInputs(origin, f"202{index - 1}1231")
    pathSet = _operatingTournamentPathSet(origin, outcome, (0.10, -0.05))
    policy = buildOperatingStrategy(
        f"observed-{index}",
        priceChange=(0.0, 0.0),
        capacityInvestment=(0.0, 0.0),
        borrow=(0.0, 0.0),
        repay=(0.0, 0.0),
        refs=(f"provider://policy/{index}",),
    )
    bridged = bridgeOperatingPath(
        pathSet.paths[0],
        truth.exposures,
        factorSpecs=driverFactorsToOperatingSpecs(pathSet.factorSpecs),
        baselines=_operatingTournamentBaselines(),
    )
    run = runOperatingStrategies(
        inputs,
        (bridged.path,),
        (policy,),
        debtLimit=5000.0,
        maxFinancing=1000.0,
        maxInvestment=1000.0,
    )
    actual = tuple(
        {metric: float(step.after[metric]) for metric in ("operatingProfit", "cash")} for step in run.traces[0].steps
    )
    return hc.OperatingModelReplayEpisode(
        episodeId=f"operating-{index}",
        originAsOf=origin,
        outcomeAvailableAt=outcome,
        regime="calm" if index % 2 else "stress",
        inputs=inputs,
        realizedPathSet=pathSet,
        baselines=_operatingTournamentBaselines(),
        observedPolicy=policy,
        actualByStep=actual,
    )


def _operatingTournamentSpec() -> hc.WorldModelTournamentSpec:
    return hc.WorldModelTournamentSpec(
        evaluationKnowledgeAsOf="20251231",
        metrics=("operatingProfit", "cash"),
        metricScales={"operatingProfit": 100.0, "cash": 1000.0},
        baselineModelId="baseline",
        minOrigins=2,
    )


def _runOperatingTournament(candidates, episodes):
    return hc.runOperatingModelTournament(
        candidates,
        episodes,
        _operatingTournamentSpec(),
        debtLimit=5000.0,
        maxFinancing=1000.0,
        maxInvestment=1000.0,
    )


def testOperatingModelTournamentRunsAdmittedTransmissionBeforeWorldEvolution():
    baseline = _operatingTournamentCandidate("baseline", 0.5, "a")
    measured = _operatingTournamentCandidate("measured", 1.5, "d")
    episodes = (_operatingTournamentEpisode(1, measured), _operatingTournamentEpisode(2, measured))

    report = _runOperatingTournament((baseline, measured), episodes)
    repeated = _runOperatingTournament((measured, baseline), tuple(reversed(episodes)))
    rows = {row.modelId: row for row in report.candidates}

    assert report == repeated
    assert report.evaluationMode == "conditionalOnRealizedDriverPath"
    assert report.selectedModelId == "measured"
    assert rows["measured"].loss == pytest.approx(0.0)
    assert rows["measured"].comparisonWeight > rows["baseline"].comparisonWeight
    assert report.status == "documented"
    assert report.admissionStatus == "notAdmitted"
    assert "transmissionComparisonWeightsAreNotProbabilities" in report.warnings


def testOperatingModelTournamentRejectsUnverifiedOrAssumptionLaunderedCandidate():
    baseline = _operatingTournamentCandidate("baseline", 0.5, "a")
    measured = _operatingTournamentCandidate("measured", 1.5, "d")
    episodes = (_operatingTournamentEpisode(1, measured), _operatingTournamentEpisode(2, measured))

    with pytest.raises(hc.WorldModelTournamentError, match="admission verifier"):
        _runOperatingTournament((replace(baseline, admissionVerifier=None), measured), episodes)

    launderedPathSet = replace(
        episodes[0].realizedPathSet,
        audit=replace(
            episodes[0].realizedPathSet.audit,
            assumptionHash=canonicalPayloadHash({"assumption": "hidden"}),
        ),
    )
    with pytest.raises(hc.WorldModelTournamentError, match="without assumptions"):
        _runOperatingTournament(
            (baseline, measured),
            (replace(episodes[0], realizedPathSet=launderedPathSet), episodes[1]),
        )

    driftedExposure = replace(measured.exposures[0], coefficient=1.6)
    with pytest.raises(hc.WorldModelTournamentError, match="exposure contract mismatch"):
        _runOperatingTournament((baseline, replace(measured, exposures=(driftedExposure,))), episodes)

    changedMeasured = _operatingTournamentCandidate("measured", 1.4, "d")
    changed = _runOperatingTournament((baseline, changedMeasured), episodes)
    original = _runOperatingTournament((baseline, measured), episodes)
    assert changed.tournamentHash != original.tournamentHash
    assert changed.candidates != original.candidates

    lookaheadInputs = replace(episodes[0].inputs, knowledgeAsOf="20210102")
    with pytest.raises(hc.WorldModelTournamentError, match="not PIT"):
        _runOperatingTournament(
            (baseline, measured),
            (replace(episodes[0], inputs=lookaheadInputs), episodes[1]),
        )


def _modelUncertaintyCase(caseId: str, demandChanges: tuple[float, ...]) -> OperatingScenarioCase:
    factor = DriverFactorSpec(
        "demandFactor",
        "ratioChangePerStep",
        "quarter",
        "innovation",
        "simple-return-v1",
    )
    card = DriverCard(
        cardId=f"{caseId}-demand",
        sourceKind="explicitAssumption",
        providerId="user",
        datasetId="model-uncertainty-test",
        entityId="005930",
        frequency="quarter",
        stepSpan=1,
        factors=(factor,),
        historyStatus="explicitAssumption",
        sourceRefs=(f"assumption://{caseId}/demand",),
        assumptionId=f"{caseId}-demand",
        claim=f"Demand factor follows {demandChanges}.",
        falsifier="Observed demand factor differs from the explicit case.",
    )
    pathSet = buildDriverPathSet(
        (DriverAssumptionSource(card, tuple({"demandFactor": value} for value in demandChanges)),),
        knowledgeAsOf="20250101",
        horizon=len(demandChanges),
        pathCount=1,
        blockLength=1,
        seed=7,
    )
    return OperatingScenarioCase(
        caseId=caseId,
        label=caseId.title(),
        pathSet=pathSet,
        exposures=(),
        baselines=_operatingTournamentBaselines(),
        refs=(f"scenario://{caseId}",),
    )


def _runModelUncertaintyExperiment(candidates, tournament, cases=None, strategies=None):
    inputs = _operatingTournamentInputs("20250101", "20241231")
    inputs = replace(inputs, state={**inputs.state, "capacityUnits": 105.0})
    caseTuple = cases or (
        _modelUncertaintyCase("growth", (0.10, 0.0)),
        _modelUncertaintyCase("stress", (-0.10, 0.0)),
    )
    strategyTuple = strategies or (
        buildOperatingStrategy(
            "hold",
            priceChange=(0.0, 0.0),
            capacityInvestment=(0.0, 0.0),
            borrow=(0.0, 0.0),
            repay=(0.0, 0.0),
            refs=("strategy://hold",),
            isBaseline=True,
        ),
        buildOperatingStrategy(
            "invest",
            priceChange=(0.0, 0.0),
            capacityInvestment=(20.0, 0.0),
            borrow=(0.0, 0.0),
            repay=(0.0, 0.0),
            refs=("strategy://invest",),
        ),
    )
    return hc.runModelUncertaintyScenarioExperiment(
        "005930",
        inputs,
        caseTuple,
        strategyTuple,
        candidates,
        tournament,
        debtLimit=5000.0,
        maxFinancing=1000.0,
        maxInvestment=1000.0,
        objectiveIndex=1,
    )


def testModelUncertaintyScenarioExperimentPreservesLeadershipReversalsAndWorstModel():
    baseline = _operatingTournamentCandidate("baseline", 0.5, "a")
    measured = _operatingTournamentCandidate("measured", 1.5, "d")
    candidates = (baseline, measured)
    episodes = (_operatingTournamentEpisode(1, measured), _operatingTournamentEpisode(2, measured))
    tournament = _runOperatingTournament(candidates, episodes)

    report = _runModelUncertaintyExperiment(candidates, tournament)
    repeated = _runModelUncertaintyExperiment(tuple(reversed(candidates)), tournament)
    growth = next(row for row in report.caseFragilities if row.caseId == "growth")

    assert report == repeated
    assert report.cellCount == 2 * 2 * 2
    assert report.status == "documented"
    assert report.admissionStatus == "notAdmitted"
    assert report.recommendationCeiling == "conditionalOnly"
    assert report.recommendation is None
    assert report.tournamentComparisonHash == tournament.comparisonHash
    assert growth.leadershipReversal is True
    assert dict(growth.leaderByModel) == {"baseline": ("hold",), "measured": ("invest",)}
    assert sum(weight for _, weight in growth.leaderWeightShares) == pytest.approx(1.0)
    assert all(summary.worstModelId and summary.worstCaseId for summary in report.strategySummaries)
    assert sum(summary.leaderWeightShare for summary in report.strategySummaries) == pytest.approx(1.0)
    assert "modelComparisonWeightsAreNotProbabilities" in report.warnings
    assert "conditionalModelUncertaintyNoRecommendation" in report.blockedReasons


def testModelUncertaintyScenarioExperimentRejectsContractDriftAndAdmissionLaundering():
    baseline = _operatingTournamentCandidate("baseline", 0.5, "a")
    measured = _operatingTournamentCandidate("measured", 1.5, "d")
    candidates = (baseline, measured)
    episodes = (_operatingTournamentEpisode(1, measured), _operatingTournamentEpisode(2, measured))
    tournament = _runOperatingTournament(candidates, episodes)

    changedMeasured = _operatingTournamentCandidate("measured", 1.4, "d")
    with pytest.raises(hc.WorldModelTournamentError, match="candidate content drifted"):
        _runModelUncertaintyExperiment((baseline, changedMeasured), tournament)

    tamperedRows = tuple(replace(row, comparisonWeight=1.0 - row.comparisonWeight) for row in tournament.candidates)
    with pytest.raises(hc.WorldModelTournamentError, match="comparison contract drifted"):
        _runModelUncertaintyExperiment(
            candidates,
            replace(tournament, candidates=tamperedRows),
        )

    embeddedLaw = replace(
        _modelUncertaintyCase("growth", (0.10, 0.0)),
        exposures=baseline.exposures,
        coefficientBindings=baseline.coefficientBindings,
    )
    with pytest.raises(hc.WorldModelTournamentError, match="must not embed a transmission model"):
        _runModelUncertaintyExperiment(
            candidates,
            tournament,
            cases=(embeddedLaw, _modelUncertaintyCase("stress", (-0.10, 0.0))),
        )

    with pytest.raises(hc.WorldModelTournamentError, match="weights require eligible evidence"):
        _runModelUncertaintyExperiment(
            candidates,
            replace(tournament, selectionStatus="baselineBest", selectedModelId=""),
        )
