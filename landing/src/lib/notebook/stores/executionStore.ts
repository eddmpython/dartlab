import { writable, get } from 'svelte/store';
import type { CellOutput, ExecutionEngine, CompletionItem, VariableInfo, PackageInfo, DocResult, FileEntry, PyApiResponse } from '../engine/executionEngine';
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

let prewarmed: Promise<void> | null = null;

/**
 * 사전 로딩. 허브에서 사용자가 노트북을 만들거나 열려는 낌새(hover·click)에 미리 커널을 띄우고
 * dartlab wheel 설치까지 끝낸다. 엔진은 모듈 싱글턴이라 허브 → 에디터 클라이언트 내비게이션에서
 * 그대로 재사용되므로, 에디터가 열릴 때는 이미 준비돼 있다(첫 셀 실행 전 21MB 대기 제거).
 * 여러 번 불러도 한 번만 돈다. 실패는 삼킨다(에디터가 정상 경로로 다시 초기화).
 */
export function prewarmEngine(): Promise<void> {
	if (!prewarmed) {
		prewarmed = (async () => {
			await bringUpEngine(); // 엔진 기동만. 노트북 부착(autoRun)은 에디터가 한다.
			await engine?.warm?.();
		})().catch(() => undefined);
	}
	return prewarmed;
}

const dataWarmed = new Set<string>();
const prewarmedOutputs = new Map<string, CellOutput>();

/**
 * 데이터 + 결과 사전 계산. 첫 셀 코드를 조용히 한 번 실행한다. 이때 두 가지가 미리 끝난다.
 *   (1) 그 셀이 여는 회사의 parquet 이 커널 FS 로 올라온다(다음 실행은 fetch 없음).
 *   (2) panel 의 polars WASM 계산 결과(표)까지 나온다. 그 결과를 버리지 않고 캐시한다.
 * 사용자가 글 읽는 동안 이 계산이 끝나 있으면, 첫 클릭은 fetch 도 계산도 없이 캐시된 결과를
 * 즉시 보여준다(체감 0초). 캐시 결과는 이번 세션에서 방금 같은 커널이 낸 것이라 정확하다.
 * 멱등. 커널이 죽으면 FS·결과 캐시 모두 무효라 destroyEngine 에서 비운다.
 */
export async function prewarmData(code: string): Promise<void> {
	const key = code.trim();
	if (!key || dataWarmed.has(key)) return;
	dataWarmed.add(key);
	try {
		const out = await runSnippet(code); // 데이터 fetch + 계산. 결과를 캐시한다.
		if (out.type !== 'error') prewarmedOutputs.set(key, out);
	} catch {
		dataWarmed.delete(key); // 실패면 다음 기회에 다시.
	}
}

/** 프리페치가 미리 낸 결과를 한 번 꺼내 쓴다(꺼내면 지워, 재클릭은 실제 재실행). */
export function takePrewarmedOutput(code: string): CellOutput | undefined {
	const key = code.trim();
	const out = prewarmedOutputs.get(key);
	if (out) prewarmedOutputs.delete(key);
	return out;
}

/**
 * browser-as-server: 브라우저 안 dartlab FastAPI 로 HTTP 요청을 서빙한다. Service Worker 가 페이지
 * fetch('/pyapi/*')를 pyapiBridge 를 통해 여기로 relay 한다. 노트북 execute 와 같은 워커 커널 공유.
 */
export async function serveApi(req: {
	method: string;
	path: string;
	body?: string;
}): Promise<PyApiResponse> {
	await bringUpEngine();
	if (!engine?.isReady || !engine.serveApi) {
		return { status: 503, headers: { 'content-type': 'application/json' }, body: '{"error":"engine not ready"}' };
	}
	return engine.serveApi(req);
}

let bringUp: Promise<void> | null = null;

/** 워커 기동 + 위젯 브리지. 중복 호출 안전(진행 중이면 그 약속을 공유). 노트북에는 손대지 않는다. */
async function bringUpEngine(): Promise<void> {
	if (engine?.isReady) return;
	if (bringUp) return bringUp;

	engineStatus.set('loading');
	engineError.set(null);
	bringUp = (async () => {
		// 앞선 기동이 실패했으면 죽은 워커가 남아 있다. 붙들고 있지 말고 버린 뒤 새로 띄운다.
		engine?.destroy();
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
	})();

	try {
		await bringUp;
	} catch (err) {
		engineStatus.set('error');
		engineError.set(String(err));
	} finally {
		bringUp = null;
	}
}

