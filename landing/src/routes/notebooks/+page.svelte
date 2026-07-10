<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { Plus, FolderOpen } from 'lucide-svelte';
	// 헤더 = 터미널·카드 공통 SSOT(surfaces). BrandMark·BrandSwitch·BrandSocial·SupportDialog 동일 컨트롤 공유.
	import '@dartlab/ui-surfaces/terminal/terminal.css';
	import {
		DARTLAB_BRAND_LINKS,
		SupportDialog,
		BrandMark,
		BrandSwitch,
		BrandSocial,
		fetchGithubStars
	} from '@dartlab/ui-surfaces/terminal';
	// 사전 로딩: 노트북을 만들거나 열려는 낌새에 커널+dartlab 을 미리 올린다(에디터 열릴 때 대기 0).
	import { prewarmEngine } from '$lib/notebook/stores/executionStore';
	import type { Notebook } from '$lib/notebook/stores/notebookStore';
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

	async function refresh() {
		mine = await listNotebooks();
	}

	onMount(async () => {
		await refresh();
		loading = false;
		nowMs = Date.now();
	});

	function nowIso() {
		return new Date().toISOString();
	}

	async function newNotebook() {
		prewarmEngine(); // 커널+dartlab 사전 로딩 시작(대기 안 함)
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
		await refresh();
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
</script>

<svelte:head>
	<title>Notebooks · dartlab</title>
	<meta
		name="description"
		content="설치 없이 브라우저에서 바로 실행하는 파이썬 노트북. dartlab 이 들어 있어 회사 이름만 넣으면 공시와 재무제표를 불러옵니다."
	/>
</svelte:head>

<div class="dlTerm hubPage">
	<!-- 헤더 = 터미널·카드 top bar 정본(.dlTerm + terminal.css 재사용). brand · 목적지 · SNS 동일 컨트롤. 경계 없음. -->
	<header class="nbHeader">
		<div class="topBar">
			<BrandMark tag="notebook" href="{base}/" {base} title="DartLab 홈" />
			<div class="topRight">
				<div class="hdrLinks">
					<a class="hdrLink hdrTerm" href="{base}/terminal" title="터미널 · 데이터 워크벤치">터미널</a>
					<a class="hdrLink hdrBlog" href="{base}/blog" title="블로그 · 기업 이야기">블로그</a>
					<a class="hdrLink hdrViewer" href="{base}/cards" title="카드뉴스 · 캐러셀 피드">카드뉴스</a>
				</div>
				<BrandSocial {links} {ghStars} onSupport={() => (supportOpen = true)}>
					{#snippet leading()}<BrandSwitch />{/snippet}
				</BrandSocial>
			</div>
		</div>
	</header>

	<section class="hero">
		<div class="hero-head">
			<picture>
				<source srcset="{base}/avatar.webp" type="image/webp" />
				<img class="hero-avatar" src="{base}/avatar.png" alt="" width="52" height="52" />
			</picture>
			<div>
				<h1>노트북</h1>
				<p class="hero-kicker">설치 없이 브라우저에서 파이썬을 쓰는 곳</p>
			</div>
		</div>
		<p class="hero-sub">
			노트북은 글과 코드를 한 장에 섞어 두는 문서입니다. 코드 칸에 파이썬을 적고 실행하면 바로 아래에
			결과가 나옵니다. 여기서는 그 파이썬이 <a class="hero-link" href="{base}/blog/pyodide-dartlab-lite">Pyodide</a>
			로 이 브라우저 안에서 돕니다. 설치도 가입도 없습니다.
		</p>
		<p class="hero-sub">
			dartlab 이 이미 들어 있어서, 종목코드 여섯 자리만 넣으면 그 회사의 공시와 재무제표를 바로
			불러옵니다. 데이터는 내려받고 계산은 전부 이 브라우저에서 끝납니다. 코드도 결과도 밖으로
			나가지 않고, 만든 노트북은 이 브라우저에 저장됩니다.
		</p>
		<div class="hero-actions">
			<button class="btn-primary" onclick={newNotebook} onpointerenter={prewarmEngine}><Plus size={16} /> 새 노트북</button>
			<button class="btn-ghost" onclick={openFile}><FolderOpen size={15} /> 파일 열기</button>
		</div>
		<!-- 배우는 곳은 블로그다. 허브는 실습장이고, 커리큘럼은 dartlab 이야기가 맡는다. -->
		<p class="hero-hint">
			처음이라면 <a class="hero-link" href="{base}/blog/category/dartlab-stories">dartlab 이야기</a>
			를 보세요. 글을 읽다가 그 자리에서 코드를 돌려 보고, 그대로 노트북으로 가져올 수 있습니다.
		</p>
	</section>

	{#if !loading && mine.length > 0}
		<section class="gallery">
			<h2 class="sec-title">내 노트북</h2>
			<div class="grid">
				{#each mine as nb (nb.id)}
					<NotebookCard
						title={nb.title}
						subtitle={nb.description}
						metaLeft={`${nb.cellCount} 셀`}
						metaRight={relTime(nb.updatedAt)}
						onopen={() => goto(`${base}/notebooks/${nb.id}`)}
						ondelete={() => removeMine(nb.id)}
					/>
				{/each}
			</div>
		</section>
	{/if}
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
	/* 허브다운 정도의 장식. 아바타 + 제목 한 줄 (히어로 배너 아님). */
	.hero-head {
		display: flex;
		align-items: center;
		gap: 14px;
		margin: 0 0 12px;
	}
	.hero-avatar {
		width: 52px;
		height: 52px;
		border-radius: 50%;
		display: block;
		flex-shrink: 0;
		box-shadow: 0 0 0 1px var(--dl-line-strong);
	}
	.hero h1 {
		margin: 0;
		font-size: 30px;
		font-weight: 700;
		letter-spacing: -0.02em;
		color: var(--dl-ink-print);
	}
	.hero-kicker {
		margin: 2px 0 0;
		font-size: 13px;
		color: var(--dl-ink-mute);
	}
	.hero-sub {
		margin: 0 0 10px;
		font-size: 14px;
		line-height: 1.7;
		color: var(--dl-ink);
	}
	.hero-sub:last-of-type {
		margin-bottom: 20px;
	}
	/* Pyodide 가 무엇인지는 dartlab 소식 글이 정본. 히어로는 한 단어만 걸고 넘긴다. */
	.hero-link {
		color: var(--dl-accent);
		text-decoration: none;
		border-bottom: 1px solid rgba(var(--dl-accent-rgb), 0.4);
	}
	.hero-link:hover {
		border-bottom-color: var(--dl-accent);
	}
	.hero-hint {
		margin: 16px 0 0;
		font-size: 13.5px;
		line-height: 1.7;
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
		color: var(--dl-ink);
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 0.95rem;
	}
</style>
