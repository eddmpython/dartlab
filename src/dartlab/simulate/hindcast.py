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
from dataclasses import dataclass
from datetime import datetime as _dt
from datetime import timedelta as _td
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

import numpy as np
import polars as pl

from dartlab.simulate import estimate as _estimate
from dartlab.simulate import lattice as _lattice
from dartlab.simulate import readingScorecard as _sc
from dartlab.simulate import scenarioSim as _ss
from dartlab.simulate import table as _table
from dartlab.simulate.factors import macroFactors
from dartlab.simulate.vintage import canonicalPayloadHash
from dartlab.simulate.world import ObjectiveSpec, ScenarioPath, StrategySpec, WorldModel, WorldState, simulateWorld
from dartlab.synth.expectationSpec import pinballLoss

H_STAR_RULES = "hstar-v1: env=|cov90-0.90|>0.10 첫 h, firm=t(IC)<2.0 첫 h. 곡선 통보고, 셀 선별 금지."
WORLD_TOURNAMENT_EVALUATION_MODE = "conditionalOnRealizedPath"
WORLD_TOURNAMENT_LOSS_RULE = "mean-normalized-squared-error-v1"
WORLD_TOURNAMENT_WEIGHT_RULE = "softmax-negative-loss-v1"


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


def _validateWorldModelCandidates(
    candidates: tuple[WorldModel, ...],
    spec: WorldModelTournamentSpec,
) -> None:
    if len(candidates) < 2:
        raise WorldModelTournamentError("world model tournament needs at least two candidates")
    modelIds = tuple(model.modelId for model in candidates)
    if len(set(modelIds)) != len(modelIds):
        raise WorldModelTournamentError("candidate model ids must be unique")
    if spec.baselineModelId not in modelIds:
        raise WorldModelTournamentError("baseline model is not a tournament candidate")
    sharedContract = canonicalPayloadHash(_worldModelSharedContractPayload(candidates[0]))
    if any(canonicalPayloadHash(_worldModelSharedContractPayload(model)) != sharedContract for model in candidates[1:]):
        raise WorldModelTournamentError("shared variable contract, action contract, and step contract required")
    variableById = {variable.variableId: variable for variable in candidates[0].variables}
    if any(metric not in variableById or variableById[metric].role == "shock" for metric in spec.metrics):
        raise WorldModelTournamentError("tournament metric is not a model output")


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
            stepLosses = tuple(
                sum(
                    ((float(predicted.after[metric]) - float(actual[metric])) / float(spec.metricScales[metric])) ** 2
                    for metric in spec.metrics
                )
                / len(spec.metrics)
                for predicted, actual in zip(trace.steps, episode.actualByStep, strict=True)
            )
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


def _worldModelTournamentCandidates(
    candidates: tuple[WorldModel, ...],
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
                "modelVersion": model.version,
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
    candidates: tuple[WorldModel, ...],
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
                    modelVersion=model.version,
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
    candidates: tuple[WorldModel, ...],
    episodes: tuple[WorldModelReplayEpisode, ...],
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
                    modelVersion=model.version,
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
    candidates: tuple[WorldModel, ...],
    episodes: tuple[WorldModelReplayEpisode, ...],
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
    candidateRows = _worldModelTournamentCandidates(candidateTuple, raw, spec)
    slices = _worldModelTournamentSlices(candidateTuple, episodeTuple, raw, spec)
    best = candidateRows[0]
    warnings = [
        "realizedPathIsConditionalLawTest",
        "comparisonWeightsAreNotProbabilities",
        "modelTournamentNotAdmission",
    ]
    selectionStatus = "eligible"
    selectedModelId = best.modelId
    if len(episodeTuple) < spec.minOrigins:
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
    episodeHashes = tuple(canonicalPayloadHash(_worldReplayEpisodePayload(episode)) for episode in episodeTuple)
    reportPayload = {
        "schemaVersion": "world-model-tournament-v1",
        "evaluationMode": WORLD_TOURNAMENT_EVALUATION_MODE,
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
    return WorldModelTournamentReport(
        tournamentHash=canonicalPayloadHash(reportPayload),
        evaluationMode=WORLD_TOURNAMENT_EVALUATION_MODE,
        status="documented",
        admissionStatus="notAdmitted",
        selectionStatus=selectionStatus,
        selectedModelId=selectedModelId,
        baselineModelId=spec.baselineModelId,
        episodeCount=len(episodeTuple),
        modelCount=len(candidateTuple),
        episodeHashes=episodeHashes,
        candidates=candidateRows,
        slices=slices,
        warnings=warningTuple,
    )
