"""Objective aggregation, constraint breaches, and the run decision verdict.

전이 실행과 "그래서 어느 전략이 나은가"는 서로 다른 관심사다. 전자는 법칙을 순서대로
굴리는 일이고, 후자는 목적 계약을 검사하고 경로값을 위험 선호대로 접어 판정과 경고를
만드는 일이다. 한 함수에 붙어 있으면 위험 집계 규칙을 하나 고칠 때마다 실행 루프 전체를
다시 읽어야 한다.

`_ObjectiveLedger` 가 그 경계다. 실행기는 경로 trace 하나를 넘길 뿐이고, 전량 보존이든
compact 모드(SQLite spill)든 어떤 방식으로 접히는지는 원장이 혼자 안다.
"""

from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from typing import Mapping

from dartlab.simulate.worldTypes import (
    ConstraintSpec,
    ObjectiveSpec,
    PathTrace,
    ScenarioPath,
    SimulationBlocked,
    SimulationSpecError,
    StrategyEvaluation,
    StrategySpec,
)


class _CvarSpill:
    """compact 실행의 경로값을 임시 SQLite 파일에 흘려 exact weighted CVaR을 집계한다."""

    def __init__(self) -> None:
        self._connection = sqlite3.connect("")
        self._connection.execute("PRAGMA journal_mode=OFF")
        self._connection.execute("PRAGMA synchronous=OFF")
        self._connection.execute(
            "CREATE TABLE score (strategyIndex INTEGER, objectiveIndex INTEGER, ordinal INTEGER, value REAL, weight REAL)"
        )
        self._prepared = False

    def add(self, strategyIndex: int, objectiveIndex: int, ordinal: int, value: float, weight: float) -> None:
        """경로 목적값과 가중치를 메모리 대신 임시 저장소에 추가한다.

        Args:
            strategyIndex: 전략의 내부 순번.
            objectiveIndex: 목적 함수의 내부 순번.
            ordinal: 같은 값의 안정 정렬을 위한 경로 순번.
            value: 목적 함수 값.
            weight: 경로 가중치.

        Returns:
            없음.

        Raises:
            sqlite3.Error: 임시 저장소 쓰기에 실패한 경우.

        Example:
            ``spill.add(0, 0, 3, 12.5, 1.0)``
        """

        self._connection.execute(
            "INSERT INTO score VALUES (?, ?, ?, ?, ?)",
            (strategyIndex, objectiveIndex, ordinal, value, weight),
        )

    def weightedCvar(self, strategyIndex: int, objectiveIndex: int, tailFraction: float) -> float:
        """낮은 목적값 꼬리를 value와 ordinal 순으로 읽어 exact weighted CVaR을 반환한다.

        Args:
            strategyIndex: 집계할 전략 순번.
            objectiveIndex: 집계할 목적 함수 순번.
            tailFraction: 낮은 꼬리에 포함할 가중 비율.

        Returns:
            가중 꼬리 평균 값.

        Raises:
            SimulationSpecError: 양수 가중치가 없어 CVaR을 계산할 수 없는 경우.
            sqlite3.Error: 임시 저장소 읽기 또는 인덱스 생성에 실패한 경우.

        Example:
            ``score = spill.weightedCvar(0, 0, 0.05)``
        """

        if not self._prepared:
            self._connection.execute(
                "CREATE INDEX score_order ON score (strategyIndex, objectiveIndex, value, ordinal)"
            )
            self._prepared = True
        totalWeight = float(
            self._connection.execute(
                "SELECT SUM(weight) FROM score WHERE strategyIndex=? AND objectiveIndex=?",
                (strategyIndex, objectiveIndex),
            ).fetchone()[0]
        )
        target = totalWeight * tailFraction
        used = 0.0
        total = 0.0
        rows = self._connection.execute(
            "SELECT value, weight FROM score WHERE strategyIndex=? AND objectiveIndex=? ORDER BY value, ordinal",
            (strategyIndex, objectiveIndex),
        )
        for value, weight in rows:
            take = min(float(weight), target - used)
            if take > 0:
                total += float(value) * take
                used += take
            if used >= target - 1e-12:
                break
        if used <= 0:
            raise SimulationSpecError("compact cvar spill has no positive weight")
        return total / used

    def close(self) -> None:
        """임시 SQLite 저장소를 닫고 운영체제가 파일을 회수하게 한다.

        Args:
            없음.

        Returns:
            없음.

        Raises:
            sqlite3.Error: 연결 종료에 실패한 경우.

        Example:
            ``spill.close()``
        """

        connection = getattr(self, "_connection", None)
        if connection is not None:
            connection.close()
            self._connection = None

    def __del__(self) -> None:
        self.close()


