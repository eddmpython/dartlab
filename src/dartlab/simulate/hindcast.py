"""재예보 시험장 : 과거 시점에 보행자를 세워 걸음수별 skill 곡선 실측 (L2.5 simulate).

"과거로 돌아가 미래를 연장하고 이미 아는 답과 대조"(기상 reforecast 동형)의 본진. 두 팔 (15 §6):
- fan: origin PIT 격자의 스텝별 분위를 기대 원장에 봉인(issuedLive=False)·채점 + 곡선 직접 산출
  → coverage(h)·CRPS(h)/carry. 격자 분포가 몇 걸음까지 현실을 커버하나 (h*_env).
- actualPath: 실측 매크로 경로 주입 = 회사층 법칙 격리 채점. origin vintage 베타(nested PIT) x
  실현 누적충격의 예측 반응 vs 실현 버킷중립 초과의 걸음수별 IC + t (h*_firm). **arm 라벨 영구:
  조건부(매크로 실경로 가정) 채점이지 트랙레코드가 아니다.**

h* 판정 규칙 (사전 등록 H_STAR_RULES, 변경 = 새 시리즈): h*_env = coverage90([p5,p95] 명목 90%)
이탈 |cov-0.90|>0.10 첫 걸음. h*_firm = IC 평균의 t < 2.0 첫 걸음. 개별 셀 주장 금지 = 곡선
전체(전 팩터 x 전 지평) 통봉인·통보고. 어떤 채널도 벤치마크를 못 이기면 "다걸음 전개 기각"이
정직한 산출이다 (VAR 기각 동형).

Layer: L2.5 simulate. lattice·scenarioSim·table·estimate(봉인·채점)·readingScorecard(라벨) 배선.

같은 모듈의 world model tournament는 기존 ``WorldModel`` 커널을 바꾸지 않고, 동일한 과거
origin 상태·실현 외생 경로·관측 행동·실제 결과를 복수 세계모델에 공급한다. 이 채점은 미래
경로 예측이 아니라 실현 경로를 조건으로 법칙만 격리하는 ``conditionalOnRealizedPath`` 시험이다.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from datetime import datetime as _dt
from datetime import timedelta as _td
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Mapping

import numpy as np
import polars as pl

from dartlab.simulate import estimate as _estimate
from dartlab.simulate import lattice as _lattice
from dartlab.simulate import readingScorecard as _sc
from dartlab.simulate import scenarioSim as _ss
from dartlab.simulate import table as _table
from dartlab.simulate.factors import macroFactors
from dartlab.simulate.vintage import canonicalPayloadHash
from dartlab.simulate.world import (
    ObjectiveSpec,
    ScenarioPath,
    StrategySpec,
    WorldModel,
    WorldState,
    executableHashFor,
    simulateWorld,
)
from dartlab.synth.expectationSpec import pinballLoss

if TYPE_CHECKING:
    from dartlab.simulate.admissionRegistry import AdmissionVerifier
    from dartlab.simulate.driverPaths import DriverPathSet
    from dartlab.simulate.operatingBridge import OperatingShockBaseline, OperatingTransmissionExposure
    from dartlab.simulate.operatingWorld import OperatingWorldInputs
    from dartlab.simulate.scenarioComposition import (
        ConditionalScenarioExperiment,
        OperatingScenarioCase,
        ScenarioCoefficientBinding,
    )
    from dartlab.simulate.stateCompiler import CompiledPointInTimeState
    from dartlab.simulate.stateSupport import StatePrimitive

H_STAR_RULES = "hstar-v1: env=|cov90-0.90|>0.10 첫 h, firm=t(IC)<2.0 첫 h. 곡선 통보고, 셀 선별 금지."
WORLD_TOURNAMENT_EVALUATION_MODE = "conditionalOnRealizedPath"
OPERATING_MODEL_TOURNAMENT_EVALUATION_MODE = "conditionalOnRealizedDriverPath"
WORLD_TOURNAMENT_LOSS_RULE = "mean-normalized-squared-error-v1"
WORLD_TOURNAMENT_WEIGHT_RULE = "softmax-negative-loss-v1"
MODEL_UNCERTAINTY_SCENARIO_EXPERIMENT_VERSION = "model-uncertainty-scenario-experiment-v1"


def origins(weekEnd: pl.DataFrame, *, start: str = "20190101", gapWeeks: int = 8, steps: int = 8) -> list[str]:
    """재예보 출발점 목록 (사전 등록): start 이후 주말일을 gap 간격 비중첩 추출, 지평 도래분만.

    Args:
        weekEnd: (week, date). start: 첫 origin 하한. gapWeeks: 간격 (>= steps = 표본 비중첩,
            인접 여정 겹침 t 부풀림 차단). steps: 지평 주 수 (마지막 origin + steps 가 데이터 안).

    Returns:
        비중첩 간격과 지평 도래 조건을 만족하는 origin 날짜 목록.

    Raises:
        없음.

    Example:
        ``selected = origins(weekEnd, start="20200101", gapWeeks=8, steps=8)``
    """
    dates = weekEnd.sort("week")["date"].to_list()
    picked = [d for i, d in enumerate(dates) if d >= start and i % max(gapWeeks, steps) == 0]
    return [d for d in picked if dates.index(d) + steps < len(dates)]


def _factorLevelAt(macro: pl.DataFrame, factor: str, date: str) -> float | None:
    s = macro.filter(pl.col("date") <= date)[factor].drop_nulls()
    return float(s[-1]) if s.len() else None


def fanCurves(
    *,
    dataDir: Path | None = None,
    baseDir: Path | None = None,
    start: str = "20190101",
    steps: int = 8,
    gapWeeks: int = 8,
    seal: bool = True,
) -> pl.DataFrame:
    """fan 팔: origin 별 격자 스텝 분위 vs 실현 → (factor, h, cov90, cov50, crps, crpsCarry, n).

    carry 벤치마크 = 무변화 점예보 (CRPS = |실현-현재|, 점예보의 CRPS = MAE). 봉인은 기존
    sealMacroOutlook 계약 재사용 (issuedLive=False, 같은 vintage 재실행 멱등 스킵).

    Args:
        dataDir: 매크로 및 주간 캘린더 데이터 위치.
        baseDir: 기대 원장 봉인 위치.
        start: 첫 origin 날짜 하한.
        steps: 평가할 최대 주간 지평.
        gapWeeks: origin 사이 최소 주간 간격.
        seal: 기대 원장 봉인과 due score 실행 여부.

    Returns:
        걸음수별 곡선 + skill = crpsCarry/crps (>1 = 격자가 carry 보다 낫다). h* 판정은 호출측이
        H_STAR_RULES 로 (곡선 전체 반환 = 셀 선별 금지).

    Raises:
        하위 데이터 로더, 격자 생성기, 원장 계약에서 발생한 예외를 그대로 전달한다.

    Example:
        ``curves = fanCurves(start="20200101", steps=4, seal=False)``
    """
    macro = _table.macroDaily(dataDir)
    _, weekEnd = _table.weekCalendar(dataDir)
    kinds = {mf.factor: mf.kind for mf in macroFactors()}
    ogs = origins(weekEnd, start=start, gapWeeks=gapWeeks, steps=steps)
    rows: list[dict] = []
    for og in ogs:
        pit = macro.filter(pl.col("date") <= og)
        if pit.height < 100:
            continue
        cov = _ss.factorCovariance(pit)
        lat = _lattice.growLattice(
            cov, steps=steps, stepDays=5, beamWidth=_lattice.beamFor(len(cov["factors"])), perStep=True
        )
        for h, marg in enumerate(lat["stepMarginals"], 1):
            target = (_dt.strptime(og, "%Y%m%d") + _td(days=7 * h)).strftime("%Y%m%d")
            if seal:
                _estimate.sealMacroOutlook(pit, marg, asOf=og, horizonWeeks=h, live=False, baseDir=baseDir)
            for factor, q in marg.items():
                cur = _factorLevelAt(pit, factor, og)
                act = _factorLevelAt(macro, factor, target)
                if cur is None or act is None:
                    continue
                if kinds.get(factor) == "price":
                    if cur <= 0:
                        continue
                    quants = {p: cur * (1.0 + q[p]) for p in (5, 25, 50, 75, 95)}
                else:
                    quants = {p: cur + q[p] for p in (5, 25, 50, 75, 95)}
                rows.append(
                    {
                        "origin": og,
                        "factor": factor,
                        "h": h,
                        "hit90": quants[5] <= act <= quants[95],
                        "hit50": quants[25] <= act <= quants[75],
                        "crps": pinballLoss(quants, act),
                        "crpsCarry": abs(act - cur),
                    }
                )
    if seal:
        _estimate.scoreMacroDue(market="KR", baseDir=baseDir, macro=macro)
    if not rows:
        return pl.DataFrame(
            schema={
                "factor": pl.Utf8,
                "h": pl.Int64,
                "cov90": pl.Float64,
                "cov50": pl.Float64,
                "crps": pl.Float64,
                "crpsCarry": pl.Float64,
                "skill": pl.Float64,
                "n": pl.UInt32,
            }
        )
    return (
        pl.DataFrame(rows)
        .group_by(["factor", "h"])
        .agg(
            cov90=pl.col("hit90").mean(),
            cov50=pl.col("hit50").mean(),
            crps=pl.col("crps").mean(),
            crpsCarry=pl.col("crpsCarry").mean(),
            n=pl.len(),
        )
        .with_columns(skill=pl.col("crpsCarry") / pl.col("crps"))
        .select("factor", "h", "cov90", "cov50", "crps", "crpsCarry", "skill", "n")
        .sort(["factor", "h"])
    )


def actualPathCurves(
    *,
    dataDir: Path | None = None,
    start: str = "20190101",
    steps: int = 8,
    gapWeeks: int = 8,
    minCross: int = 300,
) -> pl.DataFrame:
    """actualPath 팔: 실측 매크로 경로 주입 회사층 IC 곡선 → (h, icMean, t, nOrigins, avgCross).

    예측 = origin vintage 베타(nested PIT: macroBetaByCodeWide(asOf=origin)) x 실현 누적 팩터
    변화. 실현 = 지평 h 버킷중립 초과(weeklyLabels horizonDays=5h, 절단 포함). IC = origin 별
    횡단면 Spearman. **조건부 채점(매크로 실경로 가정) 라벨 영구 = 트랙레코드 아님.**

    Args:
        dataDir: 매크로, 가격, 베타 데이터 위치.
        start: 첫 origin 날짜 하한.
        steps: 평가할 최대 주간 지평.
        gapWeeks: origin 사이 최소 주간 간격.
        minCross: origin별 IC 계산에 필요한 최소 종목 수.

    Returns:
        걸음수별 IC 곡선 (origin 비중첩 = 플레인 t 유효, 참고로 표본 std 병기). h*_firm 판정은
        호출측 H_STAR_RULES.

    Raises:
        하위 데이터 로더, 라벨 빌더, 베타 계산에서 발생한 예외를 그대로 전달한다.

    Example:
        ``curves = actualPathCurves(start="20200101", steps=4, minCross=300)``
    """
    macro = _table.macroDaily(dataDir)
    weekMap, weekEnd = _table.weekCalendar(dataDir)
    px = _table.dailyPrices(dataDir)
    kinds = {mf.factor: mf.kind for mf in macroFactors()}
    we = weekEnd.sort("week")
    dates = we["date"].to_list()
    ogs = origins(we, start=start, gapWeeks=gapWeeks, steps=steps)
    labsByH = {h: _sc.weeklyLabels(we, px, horizonDays=5 * h) for h in range(1, steps + 1)}
    weekByDate = dict(zip(we["date"].to_list(), we["week"].to_list()))
    rows: list[dict] = []
    for og in ogs:
        idx = dates.index(og)
        betas = _lattice.winsorizeBetas(_table.macroBetaByCodeWide(og, baseDir=dataDir))
        if betas.height == 0:
            continue
        pit = macro.filter(pl.col("date") <= og)
        for h in range(1, steps + 1):
            target = dates[idx + h]
            pred = pl.lit(0.0)
            for factor, kind in kinds.items():
                col = f"{factor}Beta"
                if col not in betas.columns or factor not in macro.columns:
                    continue
                cur = _factorLevelAt(pit, factor, og)
                lvl = _factorLevelAt(macro, factor, target)
                if cur is None or lvl is None or (kind == "price" and cur <= 0):
                    continue
                dv = (lvl / cur - 1.0) if kind == "price" else (lvl - cur)
                pred = pred + pl.col(col).fill_null(0.0) * dv
            sig = betas.select("code", pred=pred)
            lab = labsByH[h].filter(pl.col("week") == weekByDate[og]).select("code", "exNeutral")
            j = sig.join(lab, on="code", how="inner").drop_nulls()
            if j.height < minCross:
                continue
            rr = j.with_columns(pr=pl.col("pred").rank(), lr=pl.col("exNeutral").rank())
            ic = float(np.corrcoef(rr["pr"].to_numpy(), rr["lr"].to_numpy())[0, 1])
            rows.append({"origin": og, "h": h, "ic": ic, "nCross": j.height})
    if not rows:
        return pl.DataFrame(
            schema={"h": pl.Int64, "icMean": pl.Float64, "t": pl.Float64, "nOrigins": pl.UInt32, "avgCross": pl.Float64}
        )
    df = pl.DataFrame(rows)
    return (
        df.group_by("h")
        .agg(
            icMean=pl.col("ic").mean(),
            t=pl.col("ic").mean() / (pl.col("ic").std() / pl.len().sqrt()),
            nOrigins=pl.len(),
            avgCross=pl.col("nCross").mean(),
        )
        .sort("h")
    )


def hStar(fan: pl.DataFrame, firm: pl.DataFrame) -> dict:
    """사전 등록 규칙(H_STAR_RULES)으로 전개 한계 판정 → {"env": {factor: h*}, "firm": h*}.

    h* = 규칙 위반 첫 걸음 (전 걸음 통과면 지평+1 = 관측 한계까지 유효). 곡선 전체와 함께
    보고해야 하며 h* 단독 인용 금지.

    Args:
        fan: factor, h, cov90을 가진 환경 재예보 곡선.
        firm: h, t를 가진 회사층 조건부 채점 곡선.

    Returns:
        factor별 환경 전개 한계, 회사층 전개 한계, 적용 규칙 문자열.

    Raises:
        polars.exceptions.ColumnNotFoundError: 필수 곡선 열이 없는 경우.

    Example:
        ``limits = hStar(fanCurves, firmCurves)``
    """
    env: dict[str, int] = {}
    for factor in fan["factor"].unique().sort().to_list() if fan.height else []:
        sub = fan.filter(pl.col("factor") == factor).sort("h")
        star = int(sub["h"].max()) + 1
        for r in sub.iter_rows(named=True):
            if abs(r["cov90"] - 0.90) > 0.10:
                star = r["h"]
                break
        env[factor] = star
    firmStar = (int(firm["h"].max()) + 1) if firm.height else 0
    for r in firm.sort("h").iter_rows(named=True) if firm.height else []:
        if r["t"] < 2.0:
            firmStar = r["h"]
            break
    return {"env": env, "firm": firmStar, "rules": H_STAR_RULES}


class WorldModelTournamentError(ValueError):
    """세계모델 토너먼트 입력 또는 시간 계약이 잘못되면 발생한다."""


def _freezeTournamentMapping(values: Mapping) -> Mapping:
    return MappingProxyType(dict(values))


def _tournamentDateText(value: str, label: str) -> str:
    text = str(value).replace("-", "")[:8]
    if len(text) != 8 or not text.isdigit():
        raise WorldModelTournamentError(f"invalid {label}: {value}")
    return text


def _tournamentFinite(value: float, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise WorldModelTournamentError(f"{label} must be finite")
    return number


@dataclass(frozen=True)
class WorldModelReplayEpisode:
    """한 origin의 초기상태, 실현 경로, 관측 행동, 실제 상태를 묶는다."""

    episodeId: str
    originAsOf: str
    outcomeAvailableAt: str
    regime: str
    initialState: WorldState
    realizedPath: ScenarioPath
    observedPolicy: StrategySpec
    actualByStep: tuple[Mapping[str, float], ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "actualByStep",
            tuple(_freezeTournamentMapping(step) for step in self.actualByStep),
        )


@dataclass(frozen=True)
class OperatingTransmissionCandidate:
    """한 admitted factor transmission 계수 후보와 검증 경계를 묶는다."""

    modelId: str
    modelVersion: str
    exposures: tuple[OperatingTransmissionExposure, ...]
    coefficientBindings: tuple[ScenarioCoefficientBinding, ...]
    admissionVerifier: AdmissionVerifier | None
    refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "exposures", tuple(self.exposures))
        object.__setattr__(self, "coefficientBindings", tuple(self.coefficientBindings))
        object.__setattr__(self, "refs", tuple(self.refs))


@dataclass(frozen=True)
class OperatingModelReplayEpisode:
    """한 PIT origin의 실현 driver 경로와 실제 operating outcome을 묶는다."""

    episodeId: str
    originAsOf: str
    outcomeAvailableAt: str
    regime: str
    inputs: OperatingWorldInputs
    realizedPathSet: DriverPathSet
    baselines: tuple[OperatingShockBaseline, ...]
    observedPolicy: StrategySpec
    actualByStep: tuple[Mapping[str, float], ...]
    compiledState: CompiledPointInTimeState | None = None
    statePrimitives: tuple[StatePrimitive, ...] = ()
    stateRef: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "baselines", tuple(self.baselines))
        object.__setattr__(
            self,
            "actualByStep",
            tuple(_freezeTournamentMapping(step) for step in self.actualByStep),
        )
        object.__setattr__(self, "statePrimitives", tuple(self.statePrimitives))


@dataclass(frozen=True)
class WorldModelTournamentSpec:
    """채점 지표, 척도, baseline, 표본 문턱, 비교 가중 규칙을 선언한다."""

    evaluationKnowledgeAsOf: str
    metrics: tuple[str, ...]
    metricScales: Mapping[str, float]
    baselineModelId: str
    minOrigins: int
    weightTemperature: float = 1.0
    minSkillVsBaseline: float = 0.0
    lossRule: str = WORLD_TOURNAMENT_LOSS_RULE
    weightRule: str = WORLD_TOURNAMENT_WEIGHT_RULE

    def __post_init__(self) -> None:
        object.__setattr__(self, "metrics", tuple(self.metrics))
        object.__setattr__(self, "metricScales", _freezeTournamentMapping(self.metricScales))


@dataclass(frozen=True)
class WorldModelSliceScore:
    """origin, horizon, regime 중 한 절편의 모델 손실과 baseline skill을 보존한다."""

    modelId: str
    modelVersion: str
    scope: str
    scopeKey: str
    loss: float
    baselineLoss: float
    skillVsBaseline: float
    observationCount: int
    runHash: str = ""
    resultHash: str = ""
    executableHash: str = ""


@dataclass(frozen=True)
class WorldModelTournamentCandidate:
    """한 후보 세계모델의 전체 replay 성적, 순위, 비교 가중치를 보존한다."""

    modelId: str
    modelVersion: str
    candidateHash: str
    loss: float
    baselineLoss: float
    skillVsBaseline: float
    comparisonWeight: float
    rank: int
    originCount: int
    observationCount: int


@dataclass(frozen=True)
class WorldModelTournamentReport:
    """동일 episode에서 경쟁한 세계모델의 재현 가능한 documented 결과다."""

    tournamentHash: str
    evaluationMode: str
    status: str
    admissionStatus: str
    selectionStatus: str
    selectedModelId: str
    baselineModelId: str
    episodeCount: int
    modelCount: int
    episodeHashes: tuple[str, ...]
    candidates: tuple[WorldModelTournamentCandidate, ...]
    slices: tuple[WorldModelSliceScore, ...]
    warnings: tuple[str, ...]
    comparisonHash: str = ""


@dataclass(frozen=True)
class ModelUncertaintyCell:
    """One model, assumption case, and strategy result without model averaging."""

    modelId: str
    modelVersion: str
    candidateHash: str
    comparisonWeight: float
    caseId: str
    label: str
    strategyId: str
    score: float
    regret: float
    feasible: bool
    breachCount: int
    scoreLeader: bool
    assumptionSetHash: str
    sourceExperimentHash: str
    runHash: str
    resultHash: str


@dataclass(frozen=True)
class ModelUncertaintyStrategySummary:
    """Weighted strategy summary with its worst model and assumption case retained."""

    strategyId: str
    weightedMeanScore: float
    weightedMeanRegret: float
    worstScore: float
    worstRegret: float
    worstModelId: str
    worstCaseId: str
    leaderWeightShare: float
    feasibleWeightShare: float
    breachCount: int
    cellCount: int


@dataclass(frozen=True)
class ModelUncertaintyCaseFragility:
    """Case-level strategy leadership changes across transmission models."""

    caseId: str
    label: str
    leadershipReversal: bool
    stableLeaderStrategies: tuple[str, ...]
    leaderByModel: tuple[tuple[str, tuple[str, ...]], ...]
    leaderWeightShares: tuple[tuple[str, float], ...]
    worstModelId: str
    worstModelLeaderScore: float
    worstLeaderMargin: float
    maxStrategyScoreSpread: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "stableLeaderStrategies", tuple(self.stableLeaderStrategies))
        object.__setattr__(
            self,
            "leaderByModel",
            tuple((modelId, tuple(strategyIds)) for modelId, strategyIds in self.leaderByModel),
        )
        object.__setattr__(self, "leaderWeightShares", tuple(tuple(item) for item in self.leaderWeightShares))


@dataclass(frozen=True)
class ModelUncertaintyScenarioExperiment:
    """Conditional model by assumption by strategy experiment and fragility ledger."""

    uncertaintyHash: str
    schemaVersion: str
    status: str
    admissionStatus: str
    recommendationCeiling: str
    recommendation: str | None
    entityId: str
    tournamentHash: str
    tournamentComparisonHash: str
    tournamentEvaluationMode: str
    tournamentSelectionStatus: str
    modelCount: int
    scenarioCount: int
    strategyCount: int
    cellCount: int
    modelIds: tuple[str, ...]
    modelVersions: tuple[str, ...]
    candidateHashes: tuple[str, ...]
    modelComparisonWeights: tuple[tuple[str, float], ...]
    sourceExperimentHashes: tuple[tuple[str, str], ...]
    cells: tuple[ModelUncertaintyCell, ...]
    strategySummaries: tuple[ModelUncertaintyStrategySummary, ...]
    caseFragilities: tuple[ModelUncertaintyCaseFragility, ...]
    blockedReasons: tuple[str, ...]
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        for fieldName in (
            "modelIds",
            "modelVersions",
            "candidateHashes",
            "modelComparisonWeights",
            "sourceExperimentHashes",
            "cells",
            "strategySummaries",
            "caseFragilities",
            "blockedReasons",
            "warnings",
        ):
            object.__setattr__(self, fieldName, tuple(getattr(self, fieldName)))


def _worldModelTournamentComparisonHash(report: WorldModelTournamentReport) -> str:
    return canonicalPayloadHash(
        {
            "schemaVersion": "world-model-tournament-comparison-v1",
            "tournamentHash": report.tournamentHash,
            "evaluationMode": report.evaluationMode,
            "status": report.status,
            "admissionStatus": report.admissionStatus,
            "selectionStatus": report.selectionStatus,
            "selectedModelId": report.selectedModelId,
            "baselineModelId": report.baselineModelId,
            "episodeCount": report.episodeCount,
            "modelCount": report.modelCount,
            "episodeHashes": report.episodeHashes,
            "candidates": report.candidates,
            "slices": report.slices,
            "warnings": report.warnings,
        }
    )


def _worldReplayEpisodePayload(episode: WorldModelReplayEpisode) -> dict:
    return {
        "episodeId": episode.episodeId,
        "originAsOf": episode.originAsOf,
        "outcomeAvailableAt": episode.outcomeAvailableAt,
        "regime": episode.regime,
        "initialState": {
            "values": episode.initialState.values,
            "step": episode.initialState.step,
            "asOf": episode.initialState.asOf,
            "refs": episode.initialState.refs,
            "knowledgeAsOf": episode.initialState.knowledgeAsOf,
            "decisionAsOf": episode.initialState.decisionAsOf,
        },
        "realizedPath": {
            "pathId": episode.realizedPath.pathId,
            "steps": episode.realizedPath.steps,
            "frequency": episode.realizedPath.frequency,
            "stepSpan": episode.realizedPath.stepSpan,
            "validationStatus": episode.realizedPath.validationStatus,
            "knowledgeAsOf": episode.realizedPath.knowledgeAsOf,
            "historyStatus": episode.realizedPath.historyStatus,
            "refs": episode.realizedPath.refs,
        },
        "observedPolicy": {
            "strategyId": episode.observedPolicy.strategyId,
            "actionsByStep": episode.observedPolicy.actionsByStep,
            "refs": episode.observedPolicy.refs,
            "policyVersion": episode.observedPolicy.policyVersion,
            "policyProvenance": episode.observedPolicy.policyProvenance,
        },
        "actualByStep": episode.actualByStep,
    }


def _operatingTransmissionCandidatePayload(candidate: OperatingTransmissionCandidate) -> dict:
    return {
        "modelId": candidate.modelId,
        "modelVersion": candidate.modelVersion,
        "exposures": candidate.exposures,
        "coefficientBindings": candidate.coefficientBindings,
        "refs": candidate.refs,
    }


def _worldModelCandidatePayload(model: WorldModel) -> dict:
    return {
        "modelId": model.modelId,
        "modelVersion": model.version,
        "sharedContract": _worldModelSharedContractPayload(model),
        "laws": tuple(
            {
                "lawId": law.lawId,
                "outputs": law.outputs,
                "priorInputs": law.priorInputs,
                "currentInputs": law.currentInputs,
                "shockInputs": law.shockInputs,
                "actionInputs": law.actionInputs,
                "pathParameterInputs": law.pathParameterInputs,
                "usesActionCost": law.usesActionCost,
                "evidenceKind": law.evidenceKind,
                "provenance": law.provenance,
                "version": law.version,
                "status": law.status,
                "certificate": law.certificate,
                "parameters": law.parameters,
                "pathParameterUnits": law.pathParameterUnits,
            }
            for law in model.laws
        ),
        "executableHash": executableHashFor(model, ()),
    }


def _tournamentCandidateHash(candidate: WorldModel | OperatingTransmissionCandidate) -> str:
    if isinstance(candidate, WorldModel):
        return canonicalPayloadHash(_worldModelCandidatePayload(candidate))
    return canonicalPayloadHash(_operatingTransmissionCandidatePayload(candidate))


def _operatingReplayEpisodePayload(episode: OperatingModelReplayEpisode) -> dict:
    path = episode.realizedPathSet.paths[0]
    compiledState = episode.compiledState
    return {
        "episodeId": episode.episodeId,
        "originAsOf": episode.originAsOf,
        "outcomeAvailableAt": episode.outcomeAvailableAt,
        "regime": episode.regime,
        "inputs": episode.inputs,
        "realizedPathSet": {
            "path": path,
            "factorSpecs": episode.realizedPathSet.factorSpecs,
            "audit": episode.realizedPathSet.audit,
        },
        "baselines": episode.baselines,
        "observedPolicy": {
            "strategyId": episode.observedPolicy.strategyId,
            "actionsByStep": episode.observedPolicy.actionsByStep,
            "refs": episode.observedPolicy.refs,
            "policyVersion": episode.observedPolicy.policyVersion,
            "policyProvenance": episode.observedPolicy.policyProvenance,
        },
        "actualByStep": episode.actualByStep,
        "compiledState": (
            {
                "stateId": compiledState.stateId,
                "manifestHash": compiledState.manifestHash,
                "stateCompilationContractHash": compiledState.stateCompilationContractHash,
                "stateReceiptId": compiledState.stateReceiptId,
                "providerBatchReceiptIds": compiledState.providerBatchReceiptIds,
            }
            if compiledState is not None
            else None
        ),
        "statePrimitives": episode.statePrimitives,
        "stateRef": episode.stateRef,
    }


def _worldModelSharedContractPayload(model: WorldModel) -> dict:
    return {
        "variables": model.variables,
        "actions": model.actions,
        "stepFrequency": model.stepFrequency,
        "stepSpan": model.stepSpan,
    }


def _validateWorldModelTournamentSpec(spec: WorldModelTournamentSpec) -> None:
    _tournamentDateText(spec.evaluationKnowledgeAsOf, "evaluationKnowledgeAsOf")
    if not spec.metrics or len(set(spec.metrics)) != len(spec.metrics):
        raise WorldModelTournamentError("tournament metrics must be non-empty and unique")
    if set(spec.metricScales) != set(spec.metrics):
        raise WorldModelTournamentError("metric scales must exactly cover tournament metrics")
    if any(_tournamentFinite(value, f"metric scale {metric}") <= 0 for metric, value in spec.metricScales.items()):
        raise WorldModelTournamentError("metric scales must be positive")
    if not spec.baselineModelId or spec.minOrigins < 1:
        raise WorldModelTournamentError("baseline and minimum origin count are required")
    if _tournamentFinite(spec.weightTemperature, "weightTemperature") <= 0:
        raise WorldModelTournamentError("weight temperature must be positive")
    _tournamentFinite(spec.minSkillVsBaseline, "minSkillVsBaseline")
    if spec.lossRule != WORLD_TOURNAMENT_LOSS_RULE or spec.weightRule != WORLD_TOURNAMENT_WEIGHT_RULE:
        raise WorldModelTournamentError("unsupported tournament scoring rule")


def _validateTournamentCandidateIdentity(
    candidates: tuple[WorldModel | OperatingTransmissionCandidate, ...],
    spec: WorldModelTournamentSpec,
) -> None:
    if len(candidates) < 2:
        raise WorldModelTournamentError("world model tournament needs at least two candidates")
    modelIds = tuple(model.modelId for model in candidates)
    if len(set(modelIds)) != len(modelIds):
        raise WorldModelTournamentError("candidate model ids must be unique")
    if spec.baselineModelId not in modelIds:
        raise WorldModelTournamentError("baseline model is not a tournament candidate")
    if any(not model.modelId or not _tournamentCandidateVersion(model) for model in candidates):
        raise WorldModelTournamentError("candidate model identity is incomplete")


def _validateWorldModelCandidates(
    candidates: tuple[WorldModel, ...],
    spec: WorldModelTournamentSpec,
) -> None:
    _validateTournamentCandidateIdentity(candidates, spec)
    sharedContract = canonicalPayloadHash(_worldModelSharedContractPayload(candidates[0]))
    if any(canonicalPayloadHash(_worldModelSharedContractPayload(model)) != sharedContract for model in candidates[1:]):
        raise WorldModelTournamentError("shared variable contract, action contract, and step contract required")
    variableById = {variable.variableId: variable for variable in candidates[0].variables}
    if any(metric not in variableById or variableById[metric].role == "shock" for metric in spec.metrics):
        raise WorldModelTournamentError("tournament metric is not a model output")


def _validateOperatingCandidate(candidate: OperatingTransmissionCandidate) -> None:
    if candidate.admissionVerifier is None:
        raise WorldModelTournamentError("operating transmission candidate needs an admission verifier")
    if not candidate.refs or not candidate.exposures or not candidate.coefficientBindings:
        raise WorldModelTournamentError("operating transmission candidate contract is incomplete")
    if any(exposure.evidenceKind != "measuredAssociation" for exposure in candidate.exposures):
        raise WorldModelTournamentError("operating model tournament accepts only measured coefficient exposures")


def _validateOperatingReplayTiming(
    episode: OperatingModelReplayEpisode,
    evaluationKnowledge: str,
) -> None:
    origin = _tournamentDateText(episode.originAsOf, f"origin {episode.episodeId}")
    outcome = _tournamentDateText(episode.outcomeAvailableAt, f"outcome {episode.episodeId}")
    if outcome <= origin or outcome > evaluationKnowledge:
        raise WorldModelTournamentError("operating replay outcome timing is invalid")
    if not episode.regime:
        raise WorldModelTournamentError("operating replay episode needs a regime label")
    inputKnowledge = _tournamentDateText(episode.inputs.knowledgeAsOf, "operating input knowledge")
    inputDecision = _tournamentDateText(episode.inputs.decisionAsOf, "operating input decision")
    if inputKnowledge > origin or inputDecision != origin:
        raise WorldModelTournamentError("operating replay initial state is not PIT at the origin")
    path = episode.realizedPathSet.paths[0]
    pathKnowledge = _tournamentDateText(path.knowledgeAsOf, "realized driver path knowledge")
    auditKnowledge = _tournamentDateText(episode.realizedPathSet.audit.knowledgeAsOf, "driver path audit knowledge")
    if pathKnowledge <= origin or pathKnowledge > outcome or auditKnowledge != pathKnowledge:
        raise WorldModelTournamentError("realized driver path timing is not retrospective")


def _validateOperatingRealizedPath(episode: OperatingModelReplayEpisode) -> ScenarioPath:
    pathSet = episode.realizedPathSet
    if len(pathSet.paths) != 1 or pathSet.audit.pathCount != 1:
        raise WorldModelTournamentError("operating replay needs exactly one realized driver path")
    path = pathSet.paths[0]
    audit = pathSet.audit
    if path.weightKind != "unweighted" or path.weight is not None:
        raise WorldModelTournamentError("operating replay realized driver path must be unweighted")
    if (
        path.validationStatus != "retrospectiveOnly"
        or path.historyStatus != "realizedOutcome"
        or audit.validationStatus != "retrospectiveOnly"
        or audit.historyStatus != "realizedOutcome"
        or audit.observedHistoryStatus != "realizedOutcome"
        or audit.assumptionHash
        or audit.overlayHash
    ):
        raise WorldModelTournamentError("operating replay path set must contain realized outcomes without assumptions")
    return path


def _validateOperatingReplayStepContract(
    episode: OperatingModelReplayEpisode,
    path: ScenarioPath,
) -> int:
    pathSet = episode.realizedPathSet
    audit = pathSet.audit
    horizon = len(path.steps)
    if horizon < 1 or audit.horizon != horizon:
        raise WorldModelTournamentError("operating replay driver horizon is invalid")
    if path.frequency != audit.frequency or path.stepSpan != audit.stepSpan:
        raise WorldModelTournamentError("operating replay driver step contract drifted")
    if path.frequency != episode.inputs.stepFrequency or path.stepSpan != episode.inputs.stepSpan:
        raise WorldModelTournamentError("operating replay input and driver step contracts differ")
    factorIds = {factor.variableId for factor in pathSet.factorSpecs}
    if not factorIds or len(factorIds) != len(pathSet.factorSpecs):
        raise WorldModelTournamentError("operating replay factor contracts are incomplete")
    if any(set(step) != factorIds for step in path.steps):
        raise WorldModelTournamentError("operating replay driver factor coverage drifted")
    return horizon


def _validateOperatingReplayOutcomes(
    episode: OperatingModelReplayEpisode,
    spec: WorldModelTournamentSpec,
    horizon: int,
) -> None:
    if len(episode.actualByStep) != horizon or len(episode.observedPolicy.actionsByStep) != horizon:
        raise WorldModelTournamentError("operating replay path, policy, and actual horizon must match")
    if episode.observedPolicy.policyFn is not None:
        raise WorldModelTournamentError("operating replay observed policy must be a fixed action record")
    for step in episode.actualByStep:
        if not set(spec.metrics) <= set(step):
            raise WorldModelTournamentError("operating replay actual step is missing tournament metrics")
        for metric in spec.metrics:
            _tournamentFinite(step[metric], f"actual {episode.episodeId} {metric}")


def _validateOperatingReplayShape(
    episode: OperatingModelReplayEpisode,
    spec: WorldModelTournamentSpec,
) -> None:
    path = _validateOperatingRealizedPath(episode)
    horizon = _validateOperatingReplayStepContract(episode, path)
    _validateOperatingReplayOutcomes(episode, spec, horizon)


def _validateOperatingCoefficientCandidate(
    candidate: OperatingTransmissionCandidate,
    episode: OperatingModelReplayEpisode,
) -> None:
    from dartlab.simulate.scenarioComposition import (
        OperatingScenarioCase,
        ScenarioCompositionError,
        validateScenarioCoefficientBindings,
    )

    case = OperatingScenarioCase(
        caseId=f"replay:{episode.episodeId}:{candidate.modelId}",
        label=f"{candidate.modelId} at {episode.originAsOf}",
        pathSet=episode.realizedPathSet,
        exposures=candidate.exposures,
        baselines=episode.baselines,
        refs=candidate.refs,
        coefficientBindings=candidate.coefficientBindings,
        admissionVerifier=candidate.admissionVerifier,
    )
    try:
        validateScenarioCoefficientBindings(case)
    except ScenarioCompositionError as error:
        raise WorldModelTournamentError(f"operating coefficient candidate is invalid: {error}") from error


def _validateOperatingModelTournamentInputs(
    candidates: tuple[OperatingTransmissionCandidate, ...],
    episodes: tuple[OperatingModelReplayEpisode, ...],
    spec: WorldModelTournamentSpec,
) -> None:
    _validateWorldModelTournamentSpec(spec)
    _validateTournamentCandidateIdentity(candidates, spec)
    for candidate in candidates:
        _validateOperatingCandidate(candidate)
    if not episodes:
        raise WorldModelTournamentError("operating model tournament needs replay episodes")
    episodeIds = tuple(episode.episodeId for episode in episodes)
    origins = tuple(episode.originAsOf for episode in episodes)
    if len(set(episodeIds)) != len(episodeIds) or len(set(origins)) != len(origins):
        raise WorldModelTournamentError("operating replay episode ids and origins must be unique")
    evaluationKnowledge = _tournamentDateText(spec.evaluationKnowledgeAsOf, "evaluationKnowledgeAsOf")
    for episode in episodes:
        _validateOperatingReplayShape(episode, spec)
        _validateOperatingReplayTiming(episode, evaluationKnowledge)
        for candidate in candidates:
            _validateOperatingCoefficientCandidate(candidate, episode)


def _validateWorldReplayTiming(
    episode: WorldModelReplayEpisode,
    evaluationKnowledge: str,
) -> None:
    origin = _tournamentDateText(episode.originAsOf, f"origin {episode.episodeId}")
    outcome = _tournamentDateText(episode.outcomeAvailableAt, f"outcome {episode.episodeId}")
    if outcome <= origin:
        raise WorldModelTournamentError("replay outcome must follow its origin")
    if outcome > evaluationKnowledge:
        raise WorldModelTournamentError("replay outcome is newer than evaluation knowledge")
    if not episode.regime:
        raise WorldModelTournamentError("replay episode needs a regime label")
    initialKnowledge = _tournamentDateText(episode.initialState.knowledgeAsOf, "initial state knowledge")
    initialDecision = _tournamentDateText(episode.initialState.decisionAsOf, "initial state decision")
    if initialKnowledge > origin or initialDecision > origin:
        raise WorldModelTournamentError("initial state contains lookahead")
    pathKnowledge = _tournamentDateText(episode.realizedPath.knowledgeAsOf, "realized path knowledge")
    if pathKnowledge <= origin or pathKnowledge > outcome:
        raise WorldModelTournamentError("realized path timing is not retrospective")
    if (
        episode.realizedPath.validationStatus != "retrospectiveOnly"
        or episode.realizedPath.historyStatus != "realizedOutcome"
    ):
        raise WorldModelTournamentError("replay path must be labeled as a realized retrospective outcome")


def _validateWorldReplayShape(
    episode: WorldModelReplayEpisode,
    spec: WorldModelTournamentSpec,
) -> None:
    if episode.realizedPath.weightKind != "unweighted" or episode.realizedPath.weight is not None:
        raise WorldModelTournamentError("each replay origin must have one unweighted realized path")
    horizon = len(episode.realizedPath.steps)
    if horizon < 1 or len(episode.actualByStep) != horizon or len(episode.observedPolicy.actionsByStep) != horizon:
        raise WorldModelTournamentError("replay path, policy, and actual horizon must match")
    if episode.observedPolicy.policyFn is not None:
        raise WorldModelTournamentError("observed policy must be a fixed action record")
    for step in episode.actualByStep:
        if not set(spec.metrics) <= set(step):
            raise WorldModelTournamentError("actual replay step is missing tournament metrics")
        for metric in spec.metrics:
            _tournamentFinite(step[metric], f"actual {episode.episodeId} {metric}")


def _validateWorldModelTournamentInputs(
    candidates: tuple[WorldModel, ...],
    episodes: tuple[WorldModelReplayEpisode, ...],
    spec: WorldModelTournamentSpec,
) -> None:
    _validateWorldModelTournamentSpec(spec)
    _validateWorldModelCandidates(candidates, spec)
    if not episodes:
        raise WorldModelTournamentError("world model tournament needs replay episodes")
    episodeIds = tuple(episode.episodeId for episode in episodes)
    origins = tuple(episode.originAsOf for episode in episodes)
    if len(set(episodeIds)) != len(episodeIds) or len(set(origins)) != len(origins):
        raise WorldModelTournamentError("replay episode ids and origins must be unique")
    evaluationKnowledge = _tournamentDateText(spec.evaluationKnowledgeAsOf, "evaluationKnowledgeAsOf")
    for episode in episodes:
        _validateWorldReplayTiming(episode, evaluationKnowledge)
        _validateWorldReplayShape(episode, spec)


def _worldModelTournamentSkill(loss: float, baselineLoss: float) -> float:
    if baselineLoss <= 1e-15:
        return 0.0 if loss <= 1e-15 else -1.0
    return 1.0 - loss / baselineLoss


def _worldModelMeanLoss(records: list[dict]) -> tuple[float, int]:
    count = sum(int(record["observationCount"]) for record in records)
    if count < 1:
        raise WorldModelTournamentError("tournament loss has no observations")
    return sum(float(record["lossSum"]) for record in records) / count, count


def _tournamentCandidateVersion(candidate: WorldModel | OperatingTransmissionCandidate) -> str:
    return candidate.version if isinstance(candidate, WorldModel) else candidate.modelVersion


def _tournamentStepLosses(
    predictedSteps,
    actualByStep: tuple[Mapping[str, float], ...],
    spec: WorldModelTournamentSpec,
) -> tuple[float, ...]:
    try:
        return tuple(
            sum(
                ((float(predicted.after[metric]) - float(actual[metric])) / float(spec.metricScales[metric])) ** 2
                for metric in spec.metrics
            )
            / len(spec.metrics)
            for predicted, actual in zip(predictedSteps, actualByStep, strict=True)
        )
    except KeyError as error:
        raise WorldModelTournamentError(
            f"tournament metric is not produced by the executable: {error.args[0]}"
        ) from error


def _worldModelTournamentRawScores(
    candidates: tuple[WorldModel, ...],
    episodes: tuple[WorldModelReplayEpisode, ...],
    spec: WorldModelTournamentSpec,
) -> list[dict]:
    raw: list[dict] = []
    for model in candidates:
        for episode in episodes:
            run = simulateWorld(
                model,
                episode.initialState,
                (episode.realizedPath,),
                (episode.observedPolicy,),
                objectives=(ObjectiveSpec(spec.metrics[0], reducer="terminal", risk="average"),),
            )
            if len(run.traces) != 1:
                raise WorldModelTournamentError("replay run must retain exactly one trace")
            trace = run.traces[0]
            stepLosses = _tournamentStepLosses(trace.steps, episode.actualByStep, spec)
            raw.append(
                {
                    "modelId": model.modelId,
                    "modelVersion": model.version,
                    "episodeId": episode.episodeId,
                    "regime": episode.regime,
                    "lossSum": sum(stepLosses) * len(spec.metrics),
                    "observationCount": len(stepLosses) * len(spec.metrics),
                    "stepLosses": stepLosses,
                    "runHash": run.runHash,
                    "resultHash": run.resultHash,
                    "executableHash": run.executableHash,
                }
            )
    return raw


def _operatingModelTournamentRawScores(
    candidates: tuple[OperatingTransmissionCandidate, ...],
    episodes: tuple[OperatingModelReplayEpisode, ...],
    spec: WorldModelTournamentSpec,
    *,
    debtLimit: float,
    maxFinancing: float,
    maxInvestment: float,
) -> list[dict]:
    from dartlab.simulate.driverPaths import driverFactorsToOperatingSpecs
    from dartlab.simulate.operatingBridge import bridgeOperatingPath
    from dartlab.simulate.operatingWorld import runOperatingStrategies

    raw: list[dict] = []
    for candidate in candidates:
        candidateHash = _tournamentCandidateHash(candidate)
        for episode in episodes:
            path = episode.realizedPathSet.paths[0]
            bridged = bridgeOperatingPath(
                path,
                candidate.exposures,
                factorSpecs=driverFactorsToOperatingSpecs(episode.realizedPathSet.factorSpecs),
                baselines=episode.baselines,
                compiledState=episode.compiledState,
                statePrimitives=episode.statePrimitives,
                stateRef=episode.stateRef,
                admissionVerifier=candidate.admissionVerifier,
                pathId=f"replay:{episode.episodeId}:{candidate.modelId}",
            )
            run = runOperatingStrategies(
                episode.inputs,
                (bridged.path,),
                (episode.observedPolicy,),
                debtLimit=debtLimit,
                maxFinancing=maxFinancing,
                maxInvestment=maxInvestment,
            )
            if len(run.traces) != 1:
                raise WorldModelTournamentError("operating replay run must retain exactly one trace")
            trace = run.traces[0]
            stepLosses = _tournamentStepLosses(trace.steps, episode.actualByStep, spec)
            compositeRunHash = canonicalPayloadHash(
                {
                    "runHash": run.runHash,
                    "bridgeHash": bridged.audit.bridgeHash,
                    "candidateHash": candidateHash,
                }
            )
            compositeResultHash = canonicalPayloadHash(
                {
                    "resultHash": run.resultHash,
                    "bridgeHash": bridged.audit.bridgeHash,
                }
            )
            compositeExecutableHash = canonicalPayloadHash(
                {
                    "worldExecutableHash": run.executableHash,
                    "transmissionCandidateHash": candidateHash,
                }
            )
            raw.append(
                {
                    "modelId": candidate.modelId,
                    "modelVersion": candidate.modelVersion,
                    "episodeId": episode.episodeId,
                    "regime": episode.regime,
                    "lossSum": sum(stepLosses) * len(spec.metrics),
                    "observationCount": len(stepLosses) * len(spec.metrics),
                    "stepLosses": stepLosses,
                    "runHash": compositeRunHash,
                    "resultHash": compositeResultHash,
                    "executableHash": compositeExecutableHash,
                }
            )
    return raw


def _worldModelTournamentCandidates(
    candidates: tuple[WorldModel | OperatingTransmissionCandidate, ...],
    raw: list[dict],
    spec: WorldModelTournamentSpec,
) -> tuple[WorldModelTournamentCandidate, ...]:
    baselineByEpisode = {record["episodeId"]: record for record in raw if record["modelId"] == spec.baselineModelId}
    drafts: list[dict] = []
    for model in candidates:
        records = [record for record in raw if record["modelId"] == model.modelId]
        loss, observationCount = _worldModelMeanLoss(records)
        baselineLoss, _ = _worldModelMeanLoss([baselineByEpisode[record["episodeId"]] for record in records])
        drafts.append(
            {
                "modelId": model.modelId,
                "modelVersion": _tournamentCandidateVersion(model),
                "candidateHash": _tournamentCandidateHash(model),
                "loss": loss,
                "baselineLoss": baselineLoss,
                "skillVsBaseline": _worldModelTournamentSkill(loss, baselineLoss),
                "originCount": len(records),
                "observationCount": observationCount,
            }
        )
    ranked = sorted(drafts, key=lambda row: (row["loss"], row["modelId"]))
    minimumLoss = float(ranked[0]["loss"])
    rawWeights = {
        row["modelId"]: math.exp(-(float(row["loss"]) - minimumLoss) / spec.weightTemperature) for row in ranked
    }
    weightTotal = sum(rawWeights.values())
    return tuple(
        WorldModelTournamentCandidate(
            **row,
            comparisonWeight=rawWeights[row["modelId"]] / weightTotal,
            rank=index,
        )
        for index, row in enumerate(ranked, 1)
    )


def _worldModelOriginSlices(
    raw: list[dict],
    spec: WorldModelTournamentSpec,
) -> list[WorldModelSliceScore]:
    baselineByEpisode = {record["episodeId"]: record for record in raw if record["modelId"] == spec.baselineModelId}
    slices: list[WorldModelSliceScore] = []
    for record in raw:
        baseline = baselineByEpisode[record["episodeId"]]
        loss = float(record["lossSum"]) / int(record["observationCount"])
        baselineLoss = float(baseline["lossSum"]) / int(baseline["observationCount"])
        slices.append(
            WorldModelSliceScore(
                modelId=record["modelId"],
                modelVersion=record["modelVersion"],
                scope="origin",
                scopeKey=record["episodeId"],
                loss=loss,
                baselineLoss=baselineLoss,
                skillVsBaseline=_worldModelTournamentSkill(loss, baselineLoss),
                observationCount=record["observationCount"],
                runHash=record["runHash"],
                resultHash=record["resultHash"],
                executableHash=record["executableHash"],
            )
        )
    return slices


def _worldModelHorizonSlices(
    candidates: tuple[WorldModel | OperatingTransmissionCandidate, ...],
    raw: list[dict],
    spec: WorldModelTournamentSpec,
) -> list[WorldModelSliceScore]:
    slices: list[WorldModelSliceScore] = []
    maximumHorizon = max(len(record["stepLosses"]) for record in raw)
    for step in range(maximumHorizon):
        for model in candidates:
            modelLosses = [
                record["stepLosses"][step]
                for record in raw
                if record["modelId"] == model.modelId and len(record["stepLosses"]) > step
            ]
            baselineLosses = [
                record["stepLosses"][step]
                for record in raw
                if record["modelId"] == spec.baselineModelId and len(record["stepLosses"]) > step
            ]
            loss = sum(modelLosses) / len(modelLosses)
            baselineLoss = sum(baselineLosses) / len(baselineLosses)
            slices.append(
                WorldModelSliceScore(
                    modelId=model.modelId,
                    modelVersion=_tournamentCandidateVersion(model),
                    scope="horizon",
                    scopeKey=str(step + 1),
                    loss=loss,
                    baselineLoss=baselineLoss,
                    skillVsBaseline=_worldModelTournamentSkill(loss, baselineLoss),
                    observationCount=len(modelLosses) * len(spec.metrics),
                )
            )
    return slices


def _worldModelRegimeSlices(
    candidates: tuple[WorldModel | OperatingTransmissionCandidate, ...],
    episodes: tuple[WorldModelReplayEpisode | OperatingModelReplayEpisode, ...],
    raw: list[dict],
    spec: WorldModelTournamentSpec,
) -> list[WorldModelSliceScore]:
    slices: list[WorldModelSliceScore] = []
    for regime in sorted({episode.regime for episode in episodes}):
        for model in candidates:
            modelRecords = [
                record for record in raw if record["modelId"] == model.modelId and record["regime"] == regime
            ]
            baselineRecords = [
                record for record in raw if record["modelId"] == spec.baselineModelId and record["regime"] == regime
            ]
            loss, observationCount = _worldModelMeanLoss(modelRecords)
            baselineLoss, _ = _worldModelMeanLoss(baselineRecords)
            slices.append(
                WorldModelSliceScore(
                    modelId=model.modelId,
                    modelVersion=_tournamentCandidateVersion(model),
                    scope="regime",
                    scopeKey=regime,
                    loss=loss,
                    baselineLoss=baselineLoss,
                    skillVsBaseline=_worldModelTournamentSkill(loss, baselineLoss),
                    observationCount=observationCount,
                )
            )
    return slices


def _worldModelTournamentSlices(
    candidates: tuple[WorldModel | OperatingTransmissionCandidate, ...],
    episodes: tuple[WorldModelReplayEpisode | OperatingModelReplayEpisode, ...],
    raw: list[dict],
    spec: WorldModelTournamentSpec,
) -> tuple[WorldModelSliceScore, ...]:
    slices = [
        *_worldModelOriginSlices(raw, spec),
        *_worldModelHorizonSlices(candidates, raw, spec),
        *_worldModelRegimeSlices(candidates, episodes, raw, spec),
    ]
    scopeOrder = {"origin": 0, "horizon": 1, "regime": 2}
    slices.sort(key=lambda row: (scopeOrder[row.scope], row.scopeKey, row.modelId))
    return tuple(slices)


def _buildWorldModelTournamentReport(
    candidates: tuple[WorldModel | OperatingTransmissionCandidate, ...],
    episodes: tuple[WorldModelReplayEpisode | OperatingModelReplayEpisode, ...],
    episodeHashes: tuple[str, ...],
    raw: list[dict],
    spec: WorldModelTournamentSpec,
    *,
    evaluationMode: str,
    baseWarnings: tuple[str, ...],
) -> WorldModelTournamentReport:
    candidateRows = _worldModelTournamentCandidates(candidates, raw, spec)
    slices = _worldModelTournamentSlices(candidates, episodes, raw, spec)
    best = candidateRows[0]
    warnings = list(baseWarnings)
    selectionStatus = "eligible"
    selectedModelId = best.modelId
    if len(episodes) < spec.minOrigins:
        selectionStatus = "insufficientEvidence"
        selectedModelId = ""
        warnings.append("minimumOriginCountNotMet")
    elif best.modelId == spec.baselineModelId:
        selectionStatus = "baselineBest"
        selectedModelId = ""
        warnings.append("baselineRemainsBest")
    elif best.skillVsBaseline <= spec.minSkillVsBaseline:
        selectionStatus = "noSkillGain"
        selectedModelId = ""
        warnings.append("minimumSkillGainNotMet")
    warningTuple = tuple(warnings)
    reportPayload = {
        "schemaVersion": "world-model-tournament-v1",
        "evaluationMode": evaluationMode,
        "status": "documented",
        "admissionStatus": "notAdmitted",
        "selectionStatus": selectionStatus,
        "selectedModelId": selectedModelId,
        "baselineModelId": spec.baselineModelId,
        "episodeHashes": episodeHashes,
        "spec": spec,
        "candidates": candidateRows,
        "slices": slices,
        "warnings": warningTuple,
    }
    report = WorldModelTournamentReport(
        tournamentHash=canonicalPayloadHash(reportPayload),
        evaluationMode=evaluationMode,
        status="documented",
        admissionStatus="notAdmitted",
        selectionStatus=selectionStatus,
        selectedModelId=selectedModelId,
        baselineModelId=spec.baselineModelId,
        episodeCount=len(episodes),
        modelCount=len(candidates),
        episodeHashes=episodeHashes,
        candidates=candidateRows,
        slices=slices,
        warnings=warningTuple,
    )
    return replace(report, comparisonHash=_worldModelTournamentComparisonHash(report))


def runWorldModelTournament(
    candidates: tuple[WorldModel, ...],
    episodes: tuple[WorldModelReplayEpisode, ...],
    spec: WorldModelTournamentSpec,
) -> WorldModelTournamentReport:
    """동일한 과거 episode에서 세계모델을 실행하고 손실과 절편별 skill을 비교한다.

    Args:
        candidates: 동일 변수, 행동, 시간 계약을 가진 둘 이상의 세계모델.
        episodes: origin 상태, 실현 경로, 관측 행동, 실제 상태를 가진 replay 묶음.
        spec: 채점 지표, 척도, baseline, 표본 문턱, 비교 가중 규칙.

    Returns:
        전체 후보 순위와 origin, horizon, regime 절편을 가진 documented report.

    Raises:
        WorldModelTournamentError: 시간 인과, 공통 계약, episode, 채점 규칙이 잘못된 경우.

    Example:
        ``report = runWorldModelTournament((baseline, candidate), episodes, spec)``
    """

    candidateTuple = tuple(sorted(candidates, key=lambda model: model.modelId))
    episodeTuple = tuple(sorted(episodes, key=lambda episode: (episode.originAsOf, episode.episodeId)))
    _validateWorldModelTournamentInputs(candidateTuple, episodeTuple, spec)
    raw = _worldModelTournamentRawScores(candidateTuple, episodeTuple, spec)
    episodeHashes = tuple(canonicalPayloadHash(_worldReplayEpisodePayload(episode)) for episode in episodeTuple)
    return _buildWorldModelTournamentReport(
        candidateTuple,
        episodeTuple,
        episodeHashes,
        raw,
        spec,
        evaluationMode=WORLD_TOURNAMENT_EVALUATION_MODE,
        baseWarnings=(
            "realizedPathIsConditionalLawTest",
            "comparisonWeightsAreNotProbabilities",
            "modelTournamentNotAdmission",
        ),
    )


def runOperatingModelTournament(
    candidates: tuple[OperatingTransmissionCandidate, ...],
    episodes: tuple[OperatingModelReplayEpisode, ...],
    spec: WorldModelTournamentSpec,
    *,
    debtLimit: float,
    maxFinancing: float,
    maxInvestment: float,
) -> WorldModelTournamentReport:
    """Run admitted transmission candidates from realized drivers through the operating world.

    Args:
        candidates: Two or more signed coefficient candidates that bridge driver factors
            into operating shocks.
        episodes: PIT operating states, one realized driver path, observed actions, and
            actual step outcomes for each historical origin.
        spec: Shared metrics, scales, baseline id, sample floor, and comparison rule.
        debtLimit: Hard operating-world debt constraint.
        maxFinancing: Per-step borrow and repay bound.
        maxInvestment: Per-step capacity investment bound.

    Returns:
        Documented tournament report with overall, origin, horizon, and regime scores.

    Raises:
        WorldModelTournamentError: If PIT timing, realized path status, coefficient
            admission, factor meaning, horizon, or scoring contracts drift.

    Example:
        ``report = runOperatingModelTournament(candidates, episodes, spec, debtLimit=1000, maxFinancing=100, maxInvestment=100)``
    """

    limits = (
        _tournamentFinite(debtLimit, "debtLimit"),
        _tournamentFinite(maxFinancing, "maxFinancing"),
        _tournamentFinite(maxInvestment, "maxInvestment"),
    )
    if any(value < 0 for value in limits):
        raise WorldModelTournamentError("operating tournament limits must be nonnegative")
    candidateTuple = tuple(sorted(candidates, key=lambda candidate: candidate.modelId))
    episodeTuple = tuple(sorted(episodes, key=lambda episode: (episode.originAsOf, episode.episodeId)))
    _validateOperatingModelTournamentInputs(candidateTuple, episodeTuple, spec)
    raw = _operatingModelTournamentRawScores(
        candidateTuple,
        episodeTuple,
        spec,
        debtLimit=limits[0],
        maxFinancing=limits[1],
        maxInvestment=limits[2],
    )
    episodeHashes = tuple(canonicalPayloadHash(_operatingReplayEpisodePayload(episode)) for episode in episodeTuple)
    return _buildWorldModelTournamentReport(
        candidateTuple,
        episodeTuple,
        episodeHashes,
        raw,
        spec,
        evaluationMode=OPERATING_MODEL_TOURNAMENT_EVALUATION_MODE,
        baseWarnings=(
            "realizedDriverPathIsRetrospectiveModelTest",
            "transmissionComparisonWeightsAreNotProbabilities",
            "modelTournamentNotAdmission",
        ),
    )


def _validTournamentDigest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _validateModelUncertaintyTournament(
    candidates: tuple[OperatingTransmissionCandidate, ...],
    tournament: WorldModelTournamentReport,
) -> dict[str, WorldModelTournamentCandidate]:
    if tournament.evaluationMode != OPERATING_MODEL_TOURNAMENT_EVALUATION_MODE:
        raise WorldModelTournamentError("model uncertainty needs an operating model tournament")
    if tournament.status != "documented" or tournament.admissionStatus != "notAdmitted":
        raise WorldModelTournamentError("model tournament must remain documented and not admitted")
    if tournament.selectionStatus != "eligible":
        raise WorldModelTournamentError("model tournament weights require eligible evidence")
    if not _validTournamentDigest(tournament.tournamentHash):
        raise WorldModelTournamentError("model tournament hash is invalid")
    if not _validTournamentDigest(
        tournament.comparisonHash
    ) or tournament.comparisonHash != _worldModelTournamentComparisonHash(tournament):
        raise WorldModelTournamentError("model tournament comparison contract drifted")
    if tournament.modelCount != len(candidates) or len(tournament.candidates) != len(candidates):
        raise WorldModelTournamentError("model tournament candidate count drifted")
    rowById = {row.modelId: row for row in tournament.candidates}
    if len(rowById) != len(tournament.candidates):
        raise WorldModelTournamentError("model tournament candidate ids must be unique")
    if set(rowById) != {candidate.modelId for candidate in candidates}:
        raise WorldModelTournamentError("model tournament candidate identities drifted")
    weightTotal = 0.0
    for candidate in candidates:
        _validateOperatingCandidate(candidate)
        row = rowById[candidate.modelId]
        if row.modelVersion != candidate.modelVersion:
            raise WorldModelTournamentError("model tournament candidate version drifted")
        if row.candidateHash != _tournamentCandidateHash(candidate):
            raise WorldModelTournamentError("model tournament candidate content drifted")
        if not _validTournamentDigest(row.candidateHash):
            raise WorldModelTournamentError("model tournament candidate hash is invalid")
        weight = _tournamentFinite(row.comparisonWeight, f"comparison weight {row.modelId}")
        if weight <= 0:
            raise WorldModelTournamentError("model comparison weights must be positive")
        weightTotal += weight
    if not math.isclose(weightTotal, 1.0, rel_tol=1e-12, abs_tol=1e-12):
        raise WorldModelTournamentError("model comparison weights must sum to one")
    return rowById


def _validateModelUncertaintyTemplates(
    entityId: str,
    candidates: tuple[OperatingTransmissionCandidate, ...],
    cases: tuple[OperatingScenarioCase, ...],
    strategies: tuple[StrategySpec, ...],
    objectiveIndex: int,
) -> None:
    if not entityId:
        raise WorldModelTournamentError("model uncertainty entity id is required")
    if len(candidates) < 2 or len({candidate.modelId for candidate in candidates}) != len(candidates):
        raise WorldModelTournamentError("model uncertainty needs unique model candidates")
    if len(cases) < 2 or len({case.caseId for case in cases}) != len(cases):
        raise WorldModelTournamentError("model uncertainty needs unique assumption cases")
    if len(strategies) < 2 or len({strategy.strategyId for strategy in strategies}) != len(strategies):
        raise WorldModelTournamentError("model uncertainty needs unique strategies")
    if objectiveIndex < 0:
        raise WorldModelTournamentError("model uncertainty objective index must be nonnegative")
    for case in cases:
        if case.exposures or case.coefficientBindings:
            raise WorldModelTournamentError("assumption case must not embed a transmission model")
        if case.policyAdmissionEvidence is not None:
            raise WorldModelTournamentError("model uncertainty cannot consume policy admission evidence")
        if case.operatingPathAdmissionReceiptId or case.operatingPathCertificateId:
            raise WorldModelTournamentError("model uncertainty cannot consume operating path admission")


def _modelUncertaintyCandidateCases(
    candidate: OperatingTransmissionCandidate,
    cases: tuple[OperatingScenarioCase, ...],
    tournamentHash: str,
) -> tuple[OperatingScenarioCase, ...]:
    candidateHash = _tournamentCandidateHash(candidate)
    rows = []
    for case in cases:
        if case.admissionVerifier is not None and case.admissionVerifier is not candidate.admissionVerifier:
            raise WorldModelTournamentError("assumption case and model candidate admission verifiers differ")
        refs = tuple(
            dict.fromkeys(
                (
                    *case.refs,
                    *candidate.refs,
                    f"modelCandidate:{candidateHash}",
                    f"modelTournament:{tournamentHash}",
                )
            )
        )
        rows.append(
            replace(
                case,
                exposures=candidate.exposures,
                coefficientBindings=candidate.coefficientBindings,
                admissionVerifier=candidate.admissionVerifier,
                policyAdmissionEvidence=None,
                operatingPathAdmissionReceiptId="",
                operatingPathCertificateId="",
                refs=refs,
            )
        )
    return tuple(rows)


def _runModelUncertaintyExperiments(
    entityId: str,
    inputs: OperatingWorldInputs,
    candidates: tuple[OperatingTransmissionCandidate, ...],
    rowsById: Mapping[str, WorldModelTournamentCandidate],
    cases: tuple[OperatingScenarioCase, ...],
    strategies: tuple[StrategySpec, ...],
    tournamentHash: str,
    *,
    debtLimit: float,
    maxFinancing: float,
    maxInvestment: float,
    objectiveIndex: int,
    traceLimit: int | None,
) -> tuple[tuple[OperatingTransmissionCandidate, WorldModelTournamentCandidate, ConditionalScenarioExperiment], ...]:
    from dartlab.simulate.scenarioComposition import runConditionalScenarioExperiment

    rows = []
    for candidate in candidates:
        candidateCases = _modelUncertaintyCandidateCases(candidate, cases, tournamentHash)
        experiment = runConditionalScenarioExperiment(
            entityId,
            inputs,
            candidateCases,
            strategies,
            debtLimit=debtLimit,
            maxFinancing=maxFinancing,
            maxInvestment=maxInvestment,
            objectiveIndex=objectiveIndex,
            traceLimit=traceLimit,
        )
        rows.append((candidate, rowsById[candidate.modelId], experiment))
    return tuple(rows)


def _modelUncertaintyCells(
    experiments: tuple[
        tuple[OperatingTransmissionCandidate, WorldModelTournamentCandidate, ConditionalScenarioExperiment], ...
    ],
) -> tuple[ModelUncertaintyCell, ...]:
    rows = []
    for candidate, tournamentRow, experiment in experiments:
        for cell in experiment.cells:
            rows.append(
                ModelUncertaintyCell(
                    modelId=candidate.modelId,
                    modelVersion=candidate.modelVersion,
                    candidateHash=tournamentRow.candidateHash,
                    comparisonWeight=tournamentRow.comparisonWeight,
                    caseId=cell.caseId,
                    label=cell.label,
                    strategyId=cell.strategyId,
                    score=cell.score,
                    regret=cell.regret,
                    feasible=cell.feasible,
                    breachCount=cell.breachCount,
                    scoreLeader=cell.scoreLeader,
                    assumptionSetHash=cell.assumptionSetHash,
                    sourceExperimentHash=experiment.experimentHash,
                    runHash=cell.runHash,
                    resultHash=cell.resultHash,
                )
            )
    rows.sort(key=lambda row: (row.caseId, row.modelId, row.strategyId))
    return tuple(rows)


def _modelCaseLeaderCounts(cells: tuple[ModelUncertaintyCell, ...]) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = {}
    for cell in cells:
        if cell.scoreLeader:
            key = (cell.modelId, cell.caseId)
            counts[key] = counts.get(key, 0) + 1
    return counts


def _modelUncertaintyStrategySummaries(
    cells: tuple[ModelUncertaintyCell, ...],
    strategyIds: tuple[str, ...],
    scenarioCount: int,
) -> tuple[ModelUncertaintyStrategySummary, ...]:
    leaderCounts = _modelCaseLeaderCounts(cells)
    summaries = []
    for strategyId in strategyIds:
        strategyCells = tuple(cell for cell in cells if cell.strategyId == strategyId)
        contributions = tuple((cell, cell.comparisonWeight / scenarioCount) for cell in strategyCells)
        worst = min(strategyCells, key=lambda cell: (cell.score, cell.modelId, cell.caseId))
        summaries.append(
            ModelUncertaintyStrategySummary(
                strategyId=strategyId,
                weightedMeanScore=sum(cell.score * weight for cell, weight in contributions),
                weightedMeanRegret=sum(cell.regret * weight for cell, weight in contributions),
                worstScore=worst.score,
                worstRegret=max(cell.regret for cell in strategyCells),
                worstModelId=worst.modelId,
                worstCaseId=worst.caseId,
                leaderWeightShare=sum(
                    (
                        weight / leaderCounts[(cell.modelId, cell.caseId)]
                        for cell, weight in contributions
                        if cell.scoreLeader
                    ),
                    0.0,
                ),
                feasibleWeightShare=sum((weight for cell, weight in contributions if cell.feasible), 0.0),
                breachCount=sum(cell.breachCount for cell in strategyCells),
                cellCount=len(strategyCells),
            )
        )
    return tuple(summaries)


def _leaderRowsByModel(
    caseCells: tuple[ModelUncertaintyCell, ...],
) -> tuple[tuple[str, tuple[str, ...], float, float], ...]:
    rows = []
    for modelId in sorted({cell.modelId for cell in caseCells}):
        modelCells = tuple(cell for cell in caseCells if cell.modelId == modelId)
        leaderScore = max(cell.score for cell in modelCells)
        leaders = tuple(sorted(cell.strategyId for cell in modelCells if cell.scoreLeader))
        distinctScores = sorted({cell.score for cell in modelCells}, reverse=True)
        margin = leaderScore - distinctScores[1] if len(distinctScores) > 1 else 0.0
        rows.append((modelId, leaders, leaderScore, margin))
    return tuple(rows)


def _modelUncertaintyCaseFragilities(
    cells: tuple[ModelUncertaintyCell, ...],
    caseIds: tuple[str, ...],
    weightsById: Mapping[str, float],
    strategyIds: tuple[str, ...],
) -> tuple[ModelUncertaintyCaseFragility, ...]:
    rows = []
    for caseId in caseIds:
        caseCells = tuple(cell for cell in cells if cell.caseId == caseId)
        leaderRows = _leaderRowsByModel(caseCells)
        leaderSets = tuple(set(leaders) for _, leaders, _, _ in leaderRows)
        stableLeaders = tuple(sorted(set.intersection(*leaderSets)))
        leaderShares = {
            strategyId: sum(
                (weightsById[modelId] / len(leaders) for modelId, leaders, _, _ in leaderRows if strategyId in leaders),
                0.0,
            )
            for strategyId in strategyIds
        }
        worstModelId, _, worstLeaderScore, _ = min(leaderRows, key=lambda row: (row[2], row[0]))
        modelSpreads = []
        for strategyId in strategyIds:
            scores = tuple(cell.score for cell in caseCells if cell.strategyId == strategyId)
            modelSpreads.append(max(scores) - min(scores))
        rows.append(
            ModelUncertaintyCaseFragility(
                caseId=caseId,
                label=caseCells[0].label,
                leadershipReversal=len({leaders for _, leaders, _, _ in leaderRows}) > 1,
                stableLeaderStrategies=stableLeaders,
                leaderByModel=tuple((modelId, leaders) for modelId, leaders, _, _ in leaderRows),
                leaderWeightShares=tuple((strategyId, leaderShares[strategyId]) for strategyId in strategyIds),
                worstModelId=worstModelId,
                worstModelLeaderScore=worstLeaderScore,
                worstLeaderMargin=min(margin for _, _, _, margin in leaderRows),
                maxStrategyScoreSpread=max(modelSpreads),
            )
        )
    return tuple(rows)


def runModelUncertaintyScenarioExperiment(
    entityId: str,
    inputs: OperatingWorldInputs,
    cases: tuple[OperatingScenarioCase, ...],
    strategies: tuple[StrategySpec, ...],
    candidates: tuple[OperatingTransmissionCandidate, ...],
    tournament: WorldModelTournamentReport,
    *,
    debtLimit: float,
    maxFinancing: float,
    maxInvestment: float,
    objectiveIndex: int = 0,
    traceLimit: int | None = None,
) -> ModelUncertaintyScenarioExperiment:
    """Run every strategy under every assumption case and admitted transmission candidate.

    Historical tournament comparison weights summarize results but remain explicitly
    non-probabilistic. The result preserves worst-model outcomes and case-level strategy
    leadership reversals and never emits a recommendation or admission artifact.

    Args:
        entityId: Company or security identifier for the shared operating state.
        inputs: Point-in-time operating state used by every model and case.
        cases: Two or more future driver assumption cases without embedded transmission laws.
        strategies: Two or more shared action paths evaluated in every cell.
        candidates: Signed measured-association transmission candidates from the tournament.
        tournament: Eligible operating model tournament that exactly binds the candidates.
        debtLimit: Hard debt constraint for every operating-world execution.
        maxFinancing: Per-step borrow and repay bound.
        maxInvestment: Per-step capacity investment bound.
        objectiveIndex: Operating objective used for scalar score, regret, and leader rows.
        traceLimit: Optional retained trace cap within each source experiment.

    Returns:
        Documented model uncertainty ledger with all cells, weighted summaries, worst-model
        coordinates, case fragility, source experiment hashes, and recommendation blockers.

    Capabilities:
        Executes the full model by assumption by strategy matrix, retains source run
        hashes, and reports weighted summaries, worst models, and leadership reversals.

    AIContext:
        Use after an operating model tournament when an agent must compare strategies
        without silently treating retrospective comparison weights as probabilities.

    Guide:
        Supply law-free assumption cases. Every candidate must exactly match its
        tournament id, version, and content hash. Cases receive candidate laws only
        inside this execution boundary.

    When:
        Call when future strategy conclusions may change across plausible admitted
        transmission coefficient candidates.

    How:
        Run ``runOperatingModelTournament`` first, build at least two future cases and
        strategies, then pass the unchanged candidates and tournament report here.

    Requires:
        No network or API key. Requires admitted coefficient receipts accessible through
        each candidate verifier and point-in-time operating inputs.

    Raises:
        WorldModelTournamentError: If identities, content hashes, comparison weights,
            assumption boundaries, or experiment dimensions drift.
        ScenarioCompositionError: If a candidate-specific conditional experiment violates
            driver, bridge, strategy, or operating-world contracts.

    Example:
        ``report = runModelUncertaintyScenarioExperiment("005930", inputs, cases, strategies, candidates, tournament, debtLimit=1000, maxFinancing=100, maxInvestment=100)``

    SeeAlso:
        ``runOperatingModelTournament`` and
        ``dartlab.simulate.scenarioComposition.runConditionalScenarioExperiment``.
    """

    candidateTuple = tuple(sorted(candidates, key=lambda candidate: candidate.modelId))
    caseTuple = tuple(sorted(cases, key=lambda case: case.caseId))
    strategyTuple = tuple(sorted(strategies, key=lambda strategy: strategy.strategyId))
    _validateModelUncertaintyTemplates(entityId, candidateTuple, caseTuple, strategyTuple, objectiveIndex)
    rowsById = _validateModelUncertaintyTournament(candidateTuple, tournament)
    experiments = _runModelUncertaintyExperiments(
        entityId,
        inputs,
        candidateTuple,
        rowsById,
        caseTuple,
        strategyTuple,
        tournament.tournamentHash,
        debtLimit=debtLimit,
        maxFinancing=maxFinancing,
        maxInvestment=maxInvestment,
        objectiveIndex=objectiveIndex,
        traceLimit=traceLimit,
    )
    cells = _modelUncertaintyCells(experiments)
    strategyIds = tuple(strategy.strategyId for strategy in strategyTuple)
    caseIds = tuple(case.caseId for case in caseTuple)
    weightsById = {modelId: row.comparisonWeight for modelId, row in rowsById.items()}
    summaries = _modelUncertaintyStrategySummaries(cells, strategyIds, len(caseTuple))
    fragilities = _modelUncertaintyCaseFragilities(cells, caseIds, weightsById, strategyIds)
    sourceExperimentHashes = tuple(
        (candidate.modelId, experiment.experimentHash) for candidate, _, experiment in experiments
    )
    blockedReasons = (
        "conditionalModelUncertaintyNoRecommendation",
        "modelWeightsNotProbabilities",
        "tournamentNotAdmission",
    )
    warnings = (
        "modelComparisonWeightsAreNotProbabilities",
        "modelUncertaintyExperimentNotAdmission",
        "retrospectiveModelWeightsAppliedToConditionalCases",
        "scoreLeaderNotRecommendation",
    )
    payload = {
        "schemaVersion": MODEL_UNCERTAINTY_SCENARIO_EXPERIMENT_VERSION,
        "entityId": entityId,
        "tournamentHash": tournament.tournamentHash,
        "tournamentComparisonHash": tournament.comparisonHash,
        "tournamentEvaluationMode": tournament.evaluationMode,
        "tournamentSelectionStatus": tournament.selectionStatus,
        "modelIds": tuple(candidate.modelId for candidate in candidateTuple),
        "modelVersions": tuple(candidate.modelVersion for candidate in candidateTuple),
        "candidateHashes": tuple(rowsById[candidate.modelId].candidateHash for candidate in candidateTuple),
        "modelComparisonWeights": tuple(
            (candidate.modelId, rowsById[candidate.modelId].comparisonWeight) for candidate in candidateTuple
        ),
        "sourceExperimentHashes": sourceExperimentHashes,
        "limits": {
            "debtLimit": float(debtLimit),
            "maxFinancing": float(maxFinancing),
            "maxInvestment": float(maxInvestment),
            "objectiveIndex": objectiveIndex,
            "traceLimit": traceLimit,
        },
        "cells": cells,
        "strategySummaries": summaries,
        "caseFragilities": fragilities,
        "blockedReasons": blockedReasons,
        "warnings": warnings,
    }
    return ModelUncertaintyScenarioExperiment(
        uncertaintyHash=canonicalPayloadHash(payload),
        schemaVersion=MODEL_UNCERTAINTY_SCENARIO_EXPERIMENT_VERSION,
        status="documented",
        admissionStatus="notAdmitted",
        recommendationCeiling="conditionalOnly",
        recommendation=None,
        entityId=entityId,
        tournamentHash=tournament.tournamentHash,
        tournamentComparisonHash=tournament.comparisonHash,
        tournamentEvaluationMode=tournament.evaluationMode,
        tournamentSelectionStatus=tournament.selectionStatus,
        modelCount=len(candidateTuple),
        scenarioCount=len(caseTuple),
        strategyCount=len(strategyTuple),
        cellCount=len(cells),
        modelIds=tuple(candidate.modelId for candidate in candidateTuple),
        modelVersions=tuple(candidate.modelVersion for candidate in candidateTuple),
        candidateHashes=tuple(rowsById[candidate.modelId].candidateHash for candidate in candidateTuple),
        modelComparisonWeights=tuple(
            (candidate.modelId, rowsById[candidate.modelId].comparisonWeight) for candidate in candidateTuple
        ),
        sourceExperimentHashes=sourceExperimentHashes,
        cells=cells,
        strategySummaries=summaries,
        caseFragilities=fragilities,
        blockedReasons=blockedReasons,
        warnings=warnings,
    )
