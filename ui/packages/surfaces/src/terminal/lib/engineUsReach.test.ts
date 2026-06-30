// US(EDGAR) 회사가 엔진에 도달하는지 검증 · routeLoad 가 finance+prices+index 에 US 를 병합하면
// suggest 가 ticker 를 찾고 buildCompany 가 non-null co 를 만든다(eco 없이도). 통화 표시 polish 와 독립.
import { describe, it, expect } from 'vitest';
import { createEngine } from './engine';
import type { RawData } from './types';

function rawWithUs(): RawData {
	// US 번들 1개(AAPL) · proto_us_terminal_data.py 산출 shape 축약. KR base 는 빈 생태계.
	const aaplFin = {
		currency: 'USD',
		is: { sales: [null, null, 0.3833, 0.391, 0.4162], op: [null, null, 0.1142, 0.1232, 0.1331], net: [null, null, 0.097, 0.0937, 0.112], opMargin: [null, null, 29.8, 31.5, 32] },
		bs: { assets: {}, liab: {}, equity: {}, totals: { totalAsset: [null, null, 0.3525, 0.3526, 0.365], totalLiab: [null, null, 0.2901, 0.2904, 0.308], totalEquity: [null, null, 0.0621, 0.0621, 0.062], currAsset: [null, null, 0.135, 0.1436, 0.153], currLiab: [null, null, 0.145, 0.1453, 0.176] } },
		cf: { op: 0.118, inv: -0.01, fin: -0.1, opening: null, closing: null, fx: 0 },
		ratios: { roe: [null, null, 156, 151, 180], debtRatio: [null, null, 467, 467, 496] },
		macroExposure: null
	};
	const aaplPx = { currency: 'USD', currentPrice: 293.08, marketCap: 4304570296480, return1m: 1, return3m: 2, return1y: 40, volatility1y: 30, week52High: 320, week52Low: 200, volumeAvg30d: 50000000, foreignPct: null, beta: null, priceUpdated: '2026-06-24' };
	return {
		finance: { years: ['2021', '2022', '2023', '2024', '2025'], companies: { AAPL: aaplFin } },
		macro: null,
		meta: null,
		prices: { data: { AAPL: aaplPx } },
		index: [{ stockCode: 'AAPL', corpName: 'Apple Inc.', industry: 'Nasdaq', revenue: 0.4162 }],
		eco: null,
		quarters: null,
		industryStats: null
	} as unknown as RawData;
}

describe('US terminal reach', () => {
	const eng = createEngine(rawWithUs());

	it('suggest 가 ticker(AAPL)로 US 회사를 찾는다', () => {
		const hits = eng.suggest('AAPL', 5);
		expect(hits.some((h) => h.code === 'AAPL')).toBe(true);
	});

	it('suggest 가 회사명(Apple)으로도 찾는다', () => {
		const hits = eng.suggest('Apple', 5);
		expect(hits.some((h) => h.code === 'AAPL')).toBe(true);
	});

	it('buildCompany 가 US 회사 co 를 non-null 로 만든다 (finance+prices 병합 전제)', () => {
		const co = eng.buildCompany('AAPL');
		expect(co).not.toBeNull();
		expect(co?.code).toBe('AAPL');
		expect(co?.name).toBeTruthy();
		// 가격/재무가 흘러든다 · currentPrice, 매출 시리즈 존재
		expect(co?.price.last).toBe(293.08);
		expect(co?.income.rows.find((r) => r.id === 'sales')?.vals.some((v) => v != null)).toBe(true);
	});

	it('finance 또는 prices 누락 회사는 buildCompany null (게이트 동작 확인)', () => {
		expect(eng.buildCompany('ZZZZ')).toBeNull();
	});
});
