import type { LensPort, LensProductBundle } from '@dartlab/ui-contracts';
import type { LocalApi } from '../api/localApi';

/** 로컬 터미널은 Python 엔진의 같은 Company 세션 product bundle을 그대로 소비한다. */
export function localLensPort(api: LocalApi): LensPort {
	return {
		products(code) {
			return api.getJson<LensProductBundle>(`/api/company/${encodeURIComponent(code)}/lenses`);
		}
	};
}
