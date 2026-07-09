import type { Cell } from '../stores/notebookStore';

interface JupyterNotebook {
	nbformat: number;
	nbformat_minor: number;
	metadata: Record<string, unknown>;
	cells: JupyterCell[];
}

interface JupyterCell {
	cell_type: 'code' | 'markdown' | 'raw';
	id: string;
	source: string;
	metadata: Record<string, unknown>;
	execution_count?: number | null;
	outputs?: JupyterOutput[];
}

interface JupyterOutput {
	output_type: string;
	name?: string;
	text?: string;
	data?: Record<string, unknown>;
	metadata?: Record<string, unknown>;
	execution_count?: number;
	ename?: string;
	evalue?: string;
	traceback?: string[];
}

export interface JupyterWriteOptions {
	includeOutputs?: boolean;
	kernelName?: string;
}

export function writeJupyterFile(cells: Cell[], options: JupyterWriteOptions = {}): string {
	const includeOutputs = options.includeOutputs !== false;
	const kernelName = options.kernelName || 'python3';

	const jCells: JupyterCell[] = [];

	for (const cell of cells) {
		if (cell.type === 'code') {
			const jCell: JupyterCell = {
				cell_type: 'code',
				id: sanitizeCellId(cell.id),
				source: cell.content,
				metadata: {},
				execution_count: cell.executionCount ?? null,
				outputs: []
			};

			if (includeOutputs && cell.output) {
				jCell.outputs = convertOutput(cell.output);
			}

			jCells.push(jCell);
		} else if (cell.type === 'markdown') {
			jCells.push({
				cell_type: 'markdown',
				id: sanitizeCellId(cell.id),
				source: cell.content,
				metadata: {}
			});
		}
	}

	const nb: JupyterNotebook = {
		nbformat: 4,
		nbformat_minor: 5,
		metadata: {
			kernelspec: {
				display_name: 'Python 3',
				language: 'python',
				name: kernelName
			},
			language_info: {
				name: 'python',
				version: '3.12.0'
			}
		},
		cells: jCells
	};

	return JSON.stringify(nb, null, 1);
}

function convertOutput(output: Cell['output']): JupyterOutput[] {
	if (!output) return [];

	const stdoutSep = '__STDOUT_END__\n';

	if (output.type === 'error') {
		const lines = output.data.split('\n');
		const firstLine = lines[0] || '';
		const colonIdx = firstLine.indexOf(':');
		const ename = colonIdx > 0 ? firstLine.slice(0, colonIdx).trim() : 'Error';
		const evalue = colonIdx > 0 ? firstLine.slice(colonIdx + 1).trim() : firstLine;

		return [{
			output_type: 'error',
			ename,
			evalue,
			traceback: lines
		}];
	}

	if (output.type === 'image') {
		const results: JupyterOutput[] = [];
		let imgData = output.data;

		const sepIdx = imgData.indexOf(stdoutSep);
		if (sepIdx !== -1) {
			const stdout = imgData.slice(0, sepIdx);
			imgData = imgData.slice(sepIdx + stdoutSep.length);
			if (stdout) {
				results.push({ output_type: 'stream', name: 'stdout', text: stdout });
			}
		}

		const base64Match = imgData.match(/^data:image\/png;base64,(.+)$/);
		if (base64Match) {
			results.push({
				output_type: 'display_data',
				data: { 'image/png': base64Match[1], 'text/plain': '<Figure>' },
				metadata: {}
			});
		} else {
			results.push({
				output_type: 'display_data',
				data: { 'text/plain': imgData },
				metadata: {}
			});
		}

		return results;
	}

	if (output.type === 'html') {
		return [{
			output_type: 'display_data',
			data: { 'text/html': output.data, 'text/plain': '<HTML>' },
			metadata: {}
		}];
	}

	if (output.type === 'text' || output.type === 'dataframe' || output.type === 'widget') {
		return [{
			output_type: 'stream',
			name: 'stdout',
			text: output.data
		}];
	}

	return [];
}

function sanitizeCellId(id: string): string {
	const cleaned = id.replace(/[^a-zA-Z0-9\-_]/g, '');
	if (cleaned.length === 0) return crypto.randomUUID().replace(/-/g, '').slice(0, 8);
	return cleaned.slice(0, 64);
}

export function downloadAsJupyterFile(cells: Cell[], filename: string, options: JupyterWriteOptions = {}): void {
	const content = writeJupyterFile(cells, options);
	const blob = new Blob([content], { type: 'application/x-ipynb+json' });
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = filename.endsWith('.ipynb') ? filename : `${filename}.ipynb`;
	a.click();
	URL.revokeObjectURL(url);
}
