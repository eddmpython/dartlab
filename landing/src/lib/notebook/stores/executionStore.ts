import { writable, get } from 'svelte/store';
import type { ExecutionEngine, CompletionItem, VariableInfo, PackageInfo, DocResult, FileEntry } from '../engine/executionEngine';
import { WorkerEngine } from '../engine/workerEngine';
import { notebook, applyCellExecutionResult, setCellOutput, focusNextCell, nextExecutionCount, saveToStorage, cellOutputs, setCellErrors } from './notebookStore';
import type { WorkspaceFile } from './notebookStore';
import { getReactiveCells, detectMultipleDefinitions } from '../engine/dataflow';
import { initWidgetBridge, registerWidgetCell, destroyWidgetBridge } from '../widgets/WidgetBridge';

export type EngineStatus = 'idle' | 'loading' | 'ready' | 'executing' | 'error';

export const engineStatus = writable<EngineStatus>('idle');
export const runningCellId = writable<string | null>(null);
export const engineError = writable<string | null>(null);
export const reactiveMode = writable<boolean>(true);
export const reactiveQueue = writable<Set<string>>(new Set());
export const executionDoneCounter = writable<number>(0);
export const notebookFilePath = writable<string>('/workspace/Untitled.py');

let engine: ExecutionEngine | null = null;
let syncTimer: ReturnType<typeof setTimeout> | null = null;

let executionQueue: Promise<void> = Promise.resolve();

function enqueueExecution(fn: () => Promise<void>): Promise<void> {
	executionQueue = executionQueue.then(fn, fn);
	return executionQueue;
}

function debouncedSync() {
	if (syncTimer) clearTimeout(syncTimer);
	syncTimer = setTimeout(() => { syncNotebookFile(); }, 2000);
}

export async function initEngine(autoRun = true): Promise<void> {
	if (engine?.isReady) return;

	engineStatus.set('loading');
	engineError.set(null);

	try {
		engine = new WorkerEngine();
		await engine.initialize();
		initWidgetBridge(
			async (widgetId, value) => {
				if (engine?.isReady) {
					await engine.updateWidgetValue(widgetId, value);
				}
			},
			async (cellId) => {
				await triggerWidgetReactive(cellId);
			}
		);
		engineStatus.set('ready');
	} catch (err) {
		engineStatus.set('error');
		engineError.set(String(err));
		return;
	}

	try {
		const nb = get(notebook);
		if (nb.metadata?.notebookFilePath) {
			notebookFilePath.set(nb.metadata.notebookFilePath);
		}
		if (nb.workspaceFiles?.length) {
			await restoreWorkspaceFiles(nb.workspaceFiles);
		}
		await syncNotebookFile();
	} catch {
		// workspace restore failed, engine still usable
	}

	if (autoRun) {
		try {
			const currentNb = get(notebook);
			const codeCells = currentNb.cells.filter((c) => c.type === 'code' && c.content.trim());
			if (codeCells.length > 0) {
				await executeAllCells(currentNb.cells);
			}
		} catch {
			// auto-run failed, engine still usable
		}
	}
}

async function executeSingleCell(cellId: string, code: string): Promise<boolean> {
	if (!engine?.isReady) return false;

	runningCellId.set(cellId);
	engineStatus.set('executing');

	const executionCount = nextExecutionCount();
	const startTime = performance.now();
	let success = true;
	let output: import('./notebookStore').CellOutput;

	try {
		output = await engine.execute(code);
		if (output.type === 'error') success = false;
		if (output.type === 'widget') {
			try {
				const sep = '__STDOUT_END__\n';
				let jsonStr = output.data;
				const sepIdx = output.data.indexOf(sep);
				if (sepIdx !== -1) jsonStr = output.data.slice(sepIdx + sep.length);
				const parsed = JSON.parse(jsonStr);
				if (parsed.id && parsed.__chani_widget__) {
					registerWidgetCell(parsed.id, cellId);
				}
			} catch { /* widget registration failed */ }
		}
	} catch (err) {
		output = {
			type: 'error',
			data: String(err),
			executedAt: new Date().toISOString()
		};
		success = false;
	} finally {
		const executionTime = performance.now() - startTime;
		applyCellExecutionResult(cellId, { output: output!, executionCount, executionTime });
		runningCellId.set(null);
	}
	return success;
}

async function runReactiveCells(triggeredCellId: string): Promise<void> {
	const nb = get(notebook);
	const cells = nb.cells.map((c) => ({ id: c.id, type: c.type, content: c.content }));
	const dependentCellIds = getReactiveCells(triggeredCellId, cells);

	if (dependentCellIds.length === 0) return;

	reactiveQueue.set(new Set(dependentCellIds));

	for (const depCellId of dependentCellIds) {
		const depCell = nb.cells.find((c) => c.id === depCellId);
		if (!depCell || depCell.type !== 'code' || !depCell.content.trim()) continue;

		const depSuccess = await executeSingleCell(depCellId, depCell.content);
		reactiveQueue.update((q) => {
			const next = new Set(q);
			next.delete(depCellId);
			return next;
		});

		if (!depSuccess) break;
	}

	reactiveQueue.set(new Set());
}

