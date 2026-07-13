// PYPROC GATE-A: 핀된 pyproc(Runtime + AsgiServer) x 현재 발행된 PyPI dartlab 이 브라우저 런타임에서
// 동작하는지 node-pyodide 로 검증. 주간 핀 범프 봇(pyprocPinBump.yml)이 새 pyproc SHA 를 착지시키기
// 전에 이 게이트를 통과해야 한다. dartlab 은 micropip 로 auto-sync 되므로 대상 = "핀 pyproc x PyPI 최신
// dartlab"(프로덕션 현실). boot() 은 main-thread(document) 전용이라 쓰지 않고, 워커 프로덕션 경로와
// 동일하게 node-pyodide 를 new Runtime(py) 로 채택한다(pyproc/runtime, SAB 쓰는 process-os 미유입).
//
// 사용: node .github/scripts/pyprocSmoke.mjs
// 요구: npm 에 pyproc(핀 SHA) + pyodide 설치. 네트워크(PyPI + pyodide CDN) 필요.
// 실측 기대: pyproc Runtime.run + AsgiServer 로 dartlab /health 200. 실패 시 exit 1.

import { loadPyodide } from 'pyodide';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';

// pyproc 는 landing 워크스페이스 의존이라 npm install 시 landing/node_modules 로 간다(루트 아님).
// 루트/landing 양쪽에서 해소되도록 명시 paths.
const _ppRuntime = createRequire(import.meta.url).resolve('pyproc/runtime', {
	paths: [process.cwd(), join(process.cwd(), 'landing')]
});
const { Runtime } = await import(pathToFileURL(_ppRuntime).href);

const t0 = Date.now();
const el = () => ((Date.now() - t0) / 1000).toFixed(1) + 's';

try {
	const py = await loadPyodide();
	await py.loadPackage(['micropip']);

	const rt = new Runtime(py); // 우리 pyodide 를 채택(재부팅 안 함)
	if (rt.run('1 + 1') !== 2) throw new Error('Runtime.run 기본 실행 실패');

	// 워커 PYAPI 설치 시퀀스와 동일(fastapi lazy + typing-extensions 4.12 승격).
	await rt.runAsync(`
import micropip
await micropip.install("dartlab")
try:
    import fastapi  # noqa
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
	const health = await asgi.serve('GET', '/health', null, ''); // 실제 dartlab 라우트를 pyproc 으로 서빙
	if (health.status !== 200) throw new Error(`/health status ${health.status} (200 기대)`);

	const ver = JSON.parse(health.body).version || '?';
	console.log(`[pyproc-smoke] PASS pyproc Runtime+AsgiServer 가 dartlab ${ver} /health 200 서빙 (${el()})`);
} catch (e) {
	console.error('[pyproc-smoke] FAIL: pyproc Runtime/AsgiServer + dartlab 검증 실패');
	console.error(String(e).slice(-800));
	process.exit(1);
}
