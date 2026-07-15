import assert from 'node:assert/strict';
import test from 'node:test';

import {
	accessibilityProfiles,
	compileAccessibilitySurface,
	compileProfileExecution,
	coreActions,
	inspectAccessibilityEquivalence,
	renderAccessibilitySurface
} from './accessibilityEquivalenceProbe.mjs';

test('spatial과 table은 같은 여섯 command를 같은 순서로 제공한다', () => {
	const spatial = compileAccessibilitySurface('spatial');
	const table = compileAccessibilitySurface('table');
	assert.equal(spatial.controls.length, 6);
	assert.equal(table.controls.length, 6);
	assert.deepEqual(spatial.commands, table.commands);
	assert.deepEqual(spatial.commands, coreActions.map((action) => action.command));
});

test('모든 action은 surface별 unique focus ID와 native keyboard control을 가진다', () => {
	for (const surfaceName of ['spatial', 'table']) {
		const surface = compileAccessibilitySurface(surfaceName);
		assert.equal(new Set(surface.controls.map((control) => control.focusId)).size, 6);
		assert.ok(surface.controls.every((control) => control.keyboardNative));
	}
});

test('모든 action은 screen reader summary와 polite live region을 가진다', () => {
	for (const surfaceName of ['spatial', 'table']) {
		const surface = compileAccessibilitySurface(surfaceName);
		assert.ok(surface.controls.every((control) => control.label && control.screenReaderSummary));
		assert.deepEqual(surface.liveRegion, { role: 'status', ariaLive: 'polite', atomic: true });
	}
});

test('relation table은 caption, row header, 동일 control을 렌더링한다', () => {
	const html = renderAccessibilitySurface('table');
	assert.match(html, /<caption>/);
	assert.equal((html.match(/<th scope="row">/g) ?? []).length, 6);
	for (const action of coreActions) assert.match(html, new RegExp(`data-action="${action.id}"`));
});

test('spatial DOM은 list semantics와 동일 control을 렌더링한다', () => {
	const html = renderAccessibilitySurface('spatial');
	assert.match(html, /role="list"/);
	assert.equal((html.match(/role="listitem"/g) ?? []).length, 6);
	for (const action of coreActions) assert.match(html, new RegExp(`data-action="${action.id}"`));
});

test('여섯 accessibility profile에서 핵심 task 36개를 모두 완료한다', () => {
	const executions = Object.keys(accessibilityProfiles).map(compileProfileExecution);
	assert.equal(executions.length, 6);
	assert.equal(executions.reduce((sum, item) => sum + item.taskCount, 0), 36);
	assert.equal(executions.reduce((sum, item) => sum + item.completedTaskCount, 0), 36);
	assert.ok(executions.every((item) => item.failedTaskCount === 0));
});

test('mobile low GPU는 table fallback이며 spatial-only action이 없다', () => {
	const execution = compileProfileExecution('mobileLowGpu');
	assert.equal(execution.surface, 'table');
	assert.equal(execution.lowGpuFallbackApplied, true);
	assert.equal(execution.spatialOnlyActionCount, 0);
});

test('reduced motion profile은 motion duration을 0으로 강제한다', () => {
	const execution = compileProfileExecution('reducedMotion');
	assert.equal(execution.motionDurationMs, 0);
	assert.equal(execution.reducedMotionApplied, true);
});

test('high contrast와 200% zoom profile 계약이 유지된다', () => {
	const contrast = compileProfileExecution('highContrast');
	const zoom = compileProfileExecution('zoom200');
	assert.equal(contrast.highContrastNonColorCoverage, 6);
	assert.equal(zoom.zoomReflowContract, true);
});

test('전체 accessibility equivalence report가 machine gate를 통과한다', () => {
	const report = inspectAccessibilityEquivalence();
	assert.equal(report.commandParity, true);
	assert.equal(report.keyboardNativeCoverage, 12);
	assert.equal(report.screenReaderSummaryCoverage, 12);
	assert.equal(report.completedTaskCount, 36);
	assert.equal(report.taskCount, 36);
	assert.equal(report.profileReadyCount, 6);
	assert.equal(report.machineReady, true);
});

test('지원하지 않는 surface와 profile을 fail closed한다', () => {
	assert.throws(() => compileAccessibilitySurface('canvasOnly'), /unsupported accessibility surface/);
	assert.throws(() => compileProfileExecution('unknown'), /unsupported accessibility profile/);
});
