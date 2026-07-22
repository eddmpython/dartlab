"""U5 scene tile을 GPU 친화적인 runtime-only binary bundle로 변환한다."""

from __future__ import annotations

import hashlib
import json
import math
import struct
from dataclasses import asdict
from enum import Enum

from .spatial.contracts import SceneNode, SceneProxy, SceneTile, SpatialProjection
from .spatial.tiles import validateSceneTileGraph

GPU_TILE_MAGIC = b"DUGPU1\0\0"
GPU_TILE_SCHEMA_VERSION = "du-gpu-tile-v1"
GPU_MANIFEST_SCHEMA_VERSION = "du-gpu-manifest-v1"
NODE_RECORD = struct.Struct("<4fIHHf")
EDGE_RECORD = struct.Struct("<7fHH")

_FAMILY_LABELS = {
    "ENTITY": "법인과 인물",
    "DATA": "공시와 재무 데이터",
    "KNOWLEDGE": "블로그와 지식",
    "MEDIA": "이미지와 영상",
    "CAPABILITY": "분석 엔진",
    "OTHER": "기타 근거",
}

_NAMESPACE_LABELS = {
    "media catalog record": "미디어 카탈로그",
    "objects": "미디어 객체",
    "dart": "DART 공시",
    "edgar": "EDGAR 공시",
}


