/**
 * Universe semantic logical coordinate와 viewport anchor 결정론을 검증한다.
 *
 * Capabilities
 *   Stage, valid order 또는 time unknown lane, status를 logical coordinate로 만들고 viewport 및 DPR anchor와 layout receipt를 계산한다.
 *
 * AIContext
 *   AI 역할: force simulation의 임의 위치를 truth로 저장하지 않고 같은 scene의 위치를 재현한다.
 *
 * Guide
 *   Pure logical hash, viewport projection, real browser audit를 별도 단계로 실행한다.
 *
 * When
 *   U0-V02 layout algorithm, semantic anchor 또는 viewport mapping이 바뀔 때 사용한다.
 *
 * How
 *   compileDeterministicLayout 뒤 projectAnchors를 호출하고 browserLayoutAudit.ps1로 engine drift를 측정한다.
 *
 * Requires
 *   Pure probe는 Node.js만, browser audit는 Playwright CLI와 Chrome, Firefox, WebKit이 필요하다.
 *
 * Raises
 *   잘못된 node identity, stage, status, valid order, viewport, DPR은 Error를 발생시킨다.
 *
 * Example
 *   `node deterministicLayoutProbe.mjs`
 *
 * See Also
 *   tests/_attempts/dartlabUniverse/visual/layoutReference.html
 *
 * 결과
 *   Reference 또는 live bounded scene의 20 replay logical hash와 3 viewport anchor를 deterministic receipt로 출력한다.
 */

export const layoutVersion = 'universeSemanticLayout.v1';
export const stageAnchors = Object.freeze({
	upstream: 0.14,
	midstream: 0.5,
	downstream: 0.86,
	unknown: 0.5
});
export const statusOffsets = Object.freeze({
	fact: -0.018,
	candidate: -0.012,
	derived: -0.006,
	disputed: 0,
	retracted: 0.006,
	scenario: 0.012,
	unknown: 0.018
});
const statuses = Object.freeze(Object.keys(statusOffsets));

function stableValue(value) {
	if (Array.isArray(value)) return value.map(stableValue);
	if (value && typeof value === 'object') {
		return Object.fromEntries(Object.keys(value).sort().map((key) => [key, stableValue(value[key])]));
	}
	return value;
}

function stableStringify(value) {
	return JSON.stringify(stableValue(value));
}

function fnv1a64(value) {
	let hash = 0xcbf29ce484222325n;
	for (const character of value) {
		hash ^= BigInt(character.codePointAt(0));
		hash = BigInt.asUintN(64, hash * 0x100000001b3n);
	}
	return hash.toString(16).padStart(16, '0');
}

export function deterministicPayloadHash(value) {
	return `fnv1a64:${fnv1a64(stableStringify(value))}`;
}

function roundLogical(value) {
	return Math.round(value * 1_000_000) / 1_000_000;
}

function stableUnit(nodeId, salt) {
	const digest = fnv1a64(`${salt}:${nodeId}`);
	const integer = Number.parseInt(digest.slice(-8), 16);
	return integer / 0xffffffff;
}

function validateNode(node) {
	if (!node || typeof node.nodeId !== 'string' || !node.nodeId || typeof node.label !== 'string' || !node.label) {
		throw new Error('layout node identity and label are required');
	}
	if (!(node.stage in stageAnchors)) throw new Error(`unsupported layout stage: ${node.stage}`);
	if (!statuses.includes(node.status)) throw new Error(`unsupported layout status: ${node.status}`);
	if (node.validOrder !== null && (!Number.isInteger(node.validOrder) || node.validOrder < 0)) {
		throw new Error('layout validOrder must be null or a non-negative integer');
	}
}

