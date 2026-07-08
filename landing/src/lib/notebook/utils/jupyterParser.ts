import type { Cell, CellOutput } from '../stores/notebookStore';

interface JupyterNotebook {
	nbformat: number;
	nbformat_minor: number;
	metadata: Record<string, unknown>;
	cells: JupyterCell[];
}

interface JupyterCell {
	cell_type: 'code' | 'markdown' | 'raw';
	id?: string;
	source: string | string[];
	metadata: Record<string, unknown>;
	execution_count?: number | null;
	outputs?: JupyterOutput[];
}

interface JupyterOutput {
	output_type: 'stream' | 'display_data' | 'execute_result' | 'error';
	name?: string;
	text?: string | string[];
	data?: Record<string, unknown>;
	metadata?: Record<string, unknown>;
	execution_count?: number;
	ename?: string;
	evalue?: string;
	traceback?: string[];
}

export interface JupyterParseResult {
	cells: Cell[];
	metadata: Record<string, unknown>;
	errors: string[];
}

export function parseJupyterFile(jsonStr: string): JupyterParseResult {
	const errors: string[] = [];

	let raw: JupyterNotebook;
	try {
		raw = JSON.parse(jsonStr);
	} catch (e) {
		return { cells: [], metadata: {}, errors: ['Invalid JSON: ' + (e as Error).message] };
	}

	if (raw.nbformat !== 4) {
		errors.push(`Unsupported nbformat version: ${raw.nbformat} (expected 4)`);
	}

	if (!Array.isArray(raw.cells)) {
		return { cells: [], metadata: raw.metadata || {}, errors: ['No cells array found'] };
	}

	const cells: Cell[] = [];

	for (let i = 0; i < raw.cells.length; i++) {
		const jCell = raw.cells[i];
		const source = normalizeSource(jCell.source);

		if (jCell.cell_type === 'code') {
			const cell: Cell = {
				id: jCell.id || crypto.randomUUID(),
				type: 'code',
				content: source,
				executionCount: typeof jCell.execution_count === 'number' ? jCell.execution_count : undefined
			};

			const output = convertOutputs(jCell.outputs || []);
			if (output) {
				cell.output = output;
			}

			cells.push(cell);
		} else if (jCell.cell_type === 'markdown') {
			cells.push({
				id: jCell.id || crypto.randomUUID(),
				type: 'markdown',
				content: source
			});
		} else if (jCell.cell_type === 'raw') {
			cells.push({
				id: jCell.id || crypto.randomUUID(),
				type: 'code',
				content: source
			});
		}
	}

	if (cells.length === 0) {
		cells.push({ id: crypto.randomUUID(), type: 'code', content: '' });
	}

	return { cells, metadata: raw.metadata || {}, errors };
}

function normalizeSource(source: string | string[]): string {
	if (Array.isArray(source)) return source.join('');
	return source;
}

function convertOutputs(outputs: JupyterOutput[]): CellOutput | null {
	if (outputs.length === 0) return null;

	const textParts: string[] = [];
	let errorOutput: CellOutput | null = null;
	let htmlOutput: CellOutput | null = null;
	let imageOutput: CellOutput | null = null;

	for (const out of outputs) {
		if (out.output_type === 'stream') {
			textParts.push(normalizeSource(out.text || ''));
		} else if (out.output_type === 'error') {
			const tb = (out.traceback || [])
				.map((line) => stripAnsi(line))
				.join('\n');
			errorOutput = {
				type: 'error',
				data: `${out.ename}: ${out.evalue}\n${tb}`,
				executedAt: new Date().toISOString()
			};
		} else if (out.output_type === 'execute_result' || out.output_type === 'display_data') {
			const data = out.data || {};

			if (data['image/png']) {
				imageOutput = {
					type: 'image',
					data: `data:image/png;base64,${data['image/png']}`,
					executedAt: new Date().toISOString()
				};
			} else if (data['image/svg+xml']) {
				htmlOutput = {
					type: 'html',
					data: normalizeSource(data['image/svg+xml'] as string | string[]),
					executedAt: new Date().toISOString()
				};
			} else if (data['text/html']) {
				htmlOutput = {
					type: 'html',
					data: normalizeSource(data['text/html'] as string | string[]),
					executedAt: new Date().toISOString()
				};
			} else if (data['text/plain']) {
				textParts.push(normalizeSource(data['text/plain'] as string | string[]));
			}
		}
	}

	if (errorOutput) return errorOutput;
	if (imageOutput) {
		if (textParts.length > 0) {
			imageOutput.data = textParts.join('') + '__STDOUT_END__\n' + imageOutput.data;
		}
		return imageOutput;
	}
	if (htmlOutput) return htmlOutput;
	if (textParts.length > 0) {
		return {
			type: 'text',
			data: textParts.join(''),
			executedAt: new Date().toISOString()
		};
	}

	return null;
}

function stripAnsi(str: string): string {
	return str.replace(/\x1b\[[0-9;]*[a-zA-Z]/g, '');
}
