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
    PolicyAdmissionEvidence,
    PolicyEvaluationError,
    PolicyEvaluationSpec,
    PolicyOosEpisode,
    PolicyOosLedgerSnapshot,
    PolicyPathPrimitive,
    admitPolicyOosEpisode,
    appendPolicyOosEpisode,
    buildPolicyOosEpisode,
    evaluatePolicyOos,
    initializePolicyOosLedger,
    issuePolicyEvaluationCertificate,
    readPolicyOosLedger,
    sealPolicyOosBatch,
    validatePolicyEvaluationCertificate,
    weightedLowerCvar,
)
from dartlab.simulate.vintage import VintageRef, canonicalPayloadBytes, canonicalPayloadHash
from dartlab.simulate.world import (
    ActionSpec,
    LawSpec,
    ObjectiveSpec,
    ScenarioPath,
    SimulationSpecError,
    StrategySpec,
    VariableSpec,
    WorldModel,
    WorldState,
    bindAdmittedPathContent,
    bindPathAdmissionReceipt,
    constraintContractHash,
    objectiveContractHash,
    pathSetAdmissionArtifact,
    pathSetAdmissionSubjectHash,
    simulateWorld,
    strategyContractHash,
)


def _episodePayload(episode):
    return {
        name: getattr(episode, name)
        for name in episode.__dataclass_fields__
        if name not in {"episodeId", "episodeReceiptId"}
    }


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
    return (
        run,
        paths,
        baseline,
        candidate,
        objective,
        outcomeReceipt.receiptId,
        verifier,
        registry,
        artifacts,
        privateBytes,
        trusted,
    )


def _issueTestReceipt(
    context,
    *,
    kind,
    content,
    subjectHash=None,
    status="admitted",
    knowledgeAsOf="20191231",
    issuedAt="20191231T000000Z",
    ruleId=None,
    ruleHash=None,
    parentReceiptIds=(),
):
    registry, artifacts, privateBytes, trusted = context
    artifactHash = putAdmissionArtifact(artifacts, content)
    return issueAdmissionReceipt(
        registry,
        artifacts,
        privateKey=privateBytes,
        kind=kind,
        subjectHash=artifactHash if subjectHash is None else subjectHash,
        artifactHash=artifactHash,
        parentReceiptIds=parentReceiptIds,
        ruleId=ruleId or f"test-{kind}",
        ruleVersion="1",
        ruleHash=ruleHash or canonicalPayloadHash({"rule": kind}),
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuerExecutableHash=sha256(b"test-policy-issuer-v1").hexdigest(),
        knowledgeAsOf=knowledgeAsOf,
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency="week",
        stepSpan=1,
        maxAdmittedStep=1,
        status=status,
        issuedAt=issuedAt,
        trustedIssuers=trusted,
    )


