import type {
	EvidencePointer,
	EvidenceReceipt,
	GapReceipt,
	SearchPort,
	UniverseEvidenceCandidate,
	UniverseEvidenceQuery,
	UniverseEvidenceResolution
} from '@dartlab/ui-contracts';
import type { DataCore } from '../fetch/request';
import { createSearchPort } from '../search/filingSearch';
import { canonicalSha256, stripSha256 } from './canonical';

const EVIDENCE_ID = /^evidence:[0-9a-f]{64}$/;
const HASH_ID = /^sha256:[0-9a-f]{64}$/;

async function identity(prefix: string, payload: unknown): Promise<string> {
	return `${prefix}:${stripSha256(await canonicalSha256(payload))}`;
}

async function resolutionGap(query: UniverseEvidenceQuery, reasonCode: string, requestedField: string): Promise<GapReceipt> {
	return {
		gapId: await identity('gap', { claimId: query.claimId, reasonCode, requestedField }),
		kind: 'unresolved',
		ownerSource: 'filingSearch',
		requestedField,
		reasonCode,
		retryPolicy: reasonCode === 'candidateOnly' ? 'supplyExactDocumentLocator' : 'retryAfterIndexRefresh'
	};
}

function exactPointerIssue(pointer: EvidencePointer, query: UniverseEvidenceQuery): string | null {
	if (!EVIDENCE_ID.test(pointer.evidenceId)) return 'invalidEvidenceIdentity';
	if (!pointer.documentId || !pointer.sectionPath || pointer.sectionOrder < 0) return 'missingDocumentSection';
	if (!pointer.sourceRef || !pointer.sourcePath || !pointer.sourceVersion || !pointer.contentHash) return 'missingImmutableSource';
	if (!HASH_ID.test(pointer.contentHash)) return 'invalidContentHash';
	if (!pointer.sourcePublishedAt || !pointer.availableAt) return 'missingEvidenceTime';
	if (query.knownAt && pointer.availableAt > query.knownAt) return 'knowledgeLookAhead';
	if (pointer.subjectId !== query.subjectId || pointer.predicate !== query.predicate
		|| pointer.objectId !== query.objectId || pointer.direction !== query.direction) return 'semanticBindingMismatch';
	if (pointer.locatorKind === 'text') {
		if (!pointer.textLocator || pointer.tableLocator) return 'invalidTextLocator';
		if (pointer.textLocator.charStart < 0 || pointer.textLocator.charEnd <= pointer.textLocator.charStart
			|| !HASH_ID.test(pointer.textLocator.snippetHash)) return 'invalidTextLocator';
	} else if (pointer.locatorKind === 'table') {
		if (!pointer.tableLocator || pointer.textLocator) return 'invalidTableLocator';
		if (pointer.tableLocator.rowIndex < 0 || !HASH_ID.test(pointer.tableLocator.headerHash)
			|| !HASH_ID.test(pointer.tableLocator.rowHash)) return 'invalidTableLocator';
	} else return 'invalidLocatorKind';
	return null;
}

async function receipt(
	query: UniverseEvidenceQuery,
	pointer: EvidencePointer | null,
	status: EvidenceReceipt['status'],
	generatedAt: string
): Promise<EvidenceReceipt> {
	const evidenceRefs = pointer ? [pointer.evidenceId] : [];
	return {
		receiptId: await identity('receipt', { claimId: query.claimId, evidenceRefs, status, validAt: query.validAt, knownAt: query.knownAt }),
		claimId: query.claimId,
		evidenceRefs,
		derivationRefs: [],
		falsifierRefs: [],
		sourceSnapshotIds: [],
		status,
		validAt: query.validAt,
		knownAt: query.knownAt,
		generatedAt
	};
}

function candidatesFromHits(hits: Awaited<ReturnType<SearchPort['queryFilings']>>): UniverseEvidenceCandidate[] {
	return hits.map((hit) => ({
		documentId: hit.rceptNo,
		title: hit.reportNm,
		entityId: hit.stockCode,
		publishedAt: hit.rceptDt,
		sourceRef: hit.sourceRef,
		snippet: hit.snippet,
		score: hit.score
	}));
}

export async function resolveUniverseEvidence(
	query: UniverseEvidenceQuery,
	search: Pick<SearchPort, 'queryFilings' | 'indexBuiltAt'>
): Promise<UniverseEvidenceResolution> {
	const pointer = query.pointer ?? null;
	if (pointer) {
		const issue = exactPointerIssue(pointer, query);
		if (!issue) {
			const generatedAt = query.knownAt ?? pointer.availableAt;
			return {
				query,
				pointer,
				receipt: await receipt(query, pointer, 'supported', generatedAt),
				candidates: [],
				gaps: [],
				indexBuiltAt: null
			};
		}
		const generatedAt = query.knownAt ?? query.validAt ?? 'unknown';
		return {
			query,
			pointer: null,
			receipt: await receipt(query, null, 'missing', generatedAt),
			candidates: [],
			gaps: [await resolutionGap(query, issue, 'exact evidence pointer')],
			indexBuiltAt: null
		};
	}

	let indexBuiltAt: string | null = null;
	let candidates: UniverseEvidenceCandidate[] = [];
	const gaps: GapReceipt[] = [];
	try {
		const [hits, builtAt] = await Promise.all([
			search.queryFilings({ text: query.text, limit: 8 }),
			search.indexBuiltAt()
		]);
		indexBuiltAt = builtAt;
		candidates = candidatesFromHits(hits);
		gaps.push(await resolutionGap(query, candidates.length ? 'candidateOnly' : 'noSearchHit', 'exact text or table locator'));
	} catch {
		gaps.push(await resolutionGap(query, 'searchUnavailable', 'filing search candidates'));
	}
	const generatedAt = query.knownAt ?? indexBuiltAt ?? query.validAt ?? 'unknown';
	return {
		query,
		pointer: null,
		receipt: await receipt(query, null, 'missing', generatedAt),
		candidates,
		gaps,
		indexBuiltAt
	};
}

export function createUniverseEvidenceResolver(core: DataCore): (query: UniverseEvidenceQuery) => Promise<UniverseEvidenceResolution> {
	const search = createSearchPort(core);
	return (query) => resolveUniverseEvidence(query, search);
}
