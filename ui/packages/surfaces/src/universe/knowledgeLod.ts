import type { UniverseLane } from '@dartlab/ui-contracts';

export type KnowledgeLodLevel = 'L0' | 'L1' | 'L2' | 'L3';

export function knowledgeLodLevel(scale: number): KnowledgeLodLevel {
	if (scale < 0.82) return 'L0';
	if (scale < 1.6) return 'L1';
	if (scale < 3) return 'L2';
	return 'L3';
}

export function knowledgeLabelBudget(level: KnowledgeLodLevel, visibleNodeCount: number): number {
	if (level === 'L0') return 8;
	if (level === 'L1') return visibleNodeCount > 40 ? 12 : 18;
	if (level === 'L2') return 32;
	return 48;
}

export function knowledgeEdgeVisible(level: KnowledgeLodLevel, lane: UniverseLane, selected: boolean): boolean {
	return level !== 'L0' || lane === 'fact' || selected;
}
