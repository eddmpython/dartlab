import type {
	UniverseCatalogCoverage,
	UniverseConformanceObservation,
	UniverseEntityProfile,
	UniverseEntitySearchRequest,
	UniverseEntitySearchResult,
	UniverseGlobalEntity,
	UniverseLegalEntityIdentity,
	UniversePairComparison
} from '@dartlab/ui-contracts';
import { buildGrid, FINANCE_COLUMNS, num, type Parsed, type RawRow } from '../finance/accounts';
import type { DataCore } from '../fetch/request';
import { compilePairedConformance, UNIVERSE_PAIRED_QUESTIONS } from './conformance';

const SIX_HOURS = 6 * 60 * 60 * 1_000;
const WHOLE_FILE_CACHE = { scope: 'memory', ttlMs: SIX_HOURS, maxEntries: 8 } as const;
const DART_REGISTRY_PATH = 'metadata/dartList.parquet';
const DART_PROFILE_PATH = 'dart/scan/corpProfile.parquet';
const SEC_TICKERS_PATH = 'edgar/tickers/tickers.parquet';
const EDGAR_FINANCE_PATH = 'edgar/scan/finance.parquet';
const STOCK_CODE = /^[0-9A-Z]{6}$/;
const US_TICKER = /^[A-Z][A-Z0-9.-]{0,9}$/;
const DATE8 = /^[0-9]{8}$/;

interface DartRegistryRow extends Record<string, unknown> {
	corp_code?: unknown;
	corp_name?: unknown;
	corp_eng_name?: unknown;
	stock_code?: unknown;
	modify_date?: unknown;
}

interface DartProfileRow extends Record<string, unknown> {
	corp_code?: unknown;
	stockCode?: unknown;
	induty_code?: unknown;
	est_dt?: unknown;
	corp_cls?: unknown;
}

interface SecTickerRow extends Record<string, unknown> {
	ticker?: unknown;
	cik?: unknown;
	title?: unknown;
	exchange?: unknown;
	is_exchange_listed?: unknown;
	is_otc?: unknown;
}

interface EdgarFinanceRow extends Record<string, unknown> {
	stockCode?: unknown;
	cik?: unknown;
	corpName?: unknown;
	fy?: unknown;
	sic?: unknown;
	sector?: unknown;
	sales?: unknown;
	operating_profit?: unknown;
	net_profit?: unknown;
	interest_expense?: unknown;
	total_assets?: unknown;
	current_assets?: unknown;
	current_liabilities?: unknown;
	total_stockholders_equity?: unknown;
	cash_and_cash_equivalents?: unknown;
	longterm_borrowings?: unknown;
	operating_cashflow?: unknown;
	investing_cashflow?: unknown;
	financing_cash_flow?: unknown;
	capex?: unknown;
	total_liabilities?: unknown;
	shortterm_borrowings?: unknown;
}

interface EdgarFinanceHistory {
	latest: EdgarFinanceRow;
	previous: EdgarFinanceRow | null;
}

interface UniverseGlobalCatalog {
	coverage: UniverseCatalogCoverage;
	entities: readonly UniverseGlobalEntity[];
	entityById: ReadonlyMap<string, UniverseGlobalEntity>;
	edgarFinanceByCik: ReadonlyMap<string, EdgarFinanceHistory>;
}

export interface UniverseGlobalRuntime {
	coverage(): Promise<UniverseCatalogCoverage>;
	search(request: UniverseEntitySearchRequest): Promise<UniverseEntitySearchResult>;
	profile(entityId: string): Promise<UniverseEntityProfile>;
	compare(krEntityId: string, usEntityId: string): Promise<UniversePairComparison>;
}

function text(value: unknown): string {
	return typeof value === 'string' ? value.trim() : value == null ? '' : String(value).trim();
}

function bool(value: unknown): boolean {
	return value === true || value === 1 || value === '1' || value === 'true';
}

function corpCode(value: unknown): string | null {
	const code = text(value);
	return /^[0-9]{8}$/.test(code) ? code : null;
}

function cik(value: unknown): string | null {
	const raw = text(value).replace(/^0+/, '');
	return /^[0-9]{1,10}$/.test(raw) ? raw.padStart(10, '0') : null;
}