def _admittedPolicyFixture(
    tmp_path,
    *,
    executableHash=None,
    baselineHash=None,
    candidateHash=None,
    constraintHash=None,
    pathRuleHash=None,
):
    registry = tmp_path / "admission.sqlite"
    artifacts = tmp_path / "artifacts"
    ledger = tmp_path / "policy-oos.sqlite"
    initializeAdmissionRegistry(registry)
    initializePolicyOosLedger(ledger)
    private = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    privateBytes = private.private_bytes_raw()
    public = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    trusted = {"test-key": TrustedIssuer("test-issuer", "test-key", public)}
    context = (registry, artifacts, privateBytes, trusted)
    verifier = AdmissionVerifier(registry, artifacts, trusted)
    pathRuleHash = pathRuleHash or canonicalPayloadHash({"rule": "paired-paths"})
    pathVintageReceipt = _issueTestReceipt(
        context,
        kind="dataVintage",
        content=b"historical path input vintage",
        status="verifiedVintage",
    )
    historicalPaths = tuple(
        ScenarioPath(
            f"p-{index:03d}",
            ({"shock": float(index)},),
            weight=1.0,
            weightKind="subjective",
            frequency="week",
            certificateId="1" * 64,
            validationStatus="admitted",
            maxAdmittedStep=1,
            knowledgeAsOf="20191231",
            historyStatus="asKnown",
        )
        for index in range(125)
    )
    pathReceipt = _issueTestReceipt(
        context,
        kind="pathSet",
        content=pathSetAdmissionArtifact(historicalPaths),
        ruleId="paired-paths",
        ruleHash=pathRuleHash,
        parentReceiptIds=(pathVintageReceipt.receiptId,),
    )
    outcomeReceipt = _issueTestReceipt(
        context,
        kind="dataVintage",
        content=b"outcome panel known 2021-01-01",
        status="verifiedVintage",
        knowledgeAsOf="20210101",
        issuedAt="20210101T000000Z",
    )
    dataVintageHash = canonicalPayloadHash({"initial": "as-known"})
    executableHash = executableHash or canonicalPayloadHash({"executable": "policy-world-v1"})
    baselineHash = baselineHash or canonicalPayloadHash({"strategy": "baseline-v1"})
    candidateHash = candidateHash or canonicalPayloadHash({"strategy": "candidate-v1"})
    initialReceipt = _issueTestReceipt(
        context,
        kind="initialState",
        content=b"initial state",
        subjectHash=dataVintageHash,
    )
    modelReceipt = _issueTestReceipt(
        context,
        kind="modelExecutable",
        content=b"world executable",
        subjectHash=executableHash,
    )
    baselineReceipt = _issueTestReceipt(
        context,
        kind="strategy",
        content=b"baseline strategy",
        subjectHash=baselineHash,
    )
    candidateReceipt = _issueTestReceipt(
        context,
        kind="strategy",
        content=b"candidate strategy",
        subjectHash=candidateHash,
    )
    noParameterHash = sha256(b"dartlab.policy-oos.no-parameter-contract.v1").hexdigest()
    signedEpisodes = []
    for index in range(40):
        raw = _episode(index)
        episodeConstraintHash = constraintHash or raw.constraintContractHash
        originKey = canonicalPayloadHash(
            {
                "protocol": raw.schemaVersion,
                "originAsOf": raw.originAsOf,
                "outcomeThrough": raw.outcomeThrough,
                "executableHash": executableHash,
                "baselineContract": baselineHash,
                "candidateContract": candidateHash,
                "objectiveContract": raw.objectiveContractHash,
                "constraintContract": episodeConstraintHash,
                "pathRuleHash": pathRuleHash,
                "parameterContract": noParameterHash,
            }
        )
        raw = replace(
            raw,
            episodeId="",
            originKey=originKey,
            outcomeAvailableAt="20210101",
            evaluationKnowledgeAsOf="20210101",
            executableHash=executableHash,
            dataVintageHash=dataVintageHash,
            pathAdmissionReceiptId=pathReceipt.receiptId,
            pathContentHash=pathReceipt.subjectHash,
            pathRuleId=pathReceipt.ruleId,
            pathRuleVersion=pathReceipt.ruleVersion,
            pathRuleHash=pathRuleHash,
            parameterContractHash=noParameterHash,
            outcomeVintageReceiptId=outcomeReceipt.receiptId,
            baselineStrategyContractHash=baselineHash,
            candidateStrategyContractHash=candidateHash,
            constraintContractHash=episodeConstraintHash,
        )
        raw = replace(raw, episodeId=canonicalPayloadHash(_episodePayload(raw)))
        signed = admitPolicyOosEpisode(
            raw,
            registry,
            artifacts,
            privateKey=privateBytes,
            initialStateReceiptId=initialReceipt.receiptId,
            modelReceiptId=modelReceipt.receiptId,
            baselineStrategyReceiptId=baselineReceipt.receiptId,
            candidateStrategyReceiptId=candidateReceipt.receiptId,
            issuerId="test-issuer",
            issuerKeyId="test-key",
            issuerExecutableHash=sha256(b"test-policy-issuer-v1").hexdigest(),
            issuedAt="20210101T120000Z",
            trustedIssuers=trusted,
        )
        appendPolicyOosEpisode(ledger, signed, admissionVerifier=verifier)
        signedEpisodes.append(signed)
    snapshot = readPolicyOosLedger(ledger, admissionVerifier=verifier)
    return {
        "registry": registry,
        "artifacts": artifacts,
        "ledger": ledger,
        "privateKey": privateBytes,
        "trusted": trusted,
        "verifier": verifier,
        "snapshot": snapshot,
        "episodes": tuple(signedEpisodes),
        "executableHash": executableHash,
        "baselineHash": baselineHash,
        "candidateHash": candidateHash,
        "pathRuleHash": pathRuleHash,
        "parameterContractHash": noParameterHash,
    }


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
    run, paths, baseline, candidate, objective, outcomeReceiptId, verifier, *_ = _signedRun(tmp_path)
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


