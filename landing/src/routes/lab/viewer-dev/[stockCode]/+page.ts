import type { PageLoad } from './$types';
import { normalizeCompareTargets } from '@dartlab/ui-surfaces/viewer';

// 공시뷰어 · 브라우저가 HF panel 하나를 직접 읽어 온더플라이 렌더 (서버 0). 동적 종목.
export const prerender = 'auto';
export const ssr = false;

// ?vs=000660,035720 · 비교할 추가 회사(쉼표). 없으면 단일 뷰어.
export const load: PageLoad = ({ params, url }) => {
	const targets = normalizeCompareTargets(params.stockCode, url.searchParams.get('vs'));
	return {
		code: params.stockCode,
		vs: targets.vs,
		vsRejected: targets.rejected
	};
};
