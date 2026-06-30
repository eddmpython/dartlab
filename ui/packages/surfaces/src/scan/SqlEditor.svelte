<script lang="ts">
	/**
	 * Power user SQL Editor · DuckDB-WASM 직접 query (PR-δ).
	 *
	 * 등록 테이블 (8+):
	 *   In-memory (그리드 결과 재사용):
	 *     - ecosystem      : 회사 노드 (raw 41 필드 · id/label/industry/roe/opMargin/등급/Δ 등)
	 *     - prices         : KRX SQL 결과 (currentPrice/marketCap/return1y/spark[] 등)
	 *     - valuation_mem  : Naver API in-mem (per/pbr/dividendYield/marketCap)
	 *     - changes_mem    : 공시 변경 카운트 in-mem
	 *   HF parquet 직접 view (lazy SQL 시 fetch):
	 *     - finance_lite   : 회사×분기×계정 long-form (5Y 재무 시계열)
	 *     - valuation      : full valuation parquet (이름 같으면 mem 우선이라 _mem 분리)
	 *     - changes        : full changes parquet (모든 변경 raw)
	 *     - dividend       : dart/scan/report/dividend.parquet
	 *     - treasuryStock  : dart/scan/report/treasuryStock.parquet
	 *     - executive      : dart/scan/report/executive.parquet
	 *
	 * 좌측 panel: INFORMATION_SCHEMA 로 동적 테이블·컬럼 list. 컬럼 클릭 = textarea 삽입.
	 *
	 * 안전장치:
	 *   - SELECT/WITH/SHOW/DESCRIBE/EXPLAIN/PRAGMA 만 (DROP/INSERT/UPDATE 등 차단)
	 *   - 5초 timeout
	 *   - 결과 1만 row cap
	 */
	import type { DartDb } from './duckSql';
	import type { PriceMetrics, ValuationMetrics, ChangeMetrics } from './duckSql';

	interface Props {
		db: DartDb | null;
		ecosystem: unknown[];
		priceMap: Map<string, PriceMetrics>;
		valuationMap: Map<string, ValuationMetrics>;
		changesMap: Map<string, ChangeMetrics>;
	}

	let { db, ecosystem, priceMap, valuationMap, changesMap }: Props = $props();

	const PRESETS: { title: string; sql: string }[] = [
		{
			title: '시총 TOP 50 (prices + ecosystem join)',
			sql: `SELECT e.label, e.industryName, p.marketCap, e.roe, e.opMargin, p.return1y
FROM ecosystem e
LEFT JOIN prices p ON p.stockCode = e.id
WHERE p.marketCap IS NOT NULL
ORDER BY p.marketCap DESC
LIMIT 50`
		},
		{
			title: '산업별 평균 ROE',
			sql: `SELECT industryName, COUNT(*) AS 회사수, AVG(roe) AS avg_roe, AVG(opMargin) AS avg_opm
FROM ecosystem
WHERE roe IS NOT NULL
GROUP BY industryName
ORDER BY avg_roe DESC`
		},
		{
			title: '저PER + 우량 등급 (valuation join)',
			sql: `SELECT e.label, e.industryName, v.per, v.pbr, e.roe, e.qualGrade, v.dividendYield
FROM ecosystem e
JOIN valuation v ON v.stockCode = e.id
WHERE v.per BETWEEN 0 AND 10
  AND e.qualGrade IN ('우수', '양호')
ORDER BY v.per ASC LIMIT 50`
		},
		{
			title: '1Y 수익률 TOP + 흑자',
			sql: `SELECT e.label, e.industryName, p.return1y, e.roe, e.opMargin
FROM ecosystem e
JOIN prices p ON p.stockCode = e.id
WHERE p.return1y IS NOT NULL AND e.opMargin > 0
ORDER BY p.return1y DESC LIMIT 50`
		},
		{
			title: '부채비율 급증 회사',
			sql: `SELECT label, industryName, debtRatio, debtRatioDelta, icr, debtGrade
FROM ecosystem
WHERE debtRatioDelta > 30
ORDER BY debtRatioDelta DESC LIMIT 50`
		},
		{
			title: '공시 변경 활발 회사 (changes join)',
			sql: `SELECT e.label, e.industryName, c.numericChanges1y, c.structuralChanges1y, e.opMargin
FROM ecosystem e
JOIN changes_mem c ON c.stockCode = e.id
WHERE c.totalChanges1y > 5
ORDER BY c.totalChanges1y DESC LIMIT 50`
		},
		{
			title: '5Y 매출 추이 (finance_lite long-form)',
			sql: `SELECT e.label, f.bsns_year, f.thstrm_amount AS revenue
FROM finance_lite f
JOIN ecosystem e ON e.id = f.stockCode
WHERE f.account_id = 'sales'
  AND f.reprt_nm IN ('연간', '4분기', '사업보고서')
  AND e.id IN ('005930', '000660', '035720', '005380', '051910')
ORDER BY e.label, f.bsns_year`
		},
		{
			title: '배당 선언 회사 (dividend report)',
			sql: `SELECT e.label, e.industryName, d.*
FROM dividend d
JOIN ecosystem e ON e.id = d.stockCode
LIMIT 50`
		},
		{
			title: '자사주 매입 (treasuryStock report)',
			sql: `SELECT e.label, e.industryName, t.*
FROM treasuryStock t
JOIN ecosystem e ON e.id = t.stockCode
LIMIT 50`
		},
		{
			title: '임원 정보 (executive report)',
			sql: `SELECT e.label, x.*
FROM executive x
JOIN ecosystem e ON e.id = x.stockCode
LIMIT 50`
		}
	];

	let sql = $state(PRESETS[0].sql);
	let rows = $state<Record<string, unknown>[]>([]);
	let columns = $state<string[]>([]);
	let error = $state<string | null>(null);
	let loading = $state(false);
	let elapsed = $state<number | null>(null);
	let registered = $state(false);

	interface SchemaCol {
		table: string;
		column: string;
		type: string;
	}
	let schema = $state<SchemaCol[]>([]);

	const READONLY_RE = /^\s*(SELECT|WITH|SHOW|DESCRIBE|EXPLAIN|PRAGMA)\b/i;
	const DESTRUCTIVE_RE = /\b(DROP|DELETE|UPDATE|INSERT|CREATE|ALTER|ATTACH|DETACH|COPY|TRUNCATE)\b/i;

	async function ensureRegistered() {
		if (registered || !db) return;
		try {
			// ── in-memory (그리드가 이미 fetch 한 결과 재사용 · 빠름) ──
			await db.registerJson('ecosystem', ecosystem);
			if (priceMap.size > 0) {
				const arr = Array.from(priceMap.entries()).map(([stockCode, p]) => ({
					stockCode,
					...p
				}));
				await db.registerJson('prices', arr);
			}
			if (valuationMap.size > 0) {
				const arr = Array.from(valuationMap.entries()).map(([stockCode, v]) => ({
					stockCode,
					...v
				}));
				await db.registerJson('valuation_mem', arr);
			}
			if (changesMap.size > 0) {
				const arr = Array.from(changesMap.entries()).map(([stockCode, c]) => ({
					stockCode,
					...c
				}));
				await db.registerJson('changes_mem', arr);
			}

			// ── HF parquet view (lazy SQL 시점에 fetch · 첫 query 시 약간 지연) ──
			const lazyParquets: Array<[string, string]> = [
				['finance_lite', 'dart/scan/finance-lite.parquet'],
				['valuation', 'dart/scan/valuation.parquet'],
				['changes', 'dart/scan/changes.parquet'],
				['dividend', 'dart/scan/report/dividend.parquet'],
				['treasuryStock', 'dart/scan/report/treasuryStock.parquet'],
				['executive', 'dart/scan/report/executive.parquet']
			];
			for (const [view, path] of lazyParquets) {
				try {
					await db.registerHfParquet(view, path);
				} catch (err) {
					console.info(`[scan-sql] ${view} parquet skip · ${path}`, err);
				}
			}

			registered = true;
			await loadSchema();
		} catch (err) {
			console.warn('[scan-sql] register 실패', err);
		}
	}

	async function loadSchema() {
		if (!db) return;
		try {
			const result = await db.query<{
				table_name: string;
				column_name: string;
				data_type: string;
			}>(`
				SELECT table_name, column_name, data_type
				FROM information_schema.columns
				WHERE table_schema = 'main'
				ORDER BY table_name, ordinal_position
			`);
			schema = result.map((r) => ({
				table: String(r.table_name),
				column: String(r.column_name),
				type: String(r.data_type)
			}));
		} catch (err) {
			console.warn('[scan-sql] schema query 실패', err);
		}
	}

	async function runSql() {
		if (!db) {
			error = 'db 가 아직 준비 안 됐습니다 (그리드 로드 후 다시 시도).';
			return;
		}
		const trimmed = sql.trim();
		if (!trimmed) return;

		if (DESTRUCTIVE_RE.test(trimmed)) {
			error = '안전상 DROP/DELETE/UPDATE/INSERT/CREATE/ALTER/ATTACH 는 차단됩니다. SELECT 위주만 가능.';
			return;
		}
		if (!READONLY_RE.test(trimmed)) {
			error = 'SELECT / WITH / SHOW / DESCRIBE / EXPLAIN / PRAGMA 로 시작해야 합니다.';
			return;
		}

		loading = true;
		error = null;
		const t0 = performance.now();

		try {
			await ensureRegistered();
			const result = await Promise.race([
				db.query<Record<string, unknown>>(trimmed),
				new Promise<never>((_, reject) =>
					setTimeout(() => reject(new Error('5초 timeout · query 가 너무 오래 걸립니다')), 5000)
				)
			]);
			const cap = result.slice(0, 10000);
			rows = cap;
			columns = cap.length > 0 ? Object.keys(cap[0]) : [];
			elapsed = performance.now() - t0;
			if (result.length > 10000) {
				error = `1만 row 표시 (전체 ${result.length.toLocaleString()} row).`;
			}
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
			rows = [];
			columns = [];
			elapsed = null;
		} finally {
			loading = false;
		}
	}

	function applyPreset(p: { sql: string }) {
		sql = p.sql;
	}

	let textarea: HTMLTextAreaElement | undefined = $state(undefined);

	function insertAtCursor(text: string) {
		if (!textarea) {
			sql = sql + text;
			return;
		}
		const start = textarea.selectionStart ?? sql.length;
		const end = textarea.selectionEnd ?? sql.length;
		sql = sql.slice(0, start) + text + sql.slice(end);
		setTimeout(() => {
			if (textarea) {
				const pos = start + text.length;
				textarea.setSelectionRange(pos, pos);
				textarea.focus();
			}
		}, 0);
	}

	function fmtCell(v: unknown): string {
		if (v == null) return '·';
		if (Array.isArray(v)) return `[${v.length}]`;
		if (typeof v === 'number') {
			if (!Number.isFinite(v)) return '·';
			const fmt1 = (n: number) =>
				n.toLocaleString('ko-KR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
			if (Math.abs(v) >= 1e8) return fmt1(v / 1e8) + '억';
			if (Math.abs(v) >= 1e4) return fmt1(v / 1e4) + '만';
			if (Math.abs(v) < 1 && v !== 0) {
				return v.toLocaleString('ko-KR', { minimumFractionDigits: 3, maximumFractionDigits: 3 });
			}
			return v.toLocaleString('ko-KR', { maximumFractionDigits: 2 });
		}
		return String(v);
	}

	function handleKey(e: KeyboardEvent) {
		if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
			e.preventDefault();
			void runSql();
		}
	}

	// 진입 즉시 schema 로드 (그리드가 이미 init 완료한 상태)
	$effect(() => {
		if (db && !registered) void ensureRegistered();
	});

	// 테이블별 컬럼 그룹
	let schemaByTable = $derived.by(() => {
		const map = new Map<string, SchemaCol[]>();
		for (const s of schema) {
			if (!map.has(s.table)) map.set(s.table, []);
			map.get(s.table)!.push(s);
		}
		return map;
	});
