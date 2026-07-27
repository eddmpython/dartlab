// 블로그·정적 SEO 표면용 연간 5개년 IS/BS/CF · 데이터 SSOT(dart/finance/{code}.parquet)를
// Node+브라우저 공통 hyparquet 로 직독, financeSource(터미널)와 **동일한** 28 표준계정(accounts.ts)으로
// 표준화한다. 평행 재구현 추가 0.
//
// SvelteKit 블로그 라우트 +page.server.ts 가 prerender(빌드타임·Node)에 호출 → 정적 HTML 에 구워진다.
// 따라서 화석화가 구조적으로 불가능(매 빌드가 현재 매핑·현재 데이터로 재산출). 옛 sync_financials.py
// (커밋 시점 정적 bake) 대체.
//
// 윈도 정책: 연간(reprt_code 11011 = q4)만, 최신 maxYears 개 회계연도. 옛 bake 의 버그(최신 부분분기
// 2026Q1 혼입·"최근 5개년" 표에 분기 섞임)를 구조적으로 배제.
import { isKrStockCode, normalizeKrCode } from '@dartlab/ui-contracts';
import { readParquetWholeFile, type FetchLike } from '../parquet/hfRange';
import {
	buildGrid,
	FINANCE_COLUMNS,
	isStock,
	num,
	Q_BY_CODE,
	selectFreshestFinanceScope,
	type Parsed,
	type RawRow
} from './accounts';

export interface AnnualStmtRow {
	key: string;
	label: string;
	values: (number | null)[]; // 억원 (연도 축과 동일 순서)
}
// index signature · 블로그 ComboChart 의 DataPoint({year; [k]: string|number|null}) 와 호환.
export interface AnnualChartISPoint {
	year: string;
	매출액: number | null;
	영업이익: number | null;
	당기순이익: number | null;
	[key: string]: string | number | null;
}
export interface AnnualChartBSPoint {
	year: string;
	부채: number | null;
	자본: number | null;
	[key: string]: string | number | null;
}
export interface AnnualChartCFPoint {
	year: string;
	영업CF: number | null;
	투자CF: number | null;
	재무CF: number | null;
	[key: string]: string | number | null;
}
export interface CompanyAnnualFinance {
	code: string;
	scope: 'CFS' | 'OFS'; // 최신 공시 우선, 동률이면 연결
	years: string[]; // 최신 우선 · 예: ['2025','2024','2023','2022','2021']
	asOf: string | null; // 최신 회계연도 라벨 (데이터 기준 시점)
	is: AnnualStmtRow[];
	bs: AnnualStmtRow[];
	cf: AnnualStmtRow[];
	charts: { is: AnnualChartISPoint[]; bs: AnnualChartBSPoint[]; cf: AnnualChartCFPoint[] };
}

// 한 scope(연결/별도)의 행을 Parsed[] 로 · financeSource buildBundle 의 IS/CIS 채택 규약과 동일.
function parseScope(rows: RawRow[], fs: string): Parsed[] {
	const incomeSrc = rows.some((r) => (r.fs_div || '') === fs && r.sj_div === 'IS') ? 'IS' : 'CIS';
	const out: Parsed[] = [];
	for (const r of rows) {
		if ((r.fs_div || '') !== fs) continue;
		const q = Q_BY_CODE[String(r.reprt_code || '')];
		const year = Number(r.bsns_year);
		const amt = num(r.thstrm_amount);
		if (!q || !Number.isFinite(year) || amt == null) continue;
		const sjRaw = String(r.sj_div || '');
		const mk = (sj: string): Parsed => ({
			sj,
			year,
			q,
			id: String(r.account_id || ''),
			nm: String(r.account_nm || ''),
			detail: String(r.account_detail || ''),
			ord: num(r.ord) ?? Number.MAX_SAFE_INTEGER,
			amt
		});
		if (sjRaw === 'CIS') out.push(mk('CIS'));
		if (sjRaw === 'IS' || sjRaw === 'CIS') {
			if (sjRaw !== incomeSrc) continue;
			out.push(mk('IS'));
		} else out.push(mk(sjRaw)); // BS · CF · SCE
	}
	return out;
}

