import { loadDartDb } from '$lib/data/duckdb';
import { createDataCore, type DataCore } from '@dartlab/ui-runtime/data/fetch/request';
import { loadHfJson, loadJson } from '@dartlab/ui-runtime/data/dartlabData';
import { loadHfValuationFor, type ValuationRuntimeMetrics } from '$lib/data/valuationRuntime';
import { loadCompanyChanges, type CompanyChange } from '@dartlab/ui-surfaces/scan';
import { BrowserCompany } from './company';
import type { BrowserTable, BrowserText } from './types';
import { toDividendFact, toTreasuryFact, toExecutiveFact, toAuditFact, toMajorHolderFact, toCorporateBondFact } from './reportFacts';

export type StatementKey = 'IS' | 'BS' | 'CF';
export type StatementFreq = 'Y' | 'Q';

export interface LiveStatementSlot {
	annual: BrowserTable | null;
	quarterly: BrowserTable | null;
	status: 'ready' | 'fallback' | 'missing';
	source: string;
}

export interface LiveCompanySummary {
	revenue: number | null;
	op: number | null;
	net: number | null;
	opMargin: number | null;
	roe: number | null;
	debtRatio: number | null;
	year: string | null;
}

export interface LiveCompanyPrice {
	currentPrice: number | null;
	marketCap: number | null;
	per: number | null;
	pbr: number | null;
	dividendYield: number | null;
	snapshotAt: string | null;
	return1m: number | null;
	return3m: number | null;
	return1y: number | null;
	volatility1y: number | null;
}

export interface LiveCompanyChange {
	fromPeriod: string;
	toPeriod: string;
	sectionTitle: string;
	changeType: string;
	preview: string | null;
}

export interface LiveCompanyDiagnosis {
	key: 'growth' | 'profitability' | 'structure';
	label: string;
	value: string;
	tone: 'good' | 'bad' | 'neutral';
	source: string;
}

export interface LiveCompanySourceStatus {
	key: 'finance' | 'report' | 'docs' | 'map' | 'price';
	label: string;
	status: 'ready' | 'fallback' | 'missing' | 'lazy';
	source: string;
}

export interface LiveCompanyReportFact {
	key: 'dividend' | 'treasuryStock' | 'executive' | 'auditOpinion' | 'majorHolder' | 'corporateBond';
	label: string;
	value: string;
	detail: string;
	source: string;
	// 도시에 스파인 · 출처 공시 접수번호(↗원문) + 결산 기준일(as-of). contracts 와 동기(additive optional).
	rceptNo?: string | null;
	stlmDt?: string | null;
}

export interface LiveCompanyDocExcerpt {
	title: string;
	year: string | null;
	reportType: string | null;
	excerpt: string;
	rceptNo: string | null;
	source: string;
}

export type StatementDashboardTopic = 'IS' | 'BS' | 'CF';
export type StatementChartKind = 'bar' | 'line' | 'stack';

export interface StatementMetric {
	key: string;
	label: string;
	value: number | null;
	display: string;
	unit: string;
	period: string | null;
	delta: number | null;
	tone: 'good' | 'bad' | 'neutral';
	formula: string;
	source: string;
}

export interface StatementChartSeries {
	key: string;
	label: string;
	unit: string;
	values: Array<number | null>;
}

export interface StatementChart {
	key: string;
	title: string;
	kind: StatementChartKind;
	periods: string[];
	series: StatementChartSeries[];
}

export interface StatementGroupRow {
	key: string;
	label: string;
	unit: string;
	values: Array<number | string | null>;
	yoy: number | null;
	source: string;
	raw: BrowserTable['rows'][number];
}

export interface StatementGroup {
	key: string;
	label: string;
	rows: StatementGroupRow[];
}

export interface StatementDashboard {
	topic: StatementDashboardTopic;
	title: string;
	subtitle: string;
	periods: string[];
	metrics: StatementMetric[];
	charts: StatementChart[];
	groups: StatementGroup[];
	rawTable: BrowserTable | null;
	quality: {
		sourceLabel: string;
		missingAccounts: string[];
	};
}

export interface LiveCompanyEvidence {
	accountLabel: string;
	accountKey: string;
	values: Array<{ period: string; value: number | string | null; unit: string }>;
	facts: LiveCompanyReportFact[];
	docs: LiveCompanyDocExcerpt[];
	changes: LiveCompanyChange[];
}

export interface LiveCompanyBundle {
	stockCode: string;
	companyMeta: any;
	industryMeta: any;
	meta: any;
	price: LiveCompanyPrice | null;
	summary: LiveCompanySummary | null;
	statements: {
		IS: LiveStatementSlot;
		BS: LiveStatementSlot;
		CF: LiveStatementSlot;
	};
	overview: BrowserText;
	changes: LiveCompanyChange[];
	diagnosis: LiveCompanyDiagnosis[];
	sourceStatus: LiveCompanySourceStatus[];
	source: string;
}

interface PriceSnapshotFile {
	builtAt?: string;
	data?: Record<string, PriceSnapshotItem>;
}

interface PriceSnapshotItem {
	currentPrice?: number | null;
	marketCap?: number | null;
	return1m?: number | null;
	return3m?: number | null;
	return1y?: number | null;
	volatility1y?: number | null;
	priceUpdated?: string | null;
}

interface FinancialYear {
	year?: string | number;
	sales?: number | null;
	operating_profit?: number | null;
	net_profit?: number | null;
	total_assets?: number | null;
}

