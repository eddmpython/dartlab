import { base } from '$app/paths';
import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

// 로컬 UI 진입 = 곧장 챗(기본 작업대). 운영자 지정: chat 이 기본, 터미널은 챗 종목 컨텍스트나 딥링크로 진입.
export const load: PageLoad = () => {
	redirect(307, `${base}/chat`);
};
