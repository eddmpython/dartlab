export const categoryDefinitions = [
	{
		id: 'reading-disclosures',
		slug: 'reading-disclosures',
		folder: '01-reading-disclosures',
		label: '공시 읽기',
		description: 'DART와 EDGAR 공시, 사업보고서, 감사보고서, 지배구조를 실전 판단으로 연결하는 글입니다.',
		seoTitle: '공시 읽기 | DART·EDGAR 사업보고서와 감사 신호 읽는 법',
		seoDescription:
			'DartLab 공시 읽기 카테고리. DART, EDGAR, 사업보고서, 감사보고서, 지배구조, 위험 신호, 업종별 읽기, 한미 비교까지 실전 판단으로 연결하는 글을 모았습니다.',
		brandMessage:
			'DartLab은 공시를 검색 결과가 아니라 판단의 중심으로 읽습니다. 사업보고서, 감사 문구, 지배구조, 위험 신호를 실제 투자 해석으로 연결합니다.'
	},
	{
		id: 'dartlab-news',
		slug: 'dartlab-news',
		folder: '02-dartlab-news',
		label: 'DartLab 소식',
		description: 'dartlab 설치, 업데이트, 사용 팁, 새 기능 소개를 다룹니다.',
		seoTitle: 'DartLab 소식 | 설치, 업데이트, 사용 팁',
		seoDescription:
			'DartLab 소식 카테고리. dartlab 설치 방법, 새 기능 소개, 업데이트 내역, 초보자 가이드를 모았습니다.',
		brandMessage:
			'DartLab은 누구나 전자공시 분석을 시작할 수 있도록, 설치부터 활용까지 쉽게 안내합니다.'
	},
	{
		id: 'corporate-analysis',
		slug: 'corporate-analysis',
		folder: '03-corporate-analysis',
		label: '실전기업분석',
		description: '수익 구조, 자금 구조, 투자 효율까지 기업 전체를 읽는 분석 프레임워크입니다.',
		seoTitle: '실전기업분석 | 수익 구조부터 투자 효율까지',
		seoDescription:
			'DartLab 실전기업분석 카테고리. 수익 구조, 비용 구조, 현금흐름, 부문별 이익률, 집중도 분석을 실제 기업 데이터로 정리합니다.',
		brandMessage:
			'DartLab은 재무제표 숫자 나열이 아니라, 이 회사가 무엇으로 돈을 벌고 구조가 얼마나 튼튼한지 판단하는 분석 흐름을 만듭니다.'
	},
	{
		id: 'credit-reports',
		slug: 'credit-reports',
		folder: '04-credit-reports',
		label: '신용분석 보고서',
		description: 'dartlab 독립 신용평가(dCR) 엔진이 산출한 기업별 신용분석 보고서입니다.',
		seoTitle: '신용분석 보고서 | dartlab 독립 신용평가(dCR)',
		seoDescription:
			'dartlab dCR 신용분석 보고서. 공시 데이터 기반 정량 분석으로 산출한 독립 신용등급, 등급 근거, 재무 하이라이트, 등급 전망을 제공합니다.',
		brandMessage:
			'DartLab은 공시 데이터만으로 재현 가능한 독립 신용등급을 산출합니다.'
	},
	{
		id: 'company-reports',
		slug: 'company-reports',
		folder: '05-company-reports',
		label: '기업분석 보고서',
		description: '6막 재무 서사 기반 기업별 종합 분석 보고서입니다.',
		seoTitle: '기업분석 보고서 | 6막 재무 서사',
		seoDescription:
			'dartlab 기업분석 보고서. 사업이해→수익성→현금전환→안정성→자본배분→전망의 6막 인과 구조로 기업을 분석합니다.',
		brandMessage:
			'DartLab은 숫자 나열이 아니라, 기업의 스토리를 6막 인과 구조로 전달합니다.'
	},
	{
		id: 'macro-reports',
		slug: 'macro-reports',
		folder: '06-macro-reports',
		label: '경제분석 보고서',
		description: '매월 자동 발간되는 매크로 경제분석 보고서입니다. 11축 분석 + 40개 투자전략.',
		seoTitle: '경제분석 보고서 | dartlab 매크로 엔진',
		seoDescription:
			'dartlab 경제분석 보고서. 사이클→금리→위기→전망의 3막 서사 구조로 경제를 분석합니다. Hamilton RS, Kalman DFM, Nelson-Siegel, BIS Credit-to-GDP gap 등 12개 방법론.',
		brandMessage:
			'DartLab은 종목코드 없이 경제 전체를 분석합니다. 매월 자동 발간.'
	}
] as const;