export async function loadLiveCompany(stockCode: string): Promise<LiveCompanyBundle> {
	const valuationPromise = loadHfValuationFor(stockCode, fetch).catch(() => null);
	const [companyMeta, meta, priceSnapshot] = await Promise.all([
		loadJson<any>(`map/companies/${stockCode}.json`, {
			fetchFn: fetch,
			required: true,
			preferLocal: true
		}),
		loadJson<any>('map/meta.json', { fetchFn: fetch, preferLocal: true }),
		// 시세 스냅샷만 HF-first · 일배치 HF 갱신을 정적 사본이 가리는 동결 방지 (terminal routeLoad 동일)
		loadJson<PriceSnapshotFile>('map/prices-snapshot.json', { fetchFn: fetch })
	]);
	const valuation = await withTimeout(valuationPromise, 1200, null);

	const industryId = companyMeta?.ego?.industry ?? null;
	const industryMeta = industryId
		? await loadJson<any>(`map/industries/${industryId}.json`, { fetchFn: fetch, preferLocal: true })
		: null;

	const financials = normalizeFinancials(companyMeta?.financials5y);
	const statements = {
		IS: buildStatementSlot(null, null, buildIncomeStatement(stockCode, financials)),
		BS: buildStatementSlot(null, null, buildBalanceSheet(stockCode, financials)),
		CF: buildStatementSlot(null, null, null)
	};
	const summary = buildSummary(financials, statements);
	const price = buildPrice(stockCode, priceSnapshot, valuation);

	return {
		stockCode,
		companyMeta,
		industryMeta,
		meta,
		price,
		summary,
		statements,
		overview: buildOverview(stockCode, companyMeta, industryMeta),
		changes: [],
		diagnosis: buildDiagnosis(summary, statements),
		sourceStatus: buildSourceStatus(statements, [], companyMeta, meta, price),
		source: 'landing/static/map'
	};
}

function withTimeout<T>(promise: Promise<T>, ms: number, fallback: T): Promise<T> {
	return new Promise((resolve) => {
		const timer = window.setTimeout(() => resolve(fallback), ms);
		promise.then(
			(value) => {
				window.clearTimeout(timer);
				resolve(value);
			},
			() => {
				window.clearTimeout(timer);
				resolve(fallback);
			}
		);
	});
}

export async function loadLiveCompanyStatement(
	stockCode: string,
	topic: StatementKey,
	freq: StatementFreq
): Promise<BrowserTable | null> {
	return await loadStatement(new BrowserCompany(stockCode, { fetchFn: fetch }), topic, freq);
}

export async function loadLiveCompanyChanges(stockCode: string, limit = 8): Promise<CompanyChange[]> {
	return await loadChangesForCompany(stockCode, limit);
}

// 정기보고서 팩트 · hyparquet 직독(reportSource 와 동일 빠른 경로, 60분 read 캐시).
// ⛔ DuckDB-WASM 경유 폐기: 단일 워커 직렬 큐에 6개 전시장 parquet 등록+스캔이 묶여 첫 표시가
//   수십 초로 멈추던 회귀(인력·주주환원 패널은 이미 hyparquet 이관, 본 패널만 잔류했었다).
//   origin='hfRange' 는 표기용 · URL 은 hfRangeUrl 이 자동 해석(HF_RESOLVE). core 미주입이라 모듈 1회 생성.
const REPORT_FACTS_TTL = 3_600_000;
let _reportFactsCore: DataCore | null = null;
function reportFactsCore(): DataCore {
	return (_reportFactsCore ??= createDataCore());
}

// 4자리 달력연도만 인식 · auditOpinion 등은 year 가 '제58기 1분기' 기수 라벨이라
// 단순 숫자추출(→581)은 오정렬. 기수만 있으면 -1 로 후순위(DuckDB NULLS LAST 대체).
const factYear = (r: any): number => {
	const m = String(r?.year ?? '').match(/(?:19|20)\d{2}/);
	return m ? Number(m[0]) : -1;
};

// 최신 연도 우선 정렬(DuckDB ORDER BY TRY_CAST(year) DESC 대체). stockCode 컬럼 필요(filter 기준).
async function readReportFactRows(path: string, code: string, columns: string[]): Promise<any[]> {
	const rows = await reportFactsCore().requestParquetRows<Record<string, unknown>>({
		origin: 'hfRange',
		path: `dart/scan/report/${path}.parquet`,
		columns: ['stockCode', 'year', ...columns],
		filter: { stockCode: { $eq: code } },
		cacheKey: `reportFacts.${path}:${code}`,
		cache: { scope: 'memory', ttlMs: REPORT_FACTS_TTL, maxEntries: 256 }
	});
	return rows.slice().sort((a, b) => factYear(b) - factYear(a));
}

export async function loadLiveCompanyReportFacts(stockCode: string): Promise<LiveCompanyReportFact[]> {
	try {
		const [dividend, treasury, executive, audit, holder, bond] = await Promise.all([
			readReportFactRows('dividend', stockCode, ['rcept_no', 'stlm_dt', 'se', 'thstrm', 'frmtrm', 'lwfr']),
			readReportFactRows('treasuryStock', stockCode, ['rcept_no', 'stlm_dt', 'stock_knd', 'trmend_qy', 'change_qy_acqs', 'change_qy_dsps']),
			readReportFactRows('executive', stockCode, ['rcept_no', 'stlm_dt', 'nm', 'ofcps', 'chrg_job']),
			readReportFactRows('auditOpinion', stockCode, ['rcept_no', 'stlm_dt', 'adtor', 'adt_opinion', 'emphs_matter', 'core_adt_matter']),
			readReportFactRows('majorHolder', stockCode, ['rcept_no', 'stlm_dt', 'mxmm_shrholdr_nm', 'posesn_stock_co', 'qota_rt', 'change_cause']),
			readReportFactRows('corporateBond', stockCode, ['rcept_no', 'stlm_dt', 'scrits_knd_nm', 'isu_de', 'facvalu_totamt', 'intrt', 'evl_grad_instt'])
		]);
		// 임원: 최신 연도의 이름 있는 행 최대 3 (DuckDB nm IS NOT NULL ... LIMIT 3 대체).
		const execTopYear = executive.length ? factYear(executive[0]) : -1;
		const execRows = executive.filter((r) => factYear(r) === execTopYear && r.nm != null).slice(0, 3);
		return [
			toDividendFact(dividend[0]),
			toTreasuryFact(treasury[0]),
			toExecutiveFact(execRows),
			toAuditFact(audit[0]),
			toMajorHolderFact(holder[0]),
			toCorporateBondFact(bond[0])
		].filter((x): x is LiveCompanyReportFact => x != null);
	} catch (err) {
		console.warn(`[dartlab-browser] report facts fallback: ${stockCode}`, err);
		return [];
	}
}

