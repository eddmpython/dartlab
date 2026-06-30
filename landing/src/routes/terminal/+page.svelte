<script lang="ts">
	import type { PageData } from './$types';
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { createEngine, TerminalSurface, type RawData } from '@dartlab/ui-surfaces/terminal';
	import { getPublicRuntime } from '$lib/runtime/publicRuntime';
	import { terminalHosts, terminalLinks } from '$lib/terminal-shell/terminalShell';
	import { loadDartDb } from '$lib/data/duckdb';
	import { loadCarousels } from '$lib/cards/contract';
	import { loadMediaIndex } from '$lib/cards/media';
	import type { MediaIndex, CarouselContract } from '$lib/cards/model';
	import PostModal from '$lib/cards/PostModal.svelte';

	// DuckDB-WASM 프리워밍 · JSON 데이터 로드와 병렬로 미리 인스턴스화 (주가 차트 체감속도↑)
	void loadDartDb();

	// 공개 셸 runtime 주입 · surface 는 포트만 본다 (전역 locator·silent fallback 철거, 4a-2)
	const runtime = getPublicRuntime();

	let { data }: { data: PageData } = $props();
	const eng = $derived(createEngine(data.raw as RawData));
	const ready = $derived(!!data.raw.finance.years.length && Object.keys(data.raw.prices.data).length > 0);

	// 모바일 이관 · 3패널 고밀도 터미널은 좁은 화면에서 구조적으로 못 쓴다. 같은 데이터의 단일컬럼 읽기형 /report
	// 로 이관(데스크톱은 그대로). 클라 폭 판정이라 onMount(하이드레이션 후). replaceState=뒤로가기 루프 방지.
	let mobileRedirect = $state(false);
	onMount(() => {
		if (window.matchMedia('(max-width: 767px)').matches) {
			mobileRedirect = true;
			void goto(`${base}/report`, { replaceState: true });
		}
	});

	// 카드뉴스(편집 캐러셀) · 발간된 글 목록(회사당 N편) + 미디어(hero·표시명). 회사 네비「카드뉴스」노출 판단·다이얼로그 데이터.
	// surface 는 cardsCodes/onOpenCards 콜백만 받고, 포스트 다이얼로그(Deck=landing 의존)는 이 셸이 오버레이로 띄운다.
	let cardsPosts = $state<CarouselContract[]>([]);
	let media = $state<MediaIndex | null>(null);
	let cardsPost = $state<{ code: string; slug: string; corpName: string } | null>(null);
	loadCarousels().then((p) => (cardsPosts = p));
	loadMediaIndex().then((m) => (media = m));
	// 카드 있는 회사 코드 집합(surface 의 「카드뉴스」버튼 노출 판단). 회사당 N편이어도 코드 1개.
	const cardsCodes = $derived(new Set(cardsPosts.map((p) => p.code)));

	function openCards(code: string) {
		// posts 는 발간 최신순(date 내림차순) → 그 회사 최신 글을 연다.
		const latest = cardsPosts.find((p) => p.code === code);
		if (!latest) return;
		const corpName = media?.companies[code]?.displayName ?? eng.nameOf(code) ?? code;
		cardsPost = { code, slug: latest.slug, corpName };
	}
</script>

<svelte:head>
	<title>Terminal · 시세·재무·공시 데이터 워크벤치 | dartlab</title>
	<meta
		name="description"
		content="상장사 주가 차트(보조지표·백테스팅·경제지표 오버레이), 재무제표 전 기간, 정기보고서 팩트, 공시 추적을 한 화면에 모은 DartLab Terminal."
	/>
</svelte:head>

{#if mobileRedirect}
	<div class="loading">모바일 · 보고서 뷰로 이동 중 …</div>
{:else if ready}
	<TerminalSurface {eng} {runtime} hosts={terminalHosts} links={terminalLinks} initial="005930" {cardsCodes} onOpenCards={openCards} />
{:else}
	<div class="loading">HuggingFace · dartlab-data 연결 중 …</div>
{/if}

{#if cardsPost}
	<!-- 카드뉴스 다이얼로그 · 터미널 회사 네비「카드뉴스」클릭 시. /cards 피드와 동일 PostModal(Deck+캡션). -->
	<PostModal rt={runtime} code={cardsPost.code} slug={cardsPost.slug} corpName={cardsPost.corpName} {media} {base} onClose={() => (cardsPost = null)} />
{/if}

<style>
	.loading {
		height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--dl-bg-base);
		color: var(--dl-ink-mute);
		font-family: var(--dl-font-mono);
		font-size: 12px;
	}
</style>