export type CategoryId = (typeof categoryDefinitions)[number]['id'];
export type CategoryDefinition = (typeof categoryDefinitions)[number];

export const seriesDefinitions = {
	'dart-foundations': {
		id: 'dart-foundations',
		label: 'DART 첫걸음',
		description: 'DART 구조와 OpenDART 역할을 입문자 기준으로 정리하는 시리즈입니다.',
		seoTitle: 'DART 첫걸음 | 전자공시를 처음부터 읽는 법',
		seoDescription: 'DartLab DART 첫걸음 시리즈. DART 구조, 첫 클릭 순서, OpenDART 역할을 입문자 기준으로 쉽게 정리합니다.',
		brandMessage: 'DartLab은 DART를 메뉴 많은 사이트가 아니라, 초보자도 길을 잃지 않게 만드는 전자공시 지도처럼 다룹니다.'
	},
	'edgar-reading': {
		id: 'edgar-reading',
		label: 'EDGAR 실전 입문',
		description: '10-K, 10-Q, 8-K, filing 원문과 Risk Factors를 한국 투자자 기준으로 파악하게 만드는 시리즈입니다.',
		seoTitle: 'EDGAR 실전 입문 | 10-K, 8-K, Risk Factors 읽는 법',
		seoDescription: 'DartLab EDGAR 실전 입문 시리즈. 10-K, 8-K, filing 원문, Risk Factors, MD&A를 실제 읽기 순서로 연결합니다.',
		brandMessage: 'DartLab은 EDGAR를 낯선 미국 서류 묶음이 아니라, 무엇을 언제 어떻게 확인해야 하는지 알려주는 읽기 흐름으로 정리합니다.'
	},
	'report-reading-foundations': {
		id: 'report-reading-foundations',
		label: '사업보고서 실전 읽기',
		description: '사업보고서의 핵심 섹션과 신규사업 문구를 실제 판단 순서에 맞춰 읽게 만드는 기본 시리즈입니다.',
		seoTitle: '사업보고서 실전 읽기 | 사업의 내용과 공시 텍스트 읽는 법',
		seoDescription: 'DartLab 사업보고서 실전 읽기 시리즈. 사업의 내용, 신규사업 계획, 텍스트 변화 신호를 실제 판단 흐름으로 연결합니다.',
		brandMessage: 'DartLab은 사업보고서를 숫자의 주변부가 아니라, 투자 판단의 방향을 먼저 바꾸는 본문으로 봅니다.'
	},
	'audit-and-governance': {
		id: 'audit-and-governance',
		label: '감사와 경고 신호',
		description: '감사보고서, KAM, 적정 의견 아래 위험 신호, 내부회계·감사위원회, 정정·재감사, 감사보수를 읽는 시리즈입니다.',
		seoTitle: '감사와 경고 신호 | 감사보고서, 비적정 의견, 우발부채 읽는 법',
		seoDescription: 'DartLab 감사와 경고 신호 시리즈. 감사보고서, KAM, 적정 의견 아래 위험 신호, 내부회계, 감사위원회, 정정·재감사 신호, 감사보수를 해석하는 글을 모았습니다.',
		brandMessage: 'DartLab은 감사의견 한 줄보다, 그 뒤에서 실제로 무엇을 걱정하고 있는지를 보여주는 문구를 더 중요하게 봅니다.'
	},
	'ownership-and-governance': {
		id: 'ownership-and-governance',
		label: '대주주·보수·주주환원',
		description: '대주주, 특수관계인, 임원 보수, 주주환원, 주총 안건, 지배구조 위험을 실제 판단 기준으로 읽는 시리즈입니다.',
		seoTitle: '대주주·보수·주주환원 | 오너십과 지배구조 읽는 법',
		seoDescription: 'DartLab 대주주·보수·주주환원 시리즈. 최대주주, 특수관계인, 임원 보수, 주주환원, 주주총회소집공고, 지배구조 위험을 실제 판단 흐름으로 정리합니다.',
		brandMessage: 'DartLab은 숫자만이 아니라, 누가 회사 방향을 정하고 누가 혜택을 가져가는지까지 함께 읽습니다.'
	},
	'industry-reading': {
		id: 'industry-reading',
		label: '업종별 공시 읽기',
		description: '건설, 바이오, 금융처럼 업종마다 다른 공시 읽기 순서와 핵심 체크포인트를 정리하는 시리즈입니다.',
		seoTitle: '업종별 공시 읽기 | 건설, 바이오, 금융 사업보고서 읽는 법',
		seoDescription: 'DartLab 업종별 공시 읽기 시리즈. 건설업 수주잔고, 바이오 개발비, 금융업 이자마진처럼 업종마다 달라지는 공시 읽기 포인트를 실전 순서로 정리합니다.',
		brandMessage: 'DartLab은 같은 항목이라도 업종이 다르면 읽는 순서가 달라진다는 것을 보여줍니다.'
	},
	'global-comparison': {
		id: 'global-comparison',
		label: '한미 공시 비교 실전',
		description: '같은 산업의 한국·미국 기업을 나란히 놓고 DART와 EDGAR 공시를 실전 비교하는 시리즈입니다.',
		seoTitle: '한미 공시 비교 실전 | DART vs EDGAR 같은 산업 다른 숫자',
		seoDescription: 'DartLab 한미 공시 비교 실전 시리즈. 같은 산업의 한국·미국 기업을 DART와 EDGAR 공시로 나란히 비교합니다.',
		brandMessage: 'DartLab은 같은 산업의 한국·미국 기업을 나란히 놓고 회계 기준, 공시 구조, 숫자의 의미 차이까지 직접 비교합니다.'
	},
	'financial-context': {
		id: 'financial-context',
		label: '숫자 뒤 맥락 읽기',
		description: '재무제표 숫자만으로 놓치는 사업 맥락과 해석의 함정을 잡아주는 시리즈입니다.',
		seoTitle: '숫자 뒤 맥락 읽기 | 재무제표 숫자만 보면 안 되는 이유',
		seoDescription: 'DartLab 숫자 뒤 맥락 읽기 시리즈. 개발비, 리스부채, 지분법손익, 영업외손익, 환율, 이연법인세, OCI 같은 공시 문맥을 함께 읽는 글을 모았습니다.',
		brandMessage: 'DartLab은 숫자가 맞는지보다, 그 숫자가 왜 그렇게 나왔는지를 더 중요하게 봅니다.'
	},
	'capital-and-earnings': {
		id: 'capital-and-earnings',
		label: '자본·이익의 질',
		description: 'CAPEX, 운전자본, 현금흐름, 유상증자, CB, RCPS, 메자닌까지 자본과 이익의 질을 읽는 시리즈입니다.',
		seoTitle: '자본·이익의 질 | CAPEX, 운전자본, 자금조달 읽는 법',
		seoDescription: 'DartLab 자본·이익의 질 시리즈. CAPEX, 매출채권, 재고, 수주잔고, 유상증자, CB, RCPS, 메자닌까지 자본과 이익의 질을 해석합니다.',
		brandMessage: 'DartLab은 이익의 크기보다, 그 이익이 진짜인지, 자금조달 구조가 건강한지를 더 중요하게 봅니다.'
	},
	'data-pipeline': {
		id: 'data-pipeline',
		label: '공시 데이터 파이프라인',
		description: 'OpenDART, corp_code, XBRL을 실제 수집기 구조로 연결하는 시리즈입니다.',
		seoTitle: '공시 데이터 파이프라인 | OpenDART와 공시 수집 설계',
		seoDescription: 'DartLab 공시 데이터 파이프라인 시리즈. OpenDART, corp_code, XBRL, 원문 데이터를 실제 수집 구조로 연결합니다.',
		brandMessage: 'DartLab은 공시를 읽는 법을 넘어서, 반복 가능한 수집기와 분석 파이프라인으로 연결하는 방법까지 다룹니다.'
	},
	'corporate-analysis': {
		id: 'corporate-analysis',
		label: '실전기업분석',
		description: '수익 구조, 자금 구조, 자산 구조, 투자 효율까지 기업 전체를 읽는 분석 프레임워크 시리즈입니다.',
		seoTitle: '기업 분석 실전 | 수익 구조부터 투자 효율까지 읽는 법',
		seoDescription: 'DartLab 기업 분석 실전 시리즈. 수익 구조, 비용 구조, 현금흐름, 부문별 이익률을 실제 기업 데이터로 분석합니다.',
		brandMessage: 'DartLab은 재무제표 숫자를 나열하는 것이 아니라, 이 회사가 무엇으로 돈을 벌고 구조가 얼마나 튼튼한지를 판단합니다.'
	},
	'dartlab-news': {
		id: 'dartlab-news',
		label: 'DartLab 소식',
		description: 'dartlab 설치, 업데이트, 사용 팁, 새 기능 소개를 다루는 시리즈입니다.',
		seoTitle: 'DartLab 소식 | 설치부터 활용까지',
		seoDescription: 'DartLab 소식 시리즈. dartlab 설치 방법, 초보자 가이드, 새 기능 소개, 업데이트 내역을 다룹니다.',
		brandMessage: 'DartLab은 전자공시 분석을 누구나 시작할 수 있도록, 설치부터 실전 활용까지 쉽게 안내합니다.'
	},
	'company-reports': {
		id: 'company-reports',
		label: '기업분석 보고서',
		description: '6막 재무 서사 기반 기업별 종합 분석 보고서입니다.',
		seoTitle: '기업분석 보고서 | 6막 재무 서사',
		seoDescription: 'dartlab 기업분석 보고서. 사업이해→수익성→현금전환→안정성→자본배분→전망의 6막 인과 구조로 기업을 분석합니다.',
		brandMessage: 'DartLab은 숫자 나열이 아니라, 기업의 스토리를 6막 인과 구조로 전달합니다.'
	}
} as const;

