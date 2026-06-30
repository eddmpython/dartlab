import { describe, it, expect, vi, beforeEach } from 'vitest';

// origins 레지스트리는 mock · vitest 워크스페이스 해석 비의존 + URL 예측 가능.
vi.mock('@dartlab/ui-runtime/data/origins/registry', () => ({
	originUrl: (_id: string, path: string) => `https://media.test/${path}`
}));

/** path 부분일치로 JSON 응답하는 fetch 목. 미스 = 404(ok:false). */
function mockFetch(map: Record<string, unknown>) {
	return vi.fn(async (url: string) => {
		const key = Object.keys(map).find((k) => url.includes(k));
		if (key) return { ok: true, json: async () => map[key] } as unknown as Response;
		return { ok: false, json: async () => ({}) } as unknown as Response;
	});
}

const POSTS = [
	{ code: '005930', slug: '005930-samsung', title: '삼성', name: '삼성전자', date: '2026-01-02', slides: [] },
	{ code: '000660', slug: '000660-skhynix', name: 'SK하이닉스', date: '2026-01-01', slides: [] }
];

describe('단일 파일 캐러셀 계약', () => {
	beforeEach(() => vi.resetModules()); // 모듈 캐시(_all) 리셋

	it('loadCarousels 는 index.json posts[](전체 계약)를 1회 fetch·캐시', async () => {
		const f = mockFetch({ 'carousels/index.json': { posts: POSTS } });
		vi.stubGlobal('fetch', f);
		const { loadCarousels } = await import('./contract');
		const all = await loadCarousels();
		expect(all.map((c) => c.slug)).toEqual(['005930-samsung', '000660-skhynix']);
		await loadCarousels();
		expect(f).toHaveBeenCalledTimes(1); // 두 번 호출해도 fetch 1회
	});

	it('loadContract 는 추가 fetch 없이 캐시된 전체에서 슬러그로 찾는다', async () => {
		const f = mockFetch({ 'carousels/index.json': { posts: POSTS } });
		vi.stubGlobal('fetch', f);
		const { loadContract } = await import('./contract');
		const c = await loadContract('000660-skhynix');
		expect(c?.code).toBe('000660');
		expect(f).toHaveBeenCalledTimes(1); // per-slug round-trip 없음 · 단일 파일에서 찾기
		expect(String(f.mock.calls[0][0])).toContain('carousels/index.json');
		expect(await loadContract('nope')).toBeNull();
	});

	it('미게시(404) 면 빈 배열·계약 null(빈 화면 방지)', async () => {
		vi.stubGlobal('fetch', mockFetch({}));
		const { loadCarousels, loadContract } = await import('./contract');
		expect(await loadCarousels()).toEqual([]);
		expect(await loadContract('x')).toBeNull();
	});

	it('resolveSlideImage: 이슈 슬라이드(hfMedia 상대경로)는 회사 매니페스트 조회 없이 직접 해석', async () => {
		const { resolveSlideImage } = await import('./contract');
		// 슬래시 포함(issues/<slug>/...) = 이슈 → originUrl 로 그대로. media=null 이어도 해석됨.
		expect(resolveSlideImage(null, '', 'issues/2026-06-korea-macro/cover.ab12cd34.webp')).toBe(
			'https://media.test/issues/2026-06-korea-macro/cover.ab12cd34.webp'
		);
		// image 없으면 undefined.
		expect(resolveSlideImage(null, '', undefined)).toBeUndefined();
	});
});
