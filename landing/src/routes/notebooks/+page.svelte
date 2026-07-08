<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { Sun, Moon, Plus, FolderOpen } from 'lucide-svelte';
	import { themePref, toggleTheme } from '$lib/theme';
	import type { Notebook } from '$lib/notebook/stores/notebookStore';
	import { EXAMPLES } from '$lib/notebook/examples';
	import {
		listNotebooks,
		putNotebook,
		deleteNotebook,
		type NotebookSummary
	} from '$lib/notebook/storage/localStore';
	import {
		openFileDialog,
		readFileAsText,
		importJupyterNotebook,
		importMarimoNotebook
	} from '$lib/notebook/utils/notebookFormat';
	import NotebookCard from '$lib/notebook/NotebookCard.svelte';

	let mine = $state<NotebookSummary[]>([]);
	let loading = $state(true);

	onMount(async () => {
		mine = await listNotebooks();
		loading = false;
	});

	function nowIso() {
		return new Date().toISOString();
	}

	async function newNotebook() {
		const now = nowIso();
		const nb: Notebook = {
			id: crypto.randomUUID(),
			title: 'Untitled',
			cells: [{ id: crypto.randomUUID(), type: 'code', content: '' }],
			metadata: { createdAt: now, updatedAt: now }
		};
		await putNotebook(nb);
		await goto(`${base}/notebooks/${nb.id}`);
	}

	async function openExample(exId: string) {
		const ex = EXAMPLES.find((e) => e.id === exId);
		if (!ex) return;
		const now = nowIso();
		const nb: Notebook = {
			id: crypto.randomUUID(),
			title: ex.title,
			cells: ex.cells.map((c) => ({ ...c })),
			metadata: { createdAt: now, updatedAt: now }
		};
		await putNotebook(nb);
		await goto(`${base}/notebooks/${nb.id}`);
	}

	async function openFile() {
		const file = await openFileDialog('.ipynb,.py,.json');
		if (!file) return;
		const text = await readFileAsText(file);
		let nb: Notebook;
		if (file.name.endsWith('.ipynb')) nb = importJupyterNotebook(text, file.name);
		else if (file.name.endsWith('.py')) nb = importMarimoNotebook(text, file.name);
		else nb = { ...(JSON.parse(text) as Notebook), id: crypto.randomUUID() };
		nb.id = nb.id || crypto.randomUUID();
		await putNotebook(nb);
		await goto(`${base}/notebooks/${nb.id}`);
	}

	async function removeMine(id: string) {
		await deleteNotebook(id);
		mine = await listNotebooks();
	}

	function relTime(iso: string): string {
		if (!iso) return '';
		const then = Date.parse(iso);
		if (Number.isNaN(then)) return '';
		const sec = Math.max(0, Math.floor((nowMs - then) / 1000));
		if (sec < 60) return '방금';
		const min = Math.floor(sec / 60);
		if (min < 60) return `${min}분 전`;
		const hr = Math.floor(min / 60);
		if (hr < 24) return `${hr}시간 전`;
		const day = Math.floor(hr / 24);
		if (day < 30) return `${day}일 전`;
		return new Date(then).toLocaleDateString('ko-KR');
	}
	// nowMs 를 mount 시 고정(Date.now 반복 호출 회피, 상대시각 표시용)
	let nowMs = $state(0);
	onMount(() => {
		nowMs = Date.now();
	});
</script>

<svelte:head>
	<title>Notebooks · dartlab</title>
	<meta
		name="description"
		content="브라우저에서 바로 실행하는 범용 파이썬 노트북 허브. 예제로 dartlab 엔진(공시·재무·신용·감사)을 익히거나 새 노트북을 만들어 설치 없이 파이썬을 쓰세요."
	/>
</svelte:head>

