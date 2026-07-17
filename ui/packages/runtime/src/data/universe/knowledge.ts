import type {
	UniverseKnowledgeContent,
	UniverseKnowledgeCoverage,
	UniverseKnowledgeDomain,
	UniverseKnowledgeDomainId,
	UniverseKnowledgeEdge,
	UniverseKnowledgeFilmBeat,
	UniverseKnowledgeNode,
	UniverseKnowledgeNodeKind,
	UniverseKnowledgeOverview,
	UniverseKnowledgeRelation,
	UniverseKnowledgeRepository,
	UniverseKnowledgeScene,
	UniverseKnowledgeSearchHit,
	UniverseKnowledgeSearchRequest,
	UniverseKnowledgeSearchResult
} from '@dartlab/ui-contracts';
import { UNIVERSE_KNOWLEDGE_SCHEMA_VERSION } from '@dartlab/ui-contracts';
import type { DataCore } from '../fetch/request';

const HF_REPOSITORY_ID = 'eddmpython/dartlab-data';
const MAX_SCENE_NODES = 80;

interface HfSibling {
	rfilename: string;
}

interface HfDatasetInfo {
	sha: string;
	lastModified: string;
	mainSize: number;
	usedStorage: number;
	siblings?: readonly HfSibling[];
}

interface HfTreeEntry {
	type: 'directory' | 'file';
	path: string;
}

interface SkillGraphNode {
	id: string;
	title: string;
	category: string;
	purpose: string;
	inDegree: number;
	outDegree: number;
	cluster: string;
}

interface SkillGraphEdge {
	src: string;
	dst: string;
	kind: string;
}

interface SkillGraphSource {
	nodes: readonly SkillGraphNode[];
	edges: readonly SkillGraphEdge[];
}

interface SkillCatalogEntry {
	id: string;
	title: string;
	category: string;
	purpose: string;
	whenToUse?: readonly string[];
	apiRefs?: readonly string[];
	datasetRefs?: readonly string[];
	knowledgeRefs?: readonly string[];
	sourceRefs?: readonly string[];
}

interface SkillCatalogSource {
	meta?: { skillCount?: number };
	skills: readonly SkillCatalogEntry[];
}

export interface UniverseKnowledgeLoaders {
	loadSkillGraph: () => Promise<SkillGraphSource>;
	loadSkillCatalog: () => Promise<SkillCatalogSource>;
}

export interface UniverseKnowledgeRuntime {
	overview(): Promise<UniverseKnowledgeOverview>;
	coverage(): Promise<UniverseKnowledgeCoverage>;
	search(request: UniverseKnowledgeSearchRequest): Promise<UniverseKnowledgeSearchResult>;
	open(targetId: string): Promise<UniverseKnowledgeScene>;
	content(targetId: string): Promise<UniverseKnowledgeContent>;
}

const CONTENT_BYTE_LIMIT = 64 * 1024;
const CONTENT_TEXT_DISPLAY_LIMIT = 20 * 1024;
const CONTENT_ROW_LIMIT = 12;
const CONTENT_COLUMN_LIMIT = 16;

const DOMAIN_COPY: Readonly<Record<UniverseKnowledgeDomainId, Omit<UniverseKnowledgeDomain, 'itemCount'>>> = {
	sources: {
		domainId: 'sources', label: '데이터 원천', labelEn: 'DATA SOURCES',
		description: 'Hugging Face 저장소, 메타데이터, 배포 산출물과 데이터 계보',
		sourceRefs: ['https://huggingface.co/datasets/eddmpython/dartlab-data']
	},
	entities: {
		domainId: 'entities', label: '법인과 기관', labelEn: 'ENTITIES',
		description: 'DART 법인, SEC CIK, 상장사, 기관과 식별자',
		sourceRefs: ['hf://dart', 'hf://edgar/tickers']
	},
	securities: {
		domainId: 'securities', label: '증권과 시장', labelEn: 'SECURITIES',
		description: '종목, 시장, 거래소, 지수와 가격 식별 체계',
		sourceRefs: ['hf://gov', 'hf://edgar/prices']
	},
	filings: {
		domainId: 'filings', label: '공시와 문서', labelEn: 'FILINGS',
		description: 'DART와 EDGAR 원문, 패널, 보고서, 검색 근거',
		sourceRefs: ['hf://dart/panel', 'hf://edgar/panel']
	},
	observations: {
		domainId: 'observations', label: '재무 관측', labelEn: 'OBSERVATIONS',
		description: '재무제표, 계정, 비율, 값, 단위와 관측 시점',
		sourceRefs: ['hf://dart/finance', 'hf://edgar/finance']
	},
	industry: {
		domainId: 'industry', label: '산업과 관계', labelEn: 'INDUSTRY',
		description: '산업 분류, 밸류체인, 공급망과 기업 관계',
		sourceRefs: ['hf://landing/map', 'dartlab://skills/engines.industry']
	},
	marketData: {
		domainId: 'marketData', label: '가격과 퀀트', labelEn: 'MARKET DATA',
		description: '주가, 거래량, 수급, 팩터, 기대와 정량 신호',
		sourceRefs: ['hf://gov/prices', 'hf://edgar/prices', 'dartlab://skills/engines.quant']
	},
	macro: {
		domainId: 'macro', label: '거시와 공공', labelEn: 'MACRO',
		description: '금리, 경기, 무역, 공공 통계와 거시 전파',
		sourceRefs: ['hf://macro', 'hf://gov/indices', 'dartlab://skills/engines.macro']
	},
	intelligence: {
		domainId: 'intelligence', label: '뉴스와 리서치', labelEn: 'INTELLIGENCE',
		description: '뉴스 메타, 증권사 리서치와 외부 지식 신호',
		sourceRefs: ['hf://news', 'hf://research']
	},
	capabilities: {
		domainId: 'capabilities', label: '엔진과 능력', labelEn: 'CAPABILITIES',
		description: 'DartLab 엔진, 분석 축, 실행 환경과 계산 계보',
		sourceRefs: ['dartlab://skills/engines', 'hf://pyodide']
	},
	skills: {
		domainId: 'skills', label: 'Skill OS', labelEn: 'SKILL OS',
		description: '사용 절차, 운영 계약, 분석 레시피와 지식 연결',
		sourceRefs: ['dartlab://skills/start.dartlabSkillOs']
	},
	timeMedia: {
		domainId: 'timeMedia', label: '시간과 미디어', labelEn: 'TIME AND MEDIA',
		description: '스냅샷, 변경 이력, 이미지, 영상과 표현 자산',
		sourceRefs: ['hf://assets', 'hf://landing']
	}
};

