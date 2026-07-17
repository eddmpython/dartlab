import { describe, expect, it } from 'vitest';
import type { DataCore } from '../fetch/request';
import { buildUniverseGlobalCatalog, createUniverseGlobalRuntime, searchUniverseGlobalCatalog } from './global';

const dartRows = [
	{ corp_code: '00126380', corp_name: '삼성전자', corp_eng_name: 'Samsung Electronics', stock_code: '005930', modify_date: '20260716' },
	{ corp_code: '00100090', corp_name: 'LG스포츠', corp_eng_name: 'LG SPORTS Ltd.', stock_code: ' ', modify_date: '20250204' }
];
const dartProfiles = [
	{ corp_code: '00126380', stockCode: '005930', induty_code: '264', est_dt: '19690113', corp_cls: 'Y' }
];
const secRows = [
	{ ticker: 'AAPL', cik: '0000320193', title: 'Apple Inc.', exchange: 'Nasdaq', is_exchange_listed: true, is_otc: false },
	{ ticker: 'APC.F', cik: '0000320193', title: 'Apple Inc.', exchange: null, is_exchange_listed: false, is_otc: true }
];
const edgarRows = [
	{
		stockCode: 'AAPL', cik: '0000320193', corpName: 'Apple Inc.', fy: 2023, sector: 'manufacturing', sic: '3571',
		sales: 383_000, operating_profit: 114_000, net_profit: 97_000, total_assets: 352_000,
		total_stockholders_equity: 62_000, total_liabilities: 290_000, current_assets: 143_000, current_liabilities: 145_000
	},
	{
		stockCode: 'AAPL', cik: '0000320193', corpName: 'Apple Inc.', fy: 2024, sector: 'manufacturing', sic: '3571',
		sales: 391_000, operating_profit: 123_000, net_profit: 94_000, total_assets: 365_000,
		total_stockholders_equity: 57_000, total_liabilities: 308_000, current_assets: 153_000, current_liabilities: 176_000,
		cash_and_cash_equivalents: 30_000, operating_cashflow: 118_000, investing_cashflow: -9_000,
		financing_cash_flow: -122_000, capex: 9_400, shortterm_borrowings: 10_000, longterm_borrowings: 86_000,
		interest_expense: 3_000
	},
	{
		stockCode: '0009999999', cik: '0009999999', corpName: 'CIK ONLY TRUST', fy: 2024, sector: 'finance', sic: '6726',
		sales: 100, net_profit: 8, total_assets: 1_000, total_stockholders_equity: 600
	}
];

function financeRow(
	sj_div: string,
	account_id: string,
	account_nm: string,
	thstrm_amount: number,
	bsns_year = '2024'
): Record<string, unknown> {
	return {
		sj_div, fs_div: 'CFS', reprt_code: '11011', rcept_no: `${bsns_year}0315000001`, bsns_year,
		account_id, account_nm, account_detail: '-', thstrm_amount, thstrm_add_amount: null, ord: 1
	};
}

const samsungFinance = [
	financeRow('IS', 'ifrs-full_Revenue', '매출액', 300_000),
	financeRow('IS', 'dart_OperatingIncomeLoss', '영업이익', 30_000),
	financeRow('IS', 'ifrs-full_ProfitLoss', '당기순이익', 24_000),
	financeRow('BS', 'ifrs-full_Assets', '자산총계', 500_000),
	financeRow('BS', 'ifrs-full_Liabilities', '부채총계', 200_000),
	financeRow('BS', 'ifrs-full_Equity', '자본총계', 300_000),
	financeRow('BS', 'ifrs-full_CurrentAssets', '유동자산', 220_000),
	financeRow('BS', 'ifrs-full_CurrentLiabilities', '유동부채', 110_000),
	financeRow('CF', 'ifrs-full_CashFlowsFromUsedInOperatingActivities', '영업활동현금흐름', 42_000),
	financeRow('IS', 'ifrs-full_Revenue', '매출액', 250_000, '2023')
];

