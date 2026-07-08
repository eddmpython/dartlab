import type { Cell } from '../stores/notebookStore';

export interface MarimoParseResult {
	cells: Cell[];
	appConfig: Record<string, unknown>;
	errors: string[];
}

interface RawCellBlock {
	decorator: string;
	funcName: string;
	params: string[];
	bodyLines: string[];
	isHidden: boolean;
}

export function parseMarimoFile(source: string): MarimoParseResult {
	const errors: string[] = [];
	const appConfig: Record<string, unknown> = {};

	const lines = source.replace(/\r\n/g, '\n').split('\n');

	const appMatch = source.match(/marimo\.App\(([^)]*)\)/);
	if (appMatch && appMatch[1].trim()) {
		try {
			const configStr = appMatch[1].trim();
			const widthMatch = configStr.match(/width\s*=\s*["']([^"']+)["']/);
			if (widthMatch) appConfig.width = widthMatch[1];
			const titleMatch = configStr.match(/app_title\s*=\s*["']([^"']+)["']/);
			if (titleMatch) appConfig.title = titleMatch[1];
		} catch {
			errors.push('Failed to parse App() config');
		}
	}

	const rawBlocks = extractCellBlocks(lines, errors);
	const cells = rawBlocks.map((block) => convertBlockToCell(block));

	if (cells.length === 0) {
		cells.push({
			id: crypto.randomUUID(),
			type: 'code',
			content: ''
		});
	}

	return { cells, appConfig, errors };
}

function extractCellBlocks(lines: string[], errors: string[]): RawCellBlock[] {
	const blocks: RawCellBlock[] = [];
	let i = 0;

	while (i < lines.length) {
		const line = lines[i];
		const trimmed = line.trim();

		if (trimmed === '@app.cell' || trimmed === '@app.cell()' || trimmed.startsWith('@app.cell(')) {
			const decorator = trimmed;
			const isHidden = decorator.includes('hide_code=True') || decorator.includes('hide_code = True');
			i++;

			while (i < lines.length && lines[i].trim() === '') i++;

			if (i >= lines.length) {
				errors.push('Unexpected end of file after @app.cell decorator');
				break;
			}

			const defLine = lines[i].trim();
			const defMatch = defLine.match(/^def\s+(\w+)\s*\(([^)]*)\)\s*:/);
			if (!defMatch) {
				errors.push(`Expected function definition after @app.cell, got: ${defLine}`);
				i++;
				continue;
			}

			const funcName = defMatch[1];
			const paramStr = defMatch[2].trim();
			const params = paramStr
				? paramStr.split(',').map((p) => p.trim()).filter(Boolean)
				: [];
			i++;

			const bodyLines: string[] = [];
			let baseIndent = -1;

			while (i < lines.length) {
				const bodyLine = lines[i];

				if (bodyLine.trim() === '' && i + 1 < lines.length) {
					const nextNonEmpty = findNextNonEmptyLine(lines, i + 1);
					if (nextNonEmpty === -1) break;
					const nextTrimmed = lines[nextNonEmpty].trim();
					if (nextTrimmed.startsWith('@app.cell') || nextTrimmed.startsWith('if __name__')) break;

					const nextIndent = getIndent(lines[nextNonEmpty]);
					if (baseIndent >= 0 && nextIndent <= 0) break;

					bodyLines.push('');
					i++;
					continue;
				}

				if (bodyLine.trim() === '') {
					bodyLines.push('');
					i++;
					continue;
				}

				const currentIndent = getIndent(bodyLine);

				if (baseIndent < 0) {
					baseIndent = currentIndent;
				}

				if (currentIndent < baseIndent && bodyLine.trim() !== '') {
					break;
				}

				bodyLines.push(bodyLine);
				i++;
			}

			blocks.push({
				decorator,
				funcName,
				params,
				bodyLines,
				isHidden
			});
		} else {
			i++;
		}
	}

	return blocks;
}

