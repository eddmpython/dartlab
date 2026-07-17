import { describe, expect, it } from 'vitest';
import { knowledgeEdgeVisible, knowledgeLabelBudget, knowledgeLodLevel } from './knowledgeLod';

describe('Universe knowledge LOD', () => {
	it('moves through four stable semantic zoom levels', () => {
		expect([0.62, 0.82, 1.6, 3, 4.8].map(knowledgeLodLevel)).toEqual(['L0', 'L1', 'L2', 'L3', 'L3']);
	});

	it('keeps facts and selected evidence visible in the overview level', () => {
		expect(knowledgeEdgeVisible('L0', 'fact', false)).toBe(true);
		expect(knowledgeEdgeVisible('L0', 'derived', false)).toBe(false);
		expect(knowledgeEdgeVisible('L0', 'derived', true)).toBe(true);
		expect(knowledgeLabelBudget('L0', 80)).toBe(8);
		expect(knowledgeLabelBudget('L3', 80)).toBe(48);
	});
});
