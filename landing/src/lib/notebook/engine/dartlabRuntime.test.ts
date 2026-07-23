import { describe, expect, it, vi } from 'vitest';

import {
	createDartlabRuntimeLoader,
	DARTLAB_PYODIDE_PACKAGES,
	DARTLAB_PYODIDE_PRELOAD
} from './dartlabRuntime';
import { DARTLAB_REQUIREMENT } from './runtimeManifest';

describe('createDartlabRuntimeLoader', () => {
	it('dartlab 지연 import 전에 Pyodide 내장 의존성을 적재한다', async () => {
		const calls: string[] = [];
		const loader = createDartlabRuntimeLoader({
			loadPackages: vi.fn(async (packages: string[]) => {
				calls.push(`load:${packages.join(',')}`);
			}),
			install: vi.fn(async (packageName: string) => {
				calls.push(`install:${packageName}`);
			}),
			runAsync: vi.fn(async (code: string) => {
				calls.push(`run:${code}`);
			})
		});

		await loader.ensure('import dartlab\nc = dartlab.Company("005930")');

		expect(calls).toEqual([
			`load:${DARTLAB_PYODIDE_PACKAGES.join(',')}`,
			`run:${DARTLAB_PYODIDE_PRELOAD}`,
			`install:${DARTLAB_REQUIREMENT}`,
			'run:import dartlab'
		]);
		expect(loader.isReady()).toBe(true);
	});

	it('사전 로딩과 첫 셀이 겹쳐도 설치를 한 번만 실행한다', async () => {
		let release: (() => void) | undefined;
		const gate = new Promise<void>((resolve) => {
			release = resolve;
		});
		const runtime = {
			loadPackages: vi.fn(async () => gate),
			install: vi.fn(async () => undefined),
			runAsync: vi.fn(async () => undefined)
		};
		const loader = createDartlabRuntimeLoader(runtime);

		const warm = loader.ensure('import dartlab');
		const execute = loader.ensure('from dartlab import Company');
		release?.();
		await Promise.all([warm, execute]);

		expect(runtime.loadPackages).toHaveBeenCalledTimes(1);
		expect(runtime.install).toHaveBeenCalledTimes(1);
		expect(runtime.runAsync).toHaveBeenCalledTimes(2);
	});

	it('dartlab 을 쓰지 않는 일반 Python 셀은 건드리지 않는다', async () => {
		const runtime = {
			loadPackages: vi.fn(async () => undefined),
			install: vi.fn(async () => undefined),
			runAsync: vi.fn(async () => undefined)
		};
		const loader = createDartlabRuntimeLoader(runtime);

		await loader.ensure('print("hello")');

		expect(runtime.loadPackages).not.toHaveBeenCalled();
		expect(runtime.install).not.toHaveBeenCalled();
		expect(runtime.runAsync).not.toHaveBeenCalled();
	});

	it('설치가 실패하면 다음 요청에서 다시 시도한다', async () => {
		const runtime = {
			loadPackages: vi
				.fn()
				.mockRejectedValueOnce(new Error('network'))
				.mockResolvedValue(undefined),
			install: vi.fn(async () => undefined),
			runAsync: vi.fn(async () => undefined)
		};
		const loader = createDartlabRuntimeLoader(runtime);

		await expect(loader.ensure('import dartlab')).rejects.toThrow('network');
		await expect(loader.ensure('import dartlab')).resolves.toBeUndefined();

		expect(runtime.loadPackages).toHaveBeenCalledTimes(2);
		expect(loader.isReady()).toBe(true);
	});
});
