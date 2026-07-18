import type {
	UniverseKnowledgeContent,
	UniverseKnowledgeEdge,
	UniverseKnowledgeNode,
	UniverseKnowledgeNodeKind,
	UniverseKnowledgeScene,
	UniverseKnowledgeTreeNode
} from '@dartlab/ui-contracts';
import { compileKnowledgeFilm } from './knowledgeFilm';

const MAX_SCENE_NODES = 80;

function stableToken(value: string): string {
	let hash = 2166136261;
	for (let index = 0; index < value.length; index += 1) {
		hash ^= value.charCodeAt(index);
		hash = Math.imul(hash, 16777619);
	}
	return (hash >>> 0).toString(36);
}

function exactRef(sourceRef: string, fragment: string): string {
	return `${sourceRef.split('#')[0]}#${fragment}`;
}

function safeCount(value: number): number {
	return Math.max(0, Math.min(Number.MAX_SAFE_INTEGER, Math.floor(value)));
}

function safeAdd(left: number, right: number): number {
	return safeCount(Math.min(Number.MAX_SAFE_INTEGER, left + right));
}

function point(index: number, total: number, radius: number, phase = 0): { x: number; y: number } {
	const angle = phase + (index / Math.max(1, total)) * Math.PI * 2;
	return { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius * 0.76 };
}

function projectedNode(input: {
	nodeId: string;
	label: string;
	secondaryLabel: string;
	kind: UniverseKnowledgeNodeKind;
	target: UniverseKnowledgeNode;
	weight: number;
	x: number;
	y: number;
	sourceRef: string;
	evidenceRefs?: readonly string[];
	attributes: UniverseKnowledgeNode['attributes'];
}): UniverseKnowledgeNode {
	return Object.freeze({
		nodeId: input.nodeId,
		label: input.label,
		secondaryLabel: input.secondaryLabel,
		kind: input.kind,
		domainId: input.target.domainId,
		lane: 'fact',
		weight: input.weight,
		x: input.x,
		y: input.y,
		expandable: false,
		sourceRef: input.sourceRef,
		evidenceRefs: Object.freeze([...(input.evidenceRefs ?? [input.sourceRef])]),
		attributes: Object.freeze({ ...input.attributes })
	});
}

function projectedEdge(input: {
	edgeId: string;
	sourceId: string;
	targetId: string;
	relation: UniverseKnowledgeEdge['relation'];
	sourceRef: string;
	evidenceRefs?: readonly string[];
	ruleId: string;
}): UniverseKnowledgeEdge {
	return Object.freeze({
		edgeId: input.edgeId,
		sourceId: input.sourceId,
		targetId: input.targetId,
		relation: input.relation,
		lane: 'fact',
		sourceRef: input.sourceRef,
		evidenceRefs: Object.freeze([...(input.evidenceRefs ?? [input.sourceRef])]),
		ruleId: input.ruleId
	});
}

interface TextSpan {
	label: string;
	lineStart: number;
	lineEnd: number;
	excerpt: string;
}

