// Company compare · 단일 뷰어를 회사별로 미러한다. 각 회사의 이 섹션(+활성 블록) 콘텐츠를
// 자기 열에 통째로 보여줄 뿐, 계정/키 단위로 쪼개거나 회사 간 행 정렬을 하지 않는다
// (운영자 요청: "계정간 비교 말고 각 회사 표 그대로 나란히" = 요약재무 방식). 절번호 drift로
// 같은 sectionKey 가 없는 회사는 기준 블록의 disclosureKey 로 전역 조회해 누락을 막는다.

import type { PanelBundle, PanelRow } from '../types';
import { COMPARE_SEP, type AlignedRow, type CompareDiagnostics } from './types';
import { bundleIndex } from './bundleIndex';

function shareClass(cells: (string | null)[]): 'shared' | 'partial' | 'solo' {
	const present = cells.filter((c) => c != null).length;
	return present >= cells.length ? 'shared' : present > 1 ? 'partial' : 'solo';
}

export interface RowCompareResult {
	rows: AlignedRow[];
	diagnostics: CompareDiagnostics;
}

function combineCells(rows: PanelRow[], period: string): string | null {
	const joined = rows
		.map((r) => r.cells?.[period])
		.filter((c): c is string => typeof c === 'string' && c.trim() !== '')
		.join('\n');
	return joined !== '' ? joined : null;
}

// 한 회사의 이 섹션(+활성 블록) content-bearing 행. sectionKey 가 없으면(절번호 drift)
// 기준 블록의 disclosureKey 로 전역 조회해 누락 방지.
function sectionRowsFor(b: PanelBundle, sectionKey: string, block: string | null, baseDks: Set<string>): PanelRow[] {
	let leaves = b.gridBySection.get(sectionKey) ?? [];
	if (block) leaves = leaves.filter((r) => r.blockLeaf === block);
	if (leaves.length === 0 && baseDks.size) {
		const idx = bundleIndex(b);
		leaves = [...baseDks].flatMap((dk) => idx.byDisclosureKey.get(dk) ?? []);
	}
	return leaves;
}

// N 회사를 한 시점에 비교. 결과 = 한 행(회사 = 열), 각 셀 = 그 회사의 섹션/블록 콘텐츠 통째.
// null 셀 = honest-gap(그 회사엔 해당 공시 없음).
export function compareRows(
	bundles: PanelBundle[],
	sectionKey: string,
	period: string,
	block: string | null = null
): RowCompareResult {
	const base = bundles[0];
	let baseRows = base?.gridBySection.get(sectionKey) ?? [];
	if (block) baseRows = baseRows.filter((r) => r.blockLeaf === block);
	const baseDks = new Set(baseRows.map((r) => r.disclosureKey).filter((k): k is string => !!k));
	const cells = bundles.map((b) => combineCells(sectionRowsFor(b, sectionKey, block, baseDks), period));
	const label = block || (sectionKey.split(COMPARE_SEP).pop() ?? '');
	const rows: AlignedRow[] = cells.some((c) => c != null)
		? [
				{
					alignKey: `SEC${COMPARE_SEP}${block ?? sectionKey}`,
					label,
					disclosureKey: null,
					scope: null,
					leafType: 'text',
					blockType: 'text',
					cells,
					shareClass: shareClass(cells)
				}
			]
		: [];
	const sharedRows = rows.filter((r) => r.shareClass === 'shared').length;
	const partialRows = rows.filter((r) => r.shareClass === 'partial').length;
	return {
		rows,
		diagnostics: {
			mode: 'row',
			period,
			rowCount: rows.length,
			sharedRows,
			partialRows,
			soloRows: rows.length - sharedRows - partialRows,
			narrativePolicy: 'company-row'
		}
	};
}

export function alignBundles(bundles: PanelBundle[], sectionKey: string, period: string, block: string | null = null): AlignedRow[] {
	return compareRows(bundles, sectionKey, period, block).rows;
}

// TOC 점/회색처리 · 회사가 이 섹션/블록 콘텐츠를 가졌나(절번호 drift 시 disclosureKey 전역).
export function sectionPresence(bundles: PanelBundle[], sectionKey: string, block: string | null = null): boolean[] {
	const base = bundles[0];
	let baseRows = base?.gridBySection.get(sectionKey) ?? [];
	if (block) baseRows = baseRows.filter((r) => r.blockLeaf === block);
	const baseDks = new Set(baseRows.map((r) => r.disclosureKey).filter((k): k is string => !!k));
	return bundles.map((b) => sectionRowsFor(b, sectionKey, block, baseDks).length > 0);
}

// Common periods, latest first. Uses intersection first, then union fallback.
export function commonPeriods(bundles: PanelBundle[]): string[] {
	if (!bundles.length) return [];
	const sets = bundles.map((b) => new Set(b.periods));
	const inter = bundles[0].periods.filter((p) => sets.every((s) => s.has(p)));
	if (inter.length) return inter;
	const union = new Set<string>();
	for (const b of bundles) for (const p of b.periods) union.add(p);
	return [...union].sort((a, b) => (a < b ? 1 : a > b ? -1 : 0));
}
