import { describe, expect, it } from 'vitest';

import { listScanPresets } from './scanPresets';

describe('scan preset runtime port source', () => {
	it('generated screens JSON definitions are available without a server', () => {
		const presets = listScanPresets();
		expect(presets.map((item) => item.id)).toContain('financialStabilityDrawdown');
		expect(presets.map((item) => item.id)).toContain('resilientCompounders');
		expect((presets[0]?.payload.spec as { where?: unknown[] }).where?.length).toBeGreaterThan(0);
	});
});
