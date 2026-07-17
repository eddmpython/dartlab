<script lang="ts">
	// 노트북 옆에 두는 dartlab 이야기 목록. 배우면서 실습하는 자리라 이 카테고리만 보여 준다.
	// 글이 SSOT 이고 여기선 posts.ts 색인을 읽기만 한다(사본·별도 색인 없음).
	import { base } from '$app/paths';
	import { Search, ExternalLink } from 'lucide-svelte';
	import { blogAssetUrl, getPostsByCategory } from '$lib/blog/posts';

	const stories = getPostsByCategory('dartlab-stories');

	let query = $state('');
	const filtered = $derived.by(() => {
		const q = query.trim().toLowerCase();
		if (!q) return stories;
		return stories.filter(
			(p) => p.title.toLowerCase().includes(q) || p.description.toLowerCase().includes(q)
		);
	});
</script>

<div class="sp">
	<div class="sp-search">
		<Search size={13} />
		<input bind:value={query} placeholder="글 검색" spellcheck="false" />
	</div>

	{#if stories.length === 0}
		<p class="sp-empty">아직 발행된 글이 없습니다.</p>
	{:else if filtered.length === 0}
		<p class="sp-empty">검색 결과가 없습니다.</p>
	{:else}
		<ul class="sp-list">
			{#each filtered as post (post.slug)}
				<li>
					<a class="sp-item" href="{base}/blog/{post.slug}" target="_blank" rel="noopener">
						{#if post.cardPreviewWebp || post.cardPreview}
							<img
								class="sp-thumb"
								src={blogAssetUrl(post.cardPreviewWebp ?? post.cardPreview, base)}
								alt=""
								loading="lazy"
							/>
						{/if}
						<span class="sp-text">
							<span class="sp-title">{post.title}</span>
							<span class="sp-meta">{post.readingMinutes}분<ExternalLink size={10} /></span>
						</span>
					</a>
				</li>
			{/each}
		</ul>
	{/if}
</div>

<style>
	.sp {
		display: flex;
		flex-direction: column;
		gap: 8px;
		padding: 0 8px;
	}
	.sp-search {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 5px 8px;
		border: 1px solid var(--nb-border);
		border-radius: 6px;
		background: var(--nb-bg);
		color: var(--nb-text-muted);
	}
	.sp-search input {
		flex: 1;
		min-width: 0;
		border: none;
		outline: none;
		background: transparent;
		color: var(--nb-text);
		font-size: 12px;
		font-family: var(--dl-font-ui);
	}
	.sp-empty {
		margin: 12px 4px;
		font-size: 12px;
		color: var(--nb-text-muted);
	}
	.sp-list {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.sp-item {
		display: flex;
		gap: 8px;
		padding: 6px;
		border-radius: 6px;
		text-decoration: none;
		color: inherit;
		transition: background 0.1s ease;
	}
	.sp-item:hover {
		background: var(--nb-card);
	}
	.sp-thumb {
		width: 52px;
		height: 40px;
		flex-shrink: 0;
		object-fit: cover;
		border-radius: 4px;
		background: var(--nb-card);
	}
	.sp-text {
		display: flex;
		flex-direction: column;
		gap: 3px;
		min-width: 0;
	}
	.sp-title {
		font-size: 12px;
		line-height: 1.35;
		color: var(--nb-text);
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	.sp-meta {
		display: flex;
		align-items: center;
		gap: 4px;
		font-family: var(--dl-font-mono);
		font-size: 10px;
		color: var(--nb-text-muted);
	}
</style>
