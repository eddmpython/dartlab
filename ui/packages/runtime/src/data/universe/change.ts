import type {
	EvidenceReceipt,
	GapReceipt,
	SourceSnapshotSet,
	UniverseAssertion,
	UniverseAtlas,
	UniverseChangeAggregate,
	UniverseChangeKind,
	UniverseChangeMark,
	UniverseChangeSet
} from '@dartlab/ui-contracts';
import type { DataCore } from '../fetch/request';
import { canonicalSha256, stripSha256 } from './canonical';

const CHANGE_LIMIT = 200;
const CHANGE_CACHE = { scope: 'memory', ttlMs: 6 * 60 * 60 * 1_000, maxEntries: 8 } as const;

interface TimelinePayload {
	periods: string[];
	data: Record<string, Record<string, { revenue?: number | null; opMargin?: number | null }>>;
	industryTotals: Record<string, Record<string, { totalRevenue?: number; count?: number; avgOpm?: number }>>;
}

interface MoverEntry {
	stockCode?: string;
	corpName?: string;
	industry?: string;
	revenue?: number | null;
	asOfYear?: number | string;
	signal?: string;
}

interface MoversPayload {
	asOf: string;
	categories: Record<string, { title?: string; entries?: MoverEntry[] }>;
	disclaimer?: string;
}

