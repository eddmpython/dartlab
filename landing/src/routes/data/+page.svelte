<script lang="ts">
	// 데이터 센터 — dartlab 공동작업대(HF parquet)를 탐색·다운로드·라이브 API 로.
	// 흐름: 고르기 → 실제 데이터 미리보기 → 가져가기(다운로드 + 구글시트·엑셀·Python·curl API).
	// 신규 작성기 0(readParquetRows·objectsToWorkbook·toCsv·originUrl 재사용). 색은 전부 디자인 토큰 SSOT.
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
	const PREVIEW_N = 12;
	const BULK_OBS = new Set(['macro/fred', 'macro/ecos', 'macro/customs']);
	const tier2On = originConfigured('csvWorker');

	const ID_HINT: Record<string, string> = { company: '005930', series: 'DGS10', dateShard: '2024', bulk: 'observations' };

	const GROUPS = [
		{ name: 'DART · 한국 공시', test: (d: string) => d.startsWith('dart/') },
		{ name: 'SEC EDGAR · 미국', test: (d: string) => d.startsWith('edgar/') },
		{ name: 'KRX · 공공데이터 (시세·지수)', test: (d: string) => d.startsWith('gov/') || d.startsWith('krx/') },
		{ name: '거시경제', test: (d: string) => d.startsWith('macro/') },
		{ name: '리서치', test: (d: string) => d.startsWith('research/') }
	];
	const grouped = GROUPS.map((g) => ({ name: g.name, items: DOWNLOAD_CATALOG.filter((e) => g.test(e.dir)) })).filter((g) => g.items.length);

	const QUICK = [
		{ label: '삼성전자 주가', dir: 'gov/prices/company', id: '005930' },
		{ label: '삼성전자 재무', dir: 'dart/finance', id: '005930' },
		{ label: 'SK하이닉스 주가', dir: 'gov/prices/company', id: '000660' },
		{ label: 'KOSPI 지수', dir: 'gov/indices/index', id: 'KOSPI-코스피' },
		{ label: 'FRED 금리(10년)', dir: 'macro/fred', id: 'DGS10' }
	];

	const CONSUMERS = [
		{ key: 'sheets', label: '구글시트' },
		{ key: 'excel', label: '엑셀' },
		{ key: 'python', label: 'Python' },
		{ key: 'curl', label: 'curl' }
	] as const;

	let dir = $state<CatalogEntry | null>(null);
	let id = $state('');
	let allCols = $state<string[]>([]);
	let totalRows = $state(0);
	let previewRows = $state<Record<string, unknown>[]>([]);
	let pickedCols = $state<Set<string>>(new Set());
	let limitMode = $state<'all' | 'tail' | 'head'>('all');
	let limitN = $state(250);
	let freq = $state('');
	let busy = $state('');
	let probing = $state(false);
	let probeErr = $state('');
	let probedKey = $state('');
	let fileSize = $state(0);
	let apiTab = $state<'sheets' | 'excel' | 'python' | 'curl'>('sheets');
	let showCols = $state(false);
	let copiedKey = $state('');

	// ── 파일 브라우저(탐색) — HF 트리 그대로(공개 repo). CORS 허용·Link 커서 페이지네이션 ──
	const HF_API = 'https://huggingface.co/api/datasets/eddmpython/dartlab-data/tree/main';
	const HF_RESOLVE = 'https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main';
	type Entry = { type: string; path: string; name: string; size: number };
	let mode = $state<'sets' | 'browse'>('sets');
	let cwd = $state('');
	let entries = $state<Entry[]>([]);
	let browseLoading = $state(false);
	let nextCursor = $state<string | null>(null);
	let totalCount = $state(0);
	let filter = $state('');

	function fmtBytes(n: number): string {
		if (!n) return '';
		if (n < 1024) return `${n} B`;
		if (n < 1048576) return `${(n / 1024).toFixed(0)} KB`;
		if (n < 1073741824) return `${(n / 1048576).toFixed(1)} MB`;
		return `${(n / 1073741824).toFixed(2)} GB`;
	}

	async function loadTree(path: string, append = false) {
		browseLoading = true;
		try {
			const base = path ? `${HF_API}/${path}` : HF_API; // 루트는 trailing slash 금지(HF 가 거부)
			const url = append && nextCursor ? nextCursor : `${base}?limit=100`;
			const res = await fetch(url);
			totalCount = Number(res.headers.get('X-Total-Count')) || 0;
			const link = res.headers.get('Link') || '';
			const m = link.match(/<([^>]+)>;\s*rel="next"/);
			nextCursor = m ? m[1] : null;
			const list = (await res.json()) as Array<{ type: string; path: string; size?: number; lfs?: { size?: number } }>;
			const mapped: Entry[] = list.map((x) => ({ type: x.type, path: x.path, name: x.path.split('/').pop() ?? x.path, size: x.lfs?.size ?? x.size ?? 0 }));
			entries = append ? [...entries, ...mapped] : mapped;
			if (!append) {
				cwd = path;
				filter = '';
			}
		} catch {
			if (!append) entries = [];
		} finally {
			browseLoading = false;
		}
	}

	function switchBrowse() {
		mode = 'browse';
		if (!entries.length) loadTree('');
	}
	const crumbs = $derived(cwd ? cwd.split('/') : []);
	const shownEntries = $derived.by(() => {
		const f = filter.trim().toLowerCase();
		const list = f ? entries.filter((e) => e.name.toLowerCase().includes(f)) : entries;
		return [...list].sort((a, b) => (a.type === b.type ? a.name.localeCompare(b.name) : a.type === 'directory' ? -1 : 1));
	});

	function openEntry(e: Entry) {
		if (e.type === 'directory') {
			loadTree(e.path);
			return;
		}
		if (e.name.endsWith('.parquet')) {
			const d = e.path.replace(/\/[^/]+$/, '');
			const idv = e.name.replace(/\.parquet$/, '');
			const entry = DOWNLOAD_CATALOG.find((c) => c.dir === d);
			if (entry) {
				mode = 'sets';
				selectDir(d);
				id = idv;
				probe();
				return;
			}
		}
		window.open(`${HF_RESOLVE}/${e.path}`, '_blank'); // 카탈로그 밖·비parquet = 원본 직링크
	}
	const rawUrl = $derived(dir && id.trim() ? `${HF_RESOLVE}/${physical(dir.dir, id.trim()).path}` : '');

	const cleanName = (s: string) => s.replace(/[\\/:*?"<>|]+/g, '_').slice(0, 80);

	function physical(d: string, idv: string) {
		if (BULK_OBS.has(d)) return { path: `${d}/observations.parquet`, seriesCol: 'seriesId', seriesVal: idv };
		return { path: `${d}/${idv}.parquet`, seriesCol: null as string | null, seriesVal: null as string | null };
	}

	const cols = $derived([...pickedCols].filter((c) => allCols.includes(c)));
	const outCols = $derived(cols.length ? cols : allCols);
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
	const liveTsv = $derived(liveUrl ? liveUrl.replace(/\.csv(\?|$)/, '.tsv$1') : '');
	const snippet = $derived.by(() => {
		if (!liveUrl) return '';
		if (apiTab === 'sheets') return `=IMPORTDATA("${liveUrl}")`;
		if (apiTab === 'excel') return liveTsv;
		if (apiTab === 'python') return `import pandas as pd\ndf = pd.read_csv("${liveUrl}")`;
		return `curl "${liveUrl}"`;
	});
	const apiHint = $derived.by(() => {
		if (apiTab === 'sheets') return '구글시트 빈 셀에 붙여넣기 → 약 1시간마다 자동 갱신.';
		if (apiTab === 'excel') return '엑셀 → 데이터 → 웹에서 → 이 .tsv URL 붙여넣기 → 모두 새로 고침. (한국 엑셀 콤마 회피)';
		if (apiTab === 'python') return 'pandas 가 URL 을 바로 읽습니다. 슬라이스는 URL 쿼리(?cols=&tail=&freq=)로.';
		return '터미널·어디서나. JSON 이 아니라 CSV — 그대로 표 형태.';
	});

	const previewCap = $derived(totalRows ? Math.min(PREVIEW_N, totalRows) : PREVIEW_N);

	function fmt(v: unknown): string {
		if (v === null || v === undefined) return '';
		if (v instanceof Date) return v.toISOString().slice(0, 10);
		if (typeof v === 'number') return Number.isInteger(v) ? v.toLocaleString() : String(v);
		if (typeof v === 'bigint') return v.toLocaleString();
		const s = String(v);
		return s.length > 60 ? s.slice(0, 60) + '…' : s;
	}

	function selectDir(dirStr: string) {
		dir = DOWNLOAD_CATALOG.find((e) => e.dir === dirStr) ?? null;
		allCols = [];
		pickedCols = new Set();
		totalRows = 0;
		previewRows = [];
		probeErr = '';
		probedKey = '';
		showCols = false;
		if (dir && (dir.shardKind === 'dateShard' || dir.shardKind === 'bulk')) limitMode = 'head';
	}
	function changeDir(dirStr: string) {
		selectDir(dirStr);
		if (id.trim()) probe();
	}
	function idBlur() {
		if (id.trim() && dir && probedKey !== `${dir.dir}/${id.trim()}`) probe();
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
		const key = `${dir.dir}/${id.trim()}`;
		try {
			const phys = physical(dir.dir, id.trim());
			const meta = await readParquetMetadata(phys.path);
			allCols = meta.columns;
			totalRows = meta.rows;
			fileSize = meta.size ?? 0;
			pickedCols = new Set();
			// 실데이터 미리보기 — 첫 PREVIEW_N 행(전 컬럼). 컬럼 토글은 캐시에서 즉시 재렌더.
			if (phys.seriesCol) {
				const all = (await readParquetRows(phys.path, {})).rows;
				const sub = all.filter((r) => String(r[phys.seriesCol as string]) === phys.seriesVal);
				if (!sub.length) throw new Error(`시리즈 '${phys.seriesVal}' 없음 — manifest 확인`);
				totalRows = sub.length;
				previewRows = sub.slice(0, PREVIEW_N);
			} else {
				previewRows = (await readParquetRows(phys.path, { rowStart: 0, rowEnd: PREVIEW_N })).rows;
			}
			probedKey = key;
		} catch (e) {
			probeErr = `조회 실패 — 경로/ID 확인 (${String((e as Error)?.message ?? e).slice(0, 60)})`;
			allCols = [];
			totalRows = 0;
			previewRows = [];
		} finally {
			probing = false;
		}
	}

	async function loadExample(ex: (typeof QUICK)[number]) {
		mode = 'sets';
		selectDir(ex.dir);
		id = ex.id;
		await probe();
	}

	onMount(() => loadExample(QUICK[0]));

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
				if (!rows.length) throw new Error(`시리즈 '${phys.seriesVal}' 없음`);
			}
			if (freq) {
				const dc = detectDateCol(cols.length ? cols : allCols);
				if (dc) rows = downsample(rows, dc, freq);
			}
			if (limitMode === 'tail') rows = rows.slice(Math.max(0, rows.length - limitN));
			else if (limitMode === 'head') rows = rows.slice(0, limitN);
		}
		const oc = cols.length ? cols : rows.length ? Object.keys(rows[0]) : allCols;
		return { label: `${dir.dir.replace(/\//g, '_')}_${cleanName(id.trim())}`, columns: oc, rows };
	}

	async function download(f: 'xlsx' | 'csv') {
		if (!dir || !id.trim()) return;
		busy = f;
		probeErr = '';
		try {
			const sheet = await readSlice();
			if (!sheet.rows.length) {
				probeErr = '결과 0행 — ID/슬라이스 확인';
				return;
			}
			const name = sheet.label;
			if (f === 'xlsx') downloadBlob(objectsToWorkbook([sheet]), `${name}.xlsx`, XLSX_MIME);
			else if (sheet.rows.length <= EXCEL_MAX) downloadCsv(name, sheet.columns, sheet.rows);
			else {
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
		<h1>dartlab 데이터를 시트·코드에서 바로</h1>
		<p class="lead">DART·EDGAR·KRX·거시 데이터를 골라 <strong>미리보고</strong>, <strong>다운로드</strong>하거나, 구글시트·엑셀·Python 이 <strong>라이브로 읽는 API</strong>로 가져갑니다.</p>
	</header>

	<div class="quick">
		<span class="quick-label">빠른 시작</span>
		{#each QUICK as ex (ex.label)}
			<button class="chip-ex" onclick={() => loadExample(ex)}>{ex.label}</button>
		{/each}
	</div>

	<section class="panel">
		<div class="modes">
			<button class="modetab" class:on={mode === 'sets'} onclick={() => (mode = 'sets')}>데이터셋</button>
			<button class="modetab" class:on={mode === 'browse'} onclick={switchBrowse}>탐색 — 파일 브라우저</button>
		</div>

		{#if mode === 'sets'}
		<!-- 1. 고르기 -->
		<div class="ctl">
			<label class="fld grow">
				<span class="fld-label">데이터셋</span>
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
			{#if dir}<span class="tag" class:live={eligible}>{eligible ? '라이브 API' : '다운로드 전용'}</span>{/if}
		</div>
		{#if dir && BULK_OBS.has(dir.dir)}<p class="micro">시리즈ID 입력 · 목록은 <code>{dir.dir}/manifest</code></p>{/if}
		{#if probeErr}<p class="err">{probeErr}</p>{/if}

		{#if probing && !previewRows.length}
			<p class="loading">데이터 불러오는 중…</p>
		{/if}

		{#if probed && allCols.length}
			<!-- 2. 미리보기 -->
			<div class="block">
				<div class="block-head">
					<span class="block-title">미리보기</span>
					<span class="block-meta">전체 {totalRows.toLocaleString()}행 · {allCols.length}열 · 처음 {previewCap}행</span>
				</div>
				<div class="tablewrap">
					<table class="ptable">
						<thead><tr>{#each outCols as c (c)}<th>{c}</th>{/each}</tr></thead>
						<tbody>
							{#each previewRows as r, i (i)}
								<tr>{#each outCols as c (c)}<td>{fmt(r[c])}</td>{/each}</tr>
							{/each}
						</tbody>
					</table>
				</div>
				<!-- 옵션 (항상 보임, 미리보기·API 에 즉시 반영) -->
				<div class="opts">
					<div class="opt">
						<span class="opt-k">컬럼</span>
						<div class="colwrap">
							<button class="link-btn" onclick={() => (showCols = !showCols)} aria-expanded={showCols}>{cols.length === 0 || cols.length === allCols.length ? `전체 ${allCols.length}열` : `${cols.length} / ${allCols.length}열`} <span class="caret">{showCols ? '▾' : '▸'}</span></button>
							{#if showCols}<div class="cols">{#each allCols as c (c)}<label class="chip" class:on={pickedCols.has(c)}><input type="checkbox" checked={pickedCols.has(c)} onchange={() => toggleCol(c)} />{c}</label>{/each}</div>{/if}
						</div>
					</div>
					<div class="opt">
						<span class="opt-k">범위</span>
						<div class="range">
							<label class="radio"><input type="radio" value="all" bind:group={limitMode} /> 전체</label>
							<label class="radio"><input type="radio" value="tail" bind:group={limitMode} /> 최근</label>
							<label class="radio"><input type="radio" value="head" bind:group={limitMode} /> 처음</label>
							{#if limitMode !== 'all'}<input class="num" type="number" min="1" bind:value={limitN} /> 행{/if}
							{#if hasDateCol}<span class="sep">·</span><span class="radio">주기<select bind:value={freq}><option value="">원본</option><option value="d">일</option><option value="w">주</option><option value="m">월</option><option value="q">분기</option><option value="y">연</option></select></span>{/if}
						</div>
					</div>
				</div>
			</div>

			<!-- 3. 가져가기 -->
			<div class="get">
				<div class="get-col">
					<span class="get-k">다운로드</span>
					<div class="btns">
						<button class="btn primary" onclick={() => download('xlsx')} disabled={!!busy}>{busy === 'xlsx' ? '변환 중…' : 'Excel (.xlsx)'}</button>
						<button class="btn" onclick={() => download('csv')} disabled={!!busy}>{busy === 'csv' ? '변환 중…' : 'CSV'}</button>
						{#if rawUrl}<a class="btn ghost" href={rawUrl} target="_blank" rel="noopener">원본 .parquet ↗</a>{/if}
					</div>
					<p class="note">가공(Excel/CSV) = 한도 없음·진짜 Number · 원본 = HF parquet{#if fileSize} {fmtBytes(fileSize)}{/if}</p>
				</div>

				{#if eligible && tier2On && liveUrl}
					<div class="get-col api">
						<span class="get-k">라이브 API <span class="muted">— 시트·코드가 URL 을 직접 읽음</span></span>
						<div class="apitabs">
							{#each CONSUMERS as c (c.key)}
								<button class="apitab" class:on={apiTab === c.key} onclick={() => (apiTab = c.key)}>{c.label}</button>
							{/each}
						</div>
						<div class="snippet">
							<pre>{snippet}</pre>
							<button class="btn sm" onclick={() => copy(snippet, 'snip')}>{copiedKey === 'snip' ? '복사됨 ✓' : '복사'}</button>
						</div>
						<p class="note">{apiHint}</p>
					</div>
				{/if}
			</div>
		{/if}
		{:else}
			<!-- 탐색 — 파일 브라우저 (HF 트리 그대로 · 공개 repo) -->
			<div class="browse">
				<div class="crumbs">
					<button class="crumb" onclick={() => loadTree('')}>dartlab-data</button>
					{#each crumbs as seg, i (i)}
						<span class="crumb-sep">/</span>
						<button class="crumb" onclick={() => loadTree(crumbs.slice(0, i + 1).join('/'))}>{seg}</button>
					{/each}
				</div>
				<input class="id-input bsearch" placeholder="이 폴더에서 검색 (파일명·종목코드)" bind:value={filter} aria-label="파일 검색" />
				<div class="tablewrap blist">
					<table class="ptable">
						<tbody>
							{#each shownEntries as e (e.path)}
								<tr class="brow" onclick={() => openEntry(e)}>
									<td class="bname"><span class="bicon">{e.type === 'directory' ? '📁' : e.name.endsWith('.parquet') ? '▦' : '·'}</span>{e.name}</td>
									<td class="bsize">{e.type === 'directory' ? '' : fmtBytes(e.size)}</td>
									<td class="bact">{e.type === 'directory' ? '열기 →' : e.name.endsWith('.parquet') ? '미리보기 →' : '원본 ↗'}</td>
								</tr>
							{/each}
							{#if !shownEntries.length && !browseLoading}<tr><td colspan="3" class="bempty">{filter ? '검색 결과 없음' : '비어 있음'}</td></tr>{/if}
						</tbody>
					</table>
				</div>
				<div class="bfoot">
					<span class="block-meta">{totalCount ? `${totalCount.toLocaleString()}개 항목` : `${entries.length}개`}{#if browseLoading} · 불러오는 중…{/if}{#if filter} · 검색은 불러온 항목 내{/if}</span>
					{#if nextCursor && !filter}<button class="btn sm" onclick={() => loadTree(cwd, true)} disabled={browseLoading}>더 보기</button>{/if}
				</div>
			</div>
		{/if}
	</section>

	<footer class="dc-foot">거대 전량은 <a href="https://huggingface.co/datasets/eddmpython/dartlab-data" target="_blank" rel="noopener">HuggingFace 데이터셋</a>에서.</footer>
</main>

<style>
	.dc {
		max-width: 900px;
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
		font-family: var(--dl-font-head);
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

	.panel {
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-lg);
		background: var(--dl-bg-raised);
		padding: var(--dl-s-4) var(--dl-s-5);
	}

	/* 모드 토글 */
	.modes {
		display: flex;
		gap: var(--dl-s-1);
		margin-bottom: var(--dl-s-4);
		border-bottom: 1px solid var(--dl-line);
	}
	.modetab {
		padding: 0.45rem 0.9rem;
		background: none;
		border: 0;
		border-bottom: 2px solid transparent;
		color: var(--dl-ink-mute);
		font-size: 0.88rem;
		font-weight: 600;
		font-family: inherit;
		cursor: pointer;
		margin-bottom: -1px;
	}
	.modetab:hover {
		color: var(--dl-ink);
	}
	.modetab.on {
		color: var(--dl-accent);
		border-bottom-color: var(--dl-accent);
	}

	/* 탐색 (파일 브라우저) */
	.browse {
		display: flex;
		flex-direction: column;
		gap: var(--dl-s-3);
	}
	.crumbs {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.25rem;
	}
	.crumb {
		background: none;
		border: 0;
		color: var(--dl-accent);
		font-family: var(--dl-font-mono);
		font-size: 0.82rem;
		cursor: pointer;
		padding: 0.1rem 0.2rem;
	}
	.crumb:hover {
		text-decoration: underline;
	}
	.crumb-sep {
		color: var(--dl-ink-faint);
	}
	.bsearch {
		width: 100%;
		max-width: 340px;
	}
	.blist {
		max-height: 440px;
		overflow-y: auto;
	}
	.brow {
		cursor: pointer;
	}
	.brow:hover td {
		background: var(--dl-bg-overlay);
	}
	.bname {
		color: var(--dl-ink);
	}
	.bicon {
		display: inline-block;
		width: 1.4rem;
	}
	.bsize {
		color: var(--dl-ink-mute);
		text-align: right;
		white-space: nowrap;
	}
	.bact {
		color: var(--dl-accent);
		text-align: right;
		white-space: nowrap;
		font-size: 0.72rem;
	}
	.bempty {
		color: var(--dl-ink-mute);
		text-align: center;
		padding: var(--dl-s-4);
	}
	.bfoot {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--dl-s-3);
	}

	/* 고르기 */
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
	.loading {
		margin: var(--dl-s-4) 0 0;
		color: var(--dl-ink-mute);
		font-size: 0.85rem;
	}

	/* 블록 (미리보기) */
	.block {
		margin-top: var(--dl-s-4);
		padding-top: var(--dl-s-4);
		border-top: 1px solid var(--dl-line);
	}
	.block-head {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: var(--dl-s-3);
		margin-bottom: var(--dl-s-2);
		flex-wrap: wrap;
	}
	.block-title {
		font-size: 0.86rem;
		font-weight: 600;
		color: var(--dl-ink-print);
	}
	.block-meta {
		font-size: 0.78rem;
		color: var(--dl-ink-mute);
	}
	.tablewrap {
		overflow-x: auto;
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-md);
		background: var(--dl-bg-base);
	}
	.ptable {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.78rem;
		font-family: var(--dl-font-mono);
	}
	.ptable th {
		position: sticky;
		top: 0;
		text-align: left;
		padding: 0.4rem 0.6rem;
		background: var(--dl-bg-overlay);
		color: var(--dl-ink-dim);
		font-weight: 600;
		white-space: nowrap;
		border-bottom: 1px solid var(--dl-line);
	}
	.ptable td {
		padding: 0.32rem 0.6rem;
		color: var(--dl-ink);
		white-space: nowrap;
		border-bottom: 1px solid var(--dl-line);
	}
	.ptable tbody tr:last-child td {
		border-bottom: 0;
	}
	.ptable tbody tr:hover td {
		background: var(--dl-bg-overlay);
	}

	/* 옵션 */
	.opts {
		display: flex;
		flex-direction: column;
		gap: var(--dl-s-2);
		margin-top: var(--dl-s-3);
	}
	.opt {
		display: flex;
		gap: var(--dl-s-3);
		align-items: baseline;
	}
	.opt-k {
		flex: 0 0 2.6rem;
		font-size: 0.76rem;
		font-weight: 600;
		color: var(--dl-ink-dim);
	}
	.colwrap {
		display: flex;
		flex-direction: column;
		gap: var(--dl-s-2);
		align-items: flex-start;
	}
	.link-btn {
		padding: 0.05rem 0;
		background: none;
		border: 0;
		color: var(--dl-ink);
		font-size: 0.82rem;
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
	.cols {
		display: flex;
		flex-wrap: wrap;
		gap: var(--dl-s-1);
	}
	.chip {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		padding: 0.2rem 0.55rem;
		border-radius: var(--dl-r-pill);
		border: 1px solid var(--dl-line-strong);
		background: var(--dl-bg-overlay);
		color: var(--dl-ink-mute);
		font-size: 0.76rem;
		font-family: var(--dl-font-mono);
		cursor: pointer;
		user-select: none;
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
	.range {
		display: flex;
		flex-wrap: wrap;
		gap: var(--dl-s-2);
		align-items: center;
	}
	.radio {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		font-size: 0.84rem;
		color: var(--dl-ink);
	}
	.sep {
		color: var(--dl-ink-faint);
	}
	.num {
		width: 76px;
		padding: 0.3rem 0.5rem;
	}
	.range select {
		padding: 0.26rem 0.45rem;
		font-size: 0.84rem;
	}

	/* 가져가기 */
	.get {
		display: grid;
		grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr);
		gap: var(--dl-s-5);
		margin-top: var(--dl-s-4);
		padding-top: var(--dl-s-4);
		border-top: 1px solid var(--dl-line);
	}
	.get-col {
		display: flex;
		flex-direction: column;
		gap: var(--dl-s-2);
	}
	.get-k {
		font-size: 0.82rem;
		font-weight: 600;
		color: var(--dl-ink-print);
	}
	.get-k .muted {
		font-weight: 400;
		color: var(--dl-ink-mute);
		font-size: 0.78rem;
	}
	.btns {
		display: flex;
		gap: var(--dl-s-2);
		flex-wrap: wrap;
	}
	.note {
		margin: 0;
		font-size: 0.76rem;
		color: var(--dl-ink-mute);
		line-height: 1.5;
	}
	.apitabs {
		display: flex;
		gap: 0;
		border: 1px solid var(--dl-line-strong);
		border-radius: var(--dl-r-md);
		overflow: hidden;
		width: fit-content;
	}
	.apitab {
		padding: 0.34rem 0.7rem;
		background: transparent;
		border: 0;
		border-right: 1px solid var(--dl-line);
		color: var(--dl-ink-mute);
		font-size: 0.8rem;
		font-family: inherit;
		cursor: pointer;
	}
	.apitab:last-child {
		border-right: 0;
	}
	.apitab.on {
		background: var(--dl-accent);
		color: var(--dl-white, #fff);
		font-weight: 600;
	}
	.snippet {
		display: flex;
		gap: var(--dl-s-2);
		align-items: stretch;
	}
	.snippet pre {
		flex: 1;
		min-width: 0;
		margin: 0;
		padding: 0.5rem 0.6rem;
		border-radius: var(--dl-r-md);
		background: var(--dl-bg-deep);
		border: 1px solid var(--dl-line);
		color: var(--dl-accent-light);
		font-family: var(--dl-font-mono);
		font-size: 0.74rem;
		line-height: 1.5;
		white-space: pre-wrap;
		word-break: break-all;
		overflow: hidden;
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
		padding: 0.4rem 0.7rem;
		font-size: 0.78rem;
		align-self: flex-start;
	}

	.dc-foot {
		margin-top: var(--dl-s-5);
		font-size: 0.8rem;
		color: var(--dl-ink-mute);
	}
	.dc-foot a {
		color: var(--dl-accent);
		text-decoration: none;
	}
	.dc-foot a:hover {
		text-decoration: underline;
	}

	@media (max-width: 640px) {
		.get {
			grid-template-columns: 1fr;
		}
	}

	/* 접근성 — 키보드 포커스 */
	.btn:focus-visible,
	.chip-ex:focus-visible,
	.link-btn:focus-visible,
	.apitab:focus-visible,
	select:focus-visible,
	.id-input:focus-visible,
	.num:focus-visible,
	.chip:focus-within,
	.radio:focus-within {
		outline: 2px solid var(--dl-focus);
		outline-offset: 2px;
		border-radius: var(--dl-r-sm);
	}
</style>
