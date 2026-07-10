<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/state';
	import NotebookEditor from '$lib/notebook/NotebookEditor.svelte';
	import type { Notebook } from '$lib/notebook/stores/notebookStore';
	import { getNotebook } from '$lib/notebook/storage/localStore';

	let initial = $state<Notebook | null>(null);
	let status = $state<'loading' | 'ready' | 'notfound'>('loading');
	let loadedId: string | null = null;

	// onMount 는 같은 라우트 안에서 id 만 바뀔 때 재실행되지 않아 "불러오는 중"에서 고착됐다.
	// $effect 는 id 변경을 감지해 다시 로드한다.
	$effect(() => {
		const id = page.params.id;
		if (id === loadedId) return;
		loadedId = id ?? null;
		void load(id);
	});

	async function load(id: string | undefined) {
		if (!id) {
			status = 'notfound';
			return;
		}
		status = 'loading';
		initial = null;
		const found = await getNotebook(id);
		if (found) {
			initial = found;
			status = 'ready';
			return;
		}
		status = 'notfound';
	}
</script>

<svelte:head>
	<title>{initial?.title ?? 'Notebook'} · dartlab</title>
</svelte:head>

{#if status === 'ready' && initial}
	{#key initial.id}
		<NotebookEditor homeHref="{base}/notebooks" initialNotebook={initial} />
	{/key}
{:else}
	<div class="nb-fallback">
		{#if status === 'loading'}
			<div class="spin">⟳</div>
			<p>불러오는 중...</p>
		{:else}
			<p class="nf-title">노트북을 찾을 수 없습니다</p>
			<p class="nf-sub">이 브라우저에 저장된 노트북이 아닙니다.</p>
			<a class="nf-link" href="{base}/notebooks">← 노트북 허브로</a>
		{/if}
	</div>
{/if}

<style>
	.nb-fallback {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 10px;
		background: var(--dl-bg-deep);
		color: var(--dl-ink-mute);
		font-family: var(--dl-font-ui);
	}
	.spin {
		font-size: 22px;
		color: var(--dl-accent);
		animation: nbspin 1s linear infinite;
	}
	@keyframes nbspin {
		to {
			transform: rotate(360deg);
		}
	}
	.nf-title {
		font-size: 18px;
		font-weight: 600;
		color: var(--dl-ink);
	}
	.nf-sub {
		font-size: 13px;
	}
	.nf-link {
		margin-top: 8px;
		color: var(--dl-accent);
		text-decoration: none;
		font-size: 14px;
	}
	.nf-link:hover {
		text-decoration: underline;
	}
</style>
