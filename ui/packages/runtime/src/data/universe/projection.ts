import {
	UNIVERSE_PREDICATES,
	UNIVERSE_PROJECTION_SCHEMA_VERSION,
	UNIVERSE_SCHEMA_VERSION,
	type OmissionReceipt,
	type ProjectionSpec,
	type SceneReceipt,
	type UniverseAtlas,
	type UniverseLane,
	type UniverseNode,
	type UniverseNodePresentation,
	type UniversePredicate,
	type UniverseRelation,
	type UniverseScene,
	type UniverseStage
} from '@dartlab/ui-contracts';
import { applyKnowledgeCutoff } from './time';
import { canonicalSha256, isSha256Id, stripSha256 } from './canonical';

const LANES: readonly UniverseLane[] = ['fact', 'candidate', 'derived', 'scenario'];
const LANE_RANK: Readonly<Record<UniverseLane, number>> = { fact: 0, candidate: 1, derived: 2, scenario: 3 };
const ASSERTION_ID_PATTERN = /^assertion:[0-9a-f]{64}$/;
const EVIDENCE_ID_PATTERN = /^evidence:[0-9a-f]{64}$/;
const PREDICATES = new Set<string>(UNIVERSE_PREDICATES);

interface QueueEntry {
	baseDepth: number;
	laneRank: number;
	negativePriority: number;
	edgeId: string;
}

function countBy<T extends string>(values: readonly T[]): Array<readonly [T, number]> {
	const counts = new Map<T, number>();
	for (const value of values) counts.set(value, (counts.get(value) ?? 0) + 1);
	return [...counts.entries()].sort(([left], [right]) => left.localeCompare(right));
}

function compareQueue(left: QueueEntry, right: QueueEntry): number {
	return left.baseDepth - right.baseDepth
		|| left.laneRank - right.laneRank
		|| left.negativePriority - right.negativePriority
		|| left.edgeId.localeCompare(right.edgeId);
}

function normalizeSpec(spec: ProjectionSpec): ProjectionSpec {
	const seedIds = [...new Set(spec.seedIds)].sort();
	if (!spec.projectionId || !spec.query || seedIds.length === 0) {
		throw new Error('Universe projection identity, query, and seeds are required');
	}
	if (!isSha256Id(spec.sourceSnapshotSetId)) throw new Error('Universe projection requires a SourceSnapshotSet SHA-256 identity');
	if (!Number.isInteger(spec.maxDepth) || spec.maxDepth < 0 || spec.maxDepth > 6) throw new Error('Universe maxDepth must be between 0 and 6');
	if (!Number.isInteger(spec.maxNodes) || spec.maxNodes < 1 || spec.maxNodes > 500) throw new Error('Universe maxNodes must be between 1 and 500');
	if (!Number.isInteger(spec.maxEdges) || spec.maxEdges < 0 || spec.maxEdges > 2_000) throw new Error('Universe maxEdges must be between 0 and 2000');
	if (seedIds.length > spec.maxNodes) throw new Error('Universe seed count exceeds maxNodes');
	for (const predicate of spec.predicates ?? []) {
		if (!PREDICATES.has(predicate)) throw new Error(`Universe predicate is not admitted: ${predicate}`);
	}
	return { ...spec, seedIds };
}

function validateGraph(
	spec: ProjectionSpec,
	nodes: readonly UniverseNode[],
	edges: readonly UniverseRelation[]
): { nodeIndex: Map<string, UniverseNode>; edgeIndex: Map<string, UniverseRelation> } {
	const nodeIndex = new Map<string, UniverseNode>();
	for (const node of nodes) {
		if (!node.nodeId || !node.label || !LANES.includes(node.lane) || !node.sourceKind || !node.sourceRef) {
			throw new Error('Universe node identity, lane, or source is invalid');
		}
		if (nodeIndex.has(node.nodeId)) throw new Error(`Universe duplicate node: ${node.nodeId}`);
		nodeIndex.set(node.nodeId, node);
	}
	for (const seedId of spec.seedIds) {
		if (!nodeIndex.has(seedId)) throw new Error(`Universe seed is missing: ${seedId}`);
	}
	const edgeIndex = new Map<string, UniverseRelation>();
	for (const edge of edges) {
		if (!edge.edgeId || !PREDICATES.has(edge.predicate) || !edge.sourceRef || !LANES.includes(edge.lane)
			|| !nodeIndex.has(edge.sourceId) || !nodeIndex.has(edge.targetId)) {
			throw new Error('Universe edge identity, predicate, lane, or endpoint is invalid');
		}
		if (edge.sourceId === edge.targetId) throw new Error('Universe projection does not admit self-loop edges');
		if (edgeIndex.has(edge.edgeId)) throw new Error(`Universe duplicate edge: ${edge.edgeId}`);
		if (edge.lane === 'fact') {
			if (!ASSERTION_ID_PATTERN.test(edge.assertionId) || edge.evidenceRefs.length === 0
				|| edge.evidenceRefs.some((ref) => !EVIDENCE_ID_PATTERN.test(ref))) {
				throw new Error('Universe fact edge requires exact assertion and evidence identities');
			}
		} else if (edge.assertionId || edge.evidenceRefs.length > 0) {
			throw new Error('Universe non-fact edge cannot carry fact admission fields');
		}
		if (edge.lane === 'derived' && edge.derivationRefs.length === 0) throw new Error('Universe derived edge requires derivationRefs');
		if (edge.lane === 'scenario' && !edge.scenarioReceiptId) throw new Error('Universe scenario edge requires a scenario receipt');
		edgeIndex.set(edge.edgeId, edge);
	}
	return { nodeIndex, edgeIndex };
}

