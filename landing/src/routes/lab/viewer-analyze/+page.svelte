<script lang="ts">
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { Activity, Hash, Percent, Search, Sparkles, TrendingDown, TrendingUp } from 'lucide-svelte';
	import CompanyQuickSearch from '$lib/components/search/CompanyQuickSearch.svelte';
	import {
		PanelMatrix,
		PanelTocTree,
		TimelineRibbon,
		loadPanelBundle,
		loadCompanies,
		analyzeViewport,
		financeSignals,
		type CellFacet,
		type FinanceSignal,
		financeAvailability,
		loadFinanceStatement,
		narrateSignals,
		webgpuAvailable,
		type FinanceKind,
		type FinanceScope,
		type PanelBundle
	} from '@dartlab/ui-surfaces/viewer';

	let { data }: { data: { code: string } } = $props();
	const code = $derived(data.code);

	const COL_CHOICES = [3, 6, 9] as const;
	const SAMPLES = ['100억 이상', '1조 이상', '500억 이상', '50억 이하'];
	const FIN_KINDS: { k: FinanceKind; label: string }[] = [
		{ k: 'IS', label: '손익' },
		{ k: 'BS', label: '재무상태' },
		{ k: 'CF', label: '현금흐름' }
	];

	let nameMap = $state<Map<string, string>>(new Map());
	let bundle = $state<PanelBundle | null>(null);
	let loading = $state(true);
	let errorMsg = $state<string | null>(null);
	let activeSectionKey = $state<string | undefined>(undefined);
	let activeBlock = $state<string | null>(null);
	let windowEnd = $state(0);
	let cols = $state(6);
	let annualOnly = $state(false);
	let query = $state('');
	let glowCell = $state<{ rowIndex: number; period: string } | null>(null);

	// finance 신호
	let financeKind = $state<FinanceKind>('IS');
	let financeScope = $state<FinanceScope | null>(null);
	let financeLoading = $state(false);
	let financeErr = $state<string | null>(null);
	let financeSigs = $state<FinanceSignal[]>([]);
	let financeRan = $state(false);

	// WebLLM 내레이션 (실험) · 결정론 신호를 한국어로 다듬기만(숫자 불변). WebGPU 없으면 비활성.
	let webgpuOk = $state(false);
	let llmText = $state<string | null>(null);
	let llmLoading = $state(false);
	let llmErr = $state<string | null>(null);
	let llmProgress = $state(0);

	$effect(() => {
		webgpuOk = webgpuAvailable();
		void loadCompanies().then((companies) => (nameMap = new Map(companies.map((c) => [c.code, c.name]))));
	});

	$effect(() => {
		const c = code;
		loading = true;
		errorMsg = null;
		bundle = null;
		financeSigs = [];
		financeRan = false;
		financeErr = null;
		void loadPanelBundle(c)
			.then((next) => {
				if (code !== c) return;
				bundle = next;
				activeSectionKey = next.toc.chapters[0]?.sections[0]?.sectionKey;
				activeBlock = null;
				windowEnd = 0;
				if (!next.periods.length) errorMsg = '이 종목의 panel 데이터가 없습니다.';
			})
			.catch((e) => {
				if (code === c) errorMsg = `로드 실패: ${e instanceof Error ? e.message : String(e)}`;
			})
			.finally(() => {
				if (code === c) loading = false;
			});
	});

	const corpName = $derived(bundle?.corpName || nameMap.get(code) || code);
	const periods = $derived(bundle?.periods ?? []);
	const annualPeriods = $derived.by(() => {
		const cur = bundle;
		return cur ? periods.filter((p) => cur.periodKind[p] === 'annual') : [];
	});
	const visiblePeriods = $derived(annualOnly && annualPeriods.length ? annualPeriods : periods);
	const windowPeriods = $derived(visiblePeriods.slice(windowEnd, windowEnd + cols));
	const dartUrls = $derived(bundle?.dartUrlByPeriod ?? {});
	const rows = $derived.by(() => {
		if (!activeSectionKey || !bundle) return [];
		const secRows = bundle.gridBySection.get(activeSectionKey) ?? [];
		return activeBlock ? secRows.filter((r) => r.blockLeaf === activeBlock) : secRows;
	});
	const sectionLabel = $derived(activeSectionKey ? activeSectionKey.split('␟').slice(1).join(' · ') : '');

	// ★화면 내 분석 · viewport(현재 섹션×보이는 기간) 위 결정론 facet 분석. activeSection/window/query 바뀌면 자동 재계산.
	const viewport = $derived.by(() =>
		activeSectionKey && rows.length ? analyzeViewport(rows, windowPeriods, { sectionKey: activeSectionKey, query: query.trim() || undefined }) : null
	);
	const canOlder = $derived(windowEnd + cols < visiblePeriods.length);
	const canNewer = $derived(windowEnd > 0);

	function gotoCompany(next: string) {
		void goto(`${base}/lab/viewer-analyze?code=${next}`);
	}
	function pickSection(sectionKey: string) {
		activeSectionKey = sectionKey;
		activeBlock = null;
	}
	function pickBlock(sectionKey: string, blockLeaf: string) {
		activeSectionKey = sectionKey;
		activeBlock = blockLeaf;
	}
	function pickPeriod(p: string) {
		const idx = visiblePeriods.indexOf(p);
		if (idx >= 0) windowEnd = Math.min(Math.max(0, idx), Math.max(0, visiblePeriods.length - cols));
	}
	function moveNewer() {
		windowEnd = Math.max(0, windowEnd - 1);
	}
	function moveOlder() {
		windowEnd = Math.min(Math.max(0, visiblePeriods.length - cols), windowEnd + 1);
	}
	function focusFacet(f: CellFacet) {
		if (!windowPeriods.includes(f.period)) pickPeriod(f.period);
		glowCell = { rowIndex: f.rowIndex, period: f.period };
		window.setTimeout(() => (glowCell = null), 2200);
	}

	async function loadFinance() {
		if (!bundle || financeLoading) return;
		financeLoading = true;
		financeErr = null;
		financeSigs = [];
		financeRan = true;
		try {
			const avail = await financeAvailability(code, 'KR');
			const scope: FinanceScope = avail.scopes.includes('CFS') ? 'CFS' : (avail.scopes[0] ?? 'CFS');
			const freq = financeKind === 'CF' ? 'annual' : 'quarter';
			const stmt = await loadFinanceStatement(code, 'KR', financeKind, freq, scope);
			if (!stmt || !stmt.rows.length) {
				financeErr = '재무 데이터 없음 (이 종목·구분은 미보고)';
				return;
			}
			financeScope = scope;
			financeSigs = financeSignals(stmt, { minRun: 4, minDeltaPct: 0.3, topK: 12 });
			if (!financeSigs.length) financeErr = '주목할 신호 없음 (전부 평탄/소폭 변동)';
		} catch (e) {
			financeErr = e instanceof Error ? e.message : String(e);
		} finally {
			financeLoading = false;
		}
	}
	function pickFinanceKind(k: FinanceKind) {
		if (financeKind === k) return;
		financeKind = k;
		if (financeRan) void loadFinance();
	}

	const won = (v: number): string => {
		const a = Math.abs(v);
		const sign = v < 0 ? '-' : '';
		if (a >= 1e12) return `${sign}${(a / 1e12).toFixed(2)}조`;
		if (a >= 1e8) return `${sign}${(a / 1e8).toFixed(1)}억`;
		if (a >= 1e4) return `${sign}${(a / 1e4).toFixed(0)}만`;
		return `${sign}${a.toLocaleString()}`;
	};
	const pct = (v: number | null): string => (v === null ? '-' : `${v > 0 ? '+' : ''}${(v * 100).toFixed(0)}%`);
	function kindBadge(k: FinanceSignal['kind']): string {
		if (k === 'flip') return '부호전환';
		if (k === 'streak') return '연속추세';
		return '큰변동';
	}

	// 결정론 한국어 내레이션 (model 0 · 숫자 절대 안 틀림). 신호를 문장으로 조립할 뿐 새 사실 생성 X.
	const narration = $derived.by(() => {
		const va = viewport;
		if (!va) return '';
		const parts: string[] = [];
		parts.push(`이 화면(${va.periods.length}기간·${va.rowsVisible}행): 금액 ${va.amountCells}곳·비율 ${va.percentCells}곳·연도 ${va.yearCells}곳.`);
		if (va.biggestAmount > 0) parts.push(`최대 금액 ${won(va.biggestAmount)}.`);
		if (va.constraint && va.constraintHits.length) parts.push(`입력 조건 만족 ${va.constraintHits.length}곳 · BM25 검색이 구조적으로 못 찾는 정량 조건을 산술로 포착.`);
		const flips = financeSigs.filter((s) => s.kind === 'flip');
		const streaks = financeSigs.filter((s) => s.kind === 'streak');
		const movers = financeSigs.filter((s) => s.kind === 'mover');
		if (flips.length) parts.push(`재무 부호전환 ${flips.length}건 (${flips[0].label} ${flips[0].flipAt} 흑↔적자).`);
		if (streaks.length) parts.push(`연속 추세 ${streaks.length}건 (${streaks[0].label} ${streaks[0].monotoneRun}기간 ${streaks[0].direction === 'up' ? '증가' : '감소'}).`);
		if (movers.length) parts.push(`직전 대비 큰 변동 ${movers.length}건 (${movers[0].label} ${pct(movers[0].deltaPct)}).`);
		return parts.join(' ');
	});

	// 화면/신호가 바뀌면 이전 LLM 다듬기 결과 무효화 (stale 방지).
	$effect(() => {
		void narration;
		llmText = null;
		llmErr = null;
		llmProgress = 0;
	});

	async function runLlmNarration() {
		if (!narration || llmLoading) return;
		llmLoading = true;
		llmErr = null;
		llmProgress = 0;
		try {
			llmText = await narrateSignals(narration, { onProgress: (p) => (llmProgress = p.progress) });
		} catch (e) {
			llmErr = e instanceof Error ? e.message : String(e);
		} finally {
			llmLoading = false;
		}
	}
