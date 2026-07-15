/**
 * Universe state grammar와 reviewed comprehension gate를 검증한다.
 *
 * Capabilities
 *   7개 상태를 color 외 stroke, pattern, glyph, label, evidence action, aria channel로 분리한다.
 *
 * AIContext
 *   AI 역할: confidence opacity나 색 하나로 truth status를 표현하지 않고 unknown과 candidate를 보존한다.
 *
 * Guide
 *   30개 deterministic card contract와 실제 participant review readiness를 분리한다.
 *
 * When
 *   U0-V01 visual grammar 또는 상태 token이 바뀔 때 실행한다.
 *
 * How
 *   compileVisualCards 뒤 inspectVisualGrammar와 scoreComprehension을 순서대로 호출한다.
 *
 * Requires
 *   Node.js 표준 라이브러리만 사용하며 renderer dependency가 필요하지 않다.
 *
 * Raises
 *   잘못된 status, confidence, answer 또는 review metadata는 Error를 발생시킨다.
 *
 * Example
 *   `node visualGrammarProbe.mjs`
 *
 * See Also
 *   mainPlan/dartlab-universe/11-visual-information-physics.md
 *
 * 결과
 *   Machine contract와 reviewed participant comprehension을 별도 gate로 출력한다.
 */

import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

export const visualGrammarVersion = 'universeVisualGrammar.v1';
export const stateOrder = Object.freeze([
	'fact',
	'candidate',
	'derived',
	'disputed',
	'retracted',
	'scenario',
	'unknown'
]);

export const visualTokens = Object.freeze({
	fact: Object.freeze({
		stroke: 'solid-2',
		pattern: 'none',
		glyph: 'check-circle',
		label: '근거 확인',
		color: 'evidenceGreen',
		evidenceAction: 'openEvidence',
		ariaStatus: '원문 근거가 결속된 사실'
	}),
	candidate: Object.freeze({
		stroke: 'dash-2-2',
		pattern: 'diagonal-open',
		glyph: 'search',
		label: '근거 탐색 중',
		color: 'candidateAmber',
		evidenceAction: 'findEvidence',
		ariaStatus: '근거를 찾아야 하는 관계 후보'
	}),
	derived: Object.freeze({
		stroke: 'double-1',
		pattern: 'horizontal',
		glyph: 'function',
		label: '계산 결과',
		color: 'derivedBlue',
		evidenceAction: 'inspectDerivation',
		ariaStatus: '원천 자료에서 계산한 파생 결과'
	}),
	disputed: Object.freeze({
		stroke: 'dash-dot-2',
		pattern: 'cross',
		glyph: 'split',
		label: '근거 충돌',
		color: 'disputedOrange',
		evidenceAction: 'compareEvidence',
		ariaStatus: '서로 충돌하는 근거가 있는 주장'
	}),
	retracted: Object.freeze({
		stroke: 'strike-2',
		pattern: 'backslash',
		glyph: 'undo',
		label: '철회됨',
		color: 'retractedRed',
		evidenceAction: 'openRetraction',
		ariaStatus: '후속 공시로 철회된 과거 주장'
	}),
	scenario: Object.freeze({
		stroke: 'dot-2',
		pattern: 'wave',
		glyph: 'flask',
		label: '가정 시나리오',
		color: 'scenarioPurple',
		evidenceAction: 'inspectAssumptions',
		ariaStatus: '관측 사실이 아닌 명시적 가정 시나리오'
	}),
	unknown: Object.freeze({
		stroke: 'gap-2',
		pattern: 'empty',
		glyph: 'question',
		label: '판정 불가',
		color: 'unknownGray',
		evidenceAction: 'explainGap',
		ariaStatus: '근거 결손으로 상태를 판정할 수 없음'
	})
});

const confidenceTokens = Object.freeze({
	low: Object.freeze({ badge: '낮음', marker: 'one-of-three' }),
	medium: Object.freeze({ badge: '중간', marker: 'two-of-three' }),
	high: Object.freeze({ badge: '높음', marker: 'three-of-three' })
});

const cardStateSequence = Object.freeze([
	'fact', 'candidate', 'derived', 'disputed', 'retracted', 'scenario', 'unknown',
	'candidate', 'fact', 'unknown', 'scenario', 'derived', 'retracted', 'disputed',
	'fact', 'candidate', 'derived', 'disputed', 'retracted', 'scenario', 'unknown',
	'candidate', 'fact', 'unknown', 'scenario', 'derived', 'retracted', 'disputed',
	'fact', 'candidate'
]);