const DOMAIN_ORDER = Object.keys(DOMAIN_COPY) as UniverseKnowledgeDomainId[];

function emptyDomainCounts(): Record<UniverseKnowledgeDomainId, number> {
	return Object.fromEntries(DOMAIN_ORDER.map((domainId) => [domainId, 0])) as Record<UniverseKnowledgeDomainId, number>;
}

function normalizedPath(path: string): string {
	return path.replace(/^\/+|\/+$/g, '');
}

export function classifyKnowledgePath(inputPath: string): UniverseKnowledgeDomainId {
	const path = normalizedPath(inputPath).toLocaleLowerCase();
	if (path.startsWith('assets/')) return 'timeMedia';
	if (path.startsWith('news/') || path.startsWith('research/')) return 'intelligence';
	if (path.startsWith('macro/') || path.startsWith('gov/indices') || path.startsWith('krx/indices')) return 'macro';
	if (path.startsWith('gov/prices') || path.startsWith('krx/prices') || path.startsWith('edgar/prices') || path.startsWith('expectations/')) return 'marketData';
	if (path.startsWith('landing/map') || path.startsWith('dart/scan') || path.includes('/industry')) return 'industry';
	if (path.startsWith('dart/finance') || path.startsWith('edgar/finance')) return 'observations';
	if (path.startsWith('dart/panel') || path.startsWith('dart/report') || path.startsWith('dart/ipo')
		|| path.startsWith('dart/allfilings') || path.startsWith('dart/search') || path.startsWith('dart/contentindex')
		|| path.startsWith('edgar/panel') || path.startsWith('edgar/meta')) return 'filings';
	if (path.startsWith('edgar/tickers') || path.includes('corpcode') || path.includes('companyprofile') || path.includes('/profile')) return 'entities';
	if (path.startsWith('pyodide/')) return 'capabilities';
	if (path.startsWith('landing/') && /\.(png|webp|jpe?g|gif|svg|mp4|webm|m4a)$/i.test(path)) return 'timeMedia';
	if (path.startsWith('gov/') || path.startsWith('krx/') || path.includes('security')) return 'securities';
	return 'sources';
}

function skillDomain(category: string): UniverseKnowledgeDomainId {
	return category === 'engines' ? 'capabilities' : 'skills';
}

function lifecycleForPath(path: string): string {
	const lower = path.toLocaleLowerCase();
	if (lower.includes('/_staging/') || lower.includes('/staging/')) return 'staging';
	if (lower.includes('/compat') || lower.includes('/legacy')) return 'compatibility';
	return 'active';
}

function kindForPath(path: string, domainId: UniverseKnowledgeDomainId): UniverseKnowledgeNodeKind {
	if (/\.(png|webp|jpe?g|gif|svg|mp4|webm|m4a|mp3|wav)$/i.test(path)) return 'media';
	if (domainId === 'entities') return 'entity';
	if (domainId === 'observations' || domainId === 'marketData' || domainId === 'macro') return 'observation';
	if (domainId === 'filings' || /\.(md|txt|xml|html|pdf)$/i.test(path)) return 'document';
	return 'file';
}

function sourceUrl(revision: string, path: string): string {
	const encoded = normalizedPath(path).split('/').map(encodeURIComponent).join('/');
	return `https://huggingface.co/datasets/${HF_REPOSITORY_ID}/blob/${revision}/${encoded}`;
}

