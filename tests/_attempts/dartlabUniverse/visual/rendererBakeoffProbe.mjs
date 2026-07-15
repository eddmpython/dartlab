import { coreActions } from './accessibilityEquivalenceProbe.mjs';

export { coreActions };

export const rendererBudgets = Object.freeze({
	desktopMinimumFps: 45,
	mobileMinimumFps: 30,
	desktopMaximumHeapBytes: 512 * 1024 * 1024,
	mobileMaximumHeapBytes: 250 * 1024 * 1024,
	requiredTaskCompletionRate: 1
});

export const rendererDefinitions = Object.freeze([
	Object.freeze({ id: 'svgReference', surface: 'spatial', kind: 'reference', dependency: null }),
	Object.freeze({
		id: 'currentCosmos',
		surface: 'spatial',
		kind: 'incumbent',
		dependency: '@cosmograph/cosmos@1.6.1',
		license: 'CC-BY-NC-4.0',
		dependencyRawBytes: 311453,
		dependencyGzipBytes: 91863
	}),
	Object.freeze({ id: 'domReference', surface: 'table', kind: 'reference', dependency: null }),
	Object.freeze({ id: 'canvas2dCandidate', surface: 'spatial', kind: 'candidate', dependency: null })
]);

function requireInteger(value, label, minimum = 1) {
	if (!Number.isInteger(value) || value < minimum) throw new Error(`${label} must be an integer >= ${minimum}`);
}

export function buildRendererFixture({ nodeCount = 500, edgeCount = 1000 } = {}) {
	requireInteger(nodeCount, 'nodeCount', 2);
	requireInteger(edgeCount, 'edgeCount');
	const goldenAngle = Math.PI * (3 - Math.sqrt(5));
	const nodes = Array.from({ length: nodeCount }, (_, index) => {
		const radius = Math.sqrt((index + 0.5) / nodeCount) * 0.46;
		const angle = index * goldenAngle;
		return Object.freeze({
			id: `node-${String(index + 1).padStart(4, '0')}`,
			label: `회사 ${index + 1}`,
			x: Number((0.5 + Math.cos(angle) * radius).toFixed(6)),
			y: Number((0.5 + Math.sin(angle) * radius).toFixed(6)),
			status: index % 7
		});
	});
	const edges = Array.from({ length: edgeCount }, (_, index) => {
		const sourceIndex = index % nodeCount;
		let targetIndex = (sourceIndex * 17 + Math.floor(index / nodeCount) * 29 + 1) % nodeCount;
		if (targetIndex === sourceIndex) targetIndex = (targetIndex + 1) % nodeCount;
		return Object.freeze({
			id: `edge-${String(index + 1).padStart(5, '0')}`,
			source: nodes[sourceIndex].id,
			target: nodes[targetIndex].id
		});
	});
	return Object.freeze({
		schemaVersion: 'rendererFixture.v1',
		nodeCount,
		edgeCount,
		nodes: Object.freeze(nodes),
		edges: Object.freeze(edges)
	});
}

function validateMeasurement(measurement, fixture) {
	const definition = rendererDefinitions.find((item) => item.id === measurement?.rendererId);
	if (!definition) throw new Error(`unsupported renderer measurement: ${measurement?.rendererId}`);
	for (const field of ['mountMs', 'frameP95Ms', 'frameP95Fps', 'heapUsedAfterBytes', 'bundleRawBytes']) {
		if (!Number.isFinite(measurement[field]) || measurement[field] < 0) {
			throw new Error(`${measurement.rendererId}.${field} must be a non-negative finite number`);
		}
	}
	requireInteger(measurement.taskCount, `${measurement.rendererId}.taskCount`);
	requireInteger(measurement.taskCompletedCount, `${measurement.rendererId}.taskCompletedCount`, 0);
	if (measurement.taskCompletedCount > measurement.taskCount) throw new Error(`${measurement.rendererId} completed too many tasks`);
	if (measurement.renderedNodeCount !== fixture.nodeCount || measurement.renderedEdgeCount !== fixture.edgeCount) {
		throw new Error(`${measurement.rendererId} did not render the complete bounded fixture`);
	}
	return definition;
}

