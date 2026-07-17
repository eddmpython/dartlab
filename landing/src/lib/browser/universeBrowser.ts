import { createDataCore } from '@dartlab/ui-runtime/data/fetch/request';
import {
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
	return {
		seed,
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
