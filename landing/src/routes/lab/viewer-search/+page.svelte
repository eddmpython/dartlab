<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { Activity, Database, Search, Sparkles, Table2 } from 'lucide-svelte';
	import CompanyQuickSearch from '$lib/components/search/CompanyQuickSearch.svelte';
	import {
		PanelMatrix,
		PanelTocTree,
		TimelineRibbon,
		checkBrowserAiAvailability,
		runBrowserAiPrompt,
		type BrowserAiStatus,
		scanDeepRowsChunked,
		type DeepSearchRow,
		loadPanelBundle,
		buildIndexChunked,
		search,
		type SearchHit,
		type SearchIndex,
		buildEvidencePack,
		highlightParts,
		type EvidenceItem,
		analyzeEvidencePack,
		attachBrowserAiText,
		type ViewerAnalysis,
		loadCompanies,
		type PanelBundle
	} from '@dartlab/ui-surfaces/viewer';

	let { data }: { data: { code: string } } = $props();
	const code = $derived(data.code);

	const COL_CHOICES = [3, 6, 9] as const;
	const DEEP_PERIOD_LIMIT = 4;
	const DEEP_CELL_CAP = 1000;
	const SAMPLE_QUERIES = ['환율 위험', '재고자산', 'AI 반도체 투자', '현금흐름', '당기순이익 감소', '우발부채', '특수관계자 거래', '배당'];

	let nameMap = $state<Map<string, string>>(new Map());
	let bundle = $state<PanelBundle | null>(null);
	let loading = $state(true);
	let errorMsg = $state<string | null>(null);
	let activeSectionKey = $state<string | undefined>(undefined);
	let activeBlock = $state<string | null>(null);
	let windowEnd = $state(0);
	let cols = $state(3);
	let annualOnly = $state(false);
	let query = $state('환율 위험');
	let expand = $state(true);
	let searchIndex = $state<SearchIndex | null>(null);
	let indexing = $state(false);
	let indexMs = $state(0);
	let glowCell = $state<{ rowIndex: number; period: string } | null>(null);
	let highlightCell = $state<{ rowIndex: number; period: string; terms: string[] } | null>(null);
	let deepBuilding = $state(false);
	let deepMs = $state(0);
	let deepRows = $state(0);
	let deepHits = $state<SearchHit[]>([]);
	let deepError = $state<string | null>(null);
	let browserAi = $state<BrowserAiStatus>({ status: 'unsupported' });
	let analysis = $state<ViewerAnalysis | null>(null);
	let aiRunning = $state(false);
	let aiError = $state<string | null>(null);
	let aiMs = $state(0);
	let aiDownloadRatio = $state<number | null>(null);
	let requestSeq = 0;

	onMount(() => {
		void loadCompanies().then((companies) => (nameMap = new Map(companies.map((item) => [item.code, item.name]))));
		void checkBrowserAiAvailability().then((status) => (browserAi = status));
	});

	$effect(() => {
		const c = code;
		loading = true;
		errorMsg = null;
		bundle = null;
		searchIndex = null;
		deepHits = [];
		deepError = null;
		analysis = null;
		aiError = null;
		aiMs = 0;
		void loadPanelBundle(c)
			.then((next) => {
				if (code !== c) return;
				bundle = next;
				activeSectionKey = next.toc.chapters[0]?.sections[0]?.sectionKey;
				activeBlock = null;
				windowEnd = 0;
				if (!next.periods.length) errorMsg = '이 종목의 panel 데이터가 없습니다.';
			})
			.catch((error) => {
				if (code === c) errorMsg = `로드 실패: ${error instanceof Error ? error.message : String(error)}`;
			})
			.finally(() => {
				if (code === c) loading = false;
			});
	});

	$effect(() => {
		const current = bundle;
		searchIndex = null;
		indexMs = 0;
		if (!current || !current.periods.length) {
			indexing = false;
			return;
		}
		let cancelled = false;
		indexing = true;
		const started = performance.now();
		void buildIndexChunked(current).then((idx) => {
			if (cancelled) return;
			searchIndex = idx;
			indexMs = performance.now() - started;
			indexing = false;
		});
		return () => {
			cancelled = true;
		};
	});

	const corpName = $derived(bundle?.corpName || nameMap.get(code) || code);
	const periods = $derived(bundle?.periods ?? []);
	const annualPeriods = $derived.by(() => {
		const current = bundle;
		return current ? periods.filter((period) => current.periodKind[period] === 'annual') : [];
	});
	const visiblePeriods = $derived(annualOnly && annualPeriods.length ? annualPeriods : periods);
	const windowPeriods = $derived(visiblePeriods.slice(windowEnd, windowEnd + cols));
	const dartUrls = $derived(bundle?.dartUrlByPeriod ?? {});
	const rows = $derived.by(() => {
		if (!activeSectionKey || !bundle) return [];
		const sectionRows = bundle.gridBySection.get(activeSectionKey) ?? [];
		return activeBlock ? sectionRows.filter((row) => row.blockLeaf === activeBlock) : sectionRows;
	});
	const baseResult = $derived.by(() => {
		if (!searchIndex || query.trim().length < 1) return { hits: [] as SearchHit[], added: [] as string[] };
		return search(searchIndex, query, { topK: 12, expand });
	});
	const evidencePack = $derived.by(() => {
		if (!searchIndex || query.trim().length < 1) return null;
		return buildEvidencePack(searchIndex, query, { topK: 10, expand });
	});
	const canAnalyze = $derived.by(() => Boolean(bundle && searchIndex && query.trim().length > 0 && !indexing && !aiRunning));
	const canNewer = $derived(windowEnd > 0);
	const canOlder = $derived(windowEnd + cols < visiblePeriods.length);

	$effect(() => {
		query;
		expand;
		deepHits;
		analysis = null;
		aiError = null;
		aiMs = 0;
		aiDownloadRatio = null;
	});

	function gotoCompany(nextCode: string) {
		void goto(`${base}/lab/viewer-search?code=${nextCode}`);
	}

	function pickSection(sectionKey: string) {
		activeSectionKey = sectionKey;
		activeBlock = null;
	}

	function pickBlock(sectionKey: string, blockLeaf: string) {
		activeSectionKey = sectionKey;
		activeBlock = blockLeaf;
	}

	function pickPeriod(period: string) {
		const idx = visiblePeriods.indexOf(period);
		if (idx >= 0) windowEnd = idx;
	}

	function moveNewer() {
		windowEnd = Math.max(0, windowEnd - 1);
	}

	function moveOlder() {
		windowEnd = Math.min(Math.max(0, visiblePeriods.length - cols), windowEnd + 1);
	}

	function focusHit(hit: SearchHit) {
		pickSection(hit.sectionKey);
		pickPeriod(hit.period);
		const terms = hit.matchedTerms.length ? hit.matchedTerms : query.split(/\s+/).filter((term) => term.length >= 2);
		glowCell = { rowIndex: hit.rowIndex, period: hit.period };
		highlightCell = { rowIndex: hit.rowIndex, period: hit.period, terms };
		window.setTimeout(() => (glowCell = null), 2200);
	}

	function focusEvidence(item: EvidenceItem) {
		focusHit({
			sectionKey: item.sectionKey,
			rowIndex: item.rowIndex,
			chapter: item.chapter,
			section: item.section,
			block: item.block,
			scope: item.scope,
			period: item.period,
			score: item.score,
			snippet: item.snippet,
			matchKind: item.matchKind,
			matchedTerms: item.matchedTerms,
			stale: false // 재구성은 점프·glow 좌표용(섹션/행/기간) · 칩 재표시 아님이라 stale 무관
		});
	}

	function tableRowsForDeepSearch(source: PanelBundle): DeepSearchRow[] {
		const out: DeepSearchRow[] = [];
		const scanPeriods = source.periods.slice(0, DEEP_PERIOD_LIMIT);
		for (const [sectionKey, sectionRows] of source.gridBySection) {
			for (let rowIndex = 0; rowIndex < sectionRows.length; rowIndex++) {
				const row = sectionRows[rowIndex];
				if (row.blockType !== 'table') continue;
				const cells: Record<string, string> = {};
				for (const period of scanPeriods) {
					const value = row.cells[period];
					if (value) cells[period] = value.length > DEEP_CELL_CAP ? value.slice(0, DEEP_CELL_CAP) : value;
				}
				if (Object.keys(cells).length === 0) continue;
				out.push({
					sectionKey,
					rowIndex,
					chapter: row.chapter,
					section: row.sectionLeaf,
					block: row.blockLeaf,
					scope: row.scope ?? '',
					cells
				});
			}
		}
		return out;
	}

	async function runDeepSearch() {
		if (!bundle || !query.trim() || deepBuilding) return;
		const requestId = ++requestSeq;
		deepError = null;
		deepHits = [];
		deepMs = 0;
		deepBuilding = true;
		const rows = tableRowsForDeepSearch(bundle);
		deepRows = rows.length;
		try {
			const result = await scanDeepRowsChunked(rows, query, { topK: 20, expand, cellCap: DEEP_CELL_CAP, chunkRows: 64 });
			if (requestSeq !== requestId) return;
			deepHits = result.hits;
			deepMs = result.ms;
			deepRows = result.rows;
		} catch (error) {
			if (requestSeq === requestId) deepError = error instanceof Error ? error.message : String(error);
		} finally {
			if (requestSeq === requestId) deepBuilding = false;
		}
	}

	async function runAiAnalysis() {
		if (!bundle || !evidencePack || aiRunning) return;
		aiRunning = true;
		aiError = null;
		aiDownloadRatio = null;
		const started = performance.now();
		const baseAnalysis = analyzeEvidencePack({
			code,
			companyName: corpName,
			periodCount: periods.length,
			evidencePack,
			deepHits
		});
		analysis = baseAnalysis;
		try {
			if (browserAi.status === 'available') {
				const modelText = await runBrowserAiPrompt(baseAnalysis.prompt, {
					onDownload(progress) {
						aiDownloadRatio = typeof progress.ratio === 'number' ? progress.ratio : null;
					}
				});
				analysis = attachBrowserAiText(baseAnalysis, modelText);
				browserAi = { status: 'available', raw: 'available' };
			}
		} catch (error) {
			aiError = `브라우저 AI 실패, 근거팩 분석 유지: ${error instanceof Error ? error.message : String(error)}`;
			browserAi = await checkBrowserAiAvailability();
		} finally {
			aiMs = performance.now() - started;
			aiRunning = false;
		}
	}

	function kindLabel(kind: SearchHit['matchKind']): string {
		if (kind === 'table') return '표';
		if (kind === 'amount') return '금액';
		return '본문';
	}

	function hitLabel(hit: SearchHit | EvidenceItem): string {
		return [hit.chapter, hit.section, hit.block].filter(Boolean).join(' > ');
	}

	function aiStatusLabel(status: BrowserAiStatus['status']): string {
		if (status === 'available') return 'model ready';
		if (status === 'downloadable') return 'downloadable';
		if (status === 'downloading') return 'downloading';
		if (status === 'unavailable') return 'unavailable';
		if (status === 'error') return 'error';
		return 'evidence mode';
	}

	function confidenceLabel(confidence: ViewerAnalysis['confidence']): string {
		if (confidence === 'high') return '높음';
		if (confidence === 'medium') return '중간';
		return '낮음';
	}
