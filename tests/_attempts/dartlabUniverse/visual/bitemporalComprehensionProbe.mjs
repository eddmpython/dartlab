/**
 * Universe validAt와 knownAt의 독립 판독 및 reviewed comprehension gate를 검증한다.
 *
 * Capabilities
 *   12개 revision task에서 현실 유효성과 당시 지식 가능성을 별도 answer와 control로 계산한다.
 *
 * AIContext
 *   AI 역할: availableAt을 validAt으로 바꾸거나 두 시간 축을 한 slider로 합치지 않는다.
 *
 * Guide
 *   Deterministic answer key와 human-reviewed response readiness를 분리한다.
 *
 * When
 *   U0-V04 Time Lens grammar, query semantics 또는 comprehension scoring이 바뀔 때 사용한다.
 *
 * How
 *   compileTimeTasks 뒤 renderReferenceTask, scoreTimeComprehension, inspectBitemporalComprehension을 실행한다.
 *
 * Requires
 *   Node.js 표준 라이브러리와 deterministic payload hash만 사용한다.
 *
 * Raises
 *   잘못된 interval, source time, query time, answer, review metadata는 Error를 발생시킨다.
 *
 * Example
 *   `node bitemporalComprehensionProbe.mjs`
 *
 * See Also
 *   mainPlan/dartlab-universe/02-ontology-evidence-contract.md
 *
 * 결과
 *   Machine time grammar와 reviewed validAt 및 knownAt accuracy를 별도 gate로 출력한다.
 */

import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

import { deterministicPayloadHash } from './deterministicLayoutProbe.mjs';

export const bitemporalGrammarVersion = 'universeBitemporalGrammar.v1';

const taskSeeds = Object.freeze([
	['01', '2026-01-01', '2026-12-31', '2026-01-05T09:00:00Z', '2026-01-05T10:00:00Z', '2026-06-30', '2026-06-30T23:59:59Z'],
	['02', '2026-01-01', '2026-12-31', '2026-07-01T09:00:00Z', '2026-07-01T10:00:00Z', '2026-06-30', '2026-06-30T23:59:59Z'],
	['03', '2025-01-01', '2025-12-31', '2025-01-02T09:00:00Z', '2025-01-02T10:00:00Z', '2026-06-30', '2026-06-30T23:59:59Z'],
	['04', '2027-01-01', '2027-12-31', '2027-01-02T09:00:00Z', '2027-01-02T10:00:00Z', '2026-06-30', '2026-06-30T23:59:59Z'],
	['05', '2027-01-01', '2027-12-31', '2026-01-02T09:00:00Z', '2026-01-02T10:00:00Z', '2026-06-30', '2026-06-30T23:59:59Z'],
	['06', '2025-01-01', '2026-12-31', '2026-07-10T09:00:00Z', '2026-07-10T10:00:00Z', '2026-06-30', '2026-06-30T23:59:59Z'],
	['07', '2026-03-01', null, '2026-03-01T09:00:00Z', '2026-03-01T10:00:00Z', '2029-06-30', '2029-06-30T23:59:59Z'],
	['08', '2026-01-01', '2026-06-30', '2026-01-01T09:00:00Z', '2026-01-01T10:00:00Z', '2026-06-30', '2026-06-30T23:59:59Z'],
	['09', '2026-01-01', '2026-12-31', '2026-06-30T09:00:00Z', '2026-06-30T10:00:00Z', '2026-06-30', '2026-06-30T10:00:00Z'],
	['10', '2025-01-01', '2025-06-30', '2026-01-01T09:00:00Z', '2026-01-01T10:00:00Z', '2025-03-31', '2025-12-31T23:59:59Z'],
	['11', '2026-07-01', '2026-12-31', '2026-06-01T09:00:00Z', '2026-06-01T10:00:00Z', '2026-08-01', '2026-05-31T23:59:59Z'],
	['12', '2026-01-01', '2026-01-31', '2026-02-10T09:00:00Z', '2026-02-12T10:00:00Z', '2026-01-15', '2026-02-11T23:59:59Z']
]);

function parseTimestamp(value, field) {
	const timestamp = Date.parse(String(value ?? ''));
	if (!Number.isFinite(timestamp)) throw new Error(`invalid ${field}: ${value}`);
	return timestamp;
}

function parseDate(value, field) {
	if (!/^\d{4}-\d{2}-\d{2}$/.test(String(value ?? ''))) {
		throw new Error(`invalid ${field}: ${value}`);
	}
	const timestamp = Date.parse(`${value}T00:00:00Z`);
	if (!Number.isFinite(timestamp)) throw new Error(`invalid ${field}: ${value}`);
	return timestamp;
}

function escapeHtml(value) {
	return String(value)
		.replaceAll('&', '&amp;')
		.replaceAll('<', '&lt;')
		.replaceAll('>', '&gt;')
		.replaceAll('"', '&quot;')
		.replaceAll("'", '&#39;');
}

