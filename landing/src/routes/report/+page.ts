import type { PageLoad } from './$types';

// 본진 기업분석보고서 · 데이터 작업대 리얼타임(조회 시점 조립). 정적 story JSON 폐기, 사전 bake 없음.
// ssr=false: 보고서는 HF parquet 을 브라우저가 직접 읽어 계산(rt.finance.bundle 은 클라이언트 포트).
export const ssr = false;
export const prerender = false;

export const load: PageLoad = ({ url }) => {
	const sym = url.searchParams.get('sym') || '005930';
	// 관점 키 · 레거시 'type=full' 은 첫 관점(수익성)으로 매핑.
	const raw = url.searchParams.get('view') || url.searchParams.get('type') || 'earningsPower';
	const perspective = raw === 'full' ? 'earningsPower' : raw;
	return { sym, perspective };
};
