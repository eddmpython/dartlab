import { describe, expect, it } from 'vitest';
import { bundleFromRows } from './financeSource';
import type { RawRow } from '../../../data/finance/accounts';

function asset(scope: 'CFS' | 'OFS', year: number, reportCode: string, amount: number): RawRow {
	return {
		fs_div: scope,
		sj_div: 'BS',
		reprt_code: reportCode,
		bsns_year: year,
		account_id: 'ifrs-full_Assets',
		account_nm: '자산총계',
		account_detail: '-',
		thstrm_amount: amount,
		ord: 1
	};
}

describe('bundleFromRows scope freshness', () => {
	it('과거 연결보다 최신 별도 공시를 자동 선택한다', () => {
		const bundle = bundleFromRows([
			asset('CFS', 2017, '11012', 1),
			asset('OFS', 2025, '11011', 2),
			asset('OFS', 2026, '11013', 3)
		]);

		expect(bundle?.scope).toBe('OFS');
		expect(bundle?.views.quarter?.periods.at(-1)).toBe('26Q1');
	});

	it('최신 기간이 같으면 연결을 우선한다', () => {
		const bundle = bundleFromRows([
			asset('CFS', 2026, '11013', 1),
			asset('OFS', 2026, '11013', 2)
		]);

		expect(bundle?.scope).toBe('CFS');
	});

	it('사용자가 지정한 가용 범위는 최신성 자동 선택보다 우선한다', () => {
		const bundle = bundleFromRows(
			[asset('CFS', 2017, '11012', 1), asset('OFS', 2026, '11013', 2)],
			'CFS'
		);

		expect(bundle?.scope).toBe('CFS');
		expect(bundle?.views.quarter?.periods.at(-1)).toBe('17Q2');
	});
});