</script>

<div class="sql-editor">
	<header class="se-head">
		<div class="se-title">
			<span class="se-eyebrow">SQL Editor</span>
			<span class="se-sub">4 테이블 attached</span>
		</div>
		<div class="se-actions">
			<button
				type="button"
				class="se-run"
				onclick={runSql}
				disabled={loading || !db}
				title="⌘Enter / Ctrl+Enter"
			>
				{#if loading}실행 중…{:else}▶ 실행{/if}
			</button>
		</div>
	</header>

	<div class="se-body">
		<aside class="se-sidebar">
			<div class="sec">
				<div class="sec-title">스키마</div>
				{#if schema.length === 0}
					<div class="sec-empty">db 준비 중…</div>
				{:else}
					{#each [...schemaByTable] as [table, cols] (table)}
						<details class="table-block" open={table === 'ecosystem' || table === 'prices'}>
							<summary class="table-name">
								<span class="t-name">{table}</span>
								<span class="t-count">{cols.length}</span>
							</summary>
							<ul class="col-list">
								{#each cols as c (c.column)}
									<li>
										<button
											type="button"
											class="col-btn"
											onclick={() => insertAtCursor(`${table}.${c.column}`)}
											title="클릭 = textarea 삽입"
										>
											<span class="c-name">{c.column}</span>
											<span class="c-type">{c.type}</span>
										</button>
									</li>
								{/each}
							</ul>
						</details>
					{/each}
				{/if}
			</div>

			<div class="sec">
				<div class="sec-title">프리셋</div>
				{#each PRESETS as p, i (i)}
					<button type="button" class="preset-btn" onclick={() => applyPreset(p)}>
						{p.title}
					</button>
				{/each}
			</div>

			<div class="sec se-help">
				<div class="sec-title">단축키</div>
				<div class="kb"><kbd>⌘ Enter</kbd> 실행</div>
				<div class="kb"><kbd>READ-ONLY</kbd> SELECT/WITH/SHOW/DESCRIBE/EXPLAIN/PRAGMA</div>
				<div class="kb">5초 timeout · 1만 row cap</div>
			</div>
		</aside>

		<section class="se-main">
			<textarea
				class="se-textarea"
				bind:this={textarea}
				bind:value={sql}
				onkeydown={handleKey}
				placeholder="SELECT label, marketCap FROM ecosystem ORDER BY marketCap DESC LIMIT 50"
				spellcheck={false}
			></textarea>

			{#if error}
				<div class="se-error">⚠ {error}</div>
			{/if}

			{#if rows.length > 0}
				<div class="se-meta">
					{rows.length.toLocaleString()} row · {columns.length} cols
					{#if elapsed !== null}· {Math.round(elapsed)} ms{/if}
				</div>
				<div class="se-result">
					<table>
						<thead>
							<tr>
								{#each columns as c (c)}
									<th>{c}</th>
								{/each}
							</tr>
						</thead>
						<tbody>
							{#each rows.slice(0, 200) as row, i (i)}
								<tr>
									{#each columns as c (c)}
										<td>{fmtCell(row[c])}</td>
									{/each}
								</tr>
							{/each}
						</tbody>
					</table>
					{#if rows.length > 200}
						<div class="se-more">… 200 row 만 표시 (전체 {rows.length.toLocaleString()} row)</div>
					{/if}
				</div>
			{/if}
		</section>
	</div>
</div>

<style>
	.sql-editor {
		display: flex;
		flex-direction: column;
		height: 100%;
		min-height: 0;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 6px;
		overflow: hidden;
	}
	.se-head {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 10px 14px;
		background: #0a0e18;
		border-bottom: 1px solid #1e2433;
	}
	.se-title {
		display: flex;
		align-items: baseline;
		gap: 10px;
	}
	.se-eyebrow {
		font-size: 12px;
		font-weight: 700;
		color: #f1f5f9;
	}
	.se-sub {
		font-size: 10px;
		color: #64748b;
		font-family: monospace;
	}
	.se-run {
		padding: 6px 14px;
		font-size: 12px;
		font-weight: 600;
		color: var(--amber);
		background: rgba(var(--amber-rgb), 0.1);
		border: 1px solid rgba(var(--amber-rgb), 0.4);
		border-radius: 4px;
		cursor: pointer;
		font-family: inherit;
	}
	.se-run:hover:not(:disabled) {
		background: rgba(var(--amber-rgb), 0.18);
	}
	.se-run:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.se-body {
		flex: 1;
		min-height: 0;
		display: grid;
		grid-template-columns: 240px 1fr;
		gap: 0;
	}
	.se-sidebar {
		border-right: 1px solid #1e2433;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		font-size: 11px;
	}
	.sec {
		padding: 10px;
		border-bottom: 1px solid #1e2433;
	}
	.sec-title {
		font-size: 10px;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 6px;
	}
	.sec-empty {
		font-size: 10px;
		color: #475569;
		padding: 6px 0;
	}

	.table-block {
		margin-bottom: 4px;
	}
	.table-block summary {
		display: flex;
		justify-content: space-between;
		align-items: center;
		cursor: pointer;
		padding: 4px 6px;
		background: #0a0e18;
		border-radius: 3px;
		list-style: none;
	}
	.table-block summary::-webkit-details-marker {
		display: none;
	}
	.table-block summary::before {
		content: '▸';
		font-size: 9px;
		color: #64748b;
		margin-right: 4px;
	}
	.table-block[open] summary::before {
		content: '▾';
	}
	.t-name {
		font-family: monospace;
		font-size: 11px;
		color: var(--amber);
		font-weight: 600;
	}
	.t-count {
		font-family: monospace;
		font-size: 9px;
		color: #64748b;
	}
	.col-list {
		list-style: none;
		margin: 2px 0 0;
		padding: 0 0 0 14px;
		display: flex;
		flex-direction: column;
		gap: 1px;
	}
	.col-btn {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 6px;
		width: 100%;
		padding: 2px 6px;
		background: transparent;
		border: none;
		border-radius: 2px;
		color: inherit;
		cursor: pointer;
		text-align: left;
		font-family: inherit;
	}
	.col-btn:hover {
		background: rgba(var(--amber-rgb), 0.06);
	}
	.c-name {
		font-family: monospace;
		font-size: 10px;
		color: #cbd5e1;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.c-type {
		font-family: monospace;
		font-size: 8px;
		color: #475569;
		flex-shrink: 0;
	}

	.preset-btn {
		display: block;
		width: 100%;
		text-align: left;
		padding: 5px 8px;
		margin-bottom: 2px;
		background: transparent;
		border: 1px solid #1e2433;
		border-radius: 3px;
		color: #cbd5e1;
		font-size: 10px;
		cursor: pointer;
		font-family: inherit;
		line-height: 1.4;
	}
	.preset-btn:hover {
		background: rgba(var(--amber-rgb), 0.06);
		border-color: rgba(var(--amber-rgb), 0.4);
		color: var(--amber);
	}

	.se-help .kb {
		font-size: 10px;
		color: #64748b;
		margin-bottom: 3px;
	}
	.se-help kbd {
		font-family: monospace;
		padding: 1px 5px;
		background: #1e2433;
		border-radius: 2px;
		color: #cbd5e1;
		font-size: 9px;
	}

	.se-main {
		display: flex;
		flex-direction: column;
		min-height: 0;
		min-width: 0;
	}
	.se-textarea {
		flex-shrink: 0;
		height: 140px;
		padding: 12px;
		background: #050811;
		border: none;
		border-bottom: 1px solid #1e2433;
		color: #f1f5f9;
		font-family: 'JetBrains Mono', monospace;
		font-size: 12px;
		line-height: 1.5;
		resize: vertical;
	}
	.se-textarea:focus {
		outline: none;
		background: #0a0e18;
	}
	.se-error {
		flex-shrink: 0;
		padding: 8px 12px;
		background: rgba(239, 68, 68, 0.08);
		color: #ef4444;
		font-size: 11px;
		border-bottom: 1px solid rgba(239, 68, 68, 0.2);
	}
	.se-meta {
		flex-shrink: 0;
		padding: 6px 12px;
		font-size: 10px;
		color: #64748b;
		font-family: monospace;
		background: #0a0e18;
		border-bottom: 1px solid #1e2433;
	}
	.se-result {
		flex: 1;
		min-height: 0;
		overflow: auto;
	}
	.se-result table {
		width: 100%;
		border-collapse: collapse;
		font-size: 11px;
		font-variant-numeric: tabular-nums;
	}
	.se-result th {
		position: sticky;
		top: 0;
		background: #0a0e18;
		color: #cbd5e1;
		font-weight: 600;
		text-align: left;
		padding: 6px 10px;
		border-bottom: 1px solid #1e2433;
		font-size: 10px;
		z-index: 1;
	}
	.se-result td {
		padding: 5px 10px;
		border-bottom: 1px solid rgba(30, 36, 51, 0.5);
		color: #cbd5e1;
		white-space: nowrap;
		max-width: 280px;
		overflow: hidden;
		text-overflow: ellipsis;
		font-family: 'JetBrains Mono', monospace;
	}
	.se-result tr:hover td {
		background: rgba(255, 255, 255, 0.02);
	}
	.se-more {
		padding: 8px 12px;
		font-size: 10px;
		color: #64748b;
		text-align: center;
		font-family: monospace;
	}

	@media (max-width: 768px) {
		.se-body {
			grid-template-columns: 1fr;
		}
		.se-sidebar {
			display: none;
		}
	}
</style>