<div class="hub">
	<header class="hub-top">
		<a class="brand" href="{base}/" title="dartlab">
			<picture>
				<source srcset="{base}/avatar.webp" type="image/webp" />
				<img src="{base}/avatar.png" alt="dartlab" width="24" height="24" class="brand-avatar" />
			</picture>
			<span class="brand-word">dartlab <span class="brand-sub">notebook</span></span>
		</a>
		<button
			class="theme-btn"
			onclick={toggleTheme}
			title={$themePref === 'light' ? '다크 모드로' : '라이트 모드로'}
			aria-label="테마 전환"
		>
			{#if $themePref === 'light'}<Moon size={16} />{:else}<Sun size={16} />{/if}
		</button>
	</header>

	<section class="hero">
		<h1>노트북</h1>
		<p class="hero-sub">
			브라우저에서 바로 실행하는 범용 파이썬 노트북. 설치 없이 numpy · pandas 를 쓰고, 아래 예제로 dartlab
			엔진(공시 수평화 · 재무 계정 · 신용등급 · 감사 점검)을 셀 단위로 익힙니다. 노트북은 이 브라우저에 로컬
			저장됩니다.
		</p>
		<div class="hero-actions">
			<button class="btn-primary" onclick={newNotebook}><Plus size={16} /> 새 노트북</button>
			<button class="btn-ghost" onclick={openFile}><FolderOpen size={15} /> 파일 열기</button>
		</div>
	</section>

	<section class="gallery">
		<h2 class="sec-title">예제 · 템플릿</h2>
		<div class="grid">
			{#each EXAMPLES as ex (ex.id)}
				<NotebookCard
					kind="example"
					title={ex.title}
					subtitle={ex.description}
					metaLeft={ex.tags.join(' · ')}
					metaRight={`${ex.cells.length} 셀`}
					onopen={() => openExample(ex.id)}
				/>
			{/each}
		</div>
	</section>

	<section class="gallery">
		<h2 class="sec-title">내 노트북</h2>
		{#if loading}
			<p class="muted">불러오는 중...</p>
		{:else if mine.length === 0}
			<div class="empty">
				<p class="empty-title">아직 노트북이 없어요</p>
				<p class="empty-sub">새로 만들거나 위 예제로 시작해보세요.</p>
				<button class="btn-primary" onclick={newNotebook}><Plus size={16} /> 새 노트북</button>
			</div>
		{:else}
			<div class="grid">
				{#each mine as nb (nb.id)}
					<NotebookCard
						kind="local"
						title={nb.title}
						subtitle=""
						metaLeft={`${nb.cellCount} 셀`}
						metaRight={relTime(nb.updatedAt)}
						onopen={() => goto(`${base}/notebooks/${nb.id}`)}
						ondelete={() => removeMine(nb.id)}
					/>
				{/each}
			</div>
		{/if}
	</section>
</div>

<style>
	.hub {
		min-height: 100vh;
		background: var(--dl-bg-deep);
		color: var(--dl-ink);
		font-family: var(--dl-font-ui);
	}
	.hub-top {
		position: sticky;
		top: 0;
		z-index: 20;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 12px 24px;
		background: color-mix(in srgb, var(--dl-bg-deep) 88%, transparent);
		backdrop-filter: blur(8px);
		border-bottom: 1px solid var(--dl-line);
	}
	.brand {
		display: flex;
		align-items: center;
		gap: 8px;
		text-decoration: none;
	}
	.brand-avatar {
		width: 24px;
		height: 24px;
		border-radius: 50%;
	}
	.brand-word {
		font-size: 14px;
		font-weight: 600;
		color: var(--dl-ink);
	}
	.brand-sub {
		color: var(--dl-accent);
	}
	.theme-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 30px;
		height: 30px;
		border: none;
		border-radius: var(--dl-r-md);
		background: transparent;
		color: var(--dl-ink-dim);
		cursor: pointer;
		transition: all 0.15s ease;
	}
	.theme-btn:hover {
		color: var(--dl-ink);
		background: var(--dl-bg-raised);
	}

	.hero {
		max-width: 1100px;
		margin: 0 auto;
		padding: 40px 24px 24px;
	}
	.hero h1 {
		margin: 0 0 10px;
		font-size: 30px;
		font-weight: 700;
		letter-spacing: -0.02em;
		color: var(--dl-ink-print);
	}
	.hero-sub {
		margin: 0 0 20px;
		max-width: 640px;
		font-size: 14px;
		line-height: 1.6;
		color: var(--dl-ink-mute);
	}
	.hero-actions {
		display: flex;
		gap: 10px;
	}
	.btn-primary {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 9px 16px;
		border: none;
		border-radius: var(--dl-r-md);
		background: var(--dl-accent);
		color: #fff;
		font-size: 14px;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.15s ease;
	}
	.btn-primary:hover {
		background: var(--dl-accent-dim);
	}
	.btn-ghost {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 9px 16px;
		border: 1px solid var(--dl-line-strong);
		border-radius: var(--dl-r-md);
		background: transparent;
		color: var(--dl-ink-mute);
		font-size: 14px;
		cursor: pointer;
		transition: all 0.15s ease;
	}
	.btn-ghost:hover {
		border-color: var(--dl-accent);
		color: var(--dl-accent);
	}

	.gallery {
		max-width: 1100px;
		margin: 0 auto;
		padding: 12px 24px 32px;
	}
	.sec-title {
		margin: 0 0 14px;
		font-size: 13px;
		font-weight: 700;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--dl-ink-dim);
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 0.95rem;
	}
	.muted {
		color: var(--dl-ink-dim);
		font-size: 13px;
	}
	.empty {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 6px;
		padding: 28px;
		border: 1px dashed var(--dl-line-strong);
		border-radius: var(--dl-r-md);
		background: var(--dl-bg-raised);
	}
	.empty-title {
		margin: 0;
		font-size: 15px;
		font-weight: 600;
		color: var(--dl-ink);
	}
	.empty-sub {
		margin: 0 0 8px;
		font-size: 13px;
		color: var(--dl-ink-mute);
	}
</style>
