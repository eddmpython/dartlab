<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { Plus, FolderOpen } from 'lucide-svelte';
	// 헤더 = 터미널·카드 공통 SSOT(surfaces). BrandSwitch·BrandSocial·SupportDialog 동일 컨트롤 공유.
	import '@dartlab/ui-surfaces/terminal/terminal.css';
	import {
		DARTLAB_BRAND_LINKS,
		SupportDialog,
		BrandSwitch,
		BrandSocial,
		fetchGithubStars
	} from '@dartlab/ui-surfaces/terminal';
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

	const links = DARTLAB_BRAND_LINKS;
	let ghStars = $state<number | null>(null);
	fetchGithubStars(links.repo).then((n) => (ghStars = n));
	let supportOpen = $state(false);

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

<div class="dlTerm hubPage">
	<!-- 헤더 = 터미널·카드 top bar 정본(.dlTerm + terminal.css 재사용). brand · 목적지 · SNS 동일 컨트롤. 경계 없음. -->
	<header class="nbHeader">
		<div class="topBar">
			<a class="brand" href="{base}/" title="DartLab 홈">
				<picture>
					<source srcset="{base}/avatar.webp" type="image/webp" />
					<img class="brandLogo" src="{base}/avatar.png" alt="DartLab" width="22" height="22" />
				</picture>
				<span class="brandName">DartLab</span>
				<span class="brandSlash">/</span>
				<span class="brandTag">notebook</span>
			</a>
			<div class="topRight">
				<div class="hdrLinks">
					<a class="hdrLink hdrTerm" href="{base}/terminal" title="터미널 · 데이터 워크벤치">터미널</a>
					<a class="hdrLink hdrBlog" href="{base}/blog" title="블로그 · 기업 이야기">블로그</a>
					<a class="hdrLink hdrViewer" href="{base}/cards" title="카드뉴스 · 캐러셀 피드">카드뉴스</a>
				</div>
				<nav class="sns" aria-label="dartlab 채널">
					<BrandSwitch />
					<BrandSocial {links} {ghStars} onSupport={() => (supportOpen = true)} />
				</nav>
			</div>
		</div>
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

<SupportDialog lang="kr" {links} {base} open={supportOpen} onClose={() => (supportOpen = false)} />

<style>
	/* .dlTerm(terminal.css)은 height:100vh·overflow:hidden·display:flex(고정 풀스크린 앱)이라 덮어쓴다.
	   허브는 문서형이라 block 흐름이 맞다. flex column 이면 .hero/.gallery 의 margin:0 auto 가 stretch 를
	   이겨 아이템을 content 폭으로 줄여(그리드 1열) 버린다 -> block 으로 정상 중앙정렬 복원. font-size 도
	   .dlTerm(11.5px) 대신 문서 기본으로. */
	.hubPage {
		min-height: 100vh;
		height: auto;
		overflow: visible;
		display: block;
		background: var(--dl-bg-deep);
		color: var(--dl-ink);
		font-family: var(--dl-font-ui);
		font-size: 16px;
	}
	/* 헤더 내부(topBar·brand·hdrLinks·sns 등)는 terminal.css(.dlTerm 스코프) 정본 그대로. 여기선 sticky 래퍼만. */
	.nbHeader {
		position: sticky;
		top: 0;
		z-index: 20;
		padding: 10px 18px;
		background: color-mix(in srgb, var(--dl-bg-deep) 92%, transparent);
		backdrop-filter: blur(8px);
	}
	/* 터미널 topBar 정본은 하단 amber 보더를 긋는다. 노트북 허브는 그 경계를 원치 않음(카드와 동일 제거). */
	.hubPage :global(.topBar) {
		border-bottom: none;
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