def _jsonValue(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonValue(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonValue(item) for item in value]
    return value


def _compactJson(value) -> bytes:
    return json.dumps(
        _jsonValue(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _familyKey(semanticKey: str) -> str:
    parts = semanticKey.split(":")
    candidate = parts[1] if len(parts) > 1 and parts[0] in {"L0", "L1", "L2"} else parts[0]
    return candidate.split("|", 1)[0].strip().upper() or "OTHER"


class UniverseGpuTransport:
    """검증된 한 SpatialProjection을 browser renderer용 immutable binary tile로 노출한다."""

    def __init__(self, projection: SpatialProjection, *, objectLabels: dict[str, str]):
        failures = validateSceneTileGraph(projection.manifest, projection.tiles)
        if failures:
            raise ValueError(f"U6 transport가 손상된 U5 tile을 거부함: {failures}")
        if not projection.meaningReport.passed:
            raise ValueError("U6 transport는 의미 보존 실패 projection을 거부함")
        self.projection = projection
        self.objectLabels = objectLabels
        self.tileById = {item.envelope.tileId: item for item in projection.tiles}
        self.communityById = {item.communityLogicalId: item for item in projection.state.communities}
        self.familyByCommunity = self._familyMap()
        familyKeys = tuple(sorted(set(self.familyByCommunity.values())))
        self.styleKeys = familyKeys or ("OTHER",)
        self.styleIndex = {item: index for index, item in enumerate(self.styleKeys)}
        self.pointByRef = self._pointIndex()

    def _familyMap(self) -> dict[str, str]:
        familyByCommunity = {}
        for community in self.projection.state.communities:
            if community.level == 0:
                familyByCommunity[community.communityLogicalId] = "OTHER"
            elif community.level == 1:
                familyByCommunity[community.communityLogicalId] = _familyKey(community.semanticKey)
        for community in self.projection.state.communities:
            if community.level == 2:
                parent = community.parentCommunityLogicalId or ""
                familyByCommunity[community.communityLogicalId] = familyByCommunity.get(parent, "OTHER")
        return familyByCommunity

    def _pointIndex(self) -> dict[str, tuple[tuple[int, int, int], str]]:
        points = {}
        for tile in self.projection.tiles:
            for proxy in tile.proxies:
                value = (proxy.positionQ, self.familyByCommunity.get(proxy.communityLogicalId, "OTHER"))
                points[proxy.proxyId] = value
                points[proxy.communityLogicalId] = value
            for node in tile.nodes:
                value = (node.positionQ, self.familyByCommunity.get(node.clusterId, "OTHER"))
                points[node.nodeId] = value
                points[node.targetId] = value
        return points

    def _proxyLabel(self, proxy: SceneProxy) -> str:
        community = self.communityById[proxy.communityLogicalId]
        family = self.familyByCommunity.get(proxy.communityLogicalId, "OTHER")
        if community.level == 0:
            return "DartLab 전체 지식 우주"
        if community.level == 1:
            return _FAMILY_LABELS.get(family, community.semanticKey)
        representative = next(
            (self.objectLabels[item] for item in proxy.representativeObjectIds if item in self.objectLabels),
            "",
        )
        if (
            family in {"DATA", "MEDIA"}
            or len(representative) > 72
            or "/" in representative
            or "/sha256/" in representative
            or representative.startswith("du:v1:")
            or representative.casefold() in {"objects", "media_catalog_record"}
        ):
            representative = ""
        if not representative:
            parts = community.semanticKey.split(":")
            kindLabels = {
                "blog_post": "블로그",
                "capability": "분석",
                "collection": "컬렉션",
                "dataset": "데이터셋",
                "document": "문서",
                "organization": "법인",
                "table": "테이블",
            }
            namespace = " · ".join(item.replace("-", " ").replace("_", " ") for item in parts[3:-1] if item)
            representative = (
                _NAMESPACE_LABELS.get(namespace.casefold(), namespace)
                if namespace
                else kindLabels.get(parts[2] if len(parts) > 2 else "", family)
            )
        suffix = f" 외 {proxy.memberCount - 1:,}개" if proxy.memberCount > 1 else ""
        return representative + suffix

    def _nodeMetadata(self, item: SceneProxy | SceneNode) -> dict[str, object]:
        if isinstance(item, SceneProxy):
            community = self.communityById[item.communityLogicalId]
            family = self.familyByCommunity.get(item.communityLogicalId, "OTHER")
            return {
                "pickId": item.pickId,
                "targetKind": "COMMUNITY",
                "targetId": item.communityLogicalId,
                "label": self._proxyLabel(item),
                "family": family,
                "lodLevel": item.lodLevel,
                "memberCount": item.memberCount,
                "evidenceCount": item.evidenceCount,
                "statementCount": item.statementCount,
                "drillTargetTileId": item.drillTargetTileId,
                "detailRef": item.detailRef,
                "semanticKey": community.semanticKey,
            }
        family = self.familyByCommunity.get(item.clusterId, "OTHER")
        return {
            "pickId": item.pickId,
            "targetKind": item.targetKind,
            "targetId": item.targetId,
            "label": self.objectLabels.get(item.targetId, item.targetId),
            "family": family,
            "lodLevel": item.lodLevel,
            "memberCount": 1,
            "evidenceCount": 0,
            "statementCount": 0,
            "drillTargetTileId": "",
            "detailRef": item.detailRef,
            "semanticKey": item.kind,
        }

    def _nodeRecord(self, item: SceneProxy | SceneNode, halfExtent: float) -> bytes:
        family = (
            self.familyByCommunity.get(item.communityLogicalId, "OTHER")
            if isinstance(item, SceneProxy)
            else self.familyByCommunity.get(item.clusterId, "OTHER")
        )
        memberCount = item.memberCount if isinstance(item, SceneProxy) else 1
        importance = math.log2(memberCount + 1) if isinstance(item, SceneProxy) else math.log2(item.importance + 2)
        displaySize = min(42.0, max(4.0, 4.0 + importance * (1.75 if isinstance(item, SceneProxy) else 1.05)))
        flags = 1 if isinstance(item, SceneProxy) else 0
        return NODE_RECORD.pack(
            item.positionQ[0] / halfExtent,
            item.positionQ[1] / halfExtent,
            item.positionQ[2] / halfExtent,
            displaySize,
            item.pickId,
            self.styleIndex.get(family, 0),
            flags,
            float(importance),
        )

    def encodeTile(self, tileId: str) -> bytes:
        tile = self.tileById.get(tileId)
        if tile is None:
            raise KeyError(tileId)
        halfExtent = float(
            max(abs(value) for value in asdict(self.projection.manifest.bounds).values() for value in value)
        )
        orderedPoints: tuple[SceneProxy | SceneNode, ...] = (*tile.proxies, *tile.nodes)
        nodeBytes = b"".join(self._nodeRecord(item, halfExtent) for item in orderedPoints)
        edgePayload = bytearray()
        for edge in tile.edges:
            fromPoint = self.pointByRef.get(edge.fromNodeId)
            toPoint = self.pointByRef.get(edge.toNodeId)
            if fromPoint is None or toPoint is None:
                raise ValueError(f"U6 edge endpoint 누락: {edge.edgeId}")
            fromPosition, family = fromPoint
            toPosition, _toFamily = toPoint
            edgePayload.extend(
                EDGE_RECORD.pack(
                    fromPosition[0] / halfExtent,
                    fromPosition[1] / halfExtent,
                    fromPosition[2] / halfExtent,
                    toPosition[0] / halfExtent,
                    toPosition[1] / halfExtent,
                    toPosition[2] / halfExtent,
                    float(math.log2(edge.aggregateCount + 1)),
                    self.styleIndex.get(family, 0),
                    0,
                )
            )
        recordPayload = nodeBytes + bytes(edgePayload)
        header = {
            "schemaVersion": GPU_TILE_SCHEMA_VERSION,
            "sceneId": tile.envelope.sceneId,
            "snapshotId": tile.envelope.snapshotId,
            "projectionDigest": tile.envelope.projectionDigest,
            "visibilityScopeDigest": tile.envelope.visibilityScopeDigest,
            "generation": tile.envelope.generation,
            "tileId": tile.envelope.tileId,
            "parentTileId": tile.envelope.parentTileId,
            "childTileIds": tile.envelope.childTileIds,
            "lodLevel": tile.envelope.lodLevel,
            "screenSpaceError": tile.envelope.screenSpaceError,
            "bounds3d": asdict(tile.envelope.bounds3d),
            "nodeCount": len(orderedPoints),
            "edgeCount": len(tile.edges),
            "nodeStride": NODE_RECORD.size,
            "edgeStride": EDGE_RECORD.size,
            "nodeBytes": len(nodeBytes),
            "edgeBytes": len(edgePayload),
            "sourceContentDigest": tile.envelope.contentDigest,
            "recordDigest": hashlib.sha256(recordPayload).hexdigest(),
            "styleKeys": self.styleKeys,
            "nodeMetadata": tuple(self._nodeMetadata(item) for item in orderedPoints),
        }
        headerBytes = _compactJson(header)
        return GPU_TILE_MAGIC + struct.pack("<I", len(headerBytes)) + headerBytes + recordPayload

    def manifestPayload(self) -> bytes:
        manifest = self.projection.manifest
        payload = {
            "schemaVersion": GPU_MANIFEST_SCHEMA_VERSION,
            "scene": asdict(manifest),
            "meaningReportDigest": self.projection.meaningReport.digest,
            "meaningPreservation": self.projection.meaningReport.meaningPreservation,
            "rootTileId": manifest.rootTileId,
            "styleKeys": self.styleKeys,
            "transport": {
                "tileSchemaVersion": GPU_TILE_SCHEMA_VERSION,
                "nodeStride": NODE_RECORD.size,
                "edgeStride": EDGE_RECORD.size,
                "persistenceMode": "EPHEMERAL",
            },
        }
        return _compactJson(payload)