function finite(value: unknown): number | null {
	return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function displayText(value: unknown, fallback: string): string {
	const text = String(value ?? '').trim() || fallback;
	return text.replace(/[\u2013\u2014]/g, ':');
}

async function identity(prefix: string, payload: unknown): Promise<string> {
	return `${prefix}:${stripSha256(await canonicalSha256(payload))}`;
}

async function gap(ownerSource: string, requestedField: string, reasonCode: string): Promise<GapReceipt> {
	return {
		gapId: await identity('gap', { ownerSource, requestedField, reasonCode }),
		kind: reasonCode === 'boundedOmission' ? 'omitted' : 'unresolved',
		ownerSource,
		requestedField,
		reasonCode,
		retryPolicy: reasonCode === 'historicalSnapshotUnavailable' ? 'retryWhenImmutableSnapshotExists' : 'retryAfterSourceRefresh'
	};
}

async function missingReceipt(claimId: string, snapshotSetId: string, validAt: string | null, knownAt: string | null): Promise<EvidenceReceipt> {
	return {
		receiptId: await identity('receipt', { claimId, snapshotSetId, validAt, knownAt, status: 'missing' }),
		claimId,
		evidenceRefs: [],
		derivationRefs: [],
		falsifierRefs: [],
		sourceSnapshotIds: [snapshotSetId],
		status: 'missing',
		validAt,
		knownAt,
		generatedAt: knownAt ?? validAt ?? 'unknown'
	};
}

async function exactReceipt(assertion: UniverseAssertion | null, snapshotSetId: string, claimId: string, generatedAt: string): Promise<EvidenceReceipt> {
	const evidenceRefs = assertion?.evidenceRefs.map((pointer) => pointer.evidenceId) ?? [];
	return {
		receiptId: await identity('receipt', { claimId, snapshotSetId, evidenceRefs, status: evidenceRefs.length ? 'supported' : 'missing' }),
		claimId,
		evidenceRefs,
		derivationRefs: [],
		falsifierRefs: [],
		sourceSnapshotIds: [snapshotSetId],
		status: evidenceRefs.length ? 'supported' : 'missing',
		validAt: assertion?.validFrom ?? null,
		knownAt: assertion?.availableAt ?? null,
		generatedAt
	};
}

async function requestJson<T>(core: DataCore, path: string): Promise<T | null> {
	try {
		return await core.request<T>({
			origin: 'hf',
			path,
			cache: CHANGE_CACHE,
			cacheKey: `universe-change:${path}`,
			parse: async (response) => {
				if (!response.ok) throw new Error(`Universe change source load failed: ${path}`);
				return await response.json() as T;
			}
		});
	} catch {
		return null;
	}
}

function aggregateCoverage(
	atlas: UniverseAtlas,
	timeline: TimelinePayload | null,
	period: string | null,
	marks: readonly UniverseChangeMark[],
	omittedByIndustry: ReadonlyMap<string, number>
): UniverseChangeAggregate[] {
	const coveredByIndustry = period && timeline ? timeline.industryTotals[period] ?? {} : {};
	const changes = new Map<string, number>();
	for (const mark of marks) changes.set(mark.industryId, (changes.get(mark.industryId) ?? 0) + 1);
	return atlas.industries.map((industry) => {
		const coveredCount = Math.min(industry.nodeCount, Math.max(0, Number(coveredByIndustry[industry.id]?.count ?? 0)));
		return {
			industryId: industry.id,
			industryLabel: industry.name,
			memberCount: industry.nodeCount,
			coveredCount,
			unknownCount: Math.max(0, industry.nodeCount - coveredCount),
			omittedCount: omittedByIndustry.get(industry.id) ?? 0,
			coverage: industry.nodeCount > 0 ? coveredCount / industry.nodeCount : 0,
			changeCount: changes.get(industry.id) ?? 0
		};
	}).sort((left, right) => right.changeCount - left.changeCount || left.industryId.localeCompare(right.industryId));
}

export async function loadCurrentChangeUniverse(
	core: DataCore,
	atlas: UniverseAtlas,
	snapshot: SourceSnapshotSet,
	maxMarks = CHANGE_LIMIT
): Promise<UniverseChangeSet> {
	const safeLimit = Math.max(1, Math.min(CHANGE_LIMIT, Math.trunc(maxMarks)));
	const [timeline, movers] = await Promise.all([
		requestJson<TimelinePayload>(core, 'landing/map/timeline.json'),
		requestJson<MoversPayload>(core, 'landing/map/movers.json')
	]);
	const gaps: GapReceipt[] = [];
	if (!timeline) gaps.push(await gap('mapTimeline', 'historical observations', 'sourceUnavailable'));
	if (!movers) gaps.push(await gap('mapMovers', 'current mover signals', 'sourceUnavailable'));
	gaps.push(await gap('sourceSnapshotSet', 'exact before and after assertion history', 'historicalSnapshotUnavailable'));

	const periods = [...(timeline?.periods ?? [])].sort();
	const fromPeriod = periods.at(-1) ?? null;
	const toPeriod = movers?.asOf ?? snapshot.createdAt;
	const entries = Object.entries(movers?.categories ?? {}).flatMap(([category, value]) =>
		(value.entries ?? []).map((entry) => ({ category, entry }))
	).sort((left, right) => String(left.entry.stockCode ?? '').localeCompare(String(right.entry.stockCode ?? ''))
		|| left.category.localeCompare(right.category));
	const unique = new Map<string, { category: string; entry: MoverEntry }>();
	for (const row of entries) {
		const stockCode = String(row.entry.stockCode ?? '');
		if (stockCode && !unique.has(stockCode)) unique.set(stockCode, row);
	}
	const selected = [...unique.values()].slice(0, safeLimit);
	const omittedByIndustry = new Map<string, number>();
	for (const row of [...unique.values()].slice(safeLimit)) {
		const industryId = String(row.entry.industry ?? 'unknown');
		omittedByIndustry.set(industryId, (omittedByIndustry.get(industryId) ?? 0) + 1);
	}
	if (unique.size > safeLimit) gaps.push(await gap('mapMovers', 'change marks beyond scene budget', 'boundedOmission'));

	const marks: UniverseChangeMark[] = [];
	for (const { category, entry } of selected) {
		const entityId = String(entry.stockCode ?? '');
		const industryId = String(entry.industry ?? 'unknown');
		const claimId = await identity('claim', { mode: 'currentSignals', category, entityId, toPeriod });
		const before = await missingReceipt(`${claimId}:before`, snapshot.snapshotSetId, fromPeriod, toPeriod);
		const after = await missingReceipt(`${claimId}:after`, snapshot.snapshotSetId, toPeriod, toPeriod);
		const evidenceGap = await gap('filingEvidence', `${entityId} before and after exact locator`, 'currentSignalHasNoAssertionHistory');
		const beforeValue = fromPeriod ? finite(timeline?.data[fromPeriod]?.[entityId]?.revenue) : null;
		const afterValue = finite(entry.revenue);
		marks.push({
			changeId: await identity('change', { mode: 'currentSignals', category, entityId, fromPeriod, toPeriod, beforeValue, afterValue }),
			entityId,
			entityLabel: displayText(entry.corpName, entityId),
			industryId,
			kind: 'newlyKnown',
			metricId: category,
			beforeValue,
			afterValue,
			unit: beforeValue === null && afterValue === null ? null : 'KRW',
			eventAt: toPeriod,
			knownAt: toPeriod,
			sourceRef: `map:movers#category=${category}&stockCode=${entityId}`,
			summary: displayText(entry.signal, '현재 변화 신호'),
			evidence: { before, after, gaps: [evidenceGap] }
		});
	}
	const aggregates = aggregateCoverage(atlas, timeline, fromPeriod, marks, omittedByIndustry);
	const diffPayload = { mode: 'currentSignals', snapshotSetId: snapshot.snapshotSetId, fromPeriod, toPeriod, marks, aggregates, gaps };
	return {
		mode: 'currentSignals',
		fromSnapshotSetId: null,
		toSnapshotSetId: snapshot.snapshotSetId,
		fromPeriod,
		toPeriod,
		marks,
		aggregates,
		gaps,
		diffHash: await canonicalSha256(diffPayload),
		generatedAt: toPeriod
	};
}

function relationKey(assertion: UniverseAssertion): string {
	return `${assertion.subjectId}\u0000${assertion.predicate}\u0000${assertion.objectId}\u0000${assertion.direction}`;
}

function exactKind(before: UniverseAssertion | null, after: UniverseAssertion | null, beforeKnownAt: string): UniverseChangeKind {
	if (before && !after) return 'stale';
	if (!before && after) return after.validFrom && after.validFrom <= beforeKnownAt ? 'newlyKnown' : 'created';
	if (after?.status === 'retracted' && before?.status !== 'retracted') return 'retracted';
	return 'corrected';
}

export interface ExactChangeInput {
	beforeSnapshot: SourceSnapshotSet;
	afterSnapshot: SourceSnapshotSet;
	beforeAssertions: readonly UniverseAssertion[];
	afterAssertions: readonly UniverseAssertion[];
	beforeKnownAt: string;
	afterKnownAt: string;
}

export async function compileExactChangeUniverse(input: ExactChangeInput): Promise<UniverseChangeSet> {
	if (!input.beforeSnapshot.exactReplayReady || !input.afterSnapshot.exactReplayReady) {
		throw new Error('Exact Universe change mode requires two replayable snapshot sets');
	}
	const visibleBefore = input.beforeAssertions.filter((assertion) => assertion.availableAt <= input.beforeKnownAt);
	const visibleAfter = input.afterAssertions.filter((assertion) => assertion.availableAt <= input.afterKnownAt);
	const beforeMap = new Map(visibleBefore.map((assertion) => [relationKey(assertion), assertion]));
	const afterMap = new Map(visibleAfter.map((assertion) => [relationKey(assertion), assertion]));
	const keys = [...new Set([...beforeMap.keys(), ...afterMap.keys()])].sort();
	const marks: UniverseChangeMark[] = [];
	for (const key of keys) {
		const before = beforeMap.get(key) ?? null;
		const after = afterMap.get(key) ?? null;
		if (before && after && before.evidenceBindingHash === after.evidenceBindingHash && before.status === after.status) continue;
		const anchor = after ?? before;
		if (!anchor) continue;
		const kind = exactKind(before, after, input.beforeKnownAt);
		const claimId = await identity('claim', { mode: 'exactReplay', key, kind, before: before?.assertionId, after: after?.assertionId });
		const evidenceGaps: GapReceipt[] = [];
		if (!before?.evidenceRefs.length) evidenceGaps.push(await gap('beforeSnapshot', `${key} exact locator`, 'beforeEvidenceMissing'));
		if (!after?.evidenceRefs.length) evidenceGaps.push(await gap('afterSnapshot', `${key} exact locator`, 'afterEvidenceMissing'));
		marks.push({
			changeId: await identity('change', { key, kind, before: before?.assertionId, after: after?.assertionId }),
			entityId: anchor.subjectId,
			entityLabel: anchor.subjectId,
			industryId: 'unknown',
			kind,
			metricId: anchor.predicate,
			beforeValue: null,
			afterValue: null,
			unit: null,
			eventAt: after?.eventAt ?? before?.eventAt ?? input.afterKnownAt,
			knownAt: after?.availableAt ?? input.afterKnownAt,
			sourceRef: after?.evidenceRefs[0]?.sourceRef ?? before?.evidenceRefs[0]?.sourceRef ?? 'unresolved',
			summary: `${anchor.subjectId} ${anchor.predicate} ${anchor.objectId}`,
			evidence: {
				before: await exactReceipt(before, input.beforeSnapshot.snapshotSetId, `${claimId}:before`, input.afterKnownAt),
				after: await exactReceipt(after, input.afterSnapshot.snapshotSetId, `${claimId}:after`, input.afterKnownAt),
				gaps: evidenceGaps
			}
		});
	}
	const diffPayload = {
		mode: 'exactReplay', beforeSnapshotSetId: input.beforeSnapshot.snapshotSetId,
		afterSnapshotSetId: input.afterSnapshot.snapshotSetId, beforeKnownAt: input.beforeKnownAt,
		afterKnownAt: input.afterKnownAt, marks
	};
	return {
		mode: 'exactReplay',
		fromSnapshotSetId: input.beforeSnapshot.snapshotSetId,
		toSnapshotSetId: input.afterSnapshot.snapshotSetId,
		fromPeriod: input.beforeKnownAt,
		toPeriod: input.afterKnownAt,
		marks,
		aggregates: [],
		gaps: marks.flatMap((mark) => mark.evidence.gaps),
		diffHash: await canonicalSha256(diffPayload),
		generatedAt: input.afterKnownAt
	};
}
