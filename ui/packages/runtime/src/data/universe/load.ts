import type {
	SnapshotSource,
	SourceSnapshotSet,
	UniverseAtlas,
	UniverseObservationPoint,
	UniverseObservationRange,
	UniverseReleaseState,
	UniverseRouteMeta,
	UniverseRouteSeed
} from '@dartlab/ui-contracts';
import type { DataCore } from '../fetch/request';
import { canonicalSha256 } from './canonical';
import { adaptAtlas, compileProjection } from './projection';
import { compileUniverseProductReceipt } from './release';

const HOUR = 60 * 60 * 1_000;
const JSON_CACHE = { scope: 'memory', ttlMs: 6 * HOUR, maxEntries: 64 } as const;
const SOURCE_SPECS = [
	['mapMeta', 'landing/map/meta.json', 'buildTime'],
	['mapAtlas', 'landing/map/atlas.json', 'buildTime'],
	['mapEcosystem', 'landing/map/ecosystem.json', 'buildTime'],
	['searchIndex', 'landing/map/search-index.json', 'buildTime'],
	['mapTimeline', 'landing/map/timeline.json', 'buildTime'],
	['mapMovers', 'landing/map/movers.json', 'buildTime'],
	['dartPanelSample', 'dart/panel/005930.parquet', 'dart'],
	['dartFinanceSample', 'dart/finance/005930.parquet', 'finance'],
	['capabilityCatalog', 'dartlab.reference.capability.loadCapabilities', 'catalog'],
	['recipeCatalog', 'src/dartlab/skills/catalog.json', 'catalog']
] as const;
const INDUSTRY_ID = /^[A-Za-z][A-Za-z0-9]*$/;
const STOCK_CODE = /^[0-9A-Z]{6}$/;
const METRIC_FIELDS: Readonly<Record<string, string>> = {
	sales: 'sales',
	operatingProfit: 'operating_profit',
	netProfit: 'net_profit',
	totalAssets: 'total_assets'
};

interface LoadedArtifact<T> {
	value: T;
	path: string;
	versionOrEtag: string | null;
	payloadHash: string;
	contentLength: number | null;
}

function disabledUniverseRouteSeed(): UniverseRouteSeed {
	const input = {
		meta: {
			schemaVersion: 1,
			buildId: 'disabled',
			buildTime: '1970-01-01T00:00:00.000Z',
			commitSha: '',
			dataAsOf: {},
			sizes: {},
			counts: {}
		},
		atlas: { version: 'disabled', industries: [], flows: [] },
		snapshot: {
			schemaVersion: 'sourceSnapshotSet.v1',
			snapshotSetId: 'disabled',
			createdAt: '1970-01-01T00:00:00.000Z',
			sources: [],
			mapBuildId: null,
			capabilityCatalogVersion: null,
			recipeCatalogVersion: null,
			exactReplayReady: false,
			unreplayableSourceIds: [],
			missingDataAsOfSourceIds: [],
			missingRedistributionReceiptSourceIds: []
		},
		scene: {
			schemaVersion: 'boundedScene.v1' as const,
			sceneId: 'disabled',
			nodes: [],
			edges: [],
			assertions: [],
			receipt: {
				specHash: 'disabled',
				sourceSnapshotSetId: 'disabled',
				inputNodeCount: 0,
				inputEdgeCount: 0,
				outputNodeCount: 0,
				outputEdgeCount: 0,
				seedCount: 0,
				retainedSeedCount: 0,
				maxDepthObserved: 0,
				omission: { omittedNodeCount: 0, omittedEdgeCount: 0, nodeReasonCounts: [], edgeReasonCounts: [], omittedNodeLaneCounts: [], omittedEdgeLaneCounts: [] }
			},
			sceneHash: 'disabled'
		},
		releaseState: 'disabled' as const
	};
	return { ...input, product: compileUniverseProductReceipt(input) };
}

function asRecord(value: unknown): Record<string, unknown> {
	if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Universe JSON root must be an object');
	return value as Record<string, unknown>;
}

function headerValue(response: Response, name: string): string | null {
	const value = response.headers.get(name)?.trim().replace(/^"|"$/g, '');
	return value || null;
}