export function compileDeterministicLayout(inputNodes, options = {}) {
	if (!Array.isArray(inputNodes) || inputNodes.length === 0) throw new Error('layout requires nodes');
	const sourceSceneHash = String(options.sourceSceneHash ?? '');
	if (!/^sha256:[0-9a-f]{64}$/.test(sourceSceneHash)) {
		throw new Error('layout requires a source scene SHA-256 hash');
	}
	const nodeIndex = new Map();
	for (const node of inputNodes) {
		validateNode(node);
		if (nodeIndex.has(node.nodeId)) throw new Error(`duplicate layout node: ${node.nodeId}`);
		nodeIndex.set(node.nodeId, Object.freeze({ ...node }));
	}
	const ordered = [...nodeIndex.values()].sort((left, right) => left.nodeId.localeCompare(right.nodeId));
	const knownValidOrders = ordered
		.map((node) => node.validOrder)
		.filter((validOrder) => validOrder !== null);
	const maxValidOrder = Math.max(...knownValidOrders, 1);
	const coordinates = ordered.map((node) => {
		const microX = (stableUnit(node.nodeId, 'x') - 0.5) * 0.032;
		const microY = (stableUnit(node.nodeId, 'y') - 0.5) * 0.022;
		const baseY = node.validOrder === null
			? 0.5
			: 0.1 + (node.validOrder / maxValidOrder) * 0.8;
		return Object.freeze({
			nodeId: node.nodeId,
			label: node.label,
			stage: node.stage,
			status: node.status,
			logicalX: roundLogical(Math.min(0.96, Math.max(0.04, stageAnchors[node.stage] + microX))),
			logicalY: roundLogical(Math.min(0.96, Math.max(0.04, baseY + statusOffsets[node.status] + microY)))
		});
	});
	const receipt = Object.freeze({
		schemaVersion: 'logicalLayoutReceipt.v1',
		layoutVersion,
		sourceSceneHash,
		nodeCount: coordinates.length,
		validTimeKnownCount: knownValidOrders.length,
		validTimeUnknownCount: coordinates.length - knownValidOrders.length,
		xSemantic: 'industryStage',
		ySemantic: 'validOrderOrUnknownLane',
		microOffsetSemantic: 'stableNodeIdentity',
		forceIterationCount: 0,
		fallbackReason: ''
	});
	const logicalPayload = { receipt, coordinates };
	return Object.freeze({
		coordinates: Object.freeze(coordinates),
		receipt,
		logicalHash: deterministicPayloadHash(logicalPayload)
	});
}

export function projectAnchors(layout, viewport) {
	if (!layout || !Array.isArray(layout.coordinates) || !layout.logicalHash) {
		throw new Error('anchor projection requires a compiled layout');
	}
	const width = Number(viewport?.width);
	const height = Number(viewport?.height);
	const dpr = Number(viewport?.dpr);
	if (!(width > 0) || !(height > 0) || !(dpr > 0)) {
		throw new Error('viewport width, height, and DPR must be positive');
	}
	const marginX = Math.min(64, width * 0.08);
	const marginY = Math.min(56, height * 0.08);
	const innerWidth = width - marginX * 2;
	const innerHeight = height - marginY * 2;
	const anchors = layout.coordinates.map((coordinate) => Object.freeze({
		nodeId: coordinate.nodeId,
		x: Math.round((marginX + coordinate.logicalX * innerWidth) * dpr) / dpr,
		y: Math.round((marginY + coordinate.logicalY * innerHeight) * dpr) / dpr
	}));
	const receipt = Object.freeze({
		schemaVersion: 'viewportAnchorReceipt.v1',
		logicalHash: layout.logicalHash,
		width,
		height,
		dpr,
		marginX,
		marginY,
		anchorCount: anchors.length
	});
	return Object.freeze({
		anchors: Object.freeze(anchors),
		receipt,
		anchorHash: deterministicPayloadHash({ receipt, anchors })
	});
}

export function referenceLayoutNodes() {
	const stages = ['upstream', 'midstream', 'downstream', 'unknown'];
	return Object.freeze(Array.from({ length: 20 }, (_, index) => Object.freeze({
		nodeId: `layout-node-${String(index + 1).padStart(2, '0')}`,
		label: `Layout Node ${String(index + 1).padStart(2, '0')}`,
		stage: stages[index % stages.length],
		status: statuses[index % statuses.length],
		validOrder: index % 10
	})));
}

function replayOrder(nodes, replayIndex) {
	const rotated = [...nodes.slice(replayIndex % nodes.length), ...nodes.slice(0, replayIndex % nodes.length)];
	return replayIndex % 2 === 0 ? rotated : rotated.reverse();
}

