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
import { readParquetWholeFile, type FetchLike } from '../parquet/hfRange';
import { buildGrid, FINANCE_COLUMNS, num, Q_BY_CODE, type Parsed, type RawRow } from './accounts';

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
	scope: 'CFS' | 'OFS'; // 연결 우선
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

function hasScope(rows: RawRow[], fs: string): boolean {
	for (const r of rows) {
		if ((r.fs_div || '') !== fs) continue;
		if (Q_BY_CODE[String(r.reprt_code || '')] && num(r.thstrm_amount) != null) return true;
	}
	return false;
}

// raw 행 → 연간 5개년 표준화 결과 (순수·테스트 가능, 네트워크 없음).
export function buildAnnualFromRows(code: string, rows: RawRow[], maxYears = 5): CompanyAnnualFinance | null {
	if (!rows || rows.length === 0) return null;
	const scope: 'CFS' | 'OFS' | null = hasScope(rows, 'CFS') ? 'CFS' : hasScope(rows, 'OFS') ? 'OFS' : null;
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
	const c = (code || '').trim();
	if (!/^\d{6}$/.test(c)) return null; // KR 상장사만 HF 정적 parquet 보유
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