async function requestArtifact<T>(core: DataCore, path: string, validate: (value: unknown) => T): Promise<LoadedArtifact<T>> {
	return core.request({
		origin: 'hf',
		path,
		cache: JSON_CACHE,
		cacheKey: `universe:${path}`,
		parse: async (response) => {
			if (!response.ok) throw new Error(`Universe source load failed: ${path} (${response.status})`);
			const value = validate(await response.json());
			const repoCommit = headerValue(response, 'x-repo-commit');
			const etag = headerValue(response, 'etag');
			const versionParts = [repoCommit ? `hfCommit:${repoCommit}` : '', etag ? `etag:${etag}` : ''].filter(Boolean);
			const length = Number(response.headers.get('content-length'));
			return {
				value,
				path,
				versionOrEtag: versionParts.length > 0 ? versionParts.join(';') : null,
				payloadHash: await canonicalSha256(value),
				contentLength: Number.isFinite(length) && length >= 0 ? length : null
			};
		}
	});
}

function validateMeta(value: unknown): UniverseRouteMeta {
	const row = asRecord(value);
	if (row.schemaVersion !== 1 || typeof row.buildId !== 'string' || typeof row.buildTime !== 'string'
		|| typeof row.commitSha !== 'string') throw new Error('Universe map meta schema is unsupported');
	return row as unknown as UniverseRouteMeta;
}

function validateAtlas(value: unknown): UniverseAtlas {
	const row = asRecord(value);
	if (typeof row.version !== 'string' || !Array.isArray(row.industries) || !Array.isArray(row.flows)) {
		throw new Error('Universe atlas schema is unsupported');
	}
	for (const industry of row.industries) {
		const item = asRecord(industry);
		if (typeof item.id !== 'string' || typeof item.name !== 'string' || !Array.isArray(item.stages)) {
			throw new Error('Universe atlas industry is invalid');
		}
	}
	return row as unknown as UniverseAtlas;
}

function sourceDataAsOf(meta: UniverseRouteMeta, key: string): string | null {
	if (key === 'buildTime') return meta.buildTime || null;
	if (key === 'catalog') return null;
	return meta.dataAsOf[key] ?? null;
}

function unavailableSource(meta: UniverseRouteMeta, sourceId: string, path: string, dataKey: string): SnapshotSource {
	return {
		sourceId,
		origin: sourceId.endsWith('Catalog') ? 'runtimeCatalog' : 'hfDataset',
		path,
		versionOrEtag: null,
		payloadHash: null,
		dataAsOf: sourceDataAsOf(meta, dataKey),
		redistributionReceiptId: null,
		replayStatus: 'unreplayable',
		unreplayableReason: 'notLoadedInAtlasRoute',
		contentLength: null
	};
}

function loadedSource(
	meta: UniverseRouteMeta,
	sourceId: string,
	dataKey: string,
	artifact: LoadedArtifact<unknown>
): SnapshotSource {
	return {
		sourceId,
		origin: 'hfDataset',
		path: artifact.path,
		versionOrEtag: artifact.versionOrEtag,
		payloadHash: artifact.payloadHash,
		dataAsOf: sourceDataAsOf(meta, dataKey),
		redistributionReceiptId: null,
		replayStatus: artifact.versionOrEtag ? 'replayable' : 'unreplayable',
		unreplayableReason: artifact.versionOrEtag ? null : 'movingSourceHasNoImmutableVersion',
		contentLength: artifact.contentLength
	};
}

export async function buildUniverseSnapshot(
	metaArtifact: LoadedArtifact<UniverseRouteMeta>,
	atlasArtifact: LoadedArtifact<UniverseAtlas>
): Promise<SourceSnapshotSet> {
	const meta = metaArtifact.value;
	const loaded = new Map<string, LoadedArtifact<unknown>>([
		['mapMeta', metaArtifact],
		['mapAtlas', atlasArtifact]
	]);
	const sources = SOURCE_SPECS.map(([sourceId, path, dataKey]) => {
		const artifact = loaded.get(sourceId);
		return artifact ? loadedSource(meta, sourceId, dataKey, artifact) : unavailableSource(meta, sourceId, path, dataKey);
	}).sort((left, right) => left.sourceId.localeCompare(right.sourceId));
	const snapshotPayload = {
		schemaVersion: 'sourceSnapshotSet.v1',
		sources: sources.map((source) => ({
			sourceId: source.sourceId,
			origin: source.origin,
			path: source.path,
			versionOrEtag: source.versionOrEtag,
			payloadHash: source.payloadHash,
			replayStatus: source.replayStatus
		})),
		mapBuildId: meta.buildId,
		capabilityCatalogVersion: null,
		recipeCatalogVersion: null
	};
	const snapshotSetId = await canonicalSha256(snapshotPayload);
	const unreplayableSourceIds = sources.filter((source) => source.replayStatus === 'unreplayable').map((source) => source.sourceId);
	return {
		schemaVersion: 'sourceSnapshotSet.v1',
		snapshotSetId,
		createdAt: meta.buildTime,
		sources,
		mapBuildId: meta.buildId,
		capabilityCatalogVersion: null,
		recipeCatalogVersion: null,
		exactReplayReady: unreplayableSourceIds.length === 0,
		unreplayableSourceIds,
		missingDataAsOfSourceIds: sources.filter((source) => !source.dataAsOf).map((source) => source.sourceId),
		missingRedistributionReceiptSourceIds: sources.filter((source) => !source.redistributionReceiptId).map((source) => source.sourceId)
	};
}