function nonColorSignature(token) {
	return [token.stroke, token.pattern, token.glyph, token.label, token.evidenceAction, token.ariaStatus].join('|');
}

function escapeHtml(value) {
	return String(value)
		.replaceAll('&', '&amp;')
		.replaceAll('<', '&lt;')
		.replaceAll('>', '&gt;')
		.replaceAll('"', '&quot;')
		.replaceAll("'", '&#39;');
}

export function compileVisualCard(input) {
	const status = String(input?.status ?? '');
	const confidence = String(input?.confidence ?? '');
	if (!stateOrder.includes(status)) {
		throw new Error(`unsupported visual status: ${status}`);
	}
	if (!(confidence in confidenceTokens)) {
		throw new Error(`unsupported confidence band: ${confidence}`);
	}
	const token = visualTokens[status];
	const confidenceToken = confidenceTokens[confidence];
	const cardId = String(input.cardId ?? '');
	const subjectLabel = String(input.subjectLabel ?? '');
	const predicateLabel = String(input.predicateLabel ?? '');
	const objectLabel = String(input.objectLabel ?? '');
	if (!cardId || !subjectLabel || !predicateLabel || !objectLabel) {
		throw new Error('visual card identity and relation labels are required');
	}
	const accessibleText = `${subjectLabel}, ${predicateLabel}, ${objectLabel}. ${token.ariaStatus}. 신뢰도 ${confidenceToken.badge}.`;
	return Object.freeze({
		cardId,
		status,
		subjectLabel,
		predicateLabel,
		objectLabel,
		stroke: token.stroke,
		pattern: token.pattern,
		glyph: token.glyph,
		statusLabel: token.label,
		color: token.color,
		evidenceAction: token.evidenceAction,
		ariaStatus: token.ariaStatus,
		confidence,
		confidenceBadge: confidenceToken.badge,
		confidenceMarker: confidenceToken.marker,
		opacity: 1,
		accessibleText,
		nonColorSignature: nonColorSignature(token)
	});
}

export function compileVisualCards() {
	return Object.freeze(cardStateSequence.map((status, index) => compileVisualCard({
		cardId: `visual-card-${String(index + 1).padStart(2, '0')}`,
		status,
		subjectLabel: `기업 ${String((index % 9) + 1).padStart(2, '0')}`,
		predicateLabel: ['공급', '비교', '변화'][index % 3],
		objectLabel: `기업 ${String(((index + 3) % 11) + 1).padStart(2, '0')}`,
		confidence: ['low', 'medium', 'high'][index % 3]
	})));
}

export function renderReferenceCard(card) {
	if (!card || !stateOrder.includes(card.status)) {
		throw new Error('reference card requires a compiled visual card');
	}
	return [
		`<article data-card-id="${escapeHtml(card.cardId)}" data-status="${escapeHtml(card.status)}"`,
		` data-stroke="${escapeHtml(card.stroke)}" data-pattern="${escapeHtml(card.pattern)}"`,
		` aria-label="${escapeHtml(card.accessibleText)}">`,
		`<span aria-hidden="true" data-glyph="${escapeHtml(card.glyph)}"></span>`,
		`<strong>${escapeHtml(card.statusLabel)}</strong>`,
		`<span>${escapeHtml(card.subjectLabel)} ${escapeHtml(card.predicateLabel)} ${escapeHtml(card.objectLabel)}</span>`,
		`<span aria-label="신뢰도 ${escapeHtml(card.confidenceBadge)}" data-confidence-marker="${escapeHtml(card.confidenceMarker)}">${escapeHtml(card.confidenceBadge)}</span>`,
		`<button type="button" data-evidence-action="${escapeHtml(card.evidenceAction)}">근거 확인</button>`,
		'</article>'
	].join('');
}

function parseReviewedAt(value) {
	const timestamp = Date.parse(String(value ?? ''));
	if (!Number.isFinite(timestamp)) {
		throw new Error(`invalid reviewedAt: ${value}`);
	}
	return new Date(timestamp).toISOString();
}