export type SeriesId = keyof typeof seriesDefinitions;
export type SeriesDefinition = (typeof seriesDefinitions)[SeriesId];

const categoryById = new Map<string, CategoryDefinition>(categoryDefinitions.map((category) => [category.id, category]));
const categoryBySlug = new Map<string, CategoryDefinition>(categoryDefinitions.map((category) => [category.slug, category]));

export interface PostMeta {
	slug: string;
	title: string;
	date: string;
	description: string;
	thumbnail: string;
	cardPreview: string;
	cardPreviewWebp?: string;
	previewAsset?: string;
	readingMinutes: number;
	category: CategoryId;
	categoryLabel: string;
	categoryFolder: string;
	order: number;
	series?: SeriesId;
	seriesLabel?: string;
	seriesOrder?: number;
}

type BlogModule = { metadata?: Record<string, string | number> };

const modules = import.meta.glob('@blog/**/index.md', { eager: true }) as Record<string, BlogModule>;
const rawModules = import.meta.glob('@blog/**/index.md', { eager: true, query: '?raw', import: 'default' }) as Record<string, string>;
const svgAssets = import.meta.glob('@blog/**/assets/*.svg', { eager: false }) as Record<string, () => Promise<unknown>>;

/** Build a map: post directory path → sorted list of SVG filenames */
function buildAssetIndex(): Map<string, string[]> {
	const index = new Map<string, string[]>();
	for (const assetPath of Object.keys(svgAssets)) {
		// assetPath: /blog/01-disclosure-systems/001-everything-about-dart/assets/001-disclosure-flow.svg
		const match = assetPath.match(/^(\/blog\/[^/]+\/[^/]+)\/assets\/([^/]+\.svg)$/);
		if (!match) continue;
		const postDir = match[1]; // /blog/01-disclosure-systems/001-everything-about-dart
		const fileName = match[2];
		const list = index.get(postDir) ?? [];
		list.push(fileName);
		index.set(postDir, list);
	}
	// Sort each list so first SVG is deterministic
	for (const list of index.values()) list.sort();
	return index;
}