export async function loadLiveCompanyPanelExcerpts(stockCode: string, limit = 8): Promise<LiveCompanyDocExcerpt[]> {
	try {
		const db = await loadDartDb();
		if (!db) return [];
		await db.registerHfParquet('companyPanel', `dart/panel/${stockCode}.parquet`);
		const rows = await db.query<any>(`
			SELECT
				"period",
				COALESCE(NULLIF("sectionLeaf", ''), NULLIF("blockLeaf", ''), NULLIF("chapter", ''), 'panel 원문') AS title,
				"rceptNo",
				SUBSTR(
					REGEXP_REPLACE(REGEXP_REPLACE("contentRaw", '<[^>]+>', ' ', 'g'), '\\s+', ' ', 'g'),
					1,
					360
				) AS excerpt
			FROM companyPanel
			WHERE "contentRaw" IS NOT NULL
			  AND LENGTH("contentRaw") > 80
			  AND (
				"sectionLeaf" LIKE '%사업%'
				OR "sectionLeaf" LIKE '%제품%'
				OR "sectionLeaf" LIKE '%매출%'
				OR "sectionLeaf" LIKE '%위험%'
				OR "sectionLeaf" LIKE '%재무%'
				OR "sectionLeaf" LIKE '%주석%'
				OR "sectionLeaf" LIKE '%감사%'
				OR "blockLeaf" LIKE '%사업%'
				OR "blockLeaf" LIKE '%제품%'
				OR "blockLeaf" LIKE '%매출%'
				OR "blockLeaf" LIKE '%위험%'
				OR "blockLeaf" LIKE '%재무%'
				OR "blockLeaf" LIKE '%주석%'
				OR "blockLeaf" LIKE '%감사%'
			  )
			ORDER BY "period" DESC NULLS LAST, "blockOrder" ASC
			LIMIT ${Math.max(1, Math.min(20, limit))}
		`);
		return rows.map((row) => ({
			title: row.title ?? 'panel 원문',
			year: periodYear(row.period),
			reportType: periodReportType(row.period),
			excerpt: row.excerpt ?? '',
			rceptNo: row.rceptNo ?? null,
			source: `dart/panel/${stockCode}.parquet`
		}));
	} catch (err) {
		console.warn(`[dartlab-browser] panel excerpt fallback: ${stockCode}`, err);
		return [];
	}
}

export function buildStatementDashboard(
	topic: StatementDashboardTopic,
	table: BrowserTable | null
): StatementDashboard {
	const spec = STATEMENT_SPECS[topic];
	const periods = table?.columns ?? [];
	const groups = spec.groups.map((group) => ({
		key: group.key,
		label: group.label,
		rows: group.accounts
			.map((account) => toGroupRow(table, account))
			.filter((row): row is StatementGroupRow => row != null)
	}));
	const missingAccounts = spec.required
		.filter((account) => !findAccountRow(table, account.match))
		.map((account) => account.label);

	return {
		topic,
		title: spec.title,
		subtitle: spec.subtitle,
		periods,
		metrics: spec.metrics.map((metric) => buildMetric(table, metric)),
		charts: spec.charts.map((chart) => buildChart(table, chart)),
		groups,
		rawTable: table,
		quality: {
			sourceLabel: sourceLabel(table?.source),
			missingAccounts
		}
	};
}

export function buildEvidenceForAccount(
	account: StatementGroupRow | null,
	periods: string[],
	facts: LiveCompanyReportFact[],
	docs: LiveCompanyDocExcerpt[],
	changes: LiveCompanyChange[]
): LiveCompanyEvidence | null {
	if (!account) return null;
	const labels = evidenceLabels(account.label, account.key);
	return {
		accountLabel: account.label,
		accountKey: account.key,
		values: periods.map((period, i) => ({
			period,
			value: account.values[i] ?? null,
			unit: account.unit
		})),
		facts: facts.filter((fact) => labels.facts.some((key) => fact.key === key || fact.label.includes(key))),
		docs: docs.filter((doc) =>
			labels.docs.some((key) => `${doc.title} ${doc.excerpt}`.toLowerCase().includes(key.toLowerCase()))
		),
		changes: changes.filter((change) =>
			labels.docs.some((key) => `${change.sectionTitle} ${change.preview ?? ''}`.toLowerCase().includes(key.toLowerCase()))
		)
	};
}

interface AccountSpec {
	key: string;
	label: string;
	unit: string;
	match: string[];
}

interface MetricSpec extends AccountSpec {
	formula: string;
	kind?: 'amount' | 'pct' | 'ratio';
	calc?: (table: BrowserTable | null) => number | null;
}

interface ChartSpec {
	key: string;
	title: string;
	kind: StatementChartKind;
	series: AccountSpec[];
}

interface StatementSpec {
	title: string;
	subtitle: string;
	required: AccountSpec[];
	metrics: MetricSpec[];
	charts: ChartSpec[];
	groups: Array<{ key: string; label: string; accounts: AccountSpec[] }>;
}

