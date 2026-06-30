<script lang="ts">
	// 데이터 센터 — dartlab HF parquet 를 엑셀·구글시트에서 바로 쓰게 하는 작업대.
	// 상단: 사용법(구글시트 라이브 / 엑셀 라이브 / 다운로드) + 빠른 예시. 아래: 빌더(고르면 다운로드 + 라이브 URL).
	// 신규 작성기 0 — readParquetRows·objectsToWorkbook·toCsv·originUrl 재사용. 색은 전부 디자인 토큰 SSOT(--dl-*).
	import Header from '$lib/components/sections/Header.svelte';
	import { base } from '$app/paths';
	import { readParquetRows, readParquetMetadata } from '@dartlab/ui-runtime/data/parquet/hfRange';
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
	const CELL_CAP = 45_000;
	const EXCEL_MAX = 1_000_000;
	const BULK_OBS = new Set(['macro/fred', 'macro/ecos', 'macro/customs']);
	const tier2On = originConfigured('csvWorker');

	const ID_HINT: Record<string, { ph: string; note: string }> = {
		company: { ph: '005930', note: '종목코드 / ticker' },
		series: { ph: 'DGS10', note: '시리즈ID · 지수명 · YYYYMM' },
		dateShard: { ph: '2024', note: '연·날짜 (대형 — 다운로드 전용)' },
		bulk: { ph: 'observations', note: '단일/대형 파일 (다운로드 전용)' }
	};

	// 빠른 예시 — 클릭하면 빌더에 채우고 스키마까지 조회
	const QUICK = [
		{ label: '삼성전자 주가', dir: 'gov/prices/company', id: '005930', cols: ['date', 'close', 'volume'] },
		{ label: '삼성전자 재무', dir: 'dart/finance', id: '005930', cols: ['bsns_year', 'account_nm', 'thstrm_amount'] },
		{ label: 'SK하이닉스 주가', dir: 'gov/prices/company', id: '000660', cols: ['date', 'close', 'volume'] },
		{ label: '현대차 재무', dir: 'dart/finance', id: '005380', cols: ['bsns_year', 'account_nm', 'thstrm_amount'] },
		{ label: 'KOSPI 지수', dir: 'gov/indices/index', id: 'KOSPI-코스피', cols: [] }
	];

	let dir = $state<CatalogEntry | null>(null);
	let id = $state('');
	let allCols = $state<string[]>([]);
	let pickedCols = $state<Set<string>>(new Set());
	let totalRows = $state(0);
	let probing = $state(false);
	let probeErr = $state('');
	let probedKey = $state('');
	let limitMode = $state<'all' | 'tail' | 'head'>('tail');
	let limitN = $state(250);
	let freq = $state('');
	let busy = $state('');
	let usageTab = $state<'sheets' | 'excel' | 'download'>('sheets');
	let copiedKey = $state('');

	const cleanName = (s: string) => s.replace(/[\\/:*?"<>|]+/g, '_').slice(0, 80);

	function physical(d: string, idv: string) {
		if (BULK_OBS.has(d)) return { path: `${d}/observations.parquet`, seriesCol: 'seriesId', seriesVal: idv };
		return { path: `${d}/${idv}.parquet`, seriesCol: null as string | null, seriesVal: null as string | null };
	}

	const cols = $derived([...pickedCols].filter((c) => allCols.includes(c)));
	const hasDateCol = $derived(allCols.some((c) => /(^date$|날짜|기준일|^month$|pub_?date|기간)/i.test(c)));
	const eligible = $derived(dir ? isTier2Eligible(dir) : false);
	const probed = $derived(dir != null && id.trim() !== '' && probedKey === `${dir.dir}/${id.trim()}`);

	function buildLiveUrl(d: string, idv: string, projected: string[], all: string[]): string {
		const p = new URLSearchParams();
		if (projected.length && projected.length < all.length) p.set('cols', projected.join(','));
		if (limitMode === 'tail') p.set('tail', String(limitN));
		else if (limitMode === 'head') p.set('head', String(limitN));
		if (freq) p.set('freq', freq);
		const qs = p.toString();
		return originUrl('csvWorker', `${d}/${idv}.csv${qs ? `?${qs}` : ''}`);
	}

	const liveUrl = $derived(dir && id.trim() && tier2On && eligible ? buildLiveUrl(dir.dir, id.trim(), cols, allCols) : '');

	// 사용법 탭 예시 URL — 고정 샘플(삼성 주가). 워커 배포돼야 실제 URL, 아니면 형식만.
	const exCsv = $derived(tier2On ? originUrl('csvWorker', 'gov/prices/company/005930.csv?cols=date,close&tail=250') : 'https://{워커}/v1/gov/prices/company/005930.csv?cols=date,close&tail=250');
	const exTsv = $derived(exCsv.replace('.csv?', '.tsv?'));

	const preview = $derived.by(() => {
		const nc = cols.length || allCols.length || 0;
		const nr = limitMode === 'all' ? totalRows : Math.min(limitN, totalRows || limitN);
		return { nc, nr, cells: nc * nr, over: nc * nr > CELL_CAP };
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
			pickedCols = new Set();
			probedKey = `${dir.dir}/${id.trim()}`;
		} catch (e) {
			probeErr = `조회 실패 — 경로/ID 확인 (${String((e as Error)?.message ?? e).slice(0, 70)})`;
			allCols = [];
			totalRows = 0;
		} finally {
			probing = false;
		}
	}

	async function applyExample(ex: (typeof QUICK)[number]) {
		const entry = DOWNLOAD_CATALOG.find((e) => e.dir === ex.dir);
		if (!entry) return;
		dir = entry;
		id = ex.id;
		await probe();
		if (ex.cols.length) pickedCols = new Set(ex.cols.filter((c) => allCols.includes(c)));
		document.getElementById('builder')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

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
		probeErr = '';
		try {
			const sheet = await readSlice();
			if (!sheet.rows.length) {
				probeErr = '결과 0행 — ID/슬라이스 확인';
				return;
			}
			const name = sheet.label;
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
			probeErr = `다운로드 실패 — ${String((e as Error)?.message ?? e).slice(0, 80)}`;
		} finally {
			busy = '';
		}
	}

	async function copy(text: string, key: string) {
		try {
			await navigator.clipboard.writeText(text);
			copiedKey = key;
			setTimeout(() => (copiedKey = key === copiedKey ? '' : copiedKey), 1600);
		} catch {
			/* clipboard 차단 — 무시 */
		}
	}
</script>

<svelte:head>
	<title>데이터 센터 | dartlab</title>
	<meta name="robots" content="noindex" />
</svelte:head>

<Header />

<main class="dc">
	<header class="hero">
		<p class="kicker">데이터 센터</p>
		<h1>엑셀·구글시트에서 dartlab 데이터를 바로</h1>
		<p class="lead">
			DART·EDGAR·KRX·거시 데이터를 골라서 <strong>.xlsx/.csv 로 받거나</strong>, 같은 선택으로
			시트가 <strong>라이브로 빨아들이는 URL</strong>을 만듭니다. parquet 을 몰라도, 코드 없이.
		</p>
	</header>

	<!-- 사용법 -->
	<section class="usage">
		<div class="tabs" role="tablist">
			<button class="tab" class:on={usageTab === 'sheets'} onclick={() => (usageTab = 'sheets')}>구글시트 라이브</button>
			<button class="tab" class:on={usageTab === 'excel'} onclick={() => (usageTab = 'excel')}>엑셀 라이브</button>
			<button class="tab" class:on={usageTab === 'download'} onclick={() => (usageTab = 'download')}>한 번 받기</button>
		</div>

		<div class="tabbody">
			{#if usageTab === 'sheets'}
				<ol class="steps">
					<li><a href="https://sheets.google.com" target="_blank" rel="noopener">구글시트</a> 새 문서를 엽니다.</li>
					<li>빈 셀을 클릭하고 아래 수식을 붙여넣습니다.</li>
					<li>데이터가 셀 격자로 들어옵니다 — <strong>약 1시간마다 자동 갱신</strong>.</li>
				</ol>
				<div class="snippet">
					<code>={'IMPORTDATA'}("{exCsv}")</code>
					<button class="btn sm" onclick={() => copy(`=IMPORTDATA("${exCsv}")`, 'sheets')}>{copiedKey === 'sheets' ? '복사됨 ✓' : '복사'}</button>
				</div>
				<p class="fine">슬라이스는 URL 쿼리로: <code>?cols=date,close&tail=250&freq=m</code>. 아래 빌더가 선택대로 URL을 만들어 줍니다.</p>
			{:else if usageTab === 'excel'}
				<ol class="steps">
					<li>엑셀 → <strong>데이터 → 웹에서</strong>(From Web).</li>
					<li>아래 <code>.tsv</code> URL을 넣고 Text/CSV 커넥터로 표를 불러옵니다.</li>
					<li><strong>모두 새로 고침</strong>으로 갱신. (한국 엑셀은 <code>.tsv</code> 권장 — 콤마 로케일 충돌 회피.)</li>
				</ol>
				<div class="snippet">
					<code>{exTsv}</code>
					<button class="btn sm" onclick={() => copy(exTsv, 'excel')}>{copiedKey === 'excel' ? '복사됨 ✓' : '복사'}</button>
				</div>
				<p class="fine">라이브 ≠ 실시간 셀함수 — 열기/수동/스케줄로 새로고침됩니다.</p>
			{:else}
				<ol class="steps">
					<li>아래 빌더에서 데이터셋·종목·컬럼·범위를 고릅니다.</li>
					<li><strong>Excel(.xlsx)</strong> 또는 <strong>CSV</strong> 버튼을 누르면 브라우저가 바로 변환·저장.</li>
					<li>한도 없음(로컬 메모리) · 숫자는 진짜 Number라 <code>=SUM</code> 즉시 작동 · 큰 파일도 OK.</li>
				</ol>
				<p class="fine">거대 데이터 전량은 <a href="https://huggingface.co/datasets/eddmpython/dartlab-data" target="_blank" rel="noopener">HuggingFace 데이터셋</a>에서.</p>
			{/if}
		</div>

		<div class="quick">
			<span class="quick-label">빠른 예시</span>
			{#each QUICK as ex (ex.label)}
				<button class="chip-ex" onclick={() => applyExample(ex)}>{ex.label}</button>
			{/each}
		</div>
	</section>

	<!-- 빌더 -->
	<div class="rule" id="builder"><span>직접 만들기</span></div>

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
		<section class="step">
			<h2><span class="n">2</span> {dir.shardKind === 'company' ? '종목' : '항목'} 선택</h2>
			<div class="row">
				<input
					class="id-input"
					placeholder={ID_HINT[dir.shardKind]?.ph}
					bind:value={id}
					onkeydown={(ev) => ev.key === 'Enter' && probe()}
				/>
				<button class="btn" onclick={probe} disabled={!id.trim() || probing}>{probing ? '조회 중…' : '스키마 조회'}</button>
			</div>
			<p class="hint">{ID_HINT[dir.shardKind]?.note}{#if BULK_OBS.has(dir.dir)} · 시리즈 목록은 <code>{dir.dir}/manifest</code>{/if}</p>
			{#if probeErr}<p class="err">{probeErr}</p>{/if}
		</section>
	{/if}

	{#if probed && allCols.length}
		<section class="step">
			<h2><span class="n">3</span> 컬럼 <span class="muted">미선택 = 전체 {allCols.length}열 · 전체 {totalRows.toLocaleString()}행</span></h2>
			<div class="cols">
				{#each allCols as c (c)}
					<label class="chip" class:on={pickedCols.has(c)}>
						<input type="checkbox" checked={pickedCols.has(c)} onchange={() => toggleCol(c)} />
						{c}
					</label>
				{/each}
			</div>
		</section>

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
					<span class="radio">주기
						<select bind:value={freq}>
							<option value="">원본</option>
							<option value="d">일</option>
							<option value="w">주</option>
							<option value="m">월</option>
							<option value="q">분기</option>
							<option value="y">연</option>
						</select>
					</span>
				{/if}
			</div>
		</section>

		<section class="step out">
			<h2><span class="n">5</span> 받기</h2>

			<div class="cell-preview">
				받을 데이터 ≈ <strong>{preview.nr.toLocaleString()}행 × {preview.nc}열</strong>
				= {preview.cells.toLocaleString()}셀 <span class="muted">(전체 {totalRows.toLocaleString()}행)</span>
				{#if preview.over}
					<span class="warn">· 라이브는 ~5만셀 한도 → 워커가 최근행 자동 절단. 컬럼/최근N으로 줄이면 전량.</span>
				{/if}
			</div>

			<div class="dl-row">
				<button class="btn primary" onclick={() => download('xlsx')} disabled={!!busy}>{busy === 'xlsx' ? '변환 중…' : 'Excel 다운로드 (.xlsx)'}</button>
				<button class="btn" onclick={() => download('csv')} disabled={!!busy}>{busy === 'csv' ? '변환 중…' : 'CSV 다운로드'}</button>
				<span class="dl-note">브라우저가 직접 변환 — 한도 없음, 숫자는 진짜 Number</span>
			</div>

			<div class="live">
				<h3>라이브 (구글시트 · 엑셀)</h3>
				{#if !eligible}
					<p class="muted">이 데이터셋은 대형이라 라이브 변환 비대상 — 위 Tier1 다운로드를 쓰세요.</p>
				{:else if !tier2On}
					<p class="muted">라이브 워커 미설정(<code>VITE_DARTLAB_CSV_PROXY</code>) — 지금은 다운로드로.</p>
				{:else}
					<div class="url-box">
						<code>{liveUrl}</code>
						<button class="btn sm" onclick={() => copy(`=IMPORTDATA("${liveUrl}")`, 'live')}>{copiedKey === 'live' ? '복사됨 ✓' : '=IMPORTDATA 복사'}</button>
					</div>
					<p class="fine">구글시트 빈 셀에 붙여넣기 → ~1시간 자동 갱신. 엑셀이면 <code>.csv</code>를 <code>.tsv</code>로 바꿔 데이터→웹에서.</p>
				{/if}
			</div>
		</section>
	{/if}

	<footer class="dc-foot">
		돌아가기: <a href="{base}/">홈</a> · 벌크 전량: <a href="https://huggingface.co/datasets/eddmpython/dartlab-data" target="_blank" rel="noopener">HuggingFace</a>
	</footer>
</main>

<style>
	.dc {
		max-width: 960px;
		margin: 0 auto;
		padding: 6rem 1.25rem 5rem;
		color: var(--dl-ink);
		font-family: var(--dl-font-ui);
	}

	/* ── Hero ── */
	.hero {
		padding-bottom: var(--dl-s-5);
		border-bottom: 1px solid var(--dl-line);
	}
	.kicker {
		margin: 0 0 var(--dl-s-2);
		color: var(--dl-accent);
		font-size: 0.72rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.12em;
	}
	.hero h1 {
		margin: 0 0 var(--dl-s-3);
		font-family: var(--dl-font-head);
		font-size: clamp(1.8rem, 3.6vw, 2.6rem);
		line-height: 1.12;
		color: var(--dl-ink-print);
	}
	.lead {
		margin: 0;
		max-width: 40rem;
		color: var(--dl-ink-mute);
		font-size: 1rem;
		line-height: 1.7;
	}
	.lead strong {
		color: var(--dl-ink);
		font-weight: 600;
	}

	/* ── 사용법 ── */
	.usage {
		margin-top: var(--dl-s-5);
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-lg);
		background: var(--dl-bg-raised);
		overflow: hidden;
	}
	.tabs {
		display: flex;
		border-bottom: 1px solid var(--dl-line);
	}
	.tab {
		flex: 1;
		padding: 0.7rem 0.5rem;
		background: transparent;
		border: 0;
		border-bottom: 2px solid transparent;
		color: var(--dl-ink-mute);
		font-size: 0.86rem;
		font-weight: 600;
		font-family: inherit;
		cursor: pointer;
		transition: color var(--dl-dur-hover) var(--dl-ease), border-color var(--dl-dur-hover) var(--dl-ease);
	}
	.tab:hover {
		color: var(--dl-ink);
	}
	.tab.on {
		color: var(--dl-accent);
		border-bottom-color: var(--dl-accent);
	}
	.tabbody {
		padding: var(--dl-s-4) var(--dl-s-5);
	}
	.steps {
		margin: 0 0 var(--dl-s-3);
		padding-left: 1.3rem;
		color: var(--dl-ink);
		font-size: 0.92rem;
		line-height: 1.8;
	}
	.steps strong {
		color: var(--dl-ink-print);
	}
	.steps a {
		color: var(--dl-accent);
		text-decoration: none;
	}
	.steps a:hover {
		text-decoration: underline;
	}
	.snippet {
		display: flex;
		gap: var(--dl-s-2);
		align-items: stretch;
		flex-wrap: wrap;
	}
	.snippet code {
		flex: 1;
		min-width: 260px;
		padding: 0.55rem 0.7rem;
		border-radius: var(--dl-r-md);
		background: var(--dl-bg-deep);
		border: 1px solid var(--dl-line);
		color: var(--dl-accent-light);
		font-family: var(--dl-font-mono);
		font-size: 0.78rem;
		word-break: break-all;
		line-height: 1.5;
	}
	.fine {
		margin: var(--dl-s-3) 0 0;
		color: var(--dl-ink-mute);
		font-size: 0.8rem;
		line-height: 1.6;
	}
	.fine code,
	.steps code,
	.hint code {
		padding: 0.06rem 0.34rem;
		border-radius: var(--dl-r-sm);
		background: var(--dl-bg-overlay);
		color: var(--dl-accent);
		font-family: var(--dl-font-mono);
		font-size: 0.86em;
	}
	.quick {
		display: flex;
		flex-wrap: wrap;
		gap: var(--dl-s-2);
		align-items: center;
		padding: var(--dl-s-3) var(--dl-s-5) var(--dl-s-4);
		border-top: 1px solid var(--dl-line);
	}
	.quick-label {
		color: var(--dl-ink-dim);
		font-size: 0.75rem;
		font-weight: 600;
		margin-right: var(--dl-s-1);
	}
	.chip-ex {
		padding: 0.32rem 0.8rem;
		border-radius: var(--dl-r-pill);
		border: 1px solid var(--dl-line-strong);
		background: var(--dl-bg-overlay);
		color: var(--dl-ink);
		font-size: 0.82rem;
		font-family: inherit;
		cursor: pointer;
		transition: border-color var(--dl-dur-hover) var(--dl-ease), color var(--dl-dur-hover) var(--dl-ease);
	}
	.chip-ex:hover {
		border-color: var(--dl-accent);
		color: var(--dl-accent);
	}

	/* ── 구분선 ── */
	.rule {
		display: flex;
		align-items: center;
		gap: var(--dl-s-3);
		margin: var(--dl-s-7) 0 var(--dl-s-2);
		color: var(--dl-ink-dim);
		font-size: 0.8rem;
		font-weight: 600;
		letter-spacing: 0.04em;
	}
	.rule::before,
	.rule::after {
		content: '';
		flex: 1;
		height: 1px;
		background: var(--dl-line);
	}

	/* ── Step ── */
	.step {
		margin-top: var(--dl-s-5);
	}
	.step h2 {
		display: flex;
		align-items: center;
		gap: var(--dl-s-2);
		margin: 0 0 var(--dl-s-3);
		font-size: 0.98rem;
		font-weight: 600;
		color: var(--dl-ink-print);
	}
	.step h2 .n {
		display: inline-grid;
		place-items: center;
		width: 22px;
		height: 22px;
		border-radius: var(--dl-r-pill);
		background: var(--dl-accent);
		color: var(--dl-white, #fff);
		font-size: 0.72rem;
		font-weight: 700;
	}
	.muted {
		color: var(--dl-ink-mute);
		font-weight: 400;
		font-size: 0.8rem;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(224px, 1fr));
		gap: var(--dl-s-2);
	}
	.card {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		text-align: left;
		padding: 0.7rem 0.8rem;
		border-radius: var(--dl-r-md);
		border: 1px solid var(--dl-line);
		background: var(--dl-bg-raised);
		cursor: pointer;
		font-family: inherit;
		transition: border-color var(--dl-dur-hover) var(--dl-ease), background var(--dl-dur-hover) var(--dl-ease);
	}
	.card:hover {
		border-color: var(--dl-line-strong);
		background: var(--dl-bg-overlay);
	}
	.card.on {
		border-color: var(--dl-accent);
		background: var(--dl-accent-soft);
	}
	.card-label {
		font-size: 0.86rem;
		font-weight: 600;
		color: var(--dl-ink);
	}
	.card-dir {
		font-size: 0.72rem;
		color: var(--dl-ink-mute);
		font-family: var(--dl-font-mono);
	}
	.dc-badges {
		display: flex;
		gap: var(--dl-s-1);
		align-items: center;
		margin-top: auto;
		padding-top: 0.45rem;
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
		font-size: 0.66rem;
		font-weight: 600;
		padding: 0.08rem 0.45rem;
		border-radius: var(--dl-r-sm);
		background: var(--dl-bg-overlay);
		color: var(--dl-ink-mute);
	}
	.dc-badge.k-company,
	.dc-badge.k-series {
		color: var(--dl-info);
	}
	.dc-badge.is-live {
		background: var(--dl-cat-operation-soft);
		color: var(--dl-good);
	}

	.row {
		display: flex;
		gap: var(--dl-s-2);
		align-items: center;
	}
	.row.wrap {
		flex-wrap: wrap;
	}
	.id-input {
		flex: 1;
		max-width: 280px;
		padding: 0.55rem 0.7rem;
		border-radius: var(--dl-r-md);
		border: 1px solid var(--dl-line-strong);
		background: var(--dl-bg-raised);
		color: var(--dl-ink);
		font-size: 0.92rem;
		font-family: var(--dl-font-mono);
	}
	.id-input:focus {
		outline: none;
		border-color: var(--dl-accent);
	}
	.hint {
		margin: var(--dl-s-2) 0 0;
		color: var(--dl-ink-mute);
		font-size: 0.8rem;
	}
	.err {
		margin: var(--dl-s-2) 0 0;
		color: var(--dl-bad);
		font-size: 0.82rem;
	}

	.cols {
		display: flex;
		flex-wrap: wrap;
		gap: var(--dl-s-1);
	}
	.chip {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		padding: 0.28rem 0.7rem;
		border-radius: var(--dl-r-pill);
		border: 1px solid var(--dl-line-strong);
		background: var(--dl-bg-raised);
		color: var(--dl-ink-mute);
		font-size: 0.8rem;
		font-family: var(--dl-font-mono);
		cursor: pointer;
		user-select: none;
		transition: color var(--dl-dur-hover) var(--dl-ease), border-color var(--dl-dur-hover) var(--dl-ease);
	}
	.chip.on {
		border-color: var(--dl-accent);
		background: var(--dl-accent-soft);
		color: var(--dl-ink);
	}
	.chip input {
		accent-color: var(--dl-accent);
	}

	.radio {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		font-size: 0.88rem;
		color: var(--dl-ink);
	}
	.radio input {
		accent-color: var(--dl-accent);
	}
	.num {
		width: 84px;
		padding: 0.4rem 0.55rem;
		border-radius: var(--dl-r-md);
		border: 1px solid var(--dl-line-strong);
		background: var(--dl-bg-raised);
		color: var(--dl-ink);
		font-family: var(--dl-font-mono);
	}
	select {
		padding: 0.32rem 0.5rem;
		border-radius: var(--dl-r-md);
		border: 1px solid var(--dl-line-strong);
		background: var(--dl-bg-raised);
		color: var(--dl-ink);
		font-family: inherit;
	}
	.sep {
		color: var(--dl-ink-faint);
	}

	.btn {
		padding: 0.55rem 1rem;
		border-radius: var(--dl-r-md);
		border: 1px solid var(--dl-line-strong);
		background: var(--dl-bg-overlay);
		color: var(--dl-ink);
		font-size: 0.86rem;
		font-family: inherit;
		cursor: pointer;
		white-space: nowrap;
		transition: border-color var(--dl-dur-hover) var(--dl-ease);
	}
	.btn:hover:not(:disabled) {
		border-color: var(--dl-accent);
	}
	.btn:disabled {
		opacity: 0.5;
		cursor: default;
	}
	.btn.primary {
		background: var(--dl-accent);
		border-color: var(--dl-accent);
		color: var(--dl-white, #fff);
		font-weight: 600;
	}
	.btn.primary:hover:not(:disabled) {
		background: var(--dl-accent-dim);
	}
	.btn.sm {
		padding: 0.4rem 0.7rem;
		font-size: 0.78rem;
	}

	.out {
		padding: var(--dl-s-4) var(--dl-s-5);
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-lg);
		background: var(--dl-bg-raised);
	}
	.cell-preview {
		margin-bottom: var(--dl-s-3);
		color: var(--dl-ink);
		font-size: 0.88rem;
		line-height: 1.6;
	}
	.cell-preview strong {
		color: var(--dl-ink-print);
	}
	.cell-preview .warn {
		color: var(--dl-warn);
	}
	.dl-row {
		display: flex;
		gap: var(--dl-s-3);
		align-items: center;
		flex-wrap: wrap;
	}
	.dl-note {
		color: var(--dl-ink-mute);
		font-size: 0.8rem;
	}
	.live {
		margin-top: var(--dl-s-4);
		padding-top: var(--dl-s-4);
		border-top: 1px solid var(--dl-line);
	}
	.live h3 {
		margin: 0 0 var(--dl-s-3);
		font-size: 0.88rem;
		font-weight: 600;
		color: var(--dl-ink-print);
	}
	.url-box {
		display: flex;
		gap: var(--dl-s-2);
		align-items: stretch;
		flex-wrap: wrap;
	}
	.url-box code {
		flex: 1;
		min-width: 260px;
		padding: 0.55rem 0.7rem;
		border-radius: var(--dl-r-md);
		background: var(--dl-bg-deep);
		border: 1px solid var(--dl-line);
		color: var(--dl-accent-light);
		font-family: var(--dl-font-mono);
		font-size: 0.78rem;
		word-break: break-all;
		line-height: 1.5;
	}

	.dc-foot {
		margin-top: var(--dl-s-7);
		padding-top: var(--dl-s-4);
		border-top: 1px solid var(--dl-line);
		color: var(--dl-ink-mute);
		font-size: 0.82rem;
	}
	.dc-foot a {
		color: var(--dl-accent);
		text-decoration: none;
	}
	.dc-foot a:hover {
		text-decoration: underline;
	}
</style>
