import type { Cell } from '../stores/notebookStore';
import { analyzeCell } from '../engine/dataflow';

export interface MarimoWriteOptions {
	appTitle?: string;
	appWidth?: string;
}

export function writeMarimoFile(cells: Cell[], options: MarimoWriteOptions = {}): string {
	const parts: string[] = [];

	parts.push(generateHeader(options));
	parts.push(generateImportCell());

	const codeCells = cells.filter((c) => c.type === 'code' || c.type === 'markdown');

	const allDefines = new Map<string, string>();
	for (const cell of codeCells) {
		if (cell.type !== 'code') continue;
		const analysis = analyzeCell(cell.id, cell.content);
		for (const varName of analysis.defines) {
			allDefines.set(varName, cell.id);
		}
	}

	for (const cell of codeCells) {
		if (cell.type === 'markdown') {
			parts.push(generateMarkdownCell(cell));
		} else {
			parts.push(generateCodeCell(cell, allDefines));
		}
	}

	parts.push(generateFooter());

	return parts.join('\n\n');
}

function generateHeader(options: MarimoWriteOptions): string {
	const configParts: string[] = [];
	if (options.appTitle) configParts.push(`app_title="${options.appTitle}"`);
	if (options.appWidth) configParts.push(`width="${options.appWidth}"`);

	const configStr = configParts.length > 0 ? configParts.join(', ') : '';

	return `import marimo

app = marimo.App(${configStr})`;
}

function generateImportCell(): string {
	return `@app.cell
def _():
    import marimo as mo
    return (mo,)`;
}

function generateCodeCell(cell: Cell, allDefines: Map<string, string>): string {
	const analysis = analyzeCell(cell.id, cell.content);

	const params: string[] = [];
	for (const varName of analysis.uses) {
		if (allDefines.has(varName) && allDefines.get(varName) !== cell.id) {
			params.push(varName);
		}
	}

	const usesMo = cell.content.includes('mo.');
	if (usesMo && !params.includes('mo')) {
		params.unshift('mo');
	}

	const defines = Array.from(analysis.defines);

	const indented = cell.content
		.split('\n')
		.map((line) => (line.trim() === '' ? '' : `    ${line}`))
		.join('\n');

	const returnLine = defines.length > 0
		? `    return (${defines.join(', ')},)`
		: '    return';

	const paramStr = params.length > 0 ? params.join(', ') : '';

	return `@app.cell
def _(${paramStr}):
${indented}
${returnLine}`;
}

function generateMarkdownCell(cell: Cell): string {
	const content = cell.content;
	const escaped = content.replace(/\\/g, '\\\\').replace(/"""/g, '\\"\\"\\"');
	const indentedContent = escaped.split('\n').map((line) => (line.trim() === '' ? '' : `    ${line}`)).join('\n');

	return `@app.cell
def _(mo):
    mo.md(
        """
${indentedContent}
        """
    )
    return`;
}


function generateFooter(): string {
	return `if __name__ == "__main__":
    app.run()`;
}

export function downloadAsMarimoFile(cells: Cell[], filename: string, options: MarimoWriteOptions = {}): void {
	const content = writeMarimoFile(cells, options);
	const blob = new Blob([content], { type: 'text/x-python' });
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = filename.endsWith('.py') ? filename : `${filename}.py`;
	a.click();
	URL.revokeObjectURL(url);
}
