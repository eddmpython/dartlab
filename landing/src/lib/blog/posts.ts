export interface PostMeta {
	slug: string;
	title: string;
	date: string;
	description: string;
	thumbnail: string;
}

const modules = import.meta.glob('@blog/*.md', { eager: true }) as Record<
	string,
	{ metadata?: Record<string, string> }
>;

function buildPosts(): PostMeta[] {
	const result: PostMeta[] = [];
	for (const [path, mod] of Object.entries(modules)) {
		const m = mod.metadata;
		if (!m?.title || !m?.date) continue;
		const slug = path
			.replace(/^.*?\/blog\//, '')
			.replace(/^\d+-/, '')
			.replace(/\.md$/, '');
		result.push({
			slug,
			title: m.title,
			date: m.date,
			description: m.description ?? '',
			thumbnail: m.thumbnail ?? '/avatar-chart.png'
		});
	}
	return result.sort((a, b) => b.date.localeCompare(a.date));
}

export const posts: PostMeta[] = buildPosts();

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