function contentUrl(revision: string, path: string): string {
	const encoded = normalizedPath(path).split('/').map(encodeURIComponent).join('/');
	return `https://huggingface.co/datasets/${HF_REPOSITORY_ID}/resolve/${encodeURIComponent(revision)}/${encoded}`;
}

function contentKind(path: string): UniverseKnowledgeContent['kind'] {
	const lower = path.toLocaleLowerCase();
	if (/\.(png|webp|jpe?g|gif|svg|avif)$/.test(lower)) return 'image';
	if (/\.(mp4|webm|mov)$/.test(lower)) return 'video';
	if (/\.(m4a|mp3|wav|ogg|flac)$/.test(lower)) return 'audio';
	if (lower.endsWith('.parquet')) return 'table';
	if (/\.(json|jsonl|ndjson)$/.test(lower)) return 'json';
	if (/\.(md|mdx|txt|csv|tsv|xml|html?|ya?ml|toml|ini|py|ts|js|css|sql)$/.test(lower)) return 'text';
	return 'binary';
}

function contentMime(kind: UniverseKnowledgeContent['kind'], path: string): string {
	const extension = path.split('.').at(-1)?.toLocaleLowerCase() ?? '';
	if (kind === 'image') return extension === 'svg' ? 'image/svg+xml' : `image/${extension === 'jpg' ? 'jpeg' : extension}`;
	if (kind === 'video') return `video/${extension === 'mov' ? 'quicktime' : extension}`;
	if (kind === 'audio') return `audio/${extension === 'm4a' ? 'mp4' : extension}`;
	if (kind === 'json') return extension === 'json' ? 'application/json' : 'application/x-ndjson';
	if (kind === 'table') return 'application/vnd.apache.parquet';
	if (kind === 'text') return extension === 'html' || extension === 'htm' ? 'text/html' : 'text/plain';
	return 'application/octet-stream';
}

function printableCell(value: unknown): string {
	if (value === null || value === undefined) return '';
	if (typeof value === 'bigint') return value.toString();
	if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
	try {
		return JSON.stringify(value, (_, item: unknown) => typeof item === 'bigint' ? item.toString() : item);
	} catch {
		return String(value);
	}
}

function parseJson<T>(response: Response): Promise<T> {
	if (!response.ok) throw new Error(`Universe knowledge source failed: ${response.status}`);
	return response.json() as Promise<T>;
}

function stableUnit(value: string): number {
	let hash = 2166136261;
	for (let index = 0; index < value.length; index += 1) {
		hash ^= value.charCodeAt(index);
		hash = Math.imul(hash, 16777619);
	}
	return (hash >>> 0) / 0xffffffff;
}

function radialPosition(index: number, count: number, nodeId: string): { x: number; y: number } {
	const ring = index < 24 ? 0 : index < 56 ? 1 : 2;
	const ringStart = ring === 0 ? 0 : ring === 1 ? 24 : 56;
	const ringSize = ring === 0 ? Math.min(count, 24) : ring === 1 ? Math.min(Math.max(0, count - 24), 32) : Math.max(1, count - 56);
	const angle = ((index - ringStart) / Math.max(1, ringSize)) * Math.PI * 2 - Math.PI / 2;
	const radii = [0.42, 0.7, 0.91] as const;
	const radius = (radii[ring] ?? radii[0]) + (stableUnit(nodeId) - 0.5) * 0.045;
	return { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius * 0.78 };
}

function makeNode(
	nodeId: string,
	label: string,
	secondaryLabel: string,
	kind: UniverseKnowledgeNodeKind,
	domainId: UniverseKnowledgeDomainId | null,
	weight: number,
	expandable: boolean,
	sourceRef: string,
	attributes: UniverseKnowledgeNode['attributes'],
	position: { x: number; y: number } = { x: 0, y: 0 }
): UniverseKnowledgeNode {
	return Object.freeze({ nodeId, label, secondaryLabel, kind, domainId, weight, x: position.x, y: position.y, expandable, sourceRef, attributes });
}

function filmFor(nodes: readonly UniverseKnowledgeNode[], edges: readonly UniverseKnowledgeEdge[]): readonly UniverseKnowledgeFilmBeat[] {
	const firstNode = nodes[0];
	if (!firstNode) return [];
	const focusNodes = [firstNode, ...nodes.slice(1).sort((left, right) => right.weight - left.weight || left.nodeId.localeCompare(right.nodeId)).slice(0, 5)];
	return focusNodes.map((node, index) => Object.freeze({
		beatId: `beat:${index}:${node.nodeId}`,
		label: index === 0 ? '전체 조망' : node.label,
		narration: index === 0 ? `${nodes.length.toLocaleString()}개 지식 개체의 구조를 먼저 봅니다.` : `${node.label}에서 연결된 지식과 원천을 따라갑니다.`,
		targetNodeId: node.nodeId,
		revealNodeIds: nodes.slice(0, Math.max(1, Math.ceil(((index + 1) / focusNodes.length) * nodes.length))).map((item) => item.nodeId),
		revealEdgeIds: edges.slice(0, Math.ceil(((index + 1) / focusNodes.length) * edges.length)).map((edge) => edge.edgeId),
		durationMs: index === 0 ? 2200 : 1900
	}));
}

