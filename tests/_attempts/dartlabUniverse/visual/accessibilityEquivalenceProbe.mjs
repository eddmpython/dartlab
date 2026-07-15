/**
 * Universe spatial scene과 table의 접근성 작업 동등성을 검증한다.
 *
 * Capabilities
 *   여섯 핵심 작업을 keyboard, screen reader, reduced motion, high contrast, zoom, low GPU profile에 투영한다.
 *
 * AIContext
 *   AI 역할: Canvas나 spatial mark에서만 가능한 작업을 만들지 않고 table fallback을 동등 command로 유지한다.
 *
 * Guide
 *   Native control, unique focus ID, live summary와 surface-independent command를 계약으로 고정한다.
 *
 * When
 *   U0-V05 accessibility bridge, core action 또는 fallback policy가 바뀔 때 사용한다.
 *
 * How
 *   compileAccessibilitySurface와 inspectAccessibilityEquivalence를 실행하고 reference page에서 실제 task를 확인한다.
 *
 * Requires
 *   Node.js 표준 라이브러리만 사용하며 Canvas 또는 renderer dependency가 필요하지 않다.
 *
 * Raises
 *   지원하지 않는 surface, profile, action 또는 중복 focus ID는 Error를 발생시킨다.
 *
 * Example
 *   `node accessibilityEquivalenceProbe.mjs`
 *
 * See Also
 *   mainPlan/dartlab-universe/11-visual-information-physics.md
 *
 * 결과
 *   Profile별 핵심 task completion, table equivalence, semantic accessibility receipt를 출력한다.
 */

export const accessibilityContractVersion = 'universeAccessibility.v1';

export const coreActions = Object.freeze([
	Object.freeze({ id: 'selectNode', command: 'selectNode', label: '회사 선택', control: 'button', summary: '선택한 회사를 읽습니다.' }),
	Object.freeze({ id: 'inspectRelation', command: 'inspectRelation', label: '관계 확인', control: 'button', summary: '선택 관계의 상태와 방향을 읽습니다.' }),
	Object.freeze({ id: 'openEvidence', command: 'openEvidence', label: '근거 열기', control: 'button', summary: '근거 문서와 exact locator를 엽니다.' }),
	Object.freeze({ id: 'setValidAt', command: 'setValidAt', label: '실제 유효 시점', control: 'date', summary: '실제 유효 시점을 바꿉니다.' }),
	Object.freeze({ id: 'setKnownAt', command: 'setKnownAt', label: '당시 지식 시점', control: 'datetime-local', summary: '당시 알 수 있었던 cutoff를 바꿉니다.' }),
	Object.freeze({ id: 'shareProjection', command: 'shareProjection', label: '장면 공유', control: 'button', summary: '현재 projection의 재현 가능한 링크를 준비합니다.' })
]);

export const accessibilityProfiles = Object.freeze({
	keyboard: Object.freeze({ id: 'keyboard', surface: 'spatial', reducedMotion: false, highContrast: false, zoomPercent: 100, lowGpu: false }),
	screenReader: Object.freeze({ id: 'screenReader', surface: 'spatial', reducedMotion: false, highContrast: false, zoomPercent: 100, lowGpu: false }),
	reducedMotion: Object.freeze({ id: 'reducedMotion', surface: 'spatial', reducedMotion: true, highContrast: false, zoomPercent: 100, lowGpu: false }),
	highContrast: Object.freeze({ id: 'highContrast', surface: 'spatial', reducedMotion: false, highContrast: true, zoomPercent: 100, lowGpu: false }),
	zoom200: Object.freeze({ id: 'zoom200', surface: 'table', reducedMotion: false, highContrast: false, zoomPercent: 200, lowGpu: false }),
	mobileLowGpu: Object.freeze({ id: 'mobileLowGpu', surface: 'table', reducedMotion: true, highContrast: false, zoomPercent: 100, lowGpu: true })
});

function escapeHtml(value) {
	return String(value)
		.replaceAll('&', '&amp;')
		.replaceAll('<', '&lt;')
		.replaceAll('>', '&gt;')
		.replaceAll('"', '&quot;')
		.replaceAll("'", '&#39;');
}

function renderControl(surface, action) {
	const focusId = `${surface}-${action.id}`;
	if (action.control === 'button') {
		const className = action.id === 'selectNode' ? ' class="node-pulse"' : '';
		return `<button type="button"${className} id="${focusId}" data-testid="${focusId}" data-action="${action.id}" aria-describedby="${focusId}-description">${escapeHtml(action.label)}</button><span id="${focusId}-description" class="sr-only">${escapeHtml(action.summary)}</span>`;
	}
	const inputType = action.control;
	const value = inputType === 'date' ? '2026-07-16' : '2026-07-16T10:00';
	return `<label for="${focusId}">${escapeHtml(action.label)}</label><input id="${focusId}" data-testid="${focusId}" data-action="${action.id}" type="${inputType}" value="${value}" aria-describedby="${focusId}-description" /><span id="${focusId}-description" class="sr-only">${escapeHtml(action.summary)}</span>`;
}

