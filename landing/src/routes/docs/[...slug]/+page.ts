import type { EntryGenerator } from './$types';

const modules = import.meta.glob(
	[
		'@docs/getting-started/*.md',
		'@docs/user-guide/*.md',
		'@docs/api/*.md',
		'@docs/index.md',
		'!@docs/**/STATUS.md'
	],
	{ eager: true }
) as Record<string, { default: ConstructorOfATypedSvelteComponent; metadata?: Record<string, string> }>;

function normalizePath(rawPath: string): string {
	return rawPath.replace(/^.*?\/docs\//, '').replace(/\.md$/, '').replace(/\/index$/, '');
}

const slugMap = new Map<string, { component: ConstructorOfATypedSvelteComponent; metadata?: Record<string, string> }>();

for (const [path, mod] of Object.entries(modules)) {
	const slug = normalizePath(path);
	slugMap.set(slug, { component: mod.default, metadata: mod.metadata });
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
		slug
	};
}