</script>

<svelte:head>
	<title>{corpName} 화면 분석 lab · dartlab</title>
	<meta name="robots" content="noindex" />
</svelte:head>

<main class="page">
	<header class="topbar">
		<a class="brand" href={`${base}/lab`}>dartlab / lab</a>
		<div class="company-slot">
			<CompanyQuickSearch onpick={gotoCompany} placeholder="회사명·종목코드로 분석 lab 열기" />
		</div>
		<a class="viewer-link" href={`${base}/viewer/company/${code}`}>본진 viewer</a>
	</header>

	<section class="hero">
		<div>
			<div class="eyebrow">viewport analysis lab · 결정론 facet + 재무신호 (LLM 0)</div>
			<h1>{corpName}</h1>
			<div class="meta">{code} · {sectionLabel || '섹션 선택'} · 기간 {periods.length}</div>
		</div>
		{#if viewport}
			<div class="metrics">
				<div class="metric"><Hash size={13} /> 금액 {viewport.amountCells}</div>
				<div class="metric"><Percent size={13} /> 비율 {viewport.percentCells}</div>
				<div class="metric"><Activity size={13} /> 최대 {viewport.biggestAmount > 0 ? won(viewport.biggestAmount) : '-'}</div>
			</div>
		{/if}
	</section>

	<section class="controls">
		<div class="querybox">
			<Search size={16} />
			<input bind:value={query} type="search" aria-label="정량 조건 검색" placeholder="정량 조건: 100억 이상 · 1조 이상 · 50억 이하" />
		</div>
		<div class="samples">
			{#each SAMPLES as s}
				<button type="button" class:active={query === s} onclick={() => (query = s)}>{s}</button>
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
				<PanelMatrix {rows} periods={windowPeriods} dartUrlByPeriod={dartUrls} glow={glowCell} />
			</section>

			<aside class="right">
				<!-- 1) 화면 정량 (viewport facets) -->
				<div class="group">
					<div class="panel-title">화면 정량 <span>{viewport?.facets.length ?? 0} facet</span></div>
					{#if viewport}
						<div class="stats">
							<span>금액 {viewport.amountCells}</span>
							<span>비율 {viewport.percentCells}</span>
							<span>연도 {viewport.yearCells}</span>
						</div>
						{#if viewport.constraint}
							<div class="constraint-head">
								조건 만족 <strong>{viewport.constraintHits.length}</strong>곳
								<small>BM25 비가시 정량조건</small>
							</div>
							{#each viewport.constraintHits.slice(0, 14) as f (`${f.rowIndex}-${f.period}`)}
								<button type="button" class="hit" onclick={() => focusFacet(f)}>
									<div class="hit-head"><span>{won(f.amount)}</span><code>{f.period}</code></div>
									<strong>{f.label || '(라벨 없음)'}</strong>
								</button>
							{:else}
								<div class="empty">조건 만족 셀 없음</div>
							{/each}
						{:else}
							<div class="empty">정량 조건을 입력하면 화면에서 충족 셀을 찾아 표시합니다.</div>
						{/if}
					{:else}
						<div class="empty">섹션을 선택하세요.</div>
					{/if}
				</div>

				<!-- 2) 재무 신호 (정렬 숫자) -->
				<div class="group">
					<div class="panel-title">재무 신호 <span>{financeSigs.length}</span></div>
					<div class="fin-kinds">
						{#each FIN_KINDS as fk}
							<button type="button" class:active={financeKind === fk.k} onclick={() => pickFinanceKind(fk.k)}>{fk.label}</button>
						{/each}
						<button type="button" class="run" onclick={loadFinance} disabled={financeLoading}>
							<Sparkles size={13} /> {financeLoading ? '분석 중' : financeRan ? '재분석' : '분석'}
						</button>
					</div>
					{#if financeScope}<div class="stats"><span>{financeScope === 'CFS' ? '연결' : '개별'}</span><span>정렬 숫자 · 계정라벨</span></div>{/if}
					{#if financeErr}
						<div class="empty">{financeErr}</div>
					{:else if financeLoading}
						<div class="empty">DuckDB 재무 query 중…</div>
					{:else if financeSigs.length}
						{#each financeSigs as s (s.accountId)}
							<div class="hit fin" class:flip={s.kind === 'flip'}>
								<div class="hit-head">
									<span class="badge {s.kind}">{kindBadge(s.kind)}</span>
									{#if s.direction === 'up'}<TrendingUp size={13} />{:else if s.direction === 'down'}<TrendingDown size={13} />{/if}
								</div>
								<strong>{s.label}</strong>
								<div class="fin-detail">
									{#if s.kind === 'flip'}{won(s.prev ?? 0)} → {won(s.latest)} · {s.flipAt} 흑↔적자
									{:else if s.kind === 'streak'}{s.monotoneRun}기간 연속 {s.direction === 'up' ? '증가' : '감소'} · 최근 {won(s.latest)}
									{:else}직전 대비 {pct(s.deltaPct)} · {won(s.prev ?? 0)} → {won(s.latest)}{/if}
								</div>
							</div>
						{/each}
					{:else if !financeRan}
						<div class="empty">"분석"으로 정렬된 재무 숫자의 연속추세·흑적전환·큰변동을 결정론으로 추출합니다.</div>
					{/if}
				</div>

				<!-- 3) 요약 (결정론 한국어 내레이션, model 0) + 선택: WebLLM 다듬기(실험) -->
				<div class="group">
					<div class="panel-title">요약 <span>결정론</span></div>
					<p class="narration">{narration}</p>
					<div class="note">숫자는 결정론 추출이라 절대 틀리지 않습니다.</div>

					{#if webgpuOk}
						<button type="button" class="llm-run" onclick={runLlmNarration} disabled={llmLoading || !narration}>
							<Sparkles size={13} />
							{llmLoading ? `온디바이스 모델 준비 ${Math.round(llmProgress * 100)}%` : 'LLM으로 다듬기 (실험)'}
						</button>
						{#if llmText}
							<p class="narration llm">{llmText}</p>
						{/if}
						{#if llmErr}
							<div class="note err">{llmErr}</div>
						{/if}
						<div class="note">실험: Qwen3-0.6B 온디바이스(~360MB 1회 다운로드, 외부 전송 0). 위 결정론 신호를 문장만 다듬음 · 숫자·사실의 진실 원본은 결정론.</div>
					{:else}
						<div class="note">이 브라우저는 WebGPU 미지원 · 결정론 내레이션만 제공(온디바이스 LLM 다듬기 비활성).</div>
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
	.samples button,
	.view-controls button,
	.fin-kinds button {
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
	.samples button:hover,
	.view-controls button:hover,
	.fin-kinds button:hover,
	.samples button.active,
	.view-controls button.active,
	.fin-kinds button.active {
		border-color: rgba(var(--dl-accent-rgb), 0.55);
		color: var(--dl-accent);
		background: rgba(var(--dl-accent-rgb), 0.09);
	}
	.fin-kinds .run {
		margin-left: auto;
		border-color: rgba(56, 189, 248, 0.45);
		color: #bae6fd;
		background: rgba(14, 165, 233, 0.08);
	}
	.fin-kinds .run:disabled {
		opacity: 0.5;
		cursor: default;
	}
	.samples {
		display: flex;
		gap: 6px;
		overflow-x: auto;
	}
	.workspace {
		flex: 1 1 auto;
		min-height: 0;
		display: grid;
		grid-template-columns: 240px minmax(0, 1fr) 380px;
	}
	.left,
	.right {
		min-height: 0;
		overflow-y: auto;
		background: #050811;
	}
	.left {
		border-right: 1px solid #1e2433;
	}
	.right {
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
		gap: 4px;
	}
	.panel-title {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
		padding: 7px 4px;
		color: #94a3b8;
		font-size: 11px;
		font-weight: 800;
		text-transform: uppercase;
	}
	.panel-title span {
		color: var(--dl-accent);
	}
	.group + .group {
		margin-top: 12px;
		padding-top: 8px;
		border-top: 1px solid #1e2433;
	}
	.stats {
		display: flex;
		gap: 5px;
		flex-wrap: wrap;
		padding: 0 0 7px;
	}
	.stats span {
		padding: 2px 7px;
		border: 1px solid #1e2433;
		border-radius: 999px;
		color: #94a3b8;
		font-size: 10px;
	}
	.constraint-head {
		display: flex;
		align-items: baseline;
		gap: 6px;
		padding: 4px 0 8px;
		color: #cbd5e1;
		font-size: 12px;
	}
	.constraint-head strong {
		color: var(--dl-accent);
		font-size: 14px;
	}
	.constraint-head small {
		margin-left: auto;
		color: #64748b;
		font-size: 10px;
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
	.hit.fin {
		cursor: default;
	}
	.hit.fin.flip {
		border-color: rgba(248, 113, 113, 0.4);
	}
	.hit:hover:not(.fin) {
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
	.hit-head span:not(.badge) {
		color: var(--dl-accent);
		font-weight: 700;
		font-size: 12px;
	}
	.hit strong {
		font-size: 12px;
		color: #e2e8f0;
		line-height: 1.35;
	}
	.badge {
		padding: 1px 6px;
		border-radius: 999px;
		font-size: 10px;
		font-weight: 700;
	}
	.badge.flip {
		background: rgba(248, 113, 113, 0.16);
		color: #fca5a5;
	}
	.badge.streak {
		background: rgba(74, 222, 128, 0.14);
		color: #86efac;
	}
	.badge.mover {
		background: rgba(251, 191, 36, 0.16);
		color: #fcd34d;
	}
	.fin-detail {
		color: #94a3b8;
		font-size: 11px;
		line-height: 1.4;
	}
	.narration {
		margin: 0 0 8px;
		padding: 10px;
		border: 1px solid #1e2433;
		border-radius: 7px;
		background: #0a0e18;
		color: #dbeafe;
		font-size: 12px;
		line-height: 1.6;
	}
	.narration.llm {
		margin-top: 8px;
		border-color: rgba(56, 189, 248, 0.35);
		background: rgba(14, 165, 233, 0.06);
		color: #bae6fd;
	}
	.llm-run {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		height: 28px;
		margin: 2px 0 6px;
		padding: 0 10px;
		border: 1px solid rgba(56, 189, 248, 0.45);
		border-radius: 6px;
		background: rgba(14, 165, 233, 0.08);
		color: #bae6fd;
		font: inherit;
		font-size: 11px;
		cursor: pointer;
	}
	.llm-run:disabled {
		opacity: 0.5;
		cursor: default;
	}
	.note {
		color: #64748b;
		font-size: 10px;
	}
	.note.err {
		color: #f87171;
	}
	.empty {
		padding: 12px;
		text-align: center;
		color: #64748b;
		font-size: 12px;
	}
	.state {
		flex: 1 1 auto;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 12px;
		color: #64748b;
		font-size: 12px;
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
			max-height: 380px;
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
		.hero {
			flex-direction: column;
			align-items: stretch;
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
	}
</style>
