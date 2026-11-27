<script module lang="ts">
	import type { FeedItem } from '$lib/blog/posts';

	// 글을 읽고 뒤로 돌아오면 첫 화면이 새로 그려진다. 받아 둔 글을 여기 남겨 두어야 같은 길이로 다시 그려지고
	// 읽던 위치로 돌아온다(처음 연 화면은 비어 있어 HTML 의 12편과 같다).
	let kept: { pages: number; extra: FeedItem[] } | null = null;
</script>

<script lang="ts">
	// 첫 화면 글 목록. 처음 12편은 HTML 에 있고, 끝에 가까워지면 다음 12편(blog/list/<n>.json)을 받아 붙인다.
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { Calendar, ArrowRight } from 'lucide-svelte';
	import CardThumb from '$lib/blog/CardThumb.svelte';

	let { initial, pages }: { initial: FeedItem[]; pages: number } = $props();

	let extra = $state<FeedItem[]>(kept?.extra ?? []);
	let loadedPages = $state(kept?.pages ?? 1);
	let loading = $state(false);
	let failed = $state(false);
	let sentinel = $state<HTMLDivElement | null>(null);

	const items = $derived([...initial, ...extra]);
	const hasMore = $derived(loadedPages < pages);

	function assetUrl(path: string) {
		return /^https?:\/\//i.test(path) ? path : `${base}${path}`;
	}

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });
	}

	async function loadMore() {
		if (loading || !hasMore) return;
		loading = true;
		failed = false;
		try {
			const next = loadedPages + 1;
			const response = await fetch(`${base}/blog/list/${next}.json`);
			if (!response.ok) throw new Error(String(response.status));
			const body = (await response.json()) as { page: number; items: FeedItem[] };
			const seen = new Set(items.map((item) => item.slug));
			extra = [...extra, ...body.items.filter((item) => !seen.has(item.slug))];
			loadedPages = next;
			kept = { pages: loadedPages, extra: $state.snapshot(extra) as FeedItem[] };
		} catch {
			failed = true;
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		if (!sentinel) return;
		const observer = new IntersectionObserver(
			(entries) => {
				if (entries.some((entry) => entry.isIntersecting) && !failed) void loadMore();
			},
			{ rootMargin: '600px 0px' }
		);
		observer.observe(sentinel);
		return () => observer.disconnect();
	});

	// 받은 쪽이 짧아 끝 표지가 계속 보이면 관찰자가 다시 알리지 않으니, 받은 뒤 한 번 더 본다.
	$effect(() => {
		if (loading || failed || !hasMore || !sentinel) return;
		const rect = sentinel.getBoundingClientRect();
		if (rect.top < window.innerHeight + 600) void loadMore();
	});
</script>

<section class="post-feed" aria-label="최신 글">
	<div class="feed-head">
		<h2 class="feed-heading">최신 글</h2>
		<a class="feed-more" href="{base}/blog">카테고리별로 보기 <ArrowRight size={14} /></a>
	</div>

	<div class="feed-grid">
		{#each items as post (post.slug)}
			<a href="{base}/blog/{post.slug}" class="feed-card">
				<div class="feed-thumb">
					<CardThumb
						image={assetUrl(post.cardPreview)}
						imageWebp={post.cardPreviewWebp ? assetUrl(post.cardPreviewWebp) : undefined}
						keyword={post.cardKeyword}
						kicker={post.corpName ?? post.categoryLabel}
						alt={post.title}
					/>
				</div>
				<div class="feed-body">
					<div class="feed-meta">
						<span class="feed-badge">{post.categoryLabel}</span>
						<span class="feed-date"><Calendar size={12} /> {formatDate(post.date)} · {post.readingMinutes}분</span>
					</div>
					<h3 class="feed-title">{post.title}</h3>
					{#if post.description}<p class="feed-desc">{post.description}</p>{/if}
				</div>
			</a>
		{/each}
	</div>

	<div class="feed-foot" bind:this={sentinel}>
		{#if hasMore}
			<button type="button" class="feed-load" onclick={() => void loadMore()} disabled={loading}>
				{#if loading}글을 더 받는 중...{:else if failed}다시 받기{:else}글 더 보기{/if}
			</button>
		{:else}
			<a class="feed-load" href="{base}/blog">블로그에서 카테고리별로 보기</a>
		{/if}
	</div>
</section>

<style>
	.post-feed {
		max-width: 72rem;
		margin: 0 auto;
		padding: 1.5rem 1.5rem 4rem;
	}
	.feed-head {
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 1rem;
	}
	.feed-heading {
		margin: 0;
		font-size: 1.25rem;
		font-weight: 800;
		color: var(--dl-ink);
	}
	.feed-more {
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--dl-ink-mute);
		text-decoration: none;
		white-space: nowrap;
	}
	.feed-more:hover {
		color: var(--dl-red);
	}
	.feed-grid {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 1.5rem 1.25rem;
	}
	.feed-card {
		display: flex;
		flex-direction: column;
		gap: 0.7rem;
		color: inherit;
		text-decoration: none;
	}
	.feed-thumb {
		aspect-ratio: 1200 / 630;
		transition: transform 0.2s ease;
	}
	.feed-card:hover .feed-thumb {
		transform: translateY(-3px);
	}
	.feed-body {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
	}
	.feed-meta {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.75rem;
		color: var(--dl-ink-dim);
	}
	.feed-badge {
		padding: 0.12rem 0.5rem;
		border-radius: 999px;
		font-weight: 700;
		color: var(--dl-red);
		background: color-mix(in srgb, var(--dl-red) 12%, transparent);
	}
	.feed-date {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
	}
	.feed-title {
		margin: 0;
		font-size: 1rem;
		font-weight: 700;
		line-height: 1.4;
		color: var(--dl-ink);
		display: -webkit-box;
		-webkit-box-orient: vertical;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		overflow: hidden;
	}
	.feed-card:hover .feed-title {
		color: var(--dl-red);
	}
	.feed-desc {
		margin: 0;
		font-size: 0.85rem;
		line-height: 1.55;
		color: var(--dl-ink-mute);
		display: -webkit-box;
		-webkit-box-orient: vertical;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		overflow: hidden;
	}
	.feed-foot {
		display: flex;
		justify-content: center;
		margin-top: 2rem;
	}
	.feed-load {
		padding: 0.6rem 1.4rem;
		border-radius: 999px;
		border: 1px solid var(--dl-mkt-border);
		background: var(--dl-mkt-card);
		color: var(--dl-ink-mute);
		font-size: 0.88rem;
		font-weight: 600;
		text-decoration: none;
		cursor: pointer;
	}
	.feed-load:hover:not(:disabled) {
		color: var(--dl-ink);
		border-color: var(--dl-red);
	}
	.feed-load:disabled {
		cursor: progress;
		opacity: 0.7;
	}
	@media (max-width: 960px) {
		.feed-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}
	@media (max-width: 640px) {
		.post-feed {
			padding: 1rem 1rem 3rem;
		}
		.feed-grid {
			grid-template-columns: minmax(0, 1fr);
		}
	}
</style>
