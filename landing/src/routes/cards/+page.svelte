<script lang="ts">
	// 라이브 카드 캐러셀 라우터 · 전 종목의 인스타식 4:5 캐러셀 피드. 각 카드는 첫 슬라이드(회사 사진+이름)가
	// 바로 보이고 그 자리에서 스와이프, 뷰포트 진입 시 라이브 빌드. 공통배선: 데이터=loadJson·미디어=hfMedia.
	import type { PageData } from './$types';
	import { base } from '$app/paths';
	import { setStaticBase } from '@dartlab/ui-runtime/data/dartlabData';
	import { getPublicRuntime } from '$lib/runtime/publicRuntime';
	import '@dartlab/ui-surfaces/terminal/terminal.css';
	import { DARTLAB_BRAND_LINKS, SupportDialog, BrandSwitch, BrandSocial, fetchGithubStars, fmtStars } from '@dartlab/ui-surfaces/terminal';
	import { loadMediaIndex } from '$lib/cards/media';
	import { loadCarousels, contractToCards } from '$lib/cards/contract';
	import type { MediaIndex, CarouselContract } from '$lib/cards/model';
	import PostModal from '$lib/cards/PostModal.svelte';
	import FeedCard from '$lib/cards/FeedCard.svelte';

	let { data }: { data: PageData } = $props();

	setStaticBase(base);
	const rt = getPublicRuntime();
	const links = DARTLAB_BRAND_LINKS;

	let ghStars = $state<number | null>(null);
	fetchGithubStars(links.repo).then((n) => (ghStars = n));

	let media = $state<MediaIndex | null>(null);
	let posts = $state<CarouselContract[]>([]); // 전 캐러셀 계약(회사당 N편 1:N) = 피드, 단일 fetch
	let loaded = $state(false);
	let query = $state(data.sym || '');
	let visibleCount = $state(12);
	let searchEl = $state<HTMLInputElement | null>(null);
	let sentinel = $state<HTMLDivElement | null>(null);
	let supportOpen = $state(false);
	// 인스타 포스트 모달 · 첫장 클릭 시 좌 캐러셀 + 우 캡션(PostModal 이 계약 로드·렌더). /terminal 카드뉴스와 공유.
	let post = $state<{ code: string; slug: string; corpName: string } | null>(null);

	function openPost(code: string, slug: string, corpName: string) {
		post = { code, slug, corpName };
	}

	loadMediaIndex().then((m) => (media = m));
	loadCarousels().then((p) => {
		// posts 순서 그대로 = 발간 최신순(build 가 date 내림차순 정렬). 재정렬 금지.
		posts = p;
		loaded = true;
		// 터미널 카드 버튼이 sym(코드)으로 들어왔는데 그 회사 글이 없으면 전체 피드로(빈 화면 방지).
		if (data.sym && !posts.some((x) => x.code === data.sym)) query = '';
		// 공유/딥링크 ?post=<슬러그> · 해당 캐러셀 포스트 모달 바로 열기(cardShare 워커가 사람을 여기로 보냄).
		if (data.post) {
			const hit = posts.find((x) => x.slug === data.post);
			if (hit) openPost(hit.code, hit.slug, hit.name || media?.companies[hit.code]?.displayName || hit.code);
		}
	});

	// 피드 = 전 캐러셀 계약(회사당 N편). 이름은 계약(name) 우선, 없으면 hfMedia 매니페스트.
	const feedRows = $derived.by(() => {
		const rows = posts.map((p) => ({
			stockCode: p.code,
			slug: p.slug,
			title: p.title ?? '',
			caption: p.caption ?? '',
			pinnedComment: p.pinnedComment ?? '',
			standalone: !!p.standalone,
			leadCards: contractToCards(p, media), // 계약 lead 슬라이드 미리 투영 · 미리보기 표지 깜빡임 제거
			corpName: p.name || media?.companies[p.code]?.displayName || p.code
		}));
		const q = query.trim().toLowerCase();
		return q
			? rows.filter(
					(r) =>
						r.corpName.toLowerCase().includes(q) ||
						r.stockCode.toLowerCase().includes(q) ||
						r.title.toLowerCase().includes(q)
				)
			: rows;
	});
	const visible = $derived(feedRows.slice(0, visibleCount));

	$effect(() => {
		if (!sentinel) return;
		const io = new IntersectionObserver(
			(e) => {
				if (e[0]?.isIntersecting && visibleCount < feedRows.length) visibleCount += 24;
			},
			{ rootMargin: '800px' }
		);
		io.observe(sentinel);
		return () => io.disconnect();
	});

	$effect(() => {
		query;
		visibleCount = 24;
	});

	function onWinKey(e: KeyboardEvent) {
		if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
			e.preventDefault();
			searchEl?.focus();
		}
		// Esc 로 포스트 닫기는 PostModal 이 자체 처리(svelte:window).
	}
</script>

<svelte:window onkeydown={onWinKey} />
<svelte:head><title>카드 캐러셀 · DartLab</title></svelte:head>

