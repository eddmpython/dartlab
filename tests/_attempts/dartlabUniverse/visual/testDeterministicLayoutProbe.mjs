import assert from 'node:assert/strict';
import test from 'node:test';

import {
	compileDeterministicLayout,
	inspectDeterministicLayout,
	projectAnchors,
	referenceLayoutNodes
} from './deterministicLayoutProbe.mjs';

const sourceSceneHash = `sha256:${'a'.repeat(64)}`;

test('20 replay의 logical coordinate hash가 입력 순서와 무관하다', () => {
	const nodes = referenceLayoutNodes();
	const expected = compileDeterministicLayout(nodes, { sourceSceneHash }).logicalHash;
	for (let index = 0; index < 20; index += 1) {
		const ordered = index % 2 === 0 ? [...nodes].reverse() : [...nodes.slice(index), ...nodes.slice(0, index)];
		assert.equal(compileDeterministicLayout(ordered, { sourceSceneHash }).logicalHash, expected);
	}
});

test('stage semantic anchor가 upstream에서 downstream 순서를 보존한다', () => {
	const layout = compileDeterministicLayout(referenceLayoutNodes(), { sourceSceneHash });
	const groups = Map.groupBy(layout.coordinates, (coordinate) => coordinate.stage);
	const average = (stage) => groups.get(stage).reduce((sum, item) => sum + item.logicalX, 0) / groups.get(stage).length;
	assert.ok(average('upstream') < average('midstream'));
	assert.ok(average('midstream') < average('downstream'));
});

test('logical coordinate는 0과 1 사이의 6자리 정밀도를 가진다', () => {
	const layout = compileDeterministicLayout(referenceLayoutNodes(), { sourceSceneHash });
	for (const coordinate of layout.coordinates) {
		assert.ok(coordinate.logicalX >= 0 && coordinate.logicalX <= 1);
		assert.ok(coordinate.logicalY >= 0 && coordinate.logicalY <= 1);
		assert.equal(Number(coordinate.logicalX.toFixed(6)), coordinate.logicalX);
		assert.equal(Number(coordinate.logicalY.toFixed(6)), coordinate.logicalY);
	}
});

test('viewport anchor는 DPR grid에 정렬된다', () => {
	const layout = compileDeterministicLayout(referenceLayoutNodes(), { sourceSceneHash });
	const projection = projectAnchors(layout, { width: 390, height: 844, dpr: 3 });
	for (const anchor of projection.anchors) {
		assert.ok(Math.abs(anchor.x * 3 - Math.round(anchor.x * 3)) < 1e-9);
		assert.ok(Math.abs(anchor.y * 3 - Math.round(anchor.y * 3)) < 1e-9);
	}
});

test('3 viewport와 20 replay의 anchor hash가 모두 일치한다', () => {
	const report = inspectDeterministicLayout();
	assert.equal(report.logicalHashMatches, report.logicalHashTotal);
	assert.equal(report.anchorHashMatches, report.anchorHashTotal);
	assert.equal(report.anchorHashTotal, 60);
	assert.equal(report.machineReady, true);
});

test('force iteration 없이 semantic receipt를 만든다', () => {
	const layout = compileDeterministicLayout(referenceLayoutNodes(), { sourceSceneHash });
	assert.equal(layout.receipt.xSemantic, 'industryStage');
	assert.equal(layout.receipt.ySemantic, 'validOrderOrUnknownLane');
	assert.equal(layout.receipt.validTimeKnownCount, 20);
	assert.equal(layout.receipt.validTimeUnknownCount, 0);
	assert.equal(layout.receipt.forceIterationCount, 0);
	assert.equal(layout.receipt.fallbackReason, '');
});

test('valid time 결손을 임의 순서가 아닌 unknown lane으로 보존한다', () => {
	const nodes = referenceLayoutNodes().map((node) => ({ ...node, validOrder: null }));
	const layout = compileDeterministicLayout(nodes, { sourceSceneHash });
	assert.equal(layout.receipt.validTimeKnownCount, 0);
	assert.equal(layout.receipt.validTimeUnknownCount, nodes.length);
	for (const coordinate of layout.coordinates) {
		assert.ok(coordinate.logicalY >= 0.47 && coordinate.logicalY <= 0.53);
	}
});

test('여러 scene의 replay와 viewport hash를 scene별로 집계한다', () => {
	const fixtures = ['a', 'b', 'c'].map((suffix, index) => ({
		sceneName: `scene-${suffix}`,
		sourceSceneHash: `sha256:${suffix.repeat(64)}`,
		nodes: referenceLayoutNodes().slice(0, 5 + index)
	}));
	const report = inspectDeterministicLayout(fixtures);
	assert.equal(report.sceneCount, 3);
	assert.equal(report.nodeCount, 18);
	assert.equal(report.logicalHashMatches, 60);
	assert.equal(report.logicalHashTotal, 60);
	assert.equal(report.anchorHashMatches, 180);
	assert.equal(report.anchorHashTotal, 180);
	assert.equal(report.machineReady, true);
});

test('다른 source scene은 logical identity를 바꾼다', () => {
	const nodes = referenceLayoutNodes();
	const first = compileDeterministicLayout(nodes, { sourceSceneHash });
	const second = compileDeterministicLayout(nodes, { sourceSceneHash: `sha256:${'b'.repeat(64)}` });
	assert.notEqual(first.logicalHash, second.logicalHash);
});

test('duplicate node와 malformed viewport를 fail closed한다', () => {
	const nodes = referenceLayoutNodes();
	assert.throws(
		() => compileDeterministicLayout([...nodes, nodes[0]], { sourceSceneHash }),
		/duplicate layout node/
	);
	const layout = compileDeterministicLayout(nodes, { sourceSceneHash });
	assert.throws(() => projectAnchors(layout, { width: 0, height: 720, dpr: 1 }), /must be positive/);
});