def testTypedEpisodeSignerRejectsWrongKeyAndFutureDecisionParent(tmp_path) -> None:
    run, paths, baseline, candidate, objective, outcomeReceiptId, verifier, *context = _signedRun(tmp_path)
    registry, artifacts, privateBytes, trusted = context
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
    receiptContext = (registry, artifacts, privateBytes, trusted)
    initialReceipt = _issueTestReceipt(
        receiptContext,
        kind="initialState",
        content=b"signed initial state",
        subjectHash=episode.dataVintageHash,
    )
    modelReceipt = _issueTestReceipt(
        receiptContext,
        kind="modelExecutable",
        content=b"signed model executable",
        subjectHash=episode.executableHash,
    )
    baselineReceipt = _issueTestReceipt(
        receiptContext,
        kind="strategy",
        content=b"signed baseline strategy",
        subjectHash=episode.baselineStrategyContractHash,
    )
    candidateReceipt = _issueTestReceipt(
        receiptContext,
        kind="strategy",
        content=b"signed candidate strategy",
        subjectHash=episode.candidateStrategyContractHash,
    )
    signerArguments = {
        "initialStateReceiptId": initialReceipt.receiptId,
        "modelReceiptId": modelReceipt.receiptId,
        "baselineStrategyReceiptId": baselineReceipt.receiptId,
        "candidateStrategyReceiptId": candidateReceipt.receiptId,
        "issuerId": "test-issuer",
        "issuerKeyId": "test-key",
        "issuerExecutableHash": sha256(b"test-policy-issuer-v1").hexdigest(),
        "issuedAt": "20250105T120000Z",
        "trustedIssuers": trusted,
    }
    wrongKey = Ed25519PrivateKey.generate().private_bytes_raw()
    with pytest.raises(PolicyEvaluationError, match="does not match"):
        admitPolicyOosEpisode(
            episode,
            registry,
            artifacts,
            privateKey=wrongKey,
            **signerArguments,
        )
    futureModelReceipt = _issueTestReceipt(
        receiptContext,
        kind="modelExecutable",
        content=b"future model executable",
        subjectHash=episode.executableHash,
        knowledgeAsOf="20250103",
        issuedAt="20250103T000000Z",
    )
    with pytest.raises(PolicyEvaluationError, match="after the origin"):
        admitPolicyOosEpisode(
            episode,
            registry,
            artifacts,
            privateKey=privateBytes,
            **{**signerArguments, "modelReceiptId": futureModelReceipt.receiptId},
        )
    drifted = replace(
        episode,
        episodeId="",
        paths=(replace(episode.paths[0], pathId="substituted-path"),),
    )
    drifted = replace(drifted, episodeId=canonicalPayloadHash(_episodePayload(drifted)))
    with pytest.raises(PolicyEvaluationError, match="drifted from its admitted artifact"):
        admitPolicyOosEpisode(
            drifted,
            registry,
            artifacts,
            privateKey=privateBytes,
            **signerArguments,
        )
    signed = admitPolicyOosEpisode(
        episode,
        registry,
        artifacts,
        privateKey=privateBytes,
        **signerArguments,
    )
    assert signed.admissionStatus == "admitted"
    assert verifier.verify(signed.episodeReceiptId, expectedKind="policyEpisode").artifactHash == signed.episodeId
    ledger = tmp_path / "signed-policy-oos.sqlite"
    initializePolicyOosLedger(ledger)
    with pytest.raises(PolicyEvaluationError, match="runtime verifier"):
        appendPolicyOosEpisode(ledger, signed)
    appendPolicyOosEpisode(ledger, signed, admissionVerifier=verifier)
    with pytest.raises(PolicyEvaluationError, match="runtime verifier"):
        readPolicyOosLedger(ledger)
    assert readPolicyOosLedger(ledger, admissionVerifier=verifier).episodes == (signed,)
    forged = replace(episode, episodeId="", admissionStatus="admitted")
    forged = replace(forged, episodeId=canonicalPayloadHash(_episodePayload(forged)))
    forgedArtifact = putAdmissionArtifact(artifacts, canonicalPayloadBytes(_episodePayload(forged)))
    forgedReceipt = issueAdmissionReceipt(
        registry,
        artifacts,
        privateKey=privateBytes,
        kind="policyEpisode",
        subjectHash=forged.episodeId,
        artifactHash=forgedArtifact,
        parentReceiptIds=(
            episode.pathAdmissionReceiptId,
            episode.outcomeVintageReceiptId,
            initialReceipt.receiptId,
            modelReceipt.receiptId,
            baselineReceipt.receiptId,
            candidateReceipt.receiptId,
        ),
        ruleId="caller-selected-rule",
        ruleVersion="1",
        ruleHash=canonicalPayloadHash({"rule": "caller-selected"}),
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuerExecutableHash=sha256(b"test-policy-issuer-v1").hexdigest(),
        knowledgeAsOf="20250105",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        frequency="step",
        stepSpan=1,
        maxAdmittedStep=1,
        status="admitted",
        issuedAt="20250105T120000Z",
        trustedIssuers=trusted,
    )
    forged = replace(forged, episodeReceiptId=forgedReceipt.receiptId)
    forgedLedger = tmp_path / "forged-policy-oos.sqlite"
    initializePolicyOosLedger(forgedLedger)
    with pytest.raises(PolicyEvaluationError, match="typed admission rule mismatch"):
        appendPolicyOosEpisode(forgedLedger, forged, admissionVerifier=verifier)


