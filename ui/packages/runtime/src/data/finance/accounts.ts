// 재무제표 28 표준계정 매핑 + 계정매칭 · 단일 SSOT.
//
// 원래 financeSource.ts(터미널 번들)에 인라인돼 있던 STD 테이블·매칭 규칙·파싱 primitive 를
// 여기로 추출한다. financeSource.ts(브라우저 터미널)와 annual.ts(블로그·정적 SEO 빌드타임)가
// **같은 표준화**를 공유 · 평행 재구현 추가 0. src/dartlab/viz/display/finance/accounts.py(_STANDARDS)
// 포팅의 TS 정본.
//
// Node+브라우저 안전(svelte·DOM 의존 0) · annual.ts 가 SvelteKit prerender(Node)에서 import 한다.

export interface StdAcct {
	key: string;
	sj: 'IS' | 'BS' | 'CF' | 'CIS';
	ids: string[]; // account_id (IFRS) 우선
	kw: string[]; // account_nm 키워드 fallback
	ex?: string[]; // nm 매칭 제외 키워드 · includes 포함매칭의 오선택 차단 (예: longDebt 가 '유동성장기차입금'을 잡는 사고)
}

// ── 28 표준계정 (accounts.py _STANDARDS 포팅) ──
export const STD: StdAcct[] = [
	// IS
	{ key: 'revenue', sj: 'IS', ids: ['ifrs-full_Revenue', 'ifrs_Revenue'], kw: ['매출액', '영업수익', '수익(매출액)'] },
	{ key: 'costOfSales', sj: 'IS', ids: ['ifrs-full_CostOfSales', 'ifrs_CostOfSales'], kw: ['매출원가'] },
	{ key: 'grossProfit', sj: 'IS', ids: [], kw: ['매출총이익'] },
	{ key: 'operatingIncome', sj: 'IS', ids: ['dart_OperatingIncomeLoss', 'ifrs-full_ProfitLossFromOperatingActivities', 'ifrs_OperatingProfitLoss'], kw: ['영업이익', '영업이익(손실)'] },
	{ key: 'netIncome', sj: 'IS', ids: ['ifrs-full_ProfitLoss', 'ifrs_ProfitLoss'], kw: ['당기순이익', '당기순이익(손실)', '순이익'] },
	{ key: 'sga', sj: 'IS', ids: ['dart_TotalSellingGeneralAdministrativeExpenses', 'ifrs-full_SellingGeneralAndAdministrativeExpense'], kw: ['판매비와관리비', '판매관리비'] },
	{ key: 'financeIncome', sj: 'IS', ids: ['ifrs-full_FinanceIncome', 'ifrs_FinanceIncome'], kw: ['금융수익'] },
	{ key: 'financeCosts', sj: 'IS', ids: ['ifrs-full_FinanceCosts', 'ifrs_FinanceCosts'], kw: ['금융비용'] },
	{ key: 'incomeTax', sj: 'IS', ids: ['ifrs-full_IncomeTaxExpenseContinuingOperations', 'ifrs_IncomeTaxExpense'], kw: ['법인세비용'] },
	// BS
	{ key: 'assets', sj: 'BS', ids: ['ifrs-full_Assets', 'ifrs_Assets'], kw: ['자산총계'] },
	{ key: 'currentAssets', sj: 'BS', ids: ['ifrs-full_CurrentAssets', 'ifrs_CurrentAssets'], kw: ['유동자산'] },
	{ key: 'cash', sj: 'BS', ids: ['ifrs-full_CashAndCashEquivalents', 'ifrs_CashAndCashEquivalents'], kw: ['현금및현금성자산', '현금성자산'] },
	{ key: 'inventories', sj: 'BS', ids: ['ifrs-full_Inventories', 'ifrs_Inventories'], kw: ['재고자산'] },
	{ key: 'receivables', sj: 'BS', ids: ['ifrs-full_TradeAndOtherCurrentReceivables', 'dart_ShortTermTradeReceivable'], kw: ['매출채권'] },
	{ key: 'liabilities', sj: 'BS', ids: ['ifrs-full_Liabilities', 'ifrs_Liabilities'], kw: ['부채총계'] },
	{ key: 'currentLiabilities', sj: 'BS', ids: ['ifrs-full_CurrentLiabilities', 'ifrs_CurrentLiabilities'], kw: ['유동부채'] },
	{ key: 'payables', sj: 'BS', ids: ['ifrs-full_TradeAndOtherCurrentPayables', 'dart_ShortTermTradePayables'], kw: ['매입채무'] },
	{ key: 'shortDebt', sj: 'BS', ids: ['ifrs-full_ShorttermBorrowings', 'ifrs_ShorttermBorrowings'], kw: ['단기차입금'], ex: ['유동성'] },
	// '유동성장기차입금'.includes('장기차입금')=true 라 ex 가드 없이는 longDebt 가 유동성 행을
	// 오선택/이중계상 · 차입 3분해(shortDebt·currentLtDebt·longDebt)의 정합 전제.
	{ key: 'longDebt', sj: 'BS', ids: ['ifrs-full_LongtermBorrowings', 'ifrs_LongtermBorrowings'], kw: ['장기차입금', '사채'], ex: ['유동성'] },
	{ key: 'currentLtDebt', sj: 'BS', ids: [], kw: ['유동성장기차입금', '유동성장기부채', '유동성사채'] },
	{ key: 'equity', sj: 'BS', ids: ['ifrs-full_Equity', 'ifrs_Equity'], kw: ['자본총계'] },
	{ key: 'capitalStock', sj: 'BS', ids: ['ifrs-full_IssuedCapital', 'ifrs_IssuedCapital', 'dart_IssuedCapital'], kw: ['자본금'], ex: ['잉여금'] },
	{ key: 'capitalSurplus', sj: 'BS', ids: ['ifrs-full_SharePremium', 'dart_AdditionalPaidInCapital', 'ifrs_SharePremium'], kw: ['자본잉여금', '주식발행초과금'] },
	{ key: 'retainedEarnings', sj: 'BS', ids: ['ifrs-full_RetainedEarnings', 'ifrs_RetainedEarnings'], kw: ['이익잉여금'] },
	// CF
	{ key: 'cfOperating', sj: 'CF', ids: ['ifrs-full_CashFlowsFromUsedInOperatingActivities', 'ifrs_CashFlowsFromUsedInOperatingActivities'], kw: ['영업활동현금흐름', '영업활동'] },
	{ key: 'cfInvesting', sj: 'CF', ids: ['ifrs-full_CashFlowsFromUsedInInvestingActivities', 'ifrs_CashFlowsFromUsedInInvestingActivities'], kw: ['투자활동현금흐름', '투자활동'] },
	{ key: 'cfFinancing', sj: 'CF', ids: ['ifrs-full_CashFlowsFromUsedInFinancingActivities', 'ifrs_CashFlowsFromUsedInFinancingActivities'], kw: ['재무활동현금흐름', '재무활동'] },
	{ key: 'capex', sj: 'CF', ids: ['ifrs-full_PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities', 'dart_PurchaseOfPropertyPlantAndEquipment'], kw: ['유형자산의취득', '유형자산취득'] },
	{ key: 'dividendsPaid', sj: 'CF', ids: ['ifrs-full_DividendsPaidClassifiedAsFinancingActivities', 'ifrs_DividendsPaid'], kw: ['배당금지급'] },
	// CIS · 포괄손익계산서 원본 레인. 단일 포괄손익 회사(카카오류)의 손익 폴백·포괄손익 격차·SCE OCI 폴백.
	{ key: 'cisNetIncome', sj: 'CIS', ids: ['ifrs-full_ProfitLoss', 'ifrs_ProfitLoss'], kw: ['당기순이익', '분기순이익', '반기순이익'] },
	{ key: 'cisComprehensive', sj: 'CIS', ids: ['ifrs-full_ComprehensiveIncome', 'ifrs_ComprehensiveIncome'], kw: ['총포괄손익', '총포괄이익'] }
];

