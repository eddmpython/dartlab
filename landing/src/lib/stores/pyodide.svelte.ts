import { browser } from '$app/environment';
import { runSnippet } from '$lib/notebook/stores/executionStore';

type Status = 'idle' | 'loading' | 'ready' | 'error';

type State = {
	status: Status;
	progress: number;
	step: string;
	logs: string[];
	errorMsg: string;
	currentStock: string;
};

export const pyodideStore = $state<State>({
	status: 'idle',
	progress: 0,
	step: '',
	logs: [],
	errorMsg: '',
	currentStock: ''
});

let _ready = false;
let _initPromise: Promise<void> | null = null;
let _scanLiteLoaded = false;
let _scanLitePromise: Promise<void> | null = null;

function pushLog(msg: string) {
	pyodideStore.logs = [...pyodideStore.logs, msg];
}

export async function initPyodide(stockCode = '005930'): Promise<void> {
	if (!browser) return;
	if (pyodideStore.status === 'ready') {
		if (pyodideStore.currentStock !== stockCode) {
			await ensureCompany(stockCode);
		}
		return;
	}
	if (_initPromise) return _initPromise;

	pyodideStore.status = 'loading';
	pyodideStore.logs = [];
	pyodideStore.errorMsg = '';
	pyodideStore.progress = 0;
	pyodideStore.step = '';

	_initPromise = (async () => {
		try {
			pyodideStore.step = 'engine';
			pyodideStore.progress = 0.1;
			pushLog('공유 pyproc machine 시작');
			const imported = await runSnippet('import dartlab');
			if (imported.type === 'error') throw new Error(imported.data);

			_ready = true;
			pyodideStore.step = 'company';
			pyodideStore.progress = 0.85;
			await ensureCompany(stockCode);
			pyodideStore.progress = 1;
			pyodideStore.step = 'ready';
			pushLog('DartLab 준비 완료');
			pyodideStore.status = 'ready';
		} catch (e: unknown) {
			_ready = false;
			pyodideStore.status = 'error';
			pyodideStore.errorMsg = e instanceof Error ? e.message : String(e);
			_initPromise = null;
			throw e;
		}
	})();

	return _initPromise;
}

export async function ensureCompany(stockCode: string): Promise<void> {
	if (!_ready) throw new Error('pyproc machine not initialized');
	if (pyodideStore.currentStock === stockCode) return;
	const result = await runSnippet(
		`c = dartlab.Company(${JSON.stringify(stockCode)})`
	);
	if (result.type === 'error') throw new Error(result.data);
	pyodideStore.currentStock = stockCode;
	pushLog(`Company(${stockCode}) 준비`);
}

export async function ensureScanLite(): Promise<void> {
	if (!_ready) throw new Error('pyproc machine not initialized');
	if (_scanLiteLoaded) return;
	if (_scanLitePromise) return _scanLitePromise;
	_scanLitePromise = (async () => {
		const result = await runSnippet('import dartlab');
		if (result.type === 'error') throw new Error(result.data);
		_scanLiteLoaded = true;
	})();
	try {
		await _scanLitePromise;
	} finally {
		_scanLitePromise = null;
	}
}

export async function runScan(axis: string, target?: string): Promise<RunResult> {
	if (!_ready) throw new Error('pyproc machine not initialized');
	await ensureScanLite();
	const call =
		target === undefined
			? `dartlab.scan(${JSON.stringify(axis)})`
			: `dartlab.scan(${JSON.stringify(axis)}, ${JSON.stringify(target)})`;
	return runCode(`print(${call})`);
}

export type RunResult = { ok: boolean; output: string };

export async function runCode(code: string): Promise<RunResult> {
	if (!_ready) throw new Error('pyproc machine not initialized');
	const result = await runSnippet(code);
	return {
		ok: result.type !== 'error',
		output: result.data.slice(0, result.type === 'error' ? 1500 : undefined)
	};
}

export async function setProviderKey(provider: string, key: string): Promise<void> {
	if (!_ready) throw new Error('pyproc machine not initialized');
	const envMap: Record<string, string[]> = {
		gemini: ['GEMINI_API_KEY', 'GOOGLE_API_KEY'],
		openai: ['OPENAI_API_KEY']
	};
	const names = envMap[provider];
	if (!names) throw new Error(`지원하지 않는 provider: ${provider}`);
	const assignments = names
		.map((name) => `os.environ[${JSON.stringify(name)}] = ${JSON.stringify(key)}`)
		.join('\n');
	const result = await runSnippet(`import os\n${assignments}`);
	if (result.type === 'error') throw new Error(result.data);
}

export function isPyReady(): boolean {
	return pyodideStore.status === 'ready' && _ready;
}
