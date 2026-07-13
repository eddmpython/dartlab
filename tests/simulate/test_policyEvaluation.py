"""Kill tests for raw paired-origin OOS ledger and policy statistics."""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import date, timedelta
from hashlib import sha256

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from dartlab.simulate.admissionRegistry import (
    AdmissionVerifier,
    TrustedIssuer,
    initializeAdmissionRegistry,
    issueAdmissionReceipt,
    putAdmissionArtifact,
)
from dartlab.simulate.policyEvaluation import (
    PolicyEvaluationError,
    PolicyEvaluationSpec,
    PolicyOosEpisode,
    PolicyOosLedgerSnapshot,
    PolicyPathPrimitive,
    appendPolicyOosEpisode,
    buildPolicyOosEpisode,
    evaluatePolicyOos,
    initializePolicyOosLedger,
    readPolicyOosLedger,
    weightedLowerCvar,
)
from dartlab.simulate.vintage import VintageRef, canonicalPayloadHash
from dartlab.simulate.world import (
    LawSpec,
    ObjectiveSpec,
    ScenarioPath,
    StrategySpec,
    VariableSpec,
    WorldModel,
    WorldState,
    bindAdmittedPathContent,
    bindPathAdmissionReceipt,
    objectiveContractHash,
    pathSetAdmissionArtifact,
    pathSetAdmissionSubjectHash,
    simulateWorld,
)


def _episodePayload(episode):
    return {name: getattr(episode, name) for name in episode.__dataclass_fields__ if name != "episodeId"}


def _stamp(day: date) -> str:
    return day.strftime("%Y%m%d")


def _episode(
    ordinal: int,
    *,
    pathCount: int = 125,
    candidateLift: float = 0.1,
    candidateBreach: bool = False,
) -> PolicyOosEpisode:
    origin = date(2020, 1, 3) + timedelta(days=7 * ordinal)
    objective = ObjectiveSpec("metric", reducer="terminal", direction="maximize", risk="average")
    paths = tuple(
        PolicyPathPrimitive(
            pathId=f"p-{pathIndex:03d}",
            pathOrdinal=pathIndex,
            pathWeight=1.0,
            parameterDrawHash=canonicalPayloadHash({}),
            baselineMetricByStep=(float(pathIndex),),
            candidateMetricByStep=(float(pathIndex) + candidateLift,),
            baselineBreachesByStep=((),),
            candidateBreachesByStep=(("limit",) if candidateBreach and pathIndex == 0 else (),),
            baselineTraceHash=canonicalPayloadHash({"o": ordinal, "p": pathIndex, "s": "b"}),
            candidateTraceHash=canonicalPayloadHash({"o": ordinal, "p": pathIndex, "s": "c"}),
        )
        for pathIndex in range(pathCount)
    )
    provisional = PolicyOosEpisode(
        episodeId="",
        originKey=canonicalPayloadHash({"origin": _stamp(origin)}),
        originOrdinal=ordinal,
        originAsOf=_stamp(origin),
        outcomeThrough=_stamp(origin + timedelta(days=28)),
        outcomeAvailableAt=_stamp(origin + timedelta(days=29)),
        evaluationKnowledgeAsOf=_stamp(origin + timedelta(days=30)),
        evidenceKind="modelReplay",
        runHash=canonicalPayloadHash({"run": ordinal}),
        resultHash=canonicalPayloadHash({"result": ordinal}),
        traceRoot=canonicalPayloadHash({"trace": ordinal}),
        executableHash="a" * 64,
        parameterHash=canonicalPayloadHash({"parameter": ordinal}),
        dataVintageHash=canonicalPayloadHash({"vintage": ordinal}),
        pathAdmissionReceiptId=canonicalPayloadHash({"pathReceipt": ordinal}),
        pathContentHash=canonicalPayloadHash({"pathContent": ordinal}),
        pathRuleId="path-rule",
        pathRuleVersion="1",
        pathRuleHash="b" * 64,
        parameterContractHash="c" * 64,
        outcomeVintageReceiptId=canonicalPayloadHash({"outcome": ordinal}),
        baselineStrategyId="baseline",
        baselinePolicyVersion="static-v1",
        baselineStrategyContractHash="d" * 64,
        candidateStrategyId="candidate",
        candidatePolicyVersion="policy-v1",
        candidateStrategyContractHash="e" * 64,
        objective=objective,
        objectiveContractHash=objectiveContractHash(objective),
        constraintContractHash="f" * 64,
        paths=paths,
    )
    return replace(provisional, episodeId=canonicalPayloadHash(_episodePayload(provisional)))


