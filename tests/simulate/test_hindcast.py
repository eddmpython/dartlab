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

import numpy as np
import polars as pl
import pytest

from dartlab.simulate import hindcast as hc
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
