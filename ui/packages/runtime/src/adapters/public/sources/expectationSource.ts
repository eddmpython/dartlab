// 기대치 격자 성적표 · HF expectations/scorecard.json 직독 (원장 정본 = HF append-only).
// 발행 = dartlab.simulate.expectationCycle (CI cron) · 여기는 read-only 소비자.
import type { ExpectationScorecard, ExpectationsPort } from '@dartlab/ui-contracts';
import { moduleFallbackCore, type DataCore } from '../../../data/fetch/request';

const fallbackCore = moduleFallbackCore();

export function createExpectationPort(core?: DataCore): ExpectationsPort {
	return {
		async getScorecard(): Promise<ExpectationScorecard | null> {
			try {
				return await fallbackCore(core).request<ExpectationScorecard>({
					origin: 'hf',
					path: 'expectations/scorecard.json',
					parse: (res) => res.json() as Promise<ExpectationScorecard>,
					cacheKey: 'expectations.scorecard',
					cache: { scope: 'memory', ttlMs: 60 * 60_000, maxEntries: 1 }
				});
			} catch {
				return null; // 미발간/조회 실패 · 패널이 빈상태 문구로 정직 표기 (contracts 계약)
			}
		}
	};
}