const ACCOUNTS = {
	revenue: { key: 'revenue', label: '매출액', unit: 'KRW', match: ['ifrs-full_Revenue', 'Revenue', 'sales', '매출액'] },
	grossProfit: { key: 'grossProfit', label: '매출총이익', unit: 'KRW', match: ['GrossProfit', '매출총이익'] },
	sga: { key: 'sga', label: '판매비와관리비', unit: 'KRW', match: ['SellingGeneralAdministrative', '판매비와관리비', '판관비'] },
	op: { key: 'op', label: '영업이익', unit: 'KRW', match: ['dart_OperatingIncomeLoss', 'OperatingIncomeLoss', 'operating_profit', '영업이익'] },
	financeIncome: { key: 'financeIncome', label: '금융수익', unit: 'KRW', match: ['FinanceIncome', '금융수익'] },
	financeCost: { key: 'financeCost', label: '금융비용', unit: 'KRW', match: ['FinanceCosts', '금융비용'] },
	tax: { key: 'tax', label: '법인세비용', unit: 'KRW', match: ['IncomeTaxExpense', '법인세'] },
	net: { key: 'net', label: '순이익', unit: 'KRW', match: ['ifrs-full_ProfitLoss', 'ProfitLoss', 'net_profit', '당기순이익', '순이익'] },
	cash: { key: 'cash', label: '현금및현금성자산', unit: 'KRW', match: ['CashAndCashEquivalents', 'cash', '현금및현금성자산', '현금성자산'] },
	receivables: { key: 'receivables', label: '매출채권', unit: 'KRW', match: ['TradeAndOtherCurrentReceivables', 'receivables', '매출채권'] },
	inventory: { key: 'inventory', label: '재고자산', unit: 'KRW', match: ['Inventories', 'inventory', '재고자산'] },
	tangible: { key: 'tangible', label: '유형자산', unit: 'KRW', match: ['PropertyPlantAndEquipment', 'tangible', '유형자산'] },
	intangible: { key: 'intangible', label: '무형자산', unit: 'KRW', match: ['IntangibleAssets', 'intangible', '무형자산'] },
	assets: { key: 'assets', label: '총자산', unit: 'KRW', match: ['ifrs-full_Assets', 'Assets', 'total_assets', 'totalAsset', '자산총계', '총자산'] },
	tradePayables: { key: 'tradePayables', label: '매입채무/영업부채', unit: 'KRW', match: ['TradeAndOtherCurrentPayables', 'TradePayables', 'trade_payables', '매입채무', '매입채무및기타채무', '영업부채'] },
	borrowings: { key: 'borrowings', label: '차입금', unit: 'KRW', match: ['Borrowings', 'ShorttermBorrowings', 'LongtermBorrowings', '차입금'] },
	bonds: { key: 'bonds', label: '사채', unit: 'KRW', match: ['BondsIssued', 'Debentures', '사채'] },
	liabilities: { key: 'liabilities', label: '총부채', unit: 'KRW', match: ['ifrs-full_Liabilities', 'Liabilities', 'totalLiab', '부채총계', '총부채'] },
	capitalStock: { key: 'capitalStock', label: '자본금', unit: 'KRW', match: ['IssuedCapital', 'CapitalStock', '자본금'] },
	capitalSurplus: { key: 'capitalSurplus', label: '자본잉여금', unit: 'KRW', match: ['SharePremium', 'CapitalSurplus', '자본잉여금'] },
	retainedEarnings: { key: 'retainedEarnings', label: '이익잉여금', unit: 'KRW', match: ['RetainedEarnings', 'retained_earnings', '이익잉여금', '결손금'] },
	treasuryStock: { key: 'treasuryStock', label: '자기주식', unit: 'KRW', match: ['TreasuryShares', 'treasuryStock', '자기주식'] },
	otherEquity: { key: 'otherEquity', label: '기타자본', unit: 'KRW', match: ['OtherComponentsOfEquity', 'other_equity', '기타자본', '기타포괄손익누계액'] },
	equity: { key: 'equity', label: '총자본', unit: 'KRW', match: ['ifrs-full_Equity', 'Equity', 'totalEquity', '자본총계', '총자본'] },
	ocf: { key: 'ocf', label: '영업활동현금흐름', unit: 'KRW', match: ['CashFlowsFromUsedInOperatingActivities', '영업활동현금흐름', '영업CF', 'op'] },
	icf: { key: 'icf', label: '투자활동현금흐름', unit: 'KRW', match: ['CashFlowsFromUsedInInvestingActivities', '투자활동현금흐름', '투자CF', 'inv'] },
	capex: { key: 'capex', label: 'CAPEX', unit: 'KRW', match: ['PurchaseOfPropertyPlantAndEquipment', '유형자산의취득', 'CAPEX'] },
	fcf: { key: 'fcf', label: 'FCF', unit: 'KRW', match: ['FreeCashFlow', 'FCF'] },
	financingCf: { key: 'financingCf', label: '재무활동현금흐름', unit: 'KRW', match: ['CashFlowsFromUsedInFinancingActivities', '재무활동현금흐름', '재무CF', 'fin'] },
	dividendPaid: { key: 'dividendPaid', label: '배당 지급', unit: 'KRW', match: ['DividendsPaid', '배당금의지급', '배당'] },
	closingCash: { key: 'closingCash', label: '기말현금', unit: 'KRW', match: ['CashAndCashEquivalentsAtEndOfPeriod', '기말현금', 'closing'] }
} satisfies Record<string, AccountSpec>;

