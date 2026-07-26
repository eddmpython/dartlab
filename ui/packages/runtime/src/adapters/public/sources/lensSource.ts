import type { LensPort, LensProductBundle } from '@dartlab/ui-contracts';
import { loadJson } from '../../../data/dartlabData';

const browser = typeof window !== 'undefined';

/**
 * 퍼블릭 터미널은 엔진이 미리 발행한 product artifact만 읽는다.
 * 파일이 아직 발행되지 않은 회사는 null이며 브라우저가 판단을 재계산하지 않는다.
 */
export function createPublicLensPort(): LensPort {
	return {
		async products(code) {
			if (!browser) return null;
			return loadJson<LensProductBundle>(`lenses/${code.trim()}.json`, {
				fetchFn: fetch,
				required: false
			});
		}
	};
}
