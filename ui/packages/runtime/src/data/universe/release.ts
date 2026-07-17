import type {
	UniverseAssertion,
	UniverseCapabilityId,
	UniverseCapabilityReceipt,
	UniverseProductReceipt,
	UniverseReleaseState,
	UniverseRouteSeed
} from '@dartlab/ui-contracts';

type ProductInput = Omit<UniverseRouteSeed, 'product'>;

function capability(
	capabilityId: UniverseCapabilityId,
	status: UniverseCapabilityReceipt['status'],
	mode: string,
	reasonCode: string
): UniverseCapabilityReceipt {
	return { capabilityId, status, mode, reasonCode };
}

function assertionHasExactEvidence(assertion: UniverseAssertion | undefined): boolean {
	if (!assertion || !['observed', 'corroborated'].includes(assertion.status)) return false;
	return assertion.evidenceRefs.length > 0 && assertion.evidenceRefs.every((pointer) => Boolean(
		pointer.documentId
		&& pointer.sectionPath
		&& pointer.sourceRef
		&& pointer.sourcePublishedAt
		&& pointer.availableAt
		&& pointer.contentHash
		&& (pointer.textLocator || pointer.tableLocator)
	));
}

function assertProductionScene(input: ProductInput): void {
	if (!input.meta.buildId || !input.meta.buildTime || !input.scene.sceneHash) {
		throw new Error('Universe production admission failed: build identity is incomplete');
	}
	if (input.atlas.industries.length === 0 || input.scene.nodes.length === 0) {
		throw new Error('Universe production admission failed: atlas scene is empty');
	}
	if (input.scene.nodes.some((node) => !node.nodeId || !node.sourceRef)) {
		throw new Error('Universe production admission failed: node provenance is incomplete');
	}
	const nodeIds = new Set(input.scene.nodes.map((node) => node.nodeId));
	if (nodeIds.size !== input.scene.nodes.length || new Set(input.scene.edges.map((edge) => edge.edgeId)).size !== input.scene.edges.length) {
		throw new Error('Universe production admission failed: scene identity is duplicated');
	}
	if (input.scene.edges.some((edge) => !edge.sourceRef || edge.sourceId === edge.targetId || !nodeIds.has(edge.sourceId) || !nodeIds.has(edge.targetId))) {
		throw new Error('Universe production admission failed: relation provenance is incomplete');
	}
	if (input.scene.receipt.outputNodeCount !== input.scene.nodes.length
		|| input.scene.receipt.outputEdgeCount !== input.scene.edges.length) {
		throw new Error('Universe production admission failed: scene receipt count is inconsistent');
	}
	const assertions = new Map(input.scene.assertions.map((assertion) => [assertion.assertionId, assertion]));
	if (input.scene.edges.some((edge) => edge.lane === 'fact' && !assertionHasExactEvidence(assertions.get(edge.assertionId)))) {
		throw new Error('Universe production admission failed: fact relation has no exact evidence');
	}
}

export function compileUniverseProductReceipt(input: ProductInput): UniverseProductReceipt {
	const factRelationCount = input.scene.edges.filter((edge) => edge.lane === 'fact').length;
	if (input.releaseState === 'disabled') {
		return {
			schemaVersion: 'universeProductReceipt.v1',
			releaseState: input.releaseState,
			routeReady: false,
			generatedAt: input.meta.buildTime,
			buildId: input.meta.buildId,
			sceneHash: input.scene.sceneHash,
			factRelationCount,
			capabilities: [
				'atlas', 'changeSignals', 'exactReplay', 'evidenceSearch', 'thesisKillChain', 'factRelations'
			].map((capabilityId) => capability(capabilityId as UniverseCapabilityId, 'disabled', 'off', 'routeDisabled'))
		};
	}

	assertProductionScene(input);
	return {
		schemaVersion: 'universeProductReceipt.v1',
		releaseState: input.releaseState,
		routeReady: true,
		generatedAt: input.meta.buildTime,
		buildId: input.meta.buildId,
		sceneHash: input.scene.sceneHash,
		factRelationCount,
		capabilities: [
			capability('atlas', 'ready', 'deterministic2d', 'admitted'),
			capability('changeSignals', 'ready', 'currentSignals', 'admittedAsDerivedSignals'),
			capability(
				'exactReplay',
				input.snapshot.exactReplayReady ? 'ready' : 'guarded',
				input.snapshot.exactReplayReady ? 'exactReplay' : 'currentOnly',
				input.snapshot.exactReplayReady ? 'admitted' : 'immutableSourceSetIncomplete'
			),
			capability('evidenceSearch', 'ready', 'candidateOnlyUntilExactPointer', 'failClosedEvidenceAdmission'),
			capability('thesisKillChain', 'ready', 'openUntilEvidenceComplete', 'failClosedConclusion'),
			capability(
				'factRelations',
				factRelationCount > 0 ? 'ready' : 'guarded',
				factRelationCount > 0 ? 'exactEvidence' : 'candidateAndDerivedOnly',
				factRelationCount > 0 ? 'admitted' : 'noExactFactRelations'
			)
		]
	};
}
