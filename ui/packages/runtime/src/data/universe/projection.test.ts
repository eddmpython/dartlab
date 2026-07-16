import { describe, expect, it } from 'vitest';
import type { ProjectionSpec, UniverseNode, UniverseRelation } from '@dartlab/ui-contracts';
import { compileProjection } from './projection';

const snapshotId = `sha256:${'a'.repeat(64)}`;
const spec: ProjectionSpec = {
	projectionId: 'fixture',
	query: 'fixture query',
	seedIds: ['a'],
	sourceSnapshotSetId: snapshotId,
	maxDepth: 2,
	maxNodes: 2,
	maxEdges: 1
};
const nodes: UniverseNode[] = [
	{ nodeId: 'a', label: 'A', lane: 'candidate', priority: 2, sourceKind: 'fixture', sourceRef: 'fixture:a' },
	{ nodeId: 'b', label: 'B', lane: 'candidate', priority: 1, sourceKind: 'fixture', sourceRef: 'fixture:b' },
	{ nodeId: 'c', label: 'C', lane: 'candidate', priority: 0, sourceKind: 'fixture', sourceRef: 'fixture:c' }
];
const edges: UniverseRelation[] = [
	{
		edgeId: 'edge:ab', sourceId: 'a', targetId: 'b', predicate: 'suppliesTo', lane: 'candidate', priority: 2,
		sourceRef: 'fixture:ab', assertionId: '', evidenceRefs: [], derivationRefs: [], scenarioReceiptId: ''
	},
	{
		edgeId: 'edge:ac', sourceId: 'a', targetId: 'c', predicate: 'sellsTo', lane: 'candidate', priority: 1,
		sourceRef: 'fixture:ac', assertionId: '', evidenceRefs: [], derivationRefs: [], scenarioReceiptId: ''
	}
];

describe('compileProjection', () => {
	it('is order independent and keeps hard bounds with omission receipts', async () => {
		const first = await compileProjection(spec, nodes, edges);
		const second = await compileProjection(spec, [...nodes].reverse(), [...edges].reverse());
		expect(second.sceneHash).toBe(first.sceneHash);
		expect(first.nodes.map((node) => node.nodeId)).toEqual(['a', 'b']);
		expect(first.edges.map((edge) => edge.edgeId)).toEqual(['edge:ab']);
		expect(first.receipt.omission.omittedNodeCount).toBe(1);
		expect(first.receipt.omission.omittedEdgeCount).toBe(1);
	});

	it('fails closed for a self loop', async () => {
		const loop = { ...edges[0]!, targetId: 'a' };
		await expect(compileProjection(spec, nodes, [loop])).rejects.toThrow('self-loop');
	});

	it('requires exact assertion and evidence identities for fact edges', async () => {
		const fact = { ...edges[0]!, lane: 'fact' as const };
		await expect(compileProjection(spec, nodes, [fact])).rejects.toThrow('exact assertion and evidence');
	});
});