def _signedRun(tmp_path, *, traceLimit=None):
    registry = tmp_path / "admission.sqlite"
    artifacts = tmp_path / "artifacts"
    initializeAdmissionRegistry(registry)
    private = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    privateBytes = private.private_bytes_raw()
    public = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    trusted = {"test-key": TrustedIssuer("test-issuer", "test-key", public)}
    verifier = AdmissionVerifier(registry, artifacts, trusted)

    rawHash = putAdmissionArtifact(artifacts, b"decision-time shock panel")
    payloadHash = canonicalPayloadHash({"shock": [0.1]})
    vintageReceipt = issueAdmissionReceipt(
        registry,
        artifacts,
        privateKey=privateBytes,
        kind="dataVintage",
        subjectHash=payloadHash,
        artifactHash=rawHash,
        parentReceiptIds=(),
        ruleId="pit-vintage",
        ruleVersion="1",
        ruleHash=sha256(b"pit-vintage-v1").hexdigest(),
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuerExecutableHash=sha256(b"issuer-v1").hexdigest(),
        knowledgeAsOf="20250101",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency="step",
        stepSpan=1,
        maxAdmittedStep=1,
        status="verifiedVintage",
        issuedAt="20250101T000000Z",
        trustedIssuers=trusted,
    )
    vintage = VintageRef(
        artifactKind="shockPanel",
        provider="test",
        artifactId="shock-panel",
        artifactHash=rawHash,
        payloadHash=payloadHash,
        knowledgeAsOf="20250101",
        availableAt="20250101",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        receiptId=vintageReceipt.receiptId,
    )
    path = ScenarioPath(
        "path",
        ({"shock": 0.1},),
        certificateId="a" * 64,
        validationStatus="admitted",
        maxAdmittedStep=1,
        knowledgeAsOf="20250101",
        historyStatus="asKnown",
        vintage=vintage,
    )
    paths = bindAdmittedPathContent((path,))
    pathHash = putAdmissionArtifact(artifacts, pathSetAdmissionArtifact(paths))
    pathReceipt = issueAdmissionReceipt(
        registry,
        artifacts,
        privateKey=privateBytes,
        kind="pathSet",
        subjectHash=pathHash,
        artifactHash=pathHash,
        parentReceiptIds=(vintageReceipt.receiptId,),
        ruleId="path-admission",
        ruleVersion="1",
        ruleHash=sha256(b"path-admission-v1").hexdigest(),
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuerExecutableHash=sha256(b"path-issuer-v1").hexdigest(),
        knowledgeAsOf="20250101",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency="step",
        stepSpan=1,
        maxAdmittedStep=1,
        status="admitted",
        issuedAt="20250101T000000Z",
        trustedIssuers=trusted,
    )
    paths = bindPathAdmissionReceipt(paths, pathReceipt.receiptId)

    outcomeRaw = putAdmissionArtifact(artifacts, b"realized outcome")
    outcomePayload = canonicalPayloadHash({"outcome": 0.1})
    outcomeReceipt = issueAdmissionReceipt(
        registry,
        artifacts,
        privateKey=privateBytes,
        kind="dataVintage",
        subjectHash=outcomePayload,
        artifactHash=outcomeRaw,
        parentReceiptIds=(),
        ruleId="outcome-vintage",
        ruleVersion="1",
        ruleHash=sha256(b"outcome-vintage-v1").hexdigest(),
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuerExecutableHash=sha256(b"outcome-issuer-v1").hexdigest(),
        knowledgeAsOf="20250104",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency="step",
        stepSpan=1,
        maxAdmittedStep=1,
        status="verifiedVintage",
        issuedAt="20250105T000000Z",
        trustedIssuers=trusted,
    )
    model = WorldModel(
        "policy-oos-world",
        "1",
        (VariableSpec("shock", "ratio", "shock"), VariableSpec("metric", "ratio", "metric")),
        (),
        (
            LawSpec(
                "identity",
                outputs=("metric",),
                shockInputs=("shock",),
                fn=lambda ctx: {"metric": ctx.shocks["shock"]},
            ),
        ),
    )
    baseline = StrategySpec("baseline", ({},), isBaseline=True, policyVersion="static-v1")

    def policy(_):
        return {}

    candidate = StrategySpec(
        "candidate",
        ({},),
        policyVersion="policy-v1",
        policyProvenance="test-policy",
        policyFn=policy,
    )
    objective = ObjectiveSpec("metric", reducer="terminal", direction="maximize", risk="average")
    run = simulateWorld(
        model,
        WorldState({}, asOf="20250101", knowledgeAsOf="20250101", decisionAsOf="20250102"),
        paths,
        (baseline, candidate),
        objectives=(objective,),
        traceLimit=traceLimit,
        admissionVerifier=verifier,
    )
    return run, paths, baseline, candidate, objective, outcomeReceipt.receiptId, verifier


