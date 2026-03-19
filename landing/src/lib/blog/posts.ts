export const categoryDefinitions = [
	{
		id: 'disclosure-systems',
		slug: 'disclosure-systems',
		folder: '01-disclosure-systems',
		label: '공시 시스템',
		description: 'DART와 EDGAR의 구조, form 체계, 원문 접근 방식을 다룹니다.',
		seoTitle: '공시 시스템 | DART와 EDGAR를 구조적으로 읽는 법',
		seoDescription:
			'DartLab 공시 시스템 카테고리. DART, EDGAR, 8-K, 20-F, 원문 공시와 form 구조를 실전적으로 읽는 글을 모았습니다.',
		brandMessage:
			'DartLab은 공시를 검색 결과가 아니라 시스템 구조로 읽습니다. DART와 EDGAR의 form, 제출 흐름, 원문 접근 방식을 실전적으로 정리합니다.'
	},
	{
		id: 'report-reading',
		slug: 'report-reading',
		folder: '02-report-reading',
		label: '사업보고서 읽기',
		description: '사업보고서와 핵심 서술 섹션을 실제 판단으로 연결하는 글입니다.',
		seoTitle: '사업보고서 읽기 | 텍스트와 리스크를 읽는 법',
		seoDescription:
			'DartLab 사업보고서 읽기 카테고리. 사업의 내용, 감사보고서, KAM, MD&A, 우발부채 같은 서술형 공시를 투자 판단으로 연결하는 글을 모았습니다.',
		brandMessage:
			'DartLab은 사업보고서를 숫자의 부록이 아니라 판단의 중심으로 봅니다. 텍스트, 리스크, 감사 문구를 실제 투자 해석으로 연결합니다.'
	},
	{
		id: 'financial-interpretation',
		slug: 'financial-interpretation',
		folder: '03-financial-interpretation',
		label: '재무 해석',
		description: '설비투자, 비용 구조, 주석 해석을 투자 판단 관점에서 풉니다.',
		seoTitle: '재무 해석 | 주석, 현금흐름, 이익의 질 읽는 법',
		seoDescription:
			'DartLab 재무 해석 카테고리. 생산능력, 건설중인자산, 감가상각, 매출채권, 대손충당금처럼 숫자 뒤 구조를 읽는 심화 글을 모았습니다.',
		brandMessage:
			'DartLab은 재무제표 숫자만 보지 않습니다. 주석, 현금흐름, 운전자본, 고정비 구조를 함께 읽어 이익의 질을 해석합니다.'
	},
	{
		id: 'data-automation',
		slug: 'data-automation',
		folder: '04-data-automation',
		label: '데이터 자동화',
		description: '공시 데이터를 수집하고 분석 파이프라인으로 연결하는 방법입니다.',
		seoTitle: '데이터 자동화 | OpenDART와 EDGAR 파이프라인',
		seoDescription:
			'DartLab 데이터 자동화 카테고리. OpenDART, EDGAR, XBRL, corp_code, 원문 공시를 실제 수집 파이프라인으로 연결하는 글을 모았습니다.',
		brandMessage:
			'DartLab은 공시를 손으로만 읽지 않습니다. OpenDART와 EDGAR 데이터를 파이프라인으로 묶어 반복 가능한 분석 구조를 만듭니다.'
	}
] as const;

export type CategoryId = (typeof categoryDefinitions)[number]['id'];
export type CategoryDefinition = (typeof categoryDefinitions)[number];

