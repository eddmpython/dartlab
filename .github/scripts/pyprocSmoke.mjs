// PYPROC GATE-A: 핀된 pyproc(Runtime + AsgiServer) x 현재 발행된 PyPI dartlab 이 브라우저 런타임에서
// 동작하는지 node-pyodide 로 검증. 주간 핀 범프 봇(pyprocPinBump.yml)이 새 pyproc SHA 를 착지시키기
// 전에 이 게이트를 통과해야 한다. dartlab 은 micropip 로 auto-sync 되므로 대상 = "핀 pyproc x PyPI 최신
// dartlab"(프로덕션 현실). boot() 은 main-thread(document) 전용이라 쓰지 않고, 워커 프로덕션 경로와
// 동일하게 node-pyodide 를 new Runtime(py) 로 채택한다(pyproc/runtime, SAB 쓰는 process-os 미유입).
//
// 사용: node .github/scripts/pyprocSmoke.mjs
// 요구: npm 에 pyproc(핀 SHA) + pyodide 설치. 네트워크(PyPI + pyodide CDN) 필요.
// 실측 기대: pyproc rt.run + rt.fs(파일 IO) + rt.setStdout + AsgiServer 로 dartlab /health 200. 실패 시 exit 1.

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

	// 워커가 raw pyodide.FS/setStdout 에서 rt.* 로 이관했으므로 그 계약을 게이트가 지킨다(pyproc 범프 회귀
	// 가드). migration notes #1(readFile 기본 binary·{utf8} 문자열)·#2(stat.isDir, mode 비트 없음)·
	// readdir(./.. 이미 필터)·writeFile(문자열→utf8)·exists. 하나라도 어긋나면 워커 파일 IO 가 깨진다.
	rt.fs.mkdir('/gate');
	rt.fs.writeFile('/gate/a.txt', 'x안녕'); // 문자열 → utf8 자동(워커 marimoShim/matplotlibrc 패턴)
	if (rt.fs.readFile('/gate/a.txt', { encoding: 'utf8' }) !== 'x안녕') throw new Error('rt.fs readFile{utf8} 원문 불일치(#1)');
	if (!(rt.fs.readFile('/gate/a.txt') instanceof Uint8Array)) throw new Error('rt.fs readFile 기본 binary 아님(#1)');
	if (rt.fs.stat('/gate').isDir !== true || rt.fs.stat('/gate/a.txt').isDir !== false) throw new Error('rt.fs stat.isDir 어긋남(#2)');
	const _ents = rt.fs.readdir('/gate');
	if (!_ents.includes('a.txt') || _ents.includes('.') || _ents.includes('..')) throw new Error('rt.fs readdir ./.. 필터 어긋남');
	if (rt.fs.exists('/gate/a.txt') !== true || rt.fs.exists('/gate/none') !== false) throw new Error('rt.fs exists 어긋남');
	rt.fs.unlink('/gate/a.txt');
	rt.fs.rmdir('/gate');
	if (rt.fs.exists('/gate') !== false) throw new Error('rt.fs unlink/rmdir 후 잔존');
	const _cap = [];
	rt.setStdout((t) => _cap.push(t));
	rt.run('print("gatecap")');
	rt.setStdout(null);
	if (!_cap.join('').includes('gatecap')) throw new Error('rt.setStdout 청크 캡처 실패');

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