const STATEMENT_SPECS: Record<StatementDashboardTopic, StatementSpec> = {
	IS: {
		title: '손익계산서',
		subtitle: '매출에서 이익까지 성장, 마진, 비용 압력을 한 번에 본다.',
		required: [ACCOUNTS.revenue, ACCOUNTS.op, ACCOUNTS.net],
		metrics: [
			{ ...ACCOUNTS.revenue, formula: '재무제표 매출액' },
			{ ...ACCOUNTS.revenue, key: 'revenueYoy', label: '매출 YoY', unit: '%', kind: 'pct', formula: '(최근 매출 / 전기 매출 - 1) * 100', calc: (table) => yoy(readSeries(table, ACCOUNTS.revenue.match)) },
			{ ...ACCOUNTS.op, formula: '재무제표 영업이익' },
			{ ...ACCOUNTS.op, key: 'opMargin', label: '영업이익률', unit: '%', kind: 'pct', formula: '영업이익 / 매출액', calc: (table) => ratioLatest(table, ACCOUNTS.op.match, ACCOUNTS.revenue.match) },
			{ ...ACCOUNTS.net, formula: '재무제표 순이익' },
			{ ...ACCOUNTS.net, key: 'netMargin', label: '순이익률', unit: '%', kind: 'pct', formula: '순이익 / 매출액', calc: (table) => ratioLatest(table, ACCOUNTS.net.match, ACCOUNTS.revenue.match) }
		],
		charts: [
			{ key: 'is-profit', title: '매출 · 영업이익 · 순이익', kind: 'bar', series: [ACCOUNTS.revenue, ACCOUNTS.op, ACCOUNTS.net] },
			{ key: 'is-margin', title: '영업이익률 · 순이익률', kind: 'line', series: [
				{ key: 'opMargin', label: '영업이익률', unit: '%', match: [] },
				{ key: 'netMargin', label: '순이익률', unit: '%', match: [] }
			] }
		],
		groups: [
			{ key: 'revenue', label: '수익', accounts: [ACCOUNTS.revenue, ACCOUNTS.grossProfit] },
			{ key: 'cost', label: '비용', accounts: [ACCOUNTS.sga, ACCOUNTS.financeCost, ACCOUNTS.tax] },
			{ key: 'profit', label: '이익', accounts: [ACCOUNTS.op, ACCOUNTS.financeIncome, ACCOUNTS.net] }
		]
	},
	BS: {
		title: '재무상태표',
		subtitle: '자산, 부채, 자본의 균형과 위험을 계정군별로 본다.',
		required: [ACCOUNTS.assets, ACCOUNTS.liabilities, ACCOUNTS.equity],
		metrics: [
			{ ...ACCOUNTS.assets, formula: '재무제표 총자산' },
			{ ...ACCOUNTS.cash, formula: '재무제표 현금및현금성자산' },
			{ ...ACCOUNTS.liabilities, formula: '재무제표 총부채' },
			{ ...ACCOUNTS.equity, formula: '재무제표 총자본' },
			{ ...ACCOUNTS.liabilities, key: 'debtRatio', label: '부채비율', unit: '%', kind: 'pct', formula: '부채총계 / 자본총계', calc: (table) => ratioLatest(table, ACCOUNTS.liabilities.match, ACCOUNTS.equity.match) },
			{ ...ACCOUNTS.equity, key: 'roeProxy', label: 'ROE', unit: '%', kind: 'pct', formula: '순이익 / 자본총계', calc: () => null }
		],
		charts: [
			{ key: 'bs-assets', title: '자산 구성', kind: 'stack', series: [ACCOUNTS.cash, ACCOUNTS.receivables, ACCOUNTS.inventory, ACCOUNTS.tangible, ACCOUNTS.intangible] },
			{ key: 'bs-capital', title: '부채 · 자본', kind: 'bar', series: [ACCOUNTS.liabilities, ACCOUNTS.equity] }
		],
		groups: [
			{ key: 'assets', label: '자산', accounts: [ACCOUNTS.cash, ACCOUNTS.receivables, ACCOUNTS.inventory, ACCOUNTS.tangible, ACCOUNTS.intangible, ACCOUNTS.assets] },
			{ key: 'liabilities', label: '부채', accounts: [ACCOUNTS.tradePayables, ACCOUNTS.borrowings, ACCOUNTS.bonds, ACCOUNTS.liabilities] },
			{ key: 'equity', label: '자본', accounts: [ACCOUNTS.capitalStock, ACCOUNTS.capitalSurplus, ACCOUNTS.retainedEarnings, ACCOUNTS.treasuryStock, ACCOUNTS.otherEquity, ACCOUNTS.equity] }
		]
	},
	CF: {
		title: '현금흐름표',
		subtitle: '이익이 현금으로 바뀌는지, 투자와 자금조달이 어떻게 움직이는지 본다.',
		required: [ACCOUNTS.ocf, ACCOUNTS.icf, ACCOUNTS.financingCf],
		metrics: [
			{ ...ACCOUNTS.ocf, formula: '재무제표 영업활동현금흐름' },
			{ ...ACCOUNTS.icf, formula: '재무제표 투자활동현금흐름' },
			{ ...ACCOUNTS.financingCf, formula: '재무제표 재무활동현금흐름' },
			{ ...ACCOUNTS.fcf, formula: 'CAPEX가 있으면 영업CF + CAPEX, 없으면 영업CF + 투자CF', calc: calcFcf },
			{ ...ACCOUNTS.ocf, key: 'cashConversion', label: '현금전환율', unit: '%', kind: 'pct', formula: '영업CF / 순이익', calc: () => null },
			{ ...ACCOUNTS.closingCash, formula: '재무제표 기말현금' }
		],
		charts: [
			{ key: 'cf-stack', title: '영업 · 투자 · 재무 CF', kind: 'bar', series: [ACCOUNTS.ocf, ACCOUNTS.icf, ACCOUNTS.financingCf] },
			{ key: 'cf-cash', title: 'FCF · 기말현금', kind: 'line', series: [ACCOUNTS.fcf, ACCOUNTS.closingCash] }
		],
		groups: [
			{ key: 'operating', label: '영업 현금흐름', accounts: [ACCOUNTS.ocf] },
			{ key: 'investing', label: '투자 현금흐름', accounts: [ACCOUNTS.icf, ACCOUNTS.capex] },
			{ key: 'financing', label: '재무 현금흐름', accounts: [ACCOUNTS.financingCf, ACCOUNTS.dividendPaid, ACCOUNTS.closingCash] }
		]
	}
};

function buildMetric(table: BrowserTable | null, spec: MetricSpec): StatementMetric {
	const values = spec.calc ? latestSeriesValue(spec.calc(table)) : readSeries(table, spec.match).at(-1) ?? null;
	const row = spec.calc ? null : findAccountRow(table, spec.match);
	const delta = spec.calc ? null : yoy(readSeries(table, spec.match));
	const period = table?.columns.at(-1) ?? null;
	return {
		key: spec.key,
		label: spec.label,
		value: values,
		display: formatMetricValue(values, spec.unit),
		unit: spec.unit,
		period,
		delta,
		tone: metricTone(spec.key, values, delta),
		formula: spec.formula,
		source: sourceLabel(table?.source ?? (row ? '재무제표' : null))
	};
}

function buildChart(table: BrowserTable | null, spec: ChartSpec): StatementChart {
	const periods = table?.columns ?? [];
	const series = spec.series.map((item) => {
		let values: Array<number | null>;
		if (item.key === 'opMargin') values = ratioSeries(table, ACCOUNTS.op.match, ACCOUNTS.revenue.match);
		else if (item.key === 'netMargin') values = ratioSeries(table, ACCOUNTS.net.match, ACCOUNTS.revenue.match);
		else if (item.key === 'fcf') values = fcfSeries(table);
		else values = readSeries(table, item.match);
		return { key: item.key, label: item.label, unit: item.unit, values };
	});
	return { key: spec.key, title: spec.title, kind: spec.kind, periods, series };
}

function toGroupRow(table: BrowserTable | null, spec: AccountSpec): StatementGroupRow | null {
	const row = findAccountRow(table, spec.match);
	if (!row || !table) return null;
	const values = row.values;
	return {
		key: spec.key,
		label: row.label || spec.label,
		unit: row.unit || spec.unit,
		values,
		yoy: yoy(values.map(numberOrNull)),
		source: sourceLabel(table.source),
		raw: row
	};
}

