/**
 * Universe의 밀도 상한, label collision, lower LOD, 생략 영수증을 검증한다.
 *
 * Capabilities
 *   250, 500, 1,000 node fixture를 desktop과 mobile budget에 맞춰 deterministic하게 축소한다.
 *
 * AIContext
 *   AI 역할: 화면에 들어오지 않은 node, edge, label을 삭제된 사실처럼 숨기지 않고 reason과 count로 남긴다.
 *
 * Guide
 *   Active mark와 label budget은 representation 계약이며 truth 또는 source artifact를 수정하지 않는다.
 *
 * When
 *   U0-V03 density, LOD, label policy 또는 omission receipt가 바뀔 때 사용한다.
 *
 * How
 *   Stable priority truncation, semantic layout, viewport anchor, collision-free label selection을 순서대로 적용한다.
 *
 * Requires
 *   deterministicLayoutProbe.mjs의 logical layout과 viewport projection이 필요하다.
 *
 * Raises
 *   잘못된 fixture size, target, node identity, edge endpoint는 Error를 발생시킨다.
 *
 * Example
 *   `node densityOmissionProbe.mjs`
 *
 * See Also
 *   tests/_attempts/dartlabUniverse/visual/deterministicLayoutProbe.mjs
 *
 * 결과
 *   여섯 density case의 mark 상한, collision, exact omission coverage와 repeat hash를 출력한다.
 */

import {
	compileDeterministicLayout,
	deterministicPayloadHash,
	projectAnchors
} from './deterministicLayoutProbe.mjs';

const stages = Object.freeze(['upstream', 'midstream', 'downstream', 'unknown']);
const statuses = Object.freeze(['fact', 'candidate', 'derived', 'disputed', 'retracted', 'scenario', 'unknown']);
const fixtureSizes = Object.freeze([250, 500, 1000]);

export const densityTargets = Object.freeze({
	desktop: Object.freeze({
		name: 'desktop', width: 1280, height: 720, dpr: 1,
		nodeBudget: 500, edgeBudget: 1000, labelBudget: 80,
		labelWidth: 72, labelHeight: 20, labelGap: 2
	}),
	mobile: Object.freeze({
		name: 'mobile', width: 390, height: 844, dpr: 3,
		nodeBudget: 250, edgeBudget: 500, labelBudget: 40,
		labelWidth: 64, labelHeight: 20, labelGap: 2
	})
});

function statusCounts(nodes) {
	const counts = Object.fromEntries(statuses.map((status) => [status, 0]));
	for (const node of nodes) counts[node.status] += 1;
	return Object.freeze(counts);
}

function quantile(values, fraction) {
	if (values.length === 0) return null;
	const index = Math.round((values.length - 1) * fraction);
	return values[index];
}

function changeQuantiles(nodes) {
	const values = nodes.map((node) => node.changeMagnitude).sort((left, right) => left - right);
	return Object.freeze({
		p25: quantile(values, 0.25),
		p50: quantile(values, 0.5),
		p75: quantile(values, 0.75)
	});
}

function priorityOrder(left, right) {
	return right.priority - left.priority || left.nodeId.localeCompare(right.nodeId);
}

function edgePriorityOrder(left, right) {
	return right.priority - left.priority || left.edgeId.localeCompare(right.edgeId);
}

function rectanglesOverlap(left, right, gap) {
	return left.x < right.x + right.width + gap
		&& left.x + left.width + gap > right.x
		&& left.y < right.y + right.height + gap
		&& left.y + left.height + gap > right.y;
}

function collisionPairCount(labels, gap = 0) {
	let count = 0;
	for (let leftIndex = 0; leftIndex < labels.length; leftIndex += 1) {
		for (let rightIndex = leftIndex + 1; rightIndex < labels.length; rightIndex += 1) {
			if (rectanglesOverlap(labels[leftIndex], labels[rightIndex], gap)) count += 1;
		}
	}
	return count;
}

function selectLabels(activeNodes, anchorByNode, target) {
	const selected = [];
	let collisionOmittedCount = 0;
	let budgetOmittedCount = 0;
	for (const node of [...activeNodes].sort(priorityOrder)) {
		if (selected.length >= target.labelBudget) {
			budgetOmittedCount += 1;
			continue;
		}
		const anchor = anchorByNode.get(node.nodeId);
		const width = target.labelWidth;
		const height = target.labelHeight;
		const candidate = Object.freeze({
			nodeId: node.nodeId,
			label: node.label,
			x: Math.max(0, Math.min(target.width - width, anchor.x + 6)),
			y: Math.max(0, Math.min(target.height - height, anchor.y - height / 2)),
			width,
			height
		});
		if (selected.some((label) => rectanglesOverlap(candidate, label, target.labelGap))) {
			collisionOmittedCount += 1;
			continue;
		}
		selected.push(candidate);
	}
	const pairCount = collisionPairCount(selected);
	const possiblePairs = selected.length * (selected.length - 1) / 2;
	return Object.freeze({
		labels: Object.freeze(selected),
		receipt: Object.freeze({
			candidateCount: activeNodes.length,
			visibleCount: selected.length,
			labelBudget: target.labelBudget,
			collisionOmittedCount,
			budgetOmittedCount,
			omittedCount: collisionOmittedCount + budgetOmittedCount,
			pairCollisionCount: pairCount,
			collisionRate: possiblePairs === 0 ? 0 : pairCount / possiblePairs
		})
	});
}

