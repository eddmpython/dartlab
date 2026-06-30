/**
 * Scan Studio URL 직렬화 · base64 ?q= 페이로드.
 *
 * v2 ScanPayload: { v: 2, i, c, s, cols, p, sel }
 * v1 (구 /screener) ScreenerPayload: { i, c, s, p } · backward compat 디코딩.
 *
 * v1 → v2 마이그레이션: cols 가 없으면 default 컬럼 사용. 깨진 derived 메트릭
 * (qoqRevenueGrowth, revCagr, etc.) 가 cond 에 있으면 silent drop + console warn.
 */

import type { ScanPayload, FilterCond, SortKey } from './types';
import { METRICS_BY_KEY } from './metrics';

const VALID_METRIC_KEYS = new Set(Object.keys(METRICS_BY_KEY));
const VALID_OPS = new Set(['>=', '<=', '==', '!=', 'between', 'contains', 'in', 'exists']);

function b64encode(s: string): string {
	if (typeof window === 'undefined') return '';
	return window.btoa(unescape(encodeURIComponent(s)));
}
function b64decode(s: string): string {
	if (typeof window === 'undefined') return '';
	return decodeURIComponent(escape(window.atob(s)));
}

export function encodeScanPayload(p: ScanPayload): string {
	return b64encode(JSON.stringify(p));
}

/** ?q= 디코드. v2 우선, v1 도 허용 (cols 없으면 caller 가 default 사용). */
export function decodeScanPayload(q: string): ScanPayload | null {
	if (!q) return null;
	try {
		const obj = JSON.parse(b64decode(q));
		if (!obj || typeof obj !== 'object') return null;

		// v2 정상 페이로드
		if (obj.v === 2) {
			return sanitizePayload(obj);
		}
		// v1 · { i, c, s, p } 만 · 마이그레이션
		if (Array.isArray(obj.i) && Array.isArray(obj.c) && Array.isArray(obj.s)) {
			console.info('[scan] v1 /screener payload 디코딩 · 호환 모드');
			return sanitizePayload({
				v: 2,
				i: obj.i,
				c: obj.c,
				s: obj.s,
				cols: [],
				p: obj.p
			});
		}
		return null;
	} catch (err) {
		console.warn('[scan] payload 디코딩 실패', err);
		return null;
	}
}

function sanitizePayload(raw: any): ScanPayload {
	const droppedConds: string[] = [];
	const conds: FilterCond[] = (Array.isArray(raw.c) ? raw.c : [])
		.filter((c: any) => {
			if (!c || typeof c !== 'object') return false;
			if (typeof c.metric !== 'string') return false;
			if (!VALID_METRIC_KEYS.has(c.metric)) {
				droppedConds.push(c.metric);
				return false;
			}
			if (!VALID_OPS.has(c.op)) return false;
			return true;
		})
		.map((c: any) => ({
			metric: c.metric,
			op: c.op,
			value: c.value,
			value2: c.value2,
			negate: c.negate
		}));
	if (droppedConds.length > 0) {
		console.info('[scan] 호환 안 되는 메트릭 cond drop:', droppedConds.join(', '));
	}

	const sorts: SortKey[] = (Array.isArray(raw.s) ? raw.s : [])
		.filter((s: any) => s && typeof s.key === 'string' && VALID_METRIC_KEYS.has(s.key))
		.map((s: any) => ({ key: s.key, dir: s.dir === 'asc' ? 'asc' : 'desc' }));

	const cols: string[] = (Array.isArray(raw.cols) ? raw.cols : [])
		.filter((k: any) => typeof k === 'string' && VALID_METRIC_KEYS.has(k));

	return {
		v: 2,
		i: Array.isArray(raw.i) ? raw.i.filter((x: any) => typeof x === 'string') : [],
		c: conds,
		s: sorts,
		cols,
		p: typeof raw.p === 'string' ? raw.p : undefined,
		sel: typeof raw.sel === 'string' ? raw.sel : undefined
	};
}