def testSignedBatchAndRawReplayAreRequiredForPolicyAdmission(tmp_path) -> None:
    fixture = _admittedPolicyFixture(tmp_path)
    batch = sealPolicyOosBatch(
        fixture["snapshot"],
        fixture["registry"],
        fixture["artifacts"],
        privateKey=fixture["privateKey"],
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuerExecutableHash="1" * 64,
        issuedAt="20210102T000000Z",
        trustedIssuers=fixture["trusted"],
    )
    certificate = issuePolicyEvaluationCertificate(
        fixture["snapshot"],
        batch,
        PolicyEvaluationSpec(materialityMargin=0.05),
        fixture["registry"],
        fixture["artifacts"],
        privateKey=fixture["privateKey"],
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuerExecutableHash="1" * 64,
        issuedAt="20210103T000000Z",
        trustedIssuers=fixture["trusted"],
    )
    first = fixture["episodes"][0]
    validationArguments = {
        "decisionAsOf": "20210104",
        "executableHash": fixture["executableHash"],
        "baselineStrategyContractHash": fixture["baselineHash"],
        "candidateStrategyContractHash": fixture["candidateHash"],
        "objectiveContractHash": first.objectiveContractHash,
        "constraintContractHash": first.constraintContractHash,
        "pathRuleHash": fixture["pathRuleHash"],
        "parameterContractHash": fixture["parameterContractHash"],
        "pathFrequency": "week",
        "pathStepSpan": 1,
        "pathHorizon": 1,
    }
    report = validatePolicyEvaluationCertificate(
        fixture["snapshot"],
        batch,
        certificate,
        fixture["verifier"],
        **validationArguments,
    )
    assert certificate.status == "policyAdmitted"
    assert report.status == "statisticallyEligible"
    assert report.nOrigins == 40
    with pytest.raises(PolicyEvaluationError, match="content hash"):
        validatePolicyEvaluationCertificate(
            fixture["snapshot"],
            batch,
            replace(certificate, spec=replace(certificate.spec, materialityMargin=0.0)),
            fixture["verifier"],
            **validationArguments,
        )
    with pytest.raises(PolicyEvaluationError, match="unavailable"):
        validatePolicyEvaluationCertificate(
            fixture["snapshot"],
            batch,
            certificate,
            fixture["verifier"],
            **{**validationArguments, "decisionAsOf": "20210102"},
        )
    with pytest.raises(PolicyEvaluationError, match="current decision contract"):
        validatePolicyEvaluationCertificate(
            fixture["snapshot"],
            batch,
            certificate,
            fixture["verifier"],
            **{**validationArguments, "executableHash": "9" * 64},
        )


