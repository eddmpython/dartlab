import type {
	UniverseKnowledgeDomainId,
	UniverseKnowledgeNodeKind,
	UniverseKnowledgeSearchHit,
	UniverseKnowledgeSearchRequest
} from '@dartlab/ui-contracts';
import {
	classifyKnowledgePath,
	knowledgeLifecycleForPath,
	knowledgeNodeKindForPath,
	knowledgeSkillDomain,
	knowledgeSourceUrl
} from './knowledgeCatalog';

export interface KnowledgeSearchSkill {
	id: string;
	title: string;
	category: string;
	purpose: string;
	whenToUse?: readonly string[];
	apiRefs?: readonly string[];
	datasetRefs?: readonly string[];
	sourceRefs?: readonly string[];
}

export interface KnowledgeSearchIndex {
	revision: string;
	filePaths: readonly string[];
	skills: readonly KnowledgeSearchSkill[];
}

interface PreparedKnowledgeFile {
	path: string;
	label: string;
	domainId: UniverseKnowledgeDomainId;
	kind: UniverseKnowledgeNodeKind;
	searchText: string;
	pathExact: string;
	labelExact: string;
	active: boolean;
}

interface PreparedKnowledgeSkill {
	id: string;
	title: string;
	purpose: string;
	domainId: UniverseKnowledgeDomainId;
	kind: 'capability' | 'skill';
	searchText: string;
	titleExact: string;
	sourceRef: string;
}

export interface PreparedKnowledgeSearchIndex {
	revision: string;
	files: readonly PreparedKnowledgeFile[];
	skills: readonly PreparedKnowledgeSkill[];
}

export interface KnowledgeSearchExecution {
	hits: readonly UniverseKnowledgeSearchHit[];
	execution: 'worker' | 'mainThreadFallback';
	indexState: 'coldStart' | 'primed' | 'fallback';
	elapsedMs: number;
	workerElapsedMs: number | null;
	budgetMs: number;
	withinBudget: boolean;
}

export const KNOWLEDGE_SEARCH_BUDGET_MS = Object.freeze({ coldStart: 250, primed: 50, fallback: 120 });

export interface KnowledgeSearchExecutor {
	search(index: KnowledgeSearchIndex, request: UniverseKnowledgeSearchRequest): Promise<KnowledgeSearchExecution>;
	prime(index: KnowledgeSearchIndex): Promise<void>;
}

interface WorkerRequest {
	requestId: number;
	request: UniverseKnowledgeSearchRequest;
	index?: KnowledgeSearchIndex;
}

interface WorkerResponse {
	requestId: number;
	hits?: readonly UniverseKnowledgeSearchHit[];
	elapsedMs?: number;
	indexPrepared?: boolean;
	error?: string;
}

interface PendingSearch {
	resolve: (response: WorkerResponse) => void;
	reject: (error: Error) => void;
}

function scorePrepared(query: string, terms: readonly string[], searchText: string, exactValue: string, alternateExactValue = ''): number {
	if (!terms.every((term) => searchText.includes(term))) return 0;
	if (exactValue === query || alternateExactValue === query) return 120;
	if (exactValue.startsWith(query) || alternateExactValue.startsWith(query)) return 92;
	return 58 + terms.length * 7 - Math.min(18, searchText.length / 160);
}

export function prepareKnowledgeSearchIndex(index: KnowledgeSearchIndex): PreparedKnowledgeSearchIndex {
	const files = index.filePaths.map((path): PreparedKnowledgeFile => {
		const domainId = classifyKnowledgePath(path);
		const label = path.split('/').at(-1) ?? path;
		return Object.freeze({
			path,
			label,
			domainId,
			kind: knowledgeNodeKindForPath(path, domainId),
			searchText: path.toLocaleLowerCase(),
			pathExact: path.toLocaleLowerCase(),
			labelExact: label.toLocaleLowerCase(),
			active: knowledgeLifecycleForPath(path) === 'active'
		});
	});
	const skills = index.skills.map((skill): PreparedKnowledgeSkill => {
		const domainId = knowledgeSkillDomain(skill.category);
		return Object.freeze({
			id: skill.id,
			title: skill.title,
			purpose: skill.purpose,
			domainId,
			kind: domainId === 'capabilities' ? 'capability' : 'skill',
			searchText: [skill.id, skill.title, skill.purpose, ...(skill.whenToUse ?? []), ...(skill.apiRefs ?? []), ...(skill.datasetRefs ?? [])].join(' ').toLocaleLowerCase(),
			titleExact: skill.title.toLocaleLowerCase(),
			sourceRef: skill.sourceRefs?.[0] ?? `dartlab://skills/${skill.id}`
		});
	});
	return Object.freeze({ revision: index.revision, files: Object.freeze(files), skills: Object.freeze(skills) });
}