async function triggerWidgetReactive(definingCellId: string): Promise<void> {
	if (!engine?.isReady) return;

	return enqueueExecution(async () => {
		await runReactiveCells(definingCellId);
		engineStatus.set('ready');
	});
}

function refreshCellErrors(): Map<string, string[]> {
	const nb = get(notebook);
	const errors = detectMultipleDefinitions(nb.cells);
	setCellErrors(errors);
	return errors;
}

export async function executeCell(cellId: string, code: string, moveToNext = false): Promise<void> {
	if (!engine) {
		await initEngine(false);
	}

	if (!engine?.isReady) {
		setCellOutput(cellId, {
			type: 'error',
			data: 'Engine not ready. Please wait for initialization.',
			executedAt: new Date().toISOString()
		});
		return;
	}

	const errors = refreshCellErrors();
	if (errors.has(cellId)) {
		const conflictVars = errors.get(cellId)!.join(', ');
		setCellOutput(cellId, {
			type: 'error',
			data: `Multiple definitions error: [${conflictVars}] is defined in multiple cells.\nEach variable must be defined in exactly one cell (marimo-style reactive model).\nRename or remove the duplicate definition.`,
			executedAt: new Date().toISOString()
		});
		if (moveToNext) focusNextCell(cellId);
		return;
	}

	return enqueueExecution(async () => {
		const success = await executeSingleCell(cellId, code);

		if (success && get(reactiveMode)) {
			await runReactiveCells(cellId);
		}

		engineStatus.set('ready');
		saveToStorage();
		debouncedSync();
		executionDoneCounter.update((n) => n + 1);

		if (moveToNext) {
			focusNextCell(cellId);
		}
	});
}

export async function executeAllCells(cells: { id: string; type: string; content: string }[]): Promise<void> {
	refreshCellErrors();
	for (const cell of cells) {
		if (cell.type === 'code' && cell.content.trim()) {
			await executeCell(cell.id, cell.content);
		}
	}
}

export function destroyEngine(): void {
	if (syncTimer) {
		clearTimeout(syncTimer);
		syncTimer = null;
	}
	executionQueue = Promise.resolve();
	destroyWidgetBridge();
	engine?.destroy();
	engine = null;
	engineStatus.set('idle');
	runningCellId.set(null);
	engineError.set(null);
	reactiveQueue.set(new Set());
}

export async function getVariableNames(): Promise<string[]> {
	if (!engine?.isReady) return [];
	return engine.getVariableNames();
}

export async function getCompletions(objName: string): Promise<CompletionItem[]> {
	if (!engine?.isReady) return [];
	return engine.getCompletions(objName);
}

export async function getVariablesWithInfo(): Promise<VariableInfo[]> {
	if (!engine?.isReady) return [];
	return engine.getVariablesWithInfo();
}

export async function installPackage(packageName: string): Promise<void> {
	if (!engine?.isReady) return;
	await engine.installPackage(packageName);
}

export async function getInstalledPackages(): Promise<PackageInfo[]> {
	if (!engine?.isReady) return [];
	return engine.getInstalledPackages();
}

export async function getDocstring(name: string): Promise<DocResult | null> {
	if (!engine?.isReady) return null;
	return engine.getDocstring(name);
}

export async function listFiles(path: string): Promise<FileEntry[]> {
	if (!engine?.isReady) return [];
	return engine.listFiles(path);
}

export async function readFile(path: string): Promise<string> {
	if (!engine?.isReady) return '';
	return engine.readFile(path);
}

export async function writeFile(path: string, content: string): Promise<void> {
	if (!engine?.isReady) return;
	await engine.writeFile(path, content);
}

export async function mkdirFS(path: string): Promise<void> {
	if (!engine?.isReady) return;
	await engine.mkdir(path);
}

export async function removeFileFS(path: string): Promise<void> {
	if (!engine?.isReady) return;
	await engine.removeFile(path);
}

export async function renamePathFS(oldPath: string, newPath: string): Promise<void> {
	if (!engine?.isReady) return;
	const entries = await engine.listFiles(oldPath).catch(() => null);
	if (entries !== null) {
		await engine.mkdir(newPath);
		for (const entry of entries) {
			const childOld = entry.path;
			const childNew = newPath + '/' + entry.name;
			if (entry.isDir) {
				await renamePathFS(childOld, childNew);
			} else {
				const content = await engine.readFile(childOld);
				await engine.writeFile(childNew, content);
			}
		}
		await engine.removeFile(oldPath);
	} else {
		const content = await engine.readFile(oldPath);
		await engine.writeFile(newPath, content);
		await engine.removeFile(oldPath);
	}
}

