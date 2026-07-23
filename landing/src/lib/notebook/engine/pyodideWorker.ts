/// <reference lib="webworker" />
import { MARIMO_SHIM_FILES } from './marimoShim';
import { wrapLastExpression } from './lastExpression';
import { CheckpointGraph } from './checkpointGraph';
import {
	mergePackageSpecs,
	packageSpecKey,
	parsePackageManifest,
	parsePipInstallCommand,
	parseRequirementsText,
	serializePackageManifest
} from './packageManifest';
import { HandRolledAsgi, PyprocAsgi, type AsgiKernel } from './kernel/asgiSeam';
import { Runtime } from 'pyproc/runtime';
import { createDartlabRuntimeLoader } from './dartlabRuntime';

declare const self: DedicatedWorkerGlobalScope;

// pyodide 는 이제 공유 rt(pyproc Runtime) 로 감싸 FS·run·출력·인터럽트를 rt.* 로 쓴다(단일 런타임
// SSOT). 여기 남는 직접 표면은 pyproc 미담당분뿐: mountNativeFS(OPFS 워크스페이스) + _module(체크포인트
// 스냅샷). runPython/runPythonAsync/globals 는 pyproc 설치 실패 시 HandRolledAsgi(raw) 폴백용(PyLike 충족).
interface PyodideInterface {
	runPythonAsync: (code: string) => Promise<unknown>;
	runPython: (code: string) => unknown;
	globals: { get: (name: string) => unknown; set: (name: string, value: unknown) => void };
	mountNativeFS?: (
		path: string,
		handle: FileSystemDirectoryHandle
	) => Promise<{ syncfs: () => Promise<void> }>;
	_module: {
		HEAPU8: Uint8Array;
		_emscripten_stack_get_current?: () => number;
		_emscripten_stack_restore?: (pointer: number) => void;
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
// 공유 pyproc Runtime(단일 런타임 SSOT). init 에서 new Runtime(pyodide) 로 만들어 커널(ASGI)·셀실행·
// 파일 IO 가 같은 rt 를 쓴다. pyodide 가 set 이면 rt 도 항상 set(둘은 init 에서 함께 생성).
let rt: Runtime | null = null;
let stdoutBuffer: string[] = [];
let stderrBuffer: string[] = [];
const wrapCache = new Map<string, string>();
let workspaceSync: (() => Promise<void>) | null = null;
let persistentWorkspace = false;
let attachedWorkspaceId: string | null = null;
let interruptMode: 'soft' | 'hard' = 'hard';
let checkpointGraph: CheckpointGraph | null = null;
let packageRestoreSignature = '';
let packageRestoreError = '';

const PACKAGE_DIR = '/workspace/.dartlab';
const PACKAGE_MANIFEST_PATH = `${PACKAGE_DIR}/requirements.json`;
const WORKSPACE_REQUIREMENTS_PATH = '/workspace/requirements.txt';

// 노트북 편의: 셀이 dartlab 을 import 하면 최초 1회 자동 설치(HF pyodide wheel). 커널은 범용 그대로.
// dartlab 안 쓰는 노트북은 이 경로에 안 들어온다. 덕에 셀 코드는 `import dartlab` 한 줄이면 된다
// (micropip.install 노출 불필요). 그다음은 데스크톱과 동일하게 `dartlab.Company(code)` 를 쓰면 되고
// 데이터·C 확장·설정은 라이브러리가 흡수한다 (데이터는 메서드 첫 접근 시 lazy fetch, prefetch 불필요).
// PyPI 에서 설치한다. pip 과 같은 진입점·같은 버전이라 본체 릴리즈에 자동으로 맞는다(HF wheel URL·
// 수동 버전 포인터 제거). 다만 dartlab 의 지연 import 때문에 Pyodide 는 transitive C 확장을 스스로
// 발견하지 못한다. dartlabRuntime 이 polars·pyarrow·lxml·numpy 를 먼저 적재하고 동시 설치도 합친다.
let dartlabLoader: ReturnType<typeof createDartlabRuntimeLoader> | null = null;

async function ensureDartlab(code: string): Promise<void> {
	await dartlabLoader?.ensure(code);
}

// browser-as-server: 이 워커(노트북 execute 커널)에 dartlab FastAPI 를 얹는다. 한 커널, 두 인터페이스.
// ASGI dispatch 는 커널 seam(kernel/asgiSeam.ts)이 소유한다. USE_PYPROC_ASGI=true(기본)면 워커의
// pyodide 를 new Runtime(py) 로 채택해 pyproc AsgiServer 로 서빙(공유 런타임 SSOT). 설치 실패 시 손수
// _dl_dispatch 경로로 자동 폴백(kill-switch). false 로 되돌리면 손수 경로 고정. mainPlan/pyproc-runtime-ssot.
// fastapi 는 첫 /pyapi 요청 때만 설치(노트북만 쓰면 비용 0). dartlab 설치는 seam 위 ensureDartlab.
const USE_PYPROC_ASGI = true;
let asgiKernel: AsgiKernel | null = null;

function reply(id: string, result: unknown, error?: string) {
	self.postMessage({ id, result, error });
}

function installMarimoShim() {
	if (!rt) return;
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
		try { rt.fs.mkdir(dir); } catch { /* exists */ }
	}
	for (const [path, content] of Object.entries(MARIMO_SHIM_FILES)) {
		rt.fs.writeFile(path, content.trim() + '\n');
	}
}

async function initialize(interruptBuffer?: Uint8Array | null) {
	const { loadPyodide: _loadPyodide } = await import(/* @vite-ignore */ PYODIDE_CDN_ESM) as { loadPyodide: (config?: Record<string, unknown>) => Promise<PyodideInterface> };
	pyodide = await _loadPyodide({
		indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.27.5/full/'
	});
	// 공유 런타임 채택: 이후 FS·run·출력·인터럽트·패키지로드는 전부 rt.* 로(pyproc 단일 SSOT).
	rt = new Runtime(pyodide);
	dartlabLoader = createDartlabRuntimeLoader(rt);
	// 인터럽트: rt 는 SAB 를 받아 엔진이 Uint8Array 뷰로 감싼다(공유 유지). 미지원 엔진이면 false.
	if (interruptBuffer && rt.setInterruptBuffer(interruptBuffer.buffer)) {
		interruptMode = 'soft';
	}
	rt.setStdout((text) => stdoutBuffer.push(text));
	rt.setStderr((text) => stderrBuffer.push(text));
	await rt.loadPackagesFromImports('import micropip');
	try { rt.fs.mkdir('/workspace'); } catch { /* exists */ }
	// 허브 프리워밍 시점에는 대상 ID가 없다. OPFS는 attachWorkspace에서 노트북별로 마운트한다.
	// 웹워커에는 DOM(document)이 없으므로 matplotlib 은 non-interactive AGG 백엔드 강제.
	// (기본 pyodide 백엔드는 wasm_backend 가 js.document 를 import 하려다 워커에서 실패)
	// + matplotlibrc 로 테마 중립 색 강제.
	rt.fs.writeFile('/matplotlibrc', MATPLOTLIBRC);
	rt.run('import os, sys; os.chdir("/workspace")\nif "/workspace" not in sys.path: sys.path.insert(0, "/workspace")\nos.environ["MPLBACKEND"] = "AGG"\nos.environ["MATPLOTLIBRC"] = "/matplotlibrc"');
	installMarimoShim();
	asgiKernel = USE_PYPROC_ASGI ? new PyprocAsgi(rt) : new HandRolledAsgi(pyodide);
}

async function attachWorkspace(workspaceId: string): Promise<boolean> {
	if (!pyodide?.mountNativeFS || !self.navigator.storage?.getDirectory) return false;
	if (attachedWorkspaceId === workspaceId) return persistentWorkspace;
	if (attachedWorkspaceId) throw new Error('a different notebook workspace is already attached');

	try {
		const safeId = workspaceId.replace(/[^a-zA-Z0-9_-]/g, '_');
		const root = await self.navigator.storage.getDirectory();
		const workspaces = await root.getDirectoryHandle('dartlab-notebook-workspaces', { create: true });
		const handle = await workspaces.getDirectoryHandle(safeId, { create: true });
		const mounted = await pyodide.mountNativeFS('/workspace', handle);
		workspaceSync = mounted.syncfs;
		await workspaceSync();
		attachedWorkspaceId = workspaceId;
		persistentWorkspace = true;
		await restoreWorkspacePackages().catch(() => undefined);
		return true;
	} catch {
		workspaceSync = null;
		attachedWorkspaceId = null;
		persistentWorkspace = false;
		return false;
	}
}

async function syncWorkspace(): Promise<void> {
	if (!workspaceSync) return;
	try { await workspaceSync(); } catch { /* keep kernel usable when persistence fails */ }
}

function fileExists(path: string): boolean {
	return rt ? rt.fs.exists(path) : false;
}

function readTextFile(path: string): string | null {
	if (!rt || !fileExists(path)) return null;
	try {
		return rt.fs.readFile(path, { encoding: 'utf8' }) as string;
	} catch {
		return null;
	}
}

function ensurePackageDir(): void {
	if (!rt || fileExists(PACKAGE_DIR)) return;
	try {
		rt.fs.mkdir(PACKAGE_DIR);
	} catch {
		/* directory may already exist */
	}
}

function readManifestPackages(): string[] {
	const text = readTextFile(PACKAGE_MANIFEST_PATH);
	if (!text) return [];
	try {
		return parsePackageManifest(text).packages;
	} catch {
		return [];
	}
}

function readWorkspacePackageSpecs(): string[] {
	let specs = readManifestPackages();
	const requirements = readTextFile(WORKSPACE_REQUIREMENTS_PATH);
	if (requirements) {
		specs = mergePackageSpecs(specs, parseRequirementsText(requirements));
	}
	return specs;
}

async function writePackageManifest(specs: string[]): Promise<void> {
	if (!rt) return;
	ensurePackageDir();
	rt.fs.writeFile(PACKAGE_MANIFEST_PATH, serializePackageManifest(specs));
	await syncWorkspace();
}

async function installPackageSpecs(specs: string[], persist: boolean): Promise<string[]> {
	if (!rt) return [];
	const normalized = mergePackageSpecs([], specs);
	if (normalized.length === 0) return [];
	await rt.runAsync(
		`import micropip\nawait micropip.install(${JSON.stringify(normalized)})\nimport importlib\nimportlib.invalidate_caches()`
	);
	packageRestoreError = '';
	if (persist) {
		const nextSpecs = mergePackageSpecs(readManifestPackages(), normalized);
		await writePackageManifest(nextSpecs);
		packageRestoreSignature = nextSpecs.join('\n');
	}
	return normalized;
}

async function restoreWorkspacePackages(): Promise<void> {
	const specs = readWorkspacePackageSpecs();
	const signature = specs.join('\n');
	if (!signature || signature === packageRestoreSignature) return;
	try {
		await installPackageSpecs(specs, false);
		packageRestoreSignature = signature;
		packageRestoreError = '';
	} catch (err) {
		packageRestoreError = String(err);
		throw err;
	}
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
	if (!rt) return { type: 'error', data: 'Pyodide not initialized', executedAt: new Date().toISOString() };

	stdoutBuffer = [];
	stderrBuffer = [];

	try {
		const pipSpecs = parsePipInstallCommand(code);
		if (pipSpecs) {
			const installedSpecs = await installPackageSpecs(pipSpecs, true);
			return {
				type: 'text',
				data: installedSpecs.length ? `Installed ${installedSpecs.join(', ')}` : 'No packages installed',
				executedAt: new Date().toISOString()
			};
		}

		// dartlab 을 import 하는 첫 셀이면 자동 설치(그 외 노트북은 미진입, 커널은 범용 유지).
		await ensureDartlab(code);
		const hasImport = /(?:^|\n)\s*(?:import |from )\S+/.test(code);
		if (hasImport) {
			await rt.loadPackagesFromImports(code);
			rt.run('import importlib; importlib.invalidate_caches()');
		}

		let wrappedCode = wrapCache.get(code);
		if (!wrappedCode) {
			wrappedCode = '__eddmlab_result__ = None\n' + wrapLastExpression(code);
			if (wrapCache.size >= 200) wrapCache.delete(wrapCache.keys().next().value!);
			wrapCache.set(code, wrappedCode);
		}
		await rt.runAsync(wrappedCode);

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

		const hasResult = rt.run('__eddmlab_result__ is not None') as boolean;
		const hasFigures = rt.run(
			"__import__('matplotlib.pyplot', fromlist=['pyplot']).get_fignums() if 'matplotlib' in __import__('sys').modules else []"
		);
		const needsFormat = hasResult || (hasFigures && (hasFigures as unknown[]).length > 0);

		let fmt = { repr: '', df: null as unknown, img: null as string | null, html: null as string | null, widget: null as string | null };
		if (needsFormat) {
			const raw = rt.run(FORMAT_CODE);
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
	} finally {
		await syncWorkspace();
	}
}

self.onmessage = async (e: MessageEvent) => {
	const { id, cmd, args } = e.data as { id: string; cmd: string; args: unknown[] };

	try {
		switch (cmd) {
			case 'initialize': {
				await initialize((args[0] as Uint8Array | null | undefined) ?? null);
				reply(id, { ok: true });
				break;
			}
			case 'attachWorkspace': {
				reply(id, await attachWorkspace(args[0] as string));
				break;
			}
			case 'getRuntimeCapabilities': {
				reply(id, {
					persistentWorkspace,
					interrupt: interruptMode,
					memoryTransactions: 'experimental',
					packagePersistence: 'workspace-manifest'
				});
				break;
			}
			case 'restoreWorkspacePackages': {
				await restoreWorkspacePackages();
				reply(id, { ok: true });
				break;
			}
			case 'createCheckpoint': {
				if (!pyodide) throw new Error('Pyodide not initialized');
				checkpointGraph ??= new CheckpointGraph(pyodide._module);
				reply(id, checkpointGraph.create((args[0] as string) || 'checkpoint'));
				break;
			}
			case 'restoreCheckpoint': {
				if (!checkpointGraph) throw new Error('checkpoint graph is empty');
				reply(id, checkpointGraph.restore(args[0] as string));
				break;
			}
			case 'listCheckpoints': {
				reply(id, checkpointGraph?.list() ?? []);
				break;
			}
			case 'clearCheckpoints': {
				checkpointGraph?.clear();
				checkpointGraph = null;
				reply(id, null);
				break;
			}
			case 'warm': {
				// 사전 로딩: 커널이 뜬 뒤 dartlab wheel 설치 + import 까지 미리 끝낸다. 사용자가 첫 셀을
				// 돌릴 때 21MB wheel + C 확장(polars·pyarrow) 다운로드를 기다리지 않게 하는 게 목적.
				// 실패해도 조용히 넘어간다(첫 import dartlab 셀에서 ensureDartlab 이 다시 시도).
				try {
					await ensureDartlab('import dartlab');
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
			case 'pyapi': {
				// browser-as-server: 페이지 fetch('/pyapi/*') 가 SW 를 거쳐 여기로. dartlab FastAPI 서빙.
				await ensureDartlab('import dartlab');
				if (!asgiKernel) throw new Error('kernel not initialized');
				try {
					await asgiKernel.install();
				} catch (err) {
					// pyproc 경로 설치 실패 시 손수 경로로 자동 폴백(조용한 죽은 커널 금지, PRD kill-switch).
					if (asgiKernel instanceof PyprocAsgi && pyodide) {
						asgiKernel = new HandRolledAsgi(pyodide);
						await asgiKernel.install();
					} else {
						throw err;
					}
				}
				const req = args[0] as { method: string; path: string; body?: string };
				const res = await asgiKernel.serve(req.method, req.path, req.body ?? '');
				reply(id, { status: res.status, headers: { 'content-type': 'application/json', 'x-dartlab-tier': 'browser', 'x-dartlab-kernel': asgiKernel.name }, body: res.body });
				break;
			}
			case 'getVariableNames': {
				if (!rt) { reply(id, []); break; }
				const result = rt.run("[k for k in dir() if not k.startswith('_')]");
				reply(id, Array.from(result as Iterable<string>));
				break;
			}
			case 'getVariablesWithInfo': {
				if (!rt) { reply(id, []); break; }
				const result = rt.run(`
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
				if (!rt) { reply(id, []); break; }
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
				const result = rt.run(code);
				const str = String(result);
				reply(id, (!str || str === 'None') ? [] : JSON.parse(str));
				break;
			}
			case 'installPackage': {
				if (!rt) { reply(id, null); break; }
				await installPackageSpecs([args[0] as string], true);
				reply(id, null);
				break;
			}
			case 'getInstalledPackages': {
				if (!rt) { reply(id, []); break; }
				const requestedSpecs = readWorkspacePackageSpecs();
				const requestedByKey = new Map(requestedSpecs.map((spec) => [packageSpecKey(spec), spec]));
				const result = await rt.runAsync(`
import json as __json__
import micropip
__pkgs__ = []
for __name__, __pkg__ in sorted(micropip.list().items()):
    __pkgs__.append({'name': __name__, 'version': str(__pkg__.version)})
__json__.dumps(__pkgs__)
`);
				const installed = JSON.parse(String(result)) as Array<{ name: string; version: string }>;
				const installedKeys = new Set<string>();
				const enriched: Array<{
					name: string;
					version: string;
					requested?: boolean;
					requirement?: string;
					missing?: boolean;
					error?: string;
				}> = installed.map((pkg) => {
					const key = packageSpecKey(pkg.name);
					installedKeys.add(key);
					const requirement = requestedByKey.get(key);
					return requirement ? { ...pkg, requested: true, requirement } : pkg;
				});
				for (const [key, requirement] of requestedByKey) {
					if (installedKeys.has(key)) continue;
					enriched.push({
						name: requirement,
						version: '',
						requested: true,
						requirement,
						missing: true,
						error: packageRestoreError || undefined
					});
				}
				reply(id, enriched);
				break;
			}
			case 'getDocstring': {
				if (!rt) { reply(id, null); break; }
				const name = args[0] as string;
				const result = rt.run(`
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
				if (!rt) { reply(id, null); break; }
				const [widgetId, value] = args as [string, unknown];
				const safeId = widgetId.replace(/'/g, "\\'");
				const valueStr = JSON.stringify(value);
				rt.run(`
from marimo._ui.base import UIElement as __UIElem__
__UIElem__._set_value('${safeId}', __import__('json').loads('${valueStr.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}'))
`);
				reply(id, null);
				break;
			}
			case 'listFiles': {
				if (!rt) { reply(id, []); break; }
				const path = args[0] as string;
				try {
					const entries = rt.fs.readdir(path);
					const result = entries.map((name) => {
						const fullPath = path.endsWith('/') ? path + name : path + '/' + name;
						try {
							const stat = rt!.fs.stat(fullPath);
							return { name, path: fullPath, isDir: stat.isDir, size: stat.size };
						} catch {
							return { name, path: fullPath, isDir: false, size: 0 };
						}
					});
					reply(id, result);
				} catch { reply(id, []); }
				break;
			}
			case 'readFile': {
				if (!rt) { reply(id, ''); break; }
				try {
					reply(id, rt.fs.readFile(args[0] as string, { encoding: 'utf8' }) as string);
				} catch { reply(id, ''); }
				break;
			}
			case 'writeFile': {
				if (!rt) { reply(id, null); break; }
				rt.fs.writeFile(args[0] as string, args[1] as string);
				await syncWorkspace();
				reply(id, null);
				break;
			}
			case 'mkdir': {
				if (!rt) { reply(id, null); break; }
				const p = args[0] as string;
				try { rt.fs.mkdir(p); } catch { /* exists */ }
				const initPath = p.endsWith('/') ? p + '__init__.py' : p + '/__init__.py';
				if (!rt.fs.exists(initPath)) {
					try { rt.fs.writeFile(initPath, ''); } catch { /* skip */ }
				}
				await syncWorkspace();
				reply(id, null);
				break;
			}
			case 'removeFile': {
				if (!rt) { reply(id, null); break; }
				await removeFileRecursive(args[0] as string);
				await syncWorkspace();
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
	const r = rt;
	if (!r) return;
	try {
		const stat = r.fs.stat(path);
		if (stat.isDir) {
			const entries = r.fs.readdir(path);
			for (const name of entries) {
				const child = path.endsWith('/') ? path + name : path + '/' + name;
				await removeFileRecursive(child);
			}
			r.fs.rmdir(path);
		} else {
			r.fs.unlink(path);
		}
	} catch { /* ignore */ }
}