const assetIndex = buildAssetIndex();

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

		const series = metadata.series ? (String(metadata.series).trim() as SeriesId) : undefined;
		const rawSeriesOrder = metadata.seriesOrder === undefined ? undefined : String(metadata.seriesOrder).trim();
		const seriesOrder = rawSeriesOrder ? Number.parseInt(rawSeriesOrder, 10) : undefined;
		const rawMarkdown = rawModules[path] ?? '';
		const readingMinutes = estimateReadingMinutes(rawMarkdown);
		const previewAsset = findPreviewAsset(path, rawMarkdown);
		const thumbnail = metadata.thumbnail ? String(metadata.thumbnail) : '/avatar-chart.png';
		const cardPreview = metadata.cardPreview ? String(metadata.cardPreview) : previewAsset ?? thumbnail;
		const cardPreviewWebp = toWebpAsset(cardPreview);

		result.push({
			slug: parsed.slug,
			title: String(metadata.title),
			date: String(metadata.date),
			description: metadata.description ? String(metadata.description) : '',
			thumbnail,
			cardPreview,
			cardPreviewWebp,
			previewAsset,
			readingMinutes,
			category: category.id,
			categoryLabel: category.label,
			categoryFolder: category.folder,
			order: parsed.order,
			series,
			seriesLabel: series ? seriesDefinitions[series]?.label ?? series : undefined,
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

function estimateReadingMinutes(rawMarkdown: string): number {
	if (!rawMarkdown) return 3;
	const withoutFrontmatter = rawMarkdown.replace(/^---[\s\S]*?---\s*/, '');
	const withoutCode = withoutFrontmatter.replace(/```[\s\S]*?```/g, ' ');
	const withoutImages = withoutCode.replace(/!\[[^\]]*\]\([^)]+\)/g, ' ');
	const plainText = withoutImages
		.replace(/\[[^\]]+\]\([^)]+\)/g, '$1')
		.replace(/[#>*`|_-]/g, ' ')
		.replace(/\s+/g, ' ')
		.trim();
	const tokenCount = plainText ? plainText.split(' ').length : 0;
	return Math.max(3, Math.ceil(tokenCount / 220));
}

function toWebpAsset(path: string): string | undefined {
	if (path.endsWith('.png')) return path.replace(/\.png$/i, '.webp');
	if (path.endsWith('.jpg')) return path.replace(/\.jpg$/i, '.webp');
	if (path.endsWith('.jpeg')) return path.replace(/\.jpeg$/i, '.webp');
	return undefined;
}

function findPreviewAsset(postPath: string, rawMarkdown: string): string | undefined {
	const firstSvgInBody = rawMarkdown.match(/!\[[^\]]*\]\(\.\/assets\/([^)]+\.svg)\)/i);
	if (firstSvgInBody) return `/blog/assets/${firstSvgInBody[1]}`;

	// postPath: /blog/01-disclosure-systems/001-everything-about-dart/index.md
	const postDir = postPath.replace(/\/index\.md$/, '');
	const svgs = assetIndex.get(postDir);
	if (!svgs || svgs.length === 0) return undefined;
	// Fallback for posts with svg assets but no explicit markdown hit.
	return `/blog/assets/${svgs[0]}`;
}

