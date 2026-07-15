import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import {
	buildRendererFixture,
	coreActions,
	evaluateRendererBakeoff,
	rendererDefinitions
} from './rendererBakeoffProbe.mjs';

function passingReceipt() {
	const measurements = (nodeCount, edgeCount) => rendererDefinitions.map((definition, index) => ({
			rendererId: definition.id,
			mountMs: 10 + index,
			frameP95Ms: 16.7,
			frameP95Fps: 59.88,
			heapUsedAfterBytes: definition.id === 'currentCosmos' ? 80_000_000 : 20_000_000,
			bundleRawBytes: definition.id === 'currentCosmos' ? 311_900 : 10_000 + index,
			taskCount: coreActions.length,
			taskCompletedCount: coreActions.length,
			renderedNodeCount: nodeCount,
			renderedEdgeCount: edgeCount
		}));
	return {
		schemaVersion: 'rendererBakeoffReceipt.v1',
		bundleAudit: {
			builtinPortfolioRawBytes: 17438,
			cosmosPortfolioRawBytes: 328891,
			canvas2dIncrementalDependencyBytes: 0
		},
		fixture: { nodeCount: 500, edgeCount: 1000 },
		measurements: measurements(500, 1000),
		mobileFixture: { nodeCount: 250, edgeCount: 500 },
		mobileMeasurements: measurements(250, 500)
	};
}

test('500 node와 1,000 edge deterministic fixture를 만든다', () => {
	const first = buildRendererFixture();
	const second = buildRendererFixture();
	assert.equal(first.nodes.length, 500);
	assert.equal(first.edges.length, 1000);
	assert.deepEqual(first, second);
	assert.ok(first.edges.every((edge) => edge.source !== edge.target));
});

test('네 renderer 정의는 SVG, current Cosmos, DOM, Canvas 2D를 고정한다', () => {
	assert.deepEqual(rendererDefinitions.map((item) => item.id), [
		'svgReference', 'currentCosmos', 'domReference', 'canvas2dCandidate'
	]);
	const cosmos = rendererDefinitions.find((item) => item.id === 'currentCosmos');
	assert.equal(cosmos.dependency, '@cosmograph/cosmos@1.6.1');
	assert.equal(cosmos.license, 'CC-BY-NC-4.0');
	assert.equal(cosmos.dependencyRawBytes, 311453);
});

test('current Cosmos version과 license는 repository lockfile과 일치한다', async () => {
	const lockUrl = new URL('../../../../package-lock.json', import.meta.url);
	const lock = JSON.parse(await readFile(lockUrl, 'utf8'));
	const locked = lock.packages['node_modules/@cosmograph/cosmos'];
	assert.equal(locked.version, '1.6.1');
	assert.equal(locked.license, 'CC-BY-NC-4.0');
});

test('동등 task와 예산 및 bundle과 heap 개선이 있으면 Canvas 2D를 promote한다', () => {
	const decision = evaluateRendererBakeoff(passingReceipt());
	assert.equal(decision.desktopTaskReadyCount, 4);
	assert.equal(decision.mobileTaskReadyCount, 4);
	assert.equal(decision.desktopPerformanceReadyCount, 4);
	assert.equal(decision.mobilePerformanceReadyCount, 4);
	assert.equal(decision.candidatePromoted, true);
	assert.equal(decision.builtinPortfolioRawBytes, 17438);
	assert.equal(decision.cosmosPortfolioRawBytes, 328891);
	assert.deepEqual(decision.productionPortfolio, ['svgReference', 'canvas2dCandidate', 'domReference']);
	assert.equal(decision.newExternalDependencyRequired, false);
	assert.equal(decision.rendererContractReady, true);
	assert.equal(decision.productionReady, false);
});

test('CC-BY-NC current Cosmos를 production-ready로 오판하지 않는다', () => {
	const decision = evaluateRendererBakeoff(passingReceipt());
	assert.equal(decision.currentCosmosLicenseReady, false);
});

test('task 결손 또는 성능 결손 candidate는 fail closed한다', () => {
	const taskFailure = passingReceipt();
	taskFailure.measurements[3].taskCompletedCount = coreActions.length - 1;
	assert.equal(evaluateRendererBakeoff(taskFailure).candidatePromoted, false);
	const frameFailure = passingReceipt();
	frameFailure.measurements[3].frameP95Fps = 30;
	assert.equal(evaluateRendererBakeoff(frameFailure).candidatePromoted, false);
	const mobileFrameFailure = passingReceipt();
	mobileFrameFailure.mobileMeasurements[3].frameP95Fps = 29;
	assert.equal(evaluateRendererBakeoff(mobileFrameFailure).candidatePromoted, false);
});

test('중복, 불완전, fixture 생략 receipt를 거부한다', () => {
	const duplicate = passingReceipt();
	duplicate.measurements[3].rendererId = 'svgReference';
	assert.throws(() => evaluateRendererBakeoff(duplicate), /duplicate renderer measurement/);
	const incomplete = passingReceipt();
	incomplete.measurements.pop();
	assert.throws(() => evaluateRendererBakeoff(incomplete), /measurement count/);
	const omission = passingReceipt();
	omission.measurements[0].renderedEdgeCount = 999;
	assert.throws(() => evaluateRendererBakeoff(omission), /complete bounded fixture/);
	const mobileOmission = passingReceipt();
	mobileOmission.mobileMeasurements[0].renderedNodeCount = 249;
	assert.throws(() => evaluateRendererBakeoff(mobileOmission), /complete bounded fixture/);
	const missingBundleAudit = passingReceipt();
	delete missingBundleAudit.bundleAudit;
	assert.throws(() => evaluateRendererBakeoff(missingBundleAudit), /bundle audit/);
});