def testAppendOnlyLedgerRejectsDuplicateOriginAndMutation(tmp_path) -> None:
    database = tmp_path / "policy-oos.sqlite"
    initializePolicyOosLedger(database)
    first = _episode(0)
    appendPolicyOosEpisode(database, first)
    duplicate = replace(_episode(1), originKey=first.originKey)
    duplicate = replace(duplicate, episodeId=canonicalPayloadHash(_episodePayload(duplicate)))
    with pytest.raises(PolicyEvaluationError, match="duplicate"):
        appendPolicyOosEpisode(database, duplicate)
    with sqlite3.connect(database) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE policy_oos_episodes SET origin_key='x'")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM policy_oos_episodes")
    snapshot = readPolicyOosLedger(database)
    assert snapshot.episodes == (first,)
    assert len(snapshot.ledgerRoot) == 64
    with sqlite3.connect(database) as connection:
        connection.execute("DROP TRIGGER policy_oos_no_update")
        connection.execute("UPDATE policy_oos_episodes SET payload_json='{}'")
    with pytest.raises(PolicyEvaluationError, match="malformed"):
        readPolicyOosLedger(database)


def testStatisticalEligibilityIsDeterministicButNotAdmission() -> None:
    episodes = tuple(_episode(index) for index in range(40))
    snapshot = PolicyOosLedgerSnapshot(episodes, canonicalPayloadHash({"ledger": "complete"}))
    spec = PolicyEvaluationSpec(materialityMargin=0.05)
    first = evaluatePolicyOos(snapshot, spec)
    reordered = evaluatePolicyOos(PolicyOosLedgerSnapshot(tuple(reversed(episodes)), snapshot.ledgerRoot), spec)
    assert first == reordered
    assert first.status == "statisticallyEligible"
    assert first.admissionStatus == "documented"
    assert first.nOrigins == 40
    assert first.effectiveBlockCount >= 8
    assert first.minimumTailEffectivePaths >= 20
    assert first.primaryLowerBound == pytest.approx(0.1)
    assert first.cvarDeltaLowerBound == pytest.approx(0.1)


def testUniqueOriginFloorAndAnyHardBreachFailClosed() -> None:
    spec = PolicyEvaluationSpec(materialityMargin=0.05)
    short = tuple(_episode(index) for index in range(39))
    shortReport = evaluatePolicyOos(
        PolicyOosLedgerSnapshot(short, canonicalPayloadHash({"ledger": "short"})),
        spec,
    )
    assert shortReport.status == "insufficientEvidence"
    assert "insufficientOrigins" in shortReport.reasons
    breached = tuple(_episode(index, candidateBreach=index == 39) for index in range(40))
    breachReport = evaluatePolicyOos(
        PolicyOosLedgerSnapshot(breached, canonicalPayloadHash({"ledger": "breached"})),
        spec,
    )
    assert breachReport.status == "rejected"
    assert breachReport.candidateHardBreachCount == 1


def testCvarNoninferiorityUsesSeparatePolicyCvarsNotCvarOfDelta() -> None:
    baseline = (-100.0, 0.0)
    candidate = (0.0, -99.0)
    weights = (1.0, 1.0)
    baselineCvar = weightedLowerCvar(baseline, weights, 0.5)[0]
    candidateCvar = weightedLowerCvar(candidate, weights, 0.5)[0]
    deltaCvar = weightedLowerCvar(
        tuple(right - left for left, right in zip(baseline, candidate, strict=True)), weights, 0.5
    )[0]
    assert candidateCvar - baselineCvar == pytest.approx(1.0)
    assert deltaCvar == pytest.approx(-99.0)


def testEpisodeBuildsOnlyFromFullPairedRunAndKeepsModelReplayLabel(tmp_path) -> None:
    run, paths, baseline, candidate, objective, outcomeReceiptId, verifier = _signedRun(tmp_path)
    episode = buildPolicyOosEpisode(
        run,
        paths,
        baseline,
        candidate,
        objective,
        (),
        originOrdinal=0,
        outcomeThrough="20250103",
        outcomeAvailableAt="20250104",
        evaluationKnowledgeAsOf="20250105",
        outcomeVintageReceiptId=outcomeReceiptId,
        admissionVerifier=verifier,
    )
    assert episode.evidenceKind == "modelReplay"
    assert episode.admissionStatus == "documented"
    assert episode.originAsOf == run.decisionAsOf
    assert episode.pathContentHash == pathSetAdmissionSubjectHash(paths)
    assert episode.paths[0].baselineMetricByStep == (0.1,)
    compact = _signedRun(tmp_path / "compact", traceLimit=1)
    with pytest.raises(PolicyEvaluationError, match="full retained traces"):
        buildPolicyOosEpisode(
            compact[0],
            compact[1],
            compact[2],
            compact[3],
            compact[4],
            (),
            originOrdinal=0,
            outcomeThrough="20250103",
            outcomeAvailableAt="20250104",
            evaluationKnowledgeAsOf="20250105",
            outcomeVintageReceiptId=compact[5],
            admissionVerifier=compact[6],
        )