export function inspectDeterministicLayout(fixtures = null) {
	const sceneFixtures = fixtures ?? [{
		sceneName: 'reference',
		sourceSceneHash: `sha256:${'a'.repeat(64)}`,
		nodes: referenceLayoutNodes()
	}];
	if (!Array.isArray(sceneFixtures) || sceneFixtures.length === 0) {
		throw new Error('layout inspection requires scene fixtures');
	}
	const viewports = Object.freeze([
		Object.freeze({ name: 'desktop', width: 1280, height: 720, dpr: 1 }),
		Object.freeze({ name: 'laptop', width: 1440, height: 900, dpr: 1 }),
		Object.freeze({ name: 'mobile', width: 390, height: 844, dpr: 3 })
	]);
	const sceneReports = sceneFixtures.map((fixture) => {
		const nodes = fixture.nodes;
		const sourceSceneHash = fixture.sourceSceneHash;
		const layouts = Array.from({ length: 20 }, (_, index) => compileDeterministicLayout(
			replayOrder(nodes, index),
			{ sourceSceneHash }
		));
		const expectedHash = layouts[0].logicalHash;
		const logicalHashMatches = layouts.filter((layout) => layout.logicalHash === expectedHash).length;
		let anchorHashMatches = 0;
		for (const viewport of viewports) {
			const expected = projectAnchors(layouts[0], viewport).anchorHash;
			anchorHashMatches += layouts.filter(
				(layout) => projectAnchors(layout, viewport).anchorHash === expected
			).length;
		}
		return Object.freeze({
			sceneName: String(fixture.sceneName ?? ''),
			sourceSceneHash,
			nodeCount: nodes.length,
			validTimeKnownCount: layouts[0].receipt.validTimeKnownCount,
			validTimeUnknownCount: layouts[0].receipt.validTimeUnknownCount,
			replayCount: layouts.length,
			logicalHash: expectedHash,
			logicalHashMatches,
			logicalHashTotal: layouts.length,
			anchorHashMatches,
			anchorHashTotal: layouts.length * viewports.length
		});
	});
	const sum = (key) => sceneReports.reduce((total, report) => total + report[key], 0);
	const logicalHashMatches = sum('logicalHashMatches');
	const logicalHashTotal = sum('logicalHashTotal');
	const anchorHashMatches = sum('anchorHashMatches');
	const anchorHashTotal = sum('anchorHashTotal');
	return Object.freeze({
		schemaVersion: 'deterministicLayoutReport.v1',
		layoutVersion,
		sceneCount: sceneReports.length,
		sceneReports: Object.freeze(sceneReports),
		nodeCount: sum('nodeCount'),
		validTimeKnownCount: sum('validTimeKnownCount'),
		validTimeUnknownCount: sum('validTimeUnknownCount'),
		replayCount: sum('replayCount'),
		replayCountPerScene: 20,
		logicalHash: sceneReports.length === 1 ? sceneReports[0].logicalHash : '',
		logicalHashMatches,
		logicalHashTotal,
		viewportCount: viewports.length,
		anchorHashMatches,
		anchorHashTotal,
		forceIterationCount: 0,
		machineReady: logicalHashMatches === logicalHashTotal
			&& anchorHashMatches === anchorHashTotal
	});
}

export async function inspectLiveDeterministicLayout() {
	const { execFileSync } = await import('node:child_process');
	const fixtureOutput = execFileSync('uv', [
		'run',
		'python',
		'-X',
		'utf8',
		'-m',
		'tests._attempts.dartlabUniverse.visual.liveLayoutFixture',
		'--compact'
	], { encoding: 'utf8' });
	return inspectDeterministicLayout(JSON.parse(fixtureOutput));
}

export async function main() {
	const report = process.argv.includes('--live')
		? await inspectLiveDeterministicLayout()
		: inspectDeterministicLayout();
	process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
	return 0;
}

if (typeof process !== 'undefined' && process.versions?.node) {
	const { pathToFileURL } = await import('node:url');
	if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
		process.exitCode = await main();
	}
}