function sanitizePart(part: string): string {
	return part.replace(/[<>:"|?*\x00-\x1f]/g, '_').trim() || 'Untitled';
}

async function ensureDirs(dir: string): Promise<void> {
	if (!engine?.isReady || dir === '/workspace') return;
	const parts = dir.split('/').filter(Boolean);
	let current = '';
	for (const part of parts) {
		current += '/' + part;
		try { await engine.mkdir(current); } catch { /* exists */ }
	}
}

export async function syncNotebookFile(): Promise<void> {
	if (!engine?.isReady) return;
	const nb = get(notebook);
	const currentPath = get(notebookFilePath);

	await ensureDirs(currentPath.substring(0, currentPath.lastIndexOf('/')) || '/workspace');

	const codeCells = nb.cells.filter((c) => c.type === 'code' && c.content.trim());
	const pyContent = codeCells.map((c) => c.content).join('\n\n');
	await engine.writeFile(currentPath, pyContent);
}

export const notebookPathVersion = writable<number>(0);

export async function changeNotebookPath(rawInput: string): Promise<void> {
	if (!engine?.isReady) return;

	let normalized = rawInput.replace(/\\/g, '/').trim();
	if (!normalized.startsWith('/workspace')) {
		normalized = '/workspace/' + normalized.replace(/^\/+/, '');
	}
	if (!normalized.endsWith('.py')) {
		normalized += '.py';
	}

	const parts = normalized.split('/').filter(Boolean);
	const safeParts = parts.map(sanitizePart);
	const newPath = '/' + safeParts.join('/');

	const oldPath = get(notebookFilePath);
	if (newPath === oldPath) return;

	const dir = newPath.substring(0, newPath.lastIndexOf('/'));
	await ensureDirs(dir);

	if (oldPath && oldPath !== newPath) {
		try { await engine.removeFile(oldPath); } catch { /* old file may not exist */ }
	}

	const fileName = safeParts[safeParts.length - 1];
	const title = fileName.replace(/\.py$/, '');

	notebookFilePath.set(newPath);
	notebook.update((n) => ({
		...n,
		title,
		metadata: { ...n.metadata, notebookFilePath: newPath }
	}));

	await syncNotebookFile();
	saveToStorage();
	notebookPathVersion.update((n) => n + 1);
}

export async function loadNotebookFromFile(path: string): Promise<void> {
	if (!engine?.isReady) return;
	const content = await engine.readFile(path);

	const fileName = path.split('/').pop() || 'Untitled.py';
	const title = fileName.replace(/\.py$/, '');

	const cells: { id: string; type: 'code'; content: string }[] = [];
	if (content.trim()) {
		const blocks = content.split(/\n{2,}/);
		for (const block of blocks) {
			if (block.trim()) {
				cells.push({ id: crypto.randomUUID(), type: 'code', content: block.trim() });
			}
		}
	}

	if (cells.length === 0) {
		cells.push({ id: crypto.randomUUID(), type: 'code', content: '' });
	}

	const { loadNotebook: loadNb } = await import('./notebookStore');
	loadNb({
		id: crypto.randomUUID(),
		title,
		cells,
		metadata: {
			notebookFilePath: path,
			createdAt: new Date().toISOString(),
			updatedAt: new Date().toISOString()
		}
	});
	notebookFilePath.set(path);
}

async function collectWorkspaceFilesRecursive(dirPath: string): Promise<WorkspaceFile[]> {
	if (!engine?.isReady) return [];
	const entries = await engine.listFiles(dirPath);
	const result: WorkspaceFile[] = [];
	const nbFile = get(notebookFilePath);

	for (const entry of entries) {
		if (entry.path === nbFile) continue;

		if (entry.isDir) {
			result.push({ path: entry.path, content: '', isDir: true });
			const children = await collectWorkspaceFilesRecursive(entry.path);
			result.push(...children);
		} else {
			const content = await engine.readFile(entry.path);
			result.push({ path: entry.path, content, isDir: false });
		}
	}
	return result;
}


async function restoreWorkspaceFiles(files: WorkspaceFile[]): Promise<void> {
	if (!engine?.isReady || !files?.length) return;

	const dirs = files.filter((f) => f.isDir).sort((a, b) => a.path.length - b.path.length);
	for (const dir of dirs) {
		try { await engine.mkdir(dir.path); } catch { /* skip */ }
	}

	const regularFiles = files.filter((f) => !f.isDir);
	for (const file of regularFiles) {
		try { await engine.writeFile(file.path, file.content); } catch { /* skip */ }
	}
}

export async function saveWorkspaceSnapshot(): Promise<void> {
	if (!engine?.isReady) return;
	try {
		const files = await collectWorkspaceFilesRecursive('/workspace');
		notebook.update((nb) => ({ ...nb, workspaceFiles: files }));
		saveToStorage();
	} catch {
		// workspace snapshot failed silently
	}
}
