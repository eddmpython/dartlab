"""lensAvailabilityProbe의 environment와 missing 경계를 검증한다."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests._attempts.dartlabUniverse.policy import (
    LensRuntime,
    LensSpec,
    inspectCatalogLensReadiness,
    inspectLensAvailability,
    resolveLensOutput,
)

ARCHETYPES = ("scalar", "series", "table", "ranking", "distribution", "scenario")


def _spec(archetype: str, *, runtimeStatus: str = "available") -> LensSpec:
    lensId = f"lens.{archetype}"
    return LensSpec(
        lensId=lensId,
        capabilityRef=f"cap.{archetype}",
        skillRef=f"skill.{archetype}",
        outputArchetype=archetype,
        unit="unitless" if archetype == "scalar" else f"{archetype}Unit",
        coveragePolicy="report numerator and denominator",
        missingPolicy="preserve",
        runtime=tuple(
            LensRuntime(environment, runtimeStatus, None)
            for environment in ("publicBrowser", "localPython", "localServer")
        ),
        redistributionReceiptIds=(f"receipt.{archetype}",),
    )


def _specs() -> tuple[LensSpec, ...]:
    return tuple(_spec(archetype) for archetype in ARCHETYPES)


def _catalogIds() -> tuple[set[str], set[str]]:
    specs = _specs()
    return ({spec.capabilityRef for spec in specs}, {spec.skillRef for spec in specs})


def _report(specs: tuple[LensSpec, ...], *, publicPolicyReady: bool = True):
    capabilityIds, skillIds = _catalogIds()
    return inspectLensAvailability(
        specs,
        capabilityIds=capabilityIds,
        skillIds=skillIds,
        publicPolicyReady=publicPolicyReady,
    )


def _assertSixArchetypesAvailable() -> None:
    report = _report(_specs())
    assert report.lensCount == 6
    assert report.archetypeCoverageComplete is True
    assert report.archetypeCounts == {archetype: 1 for archetype in sorted(ARCHETYPES)}
    assert report.environmentExecutableCounts == {
        "localPython": 6,
        "localServer": 6,
        "publicBrowser": 6,
    }
    assert report.invalidLensIds == ()


def testSixOutputArchetypesCoverThreeEnvironments() -> None:
    """6 archetype의 explicit contract가 세 환경에서 실행 가능하다.

    Args
        없음.

    Example
        pytest가 6 by 3 availability를 검증한다.

    Requires
        synthetic six archetype fixtures.

    Raises
        AssertionError: archetype 또는 environment coverage가 빠질 때.
    """

    _assertSixArchetypesAvailable()


def _assertPolicyBlocksOnlyPublic() -> None:
    report = _report(_specs(), publicPolicyReady=False)
    assert report.environmentExecutableCounts == {
        "localPython": 6,
        "localServer": 6,
        "publicBrowser": 0,
    }
    assert report.reasonCounts == {"publicPolicyNotReady": 6}


def testPolicyGapBlocksPublicButNotLocal() -> None:
    """Receipt gate 결손은 publicBrowser만 차단한다.

    Args
        없음.

    Example
        pytest가 public과 local 분리를 검증한다.

    Requires
        synthetic six archetype fixtures.

    Raises
        AssertionError: policy gap이 public lens를 허용할 때.
    """

    _assertPolicyBlocksOnlyPublic()


def _assertInvalidSemanticContract() -> None:
    broken = replace(_spec("scalar"), unit="", missingPolicy="zeroFill")
    report = _report((broken,))
    assert report.invalidLensIds == ("lens.scalar",)
    assert report.environmentExecutableCounts == {
        "localPython": 0,
        "localServer": 0,
        "publicBrowser": 0,
    }
    assert report.validationReasonCounts == {
        "invalidMissingPolicy": 1,
        "missingUnit": 1,
    }
    assert set(report.reasonCounts) == {"invalidMissingPolicy"}


def testMissingUnitAndZeroFillPolicyInvalidateLens() -> None:
    """Unit 결손과 zero fill missing policy를 차단한다.

    Args
        없음.

    Example
        pytest가 semantic lens contract 결손을 검증한다.

    Requires
        synthetic scalar lens.

    Raises
        AssertionError: invalid lens가 executable일 때.
    """

    _assertInvalidSemanticContract()


def _assertUnavailableDoesNotCallLoader() -> None:
    spec = _spec("series", runtimeStatus="unavailable")
    report = _report((spec,))
    availability = next(entry for entry in report.entries if entry.environment == "publicBrowser")
    calls = 0

    def _loader():
        nonlocal calls
        calls += 1
        return [1, 2, 3]

    output = resolveLensOutput(spec, availability, _loader)
    assert calls == 0
    assert output.status == "unavailable"
    assert output.value is None


def testUnavailableLensNeverCallsLoader() -> None:
    """Unavailable lens가 client loader를 실행하지 않는다.

    Args
        없음.

    Example
        pytest가 loader call count 0을 검증한다.

    Requires
        synthetic unavailable series lens.

    Raises
        AssertionError: unavailable loader가 호출될 때.
    """

    _assertUnavailableDoesNotCallLoader()


def _assertMissingPayloadPreserved() -> None:
    spec = _spec("table")
    report = _report((spec,))
    availability = next(entry for entry in report.entries if entry.environment == "localPython")
    output = resolveLensOutput(spec, availability, lambda: None)
    assert output.status == "missing"
    assert output.value is None
    assert output.reason == "sourceMissing"
    assert output.missingPolicy == "preserve"


def testMissingPayloadIsNotConvertedToZero() -> None:
    """Available lens의 missing payload를 0이나 빈 성공으로 바꾸지 않는다.

    Args
        없음.

    Example
        pytest가 missing output envelope를 검증한다.

    Requires
        synthetic available table lens.

    Raises
        AssertionError: missing payload가 ready 또는 0으로 바뀔 때.
    """

    _assertMissingPayloadPreserved()


def _assertUnknownCapabilityBlocked() -> None:
    spec = _spec("ranking")
    report = inspectLensAvailability(
        [spec],
        capabilityIds=[],
        skillIds=[spec.skillRef],
        publicPolicyReady=True,
    )
    assert report.invalidLensIds == (spec.lensId,)
    assert report.reasonCounts == {"unknownCapability": 3}


def testUnknownCapabilityCannotBecomeLens() -> None:
    """Catalog에 없는 capabilityRef를 lens로 노출하지 않는다.

    Args
        없음.

    Example
        pytest가 unknown capability 차단을 검증한다.

    Requires
        synthetic ranking lens.

    Raises
        AssertionError: unknown capability lens가 executable일 때.
    """

    _assertUnknownCapabilityBlocked()


def _assertDuplicateLensRejected() -> None:
    spec = _spec("distribution")
    with pytest.raises(ValueError, match="duplicate lensId"):
        _report((spec, spec))


def testDuplicateLensIdIsRejected() -> None:
    """같은 lensId 두 개가 registry에 들어가지 못하게 한다.

    Args
        없음.

    Example
        pytest가 duplicate lens rejection을 검증한다.

    Requires
        synthetic distribution lens.

    Raises
        AssertionError: duplicate lens가 조용히 수용될 때.
    """

    _assertDuplicateLensRejected()


def _assertCatalogReadinessCanBecomeTrue() -> None:
    capabilities = {
        "cap.scalar": {
            "returns": "float",
            "outputArchetype": "scalar",
            "unit": "ratio",
            "coveragePolicy": "numerator and denominator",
            "missingPolicy": "preserve",
            "runtimeCompatibility": {"publicBrowser": {"status": "available"}},
        }
    }
    skills = [
        {
            "id": "skill.scalar",
            "runtimeCompatibility": {"publicBrowser": {"status": "available"}},
        }
    ]
    report = inspectCatalogLensReadiness(
        capabilities,
        skills,
        sourceCount=1,
        reviewedReceiptCount=1,
    )
    assert report.currentPublicLensReadyCount == 1
    assert report.publicLensReady is True


def testCompleteCatalogAndPolicyCanBecomePublicReady() -> None:
    """완전한 semantic runtime 선언과 receipt가 positive gate를 통과한다.

    Args
        없음.

    Example
        pytest가 catalog readiness positive branch를 검증한다.

    Requires
        synthetic complete catalog fixture.

    Raises
        AssertionError: 완전한 catalog가 ready가 아닐 때.
    """

    _assertCatalogReadinessCanBecomeTrue()
