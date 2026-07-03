// 기대치 격자 원장 · HF expectations/ 직독 (원장 정본 = append-only parquet + scorecard.json).
// 발행 = dartlab.simulate.expectationCycle (CI cron) · 여기는 read-only 소비자.
import type {
	EstimateStatementRow,
	ExpectationRow,
	ExpectationScorecard,
	ExpectationScoreRow,
	ExpectationsPort
} from '@dartlab/ui-contracts';
import { moduleFallbackCore, type DataCore } from '../../../data/fetch/request';

const fallbackCore = moduleFallbackCore();
const HOUR = 60 * 60_000;

function parseMaybeJson<T>(v: unknown): T | null {
	if (v == null) return null;
	if (typeof v !== 'string') return v as T;
	try {
		const parsed = JSON.parse(v) as T;
		return parsed ?? null;
	} catch {
		return null;
	}
}

export function createExpectationPort(core?: DataCore): ExpectationsPort {
	const c = () => fallbackCore(core);
	return {
		async getScorecard(): Promise<ExpectationScorecard | null> {
			try {
				return await c().request<ExpectationScorecard>({
					origin: 'hf',
					path: 'expectations/scorecard.json',
					parse: (res) => res.json() as Promise<ExpectationScorecard>,
					cacheKey: 'expectations.scorecard',
					cache: { scope: 'memory', ttlMs: HOUR, maxEntries: 1 }
				});
			} catch {
				return null; // 미발간/조회 실패 · 패널이 빈상태 문구로 정직 표기 (contracts 계약)
			}
		},
		async getLedger() {
			// 연도 shard: 원장은 2026 탄생 · 소형 통파일(수십 KB)이라 whole-file 직독.
			const year = new Date().getUTCFullYear();
			const [expRaw, scoreRaw] = await Promise.all([
				c().requestParquetWholeFile<Record<string, unknown>>({
					origin: 'hf',
					path: `expectations/expectations_${year}.parquet`,
					cacheKey: `expectations.rows:${year}`,
					cache: { scope: 'memory', ttlMs: HOUR, maxEntries: 2 }
				}),
				c().requestParquetWholeFile<Record<string, unknown>>({
					origin: 'hf',
					path: `expectations/scores_${year}.parquet`,
					cacheKey: `expectations.scores:${year}`,
					cache: { scope: 'memory', ttlMs: HOUR, maxEntries: 2 }
				})
			]);
			if (!expRaw) return null;
			const expectations: ExpectationRow[] = expRaw.map((r) => {
				const q = parseMaybeJson<Record<string, number>>(r.quantiles);
				return {
					expectationId: String(r.expectationId),
					domain: String(r.domain),
					variable: String(r.variable),
					unit: String(r.unit),
					freq: String(r.freq),
					horizon: Number(r.horizon),
					targetPeriod: String(r.targetPeriod),
					issuedAt: String(r.issuedAt),
					issuedLive: Boolean(r.issuedLive),
					kind: String(r.kind),
					quantiles: q ? Object.fromEntries(Object.entries(q).map(([k, v]) => [Number(k), Number(v)])) : null,
					direction: parseMaybeJson<ExpectationRow['direction']>(r.direction),
					warnings: parseMaybeJson<string[]>(r.warnings) ?? []
				};
			});
			const scores: ExpectationScoreRow[] = (scoreRaw ?? []).map((r) => ({
				expectationId: String(r.expectationId),
				scoredAt: String(r.scoredAt),
				actual: r.actual == null ? null : String(r.actual),
				coverageHit90: r.coverageHit90 == null ? null : Boolean(r.coverageHit90),
				coverageHit50: r.coverageHit50 == null ? null : Boolean(r.coverageHit50),
				skill: r.skill == null ? null : Number(r.skill),
				brier: r.brier == null ? null : Number(r.brier),
				error: r.error == null ? null : String(r.error)
			}));
			return { expectations, scores };
		},
		async getEstimateStatements(code: string): Promise<EstimateStatementRow[] | null> {
			// 라이브러리 발행 뷰(estimateStatements.parquet) 직독. 매핑·라벨·순서는 뷰가 가진다.
			const raw = await c().requestParquetWholeFile<Record<string, unknown>>({
				origin: 'hf',
				path: 'expectations/estimateStatements.parquet',
				cacheKey: 'expectations.estimateStatements',
				cache: { scope: 'memory', ttlMs: HOUR, maxEntries: 1 }
			});
			if (!raw) return null;
			return raw
				.filter((r) => String(r.code) === code)
				.map((r) => ({
					code: String(r.code),
					targetPeriod: String(r.targetPeriod),
					quantile: Number(r.quantile),
					statement: String(r.statement),
					rowKey: String(r.rowKey),
					labelKr: String(r.labelKr),
					labelEn: String(r.labelEn),
					sortOrder: Number(r.sortOrder),
					value: Number(r.value),
					parentId: String(r.parentId)
				}));
		}
	};
}