def _constraintBreaches(
    constraints: tuple[ConstraintSpec, ...], values: Mapping[str, float], scope: str
) -> tuple[str, ...]:
    out: list[str] = []
    for spec in constraints:
        if spec.scope != scope:
            continue
        if spec.metric not in values:
            raise SimulationBlocked(f"constraint metric missing: {spec.metric}")
        value = values[spec.metric]
        if spec.operator == "ge":
            breached = value < spec.threshold
        elif spec.operator == "le":
            breached = value > spec.threshold
        else:
            raise SimulationSpecError(f"unknown constraint operator: {spec.operator}")
        if breached:
            out.append(f"{spec.metric}:{spec.operator}:{spec.threshold}")
    return tuple(out)


def _pathMetric(trace: PathTrace, objective: ObjectiveSpec) -> float:
    values = [step.after[objective.metric] for step in trace.steps]
    if objective.reducer == "terminal":
        value = values[-1]
    elif objective.reducer == "minimum":
        value = min(values)
    elif objective.reducer == "maximum":
        value = max(values)
    elif objective.reducer == "cumulative":
        value = sum(values)
    else:
        raise SimulationSpecError(f"unknown objective reducer: {objective.reducer}")
    if objective.direction == "maximize":
        return value
    if objective.direction == "minimize":
        return -value
    raise SimulationSpecError(f"unknown objective direction: {objective.direction}")


def _aggregate(values: list[float], weights: list[float], objective: ObjectiveSpec) -> float:
    if objective.risk == "worst":
        return min(values)
    if objective.risk == "average":
        total = sum(weights)
        return sum(value * weight for value, weight in zip(values, weights, strict=True)) / total
    if objective.risk == "cvar":
        if not 0 < objective.tailFraction <= 1:
            raise SimulationSpecError("tailFraction must be in (0, 1]")
        ordered = sorted(zip(values, weights, strict=True), key=lambda pair: pair[0])
        target = sum(weights) * objective.tailFraction
        used = 0.0
        total = 0.0
        for value, weight in ordered:
            take = min(weight, target - used)
            if take > 0:
                total += value * take
                used += take
            if used >= target - 1e-12:
                break
        return total / used
    raise SimulationSpecError(f"unknown objective risk: {objective.risk}")


def _pareto(evaluations: tuple[StrategyEvaluation, ...]) -> tuple[str, ...]:
    feasible = [evaluation for evaluation in evaluations if evaluation.feasible]
    frontier: list[str] = []
    for candidate in feasible:
        dominated = False
        for other in feasible:
            if other.strategyId == candidate.strategyId:
                continue
            noWorse = all(a >= b - 1e-12 for a, b in zip(other.objectiveScores, candidate.objectiveScores, strict=True))
            better = any(a > b + 1e-12 for a, b in zip(other.objectiveScores, candidate.objectiveScores, strict=True))
            if noWorse and better:
                dominated = True
                break
        if not dominated:
            frontier.append(candidate.strategyId)
    return tuple(sorted(frontier))


def _validateTraceLimit(traceLimit: int | None) -> None:
    """보존 상한이 실행 전에 의미 있는 값인지 확인한다."""

    if traceLimit is not None and (not isinstance(traceLimit, int) or traceLimit < 0):
        raise SimulationSpecError("traceLimit must be a nonnegative integer or None")


