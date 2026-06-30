<script lang="ts">
	// 데이터 센터 — dartlab HF parquet 를 엑셀·구글시트에서 바로. 한 화면 컴팩트(무스크롤 지향):
	// 빠른시작 칩 → 데이터셋 드롭다운 + ID → (조회되면) 컬럼·범위 → 받기(다운로드 + 라이브 URL).
	// 기본값(삼성 주가)이 로드 시 바로 보여 "딱 보고 쓴다". 색은 전부 디자인 토큰 SSOT(--dl-*).
	import { onMount } from 'svelte';
	import Header from '$lib/components/sections/Header.svelte';
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

	const ID_HINT: Record<string, string> = {
		company: '005930',
		series: 'DGS10',
		dateShard: '2024',
		bulk: 'observations'
	};

	// 데이터셋 드롭다운 — 출처별 그룹(21장 카드 대신 한 줄로 접음)
	const GROUPS = [
		{ name: 'DART · 한국 공시', test: (d: string) => d.startsWith('dart/') },
		{ name: 'SEC EDGAR · 미국', test: (d: string) => d.startsWith('edgar/') },
		{ name: 'KRX · 공공데이터 (시세·지수)', test: (d: string) => d.startsWith('gov/') || d.startsWith('krx/') },
		{ name: '거시경제', test: (d: string) => d.startsWith('macro/') },
		{ name: '리서치', test: (d: string) => d.startsWith('research/') }
	];
	const grouped = GROUPS.map((g) => ({ name: g.name, items: DOWNLOAD_CATALOG.filter((e) => g.test(e.dir)) })).filter((g) => g.items.length);

	// 빠른 시작 — 클릭하면 즉시 채우고 조회
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
	let copiedKey = $state('');
	let showCols = $state(false); // 컬럼 칩은 기본 접힘(전체) — [고르기]로만 펼침(단순성)

	function changeDir(dirStr: string) {
		selectDir(dirStr);
		if (id.trim()) probe(); // 데이터셋 바꾸면 같은 ID 로 자동 조회(편의성)
	}
	function idBlur() {
		if (id.trim() && dir && probedKey !== `${dir.dir}/${id.trim()}`) probe();
	}

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
		return { nc, nr, cells: nc * nr, over: nc * nr > CELL_CAP };
	});

	function selectDir(dirStr: string) {
		const entry = DOWNLOAD_CATALOG.find((e) => e.dir === dirStr) ?? null;
		dir = entry;
		allCols = [];
		pickedCols = new Set();
		totalRows = 0;
		probeErr = '';
		probedKey = '';
		if (entry && (entry.shardKind === 'dateShard' || entry.shardKind === 'bulk')) limitMode = 'head';
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
			probeErr = `조회 실패 — 경로/ID 확인 (${String((e as Error)?.message ?? e).slice(0, 60)})`;
			allCols = [];
			totalRows = 0;
		} finally {
			probing = false;
		}
	}

	async function loadExample(ex: (typeof QUICK)[number]) {
		selectDir(ex.dir);
		id = ex.id;
		await probe();
		if (ex.cols.length) pickedCols = new Set(ex.cols.filter((c) => allCols.includes(c)));
	}

	onMount(() => {
		loadExample(QUICK[0]); // 로드 즉시 작동 예시(삼성 주가) — "딱 보고 쓴다"
	});

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
			setTimeout(() => (copiedKey = ''), 1600);
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
	<header class="head">
		<p class="kicker">데이터 센터</p>
		<h1>엑셀·구글시트에서 dartlab 데이터를 바로</h1>
		<p class="lead">골라서 <strong>.xlsx/.csv 로 받거나</strong>, 같은 선택으로 시트가 <strong>라이브로 빨아들이는 URL</strong>을 만듭니다.</p>
	</header>

	<div class="quick">
		<span class="quick-label">빠른 시작</span>
		{#each QUICK as ex (ex.label)}
			<button class="chip-ex" onclick={() => loadExample(ex)}>{ex.label}</button>
		{/each}
	</div>

	<section class="panel">
		<!-- 1줄: 데이터 + ID + 조회 -->
		<div class="ctl">
			<label class="fld grow">
				<span class="fld-label">데이터</span>
				<select value={dir?.dir ?? ''} onchange={(e) => changeDir(e.currentTarget.value)} aria-label="데이터셋 선택">
					{#each grouped as g (g.name)}
						<optgroup label={g.name}>
							{#each g.items as e (e.dir)}<option value={e.dir}>{e.label}</option>{/each}
						</optgroup>
					{/each}
				</select>
			</label>
			<label class="fld">
				<span class="fld-label">{dir?.shardKind === 'company' ? '종목' : '항목'}</span>
				<input class="id-input" placeholder={dir ? ID_HINT[dir.shardKind] : ''} bind:value={id} aria-label="종목·항목 ID" onkeydown={(ev) => ev.key === 'Enter' && probe()} onblur={idBlur} />
			</label>
			<button class="btn" onclick={probe} disabled={!id.trim() || probing}>{probing ? '조회 중…' : '조회'}</button>
			{#if dir}
				<span class="tag" class:live={eligible}>{eligible ? '라이브 가능' : '다운로드 전용'}</span>
			{/if}
		</div>
		{#if dir && BULK_OBS.has(dir.dir)}<p class="micro">시리즈ID 를 넣으세요 · 목록은 <code>{dir.dir}/manifest</code></p>{/if}
		{#if probeErr}<p class="err">{probeErr}</p>{/if}

		{#if probed && allCols.length}
			<!-- 컬럼 (기본 접힘 = 전체) -->
			<div class="optline">
				<span class="opt-label">컬럼</span>
				<div class="colwrap">
					<button class="link-btn" onclick={() => (showCols = !showCols)} aria-expanded={showCols}>
						{cols.length === 0 || cols.length === allCols.length ? `전체 ${allCols.length}열` : `${cols.length} / ${allCols.length}열 선택`}
						<span class="caret">{showCols ? '▾' : '▸'}</span>
					</button>
					{#if showCols}
						<div class="cols">
							{#each allCols as c (c)}
								<label class="chip" class:on={pickedCols.has(c)}>
									<input type="checkbox" checked={pickedCols.has(c)} onchange={() => toggleCol(c)} />{c}
								</label>
							{/each}
						</div>
					{/if}
				</div>
			</div>
			<!-- 범위 -->
			<div class="optline">
				<span class="opt-label">범위</span>
				<div class="range">
					<label class="radio"><input type="radio" value="tail" bind:group={limitMode} /> 최근</label>
					<label class="radio"><input type="radio" value="head" bind:group={limitMode} /> 처음</label>
					<label class="radio"><input type="radio" value="all" bind:group={limitMode} /> 전체</label>
					{#if limitMode !== 'all'}<input class="num" type="number" min="1" bind:value={limitN} /> 행{/if}
					{#if hasDateCol}<span class="sep">·</span><span class="radio">주기<select bind:value={freq}><option value="">원본</option><option value="d">일</option><option value="w">주</option><option value="m">월</option><option value="q">분기</option><option value="y">연</option></select></span>{/if}
					<span class="prev">{preview.nr.toLocaleString()}행 × {preview.nc}열{#if preview.over}<span class="warn"> · ~5만셀 한도 자동절단</span>{/if}</span>
				</div>
			</div>

			<!-- 받기 -->
			<div class="out">
				<div class="optline">
					<span class="opt-label">받기</span>
					<div class="dl">
						<button class="btn primary" onclick={() => download('xlsx')} disabled={!!busy}>{busy === 'xlsx' ? '변환 중…' : 'Excel (.xlsx)'}</button>
						<button class="btn" onclick={() => download('csv')} disabled={!!busy}>{busy === 'csv' ? '변환 중…' : 'CSV'}</button>
						<span class="dl-note">브라우저 직접 변환 · 한도 없음 · 진짜 Number</span>
					</div>
				</div>
				{#if eligible && tier2On && liveUrl}
					<div class="optline">
						<span class="opt-label">라이브</span>
						<div class="livebox">
							<code>{liveUrl}</code>
							<button class="btn sm" onclick={() => copy(`=IMPORTDATA("${liveUrl}")`, 'live')}>{copiedKey === 'live' ? '복사됨 ✓' : '=IMPORTDATA 복사'}</button>
						</div>
					</div>
				{/if}
			</div>
		{/if}
	</section>

	<details class="usage">
		<summary>구글시트·엑셀에서 쓰는 법</summary>
		<ul>
			<li><strong>구글시트</strong> — 빈 셀에 <code>=IMPORTDATA("위 URL")</code> 붙여넣기. 약 1시간마다 자동 갱신.</li>
			<li><strong>엑셀</strong> — 데이터 → 웹에서 → 위 URL의 <code>.csv</code>를 <code>.tsv</code>로 바꿔 입력 → 모두 새로 고침. (한국 엑셀 콤마 로케일 회피)</li>
			<li><strong>한 번 받기</strong> — Excel/CSV 버튼. 한도 없음, 큰 파일도 OK. 거대 전량은 <a href="https://huggingface.co/datasets/eddmpython/dartlab-data" target="_blank" rel="noopener">HuggingFace</a>.</li>
		</ul>
	</details>
</main>

<style>
	.dc {
		max-width: 880px;
		margin: 0 auto;
		padding: 5.5rem 1.25rem 4rem;
		color: var(--dl-ink);
		font-family: var(--dl-font-ui);
	}

	.head {
		margin-bottom: var(--dl-s-4);
	}
	.kicker {
		margin: 0 0 var(--dl-s-1);
		color: var(--dl-accent);
		font-size: 0.7rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.12em;
	}
	.head h1 {
		margin: 0 0 var(--dl-s-2);
		font-family: var(--dl-font-head); /* = Pretendard (토큰 통일) — 본문과 같은 family, 위계는 weight/size */
		font-size: clamp(1.5rem, 3vw, 2.1rem);
		font-weight: 600;
		line-height: 1.2;
		letter-spacing: -0.01em;
		color: var(--dl-ink-print);
	}
	.lead {
		margin: 0;
		color: var(--dl-ink-mute);
		font-size: 0.94rem;
		line-height: 1.6;
	}
	.lead strong {
		color: var(--dl-ink);
		font-weight: 600;
	}

	/* 빠른 시작 */
	.quick {
		display: flex;
		flex-wrap: wrap;
		gap: var(--dl-s-2);
		align-items: center;
		margin-bottom: var(--dl-s-3);
	}
	.quick-label {
		color: var(--dl-ink-dim);
		font-size: 0.74rem;
		font-weight: 600;
	}
	.chip-ex {
		padding: 0.3rem 0.75rem;
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

	/* 패널 */
	.panel {
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-lg);
		background: var(--dl-bg-raised);
		padding: var(--dl-s-4) var(--dl-s-5);
	}

	.ctl {
		display: flex;
		gap: var(--dl-s-3);
		align-items: flex-end;
		flex-wrap: wrap;
	}
	.fld {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}
	.fld.grow {
		flex: 1;
		min-width: 240px;
	}
	.fld-label {
		font-size: 0.74rem;
		font-weight: 600;
		color: var(--dl-ink-dim);
	}
	select,
	.id-input,
	.num {
		padding: 0.5rem 0.6rem;
		border-radius: var(--dl-r-md);
		border: 1px solid var(--dl-line-strong);
		background: var(--dl-bg-overlay);
		color: var(--dl-ink);
		font-size: 0.9rem;
		font-family: inherit;
	}
	.id-input {
		width: 150px;
		font-family: var(--dl-font-mono);
	}
	select:focus,
	.id-input:focus,
	.num:focus {
		outline: none;
		border-color: var(--dl-accent);
	}
	.tag {
		align-self: center;
		padding: 0.18rem 0.55rem;
		border-radius: var(--dl-r-pill);
		font-size: 0.7rem;
		font-weight: 600;
		background: var(--dl-bg-overlay);
		color: var(--dl-ink-mute);
	}
	.tag.live {
		background: var(--dl-cat-operation-soft);
		color: var(--dl-good);
	}
	.micro {
		margin: var(--dl-s-2) 0 0;
		color: var(--dl-ink-mute);
		font-size: 0.78rem;
	}
	.err {
		margin: var(--dl-s-2) 0 0;
		color: var(--dl-bad);
		font-size: 0.82rem;
	}

	/* 옵션 줄 — 좌측 라벨 + 우측 컨트롤 */
	.optline {
		display: flex;
		gap: var(--dl-s-3);
		align-items: baseline;
		margin-top: var(--dl-s-4);
		padding-top: var(--dl-s-4);
		border-top: 1px solid var(--dl-line);
	}
	.opt-label {
		flex: 0 0 3rem;
		font-size: 0.78rem;
		font-weight: 600;
		color: var(--dl-ink-dim);
		padding-top: 0.15rem;
	}
	.cols,
	.range,
	.dl,
	.livebox {
		flex: 1;
		display: flex;
		flex-wrap: wrap;
		gap: var(--dl-s-2);
		align-items: center;
	}
	.colwrap {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: var(--dl-s-2);
		align-items: flex-start;
	}
	.link-btn {
		padding: 0.1rem 0;
		background: none;
		border: 0;
		color: var(--dl-ink);
		font-size: 0.85rem;
		font-family: inherit;
		cursor: pointer;
	}
	.link-btn:hover {
		color: var(--dl-accent);
	}
	.caret {
		color: var(--dl-accent);
		font-size: 0.7rem;
	}
	.range {
		row-gap: var(--dl-s-1);
	}

	.chip {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		padding: 0.22rem 0.6rem;
		border-radius: var(--dl-r-pill);
		border: 1px solid var(--dl-line-strong);
		background: var(--dl-bg-overlay);
		color: var(--dl-ink-mute);
		font-size: 0.78rem;
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
	.chip input,
	.radio input {
		accent-color: var(--dl-accent);
	}
	.radio {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		font-size: 0.85rem;
		color: var(--dl-ink);
	}
	.sep {
		color: var(--dl-ink-faint);
	}
	.num {
		width: 78px;
		padding: 0.32rem 0.5rem;
	}
	.range select {
		padding: 0.28rem 0.45rem;
		font-size: 0.85rem;
	}
	.prev {
		margin-left: auto;
		font-size: 0.8rem;
		color: var(--dl-ink-mute);
	}
	.prev .warn {
		color: var(--dl-warn);
	}

	.out {
		margin-top: 0;
	}
	.btn {
		padding: 0.5rem 0.95rem;
		border-radius: var(--dl-r-md);
		border: 1px solid var(--dl-line-strong);
		background: var(--dl-bg-overlay);
		color: var(--dl-ink);
		font-size: 0.85rem;
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
		padding: 0.38rem 0.65rem;
		font-size: 0.78rem;
	}
	.dl-note {
		font-size: 0.76rem;
		color: var(--dl-ink-mute);
	}
	.livebox code {
		flex: 1;
		min-width: 220px;
		padding: 0.5rem 0.6rem;
		border-radius: var(--dl-r-md);
		background: var(--dl-bg-deep);
		border: 1px solid var(--dl-line);
		color: var(--dl-accent-light);
		font-family: var(--dl-font-mono);
		font-size: 0.74rem;
		word-break: break-all;
		line-height: 1.45;
	}

	/* 사용법 (접힘) */
	.usage {
		margin-top: var(--dl-s-4);
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-md);
		background: var(--dl-bg-raised);
		padding: 0 var(--dl-s-4);
	}
	.usage summary {
		padding: var(--dl-s-3) 0;
		cursor: pointer;
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--dl-ink);
		list-style: none;
	}
	.usage summary::before {
		content: '▸ ';
		color: var(--dl-accent);
	}
	.usage[open] summary::before {
		content: '▾ ';
	}
	.usage ul {
		margin: 0 0 var(--dl-s-3);
		padding-left: 1.2rem;
		color: var(--dl-ink);
		font-size: 0.85rem;
		line-height: 1.8;
	}
	.usage strong {
		color: var(--dl-ink-print);
	}
	.usage a {
		color: var(--dl-accent);
		text-decoration: none;
	}
	.usage a:hover {
		text-decoration: underline;
	}
	code {
		padding: 0.06rem 0.34rem;
		border-radius: var(--dl-r-sm);
		background: var(--dl-bg-overlay);
		color: var(--dl-accent);
		font-family: var(--dl-font-mono);
		font-size: 0.86em;
	}

	/* 접근성 — 키보드 포커스 링 */
	.btn:focus-visible,
	.chip-ex:focus-visible,
	.link-btn:focus-visible,
	select:focus-visible,
	.id-input:focus-visible,
	.num:focus-visible,
	.chip:focus-within,
	.radio:focus-within,
	summary:focus-visible {
		outline: 2px solid var(--dl-focus);
		outline-offset: 2px;
		border-radius: var(--dl-r-sm);
	}
</style>
