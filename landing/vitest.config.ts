// 순수 lib 헬퍼 단위테스트 전용 vitest 설정 — SvelteKit vite.config(무거운 dev 플러그인·SSR noExternal)와
// 분리한다. 대상은 Svelte 비의존 순수 함수(render.ts 기하/포맷·cards projection)뿐이라 node 환경 + $lib alias 만
// 있으면 충분하고, sveltekit 플러그인을 끌어오지 않아 빠르고 결정론적이다. ($app/* 는 순수 헬퍼가 안 쓴다.)
import { defineConfig } from 'vitest/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
	resolve: {
		alias: { $lib: path.resolve(root, 'src/lib') }
	},
	test: {
		// scan 판정격자·URL 계약은 surfaces 에 살지만 Svelte 비의존 순수 함수라 같은 러너로 검사한다.
		// (surfaces 는 자체 vitest 를 두지 않는다. 러너 SSOT 는 landing 하나.)
		include: ['src/lib/**/*.test.ts', '../ui/packages/surfaces/src/scan/**/*.test.ts'],
		environment: 'node'
	}
});
