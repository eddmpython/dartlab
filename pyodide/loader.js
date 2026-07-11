// @ts-nocheck
/**
 * dartlab Pyodide 로더. 모든 배포 타겟(playground, xlwings lite, JupyterLite)이 공유.
 *
 * 사용법:
 *   import { initDartlab } from "./loader.js";
 *   const { py, run } = await initDartlab({ stockCode: "005930", onLog: console.log });
 *   await run(`print(c.show("IS").shape)`);
 */

const HF_BASE = "https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main";
const PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v0.27.2/full/pyodide.js";

const BUILTIN_PACKAGES = [
  "polars", "pyarrow", "micropip", "beautifulsoup4", "lxml",
  "httpx", "pydantic", "rich", "sqlite3", "numpy",
];


// finance + report 만 미리 받는다 (작고 흔함). panel 보드는 c.panel 첫 호출 시 lazy fetch.
// (옛 dart/docs 는 폐기 카테고리라 제거. HF 부재로 404 만 나던 죽은 경로였다.)
const DATA_CATEGORIES = [
  { dir: "dart/finance", name: "finance" },
  { dir: "dart/report", name: "report" },
];

/**
 * dartlab을 pyodide에서 초기화한다.
 *
 * @param {Object} options
 * @param {string} options.stockCode - 종목코드 (기본 "005930")
 * @param {(msg: string) => void} [options.onLog] - 로그 콜백
 * @param {(step: string, progress: number) => void} [options.onProgress] - 진행 콜백
 * @returns {{ py: PyodideInterface, run: (code: string) => Promise<any> }}
 */
export async function initDartlab(options = {}) {
  const {
    stockCode = "005930",
    onLog = () => {},
    onProgress = () => {},
  } = options;

  // 1. Pyodide 로드
  onProgress("pyodide", 0);
  onLog("[1/5] Pyodide 로드...");

  let loadPyodide;
  if (typeof globalThis.loadPyodide === "function") {
    loadPyodide = globalThis.loadPyodide;
  } else {
    // 동적 import (브라우저에서 CDN script 태그 없이 사용 시).
    // pyodide.js 는 UMD 라 import 네임스페이스에 loadPyodide 가 없고 side-effect 로
    // globalThis.loadPyodide 만 설정된다. 첫 호출 레이스 방지로 전역 fallback 을 함께 본다.
    const mod = await import(/* webpackIgnore: true */ PYODIDE_CDN);
    loadPyodide = mod.loadPyodide || globalThis.loadPyodide;
  }

  const py = await loadPyodide();
  onLog(`    Pyodide ${py.version}`);

  // 2. 빌트인 패키지
  onProgress("packages", 0.2);
  onLog("[2/5] 빌트인 패키지 로드...");
  await py.loadPackage(BUILTIN_PACKAGES);

  // 3. dartlab 설치 (PyPI). pip 과 같은 진입점·같은 버전이라 본체 릴리즈에 자동으로 맞는다.
  // micropip 이 PyPI 최신 wheel 을 받고 deps(diff-match-patch·openpyxl 등)를 자동 해소한다. C 확장은
  // 위에서 loadPackage 로 미리 올렸고, emscripten 마커로 서버/AI dep(marimo·mcp 등)은 빠진다.
  onProgress("wheel", 0.4);
  onLog("[3/5] dartlab 설치 (PyPI)...");

  await py.runPythonAsync(`
import micropip
await micropip.install("dartlab")
  `);

  // 4. HF parquet prefetch
  onProgress("data", 0.6);
  onLog("[4/5] HF 데이터 다운로드...");

  for (const cat of DATA_CATEGORIES) {
    const url = `${HF_BASE}/${cat.dir}/${stockCode}.parquet`;
    const r = await fetch(url);
    if (!r.ok) { onLog(`    ⚠ ${cat.name} 실패 (${r.status})`); continue; }
    const buf = new Uint8Array(await r.arrayBuffer());
    py.FS.mkdirTree(`/data/${cat.dir}`);
    py.FS.writeFile(`/data/${cat.dir}/${stockCode}.parquet`, buf);
    onLog(`    ${cat.name}: ${(buf.length / 1024).toFixed(0)} KB`);
  }

  // 5. import + Company 생성
  onProgress("init", 0.9);
  onLog("[5/5] dartlab 초기화...");

  py.setStdout({ batched: (msg) => onLog("    " + msg) });

  await py.runPythonAsync(`
import dartlab
c = dartlab.Company("${stockCode}")
  `);
  onLog(`    Company(${stockCode}) 준비 완료`);
  onProgress("done", 1.0);

  /** pyodide.runPythonAsync 래퍼 */
  async function run(code) {
    return await py.runPythonAsync(code);
  }

  return { py, run };
}

/**
 * 추가 종목 데이터를 prefetch하고 Company를 생성한다.
 */
export async function loadCompany(py, stockCode, options = {}) {
  const { onLog = () => {} } = options;

  for (const cat of DATA_CATEGORIES) {
    const url = `${HF_BASE}/${cat.dir}/${stockCode}.parquet`;
    const r = await fetch(url);
    if (!r.ok) { onLog(`⚠ ${cat.name} 실패`); continue; }
    const buf = new Uint8Array(await r.arrayBuffer());
    py.FS.mkdirTree(`/data/${cat.dir}`);
    py.FS.writeFile(`/data/${cat.dir}/${stockCode}.parquet`, buf);
  }

  await py.runPythonAsync(`c = dartlab.Company("${stockCode}")`);
  onLog(`Company(${stockCode}) 준비 완료`);
}

/**
 * 전종목 scan 프리빌드 경량본(`finance-lite.parquet`, ~18MB)을 FS에 다운로드한다.
 *
 * dartlab.scan() 이 호출되면 파이썬 측에서도 자동 fetch 가 시도되지만,
 * 대시보드 페이지처럼 미리 받아두는 게 UX 상 좋을 때 명시적으로 호출한다.
 *
 * @param {PyodideInterface} py
 * @param {Object} [options]
 * @param {(msg: string) => void} [options.onLog]
 */
export async function loadScanLite(py, options = {}) {
  const { onLog = () => {} } = options;
  const url = `${HF_BASE}/dart/scan/finance-lite.parquet`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`scan finance-lite fetch 실패: ${r.status} ${url}`);
  const buf = new Uint8Array(await r.arrayBuffer());
  py.FS.mkdirTree(`/data/dart/scan`);
  py.FS.writeFile(`/data/dart/scan/finance-lite.parquet`, buf);
  onLog(`scan finance-lite: ${(buf.length / 1024 / 1024).toFixed(1)} MB`);
}

/**
 * AI provider API 키를 설정한다.
 */
export async function setApiKey(py, provider, apiKey) {
  const envMap = {
    gemini: ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
    openai: ["OPENAI_API_KEY"],
  };
  const keys = envMap[provider];
  if (!keys) throw new Error(`지원하지 않는 provider: ${provider}`);

  for (const k of keys) {
    await py.runPythonAsync(`import os; os.environ["${k}"] = "${apiKey}"`);
  }
}
