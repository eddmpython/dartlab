// PYPROC GATE-B (Tier-2): 실 headless Chromium + crossOriginIsolated(COEP credentialless) 에서
//  (1) R1: micropip 이 dartlab 휠(files.pythonhosted.org, CORP 없음)을 설치하나?
//  (2) fork: pyproc PyProc.boot(2) 스냅샷-fork + map 이 실동작하나?
// node 로는 못 덮는 프로세스 OS 경로(SAB + 중첩 워커)를 실브라우저에서 검증. pyprocPinBump.yml 의
// tier2/minor+ 핀 범프에서 돈다. 실측(로컬): R1 OK + fork 286ms/워커 + map 결과 정확.
//
// 사용: node .github/scripts/pyprocForkSmoke.mjs
// 요구: npm 에 pyproc(핀 SHA) + playwright + chromium(`npx playwright install chromium`). 네트워크 필요.
// 주의: pyproc v0.0.4 기본 indexURL 은 v314.0.2(부재)라 소비자가 indexURL 을 반드시 넘긴다.
import { chromium } from 'playwright';
import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { join, extname, dirname } from 'node:path';
import { createRequire } from 'node:module';

const PYODIDE_INDEX = 'https://cdn.jsdelivr.net/pyodide/v0.27.5/full/';
// pyproc 는 landing 워크스페이스 의존이라 npm install 시 landing/node_modules 로 간다. 루트/landing 양쪽 대응.
// pyproc 은 exports 맵이 있어 package.json 서브패스가 막힌다. '.'(index.js) 를 해소해 패키지 디렉토리를 얻는다.
const PYPROC_DIR = dirname(
	createRequire(import.meta.url).resolve('pyproc', { paths: [process.cwd(), join(process.cwd(), 'landing')] })
);
const MIME = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.map': 'application/json', '.wasm': 'application/wasm' };
const FN = 'def _fn(n):\\n    return sum(i*i for i in range(n))';

const TEST_HTML = `<!doctype html><html><head><meta charset="utf-8"></head><body>
<script type="module">
window.__r = { step: 'start', coi: globalThis.crossOriginIsolated };
try {
  const { boot, PyProc } = await import('/pyproc/index.js');
  const rt = await boot({ indexURL: '${PYODIDE_INDEX}' });
  window.__r.run = rt.run('1 + 1');
  await rt.install('micropip');
  await rt.runAsync('import micropip; await micropip.install("dartlab")');
  window.__r.wheelInstall = 'OK';
  window.__r.dartlabVersion = rt.run('import dartlab; dartlab.__version__');
  const os = new PyProc({ indexURL: '${PYODIDE_INDEX}' });
  window.__r.bootInfo = await os.boot(2);
  window.__r.forkOut = await os.map('${FN}', [1000, 2000]);
  os.terminate();
  window.__r.step = 'done';
} catch (e) { window.__r.error = String(e && e.stack || e).slice(-600); }
window.__done = true;
</script></body></html>`;

const server = http.createServer(async (req, res) => {
	res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
	res.setHeader('Cross-Origin-Embedder-Policy', 'credentialless');
	const url = (req.url || '/').split('?')[0];
	if (url === '/' || url === '/index.html') {
		res.setHeader('Content-Type', 'text/html; charset=utf-8');
		return res.end(TEST_HTML);
	}
	if (url.startsWith('/pyproc/')) {
		try {
			const body = await readFile(join(PYPROC_DIR, url.slice('/pyproc/'.length)));
			res.setHeader('Content-Type', MIME[extname(url)] || 'application/octet-stream');
			return res.end(body);
		} catch {
			res.statusCode = 404;
			return res.end('404');
		}
	}
	res.statusCode = 404;
	res.end('404');
});
await new Promise((r) => server.listen(0, r));
const port = server.address().port;

const browser = await chromium.launch({ headless: true });
try {
	const page = await browser.newPage();
	const logs = [];
	page.on('console', (m) => logs.push(m.text()));
	page.on('pageerror', (e) => logs.push('PAGEERR ' + String(e).slice(0, 300)));
	await page.goto(`http://localhost:${port}/`, { waitUntil: 'load' });
	try {
		await page.waitForFunction('window.__done === true', undefined, { timeout: 300000 });
	} catch (e) {
		logs.push('WAIT_TIMEOUT ' + String(e).slice(0, 120));
	}
	const r = await page.evaluate(() => window.__r || { step: 'no __r' });
	const pass =
		r.coi === true &&
		r.wheelInstall === 'OK' &&
		r.bootInfo &&
		r.bootInfo.forked === true &&
		Array.isArray(r.forkOut) &&
		r.forkOut.length === 2;
	if (pass) {
		console.log(`[pyproc-fork-smoke] PASS coi+휠설치(R1)+fork ${r.bootInfo.workers}워커/${r.bootInfo.avgBootMs}ms, map=${JSON.stringify(r.forkOut)}`);
	} else {
		console.error('[pyproc-fork-smoke] FAIL', JSON.stringify(r));
		console.error('LOGS:', logs.slice(-10).join('\n'));
	}
	process.exitCode = pass ? 0 : 1;
} finally {
	await browser.close();
	server.close();
}