export const STD_BY_KEY: Record<string, StdAcct> = Object.fromEntries(STD.map((s) => [s.key, s]));
export const isStock = (k: string): boolean => STD_BY_KEY[k]?.sj === 'BS';

// thstrm_add_amount = 누적(YTD) · 정량재무 표(분기 standalone)가 쓴다. 표·차트 1회 다운로드 공유 위해 컬럼셋 통일.
export const FINANCE_COLUMNS = ['sj_div', 'fs_div', 'reprt_code', 'rcept_no', 'bsns_year', 'account_id', 'account_nm', 'account_detail', 'thstrm_amount', 'thstrm_add_amount', 'ord'];

export const Q_BY_CODE: Record<string, number> = { '11013': 1, '11012': 2, '11014': 3, '11011': 4 };

export interface RawRow extends Record<string, unknown> {
	sj_div?: string | null;
	fs_div?: string | null;
	reprt_code?: string | null;
	rcept_no?: string | null;
	bsns_year?: string | number | null;
	account_id?: string | null;
	account_nm?: string | null;
	account_detail?: string | null;
	thstrm_amount?: string | number | null;
	thstrm_add_amount?: string | number | null;
	ord?: string | number | null;
}

export type FinanceScope = 'CFS' | 'OFS';

/** 연결·별도 자동 선택 SSOT. 최신 유효 공시가 같은 경우에만 연결을 우선한다. */
export function latestFinancePeriod(rows: RawRow[], scope: FinanceScope, quarter?: number): number | null {
	let latest: number | null = null;
	for (const row of rows) {
		if ((row.fs_div || '') !== scope) continue;
		if (!['IS', 'CIS', 'BS', 'CF'].includes(String(row.sj_div || ''))) continue;
		const q = Q_BY_CODE[String(row.reprt_code || '')];
		const year = Number(row.bsns_year);
		if (!q || (quarter != null && q !== quarter) || !Number.isFinite(year) || num(row.thstrm_amount) == null) continue;
		const period = year * 10 + q;
		if (latest == null || period > latest) latest = period;
	}
	return latest;
}

