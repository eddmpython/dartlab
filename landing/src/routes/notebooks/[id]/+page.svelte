<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import NotebookEditor from '$lib/notebook/NotebookEditor.svelte';
	import type { Notebook } from '$lib/notebook/stores/notebookStore';
	import { getExample } from '$lib/notebook/examples';
	import { getNotebook, putNotebook } from '$lib/notebook/storage/localStore';

	let initial = $state<Notebook | null>(null);
	let status = $state<'loading' | 'ready' | 'notfound'>('loading');

	onMount(async () => {
		const id = page.params.id;
		if (!id) {
			status = 'notfound';
			return;
		}

		// 1) 예제 id 로 직접 진입 → fork-to-local (예제 원본 불변, 새 로컬 노트북 복제)
		const ex = getExample(id);
		if (ex) {
			const now = new Date().toISOString();
			const nb: Notebook = {
				id: crypto.randomUUID(),
				title: ex.title,
				cells: ex.cells.map((c) => ({ ...c })),
				metadata: { createdAt: now, updatedAt: now }
			};
			await putNotebook(nb);
			await goto(`${base}/notebooks/${nb.id}`, { replaceState: true });
			return;
		}

		// 2) 로컬 노트북 id → IndexedDB 로드
		const found = await getNotebook(id);
		if (found) {
			initial = found;
			status = 'ready';
			return;
		}
		status = 'notfound';
	});
</script>

<svelte:head>
	<title>{initial?.title ?? 'Notebook'} · dartlab</title>
</svelte:head>

{#if status === 'ready' && initial}
	<NotebookEditor homeHref="{base}/notebooks" initialNotebook={initial} />
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
