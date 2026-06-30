// Svelte context 주입 · surface 는 이 훅으로만 runtime 을 얻는다 (전역 locator 금지).
import { getContext, setContext } from 'svelte';
import type { DartLabRuntime } from '@dartlab/ui-contracts';

const KEY = Symbol('dartlab-runtime');

export function setDartLabRuntime(runtime: DartLabRuntime): void {
	setContext(KEY, runtime);
}

export function useDartLabRuntime(): DartLabRuntime {
	const runtime = getContext<DartLabRuntime | undefined>(KEY);
	if (!runtime) {
		throw new Error('DartLabRuntime context 미설정 · 앱 shell 에서 setDartLabRuntime() 으로 주입해야 한다.');
	}
	return runtime;
}
