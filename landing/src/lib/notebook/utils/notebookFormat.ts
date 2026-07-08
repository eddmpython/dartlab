import type { Notebook } from '../stores/notebookStore';
import { parseMarimoFile, filterMarimoImportCell } from './marimoParser';
import { writeMarimoFile, type MarimoWriteOptions } from './marimoWriter';
import { parseJupyterFile } from './jupyterParser';
import { writeJupyterFile, type JupyterWriteOptions } from './jupyterWriter';

export function serializeNotebook(nb: Notebook): string {
	return JSON.stringify(nb, null, 2);
}

export function deserializeNotebook(json: string): Notebook {
	return JSON.parse(json);
}

export function downloadNotebook(nb: Notebook): void {
	const json = serializeNotebook(nb);
	const blob = new Blob([json], { type: 'application/json' });
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = `${nb.title || 'notebook'}.json`;
	a.click();
	URL.revokeObjectURL(url);
}

export function importMarimoNotebook(source: string, filename?: string): Notebook {
	const result = parseMarimoFile(source);
	const cells = filterMarimoImportCell(result.cells);

	const title = filename
		? filename.replace(/\.py$/, '')
		: (result.appConfig.title as string) || 'Imported';

	return {
		id: crypto.randomUUID(),
		title,
		cells: cells.length > 0 ? cells : [{ id: crypto.randomUUID(), type: 'code' as const, content: '' }],
		metadata: {
			createdAt: new Date().toISOString(),
			updatedAt: new Date().toISOString()
		}
	};
}

export function exportAsMarimoFile(nb: Notebook): string {
	const options: MarimoWriteOptions = {};
	if (nb.title && nb.title !== 'Untitled') options.appTitle = nb.title;
	return writeMarimoFile(nb.cells, options);
}

export function downloadAsMarimoFile(nb: Notebook): void {
	const content = exportAsMarimoFile(nb);
	const blob = new Blob([content], { type: 'text/x-python' });
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = `${nb.title || 'notebook'}.py`;
	a.click();
	URL.revokeObjectURL(url);
}

export function openFileDialog(accept: string): Promise<File | null> {
	return new Promise((resolve) => {
		const input = document.createElement('input');
		input.type = 'file';
		input.accept = accept;
		input.onchange = () => resolve(input.files?.[0] ?? null);
		input.addEventListener('cancel', () => resolve(null));

		const onFocus = () => {
			setTimeout(() => {
				if (!input.files?.length) resolve(null);
				window.removeEventListener('focus', onFocus);
			}, 500);
		};
		window.addEventListener('focus', onFocus, { once: true });

		input.click();
	});
}

export async function readFileAsText(file: File): Promise<string> {
	return new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.onload = () => resolve(reader.result as string);
		reader.onerror = () => reject(reader.error);
		reader.readAsText(file);
	});
}

export function importJupyterNotebook(jsonStr: string, filename?: string): Notebook {
	const result = parseJupyterFile(jsonStr);

	const title = filename
		? filename.replace(/\.ipynb$/, '')
		: 'Imported';

	return {
		id: crypto.randomUUID(),
		title,
		cells: result.cells.length > 0 ? result.cells : [{ id: crypto.randomUUID(), type: 'code' as const, content: '' }],
		metadata: {
			createdAt: new Date().toISOString(),
			updatedAt: new Date().toISOString()
		}
	};
}

export function exportAsJupyterFile(nb: Notebook, options: JupyterWriteOptions = {}): string {
	return writeJupyterFile(nb.cells, options);
}

export function downloadAsJupyterFile(nb: Notebook, options: JupyterWriteOptions = {}): void {
	const content = exportAsJupyterFile(nb, options);
	const blob = new Blob([content], { type: 'application/x-ipynb+json' });
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = `${nb.title || 'notebook'}.ipynb`;
	a.click();
	URL.revokeObjectURL(url);
}