// raw 행 → 연간 5개년 표준화 결과 (순수·테스트 가능, 네트워크 없음).
export function buildAnnualFromRows(code: string, rows: RawRow[], maxYears = 5): CompanyAnnualFinance | null {
	if (!rows || rows.length === 0) return null;
	const scope = selectFreshestFinanceScope(rows, 4);
	if (!scope) return null;
	const parsed = parseScope(rows, scope);
	if (parsed.length === 0) return null;
	const grid = buildGrid(parsed);

	// 연간 = q4 (reprt_code 11011). 부분분기(q1~q3)는 표에 절대 섞지 않는다.
	const annual = (key: string, y: number): number | null => grid[key]?.get(`${y}-4`)?.amt ?? null;

	// 연간(q4) 데이터가 있는 회계연도 · 핵심 계정 기준 · 최신 maxYears 개.
	const yset = new Set<number>();
	for (const k of ['revenue', 'assets', 'cfOperating', 'netIncome', 'equity']) {
		for (const pk of grid[k]?.keys() ?? []) {
			const parts = pk.split('-');
			if (parts[1] === '4' && parts[0]) yset.add(Number(parts[0]));
		}
	}
	const yrs = [...yset].filter((y) => Number.isFinite(y)).sort((a, b) => b - a).slice(0, maxYears); // 최신 우선
	if (yrs.length === 0) return null;
	const years = yrs.map(String);

	const oku = (v: number | null): number | null => (v == null ? null : +(v / 1e8).toFixed(1)); // 원 → 억원
	const rowVals = (key: string): (number | null)[] => yrs.map((y) => oku(annual(key, y)));
	const deriveSub = (totalKey: string, partKey: string): (number | null)[] =>
		yrs.map((y) => {
			const t = annual(totalKey, y);
			const p = annual(partKey, y);
			return t != null && p != null ? oku(t - p) : null;
		});
	const grossProfitVals = (): (number | null)[] =>
		yrs.map((y) => {
			const direct = annual('grossProfit', y);
			if (direct != null) return oku(direct);
			const rev = annual('revenue', y);
			const cogs = annual('costOfSales', y);
			return rev != null && cogs != null ? oku(rev - cogs) : null;
		});
	const equityVals = (): (number | null)[] =>
		yrs.map((y) => {
			const e = annual('equity', y);
			if (e != null) return oku(e);
			const a = annual('assets', y);
			const l = annual('liabilities', y);
			return a != null && l != null ? oku(a - l) : null;
		});

	const is: AnnualStmtRow[] = [
		{ key: 'revenue', label: '매출액', values: rowVals('revenue') },
		{ key: 'costOfSales', label: '매출원가', values: rowVals('costOfSales') },
		{ key: 'grossProfit', label: '매출총이익', values: grossProfitVals() },
		{ key: 'operatingIncome', label: '영업이익', values: rowVals('operatingIncome') },
		{ key: 'financeIncome', label: '금융수익', values: rowVals('financeIncome') },
		{ key: 'financeCosts', label: '금융비용', values: rowVals('financeCosts') },
		{ key: 'netIncome', label: '당기순이익', values: rowVals('netIncome') }
	];
	const bs: AnnualStmtRow[] = [
		{ key: 'assets', label: '자산총계', values: rowVals('assets') },
		{ key: 'currentAssets', label: '유동자산', values: rowVals('currentAssets') },
		{ key: 'nonCurrentAssets', label: '비유동자산', values: deriveSub('assets', 'currentAssets') },
		{ key: 'liabilities', label: '부채총계', values: rowVals('liabilities') },
		{ key: 'currentLiabilities', label: '유동부채', values: rowVals('currentLiabilities') },
		{ key: 'nonCurrentLiabilities', label: '비유동부채', values: deriveSub('liabilities', 'currentLiabilities') },
		{ key: 'equity', label: '자본총계', values: equityVals() }
	];
	const cf: AnnualStmtRow[] = [
		{ key: 'cfOperating', label: '영업활동현금흐름', values: rowVals('cfOperating') },
		{ key: 'cfInvesting', label: '투자활동현금흐름', values: rowVals('cfInvesting') },
		{ key: 'cfFinancing', label: '재무활동현금흐름', values: rowVals('cfFinancing') }
	];

	if (![...is, ...bs, ...cf].some((r) => r.values.some((v) => v != null))) return null;

	const at = (arr: AnnualStmtRow[], key: string, i: number): number | null => arr.find((r) => r.key === key)?.values[i] ?? null;
	const charts = {
		is: years.map((y, i) => ({ year: y, 매출액: at(is, 'revenue', i), 영업이익: at(is, 'operatingIncome', i), 당기순이익: at(is, 'netIncome', i) })),
		bs: years.map((y, i) => ({ year: y, 부채: at(bs, 'liabilities', i), 자본: at(bs, 'equity', i) })),
		cf: years.map((y, i) => ({ year: y, 영업CF: at(cf, 'cfOperating', i), 투자CF: at(cf, 'cfInvesting', i), 재무CF: at(cf, 'cfFinancing', i) }))
	};

	return { code, scope, years, asOf: years[0] ?? null, is, bs, cf, charts };
}