def testRuntimeRecommendationOpensOnlyForMatchingPolicyCertificate(tmp_path) -> None:
    def transition(context):
        return {"metric": context.shocks["shock"] + context.actions["invest"]}

    model = WorldModel(
        "admitted-policy-world",
        "1",
        (VariableSpec("shock", "ratio", "shock"), VariableSpec("metric", "ratio", "metric")),
        (
            ActionSpec(
                "invest",
                "ratio",
                0.0,
                1.0,
                0,
                0.0,
                "accountingIdentity",
                "contractual test action",
            ),
        ),
        (
            LawSpec(
                "action-identity",
                outputs=("metric",),
                shockInputs=("shock",),
                actionInputs=("invest",),
                evidenceKind="accountingIdentity",
                provenance="contractual identity",
                fn=transition,
            ),
        ),
        stepFrequency="week",
    )
    baseline = StrategySpec("baseline", ({"invest": 0.0},), isBaseline=True, policyVersion="static-v1")
    candidate = StrategySpec("candidate", ({"invest": 1.0},), policyVersion="policy-v1")
    objective = ObjectiveSpec("metric", reducer="terminal", direction="maximize", risk="average")
    initial = WorldState({}, asOf="20210103", knowledgeAsOf="20210103", decisionAsOf="20210104")
    preliminaryPath = ScenarioPath("current", ({"shock": 0.0},), frequency="week")
    preliminary = simulateWorld(
        model,
        initial,
        (preliminaryPath,),
        (baseline, candidate),
        objectives=(objective,),
    )
    pathRuleHash = canonicalPayloadHash({"rule": "paired-paths"})
    fixture = _admittedPolicyFixture(
        tmp_path,
        executableHash=preliminary.executableHash,
        baselineHash=strategyContractHash(baseline),
        candidateHash=strategyContractHash(candidate),
        constraintHash=constraintContractHash(()),
        pathRuleHash=pathRuleHash,
    )
    batch = sealPolicyOosBatch(
        fixture["snapshot"],
        fixture["registry"],
        fixture["artifacts"],
        privateKey=fixture["privateKey"],
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuerExecutableHash="1" * 64,
        issuedAt="20210102T000000Z",
        trustedIssuers=fixture["trusted"],
    )
    certificate = issuePolicyEvaluationCertificate(
        fixture["snapshot"],
        batch,
        PolicyEvaluationSpec(materialityMargin=0.05),
        fixture["registry"],
        fixture["artifacts"],
        privateKey=fixture["privateKey"],
        issuerId="test-issuer",
        issuerKeyId="test-key",
        issuerExecutableHash="1" * 64,
        issuedAt="20210103T000000Z",
        trustedIssuers=fixture["trusted"],
    )
    receiptContext = (
        fixture["registry"],
        fixture["artifacts"],
        fixture["privateKey"],
        fixture["trusted"],
    )
    currentVintageReceipt = _issueTestReceipt(
        receiptContext,
        kind="dataVintage",
        content=b"current decision path vintage",
        status="verifiedVintage",
        knowledgeAsOf="20210103",
        issuedAt="20210103T000000Z",
    )
    currentVintage = VintageRef(
        artifactKind="shockPanel",
        provider="test",
        artifactId="current-path-vintage",
        artifactHash=currentVintageReceipt.artifactHash,
        payloadHash=currentVintageReceipt.subjectHash,
        knowledgeAsOf="20210103",
        availableAt="20210103",
        revisionPolicy="asKnown",
        coverage="asOfExact",
        receiptId=currentVintageReceipt.receiptId,
    )
    currentPaths = bindAdmittedPathContent(
        (
            ScenarioPath(
                "current",
                ({"shock": 0.0},),
                frequency="week",
                certificateId="2" * 64,
                validationStatus="admitted",
                maxAdmittedStep=1,
                knowledgeAsOf="20210103",
                historyStatus="asKnown",
                vintage=currentVintage,
            ),
        )
    )
    currentPathReceipt = _issueTestReceipt(
        receiptContext,
        kind="pathSet",
        content=pathSetAdmissionArtifact(currentPaths),
        knowledgeAsOf="20210103",
        issuedAt="20210103T000000Z",
        ruleId="paired-paths",
        ruleHash=pathRuleHash,
        parentReceiptIds=(currentVintageReceipt.receiptId,),
    )
    currentPaths = bindPathAdmissionReceipt(currentPaths, currentPathReceipt.receiptId)
    conditional = simulateWorld(
        model,
        initial,
        currentPaths,
        (baseline, candidate),
        objectives=(objective,),
        admissionVerifier=fixture["verifier"],
    )
    assert conditional.decisionStatus == "conditionalOnly"
    assert conditional.recommendation is None
    admitted = simulateWorld(
        model,
        initial,
        currentPaths,
        (baseline, candidate),
        objectives=(objective,),
        admissionVerifier=fixture["verifier"],
        policyAdmissionEvidence=PolicyAdmissionEvidence(fixture["snapshot"], batch, certificate),
    )
    assert admitted.decisionStatus == "comparable"
    assert admitted.recommendation == "candidate"
    assert admitted.policyEvaluationCertificateId == certificate.certificateId
    with pytest.raises(SimulationSpecError, match="policy admission verification failed"):
        simulateWorld(
            model,
            initial,
            currentPaths,
            (baseline, replace(candidate, actionsByStep=({"invest": 0.5},))),
            objectives=(objective,),
            admissionVerifier=fixture["verifier"],
            policyAdmissionEvidence=PolicyAdmissionEvidence(fixture["snapshot"], batch, certificate),
        )
