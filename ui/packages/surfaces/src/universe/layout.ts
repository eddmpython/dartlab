import type { UniverseStage, UniverseVisualStatus } from '@dartlab/ui-contracts';

export const UNIVERSE_LAYOUT_VERSION = 'universeSemanticLayout.v1' as const;
export const STAGE_ANCHORS: Readonly<Record<UniverseStage, number>> = {
	upstream: 0.14,
	midstream: 0.5,
	downstream: 0.86,
	unknown: 0.5
};
export const STATUS_OFFSETS: Readonly<Record<UniverseVisualStatus, number>> = {
	fact: -0.018,
	candidate: -0.012,
	derived: -0.006,
	disputed: 0,
	retracted: 0.006,
	scenario: 0.012,
	unknown: 0.018
};

export interface UniverseLayoutNode {
	nodeId: string;
	label: string;
	stage: UniverseStage;
	status: UniverseVisualStatus;
	validOrder: number | null;
}


export interface UniverseLogicalCoordinate {
	nodeId: string;
	label: string;
	stage: UniverseStage;
	status: UniverseVisualStatus;
	logicalX: number;
	logicalY: number;
}

export interface UniverseLogicalLayout {
	coordinates: readonly UniverseLogicalCoordinate[];
	receipt: Readonly<Record<string, unknown>>;
	logicalHash: string;
}

export interface UniverseViewport {
	width: number;
	height: number;
	dpr: number;
}

export interface UniverseAnchor {
	nodeId: string;
	x: number;
	y: number;
}

export interface UniverseAnchorLayout {
	anchors: readonly UniverseAnchor[];
	receipt: Readonly<Record<string, unknown>>;
	anchorHash: string;
}

function stableValue(value: unknown): unknown {
	if (Array.isArray(value)) return value.map(stableValue);
	if (value && typeof value === 'object') {
		const row = value as Record<string, unknown>;
		return Object.fromEntries(Object.keys(row).sort().map((key) => [key, stableValue(row[key])]));
	}
	return value;
}

function fnv1a64(value: string): string {
	let hash = 0xcbf29ce484222325n;
	for (const character of value) {
		hash ^= BigInt(character.codePointAt(0) ?? 0);
		hash = BigInt.asUintN(64, hash * 0x100000001b3n);
	}
	return hash.toString(16).padStart(16, '0');
}

export function deterministicPayloadHash(value: unknown): string {
	return `fnv1a64:${fnv1a64(JSON.stringify(stableValue(value)))}`;
}

function stableUnit(nodeId: string, salt: string): number {
	const digest = fnv1a64(`${salt}:${nodeId}`);
	return Number.parseInt(digest.slice(-8), 16) / 0xffffffff;
}

function roundLogical(value: number): number {
	return Math.round(value * 1_000_000) / 1_000_000;
}

export function compileDeterministicLayout(inputNodes: readonly UniverseLayoutNode[], sourceSceneHash: string): UniverseLogicalLayout {
	if (inputNodes.length === 0) throw new Error('Universe layout requires nodes');
	if (!/^sha256:[0-9a-f]{64}$/.test(sourceSceneHash)) throw new Error('Universe layout requires a source scene SHA-256 hash');
	const nodeIndex = new Map<string, UniverseLayoutNode>();
	for (const node of inputNodes) {
		if (!node.nodeId || !node.label || !(node.stage in STAGE_ANCHORS) || !(node.status in STATUS_OFFSETS)) {
			throw new Error('Universe layout node is invalid');
		}
		if (node.validOrder !== null && (!Number.isInteger(node.validOrder) || node.validOrder < 0)) {
			throw new Error('Universe layout validOrder is invalid');
		}
		if (nodeIndex.has(node.nodeId)) throw new Error(`Universe duplicate layout node: ${node.nodeId}`);
		nodeIndex.set(node.nodeId, Object.freeze({ ...node }));
	}
	const ordered = [...nodeIndex.values()].sort((left, right) => left.nodeId.localeCompare(right.nodeId));
	const knownValidOrders = ordered.map((node) => node.validOrder).filter((value): value is number => value !== null);
	const maxValidOrder = Math.max(...knownValidOrders, 1);
	const coordinates = ordered.map((node): UniverseLogicalCoordinate => {
		const microX = (stableUnit(node.nodeId, 'x') - 0.5) * 0.032;
		const microY = (stableUnit(node.nodeId, 'y') - 0.5) * 0.022;
		const baseY = node.validOrder === null ? 0.5 : 0.1 + (node.validOrder / maxValidOrder) * 0.8;
		return Object.freeze({
			nodeId: node.nodeId,
			label: node.label,
			stage: node.stage,
			status: node.status,
			logicalX: roundLogical(Math.min(0.96, Math.max(0.04, STAGE_ANCHORS[node.stage] + microX))),
			logicalY: roundLogical(Math.min(0.96, Math.max(0.04, baseY + STATUS_OFFSETS[node.status] + microY)))
		});
	});
	const receipt = Object.freeze({
		schemaVersion: 'logicalLayoutReceipt.v1',
		layoutVersion: UNIVERSE_LAYOUT_VERSION,
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
	return Object.freeze({ coordinates: Object.freeze(coordinates), receipt, logicalHash: deterministicPayloadHash({ receipt, coordinates }) });
}

export function projectAnchors(layout: UniverseLogicalLayout, viewport: UniverseViewport): UniverseAnchorLayout {
	if (!(viewport.width > 0) || !(viewport.height > 0) || !(viewport.dpr > 0)) throw new Error('Universe viewport is invalid');
	const marginX = Math.min(64, viewport.width * 0.08);
	const marginY = Math.min(56, viewport.height * 0.08);
	const innerWidth = viewport.width - marginX * 2;
	const innerHeight = viewport.height - marginY * 2;
	const anchors = layout.coordinates.map((coordinate) => Object.freeze({
		nodeId: coordinate.nodeId,
		x: Math.round((marginX + coordinate.logicalX * innerWidth) * viewport.dpr) / viewport.dpr,
		y: Math.round((marginY + coordinate.logicalY * innerHeight) * viewport.dpr) / viewport.dpr
	}));
	const receipt = Object.freeze({
		schemaVersion: 'viewportAnchorReceipt.v1', logicalHash: layout.logicalHash,
		width: viewport.width, height: viewport.height, dpr: viewport.dpr, marginX, marginY, anchorCount: anchors.length
	});
	return Object.freeze({ anchors: Object.freeze(anchors), receipt, anchorHash: deterministicPayloadHash({ receipt, anchors }) });
}
