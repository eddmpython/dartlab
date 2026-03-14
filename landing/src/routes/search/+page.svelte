<script lang="ts">
	import { base } from '$app/paths';
	import { posts } from '$lib/blog/posts';
	import { flattenNav, navigation } from '$lib/docs/navigation';
	import { buildAbsoluteUrl, buildBreadcrumbJsonLd } from '$lib/seo';
	import { onMount } from 'svelte';

	const docItems = flattenNav(navigation)
		.filter((item) => item.href !== '/docs/getting-started')
		.map((item) => ({
			title: item.title,
			href: item.href,
			kind: 'Docs'
		}));

	const blogItems = posts.map((post) => ({
		title: post.title,
		href: `/blog/${post.slug}`,
		kind: 'Blog',
		description: post.description
	}));

	let queryInput = $state('');

	onMount(() => {
		queryInput = new URLSearchParams(window.location.search).get('q')?.trim() ?? '';
	});

	const query = $derived(queryInput.trim().toLowerCase());
	const docResults = $derived(
		query
			? docItems.filter((item) => item.title.toLowerCase().includes(query)).slice(0, 12)
			: []
	);
	const blogResults = $derived(
		query
			? blogItems
					.filter((item) => `${item.title} ${item.description ?? ''}`.toLowerCase().includes(query))
					.slice(0, 12)
			: []
	);
	const totalResults = $derived(docResults.length + blogResults.length);
	const pageUrl = buildAbsoluteUrl('search');
	const pageTitle = 'DartLab 검색 — 전자공시 문서와 블로그 찾기';
	const pageDesc = 'DartLab 문서와 블로그에서 전자공시, DART, EDGAR 관련 내용을 검색한다.';
	const searchJsonLd = JSON.stringify([
		{
			'@context': 'https://schema.org',
			'@type': 'SearchResultsPage',
			name: pageTitle,
			description: pageDesc,
			url: pageUrl,
			inLanguage: 'ko'
		},
		buildBreadcrumbJsonLd([
			{ name: 'DartLab', url: buildAbsoluteUrl('') },
			{ name: 'Search', url: buildAbsoluteUrl('search') }
		])
	]);
</script>

<svelte:head>
	<title>{pageTitle}</title>
	<meta name="description" content={pageDesc} />
	<link rel="canonical" href={pageUrl} />
	<meta property="og:type" content="website" />
	<meta property="og:title" content={pageTitle} />
	<meta property="og:description" content={pageDesc} />
	<meta property="og:url" content={pageUrl} />
	<meta property="og:image" content={buildAbsoluteUrl('og-image.png')} />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content={pageTitle} />
	<meta name="twitter:description" content={pageDesc} />
	<meta name="twitter:image" content={buildAbsoluteUrl('og-image.png')} />
	{@html `<script type="application/ld+json">${searchJsonLd}</script>`}
</svelte:head>