function textSpans(text: string): readonly TextSpan[] {
	const lines = text.replace(/\r\n/g, '\n').split('\n');
	const spans: TextSpan[] = [];
	let index = 0;
	while (index < lines.length) {
		while (index < lines.length && !lines[index]?.trim()) index += 1;
		if (index >= lines.length) break;
		const start = index;
		const heading = /^\s{0,3}#{1,6}\s+/.test(lines[index] ?? '');
		if (heading) {
			index += 1;
		} else {
			while (index < lines.length && lines[index]?.trim() && index - start < 8) index += 1;
		}
		const end = Math.max(start, index - 1);
		const excerpt = lines.slice(start, end + 1).join(' ').trim();
		const label = heading
			? (lines[start] ?? '').replace(/^\s{0,3}#{1,6}\s+/, '').trim()
			: excerpt;
		spans.push(Object.freeze({
			label: label.slice(0, 72) || `문서 구간 ${spans.length + 1}`,
			lineStart: start + 1,
			lineEnd: end + 1,
			excerpt: excerpt.slice(0, 240)
		}));
	}
	return Object.freeze(spans);
}

function parentPointer(node: UniverseKnowledgeTreeNode): string | null {
	if (!node.pointer) return null;
	const slash = node.pointer.lastIndexOf('/');
	return slash <= 0 ? '' : node.pointer.slice(0, slash);
}

export function compileKnowledgeContentScene(
	scene: UniverseKnowledgeScene,
	content: UniverseKnowledgeContent,
	focusNodeId: string | null = null
): UniverseKnowledgeScene {
	if (scene.targetId !== content.targetId) return scene;
	const target = scene.nodes.find((node) => node.nodeId === content.targetId);
	if (!target) return scene;

	const nodes: UniverseKnowledgeNode[] = scene.nodes.slice(0, MAX_SCENE_NODES);
	const visibleNodeIds = new Set(nodes.map((node) => node.nodeId));
	const edges: UniverseKnowledgeEdge[] = scene.edges
		.filter((edge) => visibleNodeIds.has(edge.sourceId) && visibleNodeIds.has(edge.targetId));
	let contentPotential = 0;

	const add = (node: UniverseKnowledgeNode, edge: UniverseKnowledgeEdge): boolean => {
		if (nodes.length >= MAX_SCENE_NODES || visibleNodeIds.has(node.nodeId)) return false;
		nodes.push(node);
		visibleNodeIds.add(node.nodeId);
		if (visibleNodeIds.has(edge.sourceId) && visibleNodeIds.has(edge.targetId)) edges.push(edge);
		return true;
	};

	contentPotential += 1;
	const historyId = `content:${stableToken(content.targetId)}:revision`;
	const historyPoint = point(0, 1, 0.24, -Math.PI / 2);
	add(projectedNode({
		nodeId: historyId,
		label: content.fileMeta.lastCommitTitle ?? '파일 수정 이력',
		secondaryLabel: content.fileMeta.lastCommitAt ?? 'Hugging Face revision history',
		kind: 'revision',
		target,
		weight: 7,
		x: historyPoint.x,
		y: historyPoint.y,
		sourceRef: content.fileMeta.historyRef,
		evidenceRefs: [content.fileMeta.historyRef, content.sourceRef],
		attributes: {
			commitId: content.fileMeta.lastCommitId,
			commitTitle: content.fileMeta.lastCommitTitle,
			committedAt: content.fileMeta.lastCommitAt,
			blobId: content.fileMeta.blobId,
			revision: content.revision
		}
	}), projectedEdge({
		edgeId: `edge:${historyId}:${content.targetId}`,
		sourceId: historyId,
		targetId: content.targetId,
		relation: 'revised',
		sourceRef: content.fileMeta.historyRef,
		evidenceRefs: [content.fileMeta.historyRef, content.sourceRef],
		ruleId: 'knowledge.contentRevision.v1'
	}));

	if (content.kind === 'table') {
		const totalRows = content.tableMeta.totalRows ?? content.rows.length;
		const totalColumns = content.tableMeta.totalColumns ?? content.columns.length;
		contentPotential = safeAdd(contentPotential, safeCount(totalRows * (totalColumns + 1)));
		const rowPrefix = `content:${stableToken(content.targetId)}:row:`;
		const fieldPrefix = `content:${stableToken(content.targetId)}:field:`;
		let focusRow: number | null = null;
		if (focusNodeId?.startsWith(rowPrefix)) focusRow = Number(focusNodeId.slice(rowPrefix.length));
		if (focusNodeId?.startsWith(fieldPrefix)) focusRow = Number(focusNodeId.slice(fieldPrefix.length).split(':')[0]);
		if (focusRow === null || !Number.isInteger(focusRow) || focusRow < content.tableMeta.rowStart || focusRow >= content.tableMeta.rowEnd) {
			focusRow = null;
		}

		const rowIds = new Map<number, string>();
		for (let index = 0; index < content.rows.length; index += 1) {
			const absoluteRow = content.tableMeta.rowStart + index;
			const rowId = `${rowPrefix}${absoluteRow}`;
			const position = point(index, content.rows.length, 0.6, -Math.PI / 2);
			const ref = exactRef(content.sourceRef, `row=${absoluteRow + 1}`);
			if (add(projectedNode({
				nodeId: rowId,
				label: `행 ${absoluteRow + 1}`,
				secondaryLabel: `${content.columns.length}개 필드 · 원본 레코드`,
				kind: 'record',
				target,
				weight: absoluteRow === focusRow ? 8 : 5.5,
				x: position.x,
				y: position.y,
				sourceRef: ref,
				attributes: { rowIndex: absoluteRow, rowNumber: absoluteRow + 1, format: content.tableMeta.format }
			}), projectedEdge({
				edgeId: `edge:${content.targetId}:${rowId}`,
				sourceId: content.targetId,
				targetId: rowId,
				relation: 'contains',
				sourceRef: ref,
				ruleId: 'knowledge.contentRow.v1'
			}))) rowIds.set(absoluteRow, rowId);
		}

		const focusIndex = focusRow === null ? -1 : focusRow - content.tableMeta.rowStart;
		const focusRecord = focusIndex >= 0 ? content.rows[focusIndex] : null;
		const focusRowId = focusRow === null ? null : rowIds.get(focusRow);
		if (focusRecord && focusRowId && focusRow !== null) {
			const rowNode = nodes.find((node) => node.nodeId === focusRowId) ?? target;
			for (let index = 0; index < content.columns.length; index += 1) {
				const column = content.columns[index] ?? `column_${index + 1}`;
				const absoluteColumn = content.tableMeta.columnStart + index;
				const gridColumn = index % 4;
				const gridRow = Math.floor(index / 4);
				const gridRowCount = Math.ceil(content.columns.length / 4);
				const position = {
					x: (gridColumn - 1.5) * 0.36,
					y: (gridRow - (gridRowCount - 1) / 2) * 0.36
				};
				const ref = exactRef(content.sourceRef, `row=${focusRow + 1}&column=${encodeURIComponent(column)}`);
				const fieldId = `${fieldPrefix}${focusRow}:${absoluteColumn}`;
				add(projectedNode({
					nodeId: fieldId,
					label: column,
					secondaryLabel: String(focusRecord[column] ?? '').slice(0, 120) || '빈 값',
					kind: 'field',
					target,
					weight: 4.5,
					x: rowNode.x + position.x,
					y: rowNode.y + position.y,
					sourceRef: ref,
					attributes: {
						rowIndex: focusRow,
						rowNumber: focusRow + 1,
						columnIndex: absoluteColumn,
						column,
						value: focusRecord[column] ?? ''
					}
				}), projectedEdge({
					edgeId: `edge:${focusRowId}:${fieldId}`,
					sourceId: focusRowId,
					targetId: fieldId,
					relation: 'contains',
					sourceRef: ref,
					ruleId: 'knowledge.contentField.v1'
				}));
			}
		}
	} else if (content.kind === 'json') {
		contentPotential = safeAdd(contentPotential, content.tree.length);
		const pointerIds = new Map<string, string>();
		for (let index = 0; index < content.tree.length; index += 1) {
			const item = content.tree[index];
			if (!item) continue;
			const nodeId = `content:${stableToken(content.targetId)}:json:${stableToken(item.pointer || '/')}`;
			const parent = parentPointer(item);
			const parentId = parent === null ? content.targetId : pointerIds.get(parent);
			if (!parentId) continue;
			const position = point(index, Math.min(content.tree.length, MAX_SCENE_NODES), 0.36 + Math.min(0.48, item.depth * 0.07), -Math.PI / 2);
			const ref = exactRef(content.sourceRef, `json-pointer=${encodeURIComponent(item.pointer)}`);
			if (add(projectedNode({
				nodeId,
				label: item.key,
				secondaryLabel: item.childCount > 0 ? `${item.childCount}개 하위 항목` : item.value.slice(0, 120),
				kind: item.childCount > 0 ? 'record' : 'field',
				target,
				weight: Math.max(3.5, 7 - item.depth * 0.45),
				x: position.x,
				y: position.y,
				sourceRef: ref,
				attributes: { pointer: item.pointer, valueKind: item.valueKind, value: item.value, childCount: item.childCount }
			}), projectedEdge({
				edgeId: `edge:${parentId}:${nodeId}`,
				sourceId: parentId,
				targetId: nodeId,
				relation: 'contains',
				sourceRef: ref,
				ruleId: 'knowledge.contentJsonPointer.v1'
			}))) pointerIds.set(item.pointer, nodeId);
		}
		if (content.tree.length === 0 && content.text) {
			const spans = textSpans(content.text);
			contentPotential = safeAdd(contentPotential, spans.length);
			for (let index = 0; index < spans.length; index += 1) {
				const span = spans[index];
				if (!span) continue;
				const position = point(index, spans.length, 0.5 + (index % 3) * 0.11, -Math.PI / 2);
				const ref = exactRef(content.sourceRef, `L${span.lineStart}-L${span.lineEnd}`);
				const nodeId = `content:${stableToken(content.targetId)}:json-lines:${span.lineStart}-${span.lineEnd}`;
				add(projectedNode({
					nodeId,
					label: span.label,
					secondaryLabel: `JSON 원문 ${span.lineStart}-${span.lineEnd}행`,
					kind: 'section',
					target,
					weight: 5.5,
					x: position.x,
					y: position.y,
					sourceRef: ref,
					attributes: { lineStart: span.lineStart, lineEnd: span.lineEnd, excerpt: span.excerpt, truncated: content.receipt.truncated }
				}), projectedEdge({
					edgeId: `edge:${content.targetId}:${nodeId}`,
					sourceId: content.targetId,
					targetId: nodeId,
					relation: 'describes',
					sourceRef: ref,
					ruleId: 'knowledge.contentJsonLineSpan.v1'
				}));
			}
		}
	} else if (content.kind === 'text' && content.text) {
		const spans = textSpans(content.text);
		contentPotential = safeAdd(contentPotential, spans.length);
		for (let index = 0; index < spans.length; index += 1) {
			const span = spans[index];
			if (!span) continue;
			const position = point(index, spans.length, 0.5 + (index % 3) * 0.11, -Math.PI / 2);
			const ref = exactRef(content.sourceRef, `L${span.lineStart}-L${span.lineEnd}`);
			const nodeId = `content:${stableToken(content.targetId)}:lines:${span.lineStart}-${span.lineEnd}`;
			add(projectedNode({
				nodeId,
				label: span.label,
				secondaryLabel: `원문 ${span.lineStart}-${span.lineEnd}행`,
				kind: 'section',
				target,
				weight: 5.5,
				x: position.x,
				y: position.y,
				sourceRef: ref,
				attributes: { lineStart: span.lineStart, lineEnd: span.lineEnd, excerpt: span.excerpt, truncated: content.receipt.truncated }
			}), projectedEdge({
				edgeId: `edge:${content.targetId}:${nodeId}`,
				sourceId: content.targetId,
				targetId: nodeId,
				relation: 'describes',
				sourceRef: ref,
				ruleId: 'knowledge.contentLineSpan.v1'
			}));
		}
	}

	const addedNodeCount = Math.max(0, nodes.length - scene.nodes.length);
	const omittedContent = Math.max(0, contentPotential - addedNodeCount);
	const frozenNodes = Object.freeze(nodes.map((node) => Object.freeze({ ...node })));
	const frozenEdges = Object.freeze(edges.map((edge) => Object.freeze({ ...edge })));
	return Object.freeze({
		...scene,
		sceneId: `${scene.sceneId}:content:${content.tableMeta.rowStart}:${content.tableMeta.columnStart}:${stableToken(focusNodeId ?? '')}`,
		nodes: frozenNodes,
		edges: frozenEdges,
		film: compileKnowledgeFilm(frozenNodes, frozenEdges),
		receipt: Object.freeze({
			indexedItemCount: safeAdd(scene.receipt.indexedItemCount, contentPotential),
			outputNodeCount: frozenNodes.length,
			outputEdgeCount: frozenEdges.length,
			omittedNodeCount: safeAdd(scene.receipt.omittedNodeCount, omittedContent),
			sourceRevision: scene.receipt.sourceRevision
		})
	});
}
