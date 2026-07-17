import type {
	UniverseKnowledgeEdge,
	UniverseKnowledgeFilmBeat,
	UniverseKnowledgeNode,
	UniverseLane
} from '@dartlab/ui-contracts';

const LANE_ORDER: Readonly<Record<UniverseLane, number>> = Object.freeze({ fact: 0, derived: 1, candidate: 2, scenario: 3 });

function visibleNodeIds(nodes: readonly UniverseKnowledgeNode[], visited: ReadonlySet<string>): readonly string[] {
	return Object.freeze(nodes.filter((node) => visited.has(node.nodeId)).map((node) => node.nodeId));
}

function visibleEdgeIds(edges: readonly UniverseKnowledgeEdge[], visited: ReadonlySet<string>): readonly string[] {
	return Object.freeze(edges.filter((edge) => visited.has(edge.edgeId)).map((edge) => edge.edgeId));
}

export function compileKnowledgeFilm(
	nodes: readonly UniverseKnowledgeNode[],
	edges: readonly UniverseKnowledgeEdge[],
	maxBeats = 8
): readonly UniverseKnowledgeFilmBeat[] {
	const center = nodes[0];
	if (!center) return Object.freeze([]);
	const safeBeatLimit = Math.max(3, Math.min(12, maxBeats));
	const nodeById = new Map(nodes.map((node) => [node.nodeId, node]));
	const visitedNodes = new Set<string>([center.nodeId]);
	const visitedEdges = new Set<string>();
	const beats: UniverseKnowledgeFilmBeat[] = [Object.freeze({
		beatId: `beat:establish:${center.nodeId}`,
		mode: 'establish',
		label: '출발점',
		narration: `${center.label}에서 지식 경로를 시작합니다.`,
		targetNodeId: center.nodeId,
		focusEdgeId: null,
		lane: center.lane,
		revealNodeIds: Object.freeze([center.nodeId]),
		revealEdgeIds: Object.freeze([]),
		cameraScale: 1.45,
		durationMs: 1800
	})];

	while (beats.length < safeBeatLimit - 1) {
		const candidates = edges.filter((edge) => {
			if (visitedEdges.has(edge.edgeId)) return false;
			const sourceVisited = visitedNodes.has(edge.sourceId);
			const targetVisited = visitedNodes.has(edge.targetId);
			return sourceVisited !== targetVisited;
		}).sort((left, right) =>
			LANE_ORDER[left.lane] - LANE_ORDER[right.lane]
			|| left.relation.localeCompare(right.relation)
			|| left.edgeId.localeCompare(right.edgeId)
		);
		const edge = candidates[0];
		if (!edge) break;
		const sourceWasVisited = visitedNodes.has(edge.sourceId);
		visitedEdges.add(edge.edgeId);
		visitedNodes.add(edge.sourceId);
		visitedNodes.add(edge.targetId);
		const source = nodeById.get(edge.sourceId);
		const target = nodeById.get(edge.targetId);
		if (!source || !target) continue;
		const focusNode = sourceWasVisited ? target : source;
		const mode = edge.lane === 'fact' && edge.relation !== 'supported' ? 'trace' as const : 'evidence' as const;
		beats.push(Object.freeze({
			beatId: `beat:${mode}:${edge.edgeId}`,
			mode,
			label: `${edge.relation} · ${focusNode.label}`,
			narration: `${source.label}에서 ${edge.relation} 관계를 따라 ${target.label}로 이동합니다. ${edge.lane.toLocaleUpperCase()} 근거 레인입니다.`,
			targetNodeId: focusNode.nodeId,
			focusEdgeId: edge.edgeId,
			lane: edge.lane,
			revealNodeIds: visibleNodeIds(nodes, visitedNodes),
			revealEdgeIds: visibleEdgeIds(edges, visitedEdges),
			cameraScale: edge.lane === 'fact' ? 1.62 : 1.88,
			durationMs: edge.lane === 'fact' ? 1850 : 2200
		}));
		if (visitedNodes.size === nodes.length && visitedEdges.size === edges.length) break;
	}

	if (nodes.length > 1 && beats.length < safeBeatLimit) {
		beats.push(Object.freeze({
			beatId: `beat:resolve:${center.nodeId}`,
			mode: 'resolve',
			label: '전체 결속',
			narration: `${nodes.length.toLocaleString()}개 지식 개체와 ${edges.length.toLocaleString()}개 관계를 하나의 근거 장면으로 결속했습니다.`,
			targetNodeId: center.nodeId,
			focusEdgeId: null,
			lane: null,
			revealNodeIds: Object.freeze(nodes.map((node) => node.nodeId)),
			revealEdgeIds: Object.freeze(edges.map((edge) => edge.edgeId)),
			cameraScale: 1,
			durationMs: 2400
		}));
	}
	return Object.freeze(beats);
}
