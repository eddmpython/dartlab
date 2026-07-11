// PyPI publish 게이트: 발행될 바로 그 wheel 을 pyodide 에서 micropip.install + import dartlab 검증.
//
// 브라우저 dartlab(노트북·xlwings·블로그)은 micropip.install("dartlab") 로 PyPI 최신을 받는다.
// wheel 의존성 마커가 pyodide 를 깨면(예 marimo transitive msgspec: 순수휠 없음) 브라우저가 조용히
// 죽는다. 이 게이트가 publish 전에 그걸 잡는다. 실측: 0.10.7 은 여기서 FAIL, 0.10.9 는 PASS.
//
// 사용: node .github/scripts/pyodideSmoke.mjs dist/dartlab-x.y.z-py3-none-any.whl
// 요구: npm install pyodide (버전은 브라우저 워커와 맞춘다). 네트워크(PyPI + pyodide CDN) 필요.

import { loadPyodide } from 'pyodide';
import { readFileSync } from 'node:fs';

const wheelPath = process.argv[2];
if (!wheelPath) {
	console.error('사용: node pyodideSmoke.mjs <wheel 경로>');
	process.exit(2);
}
const wheelName = wheelPath.split(/[\\/]/).pop();

const t0 = Date.now();
const py = await loadPyodide();
await py.loadPackage(['micropip']);
py.FS.mkdirTree('/wheels');
py.FS.writeFile('/wheels/' + wheelName, new Uint8Array(readFileSync(wheelPath)));

try {
	const version = await py.runPythonAsync(`
import micropip
await micropip.install("emfs:/wheels/${wheelName}")
import dartlab
c = dartlab.Company  # 공개 진입점 로드 확인
assert dartlab.__version__, "no __version__"
dartlab.__version__
`);
	console.log(`[pyodide-smoke] PASS dartlab ${version} (${((Date.now() - t0) / 1000).toFixed(1)}s)`);
} catch (e) {
	console.error('[pyodide-smoke] FAIL: pyodide 에서 micropip.install 또는 import 실패');
	console.error(String(e).slice(-800));
	process.exit(1);
}
