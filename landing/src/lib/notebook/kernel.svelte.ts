// 범용 브라우저 파이썬 커널 (pyodide). dartlab 종속 없음.
// 어떤 파이썬 코드든 실행하고, import 는 자동 로드(numpy/pandas/matplotlib/polars 등),
// top-level await(micropip.install 등)도 지원한다. 셀 간 네임스페이스는 공유된다.

import { browser } from '$app/environment';
import type { CellRun, NbOutput } from './types';

const PYODIDE_CDN = 'https://cdn.jsdelivr.net/pyodide/v0.27.2/full/pyodide.js';

type Status = 'idle' | 'loading' | 'ready' | 'error';

export const kernelStore = $state<{ status: Status; step: string; logs: string[]; errorMsg: string }>({
	status: 'idle',
	step: '',
	logs: [],
	errorMsg: ''
});

let _py: any = null;
let _initPromise: Promise<void> | null = null;

async function loadPyodideInstance() {
	let loadPyodide: any;
	if (typeof (globalThis as any).loadPyodide === 'function') {
		loadPyodide = (globalThis as any).loadPyodide;
	} else {
		// pyodide.js 는 UMD 라 import 네임스페이스에 loadPyodide 가 없고 side-effect 로
		// globalThis.loadPyodide 만 설정된다. 전역 fallback 을 함께 본다.
		const mod = await import(/* @vite-ignore */ PYODIDE_CDN);
		loadPyodide = (mod as any).loadPyodide || (globalThis as any).loadPyodide;
	}
	return await loadPyodide();
}

// 한 번만 실행. 출력 포매터(matplotlib 그림 / DataFrame 표 / repr) 정의.
const BOOTSTRAP = `
import os as _nb_os
_nb_os.environ.setdefault("MPLBACKEND", "AGG")
import json as _nb_json, traceback as _nb_tb, sys as _nb_sys, io as _nb_io, base64 as _nb_b64

def _nb_safe(v):
    if v is None or isinstance(v, (bool, int, str)):
        return v
    if isinstance(v, float):
        if v != v or v in (float("inf"), float("-inf")):
            return None
        return v
    return str(v)

def _nb_capture_mpl():
    plt = _nb_sys.modules.get("matplotlib.pyplot")
    if plt is None:
        return None
    nums = plt.get_fignums()
    if not nums:
        return None
    fig = plt.figure(nums[-1])
    buf = _nb_io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=110)
    plt.close("all")
    return _nb_b64.b64encode(buf.getvalue()).decode("ascii")

def _nb_frame(val):
    try:
        import polars as _pl
        if isinstance(val, _pl.DataFrame):
            head = val.head(200)
            return {"type": "dataframe", "columns": [str(c) for c in head.columns], "dtypes": [str(t) for t in head.dtypes], "rows": [[_nb_safe(x) for x in r] for r in head.iter_rows()], "nrows": int(val.height), "ncols": int(val.width), "truncated": bool(val.height > 200)}
        if isinstance(val, _pl.Series):
            head = val.head(200)
            return {"type": "dataframe", "columns": [str(val.name) or "value"], "dtypes": [str(val.dtype)], "rows": [[_nb_safe(x)] for x in head.to_list()], "nrows": int(val.len()), "ncols": 1, "truncated": bool(val.len() > 200)}
    except Exception:
        pass
    try:
        import pandas as _pd
        if isinstance(val, _pd.DataFrame):
            head = val.head(200)
            return {"type": "dataframe", "columns": [str(c) for c in head.columns], "dtypes": [str(t) for t in head.dtypes], "rows": [[_nb_safe(x) for x in r] for r in head.itertuples(index=False, name=None)], "nrows": int(val.shape[0]), "ncols": int(val.shape[1]), "truncated": bool(val.shape[0] > 200)}
        if isinstance(val, _pd.Series):
            head = val.head(200)
            return {"type": "dataframe", "columns": [str(head.name) or "value"], "dtypes": [str(val.dtype)], "rows": [[_nb_safe(x)] for x in head.tolist()], "nrows": int(val.shape[0]), "ncols": 1, "truncated": bool(val.shape[0] > 200)}
    except Exception:
        pass
    return None

def _nb_format(val):
    if val is None:
        return {"type": "none"}
    fr = _nb_frame(val)
    if fr is not None:
        return fr
    _html = getattr(val, "_repr_html_", None)
    if callable(_html):
        try:
            return {"type": "html", "data": str(_html())}
        except Exception:
            pass
    return {"type": "repr", "data": repr(val)}
`;

// 셀마다 실행. eval_code_async 가 마지막 표현식 값 반환 + top-level await 지원.
const WRAPPER = `
__nb_result__ = "null"
try:
    from pyodide.code import eval_code_async as _nb_eval
    _nb_val = await _nb_eval(__nb_src__, globals())
    _nb_img = _nb_capture_mpl()
    if _nb_img is not None:
        __nb_result__ = _nb_json.dumps({"type": "image", "data": _nb_img})
    else:
        __nb_result__ = _nb_json.dumps(_nb_format(_nb_val))
except Exception:
    __nb_result__ = _nb_json.dumps({"type": "error", "data": _nb_tb.format_exc()})
`;

export async function initKernel(): Promise<void> {
	if (!browser) return;
	if (kernelStore.status === 'ready') return;
	if (_initPromise) return _initPromise;

	kernelStore.status = 'loading';
	kernelStore.errorMsg = '';
	kernelStore.logs = [];

	_initPromise = (async () => {
		try {
			kernelStore.step = 'Pyodide 로드';
			_py = await loadPyodideInstance();
			kernelStore.step = '준비';
			await _py.runPythonAsync(BOOTSTRAP);
			kernelStore.status = 'ready';
			kernelStore.step = 'done';
		} catch (e: unknown) {
			kernelStore.status = 'error';
			kernelStore.errorMsg = e instanceof Error ? e.message : String(e);
			_initPromise = null;
			throw e;
		}
	})();

	return _initPromise;
}

export async function runCell(code: string): Promise<CellRun> {
	if (!_py) throw new Error('kernel not ready');
	// import 된 패키지 자동 로드 (numpy/pandas/matplotlib/... pyodide 배포본)
	try {
		await _py.loadPackagesFromImports(code);
	} catch {
		/* 배포본에 없는 패키지는 셀 내부 import 에서 에러로 드러난다 */
	}

	const buffer: string[] = [];
	_py.setStdout({ batched: (msg: string) => buffer.push(msg) });
	_py.setStderr({ batched: (msg: string) => buffer.push(msg) });
	try {
		_py.globals.set('__nb_src__', code);
		await _py.runPythonAsync(WRAPPER);
		const raw = _py.globals.get('__nb_result__');
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

export function isKernelReady(): boolean {
	return kernelStore.status === 'ready' && _py !== null;
}
