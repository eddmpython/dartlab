import assert from 'node:assert/strict';
import test from 'node:test';

import {
	compileTimeTask,
	compileTimeTasks,
	inspectBitemporalComprehension,
	renderReferenceTask,
	scoreTimeComprehension
} from './bitemporalComprehensionProbe.mjs';

function perfectReview(participantIndex) {
	return {
		participantId: `time-participant-${participantIndex}`,
		reviewer: 'operator-1',
		reviewedAt: `2026-07-${String(participantIndex + 1).padStart(2, '0')}T10:00:00Z`,
		origin: 'humanReviewed',
		responses: compileTimeTasks().map((task) => ({
			taskId: task.taskId,
			selectedValid: task.validAnswer,
			selectedKnown: task.knownAnswer
		}))
	};
}

test('12개 task가 valid와 known 네 answer 조합을 모두 포함한다', () => {
	const tasks = compileTimeTasks();
	assert.equal(tasks.length, 12);
	assert.deepEqual(
		new Set(tasks.map((task) => `${task.validAnswer}:${task.knownAnswer}`)),
		new Set(['true:true', 'true:false', 'false:true', 'false:false'])
	);
});

test('validAt과 knownAt은 별도 control과 aria 설명을 가진다', () => {
	for (const task of compileTimeTasks()) {
		assert.deepEqual(task.controls.map((control) => control.id), ['validAt', 'knownAt']);
		assert.equal(task.combinedSlider, false);
		assert.match(task.accessibleSummary, /실제 유효 시점/);
		assert.match(task.accessibleSummary, /당시 알 수 있었던 시점/);
	}
});

test('미래 효력 공시는 known이지만 query validAt에는 아직 유효하지 않다', () => {
	const task = compileTimeTasks().find((item) => item.taskId === 'time-task-05');
	assert.equal(task.validAnswer, false);
	assert.equal(task.knownAnswer, true);
});

test('과거 사건의 늦은 공시는 valid하지만 query knownAt에는 아직 보이지 않는다', () => {
	const task = compileTimeTasks().find((item) => item.taskId === 'time-task-06');
	assert.equal(task.validAnswer, true);
	assert.equal(task.knownAnswer, false);
});

test('query cutoff가 달라도 assertion identity는 바뀌지 않는다', () => {
	const base = {
		taskId: 'identity', validFrom: '2026-01-01', validTo: '2026-12-31',
		sourcePublishedAt: '2026-01-02T09:00:00Z', availableAt: '2026-01-02T10:00:00Z',
		queryValidAt: '2026-03-01', queryKnownAt: '2026-03-01T23:59:59Z'
	};
	const first = compileTimeTask(base);
	const second = compileTimeTask({ ...base, queryValidAt: '2026-09-01', queryKnownAt: '2027-01-01T00:00:00Z' });
	assert.equal(first.assertionIdentity, second.assertionIdentity);
});

test('DOM reference는 reality와 knowledge fieldset을 분리한다', () => {
	const html = renderReferenceTask(compileTimeTasks()[0]);
	assert.match(html, /data-time-axis="reality"/);
	assert.match(html, /data-time-axis="knowledge"/);
	assert.match(html, /aria-label="실제 유효 기간"/);
	assert.match(html, /aria-label="원천 공개 시간"/);
});

test('12명 perfect review는 두 축과 combined 90% gate를 통과한다', () => {
	const records = Array.from({ length: 12 }, (_, index) => perfectReview(index));
	const score = scoreTimeComprehension(records);
	assert.equal(score.participantCount, 12);
	assert.equal(score.reviewedResponseCount, 144);
	assert.equal(score.axisAnswerCount, 288);
	assert.equal(score.validAccuracy, 1);
	assert.equal(score.knownAccuracy, 1);
	assert.equal(score.combinedAccuracy, 1);
	assert.equal(score.passed, true);
});

test('review가 없으면 grammar contract만 통과하고 live는 차단한다', () => {
	const report = inspectBitemporalComprehension();
	assert.equal(report.contractReady, true);
	assert.equal(report.participantCount, 0);
	assert.equal(report.validAccuracy, null);
	assert.equal(report.knownAccuracy, null);
	assert.equal(report.comprehensionReady, false);
	assert.equal(report.liveReady, false);
	assert.deepEqual(report.blockerReasons, [
		'reviewedParticipantsBelow12',
		'bitemporalAccuracyUnmeasured'
	]);
});

test('역전 interval, source time, 불완전 review를 fail closed한다', () => {
	const base = {
		taskId: 'bad', validFrom: '2026-12-31', validTo: '2026-01-01',
		sourcePublishedAt: '2026-01-01T09:00:00Z', availableAt: '2026-01-01T10:00:00Z',
		queryValidAt: '2026-06-01', queryKnownAt: '2026-06-01T00:00:00Z'
	};
	assert.throws(() => compileTimeTask(base), /validFrom must not be after validTo/);
	assert.throws(() => compileTimeTask({
		...base,
		validFrom: '2026-01-01', validTo: '2026-12-31',
		sourcePublishedAt: '2026-01-02T11:00:00Z', availableAt: '2026-01-02T10:00:00Z'
	}), /sourcePublishedAt must not be after availableAt/);
	const incomplete = perfectReview(1);
	incomplete.responses = incomplete.responses.slice(0, 11);
	assert.throws(() => scoreTimeComprehension([incomplete]), /answer all 12 time tasks/);
});
