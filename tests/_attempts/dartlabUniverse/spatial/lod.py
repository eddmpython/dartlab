"""Object, source, period, statement, evidence, relation 방향을 보존하는 semantic LOD."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from functools import lru_cache
from heapq import nsmallest

from ..catalog.models import CatalogObject, CatalogResource, CatalogState
from ..contracts import EpistemicClass, VerificationState
from ..graph.relations import GraphRelation
from ..graph.statements import GraphStatement
from ..ids import logicalId
from .contracts import (
    CommunityVersion,
    ConservationAssertion,
    DrillPath,
    LogicalCoordinate,
    MeaningPreservationReport,
    ProjectionRequest,
    SceneEdge,
    SceneNode,
    SceneProxy,
)
from .digest import spatialId, spatialPackedDigest
from .layout import communityAnchors


@dataclass(slots=True)
class _ProxyFacts:
    members: frozenset[str]
    memberDigest: str
    kindHistogram: tuple[tuple[str, int], ...]
    sourceHistogram: tuple[tuple[str, int], ...]
    epistemicHistogram: tuple[tuple[str, int], ...]
    verificationHistogram: tuple[tuple[str, int], ...]
    periodRange: tuple[str | None, str | None]
    statementRefs: frozenset[str]
    statementRefSetDigest: str
    evidenceRefs: frozenset[str]
    evidenceRefSetDigest: str
    relationDirections: dict[str, tuple[str, str]]
    relationRefSetDigest: str
    relationTypeDirectionDigest: str


@dataclass(frozen=True, slots=True)
class LodCompilation:
    proxies: tuple[SceneProxy, ...]
    nodes: tuple[SceneNode, ...]
    edges: tuple[SceneEdge, ...]
    drillPaths: tuple[DrillPath, ...]
    meaningReport: MeaningPreservationReport
    digest: str


def _histogram(values) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(Counter(values).items()))


def _periodRange(
    objects: tuple[CatalogObject, ...], statements: tuple[GraphStatement, ...]
) -> tuple[str | None, str | None]:
    starts = [item.validTime.start for item in objects if item.validTime.start]
    ends = [item.validTime.end for item in objects if item.validTime.end]
    for statement in statements:
        if statement.periodStart:
            starts.append(statement.periodStart)
        if statement.instant:
            starts.append(statement.instant)
            ends.append(statement.instant)
        if statement.periodEnd:
            ends.append(statement.periodEnd)
    return (min(starts) if starts else None, max(ends) if ends else None)


@lru_cache(maxsize=None)
def _styleToken(epistemic: EpistemicClass, verification: VerificationState) -> str:
    return f"epistemic:{epistemic.value.casefold()}:verification:{verification.value.casefold()}"


def _completeProxyFacts(
    *,
    members: frozenset[str],
    memberDigest: str,
    kindHistogram: tuple[tuple[str, int], ...],
    sourceHistogram: tuple[tuple[str, int], ...],
    epistemicHistogram: tuple[tuple[str, int], ...],
    verificationHistogram: tuple[tuple[str, int], ...],
    periodRange: tuple[str | None, str | None],
    statementRefs: frozenset[str],
    evidenceRefs: frozenset[str],
    relationDirections: dict[str, tuple[str, str]],
    needsConservationDigest: bool,
) -> _ProxyFacts:
    orderedDirections = tuple(sorted(relationDirections.items())) if needsConservationDigest else ()
    return _ProxyFacts(
        members=members,
        memberDigest=memberDigest,
        kindHistogram=kindHistogram,
        sourceHistogram=sourceHistogram,
        epistemicHistogram=epistemicHistogram,
        verificationHistogram=verificationHistogram,
        periodRange=periodRange,
        statementRefs=statementRefs,
        statementRefSetDigest=spatialPackedDigest("STATEMENT_REF_SET", tuple(sorted(statementRefs))),
        evidenceRefs=evidenceRefs,
        evidenceRefSetDigest=spatialPackedDigest("EVIDENCE_REF_SET", tuple(sorted(evidenceRefs))),
        relationDirections=relationDirections,
        relationRefSetDigest=(
            spatialPackedDigest("RELATION_REF_SET", tuple(relationId for relationId, _value in orderedDirections))
            if needsConservationDigest
            else ""
        ),
        relationTypeDirectionDigest=(
            spatialPackedDigest("RELATION_TYPE_DIRECTION", orderedDirections) if needsConservationDigest else ""
        ),
    )


def _proxyFacts(
    communities: tuple[CommunityVersion, ...],
    objects: tuple[CatalogObject, ...],
    resources: dict[str, CatalogResource],
    evidenceByObject: dict[str, list[str]],
    statements: tuple[GraphStatement, ...],
    relations: tuple[GraphRelation, ...],
    rootCommunityId: str,
    homeL1: dict[str, str],
    homeL2: dict[str, str],
) -> dict[str, _ProxyFacts]:
    objectById = {item.objectId: item for item in objects}
    childrenByParent: dict[str, list[str]] = defaultdict(list)
    for community in communities:
        if community.parentCommunityLogicalId:
            childrenByParent[community.parentCommunityLogicalId].append(community.communityLogicalId)
    statementsByObject: dict[str, list[GraphStatement]] = defaultdict(list)
    for item in statements:
        if item.subjectRef in objectById:
            statementsByObject[item.subjectRef].append(item)
        if item.objectRef in objectById and item.objectRef != item.subjectRef:
            statementsByObject[item.objectRef].append(item)
    relationDirections: dict[str, dict[str, tuple[str, str]]] = defaultdict(dict)
    for relation in relations:
        fromCluster = homeL2.get(relation.fromRef)
        toCluster = homeL2.get(relation.toRef)
        if fromCluster is not None and toCluster is not None:
            relationDirections[rootCommunityId][relation.relationId] = (relation.relationType, "INTERNAL")
        elif fromCluster is not None:
            relationDirections[rootCommunityId][relation.relationId] = (relation.relationType, "OUTBOUND")
        elif toCluster is not None:
            relationDirections[rootCommunityId][relation.relationId] = (relation.relationType, "INBOUND")
        for fromCommunity, toCommunity in (
            (homeL1.get(relation.fromRef), homeL1.get(relation.toRef)),
            (fromCluster, toCluster),
        ):
            if fromCommunity is not None and fromCommunity == toCommunity:
                relationDirections[fromCommunity][relation.relationId] = (relation.relationType, "INTERNAL")
            else:
                if fromCommunity is not None:
                    relationDirections[fromCommunity][relation.relationId] = (relation.relationType, "OUTBOUND")
                if toCommunity is not None:
                    relationDirections[toCommunity][relation.relationId] = (relation.relationType, "INBOUND")
    facts = {}
    for community in reversed(communities):
        childFacts = tuple(facts[item] for item in childrenByParent.get(community.communityLogicalId, ()))
        if childFacts:
            histograms = []
            for fieldName in (
                "kindHistogram",
                "sourceHistogram",
                "epistemicHistogram",
                "verificationHistogram",
            ):
                combined = Counter()
                for child in childFacts:
                    combined.update(dict(getattr(child, fieldName)))
                histograms.append(tuple(sorted(combined.items())))
            starts = [item.periodRange[0] for item in childFacts if item.periodRange[0]]
            ends = [item.periodRange[1] for item in childFacts if item.periodRange[1]]
            facts[community.communityLogicalId] = _completeProxyFacts(
                members=frozenset().union(*(item.members for item in childFacts)),
                memberDigest=community.memberDigest,
                kindHistogram=histograms[0],
                sourceHistogram=histograms[1],
                epistemicHistogram=histograms[2],
                verificationHistogram=histograms[3],
                periodRange=(min(starts) if starts else None, max(ends) if ends else None),
                statementRefs=frozenset().union(*(item.statementRefs for item in childFacts)),
                evidenceRefs=frozenset().union(*(item.evidenceRefs for item in childFacts)),
                relationDirections=relationDirections[community.communityLogicalId],
                needsConservationDigest=True,
            )
            continue
        memberObjects = tuple(objectById[item] for item in community.memberObjectIds)
        memberStatementsById = {
            statement.statementId: statement
            for objectId in community.memberObjectIds
            for statement in statementsByObject.get(objectId, ())
        }
        memberStatements = tuple(memberStatementsById.values())
        evidenceRefs = {
            evidenceId for objectId in community.memberObjectIds for evidenceId in evidenceByObject.get(objectId, ())
        }
        for statement in memberStatements:
            evidenceRefs.update(statement.evidenceRefs)
        facts[community.communityLogicalId] = _completeProxyFacts(
            members=frozenset(community.memberObjectIds),
            memberDigest=community.memberDigest,
            kindHistogram=_histogram(item.objectKind for item in memberObjects),
            sourceHistogram=_histogram(resources[item.resourceRefs[0]].sourceRef for item in memberObjects),
            epistemicHistogram=_histogram(item.epistemicClass.value for item in memberObjects),
            verificationHistogram=_histogram(item.verificationState.value for item in memberObjects),
            periodRange=_periodRange(memberObjects, memberStatements),
            statementRefs=frozenset(memberStatementsById),
            evidenceRefs=frozenset(evidenceRefs),
            relationDirections=relationDirections[community.communityLogicalId],
            needsConservationDigest=False,
        )
    return facts


def _relationHistogram(facts: _ProxyFacts) -> tuple[tuple[str, int], ...]:
    return _histogram(f"{relationType}:{direction}" for relationType, direction in facts.relationDirections.values())


def _assertion(parentId: str, kind: str, expected, actual) -> ConservationAssertion:
    passed = expected == actual
    expectedDigest = spatialPackedDigest("MEANING_ASSERTION", expected)
    actualDigest = expectedDigest if passed else spatialPackedDigest("MEANING_ASSERTION", actual)
    return ConservationAssertion(parentId, kind, passed, expectedDigest, actualDigest)


def _setAssertion(
    parentId: str,
    kind: str,
    expected: frozenset[str],
    actual: frozenset[str],
    expectedDigest: str,
) -> ConservationAssertion:
    passed = expected == actual
    actualDigest = expectedDigest if passed else spatialPackedDigest(kind, tuple(sorted(actual)))
    return ConservationAssertion(parentId, kind, passed, expectedDigest, actualDigest)


def _drillPath(
    targetKind: str,
    targetId: str,
    levelRefs: tuple[tuple[str, str], ...],
    detailRef: str,
    evidenceRefs: tuple[str, ...],
) -> DrillPath:
    digest = spatialPackedDigest("DRILL_PATH", targetKind, targetId, levelRefs, detailRef, evidenceRefs)
    return DrillPath(targetKind, targetId, levelRefs, detailRef, evidenceRefs, digest)


def _meaningReport(
    communities: tuple[CommunityVersion, ...],
    facts: dict[str, _ProxyFacts],
) -> MeaningPreservationReport:
    childrenByParent: dict[str, list[CommunityVersion]] = defaultdict(list)
    for item in communities:
        if item.parentCommunityLogicalId:
            childrenByParent[item.parentCommunityLogicalId].append(item)
    assertions = []
    for parentId, children in sorted(childrenByParent.items()):
        parent = facts[parentId]
        childFacts = tuple(facts[item.communityLogicalId] for item in children)
        memberUnion = frozenset().union(*(item.members for item in childFacts))
        assertions.append(
            _setAssertion(parentId, "PRIMARY_MEMBER_SET", parent.members, memberUnion, parent.memberDigest)
        )
        for kind, fieldName in (
            ("KIND_HISTOGRAM", "kindHistogram"),
            ("SOURCE_HISTOGRAM", "sourceHistogram"),
            ("EPISTEMIC_HISTOGRAM", "epistemicHistogram"),
            ("VERIFICATION_HISTOGRAM", "verificationHistogram"),
        ):
            combined = Counter()
            for child in childFacts:
                combined.update(dict(getattr(child, fieldName)))
            assertions.append(_assertion(parentId, kind, getattr(parent, fieldName), tuple(sorted(combined.items()))))
        childStarts = [item.periodRange[0] for item in childFacts if item.periodRange[0]]
        childEnds = [item.periodRange[1] for item in childFacts if item.periodRange[1]]
        childPeriod = (min(childStarts) if childStarts else None, max(childEnds) if childEnds else None)
        assertions.append(_assertion(parentId, "PERIOD_RANGE", parent.periodRange, childPeriod))
        statementUnion = frozenset().union(*(item.statementRefs for item in childFacts))
        evidenceUnion = frozenset().union(*(item.evidenceRefs for item in childFacts))
        relationUnion = frozenset().union(*(frozenset(item.relationDirections) for item in childFacts))
        assertions.append(
            _setAssertion(
                parentId,
                "STATEMENT_REF_SET",
                parent.statementRefs,
                statementUnion,
                parent.statementRefSetDigest,
            )
        )
        assertions.append(
            _setAssertion(
                parentId,
                "EVIDENCE_REF_SET",
                parent.evidenceRefs,
                evidenceUnion,
                parent.evidenceRefSetDigest,
            )
        )
        parentRelationRefs = frozenset(parent.relationDirections)
        assertions.append(
            _setAssertion(
                parentId,
                "RELATION_REF_SET",
                parentRelationRefs,
                relationUnion,
                parent.relationRefSetDigest,
            )
        )
        directionPassed = parentRelationRefs == relationUnion
        assertions.append(
            ConservationAssertion(
                parentId,
                "RELATION_TYPE_DIRECTION",
                directionPassed,
                parent.relationTypeDirectionDigest,
                (
                    parent.relationTypeDirectionDigest
                    if directionPassed
                    else spatialPackedDigest(
                        "RELATION_TYPE_DIRECTION",
                        tuple(
                            sorted(
                                (relationId, parent.relationDirections[relationId])
                                for relationId in relationUnion
                                if relationId in parent.relationDirections
                            )
                        ),
                    )
                ),
            )
        )
    ordered = tuple(sorted(assertions, key=lambda item: (item.parentCommunityId, item.assertionKind)))
    passedCount = sum(item.passed for item in ordered)
    failures = () if passedCount == len(ordered) else ("MEANING_CONSERVATION_FAILED",)
    base = MeaningPreservationReport(
        passed=not failures,
        assertionCount=len(ordered),
        passedAssertionCount=passedCount,
        meaningPreservation=passedCount / len(ordered) if ordered else 1.0,
        assertions=ordered,
        failureCodes=failures,
        digest="",
    )
    return replace(base, digest=spatialPackedDigest("MEANING_REPORT", base))


def _compileEdges(
    relations: tuple[GraphRelation, ...],
    homeL1: dict[str, str],
    homeL2: dict[str, str],
) -> tuple[SceneEdge, ...]:
    visibleIds = frozenset(homeL2)
    levelThreeEdges = []
    aggregate: dict[tuple[int, str, str, str, EpistemicClass, VerificationState], list[GraphRelation]] = defaultdict(
        list
    )
    for relation in relations:
        if relation.fromRef not in visibleIds or relation.toRef not in visibleIds:
            continue
        for level, homes in ((1, homeL1), (2, homeL2)):
            fromRef = homes[relation.fromRef]
            toRef = homes[relation.toRef]
            if fromRef != toRef:
                aggregate[
                    (level, fromRef, toRef, relation.relationType, relation.epistemicClass, relation.verificationState)
                ].append(relation)
        if homeL2[relation.fromRef] == homeL2[relation.toRef]:
            levelThreeEdges.append(
                SceneEdge(
                    edgeId=relation.relationId,
                    relationType=relation.relationType,
                    fromNodeId=relation.fromRef,
                    toNodeId=relation.toRef,
                    weight=relation.weight if relation.weight is not None else 1.0,
                    epistemicClass=relation.epistemicClass,
                    verificationState=relation.verificationState,
                    evidenceCount=len(relation.evidenceRefs),
                    lodLevel=3,
                    aggregateCount=1,
                    styleToken=_styleToken(relation.epistemicClass, relation.verificationState),
                    detailRef=relation.relationId,
                )
            )
    aggregateEdges = []
    for (level, fromRef, toRef, relationType, epistemic, verification), members in sorted(
        aggregate.items(),
        key=lambda item: (
            item[0][0],
            item[0][1],
            item[0][2],
            item[0][3],
            item[0][4].value,
            item[0][5].value,
        ),
    ):
        relationIds = tuple(sorted(item.relationId for item in members))
        relationSetDigest = spatialPackedDigest("RELATION_REF_SET", relationIds)
        edgeId = logicalId("scene-edge", (level, fromRef, relationType, toRef, relationSetDigest))
        aggregateEdges.append(
            SceneEdge(
                edgeId=edgeId,
                relationType=relationType,
                fromNodeId=fromRef,
                toNodeId=toRef,
                weight=sum(item.weight if item.weight is not None else 1.0 for item in members),
                epistemicClass=epistemic,
                verificationState=verification,
                evidenceCount=len({evidence for item in members for evidence in item.evidenceRefs}),
                lodLevel=level,
                aggregateCount=len(members),
                styleToken=_styleToken(epistemic, verification),
                detailRef=f"du:relation-set:{relationSetDigest}",
            )
        )
    return (*aggregateEdges, *levelThreeEdges)


def compileSemanticLod(
    catalog: CatalogState,
    objects: tuple[CatalogObject, ...],
    relations: tuple[GraphRelation, ...],
    statements: tuple[GraphStatement, ...],
    communities: tuple[CommunityVersion, ...],
    coordinates: tuple[LogicalCoordinate, ...],
    request: ProjectionRequest,
) -> LodCompilation:
    """Primary-home hierarchy를 scene proxy와 exact conservation report로 변환한다."""
    objectIds = frozenset(item.objectId for item in objects)
    activeRelations = relations
    activeStatements = statements
    resourceByVersion = {item.resourceVersionId: item for item in catalog.resources}
    communityById = {item.communityLogicalId: item for item in communities}
    homeL2 = {item.objectId: item.clusterId for item in coordinates}
    homeL1 = {
        objectId: communityById[clusterId].parentCommunityLogicalId or "" for objectId, clusterId in homeL2.items()
    }
    root = next(item for item in communities if item.level == 0)
    evidenceByObject: dict[str, list[str]] = defaultdict(list)
    evidenceById = {} if activeStatements else None
    for item in catalog.evidence:
        if item.visibility not in request.allowedVisibility:
            continue
        if evidenceById is not None:
            evidenceById[item.evidenceId] = item
        if item.objectId in objectIds:
            evidenceByObject[item.objectId].append(item.evidenceId)
    facts = _proxyFacts(
        communities,
        objects,
        resourceByVersion,
        evidenceByObject,
        activeStatements,
        activeRelations,
        root.communityLogicalId,
        homeL1,
        homeL2,
    )
    meaning = _meaningReport(communities, facts)
    anchors = communityAnchors(communities, request.budget)
    neighborClusters: dict[str, Counter[str]] = defaultdict(Counter)
    for relation in activeRelations:
        fromCluster = homeL2.get(relation.fromRef)
        toCluster = homeL2.get(relation.toRef)
        if fromCluster and toCluster and fromCluster != toCluster:
            neighborClusters[fromCluster][toCluster] += 1
            neighborClusters[toCluster][fromCluster] += 1
    pickIdByCommunity = {target: index for index, target in enumerate(sorted(communityById), 1)}
    objectPickIdOffset = len(pickIdByCommunity) + 1
    proxies = []
    for community in communities:
        proxyFacts = facts[community.communityLogicalId]
        representatives = tuple(
            item
            for item, _importance in nsmallest(
                request.budget.representativeCount,
                community.memberImportance,
                key=lambda item: (-item[1], item[0]),
            )
        )
        secondary = tuple(item for item, _count in neighborClusters[community.communityLogicalId].most_common(4))
        relationHistogram = _relationHistogram(proxyFacts)
        proxyVersionId = spatialId(
            "scene-proxy-version",
            community.communityVersionId,
            community.memberDigest,
            proxyFacts.kindHistogram,
            proxyFacts.sourceHistogram,
            proxyFacts.epistemicHistogram,
            proxyFacts.verificationHistogram,
            proxyFacts.periodRange,
            proxyFacts.statementRefSetDigest,
            proxyFacts.evidenceRefSetDigest,
            relationHistogram,
        )
        proxies.append(
            SceneProxy(
                proxyId=community.communityLogicalId,
                proxyVersionId=proxyVersionId,
                communityLogicalId=community.communityLogicalId,
                communityVersionId=community.communityVersionId,
                memberDigest=community.memberDigest,
                memberCount=community.memberCount,
                representativeObjectIds=representatives,
                representativeRuleVersion="du-representative-importance-v1",
                primaryHomeClusterId=community.communityLogicalId,
                secondaryMemberships=secondary,
                drillTargetTileId="",
                kindHistogram=proxyFacts.kindHistogram,
                sourceHistogram=proxyFacts.sourceHistogram,
                epistemicHistogram=proxyFacts.epistemicHistogram,
                verificationHistogram=proxyFacts.verificationHistogram,
                periodRange=proxyFacts.periodRange,
                statementCount=len(proxyFacts.statementRefs),
                statementRefSetDigest=proxyFacts.statementRefSetDigest,
                evidenceCount=len(proxyFacts.evidenceRefs),
                evidenceRefSetDigest=proxyFacts.evidenceRefSetDigest,
                relationTypeDirectionHistogram=relationHistogram,
                positionQ=anchors[community.communityLogicalId],
                radiusQ=max(64, round(math.sqrt(community.memberCount) * 8)),
                lodLevel=community.level,
                pickId=pickIdByCommunity[community.communityLogicalId],
                styleToken=f"community:l{community.level}",
                detailRef=community.communityVersionId,
            )
        )
    del facts, proxyFacts
    nodes = []
    drillPaths = []
    for index, (obj, coordinate, importancePair) in enumerate(
        zip(objects, coordinates, root.memberImportance, strict=True)
    ):
        if importancePair[0] != obj.objectId or coordinate.objectId != obj.objectId:
            raise ValueError("scene node 입력 순서가 object ID와 일치하지 않음")
        importance = importancePair[1]
        nodes.append(
            SceneNode(
                nodeId=obj.objectId,
                targetKind="OBJECT",
                targetId=obj.objectId,
                positionQ=coordinate.positionQ,
                radiusQ=coordinate.radiusQ,
                importance=importance,
                kind=obj.objectKind,
                epistemicClass=obj.epistemicClass,
                verificationState=obj.verificationState,
                clusterId=coordinate.clusterId,
                lodLevel=3,
                labelPriority=importance,
                pickId=objectPickIdOffset + index,
                styleToken=_styleToken(obj.epistemicClass, obj.verificationState),
                detailRef=obj.objectId,
            )
        )
        clusterId = coordinate.clusterId
        familyId = homeL1[obj.objectId]
        resourceRef = obj.resourceRefs[0]
        objectEvidence = evidenceByObject[obj.objectId]
        evidenceRefs = tuple(objectEvidence) if len(objectEvidence) < 2 else tuple(sorted(objectEvidence))
        lazyRef = (
            f"runtime-row:{resourceRef}"
            if obj.objectKind == "TABLE"
            else evidenceRefs[0]
            if evidenceRefs
            else resourceRef
        )
        levels = (
            ("L0", root.communityLogicalId),
            ("L1", familyId),
            ("L2", clusterId),
            ("L3", obj.objectId),
            ("L4", resourceRef),
            ("L5", lazyRef),
        )
        drillPaths.append(_drillPath("OBJECT", obj.objectId, levels, resourceRef, evidenceRefs))
    for statement in sorted(activeStatements, key=lambda item: item.statementId):
        anchorObjectId = statement.subjectRef if statement.subjectRef in objectIds else statement.objectRef
        if anchorObjectId is None or anchorObjectId not in homeL2:
            continue
        evidenceRefs = tuple(sorted(statement.evidenceRefs))
        leafRef = (
            evidenceRefs[0]
            if evidenceRefs
            else statement.derivationRef
            or next(iter(statement.assumptionRefs), spatialId("statement-detail", statement.statementId))
        )
        resourceRef = (
            evidenceById[evidenceRefs[0]].resourceVersionId
            if evidenceRefs and evidenceById is not None
            else statement.statementId
        )
        levels = (
            ("L0", root.communityLogicalId),
            ("L1", homeL1[anchorObjectId]),
            ("L2", homeL2[anchorObjectId]),
            ("L3", anchorObjectId),
            ("L4", statement.statementId),
            ("L5", leafRef),
        )
        drillPaths.append(_drillPath("STATEMENT", statement.statementId, levels, statement.statementId, evidenceRefs))
    edges = _compileEdges(activeRelations, homeL1, homeL2)
    base = LodCompilation(tuple(proxies), tuple(nodes), edges, tuple(drillPaths), meaning, "")
    digest = spatialPackedDigest(
        "SEMANTIC_LOD",
        tuple(item.proxyVersionId for item in base.proxies),
        tuple(
            (
                item.nodeId,
                item.positionQ,
                item.radiusQ,
                item.importance,
                item.styleToken,
                item.detailRef,
            )
            for item in base.nodes
        ),
        tuple((item.edgeId, item.aggregateCount, item.weight) for item in base.edges),
        tuple(item.digest for item in base.drillPaths),
        meaning.digest,
    )
    return replace(base, digest=digest)
