import { describe, expect, it } from 'vitest';
import type { UniverseLensRef } from '@dartlab/ui-contracts';
import { compileLensTray, UNIVERSE_LENS_CONTRACT_FIXTURES } from './lenses';
import { compileUniverseWorkflow, UNIVERSE_WORKFLOWS } from './workflows';

describe('Universe lens and workflow compilers', () => {
	it('renders all six engines through one standard Ref contract', async () => {
		expect(UNIVERSE_LENS_CONTRACT_FIXTURES.map((ref) => ref.engine)).toEqual(['industry', 'financial', 'credit', 'macro', 'quant', 'scan']);
		const missing: UniverseLensRef = { ...UNIVERSE_LENS_CONTRACT_FIXTURES[1]!, refId: 'missing', value: null, status: 'missing' };
		const tray = await compileLensTray(missing);
		expect(tray.primary.ref.value).toBeNull();
		expect(tray.primary.gaps[0]?.reasonCode).toBe('valueMissing');
	});

	it('opens exactly three recipes and leaves missing claims unconcluded', async () => {
		expect(UNIVERSE_WORKFLOWS.map((recipe) => recipe.workflowId)).toEqual(['growthSustainability', 'creditFragility', 'disclosureChange']);
		const result = await compileUniverseWorkflow({
			workflowId: 'growthSustainability', snapshotSetId: `sha256:${'a'.repeat(64)}`, seedIds: ['semiconductor'],
			validAt: null, knownAt: null, generatedAt: '2026-07-16'
		});
		expect(result.conclusionReady).toBe(false);
		expect(result.claims.every((claim) => claim.evidence && claim.falsifier)).toBe(true);
		expect(result.claims.some((claim) => claim.lane === 'gap')).toBe(true);
		expect(result.claims.find((claim) => claim.lane === 'scenario')).toMatchObject({ conclusionReady: false, gaps: [{ reasonCode: 'requiredEvidenceMissing' }] });
	});
});