function stockCode(value: unknown): string | null {
	const code = text(value).toUpperCase();
	return STOCK_CODE.test(code) ? code : null;
}

function ticker(value: unknown): string | null {
	const code = text(value).toUpperCase();
	return US_TICKER.test(code) ? code : null;
}

function date8(value: unknown): string | null {
	const raw = text(value).replace(/[^0-9]/g, '').slice(0, 8);
	if (!DATE8.test(raw)) return null;
	const date = `${raw.slice(0, 4)}-${raw.slice(4, 6)}-${raw.slice(6, 8)}`;
	return Number.isNaN(Date.parse(`${date}T00:00:00Z`)) ? null : date;
}

function year(value: unknown): number | null {
	const parsed = Number(value);
	return Number.isInteger(parsed) && parsed >= 1900 && parsed <= 2200 ? parsed : null;
}

function marketName(corpClass: string): string | null {
	if (corpClass === 'Y') return 'KOSPI';
	if (corpClass === 'K') return 'KOSDAQ';
	if (corpClass === 'N') return 'KONEX';
	if (corpClass === 'E') return '기타법인';
	return null;
}

function maxText(values: readonly unknown[]): string | null {
	let maximum = '';
	for (const value of values) {
		const candidate = text(value);
		if (candidate > maximum) maximum = candidate;
	}
	return maximum || null;
}

function latestEdgarFinance(rows: readonly EdgarFinanceRow[]): Map<string, EdgarFinanceHistory> {
	const result = new Map<string, EdgarFinanceHistory>();
	for (const row of rows) {
		const id = cik(row.cik);
		const fiscalYear = year(row.fy);
		if (!id || fiscalYear === null) continue;
		const current = result.get(id);
		if (!current) {
			result.set(id, { latest: row, previous: null });
			continue;
		}
		const latestYear = year(current.latest.fy) ?? -1;
		const previousYear = year(current.previous?.fy) ?? -1;
		if (fiscalYear > latestYear) {
			current.previous = current.latest;
			current.latest = row;
		} else if (fiscalYear < latestYear && fiscalYear > previousYear) {
			current.previous = row;
		}
	}
	return result;
}