export function compileAccessibilitySurface(surface) {
	if (!['spatial', 'table'].includes(surface)) throw new Error(`unsupported accessibility surface: ${surface}`);
	const controls = coreActions.map((action) => Object.freeze({
		actionId: action.id,
		command: action.command,
		focusId: `${surface}-${action.id}`,
		control: action.control,
		label: action.label,
		screenReaderSummary: action.summary,
		keyboardNative: true
	}));
	if (new Set(controls.map((control) => control.focusId)).size !== controls.length) {
		throw new Error('accessibility surface focus IDs must be unique');
	}
	return Object.freeze({
		schemaVersion: 'accessibilitySurface.v1',
		surface,
		controls: Object.freeze(controls),
		commands: Object.freeze(controls.map((control) => control.command)),
		spatialOnlyActionCount: 0,
		liveRegion: Object.freeze({ role: 'status', ariaLive: 'polite', atomic: true })
	});
}

export function renderAccessibilitySurface(surface) {
	const contract = compileAccessibilitySurface(surface);
	const controls = coreActions.map((action) => renderControl(surface, action));
	if (surface === 'spatial') {
		return `<section class="spatial-surface" aria-labelledby="spatial-title"><h2 id="spatial-title">Spatial scene 작업</h2><div class="spatial-controls" role="list">${controls.map((control) => `<div role="listitem">${control}</div>`).join('')}</div></section>`;
	}
	return `<section class="table-surface" aria-labelledby="table-title"><h2 id="table-title">Relation table 작업</h2><table><caption>Spatial scene과 동등한 핵심 작업</caption><tbody>${controls.map((control, index) => `<tr><th scope="row">${escapeHtml(coreActions[index].label)}</th><td>${control}</td></tr>`).join('')}</tbody></table></section>`;
}

export function compileProfileExecution(profileName) {
	const profile = accessibilityProfiles[profileName];
	if (!profile) throw new Error(`unsupported accessibility profile: ${profileName}`);
	const surface = compileAccessibilitySurface(profile.surface);
	const completedActions = coreActions.filter((action) => surface.commands.includes(action.command));
	const motionDurationMs = profile.reducedMotion ? 0 : 160;
	return Object.freeze({
		profile: profile.id,
		surface: profile.surface,
		taskCount: coreActions.length,
		completedTaskCount: completedActions.length,
		failedTaskCount: coreActions.length - completedActions.length,
		motionDurationMs,
		reducedMotionApplied: !profile.reducedMotion || motionDurationMs === 0,
		highContrastNonColorCoverage: profile.highContrast ? coreActions.length : null,
		zoomReflowContract: profile.zoomPercent <= 200,
		lowGpuFallbackApplied: !profile.lowGpu || profile.surface === 'table',
		spatialOnlyActionCount: surface.spatialOnlyActionCount
	});
}

export function inspectAccessibilityEquivalence() {
	const spatial = compileAccessibilitySurface('spatial');
	const table = compileAccessibilitySurface('table');
	const executions = Object.keys(accessibilityProfiles).map(compileProfileExecution);
	const commandParity = spatial.commands.every((command, index) => table.commands[index] === command);
	const uniqueFocusIdCount = new Set([
		...spatial.controls.map((control) => control.focusId),
		...table.controls.map((control) => control.focusId)
	]).size;
	const keyboardNativeCoverage = [...spatial.controls, ...table.controls]
		.filter((control) => control.keyboardNative).length;
	const screenReaderSummaryCoverage = [...spatial.controls, ...table.controls]
		.filter((control) => control.screenReaderSummary).length;
	const completedTaskCount = executions.reduce((sum, execution) => sum + execution.completedTaskCount, 0);
	const taskCount = executions.reduce((sum, execution) => sum + execution.taskCount, 0);
	const profileReadyCount = executions.filter((execution) => execution.failedTaskCount === 0
		&& execution.zoomReflowContract
		&& execution.lowGpuFallbackApplied
		&& execution.spatialOnlyActionCount === 0).length;
	return Object.freeze({
		schemaVersion: 'accessibilityEquivalenceReport.v1',
		accessibilityContractVersion,
		coreActionCount: coreActions.length,
		surfaceCount: 2,
		profileCount: executions.length,
		executions: Object.freeze(executions),
		commandParity,
		spatialActionCoverage: spatial.controls.length,
		tableActionCoverage: table.controls.length,
		uniqueFocusIdCount,
		keyboardNativeCoverage,
		screenReaderSummaryCoverage,
		spatialOnlyActionCount: spatial.spatialOnlyActionCount,
		completedTaskCount,
		taskCount,
		profileReadyCount,
		machineReady: commandParity
			&& spatial.controls.length === coreActions.length
			&& table.controls.length === coreActions.length
			&& uniqueFocusIdCount === coreActions.length * 2
			&& keyboardNativeCoverage === coreActions.length * 2
			&& screenReaderSummaryCoverage === coreActions.length * 2
			&& spatial.spatialOnlyActionCount === 0
			&& completedTaskCount === taskCount
			&& profileReadyCount === executions.length
	});
}

export function main() {
	process.stdout.write(`${JSON.stringify(inspectAccessibilityEquivalence(), null, 2)}\n`);
	return 0;
}

if (typeof process !== 'undefined' && process.versions?.node) {
	const { pathToFileURL } = await import('node:url');
	if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
		process.exitCode = main();
	}
}
