"""Skill OS recipe를 evidence와 falsifier를 보존한 SceneBeat로 투영한다.

Capabilities
    tested recipe의 procedure, requiredEvidence, negative condition을 generic workflow로 컴파일한다.

AIContext
    AI 역할: recipe instruction을 fact로 승격하지 않고 evidence gap과 falsifier qualification을 분리한다.

Guide
    Synthetic positive contract와 current catalog의 live readiness를 별도 결과로 읽는다.

When
    U0-W02 Kill-Chain compiler 적격성과 recipe schema gap을 검증할 때 사용한다.

How
    :func:`buildRecipeContract`로 source fields를 보존하고 :func:`compileRecipeWorkflow`로 beats를 만든다.

Requires
    Production canonicalPayloadHash와 live census 실행 시 tracked Skill OS catalog가 필요하다.

Raises
    ValueError: recipe identity, evidence binding, falsifier 또는 snapshot contract가 잘못됐을 때.

Example
    ``projection = compileRecipeWorkflow(recipe, bindings, snapshotSetId)``

See Also
    :mod:`tests._attempts.dartlabUniverse.snapshot.changeReplayProbe`.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from dartlab.simulate.vintage import canonicalPayloadHash

RECORDED_SOURCE_SNAPSHOT_SET_ID = "sha256:4a68a0c0129884bc138223ef3d31672c1e7dd5bbbdac33a4816d0f953e54f73a"
RECORDED_RECIPE_CATALOG_BLOB = "3c9c61cff18d19abb21cf275a1d8c55082dbb78e"
BEAT_INTENTS = {"orient", "focus", "compare", "evidence", "falsify", "conclude"}
FALSIFIER_ORIGINS = {"explicit", "failureMode", "forbidden"}
FALSIFIER_QUALIFICATIONS = {"candidate", "qualified"}


def _snapshotDigest(snapshotSetId: str) -> str:
    digest = snapshotSetId.removeprefix("sha256:")
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest.lower()):
        raise ValueError("snapshotSetId must contain a SHA-256 digest")
    return digest.lower()


def _textTuple(value: Any, label: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{label} must be a sequence")
    normalized = tuple(str(item).strip() for item in value)
    if any(not item for item in normalized):
        raise ValueError(f"{label} cannot contain empty text")
    return normalized


@dataclass(frozen=True)
class RecipeStepRef:
    """Recipe가 다음에 연결하는 skill과 원문 note를 보존한다."""

    skillId: str
    note: str


@dataclass(frozen=True)
class FalsifierSpec:
    """Recipe negative condition의 origin과 검증 가능 여부를 분리한다."""

    falsifierId: str
    origin: str
    text: str
    verificationRefs: tuple[str, ...]
    state: str = "open"
    qualification: str = "candidate"

    def __post_init__(self) -> None:
        if not self.falsifierId or not self.text:
            raise ValueError("falsifier identity and text are required")
        if self.origin not in FALSIFIER_ORIGINS:
            raise ValueError(f"unsupported falsifier origin: {self.origin}")
        if self.qualification not in FALSIFIER_QUALIFICATIONS:
            raise ValueError(f"unsupported falsifier qualification: {self.qualification}")
        if self.state != "open":
            raise ValueError("workflow projection accepts only open falsifiers")
        verificationRefs = tuple(sorted(set(self.verificationRefs)))
        if any(not reference for reference in verificationRefs):
            raise ValueError("verificationRefs cannot contain an empty reference")
        if self.qualification == "qualified" and not verificationRefs:
            raise ValueError("qualified falsifier requires verificationRefs")
        object.__setattr__(self, "verificationRefs", verificationRefs)


@dataclass(frozen=True)
class RecipeContract:
    """한 recipe의 immutable content identity와 workflow source fields를 보존한다."""

    recipeId: str
    title: str
    status: str
    recipeVersion: str
    catalogVersion: str
    procedure: tuple[str, ...]
    recipeSteps: tuple[RecipeStepRef, ...]
    requiredEvidence: tuple[str, ...]
    falsifiers: tuple[FalsifierSpec, ...]
    sourceRefs: tuple[str, ...]


@dataclass(frozen=True)
class ProjectionSeed:
    """SceneBeat가 요청하는 recipe focus와 field 범위를 최소 형태로 표현한다."""

    recipeId: str
    focusKind: str
    focusIndex: int
    fieldIds: tuple[str, ...]


@dataclass(frozen=True)
class SceneBeat:
    """Recipe source text와 evidence 또는 falsifier reference를 가진 조사 단계다."""

    beatId: str
    intent: str
    projectionSpec: ProjectionSeed
    selectedIds: tuple[str, ...]
    sourceText: str
    expectedEvidenceFields: tuple[str, ...]
    evidenceRefs: tuple[str, ...]
    sourceRefs: tuple[str, ...]
    falsifierRefs: tuple[str, ...]
    gapIds: tuple[str, ...]
    transition: str
    narration: str
    semanticStatus: str


@dataclass(frozen=True)
class GapReceipt:
    """Required evidence 또는 recipe provenance 결손을 빈 성공 대신 보존한다."""

    gapId: str
    kind: str
    ownerSource: str
    requestedField: str
    reasonCode: str
    retryPolicy: str


@dataclass(frozen=True)
class WorkflowProjectionReport:
    """한 recipe의 beats, gaps, coverage, conclusion gate와 flight identity를 기록한다."""

    schemaVersion: str
    flightId: str
    objective: str
    snapshotSetId: str
    recipeId: str
    recipeVersion: str
    catalogVersion: str
    beats: tuple[SceneBeat, ...]
    gaps: tuple[GapReceipt, ...]
    procedurePreservationCoverage: float
    requiredEvidenceAccountingCoverage: float
    boundEvidenceCoverage: float
    falsifierPreservationCoverage: float
    qualifiedOpenFalsifierCount: int
    conclusionBeatCount: int
    modelFactPromotionCount: int
    dedicatedAdapterCount: int

    def toDict(self) -> dict[str, Any]:
        """JSON compatible workflow projection payload를 반환한다.

        Returns
            Nested dataclass를 mapping과 collection으로 바꾼 값.

        Example
            ``payload = projection.toDict()``

        Requires
            Workflow fields가 JSON compatible scalar를 가져야 한다.

        Raises
            TypeError: 향후 JSON 비호환 field가 추가됐을 때 encoder가 발생시킬 수 있다.
        """

        return asdict(self)


@dataclass(frozen=True)
class WorkflowCatalogCensus:
    """Tested recipe 표본의 compiler 보존율과 live conclusion blocker를 기록한다."""

    schemaVersion: str
    catalogPath: str
    catalogBlob: str
    catalogImmutable: bool
    recordedSnapshotCatalogMatched: bool
    totalRecipeCount: int
    testedRecipeCount: int
    testedCompleteCoreContractCount: int
    selectedRecipeIds: tuple[str, ...]
    selectedProcedureCount: int
    selectedRecipeStepCount: int
    selectedRequiredEvidenceCount: int
    selectedSourceRefRecipeCount: int
    selectedFalsifierCandidateCount: int
    selectedQualifiedFalsifierCount: int
    testedExplicitVersionFieldCount: int
    testedExplicitFalsifierFieldCount: int
    procedurePreservationCoverage: float
    requiredEvidenceAccountingCoverage: float
    falsifierPreservationCoverage: float
    gapReceiptCount: int
    conclusionBeatCount: int
    modelFactPromotionCount: int
    dedicatedAdapterCount: int
    repeatedFlightHashMatchCount: int
    liveReady: bool
    blockerReasons: tuple[str, ...]

    def toDict(self) -> dict[str, Any]:
        """JSON compatible catalog census payload를 반환한다.

        Returns
            Nested dataclass를 mapping과 collection으로 바꾼 값.

        Example
            ``payload = census.toDict()``

        Requires
            Census fields가 JSON compatible scalar를 가져야 한다.

        Raises
            TypeError: 향후 JSON 비호환 field가 추가됐을 때 encoder가 발생시킬 수 있다.
        """

        return asdict(self)


def _recipeSteps(value: Any) -> tuple[RecipeStepRef, ...]:
    if value is None:
        return ()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("recipeSteps must be a sequence")
    steps = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError("recipeSteps entries must be mappings")
        skillId = str(item.get("skillId", "")).strip()
        note = str(item.get("note", "")).strip()
        if not skillId or not note:
            raise ValueError("recipeSteps entries require skillId and note")
        steps.append(RecipeStepRef(skillId=skillId, note=note))
    return tuple(steps)


def _falsifier(
    recipeId: str,
    origin: str,
    text: str,
    verificationRefs: tuple[str, ...],
) -> FalsifierSpec:
    qualification = "qualified" if verificationRefs else "candidate"
    payload = {
        "recipeId": recipeId,
        "origin": origin,
        "text": text,
        "verificationRefs": verificationRefs,
    }
    return FalsifierSpec(
        falsifierId=canonicalPayloadHash(payload),
        origin=origin,
        text=text,
        verificationRefs=verificationRefs,
        qualification=qualification,
    )


def _falsifiers(skill: Mapping[str, Any], recipeId: str) -> tuple[FalsifierSpec, ...]:
    result: list[FalsifierSpec] = []
    explicit = skill.get("falsifiers", ())
    if explicit is None:
        explicit = ()
    if not isinstance(explicit, Sequence) or isinstance(explicit, (str, bytes)):
        raise ValueError("falsifiers must be a sequence")
    for item in explicit:
        if isinstance(item, str):
            text = item.strip()
            verificationRefs: tuple[str, ...] = ()
        elif isinstance(item, Mapping):
            text = str(item.get("text", "")).strip()
            verificationRefs = _textTuple(item.get("verificationRefs", ()), "verificationRefs")
        else:
            raise ValueError("falsifier entries must be text or mappings")
        if not text:
            raise ValueError("falsifier text is required")
        result.append(_falsifier(recipeId, "explicit", text, verificationRefs))

    for origin, fieldName in (("failureMode", "failureModes"), ("forbidden", "forbidden")):
        for text in _textTuple(skill.get(fieldName, ()), fieldName):
            result.append(_falsifier(recipeId, origin, text, ()))
    return tuple(result)


def buildRecipeContract(
    skill: Mapping[str, Any],
    *,
    catalogVersion: str,
) -> RecipeContract:
    """Skill catalog entry를 lossless recipe workflow contract로 정규화한다.

    Capabilities
        Procedure, recipeSteps, requiredEvidence, sourceRefs와 negative condition origin을 보존한다.

    AIContext
        AI 역할: failureMode와 forbidden을 검증된 falsifier로 오인하지 않고 content version을 만든다.

    Args
        skill: Skill OS catalog의 recipe mapping.
        catalogVersion: Immutable Git blob 또는 동등한 catalog source version.

    Returns
        Canonical recipeVersion을 가진 :class:`RecipeContract`.

    Example
        ``recipe = buildRecipeContract(skill, catalogVersion="gitBlob:abc")``

    Guide
        Explicit falsifier도 verificationRefs가 없으면 candidate로 유지한다.

    When
        Recipe entry를 SceneBeat compiler에 전달하기 전에 호출한다.

    How
        Source field를 정규화하고 canonical payload hash를 recipeVersion으로 사용한다.

    Requires
        recipe id, title, catalogVersion이 필요하다.

    See Also
        :func:`compileRecipeWorkflow`.

    Raises
        ValueError: required identity 또는 collection shape가 잘못됐을 때.
    """

    recipeId = str(skill.get("id", "")).strip()
    title = str(skill.get("title", "")).strip()
    status = str(skill.get("status", "")).strip()
    if not recipeId or not title or not status or not catalogVersion:
        raise ValueError("recipe identity and catalogVersion are required")
    if not recipeId.startswith("recipes."):
        raise ValueError("skill is not a recipe")

    procedure = _textTuple(skill.get("procedure", ()), "procedure")
    recipeSteps = _recipeSteps(skill.get("recipeSteps", ()))
    requiredEvidence = _textTuple(skill.get("requiredEvidence", ()), "requiredEvidence")
    if len(set(requiredEvidence)) != len(requiredEvidence):
        raise ValueError("requiredEvidence cannot contain duplicates")
    sourceRefs = _textTuple(skill.get("sourceRefs", ()), "sourceRefs")
    falsifiers = _falsifiers(skill, recipeId)
    versionPayload = {
        "recipeId": recipeId,
        "title": title,
        "status": status,
        "procedure": procedure,
        "recipeSteps": [asdict(step) for step in recipeSteps],
        "requiredEvidence": requiredEvidence,
        "falsifiers": [asdict(falsifier) for falsifier in falsifiers],
        "sourceRefs": sourceRefs,
    }
    recipeVersion = "sha256:" + canonicalPayloadHash(versionPayload)
    return RecipeContract(
        recipeId=recipeId,
        title=title,
        status=status,
        recipeVersion=recipeVersion,
        catalogVersion=catalogVersion,
        procedure=procedure,
        recipeSteps=recipeSteps,
        requiredEvidence=requiredEvidence,
        falsifiers=falsifiers,
        sourceRefs=sourceRefs,
    )


def _gap(recipeId: str, requestedField: str, reasonCode: str) -> GapReceipt:
    payload = {
        "recipeId": recipeId,
        "requestedField": requestedField,
        "reasonCode": reasonCode,
    }
    return GapReceipt(
        gapId=canonicalPayloadHash(payload),
        kind="unresolved",
        ownerSource=recipeId,
        requestedField=requestedField,
        reasonCode=reasonCode,
        retryPolicy="provideReviewedReference",
    )


def _beat(
    recipe: RecipeContract,
    *,
    intent: str,
    focusKind: str,
    focusIndex: int,
    sourceText: str,
    selectedIds: tuple[str, ...] = (),
    expectedEvidenceFields: tuple[str, ...] = (),
    evidenceRefs: tuple[str, ...] = (),
    falsifierRefs: tuple[str, ...] = (),
    gapIds: tuple[str, ...] = (),
    transition: str = "replace",
    narration: str,
    semanticStatus: str,
) -> SceneBeat:
    if intent not in BEAT_INTENTS:
        raise ValueError(f"unsupported beat intent: {intent}")
    projectionSpec = ProjectionSeed(
        recipeId=recipe.recipeId,
        focusKind=focusKind,
        focusIndex=focusIndex,
        fieldIds=expectedEvidenceFields,
    )
    payload = {
        "recipeVersion": recipe.recipeVersion,
        "intent": intent,
        "projectionSpec": asdict(projectionSpec),
        "selectedIds": selectedIds,
        "sourceText": sourceText,
        "expectedEvidenceFields": expectedEvidenceFields,
        "evidenceRefs": evidenceRefs,
        "sourceRefs": recipe.sourceRefs,
        "falsifierRefs": falsifierRefs,
        "gapIds": gapIds,
        "transition": transition,
        "narration": narration,
        "semanticStatus": semanticStatus,
    }
    return SceneBeat(
        beatId=canonicalPayloadHash(payload),
        intent=intent,
        projectionSpec=projectionSpec,
        selectedIds=selectedIds,
        sourceText=sourceText,
        expectedEvidenceFields=expectedEvidenceFields,
        evidenceRefs=evidenceRefs,
        sourceRefs=recipe.sourceRefs,
        falsifierRefs=falsifierRefs,
        gapIds=gapIds,
        transition=transition,
        narration=narration,
        semanticStatus=semanticStatus,
    )


def compileRecipeWorkflow(
    recipe: RecipeContract,
    evidenceBindings: Mapping[str, Sequence[str]],
    snapshotSetId: str,
    *,
    objective: str = "falsify",
) -> WorkflowProjectionReport:
    """Recipe contract를 generic SceneBeat와 honest GapReceipt로 컴파일한다.

    Capabilities
        Orient, focus, evidence, falsify, conclude beat를 만들고 missing과 conclusion gate를 보존한다.

    AIContext
        AI 역할: recipe instruction이나 model summary를 fact로 표시하지 않고 결손을 빈 성공과 분리한다.

    Args
        recipe: Canonical recipe source contract.
        evidenceBindings: requiredEvidence field별 reviewed reference collection.
        snapshotSetId: SourceSnapshotSet canonical identity.
        objective: investigate, compare, falsify, explain 중 하나.

    Returns
        Deterministic flightId, beats, gaps와 preservation coverage report.

    Example
        ``report = compileRecipeWorkflow(recipe, {"sourceRef": ["source:1"]}, snapshotId)``

    Guide
        Unknown binding은 거부하고 missing binding은 GapReceipt로 만들며 qualified open falsifier가 없으면 conclude를 만들지 않는다.

    When
        Tested recipe를 Kill-Chain 조사 순서로 투영할 때 호출한다.

    How
        Procedure 한 줄을 focus beat 하나로 보존하고 evidence와 falsifier를 별도 lane에 놓는다.

    Requires
        Valid snapshotSetId와 recipeVersion이 필요하다.

    See Also
        :func:`buildRecipeContract`.

    Raises
        ValueError: snapshot, objective 또는 evidence binding field가 잘못됐을 때.
    """

    _snapshotDigest(snapshotSetId)
    if objective not in {"investigate", "compare", "falsify", "explain"}:
        raise ValueError(f"unsupported objective: {objective}")
    unknownFields = sorted(set(evidenceBindings) - set(recipe.requiredEvidence))
    if unknownFields:
        raise ValueError(f"unknown evidence binding fields: {unknownFields}")

    normalizedBindings = {
        field: tuple(sorted(set(_textTuple(evidenceBindings.get(field, ()), f"evidenceBindings.{field}"))))
        for field in recipe.requiredEvidence
    }
    gaps = [
        _gap(recipe.recipeId, field, "missingEvidenceBinding")
        for field, references in normalizedBindings.items()
        if not references
    ]
    if not recipe.sourceRefs:
        gaps.append(_gap(recipe.recipeId, "recipeSourceRef", "missingRecipeSourceRef"))

    beats: list[SceneBeat] = []
    beats.append(
        _beat(
            recipe,
            intent="orient",
            focusKind="recipe",
            focusIndex=-1,
            sourceText=recipe.title,
            selectedIds=tuple(step.skillId for step in recipe.recipeSteps),
            narration="recipe context",
            semanticStatus="navigation",
        )
    )
    for index, procedureText in enumerate(recipe.procedure):
        beats.append(
            _beat(
                recipe,
                intent="focus",
                focusKind="procedure",
                focusIndex=index,
                sourceText=procedureText,
                narration=f"procedure {index + 1}",
                semanticStatus="instruction",
            )
        )

    evidenceGapIds = tuple(gap.gapId for gap in gaps if gap.reasonCode == "missingEvidenceBinding")
    boundEvidenceRefs = tuple(
        sorted({reference for references in normalizedBindings.values() for reference in references})
    )
    beats.append(
        _beat(
            recipe,
            intent="evidence",
            focusKind="requiredEvidence",
            focusIndex=-1,
            sourceText="requiredEvidence",
            expectedEvidenceFields=recipe.requiredEvidence,
            evidenceRefs=boundEvidenceRefs,
            gapIds=evidenceGapIds,
            narration="evidence check",
            semanticStatus="evidenceExpectation",
        )
    )

    for index, falsifier in enumerate(recipe.falsifiers):
        beats.append(
            _beat(
                recipe,
                intent="falsify",
                focusKind=falsifier.origin,
                focusIndex=index,
                sourceText=falsifier.text,
                evidenceRefs=falsifier.verificationRefs,
                falsifierRefs=(falsifier.falsifierId,),
                narration=f"falsifier {index + 1}",
                semanticStatus=falsifier.qualification,
            )
        )

    qualifiedOpen = tuple(
        falsifier.falsifierId
        for falsifier in recipe.falsifiers
        if falsifier.qualification == "qualified" and falsifier.state == "open"
    )
    if not gaps and qualifiedOpen:
        beats.append(
            _beat(
                recipe,
                intent="conclude",
                focusKind="provisionalConclusion",
                focusIndex=-1,
                sourceText="provisionalConclusion",
                evidenceRefs=boundEvidenceRefs,
                falsifierRefs=qualifiedOpen,
                narration="provisional conclusion",
                semanticStatus="provisional",
            )
        )

    procedureTexts = tuple(beat.sourceText for beat in beats if beat.projectionSpec.focusKind == "procedure")
    falsifierTexts = tuple(beat.sourceText for beat in beats if beat.intent == "falsify")
    accountedFields = set(normalizedBindings) | {
        gap.requestedField for gap in gaps if gap.reasonCode == "missingEvidenceBinding"
    }
    flightPayload = {
        "schemaVersion": "universeFlightPlan.v1",
        "objective": objective,
        "snapshotSetId": snapshotSetId,
        "recipeId": recipe.recipeId,
        "recipeVersion": recipe.recipeVersion,
        "beats": [asdict(beat) for beat in beats],
        "gaps": [asdict(gap) for gap in gaps],
    }
    return WorkflowProjectionReport(
        schemaVersion="universeFlightPlan.v1",
        flightId=canonicalPayloadHash(flightPayload),
        objective=objective,
        snapshotSetId=snapshotSetId,
        recipeId=recipe.recipeId,
        recipeVersion=recipe.recipeVersion,
        catalogVersion=recipe.catalogVersion,
        beats=tuple(beats),
        gaps=tuple(gaps),
        procedurePreservationCoverage=(
            sum(left == right for left, right in zip(recipe.procedure, procedureTexts, strict=False))
            / len(recipe.procedure)
            if recipe.procedure
            else 1.0
        ),
        requiredEvidenceAccountingCoverage=(
            len(accountedFields & set(recipe.requiredEvidence)) / len(recipe.requiredEvidence)
            if recipe.requiredEvidence
            else 1.0
        ),
        boundEvidenceCoverage=(
            sum(bool(normalizedBindings[field]) for field in recipe.requiredEvidence) / len(recipe.requiredEvidence)
            if recipe.requiredEvidence
            else 1.0
        ),
        falsifierPreservationCoverage=(
            sum(left.text == right for left, right in zip(recipe.falsifiers, falsifierTexts, strict=False))
            / len(recipe.falsifiers)
            if recipe.falsifiers
            else 1.0
        ),
        qualifiedOpenFalsifierCount=len(qualifiedOpen),
        conclusionBeatCount=sum(beat.intent == "conclude" for beat in beats),
        modelFactPromotionCount=sum(beat.semanticStatus == "fact" for beat in beats),
        dedicatedAdapterCount=0,
    )


def _gitBlob(catalogPath: Path) -> tuple[str, str, bool]:
    repoRoot = catalogPath.resolve().parents[3]
    relativePath = catalogPath.resolve().relative_to(repoRoot).as_posix()
    tracked = subprocess.run(
        ["git", "rev-parse", f"HEAD:{relativePath}"],
        cwd=repoRoot,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    working = subprocess.run(
        ["git", "hash-object", str(catalogPath.resolve())],
        cwd=repoRoot,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return tracked, working, tracked == working


def inspectWorkflowCatalog(
    catalogPath: str | Path,
    *,
    sampleSize: int = 10,
    snapshotSetId: str = RECORDED_SOURCE_SNAPSHOT_SET_ID,
) -> WorkflowCatalogCensus:
    """Current Skill OS tested recipe의 workflow projection readiness를 센서스한다.

    Capabilities
        Tested recipe field coverage와 정렬 표본의 lossless compile, gap, conclusion gate를 계수한다.

    AIContext
        AI 역할: failureMode와 forbidden을 qualified falsifier로 부풀리지 않고 live blocker를 기록한다.

    Args
        catalogPath: Skill OS catalog JSON path.
        sampleSize: recipe ID 정렬 뒤 선택할 tested recipe 수.
        snapshotSetId: U0-S01 SourceSnapshotSet identity.

    Returns
        Current catalog census와 compiler preservation 결과.

    Example
        ``census = inspectWorkflowCatalog("src/dartlab/skills/catalog.json")``

    Guide
        표본은 대표성을 주장하지 않는 deterministic contract sample이다.

    When
        Recipe catalog가 바뀐 뒤 U0-W02 live readiness를 재측정할 때 호출한다.

    How
        Tracked Git blob을 확인하고 tested recipe 앞 N개를 evidence binding 없이 두 번 컴파일한다.

    Requires
        Git CLI와 local Skill OS catalog가 필요하다.

    See Also
        :func:`compileRecipeWorkflow`.

    Raises
        ValueError: sampleSize, snapshot 또는 catalog recipe가 잘못됐을 때.
        OSError: catalog를 읽지 못할 때.
        subprocess.CalledProcessError: tracked Git blob을 찾지 못할 때.
    """

    if sampleSize <= 0:
        raise ValueError("sampleSize must be positive")
    _snapshotDigest(snapshotSetId)
    sourcePath = Path(catalogPath)
    catalog = json.loads(sourcePath.read_text(encoding="utf-8"))
    skills = tuple(catalog.get("skills", ()))
    recipes = tuple(skill for skill in skills if skill.get("category") == "recipes")
    tested = tuple(sorted((skill for skill in recipes if skill.get("status") == "tested"), key=lambda item: item["id"]))
    selected = tested[:sampleSize]
    if len(selected) != sampleSize:
        raise ValueError("catalog does not contain the requested tested recipe sample")

    trackedCatalogBlob, workingCatalogBlob, catalogImmutable = _gitBlob(sourcePath)
    catalogVersion = f"gitBlob:{trackedCatalogBlob}" if catalogImmutable else f"workingTree:{workingCatalogBlob}"
    contracts = tuple(buildRecipeContract(skill, catalogVersion=catalogVersion) for skill in selected)
    projections = tuple(compileRecipeWorkflow(recipe, {}, snapshotSetId) for recipe in contracts)
    repeated = tuple(compileRecipeWorkflow(recipe, {}, snapshotSetId) for recipe in contracts)
    repeatedFlightHashMatchCount = sum(
        left.flightId == right.flightId for left, right in zip(projections, repeated, strict=True)
    )

    testedCompleteCoreContractCount = sum(
        bool(skill.get("procedure"))
        and bool(skill.get("requiredEvidence"))
        and bool(tuple(skill.get("failureModes", ())) + tuple(skill.get("forbidden", ())))
        and bool(skill.get("sourceRefs"))
        for skill in tested
    )
    explicitVersionFieldCount = sum("version" in skill for skill in tested)
    explicitFalsifierFieldCount = sum("falsifier" in skill or "falsifiers" in skill for skill in tested)
    qualifiedFalsifierCount = sum(
        falsifier.qualification == "qualified" for recipe in contracts for falsifier in recipe.falsifiers
    )
    gapReceiptCount = sum(len(projection.gaps) for projection in projections)
    conclusionBeatCount = sum(projection.conclusionBeatCount for projection in projections)
    recordedSnapshotCatalogMatched = catalogImmutable and trackedCatalogBlob == RECORDED_RECIPE_CATALOG_BLOB
    blockerReasons = []
    if not catalogImmutable:
        blockerReasons.append("recipeCatalogWorkingTreeDiffersFromTrackedBlob")
    if not recordedSnapshotCatalogMatched:
        blockerReasons.append("recipeCatalogDoesNotMatchRecordedSourceSnapshot")
    if explicitFalsifierFieldCount == 0:
        blockerReasons.append("recipeSchemaHasNoExplicitFalsifierField")
    if qualifiedFalsifierCount == 0:
        blockerReasons.append("selectedRecipesHaveNoQualifiedFalsifier")
    if gapReceiptCount:
        blockerReasons.append("executionEvidenceBindingsMissing")

    return WorkflowCatalogCensus(
        schemaVersion="workflowCatalogCensus.v1",
        catalogPath=sourcePath.as_posix(),
        catalogBlob=workingCatalogBlob,
        catalogImmutable=catalogImmutable,
        recordedSnapshotCatalogMatched=recordedSnapshotCatalogMatched,
        totalRecipeCount=len(recipes),
        testedRecipeCount=len(tested),
        testedCompleteCoreContractCount=testedCompleteCoreContractCount,
        selectedRecipeIds=tuple(recipe.recipeId for recipe in contracts),
        selectedProcedureCount=sum(len(recipe.procedure) for recipe in contracts),
        selectedRecipeStepCount=sum(len(recipe.recipeSteps) for recipe in contracts),
        selectedRequiredEvidenceCount=sum(len(recipe.requiredEvidence) for recipe in contracts),
        selectedSourceRefRecipeCount=sum(bool(recipe.sourceRefs) for recipe in contracts),
        selectedFalsifierCandidateCount=sum(len(recipe.falsifiers) for recipe in contracts),
        selectedQualifiedFalsifierCount=qualifiedFalsifierCount,
        testedExplicitVersionFieldCount=explicitVersionFieldCount,
        testedExplicitFalsifierFieldCount=explicitFalsifierFieldCount,
        procedurePreservationCoverage=(
            sum(projection.procedurePreservationCoverage for projection in projections) / len(projections)
        ),
        requiredEvidenceAccountingCoverage=(
            sum(projection.requiredEvidenceAccountingCoverage for projection in projections) / len(projections)
        ),
        falsifierPreservationCoverage=(
            sum(projection.falsifierPreservationCoverage for projection in projections) / len(projections)
        ),
        gapReceiptCount=gapReceiptCount,
        conclusionBeatCount=conclusionBeatCount,
        modelFactPromotionCount=sum(projection.modelFactPromotionCount for projection in projections),
        dedicatedAdapterCount=sum(projection.dedicatedAdapterCount for projection in projections),
        repeatedFlightHashMatchCount=repeatedFlightHashMatchCount,
        liveReady=not blockerReasons,
        blockerReasons=tuple(blockerReasons),
    )


def main() -> int:
    """Current Skill OS tested recipe 10개의 workflow census를 JSON으로 출력한다.

    Capabilities
        U0-W02 deterministic catalog sample과 live conclusion blocker를 재측정한다.

    AIContext
        AI 역할: compiler 보존 성공과 live recipe admission 실패를 분리한 근거를 만든다.

    Returns
        성공 시 0.

    Example
        ``python workflowProjectionProbe.py``

    Guide
        stdout을 원장에 기록하고 candidate falsifier를 qualified로 자동 승격하지 않는다.

    When
        Skill OS catalog가 바뀌었거나 Kill-Chain gate를 재심사할 때 사용한다.

    How
        Repository catalog path를 찾아 :func:`inspectWorkflowCatalog`를 호출한다.

    Requires
        Git CLI와 local Skill OS catalog가 필요하다.

    See Also
        :func:`inspectWorkflowCatalog`.

    Raises
        ValueError: catalog sample이 부족하거나 contract가 잘못됐을 때.
        OSError: catalog를 읽지 못할 때.
    """

    repoRoot = Path(__file__).resolve().parents[4]
    census = inspectWorkflowCatalog(repoRoot / "src" / "dartlab" / "skills" / "catalog.json")
    print(json.dumps(census.toDict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