export async function loadUniverseMeta(core: DataCore): Promise<UniverseRouteMeta> {
	return (await requestArtifact(core, 'landing/map/meta.json', validateMeta)).value;
}

export async function loadMarketAtlas(core: DataCore): Promise<UniverseAtlas> {
	return (await requestArtifact(core, 'landing/map/atlas.json', validateAtlas)).value;
}

export async function loadIndustryProjection(core: DataCore, industryId: string): Promise<unknown> {
	if (!INDUSTRY_ID.test(industryId)) throw new Error('Universe industryId is invalid');
	return (await requestArtifact(core, `landing/map/industries/${industryId}.json`, asRecord)).value;
}

export async function loadCompanyProjection(core: DataCore, stockCode: string): Promise<unknown> {
	if (!STOCK_CODE.test(stockCode)) throw new Error('Universe stockCode is invalid');
	return (await requestArtifact(core, `landing/map/companies/${stockCode}.json`, asRecord)).value;
}

export async function loadObservationSeries(
	core: DataCore,
	entityId: string,
	metricId: string,
	range: UniverseObservationRange = {}
): Promise<UniverseObservationPoint[]> {
	const field = METRIC_FIELDS[metricId];
	if (!field) throw new Error(`Universe observation metric is unsupported: ${metricId}`);
	const company = asRecord(await loadCompanyProjection(core, entityId));
	const rows = Array.isArray(company.financials5y) ? company.financials5y : [];
	return rows.flatMap((value) => {
		const row = asRecord(value);
		const period = String(row.year ?? '');
		if (!period || (range.from && period < range.from) || (range.to && period > range.to)) return [];
		const rawValue = row[field];
		const numericValue = typeof rawValue === 'number' && Number.isFinite(rawValue) ? rawValue : null;
		return [{
			entityId,
			metricId,
			period,
			value: numericValue,
			unit: numericValue === null ? null : 'KRW',
			availableAt: null,
			sourceRef: `map:company:${entityId}#financials5y/${period}/${field}`
		}];
	}).sort((left, right) => left.period.localeCompare(right.period));
}

export async function loadUniverseRouteSeed(
	core: DataCore,
	releaseState: UniverseReleaseState = 'ga'
): Promise<UniverseRouteSeed> {
	if (releaseState === 'disabled') return disabledUniverseRouteSeed();
	const [metaArtifact, atlasArtifact] = await Promise.all([
		requestArtifact(core, 'landing/map/meta.json', validateMeta),
		requestArtifact(core, 'landing/map/atlas.json', validateAtlas)
	]);
	const snapshot = await buildUniverseSnapshot(metaArtifact, atlasArtifact);
	const graph = await adaptAtlas(atlasArtifact.value);
	const seedIds = graph.nodes.map((node) => node.nodeId).sort();
	const scene = await compileProjection({
		projectionId: `atlas:${metaArtifact.value.buildId}`,
		query: 'current market atlas',
		seedIds,
		sourceSnapshotSetId: snapshot.snapshotSetId,
		maxDepth: 0,
		maxNodes: seedIds.length,
		maxEdges: 200
	}, graph.nodes, graph.edges);
	const input = { meta: metaArtifact.value, atlas: atlasArtifact.value, snapshot, scene, releaseState };
	return { ...input, product: compileUniverseProductReceipt(input) };
}
