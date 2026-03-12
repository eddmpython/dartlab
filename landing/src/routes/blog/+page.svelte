<script lang="ts">
	import { base } from '$app/paths';
	import { brand } from '$lib/brand';
	import { ArrowRight, Calendar } from 'lucide-svelte';
	import { getCategoryGroups, getCategoryPath, getLatestPosts, getSeriesGroups, getSeriesPath } from '$lib/blog/posts';

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
	<title>DartLab Blog | DART, EDGAR, 사업보고서, 재무 해석 — DartLab 전자공시 분석</title>
	<meta
		name="description"
		content="DartLab 블로그. DART와 EDGAR 공시 시스템, 사업보고서 읽기, 재무 해석, 데이터 자동화를 깊이 있게 정리한 구조형 아카이브입니다."
	/>
	<link rel="canonical" href="https://eddmpython.github.io/dartlab/blog/" />
	<meta property="og:type" content="website" />
	<meta property="og:title" content="DartLab Blog | DART, EDGAR, 사업보고서, 재무 해석 — DartLab 전자공시 분석" />
	<meta
		property="og:description"
		content="공시 시스템, 사업보고서 읽기, 재무 해석, 데이터 자동화를 카테고리별로 정리한 DartLab 블로그."
	/>
	<meta property="og:url" content="https://eddmpython.github.io/dartlab/blog/" />
	<meta property="og:site_name" content="DartLab" />
	<meta property="og:image" content="https://eddmpython.github.io/dartlab/og-image.png" />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content="DartLab Blog | DART, EDGAR, 사업보고서, 재무 해석 — DartLab 전자공시 분석" />
	<meta name="twitter:description" content="공시 시스템, 사업보고서 읽기, 재무 해석, 데이터 자동화를 카테고리별로 정리한 DartLab 블로그." />
	<meta name="twitter:image" content="https://eddmpython.github.io/dartlab/og-image.png" />
	{@html `<script type="application/ld+json">${jsonLd}</script>`}
</svelte:head>

