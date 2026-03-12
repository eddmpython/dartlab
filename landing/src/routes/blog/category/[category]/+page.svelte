<script lang="ts">
	import { base } from '$app/paths';
	import { brand } from '$lib/brand';
	import { ArrowRight, Calendar } from 'lucide-svelte';
	import { getCategory, getPostsByCategory, getSeriesGroupsByCategory, getSeriesPath } from '$lib/blog/posts';

	let { data } = $props();

	const category = $derived(getCategory(data.category));
	const posts = $derived(category ? getPostsByCategory(category.id) : []);
	const seriesGroups = $derived(category ? getSeriesGroupsByCategory(category.id) : []);
	const pageTitle = $derived(category ? `${category.seoTitle} — DartLab 전자공시 분석` : 'Blog Category — DartLab 전자공시 분석');
	const pageDesc = $derived(category?.seoDescription ?? 'DartLab 블로그 카테고리');
	const pageUrl = $derived(category ? `${brand.url}blog/category/${category.slug}` : `${brand.url}blog/`);
	const jsonLd = $derived(
		JSON.stringify({
			'@context': 'https://schema.org',
			'@type': 'CollectionPage',
			name: category?.label ?? 'Blog category',
			description: pageDesc,
			url: pageUrl,
			isPartOf: `${brand.url}blog/`,
			inLanguage: 'ko'
		})
	);

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString('ko-KR', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}
</script>

<svelte:head>
	<title>{pageTitle}</title>
	<meta name="description" content={pageDesc} />
	<link rel="canonical" href={pageUrl} />
	<meta property="og:type" content="website" />
	<meta property="og:title" content={pageTitle} />
	<meta property="og:description" content={pageDesc} />
	<meta property="og:url" content={pageUrl} />
	<meta property="og:site_name" content="DartLab" />
	<meta property="og:image" content={`${brand.url}og-image.png`} />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content={pageTitle} />
	<meta name="twitter:description" content={pageDesc} />
	<meta name="twitter:image" content={`${brand.url}og-image.png`} />
	{@html `<script type="application/ld+json">${jsonLd}</script>`}
</svelte:head>

