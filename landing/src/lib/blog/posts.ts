export const categoryDefinitions = [
	{
		id: 'disclosure-systems',
		folder: '01-disclosure-systems',
		label: '공시 시스템',
		description: 'DART와 EDGAR의 구조, form 체계, 원문 접근 방식을 다룹니다.'
	},
	{
		id: 'report-reading',
		folder: '02-report-reading',
		label: '사업보고서 읽기',
		description: '사업보고서와 핵심 서술 섹션을 실제 판단으로 연결하는 글입니다.'
	},
	{
		id: 'financial-interpretation',
		folder: '03-financial-interpretation',
		label: '재무 해석',
		description: '설비투자, 비용 구조, 주석 해석을 투자 판단 관점에서 풉니다.'
	},
	{
		id: 'data-automation',
		folder: '04-data-automation',
		label: '데이터 자동화',
		description: '공시 데이터를 수집하고 분석 파이프라인으로 연결하는 방법입니다.'
	}
] as const;

export type CategoryId = (typeof categoryDefinitions)[number]['id'];

export const seriesDefinitions = {
	'dart-foundations': 'DART 기초 시리즈',
	'edgar-reading': 'EDGAR 읽기 시리즈',
	'report-reading-foundations': '사업보고서 읽기 시리즈',
	'fixed-cost-and-capex': '설비투자 해석 시리즈',
	'financial-context': '재무 맥락 읽기',
	'data-automation': '데이터 자동화 시리즈',
	'working-capital-and-earnings-quality': '운전자본·이익의 질 시리즈',
	'audit-and-governance-reading': '감사·거버넌스 읽기 시리즈'
} as const;

const categoryById = new Map(categoryDefinitions.map((category) => [category.id, category]));

export interface PostMeta {
	slug: string;
	title: string;
	date: string;
	description: string;
	thumbnail: string;
	category: CategoryId;
	categoryLabel: string;
	categoryFolder: string;
	order: number;
	series?: string;
	seriesLabel?: string;
	seriesOrder?: number;
}

type BlogModule = { metadata?: Record<string, string> };

const modules = import.meta.glob('@blog/**/index.md', { eager: true }) as Record<string, BlogModule>;

function parsePostPath(path: string): { categoryFolder: string; order: number; slug: string } | undefined {
	const match = path.match(/\/blog\/([^/]+)\/(\d+)-([^/]+)\/index\.md$/);
	if (!match) return undefined;
	return {
		categoryFolder: match[1],
		order: Number.parseInt(match[2], 10),
		slug: match[3]
	};
}

function buildPosts(): PostMeta[] {
	const result: PostMeta[] = [];
	for (const [path, mod] of Object.entries(modules)) {
		const parsed = parsePostPath(path);
		const metadata = mod.metadata;
		if (!parsed || !metadata?.title || !metadata?.date) continue;

		const categoryId = (metadata.category ? String(metadata.category) : undefined) as CategoryId | undefined;
		const category = categoryId ? categoryById.get(categoryId) : undefined;
		if (!category || category.folder !== parsed.categoryFolder) continue;

		const series = metadata.series ? String(metadata.series).trim() : undefined;
		const rawSeriesOrder = metadata.seriesOrder === undefined ? undefined : String(metadata.seriesOrder).trim();
		const seriesOrder = rawSeriesOrder ? Number.parseInt(rawSeriesOrder, 10) : undefined;

		result.push({
			slug: parsed.slug,
			title: metadata.title,
			date: metadata.date,
			description: metadata.description ?? '',
			thumbnail: metadata.thumbnail ?? '/avatar-chart.png',
			category: category.id,
			categoryLabel: category.label,
			categoryFolder: category.folder,
			order: parsed.order,
			series,
			seriesLabel: series ? seriesDefinitions[series as keyof typeof seriesDefinitions] ?? series : undefined,
			seriesOrder: Number.isNaN(seriesOrder) ? undefined : seriesOrder
		});
	}

	return result.sort((a, b) => {
		const byDate = b.date.localeCompare(a.date);
		if (byDate !== 0) return byDate;
		const byOrder = b.order - a.order;
		if (byOrder !== 0) return byOrder;
		return a.slug.localeCompare(b.slug);
	});
}

export const posts: PostMeta[] = buildPosts();

export function getPost(slug: string): PostMeta | undefined {
	return posts.find((post) => post.slug === slug);
}

export function getCategoryGroups(): Array<(typeof categoryDefinitions)[number] & { posts: PostMeta[] }> {
	return categoryDefinitions
		.map((category) => ({
			...category,
			posts: posts.filter((post) => post.category === category.id)
		}))
		.filter((category) => category.posts.length > 0);
}

export function findPrevNext(slug: string): { prev?: PostMeta; next?: PostMeta } {
	const idx = posts.findIndex((post) => post.slug === slug);
	if (idx === -1) return {};
	return {
		prev: idx < posts.length - 1 ? posts[idx + 1] : undefined,
		next: idx > 0 ? posts[idx - 1] : undefined
	};
}

export function findSeriesPrevNext(slug: string): { prev?: PostMeta; next?: PostMeta } {
	const current = getPost(slug);
	if (!current?.series) return {};

	const seriesPosts = posts
		.filter((post) => post.series === current.series)
		.sort((a, b) => {
			const bySeriesOrder = (a.seriesOrder ?? Number.MAX_SAFE_INTEGER) - (b.seriesOrder ?? Number.MAX_SAFE_INTEGER);
			if (bySeriesOrder !== 0) return bySeriesOrder;
			return a.order - b.order;
		});

	const idx = seriesPosts.findIndex((post) => post.slug === slug);
	if (idx === -1) return {};
	return {
		prev: idx > 0 ? seriesPosts[idx - 1] : undefined,
		next: idx < seriesPosts.length - 1 ? seriesPosts[idx + 1] : undefined
	};
}