function convertBlockToCell(block: RawCellBlock): Cell {
	const baseIndent = findBaseIndent(block.bodyLines);
	const dedented = block.bodyLines.map((line) => {
		if (line.trim() === '') return '';
		return line.slice(Math.min(baseIndent, getIndent(line)));
	});

	const cleaned = removeReturnStatement(dedented);
	const trimmed = trimTrailingEmptyLines(cleaned);

	const isMdCell = detectMarkdownCell(trimmed);

	const content = trimmed.join('\n');

	const cell: Cell = {
		id: crypto.randomUUID(),
		type: isMdCell ? 'markdown' : 'code',
		content: isMdCell ? extractMarkdownContent(content) : content
	};

	return cell;
}

function removeReturnStatement(lines: string[]): string[] {
	const result = [...lines];

	for (let i = result.length - 1; i >= 0; i--) {
		const trimmed = result[i].trim();
		if (trimmed === '') continue;

		if (trimmed.match(/^return\s*\(\s*\)\s*$/)) {
			result.splice(i, 1);
			break;
		}

		const returnMatch = trimmed.match(/^return\s*\((.+)\)\s*$/);
		if (returnMatch) {
			result.splice(i, 1);
			break;
		}

		if (trimmed.startsWith('return ') || trimmed === 'return') {
			result.splice(i, 1);
			break;
		}

		break;
	}

	return result;
}

function detectMarkdownCell(lines: string[]): boolean {
	const code = lines.join('\n').trim();

	if (code.match(/^\s*mo\.md\s*\(\s*(?:f\s*)?(?:"""|'''|"|')/)) {
		const nonMdLines = lines.filter((l) => {
			const t = l.trim();
			return t !== '' && !t.startsWith('mo.md(') && !t.startsWith(')') &&
				!t.startsWith('"""') && !t.startsWith("'''");
		});
		if (nonMdLines.length === 0 || code.startsWith('mo.md(')) return true;
	}

	return false;
}

function extractMarkdownContent(code: string): string {
	const tripleDoubleMatch = code.match(/mo\.md\s*\(\s*(?:f\s*)?"""([\s\S]*?)"""\s*\)/);
	if (tripleDoubleMatch) return tripleDoubleMatch[1].trim();

	const tripleSingleMatch = code.match(/mo\.md\s*\(\s*(?:f\s*)?'''([\s\S]*?)'''\s*\)/);
	if (tripleSingleMatch) return tripleSingleMatch[1].trim();

	const doubleMatch = code.match(/mo\.md\s*\(\s*(?:f\s*)?"([^"]*?)"\s*\)/);
	if (doubleMatch) return doubleMatch[1].trim();

	const singleMatch = code.match(/mo\.md\s*\(\s*(?:f\s*)?'([^']*?)'\s*\)/);
	if (singleMatch) return singleMatch[1].trim();

	return code;
}

function findBaseIndent(lines: string[]): number {
	let minIndent = Infinity;
	for (const line of lines) {
		if (line.trim() === '') continue;
		const indent = getIndent(line);
		if (indent < minIndent) minIndent = indent;
	}
	return minIndent === Infinity ? 0 : minIndent;
}

function getIndent(line: string): number {
	let count = 0;
	for (const ch of line) {
		if (ch === ' ') count++;
		else if (ch === '\t') count += 4;
		else break;
	}
	return count;
}

function findNextNonEmptyLine(lines: string[], startIdx: number): number {
	for (let i = startIdx; i < lines.length; i++) {
		if (lines[i].trim() !== '') return i;
	}
	return -1;
}

function trimTrailingEmptyLines(lines: string[]): string[] {
	const result = [...lines];
	while (result.length > 0 && result[result.length - 1].trim() === '') {
		result.pop();
	}
	return result;
}

export function filterMarimoImportCell(cells: Cell[]): Cell[] {
	return cells.filter((cell) => {
		if (cell.type !== 'code') return true;
		const trimmed = cell.content.trim();
		if (trimmed === 'import marimo as mo') return false;
		if (trimmed === 'import marimo') return false;
		return true;
	});
}