export const posts: PostMeta[] = buildPosts();

export function getPost(slug: string): PostMeta | undefined {
	return posts.find((post) => post.slug === slug);
}

export function getCategory(categoryIdOrSlug: string): CategoryDefinition | undefined {
	return categoryById.get(categoryIdOrSlug as CategoryId) ?? categoryBySlug.get(categoryIdOrSlug);
}

export function getCategoryPath(categoryIdOrSlug: string): string | undefined {
	const category = getCategory(categoryIdOrSlug);
	return category ? `/blog/category/${category.slug}` : undefined;
}

export function getPostsByCategory(categoryIdOrSlug: string): PostMeta[] {
	const category = getCategory(categoryIdOrSlug);
	if (!category) return [];
	return posts.filter((post) => post.category === category.id);
}

export function getCategoryGroups(): Array<CategoryDefinition & { posts: PostMeta[]; postCount: number; seriesLabels: string[] }> {
	return categoryDefinitions
		.map((category) => {
			const categoryPosts = posts.filter((post) => post.category === category.id);
			const seriesLabels = [...new Set(categoryPosts.map((post) => post.seriesLabel).filter(Boolean))] as string[];
			return {
				...category,
				posts: categoryPosts,
				postCount: categoryPosts.length,
				seriesLabels
			};
		})
		.filter((category) => category.posts.length > 0);
}

