// 회사 재무 신호 일괄 로더 · Q&A 결정론 답(answerCompose)의 재무 근거 원천.
// IS/BS/CF 연간 statement 를 DuckDB 로 로드해 financeSignals 로 환산, 회사별 1회 캐시.
// 임계를 낮춰 모든 계정행을 신호로(질문이 계정명만 매칭하면 추세/규모/전환을 답할 수 있게).
// financeAvailability·loadFinanceStatement·financeSignals 전부 재사용 · 신규 로직 0.

import { financeAvailability, loadFinanceStatement } from './finance/financeQuery';
import { financeSignals, type FinanceSignal } from './diff';
import type { FinanceKind } from './finance/types';

// IS + CIS(단일 포괄손익만 보고하는 회사 = IS 없음) + BS + CF. financeAvailability 가 회사별 가용분만 통과시킴.
const KINDS: FinanceKind[] = ['IS', 'CIS', 'BS', 'CF'];
const cache = new Map<string, FinanceSignal[]>();

// 진입 시 백그라운드 prefetch 권장 · 질문 시점엔 캐시 히트(0ms).
export async function loadCompanyFinanceSignals(code: string): Promise<FinanceSignal[]> {
	const hit = cache.get(code);
	if (hit) return hit;
	const out: FinanceSignal[] = [];
	try {
		const avail = await financeAvailability(code, 'KR');
		if (avail.scopes.length) {
			const scope = avail.scopes.includes('CFS') ? 'CFS' : avail.scopes[0];
			for (const kind of KINDS) {
				const kinds = avail.byScope[scope];
				if (kinds && !kinds.includes(kind)) continue;
				const stmt = await loadFinanceStatement(code, 'KR', kind, 'annual', scope);
				// 임계 낮춤 = 모든 2기간+ 계정행이 신호(매칭만 되면 답 가능). 추세/전환 판정은 그대로 정확.
				if (stmt && stmt.rows.length) out.push(...financeSignals(stmt, { minRun: 2, minDeltaPct: 0 }));
			}
		}
	} catch {
		// 재무 데이터 없음 / DuckDB(iOS Safari 등) 미지원 · 빈 신호. 텍스트 검색으로 폴백.
	}
	cache.set(code, out);
	return out;
}

export function clearFinanceSignals(code?: string): void {
	if (code) cache.delete(code);
	else cache.clear();
}
