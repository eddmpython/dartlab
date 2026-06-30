// US(EDGAR) 주가 source 정규화 단위 테스트 · date(YYYY-MM-DD/YYYYMMDD/epoch 방어)→Candle.t(YYYYMMDD)
// 변환·오름차순 정렬·일자 dedup·null/비정상 close 행 제외를 네트워크 없이 검증(parseEdgarPriceRows 순수 함수).
// bake schema(date/open/high/low/close/volume)는 KR gov company 와 동형 · close=수정주가라 r/tv=null.
import { describe, it, expect } from 'vitest';
import { parseEdgarPriceRows, parseEdgarRecent } from './edgarPriceSource';

function row(o: Partial<Record<string, unknown>>): Record<string, unknown> {
	return { date: '2026-06-24', open: 1, high: 1, low: 1, close: 1, volume: 1, ...o };
}

describe('parseEdgarPriceRows', () => {
	it("date 'YYYY-MM-DD'(gather 출력) → Candle.t 'YYYYMMDD'", () => {
		const out = parseEdgarPriceRows([row({ date: '2017-05-31', close: 38.5 })]);
		expect(out).toHaveLength(1);
		expect(out[0]?.t).toBe('20170531');
		expect(out[0]?.c).toBe(38.5);
	});

	it("이미 'YYYYMMDD' 인 date 도 통과(대시 제거 idempotent)", () => {
		const out = parseEdgarPriceRows([row({ date: '20260624', close: 293.08 })]);
		expect(out[0]?.t).toBe('20260624');
	});

	it('OHLCV 매핑 + 수정주가라 r/tv=null', () => {
		const out = parseEdgarPriceRows([row({ date: '2026-06-22', open: 297.31, high: 302.42, low: 296.76, close: 297.01, volume: 44879914 })]);
		expect(out[0]).toEqual({ t: '20260622', o: 297.31, h: 302.42, l: 296.76, c: 297.01, v: 44879914, r: null, tv: null });
	});

	it('오름차순 정렬 + 일자 dedup(연도 경계 안전)', () => {
		const out = parseEdgarPriceRows([
			row({ date: '2026-06-24', close: 3 }),
			row({ date: '2026-06-22', close: 1 }),
			row({ date: '2026-06-24', close: 9 }), // 중복 일자 · keep-first(정렬 후 첫 항목)
			row({ date: '2026-06-23', close: 2 })
		]);
		expect(out.map((k) => k.t)).toEqual(['20260622', '20260623', '20260624']);
		expect(out.find((k) => k.t === '20260624')?.c).toBe(3); // keep-first
	});

	it('null·0·음수 close, 빈 date 행 제외', () => {
		const out = parseEdgarPriceRows([
			row({ date: '2026-06-20', close: null }), // close 없음
			row({ date: '2026-06-21', close: 0 }), // 0 제외
			row({ date: '2026-06-22', close: -5 }), // 음수 제외
			row({ date: '', close: 100 }), // date 없음
			row({ date: '2026-06-23', close: 250.5 }) // 유효
		]);
		expect(out.map((k) => k.t)).toEqual(['20260623']);
	});

	it('open/high/low 결측 시 close 로 폴백(라인 degenerate 방어)', () => {
		const out = parseEdgarPriceRows([row({ date: '2026-06-24', open: null, high: null, low: null, close: 100 })]);
		expect(out[0]).toMatchObject({ o: 100, h: 100, l: 100, c: 100 });
	});
});

describe('parseEdgarRecent', () => {
	it('ticker 별 그룹 + 각 그룹 오름차순 정렬', () => {
		const map = parseEdgarRecent([
			{ ticker: 'AAPL', date: '20260625', open: 287, high: 288, low: 273, close: 275, volume: 107 },
			{ ticker: 'MSFT', date: '20260624', open: 500, high: 505, low: 498, close: 502, volume: 20 },
			{ ticker: 'AAPL', date: '20260624', open: 295, high: 299, low: 292, close: 293, volume: 53 }
		]);
		expect(Object.keys(map).sort()).toEqual(['AAPL', 'MSFT']);
		expect(map.AAPL!.map((k) => k.t)).toEqual(['20260624', '20260625']); // 정렬
		expect(map.AAPL![1]).toMatchObject({ c: 275, r: null, tv: null });
		expect(map.MSFT).toHaveLength(1);
	});

	it('ticker 소문자→대문자 정규화 + 빈 ticker·비정상 close 제외', () => {
		const map = parseEdgarRecent([
			{ ticker: 'aapl', date: '20260624', open: 1, high: 1, low: 1, close: 293, volume: 1 },
			{ ticker: '', date: '20260624', open: 1, high: 1, low: 1, close: 1, volume: 1 },
			{ ticker: 'XYZ', date: '20260624', open: 1, high: 1, low: 1, close: 0, volume: 1 }
		]);
		expect(Object.keys(map)).toEqual(['AAPL']);
		expect(map.AAPL?.[0]?.c).toBe(293);
	});
});
