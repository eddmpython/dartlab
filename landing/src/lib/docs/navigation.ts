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
			{ title: 'Sections — 회사 맵', href: '/docs/getting-started/sections' },
			{ title: 'Quickstart', href: '/docs/getting-started/quickstart' }
		]
	},
	{
		title: 'API Reference',
		href: '/docs/api',
		items: [
			{ title: 'Overview', href: '/docs/api/overview' },
			{ title: 'finance.summary', href: '/docs/api/finance-summary' },
			{ title: 'finance.statements', href: '/docs/api/finance-statements' },
			{ title: 'All Modules', href: '/docs/api/finance-others' },
			{ title: 'Timeseries', href: '/docs/api/timeseries' },
			{ title: 'Sector', href: '/docs/api/sector' },
			{ title: 'Insight', href: '/docs/api/insight' },
			{ title: 'Rank', href: '/docs/api/rank' },
			{ title: 'Full Reference', href: 'https://github.com/eddmpython/dartlab/blob/master/CAPABILITIES.md' }
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
