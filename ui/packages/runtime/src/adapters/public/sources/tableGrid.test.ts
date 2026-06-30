import { describe, it, expect } from 'vitest';
import { expandGrid, expandTables, gridToRowDicts, collapseColspanDupes } from './tableGrid';

// ROWSPAN=2 COLSPAN=2 "부문" + 후속 행 셀 부족 (기존 파서가 밀리던 패턴).
const RAW_SPAN = `
<TABLE>
<THEAD><TR>
<TH COLSPAN="2">부문</TH><TH>품목</TH><TH>매입액</TH><TH>비중</TH><TH>매입처</TH>
</TR></THEAD>
<TBODY>
<TR><TD ROWSPAN="2" COLSPAN="2">CE부문</TD><TD>디스플레이</TD><TD>21,647</TD><TD>10.2%</TD><TD>CSOT 등</TD></TR>
<TR><TD>메모리</TD><TD>19,930</TD><TD>9.4%</TD><TD>Micron 등</TD></TR>
</TBODY>
</TABLE>`;

describe('expandGrid · rowspan/colspan 격자전개', () => {
	it('rowspan 아래로 채움 + 직사각', () => {
		expect(expandGrid([[{ text: 'CE', rspan: 2, cspan: 2 }, { text: 'A', rspan: 1, cspan: 1 }], [{ text: 'B', rspan: 1, cspan: 1 }]])).toEqual([
			['CE', 'CE', 'A'],
			['CE', 'CE', 'B']
		]);
	});
});

describe('collapseColspanDupes', () => {
	it('완전 중복 인접 열 합침', () => {
		expect(collapseColspanDupes([['부문', '부문', '품목'], ['CE', 'CE', 'A']])).toEqual([['부문', '품목'], ['CE', 'A']]);
	});
});

describe('expandTables + gridToRowDicts · 셀 밀림 제거', () => {
	it('직사각(ragged 0)', () => {
		const grids = expandTables(RAW_SPAN);
		expect(grids).toHaveLength(1);
		expect(new Set(grids[0]!.map((r) => r.length)).size).toBe(1);
	});

	it('메모리 행 정렬 복원 (기존 버그면 한 칸씩 밀림)', () => {
		const rows = gridToRowDicts(expandTables(RAW_SPAN)[0]!);
		expect(rows).toHaveLength(2);
		const r2 = rows[1]!;
		expect(r2['부문']).toBe('CE부문'); // rowspan forward-fill
		expect(r2['품목']).toBe('메모리');
		expect(r2['매입액']).toBe('19,930');
		expect(r2['비중']).toBe('9.4%');
		expect(r2['매입처']).toBe('Micron 등');
	});

	it('headerRow 파라미터 (메타행 회피)', () => {
		const g = [['(단위: 억원)', '(단위: 억원)'], ['품목', '매입액'], ['A', '10']];
		expect(gridToRowDicts(g, 1)).toEqual([{ 품목: 'A', 매입액: '10' }]);
	});

	it('빈/단행 = []', () => {
		expect(expandTables('')).toEqual([]);
		expect(expandTables('<TABLE><TR><TD>x</TD></TR></TABLE>')).toEqual([]);
		expect(gridToRowDicts([])).toEqual([]);
	});
});