// dart/finance/{code}.parquet(데이터 SSOT) 직독 → 연간 표준화. KR 6자리 코드 전용(EDGAR=Phase 2).
// 미존재/실패 = null(정직 폴백 · 컴포넌트가 부재 표기). 빌드타임·브라우저 공통(hyparquet).
export async function loadAnnualStatements(
	code: string,
	opts: { maxYears?: number; fetchFn?: FetchLike } = {}
): Promise<CompanyAnnualFinance | null> {
	const c = normalizeKrCode(code || '');
	if (!isKrStockCode(c)) return null; // KR 상장사만 HF 정적 parquet 보유(영숫자 코드 0008Z0 포함)
	let rows: RawRow[] | null = null;
	try {
		rows = await readParquetWholeFile<RawRow>(`dart/finance/${c}.parquet`, { columns: FINANCE_COLUMNS, fetchFn: opts.fetchFn });
	} catch (e) {
		console.warn('[blog/annual] finance parquet load failed', c, e);
		return null;
	}
	if (!rows || rows.length === 0) return null;
	return buildAnnualFromRows(c, rows, opts.maxYears ?? 5);
}

// ── 분기 뷰(라이브 테이블 = 무조건 분기 기준) ──
// 블로그 회사글의 라이브 재무 테이블은 최신성을 위해 분기 단위로 노출한다(연간 5개년은 아래 궤적 컨텍스트).
// flow(IS·CF)는 DART 분기 규약(YTD 누적/standalone 혼재)을 자동판정해 단일분기로 환산 · financeSource
// buildBundle 의 `standalone` 과 **동일 로직**(터미널 분기 뷰 SSOT 미러, 평행 재구현 아님). BS 는 시점 스냅샷.
export interface QuarterlyStmtRow {
	key: string;
	label: string;
	values: (number | null)[]; // 억원 · periods 축과 동순서(오래된→최신)
}
export interface QuarterlyChartISPoint {
	year: string; // 분기 라벨(ComboChart x축 재사용) · 예 '25Q1'
	매출액: number | null;
	영업이익: number | null;
	당기순이익: number | null;
	[key: string]: string | number | null;
}
export interface CompanyQuarterlyFinance {
	code: string;
	scope: 'CFS' | 'OFS';
	periods: string[]; // 오래된→최신 · 예 ['24Q1','24Q2',...,'25Q4']
	asOf: string | null; // 최신 분기 라벨
	is: QuarterlyStmtRow[];
	bs: QuarterlyStmtRow[];
	cf: QuarterlyStmtRow[];
	charts: { is: QuarterlyChartISPoint[] };
}

// flow 단일분기 환산 · financeSource `standalone` 과 라인 대 라인 동일(검증된 SSOT 미러).
function quarterStandalone(grid: Record<string, Map<string, Parsed>>, key: string, y: number, q: number): number | null {
	const rawV = (k: string, yy: number, qq: number): number | null => grid[k]?.get(`${yy}-${qq}`)?.amt ?? null;
	const q1 = rawV(key, y, 1),
		q2 = rawV(key, y, 2),
		q3 = rawV(key, y, 3),
		a = rawV(key, y, 4);
	const allInterim = q1 != null && q2 != null && q3 != null;
	const ytd = allInterim && a != null && q1! + q2! + q3! > a! * 1.05;
	if (q === 1) return q1; // Q1 누적 = Q1 단일분기
	if (q === 4) {
		if (a == null) return null;
		if (ytd) return q3 != null ? a - q3 : null;
		if (allInterim) return a - (q1! + q2! + q3!);
		return a; // annual-only 연도(분기 미제출) → 연간값 그대로
	}
	const cur = rawV(key, y, q);
	if (cur == null) return null;
	if (ytd) {
		const prev = rawV(key, y, q - 1);
		return prev != null ? cur - prev : cur;
	}
	return cur;
}

