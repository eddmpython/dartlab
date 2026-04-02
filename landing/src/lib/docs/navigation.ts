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
			{ title: 'Sections', href: '/docs/getting-started/sections' }
		]
	},
	{
		title: 'API Reference',
		href: '/docs/api',
		items: [
			{ title: 'Overview', href: '/docs/api/overview' },
			{ title: 'Company', href: '/docs/api/company' },
			{ title: 'Financial Data', href: '/docs/api/finance' },
			{ title: 'Analysis', href: '/docs/api/analysis' },
			{ title: 'Credit Rating', href: '/docs/api/credit' },
			{ title: 'Scan', href: '/docs/api/scan' },
			{ title: 'Gather', href: '/docs/api/gather' },
			{ title: 'Review', href: '/docs/api/review' },
			{ title: 'AI', href: '/docs/api/ai' },
			{ title: 'Advanced', href: '/docs/api/advanced' },
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
			{ title: 'Samsung Electronics (dCR-AA)', href: '/docs/credit/reports/005930' },
			{ title: 'SK hynix (dCR-AA+)', href: '/docs/credit/reports/000660' },
			{ title: 'NAVER (dCR-AA)', href: '/docs/credit/reports/035420' },
			{ title: 'LG (dCR-AA)', href: '/docs/credit/reports/003550' }
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