export function compileTimeTask(input) {
	const taskId = String(input?.taskId ?? '');
	const validFrom = String(input?.validFrom ?? '');
	const validTo = input?.validTo === null ? null : String(input?.validTo ?? '');
	const sourcePublishedAt = String(input?.sourcePublishedAt ?? '');
	const availableAt = String(input?.availableAt ?? '');
	const queryValidAt = String(input?.queryValidAt ?? '');
	const queryKnownAt = String(input?.queryKnownAt ?? '');
	if (!taskId) throw new Error('time task identity is required');
	const validFromTime = parseDate(validFrom, 'validFrom');
	const validToTime = validTo === null ? null : parseDate(validTo, 'validTo');
	const sourcePublishedTime = parseTimestamp(sourcePublishedAt, 'sourcePublishedAt');
	const availableTime = parseTimestamp(availableAt, 'availableAt');
	const queryValidTime = parseDate(queryValidAt, 'queryValidAt');
	const queryKnownTime = parseTimestamp(queryKnownAt, 'queryKnownAt');
	if (validToTime !== null && validFromTime > validToTime) {
		throw new Error('validFrom must not be after validTo');
	}
	if (sourcePublishedTime > availableTime) {
		throw new Error('sourcePublishedAt must not be after availableAt');
	}
	const validAnswer = validFromTime <= queryValidTime
		&& (validToTime === null || queryValidTime <= validToTime);
	const knownAnswer = availableTime <= queryKnownTime;
	const assertionIdentity = deterministicPayloadHash({
		documentId: `filing-${taskId}`,
		revisionId: `revision-${taskId}`,
		validFrom,
		validTo,
		sourcePublishedAt,
		availableAt
	});
	return Object.freeze({
		taskId: `time-task-${taskId}`,
		assertionIdentity,
		documentId: `filing-${taskId}`,
		revisionId: `revision-${taskId}`,
		validFrom,
		validTo,
		sourcePublishedAt,
		availableAt,
		queryValidAt,
		queryKnownAt,
		validAnswer,
		knownAnswer,
		controls: Object.freeze([
			Object.freeze({ id: 'validAt', axis: 'reality', label: '실제 유효 시점', value: queryValidAt }),
			Object.freeze({ id: 'knownAt', axis: 'knowledge', label: '당시 알 수 있었던 시점', value: queryKnownAt })
		]),
		combinedSlider: false,
		accessibleSummary: `실제 유효 시점 ${queryValidAt}. 당시 알 수 있었던 시점 ${queryKnownAt}.`
	});
}

export function compileTimeTasks() {
	return Object.freeze(taskSeeds.map((seed) => compileTimeTask({
		taskId: seed[0],
		validFrom: seed[1],
		validTo: seed[2],
		sourcePublishedAt: seed[3],
		availableAt: seed[4],
		queryValidAt: seed[5],
		queryKnownAt: seed[6]
	})));
}

export function renderReferenceTask(task) {
	if (!task || !task.taskId || !Array.isArray(task.controls) || task.controls.length !== 2) {
		throw new Error('reference time task requires a compiled task');
	}
	return [
		`<article data-task-id="${escapeHtml(task.taskId)}" aria-label="${escapeHtml(task.accessibleSummary)}">`,
		`<section aria-label="실제 유효 기간"><time>${escapeHtml(task.validFrom)}</time><time>${escapeHtml(task.validTo ?? 'open')}</time></section>`,
		`<section aria-label="원천 공개 시간"><time>${escapeHtml(task.sourcePublishedAt)}</time><time>${escapeHtml(task.availableAt)}</time></section>`,
		`<fieldset data-time-axis="reality"><legend>실제 유효했나</legend><time>${escapeHtml(task.queryValidAt)}</time></fieldset>`,
		`<fieldset data-time-axis="knowledge"><legend>당시 알 수 있었나</legend><time>${escapeHtml(task.queryKnownAt)}</time></fieldset>`,
		'</article>'
	].join('');
}

function parseReviewedAt(value) {
	return new Date(parseTimestamp(value, 'reviewedAt')).toISOString();
}

