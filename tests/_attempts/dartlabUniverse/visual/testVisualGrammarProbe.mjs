import assert from 'node:assert/strict';
import test from 'node:test';

import {
	compileVisualCard,
	compileVisualCards,
	inspectVisualGrammar,
	renderReferenceCard,
	scoreComprehension,
	stateOrder,
	visualTokens
} from './visualGrammarProbe.mjs';

function perfectReview(participantIndex) {
	const cards = compileVisualCards();
	return {
		participantId: `participant-${participantIndex}`,
		reviewer: 'operator-1',
		reviewedAt: `2026-07-15T${String(participantIndex).padStart(2, '0')}:00:00Z`,
		origin: 'humanReviewed',
		responses: cards.map((card) => ({ cardId: card.cardId, selectedStatus: card.status }))
	};
}

test('30개 card와 7개 상태를 만든다', () => {
	const cards = compileVisualCards();
	assert.equal(cards.length, 30);
	assert.deepEqual(new Set(cards.map((card) => card.status)), new Set(stateOrder));
});

test('색을 제외한 상태 signature가 7개 모두 다르다', () => {
	const signatures = stateOrder.map((status) => {
		const token = visualTokens[status];
		return [token.stroke, token.pattern, token.glyph, token.label, token.evidenceAction, token.ariaStatus].join('|');
	});
	assert.equal(new Set(signatures).size, stateOrder.length);
});

test('confidence는 opacity가 아니라 badge와 marker로 표현한다', () => {
	const cards = compileVisualCards();
	assert.ok(cards.every((card) => card.opacity === 1));
	assert.ok(cards.every((card) => card.confidenceBadge && card.confidenceMarker));
});

test('각 상태는 evidence action과 aria status를 가진다', () => {
	const cards = compileVisualCards();
	assert.ok(cards.every((card) => card.evidenceAction && card.ariaStatus && card.accessibleText));
});

test('DOM reference card는 semantic article과 button을 보존한다', () => {
	const html = renderReferenceCard(compileVisualCards()[0]);
	assert.match(html, /^<article /);
	assert.match(html, /aria-label=/);
	assert.match(html, /<button type="button" data-evidence-action=/);
});

test('12명 30문항 perfect review는 comprehension gate를 통과한다', () => {
	const records = Array.from({ length: 12 }, (_, index) => perfectReview(index));
	const score = scoreComprehension(records);
	assert.equal(score.participantCount, 12);
	assert.equal(score.reviewedResponseCount, 360);
	assert.equal(score.accuracy, 1);
	assert.equal(score.passed, true);
});

test('participant와 review가 없으면 contract만 통과하고 live는 차단한다', () => {
	const report = inspectVisualGrammar();
	assert.equal(report.contractReady, true);
	assert.equal(report.participantCount, 0);
	assert.equal(report.comprehensionAccuracy, null);
	assert.equal(report.comprehensionReady, false);
	assert.equal(report.liveReady, false);
	assert.deepEqual(report.blockerReasons, [
		'reviewedParticipantsBelow12',
		'comprehensionAccuracyUnmeasured'
	]);
});

test('잘못된 상태와 불완전한 review를 fail closed한다', () => {
	assert.throws(
		() => compileVisualCard({ cardId: 'bad', status: 'maybe', confidence: 'high', subjectLabel: 'A', predicateLabel: 'P', objectLabel: 'B' }),
		/unsupported visual status/
	);
	const incomplete = perfectReview(1);
	incomplete.responses = incomplete.responses.slice(0, 29);
	assert.throws(() => scoreComprehension([incomplete]), /answer all 30 cards/);
});
