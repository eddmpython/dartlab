export interface PostMeta {
	slug: string;
	title: string;
	date: string;
	description: string;
	thumbnail: string;
}

export const posts: PostMeta[] = [
	{
		slug: 'beyond-the-numbers',
		title: '재무제표, 숫자만 보면 안 되는 이유',
		date: '2026-03-08',
		description:
			'영업이익 30% 성장, PER 10배 — 이 숫자만 보고 투자를 결정하는가? 같은 숫자 뒤에 전혀 다른 이야기가 숨어 있다. 감사의견, 주석, 지배구조, 공시 텍스트까지 봐야 비로소 완전한 그림이 나온다.',
		thumbnail: '/avatar-celebrate.png'
	},
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
