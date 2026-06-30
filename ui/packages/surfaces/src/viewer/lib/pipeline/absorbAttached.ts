// (첨부) 물리 재무첨부 흡수 + 섹션 번호 정렬키 (Python read.absorbAttached / orderBySpine _secNum).

import type { LeafRow } from '../types';

// (첨부)연결재무제표·(첨부)재무제표 → 정규 재무섹션 흡수 (read.py absorbAttached 1:1). sectionPath(공백제거)에서
// 감지 → chapter→III, sectionLeaf→연결 "2."/별도 "4." (주석은 3./5.). 흡수행 blockOrder 를 크게 밀어(_skel 뒤로)
// 섹션 위치는 정규(XBRL) 행이 잡게 한다(섹션 앞으로 끌림 차단).
export function absorbAttachedRow(r: LeafRow): void {
	const path = (r.sectionPath ?? '').replace(/\s+/g, '');
	if (!(path.includes('(첨부)') && path.includes('재무제표'))) return;
	const consol = path.includes('연결');
	const note = (r.sectionLeaf ?? '').includes('주석');
	r.chapter = 'III. 재무에 관한 사항';
	r.sectionLeaf = note ? (consol ? '3. 연결재무제표 주석' : '5. 재무제표 주석') : consol ? '2. 연결재무제표' : '4. 재무제표';
	if (r.blockOrder != null) r.blockOrder += 1_000_000;
}

// 섹션 번호 정렬키 · "2. …"→2, "7-1. …"→[7,1]. 번호 없으면 null(nulls_last). orderBySpine _secNum/_secSub 1:1.
export function sectionNum(sectionLeaf: string): [number | null, number] {
	const m = /^\s*(\d+)/.exec(sectionLeaf);
	const sub = /^\s*\d+\s*-\s*(\d+)/.exec(sectionLeaf);
	return [m ? parseInt(m[1], 10) : null, sub ? parseInt(sub[1], 10) : 0];
}
