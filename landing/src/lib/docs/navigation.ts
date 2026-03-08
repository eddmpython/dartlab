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
			{ title: 'All Modules', href: '/docs/api/finance-others' }
		]
	},
	{
		title: 'Tutorials',
		href: '/docs/tutorials',
		items: [
			{ title: '1. Quickstart', href: '/docs/tutorials/quickstart' },
			{ title: '2. Financial Deep Dive', href: '/docs/tutorials/financial' },
			{ title: '3. Disclosure Text', href: '/docs/tutorials/disclosure' },
			{ title: '4. Advanced Analysis', href: '/docs/tutorials/advanced' }
		]
	},
	{
		title: 'User Guide',
		href: '/docs/user-guide',
		items: [
			{ title: 'Bridge Matching', href: '/docs/user-guide/bridge-matching' }
		]
	},
	{
		title: 'Changelog',
		href: '/docs/changelog'
	}
];

function flattenNav(items: NavItem[]): NavItem[] {
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
