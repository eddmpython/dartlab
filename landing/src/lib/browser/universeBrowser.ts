import { createDataCore } from '@dartlab/ui-runtime/data/fetch/request';
import {
	createUniverseGlobalRuntime,
	createUniverseKnowledgeRuntime,
	createUniverseEvidenceResolver,
	loadCurrentChangeUniverse,
	loadCompanyProjection,
	loadIndustryProjection,
	loadObservationSeries,
	loadUniverseRouteSeed
} from '@dartlab/ui-runtime/data/universe';
import type { DartlabBrowserOptions, UniverseBrowser } from './types';

export function createUniverseBrowser(options: DartlabBrowserOptions): UniverseBrowser {
	const dataCore = createDataCore({ fetchFn: options.fetchFn });
	let seedPromise: ReturnType<typeof loadUniverseRouteSeed> | null = null;
	const seed = () => (seedPromise ??= loadUniverseRouteSeed(dataCore, options.universeReleaseState));
	const resolveEvidence = createUniverseEvidenceResolver(dataCore);
	const global = createUniverseGlobalRuntime(dataCore);
	const knowledge = createUniverseKnowledgeRuntime(dataCore, {
		loadSkillGraph: async () => (await import('$skills/graph.json')).default,
		loadSkillCatalog: async () => (await import('$skills/catalog.json')).default
	});
	return {
		seed,
		knowledgeOverview: knowledge.overview,
		knowledgeCoverage: knowledge.coverage,
		knowledgeContent: knowledge.content,
		searchKnowledge: knowledge.search,
		openKnowledge: knowledge.open,
		globalCoverage: global.coverage,
		searchEntities: global.search,
		entityProfile: global.profile,
		compareEntities: global.compare,
		industry: (industryId) => loadIndustryProjection(dataCore, industryId),
		company: (stockCode) => loadCompanyProjection(dataCore, stockCode),
		observations: (entityId, metricId, range) => loadObservationSeries(dataCore, entityId, metricId, range),
		changes: async (maxMarks) => {
			const routeSeed = await seed();
			return loadCurrentChangeUniverse(dataCore, routeSeed.atlas, routeSeed.snapshot, maxMarks);
		},
		resolveEvidence
	};
}
