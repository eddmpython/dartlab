import { describe, expect, it } from 'vitest';
import { CURRENT_MACRO_EDGE_SECTOR_KEYS, EDGE_SECTOR_TO_TAILWIND, classifyTailwind, hasNegativeTailwind } from './macroMappings';

describe('macroMappings · terminal macro lens wiring', () => {
	it('positive blended never renders as headwind', () => {
		expect(classifyTailwind(0.08)).toMatchObject({ bucket: 'weakTailwind', tone: 'good', labelKr: '상대 약순풍' });
		expect(classifyTailwind(0.4)).toMatchObject({ bucket: 'tailwind', tone: 'up', labelKr: '순풍' });
		expect(classifyTailwind(0)).toMatchObject({ bucket: 'neutral', tone: 'neutral', labelKr: '중립' });
		expect(classifyTailwind(-0.01)).toMatchObject({ bucket: 'headwind', tone: 'down', labelKr: '역풍' });
	});

	it('headwind existence is based only on negative blended values', () => {
		expect(hasNegativeTailwind([{ blended: 0.02 }, { blended: 0.4 }])).toBe(false);
		expect(hasNegativeTailwind([{ blended: 0.02 }, { blended: -0.01 }])).toBe(true);
	});

	it('covers current v19 transmission sector keys with explicit null joins for weak mappings', () => {
		expect([...CURRENT_MACRO_EDGE_SECTOR_KEYS].sort()).toEqual([
			'all',
			'auto',
			'bank',
			'battery',
			'chemical',
			'energy',
			'finance',
			'food',
			'logistics',
			'retail',
			'semiconductor',
			'shipbuilding',
			'utility'
		]);
		expect(EDGE_SECTOR_TO_TAILWIND.logistics).toMatchObject({ industryId: 'logistics', tailwindKey: null });
		expect(EDGE_SECTOR_TO_TAILWIND.utility).toMatchObject({ industryId: null, tailwindKey: null });
		expect(EDGE_SECTOR_TO_TAILWIND.all).toMatchObject({ industryId: null, tailwindKey: null });
	});
});
