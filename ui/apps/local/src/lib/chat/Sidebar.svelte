<script lang="ts">
	// 챗 사이드바. 브랜드 + 테마토글 + [새 대화] + 검색 + 대화이력(고정·이름변경·삭제) + 전체삭제.
	// 옛 ui/web AppSidebar 의 AskNav 를 runes 로 옮긴 것.
	import { base } from '$app/paths';
	import { theme } from './theme.svelte';
	import type { ChatStore, Conversation } from './chatStore.svelte';

	let { store }: { store: ChatStore } = $props();

	let q = $state('');
	let menuId = $state<string | null>(null);
	let renamingId = $state<string | null>(null);
	let renameDraft = $state('');

	const filtered = $derived.by(() => {
		const needle = q.trim().toLowerCase();
		const list = store.sorted;
		if (!needle) return list;
		return list.filter((c) => {
			const hay = (c.title + ' ' + c.messages.map((m) => m.text).join(' ')).toLowerCase();
			return hay.includes(needle);
		});
	});

	function startRename(c: Conversation): void {
		menuId = null;
		renamingId = c.id;
		renameDraft = c.title;
	}
	function commitRename(): void {
		if (renamingId) store.renameConversation(renamingId, renameDraft);
		renamingId = null;
	}
	function confirmDelete(c: Conversation): void {
		menuId = null;
		if (confirm(`"${c.title || '새 대화'}" 대화를 삭제할까요? 되돌릴 수 없습니다.`)) {
			store.deleteConversation(c.id);
		}
	}
	function confirmClearAll(): void {
		if (confirm(`${store.conversations.length}개 대화를 모두 삭제할까요? 되돌릴 수 없습니다.`)) {
			store.clearAll();
		}
	}
</script>

<svelte:window onclick={() => (menuId = null)} />