function findAccountRow(table: BrowserTable | null | undefined, matches: string[]): BrowserTable['rows'][number] | null {
	if (!table) return null;
	const normalizedMatches = matches.map((match) => match.toLowerCase());
	const exact =
		table.rows.find((row) => {
			const key = String(row.key ?? '').toLowerCase();
			const label = String(row.label ?? '').toLowerCase();
			return normalizedMatches.some((match) => key === match || label === match);
		}) ?? null;
	if (exact) return exact;

	const broadUnsafe = new Set(['assets', 'liabilities', 'equity']);
	return (
		table.rows.find((row) => {
			const key = String(row.key ?? '').toLowerCase();
			const label = String(row.label ?? '').toLowerCase();
			return normalizedMatches.some((match) => {
				if (broadUnsafe.has(match)) return false;
				return key.includes(match) || label.includes(match);
			});
		}) ?? null
	);
}

function readSeries(table: BrowserTable | null | undefined, matches: string[]): Array<number | null> {
	return findAccountRow(table, matches)?.values.map(numberOrNull) ?? [];
}

function ratioLatest(table: BrowserTable | null, numerator: string[], denominator: string[]): number | null {
	return ratioSeries(table, numerator, denominator).at(-1) ?? null;
}

function ratioSeries(table: BrowserTable | null, numerator: string[], denominator: string[]): Array<number | null> {
	const a = readSeries(table, numerator);
	const b = readSeries(table, denominator);
	const len = Math.max(a.length, b.length);
	return Array.from({ length: len }, (_, i) => (a[i] != null && b[i] ? (a[i]! / b[i]!) * 100 : null));
}

function calcFcf(table: BrowserTable | null): number | null {
	return fcfSeries(table).at(-1) ?? null;
}

function fcfSeries(table: BrowserTable | null): Array<number | null> {
	const ocf = readSeries(table, ACCOUNTS.ocf.match);
	const capex = readSeries(table, ACCOUNTS.capex.match);
	const icf = readSeries(table, ACCOUNTS.icf.match);
	const len = Math.max(ocf.length, capex.length, icf.length);
	return Array.from({ length: len }, (_, i) => {
		if (ocf[i] == null) return null;
		if (capex[i] != null) return ocf[i]! + capex[i]!;
		if (icf[i] != null) return ocf[i]! + icf[i]!;
		return null;
	});
}

function yoy(values: Array<number | null>): number | null {
	const nums = values.filter((v): v is number => typeof v === 'number' && Number.isFinite(v));
	if (nums.length < 2 || nums.at(-2) === 0) return null;
	return (nums.at(-1)! / nums.at(-2)! - 1) * 100;
}

function latestSeriesValue(value: number | null): number | null {
	return value == null || !Number.isFinite(value) ? null : value;
}

function formatMetricValue(value: number | null, unit: string): string {
	if (value == null || !Number.isFinite(value)) return '데이터 없음';
	if (unit === '%') return `${value.toFixed(1)}%`;
	return formatAmountShort(value);
}

function metricTone(key: string, value: number | null, delta: number | null): 'good' | 'bad' | 'neutral' {
	if (value == null && delta == null) return 'neutral';
	if (key === 'debtRatio') return value != null && value > 200 ? 'bad' : 'neutral';
	const signal = delta ?? value;
	if (signal == null) return 'neutral';
	if (signal > 0) return 'good';
	if (signal < 0) return 'bad';
	return 'neutral';
}

function sourceLabel(source: string | undefined | null): string {
	if (!source) return '출처 대기';
	if (source.includes('dart/finance')) return '재무제표';
	if (source.includes('dashboards/finance') || source.includes('dashboards/quarters')) return '재무제표';
	if (source.includes('dart/panel')) return '공시 panel 원문';
	if (source.includes('report')) return '정기보고서';
	if (source.includes('map') || source.includes('dashboard')) return '산업지도';
	return '원본 데이터';
}

function periodYear(period: unknown): string | null {
	const text = String(period ?? '').trim();
	const match = text.match(/^(\d{4})/);
	return match?.[1] ?? null;
}

function periodReportType(period: unknown): string | null {
	const text = String(period ?? '').trim().toUpperCase();
	if (text.endsWith('Q4')) return '사업보고서';
	if (text.endsWith('Q2')) return '반기보고서';
	if (text.endsWith('Q1') || text.endsWith('Q3')) return '분기보고서';
	return text ? '정기보고서' : null;
}

function evidenceLabels(label: string, key: string): { docs: string[]; facts: string[] } {
	const text = `${label} ${key}`;
	if (/매출|Revenue|sales|영업|순이익|Profit/i.test(text)) {
		return { docs: ['사업', '제품', '매출', '시장', '위험'], facts: ['dividend', 'executive', 'auditOpinion'] };
	}
	if (/재고|채권|자산|현금|유형|무형|Assets|Inventories/i.test(text)) {
		return { docs: ['주석', '재고', '채권', '자산', '위험'], facts: ['auditOpinion', 'majorHolder'] };
	}
	if (/부채|차입|사채|Liabilities|Borrowings|Bonds/i.test(text)) {
		return { docs: ['차입', '사채', '유동성', '위험', '재무'], facts: ['corporateBond', 'auditOpinion'] };
	}
	if (/자본|배당|자사주|Equity|Dividend/i.test(text)) {
		return { docs: ['배당', '자본', '주주'], facts: ['dividend', 'treasuryStock', 'majorHolder'] };
	}
	if (/현금흐름|CF|CashFlows|투자|재무활동/i.test(text)) {
		return { docs: ['현금흐름', '투자', '자금', '배당'], facts: ['dividend', 'treasuryStock', 'corporateBond'] };
	}
	return { docs: ['사업', '재무', '위험'], facts: ['auditOpinion'] };
}

async function loadStatement(
	company: BrowserCompany,
	topic: StatementKey,
	freq: StatementFreq
): Promise<BrowserTable | null> {
	try {
		const result = await company.show(topic, { freq });
		return result.kind === 'table' ? result : null;
	} catch {
		return null;
	}
}

async function loadChangesForCompany(stockCode: string, limit = 6): Promise<CompanyChange[]> {
	try {
		const db = await loadDartDb();
		if (!db) return [];
		return await loadCompanyChanges(db, stockCode, limit);
	} catch {
		return [];
	}
}