function specPayload(spec: ProjectionSpec): Record<string, unknown> {
	const payload: Record<string, unknown> = {
		schemaVersion: UNIVERSE_PROJECTION_SCHEMA_VERSION,
		projectionId: spec.projectionId,
		query: spec.query,
		seedIds: spec.seedIds,
		sourceSnapshotSetId: spec.sourceSnapshotSetId,
		maxDepth: spec.maxDepth,
		maxNodes: spec.maxNodes,
		maxEdges: spec.maxEdges
	};
	if (spec.validAt !== undefined) payload.validAt = spec.validAt;
	if (spec.knownAt !== undefined) payload.knownAt = spec.knownAt;
	if (spec.predicates !== undefined) payload.predicates = [...spec.predicates].sort();
	if (spec.statuses !== undefined) payload.statuses = [...spec.statuses].sort();
	return payload;
}

export async function compileProjection(
	inputSpec: ProjectionSpec,
	inputNodes: readonly UniverseNode[],
	inputEdges: readonly UniverseRelation[],
	inputAssertions: UniverseScene['assertions'] = []
): Promise<UniverseScene> {
	const spec = normalizeSpec(inputSpec);
	const assertions = applyKnowledgeCutoff(inputAssertions, spec.validAt ?? null, spec.knownAt ?? null)
		.filter((assertion) => !spec.statuses?.length || spec.statuses.includes(assertion.status));
	const admittedAssertionIds = new Set(assertions.map((assertion) => assertion.assertionId));
	const predicateFilter = new Set(spec.predicates ?? []);
	const filtersFacts = inputAssertions.length > 0 || spec.validAt != null || spec.knownAt != null || Boolean(spec.statuses?.length);
	const nodes = [...inputNodes];
	const edges = inputEdges.filter((edge) => {
		if (predicateFilter.size > 0 && !predicateFilter.has(edge.predicate)) return false;
		return edge.lane !== 'fact' || !filtersFacts || admittedAssertionIds.has(edge.assertionId);
	});
	const { nodeIndex, edgeIndex } = validateGraph(spec, nodes, edges);
	const adjacency = new Map<string, string[]>();
	for (const edge of edges) {
		for (const endpoint of [edge.sourceId, edge.targetId]) {
			const ids = adjacency.get(endpoint) ?? [];
			ids.push(edge.edgeId);
			adjacency.set(endpoint, ids);
		}
	}
	for (const ids of adjacency.values()) ids.sort();

	const selectedNodeIds = new Set(spec.seedIds);
	const selectedEdgeIds = new Set<string>();
	const depthByNode = new Map(spec.seedIds.map((seedId) => [seedId, 0]));
	const queued = new Set<string>();
	const considered = new Set<string>();
	const edgeReasons = new Map<string, string>();
	const nodeReasonHints = new Map<string, Set<string>>();
	const queue: QueueEntry[] = [];
	const enqueue = (nodeId: string): void => {
		const baseDepth = depthByNode.get(nodeId);
		if (baseDepth === undefined) return;
		for (const edgeId of adjacency.get(nodeId) ?? []) {
			if (queued.has(edgeId) || considered.has(edgeId)) continue;
			const edge = edgeIndex.get(edgeId);
			if (!edge) continue;
			queue.push({ baseDepth, laneRank: LANE_RANK[edge.lane], negativePriority: -edge.priority, edgeId });
			queued.add(edgeId);
		}
		queue.sort(compareQueue);
	};
	for (const seedId of spec.seedIds) enqueue(seedId);

	while (queue.length > 0) {
		const item = queue.shift();
		if (!item) break;
		considered.add(item.edgeId);
		const edge = edgeIndex.get(item.edgeId);
		if (!edge) continue;
		const selectedEndpoints = [edge.sourceId, edge.targetId].filter((id) => selectedNodeIds.has(id));
		if (selectedEndpoints.length === 0) {
			edgeReasons.set(edge.edgeId, 'disconnected');
			continue;
		}
		const newEndpoints = [edge.sourceId, edge.targetId].filter((id) => !selectedNodeIds.has(id));
		const selectedDepths = selectedEndpoints.map((id) => depthByNode.get(id) ?? 0);
		const nextDepth = Math.min(...selectedDepths) + Number(newEndpoints.length > 0);
		let reason = '';
		if (nextDepth > spec.maxDepth) reason = 'depthLimit';
		else if (selectedEdgeIds.size >= spec.maxEdges) reason = 'edgeBudget';
		else if (selectedNodeIds.size + new Set(newEndpoints).size > spec.maxNodes) reason = 'nodeBudget';
		if (reason) {
			edgeReasons.set(edge.edgeId, reason);
			for (const endpoint of newEndpoints) {
				const hints = nodeReasonHints.get(endpoint) ?? new Set<string>();
				hints.add(reason);
				nodeReasonHints.set(endpoint, hints);
			}
			continue;
		}
		selectedEdgeIds.add(edge.edgeId);
		for (const endpoint of newEndpoints) {
			selectedNodeIds.add(endpoint);
			depthByNode.set(endpoint, nextDepth);
			enqueue(endpoint);
		}
	}

	for (const edge of edges) {
		if (!selectedEdgeIds.has(edge.edgeId) && !edgeReasons.has(edge.edgeId)) edgeReasons.set(edge.edgeId, 'disconnected');
	}
	const nodeReasons = new Map<string, string>();
	for (const node of nodes) {
		if (selectedNodeIds.has(node.nodeId)) continue;
		const hints = nodeReasonHints.get(node.nodeId) ?? new Set<string>();
		const reason = ['nodeBudget', 'edgeBudget', 'depthLimit'].find((candidate) => hints.has(candidate)) ?? 'disconnected';
		nodeReasons.set(node.nodeId, reason);
	}
	const selectedNodes = [...selectedNodeIds].map((id) => nodeIndex.get(id)).filter((node): node is UniverseNode => Boolean(node))
		.sort((left, right) => (depthByNode.get(left.nodeId) ?? 0) - (depthByNode.get(right.nodeId) ?? 0)
			|| Number(!spec.seedIds.includes(left.nodeId)) - Number(!spec.seedIds.includes(right.nodeId))
			|| LANE_RANK[left.lane] - LANE_RANK[right.lane]
			|| right.priority - left.priority
			|| left.nodeId.localeCompare(right.nodeId));
	const selectedEdges = [...selectedEdgeIds].map((id) => edgeIndex.get(id)).filter((edge): edge is UniverseRelation => Boolean(edge))
		.sort((left, right) => Math.max(depthByNode.get(left.sourceId) ?? 0, depthByNode.get(left.targetId) ?? 0)
			- Math.max(depthByNode.get(right.sourceId) ?? 0, depthByNode.get(right.targetId) ?? 0)
			|| LANE_RANK[left.lane] - LANE_RANK[right.lane]
			|| right.priority - left.priority
			|| left.edgeId.localeCompare(right.edgeId));
	const omittedNodes = nodes.filter((node) => nodeReasons.has(node.nodeId));
	const omittedEdges = edges.filter((edge) => edgeReasons.has(edge.edgeId));
	const omission: OmissionReceipt = {
		omittedNodeCount: omittedNodes.length,
		omittedEdgeCount: omittedEdges.length,
		nodeReasonCounts: countBy([...nodeReasons.values()]),
		edgeReasonCounts: countBy([...edgeReasons.values()]),
		omittedNodeLaneCounts: countBy(omittedNodes.map((node) => node.lane)),
		omittedEdgeLaneCounts: countBy(omittedEdges.map((edge) => edge.lane))
	};
	const specHash = await canonicalSha256(specPayload(spec));
	const receipt: SceneReceipt = {
		specHash,
		sourceSnapshotSetId: spec.sourceSnapshotSetId,
		inputNodeCount: nodes.length,
		inputEdgeCount: edges.length,
		outputNodeCount: selectedNodes.length,
		outputEdgeCount: selectedEdges.length,
		seedCount: spec.seedIds.length,
		retainedSeedCount: spec.seedIds.filter((seedId) => selectedNodeIds.has(seedId)).length,
		maxDepthObserved: Math.max(...depthByNode.values(), 0),
		omission
	};
	const scenePayload: Record<string, unknown> = { schemaVersion: UNIVERSE_SCHEMA_VERSION, nodes: selectedNodes, edges: selectedEdges, receipt };
	if (inputAssertions.length > 0) scenePayload.assertions = assertions;
	const sceneHash = await canonicalSha256(scenePayload);
	if (selectedNodes.length > spec.maxNodes || selectedEdges.length > spec.maxEdges) throw new Error('Universe projection exceeded a hard bound');
	if (receipt.retainedSeedCount !== receipt.seedCount) throw new Error('Universe projection lost a seed');
	if (selectedEdges.some((edge) => !selectedNodeIds.has(edge.sourceId) || !selectedNodeIds.has(edge.targetId))) {
		throw new Error('Universe projection created a dangling edge');
	}
	return { schemaVersion: UNIVERSE_SCHEMA_VERSION, sceneId: `scene:${stripSha256(sceneHash)}`, nodes: selectedNodes, edges: selectedEdges, assertions, receipt, sceneHash };
}