function compileScene(input: {
	sceneId: string;
	title: string;
	subtitle: string;
	targetId: string;
	parentTargetId: string | null;
	breadcrumbs: UniverseKnowledgeScene['breadcrumbs'];
	center: UniverseKnowledgeNode;
	children: readonly UniverseKnowledgeNode[];
	relation?: UniverseKnowledgeRelation;
	indexedItemCount: number;
	sourceRevision: string;
}): UniverseKnowledgeScene {
	const children = input.children.slice(0, MAX_SCENE_NODES - 1).map((node, index, visible) => Object.freeze({
		...node,
		...radialPosition(index, visible.length, node.nodeId)
	}));
	const nodes = Object.freeze([Object.freeze({ ...input.center, x: 0, y: 0 }), ...children]);
	const edges = Object.freeze(children.map((node): UniverseKnowledgeEdge => Object.freeze({
		edgeId: `edge:${input.center.nodeId}:${node.nodeId}`,
		sourceId: input.center.nodeId,
		targetId: node.nodeId,
		relation: input.relation ?? 'contains',
		sourceRef: node.sourceRef
	})));
	return Object.freeze({
		schemaVersion: UNIVERSE_KNOWLEDGE_SCHEMA_VERSION,
		sceneId: input.sceneId,
		title: input.title,
		subtitle: input.subtitle,
		targetId: input.targetId,
		parentTargetId: input.parentTargetId,
		breadcrumbs: Object.freeze([...input.breadcrumbs]),
		nodes,
		edges,
		film: Object.freeze(filmFor(nodes, edges)),
		receipt: Object.freeze({
			indexedItemCount: input.indexedItemCount,
			outputNodeCount: nodes.length,
			outputEdgeCount: edges.length,
			omittedNodeCount: Math.max(0, input.children.length - children.length),
			sourceRevision: input.sourceRevision
		})
	});
}

function repository(info: HfDatasetInfo, fileCount: number | null): UniverseKnowledgeRepository {
	return Object.freeze({
		repositoryId: HF_REPOSITORY_ID,
		revision: info.sha,
		lastModified: info.lastModified,
		mainSizeBytes: info.mainSize,
		usedStorageBytes: info.usedStorage,
		fileCount
	});
}

function domainNode(domain: UniverseKnowledgeDomain, index: number, total: number): UniverseKnowledgeNode {
	const angle = (index / total) * Math.PI * 2 - Math.PI / 2;
	return makeNode(
		`domain:${domain.domainId}`,
		domain.label,
		domain.itemCount === null ? domain.labelEn : `${domain.itemCount.toLocaleString()} items`,
		'domain',
		domain.domainId,
		16 + Math.log10(Math.max(1, domain.itemCount ?? 1)) * 5,
		true,
		domain.sourceRefs[0] ?? '',
		{ description: domain.description, labelEn: domain.labelEn },
		{ x: Math.cos(angle) * 0.76, y: Math.sin(angle) * 0.6 }
	);
}

function rootScene(domains: readonly UniverseKnowledgeDomain[], info: HfDatasetInfo, rootEntries: readonly HfTreeEntry[], skillRelationCount: number): UniverseKnowledgeScene {
	const center = makeNode(
		'knowledge:root', 'DartLab', 'UNIFIED KNOWLEDGE', 'root', null, 34, false,
		`https://huggingface.co/datasets/${HF_REPOSITORY_ID}`,
		{ rootEntryCount: rootEntries.length, skillRelationCount, revision: info.sha }
	);
	const nodes = [center, ...domains.map((domain, index) => domainNode(domain, index, domains.length))];
	const edges = nodes.slice(1).map((node): UniverseKnowledgeEdge => ({
		edgeId: `edge:knowledge:root:${node.nodeId}`,
		sourceId: center.nodeId,
		targetId: node.nodeId,
		relation: 'contains',
		sourceRef: node.sourceRef
	}));
	return Object.freeze({
		schemaVersion: UNIVERSE_KNOWLEDGE_SCHEMA_VERSION,
		sceneId: `knowledge:root:${info.sha}`,
		title: 'DartLab Knowledge Universe',
		subtitle: '모든 데이터, 문서, 엔진, 스킬과 근거를 하나의 주소 공간에서 탐색합니다.',
		targetId: center.nodeId,
		parentTargetId: null,
		breadcrumbs: Object.freeze([{ targetId: center.nodeId, label: 'Universe' }]),
		nodes: Object.freeze(nodes),
		edges: Object.freeze(edges),
		film: Object.freeze(filmFor(nodes, edges)),
		receipt: Object.freeze({ indexedItemCount: domains.length, outputNodeCount: nodes.length, outputEdgeCount: edges.length, omittedNodeCount: 0, sourceRevision: info.sha })
	});
}

