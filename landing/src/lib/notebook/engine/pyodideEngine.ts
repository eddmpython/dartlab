import type { ExecutionEngine, CellOutput, CompletionItem, VariableInfo, PackageInfo, DocResult, FileEntry } from './executionEngine';
import { MARIMO_SHIM_FILES } from './marimoShim';

declare global {
	interface Window {
		loadPyodide: (config?: Record<string, unknown>) => Promise<PyodideInterface>;
	}
}

interface EmscriptenFS {
	readdir: (path: string) => string[];
	stat: (path: string) => { size: number; mode: number };
	isDir: (mode: number) => boolean;
	readFile: (path: string, opts?: { encoding: string }) => string | Uint8Array;
	writeFile: (path: string, data: string | Uint8Array, opts?: { encoding: string }) => void;
	mkdir: (path: string) => void;
	unlink: (path: string) => void;
	rmdir: (path: string) => void;
}

interface PyodideInterface {
	runPythonAsync: (code: string) => Promise<unknown>;
	loadPackagesFromImports: (code: string) => Promise<void>;
	globals: { get: (name: string) => unknown; toJs: () => Map<string, unknown> };
	setStdout: (options: { batched: (text: string) => void }) => void;
	setStderr: (options: { batched: (text: string) => void }) => void;
	runPython: (code: string) => unknown;
	isPyProxy?: (value: unknown) => boolean;
	FS: EmscriptenFS;
}

const PYODIDE_CDN = 'https://cdn.jsdelivr.net/pyodide/v0.27.5/full/pyodide.js';

export class PyodideEngine implements ExecutionEngine {
	name = 'pyodide';
	isReady = false;

	private pyodide: PyodideInterface | null = null;
	private stdoutBuffer: string[] = [];
	private stderrBuffer: string[] = [];
	private wrapCache = new Map<string, string>();

	async initialize(): Promise<void> {
		if (this.isReady) return;

		await this.loadScript(PYODIDE_CDN);

		this.pyodide = await window.loadPyodide({
			indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.27.5/full/'
		});

		this.pyodide.setStdout({
			batched: (text: string) => this.stdoutBuffer.push(text)
		});

		this.pyodide.setStderr({
			batched: (text: string) => this.stderrBuffer.push(text)
		});

		await this.pyodide.loadPackagesFromImports('import micropip');

		try {
			this.pyodide.FS.mkdir('/workspace');
		} catch {
			// already exists
		}
		this.pyodide.runPython('import os, sys; os.chdir("/workspace")\nif "/workspace" not in sys.path: sys.path.insert(0, "/workspace")');

		this.installMarimoShim();

		this.isReady = true;
	}

