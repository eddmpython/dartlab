import type { PageLoad } from './$types';
import { createUniverseBrowser } from '$lib/browser/universeBrowser';
import type { UniverseReleaseState } from '@dartlab/ui-contracts';

export const prerender = true;
// Universe 데이터는 HF 원본을 브라우저에서 읽는다. 정적 빌드가 이 요청을
// 서버에서 실행하면 CORS 응답을 교차 출처로 판정하므로 셸만 prerender한다.
export const ssr = false;

function universeReleaseState(): UniverseReleaseState {
	const configured = (import.meta.env as Record<string, string | undefined>).VITE_DARTLAB_UNIVERSE_RELEASE_STATE;
	return configured === 'disabled' ? 'disabled' : 'ga';
}

export const load: PageLoad = async ({ fetch }) => {
	return await createUniverseBrowser({ fetchFn: fetch, universeReleaseState: universeReleaseState() }).seed();
};