/** 이 노트북에 이미 부착(워크스페이스 복원 + autoRun)했는지. 프리워밍으로 엔진만 떠 있는 상태와 구분한다. */
let attachedNotebookId: string | null = null;

export async function initEngine(autoRun = true): Promise<void> {
	await bringUpEngine();
	if (!engine?.isReady) return;

	// 엔진이 이미 떠 있다고 해서 부착까지 끝난 건 아니다. 사전 로딩(prewarmEngine)이 엔진만 올려 둔
	// 경우 여기서 처음 부착한다. 옛 코드는 `if (engine?.isReady) return` 이라 프리워밍이 autoRun 을
	// 통째로 건너뛰게 만들었다(첫 셀이 영영 안 돌던 회귀).
	const nbId = get(notebook).id;
	if (attachedNotebookId === nbId) return;
	attachedNotebookId = nbId;

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
	// `if (!engine)` 로 거르면 안 된다. 기동이 한 번 실패하면 engine 은 non-null 인데 isReady 는
	// false 다. 그러면 이 분기를 건너뛰고 아래에서 영원히 "Engine not ready" 만 돌려준다. 새로고침
	// 말고는 빠져나갈 길이 없었다. bringUpEngine 은 죽은 워커를 버리고 다시 띄운다.
	if (!engine?.isReady) {
		await initEngine(false);
	}

	if (!engine?.isReady) {
		setCellOutput(cellId, {
			type: 'error',
			data: `파이썬 엔진을 띄우지 못했습니다. ${get(engineError) ?? ''}`.trim(),
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

/** 이 커널에서 이미 돌린 본문 토막. 커널이 죽으면 같이 비운다. */
const ranSnippets = new Set<string>();

/**
 * 노트북 밖(블로그 본문 셀)에서 코드 한 토막을 돌린다.
 *
 * `executeCell` 은 노트북 셀 id 를 전제로 출력 저장·반응 그래프·IndexedDB 저장까지 함께 한다.
 * 블로그 본문에는 노트북이 없으므로 그 배선을 타면 안 된다. 커널만 공유하고 나머지는 안 건드린다.
 * 같은 페이지의 셀들이 한 커널을 공유하므로 위 셀에서 만든 변수를 아래 셀이 그대로 쓴다.
 *
 * `prereq` 는 이 셀보다 위에 있는 본문 코드들이다. 순서대로 먼저 흘린다.
 */
export async function runSnippet(code: string, prereq: string[] = []): Promise<CellOutput> {
	// `if (!engine)` 로 거르면 안 된다. 프리워밍(onpointerenter)이 이미 `engine` 을 대입해 두고 아직
	// initialize 중일 수 있다. 그러면 준비를 안 기다린 채 "엔진 없음" 으로 끝난다. bringUpEngine 은
	// 중복 호출이 안전하고, 진행 중이면 그 약속을 공유한다.
	await bringUpEngine();
	if (!engine?.isReady) {
		return { type: 'error', data: '파이썬 엔진을 띄우지 못했습니다.', executedAt: new Date().toISOString() };
	}
	engineStatus.set('executing');
	try {
		// 독자는 글 중간 셀을 먼저 누른다. 그때 위 셀이 만든 `c` 가 없어 NameError 를 본다.
		// 자기 실수도 아닌데 첫 경험이 빨간 traceback 이다. 앞 셀들을 같은 커널에 먼저 흘린다.
		// 이미 돌린 토막은 건너뛴다. 커널이 살아 있는 한 그 상태도 살아 있다.
		for (const before of prereq) {
			const key = before.trim();
			if (!key || ranSnippets.has(key)) continue;
			const out = await engine.execute(before);
			if (out.type === 'error') return out; // 선행이 깨지면 그 오류를 그대로 보여준다
			ranSnippets.add(key);
		}
		const result = await engine.execute(code);
		if (result.type !== 'error') ranSnippets.add(code.trim());
		return result;
	} finally {
		engineStatus.set('ready');
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
	ranSnippets.clear(); // 커널이 사라지면 그 안의 변수도 사라진다
	dataWarmed.clear(); // 데이터 캐시(FS)도 커널과 함께 사라진다
	prewarmedOutputs.clear(); // 미리 낸 결과도 커널이 죽으면 무효
	attachedNotebookId = null; // 다음 initEngine 이 다시 부착(복원+autoRun)하도록
	prewarmed = null; // 워커가 사라졌으니 사전 로딩도 다시 할 수 있게
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
