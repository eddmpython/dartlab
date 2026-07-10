/**
 * ?q= 공유 URL 계약 동결.
 *
 * /scan 은 sitemap 등재 페이지이고 블로그·SNS 에 공유 링크가 야생에 있다. 컬럼키
 * rename · cond 스키마 변경 · preset id 변경은 옛 URL 을 조용히 파손시킨다. 이 테스트가
 * 그 계약의 잠금장치다. 빨개지면 재설계가 아니라 회귀다.
 *
 * v1 = 구 /screener 페이로드 {i, c, s, p}. v2 = 현행 {v:2, i, c, s, cols, p, sel}.
 */

import { describe, it, expect, beforeAll } from 'vitest';
import { decodeScanPayload, encodeScanPayload } from './url';
import { METRICS_BY_KEY } from './metrics';
import type { ScanPayload } from './types';

// url.ts 는 window.btoa/atob 를 쓴다. node 환경에 최소 shim 을 심는다.
beforeAll(() => {
	if (typeof globalThis.window === 'undefined') {
		(globalThis as Record<string, unknown>).window = {
			btoa: (s: string) => Buffer.from(s, 'binary').toString('base64'),
			atob: (s: string) => Buffer.from(s, 'base64').toString('binary')
		};
	}
});

/** 계약에 등장하는 메트릭 키. 이 키들이 사라지면 야생의 URL 이 조용히 drop 된다. */
const FROZEN_METRIC_KEYS = ['roe', 'marketCap', 'revenue', 'opMargin', 'debtRatio'];

describe('메트릭 키 동결', () => {
	it.each(FROZEN_METRIC_KEYS)('%s 는 카탈로그에 계속 존재한다', (key) => {
		expect(METRICS_BY_KEY[key], `${key} 가 사라지면 공유 URL 의 cond 가 silent drop 된다`).toBeDefined();
	});
});

describe('v2 왕복', () => {
	it('encode -> decode 가 페이로드를 보존한다', () => {
		const p: ScanPayload = {
			v: 2,
			i: ['반도체'],
			c: [{ metric: 'roe', op: '>=', value: 10 }],
			s: [{ key: 'marketCap', dir: 'desc' }],
			cols: ['roe', 'marketCap'],
			p: 'quality',
			sel: '005930'
		};
		const back = decodeScanPayload(encodeScanPayload(p));
		expect(back).toEqual(p);
	});

	it('between cond 의 value2 를 보존한다', () => {
		const p: ScanPayload = {
			v: 2,
			i: [],
			c: [{ metric: 'roe', op: 'between', value: 5, value2: 20 }],
			s: [],
			cols: []
		};
		const back = decodeScanPayload(encodeScanPayload(p));
		expect(back?.c[0]).toMatchObject({ metric: 'roe', op: 'between', value: 5, value2: 20 });
	});

	it('negate 플래그를 보존한다', () => {
		const p: ScanPayload = {
			v: 2,
			i: [],
			c: [{ metric: 'roe', op: '>=', value: 10, negate: true }],
			s: [],
			cols: []
		};
		expect(decodeScanPayload(encodeScanPayload(p))?.c[0].negate).toBe(true);
	});
});

describe('시장 범위 키(m) 는 additive 여야 한다', () => {
	const encodeRaw = (obj: unknown) =>
		Buffer.from(unescape(encodeURIComponent(JSON.stringify(obj))), 'binary').toString('base64');

	it('m 없는 옛 페이로드는 m=undefined (= KR)', () => {
		const old = { v: 2, i: [], c: [], s: [], cols: [] };
		expect(decodeScanPayload(encodeRaw(old))!.m).toBeUndefined();
	});

	it('US / ALL 을 왕복 보존', () => {
		for (const m of ['US', 'ALL'] as const) {
			const p: ScanPayload = { v: 2, i: [], c: [], s: [], cols: [], m };
			expect(decodeScanPayload(encodeScanPayload(p))!.m).toBe(m);
		}
	});

	it('알 수 없는 m 은 조용히 버린다 (KR 로 떨어짐)', () => {
		const p = { v: 2, i: [], c: [], s: [], cols: [], m: 'JP' };
		expect(decodeScanPayload(encodeRaw(p))!.m).toBeUndefined();
	});

	it('KR 은 굳이 싣지 않아도 된다 (옛 링크와 동일 바이트 유지)', () => {
		const withoutM: ScanPayload = { v: 2, i: [], c: [], s: [], cols: [] };
		expect(encodeScanPayload(withoutM)).toBe(encodeScanPayload({ ...withoutM, m: undefined }));
	});
});

describe('v1 (/screener) 하위호환', () => {
	const encodeRaw = (obj: unknown) =>
		Buffer.from(unescape(encodeURIComponent(JSON.stringify(obj))), 'binary').toString('base64');

	it('v 필드 없는 옛 페이로드를 계속 읽는다', () => {
		const v1 = { i: ['반도체'], c: [{ metric: 'roe', op: '>=', value: 10 }], s: [{ key: 'roe', dir: 'desc' }], p: 'value' };
		const back = decodeScanPayload(encodeRaw(v1));
		expect(back).not.toBeNull();
		expect(back!.v).toBe(2);
		expect(back!.i).toEqual(['반도체']);
		expect(back!.c[0]).toMatchObject({ metric: 'roe', op: '>=', value: 10 });
		expect(back!.p).toBe('value');
		expect(back!.cols).toEqual([]); // caller 가 DEFAULT_COLUMNS 를 채운다
	});
});

describe('방어적 sanitize (크래시 금지)', () => {
	const encodeRaw = (obj: unknown) =>
		Buffer.from(unescape(encodeURIComponent(JSON.stringify(obj))), 'binary').toString('base64');

	it('알 수 없는 메트릭 cond 는 drop 하되 페이로드는 살린다', () => {
		const p = { v: 2, i: [], c: [{ metric: '__gone__', op: '>=', value: 1 }, { metric: 'roe', op: '>=', value: 10 }], s: [], cols: [] };
		const back = decodeScanPayload(encodeRaw(p));
		expect(back!.c).toHaveLength(1);
		expect(back!.c[0].metric).toBe('roe');
	});

	it('알 수 없는 op 는 drop', () => {
		const p = { v: 2, i: [], c: [{ metric: 'roe', op: '~=', value: 1 }], s: [], cols: [] };
		expect(decodeScanPayload(encodeRaw(p))!.c).toHaveLength(0);
	});

	it('알 수 없는 sort key 와 col 은 drop', () => {
		const p = { v: 2, i: [], c: [], s: [{ key: '__gone__', dir: 'desc' }], cols: ['__gone__', 'roe'] };
		const back = decodeScanPayload(encodeRaw(p))!;
		expect(back.s).toHaveLength(0);
		expect(back.cols).toEqual(['roe']);
	});

	it('빈 문자열 / 깨진 base64 는 null (throw 금지)', () => {
		expect(decodeScanPayload('')).toBeNull();
		expect(decodeScanPayload('!!!not-base64!!!')).toBeNull();
	});

	it('JSON 이 객체가 아니면 null', () => {
		expect(decodeScanPayload(encodeRaw(42))).toBeNull();
		expect(decodeScanPayload(encodeRaw(null))).toBeNull();
	});
});
