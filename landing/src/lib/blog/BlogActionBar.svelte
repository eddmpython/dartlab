<script lang="ts">
	// 블로그 상단 액션바 · 이 글에서 바로 갈 수 있는 표면(팟캐스트·카드뉴스·터미널)과 공유 버튼.
	// 모두 기존 조인키·헬퍼 재사용(신규 데이터 0): 카드=carousels/index.json(code 조인), 팟캐스트=R2 index.json
	// (stockCode/topicSlug 조인), 터미널=?sym= 딥링크, 공유=navigator.share→클립보드 폴백.
	// 발행된 슬롯만 렌더(없으면 숨김) · 카드/팟캐스트는 라이브 fetch 라 mount 후 채워진다(점진 노출).
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { loadCarousels } from '$lib/cards/contract';
	import { loadPodcastEpisodes, podcastFor } from '$lib/subjects/subjects';
	import { Headphones, Images, Share2, Terminal, Check } from 'lucide-svelte';

	interface Props {
		/** 회사글 조인키(6자리) · 있으면 터미널·카드·팟캐스트 조인. */
		stockCode?: string;
		/** 주제글 조인키(frontmatter topicSlug) · 팟캐스트 주제 조인. */
		topicSlug?: string;
		/** 이 글 절대 URL(공유 대상). */
		shareUrl: string;
		/** 공유 제목. */
		shareTitle: string;
	}
	let { stockCode = '', topicSlug = '', shareUrl, shareTitle }: Props = $props();

	const code = $derived(stockCode.trim());
	const topic = $derived(topicSlug.trim());
	// 터미널은 회사(6자리)만 · 딥링크는 즉시(동기) 노출.
	const terminalHref = $derived(/^\d{6}$/.test(code) ? `${base}/terminal?sym=${code}` : '');

	// 카드/팟캐스트는 라이브 인덱스 조인 → mount 후 채움.
	let cardSlug = $state('');
	let hasPodcast = $state(false);

	onMount(async () => {
		if (code) {
			const all = await loadCarousels();
			// 이 회사의 최신 편집 카드(발간 최신순 정렬된 posts[] 에서 첫 매치). 이슈(standalone)는 제외.
			const hit = all.find((c) => c.code === code && !c.standalone);
			if (hit) cardSlug = hit.slug;
		}
		if (code || topic) {
			const eps = podcastFor(await loadPodcastEpisodes(), code, topic);
			hasPodcast = eps.length > 0;
		}
	});

	const cardHref = $derived(cardSlug ? `${base}/cards?post=${encodeURIComponent(cardSlug)}` : '');

	let copied = $state(false);
	async function share() {
		const nav = typeof navigator !== 'undefined' ? navigator : undefined;
		if (nav?.share) {
			try {
				await nav.share({ title: shareTitle, url: shareUrl });
				return;
			} catch {
				// 사용자 취소·미지원 → 클립보드 폴백.
			}
		}
		try {
			await nav?.clipboard?.writeText(shareUrl);
			copied = true;
			setTimeout(() => (copied = false), 2000);
		} catch {
			// 클립보드 불가(비보안 컨텍스트 등) · 조용히 무시.
		}
	}

	function toPodcast() {
		const el = document.getElementById('related-podcast');
		if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}
</script>

<nav class="action-bar" aria-label="이 글의 관련 표면과 공유">
	{#if hasPodcast}
		<button type="button" class="ab-btn" onclick={toPodcast}>
			<Headphones size={15} />
			<span>팟캐스트</span>
		</button>
	{/if}
	{#if cardHref}
		<a href={cardHref} class="ab-btn">
			<Images size={15} />
			<span>카드뉴스</span>
		</a>
	{/if}
	{#if terminalHref}
		<a href={terminalHref} class="ab-btn">
			<Terminal size={15} />
			<span>터미널</span>
		</a>
	{/if}
	<button type="button" class="ab-btn ab-share" onclick={share} aria-label="이 글 공유">
		{#if copied}
			<Check size={15} /><span>복사됨</span>
		{:else}
			<Share2 size={15} /><span>공유</span>
		{/if}
	</button>
</nav>

<style>
	.action-bar {
		display: flex;
		flex-wrap: wrap;
		justify-content: center;
		gap: 0.5rem;
		margin-top: 1rem;
	}
	.ab-btn {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
		padding: 0.5rem 0.9rem;
		border-radius: 999px;
		border: 1px solid var(--dl-mkt-border, #1e2433);
		background: var(--dl-mkt-card, #0f1219);
		color: var(--dl-ink, #e2e8f0);
		font-size: 0.82rem;
		font-weight: 700;
		letter-spacing: 0.01em;
		text-decoration: none;
		cursor: pointer;
		transition: border-color 0.15s, background 0.15s, transform 0.15s, color 0.15s;
	}
	.ab-btn:hover {
		border-color: rgba(234, 70, 71, 0.32);
		background: rgba(234, 70, 71, 0.08);
		color: #fda4a4;
		transform: translateY(-1px);
	}
	.ab-share {
		border-color: rgba(234, 70, 71, 0.24);
		color: #fda4a4;
	}
</style>