def _validateObjectiveContracts(objectives: tuple[ObjectiveSpec, ...], variableIds: set[str]) -> None:
    """목적 지표가 모델 변수이고 축약, 방향, 위험, 꼬리 비율이 지원 범위인지 본다."""

    for objective in objectives:
        if objective.metric not in variableIds:
            raise SimulationSpecError(f"unknown objective metric: {objective.metric}")
        if (
            objective.reducer not in {"terminal", "minimum", "maximum", "cumulative"}
            or objective.direction not in {"maximize", "minimize"}
            or objective.risk not in {"worst", "average", "cvar"}
        ):
            raise SimulationSpecError(f"invalid objective contract: {objective.metric}")
        if not math.isfinite(float(objective.tailFraction)) or not 0 < objective.tailFraction <= 1:
            raise SimulationSpecError(f"non-finite objective contract: {objective.metric}")


def _validateConstraintContracts(constraints: tuple[ConstraintSpec, ...], variableIds: set[str]) -> None:
    """제약 지표가 모델 변수이고 적용 범위와 임계가 유한한지 본다."""

    for constraint in constraints:
        if (
            constraint.metric not in variableIds
            or constraint.scope not in {"eachStep", "terminal"}
            or not math.isfinite(float(constraint.threshold))
        ):
            raise SimulationSpecError(f"invalid constraint: {constraint.metric}")


class _ObjectiveLedger:
    """경로 trace를 받아 전략별 목적 점수와 제약 위반 수로 접는 누적 원장이다."""

    def __init__(
        self,
        strategies: tuple[StrategySpec, ...],
        objectives: tuple[ObjectiveSpec, ...],
        weights: list[float],
        traceLimit: int | None,
        cvarSpill: _CvarSpill | None,
    ) -> None:
        self.objectives = objectives
        self.weights = weights
        self.traceLimit = traceLimit
        self.cvarSpill = cvarSpill
        self.pathValues: dict[str, list[list[float]]] = {
            strategy.strategyId: [[] for _ in objectives] for strategy in strategies
        }
        self.numerators: dict[str, list[float]] = {
            strategy.strategyId: [0.0 for _ in objectives] for strategy in strategies
        }
        self.denominators: dict[str, list[float]] = {
            strategy.strategyId: [0.0 for _ in objectives] for strategy in strategies
        }
        self.worst: dict[str, list[float]] = {
            strategy.strategyId: [math.inf for _ in objectives] for strategy in strategies
        }
        self.breachCounts = {strategy.strategyId: 0 for strategy in strategies}

    def record(self, strategyIndex: int, strategyId: str, pathIndex: int, trace: PathTrace) -> None:
        """한 경로 실행 결과를 위반 수와 목적별 누적치에 반영한다.

        Args:
            strategyIndex: 전략의 내부 순번.
            strategyId: 전략 식별자.
            pathIndex: 경로의 내부 순번이자 가중치 색인.
            trace: 해당 전략과 경로 조합의 전체 기간 trace.

        Returns:
            없음.

        Raises:
            SimulationSpecError: compact 모드인데 CVaR spill이 준비되지 않은 경우.

        Example:
            ``ledger.record(0, "baseline", 0, trace)``
        """

        self.breachCounts[strategyId] += sum(len(item.breaches) for item in trace.steps)
        for objectiveIndex, objective in enumerate(self.objectives):
            value = _pathMetric(trace, objective)
            weight = self.weights[pathIndex]
            if self.traceLimit is None:
                self.pathValues[strategyId][objectiveIndex].append(value)
            if objective.risk == "average":
                self.numerators[strategyId][objectiveIndex] += value * weight
                self.denominators[strategyId][objectiveIndex] += weight
            elif objective.risk == "worst":
                self.worst[strategyId][objectiveIndex] = min(self.worst[strategyId][objectiveIndex], value)
            elif objective.risk == "cvar" and self.traceLimit is not None:
                if self.cvarSpill is None:
                    raise SimulationSpecError("compact cvar spill was not initialized")
                self.cvarSpill.add(strategyIndex, objectiveIndex, pathIndex, value, weight)

    def _score(self, strategyIndex: int, strategyId: str, objectiveIndex: int, objective: ObjectiveSpec) -> float:
        """compact 모드에서 위험 선호별로 이미 접힌 누적치를 점수 하나로 읽어낸다."""

        if objective.risk == "average":
            numerator = self.numerators[strategyId][objectiveIndex]
            denominator = self.denominators[strategyId][objectiveIndex]
            return numerator / denominator
        if objective.risk == "worst":
            return self.worst[strategyId][objectiveIndex]
        if self.cvarSpill is None:
            raise SimulationSpecError("compact cvar spill was not initialized")
        return self.cvarSpill.weightedCvar(strategyIndex, objectiveIndex, objective.tailFraction)

    def evaluations(self, strategies: tuple[StrategySpec, ...]) -> list[StrategyEvaluation]:
        """누적 원장을 전략별 최종 점수와 실행 가능 여부로 확정한다.

        Args:
            strategies: 평가 대상 전략 묶음.

        Returns:
            전략 선언 순서를 보존한 평가 결과 목록.

        Raises:
            SimulationSpecError: 위험 선호가 지원 범위를 벗어난 경우.

        Example:
            ``evaluations = ledger.evaluations(strategies)``
        """

        out: list[StrategyEvaluation] = []
        for strategyIndex, strategy in enumerate(strategies):
            objectivePathValues: list[tuple[float, ...]] = []
            objectiveScores: list[float] = []
            for objectiveIndex, objective in enumerate(self.objectives):
                if self.traceLimit is None:
                    values = tuple(self.pathValues[strategy.strategyId][objectiveIndex])
                    objectivePathValues.append(values)
                    objectiveScores.append(_aggregate(list(values), self.weights, objective))
                else:
                    objectiveScores.append(self._score(strategyIndex, strategy.strategyId, objectiveIndex, objective))
            breachCount = self.breachCounts[strategy.strategyId]
            out.append(
                StrategyEvaluation(
                    strategyId=strategy.strategyId,
                    objectiveScores=tuple(objectiveScores),
                    pathValues=tuple(objectivePathValues) if self.traceLimit is None else (),
                    breachCount=breachCount,
                    feasible=breachCount == 0,
                )
            )
        return out