<section class="search-page">
	<div class="search-shell">
		<div class="search-hero">
			<span class="search-kicker">DartLab Search</span>
			<h1>문서와 블로그를 한 번에 찾기</h1>
			<p>DART, EDGAR, 사업보고서, XBRL, 주석, 공시 해석 관련 글과 문서를 한 번에 찾는다.</p>
		</div>

		<form method="GET" action={`${base}/search`} class="search-form">
			<input
				type="search"
				name="q"
				bind:value={queryInput}
				placeholder="예: OpenDART, 8-K, 재고자산, audit"
			/>
			<button type="submit">검색</button>
		</form>

		{#if !query}
			<div class="search-suggestions">
				<a href="{base}/search?q=OpenDART">OpenDART</a>
				<a href="{base}/search?q=8-K">8-K</a>
				<a href="{base}/search?q=%EC%9E%AC%EA%B3%A0%EC%9E%90%EC%82%B0">재고자산</a>
				<a href="{base}/search?q=MD%26A">MD&amp;A</a>
				<a href="{base}/search?q=XBRL">XBRL</a>
			</div>
		{:else}
			<p class="search-count">총 {totalResults}개 결과</p>
		{/if}

		{#if query}
			<div class="search-grid">
				<section class="search-section">
					<h2>Docs</h2>
					{#if docResults.length > 0}
						<div class="result-list">
							{#each docResults as item}
								<a href="{base}{item.href}" class="result-card">
									<span class="result-kind">{item.kind}</span>
									<strong>{item.title}</strong>
									<span class="result-path">{item.href}</span>
								</a>
							{/each}
						</div>
					{:else}
						<p class="result-empty">일치하는 문서가 없다.</p>
					{/if}
				</section>

				<section class="search-section">
					<h2>Blog</h2>
					{#if blogResults.length > 0}
						<div class="result-list">
							{#each blogResults as item}
								<a href="{base}{item.href}" class="result-card">
									<span class="result-kind">{item.kind}</span>
									<strong>{item.title}</strong>
									{#if item.description}
										<p>{item.description}</p>
									{/if}
									<span class="result-path">{item.href}</span>
								</a>
							{/each}
						</div>
					{:else}
						<p class="result-empty">일치하는 블로그 글이 없다.</p>
					{/if}
				</section>
			</div>
		{/if}
	</div>
</section>

<style>
	.search-page {
		padding: 3rem 1.25rem 5rem;
	}

	.search-shell {
		max-width: 1100px;
		margin: 0 auto;
	}

	.search-hero {
		margin-bottom: 1.5rem;
	}

	.search-kicker {
		display: inline-block;
		margin-bottom: 0.65rem;
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #fdba74;
	}

	.search-hero h1 {
		margin: 0 0 0.8rem;
		font-size: clamp(2rem, 3vw, 3rem);
		line-height: 1.1;
		color: #f8fafc;
	}

	.search-hero p {
		margin: 0;
		max-width: 720px;
		line-height: 1.75;
		color: #cbd5e1;
	}

	.search-form {
		display: grid;
		grid-template-columns: minmax(0, 1fr) auto;
		gap: 0.75rem;
		margin-bottom: 1rem;
	}

	.search-form input {
		width: 100%;
		padding: 0.95rem 1rem;
		border-radius: 14px;
		border: 1px solid rgba(148, 163, 184, 0.18);
		background: rgba(15, 23, 42, 0.92);
		color: #f8fafc;
		font-size: 1rem;
	}

	.search-form button {
		padding: 0.95rem 1.2rem;
		border: none;
		border-radius: 14px;
		background: #ea4647;
		color: #fff;
		font-weight: 700;
		cursor: pointer;
	}

	.search-suggestions {
		display: flex;
		flex-wrap: wrap;
		gap: 0.6rem;
		margin-bottom: 1.25rem;
	}

	.search-suggestions a {
		padding: 0.45rem 0.75rem;
		border-radius: 999px;
		background: rgba(148, 163, 184, 0.12);
		color: #cbd5e1;
		text-decoration: none;
	}

	.search-count {
		margin: 0 0 1rem;
		color: #cbd5e1;
	}

	.search-grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 1rem;
	}

	.search-section {
		padding: 1rem;
		border-radius: 18px;
		border: 1px solid rgba(148, 163, 184, 0.14);
		background: linear-gradient(180deg, rgba(15, 23, 42, 0.86), rgba(2, 6, 23, 0.96));
	}

	.search-section h2 {
		margin: 0 0 0.9rem;
		font-size: 1rem;
		color: #f8fafc;
	}

	.result-list {
		display: flex;
		flex-direction: column;
		gap: 0.7rem;
	}

	.result-card {
		display: block;
		padding: 0.9rem 1rem;
		border-radius: 14px;
		border: 1px solid rgba(148, 163, 184, 0.14);
		background: rgba(15, 23, 42, 0.56);
		text-decoration: none;
		color: inherit;
	}

	.result-kind {
		display: inline-block;
		margin-bottom: 0.4rem;
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #fdba74;
	}

	.result-card strong {
		display: block;
		margin-bottom: 0.4rem;
		color: #f8fafc;
	}

	.result-card p {
		margin: 0 0 0.45rem;
		font-size: 0.92rem;
		line-height: 1.65;
		color: #cbd5e1;
	}

	.result-path {
		font-size: 0.82rem;
		color: #94a3b8;
	}

	.result-empty {
		margin: 0;
		color: #94a3b8;
	}

	@media (max-width: 820px) {
		.search-form,
		.search-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
