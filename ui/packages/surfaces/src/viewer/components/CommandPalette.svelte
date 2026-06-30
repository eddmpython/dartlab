<script lang="ts">
	// ⌘K 커맨드 팔레트 · 공시뷰어 *화면내검색* 전용 (본문검색 + 섹션점프). 회사전환은 헤더 종목검색 버튼이 담당(분리).
	// 본문검색은 searchIndex(gridBySection BM25) 결과를 그대로 격자로 데려간다(pickSection+pickPeriod+glow).
	// scan 검색 디자인 언어(다크 #050811 · 오렌지 var(--amber)).
	import { onMount } from 'svelte';
	import { Search } from 'lucide-svelte';
	import { search, type SearchIndex, type SearchHit } from '../lib/searchIndex';
	import type { PanelTocResponse } from '../lib/types';

	let {
		index,
		toc,
		indexing = false,
		onResult,
		onSection
	}: {
		index: SearchIndex | null;
		toc: PanelTocResponse | null;
		indexing?: boolean;
		onResult: (hit: SearchHit) => void;
		onSection: (sectionKey: string) => void;
	} = $props();

	let open = $state(false);
	let query = $state('');
	let sel = $state(0);
	let expand = $state(true);
	let inputEl = $state<HTMLInputElement | null>(null);

	type Mode = 'body' | 'section';
	const mode = $derived<Mode>(query.startsWith('>') ? 'section' : 'body');
	const term = $derived(query.replace(/^>/, '').trim());

	// 본문 검색 결과.
	const bodyRes = $derived.by(() => {
		if (mode !== 'body' || !index || term.length < 1) return { hits: [] as SearchHit[], added: [] as string[] };
		return search(index, term, { topK: 12, expand });
	});

	// 섹션 점프 후보 (TOC chapter > section 라벨 부분일치).
	const sectionRes = $derived.by(() => {
		if (mode !== 'section' || !toc) return [] as { key: string; label: string }[];
		const q = term.toLowerCase();
		const out: { key: string; label: string }[] = [];
		for (const ch of toc.chapters) {
			for (const sec of ch.sections) {
				const label = `${ch.chapter} › ${sec.sectionLeaf}`;
				if (!q || label.toLowerCase().includes(q)) out.push({ key: sec.sectionKey, label });
			}
		}
		return out.slice(0, 12);
	});

	const count = $derived(mode === 'body' ? bodyRes.hits.length : sectionRes.length);

	$effect(() => {
		// 결과 집합 바뀌면 선택 리셋.
		void count;
		void query;
		sel = 0;
	});

	function openPalette() {
		open = true;
		query = '';
		sel = 0;
		queueMicrotask(() => inputEl?.focus());
	}
	function close() {
		open = false;
	}

	function pickAt(i: number) {
		if (mode === 'body') {
			const h = bodyRes.hits[i];
			if (h) onResult(h);
		} else {
			const s = sectionRes[i];
			if (s) onSection(s.key);
		}
		close();
	}

	function onKeydown(e: KeyboardEvent) {
		if (!open) return;
		if (e.key === 'ArrowDown') {
			e.preventDefault();
			sel = Math.min(count - 1, sel + 1);
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			sel = Math.max(0, sel - 1);
		} else if (e.key === 'Enter') {
			e.preventDefault();
			if (count) pickAt(sel);
		} else if (e.key === 'Escape') {
			e.preventDefault();
			close();
		}
	}

	onMount(() => {
		// ⌘K 를 capture 단계에서 선점 + stopImmediatePropagation · 뷰어 페이지에선 전역 사이트 팔레트
		// (components/CommandPalette.svelte, svelte:window 버블 리스너)보다 우선. 뷰어 떠나면 언마운트로 전역 복귀.
		const onGlobal = (e: KeyboardEvent) => {
			if ((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K')) {
				e.preventDefault();
				e.stopImmediatePropagation();
				open ? close() : openPalette();
			}
		};
		window.addEventListener('keydown', onGlobal, true);
		return () => window.removeEventListener('keydown', onGlobal, true);
	});

	function hitLabel(h: SearchHit): string {
		return [h.section, h.block].filter(Boolean).join(' › ') || h.chapter;
	}
</script>

<button class="kbd-hint" type="button" onclick={openPalette} title="화면내검색 · 이 공시 본문에서 찾기 (⌘K)">
	<Search size={13} />
	<span>화면내검색</span>
	<kbd>⌘K</kbd>
</button>

{#if open}
	<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
	<div class="backdrop" onclick={close}>
		<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
		<div class="palette" onclick={(e) => e.stopPropagation()}>
			<div class="input-row">
				<Search size={15} class="ic" />
				<input
					bind:this={inputEl}
					bind:value={query}
					class="palette-input"
					type="text"
					placeholder="이 공시 본문에서 찾기  ·  &gt; 섹션 점프"
					onkeydown={onKeydown}
					aria-label="화면내검색"
				/>
				{#if mode === 'body'}
					<button class="exp-toggle" class:on={expand} type="button" onclick={() => (expand = !expand)} title="동의어 확장">동의어</button>
				{/if}
			</div>

			{#if mode === 'body' && bodyRes.added.length}
				<div class="chips">
					{#each bodyRes.added as s (s)}<span class="chip">+{s}</span>{/each}
				</div>
			{/if}

			<div class="results">
				{#if mode === 'body' && !index}
					<div class="hint">{indexing ? '본문 색인 준비 중…' : '본문 색인 없음'}</div>
				{:else if !term}
					<div class="hint">이 공시 본문에서 찾을 말을 입력하세요. <b>&gt;</b> 섹션 점프</div>
				{:else if count === 0}
					<div class="hint">결과 없음</div>
				{:else if mode === 'body'}
					{#each bodyRes.hits as h, i (h.sectionKey + '#' + h.rowIndex + '#' + i)}
						<button class="row" class:sel={i === sel} type="button" onmousedown={() => pickAt(i)} onmouseenter={() => (sel = i)}>
							<div class="row-main">
								<span class="row-label">{hitLabel(h)}</span>
								<span class="row-period">{h.period}</span>
							</div>
							{#if h.snippet}<div class="row-snippet">{h.snippet}</div>{/if}
						</button>
					{/each}
				{:else}
					{#each sectionRes as s, i (s.key)}
						<button class="row" class:sel={i === sel} type="button" onmousedown={() => pickAt(i)} onmouseenter={() => (sel = i)}>
							<span class="row-label">{s.label}</span>
						</button>
					{/each}
				{/if}
			</div>
		</div>
	</div>
{/if}

<style>
	.kbd-hint {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		height: 30px;
		padding: 0 10px;
		border: 1px solid #1e2433;
		border-radius: 5px;
		background: #050811;
		color: #94a3b8;
		font: inherit;
		font-size: 12px;
		cursor: pointer;
	}
	.kbd-hint:hover {
		border-color: var(--amber);
		color: var(--amber);
	}
	.kbd-hint kbd {
		font-family: monospace;
		font-size: 10px;
		color: #64748b;
		border: 1px solid #263145;
		border-radius: 3px;
		padding: 1px 4px;
	}

	.backdrop {
		position: fixed;
		inset: 0;
		z-index: 200;
		background: rgba(2, 4, 10, 0.6);
		backdrop-filter: blur(2px);
		display: flex;
		justify-content: center;
		align-items: flex-start;
		padding-top: 12vh;
	}
	.palette {
		width: min(640px, 92vw);
		max-height: 70vh;
		display: flex;
		flex-direction: column;
		background: #0a0e18;
		border: 1px solid #263145;
		border-radius: 10px;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
		overflow: hidden;
	}
	.input-row {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 12px 14px;
		border-bottom: 1px solid #1e2433;
		color: #64748b;
	}
	.palette-input {
		flex: 1;
		background: transparent;
		border: none;
		outline: none;
		color: #f1f5f9;
		font: inherit;
		font-size: 14px;
	}
	.palette-input::placeholder {
		color: #475569;
	}
	.exp-toggle {
		flex-shrink: 0;
		padding: 3px 8px;
		border: 1px solid #1e2433;
		border-radius: 5px;
		background: transparent;
		color: #64748b;
		font: inherit;
		font-size: 11px;
		cursor: pointer;
	}
	.exp-toggle.on {
		border-color: rgba(var(--amber-rgb), 0.5);
		background: rgba(var(--amber-rgb), 0.12);
		color: var(--amber);
	}
	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 5px;
		padding: 8px 14px;
		border-bottom: 1px solid #1e2433;
	}
	.chip {
		font-size: 11px;
		color: #94a3b8;
		background: rgba(148, 163, 184, 0.1);
		border-radius: 4px;
		padding: 2px 7px;
	}
	.results {
		overflow-y: auto;
		padding: 6px;
	}
	.hint {
		padding: 18px 12px;
		text-align: center;
		font-size: 12px;
		color: #64748b;
	}
	.hint b {
		font-family: monospace;
		color: #94a3b8;
	}
	.row {
		display: block;
		width: 100%;
		text-align: left;
		padding: 8px 10px;
		border: none;
		border-radius: 6px;
		background: transparent;
		color: #cbd5e1;
		font: inherit;
		cursor: pointer;
	}
	.row.sel {
		background: rgba(var(--amber-rgb), 0.12);
	}
	.row-main {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 10px;
	}
	.row-label {
		font-size: 13px;
		color: #f1f5f9;
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.row.sel .row-label {
		color: var(--amber);
	}
	.row-period {
		flex-shrink: 0;
		font-family: monospace;
		font-size: 11px;
		color: #64748b;
	}
	.row-snippet {
		margin-top: 3px;
		font-size: 11px;
		color: #64748b;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
</style>