export function buildUniverseGlobalCatalog(
	dartRows: readonly DartRegistryRow[],
	dartProfileRows: readonly DartProfileRow[],
	secRows: readonly SecTickerRow[],
	edgarRows: readonly EdgarFinanceRow[]
): UniverseGlobalCatalog {
	const profileByCorp = new Map<string, DartProfileRow>();
	for (const row of dartProfileRows) {
		const id = corpCode(row.corp_code);
		if (id) profileByCorp.set(id, row);
	}

	const krEntities: UniverseGlobalEntity[] = [];
	for (const row of dartRows) {
		const legalEntityId = corpCode(row.corp_code);
		const label = text(row.corp_name);
		if (!legalEntityId || !label) continue;
		const profile = profileByCorp.get(legalEntityId);
		const securityId = stockCode(row.stock_code) ?? stockCode(profile?.stockCode);
		const corpClass = text(profile?.corp_cls).toUpperCase();
		const industryCode = text(profile?.induty_code) || null;
		const labelEn = text(row.corp_eng_name) || null;
		krEntities.push({
			entityId: `KR:DART:${legalEntityId}`,
			market: 'KR',
			legalEntityId,
			securityId,
			ticker: securityId,
			aliases: [securityId, labelEn].filter((value): value is string => Boolean(value)),
			label,
			labelEn,
			listed: corpClass === 'Y' || corpClass === 'K' || corpClass === 'N',
			exchange: marketName(corpClass),
			industryName: industryCode ? `KSIC ${industryCode}` : null,
			industryScheme: industryCode ? 'KSIC' : null,
			validFrom: date8(profile?.est_dt),
			latestFiscalYear: null,
			financialCoverage: securityId ? 'onDemand' : 'identityOnly',
			sourceRefs: profile
				? [`${DART_REGISTRY_PATH}#corp_code=${legalEntityId}`, `${DART_PROFILE_PATH}#corp_code=${legalEntityId}`]
				: [`${DART_REGISTRY_PATH}#corp_code=${legalEntityId}`]
		});
	}

	const financeByCik = latestEdgarFinance(edgarRows);
	const tickerRowsByCik = new Map<string, SecTickerRow[]>();
	for (const row of secRows) {
		const id = cik(row.cik);
		const symbol = ticker(row.ticker);
		if (!id || !symbol) continue;
		const rows = tickerRowsByCik.get(id) ?? [];
		rows.push(row);
		tickerRowsByCik.set(id, rows);
	}

	const usEntityIds = new Set([...tickerRowsByCik.keys(), ...financeByCik.keys()]);
	const usEntities: UniverseGlobalEntity[] = [];
	for (const legalEntityId of usEntityIds) {
		const tickerRows = (tickerRowsByCik.get(legalEntityId) ?? []).slice().sort((left, right) => {
			const listedOrder = Number(bool(right.is_exchange_listed)) - Number(bool(left.is_exchange_listed));
			if (listedOrder !== 0) return listedOrder;
			const otcOrder = Number(bool(left.is_otc)) - Number(bool(right.is_otc));
			if (otcOrder !== 0) return otcOrder;
			return text(left.ticker).localeCompare(text(right.ticker));
		});
		const finance = financeByCik.get(legalEntityId);
		const primary = tickerRows[0];
		const financeTicker = ticker(finance?.latest.stockCode);
		const primaryTicker = ticker(primary?.ticker) ?? financeTicker;
		const aliases = [...new Set([...tickerRows.map((row) => ticker(row.ticker)), financeTicker].filter((value): value is string => Boolean(value)))];
		const label = text(primary?.title) || text(finance?.latest.corpName) || `SEC filer ${legalEntityId}`;
		const sector = text(finance?.latest.sector) || null;
		const latestFiscalYear = year(finance?.latest.fy);
		usEntities.push({
			entityId: `US:SEC:${legalEntityId}`,
			market: 'US',
			legalEntityId,
			securityId: null,
			ticker: primaryTicker,
			aliases,
			label,
			labelEn: label,
			listed: tickerRows.some((row) => bool(row.is_exchange_listed)),
			exchange: text(primary?.exchange) || null,
			industryName: sector,
			industryScheme: sector || text(finance?.latest.sic) ? 'SIC' : null,
			validFrom: null,
			latestFiscalYear: latestFiscalYear === null ? null : String(latestFiscalYear),
			financialCoverage: finance ? 'indexed' : primaryTicker ? 'onDemand' : 'identityOnly',
			sourceRefs: [
				...(tickerRows.length > 0 ? [`${SEC_TICKERS_PATH}#cik=${legalEntityId}`] : []),
				...(finance ? [`${EDGAR_FINANCE_PATH}#cik=${legalEntityId}`] : [])
			]
		});
	}

	const entities = [...krEntities, ...usEntities];
	const entityById = new Map(entities.map((entity) => [entity.entityId, entity]));
	const maxModifyDate = maxText(dartRows.map((row) => row.modify_date));
	const maxFiscalYear = Math.max(...edgarRows.map((row) => year(row.fy) ?? -1));
	const coverage: UniverseCatalogCoverage = {
		schemaVersion: 'universeCatalog.v1',
		entityCount: entities.length,
		krLegalEntityCount: krEntities.length,
		krSecurityCount: krEntities.filter((entity) => entity.securityId !== null).length,
		usLegalEntityCount: usEntities.length,
		usTickerCount: secRows.filter((row) => ticker(row.ticker) !== null).length,
		usFinanceEntityCount: financeByCik.size,
		sources: [
			{ sourceId: 'dartRegistry', path: DART_REGISTRY_PATH, rowCount: dartRows.length, dataAsOf: date8(maxModifyDate) },
			{ sourceId: 'dartCompanyProfile', path: DART_PROFILE_PATH, rowCount: dartProfileRows.length, dataAsOf: null },
			{ sourceId: 'secTickers', path: SEC_TICKERS_PATH, rowCount: secRows.length, dataAsOf: null },
			{ sourceId: 'edgarFinance', path: EDGAR_FINANCE_PATH, rowCount: edgarRows.length, dataAsOf: maxFiscalYear > 0 ? String(maxFiscalYear) : null }
		]
	};
	return { coverage, entities, entityById, edgarFinanceByCik: financeByCik };
}

