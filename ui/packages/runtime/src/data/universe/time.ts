import type { UniverseAssertion } from '@dartlab/ui-contracts';

function instant(value: string, field: string): number {
	const parsed = Date.parse(value);
	if (!Number.isFinite(parsed) || !/(?:Z|[+-]\d{2}:\d{2})$/.test(value)) {
		throw new Error(`Universe ${field} must be a timezone-aware timestamp`);
	}
	return parsed;
}

export function normalizeUniverseTimestamp(value: string, field: string): string {
	return new Date(instant(value, field)).toISOString();
}

export function applyKnowledgeCutoff(
	assertions: readonly UniverseAssertion[],
	validAt: string | null,
	knownAt: string | null
): UniverseAssertion[] {
	const valid = validAt ? instant(validAt, 'validAt') : null;
	const known = knownAt ? instant(knownAt, 'knownAt') : null;
	return assertions.filter((assertion) => {
		const published = instant(assertion.sourcePublishedAt, 'sourcePublishedAt');
		const available = instant(assertion.availableAt, 'availableAt');
		const from = instant(assertion.validFrom, 'validFrom');
		const to = assertion.validTo ? instant(assertion.validTo, 'validTo') : null;
		if (published > available) throw new Error('Universe sourcePublishedAt cannot be newer than availableAt');
		if (to !== null && from > to) throw new Error('Universe validFrom cannot be newer than validTo');
		if (known !== null && available > known) return false;
		if (valid !== null && (from > valid || (to !== null && valid > to))) return false;
		return true;
	});
}