function semanticStage(value: unknown): UniverseStage {
	return value === 'upstream' || value === 'midstream' || value === 'downstream' ? value : 'unknown';
}

function finiteNumberOrNull(value: unknown): number | null {
	return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function nodePresentation(industry: UniverseAtlas['industries'][number], validOrder: number): UniverseNodePresentation {
	const streamCounts = new Map<UniverseStage, number>();
	for (const stage of industry.stages) {
		const stream = semanticStage(stage.stream);
		if (stream === 'unknown') continue;
		streamCounts.set(stream, (streamCounts.get(stream) ?? 0) + (industry.stageMix[stage.key] ?? 0));
	}
	const stage = [...streamCounts.entries()].sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))[0]?.[0] ?? 'unknown';
	return {
		entityKind: 'industry',
		stage,
		validOrder,
		metricValue: finiteNumberOrNull(industry.revenue),
		comparisonValue: null,
		memberCount: industry.nodeCount,
		colorToken: `industry:${industry.id}`,
		attributes: { stagedCount: industry.stagedCount, stageMix: industry.stageMix, stages: industry.stages }
	};
}

async function edgeId(payload: unknown): Promise<string> {
	return `edge:${stripSha256(await canonicalSha256(payload))}`;
}

export async function adaptAtlas(atlas: UniverseAtlas): Promise<{ nodes: UniverseNode[]; edges: UniverseRelation[] }> {
	if (!Array.isArray(atlas.industries) || !Array.isArray(atlas.flows)) throw new Error('Universe atlas requires industries and flows');
	const revenueOrder = new Map([...atlas.industries]
		.sort((left, right) => right.revenue - left.revenue || left.id.localeCompare(right.id))
		.map((industry, index) => [industry.id, index]));
	const nodes: UniverseNode[] = atlas.industries.map((industry) => ({
		nodeId: industry.id,
		label: industry.name,
		lane: 'candidate',
		priority: finiteNumberOrNull(industry.revenue) ?? 0,
		sourceKind: 'atlas',
		sourceRef: `map:atlas#industry=${industry.id}`,
		presentation: nodePresentation(industry, revenueOrder.get(industry.id) ?? 0)
	}));
	const edges: UniverseRelation[] = [];
	for (const [index, flow] of atlas.flows.entries()) {
		const derivationRef = `map:atlas#flow=${index}`;
		edges.push({
			edgeId: await edgeId({ sourceId: flow.fromIndustry, targetId: flow.toIndustry, predicate: 'aggregateFlow', index }),
			sourceId: flow.fromIndustry,
			targetId: flow.toIndustry,
			predicate: 'aggregateFlow',
			lane: 'derived',
			priority: finiteNumberOrNull(flow.edgeCount) ?? 0,
			sourceRef: derivationRef,
			assertionId: '',
			evidenceRefs: [],
			derivationRefs: [derivationRef],
			scenarioReceiptId: ''
		});
	}
	return { nodes, edges };
}