function normalized(value: string): string {
	return value.normalize('NFKC').toLocaleLowerCase().replace(/\s+/g, ' ').trim();
}

function compact(value: string): string {
	return normalized(value).replace(/[\s:._-]+/g, '');
}

function matchScore(entity: UniverseGlobalEntity, query: string): number | null {
	const fields = [entity.entityId, entity.legalEntityId, entity.securityId, entity.ticker, entity.label, entity.labelEn, ...entity.aliases]
		.filter((value): value is string => Boolean(value))
		.map(normalized);
	const queryCompact = compact(query);
	if (fields.some((field) => field === query)) return 0;
	if (fields.some((field) => field.startsWith(query))) return 10;
	if (fields.some((field) => field.split(' ').some((part) => part.startsWith(query)))) return 14;
	if (fields.some((field) => field.includes(query))) return 20;
	if (queryCompact && fields.some((field) => compact(field).includes(queryCompact))) return 24;
	return null;
}

export function searchUniverseGlobalCatalog(
	catalog: UniverseGlobalCatalog,
	request: UniverseEntitySearchRequest
): UniverseEntitySearchResult {
	const query = normalized(request.query);
	const market = request.market ?? 'ALL';
	const limit = Math.max(1, Math.min(50, Math.floor(request.limit ?? 20)));
	if (!query) return { query: request.query, market, matches: [], coverage: catalog.coverage };
	const scored: Array<{ entity: UniverseGlobalEntity; score: number }> = [];
	for (const entity of catalog.entities) {
		if (market !== 'ALL' && entity.market !== market) continue;
		const score = matchScore(entity, query);
		if (score === null) continue;
		scored.push({ entity, score: score - Number(entity.listed) - Number(entity.financialCoverage !== 'identityOnly') });
	}
	scored.sort((left, right) => left.score - right.score
		|| left.entity.label.localeCompare(right.entity.label, left.entity.market === 'KR' ? 'ko' : 'en')
		|| left.entity.entityId.localeCompare(right.entity.entityId));
	return { query: request.query, market, matches: scored.slice(0, limit).map(({ entity }) => entity), coverage: catalog.coverage };
}

function identityFor(entity: UniverseGlobalEntity, validFrom: string | null = null): UniverseLegalEntityIdentity {
	return {
		market: entity.market,
		legalEntityId: entity.legalEntityId,
		securityId: entity.securityId,
		ticker: entity.ticker,
		validFrom: validFrom ?? entity.validFrom,
		validTo: null,
		sourceRef: entity.sourceRefs[0] ?? entity.entityId
	};
}

function addObservation(
	rows: UniverseConformanceObservation[],
	entity: UniverseLegalEntityIdentity,
	metricId: string,
	value: number | null,
	unit: string,
	dataAsOf: string,
	sourceRef: string
): void {
	if (value === null || !Number.isFinite(value)) return;
	rows.push({ entity, metricId, value, unit, dataAsOf, sourceRef });
}

function divide(numerator: number | null, denominator: number | null, scale = 100): number | null {
	return numerator !== null && denominator !== null && denominator > 0 ? (numerator / denominator) * scale : null;
}

function sumDefined(...values: Array<number | null>): number | null {
	const present = values.filter((value): value is number => value !== null);
	return present.length > 0 ? present.reduce((total, value) => total + value, 0) : null;
}