function groupFiles(paths: readonly string[], prefix: string): Array<{ path: string; count: number; file: boolean }> {
	const normalizedPrefix = normalizedPath(prefix);
	const prefixWithSlash = normalizedPrefix ? `${normalizedPrefix}/` : '';
	const groups = new Map<string, { path: string; count: number; file: boolean }>();
	for (const path of paths) {
		if (normalizedPrefix && path !== normalizedPrefix && !path.startsWith(prefixWithSlash)) continue;
		const rest = normalizedPrefix ? path.slice(prefixWithSlash.length) : path;
		if (!rest) continue;
		const segment = rest.split('/')[0];
		if (!segment) continue;
		const childPath = prefixWithSlash ? `${normalizedPrefix}/${segment}` : segment;
		const file = !rest.includes('/');
		const current = groups.get(childPath);
		if (current) {
			current.count += 1;
			current.file = current.file && file;
		} else {
			groups.set(childPath, { path: childPath, count: 1, file });
		}
	}
	return [...groups.values()].sort((left, right) => right.count - left.count || left.path.localeCompare(right.path));
}

function commonDomainPrefix(path: string): string {
	const segments = normalizedPath(path).split('/');
	const first = segments[0] ?? path;
	const second = segments[1];
	return second ? `${first}/${second}` : first;
}

function nodesForFileGroups(groups: readonly { path: string; count: number; file: boolean }[], revision: string, qualifyTopLevel = false): UniverseKnowledgeNode[] {
	return groups.map((group) => {
		const domainId = classifyKnowledgePath(group.path);
		const parts = group.path.split('/');
		const leaf = parts.at(-1) ?? group.path;
		const label = qualifyTopLevel && parts.length > 1 ? `${parts[0]?.toLocaleUpperCase()} · ${leaf}` : leaf;
		const kind = group.file ? kindForPath(group.path, domainId) : 'directory';
		return makeNode(
			group.file ? `hf:${group.path}` : `hfdir:${group.path}`,
			label,
			group.file ? lifecycleForPath(group.path) : `${group.count.toLocaleString()} files`,
			kind,
			domainId,
			6 + Math.log10(Math.max(1, group.count)) * 5,
			true,
			sourceUrl(revision, group.path),
			{ path: group.path, fileCount: group.count, lifecycle: lifecycleForPath(group.path) }
		);
	});
}

function skillNode(node: SkillGraphNode): UniverseKnowledgeNode {
	const domainId = skillDomain(node.category);
	return makeNode(
		`skill:${node.id}`,
		node.title,
		`${node.category} · ${node.inDegree + node.outDegree} relations`,
		domainId === 'capabilities' ? 'capability' : 'skill',
		domainId,
		8 + Math.log10(Math.max(1, node.inDegree + node.outDegree)) * 6,
		true,
		`dartlab://skills/${node.id}`,
		{ skillId: node.id, category: node.category, purpose: node.purpose, cluster: node.cluster }
	);
}

function scoreText(query: string, text: string, exactText: string): number {
	const terms = query.toLocaleLowerCase().split(/\s+/).filter(Boolean);
	const haystack = text.toLocaleLowerCase();
	if (!terms.every((term) => haystack.includes(term))) return 0;
	const exact = exactText.toLocaleLowerCase();
	if (exact === query.toLocaleLowerCase()) return 120;
	if (exact.startsWith(query.toLocaleLowerCase())) return 92;
	return 58 + terms.length * 7 - Math.min(18, haystack.length / 160);
}

function sceneForSearch(query: string, hits: readonly UniverseKnowledgeSearchHit[], indexedItemCount: number, revision: string): UniverseKnowledgeScene {
	const center = makeNode(
		`query:${query}`, query, `${hits.length.toLocaleString()} results`, 'query', null, 28, false,
		`query://${encodeURIComponent(query)}`, { query, indexedItemCount }
	);
	const children = hits.map((hit) => makeNode(
		hit.targetId, hit.label, hit.summary, hit.kind, hit.domainId, 7 + hit.score / 18,
		true,
		hit.sourceRef, { score: hit.score, summary: hit.summary }
	));
	return compileScene({
		sceneId: `knowledge:search:${query}:${revision}`,
		title: `“${query}” 지식 장면`,
		subtitle: `${indexedItemCount.toLocaleString()}개 주소에서 데이터와 Skill OS를 함께 검색했습니다.`,
		targetId: center.nodeId,
		parentTargetId: 'knowledge:root',
		breadcrumbs: [{ targetId: 'knowledge:root', label: 'Universe' }, { targetId: center.nodeId, label: query }],
		center, children, relation: 'describes', indexedItemCount, sourceRevision: revision
	});
}

