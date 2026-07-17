<script lang="ts">
	import { base } from '$app/paths';
	import { brand } from '$lib/brand';
	import { ArrowRight, Calendar } from 'lucide-svelte';
	import { blogAssetUrl, getCategoryGroups, getCategoryPath, getDistinctSeriesLabel, getLatestPosts, getSeriesGroups, getSeriesPath } from '$lib/blog/posts';
	import CardThumb from '$lib/blog/CardThumb.svelte';

	const categoryGroups = getCategoryGroups();
	const latestPosts = getLatestPosts(6);
	const featuredSeries = getSeriesGroups().slice(0, 4);
	const jsonLd = JSON.stringify({
		'@context': 'https://schema.org',
		'@type': 'CollectionPage',
		name: 'DartLab Blog',
		description: 'DART와 EDGAR, 사업보고서 읽기, 재무 해석, 데이터 자동화를 다루는 DartLab 블로그 허브',
		url: `${brand.url}blog/`,
		isPartOf: brand.url,
		inLanguage: 'ko'
	});

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString('ko-KR', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}
</script>

<svelte:head>
	<title>DartLab Blog | DART, EDGAR, 사업보고서, 재무 해석 · DartLab 전자공시 분석</title>
	<meta
		name="description"
		content="DartLab 블로그. DART와 EDGAR 공시 시스템, 사업보고서 읽기, 재무 해석, 데이터 자동화를 깊이 있게 정리한 구조형 아카이브입니다."
	/>
	<link rel="canonical" href="https://eddmpython.github.io/dartlab/blog/" />
	<meta property="og:type" content="website" />
	<meta property="og:title" content="DartLab Blog | DART, EDGAR, 사업보고서, 재무 해석 · DartLab 전자공시 분석" />
	<meta
		property="og:description"
		content="공시 시스템, 사업보고서 읽기, 재무 해석, 데이터 자동화를 카테고리별로 정리한 DartLab 블로그."
	/>
	<meta property="og:url" content="https://eddmpython.github.io/dartlab/blog/" />
	<meta property="og:site_name" content="DartLab" />
	<meta property="og:image" content="https://eddmpython.github.io/dartlab/og-image.png" />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content="DartLab Blog | DART, EDGAR, 사업보고서, 재무 해석 · DartLab 전자공시 분석" />
	<meta name="twitter:description" content="공시 시스템, 사업보고서 읽기, 재무 해석, 데이터 자동화를 카테고리별로 정리한 DartLab 블로그." />
	<meta name="twitter:image" content="https://eddmpython.github.io/dartlab/og-image.png" />
	{@html `<script type="application/ld+json">${jsonLd}</script>`}
</svelte:head>