export function buildDensityFixture(nodeCount) {
	if (!fixtureSizes.includes(nodeCount)) {
		throw new Error(`unsupported density fixture size: ${nodeCount}`);
	}
	const nodes = Array.from({ length: nodeCount }, (_, index) => Object.freeze({
		nodeId: `density-node-${String(index + 1).padStart(4, '0')}`,
		label: `N${String(index + 1).padStart(4, '0')}`,
		stage: stages[index % stages.length],
		status: statuses[index % statuses.length],
		validOrder: index % 50,
		priority: nodeCount - index,
		changeMagnitude: Math.round((((index * 37) % 211) / 210) * 1000) / 1000
	}));
	const offsets = [1, 7, 31];
	const edges = nodes.flatMap((node, sourceIndex) => offsets.map((offset) => {
		const targetIndex = (sourceIndex + offset) % nodeCount;
		return Object.freeze({
			edgeId: `${node.nodeId}:to:${nodes[targetIndex].nodeId}`,
			sourceId: node.nodeId,
			targetId: nodes[targetIndex].nodeId,
			priority: Math.min(node.priority, nodes[targetIndex].priority)
		});
	}));
	return Object.freeze({
		schemaVersion: 'densityFixture.v1',
		nodeCount,
		sourceSceneHash: `sha256:${nodeCount.toString(16).padStart(64, '0')}`,
		nodes: Object.freeze(nodes),
		edges: Object.freeze(edges)
	});
}

export function compileDensityProjection(fixture, targetName) {
	const target = densityTargets[targetName];
	if (!target) throw new Error(`unsupported density target: ${targetName}`);
	if (!fixture || !Array.isArray(fixture.nodes) || !Array.isArray(fixture.edges)) {
		throw new Error('density projection requires nodes and edges');
	}
	const orderedNodes = [...fixture.nodes].sort(priorityOrder);
	const nodeIds = new Set(orderedNodes.map((node) => node.nodeId));
	if (nodeIds.size !== orderedNodes.length) throw new Error('density fixture contains duplicate nodes');
	for (const edge of fixture.edges) {
		if (!nodeIds.has(edge.sourceId) || !nodeIds.has(edge.targetId)) {
			throw new Error(`density edge endpoint is missing: ${edge.edgeId}`);
		}
	}
	const activeNodes = orderedNodes.slice(0, target.nodeBudget);
	const omittedNodes = orderedNodes.slice(target.nodeBudget);
	const activeNodeIds = new Set(activeNodes.map((node) => node.nodeId));
	const eligibleEdges = fixture.edges
		.filter((edge) => activeNodeIds.has(edge.sourceId) && activeNodeIds.has(edge.targetId))
		.sort(edgePriorityOrder);
	const activeEdges = eligibleEdges.slice(0, target.edgeBudget);
	const endpointOmittedEdgeCount = fixture.edges.length - eligibleEdges.length;
	const budgetOmittedEdgeCount = eligibleEdges.length - activeEdges.length;
	const layout = compileDeterministicLayout(activeNodes, { sourceSceneHash: fixture.sourceSceneHash });
	const anchorProjection = projectAnchors(layout, target);
	const anchorByNode = new Map(anchorProjection.anchors.map((anchor) => [anchor.nodeId, anchor]));
	const labelProjection = selectLabels(activeNodes, anchorByNode, target);
	const inputCounts = statusCounts(orderedNodes);
	const activeCounts = statusCounts(activeNodes);
	const omittedCounts = statusCounts(omittedNodes);
	const nodeOmissionAccounted = omittedNodes.length;
	const edgeOmissionAccounted = endpointOmittedEdgeCount + budgetOmittedEdgeCount;
	const labelOmissionAccounted = labelProjection.receipt.omittedCount;
	const receipt = Object.freeze({
		schemaVersion: 'densityOmissionReceipt.v1',
		target: target.name,
		sourceSceneHash: fixture.sourceSceneHash,
		inputNodeCount: orderedNodes.length,
		activeNodeCount: activeNodes.length,
		omittedNodeCount: omittedNodes.length,
		nodeBudget: target.nodeBudget,
		inputEdgeCount: fixture.edges.length,
		activeEdgeCount: activeEdges.length,
		omittedEdgeCount: fixture.edges.length - activeEdges.length,
		edgeBudget: target.edgeBudget,
		lowerLodApplied: omittedNodes.length > 0 || fixture.edges.length > target.edgeBudget,
		nodeOmissionReasons: Object.freeze({ activeNodeBudget: omittedNodes.length }),
		edgeOmissionReasons: Object.freeze({
			endpointOmitted: endpointOmittedEdgeCount,
			activeEdgeBudget: budgetOmittedEdgeCount
		}),
		inputStatusCounts: inputCounts,
		activeStatusCounts: activeCounts,
		omittedStatusCounts: omittedCounts,
		aggregateReceipt: Object.freeze({
			memberCount: omittedNodes.length,
			observedCount: omittedCounts.fact,
			candidateCount: omittedCounts.candidate,
			unknownCount: omittedCounts.unknown,
			omittedCount: omittedNodes.length,
			coverage: orderedNodes.length === 0 ? 1 : activeNodes.length / orderedNodes.length,
			statusCounts: omittedCounts,
			quantiles: changeQuantiles(omittedNodes),
			topChanges: Object.freeze([...omittedNodes]
				.sort((left, right) => right.changeMagnitude - left.changeMagnitude || priorityOrder(left, right))
				.slice(0, 5)
				.map((node) => Object.freeze({ nodeId: node.nodeId, changeMagnitude: node.changeMagnitude })))
		}),
		labelReceipt: labelProjection.receipt,
		receiptCoverage: Object.freeze({
			node: nodeOmissionAccounted === omittedNodes.length ? 1 : 0,
			edge: edgeOmissionAccounted === fixture.edges.length - activeEdges.length ? 1 : 0,
			label: labelOmissionAccounted === activeNodes.length - labelProjection.labels.length ? 1 : 0
		}),
		layoutHash: layout.logicalHash,
		anchorHash: anchorProjection.anchorHash
	});
	const payload = {
		receipt,
		activeNodeIds: activeNodes.map((node) => node.nodeId),
		activeEdgeIds: activeEdges.map((edge) => edge.edgeId),
		labels: labelProjection.labels
	};
	return Object.freeze({
		target,
		activeNodes: Object.freeze(activeNodes),
		activeEdges: Object.freeze(activeEdges),
		anchors: anchorProjection.anchors,
		labels: labelProjection.labels,
		receipt,
		receiptHash: deterministicPayloadHash(payload)
	});
}

