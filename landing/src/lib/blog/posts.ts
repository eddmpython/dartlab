export interface PostMeta {
	slug: string;
	title: string;
	date: string;
	description: string;
	thumbnail: string;
}

export const posts: PostMeta[] = [
	{
		slug: 'opendart-review',
		title: 'OpenDART, 솔직한 리뷰',
		date: '2026-03-08',
		description:
			'OpenDART는 세계적으로도 드문 무료 전자공시 API다. DART의 역사, XBRL 도입 과정, 좋은 점과 불편한 점, 그리고 앞으로의 기대까지 솔직하게 정리한다.',
		thumbnail: '/avatar-chart.png'
	},
	{
		slug: 'everything-about-dart',
		title: 'DART의 모든 것',
		date: '2026-03-08',
		description:
			'DART 전자공시시스템이란 무엇인가 — 사업보고서 12개 섹션, 주석 40개 항목, Open API의 한계까지 한 번에 정리한다.',
		thumbnail: '/avatar-study.png'
	}
];

export function getPost(slug: string): PostMeta | undefined {
	return posts.find((p) => p.slug === slug);
}

export function findPrevNext(slug: string): { prev?: PostMeta; next?: PostMeta } {
	const idx = posts.findIndex((p) => p.slug === slug);
	if (idx === -1) return {};
	return {
		prev: idx < posts.length - 1 ? posts[idx + 1] : undefined,
		next: idx > 0 ? posts[idx - 1] : undefined
	};
}
