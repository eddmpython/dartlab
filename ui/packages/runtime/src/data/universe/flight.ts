import type {
	EvidenceReceipt,
	GapReceipt,
	UniverseFlightPlan,
	UniverseFlightReceipt,
	UniverseWorkflowRecipe
} from '@dartlab/ui-contracts';
import { canonicalSha256, stripSha256 } from './canonical';

async function identity(prefix: string, payload: unknown): Promise<string> {
	return `${prefix}:${stripSha256(await canonicalSha256(payload))}`;
}

export interface CompileFlightPlanInput {
	recipe: UniverseWorkflowRecipe;
	snapshotSetId: string;
	seedIds: readonly string[];
	validAt: string | null;
	knownAt: string | null;
}

export async function compileFlightPlan(input: CompileFlightPlanInput): Promise<UniverseFlightPlan> {
	if (input.seedIds.length === 0) throw new Error('Universe flight requires at least one seed');
	const flightId = await identity('flight', {
		workflowId: input.recipe.workflowId,
		version: input.recipe.version,
		snapshotSetId: input.snapshotSetId,
		seedIds: [...new Set(input.seedIds)].sort(),
		validAt: input.validAt,
		knownAt: input.knownAt
	});
	const beats = await Promise.all(input.recipe.procedure.map(async (intent, index) => ({
		beatId: await identity('beat', { flightId, intent, index }),
		intent,
		projectionSpec: {
			projectionId: `${flightId}:${index}`,
			query: `${input.recipe.label} ${intent}`,
			seedIds: [...new Set(input.seedIds)].sort(),
			sourceSnapshotSetId: input.snapshotSetId,
			maxDepth: intent === 'orient' ? 0 : 2,
			maxNodes: 80,
			maxEdges: 160,
			validAt: input.validAt,
			knownAt: input.knownAt
		},
		selectedIds: index === 0 ? [...new Set(input.seedIds)].sort() : [],
		expectedEvidenceRefs: input.recipe.claims.flatMap((claim) => claim.requiredEvidence).sort(),
		transition: index === 0 ? 'replace' as const : intent === 'compare' ? 'overlay' as const : 'diff' as const,
		narration: `${input.recipe.label}: ${intent}`
	})));
	return {
		schemaVersion: 'universeFlightPlan.v1',
		flightId,
		questionRef: null,
		objective: input.recipe.objective,
		snapshotSetId: input.snapshotSetId,
		beats
	};
}

export async function compileFlightReceipt(
	plan: UniverseFlightPlan,
	claimEvidence: readonly EvidenceReceipt[],
	claimGaps: readonly GapReceipt[],
	generatedAt: string
): Promise<UniverseFlightReceipt> {
	const beatEvidence: Record<string, readonly EvidenceReceipt[]> = {};
	const beatGaps: Record<string, readonly GapReceipt[]> = {};
	for (const beat of plan.beats) {
		beatEvidence[beat.beatId] = claimEvidence;
		beatGaps[beat.beatId] = claimGaps;
	}
	const outputHash = await canonicalSha256({ flightId: plan.flightId, beatEvidence, beatGaps });
	return {
		schemaVersion: 'universeFlightReceipt.v1',
		flightId: plan.flightId,
		beatEvidence,
		beatGaps,
		outputHash,
		generatedAt
	};
}
