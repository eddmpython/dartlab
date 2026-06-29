<script lang="ts">
	// 데이터 센터 — dartlab HF parquet 를 엑셀·구글시트에서 바로 쓰게 하는 링크빌더.
	// Tier1: 브라우저가 parquet 직독 → .xlsx/.csv 다운로드(백엔드 0, cap 없음).
	// Tier2: 같은 슬라이스 선택으로 라이브 워커 URL(=IMPORTDATA / Power Query) 생성.
	// 신규 작성기 0 — readParquetRows·objectsToWorkbook·toCsv·originUrl 전부 재사용. (PRD 02·03·04)
	import Header from '$lib/components/sections/Header.svelte';
	import { base } from '$app/paths';
	import {
		readParquetRows,
		readParquetMetadata
	} from '@dartlab/ui-runtime/data/parquet/hfRange';
	import {
		objectsToWorkbook,
		downloadBlob,
		downloadCsv,
		ZipStore,
		toCsv,
		type ObjectSheet
	} from '@dartlab/ui-surfaces/downloadExport';
	import {
		DOWNLOAD_CATALOG,
		isTier2Eligible,
		type CatalogEntry
	} from '@dartlab/ui-runtime/data/catalog/downloadCatalog';
	import { originUrl, originConfigured } from '@dartlab/ui-runtime/data/origins/registry';

	const XLSX_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
	const CELL_CAP = 45_000; // IMPORTDATA ~5만셀 (워커 CELL_CAP 거울)
	const EXCEL_MAX = 1_000_000; // Excel 행 한도

	// macro 벌크 — fred/ecos/customs 는 observations.parquet 단일 파일, {id}=seriesId (워커 resolvePhysical 거울).
	const BULK_OBS = new Set(['macro/fred', 'macro/ecos', 'macro/customs']);
	const tier2On = originConfigured('csvWorker');

	// shardKind 별 {id} 입력 안내
	const ID_HINT: Record<string, { ph: string; note: string }> = {
		company: { ph: '005930', note: '종목코드 / ticker' },
		series: { ph: 'DGS10', note: '시리즈ID · 지수명 · YYYYMM' },
		dateShard: { ph: '2024', note: '연·날짜 (대형 — Tier1 다운로드 전용)' },
		bulk: { ph: 'observations', note: '단일/대형 파일 (Tier1 다운로드 전용)' }
	};

	let dir = $state<CatalogEntry | null>(null);
	let id = $state('');
	let allCols = $state<string[]>([]);
	let pickedCols = $state<Set<string>>(new Set());
	let totalRows = $state(0);
	let probing = $state(false);
	let probeErr = $state('');
	let probedKey = $state(''); // 어떤 dir/id 를 조회했는지 (변경 감지)
	let limitMode = $state<'all' | 'tail' | 'head'>('tail');
	let limitN = $state(250);
	let freq = $state('');
	let busy = $state('');
	let copied = $state(false);

	const cleanName = (s: string) => s.replace(/[\\/:*?"<>|]+/g, '_').slice(0, 80);

	function physical(d: string, idv: string) {
		if (BULK_OBS.has(d)) return { path: `${d}/observations.parquet`, seriesCol: 'seriesId', seriesVal: idv };
		return { path: `${d}/${idv}.parquet`, seriesCol: null as string | null, seriesVal: null as string | null };
	}

	const cols = $derived([...pickedCols].filter((c) => allCols.includes(c)));
	const hasDateCol = $derived(allCols.some((c) => /(^date$|날짜|기준일|^month$|pub_?date|기간)/i.test(c)));
	const eligible = $derived(dir ? isTier2Eligible(dir) : false);
	const probed = $derived(dir != null && id.trim() !== '' && probedKey === `${dir.dir}/${id.trim()}`);

	const liveUrl = $derived.by(() => {
		if (!dir || !id.trim() || !tier2On || !eligible) return '';
		const p = new URLSearchParams();
		if (cols.length && cols.length < allCols.length) p.set('cols', cols.join(','));
		if (limitMode === 'tail') p.set('tail', String(limitN));
		else if (limitMode === 'head') p.set('head', String(limitN));
		if (freq) p.set('freq', freq);
		const qs = p.toString();
		return originUrl('csvWorker', `${dir.dir}/${id.trim()}.csv${qs ? `?${qs}` : ''}`);
	});

	const preview = $derived.by(() => {
		const nc = cols.length || allCols.length || 0;
		const nr = limitMode === 'all' ? totalRows : Math.min(limitN, totalRows || limitN);
		const cells = nc * nr;
		return { nc, nr, cells, over: cells > CELL_CAP };
	});

	function pick(entry: CatalogEntry) {
		dir = entry;
		allCols = [];
		pickedCols = new Set();
		totalRows = 0;
		probeErr = '';
		probedKey = '';
		if (entry.shardKind === 'dateShard' || entry.shardKind === 'bulk') limitMode = 'head';
	}

	function toggleCol(c: string) {
		const n = new Set(pickedCols);
		if (n.has(c)) n.delete(c);
		else n.add(c);
		pickedCols = n;
	}

	async function probe() {
		if (!dir || !id.trim()) return;
		probing = true;
		probeErr = '';
		try {
			const phys = physical(dir.dir, id.trim());
			const meta = await readParquetMetadata(phys.path);
			allCols = meta.columns;
			totalRows = meta.rows;
			pickedCols = new Set(); // 기본 = 전체(빈 선택 = all)
			probedKey = `${dir.dir}/${id.trim()}`;
		} catch (e) {
			probeErr = `조회 실패 — 경로/ID 확인 (${String((e as Error)?.message ?? e).slice(0, 80)})`;
			allCols = [];
			totalRows = 0;
		} finally {
			probing = false;
		}
	}

	// ── 날짜 정규화 + freq 다운샘플 (워커 거울) ──
	function dateDigits(v: unknown): string {
		if (v instanceof Date) return v.toISOString().slice(0, 10).replace(/-/g, '');
		return String(v ?? '').replace(/[^0-9]/g, '');
	}
	function detectDateCol(cc: string[]): string | null {
		return cc.find((c) => /(^date$|날짜|기준일|^month$|pub_?date|기간)/i.test(c)) ?? null;
	}
	function downsample(rows: Record<string, unknown>[], dateCol: string, f: string) {
		const bucket = new Map<string, { k: string; row: Record<string, unknown> }>();
		for (const r of rows) {
			const digits = dateDigits(r[dateCol]);
			if (digits.length < 4) continue;
			const y = digits.slice(0, 4);
			const mo = digits.slice(4, 6) || '01';
			let key: string;
			if (f === 'y') key = y;
			else if (f === 'q') key = `${y}Q${Math.ceil(Number(mo) / 3)}`;
			else if (f === 'm') key = `${y}${mo}`;
			else if (f === 'w') {
				const da = digits.slice(6, 8) || '01';
				const dt = new Date(Number(y), Number(mo) - 1, Number(da));
				const jan1 = new Date(Number(y), 0, 1);
				const wk = Math.ceil((((+dt - +jan1) / 86400000) + jan1.getDay() + 1) / 7);
				key = `${y}W${String(wk).padStart(2, '0')}`;
			} else key = digits;
			const prev = bucket.get(key);
			if (!prev || digits >= prev.k) bucket.set(key, { k: digits, row: r });
		}
		return [...bucket.values()].sort((a, b) => a.k.localeCompare(b.k)).map((x) => x.row);
	}

	async function readSlice(): Promise<ObjectSheet> {
		if (!dir) throw new Error('데이터셋 미선택');
		const phys = physical(dir.dir, id.trim());
		const proj = cols.length && cols.length < allCols.length ? [...cols] : undefined;
		const needWhole = !!freq || !!phys.seriesCol;
		let rows: Record<string, unknown>[];
		if (!needWhole && limitMode !== 'all' && totalRows) {
			const rowStart = limitMode === 'tail' ? Math.max(0, totalRows - limitN) : 0;
			const rowEnd = limitMode === 'tail' ? totalRows : Math.min(totalRows, limitN);
			rows = (await readParquetRows(phys.path, { columns: proj, rowStart, rowEnd })).rows;
		} else {
			const readCols = phys.seriesCol && proj && !proj.includes(phys.seriesCol) ? [...proj, phys.seriesCol] : proj;
			rows = (await readParquetRows(phys.path, { columns: readCols })).rows;
			if (phys.seriesCol) {
				rows = rows.filter((r) => String(r[phys.seriesCol as string]) === phys.seriesVal);
				if (!rows.length) throw new Error(`시리즈 '${phys.seriesVal}' 없음 — manifest 확인`);
			}
			if (freq) {
				const dc = detectDateCol(cols.length ? cols : allCols);
				if (dc) rows = downsample(rows, dc, freq);
			}
			if (limitMode === 'tail') rows = rows.slice(Math.max(0, rows.length - limitN));
			else if (limitMode === 'head') rows = rows.slice(0, limitN);
		}
		const outCols = cols.length ? cols : rows.length ? Object.keys(rows[0]) : allCols;
		return { label: `${dir.dir.replace(/\//g, '_')}_${cleanName(id.trim())}`, columns: outCols, rows };
	}

	async function download(fmt: 'xlsx' | 'csv') {
		if (!dir || !id.trim()) return;
		busy = fmt;
		try {
			const sheet = await readSlice();
			const name = sheet.label;
			if (!sheet.rows.length) {
				probeErr = '결과 0행 — ID/슬라이스 확인';
				return;
			}
			if (fmt === 'xlsx') {
				downloadBlob(objectsToWorkbook([sheet]), `${name}.xlsx`, XLSX_MIME);
			} else if (sheet.rows.length <= EXCEL_MAX) {
				downloadCsv(name, sheet.columns, sheet.rows);
			} else {
				const zip = new ZipStore();
				const te = new TextEncoder();
				for (let i = 0, part = 1; i < sheet.rows.length; i += EXCEL_MAX, part += 1)
					zip.addEntry(`${name}_${part}.csv`, te.encode(toCsv(sheet.columns, sheet.rows.slice(i, i + EXCEL_MAX))));
				downloadBlob(zip.finalize(), `${name}.zip`, 'application/zip');
			}
		} catch (e) {
			probeErr = `다운로드 실패 — ${String((e as Error)?.message ?? e).slice(0, 90)}`;
		} finally {
			busy = '';
		}
	}

	async function copyLive() {
		if (!liveUrl) return;
		try {
			await navigator.clipboard.writeText(`=IMPORTDATA("${liveUrl}")`);
			copied = true;
			setTimeout(() => (copied = false), 1600);
		} catch {
			/* clipboard 차단 환경 — 무시 */
		}
	}
</script>

<svelte:head>
	<title>데이터 센터 | dartlab</title>
	<meta name="robots" content="noindex" />
</svelte:head>

<Header />

<main class="dc">
	<header class="dc-head">
		<h1>데이터 센터</h1>
		<p>
			dartlab 공동작업대(HuggingFace) 데이터를 <strong>엑셀·구글시트에서 바로</strong> 쓰세요. 골라서
			다운로드(.xlsx/.csv)하거나, 같은 선택으로 시트가 라이브로 빨아들이는 URL을 만듭니다.
		</p>
	</header>

	<!-- 1. 데이터셋 -->
	<section class="step">
		<h2><span class="n">1</span> 데이터셋</h2>
		<div class="grid">
			{#each DOWNLOAD_CATALOG as e (e.dir)}
				<button class="card" class:on={dir?.dir === e.dir} onclick={() => pick(e)}>
					<span class="card-label">{e.label}</span>
					<span class="card-dir">{e.dir}</span>
					<span class="dc-badges">
						<span class="dc-badge k-{e.shardKind}">{e.shardKind}</span>
						{#if isTier2Eligible(e)}<span class="dc-badge is-live">라이브 가능</span>{/if}
					</span>
				</button>
			{/each}
		</div>
	</section>

	{#if dir}
		<!-- 2. ID -->
		<section class="step">
			<h2><span class="n">2</span> {dir.shardKind === 'company' ? '종목' : '항목'} 선택</h2>
			<div class="row">
				<input
					class="id-input"
					placeholder={ID_HINT[dir.shardKind]?.ph}
					bind:value={id}
					onkeydown={(ev) => ev.key === 'Enter' && probe()}
				/>
				<button class="btn" onclick={probe} disabled={!id.trim() || probing}>
					{probing ? '조회 중…' : '스키마 조회'}
				</button>
			</div>
			<p class="hint">{ID_HINT[dir.shardKind]?.note}{#if BULK_OBS.has(dir.dir)} · 시리즈 목록은 <code>{dir.dir}/manifest</code>{/if}</p>
			{#if probeErr}<p class="err">{probeErr}</p>{/if}
		</section>
	{/if}

	{#if probed && allCols.length}
		<!-- 3. 컬럼 -->
		<section class="step">
			<h2><span class="n">3</span> 컬럼 <span class="muted">(미선택 = 전체 {allCols.length}열 · 전체 {totalRows.toLocaleString()}행)</span></h2>
			<div class="cols">
				{#each allCols as c (c)}
					<label class="chip" class:on={pickedCols.has(c)}>
						<input type="checkbox" checked={pickedCols.has(c)} onchange={() => toggleCol(c)} />
						{c}
					</label>
				{/each}
			</div>
		</section>

		<!-- 4. 범위 -->
		<section class="step">
			<h2><span class="n">4</span> 범위</h2>
			<div class="row wrap">
				<label class="radio"><input type="radio" value="tail" bind:group={limitMode} /> 최근</label>
				<label class="radio"><input type="radio" value="head" bind:group={limitMode} /> 처음</label>
				<label class="radio"><input type="radio" value="all" bind:group={limitMode} /> 전체</label>
				{#if limitMode !== 'all'}
					<input class="num" type="number" min="1" bind:value={limitN} /> 행
				{/if}
				{#if hasDateCol}
					<span class="sep">·</span>
					<label class="radio">주기
						<select bind:value={freq}>
							<option value="">원본</option>
							<option value="d">일</option>
							<option value="w">주</option>
							<option value="m">월</option>
							<option value="q">분기</option>
							<option value="y">연</option>
						</select>
					</label>
				{/if}
			</div>
		</section>

		<!-- 5. 결과 -->
		<section class="step out">
			<h2><span class="n">5</span> 받기</h2>

			<div class="cell-preview" class:over={preview.over && limitMode === 'all'}>
				받을 데이터 ≈ <strong>{preview.nr.toLocaleString()}행 × {preview.nc}열</strong>
				= {preview.cells.toLocaleString()}셀 (전체 {totalRows.toLocaleString()}행)
				{#if preview.over}
					<span class="warn">· 라이브는 ~5만셀 한도 — 워커가 자동 최근행 절단. 컬럼/최근N으로 줄이면 전량.</span>
				{/if}
			</div>

			<div class="dl-row">
				<button class="btn primary" onclick={() => download('xlsx')} disabled={!!busy}>
					{busy === 'xlsx' ? '변환 중…' : 'Excel 다운로드 (.xlsx)'}
				</button>
				<button class="btn" onclick={() => download('csv')} disabled={!!busy}>
					{busy === 'csv' ? '변환 중…' : 'CSV 다운로드'}
				</button>
				<span class="dl-note">브라우저가 직접 변환 — 한도 없음, 숫자는 진짜 Number</span>
			</div>

			<!-- 라이브 -->
			<div class="live">
				<h3>라이브 (구글시트 · 엑셀)</h3>
				{#if !eligible}
					<p class="muted">이 데이터셋은 대형이라 라이브 변환 비대상 — 위 Tier1 다운로드를 쓰세요.</p>
				{:else if !tier2On}
					<p class="muted">라이브 워커 미배포 (<code>VITE_DARTLAB_CSV_PROXY</code> 미설정) — 배포 후 여기에 URL이 생깁니다. 지금은 다운로드로.</p>
				{:else}
					<div class="url-box">
						<code>{liveUrl}</code>
						<button class="btn small" onclick={copyLive}>{copied ? '복사됨 ✓' : '=IMPORTDATA 복사'}</button>
					</div>
					<ul class="how">
						<li><strong>구글시트</strong>: 빈 셀에 <code>=IMPORTDATA("…")</code> 붙여넣기 (~1시간마다 자동 갱신)</li>
						<li><strong>엑셀</strong>: 데이터 → 웹에서 → 위 URL의 <code>.csv</code>를 <code>.tsv</code>로 바꿔 붙여넣기 → 모두 새로 고침</li>
					</ul>
				{/if}
			</div>
		</section>
	{/if}

	<footer class="dc-foot">
		벌크 전량은 <a href="https://huggingface.co/datasets/eddmpython/dartlab-data" target="_blank" rel="noopener">HuggingFace 데이터셋</a>에서.
		돌아가기: <a href="{base}/">홈</a>
	</footer>
</main>

<style>
	.dc {
		max-width: 960px;
		margin: 0 auto;
		padding: 28px 20px 80px;
		color: var(--dl-ink);
	}
	.dc-head h1 {
		font-size: 28px;
		margin: 8px 0 6px;
		letter-spacing: -0.01em;
	}
	.dc-head p {
		color: var(--dl-ink-dim, #94a3b8);
		font-size: 14px;
		line-height: 1.6;
		max-width: 640px;
	}
	.dc-head strong {
		color: var(--dl-ink);
	}
	.step {
		margin-top: 22px;
		padding-top: 18px;
		border-top: 1px solid var(--dl-line, rgba(148, 163, 184, 0.18));
	}
	.step h2 {
		font-size: 14px;
		font-weight: 600;
		margin: 0 0 12px;
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.step h2 .n {
		display: inline-grid;
		place-items: center;
		width: 20px;
		height: 20px;
		border-radius: 50%;
		background: var(--dl-accent, #3b82f6);
		color: #fff;
		font-size: 11px;
	}
	.muted {
		color: var(--dl-ink-dim, #94a3b8);
		font-weight: 400;
		font-size: 12px;
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
		gap: 8px;
	}
	.card {
		display: flex;
		flex-direction: column;
		gap: 4px;
		text-align: left;
		padding: 10px 12px;
		border-radius: 10px;
		border: 1px solid var(--dl-line, rgba(148, 163, 184, 0.2));
		background: var(--dl-surface, rgba(255, 255, 255, 0.02));
		cursor: pointer;
		transition: border-color 0.12s, background 0.12s;
	}
	.card:hover {
		border-color: var(--dl-accent, #3b82f6);
	}
	.card.on {
		border-color: var(--dl-accent, #3b82f6);
		background: color-mix(in srgb, var(--dl-accent, #3b82f6) 12%, transparent);
	}
	.card-label {
		font-size: 13px;
		font-weight: 600;
	}
	.card-dir {
		font-size: 11px;
		color: var(--dl-ink-dim, #94a3b8);
		font-family: var(--dl-font-mono, monospace);
	}
	.dc-badges {
		display: flex;
		gap: 4px;
		align-items: center;
		margin-top: auto;
		padding-top: 6px;
	}
	.dc-badge {
		display: inline-flex;
		align-items: center;
		width: auto;
		height: auto;
		min-width: 0;
		min-height: 0;
		line-height: 1.5;
		white-space: nowrap;
		font-size: 10px;
		font-weight: 500;
		padding: 2px 7px;
		border-radius: 6px;
		background: rgba(148, 163, 184, 0.16);
		color: var(--dl-ink-dim, #94a3b8);
	}
	.dc-badge.k-company,
	.dc-badge.k-series {
		color: #7dd3fc;
	}
	.dc-badge.is-live {
		background: rgba(34, 197, 94, 0.16);
		color: #4ade80;
	}
	.row {
		display: flex;
		gap: 8px;
		align-items: center;
	}
	.row.wrap {
		flex-wrap: wrap;
	}
	.id-input {
		flex: 1;
		max-width: 280px;
		padding: 9px 12px;
		border-radius: 8px;
		border: 1px solid var(--dl-line, rgba(148, 163, 184, 0.25));
		background: var(--dl-surface, rgba(255, 255, 255, 0.03));
		color: var(--dl-ink);
		font-size: 14px;
		font-family: var(--dl-font-mono, monospace);
	}
	.hint {
		font-size: 12px;
		color: var(--dl-ink-dim, #94a3b8);
		margin: 8px 0 0;
	}
	.err {
		font-size: 12px;
		color: #f87171;
		margin: 8px 0 0;
	}
	.cols {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
	}
	.chip {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		padding: 4px 10px;
		border-radius: 999px;
		border: 1px solid var(--dl-line, rgba(148, 163, 184, 0.22));
		font-size: 12px;
		font-family: var(--dl-font-mono, monospace);
		cursor: pointer;
		user-select: none;
	}
	.chip.on {
		border-color: var(--dl-accent, #3b82f6);
		background: color-mix(in srgb, var(--dl-accent, #3b82f6) 14%, transparent);
		color: var(--dl-ink);
	}
	.chip input {
		accent-color: var(--dl-accent, #3b82f6);
	}
	.radio {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		font-size: 13px;
	}
	.num {
		width: 84px;
		padding: 6px 8px;
		border-radius: 7px;
		border: 1px solid var(--dl-line, rgba(148, 163, 184, 0.25));
		background: var(--dl-surface, rgba(255, 255, 255, 0.03));
		color: var(--dl-ink);
	}
	select {
		padding: 5px 8px;
		border-radius: 7px;
		border: 1px solid var(--dl-line, rgba(148, 163, 184, 0.25));
		background: var(--dl-surface, rgba(255, 255, 255, 0.03));
		color: var(--dl-ink);
	}
	.sep {
		color: var(--dl-ink-dim, #94a3b8);
	}
	.btn {
		padding: 9px 16px;
		border-radius: 8px;
		border: 1px solid var(--dl-line, rgba(148, 163, 184, 0.3));
		background: var(--dl-surface, rgba(255, 255, 255, 0.04));
		color: var(--dl-ink);
		font-size: 13px;
		cursor: pointer;
		white-space: nowrap;
	}
	.btn:hover:not(:disabled) {
		border-color: var(--dl-accent, #3b82f6);
	}
	.btn:disabled {
		opacity: 0.5;
		cursor: default;
	}
	.btn.primary {
		background: var(--dl-accent, #3b82f6);
		border-color: var(--dl-accent, #3b82f6);
		color: #fff;
		font-weight: 600;
	}
	.btn.small {
		padding: 5px 10px;
		font-size: 12px;
	}
	.out {
		background: var(--dl-surface, rgba(255, 255, 255, 0.02));
		border: 1px solid var(--dl-line, rgba(148, 163, 184, 0.18));
		border-radius: 12px;
		padding: 16px 18px;
	}
	.cell-preview {
		font-size: 13px;
		color: var(--dl-ink-dim, #cbd5e1);
		margin-bottom: 14px;
	}
	.cell-preview strong {
		color: var(--dl-ink);
	}
	.cell-preview .warn {
		color: #fbbf24;
	}
	.dl-row {
		display: flex;
		gap: 10px;
		align-items: center;
		flex-wrap: wrap;
	}
	.dl-note {
		font-size: 12px;
		color: var(--dl-ink-dim, #94a3b8);
	}
	.live {
		margin-top: 20px;
		padding-top: 16px;
		border-top: 1px dashed var(--dl-line, rgba(148, 163, 184, 0.22));
	}
	.live h3 {
		font-size: 13px;
		margin: 0 0 10px;
	}
	.url-box {
		display: flex;
		gap: 8px;
		align-items: center;
		flex-wrap: wrap;
	}
	.url-box code {
		flex: 1;
		min-width: 240px;
		padding: 8px 10px;
		border-radius: 7px;
		background: rgba(0, 0, 0, 0.25);
		border: 1px solid var(--dl-line, rgba(148, 163, 184, 0.2));
		font-size: 12px;
		word-break: break-all;
		color: #7dd3fc;
	}
	.how {
		margin: 12px 0 0;
		padding-left: 18px;
		font-size: 12px;
		color: var(--dl-ink-dim, #cbd5e1);
		line-height: 1.7;
	}
	.how code {
		font-size: 11px;
		background: rgba(148, 163, 184, 0.14);
		padding: 1px 4px;
		border-radius: 4px;
	}
	.dc-foot {
		margin-top: 36px;
		padding-top: 16px;
		border-top: 1px solid var(--dl-line, rgba(148, 163, 184, 0.18));
		font-size: 12px;
		color: var(--dl-ink-dim, #94a3b8);
	}
	.dc-foot a {
		color: var(--dl-accent, #60a5fa);
		text-decoration: none;
	}
	.dc-foot a:hover {
		text-decoration: underline;
	}
</style>
