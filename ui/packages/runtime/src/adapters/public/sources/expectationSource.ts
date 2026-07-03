// 기대치 격자 원장 · HF expectations/ 직독 (원장 정본 = append-only parquet + scorecard.json).
// 발행 = dartlab.simulate.expectationCycle (CI cron) · 여기는 read-only 소비자.
import type {
	ExpectationRow,
	ExpectationScorecard,
	ExpectationScoreRow,
	ExpectationsPort,
	ProformaEstimateRow
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
		async getProforma(code: string): Promise<ProformaEstimateRow[] | null> {
			// v1: 연도 shard 통파일 직독(현재 수천 행). 전상장사 sweep 후 수십만 행이 되면
			// code 정렬 + row-group prune(hfRange) 로 전환한다 (05 E4 원장 부채로 기록).
			const year = new Date().getUTCFullYear();
			const raw = await c().requestParquetWholeFile<Record<string, unknown>>({
				origin: 'hf',
				path: `expectations/proforma_${year}.parquet`,
				cacheKey: `expectations.proforma:${year}`,
				cache: { scope: 'memory', ttlMs: HOUR, maxEntries: 2 }
			});
			if (!raw) return null;
			return raw
				.filter((r) => String(r.code) === code && Boolean(r.issuedLive))
				.map((r) => ({
					parentId: String(r.parentId),
					targetPeriod: String(r.targetPeriod),
					quantile: Number(r.quantile),
					statement: String(r.statement),
					account: String(r.account),
					value: Number(r.value),
					issuedLive: Boolean(r.issuedLive)
				}));
		}
	};
}
