import { DARTLAB_REQUIREMENT } from './runtimeManifest';

/**
 * dartlab 의 Pyodide 런타임 의존성을 한 번에 준비한다.
 *
 * dartlab 은 최상위 import 를 가볍게 유지하려고 polars 같은 모듈을 지연 import 한다. 따라서
 * 사용자 셀의 `import dartlab` 만 보고 패키지를 찾는 Pyodide 로더는 그 전이 의존성을 발견하지
 * 못한다. wheel 설치 전에 Pyodide 내장 C 확장을 명시적으로 적재하고, 동시에 들어온 사전 로딩과
 * 셀 실행은 같은 Promise 를 공유한다.
 */

interface RuntimeLike {
	loadPackages(packages: string[]): Promise<unknown>;
	install(packageName: string): Promise<unknown>;
	runAsync(code: string): Promise<unknown>;
}

const DARTLAB_IMPORT_RE = /(?:^|\n)[ \t]*(?:import[ \t]+dartlab|from[ \t]+dartlab[ \t.])/;

export const DARTLAB_PYODIDE_PACKAGES = ['lxml', 'numpy', 'polars', 'pyarrow'];
export const DARTLAB_PYODIDE_PRELOAD = DARTLAB_PYODIDE_PACKAGES
	.map((packageName) => `import ${packageName}`)
	.join('\n');

export function createDartlabRuntimeLoader(runtime: RuntimeLike) {
	let ready = false;
	let installing: Promise<void> | null = null;

	async function install(): Promise<void> {
		await runtime.loadPackages(DARTLAB_PYODIDE_PACKAGES);
		await runtime.runAsync(DARTLAB_PYODIDE_PRELOAD);
		await runtime.install(DARTLAB_REQUIREMENT);
		await runtime.runAsync('import dartlab');
		ready = true;
	}

	return {
		async ensure(code: string): Promise<void> {
			if (ready || !DARTLAB_IMPORT_RE.test(code)) return;
			installing ??= install().catch((error) => {
				installing = null;
				throw error;
			});
			await installing;
		},
		isReady(): boolean {
			return ready;
		}
	};
}
