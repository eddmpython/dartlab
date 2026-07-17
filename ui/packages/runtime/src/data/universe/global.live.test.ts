import { describe, expect, it } from 'vitest';
import { createDataCore } from '../fetch/request';
import { createUniverseGlobalRuntime } from './global';

const liveDescribe = process.env.DARTLAB_LIVE_DATA === '1' ? describe : describe.skip;

liveDescribe('Universe global catalog live SSOT', () => {
	it('공개 DART와 EDGAR parquet를 직접 읽어 검색과 프로필을 결속한다', async () => {
		const runtime = createUniverseGlobalRuntime(createDataCore());
		const coverage = await runtime.coverage();
		expect(coverage.krLegalEntityCount).toBeGreaterThan(100_000);
		expect(coverage.krSecurityCount).toBeGreaterThan(3_000);
		expect(coverage.usLegalEntityCount).toBeGreaterThan(10_000);
		expect(coverage.usFinanceEntityCount).toBeGreaterThan(7_000);

		const [samsungSearch, appleSearch, cikOnlySearch] = await Promise.all([
			runtime.search({ query: '삼성전자', market: 'KR' }),
			runtime.search({ query: 'AAPL', market: 'US' }),
			runtime.search({ query: '0000001961', market: 'US' })
		]);
		expect(samsungSearch.matches[0]?.ticker).toBe('005930');
		expect(appleSearch.matches[0]?.legalEntityId).toBe('0000320193');
		expect(cikOnlySearch.matches[0]?.legalEntityId).toBe('0000001961');

		const [samsung, apple, cikOnly] = await Promise.all([
			runtime.profile(samsungSearch.matches[0]!.entityId),
			runtime.profile(appleSearch.matches[0]!.entityId),
			runtime.profile(cikOnlySearch.matches[0]!.entityId)
		]);
		expect(samsung.answeredQuestionCount).toBeGreaterThan(10);
		expect(apple.answeredQuestionCount).toBeGreaterThan(10);
		expect(cikOnly.entity.ticker).toBeNull();
		expect(cikOnly.answeredQuestionCount).toBeGreaterThan(0);
		const comparison = await runtime.compare(samsung.entity.entityId, apple.entity.entityId);
		expect(comparison.results).toHaveLength(20);
		expect(comparison.results.find((result) => result.question.metricId === 'revenue')?.status).toBe('blocked');
	}, 60_000);
});
