import { describe, expect, it } from 'vitest';
import packageJson from '../../../../package.json';
import {
	BROWSER_RUNTIME_MANIFEST,
	DARTLAB_REQUIREMENT,
	PYODIDE_INDEX,
	PYPROC_CACHE_NAMESPACE
} from './runtimeManifest';

describe('browser runtime manifest', () => {
	it('설치된 pyproc exact pin과 런타임 정본이 같다', () => {
		expect(packageJson.dependencies.pyproc).toBe(BROWSER_RUNTIME_MANIFEST.pyproc);
		expect(BROWSER_RUNTIME_MANIFEST.pyproc).toMatch(/^\d+\.\d+\.\d+$/);
	});

	it('Pyodide, DartLab, cache namespace를 같은 정본에서 만든다', () => {
		expect(PYODIDE_INDEX).toContain(`/v${BROWSER_RUNTIME_MANIFEST.pyodide}/`);
		expect(DARTLAB_REQUIREMENT).toBe(`dartlab==${BROWSER_RUNTIME_MANIFEST.dartlab}`);
		expect(PYPROC_CACHE_NAMESPACE).toContain(
			`pyproc-${BROWSER_RUNTIME_MANIFEST.pyproc.replaceAll('.', '_')}`
		);
	});
});