<div class="blog-hub">
	<section class="blog-hub-hero">
		<div class="blog-hub-kicker">DartLab Blog</div>
		<h1 class="blog-hub-title">공시를 숫자가 아니라 구조와 맥락으로 읽는 아카이브</h1>
		<p class="blog-hub-desc">
			DART와 EDGAR, 사업보고서 읽기, 재무 해석, 데이터 자동화를 카테고리 단위로 정리합니다.
			검색으로 유입돼도 다음 읽을 글이 이어지고, 시리즈로 들어와도 구조를 잃지 않게 설계합니다.
		</p>
		<div class="blog-hub-actions">
			<a href="{base}/docs/getting-started/quickstart" class="blog-action primary">Quickstart</a>
			<a href="{base}/docs/getting-started/installation" class="blog-action">설치 가이드</a>
			<a href="{base}/docs/api/overview" class="blog-action">API Overview</a>
			<a href="{brand.repo}" target="_blank" rel="noopener" class="blog-action">GitHub</a>
		</div>
	</section>

	<section class="category-grid">
		{#each categoryGroups as category}
			<a href="{base}{getCategoryPath(category.id)}" class="category-card">
				<div class="category-card-head">
					<div>
						<div class="category-card-kicker">{category.folder}</div>
						<h2 class="category-card-title">{category.label}</h2>
					</div>
					<span class="category-count">{category.postCount} posts</span>
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
				<div class="section-kicker">Latest</div>
				<h2 class="section-title">최신 글</h2>
			</div>
			<p class="section-desc">최근 발행 글에서 현재 블로그의 주제 흐름을 바로 볼 수 있습니다.</p>
		</div>

		<div class="latest-list">
			{#each latestPosts as post}
				<a href="{base}/blog/{post.slug}" class="latest-card">
					<div class="latest-card-shell">
						<div class="latest-card-body">
							<div class="latest-card-top">
								<img src="{base}{post.thumbnail}" alt={post.title} class="latest-avatar" width="52" height="52" loading="lazy" />
								<div class="latest-card-copy">
									<div class="latest-meta">
										<span class="latest-badge">{post.categoryLabel}</span>
										{#if post.seriesLabel}
											<span class="latest-series">{post.seriesLabel}</span>
										{/if}
									</div>
									<div class="latest-date">
										<Calendar size={12} />
										{formatDate(post.date)}
										<span class="latest-dot">·</span>
										예상 {post.readingMinutes}분
									</div>
								</div>
							</div>
							<h3 class="latest-title">{post.title}</h3>
							<p class="latest-desc">{post.description}</p>
						</div>
						<img src="{base}{post.previewAsset ?? post.cardPreview}" alt={post.title} class="latest-thumb" width="172" height="172" loading="lazy" />
					</div>
				</a>
			{/each}
		</div>
	</section>

	<section class="featured-series">
		<div class="section-head">
			<div>
				<div class="section-kicker">Series</div>
				<h2 class="section-title">시리즈별로 이어 읽기</h2>
			</div>
			<p class="section-desc">깊게 읽을수록 가치가 커지는 주제는 시리즈 허브로 묶었습니다.</p>
		</div>

		<div class="series-grid">
			{#each featuredSeries as series}
				<a href="{base}{getSeriesPath(series.id)}" class="series-card">
					<div class="series-card-head">
						<h3 class="series-card-title">{series.label}</h3>
						<span class="series-count">{series.postCount} posts</span>
					</div>
					<p class="series-card-desc">{series.description}</p>
					<span class="series-card-cta">
						시리즈 보기 <ArrowRight size={14} />
					</span>
				</a>
			{/each}
		</div>
	</section>

	<section class="product-cta">
		<div class="product-cta-copy">
			<div class="section-kicker">Product</div>
			<h2 class="section-title">DartLab으로 전자공시를 실제 데이터로 연결하기</h2>
			<p class="section-desc">
				블로그는 읽는 법을 설명하고, DartLab은 그 판단을 코드와 데이터로 옮깁니다.
				재무 시계열, 사업보고서 텍스트, 정기보고서 데이터까지 하나의 흐름으로 다룰 수 있습니다.
			</p>
		</div>
		<div class="product-cta-links">
			<a href="{base}/docs/getting-started/quickstart" class="product-link primary">5분 Quickstart</a>
			<a href="{base}/docs/api/overview" class="product-link">API Overview</a>
			<a href="{base}/docs/tutorials/06_disclosure" class="product-link">공시 텍스트 튜토리얼</a>
			<a href="{base}/docs/tutorials/03_timeseries" class="product-link">시계열 튜토리얼</a>
		</div>
	</section>
</div>

<style>
	.blog-hub {
		max-width: 980px;
	}

	.blog-hub-hero {
		padding: 1rem 0 2.2rem;
		border-bottom: 1px solid rgba(30, 36, 51, 0.85);
		margin-bottom: 2.5rem;
	}

	.blog-hub-kicker,
	.section-kicker,
	.category-card-kicker {
		font-size: 0.72rem;
		font-weight: 700;
		color: #ea4647;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		margin-bottom: 0.45rem;
	}

	.blog-hub-title {
		font-size: 2.5rem;
		font-weight: 800;
		line-height: 1.16;
		color: #f8fafc;
		margin-bottom: 0.9rem;
	}

	.blog-hub-desc,
	.section-desc {
		max-width: 760px;
		font-size: 1rem;
		line-height: 1.8;
		color: #94a3b8;
	}

	.blog-hub-actions,
	.product-cta-links {
		display: flex;
		flex-wrap: wrap;
		gap: 0.7rem;
		margin-top: 1rem;
	}

	.blog-action,
	.product-link {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.72rem 1rem;
		border-radius: 999px;
		border: 1px solid rgba(148, 163, 184, 0.16);
		background: rgba(148, 163, 184, 0.06);
		color: #e2e8f0;
		text-decoration: none;
		font-weight: 700;
	}

	.blog-action.primary,
	.product-link.primary {
		background: rgba(234, 70, 71, 0.14);
		border-color: rgba(234, 70, 71, 0.28);
		color: #fda4a4;
	}

	.category-grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 1.2rem;
		margin-bottom: 3rem;
	}

	.category-card {
		display: flex;
		flex-direction: column;
		gap: 0.95rem;
		padding: 1.5rem;
		border-radius: 18px;
		border: 1px solid rgba(30, 36, 51, 0.95);
		background:
			linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0)),
			rgba(15, 18, 25, 0.94);
		text-decoration: none;
		transition: transform 0.15s, border-color 0.15s;
	}

	.category-card:hover {
		transform: translateY(-2px);
		border-color: rgba(234, 70, 71, 0.3);
	}

	.category-card-head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
	}

	.category-card-title,
	.section-title {
		font-size: 1.4rem;
		font-weight: 800;
		color: #f8fafc;
	}

	.category-count {
		font-size: 0.75rem;
		font-weight: 700;
		padding: 0.35rem 0.6rem;
		border-radius: 999px;
		background: rgba(148, 163, 184, 0.08);
		border: 1px solid rgba(148, 163, 184, 0.14);
		color: #cbd5e1;
	}

	.category-card-desc,
	.latest-desc {
		font-size: 0.92rem;
		line-height: 1.75;
		color: #94a3b8;
	}

	.category-series-list,
	.latest-meta {
		display: flex;
		flex-wrap: wrap;
		gap: 0.45rem;
	}

	.category-series,
	.latest-badge,
	.latest-series {
		display: inline-flex;
		align-items: center;
		padding: 0.28rem 0.55rem;
		border-radius: 999px;
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.03em;
		text-transform: uppercase;
	}

	.category-series,
	.latest-series {
		background: rgba(148, 163, 184, 0.08);
		border: 1px solid rgba(148, 163, 184, 0.14);
		color: #cbd5e1;
	}

	.latest-badge {
		background: rgba(234, 70, 71, 0.12);
		border: 1px solid rgba(234, 70, 71, 0.24);
		color: #fda4a4;
	}

	.category-card-cta {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		color: #ea4647;
		font-size: 0.82rem;
		font-weight: 700;
	}

	.latest-posts {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		margin-bottom: 3rem;
	}

	.section-head {
		display: flex;
		justify-content: space-between;
		align-items: flex-end;
		gap: 1.25rem;
		padding-bottom: 0.85rem;
		border-bottom: 1px solid rgba(30, 36, 51, 0.8);
	}

	.latest-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.latest-card {
		padding: 1.3rem 1.4rem;
		border-radius: 14px;
		border: 1px solid rgba(30, 36, 51, 0.9);
		background: rgba(15, 18, 25, 0.88);
		text-decoration: none;
		transition: border-color 0.15s, transform 0.15s;
	}

	.latest-card:hover {
		border-color: rgba(234, 70, 71, 0.28);
		transform: translateY(-1px);
	}

	.latest-card-shell {
		display: grid;
		grid-template-columns: minmax(0, 1fr) 172px;
		gap: 1rem;
		align-items: stretch;
	}

	.latest-card-body {
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 0.55rem;
		justify-content: center;
	}

	.latest-card-top {
		display: flex;
		align-items: center;
		gap: 0.85rem;
	}

	.latest-avatar {
		width: 52px;
		height: 52px;
		border-radius: 50%;
		border: 1px solid rgba(234, 70, 71, 0.18);
		background: rgba(15, 18, 25, 0.92);
		flex-shrink: 0;
	}

	.latest-card-copy {
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 0.45rem;
	}

	.latest-date {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 0.3rem;
		font-size: 0.75rem;
		color: #64748b;
	}

	.latest-dot {
		color: rgba(100, 116, 139, 0.72);
	}

	.latest-thumb {
		display: block;
		width: 172px;
		height: 172px;
		object-fit: cover;
		object-position: center;
		border-radius: 10px;
		align-self: stretch;
	}

	.latest-title {
		font-size: 1.16rem;
		font-weight: 700;
		color: #f8fafc;
	}

	.featured-series {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		margin-bottom: 3rem;
	}

	.series-grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 1rem;
	}

	.series-card {
		display: flex;
		flex-direction: column;
		gap: 0.8rem;
		padding: 1.35rem 1.4rem;
		border-radius: 16px;
		border: 1px solid rgba(30, 36, 51, 0.9);
		background: rgba(15, 18, 25, 0.9);
		text-decoration: none;
	}

	.series-card:hover {
		border-color: rgba(234, 70, 71, 0.28);
		transform: translateY(-1px);
	}

	.series-card-head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 0.75rem;
	}

	.series-card-title {
		font-size: 1.05rem;
		font-weight: 700;
		color: #f8fafc;
	}

	.series-count {
		font-size: 0.72rem;
		font-weight: 700;
		color: #cbd5e1;
	}

	.series-card-desc {
		font-size: 0.9rem;
		line-height: 1.7;
		color: #94a3b8;
	}

	.series-card-cta {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		color: #ea4647;
		font-size: 0.82rem;
		font-weight: 700;
	}

	.product-cta {
		padding: 1.6rem;
		border-radius: 18px;
		border: 1px solid rgba(234, 70, 71, 0.16);
		background:
			linear-gradient(135deg, rgba(234, 70, 71, 0.08), rgba(251, 146, 60, 0.04)),
			rgba(15, 18, 25, 0.94);
	}

	@media (max-width: 900px) {
		.category-grid {
			grid-template-columns: 1fr;
		}

		.series-grid {
			grid-template-columns: 1fr;
		}

		.section-head {
			flex-direction: column;
			align-items: flex-start;
		}

		.latest-card-shell {
			grid-template-columns: 1fr;
		}

		.latest-thumb {
			width: 100%;
			max-width: 220px;
			height: auto;
			aspect-ratio: 1 / 1;
			justify-self: end;
		}
	}
</style>
