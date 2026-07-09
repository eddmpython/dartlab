/// <reference lib="webworker" />
import { MARIMO_SHIM_FILES } from './marimoShim';

declare const self: DedicatedWorkerGlobalScope;

interface PyodideInterface {
	runPythonAsync: (code: string) => Promise<unknown>;
	loadPackagesFromImports: (code: string) => Promise<void>;
	globals: { get: (name: string) => unknown };
	setStdout: (options: { batched: (text: string) => void }) => void;
	setStderr: (options: { batched: (text: string) => void }) => void;
	runPython: (code: string) => unknown;
	FS: {
		readdir: (path: string) => string[];
		stat: (path: string) => { size: number; mode: number };
		isDir: (mode: number) => boolean;
		readFile: (path: string, opts?: { encoding: string }) => string | Uint8Array;
		writeFile: (path: string, data: string | Uint8Array, opts?: { encoding: string }) => void;
		mkdir: (path: string) => void;
		unlink: (path: string) => void;
		rmdir: (path: string) => void;
	};
}

const PYODIDE_CDN_ESM = 'https://cdn.jsdelivr.net/pyodide/v0.27.5/full/pyodide.mjs';

// matplotlib 을 테마 중립으로: 투명 배경 + 중립 회색 텍스트/축(다크·라이트 양쪽 가독).
const MATPLOTLIBRC = [
	'figure.facecolor: none',
	'axes.facecolor: none',
	'savefig.facecolor: none',
	'savefig.transparent: True',
	'text.color: 8a8f98',
	'axes.labelcolor: 8a8f98',
	'axes.edgecolor: 8a8f98',
	'axes.titlecolor: a8adb8',
	'xtick.color: 8a8f98',
	'ytick.color: 8a8f98',
	'grid.color: 8a8f98',
	'grid.alpha: 0.15'
].join('\n');

let pyodide: PyodideInterface | null = null;
let stdoutBuffer: string[] = [];
let stderrBuffer: string[] = [];
const wrapCache = new Map<string, string>();

// 노트북 편의: 셀이 dartlab 을 import 하면 최초 1회 자동 설치(HF pyodide wheel). 커널은 범용 그대로.
// dartlab 안 쓰는 노트북은 이 경로에 안 들어온다. 덕에 셀 코드는 `import dartlab` 한 줄이면 된다
// (micropip.install 노출 불필요). 그다음은 데스크톱과 동일하게 `dartlab.Company(code)` 를 쓰면 되고
// 데이터·C 확장·설정은 라이브러리가 흡수한다 (데이터는 메서드 첫 접근 시 lazy fetch, prefetch 불필요).
const DARTLAB_WHEEL =
	'https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/pyodide/dartlab-0.10.7-py3-none-any.whl';
const DARTLAB_IMPORT_RE = /(?:^|\n)[ \t]*(?:import[ \t]+dartlab|from[ \t]+dartlab[ \t.])/;
let dartlabReady = false;

async function ensureDartlab(code: string): Promise<void> {
	if (dartlabReady || !pyodide || !DARTLAB_IMPORT_RE.test(code)) return;
	// pyodide 표준 micropip 로 설치(marimo/duckdb strip 된 wheel 이라 deps 자동 해소).
	await pyodide.runPythonAsync(
		`import micropip\nawait micropip.install(${JSON.stringify(DARTLAB_WHEEL)})`
	);
	dartlabReady = true;
}

function reply(id: string, result: unknown, error?: string) {
	self.postMessage({ id, result, error });
}

function installMarimoShim() {
	if (!pyodide) return;
	const dirs = new Set<string>();
	for (const path of Object.keys(MARIMO_SHIM_FILES)) {
		const parts = path.split('/').slice(0, -1);
		let current = '';
		for (const part of parts) {
			if (!part) continue;
			current += '/' + part;
			dirs.add(current);
		}
	}
	const sortedDirs = Array.from(dirs).sort((a, b) => a.length - b.length);
	for (const dir of sortedDirs) {
		try { pyodide.FS.mkdir(dir); } catch { /* exists */ }
	}
	for (const [path, content] of Object.entries(MARIMO_SHIM_FILES)) {
		pyodide.FS.writeFile(path, content.trim() + '\n', { encoding: 'utf8' });
	}
}

