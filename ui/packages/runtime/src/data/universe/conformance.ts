import type {
	GapReceipt,
	UniverseConformanceObservation,
	UniverseLegalEntityIdentity,
	UniversePairedQuestion,
	UniversePairedResult
} from '@dartlab/ui-contracts';
import { canonicalSha256, stripSha256 } from './canonical';

const KR_CORP_CODE = /^[0-9]{8}$/;
const KR_SECURITY = /^[0-9A-Z]{6}$/;
const US_CIK = /^[0-9]{10}$/;
const US_TICKER = /^[A-Z][A-Z0-9.-]{0,9}$/;

export const UNIVERSE_PAIRED_QUESTIONS: readonly UniversePairedQuestion[] = [
	{ questionId: 'paired:01', label: '최근 연간 매출 규모', metricId: 'revenue' },
	{ questionId: 'paired:02', label: '최근 연간 영업이익', metricId: 'operatingProfit' },
	{ questionId: 'paired:03', label: '최근 연간 순이익', metricId: 'netIncome' },
	{ questionId: 'paired:04', label: '총자산', metricId: 'totalAssets' },
	{ questionId: 'paired:05', label: '총부채', metricId: 'totalLiabilities' },
	{ questionId: 'paired:06', label: '영업현금흐름', metricId: 'operatingCashFlow' },
	{ questionId: 'paired:07', label: '투자현금흐름', metricId: 'investingCashFlow' },
	{ questionId: 'paired:08', label: '재무현금흐름', metricId: 'financingCashFlow' },
	{ questionId: 'paired:09', label: '자본적지출', metricId: 'capitalExpenditure' },
	{ questionId: 'paired:10', label: '현금 및 현금성 자산', metricId: 'cash' },
	{ questionId: 'paired:11', label: '단기 차입금', metricId: 'shortTermDebt' },
	{ questionId: 'paired:12', label: '장기 차입금', metricId: 'longTermDebt' },
	{ questionId: 'paired:13', label: '이자비용', metricId: 'interestExpense' },
	{ questionId: 'paired:14', label: '매출 성장률', metricId: 'revenueGrowth' },
	{ questionId: 'paired:15', label: '영업이익률', metricId: 'operatingMargin' },
	{ questionId: 'paired:16', label: '자기자본이익률', metricId: 'returnOnEquity' },
	{ questionId: 'paired:17', label: '부채비율', metricId: 'debtRatio' },
	{ questionId: 'paired:18', label: '유동비율', metricId: 'currentRatio' },
	{ questionId: 'paired:19', label: '최근 정기공시 시점', metricId: 'latestPeriodicFiling' },
	{ questionId: 'paired:20', label: '공시 후 이용 가능 시점', metricId: 'filingAvailableAt' }
];

async function identity(prefix: string, payload: unknown): Promise<string> {
	return `${prefix}:${stripSha256(await canonicalSha256(payload))}`;
}

function validIdentity(entity: UniverseLegalEntityIdentity): boolean {
	if (!entity.sourceRef || !entity.validFrom || !entity.securityId || !entity.ticker) return false;
	if (entity.market === 'KR') return KR_CORP_CODE.test(entity.legalEntityId) && KR_SECURITY.test(entity.securityId);
	return US_CIK.test(entity.legalEntityId) && US_TICKER.test(entity.ticker);
}

async function conformanceGap(questionId: string, market: 'KR' | 'US' | 'PAIR', reasonCode: string): Promise<GapReceipt> {
	return {
		gapId: await identity('gap', { questionId, market, reasonCode }),
		kind: 'unresolved',
		ownerSource: market === 'PAIR' ? 'crossMarketConformance' : `${market} panel`,
		requestedField: questionId,
		reasonCode,
		retryPolicy: 'supplyExactConformanceObservation'
	};
}

function exactObservation(observation: UniverseConformanceObservation | undefined): observation is UniverseConformanceObservation {
	return Boolean(observation && validIdentity(observation.entity) && observation.sourceRef
		&& observation.dataAsOf && observation.unit && observation.value !== null);
}

export async function compilePairedConformance(
	krObservations: readonly UniverseConformanceObservation[],
	usObservations: readonly UniverseConformanceObservation[],
	questions: readonly UniversePairedQuestion[] = UNIVERSE_PAIRED_QUESTIONS
): Promise<UniversePairedResult[]> {
	if (questions.length !== 20 || new Set(questions.map((question) => question.questionId)).size !== 20) {
		throw new Error('Universe paired demo requires exactly 20 fixed questions');
	}
	const krByMetric = new Map(krObservations.map((observation) => [observation.metricId, observation]));
	const usByMetric = new Map(usObservations.map((observation) => [observation.metricId, observation]));
	const results: UniversePairedResult[] = [];
	for (const question of questions) {
		const kr = krByMetric.get(question.metricId);
		const us = usByMetric.get(question.metricId);
		const gaps: GapReceipt[] = [];
		if (!exactObservation(kr)) gaps.push(await conformanceGap(question.questionId, 'KR', 'exactObservationMissing'));
		if (!exactObservation(us)) gaps.push(await conformanceGap(question.questionId, 'US', 'exactObservationMissing'));
		if (exactObservation(kr) && exactObservation(us) && kr.unit !== us.unit) {
			gaps.push(await conformanceGap(question.questionId, 'PAIR', 'unitMismatch'));
		}
		if (exactObservation(kr) && exactObservation(us) && kr.dataAsOf !== us.dataAsOf) {
			gaps.push(await conformanceGap(question.questionId, 'PAIR', 'dataAsOfMismatch'));
		}
		results.push({
			question,
			status: gaps.length === 0 ? 'ready' : 'blocked',
			kr: exactObservation(kr) ? kr : null,
			us: exactObservation(us) ? us : null,
			gaps
		});
	}
	return results;
}
