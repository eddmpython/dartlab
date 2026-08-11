import { describe, expect, it } from 'vitest';
import packageJson from '../../../../package.json';
import {
	BROWSER_RUNTIME_MANIFEST,
	DARTLAB_REQUIREMENT,
	PYODIDE_INDEX,
	PYPROC_CACHE_NAMESPACE
} from './runtimeManifest';

describe('browser runtime manifest', () => {
	it('npm exact 의존성과 설치된 pyproc 버전을 일치시킨다', () => {
		expect(packageJson.dependencies.pyproc).toMatch(/^\d+\.\d+\.\d+$/);
		expect(BROWSER_RUNTIME_MANIFEST.pyproc).toMatch(/^\d+\.\d+\.\d+$/);
		expect(BROWSER_RUNTIME_MANIFEST.pyproc).toBe(packageJson.dependencies.pyproc);
	});

	it('Pyodide, DartLab, cache namespace를 같은 정본에서 만든다', () => {
		expect(PYODIDE_INDEX).toContain(`/v${BROWSER_RUNTIME_MANIFEST.pyodide}/`);
		expect(BROWSER_RUNTIME_MANIFEST.pyodideScriptIntegrity).toMatch(/^sha256-[A-Za-z0-9+/]+=$/);
		expect(DARTLAB_REQUIREMENT).toBe(`dartlab==${BROWSER_RUNTIME_MANIFEST.dartlab}`);
		expect(PYPROC_CACHE_NAMESPACE).toContain(
			`pyproc-${BROWSER_RUNTIME_MANIFEST.pyproc.replaceAll('.', '_')}`
		);
	});
});
