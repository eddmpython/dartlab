"""현재 공개 ecosystem 그래프의 사실 적격성을 측정한다.

Capabilities
    기존 HF ``landing/map/ecosystem.json`` 또는 같은 스키마의 로컬 fixture를
    읽어 source 분포, self-loop, 허브, 중복, exact evidence와 시간 coverage를
    계산한다.

Args
    CLI의 ``source``는 HTTP(S) URL 또는 JSON 파일 경로다. ``incident-label``은
    짧은 이름 오탐 사례를 재현할 node label이다.

Returns
    :class:`GraphTruthReport`를 JSON으로 출력한다.

Example
    ``uv run python -X utf8 tests/_attempts/dartlabUniverse/truth/graphTruthProbe.py``

Guide
    ``observedEligibleEdges``가 전체 edge와 같지 않으면 현재 artifact를 사실
    그래프로 승격하지 않는다. 부족한 edge는 candidate hint로만 취급한다.

SeeAlso
    ``mainPlan/dartlab-universe/08-attempts-evidence-matrix.md``

Requires
    Python 표준 라이브러리만 사용한다. 새 데이터 bake나 로컬 사본을 만들지
    않는다.

AIContext
    이 probe는 관계 추출기가 아니다. 공개 artifact의 현재 품질 경계를
    반복 측정하는 U0 증거다.

LLM Specifications
    AntiPatterns: 결과를 근거로 모든 edge를 폐기하거나 자동 fact 승격하지 않는다.
    OutputSchema: GraphTruthReport의 JSON 직렬화 형태다.
    Prerequisites: ecosystem schema에 nodes와 links가 있어야 한다.
    Freshness: 실행 시점의 원격 artifact 또는 명시한 fixture 기준이다.
    Dataflow: source -> JSON -> deterministic census -> stdout JSON.
    TargetMarkets: KR current map, 이후 동일 schema의 다른 시장 fixture.

결과
    2026-07-15 HF current 실행에서 node 2,664, edge 20,560, self-loop 13,
    exact sourceRef와 availableAt을 모두 가진 observed 적격 edge 0을 확인했다.
    ``OCI`` incident edge는 4,474건이었다. 따라서 기존 edge는 U0에서
    candidate hint로만 입장시킨다는 설계를 유지한다.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.request import urlopen

DEFAULT_SOURCE = "https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/landing/map/ecosystem.json"
EXACT_EVIDENCE_FIELDS = ("sourceRef", "rceptNo")
EXACT_TIME_FIELDS = ("availableAt",)


@dataclass(frozen=True)
class GraphTruthReport:
    """공개 graph artifact의 fact admission 가능성을 요약한다.

    Args
        sourceVersion: ecosystem payload가 선언한 version.
        nodeCount: 전체 node 수.
        edgeCount: 전체 edge 수.
        linkedNodeCount: 하나 이상의 edge에 연결된 node 수.
        isolatedNodeCount: edge에 연결되지 않은 node 수.
        selfLoopCount: source와 target이 같은 edge 수.
        duplicatePresentationEdgeCount: source, target, type이 같은 중복 edge 수.
        exactSourceRefEdgeCount: exact 문서 식별자를 가진 edge 수.
        exactAvailableAtEdgeCount: 공개 가능 시점을 가진 edge 수.
        observedEligibleEdgeCount: sourceRef, availableAt, non-self-loop을 만족한 수.
        sourceCounts: source별 edge 수.
        maxDegree: 최대 unique neighbor degree.
        maxDegreeNodeId: 최대 degree node ID.
        maxDegreeNodeLabel: 최대 degree node label.
        incidentLabel: 별도 회귀핀으로 추적한 label.
        incidentNodeId: 해당 label의 node ID.
        incidentEdgeCount: 해당 node가 관여한 edge 수.

    Returns
        JSON 직렬화 가능한 immutable report.

    Example
        ``GraphTruthReport(...).toDict()``

    Raises
        생성 자체는 예외를 발생시키지 않는다.
    """

    sourceVersion: str
    nodeCount: int
    edgeCount: int
    linkedNodeCount: int
    isolatedNodeCount: int
    selfLoopCount: int
    duplicatePresentationEdgeCount: int
    exactSourceRefEdgeCount: int
    exactAvailableAtEdgeCount: int
    observedEligibleEdgeCount: int
    sourceCounts: dict[str, int]
    maxDegree: int
    maxDegreeNodeId: str | None
    maxDegreeNodeLabel: str | None
    incidentLabel: str
    incidentNodeId: str | None
    incidentEdgeCount: int

    def toDict(self) -> dict[str, Any]:
        """Report를 JSON 직렬화 가능한 dict로 바꾼다.

        Args
            없음.

        Returns
            필드 선언 순서를 보존한 dict.

        Example
            ``json.dumps(report.toDict())``

        Raises
            직렬화 가능 필드만 사용하므로 예외를 발생시키지 않는다.
        """

        return asdict(self)


def loadGraphPayload(source: str) -> dict[str, Any]:
    """HTTP URL 또는 로컬 파일에서 ecosystem payload를 읽는다.

    Args
        source: HTTP(S) URL 또는 JSON 파일 경로.

    Returns
        ``nodes``와 ``links``를 가진 dict.

    Example
        ``payload = loadGraphPayload(DEFAULT_SOURCE)``

    Raises
        ValueError: payload가 object가 아니거나 nodes와 links가 list가 아닐 때.
        OSError: 로컬 파일을 읽을 수 없을 때.
    """

    if source.startswith(("https://", "http://")):
        with urlopen(source, timeout=60) as response:
            payload = json.load(response)
    else:
        payload = json.loads(Path(source).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("ecosystem payload must be a JSON object")
    if not isinstance(payload.get("nodes"), list) or not isinstance(payload.get("links"), list):
        raise ValueError("ecosystem payload must contain nodes and links lists")
    return payload


def _hasAny(edge: dict[str, Any], fields: tuple[str, ...]) -> bool:
    return any(edge.get(field) not in (None, "", []) for field in fields)


def inspectGraphTruth(payload: dict[str, Any], *, incidentLabel: str = "OCI") -> GraphTruthReport:
    """현재 edge가 source-backed observed fact로 입장 가능한지 측정한다.

    Args
        payload: ecosystem ``nodes``와 ``links`` payload.
        incidentLabel: 짧은 이름 오탐 회귀핀으로 측정할 node label.

    Returns
        deterministic :class:`GraphTruthReport`.

    Example
        ``report = inspectGraphTruth(payload, incidentLabel="OCI")``

    Raises
        ValueError: node ID 또는 edge source/target/type이 없을 때.
    """

    nodes = payload["nodes"]
    edges = payload["links"]
    nodeLabels: dict[str, str] = {}
    for node in nodes:
        nodeId = str(node.get("id", ""))
        if not nodeId:
            raise ValueError("every node must have an id")
        nodeLabels[nodeId] = str(node.get("label", nodeId))

    incidentEdges: Counter[str] = Counter()
    neighbors: defaultdict[str, set[str]] = defaultdict(set)
    sourceCounts: Counter[str] = Counter()
    presentationKeys: Counter[tuple[str, str, str]] = Counter()
    selfLoopCount = 0
    exactSourceRefEdgeCount = 0
    exactAvailableAtEdgeCount = 0
    observedEligibleEdgeCount = 0
    for edge in edges:
        sourceId = str(edge.get("source", ""))
        targetId = str(edge.get("target", ""))
        edgeType = str(edge.get("type", ""))
        if not sourceId or not targetId or not edgeType:
            raise ValueError("every edge must have source, target, and type")
        incidentEdges[sourceId] += 1
        if targetId != sourceId:
            incidentEdges[targetId] += 1
        neighbors[sourceId].add(targetId)
        neighbors[targetId].add(sourceId)
        sourceCounts[str(edge.get("source_tag", "unknown"))] += 1
        presentationKeys[(sourceId, targetId, edgeType)] += 1
        isSelfLoop = sourceId == targetId
        hasSourceRef = _hasAny(edge, EXACT_EVIDENCE_FIELDS)
        hasAvailableAt = _hasAny(edge, EXACT_TIME_FIELDS)
        selfLoopCount += int(isSelfLoop)
        exactSourceRefEdgeCount += int(hasSourceRef)
        exactAvailableAtEdgeCount += int(hasAvailableAt)
        observedEligibleEdgeCount += int(hasSourceRef and hasAvailableAt and not isSelfLoop)

    incidentNodeId = next(
        (nodeId for nodeId, label in nodeLabels.items() if label.casefold() == incidentLabel.casefold()),
        None,
    )
    maxDegreeNodeId = max(neighbors, key=lambda nodeId: (len(neighbors[nodeId]), nodeId), default=None)
    duplicatePresentationEdgeCount = sum(count - 1 for count in presentationKeys.values() if count > 1)
    linkedNodeCount = sum(1 for nodeId in nodeLabels if incidentEdges[nodeId] > 0)
    return GraphTruthReport(
        sourceVersion=str(payload.get("version", "unknown")),
        nodeCount=len(nodes),
        edgeCount=len(edges),
        linkedNodeCount=linkedNodeCount,
        isolatedNodeCount=len(nodes) - linkedNodeCount,
        selfLoopCount=selfLoopCount,
        duplicatePresentationEdgeCount=duplicatePresentationEdgeCount,
        exactSourceRefEdgeCount=exactSourceRefEdgeCount,
        exactAvailableAtEdgeCount=exactAvailableAtEdgeCount,
        observedEligibleEdgeCount=observedEligibleEdgeCount,
        sourceCounts=dict(sorted(sourceCounts.items())),
        maxDegree=len(neighbors[maxDegreeNodeId]) if maxDegreeNodeId is not None else 0,
        maxDegreeNodeId=maxDegreeNodeId,
        maxDegreeNodeLabel=nodeLabels.get(maxDegreeNodeId) if maxDegreeNodeId is not None else None,
        incidentLabel=incidentLabel,
        incidentNodeId=incidentNodeId,
        incidentEdgeCount=incidentEdges[incidentNodeId] if incidentNodeId is not None else 0,
    )


def main() -> int:
    """CLI source를 읽고 truth report를 stdout JSON으로 출력한다.

    Args
        없음. argparse가 CLI 인자를 읽는다.

    Returns
        성공 시 0.

    Example
        ``python graphTruthProbe.py --incident-label OCI``

    Raises
        source load와 schema validation 예외를 숨기지 않는다.
    """

    parser = argparse.ArgumentParser(description="Inspect current ecosystem graph truth eligibility")
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--incident-label", dest="incidentLabel", default="OCI")
    args = parser.parse_args()
    report = inspectGraphTruth(loadGraphPayload(args.source), incidentLabel=args.incidentLabel)
    print(json.dumps(report.toDict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
