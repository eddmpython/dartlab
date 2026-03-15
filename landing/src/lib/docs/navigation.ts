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
			{ title: 'Rank', href: '/docs/api/rank' }
		]
	},
	{
		title: 'Tutorials',
		href: '/docs/tutorials',
		items: [
			{ title: '1. Quickstart', href: '/docs/tutorials/quickstart' },
			{ title: '2. Financial Statements', href: '/docs/tutorials/financial-statements' },
			{ title: '3. Timeseries', href: '/docs/tutorials/timeseries' },
			{ title: '4. Ratios', href: '/docs/tutorials/ratios' },
			{ title: '5. Report Data', href: '/docs/tutorials/report-data' },
			{ title: '6. Disclosure Text', href: '/docs/tutorials/disclosure' },
			{ title: '7. Advanced', href: '/docs/tutorials/advanced' },
			{ title: '8. Cross-Company', href: '/docs/tutorials/cross-company' },
			{ title: '9. US Stocks (EDGAR)', href: '/docs/tutorials/edgar' }
		]
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