async function initialize() {
	const { loadPyodide: _loadPyodide } = await import(/* @vite-ignore */ PYODIDE_CDN_ESM) as { loadPyodide: (config?: Record<string, unknown>) => Promise<PyodideInterface> };
	pyodide = await _loadPyodide({
		indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.27.5/full/'
	});
	pyodide.setStdout({ batched: (text) => stdoutBuffer.push(text) });
	pyodide.setStderr({ batched: (text) => stderrBuffer.push(text) });
	await pyodide.loadPackagesFromImports('import micropip');
	try { pyodide.FS.mkdir('/workspace'); } catch { /* exists */ }
	// 웹워커에는 DOM(document)이 없으므로 matplotlib 은 non-interactive AGG 백엔드 강제.
	// (기본 pyodide 백엔드는 wasm_backend 가 js.document 를 import 하려다 워커에서 실패)
	// + matplotlibrc 로 테마 중립 색 강제.
	pyodide.FS.writeFile('/matplotlibrc', MATPLOTLIBRC, { encoding: 'utf8' });
	pyodide.runPython('import os, sys; os.chdir("/workspace")\nif "/workspace" not in sys.path: sys.path.insert(0, "/workspace")\nos.environ["MPLBACKEND"] = "AGG"\nos.environ["MATPLOTLIBRC"] = "/matplotlibrc"');
	installMarimoShim();
}

