<script lang="ts">
	import { base } from '$app/paths';
	import { IndustryAtlas } from '@dartlab/ui-surfaces/map';
	import Card from '$lib/components/ui/Card.svelte';
	import Eyebrow from '$lib/components/ui/Eyebrow.svelte';
	import MonoNumber from '$lib/components/ui/MonoNumber.svelte';
	import Tag from '$lib/components/ui/Tag.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import ToggleGroup from '$lib/components/ui/ToggleGroup.svelte';
	import { fmtKrwFromEok } from '@dartlab/ui-format/krw';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const industries = $derived((data.ecosystem as any)?.industries ?? []);
	const atlasIndustries = $derived(
		((data.atlas as any)?.industries ?? []).map((ind: any) => ({
			...ind,
			color: industries.find((i: any) => i.id === ind.id)?.color ?? '#9ca3af'
		}))
	);
	const totalCompanies = $derived(((data.ecosystem as any)?.nodes ?? []).length);
	const totalLinks = $derived(((data.ecosystem as any)?.links ?? []).length);

	let selectedYear: string = $state('');
	const periods = $derived((data.timeline as any)?.periods ?? []);

	// ── 질문 프리셋 ──
	type Question = { id: string; label: string; tone: 'good' | 'bad' | 'warn' | 'info'; source: 'movers' | 'insights'; key: string };
	const QUESTIONS: Question[] = [
		{ id: 'profitImprove', label: '수익성 개선 중', source: 'movers', key: 'profitImprove', tone: 'good' },
		{ id: 'profitDecline', label: '수익성 악화', source: 'movers', key: 'profitDecline', tone: 'bad' },
		{ id: 'revenueSpike', label: '매출 급증', source: 'movers', key: 'revenueSpike', tone: 'good' },
		{ id: 'revenueDrop', label: '매출 급락', source: 'movers', key: 'revenueDrop', tone: 'bad' },
		{ id: 'debtStress', label: '부채 스트레스', source: 'movers', key: 'debtStress', tone: 'warn' },
		{ id: 'extremeWarning', label: '극단 경고', source: 'movers', key: 'extremeWarning', tone: 'bad' },
		{ id: 'connected', label: '연결성 높은 허브', source: 'insights', key: 'connected', tone: 'info' },
		{ id: 'concentrated', label: '집중 의존', source: 'insights', key: 'concentrated', tone: 'warn' },
		{ id: 'diversified', label: '다각화', source: 'insights', key: 'diversified', tone: 'info' },
		{ id: 'dependent', label: '특정 파트너 의존', source: 'insights', key: 'dependent', tone: 'warn' }
	];

	function entriesOf(q: Question): any[] {
		if (q.source === 'movers') return (data.movers as any)?.categories?.[q.key]?.entries ?? [];
		return (data.insights as any)?.rankings?.[q.key] ?? [];
	}

	let selectedQ: Question | null = $state(null);
	const selectedEntries = $derived(selectedQ ? entriesOf(selectedQ) : []);

	function pickQ(q: Question) {
		selectedQ = selectedQ?.id === q.id ? null : q;
		selectedNode = null;
		searchOpen = false;
	}

	// ── 회사 검색 ──
	let searchOpen = $state(false);
	let searchQ = $state('');
	let searchSel = $state(0);
	const allNodes = $derived((data.ecosystem as any)?.nodes ?? []);
	const searchResults = $derived.by(() => {
		const q = searchQ.trim().toLowerCase();
		if (!q) return [];
		return allNodes
			.filter((n: any) => {
				return (
					n.id?.toLowerCase().includes(q) ||
					n.label?.toLowerCase().includes(q) ||
					n.industryName?.toLowerCase().includes(q)
				);
			})
			.slice(0, 10);
	});
	function onSearchKey(e: KeyboardEvent) {
		if (e.key === 'ArrowDown') { e.preventDefault(); searchSel = Math.min(searchSel + 1, searchResults.length - 1); }
		else if (e.key === 'ArrowUp') { e.preventDefault(); searchSel = Math.max(searchSel - 1, 0); }
		else if (e.key === 'Enter' && searchResults[searchSel]) {
			window.location.href = `${base}/terminal?sym=${searchResults[searchSel].id}`;
		} else if (e.key === 'Escape') {
			searchOpen = false;
			searchQ = '';
		}
	}

	// ── 회사/업종 선택 ──
	let selectedNode: any = $state(null);
	let selectedIndustry: any = $state(null);

	function onAtlasSelect(ind: any) {
		selectedIndustry = ind;
		selectedNode = null;
		selectedQ = null;
	}

	// ── ESC 닫기 + / 로 검색 열기 ──
	function onKey(e: KeyboardEvent) {
		const tag = (e.target as Element)?.tagName;
		if (tag === 'INPUT' || tag === 'TEXTAREA') return;
		if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
			e.preventDefault();
			searchOpen = true;
			return;
		}
		if (e.key === 'Escape') {
			if (searchOpen) { searchOpen = false; searchQ = ''; return; }
			if (selectedQ) { selectedQ = null; return; }
			if (selectedIndustry) { selectedIndustry = null; return; }
			if (selectedNode) { selectedNode = null; return; }
		}
	}
