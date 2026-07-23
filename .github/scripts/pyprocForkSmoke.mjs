// PYPROC GATE-B: 실 Chromium의 COI 환경에서 root machine, DartLab wheel, history, proc를 검증한다.
import { chromium } from 'playwright';
import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { join, extname, dirname } from 'node:path';
import { createRequire } from 'node:module';

const RUNTIME_MANIFEST = JSON.parse(
	await readFile(new URL('../../landing/runtime-manifest.json', import.meta.url), 'utf8')
);
const PYODIDE_VERSION = RUNTIME_MANIFEST.pyodide;
const DARTLAB_VERSION = RUNTIME_MANIFEST.dartlab;
const PYODIDE_INDEX = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
const PYPROC_DIR = dirname(
	createRequire(import.meta.url).resolve('pyproc', {
		paths: [process.cwd(), join(process.cwd(), 'landing')]
	})
);
const PYPROC_VERSION = JSON.parse(
	await readFile(join(PYPROC_DIR, 'package.json'), 'utf8')
).version;
if (PYPROC_VERSION !== RUNTIME_MANIFEST.pyproc) {
	throw new Error(`pyproc manifest ${RUNTIME_MANIFEST.pyproc} != installed ${PYPROC_VERSION}`);
}
const MIME = {
	'.js': 'text/javascript',
	'.mjs': 'text/javascript',
	'.json': 'application/json',
	'.map': 'application/json',
	'.wasm': 'application/wasm'
};
const FN = 'def _fn(n):\\n    return sum(i*i for i in range(n))';

const TEST_HTML = `<!doctype html><html><head><meta charset="utf-8"></head><body>
<script type="module">
window.__r = { step: 'start', coi: globalThis.crossOriginIsolated };
try {
  const { boot, checkEnvironment } = await import('/pyproc/index.js');
  const machine = await boot({ indexURL: '${PYODIDE_INDEX}', packages: ['micropip', 'polars'] });
  window.__r.run = machine.run('1 + 1');
  window.__r.environment = checkEnvironment();
  await machine.runtime.install('dartlab==${DARTLAB_VERSION}');
  window.__r.dartlabVersion = machine.run('import dartlab, polars; dartlab.__version__');
  machine.run('branch_value = 1');
  const a = machine.history.checkpoint();
  machine.run('branch_value = 2');
  machine.history.checkpoint();
  machine.history.restore(a);
  machine.run('branch_value = 3');
  const c = machine.history.checkpoint();
  window.__r.branchParent = machine.history.tree().find((node) => node.index === c.index)?.parent;
  window.__r.branchExpected = a.index;
  const pool = await machine.proc({ lanes: 2, indexURL: '${PYODIDE_INDEX}' });
  window.__r.forkOut = await pool.map('${FN}', [1000, 2000]);
  window.__r.processes = pool.ps().length;
  pool.terminate();
  window.__r.step = 'done';
} catch (error) {
  window.__r.error = String(error && error.stack || error).slice(-1200);
}
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
await new Promise((resolve) => server.listen(0, resolve));
const port = server.address().port;

const browser = await chromium.launch({ headless: true });
try {
	const page = await browser.newPage();
	const logs = [];
	page.on('console', (message) => logs.push(message.text()));
	page.on('pageerror', (error) => logs.push(`PAGEERR ${String(error).slice(0, 500)}`));
	await page.goto(`http://localhost:${port}/`, { waitUntil: 'load' });
	await page.waitForFunction('window.__done === true', undefined, { timeout: 300_000 });
	const result = await page.evaluate(() => window.__r);
	const pass =
		result.step === 'done' &&
		result.coi === true &&
		result.environment?.ok === true &&
		result.dartlabVersion === DARTLAB_VERSION &&
		result.branchParent === result.branchExpected &&
		Array.isArray(result.forkOut) &&
		result.forkOut.length === 2;
	if (!pass) throw new Error(`${JSON.stringify(result)}\n${logs.slice(-10).join('\n')}`);
	console.log(`[pyproc-fork-smoke] PASS ${JSON.stringify(result)}`);
} catch (error) {
	console.error('[pyproc-fork-smoke] FAIL');
	console.error(String(error?.stack || error).slice(-2000));
	process.exitCode = 1;
} finally {
	await browser.close();
	await new Promise((resolve) => server.close(resolve));
}
