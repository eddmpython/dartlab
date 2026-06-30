// Compare target normalization · browser-side equivalent of Python compare input guards.

import { marketForCode, type Market } from '../dartUrl';

export const MAX_COMPARE_TARGETS = 6;

export interface CompareTargetRejection {
	code: string;
	reason: 'duplicate' | 'self' | 'cross-market' | 'overflow';
}

export interface CompareTargetSet {
	reference: string;
	market: Market;
	vs: string[];
	rejected: CompareTargetRejection[];
}

export function normalizeCompareTargets(reference: string, rawVs: string[] | string | null | undefined): CompareTargetSet {
	const ref = normalizeCode(reference);
	const market = marketForCode(ref);
	const candidates = (Array.isArray(rawVs) ? rawVs : (rawVs ?? '').split(',')).map(normalizeCode).filter(Boolean);
	const seen = new Set([ref]);
	const vs: string[] = [];
	const rejected: CompareTargetRejection[] = [];
	for (const c of candidates) {
		if (c === ref) {
			rejected.push({ code: c, reason: 'self' });
			continue;
		}
		if (seen.has(c)) {
			rejected.push({ code: c, reason: 'duplicate' });
			continue;
		}
		if (marketForCode(c) !== market) {
			rejected.push({ code: c, reason: 'cross-market' });
			continue;
		}
		if (vs.length + 1 >= MAX_COMPARE_TARGETS) {
			rejected.push({ code: c, reason: 'overflow' });
			continue;
		}
		seen.add(c);
		vs.push(c);
	}
	return { reference: ref, market, vs, rejected };
}

function normalizeCode(code: string): string {
	const c = code.trim();
	return /^\d{6}$/.test(c) ? c : c.toUpperCase();
}
