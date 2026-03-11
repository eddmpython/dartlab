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
	const result: Array<PostMeta & { order: number }> = [];
	for (const [path, mod] of Object.entries(modules)) {
		const m = mod.metadata;
		if (!m?.title || !m?.date) continue;
		const match = path.match(/\/blog\/(\d+)-/);
		const order = match ? Number.parseInt(match[1], 10) : 0;
		const slug = path
			.replace(/^.*?\/blog\//, '')
			.replace(/^\d+-/, '')
			.replace(/\.md$/, '');
		result.push({
			order,
			slug,
			title: m.title,
			date: m.date,
			description: m.description ?? '',
			thumbnail: m.thumbnail ?? '/avatar-chart.png'
		});
	}
	return result
		.sort((a, b) => {
			const byDate = b.date.localeCompare(a.date);
			if (byDate !== 0) return byDate;
			const byOrder = b.order - a.order;
			if (byOrder !== 0) return byOrder;
			return a.slug.localeCompare(b.slug);
		})
		.map(({ order: _order, ...post }) => post);
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