	private installMarimoShim(): void {
		if (!this.pyodide) return;
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
			try { this.pyodide.FS.mkdir(dir); } catch { /* exists */ }
		}
		for (const [path, content] of Object.entries(MARIMO_SHIM_FILES)) {
			this.pyodide.FS.writeFile(path, content.trim() + '\n', { encoding: 'utf8' });
		}
	}

	async execute(code: string): Promise<CellOutput> {
		if (!this.pyodide) {
			return {
				type: 'error',
				data: 'Pyodide not initialized',
				executedAt: new Date().toISOString()
			};
		}

		this.stdoutBuffer = [];
		this.stderrBuffer = [];

		try {
			const hasImport = /(?:^|\n)\s*(?:import |from )\S+/.test(code);
			if (hasImport) {
				await this.pyodide.loadPackagesFromImports(code);
				this.pyodide.runPython('import importlib; importlib.invalidate_caches()');
			}

			let wrappedCode = this.wrapCache.get(code);
			if (!wrappedCode) {
				wrappedCode = '__eddmlab_result__ = None\n' + this.wrapLastExpression(code);
				if (this.wrapCache.size >= 200) {
					this.wrapCache.delete(this.wrapCache.keys().next().value!);
				}
				this.wrapCache.set(code, wrappedCode);
			}
			await this.pyodide.runPythonAsync(wrappedCode);

			const stdout = this.stdoutBuffer.join('\n');
			const stderr = this.stderrBuffer.join('\n');

			if (stderr) {
				return {
					type: 'error',
					data: stderr,
					executedAt: new Date().toISOString()
				};
			}

			const hasResult = this.pyodide.runPython('__eddmlab_result__ is not None') as boolean;
			const hasFigures = this.pyodide.runPython(
				"__import__('matplotlib.pyplot', fromlist=['pyplot']).get_fignums() if 'matplotlib' in __import__('sys').modules else []"
			);
			const needsFormat = hasResult || (hasFigures && (hasFigures as unknown[]).length > 0);

			const fmt = needsFormat
				? this.formatResult()
				: { repr: '', dataframe: null, image: null, html: null, widget: null };

			if (fmt.widget) {
				const data = stdout ? stdout + '\n__STDOUT_END__\n' + fmt.widget : fmt.widget;
				return {
					type: 'widget',
					data,
					executedAt: new Date().toISOString()
				};
			}

			if (fmt.image) {
				const data = stdout ? stdout + '\n__STDOUT_END__\n' + fmt.image : fmt.image;
				return {
					type: 'image',
					data,
					executedAt: new Date().toISOString()
				};
			}

			if (fmt.html) {
				return {
					type: 'html',
					data: (stdout ? '<pre>' + stdout + '</pre>' : '') + fmt.html,
					executedAt: new Date().toISOString()
				};
			}

			if (fmt.dataframe) {
				const dfJson = JSON.stringify(fmt.dataframe);
				const data = stdout ? stdout + '\n__STDOUT_END__\n' + dfJson : dfJson;
				return {
					type: 'dataframe',
					data,
					executedAt: new Date().toISOString()
				};
			}

			let output = stdout;
			if (fmt.repr) {
				output = output ? output + '\n' + fmt.repr : fmt.repr;
			}

			return {
				type: 'text',
				data: output || '',
				executedAt: new Date().toISOString()
			};
		} catch (err) {
			return {
				type: 'error',
				data: String(err),
				executedAt: new Date().toISOString()
			};
		}
	}

	private formatResult(): { repr: string; dataframe: unknown | null; image: string | null; html: string | null; widget: string | null } {
		if (!this.pyodide) return { repr: '', dataframe: null, image: null, html: null, widget: null };
		try {
			const code = `
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
			const raw = this.pyodide.runPython(code);
			const str = String(raw);
			if (str && str !== 'None') {
				const parsed = JSON.parse(str);
				return { repr: parsed.repr || '', dataframe: parsed.df, image: parsed.img, html: parsed.html, widget: parsed.widget };
			}
		} catch {
			// fallback
		}
		return { repr: '', dataframe: null, image: null, html: null, widget: null };
	}

	private wrapLastExpression(code: string): string {
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

	interrupt(): void {
		// Pyodide doesn't support interrupt in main thread
	}

	destroy(): void {
		this.pyodide = null;
		this.isReady = false;
	}

	async getVariable(name: string): Promise<unknown> {
		if (!this.pyodide) return undefined;
		try {
			return this.pyodide.globals.get(name);
		} catch {
			return undefined;
		}
	}

	async getVariableNames(): Promise<string[]> {
		if (!this.pyodide) return [];
		try {
			const result = this.pyodide.runPython(
				"[k for k in dir() if not k.startswith('_')]"
			);
			return Array.from(result as Iterable<string>);
		} catch {
			return [];
		}
	}

	async getCompletions(objName: string): Promise<CompletionItem[]> {
		if (!this.pyodide) return [];
		try {
			if (objName) {
				this.pyodide.globals.get('__builtins__');
				const safeObjName = JSON.stringify(objName);
				const code = `
import json as __json__
__comp_result__ = '[]'
__comp_obj_name__ = ${safeObjName}
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
`;
				const result = this.pyodide.runPython(code);
				const str = String(result);
				if (!str || str === 'None' || str === 'undefined') return [];
				return JSON.parse(str);
			} else {
				const code = `
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
__comp_result__ = __json__.dumps(__comp_items__)
__comp_result__
`;
				const result = this.pyodide.runPython(code);
				const str = String(result);
				if (!str || str === 'None' || str === 'undefined') return [];
				return JSON.parse(str);
			}
		} catch {
			return [];
		}
	}

	async getVariablesWithInfo(): Promise<VariableInfo[]> {
		if (!this.pyodide) return [];
		try {
			const code = `
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
`;
			const result = this.pyodide.runPython(code);
			return JSON.parse(String(result));
		} catch {
			return [];
		}
	}

	async installPackage(packageName: string): Promise<void> {
		if (!this.pyodide) return;
		const safeName = packageName.replace(/'/g, "\\'");
		await this.pyodide.runPythonAsync(
			`import micropip; await micropip.install('${safeName}')`
		);
	}

	async getInstalledPackages(): Promise<PackageInfo[]> {
		if (!this.pyodide) return [];
		try {
			const code = `
import json as __json__
import micropip
__pkgs__ = []
for __name__, __pkg__ in sorted(micropip.list().items()):
    __pkgs__.append({'name': __name__, 'version': str(__pkg__.version)})
__json__.dumps(__pkgs__)
`;
			const result = await this.pyodide.runPythonAsync(code);
			return JSON.parse(String(result));
		} catch {
			return [];
		}
	}

	async getDocstring(name: string): Promise<DocResult | null> {
		if (!this.pyodide) return null;
		try {
			const safeName = JSON.stringify(name);
			const code = `
import json as __json__
import inspect as __inspect__
__doc_result__ = None
__doc_name__ = ${safeName}
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
`;
			const result = this.pyodide.runPython(code);
			if (!result || String(result) === 'None' || String(result) === 'null') return null;
			return JSON.parse(String(result));
		} catch {
			return null;
		}
	}

	async listFiles(path: string): Promise<FileEntry[]> {
		if (!this.pyodide) return [];
		try {
			const entries = this.pyodide.FS.readdir(path).filter((n: string) => n !== '.' && n !== '..');
			return entries.map((name: string) => {
				const fullPath = path.endsWith('/') ? path + name : path + '/' + name;
				try {
					const stat = this.pyodide!.FS.stat(fullPath);
					return {
						name,
						path: fullPath,
						isDir: this.pyodide!.FS.isDir(stat.mode),
						size: stat.size,
					};
				} catch {
					return { name, path: fullPath, isDir: false, size: 0 };
				}
			});
		} catch {
			return [];
		}
	}

	async readFile(path: string): Promise<string> {
		if (!this.pyodide) return '';
		try {
			return this.pyodide.FS.readFile(path, { encoding: 'utf8' }) as string;
		} catch {
			return '';
		}
	}

	async writeFile(path: string, content: string): Promise<void> {
		if (!this.pyodide) return;
		this.pyodide.FS.writeFile(path, content, { encoding: 'utf8' });
	}

	async mkdir(path: string): Promise<void> {
		if (!this.pyodide) return;
		try {
			this.pyodide.FS.mkdir(path);
		} catch {
			// already exists
		}
		try {
			const initPath = path.endsWith('/') ? path + '__init__.py' : path + '/__init__.py';
			this.pyodide.FS.stat(initPath);
		} catch {
			try {
				const initPath = path.endsWith('/') ? path + '__init__.py' : path + '/__init__.py';
				this.pyodide.FS.writeFile(initPath, '', { encoding: 'utf8' });
			} catch { /* skip */ }
		}
	}

	async updateWidgetValue(widgetId: string, value: unknown): Promise<void> {
		if (!this.pyodide) return;
		const safeId = widgetId.replace(/'/g, "\\'");
		const valueStr = JSON.stringify(value);
		this.pyodide.runPython(`
from marimo._ui.base import UIElement as __UIElem__
__UIElem__._set_value('${safeId}', __import__('json').loads('${valueStr.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}'))
`);
	}

	async removeFile(path: string): Promise<void> {
		if (!this.pyodide) return;
		try {
			const stat = this.pyodide.FS.stat(path);
			if (this.pyodide.FS.isDir(stat.mode)) {
				const entries = this.pyodide.FS.readdir(path).filter((n: string) => n !== '.' && n !== '..');
				for (const name of entries) {
					const child = path.endsWith('/') ? path + name : path + '/' + name;
					await this.removeFile(child);
				}
				this.pyodide.FS.rmdir(path);
			} else {
				this.pyodide.FS.unlink(path);
			}
		} catch {
			// ignore
		}
	}

	private loadScript(src: string): Promise<void> {
		const existing = document.querySelector(`script[src="${src}"]`);
		if (existing) return Promise.resolve();

		const pending = PyodideEngine.loadingScripts.get(src);
		if (pending) return pending;

		const promise = new Promise<void>((resolve, reject) => {
			const script = document.createElement('script');
			script.src = src;
			script.onload = () => {
				PyodideEngine.loadingScripts.delete(src);
				resolve();
			};
			script.onerror = () => {
				PyodideEngine.loadingScripts.delete(src);
				reject(new Error(`Failed to load ${src}`));
			};
			document.head.appendChild(script);
		});

		PyodideEngine.loadingScripts.set(src, promise);
		return promise;
	}

	private static loadingScripts = new Map<string, Promise<void>>();
}
