import type { Cell } from '../stores/notebookStore';

export interface SectionGroup {
	id: string;
	sectionIndex: number;
	headerCell: Cell;
	learnCells: Cell[];
	practiceCells: Cell[];
}

export interface StudySections {
	preSectionCells: Cell[];
	sections: SectionGroup[];
	postSectionCells: Cell[];
}

export interface GroupOptions {
	learnOnly?: boolean;
}

function isUserCodeCell(cell: Cell): boolean {
	return (cell.type === 'code' || cell.type === 'guide') && !cell.study;
}

function isStudyContentCell(cell: Cell): boolean {
	return cell.type === 'study' || (cell.type === 'markdown' && !!cell.study);
}

export function groupStudyCells(cells: Cell[], options?: GroupOptions): StudySections {
	const preSectionCells: Cell[] = [];
	const sections: SectionGroup[] = [];
	const postSectionCells: Cell[] = [];

	let current: SectionGroup | null = null;
	let seenFirstSection = false;

	for (const cell of cells) {
		const isSectionDivider =
			cell.type === 'study' && cell.study?.blockType === 'sectionDivider';

		if (isSectionDivider) {
			if (current) sections.push(current);
			seenFirstSection = true;
			current = {
				id: cell.id,
				sectionIndex: cell.study!.sectionIndex ?? sections.length,
				headerCell: cell,
				learnCells: [],
				practiceCells: []
			};
			continue;
		}

		if (!seenFirstSection) {
			preSectionCells.push(cell);
			continue;
		}

		const isFooter =
			cell.type === 'study' && cell.study?.blockType === 'footer';

		if (isFooter) {
			if (current) {
				sections.push(current);
				current = null;
			}
			postSectionCells.push(cell);
			continue;
		}

		if (!current) {
			postSectionCells.push(cell);
			continue;
		}

		if (isUserCodeCell(cell)) {
			if (!options?.learnOnly) {
				current.practiceCells.push(cell);
			}
		} else if (isStudyContentCell(cell)) {
			current.learnCells.push(cell);
		} else if (cell.type === 'markdown') {
			current.learnCells.push(cell);
		} else {
			current.practiceCells.push(cell);
		}
	}

	if (current) sections.push(current);

	return { preSectionCells, sections, postSectionCells };
}
