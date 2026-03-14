import type { EntryGenerator } from './$types';

const modules = import.meta.glob('@blog/**/index.md', { eager: true }) as Record<
	string,
	{ default: ConstructorOfATypedSvelteComponent; metadata?: Record<string, string> }
>;
const rawModules = import.meta.glob('@blog/**/index.md', { eager: true, query: '?raw', import: 'default' }) as Record<string, string>;

function normalizePath(rawPath: string): string {
	const match = rawPath.match(/\/blog\/[^/]+\/\d+-([^/]+)\/index\.md$/);
	return match?.[1] ?? '';
}

const slugMap = new Map<
	string,
	{ component: ConstructorOfATypedSvelteComponent; metadata?: Record<string, string>; rawMarkdown: string }
>();

for (const [path, mod] of Object.entries(modules)) {
	const slug = normalizePath(path);
	if (!slug) continue;
	slugMap.set(slug, { component: mod.default, metadata: mod.metadata, rawMarkdown: rawModules[path] ?? '' });
}

export const entries: EntryGenerator = () => {
	return [...slugMap.keys()].map((slug) => ({ slug }));
};

export const prerender = true;

export function load({ params }: { params: { slug: string } }) {
	const entry = slugMap.get(params.slug);

	if (!entry) {
		return { status: 404 };
	}

	return {
		component: entry.component,
		metadata: entry.metadata ?? {},
		rawMarkdown: entry.rawMarkdown,
		slug: params.slug,
		currentCategory: entry.metadata?.category ?? null
	};
}