{#if !category}
	<div class="category-not-found">
		<h1>404</h1>
		<p>카테고리를 찾을 수 없습니다.</p>
	</div>
{:else}
	<div class="category-page">
		<section class="category-hero">
			<div class="category-kicker">{category.folder}</div>
			<h1 class="category-title">{category.label}</h1>
			<p class="category-desc">{category.description}</p>
			<p class="category-brand">{category.brandMessage}</p>
		</section>

		<section class="category-series-block">
			<div class="category-series-heading">이 카테고리에서 이어지는 읽기 흐름</div>
			<div class="category-series-links">
				{#each seriesGroups as series}
					<a href="{base}{getSeriesPath(series.id)}" class="category-series-chip">
						{series.label}
						<span class="category-series-count">{series.postCount}</span>
					</a>
				{/each}
			</div>
		</section>

		<section class="category-posts">
			{#each posts as post}
				<a href="{base}/blog/{post.slug}" class="category-post-card">
					<div class="category-post-shell">
						<div class="category-post-body">
							<div class="category-post-top">
								<img src="{base}{post.thumbnail}" alt={post.title} class="category-post-avatar" width="52" height="52" loading="lazy" />
								<div class="category-post-meta">
									{#if post.seriesLabel}
										<span class="category-post-series">{post.seriesLabel}</span>
									{/if}
									<div class="category-post-date">
										<Calendar size={12} />
										{formatDate(post.date)}
										<span class="category-post-dot">·</span>
										예상 {post.readingMinutes}분
									</div>
								</div>
							</div>
							<h2 class="category-post-title">{post.title}</h2>
							<p class="category-post-desc">{post.description}</p>
							<span class="category-post-cta">
								읽기 <ArrowRight size={14} />
							</span>
						</div>
						<img src="{base}{post.cardPreview}" alt={post.title} class="category-post-thumb" width="172" height="172" loading="lazy" />
					</div>
				</a>
			{/each}
		</section>

		<section class="category-footer-brand">
			<div class="category-footer-copy">
				<h2>DartLab에서 이 카테고리를 다루는 이유</h2>
				<p>{category.brandMessage}</p>
			</div>
			<div class="category-footer-actions">
				<a href="{base}/docs/getting-started/quickstart" class="category-footer-link">Quickstart 보기</a>
				<a href="{base}/docs/getting-started/installation" class="category-footer-link muted">설치 가이드</a>
				<a href="{base}/docs/api/overview" class="category-footer-link muted">API Overview</a>
				<a href="{base}/blog/" class="category-footer-link muted">블로그 허브</a>
			</div>
		</section>
	</div>
{/if}

<style>
	.category-page {
		max-width: 980px;
	}

	.category-not-found {
		text-align: center;
		padding: 4rem 2rem;
	}

	.category-hero {
		padding-bottom: 2rem;
		border-bottom: 1px solid rgba(30, 36, 51, 0.85);
		margin-bottom: 2rem;
	}

	.category-kicker {
		font-size: 0.72rem;
		font-weight: 700;
		color: #ea4647;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		margin-bottom: 0.45rem;
	}

	.category-title {
		font-size: 2.35rem;
		font-weight: 800;
		color: #f8fafc;
		margin-bottom: 0.8rem;
	}

	.category-desc,
	.category-brand {
		max-width: 780px;
		font-size: 1rem;
		line-height: 1.8;
		color: #94a3b8;
	}

	.category-brand {
		color: #cbd5e1;
		margin-top: 0.9rem;
	}

	.category-series-block {
		margin-bottom: 2rem;
	}

	.category-series-heading {
		font-size: 0.78rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #64748b;
		margin-bottom: 0.85rem;
	}

	.category-series-links {
		display: flex;
		flex-wrap: wrap;
		gap: 0.55rem;
	}

	.category-series-chip,
	.category-post-series {
		display: inline-flex;
		align-items: center;
		padding: 0.3rem 0.6rem;
		border-radius: 999px;
		background: rgba(148, 163, 184, 0.08);
		border: 1px solid rgba(148, 163, 184, 0.14);
		color: #cbd5e1;
		font-size: 0.68rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		text-decoration: none;
	}

	.category-series-chip {
		gap: 0.35rem;
	}

	.category-series-count {
		color: #64748b;
	}

	.category-posts {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.category-post-card {
		padding: 1.4rem 1.5rem;
		border-radius: 16px;
		border: 1px solid rgba(30, 36, 51, 0.9);
		background: rgba(15, 18, 25, 0.9);
		text-decoration: none;
		transition: border-color 0.15s, transform 0.15s;
	}

	.category-post-card:hover {
		border-color: rgba(234, 70, 71, 0.28);
		transform: translateY(-1px);
	}

	.category-post-shell {
		display: grid;
		grid-template-columns: minmax(0, 1fr) 172px;
		gap: 1rem;
		align-items: stretch;
	}

	.category-post-body {
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 0.45rem;
		justify-content: center;
	}

	.category-post-top {
		display: flex;
		align-items: center;
		gap: 0.85rem;
	}

	.category-post-meta {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 0.45rem;
	}

	.category-post-avatar {
		width: 52px;
		height: 52px;
		border-radius: 50%;
		border: 1px solid rgba(234, 70, 71, 0.18);
		background: rgba(15, 18, 25, 0.92);
		flex-shrink: 0;
	}

	.category-post-date {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 0.3rem;
		font-size: 0.75rem;
		color: #64748b;
	}

	.category-post-dot {
		color: rgba(100, 116, 139, 0.72);
	}

	.category-post-thumb {
		display: block;
		width: 172px;
		height: 172px;
		object-fit: cover;
		object-position: center;
		border-radius: 10px;
		align-self: stretch;
	}

	.category-post-title {
		font-size: 1.2rem;
		font-weight: 700;
		color: #f8fafc;
	}

	.category-post-desc {
		font-size: 0.92rem;
		line-height: 1.75;
		color: #94a3b8;
	}

	.category-post-cta {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		color: #ea4647;
		font-size: 0.82rem;
		font-weight: 700;
	}

	@media (max-width: 900px) {
		.category-post-shell {
			grid-template-columns: 1fr;
		}

		.category-post-thumb {
			width: 100%;
			max-width: 220px;
			height: auto;
			aspect-ratio: 1 / 1;
			justify-self: end;
		}
	}

	.category-footer-brand {
		margin-top: 2.5rem;
		padding-top: 1.5rem;
		border-top: 1px solid rgba(30, 36, 51, 0.8);
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
	}

	.category-footer-actions {
		display: flex;
		flex-wrap: wrap;
		gap: 0.7rem 1rem;
	}

	.category-footer-copy h2 {
		font-size: 1.1rem;
		font-weight: 800;
		color: #f8fafc;
		margin-bottom: 0.4rem;
	}

	.category-footer-copy p {
		color: #94a3b8;
		line-height: 1.75;
	}

	.category-footer-link {
		color: #ea4647;
		text-decoration: none;
		font-weight: 700;
	}

	.category-footer-link.muted {
		color: #94a3b8;
		font-weight: 600;
	}
</style>