@dataclass(frozen=True)
class _QualificationIssues:
    """판정 등급을 조건부로 끌어내리는 근거 부족 항목을 한 자리에 모은다."""

    unqualifiedLaws: list[str]
    assumedLaws: list[str]
    assumedActions: list[str]
    assumedActionLaws: list[str]
    pathAdmissionIssues: list[str]
    parameterProvenanceIssues: list[str]
    undocumentedParameterPaths: list[str]


def _collectQualificationIssues(model, paths: tuple[ScenarioPath, ...]) -> _QualificationIssues:
    """법칙, 행동, 경로, 파라미터 provenance에서 근거가 모자란 항목을 훑어 모은다."""

    actionLaws = [law for law in model.laws if law.actionInputs]
    parameterPaths = tuple(path for path in paths if path.parameterDraws)
    return _QualificationIssues(
        unqualifiedLaws=[law.lawId for law in model.laws if law.status != "active"],
        assumedLaws=[law.lawId for law in model.laws if law.evidenceKind == "explicitAssumption"],
        assumedActions=[
            action.actionId
            for action in model.actions
            if action.effectEvidence not in {"identifiedIntervention", "accountingIdentity"}
        ],
        assumedActionLaws=[
            law.lawId for law in actionLaws if law.evidenceKind not in {"identifiedIntervention", "accountingIdentity"}
        ],
        pathAdmissionIssues=[path.pathId for path in paths if path.validationStatus != "admitted"],
        parameterProvenanceIssues=[
            path.pathId
            for path in parameterPaths
            if path.parameterDrawReceipt is None or path.parameterDrawReceipt.status != "admitted"
        ],
        undocumentedParameterPaths=[path.pathId for path in parameterPaths if path.parameterDrawReceipt is None],
    )