export function getLatestPosts(limit = 6): PostMeta[] {
	return posts.slice(0, limit);
}

export function getRelatedPostsByCategory(slug: string, limit = 3): PostMeta[] {
	const current = getPost(slug);
	if (!current) return [];
	return posts.filter((post) => post.category === current.category && post.slug !== slug).slice(0, limit);
}

export function getSeriesPosts(seriesId: string): PostMeta[] {
	return posts
		.filter((post) => post.series === seriesId)
		.sort((a, b) => {
			const bySeriesOrder = (a.seriesOrder ?? Number.MAX_SAFE_INTEGER) - (b.seriesOrder ?? Number.MAX_SAFE_INTEGER);
			if (bySeriesOrder !== 0) return bySeriesOrder;
			return a.order - b.order;
		});
}

export function getSeries(seriesId: string): SeriesDefinition | undefined {
	return seriesDefinitions[seriesId as SeriesId];
}

export function getSeriesPath(seriesId: string): string | undefined {
	const series = getSeries(seriesId);
	return series ? `/blog/series/${series.id}` : undefined;
}

export function getSeriesGroups(): Array<SeriesDefinition & { posts: PostMeta[]; postCount: number }> {
	return Object.values(seriesDefinitions)
		.map((series) => {
			const seriesPosts = getSeriesPosts(series.id);
			return {
				...series,
				posts: seriesPosts,
				postCount: seriesPosts.length
			};
		})
		.filter((series) => series.postCount > 0)
		.sort((a, b) => b.postCount - a.postCount || a.label.localeCompare(b.label));
}

export function getSeriesGroupsByCategory(categoryIdOrSlug: string): Array<SeriesDefinition & { posts: PostMeta[]; postCount: number }> {
	const category = getCategory(categoryIdOrSlug);
	if (!category) return [];
	return getSeriesGroups().filter((series) => series.posts.some((post) => post.category === category.id));
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

	const seriesPosts = getSeriesPosts(current.series);
	const idx = seriesPosts.findIndex((post) => post.slug === slug);
	if (idx === -1) return {};
	return {
		prev: idx > 0 ? seriesPosts[idx - 1] : undefined,
		next: idx < seriesPosts.length - 1 ? seriesPosts[idx + 1] : undefined
	};
}
