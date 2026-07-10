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
	// 레슨 SSOT = lessons/content/**/*.yaml. 레지스트리가 원본을 그대로 읽어 목록·셀을 낸다.
	import {
		TRACKS,
		listLessons,
		lessonsOfTrack,
		getLesson,
		lessonToCells,
		lessonNotebookId,
		isLessonNotebook
	} from '$lib/notebook/lessons/registry';
	import {
		listNotebooks,
		getNotebook,
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
	/** 이미 시작한 레슨(=IndexedDB 에 `lesson:` 노트북이 있는 것). 카드에 '이어하기' 를 띄운다. */
	let startedLessons = $state<Set<string>>(new Set());

	const links = DARTLAB_BRAND_LINKS;
	let ghStars = $state<number | null>(null);
	fetchGithubStars(links.repo).then((n) => (ghStars = n));
	let supportOpen = $state(false);

	async function refresh() {
		const all = await listNotebooks();
		// 레슨 진행분은 '내 노트북' 목록에 섞지 않는다. 카드의 '이어하기' 배지로만 드러난다.
		mine = all.filter((nb) => !isLessonNotebook(nb.id));
		startedLessons = new Set(
			all.filter((nb) => isLessonNotebook(nb.id)).map((nb) => nb.id.slice('lesson:'.length))
		);
	}

	onMount(async () => {
		await refresh();
		loading = false;
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

	/**
	 * 레슨 열기. 이미 시작한 레슨이면 그대로 이어하고, 처음이면 원본에서 셀을 투영해 만든다.
	 * 열 때마다 uuid 사본을 만들던 옛 동작은 같은 레슨을 두 번 누르면 사본이 둘 생기고
	 * 진도가 어디에도 남지 않았다.
	 */
	async function openLesson(lessonId: string) {
		prewarmEngine(); // 커널+dartlab 사전 로딩 시작(대기 안 함)
		const nbId = lessonNotebookId(lessonId);
		const existing = await getNotebook(nbId);
		if (!existing) {
			const lesson = getLesson(lessonId);
			if (!lesson) return;
			const now = nowIso();
			const nb: Notebook = {
				id: nbId,
				title: lesson.meta.title,
				description: lesson.meta.description,
				cells: lessonToCells(lesson).map((cell) => ({
					id: cell.id,
					type: cell.type,
					content: cell.content
				})),
				metadata: { createdAt: now, updatedAt: now }
			};
			await putNotebook(nb);
		}
		await goto(`${base}/notebooks/${nbId}`);
	}

	/** 레슨을 순정 상태로. 저장분을 지우면 다음 열기에서 원본이 다시 투영된다. */
	async function resetLesson(lessonId: string) {
		await deleteNotebook(lessonNotebookId(lessonId));
		await refresh();
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
				<p class="hero-kicker">브라우저에서 바로 실행하는 파이썬 노트북</p>
			</div>
		</div>
		<p class="hero-sub">
			설치 없이 브라우저에서 바로 돕니다. 재무제표 · 계정 · 22축 분석 · 신용등급 · 서사 · 전종목 스캔까지
			여기서 됩니다. 실시간 시세와 뉴스 수집만 <code>pip install dartlab</code> 로 로컬에서 쓰세요.
			레슨과 노트북은 이 브라우저에 저장되고, 하던 곳에서 이어집니다.
		</p>
		<div class="hero-actions">
			<button class="btn-primary" onclick={newNotebook} onpointerenter={prewarmEngine}><Plus size={16} /> 새 노트북</button>
			<button class="btn-ghost" onclick={openFile}><FolderOpen size={15} /> 파일 열기</button>
		</div>
	</section>

	<!-- 커리큘럼. 트랙 순서가 곧 학습 경로다. 레슨 원본은 lessons/content/**/*.yaml 한 편당 한 파일. -->
	{#each TRACKS as track (track.id)}
		{@const lessons = lessonsOfTrack(track.id)}
		{#if lessons.length}
			<section class="gallery">
				<div class="track-head">
					<h2 class="sec-title">{track.title}</h2>
					<p class="track-blurb">{track.blurb}</p>
				</div>
				<div class="grid">
					{#each lessons as lesson (lesson.id)}
						<NotebookCard
							kind="example"
							title={lesson.title}
							subtitle={lesson.description}
							metaLeft={`${lesson.level} · ${lesson.tags.join(' · ')}`}
							metaRight={lesson.minutes ? `${lesson.minutes}분` : `${lesson.sectionCount} 단계`}
							badge={startedLessons.has(lesson.id) ? '이어하기' : ''}
							deletePrompt="처음부터 다시 시작할까요?"
							deleteLabel="초기화"
							onopen={() => openLesson(lesson.id)}
							ondelete={startedLessons.has(lesson.id) ? () => resetLesson(lesson.id) : undefined}
						/>
					{/each}
				</div>
			</section>
		{/if}
	{/each}

	<section class="gallery">
		<h2 class="sec-title">내 노트북</h2>
		{#if loading}
			<p class="muted">불러오는 중...</p>
		{:else if mine.length === 0}
			<div class="empty">
				<p class="empty-title">아직 노트북이 없어요</p>
				<p class="empty-sub">새로 만들거나 위 예제로 시작해보세요.</p>
				<button class="btn-primary" onclick={newNotebook} onpointerenter={prewarmEngine}><Plus size={16} /> 새 노트북</button>
			</div>
		{:else}
			<div class="grid">
				{#each mine as nb (nb.id)}
					<NotebookCard
						kind="local"
						title={nb.title}
						subtitle={nb.description}
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
		margin: 0 0 20px;
		font-size: 14px;
		line-height: 1.7;
		color: var(--dl-ink);
	}
	.hero-sub code {
		font-family: var(--dl-font-mono);
		font-size: 12.5px;
		padding: 1px 5px;
		border-radius: 3px;
		background: var(--dl-bg-raised);
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
	/* 트랙 헤더. 제목 옆에 그 트랙이 무엇을 가르치는지 한 줄. */
	.track-head {
		display: flex;
		align-items: baseline;
		gap: 10px;
		flex-wrap: wrap;
		margin: 0 0 14px;
	}
	.track-head .sec-title {
		margin: 0;
	}
	.track-blurb {
		margin: 0;
		font-size: 13px;
		color: var(--dl-ink-mute);
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
	.muted {
		color: var(--dl-ink-mute);
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
