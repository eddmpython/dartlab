import { loadJson, prewarmJson } from '@dartlab/ui-runtime/data/dartlabData';
import { BrowserCompany } from './company';
import type { DartlabBrowserOptions, MarketMapBundle, ScanBundle } from './types';

export function createDartlabBrowser(options: DartlabBrowserOptions) {
	const fetchFn = options.fetchFn;

	return {
		async Company(stockCode: string): Promise<BrowserCompany> {
			return new BrowserCompany(stockCode, options);
		},

		async marketMap(): Promise<MarketMapBundle> {
			const [ecosystem, atlas, industryStats, meta, movers, timeline] = await Promise.all([
				loadJson<any>('map/ecosystem.json', { fetchFn, required: true }),
				loadJson<any>('map/atlas.json', { fetchFn, required: true }),
				loadJson<any>('map/industryStats.json', { fetchFn }),
				loadJson<any>('map/meta.json', { fetchFn }),
				loadJson<any>('map/movers.json', { fetchFn }),
				loadJson<any>('map/timeline.json', { fetchFn })
			]);
			return { ecosystem, atlas, industryStats: industryStats ?? {}, meta, movers, timeline };
		},

		async scan(): Promise<ScanBundle> {
			const [ecosystem, meta, markets] = await Promise.all([
				loadJson<any>('map/ecosystem.json', { fetchFn }),
				loadJson<any>('map/meta.json', { fetchFn }),
				loadJson<Record<string, string>>('map/markets.json', { fetchFn })
			]);
			return {
				ecosystem: ecosystem ?? { nodes: [], industries: [] },
				meta,
				markets: markets ?? {}
			};
		},

		prewarm(paths: string[]): void {
			prewarmJson(paths, fetchFn);
		}
	};
}