export function scoreComprehension(records, cards = compileVisualCards()) {
	if (!Array.isArray(records) || !Array.isArray(cards)) {
		throw new Error('comprehension records and cards are required');
	}
	const answerKey = new Map(cards.map((card) => [card.cardId, card.status]));
	if (answerKey.size !== 30) {
		throw new Error('visual comprehension requires exactly 30 cards');
	}
	const reviewedParticipants = new Map();
	let reviewedResponseCount = 0;
	let correctResponseCount = 0;
	for (const record of records) {
		const participantId = String(record?.participantId ?? '');
		const reviewer = String(record?.reviewer ?? '');
		const origin = String(record?.origin ?? '');
		if (!participantId || !reviewer || origin !== 'humanReviewed') {
			throw new Error('review record requires participantId, reviewer, and humanReviewed origin');
		}
		parseReviewedAt(record.reviewedAt);
		if (!Array.isArray(record.responses)) {
			throw new Error('review record responses must be an array');
		}
		const responseMap = new Map();
		for (const response of record.responses) {
			const cardId = String(response?.cardId ?? '');
			const selectedStatus = String(response?.selectedStatus ?? '');
			if (!answerKey.has(cardId) || !stateOrder.includes(selectedStatus) || responseMap.has(cardId)) {
				throw new Error('review response card or status is invalid');
			}
			responseMap.set(cardId, selectedStatus);
		}
		if (responseMap.size !== answerKey.size || reviewedParticipants.has(participantId)) {
			throw new Error('each unique participant must answer all 30 cards once');
		}
		let participantCorrect = 0;
		for (const [cardId, selectedStatus] of responseMap) {
			participantCorrect += Number(answerKey.get(cardId) === selectedStatus);
		}
		reviewedParticipants.set(participantId, participantCorrect);
		reviewedResponseCount += responseMap.size;
		correctResponseCount += participantCorrect;
	}
	const participantCount = reviewedParticipants.size;
	const accuracy = reviewedResponseCount > 0 ? correctResponseCount / reviewedResponseCount : null;
	return Object.freeze({
		participantCount,
		reviewedResponseCount,
		correctResponseCount,
		accuracy,
		participantTarget: 12,
		accuracyTarget: 0.9,
		reviewedReady: participantCount >= 12,
		passed: participantCount >= 12 && accuracy !== null && accuracy >= 0.9
	});
}

export function inspectVisualGrammar(records = []) {
	const cards = compileVisualCards();
	const signatures = new Set(stateOrder.map((status) => nonColorSignature(visualTokens[status])));
	const colorOnlyCollisionCount = stateOrder.length - signatures.size;
	const evidenceAffordanceCoverage = cards.filter((card) => card.evidenceAction && card.statusLabel).length;
	const ariaCoverage = cards.filter((card) => card.accessibleText && card.ariaStatus).length;
	const confidenceOpacityUsageCount = cards.filter((card) => card.opacity !== 1).length;
	const renderedCardCount = cards.filter((card) => renderReferenceCard(card).includes('aria-label=')).length;
	const comprehension = scoreComprehension(records, cards);
	const contractReady = colorOnlyCollisionCount === 0
		&& evidenceAffordanceCoverage === cards.length
		&& ariaCoverage === cards.length
		&& confidenceOpacityUsageCount === 0
		&& renderedCardCount === cards.length;
	const blockerReasons = [];
	if (!contractReady) blockerReasons.push('visualGrammarContractFailed');
	if (!comprehension.reviewedReady) blockerReasons.push('reviewedParticipantsBelow12');
	if (comprehension.accuracy === null) blockerReasons.push('comprehensionAccuracyUnmeasured');
	else if (comprehension.accuracy < comprehension.accuracyTarget) blockerReasons.push('comprehensionAccuracyBelow90Percent');
	return Object.freeze({
		schemaVersion: 'visualGrammarReport.v1',
		visualGrammarVersion,
		stateCount: stateOrder.length,
		cardCount: cards.length,
		uniqueNonColorSignatureCount: signatures.size,
		colorOnlyCollisionCount,
		evidenceAffordanceCoverage,
		ariaCoverage,
		confidenceOpacityUsageCount,
		renderedCardCount,
		participantCount: comprehension.participantCount,
		reviewedResponseCount: comprehension.reviewedResponseCount,
		comprehensionAccuracy: comprehension.accuracy,
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
			throw new Error('usage: visualGrammarProbe.mjs [--responses reviewedResponses.json]');
		}
		records = JSON.parse(readFileSync(args[1], 'utf8'));
		if (!Array.isArray(records)) {
			throw new Error('reviewed response file must contain a JSON array');
		}
	}
	process.stdout.write(`${JSON.stringify(inspectVisualGrammar(records), null, 2)}\n`);
	return 0;
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
	process.exitCode = main();
}