<div class="dlTerm cardsPage">
	<!-- 헤더 = 터미널 top bar 그대로(.dlTerm + terminal.css 재사용). brand · 검색 · SNS 아이콘(터미널 동일 정본). -->
	<header class="cHeader">
		<div class="topBar">
			<a class="brand" href="{base}/" title="DartLab 홈">
				<picture>
					<source srcset="{base}/avatar.webp" type="image/webp" />
					<img class="brandLogo" src="{base}/avatar.png" alt="DartLab" width="22" height="22" />
				</picture>
				<span class="brandName">DartLab</span>
				<span class="brandSlash">/</span>
				<span class="brandTag">cards</span>
			</a>

			<form class="cmdBar" role="search" onsubmit={(e) => e.preventDefault()}>
				<span class="cmdPrompt">‹GO›</span>
				<input class="cmdInput" bind:this={searchEl} bind:value={query} spellcheck={false} placeholder="회사명·종목코드 검색" aria-label="회사 검색" />
				<kbd class="cmdKbd">⌘K</kbd>
			</form>

			<div class="topRight">
				<!-- 터미널 상단 목적지 버튼(hdrLinks)과 동형 · 카드 피드에서 터미널·블로그·공시뷰어로 바로 이동. terminal.css amber 정본 재사용. -->
				<div class="hdrLinks">
					<a class="hdrLink hdrTerm" href="{base}/terminal" title="터미널 · 시세·재무·공시 데이터 워크벤치">터미널</a>
					<a class="hdrLink hdrBlog" href="{base}/blog" title="블로그 · 기업 이야기·공시 읽기·dartlab 소식">블로그</a>
					<a class="hdrLink hdrViewer" href="{base}/viewer" title="공시뷰어 · 공시 원문·재무 읽기 전용 뷰">공시뷰어</a>
				</div>
				<BrandSocial {links} {ghStars} onSupport={() => (supportOpen = true)}>
					{#snippet leading()}<BrandSwitch />{/snippet}
				</BrandSocial>
			</div>
		</div>
	</header>

	<main class="feed" aria-label="기업이야기 카드 캐러셀 피드">
		{#if !loaded}
			<p class="feedEmpty">캐러셀 불러오는 중…</p>
		{:else}
			<div class="grid">
				{#each visible as row (row.slug)}
					<FeedCard {rt} code={row.stockCode} slug={row.slug} corpName={row.corpName} title={row.title} caption={row.caption} pinnedComment={row.pinnedComment} standalone={row.standalone} leadCards={row.leadCards} {base} {media} onOpen={() => openPost(row.stockCode, row.slug, row.corpName)} />
				{/each}
			</div>
			<div bind:this={sentinel} class="sentinel"></div>
			{#if feedRows.length === 0}<p class="feedEmpty">{query ? `"${query}" 검색 결과가 없습니다.` : '게시된 편집 캐러셀이 없습니다.'}</p>{/if}
		{/if}
	</main>

	{#if post}
		<PostModal {rt} code={post.code} slug={post.slug} corpName={post.corpName} {media} {base} onClose={() => (post = null)} />
	{/if}
</div>

<SupportDialog lang="kr" {links} {base} open={supportOpen} onClose={() => (supportOpen = false)} />

<style>
	.cardsPage {
		/* ⚠ .dlTerm(terminal.css)은 height:100vh·overflow:hidden(고정 풀스크린 앱)이라 그대로 두면 페이지가
		   스크롤되지 않는다. /cards 는 일반 문서 스크롤이라 height/overflow 를 여기서 덮어쓴다(specificity 우위). */
		min-height: 100vh;
		height: auto;
		overflow: visible;
		background: #030509;
		color: #f1f5f9;
		display: flex;
		flex-direction: column;
		font-size: 16px;
		font-family: 'Pretendard Variable', 'Pretendard', system-ui, sans-serif;
	}
	/* 헤더 내부(topBar·brand·cmdBar·sns·snsBtn 등)는 terminal.css(.dlTerm 스코프) 정본 그대로. 여기선
	   sticky 래퍼만. */
	.cHeader {
		position: sticky;
		top: 0;
		z-index: 20;
		padding: 10px 18px;
		background: rgba(5, 8, 17, 0.92);
		backdrop-filter: blur(8px);
	}
	/* 터미널 topBar 정본은 하단에 amber 보더(.dlTerm .topBar border-bottom: var(--bdAmber))를 긋는다.
	   /cards 는 그 줄을 원치 않음 → 스코프 우위로 제거(헤더 SNS 마크업은 그대로 재사용). */
	.cardsPage :global(.topBar) {
		border-bottom: none;
	}
	.feed {
		flex: 1;
		padding: 24px 20px 80px;
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
		gap: 24px;
		max-width: 1480px;
		margin: 0 auto;
		align-items: start;
	}
	.sentinel {
		height: 1px;
	}
	/* 인스타 포스트 모달은 PostModal.svelte 로 분리(스타일 동행). /terminal 카드뉴스와 공유. */
	.feedEmpty {
		text-align: center;
		color: #64748b;
		padding: 40px 0;
	}
	/* 폰(≤640) · 1열 피드 거터 축소(인스타 패턴 유지, 양 끝 낭비 제거). 데스크톱 무변경. */
	@media (max-width: 640px) {
		.feed {
			padding: 12px 12px 64px;
		}
		.grid {
			grid-template-columns: 1fr;
			gap: 32px; /* 덱-더보기-다음덱이 붙어 보이던 것 해소 · 카드뉴스 사이 확실한 간격 */
		}
		.cHeader {
			padding: 8px 12px;
		}
	}
</style>
