<script lang="ts">
	// 첫 화면 회사 검색. 회사 목록(map/search-index*.json)은 입력창에 처음 들어올 때 받는다.
	// 고르면 터미널로 가고, 그 회사를 다룬 기업이야기 글이 있으면 그 글 링크를 같이 보인다.
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { loadJson, setStaticBase } from '@dartlab/ui-runtime/data/dartlabData';
	import type { IndexRow } from '@dartlab/ui-contracts';
	import { Search, BookOpen } from 'lucide-svelte';

	let { storyIndex = {} }: { storyIndex?: Record<string, string> } = $props();

	type Row = IndexRow & { market: '한국' | '미국' };
	let rows = $state<Row[]>([]);
	let loading = $state(false);
	let query = $state('');
	let open = $state(false);
	let active = $state(0);
	let requested: Promise<void> | null = null;

	function ensureRows() {
		requested ??= (async () => {
			loading = true;
			setStaticBase(base);
			const [kr, us] = await Promise.all([
				loadJson<IndexRow[]>('map/search-index.json', { fetchFn: fetch }).catch(() => null),
				loadJson<IndexRow[]>('map/search-index-us.json', { fetchFn: fetch }).catch(() => null)
			]);
			rows = [
				...(kr ?? []).map((row): Row => ({ ...row, market: '한국' })),
				...(us ?? []).map((row): Row => ({ ...row, market: '미국' }))
			];
			loading = false;
			if (rows.length === 0) requested = null;
		})();
		return requested;
	}

	const hits = $derived.by(() => {
		const q = query.trim().toLowerCase();
		if (!q) return [] as Row[];
		const starts: Row[] = [];
		const contains: Row[] = [];
		for (const row of rows) {
			const name = row.corpName?.toLowerCase() ?? '';
			const code = row.stockCode?.toLowerCase() ?? '';
			if (name.startsWith(q) || code.startsWith(q)) starts.push(row);
			else if (name.includes(q)) contains.push(row);
			if (starts.length >= 8) break;
		}
		return [...starts, ...contains].slice(0, 8);
	});

	$effect(() => {
		if (active >= hits.length) active = 0;
	});

	function terminalHref(code: string) {
		return `${base}/terminal?sym=${encodeURIComponent(code)}`;
	}

	function choose(row: Row | undefined) {
		if (!row) return;
		open = false;
		goto(terminalHref(row.stockCode));
	}

	function onKeydown(event: KeyboardEvent) {
		if (event.key === 'ArrowDown' && hits.length) {
			event.preventDefault();
			active = (active + 1) % hits.length;
		} else if (event.key === 'ArrowUp' && hits.length) {
			event.preventDefault();
			active = (active - 1 + hits.length) % hits.length;
		} else if (event.key === 'Enter') {
			event.preventDefault();
			choose(hits[active]);
		} else if (event.key === 'Escape') {
			open = false;
		}
	}
</script>

<div class="company-search" role="search">
	<label class="search-box">
		<Search size={18} class="search-icon" />
		<input
			type="search"
			placeholder="회사 이름이나 종목코드 (예: 삼성전자, 005930, AAPL)"
			autocomplete="off"
			spellcheck="false"
			aria-label="회사 검색"
			bind:value={query}
			onfocus={() => {
				open = true;
				void ensureRows();
			}}
			oninput={() => (open = true)}
			onblur={() => setTimeout(() => (open = false), 150)}
			onkeydown={onKeydown}
		/>
	</label>

	{#if open && query.trim()}
		<ul class="search-results" role="listbox">
			{#if loading && rows.length === 0}
				<li class="search-empty">회사 목록을 받는 중...</li>
			{:else if hits.length === 0}
				<li class="search-empty">찾는 회사가 없습니다.</li>
			{:else}
				{#each hits as row, i (row.stockCode)}
					<li role="option" aria-selected={i === active} class:active={i === active}>
						<a
							class="result-main"
							href={terminalHref(row.stockCode)}
							onmouseenter={() => (active = i)}
							onclick={(event) => {
								event.preventDefault();
								choose(row);
							}}
						>
							<span class="result-name">{row.corpName}</span>
							<span class="result-code">{row.stockCode}</span>
							<span class="result-market">{row.market}</span>
						</a>
						{#if storyIndex[row.stockCode]}
							<a class="result-story" href="{base}/blog/{storyIndex[row.stockCode]}" title="이 회사 기업이야기 읽기">
								<BookOpen size={13} /> 기업이야기
							</a>
						{/if}
					</li>
				{/each}
			{/if}
		</ul>
	{/if}
</div>

<style>
	.company-search {
		position: relative;
		width: 100%;
		max-width: 40rem;
	}
	.search-box {
		display: flex;
		align-items: center;
		gap: 0.65rem;
		padding: 0.85rem 1.1rem;
		border-radius: 14px;
		border: 1px solid var(--dl-mkt-border);
		background: var(--dl-mkt-card);
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.18);
		cursor: text;
	}
	.search-box:focus-within {
		border-color: var(--dl-red);
	}
	.search-box :global(.search-icon) {
		color: var(--dl-ink-dim);
		flex-shrink: 0;
	}
	.search-box input {
		flex: 1;
		min-width: 0;
		background: transparent;
		border: 0;
		outline: none;
		font-size: 1rem;
		color: var(--dl-ink);
	}
	.search-box input::placeholder {
		color: var(--dl-ink-dim);
	}
	.search-results {
		position: absolute;
		z-index: 30;
		top: calc(100% + 0.4rem);
		left: 0;
		right: 0;
		margin: 0;
		padding: 0.35rem;
		list-style: none;
		border-radius: 12px;
		border: 1px solid var(--dl-mkt-border);
		background: var(--dl-mkt-bg-0);
		box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
	}
	.search-results li {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		border-radius: 8px;
	}
	.search-results li.active {
		background: var(--dl-mkt-card);
	}
	.result-main {
		flex: 1;
		min-width: 0;
		display: flex;
		align-items: baseline;
		gap: 0.6rem;
		padding: 0.55rem 0.7rem;
		color: var(--dl-ink);
		text-decoration: none;
	}
	.result-name {
		font-weight: 700;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.result-code {
		font-family: var(--font-mono, monospace);
		font-size: 0.78rem;
		color: var(--dl-ink-dim);
	}
	.result-market {
		margin-left: auto;
		font-size: 0.75rem;
		color: var(--dl-ink-mute);
		white-space: nowrap;
	}
	.result-story {
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
		flex-shrink: 0;
		margin-right: 0.4rem;
		padding: 0.25rem 0.55rem;
		border-radius: 999px;
		font-size: 0.72rem;
		font-weight: 700;
		color: var(--dl-red);
		border: 1px solid color-mix(in srgb, var(--dl-red) 40%, transparent);
		text-decoration: none;
	}
	.search-empty {
		padding: 0.7rem 0.8rem;
		font-size: 0.85rem;
		color: var(--dl-ink-dim);
	}
</style>