</script>

<svelte:head>
	<title>산업지도 · /lab</title>
	<meta name="robots" content="noindex" />
</svelte:head>

<svelte:window onkeydown={onKey} />

<!-- nav -->
<header class="lab-nav">
	<div class="nav-inner">
		<a href="{base}/lab" class="brand">
			<span class="brand-mark">dartlab</span>
			<span class="brand-slash">/</span>
			<span class="brand-ctx">lab · map</span>
		</a>
		<div class="nav-actions">
			<button class="nav-search-btn" onclick={() => (searchOpen = true)}>
				<span>회사 검색</span>
				<kbd class="dl-kbd">/</kbd>
			</button>
			<Button variant="ghost" size="sm" href="{base}/lab">/lab</Button>
			<Button variant="ghost" size="sm" href="{base}/terminal">005930</Button>
		</div>
	</div>
</header>

<!-- 검색 모달 -->
{#if searchOpen}
	<div class="search-overlay" onclick={() => (searchOpen = false)} role="presentation">
		<div
			class="search-modal"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
			role="dialog"
			aria-modal="true"
			tabindex="-1"
		>
			<div class="search-input-wrap">
				<svg class="search-icon" width="14" height="14" viewBox="0 0 14 14" fill="none">
					<circle cx="6" cy="6" r="4.5" stroke="currentColor" stroke-width="1.5" />
					<path d="M9.5 9.5L13 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
				</svg>
				<input
					type="text"
					placeholder="회사명 · 종목코드 · 업종 검색"
					bind:value={searchQ}
					onkeydown={onSearchKey}
				/>
				<kbd class="dl-kbd">ESC</kbd>
			</div>
			{#if searchResults.length > 0}
				<ul class="search-list">
					{#each searchResults as r, i}
						<li>
							<a
								href="{base}/terminal?sym={r.id}"
								class="search-item"
								class:active={i === searchSel}
								onmouseenter={() => (searchSel = i)}
							>
								<span class="search-code dl-mono">{r.id}</span>
								<span class="search-name">{r.label}</span>
								<span class="search-ind">{r.industryName ?? r.industry ?? ''}</span>
							</a>
						</li>
					{/each}
				</ul>
			{:else if searchQ}
				<div class="search-empty">
					<span class="dl-eyebrow">결과 없음</span>
				</div>
			{:else}
				<div class="search-empty">
					<span class="dl-eyebrow">↑↓ 이동 · Enter 선택 · Esc 닫기</span>
				</div>
			{/if}
		</div>
	</div>
{/if}

<!-- editorial hero -->
<section class="hero">
	<div class="hero-inner">
		<Eyebrow text="한국 산업 지도 · 2026.04" />
		<h1 class="hero-h1">
			<MonoNumber value={totalCompanies.toLocaleString()} size="xl" tone="ink" align="left" />
			<span class="hero-h1-text">개 상장사의 네트워크</span>
		</h1>
		<p class="hero-sub">
			34 개 업종 · 공시 기반 공급망 연결 <span class="hero-mono dl-mono">{totalLinks.toLocaleString()}</span> · 주 1회 갱신.
			질문을 고르면 지도가 답을 보여준다.
		</p>
	</div>
</section>

<!-- 질문 스트립 -->
<div class="qstrip-wrap">
	<div class="qstrip-inner">
		<span class="dl-eyebrow">지금 무엇을 봐야 할까</span>
		<div class="qstrip">
			{#each QUESTIONS as q}
				{@const count = entriesOf(q).length}
				<button
					type="button"
					class="qbtn tone-{q.tone}"
					class:active={selectedQ?.id === q.id}
					disabled={count === 0}
					onclick={() => pickQ(q)}
				>
					<span>{q.label}</span>
					<span class="qcount dl-mono">{count}</span>
				</button>
			{/each}
		</div>
	</div>
</div>

<!-- 메인 캔버스 -->
<main class="map-main">
	<IndustryAtlas
		industries={atlasIndustries}
		flows={(data.atlas as any)?.flows ?? []}
		onSelect={onAtlasSelect}
		timelineYear={selectedYear}
		industryTotalsByYear={(data.timeline as any)?.industryTotals ?? {}}
	/>
</main>

<!-- 하단 타임라인 -->
{#if periods.length > 1}
	<div class="tl-wrap">
		<ToggleGroup
			options={[{ value: '', label: '현재' }, ...periods.map((p: string) => ({ value: p, label: p }))]}
			value={selectedYear}
			onChange={(v) => (selectedYear = v)}
			size="sm"
		/>
	</div>
{/if}

<!-- Inspector: 질문 답 -->
{#if selectedQ}
	<aside class="inspector">
		<Card eyebrow="QUESTION · 답 종목 {selectedEntries.length} 사" accent={selectedQ.tone === 'good' ? 'good' : selectedQ.tone === 'bad' ? 'bad' : selectedQ.tone === 'warn' ? 'warn' : 'info'}>
			<div class="ins-head">
				<h3 class="ins-title">{selectedQ.label}</h3>
				<button class="ins-close" onclick={() => (selectedQ = null)} aria-label="닫기">×</button>
			</div>
			<ol class="ins-list">
				{#each selectedEntries.slice(0, 12) as e, i}
					<li>
						<a href="{base}/terminal?sym={e.stockCode}" class="ins-item">
							<span class="ins-rank dl-mono">{(i + 1).toString().padStart(2, '0')}</span>
							<span class="ins-name">{e.corpName ?? e.stockCode}</span>
							<span class="ins-rev dl-mono">{e.revenue ? fmtKrwFromEok(e.revenue / 1e8) : '·'}</span>
						</a>
					</li>
				{/each}
			</ol>
			{#if selectedEntries.length > 12}
				<p class="dl-eyebrow" style="text-align: center; padding-top: var(--dl-s-3);">+ {selectedEntries.length - 12} 더</p>
			{/if}
		</Card>
	</aside>
{/if}

<!-- Inspector: 업종 선택 -->
{#if selectedIndustry && !selectedQ}
	<aside class="inspector">
		<Card eyebrow="INDUSTRY · 업종 상세" accent="orange">
			<div class="ins-head">
				<h3 class="ins-title">{selectedIndustry.name}</h3>
				<button class="ins-close" onclick={() => (selectedIndustry = null)} aria-label="닫기">×</button>
			</div>
			<div class="ind-stats">
				<div>
					<span class="dl-label">회사 수</span>
					<MonoNumber value={selectedIndustry.nodeCount?.toLocaleString() ?? '·'} size="lg" tone="ink" align="left" />
				</div>
				<div>
					<span class="dl-label">총 매출</span>
					<MonoNumber value={fmtKrwFromEok(selectedIndustry.revenue / 1e8)} size="lg" tone="ink" align="left" />
				</div>
			</div>
			<div class="ind-tags">
				<Tag tone="info">{selectedIndustry.id}</Tag>
				{#if selectedIndustry.stagedCount}<Tag>{selectedIndustry.stagedCount} 단계</Tag>{/if}
			</div>
		</Card>
	</aside>
{/if}

<style>
	.lab-nav {
		position: sticky;
		top: 0;
		z-index: 30;
		border-bottom: 1px solid var(--dl-line);
		background: rgba(15, 15, 16, 0.85);
		backdrop-filter: blur(14px);
	}
	.nav-inner {
		max-width: var(--dl-w-max);
		margin-inline: auto;
		padding: var(--dl-s-3) var(--dl-s-6);
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	.brand { display: inline-flex; align-items: baseline; gap: var(--dl-s-2); text-decoration: none; color: var(--dl-ink); }
	.brand-mark { font-family: var(--dl-font-head); font-weight: 700; font-size: 18px; letter-spacing: -0.02em; }
	.brand-slash { color: var(--dl-ink-faint); font-weight: 300; }
	.brand-ctx { font-family: var(--dl-font-mono); font-size: 11px; text-transform: uppercase; letter-spacing: 0.16em; color: var(--dl-orange); }
	.nav-actions { display: flex; gap: var(--dl-s-2); align-items: center; }
	.nav-search-btn {
		display: inline-flex; align-items: center; gap: var(--dl-s-2);
		padding: 5px 10px 5px 12px;
		background: var(--dl-bg-overlay);
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-md);
		color: var(--dl-ink-mute);
		font-family: var(--dl-font-ui);
		font-size: 12px;
		cursor: pointer;
		transition: all var(--dl-dur-hover) var(--dl-ease);
	}
	.nav-search-btn:hover { border-color: var(--dl-line-strong); color: var(--dl-ink); }

	/* ── search modal ── */
	.search-overlay {
		position: fixed; inset: 0; z-index: 100;
		background: rgba(8, 9, 11, 0.65);
		backdrop-filter: blur(6px);
		display: flex; align-items: flex-start; justify-content: center;
		padding-top: 12vh;
		animation: fade-in 120ms var(--dl-ease);
	}
	.search-modal {
		width: min(560px, calc(100vw - 24px));
		background: var(--dl-bg-modal);
		border: 1px solid var(--dl-line-strong);
		border-radius: var(--dl-r-lg);
		overflow: hidden;
		box-shadow: 0 24px 48px -16px rgba(0, 0, 0, 0.7);
		animation: slip-in 160ms var(--dl-ease);
	}
	.search-input-wrap {
		display: flex; align-items: center; gap: var(--dl-s-3);
		padding: var(--dl-s-4);
		border-bottom: 1px solid var(--dl-line);
	}
	.search-icon { color: var(--dl-ink-dim); flex-shrink: 0; }
	.search-input-wrap input {
		flex: 1;
		background: transparent;
		border: none;
		outline: none;
		color: var(--dl-ink-print);
		font-family: var(--dl-font-ui);
		font-size: 16px;
	}
	.search-input-wrap input::placeholder { color: var(--dl-ink-faint); }

	.search-list { list-style: none; padding: var(--dl-s-2); margin: 0; max-height: 50vh; overflow-y: auto; }
	.search-item {
		display: grid;
		grid-template-columns: 70px 1fr auto;
		gap: var(--dl-s-3);
		align-items: center;
		padding: var(--dl-s-2) var(--dl-s-3);
		border-radius: var(--dl-r-sm);
		text-decoration: none;
		color: var(--dl-ink);
		transition: background var(--dl-dur-hover) var(--dl-ease);
	}
	.search-item.active, .search-item:hover { background: var(--dl-bg-overlay); }
	.search-code { font-size: 11px; color: var(--dl-ink-dim); }
	.search-name { font-size: 14px; color: var(--dl-ink-print); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.search-ind { font-size: 11px; color: var(--dl-ink-mute); }

	.search-empty { padding: var(--dl-s-5); text-align: center; }

	@keyframes fade-in {
		from { opacity: 0; }
		to { opacity: 1; }
	}
	@keyframes slip-in {
		from { opacity: 0; transform: translateY(-8px); }
		to { opacity: 1; transform: translateY(0); }
	}

	.hero { padding: var(--dl-s-6) var(--dl-s-6) var(--dl-s-4); }
	.hero-inner { max-width: var(--dl-w-max); margin-inline: auto; }
	.hero-h1 {
		display: flex;
		align-items: baseline;
		gap: var(--dl-s-3);
		flex-wrap: wrap;
		font-family: var(--dl-font-ui);
		font-size: clamp(28px, 4vw, 44px);
		font-weight: 800;
		letter-spacing: -0.025em;
		line-height: 1.1;
		color: var(--dl-ink-print);
		margin: var(--dl-s-2) 0 var(--dl-s-3);
	}
	.hero-h1-text { font-size: 0.7em; font-weight: 600; color: var(--dl-ink); }
	.hero-sub { font-size: 14px; color: var(--dl-ink-mute); line-height: 1.6; max-width: var(--dl-w-article); margin: 0; }
	.hero-mono { color: var(--dl-orange); font-weight: 600; }

	.qstrip-wrap {
		padding: 0 var(--dl-s-6) var(--dl-s-4);
		border-bottom: 1px solid var(--dl-line);
	}
	.qstrip-inner {
		max-width: var(--dl-w-max);
		margin-inline: auto;
		display: flex;
		flex-direction: column;
		gap: var(--dl-s-2);
	}
	.qstrip { display: flex; gap: var(--dl-s-2); flex-wrap: wrap; }
	.qbtn {
		display: inline-flex;
		align-items: center;
		gap: var(--dl-s-2);
		padding: 6px 12px;
		border-radius: var(--dl-r-pill);
		border: 1px solid var(--dl-line);
		background: var(--dl-bg-raised);
		color: var(--dl-ink-mute);
		font-family: var(--dl-font-ui);
		font-size: 12px;
		font-weight: 500;
		cursor: pointer;
		white-space: nowrap;
		transition: all var(--dl-dur-hover) var(--dl-ease);
	}
	.qbtn:hover:not(:disabled) {
		border-color: var(--dl-line-strong);
		color: var(--dl-ink);
		background: var(--dl-bg-overlay);
	}
	.qbtn:disabled { opacity: 0.35; cursor: not-allowed; }
	.qcount {
		font-size: 10px;
		color: var(--dl-ink-dim);
		padding: 1px 6px;
		border-radius: var(--dl-r-pill);
		background: rgba(255, 255, 255, 0.04);
	}
	.qbtn.active {
		background: var(--dl-bg-modal);
		color: var(--dl-ink-print);
		font-weight: 600;
	}
	.qbtn.active.tone-good { border-color: rgba(52, 211, 153, 0.5); color: var(--dl-good); }
	.qbtn.active.tone-bad { border-color: rgba(239, 68, 68, 0.5); color: var(--dl-bad); }
	.qbtn.active.tone-warn { border-color: rgba(251, 191, 36, 0.5); color: var(--dl-warn); }
	.qbtn.active.tone-info { border-color: rgba(96, 165, 250, 0.5); color: var(--dl-info); }

	.map-main {
		position: relative;
		height: calc(100vh - 320px);
		min-height: 480px;
	}

	.tl-wrap {
		position: fixed;
		left: 50%;
		bottom: var(--dl-s-4);
		transform: translateX(-50%);
		z-index: 20;
		padding: var(--dl-s-2);
		background: rgba(15, 15, 16, 0.9);
		backdrop-filter: blur(14px);
		border-radius: var(--dl-r-pill);
		border: 1px solid var(--dl-line);
	}

	.inspector {
		position: fixed;
		top: 76px;
		right: var(--dl-s-3);
		bottom: 80px;
		width: 360px;
		max-width: calc(100vw - 24px);
		z-index: 25;
		overflow-y: auto;
	}
	.ins-head { display: flex; justify-content: space-between; align-items: flex-start; gap: var(--dl-s-2); margin-bottom: var(--dl-s-3); }
	.ins-title { font-size: 18px; font-weight: 700; letter-spacing: -0.015em; color: var(--dl-ink-print); margin: 0; line-height: 1.2; }
	.ins-close {
		width: 24px; height: 24px; border-radius: var(--dl-r-sm);
		border: 1px solid transparent; background: transparent;
		color: var(--dl-ink-dim); font-size: 18px; line-height: 1;
		cursor: pointer; display: grid; place-items: center;
		transition: all var(--dl-dur-hover) var(--dl-ease);
	}
	.ins-close:hover { background: var(--dl-bg-overlay); color: var(--dl-ink); }

	.ins-list { list-style: none; padding: 0; margin: 0; }
	.ins-item {
		display: grid;
		grid-template-columns: 24px 1fr auto;
		gap: var(--dl-s-2);
		align-items: center;
		padding: var(--dl-s-2) var(--dl-s-2);
		border-radius: var(--dl-r-sm);
		text-decoration: none;
		color: var(--dl-ink);
		transition: background var(--dl-dur-hover) var(--dl-ease);
	}
	.ins-item:hover { background: var(--dl-bg-overlay); }
	.ins-rank { font-size: 10px; color: var(--dl-ink-faint); }
	.ins-name { font-size: 13px; color: var(--dl-ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.ins-rev { font-size: 11px; color: var(--dl-ink-mute); }

	.ind-stats {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--dl-s-3);
		padding: var(--dl-s-3) 0;
	}
	.ind-stats > div { display: flex; flex-direction: column; gap: var(--dl-s-1); }
	.ind-tags { display: flex; gap: var(--dl-s-2); flex-wrap: wrap; padding-top: var(--dl-s-3); border-top: 1px solid var(--dl-line); }

	@media (max-width: 720px) {
		.map-main { height: calc(100vh - 380px); min-height: 380px; }
		.inspector { left: 0; right: 0; top: auto; bottom: 0; width: 100%; max-width: 100%; max-height: 60vh; }
	}
</style>
