import { brand } from '$lib/brand';

export interface SeoThing {
	'@context'?: 'https://schema.org';
	'@type': string;
	[key: string]: unknown;
}

interface ArticleOptions {
	title: string;
	description: string;
	url: string;
	image?: string;
	type?: string;
	datePublished?: string;
	dateModified?: string;
	section?: string;
	keywords?: string[];
	isPartOf?: string;
}

interface BreadcrumbItem {
	name: string;
	url: string;
}

export interface FaqItem {
	question: string;
	answer: string;
}

const organizationId = `${brand.url}#organization`;
const websiteId = `${brand.url}#website`;

export function buildAbsoluteUrl(path = ''): string {
	return `${brand.url}${path.replace(/^\//, '')}`;
}

export function buildOrganizationJsonLd(): SeoThing {
	return {
		'@context': 'https://schema.org',
		'@type': 'Organization',
		'@id': organizationId,
		name: brand.name,
		url: brand.url,
		logo: buildAbsoluteUrl('og-image.png'),
		description: 'DartLab은 한국 DART 전자공시와 SEC EDGAR 데이터를 분석하는 오픈소스 도구다.',
		sameAs: [brand.repo, brand.pypi, brand.coffee]
	};
}

export function buildWebsiteJsonLd(): SeoThing {
	return {
		'@context': 'https://schema.org',
		'@type': 'WebSite',
		'@id': websiteId,
		name: brand.name,
		url: brand.url,
		description: 'DART 전자공시 분석과 공시 읽기 가이드를 제공하는 DartLab 공식 사이트',
		inLanguage: ['ko', 'en'],
		publisher: { '@id': organizationId },
		potentialAction: {
			'@type': 'SearchAction',
			target: `${buildAbsoluteUrl('search')}?q={search_term_string}`,
			'query-input': 'required name=search_term_string'
		}
	};
}

export function buildPersonJsonLd(): SeoThing {
	return {
		'@context': 'https://schema.org',
		'@type': 'Person',
		'@id': `${brand.url}#author`,
		name: 'eddmpython',
		url: 'https://github.com/eddmpython',
		worksFor: { '@id': organizationId },
		sameAs: [
			'https://github.com/eddmpython',
			'https://pypi.org/user/eddmpython/',
			'https://www.youtube.com/@eddmpython',
			'https://www.threads.net/@eddmpython',
			'https://eddm.tistory.com'
		]
	};
}

export function buildSoftwareApplicationJsonLd(): SeoThing {
	return {
		'@context': 'https://schema.org',
		'@type': 'SoftwareApplication',
		name: 'DartLab',
		alternateName: 'DART Disclosure Analysis Library',
		applicationCategory: 'DeveloperApplication',
		operatingSystem: 'Windows, macOS, Linux',
		description:
			'A Python library for DART and SEC EDGAR disclosure analysis. Parses financial statements, annual reports, and disclosure text into horizontalized time-series data.',
		url: brand.url,
		downloadUrl: brand.pypi,
		softwareVersion: brand.version,
		inLanguage: ['ko', 'en'],
		author: { '@type': 'Person', name: 'eddmpython', url: 'https://github.com/eddmpython' },
		publisher: { '@id': organizationId },
		offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
		license: 'https://opensource.org/licenses/MIT',
		programmingLanguage: 'Python',
		codeRepository: brand.repo,
		keywords: ['DART', '전자공시', 'OpenDART', 'EDGAR', 'financial statements', 'annual report', 'Python']
	};
}

export function buildArticleJsonLd(options: ArticleOptions): SeoThing {
	const keywords = (options.keywords ?? []).filter(Boolean);

	return {
		'@context': 'https://schema.org',
		'@type': options.type ?? 'Article',
		headline: options.title,
		name: options.title,
		description: options.description,
		url: options.url,
		mainEntityOfPage: options.url,
		image: options.image,
		datePublished: options.datePublished,
		dateModified: options.dateModified ?? options.datePublished,
		articleSection: options.section,
		keywords: keywords.length > 0 ? keywords.join(', ') : undefined,
		inLanguage: 'ko',
		author: { '@type': 'Person', name: 'eddmpython', url: 'https://github.com/eddmpython' },
		publisher: {
			'@type': 'Organization',
			'@id': organizationId,
			name: brand.name,
			logo: { '@type': 'ImageObject', url: buildAbsoluteUrl('og-image.png') }
		},
		isPartOf: options.isPartOf ? { '@id': options.isPartOf } : { '@id': websiteId }
	};
}

export function buildBreadcrumbJsonLd(items: BreadcrumbItem[]): SeoThing {
	return {
		'@context': 'https://schema.org',
		'@type': 'BreadcrumbList',
		itemListElement: items.map((item, index) => ({
			'@type': 'ListItem',
			position: index + 1,
			name: item.name,
			item: item.url
		}))
	};
}

function stripMarkdown(value: string): string {
	return value
		.replace(/```[\s\S]*?```/g, ' ')
		.replace(/`([^`]+)`/g, '$1')
		.replace(/!\[[^\]]*\]\([^)]+\)/g, ' ')
		.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
		.replace(/[*_>#-]/g, ' ')
		.replace(/\s+/g, ' ')
		.trim();
}

export function parseFaqFromMarkdown(rawMarkdown: string): FaqItem[] {
	if (!rawMarkdown) return [];

	const body = rawMarkdown.replace(/^---[\s\S]*?---\s*/, '');
	const lines = body.split('\n');
	const startIndex = lines.findIndex((line) => /^##\s+(FAQ|자주 묻는 질문)\s*$/i.test(line.trim()));
	if (startIndex === -1) return [];

	const sectionLines = [];
	for (let index = startIndex + 1; index < lines.length; index += 1) {
		const line = lines[index];
		if (/^##\s+/.test(line.trim())) break;
		sectionLines.push(line);
	}

	const faqs: FaqItem[] = [];
	let currentQuestion = '';
	let answerLines: string[] = [];

	function flush() {
		const answer = stripMarkdown(answerLines.join('\n'));
		if (currentQuestion && answer) {
			faqs.push({ question: stripMarkdown(currentQuestion), answer });
		}
		currentQuestion = '';
		answerLines = [];
	}

	for (const rawLine of sectionLines) {
		const line = rawLine.trim();
		if (/^###\s+/.test(line)) {
			flush();
			currentQuestion = line.replace(/^###\s+/, '').trim();
			continue;
		}
		answerLines.push(rawLine);
	}

	flush();
	return faqs;
}

export function buildFaqJsonLd(items: FaqItem[]): SeoThing {
	return {
		'@context': 'https://schema.org',
		'@type': 'FAQPage',
		mainEntity: items.map((item) => ({
			'@type': 'Question',
			name: item.question,
			acceptedAnswer: {
				'@type': 'Answer',
				text: item.answer
			}
		}))
	};
}