export const seriesDefinitions = {
	'dart-foundations': {
		id: 'dart-foundations',
		label: 'DART 첫걸음',
		description: 'DART에서 무엇부터 눌러야 하는지, OpenDART는 어디까지 되는지 입문자 기준으로 정리하는 시리즈입니다.',
		seoTitle: 'DART 첫걸음 | 전자공시를 처음부터 읽는 법',
		seoDescription: 'DartLab DART 첫걸음 시리즈. DART 구조, 첫 클릭 순서, OpenDART 역할을 입문자 기준으로 쉽게 정리합니다.',
		brandMessage: 'DartLab은 DART를 메뉴 많은 사이트가 아니라, 초보자도 길을 잃지 않게 만드는 전자공시 지도처럼 다룹니다.'
	},
	'edgar-reading': {
		id: 'edgar-reading',
		label: 'EDGAR 실전 입문',
		description: '10-K, 10-Q, 8-K, filing 원문을 한국 투자자 기준으로 빠르게 파악하게 만드는 시리즈입니다.',
		seoTitle: 'EDGAR 실전 입문 | 10-K, 8-K, filing 원문 읽는 법',
		seoDescription: 'DartLab EDGAR 실전 입문 시리즈. 10-K, 8-K, filing 원문, SEC form 구조를 실제 읽기 순서로 연결합니다.',
		brandMessage: 'DartLab은 EDGAR를 낯선 미국 서류 묶음이 아니라, 무엇을 언제 어떻게 확인해야 하는지 알려주는 읽기 흐름으로 정리합니다.'
	},
	'report-reading-foundations': {
		id: 'report-reading-foundations',
		label: '사업보고서 실전 읽기',
		description: '사업보고서의 핵심 섹션과 신규사업 문구를 실제 판단 순서에 맞춰 읽게 만드는 기본 시리즈입니다.',
		seoTitle: '사업보고서 실전 읽기 | 사업의 내용과 공시 텍스트 읽는 법',
		seoDescription: 'DartLab 사업보고서 실전 읽기 시리즈. 사업의 내용, 리스크, MD&A, 신규사업 계획, 텍스트 변화 신호를 실제 판단 흐름으로 연결합니다.',
		brandMessage: 'DartLab은 사업보고서를 숫자의 주변부가 아니라, 투자 판단의 방향을 먼저 바꾸는 본문으로 봅니다.'
	},
	'fixed-cost-and-capex': {
		id: 'fixed-cost-and-capex',
		label: '설비투자와 고정비',
		description: '생산능력, 건설중인자산, 감가상각, 유형자산 손상차손을 한 흐름으로 읽어 CAPEX 이후를 판단하게 만드는 시리즈입니다.',
		seoTitle: '설비투자와 고정비 | 생산능력, CAPEX, 손상차손 읽는 법',
		seoDescription: 'DartLab 설비투자와 고정비 시리즈. 생산능력, 가동률, 건설중인자산, 감가상각, 유형자산 손상차손을 연결해 투자 이후 비용 구조와 실패 신호를 읽는 글을 모았습니다.',
		brandMessage: 'DartLab은 설비투자를 좋은 뉴스로만 읽지 않고, 그 뒤에 따라오는 고정비와 마진 부담, 늦게 드러나는 손상차손까지 같이 봅니다.'
	},
	'financial-context': {
		id: 'financial-context',
		label: '숫자 뒤 맥락 읽기',
		description: '재무제표 숫자만으로 놓치는 사업 맥락과 해석의 함정을 개발비·무형자산, 리스부채, 리스 개정·세일앤리스백, 자산 매각 이익과 유동성 위기 가림, 관계사 자산 매각 이익, 관계사 매출 왜곡, 관계사 채권·대여금, 관계사 채권 대손충당금 지연, 지분법손익, 영업외손익, 환율·파생, 판관비 구조, 이연법인세, 기타포괄손익 누적, 매각예정자산·중단영업까지 포함해 잡아주는 입문형 시리즈입니다.',
		seoTitle: '숫자 뒤 맥락 읽기 | 재무제표 숫자만 보면 안 되는 이유',
		seoDescription: 'DartLab 숫자 뒤 맥락 읽기 시리즈. 숫자만 보지 않고 사업보고서, 신규사업, 개발비·무형자산, 리스부채, 리스 개정·세일앤리스백, 자산 매각 이익과 유동성 위기 가림, 관계사 자산 매각 이익, 관계사 매출 왜곡, 관계사 채권·대여금, 관계사 채권 대손충당금 지연, 지분법손익, 영업외손익, 환율·파생, 판관비 구조, 이연법인세, 기타포괄손익, 매각예정자산·중단영업 같은 공시 문맥을 함께 읽는 기초 글을 모았습니다.',
		brandMessage: 'DartLab은 숫자가 맞는지보다, 그 숫자가 왜 그렇게 나왔는지와 어떤 기대, 부채, 리스 재편, 관계사 거래와 내부 매출, 관계사 채권과 대여금, 늦게 커지는 대손충당금, 비본업 손익, 환율 효과, 세금 시차, OCI 누적, 분류 변화, 비용 구조가 뒤에 숨어 있는지까지 설명되는 분석을 더 중요하게 봅니다.'
	},
	'data-automation': {
		id: 'data-automation',
		label: '공시 데이터 파이프라인',
		description: 'OpenDART, corp_code, 공시 원문, XBRL을 실제 수집기 구조로 연결하는 시리즈입니다.',
		seoTitle: '공시 데이터 파이프라인 | OpenDART와 공시 수집 설계',
		seoDescription: 'DartLab 공시 데이터 파이프라인 시리즈. OpenDART, corp_code, 주요사항보고서, XBRL, 원문 데이터를 실제 수집 구조로 연결합니다.',
		brandMessage: 'DartLab은 공시를 읽는 법을 넘어서, 반복 가능한 수집기와 분석 파이프라인으로 연결하는 방법까지 다룹니다.'
	},
	'working-capital-and-earnings-quality': {
		id: 'working-capital-and-earnings-quality',
		label: '재고·채권·이익의 질',
		description: '매출채권, 재고, 재고평가손실·저가수주 압박, 수주잔고와 현금 괴리, 미청구공사·선수수익 비대칭, 공사손실충당부채, 추가원가·공사미수금 동시 악화, 공사선수금 감소·공사미수금 증가, 매출 인식 시점, 영업현금흐름, 선수금·계약부채, 팩토링·유동화, 공급망금융을 함께 봐서 성장의 질과 회수 구조를 읽는 시리즈입니다.',
		seoTitle: '재고·채권·이익의 질 | 운전자본, 매출 인식, 현금흐름 읽는 법',
		seoDescription: 'DartLab 재고·채권·이익의 질 시리즈. 매출채권, 대손충당금, 재고, 재고평가손실·저가수주 압박, 수주잔고와 현금 괴리, 미청구공사·선수수익 비대칭, 공사손실충당부채, 추가원가·공사미수금 동시 악화, 공사선수금 감소·공사미수금 증가, 매출 인식 시점, 영업현금흐름, 선수금·계약부채, 팩토링·유동화, 공급망금융을 통해 숫자 뒤 질을 해석합니다.',
		brandMessage: 'DartLab은 이익의 크기보다, 그 이익이 언제 잡혔는지, 미청구공사가 얼마나 앞서가는지, 공사손실충당부채가 왜 늦게 튀는지, 추가원가와 공사미수금이 함께 늘고 있는지, 공사선수금이 줄고 회사가 더 오래 버티는 구조로 바뀌는지, 가격을 얼마나 지키고 있는지, 실제로 회수되고 지급되는지와 어떤 금융기법 없이도 오래 버틸 수 있는지를 더 중요하게 봅니다.'
	},
	'audit-and-governance-reading': {
		id: 'audit-and-governance-reading',
		label: '감사와 경고 신호',
		description: '감사보고서, KAM, 한정·부적정·의견거절, 우발부채, 지급보증·담보·약정, 내부회계·감사위원회, 감사 전 내부결산 오류, 잠정실적·사업보고서 숫자 불일치, 잠정실적 정정 반복, 감사 후 정정공시, 감사위원회 반복 지적, 긴 활동내역 아래 약한 실질 감독, 적정 의견 아래 위험 신호, 계속기업 관련 불확실성, 차입 약정·기한이익상실 위험, 정정·재감사 신호, 감사보수·비감사보수, 자본잠식·관리종목 신호를 읽는 시리즈입니다.',
		seoTitle: '감사와 경고 신호 | 감사보고서, 비적정 의견, 우발부채 읽는 법',
		seoDescription: 'DartLab 감사와 경고 신호 시리즈. 감사보고서, KAM, 한정·부적정·의견거절, 우발부채, 소송, 지급보증, 담보, 약정, 내부회계, 감사위원회, 감사 전 내부결산 오류, 잠정실적·사업보고서 숫자 불일치, 잠정실적 정정 반복, 감사 후 정정공시, 감사위원회 반복 지적, 긴 활동내역 아래 약한 실질 감독, 계속기업 관련 불확실성, 차입 약정 위반 위험, 정정·재감사 신호, 감사보수·비감사보수, 자본잠식·관리종목 신호처럼 신뢰도 판단에 중요한 문구를 해석하는 글을 모았습니다.',
		brandMessage: 'DartLab은 감사의견 한 줄보다, 비적정 의견의 강도와 근거, 우발부채와 보증·담보 구조, 내부회계와 감독기구, 감사 전 내부결산 오류, 잠정실적과 사업보고서 숫자 불일치, 잠정실적 정정 반복, 감사 후 정정공시, 감사위원회의 반복 지적과 긴 활동내역 아래 남아 있는 약한 실질 감독, 계속기업 관련 불확실성, 차입 약정과 기한이익상실 가능성, 정정·재감사 신호, 감사보수와 비감사보수의 긴장감, 자본잠식과 관리종목 경고까지 포함해 그 뒤에서 실제로 무엇을 걱정하고 있는지를 보여주는 문구를 더 중요하게 봅니다.'
	},
	'ownership-and-governance-reading': {
		id: 'ownership-and-governance-reading',
		label: '대주주·보수·주주환원',
		description: '대주주, 특수관계인, 임원 보수, 주주환원, 주총 안건, 최대주주 주식담보, 스톡옵션을 실제 판단 기준으로 읽는 시리즈입니다.',
		seoTitle: '대주주·보수·주주환원 | 오너십과 지배구조 읽는 법',
		seoDescription: 'DartLab 대주주·보수·주주환원 시리즈. 최대주주, 특수관계인, 임원 보수, 주주환원, 주주총회소집공고, 최대주주 주식담보, 스톡옵션을 실제 판단 흐름으로 정리합니다.',
		brandMessage: 'DartLab은 숫자만이 아니라, 누가 회사 방향을 정하고 누가 혜택을 가져가며 누가 지분 압박을 받고 있고 어떤 방식으로 희석이 생기는지까지 함께 읽습니다.'
	},
	'industry-reading': {
		id: 'industry-reading',
		label: '업종별 공시 읽기',
		description: '건설, 바이오, 금융, 지주사, 유통·플랫폼처럼 업종마다 다른 공시 읽기 순서와 핵심 체크포인트를 정리하는 시리즈입니다.',
		seoTitle: '업종별 공시 읽기 | 건설, 바이오, 금융, 지주사 사업보고서 읽는 법',
		seoDescription: 'DartLab 업종별 공시 읽기 시리즈. 건설업 수주잔고, 바이오 개발비, 금융업 이자마진, 지주사 지분법, 유통 GMV처럼 업종마다 달라지는 공시 읽기 포인트를 실전 순서로 정리합니다.',
		brandMessage: 'DartLab은 같은 항목이라도 업종이 다르면 읽는 순서가 달라진다는 것을 보여줍니다. 건설업의 수주잔고, 바이오의 개발비, 금융업의 충당금, 지주사의 지분법손익, 유통의 GMV를 각각의 맥락에서 읽는 법을 정리합니다.'
	},
	'corporate-actions-and-financing': {
		id: 'corporate-actions-and-financing',
		label: '이벤트·자금조달 공시',
		description: '유상증자, 전환사채, 교환사채, 우선주·RCPS, RCPS 상환 압박·자본 재분류, RCPS 조건변경·상환 유예, 우선주 누적배당 현금 압박, 우선주 의무배당 미지급과 협상력 역전, 우선주 배당 스텝업 조항, 메자닌 보호조항과 만기연장·조건변경, 리픽싱 이후 실제 전환·오버행, 메자닌 조기상환 요구, 자기주식, 제3자배정, 최대주주 변경, 합병·분할, 감자·주식병합 같은 기업 이벤트 공시를 실제 판단 흐름으로 읽는 시리즈입니다.',
		seoTitle: '이벤트·자금조달 공시 | 유상증자, CB, 리픽싱 읽는 법',
		seoDescription:
			'DartLab 이벤트·자금조달 공시 시리즈. 유상증자, 전환사채, BW, 교환사채, 우선주, RCPS, RCPS 상환 압박·자본 재분류, RCPS 조건변경·상환 유예, 우선주 누적배당 현금 압박, 우선주 의무배당 미지급과 협상력 역전, 우선주 배당 스텝업 조항, 메자닌 보호조항과 만기연장·조건변경, 리픽싱 이후 실제 전환·오버행, 메자닌 조기상환 요구, 자기주식, 제3자배정, 최대주주 변경, 합병·분할, 감자·주식병합 같은 이벤트 공시를 실제 판단 흐름으로 정리합니다.',
		brandMessage: 'DartLab은 기업 이벤트 공시를 단발 뉴스가 아니라, 희석과 자금조달, 권리 구조, 지배력 변화, RCPS 조건변경과 상환 유예, 우선주 누적배당의 잠복 부담, 우선주 의무배당 미지급 이후 협상력 이동, 우선주 배당 스텝업이 시간을 더 비싸게 만드는 구조, 메자닌 보호조항과 조건변경, 실제 전환과 오버행, 조기상환 요구, 주가 착시의 신호로 읽습니다.'
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