function buildStatementSlot(
	annual: BrowserTable | null,
	quarterly: BrowserTable | null,
	fallback: BrowserTable | null
): LiveStatementSlot {
	const selectedAnnual = annual ?? fallback;
	const status = annual ? 'ready' : fallback ? 'fallback' : 'missing';
	return {
		annual: selectedAnnual,
		quarterly,
		status,
		source: selectedAnnual?.source ?? quarterly?.source ?? 'missing'
	};
}

function buildPrice(
	stockCode: string,
	snapshot: PriceSnapshotFile | null,
	valuation: ValuationRuntimeMetrics | null
): LiveCompanyPrice | null {
	const item = snapshot?.data?.[stockCode];
	if (!item && !valuation) return null;
	return {
		currentPrice: numberOrNull(item?.currentPrice) ?? valuation?.currentPrice ?? null,
		marketCap: valuation?.marketCap ?? numberOrNull(item?.marketCap),
		per: valuation?.per ?? null,
		pbr: valuation?.pbr ?? null,
		dividendYield: valuation?.dividendYield ?? null,
		snapshotAt: item?.priceUpdated ?? snapshot?.builtAt ?? null,
		return1m: numberOrNull(item?.return1m),
		return3m: numberOrNull(item?.return3m),
		return1y: numberOrNull(item?.return1y),
		volatility1y: numberOrNull(item?.volatility1y)
	};
}

function normalizeFinancials(value: unknown): FinancialYear[] {
	if (!Array.isArray(value)) return [];
	return value
		.map((row) => ({
			year: (row as FinancialYear).year,
			sales: numberOrNull((row as FinancialYear).sales),
			operating_profit: numberOrNull((row as FinancialYear).operating_profit),
			net_profit: numberOrNull((row as FinancialYear).net_profit),
			total_assets: numberOrNull((row as FinancialYear).total_assets)
		}))
		.filter((row) => row.year != null)
		.sort((a, b) => Number(a.year) - Number(b.year));
}

function buildSummary(
	financials: FinancialYear[],
	statements?: Record<StatementKey, LiveStatementSlot>
): LiveCompanySummary | null {
	const latest = financials.at(-1);
	const isTable = statements?.IS.annual;
	const bsTable = statements?.BS.annual;
	const latestColumn = isTable?.columns.at(-1);
	const revenue = numberOrNull(latest?.sales) ?? readLatestByKey(isTable, ['ifrs-full_Revenue', 'Revenue', 'sales', '매출액']);
	const op =
		numberOrNull(latest?.operating_profit) ??
		readLatestByKey(isTable, ['dart_OperatingIncomeLoss', 'OperatingIncomeLoss', 'op', '영업이익']);
	const net =
		numberOrNull(latest?.net_profit) ??
		readLatestByKey(isTable, ['ifrs-full_ProfitLoss', 'ProfitLoss', 'net', '당기순이익']);
	const assets =
		numberOrNull(latest?.total_assets) ??
		readLatestByKey(bsTable, ['ifrs-full_Assets', 'Assets', 'totalAsset', 'total_assets', '자산총계']);
	const liabilities = readLatestByKey(bsTable, [
		'ifrs-full_Liabilities',
		'Liabilities',
		'totalLiab',
		'부채총계'
	]);
	const equity = readLatestByKey(bsTable, [
		'ifrs-full_Equity',
		'Equity',
		'totalEquity',
		'total_stockholders_equity',
		'자본총계',
		'총자본'
	]);
	if (revenue == null && op == null && net == null && assets == null) return null;
	return {
		year: latest?.year != null ? String(latest.year) : (latestColumn ?? null),
		revenue,
		op,
		net,
		opMargin: revenue && op != null ? (op / revenue) * 100 : null,
		roe: null,
		debtRatio: equity && liabilities != null ? (liabilities / equity) * 100 : null
	};
}

function buildDiagnosis(
	summary: LiveCompanySummary | null,
	statements: Record<StatementKey, LiveStatementSlot>
): LiveCompanyDiagnosis[] {
	const is = statements.IS.annual;
	const bs = statements.BS.annual;
	const cf = statements.CF.annual;
	const revenueSeries = readSeriesByKey(is, ['ifrs-full_Revenue', 'Revenue', 'sales', '매출액']);
	const opSeries = readSeriesByKey(is, ['dart_OperatingIncomeLoss', 'OperatingIncomeLoss', 'op', '영업이익']);
	const debtSeries = readSeriesByKey(bs, ['ifrs-full_Liabilities', 'Liabilities', 'totalLiab', '부채총계']);
	const equitySeries = readSeriesByKey(bs, ['ifrs-full_Equity', 'Equity', 'totalEquity', '자본총계', '총자본']);
	const ocfSeries = readSeriesByKey(cf, ['영업활동현금흐름', 'CashFlowsFromUsedInOperatingActivities', 'op']);

	const revenueGrowth = pctChange(lastTwoNumbers(revenueSeries));
	const opMargin = summary?.opMargin ?? null;
	const latestDebt = debtSeries.at(-1);
	const latestEquity = equitySeries.at(-1);
	const debtRatio =
		latestDebt != null && latestEquity != null && latestEquity !== 0
			? (latestDebt / latestEquity) * 100
			: summary?.debtRatio ?? null;
	const ocf = ocfSeries.at(-1);

	return [
		{
			key: 'growth',
			label: '성장',
			value: revenueGrowth == null ? '매출 추세 데이터 없음' : `매출 ${formatSignedPct(revenueGrowth)}`,
			tone: toneFromNumber(revenueGrowth),
			source: is?.source ?? 'missing'
		},
		{
			key: 'profitability',
			label: '수익성',
			value: opMargin == null ? '영업이익률 데이터 없음' : `영업이익률 ${formatPctValue(opMargin)}`,
			tone: toneFromNumber(opMargin),
			source: is?.source ?? 'missing'
		},
		{
			key: 'structure',
			label: '구조',
			value:
				debtRatio == null
					? ocf == null
						? '재무구조/현금흐름 데이터 없음'
						: `영업CF ${formatAmountShort(ocf)}`
					: `부채비율 ${formatPctValue(debtRatio)}`,
			tone: debtRatio == null ? toneFromNumber(ocf) : debtRatio > 200 ? 'bad' : 'neutral',
			source: bs?.source ?? cf?.source ?? 'missing'
		}
	];
}