</script>

<svelte:head>
	<title>{corpName} viewer search lab · dartlab</title>
	<meta name="robots" content="noindex" />
</svelte:head>

<main class="page">
	<header class="topbar">
		<a class="brand" href={`${base}/lab`}>dartlab / lab</a>
		<div class="company-slot">
			<CompanyQuickSearch onpick={gotoCompany} placeholder="회사명·종목코드로 lab 열기" />
		</div>
		<a class="viewer-link" href={`${base}/viewer/company/${code}`}>본진 viewer</a>
	</header>

	<section class="hero">
		<div>
			<div class="eyebrow">viewer search lab</div>
			<h1>{corpName}</h1>
			<div class="meta">{code} · 기간 {periods.length} · 현재 섹션 행 {rows.length}</div>
		</div>
		<div class="metrics">
			<div class="metric"><Activity size={14} /> 기본색인 {indexing ? '준비 중' : searchIndex ? `${indexMs.toFixed(0)}ms` : '-'}</div>
			<div class="metric"><Database size={14} /> 행 {searchIndex?.rows.length ?? 0} · vocab {searchIndex?.vocab ?? 0}</div>
			<div class="metric"><Table2 size={14} /> deep {deepBuilding ? `검색 중 ${deepRows || '-'}행` : deepRows ? `${deepRows}행 스캔` : '대기'}</div>
			<div class="metric"><Sparkles size={14} /> AI {aiRunning ? '분석 중' : aiStatusLabel(browserAi.status)}</div>
		</div>
	</section>

	<section class="controls">
		<div class="querybox">
			<Search size={16} />
			<input bind:value={query} type="search" aria-label="현재 공시 내용 검색" placeholder="공시 안에서 찾기" onkeydown={(event) => event.key === 'Enter' && runDeepSearch()} />
			<button type="button" class:active={expand} onclick={() => (expand = !expand)}>동의어</button>
			<button type="button" onclick={runDeepSearch} disabled={!bundle || deepBuilding}>
				{deepBuilding ? '표 검색 중' : '표까지 검색'}
			</button>
			<button type="button" class="ai-run" onclick={runAiAnalysis} disabled={!canAnalyze}>
				<Sparkles size={14} /> {aiRunning ? '분석 중' : '분석'}
			</button>
		</div>
		<div class="samples">
			{#each SAMPLE_QUERIES as sample}
				<button type="button" class:active={query === sample} onclick={() => (query = sample)}>{sample}</button>
			{/each}
		</div>
	</section>

	{#if loading}
		<div class="state"><div class="spinner"></div><p>{corpName} panel 로드 중</p></div>
	{:else if errorMsg}
		<div class="state error"><p>{errorMsg}</p></div>
	{:else if bundle}
		<section class="workspace">
			<aside class="left">
				<div class="panel-title">TOC</div>
				<PanelTocTree toc={bundle.toc} {activeSectionKey} {activeBlock} onpick={pickSection} onpickBlock={pickBlock} />
			</aside>

			<section class="center">
				<div class="ribbon">
					<TimelineRibbon periods={visiblePeriods} {windowPeriods} onpick={pickPeriod} onnewer={moveNewer} onolder={moveOlder} {canNewer} {canOlder} />
					<div class="view-controls">
						<button type="button" class:active={annualOnly} onclick={() => ((annualOnly = !annualOnly), (windowEnd = 0))}>연간</button>
						{#each COL_CHOICES as choice}
							<button type="button" class:active={cols === choice} onclick={() => (cols = choice)}>{choice}</button>
						{/each}
					</div>
				</div>
				<PanelMatrix {rows} periods={windowPeriods} dartUrlByPeriod={dartUrls} glow={glowCell} highlight={highlightCell} />
			</section>

			<aside class="right">
				<div class="result-group">
					<div class="panel-title">기본 검색 <span>{baseResult.hits.length}</span></div>
					{#if indexing}
						<div class="empty">색인 준비 중</div>
					{:else if baseResult.hits.length === 0}
						<div class="empty">결과 없음</div>
					{:else}
						{#each baseResult.hits as hit, i (`base-${hit.sectionKey}-${hit.rowIndex}-${i}`)}
							<button type="button" class="hit" onmousedown={() => focusHit(hit)}>
								<div class="hit-head">
									<span>{kindLabel(hit.matchKind)}</span>
									<code>{hit.period}</code>
								</div>
								<strong>{hitLabel(hit)}</strong>
								<p>
									{#each highlightParts(hit.snippet, hit.matchedTerms) as part}
										{#if part.hit}<mark>{part.text}</mark>{:else}{part.text}{/if}
									{/each}
								</p>
							</button>
						{/each}
					{/if}
				</div>

				<div class="result-group">
					<div class="panel-title">근거팩 <span>{evidencePack?.stats.total ?? 0}</span></div>
					{#if evidencePack}
						<div class="pack-stats">
							<span>본문 {evidencePack.stats.text}</span>
							<span>표 {evidencePack.stats.table}</span>
							<span>금액 {evidencePack.stats.amount}</span>
						</div>
						{#each evidencePack.items as item (item.id)}
							<button type="button" class="hit evidence" onmousedown={() => focusEvidence(item)}>
								<div class="hit-head">
									<span>{kindLabel(item.matchKind)}</span>
									<code>{item.period}</code>
								</div>
								<strong>{hitLabel(item)}</strong>
								<p>{item.snippet}</p>
							</button>
						{/each}
					{:else}
						<div class="empty">검색어를 입력하면 생성</div>
					{/if}
				</div>

				<div class="result-group analyst">
					<div class="panel-title">AI analyst <span>{analysis ? confidenceLabel(analysis.confidence) : aiStatusLabel(browserAi.status)}</span></div>
					<div class="pack-stats">
						<span>{analysis?.modelMode ?? 'evidence'}</span>
						<span>{aiMs ? `${aiMs.toFixed(0)}ms` : 'standby'}</span>
						{#if aiDownloadRatio !== null}
							<span>{Math.round(aiDownloadRatio * 100)}%</span>
						{/if}
					</div>
					{#if aiRunning && !analysis}
						<div class="empty">분석 중</div>
					{:else if analysis}
						<p class="analysis-answer">{analysis.modelText ?? analysis.answer}</p>
						<div class="signals">
							{#each analysis.signals as signal}
								<div class="signal">
									<span>{signal.label}</span>
									<strong>{signal.value}</strong>
									<small>{signal.detail}</small>
								</div>
							{/each}
						</div>
						<div class="analysis-evidence">
							{#each analysis.evidence as item (item.id)}
								<button type="button" class="mini-hit" onmousedown={() => focusEvidence(item)}>
									<code>{item.period}</code>
									<span>{hitLabel(item)}</span>
								</button>
							{/each}
						</div>
						<div class="next-queries">
							{#each analysis.nextQueries as nextQuery}
								<button type="button" onclick={() => (query = nextQuery)}>{nextQuery}</button>
							{/each}
						</div>
					{:else}
						<div class="empty">근거팩 생성 후 분석 실행</div>
					{/if}
					{#if aiError}
						<div class="empty error">{aiError}</div>
					{/if}
				</div>

				<div class="result-group">
					<div class="panel-title">표 deep search <span>{deepHits.length}</span></div>
					<div class="pack-stats"><span>최신 {DEEP_PERIOD_LIMIT}기간</span><span>셀 {DEEP_CELL_CAP}자</span></div>
					{#if deepError}
						<div class="empty error">{deepError}</div>
					{:else if deepBuilding}
						<div class="empty">표 본문 검색 중 · {deepRows || '-'}행</div>
					{:else if deepRows === 0}
						<div class="empty">표 본문 검색은 버튼으로 실행</div>
					{:else if deepHits.length === 0}
						<div class="empty">결과 없음 · {deepMs.toFixed(1)}ms</div>
					{:else}
						<div class="pack-stats"><span>{deepMs.toFixed(1)}ms</span></div>
						{#each deepHits as hit, i (`deep-${hit.sectionKey}-${hit.rowIndex}-${i}`)}
							<button type="button" class="hit" onmousedown={() => focusHit(hit)}>
								<div class="hit-head">
									<span>{kindLabel(hit.matchKind)}</span>
									<code>{hit.period}</code>
								</div>
								<strong>{hitLabel(hit)}</strong>
								<p>{hit.snippet}</p>
							</button>
						{/each}
					{/if}
				</div>
			</aside>
		</section>
	{/if}
</main>

<style>
	.page {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		background: #050811;
		color: #f1f5f9;
	}
	.topbar {
		position: sticky;
		top: 0;
		z-index: 90;
		display: grid;
		grid-template-columns: auto minmax(240px, 420px) auto;
		align-items: center;
		gap: 14px;
		height: 54px;
		padding: 0 16px;
		border-bottom: 1px solid #1e2433;
		background: rgba(5, 8, 17, 0.94);
		backdrop-filter: blur(10px);
	}
	.brand,
	.viewer-link {
		color: #cbd5e1;
		text-decoration: none;
		font-size: 13px;
		font-weight: 700;
		white-space: nowrap;
	}
	.viewer-link {
		justify-self: end;
		color: var(--dl-accent);
	}
	.company-slot {
		min-width: 0;
	}
	.hero {
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		gap: 20px;
		padding: 18px 16px 14px;
		border-bottom: 1px solid #1e2433;
	}
	.eyebrow {
		color: #64748b;
		font-size: 10px;
		font-weight: 800;
		text-transform: uppercase;
	}
	h1 {
		margin: 4px 0;
		font-size: 25px;
		font-weight: 850;
	}
	.meta {
		color: #94a3b8;
		font-size: 12px;
	}
	.metrics {
		display: flex;
		align-items: center;
		gap: 8px;
		flex-wrap: wrap;
		justify-content: flex-end;
	}
	.metric {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		height: 28px;
		padding: 0 9px;
		border: 1px solid #1e2433;
		border-radius: 6px;
		color: #94a3b8;
		background: #0a0e18;
		font-size: 11px;
	}
	.controls {
		display: flex;
		flex-direction: column;
		gap: 8px;
		padding: 10px 16px;
		border-bottom: 1px solid #1e2433;
	}
	.querybox {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.querybox input {
		flex: 1 1 auto;
		min-width: 0;
		height: 34px;
		padding: 0 11px;
		border: 1px solid #1e2433;
		border-radius: 6px;
		background: #0a0e18;
		color: #f1f5f9;
		font: inherit;
		font-size: 13px;
		outline: none;
	}
	.querybox input:focus {
		border-color: var(--dl-accent);
	}
	button {
		font: inherit;
	}
	.querybox button,
	.samples button,
	.view-controls button {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
		height: 30px;
		padding: 0 10px;
		border: 1px solid #1e2433;
		border-radius: 6px;
		background: #050811;
		color: #94a3b8;
		font-size: 12px;
		cursor: pointer;
		white-space: nowrap;
	}
	.querybox button:hover,
	.samples button:hover,
	.view-controls button:hover,
	.querybox button.active,
	.samples button.active,
	.view-controls button.active {
		border-color: rgba(var(--dl-accent-rgb), 0.55);
		color: var(--dl-accent);
		background: rgba(var(--dl-accent-rgb), 0.09);
	}
	.querybox button:disabled {
		opacity: 0.45;
		cursor: default;
	}
	.querybox .ai-run {
		border-color: rgba(56, 189, 248, 0.45);
		color: #bae6fd;
		background: rgba(14, 165, 233, 0.08);
	}
	.samples {
		display: flex;
		gap: 6px;
		overflow-x: auto;
		padding-bottom: 2px;
	}
	.workspace {
		flex: 1 1 auto;
		min-height: 0;
		display: grid;
		grid-template-columns: 240px minmax(0, 1fr) 360px;
	}
	.left,
	.right {
		min-height: 0;
		overflow-y: auto;
		border-right: 1px solid #1e2433;
		background: #050811;
	}
	.right {
		border-right: none;
		border-left: 1px solid #1e2433;
		padding: 10px;
	}
	.center {
		min-width: 0;
		min-height: 0;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}
	.ribbon {
		flex-shrink: 0;
		display: grid;
		grid-template-columns: minmax(0, 1fr) auto;
		gap: 8px;
		align-items: center;
		padding: 7px 10px;
		border-bottom: 1px solid #1e2433;
	}
	.view-controls {
		display: flex;
		align-items: center;
		gap: 4px;
	}
	.panel-title {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
		padding: 7px 8px;
		color: #94a3b8;
		font-size: 11px;
		font-weight: 800;
		text-transform: uppercase;
	}
	.panel-title span {
		color: var(--dl-accent);
	}
	.result-group + .result-group {
		margin-top: 12px;
		padding-top: 12px;
		border-top: 1px solid #1e2433;
	}
	.hit {
		display: flex;
		flex-direction: column;
		gap: 5px;
		width: 100%;
		margin-bottom: 6px;
		padding: 9px;
		border: 1px solid #1e2433;
		border-radius: 7px;
		background: #0a0e18;
		color: #cbd5e1;
		text-align: left;
		cursor: pointer;
	}
	.hit:hover {
		border-color: rgba(var(--dl-accent-rgb), 0.55);
	}
	.hit-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
		color: #64748b;
		font-size: 10px;
	}
	.hit-head span {
		color: var(--dl-accent);
	}
	.hit strong {
		font-size: 12px;
		color: #e2e8f0;
		line-height: 1.35;
	}
	.hit p {
		margin: 0;
		color: #94a3b8;
		font-size: 12px;
		line-height: 1.45;
	}
	mark {
		padding: 0 2px;
		border-radius: 3px;
		background: rgba(251, 191, 36, 0.22);
		color: #fef3c7;
	}
	.pack-stats {
		display: flex;
		gap: 5px;
		flex-wrap: wrap;
		padding: 0 0 7px;
	}
	.pack-stats span {
		padding: 2px 7px;
		border: 1px solid #1e2433;
		border-radius: 999px;
		color: #94a3b8;
		font-size: 10px;
	}
	.analysis-answer {
		margin: 0 0 9px;
		padding: 10px;
		border: 1px solid #1e2433;
		border-radius: 7px;
		background: #0a0e18;
		color: #dbeafe;
		font-size: 12px;
		line-height: 1.55;
		white-space: pre-wrap;
	}
	.signals {
		display: grid;
		gap: 6px;
	}
	.signal {
		display: grid;
		gap: 3px;
		padding: 8px;
		border: 1px solid #1e2433;
		border-radius: 7px;
		background: #070b14;
	}
	.signal span {
		color: #64748b;
		font-size: 10px;
		text-transform: uppercase;
	}
	.signal strong {
		color: #e2e8f0;
		font-size: 12px;
		line-height: 1.35;
	}
	.signal small {
		color: #94a3b8;
		font-size: 11px;
		line-height: 1.35;
	}
	.analysis-evidence,
	.next-queries {
		display: flex;
		flex-wrap: wrap;
		gap: 5px;
		margin-top: 8px;
	}
	.mini-hit,
	.next-queries button {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		max-width: 100%;
		padding: 5px 7px;
		border: 1px solid #1e2433;
		border-radius: 6px;
		background: #050811;
		color: #94a3b8;
		font-size: 11px;
		cursor: pointer;
	}
	.mini-hit span {
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.mini-hit:hover,
	.next-queries button:hover {
		border-color: rgba(56, 189, 248, 0.5);
		color: #bae6fd;
	}
	.empty,
	.state {
		color: #64748b;
		font-size: 12px;
	}
	.empty {
		padding: 12px;
		text-align: center;
	}
	.state {
		flex: 1 1 auto;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 12px;
	}
	.error {
		color: #f87171;
	}
	.spinner {
		width: 24px;
		height: 24px;
		border: 2px solid #1e2433;
		border-top-color: var(--dl-accent);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
	@media (max-width: 1180px) {
		.workspace {
			grid-template-columns: 220px minmax(0, 1fr);
		}
		.right {
			grid-column: 1 / -1;
			border-left: none;
			border-top: 1px solid #1e2433;
			max-height: 360px;
		}
	}
	@media (max-width: 760px) {
		.topbar {
			grid-template-columns: 1fr auto;
			height: auto;
			padding: 10px;
		}
		.company-slot {
			grid-column: 1 / -1;
			order: 3;
		}
		.hero,
		.querybox {
			align-items: stretch;
			flex-direction: column;
		}
		.workspace {
			grid-template-columns: 1fr;
		}
		.left {
			max-height: 180px;
			border-right: none;
			border-bottom: 1px solid #1e2433;
		}
		.ribbon {
			grid-template-columns: 1fr;
		}
		.metrics {
			justify-content: flex-start;
		}
	}
</style>