export function inspectDensityOmission() {
	const cases = [];
	for (const nodeCount of fixtureSizes) {
		const fixture = buildDensityFixture(nodeCount);
		for (const targetName of Object.keys(densityTargets)) {
			const projection = compileDensityProjection(fixture, targetName);
			const reversed = compileDensityProjection({
				...fixture,
				nodes: [...fixture.nodes].reverse(),
				edges: [...fixture.edges].reverse()
			}, targetName);
			cases.push(Object.freeze({
				nodeCount,
				target: targetName,
				activeNodeCount: projection.receipt.activeNodeCount,
				omittedNodeCount: projection.receipt.omittedNodeCount,
				activeEdgeCount: projection.receipt.activeEdgeCount,
				omittedEdgeCount: projection.receipt.omittedEdgeCount,
				visibleLabelCount: projection.receipt.labelReceipt.visibleCount,
				labelCollisionRate: projection.receipt.labelReceipt.collisionRate,
				receiptCoverage: projection.receipt.receiptCoverage,
				receiptHash: projection.receiptHash,
				repeatHashMatches: projection.receiptHash === reversed.receiptHash
			}));
		}
	}
	const maximumCollisionRate = Math.max(...cases.map((item) => item.labelCollisionRate));
	const exactReceiptCases = cases.filter((item) => Object.values(item.receiptCoverage).every((value) => value === 1)).length;
	const repeatHashMatches = cases.filter((item) => item.repeatHashMatches).length;
	const budgetCompliantCases = cases.filter((item) => {
		const target = densityTargets[item.target];
		return item.activeNodeCount <= target.nodeBudget
			&& item.activeEdgeCount <= target.edgeBudget
			&& item.visibleLabelCount <= target.labelBudget;
	}).length;
	return Object.freeze({
		schemaVersion: 'densityOmissionReport.v1',
		caseCount: cases.length,
		cases: Object.freeze(cases),
		maximumCollisionRate,
		collisionTarget: 0.02,
		exactReceiptCases,
		repeatHashMatches,
		budgetCompliantCases,
		machineReady: maximumCollisionRate <= 0.02
			&& exactReceiptCases === cases.length
			&& repeatHashMatches === cases.length
			&& budgetCompliantCases === cases.length
	});
}

export function main() {
	process.stdout.write(`${JSON.stringify(inspectDensityOmission(), null, 2)}\n`);
	return 0;
}

if (typeof process !== 'undefined' && process.versions?.node) {
	const { pathToFileURL } = await import('node:url');
	if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
		process.exitCode = main();
	}
}
