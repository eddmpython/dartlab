import { describe, expect, it } from 'vitest';
import type { UniverseLayoutNode } from './layout';
import { compileDeterministicLayout, projectAnchors } from './layout';

const stages = ['upstream', 'midstream', 'downstream', 'unknown'] as const;
const statuses = ['fact', 'candidate', 'derived', 'disputed', 'retracted', 'scenario', 'unknown'] as const;
const nodes: UniverseLayoutNode[] = Array.from({ length: 20 }, (_, index) => ({
	nodeId: `layout-node-${String(index + 1).padStart(2, '0')}`,
	label: `Layout Node ${String(index + 1).padStart(2, '0')}`,
	stage: stages[index % stages.length]!,
	status: statuses[index % statuses.length]!,
	validOrder: index % 10
}));

describe('Universe deterministic layout', () => {
	it('matches the promoted attempt golden hash and ignores input order', () => {
		const sceneHash = `sha256:${'a'.repeat(64)}`;
		const first = compileDeterministicLayout(nodes, sceneHash);
		const reversed = compileDeterministicLayout([...nodes].reverse(), sceneHash);
		expect(first.logicalHash).toBe('fnv1a64:8a896e8cdae42039');
		expect(reversed.logicalHash).toBe(first.logicalHash);
		expect(projectAnchors(first, { width: 1280, height: 720, dpr: 1 }).anchorHash)
			.toBe(projectAnchors(reversed, { width: 1280, height: 720, dpr: 1 }).anchorHash);
	});
});