// raw 행 → 분기 뷰(순수·네트워크 없음). maxQuarters 개 최신 분기.
export function buildQuarterlyFromRows(code: string, rows: RawRow[], maxQuarters = 8): CompanyQuarterlyFinance | null {
	if (!rows || rows.length === 0) return null;
	const scope = selectFreshestFinanceScope(rows);
	if (!scope) return null;
	const parsed = parseScope(rows, scope);
	if (parsed.length === 0) return null;
	const grid = buildGrid(parsed);

	// 사용 가능한 (year,q) · 매출 또는 자산 존재 기준 · 오래된→최신 정렬 후 최신 maxQuarters 개.
	const pkSet = new Set<string>();
	for (const key of ['revenue', 'assets', 'cfOperating', 'netIncome']) {
		for (const pk of grid[key]?.keys() ?? []) pkSet.add(pk);
	}
	const allPk = [...pkSet]
		.map((pk) => {
			const parts = pk.split('-').map(Number);
			return { y: parts[0] ?? 0, q: parts[1] ?? 0 };
		})
		.filter((p) => Number.isFinite(p.y) && p.q >= 1 && p.q <= 4)
		.sort((a, b) => a.y - b.y || a.q - b.q);
	// 분기(Q1~Q3) 제출이 없으면(연간만 있는 회사) 분기 뷰를 만들지 않는다 · 연간값을 Q4 로 오표기 방지.
	// financeSource `views.quarter = hasInterim ? ... : null` 미러. 연간 궤적 섹션이 대신 커버.
	if (!allPk.some((p) => p.q !== 4)) return null;
	const used = allPk.slice(-maxQuarters);
	if (used.length === 0) return null;
	const periods = used.map((p) => `${String(p.y).slice(2)}Q${p.q}`);

	const oku = (v: number | null): number | null => (v == null ? null : +(v / 1e8).toFixed(1));
	const rawSnap = (key: string, y: number, q: number): number | null => grid[key]?.get(`${y}-${q}`)?.amt ?? null;
	// 값: BS = 시점 스냅샷, flow(IS·CF) = 단일분기 환산.
	const rowVals = (key: string): (number | null)[] => used.map((p) => oku(isStock(key) ? rawSnap(key, p.y, p.q) : quarterStandalone(grid, key, p.y, p.q)));

	const is: QuarterlyStmtRow[] = [
		{ key: 'revenue', label: '매출액', values: rowVals('revenue') },
		{ key: 'operatingIncome', label: '영업이익', values: rowVals('operatingIncome') },
		{ key: 'netIncome', label: '당기순이익', values: rowVals('netIncome') }
	];
	const bs: QuarterlyStmtRow[] = [
		{ key: 'assets', label: '자산총계', values: rowVals('assets') },
		{ key: 'liabilities', label: '부채총계', values: rowVals('liabilities') },
		{ key: 'equity', label: '자본총계', values: rowVals('equity') }
	];
	const cf: QuarterlyStmtRow[] = [
		{ key: 'cfOperating', label: '영업활동현금흐름', values: rowVals('cfOperating') },
		{ key: 'cfInvesting', label: '투자활동현금흐름', values: rowVals('cfInvesting') },
		{ key: 'cfFinancing', label: '재무활동현금흐름', values: rowVals('cfFinancing') }
	];
	if (![...is, ...bs, ...cf].some((r) => r.values.some((v) => v != null))) return null;

	const at = (arr: QuarterlyStmtRow[], key: string, i: number): number | null => arr.find((r) => r.key === key)?.values[i] ?? null;
	const charts = {
		is: periods.map((label, i) => ({ year: label, 매출액: at(is, 'revenue', i), 영업이익: at(is, 'operatingIncome', i), 당기순이익: at(is, 'netIncome', i) }))
	};

	return { code, scope, periods, asOf: periods[periods.length - 1] ?? null, is, bs, cf, charts };
}

// dart/finance/{code}.parquet 직독 → 분기 표준화. KR 6자리 전용 · 미존재/실패 = null.
export async function loadQuarterlyStatements(
	code: string,
	opts: { maxQuarters?: number; fetchFn?: FetchLike } = {}
): Promise<CompanyQuarterlyFinance | null> {
	const c = normalizeKrCode(code || '');
	if (!isKrStockCode(c)) return null;
	let rows: RawRow[] | null = null;
	try {
		rows = await readParquetWholeFile<RawRow>(`dart/finance/${c}.parquet`, { columns: FINANCE_COLUMNS, fetchFn: opts.fetchFn });
	} catch (e) {
		console.warn('[blog/quarterly] finance parquet load failed', c, e);
		return null;
	}
	if (!rows || rows.length === 0) return null;
	return buildQuarterlyFromRows(c, rows, opts.maxQuarters ?? 8);
}

// 연간 + 분기 동시 산출 · parquet 1회만 읽어(중복 다운로드/파싱 0) 두 뷰를 만든다. 블로그 라우트 진입점.
export interface CompanyFinance {
	annual: CompanyAnnualFinance | null;
	quarterly: CompanyQuarterlyFinance | null;
}
export async function loadCompanyFinance(
	code: string,
	opts: { maxYears?: number; maxQuarters?: number; fetchFn?: FetchLike } = {}
): Promise<CompanyFinance> {
	const c = normalizeKrCode(code || '');
	if (!isKrStockCode(c)) return { annual: null, quarterly: null };
	let rows: RawRow[] | null = null;
	try {
		rows = await readParquetWholeFile<RawRow>(`dart/finance/${c}.parquet`, { columns: FINANCE_COLUMNS, fetchFn: opts.fetchFn });
	} catch (e) {
		console.warn('[blog/finance] finance parquet load failed', c, e);
		return { annual: null, quarterly: null };
	}
	if (!rows || rows.length === 0) return { annual: null, quarterly: null };
	return {
		annual: buildAnnualFromRows(c, rows, opts.maxYears ?? 5),
		quarterly: buildQuarterlyFromRows(c, rows, opts.maxQuarters ?? 8)
	};
}