export function selectFreshestFinanceScope(rows: RawRow[], quarter?: number): FinanceScope | null {
	const cfs = latestFinancePeriod(rows, 'CFS', quarter);
	const ofs = latestFinancePeriod(rows, 'OFS', quarter);
	if (cfs == null) return ofs == null ? null : 'OFS';
	if (ofs == null) return 'CFS';
	return ofs > cfs ? 'OFS' : 'CFS';
}

export interface Parsed {
	sj: string;
	year: number;
	q: number; // 1..4
	id: string;
	nm: string;
	detail: string;
	ord: number;
	amt: number; // 누적(YTD) for IS/CF, 시점 for BS
}

export function num(v: unknown): number | null {
	if (typeof v === 'number') return Number.isFinite(v) ? v : null;
	if (typeof v === 'bigint') return Number(v);
	if (typeof v === 'string' && v.trim()) {
		const n = Number(v.replace(/,/g, ''));
		return Number.isFinite(n) ? n : null;
	}
	return null;
}

// 표준계정 × (year,q) 격자 · STD 별 독립 매칭(행 소비/순서 의존 없음). id 매칭 우선, 없으면 nm 키워드.
// 같은 셀 다중 후보 시 account_detail='-' 우선·ord 최소. financeSource buildBundle 의 인라인 로직과 동일.
export function buildGrid(parsed: Parsed[]): Record<string, Map<string, Parsed>> {
	const score = (x: Parsed, byId: boolean) => (byId ? 0 : 1000) + (x.detail === '-' || x.detail === '' ? 0 : 100) + Math.min(x.ord, 99);
	const grid: Record<string, Map<string, Parsed>> = {};
	for (const s of STD) {
		const m = new Map<string, Parsed>();
		for (const p of parsed) {
			if (p.sj !== s.sj) continue;
			const idHit = s.ids.length > 0 && s.ids.includes(p.id);
			const nmHit = !idHit && s.kw.some((k) => p.nm.includes(k)) && !s.ex?.some((x) => p.nm.includes(x));
			if (!idHit && !nmHit) continue;
			const pk = `${p.year}-${p.q}`;
			const cur = m.get(pk);
			if (!cur || score(p, idHit) < score(cur, s.ids.includes(cur.id))) m.set(pk, p);
		}
		grid[s.key] = m;
	}
	return grid;
}
