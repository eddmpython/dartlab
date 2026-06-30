// 정량재무제표 IO · 회사 parquet(dart/finance/{code}.parquet)을 차트(hyparquet)가 이미 받아 캐시한 raw 행으로
// JS 집계. DuckDB-WASM 제거(수십 MB SQL 엔진 콜드스타트·HF 직결 range 왕복 0): 셸이 provideFinanceRows 로
// 행 로더(런타임 hyparquet, 차트와 캐시 공유)를 주입한다. 순수 SQL등가 로직(queryRowsFromRaw·pivot·
// buildSceMatrix)은 financePivot.ts · 테스트 가능. 미주입(또는 행 미가용) = 정직 빈 재무(throw 금지).

import { buildSceMatrix, pivot, queryRowsFromRaw, sceComponent, type RawFinanceRow, type SceQueryRow } from './financePivot';
import type { FinanceFreq, FinanceKind, FinanceScope, FinanceStatement, SceMatrixData } from './types';

const ALL_KINDS: FinanceKind[] = ['IS', 'BS', 'CF', 'CIS', 'SCE'];

// 회사 재무 raw 행 주입 · surfaces 는 hyparquet/런타임에 직접 결합하지 않는다(셸이 주입). 미주입·실패 = null.
// landing 컴포지션 루트가 provideFinanceRows(loadFinanceRows)로 주입 · bundle()(차트)과 같은 rowsCache 공유.
let rowsProvider: ((code: string) => Promise<RawFinanceRow[] | null>) | null = null;
export function provideFinanceRows(loader: (code: string) => Promise<RawFinanceRow[] | null>): void {
	rowsProvider = loader;
}
function loadRows(code: string): Promise<RawFinanceRow[] | null> {
	return rowsProvider ? rowsProvider(code) : Promise.resolve(null);
}

// 숫자 파싱 · financePivot 의 SQL등가 파서와 동일 규약(콤마 제거 후 실수, 실패 null). SCE 매핑 전용.
function toNum(v: unknown): number | null {
	if (v == null) return null;
	if (typeof v === 'number') return Number.isFinite(v) ? v : null;
	if (typeof v === 'bigint') return Number(v);
	const n = Number(String(v).replace(/,/g, ''));
	return Number.isFinite(n) ? n : null;
}
const toInt = (v: unknown): number | null => { const n = toNum(v); return n == null ? null : Math.trunc(n); };

export interface FinanceAvailability {
	scopes: FinanceScope[]; // 실제 보고된 범위(CFS/OFS) · 별도 없는 회사는 OFS 토글 숨김. CFS 우선 정렬 = 연결 우선 기본.
	byScope: Record<string, FinanceKind[]>; // scope → 가용 statement (단일 포괄손익 회사는 IS 없음)
}

// 회사의 (scope × statement) 가용 조합 · 빈 scope 토글·빈 statement 탭 제거. dart/finance 인코딩이 회사별로
// 다른 현실 반영(연결/별도 유무 + 별도 2표 vs 단일 포괄손익). scopes 는 CFS 우선 정렬이라 기본 = 연결 우선.
export async function financeAvailability(stockCode: string, market: 'KR' | 'US'): Promise<FinanceAvailability> {
	const fallback: FinanceAvailability = { scopes: ['CFS', 'OFS'], byScope: { CFS: ALL_KINDS, OFS: ALL_KINDS } };
	if (market !== 'KR') return { scopes: [], byScope: {} };
	const rows = await loadRows(stockCode);
	if (!rows) return fallback; // 행 미가용(미주입·로드 실패) · 토글 노출, 로드에서 정직 안내
	const present: Record<string, Set<string>> = {};
	for (const r of rows) {
		const fs = String(r.fs_div ?? ''), sj = String(r.sj_div ?? '');
		if (!fs || !sj) continue;
		(present[fs] ??= new Set()).add(sj);
	}
	const scopes = (['CFS', 'OFS'] as FinanceScope[]).filter((s) => present[s]?.size); // CFS 우선 정렬 유지
	const byScope: Record<string, FinanceKind[]> = {};
	for (const s of scopes) byScope[s] = ALL_KINDS.filter((k) => present[s].has(k));
	return scopes.length ? { scopes, byScope } : fallback;
}

// 자본변동표(SCE) · 변동유형×자본구성요소 matrix (연간 11011). account×period 표가 아닌 전용.
export async function loadSceMatrix(stockCode: string, market: 'KR' | 'US', scope: FinanceScope): Promise<SceMatrixData | null> {
	if (market !== 'KR') return null;
	const rows = await loadRows(stockCode);
	if (!rows) return null;
	const raw: SceQueryRow[] = [];
	for (const r of rows) {
		if (String(r.sj_div ?? '') !== 'SCE' || String(r.fs_div ?? '') !== scope || String(r.reprt_code ?? '') !== '11011' || r.account_nm == null) continue;
		raw.push({
			period: String(r.bsns_year ?? ''),
			label: String(r.account_nm),
			comp: sceComponent(r.account_detail == null ? null : String(r.account_detail)),
			val: toNum(r.thstrm_amount),
			ord: toInt(r.ord)
		});
	}
	if (raw.length === 0) return { scope, periods: [], components: [], byPeriod: {}, unit: 'KRW' };
	return buildSceMatrix(raw, scope);
}

// 한 statement(연결/별도·freq) · raw 행 → QueryRow(JS) → pivot. EDGAR(us)는 v1 미지원(null).
export async function loadFinanceStatement(
	stockCode: string,
	market: 'KR' | 'US',
	kind: FinanceKind,
	freq: FinanceFreq,
	scope: FinanceScope
): Promise<FinanceStatement | null> {
	if (market !== 'KR') return null; // EDGAR companyfacts → statement 매핑은 후속(별도 스키마)
	const rows = await loadRows(stockCode);
	if (!rows) return null; // 행 미가용 · 호출측이 안내
	const qrows = queryRowsFromRaw(rows, kind, freq, scope);
	if (qrows.length === 0) return { kind, scope, freq, periods: [], rows: [], unit: 'KRW' };
	return pivot(qrows, kind, scope, freq);
}
