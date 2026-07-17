import { describe, expect, it } from 'vitest';
import type { UniverseKnowledgeEdge, UniverseKnowledgeNode } from '@dartlab/ui-contracts';
import { compileKnowledgeFilm } from './knowledgeFilm';

function node(nodeId: string, label: string): UniverseKnowledgeNode {
	return {
		nodeId, label, secondaryLabel: '', kind: 'file', domainId: 'sources', lane: 'fact', weight: 10,
		x: 0, y: 0, expandable: false, sourceRef: `source://${nodeId}`, evidenceRefs: [`source://${nodeId}`], attributes: {}
	};
}

const nodes = [node('file', '원본 파일'), node('dataset', '데이터셋'), { ...node('security', '005930'), kind: 'security' as const, lane: 'derived' as const }];
const edges: UniverseKnowledgeEdge[] = [
	{ edgeId: 'dataset-file', sourceId: 'dataset', targetId: 'file', relation: 'contains', lane: 'fact', sourceRef: 'source://file', evidenceRefs: ['source://file'], ruleId: 'fact.v1' },
	{ edgeId: 'security-file', sourceId: 'security', targetId: 'file', relation: 'describes', lane: 'derived', sourceRef: 'source://file', evidenceRefs: ['source://file'], ruleId: 'derived.v1' }
];

describe('Universe Knowledge Film', () => {
	it('reveals fact paths before derived evidence and resolves to the full scene', () => {
		const film = compileKnowledgeFilm(nodes, edges);
		expect(film.map((beat) => beat.mode)).toEqual(['establish', 'trace', 'evidence', 'resolve']);
		expect(film[1]).toMatchObject({ focusEdgeId: 'dataset-file', lane: 'fact' });
		expect(film[2]).toMatchObject({ focusEdgeId: 'security-file', lane: 'derived' });
		expect(film.at(-1)?.revealNodeIds).toEqual(['file', 'dataset', 'security']);
		expect(film.at(-1)?.cameraScale).toBe(1);
	});

	it('keeps large scenes within a deterministic beat budget', () => {
		const manyNodes = Array.from({ length: 30 }, (_, index) => node(`node-${index}`, `노드 ${index}`));
		const manyEdges = manyNodes.slice(1).map((item, index): UniverseKnowledgeEdge => ({
			edgeId: `edge-${index}`, sourceId: manyNodes[0]!.nodeId, targetId: item.nodeId, relation: 'contains', lane: 'fact',
			sourceRef: item.sourceRef, evidenceRefs: item.evidenceRefs, ruleId: 'test.v1'
		}));
		const first = compileKnowledgeFilm(manyNodes, manyEdges, 8);
		const second = compileKnowledgeFilm([...manyNodes].reverse().reverse(), [...manyEdges].reverse(), 8);
		expect(first).toHaveLength(8);
		expect(second.map((beat) => beat.beatId)).toEqual(first.map((beat) => beat.beatId));
		expect(first.at(-1)?.mode).toBe('resolve');
	});
});