function financeObservations(
	entity: UniverseGlobalEntity,
	rows: readonly RawRow[],
	path: string,
	validFrom: string | null
): UniverseConformanceObservation[] {
	const annual = rows.filter((row) => text(row.reprt_code) === '11011' && year(row.bsns_year) !== null);
	if (annual.length === 0) return [];
	const latestYear = Math.max(...annual.map((row) => year(row.bsns_year) ?? -1));
	const scope = annual.some((row) => year(row.bsns_year) === latestYear && text(row.fs_div) === 'CFS') ? 'CFS' : 'OFS';
	const scoped = annual.filter((row) => text(row.fs_div) === scope);
	const receiptByYear = new Map<number, string>();
	for (const row of scoped) {
		const fiscalYear = year(row.bsns_year);
		if (fiscalYear === null) continue;
		const receipt = text(row.rcept_no);
		if (receipt && (!receiptByYear.has(fiscalYear) || receipt < receiptByYear.get(fiscalYear)!)) receiptByYear.set(fiscalYear, receipt);
	}
	const parsed: Parsed[] = [];
	const incomeSource = scoped.some((row) => text(row.sj_div) === 'IS') ? 'IS' : 'CIS';
	for (const row of scoped) {
		const fiscalYear = year(row.bsns_year);
		const amount = num(row.thstrm_amount);
		if (fiscalYear === null || amount === null) continue;
		const sourceStatement = text(row.sj_div);
		const parsedRow = (statement: string): Parsed => ({
			sj: statement,
			year: fiscalYear,
			q: 4,
			id: text(row.account_id),
			nm: text(row.account_nm),
			detail: text(row.account_detail),
			ord: num(row.ord) ?? 9999,
			amt: amount
		});
		if (sourceStatement === 'CIS') parsed.push(parsedRow('CIS'));
		if (sourceStatement === 'IS' || sourceStatement === 'CIS') {
			if (sourceStatement === incomeSource) parsed.push(parsedRow('IS'));
		} else {
			parsed.push(parsedRow(sourceStatement));
		}
	}
	const grid = buildGrid(parsed);
	const value = (key: string, fiscalYear = latestYear): number | null => grid[key]?.get(`${fiscalYear}-4`)?.amt ?? null;
	const revenue = value('revenue');
	const operatingProfit = value('operatingIncome');
	const netIncome = value('netIncome') ?? value('cisNetIncome');
	const assets = value('assets');
	const liabilities = value('liabilities');
	const equity = value('equity');
	const currentAssets = value('currentAssets');
	const currentLiabilities = value('currentLiabilities');
	const previousRevenue = value('revenue', latestYear - 1);
	const shortDebt = sumDefined(value('shortDebt'), value('currentLtDebt'));
	const currency = entity.market === 'KR' ? 'KRW' : 'USD';
	const dataAsOf = String(latestYear);
	const identity = identityFor(entity, validFrom);
	const observations: UniverseConformanceObservation[] = [];
	const add = (metricId: string, amount: number | null, unit = currency, sourceKey = metricId) =>
		addObservation(observations, identity, metricId, amount, unit, dataAsOf, `${path}#${scope}/${latestYear}/${sourceKey}`);
	add('revenue', revenue, currency, 'revenue');
	add('operatingProfit', operatingProfit, currency, 'operatingIncome');
	add('netIncome', netIncome, currency, 'netIncome');
	add('totalAssets', assets, currency, 'assets');
	add('totalLiabilities', liabilities, currency, 'liabilities');
	add('operatingCashFlow', value('cfOperating'), currency, 'cfOperating');
	add('investingCashFlow', value('cfInvesting'), currency, 'cfInvesting');
	add('financingCashFlow', value('cfFinancing'), currency, 'cfFinancing');
	add('capitalExpenditure', value('capex'), currency, 'capex');
	add('cash', value('cash'), currency, 'cash');
	add('shortTermDebt', shortDebt, currency, 'shortDebt+currentLtDebt');
	add('longTermDebt', value('longDebt'), currency, 'longDebt');
	add('interestExpense', value('financeCosts'), currency, 'financeCosts');
	add('revenueGrowth', divide(revenue === null || previousRevenue === null ? null : revenue - previousRevenue, previousRevenue), '%', 'revenueGrowth');
	add('operatingMargin', divide(operatingProfit, revenue), '%', 'operatingMargin');
	add('returnOnEquity', divide(netIncome, equity), '%', 'returnOnEquity');
	add('debtRatio', divide(liabilities, equity), '%', 'debtRatio');
	add('currentRatio', divide(currentAssets, currentLiabilities), '%', 'currentRatio');
	const receiptDate = date8(receiptByYear.get(latestYear));
	if (receiptDate) {
		const timestamp = Date.parse(`${receiptDate}T00:00:00Z`);
		addObservation(observations, identity, 'latestPeriodicFiling', timestamp, 'unix-ms', receiptDate, `${path}#${scope}/${latestYear}/rcept_no`);
		addObservation(observations, identity, 'filingAvailableAt', timestamp, 'unix-ms', receiptDate, `${path}#${scope}/${latestYear}/rcept_no`);
	}
	return observations;
}