export function evaluateRendererBakeoff(report) {
	if (!report || report.schemaVersion !== 'rendererBakeoffReceipt.v1') throw new Error('invalid renderer bakeoff report');
	if (!report.bundleAudit || report.bundleAudit.builtinPortfolioRawBytes < 1
		|| report.bundleAudit.cosmosPortfolioRawBytes < 1) throw new Error('invalid renderer bundle audit');
	const fixture = buildRendererFixture(report.fixture);
	const mobileFixture = buildRendererFixture(report.mobileFixture);
	if (!Array.isArray(report.measurements) || report.measurements.length !== rendererDefinitions.length) {
		throw new Error(`renderer measurement count must be ${rendererDefinitions.length}`);
	}
	if (!Array.isArray(report.mobileMeasurements) || report.mobileMeasurements.length !== rendererDefinitions.length) {
		throw new Error(`mobile renderer measurement count must be ${rendererDefinitions.length}`);
	}
	const byId = new Map();
	for (const measurement of report.measurements) {
		const definition = validateMeasurement(measurement, fixture);
		if (byId.has(definition.id)) throw new Error(`duplicate renderer measurement: ${definition.id}`);
		byId.set(definition.id, Object.freeze({ ...measurement, definition }));
	}
	const ordered = rendererDefinitions.map((definition) => byId.get(definition.id));
	if (ordered.some((measurement) => !measurement)) throw new Error('renderer measurement set is incomplete');
	const mobileById = new Map();
	for (const measurement of report.mobileMeasurements) {
		const definition = validateMeasurement(measurement, mobileFixture);
		if (mobileById.has(definition.id)) throw new Error(`duplicate mobile renderer measurement: ${definition.id}`);
		mobileById.set(definition.id, Object.freeze({ ...measurement, definition }));
	}
	const mobileOrdered = rendererDefinitions.map((definition) => mobileById.get(definition.id));
	if (mobileOrdered.some((measurement) => !measurement)) throw new Error('mobile renderer measurement set is incomplete');
	const desktopTaskReadyCount = ordered.filter((measurement) =>
		measurement.taskCompletedCount === coreActions.length && measurement.taskCount === coreActions.length
	).length;
	const mobileTaskReadyCount = mobileOrdered.filter((measurement) =>
		measurement.taskCompletedCount === coreActions.length && measurement.taskCount === coreActions.length
	).length;
	const desktopPerformanceReadyCount = ordered.filter((measurement) =>
		measurement.frameP95Fps >= rendererBudgets.desktopMinimumFps
		&& measurement.heapUsedAfterBytes <= rendererBudgets.desktopMaximumHeapBytes
	).length;
	const mobilePerformanceReadyCount = mobileOrdered.filter((measurement) =>
		measurement.frameP95Fps >= rendererBudgets.mobileMinimumFps
		&& measurement.heapUsedAfterBytes <= rendererBudgets.mobileMaximumHeapBytes
	).length;
	const cosmos = byId.get('currentCosmos');
	const canvas = byId.get('canvas2dCandidate');
	const mobileCosmos = mobileById.get('currentCosmos');
	const mobileCanvas = mobileById.get('canvas2dCandidate');
	const canvasBundleImprovement = report.bundleAudit.canvas2dIncrementalDependencyBytes === 0
		&& report.bundleAudit.builtinPortfolioRawBytes < report.bundleAudit.cosmosPortfolioRawBytes;
	const canvasHeapImprovement = canvas.heapUsedAfterBytes < cosmos.heapUsedAfterBytes
		&& mobileCanvas.heapUsedAfterBytes < mobileCosmos.heapUsedAfterBytes;
	const canvasTaskAndBudgetReady = canvas.taskCompletedCount === coreActions.length
		&& canvas.frameP95Fps >= rendererBudgets.desktopMinimumFps
		&& canvas.heapUsedAfterBytes <= rendererBudgets.desktopMaximumHeapBytes
		&& mobileCanvas.taskCompletedCount === coreActions.length
		&& mobileCanvas.frameP95Fps >= rendererBudgets.mobileMinimumFps
		&& mobileCanvas.heapUsedAfterBytes <= rendererBudgets.mobileMaximumHeapBytes;
	const currentCosmosLicenseReady = cosmos.definition.license !== 'CC-BY-NC-4.0';
	const candidatePromoted = canvasTaskAndBudgetReady && canvasBundleImprovement && canvasHeapImprovement;
	return Object.freeze({
		schemaVersion: 'rendererBakeoffDecision.v1',
		fixtureNodeCount: fixture.nodeCount,
		fixtureEdgeCount: fixture.edgeCount,
		mobileFixtureNodeCount: mobileFixture.nodeCount,
		mobileFixtureEdgeCount: mobileFixture.edgeCount,
		rendererCount: ordered.length,
		desktopTaskReadyCount,
		mobileTaskReadyCount,
		desktopPerformanceReadyCount,
		mobilePerformanceReadyCount,
		canvasBundleImprovement,
		builtinPortfolioRawBytes: report.bundleAudit.builtinPortfolioRawBytes,
		cosmosPortfolioRawBytes: report.bundleAudit.cosmosPortfolioRawBytes,
		canvasHeapImprovement,
		candidatePromoted,
		currentCosmosLicenseReady,
		newExternalDependencyRequired: false,
		productionPortfolio: candidatePromoted
			? Object.freeze(['svgReference', 'canvas2dCandidate', 'domReference'])
			: Object.freeze(['svgReference', 'domReference']),
		rendererContractReady: desktopTaskReadyCount === rendererDefinitions.length
			&& mobileTaskReadyCount === rendererDefinitions.length
			&& candidatePromoted,
		productionReady: false
	});
}

async function runCli() {
	const { readFile } = await import('node:fs/promises');
	const { fileURLToPath } = await import('node:url');
	const receiptUrl = new URL('./rendererBakeoffReceipt.json', import.meta.url);
	const receipt = JSON.parse(await readFile(fileURLToPath(receiptUrl), 'utf8'));
	process.stdout.write(`${JSON.stringify({ receipt, decision: evaluateRendererBakeoff(receipt) }, null, 2)}\n`);
}

const isNode = typeof process !== 'undefined' && Boolean(process.versions?.node);
if (isNode) {
	const { pathToFileURL } = await import('node:url');
	if (import.meta.url === pathToFileURL(process.argv[1]).href) await runCli();
}
