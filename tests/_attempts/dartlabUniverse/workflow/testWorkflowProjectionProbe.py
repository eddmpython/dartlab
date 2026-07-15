"""workflowProjectionProbe의 lossless compile과 conclusion gate를 검증한다."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests._attempts.dartlabUniverse.workflow import (
    FalsifierSpec,
    buildRecipeContract,
    compileRecipeWorkflow,
    inspectWorkflowCatalog,
)

SNAPSHOT_SET_ID = "sha256:" + "b" * 64
CATALOG_VERSION = "gitBlob:fixture"


def _skill(*, qualified: bool = True, sourceRefs: bool = True) -> dict:
    skill = {
        "id": "recipes.fixture.killChain",
        "title": "Fixture Kill Chain",
        "status": "tested",
        "procedure": ["collect source", "compare threshold"],
        "recipeSteps": [{"skillId": "recipes.fixture.source", "note": "source를 먼저 확인한다."}],
        "requiredEvidence": ["sourceRef", "valueRef"],
        "failureModes": ["unit mismatch"],
        "forbidden": ["do not infer missing value"],
        "sourceRefs": ["dartlab://skills/recipes.fixture.killChain"] if sourceRefs else [],
    }
    if qualified:
        skill["falsifiers"] = [
            {
                "text": "value falls below reviewed threshold",
                "verificationRefs": ["rule:reviewed-threshold"],
            }
        ]
    return skill


def _bindings() -> dict[str, tuple[str, ...]]:
    return {
        "sourceRef": ("source:exact",),
        "valueRef": ("value:exact",),
    }


def _compile(*, qualified: bool = True, sourceRefs: bool = True, bindings=None):
    recipe = buildRecipeContract(
        _skill(qualified=qualified, sourceRefs=sourceRefs),
        catalogVersion=CATALOG_VERSION,
    )
    return recipe, compileRecipeWorkflow(
        recipe,
        _bindings() if bindings is None else bindings,
        SNAPSHOT_SET_ID,
    )


def _assertLosslessGenericCompile() -> None:
    recipe, projection = _compile()
    focusTexts = tuple(beat.sourceText for beat in projection.beats if beat.intent == "focus")
    falsifierTexts = tuple(beat.sourceText for beat in projection.beats if beat.intent == "falsify")
    assert focusTexts == recipe.procedure
    assert falsifierTexts == tuple(falsifier.text for falsifier in recipe.falsifiers)
    assert projection.procedurePreservationCoverage == 1.0
    assert projection.requiredEvidenceAccountingCoverage == 1.0
    assert projection.boundEvidenceCoverage == 1.0
    assert projection.falsifierPreservationCoverage == 1.0
    assert projection.conclusionBeatCount == 1
    conclude = next(beat for beat in projection.beats if beat.intent == "conclude")
    qualifiedIds = tuple(
        falsifier.falsifierId for falsifier in recipe.falsifiers if falsifier.qualification == "qualified"
    )
    assert conclude.falsifierRefs == qualifiedIds
    assert projection.dedicatedAdapterCount == 0


def _assertMissingEvidenceBecomesGap() -> None:
    _, projection = _compile(bindings={"sourceRef": ("source:exact",)})
    assert projection.boundEvidenceCoverage == 0.5
    assert projection.requiredEvidenceAccountingCoverage == 1.0
    assert projection.conclusionBeatCount == 0
    assert len(projection.gaps) == 1
    gap = projection.gaps[0]
    assert gap.requestedField == "valueRef"
    assert gap.reasonCode == "missingEvidenceBinding"
    evidenceBeat = next(beat for beat in projection.beats if beat.intent == "evidence")
    assert gap.gapId in evidenceBeat.gapIds


def _assertCandidateDoesNotAuthorizeConclusion() -> None:
    recipe, projection = _compile(qualified=False)
    assert len(recipe.falsifiers) == 2
    assert all(falsifier.qualification == "candidate" for falsifier in recipe.falsifiers)
    assert projection.qualifiedOpenFalsifierCount == 0
    assert projection.conclusionBeatCount == 0
    assert projection.falsifierPreservationCoverage == 1.0


def _assertSourceGapBlocksConclusion() -> None:
    _, projection = _compile(sourceRefs=False)
    assert projection.conclusionBeatCount == 0
    assert any(gap.reasonCode == "missingRecipeSourceRef" for gap in projection.gaps)
    assert projection.modelFactPromotionCount == 0


def _assertCanonicalFlightHash() -> None:
    recipe = buildRecipeContract(_skill(), catalogVersion=CATALOG_VERSION)
    first = compileRecipeWorkflow(
        recipe,
        {"sourceRef": ("source:exact",), "valueRef": ("value:2", "value:1")},
        SNAPSHOT_SET_ID,
    )
    second = compileRecipeWorkflow(
        recipe,
        {"valueRef": ("value:1", "value:2"), "sourceRef": ("source:exact",)},
        SNAPSHOT_SET_ID,
    )
    assert first.flightId == second.flightId


def _assertRecipeContentChangesIdentity() -> None:
    firstSkill = _skill()
    secondSkill = _skill()
    secondSkill["procedure"] = list(reversed(secondSkill["procedure"]))
    firstRecipe = buildRecipeContract(firstSkill, catalogVersion=CATALOG_VERSION)
    secondRecipe = buildRecipeContract(secondSkill, catalogVersion=CATALOG_VERSION)
    firstProjection = compileRecipeWorkflow(firstRecipe, _bindings(), SNAPSHOT_SET_ID)
    secondProjection = compileRecipeWorkflow(secondRecipe, _bindings(), SNAPSHOT_SET_ID)
    assert firstRecipe.recipeVersion != secondRecipe.recipeVersion
    assert firstProjection.flightId != secondProjection.flightId


def _assertInvalidInputsFailClosed() -> None:
    recipe = buildRecipeContract(_skill(), catalogVersion=CATALOG_VERSION)
    with pytest.raises(ValueError, match="unknown evidence binding"):
        compileRecipeWorkflow(recipe, {"unknownRef": ("x",)}, SNAPSHOT_SET_ID)
    with pytest.raises(ValueError, match="qualified falsifier requires"):
        FalsifierSpec(
            falsifierId="falsifier:bad",
            origin="explicit",
            text="unverifiable condition",
            verificationRefs=(),
            qualification="qualified",
        )


def _assertLiveCatalogCensus(repoRoot: Path) -> None:
    census = inspectWorkflowCatalog(repoRoot / "src" / "dartlab" / "skills" / "catalog.json")
    assert census.totalRecipeCount == 156
    assert census.testedRecipeCount == 30
    assert census.testedCompleteCoreContractCount == 22
    assert len(census.selectedRecipeIds) == 10
    assert census.selectedProcedureCount == 80
    assert census.selectedRecipeStepCount == 25
    assert census.selectedRequiredEvidenceCount == 60
    assert census.selectedSourceRefRecipeCount == 10
    assert census.selectedFalsifierCandidateCount == 29
    assert census.selectedQualifiedFalsifierCount == 0
    assert census.testedExplicitVersionFieldCount == 0
    assert census.testedExplicitFalsifierFieldCount == 0
    assert census.procedurePreservationCoverage == 1.0
    assert census.requiredEvidenceAccountingCoverage == 1.0
    assert census.falsifierPreservationCoverage == 1.0
    assert census.gapReceiptCount == 60
    assert census.conclusionBeatCount == 0
    assert census.modelFactPromotionCount == 0
    assert census.dedicatedAdapterCount == 0
    assert census.repeatedFlightHashMatchCount == 10
    assert census.catalogImmutable is True
    assert census.recordedSnapshotCatalogMatched is True
    assert census.liveReady is False


def testLosslessGenericCompile() -> None:
    """Procedure, evidence, falsifier와 conclusion gate의 positive path를 검증한다.

    Example
        ``pytest testWorkflowProjectionProbe.py``

    Requires
        Synthetic qualified recipe fixture.

    Raises
        AssertionError: Generic compile에서 source field가 유실됐을 때.
    """

    _assertLosslessGenericCompile()


def testMissingEvidenceBecomesGap() -> None:
    """Missing required evidence가 GapReceipt로 보존되는지 검증한다.

    Example
        ``pytest testWorkflowProjectionProbe.py``

    Requires
        Partial evidence binding fixture.

    Raises
        AssertionError: Missing이 빈 성공 또는 conclusion으로 바뀌었을 때.
    """

    _assertMissingEvidenceBecomesGap()


def testCandidateDoesNotAuthorizeConclusion() -> None:
    """FailureMode와 forbidden 후보가 conclusion을 열지 못하게 검증한다.

    Example
        ``pytest testWorkflowProjectionProbe.py``

    Requires
        Explicit falsifier가 없는 recipe fixture.

    Raises
        AssertionError: Candidate가 qualified falsifier로 승격됐을 때.
    """

    _assertCandidateDoesNotAuthorizeConclusion()


def testSourceGapBlocksConclusion() -> None:
    """Recipe provenance 결손이 conclusion을 차단하고 fact를 만들지 않음을 검증한다.

    Example
        ``pytest testWorkflowProjectionProbe.py``

    Requires
        sourceRefs가 없는 recipe fixture.

    Raises
        AssertionError: Source gap이 숨겨지거나 fact가 생성됐을 때.
    """

    _assertSourceGapBlocksConclusion()


def testCanonicalFlightHash() -> None:
    """Evidence mapping과 reference 순서에 flightId가 흔들리지 않음을 검증한다.

    Example
        ``pytest testWorkflowProjectionProbe.py``

    Requires
        같은 evidence set을 가진 두 fixture.

    Raises
        AssertionError: Canonical flight identity가 입력 순서에 의존할 때.
    """

    _assertCanonicalFlightHash()


def testRecipeContentChangesIdentity() -> None:
    """Procedure 순서 변화가 recipeVersion과 flightId를 바꾸는지 검증한다.

    Example
        ``pytest testWorkflowProjectionProbe.py``

    Requires
        Procedure 순서가 다른 두 recipe fixture.

    Raises
        AssertionError: 의미 있는 recipe 변화가 identity에 반영되지 않을 때.
    """

    _assertRecipeContentChangesIdentity()


def testInvalidInputsFailClosed() -> None:
    """Unknown evidence와 unverifiable qualified falsifier를 거부하는지 검증한다.

    Example
        ``pytest testWorkflowProjectionProbe.py``

    Requires
        Compiler와 FalsifierSpec validation.

    Raises
        AssertionError: Invalid input이 조용히 수용됐을 때.
    """

    _assertInvalidInputsFailClosed()


def testLiveCatalogCensus() -> None:
    """Current tested recipe 10개 표본의 실측과 live blocker를 고정한다.

    Example
        ``pytest testWorkflowProjectionProbe.py``

    Requires
        Tracked local Skill OS catalog와 Git CLI.

    Raises
        AssertionError: Catalog schema 또는 compiler 결과가 drift했을 때.
    """

    _assertLiveCatalogCensus(Path(__file__).resolve().parents[4])
