// PYPROC GATE-A: 현재 landing이 쓰는 공개 machine 계약을 node-pyodide에서 검증한다.
// Pyodide 설치 버전은 landing/runtime-manifest.json에서 읽고 pyproc은 npm 설치본을 쓴다.

import { loadPyodide } from 'pyodide';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { dirname, join } from 'node:path';
import { readFileSync } from 'node:fs';

const RUNTIME_MANIFEST = JSON.parse(
	readFileSync(new URL('../../landing/runtime-manifest.json', import.meta.url), 'utf8')
);
const PYODIDE_VERSION = RUNTIME_MANIFEST.pyodide;
const DARTLAB_VERSION = RUNTIME_MANIFEST.dartlab;
const PYODIDE_INDEX = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
const startedAt = Date.now();

const pyprocEntry = createRequire(import.meta.url).resolve('pyproc', {
	paths: [process.cwd(), join(process.cwd(), 'landing')]
});
const pyprocVersion = JSON.parse(
	readFileSync(join(dirname(pyprocEntry), 'package.json'), 'utf8')
).version;
const { boot, checkEnvironment } = await import(pathToFileURL(pyprocEntry).href);

function requireValue(condition, message) {
	if (!condition) throw new Error(message);
}

try {
	let loaderCalls = 0;
	const stdout = [];
	const machine = await boot({
		indexURL: PYODIDE_INDEX,
		loadPyodide: async () => {
			loaderCalls += 1;
			return loadPyodide();
		},
		stdout: (text) => stdout.push(text)
	});
	const rt = machine.runtime;

	requireValue(loaderCalls === 1, `loadPyodide 호출 ${loaderCalls}회`);
	requireValue(machine.run('1 + 1') === 2, 'machine.run 기본 실행 실패');
	machine.fs.mkdir('/gate');
	machine.fs.writeFile('/gate/a.txt', 'x안녕');
	requireValue(
		machine.fs.readFile('/gate/a.txt', { encoding: 'utf8' }) === 'x안녕',
		'machine.fs UTF-8 왕복 실패'
	);
	requireValue(machine.fs.stat('/gate').isDir, 'machine.fs stat 실패');
	machine.fs.unlink('/gate/a.txt');
	machine.fs.rmdir('/gate');

	rt.setStdout((text) => stdout.push(text));
	machine.run('print("gatecap")');
	requireValue(stdout.join('').includes('gatecap'), 'runtime stdout 캡처 실패');

	machine.run('branch_value = 1');
	const branchA = machine.history.checkpoint();
	machine.run('branch_value = 2');
	machine.history.checkpoint();
	machine.history.restore(branchA);
	requireValue(machine.run('branch_value') === 1, 'history restore 실패');
	machine.run('branch_value = 3');
	const branchC = machine.history.checkpoint();
	const branchNode = machine.history.tree().find((node) => node.index === branchC.index);
	requireValue(branchNode?.parent === branchA.index, 'history 분기 부모 실패');

	await rt.loadPackages(['micropip', 'lxml', 'numpy', 'polars', 'pyarrow']);
	await rt.install(`dartlab==${DARTLAB_VERSION}`);
	const imported = machine.run(
		'import dartlab, polars, pyarrow, lxml, numpy; [dartlab.__version__, polars.__version__]'
	);
	const versions = Array.from(imported);
	imported.destroy?.();
	requireValue(versions[0] === DARTLAB_VERSION, `dartlab 버전 불일치: ${versions[0]}`);

	await machine.runAsync(`
import micropip
try:
    import fastapi
except ImportError:
    try:
        micropip.uninstall("typing-extensions")
    except Exception:
        pass
    await micropip.install("typing-extensions>=4.12.0")
    await micropip.install("fastapi")
import dartlab.webapi as _w
_dl_app = _w.buildBrowserApi()
`);
	const asgi = rt.enableAsgiServer({ app: '_dl_app' });
	await asgi.install();
	const health = await asgi.serve('GET', '/health', null, '');
	requireValue(health.status === 200, `/health status ${health.status}`);
	requireValue(JSON.parse(health.body).version === DARTLAB_VERSION, '/health dartlab 버전 불일치');

	const report = {
		ok: true,
		pyproc: pyprocVersion,
		pyodide: PYODIDE_VERSION,
		dartlab: DARTLAB_VERSION,
		history: { branchParent: branchNode.parent, restored: 1 },
		asgi: { status: health.status },
		environment: checkEnvironment(),
		elapsedMs: Date.now() - startedAt
	};
	console.log(`[pyproc-smoke] PASS ${JSON.stringify(report)}`);
} catch (error) {
	console.error('[pyproc-smoke] FAIL: 공개 machine 계약 검증 실패');
	console.error(String(error?.stack || error).slice(-1500));
	process.exit(1);
}