function edgarScanObservations(
	entity: UniverseGlobalEntity,
	history: EdgarFinanceHistory
): UniverseConformanceObservation[] {
	const row = history.latest;
	const fiscalYear = year(row.fy);
	if (fiscalYear === null) return [];
	const previousSales = num(history.previous?.sales);
	const revenue = num(row.sales);
	const operatingProfit = num(row.operating_profit);
	const netIncome = num(row.net_profit);
	const assets = num(row.total_assets);
	const liabilities = num(row.total_liabilities);
	const equity = num(row.total_stockholders_equity);
	const currentAssets = num(row.current_assets);
	const currentLiabilities = num(row.current_liabilities);
	const identity = identityFor(entity);
	const observations: UniverseConformanceObservation[] = [];
	const add = (metricId: string, value: number | null, unit = 'USD', field = metricId) =>
		addObservation(observations, identity, metricId, value, unit, String(fiscalYear), `${EDGAR_FINANCE_PATH}#cik=${entity.legalEntityId}/${fiscalYear}/${field}`);
	add('revenue', revenue, 'USD', 'sales');
	add('operatingProfit', operatingProfit, 'USD', 'operating_profit');
	add('netIncome', netIncome, 'USD', 'net_profit');
	add('totalAssets', assets, 'USD', 'total_assets');
	add('totalLiabilities', liabilities, 'USD', 'total_liabilities');
	add('operatingCashFlow', num(row.operating_cashflow), 'USD', 'operating_cashflow');
	add('investingCashFlow', num(row.investing_cashflow), 'USD', 'investing_cashflow');
	add('financingCashFlow', num(row.financing_cash_flow), 'USD', 'financing_cash_flow');
	add('capitalExpenditure', num(row.capex), 'USD', 'capex');
	add('cash', num(row.cash_and_cash_equivalents), 'USD', 'cash_and_cash_equivalents');
	add('shortTermDebt', num(row.shortterm_borrowings), 'USD', 'shortterm_borrowings');
	add('longTermDebt', num(row.longterm_borrowings), 'USD', 'longterm_borrowings');
	add('interestExpense', num(row.interest_expense), 'USD', 'interest_expense');
	add('revenueGrowth', divide(revenue === null || previousSales === null ? null : revenue - previousSales, previousSales), '%', 'revenueGrowth');
	add('operatingMargin', divide(operatingProfit, revenue), '%', 'operatingMargin');
	add('returnOnEquity', divide(netIncome, equity), '%', 'returnOnEquity');
	add('debtRatio', divide(liabilities, equity), '%', 'debtRatio');
	add('currentRatio', divide(currentAssets, currentLiabilities), '%', 'currentRatio');
	return observations;
}

function entityProfile(entity: UniverseGlobalEntity, observations: readonly UniverseConformanceObservation[], validFrom: string | null): UniverseEntityProfile {
	const byMetric = new Map(observations.map((observation) => [observation.metricId, observation]));
	const answeredQuestionCount = UNIVERSE_PAIRED_QUESTIONS.filter((question) => {
		const observation = byMetric.get(question.metricId);
		return observation?.value !== null && observation?.unit && observation?.dataAsOf && observation?.sourceRef;
	}).length;
	const gaps = UNIVERSE_PAIRED_QUESTIONS
		.filter((question) => !byMetric.has(question.metricId))
		.map((question) => `${question.questionId}:${question.metricId}`);
	return {
		entity,
		identity: identityFor(entity, validFrom),
		observations,
		answeredQuestionCount,
		questionCount: UNIVERSE_PAIRED_QUESTIONS.length,
		status: answeredQuestionCount === UNIVERSE_PAIRED_QUESTIONS.length ? 'ready' : answeredQuestionCount > 0 ? 'partial' : 'identityOnly',
		gaps
	};
}