<div class="blog-hub">
	<section class="blog-hub-hero">
		<h1 class="blog-hub-title">DART · EDGAR 전자공시를 구조와 맥락으로 읽는 아카이브</h1>
		<p class="blog-hub-desc">
			DART와 EDGAR, 사업보고서 읽기, 재무 해석, 데이터 자동화를 카테고리 단위로 정리합니다.
		</p>
	</section>

	<section class="category-grid">
		{#each categoryGroups as category}
			<a href="{base}{getCategoryPath(category.id)}" class="category-card">
				<div class="category-card-head">
					<div>
						<div class="category-card-kicker">{category.folder}</div>
						<h2 class="category-card-title">{category.label}</h2>
					</div>
					<span class="category-count">{category.postCount}</span>
				</div>
				<p class="category-card-desc">{category.description}</p>
				{#if category.seriesLabels.length > 0}
					<div class="category-series-list">
						{#each category.seriesLabels.slice(0, 3) as seriesLabel}
							<span class="category-series">{seriesLabel}</span>
						{/each}
					</div>
				{/if}
				<span class="category-card-cta">
					카테고리 보기 <ArrowRight size={14} />
				</span>
			</a>
		{/each}
	</section>

	<section class="latest-posts">
		<div class="section-head">
			<div>
				<h2 class="section-title">최신 글</h2>
			</div>
		</div>

		<div class="latest-list">
			{#each latestPosts as post}
				<a href="{base}/blog/{post.slug}" class="latest-card">
					<div class="latest-card-shell">
						<div class="latest-card-body">
							<div class="latest-card-top">
								<div class="latest-card-copy">
									<div class="latest-meta">
										<span class="latest-badge">{post.categoryLabel}</span>
										{#if getDistinctSeriesLabel(post)}
											<span class="latest-series">{getDistinctSeriesLabel(post)}</span>
										{/if}
									</div>
									<div class="latest-date">
										<Calendar size={12} />
										{formatDate(post.date)}
										<span class="latest-dot">·</span>
										{post.readingMinutes}분
									</div>
								</div>
							</div>
							<h3 class="latest-title">{post.title}</h3>
							<p class="latest-desc">{post.description}</p>
						</div>
						<CardThumb
							image={blogAssetUrl(post.cardPreview, base)}
							imageWebp={post.cardPreviewWebp ? blogAssetUrl(post.cardPreviewWebp, base) : undefined}
							keyword={post.cardKeyword}
							kicker={post.categoryLabel}
							alt={post.title}
						/>
					</div>
				</a>
			{/each}
		</div>
	</section>

	<section class="featured-series">
		<div class="section-head">
			<div>
				<h2 class="section-title">시리즈</h2>
			</div>
		</div>

		<div class="series-grid">
			{#each featuredSeries as series}
				<a href="{base}{getSeriesPath(series.id)}" class="series-card">
					<div class="series-card-head">
						<h3 class="series-card-title">{series.label}</h3>
						<span class="series-count">{series.postCount}</span>
					</div>
					<p class="series-card-desc">{series.description}</p>
					<span class="series-card-cta">
						시리즈 보기 <ArrowRight size={14} />
					</span>
				</a>
			{/each}
		</div>
	</section>
</div>

<style>
	.blog-hub {
		max-width: 980px;
	}

	.blog-hub-hero {
		padding: 0.5rem 0 2rem;
		border-bottom: 1px solid var(--dl-mkt-border);
		margin-bottom: 2rem;
	}

	.blog-hub-title {
		font-size: 2rem;
		font-weight: 700;
		line-height: 1.2;
		color: var(--dl-ink-print);
		margin-bottom: 0.6rem;
	}

	.blog-hub-desc {
		max-width: 600px;
		font-size: 0.9375rem;
		line-height: 1.7;
		color: var(--dl-ink-mute);
	}

	.category-card-kicker {
		font-size: 0.6875rem;
		font-weight: 600;
		color: var(--dl-ink-dim);
		letter-spacing: 0.03em;
		font-family: 'JetBrains Mono', monospace;
		margin-bottom: 0.25rem;
	}

	.section-title {
		font-size: 1.25rem;
		font-weight: 700;
		color: var(--dl-ink-print);
	}

	.category-grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 1rem;
		margin-bottom: 2.5rem;
	}

	.category-card {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		padding: 1.25rem;
		border-radius: 12px;
		border: 1px solid var(--dl-mkt-border);
		background: var(--dl-mkt-card);
		text-decoration: none;
		transition: border-color 0.15s;
	}

	.category-card:hover {
		border-color: rgba(234, 70, 71, 0.3);
	}

	.category-card-head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
	}

	.category-card-title {
		font-size: 1.1rem;
		font-weight: 700;
		color: var(--dl-ink-print);
	}

	.category-count {
		font-size: 0.75rem;
		font-weight: 600;
		padding: 0.2rem 0.5rem;
		border-radius: 6px;
		background: rgba(148, 163, 184, 0.08);
		border: 1px solid var(--dl-mkt-border);
		color: var(--dl-ink-mute);
		font-family: 'JetBrains Mono', monospace;
	}

	.category-card-desc {
		font-size: 0.875rem;
		line-height: 1.65;
		color: var(--dl-ink-mute);
	}

	.category-series-list,
	.latest-meta {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
	}

	.category-series,
	.latest-badge,
	.latest-series {
		display: inline-flex;
		align-items: center;
		padding: 0.2rem 0.45rem;
		border-radius: 6px;
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.02em;
	}

	.category-series,
	.latest-series {
		background: rgba(148, 163, 184, 0.08);
		border: 1px solid var(--dl-mkt-border);
		color: var(--dl-ink-mute);
	}

	.latest-badge {
		background: rgba(234, 70, 71, 0.1);
		border: 1px solid rgba(234, 70, 71, 0.2);
		color: var(--p-red-400);
	}

	.category-card-cta {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		color: var(--dl-red);
		font-size: 0.8rem;
		font-weight: 600;
	}

	.latest-posts,
	.featured-series {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		margin-bottom: 2.5rem;
	}

	.section-head {
		padding-bottom: 0.6rem;
		border-bottom: 1px solid var(--dl-mkt-border);
	}

	.latest-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.latest-card {
		padding: 1rem 1.25rem;
		border-radius: 12px;
		border: 1px solid var(--dl-mkt-border);
		background: var(--dl-mkt-card);
		text-decoration: none;
		transition: border-color 0.15s;
	}

	.latest-card:hover {
		border-color: rgba(234, 70, 71, 0.25);
	}

	.latest-card-shell {
		display: grid;
		grid-template-columns: minmax(0, 1fr) clamp(240px, 32%, 320px);
		gap: 1.25rem;
		align-items: stretch;
		min-height: 160px; /* 카드 균일 높이 · 우측 썸네일이 비율로 위아래 꽉 차게 */
	}

	.latest-card-body {
		min-width: 0;
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: 0.4rem;
	}

	.latest-card-top {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.latest-card-copy {
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
	}

	.latest-date {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 0.3rem;
		font-size: 0.72rem;
		color: var(--dl-ink-dim);
	}

	.latest-dot {
		color: rgba(100, 116, 139, 0.5);
	}

	.latest-title {
		font-size: 1.05rem;
		font-weight: 700;
		color: var(--dl-ink-print);
		display: -webkit-box;
		-webkit-box-orient: vertical;
		-webkit-line-clamp: 2;
		overflow: hidden;
	}

	.latest-desc {
		font-size: 0.85rem;
		line-height: 1.6;
		color: var(--dl-ink-mute);
		display: -webkit-box;
		-webkit-box-orient: vertical;
		-webkit-line-clamp: 2;
		overflow: hidden;
	}

	.series-grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 0.75rem;
	}

	.series-card {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
		padding: 1.1rem 1.25rem;
		border-radius: 12px;
		border: 1px solid var(--dl-mkt-border);
		background: var(--dl-mkt-card);
		text-decoration: none;
		transition: border-color 0.15s;
	}

	.series-card:hover {
		border-color: rgba(234, 70, 71, 0.25);
	}

	.series-card-head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 0.75rem;
	}

	.series-card-title {
		font-size: 0.95rem;
		font-weight: 700;
		color: var(--dl-ink-print);
	}

	.series-count {
		font-size: 0.72rem;
		font-weight: 600;
		color: var(--dl-ink-mute);
		font-family: 'JetBrains Mono', monospace;
	}

	.series-card-desc {
		font-size: 0.85rem;
		line-height: 1.65;
		color: var(--dl-ink-mute);
	}

	.series-card-cta {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		color: var(--dl-red);
		font-size: 0.8rem;
		font-weight: 600;
	}

	@media (max-width: 900px) {
		.category-grid,
		.series-grid {
			grid-template-columns: 1fr;
		}

		.latest-card-shell {
			grid-template-columns: 1fr;
			min-height: 0;
		}

		.latest-card-shell :global(.card-thumb) {
			aspect-ratio: 1200 / 630;
		}

		.blog-hub-title {
			font-size: 1.6rem;
		}
	}
</style>
