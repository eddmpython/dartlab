/**
 * Scan Studio · DuckDB-WASM 으로 HF parquet 직접 query.
 *
 * 3 source 별 lazy 로드:
 *   - prices  : gov/prices/date/{year}.parquet + raw-{year-1}.parquet UNION → 1Y window
 *               currentPrice/marketCap/ma20/high-low/return1m/3m/1y/volatility1y/spark
 *   - valuation: dart/scan/valuation.parquet → per/pbr/dividendYield/marketCap (Naver)
 *   - changes  : dart/scan/changes.parquet → 1Y numeric/structural/total 변경 카운트
 *
 * 책임: Map<stockCode|ISU_CD, …> 반환. 호출자가 ScanNode 와 join.
 *
 * 주: PR-B 단계는 현 `/screener` 의 검증된 SQL 를 그대로 lift. 5Y monthly cell hover
 * 시계열은 PR-D 디테일 패널에서. PR-B 는 60일 sparkline 만 활용.
 */

// duckdb 접근은 셸이 주입한다 · surfaces(vanilla svelte)는 SvelteKit/Vite 전용 $lib/data/duckdb
// ($app/environment·@vite-ignore·OPFS)에 직접 결합하지 않는다(viewer financeQuery seam 동형, queryStream/persisted 등
// scan 사용 멤버 포함). landing 컴포지션 루트가 provideScanDuckDb(loadDartDb) 주입. 미주입(또는 기기 제약) = null → 정직 강등.
export interface DartDb {
	readonly persisted: boolean;
	readonly opfsRebuilt: boolean;
	query<T = Record<string, unknown>>(sql: string): Promise<T[]>;
	queryStream<T = Record<string, unknown>>(sql: string): AsyncGenerator<T[], void, void>;
	registerHfParquet(viewName: string, hfPath: string): Promise<void>;
	registerJson(tableName: string, rows: unknown[]): Promise<void>;
	close(): Promise<void>;
}
let scanDuckDbProvider: (() => Promise<DartDb | null>) | null = null;
export function provideScanDuckDb(provider: () => Promise<DartDb | null>): void {
	scanDuckDbProvider = provider;
}
function loadDartDb(): Promise<DartDb | null> {
	return scanDuckDbProvider ? scanDuckDbProvider() : Promise.resolve(null);
}
// SQL 단일인용 escape · 1줄 순수 유틸(옛 $lib/data/duckdb.sqlEscape 인라인 · 결합 절제).
function sqlEscape(value: string): string {
	return value.replace(/'/g, "''");
}

/** persisted DB 의 특정 테이블 존재 여부. db.persisted 가 true 일 때만 의미. */
async function persistedHas(db: DartDb, tableName: string): Promise<boolean> {
	if (!db.persisted) return false;
	try {
		const r = await db.query<{ n: number }>(
			`SELECT COUNT(*) AS n FROM information_schema.tables
			 WHERE table_schema = 'persisted' AND table_name = '${tableName}'`
		);
		return Number(r[0]?.n ?? 0) > 0;
	} catch {
		return false;
	}
}

/** KRX prices 1Y window view 등록 (krxPrices 라는 이름으로). */
async function setupKrxPricesView(db: DartDb): Promise<void> {
	const year = new Date().getFullYear();
	await db.registerHfParquet('krxPricesCurr', `gov/prices/date/${year}.parquet`);
	try {
		await db.registerHfParquet('krxPricesPrev', `gov/prices/date/${year - 1}.parquet`);
		await db.query(
			`CREATE OR REPLACE VIEW krxPrices AS SELECT * FROM krxPricesCurr UNION ALL SELECT * FROM krxPricesPrev`
		);
	} catch (errPrev) {
		console.warn(`[scan] 직전 연도 parquet 등록 실패 · 현재 연도만`, errPrev);
		await db.query(`CREATE OR REPLACE VIEW krxPrices AS SELECT * FROM krxPricesCurr`);
	}
}

export type DbState = 'idle' | 'loading' | 'ready' | 'unsupported' | 'error';

export interface PriceMetrics {
	currentPrice: number | null;
	marketCap: number | null;
	ma20: number | null;
	high60: number | null;
	low60: number | null;
	week52High: number | null;
	week52Low: number | null;
	volumeAvg30d: number | null;
	volatility1y: number | null;
	return1m: number | null;
	return3m: number | null;
	return1y: number | null;
	/** 30거래일 종가 (초단기 추세). */
	spark30: number[];
	/** 60거래일 종가 (단기 추세). */
	spark60: number[];
	/** 1년(252거래일) 종가 (5일 다운샘플 ≈ 50포인트). cell sparkline + hover 차트 공용. */
	spark: number[];
}

export interface ValuationMetrics {
	per: number | null;
	pbr: number | null;
	dividendYield: number | null;
	marketCap: number | null;
}

export interface ChangeMetrics {
	numericChanges1y: number;
	structuralChanges1y: number;
	totalChanges1y: number;
	recentChangeYear: number | null;
}

export interface FinanceLiteMetrics {
	revenue: number | null;
	opMargin: number | null;
	roe: number | null;
	debtRatio: number | null;
}

export interface UniverseNode {
	id: string;
	label: string;
	industry: string;
	industryName: string;
	market: string;
	currentPrice: number | null;
	marketCap: number | null;
	per: number | null;
	pbr: number | null;
	dividendYield: number | null;
	revenue: number | null;
	opMargin: number | null;
	roe: number | null;
	debtRatio: number | null;
	color: string;
}

const num = (v: unknown): number | null => {
	if (v === null || v === undefined) return null;
	const n = Number(v);
	return Number.isFinite(n) ? n : null;
};

const pctReturn = (curr: number | null, past: number | null): number | null => {
	if (curr == null || past == null || past === 0) return null;
	return (curr / past - 1) * 100;
};

/** ISU_CD → stockCode (A005930 → 005930). */
export function isuCdToStockCode(isuCd: string): string {
	if (!isuCd) return '';
	return isuCd.startsWith('A') ? isuCd.slice(1) : isuCd;
}

/** DuckDB 인스턴스화만. parquet 등록·SQL 은 호출자가 단계별로 진행. */
export async function ensureDuckDb(): Promise<{ db: DartDb | null; state: DbState; error?: string }> {
	console.info('[scan] DuckDB 인스턴스 시작');
	const t0 = performance.now();
	try {
		const db = await loadDartDb();
		if (!db) {
			console.warn('[scan] DuckDB 사용 불가 (iOS Safari 또는 환경 미지원)');
			return { db: null, state: 'unsupported' };
		}
		console.info(`[scan] DuckDB ready (${(performance.now() - t0).toFixed(0)}ms)`);
		return { db, state: 'ready' };
	} catch (err) {
		const message = err instanceof Error ? err.message : String(err);
		console.error('[scan] DuckDB 인스턴스화 예외', err);
		return { db: null, state: 'error', error: message };
	}
}

/** Phase 1 · latest snapshot 만. 현재가 + 시총만. 매우 가볍.
 *
 *  - 한 raw-{year}.parquet 만 등록 (직전 연도 X)
 *  - WINDOW + LAG + 252-day aggregate 모두 X
 *  - 회사당 마지막 거래일 row 1개만 read
 *
 * 결과: PriceMetrics 의 currentPrice + marketCap 만 채움. 나머지 null.
 */
export async function loadPriceSnapshot(db: DartDb): Promise<Map<string, PriceMetrics>> {
	const t0 = performance.now();
	const year = new Date().getFullYear();
	try {
		await db.registerHfParquet('krxPricesCurr', `gov/prices/date/${year}.parquet`);
		const rows = await db.query<{
			ISU_CD: string;
			currentPrice: number | null;
			marketCap: number | null;
		}>(`
			WITH ranked AS (
				SELECT
					ISU_CD,
					CAST(TDD_CLSPRC AS DOUBLE) AS close,
					CAST(MKTCAP AS DOUBLE) AS mktcap,
					ROW_NUMBER() OVER (PARTITION BY ISU_CD ORDER BY BAS_DD DESC) AS rn
				FROM krxPricesCurr
			)
			SELECT ISU_CD, close AS currentPrice, mktcap AS marketCap
			FROM ranked WHERE rn = 1
		`);
		const map = new Map<string, PriceMetrics>();
		for (const r of rows) {
			const code = isuCdToStockCode(r.ISU_CD);
			if (!code) continue;
			map.set(code, {
				currentPrice: num(r.currentPrice),
				marketCap: num(r.marketCap),
				ma20: null,
				high60: null,
				low60: null,
				week52High: null,
				week52Low: null,
				volumeAvg30d: null,
				volatility1y: null,
				return1m: null,
				return3m: null,
				return1y: null,
				spark30: [],
				spark60: [],
				spark: []
			});
		}
		console.info(
			`[scan] ✅ Phase 1 snapshot · ${map.size}사 (${(performance.now() - t0).toFixed(0)}ms)`
		);
		return map;
	} catch (err) {
		console.error('[scan] ❌ Phase 1 snapshot SQL 실패', err);
		return new Map();
	}
}

/** HF parquet 만으로 /scan 초기 유니버스를 구성한다. 로컬 ecosystem 집계 JSON 을 쓰지 않는다.
 *
 * 첫 화면 속도를 위해 scan universe 는 KRX latest row + valuation 만 읽는다.
 * finance-lite, 1Y prices, changes 는 사용자가 해당 컬럼을 켤 때 lazy 로드한다.
 */
export async function loadUniverseSnapshot(db: DartDb): Promise<UniverseNode[]> {
	const year = new Date().getFullYear();
	try {
		await db.registerHfParquet('scanPricesCurr', `gov/prices/date/${year}.parquet`);
		await db.registerHfParquet('scanValuation', 'dart/scan/valuation.parquet');

		const rows = await db.query<{
			stockCode: string;
			corpName: string;
			market: string;
			currentPrice: number | null;
			marketCap: number | null;
			per: number | null;
			pbr: number | null;
			dividendYield: number | null;
		}>(`
			WITH latest_price AS (
				SELECT
					ISU_CD AS stockCode,
					ISU_NM AS corpName,
					MKT_NM AS market,
					CAST(TDD_CLSPRC AS DOUBLE) AS currentPrice,
					CAST(MKTCAP AS DOUBLE) AS marketCap,
					ROW_NUMBER() OVER (PARTITION BY ISU_CD ORDER BY BAS_DD DESC) AS rn
				FROM scanPricesCurr
			)
			SELECT
				p.stockCode,
				p.corpName,
				p.market,
				p.currentPrice,
				COALESCE(v.marketCap, p.marketCap) AS marketCap,
				v.per,
				v.pbr,
				v.dividendYield
			FROM latest_price p
			LEFT JOIN scanValuation v ON v.stockCode = p.stockCode
			WHERE p.rn = 1
		`);

		return rows
			.filter((r) => r.stockCode && r.corpName)
			.map((r) => {
				return {
					id: r.stockCode,
					label: r.corpName,
					industry: r.market || 'KRX',
					industryName: r.market || 'KRX',
					market: r.market || 'KRX',
					currentPrice: num(r.currentPrice),
					marketCap: num(r.marketCap),
					per: num(r.per),
					pbr: num(r.pbr),
					dividendYield: num(r.dividendYield),
					revenue: null,
					opMargin: null,
					roe: null,
					debtRatio: null,
					color: marketColorForNode(r.market)
				};
			});
	} catch (err) {
		console.warn('[scan] HF universe parquet 로드 실패', err);
		return [];
	}
}

function marketColorForNode(market: string | null | undefined): string {
	if (market === 'KOSPI') return '#60a5fa';
	if (market === 'KOSDAQ') return '#22c55e';
	if (market === 'KONEX') return '#f59e0b';
	return '#94a3b8';
}

/** finance-lite.parquet 에서 전종목 핵심 재무비율을 lazy 로드한다. */
export async function loadFinanceLiteMetrics(db: DartDb): Promise<Map<string, FinanceLiteMetrics>> {
	const t0 = performance.now();
	try {
		await db.registerHfParquet('scanFinanceLite', 'dart/scan/finance-lite.parquet');
		const rows = await db.query<{
			stockCode: string;
			revenue: number | null;
			op: number | null;
			net: number | null;
			equity: number | null;
			currentLiab: number | null;
			noncurrentLiab: number | null;
		}>(`
			WITH latest_fin_year AS (
				SELECT stockCode, MAX(TRY_CAST(bsns_year AS INTEGER)) AS y
				FROM scanFinanceLite
				WHERE fs_nm = '연결재무제표'
				  AND reprt_nm = '4분기'
				  AND stockCode IS NOT NULL
				GROUP BY stockCode
			)
			SELECT
				f.stockCode,
				MAX(CASE WHEN account_id = 'ifrs-full_Revenue'
					THEN TRY_CAST(REPLACE(thstrm_amount, ',', '') AS DOUBLE) END) AS revenue,
				MAX(CASE WHEN account_id = 'dart_OperatingIncomeLoss'
					THEN TRY_CAST(REPLACE(thstrm_amount, ',', '') AS DOUBLE) END) AS op,
				MAX(CASE WHEN account_id = 'ifrs-full_ProfitLoss'
					THEN TRY_CAST(REPLACE(thstrm_amount, ',', '') AS DOUBLE) END) AS net,
				MAX(CASE WHEN account_id = 'ifrs-full_Equity'
					THEN TRY_CAST(REPLACE(thstrm_amount, ',', '') AS DOUBLE) END) AS equity,
				MAX(CASE WHEN account_id = 'ifrs-full_CurrentLiabilities'
					THEN TRY_CAST(REPLACE(thstrm_amount, ',', '') AS DOUBLE) END) AS currentLiab,
				MAX(CASE WHEN account_id = 'ifrs-full_NoncurrentLiabilities'
					THEN TRY_CAST(REPLACE(thstrm_amount, ',', '') AS DOUBLE) END) AS noncurrentLiab
			FROM scanFinanceLite f
			JOIN latest_fin_year y
			  ON y.stockCode = f.stockCode
			 AND y.y = TRY_CAST(f.bsns_year AS INTEGER)
			WHERE f.fs_nm = '연결재무제표'
			  AND f.reprt_nm = '4분기'
			GROUP BY f.stockCode
		`);
		const map = new Map<string, FinanceLiteMetrics>();
		for (const r of rows) {
			if (!r.stockCode) continue;
			const revenue = num(r.revenue);
			const op = num(r.op);
			const net = num(r.net);
			const equity = num(r.equity);
			const liabilities = (num(r.currentLiab) ?? 0) + (num(r.noncurrentLiab) ?? 0);
			map.set(r.stockCode, {
				revenue,
				opMargin: revenue && op != null ? (op / revenue) * 100 : null,
				roe: equity && net != null ? (net / equity) * 100 : null,
				debtRatio: equity ? (liabilities / equity) * 100 : null
			});
		}
		console.info(
			`[scan] ✅ finance-lite metrics · ${map.size}사 (${(performance.now() - t0).toFixed(0)}ms)`
		);
		return map;
	} catch (err) {
		console.warn('[scan] finance-lite metrics 로드 실패', err);
		return new Map();
	}
}

/** PRICES_MAIN_SQL · main aggregate (spark 제외, 빠름). */
const PRICES_MAIN_SQL = `
	WITH ranked AS (
		SELECT
			ISU_CD,
			BAS_DD,
			CAST(TDD_CLSPRC AS DOUBLE) AS close,
			CAST(TDD_HGPRC AS DOUBLE) AS high,
			CAST(TDD_LWPRC AS DOUBLE) AS low,
			CAST(ACC_TRDVOL AS DOUBLE) AS volume,
			CAST(MKTCAP AS DOUBLE) AS mktcap,
			ROW_NUMBER() OVER (PARTITION BY ISU_CD ORDER BY BAS_DD DESC) AS rn
		FROM krxPrices
	),
	last252 AS (SELECT * FROM ranked WHERE rn <= 252),
	latest AS (SELECT ISU_CD, close AS currentPrice, mktcap AS marketCap FROM last252 WHERE rn = 1),
	ma20 AS (SELECT ISU_CD, AVG(close) AS ma20 FROM last252 WHERE rn <= 20 GROUP BY ISU_CD),
	bounds60 AS (
		SELECT ISU_CD, MAX(high) AS high60, MIN(low) AS low60
		FROM last252 WHERE rn <= 60 GROUP BY ISU_CD
	),
	bounds252 AS (
		SELECT ISU_CD, MAX(high) AS week52High, MIN(low) AS week52Low
		FROM last252 GROUP BY ISU_CD
	),
	volavg30 AS (
		SELECT ISU_CD, AVG(volume) AS volumeAvg30d
		FROM last252 WHERE rn <= 30 GROUP BY ISU_CD
	),
	prev21 AS (SELECT ISU_CD, close AS prev21 FROM last252 WHERE rn = 21),
	prev63 AS (SELECT ISU_CD, close AS prev63 FROM last252 WHERE rn = 63),
	prev252 AS (SELECT ISU_CD, close AS prev252 FROM last252 WHERE rn = 252),
	logret AS (
		SELECT ISU_CD,
			CASE WHEN close > 0 AND LAG(close) OVER (PARTITION BY ISU_CD ORDER BY BAS_DD) > 0
				THEN LN(close / LAG(close) OVER (PARTITION BY ISU_CD ORDER BY BAS_DD))
				ELSE NULL END AS lnret
		FROM last252
	),
	vol AS (
		SELECT ISU_CD, STDDEV_SAMP(lnret) * SQRT(252) * 100 AS volatility1y
		FROM logret WHERE lnret IS NOT NULL GROUP BY ISU_CD
	)
	SELECT
		l.ISU_CD,
		l.currentPrice, l.marketCap,
		m.ma20,
		b60.high60, b60.low60,
		b252.week52High, b252.week52Low,
		va.volumeAvg30d,
		v.volatility1y,
		p21.prev21, p63.prev63, p252.prev252
	FROM latest l
	LEFT JOIN ma20 m USING (ISU_CD)
	LEFT JOIN bounds60 b60 USING (ISU_CD)
	LEFT JOIN bounds252 b252 USING (ISU_CD)
	LEFT JOIN volavg30 va USING (ISU_CD)
	LEFT JOIN vol v USING (ISU_CD)
	LEFT JOIN prev21 p21 USING (ISU_CD)
	LEFT JOIN prev63 p63 USING (ISU_CD)
	LEFT JOIN prev252 p252 USING (ISU_CD)
`;

/** SPARK60_SQL · 60거래일 종가 array. 단기 모멘텀 column. */
const SPARK60_SQL = `
	WITH ranked AS (
		SELECT
			ISU_CD,
			BAS_DD,
			CAST(TDD_CLSPRC AS DOUBLE) AS close,
			ROW_NUMBER() OVER (PARTITION BY ISU_CD ORDER BY BAS_DD DESC) AS rn
		FROM krxPrices
	)
	SELECT ISU_CD, LIST(close ORDER BY BAS_DD ASC) AS spark60
	FROM ranked
	WHERE rn <= 60
	GROUP BY ISU_CD
`;

/** SPARK_SQL · 1Y(252거래일) 종가 array, 5일 다운샘플 ≈ 50포인트. cell sparkline + hover 차트 공용. */
const SPARK_SQL = `
	WITH ranked AS (
		SELECT
			ISU_CD,
			BAS_DD,
			CAST(TDD_CLSPRC AS DOUBLE) AS close,
			ROW_NUMBER() OVER (PARTITION BY ISU_CD ORDER BY BAS_DD DESC) AS rn
		FROM krxPrices
	)
	SELECT ISU_CD, LIST(close ORDER BY BAS_DD ASC) AS spark
	FROM ranked
	WHERE rn <= 252 AND rn % 5 = 0
	GROUP BY ISU_CD
`;

interface PriceRow {
	ISU_CD: string;
	currentPrice: number | null;
	marketCap: number | null;
	ma20: number | null;
	high60: number | null;
	low60: number | null;
	week52High: number | null;
	week52Low: number | null;
	volumeAvg30d: number | null;
	volatility1y: number | null;
	prev21: number | null;
	prev63: number | null;
	prev252: number | null;
	spark60: number[] | null;
	spark: number[] | null;
}

/** Promise + timeout · N초 안에 안 끝나면 throw. */
function withTimeout<T>(p: Promise<T>, ms: number, label: string): Promise<T> {
	return Promise.race([
		p,
		new Promise<T>((_, reject) =>
			setTimeout(() => reject(new Error(`${label} timeout ${ms}ms`)), ms)
		)
	]);
}

/** Phase 2 · main aggregate (가벼운 SQL) + spark 별도 query. spark 가 hang 해도 main 은 결과 나옴. */
export async function loadPriceMetrics(db: DartDb): Promise<Map<string, PriceMetrics>> {
	const t0 = performance.now();
	const map = new Map<string, PriceMetrics>();

	// 1. parquet view 등록 (10초 timeout)
	try {
		console.info('[scan] KRX parquet 등록 시작…');
		await withTimeout(setupKrxPricesView(db), 30_000, 'KRX parquet 등록');
		console.info(`[scan] ✅ KRX parquet 등록 완료 (${(performance.now() - t0).toFixed(0)}ms)`);
	} catch (err) {
		console.error('[scan] ❌ KRX parquet 등록 실패', err);
		return map;
	}

	// 2. main aggregate SQL (currentPrice, marketCap, return, vol, week52 등) · spark 제외, 가벼움
	const tMain = performance.now();
	try {
		console.info('[scan] KRX main aggregate SQL 시작…');
		const rows = await withTimeout(
			db.query<Omit<PriceRow, 'spark'>>(PRICES_MAIN_SQL),
			60_000,
			'KRX main aggregate'
		);
		for (const r of rows) {
			const code = isuCdToStockCode(r.ISU_CD);
			if (!code) continue;
			const currentPrice = num(r.currentPrice);
			map.set(code, {
				currentPrice,
				marketCap: num(r.marketCap),
				ma20: num(r.ma20),
				high60: num(r.high60),
				low60: num(r.low60),
				week52High: num(r.week52High),
				week52Low: num(r.week52Low),
				volumeAvg30d: num(r.volumeAvg30d),
				volatility1y: num(r.volatility1y),
				return1m: pctReturn(currentPrice, num(r.prev21)),
				return3m: pctReturn(currentPrice, num(r.prev63)),
				return1y: pctReturn(currentPrice, num(r.prev252)),
				spark30: [],
				spark60: [],
				spark: []
			});
		}
		console.info(
			`[scan] ✅ KRX main aggregate · ${map.size}사 (${(performance.now() - tMain).toFixed(0)}ms)`
		);
	} catch (err) {
		console.error('[scan] ❌ KRX main aggregate SQL 실패', err);
		return map;
	}

	// 3. 60D spark 별도 query · hang 해도 main 결과는 보존 (20초 timeout)
	try {
		const tSpark60 = performance.now();
		console.info('[scan] KRX spark 60D SQL 시작…');
		const spark60Rows = await withTimeout(
			db.query<{ ISU_CD: string; spark60: number[] | null }>(SPARK60_SQL),
			20_000,
			'KRX spark 60D'
		);
		let merged = 0;
		for (const r of spark60Rows) {
			const code = isuCdToStockCode(r.ISU_CD);
			if (!code) continue;
			const existing = map.get(code);
			if (existing) {
				existing.spark60 = toPlainNumberArray(r.spark60);
				existing.spark30 = existing.spark60.slice(-30);
				merged++;
			}
		}
		console.info(
			`[scan] ✅ KRX spark 60D · ${merged}사 (${(performance.now() - tSpark60).toFixed(0)}ms)`
		);
	} catch (err) {
		console.warn('[scan] ⚠ KRX spark 60D 별도 query 실패 · main 결과만 반환', err);
	}

	// 4. 1Y spark 별도 query · hang 해도 main 결과는 보존 (30초 timeout)
	try {
		const tSpark = performance.now();
		console.info('[scan] KRX spark 1Y SQL 시작…');
		const sparkRows = await withTimeout(
			db.query<{ ISU_CD: string; spark: number[] | null }>(SPARK_SQL),
			30_000,
			'KRX spark'
		);
		let merged = 0;
		// 디버그 · 첫 row 의 spark 컬럼 타입 확인
		if (sparkRows.length > 0) {
			const first = sparkRows[0];
			console.info(
				`[scan] spark sample · type=${typeof first.spark}, isArray=${Array.isArray(first.spark)}, ctor=${first.spark?.constructor?.name}, len=${(first.spark as any)?.length}`
			);
		}
		for (const r of sparkRows) {
			const code = isuCdToStockCode(r.ISU_CD);
			if (!code) continue;
			const existing = map.get(code);
			if (existing) {
				existing.spark = toPlainNumberArray(r.spark);
				merged++;
			}
		}
		console.info(
			`[scan] ✅ KRX spark 1Y · ${merged}사 (${(performance.now() - tSpark).toFixed(0)}ms)`
		);
	} catch (err) {
		console.warn('[scan] ⚠ KRX spark 별도 query 실패 · main 결과만 반환', err);
	}

	return map;
}

function toPlainNumberArray(value: Iterable<number> | null | undefined): number[] {
	if (value == null) return [];
	try {
		return Array.from(value, (v) => Number(v)).filter((v) => Number.isFinite(v));
	} catch {
		return [];
	}
}

/** valuation.parquet → PER/PBR/배당수익률/시총 (Naver, 매일 KST 04:00 갱신). */
export async function loadValuation(db: DartDb): Promise<Map<string, ValuationMetrics>> {
	const t0 = performance.now();
	try {
		await db.registerHfParquet('valuation', 'dart/scan/valuation.parquet');
		const rows = await db.query<{
			stockCode: string;
			per: number | null;
			pbr: number | null;
			dividendYield: number | null;
			marketCap: number | null;
		}>(`
			SELECT
				stockCode,
				CAST(per AS DOUBLE) AS per,
				CAST(pbr AS DOUBLE) AS pbr,
				CAST(dividendYield AS DOUBLE) AS dividendYield,
				CAST(marketCap AS DOUBLE) AS marketCap
			FROM valuation
		`);
		const map = new Map<string, ValuationMetrics>();
		for (const r of rows) {
			if (!r.stockCode) continue;
			map.set(r.stockCode, {
				per: num(r.per),
				pbr: num(r.pbr),
				dividendYield: num(r.dividendYield),
				marketCap: num(r.marketCap)
			});
		}
		console.info(
			`[scan] ✅ valuation · ${map.size}사 (${(performance.now() - t0).toFixed(0)}ms)`
		);
		return map;
	} catch (err) {
		console.warn('[scan] valuation.parquet 로드 실패', err);
		return new Map();
	}
}

/** changes.parquet → 1Y 공시 변경 카운트 + 최근 변경 연도. */
export async function loadChanges(db: DartDb): Promise<Map<string, ChangeMetrics>> {
	const t0 = performance.now();
	try {
		await db.registerHfParquet('changes', 'dart/scan/changes.parquet');
		const currentYear = new Date().getFullYear();
		const lastYear = currentYear - 1;
		const rows = await db.query<{
			stockCode: string;
			numericChanges1y: number;
			structuralChanges1y: number;
			totalChanges1y: number;
			recentChangeYear: number | null;
		}>(`
			SELECT
				stockCode,
				COUNT(*) FILTER (WHERE changeType = 'numeric' AND CAST(toPeriod AS INTEGER) IN (${currentYear}, ${lastYear})) AS numericChanges1y,
				COUNT(*) FILTER (WHERE changeType = 'structural' AND CAST(toPeriod AS INTEGER) IN (${currentYear}, ${lastYear})) AS structuralChanges1y,
				COUNT(*) FILTER (WHERE CAST(toPeriod AS INTEGER) IN (${currentYear}, ${lastYear})) AS totalChanges1y,
				MAX(CAST(toPeriod AS INTEGER)) AS recentChangeYear
			FROM changes
			WHERE stockCode IS NOT NULL
			GROUP BY stockCode
		`);
		const map = new Map<string, ChangeMetrics>();
		for (const r of rows) {
			map.set(r.stockCode, {
				numericChanges1y: Number(r.numericChanges1y) || 0,
				structuralChanges1y: Number(r.structuralChanges1y) || 0,
				totalChanges1y: Number(r.totalChanges1y) || 0,
				recentChangeYear: r.recentChangeYear != null ? Number(r.recentChangeYear) : null
			});
		}
		console.info(
			`[scan] ✅ changes · ${map.size}사 (${(performance.now() - t0).toFixed(0)}ms)`
		);
		return map;
	} catch (err) {
		console.warn('[scan] changes.parquet 로드 실패', err);
		return new Map();
	}
}

/** 한 회사의 60거래일 종가 (cell hover sparkline). prices map 에 이미 있어 빠른 lookup. */
export function getSparkForCompany(
	priceMap: Map<string, PriceMetrics>,
	stockCode: string
): number[] {
	return priceMap.get(stockCode)?.spark ?? [];
}

// ── Streaming variants (PR-β) ────────────────────────
//
// generator 가 chunk 단위 (2048 row 까지) Map 으로 yield.
// caller 가 progressive 하게 main map 에 merge · 첫 batch 가 < 1초 안에 시각화.

const PRICES_SQL = `
	WITH ranked AS (
		SELECT
			ISU_CD,
			BAS_DD,
			CAST(TDD_CLSPRC AS DOUBLE) AS close,
			CAST(TDD_HGPRC AS DOUBLE) AS high,
			CAST(TDD_LWPRC AS DOUBLE) AS low,
			CAST(ACC_TRDVOL AS DOUBLE) AS volume,
			CAST(MKTCAP AS DOUBLE) AS mktcap,
			ROW_NUMBER() OVER (PARTITION BY ISU_CD ORDER BY BAS_DD DESC) AS rn
		FROM krxPrices
	),
	last252 AS (SELECT * FROM ranked WHERE rn <= 252),
	latest AS (SELECT ISU_CD, close AS currentPrice, mktcap AS marketCap FROM last252 WHERE rn = 1),
	ma20 AS (SELECT ISU_CD, AVG(close) AS ma20 FROM last252 WHERE rn <= 20 GROUP BY ISU_CD),
	bounds60 AS (
		SELECT ISU_CD, MAX(high) AS high60, MIN(low) AS low60
		FROM last252 WHERE rn <= 60 GROUP BY ISU_CD
	),
	bounds252 AS (
		SELECT ISU_CD, MAX(high) AS week52High, MIN(low) AS week52Low
		FROM last252 GROUP BY ISU_CD
	),
	volavg30 AS (
		SELECT ISU_CD, AVG(volume) AS volumeAvg30d
		FROM last252 WHERE rn <= 30 GROUP BY ISU_CD
	),
	prev21 AS (SELECT ISU_CD, close AS prev21 FROM last252 WHERE rn = 21),
	prev63 AS (SELECT ISU_CD, close AS prev63 FROM last252 WHERE rn = 63),
	prev252 AS (SELECT ISU_CD, close AS prev252 FROM last252 WHERE rn = 252),
	logret AS (
		SELECT ISU_CD,
			CASE WHEN close > 0 AND LAG(close) OVER (PARTITION BY ISU_CD ORDER BY BAS_DD) > 0
				THEN LN(close / LAG(close) OVER (PARTITION BY ISU_CD ORDER BY BAS_DD))
				ELSE NULL END AS lnret
		FROM last252
	),
	vol AS (
		SELECT ISU_CD, STDDEV_SAMP(lnret) * SQRT(252) * 100 AS volatility1y
		FROM logret WHERE lnret IS NOT NULL GROUP BY ISU_CD
	),
	spark AS (
		SELECT ISU_CD, ARRAY_AGG(close ORDER BY BAS_DD ASC) AS spark
		FROM last252 WHERE rn <= 60 AND rn % 4 = 0
		GROUP BY ISU_CD
	)
	SELECT
		l.ISU_CD,
		l.currentPrice, l.marketCap,
		m.ma20,
		b60.high60, b60.low60,
		b252.week52High, b252.week52Low,
		va.volumeAvg30d,
		v.volatility1y,
		p21.prev21, p63.prev63, p252.prev252,
		s.spark
	FROM latest l
	LEFT JOIN ma20 m USING (ISU_CD)
	LEFT JOIN bounds60 b60 USING (ISU_CD)
	LEFT JOIN bounds252 b252 USING (ISU_CD)
	LEFT JOIN volavg30 va USING (ISU_CD)
	LEFT JOIN vol v USING (ISU_CD)
	LEFT JOIN prev21 p21 USING (ISU_CD)
	LEFT JOIN prev63 p63 USING (ISU_CD)
	LEFT JOIN prev252 p252 USING (ISU_CD)
	LEFT JOIN spark s USING (ISU_CD)
`;

/** PR-β · KRX prices SQL 결과를 batch 단위 yield. caller 가 main map 에 merge. */
export async function* loadPriceMetricsStream(
	db: DartDb
): AsyncGenerator<Map<string, PriceMetrics>, void, void> {
	const t0 = performance.now();
	const year = new Date().getFullYear();
	try {
		await db.registerHfParquet('krxPricesCurr', `gov/prices/date/${year}.parquet`);
		try {
			await db.registerHfParquet('krxPricesPrev', `gov/prices/date/${year - 1}.parquet`);
			await db.query(
				`CREATE OR REPLACE VIEW krxPrices AS SELECT * FROM krxPricesCurr UNION ALL SELECT * FROM krxPricesPrev`
			);
		} catch (errPrev) {
			console.warn(`[scan] 직전 연도 parquet 등록 실패 · 현재 연도만`, errPrev);
			await db.query(`CREATE OR REPLACE VIEW krxPrices AS SELECT * FROM krxPricesCurr`);
		}
		let totalRows = 0;
		for await (const rows of db.queryStream<{
			ISU_CD: string;
			currentPrice: number | null;
			marketCap: number | null;
			ma20: number | null;
			high60: number | null;
			low60: number | null;
			week52High: number | null;
			week52Low: number | null;
			volumeAvg30d: number | null;
			volatility1y: number | null;
			prev21: number | null;
			prev63: number | null;
			prev252: number | null;
			spark: number[] | null;
		}>(PRICES_SQL)) {
			const chunk = new Map<string, PriceMetrics>();
			for (const r of rows) {
				const code = isuCdToStockCode(r.ISU_CD);
				if (!code) continue;
				const currentPrice = num(r.currentPrice);
				const sparkArr = Array.isArray(r.spark)
					? r.spark.map((v) => Number(v)).filter((v) => Number.isFinite(v))
					: [];
				chunk.set(code, {
					currentPrice,
					marketCap: num(r.marketCap),
					ma20: num(r.ma20),
					high60: num(r.high60),
					low60: num(r.low60),
					week52High: num(r.week52High),
					week52Low: num(r.week52Low),
					volumeAvg30d: num(r.volumeAvg30d),
					volatility1y: num(r.volatility1y),
					return1m: pctReturn(currentPrice, num(r.prev21)),
					return3m: pctReturn(currentPrice, num(r.prev63)),
					return1y: pctReturn(currentPrice, num(r.prev252)),
					spark30: sparkArr.slice(-30),
					spark60: sparkArr.slice(-60),
					spark: sparkArr
				});
			}
			totalRows += chunk.size;
			if (chunk.size > 0) yield chunk;
		}
		console.info(
			`[scan] ✅ Streaming KRX prices · ${totalRows}사 (${(performance.now() - t0).toFixed(0)}ms)`
		);
	} catch (err) {
		console.error('[scan] ❌ Streaming prices SQL 실패', err);
	}
}

/** PR-β · valuation streaming. */
export async function* loadValuationStream(
	db: DartDb
): AsyncGenerator<Map<string, ValuationMetrics>, void, void> {
	const t0 = performance.now();
	try {
		await db.registerHfParquet('valuation', 'dart/scan/valuation.parquet');
		let totalRows = 0;
		for await (const rows of db.queryStream<{
			stockCode: string;
			per: number | null;
			pbr: number | null;
			dividendYield: number | null;
			marketCap: number | null;
		}>(`
			SELECT
				stockCode,
				CAST(per AS DOUBLE) AS per,
				CAST(pbr AS DOUBLE) AS pbr,
				CAST(dividendYield AS DOUBLE) AS dividendYield,
				CAST(marketCap AS DOUBLE) AS marketCap
			FROM valuation
		`)) {
			const chunk = new Map<string, ValuationMetrics>();
			for (const r of rows) {
				if (!r.stockCode) continue;
				chunk.set(r.stockCode, {
					per: num(r.per),
					pbr: num(r.pbr),
					dividendYield: num(r.dividendYield),
					marketCap: num(r.marketCap)
				});
			}
			totalRows += chunk.size;
			if (chunk.size > 0) yield chunk;
		}
		console.info(
			`[scan] ✅ Streaming valuation · ${totalRows}사 (${(performance.now() - t0).toFixed(0)}ms)`
		);
	} catch (err) {
		console.warn('[scan] valuation streaming 실패', err);
	}
}

/** PR-β · changes streaming. */
export async function* loadChangesStream(
	db: DartDb
): AsyncGenerator<Map<string, ChangeMetrics>, void, void> {
	const t0 = performance.now();
	const currentYear = new Date().getFullYear();
	const lastYear = currentYear - 1;
	try {
		await db.registerHfParquet('changes', 'dart/scan/changes.parquet');
		let totalRows = 0;
		for await (const rows of db.queryStream<{
			stockCode: string;
			numericChanges1y: number;
			structuralChanges1y: number;
			totalChanges1y: number;
			recentChangeYear: number | null;
		}>(`
			SELECT
				stockCode,
				COUNT(*) FILTER (WHERE changeType = 'numeric' AND CAST(toPeriod AS INTEGER) IN (${currentYear}, ${lastYear})) AS numericChanges1y,
				COUNT(*) FILTER (WHERE changeType = 'structural' AND CAST(toPeriod AS INTEGER) IN (${currentYear}, ${lastYear})) AS structuralChanges1y,
				COUNT(*) FILTER (WHERE CAST(toPeriod AS INTEGER) IN (${currentYear}, ${lastYear})) AS totalChanges1y,
				MAX(CAST(toPeriod AS INTEGER)) AS recentChangeYear
			FROM changes
			WHERE stockCode IS NOT NULL
			GROUP BY stockCode
		`)) {
			const chunk = new Map<string, ChangeMetrics>();
			for (const r of rows) {
				chunk.set(r.stockCode, {
					numericChanges1y: Number(r.numericChanges1y) || 0,
					structuralChanges1y: Number(r.structuralChanges1y) || 0,
					totalChanges1y: Number(r.totalChanges1y) || 0,
					recentChangeYear: r.recentChangeYear != null ? Number(r.recentChangeYear) : null
				});
			}
			totalRows += chunk.size;
			if (chunk.size > 0) yield chunk;
		}
		console.info(
			`[scan] ✅ Streaming changes · ${totalRows}사 (${(performance.now() - t0).toFixed(0)}ms)`
		);
	} catch (err) {
		console.warn('[scan] changes streaming 실패', err);
	}
}

// ── Per-company loaders (Detail 패널용) ───────────────

export interface FinanceYear {
	year: number;
	revenue: number | null;
	opProfit: number | null;
	netIncome: number | null;
	assets: number | null;
	liabilities: number | null;
}

export interface CompanyChange {
	fromPeriod: string;
	toPeriod: string;
	sectionTitle: string;
	changeType: string;
	preview: string | null;
}

/** 한 회사의 5Y 연간 재무 (5 계정). finance-lite.parquet long-form → JS pivot. */
export async function loadFinanceTimeseries(
	db: DartDb,
	stockCode: string
): Promise<FinanceYear[]> {
	try {
		await db.registerHfParquet('financeLite', 'dart/scan/finance-lite.parquet');
		// long-form raw · JS 에서 pivot. 5 계정만 추출.
		const rows = await db.query<{
			bsns_year: number;
			reprt_nm: string;
			account_id: string;
			thstrm_amount: number;
		}>(`
			SELECT
				CAST(bsns_year AS INTEGER) AS bsns_year,
				reprt_nm,
				account_id,
				CAST(thstrm_amount AS DOUBLE) AS thstrm_amount
			FROM financeLite
			WHERE stockCode = '${sqlEscape(stockCode)}'
			  AND account_id IN ('sales', 'operating_profit', 'net_income', 'assets', 'liabilities')
			  AND reprt_nm IN ('연간', '4분기', '사업보고서')
		`);

		// Pivot: year → { revenue, opProfit, netIncome, assets, liabilities }
		const byYear = new Map<number, FinanceYear>();
		for (const r of rows) {
			const y = Number(r.bsns_year);
			if (!Number.isFinite(y)) continue;
			let rec = byYear.get(y);
			if (!rec) {
				rec = {
					year: y,
					revenue: null,
					opProfit: null,
					netIncome: null,
					assets: null,
					liabilities: null
				};
				byYear.set(y, rec);
			}
			const v = num(r.thstrm_amount);
			if (v == null) continue;
			switch (r.account_id) {
				case 'sales':
					rec.revenue = v;
					break;
				case 'operating_profit':
					rec.opProfit = v;
					break;
				case 'net_income':
					rec.netIncome = v;
					break;
				case 'assets':
					rec.assets = v;
					break;
				case 'liabilities':
					rec.liabilities = v;
					break;
			}
		}
		return Array.from(byYear.values()).sort((a, b) => a.year - b.year);
	} catch (err) {
		console.warn('[scan] finance-lite per-company 로드 실패', err);
		return [];
	}
}

/** 한 회사의 최근 공시 변경 N 건. */
export async function loadCompanyChanges(
	db: DartDb,
	stockCode: string,
	limit = 3
): Promise<CompanyChange[]> {
	try {
		await db.registerHfParquet('changes', 'dart/scan/changes.parquet');
		const rows = await db.query<CompanyChange>(`
			SELECT
				fromPeriod,
				toPeriod,
				sectionTitle,
				changeType,
				NULLIF(TRIM(REGEXP_REPLACE(REGEXP_REPLACE(preview, '<[^>]+>', ' ', 'g'), '\\s+', ' ', 'g')), '') AS preview
			FROM changes
			WHERE stockCode = '${sqlEscape(stockCode)}'
			ORDER BY toPeriod DESC, sectionTitle
			LIMIT ${limit}
		`);
		return rows;
	} catch (err) {
		console.warn('[scan] changes per-company 로드 실패', err);
		return [];
	}
}