def _buildDecision(
    issues: _QualificationIssues,
    strategies: tuple[StrategySpec, ...],
    objectives: tuple[ObjectiveSpec, ...],
    inputWarnings: tuple[str, ...],
    traceLimit: int | None,
    retainedTraceCount: int,
    traceCount: int,
    policyAdmissionIssues: list[str],
) -> tuple[list[str], str, list[str]]:
    """근거 부족 항목을 사용자에게 보일 경고와 판정 등급으로 옮긴다."""

    warnings: list[str] = list(inputWarnings)
    if traceLimit is not None:
        warnings.append(
            f"compact trace retention: retained {retainedTraceCount} of {traceCount}; "
            "path-level objective values omitted"
        )
    if issues.unqualifiedLaws:
        warnings.append(f"unqualified laws: {','.join(issues.unqualifiedLaws)}")
    if issues.assumedLaws or issues.assumedActions or issues.assumedActionLaws:
        warnings.append("unvalidated transition or intervention effects are conditional assumptions")
    if issues.pathAdmissionIssues:
        warnings.append(f"paths are not admitted: {','.join(issues.pathAdmissionIssues)}")
    if issues.undocumentedParameterPaths:
        warnings.append("parameterMeasure:undocumented:" + ",".join(issues.undocumentedParameterPaths))
    elif issues.parameterProvenanceIssues:
        warnings.append("parameterMeasure:documentedOnly")
    if policyAdmissionIssues:
        warnings.append("policy evaluation certificate is unavailable; automatic recommendation is disabled")
    baselineIds = [strategy.strategyId for strategy in strategies if strategy.isBaseline]
    if objectives and (len(strategies) < 2 or not baselineIds):
        warnings.append("recommendation needs one baseline and at least one candidate")
    if not objectives:
        decisionStatus = "abstain"
        warnings.append("no objective was declared")
    elif (
        issues.unqualifiedLaws
        or issues.assumedLaws
        or issues.assumedActions
        or issues.assumedActionLaws
        or issues.pathAdmissionIssues
        or issues.parameterProvenanceIssues
        or policyAdmissionIssues
    ):
        decisionStatus = "conditionalOnly"
    elif len(objectives) > 1:
        decisionStatus = "paretoOnly"
        warnings.append("multiple objectives have no declared scalarization")
    else:
        decisionStatus = "comparable"
    return warnings, decisionStatus, baselineIds


def _selectRecommendation(
    decisionStatus: str,
    evaluations: list[StrategyEvaluation],
    pareto: tuple[str, ...],
    objectives: tuple[ObjectiveSpec, ...],
    strategies: tuple[StrategySpec, ...],
    baselineIds: list[str],
) -> str | None:
    """단일 목적에 baseline과 후보가 갖춰졌고 유일 승자가 프론티어에 있을 때만 추천한다."""

    if not (decisionStatus == "comparable" and len(objectives) == 1 and len(strategies) >= 2 and len(baselineIds) == 1):
        return None
    feasible = [evaluation for evaluation in evaluations if evaluation.feasible]
    if not feasible:
        return None
    best = max(evaluation.objectiveScores[0] for evaluation in feasible)
    winners = [evaluation.strategyId for evaluation in feasible if abs(evaluation.objectiveScores[0] - best) <= 1e-12]
    if len(winners) == 1 and winners[0] in pareto:
        return winners[0]
    return None


def _weightLabelFor(paths: tuple[ScenarioPath, ...]) -> str:
    """경로 집합이 공유하는 가중치 성격을 그대로 읽히는 라벨 하나로 바꾼다."""

    weightKinds = {path.weightKind for path in paths}
    if weightKinds == {"calibrated"}:
        return "calibratedScenarioMeasure"
    if weightKinds == {"empirical"}:
        return "historicalEpisodeMeasure"
    if weightKinds == {"resampled"}:
        return "empiricalResamplingMeasure"
    if weightKinds == {"unweighted"}:
        return "scenarioCoverage"
    return "subjectiveScenarioWeight"
