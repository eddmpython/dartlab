export interface PostMeta {
	slug: string;
	title: string;
	date: string;
	description: string;
	thumbnail: string;
}

export const posts: PostMeta[] = [
	{
		slug: 'everything-about-edgar',
		title: 'EDGAR의 모든 것',
		date: '2026-03-11',
		description:
			'SEC EDGAR는 미국 자본시장의 핵심 인프라다. 10-K, 10-Q, 8-K, 20-F, 6-K, 13F가 각각 무엇을 담고 왜 중요한지, 제출 시한은 어떻게 다르고 데이터는 어떻게 공개되는지, 그리고 한국 투자자가 DART와 무엇을 다르게 읽어야 하는지 깊이 있게 정리한다.',
		thumbnail: '/avatar-chart.png'
	},
	{
		slug: 'python-financial-analysis',
		title: '파이썬으로 재무제표 분석하기',
		date: '2026-03-10',
		description:
			'파이썬으로 상장기업 재무제표를 분석하는 방법을 처음부터 끝까지 정리한다. 데이터 수집, 계정 표준화, 분기별 시계열, 재무비율, 기업 간 비교까지 — 엑셀로는 며칠 걸릴 작업을 코드 몇 줄로 끝내는 방법.',
		thumbnail: '/avatar-code.png'
	},
	{
		slug: 'reading-business-reports',
		title: '사업보고서 텍스트, 이렇게 읽는다',
		date: '2026-03-09',
		description:
			'사업보고서는 200페이지가 넘는 문서다. 어디서부터 읽어야 하고, 무엇을 찾아야 하며, 같은 문서에서 남들과 다른 인사이트를 뽑아내려면 어떻게 해야 하는가. 텍스트를 실제로 읽는 방법을 정리한다.',
		thumbnail: '/avatar-curious.png'
	},
	{
		slug: 'beyond-the-numbers',
		title: '재무제표, 숫자만 보면 안 되는 이유',
		date: '2026-03-08',
		description:
			'영업이익 30% 성장, PER 10배 — 이 숫자만 보고 투자를 결정하는가? 같은 숫자 뒤에 전혀 다른 이야기가 숨어 있다. 감사의견, 주석, 지배구조, 공시 텍스트까지 봐야 비로소 완전한 그림이 나온다.',
		thumbnail: '/avatar-writing.png'
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