<aside class="sidebar">
	<header class="brand">
		<a class="id" href={base || '/'}>
			<img src="{base}/avatar.png" alt="DartLab" width="32" height="32" />
			<span class="txt">
				<strong>DartLab</strong>
				<em>local · 챗</em>
			</span>
		</a>
		<button class="icon" onclick={() => theme.toggle()} aria-label="테마 전환" title="테마 전환">
			{#if theme.value === 'dark'}
				<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>
			{:else}
				<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" /></svg>
			{/if}
		</button>
	</header>

	<button class="new" onclick={() => store.newConversation()}>
		<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14" /></svg>
		<span>새 대화</span>
	</button>

	<div class="search">
		<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4-4" /></svg>
		<input bind:value={q} placeholder="대화 검색…" aria-label="대화 검색" />
	</div>

	<nav class="list">
		{#if filtered.length === 0}
			<p class="empty">{q.trim() ? '검색 결과 없음' : '대화 없음'}</p>
		{:else}
			{#each filtered as c (c.id)}
				<div class="row" class:active={c.id === store.activeId}>
					{#if renamingId === c.id}
						<!-- svelte-ignore a11y_autofocus -->
						<input
							class="rename"
							bind:value={renameDraft}
							autofocus
							onblur={commitRename}
							onkeydown={(e) => {
								if (e.key === 'Enter') commitRename();
								if (e.key === 'Escape') renamingId = null;
							}}
						/>
					{:else}
						<button class="pick" onclick={() => store.switchConversation(c.id)} ondblclick={() => startRename(c)} title={c.title}>
							{#if c.pinnedAt}
								<svg class="pin" viewBox="0 0 24 24" width="13" height="13" fill="currentColor" aria-hidden="true"><path d="M16 3l5 5-4 1-3 3-1 5-2-2-4 4-1-1 4-4-2-2 5-1 3-3z" /></svg>
							{:else}
								<svg class="ico" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15a2 2 0 0 1-2 2H8l-4 4V5a2 2 0 0 1 2-2h13a2 2 0 0 1 2 2z" /></svg>
							{/if}
							<span class="label">{c.title || '새 대화'}</span>
						</button>
						<button
							class="more"
							aria-label="대화 메뉴"
							onclick={(e) => {
								e.stopPropagation();
								menuId = menuId === c.id ? null : c.id;
							}}
						>
							<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true"><circle cx="5" cy="12" r="1.6" /><circle cx="12" cy="12" r="1.6" /><circle cx="19" cy="12" r="1.6" /></svg>
						</button>
						{#if menuId === c.id}
							<!-- svelte-ignore a11y_no_static_element_interactions a11y_click_events_have_key_events -->
							<div class="menu" onclick={(e) => e.stopPropagation()}>
								<button onclick={() => { store.togglePin(c.id); menuId = null; }}>{c.pinnedAt ? '고정 해제' : '고정'}</button>
								<button onclick={() => startRename(c)}>이름 변경</button>
								<button class="danger" onclick={() => confirmDelete(c)}>삭제</button>
							</div>
						{/if}
					{/if}
				</div>
			{/each}
		{/if}
	</nav>

	{#if store.conversations.length > 0}
		<footer class="foot">
			<button class="clear" onclick={confirmClearAll}>
				<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" /></svg>
				<span>대화 전체 삭제</span>
			</button>
		</footer>
	{/if}
</aside>

<style>
	.sidebar {
		display: flex;
		flex-direction: column;
		width: 260px;
		flex-shrink: 0;
		height: 100vh;
		border-right: 1px solid var(--dl-line, #2a2c33);
		background: var(--dl-bg-base, #0f0f10);
		padding: 0.75rem;
		gap: 0.6rem;
	}
	.brand {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	.id {
		display: flex;
		align-items: center;
		gap: 0.55rem;
		flex: 1;
		min-width: 0;
		text-decoration: none;
		color: var(--dl-ink, #e7e7ea);
	}
	.id img {
		border-radius: 8px;
		flex-shrink: 0;
	}
	.txt {
		display: grid;
		min-width: 0;
		line-height: 1.15;
	}
	.txt strong {
		font-size: 0.9rem;
		font-weight: 600;
	}
	.txt em {
		font-style: normal;
		font-size: 0.72rem;
		color: var(--dl-ink-mute, #6b7280);
	}
	.icon {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 1.9rem;
		height: 1.9rem;
		border-radius: 7px;
		border: none;
		background: none;
		color: var(--dl-ink-dim, #9aa0aa);
		cursor: pointer;
	}
	.icon:hover {
		background: var(--dl-bg-raised, #16171a);
		color: var(--dl-ink, #e7e7ea);
	}
	.new {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.55rem 0.7rem;
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 9px;
		background: var(--dl-bg-raised, #16171a);
		color: var(--dl-ink, #e7e7ea);
		font-size: 0.85rem;
		font-weight: 500;
		cursor: pointer;
	}
	.new:hover {
		border-color: var(--dl-accent, #ff5a36);
	}
	.search {
		position: relative;
		display: flex;
		align-items: center;
	}
	.search svg {
		position: absolute;
		left: 0.6rem;
		color: var(--dl-ink-mute, #6b7280);
		pointer-events: none;
	}
	.search input {
		width: 100%;
		padding: 0.45rem 0.6rem 0.45rem 1.8rem;
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 8px;
		background: var(--dl-bg-raised, #16171a);
		color: var(--dl-ink, #e7e7ea);
		font-size: 0.8rem;
		outline: none;
	}
	.search input:focus {
		border-color: var(--dl-accent, #ff5a36);
	}
	.list {
		flex: 1;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		gap: 1px;
		margin: 0 -0.25rem;
		padding: 0 0.25rem;
		scrollbar-width: thin;
	}
	.empty {
		font-size: 0.78rem;
		color: var(--dl-ink-mute, #6b7280);
		padding: 0.5rem;
		margin: 0;
	}
	.row {
		position: relative;
		display: flex;
		align-items: center;
		border-radius: 8px;
	}
	.row:hover {
		background: var(--dl-bg-raised, #16171a);
	}
	.row.active {
		background: var(--dl-bg-raised, #16171a);
	}
	.pick {
		flex: 1;
		min-width: 0;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 0.55rem;
		border: none;
		background: none;
		color: var(--dl-ink-dim, #9aa0aa);
		font-size: 0.82rem;
		text-align: left;
		cursor: pointer;
	}
	.row.active .pick {
		color: var(--dl-ink, #e7e7ea);
	}
	.pick .ico {
		flex-shrink: 0;
		color: var(--dl-ink-mute, #6b7280);
	}
	.pick .pin {
		flex-shrink: 0;
		color: var(--dl-accent, #ff5a36);
	}
	.label {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.more {
		flex-shrink: 0;
		display: none;
		align-items: center;
		justify-content: center;
		width: 1.6rem;
		height: 1.6rem;
		margin-right: 0.25rem;
		border: none;
		border-radius: 6px;
		background: none;
		color: var(--dl-ink-mute, #6b7280);
		cursor: pointer;
	}
	.row:hover .more,
	.row.active .more {
		display: inline-flex;
	}
	.more:hover {
		color: var(--dl-ink, #e7e7ea);
	}
	.menu {
		position: absolute;
		right: 0.25rem;
		top: 100%;
		z-index: 20;
		display: flex;
		flex-direction: column;
		min-width: 8rem;
		padding: 0.25rem;
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 8px;
		background: var(--dl-bg-raised, #16171a);
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
	}
	.menu button {
		text-align: left;
		padding: 0.4rem 0.55rem;
		border: none;
		border-radius: 5px;
		background: none;
		color: var(--dl-ink, #e7e7ea);
		font-size: 0.8rem;
		cursor: pointer;
	}
	.menu button:hover {
		background: var(--dl-bg-base, #0f0f10);
	}
	.menu .danger {
		color: var(--dl-bad, #ff6b6b);
	}
	.rename {
		flex: 1;
		margin: 0.3rem 0.4rem;
		padding: 0.35rem 0.5rem;
		border: 1px solid var(--dl-accent, #ff5a36);
		border-radius: 6px;
		background: var(--dl-bg-base, #0f0f10);
		color: var(--dl-ink, #e7e7ea);
		font-size: 0.8rem;
		outline: none;
	}
	.foot {
		border-top: 1px solid var(--dl-line, #2a2c33);
		padding-top: 0.5rem;
	}
	.clear {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		width: 100%;
		padding: 0.5rem 0.55rem;
		border: none;
		border-radius: 8px;
		background: none;
		color: var(--dl-ink-mute, #6b7280);
		font-size: 0.8rem;
		cursor: pointer;
	}
	.clear:hover {
		background: color-mix(in srgb, var(--dl-bad, #ff6b6b) 12%, transparent);
		color: var(--dl-bad, #ff6b6b);
	}
</style>