function buildSourceStatus(
	statements: Record<StatementKey, LiveStatementSlot>,
	changes: LiveCompanyChange[],
	companyMeta: any,
	meta: any,
	price: LiveCompanyPrice | null
): LiveCompanySourceStatus[] {
	const hasFinance = Object.values(statements).some((slot) => slot.status === 'ready');
	return [
		{
			key: 'finance',
			label: '재무제표',
			status: hasFinance ? 'ready' : Object.values(statements).some((s) => s.status === 'fallback') ? 'fallback' : 'missing',
			source: hasFinance ? '재무제표 원본' : '산업지도 요약'
		},
		{
			key: 'report',
			label: '정기보고서',
			status: changes.length ? 'ready' : 'lazy',
			source: '정형 보고서 팩트'
		},
		{
			key: 'docs',
			label: '사업보고서 원문',
			status: 'lazy',
			source: '원문 섹션'
		},
		{
			key: 'map',
			label: '산업지도',
			status: companyMeta ? 'ready' : 'missing',
			source: meta?.buildId ?? 'latest'
		},
		{
			key: 'price',
			label: '시장가격',
			status: price ? 'ready' : 'missing',
			source: price?.snapshotAt ?? '가격 스냅샷'
		}
	];
}

function buildIncomeStatement(stockCode: string, financials: FinancialYear[]): BrowserTable | null {
	if (financials.length === 0) return null;
	const columns = financials.map((row) => String(row.year));
	return {
		kind: 'table',
		topic: 'IS',
		stockCode,
		unit: '원',
		columns,
		rows: [
			{
				key: 'sales',
				label: '매출액',
				unit: '원',
				values: financials.map((row) => numberOrNull(row.sales))
			},
			{
				key: 'operating_profit',
				label: '영업이익',
				unit: '원',
				values: financials.map((row) => numberOrNull(row.operating_profit))
			},
			{
				key: 'net_profit',
				label: '순이익',
				unit: '원',
				values: financials.map((row) => numberOrNull(row.net_profit))
			}
		],
		source: 'hf://landing/map/companies/{stockCode}.json#financials5y'
	};
}

function buildBalanceSheet(stockCode: string, financials: FinancialYear[]): BrowserTable | null {
	if (financials.length === 0) return null;
	const columns = financials.map((row) => String(row.year));
	return {
		kind: 'table',
		topic: 'BS',
		stockCode,
		unit: '원',
		columns,
		rows: [
			{
				key: 'total_assets',
				label: '총자산',
				unit: '원',
				values: financials.map((row) => numberOrNull(row.total_assets))
			}
		],
		source: 'hf://landing/map/companies/{stockCode}.json#financials5y'
	};
}

function buildOverview(stockCode: string, companyMeta: any, industryMeta: any): BrowserText {
	const ego = companyMeta?.ego;
	const title = `${ego?.corpName ?? stockCode} Company`;
	const narrative = companyMeta?.aiInsight?.narrative;
	const strengths = Array.isArray(companyMeta?.aiInsight?.strengths)
		? companyMeta.aiInsight.strengths.slice(0, 2).join(' · ')
		: '';
	const weaknesses = Array.isArray(companyMeta?.aiInsight?.weaknesses)
		? companyMeta.aiInsight.weaknesses.slice(0, 2).join(' · ')
		: '';
	const fallback = [
		ego?.corpName ?? stockCode,
		ego?.industry ? `${ego.industry} 산업` : null,
		ego?.stage ? `${ego.stage} 단계` : null,
		ego?.role ? `${ego.role} 역할` : null,
		industryMeta?.name ? `${industryMeta.name} 맥락` : null
	]
		.filter(Boolean)
		.join(' · ');
	const text = typeof narrative === 'string' && narrative.trim() ? narrative : fallback;
	return {
		kind: 'text',
		topic: 'businessOverview',
		stockCode,
		title,
		text: [text, strengths ? `강점: ${strengths}` : null, weaknesses ? `약점: ${weaknesses}` : null]
			.filter(Boolean)
			.join('\n'),
		source: `hf://landing/map/companies/${stockCode}.json`
	};
}

function numberOrNull(value: unknown): number | null {
	if (typeof value === 'number') return Number.isFinite(value) ? value : null;
	if (typeof value === 'bigint') {
		const n = Number(value);
		return Number.isFinite(n) ? n : null;
	}
	if (typeof value === 'string' && value.trim()) {
		const n = Number(value.replace(/,/g, ''));
		return Number.isFinite(n) ? n : null;
	}
	return null;
}

function readLatestByKey(table: BrowserTable | null | undefined, keys: string[]): number | null {
	const series = readSeriesByKey(table, keys);
	return series.length ? series.at(-1) ?? null : null;
}

function readSeriesByKey(table: BrowserTable | null | undefined, keys: string[]): Array<number | null> {
	if (!table) return [];
	const row = table.rows.find((r) => {
		const key = String(r.key ?? '').toLowerCase();
		const label = String(r.label ?? '').toLowerCase();
		return keys.some((candidate) => {
			const c = candidate.toLowerCase();
			return key === c || label === c || key.includes(c) || label.includes(c);
		});
	});
	return row ? row.values.map(numberOrNull) : [];
}

function lastTwoNumbers(values: Array<number | null>): [number, number] | null {
	const nums = values.filter((v): v is number => typeof v === 'number' && Number.isFinite(v));
	if (nums.length < 2) return null;
	return [nums[nums.length - 2], nums[nums.length - 1]];
}

function pctChange(pair: [number, number] | null): number | null {
	if (!pair || pair[0] === 0) return null;
	return (pair[1] / pair[0] - 1) * 100;
}

function toneFromNumber(value: number | null | undefined): 'good' | 'bad' | 'neutral' {
	if (value == null || !Number.isFinite(value)) return 'neutral';
	if (value > 0) return 'good';
	if (value < 0) return 'bad';
	return 'neutral';
}

function formatSignedPct(value: number): string {
	return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;
}

function formatPctValue(value: number): string {
	return `${value.toFixed(1)}%`;
}

function formatAmountShort(value: number): string {
	const abs = Math.abs(value);
	if (abs >= 1e12) return `${(value / 1e12).toFixed(1)}조`;
	if (abs >= 1e8) return `${Math.round(value / 1e8).toLocaleString()}억`;
	return value.toLocaleString();
}

