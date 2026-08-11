import manifest from '../../../../runtime-manifest.json';

/**
 * 브라우저 Python 머신의 재현 가능한 환경 정본.
 *
 * Pyodide와 DartLab은 manifest에서, pyproc은 npm이 설치한 실제 버전에서 읽는다.
 * 세 버전 중 하나를 바꾸면 캐시 namespace도 함께 바뀐다.
 */
export const BROWSER_RUNTIME_MANIFEST = Object.freeze({ ...manifest, pyproc: __PYPROC_VERSION__ });

export const PYODIDE_INDEX =
	`https://cdn.jsdelivr.net/pyodide/v${BROWSER_RUNTIME_MANIFEST.pyodide}/full/`;
export const PYODIDE_CDN_ESM = `${PYODIDE_INDEX}pyodide.mjs`;
export const DARTLAB_REQUIREMENT = `dartlab==${BROWSER_RUNTIME_MANIFEST.dartlab}`;
export const PYPROC_CACHE_NAMESPACE = [
	`pyproc-${BROWSER_RUNTIME_MANIFEST.pyproc}`,
	`pyodide-${BROWSER_RUNTIME_MANIFEST.pyodide}`,
	`dartlab-${BROWSER_RUNTIME_MANIFEST.dartlab}`
].join('_').replaceAll('.', '_');