async function loadCatalog(core: DataCore): Promise<UniverseGlobalCatalog> {
	const [dartRows, dartProfileRows, secRows, edgarRows] = await Promise.all([
		core.requestParquetWholeFile<DartRegistryRow>({
			path: DART_REGISTRY_PATH,
			columns: ['corp_code', 'corp_name', 'corp_eng_name', 'stock_code', 'modify_date'],
			cacheKey: 'universe.global.dartRegistry.v1',
			cache: WHOLE_FILE_CACHE
		}),
		core.requestParquetWholeFile<DartProfileRow>({
			path: DART_PROFILE_PATH,
			columns: ['corp_code', 'stockCode', 'induty_code', 'est_dt', 'corp_cls'],
			cacheKey: 'universe.global.dartCompanyProfile.v1',
			cache: WHOLE_FILE_CACHE
		}),
		core.requestParquetWholeFile<SecTickerRow>({
			path: SEC_TICKERS_PATH,
			columns: ['ticker', 'cik', 'title', 'exchange', 'is_exchange_listed', 'is_otc'],
			cacheKey: 'universe.global.secTickers.v1',
			cache: WHOLE_FILE_CACHE
		}),
		core.requestParquetWholeFile<EdgarFinanceRow>({
			path: EDGAR_FINANCE_PATH,
			columns: [
				'stockCode', 'cik', 'corpName', 'fy', 'sic', 'sector', 'sales', 'operating_profit', 'net_profit',
				'interest_expense', 'total_assets', 'current_assets', 'current_liabilities', 'total_stockholders_equity',
				'cash_and_cash_equivalents', 'longterm_borrowings', 'operating_cashflow', 'investing_cashflow',
				'financing_cash_flow', 'capex', 'total_liabilities', 'shortterm_borrowings'
			],
			cacheKey: 'universe.global.edgarFinance.v1',
			cache: WHOLE_FILE_CACHE
		})
	]);
	if (!dartRows || !dartProfileRows || !secRows || !edgarRows) throw new Error('Universe global catalog source is missing');
	return buildUniverseGlobalCatalog(dartRows, dartProfileRows, secRows, edgarRows);
}

export function createUniverseGlobalRuntime(core: DataCore): UniverseGlobalRuntime {
	let catalogPromise: Promise<UniverseGlobalCatalog> | null = null;
	const catalog = () => (catalogPromise ??= loadCatalog(core));
	const profilePromises = new Map<string, Promise<UniverseEntityProfile>>();

	async function profile(entityId: string): Promise<UniverseEntityProfile> {
		const existing = profilePromises.get(entityId);
		if (existing) return existing;
		const pending = (async () => {
			const loaded = await catalog();
			const entity = loaded.entityById.get(entityId);
			if (!entity) throw new Error(`Universe entity not found: ${entityId}`);
			const validFrom = entity.validFrom;
			let observations: UniverseConformanceObservation[] = [];
			if (entity.ticker) {
				const path = entity.market === 'KR'
					? `dart/finance/${entity.ticker}.parquet`
					: `edgar/financeStmt/${entity.ticker}.parquet`;
				const rows = await core.requestParquetRows<RawRow>({
					path,
					columns: FINANCE_COLUMNS,
					cacheKey: `universe.global.finance:${entity.entityId}`,
					cache: { scope: 'memory', ttlMs: SIX_HOURS, maxEntries: 32 }
				}).catch(() => []);
				observations = financeObservations(entity, rows, path, validFrom);
			}
			if (entity.market === 'US') {
				const history = loaded.edgarFinanceByCik.get(entity.legalEntityId);
				if (history) {
					const scan = edgarScanObservations(entity, history);
					const merged = new Map(scan.map((observation) => [observation.metricId, observation]));
					for (const observation of observations) merged.set(observation.metricId, observation);
					observations = [...merged.values()];
				}
			}
			return entityProfile(entity, observations, validFrom);
		})();
		profilePromises.set(entityId, pending);
		try {
			return await pending;
		} catch (error) {
			profilePromises.delete(entityId);
			throw error;
		}
	}

	return {
		coverage: async () => (await catalog()).coverage,
		search: async (request) => searchUniverseGlobalCatalog(await catalog(), request),
		profile,
		compare: async (krEntityId, usEntityId) => {
			const [kr, us] = await Promise.all([profile(krEntityId), profile(usEntityId)]);
			if (kr.entity.market !== 'KR' || us.entity.market !== 'US') throw new Error('Universe comparison requires KR then US entities');
			const results = await compilePairedConformance(kr.observations, us.observations);
			const readyCount = results.filter((result) => result.status === 'ready').length;
			return { kr, us, results, readyCount, blockedCount: results.length - readyCount };
		}
	};
}
