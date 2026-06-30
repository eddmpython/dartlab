// Viewer compare model · 회사 비교 surface. 각 회사의 섹션/블록 콘텐츠를 열로 병치한다
// (계정/키 분해 없음). null 셀 = honest-gap(그 회사엔 해당 공시 없음).

export const COMPARE_SEP = '␟';

export type ShareClass = 'shared' | 'partial' | 'solo';

export interface CompareDiagnostics {
	mode: 'row';
	period: string;
	rowCount: number;
	sharedRows: number;
	partialRows: number;
	soloRows: number;
	narrativePolicy?: 'company-row';
}

export interface AlignedRow {
	alignKey: string;
	label: string; // 자기 식별 라벨 = blockLeaf || sectionLeaf || disclosureKey
	disclosureKey: string | null;
	scope: string | null;
	leafType: string;
	blockType: 'text' | 'table';
	cells: (string | null)[]; // company index -> 셀 본문; null = honest-gap
	shareClass: ShareClass;
}

export interface CompareBoard {
	mode: 'row';
	rows: AlignedRow[];
	diagnostics: CompareDiagnostics;
}