function fakeCore(): DataCore & { wholeCalls: string[]; rowCalls: string[] } {
	const wholeCalls: string[] = [];
	const rowCalls: string[] = [];
	const whole = new Map<string, unknown[]>([
		['metadata/dartList.parquet', dartRows],
		['dart/scan/corpProfile.parquet', dartProfiles],
		['edgar/tickers/tickers.parquet', secRows],
		['edgar/scan/finance.parquet', edgarRows]
	]);
	return {
		wholeCalls,
		rowCalls,
		request: async () => { throw new Error('unexpected request'); },
		requestBytes: async () => { throw new Error('unexpected bytes request'); },
		requestParquetWholeFile: async (spec) => {
			wholeCalls.push(spec.path);
			return (whole.get(spec.path) ?? null) as never;
		},
		requestParquetRows: async (spec) => {
			rowCalls.push(spec.path);
			return (spec.path === 'dart/finance/005930.parquet' ? samsungFinance : []) as never;
		},
		clear: () => undefined
	};
}

describe('Universe global catalog', () => {
	it('DART 전체 법인과 EDGAR CIK-only 법인을 중복 없이 유지한다', () => {
		const catalog = buildUniverseGlobalCatalog(dartRows, dartProfiles, secRows, edgarRows);
		expect(catalog.coverage).toMatchObject({
			krLegalEntityCount: 2,
			krSecurityCount: 1,
			usLegalEntityCount: 2,
			usTickerCount: 2,
			usFinanceEntityCount: 2,
			entityCount: 4
		});
		const cikOnly = searchUniverseGlobalCatalog(catalog, { query: '0009999999' }).matches[0];
		expect(cikOnly).toMatchObject({ entityId: 'US:SEC:0009999999', ticker: null, financialCoverage: 'indexed' });
	});

	it('ticker, corpCode, 한글 법인명을 같은 검색 표면에서 찾는다', () => {
		const catalog = buildUniverseGlobalCatalog(dartRows, dartProfiles, secRows, edgarRows);
		expect(searchUniverseGlobalCatalog(catalog, { query: 'AAPL' }).matches[0]?.legalEntityId).toBe('0000320193');
		expect(searchUniverseGlobalCatalog(catalog, { query: '00100090' }).matches[0]?.label).toBe('LG스포츠');
		expect(searchUniverseGlobalCatalog(catalog, { query: '삼성전자', market: 'KR' }).matches[0]?.ticker).toBe('005930');
	});

	it('글로벌 탭 진입 전에는 원천을 읽지 않고 진입 후 4개 SSOT를 한 번만 읽는다', async () => {
		const core = fakeCore();
		const runtime = createUniverseGlobalRuntime(core);
		expect(core.wholeCalls).toHaveLength(0);
		const first = await runtime.coverage();
		const second = await runtime.search({ query: 'Apple' });
		expect(first.entityCount).toBe(4);
		expect(second.matches[0]?.ticker).toBe('AAPL');
		expect(core.wholeCalls).toHaveLength(4);
		const cikOnly = await runtime.profile('US:SEC:0009999999');
		expect(cikOnly.entity.ticker).toBeNull();
		expect(cikOnly.answeredQuestionCount).toBeGreaterThan(0);
	});

	it('한미 20문항에서 통화 금액은 차단하고 같은 기준연도의 비율만 READY로 승격한다', async () => {
		const runtime = createUniverseGlobalRuntime(fakeCore());
		const comparison = await runtime.compare('KR:DART:00126380', 'US:SEC:0000320193');
		const revenue = comparison.results.find((result) => result.question.metricId === 'revenue');
		const margin = comparison.results.find((result) => result.question.metricId === 'operatingMargin');
		expect(revenue?.status).toBe('blocked');
		expect(revenue?.gaps.map((gap) => gap.reasonCode)).toContain('unitMismatch');
		expect(margin?.status).toBe('ready');
		expect(comparison.kr.answeredQuestionCount).toBeGreaterThan(5);
		expect(comparison.us.answeredQuestionCount).toBeGreaterThan(10);
	});
});
