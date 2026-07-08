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
		} else if (cell.type === 'guide') {
			jCells.push({
				cell_type: 'markdown',
				id: sanitizeCellId(cell.id),
				source: guideToMarkdown(cell),
				metadata: {}
			});
		} else if (cell.type === 'study') {
			jCells.push({
				cell_type: 'markdown',
				id: sanitizeCellId(cell.id),
				source: studyToMarkdown(cell),
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

function guideToMarkdown(cell: Cell): string {
	const parts: string[] = [];
	const guide = cell.guide;

	if (guide?.mission) {
		parts.push(`**Mission:** ${guide.mission}`);
	}

	if (guide?.hints && guide.hints.length > 0) {
		parts.push('');
		parts.push('<details><summary>Hints</summary>');
		parts.push('');
		guide.hints.forEach((hint, i) => {
			parts.push(`${i + 1}. ${hint}`);
		});
		parts.push('');
		parts.push('</details>');
	}

	if (guide?.answer) {
		parts.push('');
		parts.push('<details><summary>Answer</summary>');
		parts.push('');
		parts.push('```python');
		parts.push(guide.answer);
		parts.push('```');
		parts.push('');
		parts.push('</details>');
	}

	if (cell.content && !guide?.mission) {
		parts.push(cell.content);
	}

	return parts.join('\n');
}

function studyToMarkdown(cell: Cell): string {
	const study = cell.study;
	if (!study) return '';
	const block = study.block;
	const parts: string[] = [];

	if (study.blockType === 'intro') {
		const title = (block.title as string) || (block.metaTitle as string) || '';
		if (title) parts.push(`# ${title}`);
		if (block.goal) parts.push(`**${block.goal}**`);
		if (block.description) parts.push(block.description as string);
	} else if (study.blockType === 'sectionDivider') {
		const idx = study.sectionIndex ?? 0;
		parts.push(`## ${idx + 1}. ${block.title || ''}`);
		if (block.subtitle) parts.push(`*${block.subtitle}*`);
	} else if (study.blockType === 'code') {
		if (block.title) parts.push(`**${block.title}**`);
		if (block.description) parts.push(block.description as string);
		if (block.content) parts.push(`\`\`\`python\n${block.content}\n\`\`\``);
	} else if (study.blockType === 'tip') {
		const emoji = (block.emoji as string) || '💡';
		if (block.content) parts.push(`> ${emoji} ${block.content}`);
	} else if (study.blockType === 'list') {
		const items = (block.items as string[]) || [];
		parts.push(items.map((item) => `- ${item}`).join('\n'));
	} else if (study.blockType === 'table') {
		const headers = (block.headers as string[]) || [];
		const rows = (block.rows as string[][]) || [];
		if (headers.length > 0) {
			parts.push(`| ${headers.join(' | ')} |`);
			parts.push(`| ${headers.map(() => '---').join(' | ')} |`);
			for (const row of rows) {
				parts.push(`| ${row.join(' | ')} |`);
			}
		}
	} else if (study.blockType === 'footer') {
		if (block.title) parts.push(`## ${block.title}`);
		if (block.description) parts.push(block.description as string);
	} else {
		if (block.title) parts.push(`### ${block.title}`);
		if (block.content) parts.push(block.content as string);
		if (block.description) parts.push(block.description as string);
	}

	return parts.join('\n\n') || `[${study.blockType}]`;
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
