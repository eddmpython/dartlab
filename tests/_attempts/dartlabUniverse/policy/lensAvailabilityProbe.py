"""Capability 존재와 환경별 Lens 실행 가능성을 분리해 검증한다.

Capabilities
    scalar, series, table, ranking, distribution, scenario output contract와 unit,
    coverage, missing policy, runtime, redistribution receipt를 lens별로 판정한다.

Args
    CLI 인자는 없다. live capability와 Skill OS catalog의 lens readiness를 센서스한다.

Returns
    :class:`CatalogLensReadinessReport`를 stdout JSON으로 출력한다.

Example
    ``uv run python -X utf8 tests/_attempts/dartlabUniverse/policy/lensAvailabilityProbe.py``

Guide
    capability나 skill이 존재한다는 이유만으로 public browser에서 실행 가능하다고
    추정하지 않는다. publicBrowser 선언과 reviewed receipt가 모두 필요하다.

When
    Universe Lens Tray registry 작성 전과 capability 또는 Skill OS 변경 시 사용한다.

How
    catalog readiness를 센서스하고 explicit LensSpec fixture를 환경별로 admission한다.

Requires
    live capability builder와 local Skill OS catalog를 읽는다.

See Also
    ``mainPlan/dartlab-universe/07-implementation-playbook.md`` U0-L01.

AIContext
    AI 역할: unavailable lens를 실행된 것처럼 표시하지 않고 missing payload를 0으로
    바꾸지 않는다.

Raises
    duplicate lens, malformed runtime, unknown capability와 skill 결손을 숨기지 않는다.

결과
    2026-07-15 capability 226개에서 runtimeCompatibility, outputArchetype, unit,
    coveragePolicy, missingPolicy 선언은 모두 0개였다. return contract는 83개였다.
    Skill OS 286개는 runtimeCompatibility를 가졌지만 publicBrowser 선언은 0개였다.
    reviewed receipt도 0/10이라 current public lens ready count는 0이다.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

if __package__:
    from ..snapshot import currentSourceIds
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "snapshot"))
    from sourceSnapshotSetProbe import currentSourceIds

ARCHETYPES = frozenset({"scalar", "series", "table", "ranking", "distribution", "scenario"})
ENVIRONMENTS = frozenset({"publicBrowser", "localPython", "localServer"})
RUNTIME_STATUSES = frozenset({"available", "limited", "unavailable"})
MISSING_POLICIES = frozenset({"preserve"})


@dataclass(frozen=True)
class LensRuntime:
    """Lens 하나의 환경별 실행 선언이다."""

    environment: str
    status: str
    reason: str | None = None


@dataclass(frozen=True)
class LensSpec:
    """Generic Universe lens가 가져야 할 의미와 runtime 계약이다."""

    lensId: str
    capabilityRef: str
    skillRef: str
    outputArchetype: str
    unit: str
    coveragePolicy: str
    missingPolicy: str
    runtime: tuple[LensRuntime, ...]
    redistributionReceiptIds: tuple[str, ...] = ()


@dataclass(frozen=True)
class LensAvailability:
    """Lens와 environment 한 쌍의 실행 가능성이다."""

    lensId: str
    environment: str
    outputArchetype: str
    executable: bool
    status: str
    reason: str


@dataclass(frozen=True)
class LensAvailabilityReport:
    """Lens registry 전체의 환경별 admission 결과다."""

    lensCount: int
    archetypeCounts: dict[str, int]
    archetypeCoverageComplete: bool
    environmentExecutableCounts: dict[str, int]
    invalidLensIds: tuple[str, ...]
    validationReasonCounts: dict[str, int]
    reasonCounts: dict[str, int]
    entries: tuple[LensAvailability, ...]

    def toDict(self) -> dict[str, Any]:
        """Availability report를 JSON 직렬화 가능한 dict로 바꾼다.

        Args
            없음.

        Returns
            dataclass 선언 순서를 보존한 dict.

        Example
            ``report.toDict()``

        Requires
            없음.

        Raises
            직렬화 가능한 필드만 사용하므로 예외를 발생시키지 않는다.
        """

        return asdict(self)


@dataclass(frozen=True)
class LensOutput:
    """Ready, missing, unavailable을 구분한 lens output envelope다."""

    lensId: str
    environment: str
    status: str
    value: Any
    unit: str
    coveragePolicy: str
    missingPolicy: str
    reason: str | None


@dataclass(frozen=True)
class CatalogLensReadinessReport:
    """Capability와 Skill OS가 generic lens를 선언할 준비 정도를 요약한다."""

    capabilityCount: int
    capabilityReturnContractCount: int
    capabilityRuntimeDeclarationCount: int
    capabilityArchetypeDeclarationCount: int
    capabilityUnitDeclarationCount: int
    capabilityCoveragePolicyCount: int
    capabilityMissingPolicyCount: int
    skillCount: int
    skillRuntimeDeclarationCount: int
    skillPublicBrowserDeclarationCount: int
    sourceCount: int
    reviewedReceiptCount: int
    currentPublicLensReadyCount: int
    publicLensReady: bool

    def toDict(self) -> dict[str, Any]:
        """Catalog readiness를 JSON 직렬화 가능한 dict로 바꾼다.

        Args
            없음.

        Returns
            dataclass 선언 순서를 보존한 dict.

        Example
            ``report.toDict()``

        Requires
            없음.

        Raises
            직렬화 가능한 필드만 사용하므로 예외를 발생시키지 않는다.
        """

        return asdict(self)


def _filled(payload: dict[str, Any], field: str) -> bool:
    return payload.get(field) not in (None, "", [], {})


def _publicBrowserDeclared(payload: dict[str, Any]) -> bool:
    runtime = payload.get("runtimeCompatibility")
    if not isinstance(runtime, dict):
        return False
    publicBrowser = runtime.get("publicBrowser")
    if not isinstance(publicBrowser, dict):
        return False
    return publicBrowser.get("status") in {"available", "supported"}


def _specReasons(
    spec: LensSpec,
    capabilityIds: set[str],
    skillIds: set[str],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not spec.lensId:
        reasons.append("missingLensId")
    if spec.capabilityRef not in capabilityIds:
        reasons.append("unknownCapability")
    if spec.skillRef not in skillIds:
        reasons.append("unknownSkill")
    if spec.outputArchetype not in ARCHETYPES:
        reasons.append("invalidOutputArchetype")
    if not spec.unit:
        reasons.append("missingUnit")
    if not spec.coveragePolicy:
        reasons.append("missingCoveragePolicy")
    if spec.missingPolicy not in MISSING_POLICIES:
        reasons.append("invalidMissingPolicy")
    runtimeEnvironments = [runtime.environment for runtime in spec.runtime]
    if len(set(runtimeEnvironments)) != len(runtimeEnvironments):
        reasons.append("duplicateRuntimeEnvironment")
    if set(runtimeEnvironments) != ENVIRONMENTS:
        reasons.append("incompleteRuntimeEnvironments")
    if any(runtime.status not in RUNTIME_STATUSES for runtime in spec.runtime):
        reasons.append("invalidRuntimeStatus")
    return tuple(sorted(set(reasons)))


def inspectLensAvailability(
    specs: Iterable[LensSpec],
    *,
    capabilityIds: Iterable[str],
    skillIds: Iterable[str],
    publicPolicyReady: bool,
) -> LensAvailabilityReport:
    """Explicit LensSpec를 capability, skill, policy, environment와 대조한다.

    Capabilities
        6 archetype coverage와 3 environment 실행 가능성을 fail-closed로 계산한다.

    Args
        specs: candidate LensSpec iterable.
        capabilityIds: live capability ID set.
        skillIds: Skill OS ID set.
        publicPolicyReady: U0-P02 reviewed public policy gate.

    Returns
        deterministic :class:`LensAvailabilityReport`.

    Example
        ``inspectLensAvailability(specs, capabilityIds=ids, skillIds=skills, publicPolicyReady=True)``

    Guide
        limited는 executable이 아니다. publicBrowser는 explicit receipt ref와 global
        policy ready가 모두 있어야 한다.

    When
        Lens registry를 UI에 노출하거나 environment 상태가 바뀔 때 호출한다.

    How
        spec contract를 검사하고 runtime declaration을 environment별 entry로 펼친다.

    Requires
        capability와 skill catalog version은 같은 SourceSnapshotSet에 결속돼야 한다.

    See Also
        :func:`resolveLensOutput`.

    AIContext
        AI 역할: 지원 불명인 lens를 숨기고 reason code를 보존한다.

    Raises
        ValueError: duplicate lensId가 있을 때.
    """

    specItems = tuple(specs)
    capabilityIdSet = set(capabilityIds)
    skillIdSet = set(skillIds)
    seenLensIds: set[str] = set()
    entries: list[LensAvailability] = []
    invalidLensIds: list[str] = []
    validationReasonCounts: Counter[str] = Counter()
    reasonCounts: Counter[str] = Counter()
    archetypeCounts: Counter[str] = Counter()
    for spec in specItems:
        if spec.lensId in seenLensIds:
            raise ValueError(f"duplicate lensId: {spec.lensId}")
        seenLensIds.add(spec.lensId)
        if spec.outputArchetype in ARCHETYPES:
            archetypeCounts[spec.outputArchetype] += 1
        specReasons = _specReasons(spec, capabilityIdSet, skillIdSet)
        if specReasons:
            invalidLensIds.append(spec.lensId)
            validationReasonCounts.update(specReasons)
        runtimeByEnvironment = {runtime.environment: runtime for runtime in spec.runtime}
        for environment in sorted(ENVIRONMENTS):
            runtime = runtimeByEnvironment.get(environment)
            if specReasons:
                executable = False
                reason = specReasons[0]
            elif runtime is None:
                executable = False
                reason = "runtimeEnvironmentMissing"
            elif runtime.status == "limited":
                executable = False
                reason = runtime.reason or "runtimeLimited"
            elif runtime.status == "unavailable":
                executable = False
                reason = runtime.reason or "runtimeUnavailable"
            elif environment == "publicBrowser" and not publicPolicyReady:
                executable = False
                reason = "publicPolicyNotReady"
            elif environment == "publicBrowser" and not spec.redistributionReceiptIds:
                executable = False
                reason = "missingRedistributionReceipt"
            else:
                executable = True
                reason = "available"
            status = "available" if executable else "unavailable"
            entries.append(
                LensAvailability(
                    lensId=spec.lensId,
                    environment=environment,
                    outputArchetype=spec.outputArchetype,
                    executable=executable,
                    status=status,
                    reason=reason,
                )
            )
            if not executable:
                reasonCounts[reason] += 1

    orderedEntries = tuple(sorted(entries, key=lambda item: (item.lensId, item.environment)))
    executableCounts = {
        environment: sum(entry.executable and entry.environment == environment for entry in orderedEntries)
        for environment in sorted(ENVIRONMENTS)
    }
    normalizedArchetypeCounts = {archetype: archetypeCounts[archetype] for archetype in sorted(ARCHETYPES)}
    return LensAvailabilityReport(
        lensCount=len(specItems),
        archetypeCounts=normalizedArchetypeCounts,
        archetypeCoverageComplete=all(normalizedArchetypeCounts.values()),
        environmentExecutableCounts=executableCounts,
        invalidLensIds=tuple(sorted(invalidLensIds)),
        validationReasonCounts=dict(sorted(validationReasonCounts.items())),
        reasonCounts=dict(sorted(reasonCounts.items())),
        entries=orderedEntries,
    )


def resolveLensOutput(
    spec: LensSpec,
    availability: LensAvailability,
    loader: Callable[[], Any],
) -> LensOutput:
    """Availability를 지키면서 lens payload의 ready와 missing을 구분한다.

    Capabilities
        unavailable loader 호출을 막고 None을 0이나 빈 성공으로 바꾸지 않는다.

    Args
        spec: lens semantic contract.
        availability: environment admission result.
        loader: available일 때만 호출할 payload provider.

    Returns
        :class:`LensOutput`.

    Example
        ``resolveLensOutput(spec, availability, lambda: None)``

    Guide
        unavailable은 loader를 호출하지 않는다. available loader가 None을 반환하면
        status missing과 sourceMissing reason을 보존한다.

    When
        Lens Tray가 실제 output을 요청할 때 호출한다.

    How
        lens ID를 대조하고 availability gate 뒤에서만 loader를 평가한다.

    Requires
        loader는 side effect 없는 bounded read여야 한다.

    See Also
        :func:`inspectLensAvailability`.

    AIContext
        AI 역할: unavailable과 missing을 ready 0으로 오표시하지 않는다.

    Raises
        ValueError: spec과 availability lens ID가 다를 때.
    """

    if spec.lensId != availability.lensId:
        raise ValueError("spec and availability lensId must match")
    if not availability.executable:
        return LensOutput(
            lensId=spec.lensId,
            environment=availability.environment,
            status="unavailable",
            value=None,
            unit=spec.unit,
            coveragePolicy=spec.coveragePolicy,
            missingPolicy=spec.missingPolicy,
            reason=availability.reason,
        )
    value = loader()
    if value is None:
        return LensOutput(
            lensId=spec.lensId,
            environment=availability.environment,
            status="missing",
            value=None,
            unit=spec.unit,
            coveragePolicy=spec.coveragePolicy,
            missingPolicy=spec.missingPolicy,
            reason="sourceMissing",
        )
    return LensOutput(
        lensId=spec.lensId,
        environment=availability.environment,
        status="ready",
        value=value,
        unit=spec.unit,
        coveragePolicy=spec.coveragePolicy,
        missingPolicy=spec.missingPolicy,
        reason=None,
    )


def inspectCatalogLensReadiness(
    capabilities: dict[str, dict[str, Any]],
    skills: Iterable[dict[str, Any]],
    *,
    sourceCount: int,
    reviewedReceiptCount: int,
) -> CatalogLensReadinessReport:
    """현재 catalogs의 generic lens declaration coverage를 센서스한다.

    Capabilities
        capability output과 runtime field, Skill OS publicBrowser field, policy receipt
        coverage를 서로 분리해 계수한다.

    Args
        capabilities: loadCapabilities 결과.
        skills: catalog.json skills iterable.
        sourceCount: U0-S01 source 수.
        reviewedReceiptCount: U0-P02 valid reviewed receipt 수.

    Returns
        :class:`CatalogLensReadinessReport`.

    Example
        ``inspectCatalogLensReadiness(capabilities, skills, sourceCount=10, reviewedReceiptCount=0)``

    Guide
        returns 문구가 있어도 outputArchetype, unit, coveragePolicy, missingPolicy를
        추정하지 않는다.

    When
        capability 또는 Skill OS catalog가 바뀔 때 U0-L01을 재실행한다.

    How
        exact declaration field 존재 수만 센다.

    Requires
        catalog payload는 dict entry 구조여야 한다.

    See Also
        :func:`inspectLensAvailability`.

    AIContext
        AI 역할: catalog coverage gap을 수치로 공개한다.

    Raises
        malformed entry는 field가 없는 것으로 보존하고 별도 예외를 만들지 않는다.
    """

    capabilityItems = tuple(payload for payload in capabilities.values() if isinstance(payload, dict))
    skillItems = tuple(skill for skill in skills if isinstance(skill, dict))
    fullyDeclaredPublicLensCount = sum(
        _filled(payload, "outputArchetype")
        and _filled(payload, "unit")
        and _filled(payload, "coveragePolicy")
        and _filled(payload, "missingPolicy")
        and _publicBrowserDeclared(payload)
        for payload in capabilityItems
    )
    publicPolicyReady = sourceCount > 0 and reviewedReceiptCount == sourceCount
    currentPublicLensReadyCount = fullyDeclaredPublicLensCount if publicPolicyReady else 0
    return CatalogLensReadinessReport(
        capabilityCount=len(capabilities),
        capabilityReturnContractCount=sum(
            _filled(payload, "returns") or _filled(payload, "returnSchema") for payload in capabilityItems
        ),
        capabilityRuntimeDeclarationCount=sum(_filled(payload, "runtimeCompatibility") for payload in capabilityItems),
        capabilityArchetypeDeclarationCount=sum(_filled(payload, "outputArchetype") for payload in capabilityItems),
        capabilityUnitDeclarationCount=sum(_filled(payload, "unit") for payload in capabilityItems),
        capabilityCoveragePolicyCount=sum(_filled(payload, "coveragePolicy") for payload in capabilityItems),
        capabilityMissingPolicyCount=sum(_filled(payload, "missingPolicy") for payload in capabilityItems),
        skillCount=len(skillItems),
        skillRuntimeDeclarationCount=sum(_filled(skill, "runtimeCompatibility") for skill in skillItems),
        skillPublicBrowserDeclarationCount=sum(
            "publicBrowser" in (skill.get("runtimeCompatibility") or {}) for skill in skillItems
        ),
        sourceCount=sourceCount,
        reviewedReceiptCount=reviewedReceiptCount,
        currentPublicLensReadyCount=currentPublicLensReadyCount,
        publicLensReady=currentPublicLensReadyCount > 0,
    )


def main() -> int:
    """Live capability와 Skill OS lens readiness를 stdout JSON으로 출력한다.

    Capabilities
        current catalog declaration과 policy coverage gap을 한 report로 만든다.

    Args
        없음.

    Returns
        성공 시 0.

    Example
        ``python lensAvailabilityProbe.py``

    Guide
        current public lens를 자동 생성하지 않고 declaration coverage만 측정한다.

    When
        U0-L01과 capability 또는 Skill OS maintenance audit에서 실행한다.

    How
        capability builder, catalog.json, empty reviewed receipt registry를 결속한다.

    Requires
        DartLab capability import와 local catalog file.

    See Also
        :func:`inspectCatalogLensReadiness`.

    AIContext
        AI 역할: 현재 public lens ready count가 0인지 정직하게 측정한다.

    Raises
        catalog load와 capability build 오류를 숨기지 않는다.
    """

    from dartlab.reference.capability import loadCapabilities

    repoRoot = Path(__file__).resolve().parents[4]
    catalogPayload = json.loads((repoRoot / "src" / "dartlab" / "skills" / "catalog.json").read_text(encoding="utf-8"))
    skills = catalogPayload.get("skills", [])
    sourceIds = currentSourceIds()
    report = inspectCatalogLensReadiness(
        loadCapabilities(),
        skills,
        sourceCount=len(sourceIds),
        reviewedReceiptCount=0,
    )
    print(json.dumps(report.toDict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
