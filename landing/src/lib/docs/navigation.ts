export interface NavItem {
	title: string;
	href: string;
	items?: NavItem[];
}

export const navigation: NavItem[] = [
	{
		title: '시작하기',
		href: '/docs/getting-started',
		items: [
			{ title: '설치', href: '/docs/getting-started/installation' },
			{ title: '빠른 시작', href: '/docs/getting-started/quickstart' }
		]
	},
	{
		title: '사용 가이드',
		href: '/docs/user-guide',
		items: [
			{ title: 'Bridge Matching', href: '/docs/user-guide/bridge-matching' }
		]
	},
	{
		title: 'API Reference',
		href: '/docs/api',
		items: [
			{ title: 'Overview', href: '/docs/api/overview' },
			{ title: 'finance.summary', href: '/docs/api/finance-summary' },
			{ title: 'finance.statements', href: '/docs/api/finance-statements' },
			{ title: '기타 모듈', href: '/docs/api/finance-others' }
		]
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
