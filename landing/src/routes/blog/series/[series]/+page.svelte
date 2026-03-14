<script lang="ts">
	import { base } from '$app/paths';
	import { brand } from '$lib/brand';
	import { ArrowRight, Calendar } from 'lucide-svelte';
	import { getSeries, getSeriesPosts } from '$lib/blog/posts';

	let { data } = $props();

	const series = $derived(getSeries(data.series));
	const posts = $derived(series ? getSeriesPosts(series.id) : []);
	const pageTitle = $derived(series ? `${series.seoTitle} — DartLab 전자공시 분석` : 'Blog Series — DartLab 전자공시 분석');
	const pageDesc = $derived(series?.seoDescription ?? 'DartLab 블로그 시리즈');
	const pageUrl = $derived(series ? `${brand.url}blog/series/${series.id}` : `${brand.url}blog/`);
	const jsonLd = $derived(
		JSON.stringify({
			'@context': 'https://schema.org',
			'@type': 'CollectionPage',
			name: series?.label ?? 'Blog series',
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

{#if !series}
	<div class="series-not-found">
		<h1>404</h1>
		<p>시리즈를 찾을 수 없습니다.</p>
	</div>
{:else}
	<div class="series-page">
		<section class="series-hero">
			<div class="series-kicker">Series</div>
			<h1 class="series-title">{series.label}</h1>
			<p class="series-desc">{series.description}</p>
			<p class="series-brand">{series.brandMessage}</p>
		</section>

		<section class="series-roadmap">
			<div class="series-roadmap-heading">이 시리즈의 읽기 흐름</div>
			<div class="series-roadmap-list">
				{#each posts as post, index}
					<a href="{base}/blog/{post.slug}" class="series-step-card">
						<div class="series-step-shell">
							<div class="series-step-main">
								<picture>
									<source srcset="{base}{post.thumbnail.replace('.png', '.webp')}" type="image/webp" />
									<img src="{base}{post.thumbnail}" alt={post.title} class="series-step-avatar" width="52" height="52" loading="lazy" />
								</picture>
								<div class="series-step-body">
									<div class="series-step-meta">
										<div class="series-step-index">#{post.seriesOrder ?? index + 1}</div>
										<span class="series-step-category">{post.categoryLabel}</span>
										<span class="series-step-date"><Calendar size={12} /> {formatDate(post.date)} <span class="series-step-dot">·</span> 예상 {post.readingMinutes}분</span>
									</div>
									<h2 class="series-step-title">{post.title}</h2>
									<p class="series-step-desc">{post.description}</p>
								</div>
							</div>
							<picture>
								<source srcset="{base}{(post.previewAsset ?? post.cardPreview).replace('.png', '.webp')}" type="image/webp" />
								<img src="{base}{post.previewAsset ?? post.cardPreview}" alt={post.title} class="series-step-thumb" width="172" height="172" loading="lazy" />
							</picture>
							<span class="series-step-cta">읽기 <ArrowRight size={14} /></span>
						</div>
					</a>
				{/each}
			</div>
		</section>

		<section class="series-product-cta">
			<div class="series-product-copy">
				<div class="series-product-kicker">DartLab Product</div>
				<h2 class="series-product-title">이 시리즈를 읽고 끝내지 말고 코드로 연결하기</h2>
				<p class="series-product-desc">
					DartLab은 전자공시를 수작업 메모에서 끝내지 않고, 재무 시계열과 공시 문서를 같은 흐름에서 다루도록 설계된 제품입니다.
				</p>
			</div>
			<div class="series-product-links">
				<a href="{base}/docs/getting-started/quickstart" class="series-product-link primary">Quickstart</a>
				<a href="{base}/docs/getting-started/installation" class="series-product-link">설치 가이드</a>
				<a href="{base}/docs/api/overview" class="series-product-link">API Overview</a>
				<a href="{brand.repo}" target="_blank" rel="noopener" class="series-product-link">GitHub</a>
			</div>
		</section>
	</div>
{/if}

<style>
	.series-page {
		max-width: 980px;
	}

	.series-not-found {
		text-align: center;
		padding: 4rem 2rem;
	}

	.series-hero {
		padding-bottom: 2rem;
		border-bottom: 1px solid rgba(30, 36, 51, 0.85);
		margin-bottom: 2rem;
	}

	.series-kicker,
	.series-product-kicker {
		font-size: 0.72rem;
		font-weight: 700;
		color: #ea4647;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		margin-bottom: 0.45rem;
	}

	.series-title,
	.series-product-title {
		font-size: 2.2rem;
		font-weight: 800;
		color: #f8fafc;
		margin-bottom: 0.8rem;
	}

	.series-desc,
	.series-brand,
	.series-product-desc {
		max-width: 780px;
		font-size: 1rem;
		line-height: 1.8;
		color: #94a3b8;
	}

	.series-brand {
		color: #cbd5e1;
		margin-top: 0.9rem;
	}

	.series-roadmap {
		margin-bottom: 2.5rem;
	}

	.series-roadmap-heading {
		font-size: 0.78rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #64748b;
		margin-bottom: 0.85rem;
	}

	.series-roadmap-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.series-step-card {
		padding: 1.35rem 1.4rem;
		border-radius: 12px;
		border: 1px solid rgba(30, 36, 51, 0.9);
		background: rgba(15, 18, 25, 0.9);
		text-decoration: none;
	}

	.series-step-card:hover {
		border-color: rgba(234, 70, 71, 0.28);
	}

	.series-step-shell {
		display: grid;
		grid-template-columns: minmax(0, 1fr) 172px auto;
		gap: 1rem;
		align-items: center;
	}

	.series-step-main {
		min-width: 0;
		display: grid;
		grid-template-columns: auto minmax(0, 1fr);
		gap: 0.85rem;
		align-items: center;
	}

	.series-step-avatar {
		width: 52px;
		height: 52px;
		border-radius: 50%;
		border: 1px solid rgba(234, 70, 71, 0.18);
		background: rgba(15, 18, 25, 0.92);
		flex-shrink: 0;
	}

	.series-step-index {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 2.2rem;
		height: 2.2rem;
		border-radius: 6px;
		background: rgba(234, 70, 71, 0.12);
		border: 1px solid rgba(234, 70, 71, 0.22);
		color: #fda4a4;
		font-size: 0.76rem;
		font-weight: 800;
	}

	.series-step-meta {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.6rem;
		margin-bottom: 0.5rem;
	}

	.series-step-category {
		display: inline-flex;
		align-items: center;
		padding: 0.28rem 0.55rem;
		border-radius: 6px;
		background: rgba(148, 163, 184, 0.08);
		border: 1px solid rgba(148, 163, 184, 0.14);
		color: #cbd5e1;
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.03em;
		text-transform: uppercase;
	}

	.series-step-date {
		display: inline-flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 0.3rem;
		font-size: 0.75rem;
		color: #64748b;
	}

	.series-step-dot {
		color: rgba(100, 116, 139, 0.72);
	}

	.series-step-thumb {
		display: block;
		width: 172px;
		height: 172px;
		object-fit: cover;
		object-position: center;
		border-radius: 10px;
	}

	.series-step-title {
		font-size: 1.15rem;
		font-weight: 700;
		color: #f8fafc;
		margin-bottom: 0.45rem;
	}

	.series-step-desc {
		font-size: 0.92rem;
		line-height: 1.75;
		color: #94a3b8;
	}

	.series-step-cta {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		color: #ea4647;
		font-size: 0.82rem;
		font-weight: 700;
	}

	.series-product-cta {
		margin-top: 2.4rem;
		padding: 1.6rem;
		border-radius: 12px;
		border: 1px solid rgba(234, 70, 71, 0.16);
		background:
			linear-gradient(135deg, rgba(234, 70, 71, 0.08), rgba(251, 146, 60, 0.04)),
			rgba(15, 18, 25, 0.94);
	}

	.series-product-links {
		display: flex;
		flex-wrap: wrap;
		gap: 0.7rem;
		margin-top: 1rem;
	}

	.series-product-link {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.72rem 1rem;
		border-radius: 6px;
		border: 1px solid rgba(148, 163, 184, 0.16);
		background: rgba(148, 163, 184, 0.06);
		color: #e2e8f0;
		text-decoration: none;
		font-weight: 700;
	}

	.series-product-link.primary {
		background: rgba(234, 70, 71, 0.14);
		border-color: rgba(234, 70, 71, 0.28);
		color: #fda4a4;
	}

	@media (max-width: 820px) {
		.series-step-shell {
			grid-template-columns: 1fr;
		}

		.series-step-main {
			grid-template-columns: auto minmax(0, 1fr);
		}

		.series-step-thumb {
			width: 100%;
			max-width: 220px;
			height: auto;
			aspect-ratio: 1 / 1;
			justify-self: end;
		}
	}
</style>
