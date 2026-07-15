"""Universe live bounded scene을 visual layout 입력으로 투영한다.

Capabilities
    U0-P01 atlas, industry, company bounded scene을 U0-V02 logical layout fixture로 재사용한다.

AIContext
    AI 역할: 현재 artifact에 없는 valid time을 임의 순서로 채우지 않고 unknown으로 보존한다.

Guide
    새 graph 사본을 만들지 않고 실행 시점 public map artifact를 bounded projection으로 읽는다.

When
    Universe layout 결정론을 실제 atlas, industry, company 장면으로 다시 측정할 때 사용한다.

How
    기존 projection adapter와 compiler를 호출하고 stream만 semantic stage로 변환한다.

Requires
    Public map artifact 네트워크 접근과 U0-P01 bounded projection module이 필요하다.

Raises
    OSError: Public artifact를 읽지 못했을 때 발생한다.
    ValueError: Artifact 또는 bounded projection 계약이 깨졌을 때 발생한다.

Example
    ``uv run python -X utf8 -m tests._attempts.dartlabUniverse.visual.liveLayoutFixture``

See Also
    tests/_attempts/dartlabUniverse/projection/boundedProjection.py

결과
    Atlas 18개, industry 26개, company 50개 bounded node와 scene hash를 JSON으로 출력한다.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from tests._attempts.dartlabUniverse.projection import (
    ProjectionSpec,
    adaptAtlas,
    adaptCompany,
    adaptIndustry,
    canonicalPayloadHash,
    compileBoundedProjection,
    loadMapArtifact,
)

VALID_STAGES = frozenset({"upstream", "midstream", "downstream"})


def semanticStage(value: Any) -> str:
    """Artifact stream을 layout stage로 제한한다.

    Capabilities
        upstream, midstream, downstream 외 값을 unknown으로 정규화한다.
    AIContext
        AI 역할: 결손 stream을 의미가 있는 stage로 추정하지 않는다.
    Args
        value: Artifact의 원시 stream 값.
    Returns
        허용된 stage 또는 unknown.
    Guide
        새 stage를 추가할 때 VALID_STAGES 계약을 먼저 수정한다.
    When
        Live node를 semantic x anchor로 변환할 때 호출한다.
    How
        문자열 변환 뒤 allowlist membership만 검사한다.
    Requires
        VALID_STAGES 상수가 필요하다.
    Raises
        예외를 발생시키지 않는다.
    Example
        ``semanticStage("upstream") == "upstream"``
    See Also
        :func:`stageLookups`.
    """

    stage = str(value or "")
    return stage if stage in VALID_STAGES else "unknown"


def stageLookups(
    atlas: dict[str, Any],
    industry: dict[str, Any],
    company: dict[str, Any],
) -> tuple[dict[str, str], dict[str, str]]:
    """Industry와 company node별 semantic stage lookup을 만든다.

    Capabilities
        Industry stream과 atlas taxonomy를 node identity에 결속한다.
    AIContext
        AI 역할: explicit stream 또는 exact taxonomy key가 없으면 unknown을 유지한다.
    Args
        atlas: Current atlas artifact.
        industry: Current industry detail artifact.
        company: Current company egograph artifact.
    Returns
        Industry 및 company node stage lookup 두 개.
    Guide
        이름 유사도나 배열 위치로 stage를 추정하지 않는다.
    When
        Live bounded scene fixture를 만들기 전에 호출한다.
    How
        Stock code와 industry 및 stage exact key를 사용한다.
    Requires
        Atlas taxonomy와 source node identity가 필요하다.
    Raises
        KeyError: Industry node에 stockCode가 없을 때 발생한다.
    Example
        ``industryStages, companyStages = stageLookups(atlas, industry, company)``
    See Also
        :func:`semanticStage`.
    """

    industryStages: dict[str, str] = {}
    for stage in industry.get("stages") or []:
        for node in stage.get("nodes") or []:
            industryStages[str(node["stockCode"])] = semanticStage(node.get("stream"))
    for node in industry.get("unclassified") or []:
        industryStages[str(node["stockCode"])] = "unknown"

    taxonomyStreams: dict[tuple[str, str], str] = {}
    for item in atlas.get("industries") or []:
        industryId = str(item.get("id") or "")
        for stage in item.get("stages") or []:
            taxonomyStreams[(industryId, str(stage.get("key") or ""))] = semanticStage(stage.get("stream"))
    companyStages: dict[str, str] = {}
    companyRows = [company.get("ego") or {}, *(company.get("neighbors") or [])]
    for node in companyRows:
        nodeId = str(node.get("stockCode") or "")
        explicit = semanticStage(node.get("stream"))
        if explicit != "unknown":
            companyStages[nodeId] = explicit
            continue
        companyStages[nodeId] = taxonomyStreams.get(
            (str(node.get("industry") or ""), str(node.get("stage") or "")),
            "unknown",
        )
    return industryStages, companyStages


def loadLiveLayoutFixtures() -> list[dict[str, Any]]:
    """Current public map 3종을 bounded semantic layout fixture로 반환한다.

    Capabilities
        Atlas, semiconductor industry, Samsung egograph의 hard bound와 scene hash를 보존한다.

    AIContext
        AI 역할: current artifact의 candidate lane과 valid time 결손을 사실로 승격하지 않는다.

    Args
        없음.

    Returns
        sceneName, sourceSceneHash, bounded node와 receipt를 가진 fixture list.

    Example
        ``fixtures = loadLiveLayoutFixtures()``

    Guide
        Node validOrder는 source time 부재 때문에 None이며 layout unknown time lane으로 간다.

    When
        U0-V02 logical hash, viewport anchor, cross-browser replay를 실행할 때 호출한다.

    How
        U0-P01과 같은 source snapshot 및 projection spec으로 세 scene을 다시 compile한다.

    Requires
        Public map artifact와 boundedProjection module이 필요하다.

    See Also
        :func:`compileBoundedProjection`.

    Raises
        OSError: Remote artifact 요청이 실패했을 때 발생한다.
        ValueError: Artifact schema, seed, bound, lane 계약이 깨졌을 때 발생한다.
    """

    atlas, atlasHash = loadMapArtifact("atlas.json")
    industry, industryHash = loadMapArtifact("industries/semiconductor.json")
    company, companyHash = loadMapArtifact("companies/005930.json")
    snapshotPayload = (
        ("atlas.json", atlasHash),
        ("industries/semiconductor.json", industryHash),
        ("companies/005930.json", companyHash),
    )
    snapshotId = f"sha256:{canonicalPayloadHash(snapshotPayload)}"
    industryStages, companyStages = stageLookups(atlas, industry, company)
    adapted = (
        ("atlas", "semiconductor", *adaptAtlas(atlas), 34, 50, {}),
        ("industry", "005930", *adaptIndustry(industry), 50, 80, industryStages),
        ("company", "005930", *adaptCompany(company), 50, 80, companyStages),
    )
    fixtures: list[dict[str, Any]] = []
    for sceneName, seedId, nodes, edges, maxNodes, maxEdges, stageByNode in adapted:
        spec = ProjectionSpec(
            projectionId=f"live:{sceneName}",
            query=f"current {sceneName} layout projection",
            seedIds=(seedId,),
            sourceSnapshotSetId=snapshotId,
            maxDepth=2,
            maxNodes=maxNodes,
            maxEdges=maxEdges,
        )
        scene = compileBoundedProjection(spec, nodes, edges)
        fixtures.append(
            {
                "schemaVersion": "liveLayoutFixture.v1",
                "sceneName": sceneName,
                "sourceSceneHash": f"sha256:{scene.sceneHash}",
                "sourceSnapshotSetId": snapshotId,
                "inputNodeCount": scene.receipt.inputNodeCount,
                "outputNodeCount": scene.receipt.outputNodeCount,
                "nodes": [
                    {
                        "nodeId": node.nodeId,
                        "label": node.label,
                        "stage": stageByNode.get(node.nodeId, "unknown"),
                        "status": node.lane,
                        "validOrder": None,
                    }
                    for node in scene.nodes
                ],
            }
        )
    return fixtures


def main() -> int:
    """Live layout fixture CLI를 실행한다.

    Capabilities
        Pretty 또는 compact JSON fixture를 stdout으로 출력한다.
    AIContext
        AI 역할: 생성 결과를 저장소 artifact로 자동 저장하지 않는다.
    Args
        없음.
    Returns
        정상 완료 시 0.
    Guide
        Browser audit 전용 전송에는 --compact를 사용한다.
    When
        사람 또는 Node probe가 현재 fixture를 요청할 때 실행한다.
    How
        Argument를 해석하고 loadLiveLayoutFixtures 결과를 직렬화한다.
    Requires
        Public map artifact 접근이 필요하다.
    Raises
        OSError: Artifact load가 실패했을 때 발생한다.
        ValueError: Projection 계약이 깨졌을 때 발생한다.
    Example
        ``python -m tests._attempts.dartlabUniverse.visual.liveLayoutFixture --compact``
    See Also
        :func:`loadLiveLayoutFixtures`.
    """

    parser = argparse.ArgumentParser(description="Build live Universe layout fixtures")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            loadLiveLayoutFixtures(),
            ensure_ascii=False,
            indent=None if args.compact else 2,
            separators=(",", ":") if args.compact else None,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
