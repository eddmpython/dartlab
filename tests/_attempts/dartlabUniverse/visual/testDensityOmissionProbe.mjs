import assert from 'node:assert/strict';
import test from 'node:test';

import {
	buildDensityFixture,
	compileDensityProjection,
	densityTargets,
	inspectDensityOmission
} from './densityOmissionProbe.mjs';

test('250, 500, 1,000 node fixture와 3배 edge를 만든다', () => {
	for (const size of [250, 500, 1000]) {
		const fixture = buildDensityFixture(size);
		assert.equal(fixture.nodes.length, size);
		assert.equal(fixture.edges.length, size * 3);
		assert.equal(new Set(fixture.nodes.map((node) => node.nodeId)).size, size);
	}
});

test('desktop과 mobile active mark 상한을 넘지 않는다', () => {
	for (const size of [250, 500, 1000]) {
		for (const targetName of Object.keys(densityTargets)) {
			const projection = compileDensityProjection(buildDensityFixture(size), targetName);
			const target = densityTargets[targetName];
			assert.ok(projection.activeNodes.length <= target.nodeBudget);
			assert.ok(projection.activeEdges.length <= target.edgeBudget);
			assert.ok(projection.labels.length <= target.labelBudget);
		}
	}
});

test('1,000 node는 desktop 500, mobile 250으로 lower LOD를 적용한다', () => {
	const fixture = buildDensityFixture(1000);
	const desktop = compileDensityProjection(fixture, 'desktop');
	const mobile = compileDensityProjection(fixture, 'mobile');
	assert.equal(desktop.receipt.activeNodeCount, 500);
	assert.equal(desktop.receipt.omittedNodeCount, 500);
	assert.equal(mobile.receipt.activeNodeCount, 250);
	assert.equal(mobile.receipt.omittedNodeCount, 750);
	assert.equal(desktop.receipt.lowerLodApplied, true);
	assert.equal(mobile.receipt.lowerLodApplied, true);
});

test('node와 edge와 label 생략 수를 reason으로 100% 설명한다', () => {
	for (const size of [250, 500, 1000]) {
		for (const targetName of Object.keys(densityTargets)) {
			const receipt = compileDensityProjection(buildDensityFixture(size), targetName).receipt;
			assert.equal(receipt.activeNodeCount + receipt.omittedNodeCount, receipt.inputNodeCount);
			assert.equal(receipt.activeEdgeCount + receipt.omittedEdgeCount, receipt.inputEdgeCount);
			assert.equal(receipt.nodeOmissionReasons.activeNodeBudget, receipt.omittedNodeCount);
			assert.equal(
				receipt.edgeOmissionReasons.endpointOmitted + receipt.edgeOmissionReasons.activeEdgeBudget,
				receipt.omittedEdgeCount
			);
			assert.equal(receipt.labelReceipt.visibleCount + receipt.labelReceipt.omittedCount, receipt.activeNodeCount);
			assert.deepEqual(receipt.receiptCoverage, { node: 1, edge: 1, label: 1 });
		}
	}
});

test('aggregate receipt가 omitted member와 상태 및 변화 요약을 보존한다', () => {
	const receipt = compileDensityProjection(buildDensityFixture(1000), 'mobile').receipt;
	const aggregate = receipt.aggregateReceipt;
	assert.equal(aggregate.memberCount, 750);
	assert.equal(aggregate.omittedCount, 750);
	assert.equal(Object.values(aggregate.statusCounts).reduce((sum, value) => sum + value, 0), 750);
	assert.ok(aggregate.coverage > 0 && aggregate.coverage < 1);
	assert.ok(aggregate.quantiles.p25 <= aggregate.quantiles.p50);
	assert.ok(aggregate.quantiles.p50 <= aggregate.quantiles.p75);
	assert.equal(aggregate.topChanges.length, 5);
});

test('visible label rectangle의 pair collision은 2% 이하이다', () => {
	const report = inspectDensityOmission();
	assert.ok(report.maximumCollisionRate <= 0.02);
	for (const item of report.cases) assert.equal(item.labelCollisionRate, 0);
});

test('입력 순서를 뒤집어도 여섯 receipt hash가 같다', () => {
	const report = inspectDensityOmission();
	assert.equal(report.repeatHashMatches, 6);
	assert.equal(report.caseCount, 6);
	assert.equal(report.machineReady, true);
});

test('지원하지 않는 size, target, dangling edge를 fail closed한다', () => {
	assert.throws(() => buildDensityFixture(251), /unsupported density fixture size/);
	const fixture = buildDensityFixture(250);
	assert.throws(() => compileDensityProjection(fixture, 'tablet'), /unsupported density target/);
	assert.throws(() => compileDensityProjection({
		...fixture,
		edges: [{ edgeId: 'bad', sourceId: fixture.nodes[0].nodeId, targetId: 'missing', priority: 1 }]
	}, 'desktop'), /edge endpoint is missing/);
});