export function createUniverseKnowledgeRuntime(core: DataCore, loaders: UniverseKnowledgeLoaders): UniverseKnowledgeRuntime {
	const loadMetadata = () => core.request<HfDatasetInfo>({
		origin: 'hfApi',
		path: '?expand[]=sha&expand[]=lastModified&expand[]=mainSize&expand[]=usedStorage',
		cacheKey: 'universe:knowledge:hfMeta',
		parse: parseJson
	});

	const loadRoot = () => core.request<readonly HfTreeEntry[]>({
		origin: 'hfApi',
		path: 'tree/main?recursive=false&expand=false&limit=1000',
		cacheKey: 'universe:knowledge:hfRoot',
		parse: parseJson
	});

	const loadFileIndex = () => core.request<HfDatasetInfo>({
		origin: 'hfApi',
		path: '?expand[]=siblings&expand[]=sha&expand[]=lastModified&expand[]=mainSize&expand[]=usedStorage',
		cacheKey: 'universe:knowledge:hfFileIndex',
		parse: parseJson
	});

	async function overview(): Promise<UniverseKnowledgeOverview> {
		const [info, rootEntries, graph] = await Promise.all([loadMetadata(), loadRoot(), loaders.loadSkillGraph()]);
		const engineSkillCount = graph.nodes.filter((node) => node.category === 'engines').length;
		const domains = DOMAIN_ORDER.map((domainId): UniverseKnowledgeDomain => Object.freeze({
			...DOMAIN_COPY[domainId],
			itemCount: domainId === 'capabilities' ? engineSkillCount : domainId === 'skills' ? graph.nodes.length - engineSkillCount : null
		}));
		return Object.freeze({
			schemaVersion: UNIVERSE_KNOWLEDGE_SCHEMA_VERSION,
			repository: repository(info, null),
			skillCount: graph.nodes.length,
			skillRelationCount: graph.edges.length,
			domains: Object.freeze(domains),
			scene: rootScene(domains, info, rootEntries, graph.edges.length)
		});
	}

	async function coverage(): Promise<UniverseKnowledgeCoverage> {
		const [info, catalog] = await Promise.all([loadFileIndex(), loaders.loadSkillCatalog()]);
		const paths = (info.siblings ?? []).map((entry) => entry.rfilename);
		const domainCounts = emptyDomainCounts();
		for (const path of paths) domainCounts[classifyKnowledgePath(path)] += 1;
		for (const skill of catalog.skills) domainCounts[skillDomain(skill.category)] += 1;
		return Object.freeze({
			repository: repository(info, paths.length),
			hfFileCount: paths.length,
			skillCount: catalog.skills.length,
			addressableItemCount: paths.length + catalog.skills.length,
			domainCounts: Object.freeze(domainCounts)
		});
	}

	async function search(request: UniverseKnowledgeSearchRequest): Promise<UniverseKnowledgeSearchResult> {
		const query = request.query.trim();
		if (query.length < 2) throw new Error('Universe knowledge search requires at least two characters');
		const limit = Math.max(12, Math.min(80, request.limit ?? 48));
		const [info, catalog] = await Promise.all([loadFileIndex(), loaders.loadSkillCatalog()]);
		const fileHits: UniverseKnowledgeSearchHit[] = [];
		for (const sibling of info.siblings ?? []) {
			const domainId = classifyKnowledgePath(sibling.rfilename);
			if (request.domainId && request.domainId !== domainId) continue;
			const label = sibling.rfilename.split('/').at(-1) ?? sibling.rfilename;
			let score = scoreText(query, sibling.rfilename, label);
			if (score <= 0) continue;
			if (lifecycleForPath(sibling.rfilename) !== 'active') score -= 16;
			fileHits.push({
				targetId: `hf:${sibling.rfilename}`,
				label,
				summary: sibling.rfilename,
				kind: kindForPath(sibling.rfilename, domainId),
				domainId,
				sourceRef: sourceUrl(info.sha, sibling.rfilename),
				score
			});
		}
		const skillHits: UniverseKnowledgeSearchHit[] = [];
		for (const skill of catalog.skills) {
			const domainId = skillDomain(skill.category);
			if (request.domainId && request.domainId !== domainId) continue;
			const text = [skill.id, skill.title, skill.purpose, ...(skill.whenToUse ?? []), ...(skill.apiRefs ?? []), ...(skill.datasetRefs ?? [])].join(' ');
			const score = scoreText(query, text, skill.title);
			if (score <= 0) continue;
			skillHits.push({
				targetId: `skill:${skill.id}`,
				label: skill.title,
				summary: skill.purpose,
				kind: domainId === 'capabilities' ? 'capability' : 'skill',
				domainId,
				sourceRef: skill.sourceRefs?.[0] ?? `dartlab://skills/${skill.id}`,
				score: score + 8
			});
		}
		const hits = [...fileHits, ...skillHits]
			.sort((left, right) => right.score - left.score || left.targetId.localeCompare(right.targetId))
			.slice(0, limit);
		const indexedItemCount = (info.siblings?.length ?? 0) + catalog.skills.length;
		return Object.freeze({
			query,
			domainId: request.domainId ?? null,
			hits: Object.freeze(hits),
			indexedItemCount,
			scene: sceneForSearch(query, hits, indexedItemCount, info.sha)
		});
	}

	async function openDomain(domainId: UniverseKnowledgeDomainId): Promise<UniverseKnowledgeScene> {
		const [info, graph] = await Promise.all([loadFileIndex(), loaders.loadSkillGraph()]);
		const paths = (info.siblings ?? []).map((entry) => entry.rfilename).filter((path) => classifyKnowledgePath(path) === domainId);
		const grouped = new Map<string, number>();
		const exactPaths = new Set(paths);
		for (const path of paths) {
			const key = commonDomainPrefix(path);
			grouped.set(key, (grouped.get(key) ?? 0) + 1);
		}
		const fileNodes = nodesForFileGroups([...grouped.entries()].map(([path, count]) => ({ path, count, file: count === 1 && exactPaths.has(path) })), info.sha, true);
		const graphNodes = graph.nodes.filter((node) => skillDomain(node.category) === domainId).map(skillNode);
		const children = [...fileNodes, ...graphNodes].sort((left, right) => right.weight - left.weight || left.nodeId.localeCompare(right.nodeId));
		const copy = DOMAIN_COPY[domainId];
		const center = makeNode(`domain:${domainId}`, copy.label, copy.labelEn, 'domain', domainId, 30, false, copy.sourceRefs[0] ?? '', { description: copy.description });
		return compileScene({
			sceneId: `knowledge:domain:${domainId}:${info.sha}`,
			title: copy.label,
			subtitle: copy.description,
			targetId: center.nodeId,
			parentTargetId: 'knowledge:root',
			breadcrumbs: [{ targetId: 'knowledge:root', label: 'Universe' }, { targetId: center.nodeId, label: copy.label }],
			center, children, indexedItemCount: paths.length + graphNodes.length, sourceRevision: info.sha
		});
	}

	async function openDirectory(path: string): Promise<UniverseKnowledgeScene> {
		const info = await loadFileIndex();
		const paths = (info.siblings ?? []).map((entry) => entry.rfilename);
		const groups = groupFiles(paths, path);
		const domainId = classifyKnowledgePath(path);
		const label = normalizedPath(path).split('/').at(-1) ?? path;
		const parentPath = normalizedPath(path).split('/').slice(0, -1).join('/');
		const center = makeNode(`hfdir:${path}`, label, normalizedPath(path), 'directory', domainId, 28, false, sourceUrl(info.sha, path), { path, lifecycle: lifecycleForPath(path) });
		return compileScene({
			sceneId: `knowledge:directory:${path}:${info.sha}`,
			title: label,
			subtitle: `${groups.reduce((total, group) => total + group.count, 0).toLocaleString()}개 파일을 경로 계층으로 투영했습니다.`,
			targetId: center.nodeId,
			parentTargetId: parentPath ? `hfdir:${parentPath}` : `domain:${domainId}`,
			breadcrumbs: [
				{ targetId: 'knowledge:root', label: 'Universe' },
				{ targetId: `domain:${domainId}`, label: DOMAIN_COPY[domainId].label },
				...normalizedPath(path).split('/').map((segment, index, parts) => ({ targetId: `hfdir:${parts.slice(0, index + 1).join('/')}`, label: segment }))
			],
			center,
			children: nodesForFileGroups(groups, info.sha),
			indexedItemCount: groups.reduce((total, group) => total + group.count, 0),
			sourceRevision: info.sha
		});
	}

	async function openFile(path: string): Promise<UniverseKnowledgeScene> {
		const info = await loadFileIndex();
		const domainId = classifyKnowledgePath(path);
		const parts = normalizedPath(path).split('/');
		const label = parts.at(-1) ?? path;
		const parentPath = parts.slice(0, -1).join('/');
		const center = makeNode(`hf:${path}`, label, normalizedPath(path), kindForPath(path, domainId), domainId, 30, false, sourceUrl(info.sha, path), {
			path, extension: label.includes('.') ? label.split('.').at(-1) ?? '' : '', lifecycle: lifecycleForPath(path), revision: info.sha
		});
		const ancestors = parts.slice(0, -1).map((segment, index) => {
			const ancestorPath = parts.slice(0, index + 1).join('/');
			return makeNode(`hfdir:${ancestorPath}`, segment, ancestorPath, 'directory', classifyKnowledgePath(ancestorPath), 10 + index, true, sourceUrl(info.sha, ancestorPath), { path: ancestorPath });
		}).reverse();
		return compileScene({
			sceneId: `knowledge:file:${path}:${info.sha}`,
			title: label,
			subtitle: '원본 파일의 주소, 수명주기와 상위 데이터 계층을 함께 표시합니다.',
			targetId: center.nodeId,
			parentTargetId: parentPath ? `hfdir:${parentPath}` : `domain:${domainId}`,
			breadcrumbs: [{ targetId: 'knowledge:root', label: 'Universe' }, { targetId: `domain:${domainId}`, label: DOMAIN_COPY[domainId].label }, { targetId: center.nodeId, label }],
			center, children: ancestors, relation: 'available', indexedItemCount: 1, sourceRevision: info.sha
		});
	}

	async function openSkill(skillId: string): Promise<UniverseKnowledgeScene> {
		const [info, graph] = await Promise.all([loadMetadata(), loaders.loadSkillGraph()]);
		const selected = graph.nodes.find((node) => node.id === skillId);
		if (!selected) throw new Error(`Universe skill not found: ${skillId}`);
		const neighborIds = new Set<string>();
		for (const edge of graph.edges) {
			if (edge.src === skillId) neighborIds.add(edge.dst);
			if (edge.dst === skillId) neighborIds.add(edge.src);
		}
		const neighbors = graph.nodes.filter((node) => neighborIds.has(node.id)).map(skillNode)
			.sort((left, right) => right.weight - left.weight || left.nodeId.localeCompare(right.nodeId));
		const center = skillNode(selected);
		return compileScene({
			sceneId: `knowledge:skill:${skillId}:${info.sha}`,
			title: selected.title,
			subtitle: selected.purpose,
			targetId: center.nodeId,
			parentTargetId: `domain:${skillDomain(selected.category)}`,
			breadcrumbs: [
				{ targetId: 'knowledge:root', label: 'Universe' },
				{ targetId: `domain:${skillDomain(selected.category)}`, label: DOMAIN_COPY[skillDomain(selected.category)].label },
				{ targetId: center.nodeId, label: selected.title }
			],
			center, children: neighbors, relation: 'used', indexedItemCount: neighborIds.size + 1, sourceRevision: info.sha
		});
	}

	async function open(targetId: string): Promise<UniverseKnowledgeScene> {
		if (targetId === 'knowledge:root') return (await overview()).scene;
		if (targetId.startsWith('domain:')) return openDomain(targetId.slice('domain:'.length) as UniverseKnowledgeDomainId);
		if (targetId.startsWith('hfdir:')) return openDirectory(targetId.slice('hfdir:'.length));
		if (targetId.startsWith('hf:')) return openFile(targetId.slice('hf:'.length));
		if (targetId.startsWith('skill:')) return openSkill(targetId.slice('skill:'.length));
		throw new Error(`Universe knowledge target is unsupported: ${targetId}`);
	}

	async function content(targetId: string): Promise<UniverseKnowledgeContent> {
		if (!targetId.startsWith('hf:')) throw new Error(`Universe content target is unsupported: ${targetId}`);
		const path = normalizedPath(targetId.slice('hf:'.length));
		if (!path) throw new Error('Universe content path is empty');
		const info = await loadMetadata();
		const kind = contentKind(path);
		const mimeType = contentMime(kind, path);
		const title = path.split('/').at(-1) ?? path;
		const sourceRef = sourceUrl(info.sha, path);
		const rawRef = contentUrl(info.sha, path);
		let text = '';
		let columns: readonly string[] = [];
		let rows: readonly Readonly<Record<string, string>>[] = [];
		let requestedBytes = 0;
		let returnedBytes = 0;
		let truncated = false;
		let mode: UniverseKnowledgeContent['receipt']['mode'] = 'addressOnly';

		if (kind === 'table') {
			const rawRows = await core.requestParquetRows<Record<string, unknown>>({
				path,
				revision: info.sha,
				rowStart: 0,
				rowEnd: CONTENT_ROW_LIMIT,
				cacheKey: `universe:knowledge:content:${info.sha}:${path}:rows:${CONTENT_ROW_LIMIT}`
			});
			columns = Object.freeze([...new Set(rawRows.flatMap((row) => Object.keys(row)))].slice(0, CONTENT_COLUMN_LIMIT));
			rows = Object.freeze(rawRows.slice(0, CONTENT_ROW_LIMIT).map((row) => Object.freeze(Object.fromEntries(columns.map((column) => [column, printableCell(row[column])])))));
			truncated = rawRows.length >= CONTENT_ROW_LIMIT;
			mode = 'parquetRows';
		} else if (kind === 'text' || kind === 'json') {
			requestedBytes = CONTENT_BYTE_LIMIT;
			const buffer = await core.requestBytes({
				origin: 'hfRevisionRange',
				path: `${info.sha}/${path}`,
				start: 0,
				len: CONTENT_BYTE_LIMIT,
				cacheKey: `universe:knowledge:content:${info.sha}:${path}:bytes:${CONTENT_BYTE_LIMIT}`
			});
			returnedBytes = buffer.byteLength;
			truncated = returnedBytes >= CONTENT_BYTE_LIMIT;
			text = new TextDecoder().decode(buffer).replace(/\u0000+$/g, '');
			if (kind === 'json' && !truncated && path.toLocaleLowerCase().endsWith('.json')) {
				try { text = JSON.stringify(JSON.parse(text), null, 2); } catch { /* 원문 미리보기를 유지한다. */ }
			}
			if (text.length > CONTENT_TEXT_DISPLAY_LIMIT) {
				text = text.slice(0, CONTENT_TEXT_DISPLAY_LIMIT);
				truncated = true;
			}
			mode = 'byteRange';
		} else if (kind === 'image' || kind === 'video' || kind === 'audio') {
			mode = 'mediaReference';
		}

		return Object.freeze({
			targetId, path, title, kind, mimeType, revision: info.sha, sourceRef, contentRef: rawRef, text,
			columns, rows,
			receipt: Object.freeze({ mode, requestedBytes, returnedBytes, rowLimit: kind === 'table' ? CONTENT_ROW_LIMIT : 0, truncated })
		});
	}

	return { overview, coverage, search, open, content };
}