function wrapLastExpression(code: string): string {
	const lines = code.trimEnd().split('\n');
	if (lines.length === 0) return code;
	const lastLine = lines[lines.length - 1];
	const trimmed = lastLine.trim();
	if (!trimmed || trimmed.startsWith('#')) return code;
	if (/^\s/.test(lastLine)) return code;
	const statementKeywords = [
		'import ', 'from ', 'def ', 'class ', 'if ', 'elif ', 'else:',
		'for ', 'while ', 'try:', 'except', 'finally:', 'with ',
		'return ', 'yield ', 'raise ', 'pass', 'break', 'continue',
		'del ', 'assert ', 'global ', 'nonlocal ', 'async ', 'await ',
	];
	const isStatement = statementKeywords.some((kw) => trimmed.startsWith(kw));
	const isSimpleAssignment = /^[a-zA-Z_]\w*\s*(=|[+\-*/%&|^]=|<<=|>>=|\*\*=|\/\/=)(?!=)/.test(trimmed);
	const isAnnotatedAssignment = /^[a-zA-Z_]\w*\s*:\s*\S.*=(?!=)/.test(trimmed);
	const isSubscriptOrAttrAssignment = /^[a-zA-Z_]\w*[\[.].*=(?!=)/.test(trimmed);
	const isTupleUnpack = /^[a-zA-Z_]\w*(\s*,\s*[a-zA-Z_]\w*)+\s*=(?!=)/.test(trimmed);
	if (isStatement || isSimpleAssignment || isAnnotatedAssignment || isSubscriptOrAttrAssignment || isTupleUnpack) {
		return code;
	}
	lines[lines.length - 1] = `__eddmlab_result__ = ${trimmed}`;
	return lines.join('\n') + '\n__eddmlab_result__';
}

const FORMAT_CODE = `
import json as __json__
__eddm_fmt__ = {'repr': '', 'df': None, 'img': None, 'html': None, 'widget': None}
__eddm_r__ = globals().get('__eddmlab_result__')

try:
    from marimo._ui.base import UIElement as __UIElem__
    if isinstance(__eddm_r__, __UIElem__):
        __eddm_fmt__['widget'] = __json__.dumps(__eddm_r__._to_json())
except:
    pass

if __eddm_fmt__['widget'] is None and __eddm_r__ is not None:
    try:
        import pandas as _pd
        if isinstance(__eddm_r__, _pd.DataFrame):
            __df_total__ = len(__eddm_r__)
            __df_cols_info__ = []
            for __c__ in __eddm_r__.columns:
                __dt__ = str(__eddm_r__[__c__].dtype)
                __df_cols_info__.append({'name': str(__c__), 'dtype': __dt__})
            __df_slice__ = __eddm_r__.head(500)
            __df_records__ = __json__.loads(__df_slice__.to_json(orient='split', date_format='iso'))
            __eddm_fmt__['df'] = {
                'type': 'dataframe',
                'totalRows': __df_total__,
                'totalCols': len(__eddm_r__.columns),
                'columns': __df_cols_info__,
                'index': [str(i) for i in __df_slice__.index.tolist()],
                'data': __df_records__['data']
            }
        elif isinstance(__eddm_r__, _pd.Series):
            __s_total__ = len(__eddm_r__)
            __s_slice__ = __eddm_r__.head(500)
            __eddm_fmt__['df'] = {
                'type': 'series',
                'totalRows': __s_total__,
                'totalCols': 1,
                'columns': [{'name': str(__eddm_r__.name or ''), 'dtype': str(__eddm_r__.dtype)}],
                'index': [str(i) for i in __s_slice__.index.tolist()],
                'data': [[v] for v in __json__.loads(__s_slice__.to_json(orient='values'))]
            }
    except:
        pass

# polars DataFrame(및 .df 로 언랩되는 dartlab SelectResult 등)도 pandas 와 동일한 구조화
# 'dataframe' 산출물로 뽑아 marimo 표(DataFrameTable)로 렌더. dtype 문자열은 프론트 정규식이
# 이미 polars 표기(Int64/Float64/String/Utf8/Boolean/Date/Datetime)를 커버. 실패 시 _repr_html_ 폴백.
if __eddm_fmt__['widget'] is None and __eddm_fmt__['df'] is None and __eddm_r__ is not None:
    try:
        import polars as _pl2, math as _math2
        __pl_df__ = __eddm_r__ if isinstance(__eddm_r__, _pl2.DataFrame) else getattr(__eddm_r__, 'df', None)
        if isinstance(__pl_df__, _pl2.DataFrame):
            __pl_num__ = (_pl2.Float64, _pl2.Float32, _pl2.Int64, _pl2.Int32, _pl2.Int16, _pl2.Int8, _pl2.UInt64, _pl2.UInt32, _pl2.UInt16, _pl2.UInt8, _pl2.Boolean)
            __pl_cols__ = [{'name': str(_c), 'dtype': str(_d)} for _c, _d in zip(__pl_df__.columns, __pl_df__.dtypes)]
            __pl_slice__ = __pl_df__.head(500)
            __pl_exprs__ = [(_pl2.col(_c) if _d in __pl_num__ else _pl2.col(_c).cast(_pl2.Utf8, strict=False).alias(_c)) for _c, _d in zip(__pl_slice__.columns, __pl_slice__.dtypes)]
            __pl_rows__ = (__pl_slice__.with_columns(__pl_exprs__) if __pl_slice__.width else __pl_slice__).rows()
            __eddm_fmt__['df'] = {
                'type': 'dataframe',
                'totalRows': __pl_df__.height,
                'totalCols': __pl_df__.width,
                'columns': __pl_cols__,
                'index': [str(_i) for _i in range(len(__pl_rows__))],
                'data': [[(None if isinstance(_v, float) and not _math2.isfinite(_v) else _v) for _v in _row] for _row in __pl_rows__],
            }
    except:
        pass

if __eddm_fmt__['widget'] is None and __eddm_fmt__['df'] is None and __eddm_r__ is not None:
    try:
        if hasattr(__eddm_r__, '_repr_html_'):
            __eddm_html__ = __eddm_r__._repr_html_()
            if '<chani-widget' in str(__eddm_html__):
                __eddm_fmt__['widget'] = __json__.dumps({
                    "__chani_widget__": True,
                    "id": "__html_with_widgets__",
                    "type": "html_composite",
                    "config": {},
                    "value": None,
                    "html": str(__eddm_html__)
                })
            elif __eddm_html__:
                __eddm_fmt__['html'] = str(__eddm_html__)
    except:
        pass

try:
    import matplotlib.pyplot as _plt
    __eddm_figs__ = [_plt.figure(n) for n in _plt.get_fignums()]
    if __eddm_figs__:
        import io as _io, base64 as _b64
        _buf = _io.BytesIO()
        __eddm_figs__[-1].savefig(_buf, format='png', bbox_inches='tight', dpi=150, transparent=True, edgecolor='none')
        _buf.seek(0)
        __eddm_fmt__['img'] = 'data:image/png;base64,' + _b64.b64encode(_buf.read()).decode()
        _buf.close()
        _plt.close('all')
except:
    pass

if __eddm_fmt__['img'] is None and __eddm_r__ is not None:
    try:
        import matplotlib.figure as _mfig
        if isinstance(__eddm_r__, _mfig.Figure):
            import io as _io, base64 as _b64, matplotlib.pyplot as _plt
            _buf = _io.BytesIO()
            __eddm_r__.savefig(_buf, format='png', bbox_inches='tight', dpi=150, transparent=True, edgecolor='none')
            _buf.seek(0)
            __eddm_fmt__['img'] = 'data:image/png;base64,' + _b64.b64encode(_buf.read()).decode()
            _buf.close()
            _plt.close(__eddm_r__)
    except:
        pass

if __eddm_fmt__['img'] is None and __eddm_r__ is not None:
    try:
        import plotly.graph_objects as _pgo
        if isinstance(__eddm_r__, _pgo.Figure):
            __eddm_fmt__['html'] = __eddm_r__.to_html(include_plotlyjs='cdn', full_html=False)
    except:
        pass

if __eddm_r__ is not None and __eddm_fmt__['img'] is None and __eddm_fmt__['html'] is None and __eddm_fmt__['df'] is None:
    __eddm_repr_str__ = repr(__eddm_r__)
    if __eddm_repr_str__ != 'None':
        __eddm_fmt__['repr'] = __eddm_repr_str__
__json__.dumps(__eddm_fmt__)
`;

async function execute(code: string) {
	if (!pyodide) return { type: 'error', data: 'Pyodide not initialized', executedAt: new Date().toISOString() };

	stdoutBuffer = [];
	stderrBuffer = [];

	try {
		// dartlab 을 import 하는 첫 셀이면 자동 설치(그 외 노트북은 미진입, 커널은 범용 유지).
		await ensureDartlab(code);
		const hasImport = /(?:^|\n)\s*(?:import |from )\S+/.test(code);
		if (hasImport) {
			await pyodide.loadPackagesFromImports(code);
			pyodide.runPython('import importlib; importlib.invalidate_caches()');
		}

		let wrappedCode = wrapCache.get(code);
		if (!wrappedCode) {
			wrappedCode = '__eddmlab_result__ = None\n' + wrapLastExpression(code);
			if (wrapCache.size >= 200) wrapCache.delete(wrapCache.keys().next().value!);
			wrapCache.set(code, wrappedCode);
		}
		await pyodide.runPythonAsync(wrappedCode);

		let stdout = stdoutBuffer.join('\n');
		// matplotlib 첫 플롯의 "building the font cache" 안내는 stderr 로 나오지만 오류가 아니다.
		const stderr = stderrBuffer
			.join('\n')
			.split('\n')
			.filter((line) => !/Matplotlib is building the font cache/.test(line))
			.join('\n')
			.trim();

		// stderr(파이썬 logging.warning 등 경고)는 오류가 아니다. 진짜 예외는 runPythonAsync 가
		// throw 해 아래 catch 로 잡힌다. 벤인 stderr 는 출력에 합쳐 보이되 셀을 error 로 만들지 않는다
		// (dartlab 등 라이브러리가 stderr 로 로그를 남겨도 표·그림 결과가 사라지지 않도록).
		if (stderr) stdout = stdout ? stdout + '\n' + stderr : stderr;

		const hasResult = pyodide.runPython('__eddmlab_result__ is not None') as boolean;
		const hasFigures = pyodide.runPython(
			"__import__('matplotlib.pyplot', fromlist=['pyplot']).get_fignums() if 'matplotlib' in __import__('sys').modules else []"
		);
		const needsFormat = hasResult || (hasFigures && (hasFigures as unknown[]).length > 0);

		let fmt = { repr: '', df: null as unknown, img: null as string | null, html: null as string | null, widget: null as string | null };
		if (needsFormat) {
			const raw = pyodide.runPython(FORMAT_CODE);
			const str = String(raw);
			if (str && str !== 'None') {
				const parsed = JSON.parse(str);
				fmt = { repr: parsed.repr || '', df: parsed.df, img: parsed.img, html: parsed.html, widget: parsed.widget };
			}
		}

		if (fmt.widget) {
			const data = stdout ? stdout + '\n__STDOUT_END__\n' + fmt.widget : fmt.widget;
			return { type: 'widget', data, executedAt: new Date().toISOString() };
		}
		if (fmt.img) {
			const data = stdout ? stdout + '\n__STDOUT_END__\n' + fmt.img : fmt.img;
			return { type: 'image', data, executedAt: new Date().toISOString() };
		}
		if (fmt.html) {
			return { type: 'html', data: (stdout ? '<pre>' + stdout + '</pre>' : '') + fmt.html, executedAt: new Date().toISOString() };
		}
		if (fmt.df) {
			const dfJson = JSON.stringify(fmt.df);
			const data = stdout ? stdout + '\n__STDOUT_END__\n' + dfJson : dfJson;
			return { type: 'dataframe', data, executedAt: new Date().toISOString() };
		}
		let output = stdout;
		if (fmt.repr) output = output ? output + '\n' + fmt.repr : fmt.repr;
		return { type: 'text', data: output || '', executedAt: new Date().toISOString() };
	} catch (err) {
		return { type: 'error', data: String(err), executedAt: new Date().toISOString() };
	}
}

self.onmessage = async (e: MessageEvent) => {
	const { id, cmd, args } = e.data as { id: string; cmd: string; args: unknown[] };

	try {
		switch (cmd) {
			case 'initialize': {
				await initialize();
				reply(id, { ok: true });
				break;
			}
			case 'warm': {
				// 사전 로딩: 커널이 뜬 뒤 dartlab wheel 설치 + import 까지 미리 끝낸다. 사용자가 첫 셀을
				// 돌릴 때 21MB wheel + C 확장(polars·pyarrow) 다운로드를 기다리지 않게 하는 게 목적.
				// 실패해도 조용히 넘어간다(첫 import dartlab 셀에서 ensureDartlab 이 다시 시도).
				try {
					await ensureDartlab('import dartlab');
					await pyodide?.runPythonAsync('import dartlab');
					reply(id, { warmed: true });
				} catch (err) {
					reply(id, { warmed: false, error: String(err) });
				}
				break;
			}
			case 'execute': {
				const result = await execute(args[0] as string);
				reply(id, result);
				break;
			}
			case 'getVariableNames': {
				if (!pyodide) { reply(id, []); break; }
				const result = pyodide.runPython("[k for k in dir() if not k.startswith('_')]");
				reply(id, Array.from(result as Iterable<string>));
				break;
			}
			case 'getVariablesWithInfo': {
				if (!pyodide) { reply(id, []); break; }
				const result = pyodide.runPython(`
import json as __json__
__vars__ = []
for __n__ in sorted([k for k in dir() if not k.startswith('_')]):
    try:
        __v__ = eval(__n__)
        __t__ = type(__v__).__name__
        __r__ = repr(__v__)
        if len(__r__) > 80:
            __r__ = __r__[:77] + '...'
        __vars__.append({'name': __n__, 'type': __t__, 'value': __r__})
    except:
        pass
__json__.dumps(__vars__)
`);
				reply(id, JSON.parse(String(result)));
				break;
			}
			case 'getCompletions': {
				if (!pyodide) { reply(id, []); break; }
				const objName = args[0] as string;
				const code = objName ? `
import json as __json__
__comp_result__ = '[]'
__comp_obj_name__ = ${JSON.stringify(objName)}
try:
    __comp_obj__ = eval(compile(__comp_obj_name__, '<string>', 'eval'))
    __comp_attrs__ = [a for a in dir(__comp_obj__) if not a.startswith('_')]
    __comp_items__ = []
    for __comp_a__ in __comp_attrs__[:100]:
        try:
            __comp_val__ = getattr(__comp_obj__, __comp_a__)
            __comp_t__ = 'method' if callable(__comp_val__) else 'property'
        except:
            __comp_t__ = 'variable'
        __comp_items__.append({'label': __comp_a__, 'type': __comp_t__})
    __comp_result__ = __json__.dumps(__comp_items__)
except:
    pass
__comp_result__
` : `
import json as __json__
__comp_names__ = [k for k in dir() if not k.startswith('_')]
__comp_items__ = []
for __comp_n__ in __comp_names__[:100]:
    try:
        __comp_val__ = eval(__comp_n__)
        __comp_t__ = 'function' if callable(__comp_val__) else 'variable'
    except:
        __comp_t__ = 'variable'
    __comp_items__.append({'label': __comp_n__, 'type': __comp_t__})
__json__.dumps(__comp_items__)
`;
				const result = pyodide.runPython(code);
				const str = String(result);
				reply(id, (!str || str === 'None') ? [] : JSON.parse(str));
				break;
			}
			case 'installPackage': {
				if (!pyodide) { reply(id, null); break; }
				const safeName = (args[0] as string).replace(/'/g, "\\'");
				await pyodide.runPythonAsync(`import micropip; await micropip.install('${safeName}')`);
				reply(id, null);
				break;
			}
			case 'getInstalledPackages': {
				if (!pyodide) { reply(id, []); break; }
				const result = await pyodide.runPythonAsync(`
import json as __json__
import micropip
__pkgs__ = []
for __name__, __pkg__ in sorted(micropip.list().items()):
    __pkgs__.append({'name': __name__, 'version': str(__pkg__.version)})
__json__.dumps(__pkgs__)
`);
				reply(id, JSON.parse(String(result)));
				break;
			}
			case 'getDocstring': {
				if (!pyodide) { reply(id, null); break; }
				const name = args[0] as string;
				const result = pyodide.runPython(`
import json as __json__
import inspect as __inspect__
__doc_result__ = None
__doc_name__ = ${JSON.stringify(name)}
try:
    __doc_obj__ = eval(compile(__doc_name__, '<string>', 'eval'))
    __doc_sig__ = ''
    try:
        __doc_sig__ = str(__inspect__.signature(__doc_obj__))
    except (ValueError, TypeError):
        pass
    __doc_str__ = __inspect__.getdoc(__doc_obj__) or ''
    if len(__doc_str__) > 2000:
        __doc_str__ = __doc_str__[:2000] + '...'
    __doc_result__ = __json__.dumps({'name': __doc_name__, 'signature': __doc_sig__, 'docstring': __doc_str__})
except Exception:
    __doc_result__ = 'null'
__doc_result__
`);
				const str = String(result);
				reply(id, (!str || str === 'None' || str === 'null') ? null : JSON.parse(str));
				break;
			}
			case 'updateWidgetValue': {
				if (!pyodide) { reply(id, null); break; }
				const [widgetId, value] = args as [string, unknown];
				const safeId = widgetId.replace(/'/g, "\\'");
				const valueStr = JSON.stringify(value);
				pyodide.runPython(`
from marimo._ui.base import UIElement as __UIElem__
__UIElem__._set_value('${safeId}', __import__('json').loads('${valueStr.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}'))
`);
				reply(id, null);
				break;
			}
			case 'listFiles': {
				if (!pyodide) { reply(id, []); break; }
				const path = args[0] as string;
				try {
					const entries = pyodide.FS.readdir(path).filter((n) => n !== '.' && n !== '..');
					const result = entries.map((name) => {
						const fullPath = path.endsWith('/') ? path + name : path + '/' + name;
						try {
							const stat = pyodide!.FS.stat(fullPath);
							return { name, path: fullPath, isDir: pyodide!.FS.isDir(stat.mode), size: stat.size };
						} catch {
							return { name, path: fullPath, isDir: false, size: 0 };
						}
					});
					reply(id, result);
				} catch { reply(id, []); }
				break;
			}
			case 'readFile': {
				if (!pyodide) { reply(id, ''); break; }
				try {
					reply(id, pyodide.FS.readFile(args[0] as string, { encoding: 'utf8' }) as string);
				} catch { reply(id, ''); }
				break;
			}
			case 'writeFile': {
				if (!pyodide) { reply(id, null); break; }
				pyodide.FS.writeFile(args[0] as string, args[1] as string, { encoding: 'utf8' });
				reply(id, null);
				break;
			}
			case 'mkdir': {
				if (!pyodide) { reply(id, null); break; }
				try { pyodide.FS.mkdir(args[0] as string); } catch { /* exists */ }
				try {
					const p = args[0] as string;
					const initPath = p.endsWith('/') ? p + '__init__.py' : p + '/__init__.py';
					pyodide.FS.stat(initPath);
				} catch {
					try {
						const p = args[0] as string;
						const initPath = p.endsWith('/') ? p + '__init__.py' : p + '/__init__.py';
						pyodide.FS.writeFile(initPath, '', { encoding: 'utf8' });
					} catch { /* skip */ }
				}
				reply(id, null);
				break;
			}
			case 'removeFile': {
				if (!pyodide) { reply(id, null); break; }
				await removeFileRecursive(args[0] as string);
				reply(id, null);
				break;
			}
			default:
				reply(id, null, `Unknown command: ${cmd}`);
		}
	} catch (err) {
		reply(id, null, String(err));
	}
};

async function removeFileRecursive(path: string): Promise<void> {
	if (!pyodide) return;
	try {
		const stat = pyodide.FS.stat(path);
		if (pyodide.FS.isDir(stat.mode)) {
			const entries = pyodide.FS.readdir(path).filter((n) => n !== '.' && n !== '..');
			for (const name of entries) {
				const child = path.endsWith('/') ? path + name : path + '/' + name;
				await removeFileRecursive(child);
			}
			pyodide.FS.rmdir(path);
		} else {
			pyodide.FS.unlink(path);
		}
	} catch { /* ignore */ }
}
