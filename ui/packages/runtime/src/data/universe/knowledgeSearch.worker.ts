import type { UniverseKnowledgeSearchHit, UniverseKnowledgeSearchRequest } from '@dartlab/ui-contracts';
import type { KnowledgeSearchIndex, PreparedKnowledgeSearchIndex } from './knowledgeSearch';
import { prepareKnowledgeSearchIndex, searchPreparedKnowledgeIndex } from './knowledgeSearch';

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

interface KnowledgeWorkerScope {
	onmessage: ((event: MessageEvent<WorkerRequest>) => void) | null;
	postMessage(message: WorkerResponse): void;
}

const scope = globalThis as unknown as KnowledgeWorkerScope;
let activeIndex: PreparedKnowledgeSearchIndex | null = null;

scope.onmessage = (event) => {
	const startedAt = performance.now();
	try {
		const indexPrepared = Boolean(event.data.index);
		if (event.data.index) activeIndex = prepareKnowledgeSearchIndex(event.data.index);
		if (!activeIndex) throw new Error('Universe search worker index is missing');
		const hits = searchPreparedKnowledgeIndex(activeIndex, event.data.request);
		scope.postMessage({ requestId: event.data.requestId, hits, elapsedMs: performance.now() - startedAt, indexPrepared });
	} catch (error) {
		scope.postMessage({
			requestId: event.data.requestId,
			error: error instanceof Error ? error.message : 'Universe search worker failed'
		});
	}
};
