/**
 * 정량재무제표 분기 파생 회귀핀.
 *
 * 핵심핀: 분기단독(Q4 = 연간 − Q3누적) 그룹핑이 as-reported 표시명(account_nm) 표류에 견뎌야 한다.
 * 실측 결함(한라IMS 092460): 매출액 account_id 는 연간·분기 모두 ifrs-full_Revenue 로 일관이지만
 * account_nm 이 연간 '매출액' vs 분기 '수익(매출액)' 로 표류 → 표시명을 그룹 키에 넣으면 연간행과
 * Q3누적행이 갈라져 2025Q4 매출액이 공백이 되었다. 이 테스트가 빨개지면 그 회귀가 돌아온 것이다.
 * 반대핀: '-표준계정코드 미사용-' 플레이스홀더 id 는 서로 다른 계정이 공유하므로(비식별) id 만으로
 * 병합하면 안 된다 (이름까지 키에 포함해 분리 유지).
 */

import { describe, it, expect } from 'vitest';
import { queryRowsFromRaw, pivot, type RawFinanceRow } from './financePivot';

const UNSTANDARD = '-표준계정코드 미사용-';

function row(
	reprt_code: string,
	account_id: string,
	account_nm: string,
	thstrm_amount: number,
	thstrm_add_amount: number | null,
	opts: Partial<RawFinanceRow> = {}
): RawFinanceRow {
	return {
		sj_div: 'CIS',
		fs_div: 'CFS',
		reprt_code,
		bsns_year: '2025',
		account_id,
		account_nm,
		account_detail: '-',
		thstrm_amount: String(thstrm_amount),
		thstrm_add_amount: thstrm_add_amount == null ? '' : String(thstrm_add_amount),
		ord: '30',
		...opts
	};
}

describe('financePivot _quarterStandalone · account_nm 표류', () => {
	// 한라IMS 092460 CIS/CFS 매출액 2025 실측값.
	const REV = 'ifrs-full_Revenue';
	const revRows: RawFinanceRow[] = [
		row('11013', REV, '수익(매출액)', 26_555_572_810, 26_555_572_810),
		row('11012', REV, '수익(매출액)', 35_662_182_789, 62_217_755_599),
		row('11014', REV, '수익(매출액)', 31_667_701_866, 93_885_457_465),
		row('11011', REV, '매출액', 133_476_935_159, null) // 연간(사업보고서) 표시명 표류
	];

	it('연간·분기 표시명이 달라도 Q4(연간 − Q3누적)를 채운다', () => {
		const qrows = queryRowsFromRaw(revRows, 'CIS', 'quarter', 'CFS');
		const q4 = qrows.find((r) => r.acct === REV && r.period === '2025Q4');
		expect(q4?.val).toBe(133_476_935_159 - 93_885_457_465); // 39,591,477,694
	});

	it('Q1~Q3 단독값은 분기보고서 thstrm 그대로', () => {
		const qrows = queryRowsFromRaw(revRows, 'CIS', 'quarter', 'CFS');
		const at = (p: string) => qrows.find((r) => r.acct === REV && r.period === p)?.val;
		expect(at('2025Q1')).toBe(26_555_572_810);
		expect(at('2025Q2')).toBe(35_662_182_789);
		expect(at('2025Q3')).toBe(31_667_701_866);
	});

	it('pivot 후 매출액 행에 2025Q4 값이 존재한다', () => {
		const st = pivot(queryRowsFromRaw(revRows, 'CIS', 'quarter', 'CFS'), 'CIS', 'CFS', 'quarter');
		const rev = st.rows.find((r) => r.accountId === REV);
		expect(rev?.values['2025Q4']).toBe(39_591_477_694);
	});
});

describe('financePivot _quarterStandalone · 비식별 플레이스홀더 분리', () => {
	// 서로 다른 두 계정이 같은 '-표준계정코드 미사용-' id 를 공유 → id 만으로 병합하면 오값.
	const rows: RawFinanceRow[] = [
		// 계정 A: 연간 1000, Q3누적 700 → Q4 300
		row('11014', UNSTANDARD, '지분법이익', 50, 700),
		row('11011', UNSTANDARD, '지분법이익', 1000, null),
		// 계정 B: 연간 3000, Q3누적 100 → Q4 2900
		row('11014', UNSTANDARD, '금융수익-유효이자율법에 따른 이자수익', 40, 100),
		row('11011', UNSTANDARD, '금융수익-유효이자율법에 따른 이자수익', 3000, null)
	];

	it('플레이스홀더 id 공유 계정은 이름별로 분리돼 각자 Q4 를 낸다', () => {
		const qrows = queryRowsFromRaw(rows, 'CIS', 'quarter', 'CFS');
		const q4vals = qrows
			.filter((r) => r.acct === UNSTANDARD && r.period === '2025Q4')
			.map((r) => r.val)
			.sort((a, b) => (a ?? 0) - (b ?? 0));
		// 병합 버그면 단일 오값(2300)만 나온다. 분리되면 300·2900 둘 다.
		expect(q4vals).toEqual([300, 2900]);
	});
});
