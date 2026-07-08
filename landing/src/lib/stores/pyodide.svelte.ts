import { browser } from '$app/environment';
import { initDartlab, loadCompany, loadScanLite, setApiKey } from '$pyodide/loader.js';
import type { CellRun, NbOutput } from '$lib/notebook/types';

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

// ── notebook 셀 실행 ─────────────────────────────────────────────
// runCode 는 stdout 텍스트만 캡처한다. 노트북은 REPL 처럼 "마지막 표현식의 값" 도
// 잡아 rich 출력(DataFrame 표 등)으로 보여줘야 하므로 별도 경로를 둔다.
// _dl_format_result 가 polars/pandas DataFrame·_repr_html_·repr 을 구조화 JSON 으로 발급하고
// runCell 이 stdout 버퍼와 그 payload 를 분리 반환한다. 커널 네임스페이스(_py globals)는
// runCode 와 공유하므로 셀 간 변수·import·c 바인딩이 그대로 유지된다.

let _nbBootstrapped = false;

const NB_BOOTSTRAP = `
import ast as _dl_ast, json as _dl_json, traceback as _dl_tb

def _dl_json_safe(v):
    if v is None or isinstance(v, (bool, int, str)):
        return v
    if isinstance(v, float):
        if v != v or v in (float("inf"), float("-inf")):
            return None
        return v
    return str(v)

def _dl_format_result(val):
    if val is None:
        return {"type": "none"}
    try:
        import polars as _pl
        if isinstance(val, _pl.DataFrame):
            head = val.head(200)
            return {
                "type": "dataframe",
                "columns": [str(c) for c in head.columns],
                "dtypes": [str(t) for t in head.dtypes],
                "rows": [[_dl_json_safe(x) for x in row] for row in head.iter_rows()],
                "nrows": int(val.height),
                "ncols": int(val.width),
                "truncated": bool(val.height > 200),
            }
        if isinstance(val, _pl.Series):
            head = val.head(200)
            return {
                "type": "dataframe",
                "columns": [str(val.name) or "value"],
                "dtypes": [str(val.dtype)],
                "rows": [[_dl_json_safe(x)] for x in head.to_list()],
                "nrows": int(val.len()),
                "ncols": 1,
                "truncated": bool(val.len() > 200),
            }
    except Exception:
        pass
    try:
        import pandas as _pd
        if isinstance(val, _pd.DataFrame):
            head = val.head(200)
            return {
                "type": "dataframe",
                "columns": [str(c) for c in head.columns],
                "dtypes": [str(t) for t in head.dtypes],
                "rows": [[_dl_json_safe(x) for x in r] for r in head.itertuples(index=False, name=None)],
                "nrows": int(val.shape[0]),
                "ncols": int(val.shape[1]),
                "truncated": bool(val.shape[0] > 200),
            }
    except Exception:
        pass
    _html = getattr(val, "_repr_html_", None)
    if callable(_html):
        try:
            return {"type": "html", "data": str(_html())}
        except Exception:
            pass
    return {"type": "repr", "data": repr(val)}
`;

const NB_WRAPPER = `
__dl_nb_result__ = "null"
try:
    _dl_src = __dl_nb_src__
    _dl_tree = _dl_ast.parse(_dl_src, "<cell>", "exec")
    _dl_val = None
    _dl_body = _dl_tree.body
    if _dl_body and isinstance(_dl_body[-1], _dl_ast.Expr):
        _dl_last = _dl_body.pop()
        if _dl_body:
            _dl_mod = _dl_ast.Module(body=_dl_body, type_ignores=[])
            exec(compile(_dl_mod, "<cell>", "exec"), globals())
        _dl_expr = _dl_ast.Expression(body=_dl_last.value)
        _dl_ast.fix_missing_locations(_dl_expr)
        _dl_val = eval(compile(_dl_expr, "<cell>", "eval"), globals())
    else:
        exec(compile(_dl_tree, "<cell>", "exec"), globals())
    __dl_nb_result__ = _dl_json.dumps(_dl_format_result(_dl_val))
except Exception:
    __dl_nb_result__ = _dl_json.dumps({"type": "error", "data": _dl_tb.format_exc()})
`;

export async function runCell(code: string): Promise<CellRun> {
	if (!_py) throw new Error('pyodide not initialized');
	if (!_nbBootstrapped) {
		await _py.runPythonAsync(NB_BOOTSTRAP);
		_nbBootstrapped = true;
	}
	const buffer: string[] = [];
	_py.setStdout({ batched: (msg: string) => buffer.push(msg) });
	_py.setStderr({ batched: (msg: string) => buffer.push(msg) });
	try {
		_py.globals.set('__dl_nb_src__', code);
		await _py.runPythonAsync(NB_WRAPPER);
		const raw = _py.globals.get('__dl_nb_result__');
		const jsonStr = typeof raw === 'string' ? raw : String(raw);
		let output: NbOutput;
		try {
			output = JSON.parse(jsonStr) as NbOutput;
		} catch {
			output = { type: 'repr', data: jsonStr };
		}
		return { ok: output.type !== 'error', stdout: buffer.join('\n'), output };
	} catch (e: unknown) {
		const errText = e instanceof Error ? e.message : String(e);
		return { ok: false, stdout: buffer.join('\n'), output: { type: 'error', data: errText } };
	}
}

export function isPyReady(): boolean {
	return pyodideStore.status === 'ready' && _py !== null;
}