export function searchPreparedKnowledgeIndex(index: PreparedKnowledgeSearchIndex, request: UniverseKnowledgeSearchRequest): readonly UniverseKnowledgeSearchHit[] {
	const query = request.query.trim();
	const queryLower = query.toLocaleLowerCase();
	const terms = queryLower.split(/\s+/).filter(Boolean);
	const limit = Math.max(12, Math.min(80, request.limit ?? 48));
	const fileHits: UniverseKnowledgeSearchHit[] = [];
	for (const file of index.files) {
		if (request.domainId && request.domainId !== file.domainId) continue;
		let score = scorePrepared(queryLower, terms, file.searchText, file.pathExact, file.labelExact);
		if (score <= 0) continue;
		if (!file.active) score -= 16;
		fileHits.push({
			targetId: `hf:${file.path}`,
			label: file.label,
			summary: file.path,
			kind: file.kind,
			domainId: file.domainId,
			sourceRef: knowledgeSourceUrl(index.revision, file.path),
			score
		});
	}
	const skillHits: UniverseKnowledgeSearchHit[] = [];
	for (const skill of index.skills) {
		if (request.domainId && request.domainId !== skill.domainId) continue;
		const score = scorePrepared(queryLower, terms, skill.searchText, skill.titleExact);
		if (score <= 0) continue;
		skillHits.push({
			targetId: `skill:${skill.id}`,
			label: skill.title,
			summary: skill.purpose,
			kind: skill.kind,
			domainId: skill.domainId,
			sourceRef: skill.sourceRef,
			score: score + 8
		});
	}
	return Object.freeze([...fileHits, ...skillHits]
		.sort((left, right) => right.score - left.score || left.targetId.localeCompare(right.targetId))
		.slice(0, limit));
}

export function searchKnowledgeIndex(index: KnowledgeSearchIndex, request: UniverseKnowledgeSearchRequest): readonly UniverseKnowledgeSearchHit[] {
	return searchPreparedKnowledgeIndex(prepareKnowledgeSearchIndex(index), request);
}

export function createKnowledgeSearchExecutor(): KnowledgeSearchExecutor {
	let worker: Worker | null = null;
	let workerSignature = '';
	let workerUnavailable = typeof Worker === 'undefined';
	let requestId = 0;
	const pending = new Map<number, PendingSearch>();

	function rejectPending(error: Error): void {
		for (const entry of pending.values()) entry.reject(error);
		pending.clear();
	}

	function resetWorker(error?: Error): void {
		if (error) rejectPending(error);
		worker?.terminate();
		worker = null;
		workerSignature = '';
		workerUnavailable = true;
	}

	function ensureWorker(): Worker | null {
		if (workerUnavailable) return null;
		if (worker) return worker;
		try {
			worker = new Worker(new URL('./knowledgeSearch.worker.ts', import.meta.url), { type: 'module', name: 'dartlab-universe-search' });
			worker.onmessage = (event: MessageEvent<WorkerResponse>) => {
				const entry = pending.get(event.data.requestId);
				if (!entry) return;
				pending.delete(event.data.requestId);
				if (event.data.error) entry.reject(new Error(event.data.error));
				else entry.resolve(event.data);
			};
			worker.onerror = (event) => resetWorker(new Error(event.message || 'Universe search worker failed'));
			return worker;
		} catch {
			resetWorker();
			return null;
		}
	}

	async function searchWithWorker(index: KnowledgeSearchIndex, request: UniverseKnowledgeSearchRequest): Promise<WorkerResponse> {
		const activeWorker = ensureWorker();
		if (!activeWorker) throw new Error('Universe search worker unavailable');
		const nextRequestId = ++requestId;
		const signature = `${index.revision}:${index.filePaths.length}:${index.skills.length}`;
		const payload: WorkerRequest = {
			requestId: nextRequestId,
			request,
			...(workerSignature === signature ? {} : { index })
		};
		workerSignature = signature;
		return new Promise<WorkerResponse>((resolve, reject) => {
			pending.set(nextRequestId, { resolve, reject });
			activeWorker.postMessage(payload);
		});
	}

	async function search(index: KnowledgeSearchIndex, request: UniverseKnowledgeSearchRequest): Promise<KnowledgeSearchExecution> {
		const startedAt = performance.now();
		if (!workerUnavailable) {
			try {
				const response = await searchWithWorker(index, request);
				const elapsedMs = performance.now() - startedAt;
				const indexState = response.indexPrepared ? 'coldStart' as const : 'primed' as const;
				const budgetMs = KNOWLEDGE_SEARCH_BUDGET_MS[indexState];
				return Object.freeze({
					hits: Object.freeze([...(response.hits ?? [])]),
					execution: 'worker' as const,
					indexState,
					elapsedMs,
					workerElapsedMs: response.elapsedMs ?? null,
					budgetMs,
					withinBudget: elapsedMs <= budgetMs
				});
			} catch {
				resetWorker();
			}
		}
		const hits = searchKnowledgeIndex(index, request);
		const elapsedMs = performance.now() - startedAt;
		const budgetMs = KNOWLEDGE_SEARCH_BUDGET_MS.fallback;
		return Object.freeze({
			hits,
			execution: 'mainThreadFallback' as const,
			indexState: 'fallback' as const,
			elapsedMs,
			workerElapsedMs: null,
			budgetMs,
			withinBudget: elapsedMs <= budgetMs
		});
	}

	async function prime(index: KnowledgeSearchIndex): Promise<void> {
		if (workerUnavailable) return;
		try {
			await searchWithWorker(index, { query: '__universe_index_prime__', limit: 12 });
		} catch {
			resetWorker();
		}
	}

	return Object.freeze({ search, prime });
}
