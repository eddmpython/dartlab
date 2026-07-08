<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import NotebookEditor from '$lib/notebook/NotebookEditor.svelte';
	import type { Notebook } from '$lib/notebook/stores/notebookStore';
	import { getExample } from '$lib/notebook/examples';
	import { getNotebook, putNotebook } from '$lib/notebook/storage/localStore';

	let initial = $state<Notebook | null>(null);
	let status = $state<'loading' | 'ready' | 'notfound'>('loading');
	let loadedId: string | null = null;

	// page.params.id 변경마다 로드. 예제 id 직접 진입은 fork 후 같은 라우트(/notebooks/[id])로
	// redirect 되는데, onMount 는 컴포넌트 재사용 시 재실행 안 돼 "불러오는 중"에서 고착됐다.
	// $effect 는 uuid 로 바뀐 id 를 감지해 재실행 -> getNotebook 분기로 로드된다.
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

		// 1) 예제 id 직접 진입 -> fork-to-local (예제 원본 불변, 새 로컬 노트북 복제)
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
			// goto 가 page.params.id 를 uuid 로 바꿔 위 $effect 가 재실행 -> getNotebook 분기.
			await goto(`${base}/notebooks/${nb.id}`, { replaceState: true });
			return;
		}

		// 2) 로컬 노트북 id -> IndexedDB 로드
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