const CURRENT_EDGE_PREDICATES: Readonly<Record<string, UniversePredicate>> = {
	supplier: 'suppliesTo',
	customer: 'sellsTo',
	investor: 'ownsStakeIn',
	affiliate: 'affiliatedWith'
};

function asRecord(value: unknown): Record<string, unknown> {
	return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function asRows(value: unknown): Record<string, unknown>[] {
	return Array.isArray(value) ? value.map(asRecord) : [];
}

export async function adaptIndustryProjection(payload: unknown): Promise<{ nodes: UniverseNode[]; edges: UniverseRelation[] }> {
	const source = asRecord(payload);
	const industryId = String(source.industryId ?? 'unknown');
	const nodeMap = new Map<string, UniverseNode>();
	for (const stageRow of asRows(source.stages)) {
		const stage = semanticStage(stageRow.stream);
		for (const row of asRows(stageRow.nodes)) {
			const nodeId = String(row.stockCode ?? '');
			if (!nodeId) continue;
			nodeMap.set(nodeId, {
				nodeId,
				label: String(row.corpName ?? nodeId),
				lane: 'candidate',
				priority: finiteNumberOrNull(row.revenue) ?? 0,
				sourceKind: 'industry',
				sourceRef: `map:industry:${industryId}#node=${nodeId}`,
				presentation: {
					entityKind: 'company', stage, validOrder: null, metricValue: finiteNumberOrNull(row.revenue),
					comparisonValue: null, memberCount: null, colorToken: `industry:${industryId}`, attributes: row
				}
			});
		}
	}
	for (const row of asRows(source.unclassified)) {
		const nodeId = String(row.stockCode ?? '');
		if (!nodeId) continue;
		nodeMap.set(nodeId, {
			nodeId, label: String(row.corpName ?? nodeId), lane: 'candidate', priority: finiteNumberOrNull(row.revenue) ?? 0,
			sourceKind: 'industry', sourceRef: `map:industry:${industryId}#node=${nodeId}`,
			presentation: { entityKind: 'company', stage: 'unknown', validOrder: null, metricValue: finiteNumberOrNull(row.revenue), comparisonValue: null, memberCount: null, colorToken: `industry:${industryId}`, attributes: row }
		});
	}
	const edges: UniverseRelation[] = [];
	for (const [index, row] of asRows(source.edges).entries()) {
		const sourceId = String(row.from ?? '');
		const targetId = String(row.to ?? '');
		const predicate = CURRENT_EDGE_PREDICATES[String(row.type ?? '')];
		if (!sourceId || !targetId || !predicate || !nodeMap.has(sourceId) || !nodeMap.has(targetId) || sourceId === targetId) continue;
		edges.push({
			edgeId: await edgeId({ sourceId, targetId, predicate, index }), sourceId, targetId, predicate,
			lane: 'candidate', priority: finiteNumberOrNull(row.confidence) ?? 0,
			sourceRef: `map:industry:${industryId}#edge=${index}`,
			assertionId: '', evidenceRefs: [], derivationRefs: [], scenarioReceiptId: ''
		});
	}
	return { nodes: [...nodeMap.values()], edges };
}

export async function adaptCompanyProjection(payload: unknown): Promise<{ nodes: UniverseNode[]; edges: UniverseRelation[] }> {
	const source = asRecord(payload);
	const ego = asRecord(source.ego);
	const egoId = String(ego.stockCode ?? '');
	if (!egoId) throw new Error('Universe company projection requires an ego stockCode');
	const nodeMap = new Map<string, UniverseNode>();
	for (const row of [ego, ...asRows(source.neighbors)]) {
		const nodeId = String(row.stockCode ?? '');
		if (!nodeId) continue;
		nodeMap.set(nodeId, {
			nodeId, label: String(row.corpName ?? nodeId), lane: 'candidate',
			priority: (finiteNumberOrNull(row.revenue) ?? 0) + (nodeId === egoId ? 1e18 : 0),
			sourceKind: 'company', sourceRef: `map:company:${egoId}#node=${nodeId}`,
			presentation: {
				entityKind: 'company', stage: semanticStage(row.stream), validOrder: null,
				metricValue: finiteNumberOrNull(row.revenue), comparisonValue: null, memberCount: null,
				colorToken: `industry:${String(row.industry ?? 'unknown')}`, attributes: row
			}
		});
	}
	const edges: UniverseRelation[] = [];
	for (const [index, row] of asRows(source.edges).entries()) {
		const sourceId = String(row.from ?? '');
		const targetId = String(row.to ?? '');
		const predicate = CURRENT_EDGE_PREDICATES[String(row.type ?? '')];
		if (!sourceId || !targetId || !predicate || !nodeMap.has(sourceId) || !nodeMap.has(targetId) || sourceId === targetId) continue;
		edges.push({
			edgeId: await edgeId({ sourceId, targetId, predicate, index }), sourceId, targetId, predicate,
			lane: 'candidate', priority: finiteNumberOrNull(row.confidence) ?? 0,
			sourceRef: `map:company:${egoId}#edge=${index}`,
			assertionId: '', evidenceRefs: [], derivationRefs: [], scenarioReceiptId: ''
		});
	}
	return { nodes: [...nodeMap.values()], edges };
}
