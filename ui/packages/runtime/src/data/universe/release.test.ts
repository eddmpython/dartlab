import { describe, expect, it } from 'vitest';
import type { UniverseRouteSeed } from '@dartlab/ui-contracts';
import { compileUniverseProductReceipt } from './release';

function fixture(): Omit<UniverseRouteSeed, 'product'> {
	return {
		meta: { schemaVersion: 1, buildId: 'build-1', buildTime: '2026-07-17T00:00:00Z', commitSha: 'abc', dataAsOf: {}, sizes: {}, counts: {} },
		atlas: { version: '1', industries: [{ id: 'industry', name: '산업', revenue: 1, nodeCount: 1, stagedCount: 1, stageMix: {}, stages: [] }], flows: [] },
		snapshot: { schemaVersion: 'sourceSnapshotSet.v1', snapshotSetId: 'snapshot', createdAt: '2026-07-17T00:00:00Z', sources: [], mapBuildId: 'build-1', capabilityCatalogVersion: null, recipeCatalogVersion: null, exactReplayReady: false, unreplayableSourceIds: ['catalog'], missingDataAsOfSourceIds: [], missingRedistributionReceiptSourceIds: [] },
		scene: {
			schemaVersion: 'boundedScene.v1', sceneId: 'scene',
			nodes: [{ nodeId: 'industry', label: '산업', lane: 'candidate', priority: 1, sourceKind: 'atlas', sourceRef: 'map:atlas#industry' }],
			edges: [], assertions: [],
			receipt: { specHash: 'spec', sourceSnapshotSetId: 'snapshot', inputNodeCount: 1, inputEdgeCount: 0, outputNodeCount: 1, outputEdgeCount: 0, seedCount: 1, retainedSeedCount: 1, maxDepthObserved: 0, omission: { omittedNodeCount: 0, omittedEdgeCount: 0, nodeReasonCounts: [], edgeReasonCounts: [], omittedNodeLaneCounts: [], omittedEdgeLaneCounts: [] } },
			sceneHash: 'scene-hash'
		},
		releaseState: 'ga'
	};
}

describe('Universe product admission', () => {
	it('admits the production route while guarding evidence-specific lanes', () => {
		const receipt = compileUniverseProductReceipt(fixture());
		expect(receipt.routeReady).toBe(true);
		expect(receipt.capabilities.find((item) => item.capabilityId === 'exactReplay')?.status).toBe('guarded');
		expect(receipt.capabilities.find((item) => item.capabilityId === 'factRelations')?.status).toBe('guarded');
	});

	it('fails closed when a fact relation lacks exact evidence', () => {
		const input = fixture();
		input.scene = {
			...input.scene,
			nodes: [...input.scene.nodes, { nodeId: 'customer', label: '고객', lane: 'candidate', priority: 1, sourceKind: 'atlas', sourceRef: 'map:atlas#customer' }],
			edges: [{ edgeId: 'fact-1', sourceId: 'industry', targetId: 'customer', predicate: 'suppliesTo', lane: 'fact', priority: 1, sourceRef: 'map:edge', assertionId: 'assertion-1', evidenceRefs: [], derivationRefs: [], scenarioReceiptId: '' }],
			receipt: { ...input.scene.receipt, outputNodeCount: 2, outputEdgeCount: 1 }
		};
		expect(() => compileUniverseProductReceipt(input)).toThrow(/fact relation has no exact evidence/);
	});

	it('returns an operable disabled receipt for incident isolation', () => {
		const input = fixture();
		input.releaseState = 'disabled';
		const receipt = compileUniverseProductReceipt(input);
		expect(receipt.routeReady).toBe(false);
		expect(receipt.capabilities.every((item) => item.status === 'disabled')).toBe(true);
	});
});
