import type { EntryGenerator } from './$types';

const modules = import.meta.glob(
	[
		'@docs/getting-started/*.md',
		'@docs/api/*.md',
		'@docs/tutorials/*.md',
		'@docs/changelog.md',
		'@docs/stability.md',
		'@docs/about.md',
		'!@docs/**/STATUS.md',
		'!@docs/index.md'
	],
	{ eager: true }
) as Record<string, { default: ConstructorOfATypedSvelteComponent; metadata?: Record<string, string> }>;
const rawModules = import.meta.glob(
	[
		'@docs/getting-started/*.md',
		'@docs/api/*.md',
		'@docs/tutorials/*.md',
		'@docs/changelog.md',
		'@docs/stability.md',
		'@docs/about.md',
		'!@docs/**/STATUS.md',
		'!@docs/index.md'
	],
	{ eager: true, query: '?raw', import: 'default' }
) as Record<string, string>;

function normalizePath(rawPath: string): string {
	return rawPath
		.replace(/^.*?\/docs\//, '')
		.replace(/\/\d+_/g, '/')
		.replace(/\.md$/, '')
		.replace(/\/index$/, '');
}

const slugMap = new Map<string, { component: ConstructorOfATypedSvelteComponent; metadata?: Record<string, string>; rawMarkdown: string }>();

for (const [path, mod] of Object.entries(modules)) {
	const slug = normalizePath(path);
	slugMap.set(slug, { component: mod.default, metadata: mod.metadata, rawMarkdown: rawModules[path] ?? '' });
}

export const entries: EntryGenerator = () => {
	return [...slugMap.keys()].map((slug) => ({ slug }));
};

export const prerender = true;

export function load({ params }: { params: { slug: string } }) {
	const slug = params.slug;
	const entry = slugMap.get(slug);

	if (!entry) {
		return { status: 404 };
	}

	return {
		component: entry.component,
		metadata: entry.metadata ?? {},
		rawMarkdown: entry.rawMarkdown,
		slug
	};
}
