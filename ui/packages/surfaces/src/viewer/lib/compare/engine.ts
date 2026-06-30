// Compare module entrypoint for viewer surfaces.
// 재무 섹션도 다른 섹션과 동일하게 행 모드 · 각 회사의 표(재무상태표/손익계산서 등)를 통째로
// 나란히 보여준다(요약재무와 동일). 옛 isFinanceSection→셀(계정별 acode 분해) 분기는 제거
// (운영자 요청 "계정간 비교 말고 각 회사 표 그대로", 2026-06). 단일 뷰어가 activeBlock 으로
// 필터하던 것과 동일하게 block 을 받아 클릭한 블록만 비교한다.

import type { PanelBundle } from '../types';
import { compareRows } from './rowCompare';
import type { CompareBoard } from './types';

export interface BuildCompareBoardOptions {
	sectionKey: string;
	period: string;
	block?: string | null; // 활성 블록(예: "연결 재무상태표") · 그 블록만 비교
}

export function buildCompareBoard(bundles: PanelBundle[], opts: BuildCompareBoardOptions): CompareBoard {
	const row = compareRows(bundles, opts.sectionKey, opts.period, opts.block ?? null);
	return { mode: 'row', rows: row.rows, diagnostics: row.diagnostics };
}
