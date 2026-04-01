export interface NavItem {
	title: string;
	href: string;
	items?: NavItem[];
}

export const navigation: NavItem[] = [
	{
		title: 'Getting Started',
		href: '/docs/getting-started',
		items: [
			{ title: 'Installation', href: '/docs/getting-started/installation' },
			{ title: 'Quick Start', href: '/docs/getting-started/quickstart' },
			{ title: 'Sections — 회사 맵', href: '/docs/getting-started/sections' }
		]
	},
	{
		title: 'API Reference',
		href: '/docs/api',
		items: [
			{ title: '개요', href: '/docs/api/overview' },
			{ title: 'Company', href: '/docs/api/company' },
			{ title: '재무 데이터', href: '/docs/api/finance' },
			{ title: 'Analysis — 재무분석', href: '/docs/api/analysis' },
			{ title: 'Credit — 신용평가', href: '/docs/api/credit' },
			{ title: 'Scan — 횡단분석', href: '/docs/api/scan' },
			{ title: 'Gather — 시장 데이터', href: '/docs/api/gather' },
			{ title: 'Review — 보고서', href: '/docs/api/review' },
			{ title: 'AI — 분석가', href: '/docs/api/ai' },
			{ title: '고급 기능', href: '/docs/api/advanced' },
			{ title: 'MCP', href: '/docs/api/mcp' },
			{
				title: 'Full Reference',
				href: 'https://github.com/eddmpython/dartlab/blob/master/CAPABILITIES.md'
			}
		]
	},
	{
		title: 'Credit Reports',
		href: '/docs/credit/reports',
		items: [
			{ title: '삼성전자 dCR-AA', href: '/docs/credit/reports/005930_삼성전자' },
			{ title: 'SK하이닉스 dCR-AA+', href: '/docs/credit/reports/000660_SK하이닉스' },
			{ title: 'NAVER dCR-AA', href: '/docs/credit/reports/035420_NAVER' },
			{ title: 'LG dCR-AA', href: '/docs/credit/reports/003550_LG' }
		]
	},
	{
		title: 'Notebooks',
		href: '/docs/tutorials'
	},
	{
		title: 'About',
		href: '/docs/about'
	},
	{
		title: 'Changelog',
		href: '/docs/changelog'
	}
];

export function flattenNav(items: NavItem[]): NavItem[] {
	const result: NavItem[] = [];
	for (const item of items) {
		if (item.items && item.items.length > 0) {
			result.push(...flattenNav(item.items));
		} else {
			result.push(item);
		}
	}
	return result;
}

export function findPrevNext(
	path: string,
	items: NavItem[] = navigation
): { prev?: NavItem; next?: NavItem } {
	const flat = flattenNav(items);
	const idx = flat.findIndex((item) => path.endsWith(item.href));
	return {
		prev: idx > 0 ? flat[idx - 1] : undefined,
		next: idx < flat.length - 1 ? flat[idx + 1] : undefined
	};
}
