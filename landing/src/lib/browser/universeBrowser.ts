import { createDataCore } from '@dartlab/ui-runtime/data/fetch/request';
import {
	loadCompanyProjection,
	loadIndustryProjection,
	loadObservationSeries,
	loadUniverseRouteSeed
} from '@dartlab/ui-runtime/data/universe';
import type { DartlabBrowserOptions, UniverseBrowser } from './types';

export function createUniverseBrowser(options: DartlabBrowserOptions): UniverseBrowser {
	const dataCore = createDataCore({ fetchFn: options.fetchFn });
	return {
		seed: () => loadUniverseRouteSeed(dataCore),
		industry: (industryId) => loadIndustryProjection(dataCore, industryId),
		company: (stockCode) => loadCompanyProjection(dataCore, stockCode),
		observations: (entityId, metricId, range) => loadObservationSeries(dataCore, entityId, metricId, range)
	};
}
