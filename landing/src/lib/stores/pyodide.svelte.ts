import { browser } from '$app/environment';
import { initDartlab, loadCompany, loadScanLite, setApiKey } from '$pyodide/loader.js';

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

let _py: any = null;
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
			const { py } = await initDartlab({
				stockCode,
				onLog: (msg: string) => pushLog(msg),
				onProgress: (step: string, progress: number) => {
					pyodideStore.step = step;
					pyodideStore.progress = progress;
				}
			});
			_py = py;
			pyodideStore.currentStock = stockCode;
			pyodideStore.status = 'ready';
		} catch (e: unknown) {
			pyodideStore.status = 'error';
			pyodideStore.errorMsg = e instanceof Error ? e.message : String(e);
			_initPromise = null;
			throw e;
		}
	})();

	return _initPromise;
}

export async function ensureCompany(stockCode: string): Promise<void> {
	if (!_py) throw new Error('pyodide not initialized');
	if (pyodideStore.currentStock === stockCode) return;
	await loadCompany(_py, stockCode, { onLog: pushLog });
	pyodideStore.currentStock = stockCode;
}

export async function ensureScanLite(): Promise<void> {
	if (!_py) throw new Error('pyodide not initialized');
	if (_scanLiteLoaded) return;
	if (_scanLitePromise) return _scanLitePromise;
	_scanLitePromise = (async () => {
		await loadScanLite(_py, { onLog: pushLog });
		_scanLiteLoaded = true;
	})();
	try {
		await _scanLitePromise;
	} finally {
		_scanLitePromise = null;
	}
}

export async function runScan(axis: string, target?: string): Promise<RunResult> {
	if (!_py) throw new Error('pyodide not initialized');
	await ensureScanLite();
	const call =
		target === undefined
			? `dartlab.scan(${JSON.stringify(axis)})`
			: `dartlab.scan(${JSON.stringify(axis)}, ${JSON.stringify(target)})`;
	return runCode(`print(${call})`);
}

export type RunResult = { ok: boolean; output: string };

export async function runCode(code: string): Promise<RunResult> {
	if (!_py) throw new Error('pyodide not initialized');
	const buffer: string[] = [];
	_py.setStdout({ batched: (msg: string) => buffer.push(msg) });
	_py.setStderr({ batched: (msg: string) => buffer.push(msg) });
	try {
		await _py.runPythonAsync(code);
		return { ok: true, output: buffer.join('\n') };
	} catch (e: unknown) {
		const errText = (e instanceof Error ? e.message : String(e)).slice(0, 1500);
		const prefix = buffer.length ? buffer.join('\n') + '\n' : '';
		return { ok: false, output: prefix + errText };
	}
}

export async function setProviderKey(provider: string, key: string): Promise<void> {
	if (!_py) throw new Error('pyodide not initialized');
	await setApiKey(_py, provider, key);
}

export function isPyReady(): boolean {
	return pyodideStore.status === 'ready' && _py !== null;
}