export function scoreTimeComprehension(records, tasks = compileTimeTasks()) {
	if (!Array.isArray(records) || !Array.isArray(tasks)) {
		throw new Error('time comprehension records and tasks are required');
	}
	const answerKey = new Map(tasks.map((task) => [task.taskId, task]));
	if (answerKey.size !== 12) throw new Error('time comprehension requires exactly 12 tasks');
	const participants = new Set();
	let reviewedResponseCount = 0;
	let validCorrectCount = 0;
	let knownCorrectCount = 0;
	let combinedCorrectCount = 0;
	for (const record of records) {
		const participantId = String(record?.participantId ?? '');
		const reviewer = String(record?.reviewer ?? '');
		if (!participantId || !reviewer || record?.origin !== 'humanReviewed') {
			throw new Error('time review requires participantId, reviewer, and humanReviewed origin');
		}
		parseReviewedAt(record.reviewedAt);
		if (participants.has(participantId) || !Array.isArray(record.responses)) {
			throw new Error('time review participant and responses must be unique and complete');
		}
		const responses = new Map();
		for (const response of record.responses) {
			const taskId = String(response?.taskId ?? '');
			if (!answerKey.has(taskId) || responses.has(taskId)
				|| typeof response?.selectedValid !== 'boolean'
				|| typeof response?.selectedKnown !== 'boolean') {
				throw new Error('time review response is invalid');
			}
			responses.set(taskId, response);
		}
		if (responses.size !== answerKey.size) {
			throw new Error('each participant must answer all 12 time tasks once');
		}
		for (const [taskId, response] of responses) {
			const expected = answerKey.get(taskId);
			const validCorrect = response.selectedValid === expected.validAnswer;
			const knownCorrect = response.selectedKnown === expected.knownAnswer;
			validCorrectCount += Number(validCorrect);
			knownCorrectCount += Number(knownCorrect);
			combinedCorrectCount += Number(validCorrect && knownCorrect);
		}
		participants.add(participantId);
		reviewedResponseCount += responses.size;
	}
	const participantCount = participants.size;
	const validAccuracy = reviewedResponseCount === 0 ? null : validCorrectCount / reviewedResponseCount;
	const knownAccuracy = reviewedResponseCount === 0 ? null : knownCorrectCount / reviewedResponseCount;
	const combinedAccuracy = reviewedResponseCount === 0 ? null : combinedCorrectCount / reviewedResponseCount;
	return Object.freeze({
		participantCount,
		reviewedResponseCount,
		axisAnswerCount: reviewedResponseCount * 2,
		validCorrectCount,
		knownCorrectCount,
		combinedCorrectCount,
		validAccuracy,
		knownAccuracy,
		combinedAccuracy,
		participantTarget: 12,
		accuracyTarget: 0.9,
		reviewedReady: participantCount >= 12,
		passed: participantCount >= 12
			&& validAccuracy !== null && validAccuracy >= 0.9
			&& knownAccuracy !== null && knownAccuracy >= 0.9
			&& combinedAccuracy !== null && combinedAccuracy >= 0.9
	});
}

export function inspectBitemporalComprehension(records = []) {
	const tasks = compileTimeTasks();
	const answerCombinations = new Set(tasks.map((task) => `${task.validAnswer}:${task.knownAnswer}`));
	const separateControlCoverage = tasks.filter((task) => task.controls.length === 2
		&& task.controls[0].id === 'validAt'
		&& task.controls[1].id === 'knownAt').length;
	const combinedSliderUsageCount = tasks.filter((task) => task.combinedSlider).length;
	const ariaCoverage = tasks.filter((task) => task.accessibleSummary.includes('실제 유효 시점')
		&& task.accessibleSummary.includes('당시 알 수 있었던 시점')).length;
	const renderedTaskCount = tasks.filter((task) => {
		const html = renderReferenceTask(task);
		return html.includes('data-time-axis="reality"') && html.includes('data-time-axis="knowledge"');
	}).length;
	const comprehension = scoreTimeComprehension(records, tasks);
	const contractReady = answerCombinations.size === 4
		&& separateControlCoverage === tasks.length
		&& combinedSliderUsageCount === 0
		&& ariaCoverage === tasks.length
		&& renderedTaskCount === tasks.length;
	const blockerReasons = [];
	if (!contractReady) blockerReasons.push('bitemporalGrammarContractFailed');
	if (!comprehension.reviewedReady) blockerReasons.push('reviewedParticipantsBelow12');
	if (comprehension.validAccuracy === null || comprehension.knownAccuracy === null) {
		blockerReasons.push('bitemporalAccuracyUnmeasured');
	} else {
		if (comprehension.validAccuracy < 0.9) blockerReasons.push('validAtAccuracyBelow90Percent');
		if (comprehension.knownAccuracy < 0.9) blockerReasons.push('knownAtAccuracyBelow90Percent');
		if (comprehension.combinedAccuracy < 0.9) blockerReasons.push('combinedAccuracyBelow90Percent');
	}
	return Object.freeze({
		schemaVersion: 'bitemporalComprehensionReport.v1',
		bitemporalGrammarVersion,
		taskCount: tasks.length,
		answerCombinationCount: answerCombinations.size,
		separateControlCoverage,
		combinedSliderUsageCount,
		ariaCoverage,
		renderedTaskCount,
		participantCount: comprehension.participantCount,
		reviewedResponseCount: comprehension.reviewedResponseCount,
		axisAnswerCount: comprehension.axisAnswerCount,
		validAccuracy: comprehension.validAccuracy,
		knownAccuracy: comprehension.knownAccuracy,
		combinedAccuracy: comprehension.combinedAccuracy,
		contractReady,
		comprehensionReady: comprehension.passed,
		liveReady: contractReady && comprehension.passed,
		blockerReasons
	});
}

export function main(args = process.argv.slice(2)) {
	let records = [];
	if (args.length > 0) {
		if (args.length !== 2 || args[0] !== '--responses') {
			throw new Error('usage: bitemporalComprehensionProbe.mjs [--responses reviewedResponses.json]');
		}
		records = JSON.parse(readFileSync(args[1], 'utf8'));
		if (!Array.isArray(records)) throw new Error('reviewed response file must contain a JSON array');
	}
	process.stdout.write(`${JSON.stringify(inspectBitemporalComprehension(records), null, 2)}\n`);
	return 0;
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
	process.exitCode = main();
}
