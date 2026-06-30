import type { PageLoad } from './$types';
import { createDartlabBrowser } from '$lib/browser/dartlabBrowser';

export const prerender = true;
export const ssr = false; // WebGL은 서버 렌더 불가 · 클라이언트 전용

export const load: PageLoad = async ({ fetch }) => {
	const dartlab = createDartlabBrowser({ fetchFn: fetch });
	return await dartlab.marketMap();
};
