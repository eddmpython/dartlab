// kind 디스패처 · 앱 shell 진입점 1곳에서만 호출. surface 는 kind 를 모른다 (02 §1-5).
// 어댑터별 필수 옵션(public 의 shared 주입 등)이 다르므로 discriminated union 으로 받는다.
import type { DartLabRuntime } from '@dartlab/ui-contracts';
import { createPublicRuntime, type PublicRuntimeOptions } from './adapters/public/createPublicRuntime';
import { createLocalRuntime, type LocalRuntimeOptions } from './adapters/local/createLocalRuntime';
import { createFakeRuntime, type FakeRuntimeOptions } from './adapters/test/createFakeRuntime';

export type CreateRuntimeOptions =
	| { kind: 'public'; options: PublicRuntimeOptions }
	| { kind: 'local'; options: LocalRuntimeOptions }
	| { kind: 'test'; options?: FakeRuntimeOptions };

export function createRuntime(input: CreateRuntimeOptions): DartLabRuntime {
	switch (input.kind) {
		case 'public':
			return createPublicRuntime(input.options);
		case 'local':
			return createLocalRuntime(input.options);
		case 'test':
			return createFakeRuntime(input.options);
	}
}
